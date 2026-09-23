"""Session AO (B1304): a p one resolution step above its own structural floor passes the
significance gate with no flag, and that is how a regime-conditioned cell reached an ADMIT.

THE ARITHMETIC
--------------
`stats.perm_p_floor(n_obs, block, n_perm)` returns the smallest p a block sign-flip test can
attain: with `B = ceil(n_obs / block)` blocks there are `2**B` distinct sign assignments, so the
floor is `(1 + n_perm * 2**-B) / (n_perm + 1)`.

**`gate.py:849-863` does NOT compare `p_raw` to `p_floor`.** It refuses (NOT_EVALUABLE,
`p_floor_binds=True`) only when `p_floor >= spec.alpha` — when NO p on the series could ever be
significant. At 8 blocks the floor is 0.004006 against alpha 0.10, so that guard is 25x from
firing and NOTHING in the gate relates the observed p to its own resolution. AO's first draft of
this docstring said the gate compares `p_raw <= p_floor`; it does not, and the true version is
worse for the gate.

AO measured `sub_xvol_pullback @ target_4R + ac60 >= median` on RECORDED@mid at 16 OOS days,
block 2, so 8 blocks: floor 0.004006, observed p 0.004200, headroom **1.048x**, verdict ADMIT at
BH rank 2. Every other arm in that session ran 7x-659x above its floor.

AND THE FLOOR IS AN EXPECTATION, NOT A BOUND — WHICH IS THE SHARPER FACT
-----------------------------------------------------------------------
`perm_null.py:201-202` computes `p = (1 + ge)/(n_perm + 1)` where `ge` counts draws whose null
statistic >= the observation. When the observation is the maximum over all `2**B` achievable sign
assignments, `ge` is simply the number of draws that duplicated the identity assignment:
`Binomial(n_perm, 2**-B)`. At B = 8, n_perm = 10,000 that is mean 39.06, sd 6.24, so p is
0.004006 +/- 0.000624 — a COUNT OF DUPLICATE DRAWS rather than a measure of evidence, landing
either side of the floor by luck. AO's seed sweep confirms it on the production path: the same
cell over 20 permutation seeds gives p in [0.003500, 0.005799] with sd **0.000658** against the
0.000624 this predicts, and its verdict flips on **4 of 20 seeds**. The controls do not move —
its ungated parent is REJECT at 20/20 and `mx_btcusd @ target_5R` is ADMIT at 20/20 with p
in [0.000700, 0.002000].

WHAT IS PINNED HERE
-------------------
The arithmetic (so the numbers in AO's report are checkable without its artifacts), the
mechanism (fewer OOS days -> fewer blocks -> a higher floor, which is why a regime FILTER can
buy a smaller p by destroying the resolution that would justify it), and the gap (the gate is
silent at 1.048x). If a future session adds a headroom floor to `significance`, the last test
here is the one that should start failing, and its message says so.
"""

from __future__ import annotations

import math

import pytest

from src.research_infra.walkforward import stats as S
from src.research_infra.walkforward.options import OPTIONS

#: AO's pair-admitting arm, from `REGIME_CONDITIONING_V1.json`.
AO_N_OOS_DAYS = 16
AO_BLOCK_DAYS = 2
AO_P_RAW = 0.004199580041995801
#: and the arm it was conditioned out of.
UNGATED_N_OOS_DAYS = 28
UNGATED_BLOCK_DAYS = 3          # 28 days / 10 blocks
RANK_2_BAR_AT_39 = 0.20 / 39


def test_the_floor_arithmetic_reproduces_ao_s_numbers():
    n_perm = OPTIONS["B_balanced"].n_permutation
    fl = S.perm_p_floor(AO_N_OOS_DAYS, AO_BLOCK_DAYS, n_perm)
    assert fl["n_blocks"] == 8, fl
    assert math.isclose(fl["p_floor"], 0.004005849415058494, rel_tol=1e-12), fl
    headroom = AO_P_RAW / fl["p_floor"]
    assert 1.04 < headroom < 1.06, headroom


def test_the_admitting_window_at_eight_blocks_is_one_resolution_step_wide():
    """An 8-block test can only produce a p below the rank-2 bar by sitting on its floor."""
    n_perm = OPTIONS["B_balanced"].n_permutation
    floor = S.perm_p_floor(AO_N_OOS_DAYS, AO_BLOCK_DAYS, n_perm)["p_floor"]
    assert floor < RANK_2_BAR_AT_39, (floor, RANK_2_BAR_AT_39)
    # the whole admissible interval, in units of the smallest step the test can take
    step = 1.0 / (n_perm + 1)
    width_in_steps = (RANK_2_BAR_AT_39 - floor) / step
    assert width_in_steps < 15, width_in_steps
    # and rank 1 is UNREACHABLE at 8 blocks, which is the sharper statement
    assert floor > 0.10 / 39, (floor, 0.10 / 39)


