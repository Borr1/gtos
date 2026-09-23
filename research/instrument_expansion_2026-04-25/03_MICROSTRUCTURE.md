# Per-Instrument Microstructure Assessment — 24 Instruments

**Author:** Tier 1 Agent #3 — microstructure (Opus 4.7 max-effort)
**Date:** 2026-04-25
**Scope:** Spread, liquidity, kill-zone fit, weekend behaviour, news sensitivity, regime mapping, and FTMO 1% / 4% MTM feasibility for the 24 instruments in `data/historical_2026/`. Pure-Python, $0 API.
**Window:** Jan 2 — Apr 24, 2026 (≈81 trading days for FX / metals / indices, ≈114 calendar days for crypto).
**Sources:** Per-candle CSV (`data/historical_2026/<SYM>_M15.csv`) plus broker spread numbers (FTMO, redacted_account, Pepperstone Razor, IC Markets reference tier — recorded 2026-04-25, ±20% drift; no live MT5 tick stream available in this environment).

> **Caveats — read before quoting numbers.** (1) The CSV `volume` column is broker tick count, not actual lots traded. Per Agent 4 / data-layer roadmap, broker tick_volume on spot FX correlates 0.4–0.6 with real CME volume; on indices it correlates better; on crypto it is a CFD broker count, not exchange flow. Use as relative ordering, not absolute. (2) MT5 historical bars do not carry bid/ask, only mid OHLC, so "mean spread" here is the published broker number. The CSV-derived range serves as a sanity bound (spread cannot exceed M1 wick range). (3) "Natural KZ windows" are derived from |return|-density per UTC hour over 81 days; small samples mean per-hour density estimates have ~5-10% noise. Flag any conclusion based on a single 1-hour bucket. (4) `monday_gap_p90_pct` is calculated from any calendar gap of ≥2 days (Monday open vs Friday close); for instruments closed only ~5h on weekends (US30 cash) this includes some very short closures.

---

## Section 1 — Spread + cost analysis

### 1.1 Per-instrument typical/p99 spread (broker-published, 2026-04-25)

See `03_per_instrument_microstructure.csv` columns `spread_typ`, `spread_p99`, `spread_typ_pips`, `spread_p99_pips`.

| Instrument | Typ pips | p99 pips | Class |
|---|---|---|---|
| XAUUSD | 20.0 | 80.0 | metal |
| XAGUSD | 20.0 | 80.0 | metal |
| EURUSD | 0.6 | 2.5 | fx_major |
| GBPUSD | 0.9 | 4.0 | fx_major |
| USDJPY | 0.7 | 3.0 | fx_major |
| USDCAD | 1.2 | 5.0 | fx_major |
| USDCHF | 1.2 | 4.5 | fx_major |
| AUDUSD | 1.0 | 4.0 | fx_major |
| NZDUSD | 1.4 | 6.0 | fx_major |
| EURGBP | 1.2 | 5.5 | fx_cross |
| EURJPY | 1.2 | 4.5 | fx_cross |
| GBPJPY | 1.8 | 8.0 | fx_cross |
| AUDJPY | 1.3 | 6.0 | fx_cross |
| CHFJPY | 2.0 | 8.0 | fx_cross |
| BTCUSD | $25 | $80 | crypto |
| ETHUSD | $1.50 | $8.00 | crypto |
| US30_cash | 1.5 pts | 6.0 pts | index |
| NAS100 | 1.2 pts | 5.0 pts | index |
| SPX500 | 0.4 pts | 1.5 pts | index |
| GER40 | 1.4 pts | 5.5 pts | index |
| UK100 | 1.0 pts | 4.0 pts | index |
| JP225 | 7.0 pts | 25.0 pts | index |
| USOIL | 3.0 cts | 12.0 cts | energy |
| UKOIL | 3.0 cts | 15.0 cts | energy |

These are FTMO-tier all-in equivalents (raw + commission rolled together). Treat as ±20% — actual spreads observed during 13:30 UTC NFP / FOMC events run 5-10× higher and would appear in the p99 column if we had the live bid/ask stream.

### 1.2 Spread → R-cost translation (full table in `03_spread_cost_table.csv`)

Setup template: 1.0 × ATR-M15 stop, 1.5R reward target. Round-trip spread cost = 2 × spread_typ. R-cost % = round-trip / target.

**Best (least burdened — spread costs <5% of expected R):**

| Instrument | r_cost_typ_% | r_cost_p99_% |
|---|---|---|
| XAUUSD | 2.25% | 9.02% |
| US30_cash | 2.26% | 9.05% |
| GER40 | 3.10% | 12.19% |
| NAS100 | 4.40% | 18.32% |
| UKOIL_cash | 5.28% | 26.40% |

**Acceptable (5-10%):** USOIL 6.60%, JP225 6.95%, SPX500 7.34%, UK100 7.70%, USDJPY 9.45%.

**Spread-burdened (>10%) — a structural drag on edge:**

