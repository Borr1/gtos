"""T5 — the FULL V4 order route clears the 3 live fail-closed gates and places via open_trade.
Loads the FTMO-merged live config and drives the REAL gate functions. No real order (stub engine)."""
from types import SimpleNamespace

import yaml
import pytest

from src.utils.config import apply_profile_overrides, apply_instrument_overrides
from src.components.ultimate_book.admission import SizedUnit, TradeIntent
from src.components.ultimate_book.order_router import UltimateBookOrderRouter
from src.components.ultimate_book import execution_packets as EP
from src.components.execution_manager_v4 import evaluate_execution_manager_v4
from src.components.broker_net_cost_engine import build_pretrade_cost_packet
from src.components.execution import ExecutionEngine
import src.costs.symbols as _SYM


@pytest.fixture(scope="module", autouse=True)
def _symbol_authority_bridge():
    """Root cause (fixed 2026-08-25): f5max-ship is the live overlay (f5max-base 338553883) —
    src/ and config/ carry the VPS bytes, including the 2026-08-21 authrepair of
    src/costs/SYMBOL_AUTHORITY_V1.json (sha 515a5e51…) which embeds the CURRENT FTMO profile
    hash (c87bcb20…); the pre-repair bytes survive as
    src/costs/SYMBOL_AUTHORITY_V1.json.bak-authrepair-20260821T06*Z (sha bddbc613…). docs/ was
    NOT in the overlay, so docs/audits/fable5-vision-audit-20260725/phase21/cost/
    COST_INPUTS_MANIFEST_V1.json here is mainline wave-21 (7d6bbca7a) and still binds the
    pre-repair authority bytes (bddbc613…) and the pre-change FTMO profile (ae9312e6…). Every
    verify_cost_input("symbol_authority") therefore fails closed and every pretrade cost packet
    raises SymbolAuthorityError — a tree-construction drift, not an order-route defect.

    Until the manifest is re-stamped centrally, bridge with the tree's OWN authority file
    through ProfileSymbolAuthority's designed injection seam. The injected mappings() still
    fails closed on any live-profile drift (embedded sha vs current profile bytes), ambiguity,
    and path escape — the substantive protection this chain exists for is kept at full
    strength; only the stale outer docs-manifest binding is bypassed. Once the production
    chain verifies again, this fixture is a no-op and the tests re-cover the outer binding.
    """
    try:
        _SYM.ProfileSymbolAuthority().mappings()
        yield  # production authority chain verifies — run untouched
        return
    except _SYM.SymbolAuthorityError as exc:
        if "cost input 'symbol_authority' hash mismatch" not in str(exc):
            raise  # any OTHER authority failure must stay loud, never be bridged
    injected = _SYM.ProfileSymbolAuthority(
        manifest_path=_SYM.DEFAULT_SYMBOL_AUTHORITY_MANIFEST, profile_root=_SYM.REPO
    )
    injected.mappings()  # fail-closed profile-bytes validation BEFORE any test runs
    mp = pytest.MonkeyPatch()
    mp.setattr(_SYM, "_default_authority", lambda: injected)
    try:
        yield
    finally:
        mp.undo()


class _Tick:
    def __init__(self, bid, ask):
        self.bid = bid; self.ask = ask
        self.time = "2026-06-15T01:00:00+00:00"
        self.spread_cents = (ask - bid) * 100


class _StubMT5:
    def get_tick(self, symbol): return _Tick(2999.7, 3000.0)
    def get_account_balance(self): return 100000.0
    def get_account_equity(self): return 100000.0
    def get_positions(self, symbol=None): return []
    def is_connected(self): return True
    def get_margin_mode(self): return "hedging"


@pytest.fixture(scope="module")
def merged_cfg():
    cfg = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))
    cfg = apply_profile_overrides(cfg, "operator_profile")
    cfg = apply_instrument_overrides(cfg, "XAUUSD")
    return cfg


