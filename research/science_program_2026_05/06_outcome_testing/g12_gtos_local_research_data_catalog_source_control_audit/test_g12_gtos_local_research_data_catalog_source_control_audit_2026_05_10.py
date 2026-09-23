from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
BUILDER_PATH = ROUTE_DIR / "build_g12_gtos_local_research_data_catalog_source_control_audit_2026_05_10.py"
VERIFIER_PATH = ROUTE_DIR / "verify_g12_gtos_local_research_data_catalog_source_control_audit_2026_05_10.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


builder = _load_module(BUILDER_PATH, "g12_catalog_audit_builder")


def _load_json(name: str):
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def test_runtime_recompute_matches_expected_counts():
    recompute = builder.runtime_target_recompute()
    assert recompute["catalog_row_count"] == builder.EXPECTED["catalog_rows"]
    assert recompute["small_hash_rows"] == builder.EXPECTED["small_hash_rows"]
    assert recompute["large_file_deferrals"] == builder.EXPECTED["large_file_deferrals"]
    assert recompute["small_hashes_recomputed"] == builder.EXPECTED["small_hash_rows"]
    assert recompute["small_hash_missing_count"] == 0
    assert recompute["small_hash_mismatch_count"] == 0


def test_persisted_snapshot_staleness_is_recorded_as_exact_followup():
    root_audit = _load_json(f"{builder.PREFIX}_ROOT_RESOLVER_CONFIG_SCHEMA_AUDIT_{builder.DATE}.json")
    hash_audit = _load_json(f"{builder.PREFIX}_HASH_LARGE_FILE_DEFERRAL_AUDIT_{builder.DATE}.json")
    repair = _load_json(f"{builder.PREFIX}_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_{builder.DATE}.json")
    assert root_audit["persisted_current_worktree_path_mismatch_count"] > 0
    assert root_audit["runtime_current_worktree_paths_match_active_repo"] is True
    assert hash_audit["persisted_hash_rows_currently_missing"] > 0
    assert repair["lazy_blockers_remaining"] == []
    assert repair["followup_count"] >= 2


def test_search_missing_and_acquisition_counts_are_reconciled():
    search = _load_json(f"{builder.PREFIX}_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_{builder.DATE}.json")
    acquisition = _load_json(f"{builder.PREFIX}_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_{builder.DATE}.json")
    assert search["query_count"] == builder.EXPECTED["search_queries"]
    assert search["positive_query_count"] == builder.EXPECTED["positive_search_rows"]
    assert search["negative_query_count"] == builder.EXPECTED["negative_search_rows"]
    assert search["recoverable_market_data_count"] == builder.EXPECTED["recoverable_market_data_windows"]
    assert search["non_generatable_source_state_count"] == builder.EXPECTED["non_generatable_source_state_gaps"]
    assert acquisition["request_count"] == builder.EXPECTED["acquisition_requests"]
    assert acquisition["non_manifest_execution_count"] == 0
    assert acquisition["nonzero_cost_cap_count"] == 0


def test_safe_flags_and_noleak_boundaries_remain_closed():
    noleak = _load_json(f"{builder.PREFIX}_FORBIDDEN_ROUTE_NOLEAK_AUDIT_{builder.DATE}.json")
    completion = _load_json(f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE}.json")
    assert noleak["audit_passed"] is True
    assert noleak["broker_actual_r_read"] is False
    assert noleak["credentials_touched"] is False
    assert noleak["validation_execution_opened"] is False
    assert noleak["result_cost_r_win_rate_expectancy_scoring_opened"] is False
    assert completion["promotion_verdict"] == builder.PROMOTION_VERDICT
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False


def test_verifier_accepts_generated_g12_route():
    verifier = _load_module(VERIFIER_PATH, "g12_catalog_audit_verifier")
    result = verifier.verify()
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
