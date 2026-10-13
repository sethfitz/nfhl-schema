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

## The eighth layer

Levees (`S_Levee`, 2026-10-10), over LOMRs. Neither joins a modelled layer by
key. Levees names its stream by `WTR_NM`, as the cross sections, BFE lines,
profile baselines and water lines do; its `LEVEE_STAT` is the accreditation
the flood zones' levee subtypes (`AREA WITH REDUCED FLOOD RISK DUE TO LEVEE`)
record, and its `PAL_DATE` is "associated with the flood zone". LOMRs has no
shared field and no domain beyond `SCALE` and `STATUS`. Levees also has three
rules in prose and the first two `Date` fields.

- The codegen had no `Date`. The service writes a date as milliseconds since
  the epoch and the reference's null date, 9/9/9999, as `253392451200000`;
  `int64`, and a third null encoding in `drop_null_encodings`, was the least
  that read them. A `datetime` would have parsed the milliseconds and not the
  state geodatabase's strings, and `overture-codegen` has no date type to
  document it with.
- "Should only be populated if LEVEE_STAT is Non-Accredited" rejected 8,821 of
  the 9,443 levees holding `NP` in `LEV_AN_TYP`, since `NP` stayed a value
  everywhere. Section 7.3's own sentence made `NP` the field left empty, so
  `only_when` gained an `unless` and `required_when` a value condition
  (`DISTRICT` is required when `USACE_LEV` is `T`), each quoting its sentence.
- `FC_SEG_ID` is `R`, and 82% of the layer lacks it. It decided the fixtures:
  a finding in any other field co-occurs with a missing `FC_SEG_ID`, so seven
  cases the earlier layers would have kept do not exist here.
- The whole layer is 16,320 rows, so the control pages all of it, which the
  river marks' and water lines' controls could not. It found four rows the
  query cannot: values in the wrong case, which the service's collation folds
  into the listed value. The same fold hid them from the snapshot's counts.
- A rule's rejection shows only when every field validates, and two rules on
  one levee show one: 43 levees are reported under the analysis rule and 44
  break it.

## The ninth layer

LOMRs (`S_LOMR`, layer 1, 2026-10-10). Eight fields, no rule, no unit, no datum,
and two domains that are digits and words: the cheapest layer since the water
lines, and the first with nothing for the codegen to learn.

- The first polygon layer that is a Polygon alone. The flood zones are
  `POLYGON` or `MULTI_POLYGON`; "Multipart polygons are not allowed" holds this
  one to a single part, and four of 10,150 rows break it. A multipart polygon
  cannot be selected by a `where` on this service (`STNumGeometries()` and
  `STGeometryType()` are a 400), so the union query is four rows short of the
  model, as the levees' was, for a different reason: not a collation fold but
  a predicate the service lacks. Paging the whole layer found them.
- An empty polygon is `SHAPE.STArea() = 0`, not `SHAPE IS NULL`; the same split
  as the empty point, found the same way, by validating every row.
- `reference_intro` looked for "contains information about" and S_LOMR says
  "includes all LOMRs". Falling back to the table summary would have described
  the layer as "LOMRs not yet incorporated on the FIRM", the opposite of the
  section, so the search takes "includes" too.
- `SCALE` is a number written as text and its three outliers hold the domain's
  coded value `1000` for `6000`. No mapping is guessed; the three are rejected.

## The tenth layer

Flood Hazard Boundaries (`S_Fld_Haz_Ln`, layer 27, 2026-10-10). The lines that
bound the polygons of the flagship layer, with five fields, one domain and no
rule, so the codegen learned nothing. It joins `S_Fld_Haz_Ar` only by geometry
(Table 4: `S_Fld_Haz_Ln` "Must Be Covered by Boundary Of" `S_Fld_Haz_Ar`) and by
the three fields the two share; no remaining layer has a foreign key to a
modelled one, so none joins more directly.

