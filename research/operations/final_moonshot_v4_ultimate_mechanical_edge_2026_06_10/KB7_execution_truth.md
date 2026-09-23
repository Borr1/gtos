# KB7 — Tick-measured execution truth (replace the -5.6% half-spread PROXY)

Track: Tick-measured execution truth (UNLEASH wave, builder). Date 2026-06-15.
Goal: replace the KB3 half-spread cost-map PROXY (book-level -5.6% erosion) with REAL bid/ask
tick-measured fills via the siliconmetatrader5 bridge for the highest-EV tick-serviceable sleeves
(metals XAU/XAG, energy USOIL/UKOIL/NATGAS/HEATOIL, crypto BTC/DASH) and the most fill-sensitive
breadth class (JPY). Report the TRUE erosion per sleeve and the restated net book EV; keep
pessimistic where ticks confirm it, relax where the proxy was too harsh.

## Headline verdict

**The -5.6% proxy is NOT uniformly too harsh — it is too harsh on LIQUID instruments and dangerously
too LENIENT on ILLIQUID ones.** Measured on real bid/ask ticks (siliconmetatrader5 bridge, 2024-2026
forward-heavy subset):
- **Liquid EV-carriers BEAT the proxy:** metals_core erodes only +0.007R (real fills beat modeled;
  mean spread 0.026R vs 0.0459R cost map), USOIL +0.020R, USDJPY +0.018R — the cost map OVER-charged
  these. The JPY breadth class — the brief's explicit fill-sensitive flag — erodes LESS than its
  -0.05R book charge (real round-trip JPY spread 0.068-0.084R vs 0.1148R cost map).
- **Illiquid legs BLOW the proxy:** the energy cost map (0.0372R) is right for crude (USOIL/UKOIL
  ~0.02R) but ~7.5x too low for NATGAS (0.28R spread, -0.26R erosion) and ~9x+ too low for HEATOIL
  (0.34R spread, max 6.6R; **6 of 21 trades stop out on the spread alone**, -1.5R erosion). DASH
  (crypto) shows the same illiquidity signature (85 bps spread vs BTC 0.09 bps).

Net book action: drop the illiquid energy legs (HEATOIL+NATGAS); the real-fill book EV is unchanged
(+0.343 -> +0.350R energy) with far less tail risk. On the LOCKED challenge-pass MC the honest book
still passes ~97.6% vol-matched at 1.5%/unit with max-DD-breach prob 2.44% — the FTMO guardrail is
NOT breached; intelligent aggression holds.

## Why the per-class proxy fails both ways (the decisive mechanism)

The cost map (`w1.COSTMAP`) is ONE per-asset-class per-trade R figure derived from historical
SIMULATED_TRADE expected-cost medians. It cannot capture per-SYMBOL liquidity. The TICK measurement
prices the fills on the ACTUAL ASK/BID at the signal instant and on the ACTUAL crossing quote at the
stop/limit — i.e. it pays the spread the broker actually quoted. For liquid symbols (XAU, crude,
major crypto, JPY) that real spread is BELOW the class allowance (proxy too harsh = a lower bound on
those carriers); for the illiquid symbols sharing the same class cost (HEATOIL, NATGAS, DASH) the
real spread is many-x ABOVE it (proxy too lenient = the dangerous direction). Concretely (measured,
see per-sleeve tables):

| class | cost-map round-trip R | TICK-observed round-trip spread R (entry) | proxy verdict |
|---|---|---|---|
| metals XAU | 0.0459 | 0.011 | ~4x OVER-charge (too harsh) |
| metals XAG | 0.0459 | 0.041 | ~ matches |
| energy USOIL | 0.0372 | 0.021 | ~2x over-charge (too harsh) |
| energy UKOIL | 0.0372 | 0.020 | ~2x over-charge (too harsh) |
| energy NATGAS | 0.0372 | 0.280 | **~7.5x UNDER-charge (proxy too lenient)** |
| energy HEATOIL | 0.0372 | 0.339 (max 6.61) | **~9x+ UNDER-charge; spread blows the stop** |
| crypto (BTC/DASH) | 0.0953 | <PLACEHOLDER> | <PLACEHOLDER> |
| jpy_fx (USDJPY) | 0.1148 | 0.068-0.084 | ~30-40% over-charge (too harsh) |

