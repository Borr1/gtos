# Session AE — the learning direction: the actuator now reasons from honest evidence, in both directions

**Wave 7. Branch `phase7/learning-direction`, from `main` at `066d552b0`. Blocks B850–B899. Not merged.**

**Scoped verification (agreement §2): 240 passed / 0 failed at HEAD across the named blast radius**
(§7). `tests/ultimate_book/` failure set at HEAD is **byte-identical to the merge-base**: 59 → 59,
0 regressed, **+27 net new passing**.

---

## 0. Headline

The lane R built could only ever subtract, and that was right while its backtest half was the
legacy-cost CP4/CP5 replay. It now reads AA's broker-true splits, and swapping the evidence
**changed the verdict on all seven sleeves the legacy constant covered** — including the one that
is armed with real money:

| sleeve | legacy CP4/CP5 | cost-true | armed |
|---|---|---|---|
| **`metals_core`** | SIZE_UP ×1.15 | **DOWN_WEIGHT ×0.50** | **FTMO** |
| `metals_softband` | SIZE_UP ×1.22 | KEEP ×1.00 | — |
| `sub_mid_dn_revert` | SIZE_UP ×1.23 | HOLD_FLAG ×1.00 | — |
| **`crypto`** | INSUFFICIENT_EVIDENCE | **SIZE_UP ×1.08** | FTMO + redacted_account |
| `fx_jpy` | HOLD_FLAG ×1.00 | GATE ×0.00 | — |
| `fx_jpy_ny` | DOWN_WEIGHT ×0.50 | GATE ×0.00 | — |
| `idxrev` | GATE ×0.00 | HOLD_FLAG ×1.00 | — |

Six of the seven move toward the broker-true re-cost. **The seventh moves away from it and it is
the module's own headline example** — §5 owns that.

Three sentences on the rest. The `cost_true_survivor` **veto is retired** and the property it
protected holds by construction on all 29 sleeves, asserted against the real artifact. Composition
is **bidirectional**: brake exactly as R built it, raise only at ≥30 fills across ≥30 distinct days
at fully measured cost, by one `LIVE_UP_STEP` per owner cycle, never above `MAX_UP` or his dial, and
never un-gating. R's two carried limitations — first-passage (item 12) and the family-wise budget
(item 14) — are **both fixed**, and fixing the second exposed a third defect nobody had recorded:
**V1's calibration could not be regenerated from its own generator.**

**Nothing actuates. The lane is default-off and recommendation-only, and no VPS, broker, or config
was touched.**

---

## 1. What the lane would recommend for the armed four, today

This is the §8-item-6 input. Default-off; these are recommendations, not changes.

**`live_n = 0` on every armed sleeve**, exactly as R found — the live record covers 12 sleeves and
none of them is one of these. Run against the full 99,112-row packet export, 50 admitted fills,
cost reconciliation 0.00298 R mean absolute error, all MEASURED. So every verdict below is the
**backtest half alone**, and the live column is what it would take to move it.

### FTMO — the armed four (`SURVIVOR_BOOK_V1.accounts.FTMO.survivors`)

| sleeve | verdict | × | train | oos | sealed | live brake: stop-outs to down / gate |
|---|---|---:|---|---|---|---|
| `crypto` | **SIZE_UP** | 1.08 | +0.243 (24t/14d) | **+0.078 (93t/73d)** | **+0.289 (64t/46d)** | 17 / 26 |
| `metals_core` | **DOWN_WEIGHT** | 0.50 | −0.444 (22t/17d) | **−0.205 (232t/118d)** | **+0.138 (126t/53d)** | 20 / 30 |
| `energy_agri` | INSUFFICIENT | 1.00 | −0.762 (13t/9d) | +0.331 (23t/15d) | +0.013 (13t/8d) | 9 / 14 |
| `sub_xvol_pullback` | INSUFFICIENT | 1.00 | −0.768 (6t/4d) | +0.482 (35t/19d) | +0.553 (37t/13d) | 13 / 20 |

**Bold splits clear the day-blocked sample floor; the others do not and are not scored.**
Trades / independent days. Brake column at the shipped `armed` family scope, in measured full
stop-outs (−1.01 R).

