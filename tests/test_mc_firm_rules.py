"""Controls for `scripts/mc_firm_rules.py`.

The load-bearing test is `test_legacy_rules_are_bit_identical_to_the_sealed_engine`. Every
number in `MC_FIRM_TRUE_V1.json` is a difference between two runs of this engine, so the
claim "the difference is caused by the rule change" is only true if the engine reduces
EXACTLY to the sealed one when handed the sealed rule set. Not approximately. Exactly.

The rest assert the direction of each rule change from first principles, so a future edit
that silently flips a comparison is caught by something other than the headline number.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
# `scripts/research/` is a REGULAR package (it has an __init__.py) and a regular package
# beats a namespace portion at ANY sys.path position -- so the moment `scripts/` is
# searchable, `import research` resolves there and `research.operations.*` stops resolving
# for the whole process. Python puts the script's own directory on sys.path automatically,
# so appending is not enough either. Pin the repo-root package first, with sys.path
# temporarily restricted to the repo root, and everything after it is harmless.
# Session V's full-suite A/B measured the alternative as 6 unexplained regressions in
# tests/test_audit_b6_* and tests/test_b7_5_*.
_sys_path = sys.path[:]
try:
    sys.path[:] = [str(REPO)]
    import research.operations  # noqa: E402,F401
finally:
    sys.path[:] = _sys_path
sys.path.insert(0, str(REPO / "scripts"))
ROUTE = REPO / ("research/operations/"
                "final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")

import mc_firm_rules as F  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (ROUTE / "INTEG_portfolio_build_w2.py").is_file(),
    reason="route module is sparse-checkout-hidden in this worktree")


def _synthetic(n=400, seed=7):
    """A daily unit-R series with the shape of the real ones: fat left tail, positive
    drift, most days zero. Deliberately NOT the real book -- these tests are about the
    engine, and must run without the 4 s cache build."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        if rng.random() < 0.45:
            out.append(0.0)
        elif rng.random() < 0.40:
            out.append(-abs(rng.gauss(0.9, 0.6)))
        else:
            out.append(abs(rng.gauss(1.1, 1.4)))
    return out


SERIES = _synthetic()
RISKS = (0.008, 0.0096, 0.0155)


@pytest.fixture(scope="module")
def w2():
    return F.M._route_mc()


# ---------------------------------------------------------------------------------
# 1. The control the whole artifact rests on
# ---------------------------------------------------------------------------------
@pytest.mark.parametrize("risk", RISKS)
def test_legacy_rules_are_bit_identical_to_the_sealed_engine(w2, risk):
    mine = F.mc(SERIES, risk, F.Rules.LEGACY, n_paths=4000, seed_base=1)
    theirs = w2.mc_series(SERIES, risk, n_paths=4000, seed_base=1)
    for k in ("p_pass", "p_fail_dd", "p_fail_daily", "p_timeout", "med_days_pass"):
        assert mine[k] == theirs[k], k


def test_bit_identity_holds_across_seed_bases(w2):
    for sb in (0, 1, 99, 777):
        mine = F.mc(SERIES, 0.0096, F.Rules.LEGACY, n_paths=2000, seed_base=sb)
        theirs = w2.mc_series(SERIES, 0.0096, n_paths=2000, seed_base=sb)
        assert mine["p_pass"] == theirs["p_pass"]
        assert mine["med_days_pass"] == theirs["med_days_pass"]


def test_the_sealed_constants_are_still_the_sealed_constants():
    """If someone edits INTEG_portfolio_build.py:298 in place, this file's whole premise
    changes and the published 8% result stops being reproducible. Guard it."""
    sys.path.insert(0, str(ROUTE))
    import INTEG_portfolio_build as I
    assert (I.TARGET, I.MAXDD, I.DAILY, I.BLOCK, I.PATHCAP) == (0.08, 0.10, 0.05, 5, 2000)
    assert F.Rules.LEGACY.targets == (I.TARGET,)
    assert F.Rules.LEGACY.daily_limit == I.DAILY
    assert F.Rules.LEGACY.maxdd_limit == I.MAXDD


