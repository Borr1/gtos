# EXPANDING WHY NEGATIVE YEARS — XAUUSD × dsp_expanding_up_staircase

**ts_ict:** 2026-09-20 13:50 ICT  
**place:** false | **CF:** PAUSED | **affinity_law:** instrument×sleeve not portable by default  
**owner_pivot:** P0 WHY (idea / context / who-decided) — DEPTH OVER SPEED — STOP optimizing scoreboard n  
**owner_law_cost:** cost is NEVER the issue; cost-stress is NOT a promote/kill gate; year sums = **gross R**

## Fill model honesty
- `geometry_proxy_ohlc_touch_no_broker_fill` — NOT live book/broker fills
- Structure stop + **3R TP** or **32-bar (~8h) time_stop** MTM on PRIMARY M15 OHLC
- Blotter: `blotter_PRIMARY_XAUUSD_dsp_expanding_up_staircase.jsonl` (n=3936; hold 2022–2026)
- Tape: `/workspace/audit-merge/markets/tapes/XAUUSD_M15.csv` (2014-01-02 → 2026-06-17)
- H4: **synthesized from M15** (no native XAUUSD_H4 under audit-merge tapes)

## Year sums (GROSS R — idea/year truth)

| year | n | sumR gross | WR | ≤0 gross? | session note (gross) |
|------|---|------------|----|-----------|----------------------|
| 2022 | 322 | **-29.1312** | 0.326 | ⚠ YES | Asia -0.1R, London -18.7R, NY -1.0R, Off_hours -9.3R |
| 2023 | 322 | **+9.5394** | 0.376 | ok | Asia +20.6R, London -1.8R, NY -16.1R, Off_hours +6.8R |
| 2024 | 339 | **+47.7586** | 0.410 | ok | Asia +13.0R, London +11.4R, NY +9.2R, Off_hours +14.2R |
| 2025 | 328 | **+67.0593** | 0.433 | ok | Asia +22.1R, London +19.8R, NY +14.0R, Off_hours +11.2R |
| 2026 | 143 | **+7.4481** | 0.392 | ok | Asia +11.8R, London -2.5R, NY -12.1R, Off_hours +10.2R |

**Focus:** **2022** is the clear negative hold year (gross **−29.13R**, n=322).  
**2023** gross **+9.54R** — soft vs 2024/25 but **not ≤0**. Any prior “2023 ≤0 after cost” label is **RETRACTED** under owner law (cost never the issue).

## HARDEN_V1 wrap (NOT who decided; NOT another n-chase)
- Lon+NY alone: hold geometry went **soft** (research wrap). Asia/Off carried the **positive hold years** on session folds.
- Do **NOT** revive Lon+NY harden as a promote path. Do **NOT** chase more ATR/session n-filters here.
- 2022 is **not** the sole miss story — regime/idea context matters; filters might rewrite some tickets but autopsy ≠ n-optimize.
- Spring: out of scope; may stay weak for **year/idea** reasons only — **not** cost. `spring revive=false`.

---

## 1) 2022 losers — sample of 12

Idea in every case: geometry_proxy saw an M15 **ascending staircase** (higher highs **and** higher lows) and longed for **3R** continuation with stop under the stair low.

### L01 — 2022-01-04 12:30:00 → 2022-01-04 13:00:00 | NY | R=-1.0 | exit=`orig_stop`
- **Fill/close:** entry 1806.51 → exit 1804.97 (stop 1804.97). tape timestamps as-is (broker/server clock); session tags Asia/Lon/NY/Off on that clock — not converted ICT.
- **Idea:** Geometry proxy saw ~3-bar M15 ascending staircase (each bar higher high AND higher low) and went LONG at close 1806.51 for 3R continuation; structure stop under stair low 1804.97 (risk 1.54, ~0.8×ATR14).
- **H4/M15 context:** H4 broadly expanding up (rising highs and rising lows) — higher-TF agrees with M15 stair idea H4 closes≈[1799.69, 1801.34, 1805.21, 1805.45, 1805.74, 1807.2]. ~5d net -6.1. MFE/MAE 2.14/-2.55.
- **Why idea invalid then:**
  - Prior ~5 sessions net down (-6.1) — stair printed into weakness, not a fresh up-regime.
  - H4 agreed with expand-up — idea had room on the higher frame.
  - Brief lift (MFE 2.14) then reverse through stair low — failed continuation, stop exit −1R.
  - London/NY session: HARDEN wrap showed Lon+NY alone is where this proxy's multiyear hold geometry went soft (gross hold ~flat; Asia/Off carried the positive hold years). Not a cost story — session×idea affinity.
