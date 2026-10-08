---
sidebar_position: 1
---

# ProfileBaseline

Location and attributes for profile baseline and stream centerline features for
the Flood Risk Project area. Published as layer 17 of the NFHL MapServer, which
also carries `GFID`, `GlobalID`, `OBJECTID`, `SHAPE.STLength()`; the reference
does not define them, so they are optional and validated only by type.

## Fields

| Name | Type | Description |
| -----: | :----: | ------------- |
| `id` | [`int64`](../system/numeric.md) (optional) | The service's OBJECTID, which ArcGIS's GeoJSON output writes as the feature id. It numbers rows in one copy of the service and identifies nothing beyond it; the reference's key is BASELN_ID, assigned within one FIRM Database (one DFIRM_ID). |
| `bbox` | [`bbox`](../system/geometric.md) (optional) | An optional bounding box for the feature |
| `geometry` | [`geometry`](../system/geometric.md) | The profile baseline: in the reference's words, the location of a profile baseline or stream centerline feature for the Flood Risk Project area.<br/><br/>*Allowed geometry types: LineString* |
| `DFIRM_ID` | `string` | Study Identifier. For a single-jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code and the letter “C” (e.g., 48107C). Within each FIRM Database, the DFIRM_ID value will be identical.<br/><br/>*Maximum length: 6* |
| `VERSION_ID` | `string` | Version Identifier. Identifies the product version and relates the feature to standards according to how it was created.<br/><br/>*Maximum length: 11* |
| `BASELN_ID` | `string` | Primary key for table lookup. Assigned by table creator.<br/><br/>*Maximum length: 32* |
| `WTR_NM` | `string` | Surface Water Feature Name. This is the formal name of the surface water feature as it will appear on the hardcopy FIRM.<br/><br/>*Maximum length: 100* |
| `SEGMT_NAME` | `string` (optional) | Segment Name. This is an optional identification string for each link. If used, this value must be unique for a stream.<br/><br/>*Maximum length: 254* |
| `WATER_TYP` | [`ProfBaslnTyp`](types/prof_basln_typ.md) (optional) | Surface Water Feature Type. The type value describes the kind of watercourse represented. In the FIRM Database, this layer contains profile baselines and/or streams that are coincident with profile baselines. Acceptable values for this field are listed in the D_Prof_Basln_Typ table. Required in the reference, with the footnote "Field is applicable for BLE database." |
| `STUDY_TYP` | [`StudyTyp`](types/study_typ.md) (optional) | Study Type. This describes the type of Flood Risk Project performed for flood hazard identification. Acceptable values for this field are listed in the D_Study_Typ table. Required in the reference, with the footnote "Field is applicable for BLE database." |
| `SHOWN_FIRM` | [`TrueFalse`](types/true_false.md) (optional) | Profile Baseline Shown on FIRM. This field is true only if the profile baseline is shown on the FIRM. Because various FIS tables require a profile baseline for all studied reaches regardless of zone designation, this field must be populated to determine which profile baselines are to be shown on the FIRM panels. Acceptable values for this field are listed in the D_TrueFalse table. Required in the reference, with the footnote "Field is applicable for BLE database." |
| `SHOWN_INDX` | [`TrueFalse`](types/true_false.md) (optional) | Profile Baseline Shown on Index. This field is true only if the profile baseline is shown on the Index rather than use of S_Wtr_Ln. |
| `R_ST_DESC` | `string` (optional) | Reach Name Start Description. This describes the location of the start of the Flood Risk Project reach. Required in the reference, with the footnote "Field is applicable for BLE database."<br/><br/>*Maximum length: 254* |
| `R_END_DESC` | `string` (optional) | Reach Name End Description. This describes the location of the end of the Flood Risk Project reach. Required in the reference, with the footnote "Field is applicable for BLE database."<br/><br/>*Maximum length: 254* |
| `V_DATM_OFF` | `string` (optional) | Vertical Datum Offset (Conversion Factor). Populated if a single vertical datum offset cannot be used across the Flood Risk Project and offset values must be calculated stream by stream.<br/><br/>*Maximum length: 6*<br/>*`unit given by DATUM_UNIT`* |
| `DATUM_UNIT` | [`LengthUnits`](types/length_units.md) (optional) | Length Datum Offset (Conversion Factor) Units. This is the unit of measure for the vertical datum offset (conversion factor) distance height. Acceptable values for the field are listed in the D_Length_Units table. |
| `FLD_PROB1` | `string` (optional) | Description of Flooding Problems by flooding source.<br/><br/>*Maximum length: 254* |
| `FLD_PROB2` | `string` (optional) | Description of Flooding Problems by flooding source, continued. Used when FLD_PRB1 field does not have enough characters to hold the flooding problem description.<br/><br/>*Maximum length: 254* |
| `FLD_PROB3` | `string` (optional) | Description of Flooding Problems by flooding source, continued. Used when FLD_PRB1 and FLD_PRB2 fields do not have enough characters to hold the flooding problem description.<br/><br/>*Maximum length: 254* |
| `SPEC_CONS1` | `string` (optional) | Special Considerations field for describing the modeling methodology used.<br/><br/>*Maximum length: 254* |
| `SPEC_CONS2` | `string` (optional) | Second Special Considerations field for describing the modeling methodology used. Use this field when the description cannot be contained within the SPEC_CONS1 field.<br/><br/>*Maximum length: 254* |
| `START_ID` | `string` (optional) | Station Start Identification. This is the foreign key to the S_Stn_Start layer. This field is the link that is used to reference station start descriptions in the FDTs and profiles and which links the S_Profil_Basln table, L_XS_Elev table via the S_XS table and river marks in the S_Riv_Mrk table to the appropriate stationing starting point. Required in the reference, with the footnote "Field is applicable for BLE database."<br/><br/>*Maximum length: 32* |
| `SOURCE_CIT` | `string` | Source Citation. Abbreviation used in the metadata file when describing the source information for the feature. The abbreviation must match a value in L_Source_Cit.<br/><br/>*Maximum length: 21* |
| `GFID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 36* |
| `GlobalID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 38* |
| `OBJECTID` | [`int64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STLength()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |

## Constraints

- `spec_cons2` is forbidden when spec_cons1 is not populated
- `fld_prob3` is forbidden when fld_prob2 is not populated
- `fld_prob2` is forbidden when fld_prob1 is not populated
