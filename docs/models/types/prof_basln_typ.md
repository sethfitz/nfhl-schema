# ProfBaslnTyp

Values of `D_Prof_Basln_Typ` that apply to the FIRM Database, each as the data
stores it. Used by `S_Profil_Basln.WATER_TYP`. The last is a legacy value:
common in the data, not in the reference.

## Values

- `Profile Baseline` - Code `1000`.
- `Profile Baseline and Stream Centerline` - Code `2000`.
- `Hydraulic Link` - Code `3000`.
- `Unknown` - Code `UNK`.
- `Stream / River` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. The November 2016 Domain Tables reference's D_Carto_Hydro_Code value 4600, a cartographic code for symbolising water features that applied to the FRD only, not a type of profile baseline. The 2019 and 2024 editions list it in no domain. Held by 426 of 338,155 rows of `WATER_TYP` on NFHL service layer 17, counted 2026-10-07.

## Used By

- [`ProfileBaseline`](../profile_baseline.md)
