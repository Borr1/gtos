"""Session AU (B1550) — the frontier exit contracts are runnable, selectable, and OFF by default.

WHAT IS BEING PINNED, AND WHY BEHAVIOURALLY

`target_5R` on `mx_btcusd_d1_donchian_20_breakout` is the exit the estate's ONE standing admission is
measured at; `target_4R` on `sub_xvol_pullback` is AK's frontier winner on a sleeve that is ARMED and
trading real money at 3R on both accounts. So the two properties that matter are opposite ones:

  1. with no selection, EVERY key the placement path emits is byte-identical to the pre-B1550 output
     -- because one of the two sleeves is live money and a wiring change must not reach it;
  2. with a selection, the broker take-profit really moves, and only for the named sleeve.

Both are asserted on the SIZED OUTPUT of the real `build_book_trade_params` (and, for the geometry, on
the request the real `ExecutionEngine.open_trade` would send), never on the source text. A test that
greps `execution_packets.py` for `final_target_r=5.0` passes against a wiring that never reaches the
broker -- which is exactly the defect class AR §8.15 shipped and then caught (a forward adapter that
"just works" while the inverse one rebuilt the field as None).

The frozen expectations below are the COMMITTED contract as of B1550, read off the dict once. They are
here so that a future edit to `SLEEVE_EXIT_PROFILES` that happens to collide with a frontier value
cannot make the default-path test vacuous.
"""
from types import SimpleNamespace

import ast
import inspect
import pathlib

import pytest
import yaml

from src.components.execution import ExecutionEngine
from src.components.ultimate_book import execution_packets as EP
from src.components.ultimate_book.admission import SizedUnit, TradeIntent
from src.components.ultimate_book.book_owner import UltimateBookOwner
from src.components.ultimate_book.order_router import UltimateBookOrderRouter
from src.utils.config import apply_instrument_overrides, apply_profile_overrides

REPO = pathlib.Path(__file__).resolve().parents[2]

BTC = "mx_btcusd_d1_donchian_20_breakout"
XVOL = "sub_xvol_pullback"
CRYPTO = "crypto"

#: The committed contract at B1550: (final_target_r, final_from_intent, time_stop_bars).
COMMITTED = {
    BTC: (2.0, True, 7680),
    XVOL: (3.0, None, 1280),
}
#: What each frontier override is worth, in broker-TP R.
FRONTIER_TARGET_R = {BTC: 5.0, XVOL: 4.0}


# =====================================================================================
# the selection parser — both fail-open shapes the estate has already measured on --tags
# =====================================================================================

def test_no_selection_is_the_empty_selection():
    assert EP.parse_frontier_exits(None) == ()


def test_an_empty_string_is_refused_and_does_not_mean_all():
    """`--tags ""` is falsy at run_book.py:340 and silently means EVERY BUILT sleeve (B359). The
    same string here must not mean 'every frontier contract' -- on a selection that reaches an armed
    sleeve's exit, fail-open is the expensive direction."""
    for empty in ("", "   ", ",", " , "):
        with pytest.raises(EP.FrontierExitSelectionError):
            EP.parse_frontier_exits(empty)


def test_an_unknown_sleeve_is_refused_rather_than_dropped():
    """`registry.py:144` drops unknown `--tags` with no error and the book stands down in silence.
    A dropped frontier name is worse in kind: the operator believes a measured contract is running
    and the book is running the committed one, with a healthy heartbeat and a normal-looking log."""
    with pytest.raises(EP.FrontierExitSelectionError):
        EP.parse_frontier_exits("sub_xvol_pulback")            # one letter
    with pytest.raises(EP.FrontierExitSelectionError):
        EP.parse_frontier_exits(f"{BTC},idxrev")               # a real sleeve with no wired frontier


def test_a_valid_selection_parses_and_dedupes():
    assert EP.parse_frontier_exits(f"{BTC},{XVOL}") == (BTC, XVOL)
    assert EP.parse_frontier_exits(f" {XVOL} , {XVOL} ") == (XVOL,)
    assert EP.parse_frontier_exits([BTC]) == (BTC,)
    assert EP.parse_frontier_exits(CRYPTO) == (CRYPTO,)


# =====================================================================================
# resolve_exit_profile
# =====================================================================================

def test_the_committed_contract_is_what_this_file_thinks_it_is():
    """If `SLEEVE_EXIT_PROFILES` moves, the default-path assertions below stop meaning anything.
    Fail here rather than let a collision make them vacuous."""
    for sleeve, (ftr, ffi, tsb) in COMMITTED.items():
        prof = EP.SLEEVE_EXIT_PROFILES[sleeve]
        assert prof.get("final_target_r") == ftr
        assert prof.get("final_from_intent") == ffi
        assert prof.get("time_stop_bars") == tsb
        assert ftr != FRONTIER_TARGET_R[sleeve], "the frontier value would be indistinguishable"


