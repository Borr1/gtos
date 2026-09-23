# B1 — THE LIMIT ARM, MEASURED

**Built 2026-08-11 (swarm 2, breakthrough lane 1). Read-only: no live path, no broker call, no config
byte, no `src/` edit, no git write.** Code and receipts: `swarm2/breakthrough/b1_limit_export/`
(`b1_export.py` → the LIMIT price-bearing export; `b1_slip.py` → the tick walk; `b1_agg.py`,
`b1_armdiff.py`, `b1_inwindow.py` → the restatements; `b1_control_a.py`, `b1_reweight.py` →
controls; `b1_entry_residual.py`, `b1_adversarial.py`, `b1_feasible_edge.py`,
`b1_feasibility_controls.py` → the adversarial passes; **`b1_concentration.py`,
`b1_implementable_rank.py` → the harvestability test that closes the branch**). Every number below
has a JSON receipt in the same directory, plus `B1_LEGS_{limit,ctrlB_lg_market}.csv.gz` = the 38,066
measured rows. Step state and the one-line answer are in `PROGRESS.json`.

---

## 0. THE ANSWER

> ### The LIMIT edge SURVIVES measured slippage at the pool level — and the branch closes anyway, because the surviving part is neither harvestable nor money.
>
> **Population: all resolved-filled LIMIT candidates, five sealed months, n = 72,496** (Lane 1's arm).
>
> | basis | edge raw | stop cond. | deduction | **edge at tick truth** | t | CI95 |
> |---|---:|---:|---:|---:|---:|---|
> | MARKET, measured (n = 74,249) | +0.00844 | 0.03932 | 0.02056 | **−0.01212** | −1.70 | [−0.0261, +0.0019] |
> | LIMIT, **transferred** (the adjudication) | +0.05383 | 0.03932 | 0.02209 | **+0.03174** | 2.49 | [+0.0068, +0.0567] |
> | **LIMIT, MEASURED (this lane)** | +0.05383 | **0.04547** | **0.02789** | **+0.02594** | **2.03** | **[+0.0008, +0.0510]** |
>
> **The transfer was optimistic.** The LIMIT arm's true stop-leg slippage is **1.157×** the MARKET
> value substituted for it and its time-stop leg **8.6×**; the deduction rises 26 %, t falls
> 2.49 → **2.03**, the CI lower bound +0.0068 → **+0.0008**. The falsification bar is not reached
> (0.04547 measured against a bar this lane recomputes at 0.04699 — see §6.3, where the
> adjudication's "2.9× headroom" is corrected to **1.03×**).
>
> ### Then the decomposition that closes the branch
>
> | population | n | share | edge raw | **edge at tick truth** | t |
> |---|---:|---:|---:|---:|---:|
> | all resolved-filled LIMIT | 72,496 | 100 % | +0.0538 | **+0.0259** | **2.03** |
> | **SCORED** — passes the cost gate, the estate can rank and route it | 43,574 | 60.1 % | +0.0322 | **+0.0050** | **0.32** |
> | **UNSCORED** — `cost_r > MAX_COST_R = 0.20`, 100 % of them | 28,922 | 39.9 % | +0.0865 | **+0.0575** | **2.74** |
>
> > **Every bit of the significance lives in candidates the estate's own eligibility gate rejects, and
> > those candidates lose 0.354 R each.** The unscored rows cost **0.4402 R** to trade and realise
> > **−0.3537 R** in absolute money. They beat their fair-value null because the null is −0.41; that is
> > a true statement about selection skill and a worthless one about money. **The half the estate can
> > actually route is +0.0050, t = 0.32 — indistinguishable from zero.**
>
> ### And no construction reaches it (the coordinator's decisive question)
>
> Ranking within decision window by the estate's own frozen ridge, **over every scored LIMIT candidate
> in the window — fills and non-fills alike, which is the only information a router has:**
>
> | construction | orders placed | fills | fill rate | **R per window** | total R | t |
> |---|---:|---:|---:|---:|---:|---:|
> | top-1 per window | 9,219 | 837 | 9.1 % | **−0.00476** | −43.9 | −0.82 |
> | top-3 | 27,268 | 2,162 | 7.9 % | −0.00711 | −65.5 | −0.63 |
> | top-5 | 45,159 | 3,463 | 7.7 % | −0.01373 | −126.6 | −0.95 |
> | top-10 | 89,641 | 7,035 | 7.8 % | −0.03213 | −296.2 | −1.33 |
> | **ALL (breadth)** | 338,903 | 43,574 | 12.9 % | **+0.02348** | +216.5 | **0.32** |
>
> **Selection is negative at every depth; breadth is the pool average and is not significant.** By
> decision-time rank the edge is not concentrated at the top — rank 1 is **−0.0525** and the only
> positive bucket is ranks 11–20 (+0.0451, t 1.83). **The answer to "concentrated or spread" is
> neither: it is unordered by the estate's scorer.**
>
> ### Reported against myself: the version of this that looked spectacular was look-ahead
>
> Ranking among **candidates that filled** gives a textbook monotone ladder — rank 1 **+0.1194,
> t = 5.07**, decaying through zero to −0.236 by rank 21+ — and it is an artifact of conditioning on
> fill. Recomputed over all scored candidates it vanishes (above). I found this by running the
> implementable version of my own positive result; §6.1 records a second finding I raised and refuted
> the same way.
>
> **Net: there is a real fair-value edge in the LIMIT pool, it does survive tick-truth slippage, and
> there is no construction within the estate's reach that converts it into money.** The branch closes
> cleanly. §7 lists what would have to change for it to reopen.

---

## 1. WHY THE LIMIT ARM HAD NO PRICES — the cause, cited

The adjudication (`RECON_SLIPPAGE_ADJUDICATION_V1.md` §3.1) could not measure the LIMIT arm because
its only price-bearing input, `/private/tmp/laneG-walk/lg_{month}.pkl.gz`, is 100 % MARKET
(74,249/74,249 verified). The cause is **one explicit filter in the generator**, and it is neither a
schema gap nor an unrun branch:

```python
# /private/tmp/laneG/laneg_walk.py:236   (inside run_month)
for raw in raws:
    if str(raw["origin_family"]) not in MARKET_FAMILIES:
        continue
```

with `MARKET_FAMILIES` declared at `laneg_walk.py:64-72` as the seven MARKET origin families. The
three LIMIT families (`current_fvg_fill`, `current_ob_retest`, `current_breaker_re_entry`,
`candidate_funnel_analysis.py:49-51`) are dropped before any resolve happens.

**The engine itself has no such gap.** `resolve_post_submission_m1_lifecycle` takes the occurrence's
native order type and implements the resting-LIMIT path in full:

| capability | `file:line` |
|---|---|
| accepts `MARKET` or `LIMIT`, rejects anything else | `src/research_infra/walkforward/quote_side.py:1058-1062` |
| correct-side touch rule for a resting LIMIT (BUY LIMIT eligible only when ASK ≤ level) | `quote_side.py:512-514`, `:454`, `:466-471` |
| LIMIT fill classification (`MARKETABLE_LIMIT_AT_FIRST_STRICTLY_CAUSAL_QUOTE` / `RESTING_LIMIT_AFTER_...`) | `quote_side.py:903-905` |
| LIMIT submission-bar ordering censor | `quote_side.py:1270-1274` |
| books the approved limit price on an intrabar correct-side touch | `quote_side.py:1340`, `:1471` |

**Why Lane G filtered them.** Its purpose was the MIRROR/INV benchmark, and it reconstructs the
fill-bar spread as `abs(fill_long − fill_short)` at a common fill time (`laneg_walk.py:180-185`).
That identity holds only for a MARKET fill (successor-bar open on the executable entry side); a
resting LIMIT and its mirror each fill at their own level, so the quantity is not a spread. The
filter was correct for Lane G's question and simply left this one unmeasured.

> **Verdict: a deliberate population filter at `laneg_walk.py:236`.** Removing it required no engine
> change of any kind — one line, and the arm walks.

### 1.1 The sealed inputs had to be relocated

`laneg_walk.py:78-88` reads the sealed generation roots from `/private/tmp/w21-market-top-{feb-r2,
aprmay-r3,junjul-r4}`. **All three have been reaped from `/private/tmp`.** The held originals are at
`/Users/borr/GTOSActive/hermes-evidence-hold-20260727/`:

| root | contents |
|---|---|
| `w21-junjul-r4-roots-20260812` | 42 days, 2026-06-01..07-28 — **the tick window lives entirely here** |
| `w21-aprmay-r3-roots-20260811` | April + May |
| `w21-tmp-lab-recovery-20260810/w21-market-top-feb-r2` | February |

Only **jun + jul** are needed, and §2.3 verifies that rather than assuming it.

---

## 2. CONTROLS — the two the commission required, and a third that matters more

### 2.1 Control A — export fidelity (`b1_control_a.py` → `B1_CONTROL_A.json`)

B1's exporter is Lane G's walk with the family filter parameterised and the `mirror`/`inv` arms
dropped (nothing downstream of the slippage measurement reads them). Re-walking the **MARKET** rows
must reproduce `lg_{jun,jul}.pkl.gz`.

| | jun | jul | total |
|---|---:|---:|---:|
| rows, Lane G / B1 | 18,268 / 18,268 | 16,245 / 16,245 | 34,513 / 34,513 |
| keys only in one side | 0 | 0 | **0** |
| rows differing on `state, status, gross, fill_price, fill_time, terminal_time, entry/stop/target/risk` | 0 | 0 | **0** |

> **EXACT.** Imports resolve against the same worktree Lane G used
> (`/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809`), so the engine bytes are
> identical too.

### 2.2 Control B — measurement fidelity (`b1_slip.py --src lg` → `head_ctrlB_lg_market.json`)

B1's tick walker against **Lane G's original artifact**, all five months:

| leg | adjudication | B1 | n |
|---|---:|---:|---:|
| entry fill | +0.00663 | **+0.00663** | 18,978 → **18,978** |
| stop exit | +0.03932 | **+0.03932** | 9,543 → **9,543** |
| target exit | −0.03968 | **−0.03968** | 3,435 → **3,435** |
| time-stop exit | +0.00141 | **+0.00141** | 5,482 → **5,482** |

Shape reproduces as well (stop median +0.01707, p95 +0.1412, p99 +0.3400, adverse 99.518 %; target
adverse 0.000 %), as does the population funnel (74,249 resolved → 18,978 in-window, STOP 9,866 /
TIME_STOP 5,482 / TARGET 3,630).

> **EXACT.** The two arms are comparable by construction: same exporter, same walker, same clock rule
> (`new_york_plus_7`, `src/utils/broker_clock.py:273`), same window, same sign convention.

### 2.3 Control C — the one that ties the halves together

The restatement subtracts a slippage **I** measured from an edge **Lane 1** measured. The booking
signature is the fingerprint that says both describe the same rows — and it was never checked.

| | Lane 1 (5 months, puzzle cache) | B1 (jun+jul, this export) |
|---|---|---|
| LIMIT STOP mean gross | −1.00100 | **−1.00037** |
| LIMIT STOP fraction exactly −1.0 | 97.31 % | **97.69 %** |
| LIMIT TARGET mean gross | +2.00131 | **+2.00117** |
| LIMIT TARGET fraction exactly +2.0 | 97.60 % | **97.74 %** |
| MARKET STOP mean gross / exact | −1.04443 / 2.11 % | −1.05600 / 2.32 % |

And the edge identity itself: recomputing `edge = terminal_gross_r + spread_r` from B1's own export
gives the jun+jul LIMIT edge **+0.0367327** against the puzzle cache's **+0.03673**, and the pooled
five-month edge **+0.030867** against Lane 1's **+0.030867** — exact
(`b1_feasible_edge.py`, `b1_inwindow.py`).

### 2.4 Only June and July can contribute — verified

The adjudication's 18,978 in-window MARKET rows decompose as **jul 12,388 / jun 6,590, and nothing
else.** No February, April or May row falls inside `2026-06-18..07-24`.

---

## 3. THE EXPORT AND THE MEASUREMENT

`b1_export.py --arm limit --months jun,jul` → **229,609 price-bearing LIMIT candidate records**
(jun 119,154 / jul 110,455), of which **30,841 resolve** and **19,088 have both fill and terminal
inside the tick window** (61.9 %). 23 symbols. Cluster bootstrap on trading day, 4,000 draws, seed
20260812.

Sign: **+ve = the engine's booked price is better than achievable = engine optimism = a real cost.**

| leg | n | mean | median | p95 | p99 | adverse | MARKET | ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **stop exit** | **11,100** | **+0.04547** | +0.02261 | +0.1507 | +0.3875 | **100.0 %** | +0.03932 | **1.157×** |
| target exit | 3,992 | −0.04043 | — | — | — | 0.0 % | −0.03968 | 1.019× |
| time-stop exit | 3,786 | **+0.01211** | — | — | — | — | +0.00141 | **8.62×** |
| entry fill *(do not quote — see §6.1)* | 19,088 | +0.02322 | 0.00000 | — | — | 49.2 % | +0.00663 | 3.50× |

Stability: **jun +0.04465 (n=4,132) / jul +0.04597 (n=6,968)** — no month carries it.

### 3.1 Where the LIMIT stop leg concentrates

**By family** — and this is the constructive result in the table:

| family | n stops | stop-leg slippage | Lane 1 edge |
|---|---:|---:|---:|
| `current_fvg_fill` | 9,997 | **0.04729** | +0.0545 |
| `current_ob_retest` | 735 | **0.02977** | +0.0490 |
| `current_breaker_re_entry` | 368 | **0.02753** | +0.0523 |

> **The dominant family is the expensive one.** `current_fvg_fill` is 84 % of the LIMIT arm and pays
> **1.6–1.7×** the slippage of the other two for a near-identical raw edge. §7 prices that.

**By symbol** (`B1_LIMIT_ARM_MEASURED_V1.json` → `LIMIT_stop_by_symbol`): worst BTCUSD 0.0746
(n=1,171), ETHUSD 0.0643, EURJPY 0.0563, UK100 0.0548, GER40 0.0515; cheapest XAGUSD 0.0109,
NZDUSD 0.0185, EURUSD 0.0208, USDCAD 0.0214.

---

## 4. THE RESTATEMENT

Deduction = `stop_conditional × pS + time_stop_conditional × pX`; target leg **0 by design** (a
resting TP limit fills at its level, 0.0 % of 3,992 target crossings adverse). Barrier shares are
each arm's own **five-month** shares, taken from the puzzle cache rather than from prose and matching
Lane 1 exactly (**LIMIT** 40,153 STOP / 16,136 TARGET / 16,207 TIME_STOP = 72,496; **MARKET**
38,054 / 14,601 / 21,594 = 74,249; `b1_reweight.py`). The family→order-type map is clean:
`LIMIT|LIMIT 72,496`, `MARKET|MARKET 74,249`, no cross terms.

| basis | edge raw | stop cond. | deduction | **edge at tick truth** | t | CI95 | sig |
|---|---:|---:|---:|---:|---:|---|:--:|
| MARKET, measured | +0.00844 | 0.03932 | 0.02056 | **−0.01212** | −1.70 | [−0.0261, +0.0019] | no |
| LIMIT, transferred | +0.05383 | 0.03932 | 0.02209 | **+0.03174** | 2.49 | [+0.0068, +0.0567] | yes |
| **LIMIT, MEASURED** | +0.05383 | **0.04547** | **0.02789** | **+0.02594** | **2.03** | **[+0.0008, +0.0510]** | **yes** |

*(The transferred row reproduces the adjudication's +0.03171 / t 2.49 to four decimals — a check on
the restatement arithmetic itself, not just on the inputs.)*

### 4.1 The arm difference — the statistic the rule actually turns on

The frozen rule is a *choice between arms*, not a bet on one arm's level, so the powerful statistic
is the day-paired difference, which cancels every common day effect (`b1_armdiff.py`; every row
charged its own barrier state's measured conditional).

| population | LIMIT | MARKET | **difference** | t | CI95 | sig |
|---|---:|---:|---:|---:|---|:--:|
| five months, 100 days | +0.02594 | −0.01212 | **+0.03805** | **2.43** | [+0.0078, +0.0692] | **yes** |
| jun+jul only, 42 days | +0.00843 | −0.01994 | +0.02836 | 1.30 | [−0.0133, +0.0727] | no |

Per month: feb +0.0215 (t 0.59) · **apr +0.0865 (t 2.37, the only significant one)** · may +0.0285
(t 0.69) · jun +0.0353 (t 1.12) · jul +0.0205 (t 0.70). **All five positive.**

---

## 4bis. IS THE EDGE HARVESTABLE? — concentrated at the top, or spread?

A sibling lane established that `P(fill) × E[net|fill]` composition is refuted as a funnel repair
(−76.14 R on 1,151 trades) and that the shipped book's +0.954 R is a **non-transacting** result —
81.4 % of argmaxes never fill. So argmax-with-abstain provably cannot harvest this pool, and the open
question is whether *any* construction can. That reduces to one measurement: **is the LIMIT edge
concentrated at the top of the book (selection harvests it) or spread across it (only breadth
does)?**

**Populations, stated precisely, because two apparent contradictions today were population
mismatches:**

| tag | definition | n |
|---|---|---:|
| **P0** | all candidates, five sealed months | 632,934 |
| **P1-L** | resolved-filled LIMIT — *Lane 1's arm, and §0's headline* | 72,496 |
| **P2-L** | P1-L **carrying a ridge score** (`pred_month_boundary` ≠ None) — the routable subset | 43,574 |
| **P3-L** | all **scored** LIMIT candidates including non-fills — what a router sees at decision time | 338,903 |
| **P1-M** | resolved-filled MARKET | 74,249 |

### 4bis.1 By decision-time rank (P3-L placed, P2-L read) — the implementable statistic

`b1_implementable_rank.py`. Rank is over every scored LIMIT candidate in the window, so it uses only
decision-time information.

| within-window rank | candidates | filled | fill rate | edge at tick truth | t | CI95 |
|---|---:|---:|---:|---:|---:|---|
| 1 | 9,219 | 837 | 9.1 % | **−0.0525** | −0.81 | [−0.1808, +0.0717] |
| 2 | 9,059 | 655 | 7.2 % | +0.0218 | 0.34 | [−0.1025, +0.1445] |
| 3 | 8,990 | 670 | 7.5 % | −0.0536 | −0.90 | [−0.1680, +0.0646] |
| 4–5 | 17,891 | 1,301 | 7.3 % | −0.0469 | −0.99 | [−0.1390, +0.0495] |
| 6–10 | 44,482 | 3,572 | 8.0 % | −0.0475 | −1.27 | [−0.1216, +0.0253] |
| 11–20 | 87,104 | 8,862 | 10.2 % | +0.0451 | 1.83 | [−0.0022, +0.0943] |
| 21+ | 162,158 | 27,677 | 17.1 % | +0.0041 | 0.21 | [−0.0333, +0.0414] |

**No ordering.** The top of the book is negative; the one near-positive bucket is ranks 11–20. Note
the fill rate *rises* down the book (9.1 % → 17.1 %) — the P(fill) confound the sibling lane
identified, visible here from the other side. Top-1 by month is unstable in sign (apr −0.194,
feb +0.070, jul −0.176, jun −0.139, may +0.353) and leave-one-month-out is negative in four of five.

### 4bis.2 By absolute score decile (P2-L) — also flat

Spearman(decile, edge) **+0.164**; top decile +0.0241 vs bottom +0.0071; the day-clustered
top-minus-bottom test gives **+0.0170, t = 0.34, CI [−0.0773, +0.1182]**. The ridge has no absolute
ordering skill on this arm either — the same shape wave 21 found for the debate-engine score
(outcome-uninformative, AUC 0.4960).

### 4bis.3 The look-ahead version, and why I am not reporting it as a result

Ranking among **candidates that filled** (`b1_concentration.py`) produces exactly the ladder a
harvestable edge would produce:

| rank among fills | n | edge at tick truth | t |
|---|---:|---:|---:|
| 1 | 7,986 | **+0.1194** | **5.07** |
| 2 | 7,151 | +0.0557 | 2.24 |
| 3 | 6,156 | +0.0179 | 0.73 |
| 6–10 | 10,166 | −0.0905 | −3.76 |
| 11–20 | 2,584 | −0.1467 | −2.99 |

Monotone, 5σ at the top, and **unusable**: at decision time you do not know which candidate will
fill, and conditioning the rank on fill is the selection itself. Recomputed over all scored
candidates (§4bis.1) it disappears. **This is the single most attractive number this lane produced and
it is an artifact.**

### 4bis.4 Where the edge actually lives, and why it is not money

| population | n | mean `cost_r` | share with `cost_r > 0.20` | mean **realised net** | edge at tick truth | t |
|---|---:|---:|---:|---:|---:|---:|
| **P2-L** scored / routable | 43,574 | 0.1146 | 0.0 % | −0.0825 | **+0.0050** | 0.32 |
| **unscored** (P1-L − P2-L) | 28,922 | **0.4402** | **100.0 %** | **−0.3537** | **+0.0575** | **2.74** |

The unscored rows are exactly those the eligibility gate rejects — `if row["cost_r"] > MAX_COST_R:
continue`, `MAX_COST_R = 0.20` (`candidate_funnel_analysis.py:263`, `:52`); their
`cost_label_status` is `COMPLETE` for all 28,922, so this is the cost gate and not a data defect.

> **The fair-value null is cost-adjusted by construction, so beating it says nothing about money.**
> These candidates carry a −0.41 null and realise −0.354; that is a +0.058 edge and a 0.354 R loss per
> trade. **The estate's cost gate is already doing the right thing with them, and the significance in
> §0's headline is a property of the rows the gate throws away.**

---

## 5. IS THE 5-WEEK WINDOW ENOUGH TO SETTLE THE 5-MONTH CLAIM?

**For the slippage constant: yes.** 11,100 crossings, CI [+0.0414, +0.0502] — a ±9.5 % band; stable
across both months; and the two compositions that could bias it are measured and do not:

| composition risk | test | result |
|---|---|---|
| symbol mix of the window ≠ of the population | reweight the measured per-symbol conditional onto the five-month symbol mix (`b1_reweight.py`) | LIMIT 0.04547 → **0.04494** (−0.0005); MARKET 0.03932 → **0.03936** (+0.00004). **Immaterial.** |
| barrier mix of the window ≠ of the population | in-window LIMIT stop share 0.586 vs five-month 0.554 | real (Δ 0.032) — and **removed by construction**, since the deduction uses the five-month shares |
| the engine's LIMIT `fill_time` is bar-shifted (§6.1) | re-measure with the exit scan starting 60 s earlier | stop conditional 0.04547 → **0.04391** (−3.4 %), same 11,100 crossings. Moves the answer *in favour*. |

**For the edge, and therefore for the arm split: no — and the gap is not the window length, it is
which months the window covers.** The tick archive covers jun and jul, which are the LIMIT arm's
**two weakest months** (+0.0414, +0.0314) while April (+0.1024) carries the result and is unmeasured.
On the covered months alone the arm difference is not significant (t 1.30). The five-month
restatement is still the better *estimator* — execution cost is a physical quantity that moves 3 %
between the two measured months while edge moves 3× — but it is an extrapolation of cost onto three
months of unmeasured execution regime, and that is now the load-bearing assumption.

---

## 6. ADVERSARIAL — what I found against my own result

### 6.1 A finding I raised and then refuted on its own control

My first pass compared the booked LIMIT level against the true quote **at the booked fill instant**
and found **23.1 %** of LIMIT fills unsupported by the tape, with the unsupported rows carrying a
+0.66 R edge gap — which would have been the story of this lane. **It is largely an artifact of my
own window alignment, and the tape says so** (`b1_feasibility_controls.py`, C1):

| tick search window around `fill_time` | fraction of fills the tape supports |
|---|---:|
| `[0 s, 60 s)` — the booked M1 bar | 76.9 % |
| `[0 s, 120 s)` | 82.2 % |
| **`[−60 s, 120 s)`** | **97.3 %** |
| `[−60 s, 300 s)` | 98.0 % |
| `[−300 s, 600 s)` | **98.6 %** |

The jump on adding the *preceding* minute identifies the cause: for a resting LIMIT the engine's
`modelled_fill_time_utc` is bar-shifted relative to the intrabar touch, so the touch sits in the bar
before the one I searched. **Retracted: there is no 23 % phantom-fill population.** (This also means
the LIMIT **entry-leg** figure in §3 is measured at the wrong instant and must not be quoted — at a
−60 s offset it reads 0.447 R, which is nonsense in the other direction. The entry leg does not enter
the deduction, so nothing above depends on it.)

### 6.2 What survives that retraction — and it is still adverse

Under the **widest** search window, **1.44 % (n = 275)** of fills remain unsupported, and they are
extraordinary: **edge +0.786 R against −0.012 R** for the other 98.6 %. Density stratification says
this is not archive sparsity — in the densest 20 % of fill minutes (median **374 ticks**, where a
missed touch is essentially impossible) the phantom rate is still 16.9 % on the narrow window and the
supported/phantom edge gap is **+0.872 R**, the *largest* of any decile. The mechanism is visible in
the barrier mix: phantom rows end at TARGET **46.7 %** of the time against **20.1 %** for supported
rows — a fill granted at a price the market never offered is a free head start toward the target.

**Sensitivity:** those rows contribute **+0.0115 R/trade** of raw edge. If the same rate and effect
hold across the five months, the restated LIMIT edge falls to **+0.0144, t = 1.13 — not
significant.**

The root cause is measurable and is an engine defect, not a data defect: the LIMIT touch test decides
on a **modelled** ask (bid bar + modelled spread), and on this arm the modelled spread is **31 %
light** (0.1022 vs 0.1336 true; `b1_entry_residual.py`) against 8.8 % light on MARKET.

### 6.3 The headroom claim in the adjudication does not hold

> "The LIMIT edge would have to absorb a stop-leg slippage of **0.1150 R/stop — 2.9×** the measured
> MARKET value — before its CI touches zero." (`RECON_SLIPPAGE_ADJUDICATION_V1.md` §4.1)

Reproducing that arithmetic from its own inputs (raw edge 0.05383, se 0.01273, pS 0.55387, MARKET
time-stop conditional 0.00141):

| bound | required stop conditional | ratio to 0.03932 |
|---|---:|---:|
| **CI95 lower bound = 0** | **0.05156** | **1.31×** |
| point estimate = 0 | 0.09662 | 2.46× |

0.1150 matches neither. It is nearest the *point-estimate* bound — a materially weaker claim than
"before its CI touches zero". **On the measured basis the CI-touches-zero bar is 0.04699 against a
measured 0.04547 — 1.03× headroom.** A 3.3 % increase in the true stop conditional ends the
significance; so does simply using the in-window barrier mix (pS 0.586) instead of the five-month one
(t → 1.94).

### 6.4 The 1.157× is order type, not instrument mix

The LIMIT arm trades a different, crypto/index-heavy universe, so the pooled gap could have been pure
composition. Reweighting says the opposite (`b1_adversarial.py` TEST 1):

| | stop conditional |
|---|---:|
| LIMIT at its own symbol mix | 0.04547 |
| MARKET at its own symbol mix | 0.03932 |
| **MARKET reweighted to LIMIT's symbol mix** | **0.03709** |
| LIMIT reweighted to MARKET's symbol mix | 0.03535 |

At matched mix the gap **widens** (0.00838 vs 0.00616): the LIMIT arm trades instruments that are
intrinsically *cheaper* to stop out of, and is still worse on them. In the top-10 LIMIT symbols
(94.8 % of its stops) **8 of 10** are worse for LIMIT, median ratio **1.284**. The plausible mechanism
is mechanical: a resting limit fills on momentum *into* its level, and a stop placed beyond that level
is then hit inside the same fast move.

### 6.5 The entry leg does not threaten the result either way

The adjudication declined to charge the entry leg, arguing it cancels against the spread model. That
was measured on MARKET and never tested on LIMIT. Charging it honestly — the exact algebra is
`correction = −entry_opt_r + (spread_r_true − spread_r_model)` — gives **+0.00640** on MARKET
[+0.0049, +0.0080] and **+0.00825** on LIMIT [−0.0064, +0.0233]. **Positive on both**: the model
understates the spread by more than it overstates the fill. So the adjudication's *decision* was
conservative even though its *reason* ("it cancels") is not exactly right — the correction is not
zero, it is favourable. Charging the entry leg naively **without** the offsetting null correction
would take LIMIT to +0.0027 and is the one convention that must not be used.

### 6.6 No single LIMIT family stands on its own

| family | n | edge raw | deduction | edge at tick truth | t | CI95 |
|---|---:|---:|---:|---:|---:|---|
| `current_ob_retest` | 7,603 | +0.04899 | 0.01468 | **+0.03431** | 1.13 | [−0.0248, +0.0941] |
| `current_breaker_re_entry` | 3,982 | +0.05233 | 0.02064 | **+0.03169** | 0.78 | [−0.0491, +0.1087] |
| `current_fvg_fill` | 60,911 | +0.05453 | 0.02970 | **+0.02484** | 1.76 | [−0.0023, +0.0534] |

**None is individually significant**, and this is before any multiplicity charge. The arm result is a
pooled result; it should not be quoted as three findings.

---

## 7. WHAT SURVIVES, AND WHAT WOULD REOPEN THE BRANCH

**The branch closes on the harvestability measurement, not on the slippage measurement.** The
slippage question came back the way the adjudication guessed — LIMIT is worse than MARKET but nowhere
near the falsification bar — and the arm split at pool level is real. What kills it is that the
significant part is cost-gate-rejected and the routable part is t = 0.32, with no ordering the estate's
scorer can exploit.

**Still worth doing, independent of this branch:**

1. **Charge slippage barrier-conditionally instead of flat.** The measured structure is the
   prescription: **0.0455 on a LIMIT stop, 0.0393 on a MARKET stop, 0.0121 / 0.0014 on a time stop,
   0.0000 on a target.** No new data. The flat 0.02 taxes the ~21 % of trades ending at target for a
   cost of exactly zero and under-charges every stop — and it is 10 % of the 0.20 eligibility budget
   that §4bis.4 shows is doing real work.
2. **Repair the LIMIT touch test.** It triggers on a modelled ask that is **31 % light** on this arm
   (0.1022 vs 0.1336 true) against 8.8 % on MARKET, which manufactures the §6.2 rows. This is the only
   item here that changes what the engine *does* rather than what it reports, it has a measured
   target, and it makes the arm honest in either direction.
3. **Do not spend a tick capture on Feb/Apr/May for this question.** It was the natural next
   measurement while the arm split looked live (§5), and §4bis has since made it moot: better cost
   measurement cannot rescue a pool whose routable half has no edge and whose orderable structure is
   absent. Spend it only if item 2 changes the population.

**What would reopen the branch** — each is a specific, falsifiable measurement:

| reopener | what it would have to show |
|---|---|
| a **different scorer** | the ridge is what fails here, not necessarily the pool. Any scorer with genuine within-window ordering skill on P3-L — measured at decision-time rank, not among fills — reopens §4bis.1. The bar is a top-k slice with a positive per-window R. |
| the **cost gate is mispriced** | §4bis.4 rests on `cost_r` being right for the rejected rows. Those rows carry a modelled cost of 0.4402; a tape measurement showing true cost materially below that would move rows back into the routable pool with their +0.0575 edge attached. This is the one place a Feb/Apr/May tick capture would still pay. |
| **execution at better geometry** | the rejected rows lose 0.354 R because friction is 0.44 R. Lane 1's counterfactual-geometry result is the relevant instrument: if the edge is fixed in R while cost is fixed in price, widening makes the same candidates affordable. That is a geometry question, not a selection one. |
| **family-selective admission** | `current_ob_retest` and `current_breaker_re_entry` pay **0.0298 / 0.0275** stop slippage against `current_fvg_fill`'s **0.0473** for the same raw edge. Neither is individually significant (§6.6) and both are small, but they are the cheapest-to-execute corner of the arm and were never separated. |

---

## 8. WHAT WOULD REVERSE EACH FINDING HERE

| finding | the measurement that reverses it | nearest unrefuted variant |
|---|---|---|
| **the branch closes: no construction harvests it (§4bis)** | a scorer with within-window ordering skill on P3-L at **decision-time** rank, showing a top-k slice with positive per-window R; or a tape measurement putting the rejected rows' true cost well below their modelled 0.4402 | the ridge's **rank 11–20** bucket is the only non-negative one (+0.0451, t 1.83) — unexplained, thin, and the single place an ordering story could still live |
| **the significance is cost-gate-rejected (§4bis.4)** | `cost_r` being materially wrong for the 28,922 unscored rows; their modelled cost is 0.4402 and their `cost_label_status` is COMPLETE for all of them | widening geometry so the same candidates become affordable — a geometry question, priced by Lane 1's counterfactual walk, not a selection one |
| LIMIT survives at +0.0259, t 2.03 (§4) | a true stop conditional **3.3 % higher** (0.04699), or the five-month phantom rate matching §6.2's 1.44 %, or Feb/Apr/May execution being worse than jun/jul | the **arm difference** (+0.0381, t 2.43) — but note §4bis makes this a statement about a pool, not about a tradeable book |
| the look-ahead ladder (+0.1194 at rank 1, t 5.07) | **already reversed, by me**, by recomputing the rank over all scored candidates rather than over fills | — |
| the arm difference is significant (§4.1) | it is not significant on jun+jul alone (t 1.30) — a tick capture for Feb/Apr/May could confirm or kill it | it is **positive in all five months**; no month contradicts it |
| the 1.157× is order type, not mix (§6.4) | a symbol-level confound correlated with both arm and slippage that survives reweighting | reported at matched mix, where the gap is *larger* |
| 1.44 % phantom fills (§6.2) | n = 275. A tick-archive completeness audit showing those minutes are under-sampled — though the densest-decile control argues against it | treat it as a **bound** (−0.0115 R/trade), not a point estimate |
| my own 23 % phantom claim (§6.1) | **already reversed, by me, on the timing control** | the 1.44 % residual under the widest window |
| the adjudication's 2.9× headroom (§6.3) | an SE larger than Lane 1's day-clustered 0.01270 would widen the bar | stated both ways: 1.31× on its basis, 1.03× on the measured one |

---

## 9. PROVENANCE

- **Population**: sealed generation roots
  `/Users/borr/GTOSActive/hermes-evidence-hold-20260727/w21-junjul-r4-roots-20260812` (jun+jul, 42
  days), M1 sources from `lane-inputs-true-utc-hold-20260805/.hermes/.../manifests`, engine tree
  `worktrees/wave21-full-system-coherence-20260809` (the one Lane G walked).
- **Ticks**: `/Users/borr/GTOSActive/vps-ticks-20260726/ftmo/`, 23 symbols, `2026-06-18..07-24`,
  broker→UTC by `new_york_plus_7` (`src/utils/broker_clock.py:273`).
- **Edge ladder**: `LANE_1_FAIR_VALUE_NULL_V1.md` §1.2–1.3 / `LANE1_SUMMARY_V1.json`, independently
  reproduced here from the puzzle cache (pooled +0.030867, LIMIT +0.05383, MARKET +0.00844 — exact).
- **Barrier shares**: recomputed from `/private/tmp/w21-puzzle-cache/rows_*.pkl.gz`, not quoted from
  prose.
- **CIs**: 4,000-draw cluster bootstraps on `trading_day`, seed 20260812, throughout. The arm-difference
  bootstrap resamples whole days and treats the measured conditionals as fixed; their own SE
  (0.0016 on the deduction) is small against the 0.0157 SE of the difference.
- **Ranking score**: `pred_month_boundary`, the frozen prequential ridge's out-of-sample prediction
  written at each month boundary by `puzzle_build_cache.py`. Present on 43,574 of 72,496 resolved
  LIMIT rows; absence is the `MAX_COST_R = 0.20` eligibility gate, verified (100 % of unscored rows
  exceed it, `cost_label_status` COMPLETE on all).
- **Non-fill IS priced** in §4bis.1's per-window table: orders that never execute contribute exactly
  zero R and are counted in the denominator (338,903 placed, 43,574 filled, 12.9 %). Per-fill figures
  elsewhere do not price it and are labelled as conditional on fill.
- **Not addressed here**: multiplicity across the arms, families, rank buckets and constructions
  examined — this lane reports raw t and CI throughout and applies no family-wise correction, so no
  number in it clears an admission standard; and the LIMIT arm's 55.3 % censoring rate, which Lane 1
  §2.4 covers and this lane inherits unchanged.
- **Confers no arming, sizing, promotion or activation authority.** Read-only throughout: no live
  path, no broker call, no config byte, no `src/` edit, no git write.
