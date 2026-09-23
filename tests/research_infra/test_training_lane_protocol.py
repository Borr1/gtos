"""The ratified training lane, pinned as BEHAVIOUR.

`phase14/TRAINING_LANE_RATIFICATION.md`, ratified by Borhen 2026-07-31. This file does for the
lane what `test_population_rule_ratified.py` does for the population rule and
`test_candidate_family.py` does for the admission rule: a change that drops an honesty property
is a red test, not a silent regression.

Every test here CALLS the machinery and asserts on what it returns. None greps a module for a
string — a source-string assertion passes against a wrong implementation (`CLAUDE.md` section 6),
and the whole point of this lane is that its honesty properties do not depend on anyone's
discipline, including the test author's.

The five properties, and the section of the ratification each comes from:

    section 2  the three surfaces, and March/blackout/live-forward refused whatever any
               partition says
    section 3  ONE bill, at graduation, and only there
    section 3  a candidate whose provenance shows TEST consumption is refused
    section 4  <= 5 concurrent incubants, <= 0.05-class weight, pre-registered stop AND
               promotion rules, arming is an owner ceremony
    section 5  the sealed admission rule is unchanged by anything in here
"""

from __future__ import annotations

import json
import pathlib

import pytest

from src.research_infra.trainer_partitions import (
    DEFAULT_REGISTRY,
    DEFAULT_SURFACE_MAP,
    LANE_ITERABLE_SURFACES,
    LIVE_FORWARD_SEALED_CUTOFF,
    SURFACES,
    SurfaceBand,
    SurfaceMap,
    SurfaceRefusal,
    UncoveredGap,
    lane_disposition_for_day,
)
from src.research_infra.training_lane import (
    MAX_CONCURRENT_INCUBANTS,
    MAX_INCUBANT_WEIGHT,
    Candidate,
    GraduationRefusal,
    Incubant,
    IncubationRefusal,
    IncubationRegistry,
    IterationLedger,
    IterationLedgerRefusal,
    OwnerCeremony,
    PreRegisteredRule,
    graduate,
)
from src.research_infra.training_lane.append_only import append_row, read_rows
from src.research_infra.training_lane.iteration_ledger import candidate_id, spec_digest
from src.research_infra.walkforward import candidate_family as CF

REPO = pathlib.Path(__file__).resolve().parents[2]
AUDIT = REPO / "docs/audits/fable5-vision-audit-20260725"

SPEC = {"target_r": 5.0, "time_stop_bars": 7680}
GATE_GLOBAL_SPAN = ("1992-02-18", "2026-07-27")
MARCH = [["2026-03-01", "2026-03-31"]]


# =============================================================================================
# section 2 — the three surfaces
# =============================================================================================
def test_the_surface_vocabulary_is_exactly_the_ratified_three():
    assert SURFACES == ("TRAIN", "VAL", "TEST")
    assert LANE_ITERABLE_SURFACES == frozenset({"TRAIN", "VAL"})


@pytest.mark.parametrize("day", ["1992-02-18", "2005-06-15", "2024-12-31"])
def test_archive_history_through_2024_is_train_and_iterable(day):
    d = DEFAULT_SURFACE_MAP.surface_for_day(day)
    assert (d.surface, d.iterable) == ("TRAIN", True)


@pytest.mark.parametrize("day", ["2025-01-01", "2026-01-15", "2026-04-20", "2026-05-31"])
def test_the_2025_2026H1_window_is_val_and_carries_its_used_once_disclosure(day):
    d = DEFAULT_SURFACE_MAP.surface_for_day(day)
    assert (d.surface, d.iterable) == ("VAL", True)
    assert "d.year >= 2025" in d.disclosure, (
        "a VAL day must drag the survivor-selection disclosure with it; a disclosure that "
        "lives only in a markdown table is one a tired session forgets"
    )


@pytest.mark.parametrize("day", ["2026-03-01", "2026-03-16", "2026-03-31"])
def test_march_2026_is_test_and_refused_by_the_blackout_not_by_a_band(day):
    d = DEFAULT_SURFACE_MAP.surface_for_day(day)
    assert d.surface == "TEST"
    assert d.iterable is False
    assert d.refusal == "day_inside_reserved_blackout"
    assert d.band_id.startswith("blackout:"), (
        "March must be refused by the blackout check, which runs BEFORE any band lookup — not "
        "by whichever band happens to cover it"
    )


def test_march_survives_a_hostile_map_that_declares_it_train():
    """The exact shape of the v1 partition defect, on the surface axis. A band that spans March
    cannot unlock it, because the blackout is checked first."""
    hostile = SurfaceMap(
        map_id="hostile",
        authored_utc="",
        bands=(SurfaceBand("swallows_march", "TRAIN", "2025-06-02", "2026-04-17"),),
    )
    d = hostile.surface_for_day("2026-03-16")
    assert d.iterable is False
    assert d.refusal == "day_inside_reserved_blackout"
    # ...and the same map DOES admit a day outside the blackout, so the refusal above is not
    # "this map refuses everything".
    assert hostile.surface_for_day("2026-02-16").iterable is True


