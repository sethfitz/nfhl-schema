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
- `DUAL_ZONE`, the last AR field, is `T` on 4 rows, all in one county (DFIRM
  `51107C`) and none an AR zone: two `AE` and two `X`. `U`, which no sentence
  about the field names, is on 72,929. The 73 rows that set `AR_REVERT` to an A
  zone leave `DUAL_ZONE` empty, so the new rule rejects all of them, rows the
  only-in-AR rule already rejected. Validation now names the `DUAL_ZONE` rule
  for all 73, not the only-in-AR rule, which is the actual defect: the order
  rules run in decides what a user is told. With no AR zone in the layer,
  nothing tests the rule on data it was written for.
- The reference defines `DUAL_ZONE` by example ("Zone AR/AE, Zone AR/AH, ...")
  and by a category no field records ("Shaded X"). Reading the examples as the
  zone in `AR_REVERT` turns it into the same two-field rule as `SFHA_TF`'s.
- The service's own statistics compare text ignoring case and trailing blanks.
  That makes a count for one value an upper bound, but a total of values outside
  a vocabulary a lower bound: a variant of an allowed value folds into its group
  and vanishes. The 1,607 lone spaces in `STUDY_TYP` are hidden that way. `LIKE`
  keeps a trailing blank in its pattern, so it counts lone spaces exactly.

## The second layer

Base Flood Elevations (`S_BFE`, 2026-10-07) was the first test of "the generator
makes models, not a model". Its reference table joined on the first try, and
both its domains and the unit and datum relationships were already shaped per
table. What had been written for one layer was everywhere else: the geometry
(Polygon, hardcoded), the feature id's description (naming `FLD_AR_ID`), the
model's imports (a model with no rules imported every constraint and failed
lint), the section-introduction regex (it expected "This table", and `S_BFE`
opens with two pages of submission guidance and a requirements grid),
`legacy.json`'s single snapshot path, `report-observed` reading `FLD_ZONE`, the
fixture script, and the tests' `(only,) = LAYERS`. `snapshot-spec` could only
re-count every layer, which for a new one would have moved every zone figure in
the README; it now takes `--layer`.

- `VERSION_ID`, the zones layer's one missing field, is published on layer 16,
  so "the service omits it" is a fact about one layer, not the service.
- No BFE value clears the legacy bar; the largest outside the reference,
  `ASVD02`, is a fifth of it. The policy was never tested on a layer where it
  admits nothing.
- The largest rejection is not a vocabulary or a rule: `SOURCE_CIT`, required,
  is null on 16,273 lines. Checking the zones for the same found 12,589 rows
  nobody had counted, because the instruments built so far (`report-observed`,
  `count-broken-rules`) count values and rules, not empty required fields.
- Enums are per domain, legacy status is per layer. A value legacy on one layer
  would validate with a warning on every layer sharing its domain. Not hit
  here, since BFE adds no legacy value.

## The third layer

Cross-Sections (`S_XS`, 2026-10-07) was the first layer from the list of tables
that did not join. Its type grid wraps `STREAM_STN` and `STRMBED_EL` over two
lines, and the extraction joins a cell's lines with a space; no field name holds
one, so `reference_table` drops it. `L_Profil_Label`, listed beside it as
wrapped, is a misspelling: the reference prints `ORIENT` as `RIENT`. Three more
assumptions came from the first two layers. The requirement column says `R1` on
three fields, a footnote marker ("Field is applicable for BLE database"), and
`required` compared the cell to `"R"`, so they generated as optional with no
error; nothing checks that a requirement code is one the generator knows. `SEQ`
is the first `Short Integer`. And the section introduction ends "contains the
following elements, BLE database requirements may vary, see footnote:", not at
the colon.

- The census grouped every text field a rule reads by its value. `XS_LTR` is
  free text, a letter or number per section, and the service truncated a
  grouping by it. Its rule asks only whether it holds anything, so it is now
  grouped by populated, like a number. The lone spaces still had to be split off
  first: `= ''` matches one, and in free text a lone space is a value. 11,887 of
  them sit on unlettered sections, most of the rule's 14,801 rejections.
