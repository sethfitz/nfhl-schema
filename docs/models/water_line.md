---
sidebar_position: 1
---

# WaterLine

The S_Wtr_Ln table contains information about surface water linear features. A
spatial file with location information also corresponds with this data table.
The spatial elements representing surface water line features are lines. Surface
water features may appear in either the S_Wtr_Ar table or the S_Wtr_Ln table or
both. However, features that appear in both must match exactly. The hydrologic
structure of the modeled stream network will be represented by the
S_Profil_Basln layer. This information is used in the Transect Locator Map and
the FIRM Panel Index in the FIS Report, as well as the FIRM panels. Published as
layer 20 of the NFHL MapServer, which also carries `GFID`, `GlobalID`,
`OBJECTID`, `SHAPE.STLength()`; the reference does not define them, so they are
optional and validated only by type.

## Fields

| Name | Type | Description |
| -----: | :----: | ------------- |
| `id` | [`int64`](../system/numeric.md) (optional) | The service's OBJECTID, which ArcGIS's GeoJSON output writes as the feature id. It numbers rows in one copy of the service and identifies nothing beyond it; the reference's key is WTR_LN_ID, assigned within one FIRM Database (one DFIRM_ID). |
| `bbox` | [`bbox`](../system/geometric.md) (optional) | An optional bounding box for the feature |
| `geometry` | [`geometry`](../system/geometric.md) | The water line: in the reference's words, a surface water linear feature (a stream, as a line) that appears on the FIRM.<br/><br/>*Allowed geometry types: LineString* |
| `DFIRM_ID` | `string` | Study Identifier. For a single-jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code and the letter “C” (e.g., 48107C). Within each FIRM Database, the DFIRM_ID value will be identical.<br/><br/>*Maximum length: 6* |
| `VERSION_ID` | `string` | Version Identifier. Identifies the product version and relates the feature to standards according to how it was created.<br/><br/>*Maximum length: 11* |
| `WTR_LN_ID` | `string` | Primary key for table lookup. Assigned by table creator.<br/><br/>*Maximum length: 32* |
| `WTR_NM` | `string` | Surface Water Feature Name. This is the formal name of the surface water feature, as it will appear on the hardcopy FIRM.<br/><br/>*Maximum length: 100* |
| `SHOWN_FIRM` | [`TrueFalse`](types/true_false.md) (optional) | Shown on FIRM. If the water feature is shown on the FIRM, this field would be True. Water features that obscure a profile baseline feature for the same reach should be attributed as False. Used for cartographic representation. Acceptable values for this field are listed in D_TrueFalse. |
| `SHOWN_INDX` | [`TrueFalse`](types/true_false.md) (optional) | Shown on Index Map. If the water feature is shown on the Index Map, this field would be True. Due to the scale of the Index Map format, lower order and overly detailed water features would be attributed as False to avoid clutter on the map. Used for cartographic representation. Acceptable values for this field are listed in D_TrueFalse. |
| `SOURCE_CIT` | `string` | Source Citation. Abbreviation used in the metadata file when describing the source information for the feature. The abbreviation must match a value in L_Source_Cit.<br/><br/>*Maximum length: 21* |
| `GFID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 36* |
| `GlobalID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 38* |
| `OBJECTID` | [`int64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STLength()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
