# LengthUnits

Values of `D_Length_Units` that apply to the FIRM Database, each as the data
stores it. Used by `S_Fld_Haz_Ar.LEN_UNIT`, `S_BFE.LEN_UNIT`, `S_XS.LEN_UNIT`,
`S_Profil_Basln.DATUM_UNIT`, `S_Levee.LEN_UNIT`, `S_Cst_Tsct_Ln.FTCHLNUNIT`,
`S_Cst_Tsct_Ln.ELEV_UNIT`, `S_Cst_Tsct_Ln.LEN_UNIT`. The last is a legacy value:
common in the data, not in the reference.

## Values

- `Centimeters` - Code `CM`.
- `Feet` - Code `FT`.
- `Inches` - Code `IN`.
- `Kilometers` - Code `KM`.
- `Meters` - Code `M`.
- `Miles` - Code `MI`.
- `Millimeters` - Code `MM`.
- `U.S. Survey Feet` - Code `USFT`.
- `NP` - Code `NP`.
- `NA` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. `NA` where D_Length_Units lists `NP` for a field not populated. The same 28 coastal transects hold it in LEN_UNIT and TIME_UNIT, all in one DFIRM, 26099C. `NA` where D_Length_Units lists `NP` for a field not populated. The same 28 coastal transects hold it in FTCHLNUNIT and TIME_UNIT, all in one DFIRM, 26099C. Held by 28 of 22,367 rows of `FTCHLNUNIT` on NFHL service layer 15, counted 2026-10-13; and by 28 of 22,367 rows of `LEN_UNIT` on NFHL service layer 15, counted 2026-10-13.

## Used By

- [`BaseFloodElevation`](../base_flood_elevation.md)
- [`CoastalTransect`](../coastal_transect.md)
- [`CrossSection`](../cross_section.md)
- [`FloodHazardZone`](../flood_hazard_zone.md)
- [`Levee`](../levee.md)
- [`ProfileBaseline`](../profile_baseline.md)