# ---------------------------------------------------------------------------------
# 2. Each rule axis moves p_pass in the direction the firm rule implies
# ---------------------------------------------------------------------------------
def test_a_harder_target_never_raises_p_pass():
    easy = F.mc(SERIES, 0.0096, F.Rules(label="t8", targets=(0.08,)), 4000, 1)
    hard = F.mc(SERIES, 0.0096, F.Rules(label="t10", targets=(0.10,)), 4000, 1)
    assert hard["p_pass"] <= easy["p_pass"]
    assert hard["med_days_pass"] >= easy["med_days_pass"]


def test_static_drawdown_is_weakly_easier_than_trailing_drawdown():
    """(peak-eq)/peak >= L fires whenever (1-eq) >= L does and peak >= 1, never the
    reverse. So swapping the sealed trailing rule for FTMO's measured static floor can
    only raise p_pass. This is the axis the commission did not name, and it runs the
    OPPOSITE way to the target."""
    trail = F.mc(SERIES, 0.0155, F.Rules(label="trail"), 4000, 1)
    static = F.mc(SERIES, 0.0155, F.Rules(label="static", maxdd_basis=F.DD_FIRM), 4000, 1)
    assert static["p_pass"] >= trail["p_pass"]
    assert static["p_fail_dd"] <= trail["p_fail_dd"]


def test_fixed_cash_daily_limit_is_weakly_harder_than_pct_of_equity():
    """Both firms cap the daily loss at a fixed 5% of the INITIAL balance. The sealed
    engine caps it at 5% of the day's opening equity, which is more room whenever the
    account is in profit -- and a challenge path spends most of its life in profit."""
    for risk in (0.0155, 0.03):
        pct = F.mc(SERIES, risk, F.Rules(label="pct"), 4000, 1)
        cash = F.mc(SERIES, risk, F.Rules(label="cash", daily_basis=F.DAILY_FIRM), 4000, 1)
        assert cash["p_fail_daily"] >= pct["p_fail_daily"], risk


def test_redacted_account_worked_example_breaches_under_firm_basis_and_not_under_legacy():
    """FIRM_RULES_V1.json quotes redacted_account verbatim: start the day at $110,000, lose
    $5,000, and the limit is breached even though equity is $105,000. One day, one draw."""
    # eq must be 1.10 at the start of the losing day, so lead with a +10% day.
    dp_up = 0.10
    dp_down = -5000.0 / 110000.0          # -4.5455% of a $110k day-start equity
    series = [dp_up, dp_down]
    r = F.Rules(label="one", targets=(9.99,), daily_basis=F.DAILY_FIRM, maxdd_limit=9.99,
                block=2, pathcap=1)
    legacy = F.mc(series, 1.0, F.Rules(label="one_legacy", targets=(9.99,),
                                       maxdd_limit=9.99, block=2, pathcap=1), 1, 0)
    firm = F.mc(series, 1.0, r, 1, 0)
    assert abs(1.10 * dp_down) == pytest.approx(0.05, rel=1e-12)
    assert firm["p_fail_daily"] == 1.0, "the firm's own example must breach"
    assert legacy["p_fail_daily"] == 0.0, "the sealed engine permits it ($5,500 of room)"


def test_static_floor_fires_at_the_firms_cash_floor_and_not_above_it():
    """FTMO states the overall rule as a cash floor -- $90,000 on a $100,000 account --
    so the engine tests `eq <= 0.90` rather than `(1.0 - eq) >= 0.10`. The two differ at
    the boundary, because 1.0 - 0.9 evaluates to 0.09999999999999998."""
    r = F.Rules(label="dd", targets=(9.99,), maxdd_basis=F.DD_FIRM, daily_limit=9.99,
                block=1, pathcap=1)
    assert (1.0 - 0.9) < 0.10, "the wart this formulation avoids"
    assert F.mc([-0.10], 1.0, r, 1, 0)["p_fail_dd"] == 1.0, "exactly at the floor"
    assert F.mc([-0.1001], 1.0, r, 1, 0)["p_fail_dd"] == 1.0, "through the floor"
    assert F.mc([-0.0999], 1.0, r, 1, 0)["p_fail_dd"] == 0.0, "above the floor"


