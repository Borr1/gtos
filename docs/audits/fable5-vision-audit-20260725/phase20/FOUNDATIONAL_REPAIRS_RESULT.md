# THE FOUNDATIONAL REPAIRS — WHAT WAS FIXED, AND WHAT CHANGED

**Wave 20, phase 20. 2026-08-07. For Borhen.**

You asked for two things: *"fix everything… and then see what changes."* This is the ledger.
Section 1 is what was repaired. Section 2 is every number that moved. Section 3 is what it
means for the two funded accounts. Section 4 is what is still bent. Section 5 is what is now
open.

Every number here is traced to a committed receipt under `phase20/receipts/`. Nothing is
sampled — where a population is named, the whole population was walked.

---

## 0. THE ANSWER

> ### The ruler was bent, and it was bent in our favour.
>
> **The live sleeve estate's published gross of `+0.1128 R/trade` is `−0.0277 R/trade` once
> the walker knows which side of the book it is on.** 22,354 trades, whole population, and
> the uncorrected arm reproduces the published number bit-for-bit on 22,354 of 22,354 rows,
> so the `−0.1405` delta is about this estate and nothing else.
> (`receipts/r1/R1_ESTATE_NET_V1.json → pooled`)

**And it is not a cost. It is a wrong answer.** 89.6 % of the estate's trades keep their exit
and their result moves by exactly `0.000000`. 4.08 % change *exit reason*, and those carry
**96.5 %** of the entire delta. The migrations run one way only — 732 `target → stop`, 127
`trail → stop`, 50 `maxbars → stop`, and **zero** in the other direction.

> ### 736 of the 7,552 targets this estate books — 9.75 % — did not happen.

No cost model can undo that. A cost model subtracts a level; it cannot un-book a target.

**Three things follow, and I will not soften any of them:**

| | |
|---|---|
| **Yes, published figures you have been trading on were wrong.** | `crypto` −23.5 % of gross. `sub_mid_dn_revert` −59.6 % of gross and **−97.7 % of its expectancy**. Nine of 29 sleeves change the *sign* of their published gross. |
| **No, nothing here is a reason to touch either account today.** | The two armed sleeves that carry the money — `sub_xvol_pullback` and `energy_agri` — move by **0.1 %**. Nothing crosses an admission threshold in either direction. The armed sleeves' live behaviour is proved **byte-identical** at HEAD and at the parent commit over 556,251 generator calls. |
| **And one number moved in your favour.** | The estate's published **net** was *pessimistic*, not optimistic: `−0.1749 → −0.1231 R/trade`. The cost model was charging one full spread as a flat fee on every trade while the true effect is zero on the 89.6 % that keep a level exit. Both published numbers were wrong, in **opposite directions**. |

**Terms, defined once.**

| term | meaning |
|---|---|
| **R** | one risk unit — the distance from entry to stop. A trade that hits its stop books −1 R. |
| **gross** | the trade's result in R before any broker charge. |
| **net** | gross minus the four broker charges (spread, commission, swap, slippage), each divided by that trade's own stop distance so it is in R. |
| **emission** | a candidate the generator produced. Most never fill. |
| **fill** | an emission that actually opened a position in the walk. |
| **s/d** (spread-over-risk) | the broker's spread divided by the trade's own stop distance. **This single ratio explains every result in this document.** A sleeve with s/d = 0.25 hands a quarter of its risk unit to the broker at the door. |
| **ADMIT / REJECT** | the ratified admission standard: population `RECORDED`, option `B_balanced`, α = 0.10, Benjamini-Hochberg multiplicity correction against the declared candidate family. |
| **`p_pass`** | Monte Carlo probability of passing a prop-firm evaluation, at each firm's measured rules. |
| **day-block bootstrap** | the resampling method the gate insists on — resample whole trading days, not individual trades, so simultaneous trades cannot be counted as independent evidence. |

---

## 1. WHAT WAS REPAIRED

Four defects were named in the brief. All four are repaired, plus a fifth found during
verification. Every repair is default-ON, tested behaviourally, and touches **no
decision-contract-bound file** — so no sealed-replay option was spent.

| # | defect | what it was | what it is now | landed at | proved by |
|---|---|---|---|---|---|
| **1** | **The walk never crossed the spread** | Bar archives are BID on open/high/low/close. Every walker resolved stops and targets against them with **unshifted** levels — so a long's true stop is one spread nearer and its true target one spread further than we scored it. | One canonical module that knows which side of the book each leg transacts on, and a **single optional kwarg** on the estate's only sanctioned path labeller. `entry_price=None` reproduces the old walk byte-for-byte. | `src/research_infra/walkforward/quote_side.py:1` (357 lines, new) · `src/research_infra/walkforward/exits.py:303,333` (the entire production diff) | `tests/research_infra/test_quote_side.py` — **27 tests**, every expected number hand-computed in the test body; several **fail** against the old convention |
| **2** | **Orders born past their own stop** | `current_breaker_re_entry` emitted candidates whose stop the market had already breached. They fill 100 % of the time (marketable by construction) and book a mechanical −1.30 R each. | **Refused at emission.** The argument needs no walker convention: for a long with `fill_gap_R < −1` the order opens with its stop-loss **above its own fill price**. That is a malformed order, not a bad trade. | `src/components/broad_origin_emission_contract.py:214` · wired at `broader_origin_generators.py:1137, 1331, 1507, 1575` | `tests/test_broad_origin_emission_contract.py` (20 unit tests) + `tests/test_broad_origin_emission_repairs.py` (18 behavioural) |
| **3** | **The admission radius was in the wrong unit** | The proximity gate was denominated in **percent of price** (1.0 %) while the trade it admits is denominated in **R**, with a median risk of 7.4–8.9 bps. That is an **11.2–13.5 R gate on a 1.5 R trade**. | The percent test is kept as what it actually is — a *visibility scope* — and admission is now in the trade's own risk unit, on both sides. Every emitted candidate publishes `poi_fill_gap_r` and `poi_admission_bin`. | `broader_origin_generators.py:1103-1175, 1626-1650` | same suites; the generation audit carries a reconciled per-family partition |
| **4** | **Stale-bar entries** | The decision walked back to the last closed bar with **no maximum-age check**, so across a weekend or session gap it priced the entry off a bar that closed hours ago. | **Maximum age = one timeframe period, fail-closed**, applied to both the walk-back and the declared-bar fast path so a stale declaration cannot bypass it, and to the cross-asset leader series. | `broader_origin_generators.py:2365-2410` | behavioural tests on both selection paths and both boundary conditions |
| **5** | **The committed launcher re-armed a sleeve you disarmed** | You disarmed `mx_btcusd` on FTMO on **2026-08-05** (host commit `2fa77722d`). The host was edited; the **committed launcher was not**. For two days, a book restarted from the committed file would have re-armed it — and passed `--frontier-exits` for it. | The launcher carries your decision, and the declared armed set now lives in a versioned file with a **test that fails the build if the declaration and the launcher ever disagree**. | commit `5f7529f69` — `scripts/run_book_supervisor.ps1:86` · `config/live_armed_set.json` · `src/safety/armed_set.py` | `tests/safety/test_armed_set_single_source.py` — 13 tests, **4 of them fail against the pre-repair launcher**; it parses the tag lists out of the launcher rather than hard-coding them |

