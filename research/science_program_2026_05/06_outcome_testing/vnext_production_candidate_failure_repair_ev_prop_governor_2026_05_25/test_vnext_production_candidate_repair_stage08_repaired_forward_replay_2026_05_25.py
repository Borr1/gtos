from __future__ import annotations

import importlib.util
from io import StringIO
import json
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_candidate_repair_stage08_repaired_forward_replay_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("stage08_repaired_replay", MODULE_PATH)
stage08 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = stage08
spec.loader.exec_module(stage08)


def _row(candidate_id: str, as_of: str, r_value: float, terminal: str) -> dict:
    return {
        "candidate_id": candidate_id,
        "as_of_utc": as_of,
        "symbol": "XAUUSD",
        "session": "london",
        "side": "LONG",
        "framework": "ob_retest",
        "source_mode": "OHLC_M1_CSV",
        "month": as_of[:7],
        "terminal_outcome": terminal,
        "simulated_r": r_value,
        "stage07_ai_policy_action": "CALL_AI_NARROWED_ROUTE",
        "stage07_ai_call_required_for_production": True,
        "stage06_ltf_action": "MONITOR_LTF_PATH",
    }


def test_stage08_policy_replay_writes_segmented_decision_rows_and_ai_counts():
    decisions = StringIO()
    attempts = StringIO()
    rows = [
        _row("cand-a", "2026-01-01T07:00:00+00:00", 1.5, "target_first"),
        _row("cand-b", "2026-01-01T07:15:00+00:00", -1.0, "stop_first"),
    ]

    record, extra = stage08.run_policy_replay_stage08(
        scenario="unit",
        policy="ALLOW_FULL_RISK_SEGMENTED",
        rows=rows,
        out_decision=decisions,
        out_attempt=attempts,
    )
    decision_rows = [json.loads(line) for line in decisions.getvalue().splitlines()]

    assert record["input_rows"] == 2
    assert record["allowed_trades"] == 2
    assert record["ai_calls_required_pre_prop"] == 2
    assert record["paid_api_or_vendor_calls_made"] == 0
    assert extra["accepted_target_first"] == 1
    assert extra["accepted_stop_first"] == 1
    assert decision_rows[0]["stage_id"] == "STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY"
    assert decision_rows[0]["decision_inputs_no_future_r"] is True


def test_stage08_best_policy_ranks_terminal_day_ev_first():
    records = {
        "A": {
            "policy": "A",
            "reference_ev_per_terminal_day_usd_fee599_payout8000": 1.0,
            "payout_sensitivity_grid": [{}, {}, {}, {}, {"expected_value_per_attempt_usd": 100.0}],
            "risk_adjusted_r": 5.0,
            "pass_rate": 0.5,
            "account_loss_rate": 0.1,
            "avg_time_to_pass_days": 2.0,
            "avg_time_to_terminal_days": 2.0,
        },
        "B": {
            "policy": "B",
            "reference_ev_per_terminal_day_usd_fee599_payout8000": 2.0,
            "payout_sensitivity_grid": [{}, {}, {}, {}, {"expected_value_per_attempt_usd": 50.0}],
            "risk_adjusted_r": 1.0,
            "pass_rate": 0.1,
            "account_loss_rate": 0.0,
            "avg_time_to_pass_days": 1.0,
            "avg_time_to_terminal_days": 1.0,
        },
    }

    best = stage08.best_policy(records)

    assert best["policy"] == "B"
    assert best["reference_ev_per_terminal_day_usd_fee599_payout8000"] == 2.0