def test_no_selection_returns_the_committed_object_itself():
    """Identity, not equality: the default path cannot diverge from the dict if it IS the dict."""
    for sleeve in EP.SLEEVE_EXIT_PROFILES:
        assert EP.resolve_exit_profile(sleeve) is EP.SLEEVE_EXIT_PROFILES[sleeve]
    assert EP.resolve_exit_profile("no_such_sleeve") is EP.DEFAULT_EXIT_PROFILE


def test_a_selection_moves_only_the_named_sleeve():
    sel = (XVOL,)
    assert EP.resolve_exit_profile(XVOL, frontier_exits=sel)["final_target_r"] == 4.0
    assert EP.resolve_exit_profile(BTC, frontier_exits=sel) is EP.SLEEVE_EXIT_PROFILES[BTC]
    for sleeve in EP.SLEEVE_EXIT_PROFILES:
        if sleeve != XVOL:
            assert EP.resolve_exit_profile(sleeve, frontier_exits=sel) \
                is EP.SLEEVE_EXIT_PROFILES[sleeve]


def test_the_override_never_mutates_the_committed_dict():
    before = dict(EP.SLEEVE_EXIT_PROFILES[BTC])
    EP.resolve_exit_profile(BTC, frontier_exits=(BTC,))["final_target_r"] = 999.0
    assert EP.SLEEVE_EXIT_PROFILES[BTC] == before


def test_the_override_turns_off_final_from_intent_on_the_d1_sleeve():
    """`mx_btcusd`'s spec carries `final_from_intent=True`, so `build_book_trade_params` derives the
    broker TP from the intent's own target/stop ratio -- exactly 2.0 on all 318 walked trades. An
    override that set only `final_target_r` would be silently ignored on every intent that carries a
    target, which is every intent this sleeve produces."""
    prof = EP.resolve_exit_profile(BTC, frontier_exits=(BTC,))
    assert prof["final_from_intent"] is False and prof["final_target_r"] == 5.0
    #: and the time stop is untouched: the 80-own-bar horizon AQ repaired is the frontier cell's
    #: `maxbars`, so moving it would change the contract the cell was measured under.
    assert prof["time_stop_bars"] == COMMITTED[BTC][2]


def test_the_time_stop_is_the_research_horizon_for_both_wired_sleeves():
    """The frontier cells carry `maxbars=80` own bars and NO time stop. The live analogue is a time
    stop at 80 own bars, which fires on the same bar `maxbars` does -- AQ's C1 control, 2,086/2,086
    trades identical. If either sleeve's declared stop stopped being the 80-bar horizon, the wired
    contract would no longer be the cell that was measured."""
    assert EP.SLEEVE_EXIT_PROFILES[BTC]["time_stop_bars"] == EP.time_stop_m15(80, "D1")
    assert EP.SLEEVE_EXIT_PROFILES[XVOL]["time_stop_bars"] == EP.time_stop_m15(80, "H4")


# =====================================================================================
# the placement path — byte-identity off, a real TP move on
# =====================================================================================

@pytest.fixture(scope="module")
def merged_cfg():
    cfg = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))
    cfg = apply_profile_overrides(cfg, "operator_profile")
    return apply_instrument_overrides(cfg, "XAUUSD")


def _params(sleeve, *, frontier_exits=(), stop_dist=10.0, target_dist=None, entry=3000.0):
    su = SizedUnit(cluster="book", sleeve_members=[sleeve], n_trades=1, confidence=1.0,
                   risk_pct_per_trade=0.005, unit_risk_pct=0.5, sized=True, reason="ok")
    intent = TradeIntent(sleeve=sleeve, symbol="XAUUSD", direction=1, decision_day="2026-06-15",
                         stop_dist=stop_dist, target_dist=target_dist)
    acct = dict(current_equity=100000.0, balance=100000.0, account_login=531325516,
                day_start_equity_or_balance_baseline=100000.0, daily_reset_window_id="2026-06-15")
    geom = {"entry_price": entry, "risk_distance": stop_dist, "stop_loss": entry - stop_dist,
            "take_profit_1": entry + (target_dist or 0.0)}
    return EP.build_book_trade_params(su, intent, geom, acct,
                                      profile_namespace="operator_profile",
                                      frontier_exits=frontier_exits)


