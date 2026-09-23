# Session R — close the learning loop before the fills arrive

**Stage 5, learning lane.** Worktree `worktrees/wave4-learning-lane-20260729`, branch
`phase4/learning-lane`, from `main`. **Blocks B260–B289.**

**Read `../WAVE_4_WORKING_AGREEMENT.md` first** — especially §3, which lists what the orchestrator's
prompts got wrong last wave. Assume the same failure modes are in this one.

---

## Why this is urgent rather than merely queued

**A live funded FTMO account is being armed on three sleeves while you work.** Realized P&L starts
flowing within days. And the thing that is supposed to learn from it cannot see it.

Two measurements, both checkable in minutes — **verify both before you build anything on them**:

1. **`recommend()` decides re-rating from backtest splits only.**
   `src/components/ultimate_book/learning_actuator.py:63` takes `ev.evaluable_splits()`.
   `SleeveEvidence` declares `live_meanR` (`:42`) and `live_n` (`:43`) and **`recommend()` never
   reads either.** Confirm by reading `:63-97`.
2. **The loop is observably open on the live host.** A read-only VPS inspection on 2026-07-29 found
   `daily_sleeve_outcomes` frozen at **2026-07-02**, `owner_gated_learning_rerate_candidate_map`
   **empty (0 keys)**, and `learning_rerate_application_status:
   proposal_only_not_applied_to_live_config` — while sleeves still emit 25–43 shadow intents a
   trading day. [Orchestrator-relayed, VPS-side, **not independently verified by you** — treat as a
   claim. You cannot reach the VPS; if you need it confirmed, say so and it will be fetched.]

So arming does not close the loop. Fills will produce realized P&L and the learning rule will keep
recommending from 2026-era backtest splits. **That is the charter's whole compounding mechanism sitting
disconnected**, and it is a ~20-line extension plus a producer.

## What you own

**1. Make `recommend()` consume live evidence.** The third review sized it at ~20 lines. The design
question is not the code, it is **the evidence standard**: how many live fills before live evidence
is allowed to move a sleeve's weight, and does live evidence *override* backtest splits, sit
alongside them as another split, or only ever gate downward?

The existing rule has an answer worth preserving — `MIN_N`, the every-split bar, `GATE_MULT`,
`FLOOR_MULT`, `MAX_UP`, and a default-off `enabled` flag. **The June run's refusal to act was the gate
working correctly, not a bug.** Extend that discipline to live evidence; do not bolt on a second,
looser standard. Whatever you choose, the asymmetry that matters is that **a handful of live losses
should be able to gate a sleeve long before a handful of live wins can size one up.**

**2. Build the book-lane rerate producer.** Stage 5 puts it at ~1 AS, *"once Stage 1 gives it
cost-true inputs"* — Stage 1 is now complete, which is what unblocks you. It should read realized
outcomes, price them through **Session J's cost layer** (`src/costs/`, `cost_r(...)`,
`BROKER_TRUE_COSTS_V1.json`) rather than any other cost path, and emit per-sleeve evidence in the
shape `recommend()` consumes.

**Nothing downstream may compute a cost any other way.** F38 is the reason: the shipped model charged
zero commission at five sites and the whole 2015–2026 validation rested on it. If `cost_r` cannot
answer for a symbol, that is a **coverage fact to publish**, not a gap to fill with a plausible number.

**3. Default-off, recommendation-only, and it must stay that way.** `rerate_book(..., enabled=False)`
is the current contract. Actuation is an owner decision. Your job is to make the recommendation
*correct and live-aware*, not to let it act.

## Three traps specific to this work

- **Survivorship.** The armed book is three sleeves. Sleeves that never fire produce no evidence, and
  "no evidence" must not read as "negative evidence". K's G4 measured `metals_core` 0 fires from 990
  invocations, `crypto` 0/440, `energy_agri` 0/332 across 38 days — **all natural low frequency**,
  with empirical P(zero in a 38-day window) of 0.369 / 0.284 / 0.638 respectively and **0.075 for
  five silent together**. A rule that gates a sleeve for being quiet would gate the entire book in its
  first two months.
- **The live window is not a clean sample.** 88.5 % of core-8's confidence weight is unmeasured by
  the only live window that exists (B63/B99b); the measured 11.5 % split JPY-negative and
  `idxrev`-positive. And **the status field did not predict live sign** — `idxrev` is registry-falsified
  and was the only live-profitable sleeve (B63).
- **Cost-true means broker-true.** Realized commission+swap was 31.6 % of the live W7 loss. A rerate
  computed on gross R would re-learn the exact error F38 encoded.

## What good looks like

A future session can ask *"what does the live record say about each armed sleeve, priced at broker
truth, at what evidence class, and would it move the weight?"* — and get an answer from committed code
rather than a bespoke analysis. State plainly what your rule would do **today** on the existing live
record, and what it would need before it would do anything at all.

## Method

Commission refuters, tell them to default to "refuted", give them distinct lenses. Every wave-3 session
that did this had real errors found — see the agreement §7 for four specific cases, including one
where a session built the exact defect it was sent to prevent. Publish what they overturn rather than
quietly amending.

Use your own judgment on scope, method, the evidence standard, and on whether anything above is wrong.
