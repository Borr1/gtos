"""Read-only all-instrument data inventory.

Maps every symbol this tree can name against the bars on this clone.
Never places, remints, flattens, or applies size. Never invents a news
protocol. Does not load the selector module or the timewarp loop.

Each symbol, and the inventory itself, asks once through
``jev_client.evaluate`` (model ``jev-1.13.0``, ``merge_sleeve=False``,
POST https://api.typesafe.ai/v1/systemone). The role, cluster, probe
sleeve, side, origin, clock, admit contract, priority, gap and pull
nouls, and the entry, stop, distance, spread, threshold, loop bound,
and parameter are that Noul, Choice, or Score. Prior outcomes ride on
the ask and the return is stored for the next ask. An empty answer, a
tie, or an error leaves that field unset. A floor and a baseline are
not a question. This module does not send.
"""

from __future__ import annotations

import ast
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.data_inventory.v0"
ACCOUNT_LOGIN = 0
ACCOUNT_NS = "operator"
REPO_ROOT = Path(__file__).resolve().parents[2]

LOCK = {
    "never_place": True,
    "never_remint": True,
    "never_flatten": True,
    "never_apply_size": True,
    "never_invent_news_protocol": True,
    "never_import_selector_v4": True,
    "never_import_v4_timewarp": True,
}

MARKDOWN_COLUMNS = (
    "symbol",
    "bars present",
    "state assembled",
    "scored live",
    "gaps",
    "next pull",
)

# Named menus. Membership is a fact. The role and the pull are the return.
VPS_NAMED_PEER_PULL = ("EURUSD", "GBPUSD", "USDJPY", "US30", "XAUUSD")
CHAIR_CROSS_PULL = ("GBPJPY", "EURGBP")
_NAMED_PRIMARY = "XAUUSD"
_OPTIONAL_RISK_PEER = frozenset({"ETHUSD"})
_SLEEVE_ORDER = (
    "vss_fxcross_london_up_low",
    "kz_london_cry",
    "mx_us30",
    "dsp_two_bar_t",
)
_ROLE_ORDER = (
    "primary_xau",
    "multi_priority",
    "multi_optional",
    "chair_landed",
    "occupancy_cluster",
    "gtos_only",
)
_CLUSTER_ORDER = ("metals", "fx_major", "index", "crypto", "none")
_SIDE_ORDER = ("long", "short")
_ORIGIN_ORDER = ("f5_challenge", "other_origin")
_CLOCK_ORDER = ("as_of_open_study", "clock_now")
_PRIORITY_ORDER = (
    "0_lock",
    "2_missing_priority",
    "3_refresh_landed",
    "4_optional",
    "5_do_not_trade",
)
_ADMIT_ORDER = ("m15_h4_d1_optional", "m15_h4_only", "withhold")
_NOUL_ORDER = ("true", "false")
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_LIMIT_KEYS = frozenset(
    {
        "floor",
        "baseline",
        "day_start_baseline",
        "static_floor",
        "pass_line",
        "flatten_floor_usd",
        "daily_loss_pct",
        "floor_room",
        "to_pass",
    }
)
_BANNED_TEXT = (
    "90000",
    "90,000",
    "90_000",
    "90k",
    "90K",
    "110000",
    "110,000",
    "110_000",
    "110k",
    "110K",
)
_SECRET_PARTS = ("api_key", "authorization", "password", "secret")
_ALLOWED_TYPES = frozenset({"noul", "choice", "score"})


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    if token in _LIMIT_KEYS:
        return True
    return "floor" in token or "baseline" in token