**Why the threshold in repair 4 is one period and not something looser.** The displacement
between the emitted entry and the next real print does not start small and grow — it starts
large. At a **single** missing bar the median displacement is already 0.98–2.77 R depending on
family, with 41.7–74.6 % of rows displaced by more than a full R. There is no safe positive
age. 94.52 % of the population sits at age 0, so the budget costs almost nothing.
(`receipts/r2/R2_CENSUS_V1.json`)

**Why repair 1 is a kwarg and not a new walker.** `exits.replay` is the estate's only
sanctioned path labeller and its identity with the live primitive is fuzz-verified over 4,000
random series. A second walker would have to re-earn that, and every number it produced would
be about a different program. The correction is provably a pure change of anchor, so it is
expressed as one:

```
replay_anchor = bar_close + direction × spread          # the whole correction, for a fill-anchored trade
```

**Two things about repair 1 that should stop being repeated.**

1. **The defect is not "the bars are BID where they should be MID."** A mid archive is
   optimistic by *exactly the same amount*. The defect is that the walk never crossed the
   spread at all. Pinned by `test_anchor_is_bar_quote_invariant`.
2. **The published bias of −0.0696 R/trade is a bound on the broad family, not on the estate.**
   On the live sleeve estate the measured bias is **−0.1405 R/trade — twice as large** —
   because sleeve targets are 2R–5R, so each flipped target costs more. The owner report's
   *"any usage lever worth less than 0.07 R/trade is unfalsifiable"* should read **0.14 R/trade**
   on the sleeve estate.

### 1.1 The ground truth, settled three times

The BID finding is the load-bearing premise of the whole wave, so it was re-established from
primary data three separate times, on two clocks, with three tick sources.

