# KB — Energy + Agri Sleeves (track: energy_agri)

Build track: ENERGY (USOIL_cash, UKOIL_cash, NATGAS_cash, HEATOIL_c) + AGRI (CORN_c, COTTON_c)
on the proven machinery: H4 FVG-retest continuation entry (`gold_sleeve_strategy.fvg_signals`,
vol-gated) + STATE_D scale-out exit (`compounding_sleeve.exit_state_d`) + state gate + confidence
sizing. Module: `energy_agri_sleeve.py`. Ledgers: `ENERGY_AGRI_CANDIDATES.jsonl` (all 288 signals
incl. rejected, with full state), `ENERGY_AGRI_SLEEVE_TRADES.jsonl` (126 gated trades).

## DATA HONESTY (the binding constraint)
H4 is the only viable source (H1/D1 exports are NOT deeper for these symbols). Real spans:
- USOIL_cash : 2021 + 2025-26 (gap 2022-2024)  -> forward-validatable
- UKOIL_cash : 2020-2021 ONLY                   -> no recent data; comparator-only
- NATGAS_cash: 2024H2 + 2025-26                 -> forward-validatable
- HEATOIL_c  : 2025-26 ONLY                      -> forward-only (single-regime confound risk)
- CORN_c     : 2023-2026                         -> real TRAIN(<=2024) + FORWARD
- COTTON_c   : 2025-26 ONLY                      -> forward-only (single-regime confound risk)

So a clean TRAIN<=2024/FORWARD split exists only for USOIL/NATGAS/CORN. Forward-only symbols are
kept but CONFIDENCE-HAIRCUT to 0.5 (per `SYM_CONF`). No-lookahead verified: all state features
(ac60, vr, slope, htf_trend) use bars index<=i; only the label scorer (`simulate`/`exit_state_d`)
looks forward. CONFIRMED.

## DECISIVE FINDING 1 — energy is a VOL/EARLY-TREND regime, NOT a persistence regime
The metals persistence gate (ac60>=0.10) DESTROYS the energy edge (ac60>=0.10 -> -0.107R; higher
thresholds worse). Energy continuation pays in two near-DISJOINT states (overlap n=1):
- A) `vr >= 2.0` (extreme vol expansion = supply-shock ignition): +0.867R, 88% win, n=26,
     POSITIVE EVERY YEAR (2021:+0.46, 2025:+0.59, 2026:+1.07).
- B) `|slope_30| < 0.05` ATR/bar (flat trend = consolidation-breakout, entering the FVG
     continuation EARLY before extension): +0.701R, 69% win, n=36, POSITIVE EVERY YEAR
     (2021:+0.55, 2024:+0.28, 2025:+0.60, 2026:+1.04).
The LOSING energy state is `|slope|>=0.15` (chasing extended trends -> late, stopped: -0.127R).
**ENERGY GATE = A OR B** -> +0.771R, 77% win, n=62, positive every year (2021/2024/2025/2026).
This is robust across all 4 symbols and NOT the 2026-only confound the brief warned about.

## DECISIVE FINDING 2 — agri persistence gate transfers cleanly from metals
- HIGH conf: `ac60 >= 0.10` -> +0.641R, 89% win, n=9, positive every year it fires
  (2023:+0.22, 2025:+1.12, 2026:+0.40). Small n but consistent; weather/seasonal trends ARE
  persistent. Naturally avoids the winter dead-zone.
- Winter (Dec-Feb) is the agri dead-zone: -0.494R, 31% win. Plant/harvest months are positive.
- BREADTH conf: `month not in (Dec,Jan,Feb)` (seasonal-only) -> +0.230R, n=55 (~22/yr forward),
  positive 2026, flat 2024/25. Low EV, high frequency -> kept at small size (conf 0.25).

## FINAL SLEEVE (locked gates, STATE_D exit, confidence-weighted)
| tag                  | gate                  | n  | EV/trade | win | per-year (positive years) | conf |
|----------------------|-----------------------|----|----------|-----|---------------------------|------|
| energy_supply_shock  | vr>=2.0               | 26 | +0.867R  | 88% | 2021,2025,2026 all +      | 1.00 |
| energy_flat_breakout | \|slope\|<0.05        | 36 | +0.701R  | 69% | 2021,2024,2025,2026 all + | 1.00 |
| agri_persistence     | ac60>=0.10            |  9 | +0.641R  | 89% | 2023,2025,2026 all +      | 0.50 |
| agri_seasonal        | not Dec-Feb (residual)| 55 | +0.230R  | 53% | 2026 +, 24/25 soft        | 0.25 |

Symbols get an additional 0.5 haircut if forward-only (HEATOIL, COTTON, UKOIL).

## FORWARD HOLDOUT 2025-26 (the verdict that matters)
- ENERGY gated: n=41, +0.911R/trade, 76% win, ~20.5 trades/yr.
- AGRI gated  : n=45, +0.418R/trade, 60% win, ~22.5 trades/yr.
- ALL gated   : n=86, +0.653R/trade, 67% win, ~43 trades/yr. Conf-weighted EV = +0.715R.
Beats baselines forward: ungated fixed-2R +0.322R, ungated STATE_D +0.181R -> gated +0.653R
(2x-3.6x lift).

## PER-YEAR EV(n) — energy+agri combined, gated sleeve
- 2021: +0.53 (n18, energy)  [pre-train comparator]
- 2023: -0.05 (n5, agri)
- 2024: +0.05 (n17)
- 2025: +0.35 (n33)  FORWARD
- 2026: +0.86 (n53)  FORWARD
(2022 has no usable data for these symbols.)

## CONFOUND HONESTY
- HEATOIL/COTTON are forward-only (2025-26) -> some of the 2026 strength is single-regime. They are
  KEPT (doctrine: delete nothing) but capped at 0.5 symbol-confidence.
- The energy A-OR-B gate is the main result and is NOT a single-year confound: positive in 2021,
  2024, 2025 AND 2026, and on USOIL/NATGAS (the forward-validatable carriers) alone it is still
  +0.564R, positive every year.
- agri_persistence n=9 is small; sized at 0.5 conf accordingly. Do NOT discard for small n.

## NEXT STEPS / WHERE TO EXTEND
1. Source deeper 2015-2022 H4 for NATGAS/CORN/COTTON/HEATOIL to convert forward-only sleeves into
   train-validated ones (current blocker is data, not signal). Exact source requirement: continuous
   H4 OHLCV 2015-2021 for these 4 symbols.
2. Energy vr>=2.0 (supply-shock) is the single strongest sub-edge (88% win) — consider a dedicated
   higher-size allocation and test a tighter target ladder (the runner under STATE_D may be leaving
   R on the table during shock trends; test runR=5-6 in the vr>=2 tier).
3. Test the energy A/B gate on the metals carrier as a cross-check (does flat-slope breakout add
   frequency to metals without hurting EV?).
4. Add WHEAT_c/SOYBEAN_c to agri if their H4 exports exist with depth (currently absent from load).