#: `build_book_trade_params` stamps `datetime.now()` into three keys, so a two-call comparison must
#: exclude them or it is a clock test. Everything else is deterministic.
_WALL_CLOCK = ("decision_time_utc", "asof_utc", "gtos_vnext_prop_firm_headroom_snapshot_v4",
               "gtos_vnext_dynamic_target_stop_geometry_v4")


def _stable(tp):
    return {k: v for k, v in tp.items() if k not in _WALL_CLOCK}


@pytest.mark.parametrize("sleeve,target_dist", [(BTC, 20.0), (XVOL, 30.0)])
def test_the_default_path_is_byte_identical_on_the_sized_output(sleeve, target_dist):
    """The empty selection must produce the same placement as a call that never heard of the flag."""
    a = _params(sleeve, target_dist=target_dist)
    b = _params(sleeve, frontier_exits=(), target_dist=target_dist)
    assert _stable(a) == _stable(b)
    #: and the same as the pre-B1550 signature, which did not accept the argument at all
    su = SimpleNamespace(cluster="book", sleeve_members=[sleeve], n_trades=1, confidence=1.0,
                         risk_pct_per_trade=0.005)
    intent = TradeIntent(sleeve=sleeve, symbol="XAUUSD", direction=1, decision_day="2026-06-15",
                         stop_dist=10.0, target_dist=target_dist)
    acct = dict(current_equity=100000.0, balance=100000.0, account_login=531325516,
                day_start_equity_or_balance_baseline=100000.0, daily_reset_window_id="2026-06-15")
    geom = {"entry_price": 3000.0, "risk_distance": 10.0, "stop_loss": 2990.0}
    legacy = EP.build_book_trade_params(su, intent, geom, acct,
                                        profile_namespace="operator_profile")
    assert _stable(legacy) == _stable(a)


def test_the_default_path_carries_no_exit_contract_provenance():
    """`source_event_details` is HASHED into `gtos_vnext_source_event_hash`, so a provenance key added
    unconditionally would move the hash on every default placement."""
    tp = _params(XVOL, target_dist=30.0)
    assert "exit_contract" not in tp["gtos_vnext_source_event_details"]


@pytest.mark.parametrize("sleeve", [BTC, XVOL])
def test_the_selection_moves_the_broker_take_profit_and_the_hash(sleeve):
    off = _params(sleeve, target_dist=20.0)
    on = _params(sleeve, frontier_exits=(sleeve,), target_dist=20.0)
    k = FRONTIER_TARGET_R[sleeve]
    #: entry 3000, stop_dist 10, LONG -> TP = entry + k*R
    assert on["take_profit_1"] == pytest.approx(3000.0 + k * 10.0)
    assert on["gtos_vnext_dynamic_final_target_r"] == pytest.approx(k)
    assert off["take_profit_1"] != on["take_profit_1"]
    #: the stop is untouched -- a target change must never move the risk unit
    assert on["stop_loss"] == off["stop_loss"] == pytest.approx(2990.0)
    assert on["risk_pct_override"] == off["risk_pct_override"]
    #: the time stop the engine re-drives is untouched
    assert on["gtos_vnext_dynamic_time_stop_bars"] == off["gtos_vnext_dynamic_time_stop_bars"]
    #: and the placement says which contract placed it
    ec = on["gtos_vnext_source_event_details"]["exit_contract"]
    assert ec["kind"] == "frontier_override"
    assert ec["frontier_cell"] == ("target_5R" if sleeve == BTC else "target_4R")
    assert on["gtos_vnext_source_event_hash"] != off["gtos_vnext_source_event_hash"]


def test_the_provenance_keys_never_reach_the_geometry_contract():
    """`frontier_cell` / `frontier_evidence` are documentation. The geometry builder takes explicit
    arguments, so they can only leak by being written into a management-params dict."""
    on = _params(XVOL, frontier_exits=(XVOL,), target_dist=30.0)
    flat = repr(on["gtos_vnext_dynamic_target_stop_geometry_v4"])
    assert "frontier_evidence" not in flat and "target_4R" not in flat


def test_the_d1_sleeve_ignores_a_generator_target_under_the_override():
    """The measured failure mode of a `final_target_r`-only override: `final_from_intent` wins and the
    override is invisible. Drive it with the ratio the generator really emits (2.0)."""
    on = _params(BTC, frontier_exits=(BTC,), stop_dist=10.0, target_dist=20.0)
    assert on["gtos_vnext_dynamic_final_target_r"] == pytest.approx(5.0)


