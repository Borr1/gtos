"""Behavioural tests for Challenge ALIVE_MENU / CONF_GATE / DONE_OUTSIDE.

No broker, no TypeSafe network, no writes under shadow_logs/.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.judgment.alive_menu import StaleMenuError, assert_menu_fresh, rebuild_choice_criteria
from src.judgment.challenge import (
    CHALLENGE_LOGIN,
    VERIFICATION_QUARANTINED,
    PayoutWriterError,
    QuarantinedAccountError,
    assert_challenge_payout_writer,
)
from src.judgment.conf_gate import confidence_band, extract_confidence, log_conf_gate, noul_concentration
from src.judgment.cycle import REQUIRED_LOG_CONSTS, REQUIRED_LOG_KEYS, run_fluid_gate_cycle
from src.judgment.done_outside import completion_truth, verify_artifact, verify_side_effect
from src.judgment.flags import apply_authorized, apply_enabled, shadow_enabled
from src.judgment.inventory import (
    ESCAPE_HATCHES,
    MAX_CHOICE_OPTIONS,
    collect_live_inventory,
    inventory_fingerprint,
)
from src.judgment.veto import InventedNewsProtocolVeto, JevPlacePathVeto, refuse_broker_action

REPO = Path(__file__).resolve().parents[2]
JUDGMENT_SRC = REPO / "src" / "judgment"


def _inventory(**kwargs):
    return collect_live_inventory(
        sleeves=kwargs.get("sleeves", ("spring", "vss")),
        workers=kwargs.get("workers", ("challenge:0",)),
        handlers=kwargs.get("handlers", ("shadow_log", "label_draft")),
        include_w7_armed=False,
        include_launcher_workers=False,
    )


def test_flags_default_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GTOS_JEV_FLUID_GATES_SHADOW", raising=False)
    monkeypatch.delenv("GTOS_JEV_FLUID_GATES_APPLY", raising=False)
    assert shadow_enabled() is False
    assert apply_enabled() is False


def test_challenge_is_sole_payout_writer() -> None:
    assert_challenge_payout_writer(CHALLENGE_LOGIN)
    with pytest.raises(QuarantinedAccountError):
        assert_challenge_payout_writer(VERIFICATION_QUARANTINED)
    with pytest.raises(PayoutWriterError):
        assert_challenge_payout_writer("ftmo_w7")


def test_alive_menu_rebuilds_when_inventory_changes() -> None:
    first = _inventory(sleeves=("spring", "vss"))
    menu1 = rebuild_choice_criteria(first)
    assert menu1.rebuilt is True
    assert all(name in menu1.option_ids for name in ESCAPE_HATCHES)
    assert "sleeve:spring" in menu1.option_ids
    assert "sleeve:vss" in menu1.option_ids

    second = _inventory(sleeves=("spring",))  # vss dropped this cycle
    menu2 = rebuild_choice_criteria(second, prior_menu=menu1)
    assert menu2.inventory_changed is True
    assert menu2.rebuilt is True
    assert menu2.cycle_id != menu1.cycle_id
    assert "sleeve:vss" not in menu2.option_ids
    assert "sleeve:spring" in menu2.option_ids
    with pytest.raises(StaleMenuError):
        assert_menu_fresh(menu1, second)


def test_alive_menu_still_rebuilds_when_inventory_unchanged() -> None:
    inv = _inventory()
    menu1 = rebuild_choice_criteria(inv)
    menu2 = rebuild_choice_criteria(inv, prior_menu=menu1)
    assert menu2.rebuilt is True
    assert menu2.inventory_changed is False
    assert menu2.cycle_id != menu1.cycle_id
    assert_menu_fresh(menu2, inv)


def test_alive_menu_caps_at_255_and_keeps_escapes() -> None:
    sleeves = tuple(f"s{i:03d}" for i in range(300))
    inv = _inventory(sleeves=sleeves, workers=(), handlers=())
    menu = rebuild_choice_criteria(inv)
    assert len(menu.criteria) <= MAX_CHOICE_OPTIONS
    assert all(name in menu.option_ids for name in ESCAPE_HATCHES)


def test_hard_off_sleeves_are_not_choice_options() -> None:
    inv = collect_live_inventory(
        sleeves=("spring", "bleed", "mx_us30"),
        workers=("challenge:0",),
        handlers=("shadow_log",),
        include_w7_armed=False,
        include_launcher_workers=False,
    )
    assert "bleed" not in inv.sleeves
    assert "mx_us30" not in inv.sleeves
    assert "bleed" in inv.blocked_sleeves
    menu = rebuild_choice_criteria(inv)
    assert "sleeve:bleed" not in menu.option_ids
    assert "sleeve:spring" in menu.option_ids


def test_collect_live_inventory_reads_w7_armed_and_launcher() -> None:
    inv = collect_live_inventory(sleeves=None, workers=None)
    assert "spring" in inv.sleeves
    assert "vss" in inv.sleeves
    # Live W7 declaration on this tree.
    assert "crypto" in inv.sleeves
    assert "energy_agri" in inv.sleeves
    assert "sub_xvol_pullback" in inv.sleeves
    assert "challenge:0" in inv.workers
    assert "operator_profile" in inv.workers
    assert "redacted_account_live_bee34003" in inv.workers
    assert inv.fingerprint == inventory_fingerprint(
        inv.sleeves, inv.workers, inv.handlers, inv.blocked_sleeves
    )


def test_confidence_bands() -> None:
    assert confidence_band(0.49) == "LOW"
    assert confidence_band(0.50) == "MED"
    assert confidence_band(0.84) == "MED"
    assert confidence_band(0.85) == "HIGH"
    assert confidence_band(None) == "LOW"
    assert noul_concentration(0.5) == 0.0
    assert noul_concentration(1.0) == 1.0


def test_conf_gate_never_sets_broker_effect() -> None:
    for conf, stake in ((0.2, "sleeve_admit"), (0.7, "label_assist"), (0.99, "sleeve_admit"), (0.99, "place")):
        row = log_conf_gate(conf, stake=stake)
        assert row.broker_effect is False
    veto = log_conf_gate(0.99, stake="flatten")
    assert veto.band == "VETO"
    assert veto.disposition == "veto_place_path"


def test_extract_confidence_from_choice_and_noul() -> None:
    conf, src = extract_confidence(
        {"next_gate": {"choice": "HOLD", "confidence": 0.62, "probabilities": {"HOLD": 0.62}}},
        key="next_gate",
    )
    assert conf == pytest.approx(0.62)
    assert src == "choice_or_score_confidence"
    conf, src = extract_confidence({"evidence_enough": {"noul": 0.75}}, key="evidence_enough")
    assert conf == pytest.approx(0.5)
    assert src == "noul_distance_from_half"


def test_apply_requires_flag_and_prove_and_never_place() -> None:
    from src.judgment.flags import ProveReceipt

    receipt = ProveReceipt("UB-AUTH-010", "A1", True, "chair")
    denied = apply_authorized(
        stake="sleeve_admit", apply_flag=False, receipt=receipt, band="HIGH", required_band="HIGH"
    )
    assert denied.apply is False
    assert denied.reason == "apply_flag_off"
    no_receipt = apply_authorized(
        stake="label_assist", apply_flag=True, receipt=None, band="HIGH", required_band="MED"
    )
    assert no_receipt.apply is False
    place = apply_authorized(
        stake="place", apply_flag=True, receipt=receipt, band="HIGH", required_band="VETO"
    )
    assert place.apply is False
    assert place.mode == "veto"
    ok = apply_authorized(
        stake="label_assist", apply_flag=True, receipt=receipt, band="MED", required_band="MED"
    )
    assert ok.apply is True
    assert ok.mode == "apply_label"
    a0 = apply_authorized(
        stake="label_assist",
        apply_flag=True,
        receipt=ProveReceipt("x", "A0", True, "no"),
        band="HIGH",
        required_band="MED",
    )
    assert a0.apply is False


def test_done_outside_ignores_jev_done(tmp_path: Path) -> None:
    missing = verify_artifact(tmp_path / "nope.json", required_keys=("schema",))
    assert missing.ok is False
    assert completion_truth(jev_choice="DONE", verify=missing) == "NOT_DONE_JEV_ADVISORY_ONLY"
    good = tmp_path / "ok.json"
    good.write_text(json.dumps({"schema": "jev_fluid_gate_v1", "never_place": True}), encoding="utf-8")
    verified = verify_side_effect(
        "shadow_log",
        path=good,
        required_keys=("schema", "never_place"),
        required_consts={"never_place": True},
    )
    assert verified.ok is True
    assert completion_truth(jev_choice="CONTINUE", verify=verified) == "DONE"
    with pytest.raises(JevPlacePathVeto):
        verify_side_effect("order_send", path=good)


def test_cycle_shadow_log_and_no_apply(tmp_path: Path) -> None:
    inv = _inventory()
    result = run_fluid_gate_cycle(
        inventory=inv,
        answers={"next_gate": {"choice": "HOLD", "confidence": 0.91, "probabilities": {"HOLD": 0.91}}},
        stake="sleeve_admit",
        log_dir=tmp_path,
        force=True,
        apply_flag=False,
        jev_done_choice="DONE",
    )
    assert result.skipped is False
    assert result.conf_gate.band == "HIGH"
    assert result.conf_gate.broker_effect is False
    assert result.apply.apply is False
    assert result.apply_path is None
    assert result.log_path is not None and result.log_path.is_file()
    assert result.verify.ok is True
    # Code owns DONE even though Jev said DONE — log matched, so DONE.
    assert result.completion == "DONE"
    doc = json.loads(result.log_path.read_text(encoding="utf-8"))
    for key in REQUIRED_LOG_KEYS:
        assert key in doc
    for key, value in REQUIRED_LOG_CONSTS.items():
        assert doc[key] == value
    assert doc["account_surface"]["login"] == CHALLENGE_LOGIN
    assert "HOLD" in doc["alive_menu"]["option_ids"]


def test_cycle_skips_when_shadow_flag_off(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GTOS_JEV_FLUID_GATES_SHADOW", raising=False)
    result = run_fluid_gate_cycle(
        inventory=_inventory(),
        log_dir=tmp_path,
        force=False,
        shadow=False,
    )
    assert result.skipped is True
    assert result.log_path is None
    assert list(tmp_path.rglob("*.json")) == []


def test_cycle_apply_label_only_behind_prove(tmp_path: Path) -> None:
    prove = tmp_path / "prove"
    prove.mkdir()
    (prove / "UB-PLC-017.json").write_text(
        json.dumps(
            {
                "site_id": "UB-PLC-017",
                "wire_class": "A1",
                "proven": True,
                "owner_word": "chair named cost-vs-geometry",
            }
        ),
        encoding="utf-8",
    )
    result = run_fluid_gate_cycle(
        inventory=_inventory(),
        answers={"next_gate": {"choice": "LABEL", "confidence": 0.7, "probabilities": {"LABEL": 0.7}}},
        stake="label_assist",
        log_dir=tmp_path / "logs",
        prove_dir=prove,
        prove_site_id="UB-PLC-017",
        force=True,
        apply_flag=True,
    )
    assert result.apply.apply is True
    assert result.apply_path is not None and result.apply_path.is_file()
    draft = json.loads(result.apply_path.read_text(encoding="utf-8"))
    assert draft["chair_verb"] == "LABEL"
    assert draft["never_place"] is True
    assert draft["broker_effect"] is False


def test_cycle_high_confidence_place_stake_still_vetoes(tmp_path: Path) -> None:
    prove = tmp_path / "prove"
    prove.mkdir()
    (prove / "site.json").write_text(
        json.dumps({"site_id": "site", "wire_class": "W_named", "proven": True, "owner_word": "x"}),
        encoding="utf-8",
    )
    result = run_fluid_gate_cycle(
        inventory=_inventory(),
        answers={"next_gate": {"choice": "HOLD", "confidence": 0.99, "probabilities": {"HOLD": 0.99}}},
        stake="place",
        log_dir=tmp_path / "logs",
        prove_dir=prove,
        prove_site_id="site",
        force=True,
        apply_flag=True,
    )
    assert result.apply.apply is False
    assert result.apply.mode == "veto"
    assert result.apply_path is None
    assert result.conf_gate.broker_effect is False


def test_cycle_refuses_verification_login(tmp_path: Path) -> None:
    with pytest.raises(QuarantinedAccountError):
        run_fluid_gate_cycle(
            login=VERIFICATION_QUARANTINED,
            inventory=_inventory(),
            log_dir=tmp_path,
            force=True,
        )


def test_cycle_refuses_invented_news_protocol(tmp_path: Path) -> None:
    with pytest.raises(InventedNewsProtocolVeto):
        run_fluid_gate_cycle(
            inventory=_inventory(),
            log_dir=tmp_path,
            force=True,
            invented_files=("NEWS_PROTOCOL",),
        )


def test_cycle_refuses_place_choice_in_answers(tmp_path: Path) -> None:
    with pytest.raises(JevPlacePathVeto):
        run_fluid_gate_cycle(
            inventory=_inventory(),
            answers={"action_scope": {"choice": "flatten", "confidence": 1.0}},
            log_dir=tmp_path,
            force=True,
        )


def test_cycle_allows_zero_flatten_probability_mass(tmp_path: Path) -> None:
    """Lab corr-HOLD payloads often include flatten: 0.0 without selecting it."""

    result = run_fluid_gate_cycle(
        inventory=_inventory(),
        answers={
            "action_scope": {
                "choice": "audit_only",
                "confidence": 1.0,
                "probabilities": {"audit_only": 1.0, "flatten": 0.0},
            }
        },
        stake="corr_hold",
        log_dir=tmp_path,
        force=True,
    )
    assert result.verify.ok is True
    assert result.apply.apply is False


def test_cli_force_writes_shadow_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import run_jev_fluid_gates_shadow as cli

    monkeypatch.delenv("GTOS_JEV_FLUID_GATES_SHADOW", raising=False)
    rc = cli.main(
        [
            "--force",
            "--log-dir",
            str(tmp_path),
            "--confidence",
            "0.4",
            "--stake",
            "sleeve_admit",
        ]
    )
    assert rc == 0
    logs = list(tmp_path.rglob("*.json"))
    assert len(logs) == 1
    doc = json.loads(logs[0].read_text(encoding="utf-8"))
    assert doc["conf_gate"]["band"] == "LOW"
    assert doc["broker_effect"] is False


def test_score_steals_attached() -> None:
    text = (REPO / "judgment" / "GTOS_SCORE_STEALS.md").read_text(encoding="utf-8")
    assert "ENFORCE ALIVE_MENU" in text
    assert "ENFORCE CONF_GATE" in text
    assert "ENFORCE DONE_OUTSIDE" in text
    assert "ENFORCE S14_REGIME_GATE_SHADOW" in text
    assert "ENFORCE S15_COST_OF_ERROR" in text
    assert "VETO PLACE_PATH" in text
    assert "VETO NEWS_PROTOCOL" in text
    chair = (REPO / "judgment" / "CHAIR_ENABLE_SHADOW_CHALLENGE.md").read_text(encoding="utf-8")
    assert "GTOS_JEV_FLUID_GATES_SHADOW=1" in chair
    assert "0" in chair


def test_judgment_package_has_no_broker_imports() -> None:
    banned_roots = ("mt5", "MetaTrader5", "book_owner", "mt5_real")
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
            if isinstance(node, ast.Call):
                name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                assert name != "order_send"
                assert name != "open_trade"


def test_refuse_broker_action_is_unconditional() -> None:
    for action in ("place", "remint", "flatten", "order_send", "mint_token"):
        with pytest.raises(JevPlacePathVeto):
            refuse_broker_action(action)
