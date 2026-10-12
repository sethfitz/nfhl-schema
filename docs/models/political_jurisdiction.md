---
sidebar_position: 1
---

# PoliticalJurisdiction

The S_Pol_Ar table contains information about political areas within the Flood
Risk Project area. This includes the attributes for the political areas within
the Flood Risk Project and whether or not they have been studied or participate
in the National Flood Insurance Program (NFIP). The political jurisdiction
assigned to each area corresponds to the jurisdiction responsible for NFIP and
floodplain management for that area. This table is used in following FIS Report
components: the FIS Report cover, the FIRM panel index, the Panel Locator on the
FIRM panels, the Transect Locator Map and the following tables in the FIS
Report: Listing of NFIP Jurisdictions, Flooding Sources Included this FIS
Report, Flood Zone Designations by Community, Levees, Transect Locator Map,
Summary of Topographic Elevation Data Used in Mapping, Community Map History,
Summary of Contracted Studies Included in this FIS Report and Community
Meetings. The spatial entities representing political areas are polygons.
Published as layer 22 of the NFHL MapServer, which also carries `GFID`,
`GlobalID`, `OBJECTID`, `SHAPE.STArea()`, `SHAPE.STLength()`; the reference does
not define them, so they are optional and validated only by type.

## Fields

| Name | Type | Description |
| -----: | :----: | ------------- |
| `id` | [`int64`](../system/numeric.md) (optional) | The service's OBJECTID, which ArcGIS's GeoJSON output writes as the feature id. It numbers rows in one copy of the service and identifies nothing beyond it; the reference's key is POL_AR_ID, assigned within one FIRM Database (one DFIRM_ID). |
| `bbox` | [`bbox`](../system/geometric.md) (optional) | An optional bounding box for the feature |
| `geometry` | [`geometry`](../system/geometric.md) | The political area: in the reference's words, a political area within the Flood Risk Project area, assigned the jurisdiction responsible for NFIP and floodplain management for that area.<br/><br/>*Allowed geometry types: MultiPolygon, Polygon* |
| `DFIRM_ID` | `string` | Study Identifier. For a single-jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code and the letter “C” (e.g., 48107C). Within each FIRM Database, the DFIRM_ID value will be identical.<br/><br/>*Maximum length: 6* |
| `VERSION_ID` | `string` | Version Identifier. Identifies the product version and relates the feature to standards according to how it was created.<br/><br/>*Maximum length: 11* |
| `POL_AR_ID` | `string` | Primary key for table lookup. Assigned by table creator.<br/><br/>*Maximum length: 32* |
| `POL_NAME1` | `string` | Political Area Name 1. This is the name of the area with floodplain management jurisdiction, which must have a CID. For areas that have more than one name, this would be the primary name with subsequent names shown in field below. This corresponds to the official name of this jurisdiction used by FEMA in the NFIP. For unincorporated areas of a county, this must be the county name (e.g., Montgomery County).<br/><br/>*Maximum length: 50* |
| `POL_NAME2` | `string` (optional) | Political Area Name 2. This is the secondary name of the area shown populated if there is a common name for an area other than the official jurisdiction name. Location identifiers such as “Unincorporated Areas” or “Extrajurisdictional Areas” should be placed here.<br/><br/>*Maximum length: 50* |
| `POL_NAME3` | `string` (optional) | Political Area Name 3. This is the tertiary name of the area shown populated if there is a situation where islands, National Parks, National Forests, military bases or other area boundaries and labels need to be shown on the FIRM underneath the POL_NAME1 and POL_NAME2 labels.<br/><br/>*Maximum length: 50* |
| `CO_FIPS` | `string` | County Federal Information Processing Standard (FIPS) Code. This is the three-digit county FIPS code. This is a standard numbering system that is used by the federal government. Defined in FIPS Pub 6-4.<br/><br/>*Maximum length: 3* |
| `ST_FIPS` | [`StateFIPS`](types/state_fips.md) | State FIPS. This is the two-digit code that corresponds to the State FIPS code. This is a standard numbering system that is used by the Federal government defined in FIPS Pub 6-4. Acceptable values for this field are listed in the D_State_FIPS table. |
| `COMM_NO` | `string` | Community Number. This is the four-digit number assigned by FEMA to each community for tracking purposes under the NFIP. On newer FIRMs the State FIPS and the community number appear below the community name where it is shown in the body of the map. For single-jurisdiction FIRMs, this is the third through the sixth digits of the panel number. This number can be obtained from the Community Status Book at https://msc.fema.gov.<br/><br/>*Maximum length: 4* |
| `CID` | `string` | Community Identification Number. This is the six-digit community number assigned by FEMA. It is created by combining the State FIPS code with the COMM_NO. If the jurisdiction does not have a community number assigned by FEMA, the CID is created by combining the State FIPS code with the abbreviation contained in the COMM_NO field (FED, ST or OTHR).<br/><br/>*Maximum length: 6* |
| `ANI_TF` | [`TrueFalse`](types/true_false.md) | Area Not Included (ANI). This field contains information about the geographical area to determine whether or not it is included on the FIRM. Areas Not Included fall within the extent of the FIRM but no flood risk information is shown. This is either because the area is mapped on another FEMA map or because the area is not mapped at all by FEMA. Enter true when the area is not included in the FIRM. Acceptable values for this field are listed in the D_TrueFalse table. |
| `ANI_FIRM` | `string` (optional) | Used for ANI polygons where ANI_TF equals “T” and where the data are included in another FIRM Database, usually because it is a multicounty community. Enter the DFIRM_ID of the FIRM Database that contains the SFHA data of the ANI community. For a single-jurisdiction Flood Risk Project, the value is composed of the two-digit State FIPS code and the four-digit FEMA CID code (e.g., 480001). For a countywide Flood Risk Project, the value is composed of the two-digit State FIPS code, the three-digit county FIPS code and the letter “C” (e.g., 48107C). Populate with “NP” if the area has never been converted to a FIRM Database from paper FIRM format.<br/><br/>*Maximum length: 6* |
| `COM_NFO_ID` | `string` (optional) | Community Information Identification. Foreign key to L_Comm_Info table. This attribute links to the table L_Comm_Info that contains information about the specific community. This table must contain a number that matches a corresponding number in the COM_NFO_ID field of the L_Comm_Info table. This field is populated for any jurisdiction that has a CID number issued by FEMA.<br/><br/>*Maximum length: 32* |
| `SOURCE_CIT` | `string` | Source Citation. Abbreviation used in the metadata file when describing the source information for the feature. The abbreviation must match a value in L_Source_Cit.<br/><br/>*Maximum length: 21* |
| `GFID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 36* |
| `GlobalID` | `string` (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it.<br/><br/>*Maximum length: 38* |
| `OBJECTID` | [`int64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STArea()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |
| `SHAPE.STLength()` | [`float64`](../system/numeric.md) (optional) | Published by the NFHL map service as housekeeping for its own copy of the data; the FIRM Database reference does not define it. |

## Constraints

- `ani_firm` is forbidden when ani_tf is not T and ani_firm is not NP
