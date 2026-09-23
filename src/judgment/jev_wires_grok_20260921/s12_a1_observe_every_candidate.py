"""DRAFT ONLY — not imported by live writer. Session 12_writer_cycle_run_book_a1_observe.

Observe-every helper: one jev_client.evaluate(state) per candidate even when
STAND/SKIP. Never places. Never mutates skip_reason. Fail-closed if Jev dark.

Chair splice target: src/judgment/a1_log.py (then book_owner / bridge hooks).
Do not wholesale-copy book_owner.py onto the 10069-line host tree.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

GATE_ID = "UB-OBS-EVERY"
SCHEMA = "gtos.judgment.a1_observe_every.v0"

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _env_on(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def a1_log_enabled() -> bool:
    return _env_on("GTOS_JEV_A1_LOG") or _env_on("GTOS_JEV_ALIVE_SHADOW")


def observe_every_enabled() -> bool:
    return a1_log_enabled() and _env_on("GTOS_JEV_A1_OBSERVE_EVERY")


def dedupe_enabled() -> bool:
    raw = os.environ.get("GTOS_JEV_A1_DEDUPE", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _cache_key(intent: Any, extra: dict[str, Any] | None) -> tuple[str, str, str]:
    extra = extra or {}
    symbol = str(getattr(intent, "symbol", None) or extra.get("symbol") or "")
    sleeve = str(getattr(intent, "sleeve", None) or extra.get("sleeve") or "")
    dbar = str(
        getattr(intent, "decision_bar_iso", None)
        or extra.get("decision_bar_iso")
        or ""
    )
    return (symbol, sleeve, dbar)


def observe_every_candidate(
    intent: Any,
    *,
    tick: Any = None,
    skip_reason: str | None,
    writer_stage: str,
    occupancy: dict[str, Any] | None = None,
    governor: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
    answers_cache: dict[tuple[str, str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """POST evaluate() for this candidate. Safe no-op when flags off.

    Does not call OrderRouter.place / order_send. Does not change skip_reason.
    """
    extra = dict(extra or {})
    row: dict[str, Any] = {
        "schema": SCHEMA,
        "gate_id": GATE_ID,
        "logged_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shadow_log_only": True,
        "place_policy": "default_off_until_hist_prove",
        "session_place": False,
        "broker_effect": False,
        "choice_place_open": True,
        "never_place_eternal": False,
        "skip_reason": skip_reason,
        "writer_stage": writer_stage,
    }
    if not observe_every_enabled():
        row["skipped"] = (
            "GTOS_JEV_A1_LOG_off" if not a1_log_enabled() else "GTOS_JEV_A1_OBSERVE_EVERY_off"
        )
        return row

    # Imports stay inside the enabled path so W7 fire does not pay judgment import.
    from src.judgment.a1_log import intent_gold_state, _write  # type: ignore  # noqa: PLC0415
    from src.judgment.compose import compose_shadow  # noqa: PLC0415
    from src.judgment.jev_client import evaluate  # noqa: PLC0415
    from src.judgment.jev_questions import symbol_fanout_questions  # noqa: PLC0415

    row["questions"] = list(symbol_fanout_questions())
    try:
        state = intent_gold_state(
            intent,
            tick,
            origin="w7_ultimate_book",
            occupancy=occupancy,
            governor=governor,
        ) or {}
    except Exception:
        state = {}
    state.setdefault(
        "place_context",
        {
            "writer_ready": skip_reason is None,
            "skip_reason": skip_reason,
            "writer_stage": writer_stage,
            "ticket_draft_fp": extra.get("ticket_draft_fp"),
        },
    )
    if "news_join" not in extra:
        extra["news_join"] = "STATE_MISSING"
    row["state_identity"] = (state.get("identity") or {}) if isinstance(state, dict) else {}

    key = _cache_key(intent, extra)
    if dedupe_enabled() and answers_cache is not None and key in answers_cache:
        answers = answers_cache[key]
        row["deduped"] = True
    else:
        answers = evaluate(state if isinstance(state, dict) else {})
        if answers_cache is not None:
            answers_cache[key] = answers
        row["deduped"] = False

    row["jev"] = {k: answers.get(k) for k in ("ok", "skipped", "error", "model", "usage")}
    row["answers"] = answers.get("answers") or {}
    try:
        row["compose"] = compose_shadow(state if isinstance(state, dict) else {}, row["answers"], extra=extra)
    except Exception as exc:  # noqa: BLE001
        row["compose"] = {"error": type(exc).__name__}
    try:
        _write(row)
        row["logged"] = True
    except Exception as exc:  # noqa: BLE001
        row["logged"] = False
        row["log_error"] = type(exc).__name__
    return row