def test_crypto_stop_width_scales_broker_sl_and_tp_and_preserves_risk_pct():
    """CM's fidelity cell is stop geometry, not a target-only analogue.

    Entry 3000, native stop 10, LONG: the selected contract must send SL 2985 and TP 3060.
    A wiring that changes only `risk_distance`, only TP, or only SL is not
    `stop_1.5x_tgtscale` and would size or settle the real order against the wrong R unit.
    """
    off = _params(CRYPTO, stop_dist=10.0, target_dist=40.0)
    on = _params(CRYPTO, frontier_exits=(CRYPTO,), stop_dist=10.0, target_dist=40.0)
    assert off["stop_loss"] == pytest.approx(2990.0)
    assert off["take_profit_1"] == pytest.approx(3040.0)
    assert on["stop_loss"] == pytest.approx(2985.0)
    assert on["take_profit_1"] == pytest.approx(3060.0)
    assert on["gtos_vnext_dynamic_target_stop_geometry_v4"]["stop_invalidation"][
        "risk_distance"
    ] == pytest.approx(15.0)
    assert on["risk_pct_override"] == off["risk_pct_override"]
    assert on["gtos_vnext_source_event_details"]["exit_contract"]["frontier_cell"] \
        == "stop_1p5x_target_scale"
    assert "stop distance x1.5" in EP.describe_frontier_contract(CRYPTO)


def test_a_targetless_intent_reaches_the_same_contract():
    """`final_from_intent` also falls through when the intent carries no target; the override must
    give the same answer either way, or the contract would depend on generator plumbing."""
    with_t = _params(BTC, frontier_exits=(BTC,), target_dist=20.0)
    without = _params(BTC, frontier_exits=(BTC,), target_dist=None)
    assert with_t["take_profit_1"] == without["take_profit_1"]


# =====================================================================================
# the geometry the real engine would send
# =====================================================================================

class _CapturedRequest(Exception):
    def __init__(self, request):
        self.request = dict(request)


class _Tick:
    def __init__(self, bid, ask):
        self.bid, self.ask = bid, ask
        self.time = "2026-06-15T01:00:00+00:00"
        self.spread_cents = (ask - bid) * 100


class _StubMT5:
    _INFO = SimpleNamespace(trade_tick_size=0.01, trade_tick_value=1.0, volume_min=0.01,
                            volume_step=0.01, volume_max=100.0, filling_mode=3, spread=12)

    def __init__(self):
        self._mt5 = SimpleNamespace(
            symbol_info=lambda _s: self._INFO,
            order_calc_profit=lambda ot, _s, vol, po, pc: (
                ((pc - po) if int(ot) == 0 else (po - pc))
                / self._INFO.trade_tick_size * self._INFO.trade_tick_value * float(vol)))

    def get_tick(self, symbol): return _Tick(2999.7, 3000.0)
    def get_account_balance(self): return 100000.0
    def get_account_equity(self): return 100000.0
    def get_positions(self, symbol=None): return []
    def is_connected(self): return True
    def get_margin_mode(self): return "hedging"


def _broker_request(merged_cfg, sleeve, *, frontier_exits=()):
    """The request the REAL open_trade path would send, intercepted before any order_send."""
    tp = _params(sleeve, frontier_exits=frontier_exits, target_dist=20.0)
    ee = ExecutionEngine(_StubMT5(), merged_cfg)
    ee.symbol = ee._persist_symbol = "XAUUSD"
    ee._enforce_runtime_halt_clear = lambda *a, **k: None      # test-only; the request is intercepted

    def _capture(request, *a, **k):
        raise _CapturedRequest(request)

    ee.safe_place_order = _capture
    with pytest.raises(_CapturedRequest) as exc:
        ee.open_trade(tp, 100000.0, risk_pct_override=tp["risk_pct_override"],
                      trigger="ultimate_book")
    return exc.value.request


@pytest.mark.parametrize("sleeve", [BTC, XVOL])
def test_the_frontier_contract_clears_the_live_gates_and_moves_the_broker_tp(merged_cfg, sleeve):
    """The whole point: it is RUNNABLE. The three fail-closed gates in `open_trade` are the reason a
    plausible-looking trade_params dict can be inert, so the assertion is on the broker request."""
    off = _broker_request(merged_cfg, sleeve)
    on = _broker_request(merged_cfg, sleeve, frontier_exits=(sleeve,))
    k = FRONTIER_TARGET_R[sleeve]
    entry, r = float(on["price"]), 10.0
    assert on["tp"] == pytest.approx(entry + k * r, abs=0.02)
    assert on["sl"] == pytest.approx(off["sl"], abs=1e-9)      # same risk unit
    assert on["volume"] == pytest.approx(off["volume"], abs=1e-9)   # same size
    assert on["tp"] > off["tp"]