@pytest.mark.parametrize("day", ["2026-07-29", "2026-07-30", "2026-07-31", "2027-06-01"])
def test_the_live_forward_stream_is_test_from_the_earliest_arming_date(day):
    d = DEFAULT_SURFACE_MAP.surface_for_day(day)
    assert (d.surface, d.iterable) == ("TEST", False)
    assert d.refusal == "surface_not_iterable:TEST"


def test_the_live_test_band_equals_sealed_holdout_semantics_at_the_declared_cutoff():
    """T4's boundary is not a second literal — it must agree with the module the estate
    already uses to classify a virgin bar."""
    from src.research_infra.validation_integrity.sealed_holdout import is_sealed

    for day in ("2026-07-27", "2026-07-28", "2026-07-29", "2026-08-15"):
        virgin = is_sealed(day, LIVE_FORWARD_SEALED_CUTOFF)
        on_test_band = DEFAULT_SURFACE_MAP.surface_for_day(day).band_id == "test_live_forward_stream"
        assert virgin == on_test_band, day


def test_a_day_covered_by_no_band_is_refused_not_defaulted():
    for day in ("1900-01-01", "1992-02-17", "2026-06-01", "2026-07-28"):
        d = DEFAULT_SURFACE_MAP.surface_for_day(day)
        assert d.iterable is False
        assert d.refusal == "day_outside_every_surface"
        assert d.surface is None


def test_the_declared_gap_is_recorded_with_its_measured_prior_consumption():
    """A gap with a receipt is a decision; a gap without one gets filled permissively later.
    This one is measurably already-consumed, so it must never be mistaken for virgin."""
    gap = next(g for g in DEFAULT_SURFACE_MAP.gaps if g.gap_id == "gap_2026H1_tail_pre_arming")
    assert (gap.start, gap.end) == ("2026-06-01", "2026-07-28")
    assert "NOT VIRGIN" in gap.prior_consumption
    assert "global_span" in gap.prior_consumption
    assert gap.as_dict()["disposition"] == "refused_day_outside_every_surface"


def test_april_16_to_30_is_not_opened_as_train_because_it_was_never_read():
    """T1, the load-bearing tightening. The ratified frame says 'April's 15 sealed days' under
    TRAIN; read as 'April' that would open fifteen days whose outcomes have never been read."""
    for day in ("2026-04-16", "2026-04-20", "2026-04-30"):
        d = DEFAULT_SURFACE_MAP.surface_for_day(day)
        assert d.surface == "VAL", f"{day} must not be freely iterable TRAIN"
    # ...and the boundary records WHY, citing the measured day. Pinning the date rather than
    # the wording: 2026-04-16 is the day B36 measured as having shards and zero ledger rows,
    # and a tightening whose justification stops naming it has lost its evidence.
    band = DEFAULT_SURFACE_MAP.band("val_selection_surface_2025_2026H1")
    assert "2026-04-16" in band.tightened_from


def test_the_two_axes_disagree_on_january_and_both_answers_travel():
    """SEALED (may not be FITTED — its outcomes were read) and VAL (may be ITERATED — a window
    whose outcomes are read protects nothing by being refused). Session CD's regeneration is
    commissioned on exactly this window."""
    ld = lane_disposition_for_day("2026-01-15")
    assert ld.may_iterate is True
    assert ld.may_fit is False
    assert ld.fitting.role == "SEALED"
    assert ld.surface.surface == "VAL"
    d = ld.as_dict()
    assert d["may_iterate"] != d["may_fit"]


def test_the_surface_axis_widens_nothing_on_the_fitting_axis():
    """T5. Not one additional day became fittable. Checked over the whole span both axes
    cover, not on a sample."""
    import datetime as dt

    from src.research_infra.trainer_partitions import TRAINABLE_ROLES

    day = dt.date(2025, 1, 1)
    end = dt.date(2026, 12, 31)
    while day <= end:
        fitting = DEFAULT_REGISTRY.disposition_for_day(day)
        assert fitting.trainable == (fitting.role in TRAINABLE_ROLES)
        day += dt.timedelta(days=1)


def test_the_surface_map_and_the_partition_registry_share_one_blackout():
    """Two lanes, one March. Independent modules with independent defaults; if they diverge,
    one of them silently stops protecting it. Checked, not claimed."""
    assert DEFAULT_SURFACE_MAP.blackout == DEFAULT_REGISTRY.reserved_blackout


def test_no_band_calls_a_blackout_or_forward_day_iterable():
    """The 'more restrictive wins' rule, mechanised across the whole surface map."""
    import datetime as dt

    day = dt.date(2025, 1, 1)
    end = dt.date(2027, 12, 31)
    while day <= end:
        s = DEFAULT_SURFACE_MAP.surface_for_day(day)
        f = DEFAULT_REGISTRY.disposition_for_day(day)
        if f.role in ("RESERVED_UNREAD", "FORWARD"):
            assert s.iterable is False, f"{day} is fitting-{f.role} but lane-iterable"
        day += dt.timedelta(days=1)


