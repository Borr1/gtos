# Session R — the learning loop, closed and live-aware

**Stage 5, learning lane. Branch `phase4/learning-lane`. Blocks B260–B289.**

Both claims in the session prompt were checked before anything was built on them. One is confirmed
by direct read; the other could not be checked from here and is carried as an unverified claim.

---

## 0. What this changes, in one paragraph

`recommend()` now consumes live realized evidence, and there is a producer that turns the live
book's closed positions into that evidence at broker truth. The rule is **default-off and
recommendation-only**, and the live half can only ever *brake*: it can down-weight or gate a
sleeve, and there is no path by which a live record raises a sleeve's weight. Run against the only
live record that exists, it says **nothing at all about the three armed sleeves, because none of
them has a single closed live position** — and it says so explicitly rather than by silence.

---

## 1. The two prompt claims

**Claim 1 — `recommend()` decides from backtest splits only. CONFIRMED [VERIFIED].**
`learning_actuator.py:65` calls `ev.evaluable_splits()`; `splits()` (`:45-47`) returns only
train/oos/sealed; `live_meanR` (`:42`) and `live_n` (`:43`) were declared and read nowhere in the
module. The prompt cited `:63` — that is the `def` line, the call is at `:65`. Immaterial.

**Claim 2 — the loop is observably open on the live host. NOT VERIFIED, and not verifiable from
here.** `daily_sleeve_outcomes` frozen at 2026-07-02, an empty
`owner_gated_learning_rerate_candidate_map`, and
`learning_rerate_application_status: proposal_only_not_applied_to_live_config` are VPS-side facts.
I never touch the VPS. Nothing in this session's design depends on them being true: the producer
reads an exported packet stream, and if the VPS state is different the same code reads the newer
export. Carried as `[UNVERIFIED — orchestrator-relayed]`.

**A third claim, inherited from CLAUDE.md §4 and cheaply measurable, was checked rather than
assumed** (agreement §3 item 6). The prompt says "the armed book is three sleeves" without naming
them. From `SURVIVOR_BOOK_V1.json` directly: FTMO survivors are `metals_core`, `crypto`,
`energy_agri`, `sub_xvol_pullback`; redacted_account's are `crypto`, `energy_agri`, `sub_xvol_pullback`,
`vp_euidx_pocgrav`. The intersection is exactly **`crypto`, `energy_agri`, `sub_xvol_pullback`** —
three, confirming Session Q's per-account finding and the count in the prompt. [MEASURED]

---

## 2. The evidence standard

The prompt is right that the design question is the standard, not the code. The answer has three
parts, and each is a property the tests defend.

### 2.1 Silence is never negative evidence

`live_n == 0` has **no effect whatsoever** — not a small effect, none. This is the trap the prompt
named and it is the single most dangerous failure mode available here: K's G4 measured
`metals_core` 0 fires from 990 invocations, `crypto` 0/440 and `energy_agri` 0/332 across the whole
38-day live window, all consistent with natural low frequency. A rule that read quiet as bad would
gate the entire armed book in its first two months.

### 2.2 Live evidence may only brake, never boost

`_apply_live` composes the two halves as `min(backtest, live_cap)`. Live evidence can lower the
recommended multiplier and can gate; it can never raise one. The best a live record can do is
decline to brake. This is what makes the asymmetry structural rather than a matter of threshold
choice — and it is why `idxrev`, which is **registry-falsified, gated on every split, and was the
only live-profitable sleeve in the live window (B63)**, stays gated: its live record is positive and
the rule correctly refuses to let that rescue it.

### 2.3 Gating is cheap, sizing is dear — by a measured margin

Live evidence may **support** a size-up only at `LIVE_MIN_N_SUPPORT` = 30 fills, the same bar as a
backtest split. It may **gate** far sooner, at a boundary derived from the sleeve's own cost-true
validated distribution rather than from a chosen constant.

The null is *"this sleeve is still behaving as its cost-true validation says"*: the next `n` live
R-multiples are draws from its validated per-trade R record (shape, from the W3/W5 stream caches),
relocated so the mean equals its broker-true claim (`SURVIVOR_BOOK_V1.json:net_r.n_horizon_mean`,
per account). Cumulative live R is tested against a sequential boundary
`b_n = n·claim − c·sd·√n`, with `c` solved so the probability that a **healthy** sleeve ever crosses
in its first 60 live trades equals a stated budget: 0.20 for down-weight, 0.02 for gate.

