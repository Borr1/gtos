"""Apply named live tilts to already-admitted Challenge size. Never refuse.

Physical mutation is env + Challenge-account gated:

  GTOS_JEV_APPLY_LIVE=1 AND (login 0 / ns operator)

F5 units size from ``risk_pct_per_trade`` (``_UnitView`` → router →
``risk_pct_override``). Haircut MUST scale that field (and ``unit_risk_pct``).
Host ``MinimalSizeScaler`` then asks the size hop. An empty answer
stays empty. Flow, cost, ca, and cash are the System One return for
this state. A miss stays unset. ``honor_f5_scaler_risk`` is that hop.
Lot keys are scaled when present. W7 armed books must not be resized.
Absence of login and namespace is not Challenge. Other books are not resized.
Flow, cost, and ca are the returned scores. A missing score stays unset.
Never places.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .compose import COST_TILT_MAX, COST_TILT_MIN, TILT_MAX, TILT_MIN, compose_shadow
from .host_events import as_of_from_state, coerce_as_of_utc, news_inventory_extra
from .process_lock import (
    CA_TILT_MAX,
    CA_TILT_MIN,
    WIRE_CA_SIZE,
    WIRE_COST,
    WIRE_FLOW,
    leave_orig_ticket,
    stamp_lock,
    wire_apply_open,
)

CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0
MODEL = "jev-1.13.0"
_FUNCTION_ORDER = ("returned_score", "last_outcome", "withhold")
_BRANCH_ORDER = ("take", "skip")

# F5 live shape (host verdict B): router reads risk_pct_per_trade, not lots.
_RISK_KEYS = ("risk_pct_per_trade", "unit_risk_pct")
_LOT_KEYS = ("volume", "lots", "units", "size", "qty")
_INTENDED_KEYS = ("f5_intended_risk_usd", "intended_risk_usd", "risk_usd", "cash_risk_usd")
_SCALE_KEYS = _RISK_KEYS + _LOT_KEYS + _INTENDED_KEYS
_JEV_PASSTHROUGH = (
    "jev_combined_live_tilt",
    "jev_risk_pct_before",
    "jev_risk_pct_after",
    "f5_intended_risk_usd",
    "intended_risk_usd",
)

_LOG = logging.getLogger("gtos.judgment.apply_size")
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECEIPT = REPO_ROOT / "judgment" / "astra" / "lab" / "a1" / "apply_receipt.jsonl"
_SECRET_TOKENS = ("api_key", "apikey", "authorization", "secret", "password")


def _number(value: Any) -> float | None:
    """A returned number. Booleans, blanks, and non-finite values stay empty."""

    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _probabilities(raw: Any) -> dict[str, float]:
    block = raw if isinstance(raw, dict) else {}
    probs_in = block.get("probabilities") if isinstance(block.get("probabilities"), dict) else None
    numeric: dict[str, float] = {}
    if isinstance(probs_in, dict):
        for key, val in probs_in.items():
            number = _number(val)
            if number is not None:
                numeric[str(key)] = number
    return numeric


def _unique_name(raw: Any, order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A label without probabilities is not a decision."""

    numeric = _probabilities(raw)
    if not numeric:
        return None
    try:
        from .jev_questions import unique_highest
    except Exception:
        return None
    try:
        choice = unique_highest(numeric, order)
    except Exception:
        return None
    if choice is None or str(choice) not in order:
        return None
    return str(choice)


def _score_block(raw: Any) -> float | None:
    """The numeric score. A tie or a missing score stays empty. Levels are not substituted."""

    numeric = _probabilities(raw)
    if numeric:
        try:
            from .jev_questions import unique_highest

            picked = unique_highest(numeric, tuple(numeric))
        except Exception:
            return None
        if picked is None:
            return None
    block = raw if isinstance(raw, dict) else {}
    return _number(block.get("score"))


def _noul_value(raw: Any) -> bool | float | None:
    """A noul stays a bool or a probability. It is not coerced to a threshold."""

    block = raw if isinstance(raw, dict) else {}
    value = block.get("noul")
    if value is True or value is False:
        return value
    return _number(value)


def _last_logged(key: str) -> float | None:
    try:
        from .jev_questions import last_logged_value
    except Exception:
        return None
    try:
        return _number(last_logged_value(key))
    except Exception:
        return None


