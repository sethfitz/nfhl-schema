---
sidebar_position: 1
---

# FirmPanel

The S_FIRM_Pan table contains information about the FIRM panel area. A spatial
file with location information also corresponds with this data table. The
spatial entities representing FIRM panels are polygons. The polygon for the FIRM
panel corresponds to the panel neatlines. FIRM panels must not overlap or have
gaps within a study. In situations where a portion of a panel lies outside the
jurisdiction being mapped, the user must refer to the S_Pol_Ar table to
determine the portion of the panel area where the FIRM Database shows the
effective flood hazard data for the mapped jurisdiction. This information is
needed for the FIRM Panel Index, and the following tables in the FIS Report:
Listing of NFIP Jurisdictions, Levees, and Incorporated Letters of Map Change.
Published as layer 3 of the NFHL MapServer, which also carries `GFID`,
`GlobalID`, `OBJECTID`, `SHAPE.STArea()`, `SHAPE.STLength()`; the reference does
not define them, so they are optional and validated only by type.

## Fields

| Name | Type | Description |
| -----: | :----: | ------------- |
| `id` | [`int64`](../system/numeric.md) (optional) | The service's OBJECTID, which ArcGIS's GeoJSON output writes as the feature id. It numbers rows in one copy of the service and identifies nothing beyond it; the reference's key is FIRM_ID, assigned within one FIRM Database (one DFIRM_ID). |
| `bbox` | [`bbox`](../system/geometric.md) (optional) | An optional bounding box for the feature |
| `geometry` | [`geometry`](../system/geometric.md) | The FIRM panel: in the reference's words, the area of a hardcopy map panel, a polygon that corresponds to the panel neatlines.<br/><br/>*Allowed geometry types: MultiPolygon, Polygon* |
| `DFIRM_ID` | `string` | Study Identifier. For a single-jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code and the letter “C” (e.g., 48107C). Within each FIRM Database, the DFIRM_ID value will be identical.<br/><br/>*Maximum length: 6* |
| `VERSION_ID` | `string` | Version Identifier. Identifies the product version and relates the feature to standards according to how it was created.<br/><br/>*Maximum length: 11* |
| `FIRM_ID` | `string` | Primary key for table lookup. Assigned by table creator.<br/><br/>*Maximum length: 32* |
| `ST_FIPS` | [`StateFIPS`](types/state_fips.md) | State FIPS. This is the two-digit code that corresponds to the State Federal Information Processing Standard (FIPS) code. This is a standard numbering system used by the Federal government, defined in FIPS Pub 6-4. These two numbers correspond to the first two digits of the panel number. Acceptable values for this field are listed in the D_State_FIPS table. |
| `PCOMM` | `string` | Community or County Identification Number. This is the third through the sixth digits of the panel number. For community-based maps this corresponds to the FEMA Community Identification number. For countywide maps this is the county (or county equivalent) FIPS code with a “C.”<br/><br/>*Maximum length: 4* |
| `PANEL` | `string` | Panel Number. This is seventh through the 10th digits in the complete panel number. This is assigned by the scale of the map and the position within the community or county. The panel number scheme is described in detail in the FIRM Panel Technical Reference.<br/><br/>*Maximum length: 4* |
| `SUFFIX` | `string` | Map Suffix. This is the final digit in the complete panel number. This is a letter suffix at the end of the panel number. The map suffix is incremented one letter every time the panel gets republished.<br/><br/>*Maximum length: 1* |
| `FIRM_PAN` | `string` | FIRM Panel Number. This is the complete 11-digit FIRM panel number, which is made up of ST_FIPS, PCOMM, PANEL and SUFFIX. This is the FIRM panel number that is shown in the title block of the map.<br/><br/>*Maximum length: 11* |
| `PANEL_TYP` | [`PanelTyp`](types/panel_typ.md) | Panel Type. The type of FIRM panel identifies whether the panel is printed or not and whether it is community based or countywide. Acceptable values for this field are listed in the D_Panel_Typ table. |
| `PRE_DATE` | [`int64`](../system/numeric.md) (optional) | Preliminary Release Date. This is the preliminary release date of the current map revision. This field is not populated until the FIRM preliminary release date is established and the Prelim FIRM is ready for hardcopy production by the Mapping Partner. Then it is required. |
| `EFF_DATE` | [`int64`](../system/numeric.md) (optional) | Effective Date. This is the effective date of the current map revision. This field is not populated until the FIRM effective date is established and the Final FIRM is ready for hardcopy production by FEMA. Then it is required. |
| `SCALE` | [`Scale`](types/scale.md) | Map Scale. This is the denominator of the FIRM scale as a ratio. For example, 24000 is the denominator for a 1″ = 2000′ map. Acceptable values for this field are listed in the D_Scale table. |
| `PNP_REASON` | `string` (optional) | Panel Not Printed Reason. This is the explanation for the FIRM panels that are not printed. Only completed if the hardcopy panel is not printed by FEMA. For example, “No Special Flood Hazard Areas.” See the FIS Report Technical Reference for commonly used values.<br/><br/>*Maximum length: 254* |
| `BASE_TYP` | [`BasemapTyp`](types/basemap_typ.md) | Base map type. The type of base map used for the FIRM panel shall be recorded in this field. Acceptable values for this field are listed in the D_Basemap_Typ table. |
| `SOURCE_CIT` | `string` | Source Citation. Abbreviation used in the metadata file when describing the source information for the feature. The abbreviation must match a value in L_Source_Cit.<br/><br/>*Maximum length: 21* |
| `GFID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 36* |
| `GlobalID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 38* |
| `OBJECTID` | [`int64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STArea()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STLength()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |

## Constraints

- `pnp_reason` is forbidden when panel_typ is not Countywide, Not Printed, Community Based, Not Printed or Statewide, Not Printed