def _secret_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    return any(part in token for part in _SECRET_PARTS)


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    return cleaned


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar tokens before an ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name) or _secret_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, (list, tuple)):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        return _scrub_text(value)
    return value


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _unique(probs: Mapping[str, Any] | None, order: Sequence[str] | None) -> str | None:
    """Unique highest probability. A missing probability is not zero."""

    if not isinstance(probs, Mapping) or not probs:
        return None
    names = tuple(order) if order else tuple(str(name) for name in probs)
    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    for name in names:
        if name not in probs:
            continue
        raw = probs.get(name)
        if raw is None or isinstance(raw, bool):
            continue
        try:
            p = float(raw)
        except (TypeError, ValueError):
            continue
        if p != p:
            continue
        seen = True
        if best_p is None or p > best_p + 1e-12:
            best = str(name)
            best_p = p
            tied = False
        elif abs(p - best_p) <= 1e-12:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _choice(block: Any, order: Sequence[str]) -> str | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    probs = block.get("probabilities")
    if not isinstance(probs, Mapping):
        return None
    menu = tuple(str(name) for name in order)
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(probs, menu)
    except Exception:
        picked = None
    if picked not in menu:
        picked = _unique(probs, menu)
    if picked not in menu:
        return None
    return str(picked)


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "noul" in block and block.get("noul") is not None:
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked = _choice(block, _NOUL_ORDER)
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> float | None:
    """The Score that came back. It is not snapped to a level."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        if block.get("score") is None:
            return None
        return _finite(block.get("score"))


def _pull(block: Any, kind: str, order: Sequence[str] | None) -> Any:
    if kind == "noul":
        return _noul(block)
    if kind == "choice":
        return _choice(block, order or ())
    return _score(block)


def _why(block: Any, value: Any, order: Sequence[str] | None, receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if isinstance(block, Mapping) and block.get("error"):
        return str(block.get("error"))
    probs = block.get("probabilities") if isinstance(block, Mapping) else None
    menu = tuple(order) if order else None
    if isinstance(probs, Mapping) and probs and _unique(probs, menu) is None and _choice(block, menu or ()) is None:
        return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
    found: list[float] = []
    for key, value in dict(facts or {}).items():
        if _limit_key(str(key)) or _secret_key(str(key)):
            continue
        number = _finite(value)
        if number is not None:
            found.append(number)
    if not found:
        return list(_BETWEEN)
    return [format(number, ".10g") for number in sorted(set(found))]


def _choice_question(qid: str, text: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    cleaned = {str(key): _scrub_text(val) for key, val in criteria.items()}
    body: dict[str, Any] = {"type": "choice", "instructions": instructions, "criteria": cleaned}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, cleaned)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = {key: val for key, val in block.items() if not _limit_key(str(key))}
            shaped["type"] = "choice"
            shaped["instructions"] = instructions
            shaped["criteria"] = cleaned
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _score_question(qid: str, text: str, levels: Sequence[str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    criteria = [str(item) for item in levels] if levels else list(_BETWEEN)
    body: dict[str, Any] = {"type": "score", "instructions": instructions, "criteria": criteria}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = {key: val for key, val in block.items() if not _limit_key(str(key))}
            shaped["type"] = "score"
            shaped["instructions"] = instructions
            shaped["criteria"] = list(criteria)
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _noul_question(qid: str, text: str, yes: str, no: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(text),
            "criteria": {"true": _scrub_text(yes), "false": _scrub_text(no)},
        }
    }


def _score_text(noun: str) -> str:
    return (
        f"The score you return is the {noun} for this state. "
        "It may sit between the levels. "
        "An empty score leaves it unset. "
        "Do not send an order."
    )


def _kept_questions(questions: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, block in dict(questions).items():
        name = str(key)
        if _limit_key(name) or _secret_key(name):
            continue
        if not isinstance(block, dict) or block.get("type") not in _ALLOWED_TYPES:
            continue
        out[name] = block
    return out


def _sleeve_menu(extra: Any) -> tuple[str, ...]:
    names: list[str] = list(_SLEEVE_ORDER)
    if isinstance(extra, (list, tuple, set, frozenset)):
        for item in extra:
            text = str(item or "").strip()
            if text and text not in names:
                names.append(text)
    return tuple(names)


def _symbol_spec(sleeves: tuple[str, ...]) -> tuple[tuple[str, str, str, tuple[str, ...] | None], ...]:
    return (
        ("role", "choice", "inv_role", _ROLE_ORDER),
        ("cluster", "choice", "inv_cluster", _CLUSTER_ORDER),
        ("probe_sleeve", "choice", "inv_probe_sleeve", sleeves),
        ("side", "choice", "inv_side", _SIDE_ORDER),
        ("origin", "choice", "inv_origin", _ORIGIN_ORDER),
        ("clock", "choice", "inv_clock", _CLOCK_ORDER),
        ("priority", "choice", "inv_priority", _PRIORITY_ORDER),
        ("admit_contract", "choice", "inv_admit_contract", _ADMIT_ORDER),
        ("entry", "score", "inv_entry", None),
        ("stop", "score", "inv_stop", None),
        ("stop_dist", "score", "inv_stop_dist", None),
        ("spread_r", "score", "inv_spread_r", None),
        ("threshold", "score", "inv_threshold", None),
        ("loop_bound", "score", "inv_loop", None),
        ("parameter", "score", "inv_parameter", None),
        ("admit_sit", "noul", "inv_admit_sit", _NOUL_ORDER),
        ("admit_now", "noul", "inv_admit_now", _NOUL_ORDER),
        ("hard_off", "noul", "inv_hard_off", _NOUL_ORDER),
        ("do_not_pull", "noul", "inv_do_not_pull", _NOUL_ORDER),
        ("optional_risk_peer", "noul", "inv_optional_risk_peer", _NOUL_ORDER),
        ("occupancy_peer", "noul", "inv_occupancy_peer", _NOUL_ORDER),
        ("april_wear", "noul", "inv_april_wear", _NOUL_ORDER),
        ("parent_shadow", "noul", "inv_parent_shadow", _NOUL_ORDER),
        ("m15_stale", "noul", "inv_m15_stale", _NOUL_ORDER),
        ("insufficient_sit", "noul", "inv_insufficient_sit", _NOUL_ORDER),
        ("d1_missing", "noul", "inv_d1_missing", _NOUL_ORDER),
        ("m15_h4_missing", "noul", "inv_m15_h4_missing", _NOUL_ORDER),
        ("shadow_sufficient", "noul", "inv_shadow_sufficient", _NOUL_ORDER),
        ("us30_surface_off", "noul", "inv_us30_surface_off", _NOUL_ORDER),
        ("component_exists", "noul", "inv_component", _NOUL_ORDER),
    )


def _book_spec() -> tuple[tuple[str, str, str, tuple[str, ...] | None], ...]:
    return (
        ("april_lock", "noul", "inv_book_april_lock", _NOUL_ORDER),
        ("april_priority", "choice", "inv_book_april_priority", _PRIORITY_ORDER),
        ("threshold", "score", "inv_book_threshold", None),
        ("loop_bound", "score", "inv_book_loop", None),
        ("parameter", "score", "inv_book_parameter", None),
        ("component_exists", "noul", "inv_book_component", _NOUL_ORDER),
    )


def _role_criteria() -> dict[str, str]:
    return {
        "primary_xau": "This symbol is the primary gold name on this inventory.",
        "multi_priority": "This symbol is a priority multi-instrument name.",
        "multi_optional": "This symbol is an optional multi-instrument name.",
        "chair_landed": "This symbol is a chair-landed cross on this inventory.",
        "occupancy_cluster": "This symbol is an occupancy-cluster name.",
        "gtos_only": "This symbol is only on the code surface.",
    }


def _cluster_criteria() -> dict[str, str]:
    return {
        "metals": "This symbol is in the metals cluster.",
        "fx_major": "This symbol is in the fx major cluster.",
        "index": "This symbol is in the index cluster.",
        "crypto": "This symbol is in the crypto cluster.",
        "none": "This symbol is not in a named cluster.",
    }


def _priority_criteria() -> dict[str, str]:
    return {
        "0_lock": "This pull is the lock line.",
        "2_missing_priority": "This pull is a missing priority bar.",
        "3_refresh_landed": "This pull refreshes a landed bar.",
        "4_optional": "This pull is optional.",
        "5_do_not_trade": "This pull is not a trade surface.",
    }


def _admit_criteria() -> dict[str, str]:
    return {
        "m15_h4_d1_optional": "Live admit wants M15 and H4, and D1 is optional.",
        "m15_h4_only": "Live admit wants M15 and H4 with no optional D1.",
        "withhold": "Do not name an admit contract for this symbol.",
    }


def _symbol_questions(facts: Mapping[str, Any], sleeves: tuple[str, ...]) -> dict[str, Any]:
    """One pack for this symbol. Types are noul, choice, or score."""

    safe = _scrub(dict(facts))
    levels = _levels(safe if isinstance(safe, dict) else {})
    sleeve_criteria = {name: f"Probe this symbol with {name}." for name in sleeves}
    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        "inv_role",
        "Which inventory role is this symbol? "
        "The option you return is that role. "
        "An empty answer or a tie is not a role. "
        "Do not send an order.",
        _role_criteria(),
    ))
    pack.update(_choice_question(
        "inv_cluster",
        "Which named cluster is this symbol in? "
        "The option you return is that cluster. "
        "An empty answer or a tie is not a cluster. "
        "Do not send an order.",
        _cluster_criteria(),
    ))
    pack.update(_choice_question(
        "inv_probe_sleeve",
        "Which probe sleeve names this symbol? "
        "The option you return is that sleeve. "
        "An empty answer or a tie is not a sleeve. "
        "Do not send an order.",
        sleeve_criteria,
    ))
    pack.update(_choice_question(
        "inv_side",
        "Which side is this probe? "
        "The option you return is that side. "
        "An empty answer or a tie is not a side. "
        "Do not send an order.",
        {"long": "The probe side is long.", "short": "The probe side is short."},
    ))
    pack.update(_choice_question(
        "inv_origin",
        "Which origin names this probe? "
        "The option you return is that origin. "
        "An empty answer or a tie is not an origin. "
        "Do not send an order.",
        {
            "f5_challenge": "The probe origin is f5_challenge.",
            "other_origin": "The probe origin is something else.",
        },
    ))
    pack.update(_choice_question(
        "inv_clock",
        "Which clock names this probe? "
        "The option you return is that clock. "
        "An empty answer or a tie is not a clock. "
        "Do not send an order.",
        {
            "as_of_open_study": "The probe clock is as_of_open_study.",
            "clock_now": "The probe clock is the current clock.",
        },
    ))
    pack.update(_choice_question(
        "inv_priority",
        "Which pull priority is this symbol? "
        "The option you return is that priority. "
        "An empty answer or a tie is not a priority. "
        "Do not send an order.",
        _priority_criteria(),
    ))
    pack.update(_choice_question(
        "inv_admit_contract",
        "Which admit contract names this symbol? "
        "The option you return is that contract. "
        "An empty answer or a tie is not a contract. "
        "Do not send an order.",
        _admit_criteria(),
    ))
    pack.update(_score_question("inv_entry", _score_text("probe entry"), levels))
    pack.update(_score_question("inv_stop", _score_text("probe stop"), levels))
    pack.update(_score_question("inv_stop_dist", _score_text("probe stop distance"), levels))
    pack.update(_score_question("inv_spread_r", _score_text("probe spread in stop units"), levels))
    pack.update(_score_question("inv_threshold", _score_text("threshold parameter"), levels))
    pack.update(_score_question("inv_loop", _score_text("loop bound for this symbol"), levels))
    pack.update(_score_question("inv_parameter", _score_text("open parameter for this symbol"), levels))
    pack.update(_noul_question(
        "inv_admit_sit",
        "Is this symbol sufficient at the sit clock? "
        "An empty answer leaves it unset. Do not send an order.",
        "The symbol is sufficient at the sit clock.",
        "The symbol is not sufficient at the sit clock.",
    ))
    pack.update(_noul_question(
        "inv_admit_now",
        "Is this symbol sufficient at the current clock? "
        "An empty answer leaves it unset. Do not send an order.",
        "The symbol is sufficient now.",
        "The symbol is not sufficient now.",
    ))
    pack.update(_noul_question(
        "inv_hard_off",
        "Is this symbol a house hard-off trade surface? "
        "An empty answer leaves it unset. Do not send an order.",
        "This symbol is a house hard-off trade surface.",
        "This symbol is not a house hard-off trade surface.",
    ))
    pack.update(_noul_question(
        "inv_do_not_pull",
        "Is this symbol not a trade-surface pull? "
        "An empty answer leaves it unset. Do not send an order.",
        "Do not pull this symbol as a trade surface.",
        "This symbol may be pulled as a trade surface.",
    ))
    pack.update(_noul_question(
        "inv_optional_risk_peer",
        "Is this symbol an optional risk peer and not a trade surface? "
        "An empty answer leaves it unset. Do not send an order.",
        "This symbol is an optional risk peer, not a trade surface.",
        "This symbol is not that optional risk peer.",
    ))
    pack.update(_noul_question(
        "inv_occupancy_peer",
        "Is this symbol an occupancy peer without a jev priority? "
        "An empty answer leaves it unset. Do not send an order.",
        "This symbol is an occupancy peer without jev priority.",
        "This symbol is not that occupancy peer.",
    ))
    pack.update(_noul_question(
        "inv_april_wear",
        "Does an April historical file exist that this symbol must not wear? "
        "An empty answer leaves it unset. Do not send an order.",
        "An April file exists and this symbol must not wear it.",
        "This symbol does not carry that April gap.",
    ))
    pack.update(_noul_question(
        "inv_parent_shadow",
        "Does the parent directory shadow a fresher multi sibling for this symbol? "
        "An empty answer leaves it unset. Do not send an order.",
        "The parent shadows a fresher multi sibling.",
        "The parent does not shadow a fresher multi sibling.",
    ))
    pack.update(_noul_question(
        "inv_m15_stale",
        "Is this symbol's M15 stale against the current clock? "
        "An empty answer leaves it unset. Do not send an order.",
        "M15 is stale against the current clock.",
        "M15 is not stale against the current clock.",
    ))
    pack.update(_noul_question(
        "inv_insufficient_sit",
        "Is this symbol insufficient at the sit clock while M15 is present? "
        "An empty answer leaves it unset. Do not send an order.",
        "The symbol is insufficient at the sit clock.",
        "The symbol is not marked insufficient at the sit clock.",
    ))
    pack.update(_noul_question(
        "inv_d1_missing",
        "Is optional D1 missing for this symbol? "
        "An empty answer leaves it unset. Do not send an order.",
        "Optional D1 is missing.",
        "Optional D1 is not missing.",
    ))
    pack.update(_noul_question(
        "inv_m15_h4_missing",
        "Are challenge-true M15 and H4 missing for this symbol? "
        "An empty answer leaves it unset. Do not send an order.",
        "Challenge-true M15 and H4 are missing.",
        "Challenge-true M15 and H4 are not missing.",
    ))
    pack.update(_noul_question(
        "inv_shadow_sufficient",
        "Is this symbol shadow-sufficient on this clone? "
        "An empty answer leaves it unset. Do not send an order.",
        "This symbol is shadow-sufficient on this clone.",
        "This symbol is not shadow-sufficient on this clone.",
    ))
    pack.update(_noul_question(
        "inv_us30_surface_off",
        "Is the US30 surface off for this symbol's row? "
        "An empty answer leaves it unset. Do not send an order.",
        "The US30 surface is off on this row.",
        "The US30 surface is not off on this row.",
    ))
    pack.update(_noul_question(
        "inv_component",
        "Does this symbol's inventory component exist on this state? "
        "An empty answer leaves it unset. Do not send an order.",
        "This inventory component exists.",
        "This inventory component does not exist.",
    ))
    return _kept_questions(pack)


def _book_questions(facts: Mapping[str, Any]) -> dict[str, Any]:
    safe = _scrub(dict(facts))
    levels = _levels(safe if isinstance(safe, dict) else {})
    pack: dict[str, Any] = {}
    pack.update(_noul_question(
        "inv_book_april_lock",
        "Does this inventory lock out April historical files? "
        "An empty answer leaves it unset. Do not send an order.",
        "This inventory locks out April historical files.",
        "This inventory does not add that lock.",
    ))
    pack.update(_choice_question(
        "inv_book_april_priority",
        "Which priority names the April lock line, if the lock noul is true? "
        "The option you return is that priority. "
        "An empty answer or a tie is not a priority. "
        "Do not send an order.",
        _priority_criteria(),
    ))
    pack.update(_score_question("inv_book_threshold", _score_text("inventory threshold"), levels))
    pack.update(_score_question("inv_book_loop", _score_text("inventory loop bound"), levels))
    pack.update(_score_question("inv_book_parameter", _score_text("inventory parameter"), levels))
    pack.update(_noul_question(
        "inv_book_component",
        "Does this inventory component exist on this state? "
        "An empty answer leaves it unset. Do not send an order.",
        "This inventory component exists.",
        "This inventory component does not exist.",
    ))
    return _kept_questions(pack)


def _post(state: dict[str, Any], questions: dict[str, Any]) -> dict[str, Any]:
    """One evaluate. The client posts jev-1.13.0 to the System One URL."""

    from .jev_client import evaluate

    receipt = evaluate(
        state,
        questions=dict(questions),
        merge_sleeve=False,
        model=MODEL,
    )
    if not isinstance(receipt, dict):
        raise TypeError("evaluate_not_a_dict")
    return receipt


def _ask(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = _scrub(dict(state))
    if not isinstance(payload, dict):
        payload = {}
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    asked = _kept_questions(questions)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=asked)
    except Exception:
        loaded = None
    payload["prior_outcomes"] = [] if loaded is None else loaded
    try:
        receipt = _post(payload, asked)
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return {"error": type(exc).__name__, "answers": {}, "state": payload, "model": MODEL}
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None if answers else (receipt.get("error") or receipt.get("skipped") or "empty")
    return {
        "error": error,
        "answers": answers,
        "state": payload,
        "model": receipt.get("model") or MODEL,
    }


def _remember(state: Mapping[str, Any], rows: Sequence[tuple[str, Any, str | None]]) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            return


def _apply(
    answers: Any,
    error: Any,
    spec: Sequence[tuple[str, str, str, tuple[str, ...] | None]],
) -> dict[str, Any]:
    """Read the return. An empty block, a tie, or an error stays unset."""

    got = answers if isinstance(answers, Mapping) else {}
    out: dict[str, Any] = {}
    for field, kind, qid, order in spec:
        out[field] = _pull(got.get(qid), kind, order)
    return out


def _decide(
    state: Mapping[str, Any],
    questions: Mapping[str, Any],
    spec: Sequence[tuple[str, str, str, tuple[str, ...] | None]],
) -> dict[str, Any]:
    asked = _ask(state, questions)
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    error = asked.get("error")
    out = _apply(answers, error, spec)
    rows: list[tuple[str, Any, str | None]] = []
    for field, kind, qid, order in spec:
        value = out.get(field)
        rows.append((qid, value, _why(answers.get(qid), value, order, error)))
    _remember(asked.get("state") if isinstance(asked.get("state"), Mapping) else {}, rows)
    out["_error"] = error
    return out


def _bars() -> Any:
    try:
        from . import bars as module
    except Exception:
        return None
    return module


def normalize_symbol(symbol: Any) -> str:
    mod = _bars()
    fn = getattr(mod, "normalize_symbol", None) if mod is not None else None
    if callable(fn):
        try:
            return str(fn(symbol))
        except Exception:
            pass
    raw = str(symbol or "").strip().upper().replace(".", "_").replace(" ", "")
    if raw.endswith("_CASH"):
        raw = raw[: -len("_CASH")]
    if raw.endswith("_C"):
        raw = raw[: -len("_C")]
    return raw


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_utc(raw: Any) -> datetime | None:
    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            return raw.replace(tzinfo=timezone.utc)
        return raw.astimezone(timezone.utc)
    text = str(raw or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _rel_repo(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path)
    except Exception:
        return str(path)


def _bar_dir() -> Path | None:
    mod = _bars()
    path = getattr(mod, "CHALLENGE_BAR_DIR", None) if mod is not None else None
    return path if isinstance(path, Path) else None


def _multi_dir() -> Path | None:
    mod = _bars()
    path = getattr(mod, "CHALLENGE_BAR_MULTI_DIR", None) if mod is not None else None
    return path if isinstance(path, Path) else None


def _csv_header(path: Path) -> list[str]:
    if not path.is_file():
        return []
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        try:
            return next(reader)
        except StopIteration:
            return []


def _blank_tf(tf: str) -> dict[str, Any]:
    return {
        "tf": tf.upper(),
        "present": None,
        "path": None,
        "n": None,
        "has_time_utc": None,
        "under_data_historical": None,
        "first_utc": None,
        "last_utc": None,
        "fresh_at_as_of": None,
        "stale_at_as_of": None,
        "max_lag": None,
    }


def _tf_meta(symbol: str, tf: str, as_of: datetime | None) -> dict[str, Any]:
    mod = _bars()
    resolve = getattr(mod, "resolve_challenge_tf", None) if mod is not None else None
    load = getattr(mod, "load_ohlc_csv", None) if mod is not None else None
    snap_of = getattr(mod, "tf_snap", None) if mod is not None else None
    if not callable(resolve) or not callable(load):
        return _blank_tf(tf)
    try:
        path = resolve(symbol, tf)
    except Exception:
        return _blank_tf(tf)
    if not isinstance(path, Path):
        return _blank_tf(tf)
    present = path.is_file()
    header = _csv_header(path) if present else []
    rows: Any = []
    if present:
        try:
            rows = load(path)
        except Exception:
            rows = None
    if rows is None:
        n = None
        first = None
        last = None
        fresh = None
        stale = None
    else:
        n = len(rows)
        first = rows[0].utc if rows else None
        last = rows[-1].utc if rows else None
        fresh = None
        stale = None
        if as_of is not None and callable(snap_of):
            try:
                snap = snap_of(rows, as_of, tf.upper()) if rows else None
            except Exception:
                snap = None
                fresh = None
                stale = None
            else:
                fresh = snap is not None
                stale = bool(rows) and snap is None
    rel = None
    if present:
        rel = _rel_repo(path)
    under_data = None if rel is None else bool(rel.startswith("data/"))
    lag = getattr(mod, "_MAX_LAG", None) if mod is not None else None
    max_lag = None
    if isinstance(lag, Mapping) and tf.upper() in lag:
        max_lag = str(lag.get(tf.upper()))
    return {
        "tf": tf.upper(),
        "present": present,
        "path": rel,
        "n": n,
        "has_time_utc": ("time_utc" in header) if present else False,
        "under_data_historical": under_data,
        "first_utc": _iso(first) if isinstance(first, datetime) else None,
        "last_utc": _iso(last) if isinstance(last, datetime) else None,
        "fresh_at_as_of": fresh,
        "stale_at_as_of": stale,
        "max_lag": max_lag,
    }


def _stem_aliases(symbol: str) -> set[str]:
    norm = normalize_symbol(symbol)
    aliases = {norm} if norm else set()
    mod = _bars()
    fn = getattr(mod, "file_stem_for", None) if mod is not None else None
    if callable(fn):
        try:
            stem = str(fn(symbol) or "").strip()
        except Exception:
            stem = ""
        if stem:
            aliases.add(stem)
    if norm == "US30":
        aliases.update({"US30_cash", "US30"})
    if norm == "UK100":
        aliases.update({"UK100_cash", "UK100"})
    return {alias for alias in aliases if alias}


def _april_m15_paths(symbol: str) -> list[str]:
    aliases = _stem_aliases(symbol)
    roots = (
        REPO_ROOT / "data",
        REPO_ROOT / "data" / "historical",
        REPO_ROOT / "data" / "historical_2026",
    )
    found: list[str] = []
    for root in roots:
        if not root.is_dir():
            continue
        for alias in aliases:
            path = root / f"{alias}_M15.csv"
            if path.is_file():
                rel = _rel_repo(path)
                if rel and rel not in found:
                    found.append(rel)
    return found


def gtos_24_from_source() -> tuple[str, ...]:
    """Read GTOS_24_SYMBOL_SURFACE without importing the timewarp module."""

    path = REPO_ROOT / "src" / "research_infra" / "v4_timewarp_simulated_live_research_loop.py"
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"^GTOS_24_SYMBOL_SURFACE = \((.*?)\)\nINCLUDED_SYMBOLS",
        text,
        flags=re.S | re.M,
    )
    if not match:
        raise RuntimeError("GTOS_24_SYMBOL_SURFACE assignment not found")
    tree = ast.parse("GTOS_24_SYMBOL_SURFACE = (" + match.group(1) + ")")
    assign = tree.body[0]
    return tuple(ast.literal_eval(assign.value))


def _profile_instruments(profile: str = "operator_profile") -> list[str] | None:
    path = REPO_ROOT / "config" / "profiles" / f"{profile}.yaml"
    if not path.is_file():
        return None
    try:
        import yaml
    except Exception:
        return None
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    instruments = payload.get("instruments") or {}
    if not isinstance(instruments, Mapping):
        return None
    return sorted(str(key) for key in instruments)


def _armed_sleeves() -> dict[str, list[str]] | None:
    path = REPO_ROOT / "config" / "live_armed_set.json"
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    out: dict[str, list[str]] = {}
    accounts = payload.get("accounts") or {}
    if not isinstance(accounts, Mapping):
        return out
    for name, row in accounts.items():
        if isinstance(row, Mapping):
            out[str(name)] = list(row.get("armed_sleeves") or [])
    return out


def _sleeve_surfaces() -> dict[str, dict[str, list[str]]] | None:
    """Generator ON_SURFACE from the live registry. Does not import selector_v4."""

    try:
        from src.components.ultimate_book.sleeves import registry as reg
    except Exception:
        return None
    groups = {
        "built": getattr(reg, "BUILT", None),
        "candidate_built": getattr(reg, "CANDIDATE_BUILT", None),
        "market_expansion_built": getattr(reg, "MARKET_EXPANSION_BUILT", None),
    }
    out: dict[str, dict[str, list[str]]] = {}
    for group, mapping in groups.items():
        if not isinstance(mapping, Mapping):
            continue
        out[group] = {}
        for tag, spec in mapping.items():
            surface = getattr(spec, "on_surface", None)
            out[group][str(tag)] = list(surface) if surface is not None else []
    return out


def _admission_surfaces() -> dict[str, dict[str, list[str]]] | None:
    try:
        from src.components.ultimate_book.admission import (
            CLEAN3_REGISTRY,
            CLEAN4_REGISTRY,
            SLEEVE_REGISTRY,
        )
    except Exception:
        return None

    def _pack(reg: Any) -> dict[str, list[str]]:
        if not isinstance(reg, Mapping):
            return {}
        packed: dict[str, list[str]] = {}
        for name, spec in reg.items():
            symbols = getattr(spec, "symbols", None)
            packed[str(name)] = list(symbols) if symbols is not None else []
        return packed

    return {
        "sleeve_registry": _pack(SLEEVE_REGISTRY),
        "clean3": _pack(CLEAN3_REGISTRY),
        "clean4": _pack(CLEAN4_REGISTRY),
    }


def _export_mt5_symbols() -> list[str] | None:
    path = REPO_ROOT / "scripts" / "export_mt5_historical.py"
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r"^SYMBOLS = \{(.+?)^\}", text, flags=re.S | re.M)
    if not match:
        return []
    try:
        tree = ast.parse("SYMBOLS = {" + match.group(1) + "}")
        return sorted(ast.literal_eval(tree.body[0].value).keys())
    except Exception:
        return None


def _vnext_24() -> tuple[str, ...] | None:
    path = REPO_ROOT / "scripts" / "verify_broker_profile.py"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^VNEXT_24_SYMBOLS = \((.*?)\)\n", text, flags=re.S | re.M)
    if not match:
        return None
    tree = ast.parse("VNEXT_24_SYMBOLS = (" + match.group(1) + ")")
    return tuple(ast.literal_eval(tree.body[0].value))


def _named_file(name: str) -> Path | None:
    root = _bar_dir()
    if root is None:
        return None
    return root / name


def _read_json(path: Path | None) -> Any:
    if path is None or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _slate_counts(slate: Any) -> dict[str, int] | None:
    if not isinstance(slate, dict):
        return None
    try:
        from .challenge_shadow import _slate_bags
    except Exception:
        return None
    try:
        bags = _slate_bags(slate)
    except Exception:
        return None
    counts: Counter[str] = Counter()
    for bag in bags or []:
        if isinstance(bag, Mapping):
            counts[normalize_symbol(str(bag.get("symbol") or ""))] += 1
    counts.pop("", None)
    return dict(counts)


def _open_from_sit(sit: Mapping[str, Any]) -> dict[str, Any]:
    positions = [row for row in (sit.get("positions") or []) if isinstance(row, Mapping)]
    tickets: list[Any] = []
    symbols: list[str] = []
    times: list[datetime] = []
    for row in positions:
        ticket = row.get("ticket")
        if ticket in (None, ""):
            ticket = row.get("position")
        if ticket not in (None, ""):
            tickets.append(ticket)
        sym = normalize_symbol(str(row.get("symbol") or ""))
        if sym and sym not in symbols:
            symbols.append(sym)
        stamp = _parse_utc(row.get("time_utc") or row.get("open_utc") or row.get("time"))
        if stamp is not None:
            times.append(stamp)
    return {
        "open_ticket": tickets[0] if len(tickets) == 1 else (sit.get("open_ticket") if not tickets else None),
        "open_symbol": symbols[0] if len(symbols) == 1 else None,
        "ticket_as_of": times[0] if len(times) == 1 else None,
        "sit_as_of": _parse_utc(sit.get("sit_utc")),
    }


def _host_tape() -> dict[str, Any]:
    sit_raw = _read_json(_named_file("sit_20260917.json"))
    sit = sit_raw if isinstance(sit_raw, dict) else None
    deals_path = _named_file("deals_since_20260909.jsonl")
    deal_counts: dict[str, int] | None
    if deals_path is None or not deals_path.is_file():
        deal_counts = None
    else:
        counts: Counter[str] = Counter()
        try:
            lines = deals_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            deal_counts = None
        else:
            for line in lines:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict):
                    counts[normalize_symbol(str(row.get("symbol") or ""))] += 1
            counts.pop("", None)
            deal_counts = dict(counts)
    slate_raw = _read_json(_named_file("slate_20260917T104105Z_bddc8ff9fad4a254.json"))
    slate_counts = _slate_counts(slate_raw) if isinstance(slate_raw, dict) else None
    sit_counts: dict[str, int] | None = None
    occupied: list[str] | None = None
    open_row: dict[str, Any] = {
        "open_ticket": None,
        "open_symbol": None,
        "ticket_as_of": None,
        "sit_as_of": None,
    }
    if sit is not None:
        counter: Counter[str] = Counter()
        for row in list(sit.get("positions") or []) + list(sit.get("closes_since_2026_09_15_18UTC") or []):
            if isinstance(row, Mapping):
                counter[normalize_symbol(str(row.get("symbol") or ""))] += 1
        counter.pop("", None)
        sit_counts = dict(counter)
        occupied = [normalize_symbol(item) for item in (sit.get("occupied") or [])]
        occupied = [item for item in occupied if item]
        open_row = _open_from_sit(sit)
    shadow_raw = _read_json(_named_file("shadow.summary.json"))
    shadow = shadow_raw if isinstance(shadow_raw, dict) else None
    summary = None
    if shadow is not None:
        summary = {
            "n": shadow.get("n"),
            "n_sufficient": shadow.get("n_sufficient"),
            "n_xau_sufficient": shadow.get("n_xau_sufficient"),
            "n_non_xau_sufficient": shadow.get("n_non_xau_sufficient"),
            "n_missing_m15": shadow.get("n_missing_m15"),
            "landed_symbols": shadow.get("landed_symbols"),
        }
    return {
        "sit_utc": None if sit is None else sit.get("sit_utc"),
        "sit_as_of": open_row.get("sit_as_of"),
        "ticket_as_of": open_row.get("ticket_as_of"),
        "sit_occupied": occupied,
        "sit_counts": sit_counts,
        "deal_counts": deal_counts,
        "slate_counts": slate_counts,
        "shadow_summary": summary,
        "open_ticket": open_row.get("open_ticket"),
        "open_symbol": open_row.get("open_symbol"),
    }


def _count_for(bag: Any, symbol: str) -> int | None:
    if not isinstance(bag, Mapping):
        return None
    try:
        return int(bag.get(symbol) or 0)
    except (TypeError, ValueError):
        return None


def _tape_present(symbol: str) -> bool | None:
    mod = _bars()
    fn = getattr(mod, "challenge_tape_present", None) if mod is not None else None
    if not callable(fn):
        return None
    try:
        return bool(fn(symbol))
    except Exception:
        return None


def _landed() -> list[str] | None:
    mod = _bars()
    fn = getattr(mod, "landed_challenge_symbols", None) if mod is not None else None
    if not callable(fn):
        return None
    try:
        return [normalize_symbol(item) for item in fn() if normalize_symbol(item)]
    except Exception:
        return None


def _multi_names(attr: str) -> tuple[str, ...] | None:
    mod = _bars()
    if mod is None:
        return None
    raw = getattr(mod, attr, None)
    if raw is None:
        return None
    try:
        return tuple(str(item) for item in raw)
    except TypeError:
        return None


def jev_watch_symbols() -> list[str]:
    """Named inventory subjects plus landed symbols the bar helper can list."""

    seen: list[str] = []

    def _add(item: Any) -> None:
        sym = normalize_symbol(item)
        if sym and sym not in seen:
            seen.append(sym)

    _add(_NAMED_PRIMARY)
    for attr in ("MULTI_SYMBOL_PRIORITY", "MULTI_SYMBOL_OPTIONAL"):
        names = _multi_names(attr)
        if names:
            for item in names:
                _add(item)
    for item in VPS_NAMED_PEER_PULL:
        _add(item)
    for item in CHAIR_CROSS_PULL:
        _add(item)
    for item in _OPTIONAL_RISK_PEER:
        _add(item)
    landed = _landed()
    if landed:
        for item in landed:
            _add(item)
    return seen


def _in_universe(symbol: str, names: Sequence[str] | None) -> bool | None:
    if names is None:
        return None
    pool = {str(item) for item in names}
    norm = normalize_symbol(symbol)
    return norm in pool or f"{norm}_cash" in pool or symbol in pool


def _in_menu(symbol: str, names: Sequence[str]) -> bool:
    pool = {normalize_symbol(item) for item in names}
    return normalize_symbol(symbol) in pool


def _freshness() -> dict[str, str] | None:
    mod = _bars()
    lag = getattr(mod, "_MAX_LAG", None) if mod is not None else None
    if not isinstance(lag, Mapping):
        return None
    return {str(tf): str(delta) for tf, delta in lag.items()}


def _landing() -> list[str] | None:
    mod = _bars()
    fn = getattr(mod, "challenge_search_dirs", None) if mod is not None else None
    if not callable(fn):
        return None
    try:
        return [str(path) for path in fn()]
    except Exception:
        return None


def _challenge_paths(symbol: str) -> dict[str, str] | None:
    mod = _bars()
    fn = getattr(mod, "challenge_symbol_paths", None) if mod is not None else None
    if not callable(fn):
        return None
    try:
        paths = fn(symbol)
    except Exception:
        return None
    if not isinstance(paths, Mapping):
        return None
    out: dict[str, str] = {}
    for tf, path in paths.items():
        if isinstance(path, Path):
            rel = _rel_repo(path)
            if rel is not None:
                out[str(tf)] = rel
        else:
            out[str(tf)] = str(path)
    return out


def _books_fact(symbol: str) -> dict[str, Any]:
    mod = _bars()
    books_for = getattr(mod, "books_for_symbol", None) if mod is not None else None
    if not callable(books_for):
        return {"books_present": None, "books_for_symbol_substituted_xau": None, "books": None}
    try:
        books = books_for(symbol)
    except Exception:
        return {"books_present": None, "books_for_symbol_substituted_xau": None, "books": None}
    substituted: bool | None = False
    load = getattr(mod, "load_challenge_books", None)
    tape = getattr(mod, "challenge_tape_present", None)
    if symbol != "XAUUSD" and books is not None and callable(load) and callable(tape):
        try:
            xau_books = load("XAUUSD") if tape("XAUUSD") else None
        except Exception:
            xau_books = None
        if isinstance(xau_books, Mapping):
            try:
                xau_m15 = (xau_books.get("m15") or [None])[0]
                here_m15 = (books.get("m15") or [None])[0]
            except Exception:
                xau_m15 = None
                here_m15 = None
            if xau_m15 is not None and here_m15 is not None:
                source = str(getattr(xau_m15, "source_path", "") or "")
                substituted = getattr(xau_m15, "source_path", None) == getattr(here_m15, "source_path", None) and "XAUUSD" in source
            else:
                substituted = False
        else:
            substituted = False
    return {
        "books_present": books is not None,
        "books_for_symbol_substituted_xau": substituted,
        "books": books,
    }


def _xau_parent_vs_multi() -> dict[str, Any]:
    parent_dir = _bar_dir()
    multi_dir = _multi_dir()
    if parent_dir is None or multi_dir is None:
        return {
            "bound_dir": _rel_repo(parent_dir),
            "multi_dir": _rel_repo(multi_dir),
            "search_order": None,
            "parent_equals_multi": None,
            "tfs": {},
        }
    tfs: dict[str, Any] = {}
    compared = True
    equal = True
    for tf in ("M15", "H4", "D1"):
        parent = parent_dir / f"XAUUSD_{tf}.csv"
        multi = multi_dir / f"XAUUSD_{tf}.csv"
        parent_ok = parent.is_file()
        multi_ok = multi.is_file()
        same = False
        if parent_ok and multi_ok:
            try:
                same = parent.read_bytes() == multi.read_bytes()
            except OSError:
                same = False
                compared = False
        else:
            equal = False
        if parent_ok and multi_ok and not same:
            equal = False
        tfs[tf.lower()] = {
            "parent_present": parent_ok,
            "multi_present": multi_ok,
            "byte_identical": same if parent_ok and multi_ok else None,
        }
    return {
        "bound_dir": _rel_repo(parent_dir),
        "multi_dir": _rel_repo(multi_dir),
        "search_order": "parent then multi" if compared else None,
        "parent_equals_multi": equal if compared else None,
        "tfs": tfs,
    }


def _unused_newer_multi(symbol: str, tf: str, as_of: datetime | None, bound_rel: str | None) -> dict[str, Any] | None:
    multi_dir = _multi_dir()
    mod = _bars()
    load = getattr(mod, "load_ohlc_csv", None) if mod is not None else None
    snap_of = getattr(mod, "tf_snap", None) if mod is not None else None
    if multi_dir is None or not callable(load):
        return None
    suffix = tf.upper()
    stems: list[str] = []
    file_stem = getattr(mod, "file_stem_for", None)
    if callable(file_stem):
        try:
            named = str(file_stem(symbol) or "").strip()
        except Exception:
            named = ""
        if named:
            stems.append(named)
    for alias in sorted(_stem_aliases(symbol)):
        if alias not in stems:
            stems.append(alias)
    path: Path | None = None
    for stem in stems:
        candidate = multi_dir / f"{stem}_{suffix}.csv"
        if candidate.is_file():
            path = candidate
            break
    if path is None:
        return None
    rel = _rel_repo(path)
    if bound_rel and rel == bound_rel:
        return None
    if bound_rel:
        bound_path = Path(bound_rel)
        if not bound_path.is_absolute():
            bound_path = REPO_ROOT / bound_rel
        try:
            if bound_path.is_file() and bound_path.resolve() == path.resolve():
                return None
        except OSError:
            pass
    header = _csv_header(path)
    try:
        rows = load(path)
    except Exception:
        return None
    if not rows:
        return None
    snap = None
    if as_of is not None and callable(snap_of):
        try:
            snap = snap_of(rows, as_of, suffix)
        except Exception:
            snap = None
    last = rows[-1]
    bound_last = None
    if bound_rel and callable(load):
        bound_path = REPO_ROOT / bound_rel
        if bound_path.is_file():
            try:
                bound_rows = load(bound_path)
            except Exception:
                bound_rows = None
            if bound_rows:
                bound_last = bound_rows[-1].utc
    unused_last = last.utc if last else None
    newer = bool(unused_last and (bound_last is None or unused_last > bound_last))
    if not newer:
        return None
    return {
        "tf": suffix,
        "path": rel,
        "n": len(rows),
        "has_time_utc": "time_utc" in header,
        "first_utc": _iso(rows[0].utc) if rows else None,
        "last_utc": _iso(unused_last),
        "fresh_at_as_of": None if as_of is None else snap is not None,
        "newer_than_bound": True,
        "bound_path": bound_rel,
        "bound_last_utc": _iso(bound_last) if isinstance(bound_last, datetime) else None,
    }


def _family_hard_off(sleeve: str | None, symbol: str) -> Any:
    if not sleeve:
        return None
    try:
        from .family import hard_off_family
    except Exception:
        return None
    try:
        return hard_off_family(sleeve, symbol)
    except Exception:
        return None


def _family_lists() -> tuple[list[str] | None, list[str] | None]:
    try:
        from .family import HARD_OFF_FAMILIES, KEEP_FAMILIES
    except Exception:
        return None, None
    try:
        return list(HARD_OFF_FAMILIES), list(KEEP_FAMILIES)
    except Exception:
        return None, None


def _gold_schema() -> str | None:
    try:
        from .gold_state import SCHEMA as gold_schema
    except Exception:
        return None
    return str(gold_schema) if gold_schema else None


def _assemble_measured(
    symbol: str,
    as_of: datetime | None,
    decisions: Mapping[str, Any],
    books_fact: Mapping[str, Any],
) -> dict[str, Any]:
    base = {
        "books_present": books_fact.get("books_present"),
        "books_for_symbol_substituted_xau": books_fact.get("books_for_symbol_substituted_xau"),
        "schema": None,
        "family_class": None,
        "family_hard_off_measured": _family_hard_off(decisions.get("probe_sleeve"), symbol),
        "timeframes_m15_h4": None,
        "timeframes_m15_h4_d1": None,
        "assembler_state_sufficient": None,
        "missing_fields": None,
        "assembler_us30_off": None,
    }
    side = decisions.get("side")
    sleeve = decisions.get("probe_sleeve")
    origin = decisions.get("origin")
    clock = decisions.get("clock")
    entry = decisions.get("entry")
    stop = decisions.get("stop")
    dist = decisions.get("stop_dist")
    spread = decisions.get("spread_r")
    if as_of is None or side not in _SIDE_ORDER or not sleeve or not origin or not clock:
        return base
    if None in (entry, stop, dist, spread):
        return base
    try:
        from .gold_state import assemble_gold_state_v0
    except Exception:
        return base
    try:
        state = assemble_gold_state_v0(
            as_of_utc=as_of,
            side=side,
            sleeve=sleeve,
            symbol=symbol,
            origin_organism=origin,
            as_of_clock=clock,
            books=books_fact.get("books"),
            spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
            geometry={"entry": entry, "stop": stop, "stop_dist": dist},
            cost={"spread_r_of_stop": spread},
            sleeve_features={"tag": sleeve, "a8_source": "probe"},
        )
    except Exception:
        return base
    if not isinstance(state, dict):
        return base
    completeness = state.get("completeness") if isinstance(state.get("completeness"), dict) else {}
    identity = state.get("identity") if isinstance(state.get("identity"), dict) else {}
    surface = state.get("surface") if isinstance(state.get("surface"), dict) else {}
    missing = completeness.get("missing_fields")
    base.update(
        {
            "schema": state.get("schema"),
            "family_class": identity.get("family_class"),
            "timeframes_m15_h4": completeness.get("timeframes_m15_h4"),
            "timeframes_m15_h4_d1": completeness.get("timeframes_m15_h4_d1"),
            "assembler_state_sufficient": completeness.get("state_sufficient_for_live"),
            "missing_fields": list(missing) if isinstance(missing, (list, tuple)) else None,
            "assembler_us30_off": surface.get("us30_off"),
        }
    )
    return base


def _promote_line(row: Mapping[str, Any]) -> str:
    symbol = str(row.get("symbol") or "")
    unused: Mapping[str, Any] = {}
    newer = row.get("unused_newer_multi")
    if isinstance(newer, Mapping) and isinstance(newer.get("m15"), Mapping):
        unused = newer["m15"]
    bound: Mapping[str, Any] = {}
    bars = row.get("bars")
    if isinstance(bars, Mapping) and isinstance(bars.get("now"), Mapping):
        now = bars["now"]
        if isinstance(now.get("m15"), Mapping):
            bound = now["m15"]
    text = f"Promote multi/ {symbol} over parent"
    unused_last = unused.get("last_utc")
    bound_last = bound.get("last_utc")
    if unused_last or bound_last:
        fresh = unused.get("fresh_at_as_of")
        if fresh is True:
            mark = "fresh"
        elif fresh is False:
            mark = "also_stale"
        else:
            mark = "unset"
        text += f" (unused last={unused_last} {mark}; bound last={bound_last})"
    return text


_GAP_PULLS: tuple[tuple[str, str, Callable[[Mapping[str, Any]], str] | None], ...] = (
    ("hard_off", "house_hard_off_trade_surface", None),
    ("do_not_pull", "do_not_pull_as_trade_surface", lambda row: f"{row.get('symbol')} not a trade surface"),
    ("optional_risk_peer", "optional_risk_peer_not_trade_surface", lambda row: f"{row.get('symbol')} M15+H4 optional risk peer only — not a trade surface"),
    ("occupancy_peer", "occupancy_cluster_no_jev_priority", lambda row: f"{row.get('symbol')} M15+H4 optional occupancy peer"),
    ("april_wear", "april_historical_exists_do_not_wear", None),
    ("parent_shadow", "parent_shadows_fresher_multi", _promote_line),
    ("m15_stale", "m15_stale_vs_now", lambda row: f"{row.get('symbol')} M15 refresh through current UTC"),
    ("insufficient_sit", "insufficient_at_sit_as_of", None),
    ("d1_missing", "d1_optional_missing", lambda row: f"{row.get('symbol')} D1 optional"),
    ("m15_h4_missing", "challenge_m15_h4_missing", lambda row: f"{row.get('symbol')} M15+H4 Challenge-true (time_utc=server-3h)"),
)


def _gaps_and_pulls(decisions: Mapping[str, Any], row: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    """A gap or a pull line is present only when that Noul is true."""

    gaps: list[str] = []
    pulls: list[str] = []
    for key, label, liner in _GAP_PULLS:
        if decisions.get(key) is True:
            gaps.append(label)
            if liner is not None:
                pulls.append(liner(row))
    return gaps, pulls


def _any_present(flags: Sequence[Any]) -> bool | None:
    if any(flag is True for flag in flags):
        return True
    if flags and all(flag is False for flag in flags):
        return False
    return None


def _measure_symbol(symbol: str, now: datetime, sit_as_of: datetime | None) -> dict[str, Any]:
    m15_now = _tf_meta(symbol, "M15", now)
    h4_now = _tf_meta(symbol, "H4", now)
    d1_now = _tf_meta(symbol, "D1", now)
    m15_sit = _tf_meta(symbol, "M15", sit_as_of) if sit_as_of is not None else _blank_tf("M15")
    h4_sit = _tf_meta(symbol, "H4", sit_as_of) if sit_as_of is not None else _blank_tf("H4")
    april = _april_m15_paths(symbol)
    mod = _bars()
    can_look = _multi_dir() is not None and callable(getattr(mod, "load_ohlc_csv", None) if mod is not None else None)
    unused = {
        "m15": _unused_newer_multi(symbol, "m15", now, m15_now.get("path")),
        "h4": _unused_newer_multi(symbol, "h4", now, h4_now.get("path")),
        "d1": _unused_newer_multi(symbol, "d1", now, d1_now.get("path")),
    }
    unused = {key: value for key, value in unused.items() if value}
    books = _books_fact(symbol)
    return {
        "symbol": symbol,
        "bars": {"now": {"m15": m15_now, "h4": h4_now, "d1": d1_now}, "sit_as_of": {"m15": m15_sit, "h4": h4_sit}},
        "april_m15_paths_not_challenge": april,
        "unused_newer_multi": unused,
        "unused_m15_known": bool(unused.get("m15")) if can_look else None,
        "books": books,
        "challenge_paths": _challenge_paths(symbol),
        "challenge_tape_present": _tape_present(symbol),
    }


def _symbol_facts(
    measured: Mapping[str, Any],
    *,
    host: Mapping[str, Any],
    gtos24: Sequence[str] | None,
    profile: Sequence[str] | None,
    priority: Sequence[str] | None,
    optional: Sequence[str] | None,
) -> dict[str, Any]:
    symbol = str(measured.get("symbol") or "")
    bars = measured.get("bars") if isinstance(measured.get("bars"), Mapping) else {}
    now = bars.get("now") if isinstance(bars.get("now"), Mapping) else {}
    sit = bars.get("sit_as_of") if isinstance(bars.get("sit_as_of"), Mapping) else {}
    m15 = now.get("m15") if isinstance(now.get("m15"), Mapping) else {}
    h4 = now.get("h4") if isinstance(now.get("h4"), Mapping) else {}
    d1 = now.get("d1") if isinstance(now.get("d1"), Mapping) else {}
    sit_m15 = sit.get("m15") if isinstance(sit.get("m15"), Mapping) else {}
    unused = measured.get("unused_newer_multi") if isinstance(measured.get("unused_newer_multi"), Mapping) else {}
    unused_m15 = unused.get("m15") if isinstance(unused.get("m15"), Mapping) else {}
    books = measured.get("books") if isinstance(measured.get("books"), Mapping) else {}
    shadow = host.get("shadow_summary") if isinstance(host.get("shadow_summary"), Mapping) else {}
    occupied = host.get("sit_occupied")
    return {
        "model": MODEL,
        "login": ACCOUNT_LOGIN,
        "ns": ACCOUNT_NS,
        "symbol": symbol,
        "in_named_primary": symbol == _NAMED_PRIMARY,
        "in_multi_priority": _in_universe(symbol, priority),
        "in_multi_optional": _in_universe(symbol, optional),
        "in_named_peer_pull": _in_menu(symbol, VPS_NAMED_PEER_PULL),
        "in_chair_cross_pull": _in_menu(symbol, CHAIR_CROSS_PULL),
        "in_named_optional_risk_peer": symbol in _OPTIONAL_RISK_PEER,
        "in_gtos_24": _in_universe(symbol, gtos24),
        "in_ftmo_profile": _in_universe(symbol, profile),
        "challenge_tape_present": measured.get("challenge_tape_present"),
        "m15_present": m15.get("present"),
        "h4_present": h4.get("present"),
        "d1_present": d1.get("present"),
        "m15_n": m15.get("n"),
        "h4_n": h4.get("n"),
        "d1_n": d1.get("n"),
        "m15_fresh": m15.get("fresh_at_as_of"),
        "h4_fresh": h4.get("fresh_at_as_of"),
        "d1_fresh": d1.get("fresh_at_as_of"),
        "m15_stale_measured": m15.get("stale_at_as_of"),
        "m15_last_utc": m15.get("last_utc"),
        "h4_last_utc": h4.get("last_utc"),
        "d1_last_utc": d1.get("last_utc"),
        "sit_m15_fresh": sit_m15.get("fresh_at_as_of"),
        "sit_m15_present": sit_m15.get("present"),
        "unused_newer_m15": measured.get("unused_m15_known"),
        "unused_m15_last_utc": unused_m15.get("last_utc"),
        "unused_m15_fresh": unused_m15.get("fresh_at_as_of"),
        "april_m15_present": bool(measured.get("april_m15_paths_not_challenge")),
        "books_present": books.get("books_present"),
        "books_substituted_xau": books.get("books_for_symbol_substituted_xau"),
        "sit_count": _count_for(host.get("sit_counts"), symbol),
        "deal_count": _count_for(host.get("deal_counts"), symbol),
        "slate_count": _count_for(host.get("slate_counts"), symbol),
        "occupied_now": None if occupied is None else symbol in occupied,
        "shadow_n_xau_sufficient": shadow.get("n_xau_sufficient") if shadow else None,
        "shadow_n_sufficient": shadow.get("n_sufficient") if shadow else None,
    }


def _compose_row(measured: Mapping[str, Any], decisions: Mapping[str, Any], *, now: datetime) -> dict[str, Any]:
    symbol = str(measured.get("symbol") or "")
    sit_as_of = decisions.get("_sit_as_of") if isinstance(decisions.get("_sit_as_of"), datetime) else None
    in_gtos = decisions.get("_in_gtos_24")
    in_profile = decisions.get("_in_ftmo_profile")
    sit_count = decisions.get("_sit_count")
    deal_count = decisions.get("_deal_count")
    slate_count = decisions.get("_slate_count")
    occupied_now = decisions.get("_occupied_now")
    clean = {key: value for key, value in decisions.items() if not str(key).startswith("_")}
    draft = {
        "symbol": symbol,
        "bars": measured.get("bars"),
        "unused_newer_multi": measured.get("unused_newer_multi"),
    }
    gaps, pulls = _gaps_and_pulls(clean, draft)
    books = measured.get("books") if isinstance(measured.get("books"), Mapping) else {}
    assembled_sit = _assemble_measured(symbol, sit_as_of, clean, books)
    assembled_now = _assemble_measured(symbol, now, clean, books)
    bars = measured.get("bars") if isinstance(measured.get("bars"), Mapping) else {}
    now_bars = bars.get("now") if isinstance(bars.get("now"), Mapping) else {}
    flags = []
    for name in ("m15", "h4", "d1"):
        meta = now_bars.get(name) if isinstance(now_bars.get(name), Mapping) else {}
        flags.append(meta.get("present"))
    return {
        "symbol": symbol,
        "role": clean.get("role"),
        "cluster": clean.get("cluster"),
        "probe_sleeve": clean.get("probe_sleeve"),
        "side": clean.get("side"),
        "origin": clean.get("origin"),
        "clock": clean.get("clock"),
        "entry": clean.get("entry"),
        "stop": clean.get("stop"),
        "stop_dist": clean.get("stop_dist"),
        "spread_r": clean.get("spread_r"),
        "threshold": clean.get("threshold"),
        "loop_bound": clean.get("loop_bound"),
        "parameter": clean.get("parameter"),
        "pull_priority": clean.get("priority"),
        "component_exists": clean.get("component_exists"),
        "us30_surface_off": clean.get("us30_surface_off"),
        "in_gtos_24": in_gtos,
        "in_ftmo_profile": in_profile,
        "challenge_tape_present": measured.get("challenge_tape_present"),
        "challenge_paths": measured.get("challenge_paths"),
        "bars": measured.get("bars"),
        "april_m15_paths_not_challenge": measured.get("april_m15_paths_not_challenge"),
        "unused_newer_multi": measured.get("unused_newer_multi"),
        "state_assembled": {"sit_as_of": assembled_sit, "now": assembled_now},
        "scored_live": {
            "sit": sit_count,
            "deals": deal_count,
            "slate": slate_count,
            "occupied_now": occupied_now,
            "shadow_sufficient_on_this_clone": clean.get("shadow_sufficient"),
        },
        "admit": {
            "required": clean.get("admit_contract"),
            "sit_as_of": clean.get("admit_sit"),
            "now": clean.get("admit_now"),
        },
        "gaps": gaps,
        "next_pull": pulls,
        "bars_present_any": _any_present(flags),
        "decisions": clean,
        "decision_error": decisions.get("_error"),
        "systemone_model": MODEL,
    }


def _symbol_row(
    symbol: str,
    *,
    now: datetime,
    host: dict[str, Any],
    gtos24: Sequence[str] | None,
    profile: Sequence[str] | None,
    sit_as_of: datetime | None,
    sleeve_names: Sequence[str] | None,
    priority_names: Sequence[str] | None,
    optional_names: Sequence[str] | None,
) -> dict[str, Any]:
    try:
        measured = _measure_symbol(symbol, now, sit_as_of)
    except Exception:
        measured = {
            "symbol": normalize_symbol(symbol),
            "bars": {"now": {"m15": _blank_tf("M15"), "h4": _blank_tf("H4"), "d1": _blank_tf("D1")}, "sit_as_of": {"m15": _blank_tf("M15"), "h4": _blank_tf("H4")}},
            "april_m15_paths_not_challenge": [],
            "unused_newer_multi": {},
            "books": {"books_present": None, "books_for_symbol_substituted_xau": None, "books": None},
            "challenge_paths": None,
            "challenge_tape_present": None,
        }
    facts = _symbol_facts(
        measured,
        host=host,
        gtos24=gtos24,
        profile=profile,
        priority=priority_names,
        optional=optional_names,
    )
    sleeves = _sleeve_menu(sleeve_names)
    spec = _symbol_spec(sleeves)
    decisions = _decide(facts, _symbol_questions(facts, sleeves), spec)
    decisions["_in_gtos_24"] = facts.get("in_gtos_24")
    decisions["_in_ftmo_profile"] = facts.get("in_ftmo_profile")
    decisions["_sit_count"] = facts.get("sit_count")
    decisions["_deal_count"] = facts.get("deal_count")
    decisions["_slate_count"] = facts.get("slate_count")
    decisions["_occupied_now"] = facts.get("occupied_now")
    decisions["_sit_as_of"] = sit_as_of
    return _compose_row(measured, decisions, now=now)


def _sleeve_names_from(surfaces: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(surfaces, Mapping):
        return []
    names: list[str] = []
    for group in surfaces.values():
        if not isinstance(group, Mapping):
            continue
        for tag in group:
            text = str(tag)
            if text not in names:
                names.append(text)
    return names


def _book_facts(rows: Sequence[Mapping[str, Any]], landed: list[str] | None) -> dict[str, Any]:
    april = 0
    for row in rows:
        paths = row.get("april_m15_paths_not_challenge")
        if isinstance(paths, list):
            april += len(paths)
    return {
        "model": MODEL,
        "login": ACCOUNT_LOGIN,
        "ns": ACCOUNT_NS,
        "n_symbols": len(rows),
        "n_landed": None if landed is None else len(landed),
        "n_april_paths": april,
        "named_peer_n": len(VPS_NAMED_PEER_PULL),
        "chair_cross_n": len(CHAIR_CROSS_PULL),
    }


def _next_pull_list(rows: Sequence[Mapping[str, Any]], book: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Pull lines are the true nouls. Priority is that choice, or unset."""

    ordered: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _add(item: str, why: str | None, priority: Any) -> None:
        if not item or item in seen:
            return
        seen.add(item)
        ordered.append({"item": item, "why": why, "priority": priority})

    if book.get("april_lock") is True:
        _add(
            "Never wear April data/historical* or exports/multi_instrument",
            "april_lock",
            book.get("april_priority"),
        )
    for row in rows:
        gaps = row.get("gaps") if isinstance(row.get("gaps"), list) else []
        why = ", ".join(str(item) for item in gaps) if gaps else row.get("role")
        priority = row.get("pull_priority")
        for item in row.get("next_pull") or []:
            _add(str(item), None if why is None else str(why), priority)
    return ordered


