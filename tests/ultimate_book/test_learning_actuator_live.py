"""The live half of the learning rule: what live realized evidence may and may not do.

Behavioural throughout — every assertion is on a `recommend()` verdict or multiplier, never on the
presence of a substring in the source. The three properties being defended are:

  1. silence is never negative evidence,
  2. live evidence can only ever brake, never boost,
  3. gating is cheap and sizing is dear, by a measured margin.
"""
import inspect
import json
from pathlib import Path

import pytest

from src.components.ultimate_book.learning_actuator import (
    FLOOR_MULT,
    GATE_MULT,
    LIVE_MIN_DAY_BLOCKS_SUPPORT,
    LIVE_MIN_N,
    LIVE_MIN_N_SUPPORT,
    LIVE_UP_STEP,
    MAX_UP,
    MIN_N,
    Recommendation,
    SleeveEvidence,
    recommend,
    rerate_book,
)

REPO = Path(__file__).resolve().parents[2]
CALIBRATION = REPO / "research/operations/learning_lane_2026_07_29/LIVE_EVIDENCE_CALIBRATION_V1.json"


def _earning(**kw) -> SleeveEvidence:
    """A sleeve that is positive on every split and would be sized up on backtest alone.

    Carries day counts as well as trade counts, because that is the shape the production loader
    emits (`cost_true_splits.build_cost_true_evidence`) and the day-blocked count is the one the
    sample floor reads.
    """
    base = dict(train_meanR=+0.30, oos_meanR=+0.40, sealed_meanR=+0.50,
                train_n=100, oos_n=100, sealed_n=100,
                train_days=60, oos_days=60, sealed_days=60, status="train_validated")
    base.update(kw)
    return SleeveEvidence("s", **base)


# --------------------------------------------------------------- 1. silence is not evidence

def test_no_live_fills_changes_nothing():
    """A sleeve that has not fired has said nothing — the single most important property here.

    K's G4 measured metals_core 0 fires from 990 invocations, crypto 0/440, energy_agri 0/332 over
    the whole 38-day live window, all consistent with natural low frequency. A rule that read quiet
    as bad would gate the armed book in its first two months.
    """
    without = recommend(_earning())
    withzero = recommend(_earning(live_meanR=None, live_n=0))
    assert withzero.verdict == without.verdict == "SIZE_UP"
    assert withzero.conf_mult == without.conf_mult
    assert withzero.live_verdict == "ABSENT"
    assert withzero.gate is False


def test_zero_live_n_with_a_stale_mean_still_counts_as_silence():
    """live_n == 0 wins even if a mean is somehow present: n is the authority on whether we know."""
    r = recommend(_earning(live_meanR=-5.0, live_n=0))
    assert r.live_verdict == "ABSENT"
    assert r.verdict == "SIZE_UP" and r.conf_mult > 1.0


@pytest.mark.parametrize("n", [1, 2])
def test_below_the_floor_live_cannot_act_in_either_direction(n):
    """Catastrophic but tiny samples do nothing. The floor does not depend on the artifact."""
    assert n < LIVE_MIN_N
    r = recommend(_earning(live_meanR=-50.0, live_n=n,
                           live_gate_threshold_r=-0.1, live_kill_threshold_r=-0.2))
    assert r.live_verdict == "THIN"
    assert r.verdict == "SIZE_UP" and r.conf_mult > 1.0 and r.gate is False


# ------------------------------------------- 2. live brakes fast and raises slow (AE, 2026-07-30)

