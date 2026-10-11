"""The generated Flood Hazard Boundaries model against real NFHL features."""

from __future__ import annotations

from typing import Any

import pytest
from overture.schema.system.model_constraint import ModelConstraint

from nfhl.models import FloodHazardBoundary
from nfhl.models.enums import LnTyp
from nfhl.rule_counts import judge

from .helpers import fixture_feature, legacy_warnings_by, rejected_by, validate_as


def rejected(feature: dict[str, Any]) -> set[str]:
    return rejected_by(feature, FloodHazardBoundary)


@pytest.fixture
def boundary(boundary_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real flood zone boundary that validates, to mutate."""
    return fixture_feature(boundary_cases, "sfha_boundary")


def test_the_fixture_has_every_kind_of_case(
    boundary_cases: list[dict[str, Any]],
) -> None:
    # No LN_TYP outside D_Ln_Typ reaches the legacy threshold (spec/legacy.json),
    # so no case can warn.
    assert any(c["expect"] is None for c in boundary_cases)
    assert any(c["expect"] is not None for c in boundary_cases)
    assert not any(c["warns"] for c in boundary_cases)


def test_each_real_boundary_is_judged_as_recorded(
    boundary_cases: list[dict[str, Any]],
) -> None:
    for case in boundary_cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected(case["feature"]) == expected, case["name"]
        if case["expect"] is None:
            warned = legacy_warnings_by(case["feature"], FloodHazardBoundary)
            assert warned == [], case["name"]


def test_the_model_has_no_rules_to_judge(
    boundary_cases: list[dict[str, Any]],
) -> None:
    assert ModelConstraint.get_model_constraints(FloodHazardBoundary) == ()
    for case in boundary_cases:
        verdict = judge(FloodHazardBoundary, case["feature"]["properties"])
        assert verdict.broken == set(), case["name"]


def test_a_valid_boundary_reads_back_typed(boundary: dict[str, Any]) -> None:
    # Omitable hides the enums from mypy; the dump holds the members themselves.
    line = validate_as(FloodHazardBoundary, boundary).model_dump()
    assert line["LN_TYP"] is LnTyp.SFHA_FLOOD_ZONE_BOUNDARY
    assert line["FLD_LN_ID"]
    assert line["SOURCE_CIT"]


@pytest.mark.parametrize(
    "field", ["DFIRM_ID", "VERSION_ID", "FLD_LN_ID", "LN_TYP", "SOURCE_CIT"]
)
def test_every_field_of_the_table_is_required(
    boundary: dict[str, Any], field: str
) -> None:
    del boundary["properties"][field]
    assert rejected(boundary) == {field}


@pytest.mark.parametrize("line_type", list(LnTyp))
def test_every_line_type_of_d_ln_typ_validates(
    boundary: dict[str, Any], line_type: LnTyp
) -> None:
    boundary["properties"]["LN_TYP"] = line_type.value
    assert rejected(boundary) == set()


@pytest.mark.parametrize("line_type", ["NP", "2034", "1010", " "])
def test_the_line_type_is_the_domain_value_not_its_code(
    boundary: dict[str, Any], line_type: str
) -> None:
    boundary["properties"]["LN_TYP"] = line_type
    assert rejected(boundary) == {"LN_TYP"}


def test_a_multiline_boundary_is_rejected(boundary: dict[str, Any]) -> None:
    # Table 4: "Must Be Single Part".
    line = boundary["geometry"]["coordinates"]
    boundary["geometry"] = {"type": "MultiLineString", "coordinates": [line, line]}
    assert rejected(boundary) == {"geometry"}


def test_a_boundary_with_no_geometry_is_rejected(boundary: dict[str, Any]) -> None:
    boundary["geometry"] = None
    assert rejected(boundary) == {"geometry"}
