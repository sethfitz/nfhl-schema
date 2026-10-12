"""The generated Transect Baselines model against real NFHL features."""

from __future__ import annotations

from typing import Any

import pytest
from overture.schema.system.model_constraint import ModelConstraint

from nfhl.annotations import field_datums
from nfhl.models import TransectBaseline
from nfhl.models.enums import TsctBaslnTyp, VDatum
from nfhl.rule_counts import judge
from nfhl.spec_source import Layer, SpecReader

from .helpers import fixture_feature, legacy_warnings_by, rejected_by, validate_as

REQUIRED = [
    "DFIRM_ID",
    "VERSION_ID",
    "TBASELN_ID",
    "TBASE_TYP",
    "R_ST_DESC",
    "R_END_DESC",
    "V_DATUM",
    "WTR_NM",
    "SOURCE_CIT",
]


def rejected(feature: dict[str, Any]) -> set[str]:
    return rejected_by(feature, TransectBaseline)


def warned(feature: dict[str, Any]) -> list[str]:
    """The fields `feature` holds a legacy value in, by the warnings they raise."""
    return [m.split("=")[0] for m in legacy_warnings_by(feature, TransectBaseline)]


@pytest.fixture
def lidar(baseline_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real baseline that validates, to mutate in a test."""
    return fixture_feature(baseline_cases, "lidar_navd88")


def test_the_fixture_has_every_kind_of_case(
    baseline_cases: list[dict[str, Any]],
) -> None:
    assert any(c["expect"] is None and not c["warns"] for c in baseline_cases)
    assert any(c["warns"] for c in baseline_cases)
    assert any(c["expect"] is not None for c in baseline_cases)


def test_each_real_baseline_is_judged_as_recorded(
    baseline_cases: list[dict[str, Any]],
) -> None:
    for case in baseline_cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected(case["feature"]) == expected, case["name"]
        if case["expect"] is None:
            legacy = [case["warns"]] if case["warns"] else []
            assert warned(case["feature"]) == legacy, case["name"]


def test_the_model_has_no_rules_to_judge(
    baseline_cases: list[dict[str, Any]],
) -> None:
    assert ModelConstraint.get_model_constraints(TransectBaseline) == ()
    for case in baseline_cases:
        verdict = judge(TransectBaseline, case["feature"]["properties"])
        assert verdict.broken == set(), case["name"]


def test_a_valid_baseline_reads_back_typed(lidar: dict[str, Any]) -> None:
    # Omitable hides the enums from mypy; the dump holds the members themselves.
    baseline = validate_as(TransectBaseline, lidar).model_dump()
    assert baseline["TBASELN_ID"]
    assert baseline["CST_MDL_ID"]
    assert baseline["TBASE_TYP"] is TsctBaslnTyp.ZERO_FOOT_CONTOUR_LIDAR_SHOALS
    assert baseline["V_DATUM"] is VDatum.NAVD88


@pytest.mark.parametrize("field", REQUIRED)
def test_a_required_field_is_required(lidar: dict[str, Any], field: str) -> None:
    del lidar["properties"][field]
    assert rejected(lidar) == {field}


def test_the_model_id_is_optional(lidar: dict[str, Any]) -> None:
    # "A": required if applicable, "populated for new coastal studies"; a lone
    # space is text.
    for value in (None, "", " "):
        lidar["properties"]["CST_MDL_ID"] = value
        assert rejected(lidar) == set(), repr(value)
    del lidar["properties"]["CST_MDL_ID"]
    assert rejected(lidar) == set()


def test_the_datum_is_the_contours_and_no_field_is_measured_from_it() -> None:
    # "The vertical datum indicates the reference surface from which the
    # 0.0-foot contour is measured": the contour is the line, not a field.
    assert field_datums(TransectBaseline) == {}


def test_a_type_in_the_wrong_case_is_rejected(lidar: dict[str, Any]) -> None:
    # The 2016 Domain Tables reference's spelling, on 19 rows; the service's case
    # folding counts them as the 2024 one.
    lidar["properties"]["TBASE_TYP"] = "Zero Foot Contour Referenced To Tidal Datum"
    assert rejected(lidar) == {"TBASE_TYP"}


@pytest.mark.parametrize(
    "value", ["Zero Foot Contour", "NON-ERODIBLE BLUFF", "ZERO FOOT C"]
)
def test_a_legacy_type_warns(lidar: dict[str, Any], value: str) -> None:
    lidar["properties"]["TBASE_TYP"] = value
    assert rejected(lidar) == set()
    assert warned(lidar) == ["TBASE_TYP"]


def test_the_threshold_selects_three_types_and_not_the_2016_spelling(
    reader: SpecReader, baseline_layer: Layer
) -> None:
    # The snapshot folds case, so it counts the 2016 `Referenced To` (19 rows)
    # with the reference's `Referenced to` (5) and the threshold cannot see it.
    selected = {v.value: v.count for v in reader.legacy_candidates(baseline_layer)}
    assert selected == {
        "Zero Foot Contour": 926,
        "NON-ERODIBLE BLUFF": 347,
        "ZERO FOOT C": 54,
    }
    observed = reader.observed(baseline_layer)["fields"]["TBASE_TYP"]
    assert {"value": "Zero Foot Contour Referenced to Tidal Datum", "count": 24} in (
        observed
    )


def test_a_shoreline_type_under_the_bar_is_rejected(lidar: dict[str, Any]) -> None:
    # D_Shr_Typ's `Sandy Beach-Small Dune`, upper-cased, on 13 rows.
    lidar["properties"]["TBASE_TYP"] = "SANDY BEACH-SMALL DUNE"
    assert rejected(lidar) == {"TBASE_TYP"}


def test_a_multipart_baseline_is_rejected(lidar: dict[str, Any]) -> None:
    # Table 4 holds S_Tsct_Basln to "Must Be Single Part".
    line = lidar["geometry"]["coordinates"]
    lidar["geometry"] = {"type": "MultiLineString", "coordinates": [line, line]}
    assert rejected(lidar) == {"geometry"}


def test_a_baseline_with_no_geometry_is_rejected(lidar: dict[str, Any]) -> None:
    lidar["geometry"] = None
    assert rejected(lidar) == {"geometry"}
