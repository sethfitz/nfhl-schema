# TrueFalse

Values of `D_TrueFalse` that apply to the FIRM Database, each as the data stores
it. Used by `S_Fld_Haz_Ar.SFHA_TF`, `S_Fld_Haz_Ar.DUAL_ZONE`,
`S_Profil_Basln.SHOWN_FIRM`, `S_Profil_Basln.SHOWN_INDX`, `S_Wtr_Ln.SHOWN_FIRM`,
`S_Wtr_Ln.SHOWN_INDX`, `S_Levee.USACE_LEV`, `S_Levee.PL84_99TF`,
`S_Pol_Ar.ANI_TF`, `S_Gen_Struct.SHOWN_FIRM`, `S_Wtr_Ar.SHOWN_FIRM`,
`S_Wtr_Ar.SHOWN_INDX`. The last is a legacy value: common in the data, not in
the reference.

## Values

- `T` - True (Yes). Code `T`.
- `F` - False (No). Code `F`.
- `U` - Unknown. Code `U`.
- `1` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. A digit where D_TrueFalse lists the letters T, F and U. Every water area in four DFIRMs holds it (47025C 449, 37153C 281, 37093C 144, 13049C 14), each with SHOWN_INDX F; no other modelled layer holds it. The reference does not say whether it means T. Held by 888 of 779,833 rows of `SHOWN_FIRM` on NFHL service layer 32, counted 2026-10-12.

## Used By

- [`FloodHazardZone`](../flood_hazard_zone.md)
- [`GeneralStructure`](../general_structure.md)
- [`Levee`](../levee.md)
- [`PoliticalJurisdiction`](../political_jurisdiction.md)
- [`ProfileBaseline`](../profile_baseline.md)
- [`WaterArea`](../water_area.md)
- [`WaterLine`](../water_line.md)
