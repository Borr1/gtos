# CF Counterfactual Scoreboard — Absorb Dig_3R — 2026-09-20
_ts_ict: 2026-09-20 14:50 ICT · place=false · apply=false · promote=false · never_merge_R · no NEWS invent_

## Filter
| metric | value |
|---|---|
| n_absorb | 183 |
| n Dig_3R raw | 22 |
| n Dig_3R deduped (primary) | 20 |
| n Challenge_book | 113 |
| **n Dig3R Challenge-true subset** | **0** (empty — lenses exclusive) |

**Honesty:** Challenge-true = Challenge_book / learning_scoreboard_60. Dig_3R yearfolds are a separate lens. Primary scoreboard = Dig_3R-only absorb cells (deduped). Prior Challenge ABC remains `jev_train_cf_scoreboard_ABC.json` — never_merge_R.

## Policy citations (prior pack — not invented)
- A/B/C ids: `jev_train_cf_ABC_summary.json` / `jev_train_cf_scoreboard_ABC.json`
- C choice engine: `JEV_WIN_LOSE_LEARN_strike_rule_20260920.py` strike_when_right
- REAL menu + size_mult: `JEV_TRAIN_ABSORB_20260920.json` / build absorb `desired_size_mult`
- Menu: `A_STAND_DOWN(0)` · `B_SIZE_HALF(0.5)` · `C_SIZE_TRIM(0.75)` · `D_FULL(1)` · `E_KEEP_CAP(1)`

## A / B / C table (Dig_3R deduped, shadow CF)

| Policy | id | n_touched | n_stand | n_keep | n_half | n_trim | n_cap | n_with_R | sumR Dig_3R |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | A_baseline_raw | 20 | 0 | 20 | 0 | 0 | 0 | 20 | -27.3999 |
| B | B_learn_soft_no_panic_hardoff | 20 | 0 | 4 | 8 | 8 | 0 | 20 | +124.6936 |
| C | C_jev_trained_multi_question | 20 | 8 | 4 | 0 | 8 | 0 | 20 | +305.5492 |
| ref | actual_absorb_label | 20 | 8 | 4 | 0 | 8 | 0 | 20 | +305.5492 |

- Δ C−A = **+332.9491**
- Δ B−A = **+152.0935**
- Δ C−actual = **+0.0000**

## Choice histograms
- **A** `A_baseline_raw`: {'D_FULL': 20}
- **B** `B_learn_soft_no_panic_hardoff`: {'B_SIZE_HALF': 8, 'C_SIZE_TRIM': 8, 'D_FULL': 4}
- **C** `C_jev_trained_multi_question`: {'A_STAND_DOWN': 8, 'C_SIZE_TRIM': 8, 'D_FULL': 4}

## Dedupe
- dropped 2 REVIVE duplicates of YEARFOLD/DEEPEN cells
  - {'kept_source': 'SPRING_Dig_3R_YEARFOLD', 'dropped_source': 'REVIVE:revive_spring_false_year_moment', 'key': ['dsp_spring_close_on_20low_through_the_box', 2022, -26.2512]}
  - {'kept_source': 'THREE_FRESH_DEEPEN_Dig_3R', 'dropped_source': 'REVIVE:revive_three_fresh_dig_neg_vs_edge', 'key': ['dsp_three_fresh_lower_lows', 2014, -70.6915]}

## Gaps
- Challenge-true ∩ Dig_3R lens = 0 (lenses exclusive in absorb); Dig_3R yearfolds scored instead
- Prior A/B/C built on Challenge closes n=60 (ok_win|false_structure|event_gap); Dig_3R uses year_le0/false_spring/ok_year_proxy — adaptation cited
- alive_sleeves_for_symbol still PENDING_SHADOW on Dig cards
- CF variants PAUSED (CHAIR_CF_VARIANTS_PAUSED.lock) — shadow scoreboard only
- REVIVE rows duplicate YEARFOLD/DEEPEN cells — deduped for sumR
- No NEWS invent; never_merge_R across Dig_3R|Module_ATR|Edge_ATR|Challenge_book|year_proxy

## Paths
- `/workspace/gtos/close_loop/war_room_20260920/CF_COUNTERFACTUAL_SCOREBOARD_ABSORB_DIG3R_20260920.json`
- `/workspace/gtos/close_loop/war_room_20260920/CF_COUNTERFACTUAL_SCOREBOARD_ABSORB_DIG3R_20260920.md`
- absorb: `/workspace/gtos/close_loop/war_room_20260920/jev_train_rows_absorb_20260920.jsonl`

## Locks
- place=false · apply=false · promote=false
- never_merge_R · no NEWS invent · CF variants PAUSED
