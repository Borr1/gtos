"""Exact H4 event-transfer and default-off production-plumbing tests."""

from __future__ import annotations

import json
import random
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
from src.components.ultimate_book.event_clock_shadow import (
    ExactH4CloseClassifier,
    H4EventClockShadowLatch,
    TF_H4,
)
from src.components.ultimate_book.launcher import BookLauncher
from src.research_infra.event_clock_gate import DEFAULT_REJECT_HOURS, EventClockGate
from src.utils.broker_clock import (
    NEW_YORK_PLUS_7,
    UnknownBrokerClockError,
    fixed_offset_rule,
    utc_to_broker_naive,
)


def _utc(year, month, day, hour=0, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "bar_open",
    [
        _utc(2026, 2, 11, 18),  # EST: broker 20 -> close 00 at 22Z
        _utc(2026, 3, 20, 17),  # US/EU disagreement: EDT already, close 00 at 21Z
        _utc(2026, 7, 15, 17),  # EDT
    ],
)
def test_exact_broker_midnight_h4_close_is_the_transfer_event(bar_open):
    row = ExactH4CloseClassifier.for_server("FTMO-Server3").classify(
        decision_bar_iso=bar_open.isoformat(), timeframe=TF_H4
    )
    assert row["decision_bar_iso"] == bar_open.isoformat()
    assert row["decision_bar_semantics"] == "bar_open_utc"
    assert row["event_close_utc"] == (bar_open + timedelta(hours=4)).isoformat()
    assert (row["broker_hour"], row["broker_minute"]) == (0, 0)
    assert row["exact_h4_grid_close"] is True
    assert row["q2_hour_gate_rejects"] is True
    assert row["shadow_would_reject"] is True
    assert row["admission_effect"] is False


@pytest.mark.parametrize("minute", [15, 30, 45])
def test_hour_zero_quarter_marks_are_not_exact_h4_events(minute):
    bar_open = _utc(2026, 3, 20, 17, minute)
    row = ExactH4CloseClassifier.for_server("FTMO-Server3").classify(
        decision_bar_iso=bar_open, timeframe=TF_H4
    )
    assert (row["broker_hour"], row["broker_minute"]) == (0, minute)
    assert row["q2_hour_gate_rejects"] is True  # the broad hour cell includes it
    assert row["exact_h4_grid_close"] is False  # the live H4 event does not
    assert row["shadow_would_reject"] is False
    assert row["reason"] == "not_exact_h4_grid_close"


def test_latch_preserves_midnight_verdict_when_cycle_retries_after_broker_01():
    shadow = H4EventClockShadowLatch(lambda: "FTMO-Server3")
    bar_open = _utc(2026, 7, 15, 17)
    first = shadow.observe(
        decision_bar_iso=bar_open,
        timeframe=TF_H4,
        observed_at_utc=_utc(2026, 7, 15, 21, 1),
    )
    retry_at = _utc(2026, 7, 15, 22, 30)
    assert utc_to_broker_naive(retry_at, NEW_YORK_PLUS_7).hour == 1
    retry = shadow.observe(
        decision_bar_iso=bar_open,
        timeframe=TF_H4,
        observed_at_utc=retry_at,
    )
    assert first["latch_hit"] is False and retry["latch_hit"] is True
    assert retry["event_close_utc"] == first["event_close_utc"]
    assert retry["shadow_would_reject"] is first["shadow_would_reject"] is True
    assert retry["latched_at_utc"] == first["latched_at_utc"]
    assert retry["observed_at_utc"] != first["observed_at_utc"]
    assert shadow.latch_size == 1


def test_us_rule_not_eu_rule_controls_disagreement_window_event():
    bar_open = _utc(2026, 3, 20, 17)
    measured = ExactH4CloseClassifier.for_server("FTMO-Server3").classify(
        decision_bar_iso=bar_open, timeframe=TF_H4
    )
    eu_wrong = ExactH4CloseClassifier(
        server="test-eu-wrong",
        gate=EventClockGate(
            fixed_offset_rule(2.0, evidence="test-only EU winter proxy"),
            frozenset(DEFAULT_REJECT_HOURS),
        ),
    ).classify(decision_bar_iso=bar_open, timeframe=TF_H4)
    assert measured["broker_hour"] == 0 and measured["shadow_would_reject"] is True
    assert eu_wrong["broker_hour"] == 23
    assert eu_wrong["q2_hour_gate_rejects"] is True
    assert eu_wrong["exact_h4_grid_close"] is False
    assert eu_wrong["shadow_would_reject"] is False