def test_crypto_stop_width_reaches_the_broker_request_and_reduces_lots(merged_cfg):
    """CM's selected cell must survive the final sizing/send adapter, not just the packet builder.

    The risk percentage is unchanged, so a 1.5x wider broker stop must cut the rounded lot size
    while scaling both SL and TP from the actual entry price.  The request is intercepted before
    ``safe_place_order`` and therefore cannot reach ``order_send``.
    """
    off = _broker_request(merged_cfg, CRYPTO)
    on = _broker_request(merged_cfg, CRYPTO, frontier_exits=(CRYPTO,))
    entry = float(on["price"])
    off_r = entry - float(off["sl"])
    on_r = entry - float(on["sl"])
    assert on_r == pytest.approx(1.5 * off_r, abs=0.02)
    assert float(on["tp"]) - entry == pytest.approx(4.0 * on_r, abs=0.02)
    assert on["volume"] < off["volume"]
    assert on["volume"] == pytest.approx(off["volume"] / 1.5, abs=0.01)


# =====================================================================================
# the adopt-rehydration path
# =====================================================================================

@pytest.mark.parametrize("sleeve", [BTC, XVOL])
def test_rehydration_follows_the_selection(sleeve):
    off = EP.native_policy_instrumentation(sleeve)
    on = EP.native_policy_instrumentation(sleeve, frontier_exits=(sleeve,))
    assert off["gtos_vnext_dynamic_final_target_r"] == pytest.approx(COMMITTED[sleeve][0]
                                                                     if sleeve == XVOL else 2.0)
    assert on["gtos_vnext_dynamic_final_target_r"] == pytest.approx(FRONTIER_TARGET_R[sleeve])
    #: the time-stop the engine re-drives is the same under both
    assert on["gtos_vnext_dynamic_time_stop_bars"] == off["gtos_vnext_dynamic_time_stop_bars"]


def test_rehydration_is_unchanged_for_every_other_sleeve():
    sel = (BTC, XVOL)
    for sleeve in EP.SLEEVE_EXIT_PROFILES:
        if sleeve in sel:
            continue
        assert EP.native_policy_instrumentation(sleeve, frontier_exits=sel) \
            == EP.native_policy_instrumentation(sleeve)


# =====================================================================================
# the wiring reaches the router and the owner, and is nowhere near a config file
# =====================================================================================

def test_the_router_defaults_to_the_committed_contract(merged_cfg):
    su = SizedUnit(cluster="book", sleeve_members=[XVOL], n_trades=1, confidence=1.0,
                   risk_pct_per_trade=0.005, unit_risk_pct=0.5, sized=True, reason="ok")
    intent = TradeIntent(sleeve=XVOL, symbol="XAUUSD", direction=1, decision_day="2026-06-15",
                         stop_dist=10.0, target_dist=30.0)
    acct = dict(current_equity=100000.0, balance=100000.0, account_login=531325516,
                day_start_equity_or_balance_baseline=100000.0, daily_reset_window_id="2026-06-15")
    plain = UltimateBookOrderRouter(merged_cfg, namespace="operator_profile")
    armed = UltimateBookOrderRouter(merged_cfg, namespace="operator_profile",
                                    frontier_exits=(XVOL,))
    assert plain.frontier_exits == ()
    a = plain.build_trade_params(su, intent, _Tick(2999.7, 3000.0), acct)
    b = armed.build_trade_params(su, intent, _Tick(2999.7, 3000.0), acct)
    assert a["gtos_vnext_dynamic_final_target_r"] == pytest.approx(3.0)
    assert b["gtos_vnext_dynamic_final_target_r"] == pytest.approx(4.0)


def test_the_owner_passes_the_selection_to_the_router_and_defaults_empty(merged_cfg):
    """Constructed with a stub broker; the owner builds its engine and router in __init__ and nothing
    here ticks, generates or places."""
    owner = UltimateBookOwner(merged_cfg, _StubMT5(), ".", namespace="operator_profile")
    assert owner.router.frontier_exits == ()
    armed = UltimateBookOwner(merged_cfg, _StubMT5(), ".", namespace="operator_profile",
                              frontier_exits=(BTC,))
    assert armed.router.frontier_exits == (BTC,)
    assert armed._frontier_exits == (BTC,)


def test_the_launcher_exposes_the_flag_and_defaults_it_off():
    """AST, not `--help`: `run_book.py` is on the never-execute list and AR §8.7 recorded running it
    for exactly this check as a breach that was available for free from the source tree."""
    tree = ast.parse((REPO / "run_book.py").read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "add_argument"
             and n.args and isinstance(n.args[0], ast.Constant)
             and n.args[0].value == "--frontier-exits"]
    assert len(calls) == 1, "--frontier-exits must be declared exactly once"
    kw = {k.arg: k.value for k in calls[0].keywords}
    assert isinstance(kw["default"], ast.Constant) and kw["default"].value is None
    #: and it is threaded into the owner rather than parsed and dropped
    src = (REPO / "run_book.py").read_text(encoding="utf-8")
    assert "parse_frontier_exits(args.frontier_exits)" in src
    assert "frontier_exits=frontier_exits" in src


