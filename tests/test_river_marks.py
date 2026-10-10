"""The generated River Mile Markers model against real NFHL features."""

from __future__ import annotations

from typing import Any

import pytest
from overture.schema.system.model_constraint import ModelConstraint

from nfhl.models import RiverMark
from nfhl.rule_counts import judge

from .helpers import fixture_feature, legacy_warnings_by, rejected_by, validate_as


def rejected(feature: dict[str, Any]) -> set[str]:
    return rejected_by(feature, RiverMark)


@pytest.fixture
def numbered(mark_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real river mark that validates, to mutate in a test."""
    return fixture_feature(mark_cases, "numbered_mark")


def test_the_fixture_has_every_kind_of_case(
    mark_cases: list[dict[str, Any]],
) -> None:
    # No field has a domain, so no case can hold a legacy value.
    assert any(c["expect"] is None for c in mark_cases)
    assert any(c["expect"] is not None for c in mark_cases)
    assert not any(c["warns"] for c in mark_cases)


def test_each_real_river_mark_is_judged_as_recorded(
    mark_cases: list[dict[str, Any]],
) -> None:
    for case in mark_cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected(case["feature"]) == expected, case["name"]
        if case["expect"] is None:
            assert legacy_warnings_by(case["feature"], RiverMark) == [], case["name"]


def test_the_model_has_no_rules_to_judge(
    mark_cases: list[dict[str, Any]],
) -> None:
    assert ModelConstraint.get_model_constraints(RiverMark) == ()
    for case in mark_cases:
        verdict = judge(RiverMark, case["feature"]["properties"])
        assert verdict.broken == set(), case["name"]


def test_a_valid_river_mark_reads_back_typed(numbered: dict[str, Any]) -> None:
    mark = validate_as(RiverMark, numbered)
    assert mark.riv_mrk_id
    assert mark.start_id
    assert mark.riv_mrk_no


def test_the_mark_number_is_text_not_a_distance(numbered: dict[str, Any]) -> None:
    # "usually represents the distance", and the field is Text: section 7.3's
    # `NP` is a value, and no unit is stated for the ones that are numbers.
    numbered["properties"]["RIV_MRK_NO"] = "NP"
    assert rejected(numbered) == set()
    assert validate_as(RiverMark, numbered).riv_mrk_no == "NP"


def test_the_station_start_id_is_required_and_points_at_a_station_start(
    numbered: dict[str, Any],
) -> None:
    field = RiverMark.model_fields["start_id"]
    assert field.description is not None
    assert "S_Stn_Start" in field.description
    del numbered["properties"]["START_ID"]
    assert rejected(numbered) == {"START_ID"}


def test_a_multipoint_river_mark_is_rejected(numbered: dict[str, Any]) -> None:
    point = numbered["geometry"]["coordinates"]
    numbered["geometry"] = {"type": "MultiPoint", "coordinates": [point, point]}
    assert rejected(numbered) == {"geometry"}


def test_an_empty_river_mark_is_rejected(numbered: dict[str, Any]) -> None:
    # How ArcGIS writes an empty point; layer 7 holds none today.
    numbered["geometry"] = {"type": "Point", "coordinates": []}
    assert rejected(numbered) == {"geometry"}
