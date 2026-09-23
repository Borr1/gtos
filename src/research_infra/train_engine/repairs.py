"""CD-2 -- the repaired-stack injection, one repair at a time, each with a control.

Session CD, B2251-B2258. The four sealed January arms ran the OLD engine. This
module is where "the repaired stack" stops being a phrase and becomes a set of
named, individually switchable, individually measured changes to what the replay
COMPUTES.

## The distinction this module exists to keep

`cuts` may not change an outcome; a cut that does is a bug. **A repair exists to
change one.** They are separate flags (`--patches` vs `--repairs`) and separate
receipts for exactly that reason: a receipt that could not tell them apart would
let a speed regression hide inside an economic result.

## Every repair carries an INERT CONTROL, and that is the load-bearing part

For each repair there is a second patch id that installs the **same wrapper on
the same symbol** and computes the **same intermediate quantities**, then applies
a neutral value. If the engine is outcome-identical with the control installed,
the plumbing is proved inert and every difference the live repair produces is
attributable to the repaired NUMBER rather than to the act of wrapping.

That is a stronger control than "run without the flag", which proves only that an
un-applied patch does nothing.

## What was found NOT to apply, which is a finding and not a failure

The commission named four repairs. Two of them have no surface on this path, and
the code says so rather than this docstring:

* **The AQ time-stop contract (`96 -> 7680`) does not exist here.** The B7.5
  replay never imports `execution_packets`, never reads `SLEEVE_EXIT_PROFILES`
  and has no sleeve identity in its exit path at all. Its exit is first-touch
  target/stop, and its horizon is a flat **120-minute wall clock**
  (`REPAIRED_PENDING_EXPIRY_MINUTES = 120`,
  `replay_acceleration_attempt5_typed_sparse_runner.py:116`, applied at
  `:16164`/`:16745`; expiry built at
  `v4_timewarp_simulated_live_research_loop.py:85864-85866`). A live sleeve's
  7,680 M15 bars is 80 days; the replay cannot hold a position for 2 hours and 1
  minute. There is nothing to port.
  **But the audit found something else at that hook, and it IS a defect** --
  see `swap_horizon_true` below.
* **The spread-geometry FLOOR AT GENERATION is not rebind-reachable, and the
  ADMISSION limit is already enforced.** `config/agent_config.yaml:715-716`
  declares `selected_cell_pretrade_max_spread_r: 0.10` and
  `selected_cell_pretrade_max_total_cost_r: 0.15`; the replay enforces both
  through `broker_net_cost_engine.pretrade_cost_refusal_reasons:718-728,772-776`
  and consumes the refusal as a hard reject at
  `v4_timewarp:86204-86224`. The broad generator sees closed OHLC bars and never
  a tick (`rg -n "spread" src/components/broader_origin_generators.py` -> no
  hits), so a floor cannot be applied where the candidate is proposed without new
  plumbing. AY's `ultimate_book/spread_geometry.py` is imported by `run_book.py`
  and `book_engine.py` only -- it is a LIVE-path artifact and does not reach
  replay. The cost-tail question CD-3 asks is therefore answered as an ANALYSIS
  over the regenerated pool, not as an engine repair.

## What DOES apply

| repair | direction | one-line mechanism |
|---|---|---|
| `commission_broker_true` | charges MORE | the replay hardcodes `commission_r: 0.0` |
| `swap_horizon_true` | charges LESS | the swap model prices an 8-hour hold on a path whose maximum hold is 2 hours |
| `spread_input_truth` | charges LESS on 20/24 symbols | the quote synthesis charges a per-row CONSTANT (config spec points x point, or the admission floor table) on every symbol without a tick source -- SPX500 16.7x, NAS100 28.6x broker truth (B5 C3) |
| `cost_ruler_harmonize` | either | a packet whose component sum cannot complete gets a flat 0.12 total regardless of the components that exist (B5 C4-A) |

The first two push in opposite directions, which is why they are separable
flags and why the delta table reports each alone as well as together.
`--repairs cost_truth` is the composed R-COST-TRUTH stack in its required
install order.

## R-BELIEF (FA Phase C spec section 3 -- added after R-COST-TRUTH committed)

| repair | direction | one-line mechanism |
|---|---|---|
| `belief_cost_single_charge` | fewer admissions | ATOMIC: cost_r + candidate_direction wired into the debate (live parity); the probability_thesis add-back keeps every downstream subtraction at exactly ONE charge; p-gates re-baselined by the median-cost logit; per-row 0x/1x/2x census |
| `belief_hash_term_removal` | ~0 | deletes `family_hash*0.04` from follow_strength -- 0.45 pp of probability from a sha of the family NAME |
| `belief_confidence_constant_retire` | exactly 0 (proven per row) | the 0.55 constant x 0.20 weight leaves the score sum; with/without stamped |
| `belief_ev_walked_contract` | STAND DOWN | EV/expected_net repriced at the walked 2.0R-capped-giveback contract from the January cell table; EV can finally go NEGATIVE, p* published |
| `belief_fill_probability_deweight` | near-rank-inert | the 0.92-template score terms dropped; honest magnitude is P1-blocked and says so |

`--repairs belief` is the bundle in its required order; `--repairs
belief_honesty` is T2 arm (ii) as one flag (cost_truth + belief). The
context-wire-only form is REFUSED by name (`REFUSED_REPAIR_FORMS`).
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import math
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.research_infra.fast_engine import accel
from src.research_infra.train_engine.decision_semantics import (
    TRUSTED_COMMISSION_REPAIR_SOURCE,
    assess_cost_components,
    cost_component_capture_evidence_from_packet,
    cost_component_sum,
    cost_number,
    publish_cost_assessment,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

#: Session J's vendored broker-truth cost layer, and the loader AW used when he
#: priced F38 over the January pool. Reusing his exact call chain is deliberate:
#: two independent implementations of "broker-true commission" would be two
#: numbers, and the estate would have no way to tell which one the pool was
#: charged with.
BROKER_TRUE_COSTS_V1 = (
    REPO_ROOT
    / "research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json"
)

#: The profile whose symbol map resolves canonical -> broker symbol. AW used this
#: one (`aw_separability_mine.py:179`); the account key is `FTMO` either way, and
#: using a different profile would silently price a different broker.
COMMISSION_PROFILE = REPO_ROOT / "config/profiles/operator_profile.yaml"
COMMISSION_ACCOUNT = "FTMO"

#: The replay's own horizon, in minutes. `REPAIRED_PENDING_EXPIRY_MINUTES` in the
#: attempt5 runner, and the same number bounds the terminal path query
#: (`path_source_and_oracle(after=asof, until=expiry)`), so it is a HARD ceiling
#: on a B7.5 hold, not a typical value.
REPLAY_MAX_HOLD_MINUTES = 120.0
#: Minutes per bar the swap model assumes
#: (`selected_cell_swap_cost_minutes_per_bar`, set at `attempt5:10276-10278`).
SWAP_MODEL_MINUTES_PER_BAR = 15.0
#: What the sealed config charges: 32 bars x 15 min = 8 hours.
SEALED_SWAP_HORIZON_BARS = 32.0
#: What the path can actually reach: 120 min / 15 = 8 bars.
TRUE_SWAP_HORIZON_BARS = REPLAY_MAX_HOLD_MINUTES / SWAP_MODEL_MINUTES_PER_BAR

#: Modules that bind the two rebound symbols by name. `v4_timewarp:55` does
#: `from src.components.broker_net_cost_engine import build_pretrade_cost_packet`,
#: so the timewarp module's OWN global is what the hot caller resolves -- the
#: same trap `cuts.HASH_SYMBOL_MODULES` documents.
TIMEWARP = "src.research_infra.v4_timewarp_simulated_live_research_loop"
COST_ENGINE = "src.components.broker_net_cost_engine"
#: The attempt-5 runner module, rebound by the neutral-seed replicate dial. Its
#: `selection_sizing_factorial_binding_from_args` is resolved through module
#: globals at both call sites (`:15693` run path, `:18577` finalize path), so a
#: module-attribute rebind reaches every consumer.
ATTEMPT5 = "src.research_infra.replay_acceleration_attempt5_typed_sparse_runner"


@dataclass
class _RepairStats:
    calls: int = 0
    applied: int = 0
    neutral: int = 0
    unpriced: int = 0
    charged_r_sum: float = 0.0
    charged_r_max: float = 0.0
    #: What the FROZEN engine would have charged where the repair charged
    #: `charged_r_sum` instead. For the commission repair this is 0.0 by
    #: construction (F38's zero); for the spread-input repair it is the constant
    #: the model price replaced, so `baseline - charged` is the per-run reduction
    #: without re-reading a single pool row.
    baseline_r_sum: float = 0.0
    per_symbol: dict[str, dict[str, float]] = field(default_factory=dict)
    errors: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "calls": self.calls,
            "applied": self.applied,
            "neutral": self.neutral,
            "unpriced": self.unpriced,
            "charged_r_sum": round(self.charged_r_sum, 8),
            "charged_r_mean": (
                round(self.charged_r_sum / self.applied, 8) if self.applied else 0.0
            ),
            "charged_r_max": round(self.charged_r_max, 8),
            "baseline_r_sum": round(self.baseline_r_sum, 8),
            "baseline_r_mean": (
                round(self.baseline_r_sum / self.applied, 8) if self.applied else 0.0
            ),
            "per_symbol": {
                symbol: {
                    "n": int(row["n"]),
                    "sum_r": round(row["sum_r"], 8),
                    "mean_r": round(row["sum_r"] / row["n"], 8) if row["n"] else 0.0,
                    "baseline_sum_r": round(row.get("baseline_sum_r", 0.0), 8),
                }
                for symbol, row in sorted(self.per_symbol.items())
            },
            "errors": dict(sorted(self.errors.items())),
        }


REPAIR_STATS: dict[str, _RepairStats] = {}
_LOCK = threading.Lock()


def repair_report() -> dict[str, Any]:
    """Per-repair counters. Always reported, like `cuts.cut_report`.

    A repair that fired zero times is the failure mode worth catching -- a run
    that silently charged nothing would otherwise read exactly like a run whose
    repair had no effect.
    """

    return {name: stats.as_dict() for name, stats in REPAIR_STATS.items()}


def reset_repair_stats() -> None:
    REPAIR_STATS.clear()


class RepairUnavailable(RuntimeError):
    """A repair was requested that this module cannot honour. Never silent."""


# ---------------------------------------------------------------------------
# repair 1 -- broker-true commission (F38)
# ---------------------------------------------------------------------------
#
# `v4_timewarp.broker_calibrated_replay_cost_packet:58965-58966` writes
#
#     "commission_r": 0.0,
#     "commission_r_source": "commission_included_in_selected_cell_risk_status",
#
# onto every cost packet, and `total_cost_r` is `spread_r + slippage_r + swap_r`
# with no commission term (`broker_net_cost_engine.py:577-583`). The gate that
# was supposed to catch this is satisfied by a STRING: `commission_model_required`
# is true (`agent_config.yaml:730`) and the replay stamps
# `gtos_vnext_commission_model_status = "COMMISSION_INCLUDED_IN_SELECTED_CELL_RISK"`
# (`v4_timewarp:58895`), which is in `DEFAULT_ALLOWED_COMMISSION_STATUSES`. So the
# requirement is met by an assertion and the accounting is zero. That is F38 in
# its exact shape, and it is worse than "the sum omits a term": a control exists,
# and it passes.
#
# The charge is AW's, verbatim (`aw_separability_mine.py:171-223`,
# `src/costs/model.py:16`):
#
#     commission_r = commission_usd_per_lot / (sl_distance_price * usd_per_price_unit_per_lot)
#
# Commission in R is a property of the TRADE, not of the instrument, because the
# denominator is the stop distance.


class _CommissionPricer:
    """Per-symbol broker-true commission, resolved once and cached."""

    def __init__(self) -> None:
        self._records: dict[str, Any] = {}
        self._resolve: Any = None
        self._costs: Any = None
        self._ready = False

    def _load(self) -> None:
        if self._ready:
            return
        import yaml

        from src.components.ultimate_book.symbol_map import (
            build_broker_symbol_resolver,
        )
        from src.costs.model import load_broker_true_costs

        profile = yaml.safe_load(COMMISSION_PROFILE.read_text()) or {}
        self._resolve = build_broker_symbol_resolver(profile)
        self._costs = load_broker_true_costs(BROKER_TRUE_COSTS_V1)
        self._ready = True

    def record_for(self, symbol: str) -> Any:
        self._load()
        if symbol not in self._records:
            from src.costs.model import CostTruthError

            try:
                broker = self._resolve(symbol)
                self._records[symbol] = self._costs.instrument(
                    COMMISSION_ACCOUNT, broker
                )
            except (CostTruthError, KeyError, TypeError, ValueError) as exc:
                self._records[symbol] = exc
        return self._records[symbol]

    def commission_r(
        self, *, symbol: str, entry_price: float | None, sl_distance: float | None
    ) -> tuple[float | None, str]:
        """Round-turn commission in R, or `(None, reason)`. Never guesses."""

        from src.costs.model import (
            CostTruthError,
            _usd_per_price_unit_per_lot,
            commission_usd_per_lot,
        )

        if not sl_distance or sl_distance <= 0:
            return None, "no_stop_distance"
        record = self.record_for(symbol)
        if isinstance(record, Exception):
            return None, f"unpriced_instrument:{type(record).__name__}"
        try:
            usd, _detail = commission_usd_per_lot(record, entry_price)
            per_unit = _usd_per_price_unit_per_lot(record)
        except CostTruthError as exc:
            return None, f"cost_truth:{str(exc)[:60]}"
        if not per_unit:
            return None, "no_usd_per_price_unit"
        return float(usd) / (float(sl_distance) * float(per_unit)), "broker_true"


_PRICER = _CommissionPricer()


def _packet_number(value: Any) -> float | None:
    status, number = cost_number(value)
    return number if status == "valid" else None


def _apply_broker_true_commission_capture(
    packet: dict[str, Any],
    *,
    measured_commission_r: float,
    charge_r: float,
    source: str,
    regate: bool,
) -> dict[str, Any]:
    """Heal the whole packet contract after the out-of-band commission lookup.

    The old wrapper changed only the top-level ``commission_r`` and added a
    non-zero charge to an already-emitted total.  When the frozen builder could
    not resolve its own commission schedule, it had already replaced the
    missing total with 0.12R.  A measured zero commission was therefore falsy,
    left that fallback untouched, and left the nested ``commission_cost`` in
    ``source_gap``.  Re-gating could never clear the missing-commission reason.

    This helper updates the nested authority packet and re-decodes the total
    from the four captured components.  It does not invent a missing component;
    if spread is absent, the legacy fallback remains visibly non-authoritative.
    """

    before_total_status, before_total = cost_number(packet.get("total_cost_r"))
    before_reasons = list(packet.get("refusal_reasons") or ())
    raw_components = packet.get("total_cost_components")
    components = dict(raw_components) if isinstance(raw_components, Mapping) else {}
    original_components = dict(components)
    legacy_fallback_candidate = _packet_number(
        components.get("authority_fallback_total_cost_r")
    )
    original_commission_status, _ = cost_number(
        original_components.get("commission_r")
    )
    original_commission_cost = packet.get("commission_cost")
    original_commission_cost = (
        original_commission_cost
        if isinstance(original_commission_cost, Mapping)
        else {}
    )
    legacy_fallback = (
        0.12
        if before_total_status == "valid"
        and before_total is not None
        and legacy_fallback_candidate is not None
        and math.isclose(before_total, 0.12, rel_tol=0.0, abs_tol=1e-12)
        and math.isclose(
            legacy_fallback_candidate,
            0.12,
            rel_tol=0.0,
            abs_tol=1e-12,
        )
        and original_commission_status != "valid"
        and original_commission_cost.get("source_status") != "captured"
        and original_commission_cost.get("included_in_total_cost_r") is not True
        else None
    )

    measured_status, measured_number = cost_number(measured_commission_r)
    charge_status, charge_number = cost_number(charge_r)
    trusted_source = source == TRUSTED_COMMISSION_REPAIR_SOURCE
    valid_capture = bool(
        measured_status == "valid"
        and charge_status == "valid"
        and trusted_source
        and measured_number is not None
        and charge_number is not None
        and math.isclose(
            measured_number,
            charge_number,
            rel_tol=0.0,
            abs_tol=1e-8,
        )
    )
    raw_commission_cost = packet.get("commission_cost")
    commission_cost = (
        dict(raw_commission_cost)
        if isinstance(raw_commission_cost, Mapping)
        else {}
    )
    packet["commission_cost"] = commission_cost
    packet["commission_r"] = charge_number if charge_number is not None else charge_r
    packet["commission_r_source"] = source
    packet["commission_r_broker_true_measured"] = (
        measured_number if measured_number is not None else measured_commission_r
    )
    packet["commission_r_repair_status"] = (
        "applied" if valid_capture else "refused_invalid_commission_capture"
    )
    packet["commission_r_regated"] = bool(regate)
    packet["commission_r_repair_selection_semantics"] = (
        "broker_cost_gate_recomputed" if regate else "selection_held_fixed"
    )

    components["commission_r"] = (
        charge_number if charge_number is not None else charge_r
    )
    packet["total_cost_components"] = components

    commission_cost.update(
        {
            "source_status": "captured" if valid_capture else "invalid",
            "cost_r": charge_number if charge_number is not None else charge_r,
            "broker_true_measured_cost_r": (
                measured_number
                if measured_number is not None
                else measured_commission_r
            ),
            "included_in_total_cost_r": valid_capture,
            "missing_fields": (
                []
                if valid_capture
                else ["valid_trusted_broker_true_commission_capture"]
            ),
            "repair_source": source,
        }
    )
    capture_evidence = cost_component_capture_evidence_from_packet(packet)
    assessment = assess_cost_components(
        components,
        capture_evidence=capture_evidence,
        measured_commission_r=measured_commission_r,
    )

    original_sum = cost_component_sum(original_components)
    recorded_total_conflict = bool(
        before_total_status not in {"null", "valid"}
        or (
            before_total is not None
            and original_sum is not None
            and not math.isclose(
                before_total,
                original_sum,
                rel_tol=0.0,
                abs_tol=1e-8,
            )
        )
        or (
            before_total is not None
            and original_sum is None
            and isinstance(raw_components, Mapping)
            and legacy_fallback is None
        )
    )
    if recorded_total_conflict and legacy_fallback is None:
        assessment["state"] = "refused"
        assessment["refusal_reasons"] = list(
            dict.fromkeys(
                [
                    *assessment["refusal_reasons"],
                    "inconsistent_component:recorded_total_before_commission_repair",
                ]
            )
        )
    publish_cost_assessment(packet, assessment)

    commission_cost["included_in_total_cost_r"] = assessment["state"] == "complete"
    commission_cost["missing_fields"] = list(assessment["missing_inputs"])

    if assessment["state"] != "complete":
        packet.pop("cost_component_sum_r", None)
        if legacy_fallback is not None:
            components["authority_fallback_total_cost_r"] = legacy_fallback
        packet["commission_r_repair_total_redecode_status"] = (
            "refused_incomplete_component_sum"
            if assessment["state"] == "incomplete"
            else "refused_inconsistent_component_sum"
        )
        packet["commission_r_repair_total_redecode_missing_fields"] = list(
            assessment["missing_inputs"]
        )
        packet.pop("commission_r_repair_total_after_r", None)
    else:
        components.pop("authority_fallback_total_cost_r", None)
        redecoded = float(assessment["candidate_sum_r"])
        packet["total_cost_r"] = redecoded
        packet["cost_component_sum_r"] = redecoded
        packet["commission_r_repair_total_redecode_status"] = (
            "complete_component_sum"
        )
        packet["commission_r_repair_total_redecode_missing_fields"] = []
        packet.setdefault("commission_r_repair_total_before_r", before_total)
        packet["commission_r_repair_total_after_r"] = redecoded
        old_proxy = _packet_number(
            packet.get("old_timewarp_candidate_cost_r_fallback_diagnostic")
        )
        if old_proxy is not None:
            packet["old_proxy_vs_broker_calibrated_delta_r"] = round(
                redecoded - old_proxy, 9
            )
        if legacy_fallback is not None:
            packet["legacy_emitter_fallback_cost_r"] = legacy_fallback
            packet["legacy_emitter_fallback_replaced"] = True

    if regate:
        from src.components.broker_net_cost_engine import (
            pretrade_cost_refusal_reasons,
        )

        if packet.get("status") != "NOT_APPLICABLE":
            packet["status"] = "CHECKED"
        reasons = pretrade_cost_refusal_reasons(packet)
        if assessment["state"] != "complete":
            reasons = list(
                dict.fromkeys(
                    [
                        *reasons,
                        "commission_repair_component_sum_"
                        + assessment["state"],
                    ]
                )
            )
        packet["refusal_reasons"] = reasons
        if packet.get("status") != "NOT_APPLICABLE":
            packet["status"] = "REFUSED" if reasons else "PASSED"
        packet["commission_r_repair_removed_refusal_reasons"] = sorted(
            set(before_reasons) - set(reasons)
        )
    return packet


def _make_commission_patch(*, live: bool, regate: bool = False) -> accel.Patch:
    """`live` charges the measured commission; `regate` also re-runs the COST GATE.

    The two are separate ids because they answer different questions and the
    difference is not cosmetic. `build_pretrade_cost_packet` computes
    `refusal_reasons` and sets `status` PASSED/REFUSED **before** returning
    (`broker_net_cost_engine.py:701-704`), and one of those reasons is
    `total_cost_r_exceeds_limit` against `selected_cell_pretrade_max_total_cost_r`
    (0.15, `agent_config.yaml:716`). A charge added after the packet is built
    therefore reaches the ECONOMICS and not the GATE:

    * `commission_broker_true` -- selection held fixed, the accounting repaired.
      Isolates "what did the missing term cost", which is F38's own question.
    * `commission_broker_true_gated` -- the full repaired-stack semantics: the
      ceiling is a ceiling on TOTAL cost, so a candidate that only passed because
      commission was invisible is refused. Changes which candidates execute.

    Running only the second would confound the accounting effect with a selection
    effect and there would be no way to separate them afterwards.
    """

    name = (
        ("commission_broker_true_gated" if regate else "commission_broker_true")
        if live
        else "commission_inert_control"
    )
    stats = REPAIR_STATS.setdefault(name, _RepairStats())
    saved: dict[str, Any] = {}

    def apply() -> None:
        module = accel._module(TIMEWARP)
        if module is None or not hasattr(module, "broker_calibrated_replay_cost_packet"):
            raise RepairUnavailable(
                f"{name}: {TIMEWARP}.broker_calibrated_replay_cost_packet is not "
                "importable; the repair cannot be installed and refuses rather "
                "than running a silently un-repaired arm"
            )
        original = module.broker_calibrated_replay_cost_packet

        def repaired(**kwargs: Any) -> dict[str, Any]:
            packet = original(**kwargs)
            candidate = kwargs.get("candidate") or {}
            symbol = str(candidate.get("symbol") or "")
            entry = packet.get("entry_price")
            sl = packet.get("sl_distance")
            with _LOCK:
                stats.calls += 1
            # The control computes the SAME quantity through the SAME code and
            # then charges zero. That is what makes it a control rather than an
            # absence: a difference in the live arm cannot be the wrapper.
            value, reason = _PRICER.commission_r(
                symbol=symbol, entry_price=entry, sl_distance=sl
            )
            if value is None:
                with _LOCK:
                    stats.unpriced += 1
                    stats.errors[reason] = stats.errors.get(reason, 0) + 1
                packet["commission_r_repair_status"] = f"unpriced:{reason}"
                return packet
            charge = float(value) if live else 0.0
            with _LOCK:
                if live:
                    stats.applied += 1
                    stats.charged_r_sum += charge
                    stats.charged_r_max = max(stats.charged_r_max, charge)
                    row = stats.per_symbol.setdefault(symbol, {"n": 0, "sum_r": 0.0})
                    row["n"] += 1
                    row["sum_r"] += charge
                else:
                    stats.neutral += 1
            source = (
                TRUSTED_COMMISSION_REPAIR_SOURCE
                if live
                else "inert_control_computed_then_zeroed"
            )
            before = list(packet.get("refusal_reasons") or ())
            if live:
                _apply_broker_true_commission_capture(
                    packet,
                    measured_commission_r=float(value),
                    charge_r=charge,
                    source=source,
                    regate=regate,
                )
            else:
                # Exercise the identical healing code on a detached packet, then
                # disclose what it would have written.  The control must not
                # replace the legacy total or clear a refusal: otherwise it is
                # an economic repair wearing an inert-control label.
                probe = copy.deepcopy(packet)
                _apply_broker_true_commission_capture(
                    probe,
                    measured_commission_r=float(value),
                    charge_r=0.0,
                    source=source,
                    regate=False,
                )
                packet["commission_r_broker_true_measured"] = float(value)
                packet["commission_r_repair_status"] = "control"
                packet["commission_r_control_redecoded_total_r"] = probe.get(
                    "total_cost_r"
                )
                packet["commission_r_control_packet_unchanged"] = True
            if regate and packet.get("refusal_reasons") != before:
                with _LOCK:
                    key = "regate_changed_refusals"
                    stats.errors[key] = stats.errors.get(key, 0) + 1
            return packet

        saved[TIMEWARP] = original
        module.broker_calibrated_replay_cost_packet = repaired

    def revert() -> None:
        for module_name, value in saved.items():
            module = accel._module(module_name)
            if module is not None:
                module.broker_calibrated_replay_cost_packet = value
        saved.clear()

    return accel.Patch(
        patch_id=name,
        summary=(
            "charge broker-true round-turn commission into the replay's cost "
            "packet (F38: the replay hardcodes commission_r = 0.0 and satisfies "
            "its own commission requirement with a status string)"
            if live
            else "INERT CONTROL for commission_broker_true: identical wrapper, "
            "identical per-candidate computation, charge forced to 0.0"
        ),
        identity_argument=(
            "Changes an ECONOMIC quantity on purpose -- it is a repair, not a "
            "cut, and it is expected to move outcomes. The charge is AW's exact "
            "call chain (src/costs/model.py commission_usd_per_lot / "
            "_usd_per_price_unit_per_lot over BROKER_TRUE_COSTS_V1), so the "
            "regenerated pool is charged with the same number AW charged the "
            "sealed pool with. An instrument the layer cannot price is COUNTED "
            "and left uncharged rather than defaulted to zero silently -- "
            "defaulting to a plausible number with no basis is what F38 was."
            if live
            else "Proves the wrapper itself is inert. Same rebind, same symbol, "
            "same per-candidate commission computation, then zero. If an arm "
            "with this installed is OUTCOME_IDENTICAL to an arm with no repair, "
            "every difference the live repair produces is the NUMBER."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


# ---------------------------------------------------------------------------
# repair 2 -- the swap horizon (the AQ hook, in the one place it bites here)
# ---------------------------------------------------------------------------
#
# `attempt5:10276-10278` sets
# `broad_live_as_if_replay_pretrade_swap_cost_time_stop_bars = 32` and
# `selected_cell_swap_cost_minutes_per_bar = 15`, so the swap model prices
# `holding_days = 32 * 15 / 1440 = 0.3333` -- eight hours
# (`broker_net_cost_engine.py:372-382`). The replay's expiry is
# `min(asof + 120 min, decision_day 00:00Z + 1 day)`, so **no B7.5 position can
# be held longer than two hours** and most are held far less.
#
# The replay therefore charges a 4x-too-long carry on every candidate. This is
# the same CLASS of defect AQ repaired live -- a horizon constant that does not
# describe the contract the engine runs -- pointing the opposite way: AQ's live
# stop was 80x too SHORT, this one is 4x too LONG.
#
# The rebind is on `build_pretrade_cost_packet` as the timewarp module sees it,
# because `trade_params` is assembled inside
# `broker_calibrated_replay_cost_packet` and handed straight to it.


def _make_swap_horizon_patch(*, live: bool) -> accel.Patch:
    name = "swap_horizon_true" if live else "swap_horizon_inert_control"
    stats = REPAIR_STATS.setdefault(name, _RepairStats())
    saved: dict[str, Any] = {}

    def apply() -> None:
        module = accel._module(TIMEWARP)
        if module is None or not hasattr(module, "build_pretrade_cost_packet"):
            raise RepairUnavailable(
                f"{name}: {TIMEWARP}.build_pretrade_cost_packet is not importable"
            )
        original = module.build_pretrade_cost_packet

        def repaired(**kwargs: Any) -> dict[str, Any]:
            params = kwargs.get("trade_params")
            with _LOCK:
                stats.calls += 1
            if isinstance(params, dict):
                current = params.get("gtos_vnext_dynamic_time_stop_bars")
                target = TRUE_SWAP_HORIZON_BARS if live else current
                # The control re-writes the SAME key with the SAME value, so it
                # exercises the mutation path without moving the number.
                params["gtos_vnext_dynamic_time_stop_bars"] = target
                with _LOCK:
                    if live:
                        stats.applied += 1
                    else:
                        stats.neutral += 1
            packet = original(**kwargs)
            packet["swap_horizon_repair_status"] = "applied" if live else "control"
            packet["swap_horizon_bars_used"] = (
                TRUE_SWAP_HORIZON_BARS if live else SEALED_SWAP_HORIZON_BARS
            )
            return packet

        saved[TIMEWARP] = original
        module.build_pretrade_cost_packet = repaired

    def revert() -> None:
        for module_name, value in saved.items():
            module = accel._module(module_name)
            if module is not None:
                module.build_pretrade_cost_packet = value
        saved.clear()

    return accel.Patch(
        patch_id=name,
        summary=(
            "price swap over the horizon the replay can actually reach "
            f"({TRUE_SWAP_HORIZON_BARS:.0f} bars = {REPLAY_MAX_HOLD_MINUTES:.0f} "
            f"min) instead of the sealed {SEALED_SWAP_HORIZON_BARS:.0f} bars "
            "(8 h), which no B7.5 position can survive to"
            if live
            else "INERT CONTROL for swap_horizon_true: identical wrapper, "
            "rewrites the same key with the value it already had"
        ),
        identity_argument=(
            "An economic repair, expected to move outcomes -- downward in cost. "
            "The 120-minute ceiling is not a typical hold, it is the expiry the "
            "engine enforces (REPAIRED_PENDING_EXPIRY_MINUTES, attempt5:116, "
            "applied :16164/:16745; expiry min(asof+120min, day+1d) at "
            "v4_timewarp:85864-85866), and the same bound clamps the terminal "
            "path query, so a position that is not closed by then is marked to "
            "market. Charging 8 hours of carry against it is a modelling error "
            "with a measurable sign."
            if live
            else "Proves the wrapper is inert: it writes the key back with its "
            "existing value, so an OUTCOME_IDENTICAL control arm attributes any "
            "live difference to the horizon number."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


# ---------------------------------------------------------------------------
# CD-5's dial -- the cost ceiling, which is a SEARCH axis rather than a repair
# ---------------------------------------------------------------------------
#
# `selected_cell_pretrade_max_total_cost_r` is 0.15 (`agent_config.yaml:716`) and
# it is enforced (`pretrade_cost_refusal_reasons:772-776`). Once commission is
# counted the ceiling binds differently -- a candidate that only passed because
# 0.065 R of commission was invisible is now refused -- so "is 0.15 still the
# right ceiling" becomes a live question that the sealed campaign could not ask.
#
# This is a DIAL, not a repair: there is no true value it is being corrected to.
# It rides the repair mechanism because the machinery is identical (wrap, mutate,
# re-run the engine's own gate) and because putting it behind `--repairs` means
# every sweep cell names itself in the receipt and in the iteration-ledger spec.
#
# The per-sleeve override path is dead on this path and it is worth knowing why:
# `_resolve_max_with_sleeve_override` keys on
# `trade_params["gtos_vnext_source_event_details"]["sleeve"]`, and the replay's
# trade_params (`v4_timewarp:58888-58905`) carry no such key -- so the global
# limit is the only one reachable in replay, and a sleeve-scoped sweep would be
# measuring nothing.

#: ceiling in R -> patch id suffix. Declared, not computed from a flag, so a
#: sweep cell cannot be invented at the command line without appearing here.
COST_CEILING_CELLS: tuple[float, ...] = (0.05, 0.10, 0.25, 0.50, 1.00)
SEALED_TOTAL_COST_CEILING_R = 0.15


def _ceiling_id(value: float) -> str:
    return "cost_ceiling_" + f"{value:.2f}".replace(".", "p")


def _make_cost_ceiling_patch(ceiling: float) -> accel.Patch:
    name = _ceiling_id(ceiling)
    stats = REPAIR_STATS.setdefault(name, _RepairStats())
    saved: dict[str, Any] = {}

    def apply() -> None:
        module = accel._module(TIMEWARP)
        if module is None or not hasattr(module, "broker_calibrated_replay_cost_packet"):
            raise RepairUnavailable(f"{name}: cost packet builder not importable")
        original = module.broker_calibrated_replay_cost_packet

        def dialled(**kwargs: Any) -> dict[str, Any]:
            packet = original(**kwargs)
            from src.components.broker_net_cost_engine import (
                pretrade_cost_refusal_reasons,
            )

            with _LOCK:
                stats.calls += 1
            before = str(packet.get("status"))
            packet["max_total_cost_r"] = ceiling
            packet["cost_ceiling_dial_r"] = ceiling
            reasons = pretrade_cost_refusal_reasons(packet)
            packet["refusal_reasons"] = reasons
            if packet.get("status") != "NOT_APPLICABLE":
                packet["status"] = "REFUSED" if reasons else "PASSED"
            with _LOCK:
                stats.applied += 1
                if str(packet.get("status")) != before:
                    key = f"status_{before}_to_{packet.get('status')}"
                    stats.errors[key] = stats.errors.get(key, 0) + 1
            return packet

        saved[TIMEWARP] = original
        module.broker_calibrated_replay_cost_packet = dialled

    def revert() -> None:
        for module_name, value in saved.items():
            module = accel._module(module_name)
            if module is not None:
                module.broker_calibrated_replay_cost_packet = value
        saved.clear()

    return accel.Patch(
        patch_id=name,
        summary=(
            f"set the total-cost ceiling to {ceiling:.2f} R (sealed: "
            f"{SEALED_TOTAL_COST_CEILING_R}) and re-run the engine's own refusal "
            "check -- a SEARCH dial, not a repair"
        ),
        identity_argument=(
            "Deliberately changes admission. There is no correct value being "
            "restored, so this is not a repair and is never run as one: it is a "
            "gradient axis for CD-5, declared cell by cell so a sweep cannot be "
            "invented at the command line. The re-gate is the engine's own "
            "`pretrade_cost_refusal_reasons`, not a reimplementation. Compose it "
            "with `commission_broker_true` (not the `_gated` variant) so exactly "
            "one wrapper owns the packet builder."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


# ---------------------------------------------------------------------------
# FA-2's dial -- the neutral-selection seed replicate, a REPLICATE axis
# ---------------------------------------------------------------------------
#
# The S0 arms select by outcome-blind hash rank:
# `b7_5_selection_sizing_factorial_neutral_rank_sha256(seed, decision_window_id,
# candidate_instance_key)` (`v4_timewarp:36459`, consumed at `:52243-52249`) and
# the selection sorts on `(neutral_rank_sha256, candidate_instance_key)`
# (`:52320-52324`, `:52349`). The whole executed book of an S0 arm -- its family
# mix, its instrument mix, and therefore its cost bill -- is downstream of ONE
# seed. Whether those mixes are properties of the pool or artifacts of the
# sealed seed is unmeasured, and the March MDE needs the seed-noise band.
#
# This dial runs the SAME arm under a replicate seed. Everything else is the
# sealed machinery, untouched:
#
# * The seed originates in the decision contract
#   (`attempt5:1145-1147` inside `selection_sizing_factorial_binding_from_args`,
#   def `:891`). The contract JSON is NEVER edited; the dial wraps the
#   constructor and rebinds the seed on its RETURN value, rebuilding
#   `binding_payload` + `binding_payload_sha256` through the engine's own
#   `selection_sizing_core_binding_payload`, so every runtime stamp
#   (`attempt5:11886`), ledger field (`:12104`) and harness record declares the
#   variant seed. No output can claim the sealed seed while ranks use another.
# * The loop re-verifies the runtime seed against its module constant
#   `B7_5_SELECTION_SIZING_FACTORIAL_SEALED_NEUTRAL_SEED_SHA256`
#   (`v4_timewarp:35949-35951`, checked at `:36276-36279` -- a bare
#   module-global read at call time, so it is rebindable) and recomputes the
#   binding payload from runtime values (`:36399-36404`). The dial rebinds the
#   constant to the SAME variant seed, so the binding stays VALID and the mode
#   stays `neutral_hash_hard_eligible` -- an invalid binding would silently
#   change the arm's selection semantics, which is exactly the failure the
#   fail-closed check exists to prevent.
# * Pack identity is seed-INSENSITIVE by construction:
#   `factor_neutral_config_root` strips every `b7_5_selection_sizing_factorial_*`
#   runtime key and the harness binding record
#   (`replay_prepared_day_pack.py:592-619`), so replicate arms run against the
#   existing lane packs.
#
# Like the cost ceiling, this rides the repair mechanism so every run names its
# seed in the receipt and the iteration-ledger spec. Unlike a repair it has no
# inert-control twin: the control is folded into every call -- the wrapper first
# reproduces the original payload byte-for-byte with the SEALED seed and refuses
# if it cannot, which proves the rebuild plumbing before the variant is applied.

#: The sealed protocol seed, pinned here so the dial can refuse to replicate an
#: unknown baseline (if the contract's seed ever differs, the derivation below
#: would describe a relationship that does not hold).
SEALED_NEUTRAL_SELECTION_SEED_SHA256 = (
    "0c6b87233ad895d981b6ace153e1c355862dde7989e66abd4ca99c93b4edaf3a"
)
#: Replicate indices -> patch id suffix. Declared, not computed from a flag, so
#: a replicate cell cannot be invented at the command line without appearing
#: here (the cost-ceiling rule).
NEUTRAL_SEED_REPLICATE_CELLS: tuple[int, ...] = (1, 2)
NEUTRAL_SEED_REPLICATE_DERIVATION = (
    "sha256(utf8('gtos.train_engine.neutral_seed_replicate:{n}|"
    "' + sealed_seed_hex))"
)
#: The attribute the timewarp loop checks the runtime seed against.
TIMEWARP_SEALED_SEED_ATTR = (
    "B7_5_SELECTION_SIZING_FACTORIAL_SEALED_NEUTRAL_SEED_SHA256"
)


def neutral_seed_replicate_seed(n: int) -> str:
    """Deterministic replicate seed: r1 cdeae5d8..., r2 709126af...."""

    if n not in NEUTRAL_SEED_REPLICATE_CELLS:
        raise RepairUnavailable(f"neutral_seed_replicate_cell_undeclared:{n}")
    return hashlib.sha256(
        (
            f"gtos.train_engine.neutral_seed_replicate:{n}|"
            f"{SEALED_NEUTRAL_SELECTION_SEED_SHA256}"
        ).encode("utf-8")
    ).hexdigest()


def _replicate_id(n: int) -> str:
    return f"neutral_seed_replicate_r{n}"


def _make_neutral_seed_replicate_patch(n: int) -> accel.Patch:
    name = _replicate_id(n)
    variant_seed = neutral_seed_replicate_seed(n)
    stats = REPAIR_STATS.setdefault(name, _RepairStats())
    saved: dict[str, Any] = {}

    def apply() -> None:
        timewarp = accel._module(TIMEWARP)
        runner = accel._module(ATTEMPT5)
        if timewarp is None or not hasattr(timewarp, TIMEWARP_SEALED_SEED_ATTR):
            raise RepairUnavailable(
                f"{name}: {TIMEWARP}.{TIMEWARP_SEALED_SEED_ATTR} is not "
                "importable; the dial cannot be installed and refuses rather "
                "than running an arm whose ranks and checks could disagree"
            )
        missing = [
            symbol
            for symbol in (
                "selection_sizing_factorial_binding_from_args",
                "selection_sizing_core_binding_payload",
                "stable_sha256",
            )
            if not hasattr(runner, symbol)
        ] if runner is not None else ["<module not imported>"]
        if missing:
            raise RepairUnavailable(
                f"{name}: {ATTEMPT5} is missing {missing}; refusing"
            )
        current = getattr(timewarp, TIMEWARP_SEALED_SEED_ATTR)
        if current != SEALED_NEUTRAL_SELECTION_SEED_SHA256:
            raise RepairUnavailable(
                f"{name}: the loop's sealed-seed constant already reads "
                f"{current!r}, not the sealed protocol seed -- another seed "
                "dial is installed. Two seed dials can never compose: the arm "
                "would rank under one seed while declaring another, and no "
                "receipt could name its selection semantics."
            )
        original = runner.selection_sizing_factorial_binding_from_args

        def replicated(args: Any) -> "dict[str, Any] | None":
            binding = original(args)
            with _LOCK:
                stats.calls += 1
            if binding is None:
                # Factorial arm not requested; nothing to replicate.
                with _LOCK:
                    stats.neutral += 1
                return None
            if not isinstance(binding, dict) or binding.get("valid") is not True:
                raise RepairUnavailable(
                    f"{name}: the binding constructor returned a shape this "
                    "dial cannot rebind; refusing rather than running with an "
                    "ambiguous seed"
                )
            contract_seed = binding.get("neutral_selection_seed_sha256")
            if contract_seed != SEALED_NEUTRAL_SELECTION_SEED_SHA256:
                raise RepairUnavailable(
                    f"{name}: the decision contract carries neutral seed "
                    f"{contract_seed!r}, not the sealed protocol seed this "
                    "dial's derivation is declared against; refusing to "
                    "replicate an unknown baseline"
                )

            def payload_with(seed: str) -> dict[str, Any]:
                return runner.selection_sizing_core_binding_payload(
                    decision_contract_sha256=binding[
                        "decision_contract_sha256"
                    ],
                    common_execution_input_digest_sha256=binding[
                        "common_execution_input_digest_sha256"
                    ],
                    arm_id=binding["arm_id"],
                    arm_fingerprint_sha256=binding["arm_fingerprint_sha256"],
                    selection_factor=binding["selection_factor"],
                    sizing_factor=binding["sizing_factor"],
                    selection_mode=binding["selection_mode"],
                    sizing_mode=binding["sizing_mode"],
                    neutral_selection_seed_sha256=seed,
                    protocol_economics=binding["protocol_economics"],
                    protocol_economics_digest_sha256=binding[
                        "protocol_economics_digest_sha256"
                    ],
                )

            # The folded-in control: reproduce the ORIGINAL payload exactly
            # with the sealed seed before touching anything. If this fails the
            # kwarg reconstruction no longer matches the constructor's own call
            # (an API drift), and a variant payload built from it would be
            # fabricated provenance.
            if payload_with(contract_seed) != binding["binding_payload"]:
                with _LOCK:
                    key = "payload_reconstruction_drift"
                    stats.errors[key] = stats.errors.get(key, 0) + 1
                raise RepairUnavailable(
                    f"{name}: reconstructing the binding payload with the "
                    "sealed seed does not reproduce the constructor's own "
                    "payload; the engine's binding API has drifted and the "
                    "dial refuses rather than emit a payload it cannot prove "
                    "faithful"
                )
            rebound = dict(binding)
            rebound["neutral_selection_seed_sha256"] = variant_seed
            rebound["binding_payload"] = payload_with(variant_seed)
            rebound["binding_payload_sha256"] = runner.stable_sha256(
                rebound["binding_payload"]
            )
            # Declared provenance: this block rides the binding into the run
            # config's harness record, so the arm's own outputs name the dial,
            # both seeds, and the derivation that links them.
            rebound["neutral_selection_seed_replicate"] = {
                "dial": name,
                "replicate_index": n,
                "sealed_protocol_seed_sha256": (
                    SEALED_NEUTRAL_SELECTION_SEED_SHA256
                ),
                "variant_seed_sha256": variant_seed,
                "derivation": NEUTRAL_SEED_REPLICATE_DERIVATION,
            }
            with _LOCK:
                stats.applied += 1
            return rebound

        saved["sealed_constant"] = current
        saved["constructor"] = original
        setattr(timewarp, TIMEWARP_SEALED_SEED_ATTR, variant_seed)
        runner.selection_sizing_factorial_binding_from_args = replicated

    def revert() -> None:
        timewarp = accel._module(TIMEWARP)
        runner = accel._module(ATTEMPT5)
        if "sealed_constant" in saved and timewarp is not None:
            setattr(
                timewarp, TIMEWARP_SEALED_SEED_ATTR, saved["sealed_constant"]
            )
        if "constructor" in saved and runner is not None:
            runner.selection_sizing_factorial_binding_from_args = saved[
                "constructor"
            ]
        saved.clear()

    return accel.Patch(
        patch_id=name,
        summary=(
            f"run the S0 neutral arm under replicate seed r{n} "
            f"({variant_seed[:12]}...) instead of the sealed protocol seed -- "
            "a REPLICATE dial, not a repair: it deliberately changes the "
            "neutral arm's tiebreak ordering to measure whether the executed "
            "book's family mix and cost bill are seed artifacts"
        ),
        identity_argument=(
            "Deliberately changes the neutral arm's hash-rank ordering. No "
            "correct value is being restored, so this is not a repair and is "
            "never run as one: it is a replicate axis for the seed-noise band "
            "the March MDE needs, declared cell by cell so a variant seed "
            "cannot be invented at the command line. The variant is derived, "
            f"not typed: {NEUTRAL_SEED_REPLICATE_DERIVATION} with n={n} over "
            "the sealed seed, and the dial refuses at apply time if the "
            "loop's sealed-check constant is already rebound (two seed dials "
            "never compose) and at call time if the contract's seed is not "
            "the sealed one. Both rebind sides carry the SAME variant -- the "
            "runner-derived binding and the loop's sealed-check constant -- "
            "so the factorial binding stays VALID, selection stays "
            "`neutral_hash_hard_eligible`, and every binding payload, runtime "
            "stamp, ledger row and harness record declares the variant seed. "
            "Outcome differences against the sealed-seed arm are the "
            "measurement, not a defect. Composes freely with "
            "`commission_broker_true_gated` and `swap_horizon_true` (disjoint "
            "symbols: this dial owns the binding constructor and the sealed "
            "constant; the repairs own the cost-packet builders)."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


# ---------------------------------------------------------------------------
# repair 3 -- spread input truth (FA Phase C R-COST-TRUTH part (a); B5 C3, REFUTED both lenses)
# ---------------------------------------------------------------------------
#
# B5's adversarial pass (`phase19/receipts/forensic/B5_ADVERSARIAL_VERDICTS.md` §C3,
# both C3 entries in `b5_verdicts.json`) found that 17 of 24 symbols carry a
# per-row CONSTANT spread in both monthly pools -- SPX500 = 10.0 price units on
# all 1,943 rows (16.7x the broker-measured 0.6 anchor and 10x the worst tick
# ever captured), NAS100 = 50.0 on all 1,622 (28.6x the measured 1.75) -- because
# the replay quote synthesis falls through to the broker-profile symbol-spec
# `spread` (points) whenever the sealed replay has no tick source for the symbol
# (`v4_timewarp._predecision_tick_for_cost:58806-58820`,
# quote_source="broker_profile_symbol_spec_spread"). Three more symbols ride the
# admission floor table (BTCUSD 0.0001 / UKOIL_cash 0.0258 / USOIL_cash 0.0270 R,
# `admission.py:73-84`, branch `:58795-58802`). Only EURUSD/USDJPY/XAUUSD/XAGUSD
# -- the lane's four registered tick sources -- carry a real measured spread
# (branch `:58760-58794`).
#
# THE INTERCEPTION POINT is `_predecision_tick_for_cost` itself, rebound as a
# TIMEWARP module attribute. Chosen over packet-level surgery because it is the
# one place that (a) sees the candidate (symbol, entry, stop) AND the decision
# time, (b) RETURNS the quote_source that names which of the five branches
# fired, so the disposition can be branch-exact rather than symbol-guessed, and
# (c) sits UPSTREAM of `build_pretrade_cost_packet`, so the engine's own
# `_tick_packet` arithmetic (`spread_price = ask - bid`,
# `spread_r = spread_price / sl_distance`), its component vector, its
# `total_cost_r` sum and its `pretrade_cost_refusal_reasons` gate all consume
# the truthed quote with ZERO downstream edits. Its single call site
# (`v4_timewarp:58868`) resolves the name through module globals at call time,
# and `CampaignExactCache` caches config/timeframe state only -- never this
# function's result -- so the rebind cannot be bypassed.
#
# Branch dispositions, by the frozen quote_source:
#
# | frozen quote_source                                   | disposition |
# |---|---|
# | `broker_profile_symbol_spec_spread`                   | REPLACED with the model price (the 17-symbol constant class) |
# | `ultimate_book_measured_tick_spread_floor`            | REPLACED (the 3-symbol floor-table class; a round-trip R constant, not a decision-time quote) |
# | `broker_profile_max_spread_cents_ceiling`             | REPLACED (same config-constant class, different config key; 0 rows in either pool but the defect shape is identical) |
# | `historical_ftmo_predecision_tick` + floor-substitute | REPLACED (a crossed/zero-width tick made the tick branch fall back to the floor TABLE -- a floor use wearing a tick label) |
# | `historical_ftmo_predecision_tick` (genuine)          | UNTOUCHED -- a real last-tick quote is more honest than any model |
# | `conservative_default_spread_r_no_tick_or_symbol_spec`| UNTOUCHED -- the engine already treats this class as a SOURCE GAP and refuses it without a profile opt-in (`v4_timewarp:58974-58979`); replacing it would silently delete a fail-closed refusal. Counted. |
#
# The truth source is `src/costs/spread_model.py::spread_price(symbol, "FTMO",
# at_utc, band="mid")` over the committed fitted artifact
# `research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json` -- tick-
# measured anchors (SPX500 0.6 over 783,729 ticks), H4-bar era ratios, and the
# damped hour-of-week x vol intraweek shaping. Era note, stated because it is a
# disclosed limit and not a footnote: the anchors are measured on the Jun-Jul
# 2026 tick capture and the lane's windows are Jan/Feb 2026 -- WITHIN-ERA per
# B5 (the model's own 2026Q1 era ratios are RECORDED for the flagship symbols,
# and the 17-30x overstatement of the constants exceeds any plausible
# spread-regime shift inside the year).
#
# EXPECTED EFFECT (economic on purpose; ex-ante from B5's two independent
# refuters, numerator-only, stops untouched, pool's own caps): January pool mean
# spread_r 0.564 -> ~0.157 (3.6x inflated), untradeable 73.9% -> ~61% at
# mean-truth (Feb 82.2% -> ~60%); SPX500 48-54% of its kills un-killed, NAS100
# ~74%. A genuine geometry-killed core REMAINS (~41.6% Jan / 31.8% Feb still
# spread-killed at broker-true p50) -- this repair does not and must not claim
# to clear it.

#: The fitted spread-truth artifact and the call contract this repair prices with.
SPREAD_MODEL_V1 = (
    REPO_ROOT / "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"
)
SPREAD_ACCOUNT = "FTMO"
SPREAD_BAND = "mid"
#: The quote_source the repaired quote self-describes with.
REPAIRED_SPREAD_QUOTE_SOURCE = "spread_model_v1_hour_aware"
#: Frozen quote classes this repair replaces / must never touch (see table above).
SPREAD_REPLACED_QUOTE_SOURCES = (
    "broker_profile_symbol_spec_spread",
    "ultimate_book_measured_tick_spread_floor",
    "broker_profile_max_spread_cents_ceiling",
)
SPREAD_KEPT_QUOTE_SOURCES = (
    "historical_ftmo_predecision_tick",
    "conservative_default_spread_r_no_tick_or_symbol_spec",
)
#: The module whose `_ALLOWED_COMPONENT_SOURCES` authority table must recognise
#: the repaired quote source while the repair is installed (rebound at apply,
#: restored at revert -- the file is never edited).
DECISION_SEMANTICS = "src.research_infra.train_engine.decision_semantics"


class _SpreadTruthPricer:
    """The spread model, loaded once and priced per decision instant."""

    def __init__(self) -> None:
        self._model: Any = None

    def load(self) -> Any:
        if self._model is None:
            from src.costs.spread_model import load_spread_model

            self._model = load_spread_model(SPREAD_MODEL_V1)
        return self._model

    def estimate(self, symbol: str, at_utc: Any) -> tuple[Any, str]:
        """`(SpreadEstimate, "spread_model")` or `(None, reason)`. Never guesses."""

        from src.costs.spread_model import SpreadModelError

        try:
            return (
                self.load().estimate(
                    symbol, SPREAD_ACCOUNT, at_utc, band=SPREAD_BAND
                ),
                "spread_model",
            )
        except SpreadModelError as exc:
            return None, f"unpriced_symbol_or_era:{str(exc)[:60]}"
        except (KeyError, TypeError, ValueError) as exc:
            return None, f"spread_model_error:{type(exc).__name__}"


_SPREAD_PRICER = _SpreadTruthPricer()


def _optional_float(value: Any) -> float | None:
    try:
        if value is None or isinstance(value, bool):
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _make_spread_truth_patch(*, live: bool) -> accel.Patch:
    name = "spread_input_truth" if live else "spread_input_truth_inert_control"
    stats = REPAIR_STATS.setdefault(name, _RepairStats())
    saved: dict[str, Any] = {}

    def apply() -> None:
        module = accel._module(TIMEWARP)
        required = (
            "_predecision_tick_for_cost",
            "_broker_cost_tick_from_spread_r",
            "parse_utc",
        )
        missing = (
            [symbol for symbol in required if not hasattr(module, symbol)]
            if module is not None
            else list(required)
        )
        if missing:
            raise RepairUnavailable(
                f"{name}: {TIMEWARP} is missing {missing}; the repair cannot be "
                "installed and refuses rather than running a silently "
                "un-repaired arm"
            )
        semantics = accel._module(DECISION_SEMANTICS)
        if semantics is None or not hasattr(semantics, "_ALLOWED_COMPONENT_SOURCES"):
            raise RepairUnavailable(
                f"{name}: {DECISION_SEMANTICS}._ALLOWED_COMPONENT_SOURCES is not "
                "reachable, so the repaired quote source could not be recognised "
                "by the component-authority assessment; refusing"
            )
        original = module._predecision_tick_for_cost
        if getattr(original, "_gtos_spread_input_truth_wrapper", False):
            raise RepairUnavailable(
                f"{name}: a spread-input wrapper is already installed on "
                f"{TIMEWARP}._predecision_tick_for_cost. The live repair and "
                "its inert control can never compose: the pool could not say "
                "which spread it was charged."
            )
        try:
            _SPREAD_PRICER.load()
        except Exception as exc:  # noqa: BLE001 -- refusal must name any load failure
            raise RepairUnavailable(
                f"{name}: the spread model at {SPREAD_MODEL_V1} did not load "
                f"({type(exc).__name__}: {str(exc)[:120]}); refusing rather "
                "than running with 100% unpriced substitutions"
            ) from exc

        def truthed(**kwargs: Any) -> tuple[Any, Any]:
            tick, metadata = original(**kwargs)
            with _LOCK:
                stats.calls += 1
            meta = metadata if isinstance(metadata, Mapping) else {}
            quote_source = str(meta.get("quote_source") or "")
            floor_substituted = bool(
                meta.get("measured_tick_spread_floor_used_as_quote_substitute")
            )
            if quote_source in SPREAD_REPLACED_QUOTE_SOURCES:
                replaced_class = quote_source
            elif (
                quote_source == "historical_ftmo_predecision_tick"
                and floor_substituted
            ):
                replaced_class = "historical_tick_floor_substitute"
            else:
                # Genuine tick, the fail-closed conservative-default class, or
                # an unknown future branch: all UNTOUCHED, all counted.
                with _LOCK:
                    key = f"kept:{quote_source or 'no_quote_source'}"
                    stats.errors[key] = stats.errors.get(key, 0) + 1
                return tick, metadata

            def unpriced(reason: str) -> tuple[Any, Any]:
                with _LOCK:
                    stats.unpriced += 1
                    stats.errors[reason] = stats.errors.get(reason, 0) + 1
                return tick, metadata

            candidate = kwargs.get("candidate") or {}
            symbol = str(candidate.get("symbol") or "")
            entry = _optional_float(candidate.get("entry_price"))
            stop = _optional_float(candidate.get("stop_loss"))
            risk = abs(entry - stop) if entry is not None and stop is not None else 0.0
            if risk <= 0:
                return unpriced("no_stop_distance")
            asof = module.parse_utc(kwargs.get("asof_utc"))
            if asof is None:
                return unpriced("unparseable_asof_utc")
            estimate, reason = _SPREAD_PRICER.estimate(symbol, asof)
            if estimate is None:
                return unpriced(reason)
            model_spread_price = _optional_float(estimate.spread_price)
            if model_spread_price is None or model_spread_price <= 0:
                return unpriced("non_positive_model_spread_price")
            model_spread_r = model_spread_price / risk
            frozen_spread_r = _optional_float(
                meta.get("synthetic_quote_spread_r")
                if meta.get("synthetic_quote_spread_r") is not None
                else meta.get("historical_tick_spread_r")
            )
            with _LOCK:
                if live:
                    stats.applied += 1
                else:
                    stats.neutral += 1
                # Both arms account identically -- that is what makes the
                # control's report comparable to the live one: same calls,
                # same per-symbol pricing, different EMISSION only.
                stats.charged_r_sum += model_spread_r
                stats.charged_r_max = max(stats.charged_r_max, model_spread_r)
                if frozen_spread_r is not None:
                    stats.baseline_r_sum += frozen_spread_r
                row = stats.per_symbol.setdefault(
                    symbol, {"n": 0, "sum_r": 0.0, "baseline_sum_r": 0.0}
                )
                row["n"] += 1
                row["sum_r"] += model_spread_r
                row["baseline_sum_r"] = row.get("baseline_sum_r", 0.0) + (
                    frozen_spread_r or 0.0
                )
                key = f"replaced:{replaced_class}"
                stats.errors[key] = stats.errors.get(key, 0) + 1
                if not estimate.decidable:
                    key = f"decidable_false:{symbol}"
                    stats.errors[key] = stats.errors.get(key, 0) + 1
            if not live:
                # INERT CONTROL: identical wrapper, identical per-row model
                # computation, then the ORIGINAL (frozen) quote byte-for-byte.
                return tick, metadata
            detail = estimate.detail if isinstance(estimate.detail, Mapping) else {}
            new_tick, new_metadata = module._broker_cost_tick_from_spread_r(
                candidate=candidate,
                asof_utc=str(kwargs.get("asof_utc") or ""),
                spread_r=model_spread_r,
                quote_source=REPAIRED_SPREAD_QUOTE_SOURCE,
                extra={
                    "pre_repair_quote_source": quote_source,
                    "pre_repair_quote_class": replaced_class,
                    "pre_repair_spread_r": frozen_spread_r,
                    "spread_input_truth_delta_r": (
                        round(model_spread_r - frozen_spread_r, 9)
                        if frozen_spread_r is not None
                        else None
                    ),
                    "spread_model_artifact": SPREAD_MODEL_V1.name,
                    "spread_model_version": detail.get("model_version"),
                    "spread_model_account": SPREAD_ACCOUNT,
                    "spread_model_band": SPREAD_BAND,
                    "spread_model_composition": estimate.composition,
                    "spread_model_era": estimate.era,
                    "spread_model_era_class": estimate.era_class,
                    "spread_model_era_ratio": estimate.era_ratio,
                    "spread_model_era_note": (
                        "anchors measured Jun-Jul 2026; applied within-era per "
                        "B5 C3 (era ratios RECORDED at the lane windows)"
                    ),
                    "spread_model_coverage": estimate.coverage.value,
                    "spread_model_decidable": estimate.decidable,
                    "spread_model_anchor_price": estimate.anchor_price,
                    "spread_model_intraweek_mult": estimate.intraweek_mult,
                    "spread_model_spread_price": model_spread_price,
                    "spread_model_provenance": estimate.provenance,
                },
            )
            # The frozen branch's own provenance keys (broker_profile_*,
            # measured_tick_spread_floor_*, path_index_*) survive underneath;
            # the new synthesis overrides quote_source and the synthetic_* pair.
            merged = dict(meta)
            merged.update(new_metadata)
            return new_tick, merged

        truthed._gtos_spread_input_truth_wrapper = True  # type: ignore[attr-defined]
        saved[TIMEWARP] = original
        if live:
            allowed = semantics._ALLOWED_COMPONENT_SOURCES
            saved["allowed_component_sources"] = allowed
            semantics._ALLOWED_COMPONENT_SOURCES = {
                **allowed,
                "spread_r": frozenset(allowed["spread_r"])
                | {REPAIRED_SPREAD_QUOTE_SOURCE},
            }
        module._predecision_tick_for_cost = truthed

    def revert() -> None:
        module = accel._module(TIMEWARP)
        if TIMEWARP in saved and module is not None:
            module._predecision_tick_for_cost = saved[TIMEWARP]
        semantics = accel._module(DECISION_SEMANTICS)
        if "allowed_component_sources" in saved and semantics is not None:
            semantics._ALLOWED_COMPONENT_SOURCES = saved[
                "allowed_component_sources"
            ]
        saved.clear()

    return accel.Patch(
        patch_id=name,
        summary=(
            "price the replay's placeholder spread classes from the fitted "
            "broker-truth spread model (B5 C3: 17/24 symbols carry a per-row "
            "config-constant spread -- SPX500 10.0 = 16.7x tick truth, NAS100 "
            "50.0 = 28.6x -- and 3 more ride the admission floor table); "
            "genuine predecision ticks stay untouched. Ex-ante: Jan pool mean "
            "spread_r 0.564 -> ~0.157, untradeable 73.9% -> ~61% at mean-truth"
            if live
            else "INERT CONTROL for spread_input_truth: identical wrapper on "
            "the same symbol, identical per-row spread-model computation and "
            "accounting, then the ORIGINAL (frozen) quote emitted byte-for-byte"
        ),
        identity_argument=(
            "Changes an ECONOMIC quantity on purpose -- a repair, expected to "
            "move outcomes DOWNWARD in cost on 20 of 24 symbols. The "
            "interception point is TIMEWARP._predecision_tick_for_cost "
            "(single call site v4_timewarp:58868, resolved through module "
            "globals; CampaignExactCache caches config/timeframe state only, "
            "so no cached path bypasses it), chosen because it sees symbol + "
            "decision time, returns the branch-naming quote_source, and sits "
            "upstream of build_pretrade_cost_packet so the engine's own "
            "spread arithmetic and cost gate consume the truthed quote with "
            "no packet surgery. Replaces ONLY the placeholder classes "
            "(symbol-spec constant, floor table, max_spread_cents ceiling, "
            "and the floor-substitute inside the tick branch); genuine ticks "
            "and the fail-closed conservative-default refusal class pass "
            "through untouched and counted. A symbol/instant the model cannot "
            "price keeps the FROZEN behavior and is COUNTED as unpriced -- "
            "defaulting to a plausible number with no basis is what the "
            "constant was. While installed, decision_semantics."
            "_ALLOWED_COMPONENT_SOURCES['spread_r'] is extended at runtime "
            "with the repaired quote source (restored at revert; the file is "
            "never edited) so the component-authority assessment recognises "
            "the new producer exactly as it recognises the trusted commission "
            "repair source. Composes with commission_broker_true[_gated], "
            "swap_horizon_true, cost_ruler_harmonize, cost_ceiling_* and "
            "neutral_seed_replicate_* -- disjoint rebind targets, verified by "
            "reading: this repair owns _predecision_tick_for_cost; the "
            "commission/ceiling/ruler wrappers own "
            "broker_calibrated_replay_cost_packet; the swap repair owns "
            "build_pretrade_cost_packet; the seed dial owns the binding "
            "constructor and the sealed-seed constant."
            if live
            else "Proves the wrapper itself is inert. Same rebind, same "
            "branch dispositions, same per-row spread-model pricing and "
            "per-symbol accounting, then the frozen (tick, metadata) pair is "
            "returned unchanged -- byte-equal, not merely economically "
            "equal. If an arm with this installed is OUTCOME_IDENTICAL to an "
            "arm with no repair, every difference the live repair produces "
            "is the NUMBER. The control does NOT extend the component-source "
            "authority table: it emits only frozen quote sources."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


# ---------------------------------------------------------------------------
# repair 4 -- the cost ruler (FA Phase C R-COST-TRUTH part (b); B5 C4-A)
# ---------------------------------------------------------------------------
#
# C4-A measured that the two monthly pools ride DIFFERENT cost rulers: January's
# `cost_r` equals its four-component sum on 27,658/27,658 rows while February's
# deviates on 17,819/24,239 (73.5%), including flat 0.12 overrides on GER40
# (1,635 rows; Jan measured mean 0.323), UKOIL_cash (1,203) and USOIL_cash (717)
# that are component-blind in BOTH directions (UKOIL components 0.049 -> cost
# 0.12; GER40 mean components 0.276 -> 0.12) and mechanically evict those
# symbols from every February C1 cell. No cross-month cell comparison is
# trusted until the ruler is harmonized.
#
# THE MECHANISM, found by reading this engine: `build_pretrade_cost_packet`
# emits `total_cost_r` as the component sum ONLY when the spread term exists
# AND the commission term is ready (`broker_net_cost_engine.py:694-706`);
# otherwise it emits None, and `broker_calibrated_replay_cost_packet` then
# replaces the missing total with the flat
# `broker_replay_default_total_cost_r` -- default 0.12
# (`v4_timewarp:58601-58613`) -- at `v4_timewarp:58929-58938`, recording it as
# `total_cost_components.authority_fallback_total_cost_r` plus a refusal
# reason. THAT is the cost_missing default class: a symbol whose commission
# (or spread) input cannot resolve gets 0.12 REGARDLESS of the components
# that did.
#
# WHAT THIS WRAPPER DOES -- and the honest boundary of what it can do:
#
# * CENSUS on every packet: counts identity-holds / identity-deviates /
#   flat-override / unevaluable, per symbol, so a 2-day smoke can SEE the
#   ruler instead of trusting it.
# * ENFORCEMENT where enforcement is honest: a packet still carrying the flat
#   override whose four components are complete AND witnessed (the
#   decision_semantics component-authority assessment, the same one the
#   commission repair uses) gets `total_cost_r` rebuilt as the component sum,
#   the override marker removed, and the engine's OWN
#   `pretrade_cost_refusal_reasons` re-run. Composed with spread_input_truth
#   (the spread term) and commission_broker_true_gated (the commission term +
#   measured witness) this state is provably near-empty -- the commission
#   repair redecodes it first -- and the wrapper is the guarantee that no
#   flat-override-with-complete-components packet can survive ANY composition.
# * DOCUMENTED REFUSAL for the remainder: a flat-override packet whose
#   component set is INCOMPLETE (commission unpriceable, swap source-gap,
#   spread absent) keeps the frozen 0.12 -- visibly, counted, with the missing
#   inputs stamped per row. Inventing the missing term is what F38 was; and
#   emitting `total_cost_r = None` instead would crash the engine's own gate.
#   Removing the 0.12 fallback AT SOURCE (so the total is never fabricated at
#   all) requires editing `v4_timewarp:58930` -- an engine-file edit outside
#   this session's runtime-rebind mandate, filed here as the remainder. On the
#   24-symbol replay surface the refusal set is measured EMPTY for the
#   commission term (`test_all_twenty_four_replay_symbols_price`), so the
#   composed stack harmonizes the whole surface.

#: The wrapper marker that makes live/control double-install detectable.
_COST_RULER_MARKER = "_gtos_cost_ruler_wrapper"


def _make_cost_ruler_patch(*, live: bool) -> accel.Patch:
    name = "cost_ruler_harmonize" if live else "cost_ruler_inert_control"
    stats = REPAIR_STATS.setdefault(name, _RepairStats())
    saved: dict[str, Any] = {}

    def apply() -> None:
        module = accel._module(TIMEWARP)
        required = (
            "broker_calibrated_replay_cost_packet",
            "broker_replay_default_total_cost_r",
        )
        missing = (
            [symbol for symbol in required if not hasattr(module, symbol)]
            if module is not None
            else list(required)
        )
        if missing:
            raise RepairUnavailable(
                f"{name}: {TIMEWARP} is missing {missing}; refusing rather "
                "than running an arm whose cost ruler could not be observed"
            )
        original = module.broker_calibrated_replay_cost_packet
        if getattr(original, _COST_RULER_MARKER, False):
            raise RepairUnavailable(
                f"{name}: a cost-ruler wrapper is already installed on "
                f"{TIMEWARP}.broker_calibrated_replay_cost_packet. The live "
                "repair and its inert control can never compose: the receipt "
                "could not say which ruler priced the pool."
            )

        def count(key: str) -> None:
            stats.errors[key] = stats.errors.get(key, 0) + 1

        def harmonize(packet: dict[str, Any], *, config: Any, symbol: str) -> None:
            """Census + (live only) the honest enforcement, in place."""

            components_raw = packet.get("total_cost_components")
            components = (
                dict(components_raw) if isinstance(components_raw, Mapping) else None
            )
            _total_status, total = cost_number(packet.get("total_cost_r"))
            component_sum = (
                cost_component_sum(components) if components is not None else None
            )
            fallback = (
                _packet_number(components.get("authority_fallback_total_cost_r"))
                if components is not None
                else None
            )
            flat_override = bool(
                fallback is not None
                and total is not None
                and math.isclose(total, fallback, rel_tol=0.0, abs_tol=1e-12)
            )
            status_value: str
            if flat_override:
                assert components is not None
                with _LOCK:
                    count("census:flat_override_seen")
                    count(f"flat_override:{symbol or 'no_symbol'}")
                    default_total = float(
                        module.broker_replay_default_total_cost_r(config or {})
                    )
                    if not math.isclose(
                        fallback, default_total, rel_tol=0.0, abs_tol=1e-12
                    ):
                        count("census:flat_override_nondefault_value")
                assessment = assess_cost_components(
                    components,
                    capture_evidence=cost_component_capture_evidence_from_packet(
                        packet
                    ),
                    measured_commission_r=packet.get(
                        "commission_r_broker_true_measured"
                    ),
                )
                if assessment["state"] == "complete":
                    redecoded = float(assessment["candidate_sum_r"])
                    with _LOCK:
                        stats.applied += 1
                        stats.charged_r_sum += redecoded
                        stats.charged_r_max = max(stats.charged_r_max, redecoded)
                        stats.baseline_r_sum += float(total)
                        row = stats.per_symbol.setdefault(
                            symbol, {"n": 0, "sum_r": 0.0, "baseline_sum_r": 0.0}
                        )
                        row["n"] += 1
                        row["sum_r"] += redecoded
                        row["baseline_sum_r"] = (
                            row.get("baseline_sum_r", 0.0) + float(total)
                        )
                    components.pop("authority_fallback_total_cost_r", None)
                    packet["total_cost_components"] = components
                    packet["total_cost_r"] = redecoded
                    packet["cost_component_sum_r"] = redecoded
                    packet["cost_ruler_flat_override_value"] = fallback
                    packet["cost_ruler_total_before_r"] = float(total)
                    packet["cost_ruler_total_after_r"] = redecoded
                    packet["legacy_emitter_fallback_cost_r"] = fallback
                    packet["legacy_emitter_fallback_replaced"] = True
                    publish_cost_assessment(packet, assessment)
                    from src.components.broker_net_cost_engine import (
                        pretrade_cost_refusal_reasons,
                    )

                    before_status = str(packet.get("status"))
                    reasons = pretrade_cost_refusal_reasons(packet)
                    packet["refusal_reasons"] = reasons
                    if packet.get("status") != "NOT_APPLICABLE":
                        packet["status"] = "REFUSED" if reasons else "PASSED"
                    with _LOCK:
                        if str(packet.get("status")) != before_status:
                            count(
                                f"status_{before_status}_to_{packet.get('status')}"
                            )
                    status_value = "flat_override_replaced_with_component_sum"
                else:
                    with _LOCK:
                        count(f"kept_flat_override:{assessment['state']}")
                    packet["cost_ruler_flat_override_value"] = fallback
                    packet["cost_ruler_missing_inputs"] = list(
                        assessment["missing_inputs"]
                    )
                    publish_cost_assessment(packet, assessment)
                    status_value = f"flat_override_kept_{assessment['state']}"
            elif total is not None and component_sum is not None:
                if math.isclose(
                    total,
                    component_sum,
                    rel_tol=0.0,
                    abs_tol=1e-8,
                ):
                    with _LOCK:
                        count("census:identity_holds")
                    status_value = "identity_holds"
                else:
                    # A deviation with no flat-override marker is a mechanism
                    # this wrapper has NOT identified; mutating it would be a
                    # guess wearing a repair label. Counted, stamped, refused.
                    with _LOCK:
                        count("census:identity_deviates")
                        count(f"deviates:{symbol or 'no_symbol'}")
                    packet_delta = float(total) - float(component_sum)
                    packet["cost_ruler_identity_delta_r"] = round(packet_delta, 9)
                    status_value = "identity_deviates_unrepaired"
            else:
                with _LOCK:
                    count("census:identity_unevaluable")
                status_value = "identity_unevaluable_incomplete_components"
            packet["cost_ruler_harmonize_status"] = status_value

        def ruled(**kwargs: Any) -> dict[str, Any]:
            packet = original(**kwargs)
            with _LOCK:
                stats.calls += 1
            if not isinstance(packet, dict):
                with _LOCK:
                    count("non_dict_packet")
                return packet
            symbol = str(
                packet.get("symbol")
                or (kwargs.get("candidate") or {}).get("symbol")
                or ""
            )
            if live:
                harmonize(packet, config=kwargs.get("config"), symbol=symbol)
            else:
                # INERT CONTROL: the identical census + would-be enforcement on
                # a DETACHED copy (same counters, so the control's report is
                # comparable line for line), then the packet returned unchanged.
                probe = copy.deepcopy(packet)
                harmonize(probe, config=kwargs.get("config"), symbol=symbol)
                with _LOCK:
                    stats.neutral += 1
                    # The probe's applied count is the control's, not an
                    # economic action: move it so `applied` stays an emission
                    # counter across every repair.
                    if stats.applied:
                        stats.applied -= 1
                        count("control_would_have_replaced_flat_override")
            return packet

        ruled._gtos_cost_ruler_wrapper = True  # type: ignore[attr-defined]
        saved[TIMEWARP] = original
        module.broker_calibrated_replay_cost_packet = ruled

    def revert() -> None:
        module = accel._module(TIMEWARP)
        if TIMEWARP in saved and module is not None:
            module.broker_calibrated_replay_cost_packet = saved[TIMEWARP]
        saved.clear()

    return accel.Patch(
        patch_id=name,
        summary=(
            "harmonize the cost ruler (B5 C4-A: February's cost_r deviates "
            "from its own component sum on 73.5% of rows, with flat 0.12 "
            "overrides on GER40/UKOIL_cash/USOIL_cash): census every packet's "
            "total-vs-component-sum identity, replace the flat "
            "authority-fallback total with the WITNESSED component sum where "
            "all four terms are complete, and keep-and-count the frozen 0.12 "
            "where they are not"
            if live
            else "INERT CONTROL for cost_ruler_harmonize: identical wrapper, "
            "identical census and would-be enforcement on a detached copy of "
            "every packet, the packet itself returned unchanged"
        ),
        identity_argument=(
            "An economic repair on the packets it touches, and a census on all "
            "the rest. The flat override enters at v4_timewarp:58929-58938 "
            "(total_cost_r <= 0 -> broker_replay_default_total_cost_r, default "
            "0.12) whenever build_pretrade_cost_packet could not complete its "
            "sum (broker_net_cost_engine.py:694-706: spread term missing OR "
            "commission term not ready). Enforcement fires ONLY when the four "
            "components are complete AND witnessed under the same "
            "decision_semantics authority assessment the commission repair "
            "uses (which requires the broker-true measured commission "
            "witness), so it can never invent a term; the re-gate is the "
            "engine's own pretrade_cost_refusal_reasons. Install AFTER "
            "commission_broker_true[_gated] so this wrapper is OUTERMOST and "
            "the census reads the ruler the pool actually gets -- "
            "resolve_repairs('cost_truth') encodes that order. The per-packet "
            "action sets are disjoint by construction: the commission wrapper "
            "re-gates only packets whose commission it PRICED (its unpriced "
            "path returns before regating), while this wrapper acts only on "
            "packets still carrying the flat override -- exactly the unpriced "
            "remainder -- so no packet is ever re-gated twice. Refuses to "
            "compose with cost_ceiling_* (a third gate owner would make the "
            "deciding ceiling unattributable) and with its own inert control. "
            "The residual that stays frozen -- incomplete component sets -- is "
            "counted per state and stamped per row with its missing inputs; "
            "removing the 0.12 fabrication at source is an engine-file edit "
            "(v4_timewarp:58930) outside the runtime-rebind mandate, filed as "
            "the documented remainder."
            if live
            else "Proves the wrapper is inert: same rebind, same census, same "
            "component-authority assessment and would-be replacement computed "
            "on a deep copy, then the original packet returned unchanged. An "
            "OUTCOME_IDENTICAL control arm attributes any live difference to "
            "the harmonized NUMBER, and the control's "
            "`control_would_have_replaced_flat_override` counter states how "
            "many packets the live arm would have moved."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


# ---------------------------------------------------------------------------
# R-BELIEF -- the honesty bundle (FA Phase C spec section 3; B5 C6 both lenses,
# B4 Q1/Q2, BELIEF-RECAL)
# ---------------------------------------------------------------------------
#
# Five repairs, one bundle-level expectation stated first and honestly
# (BELIEF-RECAL section 8, binding): honest beliefs make this family STAND
# DOWN -- fewer trades, not more R. 0/108 BH-marked cells at alpha 0.10; the
# four nominal January positives transfer to February at -19.13 R. The value
# of R-BELIEF is truthful refusal and truthful pricing of any FUTURE family,
# not recovered edge from this pool. Any claim that a belief repair alone
# produced a positive broad-V4 book is a red flag against the receipts.
#
# THE CHARGE-POINT DECISION (spec 3.1, C6-B): the single charge point is
# LIVE-STYLE INSIDE THE DEBATE. Chosen because the defect class is replay/live
# DIVERGENCE -- the runtime builder passes top-level `cost_r` and
# `candidate_direction` (`probability_debate_v4.py:1094-1096`) while the
# replay builder omits both (`v4_timewarp:58197-58213`) -- and replay-style-
# at-the-consumers would leave the two systems running different belief code
# forever. C6-B measured what the naive wire does landed alone (the downstream
# funnel already charges cost exactly once): expected_net_r <= 0 goes
# 42.8% -> 57.8%, router-floor exclusion 61.3% -> 78.1%. So the wire and the
# downstream neutralizations land as ONE atomic id, and the context-wire-only
# form is REFUSED as a registrable id (`REFUSED_REPAIR_FORMS`).
#
# THE NEUTRALIZATION MECHANISM, and why it is exact rather than approximate:
# every downstream charge site reads the side thesis through ONE tiny helper,
# `TIMEWARP.probability_thesis` (4 call sites: evaluate_candidate_v4:67447,
# build_selector_event:58229, :55693, :78742), and then subtracts cost_r from
# the EV it read (`expected_net_r = round(ev_r - cost_r, 12)` at :67450 and
# the build_selector_event twin). The thesis record carries the exact cost
# the debate subtracted (`ProbabilityThesis.cost_r`, emitted by to_record).
# The add-back wrapper restores EV_precost = ev_charged + thesis.cost_r on
# the COPY probability_thesis returns -- so every frozen downstream
# subtraction lands on a restored quantity and nets to the single-charged
# ev_charged, by arithmetic identity, with zero engine-file edits:
#
#   expected_net_r = (ev_charged + c) - c = ev_charged        (exactly once)
#
# The debate RECORD itself (probability_packet on the row) keeps the charged
# EV, the fired vetoes and the charged selection scores untouched -- the
# record is the truth, the attachment layer gets the pre-cost restatement its
# consumers were calibrated for. Consequences the spec's neutralization list
# asked for, delivered by the same identity:
#   * v4_timewarp:67450 -- neutralized (nets to ev_charged);
#   * router expected_net floors :16883-16886 (0.55/0.85 at :11673/:11669) --
#     keep gating a SINGLE-charged expected_net_r, semantics preserved,
#     no change needed;
#   * the allocator (`_candidate_value` prefers ev_r -> value_source
#     "decision_time_ev_r", subtracts cost_total at :19329/:15765-15770 with
#     anti-double-charge exempting only expected_net_r-family sources) --
#     candidate_ev_r stays PRE-cost by restatement, so the allocator's own
#     single subtraction remains exactly one charge, untouched.
# The p-channel (cost_penalty = cost_r * 0.7 in the sigmoid,
# `probability_debate_v4.py:748-753`) and the +0.08 direction prior are the
# true parity content and go LIVE; the debate's own veto
# (`EV_below_trade_threshold`, min_trade_ev_r 0.0, :824-856) becomes able to
# fire -- ex ante ~42.8% of pool rows at the single charge point.
#
# P-GATE RE-BASELINE (spec 3.1 item 4): the replay p-gates were calibrated
# against a cost-blind p. With the p-channel live, p shifts by
# ~-0.43 logit at the January median cost (C6-B: median cost_r 0.6166 x the
# engine's cost_probability_penalty_multiplier 0.7 = 0.43162). The named
# gates move DOWN by that logit so they keep their calibrated operating
# point at median cost; per-row deviation from median stays live:
#   0.58 (dynamic_budget_package_min_probability, resolved in
#         `_scheduler_config_uncached`, v4_timewarp:30141-30144)
#   0.70 (SOURCE_BOUND_ROUTER_REFUSAL_MIN_PROBABILITY, :11674, module attr
#         read at gate time :16873 and at the floor-stamping sites)
#   0.85 / 0.80 (selector_reduce_risk_numeric_disagreement_min_probability /
#         selector_reduce_risk_new_entry_min_probability, resolved in the
#         same `_scheduler_config_uncached`, :31382-31385 / :31398-31401)
# RUNTIME_ROUTER_REFUSAL_MIN_PROBABILITY (0.75) belongs to the "runtime"
# floor family the spec did not name; it is left frozen and any crossing is
# visible in the row's own failure strings.
#
# THE PER-ROW SINGLE-CHARGE CENSUS: a census wrapper on
# `TIMEWARP.evaluate_candidate_v4` classifies every emitted row from its own
# fields -- ev_charged and c from the probability_packet's side thesis (the
# debate's untouched record), expected_net_r from the row:
#   |expected_net - ev_charged|       <= tol  -> charged_1x
#   |expected_net - (ev_charged - c)| <= tol  -> charged_2x  (double charge)
#   |expected_net - (ev_charged + c)| <= tol  -> charged_0x  (uncharged)
# 2x-count must be 0 and 0x-count must be 0 on priced rows (c > 0); rows with
# c == 0 are counted zero_cost_row (the three classes coincide at c = 0).

#: The allocator module. Its scoring chain resolves internally through its own
#: module globals (`_candidate_option` :27939 -> `_sum_scheduler_score_components`
#: :23209 -> `_candidate_edge_score` :13097/:23963), so module-attribute
#: rebinds reach every consumer; no other module from-imports these names
#: (verified by rg).
ALLOCATOR = "src.research.moonshot_scheduler_v4_best_trade_allocator"

#: C6-B evidence, committed walk corpus: median January pool cost_r.
JAN_POOL_MEDIAN_COST_R = 0.6166
#: The debate's own default (`probability_debate_v4.py:753`,
#: cost_probability_penalty_multiplier).
DEBATE_COST_PENALTY_MULTIPLIER = 0.7
#: Derived, not typed: the median-cost logit shift the p-channel applies.
P_GATE_LOGIT_SHIFT = JAN_POOL_MEDIAN_COST_R * DEBATE_COST_PENALTY_MULTIPLIER


def rebaselined_p_gate(value: float) -> float:
    """sigmoid(logit(value) - P_GATE_LOGIT_SHIFT); the ex-ante declared map."""

    clamped = min(max(float(value), 1e-9), 1.0 - 1e-9)
    return 1.0 / (1.0 + math.exp(-(math.log(clamped / (1.0 - clamped)) - P_GATE_LOGIT_SHIFT)))


#: The scheduler-config keys the re-baseline moves (spec 3.1 item 4's
#: 0.58 / 0.85 / 0.80), resolved inside `_scheduler_config_uncached`.
P_GATE_SCHEDULER_CONFIG_KEYS = (
    "dynamic_budget_package_min_probability",
    "selector_reduce_risk_numeric_disagreement_min_probability",
    "selector_reduce_risk_new_entry_min_probability",
)
#: The module-attr gate (spec's 0.70), rebound directly.
SOURCE_BOUND_MIN_PROBABILITY_ATTR = "SOURCE_BOUND_ROUTER_REFUSAL_MIN_PROBABILITY"

#: Wrapper markers. Same-kind double install is refused at apply time; the
#: markers are PROPAGATED through wrapper chains so a marker anywhere in the
#: chain is visible on the outermost binding.
_MARK_CONTEXT_WIRE = "_gtos_belief_context_wire_wrapper"
_MARK_DEBATE = "_gtos_belief_debate_wrapper"
_MARK_THESIS_ADDBACK = "_gtos_belief_thesis_addback_wrapper"
_MARK_CHARGE_CENSUS = "_gtos_belief_charge_census_wrapper"
_MARK_PGATE = "_gtos_belief_pgate_wrapper"
_MARK_HASH = "_gtos_belief_hash_wrapper"
_MARK_CONFIDENCE = "_gtos_belief_confidence_wrapper"
_MARK_FILL_SUM = "_gtos_belief_fill_sum_wrapper"
_MARK_FILL_EDGE = "_gtos_belief_fill_edge_wrapper"
_MARK_EV_WALKED = "_gtos_belief_ev_walked_wrapper"


def _carry_markers(new_fn: Any, old_fn: Any, *own: str) -> Any:
    """Copy `_gtos_*` markers from the wrapped function, then add our own."""

    for attr in dir(old_fn):
        if attr.startswith("_gtos_") and getattr(old_fn, attr, False):
            setattr(new_fn, attr, True)
    for marker in own:
        setattr(new_fn, marker, True)
    return new_fn


def _refuse_same_kind(name: str, current: Any, marker: str, symbol: str) -> None:
    if getattr(current, marker, False):
        raise RepairUnavailable(
            f"{name}: a wrapper of the same kind ({marker}) is already "
            f"installed on {symbol}. The live repair and its inert control "
            "can never compose: the pool could not say which belief system "
            "priced it. The apply() guard refuses even when validation is "
            "bypassed."
        )


def _count(stats: _RepairStats, key: str, n: int = 1) -> None:
    with _LOCK:
        stats.errors[key] = stats.errors.get(key, 0) + n


def _stamp_pre_repair(row: dict[str, Any], field: str) -> None:
    """First-mover pre_repair stamp: the frozen-most value wins on composition."""

    row.setdefault(f"pre_repair_{field}", row.get(field))


def _side_thesis(record: Any, action: str) -> dict[str, Any]:
    """Plain scan of the record's theses. Deliberately NOT the (rebindable)
    TIMEWARP.probability_thesis -- the census must read the debate's own
    record, never a restored copy."""

    theses = record.get("theses") if isinstance(record, Mapping) else None
    for thesis in theses if isinstance(theses, list) else ():
        if isinstance(thesis, Mapping) and str(thesis.get("action")) == action:
            return dict(thesis)
    return {}


def _side_action(side: Any) -> str | None:
    text = str(side or "").upper()
    if text == "LONG":
        return "long"
    if text == "SHORT":
        return "short"
    return None


CHARGE_CENSUS_TOL = 1e-9


def belief_charge_census_classify(
    *,
    ev_charged: float | None,
    debate_cost_r: float | None,
    expected_net_r: float | None,
    tol: float = CHARGE_CENSUS_TOL,
) -> str:
    """Classify one row's end-to-end cost charge count from its own fields."""

    if ev_charged is None or debate_cost_r is None or expected_net_r is None:
        return "unclassifiable_missing_fields"
    if abs(debate_cost_r) <= tol:
        return "zero_cost_row"
    if abs(expected_net_r - ev_charged) <= tol:
        return "charged_1x"
    if abs(expected_net_r - (ev_charged - debate_cost_r)) <= tol:
        return "charged_2x"
    if abs(expected_net_r - (ev_charged + debate_cost_r)) <= tol:
        return "charged_0x"
    return "unclassifiable_off_grid"


