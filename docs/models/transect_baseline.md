---
sidebar_position: 1
---

# TransectBaseline

The S_Tsct_Basln spatial file contains information about the transect baseline
used in the coastal flood hazard model. Typically, the S_Tsct_Basln represents
the 0.0-foot elevation contour, the starting point for the transect and the
measuring point for the coastal mapping. The spatial elements representing the
transect baselines are lines. The file describes the transect baseline profile
setting and must also include a reference to the vertical datum. When a coastal
transect baseline and water lines are available for the same study reach, only
the transect baseline shall be shown on the FIRM in order to eliminate overlaps.
This information is used in the following tables in the FIS Report: Transect
Locator Map, as well as in the Flooding Sources Included this FIS Report,
Summary of Coastal Analyses, Summary of Topographic Elevation Data Used in
Mapping and Coastal Transect Parameters. The spatial entities representing the
transect baselines are lines. Published as layer 18 of the NFHL MapServer, which
also carries `GFID`, `GlobalID`, `OBJECTID`, `SHAPE.STLength()`; the reference
does not define them, so they are optional and validated only by type.

## Fields

| Name | Type | Description |
| -----: | :----: | ------------- |
| `id` | [`int64`](../system/numeric.md) (optional) | The service's OBJECTID, which ArcGIS's GeoJSON output writes as the feature id. It numbers rows in one copy of the service and identifies nothing beyond it; the reference's key is TBASELN_ID, assigned within one FIRM Database (one DFIRM_ID). |
| `bbox` | [`bbox`](../system/geometric.md) (optional) | An optional bounding box for the feature |
| `geometry` | [`geometry`](../system/geometric.md) | The transect baseline: in the reference's words, the transect baseline used in the coastal flood hazard model, typically the 0.0-foot elevation contour, the starting point for the transect and the measuring point for the coastal mapping.<br/><br/>*Allowed geometry types: LineString* |
| `DFIRM_ID` | `string` | Study Identifier. For a single-jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code and the letter “C” (e.g., 48107C). Within each FIRM Database, the DFIRM_ID value will be identical.<br/><br/>*Maximum length: 6* |
| `VERSION_ID` | `string` | Version Identifier. Identifies the product version and relates the feature to standards according to how it was created.<br/><br/>*Maximum length: 11* |
| `TBASELN_ID` | `string` | Primary key for table lookup. Assigned by table creator.<br/><br/>*Maximum length: 32* |
| `CST_MDL_ID` | `string` (optional) | Coastal Model Identification. This field is the foreign key to the L_Cst_Model table. Multiple transects may link to a single record in the L_Cst_Model table. This field is populated for new coastal studies. This field is also populated for coastal redelineations and digital conversions when the data are available.<br/><br/>*Maximum length: 32* |
| `TBASE_TYP` | [`TsctBaslnTyp`](types/tsct_basln_typ.md) | Transect Baseline Type. This is the type of source data for the transect baseline. This value describes the criteria used in determining the transect baseline in coastal flood hazard models. Acceptable values for this field are listed in the D_TsctBasln_Typ table. |
| `R_ST_DESC` | `string` | Reach Name Start Description. This describes the location of the start of the Flood Risk Project reach.<br/><br/>*Maximum length: 254* |
| `R_END_DESC` | `string` | Reach Name End Description. This describes the location of the end of the Flood Risk Project reach.<br/><br/>*Maximum length: 254* |
| `V_DATUM` | [`VDatum`](types/v_datum.md) | Vertical Datum. The vertical datum indicates the reference surface from which the 0.0-foot contour is measured. Normally, this would be NAVD88. Acceptable values for this field are listed in the D_V_Datum table. |
| `WTR_NM` | `string` | Surface Water Feature Name. This is the formal name of the coastal water feature as it will appear on the hardcopy FIRM.<br/><br/>*Maximum length: 100* |
| `SOURCE_CIT` | `string` | Source Citation. Abbreviation used in the metadata file when describing the source information for the feature. The abbreviation must match a value in L_Source_Cit.<br/><br/>*Maximum length: 21* |
| `GFID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 36* |
| `GlobalID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 38* |
| `OBJECTID` | [`int64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STLength()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
