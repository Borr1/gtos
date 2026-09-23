# SPRING Module_ATR YEARFOLD — XAUUSD × dsp_spring_close_on_20low_through_the_box — 2026-09-20 14:22 ICT

**Affinity (full TAG):** `XAUUSD × dsp_spring_close_on_20low_through_the_box` · alias `dsp_spring_close`
**Lens:** **Module_ATR** (third) · exit_shape from recovered file **stop0.75_tgt6.0 ATR**
**Side:** LONG only · **promote=false** · **place=false** · **CF PAUSED**

## CRITICAL — three R universes (NEVER merge)

| Lens | What | R meaning |
|------|------|-----------|
| **Dig_3R** | Dig PRIMARY / SPRING_REOPEN_GROSS | Structure box-stop → **−1.0R**; fixed **+3.0R** TP; 32-bar time_stop |
| **Edge_ATR** | Instrument Edge `spring_reclaim_L20` (cite only) | ATR(14) R-unit; variable exits; no fixed 3R/6ATR |
| **Module_ATR** | This pack — recovered module exit_shape | ATR(14); stop **−0.75 ATR-R**; tgt **+6.0 ATR-R** |

**Never add Dig sumR + Edge sumR + Module sumR. Separate columns only.**

---

## Fill-model honesty

| axis | value |
|------|-------|
| model | `geometry_proxy_ohlc_touch` |
| NOT | broker fill · module-exact runtime · Dig structure stop · Edge variable exit |
| entry | signal-bar **close** (module decision index) |
| stop | `entry − 0.75 × ATR14(signal)` |
| target | `entry + 6.0 × ATR14(signal)` |
| same-bar | stop before target (conservative) |
| time_stop | 512 bars (~5.3d) — module file has **no** time_stop; residual MTM labeled time_stop |
| busy_until | yes (serial) |
| signal | verbatim ALL36 from recovered file: 20-low (+0.05ATR) down-bar close bottom40% + box<5.5ATR + no 12-bar cascade |
| missing vs live module | `stay_timing` / peer_panel / admission / TradeIntent book path |
| honesty verdict | **APPROXIMATION** of Module_ATR fills — geometry proxy ≠ module exact |

**Module path:** `/workspace/gtos/research/codila_absorb/war_room/recovered/dsp_spring_close_on_20low_through_the_box.py`  
**Tape:** `/workspace/audit-merge/markets/tapes/XAUUSD_M15.csv` · span `2014-01-02 09:00:00 -> 2026-06-17 07:45:00`  
**Split:** TRAIN ≤2021-12-31 · HOLD ≥2022-01-01 (same as Dig PRIMARY)

---

## Train / Hold (Module_ATR — ATR-R)

| split | n | sumR Module_ATR | avgR | WR |
|-------|--:|----------------:|-----:|---:|
| TRAIN | 3442 | **+225.3135** | +0.0655 | 0.1209 |
| HOLD | 2217 | **+261.0000** | +0.1177 | 0.1286 |
| overall | 5659 | +486.3135 | +0.0859 | 0.1239 |

Exits overall: orig_stop=4958 · orig_tp=700 · time_stop=1

HOLD sumR Module_ATR **PASS** · promote **NO** · place **NO**

---

## Year table — Module_ATR (all years)

| year | split | n | sumR Module_ATR | avgR | WR | ≤0? | exits (stop/tp/time) | Dig-neg? |
|-----:|-------|--:|----------------:|-----:|---:|:---:|----------------------|----------|
| 2014 | train | 406 | **-21.00** | -0.0517 | 0.103 | ⚠ | 364/42/0 | ⚠ Dig train-neg |
| 2015 | train | 465 | **-38.25** | -0.0823 | 0.099 | ⚠ | 419/46/0 |  |
| 2016 | train | 428 | **+15.31** | +0.0358 | 0.117 |  | 378/49/1 | ⚠ Dig train-neg |
| 2017 | train | 403 | **+82.50** | +0.2047 | 0.141 |  | 346/57/0 |  |
| 2018 | train | 481 | **+24.00** | +0.0499 | 0.118 |  | 424/57/0 | ⚠ Dig train-neg |
| 2019 | train | 433 | **+46.50** | +0.1074 | 0.127 |  | 378/55/0 | ⚠ Dig train-neg |
| 2020 | train | 385 | **+62.25** | +0.1617 | 0.135 |  | 333/52/0 |  |
| 2021 | train | 441 | **+54.00** | +0.1224 | 0.129 |  | 384/57/0 | ⚠ Dig train-neg |
| 2022 | hold | 568 | **+66.75** | +0.1175 | 0.129 |  | 495/73/0 | ⚠ Dig hold-neg |
| 2023 | hold | 531 | **+0.00** | +0.0000 | 0.111 | ⚠ | 472/59/0 |  |
| 2024 | hold | 440 | **+81.75** | +0.1858 | 0.139 |  | 379/61/0 |  |
| 2025 | hold | 463 | **+98.25** | +0.2122 | 0.142 |  | 397/66/0 |  |
| 2026 | hold | 215 | **+14.25** | +0.0663 | 0.121 |  | 189/26/0 | ⚠ Dig hold-neg |

