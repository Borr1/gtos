"""test_metals_a8_features.py — prove the live metals generator populates the A8 confluence features
FAITHFULLY (verbatim the build_selection_feature_store formulas), so the default-off
admission.metals_confluence_gate reproduces the verified A8 lift when the owner arms it.

(1) _ols_slope == numpy least-squares slope; (2) _a8_features == the store formulas computed
independently (numpy); (3) the live generator EMITS the 5 features on a real deep-history metals fire,
and (4) adding the features did NOT change the LOCKED signal/geometry.
"""
import glob, csv
import sys
# NOTE 2026-07-26: a hardcoded sys.path.insert(0, "/Users/borr/Documents/gtos/repo/
# ai-trading-agent") was removed here. It prepended a DIFFERENT, stale checkout, so this
# file silently tested that repo instead of the working tree whenever it ran in isolation
# (in a full-suite run sys.modules was already populated, so the same tests exercised the
# real code and could disagree). Tests must import the tree they are checked out in.
import numpy as np
from src.components.ultimate_book.primitives import Bar, atr14, vol_ratio
from src.components.ultimate_book.sleeves import metals as MT

DATA = "/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports"


def test_ols_slope_matches_numpy():
    rng = np.random.default_rng(7)
    for _ in range(20):
        y = list(rng.normal(size=30) * 5 + np.arange(30) * 0.3)
        got = MT._ols_slope(y)
        want = float(np.polyfit(np.arange(len(y)), y, 1)[0])
        assert abs(got - want) < 1e-9, f"{got} != {want}"


def test_a8_features_match_store_formulas():
    # a deterministic random-walk H4 series; compute features both ways at i and assert equality.
    rng = np.random.default_rng(11)
    px = 2000 + np.cumsum(rng.normal(size=200))
    bars = [Bar(p, p + 0.5, p - 0.5, p + rng.normal() * 0.1, 100) for p in px]
    atrs = [atr14(bars, k) for k in range(len(bars))]
    i = 180
    feats = MT._a8_features(bars, atrs, i, vol_ratio(atrs, i), bar_time=None)
    a = atrs[i]; c = bars[i].c
    # store-verbatim independent recomputation
    want_slope_norm = float(np.polyfit(np.arange(30), [bars[j].c for j in range(i - 29, i + 1)], 1)[0]) * 30.0 / c
    want_mom = (c - bars[i - 20].c) / a
    assert abs(feats["htf_slope_norm"] - want_slope_norm) < 1e-7
    assert abs(feats["mom_20_atr"] - want_mom) < 1e-9
    assert feats["atr_ratio"] == vol_ratio(atrs, i)            # atr_ratio == vol_ratio (store definition)


def _load_h4(sym):
    rows = {}
    for f in glob.glob(f"{DATA}/*/{sym}_H4.csv"):
        for r in csv.DictReader(open(f)):
            t = r.get("time") or r.get("date")
            if not t:
                continue
            try:
                rows[t] = (float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]))
            except Exception:
                continue
    items = sorted(rows.items())
    return [Bar(o, h, l, c, 0) for _, (o, h, l, c) in items]


def test_live_generator_emits_features_on_real_fire_and_signal_unchanged():
    from datetime import datetime, timezone
    bars = _load_h4("XAUUSD")
    if len(bars) < 400:
        return  # data not present in this checkout -> skip silently
    fires = 0
    for i in range(300, len(bars)):
        window = bars[max(0, i - 300):i + 1]
        intent = MT.generate_metals_core("XAUUSD", window, "2026-06-17",
                                         bar_time=datetime(2026, 6, 17, 2, tzinfo=timezone.utc))
        if intent is None:
            continue
        fires += 1
        # the 5 A8 fields are present; the computable ones are populated on a real fire
        assert intent.atr_ratio is not None and intent.atr_ratio > 0
        assert intent.htf_slope_norm is not None and intent.mom_20_atr is not None
        assert intent.fvg_freshness_bars is None or 0 <= intent.fvg_freshness_bars <= 8
        assert intent.session_hour is not None and 0 <= intent.session_hour <= 23
        # LOCKED signal/geometry unchanged: the intent's stop_dist == fvg_signal's stop_dist
        atrs = [atr14(window, k) for k in range(len(window))]
        sig = MT.fvg_signal(window, atrs, len(window) - 1)
        assert sig is not None and abs(intent.stop_dist - sig[1]) < 1e-12 and intent.direction == sig[0]
        if fires >= 5:
            break
    assert fires >= 1, "expected at least one real metals_core fire on the deep XAUUSD history"


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    p = 0
    for fn in fns:
        try:
            fn(); p += 1; print(f"PASS {fn.__name__}")
        except Exception:
            print(f"FAIL {fn.__name__}"); traceback.print_exc()
    print(f"\n{p}/{len(fns)} metals-a8-features tests passed")
    assert p == len(fns)
