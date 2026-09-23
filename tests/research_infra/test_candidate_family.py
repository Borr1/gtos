"""The prospective family declaration: the ratchet, the refusals, and the seals.

Every guard `CANDIDATE_FAMILY_V1.json`'s `freeze_rule` claims is exercised here. A rule nobody
tested is a comment, and this one is the whole mechanism between `mx_btcusd` and a verdict.

The seal tests are the load-bearing ones for the rest of the estate: they pin that adding
`declared_family_id` / `declared_family_sha256` to `GateSpec` moved no seal, that the
`spread_band` repair restores the **18** published `spec_sha256` values whose lineage predated
AG's field addition, and — because the whole complaint against that addition was that it broke
seals SILENTLY — that the **10** it breaks in the other direction are named rather than
discovered later by a failing control.
"""

from __future__ import annotations

import copy
import json

import pytest

from src.research_infra.walkforward import candidate_family as CF
from src.research_infra.walkforward.fidelity import FidelityReferencePolicy
from src.research_infra.walkforward.spec import (
    DEFAULT_SPEC,
    LEGACY_DEFAULT_SPEC,
    LEGACY_SCHEMA,
    GateSpec,
)


# ---------------------------------------------------------------------------------
def _member(name="a", **kw):
    d = {"name": name, "source": "test", "basis": "test", "declared_at": "2026-07-30"}
    d.update(kw)
    return d


def _doc(members=None, **fam):
    members = members if members is not None else [_member("a"), _member("b"), _member("c")]
    f = {"purpose": "test", "declaration_date": "2026-07-30",
         "high_water_size": len(members),
         "high_water_looks": sum(1 for m in members if m.get("look_taken", True)),
         "members": members, "history": []}
    f.update(fam)
    return {"schema": CF.SCHEMA, "declaration_date": "2026-07-30", "families": {"F": f}}


def _load(doc, tmp_path):
    p = tmp_path / "decl.json"
    p.write_text(json.dumps(doc, default=str))
    return CF.load_candidate_family(p)


# ---------------------------------------------------------------------------------
# the ratchet
# ---------------------------------------------------------------------------------
def test_effective_size_is_the_declared_row_count(tmp_path):
    f = _load(_doc(), tmp_path).family("F")
    assert f.effective_size() == 3
    assert f.looks_taken_size() == 3


def test_a_withdrawal_does_not_lower_the_bill(tmp_path):
    d = _doc()
    d["families"]["F"]["members"][0].update(
        status=CF.WITHDRAWN, withdrawn_at="2026-08-01", withdrawn_reason="test")
    f = _load(d, tmp_path).family("F")
    assert f.effective_size() == 3, (
        "a withdrawn member's look was still taken; letting a withdrawal shrink the family "
        "makes 'withdraw the siblings' the cheapest route to an admission")
    assert len(f.active()) == 2
    assert len(f.withdrawn()) == 1


def test_a_withdrawal_without_a_date_is_refused(tmp_path):
    d = _doc()
    d["families"]["F"]["members"][0]["status"] = CF.WITHDRAWN
    with pytest.raises(CF.CandidateFamilyError, match="withdrawn_at"):
        _load(d, tmp_path)


def test_deleting_a_member_row_is_refused(tmp_path):
    d = _doc()
    d["families"]["F"]["members"].pop()
    with pytest.raises(CF.CandidateFamilyError, match="DELETED"):
        _load(d, tmp_path)


def test_a_missing_high_water_size_is_refused(tmp_path):
    d = _doc()
    del d["families"]["F"]["high_water_size"]
    with pytest.raises(CF.CandidateFamilyError, match="high_water_size"):
        _load(d, tmp_path)


def test_an_unlogged_late_addition_is_refused(tmp_path):
    d = _doc()
    d["families"]["F"]["members"].append(_member("late", declared_at="2026-09-01"))
    d["families"]["F"]["high_water_size"] = 4
    d["families"]["F"]["high_water_looks"] = 4
    with pytest.raises(CF.CandidateFamilyError, match="declared_at after"):
        _load(d, tmp_path)