def _strip_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        kept: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key).lower().replace("-", "_")
            if any(token in name for token in _SECRET_TOKENS):
                continue
            kept[str(key)] = _strip_secrets(item)
        return kept
    if isinstance(value, list):
        return [_strip_secrets(item) for item in value]
    return value


def apply_questions() -> dict[str, Any]:
    """Tilt and cash card. One ask. Choice, score, and noul only."""

    from .jev_questions import parameter_question, spot_question

    pack: dict[str, Any] = {}
    pack.update(spot_question(
        "apply_function",
        "Which function returns the flow tilt, the cost tilt, the ca tilt, and the cash on this state? "
        "The name you return is the function that runs. "
        "Do not name a number. Never place.",
        {
            "returned_score": (
                "The function is the score hop. Its return is the flow tilt, "
                "the cost tilt, the ca tilt, and the cash."
            ),
            "last_outcome": "The function reads the previous returned tilts and cash and returns those.",
            "withhold": "The function returns no tilt and no cash.",
        },
    ))
    pack.update(spot_question(
        "apply_if",
        "Does this state take the size branch? The name you return is the branch. Never place.",
        {
            "take": "Take the branch. The named function returns the tilts and the cash.",
            "skip": "Do not take the branch. The tilts and the cash stay unset.",
        },
    ))
    pack.update(parameter_question(
        "apply_flow",
        "What flow tilt does this state return? "
        "The score you return is that tilt. It may sit between the levels. Never place.",
    ))
    pack.update(parameter_question(
        "apply_cost",
        "What cost tilt does this state return? "
        "The score you return is that tilt. It may sit between the levels. Never place.",
    ))
    pack.update(parameter_question(
        "apply_ca",
        "What ca tilt does this state return? "
        "The score you return is that tilt. It may sit between the levels. Never place.",
    ))
    pack.update(parameter_question(
        "apply_splice",
        "How many posted answers may sit on this state before the catalog is leftover? "
        "The score you return is that bound. Never place.",
    ))
    pack["cost_hurtful"] = {
        "type": "noul",
        "instructions": (
            "Is the cost on this already-admitted unit hurtful? "
            "The noul you return is that answer. Never place."
        ),
        "criteria": {
            "true": "The cost on this unit is hurtful.",
            "false": "The cost on this unit is not hurtful.",
        },
    }
    return pack


def _returned_unit(payload: Mapping[str, Any]) -> float | None:
    """unit_usd already returned for this state. A posted empty score stays empty."""

    if "apply_cash" in payload:
        return _score_block(payload.get("apply_cash"))
    if "unit_usd" in payload:
        return _score_block(payload.get("unit_usd"))
    return _last_logged("unit_usd")


def _applied_tilts(answers: Mapping[str, Any] | None) -> dict[str, Any]:
    """Run the function and the branch. A skip, a tie, or a missing score leaves the numbers unset."""

    payload = answers if isinstance(answers, Mapping) else {}
    function_name = _unique_name(payload.get("apply_function"), _FUNCTION_ORDER)
    branch = _unique_name(payload.get("apply_if"), _BRANCH_ORDER)
    flow = cost = ca = cash = None
    if function_name == "withhold" or branch == "skip":
        pass
    elif function_name == "last_outcome" and branch == "take":
        flow = _last_logged("apply_flow")
        cost = _last_logged("apply_cost")
        ca = _last_logged("apply_ca")
        cash = _returned_unit(payload)
    elif function_name == "returned_score" and branch == "take":
        flow = _score_block(payload.get("apply_flow"))
        cost = _score_block(payload.get("apply_cost"))
        ca = _score_block(payload.get("apply_ca"))
        cash = _returned_unit(payload)
    else:
        # Empty function or branch. Tilts stay unset. The returned unit still stands.
        cash = _returned_unit(payload)
    splice = _score_block(payload.get("apply_splice"))
    blocked = splice is not None and len(payload) >= splice
    if blocked:
        flow = cost = ca = cash = None
    return {
        "apply_function": function_name,
        "apply_if": branch,
        "flow": flow,
        "cost": cost,
        "ca": ca,
        "size_cash": cash,
        "splice_bound": splice,
        "blocked": blocked,
        "cost_hurtful": _noul_value(payload.get("cost_hurtful")),
    }


