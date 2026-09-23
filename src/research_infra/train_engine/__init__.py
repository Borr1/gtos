"""The train-grade replay lane -- built BESIDE the frozen sealed engine.

Wave 14, Session CB (B2150-B2199). Owner authority: the 2026-07-31 training-lane
ratification (`phase14/TRAINING_LANE_RATIFICATION.md`).

This lane exists because the sealed lane's acceptance test is the wrong one for
iteration. Session AX was held to **provenance identity** -- byte-identical
evidence receipts -- which forced keeping the 52 M-call authority-payload hash
loop and every field that exists to prove rather than to decide, and delivered
1.06x. The training lane needs **trade-outcome identity only**: same fills, same
exits, same per-trade R, same money at risk.

Three rules hold this lane honest, and they are enforced in code rather than in
prose:

1. `identity` freezes the tuple. Nothing may be deleted that the tuple reads.
2. `guard` refuses any day outside a trainable partition, and refuses the
   reserved blackout on EVERY path including acceptance. It imports
   `trainer_partitions` and never redefines a boundary.
3. Every artifact this lane writes is stamped
   `TRAINING_EVIDENCE - never admission-grade`.

Nothing here is admission evidence. The sealed gate is unchanged and the frozen
engine's bytes are untouched: the accelerations are runtime rebinds, exactly as
`fast_engine` established.
"""

from __future__ import annotations

#: Bumped whenever a cut changes what the engine COMPUTES. It is stamped into
#: every training artifact so a trade table can be tied to the engine that
#: produced it. `identity.TUPLE_VERSION` is separate on purpose: the tuple is a
#: contract with the reader, the engine version is a fact about the producer.
TRAIN_ENGINE_VERSION = "gtos.train_engine.v1"

#: Every artifact carries this. It is a load-bearing string, not decoration --
#: `runner` refuses to write an output without it.
TRAINING_EVIDENCE_STAMP = "TRAINING_EVIDENCE - never admission-grade"

__all__ = ["TRAIN_ENGINE_VERSION", "TRAINING_EVIDENCE_STAMP"]
