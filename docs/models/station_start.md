---
sidebar_position: 1
---

# StationStart

The S_Stn_Start table contains information about station starting locations.
These locations indicate the reference point that was used as the origin for
distance measurements along streams and rivers. This table is referenced by both
the L_XS_Elev table, which contains stream station information for cross
sections and the S_Riv_Mrk table, which contains river distance marker points.
Published as layer 13 of the NFHL MapServer, which also carries `GFID`,
`GlobalID`, `OBJECTID`; the reference does not define them, so they are optional
and validated only by type.

## Fields

| Name | Type | Description |
| -----: | :----: | ------------- |
| `id` | [`int64`](../system/numeric.md) (optional) | The service's OBJECTID, which ArcGIS's GeoJSON output writes as the feature id. It numbers rows in one copy of the service and identifies nothing beyond it; the reference's key is START_ID, assigned within one FIRM Database (one DFIRM_ID). |
| `bbox` | [`bbox`](../system/geometric.md) (optional) | An optional bounding box for the feature |
| `geometry` | [`geometry`](../system/geometric.md) | The station starting location: in the reference's words, the reference point that was used as the origin for distance measurements along streams and rivers.<br/><br/>*Allowed geometry types: Point* |
| `DFIRM_ID` | `string` | Flood Risk Project Identifier. For a single-jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code and the letter “C” (e.g., 48107C). Within each FIRM Database, the DFIRM_ID value will be identical.<br/><br/>*Maximum length: 6* |
| `VERSION_ID` | `string` | Version Identifier. Identifies the product version and relates the feature to standards according to how it was created.<br/><br/>*Maximum length: 11* |
| `START_ID` | `string` | Primary key for table lookup. Assigned by table creator. This field is the link that is used to reference station start descriptions in the FDTs and profiles and which links the S_Profil_Basln table, L_XS_Elev table via the S_XS table, and river marks in the S_Riv_Mrk table to the appropriate stationing starting point.<br/><br/>*Maximum length: 32* |
| `START_DESC` | `string` | Start Description. The description of the location of the station starting point. This should include the measurement units. For example, “Distances are measured in feet upstream from the confluence with the Main Channel of the Big River.”<br/><br/>*Maximum length: 254* |
| `LOC_ACC` | [`LocAccuracy`](types/loc_accuracy.md) | Start Station Locational Accuracy. The spatial placement accuracy level of the Station Start point. For all new models with profile baselines, the exact location of the profile baseline station start should be placed and the locational accuracy be categorized as “HIGH.” For old models where the profile baseline and station start are documented on work maps, the locational accuracy is “MEDIUM.” For areas that only have a text description, the point shall be placed as best possible, and the locational accuracy will be attributed as “LOW.” The acceptable values for this field can be found in the D_Loc_Accuracy table. |
| `SOURCE_CIT` | `string` | Source Citation. Abbreviation used in the metadata file when describing the source information for the feature. The abbreviation must match a value in L_Source_Cit.<br/><br/>*Maximum length: 21* |
| `GFID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 36* |
| `GlobalID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 38* |
| `OBJECTID` | [`int64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
