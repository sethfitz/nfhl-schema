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
| `service/observed/<id>.json` | Per-value row counts for every domain-bound field of a modelled layer, and per-pair counts for every two fields a rule reads together (`combinations`), from the service's grouped statistics. Observations, not specification. `snapshot-spec --layer ID` refreshes one layer's and keeps the others'. |
| `repairs.json` | **Not upstream.** Corrections to published domain values, each quoting the reference sentence that licenses it. Not in the manifest. |
| `relationships.json` | **Not upstream.** Which field holds another's unit or datum, which fields may be populated only alongside another or only for some zones (the AR revert fields), which values a field is limited to, and which value a field takes when another holds certain values (`SFHA_TF` from `FLD_ZONE`, `DUAL_ZONE` from `AR_REVERT`), each quoting the field description it reads. Not in the manifest. |
| `legacy.json` | **Not upstream.** Values outside the reference that at least one row in a thousand of the layer holds, which the models accept with a warning: each with its count from `service/observed/`, and a note on what is known of it. A test asserts it lists exactly what its threshold selects from that snapshot, besides the values whose `decision` admits them below the bar. Not in the manifest. |

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

**Three null encodings, from section 7.3.** A field that does not apply is `""`
(text), `-9999` (numeric) or `9/9/9999` (date), because the GIS formats cannot
hold a true null. The service writes a date as milliseconds since the Unix epoch,
so the third is `253392451200000`. The models read all three, and JSON `null`, as
not populated; `8/8/8888`, the date form of "not populated", is a value and stays
one.

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
- **`S_Profil_Basln`'s `FLD_PROB2` and `FLD_PROB3` cite `FLD_PRB1` and
  `FLD_PRB2`**, fields the table does not have; the relationships quote them as
  printed and read them as `FLD_PROB1` and `FLD_PROB2`.
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
- **`DUAL_ZONE` is defined by examples, and the models read it from
  `AR_REVERT`.** "Zone AR/AE, Zone AR/AH, Zone AR/AO, Zone AR/A" names an AR
  zone by what it reverts to, so `T` is required when `AR_REVERT` holds one of
  those four, and `F` when it holds `X`. "Shaded X" has no value of its own: an
  AR zone reverting to `X` takes `F` whatever its `AR_SUBTRV`, including the
  unshaded `AREA OF MINIMAL FLOOD HAZARD`, which no sentence names. An AR zone
  with no `AR_REVERT` takes no `DUAL_ZONE` rule. Neither sentence limits the
  field to AR zones, so `T` off one validates. "For any for AR Zones" is the
  reference's typo, quoted as printed.

Eight of the reference's 53 tables do not yet join their description table to
their type table, so `SpecReader.reference_table` raises on them: `L_Mtg_POC`
spells a field `E-MAIL` in one and `EMAIL` in the other, and `L_Profil_Label`
`ORIENT` and `RIENT`; `S_Alluvial_Fan`, `S_Cst_Gage`, `S_Label_Pt` and `S_Nodes`
each have a blank row; `L_Comm_Revis` and `L_Profil_Bkwtr_El` head the
requirement column `R/A/ OR/ A` and `R/A/O`. In the Domain Tables reference,
`D_SFHA_FLDWY` and `D_Time_Units` have irregular rows, and `D_Zone_Subtype`'s
rotated "Footnote" header extracts reversed. None of these is in this slice.

## What the service holds that the reference does not allow

`scripts/report-observed` prints these from `service/observed/28.json`; the
counts below are its output for the snapshot pinned in `MANIFEST.json`. The
models reject every one except the eight it marks `legacy`, which
`legacy.json` admits with a warning by a count threshold, not by a judgement
about each value. `scripts/count-broken-rules` counts, from the same snapshot,
the rows that break each rule, every rule run on every row on its own;
validation cannot, since it names only the first rule a feature breaks. Every
per-rule figure below is also its output.

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
  `D_Zone_Subtype` and legacy value, 6). Running every constraint on its own
  finds each of the 6 breaking its only-in-AR rule and no other (2026-10-06),
  and each of the 73 breaking that rule and the `DUAL_ZONE` rule below
  (2026-10-07). Validating them cannot show that: validation stops at the
  first rule that fails, so a feature breaking two reports one, and since the
  `DUAL_ZONE` rule the 73 report that one.
- **The `DUAL_ZONE` rules reject the same 73 rows**, for leaving it empty:
  each sets `AR_REVERT` to `A` (72) or `AE` (1), which requires `T`, and holds
  null (72) or `""` (1, DFIRM `48277C`); `DUAL_ZONE LIKE ' '` counts none of
  them. All 73 are in Texas (DFIRMs `48485C`, 64; `48303C`, 7; `48027C` and
  `48277C`, 1 each). No row sets `AR_REVERT` to `AH`, `AO` or `X`, and no row
  holds a flag the rules forbid. `T` is on 4 rows, all in DFIRM `51107C` and
  none an AR zone (two `AE`, two `X`); they validate. `U`, which neither
  sentence names, is on 72,929.