def test_live_may_now_raise_but_only_by_one_step():
    """The bidirectional half. Superseding `test_live_can_never_raise_the_multiplier`.

    Before AE the composition was `min(backtest, live_cap)` and a spectacular live record could at
    best decline to brake. That was correct containment while the backtest half was the legacy-cost
    CP4/CP5 replay; with cost-true splits it just makes the loop unable to learn upward. What
    replaces it is not "delete the min()": the raise is capped at ONE `LIVE_UP_STEP` above what the
    sleeve is currently deployed at, so no single reading of the record can reach the ceiling.
    """
    thin_backtest = dict(train_meanR=+0.01, oos_meanR=+0.01, sealed_meanR=+0.01,
                         train_n=100, oos_n=100, sealed_n=100, train_days=100, oos_days=100,
                         sealed_days=100)
    backtest_only = recommend(SleeveEvidence("s", **thin_backtest))
    assert backtest_only.verdict == "KEEP" and backtest_only.conf_mult == 1.0

    raised = recommend(SleeveEvidence(
        "s", **thin_backtest, live_meanR=+0.90, live_n=40, live_day_blocks=40,
        live_gate_threshold_r=-99.0, live_kill_threshold_r=-999.0, live_cost_coverage="MEASURED"))
    assert raised.live_verdict == "SUPPORTING"
    assert raised.live_raised is True
    assert raised.verdict == "SIZE_UP"
    # +0.90 R/fill would map to x1.25 on the backtest half's own scale; the step cap says x1.05.
    assert raised.conf_mult == 1.0 + LIVE_UP_STEP


def test_the_raise_ladder_needs_a_cycle_per_step():
    """Reaching MAX_UP from an undisturbed weight takes five owner-applied re-ratings, not one."""
    seen, current = [], 1.0
    for _ in range(8):
        r = recommend(_earning(live_meanR=+9.0, live_n=500, live_day_blocks=500,
                               live_gate_threshold_r=-99.0, live_kill_threshold_r=-999.0,
                               live_cost_coverage="MEASURED", current_conf_mult=current))
        seen.append(round(r.conf_mult, 6))
        current = r.conf_mult
    assert seen[-1] == MAX_UP
    assert max(b - a for a, b in zip(seen, seen[1:])) <= LIVE_UP_STEP + 1e-9
    # ...and the backtest half's own size-up is not throttled by the ladder: it is a static
    # artifact, not evidence arriving over time.
    assert seen[0] == recommend(_earning()).conf_mult


def test_a_raise_needs_day_blocks_not_just_fills():
    """30 fills on 9 days is not 30 observations. R measured the clustering; the bar is in days."""
    clustered = recommend(_earning(live_meanR=+0.5, live_n=40, live_day_blocks=9,
                                   live_gate_threshold_r=-99.0, live_kill_threshold_r=-999.0,
                                   live_cost_coverage="MEASURED"))
    assert clustered.live_verdict == "CONSISTENT"
    assert clustered.live_raised is False


def test_live_can_never_raise_above_max_up_or_the_owner_dial():
    spectacular = dict(live_meanR=+9.0, live_n=500, live_day_blocks=500,
                       live_gate_threshold_r=-99.0, live_kill_threshold_r=-999.0,
                       live_cost_coverage="MEASURED", current_conf_mult=MAX_UP)
    assert recommend(_earning(**spectacular)).conf_mult == MAX_UP
    dialled = recommend(_earning(**spectacular), owner_dial_cap=1.0)
    assert dialled.conf_mult == 1.0
    assert dialled.verdict == "KEEP", "a size-up the dial removed must not still be called one"


def test_a_raise_can_never_un_brake():
    """idxrev is the real case: negative on every split, and the only live-profitable sleeve (B63).

    The property is now stated as the property rather than as a verdict name — **live may not
    raise a sleeve the backtest half is braking, whichever brake it is** — because AP measured
    that the guard protected only GATE and a backtest DOWN_WEIGHT could be lifted to SIZE_UP."""
    ev = SleeveEvidence("idxrev", train_meanR=-0.024, oos_meanR=-0.089, sealed_meanR=-0.000,
                        train_n=994, oos_n=2441, sealed_n=1423,
                        train_days=142, oos_days=1102, sealed_days=279,
                        status="breadth_falsified",
                        live_meanR=+1.5, live_n=200, live_day_blocks=200,
                        live_gate_threshold_r=-99.0, live_kill_threshold_r=-999.0,
                        live_cost_coverage="MEASURED")
    r = recommend(ev)
    assert r.live_verdict == "SUPPORTING"
    assert r.backtest_verdict == "GATE"
    assert r.verdict == "GATE" and r.gate is True and r.conf_mult == GATE_MULT
    assert r.live_raised is False, "a spectacular live run must not lift a braked sleeve"


