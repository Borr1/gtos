"""P0 warroom_shadow stubs — Challenge-true fixtures, never order_send."""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path

import pytest

from src.judgment.challenge import CHALLENGE_LOGIN
from src.judgment.conf_gate import REVIEW_KEEP_TICKET
from src.judgment.cycle import REQUIRED_LOG_KEYS, run_fluid_gate_cycle
from src.judgment.flags import APPLY_ENV, SHADOW_ENV, apply_enabled
from src.judgment.inventory import collect_live_inventory
from src.judgment.p0_shadow_hooks import (
    compose_warroom_shadow,
    keep_signature_from_state,
    load_band_weights,
)
from src.judgment.s14_tape import gold_state
from src.judgment.s15_tape import FS_HALF_TICKETS
from src.judgment.s16_flags import APPLY_ENV as DIG_APPLY_ENV
from src.judgment.veto import InventedNewsProtocolVeto
from tests.judgment.cages import assert_live_cages

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


def test_keep_signature_ignores_sleeve_name_allowlist() -> None:
    """Affinity law: a KEEP *name* without STATE is not KEEP."""

    gold = gold_state(
        sleeve="spring",
        symbol="XAUUSD",
        side="long",
        candidate_id=f"challenge:{CHALLENGE_LOGIN}:name-only:spring:long",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.5,
        mom_20_atr=0.4,
    )
    keep = keep_signature_from_state(gold)
    assert keep["present"] is False
    assert keep["noul"] == 0.0
    assert keep["name_allowlist_used"] is False
    assert keep["affinity"]["instrument"] == "XAUUSD"
    assert keep["affinity"]["sleeve"] == "spring"
    assert keep["affinity"]["global_rule"] is False


def test_keep_signature_from_state_not_name() -> None:
    """Non-KEEP name + STATE keep_signature ⇒ KEEP noul 1.0."""

    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id=f"challenge:{CHALLENGE_LOGIN}:state-keep:metals_core:long",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.5,
        mom_20_atr=0.4,
    )
    gold["identity"]["keep_signature"] = True
    keep = keep_signature_from_state(gold)
    assert keep["present"] is True
    assert keep["noul"] == 1.0
    assert keep["source"] == "identity.keep_signature"
    assert keep["name_allowlist_used"] is False


def test_fire_1201_floors_do_not_flip_apply() -> None:
    weights = load_band_weights()
    assert weights["apply"] is False
    assert weights["numeric_conf_on_hist_labels"] is False
    assert weights["do_not_flip_apply"] is True
    for name in ("STRICT", "SESSION", "EVENT", "REVIEW", "KEEP"):
        band = weights["bands"][name]
        assert band["apply"] is False


def test_apply_and_dig_apply_stay_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(APPLY_ENV, raising=False)
    monkeypatch.delenv(DIG_APPLY_ENV, raising=False)
    monkeypatch.delenv(SHADOW_ENV, raising=False)
    assert apply_enabled() is False
    assert os.environ.get(APPLY_ENV) is None
    assert os.environ.get(DIG_APPLY_ENV) is None


def test_fs_nonkeep_stand_down_and_family_loser() -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="short",
        candidate_id=f"challenge:{CHALLENGE_LOGIN}:{FS_HALF_TICKETS[0]}:metals_core:short",
        close_ret_1=-0.012,
        close_ret_5bar=-0.03,
        vol_ratio=1.0,
        htf_slope_norm=-0.6,
        mom_20_atr=-0.4,
    )
    gold["identity"]["ticket"] = FS_HALF_TICKETS[0]
    gold["identity"]["s15_subclass"] = "fs_half_still_losing"
    gold["identity"]["cf_d_miss"] = "false_structure"
    gold["identity"]["cf_d_outcome"] = "LOSS"
    gold["identity"]["keep_signature"] = False
    row = compose_warroom_shadow(
        gold_state=gold,
        cost={"conf_gate_band": "CONF_GATE_STRICT", "ticket": FS_HALF_TICKETS[0]},
    ).as_dict()
    assert row["apply"] is False
    assert row["broker_effect"] is False
    assert row["conf_gate_band_disposition"] == "STRICT"
    assert row["P0_CFD_MISS_FALSE_STRUCTURE"]["choice"] == "STAND_DOWN"
    assert row["P0_CFD_SIZE_INTENT"]["choice"] == "STAND_DOWN"
    assert row["P0_KEEP_REVIEW_WIN_VS_FAMILY_LOSER"]["choice"] == "FAMILY_LOSER"
    assert row["P0_CFD_SLEEVE_FAMILY_KEEP_SIG"]["noul"] == 0.0
    assert row["P0_CFD_SLEEVE_FAMILY_KEEP_SIG"]["name_allowlist_used"] is False
    assert row["cost_kill_gate"] is False


