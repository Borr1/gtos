import json

from src.components import m1_capture


class _FakeMT5Api:
    TIMEFRAME_M1 = 1

    def __init__(self):
        self.selected = []

    def symbol_select(self, symbol, enabled):
        self.selected.append((symbol, enabled))
        return True


class _FakeMT5:
    def __init__(self, responses):
        self._mt5 = _FakeMT5Api()
        self._responses = responses

    def get_candles(self, broker_symbol, timeframe, fetch_bars):
        response = self._responses[broker_symbol]
        if isinstance(response, Exception):
            raise response
        return response


def _candle(time_utc, close):
    return {
        "time": time_utc,
        "open": close - 0.1,
        "high": close + 0.2,
        "low": close - 0.2,
        "close": close,
        "volume": 10,
    }


def test_capture_once_persists_only_new_closed_m1_rows(monkeypatch):
    appended = []
    saved = []
    heartbeats = []
    state = {
        "symbols": {
            "XAUUSD": {
                "last_time_utc": "2026-05-28T15:24:00+00:00",
            }
        }
    }
    fake = _FakeMT5(
        {
            "XAUUSD": [
                _candle("2026-05-28T15:24:00+00:00", 3320.1),
                _candle("2026-05-28T15:25:00+00:00", 3320.2),
                _candle("2026-05-28T15:26:00+00:00", 3320.3),
            ],
        }
    )

    monkeypatch.setattr(m1_capture, "_append_rows", lambda rows: appended.extend(rows))
    monkeypatch.setattr(
        m1_capture,
        "_save_state",
        lambda payload: saved.append(json.loads(json.dumps(payload))),
    )
    monkeypatch.setattr(
        m1_capture,
        "write_daemon_heartbeat",
        lambda name, **kwargs: heartbeats.append((name, kwargs)),
    )

    rows, errors = m1_capture.capture_once(
        mt5=fake,
        symbols={"XAUUSD": "XAUUSD"},
        state=state,
        fetch_bars=5,
    )

    assert rows == 1
    assert errors == []
    assert [row["time_utc"] for row in appended] == ["2026-05-28T15:25:00+00:00"]
    assert saved[-1]["symbols"]["XAUUSD"]["last_time_utc"] == "2026-05-28T15:25:00+00:00"
    assert saved[-1]["symbols"]["XAUUSD"]["last_cycle_status"] == "ok"
    assert saved[-1]["symbols"]["XAUUSD"]["last_rows_written"] == 1
    assert saved[-1]["symbols"]["XAUUSD"]["last_closed_candle_time_utc"] == "2026-05-28T15:25:00+00:00"
    assert saved[-1]["symbols"]["XAUUSD"]["last_closed_candle_age_seconds"] is not None
    assert saved[-1]["symbols"]["XAUUSD"]["last_no_new_row_reason"] is None
    assert heartbeats[-1][0] == m1_capture.LOCK_NAME
    assert heartbeats[-1][1]["extra"]["rows_written"] == 1


def test_capture_once_records_symbol_errors_without_blocking_other_symbols(monkeypatch):
    appended = []
    saved = []
    state = {"symbols": {}}
    fake = _FakeMT5(
        {
            "XAUUSD": [
                _candle("2026-05-28T15:25:00+00:00", 3320.2),
                _candle("2026-05-28T15:26:00+00:00", 3320.3),
            ],
            "AUDJPY": RuntimeError("mt5 unavailable"),
        }
    )

    monkeypatch.setattr(m1_capture, "_append_rows", lambda rows: appended.extend(rows))
    monkeypatch.setattr(
        m1_capture,
        "_save_state",
        lambda payload: saved.append(json.loads(json.dumps(payload))),
    )
    monkeypatch.setattr(m1_capture, "write_daemon_heartbeat", lambda *args, **kwargs: True)

    rows, errors = m1_capture.capture_once(
        mt5=fake,
        symbols={"XAUUSD": "XAUUSD", "AUDJPY": "AUDJPY"},
        state=state,
        fetch_bars=5,
    )

    assert rows == 1
    assert errors == ["AUDJPY:mt5 unavailable"]
    assert appended[0]["symbol"] == "XAUUSD"
    assert saved[-1]["last_error_count"] == 1
    assert saved[-1]["symbols"]["AUDJPY"]["last_cycle_status"] == "mt5_read_error"
    assert saved[-1]["symbols"]["AUDJPY"]["last_error"] == "mt5 unavailable"


