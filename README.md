# NFHL

Pydantic models for FEMA's [National Flood Hazard Layer](https://www.fema.gov/flood-maps/national-flood-hazard-layer)
(NFHL), generated from a pinned snapshot of the FIRM Database technical
references and the NFHL map service, on Overture's `overture-schema-system`.

The NFHL is the national mosaic of FEMA's effective flood maps: every
community's Flood Insurance Rate Map (FIRM) database, stitched together and
published as an ArcGIS map service and as state and county shapefile
downloads. Its core is the flood hazard zones, `S_Fld_Haz_Ar` -- the polygons
that say which land is in a Special Flood Hazard Area, which zone (`AE`, `VE`,
`X`, ...) applies, and, where one is set, the base flood elevation and the datum
and unit it is measured in. FEMA defines the tables in two PDFs, the *FIRM
Database Technical Reference* and the *Domain Tables Technical Reference*.

## Status

Slice 1 of N: **one model, `FloodHazardZone`** (`S_Fld_Haz_Ar`, service layer
28). The snapshot already holds every layer's service metadata and both
references whole, so the next tables need no new fetch.

- `spec/` -- the pinned snapshot, refreshed by `scripts/snapshot-spec`. See
  [`spec/README.md`](spec/README.md) for provenance, the defects in the
  references, and what the published data holds that the references do not
  allow.
- `nfhl.extract` -- reads the ruled tables out of the two PDFs.
- `nfhl.spec_source` -- reads the snapshot into typed records: reference
  fields, domains, service fields, observed values.
- `nfhl.codegen` -- generates `nfhl.models`; `scripts/generate-models` drives it.
- `nfhl.models` -- generated, never hand-edited.
- `tests/fixtures/flood_hazard_zones.json` -- twelve real features from the
  service, seven that validate and five that do not, each recorded with the
  field or rule that should reject it. Fetched by `scripts/fetch-fixtures`.

## Why generate rather than hand-write

The schema exists only as two PDFs and a map service that agree on most things
and not all of them. A hand-written model would be a fourth rendering, and the
one nobody could check against the other three. Generated, every field and every
allowed value traces to a page of the reference or a field of the service, a new
edition becomes a diff, and the questions the sources leave open are answered in
two small files (`spec/repairs.json`, `spec/relationships.json`), each entry
quoting the sentence it relies on, rather than in edits scattered through code.

Unlike gatis, whose bootstrap writes models once and then hands them over,
these are rewritten on every run, and a test asserts regenerating changes
nothing. What gatis refines by hand -- relationships the source states only in
prose -- lives in those two files instead, so it is regenerated with everything
else.

## Design notes

**The reference defines the model; the service is what is published.** Field
set, meaning, requirement and domain come from the reference. Type and length
come from the service, and a field whose two types disagree stops generation.
`VERSION_ID` is required by the reference and the service does not publish it,
so it is optional here.

**A vocabulary is the published string, not the coded value.** `FLD_ZONE` holds
`OPEN WATER`, not `OW`; `LEN_UNIT` holds `Feet`, not `FT`. Each enum member's
docstring gives the coded value.

**Vocabularies are closed, and that rejects a third of the data.** 32% of the
service's flood zones have a `STUDY_TYP` the November 2024 reference does not
list, most of them what look like an earlier edition's study types. The models
reject them rather than widen the enum, because the gap between the standard and
the data is the thing worth seeing; `scripts/report-observed` prints it.
Accepting a legacy vocabulary is a later, per-value decision.

**`""` and `-9999` mean not populated.** Section 7.3 of the reference makes them
the null encodings, since the GIS formats cannot hold a true null; read as a
number, `STATIC_BFE: -9999` is an elevation. `drop_null_encodings` treats them,
and JSON `null`, as absent. "Not populated" (`NP`, `-8888`, `U`) is a value and
stays one; `"-9999"` in a text field is rejected.

**Units and datums live in sibling fields.** `STATIC_BFE` is in whatever
`LEN_UNIT` says and measured from whatever `V_DATUM` says. `UnitIn("LEN_UNIT")`
and `DatumIn("V_DATUM")` declare that on the measured field;
`field_units(FloodHazardZone)` and `field_datums(...)` read it back.

**Populated-only-if rules are constraints, not validators.** `V_DATUM` only with
a `STATIC_BFE`, `LEN_UNIT` only with a `STATIC_BFE` or `DEPTH`, and `VEL_UNIT`
whenever `VELOCITY` are the system's `forbid_if` and `require_if`, so they reach
the JSON Schema as well as Python. Only the direction each description states is
enforced: nothing says a `STATIC_BFE` needs a `V_DATUM`.

**Stacking two system constraints of one kind loses one in Python.** Each
`forbid_if` registers its check under the name `@forbid_if`, so a second on the
same class replaces the first's validator while both reach the JSON Schema. The
generated models use `nfhl.constraints.forbid_if` and `require_if`, which name
each rule for its fields. `tests/test_constraints.py` pins the upstream
behaviour, so the wrapper can go when it is fixed.

**`id` is an integer.** ArcGIS's GeoJSON output writes the service's `OBJECTID`
as the feature id, which Overture's `Feature` types as a string. It numbers rows
in one copy of the service; the reference's key is `FLD_AR_ID` within one
`DFIRM_ID`.

**Fields only the service has are extras.** `GFID`, `GlobalID`, `OBJECTID` and
the geodatabase's `SHAPE.STArea()` / `SHAPE.STLength()` validate as extra
properties; the reference does not define them.

**Validate from JSON text.** The Overture `Feature` unwraps the GeoJSON envelope
only in JSON mode, so use `FloodHazardZone.model_validate_json(...)`; a parsed
dict reports every required field missing.

## Development

```
uv sync --dev
uv run pytest
uv run mypy .
uv run ruff check . && uv run ruff format --check .
for f in scripts/*; do uv run mypy --strict "$f"; done

./scripts/snapshot-spec          # refresh spec/ from FEMA (--skip-observed is fast)
./scripts/generate-models        # rewrite src/nfhl/models/ from spec/
./scripts/report-observed        # published values the reference does not allow
./scripts/fetch-fixtures         # refetch the real-feature fixture
uv run overture-codegen list     # the model, found through the entry point
```

`pytest` re-runs the PDF extraction, about 30 seconds; `-m "not slow"` skips it.

## Licence

MIT, in [`LICENSE`](LICENSE).

That covers this repository's own work -- the models, the generator, the scripts
and the documentation. It does not cover what `spec/` and `tests/fixtures/`
vendor: FEMA's two technical references, and metadata and features from the
NFHL service. These are works of the United States Government, which 17 USC 105
excludes from copyright protection in the US; neither PDF nor the service
metadata has a notice saying otherwise. `spec/MANIFEST.json` records where
and when each was retrieved.
