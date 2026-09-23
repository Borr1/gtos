# The barrier-clock defect — register entry, blast radius, and the class it belongs to

**Commission:** orchestrator, 2026-08-12. Urgent blast-radius assessment of the defect the
attrition-recovery lane found (`ATTRITION_RECOVERY_V1.md` §2.2, commit `8cb78200c`): *the barrier
clock is anchored at the decision instant rather than the fill instant for orders that rest as
limits*, so outcome measurement begins before the order would have existed.

**Scope discipline.** Measurement only. No live path, no config, no arming, nothing on a broker,
no VPS. Every number below is recomputed on this machine from sealed inputs, from code and data
rather than from documents. Receipts: `barrier_clock_receipts/` — five scripts and the five JSON
artifacts they wrote.

---

## 0. The answer, in five lines

| question | answer |
|---|---|
| **Does it touch the ARMED LIVE BOOK?** | **NO.** Structurally immune. The book places `TRADE_ACTION_DEAL` at the live tick and hangs both barriers off the price it actually paid. There is no interval between decision and fill in which a barrier could resolve. |
| **Does it touch the SLEEVE estate?** | **NO.** Structurally immune, verified independently of the attrition lane's prose. Sleeve entry is the CLOSE of the signal bar and every barrier loop starts at `i+1`. The corpus carries no order-type, limit, fill or marketability field at all. |
| **Does it touch the SEALED funnel corpus?** | **NO — and this corrects the attrition lane.** The sealed pool's own label is already fill-aware, and Lane G's resolver emits `RESOLVED_NO_FILL` on 388,912 rows. The defect lives in **re-walkers** that discard the sealed label and re-derive outcomes from the ordered-path sidecar at observation 0. |
| **What IS contaminated, then?** | Every grid that re-walks the sidecar decision-anchored. Confirmed: **FB**'s `current_ob_retest` cell and **CQ**'s inverted-breaker cell — one of the two candidates standing at the V27 family tip. |
| **Does it corrupt the frozen ridge's training target?** | **0 of 284,652 rows (0.00 %).** The label is the fill-anchored resolver's `terminal_net_r`, and a limit that never filled trains at `0.0`, not at a barrier outcome. The refit question is vacuous. |

**One sentence for the owner: no live or sleeve number moves, and no published economic figure for
the armed book is affected.**

---

## 1. TASK 1 — the armed live book and the sleeve estate

`barrier_clock_receipts/bcd_sleeve_immunity.py` → `BCD_SLEEVE_IMMUNITY.json`. Three structural
questions, each answered from source at `origin/main`, not from any document.

### 1.1 The live book places at market. Cited, not asserted.

| step | evidence |
|---|---|
| the book's entry price **is the live tick** | `src/components/ultimate_book/order_router.py:63` — `entry = float(ask if d > 0 else bid)   # cross the spread on entry` |
| both barriers hang off **that** price | `order_router.py:73` — `"stop_loss": entry - sign * rd, "take_profit_1": entry + sign * target_dist` |
| the request is a **market deal** | `execution.py:3519` `order_type = 0 if direction == "LONG" else 1`; `:3534` `"action": 1,  # TRADE_ACTION_DEAL` |
| the book module has **no notion of a limit price** | `rg limit_price src/components/ultimate_book/` → **zero hits** |
| the whole tree has **no order-placing limit path** | the only `ORDER_TYPE_BUY_LIMIT` in `src/` + `scripts/` is `scripts/mt5_preflight.py:153`, and `:167` submits it to **`mt5.order_check`**, which validates without creating an order or a ticket (`:141-147`). `TRADE_ACTION_PENDING` otherwise appears only as a constant (`mt5_interface.py:63`) and as a classifier branch in `activation_token.py:625`. |

There is therefore no decision→fill interval in the live path at all. The defect requires one.

**A corroborating detail worth recording, because it shows the live engine already knows the
hazard.** GTOS's legacy pending-limit machinery — the `PendingLimitIntent` the W7 book does not
use — refuses the exact scenario this defect books as a win: `execution.py:6119-6146` fills only
when `candle.low <= limit_price` (LONG) / `candle.high >= limit_price` (SHORT), and when the
target is reached without an entry touch it logs *"Limit intent cancelled (target reached without
entry touch)"* and cancels. The engine's own docstring is explicit that *"no broker pending order
exists until the orchestrator later sees the limit touched and calls open_trade() as a market
order"* (`:277-282`). The research grid does what the engine refuses to do.

