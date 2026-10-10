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
  update the counts and run `scripts/report-observed`.

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

1. Add a `Layer` to `nfhl.spec_source.LAYERS` (service layer id, reference
   table, class name, module) and an entry point in `pyproject.toml`.
2. Add the table to `nfhl.codegen.GEOMETRIES`, saying what its features are in
   the words of the table's introduction. Generation stops if the entry is
   missing or names a different Esri type than the service publishes.
3. Add the table's units, datums and rules to `spec/relationships.json`. A
   table that states none goes in `NO_RELATIONSHIPS` in
   `tests/test_spec_source.py` instead.
4. Run `./scripts/generate-models`. It reads the service metadata that
   `spec/` already holds for every layer, but not observations, so it runs
   before them; `snapshot-spec` needs the model to know which fields the rules
   read.
5. Run `./scripts/snapshot-spec --layer <id>`, add the snapshot's path and
   retrieval time to `observed` in `spec/legacy.json`, then
   `./scripts/report-observed`. Add whatever the threshold selects, and
   regenerate the models.
6. Add real-feature cases and a `Fixture` to `scripts/fetch-fixtures`, and run
   it with `--layer <id>`; without `--layer` (and so `make fixtures`) it
   refetches every layer. A point layer has no length, so it passes
   `short=None` to `clean_except_expected`.
7. Run `./scripts/generate-docs`. Add the layer's fixtures to
   `tests/conftest.py`, its class to `tests/test_discovery.py`, its page to
   `tests/test_docs.py`, and its own `tests/test_<module>.py`.
8. Record what the service holds that the reference does not allow in
   `spec/README.md`, and the layer in `README.md`.
9. Count the rejected rows as one union of every clause, and check it by
   validating live pages against the union over the same `OBJECTID` range.
   Geometry-less rows belong in the union, and empty is not null: an empty
   point comes back with `coordinates: []`, which `SHAPE IS NULL` misses and
   `SHAPE.STX IS NULL` counts.

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
