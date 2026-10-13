"""The generated Coastal Transects model against real NFHL features."""

from __future__ import annotations

from typing import Any

import pytest
from overture.schema.system.model_constraint import ModelConstraint

from nfhl.annotations import UnitIn, field_datums, field_units
from nfhl.models import BaseFloodElevation, CoastalTransect
from nfhl.models.enums import Event, TimeUnits, VDatum
from nfhl.rule_counts import judge
from nfhl.spec_source import Layer, SpecReader

from .helpers import fixture_feature, legacy_warnings_by, rejected_by, validate_as

REQUIRED = [
    "DFIRM_ID",
    "VERSION_ID",
    "TRAN_LN_ID",
    "TBASELN_ID",
    "TRAN_NO",
    "XCOORD",
    "YCOORD",
    "WTR_NM",
    "V_DATUM",
    "CSTLN_TYP",
    "EVENT_TYP",
    "SWEL",
    "LOC_DESC",
    "RUP",
    "ELEV_UNIT",
    "WHAFIS_TF",
    "OVERTOP_TF",
    "BW_HGT_TF",
    "HVFLOW_TF",
    "WAVE_02PCT",
    "SOURCE_CIT",
]
OPTIONAL = [
    "METHOD",
    "DATUM_CONV",
    "BEACH_SET",
    "SHORE_TYP",
    "CST_MDL_ID",
    "SIG_HT",
    "SIG_PD",
    "CON_HT",
    "CON_PD",
    "MEAN_HT",
    "MEAN_PD",
    "FETCH_LEN",
    "FTCHLNUNIT",
    "EROS_METH",
    "LU_SOURCE",
    "VZONE_EXT",
    "SETUP_DPTH",
    "LEN_UNIT",
    "TIME_UNIT",
]
# Required numbers, which the reference writes -9999 for when missing.
NUMBERS = ["XCOORD", "YCOORD", "SWEL", "RUP"]
# Each value the threshold admits (spec/legacy.json), with its field.
LEGACY = [
    ("METHOD", "NP"),
    ("V_DATUM", "ASVD02"),
    ("V_DATUM", "GUVD03"),
    ("EVENT_TYP", "NP"),
    ("FTCHLNUNIT", "NA"),
    ("VZONE_EXT", "NP"),
    ("VZONE_EXT", "WHAFIS"),
    ("VZONE_EXT", "30 FOOT SPLASH ZONE BEHIND S"),
    ("VZONE_EXT", "RUNUP EXTENT"),
    ("LEN_UNIT", "NA"),
    ("TIME_UNIT", "NP"),
    ("TIME_UNIT", "NA"),
]


def rejected(feature: dict[str, Any]) -> set[str]:
    return rejected_by(feature, CoastalTransect)


def warned(feature: dict[str, Any]) -> list[str]:
    """The fields `feature` holds a legacy value in, by the warnings they raise."""
    return [m.split("=")[0] for m in legacy_warnings_by(feature, CoastalTransect)]


