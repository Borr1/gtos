"""Scheduler and allocator expression decisions are one Choice each.

Each decision if that chooses which trade is expressed is its own question.
The two criteria are the two sides of that condition. The decision is the
option with the unique highest probability. A tie is not a decision. An
empty answer does not restore the old boolean. This module never calls
order_send and never writes an absent-mode label. Persist stays unset.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, MutableMapping, Sequence

CHALLENGE_NS = "operator"
CHALLENGE_LOGIN = 0
MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.scheduler_choices.v1"

_FORCE: bool | None = None
_ASK: Callable[..., dict[str, Any]] | None = None


def _pair(question_id: str, what: str, left: str, left_text: str, right: str, right_text: str) -> dict[str, Any]:
    return {
        "id": question_id,
        "instructions": (
            f"Scheduler and allocator question: {what} "
            f"Pick one option. {left} and {right} are the two sides of this condition. "
            f"The unique highest probability is the decision. "
            f"An empty answer or a tie does not restore the old boolean and does not express a trade from it. "
            f"Do not flatten an open ticket."
        ),
        "criteria": {left: left_text, right: right_text},
    }


QUESTIONS: dict[str, dict[str, Any]] = {
    "zero_trade_class": _pair(
        "sched_zero_trade_class",
        "whether this option is the zero-trade row.",
        "not_zero_trade",
        "This option is not the zero-trade row.",
        "is_zero_trade",
        "This option is the zero-trade row.",
    ),
    "runtime_eligibility": _pair(
        "sched_runtime_eligibility",
        "whether this option is runtime eligible.",
        "runtime_eligible",
        "This option is runtime eligible.",
        "not_runtime_eligible",
        "This option is not runtime eligible.",
    ),
    "min_trade_score": _pair(
        "sched_min_trade_score",
        "whether this option clears the minimum trade score.",
        "score_clears_min",
        "The hazard score clears the minimum trade score.",
        "score_below_min",
        "The hazard score is below the minimum trade score.",
    ),
    "executable_transfer": _pair(
        "alloc_executable_transfer",
        "whether this option's executable transfer is expressed.",
        "transfer_allowed",
        "Express this option's executable transfer.",
        "transfer_blocked",
        "Do not express this option's executable transfer.",
    ),
    "hazard_versus_zero": _pair(
        "alloc_hazard_versus_zero",
        "whether this option's hazard-adjusted score is above the zero-trade score.",
        "above_zero",
        "The hazard-adjusted score is above the zero-trade score.",
        "not_above_zero",
        "The hazard-adjusted score is not above the zero-trade score.",
    ),
    "hard_dominance": _pair(
        "alloc_hard_dominance",
        "which ordering expresses the window.",
        "hard_dominance_order",
        "Order by the hard-dominance comparator.",
        "legacy_order",
        "Order by the legacy scheduler key.",
    ),
    "eligible_pool": _pair(
        "alloc_eligible_pool",
        "whether the window expresses zero or a candidate.",
        "express_zero",
        "Express the zero trade.",
        "express_a_candidate",
        "Express a candidate from the pool.",
    ),
    "window_cardinality": _pair(
        "alloc_window_cardinality",
        "whether the window expresses one trade or several.",
        "one_trade",
        "Express one trade.",
        "several_trades",
        "Express more than one trade.",
    ),
    "leading_trade": _pair(
        "alloc_leading_trade",
        "whether this leading option is the trade expressed.",
        "express_leading",
        "Express this leading option.",
        "not_the_leading_trade",
        "Do not express this leading option.",
    ),
    "burst_guard": _pair(
        "alloc_burst_guard",
        "whether the burst condition expresses the primary option.",
        "express_primary",
        "Express this primary option.",
        "burst_blocks",
        "The burst condition withholds this option.",
    ),
    "loop_executable_transfer": _pair(
        "alloc_loop_executable_transfer",
        "whether this considered option's executable transfer is expressed.",
        "transfer_allowed",
        "Express this option's executable transfer.",
        "transfer_blocked",
        "Do not express this option's executable transfer.",
    ),
    "loop_hazard": _pair(
        "alloc_loop_hazard",
        "whether this considered option stays above the zero-trade score.",
        "above_zero",
        "The hazard-adjusted score is above the zero-trade score.",
        "not_above_zero",
        "The hazard-adjusted score is not above the zero-trade score.",
    ),
    "risk_class": _pair(
        "alloc_risk_class",
        "whether this option is new risk or a lifecycle action.",
        "new_risk",
        "This option is new risk.",
        "lifecycle_action",
        "This option is a lifecycle action.",
    ),
    "lifecycle_slot": _pair(
        "alloc_lifecycle_slot",
        "whether this lifecycle action is the trade expressed.",
        "express_lifecycle",
        "Express this lifecycle action.",
        "skip_lifecycle",
        "Do not express this lifecycle action.",
    ),
    "reduced_multi": _pair(
        "alloc_reduced_multi",
        "whether another reduced new entry is expressed.",
        "allow_another_reduced",
        "Express another reduced new entry.",
        "one_reduced_is_enough",
        "Do not express another reduced new entry.",
    ),
    "symbol_occupancy": _pair(
        "alloc_symbol_occupancy",
        "whether this symbol already has the expressed new position.",
        "symbol_is_free",
        "This symbol does not yet have the expressed new position.",
        "symbol_already_expressed",
        "This symbol already has the expressed new position.",
    ),
    "requested_risk": _pair(
        "alloc_requested_risk",
        "whether this option requests risk to express.",
        "risk_requested",
        "This option requests risk.",
        "no_risk_requested",
        "This option requests no risk.",
    ),
    "headroom_full": _pair(
        "alloc_headroom_full",
        "whether headroom expresses the full requested risk.",
        "full_risk",
        "Express the full requested risk.",
        "not_full",
        "Do not express the full requested risk.",
    ),
    "headroom_reduced": _pair(
        "alloc_headroom_reduced",
        "whether remaining headroom expresses a reduced risk.",
        "reduced_risk",
        "Express a reduced risk.",
        "no_headroom",
        "Do not express. There is no headroom.",
    ),
    "headroom_policy": _pair(
        "alloc_headroom_policy",
        "whether a reduced new entry is expressed into window headroom.",
        "reduce_to_headroom",
        "Express the reduced new entry into headroom.",
        "leave_unreduced",
        "Do not express a reduced new entry.",
    ),
    "loop_burst": _pair(
        "alloc_loop_burst",
        "whether the burst condition expresses this option.",
        "express_this",
        "Express this option.",
        "burst_blocks",
        "The burst condition withholds this option.",
    ),
    "selected_zero": _pair(
        "sched_selected_zero",
        "whether the selected action expresses zero or this trade.",
        "express_this_trade",
        "Express this trade.",
        "express_zero",
        "Express the zero trade.",
    ),
    "selected_identity": _pair(
        "sched_selected_identity",
        "whether this candidate is the trade the allocator expressed.",
        "this_candidate",
        "This candidate is the expressed trade.",
        "another_candidate",
        "Another candidate is the expressed trade.",
    ),
    "runtime_effect": _pair(
        "sched_runtime_effect",
        "whether the expressed trade has runtime effect now.",
        "runtime_effect",
        "The expressed trade has runtime effect now.",
        "no_runtime_effect",
        "The expressed trade has no runtime effect now.",
    ),
}

_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}


def set_ask(ask: Callable[..., dict[str, Any]] | None) -> None:
    global _ASK
    _ASK = ask


def set_force(force: bool | None) -> None:
    global _FORCE
    _FORCE = force


def challenge_scheduler() -> bool:
    """True on the Challenge writer, or when a test forces the Choice path."""

    if _FORCE is not None:
        return bool(_FORCE)
    argv = [str(arg) for arg in sys.argv]
    for index, arg in enumerate(argv):
        if arg == "--namespace" and index + 1 < len(argv) and argv[index + 1] == CHALLENGE_NS:
            return True
        if arg == f"--namespace={CHALLENGE_NS}":
            return True
    return os.environ.get("GTOS_BOOK_NAMESPACE") == CHALLENGE_NS


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def record_path() -> Path:
    override = (os.environ.get("GTOS_SCHEDULER_CHOICES_RECORD") or "").strip()
    if override:
        return Path(override)
    return (
        _repo_root()
        / "pipeline_state"
        / "ultimate_book"
        / CHALLENGE_NS
        / "judgment"
        / "scheduler_choices.jsonl"
    )


def armed_path() -> Path:
    return record_path().with_name("scheduler_choices_armed.json")


def clear_cache() -> None:
    _CACHE.clear()


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _append(path: Path, row: Mapping[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_jsonable(dict(row)), sort_keys=True) + "\n")
    except OSError:
        return


def write_armed_stamp() -> None:
    try:
        payload = {
            "schema": SCHEMA,
            "logged_at_utc": _now(),
            "ns": CHALLENGE_NS,
            "armed": True,
            "questions": sorted(QUESTIONS),
            "pid": os.getpid(),
            "persist": None,
            "agent_order_send": False,
            "activation_token": "stays",
            "model": MODEL,
            "flatten": False,
        }
        path = armed_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    except OSError:
        return


def _base(question: str) -> dict[str, Any]:
    spec = QUESTIONS[question]
    return {
        "schema": SCHEMA,
        "logged_at_utc": _now(),
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "question": question,
        "question_id": spec["id"],
        "choice": None,
        "probability": None,
        "probabilities": {},
        "probability_source": None,
        "decision_emitted": False,
        "model": MODEL,
        "persist": None,
        "persist_weight": None,
        "agent_order_send": False,
        "friends_copy_result": True,
        "extra_pass": False,
        "activation_token": "stays",
        "restored_boolean": False,
        "error": None,
    }


def choose(
    question: str,
    *,
    symbol: Any = None,
    reason: str = "",
    proposed: Any = None,
    facts: Mapping[str, Any] | None = None,
    ask: Callable[..., dict[str, Any]] | None = None,
    use_cache: bool = False,
    record: bool = True,
    record_to: Path | None = None,
) -> dict[str, Any]:
    """Ask one scheduler or allocator Choice. Never raises. Never sends."""

    if question not in QUESTIONS:
        row = _base("eligible_pool")
        row["question"] = question
        row["question_id"] = None
        row["error"] = "unknown_question"
        row["decision_emitted"] = False
        return row
    spec = QUESTIONS[question]
    options = tuple(spec["criteria"])
    row = _base(question)
    row["symbol"] = symbol
    row["reason"] = reason or question
    row["proposed"] = proposed
    key = (
        question,
        str(reason),
        str(proposed),
        str(symbol),
        json.dumps(_jsonable(dict(facts or {})), sort_keys=True, separators=(",", ":")),
    )
    if use_cache:
        hit = _CACHE.get(key)
        if hit is not None:
            cached = dict(hit)
            cached["logged_at_utc"] = row["logged_at_utc"]
            cached["cache"] = True
            return cached
    state = {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "question": question,
        "symbol": symbol,
        "reason": reason or question,
        "proposed": proposed,
        "persist": None,
        "model": MODEL,
        "facts": dict(facts or {}),
    }
    try:
        caller = ask if ask is not None else _ASK
        if caller is None:
            from .rung_choice import ask_choice

            caller = ask_choice
        hop = caller(
            state,
            question_id=spec["id"],
            instructions=spec["instructions"],
            criteria=spec["criteria"],
        ) or {}
    except Exception as exc:  # noqa: BLE001 — a Choice must not raise into the writer
        hop = {"error": type(exc).__name__, "decision_emitted": False}
    if not isinstance(hop, dict):
        hop = {"error": "ask_not_a_dict", "decision_emitted": False}
    row["choice"] = hop.get("choice")
    row["probability"] = hop.get("probability")
    probs = hop.get("probabilities") if isinstance(hop.get("probabilities"), dict) else {}
    row["probabilities"] = {
        str(name): value for name, value in probs.items() if str(name) in options
    }
    row["probability_source"] = hop.get("probability_source")
    row["decision_emitted"] = bool(hop.get("decision_emitted")) and row["choice"] in options
    row["error"] = hop.get("error")
    if not row["decision_emitted"]:
        row["choice"] = None
    if hop.get("model"):
        row["model"] = hop.get("model")
    if use_cache:
        if row["decision_emitted"]:
            _CACHE[key] = dict(row)
    if record:
        _append(record_to or record_path(), row)
    return row


def _side(
    question: str,
    *,
    facts: Mapping[str, Any],
    symbol: Any = None,
    proposed: Any = None,
    ask: Callable[..., dict[str, Any]] | None = None,
) -> str | None:
    row = choose(
        question,
        symbol=symbol,
        reason=question,
        proposed=proposed,
        facts=facts,
        ask=ask,
        use_cache=False,
    )
    if not row.get("decision_emitted"):
        return None
    choice = row.get("choice")
    return str(choice) if choice else None


def _wins(question: str, side: str, facts: Mapping[str, Any], **kwargs: Any) -> bool:
    return _side(question, facts=facts, **kwargs) == side


def _option_facts(option: Any, extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    facts = {
        "option_id": getattr(option, "option_id", None),
        "candidate_id": getattr(option, "candidate_id", None),
        "action_class": getattr(option, "action_class", None),
        "symbol": getattr(option, "symbol", None),
        "side": getattr(option, "side", None),
        "score": getattr(option, "score", None),
        "requested_risk_pct": getattr(option, "requested_risk_pct", None),
        "approved_risk_pct": getattr(option, "approved_risk_pct", None),
    }
    if extra:
        facts.update(dict(extra))
    return facts


def _alloc():
    import src.research.moonshot_scheduler_v4_best_trade_allocator as alloc

    return alloc


def _withheld(zero: Any) -> Any:
    from dataclasses import replace

    return replace(
        zero,
        reason="scheduler_choice_no_decision",
        decision_status="choice_no_decision",
        approved_risk_pct=0.0,
        risk_delta_pct=0.0,
    )


def eligible_by_choice(
    ordered: Sequence[Any],
    config: Any,
    *,
    ask: Callable[..., dict[str, Any]] | None = None,
) -> list[Any]:
    """Keep an option only when each eligibility side uniquely wins."""

    alloc = _alloc()
    kept: list[Any] = []
    minimum = getattr(config, "min_trade_score", None)
    for option in ordered:
        try:
            hazard = alloc._option_hazard_adjusted_executable_quality_score(option)
        except Exception:
            hazard = None
        try:
            runtime_eligible = bool(option.runtime_eligible)
        except Exception:
            runtime_eligible = None
        facts = _option_facts(
            option,
            {
                "runtime_eligible": runtime_eligible,
                "hazard_score": hazard,
                "min_trade_score": minimum,
            },
        )
        symbol = getattr(option, "symbol", None)
        proposed = getattr(option, "option_id", None)
        if not _wins(
            "zero_trade_class",
            "not_zero_trade",
            facts,
            symbol=symbol,
            proposed=proposed,
            ask=ask,
        ):
            continue
        if not _wins(
            "runtime_eligibility",
            "runtime_eligible",
            facts,
            symbol=symbol,
            proposed=proposed,
            ask=ask,
        ):
            continue
        if not _wins(
            "min_trade_score",
            "score_clears_min",
            facts,
            symbol=symbol,
            proposed=proposed,
            ask=ask,
        ):
            continue
        kept.append(option)
    return kept


def expression_gate(
    *,
    selected_action: str,
    selected_candidate_id: str,
    candidate_id: str,
    runtime_effect_now: bool,
    symbol: str,
    ask: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Express this candidate only when each gate's express side uniquely wins."""

    facts = {
        "selected_action": selected_action,
        "selected_candidate_id": selected_candidate_id,
        "candidate_id": candidate_id,
        "runtime_effect_now": bool(runtime_effect_now),
        "symbol": symbol,
    }
    zero_side = _side(
        "selected_zero",
        facts=facts,
        symbol=symbol,
        proposed=candidate_id,
        ask=ask,
    )
    if zero_side is None:
        return {
            "expressed": False,
            "reason": "scheduler_choice_no_decision",
            "question": "selected_zero",
            "restored_boolean": False,
        }
    if zero_side == "express_zero":
        return {
            "expressed": False,
            "reason": "scheduler_v4_selected_zero_trade",
            "question": "selected_zero",
            "restored_boolean": False,
        }
    identity = _side(
        "selected_identity",
        facts=facts,
        symbol=symbol,
        proposed=candidate_id,
        ask=ask,
    )
    if identity is None:
        return {
            "expressed": False,
            "reason": "scheduler_choice_no_decision",
            "question": "selected_identity",
            "restored_boolean": False,
        }
    if identity == "another_candidate":
        return {
            "expressed": False,
            "reason": "scheduler_v4_candidate_not_selected",
            "question": "selected_identity",
            "restored_boolean": False,
        }
    effect = _side(
        "runtime_effect",
        facts=facts,
        symbol=symbol,
        proposed=candidate_id,
        ask=ask,
    )
    if effect is None:
        return {
            "expressed": False,
            "reason": "scheduler_choice_no_decision",
            "question": "runtime_effect",
            "restored_boolean": False,
        }
    if effect == "no_runtime_effect":
        return {
            "expressed": False,
            "reason": "scheduler_v4_selected_action_not_runtime_eligible",
            "question": "runtime_effect",
            "restored_boolean": False,
        }
    if effect == "runtime_effect":
        return {
            "expressed": True,
            "reason": None,
            "question": "runtime_effect",
            "restored_boolean": False,
        }
    return {
        "expressed": False,
        "reason": "scheduler_choice_no_decision",
        "question": "runtime_effect",
        "restored_boolean": False,
    }