def _peers_present(names: Sequence[str]) -> bool | None:
    flags = [_tape_present(name) for name in names]
    if any(flag is None for flag in flags):
        return None
    return all(flag is True for flag in flags)


def _non_xau_books(landed: list[str] | None) -> bool | None:
    if landed is None:
        return None
    mod = _bars()
    books_for = getattr(mod, "books_for_symbol", None) if mod is not None else None
    tape = getattr(mod, "challenge_tape_present", None) if mod is not None else None
    if not callable(books_for) or not callable(tape):
        return None
    for sym in landed:
        if sym == "XAUUSD":
            continue
        try:
            if tape(sym) and books_for(sym) is not None:
                return True
        except Exception:
            return None
    return False


def _code_symbols(surfaces: Mapping[str, Any] | None) -> set[str]:
    found: set[str] = set()
    if not isinstance(surfaces, Mapping):
        return found
    for group in surfaces.values():
        if not isinstance(group, Mapping):
            continue
        for symbols in group.values():
            if isinstance(symbols, (list, tuple)):
                found.update(str(item) for item in symbols if item)
    return found


def _assemble_intent_notes() -> dict[str, Any]:
    schema = _gold_schema()
    return {
        "assembler": "assemble_gold_state_v0",
        "schema": schema,
        "sufficiency": "the admit contract choice on each row",
        "intent_gold_state": "loads challenge books via books_for_symbol when that helper is present",
        "books_for_symbol": "does not substitute XAU for another pair when the helper is present",
        "news": {"invent_news_protocol": False},
        "peer_prs_not_on_this_branch": {
            "pr_13": "CROSS_ASSET_FEATURES_V0 / CA-* labels are not imported on this branch",
            "pr_15": "peers.usdjpy on gold_state is not imported on this branch",
        },
    }


