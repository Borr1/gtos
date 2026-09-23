"""The sealed gate specification — every choice that could otherwise be made after the data.

WHY THIS FILE EXISTS
--------------------
The B7.5 campaign's standing methodological defect is recorded in `CLAUDE.md` §4: the
protocol "seals the thresholds but **not the pooling weights** (by-window vs by risk-cash),
so even the pooling semantics would otherwise be chosen after seeing the data."

`GateSpec` closes that hole by construction. Every knob that could move a verdict —
thresholds, fold rule, embargo rule, purge rule, day-aggregation, **pooling weights**,
multiplicity correction, the bootstrap seed, the trial count, the cost artifact's own
sha256 — is a field, and `seal()` hashes all of them into one `spec_sha256`. A gate result
carries the seal it ran under. Change any field and the seal changes, which makes
"we adjusted the standard after seeing the answer" visible instead of deniable.

The seal is not a permission system. Nothing stops a researcher editing the spec and
re-running. It stops them doing it *silently*.

WHAT IS NOT IN HERE
-------------------
The admission threshold values that decide Borhen's money. `DEFAULT_SPEC` is a *proposal*
carrying the author's recommended numbers; `phase5/ADMISSION_STANDARD_OPTIONS.md` sets out
three coherent options and what each admits and rejects. Choosing among them is his call,
the same class as the risk dial (`WAVE_5_WORKING_AGREEMENT.md` §1).

THE MARCH 2026 BLACKOUT
-----------------------
`reserved_blackout` is a list of date ranges the gate treats as radioactive: no fold
boundary may fall inside one, no trade overlapping one may enter train OR test, and the
count of dropped trades is published. It defaults to March 2026 — the only outcome-unread
month the programme has left (`CLAUDE.md` §4, "Keep March outcome-unread").

A correction worth recording, measured 2026-07-29 (B421): **there is no file called "the
B7.5 partition registry."** The prompt for this session, `WAVE_5_PLAN.md:61`/`:84` and
`JANUARY_BANK.md:218` all say "the B7.5 partition registry marks March 2026 as TRAIN",
which reads as though such a file exists. The only partition registry in the repo is
`research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ULTIMATE_EDGE_PARTITION_REGISTRY.jsonl`,
which belongs to the June v4 mechanical-edge route. Its hazard is real — its `TRAIN` range
`["2025-06-02", "2026-04-17"]` does swallow all of March 2026 — but B7.5's *own* contract
assigns March the opposite role: `"role": "untouched_for_this_treatment_historical_challenge"`,
`"outcome_artifact_read_by_builder": false`
(`B7_5_POST_ACCELERATION_DECISION_CONTRACT.json:819,829`). Authoring a correct registry is
Session Z's scope (`WAVE_5_PLAN.md` §2). This blackout is the local defence in the meantime.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import asdict, dataclass, field, replace
from typing import Any

from src.research_infra.walkforward.fidelity import FidelityReferencePolicy
from src.research_infra.validation_integrity.trial_budget_ledger import DSR_TRIAL_FLOOR

LEGACY_SCHEMA = "gtos.walkforward.gate_spec.v1"
SCHEMA = "gtos.walkforward.gate_spec.v2"

# `DSR_TRIAL_FLOOR` is IMPORTED, not copied. An earlier revision of this file re-declared
# it as a literal directly under a comment claiming it was reused "so the two gates cannot
# drift apart" -- asserting a coupling that did not exist, which is worse than silent
# duplication. Its home is `validation_integrity/trial_budget_ledger.py:63`.

DateRange = tuple[str, str]


def _exact_iso_date(value: Any, *, field_name: str) -> str:
    """Return one canonical calendar date; reject truncation-compatible aliases."""

    if isinstance(value, dt.datetime):
        raise ValueError(
            f"{field_name} must be an exact ISO date YYYY-MM-DD, got {value!r}"
        )
    if isinstance(value, dt.date):
        return value.isoformat()
    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} must be an exact ISO date YYYY-MM-DD, got {value!r}"
        )
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be an exact ISO date YYYY-MM-DD, got {value!r}"
        ) from exc
    if parsed.isoformat() != value:
        raise ValueError(
            f"{field_name} must be an exact ISO date YYYY-MM-DD, got {value!r}"
        )
    return value


def _immutable_date_ranges(value: Any, *, field_name: str) -> tuple[DateRange, ...]:
    """Copy nested caller containers into a canonical immutable authority value."""

    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of date pairs")
    try:
        ranges = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a sequence of date pairs") from exc
    normalized: list[DateRange] = []
    for index, raw in enumerate(ranges, start=1):
        if isinstance(raw, (str, bytes)):
            raise ValueError(f"{field_name} range {index} must contain [start, end]")
        try:
            pair = tuple(raw)
        except TypeError as exc:
            raise ValueError(
                f"{field_name} range {index} must contain [start, end]"
            ) from exc
        if len(pair) != 2:
            raise ValueError(f"{field_name} range {index} must contain [start, end]")
        normalized.append(
            (
                _exact_iso_date(pair[0], field_name=field_name),
                _exact_iso_date(pair[1], field_name=field_name),
            )
        )
    return tuple(normalized)

#: Fields dropped from `canonical()` when they are None, so adding a CAPABILITY to this spec
#: does not silently invalidate the seals of every run that predates it.
#:
#: THE DEFECT THIS REPAIRS, MEASURED (Session AI, 2026-07-30)
#: ---------------------------------------------------------
#: `spread_band` was added by Session AG (`048facafc`, "new `GateSpec.spread_band` field
#: (defaults None)") and it moved EVERY seal in the estate, because `asdict()` gains a key.
#: `AA_ESTATE_WALK.json` publishes `spec_sha256 d3df4c4386160d3a2bb6c9468886f1615cf6242fe
#: 73ac57a48a16ba034cd9652`; rebuilding that exact spec at HEAD gave `8bd15ced…`, and
#: dropping `spread_band` from the canonical dict returns `d3df4c43…` byte-for-byte. The same
#: was true of W's and X's published seals. Nothing recorded the break, so a session
#: re-deriving a published seal would read a methodology change that never happened — which
#: is precisely the signal this file exists to make undeniable.
#:
#: WHY DROPPING-WHEN-NONE IS SAFE, AND WHERE IT WOULD NOT BE
#: --------------------------------------------------------
#: Only for a field whose None means "the behaviour that existed before this field". For
#: example, `spread_band=None` charges the 37-day snapshot, which is exactly what every
#: pre-AG run charged; `declared_family_id=None` means no declaration was consulted, which is
#: exactly the pre-`candidate_family.py` state. The capture fields are likewise optional:
#: all-None means the original continuous-calendar gate, while any complete capture
#: authority changes both fold construction and the null's adjacency graph. No set value of
#: any field means what None means, so two semantically different specs can never collide.
#:
#: It would NOT be safe for a field whose None is a live third option distinguishable from
#: both "unset" and any set value, nor for one whose default is anything but None. Do not add
#: to this list without that argument, and never add a non-Optional field to it.
#:
#: THE REPAIR IS ONE-SIDED, AND SAYING SO IS THE POINT (found by an adversarial pass, B1067b)
#: -----------------------------------------------------------------------------------------
#: It restores the 18 published seals whose producing lineage PREDATED `spread_band` -- AA 7/7,
#: X 3/3, X_STATE_D 3/3, W 3/3, W_NEGATIVE_CONTROLS 2/2 -- and it BREAKS 10 that were computed
#: with the field already present at None, whose published hash therefore includes
#: `"spread_band":null`: AG_MX_PILOT_BANDED x3, EXIT_FRONTIER_V1/_TRAIL x1, FAMILY_ADMISSION_V1
#: x6. The remaining 34 set a real band and are untouched.
#:
#: 18 restored against 10 broken is a net gain and the restored cohort is the more cited one,
#: but the whole complaint against AG's change was that it broke seals SILENTLY -- so both
#: cohorts are now pinned by name in `test_candidate_family.py`. A future migration of this
#: field set has to update that test, which makes the next break loud.
_ABSENT_MEANS_UNCHANGED = (
    "spread_band",
    "declared_family_id",
    "declared_family_sha256",
    "capture_windows",
    "capture_declaration_id",
    "capture_declaration_sha256s",
)


@dataclass(frozen=True)
class GateSpec:
    """Everything fixed before the data is seen. Hash it, then run.

    Field groups, in the order a reader should audit them:

    IDENTITY        spec_id, schema, authored_utc, author_note
    SUBSTRATE       account, cost_artifact_sha256, reserved_blackout
    FOLDS           fold_rule, n_folds, min_fold_days, purge_rule, embargo_rule,
                    embargo_floor_days, embargo_quantile
    PANEL           day_aggregation, day_key
    POOLING         pooling_weights  <-- the field B7.5 left open
    NULL            null_test, block_days, n_bootstrap, n_permutation, seed
    MULTIPLICITY    multiplicity, alpha, n_trials, n_trials_basis
    ADMISSION       min_trades_total, min_trades_per_fold, min_folds_evaluable,
                    min_oos_positive_fold_frac, min_oos_mean_r, cost_coverage_floor,
                    require_measured_cost_frac
    FIDELITY        fidelity_floor, fidelity_reference_policy,
                    fidelity_precision_floor, fidelity_refusal_is_hard
    """

    # --- identity ---------------------------------------------------------------------
    spec_id: str
    authored_utc: str
    author_note: str = ""
    schema: str = SCHEMA

    # --- substrate --------------------------------------------------------------------
    account: str = "FTMO"
    #: sha256 of BROKER_TRUE_COSTS_V1.json. Empty means "not pinned" — allowed, but the
    #: gate records it as an unpinned run so a later cost-artifact change is detectable.
    cost_artifact_sha256: str = ""
    #: Date ranges (inclusive, ISO) that neither train nor test may touch.
    reserved_blackout: tuple[DateRange, ...] = (("2026-03-01", "2026-03-31"),)
    blackout_reason: str = (
        "March 2026 is the only outcome-unread month the programme has left "
        "(CLAUDE.md section 4). No fold boundary may fall inside it and no trade "
        "overlapping it may enter train or test."
    )
    #: Optional immutable authority for independently materialized, non-contiguous
    #: captures. These three fields are all-or-none. The ordered windows define data
    #: adjacency; the declaration id says which prospective authority was read; and the
    #: ordered sha256 tuple binds every declaration/amendment that produced the final
    #: windows. Runtime callers may assert equality but cannot supply or replace them.
    capture_windows: tuple[DateRange, ...] | None = None
    capture_declaration_id: str | None = None
    capture_declaration_sha256s: tuple[str, ...] | None = None

    # --- folds ------------------------------------------------------------------------
    #: "equal_calendar_folds_over_sleeve_span" — boundaries derive mechanically from the
    #: sleeve's own DATA AVAILABILITY span, never from its results. This is leak-free:
    #: availability is a property of the archive, not of outcomes.
    #: "fixed_global_calendar" — one calendar for every sleeve, taken from global_span.
    fold_rule: str = "equal_calendar_folds_over_sleeve_span"
    global_span: DateRange = ("1992-02-18", "2026-07-27")
    n_folds: int = 6
    min_fold_days: int = 90
    #: Drop from TRAIN any trade whose [entry, exit] span intersects the test fold widened
    #: by the embargo. Lopez de Prado (2018) ch.7 purging, applied to label spans rather
    #: than to row indices.
    purge_rule: str = "label_span_overlap"
    #: Embargo width is measured from the sleeve's OWN realised holds, TRAIN-side only.
    #: A nominal horizon would be wrong: across twelve live sleeves the used-fraction of
    #: horizon runs 0.4% to 105%, three exceeding their nominal horizon (SESSION_W brief),
    #: so no single nominal number is right for all of them.
    embargo_rule: str = "empirical_hold_quantile_train_side"
    embargo_quantile: float = 0.99
    embargo_floor_days: int = 1

    # --- panel ------------------------------------------------------------------------
    #: Trades are not iid. Aggregating to one observation per day removes the within-day
    #: cluster before any statistic is computed. "mean" matches the production convention
    #: in `scripts/recost_w7_validation.py:build_matrix_from` (day-mean per sleeve).
    day_aggregation: str = "mean"
    #: Which timestamp defines the day. "entry" keys a trade to the day it was decided.
    day_key: str = "entry"

    # --- pooling (the field B7.5 left open) -------------------------------------------
    #: How per-fold OOS results combine into the headline.
    #:   "equal_by_fold"  — each evaluable fold counts once. Robust to one fold holding
    #:                      most of the trades; that is the point.
    #:   "by_oos_days"    — weight by the number of OOS days the sleeve traded.
    #:   "by_oos_trades"  — weight by OOS trade count.
    pooling_weights: str = "equal_by_fold"

    # --- null -------------------------------------------------------------------------
    #: "both_conservative" runs the block sign-flip permutation AND a day-block bootstrap
    #: and takes the LARGER p. Sign-flip assumes a symmetric null; realised R is bounded
    #: below at the stop and open above, so it is not symmetric. The bootstrap needs no
    #: symmetry. Taking the max fails toward rejection, which is the direction a gate
    #: guarding a funded account should fail in.
    null_test: str = "both_conservative"
    #: Block length in DAYS for the across-day dependence. "auto" = max(cube-root rule,
    #: AR(1)-implied lag at which |rho| decays to 1%), capped to retain min_blocks.
    block_days: int | str = "auto"
    n_bootstrap: int = 10000
    n_permutation: int = 10000
    seed: int = 20260729
    #: Minimum number of sign-flip blocks. The block sign-flip null has only 2**B distinct
    #: outcomes, so exact enumeration floors p at 2**-B (sampled and legacy-continuous
    #: paths use their documented add-one floor): at B=4 the exact floor is 0.0625, ABOVE
    #: every threshold any of the three options can set. A cap of n//4 forced exactly
    #: that, and a series with a naive
    #: t-statistic of 13.49 came out at gate p=0.125. 8 blocks puts the floor at 0.004.
    min_blocks: int = 8
    #: Embargo fraction handed to the row-indexed `walk_forward_oos` CROSS-CHECK only.
    #: Sealed rather than hardcoded: this package's thesis is that every knob which could
    #: move a reported number is in the hash, and "it is only telemetry" is exactly the
    #: argument that lets a magic constant survive.
    crosscheck_embargo_frac: float = 0.01

    # --- multiplicity -----------------------------------------------------------------
    #: "benjamini_hochberg" controls the false-discovery rate across the family judged in
    #: one run; "bonferroni" controls the family-wise error rate (stricter); "none" is
    #: available only so the size of the correction can be shown, never as a standard.
    multiplicity: str = "benjamini_hochberg"
    alpha: float = 0.10
    #: DSR's n_trials. See `n_trials_basis` — this number is a FLOOR, not a measurement.
    n_trials: int = DSR_TRIAL_FLOOR
    n_trials_basis: str = (
        "FLOOR, not a measurement. No trial-budget ledger artifact exists anywhere in the "
        "repo (verified 2026-07-29: validation_integrity/trial_budget_ledger.py can build "
        "one but has never been run, and KNOWLEDGE_BASE/validation/SEALED_HOLDOUT_REGISTRY.json "
        "does not exist). The true search size behind the mx family is unrecorded. 128 is "
        "trial_budget_ledger.DSR_TRIAL_FLOOR. Gate results publish a sensitivity sweep over "
        "n_trials so the reader can see where the verdict would flip."
    )
    n_trials_sweep: tuple[int, ...] = (1, 16, 64, 128, 512, 2048)

    # --- anti-concealment ---------------------------------------------------------------
    # Every field in this block exists because an adversarial refuter got a sleeve that lost
    # 17,840 R over 23,325 trades to ADMIT under the STRICTEST option. Three separate
    # attacks, one mechanism: put the losses somewhere the scored statistic does not look.
    #
    #   fold 0    is the initial train block and is never scored, so 50,000 losing trades
    #             placed there changed nothing — and still counted toward min_trades_total.
    #   day-mean  aggregation means a day with 12 losers weighs the same as a day with one
    #             winner; 2,688 losers out of 2,913 trades pooled to +0.305 R/day.
    #   blackout  drops were reported as a COUNT, so 2,200 losing trades moved a sleeve from
    #             +94.7 R to -2,105 R lifetime with every scored number frozen.
    #
    #: Full-sample per-trade mean net R, over EVERY priced trade including fold 0. This one
    #: floor closes all three, because all three work by hiding trades from the scored
    #: window and none of them can hide a trade from the lifetime total. None disables it.
    min_lifetime_mean_r: float | None = 0.0
    #: Per-TRADE OOS expectancy, alongside the per-DAY one. Day aggregation is the right
    #: clustering control for the significance test and the wrong economics for an
    #: admission decision; requiring both to be positive keeps the two honest about each
    #: other. None disables it.
    min_oos_mean_r_per_trade: float | None = 0.0
    #: A fold whose test side is too thin to evaluate is excluded from the pooled statistic
    #: — which creates a perverse incentive, because thin folds are usually bad regimes.
    #: Measured: at 7 losers in a bad fold a sleeve ADMITs; at 8 it REJECTs. So thin folds
    #: are counted as NON-POSITIVE in the stability fraction, and too many of them refuses
    #: the sleeve outright.
    max_thin_fold_frac: float = 0.34
    #: Multiplicity is corrected within one run only, so 20 sleeves judged one at a time get
    #: 20 uncorrected tests. Measured: P(at least one junk admission per campaign) goes
    #: 8.3% -> 71.7% when the same 20 zero-edge sleeves are submitted singly. Set this to
    #: the TRUE number of hypotheses the campaign considered and the correction uses
    #: max(actual, declared).
    #:
    #: IT IS NO LONGER ONLY ON THE CALLER'S HONOUR, and the sentence that used to end this
    #: comment — "there is no persistent trial ledger in this repo" — was stale before it was
    #: struck: `research/operations/trial_budget/TRIAL_LEDGER.jsonl` carries 4,785 look events
    #: across sessions AA/AD/AF/AE. What the ledger cannot supply is a *prospective* family:
    #: it counts looks after they happen, so a bill read off it is still chosen once the
    #: outcomes are visible. `walkforward/candidate_family.py` supplies the missing half — a
    #: declaration written before the outcomes are read, with a ratchet so a withdrawal cannot
    #: shrink the bill. Prefer `candidate_family.with_declared_family(spec, family_id)` over
    #: typing this field; typing it still works and is still honest, it is just unattributable.
    declared_family_size: int | None = None
    #: Which declaration `declared_family_size` came from, as `<sha12>:<family_id>`, and the
    #: declaration file's full sha256. Set together by
    #: `candidate_family.with_declared_family`; both None means the size was typed by hand.
    #:
    #: These are sealed WHEN PRESENT and invisible to the seal when both are None
    #: (`canonical()`), so adding them did not move any spec authored before they existed —
    #: `test_candidate_family.py` pins `DEFAULT_SPEC.seal()` to the literal value it had
    #: beforehand. The asymmetry is defensible because a field that is absent cannot have
    #: moved a verdict, and no value of either field means what None means.
    declared_family_id: str | None = None
    declared_family_sha256: str | None = None
    #: Cost is a price drag divided by the stop, so a larger declared stop is a smaller cost
    #: in R. Measured: the same gold trades REJECT at a $5 stop and ADMIT at $20. Nothing
    #: cross-checks the stop against the price, so this bounds sl/entry_price. A trade
    #: outside the band is refused as implausible rather than priced.
    sl_over_price_band: tuple[float, float] = (1e-5, 0.5)
    #: Optional {sleeve: (broker_symbol, ...)}. The fidelity register keys on the sleeve
    #: NAME alone, so relabelling a 30%-recall sleeve as a per-bar one bypasses the fidelity
    #: gate entirely. Supplying this from the production resolvers
    #: (`walkforward.registry.build_symbol_allowlist`) makes the name claim checkable. None
    #: skips the check and the gate records that it was skipped.
    sleeve_symbol_allowlist: dict[str, tuple[str, ...]] | None = None

    # --- admission standard (Borhen's decision; these are the proposal's numbers) ------
    min_trades_total: int = 30
    min_trades_per_fold: int = 5
    min_folds_evaluable: int = 3
    #: Fraction of evaluable OOS folds that must be positive.
    #:
    #: NOTE ON THE FLOOR VALUE, which was raised from 0.50 after it failed its own test:
    #: 0.50 is the coin-flip point and therefore carries no information. A sleeve with no
    #: edge produces fold means scattered around zero, so ~half its folds are positive by
    #: construction. A one-regime sleeve — all its edge in a single fold, noise elsewhere —
    #: passes a 0.50 threshold roughly half the time while having no persistent edge at
    #: all. Measured: the one-regime adversary in `receipts/w_negative_controls.py` reached
    #: ADMIT at 0.50 with a pooled +0.726 R/day. Hence 0.60 here and the leave-one-out
    #: requirement below, which is the one that actually bites.
    min_oos_positive_fold_frac: float = 0.60
    min_oos_mean_r: float = 0.0
    #: LEAVE-ONE-FOLD-OUT. Drop the single best-performing OOS fold and require the pooled
    #: expectancy over what remains to still exceed this. Set to None to disable.
    #:
    #: This is the gate that actually catches a regime. A positive-fold-fraction threshold
    #: asks "how often was it positive"; this asks "does the answer survive deleting its
    #: best evidence". An edge that is really one good year fails it outright, and a real
    #: edge barely notices — which is the asymmetry a gate wants.
    min_oos_mean_r_drop_best_fold: float | None = 0.0
    #: ...and the absolute floor above is not sufficient on its own, which was measured
    #: rather than assumed. A synthetic sleeve with ALL of its edge inside a single fold
    #: (fold means 0.167, -0.180, 3.175, 0.033, 0.070) pools to +0.653 R/day and leaves
    #: +0.0225 R/day once its best fold is dropped — noise, and comfortably "> 0.0". It
    #: reached ADMIT. The absolute test is scale-blind: on a sleeve with a small headline
    #: it is demanding, and on one with a large headline it is nearly free.
    #:
    #: RETENTION fixes that by being scale-free: the expectancy surviving the drop must be
    #: at least this fraction of the headline expectancy. The example above retains
    #: 0.0225/0.653 = 3.4% and fails at any sensible setting; a genuinely persistent edge
    #: retains most of its headline because no single fold was carrying it.
    #: None disables the ratio test (the absolute floor still applies).
    min_drop_best_fold_retention: float | None = 0.50
    #: Fraction of a sleeve's trades that `cost_r` must be able to price. Below this the
    #: sleeve is NOT_EVALUABLE — never "assume zero for the rest". F38 is the other branch.
    cost_coverage_floor: float = 0.95
    #: What to do when a sleeve falls below `cost_coverage_floor`.
    #:
    #:   "refuse"             — the whole sleeve is NOT_EVALUABLE. The strictest reading,
    #:                          and the right default for an admission decision.
    #:   "restrict_to_priced" — evaluate the sleeve on the SUBSET of its universe broker
    #:                          truth can price, and stamp the verdict with exactly which
    #:                          symbols were dropped and what share of trades went with
    #:                          them. This is a different and narrower claim, and the stamp
    #:                          says so.
    #:
    #: Why "restrict_to_priced" is legitimate rather than a fudge: which symbols are
    #: priceable is determined by what is in the tick archive, NOT by what those symbols
    #: earned. The restriction is therefore independent of outcomes and does not bias the
    #: estimate — it changes the population being validated, which must be published, and
    #: is. Restricting on any outcome-dependent criterion would be selection, and is not
    #: offered.
    coverage_policy: str = "refuse"
    #: Under "restrict_to_priced", the share of the sleeve's trades that must survive the
    #: restriction. Below this the sleeve is refused anyway: a sleeve reduced to a third of
    #: its trades is not that sleeve.
    min_retained_trade_frac: float = 0.60
    #: Of the priced trades, the fraction whose cost carries Coverage.MEASURED.
    #: Below this the verdict still stands but is stamped TRANSFERRED/MODELLED.
    require_measured_cost_frac: float = 0.0
    #: Which spread band `cost_r` charges: None (the 37-day snapshot, flat across every
    #: era) or "low"/"mid"/"high" from `spread_model_v1`.
    #:
    #: This is the field that answers the gate's own disclosure. `gate._cost_window_note`
    #: says the cost artifact is a 37-day snapshot charged to a 2007-2026 panel, that cost
    #: is 33%-219% of gross R on the mx family, and that the bias is "knowable a priori"
    #: because spreads compressed. **The first two are right and the third is only half
    #: right.** Measured (Session AG): EURUSD's spread in 2000-2003 was 50x the snapshot,
    #: so FX history is indeed under-costed -- but XAUUSD's in 2020-2024 was 0.18x, so
    #: metals history is OVER-costed, and the same holds for indices and energy. The bias
    #: does not have one sign, which means it cannot be reasoned about; it has to be
    #: charged.
    #:
    #: Run the same sleeve at all three bands. One that admits at "high" is robust to the
    #: look-ahead. One that flips band gets that in its repair row instead of a silently
    #: optimistic pass. Setting a band also makes symbols priceable that the snapshot
    #: refuses outright (CADJPY, and 12 more), which is what turns NOT_EVALUABLE into a
    #: verdict.
    spread_band: str | None = None

    #: How the era and hour terms COMPOSE, added 2026-07-30 by Session AH. `None` takes
    #: `spread_model.DEFAULT_COMPOSITION` ("v2_damped", the measured one). Pass
    #: "v1_multiplicative" to reproduce any banded number published before that date -- AF's
    #: `FAMILY_ADMISSION_V1.json` and AG's `AG_MX_PILOT_BANDED.json` were both produced
    #: under v1, whose unvalidated era x hour product reached 198x on pre-2010 FX.
    spread_composition: str | None = None

    #: Overrides the fitted exponent, for walking `ERA_HOUR_EXPONENT_ENVELOPE` [0.310,
    #: 0.669]. A verdict that moves inside that envelope is BAND-UNSTABLE in the same sense
    #: `spread_band` means it, and should be reported that way rather than at its best point.
    spread_era_exponent: float | None = None

    #: Refuse to price a trade whose era band is too wide for the model's own decidability
    #: rule. `None` and `False` both mean the pre-field behaviour (price it anyway); `True`
    #: passes `require_decidable=True` down to `spread_price`, which raises, which
    #: `panel.price_trades` records as an **unpriced** trade.
    #:
    #: WHY THIS IS A SPEC AXIS AND NOT A DRIVER'S BUSINESS (Session AN, B1251)
    #: ---------------------------------------------------------------------
    #: `SpreadModel.estimate` has taken `require_decidable=` since Session AG shipped it and
    #: **no production path ever passed it** -- its only call sites anywhere were two tests
    #: (`test_spread_model.py:193`, `:374`). Meanwhile the population restriction it exists to
    #: express was reimplemented by hand three times inside one session's drivers (AL's
    #: `al_decidable_population.py`, `al_population_intersection.py`,
    #: `al_candidate_dossier.py`), each time as a per-trade `est.decidable` filter that the
    #: gate's seal could not see. A restriction that changes an ADMIT (it does -- 53x in p on
    #: `mx_btcusd`) and does not enter `spec_sha256` is not a methodology, it is a habit.
    #:
    #: This axis and `era_population.py` are the two halves of the repair: the module names the
    #: rule, this field makes the model enforce it, and `spec_id` carries the rule's name into
    #: the seal. The two are deliberately REDUNDANT on the decidable-family rules -- the module
    #: filters the population AND sets this flag -- so a filter that ever drifts from the
    #: model's own field shows up as a coverage shortfall instead of as a silent difference.
    #:
    #: THE CONSEQUENCE THAT IS NOT OBVIOUS: this interacts with `coverage_policy`. Under
    #: `B_balanced` (`restrict_to_priced`) an undecidable trade is dropped and the verdict is
    #: stamped with what went; under `A_strict` (`refuse`) a sleeve with more than 5 %
    #: undecidable trades becomes NOT_EVALUABLE outright. Both are the option behaving as
    #: documented, and it means "set the flag" and "restrict the population" are NOT the same
    #: operation. `era_population.py`'s docstring measures the difference.
    spread_require_decidable: bool | None = None

    # --- fidelity ---------------------------------------------------------------------
    #: Minimum generation-port live-recall required to score a sleeve at all.
    #: K measured per-bar 96%, first-of-day 19% (`phase3/K1_GATE_RECEIPT.md` section 3).
    #: 0.50 sits between them by construction: it admits the per-bar class and refuses the
    #: first-of-day class, which is exactly the split K's evidence supports.
    fidelity_floor: float = 0.50
    #: Which evidence class may clear the fidelity gate.  This is verdict-moving authority,
    #: so it is explicit and sealed in gate-spec v2.  Same-lineage replay is useful for
    #: deterministic replay consistency, but it is not independent generator validation.
    fidelity_reference_policy: str = FidelityReferencePolicy.INDEPENDENT_OR_LIVE.value
    #: None means precision is disclosed but does not gate.  A numeric floor requires an
    #: explicitly complete generated population; null precision refuses rather than passing.
    fidelity_precision_floor: float | None = None
    fidelity_refusal_is_hard: bool = True

    # --- free-form ---------------------------------------------------------------------
    notes: dict[str, Any] = field(default_factory=dict)

    # ----------------------------------------------------------------------------------
    def __post_init__(self) -> None:
        if self.schema not in (LEGACY_SCHEMA, SCHEMA):
            raise ValueError(
                f"unknown gate spec schema {self.schema!r}; expected {LEGACY_SCHEMA!r} or "
                f"{SCHEMA!r}"
            )
        try:
            policy = FidelityReferencePolicy(self.fidelity_reference_policy)
        except ValueError as exc:
            raise ValueError(
                f"unknown fidelity_reference_policy {self.fidelity_reference_policy!r}"
            ) from exc
        if self.schema == LEGACY_SCHEMA:
            if policy is not FidelityReferencePolicy.LEGACY_ANY_REFERENCE:
                raise ValueError(
                    "gate_spec.v1 must use legacy_any_reference: adding a v2 fidelity policy "
                    "under the historical schema would silently reinterpret old seals"
                )
            if self.fidelity_precision_floor is not None:
                raise ValueError(
                    "gate_spec.v1 cannot carry fidelity_precision_floor; use gate_spec.v2"
                )
            if any(
                value is not None
                for value in (
                    self.capture_windows,
                    self.capture_declaration_id,
                    self.capture_declaration_sha256s,
                )
            ):
                raise ValueError(
                    "gate_spec.v1 cannot carry capture authority; use gate_spec.v2"
                )
        elif policy is FidelityReferencePolicy.LEGACY_ANY_REFERENCE:
            raise ValueError(
                "gate_spec.v2 requires an explicit reference class; legacy_any_reference is "
                "historical compatibility only"
            )
        if not 0.0 <= self.fidelity_floor <= 1.0:
            raise ValueError("fidelity_floor must be in [0,1]")
        if self.fidelity_precision_floor is not None and not (
            0.0 <= self.fidelity_precision_floor <= 1.0
        ):
            raise ValueError("fidelity_precision_floor must be in [0,1] or None")
        object.__setattr__(
            self,
            "reserved_blackout",
            _immutable_date_ranges(
                self.reserved_blackout, field_name="reserved_blackout"
            ),
        )
        if self.capture_windows is not None:
            object.__setattr__(
                self,
                "capture_windows",
                _immutable_date_ranges(
                    self.capture_windows, field_name="capture_windows"
                ),
            )
        if self.capture_declaration_sha256s is not None:
            if isinstance(self.capture_declaration_sha256s, (str, bytes)):
                raise ValueError(
                    "capture_declaration_sha256s must be a sequence of sha256 values"
                )
            object.__setattr__(
                self,
                "capture_declaration_sha256s",
                tuple(self.capture_declaration_sha256s),
            )
        if self.account not in ("FTMO", "redacted_account"):
            raise ValueError(
                f"account must be 'FTMO' or 'redacted_account' (the only two the broker-truth "
                f"artifact carries), got {self.account!r}"
            )
        if self.fold_rule not in (
            "equal_calendar_folds_over_sleeve_span",
            "fixed_global_calendar",
        ):
            raise ValueError(f"unknown fold_rule {self.fold_rule!r}")
        if self.day_aggregation not in ("mean", "sum"):
            raise ValueError(f"unknown day_aggregation {self.day_aggregation!r}")
        if self.pooling_weights not in ("equal_by_fold", "by_oos_days", "by_oos_trades"):
            raise ValueError(f"unknown pooling_weights {self.pooling_weights!r}")
        if self.multiplicity not in ("benjamini_hochberg", "bonferroni", "none"):
            raise ValueError(f"unknown multiplicity {self.multiplicity!r}")
        if self.null_test not in ("both_conservative", "permutation", "bootstrap"):
            raise ValueError(f"unknown null_test {self.null_test!r}")
        if self.coverage_policy not in ("refuse", "restrict_to_priced"):
            raise ValueError(f"unknown coverage_policy {self.coverage_policy!r}")
        if not 0.0 < self.min_retained_trade_frac <= 1.0:
            raise ValueError("min_retained_trade_frac must be in (0,1]")
        if not 0.0 <= self.max_thin_fold_frac <= 1.0:
            raise ValueError("max_thin_fold_frac must be in [0,1]")
        lo, hi = self.sl_over_price_band
        if not 0.0 < lo < hi:
            raise ValueError(f"sl_over_price_band must satisfy 0 < lo < hi, got {lo},{hi}")
        if self.declared_family_size is not None and self.declared_family_size < 1:
            raise ValueError("declared_family_size must be >= 1")
        # Half a provenance is worse than none: an id with no sha names a declaration nobody
        # can pin, and a sha with no id pins a file without saying which family inside it was
        # read. Both or neither.
        if (self.declared_family_id is None) != (self.declared_family_sha256 is None):
            raise ValueError(
                "declared_family_id and declared_family_sha256 must be set together "
                f"(got id={self.declared_family_id!r}, "
                f"sha256={self.declared_family_sha256!r}). Use "
                "walkforward.candidate_family.with_declared_family()."
            )
        if self.declared_family_id is not None and self.declared_family_size is None:
            raise ValueError(
                "declared_family_id is set but declared_family_size is None: the spec claims "
                "a declaration and then carries no bill from it."
            )
        if self.n_folds < 3:
            raise ValueError(
                "n_folds must be >= 3: fold 0 is consumed as the initial train block and "
                "is never scored, so n_folds=2 leaves a single evaluable fold and "
                "min_folds_evaluable can never be met."
            )
        if not 0.0 < self.alpha < 1.0:
            raise ValueError(f"alpha must be in (0,1), got {self.alpha}")
        if not 0.0 < self.embargo_quantile <= 1.0:
            raise ValueError(f"embargo_quantile must be in (0,1], got {self.embargo_quantile}")
        if not 0.0 <= self.cost_coverage_floor <= 1.0:
            raise ValueError("cost_coverage_floor must be in [0,1]")
        if self.n_trials < 1:
            raise ValueError("n_trials must be >= 1")
        if self.min_blocks < 2:
            raise ValueError("min_blocks must be >= 2")
        if self.block_days != "auto":
            if not isinstance(self.block_days, int) or self.block_days < 1:
                raise ValueError(
                    f"block_days must be 'auto' or an int >= 1, got {self.block_days!r}. "
                    "It was previously unvalidated, and a block >= n collapses the "
                    "bootstrap's null variance to zero, floors p at 1/(n_boot+1) and turns "
                    "a non-significant series into a maximally significant one."
                )
        for lo, hi in self.reserved_blackout:
            if _d(lo) > _d(hi):
                raise ValueError(f"reserved_blackout range reversed: {lo}..{hi}")
        capture_authority = (
            self.capture_windows,
            self.capture_declaration_id,
            self.capture_declaration_sha256s,
        )
        if any(value is None for value in capture_authority) and not all(
            value is None for value in capture_authority
        ):
            raise ValueError(
                "capture_windows, capture_declaration_id, and "
                "capture_declaration_sha256s must be set together"
            )
        if self.capture_windows is not None:
            if self.fold_rule != "equal_calendar_folds_over_sleeve_span":
                raise ValueError(
                    "capture windows require fold_rule="
                    "equal_calendar_folds_over_sleeve_span"
                )
            if not self.capture_windows:
                raise ValueError("capture_windows must contain at least one window")
            if not isinstance(self.capture_declaration_id, str) or not (
                self.capture_declaration_id.strip()
            ):
                raise ValueError("capture_declaration_id must be non-empty")
            hashes = self.capture_declaration_sha256s or ()
            if not hashes:
                raise ValueError(
                    "capture_declaration_sha256s must contain at least one sha256"
                )
            for digest in hashes:
                if not isinstance(digest, str) or len(digest) != 64 or any(
                    char not in "009abcdef" for char in digest
                ):
                    raise ValueError(
                        "capture declaration hashes must be lowercase full sha256 values: "
                        f"{digest!r}"
                    )
            if len(set(hashes)) != len(hashes):
                raise ValueError(
                    "capture_declaration_sha256s must not repeat a declaration"
                )
            previous_hi: dt.date | None = None
            for index, raw in enumerate(self.capture_windows, start=1):
                if len(raw) != 2:
                    raise ValueError(
                        f"capture window {index} must contain [start, end]"
                    )
                lo, hi = _d(raw[0]), _d(raw[1])
                if hi < lo:
                    raise ValueError(
                        f"capture window {index} is reversed: {lo}..{hi}"
                    )
                if hi == lo:
                    raise ValueError(
                        f"capture window {index} must span at least two calendar days: "
                        f"{lo}..{hi}"
                    )
                if previous_hi is not None and lo <= previous_hi:
                    raise ValueError(
                        "capture windows must be strictly ordered and non-overlapping: "
                        f"window {index} starts {lo} after prior end {previous_hi}"
                    )
                if self.blackout_hits(lo, hi):
                    raise ValueError(
                        f"capture window {index} overlaps reserved blackout: {lo}..{hi}"
                    )
                previous_hi = hi

    # ----------------------------------------------------------------------------------
    def canonical(self) -> dict[str, Any]:
        """Everything that could move a verdict, in a stable order.

        `notes` is excluded deliberately — free-form commentary must not be able to change
        the seal, or every typo fix would read as a methodology change.

        `_ABSENT_MEANS_UNCHANGED` fields are dropped **when they are None**, so a spec that
        does not use a capability seals exactly as it did before that capability existed.
        See the constant for why this is safe and for the measured defect it repairs.
        """
        d = asdict(self)
        d.pop("notes", None)
        d.pop("author_note", None)
        # v1 receipts did not have reference-policy or precision authority.  Reconstructing
        # one requires the explicit legacy schema/policy pair validated in __post_init__, then
        # drops only the fields that genuinely did not exist so its published seal is stable.
        if self.schema == LEGACY_SCHEMA:
            d.pop("fidelity_reference_policy", None)
            d.pop("fidelity_precision_floor", None)
        for f in _ABSENT_MEANS_UNCHANGED:
            if getattr(self, f) is None:
                d.pop(f, None)
        # `spread_composition` is NOT an absent-means-unchanged field, because None resolves to
        # `DEFAULT_COMPOSITION` (v2_damped) at the cost layer — the NEW behaviour. Dropping it at
        # None would hash a v2-behaving spec identically to a pre-field v1 run, which is the exact
        # collision seals exist to prevent. The honest rule, fixed at the wave-8 train merge:
        #   * the key that means the PRE-FIELD behaviour is `"v1_multiplicative"`, and only that
        #     value is dropped — so every seal published before the field existed reproduces from
        #     a spec that actually behaves as those runs behaved;
        #   * None is resolved to the value it will actually run at, so the hash names behaviour,
        #     never a sentinel;
        #   * the era exponent only has an effect under a damped composition, so under v1 it is
        #     dropped whatever it says, and under v2 a None resolves to the shipped constant.
        from src.costs.spread_model import DEFAULT_COMPOSITION, ERA_HOUR_EXPONENT
        comp = self.spread_composition or DEFAULT_COMPOSITION
        if comp == "v1_multiplicative":
            d.pop("spread_composition", None)
            d.pop("spread_era_exponent", None)
        else:
            d["spread_composition"] = comp
            d["spread_era_exponent"] = (
                self.spread_era_exponent if self.spread_era_exponent is not None
                else ERA_HOUR_EXPONENT
            )
        # `spread_require_decidable` follows the SAME rule as `spread_composition`, not the
        # `_ABSENT_MEANS_UNCHANGED` rule, and the difference matters (Session AN, B1251).
        # Dropping-when-None would be wrong here for the opposite reason it is wrong there:
        # None and False are the SAME behaviour, so a spec that says False must hash like one
        # that says nothing, or the same methodology would seal two ways. The pre-field
        # behaviour is `False`, so:
        #   * the resolved value is what gets hashed -- never the sentinel;
        #   * only `False` is dropped, so every seal published before this field existed
        #     reproduces byte-for-byte from a spec that behaves as those runs behaved;
        #   * `True` is a real methodology change and is always present in the hash.
        if self.spread_require_decidable:
            d["spread_require_decidable"] = True
        else:
            d.pop("spread_require_decidable", None)
        return d

    def seal(self) -> str:
        """sha256 over the canonical spec. Stable across processes and machines."""
        blob = json.dumps(self.canonical(), sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def with_(self, **kw: Any) -> "GateSpec":
        """A modified copy. The seal changes — that is the whole point."""
        return replace(self, **kw)

    def blackout_hits(self, start: dt.date, end: dt.date) -> list[DateRange]:
        """Blackout ranges intersecting [start, end]."""
        out = []
        for lo, hi in self.reserved_blackout:
            if start <= _d(hi) and end >= _d(lo):
                out.append((lo, hi))
        return out

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.schema == LEGACY_SCHEMA:
            d.pop("fidelity_reference_policy", None)
            d.pop("fidelity_precision_floor", None)
            d.pop("capture_windows", None)
            d.pop("capture_declaration_id", None)
            d.pop("capture_declaration_sha256s", None)
        d["spec_sha256"] = self.seal()
        return d

    def write(self, path: str) -> str:
        with open(path, "w") as fh:
            json.dump(self.as_dict(), fh, indent=1, default=str, sort_keys=True)
        return self.seal()

    @classmethod
    def read(cls, path: str, *, allow_legacy: bool = False) -> "GateSpec":
        """Read a sealed current spec, or an explicitly opted-in historical v1 spec."""

        with open(path) as fh:
            d = json.load(fh)
        if not isinstance(d, dict):
            raise ValueError("GateSpec file must contain a JSON object")
        claimed = d.pop("spec_sha256", None)
        if not isinstance(claimed, str) or len(claimed) != 64 or any(
            char not in "009abcdef" for char in claimed
        ):
            raise ValueError("spec seal missing or invalid: expected lowercase full sha256")
        schema = d.get("schema")
        if schema == LEGACY_SCHEMA:
            if not allow_legacy:
                raise ValueError(
                    "gate_spec.v1 is historical compatibility only; pass "
                    "allow_legacy=True explicitly"
                )
            if any(
                d.get(field_name) is not None
                for field_name in (
                    "capture_windows",
                    "capture_declaration_id",
                    "capture_declaration_sha256s",
                )
            ):
                raise ValueError(
                    "gate_spec.v1 cannot carry capture authority; use gate_spec.v2"
                )
            d.setdefault(
                "fidelity_reference_policy",
                FidelityReferencePolicy.LEGACY_ANY_REFERENCE.value,
            )
            d.setdefault("fidelity_precision_floor", None)
        elif schema != SCHEMA:
            raise ValueError(
                f"unsupported GateSpec schema {schema!r}; expected {SCHEMA!r}"
            )
        d["reserved_blackout"] = tuple(tuple(r) for r in d.get("reserved_blackout", ()))
        if d.get("capture_windows") is not None:
            d["capture_windows"] = tuple(tuple(r) for r in d["capture_windows"])
        if d.get("capture_declaration_sha256s") is not None:
            d["capture_declaration_sha256s"] = tuple(
                d["capture_declaration_sha256s"]
            )
        d["global_span"] = tuple(d.get("global_span", ("1992-02-18", "2026-07-27")))
        d["n_trials_sweep"] = tuple(d.get("n_trials_sweep", ()))
        spec = cls(**d)
        if claimed != spec.seal():
            raise ValueError(
                f"spec seal mismatch: file claims {claimed[:16]}... but the fields hash to "
                f"{spec.seal()[:16]}.... The spec was edited without re-sealing."
            )
        return spec


def _d(s: str | dt.date) -> dt.date:
    if isinstance(s, dt.date):
        return s
    return dt.date.fromisoformat(str(s)[:10])


#: Historical reconstruction surface.  It is deliberately separate from the current default:
#: old receipts can reproduce their v1 seal and caller-count fidelity semantics, while no new
#: caller accidentally gets those semantics by importing DEFAULT_SPEC.
LEGACY_DEFAULT_SPEC = GateSpec(
    spec_id="wf_gate_v1_balanced_proposal",
    authored_utc="2026-07-29T00:00:00+00:00",
    author_note="Historical gate-spec v1 reconstruction only.",
    schema=LEGACY_SCHEMA,
    fidelity_reference_policy=FidelityReferencePolicy.LEGACY_ANY_REFERENCE.value,
)


#: The proposal. Borhen picks the standard; this is what the author recommends and what
#: `phase5/ADMISSION_STANDARD_OPTIONS.md` scores as Option B (Balanced).
DEFAULT_SPEC = GateSpec(
    spec_id="wf_gate_v2_balanced_proposal",
    authored_utc="2026-07-29T00:00:00+00:00",
    author_note=(
        "Session W proposal, Option B (Balanced). Not an owner decision. See "
        "docs/audits/fable5-vision-audit-20260725/phase5/ADMISSION_STANDARD_OPTIONS.md "
        "for Options A (Strict) and C (Permissive) and for what each admits and rejects."
    ),
)