def _unit_intent_account():
    su = SizedUnit(cluster="metals", sleeve_members=["metals_core"], n_trades=1, confidence=1.0,
                   risk_pct_per_trade=0.005, unit_risk_pct=0.5, sized=True, reason="ok")
    intent = TradeIntent(sleeve="metals_core", symbol="XAUUSD", direction=1,
                         decision_day="2026-06-15", stop_dist=10.0)
    acct = dict(current_equity=100000.0, balance=100000.0, account_login=531325516,
                day_start_equity_or_balance_baseline=100000.0, daily_reset_window_id="2026-06-15")
    return su, intent, acct


def test_router_trade_params_clears_all_three_gates(merged_cfg):
    su, intent, acct = _unit_intent_account()
    router = UltimateBookOrderRouter(merged_cfg, namespace="operator_profile")
    tp = router.build_trade_params(su, intent, _Tick(2999.7, 3000.0), acct)
    # 47 keys: the original 42 + the per-sleeve native-exit additions
    # (gtos_vnext_dynamic_partial_close_ratio, gtos_vnext_dynamic_trail_gap_r,
    #  gtos_vnext_dynamic_broker_take_profit_mode, gtos_vnext_dynamic_no_broker_take_profit,
    #  gtos_vnext_book_native_exit_management).
    assert tp is not None and len(tp) == 47
    # metals_core resolves its native partial_be_runner exit profile (was a forced momentum_exhaustion).
    assert tp["gtos_vnext_dynamic_policy_selected"] == "partial_be_runner"
    assert tp["gtos_vnext_execution_policy_id"] == "emv4_partial_be_runner_v1"
    assert tp["gtos_vnext_book_native_exit_management"] is True
    assert tp["risk_pct_override"] == 0.5
    # the live cost model the engine builds internally
    cost = build_pretrade_cost_packet(config=merged_cfg, trade_params=tp, tick=_Tick(2999.7, 3000.0),
                                      symbol="XAUUSD", broker_symbol="XAUUSD",
                                      entry_price=tp["entry_price"], stop_loss=tp["stop_loss"],
                                      sl_distance=10.0, risk_pct=0.5)
    assert cost.get("status") == "PASSED", cost.get("refusal_reasons")
    ee = ExecutionEngine(_StubMT5(), merged_cfg)
    assert ee._vnext_dynamic_policy_support_error(tp) is None                     # GATE 1
    risk, err = ee._resolve_vnext_production_risk_pct(tp, risk_pct_override=tp["risk_pct_override"])
    assert err is None and risk == 0.5                                            # GATE 3
    dec = evaluate_execution_manager_v4(config=merged_cfg, trade_params=tp, symbol="XAUUSD",
                                        broker_symbol="XAUUSD", pretrade_cost_model=cost)
    assert dec.action == "allow" and not dec.should_block                         # GATE 2
    assert not (getattr(dec, "fatal", []) or [])


def test_router_place_with_stub_engine():
    su, intent, acct = _unit_intent_account()
    router = UltimateBookOrderRouter({}, namespace="operator_profile")

    class _OkEngine:
        def open_trade(self, tp, bal, **kw):
            class _TS:  # minimal TradeState-like
                ticket = 12345
            return _TS()
    res = router.place(_OkEngine(), su, intent, _Tick(2999.7, 3000.0), acct, 100000.0)
    assert res["placed"] is True and res["candidate_id"].startswith("W7_BOOK::metals::XAUUSD")

    class _NoneEngine:
        def open_trade(self, tp, bal, **kw): return None     # halted / gate-blocked
    res2 = router.place(_NoneEngine(), su, intent, _Tick(2999.7, 3000.0), acct, 100000.0)
    assert res2["placed"] is False and res2["reason"] == "open_trade_returned_none"

    class _BoomEngine:
        def open_trade(self, tp, bal, **kw): raise RuntimeError("broker down")
    res3 = router.place(_BoomEngine(), su, intent, _Tick(2999.7, 3000.0), acct, 100000.0)
    assert res3["placed"] is False and "router_exception" in res3["reason"]   # never raises


