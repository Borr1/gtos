# Lane 2 — where the trades go to die: the exit horizon as the primary object

**Commission:** owner swarm, 2026-08-12, lane 2 of 8. *"Why are we losing or getting timed out."*
**Scope discipline.** Measurement only. Nothing armed, nothing on a broker, no VPS, no config, no
git write, no decision-contract-bound file touched. Every number below is recomputed on this machine
from the sealed corpora and the true-UTC M1 archive. Receipts: `lane2_receipts/` — 17 scripts and 13
JSON artifacts.

**Population:** all five sealed-read 2026 months (Feb, Apr, May, Jun, Jul) — **632,934 candidate
occurrences, 162,266 fills, 151,732 usable at every horizon, 100 trading days.** This is the *funnel*
candidate corpus. It is **not** the armed sleeve estate; §8 states that boundary precisely.

---

## 0. The answer in six lines

| question | answer |
|---|---|
| **Is the time stop truncating winners?** | **No — it is banking them.** The 41,204 trades time-stopped at the sealed clock are the **only positive bucket in the entire pool**: +0.1403 R/trade net, +5,781 R total, against a pool mean of −0.2326. Letting them all run to their natural barrier costs **−0.0187 R/trade** [−0.053, +0.017]. |
| **Is time-to-hit really ~d²?** | **Yes, and precisely.** Measured one-sided first-passage exponent **α = 2.087** pooled (2.174 restricted to d ≤ 1 R where 97 % of trades reach the level). The commission's mechanism is confirmed. Its predicted *consequence* is refuted by measurement: optional stopping holds, so the truncated cohort marks at fair value. |
| **What is the exit horizon worth?** | **At most +0.0034 R/trade, and its CI contains zero.** Across a **128× range** (15 min → unbounded, fill-anchored) the pooled net moves only between −0.2292 and −0.2377. On the *deployable* selected book, **extending to 2× costs −15.88 R over five months, CI [−26.9, −5.2], p = 0.0047.** The sealed 120-minute clock is already at or beside its optimum. |
| **Then why are we losing?** | **Cost is 9.4× the edge.** Total cost 0.2659 R/trade (spread 0.1233 + slippage/swap/commission 0.1426) against a measured directional edge of **+0.0282 R/trade** [+0.0098, +0.0462] over a driftless barrier walk. The geometry demands a 34.9 % hit rate to break even gross; the market delivers 31.9 %. |
| **What DOES move it?** | **Stop width — 47× the horizon lever.** Widening the stop 4× (target held at 2 R) is worth **+0.1594 R/trade [+0.1471, +0.1720]**, on 151,683 trades, because every cost term except one is a price quantity divided by the stop. |
| **Does that fix it?** | **No, and the ceiling is measurable.** The edge does *not* scale with the stop — it decays from +0.0282 (k=1) to −0.0158 (k=4). Cost floors at the **flat 0.02 R** `expected_slippage_r` constant. **The limit of the stop-widening lever is ≈ −0.036 R/trade.** No stop width makes this candidate pool positive. |

**One sentence for the owner: the clock is not the problem, and changing it is worth nothing —
the problem is that this candidate pool's directional edge is +0.028 R/trade against 0.266 R/trade
of cost, and the only lever with real magnitude (a 4× wider stop, +0.159 R/trade) still tops out
about 0.036 R short of break-even.**

---

## 1. The instrument, and its fidelity receipt

### 1.1 What the sealed labeller actually is

`resolve_post_submission_m1_lifecycle` (`src/research_infra/walkforward/quote_side.py:1032`) is the
wave-21 outcome authority. It takes two independent clocks:

* `expiry_utc` — how long a LIMIT order rests before it is cancelled;
* `required_horizon_utc` — when an open position is marked out.

**Every caller in the estate passes the same value for both.**
`candidate_funnel_analysis.py:152-153` — `expiry_utc=expiry, required_horizon_utc=expiry`. Same at
`postmortem/pm_geometry.py:162-163`, `phase0_receipts/p0_walk.py:138-139`, `p0_live_arm.py:70-71`,
`wave21_forward_shadow/shadow_lifecycle.py:182`.

And that value comes from `limit_first_expiry_utc`, generated at
`src/research_infra/v4_timewarp_simulated_live_research_loop.py:87938-87941`:

```python
expiry = min(
    asof + timedelta(minutes=campaign.pending_expiry_minutes),
    datetime.fromisoformat(day).replace(tzinfo=timezone.utc) + timedelta(days=1),
)
```

with `REPAIRED_PENDING_EXPIRY_MINUTES = 120` (`:420`).

> **The object the estate calls a "time stop" is a pending-order cancellation timer.** It was
> designed to answer *"how long do I leave an unfilled limit on the book"*, and it is being read as
> *"how long do I let a trade run"*. Those are different questions with different right answers.
> Measured, the reuse turns out not to cost anything (§4) — but it was never chosen, and nobody had
> checked.

Measured on the corpus: **93.43 % of all 632,934 rows carry exactly a 120-minute horizon**; the
remaining 6.57 % are clipped short by the `day + 1 day` term. `lane2_receipts/A_census.json`.

### 1.2 Two defects the clock design produces, both quantified

