"""The generated model against real NFHL features."""

from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import ValidationError

from nfhl.annotations import DatumIn, UnitIn, field_datums, field_units
from nfhl.models import FloodHazardZone
from nfhl.models.enums import LengthUnits, Zone


def validate(feature: dict[str, Any]) -> FloodHazardZone:
    # From JSON text, never a dict: the Feature envelope unwraps only in JSON mode.
    return FloodHazardZone.model_validate_json(json.dumps(feature))


def rejected_by(feature: dict[str, Any]) -> set[str]:
    """Wire field names (or rule names) that reject `feature`; empty if it is valid."""
    try:
        validate(feature)
    except ValidationError as e:
        return {
            str(err["loc"][0]) if err["loc"] else err["msg"].split("`")[-2]
            for err in e.errors()
        }
    return set()


def test_the_fixture_has_both_kinds_of_case(cases: list[dict[str, Any]]) -> None:
    # A did-happen control: an all-valid or all-rejected fixture tests half.
    assert any(c["expect"] is None for c in cases)
    assert any(c["expect"] is not None for c in cases)


def test_each_real_feature_is_judged_as_recorded(cases: list[dict[str, Any]]) -> None:
    for case in cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected_by(case["feature"]) == expected, case["name"]


def test_an_unknown_flood_zone_is_rejected(valid_feature: dict[str, Any]) -> None:
    assert rejected_by(valid_feature) == set()
    valid_feature["properties"]["FLD_ZONE"] = "Q"
    assert rejected_by(valid_feature) == {"FLD_ZONE"}


def test_a_coded_value_is_not_a_published_value(valid_feature: dict[str, Any]) -> None:
    # D_Zone's coded value for open water is OW; data carries OPEN WATER.
    valid_feature["properties"]["FLD_ZONE"] = "OW"
    assert rejected_by(valid_feature) == {"FLD_ZONE"}


def test_a_missing_required_field_is_rejected(valid_feature: dict[str, Any]) -> None:
    del valid_feature["properties"]["SOURCE_CIT"]
    assert rejected_by(valid_feature) == {"SOURCE_CIT"}


def test_the_reference_null_encodings_read_as_absent(
    valid_feature: dict[str, Any],
) -> None:
    props = valid_feature["properties"]
    assert props["DEPTH"] == -9999 and props["VEL_UNIT"] is None
    props["ZONE_SUBTY"] = ""
    zone = validate(valid_feature)
    dumped = json.loads(zone.model_dump_json())["properties"]
    for wire in ("DEPTH", "VEL_UNIT", "ZONE_SUBTY", "VELOCITY"):
        assert wire not in dumped, wire
    assert dumped["STATIC_BFE"] == props["STATIC_BFE"]


def test_an_empty_required_field_is_missing(valid_feature: dict[str, Any]) -> None:
    valid_feature["properties"]["STUDY_TYP"] = ""
    assert rejected_by(valid_feature) == {"STUDY_TYP"}


def test_a_numeric_null_in_a_text_field_is_not_forgiven(
    valid_feature: dict[str, Any],
) -> None:
    valid_feature["properties"]["V_DATUM"] = "-9999"
    assert rejected_by(valid_feature) == {"V_DATUM"}


def test_values_parse_to_their_enums(valid_feature: dict[str, Any]) -> None:
    zone = validate(valid_feature)
    assert zone.fld_zone is Zone.AE
    len_unit: object = zone.len_unit  # mypy cannot see past `Omitable`
    assert len_unit is LengthUnits.FEET


def test_service_only_fields_are_kept_as_extras(valid_feature: dict[str, Any]) -> None:
    zone = validate(valid_feature)
    assert zone.model_extra is not None
    assert "GlobalID" in zone.model_extra


def test_units_and_datum_are_declared_on_the_measured_fields() -> None:
    assert field_units(FloodHazardZone) == {
        "STATIC_BFE": UnitIn("LEN_UNIT"),
        "DEPTH": UnitIn("LEN_UNIT"),
        "VELOCITY": UnitIn("VEL_UNIT"),
    }
    assert field_datums(FloodHazardZone) == {"STATIC_BFE": DatumIn("V_DATUM")}


@pytest.mark.parametrize(
    ("change", "rule"),
    [
        # Only the first failing rule is reported, so each case breaks one.
        ({"STATIC_BFE": -9999, "DEPTH": 2.0}, "@forbid_if(v_datum)"),
        ({"STATIC_BFE": -9999, "V_DATUM": None}, "@forbid_if(len_unit)"),
        ({"VELOCITY": 2.5}, "@require_if(vel_unit)"),
    ],
)
def test_each_relationship_rule_fires(
    valid_feature: dict[str, Any], change: dict[str, Any], rule: str
) -> None:
    valid_feature["properties"].update(change)
    assert rejected_by(valid_feature) == {rule}


def test_a_unit_with_a_depth_but_no_bfe_is_allowed(
    valid_feature: dict[str, Any],
) -> None:
    valid_feature["properties"].update(STATIC_BFE=-9999, V_DATUM=None, DEPTH=2.0)
    assert rejected_by(valid_feature) == set()
