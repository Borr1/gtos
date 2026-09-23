"""Tests for C.3 — class-aware LONG-WR-watch SPRT halt checker.

Covers:
    - ``src/safety/sprt_class_halt_check.py``
        - ``find_class_for_instrument`` resolves classes correctly
        - ``check`` produces the expected verdict for each
          (class, n, wins) cell of the decision table
        - master switch ``sprt_halt.enabled: false`` short-circuits to OK
        - tight-FX / unconfigured instruments report CLASS_EXCLUDED
        - sample-size sentinels: < early_warning_n -> INSUFFICIENT_DATA
        - input validation (negative or impossible counts)

The checker is a pure function with no disk / network I/O, so tests
construct configs in-memory rather than loading from yaml. Where a test
needs the on-disk config (smoke tests at the bottom), it loads via the
``config`` fixture from ``tests/conftest.py``.
"""

from __future__ import annotations

import pytest

from src.safety.sprt_class_halt_check import (
    HaltCheckResult,
    check,
    find_class_for_instrument,
)


# --------------------------------------------------------------------------
# Test config fixture — minimal in-memory config matching the prod schema
# --------------------------------------------------------------------------


@pytest.fixture
def sprt_config():
    """Return a minimal config dict with the C.3 thresholds for unit tests.

    Mirrors the production ``sprt_halt`` block in
    ``config/agent_config.yaml`` exactly so unit tests fail if either
    drifts.
    """
    return {
        "sprt_halt": {
            "enabled": True,
            "automation_enabled": True,
            "trigger_n": 20,
            "early_warning_n": 10,
            "per_class_thresholds": {
                "metals": {
                    "halt_wr_pct": 55.0,
                    "early_warning_wr_pct": 50.0,
                    "instruments": ["XAUUSD", "XAGUSD"],
                },
                "indices": {
                    "halt_wr_pct": 40.0,
                    "early_warning_wr_pct": 35.0,
                    "instruments": ["US30", "US30_cash", "NAS100"],
                },
                "jpy_pairs": {
                    "halt_wr_pct": 45.0,
                    "early_warning_wr_pct": 40.0,
                    "instruments": ["USDJPY", "GBPJPY"],
                },
            },
        }
    }


# --------------------------------------------------------------------------
# find_class_for_instrument
# --------------------------------------------------------------------------


def test_find_class_metals(sprt_config):
    assert find_class_for_instrument("XAUUSD", sprt_config) == "metals"
    assert find_class_for_instrument("XAGUSD", sprt_config) == "metals"


def test_find_class_indices(sprt_config):
    assert find_class_for_instrument("US30", sprt_config) == "indices"
    assert find_class_for_instrument("US30_cash", sprt_config) == "indices"
    assert find_class_for_instrument("NAS100", sprt_config) == "indices"


def test_find_class_jpy_pairs(sprt_config):
    assert find_class_for_instrument("USDJPY", sprt_config) == "jpy_pairs"
    assert find_class_for_instrument("GBPJPY", sprt_config) == "jpy_pairs"


def test_find_class_unconfigured_returns_none(sprt_config):
    """Tight-FX (GBPUSD, EURUSD, NZDUSD) and unknown symbols return None."""
    assert find_class_for_instrument("GBPUSD", sprt_config) is None
    assert find_class_for_instrument("EURUSD", sprt_config) is None
    assert find_class_for_instrument("NZDUSD", sprt_config) is None
    assert find_class_for_instrument("UNKNOWN", sprt_config) is None


def test_find_class_empty_config_returns_none():
    assert find_class_for_instrument("XAUUSD", {}) is None
    assert find_class_for_instrument("XAUUSD", None) is None


# --------------------------------------------------------------------------
# check() — happy path verdicts per class
# --------------------------------------------------------------------------


def test_xauusd_metals_ok(sprt_config):
    """LONG_n=20, wins=12 (60%) -> OK (above metals halt 55%)."""
    result = check("XAUUSD", LONG_n=20, LONG_wins=12, config=sprt_config)
    assert result.verdict == "OK"
    assert result.class_name == "metals"
    assert result.actual_wr == pytest.approx(60.0)
    assert result.n == 20
    assert "OK" in result.message
    assert "XAUUSD" in result.message
    assert "metals" in result.message