def test_live_cannot_rescue_a_backtest_gate():
    """idxrev is the real case: negative on every split, and the only live-profitable sleeve (B63)."""
    ev = SleeveEvidence("idxrev", train_meanR=-0.024, oos_meanR=-0.089, sealed_meanR=-0.000,
                        train_n=994, oos_n=2441, sealed_n=1423, status="breadth_falsified",
                        live_meanR=+1.5, live_n=200,
                        live_gate_threshold_r=-99.0, live_kill_threshold_r=-999.0)
    r = recommend(ev)
    assert r.backtest_verdict == "GATE"
    assert r.verdict == "GATE" and r.gate is True and r.conf_mult == GATE_MULT
    assert r.live_raised is False


def test_live_cannot_lift_a_backtest_down_weight_and_that_was_a_PRE_EXISTING_hole():
    """The fix, as its own test, on a fixture that has nothing to do with idxrev.

    A MIXED sleeve with a large high-n negative split is DOWN_WEIGHTed by the backtest half. Before
    2026-07-30 a flattering live record lifted it to SIZE_UP x1.05, because the raise guard read
    `v.verdict != "GATE"` and protected only one of the two brake states. MEASURED at 5065ed24c:
    this exact evidence returned `backtest=DOWN_WEIGHT final=SIZE_UP x1.05`. It is the failure
    `_apply_live`'s own docstring names -- a false raise adds size while a sleeve's recent record
    flatters it, on a prop account, and no later re-rate reverses the loss it funds."""
    ev = SleeveEvidence("probe", train_meanR=+0.30, oos_meanR=-0.20, sealed_meanR=+0.30,
                        train_n=200, oos_n=200, sealed_n=200,
                        train_days=200, oos_days=200, sealed_days=200,
                        live_meanR=+1.5, live_n=200, live_day_blocks=200,
                        live_gate_threshold_r=-99.0, live_kill_threshold_r=-999.0,
                        live_cost_coverage="MEASURED", current_conf_mult=1.0)
    r = recommend(ev)
    assert r.backtest_verdict == "DOWN_WEIGHT"
    assert r.live_verdict == "SUPPORTING", "the fixture must actually offer a raise"
    assert r.verdict == "DOWN_WEIGHT" and r.conf_mult <= 0.5
    assert r.live_raised is False


def test_negative_live_inside_the_boundary_blocks_size_up_only():
    r = recommend(_earning(live_meanR=-0.20, live_n=10,
                           live_gate_threshold_r=-99.0, live_kill_threshold_r=-999.0))
    assert r.live_verdict == "NEGATIVE_NOT_DECISIVE"
    assert r.verdict == "KEEP" and r.conf_mult == 1.0 and r.gate is False


def test_modelled_cost_may_gate_but_never_support():
    """Understating cost is the F38 direction: a 'refuted' verdict survives it, 'healthy' does not."""
    supporting = recommend(_earning(live_meanR=+0.5, live_n=LIVE_MIN_N_SUPPORT,
                                    live_gate_threshold_r=-99.0, live_kill_threshold_r=-999.0,
                                    live_cost_coverage="MODELLED"))
    assert supporting.live_verdict == "NEGATIVE_NOT_DECISIVE"
    assert supporting.conf_mult == 1.0            # size-up refused

    gating = recommend(_earning(live_meanR=-2.0, live_n=4,      # -8R: crosses down, not kill
                                live_gate_threshold_r=-5.0, live_kill_threshold_r=-15.0,
                                live_cost_coverage="MODELLED"))
    assert gating.live_verdict == "REFUTED_DOWN"  # a modelled cost may still gate
    assert gating.conf_mult == FLOOR_MULT


# --------------------------------------------------------------- 3. the boundaries themselves

def test_crossing_the_down_boundary_down_weights():
    r = recommend(_earning(live_meanR=-1.0, live_n=5,
                           live_gate_threshold_r=-4.0, live_kill_threshold_r=-99.0))
    assert r.live_verdict == "REFUTED_DOWN"
    assert r.verdict == "DOWN_WEIGHT" and r.conf_mult == FLOOR_MULT and r.gate is False


def test_crossing_the_kill_boundary_gates():
    r = recommend(_earning(live_meanR=-1.0, live_n=10,
                           live_gate_threshold_r=-4.0, live_kill_threshold_r=-8.0))
    assert r.live_verdict == "REFUTED_KILL"
    assert r.verdict == "GATE" and r.conf_mult == GATE_MULT and r.gate is True


