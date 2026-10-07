"""The snapshot as `SpecReader` presents it, and the local readings of it."""

from __future__ import annotations

import hashlib
import json
import re

import pytest

from nfhl.constraints import NULL_ENCODING_QUOTE
from nfhl.spec_source import (
    CROSSWALK,
    DOMAIN_TABLES,
    FIRM_DATABASE,
    LAYERS,
    SPEC_DIR,
    SUMMARY_ONLY,
    TEXT_NULLS,
    Layer,
    LegacyValue,
    SpecReader,
    ZoneSubtypes,
    split_cell,
    squash,
)


def test_manifest_hashes_match_the_files_on_disk() -> None:
    manifest = json.loads((SPEC_DIR / "MANIFEST.json").read_text())
    assert manifest["files"], "manifest lists no files"
    for entry in manifest["files"]:
        data = (SPEC_DIR / entry["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], entry["path"]


@pytest.mark.parametrize("layer", LAYERS, ids=lambda lyr: lyr.table)
def test_every_relationship_quotes_its_own_field_description(
    reader: SpecReader, layer: Layer
) -> None:
    table = reader.reference_table(layer.table)
    rel = reader.relationships(layer.table)
    quoted = [
        *((u.unit_field, u.quote) for u in rel.units),
        *((d.datum_field, d.quote) for d in rel.datums),
        *((o.field, o.quote) for o in rel.only_if),
        *((o.field, o.quote) for o in rel.only_when),
        *((a.field, a.quote) for a in rel.allowed),
        *((r.field, r.quote) for r in rel.required_when),
        *((v.field, v.quote) for v in rel.value_when),
    ]
    assert quoted
    for field, quote in quoted:
        assert squash(quote) in squash(table.field(field).description), field


def test_repair_and_null_encoding_quotes_are_in_the_references(
    reader: SpecReader,
) -> None:
    assert reader.repairs
    both = reader.reference_text(DOMAIN_TABLES) + reader.reference_text(FIRM_DATABASE)
    for repair in reader.repairs:
        assert squash(repair.quote) in both, repair.find
    assert squash(NULL_ENCODING_QUOTE) in reader.reference_text(FIRM_DATABASE)


def observed_values(reader: SpecReader, layer: Layer, field: str) -> set[str]:
    return {r["value"] for r in reader.observed(layer)["fields"][field] if r["value"]}


def test_the_dash_repair_matches_what_the_service_publishes(
    reader: SpecReader, layer: Layer
) -> None:
    subtypes = reader.domain("D_Zone_Subtype").values
    repaired = [v for v in subtypes if v.value != v.published]
    observed = observed_values(reader, layer, "ZONE_SUBTY")
    assert repaired, "the repair fires on nothing"
    assert any(v.value in observed for v in repaired)
    assert not any(v.published in observed for v in repaired)
    # Scoped to the PCT phrases: the levee subtypes keep their dash on the wire.
    assert any("NON-ACCREDITED" in v for v in observed)


def test_stored_values_are_descriptions_not_codes(
    reader: SpecReader, layer: Layer
) -> None:
    zone = reader.domain("D_Zone")
    open_water = next(v for v in zone.values if v.code == "OW")
    observed = observed_values(reader, layer, "FLD_ZONE")
    assert open_water.value in observed
    assert open_water.code not in observed


@pytest.mark.parametrize(
    "table", [lyr.table for lyr in LAYERS if lyr.table not in SUMMARY_ONLY]
)
def test_a_section_introduction_is_its_prose_without_the_guidance(
    reader: SpecReader, table: str
) -> None:
    # S_BFE opens with submission guidance and a requirements grid (Table 7).
    intro = reader.reference_intro(table)
    assert intro.startswith(f"The {table} ")
    assert "Study Scenarios" not in intro
    assert "contains the following elements" not in intro


def test_a_section_that_never_says_what_it_holds_reads_the_table_summary(
    reader: SpecReader,
) -> None:
    # S_Profil_Basln's section says when it is required and how to submit its
    # long text, never what it "contains information about".
    intro = reader.reference_intro("S_Profil_Basln")
    assert intro == reader.table_summary("S_Profil_Basln")
    assert intro.startswith("Location and attributes for profile baseline")
    assert reader.table_summary("S_XS") != reader.reference_intro("S_XS")


def test_rows_for_other_fema_databases_are_excluded(reader: SpecReader) -> None:
    # D_Zone's NP row applies to the FRD only.
    assert "NP" not in {v.code for v in reader.domain("D_Zone").values}
    assert "NP" in {v.code for v in reader.domain("D_V_Datum").values}


def test_every_reference_field_is_published_except_version_id(
    reader: SpecReader, layer: Layer
) -> None:
    published = set(reader.service_fields(layer))
    missing = {f.name for f in reader.reference_table(layer.table).fields} - published
    assert missing == {"VERSION_ID"}


@pytest.mark.parametrize("table", ["S_BFE", "S_XS"])
def test_the_line_layers_publish_every_reference_field(
    reader: SpecReader, table: str
) -> None:
    # Including VERSION_ID, which the zones layer leaves out.
    layer = next(lyr for lyr in LAYERS if lyr.table == table)
    published = set(reader.service_fields(layer))
    assert {f.name for f in reader.reference_table(table).fields} <= published


def test_the_profile_baselines_layer_leaves_out_only_shown_on_index(
    reader: SpecReader, profile_layer: Layer
) -> None:
    published = set(reader.service_fields(profile_layer))
    table = reader.reference_table(profile_layer.table)
    assert {f.name for f in table.fields} - published == {"SHOWN_INDX"}
    assert not table.field("SHOWN_INDX").required


def test_a_field_name_wrapped_mid_word_joins_its_description(
    reader: SpecReader,
) -> None:
    # Table 39 wraps STREAM_STN and STRMBED_EL over two lines.
    fields = {f.name: f for f in reader.reference_table("S_XS").fields}
    assert {"STREAM_STN", "STRMBED_EL"} <= fields.keys()
    assert fields["STREAM_STN"].description.startswith("Stream Station.")


def test_a_footnote_marker_leaves_a_requirement_as_it_is(reader: SpecReader) -> None:
    # "R1": the footnote reads "Field is applicable for BLE database."
    fields = {f.name: f for f in reader.reference_table("S_XS").fields}
    assert fields["START_ID"].requirement == "R1"
    assert fields["START_ID"].required
    assert not fields["XS_LTR"].required


def test_legacy_json_lists_exactly_what_its_threshold_selects(
    reader: SpecReader,
) -> None:
    def key(v: LegacyValue) -> tuple[str, str, int, str, int]:
        return (v.domain, v.field, v.layer, v.value, v.count)

    listed = [key(LegacyValue(**v)) for v in reader.legacy["values"]]
    selected = [key(v) for lyr in LAYERS for v in reader.legacy_candidates(lyr)]
    assert listed and sorted(listed) == sorted(selected)
    assert all(v["note"] for v in reader.legacy["values"])


def test_legacy_json_cites_the_snapshot_it_counted_for_each_layer(
    reader: SpecReader,
) -> None:
    manifest = json.loads((SPEC_DIR / "MANIFEST.json").read_text())
    retrieved = {s["path"]: s["retrieved_at"] for s in manifest["sources"]}
    cited = {o["path"]: o["retrieved_at"] for o in reader.legacy["observed"]}
    assert set(cited) == {f"service/observed/{lyr.layer_id}.json" for lyr in LAYERS}
    for path, at in cited.items():
        assert retrieved[path] == at, path


def test_no_base_flood_elevation_value_is_common_enough_to_be_legacy(
    reader: SpecReader, bfe_layer: Layer
) -> None:
    # The largest value outside the reference, ASVD02 in V_DATUM, is a fifth of
    # the bar; a did-happen control that the counts were read at all.
    assert reader.legacy_candidates(bfe_layer) == []
    assert "ASVD02" in observed_values(reader, bfe_layer, "V_DATUM")


def test_no_cross_section_value_is_common_enough_to_be_legacy(
    reader: SpecReader, xs_layer: Layer
) -> None:
    # The largest value outside the reference, ASVD02 in V_DATUM, is an eighth
    # of the bar; a did-happen control that the counts were read at all.
    assert reader.legacy_candidates(xs_layer) == []
    assert "ASVD02" in observed_values(reader, xs_layer, "V_DATUM")


def test_the_profile_baselines_hold_the_zones_legacy_study_types(
    reader: SpecReader, layer: Layer, profile_layer: Layer
) -> None:
    # Five of the zones' seven legacy study types clear layer 17's own bar; the
    # ASCII apostrophe (2 rows) does not, and validates there only because the
    # two layers share the StudyTyp enum.
    def study_types(lyr: Layer) -> set[str]:
        return {
            v.value for v in reader.legacy_candidates(lyr) if v.field == "STUDY_TYP"
        }

    on_profiles = study_types(profile_layer)
    assert on_profiles == {
        "SFHAs WITH HIGH FLOOD RISK",
        "SFHAs WITH LOW FLOOD RISK",
        "SFHAs WITH MEDIUM FLOOD RISK",
        "REDELINEATION",
        "DIGITAL CONVERSION",
    }
    assert on_profiles < study_types(layer)
    apostrophe = "Shaded Zone X with depths less than 1'"
    assert apostrophe in observed_values(reader, profile_layer, "STUDY_TYP")
    assert apostrophe not in on_profiles


def test_a_lower_threshold_admits_more_but_never_a_text_null(
    reader: SpecReader, layer: Layer
) -> None:
    # A did-happen control: the selection reaches past the committed list when
    # the bar drops, and the null exclusion is what keeps `-9999` out (4,681
    # rows of AR_REVERT, above this bar).
    reader = SpecReader()
    reader.legacy["threshold"] = 0.0001
    values = {v.value for v in reader.legacy_candidates(layer)}
    assert "OTHER" in values
    assert not values & TEXT_NULLS


def crosswalk(reader: SpecReader) -> dict[str, ZoneSubtypes]:
    return {row.zone: row for row in reader.subtype_crosswalk()}


def test_the_crosswalk_has_one_row_per_zone(reader: SpecReader) -> None:
    zones = [v.value for v in reader.domain("D_Zone").values]
    assert list(crosswalk(reader)) == zones


def test_every_subtype_is_allowed_for_some_zone(reader: SpecReader) -> None:
    used = {s for row in reader.subtype_crosswalk() for s in row.subtypes}
    assert used == {v.value for v in reader.domain("D_Zone_Subtype").values}


def test_the_crosswalk_rows_read_as_the_reference_prints_them(
    reader: SpecReader,
) -> None:
    # Two rows checked whole, and the page-break continuation of X joined.
    rows = crosswalk(reader)
    assert rows["AO"] == ZoneSubtypes(
        "AO",
        ("AREA WITH FLOOD HAZARD DUE TO NON-ACCREDITED LEVEE SYSTEM", "FLOODWAY"),
        allows_none=True,
    )
    assert rows["A99"].allows_none is False
    assert rows["X"].allows_none is False
    assert rows["X"].subtypes[-1] == (
        "0.2 PCT ANNUAL CHANCE FLOOD HAZARD IN COMBINED RIVERINE AND COASTAL ZONE"
    )
    assert [z for z, row in rows.items() if not row.allows_none] == ["A99", "AR", "X"]


def test_the_crosswalk_matches_the_pdftotext_rendering(reader: SpecReader) -> None:
    # The second instrument: each row's subtypes, as printed, appear in order
    # in the independent `pdftotext` text of Table 14.
    text = reader.reference_text(FIRM_DATABASE)
    start = text.index(f"Table 14: {CROSSWALK} Flood Zones")
    region = text[start : text.index("11.9.", start)]
    printed = {v.value: v.published for v in reader.domain("D_Zone_Subtype").values}
    rows = reader.subtype_crosswalk()
    # Each row's text runs from its zone label to the next one. `AREA NOT
    # INCLUDED` wraps around its `<NULL>`, so labels are two words at most.
    starts, position = [], 0
    for row in rows:
        position = region.index(f" {' '.join(row.zone.split()[:2])} ", position)
        starts.append(position)
    for row, begin, end in zip(rows, starts, [*starts[1:], len(region)], strict=True):
        position = begin
        for subtype in row.subtypes:
            # The AE row prints `NON_ACCREDITED` (spec/repairs.json), and the D
            # row breaks its line after `NON-`.
            pattern = r"\s+".join(
                re.escape(w).replace("\\-", r"[-_]\s?")
                for w in printed[subtype].split()
            )
            found = re.compile(pattern).search(region, position, end)
            assert found, (row.zone, subtype)
            position = found.end()
        assert ("<NULL>" in region[begin:end]) is row.allows_none, row.zone


def test_the_underscore_repair_is_what_lets_the_ae_row_read(
    reader: SpecReader,
) -> None:
    unrepaired = SpecReader()
    unrepaired.repairs  # noqa: B018 -- populate the cache to edit it
    unrepaired.__dict__["repairs"] = tuple(
        r for r in reader.repairs if r.applies_to != CROSSWALK
    )
    with pytest.raises(ValueError, match="NON_ACCREDITED"):
        unrepaired.subtype_crosswalk()


def test_a_cell_splits_on_the_longest_term_and_drops_footnote_markers() -> None:
    terms = ["FLOODWAY", "FLOODWAY CONTAINED IN CHANNEL", "COASTAL FLOODPLAIN"]
    cell = "FLOODWAY CONTAINED IN CHANNEL FLOODWAY COASTAL FLOODPLAIN2"
    assert split_cell(cell, terms) == [terms[1], terms[0], terms[2]]
    with pytest.raises(ValueError, match="no subtype begins 'RIVER"):
        split_cell("FLOODWAY RIVER", terms)


def test_the_sfha_rules_read_a_or_v_and_x_or_d_as_zone_codes(
    reader: SpecReader, layer: Layer
) -> None:
    # The description says "an A or V flood zone" and "X or D flood areas";
    # the reading is every D_Zone code that begins A or V (not ANI, AREA NOT
    # INCLUDED, whose code begins A but names no flood zone), and X and D.
    # OPEN WATER and AREA NOT INCLUDED are named by neither sentence.
    zones = reader.domain("D_Zone").values
    by_flag = {
        v.value: v.any_of
        for v in reader.relationships(layer.table).value_when
        if v.field == "SFHA_TF"
    }
    sfha = {z.value for z in zones if z.code[0] in "AV" and z.code != "ANI"}
    assert set(by_flag["T"]) == sfha
    assert set(by_flag["F"]) == {"X", "D"}
    unnamed = {z.value for z in zones} - sfha - {"X", "D"}
    assert unnamed == {"AREA NOT INCLUDED", "OPEN WATER"}


def test_the_dual_zone_rules_read_the_zones_after_zone_ar(
    reader: SpecReader, layer: Layer
) -> None:
    # "Zone AR/AE, Zone AR/AH, Zone AR/AO, Zone AR/A" names the zone each dual
    # SFHA reverts to; "Shaded X" is read as X, whatever its subtype.
    by_flag = {
        v.value: v
        for v in reader.relationships(layer.table).value_when
        if v.field == "DUAL_ZONE"
    }
    dual = by_flag["T"]
    assert dual.when == "AR_REVERT"
    assert set(dual.any_of) == set(re.findall(r"Zone AR/(\w+)", dual.quote))
    assert by_flag["F"].any_of == ("X",)


def test_a_value_rule_also_requires_an_optional_field(
    reader: SpecReader, layer: Layer
) -> None:
    # "will be coded as true" asks for a value, not only for no other one. SFHA_TF
    # is required for all records, so its rules need no second half.
    halves: dict[tuple[str, tuple[str, ...]], set[bool]] = {
        (v.field, v.any_of): set() for v in reader.relationships(layer.table).value_when
    }
    for rule in reader.pair_rules(layer.table):
        if (rule.field, rule.when_values) in halves:
            halves[rule.field, rule.when_values].add(rule.requires_value)
    table = reader.reference_table(layer.table)
    for (field, _), kinds in halves.items():
        assert kinds == ({False} if table.field(field).required else {False, True})
    assert {f for f, _ in halves} == {"SFHA_TF", "DUAL_ZONE"}


def test_each_allowed_list_is_the_zones_its_quote_names(
    reader: SpecReader, layer: Layer
) -> None:
    # Both AR descriptions name AE, AO, AH, A and X; the entry lists them, in
    # D_Zone's order, and nothing else.
    allowed = reader.relationships(layer.table).allowed
    assert {a.field for a in allowed} == {"AR_REVERT", "AR_SUBTRV"}
    zones = {z.value for z in reader.domain("D_Zone").values}
    for entry in allowed:
        named = set(re.findall(r"\b[A-Z][A-Z0-9]*\b", entry.quote)) & zones
        assert set(entry.zones) == named, entry.field


def test_ar_subtrv_is_limited_to_what_the_crosswalk_lists(
    reader: SpecReader, layer: Layer
) -> None:
    # Read from Table 14, not restated: the subtypes no row of A, AE, AH, AO or
    # X lists. A99's and AR's levee subtype is one; VE's coastal floodway one.
    (entry,) = [
        a for a in reader.relationships(layer.table).allowed if a.field == "AR_SUBTRV"
    ]
    forbidden = set(reader.forbidden_values(layer.table, entry))
    rows = {r.zone: r for r in reader.subtype_crosswalk()}
    listed = {s for z in ("A", "AE", "AH", "AO", "X") for s in rows[z].subtypes}
    every = {v.value for v in reader.domain("D_Zone_Subtype").values}
    assert forbidden == every - listed
    assert "AREA WITH REDUCED FLOOD HAZARD DUE TO NON-ACCREDITED LEVEE SYSTEM" in (
        forbidden
    )
    assert "FLOODWAY" not in forbidden
    assert "AREA OF MINIMAL FLOOD HAZARD" not in forbidden


def test_no_value_pair_a_rule_rejects_is_common(
    reader: SpecReader, layer: Layer
) -> None:
    # The legacy policy, applied to pairs: a combination at least one row in a
    # thousand holds would be accepted with a warning, and the models have no
    # way to do that for a pair. If this fails, a rule now rejects a common
    # combination and the policy needs a pair form before the rule ships.
    floor = reader.legacy["threshold"] * reader.observed(layer)["total"]
    for rule, broken in reader.pair_violations(layer):
        for pair in broken:
            assert pair.count < floor, (rule.when_values, pair)


def test_the_pair_counts_find_known_violations(
    reader: SpecReader, layer: Layer
) -> None:
    # A did-happen control for the test above: the counts reach the rules,
    # and pairs the rules allow are not counted against them.
    broken = {
        (rule.field, pair.when_value, pair.value): pair.count
        for rule, pairs in reader.pair_violations(layer)
        for pair in pairs
    }
    assert broken[("ZONE_SUBTY", "X", "AREA OF SPECIAL CONSIDERATION")] > 0
    assert broken[("SFHA_TF", "X", "T")] > 0
    assert ("ZONE_SUBTY", "AE", "FLOODWAY") not in broken
    assert ("SFHA_TF", "X", "F") not in broken
    combos = reader.observed(layer)["combinations"]
    total = reader.observed(layer)["total"]
    for rows in combos.values():
        assert sum(r["count"] for r in rows) == total