def test_overlapping_bands_and_gaps_inside_bands_are_rejected_at_construction():
    with pytest.raises(ValueError, match="overlapping surface bands"):
        SurfaceMap(map_id="x", authored_utc="", bands=(
            SurfaceBand("a", "TRAIN", "2020-01-01", "2020-06-30"),
            SurfaceBand("b", "VAL", "2020-06-01", "2020-12-31"),
        ))
    with pytest.raises(ValueError, match="intersects band"):
        SurfaceMap(map_id="x", authored_utc="", bands=(
            SurfaceBand("a", "TRAIN", "2020-01-01", "2020-06-30"),
        ), gaps=(UncoveredGap("g", "2020-03-01", "2020-03-31", "why"),))


def test_the_surface_map_digest_ignores_prose_and_moves_on_a_boundary():
    base = SurfaceMap(map_id="x", authored_utc="", bands=(
        SurfaceBand("a", "TRAIN", "2020-01-01", "2020-06-30", note="one"),))
    prose = SurfaceMap(map_id="x", authored_utc="", bands=(
        SurfaceBand("a", "TRAIN", "2020-01-01", "2020-06-30", note="two"),))
    moved = SurfaceMap(map_id="x", authored_utc="", bands=(
        SurfaceBand("a", "TRAIN", "2020-01-01", "2020-07-01", note="one"),))
    assert base.digest() == prose.digest(), "improving a note must not read as drift"
    assert base.digest() != moved.digest(), "moving a boundary must read as drift"


def test_assert_no_test_consumption_names_every_offender():
    with pytest.raises(SurfaceRefusal) as exc:
        DEFAULT_SURFACE_MAP.assert_no_test_consumption(
            ["2020-01-01", "2026-03-02", "2026-03-03", "2026-08-01"]
        )
    assert {d.day for d in exc.value.refusals} == {"2026-03-02", "2026-03-03", "2026-08-01"}


# =============================================================================================
# section 2/3 — the iteration ledger: logged, surface-stamped, and never billing
# =============================================================================================
@pytest.fixture()
def ledger(tmp_path):
    return IterationLedger(tmp_path / "ITER.jsonl", session="test", now_utc="2026-07-31T00:00:00+00:00")


def _look(led, **kw):
    kw.setdefault("mechanism", "donchian_20")
    kw.setdefault("sleeve", "mx_btcusd")
    kw.setdefault("spec", SPEC)
    kw.setdefault("engine_version", "train-engine-test")
    return led.record(**kw)


def test_a_look_is_logged_unbilled_and_stamped_by_the_map_not_the_caller(ledger):
    row = _look(ledger, start="2026-01-01", end="2026-01-31", verdict="improved", metric=0.98)
    assert row["billed"] is False
    assert row["surface"] == "VAL"
    assert row["surface_stamp"]["surface_map_digest"] == DEFAULT_SURFACE_MAP.digest()
    assert row["disclosures"], "a VAL look must carry the used-once disclosure"
    assert ledger.summary()["n_rows_claiming_billed"] == 0


def test_a_look_that_touches_test_is_refused(ledger):
    for span in (("2026-03-01", "2026-03-05"), ("2026-08-01", "2026-08-05")):
        with pytest.raises(IterationLedgerRefusal, match="TEST day"):
            _look(ledger, start=span[0], end=span[1])
    assert ledger.rows() == [], "a refused look must not land in the ledger"


def test_a_gate_verdict_cannot_be_recorded_as_an_exploration_look(ledger):
    """`admitted`/`rejected` are the sealed gate's words. A TRAIN/VAL look reporting one has
    either mislabelled itself or run the gate without billing it."""
    for bad in ("admitted", "rejected", "graduated"):
        with pytest.raises(IterationLedgerRefusal, match="sealed gate"):
            _look(ledger, start="2020-01-01", end="2020-02-01", verdict=bad)


def test_a_look_with_no_dates_has_no_surface_and_is_refused(ledger):
    with pytest.raises(IterationLedgerRefusal, match="must carry its dates"):
        _look(ledger)


def test_crossing_the_declared_gap_needs_the_gap_named(ledger):
    with pytest.raises(IterationLedgerRefusal, match="no declared surface"):
        _look(ledger, start="2026-05-25", end="2026-06-10")
    row = _look(ledger, start="2026-05-25", end="2026-06-10",
                acknowledge_uncovered=("gap_2026H1_tail_pre_arming",))
    assert row["acknowledged_gaps"] == ["gap_2026H1_tail_pre_arming"]
    assert row["surface_stamp"]["clean_for_iteration"] is False
    assert row["surface"] == "VAL", "UNCOVERED is not a surface; the field must stay useful"


def test_the_estates_own_full_history_walk_is_recordable(ledger):
    """The acceptance test that keeps this ledger usable. `GateSpec.global_span` spans March
    and the declared gap; the gate does not CONSUME March (`panel.py:249` drops those trades),
    so declaring the engine's blackout must make the walk loggable."""
    row = _look(ledger, start=GATE_GLOBAL_SPAN[0], end=GATE_GLOBAL_SPAN[1],
                engine_reserved_blackout=MARCH,
                acknowledge_uncovered=("gap_2026H1_tail_pre_arming",))
    assert row["blackout_days_excluded"] == 31
    assert row["surface_stamp"]["test_days"] == []
    assert set(row["surface_stamp"]["surfaces_present"]) == {"TRAIN", "VAL", "UNCOVERED"}