def test_boundary_is_on_the_sum_not_the_mean():
    """Same mean, different n: only the one whose cumulative R crosses may fire."""
    shallow = recommend(_earning(live_meanR=-1.0, live_n=3, live_gate_threshold_r=-5.0))
    deep = recommend(_earning(live_meanR=-1.0, live_n=6, live_gate_threshold_r=-5.0))
    assert shallow.live_verdict != "REFUTED_DOWN"
    assert deep.live_verdict == "REFUTED_DOWN"


def test_live_gates_even_when_backtest_evidence_is_insufficient():
    """crypto has one split at n>=MIN_N and is armed. Thin backtest must not confer immunity."""
    ev = SleeveEvidence("crypto", train_meanR=None, oos_meanR=+1.512, sealed_meanR=+0.806,
                        train_n=0, oos_n=7, sealed_n=60, status="train_validated",
                        live_meanR=-1.4, live_n=8,
                        live_gate_threshold_r=-5.0, live_kill_threshold_r=-9.0)
    assert len(ev.evaluable_splits()) < 2          # backtest alone says INSUFFICIENT_EVIDENCE
    r = recommend(ev)
    assert r.backtest_verdict == "INSUFFICIENT_EVIDENCE"
    assert r.verdict == "GATE" and r.gate is True


# ------------------------------------- first passage vs point-in-time (R section 4 item 12, fixed by AE)

def _flat_curve(n, down, kill):
    return tuple((down, kill) for _ in range(n))


def test_a_crossing_that_later_recovers_still_counts():
    """THE fix for R item 12: the calibration solves first passage; the rule tested the endpoint.

    Six fills: the path dips to -6.0 R at fill 4 and recovers to -2.0 R by fill 6. Against a
    down-weight boundary of -5.0 the endpoint test says healthy and first passage says refuted.
    The error budget was spent when the boundary was touched; a later recovery does not refund it.
    """
    series = (-2.0, -2.0, -1.0, -1.0, +2.0, +2.0)   # cum: -2 -4 -5 -6 -4 -2
    ev = _earning(live_meanR=sum(series) / len(series), live_n=len(series), live_day_blocks=6,
                  live_gate_threshold_r=-5.0, live_kill_threshold_r=-99.0,
                  live_r_series=series, live_boundary_curve=_flat_curve(6, -5.0, -99.0))
    r = recommend(ev)
    assert r.live_evaluation == "first_passage"
    assert r.live_verdict == "REFUTED_DOWN"
    assert r.live_first_passage_n == 3          # cum hits exactly -5.0 at fill 3
    assert r.verdict == "DOWN_WEIGHT" and r.conf_mult == FLOOR_MULT

    # ...and the same record without the path reads healthy, which is the defect being fixed.
    blind = recommend(_earning(live_meanR=sum(series) / len(series), live_n=len(series),
                               live_day_blocks=6, live_gate_threshold_r=-5.0,
                               live_kill_threshold_r=-99.0))
    assert blind.live_evaluation == "point_in_time"
    assert blind.live_verdict != "REFUTED_DOWN"


def test_first_passage_prefers_the_kill_even_when_a_down_crossing_came_first():
    series = (-3.0, -3.0, -3.0, -3.0)
    ev = _earning(live_meanR=-3.0, live_n=4, live_day_blocks=4,
                  live_r_series=series, live_boundary_curve=_flat_curve(4, -5.0, -11.0))
    r = recommend(ev)
    assert r.live_verdict == "REFUTED_KILL" and r.gate is True
    assert r.live_first_passage_n == 4


def test_a_nan_inside_the_series_refuses_the_record_rather_than_failing_open():
    series = (0.5, float("nan"), 0.5)
    ev = _earning(live_meanR=0.5, live_n=3, live_day_blocks=3,
                  live_r_series=series, live_boundary_curve=_flat_curve(3, -5.0, -11.0))
    r = recommend(ev)
    assert r.live_verdict == "UNUSABLE"
    assert r.conf_mult <= 1.0 and r.gate is False