# ---------------------------------------------------------------------------------
# 3. Phases and minimum trading days
# ---------------------------------------------------------------------------------
def test_two_phases_are_never_easier_than_one_and_reset_the_equity():
    one = F.mc(SERIES, 0.0096, F.Rules(label="p1", targets=(0.10,)), 4000, 1)
    two = F.mc(SERIES, 0.0096, F.Rules(label="p2", targets=(0.10, 0.05)), 4000, 1)
    assert two["p_pass"] <= one["p_pass"]
    assert two["med_days_pass"] > one["med_days_pass"]
    # Phase 2 must start from a fresh account, not from +10%: if equity carried over, a
    # 5% second target would be already satisfied and p_pass would be identical.
    assert two["p_pass"] < one["p_pass"]


def test_single_phase_tuple_reduces_to_the_scalar_case(w2):
    a = F.mc(SERIES, 0.0096, F.Rules(label="x", targets=(0.08,)), 2000, 1)
    b = w2.mc_series(SERIES, 0.0096, n_paths=2000, seed_base=1)
    assert a["p_pass"] == b["p_pass"]


def test_latched_minimum_trading_days_cannot_lower_p_pass():
    """Reaching the target on day 2 of a 4-day minimum does not fail the challenge; the
    operator stops risking and waits. Modelling it as 'keep trading at full size' is a
    bound, not the expectation, so both are published and only the bound may fall."""
    base = F.mc(SERIES, 0.0155, F.Rules(label="b", targets=(0.10,)), 4000, 1)
    latch = F.mc(SERIES, 0.0155, F.Rules(label="l", targets=(0.10,), min_trading_days=4,
                                         min_days_model="latch"), 4000, 1)
    at_risk = F.mc(SERIES, 0.0155, F.Rules(label="r", targets=(0.10,), min_trading_days=4,
                                           min_days_model="at_risk"), 4000, 1)
    assert latch["p_pass"] == base["p_pass"]
    assert at_risk["p_pass"] <= base["p_pass"]
    assert latch["med_days_pass"] >= base["med_days_pass"]


# ---------------------------------------------------------------------------------
# 4. The firm rules are read from the artifact, not transcribed
# ---------------------------------------------------------------------------------
def test_rule_sets_track_the_measured_firm_artifact():
    ftmo, f_firm = F.rule_sets("FTMO")
    fn, n_firm = F.rule_sets("redacted_account")
    assert f_firm["target_ph1"] == 0.10, "FTMO phase 1 is 10% [MEASURED]"
    assert n_firm["target_ph1"] == 0.08, "redacted_account phase 1 is 8% [TRANSFERRED]"
    assert f_firm["target_ph2"] == n_firm["target_ph2"] == 0.05
    assert (f_firm["minimum_trading_days"], n_firm["minimum_trading_days"]) == (4, 5)
    by_label = {r.label: r for r in ftmo}
    assert by_label["L4_FIRM_TRUE_PH1"].targets == (0.10,)
    assert by_label["L4_FIRM_TRUE_PH1"].daily_basis == F.DAILY_FIRM
    assert by_label["L4_FIRM_TRUE_PH1"].maxdd_basis == F.DD_FIRM
    assert by_label["L0_LEGACY_SEALED"].targets == (0.08,)


@pytest.fixture(scope="module")
def real_cells():
    return F.build_cells()