def test_the_engine_blackout_declaration_is_checked_in_both_directions(ledger):
    narrower = [["2026-03-01", "2026-03-15"]]
    with pytest.raises(IterationLedgerRefusal, match="NARROWER"):
        _look(ledger, start=GATE_GLOBAL_SPAN[0], end=GATE_GLOBAL_SPAN[1],
              engine_reserved_blackout=narrower,
              acknowledge_uncovered=("gap_2026H1_tail_pre_arming",))
    wider = [["2026-03-01", "2026-04-30"]]
    with pytest.raises(IterationLedgerRefusal, match="(?i)not lane blackout"):
        _look(ledger, start=GATE_GLOBAL_SPAN[0], end=GATE_GLOBAL_SPAN[1],
              engine_reserved_blackout=wider,
              acknowledge_uncovered=("gap_2026H1_tail_pre_arming",))


def test_the_live_forward_stream_cannot_be_excluded_by_declaring_it_a_blackout(ledger):
    """No engine setting makes a live day un-consumed."""
    with pytest.raises(IterationLedgerRefusal, match="(?i)not lane blackout"):
        _look(ledger, start="2026-07-25", end="2026-08-05",
              engine_reserved_blackout=[["2026-07-29", "2026-08-05"]])


def test_the_iteration_ledger_never_feeds_the_dsr_trial_ledger(ledger, tmp_path):
    """The sibling-ledger decision, asserted as behaviour: lane looks must not raise the DSR
    bill. That leak is the ratification's section 1.2 defect."""
    from src.research_infra.validation_integrity.trial_budget_ledger import measured_n_trials

    trial = tmp_path / "TRIAL_LEDGER.jsonl"
    trial.write_text("")
    before = measured_n_trials(ledger_paths=[trial])["n_prospective_look_events"]
    for i in range(25):
        _look(ledger, start="2020-01-01", end=f"2020-0{1 + i % 9}-28", spec={"k": i})
    after = measured_n_trials(ledger_paths=[trial])["n_prospective_look_events"]
    assert ledger.summary()["n_looks"] == 25
    assert before == after == 0, "25 exploration looks must move the DSR bill by exactly nothing"
    reported = ledger.summary(trial_ledger_paths=[trial])
    assert "dsr_trial_ledger" in reported, "the two bills are reported side by side, never summed"


# =============================================================================================
# section 3 — ONE bill, at graduation, and only there
# =============================================================================================
@pytest.fixture()
def head_declaration():
    p = AUDIT / "phase14/receipts/CANDIDATE_FAMILY_V13.json"
    if not p.is_file():
        pytest.skip("V13 not present in this tree")
    return p


def _iterated_candidate(led, name="cc_test_candidate", spec=None):
    spec = SPEC if spec is None else spec
    cid = candidate_id(mechanism="donchian_20", sleeve="mx_btcusd", spec=spec)
    for span in (("2019-01-01", "2020-12-31"), ("2026-01-01", "2026-01-31")):
        _look(led, start=span[0], end=span[1], spec=spec, verdict="improved")
    return Candidate(candidate_id=cid, name=name, sleeve="mx_btcusd",
                     spec_digest=spec_digest(spec), basis="test", source="test",
                     proposed_by="test")


def test_graduation_bills_exactly_one_look_and_the_ratchet_moves_by_one(
    ledger, tmp_path, head_declaration
):
    before = CF.load_candidate_family(head_declaration)
    cand = _iterated_candidate(ledger)
    rec = graduate(cand, iteration_ledger=ledger.path, declaration=head_declaration,
                   out_declaration=tmp_path / "NEXT.json",
                   graduation_ledger=tmp_path / "GRAD.jsonl", declared_at="2026-07-31")
    assert rec.billed_looks == 1
    assert rec.declared_family_size == before.effective_size("CANDIDATE_BOOK_V1") + 1
    assert rec.looks_taken_size == before.family("CANDIDATE_BOOK_V1").looks_taken_size() + 1
    # and the successor declaration loads through the estate's own validating loader
    after = CF.load_candidate_family(tmp_path / "NEXT.json")
    assert after.effective_size("CANDIDATE_BOOK_V1") == rec.declared_family_size


def test_graduation_is_idempotent_so_a_retry_cannot_double_bill(
    ledger, tmp_path, head_declaration
):
    """The bill is paid before the receipt is written, so a crash between them leaves the
    estate over-billed and re-runnable. A ratchet a retry could pay twice is not a ratchet."""
    cand = _iterated_candidate(ledger)
    first = graduate(cand, iteration_ledger=ledger.path, declaration=head_declaration,
                     out_declaration=tmp_path / "NEXT.json",
                     graduation_ledger=tmp_path / "GRAD.jsonl", declared_at="2026-07-31")
    second = graduate(cand, iteration_ledger=ledger.path, declaration=tmp_path / "NEXT.json",
                      out_declaration=tmp_path / "MUST_NOT_EXIST.json",
                      graduation_ledger=tmp_path / "GRAD.jsonl", declared_at="2026-07-31")
    assert second.billed_looks == 0
    assert second.idempotent_completion is True
    assert second.declared_family_size == first.declared_family_size
    assert not (tmp_path / "MUST_NOT_EXIST.json").exists()
    assert len(read_rows(tmp_path / "GRAD.jsonl")) == 1, "one graduation, one receipt"