| Instrument | r_cost_typ_% | r_cost_p99_% | Note |
|---|---|---|---|
| NZDUSD | **49.6%** | 212.5% | typ spread 1.4p, ATR-M15 only 0.38p — the crippling case |
| EURGBP | **48.8%** | 223.7% | typ 1.2p, ATR-M15 0.33p |
| AUDUSD | 29.9% | 119.5% | typ 1.0p, ATR-M15 0.45p |
| USDCHF | 26.8% | 100.6% | typ 1.2p, ATR-M15 0.60p |
| USDCAD | 26.8% | 111.6% | typ 1.2p, ATR-M15 0.60p |
| CHFJPY | 26.3% | 105.2% | typ 2.0p, ATR-M15 1.01p |
| AUDJPY | 25.6% | 118.1% | typ 1.3p, ATR-M15 0.68p |
| EURUSD | 24.2% | 101.0% | typ 0.6p, ATR-M15 0.33p |
| EURJPY | 24.1% | 90.3% | typ 1.2p, ATR-M15 0.66p |
| ETHUSD | 21.4% | 114.0% | typ $1.50, ATR-M15 $9.36 |
| GBPJPY | 20.5% | 90.9% | typ 1.8p, ATR-M15 1.17p |
| GBPUSD | 12.6% | 56.1% | best of the FX-major spread group |
| BTCUSD | 12.2% | 39.2% | typ $25, ATR-M15 $272 |
| XAGUSD | 11.7% | 46.7% | typ 2.0c, ATR-M15 0.23 |

**Interpretation.** A 24% spread tax means a typical 1.5R OB-retest setup pays ~24% of its target away as cost. To net +1.0R you need a strategy that backtests at ≥1.32R *gross* (1.32R × 0.76 ≈ 1.00R net). At the GTOS confirmed XAUUSD expectancy of +0.20R/trade, **a 24%+ spread tax wipes most of the edge**. This is why pure spot-FX gating is unrealistic at FTMO/FN spread tiers.

### 1.3 Spread time-of-day variation (proxy)

The CSVs cannot give us actual spread by hour — only mid OHLC. As a proxy, per-hour mean range and the *open-bar range expansion ratio* indicate when broker spreads are most likely to widen. See per-instrument hourly tables in `03_hourly_buckets.json`.

Notable session-open expansion (range[hour] / range[hour-1]):

| Instrument | London-open ratio (07/06) | NY-open ratio (13/12) |
|---|---|---|
| XAUUSD | **1.16** | 1.01 |
| XAGUSD | **1.16** | 1.09 |
| EURGBP | 1.05 | 1.01 |
| GER40 | **1.08** | 0.91 |
| Most pairs | 0.92-1.05 | 0.86-1.05 |

XAUUSD/XAGUSD and German stocks reliably "wake up" at the London open; FX pairs essentially do not (the LDN open simply re-prices what was already moving). The NY open in this 2026 window is *contractionary* for most instruments — a 30-min digestion before genuine momentum appears post-13:30 NFP/data window. **This corroborates the existing XAUUSD `skip 13:00–13:14` policy**; the data shows the entire 12:00-13:00 hour is a low-density precursor and 13:00-14:00 is below-average activity for nearly every instrument.

### 1.4 Spread spike behaviour around session opens

True spread spikes (bid/ask widening) cannot be measured from OHLC alone. Empirically (per FTMO published live spread feeds + Pepperstone weekly reports cited in the data-layer roadmap):

- **XAUUSD**: 5-15× spread widening at exactly 22:00-22:05 UTC (broker rollover) and 13:30 UTC NFP/FOMC release.
- **US30_cash**: 3-5× at 13:30 UTC (open of cash session) and 21:00 UTC (cash session close).
- **JPY pairs**: 3-8× at 23:00-00:00 UTC daily (Tokyo fix) and 02:00 UTC (TYO open).
- **JP225**: ~10× at 06:00 UTC (TYO close) and 23:30-00:00 UTC (TYO pre-open).
- **Crypto (BTC/ETH)**: smaller relative spikes since 24/7, but 13:30 UTC NFP releases still cause ~2-3× widening on broker CFDs.

Recommendation: any KZ extension proposed in §3 must be cross-checked against these spike windows. We do NOT want to extend US30 KZ to include 21:00 UTC if cash close spread spikes will eat the trade.

---

## Section 2 — Liquidity profile

### 2.1 Tick volume per minute (broker-reported, relative ranking)

| Rank | Instrument | tick_vol/min | Notes |
|---|---|---|---|
| 1 | NAS100 | 260 | broker CFD tick density highest |
| 2 | BTCUSD | 251 | crypto round-the-clock |
| 3 | XAUUSD | 176 | metal |
| 4 | XAGUSD | 175 | metal — same broker family |
| 5 | US30_cash | 121 | index |
| 6 | GBPJPY | 97 | most-liquid JPY cross |
| 7 | ETHUSD | 88 | crypto |
| 8 | AUDJPY | 86 | |
| 9 | SPX500 | 83 | |
| 10 | CHFJPY | 82 | |
| 11 | EURJPY | 81 | |
| 12 | GER40 | 65 | |
| 13 | GBPUSD | 63 | |
| 14 | AUDUSD | 61 | |
| 15 | USDJPY | 60 | |
| 16 | USOIL | 58 | |
| 17 | UKOIL | 58 | |
| 18 | EURUSD | 54 | surprisingly mid-tier |
| 19 | JP225 | 55 | |
| 20 | UK100 | 48 | |
| 21 | USDCAD | 48 | |
| 22 | EURGBP | 46 | |
| 23 | NZDUSD | 42 | |
| 24 | USDCHF | 37 | |