- **Exit:** `orig_stop` (structure stop −1R).

### L02 — 2022-01-07 20:00:00 → 2022-01-10 02:00:00 | NY | R=-1.0 | exit=`orig_stop`
- **Fill/close:** entry 1796.96 → exit 1792.42 (stop 1792.42). tape timestamps as-is (broker/server clock); session tags Asia/Lon/NY/Off on that clock — not converted ICT.
- **Idea:** Geometry proxy saw ~3-bar M15 ascending staircase (each bar higher high AND higher low) and went LONG at close 1796.96 for 3R continuation; structure stop under stair low 1792.42 (risk 4.54, ~1.6×ATR14).
- **H4/M15 context:** H4 drifting up (~5.4 over 6 H4 bars) but not a clean expanding staircase H4 closes≈[1790.66, 1790.72, 1793.09, 1789.19, 1795.95, 1796.04]. ~5d net -25.7. MFE/MAE 1.67/-4.66.
- **Why idea invalid then:**
  - Prior ~5 sessions net down (-25.7) — stair printed into weakness, not a fresh up-regime.
  - Brief lift (MFE 1.67) then reverse through stair low — failed continuation, stop exit −1R.
  - London/NY session: HARDEN wrap showed Lon+NY alone is where this proxy's multiyear hold geometry went soft (gross hold ~flat; Asia/Off carried the positive hold years). Not a cost story — session×idea affinity.
- **Exit:** `orig_stop` (structure stop −1R).

### L03 — 2022-02-02 06:15:00 → 2022-02-02 07:00:00 | Asia | R=-1.0 | exit=`orig_stop`
- **Fill/close:** entry 1798.45 → exit 1797.29 (stop 1797.29). tape timestamps as-is (broker/server clock); session tags Asia/Lon/NY/Off on that clock — not converted ICT.
- **Idea:** Geometry proxy saw ~3-bar M15 ascending staircase (each bar higher high AND higher low) and went LONG at close 1798.45 for 3R continuation; structure stop under stair low 1797.29 (risk 1.16, ~1.5×ATR14).
- **H4/M15 context:** H4 drifting DOWN (~-7.1) — M15 stair is a counter-trend micro-pop H4 closes≈[1805.57, 1804.12, 1802.76, 1800.97, 1800.39, 1798.47]. ~5d net -50.4. MFE/MAE 0.23/-1.29.
- **Why idea invalid then:**
  - Prior ~5 sessions net down (-50.4) — stair printed into weakness, not a fresh up-regime.
  - H4 already leaning down; M15 stair was a local expand against the higher frame.
  - Almost no follow-through (MFE 0.23 vs risk 1.16) — trap/micro-stair that immediately gave back.
  - Even Asia/Off can trap when the stair is thin into supply or the day is already rolling over — session affinity is not a free pass.
- **Exit:** `orig_stop` (structure stop −1R).

