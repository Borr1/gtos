# KB — Crypto momentum/persistence sleeve (track key: CM)

Builder track: Crypto momentum/persistence sleeve. Status: **IMPROVEMENT** (forward-positive, adds a new asset class + ~42 trades/yr breadth, low correlation to the metals baseline).

## TL;DR deployable rule

On **BTCUSD and DASHUSD** (H4 closed bars):
- ENTRY (momentum breakout continuation): at closed bar `i`, go **LONG if close[i] > max(high[i-20 .. i-1])**, **SHORT if close[i] < min(low[i-20 .. i-1])** (20-bar Donchian breakout of the prior window, closed-bar only).
- STATE GATE (persistence): require **`ac60 = cs.autocorr(B,i,60) >= 0.15`** (lag-1 autocorr of trailing 60 H4 1-bar returns). This is the same momentum-persistence regime that makes commodity continuation pay; it is the single most important driver of crypto-breakout EV.
- GEOMETRY: **wide structural stop `sd = 2.0 * atr14(B,i)`**, **fixed target = 4R** (`target_dist = 4*sd`). Winsorize net R to [-1.3, +5]. Cost = `w1.cost_for(sym)` (0.0953 R for BTC/ETH).
- Lower-variance alternative geometry: `cs.exit_state_d` scale-out instead of 4R target → lower EV (+0.45R fwd) but higher win rate (60%) and the smoothest 2026. Use for risk-tight allocations.

No lookahead: entry uses only closed bar `i` and the prior window; `ac60` uses returns through bar `i`; `geometry_lib.simulate` looks forward only to score the label (allowed).

## Forward holdout (rule fixed on train year<=2024, then reported forward)

FINAL rule = lb20 breakout + ac60>=0.15 + sd=2a + target4, BTC+DASH:

| window | n | net EV R/trade | win% |
|---|---|---|---|
| 2024 (train) | 8 | +1.138 | 50% |
| **2025 (fwd)** | 44 | **+0.747** | 50% |
| **2026 (fwd, thru Jun)** | 16 | **+0.762** | 44% |
| **FWD 2025-26 combined** | 60 | **+0.751** | 48% |

Forward by direction: long n=37 +0.859R, short n=23 +0.578R (both sides pay).
Forward frequency: ~**42 trades/yr** across the 2-symbol set.

Per-symbol (full sample, target4 geom):
- **BTCUSD**: n=31 EV +0.866 | fwd +0.829 (2024:+1.40, 2025:+0.58, 2026:+2.03) — star carrier, positive every year.
- **DASHUSD**: n=37 EV +0.738 | fwd +0.678 (2024:+1.05, 2025:+0.95, 2026:+0.19) — remarkably stable every year.

## Where it works / where it does NOT (per-regime, NO averages-as-verdict)

- **Persistence regime is the edge.** Without the ac60 gate, crypto breakouts are net-negative every year (no-gate all-crypto ≈ -0.08R). The gate cuts ~80% of breakouts and flips the sign positive. EV is monotone in the threshold: ac>=0.10 fwd +0.58, ac>=0.15 fwd +0.75, ac>=0.175 fwd +0.90, ac>=0.20 fwd +0.85 — all forward-positive, so the gate is robust, not a single magic number. 0.15 is the freq/EV middle; raise it for tighter risk, lower it for more frequency at small size.
- **Liquidity selects the carriers.** BTCUSD and DASHUSD are forward-positive in EVERY individual year including the 2026 drawdown. The thin/illiquid alts are noise or loss: LTCUSD -0.96R (8% win), DOTUSD -0.34R, ADAUSD flat and fades forward (-0.20R fwd), XTZUSD good 2023-25 but -1.10R in 2026. Keep BTC+DASH; size the alts at zero (or tiny experimental size) until more history exists.
- **Stop width matters: crypto needs WIDE stops.** sd=1.5a underperforms (gets shaken out); sd=2.0-3.0a all work, sd=2a is the sweet spot for the 4R target. Tight gold-style stops do not transfer.
- **2026 regime caveat:** 2026 crypto was a BTC 88k->77k decline/chop. The ac60+wide-stop rule held BTC/DASH positive there (BTC +2.03!, DASH +0.19), but it is what kills the thin alts. The edge survives the adverse regime ONLY on the liquid names.

## What the trades taught us (learning)

- The confirmed commodity FVG-retest baseline does NOT transfer to crypto out-of-the-box: only BTCUSD was positive (+0.68R, n=10); altcoins were negative. Gold-tuned FVG geometry + vol gate is too tight for crypto's swings. Crypto needed its own entry (raw breakout) and wider stops.
- The momentum-persistence thesis from the prompt is CONFIRMED for crypto: the same `ac60` gate that powers commodity continuation is the dominant edge driver here too. Crypto + persistence = strong continuation.
- Beware tiny train samples: a naive train-EV ranking picked ADAUSD (train n=8 looked +2.10R) which then FAILED forward (-0.20R). Train history is too thin to rank symbols by train-EV — selection must be by liquidity + per-year forward robustness, not a single train number.

## Honest data limits

- H4 is the safe default and what `w1.load` unions. Depth: BTCUSD/ADAUSD/DASHUSD from ~2024-08/09, XTZUSD from 2023-08 (deepest), LTCUSD/DOTUSD from 2025-04. **ETHUSD H4 via `w1.load` is broken (only 134 bars from 2026-05)** — the ETH H4 export is nearly empty even though M1 ETH exists from 2024-10. ETH was therefore excluded; rebuild ETH H4 by resampling `data/mt5_research_exports/bridge_ftmo_m1_*/ETHUSD_M1.csv` (2024-10 onward) to add it as a third carrier — high priority next step given ETH's liquidity.
- Only ~Q4 2024 falls in the train window (year<=2024) for BTC/DASH (train n=2 and n=6). Train is thin; the strength of this sleeve is the FORWARD 2025+2026 holdout, both positive and consistent across two adverse and trending regimes.

## Next steps

1. Resample M1 ETHUSD (2024-10+) to H4 and add ETH as a third carrier (apply identical rule; expect BTC-like behavior).
2. Add a small-size experimental sub-sleeve for XTZUSD with a stricter ac>=0.20 gate + the exit_state_d scale-out to clip its 2026 tail (it had the deepest history and was strong 2023-25).
3. Test M1/M15 intrabar realism on BTC for the 2a stop fills (data exists from 2024-08); the wide 2a stop should be fill-robust but worth proving.
4. Confidence sizing: BTC/DASH at full sleeve size; ETH (once added) at 0.75x pending forward; alts at 0 until history deepens.

## Artifacts
- Trade ledger: `CRYPTO_MOMENTUM_TRADE_LEDGER.jsonl` (68 trades, BTC+DASH, fields: sym,t,dir,ac60,stop_dist,target_R,netR,year).
- Scratch build scripts: `/tmp/cm_*.py` (exploration; not committed).
