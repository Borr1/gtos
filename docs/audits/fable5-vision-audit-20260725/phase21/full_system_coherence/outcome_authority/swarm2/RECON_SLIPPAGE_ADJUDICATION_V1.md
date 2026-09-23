# RECONCILIATION — THE SLIPPAGE CONSTANT, ADJUDICATED

**Built 2026-08-11 (swarm 2 reconciliation lane). Read-only: no live path, no broker call, no config
byte, no `src/` edit, no git write.** Receipts: `swarm2/recon_slippage_receipts/`
(`RECON_SLIPPAGE_TRUTH_V1.json`, `RECON_LEGS_V1.csv.gz` = the 18,978 measured rows,
`recon_slip.py` + `recon_agg.py` = every number here).

---

## 0. THE ADJUDICATION

> ### The estate's flat `expected_slippage_r = 0.02` is CORRECT to within 4 %.
>
> Measured from ticks against the sealed labeller's own bookings, the exit-leg slippage the constant
> is meant to cover is **+0.02085 R per resolved trade** in-window, **+0.02132 R** re-weighted to the
> pooled five-month barrier mix. Charged: 0.02000.
>
> **The three lanes did not measure the same quantity, and none of them measured the one the constant
> is compared against.** Put on one basis they compose rather than conflict:
>
> | leg | conditional | share | per resolved trade | n | CI95 |
> |---|---:|---:|---:|---:|---|
> | entry fill | +0.00663 | 1.000 | **+0.00663** | 18,978 | [+0.0047, +0.0084] |
> | **stop exit** | **+0.03932** | 0.5199 | **+0.02044** | 9,543 | [+0.0364, +0.0431] |
> | target exit | −0.03968 | 0.1913 | **0.00000** (correct by design) | 3,435 | [−0.0427, −0.0369] |
> | time-stop exit | +0.00141 | 0.2889 | **+0.00041** | 5,482 | [−0.0001, +0.0029] |
> | **round-trip total** | | | **+0.02748** | 18,978 | |
> | **exit-only (what the constant covers)** | | | **+0.02085** | | |
>
> **Lane 6 is overturned** (its 0.0057 is an *entry-leg* figure in *inverted* risk units — 0.0114 in
> the estate's own units; the true ratio is 1.75×, not 3.5×, and the 2× is a unit error).
> **Lane 7 is overturned** (85 % of its 0.0317 is a `stop_bar_idx == 0` artifact).
> **Lane 1 is upheld** — I reproduce its stop leg to five decimals independently — **but its own
> receipt contradicts its own report**, and the report is the correct one.
>
> ### Lane 1's edge does NOT survive as significant — pooled. It survives on the LIMIT arm.
>
> | arm | edge (engine accounting) | deduction | **edge at tick truth** | t | CI95 |
> |---|---:|---:|---:|---:|---|
> | POOLED | +0.03087 | 0.02132 | **+0.00955** | 1.42 | [−0.0036, +0.0228] |
> | **LIMIT** | +0.05380 | 0.02209 | **+0.03171** | **2.49** | **[+0.0067, +0.0567]** |
> | MARKET | +0.00840 | 0.02056 | **−0.01216** | −1.70 | [−0.0262, +0.0019] |
>
> **The estate's frozen rule trades MARKET and abstains on LIMIT. At tick truth the arm it trades has
> a negative edge and the arm it excludes is the only one that survives.** That is the constructive
> finding, and it costs no validation currency to act on — it is a re-scoring of sealed data.

---

## 1. (A) WHAT EACH LANE ACTUALLY MEASURED

Three numbers, three quantities, one name. Precise definitions, taken from the scripts and receipts
rather than the prose.

| | Lane 6 → 0.0057 | Lane 7 → 0.0317 | Lane 1 → 0.0393 |
|---|---|---|---|
| **leg** | **ENTRY** | STOP exit | STOP exit |
| **conditioning** | reconciled live broker entries | conditional on a stop, *minute-open gap only* | conditional on a stop, first crossing tick |
| **risk unit** | **INVERTED (2× the original stop distance)** | original | original |
| **population** | armed estate's own live fills, **n = 138 rows**, 15 of 24 symbols, n = 1–11 per symbol | Lane 7's **own synthetic tick re-walk**, 11,370 stops | **sealed labeller's own STOP rows**, 9,526 |
| **window** | 2026-06/07 live | 2026-06-18..07-24 | 2026-06-18..07-24 |
| **includes spread?** | no (adverse fill beyond the quote) | no | no |
| **per-trade equivalent** | ≈ 0.0114 orig units, entry leg | 0.0317/fill (claimed) | 0.0214/resolved trade (report) |

### 1.1 Lane 6 — a unit error of exactly 2×, and the source says so itself

A15's 0.0057 comes from `phase21/cost/SLIPPAGE_PRICE_V1.json` via
`PHASE0_INVERSION_TRUTH_V1.md:356-361`, which states its own units plainly:

> "Candidate-weighted over the 15 surface symbols it covers: **0.0057 R in inverted units**"

The inverted contract's risk unit is **2× the original stop distance**, so a fixed price cost is worth
**half** as many inverted R as original R. `P0_T1_COST.json` carries both columns for every family and
they are exactly 2:1 — e.g. `cross_asset_lead_lag`: `eligible_spread_r_inverted_units` 0.037682,
`eligible_spread_r_orig_units` 0.075364. **Verified on all seven families.**

So `0.0057 inverted ≡ 0.0114 original`. And **the source document states the correct comparison one
paragraph later** (`:374-377`):

> "The walk already charges **0.010 R in inverted units** for slippage (the flat 0.02 R original-unit
> constant)"