Read in one line each:

- **`crypto` is the only armed sleeve the lane would size up**, and modestly — its binding split is
  +0.0775 R/trade on 93 trades over 73 days, barely clear of the +0.05 materiality band.
- **`metals_core` is the one that inverted.** Its 232-trade / 118-day OOS is −0.205 at broker truth.
  It is armed on FTMO at confidence 1.00, the highest in the book.
- **`energy_agri` and `sub_xvol_pullback` are unmeasurable, not bad.** 67 trades on 34 days and
  88 on 36 respectively; nothing clears 30 independent days. The lane gives them no backtest-side
  protection at all — only the live brake can act on them, and neither has fired live yet.

### redacted_account (gated; its survivor set differs)

| sleeve | verdict | × | note |
|---|---|---:|---|
| `crypto` | SIZE_UP | 1.08 | same evidence, brake at 15 / 22 |
| `energy_agri` | INSUFFICIENT | 1.00 | same |
| `sub_xvol_pullback` | INSUFFICIENT | 1.00 | same |
| `vp_euidx_pocgrav` | INSUFFICIENT | 1.00 | **generates nothing** — omitted from the evidence, not scored as flat |

Receipt: `phase7/receipts/AE_ARMED_FOUR.json`, regenerable in one command.

---

## 2. What was built

### 2.1 Cost-true evidence in — `src/components/ultimate_book/cost_true_splits.py`

AA's `AA_SLEEVE_SPLITS_V1.json` is a **day series** with a walk-forward fold calendar, not three
means. The partition, from the folds and asserted disjoint at load for every sleeve:

- **train** = fold 1's `train_days` — the initial in-sample period, never tested against
- **oos** = the union of `test_days` over folds 1..N−1
- **sealed** = fold N's `test_days` — the freshest slice, out-of-sample for every earlier fit

`sealed` here means "the last forward fold", **not** a B7.5 sealed replay window and not the
trainer registry's `RESERVED_UNREAD`. Days in an embargo gap belong to no split and are dropped
(0 for 27 of 29 sleeves, 2 for `energy_agri`, 4 for `idxrev`).

29 sleeves instead of 7. `rerate_book_from_live.py`'s hand-carried `BACKTEST` constant is deleted;
it survives only inside `phase7/receipts/ae_owner_evidence.py` as the comparator that produced §0.

Three sleeves (`vp_euidx_pocgrav`, `mx_eu50_cash_*`, `mx_fra40_cash_*`) generated nothing and are
**omitted, not zero-filled** — a sleeve carrying `meanR 0.0` on `n=0` reads as a measured flat
result on every split, which is exactly what the every-split bar GATES. Unmeasured must not become
dead, and `vp_euidx_pocgrav` is redacted_account's fourth UNCONDITIONAL survivor.

### 2.2 The veto retired, its property kept

`cost_true_survivor is False → block any size-up` is gone. `cost_true_survivor` and
`cost_true_tier` remain as **reporting labels** and nothing keys off them — a test asserts that
identical evidence produces an identical verdict whatever the label says.

The property moved to `tests/ultimate_book/test_learning_actuator_cost_true.py`, where it is
asserted against the real artifact: **no sleeve whose broker-true tier is CARRY_CONDITIONAL or
DEAD_BEFORE_COST comes out above ×1.00**, checked over every (account, sleeve) pair. It holds by
construction. `metals_softband` — R's worked example, SIZE_UP ×1.22 on legacy splits and killed on
both accounts — reaches KEEP ×1.00 on cost-true ones, because its best admitted split is +0.0367,
under the rule's own +0.05 materiality band.

### 2.3 Day-blocked n, on both halves

`MIN_N = 30` is a sample floor, and 30 trades on 13 days is not 30 observations of anything. R
measured the clustering on this exact book (`sub_xvol_pullback` 90 trades on 33 dates with up to 12
in one day, lag-1 ρ 0.511; `crypto` 104 on 67, ρ 0.441) and applied the correction to the live
**null** only, leaving the admission floor counting raw trades. Because AA's artifact is a day
series, both halves can now be counted the same way — which is what FOURTH_REVIEW §4.2 means by
"live n ≥ 30 (day-blocked, **the same bar a backtest split must clear**)".

