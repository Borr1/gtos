# KB7 — Stale/conservative-assumption drag audit (UNLEASH wave)

Track: audit every static/conservative assumption for drag; quantify in R; loosen where the data
holds FORWARD; map-don't-kill. Objective shift: optimize for MAX growth-rate / speed-to-target
subject to FTMO (5% daily, 10% maxDD), keeping the ONE real guardrail (P(maxDD)/P(ruin) bounded).

Method: reproduced the LOCKED clean_3 deploy series byte-for-byte from the cached streams
(`INTEG_W3_streams_cache.pkl` + `INTEG_W5_new_streams_cache.pkl`) — n_days 1679, mean 0.09127,
std 0.5997, vol_scale 0.9481, MC vm@1% 0.99905, stress@1.5%vm 0.7093 — all match
`INTEG_W5_CLEAN3_DEPLOY.json`. All sweeps use the locked W2 MC engine (build_matrix / mc_series /
joint_pass_mc; TARGET .08 / MAXDD .10 / DAILY .05 / BLOCK 5 / N 20000) and geometry_lib +
cs.exit_state_d (leak-free). TRAIN<=2024 chooses, FWD 2025-26 confirms, per-year reported.

## HEADLINE VERDICT

| stale assumption | drag found | loosen? | forward-validated |
|---|---|---|---|
| (a) cost map staleness | **already de-conservatized** (proxy overcharged 2-4x; banked +0.07..+0.13R/trade). Residual to zero-cost only +0.04..0.05R. Deployed value honest vs tick. | **NO further loosen** — already optimal & tick-honest | yes |
| (b) correlated-risk-unit concentration cap | **REAL growth drag.** Mean-pooling treats same-day same-sleeve trades as corr=1; binds on 40-81% of trade-days. | **YES — adopt sqrt-N partial pooling** | yes, per-year + stress |
| (c) pessimistic same-bar stop-wins | **negligible** (0% on metals_core; 0.005-0.015R on H4 breadth sleeves). | NO (already handled at tick in EXEC_REALISM) | yes |
| (d) static gate thresholds / ATR floors | metals GATE_K=1.2 and crypto ac60=0.15 are **TRAIN+FWD optimal**; ATR floor is **inert**; metals ac60=0.10 is a deliberate freq/EV knob. | mostly NO; one optional max-growth knob | yes |
| (e) maxbars=80 force-close | **real +0.07/+0.04/+0.19R drag on the pure-H4 / standalone-package path** (force-closes 10.7% metals / 6% energy / 19% crypto). **BUT the deployed CASCADE book has already escaped it** (every would-be-force-closed trade is cascade-filled on a longer LTF horizon or resolved <bar80; book-level delta = 0.000R, verified). | only for the LIVE-PACKAGE H4 fallback default (raise to 240) | yes (per-year monotone) |
| (bonus) winsor cap [-1.3,+5] | **fully inert on carriers** — raw R ranges metals [-1.05,+2.70] / energy [-1.04,+2.71] / crypto [-1.10,+3.91]; ZERO trades clip either cap. | NO (no drag exists) | yes |

The single actionable win is **(b) sqrt-N concentration pooling**: a free improvement on the binding
1.5x-stress constraint at matched risk, or ~27% faster speed-to-target at fixed nominal size.

---

## (a) COST MAP STALENESS — already de-conservatized; deployed value is tick-honest

`ULTIMATE_REAL_COST_MAP.json` (fx .160 / jpy .115 / index .064 / metals .046 / energy .037; global
median .095, n 1522) was committed 2026-06-13 (`450a275f8`) replacing the flat 0.17 proxy that
"overcharged 2-4x on metals/index/energy." So the cost de-conservatism is ALREADY banked.

Re-derivation check: the 247 `*_SIMULATED_TRADE_LEDGER.jsonl` (Jul-25..May-26) carry an
`expected_cost_r` CLAMPED at 0.18 (the old proxy ceiling) — they are NOT the source of the deployed
map and are stale-high, not the live values. The deployed map's lower values came from real filled
trades (the commit) and are confirmed honest by tick:

Cost sensitivity on the 3 EV-carriers (FWD EV/trade):

| carrier | deployed | x0.5 | x1.5 | x2.0 | 0.17 proxy | zero |
|---|---|---|---|---|---|---|
| metals_core | +0.865 | +0.888 | +0.843 | +0.820 | +0.741 | +0.911 |
| crypto | +0.751 | +0.799 | +0.703 | +0.656 | +0.676 | +0.846 |
| energy | +0.211 | +0.230 | +0.193 | +0.174 | +0.079 | +0.249 |