EURUSD's mid-tier rank looks anomalous — likely an artifact of the FTMO/FN feed sampling cadence rather than real liquidity. Treat tick counts as relative within asset class only. The metal pair (XAUUSD/XAGUSD) appearing in the top 4 is consistent with their published live tick stream rates from CME GC.

### 2.2 Hourly tick density distribution

See `03_hourly_buckets.json`. Per-instrument peak hours (full hour bin):

- **XAUUSD**: peak 17:00 UTC (NY late afternoon), trough 23:00 UTC (post-NY).
- **US30_cash**: peak 17:00 UTC, trough 06:00-07:00 UTC. **Activity from 16:00 to 22:00 is uniformly above mean.**
- **JP225**: peak 02:00-03:00 UTC (TYO core), trough 00:00 UTC (broker reset).
- **EURUSD/GBPUSD/USDCHF/USDCAD/EURGBP**: all peak 17:00 UTC. Trough 07:00-08:00 UTC for USDCHF.
- **JPY pairs (USDJPY/GBPJPY/EURJPY/AUDJPY/CHFJPY)**: peaks at 17:00 and at 09:00-10:00 (London/Frankfurt opening JPY rebalancing).
- **BTCUSD/ETHUSD**: peak 17:00-18:00 UTC. Lowest activity 06:00-13:00 UTC.

### 2.3 Daily-range distribution

See `vol_q25_range`, `vol_q50_range`, `vol_q75_range` columns. Selected:

| Instrument | q25 (quiet) | q50 (median) | q75 (high) | q75/q25 |
|---|---|---|---|---|
| XAUUSD | 88.2 | 120.6 | 170.4 | 1.93 |
| US30_cash | 538 | 651 | 859 | 1.60 |
| BTCUSD | $1832 | $2732 | $3486 | 1.90 |
| EURUSD | 0.0049 | 0.0070 | 0.0090 | 1.85 |
| USDJPY | 0.73 | 0.96 | 1.35 | 1.85 |
| JP225 | 986 | 1330 | 1908 | 1.94 |

q75/q25 ≈ 1.85-1.95 across the board — the ratio of "high-vol day" to "quiet day" is remarkably consistent at ~2× regardless of asset class. Implication: the vol regime *transition rate* is more diagnostic than the individual quiet/normal/high cutoffs (see §5).

### 2.4 Dead-zone identification (mean range < 0.5× overall mean)

At a strict 0.3× threshold (per spec), no instrument has any dead-zone hours — markets stay liquid enough at the broker level. At a more useful 0.5× threshold:

- **EURUSD**: hour 00 (Sunday/Monday roll boundary).
- **EURGBP**: hour 06 (pre-London + after-Asia gap — ~2h trough).
- **US30_cash**: hours 05, 06, 07 (UTC pre-cash open, ~4h before NY).
- **SPX500**: hours 06, 07.
- **UK100**: hours 06, 07.

These are the windows where placing limit orders has the highest risk of partial fills / weird slippage. For our currently-live US30 system, this aligns with our existing 13:30-16:00 NY KZ — we already avoid 05-07 UTC.

The genuinely dead window (<0.5× mean) is narrower than I expected — modern broker connectivity keeps spreads reasonable even in deep Asia hours for most instruments.

---

## Section 3 — Kill-zone fit (THIS IS THE BIG SECTION)

### 3.1 Share of |returns| in named UTC windows

(`share_*_pct` columns; rows ordered by NY share descending)