def collect_inventory(*, now: datetime | None = None) -> dict[str, Any]:
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=timezone.utc)
    try:
        gtos24: list[str] | None = list(gtos_24_from_source())
    except Exception:
        gtos24 = None
    try:
        vnext_raw = _vnext_24()
    except Exception:
        vnext_raw = None
    vnext24 = None if vnext_raw is None else list(vnext_raw)
    profile = _profile_instruments()
    sleeves = _sleeve_surfaces()
    admission = _admission_surfaces()
    host = _host_tape()
    landed = _landed()
    priority = _multi_names("MULTI_SYMBOL_PRIORITY")
    optional = _multi_names("MULTI_SYMBOL_OPTIONAL")
    watch = jev_watch_symbols()
    for bag in (host.get("sit_counts"), host.get("deal_counts"), host.get("slate_counts")):
        if not isinstance(bag, Mapping):
            continue
        for sym in bag:
            text = normalize_symbol(sym)
            if text and text not in watch:
                watch.append(text)
    sleeve_names = _sleeve_names_from(sleeves)
    sit_as_of = host.get("sit_as_of") if isinstance(host.get("sit_as_of"), datetime) else None
    rows = [
        _symbol_row(
            sym,
            now=clock,
            host=host,
            gtos24=gtos24,
            profile=profile,
            sit_as_of=sit_as_of,
            sleeve_names=sleeve_names,
            priority_names=priority,
            optional_names=optional,
        )
        for sym in watch
    ]
    book_state = _book_facts(rows, landed)
    book = _decide(book_state, _book_questions(book_state), _book_spec())
    all_code: set[str] = set()
    for seq in (gtos24, vnext24, profile, watch):
        if seq:
            all_code.update(str(item) for item in seq)
    all_code.update(_code_symbols(sleeves))
    all_code.update(_code_symbols(admission))
    exported = _export_mt5_symbols()
    if exported:
        all_code.update(exported)
    census = []
    for sym in sorted(all_code):
        census.append(
            {
                "symbol": sym,
                "in_gtos_24": _in_universe(sym, gtos24),
                "in_ftmo_profile": _in_universe(sym, profile),
                "in_jev_watch": sym in watch,
                "challenge_landed": _tape_present(sym),
                "april_m15_present": bool(_april_m15_paths(sym)),
            }
        )
    hard_off, keep = _family_lists()
    payload = {
        "schema": SCHEMA,
        "generated_at_utc": _iso(clock),
        "sit_as_of_utc": _iso(sit_as_of),
        "ticket_as_of_utc": _iso(host.get("ticket_as_of") if isinstance(host.get("ticket_as_of"), datetime) else None),
        "lock": dict(LOCK),
        "account": {
            "login": ACCOUNT_LOGIN,
            "ns": ACCOUNT_NS,
            "open_ticket": host.get("open_ticket"),
            "open_symbol": host.get("open_symbol"),
        },
        "challenge_true_contract": {
            "time_utc": "already server-3h; do not run NY+7",
            "measured_tfs": ["M15", "H4", "D1"],
            "freshness": _freshness(),
            "landing": _landing(),
            "april_historical_is_not_challenge_true": book.get("april_lock"),
            "env_override": "GTOS_CHALLENGE_BAR_MULTI",
        },
        "code_universes": {
            "multi_symbol_priority": None if priority is None else list(priority),
            "multi_symbol_optional": None if optional is None else list(optional),
            "gtos_24": gtos24,
            "vnext_24": vnext24,
            "gtos_24_matches_vnext_24": None if gtos24 is None or vnext24 is None else gtos24 == vnext24,
            "ftmo_profile_instruments": profile,
            "ftmo_profile_n": None if profile is None else len(profile),
            "occupancy_cluster_menu": list(_CLUSTER_ORDER),
            "armed_w7_sleeves": _armed_sleeves(),
            "house_hard_off_families": hard_off,
            "keep_families": keep,
            "sleeve_surfaces": sleeves,
            "admission_surfaces": admission,
            "export_mt5_historical_april": exported,
        },
        "disk": {
            "landed_challenge_symbols": landed,
            "vps_named_peer_pull": list(VPS_NAMED_PEER_PULL),
            "chair_cross_pull": list(CHAIR_CROSS_PULL),
            "vps_peer_csvs_on_this_clone": _peers_present(VPS_NAMED_PEER_PULL),
            "non_xau_books_present": _non_xau_books(landed),
            "box_multi_present": (REPO_ROOT / "gtos").is_dir(),
            "xau_parent_vs_multi": _xau_parent_vs_multi(),
        },
        "host_tape": {
            key: value
            for key, value in host.items()
            if key not in {"sit_as_of", "ticket_as_of"}
        },
        "book": {
            "april_lock": book.get("april_lock"),
            "april_priority": book.get("april_priority"),
            "threshold": book.get("threshold"),
            "loop_bound": book.get("loop_bound"),
            "parameter": book.get("parameter"),
            "component_exists": book.get("component_exists"),
            "decision_error": book.get("_error"),
            "model": MODEL,
        },
        "assemble_intent": _assemble_intent_notes(),
        "jev_rows": rows,
        "gtos_census": census,
        "next_pull": _next_pull_list(rows, book),
        "markdown_columns": list(MARKDOWN_COLUMNS),
    }
    return payload


