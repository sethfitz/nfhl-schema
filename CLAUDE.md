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
- `spec/relationships.json` -- a unit, datum, populated-only-if or
  value-follows-value relationship a field description states in prose (a
  relationship the reference states as a table, like the zone/subtype
  cross-walk, is read from the extraction instead);
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

Add a `Layer` to `nfhl.spec_source.LAYERS` (service layer id, reference table,
class name, module), an entry point in `pyproject.toml`, then run
`./scripts/snapshot-spec` (for the observed values) and
`./scripts/generate-models`. Nine reference tables do not yet join their two
field listings; `spec/README.md` names them and why.

## A rule is a constraint, not a validator

Use the `forbid_if` / `require_if` in `nfhl.constraints`, not the system's
own: two system decorators of one kind on one class lose the inner rule in
Python (`tests/test_constraints.py`). A `@model_validator` reaches only callers
who import this package; a constraint also reaches the JSON Schema.

## Validate from JSON text

`FloodHazardZone.model_validate_json(...)`. The `Feature` envelope unwraps only
in JSON mode; a dict reports every required field missing.
