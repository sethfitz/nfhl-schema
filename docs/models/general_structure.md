---
sidebar_position: 1
---

# GeneralStructure

Location and attributes for flood control structures shown on the flood profile
and FIRM. Published as layer 24 of the NFHL MapServer, which also carries
`GFID`, `GlobalID`, `OBJECTID`, `SHAPE.STLength()`; the reference does not
define them, so they are optional and validated only by type.

## Fields

| Name | Type | Description |
| -----: | :----: | ------------- |
| `id` | [`int64`](../system/numeric.md) (optional) | The service's OBJECTID, which ArcGIS's GeoJSON output writes as the feature id. It numbers rows in one copy of the service and identifies nothing beyond it; the reference's key is STRUCT_ID, assigned within one FIRM Database (one DFIRM_ID). |
| `bbox` | [`bbox`](../system/geometric.md) (optional) | An optional bounding box for the feature |
| `geometry` | [`geometry`](../system/geometric.md) | The general structure: in the reference's words, a line representing the primary characteristic of a structure that affects flood risk, such as the transportation centerline a bridge carries or the top of a dam.<br/><br/>*Allowed geometry types: LineString* |
| `DFIRM_ID` | `string` | Study Identifier. For a single-jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code and the letter “C” (e.g., 48107C). Within each FIRM Database, the DFIRM_ID value will be identical.<br/><br/>*Maximum length: 6* |
| `VERSION_ID` | `string` | Version Identifier. Identifies the product version and relates the feature to standards according to how it was created.<br/><br/>*Maximum length: 11* |
| `STRUCT_ID` | `string` | Primary key for table lookup. Assigned by table creator.<br/><br/>*Maximum length: 32* |
| `STRUCT_TYP` | [`StructTyp`](types/struct_typ.md) | Structure Type. These are hydraulic structures within the Flood Risk Project area. Acceptable values for this field are listed in the D_Struct_Typ table. |
| `CST_STRUCT` | [`CstStruct`](types/cst_struct.md) (optional) | Coastal Structure Classification. This provides the primary classification of the coastal structure. This field is populated when the structure type is a coastal structure. Acceptable values for this field are listed in the D_Cst_Struct table. |
| `STRUCT_NM` | `string` (optional) | Structure Name. This is the proper name of the feature and/or the related transportation feature name as shown on the FIRM and/or the flood profile. If the flood profile has the proper structure name and no related transportation name, this field stores the proper name (e.g., Hoover Dam). If the flood profile has the related transportation name and no proper name, this field stores the related transportation name (e.g., Main Street). If the flood profile has the proper name and the transportation name, this field stores both names (e.g., Hoover Dam / Main Street). If structure has no proper name and no related transportation name, this field is left blank; this field should not store the structure type (e.g., dam).<br/><br/>*Maximum length: 50* |
| `WTR_NM` | `string` (optional) | Surface Water Feature Name. This is the formal name of the surface-water feature associated with the structure, as it will appear on the hardcopy FIRM. Required in the reference, with the footnote "Field is applicable for BLE database."<br/><br/>*Maximum length: 100* |
| `LOC_DESC` | `string` (optional) | Location Description. This is a description of where the structure is located. Used in FIS Report Flood Protection Measures table, if applicable.<br/><br/>*Maximum length: 254* |
| `STRUC_DESC` | `string` (optional) | Structure Description. This is a description of the structure itself. This is required for structures that have a contained in structure type, to describe the type of structure that has contained flooding (e.g., culvert, channel).<br/><br/>*Maximum length: 254* |
| `SHOWN_FIRM` | [`TrueFalse`](types/true_false.md) (optional) | Shown on FIRM. If the structure is shown on the FIRM, this field would be True. If the structure is not shown on the FIRM, this field is False. All structures shown on the profile must be shown on the FIRM. Acceptable values for this field are listed in D_TrueFalse. Required in the reference, with the footnote "Field is applicable for BLE database." |
| `SOURCE_CIT` | `string` | Source Citation. Abbreviation used in the metadata file when describing the source information for the feature. The abbreviation must match a value in L_Source_Cit.<br/><br/>*Maximum length: 21* |
| `GFID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 36* |
| `GlobalID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 38* |
| `OBJECTID` | [`int64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STLength()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |

## Constraints

- `struc_desc` is required when struct_typ is 0.2-Percent-Annual-Chance Flood Discharge Contained in Structure, 1-Percent-Annual-Chance Flood Discharge Contained in Structure or Floodway Contained in Structure
