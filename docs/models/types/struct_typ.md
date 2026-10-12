# StructTyp

Values of `D_Struct_Typ` that apply to the FIRM Database, each as the data
stores it. Used by `S_Gen_Struct.STRUCT_TYP`. The last 3 are legacy values:
common in the data, not in the reference.

## Values

- `Aqueduct` - Code `1000`.
- `Bridge` - Code `1001`.
- `Canal` - Code `1002`.
- `Channel` - Code `1003`.
- `Control Structure` - Code `1006`.
- `Culvert` - Code `1007`.
- `Dam` - Code `1010`.
- `Dock` - Code `1012`.
- `Drop Structure` - Code `1013`.
- `Energy Dissipater` - Code `1014`.
- `Fish Ladder` - Code `1015`.
- `Flume` - Code `1017`.
- `Footbridge` - Code `1018`.
- `Gate` - Code `1019`.
- `Jetty` - Code `1020`.
- `Levee` - Code `1021`.
- `Lock` - Code `1022`.
- `Penstock` - Code `1023`.
- `Pier` - Code `1024`.
- `Pump Station` - Code `1025`.
- `Seawall` - Code `1026`.
- `Side Weir Structure` - Code `1027`.
- `Storm Sewer` - Code `1028`.
- `Utility Crossing` - Code `1029`.
- `Weir` - Code `1030`.
- `Wing Wall` - Code `1031`.
- `0.2-Percent-Annual-Chance Flood Discharge Contained in Structure` - Code `1033`.
- `1-Percent-Annual-Chance Flood Discharge Contained in Structure` - Code `1032`.
- `Floodway Contained in Structure` - Code `1036`.
- `Pipeline` - Code `1037`.
- `Retaining Wall` - Code `1038`.
- `Revetment` - Code `1039`.
- `Siphon` - Code `1040`.
- `Other / Misc. Structure` - Code `9000`.
- `NP` - Code `NP`.
- `1 Pct Annual Chance Flood Discharge Contained In Structure` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. The snapshot's count folds case. Counted by reading every row on 2026-10-12, 310 hold this exact spelling and the rest hold `1 PCT ... Contained in Structure` (9,135), `1 PCT ... Contained In Structure` (3,753) or all capitals (2); the model rejects those as wrong case. Short for the reference's `1-Percent-Annual-Chance Flood Discharge Contained in Structure`: the data spells the percent as `Pct` or `PCT` and drops the hyphens. The exact spelling is in 86 DFIRMs. Held by 13,200 of 285,947 rows of `STRUCT_TYP` on NFHL service layer 24, counted 2026-10-12.
- `0.2 Pct Annual Chance Flood Discharge Contained In Structure` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. The snapshot's count folds case. Counted by reading every row on 2026-10-12, 383 hold this exact spelling and the rest hold `0.2 PCT ... Contained in Structure` (5,430) or `0.2 PCT ... Contained In Structure` (5,127); the model rejects those as wrong case. Short for the reference's `0.2-Percent-Annual-Chance Flood Discharge Contained in Structure`: the data spells the percent as `Pct` or `PCT` and drops the hyphens. The exact spelling is in 83 DFIRMs. Held by 10,940 of 285,947 rows of `STRUCT_TYP` on NFHL service layer 24, counted 2026-10-12.
- `Other / Misc Structure` - Legacy: not in the November 2024 Domain Tables Technical Reference; validates with a LegacyValueWarning. The reference's `Other / Misc. Structure` (code 9000) without its period; the data holds it on 379 rows in 86 DFIRMs against 16 for the reference's spelling, in 5. Held by 379 of 285,947 rows of `STRUCT_TYP` on NFHL service layer 24, counted 2026-10-12.

## Used By

- [`GeneralStructure`](../general_structure.md)