- `STRMBED_EL` is required, and 575,580 of 952,002 rows (60%) hold `-8888`,
  "intentionally not populated", which validates as an elevation with a unit and
  a datum; 76,365 more hold the null. `WSEL_REG`'s description licenses `-8888`;
  `STRMBED_EL`'s does not.
- `LEN_UNIT` is `Miles` on 1,778 sections in 36 DFIRMs. The vocabulary lists
  it, so they validate, but their `WSEL_REG` runs from 66.2 to 1,494.7, which
  is feet. `Miles` looks like the unit of `STREAM_STN`, for which the reference
  names none.
- Section 10 of the reference says "Multi-part features are not allowed" for
  every vector file. The zones accept MultiPolygon.

## The fourth layer

Profile Baselines (`S_Profil_Basln`, 2026-10-07) was picked because the cross
sections point at it: `STREAM_STN` is "the measurement along the profile
baseline", and both tables have the `START_ID` that joins them to the station
start. Its section is the first that never says what the table "contains
information about"; it says when the table is required and how to submit long
text, so `reference_intro` raised. The class docstring falls back to the row
the reference's Table 1 summary gives each table.

- It is the first layer to share a domain with legacy values: five of the
  zones' legacy study types clear layer 17's own bar. Enums are one per domain,
  and legacy members were one per `legacy.json` entry, so the second layer's
  entries would have generated duplicate members. A member now cites every
  layer that counted it, and a value legacy on one layer validates with the
  warning on every layer sharing the domain: the zones' ASCII-apostrophe study
  type is on 2 baselines, under this layer's bar of 339, and warns rather than
  rejects there.
- `R1` decides the layer. 106,642 baselines (31.5%) have no `START_ID`, 23,554
  of them `Hydraulic Link`s; read as required, the layer rejects 33.5% of its
  rows, and read as optional, 2.3%.
- The service folded blanks the other way round from layer 28. `DATUM_UNIT`
  grouped 191,723 rows under `' '`; `LIKE ' '` counts 4,352. The empty strings
  joined the lone spaces' group, so `report-observed` overstates the lone
  spaces 44-fold here, where on the zones it hid them.
- `V_DATM_OFF` is a number stored as six characters of text, and holds
  `-9999`, `<Null>`, `NAVD88` and `Feet` as often as an offset. A text-encoded
  null is rejected only by a vocabulary, and free text has none, so these
  validate.
- A page of 2,000 baselines as GeoJSON is a 500 from the service, and 1,000
  sometimes is: the lines are long. The service also drops TLS handshakes
  (curl exit 35) often enough that the first snapshot attempt died partway, so
  every request now retries.

## Reading `R1` as optional

`R1` was read as required when the third layer landed, on the grounds that a
footnote about BLE databases does not change what a FIRM Database must hold.
Seth reversed that on 2026-10-07: the footnote limits the requirement to BLE
databases, and the profile baselines (33.5% rejected, 2.3% without `R1`) are
what made the reading costly enough to revisit. The 22 fields are optional,
and each description ends with the footnote, read from the table's own section
of the reference.

- The fixture filters had the requirement baked in. A case's "clean" clauses
  held every field the model required populated, so a case about a missing
  `START_ID` that now validates contradicted its own filter. The filters now
  allow an `R1` field to be missing, and refetching layer 17 picked a shown
  baseline without a `START_ID`, so that case asks for one.
- The rejection unions were prose, not code. Rebuilding them from
  `spec/README.md` reproduced 113,140 and 113,286 exactly, which is what
  licensed the new totals.
- Validating live pages found a baseline with no geometry: 69 on layer 17, none
  on 14 or 16, and 496 on layer 28. The earlier unions read only attributes,
  so they missed them.

## The fifth layer

Station Start Points (`S_Stn_Start`, 2026-10-08) was picked over Water Lines
because both line layers already modelled name it by key: `START_ID` is its
primary key and the foreign key of `S_XS` and `S_Profil_Basln`. Water Lines
joins them only by `WTR_NM`, a name. It is the first point layer and the first
with no rules: six fields, one of them coded.

