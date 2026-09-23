"""Behavioural tests for conf_gate_order_block + OD-13 ensemble consume.

HIGH blocks. Vendor det false → MED. No standalone ORDER_ENSEMBLE.
Dig never broker-sends. Challenge 0 only.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.judgment.alive_menu import rebuild_choice_criteria
from src.judgment.challenge import CHALLENGE_LOGIN
from src.judgment.conf_gate import conf_gate_order_block, noul_vs_choice_shape
from src.judgment.cycle import REQUIRED_LOG_KEYS, run_fluid_gate_cycle
from src.judgment.inventory import collect_live_inventory
from src.judgment.od13_ensemble import (
    StandaloneOrderEnsembleError,
    compose_od13_ensemble,
    refuse_standalone_order_ensemble,
    standalone_apply_status,
)
from src.judgment.order_ensemble_shuffle import (
    APPLY_ENABLED,
    apply_od_10_perm_avg_research_router,
    apply_od_12_yesno_reverse_regression,
    apply_order_ensemble,
    apply_order_ensemble_shuffle,
)
from src.judgment.place_choice import stamp_place_choice
from src.judgment.veto import InventedNewsProtocolVeto


def _inventory():
    return collect_live_inventory(
        sleeves=("spring", "vss"),
        workers=("challenge:0",),
        handlers=("shadow_log", "label_draft"),
        include_w7_armed=False,
        include_launcher_workers=False,
        include_research_armed=False,
    )


def test_high_block_when_vendor_deterministic() -> None:
    row = conf_gate_order_block(0.91, vendor_deterministic=True, stake="sleeve_admit")
    assert row.band == "HIGH"
    assert row.blocked is True
    assert row.disposition == "order_block_high"
    assert row.vendor_det_false_downgraded is False
    assert row.broker_effect is False
    assert row.never_place is True
    assert row.consume == "CONF_ORDER_CONSUME"


def test_vendor_det_false_downgrades_high_to_med() -> None:
    row = conf_gate_order_block(0.91, vendor_deterministic=False, stake="sleeve_admit")
    assert row.band == "MED"
    assert row.blocked is False
    assert row.disposition == "order_review_med"
    assert row.vendor_det_false_downgraded is True
    assert row.as_dict()["vendor_0_85_forbidden_as_truth"] is True


def test_low_stays_shadow() -> None:
    row = conf_gate_order_block(0.2, vendor_deterministic=True)
    assert row.band == "LOW"
    assert row.blocked is False
    assert row.disposition == "shadow_only"


def test_place_stake_still_vetoes() -> None:
    row = conf_gate_order_block(0.99, vendor_deterministic=True, stake="place")
    assert row.band == "VETO"
    assert row.blocked is True
    assert row.disposition == "veto_place_path"
    assert row.broker_effect is False


def test_noul_vs_choice_shape_consume() -> None:
    undecided = noul_vs_choice_shape(choice_confidence=0.9, noul=None)
    assert undecided["decidable"] is False
    assert undecided["consume"] == "noul_vs_choice_shape"
    agree = noul_vs_choice_shape(choice_confidence=0.9, noul=0.95)
    assert agree["decidable"] is True
    assert agree["agree"] is True
    disagree = noul_vs_choice_shape(choice_confidence=0.9, noul=0.5)
    assert disagree["agree"] is False
    assert disagree["choice_band"] == "HIGH"
    assert disagree["noul_band"] == "LOW"
    assert disagree["broker_effect"] is False


def test_shape_disagreement_downgrades_high() -> None:
    row = conf_gate_order_block(
        0.91,
        vendor_deterministic=True,
        choice_confidence=0.91,
        noul=0.5,
    )
    assert row.band == "MED"
    assert row.vendor_det_false_downgraded is True
    assert row.blocked is False


def test_od13_already_live_under_place_apply() -> None:
    menu = rebuild_choice_criteria(_inventory())
    stamp = stamp_place_choice(menu=menu)
    block = conf_gate_order_block(0.91, vendor_deterministic=True)
    row = compose_od13_ensemble(place_choice=stamp, conf_order=block)
    assert row["consume"] == "od_13"
    assert row["verdict"] == "ALREADY_LIVE"
    assert row["already_live_under"] == "PLACE_APPLY"
    assert row["place_apply"] is True
    assert row["place_ensemble"] is True
    assert row["standalone_order_ensemble"] is False
    assert "order_ensemble_shuffle" in row["killed_standalone_apply"]
    assert row["pack1b_beaten"] is False
    assert row["broker_effect"] is False
    assert row["dig_never_broker_send"] is True


def test_no_standalone_order_ensemble_path() -> None:
    with pytest.raises(StandaloneOrderEnsembleError, match="od_13"):
        refuse_standalone_order_ensemble("ORDER_ENSEMBLE")
    with pytest.raises(StandaloneOrderEnsembleError):
        apply_order_ensemble_shuffle()
    with pytest.raises(StandaloneOrderEnsembleError):
        apply_order_ensemble()
    with pytest.raises(StandaloneOrderEnsembleError):
        apply_od_10_perm_avg_research_router()
    with pytest.raises(StandaloneOrderEnsembleError):
        apply_od_12_yesno_reverse_regression()
    assert APPLY_ENABLED is False
    kills = standalone_apply_status()
    assert kills["order_ensemble_shuffle"]["verdict"] == "KILL_ENFORCE"
    assert kills["od_10_perm_avg_research_router"]["verdict"] == "KILL_ENFORCE"
    assert kills["od_12_yesno_reverse_regression"]["reason"] == "ci_only"


def test_od13_refuses_shuffle_path_name() -> None:
    menu = rebuild_choice_criteria(_inventory())
    stamp = stamp_place_choice(menu=menu)
    block = conf_gate_order_block(0.4)
    with pytest.raises(StandaloneOrderEnsembleError):
        compose_od13_ensemble(
            place_choice=stamp,
            conf_order=block,
            path_name="order_ensemble_shuffle",
        )


def test_od13_refuses_invented_news() -> None:
    menu = rebuild_choice_criteria(_inventory())
    stamp = stamp_place_choice(menu=menu)
    block = conf_gate_order_block(0.4)
    with pytest.raises(InventedNewsProtocolVeto):
        compose_od13_ensemble(
            place_choice=stamp,
            conf_order=block,
            invented_files=("NEWS_PROTOCOL",),
        )


def test_cycle_stamps_place_choice_and_conf_order(tmp_path: Path) -> None:
    result = run_fluid_gate_cycle(
        inventory=_inventory(),
        answers={"next_gate": {"choice": "HOLD", "confidence": 0.91, "probabilities": {"HOLD": 0.91}}},
        stake="sleeve_admit",
        log_dir=tmp_path,
        force=True,
        apply_flag=False,
    )
    assert result.place_choice is not None
    assert result.place_choice.complete is True
    assert result.place_choice.broker_effect is False
    assert result.conf_order is not None
    # Vendor is not truth — HIGH downgrades to MED on the order-block stamp.
    assert result.conf_order.band == "MED"
    assert result.conf_order.vendor_det_false_downgraded is True
    assert result.conf_order.blocked is False
    assert result.od13_ensemble is not None
    assert result.od13_ensemble["verdict"] == "ALREADY_LIVE"
    assert result.od13_ensemble["standalone_order_ensemble"] is False
    doc = json.loads(result.log_path.read_text(encoding="utf-8"))
    for key in ("place_choice", "conf_order_block", "od13_ensemble", "already_live_consume"):
        assert key in REQUIRED_LOG_KEYS
        assert key in doc
    assert doc["place_choice"]["complete"] is True
    assert doc["already_live_consume"]["new_broker_flags"] == []
    assert doc["already_live_consume"]["pack1b_beaten"] is False
    assert doc["account_surface"]["login"] == CHALLENGE_LOGIN
    assert doc["broker_effect"] is False
    assert "jev_repeatability_probe" in doc
    assert doc["jev_repeatability_probe"]["repeatable"] is True


def test_cycle_still_never_places_from_dig(tmp_path: Path) -> None:
    result = run_fluid_gate_cycle(
        inventory=_inventory(),
        answers={"next_gate": {"choice": "HOLD", "confidence": 0.99}},
        stake="place",
        log_dir=tmp_path,
        force=True,
        apply_flag=True,
    )
    assert result.apply.apply is False
    assert result.conf_order.band == "VETO"
    assert result.conf_order.blocked is True
    assert result.conf_gate.broker_effect is False
    assert result.place_choice.broker_effect is False


def test_conf_order_modules_have_no_order_send() -> None:
    root = Path(__file__).resolve().parents[2] / "src" / "judgment"
    for name in (
        "conf_gate.py",
        "od13_ensemble.py",
        "order_ensemble_shuffle.py",
        "place_consume_flags.py",
        "cycle.py",
    ):
        tree = ast.parse((root / name).read_text(encoding="utf-8"), filename=name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                assert fn not in {"order_send", "open_trade"}
            if isinstance(node, ast.ImportFrom):
                assert "mt5" not in (node.module or "").lower()
                assert "book_owner" not in (node.module or "").lower()