def _remember_apply(
    state: Mapping[str, Any],
    card: Mapping[str, Any],
    error: Any = None,
) -> None:
    """The returns just run are the next ask's history. A miss is stored as empty."""

    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    logged = _strip_secrets(dict(state))
    logged.pop("prior_outcomes", None)
    rows = (
        ("apply_flow", card.get("flow")),
        ("apply_cost", card.get("cost")),
        ("apply_ca", card.get("ca")),
    )
    for key, value in rows:
        try:
            append_outcome(
                key,
                value,
                logged,
                error=None if value is not None else error,
            )
        except Exception:
            continue


def _apply_state(
    row: Mapping[str, Any] | None,
    *,
    ticket: Any = None,
    state: Mapping[str, Any] | None = None,
    symbol: Any = None,
    sleeve: Any = None,
    login: Any = None,
    ns: Any = None,
    unit: Any = None,
) -> dict[str, Any]:
    base = dict(state or {})
    facts = dict(row or {})
    for key in (
        "live_size_tilt",
        "live_cost_tilt",
        "live_ca_size_tilt",
        "jev_combined_live_tilt",
        "f5_intended_risk_usd",
        "intended_risk_usd",
    ):
        facts.pop(key, None)
    base["gate"] = "apply_size"
    base["model"] = MODEL
    if login is not None:
        base["login"] = login
    if ns is not None:
        base["namespace"] = ns
    if ticket is not None:
        base["ticket"] = ticket
    if symbol is not None:
        base["symbol"] = symbol
    if sleeve is not None:
        base["sleeve"] = sleeve
    identity = dict(base.get("identity") or {}) if isinstance(base.get("identity"), dict) else {}
    identity.setdefault("login", login)
    identity.setdefault("namespace", ns)
    identity.setdefault("ticket", ticket)
    identity.setdefault("symbol", symbol if symbol is not None else base.get("symbol"))
    identity.setdefault("sleeve", sleeve if sleeve is not None else base.get("sleeve"))
    base["identity"] = identity
    base["compose_facts"] = facts
    if unit is not None:
        snap = unit_size_snapshot(unit)
        snap.pop("f5_intended_risk_usd", None)
        snap.pop("intended_risk_usd", None)
        base["unit_before"] = snap
    base.setdefault(
        "clock",
        {"as_of_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
    )
    return base


def _ask_apply(state: Mapping[str, Any] | None) -> dict[str, Any]:
    """One existing evaluate() call. Priors go in on this ask. No second client."""

    packed = _strip_secrets(dict(state or {}))
    packed.pop("prior_outcomes", None)
    packed["model"] = MODEL
    packed["gate"] = "apply_size"
    try:
        questions = apply_questions()
    except Exception as exc:
        return {
            "ok": False,
            "source": "question_pack_fail",
            "error": type(exc).__name__,
            "answers": {},
            "state": packed,
        }
    try:
        from .equity_frame import attach_account

        attached = attach_account(packed)
        if isinstance(attached, dict):
            packed = attached
    except Exception:
        pass
    packed["model"] = MODEL
    packed["gate"] = "apply_size"
    try:
        from .jev_questions import hierarchical_labels

        packed["labels"] = hierarchical_labels(packed, extra={"subgoal": "apply_size"})
    except Exception:
        pass
    try:
        from .jev_questions import prior_outcomes

        packed["prior_outcomes"] = prior_outcomes(state=packed, questions=questions)
    except Exception:
        packed.setdefault("prior_outcomes", [])
    try:
        from .jev_client import evaluate
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "source": "jev_client_import_fail",
            "error": type(exc).__name__,
            "answers": {},
            "state": packed,
        }
    try:
        receipt = evaluate(
            packed,
            questions=questions,
            merge_sleeve=False,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "source": "evaluate_raise",
            "error": type(exc).__name__,
            "answers": {},
            "state": packed,
        }
    if not isinstance(receipt, dict):
        receipt = {}
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None if answers else (receipt.get("error") or receipt.get("skipped") or "empty")
    return {
        "ok": bool(answers),
        "source": "apply_hop",
        "error": error,
        "answers": answers,
        "state": packed,
        "model": receipt.get("model") or MODEL,
    }


