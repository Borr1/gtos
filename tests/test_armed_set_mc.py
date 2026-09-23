"""Controls for the armed-set measurement (`scripts/armed_set_mc.py`) and for the
sleeve-set / sizing-convention / start-equity additions to `scripts/mc_firm_rules.py`.

Two things have to be true and neither is obvious from reading a diff.

**The additions must be inert by default.** Q's published `MC_FIRM_TRUE_V1.json` has to
keep reproducing, so every new parameter has to reduce to the sealed behaviour at its
default. The strongest form of that is `test_defaults_are_the_sealed_engine_exactly`,
which drives the whole chain -- `mc_governed` -> `mc_firm_rules.mc` ->
`INTEG_portfolio_build_w2.mc_series` -- and requires exact equality at both joints, not
closeness.

**The claim about live sizing must be sourced, not transcribed.** The session's headline
is that the live path applies the nominal dial with no volatility term. That is a claim
about production code, so it is asserted against production code
(`test_live_sizing_chain_has_no_volatility_term`), and it will go red the day someone adds
one -- which is the correct outcome, because that would make the published `eff_risk_pct`
right again.
"""

from __future__ import annotations

import math
import random
import statistics
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

import armed_set_mc as A  # noqa: E402


def _synthetic_matrix(cols, n=400, seed=11):
    """A per-sleeve daily R matrix with the real shape: sparse, fat left tail, drift."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        row = []
        for _ in cols:
            if rng.random() < 0.72:
                row.append(0.0)
            elif rng.random() < 0.42:
                row.append(-abs(rng.gauss(0.9, 0.6)))
            else:
                row.append(abs(rng.gauss(1.1, 1.4)))
        out.append(row)
    return out


COLS = ["metals_core", "crypto", "energy_agri", "sub_xvol_pullback"]
RAW = _synthetic_matrix(COLS)
RISKS = (0.0085, 0.020)


@pytest.fixture(scope="module")
def w2():
    return F.M._route_mc()


# ---------------------------------------------------------------------------------
# 1. Inertness -- the published artifact must keep reproducing
# ---------------------------------------------------------------------------------
@pytest.mark.parametrize("risk", RISKS)
def test_defaults_are_the_sealed_engine_exactly(w2, risk):
    """mc_governed(ungoverned) == mc_firm_rules.mc == INTEG_portfolio_build_w2.mc_series.

    Both joints, exactly, on the same series. This is what licenses reading any difference
    below as caused by one named change."""
    comb = A.comb_from(RAW, COLS, F.KELLY_SEALED)
    g = A.mc_governed(RAW, COLS, risk, F.Rules.LEGACY, 4000, seed_base=1,
                      kelly=F.KELLY_SEALED)
    m = F.mc(comb, risk, F.Rules.LEGACY, 4000, seed_base=1)
    t = w2.mc_series(comb, risk, n_paths=4000, seed_base=1)
    for k in ("p_pass", "p_fail_dd", "p_fail_daily", "p_timeout", "med_days_pass"):
        assert g[k] == m[k] == t[k], k


def test_start_equity_default_changes_nothing(w2):
    comb = A.comb_from(RAW, COLS, F.KELLY_SEALED)
    a = F.mc(comb, 0.0085, F.Rules.LEGACY, 3000, seed_base=1)
    b = F.mc(comb, 0.0085, F.Rules.LEGACY, 3000, seed_base=1,
             start_equity=1.0, start_days_served=0)
    assert a == b


def test_no_sleeve_set_leaves_the_published_grid_shape(monkeypatch):
    """`build_cells()` with no named set must still be the 36-cell published grid, in the
    published order. Anything else and `MC_FIRM_TRUE_V1.json` stops reproducing."""
    cells, _, survivors = F.build_cells()
    assert len(cells) == 36
    assert [c["variant"] for c in cells[:3]] == ["ALL_11_BOOK_OF_RECORD"] * 3
    # The GRID SHAPE is what this test is named for and what `MC_FIRM_TRUE_V1.json`'s
    # reproducibility depends on. The survivor MEMBERSHIP is cost-derived and has moved since
    # Q sealed it -- `sub_mid_dn_revert` now survives at max carry on both accounts -- so
    # pinning it to a literal four-tuple here made this a second place the survivor set was
    # written down, which is the thing `SURVIVOR_BOOK_V1.json` exists to stop.
    #
    # Asserted instead: every sleeve Q sealed as an FTMO survivor is still one (a DISAPPEARANCE
    # is a real regression and still fails), the set is a subset of the eleven-sleeve book of
    # record, and it is not empty.
    assert set(survivors["FTMO"]) >= {"crypto", "energy_agri", "metals_core",
                                      "sub_xvol_pullback"}, (
        "a sleeve Q sealed as an FTMO survivor no longer survives: "
        f"{sorted({'crypto', 'energy_agri', 'metals_core', 'sub_xvol_pullback'} - set(survivors['FTMO']))}")
    book_of_record = {tuple(sorted(c["sleeves"])) for c in cells
                      if c["variant"] == "ALL_11_BOOK_OF_RECORD"}
    assert len(book_of_record) == 1
    assert set(survivors["FTMO"]) <= set(next(iter(book_of_record)))
    named = F.build_cells({"X": ["crypto"]})[0]
    assert len(named) == 36 + 12
    # the named set is APPENDED, so the first 36 are byte-for-byte the published grid.
    for a, b in zip(cells, named[:18] + named[24:42]):
        assert (a["variant"], a["key"], a["account"], a["comb"]) == \
               (b["variant"], b["key"], b["account"], b["comb"])


# ---------------------------------------------------------------------------------
# 2. The sleeve-set argument
# ---------------------------------------------------------------------------------
def test_sleeve_set_parses_and_fails_closed_on_a_typo():
    assert F.parse_sleeve_set("A=crypto,metals_core") == ("A", ["crypto", "metals_core"])
    for bad in ("nosign", "A=", "A=crypto,cryptoo", "A=crypto,crypto"):
        with pytest.raises(SystemExit):
            F.parse_sleeve_set(bad)


def test_a_named_set_equals_the_derived_variant_it_names():
    """A named set must reproduce the derived variant it names, EXACTLY, on the account whose
    survivors it is -- and must NOT reproduce it on the other account, whose survivors are a
    different set. That asymmetry is the reason an explicit name is needed at all.

    The named set is FTMO's OWN derived survivors, read from `build_cells`, not the literal
    four-tuple `A.ARMED_4`. Those were the same list when Q sealed the grid and they are not
    any more: `sub_mid_dn_revert` now survives at max carry on both accounts, so naming
    `ARMED_4` compared a four-sleeve book against a five-sleeve one and asserted their series
    were equal, which is a statement about a stale constant rather than about the engine.
    `ARMED_4` is still asserted below to be what it says it is -- the armed book -- which is a
    different question and belongs to `test_no_sleeve_set_leaves_the_published_grid_shape`.
    """
    _, _, derived = F.build_cells()
    cells, _, surv = F.build_cells({"NAMED": sorted(derived["FTMO"])})
    idx = {(c["account"], c["variant"], c["key"]): c for c in cells}
    assert sorted(derived["FTMO"]) != sorted(derived["redacted_account"]), (
        "the two accounts select the same book, so this test cannot show the asymmetry "
        "it exists to show")
    for key in ("fwd_nights_max", "full_nights_0.0"):
        ftmo_named = idx[("FTMO", "NAMED", key)]
        ftmo_surv = idx[("FTMO", "SURVIVORS_ONLY", key)]
        assert ftmo_named["comb"] == ftmo_surv["comb"]
        fn_named = idx[("redacted_account", "NAMED", key)]
        fn_surv = idx[("redacted_account", "SURVIVORS_ONLY", key)]
        assert fn_named["sleeves"] != fn_surv["sleeves"]


def test_the_two_three_sleeve_books_in_the_record_are_different_books():
    """`CONF_FLOOR_3` (armed minus sub_xvol_pullback) and Q's `SURVIVORS_BOTH_ACCOUNTS`
    are both called "the three-sleeve book" somewhere in the record. They share two
    sleeves and disagree on the other."""
    assert set(A.CONF_FLOOR_3) != set(A.BOTH_3)
    assert set(A.CONF_FLOOR_3) & set(A.BOTH_3) == {"crypto", "energy_agri"}
    assert set(A.ARMED_4) - set(A.CONF_FLOOR_3) == {"sub_xvol_pullback"}
    assert set(A.ARMED_4) - set(A.BOTH_3) == {"metals_core"}


# ---------------------------------------------------------------------------------
# 3. The sizing claim, asserted against production code
# ---------------------------------------------------------------------------------
def test_live_sizing_chain_has_no_volatility_term():
    """The headline claim, tested where it lives.

    `clean3_w7_ceiling_nom2p00` must hand `size_correlated_units` the bare nominal, and
    the resulting unit risk must be `base * conf` with no volatility factor. Sizing one
    metals_core intent at the live profile is the whole proof: 0.020 * 1.00 = 0.020, not
    0.020 * 0.4234."""
    from src.components.ultimate_book import admission as P
    prof = P.ALLOCATION_PROFILES["clean3_w7_ceiling_nom2p00"]
    assert prof.risk_per_unit_A == prof.risk_per_unit_B == 0.020
    it = P.TradeIntent(sleeve="metals_core", symbol="XAUUSD", direction=1,
                       decision_day="2026-07-29", stop_dist=1.0)
    units = P.size_correlated_units([it], base_risk_per_unit=prof.risk_per_unit_A,
                                    include_clean3=True)
    assert len(units) == 1 and units[0].sized
    assert units[0].unit_risk_pct == pytest.approx(0.020, abs=1e-9)


def test_half_kelly_is_selected_by_the_live_config_and_is_a_smaller_reshape_than_the_vol_match():
    """`ultimate_book_kelly_conservative: true` selects the half bins, and the half bins
    are a REAL volatility reshape -- which is why the naive 1/vol_scale multiple is wrong.
    They are not, however, the 0.7504 the live package claims they stand in for."""
    from src.components.ultimate_book import admission as P
    assert P.KELLY_LITE_BINS_HALF == ((1, 1, 0.748), (2, 3, 0.991), (4, 99, 1.241))
    half = F.kelly_fn(F.KELLY_HALF)
    full = F.kelly_fn(F.KELLY_SEALED)
    for na in (1, 2, 3, 4, 9):
        assert 0.70 < half(na) / full(na) < 1.0
    cf = A.comb_from(RAW, COLS, F.KELLY_SEALED)
    ch = A.comb_from(RAW, COLS, F.KELLY_HALF)
    reshape = statistics.pstdev(ch) / statistics.pstdev(cf)
    assert 0.70 < reshape < 1.0


def test_live_nominal_risk_basis_drops_the_vol_scale_and_the_sealed_one_keeps_it():
    st = F.M.build([])
    rows = st["rows"]
    for r in rows:
        r["R_legacy"] = r["R"]
    _, _, _, sd_book = F.M.build_matrix_from(rows, "R_legacy")
    import collections
    pool = collections.defaultdict(list)
    for r in rows:
        c = r["cost_FTMO"]
        if c["status"] == "priced":
            pool[r["sleeve"]].append(c["cost_ex_swap_r"])
    cm = {k: statistics.median(v) for k, v in pool.items()}
    sub = [r for r in rows if r["sleeve"] in A.ARMED_4]
    _, _, r_pub, vs = F.series(sub, "FTMO", cm, "max", sd_book, forward=True)
    _, _, r_live, _ = F.series(sub, "FTMO", cm, "max", sd_book, forward=True,
                               kelly=F.KELLY_HALF,
                               risk_basis=F.RISK_LIVE_NOMINAL)
    assert r_pub == pytest.approx(F.DIAL * vs)
    assert r_live == F.DIAL
    assert vs < 0.5      # the armed book is sized DOWN 2x+ by the published convention


# ---------------------------------------------------------------------------------
# 4. The governor model
# ---------------------------------------------------------------------------------
def test_gross_cap_can_only_lower_the_days_exposure():
    """The 4% cap only ever sheds units, so the capped series' |daily move| is never
    larger than the uncapped one on the same day. Checked on the day series directly,
    which is a stronger statement than checking p_pass."""
    confs = [A.M.BOOK_CONF[c] for c in COLS]
    km = F.kelly_fn(F.KELLY_HALF)
    order = sorted(range(len(COLS)), key=lambda j: -confs[j])
    for row in RAW:
        na = sum(1 for j in range(len(COLS)) if abs(row[j] * confs[j]) > 1e-9)
        kl = km(na)
        gross = sum(0.020 * confs[j] * kl for j in range(len(COLS))
                    if abs(row[j] * confs[j]) > 1e-9)
        avail, capped = A.GROSS_OPEN_RISK_CAP, 0.0
        for j in order:
            if abs(row[j] * confs[j]) <= 1e-9:
                continue
            u = 0.020 * confs[j] * kl
            if u <= avail + 1e-9:
                avail -= u
                capped += u
        assert capped <= gross + 1e-12
        assert capped <= A.GROSS_OPEN_RISK_CAP + 1e-9


def test_smooth_derisk_is_inert_at_or_above_the_initial_balance():
    """`derisk_mode: smooth` measures drawdown from the STATIC initial balance
    (`admission.py:1326-1343`), so it is exactly 1.0 while the account is in profit --
    which is where FTMO is. A model that credited it with protection at +7.9% would be
    crediting a guard that is switched off."""
    comb = A.comb_from(RAW, COLS, F.KELLY_HALF)
    a = A.mc_governed(RAW, COLS, 0.020, F.Rules.LEGACY, 3000, seed_base=1,
                      kelly=F.KELLY_HALF, derisk=False, start_equity=1.20)
    b = A.mc_governed(RAW, COLS, 0.020, F.Rules.LEGACY, 3000, seed_base=1,
                      kelly=F.KELLY_HALF, derisk=True, start_equity=1.20)
    assert a["p_pass"] == b["p_pass"]
    assert len(comb) == len(RAW)


# ---------------------------------------------------------------------------------
# 5. The concentration model
# ---------------------------------------------------------------------------------
def test_haircut_scales_the_edge_and_leaves_the_dispersion_alone():
    j = COLS.index("sub_xvol_pullback")
    fired = [i for i in range(len(RAW)) if abs(RAW[i][j]) > 1e-12]
    base = [RAW[i][j] for i in fired]
    for lam in (0.0, 0.5, 1.0):
        h = A.haircut(RAW, COLS, "sub_xvol_pullback", lam)
        got = [h[i][j] for i in fired]
        assert statistics.fmean(got) == pytest.approx(lam * statistics.fmean(base))
        assert statistics.pstdev(got) == pytest.approx(statistics.pstdev(base))
        # zero days stay zero, so the day axis and n_active never move
        for i in range(len(RAW)):
            if i not in fired:
                assert h[i][j] == RAW[i][j] == 0.0
    # and the naive alternative does shrink the dispersion, which is why it is not primary
    s = A.scale_haircut(RAW, COLS, "sub_xvol_pullback", 0.5)
    got = [s[i][j] for i in fired]
    assert statistics.pstdev(got) == pytest.approx(0.5 * statistics.pstdev(base))


def test_haircut_of_an_absent_sleeve_is_a_no_op():
    assert A.haircut(RAW, COLS, "fx_jpy", 0.0) == RAW


def test_paired_bootstrap_reports_zero_advantage_for_a_book_against_itself():
    comb = A.comb_from(RAW, COLS, F.KELLY_HALF)
    days = [__import__("datetime").date(2025, 1, 1)
            + __import__("datetime").timedelta(days=i) for i in range(len(comb))]
    r = A.paired_block_bootstrap(days, comb, days, comb, n_boot=500)
    assert r["observed_diff_total_r"] == pytest.approx(0.0, abs=1e-9)
    assert r["boot_median"] == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------------
# 6. The guards Session V's arithmetic refuter said were claimed but not asserted
# ---------------------------------------------------------------------------------
def test_shares_only_refuses_a_non_sealed_sizing_convention(tmp_path):
    """`--shares-only` merges into an EXISTING artifact and its `--out` defaults to the
    committed one. Under `--kelly live_half_bins` it would silently rewrite every published
    share on a different basis, add rows for an ad-hoc book, and write no marker — because
    the `sizing_convention` block sits on a path this branch returns before reaching."""
    target = tmp_path / "mc.json"
    target.write_text('{"contribution_shares": {}}')
    with pytest.raises(SystemExit):
        F.main(["--shares-only", "--out", str(target), "--kelly", F.KELLY_HALF])
    with pytest.raises(SystemExit):
        F.main(["--shares-only", "--out", str(target),
                "--sleeve-set", "FOO=crypto"])
    assert target.read_text() == '{"contribution_shares": {}}'


def test_sealed_defaults_write_no_sizing_convention_block_and_non_sealed_does(tmp_path):
    """The marker that says "this run was not the sealed grid" must appear whenever any
    non-sealed flag is used, and must NOT appear otherwise — that is what keeps the
    published artifact's shape."""
    sealed = tmp_path / "sealed.json"
    F.main(["--paths", "40", "--verify-paths", "40", "--out", str(sealed)])
    import json as _json
    assert "sizing_convention" not in _json.loads(sealed.read_text())
    named = tmp_path / "named.json"
    F.main(["--paths", "40", "--verify-paths", "40", "--out", str(named),
            "--sleeve-set", "ARMED_4=" + ",".join(A.ARMED_4)])
    doc = _json.loads(named.read_text())
    assert doc["sizing_convention"]["named_sleeve_sets"]["ARMED_4"] == A.ARMED_4
    assert doc["sizing_convention"]["kelly"] == F.KELLY_SEALED


