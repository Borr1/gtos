import json
from pathlib import Path


BASE = Path(__file__).resolve().parent
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALID_TERMINAL_STATES = {
    "RECOVERY_PACKET_READY_FOR_G12_REAUDIT",
    "BLOCKED_PERMISSION_OR_ACCESS",
    "BLOCKED_SOURCE_NOT_FOUND_AFTER_SATURATION",
    "BLOCKED_VENDOR_RECOVERY_REQUIRED",
}


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


def test_generated_json_artifacts_parse_and_preserve_safety_flags():
    json_files = sorted(BASE.glob("OTR061_*.json"))
    assert json_files
    for path in json_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["promotion_verdict"] == PROMOTION_VERDICT, path.name
        assert payload["validation_safe"] is False, path.name
        assert payload["outcome_review_opened"] is False, path.name
        assert payload["live_effect"] is False, path.name
        assert payload["broker_actual_r_accessed"] is False, path.name
        assert payload["account_history_accessed"] is False, path.name
        assert payload["mt5_order_calls"] == 0, path.name


def test_decision_terminal_state_and_required_manifest_policy():
    decision = load("OTR061_XAU_TICK_RECOVERY_DECISION_LEDGER_2026-05-07.json")
    assert decision["terminal_state"] in VALID_TERMINAL_STATES
    if decision["terminal_state"] == "RECOVERY_PACKET_READY_FOR_G12_REAUDIT":
        proposal = load("OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json")
        assert proposal["schema"] == "continuation_no_retrace_decision_price_path_v1"
        assert proposal["record_count"] == 1
    else:
        manifest = load("OTR061_VENDOR_OR_ACCESS_MANIFEST_2026-05-07.json")
        assert manifest["paid_or_network_calls_made"] is False
        assert manifest["approval_required_before_any_paid_or_network_call"] is True
        assert manifest["pre_call_manifest"]["maximum_spend_without_owner_approval_usd"] == 0


def test_known_xau_tick_blocker_is_rechecked_from_absolute_path():
    search = load("OTR061_XAU_TICK_RECOVERY_SEARCH_LEDGER_2026-05-07.json")
    xau = search["exact_candidate_inspections"]["g12_abs_xau_2026_05_06_tick_parquet"]
    assert xau["exists"] is True
    assert xau["min_ts_utc"] == "2026-05-06T17:16:17.131000+00:00"
    assert xau["required_full_window_row_count"] == 0
    assert xau["decision_quote_window_row_count"] == 0
    assert xau["path_window_row_count"] == 0
    assert search["known_g12_blocker_rechecked"] is True


def test_source_hash_ledger_hashes_existing_used_files_and_excludes_forbidden_sources():
    ledger = load("OTR061_XAU_TICK_SOURCE_HASH_LEDGER_2026-05-07.json")
    assert ledger["all_used_files_hashed"] is True
    assert ledger["forbidden_source_path_hits"] == []
    assert ledger["source_files"]
    existing = [row for row in ledger["source_files"] if row["exists"]]
    assert existing
    for row in existing:
        assert row["sha256"], row
    source_ids = {row["source_id"] for row in ledger["source_files"]}
    assert "g12_abs_xau_2026_05_06_tick_parquet" in source_ids
    assert "sierra_same_market_xauusd_scid" in source_ids


def test_search_ledger_covers_all_approved_roots_and_mt5_is_read_only():
    search = load("OTR061_XAU_TICK_RECOVERY_SEARCH_LEDGER_2026-05-07.json")
    roots = set(search["approved_search_roots"])
    for expected in [
        "C:\\tmp\\gtos_otb\\OTR061TICK\\data",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs",
        "C:\\tmp",
        "C:\\SierraChart",
        "C:\\Users\\MSI\\Documents",
    ]:
        assert expected in roots
    mt5 = search["mt5_read_only_route"]
    assert mt5["attempted"] is True
    assert mt5["read_only_assertion"] is True
    assert mt5["account_info_called"] is False
    assert mt5["history_deals_get_called"] is False
    assert mt5["history_orders_get_called"] is False
    assert mt5["orders_get_called"] is False
    assert mt5["positions_get_called"] is False
    assert mt5["order_send_called"] is False
    assert mt5["symbol_select_called"] is False


def test_generated_packet_records_do_not_contain_result_label_keys():
    proposal_path = BASE / "OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json"
    if not proposal_path.exists():
        return
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    forbidden = {
        "broker_actual_r",
        "account_history",
        "actual_r",
        "win_loss",
        "outcome_r",
        "path_label",
        "path_outcome_status",
        "final_r",
        "realized_r",
        "hit_tp",
        "hit_sl",
        "synthetic_path_r",
    }
    hits = [(path, key) for path, key in walk_keys(proposal) if str(key).lower() in forbidden]
    assert hits == []


def test_completion_audit_maps_prompt_requirements_to_pass():
    completion = load("OTR061_COMPLETION_AUDIT_2026-05-07.json")
    assert completion["can_mark_goal_complete"] is True
    checklist = {row["requirement"]: row for row in completion["prompt_to_artifact_checklist"]}
    for requirement in [
        "mandatory_live_state_regenerated_and_read",
        "local_heavy_data_inventory_read",
        "controlling_inputs_read_and_hashed",
        "approved_local_roots_searched",
        "absolute_xau_tick_file_rechecked",
        "sierra_same_market_scid_checked",
        "mt5_read_only_route_attempted",
        "no_paid_or_databento_call",
        "terminal_decision_emitted",
        "no_promotion_flags_preserved",
        "forbidden_surfaces_closed",
    ]:
        assert checklist[requirement]["status"] == "PASS"
