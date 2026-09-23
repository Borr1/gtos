# r1 — THE MEASUREMENT INSTRUMENT: one canonical walker, correct about the side of the book

**Wave 20, lane r1. 2026-08-07.** Receipts under `phase20/receipts/r1/`.

---

## 0. HEADLINE

**The live sleeve estate's published gross is +0.1128 R/trade. Corrected for the side of
the book it is −0.0277 R/trade.** 22,354 trades, whole population, same walker, same bars,
and an uncorrected arm that reproduces the estate's published `r_gross` **bit-for-bit on
22,354 of 22,354 rows** — so the delta of **−0.1405 R/trade** is about this estate and
nothing else.

**And it is not a cost. It is a wrong answer.** 89.6 % of the estate's trades keep their
exit and their R moves by exactly **0.000000**; 4.08 % of trades change exit reason and
carry **96.5 %** of the entire delta. The migrations run one way only — **732
`target → stop`**, 127 `trail → stop`, 50 `maxbars → stop`, and **zero** in the other
direction. **736 of the 7,552 targets the estate books — 9.7 % — did not happen.** No cost
term can undo that; a cost model subtracts a level, it cannot un-book a target.

**On armed money the answer is specific and mostly reassuring.** Of the four sleeves the
live books run, three move by less than 0.004 R/trade. The fourth, **`crypto`, loses
23.5 % of its gross** (+0.5673 → +0.4339 R/trade), on five trades out of 181. **The
estate's one standing admission survives**: `mx_btcusd @ target_5R` goes +0.74262 →
+0.72366 R/trade with fold positivity unchanged at 5/5 — **one** exit-reason change in 318
trades.

**On the broad V4 family the correction changes nothing about the verdict and kills one
family.** All ten families are negative under both corrected anchorings; the estate's best
broad family, `structural_distance_extreme`, goes **+0.06303 → −0.11278** — an independent
reproduction of p3 §10 from a different roster read and a different spread source.

**And the second-order result matters as much as the first: the estate's NET moves the
other way.** Its cost model charges one spread as a *level* on every trade
(mean **0.191709 R**, identical to six decimals to the mean of `spread / stop distance`),
while the true effect is **zero on the 89.6 % that keep a level exit**. So the published
net was **pessimistic** by +0.0517 R/trade: **−0.174858 → −0.123124**. Both published
numbers were wrong, in opposite directions; the estate is net-negative either way and
**no sleeve changes net sign**. On the armed four the net moves −0.0087 R/trade (−2.0 %)
and three of the four go **up**. §7.

---

## 1. GROUND TRUTH — re-established here, whole population, both archives

Not taken from d8x or p3. Measured again, with independent code, on the archives the two
populations are actually walked on.

### 1.1 The M15 archive — the substrate of the live sleeve estate

`vps-bars-20260727` against `vps-ticks-20260726`. **Both carry BROKER SERVER WALL CLOCK
epochs** per their own `.timebase.json` sidecars, so the join takes no clock risk: nothing
is converted and nothing needs to be. Every M15 bar in the tick overlap, every shared
symbol, no sampling.

| | value |
|---|---:|
| symbols | **33** |
| M15 bars scored | **87,060** |
| `close == last tick BID` | **1.00000 on every one of the 33** |
| `open == first tick BID` | 1.00000 on every one |
| `(close − mid)/spread`, median | **−0.500000**, cross-symbol range **[−0.5, −0.5]** |
| `high − max(bid)` in spread units, median | **0.0000** on every one |
| `low − min(bid)` in spread units, median | **0.0000** on every one |
| `high − max(ask)` / `low − min(ask)` | −1.0 |

**No symbol disagrees.** EURUSD reads `close == last ask` on 22.5 % of bars because EURUSD
is frequently zero-spread; the mid test is unambiguous there and everywhere.
Receipt: `receipts/r1/R1_QUOTESIDE_M15_V1.json`, script `r1_quoteside_verify.py`.

### 1.2 The M1 packs — the substrate of the broad V4 family

A **different export**: `bridge_ftmo_m1_*` from the true-UTC lane hold, stamped in true
UTC, with no overlap with the broker tick export d8x used. So the M15 result transfers to
it by provenance only, which is not a measurement. Closed directly against the true-UTC
tick hold (`sources/ticks/<YYYYMM>/<SYM>/microstructure_ticks.jsonl`), joining on the
minute. `time_msc` is a **broker** epoch on those rows and is deliberately never read
(p3 §4.1 measured the 2 h gap).

| | value |
|---|---:|
| files (4 symbols × 7 months) | **28** |
| M1 bars scored | **820,452** |
| `close == last tick BID` | **1.000000, minimum across all 28 files** |
| `high == max(bid)` / `low == min(bid)` | **1.000000 on all 28** |
| `(close − mid)/spread` | **−0.5 exactly**, range across files [−0.5, −0.5] |

Receipt: `R1_QUOTESIDE_M1_V1.json`, script `r1_quoteside_m1.py`. This is stronger than
p3's 99.99 % — an exact minute join finds no exception at all.

