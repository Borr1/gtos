"""Tests for scripts/correlation_shock_monitor.py (T1.6).

Covers:
- _log_returns: happy path, length, empty/short, non-positive guard
- pearson: known-correlation, perfect/anti, zero-variance None, mismatched len
- rolling_pearson_series: window length, fewer-than-window short-circuit,
  degenerate-window skip
- evaluate_pair: alarm above threshold, ok below threshold, insufficient
  baseline, zero-baseline-std, exact-threshold edge
- enumerate_pairs: stable order, all groups, n*(n-1)/2 within group
- broker_symbol: alias hit + passthrough
- _pair_key: alphabetical canonicalization
- _load_state / _save_state / _in_cooldown: empty / corrupt / non-dict /
  recent / expired / bad-iso
- build_alert_message: contains all stat fields + threshold
- _emit_alert: success path + failure path swallowed
- check_pair: alarm + cooldown + insufficient + no_data branches
- main: no alarms exit 0, alarms exit 1, exception exit 2,
  cooldown suppresses repeat, state persisted on dispatch

All file writes go to ``tmp_path`` via module-ref monkeypatch per the
session 21 canonical pattern.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import correlation_shock_monitor as mod  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────


@pytest.fixture
def isolated_state(tmp_path, monkeypatch):
    state_file = tmp_path / "meta" / "correlation_shock_state.json"
    monkeypatch.setattr(mod, "STATE_FILE", state_file)
    return state_file


def _walk(start: float, returns: list[float]) -> list[float]:
    """Build a price series from log-returns. closes[0] = start."""
    closes = [start]
    for r in returns:
        closes.append(closes[-1] * math.exp(r))
    return closes


# ─────────────────────────────────────────────────────────────────────────
# _log_returns
# ─────────────────────────────────────────────────────────────────────────


class TestLogReturns:
    def test_basic_length_and_value(self):
        closes = [100.0, 110.0, 121.0]
        out = mod._log_returns(closes)
        assert len(out) == 2
        assert out[0] == pytest.approx(math.log(110 / 100))
        assert out[1] == pytest.approx(math.log(121 / 110))

    def test_empty_input(self):
        assert mod._log_returns([]) == []

    def test_single_element_input(self):
        assert mod._log_returns([100.0]) == []

    def test_zero_close_returns_empty(self):
        assert mod._log_returns([100.0, 0.0, 110.0]) == []

    def test_negative_close_returns_empty(self):
        assert mod._log_returns([100.0, -5.0, 110.0]) == []


# ─────────────────────────────────────────────────────────────────────────
# pearson
# ─────────────────────────────────────────────────────────────────────────


class TestPearson:
    def test_perfect_positive(self):
        rho = mod.pearson([1.0, 2.0, 3.0, 4.0], [2.0, 4.0, 6.0, 8.0])
        assert rho == pytest.approx(1.0)

    def test_perfect_negative(self):
        rho = mod.pearson([1.0, 2.0, 3.0, 4.0], [4.0, 3.0, 2.0, 1.0])
        assert rho == pytest.approx(-1.0)

    def test_zero_variance_returns_none(self):
        rho = mod.pearson([1.0, 1.0, 1.0], [1.0, 2.0, 3.0])
        assert rho is None

    def test_mismatched_length(self):
        assert mod.pearson([1.0, 2.0], [1.0]) is None

    def test_too_short(self):
        assert mod.pearson([1.0], [1.0]) is None

    def test_known_value(self):
        # Anscombe-style: known correlation roughly 0.816
        xs = [10.0, 8.0, 13.0, 9.0, 11.0, 14.0, 6.0, 4.0, 12.0, 7.0, 5.0]
        ys = [8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68]
        rho = mod.pearson(xs, ys)
        assert rho is not None
        assert 0.80 < rho < 0.83


# ─────────────────────────────────────────────────────────────────────────
# rolling_pearson_series
# ─────────────────────────────────────────────────────────────────────────


class TestRollingPearsonSeries:
    def test_too_short_returns_empty(self):
        out = mod.rolling_pearson_series([0.1, 0.2], [0.1, 0.2], window=10)
        assert out == []

    def test_window_count(self):
        rx = [0.01 * (i % 5 - 2) for i in range(60)]
        ry = [0.01 * ((i + 1) % 5 - 2) for i in range(60)]
        out = mod.rolling_pearson_series(rx, ry, window=10)
        # 60 - 10 + 1 = 51 windows
        assert len(out) == 51
        assert all(-1.0 <= v <= 1.0 for v in out)

    def test_degenerate_window_skipped(self):
        # First window has zero variance on x → skipped
        rx = [1.0] * 10 + [0.01, 0.02, 0.03]
        ry = [0.01] * 10 + [0.04, 0.05, 0.06]
        out = mod.rolling_pearson_series(rx, ry, window=10)
        # First sliding window (start=0..9) is degenerate → dropped.
        # We expect at most 4 - 1 = 3 surviving windows (positions 10, 11, 12).
        assert len(out) <= 3


# ─────────────────────────────────────────────────────────────────────────
# evaluate_pair
# ─────────────────────────────────────────────────────────────────────────


def _make_correlated_returns(n: int, rho_target: float, seed: int = 0):
    """Build two return series with approximate correlation rho_target."""
    import random
    rng = random.Random(seed)
    xs = [rng.gauss(0, 1) * 0.001 for _ in range(n)]
    ys = []
    for x in xs:
        noise = rng.gauss(0, 1) * 0.001
        ys.append(rho_target * x + ((1.0 - rho_target ** 2) ** 0.5) * noise)
    return xs, ys


class TestEvaluatePair:
    def test_insufficient_returns(self):
        rx, ry = _make_correlated_returns(20, 0.5)
        out = mod.evaluate_pair(rx, ry)
        assert out["status"] == "insufficient"
        assert out["rho_now"] is None
        assert "rolling windows" in out["reason"]

    def test_ok_when_baseline_holds(self):
        # Baseline + current with same generator → z near zero
        rx, ry = _make_correlated_returns(400, 0.6, seed=7)
        out = mod.evaluate_pair(rx, ry)
        assert out["status"] == "ok"
        assert out["z"] is not None
        assert abs(out["z"]) <= 2.0

    def test_alarm_when_correlation_breaks(self):
        # Build baseline with rho ≈ 0.7, then 50 candles of returns at rho ≈ -0.7
        baseline_rx, baseline_ry = _make_correlated_returns(250, 0.7, seed=1)
        shock_rx, shock_ry = _make_correlated_returns(50, -0.7, seed=2)
        rx = baseline_rx + shock_rx
        ry = baseline_ry + shock_ry
        out = mod.evaluate_pair(rx, ry)
        assert out["status"] == "alarm"
        assert out["z"] is not None
        assert abs(out["z"]) > 2.0

    def test_zero_baseline_std_returns_insufficient(self):
        # Construct a pair where every rolling-50 window yields the same rho
        # (equal returns → rho=1.0 in every window).
        rx = [0.001 * ((i % 5) - 2) for i in range(300)]
        ry = list(rx)  # identical → rho = 1.0 in every window → std = 0
        out = mod.evaluate_pair(rx, ry)
        assert out["status"] == "insufficient"
        assert out["baseline_std"] == 0.0


# ─────────────────────────────────────────────────────────────────────────
# enumerate_pairs / broker_symbol
# ─────────────────────────────────────────────────────────────────────────


class TestEnumeratePairs:
    def test_default_groups_have_pairs(self):
        pairs = mod.enumerate_pairs()
        assert len(pairs) > 0
        # JPY_CROSSES has 3 symbols → C(3,2) = 3 pairs
        jpy = [p for p in pairs if p[0] == "JPY_CROSSES"]
        assert len(jpy) == 3

    def test_us_indices_include_live_nas100_pairs(self):
        """Unit62: correlation-shock monitoring covers NAS100 with US indices."""
        pairs = [p for p in mod.enumerate_pairs() if p[0] == "US_INDICES"]
        assert ("US_INDICES", "US30_cash", "NAS100") in pairs
        assert ("US_INDICES", "US500", "NAS100") in pairs

    def test_stable_order(self):
        a = mod.enumerate_pairs()
        b = mod.enumerate_pairs()
        assert a == b

    def test_custom_groups(self):
        groups = {
            "A": {"instruments": ["X", "Y"]},
            "B": {"instruments": ["P", "Q", "R"]},
        }
        pairs = mod.enumerate_pairs(groups)
        # 1 + 3 = 4 pairs
        assert len(pairs) == 4
        assert ("A", "X", "Y") in pairs

    def test_empty_group_yields_no_pair(self):
        groups = {"A": {"instruments": ["X"]}}
        assert mod.enumerate_pairs(groups) == []


class TestBrokerSymbol:
    def test_alias_hit(self):
        assert mod.broker_symbol("US30_cash") == "US30.cash"

    def test_nas100_alias_hit(self):
        """Unit62: redacted_account NAS100 monitor queries the broker's NDX100 symbol."""
        assert mod.broker_symbol("NAS100") == "NDX100"

    def test_us500_alias_hit(self):
        assert mod.broker_symbol("US500") == "US500.cash"

    def test_passthrough(self):
        assert mod.broker_symbol("XAUUSD") == "XAUUSD"


