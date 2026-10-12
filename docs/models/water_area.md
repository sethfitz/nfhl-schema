---
sidebar_position: 1
---

# WaterArea

The S_Wtr_Ar table contains information about surface water area features. A
spatial file with location information also corresponds with this data table.
The spatial elements representing surface water area features are polygons. This
information is used in the Transect Locator Map and the FIRM Panel Index in the
FIS Report, as well as the FIRM panels. Published as layer 32 of the NFHL
MapServer, which also carries `GFID`, `GlobalID`, `OBJECTID`, `SHAPE.STArea()`,
`SHAPE.STLength()`; the reference does not define them, so they are optional and
validated only by type.

## Fields

| Name | Type | Description |
| -----: | :----: | ------------- |
| `id` | [`int64`](../system/numeric.md) (optional) | The service's OBJECTID, which ArcGIS's GeoJSON output writes as the feature id. It numbers rows in one copy of the service and identifies nothing beyond it; the reference's key is WTR_AR_ID, assigned within one FIRM Database (one DFIRM_ID). |
| `bbox` | [`bbox`](../system/geometric.md) (optional) | An optional bounding box for the feature |
| `geometry` | [`geometry`](../system/geometric.md) | The water area: in the reference's words, a surface water area feature (a hydrography feature shown on the FIRM as an area).<br/><br/>*Allowed geometry types: MultiPolygon, Polygon* |
| `DFIRM_ID` | `string` | Study Identifier. For a single-jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code and the letter “C” (e.g., 48107C). Within each FIRM Database, the DFIRM_ID value will be identical.<br/><br/>*Maximum length: 6* |
| `VERSION_ID` | `string` | Version Identifier. Identifies the product version and relates the feature to standards according to how it was created.<br/><br/>*Maximum length: 11* |
| `WTR_AR_ID` | `string` | Primary key for table lookup. Assigned by table creator.<br/><br/>*Maximum length: 32* |
| `WTR_NM` | `string` | Surface Water Feature Name. This is the formal name of the surface water feature, as it will appear on the hardcopy FIRM. This field is populated when the water feature name is known and shown on the FIRM. Unnamed bodies of water follow the convention shown in Section 5.3 related to null text values.<br/><br/>*Maximum length: 100* |
| `SHOWN_FIRM` | [`TrueFalse`](types/true_false.md) (optional) | Shown on FIRM. If the water feature is shown on the FIRM, this field would be True. Water features that obscure a profile baseline feature for the same reach should be attributed as False. Used for cartographic representation. Acceptable values for this field are listed in D_TrueFalse. |
| `SHOWN_INDX` | [`TrueFalse`](types/true_false.md) (optional) | Shown on Index Map. If the water feature is shown on the Index Map, this field would be True. Due to the scale of the Index Map format, lower order and overly detailed water features would be attributed as False to avoid clutter on the map. Used for cartographic representation. Acceptable values for this field are listed in D_TrueFalse. |
| `SOURCE_CIT` | `string` | Source Citation. Abbreviation used in the metadata file when describing the source information for the feature. The abbreviation must match a value in L_Source_Cit.<br/><br/>*Maximum length: 21* |
| `GFID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 36* |
| `GlobalID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 38* |
| `OBJECTID` | [`int64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STArea()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STLength()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
