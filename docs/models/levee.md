---
sidebar_position: 1
---

# Levee

The S_Levee table contains information about levees shown on the FIRMs that are
accredited and known to be protecting against the 1% annual-chance flood, as
well as levees that are provisionally accredited, and non-accredited. The
purpose of this table is to document the accreditation status of levees, as well
as associated information necessary to be shown on the FIRM and for the
population of FIS Report text related to levee structures. The spatial entities
representing levees are lines, drawn at the centerline of levees, floodwalls and
levee closure structures. Published as layer 23 of the NFHL MapServer, which
also carries `GFID`, `GlobalID`, `OBJECTID`, `SHAPE.STLength()`; the reference
does not define them, so they are optional and validated only by type.

## Fields

| Name | Type | Description |
| -----: | :----: | ------------- |
| `id` | [`int64`](../system/numeric.md) (optional) | The service's OBJECTID, which ArcGIS's GeoJSON output writes as the feature id. It numbers rows in one copy of the service and identifies nothing beyond it; the reference's key is LEVEE_ID, assigned within one FIRM Database (one DFIRM_ID). |
| `bbox` | [`bbox`](../system/geometric.md) (optional) | An optional bounding box for the feature |
| `geometry` | [`geometry`](../system/geometric.md) | The levee: in the reference's words, a line drawn at the centerline of a levee, floodwall or levee closure structure shown on the FIRM, with its accreditation status.<br/><br/>*Allowed geometry types: LineString* |
| `DFIRM_ID` | `string` | Study Identifier. For a single-jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code and the letter “C” (e.g., 48107C). Within each FIRM Database, the DFIRM_ID value will be identical.<br/><br/>*Maximum length: 6* |
| `VERSION_ID` | `string` | Version Identifier. Identifies the product version and relates the feature to standards according to how it was created.<br/><br/>*Maximum length: 11* |
| `LEVEE_ID` | `string` | Primary key for table lookup. Assigned by table creator.<br/><br/>*Maximum length: 32* |
| `FC_SYS_ID` | `string` | National Levee Database (NLD) System ID (FC_SYSTEM). The unique identifier, assigned in the NLD, for each levee system with which a levee segment is associated. Used to link levee systems in the NFHL with the NLD, where more detailed information about each levee system can be found.<br/><br/>*Maximum length: 32* |
| `LEVEE_NM` | `string` (optional) | Any commonly used name for the levee. Required in the reference, with the footnote "Field is applicable for BLE database."<br/><br/>*Maximum length: 100* |
| `LEVEE_TYP` | [`LeveeTyp`](types/levee_typ.md) (optional) | Describes the type of protecting structure. Valid values can be found in the D_Levee_Typ domain table. Required in the reference, with the footnote "Field is applicable for BLE database." |
| `WTR_NM` | `string` (optional) | Surface Water Feature Name. Name of the water body that the levee structure or segment is providing protection from. Required in the reference, with the footnote "Field is applicable for BLE database."<br/><br/>*Maximum length: 100* |
| `BANK_LOC` | `string` (optional) | Bank Location of Levee. A field to describe the location of the levee centerline in relation to the water body. For example, “Left Bank,” “Right Bank.” Required in the reference, with the footnote "Field is applicable for BLE database."<br/><br/>*Maximum length: 100* |
| `USACE_LEV` | [`TrueFalse`](types/true_false.md) (optional) | Determines if this is a U.S. Army Corps of Engineers (USACE) Levee. Valid values can be found in the D_TrueFalse domain table. Required in the reference, with the footnote "Field is applicable for BLE database." |
| `DISTRICT` | [`USACEDistrict`](types/usace_district.md) (optional) | USACE District Code. This is the code for the USACE district responsible for the segment. Field is required when the structure is owned or maintained by the USACE, with a value of “T” in the USACE_LEV field. Valid values can be found in the D_USACE_District domain table. |
| `PL84_99TF` | [`TrueFalse`](types/true_false.md) (optional) | Status of levee. This field indicates if the levee is covered under PL84-99, which is the USACE authority to provide emergency assistance and repair damaged levees. Valid values can be found in the D_TrueFalse domain table. Required in the reference, with the footnote "Field is applicable for BLE database." |
| `CONST_DATE` | [`int64`](../system/numeric.md) (optional) | Construction Date. Date on which construction was completed. |
| `DGN_FREQ` | `string` (optional) | Design Frequency. Enter the design frequency of the levee, if known. For accredited levees, a valid entry in this field is required.<br/><br/>*Maximum length: 50* |
| `FREEBOARD` | [`float64`](../system/numeric.md) (optional) | Freeboard Value. For accredited levees, enter the smallest amount of freeboard above the 1% annual-chance flood along the entire levee, floodwall, closure structure or embankments.<br/><br/>*`unit given by LEN_UNIT`* |
| `LEVEE_STAT` | [`LeveeStatus`](types/levee_status.md) (optional) | Levee Status. This field stores the accreditation status of the levee. Acceptable values for this field are listed in the D_Levee_Status table. Required in the reference, with the footnote "Field is applicable for BLE database." |
| `PAL_DATE` | [`int64`](../system/numeric.md) (optional) | Provisionally Accredited Levee Date. This field stores the end date of the Provisionally Accredited Levee (PAL) period for the levee associated with the flood zone. This field is populated for those structure features that have a PAL designation. |
| `LEV_AN_TYP` | [`LeveeAnalysisType`](types/levee_analysis_type.md) (optional) | Levee Analysis Type for Non-Accredited Levees. This should only be populated if LEVEE_STAT is Non-Accredited. Acceptable values for this field are listed in the D_Levee_Analysis_Type table. |
| `FC_SEG_ID` | `string` | National Levee Database (NLD) Segment ID (FC_SEGMENT). If the levee, floodwall or closure structure is included in the NLD, this is the segment identification number assigned in the NLD. This field is populated for all flood control features, included in the NLD, regardless of their status.<br/><br/>*Maximum length: 25* |
| `OWNER` | `string` (optional) | Levee Owner. Name of the entity that owns the levee. Required in the reference, with the footnote "Field is applicable for BLE database."<br/><br/>*Maximum length: 100* |
| `LEN_UNIT` | [`LengthUnits`](types/length_units.md) (optional) | This unit indicates the measurement system used for the freeboard elevations. Normally this would be feet. Acceptable values for this field are listed in the D_Length_Units table. |
| `SOURCE_CIT` | `string` | Source Citation. Abbreviation used in the metadata file when describing the source information for the feature. The abbreviation must match a value in L_Source_Cit.<br/><br/>*Maximum length: 21* |
| `GFID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 36* |
| `GlobalID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 38* |
| `OBJECTID` | [`int64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STLength()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |

## Constraints

- `district` is required when usace_lev is T
- `lev_an_typ` is forbidden when levee_stat is not Non-Accredited and lev_an_typ is not NP