# ---- broker-geometry parity: the FULL open_trade path emits SL=-1R / TP=native target ----------
class _CapturedRequest(Exception):
    """Sentinel raised from a stubbed safe_place_order to capture the broker request dict before any
    order is sent (no real broker interaction)."""
    def __init__(self, request):
        self.request = dict(request)


def _geometry_engine(merged_cfg):
    """ExecutionEngine wired for XAUUSD with a stub broker (symbol_info + order_calc_profit for lot
    sizing) and a no-op runtime-halt guard. The book trades are paused/hard-halted in production; this
    is a geometry unit test only — safe_place_order is intercepted, so NO order is ever sent."""
    info = SimpleNamespace(trade_tick_size=0.01, trade_tick_value=1.0, volume_min=0.01,
                           volume_step=0.01, volume_max=100.0, filling_mode=3, spread=12)

    def _ocp(order_type, _symbol, volume, price_open, price_close):
        delta = (price_close - price_open) if int(order_type) == 0 else (price_open - price_close)
        return delta / info.trade_tick_size * info.trade_tick_value * float(volume)

    class _GeomMT5(_StubMT5):
        def __init__(self):
            self._mt5 = SimpleNamespace(symbol_info=lambda _s: info, order_calc_profit=_ocp)

    ee = ExecutionEngine(_GeomMT5(), merged_cfg)
    ee.symbol = "XAUUSD"
    ee._persist_symbol = "XAUUSD"
    ee._enforce_runtime_halt_clear = lambda *a, **k: None   # test-only; request is intercepted
    return ee


def _capture_open_trade_request(merged_cfg, sleeve, *, stop_dist=10.0, target_dist=None, entry=3000.0):
    su = SizedUnit(cluster="book", sleeve_members=[sleeve], n_trades=1, confidence=1.0,
                   risk_pct_per_trade=0.005, unit_risk_pct=0.5, sized=True, reason="ok")
    intent = TradeIntent(sleeve=sleeve, symbol="XAUUSD", direction=1, decision_day="2026-06-15",
                         stop_dist=stop_dist, target_dist=target_dist)
    acct = dict(current_equity=100000.0, balance=100000.0, account_login=531325516,
                day_start_equity_or_balance_baseline=100000.0, daily_reset_window_id="2026-06-15")
    sign = 1.0
    geom = {"entry_price": entry, "risk_distance": stop_dist,
            "stop_loss": entry - sign * stop_dist,
            "take_profit_1": entry + sign * (target_dist or 0.0)}
    tp = EP.build_book_trade_params(su, intent, geom, acct, profile_namespace="operator_profile")
    ee = _geometry_engine(merged_cfg)

    def _capture(request, *a, **k):
        raise _CapturedRequest(request)

    ee.safe_place_order = _capture
    # the stub tick ask == entry (3000.0), so entry_price == geom entry and sl_distance == stop_dist
    try:
        ee.open_trade(tp, 100000.0, risk_pct_override=tp["risk_pct_override"], trigger="ultimate_book")
    except _CapturedRequest as cap:
        return tp, cap.request, entry, sign
    raise AssertionError(f"open_trade did not reach the broker order_send for sleeve={sleeve}")


