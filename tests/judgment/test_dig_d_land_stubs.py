"""Dig D land stubs — APPLY_CONSUME vs KILL. Never order_send."""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path

import pytest

from src.judgment.challenge import CHALLENGE_LOGIN, CHALLENGE_NS
from src.judgment.cycle import run_fluid_gate_cycle
from src.judgment.flags import (
    APPLY_ENV,
    CHALLENGE_PROVE_ONLY_DUAL_FLAGS,
    DIG_MULTI_STAGE_GUARD_OFF_PROVE_TRACK,
    EVERYWHERE_ENV,
    SHADOW_ENV,
)
from src.judgment.land_stubs import (
    A1_OBSERVE,
    CHAIR_BOARD,
    CHAIR_LIVE_FLAGS,
    DIG_C_0_8,
    DIG_E_APPLY,
    DIG_F_FIVE,
    KILL_ORDER,
    KilledLandStubError,
    SCHEMA,
    STUBS_PATH,
    apply_env_untouched,
    apply_od_10_perm_avg_research_router,
    apply_od_12_yesno_reverse_regression,
    apply_order_ensemble_shuffle,
    assert_no_resting_shadow,
    challenge_prove_track,
    consume,
    consume_a1_observe,
    consume_dig_c,
    flip_table,
    killed_stubs,
    land_module_has_order_send,
    live_path_stubs,
    load_land_stubs,
    lookup,
    pack1b_beaten,
    recipes,
    resting_closed_recipes,
    scan_implement_stub_resting,
    sidecar_stamp,
    verify_dig_c_live_flags,
)
from src.judgment.p0_shadow_hooks import compose_warroom_shadow, load_hook_stubs
from src.judgment.process_lock import APPLIED_WIRES
from src.judgment.s16_flags import APPLY_ENV as DIG_APPLY_ENV
from src.judgment.s16_flags import SHADOW_ENV as DIG_SHADOW_ENV
from src.judgment.s16_flags import s16_apply_enabled, s16_apply_env_forbidden

REPO = Path(__file__).resolve().parents[2]
S16_MAP = REPO / "judgment" / "astra" / "s16_guard_map.json"
FLAG_DOC = REPO / "docs" / "flags" / "DIG_D_LAND_CONSUME.json"
BOARD = REPO / "research" / "warroom" / "DIG_FEC_VERDICT_BOARD.md"
FLIPS = REPO / "research" / "warroom" / "DIG_D_STUB_FLIPS.md"
LANE = REPO / "research" / "warroom" / "DIG_LAND_D_LANE_EMPTY_20260921.md"

DIG_C_ALIASES = (
    "f5_xau_flow_alignment_size_tilt",
    "F5-JEV-004",
    "ca_cross_asset_size_tilt",
    "HOST_PROVE_C_STAMP_FIX",
)


def test_registry_binds_challenge_and_walls() -> None:
    doc = load_land_stubs()
    assert doc["schema"] == SCHEMA
    assert doc["login"] == CHALLENGE_LOGIN
    assert doc["ns"] == CHALLENGE_NS
    assert doc["chair_board"] == CHAIR_BOARD
    assert doc["resting_shadow"] == 0
    assert doc["apply_env_flipped"] is False
    assert doc["pack1b_beaten"] is False
    assert pack1b_beaten() is False
    assert doc["redacted_account"] is False
    assert doc["never_place"] is True
    assert doc["news_invent"] is False
    assert doc["broker_effect"] is False
    assert doc["w7_armed_books"] == "never"
    assert doc["out_of_scope"]["p0_warroom_shadow_hooks"]["status"] == "PARKED"
    assert doc["out_of_scope"]["p0_warroom_shadow_hooks"]["apply"] is False