def _yesno(value: Any) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    number = _finite(value)
    if number is not None:
        return format(number, ".10g")
    return "unset"


def _seq_text(value: Any) -> str:
    if value is None:
        return "unset"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value) if value else "(none)"
    return str(value)


def _bars_cell(row: dict[str, Any]) -> str:
    now = (row.get("bars") or {}).get("now") or {}
    bits = []
    for tf in ("m15", "h4", "d1"):
        meta = now.get(tf) or {}
        present = meta.get("present")
        if present is None:
            bits.append(f"{tf.upper()}=unset")
            continue
        if not present:
            bits.append(f"{tf.upper()}=missing")
            continue
        fresh = meta.get("fresh_at_as_of")
        if fresh is True:
            fresh_text = "fresh"
        elif fresh is False:
            fresh_text = "STALE"
        else:
            fresh_text = "unset"
        utc = "time_utc" if meta.get("has_time_utc") is True else ("NO_time_utc" if meta.get("has_time_utc") is False else "unset")
        bits.append(f"{tf.upper()} n={meta.get('n')} last={meta.get('last_utc')} {fresh_text} {utc}")
    return "; ".join(bits)


def _state_cell(row: dict[str, Any]) -> str:
    sit = (row.get("state_assembled") or {}).get("sit_as_of") or {}
    now = (row.get("state_assembled") or {}).get("now") or {}
    admit = row.get("admit") or {}
    family = sit.get("family_class") or "unset"
    return (
        f"sit={_yesno(admit.get('sit_as_of'))} "
        f"(M15+H4={_yesno(sit.get('timeframes_m15_h4'))}, family={family}); "
        f"now={_yesno(admit.get('now'))}; "
        f"contract={admit.get('required') or 'unset'}; "
        f"xau_sub={_yesno(sit.get('books_for_symbol_substituted_xau'))}"
    )