def test_a_logged_late_addition_is_accepted_and_raises_the_bill(tmp_path):
    d = _doc()
    d["families"]["F"]["members"].append(_member("late", declared_at="2026-09-01"))
    d["families"]["F"]["high_water_size"] = 4
    d["families"]["F"]["high_water_looks"] = 4
    d["families"]["F"]["history"] = [
        {"utc": "2026-09-01", "members_added": ["late"], "why": "test"}]
    f = _load(d, tmp_path).family("F")
    assert f.effective_size() == 4


def test_a_repeated_member_is_refused(tmp_path):
    d = _doc(members=[_member("a"), _member("a"), _member("b")])
    with pytest.raises(CF.CandidateFamilyError, match="repeats member"):
        _load(d, tmp_path)


# ---------------------------------------------------------------------------------
# the one field that can make a family cheaper
# ---------------------------------------------------------------------------------
def test_looks_taken_excludes_a_zero_trade_member_and_is_never_the_default(tmp_path):
    d = _doc(members=[_member("a"), _member("b"),
                      _member("nogen", look_taken=False,
                              no_look_evidence="n_trades = 0, verdict NOT_EVALUABLE")])
    d["families"]["F"]["high_water_looks"] = 2
    fam = _load(d, tmp_path)
    f = fam.family("F")
    assert f.effective_size() == 3
    assert f.looks_taken_size() == 2
    assert fam.effective_size("F") == 3, "the DEFAULT basis must be the conservative one"
    assert fam.effective_size("F", CF.LOOKS_TAKEN) == 2


def test_look_taken_false_without_evidence_is_refused(tmp_path):
    d = _doc(members=[_member("a"), _member("nogen", look_taken=False)])
    d["families"]["F"]["high_water_size"] = 2
    d["families"]["F"]["high_water_looks"] = 1
    with pytest.raises(CF.CandidateFamilyError, match="no_look_evidence"):
        _load(d, tmp_path)


def test_retracting_a_look_after_the_fact_is_refused(tmp_path):
    d = _doc()
    d["families"]["F"]["members"][0].update(
        look_taken=False, no_look_evidence="a retraction dressed as an exclusion")
    with pytest.raises(CF.CandidateFamilyError, match="high_water_looks"):
        _load(d, tmp_path)


def test_an_unknown_basis_is_refused(tmp_path):
    f = _load(_doc(), tmp_path).family("F")
    with pytest.raises(CF.CandidateFamilyError, match="unknown basis"):
        f.size_for("whatever_is_cheapest")


# ---------------------------------------------------------------------------------
# loader failure modes: every branch fails CLOSED
# ---------------------------------------------------------------------------------
def test_an_unreadable_declaration_raises_rather_than_defaulting(tmp_path):
    with pytest.raises(CF.CandidateFamilyError, match="cannot read"):
        CF.load_candidate_family(tmp_path / "nope.json")


def test_a_wrong_schema_is_refused(tmp_path):
    d = _doc()
    d["schema"] = "something.else.v9"
    with pytest.raises(CF.CandidateFamilyError, match="schema"):
        _load(d, tmp_path)


def test_a_declaration_with_no_families_is_refused(tmp_path):
    with pytest.raises(CF.CandidateFamilyError, match="no families"):
        _load({"schema": CF.SCHEMA, "declaration_date": "2026-07-30", "families": {}},
              tmp_path)


def test_an_unknown_family_id_is_refused(tmp_path):
    fam = _load(_doc(), tmp_path)
    with pytest.raises(CF.CandidateFamilyError, match="unknown family"):
        fam.family("NOT_DECLARED")


def test_a_bad_date_is_refused(tmp_path):
    d = _doc(members=[_member("a", declared_at="soon"), _member("b")])
    with pytest.raises(CF.CandidateFamilyError, match="not an ISO date"):
        _load(d, tmp_path)


# ---------------------------------------------------------------------------------
# the spec side: the seal
# ---------------------------------------------------------------------------------
def test_with_declared_family_carries_the_size_and_the_provenance(tmp_path):
    fam = _load(_doc(), tmp_path)
    s = CF.with_declared_family(DEFAULT_SPEC, "F", loaded=fam)
    assert s.declared_family_size == 3
    assert s.declared_family_sha256 == fam.sha256, "the FILE sha travels as provenance"
    assert s.declared_family_id == f"{fam.membership_of('F')[:12]}:F", (
        "the ID must carry the per-family MEMBERSHIP hash, not the file's")
    assert s.seal() != DEFAULT_SPEC.seal(), "a consulted declaration must move the seal"


