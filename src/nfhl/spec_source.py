"""Read the pinned spec/ snapshot into typed records.

Three upstream sources meet here, and each answers a different question:

* the **FIRM Database Technical Reference** says what a field *means*, whether it
  is required, and which domain constrains it (`ReferenceTable`);
* the **Domain Tables Technical Reference** says what values a domain allows
  (`Domain`);
* the **NFHL MapServer** says what is actually published -- which fields exist,
  with what Esri type and length (`ServiceField`) -- and, from its statistics,
  which values occur (`Observed`).

Two local files record readings of the references that the PDFs do not make
machine-readable: `spec/repairs.json` (wire-value corrections) and
`spec/relationships.json` (which field carries another's unit or datum, and
which fields are populated only alongside another). Every entry quotes the
reference sentence that licenses it, and a test asserts the quote is still there.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

SPEC_DIR = Path(__file__).resolve().parents[2] / "spec"

FIRM_DATABASE = "firm-database-technical-reference"
DOMAIN_TABLES = "domain-tables-technical-reference"


@dataclass(frozen=True, slots=True)
class Layer:
    """A service layer this package models, and the reference table it publishes.

    The service names its layers for people ("Flood Hazard Zones") and never says
    which FIRM Database table a layer serves, so the join is declared here.
    """

    layer_id: int
    table: str
    class_name: str
    module: str


LAYERS: tuple[Layer, ...] = (
    Layer(28, "S_Fld_Haz_Ar", "FloodHazardZone", "flood_hazard_zones"),
)


@dataclass(frozen=True, slots=True)
class ReferenceField:
    """One row of a FIRM Database table, joined from its two tables in the PDF."""

    name: str
    requirement: str  # "R" required for all records, "A" required if applicable
    type: str  # "Text", "Double", "Date", ...
    length: int | None  # declared text length; None for "Default"
    domain: str | None  # a D_* domain table; L_/S_ joins are not vocabularies
    description: str

    @property
    def required(self) -> bool:
        return self.requirement == "R"


@dataclass(frozen=True, slots=True)
class ReferenceTable:
    name: str
    fields: tuple[ReferenceField, ...]

    def field(self, name: str) -> ReferenceField:
        return next(f for f in self.fields if f.name == name)


@dataclass(frozen=True, slots=True)
class DomainValue:
    code: str
    value: str  # the string that appears in published data
    published: str  # `value` as the PDF prints it, before any repair
    when_used: str | None


@dataclass(frozen=True, slots=True)
class Domain:
    name: str
    values: tuple[DomainValue, ...]

    @property
    def class_name(self) -> str:
        """`D_V_Datum` -> `VDatum`. Mechanical, so a domain's name is findable."""
        return "".join(p[:1].upper() + p[1:] for p in self.name.split("_")[1:])


@dataclass(frozen=True, slots=True)
class ServiceField:
    name: str
    esri_type: str
    length: int | None


@dataclass(frozen=True, slots=True)
class UnitOf:
    field: str
    unit_field: str
    quote: str


@dataclass(frozen=True, slots=True)
class DatumOf:
    field: str
    datum_field: str
    quote: str


@dataclass(frozen=True, slots=True)
class OnlyIf:
    """`field` may be populated only when at least one of `any_of` is."""

    field: str
    any_of: tuple[str, ...]
    quote: str


@dataclass(frozen=True, slots=True)
class RequiredWhen:
    """`field` must be populated whenever `when` is."""

    field: str
    when: str
    quote: str


@dataclass(frozen=True, slots=True)
class Relationships:
    units: tuple[UnitOf, ...]
    datums: tuple[DatumOf, ...]
    only_if: tuple[OnlyIf, ...]
    required_when: tuple[RequiredWhen, ...]


@dataclass(frozen=True, slots=True)
class Repair:
    domain: str
    find: str
    replace: str
    quote: str
    reason: str

    def apply(self, value: str) -> str:
        return value.replace(self.find, self.replace)


# Private Use Area code points. The PDFs set list bullets in a symbol font, which
# pdftotext renders as U+F0A7; they are glyphs, not text.
_PRIVATE_USE = re.compile("[\ue000-\uf8ff]")


# Page furniture pdftotext leaves between paragraphs that cross a page break.
_RUNNING_HEAD = re.compile(
    r" ?FIRM Database Technical Reference \w+ \d{4} \d+ Guidance for Flood Risk "
    r"Analysis and Mapping, FIRM Database Technical Reference ?"
)


def squash(text: str) -> str:
    """Collapse whitespace, and drop bullet glyphs, so a quote can be found in
    reflowed PDF text."""
    return " ".join(_PRIVATE_USE.sub(" ", text).split())


