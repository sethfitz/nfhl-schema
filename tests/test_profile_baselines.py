"""The generated Profile Baselines model against real NFHL features."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from overture.schema.system.model_constraint import ModelConstraint

from nfhl.annotations import UnitIn, field_datums, field_units
from nfhl.models import ProfileBaseline
from nfhl.models.enums import LEGACY_MEMBERS, ProfBaslnTyp, StudyTyp, TrueFalse
from nfhl.rule_counts import judge, rule_fields, take_census
from nfhl.spec_source import Layer, SpecReader

from .helpers import fixture_feature, legacy_warnings_by, rejected_by, validate_as

# Each continuation field, with the fields that must be set before it may be.
CONTINUATIONS = {
    "FLD_PROB2": ("FLD_PROB1",),
    "FLD_PROB3": ("FLD_PROB1", "FLD_PROB2"),
    "SPEC_CONS2": ("SPEC_CONS1",),
}
CONTINUATION_RULES = {f"@forbid_if({f.lower()})" for f in CONTINUATIONS}
CONTINUATION_FIELDS = {
    "FLD_PROB1",
    "FLD_PROB2",
    "FLD_PROB3",
    "SPEC_CONS1",
    "SPEC_CONS2",
}


def rejected(feature: dict[str, Any]) -> set[str]:
    return rejected_by(feature, ProfileBaseline)


def warned(feature: dict[str, Any]) -> list[str]:
    """The fields `feature` holds a legacy value in, by the warnings they raise."""
    return [m.split("=")[0] for m in legacy_warnings_by(feature, ProfileBaseline)]


@pytest.fixture
def shown(profile_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real baseline that validates, to mutate in a test."""
    return fixture_feature(profile_cases, "profile_baseline_shown")


def test_the_fixture_has_every_kind_of_case(
    profile_cases: list[dict[str, Any]],
) -> None:
    assert any(c["expect"] is None and not c["warns"] for c in profile_cases)
    assert any(c["warns"] for c in profile_cases)
    assert any(c["expect"] is not None for c in profile_cases)


def test_each_real_baseline_is_judged_as_recorded(
    profile_cases: list[dict[str, Any]],
) -> None:
    for case in profile_cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected(case["feature"]) == expected, case["name"]
        if case["expect"] is None:
            legacy = [case["warns"]] if case["warns"] else []
            assert warned(case["feature"]) == legacy, case["name"]


def test_judging_agrees_with_validation_on_every_real_baseline(
    profile_cases: list[dict[str, Any]],
) -> None:
    for case in profile_cases:
        verdict = judge(ProfileBaseline, case["feature"]["properties"])
        if case["expect"] in CONTINUATION_RULES:
            assert verdict.broken == {case["expect"]}, case["name"]
        else:
            assert verdict.broken == set(), case["name"]


def test_a_valid_baseline_reads_back_typed(shown: dict[str, Any]) -> None:
    baseline = validate_as(ProfileBaseline, shown)
    assert baseline.water_typ is ProfBaslnTyp.PROFILE_BASELINE
    assert baseline.shown_firm is TrueFalse.T
    assert baseline.start_id


def test_the_datum_offset_is_in_datum_unit_and_has_no_datum() -> None:
    assert field_units(ProfileBaseline) == {"V_DATM_OFF": UnitIn("DATUM_UNIT")}
    assert field_datums(ProfileBaseline) == {}


def test_a_footnoted_requirement_is_still_a_requirement(shown: dict[str, Any]) -> None:
    # WATER_TYP, STUDY_TYP, SHOWN_FIRM, R_ST_DESC, R_END_DESC and START_ID are
    # "R1": required, with a footnote on BLE databases.
    for field in ("START_ID", "SHOWN_FIRM", "R_END_DESC"):
        feature = copy.deepcopy(shown)
        del feature["properties"][field]
        assert rejected(feature) == {field}


def test_shown_on_index_is_optional_and_unpublished(shown: dict[str, Any]) -> None:
    assert "SHOWN_INDX" not in shown["properties"]
    shown["properties"]["SHOWN_INDX"] = "F"
    baseline = validate_as(ProfileBaseline, shown)
    assert baseline.model_dump(mode="json")["properties"]["SHOWN_INDX"] == "F"


@pytest.mark.parametrize("then", CONTINUATIONS)
def test_a_continuation_needs_the_field_it_continues(
    shown: dict[str, Any], then: str
) -> None:
    for field in CONTINUATION_FIELDS:
        shown["properties"].pop(field, None)
    shown["properties"][then] = "continued"
    assert rejected(shown) == {f"@forbid_if({then.lower()})"}
    for first in CONTINUATIONS[then]:
        shown["properties"][first] = "the first part"
    assert rejected(shown) == set()


def test_a_multipart_baseline_is_rejected(shown: dict[str, Any]) -> None:
    line = shown["geometry"]["coordinates"]
    shown["geometry"] = {"type": "MultiLineString", "coordinates": [line, line]}
    assert rejected(shown) == {"geometry"}


def test_a_legacy_study_type_warns_on_this_layer_too(shown: dict[str, Any]) -> None:
    shown["properties"]["STUDY_TYP"] = "REDELINEATION"
    assert rejected(shown) == set()
    assert warned(shown) == ["STUDY_TYP"]


def test_a_value_legacy_on_two_layers_is_one_member_citing_both() -> None:
    member = StudyTyp.SFHAS_WITH_HIGH_FLOOD_RISK
    assert member in LEGACY_MEMBERS
    assert member.__doc__ is not None
    assert "layer 28" in member.__doc__
    assert "layer 17" in member.__doc__
    values = [m.value for m in StudyTyp]
    assert len(values) == len(set(values))


def test_the_census_groups_the_continued_text_by_whether_it_is_set() -> None:
    fields = rule_fields(ProfileBaseline)
    assert fields.by_value == ()
    assert set(fields.by_text_populated) == CONTINUATION_FIELDS


def test_the_census_counts_the_continuation_rules(
    reader: SpecReader, profile_layer: Layer
) -> None:
    rules = {c.name for c in ModelConstraint.get_model_constraints(ProfileBaseline)}
    assert rules == CONTINUATION_RULES
    _, groups = reader.rule_groups(profile_layer)
    census = take_census(ProfileBaseline, groups)
    assert census.total == reader.observed(profile_layer)["total"] > 0
    assert {r.rule: r.broken for r in census.rules} == {
        "@forbid_if(fld_prob2)": 218,
        "@forbid_if(fld_prob3)": 15,
        "@forbid_if(spec_cons2)": 142,
    }
    assert census.any_broken == 375
    assert census.any_blocked == 0