- The layer has 15.2 million rows, `OBJECTID` to 70.2 million, and some
  boundaries are huge: the first 250 rows by `OBJECTID` are 26 MB of GeoJSON,
  and a page of 2,000 is a 500. The control is 200-feature pages. Rejections
  cluster in `OBJECTID`, so pages cannot stand in for a layer-wide rate: 8 of 50
  pages held 182 or more `SOURCE_CIT` rejections each and 42 held none, against
  9.5% of the layer.
- `SHAPE IS NULL` took 152 seconds as a bare count on the first attempt and
  the whole union, which contains it, took 18 seconds later in the session; a
  timing says what the service was doing, not what the clause costs.
- `SOURCE_CIT` is missing on 9.5% of the layer (1,448,053 rows), the highest
  rate of any modelled required field, and `NP` on another 1,782,479.

## The eleventh layer

Political Jurisdictions (`S_Pol_Ar`, layer 22, 2026-10-11). Chosen because
Table 4 puts it in the `FLD_HAZ_POL` topology with both flood hazard layers and
requires the flood zones' boundary to be "Covered by Feature Class Of" it; no
remaining layer has a foreign key to a modelled one.

- The first rule on free text that reads the value. `ANI_FIRM` is limited to ANI
  areas with `NP` exempt, as in the levees, but the levees' field had a domain.
  The codegen rendered `unless` only as enum members, and the rule census
  refused any rule that asked free text more than whether it is set; both now
  take plain strings, and the census groups such a field by value (193 groups).
- `D_State_FIPS` is the first domain whose stored value is the coded value: its
  FIRM description is `01`, not `Alabama`. The FIRM-description column rule
  already gave the right answer.
- Four states' codes without their leading zero clear the legacy bar, so a
  warning admits `5` while `05` is the reference's value. That follows from the
  count rule, and it is the first legacy value that is a formatting defect
  rather than an older edition's vocabulary.
- `SHAPE.STArea() = 0`, which found the LOMRs' empty polygon, here finds a real
  sliver; the empty-geometry test is per layer, and `STLength() = 0` was the one
  that showed there is none.
- Small enough to validate whole, unlike the last two. One page of 200 failed
  after every retry and went through at 50; the six-cursor run took about 15
  minutes. `generate-models` deletes `src/nfhl/models/` before rendering, so a
  generation error leaves the tree without models until `git checkout`.

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
- The count threshold met its first exception on 2026-10-11: Arizona's unpadded
  `4` (17 rows, one DFIRM) sat under layer 22's bar of 89 beside four unpadded
  states above it, the same defect at a smaller count. A count cannot see that
  two values share a cause. `legacy.json` gained a `decision` field for the
  maintainer's call, and the selection test splits in two: undecided entries
  must equal what the threshold selects, decided ones must be values it does not
  select, at the count the snapshot holds.

## The twelfth layer

FIRM Panels (`S_FIRM_Pan`, layer 3, 2026-10-12). The relationship criterion is
used up: every foreign key a modelled layer holds names a modelled layer or an
`L_` table, and Table 4's remaining rules are within one layer. A scan of every
reference description for a `S_` name outside the modelled set finds only
unmodelled layers pointing at each other (`S_Hydro_Reach` at `S_Nodes`,
`S_Cst_Tsct_Ln` at `S_Tsct_Basln`, the label layers at `S_FIRM_Pan`). Chosen
for what it shares: `ST_FIPS` and its legacy codes with the political areas, the
FIRM Database fields, a single rule, and the panel number that joins four other
tables. The next layer has no relationship to pick it by.

- The wrong-case values cost the first live control run: 299 rows (`ORTHOPHOTO`,
  `COUNTYWIDE, PANEL PRINTED`, `COUNTYWIDE, NOT PRINTED`) the model rejects and
  the union cannot select. They are 4% of the rejected rows, against a handful
  on the levees, and `ORTHOPHOTO` (211) is over the legacy bar the snapshot
  cannot count because it folds case. A control run has to list the model-only
  rows by field and value, or an unexplained difference reads as a failure.
