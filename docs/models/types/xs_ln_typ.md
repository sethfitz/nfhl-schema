# XSLnTyp

Values of `D_XS_Ln_Typ` that apply to the FIRM Database, each as the data stores
it. Used by `S_XS.XS_LN_TYP`.

## Values

- `LETTERED, MAPPED` - Traditional Lettered XS, FDTs, Profiles. Code `1010`.
- `NOT LETTERED, MAPPED` - Modeled XSs used for Base Flood Elevation (BFE) values on FIRM panels, not shown on FDTs or Profiles, shown but not lettered on panels. Code `1020`.
- `NOT LETTERED, NOT MAPPED` - Model Backup in the FIRM Database, including unused XSs adjacent to bridges, too densely spaced, or modeled Zone A. Code `1030`.

## Used By

- [`CrossSection`](../cross_section.md)