### L04 — 2022-03-01 11:30:00 → 2022-03-01 14:45:00 | London | R=-1.0 | exit=`orig_stop`
- **Fill/close:** entry 1917.34 → exit 1911.73 (stop 1911.73). tape timestamps as-is (broker/server clock); session tags Asia/Lon/NY/Off on that clock — not converted ICT.
- **Idea:** Geometry proxy saw ~3-bar M15 ascending staircase (each bar higher high AND higher low) and went LONG at close 1917.34 for 3R continuation; structure stop under stair low 1911.73 (risk 5.61, ~2.4×ATR14).
- **H4/M15 context:** H4 choppy/sideways — expanding-up idea has little higher-TF wind H4 closes≈[1916.08, 1898.25, 1908.17, 1903.3, 1906.98, 1916.01]. ~5d net +8.9. MFE/MAE 8.96/-6.26.
- **Why idea invalid then:**
  - Prior ~5 sessions net up (8.9) — with-trend backdrop.
  - Brief lift (MFE 8.96) then reverse through stair low — failed continuation, stop exit −1R.
  - London/NY session: HARDEN wrap showed Lon+NY alone is where this proxy's multiyear hold geometry went soft (gross hold ~flat; Asia/Off carried the positive hold years). Not a cost story — session×idea affinity.
- **Exit:** `orig_stop` (structure stop −1R).

### L05 — 2022-03-21 04:30:00 → 2022-03-21 12:30:00 | Asia | R=-0.783 | exit=`time_stop`
- **Fill/close:** entry 1927.55 → exit 1922.58 (stop 1921.2). tape timestamps as-is (broker/server clock); session tags Asia/Lon/NY/Off on that clock — not converted ICT.
- **Idea:** Geometry proxy saw ~3-bar M15 ascending staircase (each bar higher high AND higher low) and went LONG at close 1927.55 for 3R continuation; structure stop under stair low 1921.20 (risk 6.35, ~2.7×ATR14).
- **H4/M15 context:** H4 choppy/sideways — expanding-up idea has little higher-TF wind H4 closes≈[1932.06, 1935.1, 1928.69, 1920.09, 1922.04, 1928.15]. ~5d net -59.3. MFE/MAE 1.41/-5.54.
- **Why idea invalid then:**
  - Prior ~5 sessions net down (-59.3) — stair printed into weakness, not a fresh up-regime.
  - Never reached 3R in 32 M15 bars (~8h); time_stop MTM -0.78R — idea stalled in range.
  - Even Asia/Off can trap when the stair is thin into supply or the day is already rolling over — session affinity is not a free pass.
- **Exit:** `time_stop` (time_stop MTM — no 3R in ~8h).

### L06 — 2022-04-01 04:15:00 → 2022-04-01 09:45:00 | Asia | R=-1.0 | exit=`orig_stop`
- **Fill/close:** entry 1936.29 → exit 1932.53 (stop 1932.53). tape timestamps as-is (broker/server clock); session tags Asia/Lon/NY/Off on that clock — not converted ICT.
- **Idea:** Geometry proxy saw ~3-bar M15 ascending staircase (each bar higher high AND higher low) and went LONG at close 1936.29 for 3R continuation; structure stop under stair low 1932.53 (risk 3.76, ~2.2×ATR14).
- **H4/M15 context:** H4 broadly expanding up (rising highs and rising lows) — higher-TF agrees with M15 stair idea H4 closes≈[1925.26, 1934.07, 1944.37, 1936.7, 1934.25, 1937.59]. ~5d net -26.1. MFE/MAE 3.2/-4.72.
- **Why idea invalid then:**
  - Prior ~5 sessions net down (-26.1) — stair printed into weakness, not a fresh up-regime.
  - H4 agreed with expand-up — idea had room on the higher frame.
  - Brief lift (MFE 3.20) then reverse through stair low — failed continuation, stop exit −1R.
  - Even Asia/Off can trap when the stair is thin into supply or the day is already rolling over — session affinity is not a free pass.
- **Exit:** `orig_stop` (structure stop −1R).

