"""The verdict. Out-of-sample only, cost-true, day-blocked, multiplicity-charged.

READING ORDER FOR A SCEPTIC
---------------------------
The three questions worth asking of any gate are: what could make it say yes when it should
say no; what does it refuse to answer; and who chose the threshold. In order:

**What could make it say yes wrongly.** Seven independent conditions must all hold for
`ADMIT`, and every one of them can fail on its own:

    fidelity        the generator reproduces this sleeve's class of decision
    coverage        broker truth priced at least `cost_coverage_floor` of its trades
    sample          enough trades overall and per fold, and enough evaluable folds
    expectancy      pooled OOS mean R net of cost exceeds `min_oos_mean_r`
    stability       at least `min_oos_positive_fold_frac` of OOS folds are positive
    robustness      deleting the single best OOS fold retains `min_drop_best_fold_retention`
                    of the headline expectancy
    significance    the family-corrected q-value clears `alpha` against a day-blocked null

`robustness` was added after `stability` failed its own adversary: a positive-fold-fraction
threshold at 0.50 is the coin-flip point and carries no information, and an absolute
leave-one-out floor of "> 0" is scale-blind. A synthetic sleeve with all its edge in one
fold pooled to +0.653 R/day, retained +0.0225 once its best fold was deleted, and reached
ADMIT. See `spec.min_drop_best_fold_retention`.

No in-sample statistic enters any of them. The IS numbers are computed and reported so
IS->OOS decay is visible, and they touch nothing.

**What it refuses.** `NOT_EVALUABLE` is a first-class outcome, not a soft fail. A sleeve
the generator cannot reproduce, or that broker truth cannot price, gets refused with the
reason attached — it is never scored on a partial basis and never given a benefit of the
doubt. Three of the twelve live market-expansion sleeves refuse on coverage alone.

**Who chose the threshold.** Not this file. `DEFAULT_SPEC` carries a proposal;
`phase5/ADMISSION_STANDARD_OPTIONS.md` sets out the alternatives with what each admits and
rejects. Sleeve composition and the admission standard are Borhen's, the same class as the
risk dial (`WAVE_5_WORKING_AGREEMENT.md` section 1).

WHAT IS COMPOSED RATHER THAN REBUILT
------------------------------------
Four components of `src/research_infra/validation_integrity/`: `dsr.deflated_sharpe_ratio`
(selection deflation), `pbo.pbo_cscv` (is the family's IS-best reverting to the OOS
median), `regime_inflation.regime_inflation_diagnostic` (is the scored window itself the
contamination — the one thing its own header says PBO and DSR "provably miss"), and
`walk_forward_oos.purged_embargoed_walkforward` (an independent, row-indexed replication of
the fold structure). They are telemetry beside the seven gates rather than gates themselves,
for a stated reason: DSR needs an honest `n_trials` and no trial-budget ledger exists
anywhere in this repo, so deflating a verdict on a number nobody measured would give the
gate a precision it has not earned. The DSR is reported across `spec.n_trials_sweep` so the
reader can see exactly where it would flip, which is the honest form of the same
information.

AMENDED 2026-07-29 (B600). **A ledger now exists.** The sentence above was true when it
was written and is no longer: `validation_integrity/trial_budget_ledger.TrialLedger` is an
append-only prospective log that every wave-6+ session writes to as it evaluates variants,
and `measured_n_trials()` combines it with the retrospective scan. `spec.n_trials` is
still a FLOOR by default, because a ledger that started on 2026-07-29 cannot retroactively
count the estate's own history — but the number is no longer unmeasurable, and a caller
that passes `n_trials=measured_n_trials(...)["n_trials"]` gets a deflation grounded in
counted look events. The sweep stays regardless; it is the honest form of the same
information whatever the point estimate is.

DIAGNOSTIC MODE
---------------
`run_gate(..., diagnose=True)` additionally attaches, per sleeve, the per-gate margins,
the failing folds / symbols / sessions, the cost decomposition, MFE-MAE aggregates and a
`prescription` naming the repair (`diagnostics.py`, FOURTH_REVIEW §2.2/§4.1). It exists
because a REJECT already contains the information about WHAT to fix and this file used to
flatten it into a sentence. It moves no verdict and relaxes no gate — there is a test that
runs the whole gate both ways and compares the verdicts field by field.
"""

from __future__ import annotations

import datetime as dt
import enum
import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from src.research_infra.validation_integrity import dsr as _dsr
from src.research_infra.validation_integrity import gauntlet as _gauntlet
from src.research_infra.validation_integrity import pbo as _pbo
from src.research_infra.validation_integrity import regime_inflation as _regime
from src.research_infra.validation_integrity import walk_forward_oos as _wfo
from src.research_infra.walkforward import stats as S
from src.research_infra.walkforward.fidelity import fidelity_for
from src.research_infra.walkforward.folds import (
    FoldSlice,
    assign_capture_folds,
    assign_folds,
    build_fold_calendar,
    validate_capture_windows,
)
from src.research_infra.walkforward.panel import (
    PricedTrade,
    SleeveCoverage,
    TradeRecord,
    build_daily_panel,
    price_trades,
)
from src.research_infra.walkforward.spec import LEGACY_SCHEMA as LEGACY_SPEC_SCHEMA
from src.research_infra.walkforward.spec import GateSpec

__all__ = ["Verdict", "SleeveVerdict", "GateResult", "run_gate"]

LEGACY_SCHEMA = "gtos.walkforward.gate_result.v1"
SCHEMA = "gtos.walkforward.gate_result.v2"


class Verdict(str, enum.Enum):
    ADMIT = "ADMIT"
    REJECT = "REJECT"
    NOT_EVALUABLE = "NOT_EVALUABLE"


@dataclass
class SleeveVerdict:
    sleeve: str
    verdict: Verdict
    reasons: list[str] = field(default_factory=list)
    gates: dict[str, Any] = field(default_factory=dict)
    telemetry: dict[str, Any] = field(default_factory=dict)
    coverage: dict[str, Any] = field(default_factory=dict)
    fidelity: dict[str, Any] = field(default_factory=dict)
    #: Set only under `coverage_policy="restrict_to_priced"` when the sleeve was evaluated
    #: on a subset of its configured universe. Travels with every downstream quote.
    universe_restriction: dict[str, Any] | None = None
    #: Set by `run_gate(..., diagnose=True)`. Per-gate margins, the failing folds /
    #: symbols / sessions, MFE-MAE aggregates, the cost decomposition, and the §2.2
    #: prescription. See `diagnostics.py` — it reads verdicts and cannot move one.
    diagnostics: dict[str, Any] | None = None
    folds: list[dict[str, Any]] = field(default_factory=list)
    #: Raw p before family correction; None when no null could be computed.
    p_raw: float | None = None
    q_value: float | None = None
    pooled_oos_mean_r: float | None = None
    n_trades: int = 0

    def as_dict(self, *, schema: str = SCHEMA) -> dict[str, Any]:
        fidelity = self.fidelity
        gates = self.gates
        if schema == LEGACY_SCHEMA:
            # gate-result v1 predates evidence-authority, lineage and precision fields.  A
            # historical v1 spec may reproduce that exact shape, but it must never produce a
            # v2-branded result whose nested semantics were legacy caller-count semantics.
            fidelity_keys = (
                "class",
                "basis",
                "reference_kind",
                "reference_recall",
                "live_recall",
                "basis_n",
                "basis_note",
                "source",
                "ceiling_stamp",
            )
            fidelity = {key: self.fidelity[key] for key in fidelity_keys if key in self.fidelity}
            gates = dict(self.gates)
            old_fidelity_gate_keys = (
                "pass",
                "floor",
                "reference_kind",
                "reference_recall",
                "live_recall",
            )
            if "fidelity" in gates:
                gates["fidelity"] = {
                    key: gates["fidelity"][key]
                    for key in old_fidelity_gate_keys
                    if key in gates["fidelity"]
                }
        return {
            "sleeve": self.sleeve,
            "verdict": self.verdict.value,
            "reasons": self.reasons,
            "gates": gates,
            "p_raw": self.p_raw,
            "q_value": self.q_value,
            "pooled_oos_mean_r": self.pooled_oos_mean_r,
            "n_trades": self.n_trades,
            "coverage": self.coverage,
            "fidelity": fidelity,
            "universe_restriction": self.universe_restriction,
            "folds": self.folds,
            "telemetry": self.telemetry,
            **({"diagnostics": self.diagnostics} if self.diagnostics else {}),
        }