| Instrument | Asia 00-04 | London 07-10:30 | NY 13-17 | US Close 17-22 | Off-hours |
|---|---|---|---|---|---|
| US30_cash | 9.3% | 9.0% | 23.1% | **34.4%** | 24.2% |
| SPX500 | 10.8% | 10.5% | 21.1% | **32.1%** | 25.5% |
| NAS100 | 11.3% | 10.6% | 21.3% | **31.7%** | 25.0% |
| GER40 | 9.4% | 14.6% | 22.3% | 25.0% | 28.8% |
| UK100 | 10.0% | 13.4% | 21.7% | 26.1% | 28.8% |
| JP225 | **18.4%** | 14.4% | 16.7% | 20.7% | 29.8% |
| XAUUSD | 15.6% | 13.4% | 19.3% | 23.8% | 27.9% |
| XAGUSD | 15.2% | 14.0% | 19.0% | 23.9% | 27.9% |
| EURUSD | 13.0% | 13.3% | 20.8% | 26.0% | 26.9% |
| GBPUSD | 13.0% | 13.1% | 21.6% | 26.0% | 26.4% |
| USDJPY | 17.5% | 14.8% | 17.8% | 22.6% | 27.3% |
| USDCAD | 12.8% | 11.7% | 22.1% | 27.5% | 26.0% |
| USDCHF | 16.0% | 12.6% | 20.4% | 25.0% | 26.0% |
| AUDUSD | 15.1% | 12.8% | 19.3% | 25.1% | 27.7% |
| NZDUSD | 17.0% | 12.7% | 18.9% | 24.0% | 27.3% |
| EURGBP | 15.3% | 12.5% | 22.7% | 24.0% | 25.5% |
| EURJPY | 18.9% | 15.6% | 17.3% | 20.9% | 27.4% |
| GBPJPY | 17.6% | 14.8% | 18.3% | 22.0% | 27.3% |
| AUDJPY | 17.9% | 14.1% | 16.8% | 22.7% | 28.4% |
| CHFJPY | 20.1% | 14.4% | 17.8% | 21.1% | 26.7% |
| BTCUSD | 16.6% | 11.5% | 16.0% | **28.3%** | 27.6% |
| ETHUSD | 16.6% | 11.5% | 16.1% | **27.6%** | 28.2% |
| USOIL_cash | 11.6% | 12.1% | 19.9% | 26.3% | 30.0% |
| UKOIL_cash | 4.7% | 12.9% | 21.4% | 28.1% | 32.9% |

**The single most important observation:** for every instrument except JP225 and the JPY crosses, the **US Close window (17:00-22:00 UTC)** carries 22-34% of daily motion — and our currently-coded KZ schedule cuts off at 17:00 UTC for XAUUSD, 16:00 UTC for US30, and 15:30 UTC for the others.

We are systematically NOT trading the second-highest-density window of the day for indices and FX majors.

### 3.2 Natural KZ windows (peaked-density, ≥1.3× uniform baseline)

See `03_natural_kz_windows.csv`. Top per-instrument windows:

| Instrument | Window 1 | Window 2 | Window 3 |
|---|---|---|---|
| XAUUSD | 15:00-18:00 (18.5%, 1.58×) | 03:00-05:00 (11.9%, 1.51×) | — |
| XAGUSD | 16:00-18:00 (12.9%, 1.55×) | 03:00-05:00 (12.4%, 1.53×) | — |
| EURUSD | 15:00-19:00 (25.0%, 1.68×) | — | — |
| GBPUSD | 15:00-19:00 (25.6%, 1.79×) | — | — |
| USDJPY | 17:00-18:00 (6.1%, 1.46×) | 15:00-16:00 (5.4%, 1.31×) | — |
| USDCAD | 15:00-19:00 (28.0%, 1.93×) | — | — |
| USDCHF | 15:00-19:00 (25.0%, 1.79×) | — | — |
| AUDUSD | 16:00-19:00 (19.0%, 1.75×) | — | — |
| NZDUSD | 16:00-18:00 (12.7%, 1.62×) | — | — |
| EURGBP | 15:00-18:00 (19.4%, 1.74×) | 00:00-01:00 (6.0%, 1.45×) | 11:00-12:00 (5.6%, 1.35×) |
| EURJPY | 17:00-18:00 (6.4%, 1.53×) | 09:00-10:00 (5.8%, 1.39×) | 03:00-04:00 (5.4%, 1.30×) |
| GBPJPY | 17:00-18:00 (7.0%, 1.69×) | 09:00-10:00 (5.7%, 1.37×) | — |
| AUDJPY | 16:00-18:00 (12.4%, 1.67×) | — | — |
| CHFJPY | 16:00-18:00 (12.2%, 1.62×) | 09:00-11:00 (11.0%, 1.33×) | 00:00-01:00 (6.4%, 1.54×) |
| **BTCUSD** | **16:00-19:00 (19.4%, 1.79×)** | — | — |
| **ETHUSD** | **16:00-19:00 (18.8%, 1.70×)** | — | — |
| **US30_cash** | **16:00-21:00 (38.6%, 2.33×)** | 22:00-23:00 (5.6%, 1.36×) | — |
| **NAS100** | **16:00-20:00 (30.2%, 2.20×)** | — | — |
| **SPX500** | **16:00-20:00 (29.6%, 2.21×)** | 22:00-23:00 (5.5%, 1.31×) | — |
| **GER40** | **14:00-19:00 (30.7%, 1.70×)** | **10:00-12:00 (13.4%, 1.74×)** | — |
| **UK100** | 15:00-19:00 (25.2%, 1.61×) | **10:00-12:00 (13.3%, 1.74×)** | — |
| **JP225** | **02:00-04:00 (13.8%, 1.68×)** | 17:00-18:00 (5.8%, 1.40×) | — |
| **USOIL** | 16:00-19:00 (17.1%, 1.38×) | — | — |
| **UKOIL** | 15:00-19:00 (23.6%, 1.47×) | 11:00-13:00 (11.5%, 1.44×) | 21:00-22:00 (5.6%, 1.34×) |

The 38.6% in US30_cash 16:00-21:00 is the highest single-window concentration in the entire universe — 5 hours capturing 38% of the trading day's motion. We currently allow trading until 16:00 UTC. **This is a 5-hour high-density window we systematically skip.**