def _scored_cell(row: dict[str, Any]) -> str:
    scored = row.get("scored_live") or {}
    occupied = scored.get("occupied_now")
    if occupied is True:
        occ = "occupied"
    elif occupied is False:
        occ = "flat"
    else:
        occ = "unset"
    return (
        f"sit={scored.get('sit')} deals={scored.get('deals')} slate={scored.get('slate')} {occ}; "
        f"shadow_sufficient={_yesno(scored.get('shadow_sufficient_on_this_clone'))}"
    )


def _gaps_cell(row: dict[str, Any]) -> str:
    gaps = row.get("gaps") or []
    if gaps:
        return ", ".join(str(item) for item in gaps)
    decisions = row.get("decisions") if isinstance(row.get("decisions"), dict) else {}
    if any(decisions.get(key) is None for key, _label, _liner in _GAP_PULLS):
        return "unset"
    return "none"


def _pull_cell(row: dict[str, Any]) -> str:
    pulls = row.get("next_pull") or []
    if pulls:
        return "; ".join(str(item) for item in pulls)
    if row.get("pull_priority") is None and not pulls:
        decided = False
        decisions = row.get("decisions") if isinstance(row.get("decisions"), dict) else {}
        for key, _label, liner in _GAP_PULLS:
            if liner is None:
                continue
            if decisions.get(key) is not None:
                decided = True
        if not decided:
            return "unset"
    return "—"