Measured result, worst case (every live fill a real measured stop-out of −1.01 R), against a
**day-block** null — `LIVE_EVIDENCE_CALIBRATION_V1.json`:

| sleeve (armed) | stop-outs to down-weight | to gate | fills to support a size-up |
|---|---:|---:|---:|
| `crypto` | 8 | 18 | 30 |
| `energy_agri` | 4 | 10 | 30 |
| `sub_xvol_pullback` | 6 | 14 | 30 |

Four to eight live losses move a sleeve down; thirty live fills are needed before live evidence can
help size one up. **Corrected twice — see §4.** The first version of this table said 3–4 and
"roughly 8×"; both numbers were wrong, in the same direction, for two independent reasons a refuter
found.

**And the standard's power is poor, which is published rather than buried.** If a sleeve's edge is
*entirely gone*, the probability it is gated within its first 60 live fills is **0.471** for
`crypto`, **0.330** for `energy_agri`, 0.753 for `sub_xvol_pullback` — and 0.002 for
`metals_softband`. A dead `energy_agri` is more likely than not to survive 60 live fills ungated.
That is a real limitation of a boundary this conservative, it is in the artifact as
`power_if_edge_gone`, and it is the strongest argument for the owner revisiting the two budgets.

A hard floor `LIVE_MIN_N = 3` sits underneath, independent of the artifact. A rule whose safety
rests entirely on an input file being correct is not safe — and §4 records why that is not a
hypothetical.

### 2.4 A fourth rule the prompt did not ask for: the cost-true veto

Running the rule surfaced a defect in it. `metals_softband` scores **SIZE_UP ×1.22** from its
every-split evidence, and the cost-true re-cost **kills it on both accounts**; `sub_mid_dn_revert`
scores ×1.23 and is likewise killed. The reason is that the rule's *backtest* half is the CP4/CP5
replay at the legacy cost map — the map F39 found had the wrong sign on tick erosion and F38 found
charged zero commission. Sizing a sleeve up on that basis, inside the system whose whole wave-3
finding was that the cost model was wrong, is the F38 failure mode wearing the learning system's
clothes.

So `cost_true_survivor=False` now vetoes any size-up. One-sided like the live stage: it never
rescues a gate. Its effect is visible per-account — `metals_core` stays SIZE_UP ×1.15 on FTMO,
where it is UNCONDITIONAL, and drops to KEEP ×1.00 on redacted_account, where broker-true carry makes it
CARRY_CONDITIONAL. Session Q's finding, mechanised.

The three CARRY_CONDITIONAL tiers are treated as **not** surviving, because they turn on a holding
time no cache records (CLAUDE.md §4).

---

## 3. The producer

`src/components/ultimate_book/live_evidence.py`, driven by `scripts/rerate_book_from_live.py`.

### 3.1 Reading realized cost, not modelling it — a stated departure from the brief

Stage 5 and the prompt both say to price realized outcomes "through Session J's cost layer". Taken
literally that is a step backwards for *realized* fills: the broker reports the commission, swap and
fee it actually charged, per deal, and a model of those numbers is strictly weaker evidence than the
numbers themselves. So the producer **reads** realized cost, and uses `cost_r` for the two jobs a
model is genuinely better at — **reconciliation** (the measured-cost-deviation tripwire Stage 3
wants) and **fallback** when a position's broker accounting is incomplete, with the coverage class
attached. What it never does is the third option, filling a missing cost with zero. Flagged per
agreement §2: this follows the prompt's intent (nothing computes a cost any other way) while
declining its literal instruction.

### 3.2 Realized R without lot volume

The packets carry no lot size, and R needs risk-in-cash at entry. It is recoverable exactly from the
position's own arithmetic: realized gross profit over the price distance travelled **is** the cash
value of one price unit for that lot.

```
cash_per_price_unit = aggregate_profit / ((exit_price − fill_price) · direction)
risk_cash           = |fill_price − fill_adjusted_stop| · cash_per_price_unit
realized_net_R      = realized_pnl / risk_cash
```

Cross-checked on the record: an SPX500 `idxrev` short returns **0.7472 R** by this derivation against
its own independently-recorded `broker_position_planned_target_r` of **0.75** — a field the
calculation never reads. [MEASURED]

### 3.3 What is admitted, and why the admitted set is not a fair sample

