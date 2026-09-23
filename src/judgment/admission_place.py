"""Challenge admission / place-ready / sleeve-select compose.

Owner 2026-09-21: every trading-decision if on Challenge 0 goes
through Jev. This module composes the **admission seat** from one System One
call. The writer (``book_owner`` → ``order_router`` → ``order_send``) still
sends. This file never imports ``order_send`` / ``mt5_real``.

Consume IDs (JEV_EVERYWHERE §3 admission + gold walk JEV_HISTORICAL):
``state_sufficient``, ``flow_alignment``, ``persistence``, ``a8_quality``,
``a8_agrees``, ``geometry_vs_tape``, ``level_respect``, ``cost_hurtful``,
``admit``.

Gold walk: ``ac60>=0.10`` is a coin (core 0.216 vs softband 0.216). Do not
re-encode that cliff. ``persistence`` is the Score on the range.

Envelope walls stay integers (token, occupancy keep-one, already_placed,
2-stop COUNT, $KILL, prop, H8, weekend clock). They are facts on this hop.
Thin facts go to the completeness Noul. W7 books do not take this hop.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .apply_size import is_challenge_account
from .challenge import CHALLENGE_NS
from .family import family_class_for, hard_off_family
from .jev_questions import (
    ADMISSION_SEAT_IDS,
    hierarchical_labels,
    sleeve_select_question,
    spot_question,
    unique_highest,
)

ADMISSION_PLACE_ENV = "GTOS_JEV_ADMISSION_PLACE"

# Admission-seat composite (JEV_EVERYWHERE §2). Gate-worker session_fitness
_FALSY = frozenset({"0", "false", "no", "off"})
ADMISSION_ORDER = ("this_candidate", "not_this_candidate")
ADMISSION_QUESTION = spot_question(
    "admission",
    "This candidate on this bar. Pick one option. Refuse only when not_this_candidate "
    "is the single highest probability. An empty answer or a tie does not refuse. "
    "Do not flatten open gold 294215389.",
    {
        "this_candidate": "This candidate is admitted on this bar.",
        "not_this_candidate": "This candidate is not admitted on this bar.",
    },
)


@dataclass(frozen=True)
class AdmissionPlaceDecision:
    """The admit Choice for this candidate. ``may_place`` reads that Choice. Never sends."""

    may_place: bool
    reason: str
    disposition: str
    admit: str | None = None
    probabilities: dict[str, Any] = field(default_factory=dict)
    unique_highest: bool = False
    probability: float | None = None
    sleeve_choice: str | None = None
    composite: float | None = None
    persist_weight: float | None = None
    skipped: str | None = None
    house_block: bool = False
    state_sufficient: bool | None = None
    answers: dict[str, Any] = field(default_factory=dict)
    extra_questions: dict[str, Any] = field(default_factory=dict)
    seat_ids: tuple[str, ...] = ("admission",)
    never_order_send: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "may_place": self.may_place,
            "reason": self.reason,
            "disposition": self.disposition,
            "admit": self.admit,
            "choice": self.admit,
            "probabilities": dict(self.probabilities),
            "unique_highest": self.unique_highest,
            "probability": self.probability,
            "sleeve_choice": self.sleeve_choice,
            "composite": self.composite,
            "persist_weight": self.persist_weight,
            "skipped": self.skipped,
            "house_block": self.house_block,
            "state_sufficient": self.state_sufficient,
            "seat_ids": list(self.seat_ids),
            "never_order_send": True,
        }


def admission_place_env_on(*, environ: Any = None) -> bool:
    env = environ if environ is not None else os.environ
    raw = str(env.get(ADMISSION_PLACE_ENV, "1")).strip().lower()
    return raw not in _FALSY


def challenge_admission_place_on(
    *,
    login: Any = None,
    ns: Any = None,
    environ: Any = None,
) -> bool:
    """Challenge-only. Explicit 0 disables. W7 ns never arms."""
    if not admission_place_env_on(environ=environ):
        return False
    return is_challenge_account(login=login, ns=ns)


def resolve_owner_login(owner: Any) -> Any:
    """Best-effort MT5 / config login. Never raises."""
    try:
        mt5 = getattr(owner, "_mt5", None)
        if mt5 is not None:
            fn = getattr(mt5, "get_account_login", None)
            if callable(fn):
                try:
                    got = fn()
                    if got is not None:
                        return got
                except Exception:
                    pass
            info = getattr(mt5, "account_info", None)
            if callable(info):
                try:
                    got = getattr(info(), "login", None)
                    if got is not None:
                        return got
                except Exception:
                    pass
        base = getattr(owner, "base_config", None) or {}
        return (base.get("deployment") or {}).get("mt5_login")
    except Exception:
        return None


def _block(answers: dict[str, Any], key: str) -> dict[str, Any]:
    raw = answers.get(key)
    return raw if isinstance(raw, dict) else {}


def _unique_option(raw: Any, order: tuple[str, ...]) -> dict[str, Any]:
    """The decision is the unique highest probability. A label without probabilities is not a decision."""
    block = raw if isinstance(raw, dict) else {}
    probs_in = block.get("probabilities") if isinstance(block.get("probabilities"), dict) else None
    numeric: dict[str, float] = {}
    if isinstance(probs_in, dict):
        for key, val in probs_in.items():
            try:
                numeric[str(key)] = float(val)
            except (TypeError, ValueError):
                continue
    choice = unique_highest(numeric or None, order)
    if choice is None:
        return {
            "choice": None,
            "probabilities": numeric,
            "unique_highest": False,
            "probability": None,
        }
    return {
        "choice": choice,
        "probabilities": numeric,
        "unique_highest": True,
        "probability": numeric.get(choice),
    }


def _choice(answers: dict[str, Any], key: str, order: tuple[str, ...] | None = None) -> str | None:
    block = _block(answers, key)
    probs = block.get("probabilities") if isinstance(block.get("probabilities"), dict) else None
    if order is None and isinstance(probs, dict):
        order = tuple(str(name) for name in probs)
    return unique_highest(probs, order)


def _score(answers: dict[str, Any], key: str) -> float | None:
    raw = _block(answers, key).get("score")
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value != value:  # NaN
        return None
    return value


def _noul(answers: dict[str, Any], key: str) -> bool | float | None:
    raw = _block(answers, key).get("noul")
    if raw is True or raw is False:
        return raw
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value != value:
        return None
    return value


def _noul_true(value: bool | float | None) -> bool | None:
    """A Noul is a probability. Only an actual bool is true or false."""
    if value is True or value is False:
        return value
    return None


def _is_metals(sleeve: str) -> bool:
    return str(sleeve or "").strip().lower().startswith("metals_")


def _a8_k_fact(intent: Any) -> dict[str, Any]:
    """Integer K=3-of-4 as a named fact. Never a refuse."""
    sleeve = str(getattr(intent, "sleeve", "") or "")
    if not _is_metals(sleeve):
        return {"evaluable": False, "k": None, "passed": None, "ignore": True}
    feats = (
        getattr(intent, "htf_slope_norm", None),
        getattr(intent, "mom_20_atr", None),
        getattr(intent, "fvg_freshness_bars", None),
        getattr(intent, "atr_ratio", None),
        getattr(intent, "session_hour", None),
    )
    if any(item is None for item in feats):
        return {"evaluable": False, "k": None, "passed": None, "ignore": False}
    try:
        from src.components.ultimate_book.metals_confluence_gate import metals_confluence

        row = metals_confluence(
            htf_slope_norm=feats[0],
            mom_20_atr=feats[1],
            fvg_freshness_bars=feats[2],
            atr_ratio=feats[3],
            session_hour=feats[4],
            enabled=True,
        )
        return {
            "evaluable": True,
            "k": int(row.score),
            "passed": bool(row.passed),
            "ignore": False,
            "cannot_refuse": True,
        }
    except Exception:
        return {"evaluable": False, "k": None, "passed": None, "ignore": False}


def attach_admission_facts(
    state: dict[str, Any] | None,
    *,
    intent: Any,
    cost_skip: str | None,
    members: list[str] | tuple[str, ...] | None = None,
    unit: Any = None,
) -> dict[str, Any]:
    """Stamp house integers as facts. Do not encode ac60>=0.10."""
    out = dict(state or {})
    identity = dict(out.get("identity") or {})
    sleeve = str(getattr(intent, "sleeve", None) or identity.get("sleeve") or "")
    symbol = str(getattr(intent, "symbol", None) or identity.get("symbol") or "")
    identity.setdefault("sleeve", sleeve)
    identity.setdefault("symbol", symbol)
    identity.setdefault(
        "family_class",
        family_class_for(sleeve, symbol=symbol, origin="f5_challenge"),
    )
    identity.setdefault("origin_organism", "f5_challenge")
    out["identity"] = identity
    feats = dict(out.get("sleeve_features") or {})
    for key in (
        "htf_slope_norm",
        "mom_20_atr",
        "fvg_freshness_bars",
        "atr_ratio",
        "session_hour",
        "vr",
        "ac60",
    ):
        if feats.get(key) is None and getattr(intent, key, None) is not None:
            feats[key] = getattr(intent, key)
    # Raw ac60 is a fact. Do not derive a core/softband boolean from 0.10.
    a8 = _a8_k_fact(intent)
    if feats.get("a8_k_of_4_pass") is None and a8.get("passed") is not None:
        feats["a8_k_of_4_pass"] = a8["passed"]
    out["sleeve_features"] = feats
    cost = dict(out.get("cost") or {})
    cost["cost_screen_would_refuse"] = cost_skip is not None
    if cost_skip is not None:
        cost["cost_skip"] = cost_skip
    out["cost"] = cost
    names = [str(item) for item in (members or ())]
    if not names and isinstance(unit, dict):
        names = [str(item) for item in (unit.get("sleeve_members") or [])]
    out["admission_place"] = {
        "ns": CHALLENGE_NS,
        "cost_skip": cost_skip,
        "sleeve_members": names,
        "a8_k_integer": a8,
        "ac60_cliff_is_coin": True,
        "do_not_reencode_ac60_0_10": True,
        "seat_ids": list(ADMISSION_SEAT_IDS),
        "question_tree_seat": "admission",
    }
    out["labels"] = hierarchical_labels(out, extra={"subgoal": "admission"})
    try:
        from .equity_frame import attach_account

        out = attach_account(out)
    except Exception:
        pass
    return out


def _house_blocked(state: dict[str, Any], intent: Any) -> bool:
    identity = state.get("identity") or {}
    sleeve = str(getattr(intent, "sleeve", None) or identity.get("sleeve") or "")
    symbol = str(getattr(intent, "symbol", None) or identity.get("symbol") or "")
    fact = identity.get("family_class") == "house_hard_off" or bool(
        hard_off_family(sleeve, symbol)
    )
    if not fact:
        return False
    try:
        from .admission_choices import blocks
        return bool(blocks(
            "house_hard_off",
            {"sleeve": sleeve, "symbol": symbol, "family_class": identity.get("family_class")},
        ))
    except Exception:
        return False


def compose_admission_place(
    state: dict[str, Any],
    answers: dict[str, Any] | None,
    *,
    intent: Any = None,
    members: list[str] | tuple[str, ...] | None = None,
    skipped: str | None = None,
) -> AdmissionPlaceDecision:
    """The admit decision is the admit Choice. Scores and walls stay facts."""
    del skipped
    answers = answers or {}
    names = [str(item).strip() for item in (members or ()) if str(item).strip()]
    extra = sleeve_select_question(names if len(names) > 1 else [])
    picked = _unique_option(answers.get("admission"), ADMISSION_ORDER)
    admit = picked["choice"]
    del intent
    try:
        from .gold_priors import applied_persistence_weight

        persist_w = applied_persistence_weight()
    except Exception:
        persist_w = None
    sleeve_order = tuple((extra.get("sleeve_select") or {}).get("criteria") or ())
    return AdmissionPlaceDecision(
        may_place=(admit == "this_candidate"),
        reason="admission_choice" if admit else "no_choice",
        disposition=admit or "no_choice",
        admit=admit,
        probabilities=picked["probabilities"],
        unique_highest=picked["unique_highest"],
        probability=picked["probability"],
        sleeve_choice=_choice(answers, "sleeve_select", sleeve_order) if extra else None,
        composite=None,
        persist_weight=persist_w if answers else None,
        house_block=False,
        state_sufficient=None,
        answers=answers,
        extra_questions=extra,
        seat_ids=tuple(ADMISSION_QUESTION) + (tuple(extra) if extra else ()),
    )


def decide_admission_place(
    *,
    intent: Any,
    tick: Any = None,
    unit: Any = None,
    cost_skip: str | None = None,
    login: Any = None,
    ns: Any = None,
    occupancy: dict[str, Any] | None = None,
    governor: dict[str, Any] | None = None,
    now: datetime | None = None,
    evaluate_jev: bool = True,
    answers: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
    skipped: str | None = None,
) -> AdmissionPlaceDecision:
    """One System One call, then compose. Never sends. Challenge caller only."""
    members: list[str] = []
    if isinstance(unit, dict):
        members = [str(item) for item in (unit.get("sleeve_members") or []) if str(item)]
    if not members and getattr(intent, "sleeve", None):
        members = [str(intent.sleeve)]
    extra = sleeve_select_question(members if len(members) > 1 else [])
    if not is_challenge_account(login=login, ns=ns):
        return AdmissionPlaceDecision(
            may_place=False,
            reason="not_challenge",
            disposition="not_challenge",
            extra_questions=extra,
        )
    packed_state = state
    if packed_state is None and intent is not None:
        try:
            from .a1_log import intent_gold_state

            packed_state = intent_gold_state(
                intent,
                tick,
                origin="f5_challenge",
                as_of_utc=now or datetime.now(timezone.utc),
                occupancy=occupancy,
                governor=governor,
            )
        except Exception:
            packed_state = None
    packed_state = attach_admission_facts(
        packed_state,
        intent=intent,
        cost_skip=cost_skip,
        members=members,
        unit=unit,
    )
    packed_answers = dict(answers or {})
    if answers is None and evaluate_jev:
        try:
            from .jev_client import evaluate

            questions = dict(ADMISSION_QUESTION)
            if extra:
                questions.update(extra)
            try:
                from .jev_questions import prior_outcomes

                packed_state["prior_outcomes"] = prior_outcomes(
                    state=packed_state, questions=questions,
                )
            except Exception:
                pass
            receipt = evaluate(
                packed_state,
                questions=questions,
                merge_sleeve=False,
            ) or {}
            got = receipt.get("answers") if isinstance(receipt, dict) else None
            packed_answers = dict(got) if isinstance(got, dict) else {}
        except Exception:
            packed_answers = {}
    return compose_admission_place(
        packed_state or {},
        packed_answers,
        intent=intent,
        members=members,
        skipped=None,
    )
