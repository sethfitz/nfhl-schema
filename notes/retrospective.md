# Building nfhl-schema: notes for a retrospective

Raw material for a write-up on building this package, alone or alongside other
schemas built on `overture-schema-system`. Append to it as each slice lands: what
was harder or easier than expected, what the reference or the data did that nobody
predicted, and what Overture's system made easy or got in the way of. Record what
happened and what it cost, not verdicts.

## The approach

Nothing in `src/nfhl/models/` is written by hand. The models are generated from a
pinned snapshot of two FEMA PDFs (the FIRM Database and Domain Tables technical
references, November 2024) and the NFHL map service's own field metadata, and
every rule that comes from prose quotes the sentence that licenses it, checked
against the PDF by a test. That made each slice a change to a generator or a JSON
file plus a regeneration, and it kept the question "where did this rule come
from?" answerable for every constraint.

Each slice was measured against the live layer, all 5.8 million Flood Hazard
Zones rows, before it was called done: how many published rows the new rule
rejects. Those counts were what made each judgement call visible.

## The data does not match its own spec

- 32% of published flood zones had a study type outside the reference's list,
  mostly "SFHAs WITH LOW/HIGH/MEDIUM FLOOD RISK". These and `REDELINEATION` and
  `DIGITAL CONVERSION` are the November 2016 edition's study types; the 2019
  edition replaced the first three and moved the other two to the study-method
  domain, where the 2024 reference still lists them. Accepting values held by at
  least 1 row in 1,000 with a warning (8 values) brought rows outside the
  reference down to 0.03%. The same bar admits the 2019 wording of study type
  1000 cut to 38 characters (6,493 rows).
- The reference describes coded-value domains, but none of the distributions use
  them: the service, the state geodatabases and the county shapefiles all store
  the description text, and the geodatabase declares no domains. The first README
  framed "store the code or the text" as a design choice; it was not one.
- The zone/subtype cross-walk (Table 14) rejects 694 rows, and the SFHA flag rule
  17. Exempting legacy subtypes from the cross-walk was forced: otherwise all
  24,849 rows of `AREA WITH REDUCED FLOOD RISK DUE TO LEVEE` fail.
- The AR revert fields are populated on 79 rows that are not AR zones, and the
  layer has no AR zones at all, so the value limits on those fields have nothing to
  check today.
- The revert BFE and depth, the numeric AR fields, are populated on 18,177 rows,
  none of them AR zones and none setting `AR_REVERT`. Most are `0` or `-8888`
  written for "does not apply". One county (DFIRM `31099C`, 3,311 rows) holds
  each polygon's area in square feet in `DEP_REVERT`, found by dividing it by
  `SHAPE.STArea()` and getting the same number every time. The rule licensing
  these is weaker than the AR fields' "only populated if": it says "populated
  when Zone equals AR", and reading it as a limit is a judgement.
- The service's own statistics compare text ignoring case and trailing blanks.
  That makes a count for one value an upper bound, but a total of values outside
  a vocabulary a lower bound: a variant of an allowed value folds into its group
  and vanishes. The 1,607 lone spaces in `STUDY_TYP` are hidden that way. `LIKE`
  keeps a trailing blank in its pattern, so it counts lone spaces exactly.

## Where overture-schema-system got in the way

These are inputs for the overture-schema backlog.

- **Stacked constraint decorators.** Two `@forbid_if` on one class both reach the
  JSON Schema, but only one runs in Python: both register under the same validator
  name, so the second replaces the first. Worked around with wrappers that name
  each rule for its fields.
- **A system `forbid_if` on a required field fails at import**, which mypy does
  not catch; the SFHA rule uses a `require_any_true` shape instead.
- **`FieldEqCondition(field, None)` never fires on an omitted `Omitable` field**:
  an omitted field is `MISSING`, not `None`. The package defines `Absent` and
  `Populated` conditions.
- **Feature ids are strings.** ArcGIS's GeoJSON writes the integer `OBJECTID` as
  the feature id, so `id` is redeclared.
- **Housekeeping fields.** The service and the geodatabase have different
  bookkeeping columns (`OBJECTID`, `GlobalID`, `GFID` vs `SHAPE_Length`,
  `SHAPE_Area`), so forbidding extra fields means choosing one distribution. They
  started as extras and are now declared `Omitable` (2026-10-05), which was built
  for JSON and may not yet behave in PySpark's column structure check.
- **The GeoJSON envelope unwraps only in JSON mode**: validating a parsed dict
  reports every required field missing.
- **Validation reports one broken constraint per feature.** Each constraint is
  its own `model_validator`, and pydantic stops at the first that raises, so a
  feature breaking three rules names one. A count of rejections per rule taken
  from validation errors undercounts every rule but the first to run. Measuring
  the revert rules needed each constraint run on its own, through
  `ModelConstraint.get_model_constraints` and `validate_instance` on a
  `model_construct`ed instance. The AR slice had read "rejected by this rule
  and nothing else" from validation errors; it held, but that instrument could
  not have shown otherwise.

## Process

- FEMA's CDN refuses Python's `urllib` (and spoofed user agents) with 403; the
  snapshot script fetches with curl.
- The early slices were committed locally and not pushed until Seth asked why
  (2026-10-05). Push each slice as it lands.
- Re-snapshotting refreshes every count, which breaks `spec/legacy.json` and the
  README figures until they are updated; a test catches the first.
- A pass re-checking every claim in the README's "what the service holds"
  section (2026-10-05) reproduced every count, and found the claims around the
  counts wrong instead. "Every count is an upper bound" held for single values
  and was backwards for totals. "An earlier edition's study types; unverified"
  stayed unverified because the search covered only the vendored 2024 PDFs.
  FEMA's superseded 2016 and 2019 references settled it, and showed two of the
  five were not missing from 2024 but filed under another domain. Counting
  `V_DATUM` "set" rows also counted values the vocabulary rejects before the
  rule runs (16,933 rows, 16,571 reaching the rule).
