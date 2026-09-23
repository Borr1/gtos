"""Tests for ``scripts.cusum_candidate_rate_monitor`` — T1.5 CUSUM on CR.

All tests use ``tmp_path`` and monkeypatch the module-level constants on the
``_mod`` object (NOT on symbols imported via ``from X import Y``). This
mirrors the canonical temporary-path isolation pattern used across tests
and ``tests/test_ob_continuation_monitor.py`` after session 21's
pytest-contamination post-mortem:

    from scripts import cusum_candidate_rate_monitor as _mod
    monkeypatch.setattr(_mod, "STATE_PATH", tmp_path / "state.json")

Writing under the real ``shadow_logs/`` or ``knowledge_base/`` would trigger
the ``ProductionWriteError`` guard installed by ``tests/conftest.py``. All
tests here are structured so no production path is ever touched.
"""
from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts import cusum_candidate_rate_monitor as _mod
from scripts.cusum_candidate_rate_monitor import (
    CUSUMState,
    _logL,
    compute_cusum,
    load_state,
    save_state,
    step_cusum,
)


# =============================================================================
# Helpers
# =============================================================================


def _ts(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> str:
    """ISO-8601 UTC timestamp with offset (matches orchestrator's format)."""
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc).isoformat()


def _write_log(path: Path, entries: list[tuple[str, str]]) -> None:
    """Write a synthetic candidate_features_log.jsonl. Each entry is (ts, decision)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for ts, decision in entries:
            fh.write(json.dumps({"timestamp_utc": ts, "decision": decision}) + "\n")


# =============================================================================
# Pure functions — _logL and step_cusum
# =============================================================================


class TestLogL:
    """Sanity-check the log-likelihood formula. p0=0.5 → symmetric, simple."""

    def test_logL_candidate_increases_when_p_alt_greater(self):
        # p_alt > p0 and we see CANDIDATE → positive (likelihood ratio > 1).
        assert _logL(p_alt=0.2, p0=0.1, observed_candidate=True) > 0

    def test_logL_candidate_decreases_when_p_alt_less(self):
        # p_alt < p0 and we see CANDIDATE → negative.
        assert _logL(p_alt=0.05, p0=0.1, observed_candidate=True) < 0

    def test_logL_no_trade_decreases_when_p_alt_greater(self):
        # p_alt > p0 and we see NO_TRADE → negative (NO_TRADE is less likely
        # under higher-p regime).
        assert _logL(p_alt=0.2, p0=0.1, observed_candidate=False) < 0

    def test_logL_no_trade_increases_when_p_alt_less(self):
        # p_alt < p0 and we see NO_TRADE → positive.
        assert _logL(p_alt=0.05, p0=0.1, observed_candidate=False) > 0

    def test_logL_exact_value(self):
        # Concrete check at the production parameters.
        assert _logL(0.206, 0.103, True) == pytest.approx(math.log(0.206 / 0.103))
        assert _logL(0.0515, 0.103, False) == pytest.approx(math.log(0.9485 / 0.897))


# =============================================================================
# Hand-worked 10-observation example — CANONICAL SMOKE TEST
# =============================================================================


class TestHandWorked10ObsExample:
    """A small, easily-verifiable sequence. Computed in the module docstring.

    Parameters: p0=0.103, p1_up=0.206, p1_down=0.0515 (defaults).

    Increments:
      candidate-observed under upper:   log(0.206/0.103)         = +0.693147
      no-trade-observed under upper:    log(0.794/0.897)         = -0.121970
      candidate-observed under lower:   log(0.0515/0.103)        = -0.693147
      no-trade-observed under lower:    log(0.9485/0.897)        = +0.055829

    Baseline sequence: 10 N's (no candidates). Upper stays at 0 (floored).
    Lower accumulates 10 * 0.055829 = 0.55829 — well below h=4.0, no alarm.
    """

    def test_ten_no_trades_lower_accumulator_exact(self):
        outcomes = [False] * 10
        final = compute_cusum(outcomes)
        assert final.n_obs == 10
        assert final.n_candidates == 0
        # 10 * _LOGL_DOWN_N
        expected_s_down = 10 * _logL(0.0515, 0.103, False)
        assert final.s_down == pytest.approx(expected_s_down, abs=1e-9)
        assert final.s_up == 0.0
        assert final.alarms_up == 0
        assert final.alarms_down == 0  # 0.558 << 4.0

    def test_ten_candidates_upper_floors_then_climbs(self):
        # Alternating 3 C / 7 N — CR=30%, strong upward shift.
        # Apply in sequence; verify intermediate values.
        outcomes = [True, False, True, False, False, True, False, False, False, False]
        state = compute_cusum(outcomes)
        # Hand-computed (from docstring verification earlier):
        #   step 1 (C): s_up = max(0, 0 + 0.69315) = 0.69315
        #   step 2 (N): s_up = max(0, 0.69315 - 0.12197) = 0.57117
        #   step 3 (C): s_up = 1.26432
        #   step 4 (N): s_up = 1.14235
        #   step 5 (N): s_up = 1.02038
        #   step 6 (C): s_up = 1.71352
        #   step 7 (N): s_up = 1.59155
        #   step 8 (N): s_up = 1.46958
        #   step 9 (N): s_up = 1.34761
        #   step 10 (N): s_up = 1.22563
        assert state.s_up == pytest.approx(1.22563, abs=1e-4)
        assert state.n_obs == 10
        assert state.n_candidates == 3
        assert state.alarms_up == 0  # 1.22 << 4.0

    def test_pure_baseline_sequence_stays_floored(self):
        # Simulate a sequence very close to p0=0.103: 1 C out of 10 = 10%.
        outcomes = [True] + [False] * 9
        state = compute_cusum(outcomes)
        # At p=10.3%, upper CUSUM should trend to 0 (floor), lower similarly.
        # The single C spike starts s_up at 0.693, then decays by 0.122/step.
        # After 6 N's total drop = 6*0.122 = 0.732 > 0.693 → floored.
        assert state.s_up == pytest.approx(0.0, abs=1e-6)
        # Lower started at 1 C = -0.693 (floored to 0), then 9 N * 0.0558 = 0.502.
        assert state.s_down == pytest.approx(9 * 0.055829, abs=1e-4)
        assert state.alarms_up == 0
        assert state.alarms_down == 0


# =============================================================================
# Threshold crossing — exact up
# =============================================================================


class TestUpperThresholdCrossing:
    def test_all_candidates_upper_alarm_fires(self):
        # Each CANDIDATE adds ~0.693 to s_up. Need ceil(4.0/0.693) = 6 C's to
        # cross h=4.0. Actually 6*0.693 = 4.158 > 4.0 → crosses on step 6.
        outcomes = [True] * 6
        state = compute_cusum(outcomes)
        assert state.alarms_up == 1
        assert state.s_up == 0.0  # Page restart after alarm

    def test_upper_alarm_fires_on_exact_crossing_step(self):
        # Feed one at a time, assert exact step of crossing.
        state = CUSUMState()
        fired_at: list[int] = []
        for i in range(6):
            step = step_cusum(state, True)
            if step.fired_up:
                fired_at.append(i + 1)
        assert fired_at == [6]

    def test_just_below_upper_threshold_no_alarm(self):
        # 5 C's → 5 * 0.693 = 3.466 < 4.0.
        outcomes = [True] * 5
        state = compute_cusum(outcomes)
        assert state.alarms_up == 0
        assert state.s_up > 3.0 and state.s_up < 4.0


class TestLowerThresholdCrossing:
    def test_lower_alarm_on_long_no_trade_run(self):
        # Each NO_TRADE adds ~0.0558 to s_down. Need ceil(4.0/0.0558) = 72 N's.
        # Exactly 72*0.0558 = 4.0200 → first cross at step 72.
        outcomes = [False] * 72
        state = compute_cusum(outcomes)
        assert state.alarms_down == 1
        assert state.s_down == 0.0  # Page restart

    def test_just_below_lower_threshold_no_alarm(self):
        # 71 N's → 71 * 0.0558 = 3.9638 < 4.0.
        outcomes = [False] * 71
        state = compute_cusum(outcomes)
        assert state.alarms_down == 0
        assert state.s_down > 3.9 and state.s_down < 4.0

    def test_lower_alarm_exact_step(self):
        state = CUSUMState()
        fired_at: list[int] = []
        for i in range(75):
            step = step_cusum(state, False)
            if step.fired_down:
                fired_at.append(i + 1)
        # Step 72 should fire, and no further alarms until accumulator recovers.
        assert fired_at == [72]


# =============================================================================
# Page restart rule — accumulator zeroes after alarm
# =============================================================================


class TestRestartAfterAlarm:
    def test_upper_resets_to_zero_after_alarm(self):
        outcomes = [True] * 6
        state = compute_cusum(outcomes)
        assert state.alarms_up == 1
        assert state.s_up == 0.0

    def test_continued_candidates_after_alarm_can_alarm_again(self):
        # 6 C's → alarm 1; 6 more → alarm 2; 6 more → alarm 3.
        outcomes = [True] * 18
        state = compute_cusum(outcomes)
        assert state.alarms_up == 3
        assert state.s_up == 0.0

    def test_no_trade_run_resets_lower_after_alarm(self):
        outcomes = [False] * 144  # 72 + 72
        state = compute_cusum(outcomes)
        assert state.alarms_down == 2


# =============================================================================
# Small-sample guard (insufficient_sample)
# =============================================================================


class TestInsufficientSample:
    def test_alarm_suppressed_when_n_obs_below_min(self, tmp_path, monkeypatch):
        # 6 C's → s_up crosses h=4.0 → would alarm, but n_obs=6 < MIN=30.
        # The run_monitor() path should set alarm_fired_today=False.
        monkeypatch.setattr(_mod, "LOG_PATH", tmp_path / "log.jsonl")
        monkeypatch.setattr(_mod, "STATE_PATH", tmp_path / "state.json")
        monkeypatch.setattr(_mod, "OUTPUT_CSV", tmp_path / "out.csv")
        # Keep MIN_OBSERVATIONS at its default 30 to exercise the gate.
        _write_log(
            tmp_path / "log.jsonl",
            [(_ts(2026, 4, 19, 0, i), "CANDIDATE") for i in range(6)],
        )
        rc = _mod.run_monitor()
        # alarms_up registered in state but suppressed externally → exit 0.
        assert rc == 0
        with open(tmp_path / "out.csv", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 1
        assert rows[0]["alarm_fired_today"] == "false"
        assert rows[0]["insufficient_sample"] == "true"
        # But the state records the alarm count honestly.
        state = load_state(tmp_path / "state.json")
        assert state.alarms_up == 1

    def test_alarm_fires_once_min_observations_met(self, tmp_path, monkeypatch):
        # 30 N's to hit MIN, then 6 C's to trigger upper alarm.
        monkeypatch.setattr(_mod, "LOG_PATH", tmp_path / "log.jsonl")
        monkeypatch.setattr(_mod, "STATE_PATH", tmp_path / "state.json")
        monkeypatch.setattr(_mod, "OUTPUT_CSV", tmp_path / "out.csv")
        entries = [(_ts(2026, 4, 19, 0, i), "NO_TRADE") for i in range(30)]
        entries += [(_ts(2026, 4, 19, 1, i), "CANDIDATE") for i in range(6)]
        _write_log(tmp_path / "log.jsonl", entries)
        rc = _mod.run_monitor()
        assert rc == 1  # alarm
        with open(tmp_path / "out.csv", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert rows[0]["alarm_fired_today"] == "true"
        assert "up" in rows[0]["alarm_side_today"]
        assert rows[0]["insufficient_sample"] == "false"


# =============================================================================
# State round-trip + reload
# =============================================================================


class TestStatePersistence:
    def test_round_trip_preserves_values(self, tmp_path):
        state = CUSUMState(
            s_up=1.234, s_down=0.456,
            n_obs=100, n_candidates=12,
            alarms_up=2, alarms_down=0,
            last_processed_ts="2026-04-19T12:34:56+00:00",
        )
        save_state(state, tmp_path / "s.json")
        loaded = load_state(tmp_path / "s.json")
        assert loaded.s_up == pytest.approx(1.234)
        assert loaded.s_down == pytest.approx(0.456)
        assert loaded.n_obs == 100
        assert loaded.n_candidates == 12
        assert loaded.alarms_up == 2
        assert loaded.alarms_down == 0
        assert loaded.last_processed_ts == "2026-04-19T12:34:56+00:00"

    def test_missing_file_returns_fresh_state(self, tmp_path):
        s = load_state(tmp_path / "does_not_exist.json")
        assert s == CUSUMState()

    def test_corrupt_json_returns_fresh_state(self, tmp_path, caplog):
        path = tmp_path / "s.json"
        path.write_text("{not valid json", encoding="utf-8")
        with caplog.at_level("WARNING"):
            s = load_state(path)
        assert s == CUSUMState()
        assert "corrupt" in caplog.text.lower()

    def test_state_with_wrong_root_type_returns_fresh(self, tmp_path, caplog):
        path = tmp_path / "s.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")
        with caplog.at_level("WARNING"):
            s = load_state(path)
        assert s == CUSUMState()

    def test_state_with_negative_field_returns_fresh(self, tmp_path, caplog):
        path = tmp_path / "s.json"
        path.write_text(json.dumps({"s_up": -1.0, "n_obs": 5}), encoding="utf-8")
        with caplog.at_level("WARNING"):
            s = load_state(path)
        assert s == CUSUMState()

    def test_state_with_missing_fields_uses_defaults(self, tmp_path):
        path = tmp_path / "s.json"
        # Only ``s_up`` present — others should default.
        path.write_text(json.dumps({"s_up": 2.5}), encoding="utf-8")
        s = load_state(path)
        assert s.s_up == pytest.approx(2.5)
        assert s.s_down == 0.0
        assert s.n_obs == 0
        assert s.last_processed_ts is None


# =============================================================================
# run_monitor — integration smoke
# =============================================================================


class TestRunMonitor:
    def test_empty_log_no_alarm_no_crash(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_mod, "LOG_PATH", tmp_path / "log.jsonl")
        monkeypatch.setattr(_mod, "STATE_PATH", tmp_path / "state.json")
        monkeypatch.setattr(_mod, "OUTPUT_CSV", tmp_path / "out.csv")
        # No log file at all.
        rc = _mod.run_monitor()
        assert rc == 0
        # CSV should still be written (with n_obs=0 row).
        assert (tmp_path / "out.csv").exists()

    def test_dry_run_writes_nothing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_mod, "LOG_PATH", tmp_path / "log.jsonl")
        monkeypatch.setattr(_mod, "STATE_PATH", tmp_path / "state.json")
        monkeypatch.setattr(_mod, "OUTPUT_CSV", tmp_path / "out.csv")
        _write_log(
            tmp_path / "log.jsonl",
            [(_ts(2026, 4, 19, 0, i), "CANDIDATE") for i in range(3)],
        )
        rc = _mod.run_monitor(dry_run=True)
        assert rc == 0
        assert not (tmp_path / "state.json").exists()
        assert not (tmp_path / "out.csv").exists()

    def test_incremental_run_processes_only_new_rows(self, tmp_path, monkeypatch):
        # First run: 10 observations. Second run: add 10 more. State should
        # reflect 20 total, not 30.
        monkeypatch.setattr(_mod, "LOG_PATH", tmp_path / "log.jsonl")
        monkeypatch.setattr(_mod, "STATE_PATH", tmp_path / "state.json")
        monkeypatch.setattr(_mod, "OUTPUT_CSV", tmp_path / "out.csv")
        entries_1 = [(_ts(2026, 4, 19, 0, i), "NO_TRADE") for i in range(10)]
        _write_log(tmp_path / "log.jsonl", entries_1)
        _mod.run_monitor()
        state_1 = load_state(tmp_path / "state.json")
        assert state_1.n_obs == 10

        entries_2 = entries_1 + [(_ts(2026, 4, 19, 1, i), "NO_TRADE") for i in range(10)]
        _write_log(tmp_path / "log.jsonl", entries_2)
        _mod.run_monitor()
        state_2 = load_state(tmp_path / "state.json")
        assert state_2.n_obs == 20
        # Second run is a NO-OP on the first 10 rows → no double-count.

    def test_reset_state_reprocesses_from_scratch(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_mod, "LOG_PATH", tmp_path / "log.jsonl")
        monkeypatch.setattr(_mod, "STATE_PATH", tmp_path / "state.json")
        monkeypatch.setattr(_mod, "OUTPUT_CSV", tmp_path / "out.csv")
        entries = [(_ts(2026, 4, 19, 0, i), "NO_TRADE") for i in range(5)]
        _write_log(tmp_path / "log.jsonl", entries)
        _mod.run_monitor()
        assert load_state(tmp_path / "state.json").n_obs == 5
        _mod.run_monitor()  # incremental: nothing new → still 5
        assert load_state(tmp_path / "state.json").n_obs == 5
        _mod.run_monitor(reset_state=True)  # should re-process all 5
        assert load_state(tmp_path / "state.json").n_obs == 5  # final count is 5

    def test_csv_snapshot_schema_is_stable(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_mod, "LOG_PATH", tmp_path / "log.jsonl")
        monkeypatch.setattr(_mod, "STATE_PATH", tmp_path / "state.json")
        monkeypatch.setattr(_mod, "OUTPUT_CSV", tmp_path / "out.csv")
        _write_log(
            tmp_path / "log.jsonl",
            [(_ts(2026, 4, 19, 0, i), "NO_TRADE") for i in range(5)],
        )
        _mod.run_monitor()
        with open(tmp_path / "out.csv", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
            fields = reader.fieldnames
        assert fields == _mod._CSV_FIELDS
        assert len(rows) == 1
        r = rows[0]
        assert r["scope"] == "OVERALL"
        assert int(r["total_obs"]) == 5
        assert int(r["candidate_count"]) == 0
        assert r["alarm_fired_today"] == "false"

    def test_same_day_rerun_dedupes_on_scope(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_mod, "LOG_PATH", tmp_path / "log.jsonl")
        monkeypatch.setattr(_mod, "STATE_PATH", tmp_path / "state.json")
        monkeypatch.setattr(_mod, "OUTPUT_CSV", tmp_path / "out.csv")
        _write_log(
            tmp_path / "log.jsonl",
            [(_ts(2026, 4, 19, 0, i), "NO_TRADE") for i in range(3)],
        )
        _mod.run_monitor(target_date=datetime(2026, 4, 19).date())
        _mod.run_monitor(target_date=datetime(2026, 4, 19).date())  # same day re-run
        with open(tmp_path / "out.csv", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 1
        assert rows[0]["date_utc"] == "2026-04-19"

    def test_malformed_log_lines_are_skipped(self, tmp_path, monkeypatch, caplog):
        monkeypatch.setattr(_mod, "LOG_PATH", tmp_path / "log.jsonl")
        monkeypatch.setattr(_mod, "STATE_PATH", tmp_path / "state.json")
        monkeypatch.setattr(_mod, "OUTPUT_CSV", tmp_path / "out.csv")
        log_path = tmp_path / "log.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            "\n".join([
                json.dumps({"timestamp_utc": _ts(2026, 4, 19, 0, 0), "decision": "NO_TRADE"}),
                "not valid json",
                json.dumps({"timestamp_utc": _ts(2026, 4, 19, 0, 15), "decision": "CANDIDATE"}),
                json.dumps({"decision": "NO_TRADE"}),  # missing ts
                json.dumps({"timestamp_utc": _ts(2026, 4, 19, 0, 30), "decision": "HALLUCINATED"}),
            ]) + "\n",
            encoding="utf-8",
        )
        with caplog.at_level("WARNING"):
            rc = _mod.run_monitor()
        assert rc == 0
        state = load_state(tmp_path / "state.json")
        # Only the 2 valid rows should be processed.
        assert state.n_obs == 2
        assert state.n_candidates == 1

    def test_corrupt_state_reprocesses_all_rows(self, tmp_path, monkeypatch, caplog):
        # Tamper the state file → monitor should degrade to fresh, reprocess
        # all rows, and NOT crash.
        monkeypatch.setattr(_mod, "LOG_PATH", tmp_path / "log.jsonl")
        monkeypatch.setattr(_mod, "STATE_PATH", tmp_path / "state.json")
        monkeypatch.setattr(_mod, "OUTPUT_CSV", tmp_path / "out.csv")
        _write_log(
            tmp_path / "log.jsonl",
            [(_ts(2026, 4, 19, 0, i), "NO_TRADE") for i in range(5)],
        )
        (tmp_path / "state.json").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "state.json").write_text("{not_valid", encoding="utf-8")
        with caplog.at_level("WARNING"):
            rc = _mod.run_monitor()
        assert rc == 0
        state = load_state(tmp_path / "state.json")
        assert state.n_obs == 5  # all 5 reprocessed


# =============================================================================
# step_cusum — unit tests for alarm signaling
# =============================================================================


class TestStepCusumAlarmFlags:
    def test_fired_up_flag_returned_on_crossing(self):
        state = CUSUMState()
        # 5 C's → s_up=3.466, no alarm.
        for _ in range(5):
            r = step_cusum(state, True)
            assert not r.fired_up
        # 6th C crosses h.
        r = step_cusum(state, True)
        assert r.fired_up
        assert not r.fired_down

    def test_fired_down_flag_returned_on_crossing(self):
        state = CUSUMState()
        for i in range(72):
            r = step_cusum(state, False)
            if i == 71:
                assert r.fired_down
                assert not r.fired_up
            else:
                assert not r.fired_down

    def test_state_returned_is_same_object_mutated(self):
        state = CUSUMState()
        r = step_cusum(state, True)
        assert r.state is state

    def test_degenerate_targets_raise(self):
        with pytest.raises(ValueError):
            step_cusum(CUSUMState(), True, p0=0.1, p1_up=0.1, p1_down=0.05)


# =============================================================================
# CLI argument parsing
# =============================================================================


class TestCLI:
    def test_parse_date(self):
        ns = _mod._parse_args(["--date", "2026-04-19"])
        assert ns.date == "2026-04-19"
        assert not ns.dry_run
        assert not ns.reset_state

    def test_parse_dry_run(self):
        ns = _mod._parse_args(["--dry-run"])
        assert ns.dry_run

    def test_parse_reset_state(self):
        ns = _mod._parse_args(["--reset-state"])
        assert ns.reset_state

    def test_invalid_date_returns_exit_2(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_mod, "LOG_PATH", tmp_path / "log.jsonl")
        monkeypatch.setattr(_mod, "STATE_PATH", tmp_path / "state.json")
        monkeypatch.setattr(_mod, "OUTPUT_CSV", tmp_path / "out.csv")
        rc = _mod.main(["--date", "not-a-date"])
        assert rc == 2