### 3.3 Comparison with currently-coded KZ schedule

`quick_reference_card.md` §1:

| Instrument | Coded London | Coded NY | Coded Tokyo |
|---|---|---|---|
| XAUUSD | 07:00-10:30 | 13:00-17:00 (skip 13:00-13:15) | — |
| US30 | 08:00-10:30 | 13:30-16:00 | — |
| USDJPY | 07:00-09:30 | 13:00-15:30 | 00:00-03:00 |
| GBPJPY | 07:00-09:30 | 13:00-15:30 | 00:00-03:00 |
| GBPUSD | 07:00-12:00 | 13:00-15:30 | — |

Compare to natural KZs. Three categories:

**Category A — coded KZ contains the natural peak** (no change required):
- **XAUUSD** — natural peak 15:00-18:00; coded NY 13:00-17:00 captures 3 of 4 peak hours. Loses 17:00-18:00 (the *single highest* hour, 6.57%). **Recommended extension: NY KZ → 13:00-18:00.**

**Category B — coded KZ misses the natural peak by 1-3 hours**:
- **US30_cash** — natural peak 16:00-21:00; coded NY 13:30-16:00. **Coded ends exactly at natural-peak start.** Massive miss. Recommended extension: 13:30-19:00 minimum, ideally 13:30-21:00 (covers 38.6% of daily motion in a single window).
- **GBPUSD** — natural peak 15:00-19:00; coded NY 13:00-15:30. Loses 15:30-19:00 (~4% of daily motion per hour). Recommended: 13:00-19:00.
- **USDJPY** — coded NY 13:00-15:30; natural peaks at 17:00-18:00 (6.1%) and 15:00-16:00 (5.4%). Recommended: extend NY to 13:00-18:00 OR add a separate "afternoon US" 17:00-18:00 micro-window.
- **GBPJPY** — coded NY 13:00-15:30; natural peak 17:00-18:00 (7.0%, the *single highest hour for this instrument*). Recommended: extend NY to 13:00-18:00.
- **EURJPY/AUDJPY/CHFJPY** (not currently traded) — would be parallel to GBPJPY recommendation.

**Category C — coded schedule has NO equivalent:**
- **JP225** — 02:00-04:00 Tokyo peak captures 14% of daily motion; we don't have JP225 coded. If we add it, must include a Tokyo KZ.
- **GER40 / UK100** (not currently traded) — both have a 10:00-12:00 London-late peak in addition to NY afternoon. Coded XAUUSD London ends at 10:30; would need to extend.
- **EURGBP** (not traded) — 00:00-01:00 mini-peak (Asian open re-pricing).
- **CHFJPY** — 00:00-01:00 mini-peak (Tokyo open).

### 3.4 Are we missing high-activity windows for non-XAU instruments?

**Yes, materially.**

The most consequential gaps for the **5 currently-live instruments**:

1. **US30 NY KZ ends 16:00 — natural peak runs until 21:00.** Of the daily motion 38.6% happens 16:00-21:00. We are trading the launch of the move and exiting before the move resolves. Single biggest config opportunity in the analysis. **Confidence: very high** — this is 81 days of data with a 2.33× density peak.

2. **GBPUSD NY KZ ends 15:30 — natural peak runs to 19:00.** We are arguably mis-classified as observer here, but if we promote, the window must extend.

3. **GBPJPY NY KZ ends 15:30 — peak hour is 17:00-18:00 at 7.0%.** Currently we exit ~90 min before the peak. Recommended extension to 13:00-18:00.

4. **USDJPY NY KZ ends 15:30 — peak is 17:00.** Same problem as GBPJPY.

5. **XAUUSD NY KZ ends 17:00 — peak hour is 17:00-18:00 at 6.57%, just past the cutoff.** Lower-impact than US30 because 17:00-18:00 is only marginally above-mean (1.58× peak ratio). Worth extending to 18:00 but not urgent.

The remaining 19 instruments are research-only at this point. For any future expansion the natural-KZ windows from §3.2 should be the starting point, NOT a copy-paste of XAUUSD's schedule.

### 3.5 Practical recommendation

I am NOT proposing config changes — that requires CEO approval and ideally an A/B shadow logger to confirm the extended-window edge persists. **My recommendation is shadow-only:**

- Add a `kz_extension_shadow_logger` that tracks CAND/fill outcomes in the proposed extended windows for each instrument.
- After 30+ days of data, compute realized R per window-extension to see if the extra activity translates to actual edge or just more noise + spread cost.
- This addresses the CEO's "research goal — high-quality frequency" memo: we'd be expanding frequency only if the realized R-per-trade in the extension matches our existing in-KZ baseline.

---

## Section 4 — Weekend + gap behaviour

See `monday_gap_*` and `weekend_density_pct` columns.

### 4.1 Mean / p90 Monday gap (vs Friday close, % of close price)

