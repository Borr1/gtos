"""Known-answer tests for the edge-factory pipeline decision logic."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.research_infra.validation_integrity.edge_factory import certify_candidate, factory_run


def _lcg(seed):
    s = [seed & 0xFFFFFFFF]
    def nxt():
        s[0] = (1664525 * s[0] + 1013904223) % (2 ** 32)
        return s[0] / 2 ** 32
    return nxt


def _gauss(rng):
    import math
    u1 = max(rng(), 1e-12); u2 = rng()
    return math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)


def _isodates(n, start=(2016, 1, 1)):
    from datetime import date, timedelta
    d0 = date(*start)
    return [(d0 + timedelta(days=i)).isoformat() for i in range(n)]


SEALED = "2018-02-01"  # ~last 25% of a 2016-01-01-start 1000-day series (ends ~2018-09)


def _book(n=1000, seed=1):
    rng = _lcg(seed)
    return {d: 0.10 + _gauss(rng) for d in _isodates(n)}


def test_integrate_genuine_uncorrelated_positive():
    book = _book(seed=1)
    rng = _lcg(777)
    # strong, genuine, uncorrelated, positive sleeve -> INTEGRATE
    cand = {d: 0.30 + _gauss(rng) for d in book}
    r = certify_candidate(cand, book, n_trials=100, sealed_start=SEALED, sr_variance=1e-3,
                          weight=0.35, perm_n=800, n_boot=1500)
    assert r["genuine_edge"]["pass"] is True, r["genuine_edge"]
    assert r["decision"] == "INTEGRATE", r


def test_reject_pure_noise():
    book = _book(seed=2)
    rng = _lcg(5)
    cand = {d: _gauss(rng) for d in book}  # zero-mean noise -> not a genuine edge
    r = certify_candidate(cand, book, n_trials=100, sealed_start=SEALED, sr_variance=1e-3,
                          perm_n=800, n_boot=1200)
    assert r["decision"] == "REJECT", r


def test_map_conditional_genuine_but_correlated_duplicate():
    book = _book(seed=3)
    # a near-duplicate of the book: genuine positive edge but corr ~1 -> diversifier fails -> not INTEGRATE
    cand = {d: v + 0.01 for d, v in book.items()}
    r = certify_candidate(cand, book, n_trials=100, sealed_start=SEALED, sr_variance=1e-3,
                          perm_n=800, n_boot=1200)
    assert r["decision"] in ("MAP-CONDITIONAL", "REJECT"), r
    assert r["decision"] != "INTEGRATE"


def test_factory_run_summary():
    book = _book(seed=4)
    rng = _lcg(11)
    cands = {
        "good": {d: 0.30 + _gauss(rng) for d in book},
        "noise": {d: _gauss(rng) for d in book},
    }
    rep = factory_run(cands, book, n_trials=100, sealed_start=SEALED, sr_variance=1e-3,
                      perm_n=600, n_boot=1000)
    assert rep["results"]["good"]["decision"] == "INTEGRATE"
    assert rep["results"]["noise"]["decision"] == "REJECT"
    assert rep["n_integrate"] == 1 and rep["n_reject"] == 1


if __name__ == "__main__":
    for fn in [test_integrate_genuine_uncorrelated_positive, test_reject_pure_noise,
               test_map_conditional_genuine_but_correlated_duplicate, test_factory_run_summary]:
        fn()
    print("edge_factory: 4/4 known-answer tests passed")