- **The revert BFE and depth rules reject 18,177 rows**, all off AR zones:
  `BFE_REVERT` is populated on 12,732 and `DEP_REVERT` on 17,914
  (`BFE_REVERT IS NOT NULL AND BFE_REVERT <> -9999`, and the same for
  `DEP_REVERT`; 18,177 with `OR`), on 2026-10-06, and the same from the
  snapshot (`count-broken-rules --rule bfe_revert --rule dep_revert`). None of
  them holds a zone in `AR_REVERT`: the 73 rows that do hold `-9999` in both.
  Most are stand-ins for "does not apply": `0` (9,830 and 11,679), which
  section 7.3 forbids for that, and `-8888` (2,850 and 2,906), its
  "intentionally not populated". Of the 52 other `BFE_REVERT` values, 17 are
  `9999`. Of the 3,329 other
  `DEP_REVERT` values, 3,311 are in DFIRM `31099C`, where each is the
  polygon's area in square feet: across 2,000 of them, `DEP_REVERT /
  SHAPE.STArea()` is 1.011e11 to 1.015e11, the square feet in a square degree
  at that latitude.

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
  of which 16,572 hold a `D_V_Datum` value and reach the rule (one of them an
  `ASVD02` or `GUVD03`, which the coastal transects' counts admit to the
  domain: `V_DATUM IN ('ASVD02', 'GUVD03') AND (STATIC_BFE = -9999 OR
  STATIC_BFE IS NULL)` returns it), the rest failing the vocabulary first; `LEN_UNIT` set with neither BFE nor depth, 1,807
  (the same, with `(DEPTH = -9999 OR DEPTH IS NULL)` added), 1,468 of them a
  `D_Length_Units` value; a velocity without a `VEL_UNIT`, 8,638
  (`(VELOCITY <> -9999 AND VELOCITY IS NOT NULL) AND (VEL_UNIT IS NULL OR VEL_UNIT = '')`),
  1,257 of them a lone space the vocabulary rejects first, so 7,381 break the
  rule, as `count-broken-rules` finds. The same velocity
  predicate selects 9,679 rows, 7,708 of them `0`, which section 7.3 forbids
  as a stand-in for "does not apply"; 7,681 of the 8,638 without a unit are
  `0`, so most of those are nulls written as zero.
- **496 rows have no geometry** (`SHAPE IS NULL`, on 2026-10-08), in 26
  DFIRMs, 313 of them in `36025C`. The models reject them: a zone is a
  Polygon or MultiPolygon, and three fetched from `53067C` all failed on
  `geometry`. None of the counts above includes them, since each reads only
  attributes.

## What the BFE lines hold that the reference does not allow

Layer 16 has 1,506,074 rows (`service/observed/16.json`), and no value outside
the reference clears the legacy bar of 1,507, so `legacy.json` lists none for
it and every one is rejected. The model has no rules beyond its fields' types
and vocabularies; `count-broken-rules` reports none. Its rejections, 16,790 rows
(1.1%) by direct query on 2026-10-07, are these:

- **`V_DATUM`: 509 rows outside `D_V_Datum`**, from `report-observed`:
  `ASVD02` (284, American Samoa) and `GUVD03` (223, Guam), the same two the
  zones hold, and `NAVD29` once, in DFIRM `01071C`, whose other lines say
  `NGVD29`. One row has none (`V_DATUM IS NULL`, DFIRM `54013C`, with an `ELEV`
  of 0).
- **`SOURCE_CIT`, required, is null on 16,273 rows** (`SOURCE_CIT IS NULL`; no
  row holds `''` or a lone space), in 21 DFIRMs, 15,578 of them in two North
  Carolina counties (`37021C`, 10,325; `37067C`, 5,253). Flood Hazard Zones has
  the same gap on 12,589 rows (`SOURCE_CIT IS NULL OR SOURCE_CIT = ''` on layer
  28), which its model also rejects.
- **`BFE_LN_ID`, the key, is empty on 9 rows** (`BFE_LN_ID IS NULL OR BFE_LN_ID
  = ''`), 8 of them `''`. The one null also lacks `ELEV` and `SOURCE_CIT`
  (DFIRM `51163C`, `V_DATUM` `NP`); it is the only row without an `ELEV`
  (`ELEV IS NULL OR ELEV = -9999`).

The union is `V_DATUM IS NULL OR V_DATUM IN ('ASVD02','GUVD03','NAVD29') OR
SOURCE_CIT IS NULL OR BFE_LN_ID IS NULL OR BFE_LN_ID = '' OR ELEV IS NULL OR
ELEV = -9999`.

`ELEV` is "the rounded, whole-foot elevation", and the models do not hold it to
that: the section's introduction allows tenths of a foot for ponding and
lacustrine areas, and 3,587 lines are in `Meters`. 23,628 rows hold a fraction
(`ELEV <> ROUND(ELEV,0)`). 3,021 are negative (`ELEV < 0`) and 127 are `0`;
nothing in the reference bounds an elevation, and a `0` may stand in for "does
not apply" as it does in the zones' revert fields, which section 7.3 forbids.

## What the cross sections hold that the reference does not allow

Layer 14 has 952,002 rows (`service/observed/14.json`). No value outside the
reference clears the legacy bar of 953, so `legacy.json` lists none for it. Its
rejections, 98,766 rows (10.4%) by direct query on 2026-10-08, are these; a
"missing" text field is `F IS NULL OR (F = '' AND F NOT LIKE ' ')`, since a
lone space in free text is a value, and a missing number `F IS NULL OR F =
-9999`:

- **`STRMBED_EL`, required, is missing on 76,365 rows.** Another 575,580, 60%
  of the layer, hold `-8888` (`STRMBED_EL = -8888`), "intentionally not
  populated" (section 7.3), and validate as an elevation. `WSEL_REG`'s
  description says to code a coastal or confluence section `-8888` (3,400
  rows); `STRMBED_EL`'s says nothing of it.
- **Required text missing**: `SOURCE_CIT` 5,114 (none `''`), `WTR_NM` 2,179,
  `MODEL_ID` 1,090, `LEN_UNIT` 13, and `XS_LN_ID` and `VERSION_ID` 9 each. A
  required number: `WSEL_REG` 101.
- **The letter rule rejects 14,801 rows**, from `count-broken-rules`: a
  `NOT LETTERED, MAPPED` section with an `XS_LTR`. 2,914 hold a letter or
  number (`XS_LTR <> ''`), and 11,887 a lone space (`XS_LTR LIKE ' '`), which
  the model reads as a value. 207 lettered sections have no `XS_LTR`; the model
  does not require one. No row is `NOT LETTERED, NOT MAPPED`.
- **`V_DATUM`: 281 rows outside `D_V_Datum`**, from `report-observed`:
  `ASVD02` (127) and `GUVD03` (73), as in the zones and BFEs, and `NGVD88`
  (81, all in DFIRM `01071C`, whose BFE lines hold the one `NAVD29`).
  `LEN_UNIT` has one lone space.

The union joins every clause above with `OR`, the rule's as `(XS_LN_TYP <>
'LETTERED, MAPPED' AND XS_LTR IS NOT NULL AND (XS_LTR <> '' OR XS_LTR LIKE
' '))` and the datums' as `V_DATUM IN ('ASVD02', 'NGVD88', 'GUVD03') OR
LEN_UNIT LIKE ' '`. On six pages of 2,000 live features, validating each
rejected exactly as many as the union selects over the same `OBJECTID` range:
253, 484, 391, 0, 0 and 0.

`START_ID`, `STREAM_STN` and `XS_LN_TYP` are `R1`, optional (README.md): 16,669
sections have no `START_ID` and 404 no `STREAM_STN`, and they validate. Read as
required, they added 14,374 rows to the union, 113,140 (11.9%).

`LEN_UNIT` is `Miles` on 1,778 sections in 36 DFIRMs (`LEN_UNIT = 'Miles'`).
`D_Length_Units` lists it, so they validate, but their `WSEL_REG` runs from
66.2 to 1,494.7, elevations in feet. The reference gives `STREAM_STN` no unit.

## What the profile baselines hold that the reference does not allow

Layer 17 has 338,155 rows (`service/observed/17.json`), so its legacy bar is
339. Six values outside the reference clear it: five of the zones' legacy study
types (`SFHAs WITH HIGH FLOOD RISK` 63,162, `... LOW ...` 29,764, `... MEDIUM
...` 14,591, `REDELINEATION` 2,183, `DIGITAL CONVERSION` 1,385), and
`WATER_TYP` `Stream / River` (426), the [November 2016 Domain Tables
reference](https://www.fema.gov/sites/default/files/nepa/Domain_Tables_Technical_Reference_Nov_2016_SUPERSEDED.pdf)'s
FRD-only cartographic code 4600 (`D_Carto_Hydro_Code`), which the 2019 and 2024
editions list in no domain. The layers share one `StudyTyp` enum, so the
zones' ASCII-apostrophe study type also validates, with a warning, on the 2
baselines that hold it, far below this layer's bar.

Its rejections, 7,677 rows (2.3%) by direct query on 2026-10-08, are these;
"missing" is as for the cross sections:

- **`SHOWN_FIRM` holds `Y` (174, all in DFIRM `51051C`), `N` (5) or a lone
  space (7)**, 186 rows, none of them in `D_TrueFalse`. `U` is on 109,221 and
  validates, since `D_TrueFalse` lists it.
- **Required text missing**: `WTR_NM` 2,020, `SOURCE_CIT` 326 (none `''`),
  `BASELN_ID` 11 (one null, in DFIRM `48485C`).
- **`WATER_TYP` outside `D_Prof_Basln_Typ`**, from `report-observed`:
  `Stream Centerline` (178), `1032` (142), `Creek` (66), `NP` (64), the 2016
  cartographic codes `Lake / Pond` (11) and `Canal / Ditch` (2), and six more
  of 10 rows or fewer, 486 rows.
- **`STUDY_TYP`**: 32 lone spaces, and `New H&H` (3), `1050` (2) and `Profile
  Baseline` (1), 38 rows.
- **`DATUM_UNIT` holds a lone space on 4,352 rows** (`DATUM_UNIT LIKE ' '`),
  which `D_Length_Units` does not list. `report-observed` prints 191,723 `' '`:
  the snapshot's grouping folded 187,371 empty strings into the lone spaces'
  group, the opposite of the way `STUDY_TYP`'s blanks fell on layer 28.
- **The continuation rules reject 375 rows**, from `count-broken-rules`:
  `FLD_PROB2` without `FLD_PROB1` (218), `FLD_PROB3` without `FLD_PROB2` (15),
  and `SPEC_CONS2` without `SPEC_CONS1` (142). Each continuation is "used when"
  the field before it "does not have enough characters", read as a limit, as
  `XS_LTR`'s "populated when" was. No row breaks two.
- **69 rows have no geometry** (`SHAPE IS NULL`), in 27 DFIRMs, 20 of them in
  `12053C`.

The union joins every clause above with `OR`, the vocabularies' as the values
`report-observed` prints and the rules' as `(F2 IS NOT NULL AND (F2 <> '' OR F2
LIKE ' ')) AND (F1 IS NULL OR (F1 = '' AND F1 NOT LIKE ' '))`. Validating live
features agrees with it: on six pages of 250 spread across the layer by
`resultOffset`, the model rejected 0, 0, 1, 0, 0 and 0, the one a feature with
no geometry; 400 rows the union selects were all rejected; and 400 rows only a
missing `R1` field selects all validated. None of 7,500 features validated on
2026-10-07 was a MultiLineString.

`START_ID`, `SHOWN_FIRM`, `WATER_TYP`, `STUDY_TYP`, `R_ST_DESC` and
`R_END_DESC` are `R1`, optional (README.md), and decide most of what the layer
would otherwise reject. `START_ID` is missing on 106,642 rows, 31.5% of the
layer, in 707 DFIRMs, 29,438 of them in `12053C`; 23,554 are `Hydraulic Link`s,
40% of the layer's 58,693. `SHOWN_FIRM` is missing on 23,153 (22,968 null, 185
`''`), `R_END_DESC` on 362, `R_ST_DESC` on 358 (no row with a null `R_ST_DESC`
has an `R_END_DESC`), `STUDY_TYP` on 147 and `WATER_TYP` on 47 (40 null, 7
`''`). Read as required, they made the union 113,325 rows (33.5%).

`V_DATM_OFF`, the datum offset, is `Text` of length 6, so the model checks its
length and nothing else: it holds `-9999` (2,172) and `<Null>` (147) written
as text, a datum name (`NAVD88`, 428) or a unit (`Feet`, 184) as often as a
number, and a lone space on 6,105 rows, and all of them validate. `DATUM_UNIT`
is set on 8,413 rows without an offset, and 113 offsets have no unit; no
sentence ties the two beyond "the unit of measure for the vertical datum
offset", so neither is rejected. `SHOWN_INDX` is in the reference and not on
the service.

## What the station starts hold that the reference does not allow

Layer 13 has 93,357 rows (`service/observed/13.json`), so its legacy bar is
94. One value outside the reference clears it: `LOC_ACC` `NP` (284, in five
DFIRMs, 154 of them in `19169C`), section 7.3's text value for "intentionally
not populated". `D_Loc_Accuracy` lists only `High`, `Medium` and `Low`, and so
did the 2016 and 2019 editions. The field description writes them `“HIGH”`,
`“MEDIUM”` and `“LOW”`; the domain and the data write `High`.

Its rejections, 9,276 rows (9.9%) by direct query on 2026-10-08, are these;
"missing" is as for the cross sections:

- **`SOURCE_CIT`, required, is missing on 8,427 rows** (8,363 null, 64 `''`),
  in 934 DFIRMs, none with more than 218 (`29163C`). 65 hold a lone space,
  which is a value and validates.
- **`START_DESC`, required, is null on 770 rows**, in 37 DFIRMs, 473 of them in
  `29139C`, `29219C` and `48471C`. No row holds `''`. 2,396 hold `NP`
  (`START_DESC = 'NP'`), and validate.
- **`START_ID`, the key, is missing on 198 rows** (124 null, 74 `''`), 123 of
  them in `48471C` and 73 in `45045C`. Every one also lacks `START_DESC` or
  `SOURCE_CIT`, so the fixture has no case for it.
- **82 points are empty** (`SHAPE.STX IS NULL`), in 21 DFIRMs. ArcGIS writes
  each as `{"type": "Point", "coordinates": []}`, and the model rejects it.
  `SHAPE IS NULL` counts none of them, so a union built on it, as the line
  layers' were, misses them: the first page validated rejected 155 where that
  union selected 147.
- **`LOC_ACC` is null on 3 rows** (two in `40073C`, one in `01129C`).

The union joins every clause above with `OR`. On fourteen pages of 2,000
`OBJECTID`s, six of them chosen for the rare clauses (`LOC_ACC` null, a missing
`START_ID`, an empty point, `NP`), the model rejected exactly as many as the
union selects over the same range, 1,735 of 9,792 features in all. The model
has no rules, so `count-broken-rules` reports none.

`START_ID` is required here and `R1`, optional, where it is a foreign key, in
`S_XS` and `S_Profil_Basln`. Where it is set it joins: in four DFIRMs
(`01003C`, `29163C`, `06037C`, `12086C`, the last with no station starts or
sections), 3,373 of 3,458 cross sections name a station start the layer holds.
The 108 baselines of `01003C` hold `NP`. The models do not check the join.
`START_ID` is 32 long on the service and 25 in the reference, and `SOURCE_CIT`
21 and 11; the models take the service's.

## What the river marks hold that the reference does not allow

Layer 7 has 13,097 rows (`service/observed/7.json`, 2026-10-10). No field has
a domain, so `report-observed` prints nothing for it and `legacy.json` lists
nothing. Its rejections, 227 rows (1.7%) by direct query on 2026-10-10, are
these; "missing" is as for the cross sections:

- **`START_ID`, the foreign key, is missing on 227 rows** (224 null, 3 `''`),
  in nine DFIRMs, 184 of them in `28149C`, `13113C` and `28001C`.
- **`RIV_MRK_ID`, the key, is missing on 3** (all `''`, DFIRM `28029C`), and
  **`RIV_MRK_NO` and `SOURCE_CIT` on 1** (DFIRM `12117C`). Each of the four
  also lacks `START_ID`, so the fixture has no case for them.

No point is empty (`SHAPE.STX IS NULL` and `SHAPE IS NULL` both count 0), no
text field holds `-9999`, `<Null>` or a lone space, and every feature is a
Point. The union is the `OR` of the four fields' missing clauses and
`SHAPE.STX IS NULL`. Validating the whole layer, in 19 pages of 2,000
`OBJECTID`s, rejected exactly as many as the union selects over each range,
227 in all: 223 for `START_ID` alone, 3 with `RIV_MRK_ID`, 1 with `RIV_MRK_NO`
and `SOURCE_CIT`. None raised a legacy-value warning. The model has no rules.

Section 7.3's `NP` is in `START_ID` on 1,593 rows, `RIV_MRK_NO` on 369 and
`SOURCE_CIT` on 176, and validates: the fields are free text. No row holds
`NP` in `RIV_MRK_NO` or `SOURCE_CIT` without it in `START_ID`. `RIV_MRK_NO`
"usually represents the distance", with no unit, and is `Text`, so the model
reads it as text.

`START_ID` is required here, as in `S_Stn_Start`, and joins where it is set:
in the six DFIRMs with the most river marks, 1,759 of 2,771 name a station
start the layer holds and 737 hold `NP`. The other 275 are DFIRM `155166`,
where every mark names `155166_1035` and the station starts run `155166_1`
upward without it. The models do not check the join. `RIV_MRK_ID` and
`START_ID` are 32 long on the service and 25 in the reference, and
`SOURCE_CIT` 21 and 11; the models take the service's.

## What the water lines hold that the reference does not allow

Layer 20 has 6,171,300 rows (`service/observed/20.json`, 2026-10-10). Its
rejections, 131,004 rows (2.1%) by direct query on 2026-10-10, are these;
"missing" is as for the cross sections:

- **`WTR_NM` is missing on 51,624** (41,074 null, 10,550 `''`), in 75 DFIRMs,
  15,248 of them in `37175C`. A lone space is text and validates (2,211 rows),
  as does `NP`, which 2,817,055 rows hold.
- **`SOURCE_CIT` is missing on 30,262** (all null), in 89 DFIRMs, 19,359 of
  them in `37021C`.
- **`SHOWN_FIRM` holds a lone space on 47,976 rows and `SHOWN_INDX` on 47,925**
  (46,829 hold it in both), 49,072 rows in 39 DFIRMs, 7,018 of them in
  `53077C`. A lone space is no value of `D_TrueFalse`. Nothing else is outside
  it: the rest of both fields is `T`, `F`, `U`, null or `''`, and `U` validates.
- **`WTR_LN_ID`, the key, is missing on 27** (26 null, 1 `''`).
- **21 rows have no geometry** (`SHAPE IS NULL`), in nine DFIRMs, 9 of them in
  `36067C`.

`DFIRM_ID` and `VERSION_ID` are missing on none. The model has no rules, so
`count-broken-rules` reports none. The union joins every clause above
with `OR`, each text field's as its missing clause (`F IS NULL OR (F = '' AND F
NOT LIKE ' ')`), the flags' as `SHOWN_FIRM LIKE ' ' OR SHOWN_INDX LIKE ' '`, and
`SHAPE IS NULL`. The layer is too large to validate whole (6.2 million rows, its
`OBJECTID`s running to 28,306,080), so ten pages of 2,000 features were
validated, each the first 2,000 rows with `OBJECTID >= n`, for `n` of 1 and 3,000,000
to 27,000,000 in steps of 3,000,000. On each, the model rejected exactly as many
as the union selects over the page's `OBJECTID` range: 0, 1,479, 0, 47, 820, 0,
0, 0, 0 and 0. No feature on them was rejected for a MultiLineString. The control does not reach an empty line that has a
geometry object: no query for it finished in 120 seconds (`SHAPE.STLength() IS
NULL` over the layer), so only a unit test holds the model to the `SHAPE IS
NULL` rows.

`SHOWN_FIRM` and `SHOWN_INDX` are `A`, required if applicable, and validate when
null or `''`. `WTR_NM` joins the cross sections, base flood elevations and
profile baselines by name, as `WTR_NM`, not by key; the models do not check it.
`WTR_LN_ID` and `SOURCE_CIT` are 32 and 21 long on the service and 25 and 11 in
the reference; the models take the service's.

## What the levees hold that the reference does not allow

Layer 23 has 16,320 rows (`service/observed/23.json`, 2026-10-10), few enough to
validate whole: every row was paged by `OBJECTID` (1,000 to a page, with
geometry) and run through the model. It rejects 13,626 (83.5%). One field
accounts for nearly all of them; "missing" is as for the cross sections:

- **`FC_SEG_ID` is missing on 13,405** (3,494 null, 9,911 `''`), in 606 DFIRMs,
  714 of them in `06095C`. It is `R`, "Required for all records", and 2,504
  levees hold one, 1,140 of those `NP`. Its description says "If the levee,
  floodwall or closure structure is included in the NLD, this is the segment
  identification number", a condition no field records; the model takes the
  table's flag. 13,234 of the rejected levees are rejected for this field alone.
- **`DISTRICT` is outside `D_USACE_District` on 184**: a lone space on 182, the
  code `1027` on 1 and `KANSAS CITY` in capitals on 1. The domain lists names.
- **`FC_SYS_ID` is missing on 110** (85 null, 25 `''`); it is `R` too, and 13,771
  levees hold `NP`.
- **`LEV_AN_TYP` is outside `D_Levee_Analysis_Type` on 33**: a lone space on 14,
  `Not Hydraulically Signific*` on 6 (the name cut at 27 characters, the
  service's length), `NV` on 5, `NHS`, `OTH`, `SR` and `<Null>` on 2 each.
- **`LEV_AN_TYP` is populated on a levee that is not `Non-Accredited` on 44**
  (by the census; validation names the rule on 43, as the 44th also breaks the
  district rule, which it reports first): `Other` on 22, `Natural Valley` on 14,
  `Sound Reach` on 7 and `Overtopping` on 1, among them 31 `Accredited`, 9
  `Never Accredited` and 4 with a blank status.
- **`DISTRICT` is missing on a USACE levee on 151** (`USACE_LEV` is `T`; 763
  levees are).
- **`LEVEE_STAT` is outside the status domain on 25**: a lone space on 18, `A` on
  3, `N` on 2 and `NON-ACCREDITED` in capitals on 2.
- **`USACE_LEV` is outside `D_TrueFalse` on 5** (`N` 4, a lone space 1),
  **`PL84_99TF` on 2** (`N`, a lone space), **`LEN_UNIT` on 3** (a lone space),
  **`SOURCE_CIT` is missing on 3** (null), and **`LEVEE_TYP` holds
  `LEVEE CENTERLINE` on 1**.

`DFIRM_ID`, `VERSION_ID` and `LEVEE_ID` are missing on none, and none lacks a
geometry or holds a MultiLineString: all 16,320 are LineStrings.

**The service's own query finds four fewer.** `KANSAS CITY`, `LEVEE CENTERLINE`
and `NON-ACCREDITED` twice (DFIRMs `20079C`, `38055C`, `18127C`) differ from a
listed value only in case, which the service's `IN` and `=` ignore, so no
`where` selects them by value. The union query selects 13,622 rows and the model
rejects 13,626; compared by `OBJECTID`, they differ on those four and no others.
The union joins with `OR` each required field's missing clause (`F IS NULL OR
(F = '' AND F NOT LIKE ' ')`), each coded field's
(`F IS NOT NULL AND (F <> '' OR F LIKE ' ') AND NOT (F IN (<the values>) AND F
NOT LIKE ' ')`), the analysis rule's (`LEV_AN_TYP IS NOT NULL AND LEV_AN_TYP <> ''
AND LEV_AN_TYP <> 'NP' AND (LEVEE_STAT IS NULL OR LEVEE_STAT = '' OR LEVEE_STAT <>
'Non-Accredited')`) and the district rule's (`USACE_LEV = 'T' AND <DISTRICT is
missing>`). The analysis rule's query selects 50, six more than the census,
because six of those levees hold a coded status or analysis type that the
vocabulary rejects first.

**`NP` is not populated, for `LEV_AN_TYP`.** "This should only be populated if
LEVEE_STAT is Non-Accredited" would reject every levee holding `NP` there: 8,821
of the 9,443 that do, 7,724 of them with `NP` in `LEVEE_STAT` as well. Section 7.3
says `NP` is "a value that indicates that the affected field was intentionally
not populated", so the rule's `unless` in `relationships.json` quotes that
sentence and exempts it. Every other value is limited to `Non-Accredited`, as
the rule says. Deleting the `unless` entry reverses it.

**`De-Accredited` and `Never Accredited` are legacy values of `LEVEE_STAT`**, on
991 and 912 levees, both over the one-in-a-thousand threshold. `D_Levee_Status`
lists `A`, `N`, `P`, `AR`, `A99` and `NP`; what the data holds for the first two
is the accreditation status in words.

**A date is milliseconds since the Unix epoch.** `CONST_DATE` and `PAL_DATE` are
the first `Date` fields modelled, as `int64`. The service writes `253392451200000`
for the reference's null date, 9/9/9999 (14,338 levees in `CONST_DATE`, 15,821
in `PAL_DATE`) and `218330035200000` for the non-populated date, 8/8/8888 (159
and 110). The models read the first as not populated, as `-9999`, and keep the
second as a value, as `-8888`. The state geodatabase and county shapefiles
store a date as a date, not as milliseconds, and no download was converted for
this layer, so the model has not met one. `PAL_DATE` is "populated for those
structure features that have a PAL designation", but of the 274 levees holding
a date in it, 66 are `Provisionally Accredited` and 99 are `Accredited`; no rule
reads it.

**`FREEBOARD` is in `LEN_UNIT`**, "the measurement system used for the freeboard
elevations", declared `UnitIn("LEN_UNIT")`. Of 694 levees holding a freeboard
(1,363 hold `-8888`), 536 hold `Feet`, 127 `NP` and 25 none; the model does not
require a unit. `LEVEE_ID`, `FC_SYS_ID` and `SOURCE_CIT` are 32, 32 and 21 long
on the service and 25, 25 and 11 in the reference, and `LEV_AN_TYP` 27 and 29;
the models take the service's. Levees name their stream by `WTR_NM`, as the
cross sections, BFE lines, profile baselines and water lines do; the models do
not check the join, and `S_Levee` has no foreign key to a modelled layer.

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
validation, not because any statistic showed it. `count-broken-rules` inherits
the case folding, judging a `FEET` as the `Feet` it is grouped with, but not
the blank folding: the snapshot splits the rows by `LIKE ' '` on each field
before grouping them, so a lone space and `""` are judged apart.

## What the LOMRs hold that the reference does not allow

Layer 1 has 10,150 rows (`service/observed/1.json`, 2026-10-10), few enough to
validate whole: every row was paged by `OBJECTID` (1,000 to a page, with
geometry) and run through the model. It rejects 69 (0.7%); "missing" is as for
the cross sections. No row breaks two clauses.

- **42 have a geometry the reference does not allow.** 37 have none
  (`SHAPE IS NULL`), each in a different DFIRM; one is empty (`SHAPE.STArea() =
  0`, `coordinates: []`); four are MultiPolygons of two or three parts, in
  `49019C`, `25021C`, `39049C` and `48439C`. "Multipart polygons are not
  allowed", so the model takes a Polygon where the flood zones take a
  MultiPolygon.
- **`SOURCE_CIT` is missing on 20** (all null), in 11 DFIRMs, 5 of them in
  `37179C`.
- **`SCALE` is outside `D_Scale` on 5**: `1000` on 3, in `26111C`, `17201C` and
  `08005C`, and null on 2, in `55059C`. `1000` is the domain's coded value for
  `6000`, not a denominator the domain lists.
- **`STATUS` holds `Superceded` on 1** (`18089C_14`), a misspelling of the
  domain's `Superseded`, which 209 rows hold.
- **`LOMR_ID`, the key, is `''` on 1** (`42005C`).

`DFIRM_ID`, `VERSION_ID`, `CASE_NO`, `EFF_DATE` and `STATUS` are missing on none.
`STATUS` holds `NP` on 1 row, which validates. The model has no rules, so
`count-broken-rules` reports none, and nothing is common enough to be legacy:
the threshold is one row in a thousand (11 here) and the most frequent value
outside the reference is `1000`, on 3.

**The union query selects 65; the model rejects 69.** The four others are the
MultiPolygons, which no `where` selects: `STNumGeometries()` and
`STGeometryType()` are a 400 on this service. Compared by `OBJECTID`, the union's
65 are a subset of the model's 69 and the difference is those four rows. The
union joins with `OR` each required field's missing clause (`F IS NULL OR (F =
'' AND F NOT LIKE ' ')`), `SCALE`'s and `STATUS`'s outside clause (`F IS NOT
NULL AND (F <> '' OR F LIKE ' ') AND NOT (F IN (<the values>) AND F NOT LIKE '
')`), and `SHAPE.STArea() IS NULL OR SHAPE.STArea() = 0`, since `SHAPE IS NULL`
misses the empty polygon. `EFF_DATE` is `R`, a date: no row lacks one, and none
holds 9/9/9999 or 8/8/8888.

**The reference's two descriptions of the table disagree.** The table summary
(Table 1) calls S_LOMR "LOMRs not yet incorporated on the FIRM"; the section
says the layer "includes all LOMRs that have been incorporated into the NFHL
database", and 9,877 rows hold `Effective` and 60 `Incorporated`. The model's
description takes the section's.

`LOMR_ID` and `SOURCE_CIT` are 32 and 21 long on the service and 25 and 11 in the
reference; the models take the service's. In the paged rows the longest value
of either is 16 and 19 characters, and 10,114 `SOURCE_CIT` values are longer
than the reference's 11 (`LEN()` is a 400 on this service).
`SOURCE_CIT` "must match a value in `L_Source_Cit`" and `LOMR_ID` joins nothing
modelled; the models check neither. `SCALE` is a number written as text, so
`D_Scale`'s `6000` is the string `"6000"`. The LOMRs share no field with the
other eight layers.

## What the flood hazard boundaries hold that the reference does not allow

Layer 27 has 15,233,741 rows (`service/observed/27.json`, 2026-10-10). Its
rejections, 1,448,350 rows (9.5%) by one union query on 2026-10-10, are these;
"missing" is as for the cross sections:

- **`SOURCE_CIT` is missing on 1,448,053**, in 330 DFIRMs, 52,877 of them in
  `34011C`, 48,315 in `12021C` and 43,607 in `37119C`. A lone space is text and
  validates (7,234 rows), as does `NP`, which 1,782,479 rows hold. The rows
  with it missing run together in `OBJECTID`: 8 of 50 sampled pages of 200
  consecutive rows held 182 to 200 of them and the other 42 held none.
- **`SHAPE` is null on 195**, in 15 DFIRMs, 124 of them in `19043C` and 28 in
  `21157C`. Two of them also lack `SOURCE_CIT`.
- **`VERSION_ID` is missing on 77**, 76 of them in `48201C`.
- **`LN_TYP` holds `NP` on 21**, 19 of them in `47053C`. `NP` is no value of
  `D_Ln_Typ`, and 21 rows is 1 in 725,000, so it is not common enough to be
  legacy. The service holds three of the domain's four values: `SFHA / Flood
  Zone Boundary` on 15,036,379, `Limit Lines` on 192,146 and `Flowage Easement
  Boundary` on 5,195; `Other Boundary` on none.
- **`FLD_LN_ID`, the key, is missing on 6**, in 3 DFIRMs. A lone space is text
  and validates (962 rows).

`DFIRM_ID` and `LN_TYP` are missing on none. The model has no rules, so
`count-broken-rules` reports none. The union joins every clause above with
`OR`, each text field's as its missing clause (`F IS NULL OR (F = '' AND F NOT
LIKE ' ')`), `LN_TYP`'s as `LN_TYP NOT IN (<the four values>)`, and `SHAPE IS
NULL`. The five counts sum to 1,448,352 and the union selects 1,448,350: the
two rows in both `SOURCE_CIT` and `SHAPE`.

The layer is too large to validate whole (`OBJECTID`s run to 70,201,356) and
its lines are large: the first 250 rows by `OBJECTID` are 26 MB of GeoJSON, and
a page of 2,000 is a 500. The control is 50 pages of 200 features, each the
first 200 rows with `OBJECTID >= n`, for `n` of 1 and 1,400,000 to 68,600,000 in
steps of 1,400,000 (10,000 rows). On each, the model rejected exactly as many
rows as the union selects over the page's `OBJECTID` range: 1,579 in all,
every one for `SOURCE_CIT`, on 8 pages. The rarer clauses are checked by
fetching every row they select (`VERSION_ID` 77, `FLD_LN_ID` 6, `LN_TYP` `NP`
21, `SHAPE IS NULL` 195) and validating it: each is rejected for its own field,
and the two rows without `SOURCE_CIT` for both. All 10,000 sampled geometries
are LineStrings and none is empty, so the sample holds no MultiLineString and
no empty line. No `where` selects a multipart line, and no query for an empty one was
tried, so the control does not reach either; only a unit test holds the model
to the multipart case. A wrong-case `LN_TYP`
is out of reach for the same reason as in the levees: the service folds case in
`=`, `IN` and grouping, and `COLLATE` is a 400.

`FLD_LN_ID` and `SOURCE_CIT` are 32 and 21 long on the service and 25 and 11 in
the reference; the models take the service's. `SOURCE_CIT` "must match a value
in `L_Source_Cit`", which the models do not check. The boundaries join the flood
hazard zones by `DFIRM_ID`, `VERSION_ID` and `SOURCE_CIT`, and geometrically:
Table 4 requires each line to be "Covered by Boundary Of" `S_Fld_Haz_Ar`.
Nothing in the layer names a zone.

## What the political jurisdictions hold that the reference does not allow

Layer 22 has 88,344 rows (`service/observed/22.json`, 2026-10-12 UTC), few
enough to validate whole: every row was paged by `OBJECTID` (200 to a page, 50
where a page of large polygons failed, with geometry) and run through the model.
It rejects 18,184 (20.6%); "missing" is as for the cross sections.

- **`SOURCE_CIT` is missing on 13,247** (13,220 null, 27 `''`), in 232 DFIRMs,
  904 of them in `45019C`. A lone space is text and validates (333 rows), as does
  `NP`, which 18,474 rows hold.
- **The `ANI_FIRM` rule rejects 4,597**, every one with `ANI_TF` `F`, in 189
  DFIRMs, 393 of them in `53077C`: a lone space (2,004), the flags `F` (1,654)
  and `U` (530), `0` (169), `<Null>` (8), and 232 DFIRM IDs, 222 of them
  `20173C`. `count-broken-rules` finds the same 4,597; validation names the rule
  on 4,557, since 40 of them also lack `SOURCE_CIT`, which fails first.
- **292 have no geometry** (`SHAPE IS NULL`), 291 in `48187C`. No polygon is
  empty: `SHAPE IS NOT NULL AND SHAPE.STLength() = 0` counts none.
  `SHAPE.STArea() = 0` selects one row, `OBJECTID` 2923, a three-vertex sliver
  whose area the service rounds to 0; it validates.
- **`VERSION_ID` is missing on 159**, 158 in `45063C`. Every one also lacks
  `SOURCE_CIT`, so the fixture has no case for it.
- **`ST_FIPS` is missing on 60**, 59 in `06107C`.
- **`ANI_TF` is missing on 31**, 30 in `42073C`.
- **One row holds nothing** but its `GlobalID` (`OBJECTID` 122639): every
  attribute null and no shape. It accounts for the single row missing
  `DFIRM_ID`, `POL_AR_ID`, `POL_NAME1`, `CO_FIPS`, `COMM_NO` and `CID`.

The union joins with `OR` each required field's missing clause (`F IS NULL OR
(F = '' AND F NOT LIKE ' ')`), `ST_FIPS`'s and `ANI_TF`'s outside clause (`F IS
NOT NULL AND (F <> '' OR F LIKE ' ') AND NOT (F IN (<the values>) AND F NOT LIKE
' ')`, the legacy codes among `ST_FIPS`'s values), the rule's (`ANI_FIRM IS NOT
NULL AND (ANI_FIRM <> '' OR ANI_FIRM LIKE ' ') AND ANI_FIRM <> 'NP' AND (ANI_TF
IS NULL OR ANI_TF <> 'T' OR ANI_TF LIKE ' ')`) and `SHAPE IS NULL`. It selects
18,184 rows on 2026-10-11; on each of the 446 pages the model rejected exactly as
many as the union selects over the page's `OBJECTID` range, and compared by
`OBJECTID` the two sets are the same. `SHAPE.STArea() = 0` in place of `SHAPE IS
NULL` would have added the sliver.

**`ST_FIPS` drops the leading zero on five states, and all five are legacy.**
`5` (352 rows, 18 DFIRMs), `1` (282, 20), `6` (116, 4) and `8` (90, 4) clear the
bar of 89 rows; each is in DFIRMs whose ID begins with the padded code (`05...`,
`01...`, `06...`, `08...`). `4` (17 rows, all `04009C`) does not, and validates
with the others by Seth Fitzsimmons's decision of 2026-10-11, recorded in its
`legacy.json` entry: it is the same defect, and the DFIRM says which state it
means. Without it the layer rejects 18,201. `D_State_FIPS`'s FIRM description is the two-digit code, so
`01`, not `Alabama`, is what the field stores.

**`ANI_FIRM` names another FIRM only on an Area Not Included.** "Used for ANI
polygons where ANI_TF equals “T”" is read as a limit, as `XS_LTR`'s "populated
when" was. The description itself says to populate `NP` "if the area has never
been converted to a FIRM Database", which is an ANI case, but `NP` is section
7.3's "intentionally not populated", so the rule's `unless` exempts it as it
does for the levees' `LEV_AN_TYP`: the 80 rows holding `NP` off an ANI area
validate. A lone space is a value and breaks the rule; `""` is a null. Deleting
the `S_Pol_Ar` entry from `relationships.json` reverses it, and would leave the
layer's rejections at 13,644. The model does not check that `ANI_FIRM` is a
DFIRM ID: on ANI areas, 40 values are neither `NP` nor of either form the
description gives (`ANI_FIRM NOT LIKE '_____C' AND ANI_FIRM NOT LIKE
'[0-9][0-9][0-9][0-9][0-9][0-9]'`).

**Two sentences the model does not enforce.** `COM_NFO_ID` "is populated for any
jurisdiction that has a CID number issued by FEMA", and a jurisdiction without
one writes `FED`, `ST` or `OTHR` in `COMM_NO` (10,037 rows). 1,311 rows with a
FEMA number lack it (`<COM_NFO_ID missing> AND COMM_NO NOT IN
('FED','ST','OTHR')`); reading that pair of sentences as a `require_if` would
reject them. `CID` "is created by combining the State FIPS code with the
COMM_NO"; the service rejects string concatenation in a `where` (a 400), so
how many rows disagree is not counted, and the model does not check it.

`POL_AR_ID`, `COM_NFO_ID` and `SOURCE_CIT` are 32, 32 and 21 long on the service
and 25, 25 and 11 in the reference; the models take the service's. 935 areas
are MultiPolygons, which the reference allows. `COM_NFO_ID` is a foreign key to
`L_Comm_Info`, which is not modelled. The political areas share `DFIRM_ID`,
`VERSION_ID` and `SOURCE_CIT` with the flood zones and join them geometrically:
Table 4 requires `S_Fld_Haz_Ar`'s boundary to be "Covered by Feature Class Of"
`S_Pol_Ar`. The models check neither.

## What the FIRM panels hold that the reference does not allow

Layer 3 has 183,680 rows (`service/observed/3.json`, 2026-10-12 UTC), few enough
to validate whole: every row was paged by `OBJECTID` (2,000 to a page, with
geometry) and run through the model. The union below selects 7,462 (4.1%) and
the model rejects 7,761; the 299 more are wrong-case vocabulary, which no
`where` can select (below). "Missing" is as for the cross sections.

- **The `PNP_REASON` rule rejects 6,688**: a reason on a panel whose type is not
  one of the three `Not Printed` values. 6,307 are a lone space (116 DFIRMs, 214
  at most in one), which the model reads as a value, as it does for `ANI_FIRM`;
  381 are text, six of them `<Null>`. `count-broken-rules` finds the same 6,688.
  The description says "Only completed if the hardcopy panel is not printed by
  FEMA"; `Unmapped Community` is not a `Not Printed` type, so a reason on one
  breaks the rule (the layer has three, none with a reason).
- **`SOURCE_CIT` is missing on 543** (542 with a shape), in 8 DFIRMs, 215 of them
  in `37021C`.
- **`PANEL_TYP` is outside `D_Panel_Typ` on 165** by the service's collation:
  `Community B` (97, three DFIRMs, 74 in `150002`), `Countywide, Panel
  Printed'` with a stray quote (43, all `06057C`), `Countywide,` (16, ten
  DFIRMs), `''` (6, `06065C`), `Countywide, Panel Not Printed` (2, `06031C`)
  and one null. The truncated ones can be a printed or a not-printed type, so
  nothing maps them.