@pytest.fixture
def study(coastal_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real transect with every optional field populated, to
    mutate in a test."""
    return fixture_feature(coastal_cases, "full_study")


def test_the_fixture_has_every_kind_of_case(
    coastal_cases: list[dict[str, Any]],
) -> None:
    assert any(c["expect"] is None and not c["warns"] for c in coastal_cases)
    assert any(c["warns"] for c in coastal_cases)
    assert any(c["expect"] is not None for c in coastal_cases)


def test_each_real_transect_is_judged_as_recorded(
    coastal_cases: list[dict[str, Any]],
) -> None:
    for case in coastal_cases:
        expected = {case["expect"]} if case["expect"] else set()
        assert rejected(case["feature"]) == expected, case["name"]
        if case["expect"] is None:
            legacy = [case["warns"]] if case["warns"] else []
            assert warned(case["feature"]) == legacy, case["name"]


def test_the_model_has_no_rules_to_judge(
    coastal_cases: list[dict[str, Any]],
) -> None:
    assert ModelConstraint.get_model_constraints(CoastalTransect) == ()
    for case in coastal_cases:
        verdict = judge(CoastalTransect, case["feature"]["properties"])
        assert verdict.broken == set(), case["name"]


def test_a_valid_transect_reads_back_typed(study: dict[str, Any]) -> None:
    # Omitable hides the enums from mypy; the dump holds the members themselves.
    transect = validate_as(CoastalTransect, study).model_dump()
    assert transect["TRAN_LN_ID"]
    assert transect["V_DATUM"] is VDatum.NAVD88
    assert transect["TIME_UNIT"] is TimeUnits.SECONDS
    assert transect["SIG_HT"] > 0


def test_the_wave_values_are_in_the_units_the_description_names() -> None:
    elevation = UnitIn("ELEV_UNIT")
    length = UnitIn("LEN_UNIT")
    time = UnitIn("TIME_UNIT")
    assert field_units(CoastalTransect) == {
        "SWEL": elevation,
        "RUP": elevation,
        "SETUP_DPTH": length,
        "CON_HT": length,
        "SIG_HT": length,
        "MEAN_HT": length,
        "SIG_PD": time,
        "CON_PD": time,
        "MEAN_PD": time,
        "FETCH_LEN": UnitIn("FTCHLNUNIT"),
    }


def test_the_elevations_are_measured_from_the_datum() -> None:
    assert set(field_datums(CoastalTransect)) == {"SWEL", "RUP"}


@pytest.mark.parametrize("field", REQUIRED)
def test_a_required_field_is_required(study: dict[str, Any], field: str) -> None:
    del study["properties"][field]
    assert rejected(study) == {field}


@pytest.mark.parametrize("field", OPTIONAL)
def test_an_optional_field_is_optional(study: dict[str, Any], field: str) -> None:
    for value in (None, ""):
        study["properties"][field] = value
        assert rejected(study) == set(), repr(value)
    del study["properties"][field]
    assert rejected(study) == set()


@pytest.mark.parametrize("field", NUMBERS)
def test_a_required_number_of_minus_9999_is_missing(
    study: dict[str, Any], field: str
) -> None:
    study["properties"][field] = -9999
    assert rejected(study) == {field}
    study["properties"][field] = -8888  # section 7.3's "not populated" is a value
    assert rejected(study) == set()


@pytest.mark.parametrize("field", ["METHOD", "FTCHLNUNIT", "TIME_UNIT", "BEACH_SET"])
def test_a_lone_space_is_no_vocabulary_value(study: dict[str, Any], field: str) -> None:
    study["properties"][field] = " "
    assert rejected(study) == {field}


def test_the_free_text_fields_take_a_lone_space(study: dict[str, Any]) -> None:
    for field in ("CST_MDL_ID", "LU_SOURCE"):
        study["properties"][field] = " "
        assert rejected(study) == set(), field


def test_the_event_is_spelled_as_the_service_publishes_it(
    study: dict[str, Any],
) -> None:
    # D_Event prints `1-Percent-Chance` with a note that the database has no
    # dashes (spec/repairs.json).
    study["properties"]["EVENT_TYP"] = "1 Percent Chance"
    assert rejected(study) == set()
    study["properties"]["EVENT_TYP"] = "0.2 Percent Chance"
    assert rejected(study) == set()
    assert validate_as(CoastalTransect, study).model_dump()["EVENT_TYP"] is (
        Event.V_0_2_PERCENT_CHANCE
    )
    for wrong in ("1-Percent-Chance", "1 PERCENT CHANCE"):
        study["properties"]["EVENT_TYP"] = wrong
        assert rejected(study) == {"EVENT_TYP"}, wrong


@pytest.mark.parametrize("unit", ["SECONDS", "WEEKS", "YEARS"])
def test_the_time_units_on_the_domains_second_page_are_listed(
    study: dict[str, Any], unit: str
) -> None:
    study["properties"]["TIME_UNIT"] = unit
    assert rejected(study) == set()
    assert warned(study) == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("TIME_UNIT", "Seconds"),
        ("METHOD", "Cut From Topo"),
        ("BEACH_SET", "Sandy Beach Backed By Shore Protection Structures"),
        ("SHORE_TYP", "Non-erodible Bluff"),
        ("CSTLN_TYP", "OPEN COAST"),
        ("VZONE_EXT", "RUNUP"),
        ("EROS_METH", "OTHER"),
    ],
)
def test_a_value_in_the_wrong_case_is_rejected(
    study: dict[str, Any], field: str, value: str
) -> None:
    # The snapshot folds each of these under the reference's spelling, so none
    # reaches the legacy threshold.
    study["properties"][field] = value
    assert rejected(study) == {field}


@pytest.mark.parametrize(("field", "value"), LEGACY)
def test_a_legacy_value_warns(study: dict[str, Any], field: str, value: str) -> None:
    study["properties"][field] = value
    assert rejected(study) == set()
    assert warned(study) == [field]


def test_the_threshold_selects_exactly_the_legacy_values(
    reader: SpecReader, coastal_layer: Layer
) -> None:
    selected = {(v.field, v.value) for v in reader.legacy_candidates(coastal_layer)}
    assert selected == set(LEGACY)


def test_a_datum_admitted_by_this_layer_warns_on_the_base_flood_elevations(
    bfe_cases: list[dict[str, Any]],
) -> None:
    # The count that admits `ASVD02` is this layer's; S_BFE's own is a fifth of the
    # bar, and D_V_Datum is one enum, so its rows validate with the warning too.
    elevation = fixture_feature(bfe_cases, bfe_cases[0]["name"])
    elevation["properties"]["V_DATUM"] = "ASVD02"
    assert rejected_by(elevation, BaseFloodElevation) == set()
    assert [
        m.split("=")[0] for m in legacy_warnings_by(elevation, BaseFloodElevation)
    ] == ["V_DATUM"]


def test_a_type_under_the_bar_is_rejected(study: dict[str, Any]) -> None:
    study["properties"]["VZONE_EXT"] = "WHAFIS 3.0"
    assert rejected(study) == {"VZONE_EXT"}


def test_a_multipart_transect_is_rejected(study: dict[str, Any]) -> None:
    # Table 4 holds S_Cst_Tsct_Ln to "Must Be Single Part".
    line = study["geometry"]["coordinates"]
    study["geometry"] = {"type": "MultiLineString", "coordinates": [line, line]}
    assert rejected(study) == {"geometry"}


def test_a_transect_with_no_geometry_is_rejected(study: dict[str, Any]) -> None:
    study["geometry"] = None
    assert rejected(study) == {"geometry"}