def test_a_candidate_with_no_logged_provenance_cannot_graduate(tmp_path, head_declaration):
    empty = tmp_path / "EMPTY.jsonl"
    empty.write_text("")
    cand = Candidate(candidate_id="0" * 16, name="ghost", sleeve="s", spec_digest="a" * 64,
                     basis="b", source="s", proposed_by="p")
    with pytest.raises(GraduationRefusal) as exc:
        graduate(cand, iteration_ledger=empty, declaration=head_declaration,
                 out_declaration=tmp_path / "N.json", graduation_ledger=tmp_path / "G.jsonl",
                 declared_at="2026-07-31")
    assert exc.value.reason == "provenance_missing"
    assert not (tmp_path / "N.json").exists(), "a refused graduation bills nothing"


def test_provenance_that_touched_test_is_refused_even_if_the_ledger_was_edited(
    ledger, tmp_path, head_declaration
):
    """The ledger refuses a TEST look at write time. This is the second line: a hand-written
    row claiming a clean surface but carrying TEST days in its stamp still cannot graduate,
    because the biller reads the STAMP, not the label."""
    cand = _iterated_candidate(ledger)
    forged = dict(ledger.rows()[0])
    forged["surface"] = "VAL"
    forged["surface_stamp"] = dict(forged["surface_stamp"])
    forged["surface_stamp"]["test_days"] = ["2026-03-10"]
    append_row(ledger.path, forged)
    with pytest.raises(GraduationRefusal) as exc:
        graduate(cand, iteration_ledger=ledger.path, declaration=head_declaration,
                 out_declaration=tmp_path / "N.json", graduation_ledger=tmp_path / "G.jsonl",
                 declared_at="2026-07-31")
    assert exc.value.reason == "provenance_touches_test"
    assert not (tmp_path / "N.json").exists()


def test_a_spec_that_was_never_looked_at_cannot_graduate(ledger, tmp_path, head_declaration):
    _iterated_candidate(ledger)
    unseen = Candidate(
        candidate_id=candidate_id(mechanism="donchian_20", sleeve="mx_btcusd", spec=SPEC),
        name="unseen", sleeve="mx_btcusd", spec_digest="f" * 64,
        basis="b", source="s", proposed_by="p")
    with pytest.raises(GraduationRefusal) as exc:
        graduate(unseen, iteration_ledger=ledger.path, declaration=head_declaration,
                 out_declaration=tmp_path / "N.json", graduation_ledger=tmp_path / "G.jsonl",
                 declared_at="2026-07-31")
    assert exc.value.reason == "provenance_spec_mismatch"


def test_a_declaration_that_lost_the_ratified_rule_cannot_be_billed_against(
    ledger, tmp_path, head_declaration
):
    """Not hypothetical: CANDIDATE_FAMILY V3 through V11 all dropped `ratified_rule` (B2204)."""
    stripped = json.loads(head_declaration.read_text())
    stripped.pop("ratified_rule", None)
    p = tmp_path / "NO_RULE.json"
    p.write_text(json.dumps(stripped))
    cand = _iterated_candidate(ledger)
    with pytest.raises(GraduationRefusal) as exc:
        graduate(cand, iteration_ledger=ledger.path, declaration=p,
                 out_declaration=tmp_path / "N.json", graduation_ledger=tmp_path / "G.jsonl",
                 declared_at="2026-07-31")
    assert exc.value.reason == "declaration_lost_the_rule"


def test_an_undeclared_family_has_no_fallback(ledger, tmp_path, head_declaration):
    cand = _iterated_candidate(ledger)
    with pytest.raises(GraduationRefusal) as exc:
        graduate(cand, family_id="NOT_A_FAMILY", iteration_ledger=ledger.path,
                 declaration=head_declaration, out_declaration=tmp_path / "N.json",
                 graduation_ledger=tmp_path / "G.jsonl", declared_at="2026-07-31")
    assert exc.value.reason == "unknown_family"


def test_the_graduation_record_carries_the_frozen_rule_into_the_gate_spec(
    ledger, tmp_path, head_declaration
):
    """`apply_to_spec` is the wiring, and it must go through the estate's existing resolver so
    there is no second way to set a family size."""
    from src.research_infra.walkforward.spec import DEFAULT_SPEC

    cand = _iterated_candidate(ledger)
    rec = graduate(cand, iteration_ledger=ledger.path, declaration=head_declaration,
                   out_declaration=tmp_path / "NEXT.json",
                   graduation_ledger=tmp_path / "GRAD.jsonl", declared_at="2026-07-31")
    assert rec.ratified_rule["family"] == "CANDIDATE_BOOK_V1"
    assert rec.ratified_rule["alpha"] == pytest.approx(0.10)
    assert rec.ratified_rule["option"] == "B_balanced"
    spec = rec.apply_to_spec(DEFAULT_SPEC)
    assert spec.declared_family_size == rec.declared_family_size
    assert spec.declared_family_id == rec.declared_family_id


