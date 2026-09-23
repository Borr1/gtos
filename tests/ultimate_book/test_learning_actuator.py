"""test_learning_actuator.py — the learning system, fed the REAL CP4 large-data numbers.

Asserts the evidence-driven re-rating makes the right calls: brake the non-edge (idxrev, negative every split,
huge n), KEEP/SIZE_UP the validated-every-split sleeves, INSUFFICIENT on thin per-split n, and respect default-off
(recommendation-only unless enabled).

AMENDED 2026-07-30 (Session AP, B1350-B1399): the MATERIALITY BAND on the SIGN TEST is now in
force — AE §5's own written recommendation, ratified by Borhen with the rest of the decision
queue. `every_neg` no longer lets an IMMATERIALLY POSITIVE split veto "negative on every split",
so a sleeve whose only non-negative number is inside +/-0.05 gates instead of escaping. **Every
assertion in this file is unchanged by it**, because these legacy fixtures are already
unambiguous — and that is the point: the band moves verdicts on the COST-TRUE basis the
production script actually runs on (`idxrev` HOLD_FLAG -> GATE, plus `asia_pdl_fade`,
`asian_fade` and `metal_session_reversion`, all toward MORE braking) and moves nothing here.

AP's FIRST attempt at this put the band on the GATE THRESHOLD instead, which withdrew the gate
from four cost-true sleeves — `vss_fxcross_london_up_low` loses 0.3749 R/trade on its train split
and stopped gating because its LEAST-negative split was -0.0377. An adversarial pass caught it.
The rule as it now stands can only ever ADD a brake, which is why these assertions are safe.
"""
import sys
# NOTE 2026-07-26: a hardcoded sys.path.insert(0, "/Users/borr/Documents/gtos/repo/
# ai-trading-agent") was removed here. It prepended a DIFFERENT, stale checkout, so this
# file silently tested that repo instead of the working tree whenever it ran in isolation
# (in a full-suite run sys.modules was already populated, so the same tests exercised the
# real code and could disagree). Tests must import the tree they are checked out in.
from src.components.ultimate_book.learning_actuator import (
    SleeveEvidence, recommend, rerate_book, GATE_MULT, MAX_UP, MIN_N)

# --- the real CP4 replay numbers (deep-history every-split meanR, n) ---
EV = [
    SleeveEvidence("idxrev",        train_meanR=-0.024, oos_meanR=-0.089, sealed_meanR=-0.000,
                   train_n=994, oos_n=2441, sealed_n=1423, status="breadth_falsified"),
    SleeveEvidence("metals_core",   train_meanR=+0.146, oos_meanR=-0.061, sealed_meanR=+0.853,
                   train_n=105, oos_n=24, sealed_n=49, status="train_validated"),
    SleeveEvidence("sub_mid_dn_revert", train_meanR=+0.228, oos_meanR=+0.674, sealed_meanR=+1.167,
                   train_n=82, oos_n=70, sealed_n=58, status="train_validated"),
    SleeveEvidence("metals_softband", train_meanR=+0.478, oos_meanR=+1.527, sealed_meanR=+0.215,
                   train_n=37, oos_n=15, sealed_n=39, status="train_validated"),
    SleeveEvidence("crypto",        train_meanR=None, oos_meanR=+1.512, sealed_meanR=+0.806,
                   train_n=0, oos_n=7, sealed_n=60, status="train_validated"),
    # --- CP5 M15 replay numbers: the OTHER falsified live-earners (fx_jpy 27% of live P&L combined) ---
    SleeveEvidence("fx_jpy",        train_meanR=-0.041, oos_meanR=+0.003, sealed_meanR=+0.123,
                   train_n=4144, oos_n=1556, sealed_n=744, status="breadth_falsified"),
    SleeveEvidence("fx_jpy_ny",     train_meanR=-0.013, oos_meanR=-0.071, sealed_meanR=+0.153,
                   train_n=1615, oos_n=702, sealed_n=274, status="forward_only"),
]


def test_l1_completion_fxjpy_not_every_split_edges():
    """L1 adjudication completion: the M15 falsified live-earners are NOT every-split edges.
    fx_jpy is MIXED (negative on the 4144-trade train sample, only a recent patch) -> HOLD_FLAG (watch,
    regime-dependent), NOT a clean gate like idxrev. fx_jpy_ny has a large high-n negative oos -> DOWN_WEIGHT.
    Neither is positive every split, so neither passes the program's one hard rule from evidence."""
    fx = recommend(EV[5])
    assert fx.verdict == "HOLD_FLAG", (fx.verdict, fx.reason)
    assert fx.conf_mult == 1.0 and fx.gate is False        # mixed -> hold + flag, never auto-gated
    ny = recommend(EV[6])
    assert ny.verdict == "DOWN_WEIGHT", (ny.verdict, ny.reason)
    assert ny.conf_mult == 0.5 and ny.gate is False        # large high-n negative split -> soft down-weight
    # the headline: neither M15 live-earner is positive-every-split (the bar the validated sleeves clear)
    for ev in (EV[5], EV[6]):
        means = [m for _, m, _ in ev.evaluable_splits()]
        assert not all(m > 0 for m in means), f"{ev.sleeve} should NOT be positive every split"


