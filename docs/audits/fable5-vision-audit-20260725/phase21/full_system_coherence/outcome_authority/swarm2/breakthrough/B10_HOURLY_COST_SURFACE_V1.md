# B10 — THE HOURLY COST SURFACE, BUILT FROM THE TAPE

**Breakthrough lane 10, 2026-08-12.** Code `b10_hourly_cost/`, receipts `b10_hourly_cost/receipts/`.

**Measurement and construction only.** No broker call, no VPS touch, no config byte, no `src/` edit,
no git write, no live path. Confers no arming, sizing, promotion or activation authority.

Every number below carries `n`, an interval where one is meaningful, and a named source. Where I
refuted my own construction I left the refutation in and said which line produced it.

---

## 0. HEADLINE

> ### The composed five-month restatement is **−1.398 R**, not −6.090 R, and the difference is a keying defect rather than a disagreement about the tape.
>
> | basis | five-month total | Feb | Apr | May | Jun | Jul |
> |---|---:|---:|---:|---:|---:|---:|
> | as sealed | **+0.954** | +14.168 | −7.742 | +5.130 | +3.964 | −14.566 |
> | Lane 7, as published | **−6.090** | +14.062 | −7.736 | +5.135 | +1.176 | −18.727 |
> | *Lane 7's own instrument, re-keyed to the exact hour* | *−2.704* | *+14.003* | *−7.737* | *+5.128* | *+2.416* | *−16.515* |
> | B10 tape-true, hourly, broker-clock keyed | −1.824 | +14.146 | −7.736 | +5.136 | +2.685 | −16.055 |
> | B10 tape-true, 15-minute | **−2.052** | +14.041 | −7.730 | +5.120 | +2.802 | −16.286 |
> | **B10 + RECON's exit-leg slippage — the composed number** | **−1.398** | **+14.285** | **−7.616** | **+5.159** | **+2.906** | **−16.132** |
>
> Lane 7 keyed its per-hour spread ratio on `utc_session.str.extract(r'moonshot_h(\d\d)')`. That label
> exists only for the `moonshot_hNN_NN` sessions, so **175 of the 282 sealed trades (62.1 %) carried no
> hour and fell back to a symbol-level median ratio** — including **46 of the 74 UK100 trades**, the
> symbol that carries the entire correction. All 46 sit in UTC hours 07–15, the London cash session,
> where UK100's true multiplier is **0.74–0.98** and the model is approximately *right*; they were
> charged at UK100's symbol median of **1.445**. A further **23 of the 107 rows that did have a label
> are off by one hour**, because `moonshot_h17_18` is a window and a decision at 18:00:00 belongs to
> its second hour. The exact UTC instant is on every row in `decision_window_id`
> (`timewarp:2026-02-02T03:30:00+00:00`); B10 reads it there, 282 of 282.
>
> **The finding survives; its size does not — which is the same sentence Lane 7 wrote about its own
> first pass, one resolution level down.** Priced from the tape the record is still negative and
> February's PASS still survives (+14.168 → +14.285 composed).
>
> ### The rollover is a BROKER-clock event and the estate keys on UTC. Every hour analysis over a span crossing a DST boundary is mis-keyed, including — before I fixed it — this one.
>
> Broker wall = `America/New_York + 7`, so broker 00:00 is **UTC 21:00 for 238 days of 2026 (65.2 %)
> and UTC 22:00 for the other 127 (34.8 %)**. A naive year-long UTC-hour-21 bucket **understates the
> true rollover spread by 27.8–32.1 %** on all twelve FX pairs, while UTC-hour-22 — an otherwise
> ordinary hour — is **overstated 2.4× to 5.0×** (EURUSD 5.00×, CHFJPY 4.71×, USDJPY 4.27×).
> **Crypto is exempt** (BTCUSD 1.01×, ETHUSD 1.00×) and **every cash CFD is shut at the rollover, so
> it cannot be smeared at all** — this is an FX-only defect. The sealed months straddle the
> 2026-03-08 transition (February is EST, April–July EDT): **28,969 of 146,745 pool fills (19.7 %)
> and 105 of the 282 sealed trades sit on the far side.** B10 re-keys on the broker clock;
> `feature_contract.py:207` does not.
>
> ### The defect is real, and the fix is four lines, because the estate already owns the measurement.
>
> `src/costs/spread_model.py:396` reads **only** `by_class_hour_of_week`. `SPREAD_MODEL_V1.json` also
> carries **`by_symbol_hour_of_week` for 36 broker symbols** — including `UK100.cash` and
> `GER40.cash` — and **no code in the tree reads it.** Measured independently against 300,538,915
> ticks, that dead table agrees with the tape to a **median 0.64 %** across all 24 surface symbols.
> The class pool averages UK100's genuine 8.9× hour cycle with SPX500/NAS100/US30/JP225, which are
> genuinely hour-flat, and prints 1.30×.
>
> ### The armed book's rollover exposure is ~zero on the three sleeves the commission names, and it is large on the fourth.
>
> **Every cash CFD is CLOSED at 21:00 UTC** — measured, zero ticks in that hour for USOIL_cash,
> UKOIL_cash, XAUUSD, UK100, GER40, US500. So `energy_agri` (0 of 2 symbols open) and
> `sub_xvol_pullback` (0 of 18) have **no rollover slot at all**; their H4 grid has five live
> decision instants, not six. `crypto` **is** open — and pays nothing: BTCUSD's rollover multiplier
> is **1.00** and its rollover spread is **0.005 R**. The exposure lands entirely on
> **`sub_mid_dn_revert`**, which `src.safety.armed_set` reports armed on both accounts and the
> commission's three-sleeve list omits: **5 of its 20 symbols are JPY crosses**, and at the rollover
> they quote **USDJPY 18.61× / CHFJPY 15.71× / GBPJPY 12.07× / AUDJPY 9.14× / EURJPY 7.53×** their own
> reference median — 5.8, 29.8, 24.0, 11.0 and 9.4 pips.
>
> ### The LIMIT branch's last reopener is CLOSED by this measurement.
>
> A sibling lane left three falsifiable reopeners; the strongest was *"a tape measurement showing the
> rejected rows' modelled 0.4402 cost is materially too high."* At tape truth it is **0.47792 — 8.6 %
> MORE expensive, not less**. Only **568 of 28,922 (1.96 %)** cross back under the 0.20 gate, they
> realise **−0.167 R, CI [−0.371, +0.046]** — not clearing zero — and **57.2 % of the rejected set
> could not clear the gate with the spread set to exactly zero**. The population is **BTCUSD (24.8 %)
> and ETHUSD (17.6 %)**, whose gate cost is commission (BTCUSD spread is **1.7 %** of its 0.6217) and
> whose hour model the tape says is already right to 0.03 %. **The cost gate is correctly rejecting
> them.**
>
> ### Hour-of-day works as a generation parameter, and delaying entry does not.
>
> An expensive hour is **not** expensive because it is informative: Spearman ρ between an hour's tape
> spread and its pre-cost gross is **−0.811 (p 1.5 × 10⁻⁶, 24 hours)**, surviving leave-out-hour-21
> (**−0.786, p 8.9 × 10⁻⁶**). Cheap-half pre-cost gross **−0.145 [−0.166, −0.124]** against
> expensive-half **−0.253 [−0.277, −0.228]** — disjoint CIs. **Delaying entry is refuted at t = −25.5**:
> on the trades D60 still takes it saves **+0.0091 R** of spread and pays **−0.211 R** of worse entry
> price, a **23× adverse ratio** — the same shape as Lane 7's passive-execution refutation, worse.

---

## 1. WHAT WAS BUILT, AND ON WHAT

