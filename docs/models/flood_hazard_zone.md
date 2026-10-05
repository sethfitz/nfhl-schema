---
sidebar_position: 1
---

# FloodHazardZone

This table is required for all FIRM Databases. The S_Fld_Haz_Ar table contains
information about the flood hazards within the Flood Risk Project area. A
spatial file with location information also corresponds with this data table.
These zones are used by FEMA to designate the Special Flood Hazard Area (SFHA).
These data are the regulatory flood zones designated by FEMA. This information
is needed for the following tables in the FIS Report: Flooding Sources Included
in this FIS Report and Summary of Hydrologic and Hydraulic Analyses. The spatial
elements representing the flood zones are polygons. The entire area of the
jurisdiction(s) mapped by the FIRM should have a corresponding flood zone
polygon. There is one polygon for each contiguous flood zone designated.
Published as layer 28 of the NFHL MapServer, which also carries `GFID`,
`GlobalID`, `OBJECTID`, `SHAPE.STArea()`, `SHAPE.STLength()`; the reference does
not define them, so they arrive as extra properties.

## Fields

| Name | Type | Description |
| -----: | :----: | ------------- |
| `id` | [`int64`](../system/numeric.md) (optional) | The service's OBJECTID, which ArcGIS's GeoJSON output writes as the feature id. It numbers rows in one copy of the service and identifies nothing beyond it; the reference's key is FLD_AR_ID, assigned within one FIRM Database (one DFIRM_ID). |
| `bbox` | [`bbox`](../system/geometric.md) (optional) | An optional bounding box for the feature |
| `geometry` | [`geometry`](../system/geometric.md) | Extent of the flood zone: in the reference's words, one polygon for each contiguous flood zone designated.<br/><br/>*Allowed geometry types: MultiPolygon, Polygon* |
| `DFIRM_ID` | `string` | Study Identifier. For a single jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code and the letter “C” (e.g., 48107C). Within each FIRM Database, the DFIRM_ID value will be identical.<br/><br/>*Maximum length: 6* |
| `VERSION_ID` | `string` (optional) | Version Identifier. Identifies the product version and relates the feature to standards according to how it was created.<br/><br/>*Maximum length: 11* |
| `FLD_AR_ID` | `string` | Primary key for table lookup. Assigned by table creator.<br/><br/>*Maximum length: 32* |
| `STUDY_TYP` | [`StudyTyp`](types/study_typ.md) | Study Type. This describes the type of Flood Risk Project performed for flood hazard identification. Acceptable values for this field are listed in the D_Study_Typ table. |
| `FLD_ZONE` | [`Zone`](types/zone.md) | Flood Zone. This is a flood zone designation. These zones are used by FEMA to designate the SFHAs. Acceptable values for this field are listed in the D_Zone table. |
| `ZONE_SUBTY` | [`ZoneSubtype`](types/zone_subtype.md) (optional) | Flood Zone Subtype. This field captures additional information about the flood zones. For example, Zone X could have “AREA WITH REDUCED FLOOD HAZARD DUE TO ACCREDITED LEVEE SYSTEM” or “0.2-PCT ANNUAL CHANCE FLOOD HAZARD” as a subtype. Types of floodways are also stored in this field. Floodways are designated by FEMA and adopted by communities to provide an area that will remain free of development to moderate increases in flood heights due to encroachment on the floodplain. Normal floodways are specified as ‘FLOODWAY.’ Special cases will have a more specific term for the designation (such as COLORADO RIVER) and will appear as a note on the hardcopy FIRM. See the FIRM Panel Technical Reference for available floodway notes. NOTE: The symbol ‘%’ is a reserved symbol in most software packages, so the word ‘percent’ was abbreviated to ‘PCT.’ Acceptable values for this field are listed in the D_Zone_Subtype table. |
| `SFHA_TF` | [`TrueFalse`](types/true_false.md) | Special Flood Hazard Area. If the area is within a SFHA this field would be true. This field will be true for any area coded as an A or V flood zone area. It should be false for any X or D flood areas. Acceptable values for this field are listed in the D_TrueFalse table. |
| `STATIC_BFE` | [`float64`](../system/numeric.md) (optional) | Static Base Flood Elevation. This field will be populated for areas that have been determined to have a constant Base Flood Elevation (BFE) over a flood zone. The BFE value will be shown beneath the zone label. In this situation the same BFE applies to the entire polygon. This normally occurs in lakes or coastal zones.<br/><br/>*`unit given by LEN_UNIT`*<br/>*`vertical datum given by V_DATUM`* |
| `V_DATUM` | [`VDatum`](types/v_datum.md) (optional) | Vertical Datum. The vertical datum indicates the reference surface from which the flood elevations are measured. Normally this would be North American Vertical Datum of 1988 for new studies. This field is only populated if the STATIC_BFE field is populated. Acceptable values for this field are listed in the D_V_Datum table. |
| `DEPTH` | [`float64`](../system/numeric.md) (optional) | Depth This is the depth for Zone AO areas. This value is shown beneath the zone label on the FIRM. This field is only populated if a depth is shown on the FIRM.<br/><br/>*`unit given by LEN_UNIT`* |
| `LEN_UNIT` | [`LengthUnits`](types/length_units.md) (optional) | Length Units. This unit indicates the measurement system used for the BFEs and/or depths. Normally this would be feet. This field is only populated if the STATIC_BFE or DEPTH field is populated. Acceptable values for this field are listed in the D_Length_Units table. |
| `VELOCITY` | [`float64`](../system/numeric.md) (optional) | Velocity. This is the velocity measurement of the flood flow in the area. Normally this is applicable to alluvial fan areas (certain Zone AO areas). This value is shown beneath the zone label on the FIRM. This field is only populated when a velocity is associated with the flood zone area.<br/><br/>*`unit given by VEL_UNIT`* |
| `VEL_UNIT` | [`VelocityUnits`](types/velocity_units.md) (optional) | Velocity Unit. This is the unit of measurement for the velocity. This field is populated when the VELOCITY field is populated. Acceptable values for this field are listed in the D_Velocity_Units table. |
| `AR_REVERT` | [`Zone`](types/zone.md) (optional) | Flood Control Restoration Zones – Zone AR Classification. If this area is Zone AR in FLD_Zone field, this field would hold the zone that area would revert to if the AR zone were removed. This field is only populated if the corresponding area is Zone AR. Acceptable values for this field are listed in the D_Zone table, but should only include one of AE, AO, AH, A, and X domain values. |
| `AR_SUBTRV` | [`ZoneSubtype`](types/zone_subtype.md) (optional) | Flood Control Restoration Zones – Zone AR Classification Zone Subtype. If this area is Zone AR in FLD_Zone field, this field would hold the zone subtype that area would revert to if the AR zone were removed. This field is only populated if the corresponding area is Zone AR. NOTE: The symbol ‘%’ is a reserved symbol in most software packages, so the word ‘percent’ was abbreviated to ‘PCT.’ Acceptable values for this field are listed in the D_Zone_Subtype_ table and must be one of the allowable subtypes for Zones AE, AO, AH, A or X. |
| `BFE_REVERT` | [`float64`](../system/numeric.md) (optional) | Flood Control Restoration Zones – BFE Revert. If zone is Zone AR in FLD_Zone field, this field would hold the static base flood elevation for the reverted zone. This field is populated when Zone equals AR and the reverted zone has a static BFE. |
| `DEP_REVERT` | [`float64`](../system/numeric.md) (optional) | Flood Control Restoration Zones – Depth Revert. If zone is Zone AR in FLD_Zone field, this field would hold the flood depth for the reverted zone. This field is populated when Zone equals AR and the reverted zone has a depth assigned. |
| `DUAL_ZONE` | [`TrueFalse`](types/true_false.md) (optional) | Flood Control Restoration Zones – Dual Zone Classification. If the flood hazard areas shown on the effective FIRM shall be designated as “dual” SFHAs (i.e., Zone AR/AE, Zone AR/AH, Zone AR/AO, Zone AR/A), this field will be coded as true. It should be false for any for AR Zones that revert to Shaded X. Acceptable values for this field are listed in the D_TrueFalse table. |
| `SOURCE_CIT` | `string` | Source Citation. Abbreviation used in the metadata file when describing the source information for the feature. The abbreviation must match a value in L_Source_Cit.<br/><br/>*Maximum length: 21* |

## Constraints

- `vel_unit` is required when velocity is populated
- `len_unit` is forbidden when static_bfe is not populated and depth is not populated
- `v_datum` is forbidden when static_bfe is not populated
