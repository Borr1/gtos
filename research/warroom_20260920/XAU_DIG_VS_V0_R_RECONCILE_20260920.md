# XAU Dig 3R-structure vs V0 1R — R reconcile — 2026-09-20

**Generated:** 2026-09-20 14:33 ICT (Asia/Bangkok)  
**Mode:** SHADOW · research_only · `place: false` · `ready_for_key_fx: false` · APPLY unset  
**Lane:** XAU spring PRIMARY (expanding / three_fresh brief) · harden PARKED untouched  
**Owner LAW:** cost never kill-gate · instrument×sleeve affinity · no NEWS invent · no APPLY · Jev never places

## 1. One-paragraph mechanism

Dig spring HOLD is positive (+54.44R, WR≈29%) only because the payoff book is asymmetric: losers are almost all orig_stop at −1R while a minority of winners print orig_tp at +3R (372×3=+1116R) plus positive time_stop MTM (+136R), clearing the 3:1 breakeven (~25% WR) by ~4pp. V0 1R truncates every winner at +1R on a denser ATR-filtered next_open L20 universe (n=3114, WR≈49%), so the same idea class sits just under 1:1 breakeven and FAIL (−56.93). Apples-to-apples proof: rescoring the identical Dig PRIMARY blotter entries under a 1R TP horizon collapses HOLD to −732.6R without changing WR — Dig PASS is win-skew / TP-horizon, not a higher hit-rate. Cost is not the kill-gate; Challenge KEEP spring 291794419 realised_r_unit150=+3.02 on time_stop with wide orig_tp, so Dig 3R-structure matches payout-path R units while V0 1R is a research stress disclosure.

## 2. Model contrast

| dimension | Dig 3R-structure (PRIMARY blotter) | V0 1R harness |
|---|---|---|
| TP horizon | **+3R** orig_tp or 32-bar time_stop MTM | **+1R** hard cap or 32-bar time_stop |
| Stop | structure / signal low → **−1R** | signal_bar_low → **−1R** |
| R-unit | price_move / abs(entry−stop) (Challenge `realised_r_unit150`) | same denom; TP forced to 1×risk |
| ATR filter | OFF | ON (0.5–3× ATR14) |
| Entry | DSP-named signal path | next_open L20 minimal |
| Spring HOLD | n=1727 · WR **29.07%** · sumR **+54.44 PASS** | n=3114 · WR **49.29%** · sumR **−56.93 FAIL** |

## 3. Same-blotter rescore (Dig entries → 1R horizon)

Method (conservative, stop-before-tp): `orig_tp`→+1.0; `orig_stop`→−1.0; `time_stop` if R≥1→+1.0 else keep MTM.

| sleeve | Dig 3R HOLD sumR | Dig→1R HOLD sumR | Δ | Dig HOLD WR | gate flip |
|---|---:|---:|---:|---:|---|
| **spring** | **+54.44** | **−732.59** | −787.03 | 0.2907 | PASS→**FAIL** |
| expanding | +102.67 | −354.85 | −457.52 | 0.3872 | PASS→**FAIL** |
| three_fresh | +155.51 | −768.18 | −923.70 | 0.3545 | PASS→**FAIL** |

Spring HOLD contribution under Dig 3R: stop **−1198** + tp3R **+1116** + time_stop **+136.44** = **+54.44**.  
Breakeven WR: 3:1 ≈ **25%** (Dig clears by ~4pp) vs 1:1 = **50%** (Dig WR 29% fails badly; V0 WR 49.3% fails thinly).

Universe caveat: Dig n≠V0 n (1727 vs 3114) — primary proof is **self-rescore of Dig blotter**, not claiming row-identical V0↔Dig.

## 4. Challenge-true evidence (payout path)

| ticket | sleeve | exit | realised_r_unit150 | geometry note |
|---|---|---|---:|---|
| 291794419 | dsp_spring_close | time_stop | **+3.02** | SL 4296.43 / TP 4364.58 / exit 4327.91 — KEEP |
| 292885676 | dsp_expanding_up_staircase | time_stop | **+2.99** | wide orig_tp; time_stop win mass |
| losers (three_fresh etc.) | — | orig_stop | **≈−1.0** | full structure stop |

Challenge book pays ~**3R** on surviving KEEP XAU structure wins and **−1R** on orig_stop — Dig 3R-structure is the matching R model; V0 1R is not how the Challenge writer scores tickets.

## 5. Chair LABEL only (no APPLY / no place)

| question | Chair label |
|---|---|
| Which R model is **Challenge-true for payout path**? | **`dig_3R_structure`** — Monday SHADOW / Challenge-true scoreboard |
| Which stays **research disclosure**? | **`v0_1R`** — honesty stress; Dig PASS is skew-dependent |
| Affinity spring | **KEEP_RESEARCH** (unchanged) |
| Expanding / spring harden | **PARKED** (unchanged) |
| **Monday-ready** | **NO** |
| APPLY / place | **unset / false** |

Trust for Monday shadow scoring: Dig 3R-structure (report V0 1R alongside as stress). Do not flip APPLY. Do not promote on Dig PASS alone while 1R stress FAILS. Cost never kill-gate — this is idea-validity / R-horizon, not friction.

## 6. Artifacts

- This pack: `XAU_DIG_VS_V0_R_RECONCILE_20260920.{md,json}`
- Dig blotters: `multiyear/blotter_PRIMARY_XAUUSD_dsp_*.jsonl`
- V0: `multiyear/MULTIYEAR_POSITIVE_V0.*` · `run_spring_v0.py`
- Prior: `XAU_SPRING_WHY_AUTOPSY_20260920.*` · affinity stamp · MULTIYEAR_POSITIVE_PLAN/REPLAY

Numbers from on-box blotters + Challenge learning_scoreboard_60. Never fabricated. place=false.
