"""The rules reach the JSON Schema as well as Python, and stack without loss."""

from __future__ import annotations

import json
from typing import Any

import jsonschema
import pytest
from overture.schema.system.model_constraint import forbid_if
from overture.schema.system.optionality import Omitable
from pydantic import BaseModel

from nfhl.constraints import Absent
from nfhl.constraints import forbid_if as named_forbid_if
from nfhl.models import FloodHazardZone


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    return FloodHazardZone.model_json_schema()


def dumped(valid_feature: dict[str, Any]) -> dict[str, Any]:
    """The feature as the model writes it, after its own null handling."""
    zone = FloodHazardZone.model_validate_json(json.dumps(valid_feature))
    feature: dict[str, Any] = json.loads(zone.model_dump_json())
    return feature


def check(schema: dict[str, Any], feature: dict[str, Any]) -> bool:
    return jsonschema.Draft202012Validator(schema).is_valid(feature)


def test_the_schema_accepts_a_valid_feature(
    schema: dict[str, Any], valid_feature: dict[str, Any]
) -> None:
    assert check(schema, dumped(valid_feature))


@pytest.mark.parametrize(
    ("drop", "add"),
    [
        (["STATIC_BFE"], {}),  # V_DATUM and LEN_UNIT left without a BFE
        ([], {"VELOCITY": 2.5}),  # a velocity without VEL_UNIT
    ],
)
def test_the_schema_enforces_the_relationship_rules(
    schema: dict[str, Any],
    valid_feature: dict[str, Any],
    drop: list[str],
    add: dict[str, Any],
) -> None:
    feature = dumped(valid_feature)
    for key in drop:
        del feature["properties"][key]
    feature["properties"].update(add)
    assert not check(schema, feature)


def test_only_v_datum_breaks_the_schema_when_len_unit_has_a_depth(
    schema: dict[str, Any], valid_feature: dict[str, Any]
) -> None:
    feature = dumped(valid_feature)
    del feature["properties"]["STATIC_BFE"]
    feature["properties"]["DEPTH"] = 2.0
    assert not check(schema, feature)
    del feature["properties"]["V_DATUM"]
    assert check(schema, feature)


def test_uniquely_named_decorators_keep_both_rules() -> None:
    class Holder(BaseModel):
        a: Omitable[int]
        b: Omitable[int]
        c: Omitable[int]

    model = named_forbid_if(["b"], Absent("a"))(
        named_forbid_if(["c"], Absent("a"))(Holder)
    )
    for kwargs in ({"b": 1}, {"c": 1}):
        with pytest.raises(ValueError):
            model.model_validate(kwargs)
    model.model_validate({"a": 0, "b": 1, "c": 1})


def test_stacked_system_decorators_drop_the_inner_rule_in_python() -> None:
    # Pins the overture-schema-system 2.0.0 behaviour `nfhl.constraints` works
    # around. If this starts failing, upstream fixed it and the wrapper can go.
    class Holder(BaseModel):
        a: Omitable[int]
        b: Omitable[int]
        c: Omitable[int]

    model = forbid_if(["b"], Absent("a"))(forbid_if(["c"], Absent("a"))(Holder))
    with pytest.raises(ValueError):
        model.model_validate({"b": 1})  # outer rule fires
    model.model_validate({"c": 1})  # inner rule silently does not