### 1.2 The sleeve estate has no decision→fill gap

| step | evidence |
|---|---|
| entry is the **close of the signal bar** — a price that traded at the decision instant | `phase6/receipts/aa_estate_generate.py:276` — `entry = bars[i].c` |
| the estate knew the convention and measured it | `:278` records `entry_convention_gap` = `direction * (next_open - decision_close) / stop_dist` |
| every barrier loop starts **strictly after** the entry bar | `src/research_infra/walkforward/exits.py:246`, `:426`, `:528` — all `for j in range(i + 1, …)` |
| the artifact carries **no order-type or fill field** | `AA_ESTATE_TRADES.json.gz`: 22,324 rows, 32 sleeves, 27 schema keys, **zero** matching `limit|order_type|fill|pending|passive|marketable` |
| no trade can resolve on its own entry bar | `min(exit_bar_offset) = 1`; rows with `exit_bar_offset == 0`: **0 of 22,324** |

So the attrition lane's "all market orders" is correct, and it is correct for a stronger reason
than order type: the sleeve entry instant *is* a traded price on the bar grid the walk uses, so
decision instant and fill instant are the same object.

### 1.3 The published sleeve and armed-book figures, checked at the walker

Every artifact named in the commission resolves to one of two lineages, and neither can carry the
defect:

| published figure | walker | anchoring |
|---|---|---|
| AD's exit frontier (1,631 gated cells) | `phase7/receipts/ad_exit_sweep.py:357` → `replay(bars, i, …)` on `AA_ESTATE_TRADES` | `i+1`, market-close entry |
| AK's frontier / orphan generators | `phase8/receipts/ak_supply_generate.py:227-249` → `replay(bars, i, …)`, `"entry_price": float(bars[i].c)` | same |
| AQ / AR / AS / AU / AV / AW re-walks | all read `AA_ESTATE_TRADES` / `AQ_ESTATE_TRADES` and call the same `replay` | same |
| **`mx_btcusd @ target_5R`** — the estate's one standing admission | same lineage (AD/AL/AU exit frontier over the estate trades) | same |
| `SURVIVOR_BOOK_V1.json` tiers and the `p_pass` series | `scripts/build_survivor_book.py` → `recost_w7_validation.py` over the `INTEG_W3/W5` daily-R caches | **no barrier walk exists in this lineage at all** — it is arithmetic over cached daily R series plus Monte Carlo |

`[MEASURED: absence]` — no sleeve-lineage artifact in the estate contains a limit level, a fill
class, or a marketability flag to anchor wrongly.

### 1.4 The live labelling / attribution path

The expectation in the commission is correct and it verifies. The live book records **broker
truth**, not a simulated walk:

* placement persists the broker ticket and `placed_at_utc` (`book_owner.py:1589-1602`), and the
  lifecycle packet carries `executed_entry_price`, `broker_order_entry_mode: "MARKET_ORDER"` and
  `broker_order_action: "TRADE_ACTION_DEAL"` (`execution.py:5430-5440`);
* Lane F's ground-truth reader takes `price_open` off live positions and reconciles against
  `history_deals_get` (`lane_f_receipts/lane_f_broker_truth.py:57-123`), i.e. the broker's own
  fill price and fill time.

There is no barrier clock in the live attribution path to anchor. **Live performance attribution
is not corrupted.**

---

## 2. TASK 2 — the funnel, and the correction to where the defect actually lives

### 2.1 The reach figure is confirmed exactly, at the population level

`barrier_clock_receipts/bcd_wave21_census.py` → `BCD_WAVE21_CENSUS.json`, over the five wave-21
months Lane G walked (`rows_{feb,apr,may,jun,jul}.pkl.gz`, the rows its `extract.py` turned into
`pool_table.npz`):

| | rows |
|---|---:|
| total pool | **632,934** ✓ |
| the three LIMIT families | **550,966** ✓ (87.05 %) |
| of those, `limit_marketable_at_decision == False` | **544,028 (98.74 %)** |
| the seven MARKET families | 81,968 |
| of those, non-marketable | **550 (0.67 %)** |

And the family split is **exact on this corpus**, which had never been tested: median and p90
`distance_to_limit_risk` is **0.000** for all seven MARKET families and **3.752 / 4.608 / 5.226**
(p50) for the three LIMIT families. The classifier `candidate_funnel_analysis._order_type:80-81`
keys on family name; on this corpus that heuristic is right to within 0.04 % of rows.

