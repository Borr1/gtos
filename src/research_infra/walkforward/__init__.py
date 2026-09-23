"""The walk-forward admission gate — the door the estate has been stranded behind.

`THIRD_REVIEW.md` §4 names exactly one entrance for the 21 candidate/expansion sleeves:
"...enter `SURVIVOR_BOOK_V1` **only through the walk-forward gate**." This package is that
gate.

WHAT THIS IS, AND WHAT IT REFUSES TO BE
---------------------------------------
A gate that cannot fail a sleeve launders unvalidated research into a book that carries a
funded account. Five construction choices make failure reachable, and each one is here
because the programme has already been burned by its absence:

1. **Out-of-sample only.** No fold's in-sample statistic ever contributes to the verdict.
   The IS number is carried as telemetry so IS->OOS decay is visible, and nothing else.
2. **Cost is charged, or the sleeve is refused.** `src/costs/cost_r` is the only cost
   authority (Session J). When it raises, the trade is UNPRICED and the sleeve's coverage
   falls; below the sealed floor the verdict is NOT_EVALUABLE, never "assume zero". F38 is
   what the other branch looks like: `broker_net_cost_engine.py:577-583` sums
   `spread + slippage + swap` and charges zero commission at five sites.
3. **The null respects day-clustering.** Trades are not iid. Day-aggregation removes the
   within-day cluster; a block treatment across days removes the rest. A per-trade
   bootstrap on this data overstated a stated error budget by 2.1x-7.7x (B279).
4. **Multiplicity is charged across the whole family judged in one run.** Testing 21
   hypotheses and reporting the winners is how `positive_weighted12_after_swap` — the LIVE
   market-expansion policy — was selected: it is literally "the 12 of 14 that came out
   positive" (`candidate_registry.py:425-438`), chosen on the same data that scored them.
5. **The spec is sealed before the data is seen** — including the pooling weights. The
   B7.5 campaign sealed its thresholds and left its pooling weights open, so the semantics
   could still be chosen after seeing results. `GateSpec.seal()` closes that hole by
   hashing the pooling rule along with everything else.

FIDELITY CEILING
----------------
A gate result is only as good as the generator feeding it, so `fidelity.py` carries a
per-sleeve live-recall record and refuses to score below a floor, saying why.

K measured that record by sleeve structure (`phase3/K1_GATE_RECEIPT.md` §3/§3.5): per-bar
sleeves 96 %, first-of-day sleeves 19 %. **The 19 % was a code-lineage artefact** — the port
ran mainline against a live record produced by `redacted_host`, which has no
`sleeves/_server_clock.py`, so every session window in nine sleeves sat 3 h apart. Session Y
measured it under the matching lineage (`replay_policy.generation_lineage`): 175 of 175
missing intents recovered, 0 newly missed, count agreement 86.44 % -> 98.86 %, and all seven
of those sleeves at 100 % live-recall. Two of the seven were never first-of-day at all.

So the floor no longer separates per-bar from first-of-day; it separates **measured from
unmeasured**, which is the property worth keeping. See `fidelity.py`'s docstring for what a
lineage-matched 100 % does and does not entitle a gate to.

BOUNDARY
--------
Offline and pure. Reads bars, cost artifacts and trade records; imports no broker module,
opens no socket, places nothing. Sleeve composition, the risk dial and the admission
threshold itself are Borhen's decisions — this package measures and proposes, and the
threshold lives in a spec file he signs, not in code.
"""

from src.research_infra.walkforward.fidelity import (
    FIDELITY_REGISTER,
    FidelityBasis,
    FidelityClass,
    FidelityEvidenceAuthority,
    FidelityReference,
    FidelityReferencePolicy,
    clear_direct_fidelity_measurements,
    direct_fidelity_measurements,
    fidelity_for,
    register_direct_fidelity_measurement,
    register_structured_fidelity_measurement,
)
from src.research_infra.walkforward.folds import Fold, assign_folds, build_fold_calendar
from src.research_infra.walkforward.gate import (
    GateResult,
    SleeveVerdict,
    Verdict,
    run_gate,
)
from src.research_infra.walkforward.panel import (
    PricedTrade,
    TradeRecord,
    build_daily_panel,
    price_trades,
)
from src.research_infra.walkforward.spec import DEFAULT_SPEC, LEGACY_DEFAULT_SPEC, GateSpec
from src.research_infra.walkforward.stats import (
    benjamini_hochberg,
    block_length_auto,
    bonferroni,
    day_block_bootstrap_p,
    lag1_autocorr,
)

__all__ = [
    "DEFAULT_SPEC",
    "LEGACY_DEFAULT_SPEC",
    "FIDELITY_REGISTER",
    "FidelityBasis",
    "FidelityClass",
    "FidelityEvidenceAuthority",
    "FidelityReference",
    "FidelityReferencePolicy",
    "Fold",
    "GateResult",
    "GateSpec",
    "PricedTrade",
    "SleeveVerdict",
    "TradeRecord",
    "Verdict",
    "assign_folds",
    "benjamini_hochberg",
    "block_length_auto",
    "bonferroni",
    "build_daily_panel",
    "build_fold_calendar",
    "clear_direct_fidelity_measurements",
    "day_block_bootstrap_p",
    "direct_fidelity_measurements",
    "fidelity_for",
    "lag1_autocorr",
    "price_trades",
    "register_direct_fidelity_measurement",
    "register_structured_fidelity_measurement",
    "run_gate",
]
