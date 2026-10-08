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
`spec/relationships.json` (which field carries another's unit or datum, which
fields are populated only alongside another or only for some zones, and which
values a field is limited to). Every entry quotes the
reference sentence that licenses it, and a test asserts the quote is still there.
"""

from __future__ import annotations

import importlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .rule_counts import RuleFields

if TYPE_CHECKING:
    from pydantic import BaseModel

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


def layer_model(layer: Layer) -> type[BaseModel]:
    """The generated model of `layer`."""
    module = importlib.import_module(f"nfhl.models.{layer.module}")
    model: type[BaseModel] = getattr(module, layer.class_name)
    return model


LAYERS: tuple[Layer, ...] = (
    Layer(28, "S_Fld_Haz_Ar", "FloodHazardZone", "flood_hazard_zones"),
    Layer(16, "S_BFE", "BaseFloodElevation", "base_flood_elevations"),
    Layer(14, "S_XS", "CrossSection", "cross_sections"),
    Layer(17, "S_Profil_Basln", "ProfileBaseline", "profile_baselines"),
)


@dataclass(frozen=True, slots=True)
class ReferenceField:
    """One row of a FIRM Database table, joined from its two tables in the PDF."""

    name: str
    # "R" required for all records, "A" required if applicable; a digit after
    # either is a footnote marker (`S_XS`'s "R1": "Field is applicable for BLE
    # database"), and a footnoted requirement is not enforced.
    requirement: str
    type: str  # "Text", "Double", "Date", ...
    length: int | None  # declared text length; None for "Default"
    domain: str | None  # a D_* domain table; L_/S_ joins are not vocabularies
    description: str
    footnote: str | None  # the text of the footnote `requirement` marks

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
    value: str  # the string the data stores
    published: str  # `value` as the PDF prints it, before any repair
    when_used: str | None
    meaning: str | None  # the FRD description, where it says more than `value`
    footnotes: tuple[str, ...]  # the text of each footnote the row cites


@dataclass(frozen=True, slots=True)
class LegacyValue:
    """A value the data holds that the reference does not list, accepted with a
    warning because it is common (`spec/legacy.json`)."""

    domain: str
    field: str
    layer: int
    value: str
    count: int
    note: str


# Null encodings written into a text field. Never vocabulary, whatever their
# count; `spec/legacy.json` says why.
TEXT_NULLS = frozenset({"", " ", "-9999", "<Null>"})


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
class OnlyWhen:
    """`field` may be populated only when `when` holds one of `any_of`."""

    field: str
    when: str
    any_of: tuple[str, ...]
    quote: str


@dataclass(frozen=True, slots=True)
class Allowed:
    """`field` may hold only some of its domain's values.

    Either `any_of` lists them, or `subtypes_of` names flood zones, and the
    values are every subtype the zone/subtype cross-walk allows for any of
    them. `zones` is whichever list the quote names.
    """

    field: str
    any_of: tuple[str, ...] | None
    subtypes_of: tuple[str, ...] | None
    quote: str

    @property
    def zones(self) -> tuple[str, ...]:
        zones = self.any_of if self.any_of is not None else self.subtypes_of
        assert zones is not None, f"{self.field}: allowed lists nothing"
        return zones


@dataclass(frozen=True, slots=True)
class RequiredWhen:
    """`field` must be populated whenever `when` is."""

    field: str
    when: str
    quote: str


@dataclass(frozen=True, slots=True)
class ValueWhen:
    """`field` holds `value` whenever `when` holds one of `any_of`."""

    field: str
    value: str
    when: str
    any_of: tuple[str, ...]
    quote: str


@dataclass(frozen=True, slots=True)
class Relationships:
    units: tuple[UnitOf, ...]
    datums: tuple[DatumOf, ...]
    only_if: tuple[OnlyIf, ...]
    only_when: tuple[OnlyWhen, ...]
    allowed: tuple[Allowed, ...]
    required_when: tuple[RequiredWhen, ...]
    value_when: tuple[ValueWhen, ...]


@dataclass(frozen=True, slots=True)
class PairCount:
    """How many rows of a layer hold `when_value` and `value` together."""

    when_value: str | None
    value: str | None
    count: int


@dataclass(frozen=True, slots=True)
class PairRule:
    """What `field` may hold while `when` holds one of `when_values`.

    Either it may not hold any of `forbidden`, or, when `requires_value`, it
    must hold something. `forbidden` lists reference values only: a rule from
    the reference says nothing about a legacy value, which is judged by its own
    warning. `licence` cites the table or quotes the sentence it comes from.
    """

    field: str
    when: str
    when_values: tuple[str, ...]
    forbidden: tuple[str, ...]
    requires_value: bool
    licence: str

    def broken_by(self, when_value: str | None, value: str | None) -> bool:
        if when_value not in self.when_values:
            return False
        if self.requires_value:
            return value is None or value == ""
        return value in self.forbidden


@dataclass(frozen=True, slots=True)
class Repair:
    applies_to: str  # a domain (`D_Zone_Subtype`) or a FIRM table's caption
    find: str
    replace: str
    quote: str
    reason: str

    def apply(self, value: str) -> str:
        return value.replace(self.find, self.replace)


@dataclass(frozen=True, slots=True)
class ZoneSubtypes:
    """One row of the zone/subtype cross-walk: the subtypes a flood zone allows.

    `subtypes` are stored values, after the same repairs as `D_Zone_Subtype`.
    `allows_none` is the row's `<NULL>`: the zone may have no subtype at all.
    """

    zone: str
    subtypes: tuple[str, ...]
    allows_none: bool


CROSSWALK = "Flood Zone and Zone Subtype Cross-Walk"
CROSSWALK_TABLE = "S_Fld_Haz_Ar"  # the section Table 14 is printed in
CROSSWALK_LICENCE = f"Table 14: {CROSSWALK}"
_CROSSWALK_HEADER = ["Flood Zones", "Applicable Zone Subtypes"]
_TABLE_LIST = ["FIRM Table Name", "Table Type", "Table Description"]
_NO_SUBTYPE = "<NULL>"
# Sections that never say what the table "contains information about".
SUMMARY_ONLY = frozenset({"S_Profil_Basln"})


def split_cell(cell: str, terms: list[str]) -> list[str]:
    """`cell` as the sequence of `terms` it is made of, longest match first.

    The extraction joins a cell's lines with spaces, so one subtype's end and the
    next one's start are not marked. Each term may carry a footnote marker set
    against its last word (`COASTAL FLOODPLAIN2`). Text that begins no term
    raises, so a value the vocabulary lacks stops generation.
    """
    by_length = sorted(terms, key=len, reverse=True)
    found = []
    rest = cell.strip()
    while rest:
        for term in by_length:
            match = re.match(rf"{re.escape(term)}\d?(?: |$)", rest)
            if match:
                found.append(term)
                rest = rest[match.end() :]
                break
        else:
            raise ValueError(f"{CROSSWALK}: no subtype begins {rest[:50]!r}")
    return found


# Private Use Area code points. The PDFs set list bullets in a symbol font, which
# pdftotext renders as U+F0A7; they are glyphs, not text.
_PRIVATE_USE = re.compile("[\ue000-\uf8ff]")


# Page furniture pdftotext leaves between paragraphs that cross a page break.
_RUNNING_HEAD = re.compile(
    r" ?FIRM Database Technical Reference \w+ \d{4} \d+ Guidance for Flood Risk "
    r"Analysis and Mapping, FIRM Database Technical Reference ?"
)
_DOMAIN_RUNNING_HEAD = re.compile(
    r" ?Domain Tables Technical Reference \w+ \d{4} \d+( Guidance for Flood Risk "
    r"Analysis and Mapping, Domain Tables Technical Reference)? ?"
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

    @cached_property
    def edition(self) -> str:
        """The references' edition, from `MANIFEST.json`."""
        edition: str = self._json("MANIFEST.json")["edition"]
        return edition

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
        A name the grid wraps mid-word (`S_XS`'s `STREAM_ST N`) extracts with a
        space where the line broke; no field name holds one, so it is removed.
        """
        ours = [t for t in self._firm_tables if t["section"] == name]
        described = next(t for t in ours if t["header"][0] == "Field Name")
        typed = next(t for t in ours if t["header"][:2] == ["Field", "R/A"])
        descriptions = {r[0]: r[2] for r in described["rows"]}
        rows = [[r[0].replace(" ", ""), *r[1:]] for r in typed["rows"]]
        if set(descriptions) != {r[0] for r in rows}:
            raise ValueError(f"{name}: description and field tables disagree")
        fields = []
        for name_, requirement, type_, length, _scale, joined in rows:
            marker = requirement.lstrip("RA")
            fields.append(
                ReferenceField(
                    name=name_,
                    requirement=requirement,
                    type=type_,
                    length=int(length) if length.isdigit() else None,
                    domain=joined if joined.startswith("D_") else None,
                    description=descriptions[name_],
                    footnote=self.section_footnote(name, marker) if marker else None,
                )
            )
        return ReferenceTable(name, tuple(fields))

    def section_footnote(self, name: str, marker: str) -> str:
        """The footnote `marker` cites in table `name`'s section.

        Read from the `pdftotext` rendering, where a footnote is a line of its
        own under the table that cites it: `1 Field is applicable for BLE
        database.` The section runs from its heading to the next table's.
        """
        text = (self.spec_dir / "reference" / f"{FIRM_DATABASE}.txt").read_text()
        section = re.search(
            rf"^\d+(?:\.\d+)*\.\s+Table:\s+{name}\s*$(.*?)"
            r"(?=^\d+(?:\.\d+)*\.\s+Table:\s+\w+\s*$|\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        notes = re.findall(rf"^{marker} (\S.*)$", section[1] if section else "", re.M)
        if not notes or len(set(notes)) > 1:
            raise ValueError(f"{name}: footnote {marker} not found once in its section")
        return squash(notes[0])

    def reference_intro(self, name: str) -> str:
        """What a table's section says its features are, before its field list.

        From the sentence that says what the table "contains information about"
        to the field list. Sections open differently before that sentence: with
        one line on when the table is required (`S_Fld_Haz_Ar`), or with pages
        of submission guidance and a requirements grid (`S_BFE`), so that is
        left out. Only in running text, not in a table, so it is read from the
        `pdftotext` rendering, with the running page header and footer removed.

        A section with no such sentence (`S_Profil_Basln`, which says only when
        the table is required and how to submit its long text) is described by
        its row of the reference's table summary instead (`table_summary`).
        """
        text = self.reference_text(FIRM_DATABASE)
        match = re.search(
            rf"(The {name}(?: table)? contains information .*?) "
            rf"The {name} (?:table|layer) contains the following elements\b",
            text,
        )
        if match is None:
            if name not in SUMMARY_ONLY:
                raise ValueError(f"{name}: section introduction not found")
            return self.table_summary(name)
        return _RUNNING_HEAD.sub(" ", match[1]).strip()

    def table_summary(self, name: str) -> str:
        """A table's one-line description in the reference's table summary
        (Table 1, "FIRM Database Table Summary")."""
        listing = next(
            (t for t in self._firm_tables if t["header"] == _TABLE_LIST), None
        )
        if listing is None:
            raise ValueError("the reference's table summary not found")
        rows = [r for r in listing["rows"] if r[0].strip() == name]
        if not rows:
            raise ValueError(f"{name}: not in the reference's table summary")
        summary: str = rows[0][2]
        return summary

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

        The data stores the *description* column as text, not the coded value:
        `FLD_ZONE` holds `OPEN WATER` and never `OW`, `LEN_UNIT` holds `Feet`,
        `STUDY_TYP` holds `SFHA with BFE and floodway`
        (`test_stored_values_are_descriptions_not_codes`). Where a domain prints
        separate FRD and FIRM descriptions (`D_V_Datum`, `D_TrueFalse`), the
        FIRM one is what is stored, and the FRD one, which spells the value out
        (`North American Vertical Datum 1988`), is kept as its meaning. Rows
        whose "Applies to" column omits FIRM belong to other FEMA databases and
        are excluded.
        """
        table = self._domain_tables[name]
        header: list[str] = table["header"]

        def column(test: Callable[[str], bool]) -> int | None:
            return next((i for i, h in enumerate(header) if test(h)), None)

        wire = column(lambda h: h.endswith("FIRM Description")) or 1
        applies = column(lambda h: h.startswith("Applies to"))
        assert applies is not None, f"{name}: no Applies to column"
        when = column(lambda h: h.startswith("When Used"))
        frd = column(lambda h: h == "FRD Description")
        # The rotated header extracts reversed in `D_Zone_Subtype`.
        cites = column(lambda h: "Footnote" in (h, h[::-1]))
        notes = self.domain_footnotes(name) if cites is not None else {}
        repairs = [r for r in self.repairs if r.applies_to == name]
        values = []
        for row in table["rows"]:
            if "FIRM" not in re.split(r",\s*", row[applies]):
                continue
            published = row[wire]
            value = published
            for repair in repairs:
                value = repair.apply(value)
            cited = re.findall(r"\d+", row[cites]) if cites is not None else []
            values.append(
                DomainValue(
                    code=row[0],
                    value=value,
                    published=published,
                    when_used=row[when] if when is not None else None,
                    meaning=row[frd] if frd is not None and row[frd] != value else None,
                    footnotes=tuple(notes[n] for n in cited),
                )
            )
        return Domain(name, tuple(values))

    def subtype_crosswalk(self) -> tuple[ZoneSubtypes, ...]:
        """Table 14 of the FIRM Database reference: which `ZONE_SUBTY` values
        each `FLD_ZONE` allows.

        Its cells name `D_Zone_Subtype` values as the PDF prints them, dashes and
        all, so each is matched against the domain's printed form and mapped to
        the stored one. A row whose zone is blank continues the row above across
        a page break. Corrections to the table's own text are repairs that apply
        to `CROSSWALK`.
        """
        table = next(t for t in self._firm_tables if t["header"] == _CROSSWALK_HEADER)
        rows: list[list[str]] = []
        for zone, cell in table["rows"]:
            if zone:
                rows.append([zone, cell])
            else:
                rows[-1][1] += f" {cell}"
        stored = {v.published: v.value for v in self.domain("D_Zone_Subtype").values}
        zones = {v.value for v in self.domain("D_Zone").values}
        repairs = [r for r in self.repairs if r.applies_to == CROSSWALK]
        found = []
        for zone, cell in rows:
            if zone not in zones:
                raise ValueError(f"{CROSSWALK}: {zone!r} is not a D_Zone value")
            for repair in repairs:
                cell = repair.apply(cell)
            terms = split_cell(cell, [*stored, _NO_SUBTYPE])
            found.append(
                ZoneSubtypes(
                    zone=zone,
                    subtypes=tuple(stored[t] for t in terms if t != _NO_SUBTYPE),
                    allows_none=_NO_SUBTYPE in terms,
                )
            )
        return tuple(found)

    def domain_footnotes(self, name: str) -> dict[str, str]:
        """The numbered footnotes printed under a domain table, by number.

        They are running text below the table, not cells of it, so they are read
        from the `pdftotext` rendering: from the domain's section introduction,
        each number in turn, the last ending where the note after them begins.
        """
        text = self.reference_text(DOMAIN_TABLES)
        intro = re.search(rf"{name} This domain table is referenced", text)
        if intro is None:
            raise ValueError(f"{name}: section introduction not found")
        starts: list[tuple[str, int, int]] = []
        position = intro.end()
        number = 1
        while found := re.compile(rf"(?<!\S){number}\. ").search(text, position):
            # A later section's first footnote is not this table's next one.
            if starts and found.start() - starts[-1][2] > 2000:
                break
            starts.append((str(number), found.start(), found.end()))
            position = found.end()
            number += 1
        if not starts:
            raise ValueError(f"{name}: no footnotes found")
        tail = re.compile(r" Note |(?<!\S)D_[A-Z]").search(text, starts[-1][2])
        ends = [s[1] for s in starts[1:]] + [tail.start() if tail else len(text)]
        return {
            number: _DOMAIN_RUNNING_HEAD.sub(" ", text[body:end]).strip()
            for (number, _, body), end in zip(starts, ends, strict=True)
        }

    # -- what the data holds beyond the reference -------------------------------

    @cached_property
    def legacy(self) -> dict[str, Any]:
        """`spec/legacy.json`: the threshold, its source, and the values."""
        payload: dict[str, Any] = self._json("legacy.json")
        return payload

    def legacy_counted_at(self, layer_id: int) -> str:
        """When the snapshot `spec/legacy.json` took `layer_id`'s counts from
        was retrieved."""
        path = f"service/observed/{layer_id}.json"
        counted: str = next(
            o["retrieved_at"] for o in self.legacy["observed"] if o["path"] == path
        )
        return counted

    def legacy_values(self, domain: str) -> tuple[LegacyValue, ...]:
        return tuple(
            LegacyValue(**v) for v in self.legacy["values"] if v["domain"] == domain
        )

    def legacy_candidates(self, layer: Layer) -> list[LegacyValue]:
        """What the threshold selects from the observed counts, notes left blank.

        `spec/legacy.json` must list exactly these; it adds only the notes.
        """
        observed = self.observed(layer)
        floor = self.legacy["threshold"] * observed["total"]
        found = []
        for field in self.reference_table(layer.table).fields:
            rows = observed["fields"].get(field.name)
            if field.domain is None or rows is None:
                continue
            allowed = {v.value for v in self.domain(field.domain).values}
            for row in rows:
                value, count = row["value"], row["count"]
                if value is None or value in TEXT_NULLS or value in allowed:
                    continue
                if count >= floor:
                    found.append(
                        LegacyValue(
                            field.domain, field.name, layer.layer_id, value, count, ""
                        )
                    )
        return found

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

    def rule_groups(self, layer: Layer) -> tuple[RuleFields, list[dict[str, Any]]]:
        """The snapshot's rows grouped by the fields the rules read, and which
        fields those are (`observed["rules"]`)."""
        recorded = self.observed(layer)["rules"]
        fields = RuleFields(
            tuple(recorded["by_value"]),
            tuple(recorded["by_populated"]),
            # Snapshots taken before free-text rule fields leave it out.
            tuple(recorded.get("by_text_populated", ())),
        )
        return fields, recorded["groups"]

    def pair_violations(self, layer: Layer) -> list[tuple[PairRule, list[PairCount]]]:
        """Each pair rule, with the observed value pairs that break it.

        Read from the snapshot's two-field counts, which `snapshot-spec` takes
        for every pair a rule reads (`observed["combinations"]`).
        """
        combinations = self.observed(layer)["combinations"]
        found = []
        for rule in self.pair_rules(layer.table):
            rows = combinations[f"{rule.when},{rule.field}"]
            broken = [
                PairCount(r[rule.when], r[rule.field], r["count"])
                for r in rows
                if rule.broken_by(r[rule.when], r[rule.field])
            ]
            found.append((rule, broken))
        return found

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
            only_when=tuple(
                OnlyWhen(r["field"], r["when"], tuple(r["any_of"]), r["quote"])
                for r in raw.get("only_when", [])
            ),
            allowed=tuple(
                Allowed(
                    r["field"],
                    tuple(r["any_of"]) if "any_of" in r else None,
                    tuple(r["subtypes_of"]) if "subtypes_of" in r else None,
                    r["quote"],
                )
                for r in raw.get("allowed", [])
            ),
            required_when=tuple(
                RequiredWhen(**r) for r in raw.get("required_when", [])
            ),
            value_when=tuple(
                ValueWhen(
                    r["field"], r["value"], r["when"], tuple(r["any_of"]), r["quote"]
                )
                for r in raw.get("value_when", [])
            ),
        )

    def forbidden_values(self, table: str, allowed: Allowed) -> tuple[str, ...]:
        """The reference values of `allowed.field`'s domain it may not hold.

        Reference values only, like a pair rule's: a legacy value is judged by
        its own warning. `subtypes_of` reads the zones' rows of the cross-walk.
        """
        domain = self.reference_table(table).field(allowed.field).domain
        assert domain is not None, f"{table}.{allowed.field} has no domain"
        if allowed.subtypes_of is not None:
            rows = {row.zone: row for row in self.subtype_crosswalk()}
            ok = {s for zone in allowed.subtypes_of for s in rows[zone].subtypes}
        else:
            ok = set(allowed.zones)
        values = [v.value for v in self.domain(domain).values]
        unknown = ok - set(values)
        if unknown:
            raise ValueError(f"{table}.{allowed.field}: not in {domain}: {unknown}")
        return tuple(v for v in values if v not in ok)

    def pair_rules(self, table: str) -> tuple[PairRule, ...]:
        """Every rule on which values two fields of `table` may hold together.

        The cross-walk gives one rule per set of zones that forbid the same
        subtypes, and one requiring a subtype of the zones whose row has no
        `<NULL>`. Each `value_when` relationship forbids the field's other
        domain values and, on a field the reference does not require, requires
        it: a field that holds a value is populated.
        """
        rules = []
        if table == CROSSWALK_TABLE:
            reference = [v.value for v in self.domain("D_Zone_Subtype").values]
            zones_by_forbidden: dict[tuple[str, ...], list[str]] = {}
            required = []
            for row in self.subtype_crosswalk():
                forbidden = tuple(s for s in reference if s not in row.subtypes)
                zones_by_forbidden.setdefault(forbidden, []).append(row.zone)
                if not row.allows_none:
                    required.append(row.zone)
            licence = CROSSWALK_LICENCE
            for forbidden, zones in zones_by_forbidden.items():
                rules.append(
                    PairRule(
                        "ZONE_SUBTY",
                        "FLD_ZONE",
                        tuple(zones),
                        forbidden,
                        False,
                        licence,
                    )
                )
            rules.append(
                PairRule("ZONE_SUBTY", "FLD_ZONE", tuple(required), (), True, licence)
            )
        reference_table = self.reference_table(table)
        for rel in self.relationships(table).value_when:
            field = reference_table.field(rel.field)
            assert field.domain is not None, f"{table}.{rel.field} has no domain"
            others = tuple(
                v.value
                for v in self.domain(field.domain).values
                if v.value != rel.value
            )
            rules.append(
                PairRule(rel.field, rel.when, rel.any_of, others, False, rel.quote)
            )
            if not field.required:
                rules.append(
                    PairRule(
                        rel.field,
                        rel.when,
                        rel.any_of,
                        forbidden=(),
                        requires_value=True,
                        licence=rel.quote,
                    )
                )
        return tuple(rules)
