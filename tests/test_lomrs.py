"""The generated LOMRs model against real NFHL features."""

from __future__ import annotations

from typing import Any

import pytest
from overture.schema.system.model_constraint import ModelConstraint

from nfhl.models import Lomr
from nfhl.models.enums import LOMCStatus, Scale
from nfhl.rule_counts import judge

from .helpers import fixture_feature, legacy_warnings_by, rejected_by, validate_as


def rejected(feature: dict[str, Any]) -> set[str]:
    return rejected_by(feature, Lomr)


@pytest.fixture
def effective(lomr_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real effective LOMR that validates, to mutate in a test."""
    return fixture_feature(lomr_cases, "effective_6000")


def test_the_fixture_has_every_kind_of_case(
    lomr_cases: list[dict[str, Any]],
) -> None:
    # No value of SCALE or STATUS is common enough to be legacy (spec/legacy.json),
    # so no case can warn.
    assert any(c["expect"] is None for c in lomr_cases)
    assert any(c["expect"] is not None for c in lomr_cases)
    assert not any(c["warns"] for c in lomr_cases)


def test_each_real_lomr_is_judged_as_recorded(
    lomr_cases: list[dict[str, Any]],
) -> None:
    for case in lomr_cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected(case["feature"]) == expected, case["name"]
        if case["expect"] is None:
            assert legacy_warnings_by(case["feature"], Lomr) == [], case["name"]


def test_the_model_has_no_rules_to_judge(lomr_cases: list[dict[str, Any]]) -> None:
    assert ModelConstraint.get_model_constraints(Lomr) == ()
    for case in lomr_cases:
        verdict = judge(Lomr, case["feature"]["properties"])
        assert verdict.broken == set(), case["name"]


def test_a_valid_lomr_reads_back_typed(effective: dict[str, Any]) -> None:
    # Omitable hides the enums from mypy; the dump holds the members themselves.
    lomr = validate_as(Lomr, effective).model_dump()
    assert lomr["STATUS"] is LOMCStatus.EFFECTIVE
    assert lomr["SCALE"] is Scale.V_6000
    assert lomr["LOMR_ID"]
    assert isinstance(lomr["EFF_DATE"], int)


@pytest.mark.parametrize(
    "field",
    [
        "DFIRM_ID",
        "VERSION_ID",
        "LOMR_ID",
        "EFF_DATE",
        "CASE_NO",
        "SCALE",
        "STATUS",
        "SOURCE_CIT",
    ],
)
def test_every_field_of_the_table_is_required(
    effective: dict[str, Any], field: str
) -> None:
    del effective["properties"][field]
    assert rejected(effective) == {field}


@pytest.mark.parametrize("scale", ["6000", "12000", "24000", "10000"])
def test_the_scale_is_a_denominator_in_d_scale(
    effective: dict[str, Any], scale: str
) -> None:
    effective["properties"]["SCALE"] = scale
    assert rejected(effective) == set()


@pytest.mark.parametrize("scale", ["1000", "1:6000", " "])
def test_the_scale_is_not_the_domain_code(
    effective: dict[str, Any], scale: str
) -> None:
    # D_Scale's coded value 1000 is the denominator 6000.
    effective["properties"]["SCALE"] = scale
    assert rejected(effective) == {"SCALE"}


def test_the_status_is_spelled_as_the_domain_spells_it(
    effective: dict[str, Any],
) -> None:
    effective["properties"]["STATUS"] = "Superceded"
    assert rejected(effective) == {"STATUS"}
    effective["properties"]["STATUS"] = "Superseded"
    assert rejected(effective) == set()


def test_a_multipart_lomr_is_rejected(effective: dict[str, Any]) -> None:
    # "Multipart polygons are not allowed."
    ring = effective["geometry"]["coordinates"]
    effective["geometry"] = {"type": "MultiPolygon", "coordinates": [ring, ring]}
    assert rejected(effective) == {"geometry"}


def test_a_lomr_with_no_geometry_is_rejected(effective: dict[str, Any]) -> None:
    effective["geometry"] = None
    assert rejected(effective) == {"geometry"}