### L07 — 2022-05-03 03:00:00 → 2022-05-03 04:30:00 | Asia | R=-1.0 | exit=`orig_stop`
- **Fill/close:** entry 1865.3 → exit 1862.34 (stop 1862.34). tape timestamps as-is (broker/server clock); session tags Asia/Lon/NY/Off on that clock — not converted ICT.
- **Idea:** Geometry proxy saw ~3-bar M15 ascending staircase (each bar higher high AND higher low) and went LONG at close 1865.30 for 3R continuation; structure stop under stair low 1862.34 (risk 2.96, ~2.9×ATR14).
- **H4/M15 context:** H4 drifting DOWN (~-18.8) — M15 stair is a counter-trend micro-pop H4 closes≈[1885.59, 1879.74, 1861.53, 1866.07, 1862.72, 1866.8]. ~5d net -32.2. MFE/MAE 1.8/-5.43.
- **Why idea invalid then:**
  - Prior ~5 sessions net down (-32.2) — stair printed into weakness, not a fresh up-regime.
  - H4 already leaning down; M15 stair was a local expand against the higher frame.
  - Brief lift (MFE 1.80) then reverse through stair low — failed continuation, stop exit −1R.
  - Even Asia/Off can trap when the stair is thin into supply or the day is already rolling over — session affinity is not a free pass.
- **Exit:** `orig_stop` (structure stop −1R).

### L08 — 2022-06-03 13:00:00 → 2022-06-03 15:15:00 | NY | R=-1.0 | exit=`orig_stop`
- **Fill/close:** entry 1865.84 → exit 1863.25 (stop 1863.25). tape timestamps as-is (broker/server clock); session tags Asia/Lon/NY/Off on that clock — not converted ICT.
- **Idea:** Geometry proxy saw ~3-bar M15 ascending staircase (each bar higher high AND higher low) and went LONG at close 1865.84 for 3R continuation; structure stop under stair low 1863.25 (risk 2.59, ~1.6×ATR14).
- **H4/M15 context:** H4 drifting DOWN (~-9.5) — M15 stair is a counter-trend micro-pop H4 closes≈[1867.79, 1868.08, 1873.25, 1867.86, 1864.83, 1858.33]. ~5d net +16.4. MFE/MAE 1.98/-3.32.
- **Why idea invalid then:**
  - Prior ~5 sessions net up (16.4) — with-trend backdrop.
  - H4 already leaning down; M15 stair was a local expand against the higher frame.
  - Brief lift (MFE 1.98) then reverse through stair low — failed continuation, stop exit −1R.
  - London/NY session: HARDEN wrap showed Lon+NY alone is where this proxy's multiyear hold geometry went soft (gross hold ~flat; Asia/Off carried the positive hold years). Not a cost story — session×idea affinity.
- **Exit:** `orig_stop` (structure stop −1R).

### L09 — 2022-07-04 05:15:00 → 2022-07-04 12:45:00 | Asia | R=-1.0 | exit=`orig_stop`
- **Fill/close:** entry 1810.06 → exit 1805.41 (stop 1805.41). tape timestamps as-is (broker/server clock); session tags Asia/Lon/NY/Off on that clock — not converted ICT.
- **Idea:** Geometry proxy saw ~3-bar M15 ascending staircase (each bar higher high AND higher low) and went LONG at close 1810.06 for 3R continuation; structure stop under stair low 1805.41 (risk 4.65, ~2.3×ATR14).
- **H4/M15 context:** H4 broadly expanding up (rising highs and rising lows) — higher-TF agrees with M15 stair idea H4 closes≈[1794.79, 1789.82, 1799.41, 1807.42, 1808.21, 1812.32]. ~5d net -20.2. MFE/MAE 4.14/-4.87.
- **Why idea invalid then:**
  - Prior ~5 sessions net down (-20.2) — stair printed into weakness, not a fresh up-regime.
  - H4 agreed with expand-up — idea had room on the higher frame.
  - Brief lift (MFE 4.14) then reverse through stair low — failed continuation, stop exit −1R.
  - Even Asia/Off can trap when the stair is thin into supply or the day is already rolling over — session affinity is not a free pass.