- **`SCALE` is outside `D_Scale` on 40**: `NP` (36, all `49019C`), `4800` (3,
  `500027`) and one null. `D_Scale` does not list `NP`; `D_Basemap_Typ` does, and
  `BASE_TYP` is `NP` on 113,744 rows.
- **`BASE_TYP` is missing on 1**, `ST_FIPS` on 1, and one row, `OBJECTID` 451726,
  holds nothing but its `GlobalID`: every attribute null and no shape. It is the
  single row missing `DFIRM_ID`, `VERSION_ID`, `FIRM_ID`, `PCOMM`, `PANEL`,
  `SUFFIX` and `FIRM_PAN`, and the one null in `ST_FIPS`, `BASE_TYP` and `SCALE`.
- **29 have no geometry** (`SHAPE IS NULL`), 24 in `06037C`. No polygon is empty,
  by validating every row: the shapes are 183,647 Polygons, 4 MultiPolygons and
  the 29 nulls. `SHAPE.STArea() = 0` selects one row, `OBJECTID` 13232, a sliver
  with a `PANEL_TYP` the vocabulary rejects, so the fixture has no case for it.
- **299 hold a vocabulary value in the wrong case**: `ORTHOPHOTO` for
  `Orthophoto` (211, in 4 DFIRMs, 84 in `55023C`), `COUNTYWIDE, PANEL PRINTED`
  (60) and `COUNTYWIDE, NOT PRINTED` (28), both `26109C`. The model rejects them;
  the service folds case in `=`, `IN` and grouping, so the union cannot, and
  `report-observed` counts `Orthophoto` as 60,336, the 211 included. 211 is
  above the legacy bar of 184, but a count the snapshot cannot see is not one
  `legacy.json` can be licensed by.