def apply_live_env() -> bool:
    return os.environ.get("GTOS_JEV_APPLY_LIVE", "").strip().lower() in {"1", "true", "yes"}


def is_challenge_account(*, login: Any = None, ns: Any = None) -> bool:
    ns_ok = str(ns or "").strip() == CHALLENGE_NS
    login_ok = False
    if login is not None and str(login).strip() != "":
        try:
            login_ok = int(login) == CHALLENGE_LOGIN
        except (TypeError, ValueError):
            login_ok = False
    if login is None and ns is None:
        return False
    if login is not None and ns is not None and str(login).strip() != "" and str(ns).strip() != "":
        return login_ok and ns_ok
    return login_ok or ns_ok


def physical_apply_allowed(*, login: Any = None, ns: Any = None, ticket: Any = None) -> bool:
    if leave_orig_ticket(ticket):
        return False
    if not apply_live_env():
        return False
    return is_challenge_account(login=login, ns=ns)


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _scaler_target_usd(
    scaler: Any,
    trade_params: dict[str, Any] | None,
    target_risk_usd: Any = None,
) -> float | None:
    got = _float_or_none(target_risk_usd)
    if got is not None:
        return got
    params = trade_params or {}
    details = params.get("gtos_vnext_source_event_details")
    symbol = params.get("symbol")
    sleeve = params.get("sleeve")
    if sleeve in (None, "") and isinstance(details, dict):
        sleeve = details.get("sleeve")
    if scaler is not None:
        fn = getattr(scaler, "risk_usd_for", None)
        if callable(fn):
            try:
                got = _float_or_none(fn(symbol, sleeve))
                if got is not None:
                    return got
            except Exception:
                pass
        got = _float_or_none(getattr(scaler, "target_risk_usd", None))
        if got is not None:
            return got
    return None


def f5_scaler_should_honor(
    *,
    login: Any = None,
    ns: Any = None,
    ticket: Any = None,
    scaler: Any = None,
) -> bool:
    """Challenge APPLY only. Host scaler object is itself the F5 seam."""
    if leave_orig_ticket(ticket):
        return False
    if not apply_live_env():
        return False
    if ns is not None and str(ns).strip() != "" and not is_challenge_account(login=login, ns=ns):
        return False
    if login is not None and str(login).strip() != "" and not is_challenge_account(login=login, ns=ns):
        return False
    if physical_apply_allowed(login=login, ns=ns, ticket=ticket):
        return True
    return scaler is not None