# =============================================================================================
# section 4 — incubation
# =============================================================================================
def _rule(rid, kind="stop"):
    return PreRegisteredRule(
        rule_id=rid,
        what=f"the {kind} condition",
        class_="RISK_BOUND_not_inference",
        action="remove from --tags (owner ceremony)" if kind == "stop" else "propose promotion",
        threshold=-12.375 if kind == "stop" else 30,
        basis="phase11/receipts/FIVE_SLEEVE_STOP_CONDITIONS_V1.json",
        pre_registered_utc="2026-07-31T00:00:00+00:00",
        why_not_inference="bounds what the owner pays to find out; it does not test an edge",
    )


def _incubant(i=0, weight=0.025, **kw):
    kw.setdefault("admission_basis", "OWNER_RISK_ACCEPTED")
    kw.setdefault("owner_risk_acceptance", "phase8/receipts/FIVE_SLEEVE_EXPANSION_20260730.md")
    return Incubant(
        incubant_id=f"inc_{i}", sleeve=f"sleeve_{i}", account="FTMO",
        proposed_weight=weight, evidence="phase14/receipts/TEST.json",
        stop_rules=(_rule(f"S{i}", "stop"),), promotion_rules=(_rule(f"P{i}", "promote"),),
        proposed_by="test", **kw)


@pytest.fixture()
def incubation(tmp_path):
    return IncubationRegistry(tmp_path / "INC.jsonl", session="test",
                              now_utc="2026-07-31T00:00:00+00:00")


def test_a_weight_above_the_incubation_ceiling_is_refused():
    with pytest.raises(IncubationRefusal) as exc:
        _incubant(weight=MAX_INCUBANT_WEIGHT * 2)
    assert exc.value.reason == "weight_above_incubation_ceiling"
    _incubant(weight=MAX_INCUBANT_WEIGHT)  # exactly at the ceiling is allowed


def test_a_registration_without_pre_registered_stop_AND_promotion_rules_is_refused():
    with pytest.raises(IncubationRefusal) as exc:
        Incubant(incubant_id="x", sleeve="s", account="FTMO", proposed_weight=0.025,
                 admission_basis="OWNER_RISK_ACCEPTED", owner_risk_acceptance="r",
                 evidence="e", stop_rules=(), promotion_rules=(_rule("P"),))
    assert exc.value.reason == "stop_rule_missing"
    with pytest.raises(IncubationRefusal) as exc:
        Incubant(incubant_id="x", sleeve="s", account="FTMO", proposed_weight=0.025,
                 admission_basis="OWNER_RISK_ACCEPTED", owner_risk_acceptance="r",
                 evidence="e", stop_rules=(_rule("S"),), promotion_rules=())
    assert exc.value.reason == "promotion_rule_missing"


def test_a_rule_with_no_basis_is_refused():
    with pytest.raises(IncubationRefusal) as exc:
        PreRegisteredRule(rule_id="S", what="w", class_="ECONOMIC", action="a",
                          threshold=1.0, basis="", pre_registered_utc="2026-07-31T00:00:00Z")
    assert exc.value.reason == "rule_incomplete"


def test_a_rule_cannot_claim_to_be_an_inference():
    with pytest.raises(IncubationRefusal) as exc:
        PreRegisteredRule(rule_id="S", what="w", class_="inference", action="a", threshold=1.0,
                          basis="b", pre_registered_utc="2026-07-31T00:00:00Z")
    assert exc.value.reason == "rule_class_unknown"


def test_the_two_intakes_must_cite_their_own_evidence():
    with pytest.raises(IncubationRefusal) as exc:
        Incubant(incubant_id="x", sleeve="s", account="FTMO", proposed_weight=0.025,
                 admission_basis="GRADUATED", evidence="e",
                 stop_rules=(_rule("S"),), promotion_rules=(_rule("P"),))
    assert exc.value.reason == "graduation_record_missing"
    with pytest.raises(IncubationRefusal) as exc:
        Incubant(incubant_id="x", sleeve="s", account="FTMO", proposed_weight=0.025,
                 admission_basis="OWNER_RISK_ACCEPTED", evidence="e",
                 stop_rules=(_rule("S"),), promotion_rules=(_rule("P"),))
    assert exc.value.reason == "owner_risk_acceptance_missing"
    with pytest.raises(IncubationRefusal) as exc:
        Incubant(incubant_id="x", sleeve="s", account="FTMO", proposed_weight=0.025,
                 admission_basis="PROBABLY_FINE", evidence="e",
                 stop_rules=(_rule("S"),), promotion_rules=(_rule("P"),))
    assert exc.value.reason == "admission_basis_unknown"


def test_arming_a_sixth_incubant_is_refused(incubation):
    cer = OwnerCeremony(decided_by="Borhen", decided_utc="2026-07-31T12:00:00+00:00",
                        receipt="phase14/receipts/TEST_CEREMONY.md")
    for i in range(MAX_CONCURRENT_INCUBANTS):
        incubation.register(_incubant(i))
        incubation.arm(f"inc_{i}", cer)
    assert incubation.capacity()["headroom"] == 0
    incubation.register(_incubant(99))
    with pytest.raises(IncubationRefusal) as exc:
        incubation.arm("inc_99", cer)
    assert exc.value.reason == "incubation_capacity_full"
    # ...and pulling one makes room, so the ceiling is a ceiling and not a deadlock
    incubation.pull("inc_0", cer, tripped_rule="S0")
    assert incubation.arm("inc_99", cer)["state"] == "ARMED"