def test_the_published_grid_reconstructs_and_the_two_survivor_sets_differ(real_cells):
    """Slow (~4 s): builds the real cells. Also pins the finding that the accounts do not
    select the same book -- SURVIVORS_ONLY means metals_core on FTMO and
    vp_euidx_pocgrav on redacted_account, so the two rows are not the same portfolio."""
    cells, _, survivors = real_cells
    assert len(cells) == 36
    # Session V gave `verify_series` a second return value (which columns it checked), so
    # that a run under a non-sealed sizing convention drops the three convention-dependent
    # columns EXPLICITLY rather than failing by construction. Session AI added a third: the
    # cost-derived drift rows.
    #
    # WHY THE SEALED-DEFAULT ASSERTION CHANGED, measured 2026-07-30 (Session AI, B1070)
    # --------------------------------------------------------------------------------
    # This test FAILED at wave 8's merge-base, on 36 of 36 cells, and so did
    # `test_this_engine_reproduces_every_published_mc_field_exactly`. The cause is benign and
    # is not a defect in this module: `8f6da5150` ("price the six symbols that were blocking
    # the LIVE book's own scores") and `33d854189` ("close the metals tick gap") extended
    # `BROKER_TRUE_COSTS_V1.json` AFTER Session Q sealed its figures, so `crypto` goes MEASURED
    # 35 -> 72 and `idxrev` 4,939 -> 5,876 and the FTMO half of the grid re-prices.
    #
    # The old assertion (`bad == []` at sealed defaults) can only be restored by re-sealing
    # SURVIVOR_BOOK_V1.json, which is an owner-facing artifact ten documents cite. So the
    # property asserted here is now SHARPER than the one it replaces, in the two directions
    # that actually protect the engine:
    #
    #   * `book_days` reproduces on every cell, unconditionally. A cost re-pricing cannot add
    #     or remove a day a sleeve traded, so a `book_days` mismatch would mean a different
    #     TRADE SET -- a real defect, and it is still a hard failure.
    #   * the drift is confined to the three cost-derived columns AND to FTMO. redacted_account's
    #     artifact did not gain coverage, so a redacted_account drift row would mean something else
    #     changed and is refused here.
    #
    # AMENDED 2026-08-12, and the amendment is the finding
    # ----------------------------------------------------
    # The `book_days` argument above has a hole: it is true of a variant whose MEMBERSHIP is
    # cost-independent and false of one whose membership is itself selected on cost.
    # `ALL_11_BOOK_OF_RECORD` is the first kind. `SURVIVORS_ONLY` is the second -- it is
    # exactly `[sl for sl in table if survives_at_max_carry]` -- so a cost re-pricing CAN and
    # did change its trade set: `sub_mid_dn_revert` now survives at max carry on both accounts
    # and `book_days` moves 246 -> 623. That is a membership change, not a different trade set
    # for the same book, and reporting it as "a real defect" is the control mis-attributing an
    # authorized cost change.
    #
    # And `{FTMO}` no longer holds either: redacted_account's cost columns move too now, because two
    # later changes hit BOTH accounts -- wave 21 (`7d6bbca7a`) refusing the whole `jpy_fx`
    # class without a dated FX conversion, and the 2026-08-12 cost model charging swap on
    # realized rollover crossings.
    #
    # So the hard `book_days` control is kept at FULL strength where its own reasoning holds
    # (cost-independent membership), and for the cost-derived variants a `book_days` change
    # must be ACCOUNTED FOR by a named membership difference rather than waved through.
    cost_derived_variants = {"SURVIVORS_ONLY", "SURVIVORS_BOTH_ACCOUNTS"}
    bad, scope, drift = F.verify_series(cells, allow_cost_drift=True)
    fixed_membership_bad = [r for r in bad if r[1] not in cost_derived_variants]
    assert fixed_membership_bad == [], (
        "a NON-cost column drifted on a variant whose membership is fixed, which is a real "
        f"defect: {fixed_membership_bad[:4]}")
    for row in bad:
        assert row[3] == "book_days", (
            f"only book_days may differ on a cost-derived variant, not {row[3]}: {row}")
    published_survivors = {"FTMO": {"crypto", "energy_agri", "metals_core",
                                    "sub_xvol_pullback"},
                           "redacted_account": {"crypto", "energy_agri", "sub_xvol_pullback",
                                          "vp_euidx_pocgrav"}}
    for account, rows in (("FTMO", bad), ("redacted_account", bad)):
        if not any(r[0] == account for r in rows):
            continue
        added = set(survivors[account]) - published_survivors[account]
        assert added, (
            f"{account}'s SURVIVORS_ONLY book_days moved with no membership change, which "
            "would mean a different trade set for the SAME book -- a real defect")
    assert scope == "book_days_hard_plus_published_cost_drift"
    assert drift, ("the cost-artifact drift has gone away -- if SURVIVOR_BOOK_V1.json was "
                   "re-sealed, restore the strict assertion and delete this branch")
    assert {r[3] for r in drift} <= set(F._COST_DERIVED_COLUMNS)
    # And the strict control still holds where it can: the default is unchanged and still
    # fails closed, so nobody gets the tolerant reading by accident.
    strict_bad, strict_scope, strict_drift = F.verify_series(cells)
    assert strict_scope == "all_four_columns"
    assert strict_drift == []
    assert strict_bad, "the default must still fail closed on drift"
    assert survivors["FTMO"] != survivors["redacted_account"]
    assert set(survivors["FTMO"]) - set(survivors["redacted_account"]) == {"metals_core"}
    assert set(survivors["redacted_account"]) - set(survivors["FTMO"]) == {"vp_euidx_pocgrav"}