def test_idxrev_gated_the_non_edge():
    r = recommend(EV[0])
    assert r.verdict == "GATE", r.verdict
    assert r.conf_mult == GATE_MULT and r.gate is True
    # the headline: the learning system catches the falsified live-earner from evidence
    assert "EVERY" in r.reason


def test_the_band_stops_a_near_zero_positive_withdrawing_a_gate():
    """The defect AE filed, on the numbers AE filed it with.

    `idxrev`'s COST-TRUE splits are -0.0243 / -0.0124 / **+0.0079**, and that +0.0079 — four
    orders of magnitude inside the +/-0.05 band a size-up must clear — used to veto `every_neg`
    and turn the gate into HOLD_FLAG x1.00. `metal_session_reversion` is the same shape at its
    most vivid: **+0.0001** excusing -0.3208 and -0.2227."""
    for name, means in (("idxrev_cost_true", (-0.0243, -0.0124, +0.0079)),
                        ("metal_session_reversion", (-0.3208, -0.2227, +0.0001))):
        ev = SleeveEvidence(name, train_meanR=means[0], oos_meanR=means[1], sealed_meanR=means[2],
                            train_n=200, oos_n=1000, sealed_n=200,
                            train_days=200, oos_days=1000, sealed_days=200)
        r = recommend(ev)
        assert r.verdict == "GATE", (name, r.verdict, r.reason)
        assert "MATERIALITY BAND" in r.reason, name


def test_the_band_does_not_gate_a_merely_thin_positive_sleeve():
    """The second clause, and the reason it exists. A sleeve positive on every split — even
    weakly — has shown no negative evidence, so "no split is materially positive" must not be
    enough to gate it on its own. The one-clause version of this rule GATED +0.01/+0.01/+0.01."""
    ev = SleeveEvidence("thin_pos", train_meanR=+0.01, oos_meanR=+0.01, sealed_meanR=+0.01,
                        train_n=100, oos_n=100, sealed_n=100,
                        train_days=100, oos_days=100, sealed_days=100)
    r = recommend(ev)
    assert r.verdict == "KEEP" and r.conf_mult == 1.0 and r.gate is False, (r.verdict, r.reason)


def test_the_band_never_withdraws_a_gate():
    """AP's first attempt did exactly that. A sleeve negative on every split gates whatever the
    magnitudes, so no near-zero split can excuse a ruinous one — the `vss_fxcross_london_up_low`
    shape (train -0.3749, oos -0.0377) that the rejected version un-gated."""
    ev = SleeveEvidence("vss_shape", train_meanR=-0.3749, oos_meanR=-0.0377, sealed_meanR=None,
                        train_n=55, oos_n=218, sealed_n=0,
                        train_days=36, oos_days=218, sealed_days=0)
    r = recommend(ev)
    assert r.verdict == "GATE" and r.gate is True and r.conf_mult == GATE_MULT, (r.verdict, r.reason)


def test_validated_every_split_kept_or_sized():
    # metals_core: oos n24 < MIN_N excluded; train+sealed both positive -> SIZE_UP/KEEP
    mc = recommend(EV[1]); assert mc.verdict in ("SIZE_UP", "KEEP"), mc.verdict
    assert 1.0 <= mc.conf_mult <= MAX_UP
    # sub_mid_dn: all 3 splits >=MIN_N and positive -> SIZE_UP
    sm = recommend(EV[2]); assert sm.verdict == "SIZE_UP", (sm.verdict, sm.reason)
    assert sm.conf_mult > 1.0 and sm.conf_mult <= MAX_UP


def test_thin_evidence_is_insufficient_never_actuates():
    # crypto: only sealed has n>=MIN_N (oos n7) -> <2 evaluable splits -> INSUFFICIENT
    c = recommend(EV[4]); assert c.verdict == "INSUFFICIENT_EVIDENCE", c.verdict
    assert c.conf_mult == 1.0 and c.gate is False and c.actuated is False


def test_default_off_is_recommendation_only():
    recs = rerate_book(EV, enabled=False)
    assert all(not r.actuated for r in recs.values())          # default-off: nothing actuates
    recs_on = rerate_book(EV, enabled=True)
    assert recs_on["idxrev"].actuated is True                  # enabled: the GATE actuates
    assert recs_on["idxrev"].gate is True


def test_bounded_no_runaway_sizeup():
    # even a huge positive every-split sleeve is capped at MAX_UP
    big = SleeveEvidence("x", train_meanR=5, oos_meanR=5, sealed_meanR=5, train_n=99, oos_n=99, sealed_n=99)
    r = recommend(big); assert r.conf_mult <= MAX_UP


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    p = 0
    for fn in fns:
        try:
            fn(); p += 1; print(f"PASS {fn.__name__}")
        except Exception:
            print(f"FAIL {fn.__name__}"); traceback.print_exc()
    print(f"\n{p}/{len(fns)} learning-actuator tests passed")
    # show the book re-rating from the real numbers
    print("\n=== LEARNING-SYSTEM book re-rating (from the CP4 large-data evidence, default-off) ===")
    for s, r in rerate_book(EV).items():
        print(f"  {s:18s} {r.verdict:22s} conf_mult x{r.conf_mult:.2f}")
    assert p == len(fns), "learning-actuator tests FAILED"
