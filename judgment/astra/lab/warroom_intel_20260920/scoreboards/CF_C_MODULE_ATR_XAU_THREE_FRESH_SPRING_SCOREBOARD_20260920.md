# CF C × Module_ATR — XAU three_fresh + spring — 2026-09-20 14:52 ICT

**SEPARATE LENS** · Dig_3R numbers must NOT appear in sumR columns (cite Dig pack path only).  
place=false · apply=false · order_send=0 · promote=false · never_merge_R · CF variants PAUSED

Dig pack cite only: `CF_COUNTERFACTUAL_SCOREBOARD_ABSORB_DIG3R_20260920.json`

## C rule (Module-native)
- **trap** (`le0` OR `sumR_Module_ATR<=0`) → `A_STAND_DOWN` (×0)
- **thin** (positive & `< median` of sleeve positive Module years) → `C_SIZE_TRIM` (×0.75)
- **win** (`>= median` positive) → `D_FULL` (×1)
- Baseline **A** = always `D_FULL`

Medians: three_fresh=61.61515 · spring=58.125

## dsp_three_fresh_lower_lows (Module_ATR only)

| Policy | n_years | Choice hist | sumR Module_ATR | year≤0 under policy |
|---|---:|---|---:|---|
| A baseline | 13 | D_FULL:13 | 491.9667 | [2014, 2015, 2018, 2021, 2026] |
| C strike | 13 | A_STAND_DOWN:5, C_SIZE_TRIM:4, D_FULL:4 | 638.5011 | [2014, 2015, 2018, 2021, 2026] |

- Δ C−A Module = **146.5344**
- year≤0 geometry: [2014, 2015, 2018, 2021, 2026]

## dsp_spring_close_on_20low_through_the_box (Module_ATR only)

| Policy | n_years | Choice hist | sumR Module_ATR | year≤0 under policy |
|---|---:|---|---:|---|
| A baseline | 13 | D_FULL:13 | 486.3135 | [2014, 2015, 2023] |
| C strike | 13 | A_STAND_DOWN:3, C_SIZE_TRIM:5, D_FULL:5 | 507.047625 | [2014, 2015, 2023] |

- Δ C−A Module = **20.734125**
- year≤0 geometry: [2014, 2015, 2023]

## Combined Module_ATR only (both sleeves)

| Policy | n_cells | Choice hist | sumR Module_ATR |
|---|---:|---|---:|
| A | 26 | D_FULL:26 | 978.2802 |
| C | 26 | A_STAND_DOWN:8, C_SIZE_TRIM:9, D_FULL:9 | 1145.548725 |

- Δ C−A Module combined = **167.268525**

## Honesty
- No Dig_3R sumR in this file’s metric columns
- No Challenge_book merge
- Blotter jsonl present (sources cited); yearfold cells are the scored universe