### 2.4 Bidirectional composition, at two speeds

`_apply_live` was `min(backtest, live_cap)`. Now:

- **Brake — unchanged, exactly as R built it.** 4–8 stop-outs against the calibrated boundary at
  R's scope; the kill boundary gates; a gate is terminal for that reading.
- **Raise — `SUPPORTING` only**, which means ≥30 fills **and** ≥30 distinct days **and** positive
  **and** inside the boundary **and** cost coverage exactly `MEASURED`. It lifts by at most
  `LIVE_UP_STEP = 0.05` above what the sleeve is **currently deployed at**, never above `MAX_UP`,
  never above `owner_dial_cap`, and **never un-gates** — `idxrev` stays gated on a live-positive
  record, which is a test.

The asymmetry is preserved because it is correct, and the code says why where the speeds diverge: a
false brake costs forgone profit and reverses on the next reading; a false raise adds size at the
moment a sleeve's recent record is flattering it, on a prop account whose drawdown limit is
absorbing, and no later re-rate reverses the loss it funds.

Reaching `MAX_UP` from an undisturbed 1.00 on live evidence alone therefore takes **five
owner-applied re-ratings**, each on a record that still clears the bar. A test walks the ladder.

### 2.5 First passage — R §4 item 12, fixed

R: *"the calibrated quantity is first passage; the implemented rule is point-in-time… it needs
ordered per-fill evidence the current `SleeveEvidence` cannot carry, which is a shape change beyond
this session."* This session is the shape change. `SleeveEvidence` carries `live_r_series` (ordered
by exit time) and `live_boundary_curve` (the boundary pair at every prefix), and the producer fills
both. A crossing **latches**: a path that dipped to −6.0 R at fill 4 and recovered to −2.0 R by
fill 6 is REFUTED_DOWN, where the endpoint test called it healthy.

A 300-path randomized property test asserts the latched verdict is **never milder** than the
endpoint one. The point-in-time path survives, labelled `live_evaluation: "point_in_time"`, for
callers that supply only a mean and a count.

### 2.6 The family-wise budget — R §4 item 14, fixed, and it costs something

`--family-scope` now names what the budget is a budget for. Bonferroni, not Šidák: the sleeves
trade overlapping symbols on overlapping days, so the union bound is the one that holds.

Shipped default **`armed`** (K = 8, the survivor cells across both accounts). The reasoning: a
multiplicity bill is owed on tests whose outcome can change something, and 14 of the 22 calibrated
cells cannot be actioned. `book` (K = 22) is available and is the conservative end. Union bound over
the armed cells is now exactly **0.20 / 0.02**.

**What it costs, on the FTMO armed four** (measured stop-outs to down-weight, and P(gating a
genuinely dead sleeve within 60 fills)):

| sleeve | `cell` (V1) | `armed` (shipped) | `book` |
|---|---|---|---|
| `crypto` | 8 → gate 18, P 0.475 | 17 → 26, P 0.255 | 21 → 29, P 0.188 |
| `energy_agri` | 4 → 10, P 0.327 | 9 → 14, P 0.145 | 11 → 16, P 0.096 |
| `metals_core` | 9 → 21, P 0.148 | 20 → 30, P 0.046 | 24 → 34, P 0.026 |
| `sub_xvol_pullback` | 6 → 13, P 0.755 | 13 → 20, P 0.536 | 16 → 23, P 0.449 |

The correction is paid for entirely out of an already-weak detector. **"Gating is cheap, sizing is
dear" still holds for every FTMO armed cell** (a test asserts it) and fails for 9 of 22 cells
overall — all published by name in `asymmetry_check`. The only armed cell where it fails is
`redacted_account/vp_euidx_pocgrav`, which generates nothing on a gated account.

### 2.7 A third defect, found while fixing the second: V1 was not reproducible