@dataclass
class GateResult:
    spec: GateSpec
    verdicts: dict[str, SleeveVerdict]
    family: dict[str, Any] = field(default_factory=dict)
    #: Per-sleeve priced trades, kept only under `run_gate(..., diagnose=True)`. The
    #: diagnosis needs the trade population (cost terms, excursions, symbols, sessions),
    #: and re-pricing it outside the gate would be a second implementation of the one
    #: thing this package insists has exactly one (`panel.price_trades`).
    priced_by_sleeve: dict[str, list[PricedTrade]] = field(default_factory=dict)

    @property
    def admitted(self) -> list[str]:
        return sorted(s for s, v in self.verdicts.items() if v.verdict is Verdict.ADMIT)

    @property
    def rejected(self) -> list[str]:
        return sorted(s for s, v in self.verdicts.items() if v.verdict is Verdict.REJECT)

    @property
    def not_evaluable(self) -> list[str]:
        return sorted(s for s, v in self.verdicts.items() if v.verdict is Verdict.NOT_EVALUABLE)

    def as_dict(self) -> dict[str, Any]:
        result_schema = (
            LEGACY_SCHEMA if self.spec.schema == LEGACY_SPEC_SCHEMA else SCHEMA
        )
        return {
            "schema": result_schema,
            "spec_sha256": self.spec.seal(),
            "spec": self.spec.as_dict(),
            "summary": {
                "n_judged": len(self.verdicts),
                "n_admit": len(self.admitted),
                "n_reject": len(self.rejected),
                "n_not_evaluable": len(self.not_evaluable),
                "admitted": self.admitted,
                "rejected": self.rejected,
                "not_evaluable": self.not_evaluable,
            },
            "family": self.family,
            "sleeves": {
                s: v.as_dict(schema=result_schema)
                for s, v in sorted(self.verdicts.items())
            },
        }

    def repair_queue(self, *, server: str | None = None, run_label: str = "",
                     extra: dict[str, Any] | None = None) -> dict[str, Any]:
        """`REPAIR_QUEUE_V1.json` — every verdict as a prescription (§2.2, §4.1).

        Requires `run_gate(..., diagnose=True)`; without the priced population the
        cost-decomposition and excursion evidence would be missing and the three-way
        split on a negative expectancy could not be made, so it refuses rather than
        emitting a queue whose prescriptions are guesses.
        """
        from src.research_infra.walkforward.diagnostics import build_repair_queue

        if not self.priced_by_sleeve:
            raise ValueError(
                "no priced population on this GateResult — call run_gate(..., "
                "diagnose=True). A repair queue built without the trade population "
                "cannot tell a cost-geometry failure from an exit failure, and guessing "
                "between them is the whole thing this queue exists to stop."
            )
        return build_repair_queue(self, priced_by_sleeve=self.priced_by_sleeve,
                                  server=server, run_label=run_label, extra=extra)


# ======================================================================================


def _pooled_oos(slices: Sequence[FoldSlice], spec: GateSpec) -> tuple[list[float], list[float]]:
    """The OOS day series across evaluable folds, plus each day's pooling weight."""
    xs: list[float] = []
    ws: list[float] = []
    ev = [s for s in slices if s.evaluable]
    if not ev:
        return [], []
    for s in ev:
        n_days = len(s.test_r)
        if n_days == 0:
            continue
        if spec.pooling_weights == "equal_by_fold":
            w = 1.0 / n_days  # each fold contributes total weight 1
        elif spec.pooling_weights == "by_oos_trades":
            w = (s.n_test_trades / n_days) if n_days else 0.0
        else:  # by_oos_days
            w = 1.0
        xs.extend(s.test_r)
        ws.extend([w] * n_days)
    return xs, ws


def _sr_variance(daily_by_sleeve: dict[str, dict[dt.date, float]]) -> tuple[float | None, str]:
    """Cross-sleeve Sharpe dispersion for DSR, via the package's own estimator."""
    names = [s for s, d in daily_by_sleeve.items() if len(d) >= 2]
    if len(names) < 2:
        return None, "unavailable: fewer than 2 sleeves with a usable daily series"
    all_days = sorted(set().union(*[set(daily_by_sleeve[s]) for s in names]))
    matrix = [[daily_by_sleeve[s].get(d, 0.0) for s in names] for d in all_days]
    try:
        est = _gauntlet.estimate_sr_variance_from_sleeves(matrix)
    except (ValueError, ZeroDivisionError) as e:  # pragma: no cover - defensive
        return None, f"unavailable: {type(e).__name__}: {e}"
    return float(est["sr_variance"]), (
        "estimated_from_per_sleeve_sharpe_dispersion_pop_ddof0 over "
        f"{len(names)} sleeves x {len(all_days)} days "
        "(validation_integrity/gauntlet.estimate_sr_variance_from_sleeves)"
    )


def _dsr_sweep(series: Sequence[float], sr_var: float | None, spec: GateSpec) -> dict:
    if sr_var is None or len(series) < 2:
        return {"available": False, "reason": "sr_variance unavailable or series too short"}
    out: dict[str, Any] = {"available": True, "sr_variance": sr_var, "sweep": {}}
    for n in spec.n_trials_sweep:
        try:
            r = _dsr.deflated_sharpe_ratio(list(series), n_trials=int(n), sr_variance=sr_var)
        except (ValueError, ZeroDivisionError) as e:
            out["sweep"][str(n)] = {"error": f"{type(e).__name__}: {e}"}
            continue
        out["sweep"][str(n)] = {
            "dsr": r["dsr"], "significant": r["significant"],
            "sr_benchmark": r["sr_benchmark"], "sr_per_period": r["sr_per_period"],
        }
    at = out["sweep"].get(str(spec.n_trials), {})
    out["at_spec_n_trials"] = {"n_trials": spec.n_trials, **at}
    return out


def _regime_inflation(daily: dict[dt.date, float], first_oos: dt.date, spec: GateSpec) -> dict:
    """Is the scored period a favourable regime rather than a representative sample?

    Composed from `validation_integrity/regime_inflation.py:203`, which exists precisely
    because — in its own words — "PBO and DSR provably miss" window-as-selection-surface
    inflation. This gate's `stability` and `robustness` gates are cruder proxies for the
    same worry, so the real instrument is run alongside them.

    `selection_window_start` is the first OOS fold's start, which makes the question
    "is the period this sleeve was SCORED on unrepresentative of its own full history,
    including the initial train block it was never scored on?"

    Telemetry, not a gate. `recommended_magnitude_haircut` is the number an owner sizing off
    `pooled_oos_mean_r` needs, and publishing a haircut is not the same as failing a sleeve.
    """
    ds = sorted(daily.items())
    if len(ds) < 30:
        return {"available": False, "reason": f"only {len(ds)} daily observations"}
    try:
        r = _regime.regime_inflation_diagnostic(ds, first_oos, int(spec.n_trials))
    except (ValueError, ZeroDivisionError, KeyError) as e:
        return {"available": False, "reason": f"{type(e).__name__}: {e}"}
    # The composed module carried a sign defect: `fwd_all_mean_ratio = mean_in_window /
    # mean_all` was tested with `ratio >= 1.5`, a POSITIVE threshold, so once mean_all went
    # negative the flag became structurally unreachable and the diagnostic was defeated
    # monotonically by making the concealed loss bigger. This gate guarded it locally.
    #
    # FIXED IN THE MODULE 2026-07-29 (B451): the ratio thresholds now apply only when
    # `mean_all > 0`, and `mean_win > 0 >= mean_all` is its own contamination class. The
    # local override below is kept — it is one line, it costs nothing, and it now doubles as
    # a CROSS-CHECK: if `negative_ratio_override` is ever True while
    # `contamination_flag_upstream` is False, the module has regressed. A test pins that
    # agreement (`tests/research_infra/test_vig_regime_inflation_sign.py`).
    ratio = r["fwd_all_mean_ratio"]
    neg_ratio = isinstance(ratio, (int, float)) and ratio is not None and ratio < 0
    return {
        "available": True,
        "selection_window_start": first_oos.isoformat(),
        "fwd_all_mean_ratio": ratio,
        "inflation_basis": r.get("inflation_basis"),
        "sign_flip_contamination": r.get("sign_flip_contamination"),
        "contamination_flag": bool(r["contamination_flag"] or neg_ratio),
        "contamination_flag_upstream": r["contamination_flag"],
        "negative_ratio_override": neg_ratio,
        "guard_agrees_with_module": bool(r["contamination_flag"]) or not neg_ratio,
        "recommended_magnitude_haircut": r["recommended_magnitude_haircut"],
        # The haircut is a `min` of two terms under a floor, so the number alone cannot be read.
        # Carried through 2026-07-30 (Session AU, B1560) because the first receipt to publish this
        # field beside a headline (AR handoff item 2) hit an arm where the value was the FLOOR and
        # the module's own prose called it "~1.0". `selection_surface_penalty` is the term that
        # usually binds and it was not surfaced here at all.
        "haircut_binding_term": r.get("haircut_binding_term"),
        "haircut_at_floor": r.get("haircut_at_floor"),
        "selection_surface_penalty": r.get("selection_surface_penalty"),
        "selection_surface_evaluable": r.get("selection_surface_evaluable"),
        "regime_basis_haircut": r.get("regime_basis_haircut"),
        "holdout_are_topk": r["holdout_are_topk"],
        "n_total_years": r["n_total_years"],
        "verdict": r["verdict"],
        "note": ("telemetry, not a gate. A set contamination_flag means the scored window's "
                 "mean is unrepresentative of the sleeve's own history; shrink any deployed "
                 "magnitude by the haircut before sizing -- but read `haircut_binding_term` and "
                 "`haircut_at_floor` first: at the floor the number is a clamp, not an estimate."),
    }


