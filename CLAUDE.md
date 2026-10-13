# NFHL

Pydantic models for FEMA's NFHL, built on `overture-schema-system`. Read
[`README.md`](README.md) first, then [`spec/README.md`](spec/README.md).

## Never edit `src/nfhl/models/`

Every file there is rewritten by `scripts/generate-models`, and
`tests/test_codegen.py` fails if a committed file differs from a fresh
generation. A change belongs in one of four places:

- `nfhl.codegen` -- how a source becomes code;
- `spec/repairs.json` -- a published domain value the database writes
  differently from the PDF;
- `spec/relationships.json` -- a unit, datum, populated-only-if,
  value-follows-value or allowed-values relationship a field description states
  in prose (a relationship the reference states as a table, like the
  zone/subtype cross-walk, is read from the extraction instead);
- `spec/legacy.json` -- a value outside the reference that the data commonly
  holds, accepted with a warning. Its entries are licensed by a count, not a
  quote: a test asserts the file lists exactly what its threshold selects from
  `spec/service/observed/`, so after `snapshot-spec` refreshes the counts,
  update the counts and run `scripts/report-observed`. The one exception is an
  entry with a `decision` field, a maintainer's call recorded with its date and
  reason, which admits a value under the bar; the test requires such an entry
  to be one the threshold would not select, so the threshold still governs the
  rest. Add one only when the maintainer has made that call. A decision also
  admits a case variant the snapshot's case folding hides (`1 PCT ...` under
  `1 Pct ...`). Count it by reading every row; the test checks it fits inside
  its folded group's count, and the generator numbers the members that differ
  only in case (`_CASE_2`).

Every entry in the first two JSON files quotes the reference sentence that licenses
it, and a test asserts the quote is still in the reference. A judgement without
a quote does not go in them; record it in `spec/README.md` instead.

## Never edit `docs/` either

`scripts/generate-docs` rewrites it from the models with `overture-codegen`, and
`tests/test_docs.py` fails if it is stale. Regenerate it after
`generate-models`.

## `spec/MANIFEST.json` says which edition the models track

Prose anywhere, including here, restates it and can go stale. The edition, the
URLs and the retrieval times are in the manifest.

## Adding a layer

A table that `FIRM_PAN` or another key joins is a candidate only if it is a
service layer; `L_Pan_Revis` and the other lookup tables are not.