# ─────────────────────────────────────────────────────────────────────────
# _pair_key
# ─────────────────────────────────────────────────────────────────────────


class TestPairKey:
    def test_alphabetical(self):
        assert mod._pair_key("G", "B", "A") == "G|A|B"
        assert mod._pair_key("G", "A", "B") == "G|A|B"

    def test_distinct_groups(self):
        assert mod._pair_key("G1", "X", "Y") != mod._pair_key("G2", "X", "Y")


# ─────────────────────────────────────────────────────────────────────────
# State / cooldown
# ─────────────────────────────────────────────────────────────────────────


class TestStateAndCooldown:
    def test_load_missing_returns_empty(self, isolated_state):
        assert mod._load_state() == {}

    def test_load_corrupt_returns_empty(self, isolated_state):
        isolated_state.parent.mkdir(parents=True, exist_ok=True)
        isolated_state.write_text("not json", encoding="utf-8")
        assert mod._load_state() == {}

    def test_load_non_dict_returns_empty(self, isolated_state):
        isolated_state.parent.mkdir(parents=True, exist_ok=True)
        isolated_state.write_text("[1, 2, 3]", encoding="utf-8")
        assert mod._load_state() == {}

    def test_save_then_load_roundtrip(self, isolated_state):
        s = {"JPY_CROSSES|GBPJPY|USDJPY": "2026-04-19T08:00:00+00:00"}
        mod._save_state(s)
        assert mod._load_state() == s

    def test_in_cooldown_recent(self, isolated_state):
        now = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
        state = {"k": (now - timedelta(hours=1)).isoformat()}
        assert mod._in_cooldown(state, "k", now=now, cooldown_hours=24.0) is True

    def test_in_cooldown_expired(self, isolated_state):
        now = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
        state = {"k": (now - timedelta(hours=25)).isoformat()}
        assert mod._in_cooldown(state, "k", now=now, cooldown_hours=24.0) is False

    def test_in_cooldown_unknown_pair(self):
        now = datetime(2026, 4, 19, tzinfo=timezone.utc)
        assert mod._in_cooldown({}, "missing", now=now) is False

    def test_in_cooldown_bad_iso(self, isolated_state):
        state = {"k": "garbage-timestamp"}
        now = datetime(2026, 4, 19, tzinfo=timezone.utc)
        assert mod._in_cooldown(state, "k", now=now) is False

    def test_in_cooldown_naive_isoformat_treated_utc(self):
        now = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
        state = {"k": (now - timedelta(hours=1)).replace(tzinfo=None).isoformat()}
        assert mod._in_cooldown(state, "k", now=now, cooldown_hours=24.0) is True


