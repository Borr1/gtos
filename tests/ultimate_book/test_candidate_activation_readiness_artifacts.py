import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_candidate_activation_readiness_2026_06_18")


def _load(name):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def test_candidate_activation_readiness_artifact_boundary():
    result = _load("CANDIDATE_ACTIVATION_READINESS_RESULT.json")
    verification = _load("CANDIDATE_ACTIVATION_READINESS_VERIFICATION_RESULT.json")

    assert result["ok"] is True
    assert result["activation_ready"] is True
    assert result["candidate_book_default_off"] is False
    assert result["runtime_effect_now"] == "candidate_book_active_in_config"
    assert result["decision"] == "CANDIDATE_BOOK_ACTIVE__PROFILE_SPEC_HISTORY_AND_LTF_READY"
    assert result["candidate_book_profile"] == "runtime_executable_native_exit_v2"
    assert result["candidate_symbol_count"] == 30
    assert verification["activation_blocker_count"] == len(result["activation_blockers"])
    assert verification["readiness_work_item_count"] == result["readiness_work_item_count"] == 0
    assert verification["activation_blocker_count"] == 0
    assert result["readiness_work_items"] == []
    assert result["ltf_stress_gaps"] == []
    assert result["profile_execution_disposition_counts"] == {
        "dual_broker_profile_spec_ready": 24,
        "ftmo_only_profile_spec_ready__redacted_account_symbol_or_spec_required_for_dual_broker": 6,
    }
    assert verification["orderflow_used"] is False
    assert verification["mt5_bridge_touched"] is False
    assert verification["mt5_bridge_successor_evidence_used"] is True
    assert verification["broker_or_order_mutation"] is False


def test_candidate_activation_readiness_preserves_repair_lanes():
    result = _load("CANDIDATE_ACTIVATION_READINESS_RESULT.json")

    assert "NATGAS_cash" not in result["symbol_readiness"]
    assert "NATGAS_cash" in result["w7_hard_dropped_symbols"]
    assert result["symbol_readiness"]["DASHUSD"]["native_eligible"] is True
    assert result["symbol_readiness"]["DASHUSD"]["active_profile_gaps"]["redacted_account"]
    assert result["symbol_readiness"]["DASHUSD"]["blocking_active_profile_gaps"] == {}
    assert result["symbol_readiness"]["DASHUSD"]["blocking_verified_broker_spec_missing_profiles"] == []
    assert result["symbol_readiness"]["DASHUSD"]["profile_missing_expected_skip_profiles"] == ["redacted_account"]
    assert result["symbol_readiness"]["DASHUSD"]["status"] == "ACTIVATION_READY"
    assert set(result["dual_broker_profile_spec_ready_symbols"]) >= {
        "AUDUSD",
        "EURGBP",
        "EURUSD",
        "GBPUSD",
        "NZDUSD",
        "USDCAD",
        "USDCHF",
    }
    assert result["symbol_readiness"]["AUDUSD"]["profile_execution_disposition"] == "dual_broker_profile_spec_ready"
    assert result["symbol_readiness"]["AUDUSD"]["active_profile_gaps"] == {}
    assert result["symbol_readiness"]["AUDUSD"]["active_verified_broker_spec_missing_profiles"] == []
    assert set(result["ftmo_only_profile_spec_ready_symbols"]) == {
        "DASHUSD",
        "LTCUSD",
        "XPDUSD",
        "XPTUSD",
        "XRPUSD",
        "XTZUSD",
    }
    for symbol in result["ftmo_only_profile_spec_ready_symbols"]:
        row = result["symbol_readiness"][symbol]
        assert row["native_eligible"] is True
        assert row["status"] == "ACTIVATION_READY"
        assert row["profile_missing_expected_skip_profiles"] == ["redacted_account"]
        assert row["blocking_active_profile_gaps"] == {}
        assert row["blocking_verified_broker_spec_missing_profiles"] == []
    non_native_items = {
        (item["symbol"], item["reason"])
        for item in result["readiness_work_items"]
        if item["reason"] == "not_in_broker_native_eligible_symbols"
    }
    assert ("DASHUSD", "not_in_broker_native_eligible_symbols") not in non_native_items
    assert result["not_native_eligible_symbols"] == []
    assert result["ltf_stress_gaps"] == []
