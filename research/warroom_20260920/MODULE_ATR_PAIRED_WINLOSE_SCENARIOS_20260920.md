# Module_ATR paired win/lose scenario cards — 20260920

**Generated:** 2026-09-20 16:11 ICT
**Mode:** SHADOW research · place=false · apply=false · cost never kill-gate
**Owner lock:** paired win/lose + small state deltas that flip outcome
**Lens:** Module_ATR research only (not Dig TRAIN / not live admit)

## Summary
- n_pairs=48 · n_cards=96
- **spring_reclaim_L20** (W2): trades=6236 pairs=24 cross_year=12 within_2021=12
- **dsp_three_fresh_like** (W1): trades=9383 pairs=24 cross_year=12 within_2021=12

## Pair kinds
1. `cross_year_2021lose_vs_adjwin` — 2021 loser ↔ 2020/2022/2023/2024 win on same atr_regime × m15_trend
2. `within_2021_same_soft_state` — same soft state; typically time_stop win vs orig_stop lose

## Sample pairs (first 6)

### spring_reclaim_L20_cross_year_2021lose_vs_adjwin_2021-08-06_2024-04-05
- kind: `cross_year_2021lose_vs_adjwin`
- shared: XAUUSD × spring_reclaim_L20 LONG · atr_regime=atr_high · m15_trend=trend_down
- win: year=2024 exit=time_stop R=+9.751 atr_pct=0.744 bars=32 stop_dist_atr=2.1788
- lose: year=2021 exit=orig_stop R=-6.623 atr_pct=0.946 bars=2 stop_dist_atr=6.6233
- flip_hint: exit pathway differs (time_stop survivor vs orig_stop false-spring)

### spring_reclaim_L20_cross_year_2021lose_vs_adjwin_2021-09-22_2023-01-12
- kind: `cross_year_2021lose_vs_adjwin`
- shared: XAUUSD × spring_reclaim_L20 LONG · atr_regime=atr_high · m15_trend=trend_up
- win: year=2023 exit=time_stop R=+1.408 atr_pct=0.952 bars=32 stop_dist_atr=5.4692
- lose: year=2021 exit=orig_stop R=-5.922 atr_pct=0.86 bars=2 stop_dist_atr=5.9216
- flip_hint: exit pathway differs (time_stop survivor vs orig_stop false-spring)

### spring_reclaim_L20_cross_year_2021lose_vs_adjwin_2021-02-04_2024-07-26
- kind: `cross_year_2021lose_vs_adjwin`
- shared: XAUUSD × spring_reclaim_L20 LONG · atr_regime=atr_low · m15_trend=trend_down
- win: year=2024 exit=time_stop R=+7.243 atr_pct=0.08 bars=32 stop_dist_atr=2.3397
- lose: year=2021 exit=orig_stop R=-5.223 atr_pct=0.064 bars=3 stop_dist_atr=5.2234
- flip_hint: exit pathway differs (time_stop survivor vs orig_stop false-spring)

### spring_reclaim_L20_cross_year_2021lose_vs_adjwin_2021-06-18_2023-12-21
- kind: `cross_year_2021lose_vs_adjwin`
- shared: XAUUSD × spring_reclaim_L20 LONG · atr_regime=atr_high · m15_trend=range
- win: year=2023 exit=time_stop R=+0.972 atr_pct=0.778 bars=32 stop_dist_atr=4.2915
- lose: year=2021 exit=orig_stop R=-4.307 atr_pct=0.792 bars=2 stop_dist_atr=4.3069
- flip_hint: exit pathway differs (time_stop survivor vs orig_stop false-spring)

### spring_reclaim_L20_cross_year_2021lose_vs_adjwin_2021-02-24_2022-11-23
- kind: `cross_year_2021lose_vs_adjwin`
- shared: XAUUSD × spring_reclaim_L20 LONG · atr_regime=atr_high · m15_trend=range
- win: year=2022 exit=time_stop R=+5.582 atr_pct=0.896 bars=32 stop_dist_atr=3.7611
- lose: year=2021 exit=orig_stop R=-3.965 atr_pct=0.804 bars=2 stop_dist_atr=3.9653
- flip_hint: exit pathway differs (time_stop survivor vs orig_stop false-spring)

### spring_reclaim_L20_cross_year_2021lose_vs_adjwin_2021-04-20_2023-04-04
- kind: `cross_year_2021lose_vs_adjwin`
- shared: XAUUSD × spring_reclaim_L20 LONG · atr_regime=atr_low · m15_trend=range
- win: year=2023 exit=time_stop R=+19.478 atr_pct=0.308 bars=32 stop_dist_atr=2.688
- lose: year=2021 exit=orig_stop R=-3.639 atr_pct=0.08 bars=2 stop_dist_atr=3.639
- flip_hint: exit pathway differs (time_stop survivor vs orig_stop false-spring)

## Artifacts
- `/workspace/gtos/research/warroom_20260920/MODULE_ATR_PAIRED_WINLOSE_SCENARIOS_20260920.json`
- `/workspace/gtos/research/warroom_20260920/MODULE_ATR_PAIRED_WINLOSE_SCENARIO_CARDS_20260920.jsonl`
- `/workspace/gtos/research/warroom_20260920/MODULE_ATR_PAIRED_WINLOSE_SCENARIOS_20260920.md`

## Walls
place=false · apply=false · no NEWS invent · cost never kill-gate · affinity instrument×sleeve · Jev never places