1. Add a `Layer` to `nfhl.spec_source.LAYERS` (service layer id, reference
   table, class name, module) and an entry point in `pyproject.toml`. A
   table whose section never says what it "contains information about"
   (`S_Profil_Basln`, `S_Gen_Struct`) also goes in `SUMMARY_ONLY` in
   `nfhl.spec_source`, or generation stops at `reference_intro`. A section
   that says it but names the table another way ("The S_Tsct_Basln spatial
   file contains") needs the pattern widened instead.
2. Add the table to `nfhl.codegen.GEOMETRIES`, saying what its features are in
   the words of the table's introduction. Generation stops if the entry is
   missing or names a different Esri type than the service publishes. A table
   whose polygons Table 4 does not hold to "Must Be Single Part" is Polygon
   and MultiPolygon.
3. Add the table's units, datums and rules to `spec/relationships.json`. A
   table that states none goes in `NO_RELATIONSHIPS` in
   `tests/test_spec_source.py` instead. A field "populated when" any of
   several others is takes `when_any_populated` in place of `when`; see the
   Coastal Transects units.
4. Run `./scripts/generate-models`. It reads the service metadata that
   `spec/` already holds for every layer, but not observations, so it runs
   before them; `snapshot-spec` needs the model to know which fields the rules
   read. A domain that stops at `irregular` rows in `tests/test_extract.py` is
   an extraction defect (`D_Time_Units` lost its second page to a header cut by
   a stray rule), not a value to admit as legacy. A field table that names its
   domain in another case (`D_VZONE`, `D_VZone`) is matched without it.
5. Run `./scripts/snapshot-spec --layer <id>`, add the snapshot's path and
   retrieval time to `observed` in `spec/legacy.json`, then
   `./scripts/report-observed`. Add whatever the threshold selects, and
   regenerate the models, and run the whole suite: a legacy value belongs to
   its domain, so other layers' fixture cases that expected it rejected
   (`ASVD02` in the zones, BFEs and cross sections) move to `warns`, and a rule
   count that reaches a row it did not before moves with them. The snapshot
   folds case, so a wrong-case value has no count to license it, and the one form it shows can be a few percent of
   its group. Before licensing a legacy value, read the layer's rows
   (keyset-paged by `OBJECTID`, no geometry) and count the exact forms.
6. Add real-feature cases and a `Fixture` to `scripts/fetch-fixtures`, and run
   it with `--layer <id>`; without `--layer` (and so `make fixtures`) it
   refetches every layer. A point layer has no length, so it passes
   `short=None` to `clean_except_expected`. A rule that reads a vocabulary
   field fires only once that field validates, so filter a rule's cases on
   "the rule would fire", not "the field is right". No `where` can exclude
   rows the service's case folding matches to a reference value but the model
   rejects: find them by reading every row, and pin their `OBJECTID`s out of
   the fixture filters. `SHAPE.STArea() = 0` matches slivers the service
   rounds to no area, which validate, as well as empty polygons; pin the
   empty ones by `OBJECTID` too. Thousands of case-variant rows do not fit in
   a `where` (the service accepts no `COLLATE`): exclude the DFIRMs that hold
   them from the clean filters and pin the cases that need those DFIRMs. A
   pinned row needs no clean filter. A row the model rejects never raises a
   legacy warning, so a legacy value on one is untested by its fixture case;
   test it by setting the value on a valid real row. Hold a vocabulary field's
   clean filter to
   the reference's values, not the legacy ones: a legacy value makes a clean
   case warn, and the legacy cases free the field through `warns`.
7. Run `./scripts/generate-docs`. Add the layer's fixtures to
   `tests/conftest.py`, its class to `tests/test_discovery.py`, its page to
   `tests/test_docs.py`, and its own `tests/test_<module>.py`. Test a legacy
   value by the warning it raises, not by `in LEGACY_MEMBERS`: the members are
   `str`, so `TrueFalse("1")` equals `StateFIPS.V_1` and `in` finds it either
   way.
8. Record what the service holds that the reference does not allow in
   `spec/README.md`, and the layer in `README.md`.
9. Count the rejected rows as one union of every clause, and check it by
   validating live pages against the union over the same `OBJECTID` range.
   Geometry-less rows belong in the union, and empty is not null: an empty
   point comes back with `coordinates: []`, which `SHAPE IS NULL` misses and
   `SHAPE.STX IS NULL` counts. That test works only for points, since it
   counts every polygon; check polygon emptiness by validating the rows. The
   service folds case, so a wrong-case vocabulary value is in the model's
   rejections and not in the union: have the page control print the
   model-only rows by field and value, and expect their sum to equal the
   difference. Cut the control's windows from the sorted ids, about 1,000
   rows each: ids can be sparse (layer 24 has 285,947 rows and ids to
   2,350,391). Cache each window and halve one the service errors on, down
   to a single row read generalised (`maxAllowableOffset`): it errors under
   load on windows whose every half it returns, not only on long shapes.

Eight reference tables do not yet join their two field listings, so
`SpecReader.reference_table` raises on them; `spec/README.md` names them and
why.

## A rule is a constraint, not a validator

Use the `forbid_if` / `require_if` in `nfhl.constraints`, not the system's
own: two system decorators of one kind on one class lose the inner rule in
Python (`tests/test_constraints.py`). A `@model_validator` reaches only callers
who import this package; a constraint also reaches the JSON Schema.

## Validate from JSON text

`FloodHazardZone.model_validate_json(...)`. The `Feature` envelope unwraps only
in JSON mode; a dict reports every required field missing.

## Keep `notes/retrospective.md` as you go

It is the raw material for a write-up on building this package. When a slice
lands, add what surprised you, what the data or the reference did, and anything
in `overture-schema-system` that got in the way.