- The first legacy value in a second domain broke the warning. `NP` cleared
  layer 13's bar in `LOC_ACC`, and every flood zone with `STUDY_TYP` `NP` began
  to warn. The enums are `str` enums, so `LocAccuracy.NP == StudyTyp.NP` and
  they hash alike: `value in LEGACY_MEMBERS` was a test of the string. It held
  only while no two legacy-bearing domains shared a value. `warn_on_legacy_values`
  now keys members by enum and name. The fixture caught it, not a unit test.
- Empty geometry is not null geometry. 82 station starts come back as
  `{"type": "Point", "coordinates": []}`, and `SHAPE IS NULL` counts none of
  them; `SHAPE.STX IS NULL` counts them, and `SHAPE.STIsEmpty() = 1` is a 400.
  The control found them: the first live page rejected 155 against a union of
  147. Whether the line and polygon layers hold empty shapes beyond their
  `SHAPE IS NULL` counts is not checked; their controls agreed on the pages
  they ran.
- The table states no relationship, so step 3 of "Adding a layer" had nothing
  to add, and a test asserting every modelled table quotes at least one failed
  until it named the tables expected to have none.
- `clean_except_expected` bounded every non-sparse case by `SHAPE.STLength()`,
  which a point does not have; it takes the bound as a parameter now.
- The 2016 and 2019 Domain Tables references were fetched again to check
  whether `D_Loc_Accuracy` ever listed `NP`. Neither did.

## The sixth layer

River Mile Markers (`S_Riv_Mrk`, 2026-10-10) was picked because its required
`START_ID` is "the foreign key to the S_Stn_Start layer", the layer modelled
last. A scan of every reference table for the five modelled keys found two
others, `L_XS_Elev` and `L_XS_Struct`, both by `XS_LN_ID`; neither is on the
service. Water Lines still joins only by name.

- The layer is small enough to validate whole: 13,097 rows in 19 pages. Every
  page's rejections matched the union's count over its `OBJECTID` range, so
  the control covers the population rather than a sample of it.
- The control does not reach the empty-point clause on this layer: no river
  mark is empty. A unit test holds the model to rejecting one.
- The first two `NP` cases fetched the same feature. `NP` in `RIV_MRK_NO` or
  `SOURCE_CIT` never appears without `NP` in `START_ID`, so one case covers
  both.
- No domain, no relationship and no rule: steps 3 and 5's legacy pass had
  nothing to add, and `report-observed` prints a header and nothing under it.

## The seventh layer

Water Lines (`S_Wtr_Ln`, 2026-10-10). No layer joins the modelled ones by a
key any more: the reference's other foreign keys, `TBASELN_ID`, `NODE_ID` and
`CST_MDL_ID`, point at layers and tables not yet modelled. What the modelled
layers share with the rest is `WTR_NM`, the stream's name, a field of Gages,
High Water Marks, Levees, General Structures, Water Areas, Subbasins, Transect
Baselines and Water Lines among the service layers. Water Lines was taken over
those because the reference makes `S_Profil_Basln` the hydrologic structure and
`S_Wtr_Ln` the streams drawn beside it, because its geometry is a line like the
modelled line layers', and because its table has two coded fields and no rule.
Levees and LOMRs stay candidates for the eighth.

- The layer has 6.2 million rows, 28.3 million `OBJECTID`s wide. Counting a
  clause over a geometry (`SHAPE.STLength() IS NULL`) did not finish in 120
  seconds; the same count on `SHAPE IS NULL` or a text field takes seconds. The
  whole-layer validation the river marks got is out of reach, so the control is
  ten pages of 2,000, and three of them held rejections.
- `GROUP BY` folds `''` into the lone space, so `report-observed` printed `' '`
  for 1,029,367 rows of `SHOWN_FIRM`. `LIKE ' '` separates them: 47,976 hold a
  lone space, and 981,391 hold `''`, which the model reads as null.