- A rule that reads a field with a vocabulary fires only on rows whose value
  validates. The first fixture filter for the `PNP_REASON` rule demanded a
  `Not Printed` type, so rows with a truncated type and a reason matched no
  case; the filter has to mean "the rule would fire", not "the field is right".
- `PRE_DATE` is `9/9/9999` on 170,984 of 183,680 rows, so a case for a missing
  date is a case for the encoding. My first comment on that case quoted 1,609,
  the `IS NULL` count, for the encoded rows.
- `FIRM_PAN` is "made up of" four other fields and disagrees with them on 13,879
  rows, 12,002 of those for reasons other than the legacy `ST_FIPS`. A
  value-follows-value rule (SFHA_TF from FLD_ZONE) has a lookup; this one is a
  concatenation, the service rejects it in a `where`, and the codegen has no
  expression for it.
- Panels are neatlines, so the fixtures' `SMALL` filter excludes most cases and the
  fixture takes whole polygons (80 KB for 27 cases).
- Lone space in free text is a value (the convention for `ANI_FIRM`), which
  makes 6,307 of the rule's 6,688 rejections a single blank character in
  `PNP_REASON`.

## The thirteenth layer

`S_Gen_Struct` (layer 24). The chain the FIRM Panels pass left, `FIRM_PAN` as a
join key of `L_Pan_Revis`, `L_MT2_LOMR`, `S_Label_Ld` and `S_Label_Pt`, ends at
once: none of the four is a service layer, and a `Layer` needs a service id for
its fields, so those tables cannot be modelled from this snapshot. The pick
went by shared fields instead: `WTR_NM` with the water lines and `SHOWN_FIRM`
with the water lines and profile baselines.

- The case-folded snapshot misled the legacy selection for the first time. The
  group it counts and the form it shows are different things: the shown
  `Floodway Contained In Structure` (292) was 114 reference rows and 178
  wrong-case ones, and the shown `1 Pct ...` (13,200) was 310 rows of that
  form and 12,890 of `PCT`. The selection test compared case-sensitively,
  so it demanded a legacy entry for a reference value. Fixed by comparing
  folded; the second case stays a call (below).
- 23,447 rows hold a `PCT` form of a legacy percent type, and 22,847 of them
  (8.0% of the layer) broke nothing else, against 299 wrong-case rows on the
  panels and a handful on the levees. The
  threshold admitted the form the snapshot shows and the model rejected its
  other cases, so the commonest forms of a legacy value were the rejected ones,
  and rejections stood at 11.3%. A decision admitted the `PCT` forms, which
  brought the layer to 3.3%. The threshold cannot select a form the snapshot
  never shows, so each decision entry is counted row by row, and the test
  bounds it by its group's count instead of finding it in the snapshot. The
  forms also share an enum member name once upper-cased, so the generator
  numbers them (`_CASE_2`); it had only ever met a legacy name colliding with a
  reference one.
- A wrong-case reference value is a different call from a wrong-case legacy
  one: `Floodway Contained In Structure` (178) stays rejected, as `ORTHOPHOTO`
  does on the panels.
- The fixture needed 180 ids pinned out of every case: `IN (<reference
  types>)` matches them, and no `where` separates them from the right form.
- Windowing the control by a fixed `OBJECTID` width does not work here: 285,947
  rows span ids to 2,350,391. Windows cut from the sorted ids hold a stable
  1,000 rows each.
- The section for the table has no "contains information about" sentence, so
  `reference_intro` raised; the second table in `SUMMARY_ONLY`.
- `STRUC_DESC` is required for the contained types, and the legacy policy
  forbids a rule that rejects a common pair, so the rule's own subject (the
  legacy forms, 14,445 rows with no description) is left unchecked.

## The fourteenth layer

`S_Wtr_Ar` (layer 32, 2026-10-12), picked as the general structures were, by
shared fields: `WTR_NM`, `SHOWN_FIRM` and `SHOWN_INDX` with the water lines,
which the reference says must match a water area exactly where both draw a
feature. Seven fields, no rule, Polygon and MultiPolygon.

