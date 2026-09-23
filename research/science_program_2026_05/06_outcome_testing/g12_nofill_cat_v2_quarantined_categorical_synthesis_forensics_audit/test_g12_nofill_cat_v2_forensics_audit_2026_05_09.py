from __future__ import annotations

import importlib.util
import json
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
DATE = "2026-05-09"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(name: str):
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def test_builder_recomputes_exact_partition_and_counts():
    builder = load_module("audit_builder", OUT_DIR / "build_g12_nofill_cat_v2_forensics_audit_2026_05_09.py")
    rows = builder.read_jsonl(builder.V2_DIR / "NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl")
    baseline = builder.recompute_baseline(rows)
    assert baseline["partition_counts"] == {"accepted": 225, "blocked": 8, "rejected": 65, "universe": 298}
    assert baseline["accepted_split"] == {"accepted_prior": 52, "accepted_source_corrected": 173}
    assert baseline["accepted_label_counts"] == builder.EXPECTED_ACCEPTED_LABELS
    assert baseline["accepted_source_lane_counts"] == builder.EXPECTED_ACCEPTED_SOURCE_LANES
    assert baseline["blocker_code_counts"] == builder.EXPECTED_BLOCKER_CODES
    assert baseline["reject_decision_counts"] == builder.EXPECTED_REJECT_DECISIONS


def test_generated_decision_and_slice_artifacts_preserve_boundaries():
    decision = load_json(f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_{DATE}.json")
    slices = load_json(f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_SLICE_RECHECK_{DATE}.json")
    assert decision["status"] == "PASS"
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False
    assert decision["route_decision"]["primary_next_route"] == "NOFILL_CAT_V2_G0_SYNTHESIS_CONTROL_ROUTE"
    assert slices["status"] == "PASS"
    assert slices["accepted_denominator"] == 225
    assert slices["duplicate_policy"]["accepted_unique_nofill_duplicate_keys"] == 182
    assert slices["duplicate_policy"]["rows_in_duplicate_key_collisions"] == 48


def test_label_and_blocker_reviews_are_non_claims():
    labels = load_json(f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_LABEL_LEARNING_REVIEW_{DATE}.json")
    blockers = load_json(f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_BLOCKER_REJECT_REVIEW_{DATE}.json")
    assert labels["status"] == "PASS"
    for item in labels["label_reviews"].values():
        assert item["row_count_check"]["status"] == "PASS"
        assert item["descriptive_only"] is True
        assert item["validation_safe_false"] is True
        assert not item["missing_required_nonclaims"]
    assert blockers["status"] == "PASS"
    assert blockers["checks"]["blocked_rows_have_no_labels"]["actual"] == []
    assert blockers["checks"]["rejected_rows_have_no_labels"]["actual"] == []
    assert blockers["checks"]["blocked_rejected_not_denominator"]["actual"] == []
    assert blockers["source_access_requirement"]["original_oti2_source_gap"]


def test_no_leak_future_review_keeps_result_route_closed():
    review = load_json(f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NO_LEAK_DUPLICATE_SOURCE_REVIEW_{DATE}.json")
    assert review["status"] == "PASS"
    assert review["forbidden_key_hits"] == []
    assert review["duplicate_policy"]["oti5_canonical_duplicate_rows_accepted"] == 3
    assert review["duplicate_policy"]["oti5_noncanonical_duplicate_rows_rejected"] == 39
    assert review["source_hash_posture"]["g12_v2_source_status"] == "PASS"
    assert review["future_route_boundary"]["future_result_lane"].startswith("closed until separate preregistration")


def test_verifier_passes_without_nested_pytest_or_rewrite():
    verifier = load_module("audit_verifier", OUT_DIR / "verify_g12_nofill_cat_v2_forensics_audit_2026_05_09.py")
    report = verifier.verify_audit(run_pytest=False, write_audit=False)
    assert report["verification_status"]["status"] == "PASS"
    assert report["can_mark_goal_complete"] is True
