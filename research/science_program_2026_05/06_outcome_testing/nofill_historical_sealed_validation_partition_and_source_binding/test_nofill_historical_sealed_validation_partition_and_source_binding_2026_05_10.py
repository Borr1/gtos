from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
BUILDER_PATH = ROUTE_DIR / "build_nofill_historical_sealed_validation_partition_and_source_binding_2026_05_10.py"
VERIFIER_PATH = ROUTE_DIR / "verify_nofill_historical_sealed_validation_partition_and_source_binding_2026_05_10.py"
PREFIX = "NOFILL_HISTORICAL_SEALED_VALIDATION"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_output_manifest_declares_required_artifacts():
    manifest = json.loads((ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_2026-05-10.json").read_text(encoding="utf-8"))
    assert manifest["cat_v3_row_count"] == 298
    assert manifest["field_count"] == 55
    assert manifest["sealed_validation_current_committed_nofill_rows"] == 0
    for relative_path in manifest["outputs"].values():
        assert (ROUTE_DIR.parents[3] / relative_path).exists()


def test_partition_ledger_blocks_all_cat_v3_rows_from_sealed_validation():
    rows = [
        json.loads(line)
        for line in (ROUTE_DIR / f"{PREFIX}_PARTITION_ROW_LEDGER_2026-05-10.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 298
    assert {row["v3_terminal_family"] for row in rows} == {
        "accepted",
        "reject",
        "source_control",
        "source_impossible",
    }
    assert all(row["sealed_validation_eligible"] is False for row in rows)
    assert sum(1 for row in rows if row["stress_robustness_eligible"]) == 298


def test_55_field_binding_matrix_is_complete_and_closed():
    matrix = json.loads((ROUTE_DIR / f"{PREFIX}_55_FIELD_SOURCE_BINDING_MATRIX_2026-05-10.json").read_text(encoding="utf-8"))
    assert matrix["field_count"] == 55
    assert matrix["all_55_fields_closed"] is True
    assert matrix["design_terminal_status_counts"] == {
        "EXISTING_SOURCE_SAFE_CAPTURE_READY": 17,
        "FORBIDDEN_OR_REDACTED_SOURCE_ONLY": 7,
        "FUTURE_LOGGER_FIELD_REQUIRED": 20,
        "SCHEMA_ONLY_CONTROL_FIELD": 11,
    }
    assert matrix["validation_safe"] is False
    assert matrix["outcome_review_opened"] is False
    assert matrix["live_effect"] is False


def test_verifier_accepts_generated_route():
    verifier = _load_module(VERIFIER_PATH, "nofill_hist_partition_verifier")
    result = verifier.verify()
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["field_blocker_count"] == 20
