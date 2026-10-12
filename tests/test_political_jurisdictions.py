"""The generated Political Jurisdictions model against real NFHL features."""

from __future__ import annotations

from typing import Any

import pytest
from overture.schema.system.model_constraint import ModelConstraint

from nfhl.models import PoliticalJurisdiction
from nfhl.models.enums import LEGACY_MEMBERS, StateFIPS, TrueFalse
from nfhl.rule_counts import judge, rule_fields, take_census
from nfhl.spec_source import Layer, SpecReader

from .helpers import fixture_feature, legacy_warnings_by, rejected_by, validate_as

ANI_FIRM_RULE = "@forbid_if(ani_firm)"


def rejected(feature: dict[str, Any]) -> set[str]:
    return rejected_by(feature, PoliticalJurisdiction)


def warned(feature: dict[str, Any]) -> list[str]:
    """The fields `feature` holds a legacy value in, by the warnings they raise."""
    return [m.split("=")[0] for m in legacy_warnings_by(feature, PoliticalJurisdiction)]


@pytest.fixture
def area(jurisdiction_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real political area on the FIRM that validates, to mutate."""
    return fixture_feature(jurisdiction_cases, "included")


@pytest.fixture
def ani_area(jurisdiction_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real Area Not Included, mapped in another FIRM."""
    return fixture_feature(jurisdiction_cases, "ani_in_another_firm")


def test_the_fixture_has_every_kind_of_case(
    jurisdiction_cases: list[dict[str, Any]],
) -> None:
    assert any(c["expect"] is None and not c["warns"] for c in jurisdiction_cases)
    assert any(c["warns"] for c in jurisdiction_cases)
    assert any(c["expect"] is not None for c in jurisdiction_cases)
    assert ANI_FIRM_RULE in {c["expect"] for c in jurisdiction_cases}


def test_each_real_area_is_judged_as_recorded(
    jurisdiction_cases: list[dict[str, Any]],
) -> None:
    for case in jurisdiction_cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected(case["feature"]) == expected, case["name"]
        if case["expect"] is None:
            legacy = [case["warns"]] if case["warns"] else []
            assert warned(case["feature"]) == legacy, case["name"]


def test_judging_agrees_with_validation_on_every_real_area(
    jurisdiction_cases: list[dict[str, Any]],
) -> None:
    for case in jurisdiction_cases:
        verdict = judge(PoliticalJurisdiction, case["feature"]["properties"])
        expected = {ANI_FIRM_RULE} if case["expect"] == ANI_FIRM_RULE else set()
        assert verdict.broken == expected, case["name"]


def test_a_valid_area_reads_back_typed(area: dict[str, Any]) -> None:
    # Omitable hides the enums from mypy; the dump holds the members themselves.
    jurisdiction = validate_as(PoliticalJurisdiction, area).model_dump()
    assert jurisdiction["ANI_TF"] is TrueFalse.F
    assert isinstance(jurisdiction["ST_FIPS"], StateFIPS)
    assert jurisdiction["POL_AR_ID"]


@pytest.mark.parametrize(
    "field",
    [
        "DFIRM_ID",
        "VERSION_ID",
        "POL_AR_ID",
        "POL_NAME1",
        "CO_FIPS",
        "ST_FIPS",
        "COMM_NO",
        "CID",
        "ANI_TF",
        "SOURCE_CIT",
    ],
)
def test_a_required_field_is_required(area: dict[str, Any], field: str) -> None:
    del area["properties"][field]
    assert rejected(area) == {field}


@pytest.mark.parametrize("field", ["POL_NAME2", "POL_NAME3", "COM_NFO_ID"])
def test_a_field_required_if_applicable_is_optional(
    area: dict[str, Any], field: str
) -> None:
    area["properties"][field] = None
    assert rejected(area) == set()


def test_the_state_is_the_two_digit_code(area: dict[str, Any]) -> None:
    area["properties"]["ST_FIPS"] = "05"
    assert rejected(area) == set()
    area["properties"]["ST_FIPS"] = "Arkansas"
    assert rejected(area) == {"ST_FIPS"}


@pytest.mark.parametrize("code", ["5", "1", "6", "8"])
def test_a_common_unpadded_state_warns(area: dict[str, Any], code: str) -> None:
    area["properties"]["ST_FIPS"] = code
    assert rejected(area) == set()
    assert warned(area) == ["ST_FIPS"]
    assert StateFIPS(code) in LEGACY_MEMBERS


def test_a_rare_unpadded_state_is_rejected(area: dict[str, Any]) -> None:
    # Arizona's 04 without its zero is under the legacy threshold
    # (spec/service/observed/22.json has the count).
    area["properties"]["ST_FIPS"] = "4"
    assert rejected(area) == {"ST_FIPS"}


def test_another_firm_is_named_only_for_an_area_not_included(
    area: dict[str, Any], ani_area: dict[str, Any]
) -> None:
    assert rejected(ani_area) == set()
    area["properties"]["ANI_FIRM"] = ani_area["properties"]["ANI_FIRM"]
    assert rejected(area) == {ANI_FIRM_RULE}
    area["properties"]["ANI_TF"] = "U"
    assert rejected(area) == {ANI_FIRM_RULE}
    area["properties"]["ANI_TF"] = "T"
    assert rejected(area) == set()


@pytest.mark.parametrize("flag", ["T", "F", "U"])
def test_not_populated_is_no_other_firm(area: dict[str, Any], flag: str) -> None:
    # Section 7.3's `NP` says the field was intentionally left empty.
    area["properties"]["ANI_TF"] = flag
    area["properties"]["ANI_FIRM"] = "NP"
    assert rejected(area) == set()


@pytest.mark.parametrize("other_firm", ["F", " ", "0"])
def test_a_flag_or_a_blank_in_the_other_firm_breaks_the_rule(
    area: dict[str, Any], other_firm: str
) -> None:
    # The published values off an ANI area: a lone space is a value, not a null.
    area["properties"]["ANI_FIRM"] = other_firm
    assert rejected(area) == {ANI_FIRM_RULE}


def test_an_empty_other_firm_is_a_null(area: dict[str, Any]) -> None:
    area["properties"]["ANI_FIRM"] = ""
    assert rejected(area) == set()


def test_a_multipart_area_is_one_feature(area: dict[str, Any]) -> None:
    # Table 4 holds S_Pol_Ar to no "Must Be Single Part".
    polygon = area["geometry"]["coordinates"]
    area["geometry"] = {"type": "MultiPolygon", "coordinates": [polygon, polygon]}
    assert rejected(area) == set()


def test_an_area_with_no_geometry_is_rejected(area: dict[str, Any]) -> None:
    area["geometry"] = None
    assert rejected(area) == {"geometry"}


def test_the_census_reads_the_flag_and_the_other_firm_by_value() -> None:
    fields = rule_fields(PoliticalJurisdiction)
    assert fields.by_value == ("ANI_TF", "ANI_FIRM")
    assert fields.by_populated == () == fields.by_text_populated


def test_the_census_counts_the_ani_firm_rule(
    reader: SpecReader, jurisdiction_layer: Layer
) -> None:
    rules = {
        c.name for c in ModelConstraint.get_model_constraints(PoliticalJurisdiction)
    }
    assert rules == {ANI_FIRM_RULE}
    _, groups = reader.rule_groups(jurisdiction_layer)
    census = take_census(PoliticalJurisdiction, groups)
    assert census.total == reader.observed(jurisdiction_layer)["total"] > 0
    assert {r.rule: r.broken for r in census.rules} == {ANI_FIRM_RULE: 4_597}
    assert census.any_broken == 4_597