- The cost de-conservatism already banked **+0.124R (metals), +0.075R (crypto), +0.132R (energy)**
  vs the old 0.17 proxy. Residual headroom to zero cost is small (+0.05/+0.10/+0.04R) — cost is a
  minor term for these wide-stop sleeves.
- **Tick cross-check (the honest test).** `ULTIMATE_TICK_SPREAD_GOLD.json` (1.29M XAUUSD ticks,
  Oct-25..Apr-26): spread_price median 0.37, p90 0.67, p99 1.17. At the ACTUAL deployed metals stop
  distance (median 12.24 price = 1.11xATR), round-trip R-cost = 0.030 (1x median) / 0.055 (1x p90) /
  0.060 (2x median) / 0.110 (2x p90). **The deployed metals cost 0.0459 sits between tick-1x-median
  and 2x-p90 — honest and mildly conservative** (covers spread widening on most fills).
- VERDICT: do NOT lower further. Lowering metals to tick-median (~0.030) would add only ~+0.016R/trade
  while removing the news/rollover-widening buffer. **Map-don't-kill: keep the deployed map.**

## (b) CONCENTRATION CAP — the real growth drag; sqrt-N pooling is the win

Deployed rule (gold_sleeve.backtest, INTEG build_matrix): all same-day same-sleeve trades pooled into
ONE risk unit at MEAN R (i.e. treated as perfectly correlated, corr=1 within class). It binds hard:

| sleeve | trade-days | multi-trade days | max/day | trades on multi-days |
|---|---|---|---|---|
| metals_core | 65 | 27 (42%) | 10 | 93/131 |
| crypto | 67 | 27 (40%) | 4 | 64/104 |
| energy_agri | 105 | 43 (41%) | 4 | 100/162 |
| idxrev | 1536 | 1241 (81%) | 19 | 6178/6473 |

Mean-pooling is too conservative: same-day same-sleeve trades are correlated but NOT identical, so the
fair credit is partial (effective N = sqrt(n)), not zero. Book-level MC (locked engine), pooling rules:

VOL-MATCHED (same daily-std budget — apples-to-apples):

| mode | sharpe | stress@1% | stress@1.5% | vm@1% pass |
|---|---|---|---|---|
| mean (DEPLOYED) | 0.1522 | 79.73% | 70.03% | 99.78% |
| **sqrtN** | **0.1550** | **81.95%** | **71.92%** | **99.89%** |
| pool_k2 | 0.1416 | 74.61% | 66.09% | 99.66% |
| pool_k3 | 0.1464 | 75.70% | 66.62% | 99.76% |

RAW (fixed nominal size — true speed-to-target):

| mode | @1% pass | @1% days | @0.75% days | worst-day@1% | breach@1% |
|---|---|---|---|---|---|
| mean | 99.78% | 85 | 113 | -2.020% | 0.000% |
| **sqrtN** | 99.26% | **62 (-27%)** | **82 (-27%)** | -2.142% | 0.000% |

Forward-only (sqrtN, the growth metric): FWD @1% median **20 days vs 28** (deployed); @0.75% **26 vs 37**.

Guardrail check (sqrtN, raw nominal): daily-breach stays **0.000% through 2.0%** (worst-day -4.28% < -5%
limit); P(maxDD) only becomes material at 2.5%+ (13.4% vs 7.8% deployed). Right-tail best-day +8.5
vs +5.1 — sqrt-N recaptures the multi-trade winning days the cap was crushing.

- **VERDICT: adopt sqrt-N partial pooling.** At a matched risk budget it STRICTLY dominates the
  deployed mean-pooling on the binding 1.5x-stress constraint (+1.9..+2.2pp) with equal/lower maxDD.
  Under the max-growth objective at fixed nominal size it is ~27% faster to target with daily-breach
  still mechanically 0% and worst-day far inside the -5% limit. Hard caps (k2/k3) are WORSE — keep
  the smooth sqrt-N rule. (Cross-sleeve diversification credit is untouched — only the WITHIN-sleeve
  same-day correlation assumption is relaxed from 1.0 to 1/sqrt(n).)

## (c) PESSIMISTIC SAME-BAR STOP-WINS — negligible at H4; already tick-handled

geometry_lib.simulate returns the STOP on any bar where both stop and target are touched. Measured
same-bar ambiguity frequency and the pess->neutral(50/50) EV drag on every geometry family:

| sleeve geometry | n | same-bar ambig % | pess->neutral drag/trade |
|---|---|---|---|
| metals_core (2R, struct stop ~1.1xATR) | 131 | **0.0%** | **+0.0000** |
| idxrev (1.5xATR stop, 0.75R tgt) | 5798 | 0.60% | +0.0053 |
| energy fvg (2R) | 402 | 1.00% | +0.0149 |
| jpy tight 1xATR (2R) | 12696 | 0.50% | +0.0074 |

H4 bars rarely span both a stop and a far target, so the pessimism almost never triggers; where it
does it is <=0.015R and on low-conf breadth sleeves. A neutral convention would recover at most HALF
of even that. The honest resolution is M1/tick — already done in EXEC_REALISM (book -5.6%, which
INCLUDES per-M1-bar adverse-before-favorable pessimism). VERDICT: keep pessimistic same-bar; not a drag.

## (d) STATIC GATES / ATR FLOORS — mostly TRAIN+FWD optimal; one optional max-growth knob

ac60 threshold (TRAIN<=24 chooses, FWD confirms):

| metals_core ac60 | TRAIN EV(n) | FWD EV(n) | crypto ac60 | TRAIN EV(n) | FWD EV(n) |
|---|---|---|---|---|---|
| >=0.05 | +0.337(108) | +0.599(84) | >=0.10 | +0.238(19) | +0.584(109) |
| **>=0.10 (deployed)** | +0.298(82) | +0.865(49) | **>=0.15 (deployed)** | **+1.138(8)** | +0.751(60) |
| >=0.15 | +0.389(59) | +1.101(30) | >=0.20 | +0.571(3) | +0.854(32) |
| >=0.20 | +0.245(27) | +1.771(9) | >=0.25 | -1.095(2) | +0.633(11) |

- crypto ac60=0.15 is the TRAIN peak (+1.14) — **deployed gate is correct; loosening to 0.10 halves
  TRAIN. Do NOT loosen.**
- metals ac60=0.10 is a deliberate FREQ/EV knob: tighter (0.15/0.20) raises FWD EV/trade monotonically
  but cuts frequency (n49->30->9); TRAIN does not clearly support tightening (0.389 vs 0.298 at n59 is
  within noise). Looser (0.05) adds +60% trades at FWD +0.599. Under MAX-GROWTH, the metals_softband
  sleeve (0.04<=ac60<0.10) already harvests the looser band at confidence-size — so the frequency is
  not lost, it is sized down. **Keep 0.10 hard / softband for 0.04-0.10; the structure is already a
  growth-aware ramp, not a binary cliff.**

GATE_K (ATR-expansion gate):
- metals deployed 1.2 is the TRAIN peak (+0.298) AND FWD peak (+0.865); 1.3+ falls off both.
  **Optimal — keep.**
- energy 1.2 has negative TRAIN (-0.21, positive only forward); GATE_K=1.5 flips TRAIN positive
  (+0.032) at lower freq. Energy's gate is arguably too LOOSE (a tightening, not a loosening) — flagged
  for the integrator, but energy's forward EV (+0.21) holds at 1.2 so it is not urgent.

ATR_STOP_FLOOR (deployed 0.25): **inert** — structural stops dominate; floor essentially never binds
(identical EV at 0.10..0.50). Not a drag, not a lever.

## (bonus) WINSOR CAP [-1.3,+5] — inert on the deployed carriers

No trade in metals_core / crypto / energy_agri reaches +5R: deployed exits cap payoff below it
(STATE_D max ~2.75R/leg; crypto fixed 4R target). Crypto EV identical at cap +5/+8/+12/+inf. The +5
winsor removes ZERO EV on the deployed book — the EXIT geometry, not the winsor, is the payoff bound.
(If a future sleeve uses an open-ended trail this would matter; for clean_3 it is a no-op.)

## (e) MAXBARS=80 FORCE-CLOSE — real on the H4/standalone path; ALREADY NEUTRALIZED in the deployed cascade book (UNLEASH-wave addition)

`geometry_lib.simulate` and `cs.exit_state_d` force-close at `maxbars=80` H4 bars (~13 trading days),
booking the bar-`end` close as `market_close` / `win_partial` / `partial_flat`. Drag #3 in the
known-drags list; NOT examined in the prior pass. Swept maxbars {80,120,160,240,400} per carrier on
the PURE-H4 STATE_D path (entries held fixed -> no lookahead, forward-only labels):

