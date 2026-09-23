import importlib.util
from pathlib import Path


BUILDER_PATH = (
    Path(__file__).resolve().parent
    / "build_otb2r_g6_local_ohlc_momentum_reversion_packets_2026_05_07.py"
)


def load_builder():
    spec = importlib.util.spec_from_file_location("otb2r_g6_builder", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_ob_bounds_parser_extracts_asof_bounds_without_outcome_fields():
    builder = load_builder()
    text = "H1 OB found at 2331.20-2344.80 near AI's POI at 2337.50"
    parsed = builder.parse_ob_bounds_from_text(
        text
    )
    assert parsed == {
        "status": "PARSED_FROM_DECISION_TIME_L2_VERIFICATION_DETAIL",
        "low": 2331.2,
        "high": 2344.8,
        "source": text,
    }


def test_build_all_remains_input_only_and_source_hash_verifiable():
    builder = load_builder()
    bundle = builder.build_all()

    assert bundle["completion"]["summary"]["can_mark_goal_complete"] is True
    assert bundle["manifest"]["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert bundle["manifest"]["validation_safe"] is False
    assert bundle["manifest"]["outcome_review_opened"] is False
    assert bundle["source_hash"]["failure_count"] == 0
    assert bundle["noleak"]["total_forbidden_record_key_hits"] == 0
    for source_key in builder.SKIPPED_SOURCE_POLICY_KEYS:
        source_info = bundle["manifest"]["source_input_hashes"][source_key]
        assert source_info["read_or_hashed"] is False
        assert source_info["sha256"] == "NOT_READ_OR_HASHED_SKIPPED_BY_POLICY"

    packet_ids = {packet["packet_id"] for packet in bundle["packets"]}
    assert packet_ids == {
        "OTG0-PKT-060",
        "OTG0-PKT-061",
        "OTG0-PKT-062",
        "OTG0-PKT-063",
        "OTG0-PKT-066",
    }
    assert sum(packet["record_count"] for packet in bundle["packets"]) > 0


def test_ob_vs_generic_uses_matched_control_not_independent_rows():
    builder = load_builder()
    bundle = builder.build_all()
    packet = next(packet for packet in bundle["packets"] if packet["packet_id"] == "OTG0-PKT-060")
    policy = bundle["matched"]["ob_vs_generic_policy"]

    assert policy["applies_to_packet_id"] == "OTG0-PKT-060"
    assert policy["independent_generic_control_rows_allowed"] is False
    assert packet["declared_future_label_family"] == "synthetic_path_r"
    assert all(record["label_family"] == "input_only_features_no_labels" for record in packet["records"])
    assert all("generic_retrace_comparator" in record for record in packet["records"])
