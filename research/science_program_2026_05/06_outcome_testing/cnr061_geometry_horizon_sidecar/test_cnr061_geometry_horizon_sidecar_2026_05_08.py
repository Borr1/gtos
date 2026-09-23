import json

from build_cnr061_geometry_horizon_sidecar_2026_05_08 import OUTPUTS, PACKET_ID
from verify_cnr061_geometry_horizon_sidecar_2026_05_08 import verify


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_sidecar_packet_has_required_input_only_rows():
    packet = load_json(OUTPUTS["packet_json"])
    rows = load_jsonl(OUTPUTS["packet_jsonl"])

    assert packet["packet_id"] == PACKET_ID
    assert packet["record_count"] == 8
    assert len(rows) == 8
    assert {row["packet_id"] for row in rows} == {PACKET_ID}
    assert {row["target_model_family"] for row in rows} == {"CNR_T0_ORIGINAL_TP1"}
    assert {row["timing_model_family"] for row in rows} == {
        "CNR_E0_DECISION_CLOSE_MARKET",
        "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE",
    }
    for row in rows:
        assert row["entry_sl_tp_or_level_packet"]["entry_price"] is not None
        assert row["entry_sl_tp_or_level_packet"]["stop_loss"] is not None
        assert row["entry_sl_tp_or_level_packet"]["take_profit_1"] is not None
        assert row["executable_quote_packet"]["quote_source_status"] == "QUOTE_EXTRACTED_SOURCE_HASHED"
        assert row["ordered_path_packet"]["path_status"] == "ORDERED_TICK_PATH_AVAILABLE"
        assert row["validation_safe"] is False
        assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_join_map_and_blocker_counts_match_control_prompt_counts():
    join_map = load_json(OUTPUTS["join_map_json"])
    blockers = load_json(OUTPUTS["blockers_json"])

    counts = join_map["source_counts"]
    assert counts["g12_ready_pkt061_rows"] == 8
    assert counts["cnr_geometry_matrix_pkt061_rows"] == 8
    assert counts["otx_pkt061_proposal_rows"] == 51
    assert counts["otx_pkt061_rows_with_decision_quote"] == 50
    assert counts["otx_pkt061_rows_with_ordered_path"] == 50
    assert counts["otx_pkt061_rows_with_entry_sl_tp_or_level_packet"] == 0
    assert counts["otr061_recovered_rows"] == 1
    assert blockers["blocker_summary"]["blocked_e0e1_t0_rows"] == 94
    assert blockers["blocker_summary"]["otr061_recovered_rows_not_ready"] == 2


def test_verifier_passes():
    report = verify()
    assert report["status"] == "PASS", report["issues"]
