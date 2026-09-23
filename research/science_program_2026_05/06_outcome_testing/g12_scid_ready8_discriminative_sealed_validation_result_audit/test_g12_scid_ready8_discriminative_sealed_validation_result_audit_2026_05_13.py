import json

import build_g12_scid_ready8_discriminative_sealed_validation_result_audit_2026_05_13 as builder


def test_root_resolution_points_to_repo():
    assert builder.ROOT.name == "ai-trading-agent"
    assert builder.INPUT_DIR.exists()
    assert builder.PROMPT_PATH.exists()


def test_safe_flag_violation_detection():
    good = {
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    bad = dict(good)
    bad["validation_safe"] = True
    assert builder.safe_flag_violations(good) == []
    assert builder.safe_flag_violations(bad) == ["validation_safe"]


def test_warning_and_delta_helpers():
    assert builder.warning_is_concentration("SESSION_CONCENTRATION_GT_50PCT")
    assert not builder.warning_is_concentration("UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30")
    assert builder.approx_equal(0.3 - 0.1, 0.2)
    assert not builder.approx_equal(0.3, 0.2)


def test_compare_count_records_discrepancy():
    discrepancies = []
    assert builder.compare_count("x", 2, 2, discrepancies)
    assert discrepancies == []
    assert not builder.compare_count("x", 1, 2, discrepancies)
    assert discrepancies == [{"metric": "x", "observed": 1, "expected": 2}]


def test_iter_jsonl_parses_all_rows(tmp_path):
    path = tmp_path / "sample.jsonl"
    path.write_text(json.dumps({"a": 1}) + "\n\n" + json.dumps({"b": 2}) + "\n", encoding="utf-8")
    rows = list(builder.iter_jsonl(path))
    assert rows == [(1, {"a": 1}), (3, {"b": 2})]


def test_synthesis_claim_audit_accepts_number_tokens():
    text = "Comparable pass-vs-control records above the duplicate floor: 1278. Descriptor one-vs-rest records: 9570."
    rows = builder.synthesis_claim_audit(text, {})
    by_claim = {row["claim"]: row for row in rows}
    assert by_claim["Comparable pass-vs-control records"]["accepted"]
    assert by_claim["Descriptor one-vs-rest records"]["accepted"]