```
packet rows scanned      : 99,112
position_closed rows     : 151
admitted as realized R   :  50
refused:  61  no_broker_exit_deal_record_join
          40  incomplete_accounting_exit_deal_only_entry_commission_missing
```

**Only a third of the closed-position record is usable, and the unusable two-thirds are not random.**
Both refusal classes were corrected after refutation (§4):

- **61 rows lack the broker deal-record join.** They are *completed holds* —
  `trade_lifecycle_status == "closed"` on 61/61 — so the original reason string
  ("still_open_or_unreconciled") was wrong. The refusal is a **calendar block**, the same one as
  B215: before 2026-06-24, 1 of 60 closed rows joins; from 2026-06-24 on, 89 of 91. It is also
  **outcome-correlated** — all 8 `tp1_full_close` rows, winners by construction, are refused and
  none admitted. `ProducerReport.coverage_note()` publishes both facts.
- **40 rows carry exit-deal accounting only**, which omits entry commission. That is **70.8 %** of
  total commission on rows carrying both legs, and **100 %** on redacted_account, whose broker truth
  records `commission_charge_side: entry_only` — its 18 such rows report commission exactly 0.0.
  Understated cost makes a record look *better*, which makes the brake fire *later*: the fail-open
  direction, and F38 exactly. They are refused, not admitted-and-labelled.

### 3.4 Cost reconciliation

`cost_r`'s commission + swap against realized charges, over the 50 admitted fills: **mean absolute
error 0.00298 R**, worst 0.0479 R, all 50 at coverage `MEASURED`.

That figure is the *corrected* one. The first version reported 0.0203 R over 89 fills, which a
refuter decomposed into **0.00298 R where the accounting is complete and 0.0425 R where it is
not** — a 14× gap on the same symbols. The residual was a data-coverage artifact reported as model
error. With the incomplete rows refused, `cost_r` reproduces realized broker charges to three
decimal places, which is a genuine corroboration of Session J's layer rather than the tension the
first number implied.

---

## 4. What I got wrong and withdrew

Three defects I found myself, and **seven more that four refuters found**. Every one is a real
error; none is cosmetic. Publishing them is the point (agreement §7).

### Found before refutation

1. **The calibration's first threshold definition was `np.quantile`, and it would have gated the
   entire armed book on its first losing trade.** Per-trade R has a point mass at the stop (measured
   **35.9 %–71.4 %** of trades, not the "34–67 %" the first draft asserted). A quantile at small `n`
   lands inside that atom, so a routine stop-out read as a 1-in-200 event; the artifact reported
   `stop_outs_to_gate = 1` for **9 of 11 sleeves**.
2. **The correction to that was also wrong.** Fixing the atom still left `stop_outs_to_down_weight
   = 1` on six sleeves, and exposed the deeper error: a **per-n** α is not the error rate the system
   experiences, because the rule is re-evaluated after every fill.
3. **The cost reconciliation compared the wrong quantities** — `cost_r().total_r` (which includes
   spread and slippage, already inside the realized fill price) against realized commission + swap +
   fee. It reported 0.0993 R, 185× Session J's figure, and I read that as a real discrepancy before
   finding it was my own arithmetic.

### Found by refuters, and fixed

4. **The live brake evaporated above the calibration's `n_max`, and the rule was non-monotone.**
   The boundary was looked up at exactly `live_n` in a table ending at 60, so the **61st consecutive
   losing fill removed a gate the 60th had applied** — more adverse evidence, less adverse verdict,
   and no possibility of the gate ever firing again. Fixed: `boundaries_at()` evaluates the closed
   form beyond the table.
5. **The F38 cost guard tested for a string the producer cannot emit.** It refused SUPPORTING only
   on `coverage == "MODELLED"`; the producer emits only `MEASURED` or `PARTIAL_EXIT_DEAL_ONLY`. So
   the guard was dead code while `PARTIAL_EXIT_DEAL_ONLY` — *itself* the understated-cost direction —
   reached SUPPORTING, reading ~0.03 R/fill better than the same trades priced whole, on **15 of 17
   sleeve-rows** of the first receipt. Inverted to permit-only-`MEASURED`.
6. **The risk denominator used the trailed stop, which inflated R only on winners.** The fallback
   chain reached `broker_position_sl` — the *live* stop at close, after break-even and trailing
   moves. Measured: 5 winners with a denominator ratio below 0.9 (min 0.100) and **zero losers**;
   worst single row +0.878 R against a true +0.328 R; corpus mean inflated **+0.0278 R** with 82 %
   of it in five trailed winners. Excluded entirely; R is now taken from the entry-time pair.