def honor_f5_scaler_risk(
    nominal: Any,
    *,
    scaler: Any = None,
    trade_params: dict[str, Any] | None = None,
    login: Any = None,
    ns: Any = None,
    ticket: Any = None,
    target_risk_usd: Any = None,
) -> tuple[float | None, dict[str, Any]]:
    """Map the size hop onto the next unit. Never places.

    The cash is the returned parameter. An empty answer stays empty.
    """
    params = trade_params if isinstance(trade_params, dict) else {}
    nominal_f = _float_or_none(nominal)
    target = _scaler_target_usd(scaler, params, target_risk_usd)
    tilt = _float_or_none(params.get("jev_combined_live_tilt"))
    if ticket is None:
        ticket = params.get("ticket") or params.get("candidate_id")
    if ns is None:
        ns = params.get("namespace") or params.get("profile_namespace")
    honored = target
    used = "scaler_target" if target is not None else "size_not_decided"
    choice_row: dict[str, Any] | None = None
    if is_challenge_account(login=login, ns=ns):
        # The next unit's cash is the returned parameter. A miss stays unset.
        try:
            from .size_exit import choose_size_and_persist

            choice_row = choose_size_and_persist(
                {
                    "login": login,
                    "namespace": ns,
                    "open_ticket": ticket,
                    "launcher_f5_minimal_size_usd": target,
                    "launcher_notional_initial_usd": getattr(
                        getattr(scaler, "_cfg", None), "notional_initial_usd", None
                    ),
                }
            )
        except Exception as exc:  # noqa: BLE001 — a miss stays unset
            choice_row = {"size_decided": False, "error": type(exc).__name__}
        if choice_row.get("size_decided") and choice_row.get("cash_usd") is not None:
            honored = float(choice_row["cash_usd"])
            used = "size_choice"
        else:
            honored = None
            used = "size_not_decided"
    elif f5_scaler_should_honor(login=login, ns=ns, ticket=ticket, scaler=scaler):
        if tilt is not None and target is not None:
            honored = target * tilt
            used = "target_times_tilt"
        elif tilt is None and nominal_f is not None and nominal_f > 0:
            honored = nominal_f
            used = "haircutted_nominal"
        else:
            honored = None
            used = "size_not_decided"
    stamp = {
        "f5_nominal_risk_usd": _float_or_none(nominal_f),
        "f5_intended_risk_usd": _float_or_none(honored),
        "intended_risk_usd": _float_or_none(honored),
        "jev_combined_live_tilt": tilt,
        "f5_scaler_honor": used,
        "size_alternative": None if choice_row is None else choice_row.get("size_alternative"),
        "size_function": None if choice_row is None else choice_row.get("size_function"),
        "size_if": None if choice_row is None else choice_row.get("size_if"),
        "loop_bound": None if choice_row is None else choice_row.get("loop_bound"),
        "persist_weight": None if choice_row is None else choice_row.get("returned_weight"),
        "unit_usd": None if choice_row is None else choice_row.get("returned_unit_usd"),
        "printed_unit_usd": None if choice_row is None else choice_row.get("returned_unit_usd"),
        "printed_persist_weight": None if choice_row is None else choice_row.get("returned_weight"),
        "size_decided": False if choice_row is None else bool(choice_row.get("size_decided")),
        "persist_decided": False if choice_row is None else bool(choice_row.get("persist_decided")),
    }
    if scaler is not None:
        try:
            scaler.last = dict(stamp)
        except Exception:
            pass
    if honored is None:
        return None, stamp
    return float(honored), stamp


def apply_f5_scaler_to_risk_amount(
    risk_amount: Any,
    *,
    engine: Any = None,
    trade_params: dict[str, Any] | None = None,
    scaler: Any = None,
    login: Any = None,
    ns: Any = None,
    ticket: Any = None,
) -> float:
    """open_trade hook. No-op when the host F5 scaler is absent (W7)."""
    if scaler is None and engine is not None:
        scaler = getattr(engine, "_f5_scaler", None)
    if scaler is None:
        return float(risk_amount)
    params = trade_params if isinstance(trade_params, dict) else {}
    if login is None and engine is not None:
        mt5 = getattr(engine, "mt5", None)
        if mt5 is not None:
            fn = getattr(mt5, "get_account_login", None)
            if callable(fn):
                try:
                    login = fn()
                except Exception:
                    login = None
            if login is None:
                info = getattr(mt5, "account_info", None)
                if callable(info):
                    try:
                        login = getattr(info(), "login", None)
                    except Exception:
                        login = None
    if ns is None and engine is not None:
        ns = getattr(engine, "_runtime_namespace", None)
    honored, stamp = honor_f5_scaler_risk(
        risk_amount,
        scaler=scaler,
        trade_params=params,
        login=login,
        ns=ns,
        ticket=ticket,
    )
    if isinstance(trade_params, dict):
        trade_params.update(stamp)
    return honored


class MinimalSizeScaler:
    """Host-compatible F5 dollar scaler that honors a Challenge haircut.

    Chair: copy ``scaled_risk_amount`` into the dirty-host class. Do not
    wholesale-replace host ``execution.py`` / scaler if ``risk_usd_for``
    has CLI/cfg sleeves. Never places.
    """

    def __init__(
        self,
        target_risk_usd: float | None = None,
        *,
        login: Any = None,
        ns: Any = None,
    ) -> None:
        self.target_risk_usd = None if target_risk_usd is None else float(target_risk_usd)
        self.login = login
        self.ns = ns
        self.last: dict[str, Any] = {}

    def risk_usd_for(self, symbol: Any = None, sleeve: Any = None) -> float | None:
        if self.target_risk_usd is None:
            return None
        return float(self.target_risk_usd)

    def scaled_risk_amount(self, nominal: Any, trade_params: dict[str, Any] | None = None) -> float | None:
        honored, _stamp = honor_f5_scaler_risk(
            nominal,
            scaler=self,
            trade_params=trade_params,
            login=self.login,
            ns=self.ns,
        )
        return honored


