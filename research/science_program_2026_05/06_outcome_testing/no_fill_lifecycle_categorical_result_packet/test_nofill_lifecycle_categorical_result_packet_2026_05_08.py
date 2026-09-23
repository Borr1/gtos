from __future__ import annotations

import json
import os
import sys
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
if str(OUT_DIR) not in sys.path:
    sys.path.insert(0, str(OUT_DIR))

import build_nofill_lifecycle_categorical_result_packet_2026_05_08 as builder
import verify_nofill_lifecycle_categorical_result_packet_2026_05_08 as verifier


DATE = "2026-05-08"


def load_json(name: str) -> dict:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_rows() -> list[dict]:
    return [json.loads(line) for line in (OUT_DIR / f"NOFILL_CAT_PACKET_ROWS_{DATE}.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def test_builder_covers_exact_298_source_closed_rows_and_flags() -> None:
    builder.build_artifacts()
    manifest = load_json(f"NOFILL_CAT_PACKET_MANIFEST_{DATE}.json")
    assert manifest["packet_id"] == builder.PACKET_ID
    assert manifest["source_universe"]["source_packet_rows"] == 298
    assert manifest["source_universe"]["source_closed_rows"] == 298
    assert manifest["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert manifest["validation_safe"] is False
    assert manifest["outcome_review_opened"] is False
    assert manifest["live_effect"] is False


def test_eligibility_precedes_labels_and_blocked_rows_have_no_label() -> None:
    builder.build_artifacts()
    rows = load_rows()
    assert len(rows) == 298
    assert all(row["eligibility_checked_before_label"] is True for row in rows)
    assert all(row["categorical_lifecycle_label"] for row in rows if row["eligibility_decision"] == "ELIGIBLE_LABEL_ASSIGNED")
    assert all(row["categorical_lifecycle_label"] is None for row in rows if row["eligibility_decision"] == "BLOCKED_BEFORE_LABEL")
    first_line = (OUT_DIR / f"NOFILL_CAT_PACKET_ROWS_{DATE}.jsonl").read_text(encoding="utf-8").splitlines()[0]
    assert first_line.index('"eligibility_decision"') < first_line.index('"categorical_lifecycle_label"')


def test_counts_duplicate_conflicts_and_row_0127_blocker_are_exact() -> None:
    builder.build_artifacts()
    manifest = load_json(f"NOFILL_CAT_PACKET_MANIFEST_{DATE}.json")
    duplicate = load_json(f"NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.json")
    counts = load_json(f"NOFILL_CAT_LIFECYCLE_CATEGORY_COUNTS_{DATE}.json")
    rows = load_rows()
    assert manifest["row_outcome"]["eligible_label_assigned_rows"] == 52
    assert manifest["row_outcome"]["blocked_before_label_rows"] == 246
    assert counts["row_level"]["categorical_label_counts"] == {"nofill_terminal_before_entry": 52}
    assert duplicate["duplicate_conflict_group_count"] == 3
    row0127 = [row for row in rows if row["source_close_packet_row_id"] == "NOFILL-CLOSE-ROW-0127"][0]
    assert row0127["eligibility_decision"] == "BLOCKED_BEFORE_LABEL"
    assert "BLOCK_RESULT_MISSING_SOURCE" in row0127["result_blocker_codes"]
    assert row0127["categorical_lifecycle_label"] is None


def test_hash_noleak_and_exclusion_audits_pass() -> None:
    builder.build_artifacts()
    source = load_json(f"NOFILL_CAT_SOURCE_HASH_AND_ASOF_AUDIT_{DATE}.json")
    noleak = load_json(f"NOFILL_CAT_NOLEAK_LABEL_FAMILY_AUDIT_{DATE}.json")
    assert source["status"] == "PASS"
    assert source["hash_mismatches"] == []
    assert source["missing_source_files"] == []
    assert source["row_0127_terminal_first_recompute"]["status"] == "PASS"
    assert source["row_0127_terminal_first_recompute"]["first_event"]["first_touch_utc"] == builder.ROW_0127_EXPECTED_FIRST_TOUCH
    assert noleak["status"] == "PASS"
    assert noleak["forbidden_packet_field_hits"] == []
    assert noleak["six_t3_overlap"] == []
    assert noleak["blocked_cnr061_overlap"] == []


def test_verifier_passes_without_nested_pytest() -> None:
    builder.build_artifacts()
    os.environ["NOFILL_CAT_SKIP_NESTED_PYTEST"] = "1"
    results = verifier.verify_packet(run_pytest=False, write_audit=True)
    assert results["verification_status"]["status"] == "PASS"
    audit = load_json(f"NOFILL_CAT_COMPLETION_AUDIT_{DATE}.json")
    assert audit["completion_status"] == "PASS_VERIFIED_CATEGORICAL_PACKET"
    assert audit["can_mark_goal_complete"] is True