[MEASURED] V1's per-cell seed was `abs(hash((SEED, account, sleeve)))`. CPython salts `str.__hash__`
per process — three runs here gave **336168621, 1028826546, 3564764250** for the same cell. Every
re-run of the builder drew different paths and landed on different boundaries.

And **R §4 item 11's claim is false in the file it shipped**. It says the per-cell seeding made "the
two accounts now agree exactly, which is the truthful result". Seeding per *(account, sleeve)* gives
one sleeve's two accounts independent noise: of the 11 calibrated sleeves, **1** has both `c_down`
and `c_kill` identical across accounts (crypto 2.246469 vs 2.248893; metals_softband kill 3.478433
vs 3.457709).

Fixed by taking R's own argument one step further — `c` is provably invariant to the location shift,
so the two accounts' cells for one sleeve are *the same computation*: `blake2b(f"{SEED}|{sleeve}")`,
per **sleeve**. Result: **11/11 agree exactly**, two builds are byte-identical
(`f8e21f3510445abd…`), and each sleeve is simulated once instead of twice. V1 is left untouched on
disk. V2 lives under `docs/` because `research/operations/` is sparse-checkout-excluded.

### 2.8 §4.3 verified, and one residue fixed — `[VERIFIED]`

`regime_inflation.py` on `main` **is sound**, checked adversarially rather than by reading the diff:
swept the whole sign plane and the detector is monotone in the concealed loss in every regime.
`mean_all > 0` → the ratio *rises* toward the flag as the hidden loss deepens; `mean_all` crosses 0 →
`sign_flip_contamination` fires and the haircut goes to the floor; `mean_all == 0` → same. The
sign-adversarial case is in `test_vig_regime_inflation_sign.py` **as a property**, not an example
(`test_flag_is_monotone_in_the_concealed_loss`). `portfolio_contribution.certify_diversifier`'s
condition 1 takes `regime_clean` as a caller bool and `edge_factory.py:99` computes it as
`ri["contamination_flag"] is False` off the fixed module — so condition 1 does consume the fix.

**The prescription's letter was not followed and that was right.** §4.3 asked to "compare on signed
differences/effect sizes rather than a ratio of means". The shipped fix keeps `fwd_all_mean_ratio`
and guards its domain instead. That is a different mechanism, it closes the property, and it avoided
redefining a published field that five call sites read.

**Residue found and fixed (B873).** A *positive* history with a *losing* window (mean_all +0.22,
mean_win −0.10) was published as `inflation_basis: "ratio_of_positive_means"` — true of the
denominator only — with a verdict reading `"CLEAN: selection window is representative"` of a window
145 % below the history it is compared against. Branch on the window's sign first.
`contamination_flag` and `recommended_magnitude_haircut` key off the two sign predicates and not off
this field, so **no verdict moves**; a sweep over the sign plane asserts exactly that.

§4.3 is closed.

---

## 3. The two owner decisions, with numbers attached

Receipt: `phase7/receipts/AE_OWNER_DECISIONS.json`. **Evidence, not decisions.**

### 3.1 FOURTH_REVIEW §8 item 6 — the false-alarm budgets and the raise-side caps

Four things are his, and they are separable:

1. **The family the budget applies to.** `armed` (shipped), `book`, `account` or `cell`. §2.6 is the
   cost table. This is the consequential one: it moves the FTMO brake by a factor of ~2–2.5.
2. **The two budget numbers**, currently 0.20 down / 0.02 gate over 60 live fills. R published these
   and flagged them; they are unchanged here, only correctly scoped. Regenerate with one command.
3. **`LIVE_UP_STEP`**, i.e. how many of his own re-rate cycles a sleeve needs to reach `MAX_UP` on
   live evidence alone: 0.05 → **5 cycles** (shipped), 0.10 → 3, 0.25 → 1.
4. **`owner_dial_cap`**, which no recommendation may exceed whatever the evidence says. Default
   `MAX_UP` = 1.25, i.e. unchanged behaviour.

