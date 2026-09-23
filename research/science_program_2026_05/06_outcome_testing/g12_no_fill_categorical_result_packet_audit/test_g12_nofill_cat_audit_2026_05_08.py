from __future__ import annotations

import json
import os
import sys
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
if str(OUT_DIR) not in sys.path:
    sys.path.insert(0, str(OUT_DIR))

import verify_g12_nofill_cat_audit_2026_05_08 as verifier


DATE = "2026-05-08"


def load_json(name: str) -> dict:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def test_decision_accepts_only_categorical_lifecycle_evidence() -> None:
    decision = load_json(f"G12_NOFILL_CAT_DECISION_LEDGER_{DATE}.json")
    assert decision["decision"] == "ACCEPT_AS_CATEGORICAL_LIFECYCLE_ONLY_EVIDENCE_WITH_BLOCKED_FAMILIES"
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False
    assert decision["counts_summary"]["total_rows"] == 298
    assert decision["counts_summary"]["eligibility_decision_counts"]["ELIGIBLE_LABEL_ASSIGNED"] == 52
    assert decision["counts_summary"]["eligibility_decision_counts"]["BLOCKED_BEFORE_LABEL"] == 246
    assert decision["counts_summary"]["categorical_lifecycle_label_counts"] == {"nofill_terminal_before_entry": 52}


def test_source_hash_and_row_0127_recomputed() -> None:
    source = load_json(f"G12_NOFILL_CAT_SOURCE_HASH_AUDIT_{DATE}.json")
    assert source["status"] == "PASS"
    assert source["hash_record_count"] == 65
    assert source["missing_source_files"] == []
    assert source["hash_mismatches"] == []
    row0127 = source["row_0127_terminal_first_recompute"]
    assert row0127["status"] == "PASS"
    assert row0127["first_event"]["first_touch_utc"] == "2026-05-06T07:15:00.634000Z"
    assert row0127["source_sha256"] == "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"


def test_noleak_duplicate_and_blocker_reviews_are_exact() -> None:
    noleak = load_json(f"G12_NOFILL_CAT_NOLEAK_LABEL_AUDIT_{DATE}.json")
    duplicate = load_json(f"G12_NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.json")
    blocker = load_json(f"G12_NOFILL_CAT_BLOCKER_REVIEW_{DATE}.json")
    assert noleak["status"] == "PASS"
    assert noleak["forbidden_packet_field_hits"] == []
    assert noleak["six_t3_overlap"] == []
    assert noleak["blocked_cnr061_overlap"] == []
    assert duplicate["duplicate_conflict_blocked_rows"] == 42
    assert duplicate["duplicate_conflict_group_count"] == 3
    assert duplicate["sample_floor_status"] == "DISCOVERY_UNDER_SAMPLE_FLOOR_NO_VALIDATION_OR_PROMOTION"
    assert blocker["no_blocked_row_relabelable_under_current_contract"] is True
    assert blocker["otx_ambiguity_resolution"]["status"] == "DOES_NOT_RESCUE_CURRENT_BLOCKED_ROWS"


def test_verifier_passes_without_nested_pytest() -> None:
    os.environ["G12_NOFILL_CAT_SKIP_NESTED_PYTEST"] = "1"
    results = verifier.verify_audit(run_pytest=False, write_audit=False)
    assert results["verification_status"]["status"] == "PASS"