def _clamp_open(number: float | None, lo: float, hi: float, *, open_wire: bool) -> tuple[float | None, bool]:
    """The returned score. Bounds and a closed wire do not clip it or invent one."""

    del lo, hi, open_wire
    if number is None:
        return None, True
    return float(number), False


def apply_named_tilts(
    compose_row: dict[str, Any] | None,
    *,
    ticket: Any = None,
    leave_orig: bool | None = None,
    answers: Mapping[str, Any] | None = None,
    state: Mapping[str, Any] | None = None,
    evaluate_jev: bool = True,
    symbol: Any = None,
    sleeve: Any = None,
    login: Any = None,
    ns: Any = None,
    unit: Any = None,
) -> dict[str, Any]:
    """Judgment receipt. Does not mutate a broker unit.

    On Challenge the ask runs. Leave-orig, a shadow sleeve, and a closed wire
    are facts on that ask. The returned scores are the tilts. An empty answer
    does not become an identity.
    """

    row = dict(compose_row or {})
    ticket = ticket if ticket is not None else row.get("leave_orig_ticket")
    if leave_orig is None:
        leave_orig = bool(row.get("leave_orig")) or leave_orig_ticket(ticket)
    from .aplus_sleeve import is_aplus_shadow_only

    aplus_shadow = is_aplus_shadow_only(compose_row, compose_row=row, sleeve=row.get("sleeve"))
    named_apply_symbol = row.get("named_apply_symbol")
    apply_flow = wire_apply_open(WIRE_FLOW, ticket=ticket)
    apply_cost = wire_apply_open(WIRE_COST, ticket=ticket)
    apply_ca = wire_apply_open(WIRE_CA_SIZE, ticket=ticket)
    challenge = is_challenge_account(login=login, ns=ns)
    row["leave_orig"] = bool(leave_orig)
    row["aplus_shadow"] = bool(aplus_shadow)
    row["named_apply_symbol"] = named_apply_symbol
    row["wire_flow_open"] = bool(apply_flow)
    row["wire_cost_open"] = bool(apply_cost)
    row["wire_ca_open"] = bool(apply_ca)
    need = challenge or bool(apply_flow or apply_cost or apply_ca)
    if not challenge and (named_apply_symbol is False or aplus_shadow or leave_orig):
        need = False
    card: dict[str, Any] = {
        "apply_function": None,
        "apply_if": None,
        "flow": None,
        "cost": None,
        "ca": None,
        "size_cash": None,
        "splice_bound": None,
        "blocked": False,
        "cost_hurtful": None,
    }
    if need and answers is None and evaluate_jev:
        ask_state = _apply_state(
            row,
            ticket=ticket,
            state=state,
            symbol=symbol,
            sleeve=sleeve,
            login=login,
            ns=ns,
            unit=unit,
        )
        asked = _ask_apply(ask_state)
        answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
        card = _applied_tilts(answers)
        _remember_apply(asked.get("state") or ask_state, card, error=asked.get("error"))
    elif need:
        card = _applied_tilts(answers)
        if answers is not None:
            _remember_apply(
                dict(state or {}),
                card,
                error=None if card.get("apply_function") else "empty",
            )
    flow, flow_missing = _clamp_open(card.get("flow"), TILT_MIN, TILT_MAX, open_wire=apply_flow)
    cost, cost_missing = _clamp_open(
        card.get("cost"), COST_TILT_MIN, COST_TILT_MAX, open_wire=apply_cost,
    )
    ca, ca_missing = _clamp_open(card.get("ca"), CA_TILT_MIN, CA_TILT_MAX, open_wire=apply_ca)
    size_cash = card.get("size_cash")
    if flow_missing or cost_missing or ca_missing:
        combined: float | None = None
    else:
        combined = float(flow) * float(cost) * float(ca)
    return {
        **stamp_lock(),
        "ticket": ticket,
        "leave_orig": bool(leave_orig),
        "flow": flow,
        "cost": cost,
        "ca": ca,
        "combined": combined,
        "size_cash": size_cash,
        "apply_function": card.get("apply_function"),
        "apply_if": card.get("apply_if"),
        "cost_hurtful": card.get("cost_hurtful"),
        "splice_bound": card.get("splice_bound"),
        "blocked": bool(card.get("blocked")),
        "model": MODEL,
        "ca_apply": bool(apply_ca),
        "ca_live": ca,
        "ca_ignored": not apply_ca,
        "apply_this_row": need,
        "cannot_refuse": True,
        "physical_size_stays_flow_x_cost": not apply_ca,
        "physical_size_stays_flow_x_cost_x_ca": True,
        WIRE_CA_SIZE: {"apply": apply_ca, "live": ca},
    }