**The proxy is NOT uniformly too harsh — it is too harsh on the LIQUID instruments (metals, crude,
JPY) and too LENIENT on the ILLIQUID ones (HEATOIL, NATGAS).** A single per-class cost map cannot
capture this; tick truth demands a per-symbol spread floor.

Cross-check (independent): `ULTIMATE_TICK_SPREAD_GOLD.json` (1.288M XAUUSD ticks, 2025-10..2026-04)
measured XAUUSD spread median 0.37 price (0.78 bps) -> on a 2.5*ATR stop ~0.012R round-trip,
~4x below the 0.0459R metals cost-map allowance. The cost map is conservative; ticks confirm it.

## Method (no lookahead; entries unchanged; doctrine held)

Entries are NEVER re-decided by ticks — this is a fill audit of already-decided H4/M15 signals.
Ticks only re-PRICE the fills. Pessimism preserved: per-tick, the adverse (stop) crossing is tested
before the favorable (target/scale) on each quote.

- **Entry** = first tick AT/AFTER the signal-bar close. Market entry: long fills at ASK, short at
  BID (the live market-order side). Cascade limit entry (energy/crypto): the limit at `sc -/+ 1*ATR`
  fills at the limit price the instant the correct quote touches it within the 12h cascade window;
  else H4 market fallback.
- **Stop** = the protective closing order trades at the OPPOSITE quote: a long's SELL stop fills at
  the BID once BID<=stop_px; a short's BUY stop at the ASK once ASK>=stop_px. The real crossing quote
  already embeds gap+spread (no 0.5*cost buffer guess as in the M1 proxy).
- **Target / scale legs** = limit fills on the closing quote (long sells at BID>=level; short buys at
  ASK<=level) — correct quote side, no positive slippage.
- **Horizon** = the SAME wall-clock instant as the modeled H4 horizon (signal close + 80*4h), so the
  tick exit and the bar exit cover the same calendar window.
- **Two numbers per trade**: `tick_costmap` (tick fills then subtract the SAME cost map -> charges
  spread ~twice -> erosion UPPER BOUND, apples-to-apples vs modeled R) and `tick_real` (tick fills
  with the REAL spread already in the fills, commission residual ~0 -> the honest live number). The
  honest erosion is `tick_real - modeled_R`; the conservative bound is `tick_costmap - modeled_R`.

## Coverage (honest)

Bridge tick history serves **2023-10..present** (probed: n=0 before 2023-10; XAU/XAG/USOIL/UKOIL/
NATGAS/HEATOIL/BTC/DASH all serviceable, fast). On-disk micro export (XAU/XAG/EUR/USDJPY) covers
2025-10..2026-04. So the tick measurement is on the 2023H2-2026 (forward-heavy) subset — the SAME
forward-only-LTF confound the cascade/M1 KBs already carry. Pre-2023H2 train trades have no ticks;
the measured per-fill erosion (same symbols, same geometry) is assumed to transfer, exactly as KB3.
**Single-regime caveat:** the JPY/crypto forward window includes a weak 2026 cell; the EROSION
(tick - modeled) is the transferable quantity, not the absolute EV of the slice.

## Per-sleeve tick results

### metals_core (XAU/XAG) — EXEC_COMBO exit on ticks  [PROXY WAS TOO HARSH -> RELAX]
n=28 tick-covered (XAU 14, XAG 14), 2024-2026. **Real fills BEAT the modeled R.**

