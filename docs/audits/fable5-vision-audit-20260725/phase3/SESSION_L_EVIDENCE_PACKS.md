# Session L — Cheap evidence packs, and banking January

**Stage 1 item 1.4 + Stage 0 item 0.4.** Worktree `worktrees/wave3-evidence-packs-20260727`, branch
`phase3/evidence-packs`, from `main` @ `1e95fe7fa`. **Your block range is B130–B139.**

**Read `../WAVE_3_WORKING_AGREEMENT.md` first.**

---

## Why this session exists

Three owner decisions are currently stated as opinions and can be converted into measurements **for
seconds of compute each**, because the evidence is already banked: 99,112 runtime-learning packets over
38 unbroken days, and 1,754 recorded governor states. Session H scoped all three and ran out of session
before executing them.

This is the cheapest decision-value-per-hour in the entire plan. Take it seriously as economics, not as
cleanup.

## 1.4a — the dial-counterfactual grid

The 2.0 % nominal dial was **structurally unreachable** in the live fortnight: the highest confidence
that actually traded was 0.40, which caps at a 0.80 % unit. The dial choice explains **37.5 % of the
loss's magnitude and none of its sign** (B65).

So the question Borhen actually faces — *what dial should the activation candidate run at?* — has never
been answered with a counterfactual. Build the grid: replay the 38 days of packets across the dial
range and report P&L, max daily loss, max drawdown, and firm-rule breach proximity per dial, **per
account** (the two firms have different daily-reset clocks, B56/B58 — a dial that is safe under one
reset rule is not automatically safe under the other).

Runs in seconds per cell. Report the whole surface, not the argmax — and note explicitly that
optimising a dial on the same 38 days you measured is in-sample. **Working agreement §3.1 applies: the
grid ships with its null control.**

## 1.4b — the D1 shed A/B

The gross-cap shed is **first-fit**, and it has **zero live evidence** — nobody has measured whether
first-fit costs anything against the alternatives. You have 1,754 recorded governor states to A/B it
over. Compare first-fit against at least: smallest-first, largest-first, and worst-expectancy-first.

Report the distribution of outcomes, not just the mean. If they are indistinguishable, that is a
genuine and useful finding — it retires a defect from the register at zero cost.

## 1.4c — the D2 runtime-day-key MC

`bar_provider.decision_day_of` returns the **UTC** date and is the correlated-unit grouping key — it
drives the one-unit-per-cluster-per-day envelope that `book_owner.py:1608-1610` records the dial as
*certified on*. Re-keying it to the runtime/broker day changes risk bucketing, which is why it is an
owner decision (B54 Part 2) and why a test pins the current boundary.

**Do not change it.** Produce the MC pack that lets Borhen decide: under the runtime day key, how does
the risk envelope move? How many additional or fewer correlated units? What happens to worst-day?

**One reframing you must carry, because it changes the decision.** The certified envelope is
`one_unit_per_cluster_per_day`, and at HEAD it is **globally `false`** — verified,
`config/agent_config.yaml:1373`, with `jpy` in `cluster_cap_exempt_clusters`. So the live book is
*already* running outside the envelope the dial was certified on. The day-key question is therefore
downstream of a larger one: **should the certified envelope be re-imposed at all?** Quantify both.

## 0.4 — `JANUARY_BANK.md`

The B7.5 campaign is being parked (`THIRD_REVIEW.md` §6.2). Parking must not orphan what January
actually established. Bank the portable claims before the estate goes cold:

- **Sizing = `material_negative`** (−0.1105, crossing the sealed threshold). Convert this into a
  **standing design rule**: *no dynamic runtime sizing on any activation path without factorial-grade
  evidence.* Dynamic sizing multiplied accepted risk ~4.2–4.5× and maxDD ~8.8× **while making cash
  strictly worse**. That is worth more than the campaign that produced it.
- **Selection = inconclusive** (−0.049, inside the ±0.1 band). State precisely what "inconclusive"
  licenses and what it does not. It is **not** evidence that selection cannot work — the factorial
  probed a discrimination problem with two binary switches over a pool containing **+6,917 R of positive
  opportunity against −31,401 R of negative** across 28,520 rows. Four cells is two bits. Write that
  down carefully; it is the most misread number in the programme.
- **F31 restatement** (zero gap-through; −8.095 R lower bound across the sealed arms).
- **April = salvage-only**: 15 sealed days (B36, not "16 of 30"), **no partial credit**, no resume path
  — the runner refuses non-fresh output namespaces (`b7_5_post_acceleration_runner.py:292-315`) and
  hardcodes sub-window away on the sealed path (`:832`).
- **March stays outcome-unread.** Say so in the bank, with the reason: it is the only untouched month
  for any future broad-family treatment, and per working agreement §3.2 it is a budgeted resource.

**And record the condition on any future resumption**, because it is easy to lose: the pooled
promote/reject/inconclusive evaluator **does not exist anywhere** — verified, zero threshold keys in any
Python; the only artifact is `factor_or_policy_promotion_authorized: False` hardcoded in two analyzers.
The protocol seals the thresholds but **not the pooling weights**. Reading April without writing and
sealing that evaluator first would improvise the terminal decision after seeing the data.

## Deliverables — the floor

1. The dial-counterfactual grid, per account, with its null control and the in-sample caveat stated.
2. The D1 shed A/B over the 1,754 governor states, distributions not means.
3. The D2 day-key MC pack, with the cluster-cap-off reframing quantified.
4. `JANUARY_BANK.md`.
5. **Owner decision packets** for whatever your measurements settle — typed: decision / evidence /
   options / recommendation / explicitly-not-taken. You produce the measurement and the recommendation;
   Borhen decides. Do not land config changes.
6. `IMPLEMENTATION_STATE.md` blocks **B130–B139**, and a full-suite A/B by failure set, committed.

Commit scoped work as you go, push your branch, do not merge to `main`.