**Both archives are BID on O/H/L/C. Settled twice, on two clocks, with two tick sources.**

---

## 2. THE CONVENTION — derived, and proved against the live engine

Every row is what the live engine does, cited. Nothing here is a textbook convention.

### 2.1 Which side transacts

| leg | you | quote side | live proof |
|---|---|---|---|
| LONG entry, at market | buy | **ASK** | `execution.py:3247` |
| SHORT entry, at market | sell | **BID** | `execution.py:3247` |
| LONG entry, pending at a level | buy | **ASK** | `execution.py:6197` |
| SHORT entry, pending at a level | sell | **BID** | `execution.py:6197` |
| LONG stop-loss | sell | **BID** | `execution.py:6953`, `:9213` |
| LONG take-profit | sell | **BID** | `execution.py:6953` |
| SHORT stop-loss | buy | **ASK** | `execution.py:6953`, `:9213` |
| SHORT take-profit | buy | **ASK** | `execution.py:6953` |
| LONG trail / scale-out / time stop / maxbars close | sell | **BID** | `execution.py:6953` — the price every management overlay reads |
| SHORT trail / scale-out / time stop / maxbars close | buy | **ASK** | `execution.py:6953` |

```
execution.py:3247   entry_price   = tick.ask if direction == "LONG" else tick.bid
execution.py:6197   current_price = tick.ask if intent.direction == "LONG" else tick.bid
execution.py:6953   current_price = tick.bid if trade.direction == "LONG" else tick.ask
execution.py:9213   current       = tick.bid if ...direction == "LONG" else tick.ask
```

`:6197` is worth naming: the engine emulates a pending order client-side and compares a
LONG's limit level against the **ask**. That is the entry-trigger side, proved rather than
assumed.

### 2.2 Where the levels hang — the question that decides the whole correction

Two anchorings are possible and they give **different** answers, so it is measured.

**The live W7 book is FILL-anchored:**

```
order_router.py:66   entry = float(ask if d > 0 else bid)   # cross the spread on entry
order_router.py:73   "stop_loss": entry - sign * rd, "take_profit_1": entry + sign * target_dist
execution_packets.py:566-569  stop_loss = entry_price - sign * risk_distance
                              take_profit_1 = entry_price + sign * final_target_r * risk_distance
execution.py:3260             sl_distance = abs(entry_price - sl)      # the R unit
```

It crosses the spread and then hangs **both** exit legs off the crossed price, and sizes
on the crossed distance. Consequences, all exact:

* R at the stop is **−1** and at the target **+T**. **The R levels do not move.**
* What moves is the tape distance to them: **the stop is one spread NEARER and the target
  one spread FURTHER**, on both sides of the market.
* Every close-based exit (maxbars, time stop, rollover flat) additionally transacts on the
  wrong side and is charged exactly one spread.

**The broad V4 family is LEVEL-anchored**, and its generator says so:
`broader_origin_generators.py:1697-1712` records `"zone_midpoint": entry` — the entry is
the POI midpoint, the stop is the zone edge plus an ATR buffer, and the target is
`entry + target_rr * (entry − stop)`. All three are absolute structural prices; nothing
hangs off a fill. There a LONG's exit legs resolve on the tape **unshifted** (they are
bid-quoted and the tape is the bid) and the displacement lands on its entry trigger, while
a SHORT takes the full shift on both legs. That is p3's SPRMT5 model, reached
independently and for a stated reason.

### 2.3 The whole correction is one number

For a fill-anchored at-market trade, on **any** tape:

```
replay_anchor = bar_close + direction * spread
```

*Derivation.* Let `E_t` be the transacted entry. `exits.replay` resolves everything on the
tape, so the anchor it needs is `E_t` translated into tape units by the trade's own
**exit**-quote offset: `anchor = E_t − exit_offset`. For a LONG, `E_t = close + (ask−tape)`
and `exit_offset = (bid−tape)`, so `anchor = close + s`. For a SHORT, `E_t = close +
(bid−tape)` and `exit_offset = (ask−tape)`, so `anchor = close − s`. Every level, every
fill, MFE and MAE follow, because each is measured from the anchor and each fill lands on
the trade's own exit-quote side.

**Two consequences worth holding on to.**

1. **It is tape-quote invariant.** A MID archive is optimistic by *exactly the same
   amount*. The defect is not "the bars are bid where they should be mid" — it is that the
   walk never crosses the spread at all, and the crossing costs one full spread from
   wherever the tape sits. Pinned by `test_anchor_is_bar_quote_invariant`.
2. **It is not monotone per trade for path-dependent exits.** For stop / target / clock
   policies the correction can never help a single trade (provable, and swept over 3,000
   random paths per policy). For `trailing_runner` and `partial_be_runner` it can: a trail
   that arms one spread later can exit later and better, and a scale-out that is not taken
   leaves full size in a winner. **So there is no per-trade bound for the four
   `partial_be_runner` sleeves or the two `trailing_runner` sleeves — only a pooled one.**
   `energy_agri` and `metals_core` are `partial_be_runner`. Pinned by
   `test_path_dependent_policies_are_not_monotone_but_are_negative_pooled` and by a
   hand-built counterexample.

