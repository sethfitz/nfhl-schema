"""The first link: PDF to extracted JSON.

The extraction is re-run against the pinned PDFs and must reproduce the
committed JSON exactly, and its cells are cross-checked against a second,
independent rendering of the same PDF (`pdftotext`), so a pdfplumber quirk
cannot pass unnoticed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from nfhl.extract import DOMAIN_HEADING, FIRM_HEADING, extract
from nfhl.spec_source import (
    DOMAIN_TABLES,
    FIRM_DATABASE,
    LAYERS,
    SPEC_DIR,
    SpecReader,
    squash,
)


@pytest.mark.slow
@pytest.mark.parametrize(
    ("stem", "heading"),
    [(FIRM_DATABASE, FIRM_HEADING), (DOMAIN_TABLES, DOMAIN_HEADING)],
)
def test_extraction_reproduces_the_committed_json(
    stem: str, heading: object, tmp_path: Path
) -> None:
    pdf = SPEC_DIR / "reference" / f"{stem}.pdf"
    committed = json.loads(pdf.with_suffix(".json").read_text())
    tables = [t.as_json() for t in extract(pdf, heading)]  # type: ignore[arg-type]
    assert tables == committed["tables"]


def modelled_domains(reader: SpecReader) -> set[str]:
    return {
        f.domain
        for layer in LAYERS
        for f in reader.reference_table(layer.table).fields
        if f.domain
    }


def raw_tables(stem: str) -> list[dict[str, object]]:
    path = SPEC_DIR / "reference" / f"{stem}.json"
    tables: list[dict[str, object]] = json.loads(path.read_text())["tables"]
    return tables


def test_the_tables_this_package_reads_have_no_irregular_rows(
    reader: SpecReader,
) -> None:
    wanted = modelled_domains(reader) | {layer.table for layer in LAYERS}
    tables = raw_tables(DOMAIN_TABLES) + raw_tables(FIRM_DATABASE)
    irregular = {
        t["section"] for t in tables if t["section"] in wanted and t["irregular"]
    }
    assert irregular == set()


def in_order_nearby(words: list[str], text: list[str], window: int = 40) -> bool:
    """Whether `words` occur in order within `window` words of `text`.

    pdftotext lays a table out by position, so a wrapped cell is interleaved
    with its neighbours (`... CONTAINED IN 0510 FIRM, FRD 1, 6 STRUCTURE`).
    """
    for start, word in enumerate(text):
        if word != words[0]:
            continue
        i, j = 1, start + 1
        while i < len(words) and j < min(len(text), start + window):
            if text[j] == words[i]:
                i += 1
            j += 1
        if i == len(words):
            return True
    return False


def words(text: str) -> list[str]:
    # Hyphens split too: a hyphenated value can wrap at its hyphen, with the code
    # column printed between the halves (`NON-` / `3020` / `ACCREDITED`).
    return re.split(r"[\s-]+", text.strip())


def domain_words(reader: SpecReader) -> list[str]:
    return words(reader.reference_text(DOMAIN_TABLES))


def test_every_domain_value_appears_in_the_pdftotext_rendering(
    reader: SpecReader,
) -> None:
    text = domain_words(reader)
    for name in modelled_domains(reader):
        for value in reader.domain(name).values:
            assert in_order_nearby(words(value.published), text), value.published


def test_the_in_order_check_can_fail(reader: SpecReader) -> None:
    text = domain_words(reader)
    assert not in_order_nearby(words("FLOODWAY CONTAINED IN STADIUM"), text)


def test_every_field_description_appears_in_the_pdftotext_rendering(
    reader: SpecReader,
) -> None:
    # Descriptions wrap across lines, columns and page breaks, so compare the
    # first and last eight words rather than the whole cell.
    text = reader.reference_text(FIRM_DATABASE)
    for layer in LAYERS:
        for field in reader.reference_table(layer.table).fields:
            words = squash(field.description).split()
            assert " ".join(words[:8]) in text, field.name
            assert " ".join(words[-8:]) in text, field.name