def test_state_keep_exempts_fs_and_stamps_keep_noul() -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id=f"challenge:{CHALLENGE_LOGIN}:293128383:metals_core:long",
        close_ret_1=-0.009,
        close_ret_5bar=-0.02,
        vol_ratio=1.0,
        htf_slope_norm=-0.5,
        mom_20_atr=-0.3,
        session="off_hours",
    )
    gold["identity"]["ticket"] = "293128383"
    gold["identity"]["cf_d_miss"] = "false_structure"
    gold["identity"]["keep_signature"] = True
    row = compose_warroom_shadow(gold_state=gold).as_dict()
    assert row["apply"] is False
    assert row["P0_CFD_MISS_FALSE_STRUCTURE"]["choice"] == "KEEP_EXEMPT"
    assert row["P0_CFD_SIZE_INTENT"]["choice"] == "KEEP_CAP"
    assert row["P0_CFD_SLEEVE_FAMILY_KEEP_SIG"]["present"] is True
    assert row["P0_CFD_SLEEVE_FAMILY_KEEP_SIG"]["noul"] == 1.0
    assert row["conf_gate_band_disposition"] == "KEEP"


def test_review_keep_ticket_291087142() -> None:
    gold = gold_state(
        sleeve="vss",
        symbol="EURGBP",
        side="short",
        candidate_id=f"challenge:{CHALLENGE_LOGIN}:{REVIEW_KEEP_TICKET}:vss:short",
        close_ret_1=-0.002,
        close_ret_5bar=-0.004,
        vol_ratio=0.9,
        htf_slope_norm=0.05,
        mom_20_atr=-0.04,
    )
    gold["identity"]["ticket"] = REVIEW_KEEP_TICKET
    gold["identity"]["keep_signature"] = True
    gold["identity"]["cf_d_miss"] = "false_structure"
    row = compose_warroom_shadow(
        gold_state=gold,
        cost={"conf_gate_band": "CONF_GATE_REVIEW", "ticket": REVIEW_KEEP_TICKET},
    ).as_dict()
    assert row["apply"] is False
    assert row["conf_gate_band_disposition"] == "REVIEW"
    assert row["P0_KEEP_REVIEW_WIN_VS_FAMILY_LOSER"]["choice"] == "REVIEW_KEEP"
    assert row["P0_CFD_MISS_FALSE_STRUCTURE"]["choice"] == "KEEP_EXEMPT"
    assert row["login"] == CHALLENGE_LOGIN


def test_cycle_stamps_warroom_shadow_challenge_true(tmp_path: Path) -> None:
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
    gold["identity"]["keep_signature"] = False
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
    assert result.apply.apply is False
    assert result.warroom_shadow is not None
    pack = result.warroom_shadow.as_dict()
    assert pack["apply"] is False
    assert pack["broker_effect"] is False
    assert pack["never_place"] is True
    assert pack["conf_gate_band_disposition"] == "STRICT"
    assert pack["P0_CFD_MISS_FALSE_STRUCTURE"]["choice"] == "STAND_DOWN"
    assert "warroom_shadow" in REQUIRED_LOG_KEYS
    doc = json.loads(result.log_path.read_text(encoding="utf-8"))
    assert doc["account_surface"]["login"] == CHALLENGE_LOGIN
    assert doc["warroom_shadow"]["apply"] is False
    assert doc["warroom_shadow"]["P0_CFD_SIZE_INTENT"]["never_apply_size"] is True
    assert doc["broker_effect"] is False
    assert_live_cages(doc)
    assert "chair_p0_apply_always_false" in result.notes


