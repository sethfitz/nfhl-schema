"""The snapshot as `SpecReader` presents it, and the local readings of it."""

from __future__ import annotations

import hashlib
import json

from nfhl.constraints import NULL_ENCODING_QUOTE
from nfhl.spec_source import (
    DOMAIN_TABLES,
    FIRM_DATABASE,
    SPEC_DIR,
    TEXT_NULLS,
    Layer,
    LegacyValue,
    SpecReader,
    squash,
)


def test_manifest_hashes_match_the_files_on_disk() -> None:
    manifest = json.loads((SPEC_DIR / "MANIFEST.json").read_text())
    assert manifest["files"], "manifest lists no files"
    for entry in manifest["files"]:
        data = (SPEC_DIR / entry["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], entry["path"]


def test_every_relationship_quotes_its_own_field_description(
    reader: SpecReader, layer: Layer
) -> None:
    table = reader.reference_table(layer.table)
    rel = reader.relationships(layer.table)
    quoted = [
        *((u.unit_field, u.quote) for u in rel.units),
        *((d.datum_field, d.quote) for d in rel.datums),
        *((o.field, o.quote) for o in rel.only_if),
        *((r.field, r.quote) for r in rel.required_when),
    ]
    assert quoted
    for field, quote in quoted:
        assert squash(quote) in squash(table.field(field).description), field


def test_repair_and_null_encoding_quotes_are_in_the_references(
    reader: SpecReader,
) -> None:
    assert reader.repairs
    for repair in reader.repairs:
        assert squash(repair.quote) in reader.reference_text(DOMAIN_TABLES)
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


def test_legacy_json_lists_exactly_what_its_threshold_selects(
    reader: SpecReader, layer: Layer
) -> None:
    def key(v: LegacyValue) -> tuple[str, str, int, str, int]:
        return (v.domain, v.field, v.layer, v.value, v.count)

    listed = [
        key(v)
        for d in {"D_Study_Typ", "D_Zone_Subtype"}
        for v in reader.legacy_values(d)
    ]
    selected = [key(v) for v in reader.legacy_candidates(layer)]
    assert listed and sorted(listed) == sorted(selected)
    assert all(v["note"] for v in reader.legacy["values"])


def test_legacy_json_cites_the_snapshot_it_counted(reader: SpecReader) -> None:
    manifest = json.loads((SPEC_DIR / "MANIFEST.json").read_text())
    source = next(
        s for s in manifest["sources"] if s["path"] == reader.legacy["observed"]
    )
    assert reader.legacy["retrieved_at"] == source["retrieved_at"]


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
