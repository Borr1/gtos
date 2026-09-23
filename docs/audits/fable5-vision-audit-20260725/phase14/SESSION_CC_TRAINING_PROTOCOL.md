# Session CC — the training-lane protocol machinery (wave 14, B2200–B2249)

Read first: `phase14/TRAINING_LANE_RATIFICATION.md` (you are implementing this — it is the
constitution, you are the legislature), `phase5/SESSION_Z_TRAINER_AND_PARTITIONS_RESULT.md`
+ `src/research_infra/trainer_partitions.py` (the fail-closed registry you EXTEND — you own
this module this wave; Session CB imports it), `src/research_infra/validation_integrity/
sealed_holdout.py` and `trial_budget_ledger.py`, `walkforward/candidate_family.py` (the
ratchet), `phase10/receipts/POPULATION_RULE_V1.json` + its pin test (the pattern your pin
tests copy), `WAVE_11_WORKING_AGREEMENT.md`. Owner authority: the 2026-07-31 ratification.

**The objective in one sentence:** the ratified protocol becomes code that fails closed —
surfaces enforced by registry, iteration logged unbilled, graduation billing exactly one
look with a clean-provenance check, incubation capacity machine-checked — so the training
lane can run hot without a single honesty property depending on anyone's discipline.

## Work orders

**CC-1 — The contamination audit, then the boundaries.** Enumerate what every existing
artifact already consumed: the June route's March-TRAIN materialization (already in
`Partition.prior_consumption`), the survivor selection's `d.year >= 2025` predicate, the
full-history gate walks, the live window reads. Then pin the three surfaces of §2 of the
ratification as registry entries — TRAIN / VAL (with its used-once disclosure carried ON
the partition record) / TEST — extending `trainer_partitions.py`'s roles and rules. More
restrictive wins; genuine gaps stay uncovered (uncovered = refused); March's blackout is
untouchable whatever any partition says. Record every boundary you tighten vs the
ratification's frame and why.

**CC-2 — The iteration ledger (unbilled, logged, append-only).** Every train/val look gets
logged — spec digest, surface stamp, date span, engine version, verdict — without touching
the family ratchet. Decide the mechanics yourself (a `surface` field on the existing trial
ledger vs a sibling ledger) and state why; the invariant that matters: **the family ratchet
moves ONLY on graduation events**, and a reader can always separate exploration looks from
billed looks.

**CC-3 — The graduation biller.** One function, atomic: takes a candidate + its provenance
chain (train/val fingerprints from the iteration ledger), REFUSES if provenance is missing
or shows any TEST consumption (sealed_holdout semantics), bills exactly one look to the
family ratchet, and emits the graduation record the sealed gate consumes. The sealed gate
itself is FROZEN — you wire to it, you do not touch it.

**CC-4 — The incubation registry.** ≤5 concurrent incubants, ≤0.05-class weight, and a
registration REFUSED unless it carries pre-registered stop AND promotion rules (the AS
dossier shape, machine-checked fields). Consumed by the dossier/ceremony flow; arming stays
an owner ceremony. CA is filing the first candidates against this — coordinate by artifact
shape, not by waiting.

**CC-5 — Pin it.** Tests in the `test_population_rule_ratified.py` pattern for: the surface
boundaries, the March/blackout refusal, the one-bill invariant, the TEST-clean refusal, the
incubation capacity/weight/pre-registration refusals. Behavioural tests, not line pins.
Then write the working-agreement amendment text (a `§ Training lane` section: surfaces,
one-bill rule, incubation, the language rule banning "dead/corpse" for
`UNTESTED_UNDER_REPAIRS` families) as your handoff — the orchestrator merges it into the
agreement at the train.

**CC-6 — The trainer-session template.** One page: what a daily TRAINER session reads
(iteration ledger tail, surface maps, repair queue), what it writes (candidate files, next
queue), and the graduation checklist. This is the operating manual for every session that
runs inside the lane after you.

## Done means

Result doc findings-first + receipts under `phase14/receipts/`, blocks B2200–B2249, scoped
A/B green vs the ZERO baseline with the tool-emitted `gtos-ab-receipt-v1` fence, honest
"what I got wrong", handoff list. Never touch the VPS; never run broker-capable scripts;
never edit `config/agent_config.yaml`, `config/profiles/redacted_account.yaml`, or any R2-bound
path. Nothing you build changes the sealed admission rule — cheapen the search, never the
gate.