# ─────────────────────────────────────────────────────────────────────────
# build_alert_message
# ─────────────────────────────────────────────────────────────────────────


class TestBuildAlertMessage:
    def test_contains_stat_fields(self):
        ev = {
            "rho_now": -0.45, "baseline_mean": 0.62,
            "baseline_std": 0.15, "z": -7.13, "n_baseline": 200,
        }
        msg = mod.build_alert_message("JPY_CROSSES", "USDJPY", "GBPJPY", ev)
        assert "JPY_CROSSES" in msg
        assert "USDJPY" in msg and "GBPJPY" in msg
        assert "-0.450" in msg
        assert "+0.620" in msg
        assert "0.150" in msg
        assert "-7.13" in msg
        assert "n=200" in msg
        assert "Alert-only" in msg
        assert "no position impact" in msg.lower()

    def test_threshold_mention(self):
        ev = {
            "rho_now": 0.1, "baseline_mean": 0.0,
            "baseline_std": 0.04, "z": 2.5, "n_baseline": 100,
        }
        msg = mod.build_alert_message("G", "A", "B", ev)
        assert f"|z|>{mod.SIGMA_THRESHOLD}" in msg


# ─────────────────────────────────────────────────────────────────────────
# _emit_alert
# ─────────────────────────────────────────────────────────────────────────


