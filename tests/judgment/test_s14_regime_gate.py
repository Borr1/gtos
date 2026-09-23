"""S14 REGIME_GATE_SHADOW — buckets, compose, Chair G1–G8, no broker path."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.judgment.alive_menu import StaleMenuError, assert_menu_fresh, rebuild_choice_criteria
from src.judgment.challenge import CHALLENGE_LOGIN
from src.judgment.chair_enforce import is_hard_off_sleeve, is_index_hard_off, is_keep_family, stamp_chair_enforce
from src.judgment.cycle import run_fluid_gate_cycle
from src.judgment.flags import apply_authorized
from src.judgment.inventory import collect_live_inventory
from src.judgment.regime_buckets import emit_regime_buckets
from src.judgment.regime_compose import compose_regime_gate, parse_regime_answers, snap_size_factor
from src.judgment.regime_gate import evaluate_s14
from src.judgment.regime_system_one import RegimeAnswerCache, call_system_one
from src.judgment.s14_tape import gold_state, historical_tape_rows
from src.judgment.place_apply import place_authorized
from src.judgment.veto import (
    InventedNewsProtocolVeto,
    JevPlacePathVeto,
    RawTickDumpVeto,
    forbidden_jev_keys_in,
    refuse_broker_action,
)
from tests.judgment.cages import assert_live_cages, assert_refuse_broker

REPO = Path(__file__).resolve().parents[2]
JUDGMENT_SRC = REPO / "src" / "judgment"


def _inv():
    return collect_live_inventory(
        sleeves=("spring", "vss", "metals_core"),
        workers=("challenge:0",),
        handlers=("shadow_log",),
        include_w7_armed=False,
        include_launcher_workers=False,
    )


def _ans(choice="trend_up", conf=0.88, change=0.2, viable=0.7):
    rest = (1.0 - conf) / 4.0
    probs = {k: rest for k in ("trend_up", "trend_down", "range", "chop", "unclear")}
    probs[choice] = conf
    return {
        "regime_type": {"choice": choice, "confidence": conf, "probabilities": probs},
        "regime_change_likely": {"noul": change},
        "strategy_viable": {"noul": viable},
    }


def test_emit_buckets_only_no_raw_close() -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id="c1",
        close_ret_1=0.012,
        close_ret_5bar=0.03,
        vol_ratio=1.05,
        htf_slope_norm=0.8,
        mom_20_atr=0.6,
    )
    state = emit_regime_buckets(gold)
    assert state.buckets["returns_1d"] == "up"
    assert state.buckets["returns_5d"] == "strong_up"
    assert state.buckets["vol_vs_baseline"] == "normal"
    assert "raw_ohlcv" not in state.jev_state
    assert "last_close" not in json.dumps(state.jev_state)
    assert state.cache_key


def test_eur_symbols_are_not_forbidden_r_keys() -> None:
    gold = gold_state(
        sleeve="vss_fxcross_london_up_low",
        symbol="EURGBP",
        side="sell",
        candidate_id="eur",
        close_ret_1=0.001,
        close_ret_5bar=-0.002,
        vol_ratio=0.9,
        htf_slope_norm=0.0,
        mom_20_atr=0.0,
        sma_frac=0.0,
    )
    state = emit_regime_buckets(gold)
    assert "EURGBP" in json.dumps(state.jev_state)
    assert forbidden_jev_keys_in(state.jev_state) == set()


def test_raw_tick_dump_veto() -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id="c1",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.5,
        mom_20_atr=0.4,
    )
    gold["raw_ohlcv"] = [[1, 2, 3, 4]]
    with pytest.raises(RawTickDumpVeto):
        emit_regime_buckets(gold)


def test_empty_spine_plus_events_is_invented_high() -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id="c1",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.5,
        mom_20_atr=0.4,
    )
    gold["news"] = {
        "spine_empty": True,
        "events": [{"impact": "HIGH", "event": "invented"}],
        "source": "unassembled",
    }
    with pytest.raises(InventedNewsProtocolVeto):
        emit_regime_buckets(gold)


def test_incomplete_state_does_not_consume() -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id="c1",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.5,
        mom_20_atr=0.4,
        sufficient=False,
        missing=["geometry"],
    )
    _state, _call, composed = evaluate_s14(gold, injected_answers=_ans(), research_thresholds=True)
    assert composed.consume is False
    assert composed.gate_decision is None
    assert composed.decidable is False


def test_snap_size_factor_never_emits_g6_075() -> None:
    assert snap_size_factor(1.0, 0.75) == 0.5
    assert snap_size_factor(1.0, 1.0) == 1.0
    assert snap_size_factor(1.0, 0.5) == 0.5
    assert snap_size_factor(0.5, 0.75) == 0.5
    assert snap_size_factor(1.0, 0.0) == 0.0


def test_compose_research_thresholds_three_labels() -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id="c1",
        close_ret_1=0.012,
        close_ret_5bar=0.03,
        vol_ratio=1.0,
        htf_slope_norm=0.8,
        mom_20_atr=0.6,
        session="off_hours",
    )
    _, _, admit = evaluate_s14(gold, injected_answers=_ans("trend_up", 0.88), research_thresholds=True)
    assert admit.gate_decision == "admit_ok_label"
    assert admit.size_factor == 1.0
    gold_v = gold_state(
        sleeve="vss_fxcross_london_up_low",
        symbol="EURGBP",
        side="sell",
        candidate_id="c2",
        close_ret_1=0.001,
        close_ret_5bar=-0.002,
        vol_ratio=0.9,
        htf_slope_norm=0.0,
        mom_20_atr=0.0,
        sma_frac=0.0,
    )
    _, _, half = evaluate_s14(gold_v, injected_answers=_ans("range", 0.62), research_thresholds=True)
    assert half.gate_decision == "half_size"
    assert half.size_factor == 0.5
    _, _, down = evaluate_s14(gold, injected_answers=_ans("chop", 0.7, viable=0.1), research_thresholds=True)
    assert down.gate_decision == "stand_down"
    assert down.size_factor == 0.0


def test_g6_london_snaps_admit_ok_to_half_size() -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id="g6",
        close_ret_1=0.012,
        close_ret_5bar=0.03,
        vol_ratio=1.0,
        htf_slope_norm=0.8,
        mom_20_atr=0.6,
        session="london",
    )
    _, _, composed = evaluate_s14(gold, injected_answers=_ans("trend_up", 0.88), research_thresholds=True)
    assert composed.chair.g6_size_ceiling == 0.75
    assert composed.gate_decision == "half_size"
    assert composed.size_factor == 0.5
    assert composed.size_factor in {0.0, 0.5, 1.0}
    assert "g6_ceiling_snapped_to_allowed_size_factor" in composed.notes


def test_production_thresholds_unset_prefer_stand_down() -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id="c1",
        close_ret_1=0.012,
        close_ret_5bar=0.03,
        vol_ratio=1.0,
        htf_slope_norm=0.8,
        mom_20_atr=0.6,
    )
    _, _, composed = evaluate_s14(gold, injected_answers=_ans("trend_up", 0.99), research_thresholds=False)
    assert composed.gate_decision == "stand_down"
    assert composed.reason == "s15_thresholds_unset_prefer_stand_down"


def test_missing_favored_fail_closed() -> None:
    gold = gold_state(
        sleeve="no_such_sleeve",
        symbol="XAUUSD",
        side="long",
        candidate_id="c1",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.5,
        mom_20_atr=0.4,
    )
    _, _, composed = evaluate_s14(gold, injected_answers=_ans(), research_thresholds=True)
    assert composed.gate_decision == "stand_down"
    assert composed.reason == "favored_regimes_missing"


def test_hard_offs_not_weakened() -> None:
    assert is_hard_off_sleeve("xa_huge_20_extreme")
    assert is_hard_off_sleeve("orb_crypto_london")
    assert is_index_hard_off(sleeve="idxrev", symbol="UK100.cash")
    assert is_index_hard_off(sleeve="dsp_walked_hi", symbol="US30.cash")
    assert is_keep_family("dsp_spring_close")
    gold = gold_state(
        sleeve="xa_huge_same_way",
        symbol="EURUSD",
        side="buy",
        candidate_id="toxic",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.8,
        mom_20_atr=0.6,
    )
    _, _, composed = evaluate_s14(gold, injected_answers=_ans("trend_up", 0.99, viable=0.99), research_thresholds=True)
    assert composed.gate_decision == "stand_down"
    assert composed.chair.hard_off is True
    assert composed.size_factor == 0.0


def test_keep_no_boost_and_g7_ceiling() -> None:
    stamp = stamp_chair_enforce(sleeve="spring", symbol="XAUUSD")
    assert stamp.keep_family is True
    assert stamp.keep_no_boost is True
    assert stamp.size_ceiling == 1.0
    gold = gold_state(
        sleeve="dsp_spring_close",
        symbol="XAUUSD",
        side="long",
        candidate_id="k",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.7,
        mom_20_atr=0.5,
    )
    _, _, composed = evaluate_s14(gold, injected_answers=_ans("trend_up", 0.92), research_thresholds=True)
    assert composed.chair.keep_family is True
    assert composed.size_factor in {0.0, 0.5, 1.0}
    assert composed.size_factor <= 1.0


def test_g8_blocks_same_sleeve_reentry() -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id="g8",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.7,
        mom_20_atr=0.5,
        occupancy={
            "already_placed_today": True,
            "same_sleeve_reentry": True,
            "new_named_fire": False,
            "minutes_since_flat": 3,
        },
    )
    _, _, composed = evaluate_s14(gold, injected_answers=_ans("trend_up", 0.9), research_thresholds=True)
    assert composed.gate_decision == "stand_down"
    assert composed.reason == "g8_block_reentry_same_sleeve"


def test_cache_replay_deterministic() -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id="cache",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.5,
        mom_20_atr=0.4,
    )
    cache = RegimeAnswerCache()
    a = call_system_one(emit_regime_buckets(gold), cache=cache, injected=_ans())
    b = call_system_one(emit_regime_buckets(gold), cache=cache)
    assert a.cache_hit is False
    assert b.cache_hit is True
    assert a.cache_key == b.cache_key
    assert a.raw == b.raw


def test_unclear_equal_not_decidable() -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id="u",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.5,
        mom_20_atr=0.4,
    )
    _, call, composed = evaluate_s14(gold)  # no injected → unclear@equal fallback
    assert call.source == "unclear_equal_fallback"
    assert composed.decidable is False


def test_stale_alive_menu_fail_closed() -> None:
    first = _inv()
    menu = rebuild_choice_criteria(first)
    second = collect_live_inventory(
        sleeves=("spring",),
        workers=("challenge:0",),
        handlers=("shadow_log",),
        include_w7_armed=False,
        include_launcher_workers=False,
    )
    with pytest.raises(StaleMenuError):
        assert_menu_fresh(menu, second)


def test_cycle_writes_s14_on_same_sidecar(tmp_path: Path) -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id="cyc",
        close_ret_1=0.012,
        close_ret_5bar=0.03,
        vol_ratio=1.0,
        htf_slope_norm=0.8,
        mom_20_atr=0.6,
        session="off_hours",
    )
    result = run_fluid_gate_cycle(
        inventory=_inv(),
        gold_state=gold,
        s14_answers=_ans("trend_up", 0.88),
        s14_research_thresholds=True,
        log_dir=tmp_path,
        force=True,
        stake="sleeve_admit",
    )
    assert result.skipped is False
    assert result.regime is not None
    assert result.regime.gate_decision == "admit_ok_label"
    assert result.regime.broker_effect is False
    assert result.apply.apply is False
    doc = json.loads(result.log_path.read_text(encoding="utf-8"))
    assert doc["steal"] == "S14"
    assert doc["broker_effect"] is False
    assert_live_cages(doc)
    assert doc["account_surface"]["login"] == CHALLENGE_LOGIN
    assert doc["regime"]["size_factor"] == 1.0
    assert "returns_1d" in doc["s14_jev_state"]
    assert "regime_type" in doc["fanout_book"]["questions"]
    assert result.completion == "DONE"


def test_shadow_flag_off_writes_nothing_with_s14(tmp_path: Path) -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id="off",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.5,
        mom_20_atr=0.4,
    )
    result = run_fluid_gate_cycle(
        inventory=_inv(),
        gold_state=gold,
        s14_answers=_ans(),
        log_dir=tmp_path,
        force=False,
        shadow=False,
    )
    assert result.skipped is True
    assert list(tmp_path.rglob("*.json")) == []


def test_admit_ok_never_maps_to_order_send() -> None:
    parsed = parse_regime_answers(_ans("trend_up", 0.99))
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id="map",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.5,
        mom_20_atr=0.4,
        session="off_hours",
    )
    composed = compose_regime_gate(
        emit_regime_buckets(gold),
        parsed,
        confidence_threshold=0.85,
        half_size_threshold=0.5,
    )
    assert composed.gate_decision == "admit_ok_label"
    assert_refuse_broker("order_send")
    denied = apply_authorized(
        stake="place",
        apply_flag=True,
        receipt=None,
        band="HIGH",
        required_band="VETO",
    )
    assert denied.apply is False
    size = apply_authorized(
        stake="size_tilt",
        apply_flag=True,
        receipt=None,
        band="HIGH",
        required_band="HIGH",
    )
    assert size.apply is False
    assert size.reason == "s15_shadow_only_no_size_tilt_apply"


def test_s14_answers_place_choice_veto(tmp_path: Path) -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id="bad",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.5,
        mom_20_atr=0.4,
    )
    kwargs = dict(
        inventory=_inv(),
        gold_state=gold,
        s14_answers={"regime_type": {"choice": "order_send", "confidence": 1.0}},
        log_dir=tmp_path,
        force=True,
    )
    if place_authorized():
        result = run_fluid_gate_cycle(**kwargs)
        assert result.conf_gate.broker_effect is False
        assert result.apply.apply is False
    else:
        with pytest.raises(JevPlacePathVeto):
            run_fluid_gate_cycle(**kwargs)


def test_historical_tape_scorecard_offline(tmp_path: Path) -> None:
    from scripts.run_s14_historical_prove import main

    score = tmp_path / "score.json"
    tape = tmp_path / "tape.jsonl"
    rc = main(["--force", "--log-dir", str(tmp_path / "logs"), "--score-out", str(score), "--write-tape", str(tape)])
    assert rc == 0
    card = json.loads(score.read_text(encoding="utf-8"))
    assert card["n_decidable"] >= 20
    assert card["n_moved"] >= 5
    assert card["n_distinct_gate"] >= 2
    assert card["n_invented_high"] == 0
    assert card["n_order_send"] == 0
    assert card["broker_effect_all_false"] is True
    assert card["pass"] is True
    assert tape.is_file()
    logs = list((tmp_path / "logs").rglob("*.json"))
    assert logs
    for path in logs:
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert_live_cages(doc)
        assert doc["broker_effect"] is False
        assert doc["account_surface"]["login"] == CHALLENGE_LOGIN


def test_judgment_package_still_has_no_broker_imports() -> None:
    banned_roots = ("mt5", "MetaTrader5", "book_owner", "mt5_real", "execution")
    for path in JUDGMENT_SRC.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    low = alias.name.lower()
                    assert all(b.lower() not in low for b in banned_roots)
            if isinstance(node, ast.ImportFrom):
                mod = (node.module or "").lower()
                assert "mt5" not in mod
                assert "book_owner" not in mod
                assert "mt5_real" not in mod
                assert not mod.endswith(".execution")
                assert mod != "execution"
            if isinstance(node, ast.Call):
                name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                assert name != "order_send"
                assert name != "open_trade"


def test_tape_has_challenge_identities() -> None:
    rows = historical_tape_rows()
    assert len(rows) >= 24
    assert all(r["login"] == CHALLENGE_LOGIN for r in rows)
    sleeves = {r["gold_state"]["identity"]["sleeve"] for r in rows}
    assert "xa_huge_20_extreme" in sleeves
    assert "idxrev" in sleeves
    assert "orb_crypto_london" in sleeves