def render_markdown(inv: dict[str, Any] | None = None) -> str:
    inv = inv if inv is not None else collect_inventory()
    lock = inv.get("lock") or {}
    contract = inv.get("challenge_true_contract") or {}
    disk = inv.get("disk") or {}
    host = inv.get("host_tape") or {}
    notes = inv.get("assemble_intent") or {}
    account = inv.get("account") or {}
    lines: list[str] = []
    lines.append("# DATA_INVENTORY_ALL_INSTRUMENTS")
    lines.append("")
    lines.append(f"Schema `{inv.get('schema')}`. Generated `{inv.get('generated_at_utc')}`.")
    lines.append(
        f"Challenge login `{account.get('login')}` / `{account.get('ns')}`. "
        f"Sit as-of `{inv.get('sit_as_of_utc')}`. Ticket `{account.get('open_ticket')}` as-of `{inv.get('ticket_as_of_utc')}`."
    )
    lines.append("")
    lines.append("## 0. Scope and lock")
    lines.append("")
    lines.append(
        "Chair ultragoal 2026-09-18: map every instrument GTOS/Challenge can see vs what Jev actually consumes. "
        "Find data gaps that block multi-instrument edge."
    )
    lines.append("")
    lines.append(
        f"- never_place={lock.get('never_place')} never_remint={lock.get('never_remint')} "
        f"never_flatten={lock.get('never_flatten')} never_apply_size={lock.get('never_apply_size')}"
    )
    lines.append(
        f"- never_invent_news_protocol={lock.get('never_invent_news_protocol')} "
        f"never_import_selector_v4={lock.get('never_import_selector_v4')} "
        f"never_import_v4_timewarp={lock.get('never_import_v4_timewarp')}"
    )
    lines.append("- This inventory does not place, remint, flatten, invent NEWS_PROTOCOL, or APPLY size wires.")
    lines.append("- Each symbol decision is the System One return for that state.")
    lines.append("")
    lines.append("## 1. Challenge-true bar contract")
    lines.append("")
    lines.append(f"- `time_utc` = {contract.get('time_utc')}.")
    lines.append(f"- Measured timeframes: `{_seq_text(contract.get('measured_tfs'))}`.")
    lines.append("- The admit contract is the choice on each row.")
    fresh = contract.get("freshness")
    lines.append(f"- Freshness: `{fresh if fresh is not None else 'unset'}`.")
    lines.append(
        f"- April historical is not challenge-true: `{contract.get('april_historical_is_not_challenge_true')}`."
    )
    landing = contract.get("landing")
    if landing is None:
        landing_text = "unset"
    else:
        landing_text = ", ".join(str(item) for item in landing) if landing else "(none)"
    lines.append(f"- Landing dirs: `{landing_text}`. Override: `{contract.get('env_override')}`.")
    lines.append("- File stems: `US30` → `US30_cash`, `UK100` → `UK100_cash`.")
    lines.append("")
    lines.append("## 2. Disk on this clone")
    lines.append("")
    landed = disk.get("landed_challenge_symbols")
    lines.append(f"- Landed Challenge-true symbols: **{_seq_text(landed)}**.")
    lines.append(f"- Non-XAU Challenge books present: **{disk.get('non_xau_books_present')}**.")
    peers = disk.get("vps_named_peer_pull") or []
    crosses = disk.get("chair_cross_pull") or []
    lines.append(
        f"- Chair 2026-09-18 zips `{', '.join(peers)}` + `{', '.join(crosses)}`: "
        f"present_here={disk.get('vps_peer_csvs_on_this_clone')} (box `/workspace/gtos`={disk.get('box_multi_present')})."
    )
    xau_shadow = disk.get("xau_parent_vs_multi") or {}
    lines.append(
        f"- XAU loader search: `{xau_shadow.get('search_order')}`; "
        f"parent_equals_multi={xau_shadow.get('parent_equals_multi')}. "
        f"Bound dir `{xau_shadow.get('bound_dir')}`; multi dir `{xau_shadow.get('multi_dir')}`."
    )
    xau_row = next((row for row in inv.get("jev_rows") or [] if row.get("symbol") == "XAUUSD"), None)
    if xau_row:
        bound = ((xau_row.get("bars") or {}).get("now") or {}).get("m15") or {}
        unused = (xau_row.get("unused_newer_multi") or {}).get("m15") or {}
        fresh = bound.get("fresh_at_as_of")
        bound_state = "fresh" if fresh is True else ("STALE" if fresh is False else "unset")
        admit_now = _yesno((xau_row.get("admit") or {}).get("now"))
        if unused:
            unused_fresh = unused.get("fresh_at_as_of")
            unused_state = "fresh" if unused_fresh is True else ("STALE" if unused_fresh is False else "unset")
            sibling = f"unused multi/ M15 last `{unused.get('last_utc')}` {unused_state} (n={unused.get('n')})"
        else:
            sibling = "no unused newer multi/ sibling"
        lines.append(
            f"- XAU lag vs now `{inv.get('generated_at_utc')}`: bound M15 last `{bound.get('last_utc')}` {bound_state} "
            f"(n={bound.get('n')}); {sibling}; admit_now={admit_now}."
        )
    lines.append(
        f"- Host sit occupied `{host.get('sit_occupied')}`; deals `{host.get('deal_counts')}`; slate `{host.get('slate_counts')}`."
    )
    shadow = host.get("shadow_summary") or {}
    lines.append(
        f"- Last shadow pack: n={shadow.get('n')} sufficient={shadow.get('n_sufficient')} "
        f"xau={shadow.get('n_xau_sufficient')} non_xau={shadow.get('n_non_xau_sufficient')} "
        f"missing_m15={shadow.get('n_missing_m15')}."
    )
    lines.append("")
    lines.append("## 3. Jev / Challenge table")
    lines.append("")
    lines.append("| symbol | bars present | state assembled | scored live | gaps | next pull |")
    lines.append("|---|---|---|---|---|---|")
    for row in inv.get("jev_rows") or []:
        lines.append(
            f"| `{row.get('symbol')}` | {_bars_cell(row)} | {_state_cell(row)} | {_scored_cell(row)} | {_gaps_cell(row)} | {_pull_cell(row)} |"
        )
    lines.append("")
    lines.append(
        "Library hazard: `score_sit` / `score_slate` default `load_gold_books()` (April XAU). "
        "`scripts/jev_challenge_shadow.py` overrides with `load_all_landed_challenge_books()`."
    )
    lines.append("")
    lines.append("## 4. GTOS-wide census")
    lines.append("")
    uni = inv.get("code_universes") or {}
    lines.append(
        f"- `MULTI_SYMBOL_PRIORITY` = `{_seq_text(uni.get('multi_symbol_priority'))}`; "
        f"optional `{_seq_text(uni.get('multi_symbol_optional'))}`."
    )
    gtos_n = "unset" if uni.get("gtos_24") is None else str(len(uni.get("gtos_24") or []))
    lines.append(
        f"- `GTOS_24_SYMBOL_SURFACE` n={gtos_n} matches `VNEXT_24_SYMBOLS`: "
        f"{uni.get('gtos_24_matches_vnext_24')}."
    )
    lines.append(f"- FTMO profile `operator_profile` instruments n={uni.get('ftmo_profile_n')}.")
    lines.append(f"- Armed W7 set (do not rewrite): `{uni.get('armed_w7_sleeves') if uni.get('armed_w7_sleeves') is not None else 'unset'}`.")
    lines.append(
        f"- House hard-off families `{_seq_text(uni.get('house_hard_off_families'))}`; keep `{_seq_text(uni.get('keep_families'))}`."
    )
    lines.append(f"- Occupancy cluster menu `{_seq_text(uni.get('occupancy_cluster_menu'))}`. The cluster on a row is the choice.")
    lines.append("")
    lines.append("| symbol | GTOS-24 | FTMO profile | Jev watch | Challenge landed | April M15 present |")
    lines.append("|---|---|---|---|---|---|")
    for row in inv.get("gtos_census") or []:
        lines.append(
            f"| `{row.get('symbol')}` | {_yesno(row.get('in_gtos_24'))} | {_yesno(row.get('in_ftmo_profile'))} | "
            f"{_yesno(row.get('in_jev_watch'))} | {_yesno(row.get('challenge_landed'))} | {_yesno(row.get('april_m15_present'))} |"
        )
    lines.append("")
    lines.append("Sleeve generator surfaces (code-known, not Challenge-landed):")
    lines.append("")
    surfaces = uni.get("sleeve_surfaces")
    if not isinstance(surfaces, dict):
        lines.append("- unset")
    else:
        for group, mapping in surfaces.items():
            lines.append(f"- **{group}**")
            if isinstance(mapping, dict):
                for tag, symbols in mapping.items():
                    lines.append(f"  - `{tag}`: {', '.join(str(item) for item in symbols)}")
    lines.append("")
    lines.append("Admission registry surfaces:")
    lines.append("")
    admission = uni.get("admission_surfaces")
    if not isinstance(admission, dict):
        lines.append("- unset")
    else:
        for group, mapping in admission.items():
            lines.append(f"- **{group}**")
            if isinstance(mapping, dict):
                for tag, symbols in mapping.items():
                    lines.append(f"  - `{tag}`: {', '.join(str(item) for item in symbols)}")
    lines.append("")
    lines.append("## 5. What assemble / intent builds per symbol")
    lines.append("")
    lines.append(f"- Assembler: `{notes.get('assembler')}`. Schema `{notes.get('schema')}`.")
    lines.append(f"- Sufficiency: {notes.get('sufficiency')}.")
    lines.append(f"- `intent_gold_state`: {notes.get('intent_gold_state')}.")
    lines.append(f"- `books_for_symbol`: {notes.get('books_for_symbol')}.")
    news = notes.get("news") if isinstance(notes.get("news"), dict) else {}
    lines.append(f"- invent NEWS_PROTOCOL={news.get('invent_news_protocol')}.")
    lines.append("- Role, cluster, sleeve, side, prices, spread, admit, gaps, and pulls are the row return.")
    lines.append("")
    lines.append("## 6. Peer PRs (not imported on this branch)")
    lines.append("")
    peers = notes.get("peer_prs_not_on_this_branch") if isinstance(notes.get("peer_prs_not_on_this_branch"), dict) else {}
    lines.append(f"- PR #13: {peers.get('pr_13')}.")
    lines.append(f"- PR #15: {peers.get('pr_15')}.")
    lines.append("- Selector V4 has no symbol universe in this inventory; do not import `selector_v4`.")
    lines.append("")
    lines.append("## 7. Next pull list")
    lines.append("")
    for item in inv.get("next_pull") or []:
        priority = item.get("priority")
        label = priority if priority else "unset"
        lines.append(f"- **{label}** — {item.get('item')}. {item.get('why')}.")
    lines.append("")
    lines.append("## 8. What this inventory does not do")
    lines.append("")
    lines.append("- No place / remint / flatten.")
    lines.append("- No invented NEWS_PROTOCOL.")
    lines.append("- No APPLY size wires.")
    lines.append("- No rewrite of the armed W7 set.")
    lines.append("- No import of `selector_v4` or `v4_timewarp_simulated_live_research_loop`.")
    lines.append("")
    return "\n".join(lines) + "\n"