### 2.2 But the corpus was already walked correctly — this is the finding that matters

`resolve_post_submission_m1_lifecycle` (`src/research_infra/walkforward/quote_side.py:1032`) is
the wave-21 resolver, and it **implements the fill gate**:

* `:1249-1250` `limit_touched(...)`, `:1291-1330` searches forward for the touch;
* `:1259-1266` returns `RESOLVED_NO_FILL` with rule `FULL_VERIFIED_M1_PATH_WITHOUT_CORRECT_SIDE_LIMIT_TOUCH`;
* `:1270-1276` **censors** submission-bar ordering rather than guessing it;
* `:1278-1290` a MARKET order fills at the **first complete successor** M1 open — *"the submission
  interval is never causal"* (`:1053`).

The `lifecycle_label_status` census proves it fired, at scale:

| | LIMIT families | MARKET families |
|---|---:|---:|
| `RESOLVED_NO_FILL` | **388,912** | — |
| `RESOLVED_FILLED_{STOP,TARGET,TIME_STOP}` | 40,153 / 16,136 / 16,207 = **72,496** | 38,054 / 14,601 / 21,594 = **74,249** |
| `CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_ORDERING` | 10,848 | — |

**70.6 % of the LIMIT population never fills, and the resolver says so.**

### 2.3 The sealed January label is fill-aware too

`barrier_clock_receipts/bcd_sealed_label.py` → `BCD_SEALED_LABEL.json`. Against
`CJ_RECLOCKED_S0R0_POOL_V1` (27,658 rows) + `CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1`, at the
pool's own native geometry (stop 1.0 R, target `policy_target_r`), comparing the pool's own
`opportunity_net_proxy_r + cost_r` against a decision-anchored walk (**A**) and a fill-anchored
walk (**C**):

| population | n | E[G sealed] | E[A decision] | E[C fill] | G == A exactly | G == C exactly |
|---|---:|---:|---:|---:|---:|---:|
| measured resting limits | 9,534 | **+0.0087** | +0.7275 | **−0.0342** | 58.97 % | **81.21 %** |
| the three LIMIT families | 12,749 | **−0.3664** | +0.1582 | **−0.3621** | 71.39 % | **88.36 %** |
| all rows | 27,658 | −0.2175 | +0.0409 | −0.2438 | 79.54 % | 87.08 % |

The sealed label tracks the fill-anchored arm to within 0.004 R and diverges from the
decision-anchored arm by **+0.52 R**. Session T1 had already named this quantity — its
`t1_fill_axis.py:6` calls the pool figure *"the frozen fill-aware walked gross"* — so the
fill-awareness of the sealed label is corroborated by prior work.

> **Correction to `ATTRITION_RECOVERY_V1.md` §6, and it should be applied at source.** The
> sentence *"Any number ever published for a LIMIT family from a decision-anchored walk is
> measuring excursion from a price the book never paid"* is true as written and is being read as
> *"every LIMIT-family number in the estate is contaminated."* It is not. **The sealed corpus and
> Lane G are clean.** The contaminated set is the grids that re-walk the sidecar from observation 0.

### 2.4 The restatement, with intervals

`barrier_clock_receipts/bcd_jan_decomposition.py` → `BCD_DECOMP_JAN.json`. All 27,658 January rows,
each at its **own** declared geometry (`entry_price` / `stop_loss` / `take_profit_1`), stop-wins tie
rule, day-block bootstrap over 21 decision days, 4,000 draws.

Three arms, which separate two sub-defects that had been travelling as one:

* **A** — barriers from the submission bar (obs 0). The defect as walked.
* **B** — barriers from the first complete successor bar (obs 1). Isolates *submission-bar
  non-causality*.
* **C** — barriers from the limit touch, searched from obs 1; never touched → NO_FILL at 0. Isolates
  *fill anchoring*.

**Sub-defect (i), submission-bar non-causality, is immaterial and can be closed:** A − B is
−0.0013 R/trade over all rows, +0.0141 on the resting-limit subset, and never exceeds 0.023 R in
any family. The whole effect is fill anchoring.

