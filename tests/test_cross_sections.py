"""The generated Cross-Sections model against real NFHL features."""

from __future__ import annotations

from typing import Any

from overture.schema.system.model_constraint import ModelConstraint

from nfhl.annotations import DatumIn, UnitIn, field_datums, field_units
from nfhl.models import CrossSection
from nfhl.models.enums import LengthUnits, VDatum, XSLnTyp
from nfhl.rule_counts import judge, rule_fields, take_census
from nfhl.spec_source import Layer, SpecReader

from .helpers import fixture_feature, rejected_by, validate_as

LETTER_RULE = "@forbid_if(xs_ltr)"


def rejected(feature: dict[str, Any]) -> set[str]:
    return rejected_by(feature, CrossSection)


def test_the_fixture_has_both_kinds_of_case(xs_cases: list[dict[str, Any]]) -> None:
    assert any(c["expect"] is None for c in xs_cases)
    assert any(c["expect"] is not None for c in xs_cases)


def test_each_real_section_is_judged_as_recorded(
    xs_cases: list[dict[str, Any]],
) -> None:
    for case in xs_cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected(case["feature"]) == expected, case["name"]


def test_judging_agrees_with_validation_on_every_real_section(
    xs_cases: list[dict[str, Any]],
) -> None:
    for case in xs_cases:
        verdict = judge(CrossSection, case["feature"]["properties"])
        if case["expect"] == LETTER_RULE:
            assert verdict.broken == {LETTER_RULE}, case["name"]
        else:
            assert verdict.broken == set(), case["name"]


def test_a_valid_section_reads_back_typed(xs_cases: list[dict[str, Any]]) -> None:
    section = validate_as(
        CrossSection, fixture_feature(xs_cases, "lettered_navd88_feet")
    )
    assert section.xs_ln_typ is XSLnTyp.LETTERED_MAPPED
    assert section.xs_ltr
    assert section.len_unit is LengthUnits.FEET
    assert section.v_datum is VDatum.NAVD88
    assert section.strmbed_el > 0


def test_both_elevations_are_in_len_unit_and_measured_from_v_datum() -> None:
    assert field_units(CrossSection) == {
        "WSEL_REG": UnitIn("LEN_UNIT"),
        "STRMBED_EL": UnitIn("LEN_UNIT"),
    }
    assert field_datums(CrossSection) == {
        "WSEL_REG": DatumIn("V_DATUM"),
        "STRMBED_EL": DatumIn("V_DATUM"),
    }


def test_a_footnoted_requirement_is_still_a_requirement(
    xs_cases: list[dict[str, Any]],
) -> None:
    # STREAM_STN, START_ID and XS_LN_TYP are "R1": required, with a footnote
    # on BLE databases.
    feature = fixture_feature(xs_cases, "unlettered")
    del feature["properties"]["XS_LN_TYP"]
    assert rejected(feature) == {"XS_LN_TYP"}


def test_a_letter_is_held_only_by_a_lettered_section(
    xs_cases: list[dict[str, Any]],
) -> None:
    feature = fixture_feature(xs_cases, "unlettered")
    feature["properties"]["XS_LTR"] = "A"
    assert rejected(feature) == {LETTER_RULE}
    feature["properties"]["XS_LN_TYP"] = "LETTERED, MAPPED"
    assert rejected(feature) == set()


def test_a_multipart_section_is_rejected(xs_cases: list[dict[str, Any]]) -> None:
    feature = fixture_feature(xs_cases, "unlettered")
    line = feature["geometry"]["coordinates"]
    feature["geometry"] = {"type": "MultiLineString", "coordinates": [line, line]}
    assert rejected(feature) == {"geometry"}


def test_the_census_groups_the_letter_by_whether_it_is_set() -> None:
    fields = rule_fields(CrossSection)
    assert (fields.by_value, fields.by_text_populated) == (("XS_LN_TYP",), ("XS_LTR",))


def test_the_census_counts_the_letter_rule(reader: SpecReader, xs_layer: Layer) -> None:
    (rule,) = ModelConstraint.get_model_constraints(CrossSection)
    assert rule.name == LETTER_RULE
    _, groups = reader.rule_groups(xs_layer)
    census = take_census(CrossSection, groups)
    assert census.total == reader.observed(xs_layer)["total"] > 0
    # 2,914 letters and 11,887 lone spaces on NOT LETTERED, MAPPED sections.
    assert census.any_broken == 14_801
    assert census.any_blocked == 0