def _wfo_crosscheck(daily: dict[dt.date, float], spec: GateSpec) -> dict:
    """Independent replication through the package's row-indexed walk-forward.

    Different axis (rows, not calendar) and different embargo convention (a fraction of the
    series, not measured holds), so agreement is evidence and disagreement is a flag worth
    reading — not an error in either.
    """
    ds = sorted(daily.items())
    if len(ds) < 8:
        return {"available": False, "reason": f"only {len(ds)} daily observations"}
    try:
        r = _wfo.purged_embargoed_walkforward(
            ds, n_folds=max(2, spec.n_folds - 1),
            embargo_frac=spec.crosscheck_embargo_frac,
            expanding=True, stat="mean",
        )
    except ValueError as e:  # pragma: no cover - defensive
        return {"available": False, "reason": f"{type(e).__name__}: {e}"}
    return {
        "available": True,
        "n_folds_evaluated": r["n_folds_evaluated"],
        "mean_is": r["mean_is_sharpe"],
        "mean_oos": r["mean_oos_sharpe"],
        "aggregate_degradation_pct": r["aggregate_degradation_pct"],
        "oos_positive_fold_frac": r["oos_positive_fold_frac"],
        "embargo_frac": spec.crosscheck_embargo_frac,
        "note": ("row-indexed cross-check (validation_integrity/walk_forward_oos), stat=mean. "
                 "Different axis (rows, not calendar) and a one-sided row-gap embargo rather "
                 "than a two-sided label-span purge, so agreement is evidence and "
                 "disagreement is a flag, not an error in either."),
    }


def _family_pbo(daily_by_sleeve: dict[str, dict[dt.date, float]]) -> dict:
    names = [s for s, d in daily_by_sleeve.items() if len(d) >= 2]
    if len(names) < 2:
        return {"available": False, "reason": "PBO needs >= 2 sleeve columns"}
    all_days = sorted(set().union(*[set(daily_by_sleeve[s]) for s in names]))
    if len(all_days) < 4:
        return {"available": False, "reason": f"only {len(all_days)} rows"}
    n_part = min(16, len(all_days))
    if n_part % 2:
        n_part -= 1
    if n_part < 2:
        return {"available": False, "reason": "cannot form an even partition count >= 2"}
    matrix = [[daily_by_sleeve[s].get(d, 0.0) for s in names] for d in all_days]
    try:
        r = _pbo.pbo_cscv(matrix, n_partitions=n_part, metric="mean")
    except ValueError as e:
        return {"available": False, "reason": f"{type(e).__name__}: {e}"}
    return {
        "available": True, "pbo": r["pbo"], "n_partitions": r["n_partitions"],
        "n_strategies": r["n_strategies"], "n_combinations": r["n_combinations"],
        "subsampled": r["subsampled"], "sleeves": names,
        "note": "IS-best sleeve's OOS rank across combinatorially symmetric splits; "
                "PBO >= 0.5 means the family's winner reverts to the OOS median",
    }


# ======================================================================================