**(i) 5,619 rows (0.89 %) are born already expired.** When the decision falls exactly on the
trading-day boundary the `min()` returns a horizon equal to the submission instant, and
`quote_side.py:1147-1148` (`if not submission < expiry <= horizon`) censors them **`CENSORED_GEOMETRY`
— all 5,619, with no exception.** They are generated, scored, and discarded. Receipt:
`ADVERSARIAL.json → zero_horizon_rows`.

**(ii) The clock runs from SUBMISSION, so a resting limit spends its trade life waiting.** Measured
over 84,435 LIMIT fills: median rest **39 min**, mean **45.6 min**, leaving a median of **79 min** and
a mean of **72.6 min** of actual trade life against the nominal 120. **35.0 % of limit fills get under
60 minutes and 15.8 % get under 30.** MARKET fills lose exactly 1 minute (the first-complete-successor
rule). Receipt: `ADVERSARIAL.json → clock_burn_LIMIT / clock_burn_MARKET`.

This is why every horizon result in §4 is reported **fill-anchored** as well as submission-anchored:
the submission-anchored clock confounds the exit horizon with the fill delay.

### 1.3 The walker, and why you can trust it

`lane2_receipts/walk.py` re-implements `resolve_post_submission_m1_lifecycle` as a vectorised
first-passage scan so that the horizon can be varied while everything else is held byte-fixed. It
reproduces every branch: the entry/exit quote transform (`quote_side.py:385-412`), the
first-complete-successor MARKET fill (`:1281-1289`), the favourable-open / intrabar-touch LIMIT fill
(`:1292-1330`), the invalid-gap guard (`:1344-1356`), the successor-open gap terminals, the
same-bar-both-touch censor, and the `LAST_COMPLETE_PRE_HORIZON_EXECUTABLE_EXIT_SIDE_CLOSE` mark.

**Fidelity, all five months** (`lane2_receipts/VALIDATE_1X.json`, `validate.py`):

| month | rows | exact status agreement | filled rows compared | max abs deviation on net R |
|---|---:|---:|---:|---:|
| feb | 121,302 | **1.000000** | 28,969 | **0.0** |
| apr | 124,284 | 0.995768 | 28,708 | **0.0** |
| may | 123,226 | **1.000000** | 27,118 | **0.0** |
| jun | 137,422 | 0.996289 | 32,925 | **0.0** |
| jul | 126,700 | 0.999953 | 29,016 | **0.0** |
| **all** | **632,934** | **0.998354** | **146,736** | **0.0** |

Every one of the 1,042 disagreements is a **month-boundary artifact in the favourable direction**:
the sealed run loads one calendar month of M1 and censors `CENSORED_SOURCE_INTERVAL_GAP` when it runs
off the end; this walker concatenates the month and its successor (`bridge_ftmo_m1_2026{02..07}`) and
resolves. Feb and May, whose windows end well inside their files, reproduce at **100.000000 %**.

**No filled row's terminal net R differs by more than 0.0.** The instrument is the sealed resolver.

**One declared deviation, used only beyond 1×.** The committed resolver censors on any M1 interval
gap. A 4× or 8× wall-clock horizon always crosses a session break, so at extended horizons this
walker treats a gap as unobserved time and keeps walking. At 1× the gap-censoring arm is the one
validated above; the tolerant arm is used only where the sealed one cannot answer by construction.

---

## 2. (A) The truncation census

### 2.1 Resolution mix — the whole corpus

`lane2_receipts/A_census.json`. 632,934 occurrences → 388,912 never fill (70.6 % of the LIMIT
population, exactly as `BARRIER_CLOCK_DEFECT_V1.md` §2.2 reported), 97,277 censor, **146,745 fill**.

| | n | TARGET | STOP | TIME_STOP |
|---|---:|---:|---:|---:|
| **all fills** | 146,745 | 20.95 % | 53.29 % | **25.76 %** |
| MARKET (7 families) | 74,249 | 19.66 % | 51.25 % | **29.08 %** |
| LIMIT (3 families) | 72,496 | 22.26 % | 55.39 % | **22.36 %** |

Per month the mix is **flat to within 1.8 pp** (TIME_STOP: feb 25.6, apr 26.7, may 26.7, jun 24.9,
jul 25.0). The June/July scoped read's 8/21 = 38 % time-stop share is **not** a June/July property —
it is a 21-trade draw from a 25.8 % population rate (binomial p = 0.13 two-sided). Do not read that
38 % as a signal.

### 2.2 Per family — the dispersion is enormous and it is a geometry fact

| family | fills | TARGET | STOP | **TIME_STOP** |
|---|---:|---:|---:|---:|
| `regime_transition_break` | 1,222 | 1.6 % | 11.0 % | **87.4 %** |
| `volatility_compression_expansion` | 2,419 | 1.3 % | 11.6 % | **87.1 %** |
| `session_open_range_break` | 4,785 | 7.0 % | 28.5 % | **64.5 %** |
| `current_ob_retest` | 7,603 | 11.8 % | 39.9 % | **48.3 %** |
| `displacement_continuation` | 20,737 | 12.4 % | 40.2 % | **47.4 %** |
| `current_breaker_re_entry` | 3,982 | 16.8 % | 47.9 % | 35.3 % |
| `liquidity_sweep_reclaim` | 23,049 | 22.2 % | 58.7 % | 19.1 % |
| `current_fvg_fill` | 60,911 | 23.9 % | 57.8 % | 18.3 % |
| `cross_asset_lead_lag` | 10,919 | 28.3 % | 62.7 % | 9.0 % |
| `structural_distance_extreme` | 11,118 | 31.0 % | 68.0 % | **1.0 %** |

