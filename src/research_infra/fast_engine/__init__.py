"""GTOS fast sealed replay engine (session AX, wave 12, blocks B1700-B1749).

The frozen sealed engine is bound by the R2 decision contract: 43 paths whose
SHA-256 feeds all four arm fingerprints, so a single edited byte expires the
parked January comparability option (CLAUDE.md H1). **Nothing in this package
edits a bound path.** The fast engine is new files that import the frozen
modules and alter their *runtime* behaviour in the evidence layer only, leaving
every bound hash on disk untouched.

The measured basis for the redesign (THIRD_REVIEW.md A1 and the first audit's
sampled profile at ``docs/audits/opus5-architecture-20260725/receipts/
profile_jan01_02_sampled.json``):

* 60.6 % of the Python heap at high-water is the monolith's per-day
  row/attribution accumulation; the source layer is 1.6 %.
* ~60 % of wall-clock self-time is evidence/attribution machinery -- canonical
  JSON, proof hashes, ABC ``isinstance`` dispatch and ledger writing -- against
  ~8 % that decides trades.
* >99.8 % of the evidence bytes are never value-read.

Acceptance is bit-honesty, not speed: a sealed January arm must reproduce
R-identically from the same sealed read-only inputs. A fast wrong engine does
not ship.
"""

from __future__ import annotations

__all__ = [
    "FAST_ENGINE_VERSION",
]

FAST_ENGINE_VERSION = "AX.1"