def test_the_selection_is_not_a_config_key_anywhere():
    """The flag must never become a YAML key: `config/agent_config.yaml` AND
    `config/profiles/redacted_account.yaml` are each hashed into a live activation token's config digest, so
    one byte would stop an armed book placing. And it must never reach `bridge._bool`, which resolves
    an absent key against `DEFAULT_CONFIG` and raises KeyError otherwise -- an exception the engine
    catches as `engine_exception`, i.e. an armed book standing down every tick with a healthy
    heartbeat (AR §0). A key that is never read cannot be read wrong."""
    for rel in ("config/agent_config.yaml", "config/profiles/redacted_account.yaml",
                "config/profiles/operator_profile.yaml", "config/profiles/ftmo.yaml"):
        text = (REPO / rel).read_text(encoding="utf-8")
        assert "frontier_exit" not in text, f"{rel} must not carry the frontier selection"
    from src.components.ultimate_book import bridge
    assert not [k for k in bridge.DEFAULT_CONFIG if "frontier" in k]
    bridge_src = inspect.getsource(bridge)
    assert "frontier" not in bridge_src, "the frontier selection must not reach the bridge"


def test_every_wired_override_is_a_sleeve_the_registry_knows():
    """A frontier contract for a sleeve no spec generates would be dead wiring that reads as live.
    AK's safe order (confidence weight first, spec second) is about ADDING a sleeve; this is the
    matching check for adding a CONTRACT -- the sleeve must already exist on both sides."""
    from src.components.ultimate_book.admission import (effective_registry,
                                                        market_expansion_conditioned_policies)
    from src.components.ultimate_book.sleeves.registry import active_specs
    #: the LIVE market-expansion policy (`agent_config.yaml:1284`), which is what makes the registry
    #: resolve 32 rather than 20 -- `include_market_expansion_book` alone fails closed by design.
    mx = list(market_expansion_conditioned_policies()["positive_weighted12_after_swap"])
    reg = set(effective_registry(include_clean3=True, include_candidate_book=True,
                                 include_market_expansion_book=True,
                                 market_expansion_sleeves=mx))
    specs = {s.tag for s in active_specs(None, include_candidate_book=True,
                                         include_market_expansion_book=True,
                                         market_expansion_sleeves=mx)}
    #: STALE EXPECTATION repaired 2026-08-25: B325's 32 became 35 when Ceremony 20260825 S1
    #: (commit 68ca70e40, pinned by tests/ultimate_book/test_widen_wrappers.py) added three
    #: WIDEN wrapper sleeves BESIDE their incumbents (parallel WIDEN_BUILT, MC pin intact).
    #: The wrapper roster is asserted by name and the count stays exact, so a fourth wrapper
    #: cannot ride in on a widened total and silent registry drift still fails loudly.
    widen = {s for s in reg if s.endswith("_widen")}
    assert widen == {"asian_fade_widen", "ny_crypto_momentum_widen",
                     "orb_crypto_london_widen"}, \
        "the WIDEN_BUILT wrappers are exactly the three the 20260825 ceremony added"
    assert len(reg) == 35, \
        "32 incumbent sleeves (CLAUDE.md §4 / B325) + 3 WIDEN_BUILT wrappers (68ca70e40)"
    for sleeve in EP.FRONTIER_EXIT_OVERRIDES:
        assert sleeve in EP.SLEEVE_EXIT_PROFILES, f"{sleeve} has no committed exit profile"
        assert sleeve in reg, f"{sleeve} carries no confidence weight -- it could never be sized"
        assert sleeve in specs, f"{sleeve} has no generation spec -- the contract would be dead"


def test_every_override_declares_its_evidence():
    for sleeve, over in EP.FRONTIER_EXIT_OVERRIDES.items():
        cell = over["frontier_cell"]
        assert any(cell.startswith(k) for k in EP.FRONTIER_CELL_KINDS), \
            f"{sleeve}: {cell!r} is not a declared kind of frontier cell"
        ev = REPO / "docs/audits/fable5-vision-audit-20260725" / over["frontier_evidence"]
        assert ev.exists(), f"{sleeve}'s cited evidence {over['frontier_evidence']} is not on disk"
        if cell.startswith("target_"):
            assert float(over["final_target_r"]) == FRONTIER_TARGET_R[sleeve]
            assert over["final_from_intent"] is False
            assert "time_stop_bars" not in over, "a target cell must not move the horizon"
        else:
            assert "final_target_r" not in over, "a horizon cell must not move the target"