def test_registering_a_dossier_does_not_consume_capacity(incubation):
    for i in range(8):
        incubation.register(_incubant(i))
    assert incubation.capacity()["armed"] == 0
    assert incubation.capacity()["headroom"] == MAX_CONCURRENT_INCUBANTS


def test_every_transition_needs_an_owner_ceremony_with_a_receipt(incubation):
    incubation.register(_incubant(1))
    with pytest.raises(IncubationRefusal) as exc:
        OwnerCeremony(decided_by="Borhen", decided_utc="2026-07-31T12:00:00+00:00", receipt="")
    assert exc.value.reason == "ceremony_incomplete"
    with pytest.raises(TypeError):
        incubation.arm("inc_1")  # no ceremony argument at all


def test_rules_written_after_the_arming_are_not_pre_registered(incubation):
    incubation.register(_incubant(2))
    late = OwnerCeremony(decided_by="Borhen", decided_utc="2026-07-30T00:00:00+00:00",
                         receipt="r")
    with pytest.raises(IncubationRefusal) as exc:
        incubation.arm("inc_2", late)
    assert exc.value.reason == "rules_not_pre_registered"


def test_pre_registration_compares_instants_not_strings(incubation):
    """Two defects in one test, both found by writing it.

    (1) ISO offsets are not lexicographically ordered: `...T00:00:00Z` sorts ABOVE
    `...T00:00:00+00:00` (`'Z' > '+'`) while denoting the same moment, so a string compare fails
    on whichever session happens to spell it with `Z` — and both spellings are valid.

    (2) The check must bind on the LATEST rule, not the earliest. This incubant's PROMOTION rule
    predates the ceremony while its STOP rule was written an hour after it; an earliest-rule
    check passes it, which is exactly the shape of adding a rule once the fills are visible.
    The first implementation did that and this test is what caught it.
    """
    rule = PreRegisteredRule(
        rule_id="S_z", what="w", class_="ECONOMIC", action="a", threshold=1.0, basis="b",
        # one hour AFTER the ceremony below, spelled with Z
        pre_registered_utc="2026-07-31T13:00:00Z",
    )
    incubation.register(Incubant(
        incubant_id="inc_tz", sleeve="s", account="FTMO", proposed_weight=0.01,
        admission_basis="OWNER_RISK_ACCEPTED", owner_risk_acceptance="r", evidence="e",
        stop_rules=(rule,), promotion_rules=(_rule("P_tz", "promote"),)))
    cer = OwnerCeremony(decided_by="Borhen", decided_utc="2026-07-31T12:00:00+00:00", receipt="r")
    with pytest.raises(IncubationRefusal) as exc:
        incubation.arm("inc_tz", cer)
    assert exc.value.reason == "rules_not_pre_registered"
    assert exc.value.detail["latest_rule"] == "S_z"


def test_a_hand_written_row_with_no_rules_is_refused_at_arming(incubation, tmp_path):
    """`register()` refuses a ruleless incubant, so such a row can only be hand-written into the
    ledger. It must refuse, not crash on an empty `min()`."""
    append_row(incubation.path, {"incubant_id": "smuggled", "state": "PROPOSED",
                                 "sleeve": "s", "proposed_weight": 0.01})
    cer = OwnerCeremony(decided_by="Borhen", decided_utc="2026-07-31T12:00:00+00:00", receipt="r")
    with pytest.raises(IncubationRefusal) as exc:
        incubation.arm("smuggled", cer)
    assert exc.value.reason == "rules_missing_on_record"


def test_a_sleeve_cannot_be_promoted_out_of_a_lane_it_never_entered(incubation):
    cer = OwnerCeremony(decided_by="Borhen", decided_utc="2026-07-31T12:00:00+00:00", receipt="r")
    incubation.register(_incubant(3))
    with pytest.raises(IncubationRefusal) as exc:
        incubation.promote("inc_3", cer)
    assert exc.value.reason == "illegal_transition"


def test_the_registry_is_append_only_and_its_state_is_the_fold(incubation):
    cer = OwnerCeremony(decided_by="Borhen", decided_utc="2026-07-31T12:00:00+00:00", receipt="r")
    incubation.register(_incubant(4))
    incubation.arm("inc_4", cer)
    incubation.pull("inc_4", cer, tripped_rule="S4")
    assert len(incubation.rows()) == 3, "history is kept, not overwritten"
    assert incubation.state()["inc_4"]["state"] == "STOPPED"
    assert incubation.state()["inc_4"]["tripped_rule"] == "S4"
    assert incubation.summary()["capacity"]["armed"] == 0


# =============================================================================================
# section 5 — nothing here moved the sealed admission rule
# =============================================================================================
def test_the_ratified_admission_rule_is_unchanged_by_this_lane(head_declaration):
    rule = json.loads(head_declaration.read_text())["ratified_rule"]
    assert rule["family"] == "CANDIDATE_BOOK_V1"
    assert rule["basis"] == CF.ALL_DECLARED
    assert rule["alpha"] == pytest.approx(0.10)
    assert rule["option"] == "B_balanced"
    assert "Borhen" in rule["ratified_by"]


