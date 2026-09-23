"""GOLIVE_vps — tests for the DUAL-MT5 adapter (FTMO-primary / redacted_account-follower).

NO broker. NO orders. NO network. Every transport is a fake in-memory adapter or the
default NullBridgeAdapter; the SiliconBridgeAdapter is never connected. Covers:
  - default-off / fail-closed / import side-effect-free
  - role invariants (FTMO primary, redacted_account follower)
  - per-broker symbol/spec translation incl. suffixes (.cash/.c) + missing-symbol skip
  - UTC clock offset check (fail-closed on no time / out-of-tolerance)
  - follower isolation: missing-symbol / large-slip / reject / not-connected / exception
    skip the follower leg, NEVER the primary
  - primary-vs-follower parity ledger + divergence summary
  - startup self-check (no connect / no order)

Run:
  python3 -m pytest GOLIVE_vps_deploy/tests/test_dual_mt5_adapter.py -q
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_PKG = _HERE.parents[1]                     # GOLIVE_vps_deploy/
sys.path.insert(0, str(_PKG / "adapters"))

import bridge_adapter as B          # noqa: E402
import dual_mt5_adapter as D        # noqa: E402


# --------------------------------------------------------------------------- #
# Fake in-memory single-terminal transport (NO broker). Implements BridgeAdapter.
# --------------------------------------------------------------------------- #
class FakeTerminal(B.BridgeAdapter):
    def __init__(self, config, *, connected=True, tick_time=None,
                 fill_price=100.0, reject=False, raise_on_send=False, equity=100000.0):
        super().__init__(config)
        self._connected = connected
        self._tick_time = tick_time
        self._fill_price = fill_price
        self._reject = reject
        self._raise_on_send = raise_on_send
        self._equity = equity
        self.sent: list[dict] = []

    def connect(self):
        return self._connected

    def disconnect(self):
        self._connected = False

    def get_tick(self, symbol):
        if not self._connected or self._tick_time is None:
            return None
        return B.TickData(bid=self._fill_price - 0.1, ask=self._fill_price + 0.1,
                          time=self._tick_time, spread_cents=20.0)

    def get_positions(self, symbol=None):
        return []

    def get_account_equity(self):
        return self._equity

    def get_account_balance(self):
        return self._equity

    def order_send(self, request):
        self.sent.append(request)
        if self._raise_on_send:
            raise RuntimeError("simulated transport blowup")
        if self._reject:
            return B.OrderResult(retcode=10004, order=0, volume=0.0, price=0.0,
                                 comment="requote/rejected")
        return B.OrderResult(retcode=10009, order=999, volume=request.get("volume", 1.0),
                             price=self._fill_price, comment="done")

    def get_history_deals(self, from_date, to_date, symbol=None):
        return []


def _dual(primary_kwargs=None, follower_kwargs=None, **adapter_kwargs):
    """Build a DualMT5Adapter with FakeTerminals swapped in (no broker)."""
    cfg = D.DualMT5Config()
    a = D.DualMT5Adapter(cfg, **adapter_kwargs)
    a.primary = FakeTerminal(cfg.primary.bridge, **(primary_kwargs or {}))
    a.follower = FakeTerminal(cfg.follower.bridge, **(follower_kwargs or {}))
    return a, cfg


# --------------------------------------------------------------------------- #
# import / default-off
# --------------------------------------------------------------------------- #
def test_import_is_side_effect_free():
    assert "nmetatrader5" not in sys.modules
    assert "MetaTrader5" not in sys.modules


def test_default_factory_is_default_off_null_terminals():
    a = D.make_dual_mt5_adapter()
    assert isinstance(a.primary, B.NullBridgeAdapter)
    assert isinstance(a.follower, B.NullBridgeAdapter)
    status = a.connect()
    assert status["live"] is False
    assert status["primary"]["connected"] is False
    assert status["follower"]["connected"] is False


def test_default_off_execute_decision_places_nothing():
    a = D.make_dual_mt5_adapter()
    a.connect()
    res = a.execute_decision(intent_id="i1", canonical_symbol="XAUUSD",
                             primary_request={"symbol": "XAUUSD", "volume": 1.0})
    # NullBridgeAdapter order_send is fail-closed -> primary not filled, follower not mirrored
    assert res.primary_executed is False
    assert res.follower.mirrored is False


# --------------------------------------------------------------------------- #
# role invariants
# --------------------------------------------------------------------------- #
def test_role_invariant_rejects_swapped_roles():
    bad_primary = D.TerminalConfig(role=D.BrokerRole.FOLLOWER,
                                   bridge=B.BridgeConfig(), symbol_map=D.FTMO_SYMBOL_MAP)
    with pytest.raises(ValueError):
        D.DualMT5Config(primary=bad_primary)


def test_default_config_is_ftmo_primary_redacted_account_follower():
    cfg = D.DualMT5Config()
    assert cfg.primary.broker == "ftmo"
    assert cfg.primary.role == D.BrokerRole.PRIMARY
    assert cfg.follower.broker == "redacted_account"
    assert cfg.follower.role == D.BrokerRole.FOLLOWER


def test_terminals_use_separate_env_var_names():
    cfg = D.DualMT5Config()
    assert cfg.primary.bridge.env_login != cfg.follower.bridge.env_login
    assert "FTMO" in cfg.primary.bridge.env_login
    assert "redacted_account" in cfg.follower.bridge.env_login


# --------------------------------------------------------------------------- #
# symbol / spec translation (suffix hazards + missing-symbol)
# --------------------------------------------------------------------------- #
def test_follower_name_translation():
    a, _ = _dual()
    spec, reason = a.translate_to_follower("USOIL_cash")
    assert reason is None
    # live-verified 2026-06-14: redacted_account names WTI "USOUSD" (FTMO uses "USOIL.cash").
    assert spec.broker_symbol == "USOUSD"


def test_follower_missing_symbol_is_skip_reason():
    a, _ = _dual()
    # NZDUSD is not a carrier in redacted_account_SYMBOL_MAP -> missing-symbol skip path.
    spec, reason = a.translate_to_follower("NZDUSD")
    assert spec is None
    assert reason == "follower_missing_symbol"


def test_unverified_floor_above_wall_skips_follower():
    # canonical floor lookup returns a value >= untradeable wall -> skip (re-measure required)
    a, _ = _dual(canonical_floor_lookup=lambda s: 0.99)
    spec, reason = a.translate_to_follower("XAUUSD")   # FN floor None -> fallback lookup
    assert spec is None
    assert reason == "follower_symbol_untradeable"


def test_symbol_coverage_reflects_ftmo_only_symbols():
    a, _ = _dual()
    cov = a.symbol_coverage()
    # FTMO carries all 27; redacted_account lacks metals crosses / DASH / agri (live-verified
    # 2026-06-14) -> those 7 follower legs SKIP (missing-symbol, isolated). 20/27 mirrorable.
    ftmo_only = {"XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD", "DASHUSD", "CORN_c", "COTTON_c"}
    assert set(cov["follower_skipped"]) == ftmo_only
    assert all(r == "follower_missing_symbol" for r in cov["follower_skipped"].values())
    assert len(cov["follower_mirrorable"]) == 20
    assert "XAUUSD" in cov["follower_mirrorable"] and "GBPJPY" in cov["follower_mirrorable"]
    assert cov["coverage_ratio"] == round(20 / 27, 4)


def test_follower_volume_rescale_index_down():
    # FTMO index contract 1, FN contract 10 -> follower lots = primary x 0.1 (never over-risk)
    a, _ = _dual()
    assert a.follower_volume_for("US30_cash", 1.0) == 0.1
    assert a.follower_volume_for("NAS100", 2.0) == 0.2
    assert a.follower_volume_for("EU50_cash", 1.0) == 0.1


def test_follower_volume_rescale_eth_up():
    # FTMO ETHUSD contract 10, FN contract 1 -> follower lots = primary x 10
    a, _ = _dual()
    assert a.follower_volume_for("ETHUSD", 1.0) == 10.0


def test_follower_volume_one_to_one_carriers_unchanged():
    a, _ = _dual()
    assert a.follower_volume_for("XAUUSD", 1.0) == 1.0
    assert a.follower_volume_for("USDJPY", 0.5) == 0.5
    assert a.follower_volume_for("USOIL_cash", 0.3) == 0.3


def test_follower_volume_below_min_lot_returns_none():
    # index x0.1: a 0.05-lot primary -> 0.005 < 0.01 follower min -> skip (None), never over-risk
    a, _ = _dual()
    assert a.follower_volume_for("US30_cash", 0.05) is None


def test_execute_rescales_follower_index_volume():
    a, _ = _dual(primary_kwargs={"fill_price": 50000.0}, follower_kwargs={"fill_price": 50000.0})
    res = a.execute_decision(
        intent_id="t", canonical_symbol="US30_cash",
        primary_request={"symbol": "US30.cash", "volume": 1.0, "stop_dist_price": 100.0})
    assert res.primary_executed is True
    assert res.follower.mirrored is True
    assert res.follower.order_result.volume == 0.1   # follower lot rescaled x0.1 (notional parity)


# --------------------------------------------------------------------------- #
# clock / UTC normalization (chronological safety)
# --------------------------------------------------------------------------- #
def test_clock_offset_safe_within_tolerance():
    ref = datetime(2026, 6, 15, 0, 0, 0, tzinfo=timezone.utc)
    chk = D.evaluate_clock_offset(broker="ftmo", role="primary",
                                  terminal_time=ref + timedelta(seconds=1), reference_utc=ref)
    assert chk.safe is True
    assert abs(chk.offset_seconds - 1.0) < 1e-6


def test_clock_offset_unsafe_beyond_tolerance():
    ref = datetime(2026, 6, 15, 0, 0, 0, tzinfo=timezone.utc)
    chk = D.evaluate_clock_offset(broker="redacted_account", role="follower",
                                  terminal_time=ref + timedelta(seconds=120), reference_utc=ref)
    assert chk.safe is False
    assert "exceeds_tol" in chk.reason


def test_clock_no_time_fails_closed():
    chk = D.evaluate_clock_offset(broker="ftmo", role="primary", terminal_time=None)
    assert chk.safe is False
    assert chk.reason == "no_terminal_time_fail_closed"


def test_check_clocks_primary_gates_system_follower_isolated():
    ref = datetime(2026, 6, 15, 0, 0, 0, tzinfo=timezone.utc)
    # primary clock fine, follower badly skewed
    a, _ = _dual(primary_kwargs={"tick_time": ref},
                 follower_kwargs={"tick_time": ref + timedelta(seconds=300)})
    out = a.check_clocks(reference_utc=ref)
    assert out["system_clock_safe"] is True       # primary safe -> system safe
    assert out["follower_clock_safe"] is False     # follower skew is isolated


# --------------------------------------------------------------------------- #
# follower isolation — every failure mode skips the follower, never the primary
# --------------------------------------------------------------------------- #
def _exec(a, canonical="XAUUSD"):
    return a.execute_decision(
        intent_id="t", canonical_symbol=canonical,
        primary_request={"symbol": "XAUUSD", "volume": 1.0, "stop_dist_price": 10.0})


def test_happy_path_both_legs_fill():
    a, _ = _dual(primary_kwargs={"fill_price": 2000.0},
                 follower_kwargs={"fill_price": 2000.0})
    res = _exec(a)
    assert res.primary_executed is True
    assert res.follower.mirrored is True
    assert res.follower.broker_symbol == "XAUUSD"
    assert res.parity.diverged is False


def test_follower_missing_symbol_skips_follower_primary_unaffected():
    a, _ = _dual()
    res = _exec(a, canonical="NZDUSD")   # not a carrier on FN map; primary request still XAUUSD-shaped
    assert res.primary_executed is True            # PRIMARY STILL EXECUTES
    assert res.follower.mirrored is False
    assert res.follower.skip_reason == "follower_missing_symbol"
    assert res.parity.diverged is True


def test_follower_reject_skips_follower_primary_unaffected():
    a, _ = _dual(follower_kwargs={"reject": True})
    res = _exec(a)
    assert res.primary_executed is True
    assert res.follower.mirrored is False
    assert res.follower.skip_reason == "follower_order_rejected"


def test_follower_transport_exception_is_contained():
    a, _ = _dual(follower_kwargs={"raise_on_send": True})
    res = _exec(a)
    assert res.primary_executed is True            # primary unaffected by follower blowup
    assert res.follower.mirrored is False
    assert res.follower.skip_reason == "follower_order_rejected"


def test_follower_large_slippage_skips_follower():
    # follower fills 50 price units away on a 10-unit stop => 5R slip >> 0.10R max
    a, _ = _dual(primary_kwargs={"fill_price": 2000.0},
                 follower_kwargs={"fill_price": 2050.0})
    res = _exec(a)
    assert res.primary_executed is True
    assert res.follower.mirrored is False
    assert res.follower.skip_reason == "follower_large_slippage"


def test_follower_not_connected_skips_follower():
    a, _ = _dual(follower_kwargs={"connected": False})
    res = _exec(a)
    assert res.primary_executed is True
    assert res.follower.mirrored is False
    assert res.follower.skip_reason == "follower_not_connected"


def test_primary_not_filled_mirrors_nothing():
    a, _ = _dual(primary_kwargs={"reject": True})
    res = _exec(a)
    assert res.primary_executed is False
    assert res.follower.mirrored is False
    assert res.follower.skip_reason is None         # nothing to mirror, not a divergence
    assert res.parity.diverged is False


# --------------------------------------------------------------------------- #
# parity ledger
# --------------------------------------------------------------------------- #
def test_parity_sink_receives_records():
    # an EXTERNAL sink (owner wires monitor.record_parity at go-live) gets every record.
    captured: list[D.ParityLegRecord] = []
    a, _ = _dual(parity_sink=captured.append,
                 primary_kwargs={"fill_price": 2000.0}, follower_kwargs={"fill_price": 2000.0})
    _exec(a)
    assert len(captured) == 1
    assert captured[0].primary_filled is True and captured[0].follower_filled is True


def test_parity_summary_over_default_in_memory_sink():
    # with the DEFAULT (in-memory) sink, parity_summary aggregates the records.
    a, _ = _dual(primary_kwargs={"fill_price": 2000.0}, follower_kwargs={"fill_price": 2000.0})
    _exec(a)
    s = a.parity_summary()
    assert s["n_decisions"] == 1
    assert s["n_primary_filled"] == 1
    assert s["n_follower_filled"] == 1
    assert s["n_diverged"] == 0


def test_parity_summary_counts_divergence_reasons():
    a, _ = _dual()
    _exec(a, canonical="NZDUSD")    # not a carrier on FN map -> diverged
    s = a.parity_summary()
    assert s["n_diverged"] == 1
    assert s["divergence_reasons"].get("follower_missing_symbol") == 1


def test_parity_sink_failure_does_not_break_execution():
    def boom(_): raise RuntimeError("sink down")
    a, _ = _dual(parity_sink=boom,
                 primary_kwargs={"fill_price": 2000.0}, follower_kwargs={"fill_price": 2000.0})
    res = _exec(a)   # must not raise
    assert res.primary_executed is True
    # the in-memory fallback still kept the record
    assert len(a.parity_records) == 1


# --------------------------------------------------------------------------- #
# startup self-check (no connect / no order)
# --------------------------------------------------------------------------- #
def test_startup_self_check_default_off_is_clean_not_broken():
    a = D.make_dual_mt5_adapter()
    rep = a.startup_self_check()
    assert rep["default_off_primary_connected"] is False
    assert rep["roles_ok_ftmo_primary_redacted_account_follower"] is True
    # default-off (not connected) is a legitimate ready-to-enable-pending state
    assert rep["ready_to_enable"] is True
    assert rep["symbol_coverage"]["coverage_ratio"] > 0


def test_startup_self_check_blocks_on_primary_clock_skew():
    ref = datetime(2026, 6, 15, 0, 0, 0, tzinfo=timezone.utc)
    a, _ = _dual(primary_kwargs={"tick_time": ref + timedelta(seconds=999)},
                 follower_kwargs={"tick_time": ref})
    rep = a.startup_self_check(reference_utc=ref)
    assert rep["clocks"]["system_clock_safe"] is False
    assert rep["ready_to_enable"] is False     # primary connected + clock unsafe -> blocked


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