- The layer's one legacy value broke the warning machinery. `SHOWN_FIRM`
  holds `1` on 888 rows, over the bar, and the model accepted it without a
  warning. `LEGACY_MEMBERS` was a frozenset of `str` enum members, and
  `TrueFalse.V_1 == "1" == StateFIPS.V_1`, so the set kept Alabama's
  unpadded code and dropped the flag. The comment in `nfhl.legacy` already
  said membership must go by enum, not value; the generated collection did
  not. The tests had the same blind spot: `StateFIPS(code) in
  LEGACY_MEMBERS` compares by value, so it would have passed with either
  member missing. Only the fixture's warning assertion caught it. It is a
  tuple now.
- A count on one layer admits a value into a domain every layer shares.
  `1` is the first legacy value in `D_TrueFalse`, so it validates with a
  warning in ten flags on eight layers, though only four DFIRMs of water
  areas hold it.
- The live control's first run died after about 250 of 780 windows: one
  window held polygons in `22051C` whose perimeters run to 8,616 degrees, and
  the service errored rather than return them. The run kept nothing. The
  second cached each window, halved a failing range, and read the 40
  polygons with a perimeter over 5 degrees generalised; it read every row
  in about 20 minutes.
- `SHAPE.STArea() = 0` finds empty polygons and slivers alike: 2 empty, 54
  that validate. Validating every row found a third empty one, `206560`,
  which reports 309,055 square degrees. Five more polygons in the same DFIRM
  report areas larger than the Earth and validate, since the model checks a
  geometry's type and rings, not its extent.
- The union's clauses summed exactly to the union (12,855): no row breaks
  two fields, apart from the 686 whose two flags are both a lone space.
  Every lone-space flag is in one DFIRM, `27127C`.

## The fifteenth layer

`S_Tsct_Basln` (layer 18, 2026-10-12), the first of the coastal cluster: the
coastal transects join it by `TBASELN_ID`, so the fields they share get settled
on this ten-field, 35,354-row layer first. A LineString, no rule, and a
`V_DATUM` that is the contour's datum rather than any field's.

- `reference_intro` raised again, for a new reason. The section has the
  sentence, but calls the table a "spatial file", not a table or a layer. The
  pattern takes that noun now; `SUMMARY_ONLY` would have thrown away an
  introduction the section has.
- The threshold selected three types, and two of them are not spellings of a
  transect baseline type at all. `NON-ERODIBLE BLUFF` is a shoreline type from
  `D_Shr_Typ`, written into the wrong field in two Maine DFIRMs, and `ZERO FOOT
  C` is a type cut to 11 characters, too short to say which of three it was.
  The rule admits by count, so both validate with a warning. The brief asked to
  keep such values rejected, which the selection test forbids: `legacy.json`
  has a field to admit a value below the bar and none to hold one above it. The orchestrator's answer was to admit by
  threshold and flag them for Seth, as `SHOWN_FIRM` `1` was.
- The case-folded snapshot hid a historical spelling this time, not a typo.
  The 19 rows the model alone rejects hold `Referenced To Tidal Datum`, the
  2016 reference's exact text, which the 2019 edition changed to `to`. The
  snapshot shows the group as the 2024 spelling, 24 rows, of which 5 are.
- A clean fixture case picked up a legacy value. The first filter allowed the
  legacy types in `TBASE_TYP`, so `not_populated_name` drew a `ZERO FOOT C` row
  that warned; the clean filter now takes the reference's values only. The
  shoreline type under the bar makes no case: all 13 rows also lack
  `SOURCE_CIT`.
- The live control's first full run died in the 154k-157k id range. The
  service answered 500 for windows whose halves it then returned. Bisecting by
  hand found no bad row: every single id came back. Load, not one oversized
  shape, as the water areas had. Halving each failed window got through, at
  about two minutes of curl retries per failure.