| instrument | scope |
|---|---|
| tick archive, fully reduced | `/Users/borr/GTOSActive/vps-ticks-20260726/`, **61 files, 300,538,915 rows**, FTMO 36 / redacted_account 25, **0 bad rows, 0 inverted quotes** (`receipts/TAPE_REDUCE_LOG.jsonl`) |
| clock | broker wall → UTC by `new_york_plus_7` (`src/utils/broker_clock.py`), NY = EDT for the whole window, so a verified constant **+3 h**; checked at three epochs on both servers |
| hourly surface | `receipts/TAPE_SPREAD_HOURLY_V1.json` — 61 symbols × 24 UTC hours × 7 weekdays |
| sub-hour surface | `receipts/B10_SUBHOUR_AND_BARMIN_V1.json` — 15-minute grid + the bar-minimum defect |
| dual-clock + DST | `receipts/B10_DUAL_CLOCK_AND_DST_V1.json` — every cell keyed in both clocks, the smear priced, the close-anchored quarter measured |
| LIMIT reopener | `receipts/B10_LIMIT_REJECTED_POPULATION_V1.json` — the 28,922 cost-gate-rejected LIMIT rows repriced |
| sealed record | 282 resolved selected trades (`frozen3.pkl`, Lane 7's own assembly, unmodified) |
| candidate pool | 146,745 filled occurrences over five months (`filled.pkl`) |
| price walk | 21,684 MARKET candidates on the M1 bid/ask tape (`lg_cov.pkl` + `m1/`) |

**Coverage, honestly stated.** FTMO: **24 of 24 surface symbols present, 822 hour cells and 4,296
hour-of-week cells, zero thin cells.** redacted_account: 25 symbols, 16 of the 24 surface names — the other
eight ship under redacted_account's own tickers (`GER30`, `NDX100`, `US30`, `UKOUSD`, `USOUSD`) and are
resolved by alias in `tape_hourly.py`; `UK100`, `SPX500` and `JP225` are present under their own names.

**Distributional, because the spike is a tail.** Every cell publishes p10/p25/p50/p75/p90/p99 from a
log-spaced histogram (40 bins per decade over 1e-6…1e4, log-linear interpolation inside the bin),
tick-weighted *and* time-weighted (dwell to the next tick, capped at 60 s so a market hole cannot
dominate an hour), plus a **day-clustered bootstrap CI** on the mean (2,000 draws, seed 20260812). A
mean is the wrong summary here and the artifact says so: UK100's reference distribution is bimodal at
**mean/median = 2.37**.

**Independent validation before anything was built on it.** EURUSD's tick-weighted hourly spread
reproduces Lane 5's independently-measured figures: worst **3.7453 bps at 21:00 UTC** against Lane 5's
3.745, best **0.0659 at 15:00 UTC** against Lane 5's 0.066. UK100's hourly means reproduce Lane 7's
tape row to within a few percent at every hour it published.

**Fallback ladder**, stamped on every cell it produces:

| rung | key | condition | used on the 282 |
|---|---|---|---|
| 1 | `SYMBOL_HOUR_OF_WEEK` | ≥ 200 ticks in that (weekday, hour) | **259** |
| 2 | `SYMBOL_HOUR` | ≥ 500 ticks in that hour | **23** |
| 3 | `CLASS_HOUR` | class median of per-symbol multipliers; stamped TRANSFERRED | 0 |
| 4 | `GLOBAL_HOUR` / `FLAT` | stamped MODELLED so a consumer can refuse it | 0 |

All 282 sealed trades priced at coverage **MEASURED**.

---

## 2. THE DEFECT, AT THE LINE THAT CAUSES IT

```python
# src/costs/spread_model.py:396
h = ((shape.get("by_class_hour_of_week") or {}).get(klass) or {}).get(how)
```

That is the whole of the hour term. `by_symbol_hour_of_week` — 36 broker symbols, present in the same
artifact — is never referenced anywhere in the tree.

`receipts/SHIPPED_VS_TAPE_V1.json`, all 24 surface symbols, FTMO. `err` is *shipped ÷ tape*, so below
1 means the model undercharges:

| symbol | class | tape hour ratio | class hour ratio | worst class err | **by-symbol err (median)** | worst UTC hr | tape mult | class mult | by-symbol mult |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **UK100** | index | **9.01×** | 1.30× | **0.157** (6.4× light) | **1.025** | 20 | 6.70 | 1.05 | 6.78 |
| **GER40** | index | 3.21× | 1.30× | **0.348** (2.9× light) | 1.020 | 20 | 3.02 | 1.05 | 3.04 |
| **EURUSD** | fx | 35.07× | 16.67× | **0.485** | 1.001 | 21 | 34.34 | 16.67 | 32.00 |
| GBPUSD | fx | 33.49× | 16.67× | 0.505 | 1.007 | 21 | 33.03 | 16.67 | 38.00 |
| USDJPY | jpy_fx | 18.90× | 13.70× | 0.589 | 1.004 | 21 | 18.61 | 12.56 | 19.33 |
| JP225 | index | 1.95× | 1.30× | 0.669 | 1.002 | 22 | 1.94 | 1.30 | 1.91 |
| SPX500 | index | 1.09× | 1.30× | 0.997 | 0.999 | 20 | 1.02 | 1.05 | 1.05 |
| BTCUSD | crypto | 1.01× | 1.00× | 0.997 | 1.000 | 21 | 1.00 | 1.00 | 1.00 |
| *(18 others)* | | | | 0.70–0.98 | 0.98–1.05 | | | | |

**Median |by-symbol err − 1| over all 24 = 0.0064.** The dead table is right; the live path does not
read it.

Three symbols are undercharged by ≥ 2× at their worst hour: **UK100, GER40, EURUSD**. Note the class
term is also *too expensive* in places — SPX500 at 20:00 UTC is charged 1.05 against a tape 1.02, and
the patched model prices it **0.87×** the shipped value.

**Two repairs, different sizes.**

1. **Read `by_symbol_hour_of_week` first.** Four lines at `:396`. Recovers a measurement already
   sealed in the shipped artifact. On the sealed record it alone gives **−2.346 R**.
2. **`b10_hourly_cost/tape_hourly.py`** adds what that table has not got: redacted_account coverage, the
   distribution rather than a point, day-clustered CIs, a per-cell coverage stamp, a 15-minute rung,
   and a documented ladder. On the sealed record: **−2.024 R**.

### Drop-in, demonstrated against the live class

`patch_spread_model(model, TapeHourly())` replaces only the third factor of
`anchor × era_ratio × intraweek`, preserves the volatility sub-term, and returns the original bound
method so a caller can A/B without rebuilding. Run against the real `load_spread_model()` at
2026-07-01 20:00 UTC:

| symbol | shipped | patched | ratio |
|---|---:|---:|---:|
| UK100 | 1.0121 px | **5.5979 px** | ×5.53 |
| SPX500 | 0.7197 px | 0.6272 px | ×0.87 |

### H1 membership — every file a repair would touch

Checked against **R2** (`B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json`):

| path | R2 binding |
|---|---|
| `src/costs/spread_model.py` | **unbound — free to edit** |
| `src/costs/model.py`, `src/costs/lifecycle.py` | **unbound** |
| `research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json` | **unbound** |
| `src/research_infra/walkforward/quote_side.py`, `gate.py`, `spec.py` | **unbound** |
| `src/research_infra/wave21_forward_shadow/shadow_costs.py`, `shadow_lifecycle.py` | **unbound** |
| `src/research_infra/v4_timewarp_simulated_live_research_loop.py` | **BOUND** (`common_behavior_inputs`) — not touched |
| `config/agent_config.yaml` | **BOUND** — not touched |

**The whole cost/spread stack is unbound.** The repair costs no re-seal and no 16.5 h re-run. B10
edited none of them; `tape_hourly.py` is a sidecar.

---

## 2A. BOTH CLOCKS, AND THE DST SMEAR THAT HAS NOW COST TWO LANES

**The rollover is a broker-clock event. The estate buckets by UTC. Those agree only inside one DST
regime.** Broker wall = `America/New_York + 7` (`src/utils/broker_clock.py`), so the offset is
**+3 h under EDT and +2 h under EST**, and

| | broker 00:00 lands at | days of 2026 | share |
|---|---|---:|---:|
| EDT (2026-03-08 → 2026-11-01) | **UTC 21:00** | 238 | **65.2 %** |
| EST (the rest) | **UTC 22:00** | 127 | **34.8 %** |

B10's own tape window (2026-06-18…07-26) is **entirely EDT**, so the measured surface is a clean
single-regime observation and is *not* smeared. Everything below is what happens when that surface —
or any UTC-bucketed statistic — is applied across a transition.

### 2A.1 What a naive UTC bucket reports, against the truth

`receipts/B10_DUAL_CLOCK_AND_DST_V1.json`. Mean spread in price units; "naive" = the annual blend a
UTC-hour bucket would produce at 2026's regime shares.

| symbol | broker 23 | **broker 00** | broker 01 | naive UTC-21 | **understates rollover** | naive UTC-22 | **overstates a cheap hour** |
|---|---:|---:|---:|---:|---:|---:|---:|
| **EURUSD** | 0.00003 | **0.00043** | 0.00003 | 0.00029 | **−32.1 %** | 0.00017 | **5.00×** |
| CHFJPY | 0.03074 | **0.31084** | 0.02668 | 0.21338 | −31.4 % | 0.12555 | 4.71× |
| USDJPY | 0.00906 | **0.06660** | 0.00641 | 0.04658 | −30.1 % | 0.02735 | 4.27× |
| NZDUSD | 0.00009 | 0.00100 | 0.00010 | 0.00068 | −31.8 % | 0.00041 | 4.00× |
| GBPUSD | 0.00011 | 0.00110 | 0.00012 | 0.00076 | −31.5 % | 0.00046 | 3.86× |
| AUDUSD | 0.00005 | 0.00049 | 0.00006 | 0.00034 | −30.9 % | 0.00021 | 3.58× |
| USDCAD | 0.00008 | 0.00083 | 0.00010 | 0.00057 | −31.5 % | 0.00035 | 3.56× |
| AUDJPY | 0.01862 | 0.11893 | 0.01566 | 0.08403 | −29.3 % | 0.05159 | 3.29× |
| GBPJPY | 0.03478 | 0.24309 | 0.03258 | 0.17061 | −29.8 % | 0.10583 | 3.25× |
| EURGBP | 0.00012 | 0.00077 | 0.00012 | 0.00054 | −29.6 % | 0.00035 | 2.92× |
| EURJPY | 0.02296 | 0.11360 | 0.02007 | 0.08206 | −27.8 % | 0.05262 | 2.62× |
| USDCHF | 0.00010 | 0.00054 | 0.00011 | 0.00039 | −28.5 % | 0.00026 | 2.36× |
| **BTCUSD** | 1.14570 | 1.22754 | 1.20862 | 1.19906 | **−2.3 %** | 1.21520 | **1.01×** |
| **ETHUSD** | 0.60929 | 0.61472 | 0.61612 | 0.61283 | **−0.3 %** | 0.61563 | **1.00×** |
| all 10 cash CFDs | — | **market closed** | — | — | **cannot smear** | — | — |

**The smear is an FX-only defect.** Crypto quotes flat through the rollover; every cash CFD is shut,
so its UTC-21 bucket is empty in one regime and empty in the other. Any statement of the form
"hour 21 is expensive" is true of twelve FX pairs, false of crypto, and undefined for ten cash CFDs.

### 2A.2 Where the spike actually sits, at 15-minute resolution

The rollover premium is not an hour — it is a **75-minute window from broker 23:45 to 01:00**, and the
book goes nearly dark inside it. Multiplier vs the symbol's reference p50; UTC in this window = broker − 3:

| broker time | 23:00 | 23:30 | **23:45** | **00:00** | **00:15** | **00:30** | **00:45** | 01:00 | 01:15 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **EURUSD** mult | 1.98 | 2.70 | **6.01** | **29.76** | **39.89** | **31.90** | **32.79** | 3.31 | 2.72 |
| EURUSD ticks | 14,421 | 7,623 | 5,106 | **667** | 1,572 | 3,632 | 3,264 | 12,263 | 10,611 |
| **USDJPY** mult | 1.82 | 2.41 | **4.32** | **21.44** | **19.95** | **18.50** | **18.49** | 2.12 | 1.31 |
| **GBPJPY** mult | 1.19 | 1.38 | **2.02** | **10.48** | **11.26** | **12.04** | **12.30** | 2.06 | 1.06 |
| **BTCUSD** mult | 1.09 | 1.04 | 1.05 | 1.05 | 1.08 | 1.15 | 1.21 | 1.17 | 1.13 |

**A close-anchored daily signal samples the ramp, not the peak.** The last quarter before broker
midnight (`close_anchored_spread` in the receipt) prices at:

| symbol | close quarter mean px | typical session px | **ratio** | vs reference p50 | n ticks |
|---|---:|---:|---:|---:|---:|
| **EURUSD** | 0.00010 | 0.00001 | **10.08×** | 9.42× | 5,106 |
| GBPUSD | 0.00019 | 0.00004 | 4.96× | 6.00× | 10,680 |
| USDJPY | 0.02057 | 0.00431 | 4.77× | 6.55× | 9,901 |
| EURGBP | 0.00023 | 0.00005 | 4.40× | 4.61× | 9,202 |
| CHFJPY | 0.07299 | 0.01783 | 4.09× | 3.85× | 11,080 |
| … 7 more FX pairs | | | 2.71–3.95× | | |
| **BTCUSD** | 1.13962 | 1.11384 | **1.02×** | 1.10× | 64,532 |
| **ETHUSD** | 0.60970 | 0.60695 | **1.00×** | 0.99× | 11,257 |

This corroborates the sibling lane's independent finding (EURUSD close spread 3.06 bp at broker
hour 00 vs 0.09 bp elsewhere, crypto exempt) and **locates it**: the close *print* sits in the 6×
ramp quarter, the hour *after* it is the 20–40× peak. Which of the two a signal pays depends on
whether it reads the close or transacts into the next bar — and the estate's replay does the latter
(`quote_side.py:53`, entry crosses the spread at the bar boundary).

