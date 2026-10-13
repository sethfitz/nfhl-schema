# VZone

Values of `D_VZone` that apply to the FIRM Database, each as the data stores it.
Used by `S_Cst_Tsct_Ln.VZONE_EXT`. The last 4 are legacy values: common in the
data, not in the reference.

## Values

- `Breaking Wave Ht` - Code `1060`.
- `High Velocity Flow` - Code `1050`.
- `Runup` - Code `1030`.
- `Wave Overtopping Splash Zone` - Code `1010`.
- `PFD` - Code `1020`.
- `NP` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. Section 7.3 of the FIRM Database reference's value for a text field “intentionally not populated”, which the FEMA Project Officer may allow in a required field. D_VZone lists five V zone types and not it (November 2024 edition). Six DFIRMs: 22023C 110, 22113C 75, 22095C 27, 34015C 10, 55047C 9, 26011C 1. Held by 232 of 22,367 rows of `VZONE_EXT` on NFHL service layer 15, counted 2026-10-13.
- `WHAFIS` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. A wave model, not a V zone extent: D_Wave_Mdl lists `WHAFIS 3.0 (1988)`, `WHAFIS 3.0 GL (1983)` and `WHAFIS 4.0 (2007)`. Five DFIRMs: 22053C 41, 25023C 30, 34033C 18, 44009C 16, 44005C 6. Held by 111 of 22,367 rows of `VZONE_EXT` on NFHL service layer 15, counted 2026-10-13.
- `30 FOOT SPLASH ZONE BEHIND S` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. A description cut at the field's 28 characters, mid-phrase. It names a splash zone, which D_VZone lists as `Wave Overtopping Splash Zone`, but the cut leaves no wording that matches. Three DFIRMs: 44005C 37, 44009C 26, 25023C 3. Held by 66 of 22,367 rows of `VZONE_EXT` on NFHL service layer 15, counted 2026-10-13.
- `RUNUP EXTENT` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. D_VZone's `Runup` with `EXTENT` added, the field's own subject. Two DFIRMs: 44005C 34, 34033C 7. Held by 41 of 22,367 rows of `VZONE_EXT` on NFHL service layer 15, counted 2026-10-13.

## Used By

- [`CoastalTransect`](../coastal_transect.md)
