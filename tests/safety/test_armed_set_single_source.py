"""The armed set has ONE source of truth, and it is enforced here.

Wave 20 found three artifacts that each wrote the armed set down as a four-tuple and
all three were wrong the same way -- omitting ``sub_mid_dn_revert`` (armed on both
accounts) and including ``mx_btcusd_d1_donchian_20_breakout`` (disarmed by the owner
on 2026-08-05). Nothing could have caught it because there was nowhere to look it up.

These tests are behavioural: they parse the launcher's actual argument list, read the
declaration, and reconcile. :func:`test_the_pre_repair_launcher_is_rejected` runs the
whole invariant against the **exact bytes of the pre-repair FTMO row** and asserts it
FAILS -- that is what makes the repair provable rather than merely different.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.safety.armed_set import (
    LAUNCHER_PATH,
    MANIFEST_PATH,
    SURFACE_EXPERIMENT,
    SURFACE_PRODUCTION,
    AccountArming,
    armed_sleeves,
    assert_consistent,
    declared_arming,
    experiment_arming,
    launcher_arming,
    manifest,
    parse_launcher,
    production_arming,
    reconcile,
)

REPO = Path(__file__).resolve().parents[2]

#: The FTMO row exactly as it stood in the committed launcher from 2026-07-31 until the
#: 2026-08-07 repair (blob 357d01a26601, identical on all 40 local branches including
#: main). Kept verbatim as a regression fixture: the invariant below MUST reject it.
PRE_REPAIR_FTMO_ROW = (
    '$books = @(\n'
    '  @{ ns="operator_profile"; profile="operator_profile"; '
    'term="C:\\MT5\\FTMO\\terminal64.exe"; kill="pipeline_state/ULTIMATE_BOOK_KILL_ftmo.flag"; '
    'log="shadow_logs\\run_book_console.log"; '
    'tags="crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout"; '
    'frontier="mx_btcusd_d1_donchian_20_breakout"; '
    'spreadFloor="sub_mid_dn_revert,sub_xvol_pullback"; '
    'laneWeights="C:\\ProgramData\\GTOS\\lane-weights\\operator_profile.json"; '
    'laneWeightsKey="C:\\ProgramData\\GTOS\\lane-weights\\lane_weights.key" },\n'
    '  @{ ns="redacted_account_live_bee34003"; profile="redacted_account"; '
    'term="C:\\MT5\\redacted_account\\terminal64.exe"; kill="pipeline_state/ULTIMATE_BOOK_KILL_fn.flag"; '
    'log="shadow_logs\\run_book_fn_console.log"; '
    'tags="crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert"; frontier=$null; '
    'spreadFloor="sub_mid_dn_revert,sub_xvol_pullback"; '
    'laneWeights="C:\\ProgramData\\GTOS\\lane-weights\\redacted_account_live_bee34003.json"; '
    'laneWeightsKey="C:\\ProgramData\\GTOS\\lane-weights\\lane_weights.key" }\n'
    ')\n'
)

#: Sleeves the owner has explicitly turned off. Naming them is the point: a
#: "did the set change" test passes happily if a disarmed sleeve comes back with a
#: matching declaration edit, and that is exactly the mistake worth blocking.
DISARMED_BY_OWNER = {
    "mx_btcusd_d1_donchian_20_breakout": "2026-08-05, D-2 CLOSED, host 2fa77722d",
    "metals_core": "2026-07-29 14:25, pulled the same day it was armed",
    "fx_jpy": "2026-07-30 ~14:57Z, pulled on AV's evidence",
    "metals_softband": "never armed; killed on FTMO",
}


# ---------------------------------------------------------------------------
# The invariant
# ---------------------------------------------------------------------------
def test_launcher_and_declaration_agree() -> None:
    problems = reconcile()
    assert problems == [], "\n".join(str(p) for p in problems)


def test_assert_consistent_is_callable_from_a_research_entrypoint() -> None:
    assert_consistent()


def test_no_owner_disarmed_sleeve_is_armed_by_the_committed_launcher() -> None:
    """The 2026-08-05 defect, stated directly. This is the test that would have
    caught it: the owner disarmed a sleeve on the host and the committed launcher
    kept arming it for two days."""

    launcher = launcher_arming()
    for account, row in launcher.items():
        assert not row.is_fail_open, f"{account} passes no --tags: every BUILT sleeve is armed"

    # The disarm was a decision about the PRODUCTION book at the production dial. Scoped to
    # production surfaces the guard is exactly as strong as it was -- and there must be at
    # least one, or a future refactor could make this vacuous by relabelling every row.
    production = production_arming(launcher)
    assert production, "no production surface: this guard would be vacuous"
    for account, row in production.items():
        offenders = row.armed & set(DISARMED_BY_OWNER)
        assert not offenders, (
            f"{account} arms owner-disarmed sleeve(s) {sorted(offenders)} "
            f"({'; '.join(DISARMED_BY_OWNER[s] for s in sorted(offenders))})"
        )
        stray = set(row.frontier_exits) & set(DISARMED_BY_OWNER)
        assert not stray, f"{account} passes --frontier-exits for disarmed {sorted(stray)}"


def test_an_experiment_surface_may_run_a_disarmed_sleeve_only_at_minimal_size() -> None:
    """The F5 minimal-size surface deliberately runs the FULL 32-sleeve registry, which
    includes `mx_btcusd_d1_donchian_20_breakout` -- the sleeve the owner disarmed on the
    production book on 2026-08-05.

    That is not a contradiction and it is not an exemption either: the disarm was a decision
    about the production dial, and the owner's F5 approval was explicitly "all 32 sleeves, not
    the armed 4". What this test pins is the PRICE of that: it may only happen on a surface
    that (a) is declared `experiment`, (b) carries a fixed minimal dollar size, and (c) is a
    different namespace from the production book. Remove any one of those and the disarmed
    sleeve is back on real money at the dial."""

    experiments = experiment_arming(launcher_arming())
    if not experiments:
        pytest.skip("no experiment surface is configured")
    production_namespaces = set(production_arming(launcher_arming()))
    for account, row in experiments.items():
        assert row.surface == SURFACE_EXPERIMENT
        assert row.minimal_size_usd, f"{account} is an experiment surface with no size"
        assert 0 < float(row.minimal_size_usd) <= 500.0
        assert account not in production_namespaces
        assert row.frontier_exits == (), "an experiment surface measures the RAW system"
    # and the production book is the THREE-sleeve book (sub_mid_dn_revert disarmed on
    # both accounts 2026-08-11, host 47d0960e6, swarm/SLEEVE_PULL_SUB_MID_DN_REVERT_V1.md
    # — this pin was written before the pull and rotted; corrected 2026-08-25)
    assert armed_sleeves() == frozenset(
        {"crypto", "energy_agri", "sub_xvol_pullback"})


def test_a_production_row_that_gains_a_minimal_size_flag_is_a_build_failure() -> None:
    """The dangerous direction, modelled. A production row that quietly acquired
    `--f5-minimal-size-usd` would place 1/200th lots while every published figure, every
    survivor screen and every learning-lane recommendation still priced it at the dial --
    silently, with a healthy log. `parse_launcher` derives the surface from the MECHANISM, so
    this is a `surface_mismatch` rather than a shrug."""

    text = ('$books = @(\n  @{ ns="x"; profile="p"; tags="crypto"; f5Size="10" }\n)\n')
    row = parse_launcher(text)["x"]
    assert row.surface == SURFACE_EXPERIMENT
    assert row.minimal_size_usd == "10"

    problems = reconcile(
        launcher={"x": row},
        declared={"x": AccountArming("x", "p", ("crypto",), surface=SURFACE_PRODUCTION)},
    )
    assert "surface_mismatch" in {p.kind for p in problems}, problems


def test_the_pre_repair_launcher_is_rejected() -> None:
    """Run the invariant against the exact pre-repair bytes. It MUST fail -- both
    because the FTMO row arms a disarmed sleeve and because its --frontier-exits
    names one. A test that cannot fail against the old behaviour proves nothing."""

    old = parse_launcher(PRE_REPAIR_FTMO_ROW)
    ftmo = old["operator_profile"]

    # The old row's own content, restated so the fixture cannot rot silently.
    assert "mx_btcusd_d1_donchian_20_breakout" in ftmo.armed
    assert ftmo.frontier_exits == ("mx_btcusd_d1_donchian_20_breakout",)

    problems = reconcile(launcher=old)
    kinds = {p.kind for p in problems}
    assert "armed_set_mismatch" in kinds, problems
    assert "frontier_exits_mismatch" in kinds, problems

    offenders = ftmo.armed & set(DISARMED_BY_OWNER)
    assert offenders == {"mx_btcusd_d1_donchian_20_breakout"}

    # And redacted_account was right AT THE TIME of the repair. The fixture predates the
    # 2026-08-11 sub_mid_dn_revert pull, so the fixture set is the current source
    # plus exactly that receipted sleeve (corrected 2026-08-25).
    assert old["redacted_account_live_bee34003"].armed == (
        armed_sleeves("redacted_account_live_bee34003") | {"sub_mid_dn_revert"})


def test_the_repair_changed_only_the_ftmo_row() -> None:
    """ROOT-CAUSE REWRITE 2026-08-25: the original pinned the FN row byte-stable against
    the wave-20 fixture, which rotted the moment a LATER receipted decision moved the row
    (sub_mid_dn_revert disarmed on BOTH accounts 2026-08-11, host 47d0960e6,
    swarm/SLEEVE_PULL_SUB_MID_DN_REVERT_V1.md). The durable invariants: the wave-20 repair
    itself did not touch FN (fixture self-checks above), the CURRENT FN row agrees with the
    single source, and the only old-vs-new delta is exactly the receipted pull."""

    old = parse_launcher(PRE_REPAIR_FTMO_ROW)["redacted_account_live_bee34003"]
    new = launcher_arming()["redacted_account_live_bee34003"]
    assert new.armed == armed_sleeves("redacted_account_live_bee34003")
    assert set(old.armed) - set(new.armed) == {"sub_mid_dn_revert"}, (
        "any FN delta beyond the receipted 2026-08-11 pull is undocumented drift")
    assert set(new.armed) - set(old.armed) == set()
    assert (old.profile, old.surface) == (new.profile, new.surface)


# ---------------------------------------------------------------------------
# The fail-open trap, modelled rather than commented
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("tags_literal", ['tags=""', "tags=$null"])
def test_empty_tags_is_unbounded_not_empty(tags_literal: str) -> None:
    """``run_book.py:383`` reads ``tuple(...) if args.tags else None``, so an empty
    ``--tags`` runs EVERY BUILT sleeve. Representing that as an empty set would let a
    caller conclude "nothing is armed" about the most dangerous configuration there
    is."""

    text = '$books = @(\n  @{ ns="x"; profile="p"; ' + tags_literal + ' }\n)\n'
    row = parse_launcher(text)["x"]
    assert row.is_fail_open
    assert row.tags is None
    assert row.armed == frozenset()  # empty, but is_fail_open says why

    problems = reconcile(
        launcher={"x": row},
        declared={"x": AccountArming("x", "p", ("crypto",))},
    )
    assert [p.kind for p in problems] == ["launcher_tags_fail_open"]


def test_a_frontier_exit_for_an_unarmed_sleeve_is_reported() -> None:
    text = ('$books = @(\n  @{ ns="x"; profile="p"; tags="crypto"; '
            'frontier="not_in_tags" }\n)\n')
    problems = reconcile(
        launcher=parse_launcher(text),
        declared={"x": AccountArming("x", "p", ("crypto",), frontier_exits=("not_in_tags",))},
    )
    assert "frontier_exit_for_unarmed_sleeve" in {p.kind for p in problems}


# ---------------------------------------------------------------------------
# The declaration is real, not decorative
# ---------------------------------------------------------------------------
def test_every_armed_sleeve_resolves_through_the_live_registry() -> None:
    """A declared name that the registry cannot resolve is a silent stand-down:
    ``registry.py:144`` drops unknown tags with no fallback and no error."""

    from src.components.ultimate_book.sleeves.registry import active_specs

    # Every worker the launcher starts, production and experiment alike: a name the registry
    # cannot resolve is a silent stand-down on any surface.
    #
    # The market-expansion book is resolved by POLICY, not by the include flag alone
    # (`book_engine._market_expansion_sleeves` -> `resolve_market_expansion_sleeves`), so a
    # bare `include_market_expansion_book=True` returns none of the twelve `mx_*` names. The
    # live config's own resolution is what the book uses, so it is what this must use.
    import yaml
    from src.components.ultimate_book.book_engine import (
        _candidate_book_sleeves, _market_expansion_sleeves,
    )

    rt = yaml.safe_load((REPO / "config/agent_config.yaml").read_text())
    rt = rt.get("gtos_vnext_runtime", rt)
    candidates = _candidate_book_sleeves(rt) or None
    expansion = _market_expansion_sleeves(rt) or None

    for account, row in declared_arming().items():
        names = sorted(row.armed)
        specs = active_specs(names, include_candidate_book=True,
                             candidate_book_sleeves=candidates,
                             include_market_expansion_book=True,
                             market_expansion_sleeves=expansion)
        assert {s.tag for s in specs} == set(names), (
            f"{account} declares names the live registry cannot resolve: "
            f"{sorted(set(names) - {s.tag for s in specs})}")


def test_the_declaration_carries_a_receipt_for_the_disarm() -> None:
    """Provenance is the half that makes this file authority rather than opinion."""

    doc = manifest()
    log = doc["decision_log"]
    assert log, "an armed-set declaration with no decision log is a guess"
    disarms = [r for r in log if "DISARM" in r["change"]]
    assert disarms, "the 2026-08-05 disarm must be on the record"
    for row in log:
        assert row.get("receipt"), f"decision {row['date']} {row['change']!r} has no receipt"
        assert row.get("authority"), f"decision {row['date']} has no authority"


def test_the_manifest_covers_exactly_the_launcher_accounts() -> None:
    assert set(declared_arming()) == set(launcher_arming())


def test_manifest_is_outside_the_token_digest_and_the_execution_seal() -> None:
    """Both claims are load-bearing for the owner: editing the armed-set declaration
    must not force an activation-token re-mint, and must not break the R2 seal.
    Verified against the implementations, not against the manifest's own prose."""

    import inspect

    from src.safety import activation_token

    src = inspect.getsource(activation_token.config_digest_for)
    # The digest is over the base config plus the active profile file only.
    assert "profile_path_for" in src and "config_path" in src
    assert "live_armed_set" not in src

    contract = json.loads((REPO / "research/operations"
                           / "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16"
                           / "B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json"
                           ).read_text())
    bound = {r["path"] if isinstance(r, dict) else r
             for group, rows in contract["input_bindings"].items()
             if isinstance(rows, list) for r in rows}
    assert str(MANIFEST_PATH.relative_to(REPO)) not in bound
    assert str(LAUNCHER_PATH.relative_to(REPO)) not in bound