An 87× spread in truncation rate across families under one shared 120-minute clock. §2.4 shows this
is almost entirely the d² law acting on different barrier widths — not ten different edges.

### 2.3 Time to target vs time to stop

At the unbounded horizon, over the 151,732-trade common population (`B_horizon.json`):

| | n | p25 | **median** | p75 | p90 | mean |
|---|---:|---:|---:|---:|---:|---:|
| time to **TARGET** | 48,367 | 15 min | **42 min** | 139 min | 458 min | 260.6 min |
| time to **STOP** | 103,358 | 6 min | **19 min** | 72 min | 259 min | 168.9 min |

**Ratio of medians: 2.21.** The target sits at 2.0 R and the stop at 1.0 R from the declared entry, so
under a d² law the expected ratio is (2.0/1.0)² × (correction for the fill price sitting at mean
a = 1.047, b = 1.953) ≈ **2.25**. Measured 2.21. Per family the ratio runs 1.53 – 2.53 with eight of
ten between 1.88 and 2.53.

**So the commission's mechanism is real: the winning side genuinely needs ~2.2× the time of the losing
side, and a fixed clock therefore truncates asymmetrically.** §3 measures what that asymmetry is worth.

### 2.4 The measured exponent

`lane2_receipts/fptx.py` → `FPT_EXPONENT.json`. One-sided first passage from the **fill price**,
measured over all 162,266 fills. Conditioning on which of two competing barriers won would bias this;
a one-sided ladder does not.

| d (R) | reach up | reach down | median T up | median T down | pooled median |
|---:|---:|---:|---:|---:|---:|
| 0.25 | 99.33 % | 99.57 % | 3 min | 1 min | 2 min |
| 0.50 | 98.78 % | 99.05 % | 12 | 6 | 9 |
| 0.75 | 98.12 % | 98.46 % | 27 | 17 | 22 |
| 1.00 | 97.54 % | 97.91 % | 47 | 34 | 40.5 |
| 1.50 | 96.28 % | 96.82 % | 104 | 84 | 94 |
| 2.00 | 95.00 % | 95.61 % | 180 | 152 | 166 |
| 3.00 | 92.67 % | 93.44 % | 364 | 328 | 346 |

**α = 2.087** (count-weighted log-log), **2.086** unweighted, **2.174** restricted to d ≤ 1 R where
≥ 97 % of trades reach the level so censoring bias is negligible. Theory: 2.000.

Per family: `cross_asset_lead_lag` 1.87, `liquidity_sweep_reclaim` 1.83, `structural_distance_extreme`
1.76, `volatility_compression_expansion` 1.66 (sub-diffusive — mean-reverting at short scales);
`current_ob_retest` 2.40, `current_breaker_re_entry` 2.37, `current_fvg_fill` 2.38 (super-diffusive —
these are the families whose entries cluster in quiet conditions).

**This is a load-bearing constant for the whole programme.** It says the horizon a contract needs
scales as the square of its barrier width, so every stop-width decision is implicitly a horizon
decision. §6 is the one place in this study where that bites.

---

## 3. (B) The counterfactual — what every time-stopped trade would have done

Same fills, same geometry, same costs; only `required_horizon_utc` moves. Because the LIMIT fill
depends on `entry` alone, **the fill population is identical in every arm by construction** — this is
not a matched-sample argument, it is the same 151,732 trades five times.

Intervals: cluster bootstrap over **100 trading days**, 2,000 draws, seed 20260812. Clustering is not
decoration — the corpus fires ~1,517 overlapping trades per day.

### 3.1 Pooled (submission-anchored, the sealed convention)

| horizon | TARGET | STOP | TIME_STOP | mean net R | median hold | Δ vs sealed [CI95] | p |
|---|---:|---:|---:|---:|---:|---|---:|
| **1× — 120 min (sealed)** | 31,179 | 79,349 | 41,204 | **−0.2326** | 22 min | — | — |
| 2× — 240 min | 39,207 | 91,271 | 21,254 | −0.2347 | 25 min | −0.0021 [−0.0063, +0.0019] | 0.308 |
| 4× — 480 min | 43,427 | 96,878 | 11,427 | −0.2350 | 25 min | −0.0025 [−0.0091, +0.0041] | 0.446 |
| 8× — 960 min | 45,541 | 99,796 | 6,395 | −0.2352 | 25 min | −0.0026 [−0.0107, +0.0048] | 0.498 |
| **unbounded** | 48,367 | 103,358 | 0 | −0.2377 | 26 min | **−0.0051 [−0.0145, +0.0050]** | 0.297 |

### 3.2 Fill-anchored, the clean instrument (`HZ_LADDER.json`)