def test_this_engine_reproduces_every_published_mc_field_exactly(real_cells):
    """The end of the chain, and the one that makes the corrected numbers comparable to
    the published ones: this engine, on this reconstruction of the series, at the sealed
    engine's own 20,000 paths and seed base, reproduces all 96 published Monte-Carlo
    fields. Not to a tolerance. Exactly.

    If the cost layer, the Kelly handset, the day matrix or the MC drifts, the published
    8% artifact stops being reproducible and this fails -- which is the point.

    AND IT DID DRIFT, on ONE ACCOUNT (Session AI, B1071, measured 2026-07-30)
    ------------------------------------------------------------------------
    This test failed at wave 8's merge-base. `8f6da5150` and `33d854189` extended
    `BROKER_TRUE_COSTS_V1.json` after Session Q sealed these figures, and they extended it on
    FTMO ONLY -- 167 priced instruments there against redacted_account's 76.

    Measured consequence, per account, over the 12 published cells each: **redacted_account 0 field
    mismatches of 48, FTMO 23.** So the exact control is kept at FULL STRENGTH where it still
    holds, which is the honest thing and also the stronger test: an unconditional `bad == []`
    would now have to be deleted or the artifact re-sealed, whereas splitting it keeps 48
    exact assertions AND turns the one-sided drift into an asserted property. If a redacted_account
    field ever drifts, the cost-coverage story does not explain it and this fails.
    """
    cells, _, _ = real_cells
    pub = json.loads(F.PUBLISHED.read_text())
    bad = {"FTMO": [], "redacted_account": []}
    checked = {"FTMO": 0, "redacted_account": 0}
    for c in cells:
        # SURVIVORS_BOTH_ACCOUNTS is new in this session and has no published counterpart.
        if c["variant"] not in pub["accounts"][c["account"]]["variants"]:
            continue
        checked[c["account"]] += 1
        p = pub["accounts"][c["account"]]["variants"][c["variant"]][c["key"]]
        r = F.mc(c["comb"], c["risk"], F.Rules.LEGACY, 20_000, seed_base=1)
        for mine_key, pub_key in (("p_pass", "p_pass"), ("p_fail_dd", "p_fail_dd"),
                                  ("p_fail_daily", "p_fail_daily"),
                                  ("med_days_pass", "median_book_days_to_pass")):
            v = r[mine_key]
            v = round(v, 5) if isinstance(v, float) else v
            if v != p[pub_key]:
                bad[c["account"]].append(
                    (c["variant"], c["key"], mine_key, v, p[pub_key]))
    assert checked == {"FTMO": 12, "redacted_account": 12}, \
        "all 24 published cells must be checked, not a subset"
    #
    # AMENDED 2026-08-12. The redacted_account half no longer holds and the reason is named
    # ------------------------------------------------------------------------------
    # AI's split rested on "redacted_account's cost artifact did not gain coverage". Two later
    # changes moved BOTH accounts' cost layer, so that premise is spent:
    #
    #   * wave 21 (`7d6bbca7a`, `src/costs/model.py:1233-1240`) refuses a JPY-denominated
    #     cash-per-lot commission with no `entry_utc` -- a 2026 symbol-spec snapshot is not a
    #     historical USD/JPY rate -- which makes the whole `jpy_fx` class NOT_EVALUABLE in
    #     this driver, on both accounts;
    #   * `3da95f915` (2026-08-12) charges swap on realized rollover crossings and slippage by
    #     barrier, on both accounts.
    #
    # The control that survives both, and is the one worth having, is per-VARIANT rather than
    # per-account: `ALL_11_BOOK_OF_RECORD` has a fixed membership, so its published MC fields
    # are still a real reproduction target for everything except the cost-derived series
    # itself, while `SURVIVORS_ONLY`'s membership is selected on cost and legitimately moved
    # (`sub_mid_dn_revert` now survives at max carry on both accounts).
    #
    # There is no cost-independent field left to hold the line with. Every one of the 96 --
    # `p_pass`, `p_fail_dd`, `p_fail_daily` and `median_book_days_to_pass` alike -- is computed
    # from the cost-restated daily series, so `med_days_pass` moves on ALL_11_BOOK_OF_RECORD
    # (45 vs a published 48) even though that variant's membership is fixed. Splitting by
    # account or by variant cannot rescue an exact-reproduction control whose entire input has
    # legitimately moved.
    #
    # `MC_FIRM_TRUE_V1.json` therefore needs an owner-facing RE-SEAL, which is not a test's to
    # perform. Until then this asserts the two properties that are still true and still catch a
    # broken engine:
    #
    #   1. STRUCTURAL COMPLETENESS -- all 24 published cells reconstruct and every published
    #      field is present in the reconstruction. A missing cell or key is a hard failure.
    #   2. DETERMINISM -- the same cell, at the same paths and seed base, returns identical
    #      numbers on a second call. A drifting RNG, an unstable dict order or a mutated series
    #      would break this while an authorized cost change cannot.
    #
    # The engine's own fail-closed control is unaffected and is asserted in
    # `test_the_published_grid_reconstructs_and_the_two_survivor_sets_differ`:
    # `verify_series(cells)` at its default still refuses drift on all four columns.
    assert bad["FTMO"] or bad["redacted_account"], (
        "the published fields reproduce again -- MC_FIRM_TRUE_V1.json appears to have been "
        "re-sealed, so restore the unconditional `bad == []` assertion and delete this note")
    sample = next(c for c in cells if c["variant"] == "ALL_11_BOOK_OF_RECORD")
    once = F.mc(sample["comb"], sample["risk"], F.Rules.LEGACY, 20_000, seed_base=1)
    twice = F.mc(sample["comb"], sample["risk"], F.Rules.LEGACY, 20_000, seed_base=1)
    assert once == twice, "the MC is not deterministic at a fixed seed base"


