"""The generated FIRM Panels model against real NFHL features."""

from __future__ import annotations

from typing import Any

import pytest
from overture.schema.system.model_constraint import ModelConstraint

from nfhl.models import FirmPanel
from nfhl.models.enums import LEGACY_MEMBERS, PanelTyp, StateFIPS
from nfhl.rule_counts import judge, rule_fields, take_census
from nfhl.spec_source import Layer, SpecReader

from .helpers import fixture_feature, legacy_warnings_by, rejected_by, validate_as

PNP_RULE = "@forbid_if(pnp_reason)"


def rejected(feature: dict[str, Any]) -> set[str]:
    return rejected_by(feature, FirmPanel)


def warned(feature: dict[str, Any]) -> list[str]:
    """The fields `feature` holds a legacy value in, by the warnings they raise."""
    return [m.split("=")[0] for m in legacy_warnings_by(feature, FirmPanel)]


@pytest.fixture
def printed(panel_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real printed panel that validates, to mutate."""
    return fixture_feature(panel_cases, "countywide_printed")


@pytest.fixture
def not_printed(panel_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real panel not printed, with its reason."""
    return fixture_feature(panel_cases, "countywide_not_printed")


def test_the_fixture_has_every_kind_of_case(panel_cases: list[dict[str, Any]]) -> None:
    assert any(c["expect"] is None and not c["warns"] for c in panel_cases)
    assert any(c["warns"] for c in panel_cases)
    assert any(c["expect"] is not None for c in panel_cases)
    assert PNP_RULE in {c["expect"] for c in panel_cases}


def test_each_real_panel_is_judged_as_recorded(
    panel_cases: list[dict[str, Any]],
) -> None:
    for case in panel_cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected(case["feature"]) == expected, case["name"]
        if case["expect"] is None:
            legacy = [case["warns"]] if case["warns"] else []
            assert warned(case["feature"]) == legacy, case["name"]


def test_judging_agrees_with_validation_on_every_real_panel(
    panel_cases: list[dict[str, Any]],
) -> None:
    for case in panel_cases:
        verdict = judge(FirmPanel, case["feature"]["properties"])
        expected = {PNP_RULE} if case["expect"] == PNP_RULE else set()
        assert verdict.broken == expected, case["name"]


def test_a_valid_panel_reads_back_typed(printed: dict[str, Any]) -> None:
    # Omitable hides the enums from mypy; the dump holds the members themselves.
    panel = validate_as(FirmPanel, printed).model_dump()
    assert panel["PANEL_TYP"] is PanelTyp.COUNTYWIDE_PANEL_PRINTED
    assert isinstance(panel["ST_FIPS"], StateFIPS)
    assert (
        panel["FIRM_PAN"]
        == panel["ST_FIPS"] + panel["PCOMM"] + panel["PANEL"] + (panel["SUFFIX"])
    )


@pytest.mark.parametrize(
    "field",
    [
        "DFIRM_ID",
        "VERSION_ID",
        "FIRM_ID",
        "ST_FIPS",
        "PCOMM",
        "PANEL",
        "SUFFIX",
        "FIRM_PAN",
        "PANEL_TYP",
        "SCALE",
        "BASE_TYP",
        "SOURCE_CIT",
    ],
)
def test_a_required_field_is_required(printed: dict[str, Any], field: str) -> None:
    del printed["properties"][field]
    assert rejected(printed) == {field}


@pytest.mark.parametrize("field", ["PRE_DATE", "EFF_DATE", "PNP_REASON"])
def test_a_field_required_if_applicable_is_optional(
    printed: dict[str, Any], field: str
) -> None:
    printed["properties"][field] = None
    assert rejected(printed) == set()


# Arizona's 4 is under the legacy threshold, admitted by decision
# (spec/legacy.json).
@pytest.mark.parametrize("code", ["5", "1", "6", "8", "4"])
def test_an_unpadded_state_warns(printed: dict[str, Any], code: str) -> None:
    printed["properties"]["ST_FIPS"] = code
    assert rejected(printed) == set()
    assert warned(printed) == ["ST_FIPS"]
    assert StateFIPS(code) in LEGACY_MEMBERS


def test_the_scale_is_one_of_the_reference_denominators(
    printed: dict[str, Any],
) -> None:
    printed["properties"]["SCALE"] = "4800"
    assert rejected(printed) == {"SCALE"}
    printed["properties"]["SCALE"] = "12000"
    assert rejected(printed) == set()


def test_not_populated_is_a_base_map_type(printed: dict[str, Any]) -> None:
    # D_Basemap_Typ lists `NP`; D_Scale does not.
    printed["properties"]["BASE_TYP"] = "NP"
    assert rejected(printed) == set()
    printed["properties"]["SCALE"] = "NP"
    assert rejected(printed) == {"SCALE"}


@pytest.mark.parametrize("panel_type", ["Community B", "Countywide, Panel Not Printed"])
def test_a_misspelled_panel_type_is_rejected(
    printed: dict[str, Any], panel_type: str
) -> None:
    printed["properties"]["PANEL_TYP"] = panel_type
    assert rejected(printed) == {"PANEL_TYP"}


def test_a_reason_is_given_only_for_a_panel_not_printed(
    printed: dict[str, Any], not_printed: dict[str, Any]
) -> None:
    assert rejected(not_printed) == set()
    printed["properties"]["PNP_REASON"] = not_printed["properties"]["PNP_REASON"]
    assert rejected(printed) == {PNP_RULE}


@pytest.mark.parametrize("kind", ["Countywide", "Community Based", "Statewide"])
def test_each_kind_of_panel_not_printed_may_give_a_reason(
    not_printed: dict[str, Any], kind: str
) -> None:
    not_printed["properties"]["PANEL_TYP"] = f"{kind}, Not Printed"
    assert rejected(not_printed) == set()


@pytest.mark.parametrize("kind", ["Unmapped Community", "Statewide, Panel Printed"])
def test_a_reason_on_any_other_panel_breaks_the_rule(
    not_printed: dict[str, Any], kind: str
) -> None:
    not_printed["properties"]["PANEL_TYP"] = kind
    assert rejected(not_printed) == {PNP_RULE}


def test_a_lone_space_is_a_reason_and_an_empty_string_is_none(
    printed: dict[str, Any],
) -> None:
    printed["properties"]["PNP_REASON"] = ""
    assert rejected(printed) == set()
    printed["properties"]["PNP_REASON"] = " "
    assert rejected(printed) == {PNP_RULE}


def test_a_multipart_panel_is_one_feature(printed: dict[str, Any]) -> None:
    # Table 4 holds S_FIRM_Pan to no "Must Be Single Part".
    polygon = printed["geometry"]["coordinates"]
    printed["geometry"] = {"type": "MultiPolygon", "coordinates": [polygon, polygon]}
    assert rejected(printed) == set()


def test_a_panel_with_no_geometry_is_rejected(printed: dict[str, Any]) -> None:
    printed["geometry"] = None
    assert rejected(printed) == {"geometry"}


def test_the_census_reads_the_panel_type_by_value_and_the_reason_by_text() -> None:
    fields = rule_fields(FirmPanel)
    assert fields.by_value == ("PANEL_TYP",)
    assert fields.by_text_populated == ("PNP_REASON",)
    assert fields.by_populated == ()


def test_the_census_counts_the_reason_rule(
    reader: SpecReader, panel_layer: Layer
) -> None:
    rules = {c.name for c in ModelConstraint.get_model_constraints(FirmPanel)}
    assert rules == {PNP_RULE}
    _, groups = reader.rule_groups(panel_layer)
    census = take_census(FirmPanel, groups)
    assert census.total == reader.observed(panel_layer)["total"] > 0
    assert {r.rule: r.broken for r in census.rules} == {PNP_RULE: 6_688}
    assert census.any_broken == 6_688
