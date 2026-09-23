"""The training lane — protocol machinery for `phase14/TRAINING_LANE_RATIFICATION.md`.

Ratified by Borhen 2026-07-31. Built by Session CC (wave 14, B2200-B2249).

THE ONE SENTENCE
----------------
Iteration on TRAIN/VAL is **logged and unbilled**; the family ratchet moves at **exactly one
point**, graduation to the sealed gate; the sealed gate itself is **frozen**. The lane changes
how cheaply the estate can *search*, never what it takes to *admit*.

THE FOUR MODULES AND WHAT EACH REFUSES
--------------------------------------
    trainer_partitions.SurfaceMap   which days a lane session may touch at all
                                    (in `src/research_infra/trainer_partitions.py`, the module
                                    that already fails closed for the fitting path — the two
                                    axes live together so they cannot silently diverge)

    iteration_ledger                every train/val look, append-only, `surface`-stamped by the
                                    map rather than by the caller. REFUSES a TEST look and a
                                    look on an unacknowledged uncovered day. Never bills.

    graduation                      the ONE billing point. REFUSES missing provenance, REFUSES
                                    provenance that touched TEST, bills exactly one look to the
                                    ratchet, emits the record the frozen gate consumes.

    incubation                      <= 5 concurrent incubants at <= 0.05-class weight, each
                                    with pre-registered stop AND promotion rules. REFUSES an
                                    arming that carries no owner ceremony.

WHY THE LEDGERS ARE SIBLINGS OF `validation_integrity.trial_budget_ledger`, NOT ROWS IN IT
------------------------------------------------------------------------------------------
`measured_n_trials()` feeds the DSR deflation, and it is `max(prospective look events, ...)`.
Writing lane iteration into that ledger would make every exploration look raise the estate's
DSR bill — which is precisely the defect the ratification's section 1.2 names ("multiplicity
billing leaked backward into exploration"; AW paid a 486-look family bill for research triage).
A sibling ledger keeps the two bills separable by construction.

The obvious objection to a sibling is that it becomes a bypass — log the real look in the cheap
ledger and never pay. It cannot: **you cannot graduate without having logged.** `graduate()`
reads its provenance out of the iteration ledger and refuses a candidate with none, so the
sibling is a prerequisite for billing rather than an alternative to it.
"""

from __future__ import annotations

from .append_only import append_row, atomic_write_json, read_rows
from .graduation import (
    DEFAULT_GRADUATION_LEDGER,
    Candidate,
    GraduationRecord,
    GraduationRefusal,
    graduate,
)
from .incubation import (
    DEFAULT_INCUBATION_REGISTRY,
    MAX_CONCURRENT_INCUBANTS,
    MAX_INCUBANT_WEIGHT,
    Incubant,
    IncubationRefusal,
    IncubationRegistry,
    OwnerCeremony,
    PreRegisteredRule,
    rules_from_dicts,
)
from .iteration_ledger import (
    DEFAULT_ITERATION_LEDGER,
    ITERATION_VERDICTS,
    IterationLedger,
    IterationLedgerRefusal,
)

__all__ = [
    "Candidate",
    "DEFAULT_GRADUATION_LEDGER",
    "DEFAULT_INCUBATION_REGISTRY",
    "DEFAULT_ITERATION_LEDGER",
    "GraduationRecord",
    "GraduationRefusal",
    "ITERATION_VERDICTS",
    "Incubant",
    "IncubationRefusal",
    "IncubationRegistry",
    "IterationLedger",
    "IterationLedgerRefusal",
    "MAX_CONCURRENT_INCUBANTS",
    "MAX_INCUBANT_WEIGHT",
    "OwnerCeremony",
    "PreRegisteredRule",
    "append_row",
    "atomic_write_json",
    "graduate",
    "read_rows",
    "rules_from_dicts",
]