### 2A.3 The same defect in my own restatement, found and fixed

`TapeHourly` now defaults to `clock="broker"`: it converts the query instant with the real DST rule
and reads the cell the tape recorded at that *broker* hour. `clock="utc"` reproduces the naive
behaviour so the two can be A/B'd, and they are:

| | 282 sealed trades | 146,745 pool fills |
|---|---:|---:|
| rows on the far side of 2026-03-08 (EST) | **105** (all February) | **28,969 (19.7 %)** |
| rows whose multiplier moves | 103 | 28,969 |
| worst single-row multiplier ratio | **1.573×** | — |
| **error if UTC-keyed** | **+0.029 R** | **−14.34 R** |

**On this record the error is small — 0.029 R of a −1.824 R restatement — and I am reporting it
because it is small, not despite that.** None of the 282 sealed trades sits at UTC 21–22 in February
with a material spread. The mechanism is nonetheless exact and it is 13× at the cell level: EURUSD at
2026-02-10 22:30 UTC is broker 00:00 and prices at **27.42×**; a UTC key reads **2.06×**. The same
instant a UTC key charges 27.42× — 21:30 UTC — is actually broker 23:00 and prices at **2.04×**.

### 2A.4 How much of the estate is exposed

| surface | count | exposure |
|---|---:|---|
| `src/` modules carrying `utc_hour` / `utc_session` | **28** | inherit the key |
| audit receipt scripts that bucket by hour **and** touch `spread`/`cost_r` | **72** of 83 | inherit the key |
| the candidate pool's own fields | `utc_hour`, `utc_session` are **stored UTC fields** of every row (`candidate_funnel_analysis.py:195`) | every downstream hour analysis inherits it by construction, including Lane 7's, Lane 1's, Lane 5's and this lane's first pass |
| **the LIVE wave-21 ridge** | `feature_contract.py:48, :50, :205, :207` — **`utc_hour` and `utc_session` are UTC-keyed CATEGORICAL FEATURES** (`"utc_hour": f"{when.hour:02d}"`, `when` = decision time UTC) | **the sharpest one.** The daily prequential refit trains over a growing window that necessarily crosses transitions, so the one-hot level `"21"` means broker 00 (rollover) for 65 % of rows and broker 23 (calm) for 35 %. The model cannot separate them, and `spread_r` / `cost_r` sit in the same feature vector. |

**None of this is a live-money change and B10 proposes none.** The prescription is one line of
convention: **hour features and hour buckets should be keyed on broker wall clock**, which
`src/utils/broker_clock.py` already supplies and fails closed on an unregistered server. It is free
for cash CFDs and crypto and it matters for exactly the twelve FX pairs.

---

## 3. THE RESTATEMENT, AND HOW IT COMPOSES WITH THE OTHER TWO CORRECTIONS

