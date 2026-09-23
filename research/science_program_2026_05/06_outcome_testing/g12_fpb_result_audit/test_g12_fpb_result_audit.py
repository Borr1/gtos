from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


builder = _load_module("g12_fpb_audit_builder", ROUTE_DIR / "build_g12_fpb_result_audit.py")


def test_recursive_key_hits_rejects_result_keys() -> None:
    payload = {"safe": {"boundary": "not R or PnL"}, "bad": {"broker_actual_r": 0.5}}
    assert builder.recursive_key_hits(payload) == ["$.bad.broker_actual_r"]


def test_safe_flags_ok_requires_no_promotion_flags() -> None:
    payload = {"promotion_verdict": "NO_PROMOTION_VERDICT"}
    for flag in builder.SAFE_FALSE_FLAGS:
        payload[flag] = False
    ok, failures = builder.safe_flags_ok(payload)
    assert ok
    assert failures == []
    payload["opens_validation"] = True
    ok, failures = builder.safe_flags_ok(payload)
    assert not ok
    assert failures == ["opens_validation"]


def test_matrix_count_audit_checks_denominator_and_labels() -> None:
    matrix = {
        "raw_candidate_attempts": 13_540_033,
        "duplicate_candidate_keys": 687_275,
        "unique_nonduplicate_candidate_path_label_denominator": 12_852_758,
        "path_label_row_count": 12_852_758,
        "opened_families": builder.EXPECTED_FAMILIES,
        "opened_family_count": 11,
        "baseline_control_families": builder.EXPECTED_BASELINES,
        "global_label_distribution": {"counts": {"ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 12_852_758}},
        "family_rows": [
            {
                "family_id": "ob_retest",
                "denominator": 12_852_758,
                "ambiguity_unresolved_count": 0,
                "counts": {"ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 12_852_758},
            }
        ],
    }
    denominator = {
        "recomputed_raw_candidate_attempts": 13_540_033,
        "recomputed_duplicate_candidate_keys": 687_275,
        "recomputed_unique_nonduplicate_denominator": 12_852_758,
        "recomputed_path_label_count": 12_852_758,
    }
    progress_last = {
        "candidate_attempts_so_far": 13_540_033,
        "duplicate_candidate_keys_so_far": 687_275,
        "unique_candidate_denominator_so_far": 12_852_758,
        "path_label_rows_so_far": 12_852_758,
    }
    result = builder.matrix_count_audit(matrix, denominator, progress_last)
    assert result["passes"]
    assert result["family_denominator_sum_ok"]
    assert result["global_label_sum_ok"]