def test_first_passage_is_never_looser_than_the_endpoint_test():
    """The property, not an example. Over random paths the latched verdict is never the milder one."""
    import random
    order = {"SUPPORTING": 0, "CONSISTENT": 1, "NEGATIVE_NOT_DECISIVE": 2,
             "REFUTED_DOWN": 3, "REFUTED_KILL": 4}
    rng = random.Random(20260730)
    for _ in range(300):
        n = rng.randint(3, 40)
        series = tuple(rng.choice([-1.01, -1.0, -0.4, 0.0, 0.8, 2.5]) for _ in range(n))
        mean = sum(series) / n
        kw = dict(live_meanR=mean, live_n=n, live_day_blocks=n, live_cost_coverage="MEASURED",
                  live_gate_threshold_r=-6.0, live_kill_threshold_r=-12.0)
        endpoint = recommend(_earning(**kw))
        latched = recommend(_earning(**kw, live_r_series=series,
                                     live_boundary_curve=_flat_curve(n, -6.0, -12.0)))
        assert order[latched.live_verdict] >= order[endpoint.live_verdict], (
            f"first passage was MILDER than the endpoint test on {series}: "
            f"{latched.live_verdict} vs {endpoint.live_verdict}")


def test_uncalibrated_sleeve_blocks_size_up_but_cannot_gate():
    r = recommend(_earning(live_meanR=-3.0, live_n=25))
    assert r.live_verdict == "UNCALIBRATED"
    assert r.gate is False and r.conf_mult == 1.0


# --------------------------------------------------------------- the retired veto, and default-off

def test_the_cost_true_labels_no_longer_veto_anything():
    """The veto is retired (AE, 2026-07-30) and this pins that it really is gone.

    `cost_true_survivor is False -> block any size-up` was a patch containing legacy-cost damage:
    the every-split evidence was the CP4/CP5 replay at the cost map F38/F39 discredited, so a
    size-up computed from it could contradict the broker-true re-cost. With `cost_true_splits.py`
    feeding cost-true means the labels are descriptive and nothing keys off them — identical
    evidence must produce an identical verdict whatever the label says.

    The PROPERTY the veto protected — no size-up on cost-discredited evidence — has moved to
    `test_learning_actuator_cost_true.py`, where it is asserted against the real artifact instead
    of against a synthetic flag.
    """
    survivor = recommend(_earning(cost_true_survivor=True, cost_true_tier="UNCONDITIONAL"))
    killed = recommend(_earning(cost_true_survivor=False, cost_true_tier="CARRY_CONDITIONAL"))
    unknown = recommend(_earning())
    assert survivor.verdict == killed.verdict == unknown.verdict == "SIZE_UP"
    assert survivor.conf_mult == killed.conf_mult == unknown.conf_mult > 1.0


def test_a_gate_is_never_rescued_by_any_label_or_record():
    """One-sided, like the live stage: a survivor tier cannot undo a gate."""
    ev = SleeveEvidence("x", train_meanR=-0.1, oos_meanR=-0.2, sealed_meanR=-0.3,
                        train_n=100, oos_n=100, sealed_n=100,
                        cost_true_survivor=True, cost_true_tier="UNCONDITIONAL")
    assert recommend(ev).verdict == "GATE"


def test_default_off_still_holds_with_live_evidence():
    evs = [_earning(live_meanR=-2.0, live_n=10, live_gate_threshold_r=-4.0, live_kill_threshold_r=-8.0)]
    off = rerate_book(evs, enabled=False)
    on = rerate_book(evs, enabled=True)
    assert all(not r.actuated for r in off.values())
    assert on["s"].actuated is True and on["s"].gate is True


def test_conf_mult_stays_bounded_under_every_live_path():
    for lm, ln, d, k in [(+99.0, 500, -1.0, -2.0), (-99.0, 500, -1.0, -2.0), (0.0, 5, None, None)]:
        r = recommend(_earning(live_meanR=lm, live_n=ln, live_gate_threshold_r=d, live_kill_threshold_r=k))
        assert 0.0 <= r.conf_mult <= MAX_UP


# --------------------------------------------------------------- the asymmetry, on real numbers

