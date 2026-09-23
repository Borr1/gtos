# What the learning stack can and cannot be trusted to do today

**Session Z, 2026-07-29. Blocks B510–B539.** Companion to `SESSION_Z_TRAINER_AND_PARTITIONS_RESULT.md`.

Session R's headline is the standard this is written to: *"the live record says nothing about any
armed sleeve … closing the loop was necessary and it does nothing today."* The equivalent sentence
for the training end of the chain is:

> **The training path is now safe to run and there is nothing it can honestly be run on.** Making it
> safe was necessary; it produces no number today, and the reason is a missing capture, not a
> missing algorithm.

---

## 1. The stack, module by module

| module | state | trust today |
|---|---|---|
| `learned_edge_dataset_builder.py` | works; **fail-closed as of this session** | Builds a frame from per-day replay ledgers. Will now REFUSE SEALED / RESERVED_UNREAD / unpartitioned days instead of admitting them silently. |
| `trainer_partitions.py` | **new** | Answers "may this day be fitted on?" fail-closed. March 2026 unreachable. |
| `trainer_folds.py` | **new** | Purged, embargoed, expanding walk-forward. Replaces leave-one-day-out. |
| `learned_edge_trainer.py` | works; **rewired this session** | Fits three heads. Refuses frames without partition annotation or label spans. |
| `learned_edge_layer_v4.py` | works | Pure-Python scorer. Runtime consumer. |
| `learned_edge_walkforward_gate.py` | works | Separate admission gate for a trained artifact. |
| `validation_integrity/` (15 modules) | 94/94 green | Composable. **9 of 15 have no `src/` or `scripts/` consumer** — tests only. |

## 2. What is now TRUE that was not

1. **A leaking split cannot be produced silently by this path.** Purge on label spans, embargo
   measured from realised holds train-side-only, expanding walk-forward, and an independent
   `audit_fold_leakage` that re-derives the invariant and raises rather than warns.
2. **March 2026 cannot be fitted on.** Refused twice over — by its own `RESERVED_UNREAD` partition
   and by the `reserved_blackout`, which is checked before any partition and which no role can
   override. The hostile case is tested: a registry whose TRAIN range spans March still refuses it.
3. **An unclassified day is refused.** The single most consequential inversion of the old behaviour.
4. **The live trading period cannot become training data.** 2026-06-10 onward is `FORWARD`, and
   rolling forward days into TRAIN now requires a deliberate registry edit.

## 3. What is NOT true, and must not be claimed

### 3.1 No model has been trained, and none should be yet
No artifact was produced. `train_learned_edge_artifact` has never been run on real ledgers in this
session, only on synthetic fixtures.

### 3.2 The substrate is one day wide
Every measurement in this session used the S0R0 arm of the B7.5 route — **6,975 missed rows and 6
oracle rows, all on `trading_day` 2026-06-04.** A single day. The fold planner needs a calendar
span to cut folds over; one day yields zero folds by construction. **What exists on this machine
cannot train anything, and that is a data-availability fact, not a code defect.**

### 3.3 The trainer's label-shuffle canary cannot detect a fold-boundary leak
`_shuffle_canary` permutes outcome labels and requires AUC ≈ 0.5. That tests FEATURE→LABEL
leakage. It cannot test fold leakage, because shuffling destroys the day-clustering that the purge
exists to control — it would pass on a completely unpurged split. It was the only leakage control
the trainer had, and it was covering a different failure mode from the one that was open. The two
are now both present and are not substitutes; the artifact records this.

### 3.4 The 96 % / 19 % port-fidelity split still bounds everything downstream
Per-bar sleeves reproduce at 96 % live-recall; first-of-day sleeves at 19 %. Anything trained on
first-of-day candidates measures the port's bug. Session Y owns that repair.

### 3.5 DSR is being deflated against a FLOOR, not a measurement
`trial_budget_ledger.py` can build a trial-budget artifact but **has never been run**, and
`KNOWLEDGE_BASE/validation/SEALED_HOLDOUT_REGISTRY.json` does not exist. Every DSR call therefore
uses `DSR_TRIAL_FLOOR = 128` — a floor standing in for an unmeasured trial count. `spec.py:175-182`
says so in the field itself. A deflation against a floor is a lower bound on the correction, so it
is conservative in the right direction, but it is not a measurement and should not be reported as
one.

### 3.6 March is reserved, not pristine
22 March 2026 days were already fitted as TRAIN by the June route (B514). The B7.5 sealed replay is
unrun and protected; model fitting already happened. Do not describe March as untouched.

## 4. What would change the answer — named captures, in cost order

1. **A multi-day/multi-month ledger set on this machine.** The binding constraint. Everything else
   is downstream. Without a calendar span there are no folds.
2. **A trial-budget ledger.** Turns the DSR floor into a measurement.
3. **Session Y's first-of-day port repair.** Until then 7 candidate sleeves cannot be honestly
   evaluated at all.
4. **A broker-trading-day → (UTC start, UTC end) helper in `src/utils/`.** Does not exist. Both
   `trainer_folds` and the builder work around it with a conservative constant widening. Correct
   and fail-closed, but it purges slightly more than necessary and the workaround is duplicated.

## 5. Duplication this session did not resolve

**Five independent purge/embargo or chronological-split implementations exist in the tree**, on
four different data shapes. Ranked by risk of divergence:

| # | location | rule | shape |
|---|---|---|---|
| 1 | `trainer_folds.py` (this session) | measured embargo, label-span purge | frame row dicts |
| 2 | `walkforward/folds.py` (Session W) | same rule, held equal by test | `PricedTrade` |
| 3 | `validation_integrity/walk_forward_oos.py` | **row-index** folds, fraction-of-length embargo | `(date, float)` pairs |
| 4 | `wave4i_integration_partition_gate.py` | fixed 24h purge + 24h embargo | rows w/ `canonical_time_utc` |
| 5 | `validation_anti_overfit_v4.py` | fixed ±240-min band — **and it is config-wired live** | rows w/ `timestamp_utc` |

(1) and (2) are coupled by test. (3) is deliberately kept as an independent cross-check. **(4) and
(5) are unreviewed by this session** and (5) is referenced from `config/agent_config.yaml`, which
this session must not edit while FTMO is armed. Flagged, not fixed.