def test_production_decision_bar_iso_is_open_not_the_event_instant():
    bar_open = _utc(2026, 7, 15, 17)  # broker 20:00
    gate = EventClockGate.for_server("FTMO-Server3")
    assert gate.rejects(bar_open) is False
    row = ExactH4CloseClassifier.for_server("FTMO-Server3").classify(
        decision_bar_iso=bar_open.isoformat(), timeframe=TF_H4
    )
    assert row["event_close_utc"] == _utc(2026, 7, 15, 21).isoformat()
    assert row["shadow_would_reject"] is True


def test_unknown_server_refuses_classifier_and_shadow_latches_no_verdict():
    with pytest.raises(UnknownBrokerClockError):
        ExactH4CloseClassifier.for_server("unmeasured-server")

    server = ["unmeasured-server"]
    shadow = H4EventClockShadowLatch(lambda: server[0])
    bar_open = _utc(2026, 7, 15, 17)
    first = shadow.observe(
        decision_bar_iso=bar_open,
        timeframe=TF_H4,
        observed_at_utc=_utc(2026, 7, 15, 21, 1),
    )
    assert first["classification_status"] == "clock_unavailable_fail_closed"
    assert first["shadow_would_reject"] is None
    assert first["admission_effect"] is False
    server[0] = "FTMO-Server3"
    retry = shadow.observe(
        decision_bar_iso=bar_open,
        timeframe=TF_H4,
        observed_at_utc=_utc(2026, 7, 15, 22, 30),
    )
    assert retry["latch_hit"] is True
    assert retry["classification_status"] == "clock_unavailable_fail_closed"
    assert retry["shadow_would_reject"] is None


