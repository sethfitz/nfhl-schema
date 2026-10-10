"""The generated Water Lines model against real NFHL features."""

from __future__ import annotations

from typing import Any

import pytest
from overture.schema.system.model_constraint import ModelConstraint

from nfhl.models import WaterLine
from nfhl.models.enums import TrueFalse
from nfhl.rule_counts import judge

from .helpers import fixture_feature, legacy_warnings_by, rejected_by, validate_as


def rejected(feature: dict[str, Any]) -> set[str]:
    return rejected_by(feature, WaterLine)


@pytest.fixture
def shown(water_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real water line that validates, to mutate in a test."""
    return fixture_feature(water_cases, "shown_on_firm")


def test_the_fixture_has_every_kind_of_case(
    water_cases: list[dict[str, Any]],
) -> None:
    # The only coded fields hold T, F or U, so no case can hold a legacy value.
    assert any(c["expect"] is None for c in water_cases)
    assert any(c["expect"] is not None for c in water_cases)
    assert not any(c["warns"] for c in water_cases)


def test_each_real_water_line_is_judged_as_recorded(
    water_cases: list[dict[str, Any]],
) -> None:
    for case in water_cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected(case["feature"]) == expected, case["name"]
        if case["expect"] is None:
            assert legacy_warnings_by(case["feature"], WaterLine) == [], case["name"]


def test_the_model_has_no_rules_to_judge(
    water_cases: list[dict[str, Any]],
) -> None:
    assert ModelConstraint.get_model_constraints(WaterLine) == ()
    for case in water_cases:
        verdict = judge(WaterLine, case["feature"]["properties"])
        assert verdict.broken == set(), case["name"]


def test_a_valid_water_line_reads_back_typed(shown: dict[str, Any]) -> None:
    # Omitable hides the enums from mypy; the dump holds the members themselves.
    line = validate_as(WaterLine, shown).model_dump()
    assert line["WTR_LN_ID"]
    assert line["WTR_NM"]
    assert line["SHOWN_FIRM"] is TrueFalse.T
    assert line["SHOWN_INDX"] is TrueFalse.T


def test_the_shown_flags_are_optional_and_take_the_domain(
    shown: dict[str, Any],
) -> None:
    # "A": required if applicable, so absent, null and "" validate; a lone space
    # is text, and no value of D_TrueFalse.
    for value in (None, ""):
        shown["properties"]["SHOWN_FIRM"] = value
        assert rejected(shown) == set(), repr(value)
    del shown["properties"]["SHOWN_INDX"]
    assert rejected(shown) == set()
    for value in ("Y", " "):
        shown["properties"]["SHOWN_FIRM"] = value
        assert rejected(shown) == {"SHOWN_FIRM"}, repr(value)


@pytest.mark.parametrize("field", ["WTR_LN_ID", "WTR_NM", "SOURCE_CIT"])
def test_a_required_field_is_required(shown: dict[str, Any], field: str) -> None:
    del shown["properties"][field]
    assert rejected(shown) == {field}


def test_the_water_name_is_the_join_to_the_modelled_layers() -> None:
    # The cross sections, base flood elevations and profile baselines name a
    # stream by WTR_NM too; the models do not check the join.
    field = WaterLine.model_fields["wtr_nm"]
    assert field.description is not None
    assert "Surface Water Feature Name" in field.description


def test_a_multiline_water_line_is_rejected(shown: dict[str, Any]) -> None:
    line = shown["geometry"]["coordinates"]
    shown["geometry"] = {"type": "MultiLineString", "coordinates": [line, line]}
    assert rejected(shown) == {"geometry"}


def test_a_water_line_with_no_geometry_is_rejected(shown: dict[str, Any]) -> None:
    shown["geometry"] = None
    assert rejected(shown) == {"geometry"}