| where | population | `close == last tick BID` |
|---|---|---:|
| M15 archive (the sleeve estate's substrate) | 87,060 bars × **33 symbols** | **1.00000 on every symbol** |
| M1 packs (the broad family's substrate) | 820,452 bars × **28 files** | **1.000000 on every file** |
| never-read tick window, 24 symbols | 60,152 in-window bars | **1.0000 on all 24** |

`(close − mid)/spread` is **−0.500000 exactly**, with a cross-symbol range of `[−0.5, −0.5]`.
This is stronger than the wave-19 figure of 99.99 % — an exact minute join finds **no
exception at all**.
(`receipts/r1/R1_QUOTESIDE_M15_V1.json`, `R1_QUOTESIDE_M1_V1.json`,
`receipts/m2/M2_TICK_OOS_V1.json`)

### 1.2 And the convention was attacked with real bid/ask ticks, not with its own reasoning

Lane v1 did not accept r1's derivation. It built a tick-level round trip on
`vps-ticks-20260726` — long pays the ask at the decision bar's last tick and exits on the bid;
short hits the bid and exits on the ask; stop wins ties — and compared it against **both** bar-walk
conventions on the same bars.

**The convention is right.** Exit-reason agreement with tick truth improves on both sides
(LONG 28,656 → 30,086 of 30,553; SHORT 28,095 → 29,336).

**And the residual has a measured cause, not a guessed one.** A short's exits are ask-quoted
and the walk approximates the ask as tape + spread-at-entry; the spread at the resolving tick
runs 1.02–1.99× the spread at entry. Regressing the per-symbol short residual on that ratio
gives **Pearson r = 0.954** across the 12 symbols with a resolving population. Longs give
r = −0.357 with a mean residual of −0.0045.

**Stated as a bound: the corrected gross of −0.0277 R/trade is still slightly optimistic on
its short leg** (9,571 of 22,354 trades, 42.8 %). Per-symbol, and the armed sleeves are the
good case: BTCUSD −0.0098, ETHUSD −0.0162, USOIL +0.0132, UKOIL −0.0074 — and **both armed
substrate sleeves are 100 % long** (0/533 and 0/88 short). No armed conclusion moves.
(`receipts/v1/V1_TICK_TRUTH_V1.json`)

---

## 2. WHAT CHANGED

### 2.1 The broad V4 family — every family is now negative, where five were positive

Population: **1,167,099 emissions** over the eight open windows (2025-10 … 2026-05), all of
them. The three sealed months (Jun/Aug/Sep 2025) were not opened.

`OLD` = published instrument. `GEN` = generator repaired only. `WALK` = walker repaired only.
`BOTH` = the repaired instrument.

**Gross R per emission, and how many of the eight windows are gross-positive ("mo"):**

| family | OLD | mo | GEN | mo | WALK | mo | **BOTH** | **mo** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| structural_distance_extreme | **+0.04525** | **8** | +0.04549 | 8 | −0.23509 | 0 | **−0.23688** | **0** |
| liquidity_sweep_reclaim | +0.02054 | 6 | +0.02093 | 6 | −0.14185 | 0 | −0.14150 | 0 |
| cross_asset_lead_lag | +0.01362 | 6 | +0.00843 | 4 | −0.19403 | 0 | −0.19915 | 0 |
| displacement_continuation | +0.00130 | 5 | +0.00084 | 5 | −0.08915 | 0 | −0.08890 | 0 |
| session_open_range_break | +0.00103 | 5 | +0.00103 | 5 | −0.05924 | 1 | −0.05924 | 1 |
| current_ob_retest | −0.00204 | 2 | −0.00084 | 3 | −0.00811 | 0 | −0.00694 | 0 |
| regime_transition_break | −0.00196 | 3 | −0.00196 | 3 | −0.03452 | 1 | −0.03452 | 1 |
| current_fvg_fill | −0.00560 | 1 | −0.00479 | 1 | −0.03408 | 0 | −0.03343 | 0 |
| volatility_compression_expansion | −0.04011 | 0 | −0.04046 | 0 | −0.09540 | 0 | −0.09561 | 0 |
| current_breaker_re_entry | −0.26166 | 0 | **−0.00746** | 2 | −0.27295 | 0 | −0.02253 | 0 |
| **families gross-positive** | **5 / 10** | | 5 / 10 | | **0 / 10** | | **0 / 10** | |
| **family-months gross-positive** | **36 / 80** | | 37 / 80 | | 2 / 80 | | **2 / 80** | |

**The walker repair does all of it.** The generator repair alone leaves 5/10 and 37/80.
(`receipts/m1/M1_FUNNEL_V1.json → by_family`)

**The generator repair's own result, isolated.** Refusing 4.21 % of emissions removes 26.54 %
of the roster's entire net loss (−33,151 R of −124,930 R). `current_breaker_re_entry` goes
from −0.36457 to −0.04011 R/emission. All 8 of 8 windows improve.
(`receipts/r2/R2_RESULT_V1.json`)

**And the family is 29 % LESS unprofitable than published, which no reader should miss.**
61.0 % of the published toll was a spread charged as a flat **cost level**; the corrected walk
charges it as **geometry** instead. Charging both double-counts it.

| stage | arm | n | gross | toll | **net** |
|---|---|---:|---:|---:|---:|
| every candidate emitted | OLD | 1,167,099 | −0.02256 | 0.08448 | **−0.10704** |
| every candidate emitted | **BOTH** | 1,117,986 | −0.04040 | 0.03102 | **−0.07142** |
| those that actually filled | OLD | 345,963 | −0.07612 | 0.28499 | **−0.36111** |
| those that actually filled | **BOTH** | 312,223 | −0.14466 | 0.11109 | **−0.25575** |
| **the trades the system actually took** | OLD | 507 | +0.18045 | 0.14938 | +0.03107 |
| **the trades the system actually took** | **BOTH** | 507 | +0.05216 | 0.01108 | **+0.04108** |

The pessimistic bound, for a reader who rejects the substitution and charges the spread twice:
emitted **−0.11862**, filled **−0.42473**, taken **−0.09722**. It is published at every stage.

**The taken book is net-positive on the corrected walk and still indistinguishable from
zero**: day-block CI95 [−0.0525, +0.1389], p(≤0) = 0.20 over 153 day blocks. The verdict's
statement that *this book cannot be adjudicated by running it* survives intact.

### 2.2 Two published headlines are overturned outright

**(a) "Before costs they are within half a percentage point of break-even."**
(Owner report, Correction 2 — the single most-quoted number in that document.)

| basis | n | win rate | breakeven | gap |
|---|---:|---:|---:|---:|
| published — gross | 298,537 | 37.98 % | 38.55 % | **−0.57 pp** |
| repaired roster, old walker — gross | 317,127 | 42.28 % | 42.57 % | −0.28 pp |
| **repaired roster, corrected — gross** | **312,223** | **36.34 %** | **43.22 %** | **−6.89 pp** |

**Twelve times larger.** The mechanism is **23,073 exit-reason changes** — 1.98 % of all
1,167,099 emissions — almost one-directional: 11,870 `target → stop`, 4,223 `path_end → stop`,
3,347 `target → no_fill`, against **168** `stop → target`. **93.13 %** of the whole gross delta
sits on rows that changed exit reason.

**(b) "The toll falls 7.4× across the deciles; the gross never leaves a ±0.04 band and has no
trend."** (FIND 2.)

**The published claim reproduces exactly on the old walker** — on the legacy clean cohort the
toll falls **7.49×**, the gross range is **0.0483** and the correlation between stop-width rank
and gross is **−0.8431**. On the repaired filled cohort at the same old walker: range 0.0459,
correlation **−0.8287**. Both are the published "±0.04 band, no trend."

**Charge the quote side and it inverts** (repaired filled cohort, ten deciles of the
generator's own stop width — figures re-derived directly from `M1_DECILES_V1.json`):

| decile | stop (bps) | median s/d | gross **OLD** | gross **CORRECTED** | toll |
|---:|---|---:|---:|---:|---:|
| 0 (tightest) | 0.26 – 2.89 | **0.2942** | **+0.01256** | **−0.29168** | 0.25120 |
| 5 | 9.33 – 12.01 | 0.0687 | −0.00003 | −0.11129 | 0.11623 |
| 9 (widest) | 41.49 – 1624.22 | 0.0367 | −0.03332 | **−0.08916** | 0.04218 |
| | | | corr **−0.8287** | corr **+0.8716** | |

Range **0.0459 → 0.2025**. **The tightest-stop decile — the only gross-positive cell in the
published table — is now the worst**, because it hands the broker 29.4 % of its risk unit at
the door.

> **The apparent edge in the tightest stops — the thing that made
> `structural_distance_extreme` look real, and the whole "trade tighter so the edge is a
> bigger fraction of R" argument — is the bid-ask, exactly and only.**

(`receipts/m1/M1_DECILES_V1.json`)

### 2.3 The verdict's three legs, re-derived

The wave-19 verdict was **SIGNAL** — the setups carry real directional content that is far too
small to transact. **That verdict does not change and is better supported than when it was
written.** But two of its three legs behave differently under the repair, and one of them
breaks as a number.

| leg | published | re-derived | standing |
|---|---|---|---|
| **1 — a 253× price-unit shortfall** | +0.0119 bps captured against a 3.0159 bps toll | on the eight open windows the numerator was **already negative before any repair** (−0.643 bps) and is **−2.153 bps** after | **STRENGTHENED — and the ratio is undefined.** There is no "shortfall factor" because there is nothing in the numerator. **Retire the 253× headline.** |
| **2 — a 0.97× accumulation ratio** | 0.965× against a live sleeve's 37.58×, published with **no interval** | 0.867× (legacy) → **0.587×** (repaired), **CI95 [−2.07, +2.22]**; per-window values run 3.0×, 4.4×, 1.0×, −4.8×, −4.4×, −1.5×, −1.3×, 2.8× | **DIES AS A NUMBER, SURVIVES AS A BOUND.** The ratio was never a measurable quantity. |
| **3 — a free broker still leaves it negative** | −0.01327 R/trade, 104.72 % cost reduction required | **−0.00600 R/trade**, 102.12 % required | **UNCHANGED.** Same arithmetic, magnitude 2.2× smaller. Still infeasible. |

**What replaces leg 2, and it is cleaner than the ratio it replaces:**

| statement | broad family (repaired) | live sleeve control (repaired) |
|---|---:|---:|
| **P(growth ≥ 10×)** — the screen's own bar | **0.0073** | **0.629** |
| signal at 320 h, per-row bps | −0.107 | **+142.76** |
| its 95 % CI | [−0.630, +0.410] | [+40.94, +233.40] |
| its own measured toll at 320 h | 3.19 bps | 29.23 bps |
| **signal vs toll, at the 95 % bound that favours it** | upper bound **7.4× SHORT** | lower bound **1.40× OVER** |

Even at the **top** of its own 95 % interval the broad family's 320-hour signal is 7.4× below
the toll it must pay to transact, while the live control clears its own — larger — toll at the
**bottom** of its interval.

**And the live control's 37.58× was mostly a coin flip.** The published figure paired against
a single coin draw, which discards half the pairs. A deterministic mirror — every row walked
both sides — gives **15.94×** on the same rows and the same old walker, and 16.65× on the
repaired one. **Both of the two numbers that expressed this discriminant (0.97× and 37.58×)
should be retired.**
(`receipts/m1/M1_ACCUM_CI_V1.json`, `M1_LIVE_ACCUM_V1.json`)

### 2.4 The live sleeve estate — nine sleeves change sign

Population: 22,354 trades, 32 sleeves, 2017–2026, whole population.

**Pooled:**

| | R/trade |
|---|---:|
| published gross | **+0.112763** |
| corrected gross (mid band) | **−0.027726** |
| **Δ gross** | **−0.140489** (se 0.004619) |
| published net | −0.174858 |
| corrected net | **−0.123124** |
| **Δ net** | **+0.051734** |

Total R over the estate: **+2,520.7 → −619.8**.

**The arithmetic checks exactly**, which is what makes the net substitution legitimate: the
estate's mean spread charge is **0.191709 R/trade** and the mean of `spread ÷ stop distance`
over the same rows is **0.191709**, identical to six decimals. So `cost_r` charges exactly one
spread as a flat level: `−0.140489 + 0.191709 = +0.051220`, against a measured `+0.051734`
(the 0.0005 residual is swap on trades whose hold changed when their exit flipped).

**Where the delta lives:**

| bucket | n | share of trades | share of delta | mean within |
|---|---:|---:|---:|---:|
| same exit: stop | 13,221 | 59.14 % | 0.00 % | **±0.00000** |
| same exit: target | 6,816 | 30.49 % | 0.00 % | **±0.00000** |
| same exit: trail | 1,042 | 4.66 % | 2.89 % | −0.08720 |
| same exit: maxbars | 362 | 1.62 % | 0.59 % | −0.05089 |
| **CHANGED: target → stop** | **732** | **3.27 %** | **84.68 %** | **−3.63320** |
| CHANGED: trail → stop | 127 | 0.57 % | 7.00 % | −1.72997 |
| CHANGED: maxbars → stop | 50 | 0.22 % | 4.60 % | −2.88727 |
| CHANGED: target → maxbars | 4 | 0.02 % | 0.24 % | −1.90830 |

**Nine sleeves flip from a positive published gross to a negative corrected one.** The ten
largest movers:

| sleeve | n | gross published | gross corrected | Δ | exits changed | s/d | sign |
|---|---:|---:|---:|---:|---:|---:|---|
| liq_asia_up_low_metal | 157 | +0.12102 | −0.46497 | −0.58599 | 14.65 % | 0.6619 | **FLIP** |
| asia_pdl_fade | 2,827 | +0.17195 | −0.32888 | −0.50083 | 12.98 % | 0.2435 | **FLIP** |
| vss_fxcross_london_up_low | 308 | +0.23701 | −0.05520 | −0.29221 | 9.74 % | 0.2174 | **FLIP** |
| **sub_mid_dn_revert** *(ARMED)* | 533 | +0.47842 | **+0.19325** | −0.28518 | 7.13 % | 0.0871 | |
| mx_cadjpy_d1_volume_surge_reversal | 286 | +0.12238 | −0.05594 | −0.17832 | 5.94 % | 0.1440 | **FLIP** |
| mx_nzdjpy_d1_donchian_20_breakout | 503 | +0.05599 | −0.11779 | −0.17378 | 5.76 % | 0.2044 | **FLIP** |
| metal_session_reversion | 837 | +0.11112 | −0.04398 | −0.15509 | 7.05 % | 0.1106 | **FLIP** |
| kz_london_crypto_low | 286 | −0.16343 | −0.30849 | −0.14506 | 2.45 % | 0.1203 | |
| asian_fade | 1,319 | +0.23821 | +0.10117 | −0.13704 | 5.15 % | 0.1092 | |
| **crypto** *(ARMED)* | 181 | +0.56732 | **+0.43389** | −0.13343 | 2.76 % | 0.0093 | |

Also flipping: `fx_jpy` (n = 3,984, +0.0687 → −0.0473), which you pulled from the live book on
2026-07-30 on other evidence. **This correction says it was never positive.**

**The pattern is s/d and nothing else.** The five worst sleeves are the five with the widest
spread relative to their own stop; the five with s/d < 0.01 are unchanged to four decimals.
That is the mechanism, not a coincidence.

**No sleeve changes NET sign.** 9 change gross sign; 0 of 29 change net sign. The estate is
net-negative in both accountings.

### 2.5 The armed sleeves

**First — the armed set itself was wrong in three wave artifacts, at both ends.**

Read from the committed launcher (`scripts/run_book_supervisor.ps1:86-87`) and reconciled
against your 2026-08-05 disarm instruction:

| | armed today, **both accounts** |
|---|---|
| ✅ | `crypto`, `energy_agri`, `sub_xvol_pullback`, **`sub_mid_dn_revert`** |
| ❌ removed 2026-08-05 by your instruction | `mx_btcusd_d1_donchian_20_breakout` |

Three wave-20 artifacts declared a four-sleeve set that **omitted `sub_mid_dn_revert`** and
**included `mx_btcusd`**. Lane v1 caught it; lane m3 re-derived it from the launcher and
measured both readings. **The omission is the expensive half** — `sub_mid_dn_revert` is the
largest proportional casualty of the entire repair and had no fold table, no p-value and no
gated verdict at corrected numbers anywhere in the wave until m3 produced them. That is now
fixed by construction (repair 5).

**Per sleeve, at the ratified rule:**

| sleeve | conf | n | gross published → corrected | Δ | net R/day published | corrected | conservative |
|---|---:|---:|---|---:|---:|---:|---:|
| **crypto** | 0.85 | 181 | +0.56732 → **+0.43389** | **−23.5 %** | +0.19296 | +0.15592 | +0.10825 |
| **sub_mid_dn_revert** | 0.20 | 533 | +0.47842 → **+0.19325** | **−59.6 %** | +0.12928 | +0.07736 | **−0.16579** |
| **energy_agri** | 0.80 | 67 | +0.77921 → +0.77851 | **−0.1 %** | −0.09178 | −0.06542 | −0.09256 |
| **sub_xvol_pullback** | 0.45 | 88 | +1.26850 → +1.26764 | **−0.1 %** | +0.92706 | +0.97050 | +0.93018 |
| `mx_btcusd` *(disarmed 08-05)* | 0.025 | 318 | +0.34906 → +0.34906 | **0.0 %** | +0.21130 | +0.22324 | +0.21079 |

`p(daily mean ≤ 0)`, published → corrected → conservative: `crypto` 0.121 → 0.163 → 0.255;
**`sub_mid_dn_revert` 0.087 → 0.188 → 0.958**; `sub_xvol_pullback` 0.0014 → 0.0009 → 0.0014;
`energy_agri` 0.620 → 0.594 → 0.621.

**`sub_mid_dn_revert` in full, because it is the finding that reaches your money.** At the
ratified rule its pooled out-of-sample expectancy collapses:

| walk | spread | verdict | pooled OOS R/day | fold means (5 OOS folds) | failing gates |
|---|---|---|---:|---|---|
| published | charged | REJECT | **+0.12065** | −0.337, +0.249, −0.444, +0.402, +0.734 | robustness, significance |
| **corrected** | removed *(honest)* | REJECT | **+0.00277** | −0.465, −0.241, −0.386, +0.355, +0.750 | stability, robustness, significance |
| **corrected** | charged *(conservative)* | REJECT | **−0.19583** | −0.791, −0.465, −0.691, +0.262, +0.705 | **all five core gates** |

**−97.7 % of its expectancy.** Read the fold means, not the pooled number: it goes from 3 of 5
positive folds to **2 of 5**, and **the three negative folds are the three oldest**. All of its
remaining expectancy sits in the two most recent folds.

It was already a REJECT, so **no admission moves**. What moves is the magnitude any sizing
decision would rest on.

**`crypto`'s −23.5 %, with its fragility stated rather than buried.** The entire effect is
**five trades out of 181** (four `target → stop`, one `maxbars → stop`). It is band-sensitive
(−0.032 at the low spread band, −0.142 at the high) and lands hardest on folds 1 and 4. Its
day-block p on net goes 0.0162 → 0.0345 — a 2× degradation that still passes at α = 0.10 and
now has materially less room at 0.05. **It is a point estimate on n = 5 events, not a precise
one.**

**`energy_agri` and `sub_xvol_pullback` are unchanged**, with **zero** exit-reason changes
between them. Both have s/d below 0.02 — one spread almost never crosses a level. That is not
luck; it is the same mechanism that kills the tight-stop families, seen from the other side.

### 2.6 The standing admission — unchanged

`mx_btcusd @ target_5R` was the estate's only admission at the sealed standard. Re-gated at
the ratified rule and at the **larger** V27 family (59 declared, not V2's 35):

| walk | cost band | verdict | pooled OOS R/day | p_raw | q |
|---|---|---|---:|---:|---:|
| published | low | ADMIT | +0.98334 | 0.001100 | 0.0649 |
| published | mid | ADMIT | +0.98169 | 0.001100 | 0.0649 |
| published | high | REJECT | +0.87808 | 0.005099 | 0.2360 |
| **corrected** | **low** | **ADMIT** | **+0.98322** | **0.001100** | **0.0649** |
| **corrected** | **mid** | **ADMIT** | **+0.98017** | **0.001100** | **0.0649** |
| **corrected** | **high** | **REJECT** | +0.76473 | 0.016298 | 0.4808 |

**"Admits at two of three cost bands" is still exactly true**, with the same two bands and the
same rejecting band. Pooled OOS moves **−0.16 %**. `p_raw` does not move at all. Fold
positivity stays 5/5. **One** exit reason changes in 232 trades.

The reason is mechanical and does not generalise: BTCUSD's spread-over-risk is the smallest in
the estate (0.0124 R against the estate's 0.1917).

**And the separate repair that DID kill this cell was composed with this one, so the two are
not confused.** A1b's corrected null flips it ADMIT → REJECT. Running A1b's own
`corrected_p_for_arm` on the daily series behind both walks: **0.002810 → 0.002843 (+1.2 %)**.
The walker moves it by nothing. **The ADMIT → REJECT is A1b's finding in full**; wave 20
neither causes it nor rescues it. (The sleeve is disarmed either way.)
(`receipts/m3/M3_COMPOSED_NULL_V1.json`)

### 2.7 What did NOT move — because "unchanged" is a result

| claim | before | after | status |
|---|---|---|---|
| broad V4 family verdict | SIGNAL | SIGNAL | **UNCHANGED, better supported** |
| leg 3 — a free broker still leaves it negative | −0.01327 R/trade, 104.72 % cut needed | −0.00600, 102.12 % needed | **UNCHANGED**, 2.2× smaller |
| `mx_btcusd @ target_5R` at the ratified rule | ADMIT at 2 of 3 bands, p 0.0011 | ADMIT at 2 of 3 bands, p 0.0011 | **UNCHANGED** |
| `energy_agri` gross | +0.77921 | +0.77851 | **UNCHANGED** (−0.1 %, 0 exit changes) |
| `sub_xvol_pullback` gross | +1.26850 | +1.26764 | **UNCHANGED** (−0.1 %, 0 exit changes) |
| every sleeve's NET sign | 0 of 29 flip | 0 of 29 flip | **UNCHANGED** |
| armed-sleeve live behaviour | — | 556,251 generator calls, identical sha256 | **UNCHANGED, proved by execution** |
| H1 decision-contract drift | 3 entries (1 real + 2 LFS pointers) | 3 entries, identical | **UNCHANGED — no seal option spent** |
| test suite, by failure set | 96 bad | 95 bad, **0 regressed**, +66 net new passing | **NO REGRESSIONS** |
| `run_book.py` import closure | 240 modules, 84 project | contains **none** of the four touched files | **UNCHANGED** |

**The exit-contract finding also survives, and the reasoning that killed it was a category
error.** Wave 19 reasoned: the effect is +0.035 R/trade and the walker bias is −0.07 to −0.12,
"so it is below the walker-bias floor." **A paired difference between two exit contracts on the
same rows is not a level.** Whatever part of the bias is common to both contracts cancels
exactly — and it is common on the 73–76 % of rows where the target contract never reaches its
target.

Measured on 1,127,805 emissions, walking **both** contracts on the same row: the correction
moves the **level** of `target_2.0R` by −0.102379 and the **paired delta** by −0.003990. Ratio
**25.7×**. `stop_only_horizon` beats `target_2.0R` by +0.039161 R/emission fill-anchored, day-block
CI95 [+0.01154, +0.06977], p 0.00235. Under level anchoring the delta gets *bigger* and its
month count improves 7/8 → **8/8**.
(`receipts/m3/M3_EXIT_CONTRACT_V1.json`)

---

## 3. WHAT IT MEANS FOR THE FUNDED ACCOUNTS

**Both accounts are armed and trading real money. Nothing in this wave changed a single byte
of live behaviour, and that was proved by execution rather than argued.**

Each armed sleeve's own generator callable was resolved from the live sleeve registry, driven
over **every decision instant** in the FTMO M15/H4/D1 archive at HEAD and at the physically
reverted parent tree, and the full emitted-order stream — every field, in order, at full float
precision — was hashed. **The two hashes are the same 64 hex characters over 556,251 generator
calls.** Structurally corroborated in clean interpreters: `run_book.py`'s import closure is 240
modules and contains none of the four touched files.
(`receipts/v1/V1_ARMED_BEHAVIOUR_{BEFORE,AFTER}_V1.json`)

### 3.1 Were figures you have been trading on wrong? Yes. Three of them.

| what you were told | what it is | how much |
|---|---|---|
| `crypto` earns +0.567 R/trade gross | **+0.434** | −23.5 %, on five trades |
| `sub_mid_dn_revert` earns +0.478 R/trade gross | **+0.193** | −59.6 %; its expectancy falls **97.7 %** |
| the estate's published **net** of −0.175 R/trade | **−0.123** | +0.052 — this one was too **harsh** |

`energy_agri` and `sub_xvol_pullback` — which between them carry the confidence weight — are
unchanged.

### 3.2 What it does to the book's probability of passing an evaluation

**These are on the ARCHIVE population** — the historical sleeve walk — **not the W7 caches the
5.46 %/month and 0.9172 headlines come from.** See §3.3; that distinction is load-bearing.

Armed four (`crypto, energy_agri, sub_mid_dn_revert, sub_xvol_pullback`), registry-confidence
weights, 2 % nominal dial, each firm's **measured** rules, 581 book days, 200,000 Monte Carlo
paths:

| arm | R / book-day | p(mean ≤ 0) | FTMO phase 1 | **FTMO 2-phase** | FN phase 1 | **FN 2-phase** |
|---|---:|---:|---:|---:|---:|---:|
| published walk, spread charged | +0.07654 | 0.0244 | 0.7023 | **0.5468** | 0.7235 | **0.5661** |
| **corrected walk, spread removed** *(the arithmetically right arm)* | **+0.06477** | 0.0416 | 0.6780 | **0.5157** | 0.7008 | **0.5366** |
| corrected walk, spread charged *(conservative bound)* | +0.02029 | 0.3011 | 0.5183 | **0.3370** | 0.5539 | **0.3626** |
| corrected at the high spread band, charged | +0.00158 | 0.4837 | 0.4565 | 0.2786 | 0.4965 | 0.3059 |

**Stated in both units, because the difference matters and the source lane got it wrong:**

| move | FTMO 2-phase | redacted_account 2-phase |
|---|---|---|
| published → **honest** | 0.5468 → 0.5157 = **−3.10 pp** (−5.7 % relative) | 0.5661 → 0.5366 = **−2.95 pp** (−5.2 % relative) |
| published → **conservative** | 0.5468 → 0.3370 = **−20.97 pp** (−38.4 % relative) | 0.5661 → 0.3626 = **−20.35 pp** (−35.9 % relative) |

> **Correction to lane m3's own write-up, and it is the kind you would have caught.**
> `SESSION_M3_ESTATE_RESTATED.md` §4.2 reads *"the honest arm costs 5.7 pp of two-phase
> `p_pass` on FTMO (0.5468 → 0.5157) and 2.9 pp on redacted_account."* `0.5468 − 0.5157 = 0.0311`,
> which is **3.10 percentage points**, not 5.7. The 5.7 is the *relative* fall (5.67 %)
> labelled as an absolute one — and the redacted_account figure in the same sentence **is** absolute,
> so the sentence silently switches units between its two halves. The receipt
> (`M3_ARMED_ECON_V1.json`) is correct; only the prose is wrong. The conservative arm's
> "21.0 pp" is right as an absolute (20.97).

The conservative arm also takes the book's daily mean to `p(mean ≤ 0) = 0.30` — **not
distinguishable from zero.**

**Why there are two arms and not one.** Under the corrected walk a long buys the ask and sells
the bid; at its stop it realises exactly −1 R, so the round-trip spread is **already inside the
R**. Charging `cost_r`'s spread term on top of it counts the same physical fact twice. That is
my reading and it is the arm that makes every number *less* bad — which is precisely why it
must be argued for rather than assumed. **The spread-charged arm is carried everywhere for a
reader who rejects the argument.**

**This one convention is worth 17.87 pp of two-phase `p_pass` on FTMO** (0.3370 → 0.5157) **and
17.40 pp on redacted_account** (0.3626 → 0.5366) — more than five times the size of the repair it is
supposed to be accounting for. **It should be adjudicated once, in one place.** (m3's open-item
list puts this at "15.4 pp"; the receipt says 17.87. Use the receipt.)

### 3.3 The single largest thing this wave did NOT settle

**Every `p_pass` you have ever seen for the armed book comes from a different population than
the one above.**

`0.9172` FTMO / `0.9331` redacted_account, `4.501 %/month`, the 5-sleeve expansion at `6.120 %` —
all of these come from the **W7 recost caches** (`INTEG_W3_streams_cache.pkl` +
`INTEG_W5_new_streams_cache.pkl`). Those caches were **not** touched by this wave.

They were built by the same class of bar walk on the same BID archive. **So the inference that
the defect reaches them is strong — but it is an inference, and I am labelling it as one.** If
it holds, every published book economic moves in the same direction as §3.2, by an amount
nobody has measured.

**That is one session of work and it is the highest-value forward item this wave leaves
behind.**

### 3.4 The coverage hole that reaches armed money

**`energy_agri` is armed on redacted_account and not one of its 67 trades is priceable on that
account.** Both of its instruments (`USOIL.cash`, `UKOIL.cash`) are absent from the redacted_account
block of the broker-true cost table **and** from the redacted_account half of the spread model.

| sleeve | n | FTMO priceable | redacted_account priceable | armed on FN |
|---|---:|---:|---:|---|
| `energy_agri` | 67 | 100.0 % | **0.0 %** | **yes** |
| `sub_xvol_pullback` | 88 | 100.0 % | **45.45 %** | **yes** |
| `sub_mid_dn_revert` | 533 | 100.0 % | 77.49 % | yes |
| `crypto` | 181 | 100.0 % | 80.66 % | yes |
| **whole estate** | **22,354** | **100.00 %** | **63.76 %** | — |

45.45 % is below the ratified `min_retained_trade_frac` of 0.60, so the standard would return
**NOT_EVALUABLE** for `sub_xvol_pullback` on redacted_account.

**This is not a reason to disarm anything.** It is a statement about what is *measured*: there
is no redacted_account-costed number for a sleeve placing real orders on that account, and
redacted_account's half of every cost-true comparison rests on 63.76 % of the population. **It is a
data capture, not a code change, and it is the cheapest item in the whole register.**

### 3.5 What I am not saying

- No arming, disarming, sizing or dial recommendation is made or implied. Composition and risk
  are yours.
- No live-forward P&L was read. The VPS was not touched. No broker-mutating script was run.
- Nothing here crosses an admission threshold in either direction. The one verdict that moved
  (`mx_btcusd`, ADMIT → REJECT) was moved by a **different** repair, was composed with this one
  and proved unaffected by it, and concerns a sleeve you already disarmed.

---

## 4. WHAT IS STILL BENT

Four defects were found by accident. That is evidence there are more, not evidence we found
them all. Lane m4 went looking systematically, on the axis all four share — *a quantity
expressed in one unit and consumed as if it were another*. It found eight more and **repaired
none of them**, deliberately: finding and pricing is a different job from fixing, and mixing
them is how a repair lands without a blast radius.

| # | defect | where | magnitude | invalidates | cost to repair |
|---|---|---|---|---|---|
| **M4-1** | **Holding time: trading-time hours consumed as wall-clock hours.** Seven sites in six receipt files pass `bars_held × nominal_bar_minutes` into a cost function whose `rollover_nights` reads it as wall time and counts calendar midnights. | `aa_estate_generate.py:305` +6 sites; `costs/model.py:420-452`; done right at `walkforward/panel.py:120-121` | nights under-counted **34.8–93.0 %** on 10 sleeves; swap under-charged **+0.003669 R/trade pooled (20.81 % of the term)**. **Published net is too GOOD.** | AD's 1,631-cell exit frontier, AH's entry-hour lever, this wave's own published net | **one line per site**, then re-run the affected receipts. **No new data needed.** |
| **M4-2** | **redacted_account cannot price the book it is armed on.** | broker-true cost table (76 FN instruments vs 167 FTMO); the FN half of the spread model | FTMO 100.00 % priceable, redacted_account **63.76 %**; `energy_agri` **0.00 %** | any redacted_account economic claim about `energy_agri`; any FN/FTMO cost comparison | **a capture, not code.** 5 instruments. |
| **M4-3** | **The spread-era model's decidability guard is inverted.** Decidability keys on band half-width, and a broker-stamped constant era has all four dispersion terms exactly 0.0 — so the band is narrowest exactly where the data is most synthetic. | `src/costs/spread_model.py:440-458` | `require_decidable=True` removes **0 of 645** FTMO placeholder eras and **134 of 1,119** real ones. **25.48 %** of the estate's total spread charge sits on a non-RECORDED era | the strongest available "remove unpriceable eras" switch | ~1 function + tests |
| **M4-4** | **Slippage charged as a constant in R across a 110× range of stop distance** *within one symbol*. | `costs/model.py:709-716` | p95/p05 stop ratio inside one symbol: USOIL.cash **109.7×**, BTCUSD 37.4×. Implied price slippage on USOIL.cash spans 0.067 → 7.37 bps. 6.03 % of the cost basis | the slippage term at both tails of every sleeve | one number per symbol, from the W7 capture that already exists |
| **M4-5** | **The walker fills a stop AT the stop even when the bar opened beyond it.** MT5 fills at the first available price. | `primitives.py:83-84` (the vendored live primitive) and its copy `walkforward/exits.py:388-391` | 125 of 13,221 stop exits and 99 of 7,552 target exits gapped through. **−0.00103 R/trade standalone** (targets nearly cancel stops); **−0.01024 composed on top of the quote-side repair** | nothing alone — it is a *composition* risk | 2 lines, but `primitives.py` is parity-locked, so it is a switch not an edit |
| **M4-6** | **A price-to-USD conversion frozen at the 2026-07-25 FX snapshot, applied to 2000–2026.** | `costs/model.py:230-238`; 65 of 167 FTMO instruments | commission **over**-charged −0.001821 R/trade pooled; per-symbol ratio median 1.49×, max 2.16×, on 7,803 trades | deep-history commission on every JPY/EUR/GBP-quoted symbol | a date-indexed rate series; the D1 archive already carries every rate |
| **M4-7** | **Post-2007 US DST rule applied with no year guard** to archives starting in 1993/2000. | `utils/broker_clock.py:126-137` | **11 of 22,354** trades in a rule-disagreement window (9 of them in armed `sub_mid_dn_revert`) | nothing published, at this size | a 3-line year branch |
| **M4-8** | **LIVE, both accounts: the stress-derisk overlay uses a static broker offset** where the governor beside it uses the calendar-aware one. | `book_engine.py:260-261` → `admission.py:439`, vs `governor_state.py:103` | correct today; **1 h wrong from 2026-11-01** for one UTC hour a day (~19 weeks/year), leaking the in-progress server day into the "fully-realised prior days" window. Direction is safe-ish — the overlay can only *reduce* risk — but the leak-free claim fails | the overlay's leak-free claim | **pass the existing function.** The governor already calls it. |

**M4-8 is the only live-path item, it is safe-direction, and it has a hard date: 2026-11-01.**

### 4.1 And the parts that were checked and found SOUND

A hunt that only reports hits is not a measurement. **The cost model is in better shape than
expected.** Its decomposition on the estate is spread **66.65 %**, commission 21.19 %, swap
6.13 %, slippage 6.03 % — and the largest term is the one term that *is* era-corrected.

Verified sound: every bar file carries a timebase declaration and the loader **refuses** a file
without one; commission fitting sums both legs and normalises consistently; swap night counting
weights weekends at 0 and the triple-swap weekday at 3, summing to exactly 7 over a week; the
day-block bootstrap centres before resampling and wraps circularly; Benjamini-Hochberg is a
correct step-up with monotone q-values and both corrections coerce a non-finite p to 1.0; folds
are calendar-cut with train-side-only embargo sizing; contract geometry is exact on all 102
USD-profit FTMO instruments.

**Two standing estate numbers are now sharper:** B613's intrabar trail assumption is not 95.8 %
but **99.91 %** (1,168 of 1,169 trail exits have their level set on their own exit bar — the
published figure was one sleeve's), and the winsorisation floor of −1.3 R is **unreachable**
under the shipped walker (minimum gross over all 22,354 trades is exactly −1.0, which is the
structural tell behind M4-5).

---

## 5. WHAT IS NOW OPEN THAT WAS NOT

### 5.1 `structural_distance_extreme` is CLOSED — and it was the best thing we had

The wave-19 owner report called it *"the single most interesting unsettled thing in the
estate."* It was gross-positive in **15 consecutive windows across three independently written
harnesses**. It needed one tick re-walk to settle. That walk was run, on **177,046,057 real
bid/ask ticks** across two archives, with MT5's own trigger sides.

| cohort | n | estate convention | **tick truth** | CI95 | p(≤0) |
|---|---:|---:|---:|---|---:|
| frozen roster, 4 tick-covered instruments × 7 windows | 3,315 | **+0.0418** | **−0.2131** | [−0.2608, −0.1624] | **1.0000** |
| **never-read** 2026-06-18 … 07-24, **24 instruments** | 3,269 | **+0.0124** | **−0.3586** | [−0.4097, −0.3054] | **1.0000** |

Positivity — which is what "persistence" means:

| | estate convention | **tick truth** |
|---|---:|---:|
| frozen windows | 6 / 7 | **0 / 7** |
| never-read weeks | 4 / 6 | **0 / 6** |
| never-read instruments | 15 / 24 | **1 / 24** |
| never-read risk-distance quintiles | — | **0 / 5** |

**The streak DID extend.** At the estate's own convention the never-read window is a 16th
consecutive positive window, +0.0124 with CI [−0.052, +0.082]. The same rows at tick truth book
−0.3586 with a CI that excludes zero. **The persistence is real and it is an artifact of
quoting both legs on one side of a book the round trip crosses twice.**

**And there was never a direction call to preserve.** The exact side mirror — same instants,
same risk, opposite direction — books −0.2504 and −0.3453 against the family's −0.2131 and
−0.3586. The signal is +0.037 on one cohort and −0.013 on the other: **it changes sign between
cohorts and neither interval excludes zero.** The family and its mirror lose the same amount.

**The mechanism has a measured break-even.** Binned by each row's own spread-over-risk, the
bid-tape arm is **flat** across a 60× range of s/d, while the tick-true arm falls monotonically
from +0.1138 to −0.8774. Break-even is **s/d ≈ 0.04**. The family's own median s/d is
**0.2267 — 5.7× over the line** — and its edge is concentrated in its tightest stops, which is
exactly where that ratio is largest.

**Recommendation: CLOSE the family.** Requirement: spread ≤ ~4 % of the trade's own risk
distance. Actual: 22.7 %. Buying that ratio from the denominator is already refuted — widening
the stop 2.83× on identical setups is worth zero. **The only remaining lever is the
instrument, and exactly 1 of 24 qualifies.**

**The one cell the evidence does not kill, filed honestly and NOT proposed.** BTCUSD in the
never-read window: median s/d **0.0162** — the only instrument of 24 below the measured
break-even — tick-true **+0.1750 R/trade**, raw p 0.063 at 1.5R and 0.050 at 2R, signal vs
mirror +0.350, on n = 100 over 32 days. **It is not admissible**: one instrument, one 5-week
window, raw p only, 24-instrument family bill unpaid. It is a **pre-declarable hypothesis**,
and if it is ever run the family bill must be declared **first** — otherwise it is the
best-of-24 pick the mechanism guarantees will look positive.

### 5.2 The accumulation screen needs re-specifying before it is used again

Both of its published numbers (0.97× and 37.58×) are partly coin-draw artifacts and neither
carried an interval. The replacement is already measured and it is a **probability**, not a
ratio:

> **P(growth ≥ 10×) = 0.0073** for the broad family against **0.629** for the live control,
> plus the level test: the 320-hour signal's own 95 % bound against its own toll — **7.4×
> SHORT** vs **1.40× OVER**.

Someone should decide whether that is the estate's admission screen and pin it with a test
**before** the next candidate family is screened.

### 5.3 The rest of the open list, ranked

| | item | why it matters | cost |
|---|---|---|---|
| 1 | **Re-walk the W7 recost caches on the corrected instrument** | Every book economic you have ever seen comes from them. §3.3. | one session, no new data |
| 2 | **Adjudicate the cost convention once** | Worth +0.052 R/trade on the estate and **17.87 points** of two-phase `p_pass` on FTMO — more than 5× the repair it is accounting for. Both arms are published; nobody has picked. | a decision, not a measurement |
| 3 | **The redacted_account capture** | Blocks any cost-true statement about a sleeve placing real orders. §3.4. | 5 instruments |
| 4 | **Diagnose `sub_mid_dn_revert`'s chronological decay** | Its three oldest OOS folds go negative under the correction; its two most recent stay positive. Regime story or spread-era story? That is the difference between *"this sleeve is dead"* and *"size it on its recent folds."* | one session |
| 5 | **Re-walk the three sealed months** | They still carry the estate's last standing positive statement about this family (+0.02718 R/fill, p 0.001, 3/3) — measured on the uncorrected walker. I **bounded** it (the correction is 4.7× its size with constant sign) rather than measuring it. Those rows are already spent, so re-walking costs no held-out data. | **the cheapest remaining item** |
| 6 | **Re-run AD's exit frontier and AH's entry-hour lever after M4-1** | Both consume the wrong holding time. Neither prescription can be quoted until they are re-run. | no new data |
| 7 | **Tick-validate the resting-limit fill** | The at-market limb of the correction was validated on real ticks; the resting-limit limb was not. It is worth ~3,347 phantom targets. | one walk over the 37-day tick overlap |

### 5.4 A seal hole that is pre-existing, structural, and that this wave is the first to walk through

**Both repair lanes claimed "no bound file was edited." Both were right and both
under-described the situation.**

`src/research_infra/v4_timewarp_simulated_live_research_loop.py` **is** a decision-contract-bound
path **and** is in `code_authority_paths` — and at `:56` it imports
`broader_origin_generators.generate_live_broader_origin_candidates` at module level: the exact
function lane r2 changed. Measured in a clean interpreter, **54 project modules are reachable by
import from that bound file and only 10 are sealed.**

So a default-ON change to an unbound module alters what a future sealed replay generates while
every drift check and the execution-seal digest report zero. **The hole is pre-existing and
structural; this wave is simply the first change to walk through it.** The legacy escape hatch
reproduces the old behaviour byte-exactly (174,497 / 174,497 rows) — but only for an operator
who knows to reach for it.

**No sealed replay is scheduled and the parked campaign's resume option is already dead by an
earlier authorised seal break, so this costs nothing today.** It should be closed before any
sealed window is ever run again.
(`receipts/v1/V1_SEAL_IMPORT_HOLE_V1.json`)

### 5.5 Documents that now contain numbers this wave overturns

Two published documents carry numbers that are now wrong, and they are the ones you read. **I
have not edited either — that is a call for whoever owns the record, not for a measurement
lane.**

| document | what is wrong | what it should say |
|---|---|---|
| `phase19/SLEEVES_OR_USAGE_OWNER_REPORT.md` — Correction 2 | *"before costs they are within half a percentage point of break-even"* (−0.57 pp) | **−6.89 pp** |
| same — FIND 2 | *"the gross never leaves a ±0.04 band and has no trend"* | range **0.203**, correlation **+0.87**, sign-inverted |
| same — FIND 6 | *"any usage lever worth less than 0.07 R/trade is unfalsifiable"* | **0.14 R/trade** on the sleeve estate |
| `phase19/SLEEVES_OR_USAGE_VERDICT.md` §1 and §3 | the **253× / 0.97× / 37.58×** triple | the first has no numerator, the second has a CI four units wide, the third was mostly a coin flip |

**The verdict itself — SIGNAL — does not change.** What has to change is the rhetoric, because
three of its most quotable numbers were artifacts of the bent ruler.

---

## 6. HOW TO CHECK THIS

Every table above is reproducible from a committed script. Nothing was taken on trust between
lanes: lane v1 re-derived r1's and r2's central claims from primary data with its own code
before believing them, and every measurement lane published the controls it had to pass.

| lane | what it did | receipt |
|---|---|---|
| **r1** | the canonical quote-side walker + the estate re-walk | `phase20/SESSION_R1_QUOTE_SIDE_WALKER.md`, `receipts/r1/` |
| **r2** | the generator's R-denominated emission contract | `SESSION_R2_GENERATOR_REPAIR.md`, `receipts/r2/` |
| **v1** | verification — A/B, armed behaviour, tick truth, seal hole | `SESSION_V1_VERIFICATION.md`, `receipts/v1/` |
| **m1** | the broad family restated on the repaired instrument | `SESSION_M1_BROAD_RESTATED.md`, `receipts/m1/` |
| **m2** | `structural_distance_extreme` settled on real ticks | `SESSION_M2_STRUCTURAL_DISTANCE_EXTREME.md`, `receipts/m2/` |
| **m3** | the live sleeve estate re-gated at the ratified rule | `SESSION_M3_ESTATE_RESTATED.md`, `receipts/m3/` |
| **m4** | the ranked register of what is still bent | `SESSION_M4_DEFECT_HUNT.md`, `receipts/m4/` |

**The controls that make these re-measurements rather than new experiments:**

| control | result |
|---|---|
| the uncorrected arm reproduces the published estate gross | **22,354 / 22,354 rows, max absolute error 0.0** |
| the uncorrected broad arm reproduces the published roster economics | identical to six decimals on n, gross, cost, net **and** fills |
| the published gate arm reproduces the ratified population rule's grid | **12 / 12 cells**, identical p, n and verdicts |
| the archive book reproduces the published control book | 201/201 days, `p_pass` 0.566017 / 0.56631 |
| the accumulation harness reproduces the published curve | **exact at all six horizons**, max \|Δ\| 6.9e-18 |
| r2's blast radius, both directions, against a frozen roster | 0 added, 90,217 removed == 90,217 predicted, **8/8 windows exact** |
| the m2 emitter reproduces the frozen roster | **23,103 / 23,103 exact**, 0 geometry mismatches |
| five arithmetic invariants on the correction itself | **5 / 5 hold**; max at-market delta exactly 0.0 |

---

## 7. SAFETY

| | |
|---|---|
| **Live behaviour** | **UNCHANGED**, proved by execution: identical sha256 over 556,251 armed-sleeve generator calls at HEAD and at the physically reverted parent. |
| **Live isolation** | `run_book.py`'s import closure is 240 modules (84 project) and contains **none** of the four touched files. The broad-origin generator has never traded live. Pinned by a test that spawns a clean interpreter and reads `sys.modules`. |
| **Test suite** | Full-suite A/B against the parent with the tree **physically reverted**: 96 bad → 95, failure sets identical as sets, **0 regressed**, +66 net new passing. The one "fixed" row is claimed as an environment flake, not a repair. |
| **H1 (decision contract)** | 3 drift entries at HEAD, **identical to before the wave** — one pre-existing owner-authorised break plus two unhydrated LFS pointers, which are not drift. A recursive scan of all 46 + 48 bound paths returns **zero** hits for any touched file. **No new option spent.** |
| **Config** | **No config byte moved.** All new runtime keys are absent from every file under `config/`, so the code default is the shipped behaviour and the sealed config is untouched. Neither activation token needs re-minting. |
| **The launcher** | `scripts/run_book_supervisor.ps1` was edited to carry your 2026-08-05 disarm decision. **It must never be carried wholesale to the host** — the host's copy is a different, ~2.5× larger file with different key names. Carry individual argument changes, never the file. |
| **VPS** | Not touched. No broker-mutating script was run. No live-forward P&L was read. |
| **Sealed data** | The three sealed months were not opened. The never-read tick window (2026-06-18 … 07-24) was opened **once**, on the pre-declared question in §5.1, and is now spent for this family. |

---

## 8. THE SHORT VERSION

1. **The ruler was bent in our favour, and it is now straight.** One module, one kwarg, 27
   hand-computed tests.
2. **The broad V4 family is more finished than we said**, not less — 0 of 10 families
   gross-positive where 5 were, and its last real family died on real ticks. **The verdict does
   not change; three of its headline numbers should be retired.**
3. **Two armed sleeves' published economics were wrong** — `crypto` by 23.5 %,
   `sub_mid_dn_revert` by 59.6 % and 97.7 % of its expectancy. **Two were not** — `energy_agri`
   and `sub_xvol_pullback` move by 0.1 %.
4. **The standing admission survives the walker untouched.** It was killed by a different
   repair, and the two were composed to prove it.
5. **The book's probability of passing an evaluation, on the archive population, falls 3.1
   points honest and 21.0 points conservative** (FTMO, two-phase). Which of those is right
   turns on **one cost convention worth 17.9 points** that nobody has adjudicated — five times
   the size of the repair itself.
6. **The numbers you actually trade on — the W7 caches — were not re-walked.** That is one
   session and it is the next thing to do.
7. **Eight more defects are found, priced and ranked.** The largest is a holding-time unit
   error costing 20.8 % of the swap term. One is live and has a date: **2026-11-01**.
8. **Nothing here is a reason to touch either account today**, and the proof that nothing
   moved is a hash, not an argument.
