"""Dig E dual-flag land consume — Challenge 0 / operator.

Board APPLY_KILL_RECEIPTS_DUAL_FLAGS_CHALLENGE_20260921.
Does not invent NEWS_PROTOCOL. Does not touch W7 / redacted_account.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.judgment.gold_state import assemble_gold_state_v0
from src.judgment.flags import (
    APPLY_ENV,
    CHALLENGE_PROVE_ONLY_DUAL_FLAGS,
    DIG_E_BOARD,
    EVERYWHERE_ENV,
    EVERYWHERE_IS_FLUID_GATES_ALIAS,
    EVERYWHERE_OPEN_IN_PROVE,
    EVERYWHERE_VERDICT,
    SHADOW_ENV,
    TRAIN_HARVEST_APPLY,
    TRAIN_HARVEST_CALL,
    TRAIN_HARVEST_ENV,
    TRAIN_HARVEST_LIVE_MULTIPLIER,
    TRAIN_HARVEST_READY_TO_APPLY,
    TRAIN_HARVEST_SHADOW,
    TRAIN_HARVEST_VERDICT,
    everywhere_is_open_in_prove,
    train_harvest_already_live,
)
from src.judgment.harvest_patterns import attach_harvest_blocks
from src.judgment.s16_flags import (
    APPLY_ENV as S16_APPLY_ENV,
)
from src.judgment.s16_flags import (
    APPLY_FORBIDDEN,
    DIG_E_VERDICT,
    ON_CHALLENGE_PROVE_ONLY_DUAL_FLAG_TRACK,
    SHADOW_DEFAULT,
    SHADOW_ENV as S16_SHADOW_ENV,
    s16_apply_enabled,
)

REPO = Path(__file__).resolve().parents[2]
DOCS_FLAGS = REPO / "docs" / "flags" / "CHALLENGE_DUAL_FLAGS.json"
DOCS_README = REPO / "docs" / "flags" / "README.md"
RECEIPT_JSON = REPO / "judgment" / "astra" / "lab" / "wires" / "DIG_E_LAND_CONSUME.json"
RECEIPT_MD = REPO / "judgment" / "DIG_E_LAND_CONSUME.md"
RECIPE = REPO / "judgment" / "CHAIR_LAND_RECIPE_VPS_F5_LIVE.md"
S16_MAP = REPO / "judgment" / "astra" / "s16_guard_map.json"


def test_everywhere_alias_not_open_in_prove() -> None:
    assert EVERYWHERE_IS_FLUID_GATES_ALIAS is True
    assert EVERYWHERE_VERDICT == "APPLY_CANDIDATE_ALREADY_LIVE"
    assert EVERYWHERE_OPEN_IN_PROVE is False
    assert everywhere_is_open_in_prove() is False
    assert EVERYWHERE_ENV == "GTOS_JEV_EVERYWHERE_SHADOW"
    assert EVERYWHERE_ENV not in CHALLENGE_PROVE_ONLY_DUAL_FLAGS
    assert CHALLENGE_PROVE_ONLY_DUAL_FLAGS == frozenset({SHADOW_ENV, APPLY_ENV})


def test_train_harvest_already_live_confirm_only() -> None:
    stamp = train_harvest_already_live()
    assert TRAIN_HARVEST_VERDICT == "ALREADY_LIVE"
    assert TRAIN_HARVEST_SHADOW == 1
    assert TRAIN_HARVEST_CALL == 1
    assert TRAIN_HARVEST_APPLY == 0
    assert TRAIN_HARVEST_ENV is None
    assert TRAIN_HARVEST_READY_TO_APPLY is False
    assert TRAIN_HARVEST_LIVE_MULTIPLIER == 1.0
    assert stamp["env_invented"] is False
    attached = attach_harvest_blocks(
        assemble_gold_state_v0(
            as_of_utc=datetime(2026, 4, 15, 12, tzinfo=timezone.utc),
            side="short",
            sleeve="dsp_two_bar_t",
            origin_organism="f5_challenge",
            as_of_clock="as_of_open_study",
            books=None,
            spines={"spine_id": "x", "sources": [], "events": [], "n_files": 0},
        )
    )
    assert attached["harvest"]["live_multiplier"] == 1.0
    assert attached["completeness"]["harvest"] is True


def test_dig_multi_stage_guard_kill() -> None:
    assert DIG_E_VERDICT == "KILL"
    assert SHADOW_DEFAULT == "0"
    assert APPLY_FORBIDDEN is True
    assert ON_CHALLENGE_PROVE_ONLY_DUAL_FLAG_TRACK is False
    assert S16_SHADOW_ENV not in CHALLENGE_PROVE_ONLY_DUAL_FLAGS
    assert S16_APPLY_ENV not in CHALLENGE_PROVE_ONLY_DUAL_FLAGS
    assert s16_apply_enabled() is False
    assert s16_apply_enabled(force=True) is False


def test_docs_flags_does_not_list_everywhere_as_open_in_prove() -> None:
    doc = json.loads(DOCS_FLAGS.read_text(encoding="utf-8"))
    open_ids = {row["id"] for row in doc["open_in_prove"]}
    assert "EVERYWHERE_SHADOW" not in open_ids
    assert "TRAIN_HARVEST" not in open_ids
    assert "DIG_MULTI_STAGE_GUARD" not in open_ids
    assert open_ids == {"FLUID_GATES"}
    assert doc["place"] is False
    assert doc["apply"] is False
    assert doc["pack1b_beaten"] is False
    assert doc["news_protocol_invented"] is False
    assert doc["policy_c_shadow_eval"] == 1
    assert doc["policy_c_shadow_eval_relitigated"] is False
    not_open = {row["id"]: row for row in doc["not_open_in_prove"]}
    assert not_open["EVERYWHERE_SHADOW"]["open_in_prove"] is False
    assert not_open["EVERYWHERE_SHADOW"]["verdict"] == "APPLY_CANDIDATE_ALREADY_LIVE"
    assert not_open["TRAIN_HARVEST"]["shadow"] == 1
    assert not_open["TRAIN_HARVEST"]["call"] == 1
    assert not_open["TRAIN_HARVEST"]["apply"] == 0
    assert not_open["TRAIN_HARVEST"]["env_invented"] is False
    assert not_open["DIG_MULTI_STAGE_GUARD"]["verdict"] == "KILL"
    readme = DOCS_README.read_text(encoding="utf-8")
    assert "EVERYWHERE_SHADOW" in readme
    assert "not listed as open `IN_PROVE`" in readme or "Not open IN_PROVE" in readme
    assert "TRAIN_HARVEST" in readme
    assert "DIG_MULTI_STAGE_GUARD" in readme
    assert "NEWS_PROTOCOL" in readme


def test_land_consume_receipt_and_recipe() -> None:
    rec = json.loads(RECEIPT_JSON.read_text(encoding="utf-8"))
    assert rec["receipt"] == "DIG_E_LAND_CONSUME"
    assert rec["board"] == DIG_E_BOARD
    assert rec["login"] == "0"
    assert rec["ns"] == "operator"
    assert rec["place"] is False
    assert rec["apply"] is False
    assert rec["pack1b_beaten"] is False
    assert rec["news_protocol_invented"] is False
    assert rec["redacted_account_untouched"] is True
    assert rec["w7_untouched"] is True
    assert rec["policy_c_shadow_eval"] == 1
    assert rec["verdicts"]["EVERYWHERE_SHADOW"]["open_in_prove"] is False
    assert rec["verdicts"]["TRAIN_HARVEST"]["apply"] == 0
    assert rec["verdicts"]["DIG_MULTI_STAGE_GUARD"]["verdict"] == "KILL"
    assert rec["verdicts"]["DIG_MULTI_STAGE_GUARD"]["shadow_default"] == "0"
    md = RECEIPT_MD.read_text(encoding="utf-8")
    assert "DIG_E_LAND_CONSUME" in md
    assert "APPLY_CANDIDATE ALREADY_LIVE" in md
    assert "KILL" in md
    recipe = RECIPE.read_text(encoding="utf-8")
    assert "APPLY_CANDIDATE ALREADY_LIVE" in recipe
    assert "TRAIN_HARVEST" in recipe
    assert "SHADOW+CALL=1" in recipe
    assert "GTOS_DIG_MULTI_STAGE_GUARD_SHADOW" in recipe
    assert "GTOS_DIG_MULTI_STAGE_GUARD_APPLY" in recipe
    assert "**`0`**" in recipe or "`0`" in recipe
    assert "forbidden" in recipe
    assert "NEWS_PROTOCOL" in recipe
    assert "pack1b_beaten=false" in recipe
    assert "POLICY_C_SHADOW_EVAL" in recipe
    guard = json.loads(S16_MAP.read_text(encoding="utf-8"))
    assert guard["status"] == "DIG_E_KILL"
    assert guard["on_challenge_prove_only_dual_flag_track"] is False
    assert guard["flags"]["default"] == "0"
    assert guard["flags"]["apply_forbidden"] is True
    # No NEWS_PROTOCOL module invented by this land.
    assert not (REPO / "src" / "judgment" / "news_protocol.py").exists()
