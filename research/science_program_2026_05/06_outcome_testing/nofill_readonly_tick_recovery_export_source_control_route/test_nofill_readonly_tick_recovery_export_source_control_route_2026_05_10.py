from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
BUILDER_PATH = ROUTE_DIR / "build_nofill_readonly_tick_recovery_export_source_control_route_2026_05_10.py"
VERIFIER_PATH = ROUTE_DIR / "verify_nofill_readonly_tick_recovery_export_source_control_route_2026_05_10.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


builder = _load_module(BUILDER_PATH, "nofill_readonly_tick_recovery_builder")


def _load_json(name: str):
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def test_group_and_candidate_counts_are_preserved():
    recovery = _load_json(f"{builder.PREFIX}_RECOVERY_LADDER_LEDGER_{builder.DATE}.json")
    assert recovery["tick_export_dependent_blocker_count"] == 31
    assert recovery["grouped_request_count"] == 22
    assert len(recovery["candidate_rows"]) == 31
    assert len(recovery["grouped_rows"]) == 22
    assert sum(1 for row in recovery["candidate_rows"] if row["source_sha256"]) == 28
    assert sum(1 for row in recovery["candidate_rows"] if row["contamination_or_embargo_blocked"]) == 12


def test_source_hash_manifest_records_recovered_tick_schema_and_hashes():
    manifest = _load_json(f"{builder.PREFIX}_SOURCE_HASH_MANIFEST_{builder.DATE}.json")
    assert manifest["recovered_source_file_count"] == 20
    for row in manifest["rows"]:
        assert row["source_sha256"]
        assert row["row_count"] > 0
        assert row["source_file_sha256_field_status"] == "recorded_in_source_hash_manifest"
        assert set(builder.REQUIRED_TICK_FIELDS).issubset({k for k, v in row["field_availability"].items() if v})
        assert all(item["inside_source_span"] for item in row["window_coverage"]["candidate_times_inside_source_span"])


def test_remaining_owner_export_requests_are_exact_xauusd_windows():
    owner = _load_json(f"{builder.PREFIX}_OWNER_ACTION_MANIFEST_{builder.DATE}.json")
    remaining = owner["market_data_export_requests"]
    assert owner["remaining_market_data_export_request_count"] == 2
    assert {(row["symbol"], row["source_date"]) for row in remaining} == {
        ("XAUUSD", "2026-04-15"),
        ("XAUUSD", "2026-04-16"),
    }
    assert all(row["read_only_extraction_attempt_status"] == "NO_TICKS_EXPORTED" for row in remaining)


def test_us30_cash_alias_is_explicitly_source_control_compatible():
    status = builder.symbol_compatibility(
        {"symbol": "US30_cash", "source_symbol": "US30_or_US30_cash_broker_alias"},
        {"broker_symbol": "US30"},
    )
    assert status["status"] == "compatible_broker_alias_for_market_data_only"


def test_noleak_and_staging_audits_preserve_boundaries():
    noleak = _load_json(f"{builder.PREFIX}_NOLEAK_AUDIT_{builder.DATE}.json")
    staging = _load_json(f"{builder.PREFIX}_LARGE_FILE_STAGING_POLICY_AUDIT_{builder.DATE}.json")
    assert noleak["audit_status"] == "PASS"
    assert noleak["account_order_history_deal_position_api_used_any"] is False
    assert staging["policy_status"] == "PASS"
    assert staging["raw_market_data_files_changed_or_untracked_visible_to_git"] == []
    assert staging["raw_market_data_files_gitignored"] is True
    assert staging["raw_market_data_files_not_tracked"] is True


def test_verifier_accepts_generated_route():
    verifier = _load_module(VERIFIER_PATH, "nofill_readonly_tick_recovery_verifier")
    result = verifier.verify()
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