# =====================================================================================
# the deliberate short horizons (AU-3)
# =====================================================================================

#: (sleeve, own D1 bars) for every horizon override, from AU_D1_HORIZONS_V1's prescriptions.
HORIZON_OVERRIDES = {
    "mx_us100_cash_d1_atr_mean_reversion": 1,
    "mx_us500_cash_d1_atr_mean_reversion": 1,
    "mx_ger40_cash_d1_volume_surge_reversal": 1,
    "mx_us30_cash_d1_volume_surge_reversal": 1,
    "mx_ethusd_d1_donchian_20_breakout": 10,
    "vol_compression": 20,
}


@pytest.mark.parametrize("sleeve,own_bars", sorted(HORIZON_OVERRIDES.items()))
def test_a_horizon_override_moves_the_time_stop_and_nothing_else(sleeve, own_bars):
    off = EP.resolve_exit_profile(sleeve)
    on = EP.resolve_exit_profile(sleeve, frontier_exits=(sleeve,))
    assert on["time_stop_bars"] == EP.time_stop_m15(own_bars, "D1")
    assert off["time_stop_bars"] == EP.time_stop_m15(80, "D1"), \
        "the committed horizon must still be the 80-bar research horizon AQ repaired it to"
    for k in ("policy", "final_target_r", "final_from_intent", "trigger_r", "trail_gap_r",
              "partial_close_ratio", "broker_take_profit_mode"):
        assert on.get(k) == off.get(k), f"{sleeve}: a horizon cell moved {k}"


@pytest.mark.parametrize("sleeve,own_bars", sorted(HORIZON_OVERRIDES.items()))
def test_the_horizon_override_reaches_the_placement_and_the_rehydration(sleeve, own_bars):
    want = EP.time_stop_m15(own_bars, "D1")
    tp = _params(sleeve, frontier_exits=(sleeve,), target_dist=20.0)
    assert tp["gtos_vnext_dynamic_time_stop_bars"] == want
    assert tp["gtos_vnext_source_event_details"]["exit_contract"]["frontier_cell"] \
        == f"time_stop_{own_bars}_d1"
    #: the broker take-profit is untouched: a horizon change must not move where profit is taken
    assert tp["take_profit_1"] == _params(sleeve, target_dist=20.0)["take_profit_1"]
    assert EP.native_policy_instrumentation(sleeve, frontier_exits=(sleeve,))[
        "gtos_vnext_dynamic_time_stop_bars"] == want


def test_the_four_one_bar_horizons_are_the_integer_AQ_removed_and_that_is_deliberate():
    """The value is 96 again, and the difference from the defect is the whole point.

    AQ's repair was a UNIT repair: a field whose unit is M15 printed bars cannot hold
    `M15_BARS_PER["D1"]` and mean anything, so 96 had to go whatever its economics. Four sleeves'
    gated ladder then said one D1 bar is their best horizon — so the same integer comes back, but as
    `time_stop_m15(1, "D1")` with a measurement behind it, in a map that is OFF by default. A test
    pins that equality so nobody reads a future diff as a revert.
    """
    one_bar = EP.time_stop_m15(1, "D1")
    assert one_bar == 96 == EP.M15_BARS_PER["D1"]
    for sleeve, own in HORIZON_OVERRIDES.items():
        if own != 1:
            continue
        assert EP.FRONTIER_EXIT_OVERRIDES[sleeve]["time_stop_bars"] == one_bar
        #: and the committed spec is emphatically NOT 96 — the accident is still repaired
        assert EP.SLEEVE_EXIT_PROFILES[sleeve]["time_stop_bars"] == 7680


