"""Known-answer tests for the portfolio-contribution diversifier gate."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.research_infra.validation_integrity.portfolio_contribution import (
    incremental_sharpe, contribution_bootstrap_ci, certify_diversifier, _corr_on_overlap,
)


def _lcg(seed):
    s = [seed & 0xFFFFFFFF]
    def nxt():
        s[0] = (1664525 * s[0] + 1013904223) % (2 ** 32)
        return s[0] / 2 ** 32
    return nxt


def _gauss(rng):
    # Box-Muller from a uniform LCG
    import math as m
    u1 = max(rng(), 1e-12); u2 = rng()
    return m.sqrt(-2 * m.log(u1)) * m.cos(2 * m.pi * u2)


def _days(n, start=0):
    return [f"20{15 + (start + i) // 365:02d}-{((start + i) % 365) // 31 + 1:02d}-{((start + i) % 31) + 1:02d}" + f"_{start+i}" for i in range(n)]


def _book(n=1200, seed=1):
    rng = _lcg(seed)
    days = [f"D{i:05d}" for i in range(n)]
    return {days[i]: 0.10 + _gauss(rng) for i in range(n)}  # mean 0.10, sd ~1


def test_uncorrelated_positive_sleeve_certifies():
    book = _book(seed=1)
    rng = _lcg(999)
    # independent positive sleeve on the SAME days (uncorrelated to book), strong mean so the
    # paired-bootstrap delta-Sharpe CI excludes 0 AND the held-out slice stays positive
    cand = {d: 0.30 + _gauss(rng) for d in book}
    res = certify_diversifier(book, cand, standalone_edge_ok=True, regime_clean=True,
                              sealed_start="D01000", weight=0.5, n_boot=1500)
    assert res["incremental"]["delta"] > 0, res["incremental"]
    corr, _ = _corr_on_overlap(book, cand)
    assert abs(corr) < 0.35
    assert res["checks"]["contribution_significant"]["pass"] is True, res["bootstrap"]
    assert res["verdict"] == "CERTIFIED_DIVERSIFIER", res["failed_checks"]


def test_duplicate_of_book_rejected_low_corr():
    book = _book(seed=2)
    cand = dict(book)  # perfect duplicate -> corr 1.0
    res = certify_diversifier(book, cand, standalone_edge_ok=True, regime_clean=True,
                              sealed_start="D01000", weight=0.5, n_boot=800)
    assert res["checks"]["low_correlation"]["pass"] is False
    assert res["verdict"] == "NOT_CERTIFIED"


def test_pure_noise_sleeve_rejected():
    book = _book(seed=3)
    rng = _lcg(7)
    cand = {d: _gauss(rng) for d in book}  # zero-mean noise
    res = certify_diversifier(book, cand, standalone_edge_ok=True, regime_clean=True,
                              sealed_start="D01000", weight=0.5, n_boot=1500)
    # zero-mean uncorrelated noise adds variance without return -> non-positive OR insignificant delta
    assert (res["checks"]["positive_contribution"]["pass"] is False
            or res["checks"]["contribution_significant"]["pass"] is False), res["checks"]
    assert res["verdict"] == "NOT_CERTIFIED"


def test_contaminated_or_nonedge_candidate_rejected():
    book = _book(seed=4)
    rng = _lcg(11)
    cand = {d: 0.10 + _gauss(rng) for d in book}
    # regime-contaminated -> reject even with positive contribution
    r1 = certify_diversifier(book, cand, standalone_edge_ok=True, regime_clean=False,
                             sealed_start="D01000", weight=0.5, n_boot=800)
    assert r1["checks"]["regime_clean"]["pass"] is False and r1["verdict"] == "NOT_CERTIFIED"
    # not a genuine standalone edge -> reject
    r2 = certify_diversifier(book, cand, standalone_edge_ok=False, regime_clean=True,
                             sealed_start="D01000", weight=0.5, n_boot=800)
    assert r2["checks"]["genuine_edge"]["pass"] is False and r2["verdict"] == "NOT_CERTIFIED"


if __name__ == "__main__":
    test_uncorrelated_positive_sleeve_certifies()
    test_duplicate_of_book_rejected_low_corr()
    test_pure_noise_sleeve_rejected()
    test_contaminated_or_nonedge_candidate_rejected()
    print("portfolio_contribution: 4/4 known-answer tests passed")
