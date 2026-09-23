"""test_metals_confluence_gate.py — assert the A8 gate reproduces the verified confluence lift on real metals.

Runs the gate over the 482-trade SELECTION_FEATURE_STORE and asserts: (1) gate-ON every-split meanR improves and
sealed reproduces the verified ~0.67 (vs ~0.227 baseline); (2) gate-OFF (default) admits all trades unchanged.
"""
import json, os, statistics as st
import sys

import pytest
# NOTE 2026-07-26: a hardcoded sys.path.insert(0, "/Users/borr/Documents/gtos/repo/
# ai-trading-agent") was removed here. It prepended a DIFFERENT, stale checkout, so this
# file silently tested that repo instead of the working tree whenever it ran in isolation
# (in a full-suite run sys.modules was already populated, so the same tests exercised the
# real code and could disagree). Tests must import the tree they are checked out in.
from src.components.ultimate_book.metals_confluence_gate import metals_confluence

# ENVIRONMENT/DATA REPAIR 2026-08-25: the 482-trade feature store was only ever a
# machine-local research artifact — never committed (`git log --all` finds no blob; not
# in /Users/borr/GTOSActive/repo either), and the original hardcoded checkout path no
# longer contains the route dir, so this module died at import with FileNotFoundError
# and took the whole file out at COLLECTION. The gate code under test is imported from
# THIS tree (the note above still binds — only frozen DATA comes from outside it); the
# one surviving copy of the store on this machine is the duplicate checkout
# `ai-trading-agent 2` (482 rows, field-complete, verified 2026-08-25). Resolve in
# order; if every candidate is absent, SKIP at collection with the named paths — never
# fail import, never pass silently.
_ROUTE_REL = ("research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
              "/SELECTION_FEATURE_STORE.jsonl")
_STORE_CANDIDATES = [
    "/Users/borr/Documents/gtos/repo/ai-trading-agent/" + _ROUTE_REL,
    "/Users/borr/Documents/gtos/repo/ai-trading-agent 2/" + _ROUTE_REL,
    os.path.join(os.path.dirname(__file__), "..", "..", _ROUTE_REL),
]
STORE = next((p for p in _STORE_CANDIDATES if os.path.isfile(p)), None)
if STORE is None:
    pytest.skip(
        "requires data: SELECTION_FEATURE_STORE.jsonl (A8 metals 482-trade feature "
        "store; machine-local, never committed). Looked in: "
        + "; ".join(_STORE_CANDIDATES),
        allow_module_level=True,
    )
rows = [json.loads(l) for l in open(STORE)]
def spl(r): return r["split"].lower()
def mean(rs): return st.fmean([r["realized_r"] for r in rs]) if rs else None


def _gate_on(r):
    return metals_confluence(htf_slope_norm=r["htf_slope_norm"], mom_20_atr=r["mom_20_atr"],
                             fvg_freshness_bars=r["fvg_freshness_bars"], ac60=r["ac60"],
                             atr_ratio=r["atr_ratio"], session_hour=r["session_hour"], enabled=True).passed


def test_gate_on_reproduces_a8_every_split_lift():
    for s in ["train", "oos", "sealed"]:
        rs = [r for r in rows if spl(r) == s]
        base = mean(rs); conf = mean([r for r in rs if _gate_on(r)])
        assert conf > base, f"{s}: confluence {conf:.3f} !> baseline {base:.3f}"
    # sealed reproduces the verified ~0.674 (within tolerance)
    sealed = [r for r in rows if spl(r) == "sealed"]
    sealed_conf = mean([r for r in sealed if _gate_on(r)])
    assert abs(sealed_conf - 0.674) < 0.03, f"sealed confluence {sealed_conf:.3f} != verified ~0.674"


def test_default_off_admits_everything():
    # enabled=False => passes regardless of features (sleeve admits as deployed)
    for r in rows[:50]:
        res = metals_confluence(htf_slope_norm=-9, mom_20_atr=-9, fvg_freshness_bars=999, ac60=-9,
                                atr_ratio=9.9, session_hour=15, enabled=False)
        assert res.passed is True
    # and a clearly-failing trade is rejected only when enabled
    res_on = metals_confluence(htf_slope_norm=-9, mom_20_atr=-9, fvg_freshness_bars=999, ac60=-9,
                               atr_ratio=9.9, session_hour=15, enabled=True)
    assert res_on.passed is False and res_on.score == 0


def test_frequency_kept_reasonable():
    kept = sum(1 for r in rows if _gate_on(r))
    assert 0.30 <= kept / len(rows) <= 0.55, f"kept {kept}/{len(rows)} out of expected ~43% band"


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    p = 0
    for fn in fns:
        try: fn(); p += 1; print(f"PASS {fn.__name__}")
        except Exception: print(f"FAIL {fn.__name__}"); traceback.print_exc()
    # show the reproduced numbers
    for s in ["train", "oos", "sealed"]:
        rs = [r for r in rows if spl(r) == s]
        print(f"  {s:6s} baseline {mean(rs):+.3f} (n{len(rs)}) -> confluence {mean([r for r in rs if _gate_on(r)]):+.3f} "
              f"(n{sum(1 for r in rs if _gate_on(r))})")
    print(f"\n{p}/{len(fns)} metals-confluence-gate tests passed")
    assert p == len(fns)