def test_shadow_flag_off_still_does_not_apply(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(SHADOW_ENV, raising=False)
    monkeypatch.delenv(APPLY_ENV, raising=False)
    result = run_fluid_gate_cycle(
        inventory=_inv(),
        log_dir=tmp_path,
        force=False,
        stake="sleeve_admit",
    )
    assert result.skipped is True
    assert result.log_path is None
    assert result.apply.apply is False
    assert result.warroom_shadow is not None
    assert result.warroom_shadow.as_dict()["apply"] is False


def test_event_band_never_invents_news(tmp_path: Path) -> None:
    gold = gold_state(
        sleeve="metals_core",
        symbol="XAUUSD",
        side="long",
        candidate_id=f"challenge:{CHALLENGE_LOGIN}:291383082:metals_core:long",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.4,
        mom_20_atr=0.3,
        spine_empty=False,
        events=[{"source": "stamped", "stamped": True, "proximity": True}],
    )
    gold["identity"]["ticket"] = "291383082"
    gold["identity"]["s15_subclass"] = "event_gap_shadow"
    gold["identity"]["cf_d_miss"] = "event_gap"
    gold["identity"]["keep_signature"] = False
    result = run_fluid_gate_cycle(
        inventory=_inv(),
        gold_state=gold,
        s14_answers=_ans("trend_up", 0.70),
        s15_subclass="event_gap_shadow",
        log_dir=tmp_path,
        force=True,
    )
    pack = result.warroom_shadow.as_dict()
    assert pack["conf_gate_band_disposition"] == "EVENT"
    assert pack["news_protocol"] == "stamps_only_never_invent"
    assert pack["P0_CFD_SIZE_INTENT"]["choice"] == "HALF"
    with pytest.raises(InventedNewsProtocolVeto):
        run_fluid_gate_cycle(
            inventory=_inv(),
            gold_state=gold,
            invented_files=("NEWS_PROTOCOL",),
            log_dir=tmp_path,
            force=True,
        )


def test_judgment_package_has_zero_order_send() -> None:
    banned = ("order_send", "open_trade")
    count = 0
    for path in JUDGMENT_SRC.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                if name in banned:
                    count += 1
            if isinstance(node, ast.ImportFrom):
                mod = (node.module or "").lower()
                if "mt5" in mod or "book_owner" in mod or mod.endswith("execution"):
                    count += 1
    assert count == 0


def test_p0_module_never_sets_apply_env() -> None:
    src = (JUDGMENT_SRC / "p0_shadow_hooks.py").read_text(encoding="utf-8")
    assert "GTOS_JEV_FLUID_GATES_APPLY=1" not in src
    assert "os.environ[" not in src
    prove = (REPO / "scripts" / "run_p0_shadow_hooks_historical_prove.py").read_text(
        encoding="utf-8"
    )
    assert "GTOS_JEV_FLUID_GATES_APPLY" not in prove or "never set" in prove.lower()
    assert "GTOS_DIG_MULTI_STAGE_GUARD_APPLY=1" not in prove


def test_apply_env_refused_on_chair_path() -> None:
    from src.judgment.p0_hist_prove import apply_env_refused

    ok = apply_env_refused(environ={SHADOW_ENV: "1"})
    assert ok["refused"] is False
    assert ok["shadow_env_set"] is True
    assert ok["apply_env_set"] is False
    blocked = apply_env_refused(environ={SHADOW_ENV: "1", APPLY_ENV: "1"})
    assert blocked["refused"] is True
    assert blocked["refuse_reason"] == "apply_env_set"
    dig = apply_env_refused(environ={DIG_APPLY_ENV: "1"})
    assert dig["refused"] is True


def test_fire_1201_keep_wins_preserved_under_stacked_bands() -> None:
    from src.judgment.cf_d import question_bank_rows
    from src.judgment.p0_hist_prove import (
        FIRE_1201_KEEP_WIN_TICKETS,
        FIRE_1201_RESIDUAL_TICKETS,
        stacked_band_row,
        summarize_fire_1201,
    )

    inventory = _inv()
    rows = [r for r in question_bank_rows() if str(r.get("ticket")) in FIRE_1201_KEEP_WIN_TICKETS]
    assert {str(r["ticket"]) for r in rows} == set(FIRE_1201_KEEP_WIN_TICKETS)
    labeled = []
    for row in rows:
        result = run_fluid_gate_cycle(
            inventory=inventory,
            gold_state=row["gold_state"],
            s14_answers=row["system_one_answers"],
            s15_ticket=str(row["ticket"]),
            s15_subclass=row.get("subclass"),
            force=True,
            stake="sleeve_admit",
        )
        pack = result.warroom_shadow.as_dict()
        assert pack["apply"] is False
        labeled.append(
            stacked_band_row(ticket=str(row["ticket"]), tape_row=row, pack=pack)
        )
    summary = summarize_fire_1201(labeled)
    assert summary["wins_preserved"] is True
    assert summary["disposition_counts"]["keep_win"] == {"KEEP": 3}
    assert summary["research_candidate"]["status"] == "EMPTY"
    assert summary["research_candidate"]["hard_off_keep_research"] is False
    assert summary["apply"] is False
    assert set(FIRE_1201_RESIDUAL_TICKETS) == {"291087142", "293128383"}


def test_historical_prove_scorecard_offline(tmp_path: Path) -> None:
    from scripts.run_p0_shadow_hooks_historical_prove import main

    score = tmp_path / "score.json"
    receipt = tmp_path / "fire1201.json"
    rc = main(
        [
            "--force",
            "--log-dir",
            str(tmp_path / "logs"),
            "--score-out",
            str(score),
            "--receipt-out",
            str(receipt),
        ]
    )
    assert rc == 0
    card = json.loads(score.read_text(encoding="utf-8"))
    assert card["apply"] is False
    assert card["apply_true"] == 0
    assert card["n_order_send"] == 0
    assert card["invented_high"] == 0
    assert card["wins_preserved"] is True
    assert card["residual_shadow_parked"] is True
    assert card["research_candidate"]["status"] == "EMPTY"
    assert card["research_candidate"]["hard_off_keep_research"] is False
    assert card["n_stamped"] == 67
    assert card["n_rows"] == 67
    assert card["fire_1201"]["disposition_counts"]["keep_win"]["KEEP"] == 3
    assert card["fire_1201"]["disposition_counts"]["residual"]["REVIEW"] == 2
    assert card["pass"] is True
    fire = json.loads(receipt.read_text(encoding="utf-8"))
    assert fire["wins_preserved"] is True
    assert fire["residual_shadow_parked"] is True
    tickets = {row["ticket"]: row for row in fire["tickets"] if row["authority"]}
    assert tickets["291816474"]["conf_gate_band_disposition"] == "KEEP"
    assert tickets["293540988"]["size_intent"] == "KEEP_CAP"
    assert tickets["291794419"]["miss_choice"] != "STAND_DOWN"
    assert tickets["291087142"]["conf_gate_band_disposition"] == "REVIEW"
    assert tickets["293128383"]["miss_choice"] == "KEEP_EXEMPT"


def test_historical_prove_refuses_apply_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.run_p0_shadow_hooks_historical_prove import main

    monkeypatch.setenv(APPLY_ENV, "1")
    monkeypatch.setenv(SHADOW_ENV, "1")
    rc = main(["--log-dir", str(tmp_path / "logs")])
    assert rc == 2


def test_historical_prove_shadow_env_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.run_p0_shadow_hooks_historical_prove import main

    monkeypatch.delenv(APPLY_ENV, raising=False)
    monkeypatch.delenv(DIG_APPLY_ENV, raising=False)
    monkeypatch.setenv(SHADOW_ENV, "1")
    score = tmp_path / "score.json"
    rc = main(
        [
            "--log-dir",
            str(tmp_path / "logs"),
            "--score-out",
            str(score),
        ]
    )
    assert rc == 0
    card = json.loads(score.read_text(encoding="utf-8"))
    assert card["shadow_env_set"] is True
    assert card["force"] is False
    assert card["apply"] is False
    assert card["wins_preserved"] is True
    logs = list((tmp_path / "logs").rglob("*.json"))
    assert logs
    for path in logs:
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert_live_cages(doc)
        assert doc["broker_effect"] is False
        if "warroom_shadow" in doc:
            assert doc["warroom_shadow"]["apply"] is False


def test_chair_receipt_documents_shadow_only() -> None:
    receipt = (REPO / "judgment" / "CHAIR_P0_SHADOW_ENABLE_HIST_PROVE.md").read_text(
        encoding="utf-8"
    )
    assert "GTOS_JEV_FLUID_GATES_SHADOW=1" in receipt
    assert "never set" in receipt.lower() or "never flip" in receipt.lower()
    assert "GTOS_JEV_FLUID_GATES_APPLY" in receipt
    assert "0" in receipt
    assert "291816474" in receipt
    assert "291087142" in receipt
    assert "EMPTY" in receipt
    assert "order_send" in receipt
    assert "NEWS_PROTOCOL" in receipt