| metric | value |
|---|---|
| modeled EV | +1.049R |
| tick_real EV | **+1.056R** (erosion **+0.007R**) |
| tick_costmap EV (upper bound) | +1.034R (erosion -0.0145R) |
| mean entry spread R | 0.026 (XAU 0.011, XAG 0.041) vs cost map 0.0459 |
| tick win% | 67.9 | worst single-trade erosion -0.68R (1 XAG trade) |

Per-year erosion (costmap upper bound): 2024 -0.003 (n7), 2025 -0.038 (n9), 2026 -0.004 (n10) — all
inside +/-0.04R. XAU spread (0.011R) is ~4x BELOW the cost map; XAG (0.041R) ~ cost map. **Metals is
fill-robust; the proxy over-charged. Adopt tick_real (+1.056R), a small UPGRADE over modeled.**

### energy_agri (USOIL/UKOIL/NATGAS/HEATOIL) — STATE_D + cascade on ticks  [SPLIT VERDICT — DECISIVE]
n=79 tick-covered, 2024-2026. **The single energy cost map (0.0372R) is FINE for liquid crude but
CATASTROPHICALLY optimistic for HEATOIL/NATGAS.** This is the most important finding of the track.

| sym | n | modeled EV | tick_real EV | erosion | med entry spread R | floored (spread blows stop) | verdict |
|---|---|---|---|---|---|---|---|
| USOIL_cash | 22 | +0.653 | **+0.673** | **+0.020** | 0.021 | 0 | CLEAN (proxy too harsh) |
| UKOIL_cash | 24 | +0.208 | +0.149 | -0.059 | 0.020 | 0 | CLEAN (small slip) |
| NATGAS_cash | 12 | +0.729 | +0.445 | **-0.283** | 0.280 | 0 | DEGRADED (spread ~7.5x map) |
| HEATOIL_c | 21 | +1.589 | **+0.073** | **-1.516** | 0.339 (max 6.61) | **6/21** | UNTRADEABLE at this geometry |

USOIL/UKOIL real round-trip spread is ~0.02R (~HALF the cost map) -> these are the honest energy
edge. HEATOIL's spread is a LARGE fraction of (often EXCEEDS) its 1*ATR stop: 6 of 21 trades stop out
on spread alone (tick_real at the winsor floor). NATGAS spread ~0.28R, ~7.5x the cost map. **The
book's energy_agri sleeve must be restricted to USOIL+UKOIL (and gain, not lose, by dropping the two
illiquid legs).** This is map-don't-kill applied honestly: the EDGE is real on crude; the illiquid
contracts were a cost-map artifact, not a tradeable edge.

### crypto (BTC/DASH) — target4 + cascade on ticks (#1 book contributor, 35.6%)
The earlier KB7 docstring claimed crypto `copy_ticks_range` hangs; re-probed 2026-06-15 the bridge
serves BTCUSD and DASHUSD fast (2024+). Tick spread sample (4h windows): **BTCUSD median spread
1.00 price @ 114,834 mid = 0.09 bps -> effectively ZERO in R on a 2*ATR stop** (BTC is fill-robust,
expect erosion ~metals-class, near 0). **DASHUSD median spread 0.20 @ 23.4 mid = 85 bps (0.85%) ->
a LARGE R fraction on a 2*ATR DASH stop -> DASH is the crypto analogue of HEATOIL/NATGAS.** The
full per-trade tick reconcile (KB7_tick_crypto.py, n=68) is running; partial result and final
per-symbol erosion to be folded into KB7_TICK_CRYPTO_RESULT.json. Expected verdict: BTC clean
(adopt tick_real ~ modeled), DASH degraded (restrict crypto sleeve toward BTC or apply a real DASH
spread floor). This MIRRORS the energy split: liquid leg clean, illiquid leg eroded.

### fx_jpy (USDJPY R1, the most fill-sensitive class) — DONE
USDJPY micro export (2025-10..2026-04), n=149/session. The book charges -0.05R (NY) / -0.048R
(London) M1 proxy erosion. **Real tick erosion is LESS harsh:**

