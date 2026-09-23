"""Behavioural guards for Session CN's outcome-blind live-cost A/B receipt."""

from __future__ import annotations

import csv
import gzip
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
DRIVER = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase17/receipts/cn_live_cost_truth.py"
)


def _module():
    spec = importlib.util.spec_from_file_location("cn_live_cost_truth", DRIVER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _broker_wall_epoch(year: int, month: int, day: int, hour: int = 0) -> int:
    """Encode a broker-naive wall-clock stamp the way the exported MT5 CSV does."""
    return int(datetime(year, month, day, hour, tzinfo=timezone.utc).timestamp())


def test_train_reader_stops_before_decoding_the_first_post_train_ohlc(tmp_path):
    cn = _module()
    path = tmp_path / "FTMO_SYN_H4.csv.gz"
    fields = ("time", "open", "high", "low", "close", "tick_volume")
    with gzip.open(path, "wt", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({
            "time": _broker_wall_epoch(2023, 1, 3, 12),
            "open": "1.0", "high": "1.1", "low": "0.9", "close": "1.0",
            "tick_volume": "10",
        })
        writer.writerow({
            "time": _broker_wall_epoch(2024, 12, 30, 12),
            "open": "2.0", "high": "2.1", "low": "1.9", "close": "2.0",
            "tick_volume": "11",
        })
        # If the upper-bound guard moves below OHLC decoding, this sentinel raises ValueError.
        writer.writerow({
            "time": _broker_wall_epoch(2025, 1, 3, 12),
            "open": "POST_TRAIN_MUST_NOT_DECODE",
            "high": "POST_TRAIN_MUST_NOT_DECODE",
            "low": "POST_TRAIN_MUST_NOT_DECODE",
            "close": "POST_TRAIN_MUST_NOT_DECODE",
            "tick_volume": "POST_TRAIN_MUST_NOT_DECODE",
        })
    Path(str(path) + ".timebase.json").write_text(json.dumps({
        "timebase": "broker_server_wall_clock",
        "broker": "FTMO-Server3",
        "symbol": "SYN",
        "timeframe": "H4",
    }))

    rows, receipt = cn.load_train_prefix(path)

    assert len(rows) == 2
    assert rows[-1]["time"].year == 2024
    assert receipt["first_refused_post_train_utc"].startswith("2025-")
    assert receipt["decoded_outcome_fields"] == []


def test_redacted_account_oil_projection_flips_only_when_broker_true_commission_is_added():
    cn = _module()
    candidate = {
        "symbol": "USOIL_cash",
        "sleeve": "energy_agri",
        "direction": "LONG",
        "source_close": 80.0,
        "sl_distance": 0.8,
        "decision_bar_utc": "2024-06-03T14:00:00+00:00",
    }

    row, gap = cn.project_candidate(
        candidate,
        account="redacted_account",
        account_config=cn._profile_configs()["redacted_account"],
        truth=cn.load_broker_true_costs(),
    )

    assert gap is None
    assert row["old_status"] == "PASSED"
    assert row["new_status"] == "REFUSED"
    assert row["decision_flipped"] is True
    assert abs(row["commission_usd_per_lot_round_turn"] - 5.0) < 1e-12
    assert abs(row["commission_r"] - 0.0625) < 1e-12
    assert not any("missing_side_aware_swap" in reason for reason in row["new_refusal_reasons"])


def test_gap_aggregation_preserves_affected_candidate_count():
    cn = _module()
    gaps = [
        {"account": "redacted_account", "sleeve": "crypto", "symbol": "DASHUSD",
         "reason": "symbol_not_in_live_profile", "gap_unit": "candidate"},
        {"account": "redacted_account", "sleeve": "crypto", "symbol": "DASHUSD",
         "reason": "symbol_not_in_live_profile", "gap_unit": "candidate"},
    ]

    assert cn._aggregate_gaps(gaps) == [{
        **{key: value for key, value in gaps[0].items() if key != "gap_unit"},
        "affected_candidate_count": 2,
    }]