def run_gate(
    trades_by_sleeve: dict[str, Iterable[TradeRecord]],
    spec: GateSpec | None = None,
    *,
    costs: Any = None,
    diagnose: bool = False,
    server: str | None = None,
    capture_windows: Sequence[Sequence[str | dt.date]] | None = None,
) -> GateResult:
    """Judge a family of sleeves under one sealed spec.

    `trades_by_sleeve` maps sleeve name -> generated trades. Every sleeve passed in is
    judged, and every sleeve judged is counted in the multiplicity correction — including
    the ones that end up NOT_EVALUABLE for coverage or fidelity, because they were still
    hypotheses someone looked at. Silently dropping them would shrink the family and make
    the survivors easier to admit, which is the failure this correction exists to prevent.

    `diagnose=True` turns on the fixing-machine head (`diagnostics.py`, FOURTH_REVIEW
    §4.1): every verdict additionally carries per-gate margins, the failing folds /
    symbols / sessions, the cost decomposition, MFE-MAE aggregates and a `prescription`.
    It changes no verdict and relaxes no gate — it keeps the numbers the gate already
    computed instead of flattening them into reason strings — and it costs one extra pass
    over the priced trades, which are retained on the result rather than re-priced.
    `server` (e.g. "FTMO-Server3") puts the session buckets on the broker's own wall
    clock; without it they fall back to UTC and say so.

    Independently materialized, non-contiguous captures are authority only when sealed in
    ``spec.capture_windows`` with their declaration identity and hashes. The unchanged
    equal-calendar builder runs separately inside each window and only its scored slices are
    concatenated. The optional ``capture_windows`` argument is a compatibility assertion:
    it must equal the sealed windows and can never define or replace them at runtime.
    """
    spec = spec or GateSpec(
        spec_id="ad_hoc", authored_utc=dt.datetime.now(dt.timezone.utc).isoformat()
    )
    runtime_capture_ranges = (
        validate_capture_windows(spec, capture_windows)
        if capture_windows is not None
        else None
    )
    if runtime_capture_ranges is not None and spec.capture_windows is None:
        raise ValueError(
            "runtime capture windows cannot define gate authority; seal them in GateSpec"
        )
    capture_ranges = (
        validate_capture_windows(spec, spec.capture_windows)
        if spec.capture_windows is not None
        else None
    )
    if (
        runtime_capture_ranges is not None
        and runtime_capture_ranges != capture_ranges
    ):
        raise ValueError(
            "runtime capture window replacement forbidden: supplied windows differ from "
            "the sealed GateSpec authority"
        )
    capture_contract: dict[str, Any] | None = None
    if capture_ranges is not None:
        capture_contract = {
            "schema": "gtos.walkforward.capture_windows.v2",
            "mode": "equal_calendar_folds_over_each_predeclared_capture_window",
            "authority": "immutable_gate_spec",
            "declaration_id": spec.capture_declaration_id,
            "declaration_sha256s": list(
                spec.capture_declaration_sha256s or ()
            ),
            "windows": [
                [lo.isoformat(), hi.isoformat()] for lo, hi in capture_ranges
            ],
            "touching_boundaries": [
                {
                    "left_end": left[1].isoformat(),
                    "right_start": right[0].isoformat(),
                }
                for left, right in zip(capture_ranges, capture_ranges[1:])
                if right[0] == left[1] + dt.timedelta(days=1)
            ],
            "touching_policy": (
                "allowed only as an explicitly declared independent-capture boundary; "
                "fold and null blocks restart there"
            ),
            "reserved_blackout": [list(window) for window in spec.reserved_blackout],
            "gate_spec_sha256": spec.seal(),
            "fold_rule": spec.fold_rule,
            "scope": (
                "capture definitions, ordering, blackout, and declaration identity are "
                "sealed; all admission thresholds remain unchanged"
            ),
        }
        capture_contract["sha256"] = hashlib.sha256(
            json.dumps(
                capture_contract,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
    verdicts: dict[str, SleeveVerdict] = {}
    per_sleeve_daily: dict[str, dict[dt.date, float]] = {}
    pending: list[tuple[str, list[float], list[float]]] = []
    kept_priced: dict[str, list[PricedTrade]] = {}

    for sleeve, raw in trades_by_sleeve.items():
        trades = list(raw)
        if capture_ranges is not None:
            outside = sorted(
                {
                    trade.day(spec.day_key)
                    for trade in trades
                    if not any(
                        lo <= trade.day(spec.day_key) <= hi
                        for lo, hi in capture_ranges
                    )
                }
            )
            if outside:
                raise ValueError(
                    f"{sleeve} has trade days outside declared capture windows: "
                    + ",".join(day.isoformat() for day in outside[:10])
                )
            escaped = []
            for trade in trades:
                key_day = trade.day(spec.day_key)
                owner = next(
                    ((lo, hi) for lo, hi in capture_ranges if lo <= key_day <= hi),
                    None,
                )
                if owner is None:  # already reported above
                    continue
                label_lo, label_hi = trade.spans()
                if label_lo < owner[0] or label_hi > owner[1]:
                    escaped.append(f"{key_day}:{label_lo}..{label_hi}")
            if escaped:
                raise ValueError(
                    f"{sleeve} trade label spans exit their owning capture window: "
                    + ",".join(escaped[:10])
                )
        sv = SleeveVerdict(sleeve=sleeve, verdict=Verdict.NOT_EVALUABLE, n_trades=len(trades))
        verdicts[sleeve] = sv

        # ---- gate 1: generator fidelity -------------------------------------------------
        fid = fidelity_for(sleeve)
        sv.fidelity = {
            "class": fid.cls.value, "basis": fid.basis.value,
            "measurement_schema": fid.measurement_schema,
            "evidence_authority": fid.evidence_authority.value,
            "reference_kind": fid.reference_kind.value,
            "reference_lineage_sha256": fid.reference_lineage_sha256,
            "generated_lineage_sha256": fid.generated_lineage_sha256,
            "reference_recall": fid.reference_recall,
            "reference_precision": fid.precision,
            "precision_supported": fid.precision_supported,
            "live_recall": (
                fid.live_recall if fid.reference_kind.value == "live_record" else None
            ),
            "counts": {
                "agreed": fid.basis_agreed,
                "reference_only": fid.basis_live_only,
                "generated_only": fid.basis_port_only,
            },
            "basis_n": fid.basis_n,
            "basis_note": fid.basis_note, "source": fid.source,
            "ceiling_stamp": fid.ceiling_stamp(spec.fidelity_floor),
        }
        refusal = fid.refusal_reason(
            spec.fidelity_floor,
            reference_policy=spec.fidelity_reference_policy,
            precision_floor=spec.fidelity_precision_floor,
        )
        sv.gates["fidelity"] = {
            "pass": refusal is None,
            "floor": spec.fidelity_floor,
            "reference_policy": spec.fidelity_reference_policy,
            "precision_floor": spec.fidelity_precision_floor,
            "measurement_schema": fid.measurement_schema,
            "evidence_authority": fid.evidence_authority.value,
            "reference_kind": fid.reference_kind.value,
            "reference_recall": fid.reference_recall,
            "reference_precision": fid.precision,
            "precision_supported": fid.precision_supported,
            "live_recall": (
                fid.live_recall if fid.reference_kind.value == "live_record" else None
            ),
        }
        if refusal is not None and spec.fidelity_refusal_is_hard:
            sv.reasons.append(refusal)
            # The VERDICT still refuses — the floor is sealed and this changes nothing
            # about it. But a refused sleeve is exactly the one a repair session needs a
            # diagnosis for (FOURTH_REVIEW §2.1: a fidelity gap is a work item on the
            # engine or the spec, never a reason the economics are unknowable), so under
            # `diagnose` the population is priced anyway and the repair queue gets its
            # cost decomposition, holds and excursions.
            if diagnose:
                kept_priced[sleeve] = [
                    p for p in price_trades(trades, spec, costs=costs)[0]
                    if p.trade.sleeve == sleeve
                ]
            continue

        # The fidelity register keys on the sleeve NAME alone, so relabelling a 30%-recall
        # first-of-day sleeve as a per-bar one walks straight through the gate above. An
        # adversarial refuter did exactly that. Checking the trades' symbols against the
        # production registry's universe for that sleeve makes the name claim falsifiable.
        allow = (spec.sleeve_symbol_allowlist or {}).get(sleeve)
        if allow is None:
            sv.gates["symbol_consistency"] = {
                "pass": True, "checked": False,
                "reason": ("no sleeve_symbol_allowlist supplied; the sleeve name was taken "
                           "on trust. Build one with "
                           "walkforward.registry.build_symbol_allowlist(config, profile)."),
            }
        else:
            seen = sorted({t.symbol for t in trades})
            stray = [x for x in seen if x not in set(allow)]
            sv.gates["symbol_consistency"] = {
                "pass": not stray, "checked": True,
                "expected_symbols": sorted(allow), "observed_symbols": seen,
                "unexpected_symbols": stray,
            }
            if stray:
                sv.reasons.append(
                    f"symbol_mismatch: {sleeve} is registered on {sorted(allow)} but was "
                    f"handed trades on {stray}. Either the trades are mislabelled or the "
                    f"registry is stale; both make the fidelity record meaningless."
                )
                if diagnose:
                    kept_priced[sleeve] = [
                        p for p in price_trades(trades, spec, costs=costs)[0]
                        if p.trade.sleeve == sleeve
                    ]
                continue

        # ---- gate 2: cost coverage ------------------------------------------------------
        priced, cov_map = price_trades(trades, spec, costs=costs)
        if diagnose:
            kept_priced[sleeve] = [p for p in priced if p.trade.sleeve == sleeve]
        cov: SleeveCoverage | None = cov_map.get(sleeve)
        sv.coverage = cov.as_dict() if cov else {}
        cov_frac = cov.coverage_frac if cov else 0.0
        cov_ok = cov_frac >= spec.cost_coverage_floor
        sv.gates["cost_coverage"] = {
            "pass": cov_ok, "coverage_frac": round(cov_frac, 6),
            "floor": spec.cost_coverage_floor,
            "policy": spec.coverage_policy,
            "weakest_coverage": cov.weakest_coverage.value if cov and cov.weakest_coverage else None,
        }
        if not cov_ok:
            unpriced_syms = sorted({
                p.trade.symbol for p in priced
                if p.status == "unpriced" and p.trade.sleeve == sleeve
            })
            priced_syms = sorted({
                p.trade.symbol for p in priced
                if p.status == "priced" and p.trade.sleeve == sleeve
            })
            sv.gates["cost_coverage"]["unpriceable_symbols"] = unpriced_syms
            sv.gates["cost_coverage"]["priceable_symbols"] = priced_syms
            if spec.coverage_policy == "refuse" or cov_frac < spec.min_retained_trade_frac:
                why = (
                    "policy=refuse"
                    if spec.coverage_policy == "refuse"
                    else f"retained {cov_frac:.1%} < min_retained_trade_frac "
                         f"{spec.min_retained_trade_frac:.0%} — a sleeve reduced this far is "
                         f"not that sleeve"
                )
                sv.reasons.append(
                    f"cost_coverage_below_floor: src.costs priced {cov_frac:.1%} of this "
                    f"sleeve's trades, floor {spec.cost_coverage_floor:.0%} ({why}). "
                    f"Unpriceable symbols: {unpriced_syms}. Reasons: "
                    f"{cov.unpriced_reasons if cov else {}}. An unpriced trade is unpriced, "
                    f"not free — filling it with a plausible number is F38."
                )
                continue
            # restrict_to_priced: proceed on the priceable subset, loudly.
            sv.gates["cost_coverage"]["pass"] = True
            sv.gates["cost_coverage"]["restricted"] = True
            # The stamp used to assert "Broker truth has no measured spread for {syms}" for
            # EVERY refusal, while the actual reason sat in `cov.unpriced_reasons` and was
            # printed only on the below-floor branch above. It cost a session a draft:
            # AF §3.3's first version routed `NATGAS.cash` to a spread capture on the
            # strength of this sentence, and its spread was already MEASURED — the refusals
            # were `commission.kind = 'unknown'` and an unresolved broker symbol. Session AP
            # then measured that there were TWO refusals rather than the one AF's correction
            # named. A stamp that names the wrong cause is worse than a stamp that names
            # none, so it now carries the layer's own words.
            reasons = dict(cov.unpriced_reasons) if cov and cov.unpriced_reasons else {}
            sv.gates["cost_coverage"]["unpriced_reasons"] = reasons
            sv.universe_restriction = {
                "policy": "restrict_to_priced",
                "retained_trade_frac": round(cov_frac, 6),
                "dropped_symbols": unpriced_syms,
                "evaluated_symbols": priced_syms,
                "unpriced_reasons": reasons,
                "stamp": (
                    f"PARTIAL UNIVERSE: evaluated on {len(priced_syms)} of "
                    f"{len(priced_syms) + len(unpriced_syms)} symbols "
                    f"({cov_frac:.1%} of trades). `src.costs` refused {unpriced_syms} for: "
                    f"{sorted(reasons) or 'no reason recorded'}. This verdict is about the "
                    f"restricted sleeve, not the sleeve as configured. The restriction is "
                    f"set by what the cost layer can price, not by results, so it does not "
                    f"bias the estimate — but it does narrow the claim, and the refusal "
                    f"reason is what says whether it is repairable."
                ),
            }
            sv.reasons.append(sv.universe_restriction["stamp"])

        # ---- panel and folds ------------------------------------------------------------
        daily_map, counts = build_daily_panel(priced, spec)
        daily = daily_map.get(sleeve, {})
        if not daily:
            sv.reasons.append("no priced trades produced a daily observation")
            continue
        per_sleeve_daily[sleeve] = daily

        capture_meta: dict[str, Any] | None = None
        if capture_ranges is None:
            span_lo, span_hi = min(daily), max(daily)
            folds = build_fold_calendar(spec, span_lo, span_hi)
            slices = assign_folds(priced, daily, folds, spec)
            initial_train_ranges = (
                [(folds[0].oos_start, folds[0].oos_end)] if folds else []
            )
        else:
            slices, capture_meta = assign_capture_folds(
                priced,
                daily,
                capture_ranges,
                spec,
            )
            capture_meta["capture_contract_sha256"] = capture_contract["sha256"]
            sv.telemetry["fold_capture"] = capture_meta
            initial_train_ranges = [
                (dt.date.fromisoformat(lo), dt.date.fromisoformat(hi))
                for lo, hi in capture_meta["initial_train_ranges"]
            ]
        sv.folds = [s.as_dict() for s in slices]

        ev = [s for s in slices if s.evaluable]
        n_thin = sum(1 for s in slices if s.status == "test_thin")
        thin_frac = (n_thin / len(slices)) if slices else 0.0

        if capture_meta is not None:
            evaluable_fold_ids = {
                row.fold.fold_id for row in slices if row.evaluable
            }
            missing_capture_ids = [
                capture["capture_id"]
                for capture in capture_meta["captures"]
                if not evaluable_fold_ids.intersection(
                    capture["composite_scored_fold_ids"]
                )
            ]
            sv.gates["capture_completeness"] = {
                "pass": not missing_capture_ids,
                "n_captures_declared": len(capture_meta["captures"]),
                "n_captures_evaluable": (
                    len(capture_meta["captures"]) - len(missing_capture_ids)
                ),
                "captures_without_evaluable_oos": missing_capture_ids,
                "rule": "every sealed capture must contribute an evaluable OOS slice",
            }
            if missing_capture_ids:
                sv.verdict = Verdict.NOT_EVALUABLE
                sv.reasons.append(
                    "capture_not_evaluable: sealed captures "
                    + ",".join(str(value) for value in missing_capture_ids)
                    + " contributed no evaluable OOS slice"
                )
                continue

        # LIFETIME ACCOUNTING. Every priced trade, in any fold, scored or not — plus the
        # gross R of whatever the blackout removed. Fold 0 is never scored, so without this
        # block a sleeve's entire early history is invisible to every gate while still
        # counting toward the sample floor.
        all_net = [p.r_net for p in priced
                   if p.status == "priced" and p.trade.sleeve == sleeve and p.r_net is not None]
        f0 = [p.r_net for p in priced
              if p.status == "priced" and p.trade.sleeve == sleeve and p.r_net is not None
              and any(lo <= p.trade.day(spec.day_key) <= hi
                      for lo, hi in initial_train_ranges)]
        scored_trade_r = [
            p.r_net for p in priced
            if p.status == "priced" and p.trade.sleeve == sleeve and p.r_net is not None
            and any(s.fold.oos_start <= p.trade.day(spec.day_key) <= s.fold.oos_end
                    for s in ev)
        ]
        lifetime_mean = (math.fsum(all_net) / len(all_net)) if all_net else float("nan")
        sv.telemetry["lifetime"] = {
            "n_priced_trades_all_folds": len(all_net),
            "sum_r_net_all_folds": math.fsum(all_net) if all_net else 0.0,
            "mean_r_net_per_trade_all_folds": lifetime_mean,
            "fold0_unscored": {
                "n_trades": len(f0),
                "sum_r_net": math.fsum(f0) if f0 else 0.0,
                "mean_r_net": (math.fsum(f0) / len(f0)) if f0 else None,
                "note": (
                    "Each capture's local fold 0 is an initial train block and is never "
                    "scored. Published because those rows are otherwise invisible to every "
                    "OOS gate."
                    if capture_ranges is not None
                    else "fold 0 is the initial train block and is never scored. Published "
                    "because it is otherwise invisible to every gate."
                ),
            },
            "blackout_removed": {
                "n_trades": cov.n_blackout_dropped if cov else 0,
                "sum_r_gross": cov.blackout_r_gross if cov else 0.0,
            },
            "n_scored_oos_trades": len(scored_trade_r),
        }
        # Sample floor counts only trades that reached a SCORED fold. Counting fold-0
        # trades toward it meant hiding losses there actively helped a sleeve qualify.
        n_scored_sample = sum(s.n_train_trades + s.n_test_trades for s in ev)
        sv.gates["sample"] = {
            "pass": (n_scored_sample >= spec.min_trades_total
                     and len(ev) >= spec.min_folds_evaluable
                     and thin_frac <= spec.max_thin_fold_frac),
            "n_trades_in_scored_folds": n_scored_sample,
            "n_priced_trades_all_folds": len(all_net),
            "min_trades_total": spec.min_trades_total,
            "n_folds_evaluable": len(ev), "min_folds_evaluable": spec.min_folds_evaluable,
            "n_folds_total": len(slices),
            "n_thin_folds": n_thin, "thin_fold_frac": thin_frac,
            "max_thin_fold_frac": spec.max_thin_fold_frac,
            "fold_status": {s.fold.fold_id: s.status for s in slices},
        }
        if not sv.gates["sample"]["pass"]:
            sv.verdict = Verdict.NOT_EVALUABLE
            sv.reasons.append(
                f"insufficient_sample: {n_scored_sample} trades in scored folds (need "
                f"{spec.min_trades_total}) across {len(ev)} evaluable folds (need "
                f"{spec.min_folds_evaluable}); {n_thin} thin folds "
                f"({thin_frac:.0%}, max {spec.max_thin_fold_frac:.0%}); fold status "
                f"{sv.gates['sample']['fold_status']}"
            )
            continue

        # ---- pooled OOS, with the pooling weights folded into the series ----------------
        xs, ws = _pooled_oos(slices, spec)
        scaled = S.apply_pooling_weights(xs, ws)
        null_segment_lengths: tuple[int, ...] | None = None
        if capture_meta is not None:
            segmented_raw: list[float] = []
            segment_lengths: list[int] = []
            for capture in capture_meta["captures"]:
                fold_ids = set(capture["composite_scored_fold_ids"])
                capture_slices = [
                    row for row in slices if row.fold.fold_id in fold_ids
                ]
                capture_xs, _capture_ws = _pooled_oos(capture_slices, spec)
                if not capture_xs:
                    continue
                segmented_raw.extend(capture_xs)
                segment_lengths.append(len(capture_xs))
            if segmented_raw != xs or sum(segment_lengths) != len(scaled):
                raise RuntimeError(
                    "capture segment assembly drifted from pooled OOS ordering"
                )
            null_segment_lengths = tuple(segment_lengths)
        pooled_mean = (math.fsum(scaled) / len(scaled)) if scaled else float("nan")
        sv.pooled_oos_mean_r = pooled_mean
        pending.append((sleeve, scaled, xs))

        fold_means = [
            (math.fsum(s.test_r) / len(s.test_r)) for s in ev if s.test_r
        ]
        # A thin fold is excluded from the pooled statistic but NOT from the stability
        # count. Excluding it from both created a perverse incentive: measured, a sleeve
        # ADMITs at 7 losers in a bad fold and REJECTs at 8, because the 8th made the fold
        # fat enough to be scored. Trading less during a bad regime must not buy a pass.
        n_stability_denom = len(fold_means) + n_thin
        pos_frac = (
            sum(1 for m in fold_means if m > 0) / n_stability_denom
            if n_stability_denom else 0.0
        )

        per_trade = (
            math.fsum(scored_trade_r) / len(scored_trade_r) if scored_trade_r else float("nan")
        )
        per_trade_ok = (
            True if spec.min_oos_mean_r_per_trade is None
            else (math.isfinite(per_trade) and per_trade > spec.min_oos_mean_r_per_trade)
        )
        sv.gates["expectancy"] = {
            "pass": bool(pooled_mean > spec.min_oos_mean_r and per_trade_ok),
            "pooled_oos_mean_r": pooled_mean, "min_oos_mean_r": spec.min_oos_mean_r,
            "pooling_weights": spec.pooling_weights,
            # Day-mean is the right clustering control and the wrong economics: a day with
            # 12 losers weighs the same as a day with one winner. Measured, a sleeve with
            # 2,688 losers of 2,913 trades and -715.8 R lifetime pooled to +0.305 R/DAY.
            "oos_mean_r_per_trade": per_trade,
            "min_oos_mean_r_per_trade": spec.min_oos_mean_r_per_trade,
            "per_trade_pass": per_trade_ok,
            "n_scored_oos_trades": len(scored_trade_r),
        }
        sv.gates["lifetime"] = {
            "pass": (True if spec.min_lifetime_mean_r is None
                     else (math.isfinite(lifetime_mean)
                           and lifetime_mean > spec.min_lifetime_mean_r)),
            "enabled": spec.min_lifetime_mean_r is not None,
            "mean_r_net_per_trade_all_folds": lifetime_mean,
            "min_lifetime_mean_r": spec.min_lifetime_mean_r,
            "n_priced_trades_all_folds": len(all_net),
            "note": ("full-sample per-trade expectancy INCLUDING the never-scored fold 0. "
                     "Closes the three concealment attacks at once: nothing can be hidden "
                     "from a lifetime total."),
        }
        sv.gates["stability"] = {
            "pass": pos_frac >= spec.min_oos_positive_fold_frac,
            "oos_positive_fold_frac": pos_frac,
            "min_oos_positive_fold_frac": spec.min_oos_positive_fold_frac,
            "fold_means": fold_means,
            "n_thin_folds_counted_as_non_positive": n_thin,
            "denominator": n_stability_denom,
        }

        # Leave-one-fold-out: delete the sleeve's single best OOS fold and re-pool. An edge
        # that is really one good regime does not survive this; a persistent one barely
        # notices. Recomputed on the weighted series so it is the same statistic, not a
        # different one that happens to be cheaper.
        if spec.min_oos_mean_r_drop_best_fold is None or len(ev) < 2:
            sv.gates["robustness"] = {
                "pass": True, "enabled": spec.min_oos_mean_r_drop_best_fold is not None,
                "reason": ("disabled by spec" if spec.min_oos_mean_r_drop_best_fold is None
                           else f"only {len(ev)} evaluable fold(s); nothing to drop"),
            }
        else:
            best_id = max(
                (s for s in ev if s.test_r),
                key=lambda s: math.fsum(s.test_r) / len(s.test_r),
            ).fold.fold_id
            kept = [s for s in slices if s.evaluable and s.fold.fold_id != best_id]
            xs2, ws2 = _pooled_oos(kept, spec)
            scaled2 = S.apply_pooling_weights(xs2, ws2) if xs2 else []
            drop_mean = (math.fsum(scaled2) / len(scaled2)) if scaled2 else float("nan")
            retention = (
                drop_mean / pooled_mean
                if math.isfinite(drop_mean) and math.isfinite(pooled_mean) and pooled_mean > 0
                else float("nan")
            )
            abs_ok = math.isfinite(drop_mean) and drop_mean > spec.min_oos_mean_r_drop_best_fold
            ret_ok = (
                True if spec.min_drop_best_fold_retention is None
                else (math.isfinite(retention)
                      and retention >= spec.min_drop_best_fold_retention)
            )
            sv.gates["robustness"] = {
                "pass": bool(abs_ok and ret_ok),
                "enabled": True,
                "dropped_fold_id": best_id,
                "pooled_oos_mean_r_excl_best_fold": drop_mean,
                "retention": retention,
                "absolute_floor": spec.min_oos_mean_r_drop_best_fold,
                "retention_floor": spec.min_drop_best_fold_retention,
                "absolute_pass": abs_ok,
                "retention_pass": ret_ok,
                "delta_vs_full": (
                    drop_mean - pooled_mean if math.isfinite(drop_mean) else None
                ),
            }

        # ---- the null -------------------------------------------------------------------
        if spec.block_days == "auto":
            block = (
                S.block_length_auto_segmented(
                    scaled,
                    null_segment_lengths,
                    min_blocks=spec.min_blocks,
                )
                if null_segment_lengths is not None
                else S.block_length_auto(scaled, min_blocks=spec.min_blocks)
            )
        else:
            block = max(1, int(spec.block_days))
        floor = S.perm_p_floor(
            len(scaled),
            block,
            spec.n_permutation,
            segment_lengths=null_segment_lengths,
        )
        null = S.combined_null_p(
            scaled, block=block, mode=spec.null_test,
            n_boot=spec.n_bootstrap, n_perm=spec.n_permutation, seed=spec.seed,
            segment_lengths=null_segment_lengths,
        )
        sv.p_raw = null["p_value"]
        sv.telemetry["null"] = null
        sv.telemetry["p_floor"] = floor
        sv.telemetry["pooling_leverage"] = S.weighted_effective_n(ws)
        sv.telemetry["dependence"] = {
            "lag1_autocorr_oos_days": S.lag1_autocorr(xs),
            "lag1_autocorr_weighted_series": S.lag1_autocorr(scaled),
            "effective_n_oos_days": S.effective_n(xs),
            "n_oos_days": len(xs),
            "block_days_used": block,
            "block_rule": spec.block_days,
            "capture_segment_lengths": (
                list(null_segment_lengths)
                if null_segment_lengths is not None
                else None
            ),
        }

        # ---- in-sample telemetry (never a gate) -----------------------------------------
        is_means = [(math.fsum(s.train_r) / len(s.train_r)) for s in ev if s.train_r]
        mean_is = (math.fsum(is_means) / len(is_means)) if is_means else float("nan")
        sv.telemetry["in_sample"] = {
            "mean_is_r": mean_is,
            "mean_oos_r": pooled_mean,
            "is_to_oos_degradation_pct": (
                (mean_is - pooled_mean) / abs(mean_is) * 100.0
                if math.isfinite(mean_is) and abs(mean_is) > 1e-12 else float("nan")
            ),
            "note": "reported so IS->OOS decay is visible; enters no gate",
        }
        sv.telemetry["walk_forward_oos_crosscheck"] = _wfo_crosscheck(daily, spec)
        first_oos = min((s.fold.oos_start for s in ev), default=None)
        sv.telemetry["regime_inflation"] = (
            _regime_inflation(daily, first_oos, spec) if first_oos
            else {"available": False, "reason": "no evaluable fold"}
        )
        sv.telemetry["purge"] = {
            "total_purged_trades": sum(s.n_purged_trades for s in slices),
            "embargo_days_by_fold": {s.fold.fold_id: s.embargo_days for s in slices},
            "embargo_rule": spec.embargo_rule,
            "embargo_quantile": spec.embargo_quantile,
        }
        sv.telemetry["blackout"] = {
            "n_trades_dropped": cov.n_blackout_dropped if cov else 0,
            "ranges": [list(r) for r in spec.reserved_blackout],
            "reason": spec.blackout_reason,
        }

    # ---- family-level: multiplicity, DSR, PBO --------------------------------------------
    fam_names = [s for s, _, _ in pending]
    fam_p = [verdicts[s].p_raw for s in fam_names]
    # The family is every sleeve JUDGED, not just those that reached a p-value.
    n_judged = len(verdicts)
    # Multiplicity is corrected WITHIN a run. Submitting 20 sleeves one at a time gives 20
    # uncorrected tests: measured, P(>=1 junk admission per campaign) goes 8.3% -> 71.7%.
    # `declared_family_size` lets the caller state the true number of hypotheses the
    # campaign considered, and the correction uses the larger of the two.
    #
    # It is on the caller's honour only when typed by hand. `walkforward/candidate_family.py`
    # supplies the accountable path: a family named PROSPECTIVELY, with a ratchet so a
    # withdrawal cannot shrink the bill, resolved into the spec by `with_declared_family()`
    # so the declaration's id and sha256 travel in the seal. The struck half of the old
    # comment -- "no persistent trial ledger exists in this repo" -- was already false:
    # `research/operations/trial_budget/TRIAL_LEDGER.jsonl` holds 4,785 look events. A
    # retrospective count is still the wrong instrument for an admission bill, because it is
    # read after the outcomes are; that is the gap the declaration closes, not the ledger.
    effective_family = max(n_judged, spec.declared_family_size or 0)
    n_padded = effective_family - len(fam_names)
    padded_p = list(fam_p) + [1.0] * n_padded

    if spec.multiplicity == "benjamini_hochberg":
        corr = S.benjamini_hochberg(padded_p, spec.alpha)
    elif spec.multiplicity == "bonferroni":
        corr = S.bonferroni(padded_p, spec.alpha)
    else:
        corr = {"rejected": [(p is not None and math.isfinite(p) and p <= spec.alpha)
                             for p in padded_p],
                "qvalues": [p if p is not None else 1.0 for p in padded_p],
                "threshold": spec.alpha, "k": 0, "m": len(padded_p), "alpha": spec.alpha}

    sr_var, sr_note = _sr_variance(per_sleeve_daily)

    for i, sleeve in enumerate(fam_names):
        sv = verdicts[sleeve]
        sv.q_value = corr["qvalues"][i]
        sig = bool(corr["rejected"][i])
        sv.gates["significance"] = {
            "pass": sig, "p_raw": sv.p_raw, "q_value": sv.q_value,
            "alpha": spec.alpha, "multiplicity": spec.multiplicity,
            "family_size": corr["m"],
            "declared_family_id": spec.declared_family_id,
            "note": (
                f"family size {corr['m']} = max(sleeves judged in this run = {n_judged}, "
                f"declared_family_size = {spec.declared_family_size}). "
                f"{len(fam_names)} reached a null; {n_padded} were refused earlier or "
                f"declared-but-not-run and are carried at p=1.0 so they cannot shrink the "
                f"family. "
                + (f"The declared size comes from {spec.declared_family_id}, a prospective "
                   f"declaration (walkforward/candidate_family.py), so this q-value names "
                   f"the exact list of looks it was corrected against."
                   if spec.declared_family_id else
                   "The declared size was typed by the caller and names no artifact: it is "
                   "honest but unattributable. `candidate_family.with_declared_family()` is "
                   "the attributable path.")
            ),
        }
        scaled = next(sc for nm, sc, _ in pending if nm == sleeve)
        sv.telemetry["dsr"] = _dsr_sweep(scaled, sr_var, spec)
        sv.telemetry["dsr"]["sr_variance_source"] = sr_note

        # If the sign-flip's structural p-floor is at or above alpha, no sleeve on this
        # series can EVER be significant, and a REJECT would be a statement about the
        # series' length and dependence rather than about the sleeve. Refuse instead.
        fl = sv.telemetry.get("p_floor", {})
        if float(fl.get("p_floor", 0.0)) >= spec.alpha:
            sv.verdict = Verdict.NOT_EVALUABLE
            sv.gates["significance"]["pass"] = False
            sv.gates["significance"]["p_floor_binds"] = True
            sv.reasons.insert(0, (
                f"insufficient_independent_blocks: the block sign-flip null over "
                f"{fl.get('n_blocks')} blocks cannot produce a p below "
                f"{fl.get('p_floor'):.5f}, which is at or above alpha={spec.alpha}. "
                f"{fl.get('n_obs')} OOS days at block length {fl.get('block')} do not "
                f"support a significance test at this level. This is a statement about the "
                f"evidence available, not about the sleeve."
            ))
            continue

        core = ("expectancy", "lifetime", "stability", "robustness", "significance")
        failed = [g for g in core if not sv.gates.get(g, {}).get("pass")]
        if failed:
            sv.verdict = Verdict.REJECT
            for g in failed:
                sv.reasons.append(_reject_reason(g, sv, spec))
        else:
            sv.verdict = Verdict.ADMIT
            restriction = (
                " " + sv.universe_restriction["stamp"] if sv.universe_restriction else ""
            )
            sv.reasons.append(
                f"ADMIT: pooled OOS mean {sv.pooled_oos_mean_r:.5f} R/day net of broker-true "
                f"cost over {sv.gates['sample']['n_folds_evaluable']} purged/embargoed folds; "
                f"{sv.gates['stability']['oos_positive_fold_frac']:.0%} of OOS folds positive; "
                f"q={sv.q_value:.4g} at {spec.multiplicity} alpha={spec.alpha} across a family "
                f"of {corr['m']}. {sv.fidelity['ceiling_stamp']}{restriction}"
            )

    family = {
        "cost_model_window_disclosure": _cost_window_note(spec),
        "multiplicity": {**{k: v for k, v in corr.items() if k != "rejected"},
                         "method": spec.multiplicity,
                         "family_members_with_null": fam_names,
                         "family_members_padded_at_p1": n_padded,
                         "n_sleeves_judged_this_run": n_judged,
                         "declared_family_size": spec.declared_family_size,
                         "declared_family_id": spec.declared_family_id,
                         "declared_family_sha256": spec.declared_family_sha256,
                         "declared_family_basis": (
                             "prospective_declaration" if spec.declared_family_id
                             else ("typed_by_caller" if spec.declared_family_size
                                   else "this_run_only")),
                         "effective_family_size": effective_family},
        "sr_variance": sr_var,
        "sr_variance_source": sr_note,
        "pbo": _family_pbo(per_sleeve_daily),
        "n_trials_basis": spec.n_trials_basis,
        "wipeout": _wipeout(verdicts),
    }
    if capture_contract is not None:
        family["fold_capture_contract"] = capture_contract
    result = GateResult(spec=spec, verdicts=verdicts, family=family,
                        priced_by_sleeve=kept_priced if diagnose else {})

    # ---- the fixing-machine head. Runs LAST, reads only what is already decided --------
    if diagnose:
        from src.research_infra.walkforward.diagnostics import diagnose_sleeve

        for sleeve, sv in verdicts.items():
            sv.diagnostics = diagnose_sleeve(
                sv, spec, priced=kept_priced.get(sleeve, ()), server=server
            ).as_dict()
    return result


#: Refusals that mean "this run could not judge anything", as distinct from "this run
#: judged and said no". Each entry is the literal PREFIX of a reason string some site in
#: this package actually writes, and every one is checked against its emitter below:
#:
#:   `port_fidelity_unmeasured`     fidelity.py:264
#:   `port_fidelity_below_floor`    fidelity.py:270
#:   `fidelity_evidence_unstructured` fidelity.py
#:   `fidelity_reference_policy_mismatch` fidelity.py
#:   `fidelity_precision_unmeasured` fidelity.py
#:   `fidelity_precision_below_floor` fidelity.py
#:   `symbol_mismatch`              gate.py:478
#:   `cost_coverage_below_floor`    gate.py:523
#:   `no priced trades produced`    gate.py:555
#:
#: CORRECTED 2026-07-30 by an adversarial pass over this block's first version, which
#: listed `symbol_outside_registry_universe`. **No reason string anywhere in the tree starts
#: with that token** — the universe-restriction text begins `"PARTIAL UNIVERSE: ..."` and is
#: a *stamp on a scored sleeve*, not a refusal, so it must NOT be a wipeout class at all. A
#: census that names a bucket nothing can ever fall into is the same defect in miniature as
#: the one this function exists to catch: it reads as coverage it does not have. The two
#: genuinely-missing classes it was standing in for are now here.
_WIPEOUT_CLASSES = (
    "port_fidelity_unmeasured",
    "port_fidelity_below_floor",
    "fidelity_evidence_unstructured",
    "fidelity_reference_policy_mismatch",
    "fidelity_precision_unmeasured",
    "fidelity_precision_below_floor",
    "symbol_mismatch",
    "cost_coverage_below_floor",
    "no priced trades produced",
)


def _wipeout(verdicts: dict[str, SleeveVerdict]) -> dict:
    """Did EVERY sleeve fail for the same infrastructural reason? Say so, loudly.

    Added 2026-07-30 (Session AQ, B1429) after a run of 72 arms came back 100 %
    NOT_EVALUABLE on `port_fidelity_unmeasured` — because the caller had not wrapped the
    gate in `family.fidelity_scope`, which every research cohort outside the production
    registry needs. Nothing in the result said that. The arms tabulated cleanly, one per
    entry hour and cost band, and read exactly like a measurement of the entry hour.

    That is the silent-null class the wave-10 agreement makes a standing rule
    ("silent nulls fall loudly"), in its most expensive form: a whole grid of nothing that
    looks like a grid of something. This block is the sound. It changes no verdict — it
    reports a property of the verdicts already decided — and a caller that ignores it is at
    least ignoring something rather than not being told.
    """
    if not verdicts:
        return {"wiped_out": False, "n_judged": 0, "reason": "no sleeves submitted"}
    n = len(verdicts)
    scored = [s for s, v in verdicts.items() if v.p_raw is not None]
    if scored:
        return {"wiped_out": False, "n_judged": n, "n_scored": len(scored)}
    counts: dict[str, int] = {}
    for v in verdicts.values():
        for cls in _WIPEOUT_CLASSES:
            if any(str(r).startswith(cls) for r in v.reasons):
                counts[cls] = counts.get(cls, 0) + 1
                break
        else:
            counts["other"] = counts.get("other", 0) + 1
    # deterministic: count desc, then class name asc. `max` alone breaks ties by dict
    # insertion order, which is trade-arrival order and therefore not reproducible.
    dominant = min(sorted(counts), key=lambda k: (-counts[k], k))
    return {
        "wiped_out": True,
        "n_judged": n, "n_scored": 0,
        "dominant_class": dominant,
        "n_in_dominant_class": counts[dominant],
        "by_class": dict(sorted(counts.items())),
        "note": (
            f"NOT ONE of {n} submitted sleeves reached a null; {counts[dominant]} failed on "
            f"`{dominant}`. This result measures the harness, not the sleeves — do not "
            f"tabulate it as a verdict grid."
            + (" `port_fidelity_unmeasured` on a research cohort almost always means the "
               "caller needs `family.fidelity_scope(members)` around `run_gate`."
               if dominant.startswith("port_fidelity_unmeasured") else "")
        ),
    }


def _cost_window_note(spec: GateSpec | None = None) -> dict:
    """The broker-truth artifact is measured in the near-present and charged to the past.

    `TICK_SPREAD_MEASUREMENT.json` measures spread over **2026-06-18 to 2026-07-24**, 37
    days, and `cost_r` charges that single p50 as a constant to every trade regardless of
    era (`model.py:347-372`); commission is fitted from the same July-2026 deal export and
    swap from current symbol specs. On the market-expansion pilot, whose panel runs
    2007-2026 with only 6.5% of trades in 2026 at all, cost came to **33%-219% of gross R**
    and flipped two sleeves from gross-positive to net-negative on its own.

    **Two sentences that used to be here are struck, and the correction is the point.**
    They read: *"Not a defect that can be fixed here — it is the only tick measurement that
    exists"* and *"The bias direction is knowable a priori: retail CFD/FX spreads
    compressed materially over that period, so historical trades are systematically
    UNDER-costed."*

    The first is now false. MT5's bar ``spread`` column records a spread per bar back to
    2000, so the era term is measurable, and `spread_model_v1` measures it (Session AG).
    The second is **half right, and the wrong half is the dangerous one**: the bias does
    not have a single sign.

        EURUSD 2000-2003    50x the snapshot   FX history IS under-costed
        USDJPY 2000-2003    20x
        XAUUSD 2020-2024   0.18x               metals history is OVER-costed
        US30   2021-2024   0.61-0.85x          indices likewise
        UKOIL  2021-2025   0.25-0.60x

    A "knowable a priori" direction that is inverted for metals, indices and energy is not
    a disclosure, it is a wrong prior — and three of the four armed sleeves trade exactly
    those families. Set `GateSpec.spread_band` to "low"/"mid"/"high" and the era is charged
    instead of assumed; a sleeve that admits at "high" is robust to the look-ahead.
    """
    band = getattr(spec, "spread_band", None) if spec is not None else None
    if band:
        from src.costs.spread_model import (
            DEFAULT_COMPOSITION,
            ERA_HOUR_EXPONENT,
            ERA_HOUR_EXPONENT_ENVELOPE,
        )
        comp = getattr(spec, "spread_composition", None) or DEFAULT_COMPOSITION
        expo = getattr(spec, "spread_era_exponent", None)
        return {
            "mode": f"spread_model[{comp}]",
            "band": band,
            "composition": comp,
            "era_hour_exponent": (None if comp == "v1_multiplicative"
                                  else (ERA_HOUR_EXPONENT if expo is None else float(expo))),
            "artifact": "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json",
            "applied_to": "each trade at its own quarter's measured era ratio",
            "direction_of_bias": (
                "charged rather than assumed. The era term is measured per symbol per "
                "quarter and it is signed both ways: FX history under-costed by up to 50x, "
                "metals/index/energy history OVER-costed by up to 5x"),
            "composition_note": (
                "the era and hour terms compose as anchor x era_ratio**b x hour_mult with "
                f"b = {ERA_HOUR_EXPONENT} (envelope {list(ERA_HOUR_EXPONENT_ENVELOPE)}), "
                "MEASURED by Session AH on three axes. b = 1 is the pre-2026-07-30 "
                "product, which AF found reaches 198x-880x the modern base on pre-2010 FX "
                "and which is REJECTED at 5.0 sigma on the affected class"
                if comp != "v1_multiplicative" else
                "b = 1: the UNVALIDATED product AF filed as a defect. Selected explicitly, "
                "so presumably to reproduce a pre-2026-07-30 number"),
            "residual_look_ahead": (
                "bands narrow the look-ahead, they do not eliminate it. The era instrument "
                "is validated at ratios 0.78-1.30 (188 held-out block pairs, skill 0.334) "
                "and at one 7-month out-of-sample point (-0.45%); nothing validates it at "
                "the 20x-50x the pre-2010 FX eras imply, and the composition exponent is "
                "measured over 2x-25x level ranges and extrapolated to 50x. Only forward "
                "tick capture closes either."),
            "status": "MEASURED with published bands; capture is what tightens them",
        }
    return {
        "mode": "flat_37_day_snapshot",
        "measured_window_broker_wall": ["2026-06-18", "2026-07-24"],
        "applied_to": "every trade in the panel, regardless of era",
        "artifact": "research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json",
        "direction_of_bias": (
            "UNSIGNED and material. Measured by spread_model_v1: FX history is under-costed "
            "(EURUSD 2000-2003 at 50x this snapshot, USDJPY 20x) while metals, index and "
            "energy history is OVER-costed (XAUUSD 2020-2024 at 0.18x, US30 2021-2024 at "
            "0.61-0.85x). The earlier claim here -- that spreads compressed so pre-2026 "
            "trades are systematically under-costed -- holds for FX only and is INVERTED "
            "for the families three of the four armed sleeves trade."),
        "magnitude_on_the_mx_pilot": "cost was 33%-219% of gross R",
        "status": (
            "NO LONGER UNAVOIDABLE. Set GateSpec.spread_band to 'low'/'mid'/'high' to "
            "charge the measured era instead of this snapshot."),
    }


def _reject_reason(gate: str, sv: SleeveVerdict, spec: GateSpec) -> str:
    g = sv.gates[gate]
    if gate == "expectancy":
        if not g.get("per_trade_pass", True):
            return (
                f"REJECT expectancy (per trade): OOS mean {g['oos_mean_r_per_trade']:.5f} "
                f"R/TRADE net of broker-true cost <= {g['min_oos_mean_r_per_trade']} over "
                f"{g['n_scored_oos_trades']} scored trades, even though the per-DAY mean is "
                f"{g['pooled_oos_mean_r']:.5f}. Day aggregation was flattering it."
            )
        return (
            f"REJECT expectancy: pooled OOS mean {g['pooled_oos_mean_r']:.5f} R/day net of "
            f"broker-true cost <= {g['min_oos_mean_r']} (pooling={g['pooling_weights']})"
        )
    if gate == "lifetime":
        return (
            f"REJECT lifetime: full-sample mean {g['mean_r_net_per_trade_all_folds']:.5f} "
            f"R/trade over {g['n_priced_trades_all_folds']} priced trades (INCLUDING the "
            f"never-scored fold 0) <= {g['min_lifetime_mean_r']}. The scored window is "
            f"positive and the sleeve's own history is not."
        )
    if gate == "stability":
        return (
            f"REJECT stability: only {g['oos_positive_fold_frac']:.0%} of OOS folds positive, "
            f"floor {g['min_oos_positive_fold_frac']:.0%}; fold means "
            f"{[round(m, 5) for m in g['fold_means']]}. An edge that lives in one fold is a "
            f"regime, not an edge."
        )
    if gate == "robustness":
        ret = g.get("retention")
        ret_s = f"{ret:.1%}" if isinstance(ret, float) and math.isfinite(ret) else "undefined"
        return (
            f"REJECT robustness: dropping the single best OOS fold (fold "
            f"{g.get('dropped_fold_id')}) takes the pooled expectancy from "
            f"{sv.pooled_oos_mean_r:.5f} to "
            f"{g.get('pooled_oos_mean_r_excl_best_fold'):.5f} R/day — {ret_s} retained "
            f"against a floor of {g.get('retention_floor')}. The result was carried by one "
            f"fold; that is a regime, not an edge."
        )
    return (
        f"REJECT significance: q={g['q_value']:.4g} (raw p={g['p_raw']:.4g}) fails "
        f"{g['multiplicity']} at alpha={g['alpha']} across a family of {g['family_size']}"
    )