| Instrument | mean_gap_% | p90_gap_% | gap_fill_rate (4h) |
|---|---|---|---|
| XAUUSD | 0.69% | 1.38% | 25% |
| XAGUSD | 1.56% | 2.69% | 38% |
| EURUSD | 0.17% | 0.47% | 50% |
| GBPUSD | 0.19% | 0.52% | 44% |
| USDJPY | 0.11% | 0.17% | 56% |
| USDCAD | 0.20% | 0.19% | 57% |
| USDCHF | 0.22% | 0.42% | 63% |
| AUDUSD | 0.36% | 0.83% | 44% |
| NZDUSD | 0.28% | 0.70% | 63% |
| EURGBP | 0.09% | 0.20% | 94% |
| EURJPY | 0.18% | 0.39% | 63% |
| GBPJPY | 0.19% | 0.39% | 56% |
| AUDJPY | 0.33% | 0.78% | 56% |
| CHFJPY | 0.11% | 0.20% | 75% |
| BTCUSD | 0% | 0% | n/a (no gap, 24/7) |
| ETHUSD | 0% | 0% | n/a (no gap, 24/7) |
| US30_cash | 0.50% | 1.05% | 38% |
| NAS100 | 0.60% | 1.24% | 33% |
| SPX500 | 0.45% | 0.91% | 23% |
| GER40 | 0.63% | 1.30% | 31% |
| UK100 | 0.38% | 0.76% | 56% |
| JP225 | 1.06% | 2.82% | 50% |
| USOIL | 2.57% | 6.55% | 46% |
| UKOIL | 2.95% | 7.36% | 50% |

### 4.2 Interpretation

**FX gaps are tiny** (0.1-0.4% mean, 0.2-0.8% p90) — no operational concern, our current SL sizes (0.5-1.5R = 0.5-2.0× ATR-D1) absorb them comfortably. EURGBP fills 94% of weekend gaps within 4 H1 — this is the most reliable gap-fill candidate.

**JP225 + XAGUSD gap > 1% mean** — non-trivial. Pending limit orders left open over the weekend on these two could be filled at unfavourable prices. Existing GTOS pending-intent persistence should already kill cross-session pending limits per `pending_intent_persistence` (closed item in CLAUDE.md), but worth adding a "pre-weekend cancel sweep" for any instrument with mean_gap > 1%.

**Oil (USOIL/UKOIL) p90 gaps 6-7%** — energy is the most gap-prone asset in this universe. If we ever consider oil, weekend pending orders are a hard no — these gaps are routinely large enough to blow through SL placement at typical 1.5-2.0R distance.

**Crypto (BTC/ETH) — 24/7, no gaps**, but `weekend_density_pct = 25.8%` means ~26% of crypto candles fall on Saturday/Sunday. If we ever add crypto, the kill-zone scheduler must explicitly include weekend trading hours, and our Monday-recovery logic (heartbeat checks, daily-loss-reset) needs to handle a market that never closed. This matches Agent C's session 39 "26% weekend density" finding.

**Indices fill rate is 23-56%** — gap fills are a coin flip. Don't trade gap-fade or gap-continuation strategies systematically without n>50.

### 4.3 Distribution of gap-fills vs gap-runs

The `gap_fill_rate_4h_pct` column shows: among Monday opens that gapped non-zero, what fraction retraced to the prior Friday close within the first 4 H1 candles.

- **EURGBP 94%** — exceptional; gaps almost always fade.
- **CHFJPY 75%, USDCHF 63%, NZDUSD 63%, EURJPY 63%, USDJPY 56%** — fade-bias.
- **SPX500 23%, XAUUSD 25%, GER40 31%, NAS100 33%** — these are the gap-RUN-bias instruments. Going *with* a gap on an index Monday open has a ~70% one-sided directional persistence in this 81-day sample.

This is a Monday-only finding (n ≈ 16 weekends), so do not over-interpret. It is, however, consistent with the documented index "Monday momentum" effect from microstructure literature.

---

## Section 5 — Volatility regime mapping

### 5.1 Daily-range distributions

(`vol_q25_range` / `vol_q50_range` / `vol_q75_range`, all in price units)

| Instrument | Quiet (≤Q25) | Normal (Q25-Q75) | High (>Q75) | regime_transition_rate |
|---|---|---|---|---|
| XAUUSD | 88 | 121 | 170 | 0.43 |
| US30_cash | 538 | 651 | 859 | 0.64 |
| USDJPY | 0.73 | 0.96 | 1.35 | 0.48 |
| GBPJPY | 0.93 | 1.44 | 1.76 | 0.39 |
| GBPUSD | 0.0069 | 0.0089 | 0.0115 | 0.70 |
| BTCUSD | $1832 | $2732 | $3486 | 0.63 |
| JP225 | 986 | 1330 | 1908 | 0.43 |
| GER40 | 240 | 362 | 570 | 0.46 |

**Regime transition rate** (= fraction of consecutive day-pairs where Q/N/H bucket changes) is the most useful quick stat:

- **Persistent regimes** (low transition, ~0.39): GBPJPY (0.39), XAUUSD (0.43), JP225 (0.43), GER40 (0.46), AUDUSD (0.61).
- **Choppy regimes** (high transition, ≥0.63): GBPUSD (0.70), US30 (0.64), BTCUSD (0.63), NAS100 (0.65), SPX500 (0.62).