def test_every_closed_recipe_flipped() -> None:
    table = flip_table()
    by_id = {row["id"]: row for row in table}
    for recipe_id in DIG_F_FIVE + DIG_E_APPLY + DIG_C_0_8 + (A1_OBSERVE,):
        assert by_id[recipe_id]["status"] == "APPLY_CONSUME"
        assert by_id[recipe_id]["live_path"] is True
        assert by_id[recipe_id]["prior_status"] not in {"SHADOW", "IN_PROVE", "APPLY_CANDIDATE"} or recipe_id in DIG_F_FIVE + DIG_E_APPLY
    for recipe_id in DIG_F_FIVE:
        assert by_id[recipe_id]["prior_status"] != "SHADOW"
    for recipe_id in KILL_ORDER + ("DIG_MULTI_STAGE_GUARD",):
        assert by_id[recipe_id]["status"] == "KILL"
        assert by_id[recipe_id]["live_path"] is False
    assert_no_resting_shadow()
    assert resting_closed_recipes() == []
    assert scan_implement_stub_resting() == []
    assert {row["id"] for row in killed_stubs()} == set(KILL_ORDER + ("DIG_MULTI_STAGE_GUARD",))
    live_ids = {row["id"] for row in live_path_stubs()}
    assert live_ids == set(DIG_F_FIVE + DIG_E_APPLY + DIG_C_0_8 + (A1_OBSERVE,))
    assert "DIG_MULTI_STAGE_GUARD" not in live_ids
    assert "order_ensemble_shuffle" not in live_ids


def test_consume_apply_vs_kill() -> None:
    ok = consume("od_13")
    assert ok["enabled"] is True
    assert ok["status"] == "APPLY_CONSUME"
    assert ok["live_path"] is True
    assert ok["broker_effect"] is False
    assert ok["never_place"] is True
    assert ok["pack1b_beaten"] is False
    assert ok["redacted_account"] is False
    assert ok["apply_env_flipped"] is False
    assert "PLACE_APPLY" in ok["flags"]

    dead = consume("order_ensemble_shuffle")
    assert dead["enabled"] is False
    assert dead["status"] == "KILL"
    assert dead["live_path"] is False
    assert dead["note"] == "subsumed_by_od_13"

    assert consume("ORDER_ENSEMBLE_SHUFFLE")["status"] == "KILL"
    assert consume("OD-10")["status"] == "KILL"
    assert consume("OD-12")["status"] == "KILL"

    s16 = consume("DIG_MULTI_STAGE_GUARD")
    assert s16["enabled"] is False
    assert s16["status"] == "KILL"
    assert s16["live_path"] is False


def test_kill_order_raises_off_live_path() -> None:
    with pytest.raises(KilledLandStubError):
        apply_order_ensemble_shuffle()
    with pytest.raises(KilledLandStubError):
        apply_od_10_perm_avg_research_router()
    with pytest.raises(KilledLandStubError):
        apply_od_12_yesno_reverse_regression()


def test_dig_c_0_8_invokes_live_code() -> None:
    for index, recipe_id in enumerate(DIG_C_0_8):
        receipt = consume_dig_c(index)
        assert receipt["id"] == recipe_id
        assert receipt["status"] == "APPLY_CONSUME"
        assert receipt["enabled"] is True
        assert receipt["broker_effect"] is False
        assert receipt["never_place"] is True
        assert receipt["apply_env_flipped"] is False
        assert receipt["login"] == CHALLENGE_LOGIN
        assert "fn" in receipt["invoked"]
        alias_receipt = consume(recipe_id)
        assert alias_receipt["status"] == "APPLY_CONSUME"
    named = consume("f5_xau_flow_alignment_size_tilt")
    assert named["id"] == "dig_c_2_named_size_tilts"
    prove = consume("HOST_PROVE_C_STAMP_FIX")
    assert prove["id"] == "dig_c_5_prove_c_stamp_fix"
    gate = consume_dig_c(3)
    assert gate["invoked"]["apply_env_flipped"] is False


