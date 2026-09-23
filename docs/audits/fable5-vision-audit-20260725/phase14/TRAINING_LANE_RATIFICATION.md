# The Training Lane — ratified 2026-07-31

**Owner decision, Borhen, 2026-07-31: "i give explicit approval, please proceed as proposed
with the training lane."** This document is the record of what was proposed and approved, and
the constitution the lane's builders implement. Session CC turns it into code and tests;
Sessions CB and CD build its engine and run its first regeneration. Where this document and a
measured fact disagree, the builder records the disagreement in writing and the more
restrictive disposition wins until the orchestrator resolves it (Session Z's rule).

## 1. Why (the four concessions — the evidence is already written)

1. **We built a verdict machine, not a training loop.** Near-miss candidates get filed with a
   p-value and never iterated. The repair queue holds gradients nobody descends. The estate's
   own record shows iteration works: AW's spread-geometry dividend, AQ's contract repair (a
   REJECT at p 0.0564 became the estate's only ADMIT at 0.0011 — *both repairs at once*), AK's
   exit frontiers. Every one was found as a side effect of verdict work.
2. **Multiplicity billing leaked backward into exploration.** AW paid a 486-look family bill
   for what was research triage. Billing belongs at ONE point: graduation to the sealed gate.
3. **January's negative was never a family verdict.** The four sealed arms ran the OLD engine —
   commission ≡ 0 (F38, confirmed by AW on all 28,519 rows), no spread-geometry floor, the
   pre-repair clocks and stops. Nobody has ever re-generated the broad family under the
   repaired stack. Language rule, binding: **"dead"/"corpse" is banned** for any family whose
   repair paths never ran through the lane — the honest label is `UNTESTED_UNDER_REPAIRS`.
4. **AX's 1.06× was the orchestrator's wrong acceptance test** — provenance-identity forced
   keeping the 52M-call hash loop and the evidence accumulation. A training engine needs
   **trade-outcome identity only**.

## 2. The three surfaces (the frame; CC audits and may tighten, never loosen)

| surface | contents (proposed) | rules |
|---|---|---|
| **TRAIN** | all bar/archive history through **2024-12-31**; the already-read replay windows (January 2026 sealed arms, April's 15 sealed days, May's ~3 days); every archive exhaust (B7.5 pool, gate walks, ledgers) | iterate freely, **unbilled**. Every look still LOGGED (append-only) with a `surface` stamp. |
| **VAL** | **2025-01-01 .. 2026-05-31**, chronological folds | ranking and gradient checks only. This surface is **used-once by survivor selection** (`d.year >= 2025`, build_survivor_book.py:60) — every VAL figure carries that disclosure; headline expectancy never quotes VAL alone. Unbilled, logged. |
| **TEST** | **March 2026** (absolute blackout, both senses — the B7.5 sealed replay stays unrun); the **live forward stream** from each arming date (sealed_holdout cutoff semantics); every `trainer_partitions` blackout | **never trained on, never iterated against.** Consumed only by the sealed gate and by live monitoring. |

CC's first work order is the **contamination audit**: enumerate what every existing artifact
already consumed (the June route's March-TRAIN materialization is already recorded in
`trainer_partitions.Partition.prior_consumption`; the survivor selection's 2025+ predicate;
the full-history gate walks) and pin the final boundaries in the fail-closed registry.

## 3. Billing (the one-bill rule)

- Iteration on TRAIN/VAL bills **nothing** to the candidate family. It is logged, not billed.
- A candidate **graduates** when its author sends it to the sealed gate. Graduation bills
  **exactly one look** to the family ratchet, atomically, with the candidate's full
  train/val provenance chain attached. A candidate whose provenance shows any TEST
  consumption is **refused graduation** (fail closed).
- **The sealed gate itself is frozen**: the ratified admission rule — `CANDIDATE_BOOK_V1`
  basis, sealed `B_balanced` α = 0.10, RECORDED population with AN's conditions (band
  alongside, declared cut rules, chronological fold table, recent-fold sizing). Nothing in
  this lane changes what it takes to admit; the lane changes how cheaply we can *search*.

## 4. Incubation (between admission and full weight)

- At most **5 concurrent incubant sleeves**, each at **≤ 0.05-class confidence weight**.
- Each incubant carries **pre-registered stop AND promotion rules, written before arming**
  (the AS dossier shape). The live stream is its test set.
- Arming/pulling/promoting is an **owner ceremony every time** — the orchestrator executes,
  Borhen decides. The risk dial, allocation profile, and sealed economic contract stay his.

## 5. Inviolate (nothing below moves, ever, under this lane)

H1/R2 seal discipline; the activation-token layer; the never-execute script list; the
ceremony discipline (flatten-first, flags-held restarts, hash-verified transfers); March and
the blackouts; the live forward stream as virgin test; `config/agent_config.yaml` and
`config/profiles/redacted_account.yaml` untouched. The frozen sealed engine stays frozen — the
train engine is a **new lane beside it**, and its outputs are training evidence, never
admission evidence.

## 6. Operations

- **Compute**: the lane runs on this laptop within its measured limits (≤2 concurrent arms,
  16 GB). The rented compute box (~$100–300/mo, 32–64 GB) is approved as an *option* —
  renting it is Borhen's purchase to make when the lane's throughput earns it.
- **Cross-model review**: graduation dossiers and load-bearing engine code get a
  second-model adversarial review (Codex CLI is on this machine) — advisory; the sealed
  gate remains the decider.
- **Sessions**: CB `B2150–B2199` (train engine), CC `B2200–B2249` (protocol machinery),
  CD `B2250–B2299` reserved (broad-family regeneration under the repaired stack — commissioned
  when CB's engine passes acceptance). CA `B2100–B2149` (revival gates) runs alongside; its
  revival candidates are the incubation lane's first intake.