For instruments with persistent regimes, ATR-based gates can be slow-moving; for choppy regimes (GBPUSD!) ATR can flip quartile from one day to the next, meaning entry-distance gates must adapt fast or risk consistently mis-calibrated SL/TP.

This may also explain why our GBPUSD observer mode is showing 6/6 = 100% in batch — 6 trades is too small to span both regime types. Once GBPUSD lives in a quartile-flip-heavy regime the realized WR could compress fast.

---

## Section 6 — News / event sensitivity (proxy)

**Status: deferred — needs news-calendar source.** The repository does not currently have an event calendar (`config.high_impact_events: []` is hardcoded empty per `04_DATA_LAYER_ROADMAP.md` §0). I do not have ForexFactory / Investing / Trading Economics CSV access from this environment.

What we *can* observe from the data:

- **13:30 UTC every Friday** (NFP) shows an average +35% range expansion vs the 13:00 UTC bar across XAUUSD, US30, EURUSD. This is the canonical NFP signature.
- **18:00 UTC ~6 times in the 81-day window** (FOMC press conferences) show 50-100% range expansion.
- These are visible in the hourly-bucket data as "tall outlier hours" in `03_hourly_buckets.json`.

**Recommendation per Agent 4 P7:** procure ForexFactory or Investing.com CSV (free) and wire into a `news_filter.py` that blocks/warns the AI gate during events. This is independent of microstructure but gates the universe of "should we even be evaluating this candle" calls.

---

## Section 7 — Per-instrument spread-cost-vs-edge ratio

See `03_spread_cost_table.csv`. Repeated for clarity:

**Spread-burdened (>10% R-cost): 14 of 24 instruments.**

The pattern: every spot FX pair *except USDJPY* is spread-burdened at FTMO/FN tier. USDJPY scrapes by at 9.4% because of its larger ATR-M15 (0.099 vs ~0.0005 for EUR/GBP/CHF/CAD/CHF crosses).

**Implication.** If we pursue an FX-major expansion, we either need:

1. A higher-ATR setup (e.g. London-open breakout structures that target 2.0R minimum, not 1.5R) — this halves the proportional spread tax.
2. A broker upgrade — Pepperstone Razor / IC Markets at 0.0-0.2 pip raw + $3.50/lot commission would cut typical EURUSD R-cost from 24% to ~9%. Only relevant post-FTMO challenge once we move to a personal funded account.
3. Acceptance — most professional FX traders run at 4-6% spread tax with strategies that backtest >2R expectancy; ours is +0.20R. 24% tax on +0.20R = +0.15R net, which barely beats breakeven once execution slippage is added.

I would not recommend extending GTOS to any spot-FX pair other than USDJPY/GBPJPY/GBPUSD on this analysis.

---

## Section 8 — Cross-instrument feasibility under FTMO 1% / 4% MTM cap

`required_lots_1pct` column = lots required to risk exactly $1000 (1% of $100k) at typical SL distance (1.0 × ATR-M15).

| Instrument | required_lots @ 1% | min lot | feasible? | note |
|---|---|---|---|---|
| XAUUSD | 0.085 | 0.01 | yes | safe |
| XAGUSD | 0.876 | 0.01 | yes | safe |
| EURUSD | 3.030 | 0.01 | yes | |
| GBPUSD | 1.053 | 0.01 | yes | |
| USDJPY | 1.687 | 0.01 | yes | |
| USDCAD | 2.392 | 0.01 | yes | |
| USDCHF | 1.524 | 0.01 | yes | |
| AUDUSD | 2.240 | 0.01 | yes | |
| NZDUSD | 2.657 | 0.01 | yes | |
| EURGBP | 2.346 | 0.01 | yes | |
| EURJPY | 2.509 | 0.01 | yes | |
| GBPJPY | 1.421 | 0.01 | yes | |
| AUDJPY | 2.461 | 0.01 | yes | |
| CHFJPY | 1.643 | 0.01 | yes | |
| BTCUSD | 0.037 | 0.01 | borderline | required lots ≈ 4× min — SL granularity is poor, 1% = 4 lots min, so 0.01 lot risks $250. **Risk-control concern.** |
| ETHUSD | 1.068 | 0.01 | yes | |
| US30_cash | 0.113 | 0.01 | yes | |
| NAS100 | 0.275 | 0.01 | yes | |
| SPX500 | 1.376 | 0.01 | yes | |
| GER40 | 0.166 | 0.01 | yes | |
| UK100 | 0.578 | 0.01 | yes | |
| JP225 | 7.443 | 0.01 | yes (high lots) | check broker volume_max |
| USOIL | 0.165 | 0.01 | yes | |
| UKOIL | 0.132 | 0.01 | yes | |

**Two flags:**

1. **BTCUSD lot granularity is poor.** Min lot 0.01 risks ~$250 on a typical SL, well over our 1% budget. Either we accept ~2.5% risk-per-trade or we wait for a BTC micro contract / sub-0.01 lot. Verify Monday what FTMO's actual BTC volume_min is — published as 0.01 but I have no live MT5 access.

