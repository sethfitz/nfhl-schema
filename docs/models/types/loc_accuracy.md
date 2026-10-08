# LocAccuracy

Values of `D_Loc_Accuracy` that apply to the FIRM Database, each as the data
stores it. Used by `S_Stn_Start.LOC_ACC`. The last is a legacy value: common in
the data, not in the reference.

## Values

- `High` - Code `H`.
- `Medium` - Code `M`.
- `Low` - Code `L`.
- `NP` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. Section 7.3 of the FIRM Database reference's value for a text field “intentionally not populated”, which the FEMA Project Officer may allow in a required field. D_Loc_Accuracy has never listed it: the November 2016, February 2019 and November 2024 editions all list only H, M and L. Held by 284 of 93,357 rows of `LOC_ACC` on NFHL service layer 13, counted 2026-10-08.

## Used By

- [`StationStart`](../station_start.md)