Horizon measured from the fill, so the limit-rest confound of §1.2 is removed. **128× range:**

| horizon from fill | TARGET | STOP | TIME_STOP | mean net R | Δ vs 120 min | extra carry | net after carry |
|---|---:|---:|---:|---:|---:|---:|---:|
| 15 min | 12,913 | 46,456 | 92,363 | −0.2365 | −0.0039 | 0.0000 | −0.2365 |
| 30 min | 20,361 | 61,187 | 70,184 | −0.2332 | −0.0006 | 0.0000 | −0.2332 |
| **60 min** | 28,287 | 74,518 | 48,927 | **−0.2292** | **+0.0034** | 0.0000 | **−0.2292** |
| 120 min | 35,070 | 85,097 | 31,565 | −0.2326 | — | 0.0000 | −0.2326 |
| 240 min | 40,051 | 92,316 | 19,365 | −0.2337 | −0.0011 | 0.0018 | −0.2355 |
| 480 min | 43,695 | 97,298 | 10,739 | −0.2354 | −0.0028 | 0.0047 | −0.2401 |
| 960 min | 45,730 | 100,040 | 5,962 | −0.2348 | −0.0022 | 0.0063 | −0.2412 |
| 1,920 min | 46,945 | 101,479 | 3,308 | −0.2353 | −0.0027 | 0.0073 | −0.2426 |
| unbounded | 48,367 | 103,358 | 0 | −0.2377 | −0.0051 | 0.0154 | −0.2531 |

**Total span of the entire ladder: 0.0085 R/trade.** The best cell in nine, 60 minutes, beats the
sealed clock by **+0.0034 R/trade — 1.4 % of the 0.2377 R/trade the pool loses.**

Carry is priced, not assumed: broker rollovers are counted on the measured `New York + 7 h` clock
(`src/utils/broker_clock.py`) between fill and exit, charged at the corpus's own median per-crossing
swap (`swap_cost_r` median among the 19.9 % of rows the sealed 120-minute clock already charged). It
reaches **0.0154 R/trade at the unbounded horizon — three times the entire horizon effect, and
pointing the wrong way.**

> *Method note, so it is not read as more precise than it is:* the carry count and the
> `median_hold_min` / `r_per_hour` fields inside `HZ_LADDER.json` anchor the fill at
> `arms["15"].end − 15`, which is exact unless a barrier fired inside the first 15 minutes. Rollover
> counting is at daily granularity, so a ≤ 15-minute anchor error changes a night count only at a
> rollover boundary. The **mean net R and Δ columns above do not use that anchor at all** — they come
> straight from the walker's own `fill_min`. The two hold-derived fields are not cited anywhere in
> this document.

### 3.3 Per family, per month — no cell survives

Per family, best fill-anchored horizon vs the sealed 120 min (`HZ_LADDER.json → by_family`):

| family | n | best H | net @ best | net @ 120 | Δ [CI95] |
|---|---:|---:|---:|---:|---|
| `volatility_compression_expansion` | 2,813 | 30 min | −0.1081 | −0.1330 | +0.0248 [−0.0015, +0.0504] |
| `structural_distance_extreme` | 11,380 | 15 min | −0.5520 | −0.5689 | +0.0169 [−0.0021, +0.0377] |
| `current_breaker_re_entry` | 4,039 | 60 min | −0.1600 | −0.1696 | +0.0096 [−0.0298, +0.0506] |
| `current_fvg_fill` | 62,222 | 240 min | −0.1897 | −0.1970 | **+0.0073 [+0.0003, +0.0138]** |
| `cross_asset_lead_lag` | 11,354 | 60 min | −0.3214 | −0.3281 | +0.0067 [−0.0037, +0.0164] |
| `regime_transition_break` | 1,272 | 960 min | −0.0652 | −0.0706 | +0.0054 [−0.0466, +0.0634] |
| `current_ob_retest` | 7,673 | 1,920 min | −0.1189 | −0.1231 | +0.0042 [−0.0435, +0.0458] |
| `session_open_range_break` | 4,790 | 960 min | −0.0933 | −0.0970 | +0.0037 [−0.0369, +0.0495] |
| `displacement_continuation` | 22,027 | 60 min | −0.1421 | −0.1435 | +0.0015 [−0.0141, +0.0162] |
| `liquidity_sweep_reclaim` | 24,162 | 30 min | −0.2933 | −0.2948 | +0.0015 [−0.0157, +0.0203] |

**Honest multiplicity statement.** This lane searched **10 families × 9 fill-anchored horizons = 90
cells**, plus 10 families × 5 submission-anchored horizons = 50, plus 5 stop scales × 4 horizons = 20,
plus 5 short horizons and 5 selected-book horizons. **Total declared: 170 cells.** Exactly one has a
lower bound above zero — `current_fvg_fill @ 240 min`, +0.0073 [+0.0003, +0.0138] — an interval whose lower bound clears zero
by 0.0003, i.e. raw p ≈ 0.05. At 170 looks the Benjamini–Hochberg rank-1 bar is α/170 = 2.9 × 10⁻⁴.
**It does not survive, its point estimate is 3.7 % of that family's own loss, and it is not
proposed.**