def test_naive_bar_open_and_cycle_time_are_refused():
    shadow = H4EventClockShadowLatch(lambda: "FTMO-Server3")
    with pytest.raises(ValueError, match="timezone-aware"):
        shadow.observe(
            decision_bar_iso=datetime(2026, 7, 15, 17),
            timeframe=TF_H4,
            observed_at_utc=_utc(2026, 7, 15, 21),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        shadow.observe(
            decision_bar_iso=_utc(2026, 7, 15, 17),
            timeframe=TF_H4,
            observed_at_utc=datetime(2026, 7, 15, 21),
        )


def _config():
    return {
        "ultimate_book_enabled": False,
        "ultimate_book_apply_to_execution": False,
        "ultimate_book_live_activation_allowed": False,
        "ultimate_book_live_broker_authority": False,
        "ultimate_book_disable_broad_selector": True,
        "ultimate_book_profile": "clean3_w7_measured_nom1p25",
        "ultimate_book_derisk_mode": "band",
        "ultimate_book_include_clean3": True,
        "ultimate_book_include_candidate_book": False,
        "ultimate_book_include_market_expansion_book": False,
        "ultimate_book_kelly_lite": True,
        "ultimate_book_kelly_conservative": True,
        "ultimate_book_stress_derisk": False,
        "ultimate_book_drop_w7_symbols": True,
        "selector_v4_enabled": True,
        "selector_v4_apply_to_execution": False,
    }


class _EngineMT5:
    def get_candles(self, symbol, timeframe, count):
        rnd = random.Random(7 if symbol == "BTCUSD" else 11)
        forming = _utc(2026, 3, 20, 21)
        start = forming - timedelta(hours=4 * count)
        price = 100.0
        rows = []
        for index in range(count + 1):
            open_price = price
            close_price = max(1.0, open_price + rnd.gauss(0.2, 0.5))
            rows.append(
                {
                    "time": (start + timedelta(hours=4 * index)).isoformat(),
                    "open": open_price,
                    "high": max(open_price, close_price) + 0.2,
                    "low": min(open_price, close_price) - 0.2,
                    "close": close_price,
                    "volume": 100,
                }
            )
            price = close_price
        return rows

    def get_account_equity(self):
        return 100_000.0


def _intent_identity(result):
    return sorted(
        (
            intent.sleeve,
            intent.symbol,
            intent.direction,
            intent.decision_day,
            float(intent.entry),
            float(intent.stop_dist),
        )
        for intent in result["intents"]
    )


def test_engine_shadow_is_default_off_and_does_not_change_admission():
    now = _utc(2026, 3, 20, 21, 1)
    control = UltimateBookLiveEngine(
        _config(), _EngineMT5(), tempfile.mkdtemp(), broker_server=lambda: "FTMO-Server3"
    ).evaluate(tags=("crypto",), now_utc=now)
    observed = UltimateBookLiveEngine(
        _config(),
        _EngineMT5(),
        tempfile.mkdtemp(),
        broker_server=lambda: "FTMO-Server3",
        event_clock_shadow=True,
    ).evaluate(tags=("crypto",), now_utc=now)

    assert "event_clock_shadow" not in control["generation"]
    assert observed["generation"]["event_clock_shadow"]
    assert control["ok"] == observed["ok"]
    assert control["reason"] == observed["reason"]
    assert control["runtime_effect_now"] == observed["runtime_effect_now"]
    assert control["n_intents"] == observed["n_intents"]
    assert _intent_identity(control) == _intent_identity(observed)
    assert all(row["admission_effect"] is False for row in observed["generation"]["event_clock_shadow"])
    assert all(row["event_close_utc"] == _utc(2026, 3, 20, 21).isoformat()
               for row in observed["generation"]["event_clock_shadow"])


def test_engine_unknown_clock_records_fail_closed_but_keeps_same_decision():
    now = _utc(2026, 3, 20, 21, 1)
    control = UltimateBookLiveEngine(
        _config(), _EngineMT5(), tempfile.mkdtemp()
    ).evaluate(tags=("crypto",), now_utc=now)
    observed = UltimateBookLiveEngine(
        _config(),
        _EngineMT5(),
        tempfile.mkdtemp(),
        broker_server=lambda: "unmeasured-server",
        event_clock_shadow=True,
    ).evaluate(tags=("crypto",), now_utc=now)
    rows = observed["generation"]["event_clock_shadow"]
    assert rows and {row["classification_status"] for row in rows} == {
        "clock_unavailable_fail_closed"
    }
    assert all(row["shadow_would_reject"] is None for row in rows)
    assert (control["reason"], control["n_intents"], _intent_identity(control)) == (
        observed["reason"], observed["n_intents"], _intent_identity(observed)
    )


class _LauncherMT5:
    def __init__(self):
        self.head = _utc(2026, 7, 15, 21)

    def get_candles(self, symbol, timeframe, count):
        return [
            {
                "time": (self.head - timedelta(hours=4 * offset)).isoformat(),
                "open": 100,
                "high": 101,
                "low": 99,
                "close": 100.5,
                "volume": 100,
            }
            for offset in (2, 1, 0)
        ]


class _LauncherOwner:
    base_config = {}
    _namespace = "q2_test"

    def manage_open_positions(self, **_kwargs):
        return {"managed": [], "adopted": [], "closed": [], "errors": []}

    def run_cycle(self, **_kwargs):
        return {
            "ok": True,
            "reason": "unchanged",
            "n_intents": 0,
            "runtime_effect_now": True,
            "placed": [],
            "shadow": 0,
            "skipped": [],
            "event_clock_shadow": [{"schema": "gtos.q2_exact_h4_event_shadow.v1"}],
        }


def test_launcher_persists_shadow_classification_in_existing_cycle_jsonl(tmp_path):
    launcher = BookLauncher(
        _LauncherOwner(),
        _LauncherMT5(),
        lambda symbol: symbol,
        repo_root=str(tmp_path),
        tags=("crypto",),
        poll_seconds=0.01,
    )
    record = launcher.tick(now_utc=_utc(2026, 7, 15, 21, 1))
    assert record["event_clock_shadow"][0]["schema"] == "gtos.q2_exact_h4_event_shadow.v1"
    path = tmp_path / "shadow_logs" / "ultimate_book_launcher.jsonl"
    persisted = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])
    assert persisted["namespace"] == "q2_test"
    assert persisted["event_clock_shadow"] == record["event_clock_shadow"]
