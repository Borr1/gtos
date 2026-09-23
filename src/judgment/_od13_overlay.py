"""OD-13 overlay for place_choice — Dig Land D land 2026-09-21.

Evidence Noul + K=3 option-order shuffle ensemble under PLACE_APPLY +
CONF_ORDER_CONSUME + Dig B high_trust_blocked_for_place. SHADOW-safe. Dig Land D never broker-sends.
Never invent NEWS. Never order_send. pack1b_beaten=false.

Env: GTOS_JEV_PLACE_ENSEMBLE=1 enables (default ON when PLACE_APPLY=1;
explicit 0/false/off disables). Fail-closed DELAY if Typesafe dark
(handled by caller). Do not trust raw API conf alone (OD-07).
"""
from __future__ import annotations

import os
from typing import Any, Mapping

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_FALSY = frozenset({"0", "false", "no", "off"})
PLACE_KEYS = frozenset({"PLACE", "STAND", "DELAY", "REMINT", "FLATTEN_CANDIDATE"})


def place_ensemble_enabled(environ: Mapping[str, str] | None = None) -> bool:
    """GTOS_JEV_PLACE_ENSEMBLE=1 to enable; default on when PLACE_APPLY=1."""
    env = environ if environ is not None else os.environ
    explicit = str(env.get("GTOS_JEV_PLACE_ENSEMBLE", "")).strip().lower()
    if explicit in _FALSY:
        return False
    if explicit in _TRUTHY:
        return True
    apply = str(env.get("GTOS_JEV_PLACE_APPLY", "")).strip().lower()
    return apply in _TRUTHY


def _noul_p_from_answers(answers: Mapping[str, Any] | None) -> float | None:
    """Extract Noul place probability; never trust raw vendor conf alone (OD-07)."""
    if not answers or not isinstance(answers, dict):
        return None
    # Prefer explicit noul / place_now; skip bare "confidence" / "conf"
    for key in ("place_now", "noul_place", "noul_place_p", "place_noul"):
        raw = answers.get(key)
        if isinstance(raw, dict):
            for fk in ("noul", "p", "probability", "answer", "value"):
                if fk in raw and fk not in {"confidence", "conf"}:
                    try:
                        return float(raw[fk])
                    except (TypeError, ValueError):
                        pass
        elif raw is not None:
            try:
                return float(raw)
            except (TypeError, ValueError):
                pass
    # state_sufficient as binary proxy only when noul absent — not API conf
    ss = answers.get("state_sufficient")
    if isinstance(ss, dict):
        ss_v = ss.get("answer", ss.get("noul", ss.get("value")))
    else:
        ss_v = ss
    if ss_v is False or str(ss_v).lower() in {"false", "no", "0"}:
        return 0.0
    return None


def _state_sufficient_fail(answers: Mapping[str, Any] | None, state: Mapping[str, Any]) -> bool:
    if state.get("state_evidence_sufficiency_pass") is False:
        return True
    if not answers or not isinstance(answers, dict):
        return False
    ss = answers.get("state_sufficient")
    if isinstance(ss, dict):
        ss_v = ss.get("answer", ss.get("noul", ss.get("value")))
    else:
        ss_v = ss
    if ss_v is False or str(ss_v).lower() in {"false", "no", "0"}:
        return True
    return False


