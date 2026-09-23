"""Complete-judge residual wires — Challenge 0 only.

No broker, no TypeSafe network, no NEWS_PROTOCOL invent.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.judgment.chair_enforce import (
    soft_g4_choice,
    soft_g6_choice,
    soft_g8_noul,
    stamp_chair_enforce,
)
from src.judgment.challenge import CHALLENGE_HARD_OFF_FAMILIES, CHALLENGE_LOGIN
from src.judgment.complete_judge import (
    ADMIT_RESIDUAL_CRITERIA,
    COMPLETE_JUDGE_QUESTION_IDS,
    admit_residual_choice,
    complete_state_view,
    compose_complete_judge,
)
from src.judgment.complete_judge_prove import hist_overlays, prove_complete_judge
from src.judgment.everywhere import compose_everywhere
from src.judgment.everywhere_tape import everywhere_historical_close_rows, inject_everywhere_answers
from src.judgment.fluid_gates import EXPECTED_ENVELOPE, EXPECTED_FLUID, assert_inventory_shape
from src.judgment.inventory import collect_live_inventory
from src.judgment.jev_client import DEFAULT_MAX_CALLS
from src.judgment.sites import COMPLETE_JUDGE_SITES, pre_everywhere_gaps

REPO = Path(__file__).resolve().parents[2]
GAPS_PATH = REPO / "judgment" / "astra" / "JEV_COMPLETE_JUDGE_GAPS.json"
HARD_OFF_LOCK = ("bleed", "orb_crypto", "idxrev", "xa_huge", "mx_us30")


def _inv():
    return collect_live_inventory(
        sleeves=("spring", "vss", "metals_core"),
        workers=(f"challenge:{CHALLENGE_LOGIN}",),
        handlers=("shadow_log",),
        include_w7_armed=False,
        include_launcher_workers=False,
    )


def test_default_max_calls_chair_raised() -> None:
    assert DEFAULT_MAX_CALLS == 500000


def test_inventory_still_48_fluid() -> None:
    shape = assert_inventory_shape()
    assert shape["n_fluid"] == EXPECTED_FLUID == 48
    assert shape["n_envelope"] == EXPECTED_ENVELOPE == 8


def test_gap_table_has_no_open_in_prove_without_hist() -> None:
    doc = json.loads(GAPS_PATH.read_text(encoding="utf-8"))
    assert doc["login"] == "0"
    assert doc["no_open_in_prove_without_hist_path"] is True
    assert doc["n_fluid_lock"] == 48
    assert doc["default_max_calls"] == 500000
    assert doc["news_protocol"] == "stamps_only_never_invent"
    verdicts = {row["id"]: row for row in doc["gaps"]}
    assert set(verdicts) == {
        "CJ-ADM-RESIDUAL",
        "CJ-CHAIR-G4",
        "CJ-CHAIR-G6",
        "CJ-CHAIR-G8",
        "FLUID-HLD-005",
        "FLUID-HLD-008",
        "FLUID-NWS-005",
        "CJ-APPLY-SIZE",
        "CJ-REMINT-FLATTEN-CONSUME",
    }
    for row in doc["gaps"]:
        assert row["in_prove"] is False
        assert row["verdict"] in {"APPLY_CANDIDATE", "KILL"}
        if row["verdict"] == "APPLY_CANDIDATE":
            assert row["hist_path"]
            assert row["apply_fire_rate"] is False
        if row["verdict"] == "KILL" and row["id"].startswith("FLUID-"):
            assert row["hist_path"]
        if row["id"] in {"CJ-APPLY-SIZE", "CJ-REMINT-FLATTEN-CONSUME"}:
            assert row["hist_path"] is None
            assert row["hist_path_not_required_because"]


def test_complete_judge_sites_not_pre_everywhere_gaps() -> None:
    gap_ids = {s.site_id for s in pre_everywhere_gaps()}
    for site in COMPLETE_JUDGE_SITES:
        assert site.site_id not in gap_ids
        assert site.jev_sits is True
        assert site.never_place is True
    assert set(COMPLETE_JUDGE_QUESTION_IDS) == {
        "admit_residual",
        "chair_soft_g4",
        "chair_soft_g6",
        "chair_soft_g8",
    }


def test_admit_residual_poles() -> None:
    hard = admit_residual_choice(
        {"identity": {"sleeve": "idxrev", "symbol": "UK100.cash"}, "completeness": {"state_sufficient_for_live": True}}
    )
    assert hard == ("envelope_hard_off", True)
    us30 = admit_residual_choice(
        {"identity": {"sleeve": "dsp_walked_hi", "symbol": "US30.cash"}, "completeness": {"state_sufficient_for_live": True}}
    )
    assert us30 == ("envelope_hard_off", True)
    insuff = admit_residual_choice(
        {
            "identity": {"sleeve": "metals_core", "symbol": "XAUUSD"},
            "completeness": {"state_sufficient_for_live": False},
        }
    )
    assert insuff == ("state_insufficient", True)
    refusal = admit_residual_choice(
        {
            "identity": {"sleeve": "metals_core", "symbol": "XAUUSD"},
            "completeness": {"state_sufficient_for_live": True},
            "occupancy": {"last_refusal_class": "cost"},
        }
    )
    assert refusal == ("last_refusal", True)
    floor = admit_residual_choice(
        {
            "identity": {"sleeve": "metals_core", "symbol": "XAUUSD"},
            "completeness": {"state_sufficient_for_live": True},
        },
        admit_choice="admit",
        admit_conf=0.40,
    )
    assert floor == ("conf_floor", True)
    injected = admit_residual_choice(
        {
            "identity": {"sleeve": "metals_core", "symbol": "XAUUSD"},
            "completeness": {"state_sufficient_for_live": True},
        },
        admit_choice="abstain",
        admit_conf=0.70,
    )
    assert injected == ("injected", True)
    unanswered = admit_residual_choice(
        {
            "identity": {"sleeve": "metals_core", "symbol": "XAUUSD"},
            "completeness": {"state_sufficient_for_live": True},
        }
    )
    assert unanswered == ("unanswered", True)
    assert set(ADMIT_RESIDUAL_CRITERIA) == {
        "envelope_hard_off",
        "state_insufficient",
        "last_refusal",
        "conf_floor",
        "injected",
        "unanswered",
    }


def test_chair_soft_labels_do_not_change_ceiling() -> None:
    assert soft_g4_choice(g4_applies=True, keep=False) == "APPLY_CUT_0_5"
    assert soft_g4_choice(g4_applies=True, keep=True) == "KEEP_EXEMPT"
    assert soft_g4_choice(g4_applies=False, keep=False) == "NOT_APPLICABLE"
    assert soft_g6_choice(session_named="london", keep=False) == "APPLY_CUT_0_75"
    assert soft_g6_choice(session_named="london", keep=True) == "KEEP_EXEMPT"
    assert soft_g6_choice(session_named="off_hours", keep=False) == "LEAVE_ALONE"
    assert soft_g6_choice(session_named="", keep=False) == "NOT_APPLICABLE"
    cut = stamp_chair_enforce(sleeve="metals_core", symbol="XAUUSD", session_named="london", g4_applies=True)
    keep = stamp_chair_enforce(sleeve="spring", symbol="XAUUSD", session_named="london", g4_applies=True)
    assert cut.size_ceiling == 0.5
    assert cut.g4_soft_label == "APPLY_CUT_0_5"
    assert cut.g6_soft_label == "APPLY_CUT_0_75"
    assert keep.size_ceiling == 1.0
    assert keep.g4_soft_label == "KEEP_EXEMPT"
    assert keep.g6_soft_label == "KEEP_EXEMPT"
    assert keep.g8_block_noul == 0.50
    placed = stamp_chair_enforce(
        sleeve="metals_core",
        symbol="XAUUSD",
        occupancy={"already_placed_today": True, "minutes_since_flat": 5},
    )
    assert placed.g8_block_reentry is True
    assert placed.g8_block_noul is not None and placed.g8_block_noul >= 0.60
    assert placed.size_ceiling == 1.0


def test_g8_noul_poles() -> None:
    assert soft_g8_noul({}) == 0.50
    assert soft_g8_noul({"already_placed_today": True}) >= 0.60
    assert soft_g8_noul({"new_named_fire": True, "minutes_since_flat": 30, "already_placed_today": False}) < 0.60
    assert soft_g8_noul({"already_placed_today": False, "minutes_since_flat": 120, "new_named_fire": False}) < 0.60


def test_sidecar_logs_complete_judge_sites() -> None:
    answers = inject_everywhere_answers(
        {
            "subclass": "fs_half_still_losing",
            "ticket": "291072108",
            "g4_applies": True,
            "gold_state": {
                "identity": {"sleeve": "metals_core", "symbol": "XAUUSD", "ticket": "291072108", "g4_applies": True},
                "news": {"spine_empty": True, "events": []},
                "completeness": {"state_sufficient_for_live": True, "missing_fields": []},
                "sessions": {"named": "off_hours"},
                "occupancy": {"already_placed_today": False, "minutes_since_flat": 120},
            },
        }
    )
    composed = compose_everywhere(
        inventory=_inv(),
        answers=answers,
        gold_state={
            "identity": {"sleeve": "metals_core", "symbol": "XAUUSD", "g4_applies": True},
            "news": {"spine_empty": True, "events": []},
            "completeness": {"state_sufficient_for_live": True},
            "sessions": {"named": "off_hours"},
            "occupancy": {"already_placed_today": False, "minutes_since_flat": 120},
        },
        stake="sleeve_admit",
    )
    by_id = {row.site_id: row for row in composed.sites}
    assert by_id["admit"].reason == "injected"
    assert by_id["admit_residual"].label == "injected"
    assert by_id["chair_soft_g4"].label == "APPLY_CUT_0_5"
    assert by_id["chair_soft_g6"].label == "LEAVE_ALONE"
    assert by_id["chair_soft_g8"].label == "allow"
    assert composed.broker_effect is False
    assert "complete_judge_shadow_labels_never_apply_fire_rate" in composed.notes


def test_hard_refuse_residual_is_envelope() -> None:
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
        gold_state={"identity": {"sleeve": "idxrev", "symbol": "UK100.cash"}},
        stake="sleeve_admit",
    )
    by_id = {row.site_id: row for row in composed.sites}
    assert by_id["admit"].label == "hard_refuse"
    assert by_id["admit"].reason == "envelope_hard_off"
    assert by_id["admit_residual"].label == "envelope_hard_off"
    assert composed.new_hard_off is False
    assert tuple(CHALLENGE_HARD_OFF_FAMILIES) == HARD_OFF_LOCK


def test_conf_floor_replaces_static_string() -> None:
    gold = {
        "identity": {"sleeve": "metals_core", "symbol": "XAUUSD"},
        "completeness": {"state_sufficient_for_live": True},
        "news": {"spine_empty": True, "events": []},
        "occupancy": {},
    }
    composed = compose_everywhere(
        inventory=_inv(),
        answers={"admit": {"choice": "admit", "confidence": 0.40, "probabilities": {"admit": 0.40}}},
        gold_state=gold,
    )
    by_id = {row.site_id: row for row in composed.sites}
    assert by_id["admit"].label == "abstain"
    assert by_id["admit"].reason == "conf_floor"
    assert by_id["admit_residual"].label == "conf_floor"


def test_hist_overlays_are_existing_tickets() -> None:
    base = everywhere_historical_close_rows()
    tickets = {str(r["ticket"]) for r in base}
    overlays = hist_overlays(base)
    assert overlays
    for row in overlays:
        assert str(row["ticket"]) in tickets
        assert row["login"] == CHALLENGE_LOGIN
        assert "NEWS_PROTOCOL" not in json.dumps(row)


def test_historical_prove_green() -> None:
    card = prove_complete_judge()
    assert card["pass"] is True
    assert card["n_decidable"] >= 20
    assert card["n_fluid"] == 48
    assert card["fire_rate_apply"] is False
    assert card["size_ceiling_apply"] is False
    assert card["never_place"] is True
    assert card["g8_high"] >= 1
    assert card["g8_low"] >= 1
    assert len(card["residual_poles"]) >= 2
    assert "injected" in card["residual_poles"]
    assert "envelope_hard_off" in card["residual_poles"]
    assert len(card["g4_poles"]) >= 2
    assert len(card["g6_poles"]) >= 2


def test_prove_script_green(tmp_path: Path) -> None:
    from scripts import run_complete_judge_historical_prove as prove

    out = tmp_path / "cj-prove.json"
    rc = prove.main(["--score-out", str(out)])
    assert rc == 0
    card = json.loads(out.read_text(encoding="utf-8"))
    assert card["pass"] is True
    assert card["login"] == CHALLENGE_LOGIN


def test_complete_judge_has_no_order_send() -> None:
    for name in ("complete_judge.py", "complete_judge_prove.py"):
        path = REPO / "src" / "judgment" / name
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                assert fn not in {"order_send", "open_trade"}
            if isinstance(node, ast.ImportFrom):
                mod = (node.module or "").lower()
                assert "mt5" not in mod
                assert "book_owner" not in mod


def test_view_never_invents_news() -> None:
    view = complete_state_view(
        {
            "identity": {"sleeve": "metals_core", "symbol": "XAUUSD"},
            "completeness": {"state_sufficient_for_live": True},
            "sessions": {"named": "ny"},
            "occupancy": {"already_placed_today": False, "minutes_since_flat": 120},
        },
        g4_applies=False,
    )
    assert view["news_protocol"] == "stamps_only_never_invent"
    assert view["fire_rate_apply"] is False
    sites = compose_complete_judge(
        {
            "identity": {"sleeve": "metals_core", "symbol": "XAUUSD"},
            "completeness": {"state_sufficient_for_live": True},
            "sessions": {"named": "ny"},
            "occupancy": {},
        }
    )
    assert {s.site_id for s in sites} == set(COMPLETE_JUDGE_QUESTION_IDS)
    assert all(s.broker_effect is False for s in sites)