def test_xauusd_metals_halt_triggered(sprt_config):
    """LONG_n=20, wins=10 (50%) -> HALT_TRIGGERED (below metals halt 55%)."""
    result = check("XAUUSD", LONG_n=20, LONG_wins=10, config=sprt_config)
    assert result.verdict == "HALT_TRIGGERED"
    assert result.class_name == "metals"
    assert result.threshold_breached == pytest.approx(55.0)
    assert result.actual_wr == pytest.approx(50.0)
    assert result.n == 20
    assert "HALT" in result.message
    assert "XAUUSD" in result.message
    assert "metals" in result.message


def test_xauusd_metals_early_warning(sprt_config):
    """LONG_n=15, wins=7 (~46.7%) -> EARLY_WARNING (below 50%, but n<20)."""
    result = check("XAUUSD", LONG_n=15, LONG_wins=7, config=sprt_config)
    assert result.verdict == "EARLY_WARNING"
    assert result.class_name == "metals"
    assert result.threshold_breached == pytest.approx(50.0)
    assert result.actual_wr == pytest.approx(46.666666, abs=1e-3)
    assert result.n == 15
    assert "EARLY WARNING" in result.message
    assert "XAUUSD" in result.message


def test_xauusd_metals_borderline_halt_at_20(sprt_config):
    """At exactly trigger_n=20, just-below-halt fires HALT_TRIGGERED."""
    # 54.99% < 55% -> halt
    result = check("XAUUSD", LONG_n=100, LONG_wins=54, config=sprt_config)
    assert result.verdict == "HALT_TRIGGERED"
    # 55.0% == halt threshold -> NOT halt (strict <)
    result = check("XAUUSD", LONG_n=100, LONG_wins=55, config=sprt_config)
    assert result.verdict == "OK"


def test_us30_indices_halt_triggered(sprt_config):
    """LONG_n=20, wins=7 (35%) -> HALT_TRIGGERED (below indices halt 40%)."""
    result = check("US30", LONG_n=20, LONG_wins=7, config=sprt_config)
    assert result.verdict == "HALT_TRIGGERED"
    assert result.class_name == "indices"
    assert result.threshold_breached == pytest.approx(40.0)
    assert result.actual_wr == pytest.approx(35.0)
    assert "HALT" in result.message


def test_nas100_indices_early_warning(sprt_config):
    """NAS100 LONG_n=12, wins=4 (~33%) -> EARLY_WARNING (below 35%)."""
    result = check("NAS100", LONG_n=12, LONG_wins=4, config=sprt_config)
    assert result.verdict == "EARLY_WARNING"
    assert result.class_name == "indices"
    assert result.threshold_breached == pytest.approx(35.0)


def test_usdjpy_jpy_halt_triggered(sprt_config):
    """LONG_n=20, wins=8 (40%) -> HALT_TRIGGERED (below jpy halt 45%)."""
    result = check("USDJPY", LONG_n=20, LONG_wins=8, config=sprt_config)
    assert result.verdict == "HALT_TRIGGERED"
    assert result.class_name == "jpy_pairs"
    assert result.threshold_breached == pytest.approx(45.0)
    assert result.actual_wr == pytest.approx(40.0)


def test_gbpjpy_jpy_ok(sprt_config):
    """LONG_n=20, wins=10 (50%) -> OK (above jpy halt 45%)."""
    result = check("GBPJPY", LONG_n=20, LONG_wins=10, config=sprt_config)
    assert result.verdict == "OK"
    assert result.class_name == "jpy_pairs"


# --------------------------------------------------------------------------
# Class exclusion + sample-size sentinels
# --------------------------------------------------------------------------


def test_eurusd_class_excluded(sprt_config):
    """EURUSD not in any class -> CLASS_EXCLUDED (no halt)."""
    result = check("EURUSD", LONG_n=20, LONG_wins=5, config=sprt_config)
    assert result.verdict == "CLASS_EXCLUDED"
    assert result.class_name is None
    assert result.threshold_breached is None
    assert result.actual_wr is None
    assert "not in any class" in result.message
    assert "EURUSD" in result.message


def test_gbpusd_class_excluded(sprt_config):
    """GBPUSD observer-only + tight-FX excluded -> CLASS_EXCLUDED."""
    result = check("GBPUSD", LONG_n=20, LONG_wins=5, config=sprt_config)
    assert result.verdict == "CLASS_EXCLUDED"
    assert result.class_name is None
    assert "GBPUSD" in result.message