*2026 partial → 2026-06-17 (tape end).

---

## Dig train/hold-neg years — three-lens compare (SEPARATE columns)

| year | Dig_3R n/sumR/WR | Edge_ATR n/sumR/WR | Module_ATR n/sumR/WR |
|-----:|------------------|--------------------|----------------------|
| 2014 | 300 / -36.39 / 0.273 | 472 / +37.37 / 0.199 | 406 / -21.00 / 0.103 |
| 2016 | 324 / -2.81 / 0.290 | 488 / +82.44 / 0.201 | 428 / +15.31 / 0.117 |
| 2018 | 360 / -11.40 / 0.278 | 494 / +11.09 / 0.162 | 481 / +24.00 / 0.118 |
| 2019 | 328 / -2.35 / 0.287 | 474 / +145.28 / 0.207 | 433 / +46.50 / 0.127 |
| 2021 | 411 / -11.06 / 0.275 | 565 / -260.74 / 0.135 | 441 / +54.00 / 0.129 |
| 2022 | 430 / -26.25 / 0.256 | 555 / +37.26 / 0.153 | 568 / +66.75 / 0.129 |
| 2026 | 170 / -22.54 / 0.265 | 232 / +51.50 / 0.215 | 215 / +14.25 / 0.121 |

**Reading (no merge):** Dig spring gross reopen vs Edge `spring_reclaim_L20` vs Module_ATR stop0.75/tgt6.0 — separate R universes.

---

## Full comparison table Dig_3R vs Edge_ATR vs Module_ATR

| year | split | Dig_3R sumR | Edge_ATR sumR | Module_ATR sumR | Dig n | Edge n | Mod n |
|-----:|-------|------------:|--------------:|----------------:|------:|-------:|------:|
| 2014 | train | -36.39 | +37.37 | -21.00 | 300 | 472 | 406 |
| 2015 | train | +3.15 | +86.05 | -38.25 | 342 | 513 | 465 |
| 2016 | train | -2.81 | +82.44 | +15.31 | 324 | 488 | 428 |
| 2017 | train | +39.07 | +110.33 | +82.50 | 299 | 461 | 403 |
| 2018 | train | -11.40 | +11.09 | +24.00 | 360 | 494 | 481 |
| 2019 | train | -2.35 | +145.28 | +46.50 | 328 | 474 | 433 |
| 2020 | train | +46.70 | +63.35 | +62.25 | 329 | 451 | 385 |
| 2021 | train | -11.06 | -260.74 | +54.00 | 411 | 565 | 441 |
| 2022 | hold | -26.25 | +37.26 | +66.75 | 430 | 555 | 568 |
| 2023 | hold | +65.76 | +165.18 | +0.00 | 409 | 549 | 531 |
| 2024 | hold | +13.35 | +185.59 | +81.75 | 358 | 491 | 440 |
| 2025 | hold | +24.12 | +106.82 | +98.25 | 360 | 491 | 463 |
| 2026 | hold | -22.54 | +51.50 | +14.25 | 170 | 232 | 215 |

> Columns are **separate R universes**. Do not sum across Dig / Edge / Module.

---

## Cite — Dig spring GROSS reopen & Edge ATR (not recomputed as Module)

- Dig spring GROSS TRAIN sumR **+24.9033** (n=2693) · HOLD **+54.4421** (n=1727)
- Dig hold years ≤0 gross: ['2022', '2026'] · Dig train-neg years: [2014, 2016, 2018, 2019, 2021]
- Dig `spring_promote_status`: **RESEARCH_OPEN_GROSS** (NOT live promote)
- Edge family `spring_reclaim_L20` · n=6236 · hold_year_sumR_ATR **1082.2684** · consec_pos **7**
- Packs: AFFINITY_SCOREBOARD · XAU_AFFINITY_YEAR_TABLE · SPRING_REOPEN_GROSS_YEARFOLD
- Overlay: `RESEARCH_ARMED_TAGS_OVERLAY_20260920.json`

---

## Verdict / Report

| item | value |
|------|-------|
| Module_ATR year table | above (2014–2026) |
| Dig spring train/hold gross (SEPARATE) | TRAIN +24.9033 / HOLD +54.4421 |
| HOLD sumR Module_ATR | **+261.0000** |
| TRAIN sumR Module_ATR | **+225.3135** |
| fill-model honesty | geometry_proxy ≠ module exact / ≠ broker |
| promote | **false** |
| place | **false** |
| CF | **PAUSED** |
| SCORE LANE | Chair NEXT — Module_ATR third lens only |

## Paths
- `/workspace/gtos/close_loop/war_room_20260920/SPRING_MODULE_ATR_YEARFOLD_20260920.md`
- `/workspace/gtos/close_loop/war_room_20260920/SPRING_MODULE_ATR_YEARFOLD_20260920.json`
- blotter: `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_XAUUSD_dsp_spring_close_on_20low_through_the_box.jsonl`
- Dig SPRING_REOPEN_GROSS · Edge spring_reclaim_L20 · recovered module · RESEARCH_ARMED_TAGS_OVERLAY
