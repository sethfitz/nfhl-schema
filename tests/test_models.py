"""The generated model against real NFHL features."""

from __future__ import annotations

import json
import warnings
from typing import Any

import pytest
from overture.schema.system.model_constraint import ModelConstraint
from pydantic import ValidationError

from nfhl.annotations import DatumIn, UnitIn, field_datums, field_units
from nfhl.legacy import LegacyValueWarning
from nfhl.models import FloodHazardZone
from nfhl.models.enums import LEGACY_MEMBERS, LengthUnits, StudyTyp, Zone
from nfhl.spec_source import Layer, SpecReader


def validate(feature: dict[str, Any]) -> FloodHazardZone:
    # From JSON text, never a dict: the Feature envelope unwraps only in JSON mode.
    return FloodHazardZone.model_validate_json(json.dumps(feature))


def legacy_warnings(feature: dict[str, Any]) -> list[str]:
    """The LegacyValueWarning messages validating `feature` raises."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        validate(feature)
    return [
        str(w.message) for w in caught if issubclass(w.category, LegacyValueWarning)
    ]


def rejected_by(feature: dict[str, Any]) -> set[str]:
    """Wire field names (or rule names) that reject `feature`; empty if it is valid."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", LegacyValueWarning)
            validate(feature)
    except ValidationError as e:
        return {
            str(err["loc"][0]) if err["loc"] else err["msg"].split("`")[-2]
            for err in e.errors()
        }
    return set()


def test_the_fixture_has_both_kinds_of_case(cases: list[dict[str, Any]]) -> None:
    # A did-happen control: an all-valid or all-rejected fixture tests half.
    assert any(c["expect"] is None for c in cases)
    assert any(c["expect"] is not None for c in cases)


def test_each_real_feature_is_judged_as_recorded(cases: list[dict[str, Any]]) -> None:
    for case in cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected_by(case["feature"]) == expected, case["name"]
        if case["expect"] is None:
            warned = [m.split("=")[0] for m in legacy_warnings(case["feature"])]
            assert warned == ([case["warns"]] if case["warns"] else []), case["name"]


def test_the_fixture_has_warned_cases(cases: list[dict[str, Any]]) -> None:
    assert any(c["warns"] for c in cases)


def test_a_legacy_value_validates_with_a_warning(
    valid_feature: dict[str, Any],
) -> None:
    valid_feature["properties"]["STUDY_TYP"] = "SFHAs WITH HIGH FLOOD RISK"
    with pytest.warns(LegacyValueWarning, match="STUDY_TYP='SFHAs WITH HIGH"):
        zone = validate(valid_feature)
    assert zone.study_typ is StudyTyp.SFHAS_WITH_HIGH_FLOOD_RISK
    assert zone.study_typ in LEGACY_MEMBERS


def test_a_reference_value_validates_without_a_warning(
    valid_feature: dict[str, Any],
) -> None:
    assert valid_feature["properties"]["STUDY_TYP"] == "SFHA with BFE and floodway"
    assert legacy_warnings(valid_feature) == []


def test_a_value_neither_listed_nor_legacy_is_still_rejected(
    valid_feature: dict[str, Any],
) -> None:
    # Observed 1,485 times, under the threshold, and FRD-only in the reference.
    valid_feature["properties"]["STUDY_TYP"] = "OTHER"
    assert rejected_by(valid_feature) == {"STUDY_TYP"}
    valid_feature["properties"]["STUDY_TYP"] = "SFHAs WITH NO FLOOD RISK"
    assert rejected_by(valid_feature) == {"STUDY_TYP"}