| carrier | force-close% @80 | FWD EV @80 | FWD EV @240 | TRAIN @80 -> @240 | per-year @240 |
|---|---|---|---|---|---|
| metals_core (H4-pure) | 10.7% | +0.865 | **+0.939 (+0.074)** | +0.298 -> +0.303 (flat, not overfit) | 2025 1.096->1.246, 2026 0.644 flat, every yr flat-or-better |
| energy (H4-pure) | 6.0% | +0.211 | **+0.253 (+0.042)** | -0.210 -> -0.168 (improves) | every year flat-or-better; 2022 -0.203->-0.062 |
| crypto (H4-pure) | 19.1% | +0.751 | **+0.943 (+0.192)** | noisy (n8 TRAIN); 400 overfits | BOTH fwd yrs up: 2025 .747->.943, 2026 .762->.944 |

The per-trade signal is honest, monotone TRAIN+FWD up to ~240, and broad across years (not a single
regime). Cap crypto at ~160-240 (the 400-bar TRAIN spike with FWD drop is the overfit edge).

**BUT the deployed clean_3 book does NOT carry this drag.** Forensic match against the cached deploy
streams (`INTEG_W3_streams_cache.pkl`):
- metals_core: **0/131** deployed rows equal the H4-base@80 label — ALL 131 are H1->M15 cascade-filled
  (maxbars 320/1280, a much longer horizon). Deployed metals_core = **+0.887 ALL / +1.235 FWD**, which
  is ABOVE even H4@240 (+0.541/+0.939): the cascade better-fill exit already dominates the maxbars term.
- energy: 20/84 energy rows match H4-base@80, crypto: 46/68 BTC/DASH rows match — but **0 of those
  matched rows CHANGE when maxbars->240** (they exited before bar 80; the force-closed trades are the
  cascade/ledger rows with a different, longer-horizon label). Re-labeling the deployed carrier streams
  at maxbars=240 and re-running the LOCKED MC: series **byte-identical** (mean 0.09127, sharpe 0.1522);
  raw/vol-matched/stress/days/breach ALL unchanged. **Book-level maxbars drag = 0.000R.**
- VERDICT: maxbars=80 is a real drag ONLY on a pure-H4 / non-cascade deployment. The deployed cascade
  book has structurally escaped it. **Actionable scope is narrow: raise the standalone deployable
  module's H4-fallback default (`ultimate_book_live_package.label_intent_R` maxbars=80) to ~240** so a
  live non-cascade fill matches the cascade horizon and recaptures the +0.04..0.19R on fallback fills.
  Map-don't-kill: keep the cascade as the primary exit (it already beats every maxbars setting).

## RECOMMENDATION TO INTEGRATOR

1. **ADOPT sqrt-N within-sleeve same-day pooling** (replace mean-pooling in build_matrix /
   gold_sleeve.backtest). Free win on the binding 1.5x-stress at matched risk; ~27% faster
   speed-to-target at fixed size; guardrail intact (0% daily breach <=2%, worst-day inside -5%).
2. **Keep the cost map** (already de-conservatized + tick-honest), the gates (TRAIN+FWD optimal),
   the same-bar convention (negligible, tick-handled), and the winsor cap (fully inert, zero clips).
3. **Raise the LIVE-PACKAGE H4-fallback maxbars 80 -> 240** (`ultimate_book_live_package.label_intent_R`
   default; the H4-fallback path in `INTEG_portfolio_build.gen_metals_core` and `cs.exit_state_d`).
   Recaptures +0.04..0.19R/trade on any non-cascade fill (forward-validated, monotone). The deployed
   CASCADE book is unaffected (drag already 0 there) — this is purely live-robustness so a missed-LTF
   fallback fill doesn't get force-closed prematurely. Keep cascade as primary exit.
4. Optional: re-examine energy GATE_K (currently TRAIN-negative at 1.2) — a tightening to ~1.5
   improves TRAIN sign at lower freq; not a max-growth lever, a robustness note.

## FILES
- `STALE_carrier_sensitivity.py` (+ `_RESULT.json`) — cost & gate sweeps on the 3 EV-carriers.
- `STALE_concentration_mc.py` (+ `_RESULT.json`) — concentration-pooling book-level MC (locked engine).
- `STALE_maxbars_winsor.py` (+ `_RESULT.json`) — maxbars {80..400} force-close sweep + winsor inertness
  (UNLEASH addition; per-carrier, per-year, TRAIN/FWD).
- `STALE_maxbars_book_mc.py` (+ `_RESULT.json`) — BOOK-level maxbars re-label test in the LOCKED MC;
  proves deployed cascade book has 0.000R maxbars drag (exposure forensics included).
- (the clean_3 deploy series is reproduced inline from `INTEG_W3_streams_cache.pkl` +
  `INTEG_W5_new_streams_cache.pkl` by both MC scripts; matches `INTEG_W5_CLEAN3_DEPLOY.json`
  mean 0.09127 / std 0.5997 / sharpe 0.1522 byte-for-byte.)