| population | n | ARM A net R/trade [CI95] | ARM C net R/trade [CI95] | inflation A−C [CI95] | never fills |
|---|---:|---|---|---|---:|
| all rows | 27,658 | −0.6228 [−0.6811, −0.5615] | −0.8992 [−0.9666, −0.8305] | **+0.2764** [+0.2585, +0.2957] | 1.28 % |
| **measured resting limits** | 9,534 | −0.0182 [−0.1121, +0.0760] | −0.7715 [−0.8687, −0.6631] | **+0.7533** [+0.7195, +0.7865] | 1.81 % |
| **marketable limits (control)** | 13,572 | −1.0519 [−1.1291, −0.9786] | −1.0550 [−1.1320, −0.9818] | **+0.0031** [−0.0023, +0.0078] | 0.71 % |
| the three LIMIT families | 12,749 | −0.6362 [−0.7159, −0.5469] | −1.1534 [−1.2543, −1.0530] | +0.5172 [+0.4694, +0.5717] | 0.24 % |
| the seven MARKET families | 14,909 | −0.6113 [−0.6743, −0.5469] | −0.6818 [−0.7440, −0.6189] | +0.0706 [+0.0626, +0.0782] | 2.17 % |

**The marketable-limit row is the control that proves the mechanism**: a limit priced through the
market has no decision→fill gap, and its inflation is +0.0031 R with an interval containing zero,
on 13,572 rows. The defect appears exactly where the order rests and nowhere else.

Per family, restricted to rows measured as resting limits:

| family (resting-limit rows only) | n | ARM A [CI95] | ARM C [CI95] | inflation [CI95] |
|---|---:|---|---|---|
| `current_fvg_fill` | 5,297 | −0.0585 [−0.1827, +0.0744] | −1.0602 [−1.2074, −0.8974] | **+1.0017** [+0.9280, +1.0792] |
| `current_breaker_re_entry` | 538 | +0.4003 [+0.2265, +0.5608] | −0.4493 [−0.6712, −0.1882] | **+0.8495** [+0.6639, +1.0097] |
| `current_ob_retest` | 1,041 | +0.4138 [+0.2756, +0.5618] | −0.3010 [−0.4270, −0.1676] | **+0.7147** [+0.6035, +0.8365] |
| `structural_distance_extreme` | 453 | −0.2211 [−0.4127, −0.0226] | −0.9213 [−1.1035, −0.7537] | **+0.7003** [+0.5969, +0.8343] |
| `cross_asset_lead_lag` | 163 | +0.3094 [+0.0662, +0.5691] | −0.1663 [−0.4036, +0.1157] | +0.4757 [+0.3513, +0.5971] |
| `liquidity_sweep_reclaim` | 1,047 | −0.2050 [−0.3026, −0.1124] | −0.4022 [−0.4852, −0.3189] | +0.1973 [+0.1615, +0.2354] |
| `session_open_range_break` | 38 | −0.1758 [−0.5195, +0.1884] | −0.2987 [−0.6261, +0.0383] | +0.1229 [+0.0136, +0.3181] |
| `displacement_continuation` | 884 | −0.2555 [−0.3508, −0.1569] | −0.3331 [−0.4151, −0.2477] | +0.0776 [+0.0520, +0.1045] |
| `volatility_compression_expansion` | 63 | −0.2439 [−0.4154, −0.0876] | −0.2461 [−0.4165, −0.0904] | +0.0022 [+0.0000, +0.0068] |
| `regime_transition_break` | 10 | +0.2216 [−0.2800, +0.9197] | +0.2216 [−0.2800, +0.9197] | +0.0000 |

**A finding the family heuristic misses, on this window.** On the January S0R0 pool — a different
window and generator from the five wave-21 months — **2,658 of 9,534 measured resting limits
(27.9 %) sit in families the classifier calls MARKET**, and their inflation is +0.2538 R/trade
[+0.2247, +0.2821]. Their median displacement from the market at the decision instant is 0.13–0.53 R,
an order of magnitude above the spread, so this is not a spread artifact. **The family-name
classifier is exact on the wave-21 corpus and understates the reach by 27.9 % on the January one:
classify by measured restingness, never by family name, whenever the pool supports it.**

Two diagnostics reproducing the attrition lane's signature at the pool's own geometry: **25.08 %**
of resting-limit rows book the target at the first observation with the limit untouched, and
signed displacement at the decision instant is **+1.3817 D mean / +0.8942 median, favourable on
100 % of them by construction**.

