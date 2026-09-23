import importlib.util
from pathlib import Path


BUILDER_PATH = (
    Path(__file__).resolve().parent
    / "build_g12_g3_g6_packet_builder_audit_2026_05_07.py"
)


def load_builder():
    spec = importlib.util.spec_from_file_location("g12_g3_g6_audit_builder", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_audit_covers_every_g3_g6_packet_without_opening_outcomes():
    builder = load_builder()
    bundle = builder.build_bundle()
    decisions = bundle["decision_ledger"]["packet_decisions"]

    assert [row["packet_id"] for row in decisions] == builder.TARGET_PACKET_IDS
    assert bundle["decision_ledger"]["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert bundle["decision_ledger"]["validation_safe"] is False
    assert bundle["decision_ledger"]["outcome_review_opened"] is False
    assert bundle["decision_ledger"]["outcomes_run"] is False
    assert bundle["decision_ledger"]["r_result_values_inspected"] is False
    assert bundle["decision_ledger"]["broker_actual_r_inspected"] is False
    assert bundle["decision_ledger"]["blocked_packet_outcomes_inspected"] is False
    assert bundle["decision_ledger"]["paid_network_api_databento_mt5_calls"] is False
    assert bundle["decision_ledger"]["live_surface_changes"] is False


def test_audit_no_leak_and_hash_recompute_are_clean():
    builder = load_builder()
    bundle = builder.build_bundle()

    assert bundle["noleak_review"]["total_forbidden_record_key_hits"] == 0
    assert bundle["source_hash_review"]["failure_count"] == 0
    assert bundle["accepted_shortlist"]["accepted_packets"]
    assert bundle["blocked_rejected_ledger"]["blocked_or_rejected_packets"]


def test_packet_decisions_are_intentionally_quarantined_or_blocked():
    builder = load_builder()
    bundle = builder.build_bundle()
    by_packet = {row["packet_id"]: row["decision"] for row in bundle["decision_ledger"]["packet_decisions"]}

    assert by_packet["OTG0-PKT-031"] == "ACCEPT_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_ONLY"
    assert by_packet["OTG0-PKT-032"] == "ACCEPT_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_ONLY"
    assert by_packet["OTG0-PKT-036"] == "ACCEPT_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_ONLY"
    assert by_packet["OTG0-PKT-062"] == "ACCEPT_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_ONLY"
    assert by_packet["OTG0-PKT-060"] == "BLOCKED_WITH_NEXT_EXACT_QUESTION"
    assert by_packet["OTG0-PKT-061"] == "BLOCKED_WITH_NEXT_EXACT_QUESTION"
    assert by_packet["OTG0-PKT-063"] == "BLOCKED_WITH_NEXT_EXACT_QUESTION"
    assert by_packet["OTG0-PKT-066"] == "BLOCKED_WITH_NEXT_EXACT_QUESTION"
