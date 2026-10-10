"""The generated Levees model against real NFHL features."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from overture.schema.system.model_constraint import ModelConstraint

from nfhl.annotations import UnitIn, field_datums, field_units
from nfhl.constraints import NULL_DATE
from nfhl.models import Levee
from nfhl.models.enums import LEGACY_MEMBERS, LeveeStatus, TrueFalse
from nfhl.rule_counts import judge, rule_fields, take_census
from nfhl.spec_source import Layer, SpecReader

from .helpers import fixture_feature, legacy_warnings_by, rejected_by, validate_as

ANALYSIS_RULE = "@forbid_if(lev_an_typ)"
DISTRICT_RULE = "@require_if(district)"
NOT_POPULATED_DATE = 218_330_035_200_000  # 8/8/8888, as the service writes it


def rejected(feature: dict[str, Any]) -> set[str]:
    return rejected_by(feature, Levee)


def warned(feature: dict[str, Any]) -> list[str]:
    """The fields `feature` holds a legacy value in, by the warnings they raise."""
    return [m.split("=")[0] for m in legacy_warnings_by(feature, Levee)]


@pytest.fixture
def usace(levee_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real accredited USACE levee that validates, to mutate."""
    return fixture_feature(levee_cases, "usace_accredited")


def test_the_fixture_has_every_kind_of_case(
    levee_cases: list[dict[str, Any]],
) -> None:
    assert any(c["expect"] is None and not c["warns"] for c in levee_cases)
    assert any(c["warns"] for c in levee_cases)
    assert any(c["expect"] is not None for c in levee_cases)
    assert {ANALYSIS_RULE, DISTRICT_RULE} <= {c["expect"] for c in levee_cases}


def test_each_real_levee_is_judged_as_recorded(
    levee_cases: list[dict[str, Any]],
) -> None:
    for case in levee_cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected(case["feature"]) == expected, case["name"]
        if case["expect"] is None:
            legacy = [case["warns"]] if case["warns"] else []
            assert warned(case["feature"]) == legacy, case["name"]


def test_judging_agrees_with_validation_on_every_real_levee(
    levee_cases: list[dict[str, Any]],
) -> None:
    for case in levee_cases:
        verdict = judge(Levee, case["feature"]["properties"])
        if case["expect"] in {ANALYSIS_RULE, DISTRICT_RULE}:
            assert verdict.broken == {case["expect"]}, case["name"]
        else:
            assert verdict.broken == set(), case["name"]


def test_a_valid_levee_reads_back_typed(usace: dict[str, Any]) -> None:
    # Omitable hides the enums from mypy; the dump holds the members themselves.
    levee = validate_as(Levee, usace).model_dump()
    assert levee["LEVEE_STAT"] is LeveeStatus.ACCREDITED
    assert levee["USACE_LEV"] is TrueFalse.T
    assert levee["DISTRICT"]
    assert levee["FREEBOARD"] > 0
    assert isinstance(levee["CONST_DATE"], int)


def test_freeboard_is_in_the_levee_unit_and_has_no_datum() -> None:
    assert field_units(Levee) == {"FREEBOARD": UnitIn("LEN_UNIT")}
    assert field_datums(Levee) == {}


def test_the_segment_id_is_required(usace: dict[str, Any]) -> None:
    # "R", though its description limits it to levees in the NLD, which no field
    # records: 13,405 of 16,320 published levees lack it.
    for value in (None, ""):
        usace["properties"]["FC_SEG_ID"] = value
        assert rejected(usace) == {"FC_SEG_ID"}, repr(value)
    usace["properties"]["FC_SEG_ID"] = "NP"
    assert rejected(usace) == set()


@pytest.mark.parametrize("field", ["FC_SYS_ID", "SOURCE_CIT", "LEVEE_ID"])
def test_a_required_field_is_required(usace: dict[str, Any], field: str) -> None:
    del usace["properties"][field]
    assert rejected(usace) == {field}


def test_a_footnoted_requirement_is_optional(usace: dict[str, Any]) -> None:
    # LEVEE_NM, LEVEE_TYP, WTR_NM, BANK_LOC, USACE_LEV, PL84_99TF, LEVEE_STAT and
    # OWNER are "R1": "Field is applicable for BLE database."
    footnoted = (
        "LEVEE_NM",
        "LEVEE_TYP",
        "WTR_NM",
        "BANK_LOC",
        "USACE_LEV",
        "PL84_99TF",
        "LEVEE_STAT",
        "OWNER",
    )
    for field in footnoted:
        feature = copy.deepcopy(usace)
        del feature["properties"][field]
        # Without a status the analysis rule has nothing to allow, and without a
        # USACE flag the district rule has nothing to require.
        assert rejected(feature) == set(), field


