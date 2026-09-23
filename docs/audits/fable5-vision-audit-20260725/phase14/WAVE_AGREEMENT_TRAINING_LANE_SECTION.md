# Handoff to the orchestrator — the `§ Training lane` agreement section

**Merge the block below into the wave working agreement at the train**, replacing
`WAVE_11_WORKING_AGREEMENT.md` §6 (the pointer that says "Session CC's merge will replace this
pointer with the full section"). Written by Session CC, B2200–B2249. Everything in it is
machine-checked by `tests/research_infra/test_training_lane_protocol.py` — the section states
the rule, the test is what enforces it.

---

## § Training lane (ratified 2026-07-31, machinery landed wave 14)

`phase14/TRAINING_LANE_RATIFICATION.md` is the constitution; this section is what binds a
session. Operating manual: `phase14/TRAINER_SESSION_TEMPLATE.md`. Code:
`src/research_infra/training_lane/` and `trainer_partitions.SurfaceMap`.

**Two axes, two verbs. Do not read one for the other.** `Disposition.trainable` says whether a
model may be **FITTED** on a day; `SurfaceMap.surface_for_day` says whether the lane may
**ITERATE** against it. They disagree on purpose — January 2026 is `SEALED` on the first and
`VAL` on the second. `lane_disposition_for_day(day)` returns both together; use it whenever the
answer will be written down.

### The three surfaces

| surface | span | rule |
|---|---|---|
| **TRAIN** | 1992-02-18 … 2024-12-31 | iterate freely, **unbilled**. Every look still logged. |
| **VAL** | 2025-01-01 … 2026-05-31 | ranking and gradient checks only, unbilled, logged. **Used-once by survivor selection** (`d.year >= 2025`, `build_survivor_book.py:74` / `KB7_growth_kelly_sizing.py:130`) — the disclosure travels on every stamped row; headline expectancy is never quoted from VAL alone. |
| **TEST** | March 2026 + every blackout; the live forward stream from **2026-07-29** | **never trained on, never iterated against.** Sealed gate and live monitoring only. |
| *(uncovered)* | 2026-06-01 … 2026-07-28 | **refused.** A declared gap, not an oversight: already consumed by every full-history gate walk (`GateSpec.global_span` ends 2026-07-27), so it is neither virgin nor open. Opening it is an owner/orchestrator decision and the honest label would be TRAIN. |

Session CC tightened the ratified frame in five places and loosened it in none; the record is
`phase14/receipts/CC_CONTAMINATION_AUDIT_V1.json` → `tightenings_vs_the_ratified_frame`. The
load-bearing one: **the frame's "April's 15 sealed days" read as "April" would have opened
2026-04-16 … 04-30, fifteen days whose outcomes have never been read.** They are VAL.

### Logging — every look, immediately

`IterationLedger(session="XX").record(...)`, append-only, shared path
`phase14/receipts/TRAINING_LANE_ITERATION_LEDGER.jsonl`. You pass **dates**; the map computes
the surface stamp. Three things you cannot forge: the surface (computed, not accepted), the
verdict (`admitted`/`rejected` are the gate's words and raise), and `billed` (written `false`,
not a parameter).

A full-history walk declares `engine_reserved_blackout=[["2026-03-01","2026-03-31"]]` — spanning
March is not consuming it — and names the gap it crosses via `acknowledge_uncovered=`. Both
declarations land in the row. **TEST has no such escape hatch and never will.**

Log as you go, not at the end. An unlogged look cannot be graduated on.

### Billing — the one-bill rule

- **Iteration on TRAIN/VAL bills nothing.** The iteration ledger is a **sibling** of the DSR
  trial ledger, never a field on it: `measured_n_trials()` feeds DSR deflation, so lane looks
  written there would raise the estate's bill with every exploration. The two are reported side
  by side and never summed.
- **The family ratchet moves ONLY through `training_lane.graduation.graduate()`**, which bills
  **exactly one look**, atomically, with the candidate's provenance chain attached. It refuses:
  `provenance_missing`, `provenance_touches_test`, `provenance_spec_mismatch`,
  `declaration_lost_the_rule`, `unknown_family`. It is idempotent — a retry completes the
  receipt, it does not re-bill.
- **Every successor declaration goes into `candidate_family.DECLARATION_CHAIN` in the same
  commit.** `test_no_declaration_on_disk_supersedes_the_chain_head` goes red until it does.
  This is not bookkeeping: the chain was nine versions stale and the default resolved a **51 %
  under-bill** (35/32 against a true 53/50), in the permissive direction (B2204).
- **The sealed gate is FROZEN.** `CANDIDATE_BOOK_V1` basis, sealed `B_balanced` α = 0.10,
  RECORDED population with AN's conditions. Nothing in the lane changes what it takes to admit —
  it changes how cheaply we can search.

### Incubation

≤ **5 concurrent armed** incubants, each ≤ **0.05-class** confidence weight, each carrying a
pre-registered **stop** rule AND a pre-registered **promotion** rule with a `basis` naming the
artifact its threshold came from. Registering a dossier does not consume capacity; **arming**
does. Every transition needs an `OwnerCeremony` with who decided, when, and the receipt — rules
dated after the arming are refused as not-pre-registered.

`admission_basis` is `GRADUATED` (cite the graduation record) or `OWNER_RISK_ACCEPTED` (cite
the owner's decision). Both are legitimate and they are **not the same claim** — the estate has
one of each, and blurring them is how a risk-accepted sleeve gets quoted later as an admitted
one. Arming, pulling and promoting stay Borhen's ceremony every time.

### Language rules, binding

- **"dead" / "corpse" are BANNED** for any family whose repair paths have never run through the
  lane. The honest label is **`UNTESTED_UNDER_REPAIRS`**. January's four sealed arms ran the OLD
  engine — commission ≡ 0 (F38, confirmed by AW on all 28,519 rows), no spread-geometry floor,
  the pre-repair clocks and stops — and nobody has re-generated the broad family under the
  repaired stack. "Negative under a stack we have since repaired" is what the evidence supports;
  "dead" is not.
- **Never print a bare ADMIT** — "admits at N of 3 bands".
- **A VAL figure carries its used-once disclosure** into the prose, not only into the row.
- **A stop rule is a price, not a prediction**: `RISK_BOUND_not_inference`.
