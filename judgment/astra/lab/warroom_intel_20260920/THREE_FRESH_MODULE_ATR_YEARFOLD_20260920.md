# THREE_FRESH Module_ATR YEARFOLD — XAUUSD × dsp_three_fresh_lower_lows — 2026-09-20 14:18 ICT

**Affinity (full TAG):** `XAUUSD × dsp_three_fresh_lower_lows` · alias `dsp_three_fresh`
**Lens:** **Module_ATR** (third) · exit_shape from recovered file **stop0.75_tgt6.0 ATR**
**Side:** LONG only · **promote=false** · **place=false** · **CF PAUSED**

## CRITICAL — three R universes (NEVER merge)

| Lens | What | R meaning |
|------|------|-----------|
| **Dig_3R** | Dig PRIMARY blotter / THREE_FRESH_DEEPEN | Structure box-stop → **−1.0R**; fixed **+3.0R** TP; 32-bar time_stop |
| **Edge_ATR** | Instrument Edge packs (cite only) | ATR(14) R-unit; variable exits; no fixed 3R/6ATR |
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
| signal | verbatim ALL36 from recovered file: fresh LL >0.15ATR ×2 + downs≥2 + vol≥0.8×median20 |
| missing vs live module | `stay_timing` / peer_panel / admission / TradeIntent book path |
| honesty verdict | **APPROXIMATION** of Module_ATR fills — geometry proxy ≠ module exact |

**Module path:** `/workspace/gtos/research/codila_absorb/war_room/recovered/dsp_three_fresh_lower_lows.py`  
**Tape:** `/workspace/audit-merge/markets/tapes/XAUUSD_M15.csv` · span `2014-01-02 09:00:00 -> 2026-06-17 07:45:00`  
**Split:** TRAIN ≤2021-12-31 · HOLD ≥2022-01-01 (same as Dig PRIMARY)

---

## Train / Hold (Module_ATR — ATR-R)

| split | n | sumR Module_ATR | avgR | WR |
|-------|--:|----------------:|-----:|---:|
| TRAIN | 6894 | **+176.8235** | +0.0256 | 0.1150 |
| HOLD | 4345 | **+315.1432** | +0.0725 | 0.1220 |
| overall | 11239 | +491.9668 | +0.0438 | 0.1177 |

Exits overall: orig_stop=9916 · orig_tp=1319 · time_stop=4

HOLD sumR Module_ATR **PASS** (positive) · promote **NO** · place **NO**

---

## Year table — Module_ATR (all years)

| year | split | n | sumR Module_ATR | avgR | WR | ≤0? | exits (stop/tp/time) | Dig-neg / 2026? |
|-----:|-------|--:|----------------:|-----:|---:|:---:|----------------------|-----------------|
| 2014 | train | 828 | **+0.00** | +0.0000 | 0.111 | ⚠ | 736/92/0 | ⚠ Dig train-neg |
| 2015 | train | 856 | **-27.75** | -0.0324 | 0.106 | ⚠ | 765/91/0 |  |
| 2016 | train | 911 | **+64.81** | +0.0711 | 0.122 |  | 800/110/1 | ⚠ Dig train-neg |
| 2017 | train | 886 | **+44.25** | +0.0499 | 0.118 |  | 781/105/0 |  |
| 2018 | train | 982 | **-41.25** | -0.0420 | 0.105 | ⚠ | 879/103/0 |  |
| 2019 | train | 882 | **+58.42** | +0.0662 | 0.121 |  | 775/106/1 | ⚠ Dig train-neg |
| 2020 | train | 826 | **+136.50** | +0.1653 | 0.136 |  | 714/112/0 |  |
| 2021 | train | 723 | **-58.16** | -0.0804 | 0.100 | ⚠ | 651/71/1 |  |
| 2022 | hold | 1001 | **+18.75** | +0.0187 | 0.114 |  | 887/114/0 |  |
| 2023 | hold | 995 | **+16.50** | +0.0166 | 0.114 |  | 882/113/0 |  |
| 2024 | hold | 910 | **+147.75** | +0.1624 | 0.135 |  | 787/123/0 |  |
| 2025 | hold | 985 | **+186.00** | +0.1888 | 0.139 |  | 848/137/0 |  |
| 2026 | hold | 454 | **-53.86** | -0.1186 | 0.095 | ⚠ | 411/42/1 | ⚠ Dig 2026 |

\*2026 partial → 2026-06-17 (tape end).

---

## Dig train-neg years + Dig 2026 — three-lens compare (SEPARATE columns)

