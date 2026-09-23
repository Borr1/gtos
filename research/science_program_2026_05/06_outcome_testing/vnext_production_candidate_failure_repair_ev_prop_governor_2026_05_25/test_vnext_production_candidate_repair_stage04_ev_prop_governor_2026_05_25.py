from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_candidate_repair_stage04_ev_prop_governor_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_candidate_repair_stage04", MODULE_PATH)
stage04 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = stage04
spec.loader.exec_module(stage04)


def _row(index: int, r: float, **overrides):
    row = {
        "candidate_id": f"cand_{index}",
        "as_of_utc": f"2026-01-{index:02d}T07:00:00+00:00",
        "symbol": "XAUUSD",
        "session": "london",
        "side": "LONG",
        "framework": "ob_retest",
        "source_mode": "OHLC_M1_CSV",
        "month": "2026-01",
        "simulated_r": r,
    }
    row.update(overrides)
    return row


def test_choose_action_uses_account_state_not_future_r_for_restart_decision():
    state = stage04.AttemptState(scenario="fixture", policy="ACCOUNT_ABANDON_OR_RESTART")
    state.equity = 90020.0
    state.day_start_equity = 100000.0

    positive = stage04.choose_action("ACCOUNT_ABANDON_OR_RESTART", _row(1, 1.5), state)
    negative = stage04.choose_action("ACCOUNT_ABANDON_OR_RESTART", _row(1, -1.0), state)

    assert positive["action"] == "ACCOUNT_ABANDON_OR_RESTART"
    assert negative["action"] == "ACCOUNT_ABANDON_OR_RESTART"
    assert positive["decision_inputs_no_future_r"] is True
    assert negative["decision_inputs_no_future_r"] is True


def test_high_quality_only_blocks_source_weak_rows_before_budget():
    state = stage04.AttemptState(scenario="fixture", policy="HIGH_QUALITY_ONLY")
    state.equity = 100000.0
    state.day_start_equity = 100000.0

    action = stage04.choose_action(
        "HIGH_QUALITY_ONLY",
        _row(1, 1.5, source_mode="MISSING_SOURCE"),
        state,
    )

    assert action["action"] == "BLOCK"
    assert action["reason"] == "high_quality_only_source_session_filter"


def test_policy_replay_segments_attempts_after_phase_pass(tmp_path):
    rows = [_row(i, 1.5) for i in range(1, 7)]
    decisions = tmp_path / "decisions.jsonl"
    attempts = tmp_path / "attempts.jsonl"

    with decisions.open("w", encoding="utf-8") as out_decision, attempts.open(
        "w", encoding="utf-8"
    ) as out_attempt:
        metrics = stage04.run_policy_replay(
            scenario="fixture",
            policy="ALLOW_FULL_RISK_SEGMENTED",
            rows=rows,
            out_decision=out_decision,
            out_attempt=out_attempt,
        )

    record = metrics.to_record()

    assert record["phase1_passes"] >= 1
    assert record["phase2_passes"] >= 1
    assert record["attempts_started"] >= 2
    assert record["allowed_trades"] == len(rows)
    assert "segmented_account_attempt" in attempts.read_text(encoding="utf-8")
