"""Read the ruled tables out of FEMA's two technical-reference PDFs.

FEMA publishes the FIRM Database schema and its domain vocabularies only as PDFs,
so this is the first link in the chain from source to model, and the one most
likely to break. The approach is deliberately dumb and checkable:

* `pdfplumber` finds each ruled table and returns its cells.
* Each table is assigned to the section heading above it -- `11.8. Table:
  S_Fld_Haz_Ar` in the FIRM Database reference, `D_Zone` in the Domain Tables
  reference -- and a table with no heading above it on its page continues the
  previous one.
* A row that does not have as many cells as its header is kept, unparsed, in
  `irregular` rather than being repaired or dropped, so nothing disappears
  silently. `tests/test_extract.py` asserts the tables this package reads have
  none.

The output is committed under `spec/reference/` and is re-derivable: a test
re-runs the extraction against the pinned PDFs and asserts it reproduces those
files byte for byte.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pdfplumber

# `11.8.       Table: S_Fld_Haz_Ar` -- a section of the FIRM Database reference.
FIRM_HEADING = re.compile(r"^\d+(?:\.\d+)*\.?\s+Table:\s+(?P<name>[A-Za-z]\w*)\s*$")
# `D_Zone` alone on a line -- a section of the Domain Tables reference.
DOMAIN_HEADING = re.compile(r"^(?P<name>D_\w+)\s*$")

Cell = str | None


@dataclass
class Table:
    """One logical table, possibly continued across pages."""

    section: str | None
    header: list[str]
    rows: list[list[str]] = field(default_factory=list)
    irregular: list[list[Cell]] = field(default_factory=list)
    fragments: list[list[list[Cell]]] = field(default_factory=list)
    pages: list[int] = field(default_factory=list)

    def as_json(self) -> dict[str, Any]:
        return {
            "section": self.section,
            "pages": self.pages,
            "header": self.header,
            "rows": self.rows,
            "irregular": self.irregular,
            "fragments": self.fragments,
        }


def clean(cell: str) -> str:
    """Join a wrapped cell back into one line.

    A line ending in a hyphen is a wrapped hyphenated word (`NON-` / `ACCREDITED`,
    `four-` / `digit`), so it joins without a space and keeps the hyphen.
    """
    text = re.sub(r"-\n", "-", cell)
    return " ".join(text.split())


def split_header(raw: list[list[Cell]]) -> tuple[list[str], list[list[Cell]]]:
    """Separate the (possibly multi-row) header from the data rows.

    A header that wraps arrives as extra rows whose first cell is `None` -- the
    merged continuation of the first column. Their text is joined into the
    column above. Columns whose header is empty are padding from the ruling and
    are dropped, which is what lets data rows (with their `None` padding also
    dropped) line up with the header.
    """
    header_rows = [raw[0]]
    for row in raw[1:]:
        if row and row[0] is None:
            header_rows.append(row)
        else:
            break
    width = max(len(r) for r in header_rows)
    merged = []
    for col in range(width):
        parts = [r[col] for r in header_rows if col < len(r) and r[col]]
        merged.append(clean(" ".join(p for p in parts if p)))
    return [h for h in merged if h], raw[len(header_rows) :]


def compact(row: list[Cell]) -> list[str]:
    """A data row without the `None` padding pdfplumber adds for merged cells."""
    return [clean(c) for c in row if c is not None]


def extract(pdf_path: Path, heading: re.Pattern[str]) -> list[Table]:
    """Every ruled table in `pdf_path`, assigned to the heading above it."""
    tables: list[Table] = []
    section: str | None = None
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            found = page.find_tables()
            boxes = [t.bbox for t in found]
            events: list[tuple[float, str, Any]] = []
            for line in page.extract_text_lines():
                inside = any(b[1] <= line["top"] <= b[3] for b in boxes)
                match = heading.match(line["text"].strip())
                if match and not inside:
                    events.append((line["top"], "heading", match["name"]))
            for t in found:
                events.append((t.bbox[1], "table", t))
            events.sort(key=lambda e: (e[0], e[1]))

            fresh = False  # whether a heading has appeared since the last table
            for _, kind, payload in events:
                if kind == "heading":
                    section, fresh = payload, True
                    continue
                raw = payload.extract()
                if not raw:
                    continue
                header, body = split_header(raw)
                ours = [t for t in tables if t.section == section]
                if len(header) < 2 and ours:
                    # A one-column "table" inside a section is a piece of the
                    # real table's header ruled as a box of its own (D_Zone_Subtype
                    # draws `Applies to` / `Database` / `Schema` this way). Kept,
                    # not parsed, and it does not break the continuation.
                    ours[-1].fragments.append(raw)
                    continue
                same = [t for t in ours if t.header == header]
                table = same[-1] if same and not fresh else Table(section, header)
                if not (same and table is same[-1]):
                    tables.append(table)
                if page_number not in table.pages:
                    table.pages.append(page_number)
                for row in body:
                    cells = compact(row)
                    if len(cells) == len(header):
                        table.rows.append(cells)
                    else:
                        table.irregular.append(row)
                fresh = False
    return tables


def write(tables: list[Table], source: str, out: Path) -> None:
    payload = {"source": source, "tables": [t.as_json() for t in tables]}
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--kind", choices=("firm", "domain"), required=True)
    args = parser.parse_args()
    pattern = FIRM_HEADING if args.kind == "firm" else DOMAIN_HEADING
    write(extract(args.pdf, pattern), args.pdf.name, args.out)


if __name__ == "__main__":
    main()