The union joins with `OR` each required field's missing clause (`F IS NULL OR
(F = '' AND F NOT LIKE ' ')`) for `DFIRM_ID`, `VERSION_ID`, `FIRM_ID`, `PCOMM`,
`PANEL`, `SUFFIX`, `FIRM_PAN` and `SOURCE_CIT`; the outside clause (`F IS NULL OR
NOT (F IN (<the values>) AND F NOT LIKE ' ')`, the legacy codes among
`ST_FIPS`'s values) for `ST_FIPS`, `PANEL_TYP`, `SCALE` and `BASE_TYP`; the
rule's (`PNP_REASON IS NOT NULL AND (PNP_REASON <> '' OR PNP_REASON LIKE ' ')
AND PANEL_TYP IN (<the four types that are not Not Printed>) AND PANEL_TYP NOT
LIKE ' '`); and `SHAPE IS NULL`. It selects 7,462 rows on 2026-10-12. Over the 92
pages the union selects no row the model accepts, the model rejects 299 the
union does not, and those 299 are the wrong-case values above (by `OBJECTID`
and by field and value), so on 87 pages the two agree and on five they differ
by exactly those rows.

**`ST_FIPS` drops the leading zero on five states, and `4` is admitted by
decision.** `1` (600 rows, 11 DFIRMs), `5` (447, 17), `8` (363, 5) and `6` (292,
4) clear the bar of 184 rows and are in `legacy.json`; each is in DFIRMs whose
ID begins with the padded code. `4` (132 rows, all `04009C`) does not. It
validates with a warning because the political areas' `4` is admitted by
Seth Fitzsimmons's decision of 2026-10-11 and the models share one `D_State_FIPS`
enum; `legacy.json` has no layer 3 entry for it, so the selection test does not
count it. Without it the layer rejects 7,594.

**`FIRM_PAN` is "made up of ST_FIPS, PCOMM, PANEL and SUFFIX", and the models do
not check it.** The service rejects string concatenation in a `where`, so the
disagreement was counted by reading every row's attributes: 13,879 rows (7.6%)
differ from `ST_FIPS + PCOMM + PANEL + SUFFIX`. 1,834 differ only by an unpadded
`ST_FIPS` (the legacy codes and `4`), 41 by an `ST_FIPS` of `04` on `05139C`'s
panels, 2 by a lowercase suffix (`08005C`), and 12,002 otherwise, in 108
DFIRMs (268 in `37183C`), among them `PCOMM` `067` against a `FIRM_PAN` of
`17067C0225E`. A rule that rejected them would reject 7.6% of the layer, so
the models take each field alone.

`FIRM_ID` is 32 long on the service and 25 in the reference; the models take the
service's. `SOURCE_CIT` "must match a value in `L_Source_Cit`", `FIRM_PAN` is a
join key of `L_Pan_Revis`, `L_MT2_LOMR`, `S_Label_Ld` and `S_Label_Pt`, and none
of those is modelled. `PRE_DATE` is `9/9/9999`, the date null, on 170,984 rows
(`PRE_DATE = timestamp '9999-09-09 00:00:00'`): the preliminary date is unset on
most panels, which the description allows. The panels share `DFIRM_ID`,
`VERSION_ID`, `SOURCE_CIT` and `ST_FIPS` with the political areas, and
`PCOMM` is, for community-based maps, the FEMA community number. A panel is a
Polygon or a MultiPolygon: Table 4 does not hold `S_FIRM_Pan` to "Must Be
Single Part", and 4 of 183,680 are multipart.

## What the general structures hold that the reference does not allow

Layer 24 has 285,947 rows (`service/observed/24.json`, 2026-10-12). The
union of every clause selects 9,521 (3.3%); the model rejects 9,556 (3.3%).
The difference, 35 rows, is all `STRUCT_TYP` in the wrong case (below).
Every row was read: paged in 286 windows of about 1,000 by `OBJECTID` (the ids
run to 2,350,391, so windows are cut from the sorted ids, not from a fixed
width), with geometry, and each row validated; the union's ids in the same
window were compared with the rows the model rejects. The union selects no row
the model accepts. On 275 pages the two agree and on 11 they differ by exactly
the wrong-case rows. Every shape is a LineString; none is null or empty.

- **`CST_STRUCT` is outside `D_Cst_Struct` on 8,909**: a lone space on 8,897
  (`CST_STRUCT LIKE ' '`; the service's `= ''` counts 125,648 because it folds
  the lone spaces into the empty strings), `MISCELLANEOUS STRUCTURES` on 11 and
  `COASTAL ARMORING STRUCTURES` on 1. The class is optional, and 150,755 rows
  hold no value. The lone space is a value, as it is in the water lines' flags.
- **`STRUCT_TYP` is missing on 102** (`= ''`) **and outside the vocabulary on
  58**: `Dike` 30, `1-Percent-Annual-Chance Flood Discharge Contained in
  Structu` 12 (cut off at 64 characters), `Spillway` 6, `Other/Misc Structure`
  3, and one to two rows each of `0.2-Percent-Annual-Chance ... Struc`,
  `1-PCT-Annual-Chance ...`, `Floodway Contained in Channel` and `Brigdge`.
- **`SOURCE_CIT` is missing on 142** (119 null, 23 empty), **`STRUCT_ID` on 15**
  and **`VERSION_ID` on 3**.
- **The `STRUC_DESC` rule breaks on 148 rows** whose type validates and has no
  description. The union's clause for it selects 293, because the service folds
  case and 145 of those hold `Floodway Contained In Structure`, which the
  model rejects for its type first.
- **35 hold a reference type in the wrong case**: 33 `Floodway Contained In
  Structure` and two the reference's percent types with a capital `In`. The
  service folds case in `=`, `IN` and grouping, so the union cannot select them;
  the control lists them by value.

The union joins with `OR` each required field's missing clause (`F IS NULL OR
(F = '' AND F NOT LIKE ' ')`) for `DFIRM_ID`, `VERSION_ID`, `STRUCT_ID` and
`SOURCE_CIT`; the outside clause for `STRUCT_TYP` (`F IS NULL OR NOT (F IN
(<the values> AND F NOT LIKE ' ')`, the legacy forms among the values);
the optional fields' (`NOT (<missing> OR (F IN (<the values>) AND F NOT LIKE '
'))`) for `CST_STRUCT` and `SHOWN_FIRM`; the rule's (`STRUCT_TYP IN (<the three
contained types>) AND STRUCT_TYP NOT LIKE ' '` with no `STRUC_DESC`); and `SHAPE
IS NULL`. Per clause: `CST_STRUCT` 8,909, `STRUCT_TYP` 160, `SOURCE_CIT` 142,
`STRUCT_ID` 15, `VERSION_ID` 3, the rule 293, the others 0; one row is in two.

**The legacy `STRUCT_TYP` forms are licensed by a count that folds case.**
The data writes the three "contained in structure" types as `1 Pct Annual
Chance Flood Discharge Contained In Structure` and `0.2 Pct ...`, and as `1
PCT ...` and `0.2 PCT ...` with `in` or `In`. The snapshot shows one form
per group and counts the group: 13,200 and 10,940. Read row by row, the
form shown has 310 and 383 rows (86 and 83 DFIRMs); the other 12,890 and
10,557 are `PCT` forms. `legacy.json` lists the form shown, with the
snapshot's count, which the selection test requires. The threshold cannot see
the `PCT` forms, so a decision (2026-10-12) admits each at its row-read count:
`1 PCT ... in` 9,135, `1 PCT ... In` 3,753, all capitals 2, `0.2 PCT ... in`
5,430 and `0.2 PCT ... In` 5,127. The enum numbers the members that differ only
in case (`..._CASE_2`). `Other / Misc Structure` (379 rows, 86 DFIRMs;
the reference's `Other / Misc. Structure` has 16 in 5) is licensed the same way
with no case variants. `Floodway Contained In Structure` (292 in the snapshot)
is not legacy: 114 of the rows are the reference's `Contained in` and 178 are
wrong-case, so `legacy_candidates` and `report-observed` compare case-folded.
The decision does not reach those 178: they are a reference value in another
case, rejected as the panels' `ORTHOPHOTO` is.

**The `STRUC_DESC` rule names the reference's three types, not the legacy
forms.** "Required for structures that have a contained in structure type"
describes the legacy forms as much as the reference's, and 14,445 rows hold
a `Pct` or `PCT` form with no description, all of which the model admits. A
rule that rejected them would reject a combination the legacy policy admits,
and `test_no_value_pair_a_rule_rejects_is_common` stops it.

**`CST_STRUCT`, "populated when the structure type is a coastal structure",
is not a rule.** The reference names no type as coastal (`Jetty`, `Seawall`,
`Revetment` and `Wing Wall` are candidates), so nothing says when it is
required. 7,216 rows hold `NP`; 150,755 hold nothing.

`SHOWN_FIRM` is `U` on 171,552 rows (60%), `T` on 85,140, `F` on 29,019, empty
on 231 and null on 5; it is optional (`R1`). `STRUCT_ID`, `SOURCE_CIT` and
`VERSION_ID` are 32, 21 and 11 long on the service and 25, 11 and 11 in the
reference; the models take the service's. `SOURCE_CIT` "must match a value in
`L_Source_Cit`", which the models do not check. Structures name their stream by
`WTR_NM`, as the water lines do; the join is not checked, and `L_Cst_Struct`
joins by `STRUCT_ID` but is not a service layer. The FIRM Database reference's
section for `S_Gen_Struct` never says what the table "contains information
about", so the model's description is the table summary (`SUMMARY_ONLY`).

## What the water areas hold that the reference does not allow

Layer 32 has 779,833 rows (`service/observed/32.json`, 2026-10-12). The
union of every clause selects 12,855 (1.65%); the model rejects 12,858
(1.65%). The difference, 3 rows, is all polygons the service returns empty
(below). Every row was read: paged in 780 windows of about 1,000 cut from the
sorted `OBJECTID`s (ids run to 4,478,248), with geometry, and each row
validated; the union's ids in the same window were compared with the rows the
model rejects. The union selects no row the model accepts, and 778 windows
agree exactly. The 40 polygons with a perimeter over 5 degrees were read
generalised (`maxAllowableOffset` 0.0001), since the service cannot return
the longest whole; the model checks only a geometry's type and that it has
rings, which generalising keeps. 779,502 shapes are Polygons, 326
MultiPolygons, and 5 null.

- **`WTR_NM` is missing on 11,548** (6,643 null, 4,905 `''`), in 34 DFIRMs,
  3,158 of them in `12073C`. A lone space is text and validates (337 rows), as
  does `NP` (469,343): "Unnamed bodies of water follow the convention shown in
  Section 5.3 related to null text values."
- **`SHOWN_FIRM` and `SHOWN_INDX` both hold a lone space on 686 rows**, every
  one in `27127C`. No row holds one in only one flag.
- **`SOURCE_CIT` is missing on 616** (all null), in 15 DFIRMs, 516 of them in
  `37021C`.
- **5 rows have no geometry** (`SHAPE IS NULL`): 3 in `22051C`, 2 in `48361C`.
- **3 polygons come back with no rings** (`coordinates: []`), which no `where`
  selects. `460719` and `461325` (`39031C`) report no area, and `SHAPE.STArea()
  = 0` finds them along with 54 slivers that have a shape and validate.
  `206560` (`22051C`) reports an area of 309,055 square degrees, more than the
  Earth's surface, and a perimeter of 8,616.

`DFIRM_ID`, `VERSION_ID` and `WTR_AR_ID` are missing on none. The model has no
rules. The union joins with `OR` each required field's missing clause (`F IS
NULL OR (F = '' AND F NOT LIKE ' ')`) for `DFIRM_ID`, `VERSION_ID`,
`WTR_AR_ID`, `WTR_NM` and `SOURCE_CIT`; each flag's optional clause (`NOT
(<missing> OR (F IN ('T', 'F', 'U', '1') AND F NOT LIKE ' '))`, the legacy `1`
among the values); and `SHAPE IS NULL`. Per clause: `WTR_NM` 11,548,
`SOURCE_CIT` 616, `SHOWN_FIRM` 686, `SHOWN_INDX` 686, geometry 5, the others
0; the flags' rows are the same 686, and no other row is in two clauses.

**`SHOWN_FIRM` holds `1` on 888 rows**, every water area in four DFIRMs
(`47025C` 449, `37153C` 281, `37093C` 144, `13049C` 14), each with `SHOWN_INDX`
`F`. It is over the layer's legacy bar (780), so `legacy.json` admits it. It is
the first legacy value in `D_TrueFalse`, and the models share one enum per
domain, so it validates with a warning in every flag of every layer:
`SFHA_TF`, `DUAL_ZONE`, `ANI_TF`, `USACE_LEV`, `PL84_99TF` and the `SHOWN_`
flags. No other modelled layer's snapshot holds it. The reference does not
say whether it means `T`.

**Six polygons in `22051C` report impossible areas**, 61,044 to 309,055 square
degrees, with perimeters of 1,621 to 8,616. The service returns one of them
(`206560`) empty, which the model rejects; the other five come back as
polygons and validate, since the model checks a geometry's type, not its
extent.

`SHOWN_FIRM` is null on 239,211 rows, `''` on 187,707, `F` on 193,767, `U` on
132,379 and `T` on 25,195; it and `SHOWN_INDX` are optional (`A`).
`WTR_AR_ID` and `SOURCE_CIT` are 32 and 21 long on the service and 25 and 11
in the reference; the models take the service's. Water areas name their
water by `WTR_NM`, as the water lines do, and "features that appear in both
must match exactly"; the models do not check it.

## What the transect baselines hold that the reference does not allow

Layer 18 has 35,354 rows (`service/observed/18.json`, 2026-10-12). The union
of every clause selects 140 (0.40%); the model rejects 159 (0.45%). The
difference, 19 rows, is the wrong-case type below. Every row was read: paged in
36 windows of about 1,000 cut from the sorted `OBJECTID`s (ids run to
162,666), with geometry, and each row validated; the union's ids in the same
window were compared with the rows the model rejects. The union selects no row
the model accepts. Every shape is a LineString: none is null, empty or
multipart.

- **`SOURCE_CIT` is missing on 140** (all null): 138 in `23023C`, every
  baseline of that DFIRM, and 2 in `36103C`.
- **`TBASE_TYP` holds `Zero Foot Contour Referenced To Tidal Datum` on 19**, all
  in `36073C`: the November 2016 Domain Tables reference's spelling of code
  1020, which the 2019 and 2024 editions write `Referenced to`. The service folds
  case in `=`, `IN` and grouping, so the union cannot select them, and
  `report-observed` counts the reference's spelling as 24, these 19 included.
- **`TBASE_TYP` holds `SANDY BEACH-SMALL DUNE` on 13**, all in `23023C` and all
  also missing `SOURCE_CIT`: `D_Shr_Typ`'s shoreline type `Sandy Beach-Small
  Dune`, upper-cased. Under the legacy bar (35).

`DFIRM_ID`, `VERSION_ID`, `TBASELN_ID`, `R_ST_DESC`, `R_END_DESC`, `WTR_NM` and
`V_DATUM` are missing or outside their vocabulary on none. The model has no
rules. The union joins with `OR` each required field's missing clause (`F IS
NULL OR (F = '' AND F NOT LIKE ' ')`) for `DFIRM_ID`, `VERSION_ID`,
`TBASELN_ID`, `R_ST_DESC`, `R_END_DESC`, `WTR_NM` and `SOURCE_CIT`; the outside
clause (`F IS NULL OR NOT (F IN (<the values>) AND F NOT LIKE ' ')`, the legacy
types among `TBASE_TYP`'s values) for `TBASE_TYP` and `V_DATUM`; and `SHAPE IS
NULL`. Per clause: `SOURCE_CIT` 140, `TBASE_TYP` 13, the others 0; the 13 are
among the 140.

**The threshold admits three types** (`legacy.json`, bar 35.354 rows), each in
one or two DFIRMs:

- `Zero Foot Contour` (926, `36103C`): the words the three `Zero Foot Contour
  ...` types begin with, without the source that tells them apart. No edition
  of the Domain Tables reference lists it (2016, 2019, 2024).
- `NON-ERODIBLE BLUFF` (347; `23015C` 222, `23023C` 125): `D_Shr_Typ`'s shoreline
  type `Non-Erodible Bluff` (code 1030), upper-cased, in the transect baseline
  type. A value of another domain, not a spelling of this one.
- `ZERO FOOT C` (54, `24009C`): a `Zero Foot Contour ...` type cut to 11
  characters and upper-cased; the cut leaves no word saying which of the three.

`CST_MDL_ID` is null on 12,559 rows, `''` on 3,254 and a lone space on 476; it
is optional (`A`). `R_ST_DESC` is `NP` on 22,056 and `WTR_NM` on 16,560.
`TBASELN_ID`, `CST_MDL_ID` and `SOURCE_CIT` are 32, 32 and 21 long on the
service and 25, 25 and 11 in the reference; the models take the service's. The
coastal transects (`S_Cst_Tsct_Ln`) join a baseline by `TBASELN_ID`, and
`CST_MDL_ID` joins `L_Cst_Model`, which is not a service layer; the models do
not check either. The section calls the table a "spatial file" ("The
S_Tsct_Basln spatial file contains information about"), which
`reference_intro` reads as it reads "table" and "layer".

## What the coastal transects hold that the reference does not allow

Layer 15 has 22,367 rows (`service/observed/15.json`, 2026-10-13). The union of
every clause selects 4,715 (21.08%); the model rejects 8,893 (39.76%). The
difference, 4,178 rows, is the wrong-case values below. Every row was read:
paged in 23 windows of about 1,000 cut from the sorted `OBJECTID`s (ids run to
155,023), with geometry, and each row validated; the union's ids in the same
window were compared with the rows the model rejects. The union selects no row
the model accepts. Every shape is a LineString: none is null, empty or
multipart. The output is `~/.local/state/nfhl-controls/layer-15/control15.json`,
beside `control15.py`.

The union joins with `OR`: for each required text field the missing clause
(`F IS NULL OR (F = '' AND F NOT LIKE ' ')`); for each required number `F IS NULL
OR F = -9999`; for each required vocabulary field the outside clause (`F IS NULL
OR NOT (F IN (<the values>) AND F NOT LIKE ' ')`, the legacy values among them);
for each optional vocabulary field `F LIKE ' ' OR (F <> '' AND F NOT IN (<the
values>))`; and `SHAPE IS NULL`. Per clause, with the rows the service counts:

- Missing required text: `LOC_DESC` 2,071, `TBASELN_ID` 338 (270 `''`, 68 null),
  `SOURCE_CIT` 6, `WTR_NM` 4; `DFIRM_ID`, `VERSION_ID`, `TRAN_LN_ID` and
  `TRAN_NO` none.
- Required numbers: `XCOORD` and `YCOORD` 898 each, the same rows (722 null, 176
  `-9999`); `RUP` 742 and `SWEL` 20, all `-9999`. `-8888`, section 7.3's number
  for a field not populated, is a value: 14,648 `RUP` and 10,793 `SWEL`.
- Required vocabulary: `V_DATUM` 410 (all null), `EVENT_TYP` 117 (`''`);
  `CSTLN_TYP`, `ELEV_UNIT` and the five flags none.
- Lone spaces in optional vocabulary fields, which the vocabulary rejects:
  `FTCHLNUNIT` 1,158, `TIME_UNIT` 649, `LEN_UNIT` 488, `BEACH_SET` 472, `EROS_METH`
  442, `SHORE_TYP` 597, `METHOD` 244 and `VZONE_EXT` 211. `''` does not match
  `LIKE ' '`, so these are lone spaces only.

**The model alone rejects 4,178 rows, each holding a value that differs from a
reference value only in case.** The service folds case in `=`, `IN` and grouping,
so the union cannot select them and `report-observed` counts them under the
reference's spelling. The model-only rows by field and value, from the control
(a row that also breaks a union clause is in the union and not listed):

- `BEACH_SET` `Sandy Beach Backed By Low Sand Berm or High Sand Dune Formation`
  3,207 and `... Backed By Shore Protection Structures` 695, where the reference
  has `by`;
- `TIME_UNIT` `Seconds` 93; `METHOD` `Cut from topo` 66; `EVENT_TYP`
  `1 PERCENT CHANCE` 69; `SHORE_TYP` `Non-erodible Bluff` 45 and `Non-erodible
  bluff` 11; `CSTLN_TYP` `OPEN COAST` 27; `VZONE_EXT` `RUNUP` 20 and `WAVE
  OVERTOPPING SPLASH ZONE` 7.

The sum, 4,240, exceeds 4,178 by 62 rows that hold two such values. Reading every
row counts the exact forms (`~/.local/state/nfhl-controls/layer-15/rows15.py`):
`BEACH_SET` `Backed By Low Sand ...` 3,458 in 90 DFIRMs and `Backed By Shore
Protection ...` 747 in 56; `METHOD` `Cut From Topo` 235 (4 DFIRMs), `Cut from
topo` 66 (`26033C`), `Combo Of Topo And Survey` 25 (`44005C`); `TIME_UNIT`
`Seconds` 171 (`44005C`, `51099C`, `37095C`, `36073C`) and `Days` 25 (`34033C`);
`SHORE_TYP` as above (`26033C`, `26103C`, `27137C`); `CSTLN_TYP` `OPEN COAST` 28
(`26099C`); `EROS_METH` `OTHER` 5 (`36055C`); `VZONE_EXT` `BREAKING WAVE HT` 1
(`26099C`). The `By` capital in `BEACH_SET` may be an earlier edition's text, as
`Referenced To Tidal Datum` was for the baselines; only the 2024 edition is
vendored here, so that is unchecked. None of these is a legacy value: the
snapshot folds each under the reference's spelling, so none reaches the
threshold, and a maintainer's `decision` would admit one.

**The threshold admits twelve values** (`legacy.json`, bar 22.367 rows), in the
fields below. `NP` is section 7.3's value for a field intentionally not
populated, which none of `D_Method`, `D_Event`, `D_VZone` or `D_Time_Units` lists:
`METHOD` 249 (7 DFIRMs), `EVENT_TYP` 8,873 (132 DFIRMs), `VZONE_EXT` 232 (6),
`TIME_UNIT` 308 (4). The rest:

- `V_DATUM` `ASVD02` 374 (`600001`, American Samoa) and `GUVD03` 62 (`660001`,
  Guam; the domain lists `GUVD04`). The same two values are under the bar in the
  zones, BFEs and cross sections, and the domain is shared, so they now validate
  with a warning there as well: the zones' rule on `V_DATUM` without a static
  BFE reaches one more row (16,572, not 16,571).
- `NA` 28 in each of `FTCHLNUNIT`, `LEN_UNIT` and `TIME_UNIT`, the same 28 rows in
  `26099C`, which also hold `OPEN COAST`.
- `VZONE_EXT` `WHAFIS` 111 (a wave model of `D_Wave_Mdl`, 5 DFIRMs),
  `30 FOOT SPLASH ZONE BEHIND S` 66 (cut at the field's 28 characters, 3 DFIRMs)
  and `RUNUP EXTENT` 41 (2 DFIRMs).

**`D_Event`'s dashes are repaired.** The reference prints `1-Percent-Chance` under
the note that the database template has no dashes; the service holds `1 Percent
Chance` on 13,376 rows and the dashed form on none (`repairs.json`, with the
quote). `EVENT_TYP` is `NP` on 8,873 and `''` on 117.

**Two defects in the reference's extraction.** `D_Time_Units` runs over two pages
and the second page's header is cut mid-word by a stray rule, so its rows
(`SECONDS`, `WEEKS`, `YEARS`) were set aside as irregular and the domain listed
four units; `SECONDS` is 7,788 of this layer's `TIME_UNIT` values.
`nfhl.extract` rejoins such a header. The field table joins `VZONE_EXT` to
`D_VZONE` and the section is `D_VZone`.

**Two rules on the units.** `LEN_UNIT` "is populated when the SETUP_DEPTH,
CON_HT, SIG_HT or MEAN_HT field is populated", and `TIME_UNIT` when `SIG_PD`,
`CON_PD` or `MEAN_PD` is. Both are modelled as `require_if` over `AnyOf` of
`Populated` conditions (`when_any_populated` in `relationships.json`). The
reference writes `SETUP_DEPTH`; the table and the service name the field
`SETUP_DPTH`, which the rule reads. A measure of `-8888`, the number section 7.3
substitutes for a value not populated, counts as populated: the reference does
not exempt it, and 1,950 and 3,657 rows hold a measure and no unit when it does.
A unit of `NP` satisfies the rule. The model rejects 779 rows for `LEN_UNIT` and
1,826 for `TIME_UNIT` that it did not reject before; the rest of each rule's
rows are already rejected for another field, and a model rule does not run on a
row with a rejected field. The units' `UnitIn` annotation, the datum annotation
on `SWEL` and `RUP` and `ELEV_UNIT` as the unit of those two are modelled.
`DATUM_CONV` has no unit field, and "such as MLLW and MSL" names the gage datum,
not a field.

`TBASELN_ID` joins `S_Tsct_Basln` and `CST_MDL_ID` joins `L_Cst_Model`, which is
not a service layer; the models check neither. `TRAN_LN_ID`, `TBASELN_ID`,
`CST_MDL_ID` and `SOURCE_CIT` are 32, 32, 32 and 21 long on the service and 25,
25, 25 and 11 in the reference; the models take the service's.