def _make_belief_cost_patch(*, live: bool) -> accel.Patch:
    """Spec 3.1 -- ATOMIC: context wire + downstream neutralization (the
    thesis add-back) + counterfactual stamps + per-row charge census + the
    p-gate re-baseline. Five rebinds, installed all-or-nothing."""

    name = "belief_cost_single_charge" if live else "belief_cost_inert_control"
    stats = REPAIR_STATS.setdefault(name, _RepairStats())
    saved: dict[str, Any] = {}

    def apply() -> None:
        module = accel._module(TIMEWARP)
        required = (
            "build_probability_context",
            "evaluate_probability_debate_team_v4",
            "probability_thesis",
            "evaluate_candidate_v4",
            "_scheduler_config_uncached",
            SOURCE_BOUND_MIN_PROBABILITY_ATTR,
            "safe_float",
        )
        missing = (
            [symbol for symbol in required if not hasattr(module, symbol)]
            if module is not None
            else list(required)
        )
        if missing:
            raise RepairUnavailable(
                f"{name}: {TIMEWARP} is missing {missing}; the atomic bundle "
                "cannot be installed and refuses rather than running a "
                "partially-wired belief system"
            )
        checks = (
            ("build_probability_context", _MARK_CONTEXT_WIRE),
            ("evaluate_probability_debate_team_v4", _MARK_DEBATE),
            ("probability_thesis", _MARK_THESIS_ADDBACK),
            ("evaluate_candidate_v4", _MARK_CHARGE_CENSUS),
            ("_scheduler_config_uncached", _MARK_PGATE),
        )
        for symbol, marker in checks:
            _refuse_same_kind(name, getattr(module, symbol), marker, symbol)

        original_context = module.build_probability_context
        original_debate = module.evaluate_probability_debate_team_v4
        original_thesis = module.probability_thesis
        original_evaluate = module.evaluate_candidate_v4
        original_sched = module._scheduler_config_uncached
        original_min_p = getattr(module, SOURCE_BOUND_MIN_PROBABILITY_ATTR)
        safe_float = module.safe_float

        # -- rebind 1: the context wire (live parity keys) -------------------
        def wired(candidate: Any, asof_utc: Any, mso: Any, **kwargs: Any) -> dict[str, Any]:
            context = original_context(candidate, asof_utc, mso, **kwargs)
            with _LOCK:
                stats.calls += 1
            cost_kwarg = kwargs.get("cost_r")
            if cost_kwarg is not None:
                resolved = safe_float(cost_kwarg, 0.0)
            else:
                # The engine's own resolution order, read back from its own
                # output: the selector source's cost_sensitivity is the
                # UNCLAMPED resolved cost_r (v4_timewarp:58127).
                resolved = None
                for source in context.get("sources") or ():
                    if (
                        isinstance(source, Mapping)
                        and source.get("source_family") == "selector"
                    ):
                        resolved = safe_float(source.get("cost_sensitivity"), 0.0)
                        break
                if resolved is None:
                    _count(stats, "cost_unresolvable_not_wired")
                    return context
                _count(stats, "cost_resolved_from_selector_source")
            wired_cost = float(resolved) if live else 0.0
            context["cost_r"] = wired_cost
            context["belief_cost_charge_point"] = (
                "debate_live_style" if live else "inert_control_zero_cost"
            )
            if live:
                direction = candidate.get("side") if isinstance(candidate, Mapping) else None
                if direction is not None:
                    context["candidate_direction"] = direction
                    _count(stats, "candidate_direction_wired")
                with _LOCK:
                    if wired_cost > 0:
                        stats.applied += 1
                        stats.charged_r_sum += wired_cost
                        stats.charged_r_max = max(stats.charged_r_max, wired_cost)
                    else:
                        stats.errors["wired_zero_cost"] = (
                            stats.errors.get("wired_zero_cost", 0) + 1
                        )
            else:
                # Control: the key exists (same call graph inside the debate),
                # the value is 0.0, candidate_direction keeps absent-semantics.
                with _LOCK:
                    stats.neutral += 1
            return context

        # -- rebind 2: the debate counterfactual + veto census ---------------
        def debated(context: Any, config: Any) -> Any:
            decision = original_debate(context, config)
            if not isinstance(context, Mapping) or "belief_cost_charge_point" not in context:
                # A context this bundle did not build (foreign caller): pass
                # through, counted.
                _count(stats, "debate_context_not_ours_passthrough")
                return decision
            _count(stats, "debate_calls")
            stripped = {
                key: value
                for key, value in context.items()
                if key
                not in ("cost_r", "candidate_direction", "belief_cost_charge_point")
            }
            frozen = original_debate(stripped, config)
            _count(stats, "counterfactual_runs")
            action = _side_action(context.get("side"))
            main_side = next(
                (t for t in decision.theses if t.action == action), None
            )
            frozen_side = next(
                (t for t in frozen.theses if t.action == action), None
            )
            if main_side is not None and live:
                if "EV_below_trade_threshold" in main_side.vetoes:
                    _count(stats, "veto_ev_below_trade_threshold_fired")
                if "probability_below_trade_threshold" in main_side.vetoes:
                    _count(stats, "veto_probability_below_threshold_fired")
            block = {
                "repair": name,
                "charge_point": context.get("belief_cost_charge_point"),
                "wired_cost_r": context.get("cost_r"),
                "pre_repair_probability": (
                    frozen_side.probability if frozen_side is not None else None
                ),
                "pre_repair_ev_r": (
                    frozen_side.ev_r if frozen_side is not None else None
                ),
                "charged_probability": (
                    main_side.probability if main_side is not None else None
                ),
                "charged_ev_r": (
                    main_side.ev_r if main_side is not None else None
                ),
                "counterfactual": (
                    "same_engine_same_config_cost_and_direction_keys_stripped"
                ),
            }
            return dataclasses.replace(
                decision,
                debate_controls={
                    **decision.debate_controls,
                    "belief_cost_single_charge": block,
                },
            )

        # -- rebind 3: the add-back (downstream neutralization) --------------
        def restored(record: Any, action: str) -> dict[str, Any]:
            thesis = original_thesis(record, action)
            if not thesis:
                return thesis
            _count(stats, "thesis_reads")
            charged_cost = safe_float(thesis.get("cost_r"), 0.0)
            charged_ev = safe_float(
                thesis.get("ev_r"), safe_float(thesis.get("EV"), 0.0)
            )
            addback = charged_cost if live else 0.0
            if charged_cost > 0:
                _count(
                    stats,
                    "thesis_addback_applied" if live else "thesis_addback_zero_control",
                )
                thesis["debate_charged_ev_r"] = charged_ev
                thesis["debate_charged_cost_r"] = charged_cost
                thesis["ev_precost_restored_for_single_charge"] = bool(live)
                if live:
                    thesis["EV"] = thesis["ev_r"] = charged_ev + addback
            return thesis

        # -- rebind 4: the per-row charge census ------------------------------
        def censused(**kwargs: Any) -> dict[str, Any]:
            result = original_evaluate(**kwargs)
            if not isinstance(result, dict):
                _count(stats, "census_non_dict_result")
                return result
            record = result.get("probability_packet")
            action = _side_action(
                (result.get("candidate_after_geometry") or {}).get("side")
                if isinstance(result.get("candidate_after_geometry"), Mapping)
                else (kwargs.get("candidate") or {}).get("side")
            )
            thesis = _side_thesis(record, action or "")
            ev_charged = _optional_float(thesis.get("ev_r"))
            debate_cost = _optional_float(thesis.get("cost_r"))
            expected_net = _optional_float(result.get("expected_net_r"))
            verdict = belief_charge_census_classify(
                ev_charged=ev_charged,
                debate_cost_r=debate_cost,
                expected_net_r=expected_net,
            )
            _count(stats, f"census:{verdict}")
            result["belief_cost_charge_census"] = {
                "classification": verdict,
                "debate_charged_ev_r": ev_charged,
                "debate_charged_cost_r": debate_cost,
                "expected_net_r": expected_net,
            }
            controls = (
                record.get("debate_controls") if isinstance(record, Mapping) else None
            )
            block = (
                controls.get("belief_cost_single_charge")
                if isinstance(controls, Mapping)
                else None
            )
            if isinstance(block, Mapping):
                for field, key in (
                    ("candidate_probability", "pre_repair_probability"),
                    ("probability", "pre_repair_probability"),
                    ("candidate_ev_r", "pre_repair_ev_r"),
                    ("ev_r", "pre_repair_ev_r"),
                    ("expectancy_r", "pre_repair_ev_r"),
                ):
                    if block.get(key) is not None:
                        result.setdefault(f"pre_repair_{field}", block.get(key))
                frozen_ev = _optional_float(block.get("pre_repair_ev_r"))
                row_cost = _optional_float(result.get("cost_r"))
                if frozen_ev is not None and row_cost is not None:
                    for field in ("candidate_expected_net_r", "expected_net_r"):
                        result.setdefault(
                            f"pre_repair_{field}", round(frozen_ev - row_cost, 12)
                        )
            return result

        # -- rebind 5: the p-gate re-baseline ---------------------------------
        def rebaselined(config: Any) -> dict[str, Any]:
            resolved = original_sched(config)
            for key in P_GATE_SCHEDULER_CONFIG_KEYS:
                before = _optional_float(resolved.get(key))
                if before is None:
                    _count(stats, f"p_gate_missing:{key}")
                    continue
                after = rebaselined_p_gate(before)
                _count(stats, f"p_gate:{key}:{before:.6g}->{after:.6g}")
                if live:
                    resolved = {**resolved, key: after}
            return resolved

        wired = _carry_markers(wired, original_context, _MARK_CONTEXT_WIRE)
        debated = _carry_markers(debated, original_debate, _MARK_DEBATE)
        restored = _carry_markers(restored, original_thesis, _MARK_THESIS_ADDBACK)
        censused = _carry_markers(censused, original_evaluate, _MARK_CHARGE_CENSUS)
        rebaselined = _carry_markers(rebaselined, original_sched, _MARK_PGATE)

        rebased_min_p = rebaselined_p_gate(float(original_min_p))
        _count(
            stats,
            f"p_gate:{SOURCE_BOUND_MIN_PROBABILITY_ATTR}:"
            f"{float(original_min_p):.6g}->{rebased_min_p:.6g}",
        )

        # All-or-nothing install with rollback: a partially-wired belief
        # system is exactly the double-charge/omission hazard this id exists
        # to prevent.
        try:
            saved["build_probability_context"] = original_context
            module.build_probability_context = wired
            saved["evaluate_probability_debate_team_v4"] = original_debate
            module.evaluate_probability_debate_team_v4 = debated
            saved["probability_thesis"] = original_thesis
            module.probability_thesis = restored
            saved["evaluate_candidate_v4"] = original_evaluate
            module.evaluate_candidate_v4 = censused
            saved["_scheduler_config_uncached"] = original_sched
            module._scheduler_config_uncached = rebaselined
            saved[SOURCE_BOUND_MIN_PROBABILITY_ATTR] = original_min_p
            if live:
                setattr(
                    module, SOURCE_BOUND_MIN_PROBABILITY_ATTR, rebased_min_p
                )
        except Exception:
            revert()
            raise

    def revert() -> None:
        module = accel._module(TIMEWARP)
        if module is not None:
            for symbol, value in saved.items():
                setattr(module, symbol, value)
        saved.clear()

    return accel.Patch(
        patch_id=name,
        summary=(
            "single-charge-point repair (ATOMIC): wire cost_r + "
            "candidate_direction into the replay debate context (live parity, "
            "v4_timewarp:58197-58213 vs probability_debate_v4.py:1094-1096), "
            "restore the pre-cost EV on every probability_thesis read so the "
            "frozen downstream subtraction (:67450) nets to exactly one "
            "charge, stamp the frozen counterfactual per row, census "
            "0x/1x/2x per row, and re-baseline the p-gates "
            "(0.58/0.70/0.85/0.80) by the declared -0.4316 median-cost logit"
            if live
            else "INERT CONTROL for belief_cost_single_charge: identical five "
            "wrappers; cost_r wired with value 0.0, candidate_direction "
            "absent-semantics preserved, add-back adds 0.0, census and "
            "counterfactual run identically, p-gates computed then applied "
            "at their ORIGINAL values"
        ),
        identity_argument=(
            "Changes probability, EV availability of the debate veto, and "
            "admission on purpose -- a repair, expected to REDUCE trades "
            "(the ex-ante veto census is ~42.8% of pool rows at the single "
            "charge point). The charge point is live-style inside the debate "
            "because the defect is replay/live divergence (C6-A/C6-B); the "
            "context-wire-only form is refused by name (REFUSED_REPAIR_FORMS) "
            "because B5 measured it double-charges 57.8%/78.1% of the funnel. "
            "Neutralization is exact by arithmetic identity, not field "
            "surgery: every downstream charge site reads the side thesis "
            "through TIMEWARP.probability_thesis (4 call sites, all in-module) "
            "and subtracts cost_r from what it reads; the add-back restores "
            "ev+cost on the returned COPY so each frozen subtraction nets to "
            "the charged EV, while the debate record on the row keeps the "
            "charged values and fired vetoes untouched. The allocator "
            "(value_source decision_time_ev_r, score_cost_total at "
            "moonshot_scheduler:19329/:15765) and the router expected_net "
            "floors (:16883-16886) therefore keep gating single-charged "
            "quantities with no rebind of their own -- their neutralization "
            "IS the restored field semantics. The per-row census reads only "
            "the row's own emitted fields and must show 2x = 0 and 0x = 0 on "
            "priced rows. P-gate re-baseline is derived, not typed: "
            "sigmoid(logit(g) - 0.6166*0.7) on the four named gates, both "
            "resolved-config keys (_scheduler_config_uncached, reached by the "
            "CampaignExactCache path too, :3840) and the module constant "
            "(read at :16873 and the floor-stamping sites, so gate and stamps "
            "stay consistent). Composes with the CJ recipe, cost_truth, the "
            "seed dial and the R-SCHEMA cuts -- disjoint rebind targets: this "
            "bundle owns the debate-context/thesis/scheduler-config chain; "
            "the cost repairs own the cost-packet builders; the seed dial "
            "owns the binding constructor. evaluate_candidate_v4 is shared "
            "with belief_ev_walked_contract by DESIGN (census inner, reprice "
            "outer -- install order in resolve_repairs('belief'))."
            if live
            else "Proves the plumbing is inert: same five wrappers, same "
            "counterfactual debate run, same census arithmetic, and the "
            "debate receives cost_r = 0.0 -- which the engine's own reader "
            "(_positive_float(context.get('cost_r') or ..., 0.0)) cannot "
            "distinguish from the frozen absent key, so p, EV, vetoes and "
            "every downstream quantity are outcome-identical to the frozen "
            "engine. Any live-vs-control difference is the WIRED NUMBER."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


# -- spec 3.2: the sha-derived probability term ------------------------------

#: The engine's own weights and clamp (v4_timewarp:53682-53694), mirrored so
#: the wrapper can PROVE its reconstruction against the frozen output before
#: applying -- reconstruction drift keeps the frozen value and is counted.
FOLLOW_STRENGTH_WEIGHTS = (
    ("extreme_strength", 0.22),
    ("trend_follow", 0.18),
    ("volatility_balance", 0.16),
    ("rr_signal", 0.16),
    ("mso_follow_ratio", 0.24),
)
FAMILY_HASH_WEIGHT = 0.04
FOLLOW_STRENGTH_CLAMP = (0.05, 0.98)


def _make_hash_removal_patch(*, live: bool) -> accel.Patch:
    name = "belief_hash_term_removal" if live else "belief_hash_inert_control"
    stats = REPAIR_STATS.setdefault(name, _RepairStats())
    saved: dict[str, Any] = {}

    def apply() -> None:
        module = accel._module(TIMEWARP)
        if module is None or not hasattr(module, "candidate_feature_signal"):
            raise RepairUnavailable(
                f"{name}: {TIMEWARP}.candidate_feature_signal is not "
                "importable; refusing rather than running with the hash term "
                "silently live"
            )
        original = module.candidate_feature_signal
        _refuse_same_kind(name, original, _MARK_HASH, "candidate_feature_signal")

        def dehashed(candidate: Any, mso: Any) -> dict[str, Any]:
            signal = original(candidate, mso)
            with _LOCK:
                stats.calls += 1
            family_hash = _optional_float(signal.get("family_hash_signal"))
            if family_hash is None:
                _count(stats, "no_family_hash_signal_passthrough")
                return signal
            mso_signal = signal.get("mso_signal")
            mso_follow = (
                _optional_float(mso_signal.get("follow_ratio"))
                if isinstance(mso_signal, Mapping)
                else None
            ) or 0.0
            parts = {
                "extreme_strength": _optional_float(signal.get("extreme_strength")),
                "trend_follow": _optional_float(signal.get("trend_follow")),
                "volatility_balance": _optional_float(
                    signal.get("volatility_balance")
                ),
                "rr_signal": _optional_float(signal.get("rr_signal")),
                "mso_follow_ratio": mso_follow,
            }
            if any(value is None for value in parts.values()):
                _count(stats, "component_missing_kept_frozen")
                return signal
            low, high = FOLLOW_STRENGTH_CLAMP
            base = sum(parts[key] * weight for key, weight in FOLLOW_STRENGTH_WEIGHTS)
            reconstructed = min(max(base + family_hash * FAMILY_HASH_WEIGHT, low), high)
            frozen = _optional_float(signal.get("follow_strength"))
            if frozen is None or abs(reconstructed - frozen) > 1e-12:
                # The engine's formula changed under us; applying our
                # subtraction would be a guess wearing a repair label.
                _count(stats, "reconstruction_drift_kept_frozen")
                return signal
            dehashed_value = min(max(base, low), high)
            with _LOCK:
                if live:
                    stats.applied += 1
                else:
                    stats.neutral += 1
                stats.charged_r_sum += abs(frozen - dehashed_value)
                stats.charged_r_max = max(
                    stats.charged_r_max, abs(frozen - dehashed_value)
                )
            signal["pre_repair_follow_strength"] = frozen
            signal["pre_repair_family_hash_signal"] = family_hash
            if live:
                signal["follow_strength"] = dehashed_value
                signal["family_hash_signal"] = 0.0
                signal["family_hash_term_removed"] = True
            else:
                # Control: compute the term, multiply by 0.0 -- the applied
                # adjustment is zero and the frozen values are emitted.
                signal["family_hash_term_removed"] = False
                signal["family_hash_control_would_apply"] = dehashed_value
            return signal

        dehashed = _carry_markers(dehashed, original, _MARK_HASH)
        saved["candidate_feature_signal"] = original
        module.candidate_feature_signal = dehashed

    def revert() -> None:
        module = accel._module(TIMEWARP)
        if module is not None and "candidate_feature_signal" in saved:
            module.candidate_feature_signal = saved["candidate_feature_signal"]
        saved.clear()

    return accel.Patch(
        patch_id=name,
        summary=(
            "remove the content-free sha term from probability: follow_strength "
            "drops family_hash*0.04 (int(sha256(origin_family)[:8],16)/0xFFFFFFFF, "
            "v4_timewarp:53681-53694) and family_hash_signal exports 0.0; "
            "measured live effect of the term: 0.00446 p-span and 0.0114 R EV "
            "from the family NAME alone (B4 Q1)"
            if live
            else "INERT CONTROL for belief_hash_term_removal: identical wrapper, "
            "computes the hash term and the de-hashed value, multiplies the "
            "adjustment by 0.0 and emits the frozen signal"
        ),
        identity_argument=(
            "Removes ~0.45 pp of probability noise and ~1.1 cR of EV noise per "
            "family name -- the smallest defect on the path, repaired for "
            "truthfulness, not yield (spec 3.2); near-zero book delta "
            "expected. The rebind is TIMEWARP.candidate_feature_signal, whose "
            "callers all resolve through module globals in the same module "
            "(build_probability_context:58098, build_selector_event:58230, "
            "candidate_generation_rank_key:56783, :78748), so probability, "
            "selector features AND the replay-cap rank key are de-hashed by "
            "one rebind. The wrapper reconstructs the engine's own "
            "follow_strength from the returned components and REFUSES the row "
            "(kept frozen, counted) unless the reconstruction reproduces the "
            "frozen value to 1e-12 -- so the subtraction can never be applied "
            "to a formula it does not describe, including when the clamp "
            "binds. The rank-key tiebreak requirement is satisfied by the "
            "key's existing final element: candidate_id, a declared "
            "content-free deterministic tiebreak that does not masquerade as "
            "signal (v4_timewarp:56777-56791). Composes with every other "
            "repair: no other wrapper touches candidate_feature_signal."
            if live
            else "Proves the wrapper is inert: same rebind, same per-row "
            "reconstruction proof, same accounting of the would-be "
            "adjustment, frozen values emitted. An OUTCOME_IDENTICAL control "
            "arm attributes any live difference to the deleted term."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


# -- spec 3.3: the 0.55 confidence constant in the scheduler score -----------

#: The constant and its weight (REPLAY_MISSING_CONFIDENCE_DEFAULT = 0.55,
#: ultimate_candidate_package.py:72 -> :2064, scheduler mirror v4_timewarp:26625;
#: weight 0.20 at moonshot_scheduler:21994). Removal shifts every row by
#: exactly -0.11 iff the constant really is constant -- the census proves it.
CONFIDENCE_CONSTANT = 0.55
CONFIDENCE_SCORE_WEIGHT = 0.20


def _make_confidence_retire_patch(*, live: bool) -> accel.Patch:
    name = (
        "belief_confidence_constant_retire"
        if live
        else "belief_confidence_inert_control"
    )
    stats = REPAIR_STATS.setdefault(name, _RepairStats())
    saved: dict[str, Any] = {}

    def apply() -> None:
        module = accel._module(ALLOCATOR)
        if module is None or not hasattr(module, "_sum_scheduler_score_components"):
            raise RepairUnavailable(
                f"{name}: {ALLOCATOR}._sum_scheduler_score_components is not "
                "importable; refusing"
            )
        original = module._sum_scheduler_score_components
        _refuse_same_kind(
            name, original, _MARK_CONFIDENCE, "_sum_scheduler_score_components"
        )

        def retired(score_components: Any) -> float:
            total = original(score_components)
            with _LOCK:
                stats.calls += 1
            if not isinstance(score_components, dict):
                _count(stats, "non_dict_components_passthrough")
                return total
            component = _optional_float(score_components.get("confidence_component"))
            if component is None:
                _count(stats, "confidence_component_absent")
                return total
            expected = round(CONFIDENCE_CONSTANT * CONFIDENCE_SCORE_WEIGHT, 12)
            if abs(component - expected) > 1e-9:
                # The constant was not constant -- a FINDING, reported, never
                # hidden; the rank-inertness claim fails on this row.
                _count(stats, "uniform_shift_violation_nonconstant_confidence")
            score_components["pre_repair_confidence_component"] = component
            score_components["score_with_confidence_component"] = total
            score_components["score_without_confidence_component"] = (
                total - component
            )
            with _LOCK:
                if live:
                    stats.applied += 1
                else:
                    stats.neutral += 1
                stats.charged_r_sum += component
            if live:
                score_components["confidence_component"] = 0.0
                score_components["confidence_component_retired"] = True
                return total - component
            score_components["confidence_component_retired"] = False
            return total

        retired = _carry_markers(retired, original, _MARK_CONFIDENCE)
        saved["_sum_scheduler_score_components"] = original
        module._sum_scheduler_score_components = retired

    def revert() -> None:
        module = accel._module(ALLOCATOR)
        if module is not None and "_sum_scheduler_score_components" in saved:
            module._sum_scheduler_score_components = saved[
                "_sum_scheduler_score_components"
            ]
        saved.clear()

    return accel.Patch(
        patch_id=name,
        summary=(
            "retire the candidate_confidence constant from the scheduler "
            "score: candidate_confidence is 0.55 on 100% of replay rows "
            "(REPLAY_MISSING_CONFIDENCE_DEFAULT, ultimate_candidate_package"
            ".py:72) yet feeds the legacy score at weight 0.20 -- a constant "
            "wearing a weight; the term is removed from the component sum and "
            "the with/without counterfactual is stamped per row"
            if live
            else "INERT CONTROL for belief_confidence_constant_retire: keep "
            "the term, weight 0.0 semantics computed and stamped, ORIGINAL "
            "total returned -- outcome-identical to the frozen engine"
        ),
        identity_argument=(
            "Expected effect ZERO on selection (spec 3.3): a constant x "
            "weight is rank-inert, so removal shifts every row's score by "
            "exactly -0.11 and can never reorder candidates -- PROVEN per "
            "row, not assumed: the wrapper stamps score_with/"
            "score_without_confidence_component on the components dict (which "
            "the engine projects onto rows) and counts "
            "uniform_shift_violation_nonconstant_confidence whenever the "
            "component differs from 0.55*0.20 by more than 1e-9; a nonzero "
            "count is a FINDING (the constant was not constant), reported "
            "not hidden. Rank invariance follows arithmetically from a zero "
            "violation count; absolute-threshold crossings (min_trade_score "
            "family) remain possible in principle and are exactly what the "
            "T2 zero-delta standard checks. The rebind is "
            "ALLOCATOR._sum_scheduler_score_components, the one place the "
            "legacy score total is formed (:23209, in-module resolution); "
            "setting confidence_component to 0.0 after stamping keeps the "
            "wrapper idempotent. Chains with "
            "belief_fill_probability_deweight on the same symbol by marker "
            "propagation -- the sum is linear, so the two subtractions "
            "compose exactly in either order."
            if live
            else "Proves removal == zero-weighting: the control computes the "
            "identical counterfactual and returns the ORIGINAL total, so a "
            "control arm is outcome-identical to the frozen engine while "
            "stamping what the live repair would have done."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


# -- spec 3.4: EV at the walked contract -------------------------------------

#: The January-fitted honest-belief cell table (BELIEF-RECAL section 1's
#: declared 160-cell partition with per-cell p-hat / W-bar / L-bar), committed
#: at the receipt's own path and pinned by sha256. Fitted on January ONLY --
#: development-fitted lane evidence by construction, disclosed on every row.
BELIEF_CELL_TABLE = (
    REPO_ROOT
    / "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/BELIEF_RECAL.json"
)
BELIEF_CELL_TABLE_SHA256 = (
    "9034e5401d167987c45ad84965b0d9ff7f49020b1ad3d5e9f5567d1795c57864"
)
#: BELIEF-RECAL section 1.1's fixed cost-band thresholds (absolute, no
#: quartile fitting, transfer byte-identically across windows).
BELIEF_COST_BANDS = ((0.10, "C1"), (0.30, "C2"), (1.00, "C3"))
BELIEF_COST_BAND_TOP = "C4"
#: Spec 3.4: n >= 30 at the finest granularity, Jeffreys/beta shrinkage
#: toward the pool base rate with prior mass 1.0 (declared here, ex ante).
BELIEF_CELL_MIN_N = 30
BELIEF_SHRINKAGE_PRIOR_MASS = 1.0


def belief_cost_band(cost_r: float) -> str:
    for threshold, band in BELIEF_COST_BANDS:
        if cost_r < threshold:
            return band
    return BELIEF_COST_BAND_TOP


class _BeliefCellTable:
    """The January cell table, loaded once, aggregated up a declared ladder:
    (family, band, session) -> (family, band) -> (band) -> pool."""

    def __init__(self) -> None:
        self._levels: Any = None
        self._pool_rate: float | None = None

    @staticmethod
    def _aggregate(cells: "list[dict[str, Any]]") -> dict[str, float]:
        n = sum(int(c["n"]) for c in cells)
        wins = sum(int(round(float(c["p_hat_win_gross"]) * int(c["n"]))) for c in cells)
        win_mass = sum(
            int(round(float(c["p_hat_win_gross"]) * int(c["n"])))
            for c in cells
            if c.get("mean_win_gross_r") is not None
        )
        w_bar = (
            sum(
                int(round(float(c["p_hat_win_gross"]) * int(c["n"])))
                * float(c["mean_win_gross_r"])
                for c in cells
                if c.get("mean_win_gross_r") is not None
            )
            / win_mass
            if win_mass
            else 0.0
        )
        loss_mass = sum(
            int(c["n"]) - int(round(float(c["p_hat_win_gross"]) * int(c["n"])))
            for c in cells
            if c.get("mean_loss_gross_abs_r") is not None
        )
        l_bar = (
            sum(
                (int(c["n"]) - int(round(float(c["p_hat_win_gross"]) * int(c["n"]))))
                * float(c["mean_loss_gross_abs_r"])
                for c in cells
                if c.get("mean_loss_gross_abs_r") is not None
            )
            / loss_mass
            if loss_mass
            else 0.0
        )
        return {"n": n, "wins": wins, "w_bar": w_bar, "l_bar": l_bar}

    def load(self) -> None:
        if self._levels is not None:
            return
        raw = BELIEF_CELL_TABLE.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != BELIEF_CELL_TABLE_SHA256:
            raise RepairUnavailable(
                "belief_ev_walked_contract: the cell table at "
                f"{BELIEF_CELL_TABLE} hashes {digest[:12]}..., not the pinned "
                f"{BELIEF_CELL_TABLE_SHA256[:12]}...; refusing to price "
                "beliefs from an unverified table"
            )
        import json

        cells = [
            {**cell["january"], "cell_id": cell["cell_id"],
             "origin_family": cell["origin_family"],
             "cost_band": cell["cost_band"],
             "route_session": cell["route_session"]}
            for cell in json.loads(raw)["cells"]
            if int(cell["january"]["n"]) > 0
        ]
        fine: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        mid: dict[tuple[str, str], list[dict[str, Any]]] = {}
        band: dict[str, list[dict[str, Any]]] = {}
        for cell in cells:
            fine.setdefault(
                (cell["origin_family"], cell["cost_band"], cell["route_session"]),
                [],
            ).append(cell)
            mid.setdefault((cell["origin_family"], cell["cost_band"]), []).append(cell)
            band.setdefault(cell["cost_band"], []).append(cell)
        pool = self._aggregate(cells)
        self._pool_rate = pool["wins"] / pool["n"] if pool["n"] else 0.0
        self._levels = (
            {key: self._aggregate(group) for key, group in fine.items()},
            {key: self._aggregate(group) for key, group in mid.items()},
            {key: self._aggregate(group) for key, group in band.items()},
            pool,
        )

    def price(
        self, *, family: str, band: str, session: str, cost_row: float
    ) -> dict[str, Any]:
        self.load()
        fine, mid, bands, pool = self._levels
        ladder = (
            ("family_band_session", fine.get((family, band, session))),
            ("family_band", mid.get((family, band))),
            ("band", bands.get(band)),
            ("pool", pool),
        )
        level_name, chosen = next(
            (
                (label, agg)
                for label, agg in ladder
                if agg is not None and agg["n"] >= BELIEF_CELL_MIN_N
            ),
            ("pool", pool),
        )
        q = self._pool_rate or 0.0
        k = BELIEF_SHRINKAGE_PRIOR_MASS
        p_raw = chosen["wins"] / chosen["n"] if chosen["n"] else q
        p_shrunk = (chosen["wins"] + k * q) / (chosen["n"] + k) if chosen["n"] else q
        w_bar = chosen["w_bar"]
        l_bar = chosen["l_bar"]
        ev = p_shrunk * w_bar - (1.0 - p_shrunk) * l_bar - cost_row
        p_star = (
            (l_bar + cost_row) / (w_bar + l_bar) if (w_bar + l_bar) > 0 else None
        )
        return {
            "cell_id": f"{family}|{band}|{session}",
            "granularity": level_name,
            "n": chosen["n"],
            "wins": chosen["wins"],
            "w_bar_gross_r": round(w_bar, 9),
            "l_bar_gross_abs_r": round(l_bar, 9),
            "pool_base_rate_gross": round(q, 9),
            "p_hat_raw": round(p_raw, 9),
            "p_hat_shrunk": round(p_shrunk, 9),
            "cost_row_r": cost_row,
            "ev_walked_r": round(ev, 9),
            "p_star_required": round(p_star, 9) if p_star is not None else None,
            "shrinkage": (
                f"beta_prior_mass_{k}_centered_on_pool_gross_win_rate"
            ),
        }


_BELIEF_CELLS = _BeliefCellTable()


def _make_ev_walked_patch(*, live: bool) -> accel.Patch:
    name = "belief_ev_walked_contract" if live else "belief_ev_walked_inert_control"
    stats = REPAIR_STATS.setdefault(name, _RepairStats())
    saved: dict[str, Any] = {}

    def apply() -> None:
        module = accel._module(TIMEWARP)
        if module is None or not hasattr(module, "evaluate_candidate_v4"):
            raise RepairUnavailable(
                f"{name}: {TIMEWARP}.evaluate_candidate_v4 is not importable; "
                "refusing"
            )
        original = module.evaluate_candidate_v4
        _refuse_same_kind(name, original, _MARK_EV_WALKED, "evaluate_candidate_v4")
        try:
            _BELIEF_CELLS.load()
        except RepairUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001 -- refusal must name any load failure
            raise RepairUnavailable(
                f"{name}: the belief cell table at {BELIEF_CELL_TABLE} did "
                f"not load ({type(exc).__name__}: {str(exc)[:120]}); refusing "
                "rather than running with unpriced beliefs"
            ) from exc

        def repriced(**kwargs: Any) -> dict[str, Any]:
            result = original(**kwargs)
            with _LOCK:
                stats.calls += 1
            if not isinstance(result, dict):
                _count(stats, "non_dict_result_passthrough")
                return result
            candidate = result.get("candidate_after_geometry")
            candidate = candidate if isinstance(candidate, Mapping) else {}
            family = str(candidate.get("origin_family") or "")
            session = str(candidate.get("route_session") or "")
            cost_row = _optional_float(result.get("cost_r"))
            if not family or cost_row is None:
                _count(stats, "cell_unpriced_missing_family_or_cost")
                result["belief_walked_contract_status"] = (
                    "unpriced_missing_family_or_cost_frozen_values_kept"
                )
                return result
            band = belief_cost_band(cost_row)
            priced = _BELIEF_CELLS.price(
                family=family, band=band, session=session, cost_row=cost_row
            )
            walked_rr = _optional_float(candidate.get("risk_reward_ratio"))
            block = {
                **priced,
                "walked_contract_rr": walked_rr,
                "contract_note": (
                    "priced AFTER the geometry rewrite (v4_timewarp:67680-67712) "
                    "from magnitudes measured on the walked 2.0R-capped-giveback "
                    "pool; the stamped 1.5R symmetric payoff described almost "
                    "no cell (W-bar 0.27-2.29, |L-bar| 0.30-1.00)"
                ),
                "cost_charge_note": (
                    "cost_row subtracted exactly once inside this formula; "
                    "expected_net_r is set to the same value, no downstream "
                    "subtraction remains"
                ),
                "evidence_class": (
                    "development_fitted_january_cells_billed_lane_evidence"
                ),
            }
            ev = float(priced["ev_walked_r"])
            with _LOCK:
                if live:
                    stats.applied += 1
                else:
                    stats.neutral += 1
                stats.charged_r_sum += cost_row
                stats.charged_r_max = max(stats.charged_r_max, cost_row)
                row = stats.per_symbol.setdefault(
                    str(candidate.get("symbol") or ""),
                    {"n": 0, "sum_r": 0.0, "baseline_sum_r": 0.0},
                )
                row["n"] += 1
                row["sum_r"] += ev
                baseline_ev = _optional_float(result.get("candidate_ev_r"))
                row["baseline_sum_r"] = row.get("baseline_sum_r", 0.0) + (
                    baseline_ev or 0.0
                )
            if ev < 0:
                _count(stats, "ev_negative_rows")
            _count(stats, f"granularity:{priced['granularity']}")
            if not live:
                # Control (spec 3.4's declared design): compute honest p/EV
                # alongside, stamp as observability, apply the ORIGINAL values.
                result["belief_walked_contract_observability"] = block
                result["belief_walked_contract_status"] = "control_observed_only"
                return result
            for field in (
                "candidate_probability",
                "probability",
                "candidate_ev_r",
                "ev_r",
                "expectancy_r",
                "candidate_expected_net_r",
                "expected_net_r",
            ):
                _stamp_pre_repair(result, field)
            p_shrunk = float(priced["p_hat_shrunk"])
            result["candidate_probability"] = p_shrunk
            result["probability"] = p_shrunk
            result["candidate_ev_r"] = ev
            result["ev_r"] = ev
            result["expectancy_r"] = ev
            result["candidate_expected_net_r"] = ev
            result["expected_net_r"] = ev
            result["belief_walked_contract"] = block
            result["belief_ev_negative"] = ev < 0
            result["belief_walked_contract_status"] = "applied"
            return result

        repriced = _carry_markers(repriced, original, _MARK_EV_WALKED)
        saved["evaluate_candidate_v4"] = original
        module.evaluate_candidate_v4 = repriced

    def revert() -> None:
        module = accel._module(TIMEWARP)
        if module is not None and "evaluate_candidate_v4" in saved:
            module.evaluate_candidate_v4 = saved["evaluate_candidate_v4"]
        saved.clear()

    return accel.Patch(
        patch_id=name,
        summary=(
            "price EV and expected_net at the WALKED contract: p-hat/W-bar/"
            "L-bar from the committed January cell table (BELIEF-RECAL, 160 "
            "declared cells, sha-pinned) at family x cost-band x session with "
            "n>=30 fallback ladder and beta shrinkage toward the pool gross "
            "win rate; EV = p*W - (1-p)*|L| - cost_row, allowed to go "
            "NEGATIVE, p* published beside it; the engine's stamped 1.5R "
            "symmetric EV (attached before the 2.0R-capped-giveback rewrite) "
            "is stamped pre_repair_*"
            if live
            else "INERT CONTROL for belief_ev_walked_contract: identical "
            "wrapper, identical cell pricing, honest p-hat/EV stamped as "
            "observability fields, ORIGINAL values applied (the spec's "
            "declared control design)"
        ),
        identity_argument=(
            "The stand-down repair (bundle headline): honest p-hat spans "
            "~0.42-0.58 in the BEST cells against stamped 0.766, and under "
            "these formulas essentially every cell of this family prices "
            "negative -- that is the CORRECT output, and the "
            "jury-cannot-express-a-loser property dies here: ev_negative_rows "
            "is counted and belief_ev_negative stamped per row. HOOK CHOICE, "
            "documented as the spec requires: recompute-at-rewrite, not "
            "move-computation -- the engine attaches belief at :67426-67450 "
            "and rewrites the contract to the 2.0R-capped giveback AFTER "
            "(:67680-67712) inside the same R2-bound function body, so "
            "moving the attachment would be an engine-file edit outside the "
            "runtime-rebind mandate; wrapping evaluate_candidate_v4 and "
            "repricing its RESULT is the first rebindable point where the "
            "walked contract (candidate_after_geometry.risk_reward_ratio) is "
            "known. The row-level authority fields are repriced (the package "
            "materialization's first_present chains read row fields first, "
            ":18983-18992, :16818-16828, so the funnel ranks and gates on the "
            "honest values); nested attach-time packets (selector_event, "
            "lifecycle) are left frozen as pre-repair provenance, disclosed "
            "by belief_walked_contract_status. Cost is charged exactly once "
            "INSIDE the formula (cost_row, the row's own measured cost -- "
            "not the cell mean -- so p* is row-exact) and expected_net_r is "
            "set to the same value, so composition with "
            "belief_cost_single_charge keeps the census single-charged: its "
            "census wrapper sits INNER (installed first in "
            "resolve_repairs('belief')) and classifies the debate chain "
            "before this wrapper overwrites. Under a composed cost-truth "
            "stack the band is assigned on the TRUTHED row cost while the "
            "cell magnitudes remain fitted on sealed January costs -- that "
            "is composition path-dependence, stamped per row (cost_row_r, "
            "granularity), and exactly why per-repair deltas do not sum. "
            "Fitted on January only: every number it produces is "
            "development-fitted lane evidence, stamped as such on the row."
            if live
            else "Proves the pricing plumbing is inert: same wrapper, same "
            "cell assignment, same shrinkage arithmetic, original values "
            "applied. An OUTCOME_IDENTICAL control arm attributes any live "
            "difference to the honest numbers."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


# -- spec 3.5: the fill-probability term (P1-blocked) ------------------------


def _make_fill_deweight_patch(*, live: bool) -> accel.Patch:
    name = (
        "belief_fill_probability_deweight"
        if live
        else "belief_fill_probability_inert_control"
    )
    stats = REPAIR_STATS.setdefault(name, _RepairStats())
    saved: dict[str, Any] = {}

    def apply() -> None:
        module = accel._module(ALLOCATOR)
        required = ("_sum_scheduler_score_components", "_candidate_edge_score")
        missing = (
            [symbol for symbol in required if not hasattr(module, symbol)]
            if module is not None
            else list(required)
        )
        if missing:
            raise RepairUnavailable(f"{name}: {ALLOCATOR} is missing {missing}; refusing")
        original_sum = module._sum_scheduler_score_components
        original_edge = module._candidate_edge_score
        _refuse_same_kind(
            name, original_sum, _MARK_FILL_SUM, "_sum_scheduler_score_components"
        )
        _refuse_same_kind(
            name, original_edge, _MARK_FILL_EDGE, "_candidate_edge_score"
        )

        def deweighted_sum(score_components: Any) -> float:
            total = original_sum(score_components)
            with _LOCK:
                stats.calls += 1
            if not isinstance(score_components, dict):
                _count(stats, "non_dict_components_passthrough")
                return total
            component = _optional_float(
                score_components.get("fill_probability_component")
            )
            if component is None:
                _count(stats, "fill_probability_component_absent")
                return total
            score_components["pre_repair_fill_probability_component"] = component
            score_components["score_with_fill_probability_component"] = total
            score_components["score_without_fill_probability_component"] = (
                total - component
            )
            with _LOCK:
                if live:
                    stats.applied += 1
                else:
                    stats.neutral += 1
                stats.charged_r_sum += component
                stats.charged_r_max = max(stats.charged_r_max, abs(component))
            if live:
                score_components["fill_probability_component"] = 0.0
                score_components["fill_probability_component_deweighted"] = True
                return total - component
            score_components["fill_probability_component_deweighted"] = False
            return total

        def deweighted_edge(**kwargs: Any) -> float:
            weight = _optional_float(kwargs.get("fill_probability_weight"))
            fill = _optional_float(kwargs.get("fill_probability")) or 0.0
            _count(stats, "edge_score_calls")
            if live:
                kwargs["fill_probability_weight"] = 0.0
                with _LOCK:
                    stats.charged_r_sum += fill * (weight or 0.0)
            return original_edge(**kwargs)

        deweighted_sum = _carry_markers(deweighted_sum, original_sum, _MARK_FILL_SUM)
        deweighted_edge = _carry_markers(
            deweighted_edge, original_edge, _MARK_FILL_EDGE
        )
        try:
            saved["_sum_scheduler_score_components"] = original_sum
            module._sum_scheduler_score_components = deweighted_sum
            saved["_candidate_edge_score"] = original_edge
            module._candidate_edge_score = deweighted_edge
        except Exception:
            revert()
            raise

    def revert() -> None:
        module = accel._module(ALLOCATOR)
        if module is not None:
            for symbol, value in saved.items():
                setattr(module, symbol, value)
        saved.clear()

    return accel.Patch(
        patch_id=name,
        summary=(
            "de-weight the fill-probability term from the scheduler score "
            "(spec 3.5, P1-blocked): execution_fill_probability is the 0.92 "
            "marketable-limit template (poi_execution_lifecycle.py:176-178, "
            "one constant for every symbol and session; 100% of executed "
            "fence trades rode 0.92/0.95) and the pool heuristic pins 19.2% "
            "of rows at its own 0.95 ceiling -- the additive score terms "
            "(legacy fill_probability_component, weight 0.10, and "
            "_candidate_edge_score's fill term) are dropped, stamped, counted"
            if live
            else "INERT CONTROL for belief_fill_probability_deweight: "
            "identical wrappers on both scoring functions, counterfactual "
            "with/without stamped, ORIGINAL totals and weight applied"
        ),
        identity_argument=(
            "Expected near-rank-inert TODAY (the term is a constant on "
            "marketable rows); the honest magnitude is UNKNOWN until P1 "
            "(fill truth from tick captures, SCHEDULED-ON-NEED) -- this item "
            "cannot be truthed inside this program's data, so it is bounded "
            "and labeled instead of modeled (spec 3.5 verbatim). Scope is "
            "the SCORE TERM only, exactly as the spec words it: the additive "
            "fill_probability_component in the legacy sum (weight 0.10, "
            "moonshot_scheduler:21998) and the additive fill term in "
            "_candidate_edge_score (weight kwarg forced 0.0; :15771-15777). "
            "The executable-transfer MULTIPLIER surfaces and the three "
            "template-vs-threshold gate decisions (full-risk 0.8, fallback "
            "envelope 0.85, stop-hazard 0.5) are decisions, not score terms "
            "-- they stay frozen, already stamped non-authoritative by "
            "decision_semantics.py:1429-1446, with the MISSED-projection "
            "extension owned by R-SCHEMA S6. The with/without counterfactual "
            "is stamped per row so near-rank-inertness is MEASURED, not "
            "asserted; the removed-term mass accumulates in charged_r_sum. "
            "Chains with belief_confidence_constant_retire on the shared sum "
            "symbol via marker propagation (linear sum, order-free)."
            if live
            else "Proves the wrapper pair is inert: same rebinds, same "
            "counterfactual computation and stamps, original totals emitted. "
            "An OUTCOME_IDENTICAL control arm attributes any live difference "
            "to the dropped term."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


#: The ONE candidate funnel in the lane. A first draft of this hook rebound
#: `V4DecisionCycleCore.generate_candidates` and its 2-day smoke censused ZERO
#: calls: the lane replays PREPARED day packs, whose candidates were generated
#: once at CJ's rematerialization and are decoded at `v4_timewarp:90651` /
#: consumed at `:90809` -- the producer path (`:90325`, `:90812` else-branch)
#: never executes in a lane arm, and the prepared branch calls no module
#: function at candidate entry. Both branches DO join at
#: `evaluate_symbol_candidates_with_batched_proof_hashes` (defined `:67852`,
#: called once, unqualified, at `:90952` -> module-global resolution), BEFORE
#: geometry/packet evaluation. That is the seam.
CANDIDATE_FUNNEL = "evaluate_symbol_candidates_with_batched_proof_hashes"
#: The default-off V27 candidate transform the arm-(v) hook enables (absent-false
#: key, explicit enabled=True call contract -- wave 18's wiring, untouched).
BREAKER_COMPONENT = "src.components.current_breaker_re_entry_repair"


def _make_breaker_transform_patch(*, live: bool) -> accel.Patch:
    name = (
        "candidate_breaker_transform" if live else "candidate_breaker_inert_control"
    )
    stats = REPAIR_STATS.setdefault(name, _RepairStats())
    saved: dict[str, Any] = {}

    def apply() -> None:
        timewarp = accel._module(TIMEWARP)
        if timewarp is None or not callable(
            getattr(timewarp, CANDIDATE_FUNNEL, None)
        ):
            raise RepairUnavailable(
                f"{name}: {TIMEWARP}.{CANDIDATE_FUNNEL} is not importable; "
                "the candidate seam does not exist and the hook refuses"
            )
        try:
            from src.components import current_breaker_re_entry_repair as breaker
        except Exception as exc:  # pragma: no cover - import failure is the message
            raise RepairUnavailable(
                f"{name}: {BREAKER_COMPONENT} failed to import ({exc!r}); refusing"
            )
        expected_cell = {
            "TRANSFORM_ID": "cq_current_breaker_inverted_target_5d_stop_0p25d_v1",
            "ENABLE_CONFIG_KEY": "phase18_current_breaker_re_entry_repair_enabled",
            "ORIGIN_FAMILY": "current_breaker_re_entry",
            "TARGET_DISTANCE_D": 5.0,
            "STOP_DISTANCE_D": 0.25,
        }
        drifted = {
            key: getattr(breaker, key, None)
            for key, value in expected_cell.items()
            if getattr(breaker, key, None) != value
        }
        if drifted:
            raise RepairUnavailable(
                f"{name}: the component no longer matches the declared V27 cell "
                f"({drifted}); refusing to run an arm whose receipt would name a "
                "transform that is not the billed candidate"
            )
        original = getattr(timewarp, CANDIDATE_FUNNEL)
        transform = breaker.apply_current_breaker_re_entry_repair
        family = breaker.ORIGIN_FAMILY
        breaker_error = breaker.CurrentBreakerRepairError

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            if args or "candidates" not in kwargs:
                # The call site passes everything by keyword (:90952). A
                # positional or candidates-less call means the funnel's
                # convention drifted under this hook; refusing is the only
                # answer whose receipt stays true.
                raise RepairUnavailable(
                    f"{name}: {CANDIDATE_FUNNEL} call convention drifted "
                    f"(args={len(args)}, candidates_kwarg="
                    f"{'candidates' in kwargs}); refusing"
                )
            out: "list[dict[str, Any]]" = []
            for row in kwargs["candidates"]:
                with _LOCK:
                    stats.calls += 1
                if str(row.get("origin_family") or "") != family:
                    with _LOCK:
                        stats.neutral += 1
                    out.append(row)
                    continue
                if live:
                    try:
                        repaired = transform(row, enabled=True)
                    except breaker_error:
                        # Fail-closed is the component's contract: a malformed
                        # breaker candidate is a data defect, not a skippable
                        # row. Count it, then let the arm die loudly.
                        with _LOCK:
                            key = "malformed_breaker_geometry"
                            stats.errors[key] = stats.errors.get(key, 0) + 1
                        raise
                    with _LOCK:
                        stats.applied += 1
                    out.append(repaired)
                else:
                    control = transform(row, enabled=False)
                    if control != row:
                        raise RepairUnavailable(
                            f"{name}: the DISABLED transform failed its own "
                            "deep-copy identity contract on a breaker row; the "
                            "control cannot prove inertness and refuses"
                        )
                    with _LOCK:
                        stats.applied += 1
                    out.append(control)
            kwargs["candidates"] = out
            return original(**kwargs)

        saved["fn"] = original
        setattr(timewarp, CANDIDATE_FUNNEL, wrapped)

    def revert() -> None:
        timewarp = accel._module(TIMEWARP)
        if "fn" in saved and timewarp is not None:
            setattr(timewarp, CANDIDATE_FUNNEL, saved["fn"])
        saved.clear()

    return accel.Patch(
        patch_id=name,
        summary=(
            "T2 arm (v)'s CANDIDATE door: every current_breaker_re_entry "
            "candidate entering the lane's one candidate funnel "
            "(evaluate_symbol_candidates_with_batched_proof_hashes -- the "
            "join point of the prepared-pack and fresh-generation branches, "
            "pre-geometry) is replaced by CQ's inverted 5D/0.25D transform "
            "(cq_current_breaker_inverted_target_5d_stop_0p25d_v1), explicit "
            "enabled=True per the component's own call contract; transformed "
            "rows then traverse every downstream eligibility, belief, cost, "
            "and admission gate unchanged"
            if live
            else "INERT CONTROL for candidate_breaker_transform: same funnel "
            "rebind, calls the transform with enabled=False (deep-copy "
            "pass-through), proves row identity per breaker candidate, "
            "transforms nothing"
        ),
        identity_argument=(
            "NOT an identity: this is the one deliberate economics-changing "
            "candidate treatment in the T2 map (the 'edge in' arm). Licensed "
            "by CANDIDATE_FAMILY_V27's billed look (CQ inverted-breaker "
            "5D/0.25D, +11.9 net R/trade TRAIN and HOLDOUT-January VAL, gate "
            "NOT_EVALUABLE at one fold of three) and declared ex ante in "
            "CELL_DECLARATION_V1 (424500467). The live config key "
            "phase18_current_breaker_re_entry_repair_enabled is NOT flipped "
            "anywhere -- absent-false everywhere, live path untouched; "
            "enablement is this hook's explicit per-call enabled=True, exactly "
            "the component's designed contract ('Selection is not "
            "activation'). Census: calls=candidates seen, neutral=non-breaker "
            "pass-throughs, applied=transformed rows; malformed geometry "
            "fails closed with the component's own error."
            if live
            else "Proves the wrapper is inert: same rebind, enabled=False "
            "pass-through, per-row deep-equality asserted. An "
            "OUTCOME_IDENTICAL control arm attributes any live difference to "
            "the transform itself."
        ),
        apply=apply,
        revert=revert,
        default_on=False,
    )


#: Repair FORMS that are refused as registrable ids, by name, with the
#: measured reason -- the atomicity rule (spec section 9 row 2).
REFUSED_REPAIR_FORMS: dict[str, str] = {
    "belief_cost_context_wire_only": (
        "REFUSED by the atomicity rule (B5 C6-B, spec 3.1/9.2): adding "
        "cost_r to the replay debate context WITHOUT the downstream "
        "neutralizations double-charges cost at every EV consumer -- "
        "measured on the committed walk corpus: expected_net_r <= 0 goes "
        "42.8% -> 57.8% and router-floor exclusion 61.3% -> 78.1%. The "
        "charge-point decision and its neutralizations land as ONE entry "
        "(belief_cost_single_charge) or not at all."
    ),
}


# ---------------------------------------------------------------------------
# registry
# ---------------------------------------------------------------------------

#: Every repair id, and its inert control beside it. The pairing is the contract:
#: a repair with no control cannot be attributed.
REPAIR_PAIRS: tuple[tuple[str, str], ...] = (
    ("commission_broker_true", "commission_inert_control"),
    ("commission_broker_true_gated", "commission_inert_control"),
    ("swap_horizon_true", "swap_horizon_inert_control"),
    ("spread_input_truth", "spread_input_truth_inert_control"),
    ("cost_ruler_harmonize", "cost_ruler_inert_control"),
    ("belief_cost_single_charge", "belief_cost_inert_control"),
    ("belief_hash_term_removal", "belief_hash_inert_control"),
    ("belief_confidence_constant_retire", "belief_confidence_inert_control"),
    ("belief_ev_walked_contract", "belief_ev_walked_inert_control"),
    ("belief_fill_probability_deweight", "belief_fill_probability_inert_control"),
    ("candidate_breaker_transform", "candidate_breaker_inert_control"),
)

#: The R-BELIEF bundle in its required install order: the single-charge
#: bundle's charge census wraps evaluate_candidate_v4 INNER (installed first)
#: so it classifies the debate chain before the walked-contract repricer
#: (installed later, therefore OUTER) overwrites the row's belief fields.
BELIEF_BUNDLE: tuple[str, ...] = (
    "belief_cost_single_charge",
    "belief_hash_term_removal",
    "belief_confidence_constant_retire",
    "belief_ev_walked_contract",
    "belief_fill_probability_deweight",
)

#: Deduplicated: `commission_inert_control` is the control for BOTH commission
#: variants (same wrapper, same computation, zero charge), so it appears in two
#: pairs and must be installed once.
REPAIR_IDS: tuple[str, ...] = tuple(
    dict.fromkeys(
        [item for pair in REPAIR_PAIRS for item in pair]
        + [_ceiling_id(value) for value in COST_CEILING_CELLS]
        + [_replicate_id(n) for n in NEUTRAL_SEED_REPLICATE_CELLS]
    )
)

#: The compositions that are wrong rather than merely unusual. Refused by name.
INCOMPATIBLE_REPAIRS: tuple[tuple[str, str, str], ...] = (
    (
        "commission_broker_true_gated",
        "cost_ceiling_*",
        "both re-run pretrade_cost_refusal_reasons on the same packet builder, "
        "so the outer wrapper would gate a packet the inner one already gated "
        "and the receipt could not say which ceiling decided. Compose a ceiling "
        "cell with `commission_broker_true` (the accounting-only variant) so "
        "exactly one wrapper owns the gate.",
    ),
    (
        "neutral_seed_replicate_r1",
        "neutral_seed_replicate_r2",
        "two seed dials in one run cannot compose: exactly one neutral seed "
        "ranks the hard-eligible pool, so the second dial would either be "
        "silently inert or rebind the loop's sealed-check constant away from "
        "the seed the ranks actually used, and no receipt could name the "
        "arm's selection semantics. One replicate per arm; the apply() guard "
        "refuses the composition even when validation is bypassed.",
    ),
    (
        "spread_input_truth",
        "spread_input_truth_inert_control",
        "the live repair and its own inert control rebind the same symbol "
        "(_predecision_tick_for_cost); nested, the pool could not say which "
        "spread it was charged -- the control would either see already-"
        "repaired quotes (and prove nothing) or overwrite repaired quotes "
        "with frozen ones (and silently disarm the repair). The apply() "
        "guard refuses the composition even when validation is bypassed.",
    ),
    (
        "cost_ruler_harmonize",
        "cost_ruler_inert_control",
        "the live repair and its own inert control rebind the same symbol "
        "(broker_calibrated_replay_cost_packet); nested, the receipt could "
        "not say which ruler priced the pool. The apply() guard refuses the "
        "composition even when validation is bypassed.",
    ),
    (
        "cost_ruler_harmonize",
        "cost_ceiling_*",
        "both re-run pretrade_cost_refusal_reasons on the same packet "
        "builder, so a flat-override packet the ruler replaced would be "
        "re-gated a second time by the dial and the receipt could not say "
        "which ceiling decided. Sweep ceiling cells against the accounting "
        "stack (commission_broker_true + spread_input_truth), where exactly "
        "one wrapper owns the gate.",
    ),
    (
        "belief_cost_single_charge",
        "belief_cost_inert_control",
        "the live bundle and its own inert control rebind the same five "
        "symbols (context builder, debate, probability_thesis, "
        "evaluate_candidate_v4, scheduler config); nested, the pool could "
        "not say which belief system priced it -- the control would either "
        "wire 0.0 over a live wire or add back on top of an add-back. The "
        "apply() guards refuse the composition even when validation is "
        "bypassed.",
    ),
    (
        "belief_hash_term_removal",
        "belief_hash_inert_control",
        "the live repair and its own inert control rebind the same symbol "
        "(candidate_feature_signal); nested, the reconstruction proof would "
        "run against an already-de-hashed signal and refuse every row, "
        "silently disarming the repair. The apply() guard refuses the "
        "composition even when validation is bypassed.",
    ),
    (
        "belief_confidence_constant_retire",
        "belief_confidence_inert_control",
        "the live repair and its own inert control rebind the same symbol "
        "(_sum_scheduler_score_components); nested, the counterfactual "
        "stamps would overwrite each other and the receipt could not say "
        "whether the term was retired. The apply() guard refuses the "
        "composition even when validation is bypassed.",
    ),
    (
        "belief_ev_walked_contract",
        "belief_ev_walked_inert_control",
        "the live repair and its own inert control rebind the same symbol "
        "(evaluate_candidate_v4) with the same wrapper kind; nested, the "
        "control would observe already-repriced rows and stamp them as the "
        "frozen engine's. The apply() guard refuses the composition even "
        "when validation is bypassed.",
    ),
    (
        "belief_fill_probability_deweight",
        "belief_fill_probability_inert_control",
        "the live repair and its own inert control rebind the same two "
        "symbols (_sum_scheduler_score_components, _candidate_edge_score); "
        "nested, the receipt could not say which weight scored the pool. "
        "The apply() guards refuse the composition even when validation is "
        "bypassed.",
    ),
    (
        "candidate_breaker_transform",
        "candidate_breaker_inert_control",
        "the live hook and its own inert control rebind the same class "
        "method (V4DecisionCycleCore.generate_candidates); nested, the "
        "control would deep-copy already-transformed rows and stamp them as "
        "proof of inertness, or the transform would invert an already-"
        "inverted candidate. The receipt could not say which candidate book "
        "the arm ran.",
    ),
)

#: Repairs the commission named that have NO surface on the replay path. Kept as
#: data rather than prose so `--repairs` can refuse them with the reason instead
#: of failing on an unknown id.
REPAIRS_THAT_DO_NOT_APPLY: dict[str, str] = {
    "time_stop_contract": (
        "The B7.5 replay has no sleeve identity in its exit path: it never "
        "imports execution_packets and never reads SLEEVE_EXIT_PROFILES. Its "
        "exit is first-touch target/stop with a flat 120-minute wall-clock "
        "expiry (REPAIRED_PENDING_EXPIRY_MINUTES = 120, "
        "replay_acceleration_attempt5_typed_sparse_runner.py:116, applied at "
        ":16164 and :16745; expiry built at v4_timewarp:85864-85866). AQ's live "
        "repair moved a per-sleeve horizon from 96 to 7,680 M15 bars = 80 days; "
        "no B7.5 position can be held for 121 minutes. The one place that class "
        "of defect DOES bite here is swap pricing -- see swap_horizon_true."
    ),
    "spread_geometry_floor_at_generation": (
        "Not rebind-reachable, and the admission limit is already enforced. "
        "config/agent_config.yaml:715-716 declares max_spread_r 0.10 and "
        "max_total_cost_r 0.15; broker_net_cost_engine.pretrade_cost_refusal_"
        "reasons:718-728 and :772-776 enforce them and v4_timewarp:86204-86224 "
        "turns the refusal into risk_decision=reject with approved_risk_pct 0. "
        "The broad generator sees closed OHLC bars and never a tick "
        "(no 'spread' token anywhere in broader_origin_generators.py), so there "
        "is no generation-time site to inject a floor into without new plumbing. "
        "AY's ultimate_book/spread_geometry.py is imported only by run_book.py "
        "and book_engine.py -- a live-path artifact that does not reach replay. "
        "The cost-tail question is therefore answered as an analysis over the "
        "regenerated pool, not as an engine repair."
    ),
    "broker_clock": (
        "Not reachable on a SEALED window, and the reason is three independent "
        "fail-closed layers rather than an absence. (1) The replay path contains "
        "no clock code at all: `broker_clock|pytz|ZoneInfo|EET|America/New_York` "
        "over v4_timewarp, both B7.5 runners, the allocator, selector_v4, the "
        "prepared-day-pack module, the integrated typed source and wave4r "
        "microstructure returns one hit and it is a prose comment. Every "
        "timestamp is relabelled naive->UTC by "
        "`wave4r_replay_microstructure.parse_utc:130-142` "
        "(`parsed.replace(tzinfo=timezone.utc)`). (2) The typed cache's identity "
        "key includes `normalizer_code_root_sha256 = _file_sha256(...)` "
        "(`replay_acceleration_integrated_source.py:111-118`, `:237`), and a "
        "runtime rebind moves no file byte, so the key is unchanged and the "
        "cached partition is reused. (3) A cold rebuild fails closed anyway: "
        "`load_or_build_partition` compares the fresh rows digest against the "
        "BUNDLE's sealed `normalized_root_sha256` (`:345-349`). And the clock is "
        "already baked into the sealed prepared day packs, whose records stamp "
        "`decision_time_utc` and whose candidates carry kill_zone/session/"
        "utc_hour_bucket computed at pack-build time. A clock repair here is a "
        "RE-MATERIALISATION, not a rebind -- which is a different session. "
        "THE MEASUREMENT IS STILL A FINDING: the sealed January source is broker "
        "wall clock mislabelled as UTC, so the whole window is +2.0 h ahead of "
        "true UTC (54/54 weekly opens at Mon 00:00 across both US and EU DST "
        "transitions, which a true-UTC FX series cannot be; the exporter did "
        "`datetime.fromtimestamp(ts, tz=timezone.utc)` on a broker-wall-clock "
        "epoch and was repaired on 2026-07-26, three days AFTER the January "
        "bundle was sealed on 2026-07-23). Every hour-of-day statement about the "
        "January pool is shifted two hours."
    ),
}


def build_repairs(*, verify: bool = False) -> list[accel.Patch]:
    return [
        _make_commission_patch(live=True, regate=False),
        _make_commission_patch(live=True, regate=True),
        _make_commission_patch(live=False),
        _make_swap_horizon_patch(live=True),
        _make_swap_horizon_patch(live=False),
        _make_spread_truth_patch(live=True),
        _make_spread_truth_patch(live=False),
        _make_cost_ruler_patch(live=True),
        _make_cost_ruler_patch(live=False),
        _make_belief_cost_patch(live=True),
        _make_belief_cost_patch(live=False),
        _make_hash_removal_patch(live=True),
        _make_hash_removal_patch(live=False),
        _make_confidence_retire_patch(live=True),
        _make_confidence_retire_patch(live=False),
        _make_ev_walked_patch(live=True),
        _make_ev_walked_patch(live=False),
        _make_fill_deweight_patch(live=True),
        _make_fill_deweight_patch(live=False),
        _make_breaker_transform_patch(live=True),
        _make_breaker_transform_patch(live=False),
        *[_make_cost_ceiling_patch(value) for value in COST_CEILING_CELLS],
        *[
            _make_neutral_seed_replicate_patch(n)
            for n in NEUTRAL_SEED_REPLICATE_CELLS
        ],
    ]


def register_repairs(installer: Any, *, verify: bool = False) -> None:
    for patch in build_repairs(verify=verify):
        installer.register(patch)


def validate_repair_ids(ids: "list[str] | tuple[str, ...]") -> None:
    """Refuse an unknown, non-applicable, or incompatible repair id, with its reason."""

    requested = set(ids)
    for left, right, why in INCOMPATIBLE_REPAIRS:
        right_hit = (
            any(item.startswith(right[:-1]) for item in requested)
            if right.endswith("*")
            else right in requested
        )
        if left in requested and right_hit:
            raise RepairUnavailable(f"{left!r} and {right!r} cannot compose: {why}")
    for item in ids:
        if item in REPAIR_IDS:
            continue
        refused = REFUSED_REPAIR_FORMS.get(item)
        if refused:
            raise RepairUnavailable(f"repair form {item!r} is refused: {refused}")
        reason = REPAIRS_THAT_DO_NOT_APPLY.get(item)
        if reason:
            raise RepairUnavailable(
                f"repair {item!r} does not apply to the B7.5 replay path. {reason}"
            )
        raise RepairUnavailable(
            f"unknown repair {item!r}; available are {REPAIR_IDS}. Repairs that "
            f"were investigated and do NOT apply: {sorted(REPAIRS_THAT_DO_NOT_APPLY)}. "
            f"Repair forms refused by name: {sorted(REFUSED_REPAIR_FORMS)}"
        )


def resolve_repairs(spec: str | None) -> list[str]:
    """`None`/`none` -> no repair (the frozen economics); `all` -> both live."""

    if spec is None:
        return []
    text = spec.strip().lower()
    if text in {"none", ""}:
        return []
    if text == "all":
        # The FULL repaired stack: commission charged AND gated, plus the swap
        # horizon. `commission_broker_true` alone is the accounting-only variant
        # and would double-install the same wrapper, so it is excluded here.
        return ["commission_broker_true_gated", "swap_horizon_true"]
    if text == "accounting":
        return ["commission_broker_true", "swap_horizon_true"]
    if text == "cost_truth":
        # The R-COST-TRUTH stack (B5 C3 + C4-A), in the ORDER that makes the
        # ruler wrapper outermost: the installer applies list-order, wrappers
        # nest later-outside, and cost_ruler_harmonize's census must read the
        # ruler the pool actually gets -- after the commission wrapper has
        # priced and redecoded. spread_input_truth's position is free (its
        # rebind target is disjoint) and it is listed first for readability.
        return [
            "spread_input_truth",
            "commission_broker_true_gated",
            "swap_horizon_true",
            "cost_ruler_harmonize",
        ]
    if text == "belief":
        # The R-BELIEF bundle alone (spec section 3), in its required install
        # order (charge census inner, walked-contract repricer outer).
        return list(BELIEF_BUNDLE)
    if text == "belief_honesty":
        # T2 arm (ii) as ONE flag: the CJ-recipe cost repairs ride the
        # baseline recipe; this adds R-COST-TRUTH (arm (i)) plus the R-BELIEF
        # bundle. R-SCHEMA rides `--patches` (cuts), not `--repairs`.
        return resolve_repairs("cost_truth") + list(BELIEF_BUNDLE)
    if text.startswith("ceiling:"):
        # `ceiling:0.25` -> the repaired stack at a swept cost ceiling. The
        # accounting-only commission variant, because the dial owns the gate.
        value = float(text.split(":", 1)[1])
        return [
            "commission_broker_true",
            "swap_horizon_true",
            _ceiling_id(value),
        ]
    if text == "controls":
        return list(dict.fromkeys(control for _live, control in REPAIR_PAIRS))
    return list(
        dict.fromkeys(item.strip() for item in spec.split(",") if item.strip())
    )


def repair_manifest() -> dict[str, Any]:
    """What a receipt records about the repair surface, without running anything."""

    return {
        "schema": "gtos.train_engine.repair_manifest.v1",
        "repair_pairs": [list(pair) for pair in REPAIR_PAIRS],
        "do_not_apply": dict(REPAIRS_THAT_DO_NOT_APPLY),
        "refused_repair_forms": dict(REFUSED_REPAIR_FORMS),
        "belief_bundle": {
            "ids": list(BELIEF_BUNDLE),
            "charge_point": (
                "debate_live_style: cost_r + candidate_direction wired into "
                "the replay debate context (parity with "
                "build_probability_debate_context_from_runtime:1094-1096); "
                "downstream single-charge held by the probability_thesis "
                "add-back identity, censused per row (0x/1x/2x)"
            ),
            "p_gate_rebaseline": {
                "logit_shift": P_GATE_LOGIT_SHIFT,
                "derivation": (
                    "JAN_POOL_MEDIAN_COST_R (0.6166, C6-B committed walk "
                    "corpus) * DEBATE_COST_PENALTY_MULTIPLIER (0.7, "
                    "probability_debate_v4.py:753)"
                ),
                "gates": {
                    "dynamic_budget_package_min_probability": [
                        0.58, rebaselined_p_gate(0.58)
                    ],
                    SOURCE_BOUND_MIN_PROBABILITY_ATTR: [
                        0.70, rebaselined_p_gate(0.70)
                    ],
                    "selector_reduce_risk_numeric_disagreement_min_probability": [
                        0.85, rebaselined_p_gate(0.85)
                    ],
                    "selector_reduce_risk_new_entry_min_probability": [
                        0.80, rebaselined_p_gate(0.80)
                    ],
                },
            },
            "cell_table": {
                "artifact": str(BELIEF_CELL_TABLE),
                "sha256": BELIEF_CELL_TABLE_SHA256,
                "partition": "origin_family x cost_band(C1<0.10,C2<0.30,C3<1.00,C4) x route_session",
                "min_n": BELIEF_CELL_MIN_N,
                "shrinkage_prior_mass": BELIEF_SHRINKAGE_PRIOR_MASS,
                "fitted_on": "january_only_development_fitted_lane_evidence",
            },
            "expected_direction": (
                "STAND DOWN -- fewer trades, not more R (BELIEF-RECAL "
                "section 8, binding); the debate EV veto ex-ante fires on "
                "~42.8% of pool rows at the single charge point; any claim "
                "a belief repair alone produced a positive broad-V4 book is "
                "a red flag against the receipts"
            ),
        },
        "commission": {
            "artifact": str(BROKER_TRUE_COSTS_V1),
            "account": COMMISSION_ACCOUNT,
            "profile": str(COMMISSION_PROFILE),
            "formula": (
                "commission_r = commission_usd_per_lot(entry_price) / "
                "(sl_distance_price * usd_per_price_unit_per_lot)"
            ),
        },
        "cost_ceiling_dial": {
            "sealed_ceiling_r": SEALED_TOTAL_COST_CEILING_R,
            "cells": list(COST_CEILING_CELLS),
            "note": (
                "a SEARCH axis, not a repair: no correct value is being "
                "restored. Per-sleeve overrides are unreachable in replay "
                "because trade_params carry no source_event_details.sleeve."
            ),
        },
        "incompatible": [list(row) for row in INCOMPATIBLE_REPAIRS],
        "swap_horizon": {
            "sealed_bars": SEALED_SWAP_HORIZON_BARS,
            "true_bars": TRUE_SWAP_HORIZON_BARS,
            "minutes_per_bar": SWAP_MODEL_MINUTES_PER_BAR,
            "replay_max_hold_minutes": REPLAY_MAX_HOLD_MINUTES,
        },
        "spread_input_truth": {
            "artifact": str(SPREAD_MODEL_V1),
            "account": SPREAD_ACCOUNT,
            "band": SPREAD_BAND,
            "quote_source": REPAIRED_SPREAD_QUOTE_SOURCE,
            "replaced_quote_sources": list(SPREAD_REPLACED_QUOTE_SOURCES)
            + ["historical_ftmo_predecision_tick+floor_substitute"],
            "kept_quote_sources": list(SPREAD_KEPT_QUOTE_SOURCES),
            "formula": (
                "spread_r = spread_model.spread_price(symbol, 'FTMO', asof_utc, "
                "band='mid').spread_price / |entry_price - stop_loss|"
            ),
            "finding": (
                "B5 C3 (REFUTED, both lenses): 17/24 symbols carry a per-row "
                "config-constant spread (SPX500 10.0 = 16.7x tick truth, "
                "NAS100 50.0 = 28.6x), 3 more ride the admission floor table; "
                "only the 4 registered tick sources are measured"
            ),
            "ex_ante_expectation": (
                "Jan pool mean spread_r 0.564 -> ~0.157; untradeable "
                "73.9% -> ~61% (Feb 82.2% -> ~60%) at mean-truth; a "
                "~41.6%/31.8% genuinely spread-killed core remains"
            ),
            "era_note": (
                "anchors measured Jun-Jul 2026, applied to Jan/Feb 2026 "
                "within-era; era ratios RECORDED at the lane windows"
            ),
        },
        "cost_ruler_harmonize": {
            "finding": (
                "B5 C4-A: February's cost_r deviates from its component sum "
                "on 73.5% of rows, incl. flat 0.12 overrides on GER40/"
                "UKOIL_cash/USOIL_cash; January's matches on 27,658/27,658"
            ),
            "mechanism": (
                "build_pretrade_cost_packet emits total_cost_r=None unless "
                "spread exists AND commission is ready "
                "(broker_net_cost_engine.py:694-706); "
                "broker_calibrated_replay_cost_packet then substitutes the "
                "flat broker_replay_default_total_cost_r (0.12) at "
                "v4_timewarp:58929-58938"
            ),
            "enforcement": (
                "flat-override totals with a COMPLETE witnessed component set "
                "are rebuilt as the component sum and re-gated by the "
                "engine's own pretrade_cost_refusal_reasons; incomplete sets "
                "keep the frozen 0.12 visibly, counted, missing inputs "
                "stamped per row"
            ),
            "documented_remainder": (
                "removing the 0.12 fabrication at source is an engine-file "
                "edit (v4_timewarp:58930) outside the runtime-rebind mandate"
            ),
        },
        "neutral_seed_replicate_dial": {
            "sealed_protocol_seed_sha256": (
                SEALED_NEUTRAL_SELECTION_SEED_SHA256
            ),
            "derivation": NEUTRAL_SEED_REPLICATE_DERIVATION,
            "cells": {
                _replicate_id(n): neutral_seed_replicate_seed(n)
                for n in NEUTRAL_SEED_REPLICATE_CELLS
            },
            "note": (
                "a REPLICATE axis, not a repair: no correct value is being "
                "restored. One replicate per arm (r1 and r2 refuse to "
                "compose); composes with commission_broker_true_gated and "
                "swap_horizon_true. Both rebind sides carry the same variant "
                "seed so the factorial binding stays valid and every output "
                "declares the seed the ranks actually used."
            ),
        },
    }
