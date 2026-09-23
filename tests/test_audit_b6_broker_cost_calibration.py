import json
from pathlib import Path
from types import SimpleNamespace

from research.operations.final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20 import (
    audit_b6_broker_cost_calibration_v123 as audit,
)


def _write_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_b6_audit_classifies_honest_and_stale_refused_cost_rows(tmp_path):
    candidate_ledger = tmp_path / "candidates.jsonl"
    tick_dir = tmp_path / "ticks" / "EURUSD"
    tick_dir.mkdir(parents=True)
    tick_path = tick_dir / "hostile5d_ticks.jsonl"
    _write_jsonl(
        tick_path,
        [
            {
                "time": "2026-05-13T00:09:00+00:00",
                "bid": 100.0,
                "ask": 100.3,
            },
            {
                "time": "2026-05-13T00:19:00+00:00",
                "bid": 100.0,
                "ask": 100.01,
            },
        ],
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "mt5_research_tick_export_v1",
                "output_dir": str(tmp_path),
                "files": {
                    "EURUSD_hostile5d_TICK": {
                        "file_symbol": "EURUSD",
                        "path": str(tick_path),
                        "row_count": 2,
                        "source_truth_scope": "ordered_price_path_only_not_broker_order_lifecycle_truth",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    _write_jsonl(
        candidate_ledger,
        [
            {
                "candidate_id": "honest",
                "decision_time_utc": "2026-05-13T00:10:00+00:00",
                "symbol": "EURUSD",
                "session": "tokyo",
                "side": "LONG",
                "entry_price": 100.0,
                "stop_loss": 99.0,
                "pretrade_cost_packet_status": "REFUSED",
                "pretrade_cost_refusal_reasons": [
                    "spread_r_exceeds_selected_cell_limit:0.300000>0.100000",
                    "total_cost_r_exceeds_limit:0.320000>0.150000",
                ],
                "expected_cost_r": 0.32,
                "spread_r": 0.30,
                "expected_slippage_r": 0.02,
            },
            {
                "candidate_id": "stale",
                "decision_time_utc": "2026-05-13T00:20:00+00:00",
                "symbol": "EURUSD",
                "session": "tokyo",
                "side": "LONG",
                "entry_price": 100.0,
                "stop_loss": 99.0,
                "pretrade_cost_packet_status": "REFUSED",
                "pretrade_cost_refusal_reasons": [
                    "spread_r_exceeds_selected_cell_limit:0.500000>0.100000",
                    "total_cost_r_exceeds_limit:0.520000>0.150000",
                ],
                "expected_cost_r": 0.52,
                "spread_r": 0.50,
                "expected_slippage_r": 0.02,
            },
        ],
    )
    args = SimpleNamespace(
        prefix="TEST",
        candidate_ledger=str(candidate_ledger),
        tick_manifest=str(manifest_path),
        sample_per_cell=20,
        lookback_minutes=60.0,
        validate_tick_sha=False,
    )

    summary, rows = audit.build_audit(args)

    assert summary["sampled_rows"] == 4
    assert summary["classification_counts"]["honest_refusal_measured_tick_matches_original_cost"] == 2
    assert (
        summary["classification_counts"][
            "mapping_bug_or_stale_floor_original_refused_but_measured_tick_passes"
        ]
        == 2
    )
    assert summary["cell_classification_counts"]["mapping_bug_or_stale_floor"] == 2
    assert {row["tick_status"] for row in rows} == {"historical_tick_found"}
