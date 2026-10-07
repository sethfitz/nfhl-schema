---
sidebar_position: 1
---

# BaseFloodElevation

The S_BFE contains information about the BFEs within a Flood Risk Project area.
A spatial file with location information also corresponds with this data table.
The spatial elements representing BFE features are lines extending from Special
Flood Hazard Area (SFHA) boundary to SFHA boundary. The ends of the BFE lines
must be snapped precisely to the SFHA boundary. Each BFE is represented by a
single line with no pseudo-nodes. Where BFE lines are shown, they must be
consistent with procedures described in the FIRM Panel Technical Reference.
Published as layer 16 of the NFHL MapServer, which also carries `GFID`,
`GlobalID`, `OBJECTID`, `SHAPE.STLength()`; the reference does not define them,
so they are optional and validated only by type.

## Fields

| Name | Type | Description |
| -----: | :----: | ------------- |
| `id` | [`int64`](../system/numeric.md) (optional) | The service's OBJECTID, which ArcGIS's GeoJSON output writes as the feature id. It numbers rows in one copy of the service and identifies nothing beyond it; the reference's key is BFE_LN_ID, assigned within one FIRM Database (one DFIRM_ID). |
| `bbox` | [`bbox`](../system/geometric.md) (optional) | An optional bounding box for the feature |
| `geometry` | [`geometry`](../system/geometric.md) | The BFE line: in the reference's words, a single line extending from Special Flood Hazard Area (SFHA) boundary to SFHA boundary.<br/><br/>*Allowed geometry types: LineString* |
| `DFIRM_ID` | `string` | Study Identifier. For a single-jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code, and the letter “C” (e.g., 48107C). Within each FIRM Database, the DFIRM_ID value will be identical.<br/><br/>*Maximum length: 6* |
| `VERSION_ID` | `string` | Version Identifier. Identifies the product version and relates the feature to standards according to how it was created.<br/><br/>*Maximum length: 11* |
| `BFE_LN_ID` | `string` | Primary key for table lookup. Assigned by table creator.<br/><br/>*Maximum length: 32* |
| `ELEV` | [`float64`](../system/numeric.md) | The rounded, whole-foot elevation of the 1% annual-chance flood. This is the value of the BFE that is printed next to the BFE line on the FIRM.<br/><br/>*`unit given by LEN_UNIT`*<br/>*`vertical datum given by V_DATUM`* |
| `LEN_UNIT` | [`LengthUnits`](types/length_units.md) | BFE Units. This unit indicates the measurement system used for the BFEs. Normally this would be feet. Acceptable values for this field are listed in the D_Length_Units table. |
| `V_DATUM` | [`VDatum`](types/v_datum.md) | Vertical Datum. The vertical datum indicates the reference surface from which the flood elevations are measured. Normally this would be North American Vertical Datum of 1988 for new studies. Acceptable values for this field are listed in the D_V_Datum table. |
| `SOURCE_CIT` | `string` | Source Citation. Abbreviation used in the metadata file when describing the source information for the feature. The abbreviation must match a value in L_Source_Cit.<br/><br/>*Maximum length: 21* |
| `GFID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 36* |
| `GlobalID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 38* |
| `OBJECTID` | [`int64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STLength()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