7. **Incomplete-accounting rows were admitted and merely labelled.** See §3.3 — entry commission is
   70.8 % of the charge, 100 % on redacted_account. Now refused.
8. **The refusal reason string was factually wrong**, calling 61 completed holds "still open", and
   it hid a calendar block and an outcome correlation. See §3.3.
9. **The null assumed iid trades, and trades are not iid.** `sub_xvol_pullback`'s 90 trades sit on
   **33 dates** (up to 12 in one day, lag-1 ρ 0.511); `crypto` 104 on 67, ρ 0.441. Under a day-block
   null the delivered error budget was **2.1×–7.7×** the stated one. Rebuilt on a day-block
   resample; the iid rate is still published beside it as `attained_familywise_*_iid` so the size of
   the correction is visible.
10. **`stop_outs_to_*` charged a stop-out 13.4 nights of carry it never pays.** The relocation shift
    is 87–99 % swap at the modelled horizon, and applying it to the loss tail asserted a
    `metals_core` redacted_account stop-out loses −1.888 R on 1 R of risk. The artifact now also publishes
    `stop_outs_*_measured` against a **real** stop-out (−1.01 R, measured on the live record), and
    §2.3 quotes those. This is what moved the headline from "3–4" to 4–8.
11. **Per-account calibration differences were Monte-Carlo noise presented as structure.** One RNG
    was threaded through every cell; `c` is provably invariant to the location shift, so FTMO-vs-
    redacted_account differences (metals_core 2.805 vs 2.789) could only be noise, and one published
    figure flipped 6/7 across seeds. Now seeded per (account, sleeve) — and the two accounts now
    agree exactly, which is the truthful result.

### Refuted and NOT fixed — carried as stated limitations

12. **The calibrated quantity is first passage; the implemented rule is point-in-time.** The rule
    tests the boundary at the current `n`, so a crossing can *un-latch* if later fills recover.
    Latching it would make implemented and calibrated agree. Not done — it needs ordered per-fill
    evidence the current `SleeveEvidence` (a mean and a count) cannot carry, which is a shape change
    beyond this session. **Consequence: the true false-alarm rate is bounded by the calibration but
    the true detection behaviour is not exactly what was solved for.**
13. **`n_max = 60` is load-bearing for the error budget, not just a table length.** The same
    boundary extended runs 0.018 → 0.051 at n=1000: a constant-`c` √n boundary is not anytime-valid.
    At measured generation rates `crypto` reaches n=60 in ~1.7 years, so this does not bind soon,
    but the budget is a 60-fill budget and should be read as one.
14. **"Family-wise" is per sleeve per account.** Across the three armed sleeves the chance that *at
    least one healthy sleeve* is spuriously down-weighted is ~0.75, not 0.20. No multiplicity
    correction is applied.
15. **`metals_core` FTMO's surviving SIZE_UP ×1.15 rests on discarding its only negative split.**
    Its oos mean is −0.061 at n=24, excluded solely for falling under `MIN_N = 30`, so the
    "positive on every split" bar is met by dropping the one split that disagrees. It is armed on
    FTMO and the cost-true veto does not catch it (UNCONDITIONAL there). Pre-existing in the
    backtest rule, surfaced here, **not fixed** — changing `MIN_N` is a change to the standing rule
    that deserves its own decision.

## 5. What the rule says today, and what it would need

Run against the live record (`LIVE_RERATE_V1.json`), default-off:

- **All three armed sleeves: `live_n = 0`, live verdict `ABSENT`, no effect.** The live record covers
  12 sleeves and none of them is `crypto`, `energy_agri` or `sub_xvol_pullback`. The market-expansion
  crypto sleeves that *did* fire (`ny_crypto_momentum`, `orb_crypto_london`, `kz_london_crypto_low`)
  are different sleeves, not the core `crypto` sleeve under another name.
- The sleeves with live evidence are the ones OD-3 already killed: `idxrev` (11/13 fills, live
  positive, still gated on backtest), `fx_jpy`, `fx_jpy_ny`.
- **Nothing is actuated anywhere**, asserted in the runner rather than assumed.