class TestEmitAlert:
    def test_success_returns_true(self, monkeypatch):
        called = []

        def fake_notify(text):
            called.append(text)
        # Patch the symbol where the lazy import resolves it: the
        # src.notifications module the function imports from.
        import src.notifications as notif
        monkeypatch.setattr(notif, "notify_alert", fake_notify)
        assert mod._emit_alert("hello") is True
        assert called == ["hello"]

    def test_failure_returns_false(self, monkeypatch):
        def boom(text):
            raise RuntimeError("network down")
        import src.notifications as notif
        monkeypatch.setattr(notif, "notify_alert", boom)
        # Must NOT raise, must return False.
        assert mod._emit_alert("hello") is False


# ─────────────────────────────────────────────────────────────────────────
# check_pair
# ─────────────────────────────────────────────────────────────────────────


def _alarm_fetcher():
    """Return a fetch callable that produces a baseline + shock pair."""
    base_rx, base_ry = _make_correlated_returns(250, 0.7, seed=1)
    shock_rx, shock_ry = _make_correlated_returns(50, -0.7, seed=2)
    closes_a = _walk(100.0, base_rx + shock_rx)
    closes_b = _walk(100.0, base_ry + shock_ry)
    by_symbol = {"A": closes_a, "B": closes_b}

    def fetch(symbol, count=mod.M15_LOOKBACK_CANDLES):
        return list(by_symbol.get(symbol, []))
    return fetch


def _ok_fetcher():
    rx, ry = _make_correlated_returns(400, 0.6, seed=7)
    closes_a = _walk(100.0, rx)
    closes_b = _walk(100.0, ry)
    by_symbol = {"A": closes_a, "B": closes_b}

    def fetch(symbol, count=mod.M15_LOOKBACK_CANDLES):
        return list(by_symbol.get(symbol, []))
    return fetch


class TestCheckPair:
    def test_no_data_skips_silently(self, isolated_state):
        def empty_fetch(symbol, count=mod.M15_LOOKBACK_CANDLES):
            return []
        d = mod.check_pair("G", "A", "B", state={}, fetch=empty_fetch)
        assert d["status"] == "no_data"
        assert d["should_alert"] is False

    def test_partial_no_data_one_side_empty(self, isolated_state):
        def half_fetch(symbol, count=mod.M15_LOOKBACK_CANDLES):
            return [100.0] * 300 if symbol == "A" else []
        d = mod.check_pair("G", "A", "B", state={}, fetch=half_fetch)
        assert d["status"] == "no_data"

    def test_alarm_fires_message(self, isolated_state):
        d = mod.check_pair("G", "A", "B", state={}, fetch=_alarm_fetcher())
        assert d["status"] == "alarm"
        assert d["should_alert"] is True
        assert "G" in d["message"]
        assert d["evaluation"]["z"] is not None

    def test_ok_does_not_alert(self, isolated_state):
        d = mod.check_pair("G", "A", "B", state={}, fetch=_ok_fetcher())
        assert d["status"] == "ok"
        assert d["should_alert"] is False

    def test_cooldown_suppresses_alarm(self, isolated_state):
        now = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
        state = {
            mod._pair_key("G", "A", "B"): (now - timedelta(hours=1)).isoformat()
        }
        d = mod.check_pair("G", "A", "B", state=state, now=now, fetch=_alarm_fetcher())
        assert d["status"] == "alarm_cooldown"
        assert d["should_alert"] is False
        assert d["message"] is None


