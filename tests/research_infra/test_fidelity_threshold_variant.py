"""`register_threshold_variant` — the registrar for a parent rule at different constants.

Session AL (B1152). A threshold variant is the one kind of research member the estate had no
registrar for: `register_surface_expansion` demands a `symbol` and a `timeframe` and writes a
`basis_note` claiming the book has never traded that symbol, all three of which are false for a
variant that runs on the parent's own surface. `fidelity_for` fails closed as UNKNOWN for an
unregistered name and `B_balanced` sets `fidelity_refusal_is_hard`, so without a registrar the
gate refuses a threshold variant for a reason that has nothing to do with fidelity.

The tests that matter are the ones about what it must NOT grant.
"""

from __future__ import annotations

import pytest

from src.research_infra.walkforward import fidelity as F

PARENT = "sub_xvol_pullback"
PROD = {"vr_xhi": 1.6, "slope_up": 1.5, "mtf_sgn_thr": 0.5, "ac_band": 0.10}
VAR = {"vr_xhi": 1.4, "slope_up": 1.25, "ac_band": 0.15}


@pytest.fixture(autouse=True)
def _clean():
    F.clear_surface_expansions()
    yield
    F.clear_surface_expansions()


def test_it_grants_the_class_rate_and_stamps_it_transferred():
    rec = F.register_threshold_variant("thr_x", parent=PARENT, params=VAR,
                                       production_params=PROD)
    par = F.FIDELITY_REGISTER[PARENT]
    assert rec.basis is F.FidelityBasis.TRANSFERRED_CLASS
    assert rec.cls is par.cls
    assert F.fidelity_for("thr_x").basis is F.FidelityBasis.TRANSFERRED_CLASS


def test_it_never_grants_a_parents_own_measured_recall():
    """The conservative direction, and the whole reason this is not a relaxation: a relaxed
    threshold fires on a SUPERSET of the parent's bars and those extra bars were never observed
    live, so a parent's MEASURED_DIRECT recall does not cover them."""
    measured = [s for s, f in F.FIDELITY_REGISTER.items()
                if f.basis in (F.FidelityBasis.MEASURED_DIRECT,
                               F.FidelityBasis.MEASURED_LINEAGE_MATCHED)
                and f.cls in F._CLASS_TOTALS]
    assert measured, "no measured-basis parent in the register to test against"
    p = measured[0]
    rec = F.register_threshold_variant("thr_m", parent=p, params={"k": 2},
                                       production_params={"k": 1})
    assert rec.basis is F.FidelityBasis.TRANSFERRED_CLASS
    assert rec.basis is not F.FIDELITY_REGISTER[p].basis
    agreed, live_only = F._CLASS_TOTALS[F.FIDELITY_REGISTER[p].cls]
    assert rec.live_recall == pytest.approx(agreed / (agreed + live_only))


def test_the_note_names_every_moved_constant():
    rec = F.register_threshold_variant("thr_x", parent=PARENT, params=VAR,
                                       production_params=PROD)
    for k in VAR:
        assert f"{k} {PROD[k]!r}->{VAR[k]!r}" in rec.basis_note
    assert "SUPERSET" in rec.basis_note
    assert PARENT in rec.basis_note


def test_a_variant_identical_to_production_is_refused():
    """Minting a second record under a second name for the same rule would let one hypothesis be
    counted as two — the mirror image of the double-count CANDIDATE_FAMILY_V1 closed."""
    with pytest.raises(ValueError, match="identical to"):
        F.register_threshold_variant("thr_same", parent=PARENT,
                                     params={"vr_xhi": 1.6, "ac_band": 0.10},
                                     production_params=PROD)


def test_the_prefix_is_required_and_is_its_own():
    with pytest.raises(ValueError, match="must start with"):
        F.register_threshold_variant("mxf_wrong_registrar", parent=PARENT, params=VAR,
                                     production_params=PROD)
    with pytest.raises(ValueError, match="must start with"):
        F.register_threshold_variant("sub_xvol_pullback_v2", parent=PARENT, params=VAR,
                                     production_params=PROD)


def test_the_surface_registrar_refuses_a_threshold_prefix_and_vice_versa():
    """Each registrar accepts only its own prefixes. Widening the shared `EXPANSION_PREFIXES`
    union must never widen what a registrar accepts — that is what the split guards."""
    with pytest.raises(ValueError, match="must start with"):
        F.register_surface_expansion("thr_not_a_surface_expansion", parent=PARENT,
                                     symbol="XAUUSD", timeframe="H4")
    assert F.THRESHOLD_VARIANT_PREFIX not in F.SURFACE_EXPANSION_PREFIXES
    assert set(F.SURFACE_EXPANSION_PREFIXES) < set(F.EXPANSION_PREFIXES)


def test_a_production_sleeve_name_is_refused():
    """Refused by the PREFIX guard, which fires first — no authored sleeve carries `thr_`, so
    that is the guard a real production name meets."""
    with pytest.raises(ValueError, match="must start with"):
        F.register_threshold_variant(PARENT, parent=PARENT, params=VAR,
                                     production_params=PROD)


def test_an_authored_entry_can_never_be_overwritten(monkeypatch):
    """The AUTHORED guard is unreachable today because no authored sleeve is `thr_`-prefixed. It
    is defence in depth for the day one is, so it is tested against that state rather than left
    as an untested branch."""
    par = F.FIDELITY_REGISTER[PARENT]
    monkeypatch.setitem(F._AUTHORED_FIDELITY_REGISTER, "thr_authored_one_day", par)
    with pytest.raises(ValueError, match="AUTHORED"):
        F.register_threshold_variant("thr_authored_one_day", parent=PARENT, params=VAR,
                                     production_params=PROD)


def test_an_unknown_parent_is_refused():
    with pytest.raises(ValueError, match="unknown parent"):
        F.register_threshold_variant("thr_orphan", parent="no_such_sleeve", params=VAR,
                                     production_params=PROD)


def test_clear_surface_expansions_removes_threshold_variants_too():
    F.register_threshold_variant("thr_x", parent=PARENT, params=VAR, production_params=PROD)
    assert F.fidelity_for("thr_x").basis is F.FidelityBasis.TRANSFERRED_CLASS
    F.clear_surface_expansions()
    assert F.fidelity_for("thr_x").basis is F.FidelityBasis.UNMEASURED


def test_the_variant_clears_the_gates_fidelity_floor_exactly_when_the_parent_does():
    """No relaxation, stated as a test: for a parent already stamped TRANSFERRED_CLASS the
    variant's record is numerically the parent's, so it can neither pass a floor the parent
    fails nor fail one the parent passes."""
    par = F.FIDELITY_REGISTER[PARENT]
    assert par.basis is F.FidelityBasis.TRANSFERRED_CLASS, (
        "this test's premise is that the parent is already transferred-class")
    rec = F.register_threshold_variant("thr_x", parent=PARENT, params=VAR,
                                       production_params=PROD)
    for floor in (0.0, 0.5, 0.9, 0.96, 1.0):
        assert (rec.refusal_reason(floor) is None) == (par.refusal_reason(floor) is None)
