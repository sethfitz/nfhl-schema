"""The generated Station Start Points model against real NFHL features."""

from __future__ import annotations

from typing import Any

import pytest
from overture.schema.system.model_constraint import ModelConstraint

from nfhl.models import CrossSection, ProfileBaseline, StationStart
from nfhl.models.enums import LEGACY_MEMBERS, LocAccuracy
from nfhl.rule_counts import judge

from .helpers import fixture_feature, legacy_warnings_by, rejected_by, validate_as


def rejected(feature: dict[str, Any]) -> set[str]:
    return rejected_by(feature, StationStart)


def warned(feature: dict[str, Any]) -> list[str]:
    """The fields `feature` holds a legacy value in, by the warnings they raise."""
    return [m.split("=")[0] for m in legacy_warnings_by(feature, StationStart)]


@pytest.fixture
def high(station_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real station start that validates, to mutate in a test."""
    return fixture_feature(station_cases, "high_accuracy")


def test_the_fixture_has_every_kind_of_case(
    station_cases: list[dict[str, Any]],
) -> None:
    assert any(c["expect"] is None and not c["warns"] for c in station_cases)
    assert any(c["warns"] for c in station_cases)
    assert any(c["expect"] is not None for c in station_cases)


def test_each_real_station_start_is_judged_as_recorded(
    station_cases: list[dict[str, Any]],
) -> None:
    for case in station_cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected(case["feature"]) == expected, case["name"]
        if case["expect"] is None:
            legacy = [case["warns"]] if case["warns"] else []
            assert warned(case["feature"]) == legacy, case["name"]


def test_the_model_has_no_rules_to_judge(
    station_cases: list[dict[str, Any]],
) -> None:
    assert ModelConstraint.get_model_constraints(StationStart) == ()
    for case in station_cases:
        verdict = judge(StationStart, case["feature"]["properties"])
        assert verdict.broken == set(), case["name"]


def test_a_valid_station_start_reads_back_typed(high: dict[str, Any]) -> None:
    station = validate_as(StationStart, high)
    assert station.loc_acc is LocAccuracy.HIGH
    assert station.start_id
    assert station.start_desc


def test_the_accuracy_is_stored_as_written_in_the_domain(
    high: dict[str, Any],
) -> None:
    # The field description writes “HIGH”; D_Loc_Accuracy and the data, High.
    high["properties"]["LOC_ACC"] = "HIGH"
    assert rejected(high) == {"LOC_ACC"}


def test_the_station_start_id_is_required_here_and_optional_where_it_points(
    high: dict[str, Any],
) -> None:
    # The key is "R" in S_Stn_Start; the foreign keys are "R1" in S_XS and
    # S_Profil_Basln.
    del high["properties"]["START_ID"]
    assert rejected(high) == {"START_ID"}
    for model in (CrossSection, ProfileBaseline):
        field = model.model_fields["start_id"]
        assert not field.is_required(), model.__name__
        assert field.description is not None
        assert "S_Stn_Start" in field.description, model.__name__


def test_a_multipoint_station_start_is_rejected(high: dict[str, Any]) -> None:
    point = high["geometry"]["coordinates"]
    high["geometry"] = {"type": "MultiPoint", "coordinates": [point, point]}
    assert rejected(high) == {"geometry"}


def test_not_populated_is_a_legacy_accuracy(high: dict[str, Any]) -> None:
    assert LocAccuracy("NP") in LEGACY_MEMBERS
    high["properties"]["LOC_ACC"] = "NP"
    assert rejected(high) == set()
    assert warned(high) == ["LOC_ACC"]