- The union (140) is the 140 missing `SOURCE_CIT`. The 13 shoreline types are
  among them, and the 19 wrong-case rows are the whole difference, so the
  layer's rejections (0.45%) are two DFIRMs' missing citations and one DFIRM's
  old spelling.

## The sixteenth layer

`S_Cst_Tsct_Ln` (layer 15, 2026-10-13), the second of the coastal cluster: 41
reference fields, 22,367 rows, a LineString, no rule, and units and a datum that
follow other fields. The model rejects 39.76% of the layer, the most of any so
far, and 4,178 of those rows are invisible to the service's own SQL.

- The first generation failed on a domain name. The field table joins
  `VZONE_EXT` to `D_VZONE`; the Domain Tables section is `D_VZone`. Nothing had
  joined a name that differed only in case, so `domain` raised `KeyError`.
  `SpecReader.domain_name` matches without case.
- `D_Time_Units` listed four of seven values. Its second page draws a rule
  inside `Type`, pdfplumber cut the header into `T` and `ype of Time Unit`, the
  three rows of that page fit no table, and the extraction kept them as
  `irregular` under a header of their own. `domain` took the first table of a
  section and never saw the second. The guard on irregular rows of modelled
  tables fired the moment `TIME_UNIT` was modelled, which is the guard working:
  an unmodelled domain with the same defect would have stayed wrong. `SECONDS`
  is 7,788 of the field's rows, so a legacy entry would have admitted the
  reference's own most common value with a warning.
- The live data and the vendored `D_Event` disagree in the way `D_Zone_Subtype`
  does, and under the same note ("the FIRM DB template will not have dashes").
  The repair for `D_Zone_Subtype` is scoped to `-PCT-`; `D_Event` needed none
  of that care, since every dash in it joins words.
- Admitting a value by one layer's count admits it for every layer on the
  domain. `ASVD02` (374) and `GUVD03` (62) pass the bar here, and the zones,
  BFEs and cross sections that had them rejected now validate them with a
  warning: three fixture cases moved from `expect` to `warns`, and one count in
  `spec/README.md` and `test_rule_counts` moved from 16,571 to 16,572, the one
  zone that holds `ASVD02` without a static BFE and now reaches the rule. The
  full suite caught all four; no test of this layer would have.
- A legacy warning is raised after validation, so a row the model rejects never
  warns. A fixture case that expects a rejection says nothing about the legacy
  values on the same row, and the three `NA` columns, `OPEN COAST` and the
  `NP` values sit on rows the model rejects or on rows with two legacy fields.
  Only one real row holds a single legacy value (`EVENT_TYP` `NP`); the other
  eleven are tested by changing one field of a real valid row.
- Case variants are thousands of rows here: 4,762 rows across 106 DFIRMs, 89 of
  them rejected for nothing else. Pinning by `OBJECTID` does not fit in a
  `where`, so the clean cases exclude the 106 DFIRMs and the cases that need
  one are pinned. The service accepts no `COLLATE`, `ASCII` or `BINARY_CHECKSUM`
  in a `where`.
- The control's model-only rows (4,178) equal the case-variant rows computed
  from the exact forms (`modelonly15.py`); the per-value sum is 4,240 because 62
  rows hold two. The union (4,715) is contained in the model's rejections.
- `LEN_UNIT` and `TIME_UNIT` "are populated when" any of three or four fields
  is. `RequiredWhen` followed one field; it now takes `when_any_populated`, a
  list, and `nfhl.constraints.AnyOf` renders it. Its `any_of` already meant the
  values of `when`, so the new name says what is listed. The SQL clauses count
  1,950 and 3,657 rows, and `judge` finds exactly those rows broken. The model
  rejects 779 and 1,826 rows it accepted before (8,893 to 11,498 of 22,367):
  the other 1,171 and 1,831 hold a rejected field too, and a model rule never
  runs on a row with a rejected field. The reference writes `SETUP_DEPTH`; the
  field is `SETUP_DPTH`. Every real "clean" fixture case had to be re-filtered:
  `not_populated_datum` held a `-8888` period and no `TIME_UNIT`.