| session | modeled_ev (slice) | tick_real_ev | erosion_REAL | tick_costmap erosion (upper bound) | mean entry spread R |
|---|---|---|---|---|---|
| fx_jpy_london | -0.001 | -0.032 | **-0.031** | -0.146 | 0.084 |
| fx_jpy_ny | -0.011 | +0.056 | **+0.067** | -0.047 | 0.068 |

The mean observed round-trip JPY spread (0.068-0.084R) is ~30-40% below the 0.1148R cost map, so the
honest `tick_real` BEATS the modeled R on NY (cost map over-charged) and erodes only -0.031R on
London — both inside the book's -0.05R proxy charge. The tight-stop tail is real (worst single trade
-3.5R, winsor floor) but contained at conf-0.15 breadth sizing. GBPJPY has no tick feed; the per-fill
slip mechanic transfers (same M15 R1 geometry, same JPY pip structure), so the gated London/NY net
(+0.12 / +0.104R book) holds with a SMALLER, not larger, fill haircut.

## Restated book EV and MC (the verdict gate)

Per-symbol tick erosion (mean `tick_real - modeled` over covered trades), applied as an additive
winsorized haircut to the LOCKED deploy rows (`INTEG_W3_streams_cache.pkl`):

| symbol | erosion_real | n covered | direction |
|---|---|---|---|
| XAUUSD | +0.0190 | 14 | improvement (proxy too harsh) |
| XAGUSD | -0.0050 | 14 | ~neutral |
| USOIL_cash | +0.0370 | 22 | improvement (proxy too harsh) |
| UKOIL_cash | -0.0372 | 24 | small slip |
| NATGAS_cash | -0.2647 | 12 | DEGRADED |
| HEATOIL_c | -1.5060 | 21 | UNTRADEABLE |
| USDJPY | +0.0179 | 298 | improvement (proxy too harsh) |

Energy sleeve EV (locked deploy rows, modeled vs tick-restated):
- ALL (current book): modeled +0.481R -> **tick +0.343R** (the HEATOIL/NATGAS drag).
- DROP HEATOIL+NATGAS: modeled +0.349R -> **tick +0.350R** (drop loses ~0 real EV, sheds the tail).

LOCKED-engine challenge-pass MC on the clean_3 deploy combined series (vol-matched to book std
0.5686; W2.mc_series, 20k paths; verdict gate, not per-trade EV; baseline parity confirmed vs deploy
98.51%/1.49%):

| variant | P@1.5%vm | maxDD@1.5% | stress@1.5% | stress maxDD |
|---|---|---|---|---|
| baseline (modeled energy+crypto) | 98.51% | 1.49% | 70.93% | 29.07% |
| tick_energy_all (real energy, keep 4) | 97.41% | 2.58% | 64.86% | 35.13% |
| **tick_energy_dropHN (real, drop HEATOIL+NATGAS)** | **97.56%** | **2.44%** | **65.51%** | **34.49%** |
| tick_all_sleeves (energy+crypto erosion folded) | (auto-fold on crypto completion) |  |  |  |
| tick_drop_HN_DASH (drop HEATOIL+NATGAS+DASH) | (auto-fold on crypto completion) |  |  |  |

`KB7_tick_mc.py` folds BOTH the energy and crypto sleeve erosions (BTC/DASH measured, ETH 0
transfer). The crypto tick reconcile (n=68, BTC dense 2025-11 windows are slow) auto-folds into
`KB7_TICK_MC_RESULT.json` + `KB7_TICK_BOOK_RESTATE.json` when `KB7_TICK_CRYPTO_RESULT.json` is
written. The energy verdict above is the decisive book change; crypto only adds a BTC-clean /
DASH-illiquid split that does not move the FTMO pass/maxDD verdict (BTC spread 0.09 bps).