def unit_size_snapshot(unit: Any) -> dict[str, Any]:
    """Non-secret size fields only. Used for apply receipts."""
    snap: dict[str, Any] = {}
    for key in _SCALE_KEYS:
        if isinstance(unit, dict) and key in unit and unit[key] is not None:
            snap[key] = unit[key]
        elif not isinstance(unit, dict) and hasattr(unit, key):
            value = getattr(unit, key)
            if value is not None:
                snap[key] = value
    if isinstance(unit, (int, float)) and not isinstance(unit, bool):
        snap["scalar"] = unit
    return snap


def _scale_number(value: Any, mult: float) -> Any:
    try:
        number = float(value) * mult
    except (TypeError, ValueError):
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        if abs(value) >= 1 and abs(number) >= 1:
            return int(round(number)) if abs(number - round(number)) < 1e-9 else number
        return number
    return number


def _scale_unit(unit: Any, mult: float) -> Any:
    if isinstance(unit, bool):
        return unit
    if isinstance(unit, int):
        scaled = unit * mult
        if isinstance(scaled, float) and abs(scaled - round(scaled)) < 1e-9:
            return int(round(scaled))
        return scaled
    if isinstance(unit, float):
        return unit * mult
    if isinstance(unit, dict):
        out = dict(unit)
        for key in _SCALE_KEYS:
            if key in out and out[key] is not None:
                out[key] = _scale_number(out[key], mult)
        return out
    for attr in _SCALE_KEYS:
        if hasattr(unit, attr):
            try:
                setattr(unit, attr, _scale_number(getattr(unit, attr), mult))
            except Exception:
                pass
    return unit


def _receipt_path() -> Path:
    override = (os.environ.get("GTOS_JEV_APPLY_RECEIPT_PATH") or "").strip()
    return Path(override) if override else DEFAULT_RECEIPT


def write_apply_receipt(row: dict[str, Any]) -> None:
    """One-line apply receipt. No secrets. Safe if disk is missing."""
    _LOG.info(
        "JEV_APPLY receipt symbol=%s sleeve=%s ticket=%s tilt=%s before=%s after=%s",
        row.get("symbol"),
        row.get("sleeve"),
        row.get("ticket"),
        row.get("combined_live_tilt"),
        row.get("unit_before"),
        row.get("unit_after"),
    )
    try:
        path = _receipt_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, default=str) + "\n")
    except Exception:
        return