The honest frame for (1) and (2): **this brake is weak and the correction made it weaker.** At the
shipped scope a genuinely dead `metals_core` has a 4.6 % chance of being gated within its first 60
live fills, and `energy_agri` 14.5 %. That is not a reason to leave the budget mislabelled — it is
the reason the label had to be fixed before the number is set.

### 3.2 FOURTH_REVIEW §8 item 8 — the `MIN_N` rule (R §4 item 15)

**The instance is resolved by evidence, not by a rule.** R's worry was that `metals_core` FTMO's
SIZE_UP ×1.15 survived only by dropping its one negative split (oos −0.061 at n=24 < MIN_N). On
cost-true splits the negative is the **232-trade / 118-day OOS**, which no sample floor can discard,
and the sleeve is DOWN_WEIGHT ×0.50. Nothing needs deciding to fix that sleeve.

**The rule is still open, and here is the proposal with its measured cost.** If a split was dropped
for `n_eff < MIN_N` and its mean **disagrees in sign** with the admitted ones, cap the
recommendation at KEEP. One-sided: it can only ever remove a size-up; it cannot gate, down-weight or
rescue anything.

What it would change, measured over both evidence bases:

| basis | sleeves it touches | effect |
|---|---|---|
| **cost-true (29 sleeves)** | **none** | all four current size-ups (`crypto`, `vol_compression`, `mx_btcusd`, `mx_ethusd`) have no disagreeing dropped split |
| legacy CP4/CP5 (7 sleeves) | `metals_core` | ×1.146 → KEEP ×1.00 — exactly the case R named |

So it is **free today and it forecloses the recurrence**. That is the whole argument for it; it is
still his call, because it is a change to the standing rule.

---

## 4. What I got wrong and withdrew

**1. My own day-blocked floor was fail-open for the brake, and only measuring it showed that.**
I introduced the day-blocked sample floor to stop concentrated evidence buying a size-up. Over the
29 sleeves it moved exactly two verdicts and they went in **opposite** directions:

- `sub_xvol_pullback` SIZE_UP ×1.25 → INSUFFICIENT_EVIDENCE. Intended and correct.
- `kz_london_crypto_low` **GATE ×0.00 → INSUFFICIENT_EVIDENCE**. Not correct. It is negative on all
  three cost-true splits and only its 167-day OOS clears 30 independent days, so a symmetric floor
  *withdrew a brake* because the evidence was day-thin.

Fixed by making the floor asymmetric like everything else in the module: a size-up must clear the
day-blocked floor, a brake may fire off the looser trade-count floor, and `recommend()` returns
`min()` of the two. A test asserts the property over every sleeve rather than the two examples. I
report this because I shipped the defect and the fix in the same session and the first version was
committed.

**2. The seed constant in my own test was wrong on the first write** — I pinned a guessed value and
the test caught it. Left as-is in the history; it is the test doing its job.

**3. One thing in the prompt I did not do as written.** The prompt says the raise bar is "live
n ≥ 30 day-blocked (the same bar a backtest split must clear)". Taken literally with the backtest
bar left at 30 *trades*, those are not the same bar. I made both sides day-blocked, which is the
reading that makes the parenthetical true, and it is the change with the widest blast radius in this
session — it is what moves `sub_xvol_pullback` off a size-up. Flagged per agreement §1.

---

## 5. What is now worse, stated plainly

**`idxrev` moved from GATE to HOLD_FLAG, and the module's own docstring uses it as the reason the
module exists.** Legacy splits were negative on all three; cost-true splits are −0.0243 / −0.0124 /
**+0.0079**, and a sealed mean of +0.0079 on n = 1145 breaks the every-split sign test.

The defect is in the **rule**, not the evidence: `every_neg` is a bare `all(m <= 0.0)` sign test with
no materiality band, while `every_pos` requires `worst >= +0.05`. A mean four orders of magnitude
below a stop-out flips a gate into a flag.

I did not add a symmetric band. Changing a threshold in the standing rule to restore a verdict I
preferred is exactly the failure this programme exists to avoid, and the band's width is a real
choice with book-wide consequences. It is a repair-queue row (`idxrev`, `EVIDENCE_BASIS`) and an
owner-facing proposal. Two things bound the damage meanwhile: HOLD_FLAG is ×1.00, so nothing is
sized up; and `idxrev` is `DEAD_BEFORE_COST` in the survivor book and not in either armed set.

