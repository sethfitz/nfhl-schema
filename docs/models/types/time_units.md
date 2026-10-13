# TimeUnits

Values of `D_Time_Units` that apply to the FIRM Database, each as the data
stores it. Used by `S_Cst_Tsct_Ln.TIME_UNIT`. The last 2 are legacy values:
common in the data, not in the reference.

## Values

- `DAYS` - Code `1000`.
- `HOURS` - Code `1010`.
- `MINUTES` - Code `1020`.
- `MONTHS` - Code `1030`.
- `SECONDS` - Code `1040`.
- `WEEKS` - Code `1050`.
- `YEARS` - Code `1060`.
- `NP` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. Section 7.3 of the FIRM Database reference's value for a text field “intentionally not populated”, which the FEMA Project Officer may allow in a required field. D_Time_Units lists seven time units and not it (November 2024 edition). Four DFIRMs: 22023C 110, 34029C 96, 22113C 75, 22095C 27. Held by 308 of 22,367 rows of `TIME_UNIT` on NFHL service layer 15, counted 2026-10-13.
- `NA` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. `NA` where D_Time_Units has no not-populated value; the other fields of the same 28 coastal transects hold it too. All in one DFIRM, 26099C. Held by 28 of 22,367 rows of `TIME_UNIT` on NFHL service layer 15, counted 2026-10-13.

## Used By

- [`CoastalTransect`](../coastal_transect.md)
