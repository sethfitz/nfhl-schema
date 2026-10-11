---
sidebar_position: 1
---

# FloodHazardBoundary

The S_Fld_Haz_Ln table contains information about the flood zone boundary
features for the Flood Risk Project area. A spatial file with location
information also corresponds with this data table. Flood hazard data should not
be shown beyond the extent of the county/community boundary. If the modeled
information extends beyond the political area, the flood hazard data should be
clipped to the political boundary. The spatial elements representing the
boundaries of the flood hazard areas depicted on the FIRM are lines. Published
as layer 27 of the NFHL MapServer, which also carries `GFID`, `GlobalID`,
`OBJECTID`, `SHAPE.STLength()`; the reference does not define them, so they are
optional and validated only by type.

## Fields

| Name | Type | Description |
| -----: | :----: | ------------- |
| `id` | [`int64`](../system/numeric.md) (optional) | The service's OBJECTID, which ArcGIS's GeoJSON output writes as the feature id. It numbers rows in one copy of the service and identifies nothing beyond it; the reference's key is FLD_LN_ID, assigned within one FIRM Database (one DFIRM_ID). |
| `bbox` | [`bbox`](../system/geometric.md) (optional) | An optional bounding box for the feature |
| `geometry` | [`geometry`](../system/geometric.md) | The flood hazard boundary: in the reference's words, the flood zone boundary features of the Flood Risk Project area, the boundaries of the flood hazard areas depicted on the FIRM.<br/><br/>*Allowed geometry types: LineString* |
| `DFIRM_ID` | `string` | Study Identifier. For a single-jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code and the letter “C” (e.g., 48107C). Within each FIRM Database, the DFIRM_ID value will be identical.<br/><br/>*Maximum length: 6* |
| `VERSION_ID` | `string` | Version Identifier. Identifies the product version and relates the feature to standards according to how it was created.<br/><br/>*Maximum length: 11* |
| `FLD_LN_ID` | `string` | Primary key for table lookup. Assigned by table creator.<br/><br/>*Maximum length: 32* |
| `LN_TYP` | [`LnTyp`](types/ln_typ.md) | Line Type. These line types describe the flood boundary and may be used to indicate how the feature must be depicted on the hardcopy FIRM. Acceptable values for this field are listed in D_Ln_Typ table. |
| `SOURCE_CIT` | `string` | Source Citation. Abbreviation used in the metadata file when describing the source information for the feature. The abbreviation must match a value in L_Source_Cit.<br/><br/>*Maximum length: 21* |
| `GFID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 36* |
| `GlobalID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 38* |
| `OBJECTID` | [`int64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STLength()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