- **Exit:** `orig_stop` (structure stop −1R).

### L10 — 2022-08-17 21:30:00 → 2022-08-18 06:30:00 | Off_hours | R=-0.7744 | exit=`time_stop`
- **Fill/close:** entry 1769.03 → exit 1762.83 (stop 1761.02). tape timestamps as-is (broker/server clock); session tags Asia/Lon/NY/Off on that clock — not converted ICT.
- **Idea:** Geometry proxy saw ~3-bar M15 ascending staircase (each bar higher high AND higher low) and went LONG at close 1769.03 for 3R continuation; structure stop under stair low 1761.02 (risk 8.01, ~3.4×ATR14).
- **H4/M15 context:** H4 drifting DOWN (~-12.3) — M15 stair is a counter-trend micro-pop H4 closes≈[1774.72, 1778.61, 1775.12, 1771.51, 1762.5, 1762.4]. ~5d net -25.9. MFE/MAE 1.15/-7.09.
- **Why idea invalid then:**
  - Prior ~5 sessions net down (-25.9) — stair printed into weakness, not a fresh up-regime.
  - H4 already leaning down; M15 stair was a local expand against the higher frame.
  - Never reached 3R in 32 M15 bars (~8h); time_stop MTM -0.77R — idea stalled in range.
  - Even Asia/Off can trap when the stair is thin into supply or the day is already rolling over — session affinity is not a free pass.
- **Exit:** `time_stop` (time_stop MTM — no 3R in ~8h).

### L11 — 2022-09-26 10:15:00 → 2022-09-26 18:15:00 | London | R=-0.7396 | exit=`time_stop`
- **Fill/close:** entry 1648.43 → exit 1638.75 (stop 1635.34). tape timestamps as-is (broker/server clock); session tags Asia/Lon/NY/Off on that clock — not converted ICT.
- **Idea:** Geometry proxy saw ~3-bar M15 ascending staircase (each bar higher high AND higher low) and went LONG at close 1648.43 for 3R continuation; structure stop under stair low 1635.34 (risk 13.09, ~3.7×ATR14).
- **H4/M15 context:** H4 choppy/sideways — expanding-up idea has little higher-TF wind H4 closes≈[1646.14, 1646.23, 1643.97, 1627.82, 1635.39, 1646.48]. ~5d net -28.6. MFE/MAE 1.34/-12.22.
- **Why idea invalid then:**
  - Prior ~5 sessions net down (-28.6) — stair printed into weakness, not a fresh up-regime.
  - Never reached 3R in 32 M15 bars (~8h); time_stop MTM -0.74R — idea stalled in range.
  - London/NY session: HARDEN wrap showed Lon+NY alone is where this proxy's multiyear hold geometry went soft (gross hold ~flat; Asia/Off carried the positive hold years). Not a cost story — session×idea affinity.
- **Exit:** `time_stop` (time_stop MTM — no 3R in ~8h).

### L12 — 2022-12-27 17:30:00 → 2022-12-28 02:30:00 | NY | R=-0.8384 | exit=`time_stop`
- **Fill/close:** entry 1827.3 → exit 1810.9 (stop 1807.74). tape timestamps as-is (broker/server clock); session tags Asia/Lon/NY/Off on that clock — not converted ICT.
- **Idea:** Geometry proxy saw ~3-bar M15 ascending staircase (each bar higher high AND higher low) and went LONG at close 1827.30 for 3R continuation; structure stop under stair low 1807.74 (risk 19.56, ~4.9×ATR14).
- **H4/M15 context:** H4 broadly expanding up (rising highs and rising lows) — higher-TF agrees with M15 stair idea H4 closes≈[1798.0, 1804.5, 1805.81, 1808.59, 1806.48, 1813.73]. ~5d net +31.0. MFE/MAE 5.99/-17.72.
- **Why idea invalid then:**
  - Prior ~5 sessions net up (31.0) — with-trend backdrop.
  - H4 agreed with expand-up — idea had room on the higher frame.
  - Never reached 3R in 32 M15 bars (~8h); time_stop MTM -0.84R — idea stalled in range.
  - London/NY session: HARDEN wrap showed Lon+NY alone is where this proxy's multiyear hold geometry went soft (gross hold ~flat; Asia/Off carried the positive hold years). Not a cost story — session×idea affinity.
