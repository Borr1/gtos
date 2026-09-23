import json
from pathlib import Path


BASE = Path(__file__).resolve().parent
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def load(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def walk_keys(value, path="$"):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield f"{path}.{key}", key
            yield from walk_keys(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            yield from walk_keys(item, f"{path}[{idx}]")


def test_all_json_artifacts_parse_and_preserve_safety_flags():
    for path in BASE.glob("OTX_G6_*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["promotion_verdict"] == PROMOTION_VERDICT, path.name
        assert payload["validation_safe"] is False, path.name
        assert payload["outcome_review_opened"] is False, path.name


def test_source_hash_ledger_hashes_every_used_file_and_excludes_forbidden_sources():
    ledger = load("OTX_G6_SOURCE_HASH_LEDGER_2026-05-07.json")
    assert ledger["all_used_files_hashed"] is True
    forbidden = tuple(fragment.lower().replace("\\", "/") for fragment in ledger["forbidden_source_fragments"])
    assert ledger["source_files"]
    for row in ledger["source_files"]:
        assert row["sha256"]
        full_path = f"{row.get('path', '')} {row.get('absolute_path', '')}".lower().replace("\\", "/")
        assert not any(fragment in full_path for fragment in forbidden), row


def test_rebuilt_packet_proposals_are_input_only_without_result_keys():
    proposals = load("OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json")
    forbidden_keys = {
        "broker_actual_r",
        "actual_r",
        "win_loss",
        "outcome_r",
        "synthetic_path_r",
        "path_label",
        "hit_tp",
        "hit_sl",
        "path_outcome_status",
        "final_r",
        "realized_r",
    }
    assert proposals["record_count"] == len(proposals["records"]) == 310
    for record in proposals["records"]:
        assert record["label_family"] == "input_only_features_no_labels"
        assert record["no_result_fields_assertion"] is True
        hits = [(path, key) for path, key in walk_keys(record) if str(key).lower() in forbidden_keys]
        assert hits == []


def test_internal_packet_audit_statuses_match_goal_resolution():
    audit = load("OTX_G6_INTERNAL_PACKET_AUDIT_2026-05-07.json")
    rows = {row["packet_id"]: row for row in audit["packet_audit_rows"]}
    assert rows["OTG0-PKT-060"]["internal_decision"] == "BLOCKED_WITH_EXACT_IMPOSSIBILITY_FROM_APPROVED_LOCAL_TICKS"
    assert rows["OTG0-PKT-061"]["internal_decision"] == "BLOCKED_WITH_EXACT_PARTIAL_TICK_COVERAGE_EVIDENCE"
    assert rows["OTG0-PKT-062"]["internal_decision"] == "CLEARED_AND_QUARANTINED_TESTED_DISCOVERY_ONLY_WITH_ROW_EXCLUSIONS"
    assert rows["OTG0-PKT-063"]["internal_decision"] == "CLEARED_FOR_EXTERNAL_G12_REAUDIT_WITH_EXACT_ROW_BLOCKERS"
    assert rows["OTG0-PKT-066"]["internal_decision"] == "CLEARED_FOR_EXTERNAL_G12_REAUDIT_WITH_EXACT_ROW_BLOCKERS"
    for row in rows.values():
        assert row["forbidden_packet_field_hits"] == []
        assert row["source_hash_missing_count"] == 0


def test_oti4b_quarantined_result_is_limited_to_packet_062_and_discovery_only():
    result = load("OTX_G6_OTI4B_QUARANTINED_RESULT_LEDGER_2026-05-07.json")
    assert result["packet_id"] == "OTG0-PKT-062"
    assert result["result_status"] == "RESULT_QUARANTINED_DISCOVERY_ONLY"
    assert result["record_count"] == 86
    assert result["countable_discovery_rows"] == 9
    assert result["resolved_synthetic_r_rows"] == 5
    for row in result["rows"]:
        assert row["packet_id"] == "OTG0-PKT-062"
        assert row["result_source"] == "external_tick_parquet_recomputed_no_hidden_path_labels"
        keys = {key for _, key in walk_keys(row)}
        assert "broker_actual_r" not in keys
        assert "win_loss" not in keys


def test_completion_audit_maps_every_target_packet_to_evidence():
    completion = load("OTX_G6_COMPLETION_AUDIT_2026-05-07.json")
    assert completion["can_mark_goal_complete"] is True
    checklist = {row["requirement"]: row for row in completion["prompt_to_artifact_checklist"]}
    for requirement in [
        "mandatory_gtos_preflight",
        "controlling_inputs_hashed",
        "tick_coverage_ledger",
        "rebuilt_packet_proposals",
        "internal_g12_style_packet_audit",
        "otg0_pkt_060_status",
        "otg0_pkt_061_status",
        "otg0_pkt_062_status",
        "otg0_pkt_063_status",
        "otg0_pkt_066_status",
        "methodology_dsr_pbo_effective_n",
        "safety_flags_preserved",
    ]:
        assert checklist[requirement]["status"] == "PASS"