def od13_ensemble_overlay(
    state: dict[str, Any],
    *,
    action: str,
    answers: Mapping[str, Any] | None = None,
    place_criteria: Mapping[str, str] | None = None,
    environ: Mapping[str, str] | None = None,
    typesafe_ok: bool = True,
) -> dict[str, Any]:
    """Thin / sufficiency fail → DELAY; else Noul + K3 ensemble; PLACE→DELAY on order block.

    When ensemble disabled, passthrough action. When Typesafe dark, DELAY fail-closed.
    """
    if not place_ensemble_enabled(environ):
        raw_off = str(action or "DELAY").upper()
        # Dig B expand: high_trust_blocked_for_place still refuses PLACE when ensemble off
        blocked = bool(
            state.get("high_trust_blocked_for_place")
            or state.get("order_sensitivity_blocks_high")
            or state.get("conf_order_consume_block")
        )
        if blocked and raw_off == "PLACE":
            return {
                "action": "DELAY",
                "refuse_place": True,
                "od13": {
                    "ok": True,
                    "skipped": "ensemble_off",
                    "reason": "high_trust_blocked_for_place",
                    "conf_order_consume": "PLACE_to_DELAY",
                    "place": False,
                    "apply": False,
                    "shadow": True,
                },
                "od13_overlay": True,
                "ensemble_enabled": False,
                "pattern": "place_choice_ensemble_noul_pair",
            }
        return {
            "action": action,
            "refuse_place": str(action).upper() in {"STAND", "DELAY"},
            "od13": {"ok": False, "skipped": "ensemble_off"},
            "od13_overlay": False,
            "ensemble_enabled": False,
        }

    if not typesafe_ok:
        return {
            "action": "DELAY",
            "refuse_place": True,
            "od13": {
                "ok": False,
                "reason": "typesafe_dark_fail_closed",
                "pattern": "place_choice_ensemble_noul_pair",
            },
            "od13_overlay": True,
            "ensemble_enabled": True,
            "pattern": "place_choice_ensemble_noul_pair",
        }

    try:
        from .dig_a_place_choice_ensemble_noul_pair import (
            ensemble_place_choice,
            PLACE_CRITERIA as OD13_CRIT,
        )
    except Exception:
        try:
            from dig_a_place_choice_ensemble_noul_pair import (  # type: ignore
                ensemble_place_choice,
                PLACE_CRITERIA as OD13_CRIT,
            )
        except Exception as exc:
            return {
                "action": "DELAY",
                "refuse_place": True,
                "od13": {"ok": False, "error": type(exc).__name__, "reason": "ensemble_import_fail"},
                "od13_overlay": False,
                "ensemble_enabled": True,
            }

    crit = dict(place_criteria or OD13_CRIT)
    st = dict(state)

    # Align CONF_ORDER_CONSUME: sufficiency fail → DELAY before ensemble
    if _state_sufficient_fail(answers, st):
        return {
            "action": "DELAY",
            "refuse_place": True,
            "od13": {
                "ok": True,
                "pattern": "place_choice_ensemble_noul_pair",
                "action": "DELAY",
                "reason": "state_sufficient_fail_conf_order_consume",
                "evidence_score": None,
                "noul_place_p": None,
                "ensemble_pick": None,
                "conf_order_consume": "sufficiency_fail_DELAY",
                "place": False,
                "apply": False,
                "shadow": True,
            },
            "od13_overlay": True,
            "ensemble_enabled": True,
            "pattern": "place_choice_ensemble_noul_pair",
        }

    noul_p = _noul_p_from_answers(answers)
    if noul_p is not None:
        st["_mock_noul_place_p"] = noul_p
    if st.get("discriminating_span") in (None, ""):
        span = st.get("place_context", {})
        if isinstance(span, dict) and span.get("discriminating_span"):
            st["discriminating_span"] = span["discriminating_span"]
        elif answers and isinstance(answers, dict):
            disc = answers.get("discriminating_span") or answers.get("span")
            if isinstance(disc, dict):
                disc = disc.get("answer") or disc.get("value") or disc.get("text")
            if disc not in (None, ""):
                st["discriminating_span"] = disc

    # Optional mock_dists from answers.place_menu_dists keyed by option_order_hash
    mock_dists = None
    if answers and isinstance(answers, dict):
        md = answers.get("place_menu_dists") or answers.get("ensemble_dists")
        if isinstance(md, dict):
            mock_dists = md

    ens = ensemble_place_choice(st, criteria=crit, mock_dists=mock_dists)
    ens_action = str(ens.get("action") or "DELAY").upper()
    if ens_action not in PLACE_KEYS:
        ens_action = "DELAY"

    order_block = bool(
        st.get("high_trust_blocked_for_place")
        or st.get("order_sensitivity_blocks_high")
        or st.get("conf_order_consume_block")
    )
    if not order_block:
        try:
            from .conf_gate_order_block import high_trust_blocked_by_order_sensitivity

            flip = st.get("option_order_flip_rate")
            swing = st.get("option_order_swing_pts")
            suf = st.get("state_evidence_sufficiency_pass")
            if suf is None:
                suf = float(ens.get("evidence_score") or 0) >= 1.0
            if flip is not None or swing is not None:
                order_block = high_trust_blocked_by_order_sensitivity(
                    flip_rate=float(flip or 0.0),
                    max_swing_pts=float(swing or 0.0),
                    state_evidence_sufficiency_pass=bool(suf),
                )
            elif ens.get("reason") == "thin_state_order_becomes_policy":
                order_block = True
        except Exception:
            if ens.get("reason") == "thin_state_order_becomes_policy":
                order_block = True

    final = ens_action
    conf_note = None
    if order_block and final == "PLACE":
        final = "DELAY"
        conf_note = "PLACE_to_DELAY"
    # Fail-closed: raw System One STAND/DELAY wins over ensemble PLACE (never upgrade refuse)
    raw = str(action or "DELAY").upper()
    if raw in {"STAND", "DELAY"} and final == "PLACE":
        final = "DELAY" if raw == "DELAY" else raw
        # Align OD-13: prefer DELAY over STAND when order/consume path
        if raw == "STAND" and conf_note:
            final = "DELAY"
        conf_note = (conf_note or "") + "|raw_refuse_wins"

    ens["conf_order_consume"] = conf_note
    ens["ok"] = True
    ens["ensemble_enabled"] = True
    # Dig A stamps stay place=false/apply=false in OD-13 payload (never broker-send here)
    ens["place"] = False
    ens["apply"] = False
    ens["shadow"] = True

    ensemble_meta = {
        "k": 3,
        "seeds": [s.get("seed") for s in (ens.get("shuffles") or [])],
        "option_order_hashes": [s.get("option_order_hash") for s in (ens.get("shuffles") or [])],
        "avg_probs": ens.get("avg_probs"),
        "ensemble_pick": ens.get("ensemble_pick"),
        "noul_place_p": ens.get("noul_place_p"),
        "noul_fire": ens.get("noul_fire"),
        "evidence_score": ens.get("evidence_score"),
        "reason": ens.get("reason"),
        "conf_order_consume": conf_note,
        "menu_hash": ens.get("menu_hash"),
    }

    return {
        "action": final,
        "refuse_place": final in {"STAND", "DELAY"},
        "od13": ens,
        "od13_overlay": True,
        "ensemble_enabled": True,
        "ensemble_meta": ensemble_meta,
        "pattern": "place_choice_ensemble_noul_pair",
    }
