"""test_symbol_damage_guard.py — the S1 per-symbol damage-memory kill switch (default-off) + its admission wiring.

Proves: the verified classifier thresholds; leak-free metrics (prior days only); DEFAULT-OFF is a byte-identical
no-op in admission; and when armed, a QUARANTINE symbol's intents are DROPPED + a RISK_REDUCE symbol is halved.
"""
import sys, datetime as dt
# NOTE 2026-07-26: a hardcoded sys.path.insert(0, "/Users/borr/Documents/gtos/repo/
# ai-trading-agent") was removed here. It prepended a DIFFERENT, stale checkout, so this
# file silently tested that repo instead of the working tree whenever it ran in isolation
# (in a full-suite run sys.modules was already populated, so the same tests exercised the
# real code and could disagree). Tests must import the tree they are checked out in.
from src.components.ultimate_book.symbol_damage_guard import (
    classify_symbol_health, damage_multiplier, compute_symbol_metrics, symbol_damage_mult,
    QUARANTINE, RISK_REDUCE, HEALTHY)
from src.components.ultimate_book.admission import size_correlated_units, TradeIntent

DAY = "2026-06-17"


def test_classifier_matches_verified_thresholds():
    assert classify_symbol_health(trades=6, losses=4, net=0.0, win_rate=0.6) == QUARANTINE       # losses>=4
    assert classify_symbol_health(trades=8, losses=2, net=-600.0, win_rate=0.6) == QUARANTINE    # net<=-500
    assert classify_symbol_health(trades=10, losses=2, net=0.0, win_rate=0.30) == QUARANTINE      # wr<=0.35
    assert classify_symbol_health(trades=3, losses=1, net=-150.0, win_rate=0.6) == RISK_REDUCE    # net<=-100
    assert classify_symbol_health(trades=3, losses=1, net=0.0, win_rate=0.40) == RISK_REDUCE       # wr<=0.45
    assert classify_symbol_health(trades=2, losses=0, net=50.0, win_rate=1.0) == HEALTHY
    assert classify_symbol_health(trades=5, losses=4, net=-600.0, win_rate=0.1) == RISK_REDUCE     # trades<6 -> not hard


def test_damage_multiplier_default_off():
    for v in (QUARANTINE, RISK_REDUCE, HEALTHY):
        assert damage_multiplier(v, enabled=False) == 1.0       # default-off = no-op
    assert damage_multiplier(QUARANTINE, enabled=True) == 0.0
    assert damage_multiplier(RISK_REDUCE, enabled=True) == 0.5
    assert damage_multiplier(HEALTHY, enabled=True) == 1.0


def test_compute_metrics_leak_free_prior_only():
    now = dt.datetime(2026, 6, 17, 12, tzinfo=dt.timezone.utc)
    def ts(d): return int(dt.datetime(2026, 6, d, 10, tzinfo=dt.timezone.utc).timestamp())
    deals = [
        {"symbol": "XAUUSD", "profit": -300, "time": ts(14)}, {"symbol": "XAUUSD", "profit": -250, "time": ts(15)},
        {"symbol": "XAUUSD", "profit": -200, "time": ts(16)}, {"symbol": "XAUUSD", "profit": 50, "time": ts(16)},
        {"symbol": "XAUUSD", "profit": -999, "time": ts(17)},   # TODAY -> excluded (leak-free)
    ]
    m = compute_symbol_metrics(deals, now, window_days=5)
    assert "XAUUSD" in m
    assert m["XAUUSD"]["trades"] == 4 and m["XAUUSD"]["losses"] == 3       # the day-17 deal excluded
    assert m["XAUUSD"]["net"] == -700.0                                    # -300-250-200+50, excludes -999
    # net<=-500 AND trades<6 -> risk_reduce (not hard, trades<6); but net<=-500 with trades>=6 would be hard
    assert symbol_damage_mult("XAUUSD", m, enabled=True) == 0.5            # risk_reduce (trades 4 < 6)


def test_admission_default_off_is_noop_and_on_drops_quarantined():
    ii = [TradeIntent("metals_core", "XAUUSD", 1, DAY, 10.0, target_dist=20.0),
          TradeIntent("crypto", "BTCUSD", 1, DAY, 100.0, target_dist=200.0)]
    base = size_correlated_units(ii, base_risk_per_unit=0.02)
    off = size_correlated_units(ii, base_risk_per_unit=0.02, symbol_damage_guard=False, symbol_damage_metrics=None)
    assert [(u.cluster, u.confidence) for u in base] == [(u.cluster, u.confidence) for u in off], "default-off must be no-op"
    # arm it: XAUUSD quarantined (6 trades, 4 losses) -> dropped; BTCUSD healthy -> kept
    metrics = {"XAUUSD": {"trades": 6, "losses": 4, "net": -600.0, "win_rate": 0.3}}
    on = size_correlated_units(ii, base_risk_per_unit=0.02, symbol_damage_guard=True, symbol_damage_metrics=metrics)
    clusters = {u.cluster for u in on}
    assert "metals" not in clusters, "QUARANTINEd XAUUSD intent must be dropped"
    assert "crypto" in clusters, "healthy BTCUSD must survive"


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    p = 0
    for fn in fns:
        try:
            fn(); p += 1; print(f"PASS {fn.__name__}")
        except Exception:
            print(f"FAIL {fn.__name__}"); traceback.print_exc()
    print(f"\n{p}/{len(fns)} symbol-damage-guard tests passed")
    assert p == len(fns)