---

## 3. WHERE THE SPREAD COMES FROM — and what happens when there isn't one

`walkforward.quote_side.spread_for` delegates to **Session AG's measured spread model**
(`src/costs/spread_model.py`, `research/operations/spread_model_2026_07_29/`): a
tick-measured anchor × the quarter's **measured era ratio** × an hour-of-week / volatility
multiplier, published as a band (`low`/`mid`/`high`).

Era-awareness is not a nicety here. The estate walk runs 2017–2026; a flat 2026 snapshot
charges FX 20–50× too little in the early years and metals too much in the middle ones,
and it does not even have a consistent sign. Every number below is published on all three
bands for that reason.

**It fails closed.** `spread_for` raises `SpreadUnavailable` rather than returning zero — a
silent zero is the defect this module exists to remove, and a fallback would hide the
repair exactly where the data is worst. All 37 broker symbols in the estate price; **zero
rows were skipped for want of a spread.**

---

## 4. WHAT SHIPPED

| file | what |
|---|---|
| `src/research_infra/walkforward/quote_side.py` | **the canonical module.** `BarQuote`, `LevelAnchor`, `SpreadUnavailable`, `transacted_entry_price`, `exit_quote_offset`, `entry_trigger_level_on_tape`, `replay_anchor`, `level_anchor_for_replay`, `spread_for`, `walk`. `walk()` returns **both** conventions and their delta in one object, so an A/B cannot drift. |
| `src/research_infra/walkforward/exits.py` | **one new optional kwarg**, `entry_price=None`. That is the entire production diff. `None` reproduces `bars[i].c` byte-for-byte. |
| `tests/research_infra/test_quote_side.py` | **27 tests**, every expected number computed by hand in the test body. |

**Why a kwarg and not a new walker.** `exits.replay` is the estate's only sanctioned path
labeller and its identity with `primitives.simulate_detail` is fuzz-verified over 4,000
random series. A second walker would have to re-earn that, and every number it produced
would be about a different program. The correction is provably a pure change of anchor, so
it is expressed as one.

**The proof tests** — these FAIL against the old unshifted convention:

* `test_long_stop_is_one_spread_nearer_and_the_old_walk_survives_it` — a bar whose low
  reaches the true stop and never reaches the old one: old books 0.0 R, truth books −1.0.
* `test_short_stop_is_one_spread_nearer` — the mirror, on the other side of the market.
* `test_long_target_is_one_spread_further` / `test_short_target_is_one_spread_further` —
  old books +2R at a target that was never reached; truth books +0.80.
* `test_trail_arms_one_spread_later_and_fills_on_the_exit_side`,
  `test_trail_that_no_longer_arms`,
  `test_partial_be_runner_scale_out_moves_with_the_anchor` — the two live exit contracts.

**The hygiene tests:** touch-exactly (and one tick short), gap-through, same-bar
stop-and-target (the pessimistic tie survives), `spread=0` reproduces the old walk
identically on four policies × both directions, `entry_price=None` is byte-identical to
the pre-r1 walker, and `spread_for` raises on an unknown symbol.

**H1:** `walkforward/exits.py` and `walkforward/quote_side.py` are **not** in R2's 43 bound
paths. **No bound file was edited by this lane.** No new seal cost.

**Live isolation — verified here, not taken on trust.** `walkforward/exits.py` is imported
by exactly **two** files in the tree, `walkforward/diagnostics.py` and this lane's own
`walkforward/quote_side.py` (`rg -l "walkforward.exits|from .exits import"` over `src/`
and `scripts/`). The two `walkforward` hits inside `src/components/ultimate_book/` are a
schema string (`cost_true_splits.py:106`) and a docstring (`sleeves/session_leadlag.py:22`),
not imports. **No live path can reach the edited function.** Separately, and for the same
reason the prompt asked: `broader_origin_generators` is referenced by
`components/orchestrator.py` and `components/v4_live_replay_decision_core.py` — the V3/V4
selector lineage, whose permission gates never fire (`live_activation_allowed: false`) —
and by **nothing** under `src/components/ultimate_book/` or in `scripts/run_book.py`. The
armed decision surface is the `ultimate_book` W7 book; the broad family is not on it.

**H2 — the A/B, physically.** BEFORE was produced by reverting the change on disk, not by
reasoning about it: **11 failed → 11 failed, the two failure sets byte-identical, 0
regressed, 0 fixed, +27 net new passing tests** over the 29 test files that reference
`walkforward` plus the two spread-model suites (3,367 → 3,394 passed). Scoped rather than
full-suite for two stated reasons — `pytest_failset.py` stamped its own full-suite capture
`usable_as_baseline: false` (*"recovered 0 ids but pytest reported 94"*), and this branch
has concurrent writers (HEAD moved `937390d59` → `8dd9b07c0` mid-session). Receipt:
`receipts/r1/R1_AB.md`.