def test_prose_does_not_move_a_family_identity_but_membership_does(tmp_path):
    """The defect this replaced: the id was the FILE sha, so editing a `basis` string or adding
    a documentation key read as a different family. `spec.canonical()` pops `notes` for exactly
    this reason — "free-form commentary must not be able to change the seal, or every typo fix
    would read as a methodology change." Caught when an adversarial pass forced a documentation
    edit and the id moved while every declared size did not."""
    base = _doc()
    fam0 = _load(base, tmp_path)
    id0 = CF.with_declared_family(DEFAULT_SPEC, "F", loaded=fam0).declared_family_id

    prose = copy.deepcopy(base)
    prose["families"]["F"]["purpose"] = "reworded, same members"
    prose["families"]["F"]["note"] = "a note nobody had written before"
    prose["families"]["F"]["members"][0]["basis"] = "a better sentence about the same member"
    fam1 = _load(prose, tmp_path)
    id1 = CF.with_declared_family(DEFAULT_SPEC, "F", loaded=fam1).declared_family_id
    assert id1 == id0, "prose must not move a family identity"
    assert fam1.sha256 != fam0.sha256, "...while the FILE sha legitimately does"

    grown = copy.deepcopy(base)
    grown["families"]["F"]["members"].append(_member("late", declared_at="2026-09-01"))
    grown["families"]["F"]["high_water_size"] = 4
    grown["families"]["F"]["high_water_looks"] = 4
    grown["families"]["F"]["history"] = [
        {"utc": "2026-09-01", "members_added": ["late"], "why": "test"}]
    fam2 = _load(grown, tmp_path)
    id2 = CF.with_declared_family(DEFAULT_SPEC, "F", loaded=fam2).declared_family_id
    assert id2 != id0, "MEMBERSHIP must move it"


def test_one_familys_identity_does_not_move_when_another_changes(tmp_path):
    d = _doc()
    d["families"]["G"] = {
        "purpose": "second", "declaration_date": "2026-07-30", "high_water_size": 2,
        "high_water_looks": 2, "members": [_member("x"), _member("y")], "history": []}
    fam0 = _load(d, tmp_path)
    f_id0 = fam0.membership_of("F")
    d["families"]["G"]["members"].append(_member("z"))
    d["families"]["G"]["high_water_size"] = 3
    d["families"]["G"]["high_water_looks"] = 3
    d["families"]["G"]["history"] = [{"utc": "2026-07-30", "members_added": ["z"]}]
    fam1 = _load(d, tmp_path)
    assert fam1.membership_of("F") == f_id0
    assert fam1.membership_of("G") != fam0.membership_of("G")


def test_the_looks_taken_basis_is_named_in_the_id_so_it_cannot_be_used_silently(tmp_path):
    d = _doc(members=[_member("a"), _member("b"),
                      _member("nogen", look_taken=False, no_look_evidence="0 trades")])
    d["families"]["F"]["high_water_looks"] = 2
    fam = _load(d, tmp_path)
    cheap = CF.with_declared_family(DEFAULT_SPEC, "F", basis=CF.LOOKS_TAKEN, loaded=fam)
    dear = CF.with_declared_family(DEFAULT_SPEC, "F", loaded=fam)
    assert cheap.declared_family_size < dear.declared_family_size
    assert cheap.declared_family_id.endswith("@looks_taken")
    assert not dear.declared_family_id.endswith("@looks_taken")
    assert cheap.seal() != dear.seal()


def test_half_a_provenance_is_refused():
    with pytest.raises(ValueError, match="must be set together"):
        DEFAULT_SPEC.with_(declared_family_id="x:y")
    with pytest.raises(ValueError, match="must be set together"):
        DEFAULT_SPEC.with_(declared_family_sha256="a" * 64)


def test_an_id_without_a_size_is_refused():
    with pytest.raises(ValueError, match="carries no bill"):
        GateSpec(spec_id="t", authored_utc="2026-07-30T00:00:00+00:00",
                 declared_family_id="x:y", declared_family_sha256="a" * 64,
                 declared_family_size=None)