### 2.5 Which published numbers are actually contaminated

Contamination requires a walker that (a) reads the ordered-path sidecar, (b) anchors on
`entry_price`, and (c) starts accumulating at the first post-decision observation with no fill
gate. Two are confirmed:

| artifact | evidence | status |
|---|---|---|
| **FB** `current_ob_retest` 1.5D / 0.25D, +1.6467 net R/trade | the attrition lane's `fb_rewalk.py`; reproduced to the last digit, then killed at −1.2493 | **already retired** by `ATTRITION_RECOVERY_V1.md` §2 |
| **CQ** `cq_current_breaker_re_entry_inverted_5d_stop_0p25d`, +11.9 net R/trade | `phase18/receipts/cq_path_pool_grid.py:498` slices strictly after the decision, `summarize_ohlc_path:773-774` runs `np.maximum.accumulate` from index 0 of that slice on `entry` = the pool's limit level, and `:1525` derives `grid_net_r` from it. **No fill gate anywhere in the file.** | **contaminated; requires re-derivation** |

**CQ is the operationally important one and it is worse than a re-derivation.** It is one of the
two candidates standing at the V27 family tip, it is on `current_breaker_re_entry` (97.58 %
resting on the wave-21 corpus), and its contract is **inverted** — and `PHASE0_INVERSION_TRUTH_V1.md`
§6 already established that an inverted LIMIT is a **SELL STOP**, that the committed resolver
cannot walk it (97.7 % censor as `CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_ORDERING` because
`limit_touched` is hardwired to direction), and that a STOP fills at its level *or worse* where a
LIMIT fills *or better*. So CQ's cell cannot be re-derived at all until `quote_side.py` gains a
STOP order type. **It should not be quoted as an economic figure until then.** This is independent
corroboration of the discovery lane's finding that the candidate is largely artifact, arriving
through a different mechanism.

`[UNVERIFIED]` — the phase-19 discovery walkers (`w0_walk.py`, `e6_build_month.py`,
`w0_measure*.py`) and `src/research_infra/cs_breaker_folds.py` read the same sidecar and were not
audited here for want of time. Every one of them should be checked against §4's detection test
before any of its numbers is quoted.

---

## 3. TASK 3 — the Lane G reconciliation, stated exactly

The commission's two branches were: *if Lane G's n = 74,249 excluded the contaminated LIMIT rows,
its fair-coin verdict stands and the LIMIT families are worse than published; if it included them,
Lane G's central estimate needs restating.* **Neither branch holds, because both assume the LIMIT
rows were walked decision-anchored, and they were not.**

1. **Lane G's population was MARKET-only, and the arithmetic is exact.** `laneg_walk.py:236` keeps
   only `origin_family in MARKET_FAMILIES`, and n = 74,249 = 38,054 + 14,601 + 21,594, the
   `RESOLVED_FILLED_*` MARKET rows. The LIMIT rows are the separate n = 72,496 bucket in
   `FUNNEL_LIMIT.json` (40,153 + 16,136 + 16,207). ✓
2. **Both buckets were walked fill-anchored**, by `resolve_post_submission_m1_lifecycle` (§2.2).
   Lane G's `E[gross + spread_r] = +0.00844 ± 0.00422` (t 2.00, p 0.045, n 74,249) carries **zero
   barrier-clock contamination**. Its fair-coin verdict stands, unqualified.
3. **The LIMIT bucket's `E[net + cost] = +0.05383 ± 0.00461` is therefore not this defect.** The
   attrition lane already attributed it correctly — Lane G's half-spread **fill-selection**
   artifact (`current_fvg_fill`: +0.05453 = 1.07 × half its own spread). A resting limit fills only
   when price comes to it, which selects on adverse movement; that is a real and separate bias, it
   was named, and it is not a clock error.
4. **So the honest sentence is: the LIMIT families are NOT worse than any published figure in the
   wave-21 corpus, because that corpus never published a decision-anchored LIMIT figure.** They are
   worse than every figure published by a *re-walk* of the sidecar — §2.4 prices that at
   **+0.7533 R/trade [+0.7195, +0.7865]** on the January resting-limit population.

---

## 4. The register entry

### BCD-1 — decision-anchored barrier clock on resting-limit orders