| year | Dig_3R n/sumR/WR | Edge_ATR n/sumR/WR | Module_ATR n/sumR/WR |
|-----:|------------------|--------------------|----------------------|
| 2014 | 567 / -70.69 / 0.293 | 734 / +104.76 / 0.146 | 828 / +0.00 / 0.111 |
| 2016 | 545 / -25.81 / 0.325 | 763 / +237.37 / 0.155 | 911 / +64.81 / 0.122 |
| 2019 | 553 / -8.81 / 0.333 | 751 / +194.48 / 0.142 | 882 / +58.42 / 0.121 |
| 2026 | 242 / -3.62 / 0.335 | 370 / +34.43 / 0.130 | 454 / -53.86 / 0.095 |

**Reading (no merge):**
- **2014:** Dig heavily neg (−70.7); Edge still +104.8 ATR; Module_ATR **flat 0.0** (exactly 8 stops per 1×+6ATR target — stop density balances rare 6ATR wins).
- **2016:** Dig neg (−25.8); Edge +237; Module_ATR **+64.8** — fat 6ATR targets pay under Module shape.
- **2019:** Dig mild neg (−8.8); Edge +194; Module_ATR **+58.4**.
- **2026:** Dig −3.6; Edge +34.4; Module_ATR **−53.9** — flush_continues / partial year hurts wide-target LONG under Module shape.

---

## Full comparison table Dig_3R vs Edge_ATR vs Module_ATR

| year | split | Dig_3R sumR | Edge_ATR sumR | Module_ATR sumR | Dig n | Edge n | Mod n |
|-----:|-------|------------:|--------------:|----------------:|------:|-------:|------:|
| 2014 | train | -70.69 | +104.76 | +0.00 | 567 | 734 | 828 |
| 2015 | train | +13.38 | +170.64 | -27.75 | 511 | 743 | 856 |
| 2016 | train | -25.81 | +237.37 | +64.81 | 545 | 763 | 911 |
| 2017 | train | +3.31 | +223.20 | +44.25 | 525 | 765 | 886 |
| 2018 | train | +0.21 | +144.98 | -41.25 | 527 | 768 | 982 |
| 2019 | train | -8.81 | +194.48 | +58.42 | 553 | 751 | 882 |
| 2020 | train | +34.99 | +113.03 | +136.50 | 546 | 740 | 826 |
| 2021 | train | +20.04 | +38.56 | -58.16 | 521 | 665 | 723 |
| 2022 | hold | +16.83 | +128.15 | +18.75 | 540 | 798 | 1001 |
| 2023 | hold | +12.92 | +73.48 | +16.50 | 551 | 736 | 995 |
| 2024 | hold | +52.19 | +251.92 | +147.75 | 578 | 761 | 910 |
| 2025 | hold | +77.20 | +178.37 | +186.00 | 583 | 789 | 985 |
| 2026 | hold | -3.62 | +34.43 | -53.86 | 242 | 370 | 454 |

> Columns are **separate R universes**. Do not sum across Dig / Edge / Module.

---

## Cite — Dig PRIMARY & Edge ATR (not recomputed here)

- Dig TRAIN sumR **-33.3755** · HOLD **+155.5139** · train-neg years 2014/2016/2019
- Edge family `dsp_three_fresh_like` · n=9383 · hold_year_sumR_ATR **1893.3525** · consec_pos **13**
- Packs: AFFINITY_THREE_FRESH_P0_NOTE · XAU_AFFINITY_HOLD_POSITIVE_SCORECARD · XAU_THREE_FRESH_2022_LOSER_SAMPLES_PLAIN
- Overlay: `RESEARCH_ARMED_TAGS_OVERLAY_20260920.json`

---

## Verdict / Report

| item | value |
|------|-------|
| Module_ATR year table | above (2014–2026) |
| Dig train-neg compare | 2014 flat / 2016+ / 2019+ under Module_ATR (vs Dig ≤0) |
| Dig 2026 | Module_ATR **-53.86** (partial) |
| HOLD sumR Module_ATR | **+315.1432** |
| TRAIN sumR Module_ATR | **+176.8235** |
| fill-model honesty | geometry_proxy ≠ module exact / ≠ broker |
| promote | **false** |
| place | **false** |
| CF | **PAUSED** |
| SCORE LANE | Chair NEXT — Module_ATR third lens only |

## Paths
- `/workspace/gtos/close_loop/war_room_20260920/THREE_FRESH_MODULE_ATR_YEARFOLD_20260920.md`
- `/workspace/gtos/close_loop/war_room_20260920/THREE_FRESH_MODULE_ATR_YEARFOLD_20260920.json`
- blotter: `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl`
- Dig deepen · Edge packs · recovered module · RESEARCH_ARMED_TAGS_OVERLAY