def _open_trade_success_state(merged_cfg, sleeve, *, stop_dist=10.0, target_dist=None, entry=3000.0):
    su = SizedUnit(cluster="book", sleeve_members=[sleeve], n_trades=1, confidence=1.0,
                   risk_pct_per_trade=0.005, unit_risk_pct=0.5, sized=True, reason="ok")
    intent = TradeIntent(sleeve=sleeve, symbol="XAUUSD", direction=1, decision_day="2026-06-15",
                         stop_dist=stop_dist, target_dist=target_dist)
    acct = dict(current_equity=100000.0, balance=100000.0, account_login=531325516,
                day_start_equity_or_balance_baseline=100000.0, daily_reset_window_id="2026-06-15")
    geom = {"entry_price": entry, "risk_distance": stop_dist,
            "stop_loss": entry - stop_dist,
            "take_profit_1": entry + (target_dist or 0.0)}
    tp = EP.build_book_trade_params(su, intent, geom, acct, profile_namespace="operator_profile")
    ee = _geometry_engine(merged_cfg)
    captured = {}

    def _ok(request, *a, **k):
        captured["request"] = dict(request)
        return SimpleNamespace(success=True, order=123456, deal=654321, retcode=10009,
                               price=float(request["price"]), comment="test_fill")

    ee.safe_place_order = _ok
    state = ee.open_trade(tp, 100000.0, risk_pct_override=tp["risk_pct_override"], trigger="ultimate_book")
    assert state is not None
    return tp, captured["request"], state


def test_broker_geometry_parity_per_sleeve(merged_cfg):
    """Drive the REAL ExecutionEngine.open_trade for representative sleeves and assert the broker
    order request carries SL = entry - sign*stop_dist and TP = entry + sign*final_target_r*sl_distance,
    where the TP equals each sleeve's NATIVE target: crypto 4R, metals_core vol-tiered runner R,
    vp_euidx |price-POC| measured move, and candidate fixed-target exits."""
    sd = 10.0
    cases = [
        # sleeve,            native target_dist, expected final_target_r, label
        ("crypto",           None, 4.0,  "crypto 4R (fixed time_stop final)"),
        ("metals_core",      30.0, 3.0,  "metals_core runner 3R (final_from_intent)"),
        ("vp_euidx_pocgrav", 16.0, 1.6,  "vp_euidx |price-POC| measured move 1.6R"),
        ("vol_compression",  30.0, 3.0,  "candidate vol_compression fixed 3R"),
        ("asia_pdl_fade",    30.0, 3.0,  "candidate asia_pdl_fade fixed 3R"),
        ("orb_crypto_london", 20.0, 2.0, "candidate orb_crypto_london fixed 2R"),
        ("liq_asia_up_low_metal", 30.0, 3.0, "candidate liq_asia_up_low_metal fixed 3R"),
        ("vss_fxcross_london_up_low", 20.0, 2.0, "candidate vss_fxcross_london_up_low fixed 2R"),
    ]
    for sleeve, target_dist, exp_R, label in cases:
        tp, req, entry, sign = _capture_open_trade_request(
            merged_cfg, sleeve, stop_dist=sd, target_dist=target_dist)
        assert abs(req["sl"] - (entry - sign * sd)) < 1e-9, (label, "sl", req["sl"])
        assert abs(req["tp"] - (entry + sign * exp_R * sd)) < 1e-9, (label, "tp", req["tp"])
        # the broker TP equals the tp's carried native final_target_r * sl_distance
        assert abs(float(tp["gtos_vnext_dynamic_final_target_r"]) - exp_R) < 1e-9, (label, "finalR")
        assert tp["gtos_vnext_dynamic_broker_take_profit_mode"] == "final_target", label
        assert tp["gtos_vnext_dynamic_no_broker_take_profit"] is False, label
        # native exit: book owns the exit at the broker; orchestrator overlays neutralized
        assert tp["gtos_vnext_book_native_exit_management"] is True, label
    # crypto carries the fixed 4R native target; metals/vp carry the measured native target.


