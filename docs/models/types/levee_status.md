# LeveeStatus

Values of `D_Levee_Status` that apply to the FIRM Database, each as the data
stores it. Used by `S_Levee.LEVEE_STAT`. The last 2 are legacy values: common in
the data, not in the reference.

## Values

- `Accredited` - Code `A`.
- `Non-Accredited` - Code `N`.
- `Provisionally Accredited` - Code `P`.
- `AR` - Code `AR`.
- `A99` - Code `A99`.
- `NP` - Code `NP`.
- `De-Accredited` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. Not in the November 2024 D_Levee_Status, which lists Accredited, Non-Accredited, Provisionally Accredited, AR, A99 and NP. By its words it names a levee that was accredited once and is not now; the reference maps it to no listed value, and its LEV_AN_TYP rule (only for Non-Accredited) does not mention it. Held by 991 of 16,320 rows of `LEVEE_STAT` on NFHL service layer 23, counted 2026-10-10.
- `Never Accredited` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. Not in the November 2024 D_Levee_Status, which lists Accredited, Non-Accredited, Provisionally Accredited, AR, A99 and NP. By its words it names a levee that has never been accredited; the reference maps it to no listed value, and its LEV_AN_TYP rule (only for Non-Accredited) does not mention it. Held by 912 of 16,320 rows of `LEVEE_STAT` on NFHL service layer 23, counted 2026-10-10.

## Used By

- [`Levee`](../levee.md)
