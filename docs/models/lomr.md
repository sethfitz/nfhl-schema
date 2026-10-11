---
sidebar_position: 1
---

# Lomr

The S_LOMR layer includes all LOMRs that have been incorporated into the NFHL
database. The S_LOMR feature class should contain at least one record for each
LOMR incorporated into the NFHL. Multipart polygons are not allowed. The spatial
entities representing LOMRs are polygons. The spatial information contains the
bounding polygon for each LOMR area, broken on panel boundaries. Published as
layer 1 of the NFHL MapServer, which also carries `GFID`, `GlobalID`,
`OBJECTID`, `SHAPE.STArea()`, `SHAPE.STLength()`; the reference does not define
them, so they are optional and validated only by type.

## Fields

| Name | Type | Description |
| -----: | :----: | ------------- |
| `id` | [`int64`](../system/numeric.md) (optional) | The service's OBJECTID, which ArcGIS's GeoJSON output writes as the feature id. It numbers rows in one copy of the service and identifies nothing beyond it; the reference's key is LOMR_ID, assigned within one FIRM Database (one DFIRM_ID). |
| `bbox` | [`bbox`](../system/geometric.md) (optional) | An optional bounding box for the feature |
| `geometry` | [`geometry`](../system/geometric.md) | The LOMR area: in the reference's words, the bounding polygon for each LOMR area, broken on panel boundaries.<br/><br/>*Allowed geometry types: Polygon* |
| `DFIRM_ID` | `string` | Study Identifier. For a single-jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code and the letter “C” (e.g., 48107C). Within each FIRM Database, the DFIRM_ID value will be identical.<br/><br/>*Maximum length: 6* |
| `VERSION_ID` | `string` | Version Identifier. Identifies the product version and relates the feature to standards according to how it was created.<br/><br/>*Maximum length: 11* |
| `LOMR_ID` | `string` | Primary key for table lookup. Assigned by table creator.<br/><br/>*Maximum length: 32* |
| `EFF_DATE` | [`int64`](../system/numeric.md) | Effective Date. Effective date of the LOMR. |
| `CASE_NO` | `string` | Case Number. This is the case number of the LOMR that is assigned by FEMA. The case number is used to track the LOMR’s supporting documentation. Hyphens are included (e.g., 11-03-0036P).<br/><br/>*Maximum length: 13* |
| `SCALE` | [`Scale`](types/scale.md) | Map Scale. This is the denominator of the effective LOMR scale as a ratio. For example, 24000 is the denominator for a 1″ = 2000′ map. Acceptable values for this field are listed in the D_Scale table. |
| `STATUS` | [`LOMCStatus`](types/lomc_status.md) | Status of the LOMR. Acceptable values for this field are listed in the D_LOMC_Status table. |
| `SOURCE_CIT` | `string` | Source Citation. Abbreviation used in the metadata file when describing the source information for the feature. The abbreviation must match a value in L_Source_Cit.<br/><br/>*Maximum length: 21* |
| `GFID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 36* |
| `GlobalID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 38* |
| `OBJECTID` | [`int64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STArea()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STLength()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
