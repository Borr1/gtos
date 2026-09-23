from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from scripts import synthesize_expanded_oos_research_program as synth


def _scratch_dir() -> Path:
    root = Path(".test_expanded_oos_final_synthesis_tmp")
    root.mkdir(exist_ok=True)
    path = root / uuid.uuid4().hex
    path.mkdir()
    return path


def _source_map() -> dict:
    return {
        "opened_outcome_slices": [],
        "reserved_holdout_slices": [{"slice_id": "RESERVED", "status": "reserved_not_opened"}],
        "sources": {
            "mt5_research_exports": {
                "manifest_count": 2,
                "by_symbol_timeframe": [
                    {"symbol": "NAS100", "timeframe": "M15"},
                    {"symbol": "XAUUSD", "timeframe": "M15"},
                ],
            },
            "mt5_live_symbol_specs": {
                "symbols": [{"symbol": "NDX100"}, {"symbol": "XAGUSD"}]
            },
            "mt5_tick_availability": {"file_count": 1},
            "sierra_scid": {
                "file_count": 4,
                "first_wave_relevant_count": 4,
                "missing_first_wave_scid_symbols": [],
                "symbols": [
                    {"symbol": "NQM26-CME", "warnings": []},
                    {"symbol": "MNQM26-CME", "warnings": []},
                    {"symbol": "SIM26-COMEX", "warnings": ["known_sparse_scid_first_wave_warning"]},
                    {"symbol": "SILM26-COMEX", "warnings": ["known_sparse_scid_first_wave_warning"]},
                ],
            },
            "sierra_depth": {
                "file_count": 62,
                "total_gb": 3.5,
                "missing_first_wave_depth_symbols": [],
                "symbols": [
                    {"symbol": "NQM26-CME"},
                    {"symbol": "MNQM26-CME"},
                    {"symbol": "SIM26-COMEX"},
                    {"symbol": "SILM26-COMEX"},
                ],
            },
            "external_validation_event_logs": {"event_log_count": 3},
            "databento_cached_orderflow": {"file_count": 7, "total_mb": 1.25},
        },
    }


def _registry() -> dict:
    return {
        "candidates": [
            {
                "candidate_id": "CAND-001-J46-J49-LIVE-BASELINE",
                "rule_name": "baseline",
                "status": "FROZEN_FOR_COMPARISON",
            },
            {
                "candidate_id": "CAND-002-V2-OB-BOUNDARY",
                "rule_name": "ob",
                "status": "FROZEN_DISCOVERY_CANDIDATE",
            },
            {
                "candidate_id": "CAND-005-NAS100-DEPTH-THINNESS",
                "rule_name": "depth",
                "status": "REGISTERED_DIAGNOSTIC_NOT_PROMOTABLE",
            },
        ],
        "excluded_routes": [{"route": "Component 3B", "status": "PARKED", "reason": "cost"}],
    }


def _portability() -> dict:
    return {
        "first_batch_recommendation": {
            "do_not_start_with": ["broad Sierra depth replay without parity extractor"]
        },
        "blocker_ledger": [
            {"tool_id": "SRC-SIERRA-SCID", "blocker": "converter missing", "trigger": "add converter"}
        ],
    }


def _p3() -> dict:
    return {
        "validation_status": "BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS",
        "inputs": {"event_log_path": "events.jsonl", "runner_summary_path": "summary.json"},
        "acceptance_gates": {"no_leak": {"metrics": {"lower_tf_start_violations": 0}}},
        "scope_counters": {
            "rows_after_cutoff": 264,
            "wanted_rows_after_cutoff": 110,
            "wanted_resolved_rows_after_cutoff": 0,
        },
    }


def _p5() -> dict:
    return {
        "inputs": {"mbo_json": "mbo.json", "mbp10_json": "mbp10.json"},
        "synthesis": {"status": "DIAGNOSTIC_ONLY_LABEL_LIMITED"},
        "feeds": {
            "MBO_TOP20": {
                "coverage": {"candidate_rows": 12, "context_rows": 47},
                "candidate_context": {
                    "event15_total_depth": {
                        "candidate_minus_context": -33.5,
                        "candidate_n": 12,
                        "context_n": 47,
                    }
                },
                "stability": {
                    "event15_total_depth": {"leave_one_date": {"sign_flip_count": 1}}
                },
                "label_coverage": {
                    "actual_r_n": 1,
                    "synthetic_label_n": 11,
                    "actual_label_status": "BLOCKED_ACTUAL_R_SPARSE_OR_ONE_SIDED",
                },
            }
        },
    }


def test_payload_keeps_no_promotion_and_all_p_items() -> None:
    payload = synth.build_payload(
        _source_map(), _registry(), _portability(), _p3(), _p5(), confluence={}, v3={}
    )

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert [row["item"] for row in payload["completion_ledger"]] == [
        "P0",
        "P1",
        "P2",
        "P3",
        "P4",
        "P5",
        "P6",
        "P7",
        "P8",
    ]
    true_oos = next(
        row for row in payload["evidence_class_table"] if row["evidence_class"] == "TRUE_TEMPORAL_OOS"
    )
    assert true_oos["status"] == "BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS"
    assert true_oos["numbers"]["wanted_resolved_rows_after_cutoff"] == 0


def test_instrument_expansion_marks_sparse_scid_warning() -> None:
    rows = synth.instrument_expansion_table(_source_map())
    silver = next(row for row in rows if row["family"] == "Silver / SI")

    assert silver["status"] == "SOURCE_READY_WITH_SPARSE_SCID_WARNING"
    assert "SIM26-COMEX" in silver["warnings"]


def test_p5_feed_metrics_preserve_depth_delta_and_label_block() -> None:
    rows = synth.p5_feed_metrics(_p5())

    assert rows[0]["event15_total_depth_candidate_minus_context"] == -33.5
    assert rows[0]["leave_one_date_sign_flip_count"] == 1
    assert rows[0]["actual_r_n"] == 1


def test_markdown_contains_core_ledgers() -> None:
    scratch = _scratch_dir()
    out = scratch / "synthesis.md"
    try:
        payload = synth.build_payload(
            _source_map(), _registry(), _portability(), _p3(), _p5(), confluence={}, v3={}
        )
        synth.write_markdown(out, payload)

        text = out.read_text(encoding="utf-8")
        assert "NO_PROMOTION_VERDICT" in text
        assert "Completion Ledger" in text
        assert "BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS" in text
        assert "broad Sierra depth replay without parity extractor" in text
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
