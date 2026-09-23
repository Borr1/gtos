# d3 — WHAT DOES A WORKING SLEEVE LOOK LIKE? The live W7 book as a control

**Lane d3, wave 19.** The estate's one worked example — the armed W7 sleeve book — used as a
control against the broad V4 origin families, to answer the owner's question directly:
**is it the sleeves or the way we're using them?**

**VERDICT: SIGNAL — and the mechanism is ACCUMULATION, not size.**

The broad family's directional signal is REAL (paired p 0.0045 over 144,725 trades in 8
windows) and it is worth **0.1490 bps of price per trade** against a **3.1907 bps** broker
toll — 21.4× short. A working sleeve's signal is worth **3.41 bps at a 2-hour horizon and
128.04 bps at 320 hours: it grows 37.58×.** The broad family's grows **0.97× — it is flat.**
Because the toll is charged once per trade regardless of how long the trade is held, a
signal that never gets bigger with time can never pay for itself at any contract. That is
why **0 of 282 transplanted contracts is net-positive.**

Everything below is measured on the whole population. Nothing is sampled. The sealed three
(jun/aug/sep 2025) were not opened.

---

## 0. What was measured, and against what

| | value |
|---|---|
| broad-family population | **144,725** at-market close-only roster emissions, 8 windows (2025-10 … 2026-05), 7 origin families, 24 instruments |
| contracts priced on it | **282** (192 flat-bps cells + 90 ATR-scaled cells), each with a matched PLACEBO-SIDE arm → **~81.6 M walked outcomes** |
| live-sleeve control | **134** AQ_ESTATE_TRADES_V2 trades of `crypto`, `energy_agri`, `sub_xvol_pullback`, `sub_mid_dn_revert`, `mx_btcusd_d1_donchian_20_breakout` whose entry falls inside the M15 tape window and whose symbol the tape carries |
| walker validation | re-walk vs the estate's own `r_gross`: **corr 0.999, sign agreement 1.000, n=134** (`D3_REV_VALIDATE.json`) |
| resolution | printed M15 bars — the unit `_trading_m15_bars_since` counts (`execution.py:8953-8958`), so a 1280-bar time stop is 320 *trading* hours, weekends excluded, exactly as the live sleeves run it |
| toll | the h1 four-term broker-true basis (hour-aware tick spread + broker-true commission + measured price-unit slippage + swap on every broker midnight the cell's OWN realised hold crosses) |
| control | **PLACEBO-SIDE** on every cell: identical rows, instants, risk distances and toll, random side. `real − placebo` is the signal; the toll cancels exactly because the difference is paired |

---

## 1. TABLE A — the structural comparison

Measured from `AQ_ESTATE_TRADES_V2.json.gz` (live sleeves) and the reproduced sealed rosters
(broad family). `D3_SLEEVE_GEOM.json`, `D3_BPS_LIVE.json`.

### 1.0 The matched comparison — same walker, same contract shape, same units

Both populations walked by the same code at the same contract (each system's own native stop,
3R target, 320-hour time stop), against the same PLACEBO-SIDE control, in **bps of price**:

| | live sleeves (n=134) | broad family (n=144,725) | apart |
|---|---:|---:|---:|
| gross | 179.35 bps | 0.2893 bps | 620× |
| placebo-side (what a coin flip gets on the same rows) | 64.33 | 0.0954 | |
| **signal (real − placebo)** | **128.04 bps** | **0.1938 bps** | **661×** |
| toll | 29.23 | 3.44 | |
| **signal ÷ toll** | **4.38** | **0.056** | **78×** |

Median stop width behind those numbers: **215.38 bps** (live) vs **9.683 bps** (broad).

### 1.1 The full structural table

| | live sleeves | broad-family origin families |
|---|---|---|
| decision grid | **H4** (4 h) for the four armed; **D1** for `mx_btcusd` | **M15** |
| stop width, median | **44.1 – 436.0 bps** | **9.683 bps** (p10 2.29, p90 52.19, mean 21.88) |
| target multiple | 3R / 4R (`crypto` 4R, `sub_xvol_pullback` 3R + 4R frontier, `energy_agri` 50 % off at 2R then 4R runner, `mx_btcusd` 2R + 5R frontier) | 2R downstream; `risk.min_rr` 1.5 at the generator |
| time stop | 1280 printed M15 bars = **320 trading hours** (`mx_*` 7680 = 1920 h) | ~2 h effective — the 9.68 bps stop is hit long before any budget binds |
| realised hold, median | **28 – 72 h** | 2.2 h at the shipped cell; **5.8 h even when given a 320-hour budget** |
| MFE arrives, median | **20 – 64 h**; only **0.6 – 4.4 %** of trades reach their MFE within 2 h | — |
| MAE, median | −0.73 … −1.10 R; **71.6 – 80.7 %** go at least 0.5 R against before working | — |
| instruments | 1 – 18 | 24 |
| firing rate | **1.0 – 2.2** trades per decision-day | ~18,000 emissions/month ≈ 600/day |
| **price captured per trade (gross)** | **25.8 – 326.1 bps** | **0.081 bps** at the shipped cell; max **+0.452 bps** of *signal* over all 192 cells |
| toll per trade | 6.3 – 58.9 bps | 3.19 bps at the shipped cell (2.94 spread+comm+slip, +0.25 swap); 3.05 – 27.38 bps over the grid |
| **gross ÷ toll** | **2.36 – 11.46** | **0.025** |
| **signal ÷ toll** | **4.38** | **0.047** (shipped) / **0.051** (best of 192) |

Per live sleeve, in price space — the units in which the comparison does not move when the
contract moves:

| sleeve | n | stop bps | gross R | **gross bps** | toll bps | gross/toll |
|---|---:|---:|---:|---:|---:|---:|
| `crypto` | 181 | 376.0 | 0.5673 | **227.86** | 54.99 | 4.14 |
| `energy_agri` | 67 | 258.1 | 0.2588 | **129.08** | 54.64 | 2.36 |
| `sub_xvol_pullback` | 88 | 197.7 | 1.3542 | **326.08** | 28.45 | 11.46 |
| `sub_mid_dn_revert` | 533 | 44.1 | 0.3735 | **25.81** | 6.33 | 4.08 |
| `mx_btcusd_d1_donchian_20_breakout` | 318 | 436.0 | 0.3576 | **144.96** | 58.92 | 2.46 |
| **broad family (shipped cell)** | 144,725 | 9.68 | 0.0084 | **0.081** | 3.19 | **0.025** |

The tightest live sleeve captures **25.81 bps** per trade. The broad family captures
**0.081 bps**. That is a factor of **319×**, and it is not a contract choice — it is what the
setups find. Read against each system's own toll: every live sleeve clears it (2.36 – 11.46×);
the broad family reaches **2.5 %** of it.

---

## 2. TABLE B — THE FORWARD TRANSPLANT: the broad family under live-sleeve-shaped contracts

Every cell is the same 144,725 rows, same entries, same sides, re-walked under a different
contract, with the toll re-charged for that cell's own realised hold. `D3_ANALYSIS.json` →
`forward_transplant_grid`; raw per-window in `d3/D3_GRID_<window>.json`.

### 2.1 Stop width × horizon, at the shipped 2R

| stop | 2 h | 8 h | 24 h | 72 h | 160 h | 320 h |
|---|---:|---:|---:|---:|---:|---:|
| **native (9.68 bps)** gross | +0.00836 | +0.00493 | +0.00372 | +0.00408 | +0.00380 | +0.00384 |
| toll | 0.32951 | 0.33323 | 0.33446 | 0.33524 | 0.33542 | 0.33546 |
| **net** | −0.32115 | −0.32830 | −0.33074 | −0.33116 | −0.33162 | −0.33162 |
| **50 bps** net | −0.05394 | −0.06104 | −0.07125 | −0.07670 | −0.08909 | −0.09331 |
| **100 bps** net | −0.02534 | −0.03004 | −0.03908 | −0.05307 | −0.06948 | −0.09008 |
| **200 bps** net | −0.01355 | −0.01709 | −0.02536 | −0.03955 | −0.05685 | −0.08682 |
| **400 bps** net | **−0.00698** | −0.00972 | −0.01567 | −0.02762 | −0.04201 | −0.06639 |

**The toll is a pure function of the stop width and it can be engineered away entirely:**
0.32951 R → 0.00777 R, a **42.4× reduction**, by widening the stop from 9.68 bps to 400 bps.
**The gross falls with it** (+0.00836 → +0.00078), because R is a ratio and both terms scale
by the same divisor. Net converges to zero **from below** and never crosses. This is f2's
cost-cap sweep reproduced through a completely different lever, and it lands in the same place.

### 2.2 Target ladder at the live-sleeve horizon (320 trading hours)

| stop | 1.5R | 2R | 3R | 4R | 5R | `energy_agri` shape (50 % @2R → BE, 4R runner) |
|---|---:|---:|---:|---:|---:|---:|
| native, net | −0.34850 | −0.33162 | −0.31090 | −0.29836 | −0.28920 | −0.31752 |
| 200 bps, net | −0.08153 | −0.08682 | −0.09790 | −0.09710 | −0.09938 | −0.09696 |
| 400 bps, net | −0.06706 | −0.06639 | −0.06528 | −0.06027 | −0.05686 | −0.06429 |

The `energy_agri` partial-runner shape is the one contract in the grid that could have hidden a
result behind a book-keeping error, and it does not: its signal at the live-sleeve horizon is
**+0.01602** at native stop and **−0.01512** at 400 bps — the same sign flip every other shape
shows. (A first pass credited the 50 % partial whenever +2R was touched anywhere inside the
horizon, including on rows whose stop had already fired, which manufactured a spurious
+0.90 R/trade. Fixed at `d3_walk.py` `be_runner_walk`: the partial now requires
`ia < is_` — the arm must be touched *before* the stop.)

### 2.3 The vol-matched version — stop = k × ATR14(H4), the sleeves' own sizing convention

A flat bps stop hands EURUSD 400 bps and BTCUSD 25 bps, so the flat grid alone is not a fair
transplant. Repeating it with the live sleeves' actual sizing rule (`D3_ATR_POOLED.json`):

| k | realised mean stop | best net over 9 (target × horizon) cells |
|---|---:|---:|
| 0.25 | 16.73 bps | −0.19743 |
| 0.5 | 33.47 bps | −0.10005 |
| 1.0 | 66.93 bps | −0.05150 |
| 2.0 | 133.86 bps | −0.02657 |
| 4.0 | 267.72 bps | −0.01344 |

**0 of 90 ATR cells is net-positive. 0 of 192 flat-bps cells is net-positive. 0 of 282.**
The best cell in the entire space is `400 bps / 2R / 2 h` at **−0.00698 R/trade, positive in
0 of 8 windows**. No cell anywhere in the grid is net-positive in more than 2 of 8 windows.

### 2.4 And the signal gets WORSE the closer the contract gets to the live sleeve's shape

Day-block bootstrap, 4,000 draws, on the paired per-day REAL−PLACEBO difference:

| cell | signal R/trade | CI95 | p(≤0) |
|---|---:|---|---:|
| shipped (native, 2R, 2 h) | **+0.01538** | [+0.00353, +0.02760] | 0.0045 |
| native, 2R, 320 h | +0.01410 | [+0.00108, +0.02695] | 0.0158 |
| `sub_xvol_pullback` shape (native, 3R, 320 h) | +0.02002 | [+0.00380, +0.03576] | 0.0073 |
| `crypto` shape (native, 4R, 320 h) | +0.01908 | [−0.00026, +0.03851] | 0.0262 |
| `sub_mid_dn_revert` scale (50 bps, 3R, 320 h) | +0.00395 | [−0.01582, +0.02307] | 0.3390 |
| `sub_xvol_pullback` scale (200 bps, 3R, 320 h) | −0.01122 | [−0.02568, +0.00311] | 0.9345 |
| **`crypto` scale (400 bps, 4R, 320 h)** | **−0.01504** | [−0.02645, −0.00366] | **0.9948** |

At the cell that most closely reproduces `crypto`'s live contract — a ~400 bps stop, a 4R
target and a 320-hour time stop — the broad family's direction call is **significantly worse
than a coin flip**. Widening the geometry does not reveal a hidden edge; it exposes an
anti-edge that the tight stop was hiding by killing the trade first.

---

## 3. TABLE C — THE REVERSE TRANSPLANT: the live sleeves under the broad family's contract

134 live-sleeve trades, re-walked on the same tape. Walker validated at corr **0.999** and
100 % sign agreement against the estate's own recorded `r_gross`.

| contract | gross | placebo | signal | toll | **net** | hold | % stopped |
|---|---:|---:|---:|---:|---:|---:|---:|
| **their own** (native stop 197–436 bps, 3R, 320 h) | +0.8328 | +0.2987 | **+0.5341** | 0.1357 | **+0.6970** | 100.2 h | 52.2 % |
| **the broad family's** (9.28 bps stop, 2R, 2 h) | −0.2017 | −0.2779 | +0.0762 | **0.7568** | **−0.9585** | 0.7 h | **68.7 %** |
| the broad family's stop, their horizon (9.28 bps, 3R, 320 h) | −0.1343 | −0.1642 | +0.0299 | 0.7599 | −0.8942 | 1.5 h | 78.4 % |
| their stop, the broad family's horizon (native, 3R, 2 h) | +0.0427 | +0.0105 | **+0.0322** | 0.0436 | −0.0009 | 2.3 h | 0.0 % |

Per sleeve, gross R/trade, own shape vs the broad family's shape:

| sleeve | n | own shape | broad shape |
|---|---:|---:|---:|
| `crypto` | 15 | +0.3285 | −0.4000 |
| `energy_agri` | 27 | +1.2222 | −0.3333 |
| `sub_xvol_pullback` | 23 | +1.9565 | −0.4783 |
| `sub_mid_dn_revert` | 30 | +0.8667 | −0.1345 |
| `mx_btcusd_d1_donchian_20_breakout` | 39 | +0.0682 | +0.0769 |

**The transplant is destructive in both directions, and that is the point.** A working sleeve
put on the broad family's contract goes from +0.70 to **−0.96 R/trade**: 68.7 % of its trades
are stopped inside two hours by a 9.28 bps stop, and the toll rises to **0.7568 R** because the
same 3 bps of spread is now 76 % of a much smaller risk unit. Neither half of the contract
alone does it — their stop with a 2-hour horizon is only −0.0009, their horizon with a 9.28 bps
stop is −0.8942. **The stop width is what kills them; the horizon is what makes them.**

---

## 4. TABLE D — THE MECHANISM: signal vs holding horizon, both systems, same units

The signature of a trading edge is that a setup tells you where price will be *later* — so the
signal should GROW with the horizon. Signal = REAL − PLACEBO-SIDE gross, in bps of price,
target 3R, whole populations. `D3_CURVE.json`.

| horizon | **live sleeves** (n=134) | p(≤0) | **broad family** (n=144,725) |
|---|---:|---:|---:|
| 2 h | 3.41 bps | 0.3940 | 0.2008 bps |
| 8 h | 32.96 | 0.0340 | 0.2051 |
| 24 h | 38.41 | 0.1435 | 0.2077 |
| 72 h | 100.01 | 0.0088 | 0.1943 |
| 160 h | 103.98 | 0.0192 | 0.1904 |
| 320 h | **128.04** | 0.0037 | **0.1938** |
| **growth 2 h → 320 h** | **37.58×** | | **0.97×** |
| level at 320 h | | | **661× apart** |

**This is the answer, in one table.** A working sleeve's setup identifies a move that then
unfolds over days — 3.41 bps of it is visible in the first two hours and 128 bps by day 13.
The broad family's setup identifies **0.20 bps and that is all there ever is**: the same 0.20
bps at 2 hours, at 24 hours and at 320 hours. It is not a small edge that needs more time. It
is a *complete* edge that is 16× too small, and time adds nothing to it.

The broker toll is **~3.06–3.19 bps per trade and is charged once**, independent of horizon.
A signal that does not accumulate can never outrun a fixed per-trade toll — which is exactly
why every one of the 282 transplanted contracts is net-negative, and why the direction of the
transplant does not matter.

---

## 5. TABLE E — COMPLETENESS: is anything hiding inside the family?

The pooled family shows zero accumulation. Before concluding, every cohort was checked
against **its own** measured toll (`D3_COHORT.json`, `D3_SEARCH.json`) — 159 cohorts × 6
horizons = **954 looks**.

By origin family, signal in bps by horizon (toll ≈ 2.94 bps short / 3.44 bps at 320 h):

| family | n | 2 h | 8 h | 24 h | 72 h | 160 h | 320 h |
|---|---:|---:|---:|---:|---:|---:|---:|
| `displacement_continuation` | 39,517 | 0.201 | 0.464 | 0.646 | **0.826** | 0.661 | 0.718 |
| `regime_transition_break` | 2,320 | 0.684 | 1.195 | **1.904** | −1.553 | −1.927 | 0.032 |
| `volatility_compression_expansion` | 5,341 | **0.765** | −1.191 | −4.087 | −3.627 | −3.380 | −3.993 |
| `liquidity_sweep_reclaim` | 43,751 | 0.252 | **0.432** | 0.362 | 0.402 | 0.318 | 0.304 |
| `cross_asset_lead_lag` | 21,678 | 0.106 | **0.482** | 0.439 | 0.449 | 0.420 | 0.413 |
| `structural_distance_extreme` | 23,923 | −0.111 | −0.123 | −0.126 | −0.126 | −0.126 | −0.126 |
| `session_open_range_break` | 8,195 | −0.827 | −1.073 | −0.840 | −1.085 | −0.865 | **−0.793** |

**Not one origin family reaches its own toll at any horizon.** The best is
`displacement_continuation` at 0.826 bps — 3.9× short — and it is the only family that shows
even a hint of accumulation (0.201 → 0.826, 4.1×, then flat).

Cohort-level search, each cohort priced against its own toll at its own best horizon:

| filter | count |
|---|---:|
| cohorts measured (n ≥ 200) | 159 |
| best-horizon ratio > 1 | **26** |
| … and positive in ≥ 75 % of windows | **5** |
| … and positive in **every** window | **0** |
| whole family (`ALL`), best ratio | **0.0761** |

The 26 are the max over 954 looks and none survives a stability requirement. The top cells are
also the smallest: `session_open_range_break|XAUUSD` (ratio 6.29, **n=330**, 4/8 windows),
`session_open_range_break|UK100` (6.20, n=319, 6/8), `session_open_range_break|GER40` (5.79,
n=319, 5/8). The one family × instrument pattern that recurs is **breakout/continuation
families on index CFDs at a ~24-hour horizon** — six of the top twelve cohorts. That is a
direction to test, not a result, and it is the single thing this lane would hand to a
sealed-test lane.

Four instruments do beat the pooled 3.19 bps toll at their best horizon and do show
accumulation — **XAGUSD** (2.339 → 3.294 bps), **BTCUSD** (1.534 → 3.076), **USOIL_cash**
(1.032 → 3.245 at 72 h), **XAUUSD** (0.365 → 2.305 at 24 h). They are exactly the instruments
the live sleeves trade. Against their *own* tolls they reach ratios of 1.72 (XAUUSD) and below,
and none is positive in more than 6 of 8 windows.

---

## 6. What would have to be true

At the shipped geometry the broad family books **−0.32115 R/trade net** on 144,725 trades. In
price space that decomposes exactly:

- toll **3.1907 bps/trade** (spread 2.94 + swap 0.25 at the realised hold)
- signal **0.1490 bps/trade** (paired, p 0.0045, positive in 7 of 8 windows)
- **shortfall 21.42×**

Three things could close it, and the measurements price all three:

1. **More signal per trade.** Price capture must rise from 0.149 bps to > 3.19 bps — **21.4×**.
   No contract change reaches it: 282 were priced and the best moved capture to 0.081 bps gross.
2. **Accumulation.** If the signal grew with horizon the way a live sleeve's does (37.58×),
   0.149 bps would become 5.6 bps and the family would clear its toll at a ~13-day hold. It
   grows **0.97×**. This is the lever that is *structurally* absent, not merely small.
3. **A cheaper toll.** The toll would have to fall below 0.149 bps — **4.7 %** of the measured
   broker spread. Widening the stop 42× moves the toll in R units and not at all in bps; there
   is no contract in the reachable space that changes what the broker charges.

---

## 7. Limits, and what would overturn this

- **The live-sleeve control is n=134 and in-sample.** Those five sleeves were selected from a
  32-sleeve estate and **every one of them REJECTS at the ratified gate** (q = 1.0). Their
  +128 bps at 320 h is an upper bound, and the in-window subset (2025-06 … 2026-05) is the
  richest slice of their history: pooled walked gross +0.9265 vs their full-population
  0.26–1.35. **A 10× haircut still leaves 12.8 bps against the broad family's 0.19.**
- **Different instrument mix.** The live sleeves trade oil, BTC, silver and indices; the broad
  family trades 24 instruments including majors. Some of the 661× gap is instrument volatility,
  not setup quality — which is precisely why §5 re-ran the search per instrument, and why the
  four high-volatility instruments are reported separately. Even there the ratio never clears 2.
- **M15 resolution with the stop-wins tie rule.** Both systems are measured the same way, so
  the comparison is internally consistent, but the absolute 2-hour numbers are more pessimistic
  than f2's M1 walk (f2 native/2 h gross +0.02328 vs +0.00836 here). The signal figures agree
  closely (f2 +0.00315 pooled at R1 with a different exit; +0.01538 here at 2R/2 h).
- **The forward transplant assumes the roster's own entry and side.** It changes the contract,
  never the setup. A different *generator* on the same instruments is untested and remains open.
- **What would overturn it:** any broad-family cohort whose signal grows monotonically with
  horizon, clears its own toll, and holds sign in 8 of 8 windows. Zero of 159 do. The nearest
  miss is index breakouts at 24 h at 6/8.

---

## 8. Artifacts

All under `phase19/receipts/discovery/d3/`:

| file | what |
|---|---|
| `D3_SLEEVE_GEOM.json` | geometry of all 32 estate sleeves (stop bps, target, hold, MFE timing, MAE, breadth, firing rate) |
| `D3_BPS_LIVE.json` | live sleeves in price space: gross bps, toll bps, ratio |
| `D3_GRID_<window>.json` × 8 | the full 432-cell forward transplant, per window |
| `D3_ANALYSIS.json` | pooled grid, paired bootstraps, horizon curves, per-family |
| `D3_ATR_POOLED.json` | the vol-matched (k × ATR14 H4) transplant |
| `D3_REVERSE.json`, `D3_REV_VALIDATE.json` | live sleeves under the broad contract, + the corr-0.999 validation |
| `D3_CURVE.json` | the accumulation curve, both systems |
| `D3_SEARCH.json`, `D3_COHORT.json` | 159 cohorts × 6 horizons, each against its own toll |
| `d3_*.py` | every script, runnable as-is |

Rosters: `/tmp/pbg_full_{jan,feb,mar}` and `/tmp/f2_close_{202510,202511,202512,202604,202605}`
(Session PB's reproduced sealed rosters, and f2's five generated windows).
Bars: the true-UTC lane hold at
`/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars`.
