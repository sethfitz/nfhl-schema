# TsctBaslnTyp

Values of `D_TsctBasln_Typ` that apply to the FIRM Database, each as the data
stores it. Used by `S_Tsct_Basln.TBASE_TYP`. The last 3 are legacy values:
common in the data, not in the reference.

## Values

- `Zero Foot Contour Field Survey` - Code `1000`.
- `Zero Foot Contour LiDAR / Shoals` - Code `1010`.
- `Zero Foot Contour Referenced to Tidal Datum` - Code `1020`.
- `Other Source` - Code `9000`.
- `NP` - Code `NP`.
- `Zero Foot Contour` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. The words the three `Zero Foot Contour ...` types of D_TsctBasln_Typ begin with (Field Survey, LiDAR / Shoals, Referenced to Tidal Datum), without the source that tells them apart. Every row is in one DFIRM, 36103C. No edition of the Domain Tables reference lists it (2016, 2019, 2024). Held by 926 of 35,354 rows of `TBASE_TYP` on NFHL service layer 18, counted 2026-10-12.
- `NON-ERODIBLE BLUFF` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. D_Shr_Typ's shoreline type `Non-Erodible Bluff` (code 1030), upper-cased, in the transect baseline type: a value of another domain. Two DFIRMs, 23015C (222) and 23023C (125). Held by 347 of 35,354 rows of `TBASE_TYP` on NFHL service layer 18, counted 2026-10-12.
- `ZERO FOOT C` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. A `Zero Foot Contour ...` type cut to 11 characters and upper-cased; the cut leaves no word saying which of the three. Every row is in one DFIRM, 24009C. Held by 54 of 35,354 rows of `TBASE_TYP` on NFHL service layer 18, counted 2026-10-12.

## Used By

- [`TransectBaseline`](../transect_baseline.md)