- **Exit:** `time_stop` (time_stop MTM — no 3R in ~8h).

---

## 2) Contrast — 3 winners from 2024/2025

What differed: **trend regime** (sustained gold up-years), often **Asia** continuation where micro-stairs were allowed to run, and H4/day backdrop not fighting the long as hard as 2022 London fades.

### W01 — 2024-01-03 01:30:00 → 2024-01-03 03:45:00 | Asia | R=3.0 | exit=`orig_tp`
- **Fill/close:** entry 2059.4 → exit 2062.53 (stop 2058.36).
- **Idea:** Geometry proxy saw ~proxy~4(not strict on OHLC snap)-bar M15 ascending staircase (each bar higher high AND higher low) and went LONG at close 2059.40 for 3R continuation; structure stop under stair low 2058.36 (risk 1.04, ~1.0×ATR14).
- **H4/M15 context:** H4 drifting DOWN (~-11.9) — M15 stair is a counter-trend micro-pop ~5d net +4.7.
- **What differed / why worked:**
  - H4 already leaning down; M15 stair was a local expand against the higher frame.
  - Price ran the full 3R before stop — true expansion follow-through.
  - Asia/Off session: same HARDEN wrap — this is where expanding-up proxy hold edge concentrated (quiet continuation / less two-way fade of micro-stairs).

### W02 — 2024-01-11 01:30:00 → 2024-01-11 08:30:00 | Asia | R=3.0 | exit=`orig_tp`
- **Fill/close:** entry 2026.42 → exit 2035.04 (stop 2023.55).
- **Idea:** Geometry proxy saw ~3-bar M15 ascending staircase (each bar higher high AND higher low) and went LONG at close 2026.42 for 3R continuation; structure stop under stair low 2023.55 (risk 2.87, ~2.0×ATR14).
- **H4/M15 context:** H4 choppy/sideways — expanding-up idea has little higher-TF wind ~5d net -5.7.
- **What differed / why worked:**
  - Prior ~5 sessions net down (-5.7) — stair printed into weakness, not a fresh up-regime.
  - Price ran the full 3R before stop — true expansion follow-through.
  - Asia/Off session: same HARDEN wrap — this is where expanding-up proxy hold edge concentrated (quiet continuation / less two-way fade of micro-stairs).

### W03 — 2025-02-10 06:00:00 → 2025-02-10 09:30:00 | Asia | R=3.0 | exit=`orig_tp`
- **Fill/close:** entry 2877.2 → exit 2892.42 (stop 2872.13).
- **Idea:** Geometry proxy saw ~3-bar M15 ascending staircase (each bar higher high AND higher low) and went LONG at close 2877.20 for 3R continuation; structure stop under stair low 2872.13 (risk 5.07, ~1.6×ATR14).
- **H4/M15 context:** H4 drifting up (~10.2 over 6 H4 bars) but not a clean expanding staircase ~5d net +75.9.
- **What differed / why worked:**
  - Prior ~5 sessions net up (75.9) — with-trend backdrop.
  - Price ran the full 3R before stop — true expansion follow-through.
  - Asia/Off session: same HARDEN wrap — this is where expanding-up proxy hold edge concentrated (quiet continuation / less two-way fade of micro-stairs).

---

## 3) WHO DECIDED

**Every sampled fill was decided by the geometry_proxy script ONLY (strict M15 ascending staircase → LONG at close; structure stop under stair low; 3R TP or 32-bar ~8h time_stop MTM on PRIMARY OHLC touch). Jev/alive/conf/S14/S15/CF/Dig/Choice/Score/regime/occupancy/NEWS were NOT consulted. HARDEN_V1 Lon+NY+ATR filters were NOT in the decision path — wrap-only research after the fact.**

