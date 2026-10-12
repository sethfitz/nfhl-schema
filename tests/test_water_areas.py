"""The generated Water Areas model against real NFHL features."""

from __future__ import annotations

from typing import Any

import pytest
from overture.schema.system.model_constraint import ModelConstraint

from nfhl.models import WaterArea
from nfhl.models.enums import TrueFalse
from nfhl.rule_counts import judge

from .helpers import fixture_feature, legacy_warnings_by, rejected_by, validate_as


def rejected(feature: dict[str, Any]) -> set[str]:
    return rejected_by(feature, WaterArea)


def warned(feature: dict[str, Any]) -> list[str]:
    """The fields `feature` holds a legacy value in, by the warnings they raise."""
    return [m.split("=")[0] for m in legacy_warnings_by(feature, WaterArea)]


@pytest.fixture
def shown(water_area_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real water area that validates, to mutate in a test."""
    return fixture_feature(water_area_cases, "shown_on_firm")


def test_the_fixture_has_every_kind_of_case(
    water_area_cases: list[dict[str, Any]],
) -> None:
    assert any(c["expect"] is None and not c["warns"] for c in water_area_cases)
    assert any(c["warns"] for c in water_area_cases)
    assert any(c["expect"] is not None for c in water_area_cases)


def test_each_real_water_area_is_judged_as_recorded(
    water_area_cases: list[dict[str, Any]],
) -> None:
    for case in water_area_cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected(case["feature"]) == expected, case["name"]
        if case["expect"] is None:
            legacy = [case["warns"]] if case["warns"] else []
            assert warned(case["feature"]) == legacy, case["name"]


def test_the_model_has_no_rules_to_judge(
    water_area_cases: list[dict[str, Any]],
) -> None:
    assert ModelConstraint.get_model_constraints(WaterArea) == ()
    for case in water_area_cases:
        verdict = judge(WaterArea, case["feature"]["properties"])
        assert verdict.broken == set(), case["name"]


def test_a_valid_water_area_reads_back_typed(shown: dict[str, Any]) -> None:
    # Omitable hides the enums from mypy; the dump holds the members themselves.
    area = validate_as(WaterArea, shown).model_dump()
    assert area["WTR_AR_ID"]
    assert area["WTR_NM"]
    assert area["SHOWN_FIRM"] is TrueFalse.T
    assert area["SHOWN_INDX"] is TrueFalse.T


@pytest.mark.parametrize(
    "field", ["DFIRM_ID", "VERSION_ID", "WTR_AR_ID", "WTR_NM", "SOURCE_CIT"]
)
def test_a_required_field_is_required(shown: dict[str, Any], field: str) -> None:
    del shown["properties"][field]
    assert rejected(shown) == {field}


@pytest.mark.parametrize("field", ["WTR_NM", "SOURCE_CIT"])
def test_an_empty_required_field_is_missing(shown: dict[str, Any], field: str) -> None:
    shown["properties"][field] = ""
    assert rejected(shown) == {field}


def test_an_unnamed_water_area_is_named_np_or_a_lone_space(
    shown: dict[str, Any],
) -> None:
    # "Unnamed bodies of water follow the convention shown in Section 5.3":
    # `NP` is a value, and a lone space is text.
    for value in ("NP", " "):
        shown["properties"]["WTR_NM"] = value
        assert rejected(shown) == set(), repr(value)


@pytest.mark.parametrize("flag", ["SHOWN_FIRM", "SHOWN_INDX"])
def test_the_shown_flags_are_optional_and_take_the_domain(
    shown: dict[str, Any], flag: str
) -> None:
    # "A": required if applicable, so absent, null and "" validate; a lone space
    # is text, and no value of D_TrueFalse.
    for value in (None, "", "T", "F", "U"):
        shown["properties"][flag] = value
        assert rejected(shown) == set(), repr(value)
    del shown["properties"][flag]
    assert rejected(shown) == set()
    for value in ("Y", " "):
        shown["properties"][flag] = value
        assert rejected(shown) == {flag}, repr(value)


@pytest.mark.parametrize("flag", ["SHOWN_FIRM", "SHOWN_INDX"])
def test_a_one_for_a_flag_warns(shown: dict[str, Any], flag: str) -> None:
    # 888 water areas hold `1` in SHOWN_FIRM, over the legacy bar; the models
    # share one enum per domain, so it validates in every D_TrueFalse field.
    shown["properties"][flag] = "1"
    assert rejected(shown) == set()
    assert warned(shown) == [flag]


def test_the_water_name_is_the_join_to_the_water_lines() -> None:
    # "Surface water features may appear in either the S_Wtr_Ar table or the
    # S_Wtr_Ln table or both"; the models do not check the join.
    field = WaterArea.model_fields["wtr_nm"]
    assert field.description is not None
    assert "Surface Water Feature Name" in field.description


def test_a_multipart_water_area_is_one_feature(shown: dict[str, Any]) -> None:
    # Table 4 holds S_Wtr_Ar to no "Must Be Single Part".
    polygon = shown["geometry"]["coordinates"]
    shown["geometry"] = {"type": "MultiPolygon", "coordinates": [polygon, polygon]}
    assert rejected(shown) == set()


def test_a_water_line_is_not_a_water_area(shown: dict[str, Any]) -> None:
    ring = shown["geometry"]["coordinates"][0]
    shown["geometry"] = {"type": "LineString", "coordinates": ring}
    assert rejected(shown) == {"geometry"}


def test_a_water_area_with_no_geometry_is_rejected(shown: dict[str, Any]) -> None:
    shown["geometry"] = None
    assert rejected(shown) == {"geometry"}