---

## 5. THE LIVE SLEEVE ESTATE — the numbers Borhen makes money on

`AQ_ESTATE_TRADES_V2.json.gz`, 22,354 trades, 32 sleeves, 2017–2026, `vps-bars-20260727`.
Recipe copied from `aa_estate_generate.py:260-274`. Whole population.

> **Control.** The uncorrected arm is re-derived from the bars, not copied from the
> artifact, and it reproduces the published `r_gross` with **max absolute error 0.0 over
> 22,354 of 22,354 rows**. If it had not, the run refuses to write.

### 5.1 Pooled

| | R/trade |
|---|---:|
| published gross | **+0.112763** |
| corrected gross, band **low** | −0.012138 |
| corrected gross, band **mid** | **−0.027726** |
| corrected gross, band **high** | −0.044429 |
| **delta (mid)** | **−0.140489** (se 0.004619) |
| trades where the delta is positive | **0.161 %** |

Total R over the estate: **+2,520.7 → −619.8**.

### 5.2 The mechanism — 96.5 % of it is a wrong exit, not a cost

| bucket | n | share of trades | sum of delta | share of delta | mean within |
|---|---:|---:|---:|---:|---:|
| `same: stop` | 13,221 | 59.14 % | **−0.00** | 0.00 % | **±0.00000** |
| `same: target` | 6,816 | 30.49 % | **+0.00** | 0.00 % | **±0.00000** |
| `same: trail` | 1,042 | 4.66 % | −90.86 | 2.89 % | −0.08720 |
| `same: maxbars` | 362 | 1.62 % | −18.42 | 0.59 % | −0.05089 |
| **`CHANGED: target → stop`** | **732** | **3.27 %** | **−2,659.50** | **84.68 %** | **−3.63320** |
| `CHANGED: trail → stop` | 127 | 0.57 % | −219.71 | 7.00 % | −1.72997 |
| `CHANGED: maxbars → stop` | 50 | 0.22 % | −144.36 | 4.60 % | −2.88727 |
| `CHANGED: target → maxbars` | 4 | 0.02 % | −7.63 | 0.24 % | −1.90830 |

Three things this settles.

1. **The two level exits move by exactly zero**, to the last bit, on 20,037 trades. That is
   the FILL-anchoring derivation of §2.2 confirmed empirically rather than argued.
2. **Every migration runs one way.** There is not a single `stop → anything` row. The stop
   can only get nearer and the target only further, so the correction is directionally
   inescapable at the exit-reason level.
3. **736 of the estate's 7,552 booked targets — 9.75 % — never happened.** That is the
   finding in one sentence, and no cost term addresses it.

### 5.3 Per sleeve, whole population

Ordered by damage. `s/d` is the median spread over risk distance; `chg%` is the share of
trades whose exit reason changed.