**What it would need before it does anything at all** [PROJECTION, and on a weak input — the
`calibrated` column of K's G4 rests on a single control calibration that **K's own refuter withdrew**
(B171: "every P(0) built on it is unsound"). Treat the days as an order of magnitude, not a figure]:

| armed sleeve | fires/day | worst-case fills to down-weight | projected days to first possible action |
|---|---:|---:|---:|
| `crypto` | 0.098 | 6 | **~74** |
| `energy_agri` | 0.065 | 3 | **~60** |
| `sub_xvol_pullback` | — | 6 | **unknown — no measured generation rate** |

So: the learning loop is now closed, and on the armed book it cannot act for roughly **two months**
even in the worst case, because a 320-hour horizon means a fill produces no evidence until it
closes. `sub_xvol_pullback` is not in K's G4 measurement at all — a coverage gap, not a rate of zero.

**This is the honest headline: closing the loop was necessary and it does nothing today.** It was
still worth doing now rather than in two months, because the alternative is discovering at the first
drawdown that the thing meant to learn from it was never wired to the record — but it should not be
mistaken for a live safety mechanism on the armed account. It is not one, and nothing here should
be presented to the owner as one.

---

## 6. Boundaries respected

- **Default-off and recommendation-only.** `rerate_book(..., enabled=False)`; the runner asserts no
  recommendation is actuated. Nothing mutates a config, a broker, or a live namespace.
- **No VPS contact of any kind.** No broker-capable script was run.
- **H1 clear.** `learning_actuator.py`, the new `live_evidence.py`, `src/costs/` and everything else
  edited are **unbound** by the R2 decision contract (43 bound paths; membership checked before
  editing). `config/agent_config.yaml` **is** bound and was not touched.
- **Strategic decisions left to the owner.** Sleeve composition, the risk dial and the allocation
  profile are untouched. The two false-alarm budgets (0.20 / 0.02) are a *measurement policy* for a
  default-off recommender, published and regenerable in one command — but they are the closest thing
  here to an owner-shaped choice, and §7 flags them for confirmation.

---

## 7. For the owner / next session

1. **The carry basis is the owner decision here, and I picked one.** `CLAIM_KEY = "n_horizon_mean"`
   reads every claim at 13.369 nights of carry. It is the basis the survivor book's tiers were
   decided at, and it is the pessimistic end of the band CLAUDE.md §4 says is *precisely OD-3's open
   question*. **It produces all five verdict changes in the receipt**, and at `n0` three of the
   sleeves it kills are positive (`metals_softband` +0.334, `vp_euidx_pocgrav` +0.272,
   `sub_mid_dn_revert` +0.271). It is also in tension with this session's own producer, which
   measures a **median live hold of 1.26 h** — roughly `n0` territory. The artifact now publishes
   `carry_sensitivity` at all six bases so the choice is visible; re-running at `n0` is one command.
   This, not the false-alarm budgets, is the closest thing here to a strategic call, and it is
   Borhen's. *(Corrected: an earlier version of this section named the budgets, which changed
   nothing, and omitted the tier set, which changed everything.)*
2. **The two false-alarm budgets are the second dial.** `FAMILYWISE_DOWN = 0.20` and
   `FAMILYWISE_KILL = 0.02` set how often a healthy sleeve is spuriously down-weighted or gated over
   its first 60 live trades — and, through §2.3's power table, how often a dead one escapes.
   Regenerate with one command to move them.
3. **`sub_xvol_pullback` has no measured generation rate.** It is armed and it is the largest
   validated edge in the book (claim +1.14 R). Extending K's G4 to it is cheap and would complete
   the time-to-action picture.
4. **The rule's backtest half is still legacy-cost.** The cost-true veto contains the damage but does
   not fix it: there are no cost-true train/oos/sealed splits, only a pooled figure. Building them
   would let the rule reason about cost-true evidence directly instead of vetoing.
5. **The admission rate is a calendar artifact, not a standing rate.** An earlier version of this
   section warned that "40 % of closed packets lack a broker exit deal" would halve the learning
   rate. A refuter split it by date: before 2026-06-24 the join rate is 1.7 %, after it is 97.8 % —
   the same B215 break this repo already documents. **Withdrawn**; it is not a live concern. What
   *is* live is the entry-commission gap (§3.3), which is a per-account property, not a date one.
6. **`metals_core` FTMO is armed and its SIZE_UP survives only by discarding a negative split**
   (§4 item 15). Worth a decision before the rule is ever enabled.
