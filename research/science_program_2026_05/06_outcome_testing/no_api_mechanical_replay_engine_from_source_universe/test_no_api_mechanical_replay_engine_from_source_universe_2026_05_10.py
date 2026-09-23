from __future__ import annotations

import csv
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
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
    "mechanical_replay_builder",
    ROUTE_DIR / "build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
)
verifier = _load_module(
    "mechanical_replay_verifier",
    ROUTE_DIR / "verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
)


def _write_synthetic_csv(path: Path) -> None:
    start = datetime(2026, 5, 4, 7, 0, tzinfo=timezone.utc)
    rows = []
    price = 100.0
    for i in range(96):
        ts = start + timedelta(minutes=15 * i)
        if i < 20:
            open_ = price
            close = price + (0.15 if i % 2 == 0 else -0.08)
        elif i == 20:
            open_, close = 100.0, 101.8
        elif i == 21:
            open_, close = 102.0, 103.4
        elif i == 22:
            open_, close = 105.2, 106.2
        elif i == 25:
            open_, close = 105.0, 103.0
        elif 40 <= i < 52:
            open_, close = 102.0 + (i % 2) * 0.02, 102.03 - (i % 2) * 0.02
        elif i == 52:
            open_, close = 102.05, 104.0
        else:
            open_ = price
            close = price + 0.35
        high = max(open_, close) + 0.35
        low = min(open_, close) - 0.35
        if i == 22:
            low = 104.7
            high = 106.6
        if i == 25:
            low = 102.8
            high = 105.3
        rows.append(
            {
                "time": ts.isoformat(),
                "open": round(open_, 5),
                "high": round(high, 5),
                "low": round(low, 5),
                "close": round(close, 5),
                "volume": 100 + i,
            }
        )
        price = close
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["time", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)


def _write_source_rows(path: Path, csv_path: Path) -> None:
    rows = [
        {
            "source_row_id": "TEST-SRC-001",
            "absolute_path": str(csv_path),
            "repo_relative_path": str(csv_path),
            "source_family": "LOCAL_OHLCV_CSV",
            "evidence_class": "LOCAL_MARKET_DATA_CONTEXT_ONLY",
            "partition_assignment": "sealed_historical_candidate_unopened",
            "symbol": "XAUUSD",
            "timeframe": "M15",
            "available_asof_fields": ["time", "open", "high", "low", "close", "volume"],
            "missing_source_state_fields": ["production_ai_prompt_hash"],
            "duplicate_key": "TEST-M15",
            "hash_status": "deferred_large_file_requires_dedicated_hash_manifest",
            "row_count_estimate": 96,
        },
        {
            "source_row_id": "TEST-SRC-002",
            "absolute_path": str(csv_path),
            "repo_relative_path": str(csv_path),
            "source_family": "LOCAL_OHLCV_CSV",
            "evidence_class": "LOCAL_MARKET_DATA_CONTEXT_ONLY",
            "partition_assignment": "sealed_historical_candidate_unopened",
            "symbol": "XAUUSD",
            "timeframe": "D1",
            "available_asof_fields": ["time", "open", "high", "low", "close", "volume"],
            "missing_source_state_fields": ["production_ai_prompt_hash"],
            "duplicate_key": "TEST-D1",
            "hash_status": "sha256_complete",
            "sha256": "not_used_for_d1_exclusion",
            "row_count_estimate": 96,
        },
    ]
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def test_family_registry_contains_required_minimum() -> None:
    family_ids = {row["family_id"] for row in builder.frozen_family_registry()}
    assert {
        "ob_retest",
        "fvg_fill",
        "breaker_re_entry",
        "opening_drive_no_fill_lifecycle",
        "session_kz_sweep",
        "liquidity_stop_run_context",
        "baseline_random_session_control",
        "baseline_shifted_entry_control",
        "baseline_momentum_continuation",
        "baseline_mean_reversion",
        "adjacent_range_compression_breakout",
    } <= family_ids


def test_build_route_emits_projection_only_inventory_and_verifies(tmp_path: Path) -> None:
    csv_path = tmp_path / "XAUUSD_M15.csv"
    source_rows = tmp_path / "source_rows.jsonl"
    output_dir = tmp_path / "route"
    _write_synthetic_csv(csv_path)
    _write_source_rows(source_rows, csv_path)

    manifest = builder.build_route(output_dir=output_dir, source_rows_path=source_rows)

    assert manifest["selected_source_count"] == 1
    assert manifest["candidate_inventory_row_count"] > 0
    assert manifest["path_label_row_count"] > 0
    assert manifest["completion_standard_satisfied"] is True

    candidate_summary = json.loads((output_dir / "NO_API_MECHANICAL_REPLAY_CANDIDATE_INVENTORY_2026-05-10.json").read_text())
    assert candidate_summary["result_scoring_fields_emitted"] is False
    assert candidate_summary["validation_labels_emitted"] is False
    assert candidate_summary["by_family"]

    candidate_rows_path = Path(candidate_summary["candidate_rows_path"])
    with candidate_rows_path.open(encoding="utf-8") as handle:
        first_row = json.loads(next(handle))
    assert first_row["projection_only"] is True
    assert first_row["no_ai_calls"] is True
    assert first_row["no_execution"] is True
    assert "broker_actual_r" not in first_row
    assert "win_rate" not in first_row

    verification = verifier.verify(output_dir)
    assert verification["ok"] is True, verification["failures"]
