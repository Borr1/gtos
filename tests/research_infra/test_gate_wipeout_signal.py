"""`GateResult.family["wipeout"]` — Session AQ (B1429).

A gate run in which NOT ONE submitted sleeve reaches a null is not a verdict grid; it is a
broken harness. It does not look like one. Session AQ produced 72 such arms — 3 families x
3 entry hours x 4 cost bands x 2 multiplicity bills — every one NOT_EVALUABLE on
`port_fidelity_unmeasured` because the caller had not wrapped `run_gate` in
`family.fidelity_scope`. They tabulated cleanly and read as a measurement of the entry hour.

These tests pin the signal that now fires, and — the part that matters — pin that it stays
SILENT the moment even one sleeve is genuinely scored, so it cannot become noise that gets
ignored.
"""
from __future__ import annotations

from src.research_infra.walkforward.gate import SleeveVerdict, Verdict, _wipeout


def _sv(name: str, *, p=None, reasons=()) -> SleeveVerdict:
    sv = SleeveVerdict(sleeve=name,
                       verdict=(Verdict.REJECT if p is not None else Verdict.NOT_EVALUABLE),
                       n_trades=100)
    sv.p_raw = p
    sv.reasons = list(reasons)
    return sv


def test_no_sleeves_is_not_a_wipeout_claim():
    w = _wipeout({})
    assert w["wiped_out"] is False
    assert w["n_judged"] == 0


def test_one_scored_sleeve_silences_it_even_among_many_refusals():
    """The signal is about the RUN, not about any sleeve. A cohort where 19 of 20 are
    unmeasurable but one is scored is a thin result, not a broken harness — and a signal
    that fired there would be ignored within a week."""
    v = {f"s{i}": _sv(f"s{i}", reasons=["port_fidelity_unmeasured: ..."]) for i in range(19)}
    v["real"] = _sv("real", p=0.02)
    w = _wipeout(v)
    assert w["wiped_out"] is False
    assert w["n_scored"] == 1
    assert w["n_judged"] == 20


def test_the_fidelity_wipeout_names_its_class_and_the_fix():
    v = {f"fam_{i}": _sv(f"fam_{i}",
                         reasons=[f"port_fidelity_unmeasured: fam_{i} was not in K1's set"])
         for i in range(3)}
    w = _wipeout(v)
    assert w["wiped_out"] is True
    assert w["n_scored"] == 0
    assert w["dominant_class"] == "port_fidelity_unmeasured"
    assert w["n_in_dominant_class"] == 3
    assert "fidelity_scope" in w["note"]
    assert "measures the harness, not the sleeves" in w["note"]


def test_a_coverage_wipeout_is_reported_without_the_fidelity_advice():
    """The remedy sentence is fidelity-specific; a coverage wipeout is a different repair
    and must not be handed the wrong instruction."""
    v = {f"s{i}": _sv(f"s{i}", reasons=["cost_coverage_below_floor: 0.31 < 0.95"])
         for i in range(4)}
    w = _wipeout(v)
    assert w["wiped_out"] is True
    assert w["dominant_class"] == "cost_coverage_below_floor"
    assert "fidelity_scope" not in w["note"]


def test_mixed_refusal_classes_report_the_whole_census_not_just_the_winner():
    v = {"a": _sv("a", reasons=["port_fidelity_unmeasured: x"]),
         "b": _sv("b", reasons=["port_fidelity_unmeasured: y"]),
         "c": _sv("c", reasons=["cost_coverage_below_floor: z"]),
         "d": _sv("d", reasons=["some_unclassified_thing"])}
    w = _wipeout(v)
    assert w["wiped_out"] is True
    assert w["by_class"] == {"port_fidelity_unmeasured": 2,
                             "cost_coverage_below_floor": 1, "other": 1}
    assert w["dominant_class"] == "port_fidelity_unmeasured"


def test_a_refusal_with_no_recognised_class_still_raises_the_flag():
    """The flag keys on 'nothing was scored', never on the reason text — so a refusal class
    nobody has enumerated yet cannot slip through as a clean grid of nulls."""
    v = {"a": _sv("a", reasons=["a brand new refusal nobody has classified"])}
    w = _wipeout(v)
    assert w["wiped_out"] is True
    assert w["by_class"] == {"other": 1}


def test_run_gate_attaches_it_to_every_result():
    """Present on the happy path too, so a consumer can read one key unconditionally."""
    import datetime as dt

    from src.research_infra.walkforward import run_gate
    from src.research_infra.walkforward.panel import TradeRecord
    from src.research_infra.walkforward.spec import GateSpec

    spec = GateSpec(spec_id="wipeout_smoke", authored_utc="2026-07-30T00:00:00+00:00")
    t = TradeRecord(sleeve="nope_not_a_sleeve", symbol="EURUSD",
                    entry_utc=dt.datetime(2025, 1, 2, tzinfo=dt.timezone.utc),
                    exit_utc=dt.datetime(2025, 1, 3, tzinfo=dt.timezone.utc),
                    direction=1, sl_distance_price=0.001, entry_price=1.05, r_gross=1.0)
    res = run_gate({"nope_not_a_sleeve": [t]}, spec)
    assert "wipeout" in res.family
    assert res.family["wipeout"]["n_judged"] == 1


# ======================================================================================
# corrections from the adversarial pass over this block's first version (B1450)
# ======================================================================================

def test_every_declared_class_is_a_prefix_some_site_actually_emits():
    """The first version of `_WIPEOUT_CLASSES` listed `symbol_outside_registry_universe`,
    and no reason string in the tree starts with it — the universe text begins
    `"PARTIAL UNIVERSE: ..."` and belongs to a SCORED sleeve, not a refusal. A census that
    names a bucket nothing can fall into reads as coverage it does not have, which is the
    same defect in miniature as the one this function exists to catch.

    This test greps the two emitting modules for each declared prefix. It is a source-text
    check by necessity — the claim IS about what the source emits — and it is paired with
    the behavioural tests above rather than standing in for them."""
    from pathlib import Path

    from src.research_infra.walkforward import gate as G

    src = ""
    for mod in ("gate.py", "fidelity.py", "panel.py"):
        src += (Path(G.__file__).parent / mod).read_text()
    for cls in G._WIPEOUT_CLASSES:
        assert f'"{cls}' in src or f"'{cls}" in src or f"f\"{cls}" in src, (
            f"{cls!r} is declared a wipeout class but no site emits a reason starting with "
            f"it — either the emitter was renamed or the class is dead"
        )
    assert "symbol_outside_registry_universe" not in G._WIPEOUT_CLASSES


def test_the_dominant_class_does_not_depend_on_insertion_order():
    """`max(counts, key=...)` breaks ties by dict insertion order, which here is trade-
    arrival order — so two runs over the same sleeves in a different order could name a
    different dominant class. Ties now break on the class name."""
    a = {"x": _sv("x", reasons=["port_fidelity_unmeasured: q"]),
         "y": _sv("y", reasons=["cost_coverage_below_floor: q"])}
    b = {"y": a["y"], "x": a["x"]}
    assert _wipeout(a)["dominant_class"] == _wipeout(b)["dominant_class"]
    assert _wipeout(a)["dominant_class"] == "cost_coverage_below_floor"   # tie -> name asc