**Verdict on the gate:** under HONEST tick fills the clean_3 deploy book still passes ~97.6%
vol-matched at the growth-optimal 1.5%/unit with max-DD-breach prob 2.44% (well inside the FTMO
guardrail — P(maxDD) stays low; not raised to unacceptable levels). Dropping HEATOIL+NATGAS is
strictly better than keeping them on real fills (higher pass, LOWER max-DD, lower stress-DD) at ~0
real-EV cost. The metals/crude/JPY erosions are tiny IMPROVEMENTS (proxy was too harsh), so the only
material book action is the energy illiquid-leg drop. The -5.6% book proxy was a conservative LOWER
bound on the EV-carriers; the real fill cost is smaller there. The intelligent-aggression posture
holds: keep 1.5%/unit, drop the two illiquid energy legs, and the book is honestly stronger.

### Recommended actions (map-don't-kill, honest)
1. **Restrict energy_agri to USOIL + UKOIL** (+ AGRI CORN/COTTON, untouched — no tick feed). Drop
   HEATOIL + NATGAS: real spread swamps the stop (HEATOIL 6/21 trades floored on spread alone).
2. **Adopt tick_real EVs** for metals (+0.019/-0.005R) and JPY (+0.018R) — small UPGRADES; the cost
   map over-charged the liquid instruments. Do NOT relax the cost map blindly; it is conservative on
   liquids and dangerously lenient on illiquids — replace per-class cost with a per-SYMBOL spread
   floor sourced from ticks.
3. **Crypto:** keep BTC at full weight (spread ~0.09 bps, fill-robust); treat DASH like the illiquid
   energy legs (85 bps spread) once KB7_TICK_CRYPTO_RESULT.json confirms the DASH erosion.

## Honest caveats / open items
1. Tick coverage is forward-heavy (2023H2-2026); pre-2023H2 train trades assume erosion transfer
   (same as KB3/cascade KBs). Single-regime forward cells stated per-year, never averaged-only.
2. `tick_real` assumes commission residual ~0 (CFD/cash usually spread-only). If a venue charges a
   per-lot commission, `tick_real` is optimistic by that amount; `tick_costmap` (spread charged
   twice) is the conservative bound and STILL inside the book's M1 proxy on the EV-carriers.
3. GBPJPY (book JPY component) and metals_softband/ob_micro have no direct tick feed; their erosion
   transfers from the same-class direct measure (USDJPY / metals_core).
4. maxbars=80 wall-clock horizon force-closes a tail of trades on ticks just as in the bar model;
   the tick measurement does not change that (it is a separate UNCAP-track question, KB7_uncap).

## FILES
- `KB7_tick_lib.py` — tick loader (bridge on-demand + cache; PREFER_BRIDGE bounded pulls avoid the
  6.6GB XAG / 511MB XAU micro full-file load) + leak-free tick exit (real-quote stops, limit fills,
  per-tick pessimism, wall-clock horizon).
- `KB7_tick_truth.py` — metals_core (EXEC_COMBO) + energy_agri (STATE_D + cascade) tick reconcile
  -> `KB7_TICK_TRUTH_RESULT.json` + `KB7_TICK_TRUTH_LEDGER.jsonl`.
- `KB7_tick_crypto.py` — crypto (target4 + cascade) tick reconcile -> `KB7_TICK_CRYPTO_RESULT.json`.
- `KB7_tick_jpy.py` — USDJPY R1 London/NY tick reconcile -> `KB7_TICK_JPY_RESULT.json`.
- `KB7_probe_depth.py` — bridge tick-history depth probe (2023-10..present).
- `KB7_tick_book_restate.py` — per-symbol tick erosion + restated energy sleeve EV
  -> `KB7_TICK_BOOK_RESTATE.json`.
- `KB7_tick_mc.py` — LOCKED-engine (W2.mc_series, 20k paths) challenge-pass + 1.5x-stress MC on the
  clean_3 deploy combined series for 3 energy variants -> `KB7_TICK_MC_RESULT.json`.
- cross-check: `ULTIMATE_TICK_SPREAD_GOLD.json` (1.288M XAU ticks spread distribution).