class SpecReader:
    """Typed access to one spec/ directory."""

    def __init__(self, spec_dir: Path = SPEC_DIR) -> None:
        self.spec_dir = spec_dir

    def _json(self, relative: str) -> Any:
        return json.loads((self.spec_dir / relative).read_text())

    # -- the FIRM Database Technical Reference --------------------------------

    @cached_property
    def _firm_tables(self) -> list[dict[str, Any]]:
        tables: list[dict[str, Any]] = self._json(f"reference/{FIRM_DATABASE}.json")[
            "tables"
        ]
        return tables

    def reference_table(self, name: str) -> ReferenceTable:
        """A table's fields, joining its description table to its field table.

        The PDF publishes each table twice -- prose descriptions, then a
        type/length/domain grid -- so a field missing from either is a defect
        in the reference and raises here rather than silently going untyped.
        """
        ours = [t for t in self._firm_tables if t["section"] == name]
        described = next(t for t in ours if t["header"][0] == "Field Name")
        typed = next(t for t in ours if t["header"][:2] == ["Field", "R/A"])
        descriptions = {r[0]: r[2] for r in described["rows"]}
        if set(descriptions) != {r[0] for r in typed["rows"]}:
            raise ValueError(f"{name}: description and field tables disagree")
        fields = []
        for name_, requirement, type_, length, _scale, joined in typed["rows"]:
            fields.append(
                ReferenceField(
                    name=name_,
                    requirement=requirement,
                    type=type_,
                    length=int(length) if length.isdigit() else None,
                    domain=joined if joined.startswith("D_") else None,
                    description=descriptions[name_],
                )
            )
        return ReferenceTable(name, tuple(fields))

    def reference_intro(self, name: str) -> str:
        """The prose the FIRM Database reference opens a table's section with.

        Only in running text, not in a table, so it is read from the
        `pdftotext` rendering, with the running page header and footer removed.
        """
        text = self.reference_text(FIRM_DATABASE)
        match = re.search(
            rf"Table: {name} (This table .*?) The {name} table contains the "
            r"following elements:",
            text,
        )
        if match is None:
            raise ValueError(f"{name}: section introduction not found")
        return _RUNNING_HEAD.sub(" ", match[1]).strip()

    def reference_text(self, stem: str) -> str:
        """The `pdftotext -layout` rendering, whitespace-collapsed for quoting."""
        return squash((self.spec_dir / "reference" / f"{stem}.txt").read_text())

    # -- the Domain Tables Technical Reference --------------------------------

    @cached_property
    def repairs(self) -> tuple[Repair, ...]:
        return tuple(Repair(**r) for r in self._json("repairs.json")["repairs"])

    @cached_property
    def _domain_tables(self) -> dict[str, dict[str, Any]]:
        found: dict[str, dict[str, Any]] = {}
        for table in self._json(f"reference/{DOMAIN_TABLES}.json")["tables"]:
            name = table["section"]
            if name and name.startswith("D_"):
                found.setdefault(name, table)
        return found

    def domain(self, name: str) -> Domain:
        """The values of one domain that apply to the FIRM Database.

        Published data carries the *description* column, not the coded value:
        `FLD_ZONE` holds `OPEN WATER` and never `OW`, `LEN_UNIT` holds `Feet`,
        `STUDY_TYP` holds `SFHA with BFE and floodway`
        (`test_published_values_are_descriptions_not_codes`). Where a domain
        prints separate FRD and FIRM descriptions (`D_V_Datum`, `D_TrueFalse`),
        the FIRM one is the published form. Rows
        whose "Applies to" column omits FIRM belong to other FEMA databases and
        are excluded.
        """
        table = self._domain_tables[name]
        header: list[str] = table["header"]
        wire = next(
            (i for i, h in enumerate(header) if h.endswith("FIRM Description")), 1
        )
        applies = next(i for i, h in enumerate(header) if h.startswith("Applies to"))
        when = next(
            (i for i, h in enumerate(header) if h.startswith("When Used")), None
        )
        repairs = [r for r in self.repairs if r.domain == name]
        values = []
        for row in table["rows"]:
            if "FIRM" not in re.split(r",\s*", row[applies]):
                continue
            published = row[wire]
            value = published
            for repair in repairs:
                value = repair.apply(value)
            values.append(
                DomainValue(
                    code=row[0],
                    value=value,
                    published=published,
                    when_used=row[when] if when is not None else None,
                )
            )
        return Domain(name, tuple(values))

    # -- the NFHL service ------------------------------------------------------

    def service_layer(self, layer: Layer) -> dict[str, Any]:
        payload: dict[str, Any] = self._json(f"service/layers/{layer.layer_id}.json")
        return payload

    def service_fields(self, layer: Layer) -> dict[str, ServiceField]:
        return {
            f["name"]: ServiceField(f["name"], f["type"], f.get("length"))
            for f in self.service_layer(layer)["fields"]
        }

    def observed(self, layer: Layer) -> dict[str, Any]:
        payload: dict[str, Any] = self._json(f"service/observed/{layer.layer_id}.json")
        return payload

    # -- local readings ----------------------------------------------------------

    def relationships(self, table: str) -> Relationships:
        raw = self._json("relationships.json")["tables"].get(table, {})
        return Relationships(
            units=tuple(UnitOf(**r) for r in raw.get("units", [])),
            datums=tuple(DatumOf(**r) for r in raw.get("datums", [])),
            only_if=tuple(
                OnlyIf(r["field"], tuple(r["any_of"]), r["quote"])
                for r in raw.get("only_if", [])
            ),
            required_when=tuple(
                RequiredWhen(**r) for r in raw.get("required_when", [])
            ),
        )