| sleeve | n | gross old | gross new (mid) | Δ mid | Δ low | Δ high | s/d | chg% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| liq_asia_up_low_metal | 157 | +0.1210 | **−0.4650** | −0.5860 | −0.5605 | −0.6115 | 0.6619 | 14.65 |
| asia_pdl_fade | 2,827 | +0.1720 | **−0.3289** | −0.5008 | −0.4661 | −0.5294 | 0.2435 | 12.98 |
| vss_fxcross_london_up_low | 308 | +0.2370 | **−0.0552** | −0.2922 | −0.2532 | −0.3312 | 0.2174 | 9.74 |
| sub_mid_dn_revert | 533 | +0.4784 | +0.1932 | −0.2852 | −0.2477 | −0.3377 | 0.0871 | 7.13 |
| mx_cadjpy_d1_volume_surge_reversal | 286 | +0.1224 | **−0.0559** | −0.1783 | −0.1573 | −0.1993 | 0.1440 | 5.94 |
| mx_nzdjpy_d1_donchian_20_breakout | 503 | +0.0560 | **−0.1178** | −0.1738 | −0.1618 | −0.2096 | 0.2044 | 5.76 |
| metal_session_reversion | 837 | +0.1111 | **−0.0440** | −0.1551 | −0.1535 | −0.1724 | 0.1106 | 7.05 |
| kz_london_crypto_low | 286 | −0.1634 | −0.3085 | −0.1451 | −0.1445 | −0.1668 | 0.1203 | 2.45 |
| asian_fade | 1,319 | +0.2382 | +0.1012 | −0.1370 | −0.1108 | −0.1714 | 0.1092 | 5.16 |
| **crypto** *(ARMED)* | 181 | +0.5673 | +0.4339 | **−0.1334** | −0.0318 | −0.1425 | 0.0093 | 2.76 |
| fx_jpy | 3,984 | +0.0687 | **−0.0473** | −0.1160 | −0.0967 | −0.1309 | 0.0889 | 3.31 |
| orb_crypto_london | 858 | +0.0996 | **−0.0150** | −0.1145 | −0.1004 | −0.1356 | 0.0750 | 3.85 |
| mx_avausd_d1_donchian_20_breakout | 189 | +0.2048 | +0.0925 | −0.1123 | −0.0644 | −0.1762 | 0.0162 | 3.70 |
| ny_crypto_momentum | 559 | −0.0163 | −0.1250 | −0.1087 | −0.0971 | −0.1098 | 0.0563 | 2.33 |
| fx_jpy_ny | 1,620 | +0.0502 | **−0.0200** | −0.0702 | −0.0572 | −0.0767 | 0.0586 | 2.10 |
| metals_softband | 237 | +0.4742 | +0.4091 | −0.0651 | −0.0437 | −0.0655 | 0.0253 | 1.69 |
| mx_ethusd_d1_donchian_20_breakout | 311 | +0.2599 | +0.2116 | −0.0483 | −0.0386 | −0.0579 | 0.0200 | 1.61 |
| metals_core | 385 | +0.1946 | +0.1521 | −0.0425 | −0.0294 | −0.0427 | 0.0225 | 1.04 |
| vol_compression | 391 | +0.3646 | +0.3301 | −0.0345 | −0.0345 | −0.0550 | 0.0136 | 1.02 |
| idxrev | 5,597 | −0.0032 | −0.0138 | −0.0106 | −0.0091 | −0.0144 | 0.0093 | 0.61 |
| metals_ob_micro | 34 | −0.2161 | −0.2192 | −0.0031 | −0.0027 | −0.0036 | 0.0260 | 0.00 |
| **sub_xvol_pullback** *(ARMED)* | 88 | +1.2685 | +1.2676 | −0.0009 | −0.0008 | −0.0009 | 0.0183 | 0.00 |
| **energy_agri** *(ARMED)* | 67 | +0.7792 | +0.7785 | −0.0007 | −0.0006 | −0.0008 | 0.0147 | 0.00 |
| **mx_btcusd_d1_donchian_20_breakout** *(ARMED)* | 318 | +0.3491 | +0.3491 | **0.0000** | −0.0000 | −0.0755 | 0.0080 | 0.00 |
| mx_ger40_cash_d1_volume_surge_reversal | 110 | +0.0909 | +0.0909 | 0.0000 | −0.0000 | −0.0000 | 0.0039 | 0.00 |
| mx_jp225_cash_d1_volume_surge_reversal | 110 | +0.2818 | +0.2818 | −0.0000 | −0.0000 | +0.0000 | 0.0095 | 0.00 |
| mx_us100_cash_d1_atr_mean_reversion | 71 | −0.2394 | −0.2394 | −0.0000 | +0.0000 | −0.0000 | 0.0044 | 0.00 |
| mx_us30_cash_d1_volume_surge_reversal | 121 | +0.1405 | +0.1405 | +0.0000 | +0.0000 | +0.0000 | 0.0030 | 0.00 |
| mx_us500_cash_d1_atr_mean_reversion | 67 | −0.1493 | −0.1493 | +0.0000 | +0.0000 | +0.0000 | 0.0060 | 0.00 |

Bold on the "gross new" column marks a **sign flip**. **Nine sleeves flip from a positive
published gross to a negative corrected one**, including `fx_jpy` (n=3,984, +0.0687 →
−0.0473), which was pulled from the live book on 2026-07-30 on other evidence and which
this correction says was never positive.

**The pattern is `s/d` and nothing else.** The five worst sleeves are the five with the
widest spread relative to their own stop; the five with `s/d < 0.01` are unchanged to four
decimals. That is not a coincidence, it is the mechanism: the displacement is `s/d` and the
flip rate is the density of paths within `s` of the stop.

---

## 6. THE BROAD V4 FAMILY

All **1,211,077** emissions of the eight open windows (2025-10..2026-05), from the
concurrent `d8` lane's emission arrays read read-only; **1,127,805 walked** (the remainder
lack a finite geometry or a path). The shipped contract: T=2.0R, 240 M1 bars, stop wins
ties. The sealed three (Jun/Aug/Sep 2025) were not opened.

> **Control.** Median `d_bps` per symbol reproduces `D8X_GEOM_V1.json → per_symbol` with
> **max relative error 0.0 across all 24 symbols.** The roster/tape join is exact.