0.010 vs 0.0057 in inverted units is **1.75×**. Lane 6 took the *other* sentence in the same section
(`:362-365`, "**3.5×** the broker-reconciled figure"), which compares an original-unit constant against
an inverted-unit measurement. **That sentence in `PHASE0_INVERSION_TRUTH_V1.md` is the divergence
line, and it is wrong by exactly the 2× unit factor.**

Two further reasons the number cannot carry the load Lane 6 put on it, independent of units:

1. **It is the ENTRY leg.** 96 % of true slippage is on the stop exit (§3). An entry-fill statistic is
   silent about it.
2. **n = 138 rows over 15 of 24 symbols at n = 1–11 per symbol**, and the source labels it
   **"TRANSFERRED, not measured"** for this population (`:359-361`).

**Lane 6's report is not present in `swarm2/`** (files there are LANE_1, LANE_3, LANE_4, LANE_7; there
is no `lane6_receipts/`). This adjudication is therefore against the cited source and the arithmetic
as reported in the commission, not against a document I could read.

### 1.2 Lane 7 — 85 % of its number is the entry minute, not a gap

`lane7_receipts/walk.py` computes, for a long:

```python
j = int(np.argmax(bl <= S))                       # first minute whose BID LOW crosses the stop
row['stop_gap_open_px'] = float(max(0.0, S - bo[j]))   # stop minus that minute's BID OPEN
```

`j == 0` means **the first strictly-post-decision minute already opened beyond the stop** — i.e. the
trade was through its stop at the entry instant. That is not a gap and not slippage; it is Lane 7's
synthetic walk filling at `ao[0]` one minute after a decision priced at the previous bar. Measured on
Lane 7's own surviving `walk.pkl`:

| | n | mean gap | contribution to the 0.06045 |
|---|---:|---:|---:|
| `stop_bar_idx == 0` | 1,585 | 0.36865 | **0.05139 (85.0 %)** |
| `stop_bar_idx > 0` (real gaps) | 9,785 | **0.01052** | 0.00906 |
| total | 11,370 | 0.06045 | |

**767 of the 1,059 rows Lane 7 counted as "gapped" (72.4 %) are `stop_bar_idx == 0`.** Excluding them,
p99 falls from **1.4519 to 0.1789** — Lane 7's headline tail statistic is almost entirely the artifact.

Corrected on Lane 7's own definition: 0.01052 × 0.5243 = **0.0055 R/fill**, not 0.0317. And even that
is a **lower bound**, because the minute-open gap is zero by construction whenever the crossing is
intrabar (90.7 % of stops), where the true slippage is the tick overshoot Lane 7's measure discards.

> **`D_SLIPPAGE_AND_STOP_FILLS_V1.json`'s `verdict` string — "the model is under-charging by
> >= 0.01170 R/fill on the stop leg alone" — does not hold.** On the same data with the entry-minute
> rows removed, Lane 7's own instrument says the model **over**-charges.

Lane 7's §5 also asserts the model "over-charges the target leg — a target is a resting limit exit and
pays no slippage at all." **That half is correct and I confirm it** (§3.3).

### 1.3 Lane 1 — upheld on the measurement, and its receipt disagrees with its report

`lane1_receipts/slip.py` is correct: exit-side quote, first crossing tick, sign convention right for
all four (side × barrier) combinations. **I reproduce it independently: 0.03932 on n = 9,543 against
Lane 1's 0.03932 on n = 9,526.** Five decimals, different code path, same tape.

But two things in Lane 1 need correcting:

- **`BARRIER_SLIPPAGE_V1.json` carries `optimism_per_resolved_trade: 0.013655`, while the report uses
  **0.0214**.** The receipt nets the target-leg credit off the stop-leg charge
  (`b = pS·0.03932 + pT·(−0.03969) = 0.018402`, ×0.742 = 0.013655 — reproduced exactly). The report
  then correctly declines that credit ("*not* crediting the target overshoot, since a TP limit fills at
  the level") and recomputes 0.7353 × 0.03932 × 0.742 = 0.0214 by hand. **The report is right and the
  JSON receipt is stale.** Anyone reading the receipt instead of the prose gets a figure 36 % too low.
- **The commission's framing of Lane 1 as "the constant is too LOW" is not what Lane 1 said.** Its
  §2.3 says the opposite: *"the estate's flat `expected_slippage_r = 0.02` is within 7 % of the
  measured truth (0.0214)."* Lane 1's finding is about **where** the constant is charged, not its
  level. That distinction is the whole of §2.

### 1.4 So: contradictory, or three quantities?

**Three quantities that were named the same thing, plus two errors.** On one basis — original risk
units, per resolved trade — they compose without conflict:

```
entry leg   0.0066   (Lane 6 measured this leg; its 0.0114 orig-unit figure is the same
                      order of magnitude, on 138 live rows vs my 18,978)
stop exit   0.0204   (Lane 1 and I agree to 5 decimals; Lane 7's corrected 0.0055 is the
                      gap-only sub-component of this, and it is a lower bound by construction)
target exit 0.0000
time stop   0.0004
            ------
round trip  0.0275
```

---

## 2. (B) HOW THE CONSTANT IS ACTUALLY USED

**It is charged ONCE per round trip, not per leg and not per side.** `config/agent_config.yaml:740`
`selected_cell_default_expected_slippage_r: 0.02`; verified 0.02 with **zero dispersion on all 81,968**
price-bearing rows, and it is a single scalar per row, not a per-leg field.

| # | consumer | `file:line` | cancels in the edge? |
|---|---|---|:--:|
| 1 | `deductible = Σ(expected_slippage_r, swap_cost_r, commission_r)` → `terminal_net_r = gross − deductible` | `candidate_funnel_analysis.py:164-174` | — |
| 2 | `cost_r = spread + slippage + swap + commission` | `src/costs/model.py:781-797` (`component_sum_r`) | — |
| 3 | **eligibility gate** `if row["cost_r"] > MAX_COST_R: continue` (`MAX_COST_R = 0.20`) | `candidate_funnel_analysis.py:263`, `:52` | **NO** |
| 4 | **expected-net gate** `expected < MIN_EXPECTED_NET_R` (0.10); `expected` is built from historical per-state means of `terminal_net_r` | `:270`, `probability_truth_analysis.py:379-381` | **NO** |
| 5 | **ranking key** `(expected, −cost_r, key)` | `:273` | no (inert: flat constant cannot reorder) |
| 6 | **censored fiat charge** `−1.0 − deductible_cost_r` | `:290`, `postmortem/pm_analysis.py:313` | **NO** |
| 7 | **live pre-trade gate** `total_cost_r = spread + slippage + swap + commission` vs `selected_cell_pretrade_max_total_cost_r` | `broker_net_cost_engine.py:718-728`, `:770` | **NO** |

### 2.1 Lane 1's cancellation claim: VERIFIED, and narrower than it reads

```
edge ≡ terminal_net_r + cost_r
     = (gross − slip − swap − comm) + (spread + slip + swap + comm)
     = gross + spread
```

**Slippage, swap and commission cancel exactly.** Lane 1's §1.2 point 1 is correct as an algebraic
identity, confirmed at both sites above.

**But "the constant cancels" is true only of the edge metric.** It does not cancel in:

- the **realized net** every published GTOS result reports (consumer 1) — charged once, at full weight;
- the **eligibility gate** (consumer 3), where **0.02 is 10 % of the entire 0.20 cost budget**, so the
  constant's level decides *which candidates are admitted at all*;
- the **expected-net gate** (consumer 4), where it shifts every historical state-mean down;
- the **censored fiat charge** (consumer 6);
- the **live pre-trade cost gate** (consumer 7).

So the level of the constant **does** matter — to selection and to every absolute R figure — and does
**not** matter to Lane 1's edge. Both halves need stating together; each alone misleads.

### 2.2 The distinction that resolves the whole dispute

Two different operations were conflated across the three lanes:

| operation | effect on the edge |
|---|---|
| **change the LEVEL of `expected_slippage_r`** (0.02 → 0.0057, or → 0.0317) | **exactly zero** — it cancels |
| **charge true slippage to the FILL PRICE** inside `quote_side.py` | reduces `gross`, and **nothing offsets it** — the edge falls by the full amount |

Lane 6 proposed the first and reported a +4.03 R book improvement from it. **The first operation cannot
move the edge at all, and its effect on the book is the opposite sign (§4.2).** Lane 1's §2.3 correctly
performs the second. The stop-leg overshoot is not in `spread_r`, `swap_cost_r`, `commission_r` or the
flat slippage constant, so it is pure uncompensated gross-side optimism.

**One term does cancel, and it is the entry leg.** The entry-fill error is a *spread-model* quantity
(measured correlation with the modelled-vs-true spread error **+0.753**): if the true entry-side quote
is Δ worse, the true fill is Δ worse **and** the true `spread_r` — hence the fair-value null — is Δ more
negative. It therefore must **not** be added to Lane 1's deduction, and must **not** be added on top of
Lane 7's tape-true spread restatement. Only the stop and time-stop legs are charged in §4.1.

---

## 3. (C) THE MEASUREMENT

**Frame.** For every row the sealed labeller resolved (`orig` arm), recover the price the engine
**booked** at each leg, then ask the tick tape what was achievable at that instant. Sign: **+ve = the
engine's booked price is better than achievable = engine optimism = a real cost.**

- Population: 74,249 sealed resolved MARKET rows, all five months
  (`/private/tmp/laneG-walk/lg_{feb,apr,may,jun,jul}.pkl.gz`).
- Restricted to fill **and** terminal inside the tick archive: **18,978 rows (25.6 %)**, 24 symbols,
  `2026-06-18..07-24`, from `/Users/borr/GTOSActive/vps-ticks-20260726/ftmo`.
- Clock: broker wall → UTC by `new_york_plus_7`, the rule declared in each file's `.timebase.json`
  sidecar and implemented at `src/utils/broker_clock.py:273`. The whole window is inside US EDT, so the
  offset is a constant +3 h and no DST ambiguity arises.
- In-window states: STOP 9,866 / TIME_STOP 5,482 / TARGET 3,630.
- CIs are 4,000-draw cluster bootstraps on `trading_day`, seed 20260812.

### 3.1 Per-leg result

| leg | n | mean | median | p95 | p99 | frac adverse | CI95 |
|---|---:|---:|---:|---:|---:|---:|---|
| entry fill | 18,978 | **+0.00663** | 0.00000 | +0.0527 | +0.2377 | 19.9 % | [+0.0047, +0.0084] |
| **stop exit** (at crossing tick) | 9,543 | **+0.03932** | +0.01707 | +0.1412 | +0.3400 | **99.5 %** | [+0.0364, +0.0431] |
| stop exit (at next tick) | 9,543 | +0.03749 | +0.01503 | +0.1900 | +0.4243 | 64.3 % | [+0.0336, +0.0421] |
| target exit | 3,435 | **−0.03968** | −0.01938 | −0.0014 | −0.0001 | **0.0 %** | [−0.0427, −0.0369] |
| time-stop exit | 5,482 | **+0.00141** | −0.00005 | +0.0361 | +0.1237 | 42.2 % | [−0.0001, +0.0029] |

**Which legs the archive can and cannot resolve.** Stops resolve for **9,543 of 9,866 (96.7 %)** and
targets for **3,435 of 3,630 (94.6 %)**; the remainder are rows whose booked barrier is never crossed by
the raw tick tape inside the engine's own [fill, terminal] span — an engine-vs-tape disagreement, not a
slippage measurement, and they are **excluded rather than imputed**. Time stops resolve for 5,482 of
5,482. **The LIMIT arm cannot be resolved at all: `lg_*.pkl.gz` is 100 % MARKET (74,249/74,249
verified), so no tick-derived slippage exists for the 72,496 resolved LIMIT rows — 49.4 % of the
population.** §5 states the capture that would fix it.

### 3.2 Stability — the number is not carried by one week

| | jun | jul | wk25 | wk26 | wk27 | wk28 | wk29 | wk30 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| stop-leg mean | 0.03555 | 0.04131 | 0.0415 | 0.0333 | 0.0389 | 0.0372 | 0.0440 | 0.0428 |
| n | 3,296 | 6,247 | 695 | 1,855 | 1,716 | 1,850 | 1,926 | 1,501 |

Range 0.0333–0.0440 across six weeks; no week is an outlier and no week drives the mean.

### 3.3 The target leg is correct by design — confirmed, not assumed

**0.0 % of 3,435 target crossings are adverse.** The tape overshoots the take-profit level by
−0.03968 R in the trade's favour, and the engine books the level exactly, declining the credit. That is
the right convention for a resting limit exit, and it means **the constant genuinely over-charges the
19.1 % of trades that end at target** — Lane 7's one correct half. Note that the flat constant charges
those trades 0.02 for a leg whose true slippage is zero.

### 3.4 Where it concentrates

**By symbol (stop leg conditional).** Worst: USDJPY 0.0657 (n=414), XAUUSD 0.0591, EURGBP 0.0504,
ETHUSD 0.0485, NZDUSD 0.0478. Best: NAS100 0.0184 (n=505), XAGUSD 0.0226, JP225 0.0233, US30_cash
0.0300. **A 3.6× spread across instruments.**

> **Lane 7's "concentrated in the JPY crosses" is only a quarter right.** USDJPY is worst of 24, but
> EURJPY is **20th** (0.0340), GBPJPY 13th (0.0382), AUDJPY 16th (0.0368), CHFJPY 7th (0.0428). Four of
> the five JPY crosses sit at or below the 24-symbol mean. The apparent JPY concentration in Lane 7's
> table is its gap-open measure loading on the entry-minute artifact.

**Round trip per resolved trade, by symbol** (entry + stop + time-stop, full table in the receipt):
**UK100 +0.1224** — a 4.5× outlier, and it is the entry/spread leg not the stop leg, independently
corroborating Lane 7's finding that the cash-index spread model is hour-flat while the tape is not.
Then GER40 +0.0459, USDJPY +0.0435, EURGBP +0.0410. Cheapest: XAGUSD +0.0060, NAS100 +0.0095,
USOIL_cash +0.0121.

**By entry hour (stop leg).** Hour 21 UTC **0.2230** (n=36, CI [0.1155, 0.3961]); hours 20–22 pooled
**0.0915** (n=273, CI [0.0657, 0.1219]); all hours 0.0393. **Hour 21 is 5.7× the mean — Lane 7's
hour-20/21 claim is CONFIRMED**, on thin n and stated with its CI. (Label precisely: this is the
*entry* hour, the hour a decision can be declined in; I do not store the stop instant.)

---

## 4. (D) THE ADJUDICATED VALUES AND THE THREE RECOMPUTATIONS

### 4.0 What to charge, and where

| quantity | value | where it applies |
|---|---:|---|
| **`expected_slippage_r` (exit-leg, the constant's own job)** | **0.0208** in-window / **0.0213** pooled-mix | consumers 1–7 in §2. Current 0.02 is **4–7 % light**. |
| entry-leg execution error | +0.0066 | belongs to the **spread model**, not slippage. Do **not** add to Lane 1's deduction; do **not** add on top of Lane 7's spread restatement. |
| target leg | 0.0000 | correct today |
| time-stop leg | +0.0004 | correct today (CI straddles zero) |

**The single most useful change is not the level — it is the location.** Charging the stop-leg
overshoot **to the fill price** in `quote_side.py:1420-1423` (Lane 1's §4.3 item 1) makes `gross`
tick-honest; changing the constant's level does not, because it cancels (§2.2). The level's real
leverage is on the **eligibility gate**, where 0.02 is 10 % of the 0.20 budget.

### 4.1 (i) Lane 1's edge against the corrected fair-value null

Deduction = stop-leg conditional × stop share + time-stop conditional × time-stop share, with shares
from Lane 1's own §1.1 barrier counts. SEs combine Lane 1's day-clustered edge SE with my bootstrap SE
on the conditional.

| arm | n | edge raw | deduction | **edge at tick truth** | t | CI95 | significant |
|---|---:|---:|---:|---:|---:|---|:--:|
| POOLED | 146,745 | +0.03087 | 0.02132 | **+0.00955** | 1.42 | [−0.0036, +0.0228] | **no** |
| **LIMIT** | 72,496 | +0.05380 | 0.02209 | **+0.03171** | **2.49** | **[+0.0067, +0.0567]** | **YES** |
| MARKET | 74,249 | +0.00840 | 0.02056 | **−0.01216** | −1.70 | [−0.0262, +0.0019] | no |

**Lane 1's headline is upheld and refined.** Its +0.0095 pooled figure reproduces at +0.00955 from an
independent measurement, and its "positive but no longer significant" verdict stands.

**What Lane 1 did not do is split the deduction by arm, and that is where the constructive result is.**
The pooled figure averages an arm that survives with an arm that does not:

> **At tick truth the estate's frozen MARKET-only rule trades the arm whose edge is −0.0122 and
> abstains on the arm whose edge is +0.0317 with a CI strictly clear of zero.** Combined with Lane 1's
> §1.3 finding that "order type" is a deterministic function of `origin_family`
> (`candidate_funnel_analysis.py:81`), the rule is a blanket exclusion of `current_fvg_fill`,
> `current_ob_retest` and `current_breaker_re_entry` — and charging true slippage makes that exclusion
> *worse*, not better, because MARKET's stop share and its edge are both on the wrong side.

**The load-bearing caveat, stated plainly: the LIMIT arm's stop slippage is UNMEASURED.** I transferred
the MARKET stop-leg conditional (0.03932) to it. That is defensible — a LIMIT entry becomes a
stop-*market* exit, same instrument, same mechanics, and Lane 1 measures LIMIT stops booking at
−1.00100 with 97.31 % exactly at the barrier, i.e. the engine treats them identically — but it is an
assumption, not a measurement. **The LIMIT edge would have to absorb a stop-leg slippage of 0.1150
R/stop — 2.9× the measured MARKET value — before its CI touches zero.** Nothing in the tape suggests
that. §5 gives the capture that would settle it.

### 4.2 (ii) The five-month sealed selected book

The 282 resolved selected trades have a **different barrier mix from the pool**, and it moves the
answer's sign:

| | selected book (282) | pool (146,745) |
|---|---:|---:|
| STOP share | **0.4362** | 0.5329 |
| TIME_STOP share | 0.3759 | 0.2576 |
| TARGET share | 0.1879 | 0.2095 |
| **true exit slippage** | **0.01768** | 0.02132 |
| charged | 0.02000 | 0.02000 |
| **Δ per trade** | **−0.00232** | +0.00132 |

> **The sealed five-month book net moves from +0.954 R to +1.609 R (+0.655 R).** The constant slightly
> **over**-charges the selected book, because selection favours trades that end at time stop or target
> rather than at a stop — exactly the two legs whose true slippage is ~0 — so the flat constant taxes
> them for a cost they do not incur.

**All three lanes got the direction of this wrong.** Lane 6 predicted +4.03 R (+0.954 → +4.987) from a
3.5× overcharge; the true overcharge is **1.13×** and worth **+0.655 R**, 6.2× smaller. Lane 7 predicted
an under-charge, i.e. the opposite sign. The correction is real, it is positive, and it is **immaterial
against a book whose fate is decided by ±6 R of spread-model error** (Lane 7's UK100 restatement).

**Do not compose this with Lane 7's spread restatement by addition.** Lane 7's +0.954 → −6.090 R
already reprices the entry/spread leg from the tape; the entry-leg term in §3.1 is the same quantity.
The slippage-only correction that is safe to add to Lane 7's restated figure is the **+0.655 R** above.

### 4.3 (iii) Lane 7's cost-veto result

**Direction: unchanged. Magnitude: negligible. The veto is structurally immune to this dispute.**

- The veto ranks candidates on ex-ante `cost_r`. `expected_slippage_r` is a **flat constant with zero
  dispersion on all 632,934 rows** (verified), so it is a pure additive shift and **cannot reorder any
  candidate against any other**. Every decile boundary, every rung, every reported gross figure is
  unchanged.
- The only mechanical effect is on the **absolute cost level and the `MAX_COST_R = 0.20` admission
  gate**. Replacing 0.02 with the pooled 0.0213 raises `cost_r` by 0.0013 uniformly — at Lane 7's L0
  mean cost of 0.2133 that is **+0.6 %**, and it admits marginally fewer candidates at the gate.
- Lane 7's L4 recommendation (cost ≤ OOS p25) and its +3.1 to +5.1 R/month recoverable stand.

**But one Lane 7 number should be withdrawn**: its §5 claim that the model "is optimistic on the stop
leg by ≥ 0.0117 R/fill (≥ 58 % too low)". The correct figure is **+0.0013 R/fill (6.6 % too low) on the
pool**, and **−0.0023 R/fill (11.6 % too HIGH) on the selected book**.

### 4.4 Is the tick window long enough to settle the five-month question?

**For the stop-leg constant: yes.** 9,543 crossings, CI [+0.0364, +0.0431] — a ±9 % band on a term
worth 0.021 R/trade. Stable across six weeks (§3.2). The five-month extrapolation risk is
**composition, not sampling**: the correction is `stop_share × 0.0393 − 0.02`, and I apply each
population's own measured stop share rather than transferring a per-trade figure, which removes the
dominant error.

**For Lane 1's edge: no, and the gap is the LIMIT arm, not the window.** The measurement covers 12.9 %
of the resolved population (18,978 of 146,745) and **0 % of the LIMIT arm**. The pooled verdict
("not significant") is robust — it holds for any LIMIT stop-leg value between 0 and 0.115 — but the
*arm split*, which is the actionable result, rests on a transfer.

---

## 5. WHAT WOULD REVERSE EACH FINDING HERE

Every negative above, with the measurement that overturns it and the nearest unrefuted constructive
variant.

| finding | the measurement that would reverse it | nearest unrefuted constructive variant |
|---|---|---|
| pooled edge not significant at tick truth (§4.1) | A stop-leg slippage below **0.0179 R/stop** pooled (vs 0.0393 measured) restores t > 1.96. Requires the LIMIT arm to fill stops ~2× better than MARKET. | **Split the arms.** LIMIT already survives at +0.0317 [+0.0067, +0.0567] without any new data. |
| LIMIT arm's edge rests on a transferred slippage | **Walk the 72,496 resolved LIMIT rows on ticks.** The blocker is that `lg_*.pkl.gz` carries prices for MARKET only; the LIMIT price-bearing export is the one missing input, and the tape for it is already on disk. ~1 session. | Report the LIMIT edge with the transfer named, as here. It falsifies only above 0.115 R/stop. |
| the constant over-charges the selected book by only 0.0023 (§4.2) | A future window whose selected book has a stop share **above 0.5089** flips the sign. The pool sits at 0.5329, so this is a live possibility, not a remote one. | Make the charge **barrier-conditional** rather than flat: 0.0393 on stops, 0 on targets, 0.0014 on time stops. Needs no new data and is exactly the measured structure. |
| hour-21 exposure is real (§3.4, §6) | n = 36. A second tick capture covering hours 20–22 outside 2026-06-18..07-24 showing a mean near 0.039. | The CI's own lower bound is **+0.1155**, still 2.9× the all-hours mean — the finding survives its own worst case. |
| entry leg is a spread quantity, not slippage (§2.2) | A decomposition showing entry-fill error uncorrelated with spread-model error. Measured correlation **+0.753**. | Treat the two together in one spread repair (Lane 7 rank 1), not as two independent charges. |

**The single capture that would settle the most**: a LIMIT-arm price-bearing export over the existing
tick window. It costs no validation currency (it re-scores sealed data), needs no new market data, and
it is the input that converts §4.1's arm split from a transfer into a measurement — which is the one
result here that changes what the estate should trade.

---

## 6. (E) THE LIVE-MONEY QUESTION

**First, a correction to the commission's premise.** The armed set is **FOUR sleeves, not three**:
`crypto`, `energy_agri`, `sub_xvol_pullback`, **`sub_mid_dn_revert`** — read from
`src.safety.armed_set.armed_sleeves()`, the single source of truth CLAUDE.md §4 requires be used
instead of prose. The commission named three.

**Second, and this bounds everything below: none of this measurement transfers to the armed book
directly.** The 18,978 rows are the **candidate-funnel** decision surface — a 24-symbol M1 barrier walk
of the research pool. The armed book is the `ultimate_book` W7 sleeve estate on **H4** bars — all four
armed sleeves are `TF_H4` at `src/components/ultimate_book/sleeves/registry.py:50` (`crypto`), `:51`
(`energy_agri`), `:54` (`sub_xvol_pullback`), `:55` (`sub_mid_dn_revert`). That is hazard **H7**: replay does not
measure the live system. What follows is an **exposure statement by instrument and hour overlap**, not
a transferred economic claim.

### 6.1 By instrument — the armed book is on the CHEAP side of the surface

| sleeve | `ON_SURFACE` | measured stop-leg | round trip | rank of 24 |
|---|---|---:|---:|---|
| `crypto` | BTCUSD, DASHUSD | BTCUSD **0.0413** | +0.0196 | 10th; **DASHUSD not in the 24-symbol surface — UNMEASURED** |
| `energy_agri` | USOIL_cash, UKOIL_cash | 0.0370 / 0.0460 | +0.0121 / +0.0160 | 15th / 6th |
| `sub_xvol_pullback`, `sub_mid_dn_revert` | CLEAN3 registry minus `NATGAS_cash`, `HEATOIL_c` | mixed | — | spans the surface |

**The two named hazards do not land on the armed book.** UK100 (+0.1224 round trip, the 4.5× outlier)
and USDJPY (worst stop leg) are **not** in `crypto` or `energy_agri`'s surfaces. The JPY crosses Lane 7
flagged are the `fx_jpy` / `fx_jpy_ny` sleeves — **both unarmed** (`fx_jpy` was pulled 2026-07-30).
BTCUSD, USOIL_cash and UKOIL_cash all sit at or below the 24-symbol mean.

### 6.2 By hour — the one real exposure, and it is structural

All four armed sleeves are H4. With the broker clock at UTC+3 through this window, MT5 H4 bars close at
broker 04:00/08:00/12:00/16:00/20:00/24:00 = **UTC 01:00, 05:00, 09:00, 13:00, 17:00 and 21:00**.

> **One of the six H4 decision instants every day — broker midnight, 21:00 UTC — is the single worst
> slippage hour on the surface: 0.2230 R conditional stop slippage (n = 36, CI [+0.1155, +0.3961]),
> against 0.0393 all-hours. 5.7× the mean, and 2.9× at its own CI lower bound.**

That instant is the daily rollover, and it is where Lane 7 independently measured hour-21 cost at
0.9216 R/fill against 0.2019 at the cheapest hour. Two instruments, same hour, same direction.

**Sizing the exposure honestly.** Restricted to the six H4-close hours the stop-leg mean is **0.0381
(n = 2,540, CI [0.0350, 0.0414])** — i.e. **indistinguishable from the all-hours 0.0393**, because the
other five H4 hours are cheap. So the exposure is **1 of 6 decision slots**, not a book-wide tax. If
armed-sleeve entries were uniform across the six slots, the expected excess over the flat 0.02 charge
would be roughly **(0.2230 − 0.0393)/6 ≈ 0.031 R per stopped trade at that slot**, or **~0.005 R per
armed trade** — small, one-sided, and adverse.

**What this does and does not license.** It is **not** a config proposal and I make none. It is one
measured fact: the armed book's H4 grid puts a decision instant on the broker rollover, the rollover is
where slippage and spread both blow out on two independent instruments, and the flat 0.02 charge prices
that instant identically to 13:00 UTC. **The exposure is real, one-sided, adverse, and small; the
instruments are on the cheap side of the surface; the measurement is on a different decision surface
and carries H7.** Any decision here is Borhen's.

---

## 7. WHERE I OVERTURNED A LANE — THE SPECIFIC LINES

| lane | claim overturned | the exact line that produced it |
|---|---|---|
| **6** | "0.0057 measured, constant is 3.5× too high, book +0.954 → +4.987 R" | `PHASE0_INVERSION_TRUTH_V1.md:362-365` — compares a 0.02 **original-unit** constant against a 0.0057 **inverted-unit** measurement. `:374-377` in the same section states the correct 0.010-inverted comparison. Unit factor exactly 2×; true ratio 1.75×; and it is the **entry** leg. |
| **7** | "0.06045 R/stop → 0.0317 R/fill, model ≥58 % too low" | `lane7_receipts/walk.py`, `j = int(np.argmax(bl<=S))` then `max(0.0, S-bo[j])` — admits `j == 0`, the entry minute. 767 of 1,059 "gapped" rows (72.4 %) are `j == 0`, contributing **0.05139 of 0.06045 (85.0 %)**. Corrected: 0.0105 R/stop, p99 1.4519 → 0.1789. |
| **7** | "concentrated in the JPY crosses" | Same artifact. Measured per-symbol: 4 of 5 JPY crosses at or below the 24-symbol mean. Its **hour** claim (20–21) is confirmed. |
| **1** | receipt `optimism_per_resolved_trade: 0.013655` | `lane1_receipts/slip.py`, `b = pS*stop_mean + pT*target_mean` — nets the target credit the report then correctly declines. **The report's 0.0214 is right; the JSON is stale.** |
| **1** | (not overturned) stop leg 0.03932 | Independently reproduced at 0.03932 on n = 9,543. **Upheld.** |
| commission | "Lane 1 concluded the constant is too LOW" | `LANE_1_FAIR_VALUE_NULL_V1.md:249-250` says the opposite — "within 7 % of the measured truth". Lane 1's finding is about **where** it is charged. |

---

## 8. PROVENANCE

- Population: `/private/tmp/laneG-walk/lg_{feb,apr,may,jun,jul}.pkl.gz` (74,249 sealed resolved MARKET
  rows; 100 % MARKET verified). Pool counts and edge ladder from `LANE_1_FAIR_VALUE_NULL_V1.md` §1.1–1.3.
- Ticks: `/Users/borr/GTOSActive/vps-ticks-20260726/ftmo/`, 24 symbols, `2026-06-18..07-24`,
  broker→UTC by `new_york_plus_7` (`src/utils/broker_clock.py:273`, declared in each `.timebase.json`).
- Sealed selected book: 282 resolved trades, `frozen3.pkl` (Lane 7's `frozen.py` output), net +0.9544 R.
- Lane 7 re-analysis: its own surviving `walk.pkl`, unmodified.
- Constant: `config/agent_config.yaml:740`; consumers traced in §2 by direct read.
- CIs: 4,000-draw cluster bootstraps on `trading_day`, seed 20260812. Nothing uses a naive i.i.d. SE.
- **Confers no arming, sizing, promotion or activation authority.**