def test_unknown_instrument_class_excluded(sprt_config):
    """An unknown ticker is treated identically to tight-FX excluded."""
    result = check("MADEUP", LONG_n=20, LONG_wins=10, config=sprt_config)
    assert result.verdict == "CLASS_EXCLUDED"
    assert result.class_name is None


def test_insufficient_data_below_early_n(sprt_config):
    """LONG_n=5 < early_warning_n=10 -> INSUFFICIENT_DATA."""
    result = check("XAUUSD", LONG_n=5, LONG_wins=1, config=sprt_config)
    assert result.verdict == "INSUFFICIENT_DATA"
    assert result.class_name == "metals"
    assert result.threshold_breached is None
    assert result.actual_wr is None
    assert result.n == 5
    assert "INSUFFICIENT" in result.message.upper() or "samples" in result.message


def test_insufficient_data_zero_samples(sprt_config):
    """LONG_n=0 -> INSUFFICIENT_DATA with no division-by-zero."""
    result = check("XAUUSD", LONG_n=0, LONG_wins=0, config=sprt_config)
    assert result.verdict == "INSUFFICIENT_DATA"
    assert result.actual_wr is None


def test_at_exact_early_warning_n_evaluated(sprt_config):
    """LONG_n == early_warning_n=10 evaluates (does not fall through to INSUFFICIENT_DATA)."""
    # 4 wins / 10 = 40% < 50% early -> EARLY_WARNING
    result = check("XAUUSD", LONG_n=10, LONG_wins=4, config=sprt_config)
    assert result.verdict == "EARLY_WARNING"
    # 6 wins / 10 = 60% > 50% early -> OK
    result = check("XAUUSD", LONG_n=10, LONG_wins=6, config=sprt_config)
    assert result.verdict == "OK"


def test_below_trigger_n_no_halt_but_warning(sprt_config):
    """For 10 <= n < 20, only EARLY_WARNING can fire — no HALT until n=20."""
    # 10% WR is far below the 55% halt; n=15 is below trigger_n=20 -> EARLY only.
    result = check("XAUUSD", LONG_n=15, LONG_wins=1, config=sprt_config)
    assert result.verdict == "EARLY_WARNING"
    assert result.threshold_breached == pytest.approx(50.0)


# --------------------------------------------------------------------------
# Master switch
# --------------------------------------------------------------------------


def test_disabled_in_config(sprt_config):
    """sprt_halt.enabled=false -> OK with disabled message regardless of n/wins."""
    sprt_config["sprt_halt"]["enabled"] = False
    result = check("XAUUSD", LONG_n=20, LONG_wins=0, config=sprt_config)
    assert result.verdict == "OK"
    assert result.class_name is None
    assert result.threshold_breached is None
    assert "disabled" in result.message.lower()


def test_missing_sprt_halt_block():
    """Empty config (no sprt_halt block) -> OK with disabled message."""
    result = check("XAUUSD", LONG_n=20, LONG_wins=0, config={})
    assert result.verdict == "OK"
    assert "disabled" in result.message.lower()


# --------------------------------------------------------------------------
# Input validation
# --------------------------------------------------------------------------


def test_negative_n_raises(sprt_config):
    with pytest.raises(ValueError, match="LONG_n must be"):
        check("XAUUSD", LONG_n=-1, LONG_wins=0, config=sprt_config)


def test_wins_exceed_n_raises(sprt_config):
    with pytest.raises(ValueError, match="LONG_wins must be in"):
        check("XAUUSD", LONG_n=10, LONG_wins=11, config=sprt_config)


def test_negative_wins_raises(sprt_config):
    with pytest.raises(ValueError, match="LONG_wins must be in"):
        check("XAUUSD", LONG_n=10, LONG_wins=-1, config=sprt_config)


# --------------------------------------------------------------------------
# Production config smoke tests — verify the on-disk config matches the
# in-memory test fixture so the two sources can never silently drift.
# --------------------------------------------------------------------------