def test_capture_once_persists_no_new_closed_m1_reason(monkeypatch):
    appended = []
    saved = []
    heartbeats = []
    state = {
        "symbols": {
            "XAUUSD": {
                "last_time_utc": "2026-05-28T15:25:00+00:00",
                "last_progress_utc": "2026-05-28T15:25:05+00:00",
            }
        }
    }
    fake = _FakeMT5(
        {
            "XAUUSD": [
                _candle("2026-05-28T15:24:00+00:00", 3320.1),
                _candle("2026-05-28T15:25:00+00:00", 3320.2),
                _candle("2026-05-28T15:26:00+00:00", 3320.3),
            ],
        }
    )

    monkeypatch.setattr(m1_capture, "_append_rows", lambda rows: appended.extend(rows))
    monkeypatch.setattr(
        m1_capture,
        "_save_state",
        lambda payload: saved.append(json.loads(json.dumps(payload))),
    )
    monkeypatch.setattr(
        m1_capture,
        "write_daemon_heartbeat",
        lambda name, **kwargs: heartbeats.append((name, kwargs)),
    )

    rows, errors = m1_capture.capture_once(
        mt5=fake,
        symbols={"XAUUSD": "XAUUSD"},
        state=state,
        fetch_bars=5,
    )

    assert rows == 0
    assert errors == []
    assert appended == []
    assert saved[-1]["symbols"]["XAUUSD"]["last_cycle_status"] == "ok"
    assert saved[-1]["symbols"]["XAUUSD"]["last_rows_written"] == 0
    assert saved[-1]["symbols"]["XAUUSD"]["last_no_new_row_reason"] == "latest_closed_m1_bar_not_new"
    assert heartbeats[-1][1]["last_progress_at"].isoformat() == "2026-05-28T15:25:05+00:00"
    assert heartbeats[-1][1]["extra"]["last_progress_source"] == (
        "persisted_symbol_last_progress_utc"
    )


def test_capture_once_skips_unrepaired_malformed_m1_rows(monkeypatch):
    appended = []
    saved = []
    state = {"symbols": {}}
    fake = _FakeMT5(
        {
            "ETHUSD": [
                {
                    "time": "2026-06-01T21:33:00+00:00",
                    "open": 6764.75,
                    "high": 6765.10,
                    "low": 6764.73,
                    "close": 6764.77,
                    "volume": 100,
                },
                _candle("2026-06-01T21:34:00+00:00", 1995.2),
            ],
        }
    )

    def _failed_repair(candles, *args, **kwargs):
        repaired = [
            {
                **candles[0],
                "ohlc_source_repair": {
                    "status": "repair_failed_local_tick_parquet_unavailable_or_empty",
                    "reason": "m1_anchor_price_jump_exceeds_threshold",
                },
            }
        ]
        return repaired, {"failed_count": 1, "repaired_count": 0, "events": []}

    monkeypatch.setattr(m1_capture, "_append_rows", lambda rows: appended.extend(rows))
    monkeypatch.setattr(
        m1_capture,
        "_save_state",
        lambda payload: saved.append(json.loads(json.dumps(payload))),
    )
    monkeypatch.setattr(m1_capture, "write_daemon_heartbeat", lambda *args, **kwargs: True)
    monkeypatch.setattr(m1_capture, "repair_malformed_ohlc_from_ticks", _failed_repair)

    rows, errors = m1_capture.capture_once(
        mt5=fake,
        symbols={"ETHUSD": "ETHUSD"},
        state=state,
        fetch_bars=5,
        config={},
    )

    assert rows == 0
    assert errors == []
    assert appended == []
    assert saved[-1]["symbols"]["ETHUSD"]["last_no_new_row_reason"] == (
        "malformed_m1_source_repair_failed"
    )
    assert saved[-1]["symbols"]["ETHUSD"]["last_ohlc_repair"]["failed_count"] == 1


def test_append_rows_partitions_by_symbol_and_day(tmp_path):
    rows = [
        {
            "time_utc": "2026-05-28T15:25:00+00:00",
            "symbol": "XAUUSD",
            "broker_symbol": "XAUUSD",
            "open": 1.0,
            "high": 2.0,
            "low": 0.5,
            "close": 1.5,
            "volume": 10,
            "captured_at_utc": "2026-05-28T15:25:10+00:00",
        },
        {
            "time_utc": "2026-05-29T00:01:00+00:00",
            "symbol": "XAUUSD",
            "broker_symbol": "XAUUSD",
            "open": 1.1,
            "high": 2.1,
            "low": 0.6,
            "close": 1.6,
            "volume": 11,
            "captured_at_utc": "2026-05-29T00:01:10+00:00",
        },
    ]

    m1_capture._append_rows(rows, root=tmp_path)

    assert (tmp_path / "XAUUSD" / "2026-05-28.csv").exists()
    assert (tmp_path / "XAUUSD" / "2026-05-29.csv").exists()
    assert "time_utc,symbol,broker_symbol" in (
        tmp_path / "XAUUSD" / "2026-05-28.csv"
    ).read_text(encoding="utf-8")


def test_append_rows_upserts_existing_symbol_minute(tmp_path):
    first = {
        "time_utc": "2026-06-01T21:44:00+00:00",
        "symbol": "ETHUSD",
        "broker_symbol": "ETHUSD",
        "open": 6764.75,
        "high": 6765.10,
        "low": 6764.73,
        "close": 6764.77,
        "volume": 3,
        "captured_at_utc": "2026-06-01T21:45:00+00:00",
    }
    repaired = {
        **first,
        "open": 1991.42,
        "high": 1993.04,
        "low": 1991.14,
        "close": 1992.17,
        "volume": 420,
        "captured_at_utc": "2026-06-01T21:48:00+00:00",
    }

    m1_capture._append_rows([first], root=tmp_path)
    m1_capture._append_rows([repaired], root=tmp_path)

    csv_text = (tmp_path / "ETHUSD" / "2026-06-01.csv").read_text(encoding="utf-8")
    assert csv_text.count("2026-06-01T21:44:00+00:00") == 1
    assert "6764.77" not in csv_text
    assert "1992.17" in csv_text