### 3.1 The composition rule

Lane 7 and B10 reprice the **entry / spread** leg. RECON reprices the **exit / slippage** leg. Disjoint
legs, so the **deltas** add — never the restated totals. RECON states the rule itself (§4.2: *"the
slippage-only correction that is safe to add to Lane 7's restated figure is the +0.655 R"*) and names
the trap: RECON's own **entry-leg** term (+0.0066 R) is the *same quantity* as the spread restatement
and must not be stacked on top.

| leg | correction | delta on the 282 |
|---|---|---:|
| entry / spread | B10 tape-true, 15-minute, broker-clock keyed | **−3.006 R** |
| exit / slippage | RECON, selected book's own barrier mix (0.01768 true vs 0.02000 charged) | **+0.654 R** |
| entry / execution error | RECON's +0.0066 R | **excluded — double-count** |
| **composed** | | **+0.954 → −1.398 R** |

RECON publishes +0.655 R for its own term; B10 reproduces +0.654 R from `−0.00232 × 282`.

Day-clustered 95 % CI on the composed five-month total: **[−34.7, +35.0] R**. The sealed figure's
own CI is [−33.5, +35.8]. **At n = 282 none of these corrections is distinguishable from any other
by this record** — Lane 7 said the same about its veto ladder and the point holds here. The pool is
the evidence surface; the 282 are the decision surface.

### 3.2 The reconciliation with Lane 7, done three ways

| instrument | keying | UK100 extra R | five-month net |
|---|---|---:|---:|
| Lane 7 level ratio (`walk.pkl`) | `utc_session` regex, 62 % fallback | **+7.081** | **−6.090** |
| **Lane 7's same instrument, re-keyed to the exact hour** | `decision_window_id` | **+3.630** | **−2.704** |
| B10 tape, hour shape | `decision_window_id` + broker clock | +2.902 | −1.824 |
| B10 tape, 15-minute | `decision_window_id` + broker clock | +3.001 | −2.052 |

Row 2 is the decisive one: **Lane 7's own measurement, unchanged, correctly keyed, moves −6.090 →
−2.704.** The residual to B10 is the tape's larger sample (300.5 M ticks vs one quote per candidate)
plus the broker-clock re-keying of §2A.3.

UK100 by exact hour, showing where the 46 mis-keyed trades sat:

| UTC hr | 0 | 1 | 2 | 6 | **7** | **8** | **9** | **10** | 11 | 12 | **13** | **14** | 15 | 16 | 17 | 19 | 20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| trades | 3 | 2 | 1 | 1 | 4 | 6 | 15 | 10 | 1 | 7 | 6 | 3 | 7 | 4 | 2 | 1 | 1 |
| tape ratio | 4.68 | 4.49 | 4.45 | 1.91 | **0.87** | **0.87** | **0.85** | **0.80** | 0.75 | 0.75 | **0.87** | **0.87** | 1.91 | 1.68 | 1.53 | 1.76 | 6.51 |
| Lane 7 charged | 4.68 | 4.49 | 4.45 | 1.91 | **1.445** | **1.445** | **1.445** | **1.445** | 0.75 | 0.75 | **1.445** | **1.445** | 1.91 | 1.79 | 1.60 | 1.76 | 6.51 |

Bold = the fallback cells. Lane 7 charged 1.445 where the tape says 0.80–0.87 — an over-correction of
roughly 70 % on 46 of 74 trades.

### 3.3 Adversarial check that licensed the whole method — and the one cell that refused

B10 prices an hour **shape** ratio (tape multiplier ÷ model multiplier, each relative to its own
reference). Lane 7 priced a **level** ratio (true quoted spread ÷ modelled quoted spread). If the
per-symbol anchor were also wrong, the shape-only correction would understate.

`adversarial_level_vs_shape.py` over **436 (symbol, hour) cells / 19,403 walked candidates**:
tick-weighted geometric-mean residual **1.008**, per-symbol residuals **0.966–1.082**, UK100 **1.0014**
with a cell-by-cell correlation of **0.992**. **The anchor is right; the hour shape is the whole model
error.**

**One cell refused: UK100 at 15:00 UTC, residual 1.949.** Not noise — resolution. 16:30 London is the
LSE closing auction and it sits inside the hour:

| UTC quarter | :00 | :15 | **:30** | **:45** |
|---|---:|---:|---:|---:|
| mean spread px | 0.736 | 0.719 | **1.995** | **1.755** |
| multiplier vs reference p50 | 0.818 | 0.796 | **2.246** | **1.924** |

Five of the seven sealed UK100 trades in that hour are at :30 or :45.

**My first refinement was wrong and its own validation caught it.** I shipped
`median_mult(h) × mean(h,q)/mean(h)`. That mixes bases in exactly the case it exists for: a bimodal
hour's *median* sits inside the cheap mode, and scaling it by a ratio of *means* lifts it by the right
factor from the wrong base. On UK100 h15:30 it gave **1.50** against a tape truth of **2.246** — 33 %
light, in the one cell the refinement was built for. Replaced with a direct level on a median basis
(median over M15 bars of the bar mean, ÷ the reference p50), validated at hour resolution against the
tick-histogram median over **1,398 cells: median ratio 1.0020, 83.5 % within 10 %**. The superseded
construction is kept in the artifact under `superseded_subhour_factor` so the error stays auditable.

### 3.4 The pool, where the statistics are

146,745 fills, five months (`receipts/B10_POOL_RESTATEMENT_V1.json`):

| | value |
|---|---:|
| extra spread | **+0.00458 R/fill**, **+672.5 R** total |
| share of total cost | **2.15 %** |
| cost | 0.21332 → **0.21790** |
| net | −0.23209 → **−0.23668** |
| of which broker-clock re-keying (§2A.3) | **+14.34 R** |

Lane 7 measured **+0.00933 R per MARKET fill / 693 R**. B10's 672.5 R over 74,249 MARKET fills is
**+0.00906 per MARKET fill** — **agreement to 3 %** from an independent tape and an independent
estimator. **The pool-level correction is where the two lanes agree; the traded-record correction is
where the keying defect lived**, which is exactly Lane 7's own observation that "selection concentrated
the book into the defect", one level sharper.

---

## 4. HOUR-OF-DAY AS A GENERATION PARAMETER

The hour is a property of the bar close today; nothing conditions on it. It is the cheapest possible
generation parameter — symbol and hour are both known before a candidate exists.

### 4.1 The mandate's central question, answered on pre-cost gross

**Is an expensive hour expensive *because* it is informative?** Instrument: pre-cost gross by UTC hour
on the 21,684-candidate walk, where cost cannot contaminate it.

| | value |
|---|---:|
| Spearman ρ (hour tape spread vs hour pre-cost gross), 24 hours | **−0.811**, p **1.51 × 10⁻⁶** |
| same, leave out hour 21 (a 9× spread outlier) | **−0.786**, p **8.94 × 10⁻⁶** |
| Pearson r | −0.940 (−0.799 without h21) |
| cheap-half pre-cost gross | **−0.1448** [−0.1658, −0.1237] |
| expensive-half pre-cost gross | **−0.2526** [−0.2768, −0.2283] |

**No.** The expensive hours are also the *less* informative hours, and the CIs are disjoint. The
trade-off the mandate names does not bind in this population — avoiding the expensive hours costs no
measured signal. That is why Lane 7's cash-session veto failed and a per-symbol tape-conditioned one
need not: Lane 7's rule keyed on a *session calendar*, this one keys on the *measured cost surface*.

Worst hour, for scale (walk, immediate arm): **UTC 21 — gross −1.306, spread 1.863 R, net −3.327 on
n = 458.**

### 4.2 Delaying entry — built, then refuted by its own control

Arms on the same 21,684 candidates and the same M1 tape, risk unit held at each trade's declared
`risk_price`:

| arm | n | breadth | gross | spread | **net/trade** | total R | R/day |
|---|---:|---:|---:|---:|---:|---:|---:|
| A0 immediate | 21,684 | 100 % | −0.1945 | 0.2064 | **−0.5560** | −12,055.9 | −430.6 |
| D15 | 14,743 | 68.0 % | −0.1369 | 0.1287 | −0.3758 | −5,540.4 | −197.9 |
| D30 | 11,935 | 55.0 % | −0.1284 | 0.1147 | −0.3415 | −4,075.4 | −145.6 |
| **D60** | 8,733 | 40.3 % | −0.0963 | 0.0960 | **−0.2786** | **−2,433.4** | −86.9 |
| CHEAP (wait for a cheap hour, ≤ 240 min) | 13,388 | 61.7 % | −0.1376 | 0.1372 | −0.4145 | −5,548.7 | −198.2 |
| **VETO (cheap hours only)** | 11,687 | 53.9 % | −0.1448 | 0.1443 | **−0.4372** | −5,109.4 | −182.5 |
| the half VETO refuses | 9,997 | 46.1 % | −0.2526 | 0.2790 | −0.6949 | −6,946.6 | −248.1 |

D60 looks like the answer. **It is not, and the same-set control says so** (`timing_controls.py`):

| control | D15 | D30 | **D60** | CHEAP |
|---|---:|---:|---:|---:|
| delayed net on the trades it takes | −0.3758 | −0.3415 | **−0.2786** | −0.4145 |
| **immediate net on the *same* trades** | −0.2661 | −0.1765 | **−0.0767** | −0.3943 |
| **paired delta (t)** | −0.110 (−24.4) | −0.165 (−26.2) | **−0.202 (−25.5)** | −0.020 (−10.6) |
| paired spread saving | +0.0005 | +0.0013 | **+0.0091** | +0.0014 |
| paired gross delta | −0.105 | −0.166 | **−0.211** | −0.022 |
| selection share of the apparent spread drop | 99.4 % | 98.6 % | **91.7 %** | 98.0 % |
| book improvement from **skipping** | +8,060 R | +9,950 R | **+11,386 R** | +6,777 R |
| book improvement from **cheaper execution** | **−1,545 R** | **−1,969 R** | **−1,764 R** | **−270 R** |

**The delay pays 0.211 R of worse entry price to save 0.009 R of spread — 23× adverse, t = −25.5.**
Every visible gain is the *skip*: D60 never enters 59.7 % of the candidates because a barrier was
already touched, and those trades would have netted −0.879 R each. That is a "cancel when the thesis
has already resolved" rule wearing a cost rule's clothes. It is worth someone's time — **+11,386 R on
21,684 candidates** — but it belongs to an exit/lifecycle lane, not to this one, and it must be priced
there with its own look-ahead audit.

**Structurally this is Lane 7's passive-execution refutation again**: Lane 7 measured +0.0094 R of
spread saved against −0.0426 R of adverse selection (4.5×). Delaying a *market* order is the same
trade at 23×. Two independent instruments, one conclusion: **on this population you cannot buy a
better price with time.**

### 4.3 The rule that does survive — and its breadth bill

Per-symbol cheap-hour restriction on the full pool (146,745 fills, five months). `precost` is stated
**MARKET-only**, because `precost = gross + spread_r` is invalid on LIMIT rows (Lane 7's own finding 3)
and every cost veto selects toward LIMIT:

| arm | n | breadth | cost | **net** | total R | **R/month** | trades/month | MKT share | **precost (MKT)** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| L0 all | 146,745 | 100 % | 0.2179 | −0.2367 | −34,731 | −6,946 | 29,349 | 50.6 % | +0.0084 |
| **H1 cheap hours only** | 82,622 | **56.3 %** | 0.2097 | **−0.2227** | −18,400 | **−3,680** | 16,524 | 50.7 % | **+0.0130** |
| the refused half | 64,123 | 43.7 % | 0.2284 | −0.2547 | −16,331 | −3,266 | 12,825 | 50.5 % | +0.0025 |
| H2 cheap hours × cost ≤ median | 40,061 | 27.3 % | 0.0467 | −0.0789 | −3,162 | −632 | 8,012 | 34.8 % | +0.0010 |
| H3 cheap hours × cost ≤ p25 | 16,804 | 11.5 % | 0.0200 | −0.0609 | −1,023 | −205 | 3,361 | **0.03 %** | — |
| C cost ≤ p25 only | 36,687 | 25.0 % | 0.0200 | −0.0678 | −2,486 | −497 | 7,337 | **0.01 %** | — |

Per-month net, tape-true, so nobody has to take the pooled figure on trust:

| arm | Feb | Apr | May | Jun | Jul |
|---|---:|---:|---:|---:|---:|
| L0 | −0.1973 | −0.2250 | −0.2485 | −0.2414 | −0.2712 |
| **H1** | **−0.1774** | **−0.2064** | **−0.2375** | **−0.2279** | **−0.2668** |
| refused half | −0.2260 | −0.2496 | −0.2627 | −0.2588 | −0.2766 |

**H1 is better in all five months, on both cost and pre-cost gross, at 56.3 % breadth**, and its
MARKET-only pre-cost gross rises +0.0084 → **+0.0130** while the refused half falls to +0.0025. It is
implementable by the frozen rule because it stays 50.7 % MARKET. It is also **small**: +0.0144 R/fill,
and no month turns positive. Lane 7's arithmetic stands — *halving a cost whose gross is zero yields
zero.*

### 4.4 An adversarial finding about Lane 7's own headline prescription

> **At `cost ≤ p25` the MARKET share is 0.014 % — 5 rows of 36,687. At `cost ≤ p10` it is zero.**

Lane 7's recommended rungs L4/L5 are, arithmetically, **"trade only LIMIT candidates."** Two
consequences it did not draw:

1. Its **"pre-cost gross does not degrade (−0.0188 → +0.00215)"** is computed on a population that is
   ~100 % LIMIT — the exact population its **own finding 3** declares the formula invalid for
   (*"applying it to LIMIT rows inflates pooled pre-cost gross from −0.0188 to +0.0309 and reverses its
   sign"*). Replicating Lane 7's full L4 (drop hours 16–21 + favourable carry + cost ≤ p25) gives
   n = 17,893 at **0.0 % MARKET share** and MARKET precost **−0.0935 on n = 2**.
2. **The frozen rule cannot execute it.** The rule abstains when the top candidate is LIMIT
   (`shadow_select.py:69-71`), so its recommended cost rung selects precisely the arm the rule refuses.

**This is not a refutation of the veto's economics — it is a relabelling.** RECON independently found
the LIMIT arm is the only one with a positive edge at tick truth (**+0.03171 R/trade, t 2.49, CI
[+0.0067, +0.0567]**) while MARKET is **−0.01216**. Lane 7's cost veto and RECON's edge split are
**the same finding reached from opposite directions**: the cheap population *is* the LIMIT population.
Lane 7's rung should be published as **"switch to the LIMIT arm"**, which is a decision about the
abstain rule, not about a cost threshold.

**And that relabelled prescription is then closed by §4A, on this lane's own measurement.** The LIMIT
arm's edge does not live in the part of it a book can reach: the routable 60.1 % is **+0.0050,
t 0.32**, and all the significance sits in the 39.9 % the cost gate rejects — whose modelled 0.4402
cost B10 measures at **0.47792**, higher not lower. So the chain runs: Lane 7's cheap rung *is* the
LIMIT arm → RECON says the LIMIT arm has the edge → **the edge is in the unroutable half and the gate
is right to reject it.** Read §4.4 and §4A together; §4.4 alone would leave a prescription this lane
went on to refute.

### 4.5 Feed to Lane 4 (breadth is a step function of cost per trade)

| quantity | value |
|---|---:|
| cost/trade at L0 | 0.21790 |
| cost/trade at H1 | 0.20968 |
| **Δ cost/trade from the hour rule alone** | **0.00822** |
| breadth L0 → H1 | 146,745 → 82,622 (**−43.7 %**) |

Lane 4 measured that **0.012 R of cost per trade moves breadth 2.5×**. The hour rule's own cost delta
is **0.00822 R** — inside that regime and below the step. Lane 4 should price the interaction
rather than infer it; the number is in `receipts/B10_POOL_RESTATEMENT_V1.json → breadth_feed_for_lane4`.

---

## 4A. THE LIMIT BRANCH'S LAST REOPENER — TESTED, AND IT CLOSES

A sibling lane closed the LIMIT-arm branch and left three falsifiable reopeners. The strongest,
verbatim: *"a tape measurement showing the rejected rows' modelled 0.4402 cost is materially too
high."* B10 is the instrument for it. `receipts/B10_LIMIT_REJECTED_POPULATION_V1.json`.

**Why this lane can test the gate at all, which is not obvious.** The gate is
`row["cost_r"] > MAX_COST_R` (`candidate_funnel_analysis.py:52, :263`), and `cost_r` is **not** the
cost that enters net. Verified identical on all 146,745 fills:

| | `cost_r` (the GATE's input) | `allin_cost_r` (what net pays) | modelled `spread_r` |
|---|---:|---:|---:|
| MARKET | 0.28098 | 0.28098 | 0.14159 |
| **LIMIT** | **0.24450** | **0.14401** | **0.10049** |

**The gate charges a LIMIT candidate a modelled spread that its own realised cost excludes** — and
that modelled spread is exactly the term B10 measured. So if the hourly model over-prices those rows,
the gate is rejecting them for a cost they would not pay even on its own accounting basis.

### 4A.1 The answer: it is not too high. It is too LOW.

n = 28,922 rejected LIMIT rows (39.9 % of the arm), **99.96 % covered by the tape**, priced on the
broker wall clock:

| | modelled | **tape-true** |
|---|---:|---:|
| mean gate cost | 0.44015 | **0.47792** |
| p10 / p25 / **p50** / p75 / p90 | 0.2181 / 0.2512 / **0.3412** / 0.5487 / 0.7931 | 0.2197 / 0.2596 / **0.3685** / 0.5972 / 0.8917 |
| **change** | | **+0.0378 R, +8.6 % MORE expensive** |
| **crossing back under the 0.20 gate** | | **568 rows — 1.96 %** |
| routable rows the tape pushes **over** the gate | | **3,537 — 8.12 %** |

**The tape moves the rejected population the wrong way, and it moves 6.2× more rows out of
affordability than into it.** A tape-true gate would *shrink* the routable LIMIT set from 43,574 to
40,605, not grow it.

Three structural facts make this robust rather than a close call:

1. **The median rejected row needs its cost cut by 1.71× to clear the gate.** A spread multiplier
   cannot do that: the median tape ratio on this population is **0.99883** (p05 0.869, p95 1.792).
2. **57.2 % of rejected rows would still exceed 0.20 with the spread set to exactly ZERO.** Their
   gate cost is carried by commission and swap, which no spread measurement can move. Spread is only
   **29.4 %** of the rejected set's gate cost.
3. **The population is crypto, and crypto is where the hour model is already right.** BTCUSD is
   **24.8 %** of the rejected rows at a gate cost of **0.6217** of which **spread is 0.0104 — 1.7 %**;
   ETHUSD is a further 17.6 %. Their tape ratios are 0.9997 and 0.9988. Their cost is **commission**,
   which Lane 7 measured at 38.0 % of all cost and named an instrument-and-venue choice.

### 4A.2 The 568 that do cross do not clear zero

| | value |
|---|---:|
| n | 568 |
| realised `terminal_net_r` | **−0.16718** |
| day-clustered CI95 | **[−0.3707, +0.0456]** |
| modelled gate cost → tape-true | 0.2118 → 0.1867 |
| realised cost (`allin_cost_r`) | 0.0430 |
| **clears zero** | **no** |

### 4A.3 Concentration — the a-priori test also fails

The reopener's own diagnostic was: *if the rejected rows cluster at the rollover or in the
hour-flat-modelled instruments, the overstatement is likely; if spread evenly, it is not.*

| | rejected set | base rate in all LIMIT | reading |
|---|---:|---:|---|
| share in **UK100 or GER40** | **13.0 %** | **20.4 %** | **under-represented, 0.64×** |
| share at the broker rollover (hour 00) | 1.31 % | 0.58 % | 2.3× elevated, but 1.3 % of the set |
| share in broker hours 23 / 00 / 01 | 4.24 % | — | immaterial |
| Herfindahl by symbol | 0.125 | — | dominated by BTCUSD + ETHUSD |

**The rejected rows are *less* concentrated in the two mis-modelled instruments than the arm as a
whole.** The diagnostic points the wrong way for the reopener.

The one place the tape *does* bite is UK100's rejected rows specifically — median ratio **1.786**,
gate cost 0.3436 → **0.6948**. That is the mirror image of §3.2: the *sealed* UK100 trades sat in the
cheap London hours, while UK100's *cost-rejected* candidates sit in the expensive ones. The gate was
already excluding them, and at tape truth it should exclude them harder.

### 4A.4 Which null you use flips the sign, and that should be stated

The sibling's finding is that the rejected rows beat their cost-implied null. That is true, and it
gets *stronger* at tape truth — but only against the **gate's** accounting basis, not the realised one:

| null | value | edge of the rejected set (realised −0.35369) |
|---|---:|---:|
| −E[gate cost], modelled | −0.44015 | **+0.08646** |
| −E[gate cost], **tape-true** | **−0.47792** | **+0.12422** |
| −E[**realised** cost `allin_cost_r`] | −0.31096 | **−0.04274** |

**Against the cost these rows would actually have paid, the "skill" is negative.** The positive
reading depends on charging them a spread the same accounting says a resting limit does not pay. That
is a real and separate finding about the *null*, not about the tape, and it points the same way as
Lane 7's finding 3 (`precost = gross + spread_r` is MARKET-only).

> **Verdict: the reopener is CLOSED, cleanly.** The modelled 0.4402 is not too high; at tape truth it
> is 0.4779. Only 1.96 % of the rejected rows become affordable, they do not clear zero, 57.2 % could
> not clear the gate at zero spread, and the population is crypto-commission rather than spread. **The
> cost gate is correctly rejecting them, and B10 is the measurement that was supposed to save them.**
>
> The other two reopeners are untouched by this lane; nothing here bears on them.

---

## 5. THE ARMED BOOK'S LIVE EXPOSURE, PRICED

All armed sleeves are **H4** (`registry.py:50, :51, :54, :55`). With the broker clock at UTC+3 the six
MT5 H4 closes are **UTC 01, 05, 09, 13, 17, 21**, and 21:00 UTC is the broker rollover.

### 5.1 The premise fails on two of the three named sleeves, because the market is shut

Measured tick counts at UTC hour 21, FTMO:

| symbol | h20 | **h21** | h22 |
|---|---:|---:|---:|
| USOIL_cash | 29,788 | **0** | 18,207 |
| UKOIL_cash | 28,878 | **0** | 0 |
| XAUUSD | 106,602 | **0** | 137,401 |
| UK100 | 59,229 | **0** | 47,799 |
| GER40 | 58,860 | **0** | 47,010 |
| SPX500 | 62,133 | **0** | 58,242 |
| BTCUSD | 370,884 | 296,532 | 470,184 |
| USDJPY | 58,146 | 8,045 | 29,585 |

| sleeve | symbols | open at the rollover | rollover multiplier | rollover spread |
|---|---:|---|---|---|
| `energy_agri` | 2 | **0 of 2** | — | **no slot exists** |
| `sub_xvol_pullback` | 18 (14 on the tape) | **0 of 18** | — | **no slot exists** |
| `crypto` | 2 | **2 of 2** | BTCUSD **1.00**, DASHUSD 1.02 | BTCUSD **0.005 R** |
| **`sub_mid_dn_revert`** | 20 (18 on the tape) | **6 of 20 (30 %)** | JPY **7.5–18.6×** | **1.1–2.7 R** |

**For `energy_agri` and `sub_xvol_pullback` the H4 grid has five live decision instants, not six.**
For `crypto`, the sixth exists and costs nothing measurable — crypto's spread is genuinely hour-flat
(BTCUSD ratio 1.01× across all 24 hours).

Four `sub_xvol_pullback` symbols are **absent from the tick archive** — `CORN_c`, `COTTON_c`,
`FRA40_cash`, `US2000_cash` — and B10 can say nothing about them. Stated, not silently dropped.

### 5.2 Where the exposure actually is

`sub_mid_dn_revert`, the JPY block, at 21:00 UTC:

| symbol | reference p50 | **rollover mult** | flat-hour mult | rollover spread (px) | in pips | risk proxy (px) | **rollover spread (R)** | **excess over flat (R)** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **CHFJPY** | 0.01894 | **15.71×** | 3.45 | 0.29766 | **29.8** | 0.11144 | **2.671** | **2.084** |
| **GBPJPY** | 0.01987 | **12.07×** | 2.86 | 0.23981 | **24.0** | 0.09734 | **2.464** | **1.880** |
| **AUDJPY** | 0.01208 | **9.14×** | 2.36 | 0.11042 | **11.0** | 0.07182 | **1.537** | **1.141** |
| **USDJPY** | 0.00314 | **18.61×** | 3.98 | 0.05841 | **5.8** | 0.05113 | **1.143** | **0.898** |
| **EURJPY** | 0.01243 | **7.53×** | 2.08 | 0.09363 | **9.4** | 0.08513 | **1.100** | **0.796** |
| BTCUSD | 1.03629 | 1.00× | 1.00 | 1.03987 | — | 204.48 | 0.005 | 0.000 |

**The R column is a proxy and must be read as one.** The risk unit is the *research pool's* median
`risk_price` for that symbol (n = 730–1,077 per symbol), not `sub_mid_dn_revert`'s own H4 geometry,
which B10 has not measured — **hazard H7 applies in full**. The **pips and the multiplier are direct
tape measurements and carry no such caveat**: at the rollover CHFJPY quotes ~30 pips and GBPJPY ~24.

**The shipped class term is roughly right for JPY and badly wrong for indices.** `jpy_fx` prints
12.56× at the rollover against a tape 7.5–18.6×; the worst per-symbol undercharge is USDJPY at 0.589
(41 % light) — real, but an order of magnitude smaller than UK100's 6.4×. **So the estate's largest
hour-model error and its largest live rollover exposure are on different instruments**, and the
commission's framing ("worth ~0.005 R per armed trade", from RECON's slippage surface) prices a third
thing again. All three are true; they are not the same quantity.

### 5.3 The three avoidance mechanisms, and which one is available

| mechanism | changes what the sleeve trades? | verdict |
|---|---|---|
| **entry-hour convention** (shift the 21:00 decision to 01:00) | **yes** | The H4 bar closing at 21:00 UTC is a *different bar* from the one closing at 01:00; its signal is computed on different data. This is a different sleeve, not a cheaper execution of the same one. |
| **spread floor** (refuse to transact above a per-symbol ceiling) | **no** | **The only one that qualifies.** The sleeve still generates, the book still decides, the order is refused only when the tape is genuinely wide. A spread floor is already armed on two sleeves (CLAUDE.md §4). What it lacked was a *measured* per-symbol ceiling; `receipts/B10_ARMED_EXPOSURE_V1.json → recommended_ceilings` supplies one per symbol, from the p90 of that symbol's cheapest open H4 slot. |
| **decision-timeframe offset** (offset the H4 grid by an hour) | **yes** | MT5 H4 bars are broker-aligned; an offset grid is a different bar series, and every published economic figure for these sleeves prices the broker-aligned one. |

### 5.4 Is this the ratified hour-01 question again? No — and here is the difference

CLAUDE.md records an hour-01 entry convention ratified previously that **admitted nothing (0 of 72
arms, best p 0.380)**. That was a **different question**:

| | AM / AQ's hour-01 convention | B10's rollover finding |
|---|---|---|
| object | **entry** timing inside the same decision bar | the **cost** charged at a decision instant |
| population | **D1 FX** cohort (100 % of fills at broker hour 00) | **H4** armed sleeves |
| instrument | gross + cost jointly, gated for admission | the spread term alone, from the tape |
| claim | an economic **edge** | an accounting **error** and an execution **exposure** |

A rule can be worthless as an edge and still be a real accounting error. The prior null does not
transfer, and B10 proposes no arming, sizing or config change of any kind.

---

## 6. THE WITHIN-BAR-MINIMUM DEFECT — MEASURED, AND ITS CONSUMER CHAIN ENUMERATED

The MT5 bar `spread` column is the **within-bar minimum** — the estate measured this at a 0.999 median
exact-match rate over 30 symbols (`phase8/receipts/AH_BAR_SPREAD_SEMANTICS.json`) and
`spread_model.py:169-174` says so in prose. B10 measures the resulting bias on the same M15 grid the
bars are cut from, from the tape:

| symbol | per-bar mean/min: mean | median | p90 | p99 |
|---|---:|---:|---:|---:|
| **EURUSD** | **2.264** | 2.076 | 3.062 | 7.163 |
| GBPUSD | 1.864 | 1.836 | 2.333 | 3.714 |
| USDJPY | 1.822 | 1.792 | 2.531 | — |
| CHFJPY | 1.639 | 1.597 | 1.950 | — |
| AUDUSD | 1.576 | 1.574 | 1.871 | — |
| USDCAD | 1.548 | 1.551 | 1.815 | — |
| … 6 more FX pairs | 1.44–1.55 | | | |
| **UK100** | **1.099** | 1.061 | 1.153 | 2.682 |

**The FX bias is 44–126 %. The index bias is ~10 %.** And there is a harder failure underneath it:

> **29.6 % of FTMO EURUSD ticks quote a spread of exactly ZERO** (bid == ask; measured on 800,000
> consecutive ticks, `min 0.0, p1 0.0, p50 1.0e-5`). Consequently **2,269 of 2,592 EURUSD M15 bars
> (87.5 %) have a within-bar minimum of exactly 0.0.** For that symbol the bar `spread` column is not
> merely optimistic — on seven bars in eight it is **zero**.

### The consumer chain, traced rather than assumed

I expected to find broad optimism. I found **one** production consumer, and the estate had already
defended against the worst of it:

| consumer | what it reads | exposure |
|---|---|---|
| `spread_model.py` `era_ratio` | the bar `spread` column, via `BAR_SPREAD_ERAS.json.gz` | **the only one.** Used as a **ratio of minima**, so a constant min-to-mean factor divides out. And its winning estimator is **`mean_all_nonzero`** — the zeros are already excluded by construction (the estimator shortlist is `p50_nonzero`, `p75_nonzero`, `p90_nonzero`, `mode_above_floor`, …). The residual min-to-p50 bias is documented at `spread_model.py:167-174` and mitigated for `SCHEDULE` eras. |
| `walkforward/quote_side.py` `spread_by_bar` | **NOT the bar column** — supplied by `shadow_lifecycle.py:125-141 spread_series()` → `spread_for()` → `spread_price()`, i.e. **the model** | inherits the *hour* defect (§2), not the min defect |
| `execution.py:2456` | `symbol_info.spread` — the **live current** quote, not a bar | none |

**So the honest answer to "every consumer of it is optimistic" is: there is one consumer, it uses the
column as a ratio, and it already filters the zeros.** The exposure that remains is **not** a level
bias — it is that the ratio is only unbiased if the min-to-mean *structure* is stable between the two
eras being divided. B10 can measure today's factor per symbol (the table above, 1.10× to 2.26×) and
**cannot measure any historical era's**, because there are no historical ticks. That is a real bound
and it is unmeasurable from available data: if the structure changed completely between two eras, the
ratio is wrong by up to the cross-symbol range of the factor, ~2×.

**The larger and fixable finding is the one directly above it in the same chain**: the forward shadow
charges spread from `spread_series`, which caches at **hour resolution**
(`instant.replace(minute=0, second=0, microsecond=0)`) and takes the **class** hour term. It therefore
inherits both the §2 class defect *and* the §3.3 sub-hour defect — one modelled number for a UK100
hour whose two halves differ by **2.7×**.

### Two independent blindnesses in the same measurement, and the combination is worse than either

| blindness | what it hides | measured size |
|---|---|---|
| **within-bar minimum** (§6 above) | the *level* of the spread inside a bar | FX **+44 to +126 %**, EURUSD **87.5 % of M15 bars read exactly 0.0** |
| **UTC bucketing** (§2A) | *which* broker hour a bar belongs to | the rollover is understated **28–32 %** and a calm hour overstated **2.4–5.0×**, on 19.7 % of the pool |

They compound in the same direction on the same instruments. The bar minimum is lowest exactly where
the tick book is thinnest and most likely to lock — the rollover, where EURUSD's tick count falls
from 5,106 to 667 per quarter-hour (§2A.2). So the bar that contains the rollover is the bar whose
minimum is most likely to be zero, **and** it is the bar a UTC key is most likely to file under the
wrong hour. A consumer reading both gets a cheap spread stamped on the wrong hour, and neither error
announces itself.

**Neither defect reaches the shipped `era_ratio` at full strength** — it filters zeros
(`mean_all_nonzero`) and divides minima by minima — but both reach anything that reads `utc_hour` off
the candidate pool, which is 72 of the 83 hour-bucketing receipt scripts in this audit tree and the
live ridge's own feature vector.

---

## 7. WHAT WOULD REVERSE EACH FINDING HERE

| finding | the measurement that would reverse it | nearest unrefuted constructive variant |
|---|---|---|
| the record restates to −1.370 R, not −6.090 | a UK100 tick capture outside 2026-06-18…07-26 showing hours 07–15 at 1.4× rather than 0.8×. The 46 mis-keyed trades are all in that band, so the whole 4.2 R difference lives there | none needed — the correction is arithmetic. But **capture UK100 and GER40 forward**, because the shape is measured on one 37-day window and nothing validates it out of window |
| the class hour term is the defect, not the anchor | an anchor residual materially away from 1.0 on a second window. Measured 1.008 over 436 cells here | if the anchor moves, the repair is the same code path — `tape_hourly.py` returns a multiplier and the anchor is a separate factor |
| delaying entry loses (t = −25.5) | a population whose price path **mean-reverts** over the delay horizon rather than continuing. Tested only on the seven MARKET families, which trade continuation geometry by construction | **walk the three POI/LIMIT families**, which are already passive and which RECON found is the only arm with a positive tick-truth edge. Their prices are not in `lg_*.pkl.gz`; this is the same single re-export Lane 7 named as its highest-value follow-up, and two lanes now want it |
| expensive hours are not more informative (ρ −0.811) | an hour whose pre-cost gross CI excludes zero on the *positive* side while its spread is above median. None of 24 qualifies | the cheap-hour restriction H1 (57 % breadth, better in all five months on cost **and** pre-cost gross) |
| the armed rollover exposure is ~zero on the three named sleeves | a broker change that opens cash CFD quoting through 21:00 UTC, or an armed set that includes `sub_mid_dn_revert` — **the latter is not hypothetical**: `src.safety.armed_set.armed_sleeves()` is the authority and RECON §6 reads four sleeves there | the **measured per-symbol spread ceiling** in `recommended_ceilings` — the only mechanism of the three that does not change what a sleeve trades |
| Lane 7's cost veto is a MARKET→LIMIT switch | a cost threshold that retains a material MARKET share. At p25 it is 5 rows of 36,687; at p50 it is 31.6 % | publish the rung as **"switch to the LIMIT arm"**, which RECON independently supports at t = 2.49, and decide it as an abstain-rule question |
| the DST smear (28–32 % / 2.4–5.0×) | a broker whose server clock does **not** follow the US DST calendar. Measured over 81 weekly session boundaries per broker, all nine transitions fall on US dates and none on EU dates (`broker_clock.py`), so this would be a broker change, not a measurement error | **key hour features and hour buckets on broker wall clock.** `src/utils/broker_clock.py` already supplies it and fails closed on an unregistered server. Free for crypto and cash CFDs, decisive for the twelve FX pairs |
| the LIMIT reopener closes | a cost measurement that moves **commission or swap**, not spread — 57.2 % of the rejected set exceeds 0.20 at zero spread and BTCUSD's gate cost is 98.3 % non-spread. Lane 7 measured commission at 38.0 % of all cost and eight symbols paying zero, so a venue/instrument change is the only lever with the right size | reprice the rejected population against a **second broker's commission schedule** (Lane 7 §7.1: zero of 25 shared instruments price within 2 % across the two hosts). That is a commission measurement, not a spread one, and this lane cannot do it |
| the bar-min defect has one consumer | a code path reading the bar `spread` column that this trace missed. Traced by grep over `src/` plus direct read of the two candidates | forward tick capture is the only thing that retires the era-ratio structure assumption; the artifact's own `honest_limit` already says so |

---

## 8. FINDINGS THAT SHOULD PROPAGATE

1. **`spread_model.py:396` reads only `by_class_hour_of_week`. `by_symbol_hour_of_week` is in the
   shipped artifact for 36 symbols and no code reads it.** It agrees with 300.5 M ticks to a median
   0.64 %. Four lines recover it. Nothing in the cost/spread stack is R2-bound.
2. **The sealed five-month record restates to −1.370 R composed (−2.024 R spread-only), not −6.090 R.**
   Lane 7's figure carries a keying defect: 62.1 % of trades had no hour, 21.5 % of the rest are off
   by one. Lane 7's own instrument, correctly keyed, gives −2.704 R.
3. **Every cash CFD is closed at 21:00 UTC.** The armed H4 grid has five live decision instants for
   `energy_agri` and `sub_xvol_pullback`, not six. Any claim about "the rollover slot" must name the
   instrument.
4. **The rollover exposure is `sub_mid_dn_revert`'s JPY block**, at 7.5–18.6× and 5.8–29.8 pips.
   Whether it is armed is a question for `src.safety.armed_set.armed_sleeves()`, and this lane's
   commission and RECON §6 disagree about the answer.
5. **You cannot buy a better price with time on this population.** Delay: +0.009 R spread saved,
   −0.211 R worse entry, 23×. Passive limits (Lane 7): +0.0094 vs −0.0426, 4.5×. Same conclusion,
   two instruments.
6. **Lane 7's `cost ≤ p25` rung is 0.014 % MARKET.** Its "pre-cost gross does not degrade" is computed
   on a ~100 % LIMIT population, which its own finding 3 declares invalid, and the frozen rule cannot
   execute it. Restated as "switch to the LIMIT arm" it is corroborated by RECON at t = 2.49.
7. **29.6 % of FTMO EURUSD ticks quote a zero spread**, so 87.5 % of its M15 bars have a within-bar
   minimum of exactly zero. The era estimator already excludes zeros (`mean_all_nonzero`); the
   residual risk is structural stability across eras and is unmeasurable without historical ticks.
8. **The forward shadow charges spread at hour resolution from the class term**
   (`shadow_lifecycle.py:125-141`), inheriting both the class defect and the sub-hour defect. UK100's
   15:00 UTC hour differs by 2.7× between its halves.
9. **The rollover is a broker-clock event and the estate keys on UTC.** Broker 00:00 is UTC 21 for
   65.2 % of 2026 and UTC 22 for 34.8 %. A UTC bucket **understates the rollover by 28–32 %** and
   **overstates its calm neighbour by 2.4–5.0×**, on twelve FX pairs; crypto is exempt and every cash
   CFD is shut. 19.7 % of the pool and 105 of the 282 sealed trades are on the far side of
   2026-03-08. **`feature_contract.py:207` makes `utc_hour` a UTC-keyed categorical feature of the
   LIVE wave-21 ridge**, whose daily refit necessarily spans transitions. Prescription: key on broker
   wall clock, which `src/utils/broker_clock.py` already supplies.
10. **The rollover premium is a 75-minute window, not an hour** — broker 23:45 to 01:00, peaking at
   **20–40× reference** for EURUSD while its tick count falls 5,106 → 667 per quarter. A
   close-anchored daily signal samples the **6× ramp quarter**; anything transacting into the next bar
   pays the peak.
11. **The LIMIT branch's strongest reopener is closed.** The cost-gate-rejected rows' modelled 0.4402
   is **0.47792 at tape truth — 8.6 % higher**; 1.96 % cross back, they do not clear zero, 57.2 %
   could not clear at zero spread, and the set is crypto-commission (BTCUSD 24.8 % of it, spread 1.7 %
   of its cost). Also: **the gate charges LIMIT rows a modelled spread their realised cost excludes**
   (`cost_r` 0.24450 vs `allin_cost_r` 0.14401), and against the realised-cost null the rejected set's
   "skill" is **−0.043, not +0.086**.
12. **The tick export is 61 files / 300,538,915 rows** — B10 independently confirms Lane 7's count
   against CLAUDE.md §4's 51 / 263,894,769, and reduced all of it with 0 bad rows and 0 inverted quotes.

---

*B10. Every figure reproducible from `b10_hourly_cost/*.py` against the sources named in §1.
Confers no arming, sizing, promotion or activation authority.*