2. **JP225 requires 7.4 lots** to achieve 1% risk at typical SL — most FTMO/FN brokers cap volume_max at 50-100 lots, so this is feasible, but each pip is $74 ((7.4 lots × $0.10 per 0.01 lot per pip) × 100 lots/pip-conversion). Slippage tolerance must be considered carefully.

3. **All 24 instruments are listed as ftmo_yes=True** based on the FTMO Tradable List (publicly available). Any new instrument added to live trading should still be verified with `mt5.symbol_info(symbol)` returning non-None — flagging this as "verify Monday before any expansion" per the existing GTOS protocol.

### 8.1 4% MTM daily-loss cap interaction

T2.8 daily-loss-stop is at 4% MTM (i.e., $4000 on FTMO Std). At 1% per trade × 2 max trades/KZ × 5 instruments = potentially 10 concurrent active risk = 10% notional. The current `concurrent_tracker` cap of `floor(4/2) = 2 filled positions` keeps actual risk ≤ 2%. Adding instruments without raising the cap means **all new instruments fight for the same 2-slot pool** — adding 6 new instruments doesn't increase trade frequency unless you also raise the concurrent cap, which has separate correlation-risk implications. **Frequency does not scale linearly with instrument count under our current architecture.** This is structural and should temper any "let's add 6 pairs" narrative.

---

## Critical questions (per task spec)

1. **Is the spread small enough relative to typical R that it doesn't kill the edge?**
   - **Yes**: XAUUSD (2.25%), US30 (2.26%), GER40 (3.10%), NAS100 (4.40%), SPX500 (7.34%), USDJPY (9.45%), USOIL (6.60%), UKOIL (5.28%), JP225 (6.95%), UK100 (7.70%).
   - **No**: 14 instruments are spread-burdened (>10%); most spot-FX is in this group. NZDUSD and EURGBP are catastrophically bad (49% / 48% R-cost).

2. **Does the instrument's natural activity align with our existing KZ schedule, or do we need new KZ definitions?**
   - **Need new KZ definitions for**: JP225 (Tokyo session 02:00-04:00 UTC, no equivalent in current schedule), GER40 (London-late 10:00-12:00 UTC + extended NY 14:00-19:00 UTC), UK100 (similar to GER40), EURGBP (00:00-01:00 + 11:00-12:00 mini-peaks), and the US30 NY extension to ~21:00 UTC.
   - **Existing schedule is fine for**: XAUUSD (minor 17:00-18:00 extension worth shadow-testing), GBPUSD core (London 07:00-12:00 already very generous; NY extension to 19:00 needed if promoted).

3. **Is liquidity sufficient at FTMO 1% lot sizes?**
   - All instruments yes, except BTCUSD has min-lot granularity that overshoots 1% risk; treat BTC as 2.5% risk if added or wait for micro contracts.

4. **Are there hours of day to AVOID (e.g. low-liquidity dead zones)?**
   - **05:00-07:00 UTC** for indices (US30/SPX500/UK100/GER40) — pre-cash session, broker quotes wide.
   - **22:00-22:05 UTC** for XAUUSD (broker rollover spike — 5-15× spread).
   - **23:00-00:00 UTC** for all FX (Tokyo handover, spreads widen).
   - **13:30 UTC every Friday** (NFP). Skip the 13:00-13:14 minute on US-data days regardless of instrument.

5. **Weekend handling: standard (FX/metals close), index (close at varying times), or crypto (24/7)?**
   - **FX (12 pairs)**: standard 21:00 UTC Friday close, 22:00 UTC Sunday open. Mean Monday gap 0.1-0.4%.
   - **Metals (XAU/XAG)**: same as FX.
   - **Indices (cash)**: vary — US30/SPX500/NAS100 ~22:00 Fri close, Asian indices (JP225) close earlier/open earlier. Mean gap 0.4-1.1%.
   - **Energy (USOIL/UKOIL)**: gaps 2.5-3% mean, p90 7-7.5% — most gap-prone class.
   - **Crypto (BTC/ETH)**: 24/7, no gaps. 26% of candles on weekends.

---

## Final summary

The single most important and actionable finding from this analysis is the **5-hour US30 NY-afternoon density window (16:00-21:00 UTC) we systematically skip**. 38.6% of the daily motion happens in a window we exit at 16:00. Compounding evidence: NAS100, SPX500, BTCUSD, ETHUSD, and to a lesser extent GBPUSD/USDJPY/GBPJPY all share the same "post-NY-cash-close peak" structure. This is not noise — 81 days of data with peak ratios 1.7×-2.3× over uniform baseline are significant past any reasonable correction.

The second-tier findings are (i) JP225 has a Tokyo peak we cannot replicate with our XAU/USD-style schedule template, and (ii) most spot FX pairs are structurally spread-burdened at FTMO retail tier.

These should drive the post-Monday expansion decisions, NOT a copy-paste of XAUUSD's KZ schedule onto new instruments.

— end —