| field | value |
|---|---|
| **class** | measurement-instrument defect — outcome resolution begins before the position could exist (lookahead) |
| **mechanism** | a barrier walk anchors both barriers on `entry_price` and starts accumulating at the first post-decision observation. When `entry_price` is a **resting limit level** rather than a traded price, the walk measures excursion from a price the book never paid, over an interval in which it held nothing. |
| **signature (any one is sufficient)** | (a) rows resolve a barrier at the **first** observation while the limit is untouched — 25.08 % of January resting-limit rows; (b) signed displacement at the decision instant is systematically **favourable** — +1.3817 D mean, favourable on 100 % of resting rows; (c) the achieved target rate exceeds the driftless bound — 52.8 % against 14.3 % at 6:1 on FB's cell; (d) `NO_FILL` never appears in the outcome vocabulary. |
| **magnitude** | +0.7533 R/trade [+0.7195, +0.7865] on measured resting limits at native geometry (n 9,534, 21 days). Per family up to **+1.0017** (`current_fvg_fill`). At a re-geometried tight stop it amplifies with 1/stop: FB's 0.25D cell shows **+2.90 R/trade**. Marketable-limit control: **+0.0031 [−0.0023, +0.0078]** — zero, as the mechanism requires. |
| **population at risk** | resting-limit orders. Wave-21 corpus: **550,966 of 632,934 rows**, 98.74 % non-marketable. January S0R0 pool: 9,534 of 27,658 measured resting, **27.9 % of them outside the three named families**. |
| **NOT at risk** | the armed live book (§1.1); the sleeve estate and every figure on it, including `mx_btcusd @ target_5R`, AD/AK/AQ/AU frontier cells, `SURVIVOR_BOOK_V1` tiers and the `p_pass` series (§1.3); live performance attribution (§1.4); the sealed pool label (§2.3); Lane G both arms (§3); the frozen ridge's training target (§5). |
| **confirmed contaminated** | FB's `current_ob_retest` 1.5D/0.25D (retired); **CQ's inverted-breaker cell** (`cq_path_pool_grid.py`), which additionally cannot be re-derived until `quote_side.py` gains a STOP order type (`PHASE0_INVERSION_TRUTH_V1.md` §6). |
| **the correct instrument already exists** | `src/research_infra/walkforward/quote_side.py:1032` `resolve_post_submission_m1_lifecycle` — fill gate at `:1291-1330`, `RESOLVED_NO_FILL` at `:1259-1266`, submission-bar censoring at `:1270-1276`, MARKET at the first complete successor open at `:1278-1290`. **No new machinery is needed for LIMIT; only STOP is missing.** |
| **standing rule** | any walk over a pool carrying `effective_order_type`, `distance_to_limit_risk` or `limit_marketable_at_decision` must either consume the sealed fill-aware label or route through the resolver. A hand-rolled `np.maximum.accumulate` over sidecar observations is the defect. |
| **detection test** | `barrier_clock_receipts/bcd_jan_decomposition.py` — run arms A/B/C and report A−C with a day-block interval; A−C ≉ 0 on the marketable control means the harness itself is wrong. |
| **first found** | attrition-recovery lane, 2026-08-12 (`ATTRITION_RECOVERY_V1.md` §2.2). Partially anticipated by Session T1's `t1_fill_axis.py` "fill gap" pass, which computed the quantity as a diagnostic and never registered it as a defect. |

### 4.1 How to detect this class

Three measurement-instrument defects surfaced in one day — the BID-archive quote side, the
1.5-vs-2.0 feature/label geometry, and now the barrier clock. All three sat inside numbers that had
been read many times, and all three are instances of one question:

> **Does the measured object exist, in the form measured, over the whole interval measured?**

The generalised test, in the order it is cheapest to run:

1. **Ask when the position began.** Walk the outcome and record the index at which the position
   *could first exist*. If any outcome resolves at or before that index, the instrument has
   lookahead. (Barrier clock: 25 % of rows resolved at index 0.)
2. **Ask what price was paid, and on which side of the book.** If the entry level is a level the
   generator *proposed* rather than a level the tape *transacted*, every excursion is measured from
   a fiction. (Quote side: entries and exits both resolved on a BID tape.)
3. **Ask whether the outcome vocabulary can express "nothing happened."** An instrument with no
   `NO_FILL`, no `CENSORED`, no `EXPIRED` state cannot represent an order that did not trade, so it
   will always report *something* — and that something is drawn from the favourable tail.
