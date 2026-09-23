"""Jev-everywhere — site inventory, sidecar fan-out, historical closes.

No broker, no TypeSafe network, no writes under shadow_logs/.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.judgment.challenge import CHALLENGE_HARD_OFF_FAMILIES, CHALLENGE_KEEP_FAMILIES, CHALLENGE_LOGIN
from src.judgment.cycle import REQUIRED_LOG_KEYS, run_fluid_gate_cycle
from src.judgment.cf_d import (
    ABLATION_ORDER,
    CF_D_KEEP_FAMILIES,
    compose_cf_d,
    load_question_bank,
    question_bank_rows,
)
from src.judgment.cf_priority import (
    RELIGION_INDEX_CRYPTO_XA_SIZE0,
    classify_sleeve_family,
    label_cf_priority,
    religion_index_crypto_xa_size0,
    sleeve_allow,
)
from src.judgment.everywhere import EVERYWHERE_QUESTION_IDS, compose_everywhere, surface_map
from src.judgment.everywhere_tape import everywhere_historical_close_rows, inject_everywhere_answers
from src.judgment.flags import EVERYWHERE_ENV, SHADOW_ENV, everywhere_shadow_enabled, shadow_enabled
from src.judgment.inventory import collect_live_inventory
from src.judgment.sites import pre_everywhere_gaps, safe_challenge_sites
from src.judgment.place_apply import place_authorized
from src.judgment.veto import InventedNewsProtocolVeto, JevPlacePathVeto

REPO = Path(__file__).resolve().parents[2]
JUDGMENT_SRC = REPO / "src" / "judgment"
HARD_OFF_LOCK = ("bleed", "orb_crypto", "idxrev", "xa_huge", "mx_us30")


def _inv():
    return collect_live_inventory(
        sleeves=("spring", "vss", "metals_core"),
        workers=("challenge:0",),
        handlers=("shadow_log",),
        include_w7_armed=False,
        include_launcher_workers=False,
    )


def test_pre_everywhere_gaps_named() -> None:
    gaps = {s.site_id for s in pre_everywhere_gaps()}
    assert "admit" in gaps
    assert "close_label" in gaps
    assert "corr_hold" in gaps
    assert "usage_router" in gaps
    assert "size_tilt" in gaps
    assert "event_stamp" in gaps
    assert "fanout_book" in gaps
    assert "sleeve_family" in gaps
    assert "size_x_conf" in gaps
    assert "cost_band" in gaps
    assert "cf_d" in gaps
    assert "place" not in gaps
    assert "order_send" not in gaps


def test_writer_house_locks_untouched() -> None:
    assert tuple(CHALLENGE_HARD_OFF_FAMILIES) == HARD_OFF_LOCK
    mapped = surface_map()
    assert mapped["new_hard_off"] is False
    assert mapped["hard_off_families_untouched"] == list(HARD_OFF_LOCK)


def test_everywhere_flag_extends_fluid_shadow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(SHADOW_ENV, raising=False)
    monkeypatch.delenv(EVERYWHERE_ENV, raising=False)
    assert shadow_enabled() is False
    assert everywhere_shadow_enabled() is False
    monkeypatch.setenv(EVERYWHERE_ENV, "1")
    assert shadow_enabled() is True
    assert everywhere_shadow_enabled() is True
    monkeypatch.delenv(EVERYWHERE_ENV, raising=False)
    monkeypatch.setenv(SHADOW_ENV, "1")
    assert everywhere_shadow_enabled() is True


def test_compose_closes_gaps_on_sidecar() -> None:
    answers = inject_everywhere_answers(
        {
            "subclass": "fs_half_still_losing",
            "ticket": "291072108",
            "gold_state": {
                "identity": {"sleeve": "metals_core", "symbol": "XAUUSD", "side": "long", "ticket": "291072108"},
                "news": {"spine_empty": True, "events": []},
                "completeness": {"state_sufficient_for_live": True, "missing_fields": []},
                "occupancy": {"corr_hold_named": False},
            },
        }
    )
    composed = compose_everywhere(
        inventory=_inv(),
        answers=answers,
        gold_state={
            "identity": {"sleeve": "metals_core", "symbol": "XAUUSD", "ticket": "291072108"},
            "news": {"spine_empty": True, "events": []},
            "completeness": {"state_sufficient_for_live": True},
        },
        close_state={"close": {"ticket": "291072108", "symbol": "XAUUSD", "side": "long"}},
        stake="sleeve_admit",
    )
    by_id = {row.site_id: row for row in composed.sites}
    assert by_id["admit"].label == "abstain"
    assert by_id["close_label"].label == "orig_stop"
    assert by_id["close_label"].decidable is True
    assert by_id["usage_router"].label == "cheap_label"
    assert by_id["event_stamp"].label == "abstain_empty_spine"
    assert by_id["cf_d"].label == "A_STAND_DOWN"
    assert composed.new_hard_off is False
    assert composed.broker_effect is False
    assert composed.never_place is True
    closed = set(composed.gaps_closed)
    assert "admit" in closed
    assert "close_label" in closed


def test_cycle_writes_everywhere_site_rows(tmp_path: Path) -> None:
    row = everywhere_historical_close_rows()[0]
    result = run_fluid_gate_cycle(
        inventory=_inv(),
        gold_state=row["gold_state"],
        s14_answers=row.get("system_one_answers"),
        close_state=row.get("close_state"),
        everywhere_answers=row.get("everywhere_answers"),
        s15_ticket=row.get("ticket"),
        s15_subclass=row.get("subclass"),
        log_dir=tmp_path,
        force=True,
        stake="sleeve_admit",
    )
    assert result.skipped is False
    assert result.everywhere is not None
    assert result.log_path is not None
    doc = json.loads(result.log_path.read_text(encoding="utf-8"))
    assert "everywhere" in REQUIRED_LOG_KEYS
    assert "everywhere" in doc
    assert doc["everywhere"]["same_admit_sidecar_not_parallel"] is True
    assert doc["everywhere"]["broker_effect"] is False
    site_ids = {s["site_id"] for s in doc["everywhere"]["sites"]}
    for needed in (
        "admit",
        "close_label",
        "corr_hold",
        "usage_router",
        "event_stamp",
        "sleeve_family",
        "size_x_conf",
        "cost_band",
        "cf_d",
    ):
        assert needed in site_ids
    for qid in ("admit", "exit_class", "usage_seat", "event_stamped"):
        assert qid in doc["fanout_book"]["questions"]
        assert qid in EVERYWHERE_QUESTION_IDS


def test_everywhere_env_writes_without_fluid_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(SHADOW_ENV, raising=False)
    monkeypatch.setenv(EVERYWHERE_ENV, "1")
    result = run_fluid_gate_cycle(
        inventory=_inv(),
        answers={"next_gate": {"choice": "HOLD", "confidence": 0.6, "probabilities": {"HOLD": 0.6}}},
        log_dir=tmp_path,
        stake="label_assist",
    )
    assert result.skipped is False
    assert result.log_path is not None
    assert result.log_path.is_file()


def test_hard_refuse_index_does_not_add_hard_off_family() -> None:
    answers = inject_everywhere_answers(
        {
            "subclass": "cost_avoided_by_reject",
            "ticket": "s15idx",
            "gold_state": {
                "identity": {"sleeve": "idxrev", "symbol": "UK100.cash", "side": "sell", "ticket": "s15idx"},
                "news": {"spine_empty": True, "events": []},
                "completeness": {"state_sufficient_for_live": True, "missing_fields": []},
                "occupancy": {},
            },
        }
    )
    composed = compose_everywhere(
        inventory=_inv(),
        answers=answers,
        gold_state={
            "identity": {"sleeve": "idxrev", "symbol": "UK100.cash"},
            "news": {"spine_empty": True, "events": []},
        },
        stake="sleeve_admit",
    )
    admit = next(s for s in composed.sites if s.site_id == "admit")
    assert admit.label == "hard_refuse"
    assert composed.new_hard_off is False
    assert tuple(CHALLENGE_HARD_OFF_FAMILIES) == HARD_OFF_LOCK


def test_corr_hold_omits_flatten() -> None:
    pack = inject_everywhere_answers(
        {
            "subclass": "session_cut_loss",
            "ticket": "291392252",
            "gold_state": {
                "identity": {"sleeve": "metals_core", "symbol": "XAUUSD", "ticket": "291392252"},
                "news": {"spine_empty": True, "events": []},
                "completeness": {"state_sufficient_for_live": True, "missing_fields": []},
                "occupancy": {"corr_hold_named": True},
            },
        }
    )
    assert "flatten" not in pack["action_scope"]["probabilities"]
    assert pack["action_scope"]["choice"] != "flatten"
    kwargs = dict(
        inventory=_inv(),
        everywhere_answers={"action_scope": {"choice": "flatten", "confidence": 1.0}},
        log_dir=Path("/tmp/jev-everywhere-veto"),
        force=True,
    )
    if place_authorized():
        result = run_fluid_gate_cycle(**kwargs)
        assert result.conf_gate.broker_effect is False
        assert result.everywhere is not None
        assert result.everywhere.broker_effect is False
    else:
        with pytest.raises(JevPlacePathVeto):
            run_fluid_gate_cycle(**kwargs)


def test_refuses_invented_news_protocol(tmp_path: Path) -> None:
    with pytest.raises(InventedNewsProtocolVeto):
        compose_everywhere(
            inventory=_inv(),
            answers={},
            invented_files=("NEWS_PROTOCOL",),
        )


def test_place_stake_never_applies(tmp_path: Path) -> None:
    result = run_fluid_gate_cycle(
        inventory=_inv(),
        answers={"next_gate": {"choice": "HOLD", "confidence": 0.99, "probabilities": {"HOLD": 0.99}}},
        everywhere_answers={"admit": {"choice": "admit", "confidence": 0.99, "probabilities": {"admit": 0.99}}},
        log_dir=tmp_path,
        force=True,
        apply_flag=True,
        stake="place",
    )
    assert result.apply.apply is False
    assert result.conf_gate.broker_effect is False
    assert result.everywhere is not None
    assert result.everywhere.broker_effect is False


def test_historical_close_tape_has_challenge_tickets() -> None:
    rows = everywhere_historical_close_rows()
    assert len(rows) >= 20
    assert all(r["login"] == CHALLENGE_LOGIN for r in rows)
    tickets = {r["ticket"] for r in rows}
    assert "291072108" in tickets
    assert "291087142" in tickets


def test_safe_sites_are_all_challenge_sidecar() -> None:
    ids = {s.site_id for s in safe_challenge_sites()}
    assert "s16_multi_stage" not in ids
    assert "place" not in ids


def test_historical_prove_script_green(tmp_path: Path) -> None:
    from scripts import run_jev_everywhere_historical_prove as prove

    rc = prove.main(
        [
            "--force",
            "--log-dir",
            str(tmp_path / "logs"),
            "--score-out",
            str(tmp_path / "scorecard.json"),
            "--write-map",
            str(tmp_path / "map.json"),
        ]
    )
    assert rc == 0
    card = json.loads((tmp_path / "scorecard.json").read_text(encoding="utf-8"))
    assert card["pass"] is True
    assert card["n_decidable"] >= 20
    assert card["n_moved"] >= 5
    assert card["n_order_send"] == 0
    assert card["new_hard_off"] is False
    assert card["same_admit_sidecar_not_parallel"] is True
    assert card["religion_index_crypto_xa_size0"] is False
    assert card["religion_index_crypto_xa_size0_revoked"] is True
    assert card["priority_sites_logged"] is True
    assert card["sleeve_allow_n"] >= 1
    assert card["regime_unknown_n"] >= 1
    assert "sleeve_family" in card["sites_logged"]
    assert "size_x_conf" in card["sites_logged"]
    assert "cost_band" in card["sites_logged"]
    assert "cf_d" in card["sites_logged"]
    assert card["chair_cf_d"]["bank"]["n"] == 10
    assert card["chair_cf_d"]["bank"]["match"] == 10
    assert card["chair_cf_d"]["bank"]["stand_down"] == 2
    assert card["chair_cf_d"]["bank"]["keep_exempt_fs"] == 2
    assert card["cf_d_stand_down_n"] >= 1
    assert card["religion_index_crypto_xa_size0"] is False


def test_chair_cf_sleeve_family_allow_set() -> None:
    assert classify_sleeve_family("dsp_spring_close") == "spring"
    assert classify_sleeve_family("vss_fxcross_london_up_low") == "vss_fxcross"
    assert classify_sleeve_family("sub_mid_dn_re") == "sub_mid"
    assert classify_sleeve_family("sub_xvol_pullback") == "sub"
    assert classify_sleeve_family("dsp_expand_range") == "dsp_expand"
    assert classify_sleeve_family("dsp_wide_london") == "dsp_wide"
    assert classify_sleeve_family("idxrev") == "index_rev_bleed"
    assert classify_sleeve_family("orb_crypto_london") == "orb_crypto"
    assert classify_sleeve_family("metals_core") == "other"
    assert classify_sleeve_family("crypto") == "other"
    assert sleeve_allow("spring") is True
    assert sleeve_allow("vss_fxcross") is True
    assert sleeve_allow("sub_mid") is True
    assert sleeve_allow("sub") is True
    assert sleeve_allow("dsp_expand") is True
    assert sleeve_allow("dsp_wide") is False
    assert sleeve_allow("other") is False


def test_religion_index_crypto_xa_size0_revoked() -> None:
    assert RELIGION_INDEX_CRYPTO_XA_SIZE0 is False
    assert religion_index_crypto_xa_size0(sleeve="idxrev", symbol="UK100.cash") is False
    assert religion_index_crypto_xa_size0(sleeve="crypto", symbol="BTCUSD") is False
    assert religion_index_crypto_xa_size0(sleeve="metals_core", symbol="XAUUSD") is False
    for sleeve, symbol, subclass in (
        ("crypto", "BTCUSD", None),
        ("metals_core", "XAUUSD", "fs_half_still_losing"),
        ("idxrev", "UK100.cash", "cost_avoided_by_reject"),
        ("orb_crypto_london", "ETHUSD", "cost_avoided_by_reject"),
        ("xa_huge_20_extreme", "EURUSD", None),
    ):
        labels = label_cf_priority(sleeve=sleeve, subclass=subclass)
        assert labels.religion_index_crypto_xa_size0 is False
        assert labels.size_cf != "SIZE_NONE"
        assert "0" not in labels.size_cf


def test_regime_unknown_honest_until_features() -> None:
    gold = {
        "identity": {"sleeve": "dsp_spring_close", "symbol": "XAUUSD"},
        "sessions": {"named": "off_hours", "source": "unassembled"},
        "levels": {"source": "unassembled"},
    }
    labels = label_cf_priority(gold_state=gold, sleeve="dsp_spring_close")
    assert labels.regime_honest == "regime_unknown"
    composed = compose_everywhere(inventory=_inv(), answers={}, gold_state=gold)
    by_id = {row.site_id: row for row in composed.sites}
    assert by_id["s14_regime"].label == "regime_unknown"
    assert by_id["s14_regime"].reason == "regime_features_unassembled_honest"
    assert "regime_unknown_honest_until_features" in composed.notes
    assert "religion_index_crypto_xa_size0_revoked" in composed.notes


def test_cf_priority_sites_on_sidecar() -> None:
    gold = {
        "identity": {"sleeve": "dsp_expand_range", "symbol": "XAUUSD", "ticket": "cfexp01"},
        "news": {"spine_empty": True, "events": []},
        "sessions": {"named": "off_hours", "source": "unassembled"},
        "levels": {"source": "unassembled"},
        "completeness": {"state_sufficient_for_live": True},
    }
    composed = compose_everywhere(inventory=_inv(), answers={}, gold_state=gold)
    by_id = {row.site_id: row for row in composed.sites}
    assert by_id["sleeve_family"].label == "dsp_expand:SLEEVE_ALLOW"
    assert by_id["sleeve_family"].moved is True
    assert by_id["size_x_conf"].label == "SIZE_X_CONF_KEEP"
    assert by_id["cost_band"].label == "COST_WIN"
    assert by_id["cf_d"].label == "D_FULL"
    assert by_id["conf_gate"].answers.get("conf_gate_shadow") == "CONF_GATE_ALLOW"
    mapped = surface_map()
    assert mapped["chair_cf"]["religion_index_crypto_xa_size0"] == "revoked"
    assert mapped["chair_cf"]["priority"][0] == "cf_d"
    assert mapped["chair_cf"]["primary_soft_policy"]["id"] == "CF_D"


def test_writer_lock_hard_refuse_does_not_force_size0() -> None:
    answers = inject_everywhere_answers(
        {
            "subclass": "cost_avoided_by_reject",
            "ticket": "s15idx",
            "gold_state": {
                "identity": {"sleeve": "idxrev", "symbol": "UK100.cash", "side": "sell", "ticket": "s15idx"},
                "news": {"spine_empty": True, "events": []},
                "completeness": {"state_sufficient_for_live": True, "missing_fields": []},
                "occupancy": {},
            },
        }
    )
    assert answers["size_label"]["score"] != 0.1
    composed = compose_everywhere(
        inventory=_inv(),
        answers=answers,
        gold_state={"identity": {"sleeve": "idxrev", "symbol": "UK100.cash"}},
        stake="sleeve_admit",
    )
    by_id = {row.site_id: row for row in composed.sites}
    assert by_id["admit"].label == "hard_refuse"
    assert by_id["size_x_conf"].answers["religion_index_crypto_xa_size0"] is False
    assert by_id["size_tilt"].label != "none"
    assert by_id["cf_d"].label == "D_FULL"
    assert composed.new_hard_off is False


def test_cf_d_stand_down_fs_when_not_keep() -> None:
    dsp = compose_cf_d(sleeve="dsp_three_bar", miss="false_structure", keep_flag=False)
    assert dsp.choice == "A_STAND_DOWN"
    assert dsp.size_factor == 0.0
    assert dsp.decided_by == "miss"
    xa = compose_cf_d(sleeve="xa_huge_same_way", miss="false_structure", keep_flag=False)
    assert xa.choice == "A_STAND_DOWN"
    assert xa.religion_index_crypto_xa_size0 is False


def test_cf_d_keep_exempt_even_on_false_structure() -> None:
    vss = compose_cf_d(sleeve="vss_fxcross_l", miss="false_structure", keep_flag=True)
    assert vss.choice == "E_KEEP_CAP"
    assert vss.size_factor == 1.0
    assert vss.keep is True
    assert vss.decided_by == "family"
    sub = compose_cf_d(sleeve="sub_mid_dn_re", miss="false_structure", keep_flag=None)
    assert sub.family == "sub_mid"
    assert sub.keep is True
    assert sub.choice == "E_KEEP_CAP"
    expand = compose_cf_d(sleeve="dsp_expand_range", miss="false_structure", keep_flag=None)
    assert expand.keep is False
    assert expand.choice == "A_STAND_DOWN"
    assert tuple(CHALLENGE_KEEP_FAMILIES) == ("spring", "vss")
    assert "dsp_expand" not in CF_D_KEEP_FAMILIES
    assert "sub_mid" in CF_D_KEEP_FAMILIES


def test_cf_d_ablation_order_and_remainders() -> None:
    assert ABLATION_ORDER == ("miss", "size", "family", "session", "conf")
    event = compose_cf_d(
        sleeve="dsp_two_bar_thrust_into_20high_continues",
        miss="event_gap",
        keep_flag=False,
        subclass="event_gap_shadow",
    )
    assert event.choice == "B_SIZE_HALF"
    assert event.decided_by == "conf"
    sess = compose_cf_d(
        sleeve="metals_core",
        subclass="session_cut_loss",
        keep_flag=False,
    )
    assert sess.miss == "session_cut"
    assert sess.choice == "C_SIZE_TRIM"
    assert sess.decided_by == "session"
    win = compose_cf_d(sleeve="dsp_spring_close", miss="ok_win", keep_flag=True, outcome="WIN")
    assert win.choice == "E_KEEP_CAP"
    assert win.score > 0.9


def test_cf_d_not_asset_zero_religion() -> None:
    for sleeve, symbol in (
        ("idxrev", "UK100.cash"),
        ("orb_crypto_london", "ETHUSD"),
        ("crypto", "BTCUSD"),
        ("xa_huge_same_way", "EURUSD"),
    ):
        labels = compose_cf_d(sleeve=sleeve, miss=None, keep_flag=False)
        assert labels.religion_index_crypto_xa_size0 is False
        assert labels.choice != "A_STAND_DOWN"
        assert labels.size_factor != 0.0


def test_cf_d_question_bank_n10_chair_choices() -> None:
    bank = load_question_bank()
    assert bank["n_questions"] == 10
    assert bank["place"] is False
    rows = question_bank_rows()
    assert len(rows) == 10
    expected = {
        "291758207": "A_STAND_DOWN",
        "291789105": "A_STAND_DOWN",
        "291087142": "E_KEEP_CAP",
        "291383082": "B_SIZE_HALF",
        "293611741": "B_SIZE_HALF",
        "293332188": "B_SIZE_HALF",
        "291794419": "E_KEEP_CAP",
        "291816474": "E_KEEP_CAP",
        "293540988": "E_KEEP_CAP",
        "293128383": "E_KEEP_CAP",
    }
    got = {}
    for row in rows:
        tape = row["bank_question"]["tape"]
        composed = compose_cf_d(
            gold_state=row["gold_state"],
            sleeve=tape["sleeve"],
            miss=tape["miss"],
            keep_flag=tape["keep"],
            session=tape["session"],
            outcome=tape["outcome"],
        )
        got[row["ticket"]] = composed.choice
        sidecar = compose_everywhere(
            inventory=_inv(),
            answers={},
            gold_state=row["gold_state"],
        )
        by_id = {s.site_id: s for s in sidecar.sites}
        assert by_id["cf_d"].label == composed.choice
        assert sidecar.broker_effect is False
    assert got == expected
    assert tuple(CHALLENGE_KEEP_FAMILIES) == ("spring", "vss")


def test_judgment_everywhere_has_no_order_send() -> None:
    for path in JUDGMENT_SRC.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                assert name not in {"order_send", "open_trade"}
            if isinstance(node, ast.ImportFrom):
                mod = (node.module or "").lower()
                assert "mt5" not in mod
                assert "book_owner" not in mod
