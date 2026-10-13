# Method

Values of `D_Method` that apply to the FIRM Database, each as the data stores
it. Used by `S_Cst_Tsct_Ln.METHOD`. The last is a legacy value: common in the
data, not in the reference.

## Values

- `Combo of Topo and Survey` - Code `1000`.
- `Cut from Topo` - Code `1010`.
- `Digitized from FIRM` - Code `1020`.
- `Field Survey` - Code `1030`.
- `NP` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. Section 7.3 of the FIRM Database reference's value for a text field “intentionally not populated”, which the FEMA Project Officer may allow in a required field. D_Method lists four methods and not it (November 2024 edition). Seven DFIRMs: 22023C 110, 22113C 75, 22095C 27, 38005C 17, 34015C 10, 55047C 9, 26011C 1. Held by 249 of 22,367 rows of `METHOD` on NFHL service layer 15, counted 2026-10-13.

## Used By

- [`CoastalTransect`](../coastal_transect.md)