def _xau_admit_now(inv: Mapping[str, Any]) -> Any:
    for row in inv.get("jev_rows") or []:
        if isinstance(row, Mapping) and row.get("symbol") == "XAUUSD":
            admit = row.get("admit") if isinstance(row.get("admit"), Mapping) else {}
            return admit.get("now")
    return None


def write_markdown(
    path: Path | None = None,
    json_path: Path | None = None,
    *,
    inv: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inv = inv if inv is not None else collect_inventory()
    md_path = path or (REPO_ROOT / "judgment" / "astra" / "DATA_INVENTORY_ALL_INSTRUMENTS.md")
    js_path = json_path or (
        REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "DATA_INVENTORY_ALL_INSTRUMENTS.json"
    )
    md_path.parent.mkdir(parents=True, exist_ok=True)
    js_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(inv), encoding="utf-8")
    js_path.write_text(json.dumps(inv, indent=2, default=str) + "\n", encoding="utf-8")
    landed = (inv.get("disk") or {}).get("landed_challenge_symbols")
    return {
        "schema": SCHEMA,
        "markdown": str(md_path.relative_to(REPO_ROOT) if md_path.is_relative_to(REPO_ROOT) else md_path),
        "json": str(js_path.relative_to(REPO_ROOT) if js_path.is_relative_to(REPO_ROOT) else js_path),
        "n_jev_rows": len(inv.get("jev_rows") or []),
        "n_gtos_census": len(inv.get("gtos_census") or []),
        "landed": None if landed is None else list(landed),
        "non_xau_books_present": (inv.get("disk") or {}).get("non_xau_books_present"),
        "xau_admit_now": _xau_admit_now(inv),
        "parent_equals_multi": ((inv.get("disk") or {}).get("xau_parent_vs_multi") or {}).get("parent_equals_multi"),
        "never_place": True,
        "never_apply_size": True,
    }
