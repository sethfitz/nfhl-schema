"""The generated Base Flood Elevations model against real NFHL features."""

from __future__ import annotations

import copy
from typing import Any

from overture.schema.system.model_constraint import ModelConstraint

from nfhl.annotations import DatumIn, UnitIn, field_datums, field_units
from nfhl.models import BaseFloodElevation
from nfhl.models.enums import LengthUnits, VDatum
from nfhl.rule_counts import take_census
from nfhl.spec_source import Layer, SpecReader

from .helpers import rejected_by, validate_as


def rejected(feature: dict[str, Any]) -> set[str]:
    return rejected_by(feature, BaseFloodElevation)


def a_valid_line(bfe_cases: list[dict[str, Any]]) -> dict[str, Any]:
    case = next(c for c in bfe_cases if c["name"] == "navd88_feet")
    feature: dict[str, Any] = copy.deepcopy(case["feature"])
    return feature


def test_the_fixture_has_both_kinds_of_case(bfe_cases: list[dict[str, Any]]) -> None:
    assert any(c["expect"] is None for c in bfe_cases)
    assert any(c["expect"] is not None for c in bfe_cases)


def test_each_real_line_is_judged_as_recorded(bfe_cases: list[dict[str, Any]]) -> None:
    for case in bfe_cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected(case["feature"]) == expected, case["name"]


def test_a_valid_line_reads_back_typed(bfe_cases: list[dict[str, Any]]) -> None:
    line = validate_as(BaseFloodElevation, a_valid_line(bfe_cases))
    assert line.len_unit is LengthUnits.FEET
    assert line.v_datum is VDatum.NAVD88
    assert line.elev > 0
    assert line.version_id  # published on this layer, unlike the zones'


def test_elev_is_in_len_unit_and_measured_from_v_datum() -> None:
    assert field_units(BaseFloodElevation) == {"ELEV": UnitIn("LEN_UNIT")}
    assert field_datums(BaseFloodElevation) == {"ELEV": DatumIn("V_DATUM")}


def test_the_numeric_null_is_a_missing_elevation(
    bfe_cases: list[dict[str, Any]],
) -> None:
    feature = a_valid_line(bfe_cases)
    feature["properties"]["ELEV"] = -9999
    assert rejected(feature) == {"ELEV"}


def test_a_multipart_line_is_rejected(bfe_cases: list[dict[str, Any]]) -> None:
    # "Each BFE is represented by a single line with no pseudo-nodes."
    feature = a_valid_line(bfe_cases)
    line = feature["geometry"]["coordinates"]
    feature["geometry"] = {"type": "MultiLineString", "coordinates": [line, line]}
    assert rejected(feature) == {"geometry"}


def test_the_model_has_no_rules_and_the_census_counts_every_row(
    reader: SpecReader, bfe_layer: Layer
) -> None:
    assert ModelConstraint.get_model_constraints(BaseFloodElevation) == ()
    _, groups = reader.rule_groups(bfe_layer)
    census = take_census(BaseFloodElevation, groups)
    assert census.rules == ()
    assert census.total == reader.observed(bfe_layer)["total"] > 0