def test_the_two_new_fields_are_invisible_to_the_seal_when_unset():
    c = DEFAULT_SPEC.canonical()
    assert "declared_family_id" not in c
    assert "declared_family_sha256" not in c
    # ...and visible when set, which is the whole point
    s = DEFAULT_SPEC.with_(declared_family_size=9, declared_family_id="x:y",
                           declared_family_sha256="a" * 64)
    assert "declared_family_id" in s.canonical()


def test_default_spec_seals_to_the_pre_AG_value_and_that_is_a_repair():
    """AG's `spread_band` field addition (048facafc) moved EVERY seal in the estate, and
    nothing recorded it: `AA_ESTATE_WALK.json` publishes `spec_sha256 d3df4c43...` and
    rebuilding that spec at HEAD gave `8bd15ced...`.

    `spec._ABSENT_MEANS_UNCHANGED` drops a capability field when it is None, which restores
    every pre-AG seal. The literal below is that seal under the v1 spread composition — the
    behaviour every pre-wave-8 run actually had. AMENDED at the wave-8 train merge: Session AH
    changed `DEFAULT_COMPOSITION` to `v2_damped`, so a default spec now BEHAVES differently and
    must seal differently; the pre-AG literal belongs to the spec that behaves as the old runs
    behaved (`spread_composition="v1_multiplicative"`, dropped from the canonical dict because
    v1 IS the pre-field behaviour — see `canonical()`'s comment). If the v1 seal moves again,
    some new field is missing from the tuple and the published `spec_sha256` values have gone
    stale a second time."""
    v1 = LEGACY_DEFAULT_SPEC.with_(spread_composition="v1_multiplicative")
    assert v1.seal() == (
        "4910f6ac46025bd676cd96860a57b699c17c60a4d4ecd5361bf228125693668e")
    # And the default seals DIFFERENTLY, because it behaves differently (AH's composition
    # repair is the default) — a hash collision here would be the exact defect seals prevent.
    assert DEFAULT_SPEC.seal() != v1.seal()


def test_a_real_methodology_difference_still_moves_the_seal():
    """The drop-when-None rule must not become a hole. Every field in
    `_ABSENT_MEANS_UNCHANGED` still changes the seal when it carries a value."""
    from src.research_infra.walkforward.spec import _ABSENT_MEANS_UNCHANGED

    base = DEFAULT_SPEC.seal()
    assert DEFAULT_SPEC.with_(spread_band="mid").seal() != base
    assert DEFAULT_SPEC.with_(spread_band="high").seal() != \
        DEFAULT_SPEC.with_(spread_band="mid").seal()
    capture = DEFAULT_SPEC.with_(
        capture_windows=(("2026-01-01", "2026-01-30"),),
        capture_declaration_id="TEST_CAPTURE_PLAN_V1",
        capture_declaration_sha256s=("1" * 64,),
    )
    assert capture.seal() != base
    assert capture.with_(capture_declaration_id="TEST_CAPTURE_PLAN_V2").seal() != (
        capture.seal()
    )
    assert capture.with_(capture_declaration_sha256s=("2" * 64,)).seal() != (
        capture.seal()
    )
    assert set(_ABSENT_MEANS_UNCHANGED) == {
        "spread_band",
        "declared_family_id",
        "declared_family_sha256",
        "capture_windows",
        "capture_declaration_id",
        "capture_declaration_sha256s",
    }, (
        "a field added to _ABSENT_MEANS_UNCHANGED needs the argument in its comment: None must "
        "mean 'the behaviour that existed before this field', and no set value may mean what "
        "None means")


