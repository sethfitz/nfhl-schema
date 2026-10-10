---
sidebar_position: 1
---

# RiverMark

The S_Riv_Mrk table contains information about the river marks shown on the FIRM
if applicable. A spatial file with location information also corresponds with
this data table. The spatial entities representing the river marks are points.
The points are generally located along the centerline of the river at regular
intervals or as indicated by the data source. Published as layer 7 of the NFHL
MapServer, which also carries `GFID`, `GlobalID`, `OBJECTID`; the reference does
not define them, so they are optional and validated only by type.

## Fields

| Name | Type | Description |
| -----: | :----: | ------------- |
| `id` | [`int64`](../system/numeric.md) (optional) | The service's OBJECTID, which ArcGIS's GeoJSON output writes as the feature id. It numbers rows in one copy of the service and identifies nothing beyond it; the reference's key is RIV_MRK_ID, assigned within one FIRM Database (one DFIRM_ID). |
| `bbox` | [`bbox`](../system/geometric.md) (optional) | An optional bounding box for the feature |
| `geometry` | [`geometry`](../system/geometric.md) | The river mark: in the reference's words, a point generally located along the centerline of the river at regular intervals or as indicated by the data source.<br/><br/>*Allowed geometry types: Point* |
| `DFIRM_ID` | `string` | Study Identifier. For a single-jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code and the letter “C” (e.g., 48107C). Within each FIRM Database, the DFIRM_ID value will be identical.<br/><br/>*Maximum length: 6* |
| `VERSION_ID` | `string` | Version Identifier. Identifies the product version and relates the feature to standards according to how it was created.<br/><br/>*Maximum length: 11* |
| `RIV_MRK_ID` | `string` | Primary key for table lookup. Assigned by table creator.<br/><br/>*Maximum length: 32* |
| `START_ID` | `string` | Station Start Identification. This is the foreign key to the S_Stn_Start layer. A code that provides a link to a point in the S_Stn_Start table at which the river mark distances start.<br/><br/>*Maximum length: 32* |
| `RIV_MRK_NO` | `string` | River Mark Number. This attribute usually represents the distance from a known point (identified by START_ID), such as the confluence with another river, to the current river mark. This is the value shown next to the river mark on the FIRM.<br/><br/>*Maximum length: 6* |
| `SOURCE_CIT` | `string` | Source Citation. Abbreviation used in the metadata file when describing the source information for the feature. The abbreviation must match a value in L_Source_Cit.<br/><br/>*Maximum length: 21* |
| `GFID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 36* |
| `GlobalID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 38* |
| `OBJECTID` | [`int64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