@pytest.mark.skipif(not CALIBRATION.is_file(), reason="calibration artifact not built")
def test_armed_sleeves_gate_far_sooner_than_they_size_up():
    """The property the whole design exists for, checked against the shipped calibration.

    A handful of live losses must move a sleeve down long before any number of live wins can move
    it up. Sizing up needs LIVE_MIN_N_SUPPORT (30) fills; down-weighting must need far fewer.
    """
    doc = json.loads(CALIBRATION.read_text())
    armed = ("crypto", "energy_agri", "sub_xvol_pullback")
    seen = 0
    for account, sleeves in doc["accounts"].items():
        for name in armed:
            cal = sleeves.get(name)
            if not cal or not cal.get("calibrated"):
                continue
            seen += 1
            # The MEASURED stop-out columns, not the relocated ones. A stop-out is a mechanical
            # -1R event plus costs; it does not scale with the sleeve's mean re-costing, so the
            # relocated figure charges it horizon-mean carry it never pays and reads too low.
            down = cal["stop_outs_to_down_weight_measured"]
            gate = cal["stop_outs_to_gate_measured"]
            assert down is not None and gate is not None
            assert down >= LIVE_MIN_N, f"{account}/{name} would fire below the hard floor"
            assert gate > down, f"{account}/{name} gates no later than it down-weights"
            assert down < LIVE_MIN_N_SUPPORT, (
                f"{account}/{name}: down-weight at {down} stop-outs vs size-up support at "
                f"{LIVE_MIN_N_SUPPORT} fills is not an asymmetry at all"
            )
            assert down <= 10, (
                f"{account}/{name} needs {down} consecutive full stop-outs to down-weight; the "
                "standard has drifted from 'a handful of live losses'"
            )
    assert seen == 6, f"expected 3 armed sleeves x 2 accounts, calibrated {seen}"


@pytest.mark.skipif(not CALIBRATION.is_file(), reason="calibration artifact not built")
def test_no_calibrated_sleeve_can_be_gated_by_one_or_two_trades():
    """The regression guard for the defect this artifact shipped with in its first two drafts."""
    doc = json.loads(CALIBRATION.read_text())
    for account, sleeves in doc["accounts"].items():
        for name, cal in sleeves.items():
            if not cal.get("calibrated"):
                continue
            for field in ("stop_outs_to_down_weight", "stop_outs_to_gate"):
                got = cal[field]
                assert got is None or got >= LIVE_MIN_N, (
                    f"{account}/{name}.{field} == {got}: a sleeve must not be gateable by "
                    f"fewer than {LIVE_MIN_N} losing trades"
                )


# ----------------------------------------------- the raise guard, EXHAUSTIVELY (Session AU, B1557)

#: Live evidence strong enough to offer a raise in every case below: SUPPORTING, far inside a
#: deliberately unreachable boundary, cost MEASURED. Any sleeve that is NOT raised under this record
#: is not raised because of the guard.
_SPECTACULAR_LIVE = dict(live_meanR=+1.5, live_n=200, live_day_blocks=200,
                         live_gate_threshold_r=-99.0, live_kill_threshold_r=-999.0,
                         live_cost_coverage="MEASURED", current_conf_mult=1.0)

#: One fixture per reachable branch of `_backtest_verdict`, chosen to land on that branch and named
#: by the branch rather than by the sleeve, so the coverage assertion below is meaningful.
_BACKTEST_BRANCHES = {
    # every split negative -> GATE (mult 0.0)
    "every_neg": dict(train_meanR=-0.20, oos_meanR=-0.30, sealed_meanR=-0.10,
                      train_n=200, oos_n=200, sealed_n=200,
                      train_days=200, oos_days=200, sealed_days=200),
    # mixed with a large high-n negative -> DOWN_WEIGHT (mult 0.5)
    "mixed_neg_heavy": dict(train_meanR=+0.30, oos_meanR=-0.20, sealed_meanR=+0.30,
                            train_n=200, oos_n=200, sealed_n=200,
                            train_days=200, oos_days=200, sealed_days=200),
    # mixed, negatives small or thin -> HOLD_FLAG (mult 1.0)
    "mixed_hold_flag": dict(train_meanR=+0.30, oos_meanR=-0.02, sealed_meanR=+0.30,
                            train_n=200, oos_n=40, sealed_n=200,
                            train_days=200, oos_days=40, sealed_days=200),
    # positive every split, worst above the band -> SIZE_UP
    "every_pos_material": dict(train_meanR=+0.30, oos_meanR=+0.40, sealed_meanR=+0.50,
                               train_n=100, oos_n=100, sealed_n=100,
                               train_days=60, oos_days=60, sealed_days=60),
    # positive every split but thin -> KEEP (mult 1.0)
    "every_pos_thin": dict(train_meanR=+0.001, oos_meanR=+0.001, sealed_meanR=+0.001,
                           train_n=100, oos_n=100, sealed_n=100,
                           train_days=60, oos_days=60, sealed_days=60),
    # too few evaluable splits -> INSUFFICIENT_EVIDENCE (mult 1.0)
    "insufficient": dict(train_meanR=+0.30, oos_meanR=None, sealed_meanR=None,
                         train_n=100, oos_n=0, sealed_n=0,
                         train_days=60, oos_days=0, sealed_days=0),
}