Per month the delta is a coin flip: feb −0.0149 (p 0.110), apr +0.0024 (0.858), may −0.0053 (0.600),
jun −0.0070 (0.505), jul −0.0003 (0.925). Four of five negative, none significant.

---

## 4. (C) The MFE/MAE anatomy — the single most direct test, and it inverts the premise

The 41,204 trades the sealed clock time-stopped (`B_horizon.json → C_time_stop_anatomy`):

| | value |
|---|---:|
| mean **gross** R at the clock | **+0.2263** |
| mean **net** R at the clock | **+0.1403** |
| **total net** | **+5,781.1 R** |
| in profit gross at the clock | **60.68 %** |
| in profit **net** at the clock | **55.34 %** |
| MFE reached before the clock (median / mean) | **+0.723 R / +0.800 R** |
| MAE reached before the clock (median / mean) | **−0.480 R / −0.513 R** |

### 4.1 The finding that answers the owner's question

Decompose the pool's P&L by how each trade ended, at the sealed clock:

| bucket | n | mean net R | **total net R** |
|---|---:|---:|---:|
| TARGET | 31,179 | +1.7026 | **+53,084** |
| STOP | 79,349 | −1.1866 | **−94,156** |
| **TIME_STOP** | **41,204** | **+0.1403** | **+5,781** |
| **total** | **151,732** | **−0.2326** | **−35,291** |

**The time stop is the only positive bucket in the pool.** The losses are not in the timed-out trades;
they are in the 79,349 stop-outs, which lose 1.19 R each against 1.70 R per winner at a 2.4× frequency.

### 4.2 Is the clock exiting right before the move?

The exact test the commission asked for: track the same 41,204 trades past their exit.

| horizon | STOP | TARGET | still open | mean net R |
|---|---:|---:|---:|---:|
| at the clock (1×) | — | — | 41,204 | **+0.1403** |
| 2× | 11,922 | 8,028 | 21,254 | +0.1324 |
| 4× | 17,529 | 12,248 | 11,427 | +0.1312 |
| 8× | 20,447 | 14,362 | 6,395 | +0.1306 |
| unbounded | 24,009 | 17,188 | 7 | **+0.1216** |

**Δ = −0.0187 R/trade [−0.0527, +0.0166], p = 0.293.** Of the truncated trades eventually resolved,
**58.3 % stop out and 41.7 % reach target.** That 41.7 % is *better* than the geometry's own 34.9 %
unconditional fair-game bar — surviving 120 minutes without touching either barrier selects for
trades sitting mid-range — and it is **still not enough to beat banking the mark**, because the mark
was already at +0.226 R gross on average. There is no systematic favourable drift after the exit.
Per family the sign runs both ways and every interval contains zero
(`B_horizon.json → C_time_stop_anatomy`).

**The clock is not exiting right before the move. It is exiting on a coin flip and charging nothing
for it, which is exactly what optional stopping predicts.**

### 4.3 Adversarial check on this lane's own best-looking positive

The one cell that looked like a real find — `structural_distance_extreme` time-stops, +0.522 R/trade
from running them unbounded — **is refuted by its own receipt** (`ADVERSARIAL.json →
sde_timestop_cell`): n = 175 (1.5 % of the family), CI **[−0.898, +2.815]**, p = 0.672, and the sum is
+91.4 R of which the **top five trades alone contribute +141.6 R**. Remove those five and the cell is
**−50.3 R**. It is a five-trade artifact and it is not proposed.

The +0.1403 R/trade of the time-stopped cohort is also flagged honestly: **conditioning on "did not
resolve within 120 minutes" is a post-fill selection.** It is a true statement about where the pool's
P&L sits and a false one if read as an achievable ex-ante return. It cannot be harvested by selecting
for it, because the selection is only knowable after the fact.

---

## 5. Why we are actually losing — the decomposition

`lane2_receipts/decomp.py` → `DECOMP.json`. A driftless process started at the executable entry quote,
with barriers at −a and +b measured from that quote, hits the target first with probability
a/(a+b) and has **expected R exactly −s**, where `s = spread / stop_distance` is the corpus's own
`spread_r` (`src/costs/model.py:1334` — *"price / stop, one crossing"*). Crossing the spread moves the
**start**, not the barriers.

Measured geometry: mean a = **1.0469**, mean b = **1.9531**, target multiple exactly **2.0 R** on every
family, mean `spread_r` **0.1233**, mean deductible **0.1425**.

| | value |
|---|---:|
| break-even (fair-game) hit rate from the fill quote | **34.90 %** |
| fair-game hit rate **after** the spread handicap | **30.79 %** |
| **realised** hit rate, unbounded horizon (n = 151,725) | **31.88 %** |
| realised gross R/trade, unbounded | −0.0951 |
| fair-game gross R/trade with the spread | −0.1233 |
| **measured directional edge (gross + spread)** | **+0.0282**, CI95 [+0.0098, +0.0462] |
| slippage + swap + commission | −0.1425 |
| **net** | **−0.2377** |

**Cost 0.2659 R/trade against edge +0.0282 R/trade: a ratio of 9.4 to 1.**