def test_legacy_warnings_can_be_made_errors(valid_feature: dict[str, Any]) -> None:
    valid_feature["properties"]["ZONE_SUBTY"] = (
        "AREA WITH REDUCED FLOOD RISK DUE TO LEVEE"
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error", LegacyValueWarning)
        with pytest.raises(LegacyValueWarning):
            validate(valid_feature)


def test_an_unknown_flood_zone_is_rejected(valid_feature: dict[str, Any]) -> None:
    assert rejected_by(valid_feature) == set()
    valid_feature["properties"]["FLD_ZONE"] = "Q"
    assert rejected_by(valid_feature) == {"FLD_ZONE"}


def test_a_coded_value_is_not_a_published_value(valid_feature: dict[str, Any]) -> None:
    # D_Zone's coded value for open water is OW; data carries OPEN WATER.
    valid_feature["properties"]["FLD_ZONE"] = "OW"
    assert rejected_by(valid_feature) == {"FLD_ZONE"}


def test_a_missing_required_field_is_rejected(valid_feature: dict[str, Any]) -> None:
    del valid_feature["properties"]["SOURCE_CIT"]
    assert rejected_by(valid_feature) == {"SOURCE_CIT"}


def test_the_reference_null_encodings_read_as_absent(
    valid_feature: dict[str, Any],
) -> None:
    props = valid_feature["properties"]
    assert props["DEPTH"] == -9999 and props["VEL_UNIT"] is None
    props["ZONE_SUBTY"] = ""
    zone = validate(valid_feature)
    dumped = json.loads(zone.model_dump_json())["properties"]
    for wire in ("DEPTH", "VEL_UNIT", "ZONE_SUBTY", "VELOCITY"):
        assert wire not in dumped, wire
    assert dumped["STATIC_BFE"] == props["STATIC_BFE"]


def test_an_empty_required_field_is_missing(valid_feature: dict[str, Any]) -> None:
    valid_feature["properties"]["STUDY_TYP"] = ""
    assert rejected_by(valid_feature) == {"STUDY_TYP"}


def test_a_numeric_null_in_a_text_field_is_not_forgiven(
    valid_feature: dict[str, Any],
) -> None:
    valid_feature["properties"]["V_DATUM"] = "-9999"
    assert rejected_by(valid_feature) == {"V_DATUM"}


def test_values_parse_to_their_enums(valid_feature: dict[str, Any]) -> None:
    zone = validate(valid_feature)
    assert zone.fld_zone is Zone.AE
    len_unit: object = zone.len_unit  # mypy cannot see past `Omitable`
    assert len_unit is LengthUnits.FEET


def test_service_only_fields_are_kept_as_extras(valid_feature: dict[str, Any]) -> None:
    zone = validate(valid_feature)
    assert zone.model_extra is not None
    assert "GlobalID" in zone.model_extra


def test_units_and_datum_are_declared_on_the_measured_fields() -> None:
    assert field_units(FloodHazardZone) == {
        "STATIC_BFE": UnitIn("LEN_UNIT"),
        "DEPTH": UnitIn("LEN_UNIT"),
        "VELOCITY": UnitIn("VEL_UNIT"),
    }
    assert field_datums(FloodHazardZone) == {"STATIC_BFE": DatumIn("V_DATUM")}


@pytest.mark.parametrize(
    ("change", "rule"),
    [
        # Only the first failing rule is reported, so each case breaks one.
        ({"STATIC_BFE": -9999, "DEPTH": 2.0}, "@forbid_if(v_datum)"),
        ({"STATIC_BFE": -9999, "V_DATUM": None}, "@forbid_if(len_unit)"),
        ({"VELOCITY": 2.5}, "@require_if(vel_unit)"),
    ],
)
def test_each_relationship_rule_fires(
    valid_feature: dict[str, Any], change: dict[str, Any], rule: str
) -> None:
    valid_feature["properties"].update(change)
    assert rejected_by(valid_feature) == {rule}


SFHA_ZONES = "A, A99, AE, AH, AO, AR, V, VE"


@pytest.mark.parametrize(
    ("change", "rule"),
    [
        # Table 14 lists COASTAL FLOODPLAIN for A, AE, V and VE, not for AH.
        ({"FLD_ZONE": "AH", "ZONE_SUBTY": "COASTAL FLOODPLAIN"}, "[AH]"),
        # Table 14 has no <NULL> in the X row: an X zone names its subtype.
        ({"FLD_ZONE": "X", "SFHA_TF": "F"}, "@require_if(zone_subty) [A99, AR, X]"),
        ({"SFHA_TF": "F"}, f"@require_any_true(sfha_tf) [{SFHA_ZONES}]"),
        (
            {
                "FLD_ZONE": "X",
                "ZONE_SUBTY": "AREA OF MINIMAL FLOOD HAZARD",
                "SFHA_TF": "U",
            },
            "@require_any_true(sfha_tf) [D, X]",
        ),
    ],
)
def test_each_zone_rule_fires(
    valid_feature: dict[str, Any], change: dict[str, Any], rule: str
) -> None:
    valid_feature["properties"].update(change)
    (reported,) = rejected_by(valid_feature)
    assert reported.endswith(rule)


def test_a_zone_rule_allows_what_the_crosswalk_lists(
    valid_feature: dict[str, Any],
) -> None:
    valid_feature["properties"].update(FLD_ZONE="AH", ZONE_SUBTY=None)
    assert rejected_by(valid_feature) == set()
    valid_feature["properties"].update(
        FLD_ZONE="AO", ZONE_SUBTY="FLOODWAY", STATIC_BFE=-9999, V_DATUM=None
    )
    valid_feature["properties"].update(DEPTH=1.0)
    assert rejected_by(valid_feature) == set()


def test_the_crosswalk_does_not_judge_a_legacy_subtype(
    valid_feature: dict[str, Any],
) -> None:
    # Table 14 lists reference subtypes only; the legacy value's own warning
    # is all it gets, whatever the zone.
    valid_feature["properties"]["ZONE_SUBTY"] = (
        "AREA WITH REDUCED FLOOD RISK DUE TO LEVEE"
    )
    assert rejected_by(valid_feature) == set()
    assert len(legacy_warnings(valid_feature)) == 1


def test_open_water_takes_no_sfha_rule(valid_feature: dict[str, Any]) -> None:
    # Neither sentence of SFHA_TF's description names OPEN WATER.
    for flag in ("T", "F", "U"):
        valid_feature["properties"].update(FLD_ZONE="OPEN WATER", SFHA_TF=flag)
        assert rejected_by(valid_feature) == set(), flag


def test_every_pair_rule_is_a_constraint_on_the_model(
    reader: SpecReader, layer: Layer
) -> None:
    names = {c.name for c in ModelConstraint.get_model_constraints(FloodHazardZone)}
    rules = reader.pair_rules(layer.table)
    assert rules
    for rule in rules:
        assert any(n.endswith(f"[{', '.join(rule.when_values)}]") for n in names)


def test_a_unit_with_a_depth_but_no_bfe_is_allowed(
    valid_feature: dict[str, Any],
) -> None:
    valid_feature["properties"].update(STATIC_BFE=-9999, V_DATUM=None, DEPTH=2.0)
    assert rejected_by(valid_feature) == set()
