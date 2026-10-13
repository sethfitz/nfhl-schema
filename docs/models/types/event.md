# Event

Values of `D_Event` that apply to the FIRM Database, each as the data stores it.
Used by `S_Cst_Tsct_Ln.EVENT_TYP`. The last is a legacy value: common in the
data, not in the reference.

## Values

- `50 Percent Chance` - Code `50pct`. Printed in the reference as `50-Percent-Chance`.
- `10 Percent Chance` - Code `10pct`. Printed in the reference as `10-Percent-Chance`.
- `4 Percent Chance` - Code `04pct`. Printed in the reference as `4-Percent-Chance`.
- `2 Percent Chance` - Code `02pct`. Printed in the reference as `2-Percent-Chance`.
- `1 Percent Plus Chance` - Code `01plus`. Printed in the reference as `1-Percent-Plus-Chance`.
- `1 Percent Minus Chance` - Code `01minus`. Printed in the reference as `1-Percent-Minus-Chance`.
- `1 Percent Chance` - Code `01pct`. Printed in the reference as `1-Percent-Chance`.
- `0.2 Percent Chance` - Code `0_2pct`. Printed in the reference as `0.2-Percent-Chance`.
- `1 Percent Chance Future Conditions` - Code `01pctfut`. Printed in the reference as `1-Percent-Chance Future Conditions`.
- `NP` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. Section 7.3 of the FIRM Database reference's value for a text field “intentionally not populated”, which the FEMA Project Officer may allow in a required field. D_Event lists nine event types and not it (November 2024 edition). 132 DFIRMs, the largest 02110C (992), 600001 (374), 25023C (236), 25001C (204), 155166 (182) and 48201C (180). Held by 8,873 of 22,367 rows of `EVENT_TYP` on NFHL service layer 15, counted 2026-10-13.

## Used By

- [`CoastalTransect`](../coastal_transect.md)
