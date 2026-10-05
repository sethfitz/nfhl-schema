# StudyTyp

Values of `D_Study_Typ` that apply to the FIRM Database, each as the data stores
it. Used by `S_Fld_Haz_Ar.STUDY_TYP`. The last 7 are legacy values: common in
the data, not in the reference.

## Values

- `BLE available but unpublished` - Base Level Engineering data are available, but zones and Baseflood Elevations (BFEs) are not published on FIRM. Code `1030`.
- `SFHA without BFE` - Such as A zones without BFEs or water surface elevations. Code `1000`.
- `SFHA with unpublished BFE` - Such as A zones with BFEs or water surface elevations calculated but not published in FIS Report. Code `1040`.
- `SFHA with BFE published only in FIS` - Such as A zones with BFEs or water surface elevations published only in FIS Report. Code `1010`.
- `SFHA with BFE no floodway` - Such as AE or VE zones with regulatory water surface elevations or depths but no floodway; or shaded-X zones that are associated with this type of study. Code `1050`.
- `SFHA with BFE and floodway` - Such as AE or VE zones with regulatory water surface elevations and a regulatory floodway; or shaded-X zones that are associated with this type of study. Code `1060`.
- `Shaded Zone X with depths less than 1’` - Such as Zone X with depths less than 1’. Code `1070`.
- `NP` - NP; unshaded-X zones. Code `NP`.
- `SFHAs WITH LOW FLOOD RISK` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. One of three study types graded by flood risk (LOW, MEDIUM, HIGH) that the 2024 reference does not list. Which edition defined them is unverified. Held by 979,594 of 5,810,832 rows of `STUDY_TYP` on NFHL service layer 28, counted 2026-10-05.
- `SFHAs WITH HIGH FLOOD RISK` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. One of three study types graded by flood risk (LOW, MEDIUM, HIGH) that the 2024 reference does not list. Which edition defined them is unverified. Held by 557,235 of 5,810,832 rows of `STUDY_TYP` on NFHL service layer 28, counted 2026-10-05.
- `SFHAs WITH MEDIUM FLOOD RISK` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. One of three study types graded by flood risk (LOW, MEDIUM, HIGH) that the 2024 reference does not list. Which edition defined them is unverified. Held by 193,351 of 5,810,832 rows of `STUDY_TYP` on NFHL service layer 28, counted 2026-10-05.
- `REDELINEATION` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. A study type naming how the map was made, which the 2024 reference does not list. Which edition defined it is unverified. Held by 72,844 of 5,810,832 rows of `STUDY_TYP` on NFHL service layer 28, counted 2026-10-05.
- `Shaded Zone X with depths less than 1'` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. The reference's code 1070, `Shaded Zone X with depths less than 1’`, written with an ASCII apostrophe where the reference prints a typographic one. More rows hold this form (33,992) than the reference's (10,645). Held by 33,992 of 5,810,832 rows of `STUDY_TYP` on NFHL service layer 28, counted 2026-10-05.
- `DIGITAL CONVERSION` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. A study type naming how the map was made, which the 2024 reference does not list. Which edition defined it is unverified. Held by 12,946 of 5,810,832 rows of `STUDY_TYP` on NFHL service layer 28, counted 2026-10-05.
- `Special Flood Hazard Area (SFHA) witho` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. Cut off at the field's 38 characters. The full value is not recoverable from the data, and the 2024 reference has no study type that begins this way. Held by 6,493 of 5,810,832 rows of `STUDY_TYP` on NFHL service layer 28, counted 2026-10-05.

## Used By

- [`FloodHazardZone`](../flood_hazard_zone.md)
