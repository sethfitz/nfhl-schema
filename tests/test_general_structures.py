"""The generated General Structures model against real NFHL features."""

from __future__ import annotations

from typing import Any

import pytest
from overture.schema.system.model_constraint import ModelConstraint

from nfhl.models import GeneralStructure
from nfhl.models.enums import LEGACY_MEMBERS, CstStruct, StructTyp, TrueFalse
from nfhl.rule_counts import judge, rule_fields, take_census
from nfhl.spec_source import Layer, SpecReader

from .helpers import fixture_feature, legacy_warnings_by, rejected_by, validate_as

DESCRIPTION_RULE = "@require_if(struc_desc)"


def rejected(feature: dict[str, Any]) -> set[str]:
    return rejected_by(feature, GeneralStructure)


def warned(feature: dict[str, Any]) -> list[str]:
    """The fields `feature` holds a legacy value in, by the warnings they raise."""
    return [m.split("=")[0] for m in legacy_warnings_by(feature, GeneralStructure)]


@pytest.fixture
def bridge(structure_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real bridge that validates, to mutate."""
    return fixture_feature(structure_cases, "bridge")


@pytest.fixture
def contained(structure_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real structure containing the 1-percent flood, described."""
    return fixture_feature(structure_cases, "one_percent_contained")


def test_the_fixture_has_every_kind_of_case(
    structure_cases: list[dict[str, Any]],
) -> None:
    assert any(c["expect"] is None and not c["warns"] for c in structure_cases)
    assert any(c["warns"] for c in structure_cases)
    assert any(c["expect"] is not None for c in structure_cases)
    assert DESCRIPTION_RULE in {c["expect"] for c in structure_cases}


def test_each_real_structure_is_judged_as_recorded(
    structure_cases: list[dict[str, Any]],
) -> None:
    for case in structure_cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected(case["feature"]) == expected, case["name"]
        if case["expect"] is None:
            legacy = [case["warns"]] if case["warns"] else []
            assert warned(case["feature"]) == legacy, case["name"]


def test_judging_agrees_with_validation_on_every_real_structure(
    structure_cases: list[dict[str, Any]],
) -> None:
    for case in structure_cases:
        verdict = judge(GeneralStructure, case["feature"]["properties"])
        expected = {DESCRIPTION_RULE} if case["expect"] == DESCRIPTION_RULE else set()
        assert verdict.broken == expected, case["name"]


def test_a_valid_structure_reads_back_typed(bridge: dict[str, Any]) -> None:
    # Omitable hides the enums from mypy; the dump holds the members themselves.
    structure = validate_as(GeneralStructure, bridge).model_dump()
    assert structure["STRUCT_TYP"] is StructTyp.BRIDGE
    assert structure["SHOWN_FIRM"] in set(TrueFalse)
    assert structure["STRUCT_ID"]


@pytest.mark.parametrize(
    "field", ["DFIRM_ID", "VERSION_ID", "STRUCT_ID", "STRUCT_TYP", "SOURCE_CIT"]
)
def test_a_required_field_is_required(bridge: dict[str, Any], field: str) -> None:
    del bridge["properties"][field]
    assert rejected(bridge) == {field}


@pytest.mark.parametrize("field", ["STRUCT_ID", "STRUCT_TYP", "SOURCE_CIT"])
def test_an_empty_required_field_is_missing(bridge: dict[str, Any], field: str) -> None:
    bridge["properties"][field] = ""
    assert rejected(bridge) == {field}


def test_a_footnoted_requirement_is_optional(bridge: dict[str, Any]) -> None:
    # WTR_NM and SHOWN_FIRM are "R1": "Field is applicable for BLE database."
    for field in ("WTR_NM", "SHOWN_FIRM"):
        del bridge["properties"][field]
        assert rejected(bridge) == set(), field


@pytest.mark.parametrize("field", ["CST_STRUCT", "STRUCT_NM", "LOC_DESC", "STRUC_DESC"])
def test_a_field_required_if_applicable_is_optional(
    bridge: dict[str, Any], field: str
) -> None:
    bridge["properties"][field] = None
    assert rejected(bridge) == set()


@pytest.mark.parametrize("flag", ["T", "F", "U"])
def test_every_true_false_value_is_a_flag(bridge: dict[str, Any], flag: str) -> None:
    bridge["properties"]["SHOWN_FIRM"] = flag
    assert rejected(bridge) == set()


def test_a_lone_space_is_not_a_flag(bridge: dict[str, Any]) -> None:
    bridge["properties"]["SHOWN_FIRM"] = " "
    assert rejected(bridge) == {"SHOWN_FIRM"}


@pytest.mark.parametrize("name", [c.value for c in CstStruct])
def test_each_coastal_class_validates(bridge: dict[str, Any], name: str) -> None:
    bridge["properties"]["CST_STRUCT"] = name
    assert rejected(bridge) == set()


@pytest.mark.parametrize("value", [" ", "MISCELLANEOUS STRUCTURES"])
def test_a_coastal_class_outside_the_domain_is_rejected(
    bridge: dict[str, Any], value: str
) -> None:
    bridge["properties"]["CST_STRUCT"] = value
    assert rejected(bridge) == {"CST_STRUCT"}


@pytest.mark.parametrize("value", ["Brigdge", "Dike", "Spillway", " "])
def test_a_structure_type_outside_the_domain_is_rejected(
    bridge: dict[str, Any], value: str
) -> None:
    bridge["properties"]["STRUCT_TYP"] = value
    assert rejected(bridge) == {"STRUCT_TYP"}


def test_a_structure_type_in_the_wrong_case_is_rejected(
    contained: dict[str, Any],
) -> None:
    # The service folds case, so it reports these as the reference's own.
    contained["properties"]["STRUCT_TYP"] = "Floodway Contained In Structure"
    assert rejected(contained) == {"STRUCT_TYP"}
    contained["properties"]["STRUCT_TYP"] = "Floodway Contained in Structure"
    assert rejected(contained) == set()


@pytest.mark.parametrize(
    "legacy",
    [
        "1 Pct Annual Chance Flood Discharge Contained In Structure",
        "0.2 Pct Annual Chance Flood Discharge Contained In Structure",
        "Other / Misc Structure",
        # Admitted by decision: the service counts them under the `Pct` spelling.
        "1 PCT Annual Chance Flood Discharge Contained in Structure",
        "1 PCT Annual Chance Flood Discharge Contained In Structure",
        "1 PCT ANNUAL CHANCE FLOOD DISCHARGE CONTAINED IN STRUCTURE",
        "0.2 PCT Annual Chance Flood Discharge Contained in Structure",
        "0.2 PCT Annual Chance Flood Discharge Contained In Structure",
    ],
)
def test_a_legacy_structure_type_warns(bridge: dict[str, Any], legacy: str) -> None:
    bridge["properties"]["STRUCT_TYP"] = legacy
    assert rejected(bridge) == set()
    assert warned(bridge) == ["STRUCT_TYP"]
    assert StructTyp(legacy) in LEGACY_MEMBERS


def test_a_case_a_decision_does_not_list_is_rejected(bridge: dict[str, Any]) -> None:
    # The decision lists spellings; it does not fold case.
    bridge["properties"]["STRUCT_TYP"] = (
        "1 pct annual chance flood discharge contained in structure"
    )
    assert rejected(bridge) == {"STRUCT_TYP"}


def test_a_description_is_required_of_a_structure_that_contains_a_flood(
    contained: dict[str, Any],
) -> None:
    assert rejected(contained) == set()
    for value in (None, ""):
        contained["properties"]["STRUC_DESC"] = value
        assert rejected(contained) == {DESCRIPTION_RULE}, repr(value)
    del contained["properties"]["STRUC_DESC"]
    assert rejected(contained) == {DESCRIPTION_RULE}


@pytest.mark.parametrize(
    "contained_type",
    [
        "0.2-Percent-Annual-Chance Flood Discharge Contained in Structure",
        "1-Percent-Annual-Chance Flood Discharge Contained in Structure",
        "Floodway Contained in Structure",
    ],
)
def test_each_contained_in_structure_type_needs_a_description(
    bridge: dict[str, Any], contained_type: str
) -> None:
    bridge["properties"]["STRUC_DESC"] = None
    assert rejected(bridge) == set()
    bridge["properties"]["STRUCT_TYP"] = contained_type
    assert rejected(bridge) == {DESCRIPTION_RULE}


def test_a_lone_space_is_a_description(contained: dict[str, Any]) -> None:
    contained["properties"]["STRUC_DESC"] = " "
    assert rejected(contained) == set()


def test_the_rule_names_the_reference_types_not_the_legacy_spellings(
    contained: dict[str, Any],
) -> None:
    # 14,445 rows hold a `Pct` or `PCT` spelling and no description; a rule
    # that rejected them would reject a combination common enough that the
    # legacy policy admits.
    contained["properties"]["STRUC_DESC"] = None
    contained["properties"]["STRUCT_TYP"] = (
        "1 Pct Annual Chance Flood Discharge Contained In Structure"
    )
    assert rejected(contained) == set()
    assert warned(contained) == ["STRUCT_TYP"]


def test_a_multiline_structure_is_rejected(bridge: dict[str, Any]) -> None:
    line = bridge["geometry"]["coordinates"]
    bridge["geometry"] = {"type": "MultiLineString", "coordinates": [line, line]}
    assert rejected(bridge) == {"geometry"}


def test_a_structure_with_no_geometry_is_rejected(bridge: dict[str, Any]) -> None:
    bridge["geometry"] = None
    assert rejected(bridge) == {"geometry"}


def test_the_census_reads_the_type_by_value_and_the_description_by_text() -> None:
    fields = rule_fields(GeneralStructure)
    assert fields.by_value == ("STRUCT_TYP",)
    assert fields.by_text_populated == ("STRUC_DESC",)
    assert fields.by_populated == ()


def test_the_census_counts_the_description_rule(
    reader: SpecReader, structure_layer: Layer
) -> None:
    rules = {c.name for c in ModelConstraint.get_model_constraints(GeneralStructure)}
    assert rules == {DESCRIPTION_RULE}
    _, groups = reader.rule_groups(structure_layer)
    census = take_census(GeneralStructure, groups)
    assert census.total == reader.observed(structure_layer)["total"] > 0
    assert (
        census.any_broken == {r.rule: r.broken for r in census.rules}[DESCRIPTION_RULE]
    )
    assert census.any_broken > 0