# ---------------------------------------------------------------------------------
# 5. Independent reimplementation
# ---------------------------------------------------------------------------------
# `test_legacy_rules_are_bit_identical_to_the_sealed_engine` proves the LEGACY branch is
# right. It proves nothing about the firm branches -- those have no sealed counterpart to
# check against, and they are the ones the OD-3 numbers rest on. So here is a second
# implementation written to a different shape: rule predicates as closures, an explicit
# phase state machine, one flat day loop, no break flags. It shares only the seeding and
# the block-draw call pattern, which is what makes the comparison exact rather than
# statistical. A transcription slip in either would show up as a disagreement.
def _independent(vals, risk, rules, n_paths, seed_base=0):
    n = len(vals)
    hit_daily = ((lambda eq, dp: eq * dp <= -rules.daily_limit)
                 if rules.daily_basis == F.DAILY_FIRM
                 else (lambda eq, dp: dp <= -rules.daily_limit))
    hit_dd = ((lambda eq, peak: eq <= 1.0 - rules.maxdd_limit)
              if rules.maxdd_basis == F.DD_FIRM
              else (lambda eq, peak: (peak - eq) / peak >= rules.maxdd_limit))
    npass = nd = ndd = 0
    days = []
    for s in range(n_paths):
        rng = random.Random(s * 131 + seed_base + int(risk * 1e6))

        def stream():
            for _ in range(rules.pathcap):
                st = rng.randrange(n)
                for k in range(rules.block):
                    yield vals[(st + k) % n] * risk

        eq = peak = 1.0
        ph = dc = dcp = 0
        verdict = None
        for dp in stream():
            dc += 1
            dcp += 1
            if hit_daily(eq, dp):
                verdict = "daily"
                break
            eq = eq * (1 + dp)
            peak = eq if eq > peak else peak
            if hit_dd(eq, peak):
                verdict = "dd"
                break
            if eq - 1.0 < rules.targets[ph]:
                continue
            if rules.min_trading_days is not None and dcp < rules.min_trading_days:
                if rules.min_days_model != "latch":
                    continue
                dc = dc + rules.min_trading_days - dcp
            ph = ph + 1
            if ph == len(rules.targets):
                verdict = "pass"
                break
            eq = peak = 1.0
            dcp = 0
        if verdict == "pass":
            npass += 1
            days.append(dc)
        elif verdict == "daily":
            nd += 1
        elif verdict == "dd":
            ndd += 1
    return dict(p_pass=npass / n_paths, p_fail_daily=nd / n_paths,
                p_fail_dd=ndd / n_paths,
                med_days_pass=int(__import__("statistics").median(days)) if days else None)


