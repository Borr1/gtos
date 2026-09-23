from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from verify_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12 import verify


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN"
DATE_TAG = "2026-05-12"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_verifier_accepts_generated_route_package():
    result = verify()
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["card_count"] == 40
    assert result["domain_count"] == 8
    assert result["replay_packet_count"] == 8
    assert result["blocked_dependency_count"] == 32
    assert result["readiness_split"] == {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
        "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 8,
    }


def test_mapping_matrix_accounts_for_every_card_and_domain_once():
    mapping = load_json("SOURCE_FIELD_MAPPING_MATRIX")
    rows = mapping["rows"]
    assert len(rows) == 40
    assert len({row["card_id"] for row in rows}) == 40
    domain_counts = Counter(row["science_domain"] for row in rows)
    assert set(domain_counts.values()) == {5}
    assert mapping["accepted_readiness_split"] == {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
        "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 8,
    }
    assert sum(row["outside_current_gtos_ob_framing"] for row in rows) == 33


def test_preregisterable_packets_are_only_for_accepted_ready_now_cards():
    mapping = load_json("SOURCE_FIELD_MAPPING_MATRIX")
    replay = load_json("REPLAY_INPUT_PACKET_DESIGN_LEDGER")
    ready_cards = sorted(
        row["card_id"]
        for row in mapping["rows"]
        if row["accepted_readiness"] == "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY"
    )
    packet_cards = sorted(row["card_id"] for row in replay["rows"])
    assert packet_cards == ready_cards
    assert len(packet_cards) == 8
    for row in replay["rows"]:
        assert row["source_group"] == "baseline_control_fields"
        assert row["duplicate_denominator_key"] == "duplicate_proxy_denominator_key"
        assert "win_rate" in row["forbidden_fields"]
        assert "broker_account" in row["forbidden_fields"]


def test_blocked_and_expansion_ledgers_stay_separate():
    blocked = load_json("BLOCKED_CARD_DEPENDENCY_LEDGER")
    expansion = load_json("EXPANSION_CANDIDATE_LEDGER")
    assert blocked["blocked_card_count"] == 32
    assert len(blocked["rows"]) == 32
    assert expansion["accepted_40_card_denominator_unchanged"] is True
    assert len(expansion["rows"]) >= 5
    assert all(row["accepted_40_card_denominator_inclusion"] is False for row in expansion["rows"])


def test_safe_flags_preserve_no_promotion_and_no_result_opening():
    for path in ROUTE_DIR.glob(f"{PREFIX}_*_{DATE_TAG}.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or "promotion_verdict" not in payload:
            continue
        assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert payload["validation_safe"] is False
        assert payload["outcome_review_opened"] is False
        assert payload["live_effect"] is False
        assert payload.get("opens_result_scoring") is False
        assert payload.get("opens_validation") is False
        assert payload.get("opens_ai_api") is False
        assert payload.get("opens_broker_account_order_history_deal_position_evidence") is False