This is an independent third measurement of the same quantity Lane G reached
(`E[gross + spread_r] = +0.0078 ± 0.0042` on 74,249 MARKET fills at the sealed horizon). This lane
gets **+0.0282, CI95 [+0.0098, +0.0462]** on 151,732 fills of both order types at the unbounded
horizon. Both are
small, positive and swamped; the difference is population and horizon, and neither rescues anything.

Per family the shortfall against the fair game runs **+2.17 pp** (`current_fvg_fill`) to **−2.00 pp**
(`volatility_compression_expansion`) — seven of ten families beat the driftless bar on hit rate and
all ten lose money. **The signals are informative; they are not informative enough to pay for the
trade.**

**One structural finding worth its own line.** `expected_slippage_r` is the constant **0.02** on all
632,934 rows — one unique value, zero variance. It is a placeholder, not a measurement, and it is
**the only cost term that does not shrink when the stop widens**, which makes it the binding floor of
§6. Any future cost work should replace it before anything else.

---

## 6. (D) The optimal-horizon surface, honestly bounded — and the lever that is 47× bigger

Since cost in R is a price quantity divided by the stop, widening the stop by k divides spread, swap
and commission by k. Since time-to-hit goes as d², a k-wide stop needs a k² horizon. `scale.py`
measures both at once, on the same 151,683 trades, with the target held at 2.0 R:

| stop k | horizon | TARGET | STOP | TIME_STOP | mean net R | median hold | Δ vs sealed [CI95] | p |
|---:|---|---:|---:|---:|---:|---:|---|---:|
| 1.0 | 120 min | 31,168 | 79,314 | 41,201 | −0.2325 | 22 min | — | — |
| 1.5 | 120 min | 22,843 | 63,170 | 65,670 | −0.1588 | 45 min | **+0.0737 [+0.0655, +0.0819]** | <0.001 |
| 1.5 | 270 min (d²) | 33,808 | 81,414 | 36,461 | −0.1628 | 58 min | +0.0696 [+0.0593, +0.0799] | <0.001 |
| 2.0 | 120 min | 16,763 | 50,586 | 84,334 | −0.1226 | 64 min | **+0.1098 [+0.0989, +0.1200]** | <0.001 |
| 2.0 | 480 min (d²) | 34,777 | 81,613 | 35,293 | −0.1248 | 103 min | +0.1077 [+0.0935, +0.1223] | <0.001 |
| 3.0 | 120 min | 9,067 | 33,289 | 109,327 | −0.0889 | 90 min | **+0.1435 [+0.1319, +0.1556]** | <0.001 |
| 3.0 | 1,080 min (d²) | 33,764 | 80,173 | 37,746 | −0.1033 | 228 min | +0.1291 [+0.1104, +0.1478] | <0.001 |
| **4.0** | **120 min** | 5,146 | 22,832 | 123,705 | **−0.0731** | 103 min | **+0.1594 [+0.1471, +0.1720]** | <0.001 |
| 4.0 | 1,920 min (d²) | 34,076 | 79,694 | 37,913 | −0.0808 | 370 min | +0.1517 [+0.1309, +0.1701] | <0.001 |
| 4.0 | unbounded | 48,463 | 101,772 | 0 | −0.0972 | 420 min | +0.1352 [+0.1125, +0.1566] | <0.001 |

**Three things this says.**

1. **Stop width is worth 47× the horizon.** +0.1594 vs +0.0034 R/trade, with an interval 25 standard
   errors from zero rather than straddling it. It independently reproduces `MAGNITUDE_PROGRAM_V1.md`
   §0 item 2 (+0.03 to +0.07 R/trade for 1.0 → 2.0 ATR) on a completely different corpus and a
   different instrument, and finds the same sign and a larger magnitude at larger k.
2. **The d²-matched horizon is *worse* than leaving the clock alone at every k.** −0.0040 at k=1.5,
   −0.0022 at k=2, −0.0144 at k=3, −0.0077 at k=4. The short clock becomes *more* protective as the
   stop widens, because a wider stop lets a losing trade travel further before the barrier catches it.
   **This is the one place the d² law changes a recommendation, and it changes it toward keeping the
   clock short, not lengthening it.**
3. **It is a cost effect, and it has a measurable ceiling.** `drift.py` → `DRIFT_SCALING.json`
   decomposes each k into fair-game (−s) plus edge:

| stop k | spread_r | deductible | fair gross (−s) | **measured edge** | edge CI95 | net |
|---:|---:|---:|---:|---:|---|---:|
| 1.0 | 0.1233 | 0.1425 | −0.1233 | **+0.0282** | [+0.0098, +0.0462] | −0.2376 |
| 1.5 | 0.0822 | 0.1017 | −0.0822 | +0.0129 | [−0.0046, +0.0298] | −0.1710 |
| 2.0 | 0.0616 | 0.0813 | −0.0616 | +0.0085 | [−0.0100, +0.0276] | −0.1344 |
| 3.0 | 0.0411 | 0.0608 | −0.0411 | **−0.0155** | [−0.0333, +0.0043] | −0.1175 |
| 4.0 | 0.0308 | 0.0506 | −0.0308 | **−0.0158** | [−0.0335, +0.0030] | −0.0972 |