def test_no_armed_sleeve_carries_a_horizon_override():
    """The five sleeves both live books trade (CLAUDE.md §4) are `crypto`, `energy_agri`,
    `sub_xvol_pullback`, `fx_jpy`, `sub_mid_dn_revert`. A horizon override on one of them would be a
    live exit change riding in on a research prescription.

    AMENDED by Session BD. This asserted `frontier_cell.startswith("target_")` for every armed
    sleeve, which was an exact proxy for "not a horizon cell" only while `target_` and `time_stop_`
    were the only two kinds. `plain_exit_no_partial` on `energy_agri` is neither -- it moves no
    number in the spec at all, it removes a management leg -- so the proxy failed on a cell it was
    never written to forbid. The invariant is asserted DIRECTLY now, which is strictly stronger than
    the string test it replaces: an armed sleeve may not carry `time_stop_bars` under ANY cell name,
    including a future kind nobody has thought of.
    """
    armed = {"crypto", "energy_agri", "sub_xvol_pullback", "fx_jpy", "sub_mid_dn_revert"}
    assert not (set(HORIZON_OVERRIDES) & armed)
    for sleeve in set(EP.FRONTIER_EXIT_OVERRIDES) & armed:
        over = EP.FRONTIER_EXIT_OVERRIDES[sleeve]
        assert "time_stop_bars" not in over, (
            f"{sleeve} is ARMED and its override moves the horizon -- a live exit change riding in "
            f"on a research prescription, which is the thing this test exists to stop"
        )
        # ...and every armed override is still a DECLARED kind, so a typo cannot reach a live book.
        assert any(over["frontier_cell"].startswith(k) for k in EP.FRONTIER_CELL_KINDS)


def test_the_armed_overrides_are_exactly_the_three_that_were_measured():
    """A roster, so a fourth armed-sleeve contract cannot appear without this line changing.

    `sub_xvol_pullback @ target_4R` (AK's frontier winner, re-gated by AU and REJECT at all four
    bands) is runnable and priced so the option is not re-derived; it is not recommended for
    arming. `crypto @ stop_1p5x_target_scale` is CM's FTMO-only selected fidelity arm, ARMED
    2026-08-02 and ROLLED BACK 2026-08-10 on the owner's word.

    `energy_agri` INVERTED on 2026-08-11 (owner-authorized, lane B7): the plain exit became the
    committed default, so the override that used to reach it -- `plain_exit_no_partial` -- would
    now resolve to the committed dict and change nothing. It points the other way and RESTORES the
    scale-out, which is what keeps a code-free rollback available.
    """
    armed = {"crypto", "energy_agri", "sub_xvol_pullback", "fx_jpy", "sub_mid_dn_revert"}
    assert {s: EP.FRONTIER_EXIT_OVERRIDES[s]["frontier_cell"]
            for s in set(EP.FRONTIER_EXIT_OVERRIDES) & armed} == {
        "crypto": "stop_1p5x_target_scale",
        "sub_xvol_pullback": "target_4R",
        "energy_agri": "partial_be_runner_restore",
    }


def test_the_scale_out_cell_adds_the_scale_out_and_moves_nothing_else():
    """BD's arm, now run from the other side. The delta must still be the scale-out ALONE.

    Same measurement, opposite default: BD compared plain against the committed scale-out; since
    2026-08-11 plain IS the committed contract and the override restores the scale-out. The
    invariant being tested is unchanged -- target and horizon must be identical in both arms, or
    the -0.2883 R/trade delta is not attributable to the scale-out.
    """
    committed = EP.SLEEVE_EXIT_PROFILES["energy_agri"]
    restored = EP.resolve_exit_profile("energy_agri", frontier_exits=("energy_agri",))
    assert committed["policy"] == "time_stop" and restored["policy"] == "partial_be_runner"
    assert committed.get("partial_close_ratio") is None and restored["partial_close_ratio"] == 0.5
    # the target and the horizon are untouched -- that is what makes the comparison a clean one
    assert restored["final_target_r"] == committed["final_target_r"] == 4.0
    assert restored["time_stop_bars"] == committed["time_stop_bars"] == 1280
    # `trigger_r` must be a NUMBER: build_book_trade_params does float(prof.get("trigger_r", ...)),
    # so a literal None here is a TypeError on the live placement path. On the restored arm it is
    # the 2.0 scale-out trigger; on the committed arm the key is absent and resolves to the target.
    assert restored["trigger_r"] == 2.0
    assert float(EP.native_policy_instrumentation("energy_agri")["gtos_vnext_dynamic_be_trigger_r"]) \
        == float(committed["final_target_r"])


def test_the_committed_energy_agri_contract_is_the_plain_exit_by_default():
    """The sleeve is ARMED. With no selection the book must resolve the PLAIN 4R contract.

    Changed 2026-08-11 (owner-authorized, lane B7): the scale-out cost -0.2883 R/trade paired on
    identical entries (n=72, t=-2.385) and is no longer the committed default.
    """
    prof = EP.resolve_exit_profile("energy_agri")
    assert prof is EP.SLEEVE_EXIT_PROFILES["energy_agri"]
    assert prof["policy"] == "time_stop"
    assert prof.get("partial_close_ratio") is None
    assert prof.get("trigger_r") is None
    assert prof["final_target_r"] == 4.0 and prof["time_stop_bars"] == 1280
