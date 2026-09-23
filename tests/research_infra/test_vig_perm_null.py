"""Known-answer tests for the permutation-null + stationary-bootstrap module.

Run directly:   /opt/homebrew/bin/python3 tests/research_infra/test_vig_perm_null.py
Or via pytest:  pytest tests/research_infra/test_vig_perm_null.py

The asserts encode the *required* statistical behavior:
  (1) iid zero-mean noise   -> block_permutation_test p_value HIGH (> 0.10)
  (2) clear positive drift  -> block_permutation_test p_value LOW  (< 0.01)
  (3) stationary_bootstrap_ci excludes 0 on drift, includes 0 on noise.

Data seeds are fixed (noise=4, drift=100) so the outcomes are deterministic;
the permutation/bootstrap seed is the module default 12345.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from research_infra.validation_integrity.perm_null import (  # noqa: E402
    block_permutation_test,
    stationary_bootstrap_ci,
    normal_cdf,
    normal_ppf,
)

# Fixed data seeds chosen so |observed| on noise is small and drift is strong.
NOISE_SEED = 4
DRIFT_SEED = 100


def _noise(n=800):
    return np.random.default_rng(NOISE_SEED).standard_normal(n)


def _drift(n=400, mu=0.5):
    return mu + np.random.default_rng(DRIFT_SEED).standard_normal(n)


# --------------------------------------------------------------------------- #
# Normal CDF / inverse-CDF (erf-based, no scipy).                             #
# --------------------------------------------------------------------------- #
def test_normal_helpers_known_values():
    assert abs(normal_cdf(0.0) - 0.5) < 1e-12
    assert abs(normal_cdf(1.959963985) - 0.975) < 1e-9
    assert abs(normal_cdf(-1.959963985) - 0.025) < 1e-9
    # Inverse round-trips and matches the textbook 1.96 quantile.
    assert abs(normal_ppf(0.975) - 1.959963985) < 1e-6
    assert abs(normal_ppf(0.025) + 1.959963985) < 1e-6
    for q in (0.01, 0.1, 0.37, 0.5, 0.63, 0.9, 0.99):
        assert abs(normal_cdf(normal_ppf(q)) - q) < 1e-10


# --------------------------------------------------------------------------- #
# (1) iid zero-mean noise -> NOT significant.                                 #
# --------------------------------------------------------------------------- #
def test_permutation_noise_not_significant():
    res = block_permutation_test(_noise(), block=5, n_perm=5000,
                                 stat="sharpe", seed=12345)
    assert res["p_value"] > 0.10, res
    # Sign-flip null must be centered near zero and non-degenerate.
    assert abs(res["null_mean"]) < 0.05
    assert res["null_std"] > 0.0
    # Gaussian cross-check agrees with the empirical permutation p.
    assert abs(res["p_value"] - res["p_value_normal"]) < 0.05


# --------------------------------------------------------------------------- #
# (2) clear positive drift -> significant.                                    #
# --------------------------------------------------------------------------- #
def test_permutation_drift_significant():
    res = block_permutation_test(_drift(), block=5, n_perm=5000,
                                 stat="sharpe", seed=12345)
    assert res["p_value"] < 0.01, res
    assert res["observed"] > res["null_p95"]  # observed beyond the 95th pct null

    # Also significant for the 'mean' statistic.
    res_mean = block_permutation_test(_drift(), block=5, n_perm=5000,
                                      stat="mean", seed=12345)
    assert res_mean["p_value"] < 0.01, res_mean


# --------------------------------------------------------------------------- #
# (3) stationary bootstrap CI: excludes 0 on drift, includes 0 on noise.      #
# --------------------------------------------------------------------------- #
def test_bootstrap_ci_drift_excludes_zero():
    ci = stationary_bootstrap_ci(_drift(), stat_fn_name="mean", block=5,
                                 n_boot=5000, alpha=0.05, seed=12345)
    assert ci["ci_low"] > 0.0, ci
    assert ci["ci_low"] < ci["point"] < ci["ci_high"]


def test_bootstrap_ci_noise_includes_zero():
    ci = stationary_bootstrap_ci(_noise(), stat_fn_name="mean", block=5,
                                 n_boot=5000, alpha=0.05, seed=12345)
    assert ci["ci_low"] < 0.0 < ci["ci_high"], ci


def test_bootstrap_ci_sharpe_option():
    ci = stationary_bootstrap_ci(_drift(), stat_fn_name="sharpe", block=5,
                                 n_boot=5000, alpha=0.05, seed=12345)
    assert ci["ci_low"] > 0.0, ci  # positive-drift Sharpe CI excludes 0


# --------------------------------------------------------------------------- #
# Determinism + edge cases.                                                   #
# --------------------------------------------------------------------------- #
def test_determinism():
    a = block_permutation_test(_drift(), seed=12345)
    b = block_permutation_test(_drift(), seed=12345)
    assert a == b
    c = stationary_bootstrap_ci(_drift(), seed=12345)
    d = stationary_bootstrap_ci(_drift(), seed=12345)
    assert c == d


def test_edge_cases():
    for bad in ([], np.array([])):
        try:
            block_permutation_test(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError on empty series")
    try:
        stationary_bootstrap_ci([1.0, 2.0, np.nan])
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError on non-finite series")


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    # Echo the headline numbers for the record.
    rn = block_permutation_test(_noise(), seed=12345)
    rd = block_permutation_test(_drift(), seed=12345)
    cn = stationary_bootstrap_ci(_noise(), seed=12345)
    cd = stationary_bootstrap_ci(_drift(), seed=12345)
    print(f"\nnoise: perm_p={rn['p_value']:.3f}  CI=({cn['ci_low']:+.4f},{cn['ci_high']:+.4f})")
    print(f"drift: perm_p={rd['p_value']:.5f} obs_sharpe={rd['observed']:.4f} "
          f"CI=({cd['ci_low']:+.4f},{cd['ci_high']:+.4f})")
    print("\nALL TESTS PASSED")


if __name__ == "__main__":
    _run_all()