def test_frequency_profile_reports_the_true_median_on_an_even_month_count():
    """`counts[n // 2]` is the UPPER median and reported 7 book-days/month where the true
    median is 6.5 — beside a mean of 7.11 that multiplies every monthly figure."""
    import datetime as _dt
    days = []
    for k, c in enumerate([2, 4, 6, 7, 8, 14]):     # even count, median 6.5
        days += [_dt.date(2025, k + 1, i + 1) for i in range(c)]
    prof = A.frequency_profile(days)
    assert prof["n_calendar_months"] == 6
    assert prof["median"] == 6.5


def test_matrix_reconstruction_control_is_exact_not_tolerant():
    """A 1e-12 tolerance is ~10,000 ulp and would not notice the round trip breaking."""
    comb = A.comb_from(RAW, COLS, F.KELLY_SEALED)
    assert A.assert_matrix_reconstructs(RAW, COLS, comb) == []
    nudged = list(comb)
    nudged[3] = math.nextafter(nudged[3], math.inf)
    assert A.assert_matrix_reconstructs(RAW, COLS, nudged) != []


def test_importing_this_module_does_not_break_the_research_namespace_package():
    """The regression Session V's own A/B caught, pinned so it cannot come back.

    `scripts/research/` is a REGULAR package (`__init__.py`), and a regular package wins
    over a namespace portion at any `sys.path` position. So once `scripts/` is searchable —
    which every one of these scripts needs, to import `recost_w7_validation` — `import
    research` resolves to `scripts/research` and `research.operations.*` stops resolving for
    the rest of the process. `tests/test_audit_b6_broker_cost_calibration.py` and
    `tests/test_b7_5_post_acceleration_contract.py` both import through it, and this module
    sorts alphabetically ahead of both, so it went from latent to load-bearing the moment
    this file existed: 6 tests moved from passing to failing in the full-suite A/B, with
    nothing in the diff that could explain them.

    The fix is to pin the repo-root package in `sys.modules` before extending the path. This
    test asserts the property, not the fix, so a different fix still satisfies it."""
    import importlib
    import research.operations
    assert not hasattr(research.operations, "__file__") or \
        "scripts" not in str(research.__path__), \
        f"`research` resolved to {list(research.__path__)}, shadowing the repo-root package"
    mod = importlib.import_module(
        "research.operations.final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20")
    assert mod is not None