def test_the_district_is_required_for_a_usace_levee(usace: dict[str, Any]) -> None:
    for value in (None, ""):
        usace["properties"]["DISTRICT"] = value
        assert rejected(usace) == {DISTRICT_RULE}, repr(value)
    usace["properties"]["DISTRICT"] = "NP"
    assert rejected(usace) == set()
    usace["properties"]["USACE_LEV"] = "F"
    usace["properties"]["DISTRICT"] = None
    assert rejected(usace) == set()


def test_the_district_is_a_name_not_its_code(usace: dict[str, Any]) -> None:
    for value in ("1027", "KANSAS CITY", " "):
        usace["properties"]["DISTRICT"] = value
        assert rejected(usace) == {"DISTRICT"}, repr(value)


def test_the_analysis_type_is_for_non_accredited_levees(
    usace: dict[str, Any],
) -> None:
    usace["properties"]["LEV_AN_TYP"] = "Natural Valley"
    assert rejected(usace) == {ANALYSIS_RULE}
    usace["properties"]["LEVEE_STAT"] = "Non-Accredited"
    assert rejected(usace) == set()
    del usace["properties"]["LEVEE_STAT"]
    assert rejected(usace) == {ANALYSIS_RULE}


@pytest.mark.parametrize("status", ["Accredited", "Never Accredited", "NP", None])
def test_not_populated_is_no_analysis_type(
    usace: dict[str, Any], status: str | None
) -> None:
    # Section 7.3's `NP` says the field was intentionally left empty.
    usace["properties"]["LEVEE_STAT"] = status
    usace["properties"]["LEV_AN_TYP"] = "NP"
    assert rejected(usace) == set()


def test_a_legacy_status_warns_and_leaves_the_analysis_rule_alone(
    usace: dict[str, Any],
) -> None:
    usace["properties"]["LEVEE_STAT"] = "De-Accredited"
    assert rejected(usace) == set()
    assert warned(usace) == ["LEVEE_STAT"]
    assert LeveeStatus.DE_ACCREDITED in LEGACY_MEMBERS
    usace["properties"]["LEV_AN_TYP"] = "Other"
    assert rejected(usace) == {ANALYSIS_RULE}


def test_the_null_date_is_not_populated_and_the_not_populated_date_is_a_value(
    usace: dict[str, Any],
) -> None:
    assert NULL_DATE == 253_392_451_200_000  # 9/9/9999
    usace["properties"]["CONST_DATE"] = NULL_DATE
    usace["properties"]["PAL_DATE"] = NOT_POPULATED_DATE
    levee = validate_as(Levee, usace).model_dump()
    assert "CONST_DATE" not in levee
    assert levee["PAL_DATE"] == NOT_POPULATED_DATE


def test_a_date_is_milliseconds_since_the_epoch(usace: dict[str, Any]) -> None:
    usace["properties"]["CONST_DATE"] = "9/9/9999"
    assert rejected(usace) == {"CONST_DATE"}
    usace["properties"]["CONST_DATE"] = -2_208_988_791_000  # 1900-01-01, as published
    assert rejected(usace) == set()


def test_a_multiline_levee_is_rejected(usace: dict[str, Any]) -> None:
    line = usace["geometry"]["coordinates"]
    usace["geometry"] = {"type": "MultiLineString", "coordinates": [line, line]}
    assert rejected(usace) == {"geometry"}


def test_a_levee_with_no_geometry_is_rejected(usace: dict[str, Any]) -> None:
    usace["geometry"] = None
    assert rejected(usace) == {"geometry"}


def test_the_census_reads_the_status_and_the_flag_with_their_dependants() -> None:
    fields = rule_fields(Levee)
    assert fields.by_value == ("USACE_LEV", "DISTRICT", "LEVEE_STAT", "LEV_AN_TYP")
    assert fields.by_populated == () == fields.by_text_populated


def test_the_census_counts_the_levee_rules(
    reader: SpecReader, levee_layer: Layer
) -> None:
    rules = {c.name for c in ModelConstraint.get_model_constraints(Levee)}
    assert rules == {ANALYSIS_RULE, DISTRICT_RULE}
    _, groups = reader.rule_groups(levee_layer)
    census = take_census(Levee, groups)
    assert census.total == reader.observed(levee_layer)["total"] > 0
    assert {r.rule: r.broken for r in census.rules} == {
        DISTRICT_RULE: 151,
        ANALYSIS_RULE: 44,
    }
    assert census.any_broken == 194