4. **Find the population the defect must NOT touch, and measure it.** Every real instrument defect
   has a control that must come out at zero. Marketable limits are the barrier clock's; they came
   out at +0.0031 [−0.0023, +0.0078]. If the control moves, the finding is something else.
5. **Compare the number against its own driftless bound.** A 6:1 contract cannot hit 52.8 % of the
   time. A ratio that is 1.5 on 632,934 of 632,934 rows while the order it describes is 2.0 on
   81,968 of 81,968 is not a coincidence either.
6. **Check whether a corrected instrument already exists in the tree.** In all three cases it did.
   The defect was never that the estate lacked the right walker; it was that a session hand-rolled
   a faster one and nobody diffed the two.

**The failure mode common to all three: exactness was mistaken for validity.** FB's cell was
certified *"5/5 claims VERIFIED, 0.0 deviation"* — a verification that the walk reproduced itself,
never that the walk described a trade.

---

## 5. TASK 2 item 6 — the training corruption, measured

`barrier_clock_receipts/bcd_training_corpus.py` → `BCD_TRAINING_CORPUS.json`, over the committed
`forward_shadow/FROZEN_TRAINING_CORPUS_V1.npz`.

| | value |
|---|---:|
| training rows | **284,652** |
| `proposed_order_type` | LIMIT 250,251 / MARKET 34,401 |
| resting (`limit_marketable_at_decision == False`) | 250,376 (87.96 %) |
| rows whose limit never filled, **trained at label 0.0** | **215,879 (75.84 %)** |
| E[y] all / LIMIT / MARKET | −0.02050 / −0.00916 / −0.10303 |
| E[y \| filled] LIMIT (n 34,372) / MARKET (n 34,401) | −0.06666 / −0.10303 |
| **rows carrying a barrier-clock outcome** | **0 (0.00 %)** |

The target is `terminal_net_r` from the fill-anchored resolver; `w21_predecision_ridge.resolved_eligible:240-246`
admits only rows whose `lifecycle_label_status` maps through
`probability_truth_analysis.RESOLVED_STATUS_TO_STATE:97-102`, and `RESOLVED_NO_FILL → NO_FILL` is a
*state*, not a rejection — `fit_shadow_ridge_model.py:170-172` reads
`float(row.get("terminal_net_r") or 0.0)`, so an unfilled limit trains at **0.0**. A barrier-clock
outcome is arithmetically unrepresentable in this corpus.

**So there is nothing to refit.** A refit on fill-anchored labels would return the identical model,
because the labels already are fill-anchored. This is a null result and it is a complete answer;
it strengthens Lane I rather than competing with it — the features carry no out-of-sample
directional information against labels that were never inflated in the first place.

**The genuine caveat, which is a different defect class and is filed here so it is not confused
with this one:** the model is trained on a population **conditioned on filling** for 86.26 % of its
LIMIT-family rows, and `distance_to_limit_risk` — the variable that governs whether a row fills —
is itself a model feature. That is a censoring/selection property, not a clock error, and it is not
assessed here.

---

## 6. What should happen next, ranked

1. **Nothing on the live book.** No armed figure moves. Do not re-price, re-size or re-arm anything
   on account of this defect.
2. **Do not quote CQ's inverted-breaker economics.** Its walker is decision-anchored on a 97.58 %
   resting family *and* its inverted contract is unmeasurable with the committed machinery. It is
   one of two candidates at the V27 tip; the other (CP's NY-metals-LONG) was not audited here.
3. **Audit the remaining sidecar walkers** — the phase-19 discovery set and `cs_breaker_folds.py` —
   with §4's detection test. Hours, not sessions.
4. **Apply the source corrections**: `ATTRITION_RECOVERY_V1.md` §6's reach sentence (§2.3 above),
   and add the fill-anchoring caveat to `current_ob_retest_geometry_candidate.py`'s docstring as
   that lane already prescribed.
5. **Classify by measured restingness, not by family name**, wherever the pool carries
   `distance_to_limit_risk` or `limit_marketable_at_decision`. Exact on the wave-21 corpus; 27.9 %
   short on the January one.

---

*Receipts: `barrier_clock_receipts/` — `bcd_sleeve_immunity.py`, `bcd_jan_decomposition.py`,
`bcd_sealed_label.py`, `bcd_wave21_census.py`, `bcd_training_corpus.py`, and the five JSON
artifacts they wrote. Every script is read-only and reproducible on this machine.*