def test_a1_observe_consume_never_places(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("GTOS_JEV_A1_LOG", raising=False)
    monkeypatch.delenv("GTOS_JEV_ALIVE_SHADOW", raising=False)
    monkeypatch.setenv("GTOS_JEV_A1_CALL", "0")
    row = consume_a1_observe()
    assert row["id"] == A1_OBSERVE
    assert row["status"] == "APPLY_CONSUME"
    assert row["observe"] is True
    assert row["apply"] is False
    assert row["broker_effect"] is False
    assert row["apply_env_flipped"] is False
    assert row["never_place"] is True
    via = consume("a1_observe")
    assert via["status"] == "APPLY_CONSUME"
    monkeypatch.setenv("GTOS_JEV_A1_LOG", "1")
    monkeypatch.setenv("GTOS_JEV_A1_LOG_PATH", str(tmp_path / "a1.jsonl"))
    logged = consume_a1_observe()
    assert logged["status"] == "APPLY_CONSUME"
    assert logged["apply"] is False
    assert logged["apply_env_flipped"] is False


def test_s16_apply_killed_even_with_env_and_force(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(DIG_APPLY_ENV, "1")
    monkeypatch.setenv(DIG_SHADOW_ENV, "1")
    assert s16_apply_enabled() is False
    assert s16_apply_enabled(force=True) is False
    assert s16_apply_env_forbidden() is True
    monkeypatch.delenv(DIG_APPLY_ENV, raising=False)
    assert s16_apply_env_forbidden() is False
    track = challenge_prove_track()
    assert track["includes_s16_apply"] is False
    assert track["includes_s16_shadow"] is False
    assert track["includes_everywhere_alias"] is True
    assert DIG_APPLY_ENV in DIG_MULTI_STAGE_GUARD_OFF_PROVE_TRACK
    assert DIG_SHADOW_ENV in DIG_MULTI_STAGE_GUARD_OFF_PROVE_TRACK
    assert DIG_APPLY_ENV not in CHALLENGE_PROVE_ONLY_DUAL_FLAGS
    assert set(CHALLENGE_PROVE_ONLY_DUAL_FLAGS) == {SHADOW_ENV, APPLY_ENV, EVERYWHERE_ENV}


def test_dig_c_stubs_match_live_flags() -> None:
    check = verify_dig_c_live_flags()
    assert check["ok"] is True, check["mismatches"]
    assert check["status"] == "APPLY_CONSUME"
    assert set(check["wires"]) == set(APPLIED_WIRES)
    assert check["physical_env"] == "GTOS_JEV_APPLY_LIVE"
    assert check["login"] == CHALLENGE_LOGIN
    assert check["ns"] == CHALLENGE_NS
    assert check["p0_warroom_shadow_apply"] is False
    assert check["apply_env_flipped"] is False
    p0 = load_hook_stubs()
    assert p0["apply"] is False
    shadow = compose_warroom_shadow().as_dict()
    assert shadow["apply"] is False
    assert shadow["login"] == CHALLENGE_LOGIN


def test_chair_live_flags_are_not_broker_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GTOS_JEV_APPLY_LIVE", raising=False)
    monkeypatch.delenv("GTOS_JEV_FLUID_GATES_APPLY", raising=False)
    assert CHAIR_LIVE_FLAGS == {
        "CONF_ORDER_CONSUME": "1",
        "PLACE_APPLY": "1",
        "PLACE_ENSEMBLE": "1",
    }
    untouched = apply_env_untouched()
    assert untouched["flipped"] is False
    assert untouched["broker_apply_env_set_by_dig_d"] is False
    assert untouched["reads"]["GTOS_JEV_APPLY_LIVE"] == ""
    assert untouched["reads"]["GTOS_JEV_FLUID_GATES_APPLY"] == ""
    doc = json.loads(FLAG_DOC.read_text(encoding="utf-8"))
    assert doc["pack1b_beaten"] is False
    assert doc["redacted_account"] is False
    assert doc["never_place"] is True
    assert doc["resting_shadow"] == 0
    assert doc["apply_env_flipped"] is False
    assert doc["flags"]["PLACE_APPLY"]["broker_flag"] is False
    assert doc["flags"]["GTOS_DIG_MULTI_STAGE_GUARD_APPLY"]["enabled"] is False
    assert doc["flags"]["GTOS_JEV_APPLY_LIVE"]["dig_d_flips"] is False
    assert lookup("od_13")["already_live"] is True
    assert lookup("EVERYWHERE_SHADOW")["already_live"] is True
    assert lookup("TRAIN_HARVEST")["apply"] is False
    src = (REPO / "src" / "judgment" / "land_stubs.py").read_text(encoding="utf-8")
    assert 'os.environ["GTOS_JEV_APPLY_LIVE"]' not in src
    assert "os.environ.setdefault" not in src or "GTOS_JEV_APPLY_LIVE" not in src
    assert "os.environ[" not in src


def test_s16_map_status_is_kill() -> None:
    mapped = json.loads(S16_MAP.read_text(encoding="utf-8"))
    assert mapped["status"] == "KILL"
    assert mapped["apply_forbidden"] is True
    assert mapped["challenge_prove_only_dual_flag_track"] is False
    assert mapped["never_place"] is True


def test_board_and_flips_name_every_stub() -> None:
    board = BOARD.read_text(encoding="utf-8")
    flips = FLIPS.read_text(encoding="utf-8")
    lane = LANE.read_text(encoding="utf-8")
    assert CHAIR_BOARD in lane
    assert "resting SHADOW = **0**" in lane or "Resting SHADOW = **0**" in lane
    for recipe_id in [row["id"] for row in recipes()]:
        assert recipe_id in board
        assert recipe_id in flips
        assert recipe_id in STUBS_PATH.read_text(encoding="utf-8")
        if recipe_id in DIG_C_0_8 or recipe_id == A1_OBSERVE or recipe_id in DIG_F_FIVE:
            assert recipe_id in lane


def test_cycle_stamps_land_consume(tmp_path: Path) -> None:
    result = run_fluid_gate_cycle(
        login=CHALLENGE_LOGIN,
        answers={"next_gate": 0.4},
        log_dir=tmp_path,
        force=True,
    )
    assert result.land_consume is not None
    stamp = result.land_consume
    assert stamp["chair_board"] == CHAIR_BOARD
    assert stamp["resting_shadow"] == 0
    assert stamp["apply_env_flipped"] is False
    assert stamp["never_place"] is True
    assert stamp["pack1b_beaten"] is False
    assert list(stamp["dig_c_0_8"]) == list(DIG_C_0_8)
    assert list(stamp["dig_f_five"]) == list(DIG_F_FIVE)
    assert stamp["a1_observe"] == A1_OBSERVE
    assert set(stamp["kill_order"]) == set(KILL_ORDER)
    assert result.apply.apply is False
    assert result.as_dict()["broker_effect"] is False
    payload = json.loads(Path(result.log_path).read_text(encoding="utf-8"))
    assert payload["land_consume"]["resting_shadow"] == 0
    assert payload["steal_dig_d"] == "DIG_D_LAND_STUBS"
    assert payload["broker_effect"] is False


def test_sidecar_stamp_is_lane_empty() -> None:
    stamp = sidecar_stamp()
    assert stamp["status"] == "LANE_EMPTY"
    assert stamp["resting_shadow"] == 0
    assert stamp["apply_env_flipped"] is False
    assert set(stamp["dig_c_0_8"]) == set(DIG_C_0_8)
    assert A1_OBSERVE in stamp["apply_consume"]
    for recipe_id in DIG_F_FIVE:
        assert recipe_id in stamp["apply_consume"]
    for recipe_id in KILL_ORDER:
        assert recipe_id in stamp["kill"]


def test_land_stubs_never_order_send() -> None:
    assert land_module_has_order_send() == 0
    src = (REPO / "src" / "judgment" / "land_stubs.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            assert name not in {"order_send", "open_trade"}
        if isinstance(node, ast.ImportFrom):
            mod = (node.module or "").lower()
            assert "mt5" not in mod
            assert "book_owner" not in mod
            assert "redacted_account" not in mod
    assert "NEWS_PROTOCOL" not in src or "never invent" in src.lower() or "news_invent" in src
    for name in DIG_C_ALIASES:
        assert lookup(name) is not None
    assert os.environ.get("GTOS_JEV_APPLY_LIVE", "") in {"", "0", "false", "off", "1", "true"}
