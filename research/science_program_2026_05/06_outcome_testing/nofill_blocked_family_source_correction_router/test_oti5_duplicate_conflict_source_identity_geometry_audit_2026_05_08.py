import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATE = "2026-05-08"


def read_json(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def read_jsonl(name: str):
    return [json.loads(line) for line in (ROOT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_oti5_duplicate_conflict_audit_counts_and_flags_are_exact() -> None:
    audit = read_json(f"OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT_{DATE}.json")
    rows = read_jsonl(f"OTI5_DUPLICATE_CONFLICT_ROW_DECISION_LEDGER_{DATE}.jsonl")

    assert audit["row_count"] == 42
    assert audit["nofill_duplicate_key_count"] == 3
    assert len(rows) == 42
    assert audit["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert audit["validation_safe"] is False
    assert audit["outcome_review_opened"] is False
    assert audit["live_effect"] is False
    assert {row["promotion_verdict"] for row in rows} == {"NO_PROMOTION_VERDICT"}
    assert {row["validation_safe"] for row in rows} == {False}
    assert {row["outcome_review_opened"] for row in rows} == {False}
    assert {row["live_effect"] for row in rows} == {False}


def test_oti5_row_decisions_cover_every_required_classification() -> None:
    rows = read_jsonl(f"OTI5_DUPLICATE_CONFLICT_ROW_DECISION_LEDGER_{DATE}.jsonl")
    canonical = [row for row in rows if row["is_canonical_geometry_row"]]
    noncanonical = [row for row in rows if not row["is_canonical_geometry_row"]]

    assert len(canonical) == 3
    assert len(noncanonical) == 39
    for row in rows:
        assert row["true_duplicate_conflict_decision"] == "TRUE_DUPLICATE_CONFLICT_UNDER_CURRENT_CONTRACT"
        assert row["source_identity_collision_decision"] == "DISTINCT_SOURCE_IDENTITY_COLLIDES_UNDER_DENOMINATOR_KEY"
        assert row["repeated_projection_decision"] == "REPEATED_PROJECTION_FAMILY_MEMBER"
        assert row["denominator_collision_decision"] == "TRUE_DENOMINATOR_COLLISION_ON_NOFILL_DUPLICATE_KEY"
        assert row["source_correctable_decision"] == "SOURCE_CORRECTABLE_CONTRACT_REVISION_REQUIRED_BEFORE_LABEL"
        assert row["exactly_impossible_decision"] == "NOT_IMPOSSIBLE_SOURCE_CORRECTABLE_BY_CANONICAL_GEOMETRY_RULE"
        assert row["source_hash_path"]
        assert row["hash_records_match_expected"] is True
        assert row["categorical_label_assigned_in_this_audit"] is None


def test_oti5_group_rules_and_source_hashes_are_complete() -> None:
    audit = read_json(f"OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT_{DATE}.json")
    source_search = read_json(f"OTI5_DUPLICATE_CONFLICT_SOURCE_SEARCH_LEDGER_{DATE}.json")
    completion = read_json(f"OTI5_DUPLICATE_CONFLICT_COMPLETION_AUDIT_{DATE}.json")

    assert audit["canonical_geometry_selection_rule"]
    assert audit["duplicate_denominator_rule"]
    assert "source_hash_path" in completion["checklist"][2]["evidence"]
    assert len(audit["group_decisions"]) == 3
    for group in audit["group_decisions"]:
        assert group["decision"] == "SOURCE_CORRECTABLE_DENOMINATOR_COLLISION_WITH_REPEATED_PROJECTIONS_AND_GEOMETRY_MISMATCH"
        assert group["source_identity_collision_decision"] == "DISTINCT_SOURCE_IDENTITIES_COLLIDE_UNDER_NOFILL_DUPLICATE_KEY"
        assert group["geometry_signature_count"] == group["record_count"]

    assert source_search["source_hash_record_count"] > 0
    assert source_search["hash_mismatches"] == []
    assert source_search["missing_source_hash_paths"] == []
    assert completion["can_mark_goal_complete"] is True
