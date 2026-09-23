"""DRAFT ONLY — not landed.

Shows how regime_system_one.call_system_one should POST jev_client.evaluate
when GTOS_JEV_REGIME_LIVE_EVALUATE=1, and fail-closed otherwise.

Do not import mt5 / book_owner / execution. Do not order_send.
"""

from __future__ import annotations

import os
from typing import Any, Mapping

# Land-time imports (do not execute here):
# from src.judgment.jev_client import evaluate
# from src.judgment.regime_system_one import (
#     MODEL_NAME, S14_QUESTION_IDS, RegimeAnswerCache, SystemOneResult,
#     build_question_pack, parse via regime_compose.parse_regime_answers
# )
# from src.judgment.veto import assert_answers_have_no_place_path, refuse_raw_tick_dump_to_jev

LIVE_EVAL_ENV = "GTOS_JEV_REGIME_LIVE_EVALUATE"
APPLY_CONF_ENV = "GTOS_JEV_CONF_GATE_APPLY"
APPLY_REGIME_ENV = "GTOS_JEV_REGIME_GATE_APPLY"


def live_evaluate_enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get(LIVE_EVAL_ENV, "")).strip().lower() in {"1", "true", "yes", "on"}


def apply_flags_must_stay_off_this_land() -> dict[str, str]:
    """Chair APPLY later. This sketch never turns them on."""
    return {
        APPLY_CONF_ENV: "0",
        APPLY_REGIME_ENV: "0",
        "GTOS_JEV_SLEEVE_SELECT_APPLY": "0",
        "place": "false",
    }


def build_jev_visible_state(bucket_state: Any) -> dict[str, Any]:
    """Buckets + identity + completeness + named context. No raw ticks, no R, no invented NEWS."""
    jev = dict(getattr(bucket_state, "jev_state", {}) or {})
    jev.setdefault("completeness", getattr(bucket_state, "completeness", {}))
    jev.setdefault("identity", getattr(bucket_state, "identity", {}))
    jev["place"] = False
    return jev


def call_system_one_draft(state: Any, *, cache=None, injected=None, offline_stub=None) -> dict[str, Any]:
    """Control flow only. Land into regime_system_one.call_system_one."""
    # 1. cache hit → parse, source=cache
    # 2. injected → parse, source=injected (Phase 1 hist)
    # 3. if live_evaluate_enabled():
    #       payload_state = build_jev_visible_state(state)
    #       questions = {**build_question_pack(sleeve), **conf_gate_questions()}
    #       receipt = evaluate(payload_state, questions=questions)  # DRAFT signature
    #       if not receipt.get("ok"):
    #           return unclear_equal_fallback (jev_dark)
    #       raw = receipt["answers"]
    #       assert_answers_have_no_place_path(raw)
    #       source = "jev_evaluate"
    #       model = receipt.get("model") or MODEL_NAME
    # 4. offline_stub → source=offline_stub_not_jev, model=None
    # 5. fallback unclear@equal, model=None
    return {
        "draft": True,
        "never_place": True,
        "apply_flags": apply_flags_must_stay_off_this_land(),
        "fail_closed_if_jev_dark": True,
    }