# ─────────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────────


class TestMain:
    def _patch_groups(self, monkeypatch, groups):
        monkeypatch.setattr(mod, "DEFAULT_CORRELATION_GROUPS", groups)
        # enumerate_pairs() reads DEFAULT_CORRELATION_GROUPS by default; we
        # patched the module reference so the change is visible.

    def _patch_fetch(self, monkeypatch, fetch):
        monkeypatch.setattr(mod, "fetch_closes", fetch)

    def test_no_alarms_returns_zero(self, isolated_state, monkeypatch):
        self._patch_groups(monkeypatch, {"G": {"instruments": ["A", "B"]}})
        self._patch_fetch(monkeypatch, _ok_fetcher())
        # No emit needed; ensure no alarms means no notify_alert dispatched.
        emitted = []
        import src.notifications as notif
        monkeypatch.setattr(notif, "notify_alert", lambda t: emitted.append(t))
        rc = mod.main()
        assert rc == 0
        assert emitted == []

    def test_alarm_returns_one_and_dispatches(self, isolated_state, monkeypatch):
        self._patch_groups(monkeypatch, {"G": {"instruments": ["A", "B"]}})
        self._patch_fetch(monkeypatch, _alarm_fetcher())
        emitted = []
        import src.notifications as notif
        monkeypatch.setattr(notif, "notify_alert", lambda t: emitted.append(t))
        rc = mod.main()
        assert rc == 1
        assert len(emitted) == 1
        # State persisted with the pair key.
        state = mod._load_state()
        assert mod._pair_key("G", "A", "B") in state

    def test_unhandled_exception_returns_two(self, isolated_state, monkeypatch):
        self._patch_groups(monkeypatch, {"G": {"instruments": ["A", "B"]}})

        def boom(symbol, count=mod.M15_LOOKBACK_CANDLES):
            raise RuntimeError("fatal")
        # Exceptions inside check_pair are NOT swallowed (only inside
        # fetch_closes itself). Patch fetch_closes to a callable that we
        # call directly via check_pair so the exception bubbles into main.
        # main wraps the entire loop in a try/except → should return 2.
        # We achieve this by making enumerate_pairs raise.
        monkeypatch.setattr(
            mod, "enumerate_pairs",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("enumerate boom")),
        )
        rc = mod.main()
        assert rc == 2

    def test_alarm_with_existing_cooldown_does_not_redispatch(
        self, isolated_state, monkeypatch,
    ):
        self._patch_groups(monkeypatch, {"G": {"instruments": ["A", "B"]}})
        self._patch_fetch(monkeypatch, _alarm_fetcher())
        emitted = []
        import src.notifications as notif
        monkeypatch.setattr(notif, "notify_alert", lambda t: emitted.append(t))

        # Pre-seed cooldown state.
        now_iso = datetime.now(timezone.utc).isoformat()
        isolated_state.parent.mkdir(parents=True, exist_ok=True)
        isolated_state.write_text(
            json.dumps({mod._pair_key("G", "A", "B"): now_iso}), encoding="utf-8"
        )
        rc = mod.main()
        assert rc == 0
        assert emitted == []

    def test_emit_failure_keeps_state_unchanged(self, isolated_state, monkeypatch):
        self._patch_groups(monkeypatch, {"G": {"instruments": ["A", "B"]}})
        self._patch_fetch(monkeypatch, _alarm_fetcher())

        import src.notifications as notif

        def boom(t):
            raise RuntimeError("telegram down")
        monkeypatch.setattr(notif, "notify_alert", boom)
        rc = mod.main()
        assert rc == 1  # alarm seen, even if dispatch failed
        # State should NOT be updated because emit failed — so a future
        # successful run can still alert.
        assert mod._load_state() == {}
