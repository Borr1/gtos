"""S15 COST_OF_ERROR — pick rule, CONF_GATE shadow bands, same sidecar, no place."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.judgment.challenge import CHALLENGE_LOGIN
from src.judgment.conf_gate import (
    REVIEW_KEEP_TICKET,
    REVIEW_OFFHOURS_TICKET,
    TICKET_SUBCLASS,
    log_conf_gate,
    log_cost_of_error,
    naive_vendor_choice,
    pick_cost_of_error,
    tape_authority_facts,
)
from src.judgment.cycle import run_fluid_gate_cycle
from src.judgment.flags import SHADOW_ENV, apply_authorized
from src.judgment.inventory import collect_live_inventory
from src.judgment.s14_tape import gold_state
from src.judgment.s15_tape import FS_HALF_TICKETS, s15_historical_tape_rows
from src.judgment.veto import InventedNewsProtocolVeto, JevPlacePathVeto, refuse_broker_action
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


def test_pick_argmin_and_tie_break() -> None:
    chosen, exp = pick_cost_of_error(0.9, cost_false_yes=1.0, cost_false_no=100.0, cost_human=50.0)
    assert chosen == "YES"
    assert exp["e_yes"] == pytest.approx(0.1)
    chosen, _ = pick_cost_of_error(0.5, cost_false_yes=20.0, cost_false_no=20.0, cost_human=2.0)
    assert chosen == "UNSURE"
    # E[YES]=E[NO] < E[HUMAN] → NO (UNSURE then NO)
    chosen, _ = pick_cost_of_error(0.5, cost_false_yes=10.0, cost_false_no=10.0, cost_human=20.0)
    assert chosen == "NO"
    # three-way tie → UNSURE
    chosen, _ = pick_cost_of_error(0.5, cost_false_yes=8.0, cost_false_no=8.0, cost_human=4.0)
    assert chosen == "UNSURE"


def test_tape_authority_key_facts_exact() -> None:
    facts = tape_authority_facts()
    assert facts["schema"] == "gtos.dig.s15.cost_matrix.v2_tape_authority"
    assert facts["false_abstain"] == 0
    assert facts["false_admit_n"] == 29
    assert facts["false_admit_tape_R"] == pytest.approx(-28.9172)
    assert facts["false_admit_shadow_R"] == pytest.approx(-13.5428)
    assert facts["cost_avoided_by_reject_n"] == 23
    assert facts["cost_avoided_by_reject_tape_R"] == pytest.approx(-24.6586)
    assert facts["g4_x_g6_overshrink"] is False
    assert facts["place"] == "infinity_veto"
    assert facts["new_hard_off"] is False
    assert facts["review_keep_ticket"] == REVIEW_KEEP_TICKET
    assert facts["review_keep_offhours_ticket"] == REVIEW_OFFHOURS_TICKET


def test_false_abstain_path_is_zero() -> None:
    """n=0 on TAPE_FALSE_ABSTAIN — no REJECT blocked a tape winner."""

    row = log_cost_of_error(0.55, stake="sleeve_admit", subclass="false_abstain")
    assert row.gate_id == "TAPE_FALSE_ABSTAIN"
    assert row.cost_false_yes == 0.0
    assert row.cost_false_no == 0.0
    assert row.cost_human == 2.0
    # E[YES]=E[NO]=0 < E[HUMAN]=2 → YES/NO tie → NO (UNSURE then NO).
    assert row.chosen == "NO"
    assert row.new_hard_off is False
    assert row.as_dict()["tape_authority"]["false_abstain"] == 0
    assert tape_authority_facts()["false_abstain"] == 0


def test_false_admit_tape_costs_prefer_no() -> None:
    """false_abstain=0 ⇒ cost_false_no=0 ⇒ argmin is NO even at vendor HIGH."""

    row = log_cost_of_error(
        0.88,
        stake="sleeve_admit",
        ticket=FS_HALF_TICKETS[0],
        subclass="fs_half_still_losing",
    )
    assert row.chosen == "NO"
    assert row.naive_vendor_choice == "YES"
    assert row.moved is True
    assert row.cost_false_no == 0.0
    assert row.conf_gate_band == "CONF_GATE_STRICT"
    assert row.conf_floor == "HIGH"
    assert row.broker_effect is False
    assert row.g4_x_g6_overshrink is False
    assert row.cost_false_yes == pytest.approx(21.4804)
    assert row.new_hard_off is False
    assert row.as_dict()["tape_authority"]["false_admit_tape_R"] == pytest.approx(-28.9172)


def test_naive_vendor_is_not_truth() -> None:
    assert naive_vendor_choice(0.85) == "YES"
    assert naive_vendor_choice(0.62) == "UNSURE"
    assert naive_vendor_choice(0.35) == "NO"
    logged = log_conf_gate(0.91, stake="sleeve_admit")
    assert logged.band == "HIGH"
    assert logged.as_dict()["vendor_0_85_forbidden_as_truth"] is True


def test_missing_triple_stays_shadow() -> None:
    row = log_cost_of_error(0.7, stake="sleeve_admit")
    assert row.chosen is None
    assert row.conf_gate_band is None
    assert row.reason == "missing_cost_triple_stay_shadow"
    assert row.broker_effect is False


def test_place_is_infinity_veto() -> None:
    row = log_cost_of_error(0.99, stake="place", subclass="fs_half_still_losing")
    assert row.chosen == "VETO"
    assert row.place_veto is True
    assert row.gate_id == "ANY_PLACE"
    assert row.conf_gate_band is None
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


def test_shadow_bands_from_close_loop() -> None:
    session = log_cost_of_error(0.8, stake="sleeve_admit", subclass="session_cut_loss")
    assert session.conf_gate_band == "CONF_GATE_SESSION"
    assert session.conf_floor == "MED_HIGH"
    event = log_cost_of_error(0.7, stake="sleeve_admit", subclass="event_gap_shadow")
    assert event.conf_gate_band == "CONF_GATE_EVENT"
    assert event.conf_floor == "HIGH_EVENT_STAMP"
    review = log_cost_of_error(0.9, stake="sleeve_admit", ticket=REVIEW_KEEP_TICKET)
    assert review.subclass == "full_size_loss"
    assert review.conf_gate_band == "CONF_GATE_REVIEW"
    assert review.conf_floor == "KEEP_SURFACE"
    off = log_cost_of_error(
        0.8, stake="sleeve_admit", subclass="review_keep_offhours_false_structure"
    )
    assert off.chosen is None
    assert off.conf_gate_band is None
    assert off.reason == "review_not_hard_cost"
    assert off.new_hard_off is False
    assert off.review_keep_offhours is True
    assert review.new_hard_off is False
    assert review.review_keep_offhours is False


def test_event_band_never_invents_news(tmp_path: Path) -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id=f"challenge:{CHALLENGE_LOGIN}:291383082:metals_core:long",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.5,
        mom_20_atr=0.4,
        spine_empty=True,
        events=[{"impact": "HIGH", "event": "invented"}],
    )
    with pytest.raises(InventedNewsProtocolVeto):
        run_fluid_gate_cycle(
            inventory=_inv(),
            gold_state=gold,
            s14_answers=_ans(),
            log_dir=tmp_path,
            force=True,
        )


def test_cycle_logs_s15_beside_s14(tmp_path: Path) -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id=f"challenge:{CHALLENGE_LOGIN}:{FS_HALF_TICKETS[0]}:metals_core:long",
        close_ret_1=0.012,
        close_ret_5bar=0.03,
        vol_ratio=1.0,
        htf_slope_norm=0.8,
        mom_20_atr=0.6,
        session="off_hours",
    )
    gold["identity"]["ticket"] = FS_HALF_TICKETS[0]
    result = run_fluid_gate_cycle(
        inventory=_inv(),
        gold_state=gold,
        s14_answers=_ans("trend_up", 0.88),
        s14_research_thresholds=True,
        s14_g4_applies=True,
        s15_ticket=FS_HALF_TICKETS[0],
        log_dir=tmp_path,
        force=True,
        stake="sleeve_admit",
    )
    assert result.skipped is False
    assert result.regime is not None
    assert result.regime.gate_decision == "half_size"
    assert result.regime.size_factor == 0.5
    assert result.cost_of_error is not None
    assert result.cost_of_error.chosen == "NO"
    assert result.cost_of_error.conf_gate_band == "CONF_GATE_STRICT"
    assert result.apply.apply is False
    doc = json.loads(result.log_path.read_text(encoding="utf-8"))
    assert_live_cages(doc)
    assert doc["broker_effect"] is False
    assert doc["steal"] == "S14"
    assert doc["steal_s15"] == "S15"
    assert doc["cost_of_error"]["pick"] == "NO"
    assert doc["conf_gate"]["conf_gate_band"] == "CONF_GATE_STRICT"
    assert doc["conf_gate"]["vendor_0_85_forbidden_as_truth"] is True
    assert doc["conf_gate"]["new_hard_off"] is False
    assert doc["account_surface"]["login"] == CHALLENGE_LOGIN
    assert doc["s15_tape_authority"]["false_abstain"] == 0
    assert doc["s15_tape_authority"]["false_admit_n"] == 29
    assert doc["s15_tape_authority"]["false_admit_tape_R"] == pytest.approx(-28.9172)
    assert doc["s15_tape_authority"]["false_admit_shadow_R"] == pytest.approx(-13.5428)
    assert doc["s15_tape_authority"]["cost_avoided_by_reject_n"] == 23
    assert doc["s15_tape_authority"]["cost_avoided_by_reject_tape_R"] == pytest.approx(-24.6586)
    assert doc["s15_tape_authority"]["g4_x_g6_overshrink"] is False
    assert doc["s15_tape_authority"]["place"] == "infinity_veto"
    assert "s15_tape_authority_baked" in result.notes


def test_g4_x_g6_does_not_overshrink(tmp_path: Path) -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id="g4g6",
        close_ret_1=0.012,
        close_ret_5bar=0.03,
        vol_ratio=1.0,
        htf_slope_norm=0.8,
        mom_20_atr=0.6,
        session="london",
    )
    result = run_fluid_gate_cycle(
        inventory=_inv(),
        gold_state=gold,
        s14_answers=_ans("trend_up", 0.88),
        s14_research_thresholds=True,
        s14_g4_applies=True,
        s15_subclass="fs_half_still_losing",
        log_dir=tmp_path,
        force=True,
    )
    assert result.regime is not None
    assert result.regime.size_factor == 0.5
    assert result.regime.size_factor != 0.25
    assert result.cost_of_error is not None
    assert result.cost_of_error.g4_x_g6_overshrink is False
    # S15 does not rewrite S14 size.
    assert result.regime.chair.size_ceiling == 0.5


def test_keep_no_boost_review_ticket(tmp_path: Path) -> None:
    gold = gold_state(
        sleeve="vss_fxcross_london_up_low",
        symbol="EURGBP",
        side="sell",
        candidate_id=f"challenge:{CHALLENGE_LOGIN}:{REVIEW_KEEP_TICKET}:vss:sell",
        close_ret_1=0.001,
        close_ret_5bar=-0.002,
        vol_ratio=0.85,
        htf_slope_norm=0.05,
        mom_20_atr=-0.04,
        sma_frac=0.0,
        session="off_hours",
    )
    result = run_fluid_gate_cycle(
        inventory=_inv(),
        gold_state=gold,
        s14_answers=_ans("range", 0.90),
        s14_research_thresholds=True,
        s15_ticket=REVIEW_KEEP_TICKET,
        log_dir=tmp_path,
        force=True,
    )
    assert result.regime is not None
    assert result.regime.chair.keep_family is True
    assert result.regime.size_factor is None or result.regime.size_factor <= 1.0
    assert result.cost_of_error is not None
    assert result.cost_of_error.conf_gate_band == "CONF_GATE_REVIEW"
    assert result.cost_of_error.keep_no_boost is True
    assert result.cost_of_error.new_hard_off is False
    assert result.regime.chair.hard_off is False


def test_cycle_293128383_keep_offhours_not_hard_off(tmp_path: Path) -> None:
    """KEEP × Off_hours × false_structure is review, not a new hard-off."""

    gold = gold_state(
        sleeve="vss",
        symbol="XAUUSD",
        side="short",
        candidate_id=f"challenge:{CHALLENGE_LOGIN}:{REVIEW_OFFHOURS_TICKET}:vss:short",
        close_ret_1=-0.009,
        close_ret_5bar=-0.02,
        vol_ratio=1.0,
        htf_slope_norm=-0.6,
        mom_20_atr=-0.4,
        session="off_hours",
    )
    gold["identity"]["ticket"] = REVIEW_OFFHOURS_TICKET
    result = run_fluid_gate_cycle(
        inventory=_inv(),
        gold_state=gold,
        s14_answers=_ans("trend_down", 0.80),
        s14_research_thresholds=True,
        s15_ticket=REVIEW_OFFHOURS_TICKET,
        log_dir=tmp_path,
        force=True,
        stake="sleeve_admit",
    )
    assert result.skipped is False
    assert result.regime is not None
    assert result.regime.chair.keep_family is True
    assert result.regime.chair.hard_off is False
    assert result.cost_of_error is not None
    assert result.cost_of_error.ticket == REVIEW_OFFHOURS_TICKET
    assert result.cost_of_error.subclass == "review_keep_offhours_false_structure"
    assert result.cost_of_error.reason == "review_not_hard_cost"
    assert result.cost_of_error.conf_gate_band is None
    assert result.cost_of_error.new_hard_off is False
    assert result.cost_of_error.review_keep_offhours is True
    assert result.apply.apply is False
    doc = json.loads(result.log_path.read_text(encoding="utf-8"))
    assert doc["s15_tape_authority"]["new_hard_off"] is False
    assert doc["cost_of_error"]["review_keep_offhours"] is True
    assert doc["cost_of_error"]["new_hard_off"] is False
    assert "s15_review_293128383_keep_offhours_not_hard_off" in result.notes


def test_shadow_env_writes_s15_fields(tmp_path: Path) -> None:
    """GTOS_JEV_FLUID_GATES_SHADOW=1 writes tape facts without --force APPLY."""

    result = run_fluid_gate_cycle(
        inventory=_inv(),
        s15_subclass="fs_half_still_losing",
        answers={"next_gate": {"choice": "HOLD", "confidence": 0.88, "probabilities": {"HOLD": 0.88}}},
        log_dir=tmp_path,
        force=False,
        environ={SHADOW_ENV: "1"},
        stake="sleeve_admit",
    )
    assert result.skipped is False
    assert result.log_path is not None
    assert result.apply.apply is False
    doc = json.loads(result.log_path.read_text(encoding="utf-8"))
    assert doc["cost_of_error"]["subclass"] == "fs_half_still_losing"
    assert doc["cost_of_error"]["conf_gate_band"] == "CONF_GATE_STRICT"
    assert doc["s15_tape_authority"]["false_abstain"] == 0
    assert doc["s15_tape_authority"]["false_admit_tape_R"] == pytest.approx(-28.9172)
    assert doc["s15_tape_authority"]["place"] == "infinity_veto"
    assert_live_cages(doc)
    assert doc["broker_effect"] is False


def test_hard_off_not_weakened_by_s15(tmp_path: Path) -> None:
    gold = gold_state(
        sleeve="idxrev",
        symbol="UK100.cash",
        side="sell",
        candidate_id="idx",
        close_ret_1=-0.01,
        close_ret_5bar=-0.02,
        vol_ratio=1.1,
        htf_slope_norm=-0.7,
        mom_20_atr=-0.4,
    )
    result = run_fluid_gate_cycle(
        inventory=_inv(),
        gold_state=gold,
        s14_answers=_ans("trend_down", 0.91),
        s14_research_thresholds=True,
        s15_subclass="cost_avoided_by_reject",
        log_dir=tmp_path,
        force=True,
    )
    assert result.regime is not None
    assert result.regime.gate_decision == "stand_down"
    assert result.regime.chair.hard_off is True
    assert result.cost_of_error is not None
    assert result.cost_of_error.chosen is None
    assert result.cost_of_error.benefit_abs_R == pytest.approx(24.6586)
    assert result.apply.apply is False


def test_shadow_flag_off_writes_nothing(tmp_path: Path) -> None:
    result = run_fluid_gate_cycle(
        inventory=_inv(),
        s15_subclass="fs_half_still_losing",
        log_dir=tmp_path,
        force=False,
        shadow=False,
    )
    assert result.skipped is True
    assert list(tmp_path.rglob("*.json")) == []


def test_tape_has_close_loop_identities() -> None:
    rows = s15_historical_tape_rows()
    tickets = {str(r.get("ticket")) for r in rows if r.get("ticket")}
    assert all(r["login"] == CHALLENGE_LOGIN for r in rows)
    assert set(FS_HALF_TICKETS) <= tickets
    assert REVIEW_KEEP_TICKET in tickets
    assert "293128383" in tickets
    assert TICKET_SUBCLASS[FS_HALF_TICKETS[0]] == "fs_half_still_losing"
    assert len(FS_HALF_TICKETS) == 21


def test_historical_prove_scorecard_offline(tmp_path: Path) -> None:
    from scripts.run_s15_historical_prove import main

    score = tmp_path / "score.json"
    tape = tmp_path / "tape.jsonl"
    rc = main(["--force", "--log-dir", str(tmp_path / "logs"), "--score-out", str(score), "--write-tape", str(tape)])
    assert rc == 0
    card = json.loads(score.read_text(encoding="utf-8"))
    assert card["n_decidable"] >= 20
    assert card["n_moved"] >= 5
    assert card["n_invented_high"] == 0
    assert card["n_order_send"] == 0
    assert card["n_false_abstain"] == 0
    assert card["g4_x_g6_overshrink"] is False
    assert card["place_infinity_veto"] is True
    assert card["broker_effect_all_false"] is True
    assert card["vendor_0_85_forbidden_as_truth"] is True
    assert card["s15_tape_authority"]["false_abstain"] == 0
    assert card["s15_tape_authority"]["false_admit_n"] == 29
    assert card["s15_tape_authority"]["false_admit_tape_R"] == pytest.approx(-28.9172)
    assert card["s15_tape_authority"]["false_admit_shadow_R"] == pytest.approx(-13.5428)
    assert card["s15_tape_authority"]["cost_avoided_by_reject_tape_R"] == pytest.approx(-24.6586)
    assert card["s15_tape_authority"]["g4_x_g6_overshrink"] is False
    assert card["pass"] is True
    assert tape.is_file()
    logs = list((tmp_path / "logs").rglob("*.json"))
    assert logs
    for path in logs:
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert_live_cages(doc)
        assert doc["broker_effect"] is False
        assert doc["account_surface"]["login"] == CHALLENGE_LOGIN
        if "cost_of_error" in doc:
            assert doc["cost_of_error"]["broker_effect"] is False
            assert doc["cost_of_error"]["new_hard_off"] is False
        if "s15_tape_authority" in doc:
            assert doc["s15_tape_authority"]["false_abstain"] == 0
            assert doc["s15_tape_authority"]["place"] == "infinity_veto"


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