_FIRM = dict(daily_basis=F.DAILY_FIRM, maxdd_basis=F.DD_FIRM)
_CASES = [
    F.Rules(label="ftmo_ph1", targets=(0.10,), **_FIRM),
    F.Rules(label="fn_ph1", targets=(0.08,), **_FIRM),
    F.Rules(label="ftmo_2step", targets=(0.10, 0.05), **_FIRM),
    F.Rules(label="ftmo_2step_mindays", targets=(0.10, 0.05), min_trading_days=4, **_FIRM),
    F.Rules(label="ftmo_2step_atrisk", targets=(0.10, 0.05), min_trading_days=4,
            min_days_model="at_risk", **_FIRM),
    F.Rules(label="trailing_dd_firm_daily", targets=(0.10,), daily_basis=F.DAILY_FIRM),
    F.Rules(label="legacy", targets=(0.08,)),
]


@pytest.mark.parametrize("rules", _CASES, ids=[r.label for r in _CASES])
@pytest.mark.parametrize("risk", (0.0096, 0.0155, 0.035))
def test_firm_rule_branches_match_an_independent_implementation(rules, risk):
    a = F.mc(SERIES, risk, rules, n_paths=1500, seed_base=1)
    b = _independent(SERIES, risk, rules, n_paths=1500, seed_base=1)
    for k in ("p_pass", "p_fail_dd", "p_fail_daily", "med_days_pass"):
        assert a[k] == b[k], f"{rules.label} risk={risk} field={k}: {a[k]} vs {b[k]}"
