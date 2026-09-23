from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-10"
PREFIX = "GTOS_CAP_LIMIT_CLOSURE"
VERIFIER_PATH = ROUTE_DIR / "verify_gtos_research_capability_limitation_closure_control_route_2026_05_10.py"


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path):
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_decision_ledger_covers_all_seven_limitation_families():
    ledger = _load_json(ROUTE_DIR / f"{PREFIX}_LIMITATION_DECISION_LEDGER_{DATE}.json")
    assert ledger["limitation_family_count"] == 7
    assert set(ledger["limitation_families"]) == {
        "market_data_absence",
        "historical_source_state_absence",
        "contamination_embargo_rejects",
        "worktree_blindness",
        "evidence_class_gate_friction",
        "data_catalog_weakness",
        "parser_hash_drift",
    }
    assert all(row["forbidden_boundary_preserved"] is True for row in ledger["rows"])
    assert all(row["artifact_refs"] for row in ledger["rows"])


def test_catalog_prototype_rows_are_source_control_only_and_hash_governed():
    rows = _load_jsonl(ROUTE_DIR / f"{PREFIX}_LOCAL_RESEARCH_DATA_CATALOG_PROTOTYPE_{DATE}.jsonl")
    assert rows
    assert all(row["allowed_evidence_class"] == "SOURCE_CONTROL_ONLY" for row in rows)
    assert all(row["hash_status"] in {"sha256_complete", "deferred_large_file_requires_dedicated_hash_manifest"} for row in rows)
    assert any(row["hash_status"] == "sha256_complete" for row in rows)


def test_source_state_taxonomy_blocks_price_backfill_for_system_truth():
    taxonomy = _load_json(ROUTE_DIR / f"{PREFIX}_HISTORICAL_SOURCE_STATE_TRUTH_TAXONOMY_{DATE}.json")
    assert "pending_lifecycle_group_id" in taxonomy["non_generatable_historical_fields"]
    assert "broker_actual_r" in taxonomy["non_generatable_historical_fields"]
    assert taxonomy["price_movement_backfill_rule"].startswith("Price movement cannot backfill")
    classes = {row["class"] for row in taxonomy["source_state_truth_taxonomy"]}
    assert {"recoverable_market_data", "non_generatable_historical_gtos_state", "schema_projection_or_fixture"} <= classes


def test_contamination_router_excludes_rejects_from_denominators():
    router = _load_json(ROUTE_DIR / f"{PREFIX}_CONTAMINATION_EMBARGO_ROUTER_{DATE}.json")
    guard = router["denominator_guard"]
    assert guard["rejects_count_as"] == "source_control_rejects_only"
    assert guard["blocked_rows_count_as"] == "source_control_blockers_only"
    assert "G12_source_control_acceptance" in guard["sealed_validation_denominator_requires"]
    assert {route["route"] for route in router["rejected_row_routes"]} >= {
        "discovery_only",
        "forensics_only",
        "source_contract_fixture",
        "stress_control",
    }


def test_parser_hash_policy_separates_strict_code_from_generated_live_state():
    policy = _load_json(ROUTE_DIR / f"{PREFIX}_PARSER_HASH_DRIFT_CONTROL_POLICY_{DATE}.json")
    classes = {row["class"]: row for row in policy["mutable_context_classification"]}
    assert "STRICT_HASH_REQUIRED" in classes
    assert "GENERATED_CONTEXT_VOLATILE" in classes
    assert ".context/LIVE_STATE.md" in classes["GENERATED_CONTEXT_VOLATILE"]["examples"]
    assert "raw_sha256_required" in policy["raw_sha_versus_lf_normalized_text_sha_policy"]["parser_code"]


def test_verifier_accepts_generated_route():
    verifier = _load_module(VERIFIER_PATH, "gtos_cap_limit_verifier")
    result = verifier.verify()
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["limitation_family_count"] == 7
    assert result["catalog_row_count"] > 0