**A second disagreement worth an owner's eye:** the lane GATEs `fx_jpy` and `fx_jpy_ny` on cost-true
splits (negative on all three, 3,984 and 1,620 trades) while `SURVIVOR_BOOK_V1` tiers them
`MEASURED_LIVE_CARRY` and `CARRY_CONDITIONAL_LIVE_SUPPORTED` — *surviving* tiers. Both artifacts are
cost-true; they are different populations (full archive vs the cached validation stream) with
different exit assumptions. Neither should be quoted as "the sleeve's economics" until they are
reconciled. Two repair rows.

---

## 6. Repair-queue rows (session `AE`)

**11 rows appended** beside AA's 87, tagged `session: "AE"`, via
`phase7/receipts/ae_repair_rows.py` (idempotent; AA's rows and AA's `summary` block untouched).
A durable standalone copy is at `phase7/receipts/AE_REPAIR_QUEUE_ROWS.json`, because
`REPAIR_QUEUE_V1.json` regenerates from `aa_estate_walk.py` and a regeneration would drop appended
rows silently.

`metals_core`, `crypto`, `sub_xvol_pullback`, `energy_agri`, `idxrev`, `fx_jpy`, `fx_jpy_ny`,
`metals_softband`, `sub_mid_dn_revert`, `kz_london_crypto_low`, `vp_euidx_pocgrav` — one new
prescription class, `EVIDENCE_BASIS`, plus `SAMPLE_EXTENSION`, `COST_GEOMETRY` and `GENERATION` from
AA's existing vocabulary.

---

## 7. Verification — the named blast radius (agreement §2)

**Scope.** Tests I added, plus every test importing a module I changed:

```
tests/ultimate_book/test_learning_actuator.py                  tests/research_infra/test_vig_regime_inflation.py
tests/ultimate_book/test_learning_actuator_live.py             tests/research_infra/test_vig_regime_inflation_sign.py
tests/ultimate_book/test_learning_actuator_cost_true.py  (new) tests/research_infra/test_vig_portfolio_contribution.py
tests/ultimate_book/test_live_evidence.py                      tests/research_infra/test_walkforward_diversifier.py
tests/ultimate_book/test_live_evidence_calibration_v2.py (new) tests/research_infra/test_validation_integrity_gauntlet.py
tests/research_infra/test_regime_spine_trials.py               tests/research_infra/test_walkforward_gate.py
tests/research_infra/test_vig_trial_budget.py                  tests/research_infra/test_wf_diagnostics.py
tests/research_infra/test_vig_trial_ledger_prospective.py      tests/research_infra/test_walkforward_book_replay.py
tests/research_infra/test_learned_edge_walkforward_gate.py     tests/research_infra/test_gate_filter_selector_evidence.py
```

plus `tests/test_implementation_state_block_citations.py`, in scope because I appended blocks.
The last three research_infra files are in scope because I appended 164 rows to the shared trial
ledger and they read it.

```
$ python3 -m pytest <all 19 files> -q -p no:randomly
240 passed, 1 warning in 19.71s
```

**Zero failures in the 18-file scope, so nothing there was suspicious and no base re-run was needed
(agreement §2 item 3).** For the record, the pre-existing subset was measured green at the
merge-base before any edit: 49 passed (the three `ultimate_book` files) + 26 passed (five
`research_infra` files).

**The citation guard did need a base run, and it found two things — one mine, one not.** It went red
at HEAD, so I ran the same file at `066d552b0`:

| test | base | HEAD before fix | cause |
|---|---|---|---|
| `test_no_new_dangling_block_citations` | pass | **fail** | **mine.** Landing B850+ pushed the ceiling past AD's `B750–B799` and AF's `B800–B849`, both cited in the wave-7 agreement and both unwritten on sibling branches, so two correct forward references became dangling. |
| `test_the_in_flight_wave_range_is_declared_and_shrinking` | **fail** | fail | **pre-existing at the merge-base.** AA's `B600–B649` entry in `IN_FLIGHT_WAVE_RANGES` was dead — every block in it sits below the ceiling, so it exempted nothing. |