def test_AA_published_spec_seals_reproduce_again():
    """The estate-facing half of the repair, asserted against the committed artifact rather
    than against a literal."""
    import importlib.util
    import pathlib
    import sys

    repo = pathlib.Path(__file__).resolve().parents[2]
    aa_dir = repo / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
    walk = aa_dir / "AA_ESTATE_WALK.json"
    if not walk.is_file() or not (aa_dir / "aa_estate_walk.py").is_file():
        pytest.skip("AA's walk artifact or driver is not in this working tree "
                    "(sparse-checkout); the literal-seal test above still covers the repair")
    spec = importlib.util.spec_from_file_location("aa_estate_walk_probe",
                                                 aa_dir / "aa_estate_walk.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["aa_estate_walk_probe"] = mod
    spec.loader.exec_module(mod)
    pub = json.loads(walk.read_text())["runs"]
    al = mod.allowlist()
    for run, option in (("B_balanced|v1_1", "B_balanced"),
                        ("A_strict|v1_1", "A_strict"),
                        ("C_exploratory|v1_1", "C_exploratory")):
        p = pub[run]
        s = mod.OPTIONS[option].with_(spec_id=p["spec_id"], sleeve_symbol_allowlist=al,
                                     declared_family_size=69, schema=LEGACY_SCHEMA,
                                     fidelity_reference_policy=(
                                         FidelityReferencePolicy.LEGACY_ANY_REFERENCE.value
                                     ),
                                     fidelity_precision_floor=None,
                                     # AA ran before the composition field existed, i.e. at v1 —
                                     # the canonical form drops exactly that value (wave-8 merge).
                                     spread_composition="v1_multiplicative")
        assert s.seal() == p["spec_sha256"], (
            f"{run}: AA's published seal does not reproduce. Either a GateSpec field was added "
            f"without a seal-lineage rule (see canonical()), or the sleeve registry moved.")


# ---------------------------------------------------------------------------------
# the sensitivity helpers
# ---------------------------------------------------------------------------------
def test_max_size_that_admits_is_the_closed_form():
    assert CF.max_size_that_admits(0.0064, 0.20) == 31
    assert CF.max_size_that_admits(0.0064, 0.05) == 7
    assert CF.max_size_that_admits(0.011998800119988001, 0.20) == 16
    with pytest.raises(CF.CandidateFamilyError):
        CF.max_size_that_admits(0.0, 0.10)


def test_sensitivity_agrees_with_the_closed_form_at_the_boundary():
    rows = CF.sensitivity(0.0064, [31, 32], alphas=(0.20,), methods=("bonferroni",))
    by_m = {r["family_size"]: r["admits"] for r in rows}
    assert by_m[31] is True
    assert by_m[32] is False, "0.20/32 = 0.00625 < 0.0064 — it misses by one member"
    with pytest.raises(CF.CandidateFamilyError):
        CF.sensitivity(0.01, [0])


def test_the_committed_declaration_loads_and_carries_the_measured_sizes():
    """V1, the wave-8 artifact of record. These numbers are what the wave-8 documents quote.

    Reads `DECLARATION_V1` **by name**, not `DEFAULT_DECLARATION` — corrected by Session AP
    (B1350-B1399). It used to read the default, which pinned V1's composition through a
    mutable pointer: the moment the default moved to AL's ratcheted V2 (35/32), a test whose
    subject is V1 started failing for a reason that had nothing to do with V1. The successor's
    own sizes are pinned in `test_candidate_family_v2_ratchet.py` and the succession itself in
    `test_candidate_family_chain.py`."""
    if not CF.DECLARATION_V1.is_file():
        pytest.skip("CANDIDATE_FAMILY_V1.json not in this working tree")
    fam = CF.load_candidate_family(CF.DECLARATION_V1)
    assert set(fam.families) == {"CANDIDATE_BOOK_V1", "MECHANISM_CROSS_V1", "ESTATE_UNION_V1"}
    assert fam.effective_size("CANDIDATE_BOOK_V1") == 32
    assert fam.effective_size("CANDIDATE_BOOK_V1", CF.LOOKS_TAKEN) == 29
    assert fam.effective_size("MECHANISM_CROSS_V1") == 276
    assert fam.effective_size("ESTATE_UNION_V1") == 298
    # Ratified 2026-07-30 by Borhen ("yes please proceed as proposed and recommended"), recorded
    # by the orchestrator at the wave-8 review. The original assertion here was
    # `is_ratified() is False` with the message "a session cannot ratify its own family" — that
    # guard did its job (the declaring session left it null) and the ratification carries owner
    # provenance, which is what this now pins. The RULE is part of the record: any change to it
    # is a new owner decision, not an edit.
    assert fam.is_ratified() is True
    assert "Borhen" in (fam.ratified_by or "")
    raw = json.loads(CF.DECLARATION_V1.read_text(encoding="utf-8"))
    rule = raw.get("ratified_rule") or {}
    assert (rule.get("family"), rule.get("basis"), rule.get("alpha"), rule.get("option")) == (
        "CANDIDATE_BOOK_V1", "all_declared", 0.10, "B_balanced")
    nogen = {m.name for m in fam.family("CANDIDATE_BOOK_V1").no_look_members()}
    assert nogen == {"mx_eu50_cash_d1_volume_surge_reversal",
                     "mx_fra40_cash_d1_volume_surge_reversal",
                     "vp_euidx_pocgrav"}


def test_the_declared_candidate_book_is_what_active_specs_resolves():
    """The prospective claim rests entirely on this: the declared family is not a judgement
    call, it is what the live config's own resolvers build. If they ever diverge, the family is
    a curated list again and the whole mechanism is worth nothing.

    Deliberately `active_specs` and NOT `effective_registry`: a config flag must not be able to
    move a multiplicity bill, and `active_specs` takes no `include_clean3`, which is exactly why
    it is the right basis. The name matters — an earlier version of this test was called
    `..._is_the_live_registry`, which a future session would have read as proof that the declared
    family IS the live generating set. It is not: `effective_registry` is **29** in this repo, a
    DIFFERENT 29 from `looks_taken`, and it excludes `sub_xvol_pullback`. See the result doc
    §2.3b.

    V1 by name, and the successor is checked separately below: V2 deliberately holds
    `active_specs`' tags PLUS AL's three declared threshold cells, which are hypotheses rather
    than registry entries and therefore have no spec to resolve. Equality is V1's property;
    superset-with-a-named-remainder is V2's."""
    if not CF.DECLARATION_V1.is_file():
        pytest.skip("CANDIDATE_FAMILY_V1.json not in this working tree")
    import yaml

    from src.components.ultimate_book import admission as P
    from src.components.ultimate_book.sleeves.registry import active_specs

    cfg_path = CF.REPO / "config/agent_config.yaml"
    if not cfg_path.is_file():
        pytest.skip("agent_config.yaml absent")
    cfg = yaml.safe_load(cfg_path.read_text())["gtos_vnext_runtime"]
    mx, err = P.resolve_market_expansion_sleeves(
        policy=cfg["ultimate_book_market_expansion_policy"],
        explicit_sleeves=tuple(cfg["ultimate_book_market_expansion_sleeves"] or ()))
    assert err is None
    specs = active_specs(
        None, include_candidate_book=bool(cfg["ultimate_book_include_candidate_book"]),
        candidate_book_sleeves=cfg["ultimate_book_candidate_book_sleeves"],
        include_market_expansion_book=bool(cfg["ultimate_book_include_market_expansion_book"]),
        market_expansion_sleeves=mx)
    fam = CF.load_candidate_family(CF.DECLARATION_V1)
    declared = {m.name for m in fam.family("CANDIDATE_BOOK_V1").members}
    assert declared == {s.tag for s in specs}

    # And the successor: still not a curated list, but the remainder must be NAMED rather
    # than merely tolerated. Every V2 member that `active_specs` cannot resolve has to be a
    # declared amendment carrying its own `why`, or the prospective claim has quietly become
    # "whatever a session added".
    if not CF.DECLARATION_V2.is_file():
        return
    v2 = CF.load_candidate_family(CF.DECLARATION_V2)
    v2_names = {m.name for m in v2.family("CANDIDATE_BOOK_V1").members}
    assert declared <= v2_names, "V2 dropped a member `active_specs` still builds"
    remainder = v2_names - declared
    raw2 = json.loads(CF.DECLARATION_V2.read_text(encoding="utf-8"))
    amended = {n for h in raw2["families"]["CANDIDATE_BOOK_V1"].get("history", [])
               for n in h.get("members_added", []) if h.get("why")}
    assert remainder == amended, (
        f"V2 members that active_specs cannot resolve and no amendment declares: "
        f"{sorted(remainder - amended)}")


# ---------------------------------------------------------------------------------
# The seal migration, pinned in BOTH directions
# ---------------------------------------------------------------------------------
#: Published seals whose producing lineage PREDATED `GateSpec.spread_band` (AG, 048facafc).
#: The `_ABSENT_MEANS_UNCHANGED` repair restores these, and they must keep reproducing.
_RESTORED_BY_THE_REPAIR = {
    "AA_ESTATE_WALK.json": 7,
    "X_ESTATE_WALK.json": 3,
    "X_STATE_D_SENSITIVITY.json": 3,
    "W_MX_PILOT.json": 3,
    "W_NEGATIVE_CONTROLS.json": 2,
}

#: Published seals computed with `spread_band` ALREADY PRESENT and set to None, so their hash
#: includes `"spread_band":null`. The repair makes these unreproducible — deliberately, and
#: net-positive against the 18 above, but it must never be silent. That is the entire
#: complaint this session made against AG's change, so it cannot be exempt from it.
_BROKEN_BY_THE_REPAIR = {
    "AG_MX_PILOT_BANDED.json": ["bea6f04c", "fa055aa4", "e2c9d11a"],
    "EXIT_FRONTIER_V1.json": ["b8cc079b"],
    "EXIT_FRONTIER_V1_TRAIL.json": ["b8cc079b"],
    "FAMILY_ADMISSION_V1.json": ["f9e697f8", "adda9729", "bbdba441",
                                 "a12e7a35", "b21a076c", "e8774886"],
}


def _seals_in(path) -> set[str]:
    out: set[str] = set()

    def walk(o):
        if isinstance(o, dict):
            v = o.get("spec_sha256")
            if isinstance(v, str) and len(v) == 64:
                out.add(v)
            for x in o.values():
                walk(x)
        elif isinstance(o, list):
            for x in o[:400]:
                walk(x)

    walk(json.loads(path.read_text()))
    return out


def test_the_seal_migration_is_documented_in_both_directions():
    """The repair restores 18 published seals and breaks 10, and both cohorts are named here.

    This test does not re-derive the seals — the drivers for X, W and AG are not all importable
    and re-running the estate is not a unit test's job. What it pins is that the two cohorts are
    still the artifacts this session measured, so a later session that changes
    `_ABSENT_MEANS_UNCHANGED` has to come here and re-measure rather than discovering the
    breakage the way this session discovered AG's: by a control failing weeks later.
    """
    import pathlib

    from src.research_infra.walkforward.spec import _ABSENT_MEANS_UNCHANGED

    aud = pathlib.Path(__file__).resolve().parents[2] / (
        "docs/audits/fable5-vision-audit-20260725")
    if not aud.is_dir():
        pytest.skip("the audit tree is not in this working tree")

    assert set(_ABSENT_MEANS_UNCHANGED) == {
        "spread_band",
        "declared_family_id",
        "declared_family_sha256",
        "capture_windows",
        "capture_declaration_id",
        "capture_declaration_sha256s",
    }, (
        "the field set changed — re-measure BOTH cohorts below before editing this test. "
        "The restored set is every published seal whose lineage predates the newly-dropped "
        "field; the broken set is every one that ran with it present and None.")

    n_restored = 0
    for fn, n in sorted(_RESTORED_BY_THE_REPAIR.items()):
        hits = list(aud.glob(f"phase*/receipts/{fn}"))
        if not hits:
            continue
        seals = _seals_in(hits[0])
        assert len(seals) >= n, f"{fn}: expected >= {n} published seals, found {len(seals)}"
        n_restored += n

    n_broken = 0
    for fn, prefixes in sorted(_BROKEN_BY_THE_REPAIR.items()):
        hits = list(aud.glob(f"phase*/receipts/{fn}"))
        if not hits:
            continue
        seals = _seals_in(hits[0])
        for pre in prefixes:
            assert any(s.startswith(pre) for s in seals), (
                f"{fn}: the seal {pre}… this session recorded as broken by the repair is no "
                f"longer published there. Either the artifact was regenerated (in which case "
                f"remove the entry) or the record is wrong.")
            n_broken += 1

    # The trade this session accepted, stated as an assertion so it cannot drift into folklore.
    assert n_restored >= 18 and n_broken >= 10
    assert n_restored > n_broken, (
        "the repair must remain net-positive; if a future field set inverts that, revert it "
        "rather than publishing a migration that breaks more than it fixes")