# ---------------------------------------------------------------------------
# Consumers must not write the set down again
# ---------------------------------------------------------------------------
def test_the_wave20_artifacts_agree_with_the_single_source() -> None:
    """The three artifacts that were wrong. They are research artifacts, not runtime,
    so this checks their published sets rather than importing them."""

    expected = armed_sleeves()
    phase20 = REPO / "docs/audits/fable5-vision-audit-20260725/phase20"

    r2 = json.loads((phase20 / "receipts/r2/R2_RESULT_V1.json").read_text())
    assert set(r2["live_isolation"]["armed_sleeves"]) == expected, r2["live_isolation"]

    rewalk = (phase20 / "receipts/r1/r1_estate_rewalk.py").read_text()
    ns: dict = {}
    exec(compile(rewalk[rewalk.index("ARMED = ("):rewalk.index("FORMERLY_ARMED")],
                 "<r1_armed>", "exec"), ns)
    assert set(ns["ARMED"]) == expected


# ---------------------------------------------------------------------------
# Consumers derive; they do not remember
# ---------------------------------------------------------------------------
def test_the_learning_lane_rerate_script_derives_its_armed_set() -> None:
    """`scripts/rerate_book_from_live.py` is the learning lane's live re-rate -- the thing
    that produces per-sleeve up/down-weight recommendations an owner sizing decision would
    read. It hard-coded a three-tuple ('the intersection of the two accounts') that omitted
    an armed sleeve, in a file whose own comment four lines above said not to do that.

    It is loaded by path rather than imported as a module because it is a script, and its
    ARMED must equal the single source of truth at import time, not merely look similar.
    """

    import importlib.util

    path = REPO / "scripts/rerate_book_from_live.py"
    spec = importlib.util.spec_from_file_location("_p4_rerate", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert set(mod.ARMED) == armed_sleeves()
    assert mod.armed_sets() == {ns: tuple(sorted(row.armed))
                                for ns, row in production_arming().items()}
    # SURVIVOR and ARMED are different sets and the script used to conflate them; both must
    # still be reachable, under names that say which is which.
    assert hasattr(mod, "survivor_sets"), "the survivor screen must keep its own name"
    # Every armed sleeve needs a horizon or time_to_first_action silently skips it.
    missing = [s for s in mod.ARMED if s not in mod.HORIZON_H]
    assert missing == [], f"armed sleeves with no structural horizon: {missing}"
