"""
Tests for scripts/api_refusal_monitor.py

Covers:
- Flat refusal vs Pydantic error detection (_is_flat_refusal)
- Time-window filtering (count_recent_refusals)
- Cooldown state logic (_in_cooldown)
- Alert message formatting (build_alert_message)
- Telegram HTTP call (send_telegram)
- Full main() flow: threshold, credentials, cooldown, state persistence
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
import urllib.error

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.api_refusal_monitor import (
    _is_flat_refusal,
    count_recent_refusals,
    _in_cooldown,
    build_alert_message,
    malformed_response_category,
    send_telegram,
    summarize_malformed_entries,
    main,
    THRESHOLD,
    WINDOW_MINUTES,
    COOLDOWN_MINUTES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(offset_minutes: int, raw_len: int, error: str) -> dict:
    ts = datetime.now(timezone.utc) - timedelta(minutes=offset_minutes)
    return {
        "timestamp": ts.isoformat(),
        "attempt": 1,
        "error": error,
        "raw_response_length": raw_len,
        "raw_response": "x" * min(raw_len, 10),  # content doesn't matter
    }


FLAT_ERROR = "Expecting value: line 1 column 1 (char 0)"
PYDANTIC_ERROR = (
    "1 validation error for PrimaryAnalysisOutput\n"
    "reasoning.liquidity_sweep.pool_type\n"
    "  Input should be 'asian_high' ..."
)


def _write_jsonl(path: Path, entries: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


# ---------------------------------------------------------------------------
# _is_flat_refusal
# ---------------------------------------------------------------------------

class TestIsFlatRefusal:
    def test_detects_38byte_refusal(self):
        e = {"error": FLAT_ERROR, "raw_response_length": 38}
        assert _is_flat_refusal(e) is True

    def test_detects_8byte_refusal(self):
        e = {"error": FLAT_ERROR, "raw_response_length": 8}
        assert _is_flat_refusal(e) is True

    def test_excludes_pydantic_validation_error(self):
        e = {"error": PYDANTIC_ERROR, "raw_response_length": 2370}
        assert _is_flat_refusal(e) is False

    def test_excludes_large_response_even_with_json_error(self):
        # A real AI response that contains invalid JSON is not a flat refusal
        e = {"error": FLAT_ERROR, "raw_response_length": 500}
        assert _is_flat_refusal(e) is False

    def test_excludes_empty_error(self):
        assert _is_flat_refusal({"error": "", "raw_response_length": 10}) is False

    def test_excludes_missing_fields(self):
        assert _is_flat_refusal({}) is False

    def test_boundary_raw_len_99_is_refusal(self):
        e = {"error": FLAT_ERROR, "raw_response_length": 99}
        assert _is_flat_refusal(e) is True

    def test_boundary_raw_len_100_not_refusal(self):
        e = {"error": FLAT_ERROR, "raw_response_length": 100}
        assert _is_flat_refusal(e) is False


# ---------------------------------------------------------------------------
# malformed_response_category / summarize_malformed_entries
# ---------------------------------------------------------------------------

class TestMalformedResponseCategory:
    def test_category_detects_flat_refusal(self):
        e = {
            "error": FLAT_ERROR,
            "raw_response_length": 38,
            "raw_response": "Sorry, I can't produce JSON right now.",
        }
        assert malformed_response_category(e) == "FLAT_REFUSAL_OR_SHORT_NON_JSON"

    def test_category_detects_fenced_or_trailing_json_parse_failure(self):
        e = {
            "error": "Extra data: line 70 column 1 (char 3378)",
            "raw_response_length": 4378,
            "raw_response": "```json\n{\"decision\":\"CANDIDATE\"}\n```",
        }
        assert malformed_response_category(e) == "JSON_FENCE_OR_TRAILING_TEXT_PARSE_FAILURE"

    def test_category_detects_large_non_json_parse_failure_without_alerting(self):
        e = {
            "error": FLAT_ERROR,
            "raw_response_length": 500,
            "raw_response": "analysis before json",
        }
        assert malformed_response_category(e) == "NON_JSON_RESPONSE_PARSE_FAILURE"
        assert _is_flat_refusal(e) is False

    def test_summary_counts_context_capture_gap(self):
        rows = [
            {
                "error": FLAT_ERROR,
                "raw_response_length": 38,
                "raw_response": "Sorry, I can't produce JSON right now.",
                "symbol": "XAUUSD",
                "candle_time": "2026-04-13T08:00:00Z",
            },
            {
                "error": PYDANTIC_ERROR,
                "raw_response_length": 2370,
                "raw_response": "{\"decision\":\"NO_TRADE\"}",
            },
        ]
        summary = summarize_malformed_entries(rows)
        assert summary["malformed_response_rows"] == 2
        assert summary["malformed_response_category_counts"] == {
            "FLAT_REFUSAL_OR_SHORT_NON_JSON": 1,
            "OTHER_MALFORMED_AI_RESPONSE": 1,
        }
        assert summary["malformed_response_rows_with_symbol_and_candle_time"] == 1
        assert summary["malformed_response_rows_missing_symbol_or_candle_time"] == 1


# ---------------------------------------------------------------------------
# count_recent_refusals
# ---------------------------------------------------------------------------

class TestCountRecentRefusals:
    def test_missing_file_returns_empty(self, tmp_path):
        assert count_recent_refusals(tmp_path / "nonexistent.jsonl") == []

    def test_empty_file_returns_empty(self, tmp_path):
        log = tmp_path / "m.jsonl"
        log.write_text("")
        assert count_recent_refusals(log) == []

    def test_counts_flat_refusals_in_window(self, tmp_path):
        log = tmp_path / "m.jsonl"
        entries = [
            _entry(5, 38, FLAT_ERROR),   # in window
            _entry(15, 38, FLAT_ERROR),  # in window
            _entry(5, 2370, PYDANTIC_ERROR),  # excluded — Pydantic
        ]
        _write_jsonl(log, entries)
        result = count_recent_refusals(log, window_minutes=30)
        assert len(result) == 2

    def test_excludes_entries_outside_window(self, tmp_path):
        log = tmp_path / "m.jsonl"
        entries = [
            _entry(5, 38, FLAT_ERROR),    # in window
            _entry(60, 38, FLAT_ERROR),   # 60 min ago — outside 30-min window
        ]
        _write_jsonl(log, entries)
        result = count_recent_refusals(log, window_minutes=30)
        assert len(result) == 1

    def test_all_pydantic_returns_empty(self, tmp_path):
        log = tmp_path / "m.jsonl"
        entries = [
            _entry(5, 2370, PYDANTIC_ERROR),
            _entry(10, 2581, PYDANTIC_ERROR),
        ]
        _write_jsonl(log, entries)
        assert count_recent_refusals(log, window_minutes=30) == []

    def test_skips_non_json_lines(self, tmp_path):
        log = tmp_path / "m.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        valid = _entry(5, 38, FLAT_ERROR)
        log.write_text(
            "not-json-at-all\n"
            + json.dumps(valid) + "\n"
            + '{"timestamp": "bad-timestamp", "error": "' + FLAT_ERROR + '", "raw_response_length": 38}\n'
        )
        result = count_recent_refusals(log, window_minutes=30)
        # Only the valid entry with a parseable timestamp counts
        assert len(result) == 1

    def test_window_boundary_inclusive(self, tmp_path):
        log = tmp_path / "m.jsonl"
        # Exactly at the boundary (within floating-point margin)
        e = _entry(29, 38, FLAT_ERROR)  # 29 min ago — inside 30-min window
        _write_jsonl(log, [e])
        assert len(count_recent_refusals(log, window_minutes=30)) == 1

    def test_large_file_with_mixed_entries(self, tmp_path):
        log = tmp_path / "m.jsonl"
        entries = (
            [_entry(i, 38, FLAT_ERROR) for i in range(1, 6)]        # 5 refusals in window
            + [_entry(i + 60, 38, FLAT_ERROR) for i in range(1, 4)] # 3 outside window
            + [_entry(i, 2370, PYDANTIC_ERROR) for i in range(1, 4)] # 3 pydantic
        )
        _write_jsonl(log, entries)
        assert len(count_recent_refusals(log, window_minutes=30)) == 5


# ---------------------------------------------------------------------------
# _in_cooldown
# ---------------------------------------------------------------------------

class TestInCooldown:
    def test_empty_state_not_in_cooldown(self):
        assert _in_cooldown({}) is False

    def test_recent_alert_in_cooldown(self):
        recent = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        assert _in_cooldown({"last_alert_utc": recent}, cooldown_minutes=30) is True

    def test_old_alert_not_in_cooldown(self):
        old = (datetime.now(timezone.utc) - timedelta(minutes=60)).isoformat()
        assert _in_cooldown({"last_alert_utc": old}, cooldown_minutes=30) is False

    def test_just_past_cooldown_boundary(self):
        just_over = (datetime.now(timezone.utc) - timedelta(minutes=30, seconds=1)).isoformat()
        assert _in_cooldown({"last_alert_utc": just_over}, cooldown_minutes=30) is False

    def test_bad_timestamp_not_in_cooldown(self):
        assert _in_cooldown({"last_alert_utc": "not-a-date"}) is False

    def test_missing_key_not_in_cooldown(self):
        assert _in_cooldown({"other_key": "value"}) is False


# ---------------------------------------------------------------------------
# build_alert_message
# ---------------------------------------------------------------------------

class TestBuildAlertMessage:
    def test_count_appears_in_message(self):
        refusals = [
            {"timestamp": "2026-04-13T08:00:00+00:00"},
            {"timestamp": "2026-04-13T08:10:00+00:00"},
            {"timestamp": "2026-04-13T08:20:00+00:00"},
        ]
        msg = build_alert_message(refusals)
        assert "3" in msg

    def test_first_and_last_timestamps_present(self):
        refusals = [
            {"timestamp": "2026-04-13T08:00:00+00:00"},
            {"timestamp": "2026-04-13T08:30:00+00:00"},
        ]
        msg = build_alert_message(refusals)
        assert "2026-04-13 08:00:00" in msg
        assert "2026-04-13 08:30:00" in msg

    def test_message_contains_action_guidance(self):
        refusals = [{"timestamp": "2026-04-13T08:00:00+00:00"}]
        msg = build_alert_message(refusals)
        # Must tell operator what to do
        assert any(word in msg for word in ["Anthropic", "kill zone", "Check"])

    def test_single_entry_no_crash(self):
        refusals = [{"timestamp": "2026-04-13T08:00:00+00:00"}]
        msg = build_alert_message(refusals)
        assert isinstance(msg, str)
        assert len(msg) > 0


# ---------------------------------------------------------------------------
# send_telegram
# ---------------------------------------------------------------------------

class TestSendTelegram:
    def _mock_urlopen(self, status=200):
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.status = status
        return ctx

    def test_successful_send_returns_true(self, operator_delivery_grant):
        # Requests ``operator_delivery_grant``: send_telegram refuses before
        # building a request unless the process is authorized to page the
        # operator (F30 / Q7). This test asserts the authorized branch.
        mock_ctx = self._mock_urlopen(200)
        with patch("scripts.api_refusal_monitor.urllib.request.urlopen", return_value=mock_ctx):
            result = send_telegram("fake-token", "12345", "Test message")
        assert result is True

    def test_non_200_returns_false(self):
        mock_ctx = self._mock_urlopen(500)
        with patch("scripts.api_refusal_monitor.urllib.request.urlopen", return_value=mock_ctx):
            result = send_telegram("fake-token", "12345", "Test")
        assert result is False

    def test_http_error_returns_false(self):
        with patch(
            "scripts.api_refusal_monitor.urllib.request.urlopen",
            side_effect=urllib.error.HTTPError(url="", code=403, msg="Forbidden", hdrs=None, fp=None),
        ):
            result = send_telegram("fake-token", "12345", "Test")
        assert result is False

    def test_connection_error_returns_false(self):
        with patch(
            "scripts.api_refusal_monitor.urllib.request.urlopen",
            side_effect=OSError("Connection refused"),
        ):
            result = send_telegram("fake-token", "12345", "Test")
        assert result is False

    def test_url_contains_token(self, operator_delivery_grant):
        # Requests ``operator_delivery_grant``: send_telegram refuses before
        # building a request unless the process is authorized to page the
        # operator (F30 / Q7). This test asserts the authorized branch.
        mock_ctx = self._mock_urlopen(200)
        with patch("scripts.api_refusal_monitor.urllib.request.urlopen", return_value=mock_ctx) as mock_open:
            with patch("scripts.api_refusal_monitor.urllib.request.Request") as mock_req:
                mock_req.return_value = MagicMock()
                send_telegram("my-secret-token", "12345", "Test")
            call_args = mock_req.call_args[0]
            assert "my-secret-token" in call_args[0]  # URL contains token


# ---------------------------------------------------------------------------
# main() — integration
# ---------------------------------------------------------------------------

class TestMain:
    def _patch_paths(self, tmp_path, log_entries=None):
        """Context manager set-up helper — patches SHADOW_LOG and STATE_FILE."""
        log = tmp_path / "malformed.jsonl"
        state = tmp_path / "state.json"
        if log_entries is not None:
            _write_jsonl(log, log_entries)
        return log, state

    def test_below_threshold_returns_0(self, tmp_path):
        log, state = self._patch_paths(
            tmp_path,
            [_entry(i, 38, FLAT_ERROR) for i in range(1, THRESHOLD + 1)],  # exactly threshold
        )
        with patch("scripts.api_refusal_monitor.SHADOW_LOG", log):
            with patch("scripts.api_refusal_monitor.STATE_FILE", state):
                assert main() == 0

    def test_above_threshold_no_credentials_returns_1(self, tmp_path):
        log, state = self._patch_paths(
            tmp_path,
            [_entry(i, 38, FLAT_ERROR) for i in range(1, THRESHOLD + 2)],
        )
        with patch("scripts.api_refusal_monitor.SHADOW_LOG", log):
            with patch("scripts.api_refusal_monitor.STATE_FILE", state):
                with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}):
                    assert main() == 1

    def test_above_threshold_with_credentials_sends_alert_returns_0(self, tmp_path):
        log, state = self._patch_paths(
            tmp_path,
            [_entry(i, 38, FLAT_ERROR) for i in range(1, THRESHOLD + 2)],
        )
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.status = 200

        with patch("scripts.api_refusal_monitor.SHADOW_LOG", log):
            with patch("scripts.api_refusal_monitor.STATE_FILE", state):
                with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "tok", "TELEGRAM_CHAT_ID": "cid"}):
                    with patch("scripts.api_refusal_monitor.urllib.request.urlopen", return_value=mock_ctx):
                        result = main()
        assert result == 0
        # State file written with last_alert_utc
        assert state.exists()
        saved = json.loads(state.read_text())
        assert "last_alert_utc" in saved

    def test_cooldown_suppresses_repeat_alert(self, tmp_path):
        log, state = self._patch_paths(
            tmp_path,
            [_entry(i, 38, FLAT_ERROR) for i in range(1, THRESHOLD + 2)],
        )
        recent = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        state.write_text(json.dumps({"last_alert_utc": recent}))

        with patch("scripts.api_refusal_monitor.SHADOW_LOG", log):
            with patch("scripts.api_refusal_monitor.STATE_FILE", state):
                with patch("scripts.api_refusal_monitor.send_telegram") as mock_send:
                    result = main()
        assert result == 0
        mock_send.assert_not_called()

    def test_telegram_failure_returns_2(self, tmp_path):
        log, state = self._patch_paths(
            tmp_path,
            [_entry(i, 38, FLAT_ERROR) for i in range(1, THRESHOLD + 2)],
        )
        with patch("scripts.api_refusal_monitor.SHADOW_LOG", log):
            with patch("scripts.api_refusal_monitor.STATE_FILE", state):
                with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "tok", "TELEGRAM_CHAT_ID": "cid"}):
                    with patch("scripts.api_refusal_monitor.send_telegram", return_value=False):
                        assert main() == 2

    def test_no_log_file_returns_0(self, tmp_path):
        """No log file at all — should be a clean no-op."""
        log = tmp_path / "nonexistent.jsonl"
        state = tmp_path / "state.json"
        with patch("scripts.api_refusal_monitor.SHADOW_LOG", log):
            with patch("scripts.api_refusal_monitor.STATE_FILE", state):
                assert main() == 0

    def test_pydantic_errors_do_not_trigger_alert(self, tmp_path):
        """Pool_type failures are not flat refusals — should never alert."""
        log, state = self._patch_paths(
            tmp_path,
            [_entry(i, 2370, PYDANTIC_ERROR) for i in range(1, 10)],
        )
        with patch("scripts.api_refusal_monitor.SHADOW_LOG", log):
            with patch("scripts.api_refusal_monitor.STATE_FILE", state):
                with patch("scripts.api_refusal_monitor.send_telegram") as mock_send:
                    result = main()
        assert result == 0
        mock_send.assert_not_called()