- `WTR_NM` is `NP` on 46% of the layer (2,817,055 rows), a value that validates;
  a model that read `NP` as null would have counted them as rejections.
- No rule, no unit, no datum: `relationships.json` and `legacy.json` gain
  nothing but the `observed` entry.

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
- **mypy sees `Omitable[X]` as its own class, not `X`.** `Omitable` is a
  `Generic` whose `__class_getitem__` returns `Annotated[X | MISSING, ...]` at
  runtime, so mypy calls `field is SomeEnum.MEMBER` a non-overlapping check.
  Tests compare through `model_dump()` instead.
- **The GeoJSON envelope unwraps only in JSON mode**: validating a parsed dict
  reports every required field missing.
- **Validation reports one broken constraint per feature.** Each constraint is
  its own `model_validator`, and pydantic stops at the first that raises, so a
  feature breaking three rules names one. A count of rejections per rule taken
  from validation errors undercounts every rule but the first to run. The
  revert slices measured each rule ad hoc, running constraints one at a time
  through `ModelConstraint.get_model_constraints` and `validate_instance` on a
  `model_construct`ed instance. `scripts/count-broken-rules` (`make rules`) now
  does that for every rule over the whole layer (`nfhl.rule_counts`), skipping
  a rule where a field it reads fails its own type, as validation would. The AR
  slice had read "rejected by this rule and nothing else" from validation
  errors; it held, but that instrument could not have shown otherwise.
- **"Holds this value" takes two constraints on an optional field.** `SFHA_TF`
  is required, so "will be true" was one `require_any_true`: not the zone, or
  not another flag. `DUAL_ZONE` is optional, and the same sentence needs a
  `forbid_if` for the other flags and a `require_if` for an empty field. The
  generator had only met the required case, so `pair_rules` now adds the second
  half for any field the reference does not require.

## Process

- FEMA's CDN refuses Python's `urllib` (and spoofed user agents) with 403; the
  snapshot script fetches with curl.
- The early slices were committed locally and not pushed until Seth asked why
  (2026-10-05). Push each slice as it lands.
- Re-snapshotting refreshes every count, which breaks `spec/legacy.json` and the
  README figures until they are updated; a test catches the first.
- A new two-field rule forces a full re-snapshot: its pair counts must sum to
  the layer total, so they cannot be taken alone and added to an older file. The
  layer lost 424 rows between 2026-10-05 and 2026-10-07, so the `DUAL_ZONE`
  slice opened with a refresh commit that moved counts unrelated to it.
- The rule checker judges the whole layer without fetching a feature. The
  service accepts SQL expressions in `groupByFieldsForStatistics`, so the nine
  text fields the rules read, plus a populated-or-null `CASE` for each of the
  five numeric ones, group all 5.8 million rows into 884 combinations in one
  query of about 12 seconds; judging a combination judges every row holding it.
  The service's collation got in the way: it folds a lone space into `""`, a
  rejected value into a null, which counted 768 velocities with a lone-space
  unit as breaking the unit rule. Grouping expressions refuse string literals
  and `CHAR_LENGTH` trims blanks, so nothing inside the grouping can tell them
  apart; a `where` with `LIKE ' '` can. The snapshot splits the rows by lone
  space per field first (25 non-empty parts) and groups each, 1,022 groups in
  all. Every per-rule figure in spec/README.md reproduced, including the
  2026-10-06 direct queries for the revert fields; case folding remains.
- A pass re-checking every claim in the README's "what the service holds"
  section (2026-10-05) reproduced every count, and found the claims around the
  counts wrong instead. "Every count is an upper bound" held for single values
  and was backwards for totals. "An earlier edition's study types; unverified"
  stayed unverified because the search covered only the vendored 2024 PDFs.
  FEMA's superseded 2016 and 2019 references settled it, and showed two of the
  five were not missing from 2024 but filed under another domain. Counting
  `V_DATUM` "set" rows also counted values the vocabulary rejects before the
  rule runs (16,933 rows, 16,571 reaching the rule).
