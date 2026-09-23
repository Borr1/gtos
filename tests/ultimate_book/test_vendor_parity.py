"""T1 — numeric-parity guard: the vendored src/components/ultimate_book pure layer must compute
IDENTICALLY to the locked research route modules. If this ever fails, the live book has drifted
from the validated book and must NOT trade. Pure, no MT5.
"""
import os
import sys
import math
import importlib

import pytest

ROUTE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "research", "operations", "final_moonshot_v4_ultimate_mechanical_edge_2026_06_10",
)


@pytest.fixture(scope="module")
def route_mods():
    if ROUTE not in sys.path:
        sys.path.insert(0, ROUTE)
    geometry_lib = importlib.import_module("geometry_lib")
    compounding_sleeve = importlib.import_module("compounding_sleeve")
    ubp = importlib.import_module("ultimate_book_live_package")
    return geometry_lib, compounding_sleeve, ubp


def _bars(prim):
    # deterministic synthetic H4 series (uptrend with noise) as the route Bar AND the src Bar
    out = []
    p = 2000.0
    for k in range(120):
        o = p
        h = o + 6 + (k % 5)
        l = o - 4 - (k % 3)
        c = o + ((k % 7) - 3) * 1.5
        out.append(prim.Bar(o, h, l, c, 100 + k))
        p = c
    return out


def test_primitives_parity(route_mods):
    geometry_lib, compounding_sleeve, _ = route_mods
    from src.components.ultimate_book import primitives as P

    rb = _bars(geometry_lib)
    sb = _bars(P)
    # atr14
    for i in (14, 40, 80, 119):
        assert abs(geometry_lib.atr14(rb, i) - P.atr14(sb, i)) < 1e-12
    # simulate (long + short, fixed target and trail)
    for d in (1, -1):
        r_fixed = geometry_lib.simulate(rb, 30, d, stop_dist=10.0, target_dist=40.0, maxbars=60)
        s_fixed = P.simulate(sb, 30, d, stop_dist=10.0, target_dist=40.0, maxbars=60)
        assert abs(r_fixed - s_fixed) < 1e-12
        r_tr = geometry_lib.simulate(rb, 30, d, stop_dist=10.0, trail_arm=12.0, trail_gap=8.0, maxbars=60)
        s_tr = P.simulate(sb, 30, d, stop_dist=10.0, trail_arm=12.0, trail_gap=8.0, maxbars=60)
        assert abs(r_tr - s_tr) < 1e-12
    # autocorr / vol_ratio / exit_state_d
    atrs_r = [geometry_lib.atr14(rb, i) for i in range(len(rb))]
    atrs_s = [P.atr14(sb, i) for i in range(len(sb))]
    for i in (70, 100, 119):
        a_r = compounding_sleeve.autocorr(rb, i); a_s = P.autocorr(sb, i)
        assert (a_r is None and a_s is None) or abs(a_r - a_s) < 1e-12
        assert abs(compounding_sleeve.vol_ratio(atrs_r, i) - P.vol_ratio(atrs_s, i)) < 1e-12
    for d in (1, -1):
        e_r = compounding_sleeve.exit_state_d(rb, 30, d, 10.0, 1.4, 0.01, maxbars=60)
        e_s = P.exit_state_d(sb, 30, d, 10.0, 1.4, 0.01, maxbars=60)
        assert abs(e_r["R"] - e_s["R"]) < 1e-12 and e_r["reason"] == e_s["reason"]


def test_admission_parity(route_mods):
    _, _, ubp = route_mods
    from src.components.ultimate_book import admission as A

    def mk(mod):
        I = mod.TradeIntent
        return [
            I(sleeve="metals_core", symbol="XAUUSD", direction=1, decision_day="2026-06-10", stop_dist=10.0),
            I(sleeve="crypto", symbol="BTCUSD", direction=1, decision_day="2026-06-10", stop_dist=500.0),
            I(sleeve="energy_agri", symbol="USOIL_cash", direction=-1, decision_day="2026-06-10", stop_dist=1.0),
            I(sleeve="idxrev", symbol="SPX500", direction=1, decision_day="2026-06-10", stop_dist=20.0),
        ]

    gs_r = ubp.GovernorState(equity=100000.0, high_water=100000.0, realized_today_pct=0.0, open_risk_pct=0.0)
    gs_s = A.GovernorState(equity=100000.0, high_water=100000.0, realized_today_pct=0.0, open_risk_pct=0.0)
    kw = dict(profile="clean3_w7_measured_nom1p25", include_clean3=True, kelly_lite=True,
              kelly_conservative=True, drop_w7_symbols=True)
    r = ubp.admit_and_size(mk(ubp), gs_r, **kw)
    s = A.admit_and_size(mk(A), gs_s, **kw)
    assert r["new_entries_allowed"] == s["new_entries_allowed"]
    ru = {u["cluster"]: u for u in r["units"]}
    su = {u["cluster"]: u for u in s["units"]}
    assert set(ru) == set(su)
    for cl in ru:
        assert abs(ru[cl]["risk_pct_per_trade"] - su[cl]["risk_pct_per_trade"]) < 1e-12
        assert ru[cl]["sized"] == su[cl]["sized"]
        assert abs(ru[cl]["confidence"] - su[cl]["confidence"]) < 1e-12
        assert ru[cl]["n_trades"] == su[cl]["n_trades"]
    # governor parity
    assert abs(r["governor"]["available_gross_risk_pct"] - s["governor"]["available_gross_risk_pct"]) < 1e-12
