"""Known-answer tests for the sub-selection stability control (3rd selection-leak guard, cycles 30-32).

A genuine sub-group edge (one cluster really pays more, in-sample AND OOS) must be STABLE: concentrating
to the in-sample-best group beats the full population OOS across (feature, K, seed) specs. A noise edge
(returns independent of the features) must be flagged UNSTABLE — the in-sample-best group is a coin flip,
exactly the cycle-32 metals result (54% beat-rate).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.research_infra.validation_integrity.selection_stability import (
    subselection_stability, assert_subselection_robust,
    universe_robustness, assert_universe_robust)


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


def _build(n, seed, real_edge):
    """n trades; first half in-sample. Two latent feature groups (x sign). If real_edge, group A
    (x>0) pays +0.6 both windows; else returns are pure noise independent of features."""
    rng = _lcg(seed)
    feats, rets, mask = [], [], []
    for i in range(n):
        x = _gauss(rng)                       # latent group axis
        y = _gauss(rng)                       # noise feature
        z = _gauss(rng)                       # noise feature
        base = _gauss(rng)
        if real_edge:
            r = (0.6 if x > 0 else -0.1) + 0.5 * base
        else:
            r = 0.20 + base                   # mean +0.2, independent of x,y,z
        feats.append([x, y, z]); rets.append(r); mask.append(i < n // 2)
    return rets, feats, mask


def test_real_subgroup_edge_is_stable():
    rets, feats, mask = _build(600, seed=11, real_edge=True)
    rep = subselection_stability(rets, feats, mask, n_seeds=6)
    assert rep["verdict"] == "STABLE_SUBSELECTION", rep
    assert rep["beat_rate"] >= 0.75, rep
    assert rep["mean_oos_delta"] > 0, rep


def test_noise_subselection_is_unstable():
    rets, feats, mask = _build(600, seed=22, real_edge=False)
    rep = subselection_stability(rets, feats, mask, n_seeds=6)
    assert rep["verdict"] == "UNSTABLE_SELECTION", rep
    # coin-flip-ish beat-rate and ~zero mean improvement (the cycle-32 metals signature)
    assert rep["beat_rate"] < 0.75, rep
    assert abs(rep["mean_oos_delta"]) < 0.10, rep


def test_assert_guard_raises_on_unstable():
    rets, feats, mask = _build(600, seed=33, real_edge=False)
    raised = False
    try:
        assert_subselection_robust(rets, feats, mask, n_seeds=6)
    except AssertionError:
        raised = True
    assert raised, "guard must fail-closed on an unstable sub-selection"


def test_assert_guard_passes_on_real_edge():
    rets, feats, mask = _build(600, seed=44, real_edge=True)
    rep = assert_subselection_robust(rets, feats, mask, n_seeds=6)
    assert rep["verdict"] == "STABLE_SUBSELECTION", rep


def test_insufficient_sample_is_flagged():
    rep = subselection_stability([0.1] * 10, [[1.0, 2.0]] * 10, [True] * 5 + [False] * 5)
    assert rep["verdict"] == "INSUFFICIENT", rep


# ---- universe_robustness (4th guard, cycles 47-49) ----
# Model: each instrument has a true per-name edge. A REAL mechanism edge => most names positive =>
# any broad subset is positive. A SUBSET artifact => only a few hand-picked names positive, the rest
# negative => the full universe / random subsets are negative (the vol_climax_FX pattern).
def _make_eval(name_edge):
    def eval_on_universe(univ):
        vals = [name_edge[s] for s in univ]
        return sum(vals) / len(vals)
    return eval_on_universe


def test_real_universe_edge_is_robust():
    # 20 names, broadly positive (a mechanism)
    edge = {f"S{i}": (0.10 if i % 5 else -0.02) for i in range(20)}  # 16 pos / 4 neg
    rep = universe_robustness(_make_eval(edge), list(edge), n_draws=24, seed=1)
    assert rep["verdict"] == "ROBUST_UNIVERSE", rep
    assert rep["full_universe_metric"] > 0 and rep["subset_positive_rate"] >= 0.6, rep


def test_subset_artifact_is_flagged():
    # 28 names; only a hand-picked 6 are strongly positive, the other 22 negative -> full universe neg
    edge = {f"S{i}": (0.5 if i < 6 else -0.15) for i in range(28)}
    rep = universe_robustness(_make_eval(edge), list(edge), n_draws=24, seed=2)
    assert rep["verdict"] == "SUBSET_SELECTION_ARTIFACT", rep
    assert rep["full_universe_metric"] < 0, rep


def test_assert_universe_guard_raises_on_artifact():
    edge = {f"S{i}": (0.5 if i < 6 else -0.15) for i in range(28)}
    raised = False
    try:
        assert_universe_robust(_make_eval(edge), list(edge), n_draws=12, seed=3)
    except AssertionError:
        raised = True
    assert raised, "guard must fail-closed on an instrument-subset artifact"
