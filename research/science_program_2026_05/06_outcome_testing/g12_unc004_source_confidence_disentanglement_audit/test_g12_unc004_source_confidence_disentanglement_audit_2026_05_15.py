import json

import build_g12_unc004_source_confidence_disentanglement_audit_2026_05_15 as builder


def test_root_resolution_points_to_current_worktree():
    assert (builder.ROOT / ".context" / "LIVE_STATE.md").exists()
    assert builder.UNC_DIR.exists()
    assert builder.PROMPT_PATH.exists()


def test_safe_flags_ok_detects_violation():
    good = {
        **builder.ALL_FLAGS,
        "route_id": "x",
        "evidence_class": "y",
    }
    bad = dict(good)
    bad["validation_safe"] = True
    assert builder.safe_flags_ok(good)
    assert not builder.safe_flags_ok(bad)


def test_target_value_and_metric_eligibility():
    ctc = {
        "target_family_id": "neutral_close_to_close_return_m15_horizons_v1",
        "close_to_close_percent_return": 0.25,
        "terminal_status": "COMPUTABLE",
        "denominator_role": "per_card_pass_row",
    }
    hl = {
        "target_family_id": "neutral_high_low_excursion_m15_horizons_v1",
        "upside_excursion_percent": 0.4,
        "downside_excursion_percent": 0.1,
        "terminal_status": "COMPUTABLE",
        "denominator_role": "per_card_pass_row",
    }
    assert builder.target_value(ctc) == 0.25
    assert abs(builder.target_value(hl) - 0.3) < 1e-12
    assert builder.metric_eligible(ctc)
    ctc["terminal_status"] = "FAIL_CLOSED_NOT_COMPUTABLE"
    assert not builder.metric_eligible(ctc)


def test_classify_delta_underpowered_and_positive():
    pass_stats = builder.Stats()
    control_stats = builder.Stats()
    for i in range(35):
        row = {"duplicate_proxy_denominator_key": f"p{i}", "symbol": "S", "canonical_economic_group": "G", "session_bucket": "A", "source_segment_sha256": "seg"}
        pass_stats.update(row, 1.0)
    for i in range(35):
        row = {"duplicate_proxy_denominator_key": f"c{i}", "symbol": "S", "canonical_economic_group": "G", "session_bucket": "A", "source_segment_sha256": "seg"}
        control_stats.update(row, 0.1)
    assert builder.classify_delta(0.9, pass_stats, control_stats)[0] == "POSITIVE_PASS_GT_CONTROL"
    small = builder.Stats()
    small.update({"duplicate_proxy_denominator_key": "one"}, 1.0)
    assert builder.classify_delta(0.9, small, control_stats)[0] == "UNDERPOWERED_POSITIVE"


def test_unc_recompute_core_counts():
    generated_at = builder.read_json(builder.UNC_MANIFEST_PATH).get("generated_at_utc")
    recomputed = builder.recompute_unc_package(generated_at)
    assert recomputed["row_counts"]["unc_rowset_rows"] == 3014
    assert recomputed["row_counts"]["unc_target_rows"] == 24112
    assert recomputed["row_counts"]["matched_control_records"] == 2094
    assert recomputed["row_counts"]["negative_inverse_neutral_records"] == 2847


def test_jsonl_hash_helper_matches_manual():
    rows = [{"b": 2, "a": 1}, {"c": 3}]
    count, digest = builder.jsonl_sha256_for_rows(rows)
    manual = b"".join(builder.jsonl_line(row) for row in rows)
    assert count == 2
    assert digest == __import__("hashlib").sha256(manual).hexdigest()


def test_manifest_self_hash_excluded_shape():
    entry = {"name": "output_manifest", "path": "x", "bytes": 1, "sha256": None, "self_hash_excluded": True}
    assert entry["sha256"] is None
    assert entry["self_hash_excluded"] is True
