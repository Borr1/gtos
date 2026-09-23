"""Known-answer tests for the decay monitor."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.research_infra.validation_integrity.decay_monitor import (
    rolling_sharpe, decay_assessment, book_decay_report, _ols_slope,
)


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


def test_intact_edge():
    rng = _lcg(1)
    # constant positive-mean edge across the whole series -> INTACT
    s = [0.3 + _gauss(rng) for _ in range(400)]
    a = decay_assessment(s, window=60)
    assert a["verdict"] == "INTACT", a
    assert a["recent_sharpe"] > 0


def test_decaying_edge():
    rng = _lcg(2)
    # strong early, fading to weak-positive late, low noise so the signal dominates -> DECAYING
    s = []
    for i in range(400):
        mu = 0.8 - 0.8 * (i / 400.0)   # 0.8 -> 0.0 (steep), recent tail clearly weak
        s.append(mu + 0.25 * _gauss(rng))
    a = decay_assessment(s, window=60)
    assert a["verdict"] in ("DECAYING", "DEAD"), a
    assert a["rolling_slope"] < 0
    assert a["recent_vs_hist_ratio"] < 0.5


def test_dead_edge():
    rng = _lcg(3)
    # positive first 70%, negative last 30% -> recent sharpe <=0 -> DEAD
    s = []
    for i in range(400):
        mu = 0.4 if i < 280 else -0.3
        s.append(mu + _gauss(rng))
    a = decay_assessment(s, window=60)
    assert a["verdict"] == "DEAD", a
    assert a["recent_sharpe"] <= 0


def test_thin_series():
    a = decay_assessment([0.1, 0.2, -0.1, 0.05] * 5, window=60)  # n=20 < 40
    assert a["verdict"] == "THIN"


def test_rolling_and_slope():
    assert rolling_sharpe([1, 2, 3], 5) == []   # too short
    rs = rolling_sharpe([1.0] * 10 + [2.0] * 10, 5)
    assert len(rs) == 16
    assert _ols_slope([1, 2, 3, 4]) > 0
    assert _ols_slope([4, 3, 2, 1]) < 0


def test_book_report():
    rng = _lcg(9)
    series = {
        "intact": [0.3 + _gauss(rng) for _ in range(400)],
        "dead": [(0.4 if i < 280 else -0.3) + _gauss(rng) for i in range(400)],
    }
    rep = book_decay_report(series, window=60)
    assert rep["per_sleeve"]["intact"]["verdict"] == "INTACT"
    assert rep["per_sleeve"]["dead"]["verdict"] == "DEAD"
    assert rep["n_intact"] == 1 and rep["n_decaying_or_dead"] == 1


if __name__ == "__main__":
    for fn in [test_intact_edge, test_decaying_edge, test_dead_edge, test_thin_series,
               test_rolling_and_slope, test_book_report]:
        fn()
    print("decay_monitor: 6/6 known-answer tests passed")