def test_fewer_oos_days_raises_the_floor_which_is_the_conditioning_trap():
    """The mechanism, as a monotone fact: halve the days and the floor rises.

    This is why a regime FILTER can look like a significance repair. It removes trades, which
    removes OOS DAYS, which removes blocks, which raises the smallest attainable p -- while the
    p it reports falls because the surviving days are the better ones.
    """
    n_perm = OPTIONS["B_balanced"].n_permutation
    floors = [S.perm_p_floor(d, 2, n_perm)["p_floor"] for d in (8, 16, 32, 64, 128)]
    assert floors == sorted(floors, reverse=True), floors
    ungated = S.perm_p_floor(UNGATED_N_OOS_DAYS, UNGATED_BLOCK_DAYS, n_perm)
    conditioned = S.perm_p_floor(AO_N_OOS_DAYS, AO_BLOCK_DAYS, n_perm)
    assert ungated["n_blocks"] == 10 and conditioned["n_blocks"] == 8
    assert conditioned["p_floor"] > ungated["p_floor"] * 3, (
        conditioned["p_floor"], ungated["p_floor"])


def test_the_gate_s_only_floor_guard_is_p_floor_vs_alpha_not_p_raw_vs_p_floor():
    """The guard that exists, and the one that does not.

    `gate.py:849-863` refuses only when `p_floor >= spec.alpha`. Nothing in the gate compares
    the observed p to its own resolution. Asserted by reproducing both conditions on AO's
    numbers, so a reader can see which one is 25x from firing.
    """
    n_perm = OPTIONS["B_balanced"].n_permutation
    spec = OPTIONS["B_balanced"]
    floor = S.perm_p_floor(AO_N_OOS_DAYS, AO_BLOCK_DAYS, n_perm)["p_floor"]
    # the guard that EXISTS: floor vs alpha. Nowhere near firing.
    assert floor < spec.alpha
    assert spec.alpha / floor > 20, spec.alpha / floor
    # the guard that DOES NOT exist: p_raw vs its own floor. 1.048x, and nothing reads it.
    assert 1.0 < AO_P_RAW / floor < 2.0, AO_P_RAW / floor
    # the proposal in AO's repair row: a 2x headroom floor catches this arm and nothing else in
    # that session (every other arm ran 7x-659x).
    assert 0.007999200079992 / S.perm_p_floor(
        UNGATED_N_OOS_DAYS, UNGATED_BLOCK_DAYS, n_perm)["p_floor"] > 2.0


def test_the_p_is_a_count_of_duplicate_draws_and_its_sd_predicts_ao_s_seed_sweep():
    """The floor is an EXPECTATION over `Binomial(n_perm, 2**-B)`, not a bound.

    If the observation is the extreme sign assignment, `ge` is the number of draws that
    duplicated it, so `sd[p] = sqrt(n_perm * q * (1-q)) / (n_perm + 1)` with `q = 2**-B`. AO
    measured sd 0.000658 over 20 seeds on the production path; this predicts 0.000624. Pinned
    because the agreement is what turns "the p is at its floor" from a description into a
    mechanism.
    """
    n_perm = OPTIONS["B_balanced"].n_permutation
    B = S.perm_p_floor(AO_N_OOS_DAYS, AO_BLOCK_DAYS, n_perm)["n_blocks"]
    q = 2.0 ** -B
    sd_p = math.sqrt(n_perm * q * (1 - q)) / (n_perm + 1)
    assert math.isclose(sd_p, 0.000623, abs_tol=2e-6), sd_p
    AO_MEASURED_SEED_SD = 0.0006581704627195884
    assert abs(AO_MEASURED_SEED_SD - sd_p) / sd_p < 0.10, (AO_MEASURED_SEED_SD, sd_p)
    # and the verdict boundary sits inside that noise
    assert abs(RANK_2_BAR_AT_39 - S.perm_p_floor(
        AO_N_OOS_DAYS, AO_BLOCK_DAYS, n_perm)["p_floor"]) / sd_p < 2.0


@pytest.mark.parametrize("opt", ["A_strict", "B_balanced", "C_exploratory"])
def test_no_option_declares_a_p_floor_headroom_requirement(opt):
    """The absence AO's repair row is filed against. If a `min_p_floor_headroom` field lands on
    `GateSpec`, this test is the one that should start failing."""
    spec = OPTIONS[opt]
    assert not hasattr(spec, "min_p_floor_headroom"), (
        f"{opt} now carries a p-floor headroom requirement -- AO's repair row "
        "SIGNIFICANCE_PASSES_A_P_ONE_STEP_ABOVE_ITS_STRUCTURAL_FLOOR has been actioned. "
        "Update this test to assert the threshold rather than its absence."
    )
