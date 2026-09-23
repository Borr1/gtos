import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
BUILDER_PATH = HERE / "build_g12_haz001_density_waiting_time_audit_2026_05_15.py"
VERIFIER_PATH = HERE / "verify_g12_haz001_density_waiting_time_audit_2026_05_15.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_g12_recomputation_accepts_no_same_class_mismatch():
    recomputation = json.loads((HERE / "G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_RECOMPUTATION_LEDGER_2026-05-15.json").read_text(encoding="utf-8"))
    assert recomputation["input_recomputation"]["haz001_target_rows"] == 24112
    assert recomputation["input_recomputation"]["haz001_rowset_rows"] == 3014
    assert recomputation["pass_control_descriptor_recomputation"]["field_mismatch_count"] == 0
    assert recomputation["deconcentration_label_recomputation"]["label_mismatch_count"] == 0
    assert recomputation["fail_closed_sensitivity_recomputation"]["label_mismatch_count"] == 0


def test_g12_discrepancy_repair_closes_manifest_hash_issue():
    discrepancy = json.loads((HERE / "G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_DISCREPANCY_REPAIR_LEDGER_2026-05-15.json").read_text(encoding="utf-8"))
    assert discrepancy["same_g12_repairable_items_remaining"] == 0
    assert discrepancy["manifest_pre_repair_discrepancies_all"]
    assert any(item["status"] == "STALE_CONTENT_OR_MANIFEST_ENTRY" for item in discrepancy["manifest_pre_repair_discrepancies_all"])


def test_g12_retest_packet_remains_source_control_only():
    recomputation = json.loads((HERE / "G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_RECOMPUTATION_LEDGER_2026-05-15.json").read_text(encoding="utf-8"))
    assert recomputation["retest_packet_audit"]["rows"] == 3014
    assert recomputation["retest_packet_audit"]["forbidden_target_or_outcome_field_counts"] == {}
    assert recomputation["retest_packet_audit"]["safe_flag_bad_rows"] == 0


def test_g12_verifier_accepts_audit_artifacts():
    verifier = load_module(VERIFIER_PATH, "g12_haz001_verifier")
    assert verifier.main() == 0
    result = json.loads((HERE / "G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_VERIFICATION_RESULT_2026-05-15.json").read_text(encoding="utf-8"))
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