def test_production_config_has_sprt_halt_block(config):
    """config/agent_config.yaml has the sprt_halt block as shipped."""
    assert "sprt_halt" in config
    sprt = config["sprt_halt"]
    assert sprt.get("enabled") is True
    assert sprt.get("automation_enabled") is True
    assert sprt.get("trigger_n") == 20
    assert sprt.get("early_warning_n") == 10
    per_class = sprt.get("per_class_thresholds", {})
    assert set(per_class.keys()) == {"metals", "indices", "jpy_pairs"}


def test_production_config_metals_thresholds(config):
    metals = config["sprt_halt"]["per_class_thresholds"]["metals"]
    assert metals["halt_wr_pct"] == 55.0
    assert metals["early_warning_wr_pct"] == 50.0
    assert "XAUUSD" in metals["instruments"]
    assert "XAGUSD" in metals["instruments"]


def test_production_config_indices_thresholds(config):
    indices = config["sprt_halt"]["per_class_thresholds"]["indices"]
    assert indices["halt_wr_pct"] == 40.0
    assert indices["early_warning_wr_pct"] == 35.0
    # Both US30 and US30_cash variants supported (FTMO uses US30_cash MT5 symbol).
    assert "US30_cash" in indices["instruments"]
    assert "NAS100" in indices["instruments"]


def test_production_config_jpy_thresholds(config):
    jpy = config["sprt_halt"]["per_class_thresholds"]["jpy_pairs"]
    assert jpy["halt_wr_pct"] == 45.0
    assert jpy["early_warning_wr_pct"] == 40.0
    assert "USDJPY" in jpy["instruments"]
    assert "GBPJPY" in jpy["instruments"]


def test_production_config_tight_fx_excluded(config):
    """GBPUSD and EURUSD must NOT appear in any class."""
    all_instruments: list = []
    for cls_data in config["sprt_halt"]["per_class_thresholds"].values():
        all_instruments.extend(cls_data.get("instruments", []))
    assert "GBPUSD" not in all_instruments
    assert "EURUSD" not in all_instruments
    assert "NZDUSD" not in all_instruments


def test_production_config_smoke_via_check(config):
    """End-to-end smoke: run check() with the on-disk config for each instrument."""
    # Metals halt
    r = check("XAUUSD", LONG_n=20, LONG_wins=10, config=config)
    assert r.verdict == "HALT_TRIGGERED"
    assert r.class_name == "metals"
    # Indices OK
    r = check("US30_cash", LONG_n=20, LONG_wins=12, config=config)
    assert r.verdict == "OK"
    assert r.class_name == "indices"
    # JPY early warning
    r = check("USDJPY", LONG_n=15, LONG_wins=5, config=config)  # 33%
    assert r.verdict == "EARLY_WARNING"
    assert r.class_name == "jpy_pairs"
    # GBPUSD excluded
    r = check("GBPUSD", LONG_n=20, LONG_wins=5, config=config)
    assert r.verdict == "CLASS_EXCLUDED"


# --------------------------------------------------------------------------
# Telegram alert template (Component 4)
# --------------------------------------------------------------------------


def test_telegram_alert_halt_triggered(sprt_config):
    from src.components.sprt_halt_alert_template import format_telegram_alert

    result = check("XAUUSD", LONG_n=20, LONG_wins=10, config=sprt_config)
    msg = format_telegram_alert(result)
    assert "HALT" in msg
    assert "XAUUSD" in msg
    assert "metals" in msg
    assert "50.0%" in msg
    assert "55.0%" in msg
    assert "ACTION" in msg


def test_telegram_alert_early_warning(sprt_config):
    from src.components.sprt_halt_alert_template import format_telegram_alert

    result = check("USDJPY", LONG_n=12, LONG_wins=4, config=sprt_config)
    msg = format_telegram_alert(result)
    assert "EARLY WARNING" in msg
    assert "USDJPY" in msg
    assert "jpy_pairs" in msg
    assert "ACTION" in msg


def test_telegram_alert_ok(sprt_config):
    from src.components.sprt_halt_alert_template import format_telegram_alert

    result = check("XAUUSD", LONG_n=20, LONG_wins=14, config=sprt_config)
    msg = format_telegram_alert(result)
    assert "OK" in msg
    assert "XAUUSD" in msg
    # No ACTION line for OK
    assert "ACTION" not in msg


