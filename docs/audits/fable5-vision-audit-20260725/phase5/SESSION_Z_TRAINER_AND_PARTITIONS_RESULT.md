# Session Z — the trainer path, made unable to leak

**Blocks B510–B539. Branch `phase5/trainer-partitions`. Not merged.**

Companion: `LEARNING_STACK_TRUST_STATEMENT.md` (deliverable 3, read it second).

---

## 0. Headline

Three things were asked for. All three are delivered, and the most important finding is that the
brief's central claim is **true in mechanism and wrong in tense.**

1. **Trainer hygiene — per-fold specs, purge, embargo.** Delivered. The trainer had *none* of it:
   its folds were leave-one-day-out, so **every future day was in train**, with no purge and no
   embargo, under a docstring that claimed a 48-hour boundary.
2. **The partition registry, re-authored to fail closed.** Delivered, as **code** rather than a
   file, because sparse-checkout can make a file-based guard silently absent.
3. **What the learning stack can and cannot be trusted to do.** Delivered separately. Short version:
   the path is now safe to run and there is nothing on this machine to honestly run it on.

Plus the named defect: `regime_inflation.py` was **still broken on `main`** and is fixed here.

## 1. Where I disagreed with my prompt, and why

Per the working agreement §2, disagreements are stated in writing.

### 1.1 "A partition registry that marks March TRAIN … handing it to a builder burns the window"

**The mechanism is real. The tense is wrong: it already happened.** [MEASURED, B514]

- 22 March 2026 days were materialized as `partition_role: "TRAIN"`, `status: "completed"`, by the
  June v4 mechanical-edge route, and are **committed at HEAD** in
  `…/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/train_ledgers/ULTIMATE_EDGE_TRAIN_DAY_PROGRESS_LEDGER.jsonl`
  (234 rows, 2025-07-01..2026-05-29, TRAIN on every row, with per-day outcome fields).
- The **B7.5 sealed replay** of March is unrun and remains protected: no March arm artifact exists,
  and the window's `source_plan_digest_sha256` is `null`, so the runner fails closed.

These are different senses of "unread" and the programme's protected asset is the second one. A
correct registry therefore cannot protect March from a burn — it stops *further* consumption and
makes the prior consumption visible. It is recorded in a machine-readable
`Partition.prior_consumption` field rather than prose. **Whether the June fit disqualifies March as
a broad-family holdout is an owner/review judgment and I have not taken it.**

I did not read any March outcome value. Verification touched `trading_day`, `partition_role` and
`status` only, and the check script prints which keys it read.

### 1.2 "The B7.5 partition registry"

No such file exists — Session W said so first (B421) and it is confirmed. The only partition
registry in the repo belongs to the **June v4 mechanical-edge route** and is bound by neither B7.5
contract. B7.5's own artifacts assign March the *opposite* role. The hazard is nonetheless real
because the file's TRAIN range `["2025-06-02","2026-04-17"]` contains March **by range** — the
string `2026-03` appears nowhere in it, so it is invisible to grep.

### 1.3 "Do not build this from scratch before reading `validation_integrity/`"

Correct instruction, and I followed it, but the answer was mixed rather than "reuse it".

## 2. Deliverable 1 — trainer hygiene

### 2.1 What was wrong [MEASURED, B513]

`_train_head_with_oof` split folds as `fold_key != fold_day` / `fold_key == fold_day`. That is
leave-one-day-out. Consequences:

- **The future was in train.** Not a walk-forward under any definition.
- **No purge.** A 48h label horizon against day folds with a zero-day gap means a position entered
  on D−1 and closed on D+1 sat in train with its outcome set by price action inside the test day.
- **No embargo.** The registry doctrine stated one; nothing implemented it.
- **The scaler saw the test fold.** `_numeric_specs(rows)` was computed once over all rows and
  reused per fold, so standardisation means/stds and the 0.5 %/99.5 % clip bounds were fitted on
  out-of-fold data. Fixed: specs are now fitted per fold on train only.

### 2.2 The blocker that turned out not to be one [MEASURED, B515]