**The edge does not scale with the stop — it decays and changes sign.** The pool's directional
information is a tight-geometry, short-horizon phenomenon. Meanwhile cost converges to the flat
0.02 R `expected_slippage_r` constant. **Limit as k → ∞: net → −0.02 + edge(∞) ≈ −0.036 R/trade.**

> **This is the honest bound and it is the most useful number in the lane: no stop width, and no
> horizon, makes this candidate pool positive. The best reachable cell in the entire 170-cell search
> is −0.073 R/trade.**

### 6.1 The price of a longer hold at the portfolio level

`sel.py` / `selboot.py` replay the sealed selector's symbol-blocking rule
(`w21_score_feb_market_top_r2.py:226-256`: a symbol is blocked while a selected trade is active) with
the month-boundary ridge prediction from the puzzle cache. **233 trades over 100 days** — an
approximation of the sealed 282, since the sealed reads use a *daily* prequential refit; treat the
level as indicative and the **paired day-by-day deltas** as the measurement.

| horizon | trades | total net R | R/day | mean hold | Δ vs 1× [CI95] | p |
|---|---:|---:|---:|---:|---|---:|
| **1× (sealed)** | 233 | **−10.42** | −0.127 | 65 min | — | — |
| 2× | 232 | −26.30 | −0.321 | 104 min | **−15.88 [−26.92, −5.19]** | **0.0015** |
| 4× | 231 | −31.70 | −0.387 | 160 min | **−21.28 [−40.17, −4.10]** | **0.0085** |
| 8× | 230 | −25.00 | −0.305 | 232 min | −14.58 [−39.03, +7.23] | 0.195 |
| unbounded | 222 | −21.95 | −0.268 | 491 min | −11.52 [−38.78, +16.19] | 0.394 |

Trade count barely moves (233 → 222): symbol blocking is not binding at these hold lengths, so the
turnover cost of a longer horizon is small. **The damage is per-trade, not per-slot.** Under BH over
these four comparisons the 2× and 4× harms survive at α = 0.05 (q = 0.006 and 0.017).

Shortening also fails on the deployable object (`SELECTED_BOOK_LEVERS.json`): 60 min −11.62 R,
30 min −19.62 R, 15 min −26.46 R. **The sealed 120-minute clock is the best of the five horizons
tested on the object that would actually trade.** It was chosen for the wrong reason and it happens
to be right.

---

## 7. (E) The constructive conclusion

### 7.1 The horizon change I would make: none

**Recommendation: leave `REPAIRED_PENDING_EXPIRY_MINUTES = 120` exactly where it is, and stop
treating the exit horizon as a candidate lever.** Worth, if changed to the pooled optimum (60 min
fill-anchored): **+0.0034 R/trade, CI [−0.0031, +0.0076]** — and on the selected book it is worth
**−1.19 R over five months.** Cost of the change: a machinery patch, a re-materialisation, and a
prereg amendment, against an effect 70× smaller than the loss it would be trying to fix.

**Two horizon repairs I *would* make, because they are defects rather than parameter choices, and
both are free:**

| repair | evidence | worth |
|---|---|---|
| **R1 — separate the two clocks.** Give `resolve_post_submission_m1_lifecycle` a `required_horizon_utc` measured **from the fill**, not from submission. | §1.2: 35.0 % of LIMIT fills currently get < 60 min of trade life and 15.8 % get < 30, purely because the order rested. | Economically ≈ 0 (**+0.0034 R/trade at best**), but it makes every future horizon measurement interpretable. Do it as hygiene, price it at zero. |
| **R2 — stop generating trades that are born expired.** The `min(asof + 120 min, day + 1 day)` clip at `v4_timewarp_simulated_live_research_loop.py:87938-87941` produces **5,619 rows with a zero-minute horizon, 100 % of which censor `CENSORED_GEOMETRY`**. Either extend past the day boundary or suppress the decision. | `ADVERSARIAL.json → zero_horizon_rows` | 0.89 % of the corpus, currently pure waste. No economic claim. |

### 7.2 The change that is worth something, and what it is worth

**Widen the stop and hold the target at 2.0 R.** At k = 2.0 with the clock unchanged:
**+0.1098 R/trade [+0.0989, +0.1200]**. At k = 4.0: **+0.1594 [+0.1471, +0.1720]**.

Translated to the funnel's own deployable cadence (233 selected trades over 107 calendar trading days
= **2.2/day, ~47/month**):

* pool-level: **−10.9 R/month → −3.4 R/month** at k = 4, i.e. **+7.5 R/month recovered**;
* on the 233-trade selected book the same arms are **+0.43 R (k=2) and −2.64 R (k=4)** over five
  months with CIs spanning ±25 R — **the selected book is far too small to resolve a 0.1 R/trade
  effect**, which is the same power problem `JUNJUL_READ_RESULT.md`'s power stamp records.

**And it does not reach break-even.** Ceiling ≈ **−0.036 R/trade** (§6). This is a *loss-reduction*
prescription, not an edge. **It does not justify arming anything**, and nothing in this lane changes
the standing verdict that the funnel is closed on measurement.

### 7.3 The one measurement that would prove this wrong

