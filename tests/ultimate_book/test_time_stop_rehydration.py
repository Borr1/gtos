"""`hydrate_vnext_dynamic_policy_from_record` must not raise on a `time_stop` record.

Found by an adversarial pass on Session AS's activation dossier (B1535), pre-existing, and live:

    `_vnext_time_stop_params` (execution.py:1532-1562) returns
    {time_stop_bars, final_target_r, no_broker_take_profit} — no `trigger_r`, correctly, because a
    time stop has no break-even trigger. But execution.py read `params["trigger_r"]` unconditionally,
    so every `policy="time_stop"` record raised `KeyError('trigger_r')`.

    That is FOUR OF THE FIVE ARMED SLEEVES. Only `energy_agri` is `partial_be_runner` and its
    params carry the key. And the live caller does not catch it: `book_owner.py:2729` calls
    `hyd(rec)` with no try/except when `_live_broker_authority()` is true — which it is on both
    funded accounts. The `except TypeError` at `:2733` only guards the observe-only branch, and a
    KeyError is not a TypeError.

So adopting any open position of an armed time-stop sleeve raised out of the book's adopt path.

These tests drive the REAL engine method against the REAL instrumentation the packet builder emits.
"""
from __future__ import annotations

import pytest

from src.components.execution import ExecutionEngine
from src.components.ultimate_book.execution_packets import (
    SLEEVE_EXIT_PROFILES,
    native_policy_instrumentation,
)

ARMED = ("crypto", "energy_agri", "sub_xvol_pullback", "fx_jpy", "sub_mid_dn_revert")


def _engine():
    eng = ExecutionEngine.__new__(ExecutionEngine)
    eng.config = {}
    eng.mt5 = None
    return eng


class _Trade:
    """Permissive stub: any attribute the hydrator reads that the test did not set returns None,
    so the test exercises the real code path instead of an attribute obstacle course. The four
    fields that MATTER are set explicitly, and `sl_distance` is one of them — the hydrator returns
    False at execution.py:2963 without it, which would make this test vacuously pass."""

    def __getattr__(self, name):
        return None


def _stub_trade():
    t = _Trade()
    t.__dict__.update(ticket=1, trade_id="t1", symbol="XAUUSD", direction=1, entry_price=100.0,
                      stop_loss=99.0, take_profit=104.0, volume=0.01, sl_distance=1.0,
                      risk_distance=1.0)
    return t


def _params_for(eng, payload):
    """The same resolution chain `hydrate_vnext_dynamic_policy_from_record` uses."""
    return (eng._vnext_be_after_trigger_params(payload)
            or eng._vnext_partial_be_runner_params(payload)
            or eng._vnext_trailing_runner_params(payload)
            or eng._vnext_momentum_exhaustion_params(payload)
            or eng._vnext_time_stop_params(payload))


@pytest.mark.parametrize("sleeve", ARMED)
def test_the_resolved_params_for_every_armed_sleeve_reach_a_trigger_r(sleeve):
    """The property the fix restores: whatever the policy, a trigger value is reachable — either
    from the params or from the instrumentation the packet builder already wrote."""
    eng = _engine()
    payload = dict(native_policy_instrumentation(sleeve))
    params = _params_for(eng, payload)
    assert params is not None, f"{sleeve} resolved to no policy params at all"
    trigger = params.get("trigger_r")
    if trigger is None:
        trigger = payload.get("gtos_vnext_dynamic_be_trigger_r")
    if trigger in (None, ""):
        trigger = params.get("final_target_r")
    assert trigger is not None, sleeve
    assert float(trigger) >= 0.0


def test_time_stop_params_deliberately_carry_no_trigger_r():
    """Pins the CAUSE, so a future reader does not 'fix' it by stuffing trigger_r into the time-stop
    params — a time stop has no break-even trigger and the params are right to omit it. The defect
    was the unconditional read at the consumer, not the producer."""
    eng = _engine()
    params = eng._vnext_time_stop_params(dict(native_policy_instrumentation("sub_xvol_pullback")))
    assert params is not None
    assert "trigger_r" not in params
    assert set(params) == {"time_stop_bars", "final_target_r", "no_broker_take_profit"}