def test_v13_is_membership_identical_to_v12(head_declaration):
    """V13 restores a dropped rule. It must declare no member and take no look — the lane makes
    searching cheap, never billing. (Renumbered from V12 at the wave-14 train: Session CA's
    look declaration took the V12 number first, per CC's own collision note.)"""
    v12 = CF.load_candidate_family(AUDIT / "phase14/receipts/CANDIDATE_FAMILY_V12.json")
    v13 = CF.load_candidate_family(head_declaration)
    assert v13.membership_sha256 == v12.membership_sha256
    for fid in v12.families:
        assert v13.effective_size(fid) == v12.effective_size(fid)
        assert v13.effective_size(fid, CF.LOOKS_TAKEN) == v12.effective_size(fid, CF.LOOKS_TAKEN)


def test_v12_added_exactly_one_look_and_no_member_over_v11():
    """The other half of the collision, pinned: CA's V12 is V11 plus ONE look (vp_euidx_pocgrav
    declared-not-taken -> TAKEN, mirrored in CANDIDATE_BOOK_V1 and ESTATE_UNION_V1) and ZERO
    new members — so the renumber changed no arithmetic and no other candidate's bar."""
    v11 = CF.load_candidate_family(AUDIT / "phase13/receipts/CANDIDATE_FAMILY_V11.json")
    v12 = CF.load_candidate_family(AUDIT / "phase14/receipts/CANDIDATE_FAMILY_V12.json")
    for fid in v11.families:
        assert v12.effective_size(fid) == v11.effective_size(fid), fid
    deltas = {
        fid: v12.effective_size(fid, CF.LOOKS_TAKEN) - v11.effective_size(fid, CF.LOOKS_TAKEN)
        for fid in v11.families
    }
    assert deltas["CANDIDATE_BOOK_V1"] == 1
    assert deltas["ESTATE_UNION_V1"] == 1
    assert all(d in (0, 1) for d in deltas.values())


def test_no_declaration_on_disk_supersedes_the_chain_head():
    """The mechanism repair behind B2204, not the instance. `DECLARATION_CHAIN` stopped at V2
    while eleven declarations sat on disk, so the default resolved a 51 % under-bill. Discovery
    is a TEST, never the resolution — a sparse-checkout-excluded file must not be able to move
    what the default resolves to."""
    head = CF.DEFAULT_DECLARATION.resolve()
    in_chain = {p.resolve() for p in CF.DECLARATION_CHAIN}
    orphans = []
    for p in sorted(AUDIT.rglob("CANDIDATE_FAMILY_V*.json")):
        if p.resolve() in in_chain:
            continue
        sup = (json.loads(p.read_text()).get("supersedes") or "")
        if sup and pathlib.Path(sup).name in {q.name for q in in_chain}:
            orphans.append(p.name)
    assert not orphans, (
        f"declaration(s) {orphans} supersede a link in DECLARATION_CHAIN but are not IN it, so "
        f"DEFAULT_DECLARATION resolves a family SMALLER than the estate's real bill — the "
        f"permissive direction. Append them to DECLARATION_CHAIN in "
        f"src/research_infra/walkforward/candidate_family.py."
    )


def test_the_contamination_audit_receipt_describes_the_live_surface_map():
    """CC-1's artifact must not go stale behind the code. A receipt that describes a map the
    module no longer has is worse than no receipt: it is a measurement someone will cite."""
    p = AUDIT / "phase14/receipts/CC_CONTAMINATION_AUDIT_V1.json"
    if not p.is_file():
        pytest.skip("contamination audit not present in this tree")
    doc = json.loads(p.read_text())
    assert doc["surface_map"]["digest"] == DEFAULT_SURFACE_MAP.digest(), (
        "the committed contamination audit describes a different surface map than the module "
        "exports. Re-run phase14/receipts/cc_contamination_audit.py."
    )
    assert doc["loosenings_vs_the_ratified_frame"] == [], (
        "the ratified frame is 'CC audits and may tighten, never loosen'"
    )
    assert set(doc["tightenings_vs_the_ratified_frame"]) == {"T1", "T2", "T3", "T4", "T5"}
    # The coverage scan is the claim that the map has no silent hole. Assert its shape rather
    # than its prose: exactly one uncovered stretch inside the modern era, and it is the
    # declared gap.
    modern = [r for r in doc["coverage"]["runs"] if r["to"] >= "1992-02-18"]
    holes = [r for r in modern if r["surface"] is None]
    assert [r["band_id"] for r in holes] == ["gap:gap_2026H1_tail_pre_arming"]


def test_the_lane_cannot_reach_the_live_config_or_the_vps():
    """A structural check, cheap and worth having: nothing in the lane names a live config or a
    broker module. The estate's brake is three YAML booleans and an activation token; a
    training lane that could touch either would be a new way to arm a book."""
    lane = REPO / "src/research_infra/training_lane"
    forbidden = ("agent_config.yaml", "profiles/redacted_account", "MetaTrader5", "order_send",
                 "mt5_real", "run_book")
    for py in sorted(lane.glob("*.py")):
        text = py.read_text()
        for token in forbidden:
            assert token not in text, f"{py.name} names {token!r}"
