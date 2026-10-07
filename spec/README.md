# Upstream snapshot

A pinned copy of what the models are generated from. Refresh with
`scripts/snapshot-spec`; `MANIFEST.json` records each source URL, when it was
retrieved, the edition, and a SHA-256 of every file.

| Path | Source |
| --- | --- |
| `reference/firm-database-technical-reference.pdf` | FEMA, *FIRM Database Technical Reference*, November 2024, from the [Guidelines & Standards technical references page](https://www.fema.gov/flood-maps/guidance-reports/guidelines-standards/technical-references-flood-risk-analysis-and-mapping). Every FIRM Database table: its fields, whether each is required, its type and length, and which domain constrains it. |
| `reference/domain-tables-technical-reference.pdf` | FEMA, *Domain Tables Technical Reference*, November 2024, same page. The coded-value vocabularies (`D_Zone`, `D_Zone_Subtype`, ...). The FIRM Database reference points here and does not repeat them. |
| `reference/*.txt` | `pdftotext -layout` of each PDF. Derived, not upstream; for grepping, and the second instrument the extraction is checked against. |
| `reference/*.json` | Every ruled table in each PDF, extracted by `nfhl.extract` (pdfplumber). Derived, and **the generation source**. A test re-runs the extraction and asserts it reproduces these files. |
| `service/MapServer.json`, `service/layers/<id>.json` | The [NFHL MapServer](https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer)'s metadata for all 32 layers and its one table: field names, Esri types, lengths. Taken whole so later slices need no new fetch. |
| `service/observed/<id>.json` | Per-value row counts for every domain-bound field of a modelled layer, and per-pair counts for every two fields a rule reads together (`combinations`), from the service's grouped statistics. Observations, not specification. |
| `repairs.json` | **Not upstream.** Corrections to published domain values, each quoting the reference sentence that licenses it. Not in the manifest. |
| `relationships.json` | **Not upstream.** Which field holds another's unit or datum, which fields may be populated only alongside another or only for some zones (the AR revert fields), which values a field is limited to, and which value a field takes when another holds certain values (`SFHA_TF` from `FLD_ZONE`), each quoting the field description it reads. Not in the manifest. |
| `legacy.json` | **Not upstream.** Values outside the reference that at least one row in a thousand of the layer holds, which the models accept with a warning: each with its count from `service/observed/`, and a note on what is known of it. A test asserts it lists exactly what its threshold selects from that snapshot. Not in the manifest. |

## Why PDFs

FEMA publishes the FIRM Database schema nowhere else in structured form. The
service is the data, not the schema: it gives types and lengths but declares no
coded-value domains, no descriptions and no required flags, and it never says
which FIRM Database table a layer serves (`nfhl.spec_source.LAYERS` declares
that join). So the reference defines the model and the service checks it.

The extraction is the link most likely to break, so it is checked from three
sides: re-extraction must reproduce the committed JSON byte for byte; every
domain value the models use must also appear, in order, in the independent
`pdftotext` rendering; and every table the models read must have no
`irregular` rows, which is where `nfhl.extract` puts a row it could not align
with its header rather than guessing.

## How the published values relate to the reference

**The data stores the description, not the coded value, in every
distribution.** `D_Zone` lists `OW` / `OPEN WATER`; the data holds `OPEN WATER`
and never `OW`. The same holds for every domain this slice reads (`Feet` not
`FT`, `SFHA with BFE and floodway` not `1060`). The reference never says so.
Two domains print separate *FRD* and *FIRM* descriptions (`D_V_Datum`,
`D_TrueFalse`); the FIRM one is what is stored (`LOCAL TIDAL DATUM`, `T`), and
the FRD one, which spells the value out (`Local Tidal Datum`, `True (Yes)`), is
what each enum member's description gives as its meaning.

Checked on 2026-10-05 against all three ways FEMA distributes the NFHL, from
the [Map Service Center](https://msc.fema.gov/portal/advanceSearch) product
search (`POST /portal/advanceSearch`, then
`GET /portal/downloadProduct?productTypeID=NFHL&productSubTypeID=...&productID=...`):

- **The map service** declares no domain on any layer 28 field
  (`jq '.fields[].domain' service/layers/28.json` prints only `null`), so what
  a query returns is what is stored; there is no coded value to translate from.
- **The state file geodatabase**, `NFHL_11_20241031.gdb` (District of Columbia,
  `NFHL_STATE_DATA`), has no coded-value domains:
  `ogrinfo -ro -json -so NFHL_11_20241031.gdb S_FLD_HAZ_AR | jq .domains` prints
  `{}`. Its `S_FLD_HAZ_AR` holds `AE`, `FLOODWAY`, `0.2 PCT ANNUAL CHANCE FLOOD
  HAZARD`, `NAVD88`, `Feet`, and `VERSION_ID` on every row, as text.
- **The county shapefiles**, `51179C_20230621.zip` (Stafford County, Virginia)
  and `39105C_20140519.zip` (Meigs County, Ohio), `NFHL_COUNTY_DATA`, hold the
  same text: `OPEN WATER`, `SFHA with BFE and floodway`, `NAVD88`, `Feet`, and,
  in Meigs, `REDELINEATION` and `SFHAs WITH LOW FLOOD RISK`.

Converted to GeoJSON with `ogr2ogr -f GeoJSONSeq`, all 1,748 Stafford features
validate against the model. Of the 652 District of Columbia features, the 51
that fail all hold `ZONE_SUBTY` `AREA WITH REDUCED FLOOD RISK DUE TO LEVEE`, a
value the reference does not list. The downloads write a missing text value as
a true null where the service sometimes writes `""`, and keep `-9999` for
numbers; the models read both. The archives are not vendored.

**Rows for other FEMA databases are excluded.** Each domain row has an
"Applies to Database Schema" column; only rows naming FIRM are kept. `D_Zone`'s
`NP` and `D_Study_Typ`'s `OTHER` are FRD-only.

**`D_Zone_Subtype` is printed with dashes the database does not use.** The
reference says so itself, under the table: "the dashes will stay in the Domain
Tables Technical Reference, however the FIRM DB template will not have dashes".
`repairs.json` removes them from the PCT phrases only (`0.2-PCT-ANNUAL-CHANCE`
to `0.2 PCT ANNUAL CHANCE`), because the service publishes
`... DUE TO NON-ACCREDITED LEVEE SYSTEM` with its dash, and the note does not
say which dashes it means.

**Two null encodings, from section 7.3.** A field that does not apply is `""`
(text) or `-9999` (numeric), because the GIS formats cannot hold a true null.
The models read both, and JSON `null`, as not populated.

## What the November 2024 references get wrong

Each is pinned by a test, so an upstream change shows up as a failure.

- **`VERSION_ID` is required by the reference and absent from the service.**
  The model makes it optional; a field that cannot be published cannot be
  required of published data.
- **Lengths disagree.** `FLD_AR_ID` is 25 in the reference and 32 on the
  service; the model takes the service's. `AR_SUBTRV` is 76 in the reference and
  57 on the service, shorter than five of the 33 `D_Zone_Subtype` values the
  field draws on.
- **The zone/subtype cross-walk (Table 14) does not match the domain.** It writes
  `NON_ACCREDITED` with an underscore in the AE row, and its footnote markers
  are set inline, so `COASTAL FLOODPLAIN2` extracts as one word. `repairs.json`
  restores the dash, and `SpecReader.subtype_crosswalk` reads each cell by
  matching the domain's printed values, longest first, past a trailing marker.
  The two footnotes are not modelled: 1 cites the CFR, and 2, "These zone
  subtypes should only be used in coastal areas", names a condition no field
  records.
- **`D_Study_Typ` 1070 ends in a typographic apostrophe**, `less than 1’`.
  Most published rows use the ASCII one (below). Not repaired: nothing in the
  reference says which is meant.
- **`AR_SUBTRV` cites "the D_Zone_Subtype_ table"**, with a stray underscore;
  its type table names `D_Zone_Subtype` correctly.
- **The AR fields' descriptions leave two things open**, and the models take
  the narrower reading of each. `AR_SUBTRV` "must be one of the allowable
  subtypes for Zones AE, AO, AH, A or X", which names the five zones together:
  read as the union of their Table 14 rows, not as a pair with the zone in
  `AR_REVERT`, though the field is "the zone subtype that area would revert
  to". So `AH` with `FLOODWAY`, a subtype Table 14 lists for `AE` only,
  validates; and an AR zone reverting to `X`, whose row has no `<NULL>`, need
  not name a subtype. Nor does either description say an AR zone must populate
  them, so nothing requires them. `AR_REVERT` "should only include" the five
  zones, the same "should" as `SFHA_TF`'s rule, and is enforced like it.
- **`BFE_REVERT` and `DEP_REVERT` say "populated when", not "only populated
  if"**, and the models read the sentence as a limit to AR zones only. "This
  field is populated when Zone equals AR and the reverted zone has a static BFE"
  (or "a depth assigned") opens with "If zone is Zone AR in FLD_Zone field, this
  field would hold" the reverted zone's BFE or depth, which gives the number no
  meaning on any other zone. The other half, a BFE or depth required on an AR
  zone whose reverted zone has one, is not checked: whether the reverted zone
  has a static BFE is recorded nowhere but these fields. Nor are they tied to
  the zone in `AR_REVERT`. Neither description names the zones, and `DEPTH`,
  "the depth for Zone AO areas", is not limited to `AO` either.
- **The revert numbers have no unit or datum.** `LEN_UNIT` is "the
  measurement system used for the BFEs and/or depths", which could cover them,
  but "is only populated if the STATIC_BFE or DEPTH field is populated", so an
  AR zone with only a `BFE_REVERT` could not state one. `V_DATUM` is limited to
  `STATIC_BFE` the same way. The models link neither field to them.

Nine of the reference's 53 tables do not yet join their description table to
their type table, so `SpecReader.reference_table` raises on them: `L_Mtg_POC`
spells a field `E-MAIL` in one and `EMAIL` in the other; `S_XS` and
`L_Profil_Label` wrap field names mid-word (`STREAM_ST N`, `RIENT`);
`S_Alluvial_Fan`, `S_Cst_Gage`, `S_Label_Pt` and `S_Nodes` each have a blank row;
`L_Comm_Revis` and `L_Profil_Bkwtr_El` head the requirement column
`R/A/ OR/ A` and `R/A/O`. In the Domain Tables reference, `D_SFHA_FLDWY` and
`D_Time_Units` have irregular rows, and `D_Zone_Subtype`'s rotated "Footnote"
header extracts reversed. None of these is in this slice.

## What the service holds that the reference does not allow

`scripts/report-observed` prints these from `service/observed/28.json`; the
counts below are its output for the snapshot pinned in `MANIFEST.json`. The
models reject every one except the eight it marks `legacy`, which
`legacy.json` admits with a warning by a count threshold, not by a judgement
about each value.

- **`STUDY_TYP`: 1,858,473 of 5,810,408 rows (32.0%) hold a value outside
  `D_Study_Typ`**, not counting the 1,607 lone spaces below. Most are the study
  types of the [November 2016 Domain Tables reference](https://www.fema.gov/sites/default/files/nepa/Domain_Tables_Technical_Reference_Nov_2016_SUPERSEDED.pdf),
  which the [February 2019 edition](https://www.fema.gov/sites/default/files/2020-02/Domain_Tables_Technical_Reference_Feb_2019.pdf)
  replaced: `SFHAs WITH LOW FLOOD RISK` (979,597), `... HIGH ...` (557,258),
  `... MEDIUM ...` (193,351), `REDELINEATION` (72,844) and `DIGITAL
  CONVERSION` (12,946). The 2019 and 2024 editions list the last two under
  `D_Study_Mth`, the study method. Then the ASCII apostrophe, `Shaded Zone X
  with depths less than 1'` (33,992); the 2019 edition's code 1000, `Special
  Flood Hazard Area (SFHA) without BFE`, cut to the field's 38 characters
  (`Special Flood Hazard Area (SFHA) witho`, 6,493); FRD-only `OTHER` (1,485);
  and a bare coded value, `1050`, once.
- **`ZONE_SUBTY`: 26,355 rows outside `D_Zone_Subtype`**, 75 of them the lone
  spaces below. Chiefly the 2019 edition's `AREA WITH REDUCED FLOOD RISK DUE TO
  LEVEE` (24,849), compound subtypes such as `1 PCT FUTURE CONDITIONS,
  FLOODWAY`, and the literal string `<Null>` (343).
- **`V_DATUM`**: `ASVD02` (562, American Samoa, absent from `D_V_Datum`),
  `GUVD03` (199, where the reference lists `GUVD04`), `NAVD 88` and `NGVD 29`
  with spaces, and `-9999` written as text (302).
- **Text fields hold the numeric null as a string**: `-9999` in `V_DATUM`,
  `LEN_UNIT`, `VEL_UNIT`, `AR_REVERT` and `AR_SUBTRV`, and `<Null>` in most of
  them.
- **The zone rules reject 711 rows**, counted from the snapshot's value pairs.
  Against Table 14: `AO` with `COASTAL FLOODPLAIN` (236), `X` with `AREA OF
  SPECIAL CONSIDERATION` (149), `A` with `ADMINISTRATIVE FLOODWAY` (119) or
  `FLOWAGE EASEMENT AREA` (2), `AE` with `RIVERINE FLOODWAY SHOWN IN COASTAL
  ZONE` (93), `AH` with `COASTAL FLOODPLAIN` (55) or `FLOODWAY` (16), and no
  subtype on `A99` (23 of the layer's 24) or `X` (1). Against `SFHA_TF`'s
  description: `AE` flagged `F` (2), and `X` flagged `T` (14) or `U` (1). The
  largest, 236, is 4% of the legacy bar of 5,811 rows, so every rule rejects;
  a test fails if a rejected pair ever clears the bar, since the models have no
  way to accept a pair with a warning.

- **The AR rules reject 79 rows, all for being populated off an AR zone.**
  The layer holds no AR zone (`FLD_ZONE = 'AR'` counts 0), so every row whose
  `AR_REVERT` or `AR_SUBTRV` the field's vocabulary accepts breaks the
  only-in-AR rule: `AR_REVERT` `A` (72) or `AE` (1), and `AR_SUBTRV`
  `0.2 PCT ANNUAL CHANCE FLOOD HAZARD` (3), `FLOODWAY` (2) or `AREA OF
  MINIMAL FLOOD HAZARD` (1). The limits on their values reject none. Values
  the vocabulary already rejects (`-9999` and `<Null>` written as text,
  `NSPNUL`, `NP`, lone spaces) never reach a rule. On 2026-10-05 the same 79
  came back from the service by direct query (`FLD_ZONE <> 'AR' AND AR_REVERT
  IN (<every D_Zone value>)`, 73; the same for `AR_SUBTRV` and every
  `D_Zone_Subtype` and legacy value, 6). Each of those 79 features breaks its
  only-in-AR rule and no other, found on 2026-10-06 by running every
  constraint on its own. Validating them cannot show that: validation stops at
  the first rule that fails, so a feature breaking three reports one.
- **The revert BFE and depth rules reject 18,177 rows**, all off AR zones:
  `BFE_REVERT` is populated on 12,732 and `DEP_REVERT` on 17,914
  (`BFE_REVERT IS NOT NULL AND BFE_REVERT <> -9999`, and the same for
  `DEP_REVERT`; 18,177 with `OR`), on 2026-10-06. None of them holds a zone
  in `AR_REVERT`: the 73 rows that do hold `-9999` in both. Most are stand-ins
  for "does not apply": `0` (9,830 and 11,679), which section 7.3 forbids for
  that, and `-8888` (2,850 and 2,906), its "intentionally not populated". Of
  the 52 other `BFE_REVERT` values, 17 are `9999`. Of the 3,329 other
  `DEP_REVERT` values, 3,311 are in DFIRM `31099C`, where each is the
  polygon's area in square feet: across 2,000 of them, `DEP_REVERT /
  SHAPE.STArea()` is 1.011e11 to 1.015e11, the square feet in a square degree
  at that latitude. Running each constraint on its own over samples (all 52
  other `BFE_REVERT` rows; the first 2,000 of the other `DEP_REVERT` rows and of
  the `BFE_REVERT = -8888` rows; the first 500 of each `0`) finds every row
  breaking the rule for each revert field it populates.

These were counted with direct queries against layer 28 on 2026-10-05 rather
than from a committed file; each is a `returnCountOnly` query with the `where`
clause given:

- **Lone spaces**, which the reference's null encodings do not include:
  `V_DATUM LIKE ' '` 60,619; `LEN_UNIT` 78,373; `AR_REVERT` 74,471; `VEL_UNIT`
  59,804; `DUAL_ZONE` 43,768; `AR_SUBTRV` 37,342; `STUDY_TYP` 1,607;
  `ZONE_SUBTY` 75. These are exact: `LIKE ' '` matches one space and not the
  empty string, and `LIKE '  %'` matches nothing in any of these fields, so no
  value holds two. Fetching the rows agrees: `STUDY_TYP = ''` returns 8,039,
  of which 6,432 hold `''` and 1,607 hold `' '`.
- **The populated-only-if rules** (`relationships.json`):
  `V_DATUM` set without a static BFE, 16,933
  (`(V_DATUM IS NOT NULL AND V_DATUM <> '') AND (STATIC_BFE = -9999 OR STATIC_BFE IS NULL)`),
  of which 16,571 hold a `D_V_Datum` value and reach the rule, the rest failing
  the vocabulary first; `LEN_UNIT` set with neither BFE nor depth, 1,807
  (the same, with `(DEPTH = -9999 OR DEPTH IS NULL)` added), 1,468 of them a
  `D_Length_Units` value; a velocity without a `VEL_UNIT`, 8,638
  (`(VELOCITY <> -9999 AND VELOCITY IS NOT NULL) AND (VEL_UNIT IS NULL OR VEL_UNIT = '')`),
  1,257 of them a lone space the vocabulary rejects first. The same velocity
  predicate selects 9,679 rows, 7,708 of them `0`, which section 7.3 forbids
  as a stand-in for "does not apply"; 7,681 of the 8,638 without a unit are
  `0`, so most of those are nulls written as zero.

**Read a count as the service's, not the models'.** The service is SQL Server
(it accepts `SHAPE.STArea()` in a `where`), and its `=`, `<>`, `IN` and
grouping ignore case and trailing blanks: `LEN_UNIT = 'feet'` and `LEN_UNIT =
'Feet '` count the same 197,726 rows as `LEN_UNIT = 'Feet'`, and `= ''` matches
a lone space. `LIKE` ignores case but not a trailing blank in its pattern,
which is why the lone-space counts use it. Folding errs in both directions. A
count for one value is an upper bound on that exact string: it includes every
variant differing only in case or trailing blanks. A total of values outside a
vocabulary is a lower bound: a variant of an allowed value folds into that
value's group and drops out of the report. The 1,607 lone spaces in
`STUDY_TYP` came back inside its 8,039 blanks and are missing from its
1,858,473, while `ZONE_SUBTY`'s 75 came back as `' '`, because no empty string
shared their group, and are counted in its 26,355. The fixture holds one real
`FEET` (`uppercase_len_unit`, DFIRM `39057C`), found because it failed
validation, not because any statistic showed it.