def test_telegram_alert_class_excluded(sprt_config):
    from src.components.sprt_halt_alert_template import format_telegram_alert

    result = check("EURUSD", LONG_n=20, LONG_wins=5, config=sprt_config)
    msg = format_telegram_alert(result)
    assert "CLASS EXCLUDED" in msg
    assert "EURUSD" in msg


def test_telegram_alert_insufficient_data(sprt_config):
    from src.components.sprt_halt_alert_template import format_telegram_alert

    result = check("XAUUSD", LONG_n=5, LONG_wins=1, config=sprt_config)
    msg = format_telegram_alert(result)
    assert "INSUFFICIENT" in msg.upper()
    assert "XAUUSD" in msg


# --------------------------------------------------------------------------
# H7 (2026-04-26): dispatch_alert routes through persistent queue
# --------------------------------------------------------------------------


def test_dispatch_alert_halt_triggered_routes_critical(tmp_path, sprt_config):
    """HALT_TRIGGERED → CRITICAL via persistent notification queue.

    Asserts on the in-memory ``sent`` capture (transport called) plus
    pending state, not on the on-disk queue file. A daemon-thread
    compaction race between enqueue and assert can wipe pending rows
    from disk; the canonical source of truth is the transport call list.
    """
    from src.components.sprt_halt_alert_template import dispatch_alert
    from src.utils import notification_queue
    from src.utils.notification_queue import Level, PersistentNotificationQueue

    sent = []
    notification_queue._reset_singleton_for_tests()
    test_q = PersistentNotificationQueue(
        queue_path=tmp_path / "queue.jsonl",
        transport=lambda m: sent.append(m) or True,
    )
    notification_queue._SINGLETON = test_q

    result = check("XAUUSD", LONG_n=20, LONG_wins=10, config=sprt_config)
    text = dispatch_alert(result)
    test_q.flush()
    test_q.stop()

    # Returned text matches what format_telegram_alert produces.
    assert "HALT" in text and "XAUUSD" in text
    # Alert was delivered via the transport.
    assert len(sent) == 1
    assert "HALT" in sent[0]

    notification_queue._reset_singleton_for_tests()


def test_dispatch_alert_early_warning_routes_high(tmp_path, sprt_config):
    """EARLY_WARNING → HIGH (5-retry exponential backoff)."""
    from src.components.sprt_halt_alert_template import dispatch_alert
    from src.utils import notification_queue
    from src.utils.notification_queue import PersistentNotificationQueue

    sent = []
    notification_queue._reset_singleton_for_tests()
    test_q = PersistentNotificationQueue(
        queue_path=tmp_path / "queue.jsonl",
        transport=lambda m: sent.append(m) or True,
    )
    notification_queue._SINGLETON = test_q

    result = check("USDJPY", LONG_n=12, LONG_wins=4, config=sprt_config)
    text = dispatch_alert(result)
    test_q.flush()
    test_q.stop()

    assert "EARLY WARNING" in text
    assert len(sent) == 1
    assert "EARLY WARNING" in sent[0]

    notification_queue._reset_singleton_for_tests()


def test_dispatch_alert_ok_does_not_enqueue(tmp_path, sprt_config):
    """OK / INSUFFICIENT_DATA / CLASS_EXCLUDED → no enqueue, just return text."""
    from src.components.sprt_halt_alert_template import dispatch_alert
    from src.utils import notification_queue
    from src.utils.notification_queue import PersistentNotificationQueue

    sent = []
    notification_queue._reset_singleton_for_tests()
    test_q = PersistentNotificationQueue(
        queue_path=tmp_path / "queue.jsonl",
        transport=lambda m: sent.append(m) or True,
    )
    notification_queue._SINGLETON = test_q

    for verdict_inputs in (
        ("XAUUSD", 20, 14),  # OK
        ("XAUUSD", 5, 1),     # INSUFFICIENT_DATA
        ("EURUSD", 20, 5),    # CLASS_EXCLUDED
    ):
        sym, n, wins = verdict_inputs
        result = check(sym, LONG_n=n, LONG_wins=wins, config=sprt_config)
        text = dispatch_alert(result)
        assert text  # text returned regardless

    test_q.flush()
    test_q.stop()

    # No alerts ever delivered through the queue transport.
    assert sent == []
    # Queue's pending state is empty too.
    assert test_q.pending_count() == 0

    notification_queue._reset_singleton_for_tests()