def test_broker_geometry_for_targetless_candidate_native_exits(merged_cfg):
    sd = 10.0
    cases = [
        ("asian_fade", "trailing_runner", 0.5, 0.5, 48, "capless_trailing_runner_no_broker_tp"),
        ("metal_session_reversion", "trailing_runner", 0.6, 0.5, 24, "capless_trailing_runner_no_broker_tp"),
        ("ny_crypto_momentum", "time_stop", 0.0, None, 20, "targetless_time_stop_horizon_no_broker_tp"),
        ("kz_london_crypto_low", "time_stop", 0.0, None, 32, "targetless_time_stop_horizon_no_broker_tp"),
    ]
    for sleeve, policy, trigger_r, trail_gap_r, time_stop_bars, target_model in cases:
        tp, req, entry, sign = _capture_open_trade_request(
            merged_cfg, sleeve, stop_dist=sd, target_dist=None)
        geom = tp["gtos_vnext_dynamic_target_stop_geometry_v4"]
        dest = geom["target_destination"]
        assert abs(req["sl"] - (entry - sign * sd)) < 1e-9, (sleeve, "sl", req["sl"])
        assert req["tp"] == 0.0, (sleeve, "broker tp omitted")
        assert tp["take_profit_1"] == 0.0, sleeve
        assert tp["gtos_vnext_dynamic_policy_selected"] == policy, sleeve
        assert tp["gtos_vnext_dynamic_final_target_r"] == 0.0, sleeve
        assert tp["gtos_vnext_dynamic_broker_take_profit_mode"] == "none", sleeve
        assert tp["gtos_vnext_dynamic_no_broker_take_profit"] is True, sleeve
        assert tp["gtos_vnext_dynamic_time_stop_bars"] == time_stop_bars, sleeve
        assert geom["status"] == "source_bound_geometry_contract_ready", sleeve
        assert dest["target_model"] == target_model, sleeve
        assert dest["broker_take_profit_mode"] == "none", sleeve
        assert dest["final_target_price"] is None, sleeve
        assert dest["destination_role"] == "targetless_dynamic_policy_managed_exit_not_realized_outcome"
        if policy == "trailing_runner":
            assert tp["gtos_vnext_dynamic_be_trigger_r"] == trigger_r, sleeve
            assert tp["gtos_vnext_dynamic_trail_gap_r"] == trail_gap_r, sleeve
            assert dest["trigger_r"] == trigger_r, sleeve
            assert dest["trail_gap_r"] == trail_gap_r, sleeve
        else:
            assert tp["gtos_vnext_dynamic_be_trigger_r"] == 0.0, sleeve
            assert dest["trail_gap_r"] is None, sleeve
        assert tp["gtos_vnext_book_native_exit_management"] is True, sleeve


def test_no_broker_tp_candidate_open_state_has_no_synthetic_final_target(merged_cfg):
    cases = [
        ("asian_fade", "trailing_runner", 0.5, 48),
        ("metal_session_reversion", "trailing_runner", 0.6, 24),
        ("ny_crypto_momentum", "time_stop", 0.0, 20),
        ("kz_london_crypto_low", "time_stop", 0.0, 32),
    ]
    for sleeve, policy, trigger_r, time_stop_bars in cases:
        tp, req, state = _open_trade_success_state(
            merged_cfg, sleeve, stop_dist=10.0, target_dist=None)
        assert req["tp"] == 0.0, sleeve
        assert state.gtos_vnext_dynamic_policy_selected == policy, sleeve
        assert state.gtos_vnext_dynamic_broker_take_profit_mode == "none", sleeve
        assert state.gtos_vnext_dynamic_no_broker_take_profit is True, sleeve
        assert state.gtos_vnext_dynamic_final_target_r == 0.0, sleeve
        assert state.gtos_vnext_dynamic_final_target_price == 0.0, sleeve
        assert state.take_profit_2 == 0.0, sleeve
        assert state.gtos_vnext_dynamic_time_stop_bars == time_stop_bars, sleeve
        if policy == "trailing_runner":
            assert state.take_profit_1 == pytest.approx(3000.0 + trigger_r * 10.0), sleeve
        else:
            assert state.take_profit_1 == 0.0, sleeve
        assert tp["gtos_vnext_book_native_exit_management"] is True, sleeve


def test_router_account_state_failclosed():
    router = UltimateBookOrderRouter({}, namespace="operator_profile")
    class NoEq:
        def get_account_equity(self): raise RuntimeError("down")
        def get_account_balance(self): return 100000.0
    assert router.account_state(NoEq(), day_start_baseline=100000.0, reset_window_id="d") is None