| family | n | gross old | **LEVEL** (its own anchoring) | **FILL** | Δ level | Δ fill | s/d |
|---|---:|---:|---:|---:|---:|---:|---:|
| **ALL** | 1,127,805 | **+0.01723** | **−0.02904** | **−0.08515** | −0.04627 | −0.10238 | 0.0814 |
| current_fvg_fill | 642,616 | +0.02537 | −0.01744 | −0.07418 | −0.04280 | −0.09954 | 0.0878 |
| current_ob_retest | 255,839 | −0.00386 | −0.03504 | −0.09327 | −0.03117 | −0.08940 | 0.0669 |
| current_breaker_re_entry | 89,837 | +0.01711 | −0.05201 | −0.09506 | −0.06913 | −0.11217 | 0.0877 |
| liquidity_sweep_reclaim | 42,293 | +0.02050 | −0.05535 | −0.11824 | −0.07585 | −0.13874 | 0.0930 |
| displacement_continuation | 38,392 | +0.00649 | −0.02390 | −0.06505 | −0.03039 | −0.07154 | 0.0447 |
| **structural_distance_extreme** | 22,775 | **+0.06303** | **−0.11278** | **−0.19064** | −0.17581 | −0.25366 | 0.2253 |
| cross_asset_lead_lag | 20,423 | +0.01585 | −0.06864 | −0.15216 | −0.08449 | −0.16801 | 0.1225 |
| session_open_range_break | 8,194 | −0.01342 | −0.03889 | −0.06788 | −0.02546 | −0.05446 | 0.0394 |
| volatility_compression_expansion | 5,138 | −0.02682 | −0.05381 | −0.06896 | −0.02699 | −0.04214 | 0.0217 |
| regime_transition_break | 2,298 | −0.02038 | −0.03566 | −0.04662 | −0.01528 | −0.02624 | 0.0167 |

**All ten families are negative under both corrected anchorings.**

**Independent corroboration of p3.** p3 §10 published `structural_distance_extreme` at
**+0.06293** on its repaired-but-uncorrected contract; this lane, from a different roster
read (d8's emission arrays vs p3's own loader), a different walker and an **era-aware**
spread rather than a flat 37-day snapshot, gets **+0.06303**, and corrects it to
**−0.11278** against p3's **−0.13028**. Two independent instruments, the same verdict, the
same magnitude to within 13 %.

---

## 7. DOES IT REACH *NET*, OR WAS THE COST MODEL ALREADY STANDING IN FOR IT?

The estate's published net charges four terms against an uncorrected gross
(`costs.model.cost_r`: `commission + swap + spread + slippage`, over `sl_distance_price`).
Its spread term is a **level** stand-in for a **resolution** effect. Charging it on top of
a corrected gross would double-count; ignoring the resolution change would understate the
repair. So both nets are computed per trade with the estate's own cost model:

```
published net = r_old − (commission + swap + spread + slippage)/d
corrected net = r_new − (commission + swap +          slippage)/d
```

### 7.1 The arithmetic checks out exactly