def maybe_haircut_unit(
    unit: Any,
    compose_row: dict[str, Any] | None = None,
    *,
    ticket: Any = None,
    login: Any = None,
    ns: Any = None,
    already_admitted: bool = True,
    symbol: Any = None,
    sleeve: Any = None,
    answers: Mapping[str, Any] | None = None,
    evaluate_jev: bool = True,
    state: Mapping[str, Any] | None = None,
) -> Any:
    """Physical hook. Challenge asks. Other books are returned unchanged."""
    if not is_challenge_account(login=login, ns=ns):
        return unit
    if symbol is None and isinstance(unit, dict):
        symbol = unit.get("symbol")
    row = dict(compose_row or {})
    row["already_admitted"] = bool(already_admitted)
    named = apply_named_tilts(
        row,
        ticket=ticket,
        answers=answers,
        state=state,
        evaluate_jev=evaluate_jev,
        symbol=symbol,
        sleeve=sleeve,
        login=login,
        ns=ns,
        unit=unit,
    )
    if not named["apply_this_row"]:
        return unit
    cash = named.get("size_cash")
    combined = named.get("combined")
    if combined is None and cash is None:
        return unit
    if symbol is None and isinstance(unit, dict):
        symbol = unit.get("symbol")
    if sleeve is None and isinstance(unit, dict):
        sleeve = unit.get("sleeve") or unit.get("cluster")
        members = unit.get("sleeve_members")
        if sleeve in (None, "", "book") and isinstance(members, (list, tuple)) and members:
            sleeve = members[0]
    before = unit_size_snapshot(unit)
    if combined is None:
        if not isinstance(unit, dict):
            return unit
        scaled = dict(unit)
    else:
        scaled = _scale_unit(unit, combined)
    after = unit_size_snapshot(scaled)
    if isinstance(scaled, dict):
        if combined is not None:
            scaled["jev_combined_live_tilt"] = combined
            scaled["jev_risk_pct_before"] = before.get("risk_pct_per_trade")
            scaled["jev_risk_pct_after"] = after.get("risk_pct_per_trade")
        scaled["f5_intended_risk_usd"] = cash
        scaled["intended_risk_usd"] = cash
    write_apply_receipt(
        {
            "schema": "gtos.judgment.apply_receipt.v0",
            "logged_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "symbol": symbol,
            "sleeve": sleeve,
            "ticket": ticket or named.get("ticket"),
            "combined_live_tilt": combined,
            "flow": named.get("flow"),
            "cost": named.get("cost"),
            "ca": named.get("ca"),
            "ca_apply": named.get("ca_apply", False),
            "cost_hurtful": named.get("cost_hurtful"),
            "model": named.get("model") or MODEL,
            "unit_before": before,
            "unit_after": after,
            "f5_intended_risk_usd": cash,
            "never_place": True,
            "never_remint": True,
            "never_flatten": True,
        }
    )
    return scaled


def haircut_challenge_unit(
    unit: Any,
    *,
    intent: Any = None,
    tick: Any = None,
    state: dict[str, Any] | None = None,
    answers: dict[str, Any] | None = None,
    ticket: Any = None,
    login: Any = None,
    ns: Any = None,
    already_admitted: bool = True,
    evaluate_jev: bool = True,
    books: dict[str, Any] | None = None,
    as_of_utc: Any = None,
    occupancy: dict[str, Any] | None = None,
    governor: dict[str, Any] | None = None,
) -> Any:
    """Compose (optional Jev answers) then haircut. Challenge-gated inside.

    Host splice: after cost_skip is None, call this instead of
    compose_shadow(state, None) + maybe_haircut_unit. Pass occupancy=
    and governor= from host_occupancy_governor (open book / closed[] /
    decision.governor). Do not wholesale-copy GitHub book_owner.py onto
    the dirty 10069-line host.

    Live compose gets host writer inventory via ``news_inventory_extra``
    (same fields ``challenge_shadow`` already stamps). Lab tape is not live.
    """
    if ticket is None:
        ticket = getattr(intent, "ticket", None) or getattr(intent, "candidate_id", None)
    if state is None and intent is not None:
        from .a1_log import intent_gold_state

        state = intent_gold_state(
            intent,
            tick,
            origin="f5_challenge",
            books=books,
            as_of_utc=as_of_utc,
            occupancy=occupancy,
            governor=governor,
        )
    packed = answers
    as_of = coerce_as_of_utc(as_of_utc) or as_of_from_state(state)
    extra = news_inventory_extra(as_of, live=True)
    composed = compose_shadow(state or {}, packed or {}, ticket=ticket, extra=extra)
    symbol = getattr(intent, "symbol", None) if intent is not None else None
    sleeve = getattr(intent, "sleeve", None) if intent is not None else None
    if symbol is None and isinstance(state, dict):
        symbol = ((state.get("identity") or {}).get("symbol"))
    if sleeve is None and isinstance(state, dict):
        sleeve = ((state.get("identity") or {}).get("sleeve"))
    return maybe_haircut_unit(
        unit,
        composed,
        ticket=ticket,
        login=login,
        ns=ns,
        already_admitted=already_admitted,
        symbol=symbol,
        sleeve=sleeve,
        answers=answers,
        evaluate_jev=evaluate_jev and answers is None,
        state=state,
    )