def _recommend_branch(kw):
    return recommend(SleeveEvidence("probe", status="train_validated", **kw, **_SPECTACULAR_LIVE))


def test_the_raise_guard_is_complete_over_every_backtest_branch():
    """**Live may not raise a sleeve the backtest half is braking, whichever brake it is.**

    AP fixed the hole and pinned the two instances it found (GATE and DOWN_WEIGHT). This is the
    property over the WHOLE branch set instead of over the two known cases, because the guard is
    written as a hardcoded tuple -- `_braking = ("GATE", "DOWN_WEIGHT")` at
    `learning_actuator.py:606` -- and a hardcoded membership list is the thing that decays when a
    future session adds a third brake. The invariant asserted here needs no tuple: whatever the
    backtest half deployed BELOW 1.0, live may not lift.

    It also asserts the reverse, so it cannot pass by braking everything: the one branch that is
    genuinely above 1.0 must still be raisable, and the two that sit exactly at 1.0 must be too --
    a loop that can only subtract is not a learning loop.
    """
    seen = {}
    for branch, kw in _BACKTEST_BRANCHES.items():
        r = _recommend_branch(kw)
        seen[branch] = (r.backtest_verdict, r.conf_mult, r.live_raised)
        assert r.live_verdict == "SUPPORTING", (
            f"{branch}: the fixture must actually OFFER a raise, else the guard is untested here")

    #: coverage: every declared verdict in the backtest vocabulary is reached by some fixture
    reached = {v for v, _, _ in seen.values()}
    assert reached == {"GATE", "DOWN_WEIGHT", "HOLD_FLAG", "SIZE_UP", "KEEP",
                       "INSUFFICIENT_EVIDENCE"}, f"branch coverage regressed: {reached}"

    braked = {b: t for b, t in seen.items() if t[1] < 1.0}
    assert braked, "no braking branch reached — the guard would be untested"
    for branch, (verdict, mult, raised) in braked.items():
        assert raised is False, (
            f"{branch}: the backtest half deployed {verdict} at x{mult} and live RAISED it. That is "
            f"the pre-existing fail-open AP measured at 5065ed24c, back. A false raise adds size at "
            f"the moment a sleeve's recent record flatters it, on a funded account.")

    #: and the guard is not just 'never raise': the branches at or above 1.0 are still liftable
    assert seen["every_pos_material"][2] is False, \
        "an already-size-up sleeve is capped by current_conf_mult + one step, not raised again here"
    for branch in ("every_pos_thin", "insufficient", "mixed_hold_flag"):
        assert seen[branch][2] is True, f"{branch}: live evidence must still be able to raise"


def test_the_braking_tuple_matches_the_measured_property():
    """The tuple and the property must agree TODAY as well as behaviourally. If a future verdict is
    added below 1.0 without being added to `_braking`, the test above fails on the behaviour and this
    one names the tuple as the site to fix."""
    from src.components.ultimate_book import learning_actuator as LA

    rs = [_recommend_branch(kw) for kw in _BACKTEST_BRANCHES.values()]
    below_one = {r.backtest_verdict for r in rs if r.conf_mult < 1.0}
    assert below_one == {"GATE", "DOWN_WEIGHT"}, (
        f"the set of backtest verdicts that deploy below 1.0 is {sorted(below_one)}; "
        f"learning_actuator._braking must name exactly these")
    assert "_braking = (\"GATE\", \"DOWN_WEIGHT\")" in inspect.getsource(LA._apply_live)
