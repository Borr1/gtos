# EURUSD × sub_mid_dn_re SHORT — DEEPEN (Chair step 1 FIRST)
as_of_ict: 2026-09-20T18:59:18.224985+07:00

## Affinity verdict: **KEEP**
- Why: ≥2 consec pos (13) · yf≥0.7 (1.0) · no catastrophic unrecovered wipe
- Gates: ≥2 consec=YES (13) · every-year=YES · yearfold_frac=1.0 · fail_years=[] · no catastrophic wipe

## Metrics
- n=5818 · avg_R=0.191638 · sum_R=1114.9514 · win_rate=0.1267
- hold_year_sumR=1114.9514
- train≤2024 sumR=1052.2343 avg_R=0.205034 · hold 2025–26 sumR=62.7171 avg_R=0.091424

## Idea (plain English)
EURUSD mid stretched above SMA20 by ≥1 ATR in London/NY → SHORT mean-revert toward mid (dn_re). Stop beyond stretch high; time_stop@32. Bet: stretch is inventory excursion, not new trend.

## Fail-year WHY
**None** — yearfold fail years empty. Soft-positive years (avg_R>0 but <0.10) are NOT kills:
- **2016**: avg_R=0.0570 sum_R=27.6493 n=485 — Still avg_R>0 so yearfold PASS; softness = lower edge density / more chop fades, NOT idea invalidation. No Lon+NY cage story.
- **2023**: avg_R=0.0781 sum_R=37.701 n=483 — Still avg_R>0 so yearfold PASS; softness = lower edge density / more chop fades, NOT idea invalidation. No Lon+NY cage story.
- **2025**: avg_R=0.0925 sum_R=43.9427 n=475 — Still avg_R>0 so yearfold PASS; softness = lower edge density / more chop fades, NOT idea invalidation. No Lon+NY cage story.
- **2026**: avg_R=0.0890 sum_R=18.7743 n=211 — Still avg_R>0 so yearfold PASS; softness = lower edge density / more chop fades, NOT idea invalidation. No Lon+NY cage story.

## Year table
| year | n | win_rate | avg_R | sum_R | avg>0 |
|---:|---:|---:|---:|---:|:---:|
| 2014 | 434 | 0.147 | 0.2907 | 126.1718 | Y |
| 2015 | 482 | 0.118 | 0.2633 | 126.9305 | Y |
| 2016 | 485 | 0.117 | 0.0570 | 27.6493 | Y |
| 2017 | 480 | 0.115 | 0.1802 | 86.5078 | Y |
| 2018 | 448 | 0.116 | 0.1159 | 51.9143 | Y |
| 2019 | 430 | 0.137 | 0.2265 | 97.408 | Y |
| 2020 | 482 | 0.143 | 0.2347 | 113.1292 | Y |
| 2021 | 472 | 0.131 | 0.2584 | 121.9506 | Y |
| 2022 | 448 | 0.150 | 0.3338 | 149.5586 | Y |
| 2023 | 483 | 0.118 | 0.0781 | 37.701 | Y |
| 2024 | 488 | 0.113 | 0.2322 | 113.3133 | Y |
| 2025 | 475 | 0.128 | 0.0925 | 43.9427 | Y |
| 2026 | 211 | 0.104 | 0.0890 | 18.7743 | Y |

## Paths
- `/workspace/instrument-edge/packs/EURUSD_SUB_MID_DN_RE_SHORT_DEEPEN_20260920.md`
- `/workspace/instrument-edge/packs/EURUSD_SUB_MID_DN_RE_SHORT_DEEPEN_20260920.json`
- source: `/workspace/instrument-edge/packs/SWARM_NONXAU_MODULE_ATR_YEARFOLD_20260920.md`
- source: `/workspace/instrument-edge/packs/SWARM_NONXAU_MODULE_ATR_YEARFOLD_20260920.json`
- source: `/workspace/instrument-edge/packs/EURUSD_SUB_MID_DN_RE_PROXY_ATR_YEAR_TABLES_20260920.md`
- source: `/workspace/instrument-edge/packs/MODULE_ATR_WINNERS_PROVE_LOOP_20260920.md`
- source: `/workspace/instrument-edge/packs/ISOLATE_WINNERS_ATR_AFFINITY_20260920.md`

## Locks
place=false · ready_for_key_fx=false · cost never kill · lenses separate · APPLY unset