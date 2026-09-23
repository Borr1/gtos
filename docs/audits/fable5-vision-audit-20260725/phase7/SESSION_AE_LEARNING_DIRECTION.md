# Session AE — the learning direction: rebuild the actuator's evidence, then let it move both ways

**Wave 7.** Worktree `worktrees/wave7-learning-direction-20260730`, branch
`phase7/learning-direction`, from `main`. **Blocks B850–B899.**

**Read `../WAVE_7_WORKING_AGREEMENT.md` in full first** — the verification policy changed —
then `FOURTH_REVIEW.md` §4.2 and §1.5, then Session R's result
(`../phase4/SESSION_R_LEARNING_LANE_RESULT.md`), then AA's result §4 (your input is named
there).

---

## The mission

The learning loop R built is closed, live-aware, and can only ever subtract. That was the
correct containment while its backtest half was the legacy-cost CP4/CP5 replay — the exact
cost model F38/F39 discredited. AA has now produced the honest replacement:
`../phase6/receipts/AA_SLEEVE_SPLITS_V1.json` — 29 sleeves of cost-true train/OOS/sealed
day-series at broker truth, with the fold calendar and per-day cost components. Your job is
§4.2, in dependency order, so that when Borhen flips the lane on it can recognize live
evidence in **both** directions.

## The work, in dependency order

**1. Cost-true evidence in.** `learning_actuator.py`'s backtest half reads AA's splits
instead of the legacy-cost CP4/CP5 splits. Then retire the `cost_true_survivor=False` veto at
`learning_actuator.py:242` — it was a bolt-on containing legacy-cost damage; once the
evidence itself is cost-true the patch has nothing left to contain. Keep its *test* as a
regression tripwire on the new path (the property it protected — "no size-up on
cost-discredited evidence" — must now hold by construction, and the test should prove it
does).

**2. Bidirectional composition with asymmetric speed.** `_apply_live`
(`learning_actuator.py:226-264`) takes `cap = _live_stage(ev)` and applies it only downward,
so live evidence can never lift a sleeve above its backtest half. Replace with the rule
FOURTH_REVIEW §4.2 specifies: **brake fast** — 4–8 stop-outs against the day-blocked
boundary, exactly as R built it, untouched; **raise slow** — only on live n ≥ 30 day-blocked
(the same bar a backtest split must clear), capped per re-rate cycle (`MAX_UP` stays the
ceiling), never above the owner's dial. The asymmetry is preserved because it is correct,
not because it is timid — say that in the code where the speeds diverge.

**3. Fix while inside** (both named by R, neither fixed, both cheap now the shape changes):
- the per-sleeve-per-account "family-wise" false-alarm budget that is actually ~0.75 across
  the book (R §4 item 14);
- the first-passage / point-in-time mismatch (R §4 item 12).

**4. Verify §4.3 landed.** `regime_inflation.py`'s sign defect was fixed by X and Z with a
hand-merge that needed the tests to catch 5 `NameError`s (B518 and the wave-6 agreement §4
item 3 record the history). Verify the module on `main` is now sound — signed
differences/effect sizes, the sign-adversarial case in tests, and
`portfolio_contribution.py`'s condition 1 consuming the fixed module. If residue remains, fix
it here; if it is sound, one `[VERIFIED]` block saying so closes §4.3 for the programme.

**5. Prepare the two owner decisions your lane feeds** (`FOURTH_REVIEW.md` §8 items 6 and 8)
— evidence, not decisions:
- R's two false-alarm budgets and the raise-side caps, restated against the cost-true
  evidence so Borhen sets numbers once, on honest inputs;
- `metals_core`-FTMO's SIZE_UP dependency (R §4 item 15: it survives only by discarding its
  one negative split) — propose the `MIN_N` rule with the cost-true splits in hand; the rule
  is his call before the lane is ever enabled.

**The lane stays default-off and recommendation-only throughout.** What changes is what it
would say, and that it can say it in both directions.

## Constraints specific to this lane

- **The live-evidence reader is live-load-bearing in spirit**: it reads the same packet
  stream the armed book emits. Behavioural tests over source-string assertions, and A/B your
  changed modules' test scope against base per the agreement §2.
- H1: `learning_actuator.py` and the validation_integrity surface were verified unbound by R
  and W — re-check membership on anything else you touch under `src/`.
- Every threshold/variant you evaluate while re-deriving budgets goes to the trial ledger.

## Deliverables

1. The rewired actuator, tests green in scope, with the veto retired and the raise path
   capped as specified.
2. `phase7/SESSION_AE_LEARNING_DIRECTION_RESULT.md` — including what the lane would
   *currently recommend* for the armed four on the cost-true evidence, as a table Borhen can
   read in one minute (that is the §8-item-6 input).
3. Repair-queue rows appended (session `AE`) where your work changes a sleeve's evidence
   basis.
4. Blocks B850–B899 appended to `IMPLEMENTATION_STATE.md`.

## Not yours

The VPS. Flipping the lane on. The budgets' final numbers, the dial, sleeve composition.
Merging to `main`. `config/agent_config.yaml`.

Use your own judgment on scope and on whether anything above is wrong — and say so in your
report when you do.
