---
sidebar_position: 1
---

# CrossSection

The S_XS table contains information about cross section lines. This information
is used in the Floodway Data Tables in the FIS Report, as well as on the FIRM
panels. Database attributes should reflect the final regulatory water surface
elevations that include any backwater elevations regardless of flood hazard zone
and should be consistent with values in the floodway data tables and flood
profiles, where applicable. All cross sections – modeled or interpolated – must
be stored in the S_XS, regardless of whether or not they are shown on the FIRM
and regardless of the flood hazard zone ultimately depicted on the effective
panels. Refer to the Guidance Document No. 31, Guidance for Flood Risk Analysis
and Mapping: Mapping Base Flood Elevations on Flood Insurance Rate Maps for
additional information about BFE and cross section placement and labeling
elevation values on the FIRM panels. The spatial entities representing cross
sections are lines. Published as layer 14 of the NFHL MapServer, which also
carries `GFID`, `GlobalID`, `OBJECTID`, `SHAPE.STLength()`; the reference does
not define them, so they are optional and validated only by type.

## Fields

| Name | Type | Description |
| -----: | :----: | ------------- |
| `id` | [`int64`](../system/numeric.md) (optional) | The service's OBJECTID, which ArcGIS's GeoJSON output writes as the feature id. It numbers rows in one copy of the service and identifies nothing beyond it; the reference's key is XS_LN_ID, assigned within one FIRM Database (one DFIRM_ID). |
| `bbox` | [`bbox`](../system/geometric.md) (optional) | An optional bounding box for the feature |
| `geometry` | [`geometry`](../system/geometric.md) | The cross section line: in the reference's words, the spatial entities representing cross sections are lines.<br/><br/>*Allowed geometry types: LineString* |
| `DFIRM_ID` | `string` | Study Identifier. For a single-jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code and the letter “C” (e.g., 48107C). Within each FIRM Database, the DFIRM_ID value will be identical.<br/><br/>*Maximum length: 6* |
| `VERSION_ID` | `string` | Version Identifier. Identifies the product version and relates the feature to standards according to how it was created.<br/><br/>*Maximum length: 11* |
| `XS_LN_ID` | `string` | Primary key for table lookup. Assigned by table creator.<br/><br/>*Maximum length: 32* |
| `WTR_NM` | `string` | Surface Water Feature Name. This is the name of the stream or water body.<br/><br/>*Maximum length: 100* |
| `STREAM_STN` | [`float64`](../system/numeric.md) (optional) | Stream Station. This is the measurement along the profile baseline to the cross section location. This value is used in the FDTs and profiles. Required in the reference, with the footnote "Field is applicable for BLE database." |
| `START_ID` | `string` (optional) | Station Start Identification. This is the foreign key to the S_Stn_Start layer. The station start describes the origin for the measurements in the STREAM_STN field. This value is used in the FDTs and profiles. Required in the reference, with the footnote "Field is applicable for BLE database."<br/><br/>*Maximum length: 32* |
| `XS_LTR` | `string` (optional) | Cross Section Letter. This is the letter or number that is assigned to the cross section on the hardcopy FIRM and in the FIS Report. This field is populated when the cross section is lettered.<br/><br/>*Maximum length: 12* |
| `XS_LN_TYP` | [`XSLnTyp`](types/xs_ln_typ.md) (optional) | Cross-Section Line Type. This attribute should contain ‘LETTERED, MAPPED’ for cross sections that are shown on the hardcopy FIRM and are given a letter. If the cross section will be shown on the FIRM but not lettered, the attribute should contain ‘NOT LETTERED, MAPPED’ to indicate that it is a cross section shown on the hardcopy FIRM, but not on the FDTs or profiles. If the cross section will not be shown on the hardcopy FIRM, this attribute should contain ‘NOT LETTERED, NOT MAPPED’ to indicate that the cross section is part of the backup data for the Flood Risk Project but is not shown on the FIRM. All cross sections used in the development of effective hydraulic models shall be stored in this table, regardless of the flood hazard zone depicted on the effective panels. Acceptable values for this field are listed in the D_XS_Ln_Typ table. Required in the reference, with the footnote "Field is applicable for BLE database." |
| `WSEL_REG` | [`float64`](../system/numeric.md) | Regulatory Water Surface Elevation for the 1% annual-chance Flood Event. This is the regulatory water-surface elevation for the 1% annual-chance flood event in the stream channel at this cross section, this should include backwater elevations. In the case of levee(s) associated with a cross section, it is assumed that the levee(s) holds. For cross sections in the coastal floodplain, this value should be coded “-8888”. For cross sections in the combined coastal and riverine floodplain, this value should reflect the results of the combined rate of occurrence analysis. For cross sections at confluences where a single water surface elevation cannot be determined this value should be coded as “-8888”. This field is stored here and in L_XS_Elev to simplify annotation of the FIRM panel water-surface elevation at this cross section. This value and the corresponding value in L_XS_Elev should match.<br/><br/>*`unit given by LEN_UNIT`*<br/>*`vertical datum given by V_DATUM`* |
| `STRMBED_EL` | [`float64`](../system/numeric.md) | Streambed Elevation. This is the water-surface elevation for the thalweg or the lowest point in the main channel. This value is used in the profiles.<br/><br/>*`unit given by LEN_UNIT`*<br/>*`vertical datum given by V_DATUM`* |
| `LEN_UNIT` | [`LengthUnits`](types/length_units.md) | Water-Surface and Streambed Elevation Units. This unit indicates the measurement system used for the water-surface and streambed elevations. Normally, this would be feet. Acceptable values for this field are listed in the D_Length_Units table. |
| `V_DATUM` | [`VDatum`](types/v_datum.md) | Vertical Datum. The vertical datum indicates the reference surface from which the flood and streambed elevations are measured. Normally, this would be NAVD88. Acceptable values for this field are listed in the D_V_Datum table. |
| `PROFXS_TXT` | `string` (optional) | Profile Cross Section Text. This field stores user-defined cross section text that is plotted on the profile. This field is only required to be populated if and when the data can be exported from RASPLOT in FIRM Database Technical Reference format.<br/><br/>*Maximum length: 80* |
| `MODEL_ID` | `string` | Model Identifier. This field stores the feature’s identifier that was used during hydrologic and hydraulic modeling. This field provides a link between the hydrologic or hydraulic modeling and this spatial file. This field should be populated with the name of the of the submitted model, Ex: River_Run.prj<br/><br/>*Maximum length: 107* |
| `SEQ` | [`int16`](../system/numeric.md) (optional) | Sequence. This is the order in which the cross sections plot on the profile. This value is needed for profiles. This field is only required if and when the data can be exported from RASPLOT in FIRM Database Technical Reference format. |
| `SOURCE_CIT` | `string` | Source Citation. Abbreviation used in the metadata file when describing the source information for the feature. The abbreviation must match a value in L_Source_Cit.<br/><br/>*Maximum length: 21* |
| `GFID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 36* |
| `GlobalID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 38* |
| `OBJECTID` | [`int64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STLength()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |

## Constraints

- `xs_ltr` is forbidden when xs_ln_typ is not LETTERED, MAPPED