def select_expressed(
    *,
    eligible_non_zero: Sequence[Any],
    zero: Any,
    snapshot: Any,
    config: Any,
    evaluated_options: MutableMapping[str, Any] | None = None,
    ask: Callable[..., dict[str, Any]] | None = None,
) -> list[Any]:
    """Choose the expressed trades from Choice sides. Never restore a boolean."""

    from dataclasses import replace

    alloc = _alloc()
    pool: list[Any] = []
    for option in eligible_non_zero:
        facts = _option_facts(option)
        symbol = getattr(option, "symbol", None)
        proposed = getattr(option, "option_id", None)
        if not _wins(
            "executable_transfer",
            "transfer_allowed",
            facts,
            symbol=symbol,
            proposed=proposed,
            ask=ask,
        ):
            continue
        if not _wins(
            "hazard_versus_zero",
            "above_zero",
            facts,
            symbol=symbol,
            proposed=proposed,
            ask=ask,
        ):
            continue
        pool.append(option)

    order = _side(
        "hard_dominance",
        facts={
            "hard_dominance_enabled": bool(
                getattr(config, "same_window_executable_comparator_hard_dominance_enabled", False)
            )
        },
        ask=ask,
    )
    if order == "hard_dominance_order":
        pool = sorted(
            pool,
            key=lambda option: alloc._scheduler_option_selection_sort_key(option, config),
            reverse=True,
        )
    elif order == "legacy_order":
        pool = sorted(
            pool,
            key=lambda option: alloc._scheduler_option_sort_key(option),
            reverse=True,
        )
    else:
        return [_withheld(zero)]

    pool_side = _side(
        "eligible_pool",
        facts={"n_eligible": len(pool)},
        ask=ask,
    )
    if pool_side == "express_zero":
        return [zero]
    if pool_side != "express_a_candidate" or not pool:
        return [_withheld(zero)]

    cardinality = _side(
        "window_cardinality",
        facts={
            "allow_multiple_new_positions_per_window": bool(
                getattr(config, "allow_multiple_new_positions_per_window", False)
            ),
            "n_eligible": len(pool),
        },
        ask=ask,
    )
    if cardinality == "one_trade":
        remaining = list(pool)
        while remaining:
            leading = remaining.pop(0)
            lead = _side(
                "leading_trade",
                facts=_option_facts(leading),
                symbol=getattr(leading, "symbol", None),
                proposed=getattr(leading, "option_id", None),
                ask=ask,
            )
            if lead is None:
                return [_withheld(zero)]
            if lead != "express_leading":
                continue
            try:
                leading, _burst_key, burst_blocked = alloc._transactional_same_decision_cluster_burst_guard(
                    leading,
                    config,
                    {},
                )
            except Exception:
                burst_blocked = None
            if evaluated_options is not None:
                evaluated_options[leading.option_id] = leading
            burst = _side(
                "burst_guard",
                facts=_option_facts(leading, {"burst_blocked_fact": burst_blocked}),
                symbol=getattr(leading, "symbol", None),
                proposed=getattr(leading, "option_id", None),
                ask=ask,
            )
            if burst == "express_primary":
                return [leading]
            if burst == "burst_blocks":
                return [zero]
            return [_withheld(zero)]
        return [_withheld(zero)]
    if cardinality != "several_trades":
        return [_withheld(zero)]

    selected: list[Any] = []
    allocated_portfolio_pct = 0.0
    allocated_cluster_pct: dict[str, float] = {}
    allocated_new_position_symbols: set[str] = set()
    selected_package_reduced_new_entries = 0
    selected_cluster_side_counts: dict[tuple[str, str], int] = {}
    released_pending_ids: set[str] = set()
    remaining_options = list(pool)
    while remaining_options:
        option = remaining_options.pop(0)
        facts = _option_facts(option)
        symbol_raw = getattr(option, "symbol", None)
        proposed = getattr(option, "option_id", None)
        if not _wins(
            "loop_executable_transfer",
            "transfer_allowed",
            facts,
            symbol=symbol_raw,
            proposed=proposed,
            ask=ask,
        ):
            continue
        if not _wins(
            "loop_hazard",
            "above_zero",
            facts,
            symbol=symbol_raw,
            proposed=proposed,
            ask=ask,
        ):
            continue
        risk_class = _side(
            "risk_class",
            facts=facts,
            symbol=symbol_raw,
            proposed=proposed,
            ask=ask,
        )
        if risk_class is None:
            continue
        if risk_class == "lifecycle_action":
            slot = _side(
                "lifecycle_slot",
                facts=_option_facts(option, {"slot_open": not selected}),
                symbol=symbol_raw,
                proposed=proposed,
                ask=ask,
            )
            if slot == "express_lifecycle":
                selected.append(option)
            continue
        if risk_class != "new_risk":
            continue
        symbol = (option.symbol or "").strip().upper()
        try:
            package_reduced_new_entry = bool(alloc._option_is_package_reduced_new_entry(option))
            multi_allowed = bool(
                alloc._option_package_reduced_new_entry_multi_select_allowed(option, config)
            )
        except Exception:
            package_reduced_new_entry = False
            multi_allowed = None
        reduced_side = _side(
            "reduced_multi",
            facts=_option_facts(
                option,
                {
                    "package_reduced_new_entry": package_reduced_new_entry,
                    "selected_package_reduced_new_entries": selected_package_reduced_new_entries,
                    "multi_select_fact": multi_allowed,
                },
            ),
            symbol=symbol_raw,
            proposed=proposed,
            ask=ask,
        )
        if reduced_side != "allow_another_reduced":
            continue
        occupancy = _side(
            "symbol_occupancy",
            facts=_option_facts(
                option,
                {"symbol_already_in_window": bool(symbol and symbol in allocated_new_position_symbols)},
            ),
            symbol=symbol_raw,
            proposed=proposed,
            ask=ask,
        )
        if occupancy != "symbol_is_free":
            continue
        requested = max(
            0.0,
            option.approved_risk_pct
            if option.approved_risk_pct is not None
            else option.requested_risk_pct,
        )
        requested_side = _side(
            "requested_risk",
            facts=_option_facts(option, {"requested": requested}),
            symbol=symbol_raw,
            proposed=proposed,
            ask=ask,
        )
        if requested_side != "risk_requested":
            continue
        try:
            cluster = alloc.cluster_key(option.symbol or "")
            replacement_portfolio_release, replacement_cluster_release, replacement_ids = (
                alloc._unused_pending_release(
                    option,
                    cluster=cluster,
                    used_pending_ids=released_pending_ids,
                )
            )
            pending_replacement = alloc._pending_replacement_from_option(option)
        except Exception:
            continue
        current_total = snapshot.total_reserved_risk_pct + allocated_portfolio_pct
        cluster_before = snapshot.cluster_risk_pct.get(cluster, 0.0) + allocated_cluster_pct.get(
            cluster,
            0.0,
        )
        effective_total = max(0.0, current_total - replacement_portfolio_release)
        effective_cluster_before = max(0.0, cluster_before - replacement_cluster_release)
        max_allowed = max(
            0.0,
            min(
                config.portfolio_ceiling_pct - effective_total,
                config.correlation_cluster_ceiling_pct - effective_cluster_before,
            ),
        )
        full_side = _side(
            "headroom_full",
            facts=_option_facts(
                option,
                {"max_allowed": max_allowed, "requested": requested},
            ),
            symbol=symbol_raw,
            proposed=proposed,
            ask=ask,
        )
        if full_side == "full_risk":
            adjusted = option
            approved = requested
        elif full_side == "not_full":
            reduced_side = _side(
                "headroom_reduced",
                facts=_option_facts(
                    option,
                    {
                        "max_allowed": max_allowed,
                        "min_reduced_risk_pct": config.min_reduced_risk_pct,
                    },
                ),
                symbol=symbol_raw,
                proposed=proposed,
                ask=ask,
            )
            if reduced_side != "reduced_risk":
                continue
            replacement_active = bool(replacement_ids) or bool(
                pending_replacement.get("runtime_replacement_applied")
            )
            policy = _side(
                "headroom_policy",
                facts=_option_facts(
                    option,
                    {
                        "allow_window_headroom_reduced_new_entries": bool(
                            config.allow_window_headroom_reduced_new_entries
                        ),
                        "replacement_active": replacement_active,
                    },
                ),
                symbol=symbol_raw,
                proposed=proposed,
                ask=ask,
            )
            if policy != "reduce_to_headroom":
                continue
            approved = max_allowed
            adjusted = replace(
                option,
                approved_risk_pct=approved,
                risk_delta_pct=approved,
                decision_status=(
                    "candidate_admitted_reduced_risk_after_pending_replacement"
                    if replacement_active
                    else "candidate_admitted_reduced_risk"
                ),
                reason=(
                    "risk_recovered_by_replacing_dominated_pending"
                    if replacement_active
                    else "risk_reduced_to_window_headroom"
                ),
                score=option.score - 0.08
                if option.reason != "risk_reduced_to_window_headroom"
                else option.score,
            )
        else:
            continue
        try:
            adjusted, burst_key, burst_blocked = alloc._transactional_same_decision_cluster_burst_guard(
                adjusted,
                config,
                selected_cluster_side_counts,
            )
        except Exception:
            burst_key = None
            burst_blocked = None
        if evaluated_options is not None:
            evaluated_options[adjusted.option_id] = adjusted
        burst = _side(
            "loop_burst",
            facts=_option_facts(adjusted, {"burst_blocked_fact": burst_blocked}),
            symbol=symbol_raw,
            proposed=getattr(adjusted, "option_id", None),
            ask=ask,
        )
        if burst != "express_this":
            continue
        selected.append(adjusted)
        if burst_key is not None:
            selected_cluster_side_counts[burst_key] = (
                selected_cluster_side_counts.get(burst_key, 0) + 1
            )
        if package_reduced_new_entry:
            selected_package_reduced_new_entries += 1
        released_pending_ids.update(replacement_ids)
        if symbol and adjusted.action_class == "new_position":
            allocated_new_position_symbols.add(symbol)
        allocated_portfolio_pct += approved
        allocated_cluster_pct[cluster] = allocated_cluster_pct.get(cluster, 0.0) + approved
    if selected:
        return selected
    return [_withheld(zero)]