**Measure the edge term at k = 6 and k = 8 with the flat `expected_slippage_r = 0.02` replaced by a
measured, price-domain slippage model.**

The kill rests on two legs: (i) the edge decays with stop width (+0.0282 → −0.0158 over k = 1 → 4),
and (ii) cost floors at a flat 0.02 R that no stop width can divide. **Both are falsifiable and both
are cheap to falsify.**

* If the k=3/k=4 edge sign flip is an artifact of the M1 walker's gap tolerance at long holds rather
  than a property of the pool, the edge could stay near +0.028 at wide stops; net would then approach
  **+0.028 − 0.02 = +0.008 R/trade** and the pool becomes marginally viable at a wide stop.
  Its interval already contains zero at k = 3 and k = 4 ([−0.033, +0.004] and [−0.034, +0.003]) —
  **this leg is not established, it is only measured.**
* If `expected_slippage_r` is genuinely price-domain (it almost certainly is — it is a placeholder
  constant, not a measurement), the floor drops from 0.02 to 0.02/k and the ceiling moves from
  −0.036 to ≈ **−0.016 at k = 4** and toward 0 beyond. That is a **cost-model repair, not a research
  question**, and it is the single highest-leverage item this lane found outside its own mandate.

Run both on the four never-funnel-read 2025 windows already materialised in the hold
(june/august/september/december 2025) **only after** the slippage repair lands — and pre-register the
stop-width ladder, because §3.3 already spent 170 cells here.

---

## 8. Boundary — what this lane does NOT cover

**Nothing in this document touches armed money, and the estate's exit-frontier question is a
different object with a different answer.**

* This corpus is the **broad-origin funnel**, resolved by `resolve_post_submission_m1_lifecycle` over
  M1 with a 120-minute pending-order clock. `activation_or_live_authority: false` by every governing
  artifact's own terms.
* The **armed book** is the W7 sleeve estate (four sleeves both accounts, per
  `src.safety.armed_set.armed_sleeves()` — never prose). Its walker is
  `src/research_infra/walkforward/exits.py` `replay(bars, i, …)` over H4/D1 bars from the signal-bar
  close, and its horizon is `time_stop_bars` in **M15 printed bars** (`execution.py:8953-8958`), the
  field Session AQ repaired from `96` to `time_stop_m15(80, "D1")`. **None of this lane's arithmetic
  transfers to it.** Independently confirmed by `BARRIER_CLOCK_DEFECT_V1.md` §1.2-1.3: the estate
  lineage carries no order-type, limit, fill or marketability field at all.
* The estate's own exit-horizon question **has already been measured and answered differently**:
  AD's 1,631 gated exit cells over 25 sleeves found every sleeve improves (median **+0.249 R/day**),
  on 23 of 25 the best exit geometry beats eliminating carry entirely, and **the failing gate at all
  25 best cells is `significance`, not magnitude.** That is a live, unfinished question. This lane's
  null is about the funnel and says nothing about it.
* The June/July scoped-LSR read's **8 of 21 time-stops** is fully explained by §2.1 as a 21-trade draw
  from a 25.8 % population rate. It is not evidence of a truncation defect and should not be cited
  as one.

---

## 9. Receipts

`lane2_receipts/` — scripts are runnable in place from the scratch directory they were built in
(`/Users/borr/.claude/jobs/adb9e69b/tmp/lane2`); inputs are the sealed candidate roots at
`/Users/borr/GTOSActive/hermes-evidence-hold-20260727/{w21-tmp-lab-recovery-20260810,w21-junjul-r4-roots-20260812}`
and the true-UTC M1 archive under `/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805`.

| artifact | what it holds |
|---|---|
| `VALIDATE_1X.json` | the fidelity receipt — 632,934 rows, 99.835 % exact status agreement, **0.0** max deviation on 146,736 net-R values |
| `A_census.json` | the truncation census: horizons, statuses, per month / family / order type |
| `B_horizon.json` | submission-anchored 1×/2×/4×/8×/∞ counterfactual + the time-stop anatomy |
| `HZ_LADDER.json` | the fill-anchored 9-rung ladder with carry priced, per family |
| `SHORT_HORIZON.json` | the 15/30/60/120/240-minute submission-anchored arm |
| `SCALE_SURFACE.json` | the 5 × 4 stop-width × horizon surface |
| `DRIFT_SCALING.json` | edge vs cost at each stop width — the ceiling calculation |
| `DECOMP.json` | fair-game hit rate, spread handicap, per-family shortfall |
| `FPT_EXPONENT.json` | the one-sided first-passage ladder and α |
| `SELECTOR_TURNOVER.json`, `SELECTOR_BOOT.json`, `SELECTED_BOOK_LEVERS.json` | the deployable object under both levers |
| `ADVERSARIAL.json` | this lane's checks on its own positives, including the refuted SDE cell |

Scripts: `extract_geom.py`, `walk.py`, `validate.py`, `census_a.py`, `analysis.py`, `fpt.py`,
`fptx.py`, `decomp.py`, `drift.py`, `scale.py`, `scalean.py`, `hz.py`, `hzan.py`, `shorth.py`,
`sel.py`, `selboot.py`, `selfinal.py`, `adv.py`.