`IN_FLIGHT_WAVE_RANGES` exists for exactly the first case and its docstring says *"whoever raises
the ceiling owns this list"*. AD's and AF's ranges are declared; AA's dead entry is dropped in the
same edit, which fixes the pre-existing failure too. **8 passed.**

**Whole-directory set diff, `tests/ultimate_book/`** — run because I changed a module the whole
directory imports:

| | merge-base `066d552b0` | HEAD |
|---|---|---|
| failed | 59 | 59 |
| passed | 669 | 696 |

`diff` of the two sorted FAILED lists: **empty. The failure sets are byte-identical — 0 regressed,
0 fixed, +27 net new passing.** All 59 are the pre-existing `market_expansion` /
`rolling_stress` / `wave_c_manifest` families, none of which this session touches.

**H1.** `learning_actuator.py`, `live_evidence.py`, the new `cost_true_splits.py`,
`rerate_book_from_live.py`, `build_live_evidence_calibration.py`, `regime_inflation.py` and
`portfolio_contribution.py` are **all unbound** by the R2 decision contract (checked by path
membership before editing). `config/agent_config.yaml` is bound and was not touched.

**Trial ledger.** 164 variants per run appended with `session: "AE"` — every family scope × cell,
both admission floors × 29 sleeves, both evidence bases × 7 sleeves, the three `LIVE_UP_STEP`
candidates, and every `MIN_N`-rule application. The generator was run twice during the session, so
the ledger carries **328 AE rows for 164 distinct variants**; the ledger's own schema counts *look
events*, not hypotheses, and two looks at one variant is honestly two looks. Total 1,971.

---

## 8. Boundaries respected

- **Default-off and recommendation-only** throughout. `rerate_book(..., enabled=False)`; the runner
  asserts no recommendation is actuated and additionally asserts the cost-true tripwire on every
  run. Nothing mutates a config, a broker, or a live namespace.
- **No VPS contact of any kind. No broker-capable script was run.** The packet stream was read from
  the read-only 2026-07-25 export on this machine.
- **`config/agent_config.yaml` untouched** — the FTMO activation token binds its digest.
- **Strategic calls left to Borhen**: the family scope, the two budgets, `LIVE_UP_STEP`, the dial,
  the `MIN_N` rule, the materiality band `idxrev` needs, and sleeve composition. All are queued in
  §3 and §5 with the numbers that would let him decide.
- **Not merged.** Branch `phase7/learning-direction`, four scoped commits.

---

## 9. Artifacts

| path | what |
|---|---|
| `src/components/ultimate_book/cost_true_splits.py` | the loader (new) |
| `src/components/ultimate_book/learning_actuator.py` | the rule: veto out, day-blocked floor, bidirectional composition, first passage |
| `src/components/ultimate_book/live_evidence.py` | producer: ordered series, boundary curve, day blocks, V2-first calibration chain |
| `scripts/build_live_evidence_calibration.py` | `--family-scope`, deterministic seeding, sensitivity table |
| `scripts/rerate_book_from_live.py` | reads the cost-true loader; `--owner-dial-cap`; runs without packets |
| `phase7/receipts/LIVE_EVIDENCE_CALIBRATION_V2.json` | the calibration of record |
| `phase7/receipts/AE_ARMED_FOUR.json` | §1's table |
| `phase7/receipts/AE_LEGACY_VS_COST_TRUE.json` | §0's table |
| `phase7/receipts/AE_ADMISSION_FLOOR.json` | day-blocked vs raw-trade n, 29 sleeves |
| `phase7/receipts/AE_OWNER_DECISIONS.json` | §3 |
| `phase7/receipts/AE_LIVE_RERATE_V2.json` | the full lane against the 99,112-row packet export |
| `phase7/receipts/AE_REPAIR_QUEUE_ROWS.json` | §6, durable copy |
| `phase7/receipts/ae_owner_evidence.py`, `ae_repair_rows.py` | the generators |