### GTOS surfaces NOT consulted (explicit gap list)
- Jev / JEV_EVERYWHERE (no jev surface at entry)
- alive / keep-alive bit
- confidence_gate / conf_gate (S15 shadow)
- S14 pack / S15 cost-matrix / S16 stack decision surfaces
- CF_D / CF_E / any CF variant (CF PAUSED)
- Choice / Score / Noul / warroom_shadow fanout fields
- Dig pocket / stand_down actuators
- occupancy / corr_hold / regime_tag calibrated live writers
- NEWS_PROTOCOL / event stamps (not consulted for these multiyear proxy fills)
- Challenge affinity scoreboard n (Challenge week is language-only here; multiyear PRIMARY is the tape)
- broker book / live fill engine (geometry_proxy OHLC touch only)
- Lon+NY+ATR HARDEN_V1 filter as a live decision (HARDEN is wrap/research only — not who decided these trades)

---

## 4) Validity rule (owner-care; NOT a cost gate)

The expanding-up staircase idea is valid when a short M15 run of higher highs AND higher lows is a continuation print inside an already-accepting up context — typically quiet Asia/Off hours where the micro-stair is not immediately two-way faded, H4 is not leaning against the long, and the prior few sessions are not already in a clear down-slide. It is a trap when the same local stair prints as a counter-trend pop into London/NY two-way liquidity, or into a day/week that is already rolling over: the geometry_proxy still fires (HH+HL is true on M15), but there is no higher-frame wind and the stair low is an easy stop. HARDEN_V1 wrap (research only) showed Lon+NY alone is where this proxy's hold years went soft on gross geometry, while Asia/Off carried the positive hold years — that is session×idea affinity, not a cost gate. Validity is about idea vs context vs who decided; it does NOT gate on round-turn cost, pip haircuts, or n-filter scoreboards.

---

## Lessons (plain)

1. 2022 was a regime miss for expanding-up on XAU: many M15 stairs printed into weakness / H4 chop or down-drift; London alone ≈ −18.7R gross that year.
2. 2023 gross sumR was still >0 (+9.5R) — soft vs 2024/25 but NOT a negative year on idea P&L; do not re-label it negative via cost stress.
3. 2024–2025 winners differ by trend regime (sustained up years) and often Asia/Off continuation where micro-stairs were not immediately faded.
4. HARDEN wrap: Lon+NY alone softened hold geometry; Asia/Off carried positive hold years — autopsy honesty, not a license to chase more n-filters.
5. Who decided is geometry_proxy only — GTOS judgment surfaces were gaps, so losers are idea/context failures of the proxy, not failed Jev/conf gates.

---

## Candle gaps

- Tape bars: **293197** (2014-01-02 09:00:00 → 2026-06-17 07:45:00)
- Gaps >60m: **3214** (weekday overnight class ≈2469; weekend ≥48h ≈650)
- Daily ~75m rollover holes + weekend gaps are normal on this FX/metal tape; not blamed as primary 2022 miss mechanism.
- H4: synthesized from M15 (no native XAUUSD_H4.csv found under audit-merge/markets/tapes)

---

## Paths

- MD: `/workspace/gtos/close_loop/war_room_20260920/EXPANDING_WHY_NEGATIVE_YEARS_20260920.md`
- JSON: `/workspace/gtos/close_loop/war_room_20260920/EXPANDING_WHY_NEGATIVE_YEARS_20260920.json`
- Blotter: `/workspace/gtos/research/warroom_20260920/multiyear/blotter_PRIMARY_XAUUSD_dsp_expanding_up_staircase.jsonl`
- HARDEN wrap: `EXPANDING_HARDEN_V1_20260920.md` / `.json`

**place=false. No spring revive. CF PAUSED. No n-optimize.**
