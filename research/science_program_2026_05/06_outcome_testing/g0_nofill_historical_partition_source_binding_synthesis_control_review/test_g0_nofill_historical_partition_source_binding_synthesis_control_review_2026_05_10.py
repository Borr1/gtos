from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
PREFIX = "G0_NOFILL_HIST_SYNTHESIS"
VERIFIER_PATH = ROUTE_DIR / "verify_g0_nofill_historical_partition_source_binding_synthesis_control_review_2026_05_10.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _load_json(name: str):
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def test_manifest_declares_required_source_control_facts():
    manifest = _load_json(f"{PREFIX}_OUTPUT_MANIFEST_2026-05-10.json")
    assert manifest["terminal_decision"] == "ACCEPT_AS_G0_SOURCE_CONTROL_SYNTHESIS_FOR_NEXT_SEALED_SOURCE_EXPANSION"
    assert manifest["cat_v3_row_count"] == 298
    assert manifest["sealed_validation_current_committed_nofill_rows"] == 0
    assert manifest["field_count"] == 55
    assert manifest["future_requirement_count"] == 20
    assert manifest["exact_repair_source_blocker_count"] == 0
    assert manifest["validation_safe"] is False
    assert manifest["outcome_review_opened"] is False
    assert manifest["live_effect"] is False
    for relative_path in manifest["outputs"].values():
        assert (REPO_ROOT / relative_path).exists()


def test_route_ranking_stays_source_expansion_only():
    ranking = _load_json(f"{PREFIX}_NEXT_SOURCE_EXPANSION_ROUTE_RANKING_2026-05-10.json")
    assert ranking["recommended_next_route_id"] == "NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET"
    first_route = ranking["routes"][0]
    assert first_route["route_class"] == "source_expansion_builder"
    assert "score outcomes" in first_route["must_not_do"]
    assert "read broker actual-R/account history" in first_route["must_not_do"]


def test_55_field_checklist_matches_accepted_counts():
    checklist = _load_json(f"{PREFIX}_55_FIELD_EXPANSION_BINDING_CHECKLIST_2026-05-10.json")
    assert checklist["field_count"] == 55
    assert checklist["binding_class_counts"] == {
        "FORBIDDEN_REDACTED_STATUS_ONLY": 7,
        "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE": 20,
        "SCHEMA_ONLY_CONTROL": 11,
        "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED": 17,
    }
    assert checklist["design_terminal_status_counts"] == {
        "EXISTING_SOURCE_SAFE_CAPTURE_READY": 17,
        "FORBIDDEN_OR_REDACTED_SOURCE_ONLY": 7,
        "FUTURE_LOGGER_FIELD_REQUIRED": 20,
        "SCHEMA_ONLY_CONTROL_FIELD": 11,
    }


def test_validation_closed_gate_ledger_opens_nothing():
    gates = _load_json(f"{PREFIX}_VALIDATION_EXECUTION_CLOSED_GATE_LEDGER_2026-05-10.json")
    assert gates["validation_safe"] is False
    assert all(item["opened"] is False for item in gates["closed_gates"])
    assert "G12-accepted source-bound packet plus separate validation-execution prompt" in {
        item["future_reopen_condition"] for item in gates["closed_gates"]
    }


def test_verifier_accepts_generated_route():
    verifier = _load_module(VERIFIER_PATH, "g0_hist_synthesis_verifier")
    result = verifier.verify()
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["recommended_next_route_id"] == "NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET"