Purge needs each row's label-determination interval; the frame carried only `trading_day`. My first
reading of the ledger-writing code said the counterfactual close time was computed and discarded —
which would have made purge impossible for the risk-rejected and missed populations, i.e. the whole
justification for this builder, and would have been a clean negative.

**Measuring the real ledgers refuted that.** `counterfactual_order_close_time_utc` exists on the
missed ledger and `selected_policy_close_time_utc` on the oracle ledger. Headline coverage is 29.6 %
(2,065 of 6,975), which looks like a capture hole and is not: **4,909 of the 4,910 rows without a
close time are `not_filled_no_trade`** — the order never filled, so there is no close instant.
Coverage is 100 % wherever a close is defined. For never-filled rows the label resolves inside the
chunk (`chunk_day_count: 1`), so the span end is derivable.

Purge is fully implementable. The builder now emits `label_span_start_utc` / `label_span_end_utc` /
`label_span_status`.

### 2.3 Why the embargo is measured, and where I reused rather than rebuilt

The embargo is the p99 of realised holds **train-side only**, floored at 1 day — the rule Session W
derived, for the reason the brief gives: across twelve live sleeves the used-fraction of nominal
horizon runs 0.4 %–105 % with three sleeves exceeding theirs, so no nominal number is right.

**On reuse.** `walkforward/folds.py::assign_folds` implements exactly this and I did not call it,
deliberately: it requires `Sequence[PricedTrade]`, a frozen dataclass wrapping a `TradeRecord`
(`entry_utc`, `exit_utc`, `sl_distance_price > 0`, `entry_price`, `r_gross`, broker symbol) that is
constructed *only* by `price_trades()` through `src.costs.cost_r`. Trainer rows are flat frame dicts
with no cost model and no stop geometry. Manufacturing a fake `TradeRecord` to reuse the function
would be worse than a sibling implementation.

What I did instead: extracted the *rule* as a shape-free function `embargo_days_from_holds` and
**held it equal to W's by test** (`test_embargo_matches_walkforward_gate`), rather than asserting
the coupling in a comment. `walkforward/spec.py:58-61` records why that distinction matters.

`validation_integrity/walk_forward_oos.py` was also considered and not used as the primary: it cuts
on **row indices** with a fraction-of-series-length embargo, and its date key is never parsed. For a
leakage argument that is the wrong axis, which is the same conclusion W reached.

`build_fold_calendar(spec, span_start, span_end)` IS shape-free and reusable, and I did not call it
either — it needs a full `GateSpec` (fidelity register, pooling weights, admission thresholds) that
is meaningless for a trainer, and its blackout boundary push-out is redundant here because blackout
days never reach the frame. That is a judgment call and a reviewer may reasonably disagree.

## 3. Deliverable 2 — the partition registry

### 3.1 Why it is code

Sparse-checkout excludes most of `research/operations/`. A file there can be committed, absent from
the working tree, and leave `git status` clean. **A guard whose enforcement depends on a file that
may not be present is not a guard.** `DEFAULT_REGISTRY` cannot go missing, cannot de-hydrate to an
LFS pointer, and carries a digest that the frame header records.

### 3.2 The three fail-closed rules

1. A day covered by **no** partition is REFUSED. The old lookup returned `(None, None)` and the only
   downstream check was `role == "SEALED"`, so uncovered days passed.
2. A day inside `reserved_blackout` is refused **whatever role any partition assigns it** — checked
   before partitions, so a hostile TRAIN range spanning March still refuses March. Tested.
3. Only `TRAIN` / `TRAIN_DEVELOPMENT_GRADE` are trainable.

Overlapping ranges are rejected at construction. v1 resolved overlaps by **file order** in a linear
scan, so a day's role was a property of line ordering; a TRAIN row placed above an overlapping
SEALED row would have admitted sealed days.

### 3.3 How v2 was authored

By reconciling v1 (2026-06-10) against B7.5's decision contract (2026-07-16, later and controlling)
window by window, taking **the more restrictive disposition** wherever they disagree and recording
the override in a `supersedes` field. Genuine gaps are left uncovered on purpose — an uncovered day
is refused, and inventing a permissive partition to fill a gap is exactly v1's failure.