The estate's mean spread charge is **0.191709 R/trade**, and the mean of `spread / stop
distance` over the same 22,354 rows is **0.191709** — identical to six decimals. So
`cost_r` charges **exactly one spread as a level**, which is what makes the substitution
legitimate: `delta_net = delta_gross + spread_r = -0.140489 + 0.191709 = +0.05122`, against
a measured **+0.051734** (the 0.0005 residual is swap on the trades whose hold changed when
their exit reason flipped).

### 7.2 And the answer inverts the sign

| | R/trade |
|---|---:|
| published gross | +0.112763 |
| corrected gross | **−0.027726** |
| **delta gross** | **−0.140489** |
| published net | −0.174858 |
| corrected net | **−0.123124** |
| **delta net** | **+0.051734** |

**The estate's gross was optimistic by 0.140 R/trade and its net was PESSIMISTIC by 0.052.**
Both published numbers are wrong, in opposite directions, and the estate is net-negative
in both accountings. The reason is that the cost model's level stand-in charges one full
spread on **every** trade while the true resolution effect is zero on the 89.6 % that keep
a level exit — so on wide-spread sleeves the stand-in over-charges badly. **No sleeve
changes net sign** (0 of 29 with a net; 9 change *gross* sign).

### 7.3 Per sleeve, and it is `s/d` again

| sleeve | n | net published | net corrected | Δ net | spread charge (R) |
|---|---:|---:|---:|---:|---:|
| **crypto** *(ARMED)* | 181 | +0.3783 | **+0.3030** | **−0.0753** | 0.0542 |
| vss_fxcross_london_up_low | 308 | −0.1183 | −0.1848 | −0.0664 | 0.2258 |
| mx_avausd_d1_donchian_20_breakout | 189 | +0.0690 | +0.0189 | −0.0501 | 0.0613 |
| sub_mid_dn_revert | 533 | +0.1697 | +0.1254 | −0.0444 | 0.2366 |
| ny_crypto_momentum | 559 | −0.2708 | −0.2944 | −0.0236 | 0.0807 |
| … 19 sleeves between −0.014 and +0.021 … | | | | | |
| **mx_btcusd_d1_donchian_20_breakout** *(ARMED)* | 318 | +0.2123 | **+0.2242** | **+0.0119** | 0.0124 |
| **energy_agri** *(ARMED)* | 67 | +0.6817 | **+0.7031** | **+0.0214** | 0.0221 |
| **sub_xvol_pullback** *(ARMED)* | 88 | +1.1798 | **+1.2107** | **+0.0309** | 0.0306 |
| kz_london_crypto_low | 286 | −0.6423 | −0.6001 | +0.0422 | 0.1769 |
| mx_nzdjpy_d1_donchian_20_breakout | 503 | −0.2037 | −0.1535 | +0.0502 | 0.2220 |
| asia_pdl_fade | 2,827 | −0.8421 | **−0.4509** | **+0.3912** | 0.8920 |
| liq_asia_up_low_metal | 157 | −1.1289 | **−0.4891** | **+0.6397** | 1.2257 |

The whole pooled `+0.0517` is two sleeves: `asia_pdl_fade` and `liq_asia_up_low_metal`,
whose spread charge is **89 %** and **123 %** of their own risk unit. **At `s/d` near or
above 1 the level-charge cost model is simply the wrong shape** — the true effect saturates
(a trade cannot lose more than its own path) while a level charge scales linearly. Those
two sleeves are the estate's worst either way; the correction makes them less absurd, not
tradeable.

**On the armed four the net barely moves: +0.436506 → +0.427783, −0.0087 R/trade (−2.0 %),
and three of the four go UP.** Only `crypto` loses (−0.0753, −19.9 %).

---

## 8. VERDICTS — does anything change?

**The broad V4 family: NO.** Its verdict was SIGNAL / finished, on the grounds that its
capture is 253× short of its toll and does not accumulate. The correction makes it *more*
negative on every one of the ten families, so every "short of its toll" conclusion survives
a fortiori. What it removes is the last positive number in the family.

**`structural_distance_extreme`: YES.** d1b's one surviving broad family — 8/8 windows,
both geometries, survived every control except the toll — is **negative at every executable
contract**: +0.06303 → −0.11278 at its own level anchoring, −0.19064 fill-anchored. The
mechanism is exactly the one p3 named: its edge lives in the tightest-stop cohort, its
`s/d` is 0.2253 (the highest of the ten), and the displacement scales with `s/d`. **Do not
propose it.**

**The armed book: one sleeve moves, three do not, and the standing admission survives.**

| cell | n | gross old | gross new | Δ | folds+ old → new | exit reasons changed |
|---|---:|---:|---:|---:|:---:|---:|
| **`mx_btcusd @ target_5R`** (LIVE, the standing admission) | 318 | **+0.74262** | **+0.72366** | **−0.01896** | **5/5 → 5/5** | **1** |
| `sub_xvol_pullback @ target_4R` (wired, OFF) | 88 | +1.54954 | +1.54642 | −0.00313 | 5/5 → 5/5 | 0 |
| `sub_xvol_pullback` as walked (ARMED) | 88 | +1.26850 | +1.26764 | −0.00086 | 5/5 → 5/5 | 0 |
| `energy_agri` (ARMED) | 67 | +0.77921 | +0.77851 | −0.00070 | 4/5 → 4/5 | 0 |
| **`crypto`** (ARMED) | 181 | **+0.56732** | **+0.43389** | **−0.13343** | 4/5 → 4/5 | **5** |

* **`mx_btcusd @ target_5R` — the estate's only standing admission, live on FTMO since
  2026-07-31 — does NOT change verdict.** −2.6 % of its gross, one exit-reason change in
  318 trades, fold positivity unchanged at 5/5, and 5/5 at the low and high spread bands
  too. Any package citing it should now cite the corrected number; nothing else moves.
* **`crypto` loses 23.5 % of its published gross, and its R/day goes +0.78386 →
  +0.59950.** That is real and it should be carried into any future sizing decision on
  that sleeve. **State the fragility with it**: the whole effect is **five trades out of
  181** (four `target → stop`, one `maxbars → stop`), it is band-sensitive (−0.032 at the
  low band, −0.142 at the high), and it lands hardest on folds 1 and 4. It is a −23.5 %
  point estimate on n=5 events, not a precise one.
* **`energy_agri` and `sub_xvol_pullback` are unaffected** at four decimals — but note §2.3
  item 2: `energy_agri`'s live contract is `partial_be_runner`, which AA did not label, and
  for that policy class no per-trade bound exists. The zero here is a statement about the
  contract that was walked.
* **`metals_core` (down-weighted ×0.50 by the learning lane) −0.0425; `fx_jpy` (pulled
  2026-07-30) flips sign.** Neither is armed today; both corroborate the pull.

### 8.1 And the admission STATISTIC, not just the point estimate

Re-running `run_gate` at the ratified rule needs AN's sealed population spec, AU's fold
construction and `CANDIDATE_BOOK_V1`'s family, and that belongs to whoever owns the
admission. What this lane can bound honestly is the **same statistic class** the gate
binds on: a **day-block** bootstrap of daily R (20,000 draws), which is the construction
the gate itself insists on (`walkforward/__init__` note 3 — a per-trade bootstrap
overstated a stated error budget by 2.1x-7.7x, B279). Raw p, no multiplicity charge.

| cell | days | gross R/day old -> new | p(<=0) | net R/day old -> new | p(<=0) |
|---|---:|---|---:|---|---:|
| **`mx_btcusd @ target_5R`** | 318 | +0.7426 -> **+0.7237** | 0.0000 -> **0.0000** | +0.4778 -> **+0.4707** | 0.0004 -> **0.0004** |
| `sub_xvol_pullback @ target_4R` | 40 | +3.4090 -> +3.4021 | 0.0001 -> 0.0001 | +3.1561 -> **+3.2191** | 0.0006 -> **0.0002** |
| `sub_xvol_pullback` as walked | 40 | +2.7907 -> +2.7888 | 0.0001 -> 0.0001 | +2.5955 -> +2.6635 | 0.0003 -> 0.0002 |
| **`crypto`** | 131 | +0.7839 -> **+0.5995** | 0.0006 -> **0.0057** | +0.5227 -> **+0.4186** | 0.0162 -> **0.0345** |
| `energy_agri` | 39 | +1.3386 -> +1.3374 | 0.0337 -> 0.0340 | +1.1711 -> +1.2079 | 0.0572 -> 0.0526 |

**Nothing crosses the sealed alpha = 0.10.** The standing admission's statistic does not
move at four decimals. The one number to carry forward is **`crypto`: raw p 0.0006 ->
0.0057 on gross and 0.0162 -> 0.0345 on net — a 2-9x degradation that still passes at 0.10
and now has materially less room at 0.05.** Receipt `R1_ADMISSION_STAT_V1.json`.


**One standing claim in the estate is now false as worded.** d8x §2 and the wave-19 owner
report state the bias as **−0.0696 R/trade**. That number is a bound on the *broad family*
at the shipped contract; on the *live sleeve estate* the measured value is **−0.1405
R/trade**, twice as large, because the sleeves' targets are wider (2R–5R) so each flipped
target costs more. The FIND 6 sentence "any usage lever worth less than 0.07 R/trade is
currently unfalsifiable" should read **0.14 R/trade on the sleeve estate**.

**And one framing is wrong and should stop being repeated.** The defect is not "the bars
are BID where they should be MID". A mid archive is optimistic by exactly the same amount
(§2.3, `test_anchor_is_bar_quote_invariant`). The defect is that the walk never crossed the
spread.

---

## 9. LIMITS

1. **The spread is modelled, not tick-measured, on the estate walk.** AG's model is
   era-aware and band-published and every table above carries all three bands, but no
   tick-level bid/ask capture exists for 2017–2025. The *sign* is not at risk; the
   magnitude carries the model's band, which is the low/high columns.
2. **Slippage past the trigger is not modelled.** A stop that gaps through fills worse than
   its level. Every corrected number here is therefore still optimistic.
3. **The estate arm walks AA's contract**, which is plain stop/target/maxbars plus the
   trail for the two `trailing_runner` sleeves. AA never labelled `partial_be_runner`, so
   the four sleeves that run it live (including armed `energy_agri` and `metals_core`) are
   corrected on a contract the live book does not run. §7 of `SESSION_AU` already flagged
   that gap; this lane does not close it.
4. **The broad arm walks from the emitted level unconditionally** and therefore poses no
   fill question. Under LEVEL anchoring a LONG's entry trigger displaces by one spread —
   it fills more often and earlier — and that is *not* modelled here. p3 §4 measured the
   fill side directly on ticks; this lane measures the resolution side on the whole
   population. They are complementary, not substitutes.
5. **`crypto`'s −23.5 % rests on five trades.** Stated in §8 and repeated here.
6. **No live-forward P&L was read, no VPS was touched, no broker-mutating script was run.**
   The sealed three windows were not opened.

---

## 10. FILES

| path | what |
|---|---|
| `src/research_infra/walkforward/quote_side.py` | the canonical module |
| `src/research_infra/walkforward/exits.py` | `+ entry_price` kwarg (the whole production diff) |
| `tests/research_infra/test_quote_side.py` | 27 hand-computed behavioural tests |
| `receipts/r1/r1_quoteside_verify.py` → `R1_QUOTESIDE_M15_V1.json` | BID, 87,060 M15 bars × 33 symbols |
| `receipts/r1/r1_quoteside_m1.py` → `R1_QUOTESIDE_M1_V1.json` | BID, 820,452 M1 bars × 28 files |
| `receipts/r1/r1_estate_rewalk.py` → `R1_ESTATE_DELTA_V1.json`, `R1_ESTATE_ROWS_V1.json.gz` | the estate, both conventions, per sleeve, per row |
| `receipts/r1/r1_estate_net.py` → `R1_ESTATE_NET_V1.json` | gross vs net, the double-count arithmetic, the mechanism decomposition |
| `receipts/r1/r1_broad_rewalk.py` → `R1_BROAD_DELTA_V1.json` | the broad family, both anchorings, per family |
| `receipts/r1/r1_frontier_admission.py` → `R1_FRONTIER_ADMISSION_V1.json` | the frontier contracts and the standing admission |
| `receipts/r1/r1_admission_stat.py` → `R1_ADMISSION_STAT_V1.json` | day-block bootstrap of the admission statistic, both conventions |