def test_partial_be_runner_params_do_carry_it():
    """The contrasting policy, and why it never hit the defect.

    This used to read `energy_agri`, which was the one armed `partial_be_runner`. Its scale-out was
    removed on 2026-08-11 (owner-authorized, lane B7), so EVERY armed sleeve is now `time_stop` and
    the defect surface described in this module's docstring covers all of them. `metals_core` is
    the nearest unarmed `partial_be_runner` and keeps this half of the contrast honest.
    """
    eng = _engine()
    params = eng._vnext_partial_be_runner_params(dict(native_policy_instrumentation("metals_core")))
    assert params is not None and "trigger_r" in params


def test_energy_agri_is_now_a_time_stop_record_like_every_other_armed_sleeve():
    """The B7 change moved `energy_agri` onto exactly the path this module exists to protect."""
    eng = _engine()
    inst = dict(native_policy_instrumentation("energy_agri"))
    assert inst["gtos_vnext_dynamic_policy_selected"] == "time_stop"
    assert eng._vnext_partial_be_runner_params(inst) is None
    params = eng._vnext_time_stop_params(inst)
    assert params is not None and "trigger_r" not in params


@pytest.mark.parametrize("sleeve", ARMED)
def test_hydrate_does_not_raise_for_any_armed_sleeve(sleeve):
    """End to end on the real method, with the broker-touching half stubbed out.

    This is the test that would have failed before the fix, with KeyError('trigger_r'), for four of
    the five sleeves on live money.
    """
    eng = _engine()
    eng.active_trade = _stub_trade()
    record = {"instrumentation": dict(native_policy_instrumentation(sleeve)),
              "execution": {"ticket": 1},
              "sleeve": sleeve, "symbol": "XAUUSD",
              "reconstructed_from_sleeve_identity": True}
    try:
        hydrated = eng.hydrate_vnext_dynamic_policy_from_record(record, modify_broker_tp=False)
    except KeyError as exc:  # the defect
        pytest.fail(f"{sleeve}: hydrate raised KeyError({exc}) — the B1535 defect is back")
    assert hydrated is True, f"{sleeve}: hydrate declined the record"
    assert eng.active_trade.gtos_vnext_dynamic_be_trigger_r is not None, sleeve
    assert float(eng.active_trade.gtos_vnext_dynamic_be_trigger_r) >= 0.0


def test_the_restored_trigger_equals_what_the_packet_builder_wrote():
    """The fallback must restore the INTENDED value, not a convenient one.
    `native_policy_instrumentation` (execution_packets.py:172) defaults trigger_r to
    final_target_r for these policies; the hydrator must land on the same number."""
    for sleeve in ARMED:
        inst = native_policy_instrumentation(sleeve)
        prof = SLEEVE_EXIT_PROFILES[sleeve]
        expected = float(prof.get("trigger_r", inst["gtos_vnext_dynamic_final_target_r"]))
        assert inst["gtos_vnext_dynamic_be_trigger_r"] == pytest.approx(expected), sleeve

        eng = _engine()
        eng.active_trade = _stub_trade()
        rec = {"instrumentation": dict(inst), "execution": {"ticket": 1},
               "sleeve": sleeve, "symbol": "XAUUSD"}
        try:
            assert eng.hydrate_vnext_dynamic_policy_from_record(rec, modify_broker_tp=False) is True
        except KeyError as exc:
            pytest.fail(f"{sleeve}: KeyError({exc})")
        assert float(eng.active_trade.gtos_vnext_dynamic_be_trigger_r) == pytest.approx(expected), \
            sleeve


def test_the_live_caller_does_not_catch_a_KeyError():
    """Why this was fatal rather than degraded: `book_owner.py` calls the hydrator with NO
    try/except on the authority-true branch, and the observe-only branch guards TypeError only."""
    from pathlib import Path
    src = (Path(__file__).resolve().parents[2]
           / "src/components/ultimate_book/book_owner.py").read_text().splitlines()
    call = next(i for i, line in enumerate(src) if "hydrated = bool(hyd(rec))" in line)
    # the authority-true call is not inside a try
    assert "try:" not in src[call - 1]
    # and the only guard nearby is TypeError
    window = "\n".join(src[call:call + 8])
    assert "except TypeError" in window and "except KeyError" not in window
