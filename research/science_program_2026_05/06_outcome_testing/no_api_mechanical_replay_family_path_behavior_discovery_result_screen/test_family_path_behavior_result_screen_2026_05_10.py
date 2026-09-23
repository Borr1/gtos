from __future__ import annotations

import importlib.util
import json
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


builder = _load_module(
    "family_path_behavior_builder",
    ROUTE_DIR / "build_family_path_behavior_result_screen_2026_05_10.py",
)
verifier = _load_module(
    "family_path_behavior_verifier",
    ROUTE_DIR / "verify_family_path_behavior_result_screen_2026_05_10.py",
)


def _candidate(family_id: str, candidate_id: str = "CID-1", duplicate_key: str = "DUP-1") -> dict:
    return {
        "candidate_id": candidate_id,
        "duplicate_key": duplicate_key,
        "family_id": family_id,
        "source_family": "LOCAL_OHLCV_CSV",
        "symbol": "XAUUSD",
        "timeframe": "M15",
        "session_or_kill_zone": "London",
        "regime_phase": "bullish_context",
        "side": "LONG",
        "source_row_id": "SRC-TEST",
        "source_partition": "sealed_historical_candidate_unopened",
    }


def _path_label(candidate_id: str = "CID-1", status: str = "ONE_ATR_CONTINUATION_CONTEXT_TOUCH") -> dict:
    return {
        "candidate_id": candidate_id,
        "duplicate_key": f"PDUP-{candidate_id}-{status}",
        "family_id": "ob_retest",
        "symbol": "XAUUSD",
        "timeframe": "M15",
        "side": "LONG",
        "source_row_id": "SRC-TEST",
        "label_status": status,
        "label_family": "DISCOVERY_PATH_LABEL_ONLY",
    }


def test_aggregate_writer_deduplicates_and_joins_path_context() -> None:
    writer = builder.AggregateOnlyWriter()
    assert writer.write_candidate(_candidate("ob_retest")) == "aggregated"
    assert writer.write_candidate(_candidate("ob_retest", candidate_id="CID-DUP")) == "duplicate"
    assert writer.write_path_label(_path_label()) == "aggregated"

    assert writer.candidate_count == 2
    assert writer.duplicate_candidate_keys == 1
    assert writer.path_label_count == 1
    assert writer.candidate_by_family["ob_retest"] == 1
    assert writer.label_by_family_status[("ob_retest", "ONE_ATR_CONTINUATION_CONTEXT_TOUCH")] == 1
    assert writer.label_by_family_symbol_status[("ob_retest", "XAUUSD", "ONE_ATR_CONTINUATION_CONTEXT_TOUCH")] == 1
    assert not writer.pending_context


def test_full_matrix_contains_all_families_and_baseline_controls() -> None:
    writer = builder.AggregateOnlyWriter()
    for idx, family_id in enumerate(builder.OPENED_FAMILIES):
        cid = f"CID-{idx}"
        writer.write_candidate(_candidate(family_id, candidate_id=cid, duplicate_key=f"DUP-{idx}"))
        status = (
            "MIDPOINT_RETRACE_BEFORE_EXTENSION"
            if family_id == "opening_drive_no_fill_lifecycle"
            else "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH"
        )
        writer.write_path_label(_path_label(candidate_id=cid, status=status))

    progress = ROUTE_DIR / "synthetic_progress_not_written.jsonl"
    matrix = builder.full_matrix_artifact(writer, [], [], [], progress, "2026-05-10T00:00:00+00:00")
    assert matrix["opened_family_count"] == 11
    assert set(matrix["opened_families"]) == set(builder.OPENED_FAMILIES)
    assert set(matrix["baseline_control_families"]) == set(builder.BASELINE_CONTROLS)
    assert matrix["compact_sample_used_for_decisive_ranking"] is False
    assert len(matrix["route_priority_not_performance"]) == 11
    assert set(matrix["label_vocabulary"]) == set(builder.LABEL_VOCABULARY)


def test_verifier_forbidden_key_scan_rejects_broker_result_keys() -> None:
    payload = {"outer": {"broker_actual_r": 1.0}, "safe_boundary_text": "not R or PnL"}
    hits = verifier.forbidden_key_hits(payload)
    assert hits == ["$.outer.broker_actual_r"]


def main() -> int:
    tests = [
        test_aggregate_writer_deduplicates_and_joins_path_context,
        test_full_matrix_contains_all_families_and_baseline_controls,
        test_verifier_forbidden_key_scan_rejects_broker_result_keys,
    ]
    failures = []
    for test in tests:
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - focused test runner summary.
            failures.append({"test": test.__name__, "error": repr(exc)})
    result = {"ok": not failures, "tests_run": len(tests), "failures": failures}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
