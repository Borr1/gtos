"""Behavioural tests for the W7 re-cost (Stage 1.2, Session N).

Every assertion here runs the real pipeline against the real caches. None of them greps
source for a substring -- a test that asserts `"commission" in open(f).read()` passes
against a wrong implementation, which is how F38 survived five audits.

The load-bearing one is `test_pipeline_reproduces_published_base_variant`: charge every row
exactly what the validation charged and the rebuilt book must reproduce
`INTEG_W7_FINAL_RESULT.json`'s published `base` variant to five decimals. If that fails,
the matrix reconstruction has drifted and no other number in this session is trustworthy.
"""

from __future__ import annotations

import collections
import datetime as dt
import json
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

recost = pytest.importorskip("recost_w7_validation")
from src.costs.model import rollover_nights  # noqa: E402


@pytest.fixture(scope="module")
def state():
    return recost.build([])


@pytest.fixture(scope="module")
def rows(state):
    return state["rows"]


def test_book_is_eleven_sleeves_and_1679_days(rows):
    """The book of record: 11 sleeves, and the day axis the validation published."""
    assert set(r["sleeve"] for r in rows) == set(recost.BOOK_CONF)
    assert len(recost.BOOK_CONF) == 11
    days = sorted({r["date"] for r in rows})
    assert len(days) == 1679


def test_winsor_is_inert_so_gross_reconstruction_is_exact(state, rows):
    """R_gross = R_cached + charged_cost is only exact if the winsor never bound.

    `wins()` clips to [-1.3, +5] *after* the cost subtraction, so a clipped row would not
    invert. Asserted against the data rather than assumed. Also checks the tighter clip
    `substrate.outcome:260` applies (`min(target_R + 0.1, r)` = +3.1 for the `g1.0_3.0`
    cells) has not bound either.
    """
    assert state["winsor_inert"] is True
    assert state["lo"] > -1.3
    assert state["hi"] < 5.0
    for sl in ("sub_xvol_pullback", "sub_mid_dn_revert"):
        assert max(r["R"] for r in rows if r["sleeve"] == sl) < 3.1


def test_every_clean_stopout_grosses_to_exactly_minus_one(rows):
    """The reconstruction's one non-tautological check.

    A full stop is −1.0 R *by construction* before cost. So for every row the generator
    booked as a clean stop, `R_gross` must come back to exactly −1.0 — whatever cost that
    row was charged, flat or per-trade. This is what an assertion of the form
    `R_gross == R + charged_cost` cannot test, because that is the definition.
    """
    checked = 0
    for r in rows:
        if -1.35 < r["R"] <= -1.0:
            assert r["R_gross"] == pytest.approx(-1.0, abs=1e-6), (
                f"{r['sleeve']}/{r['sym']} {r['date']} grossed to {r['R_gross']}")
            checked += 1
    assert checked > 3500, f"only {checked} stop-out rows found"


def test_variable_charge_sleeves_are_detected_from_their_own_dispersion(state, rows):
    """Two generators scale the cost by stop tightness per trade
    (`INTEG_portfolio_build_w3.py:89`, `EXEC_exit_variants.py:45`). They must be found from
    the data, not from a hand-maintained list — the previous version of this pipeline
    charged `metals_core` a flat 0.0459 against a true ~0.023 because the detector required
    *identical* stop-outs and a per-trade cost never produces those.
    """
    kind = {(c["sleeve"], c["sym"]): c["charge_kind"] for c in state["cost_checks"]}
    per_trade = {sl for (sl, _), k in kind.items() if k == "per_trade"}
    assert per_trade == {"metals_core", "energy_agri"}
    for sl in ("idxrev", "fx_jpy", "crypto", "vp_euidx_pocgrav", "metals_softband"):
        assert all(k == "flat" for (s, _), k in kind.items() if s == sl)
    # and the per-trade rows must not all carry one value
    mc = {round(r["charged_cost_r"], 6) for r in rows if r["sleeve"] == "metals_core"}
    assert len(mc) > 5, "metals_core charged cost collapsed to a constant"


def test_perturbing_the_charged_cost_moves_the_restated_book(rows):
    """The control the parity test cannot provide.

    Pipeline parity runs on `R_legacy = R` and never reads `charged_cost_r`, so it matches
    to five decimals even when the cost recovery is wrong — it did, while `metals_core` was
    mispriced by 2x. This asserts the restated book is actually *sensitive* to the cost
    path: shift every charged cost by +0.01 R and the restated mean must move by
    approximately that, scaled by the confidence weighting.
    """
    W2 = recost._route_mc()
    for r in rows:
        r["R_legacy"] = r["R"]
    _, _, _, sd_book = recost.build_matrix_from(rows, "R_legacy")
    for r in rows:
        r["R_a"] = r["R_gross"]
        r["R_b"] = r["R_gross"] + 0.01
    a = recost.variant_stats(rows, "R_a", sd_book, W2, dials=(0.015,))["flat"]["mean"]
    b = recost.variant_stats(rows, "R_b", sd_book, W2, dials=(0.015,))["flat"]["mean"]
    assert b - a > 0.002, f"restated book barely moved on a 0.01 R cost shift: {b - a}"


def test_charged_cost_agrees_across_independent_witnesses(state):
    """Source, the D4 re-sim's own `resim.cost`, and the stop-out mode must not disagree."""
    checks = state["cost_checks"]
    assert checks, "no (sleeve, symbol) pairs were checked"
    bad = [c for c in checks if not c["agree"]]
    assert bad == [], f"charged-cost witness disagreement: {bad}"
    multi = [c for c in checks if c["n_witnesses"] >= 2]
    assert len(multi) / len(checks) > 0.75, "too few pairs have an independent witness"


def test_stopout_rows_encode_the_charged_cost(rows):
    """A full stop books exactly -(1 + charged_cost), so the loss rows hand the cost back.

    Covers a flat pair from every flat sleeve **and** `metals_core`, which is the one that
    would have failed: its cost is per-trade, so its stop-outs are dispersed rather than
    modal. An earlier version of this test omitted it and called that "cascaded exits never
    book a clean stop" — it books 47.
    """
    for sleeve, sym, expect in (("idxrev", "SPX500", 0.0638 / 1.5),
                                ("fx_jpy", "USDJPY", 0.1148),
                                ("fx_jpy_ny", "GBPJPY", 0.1148),
                                ("metals_softband", "XAUUSD", 0.0459),
                                ("metals_ob_micro", "XAUUSD", 0.0459),
                                ("crypto", "BTCUSD", 0.0953),
                                ("vp_euidx_pocgrav", "GER40", 0.0638),
                                ("sub_xvol_pullback", "XAGUSD", 0.0459),
                                ("sub_mid_dn_revert", "EURUSD", 0.1601)):
        sel = [r["R"] for r in rows if r["sleeve"] == sleeve and r["sym"] == sym]
        assert sel, f"no rows for {sleeve}/{sym}"
        tail = [v for v in sel if -1.35 < v <= -1.0]
        assert tail, f"no stop-outs for {sleeve}/{sym}"
        assert len({round(-1.0 - v, 6) for v in tail}) == 1, f"{sleeve}/{sym} is not flat"
        assert -1.0 - tail[0] == pytest.approx(expect, abs=5e-5)

    # metals_core: per-trade, so dispersed -- and every stop-out must still gross to -1
    mc = [r for r in rows if r["sleeve"] == "metals_core" and -1.35 < r["R"] <= -1.0]
    assert len(mc) == 47
    implied = {round(-1.0 - r["R"], 6) for r in mc}
    assert len(implied) == 47, "metals_core stop-outs collapsed to a mode"
    assert 0.011 < min(implied) and max(implied) < 0.071
    assert all(r["charged_cost_r"] == pytest.approx(-1.0 - r["R"], abs=1e-9) for r in mc)


def test_symbol_map_resolves_to_real_broker_instruments(state):
    """Every mapped name must exist in that account's instrument set -- a typo here would
    surface as a silent `CostTruthError` and a row quietly dropped from the book."""
    truth = state["truth"]
    for acct, m in recost.SYMBOL_MAP.items():
        inst = set(truth.doc["accounts"][acct]["instruments"])
        missing = sorted(v for v in m.values() if v not in inst)
        assert missing == [], f"{acct} maps to nonexistent instruments: {missing}"


def test_symbol_map_agrees_with_the_live_forensics_map():
    """Independently derived, so it must agree with the map built from the brokers' own
    traded-symbol sets (`scripts/w7_live_forensics.py:212-231`)."""
    import w7_live_forensics as F
    for broker_sym, canon in F.BROKER_TO_CANONICAL.items():
        for acct in ("FTMO", "redacted_account"):
            mapped = recost.SYMBOL_MAP[acct].get(canon, canon)
            if mapped == broker_sym:
                break
        else:
            # only assert for canonicals this session actually prices
            if canon in {c for m in recost.SYMBOL_MAP.values() for c in m}:
                pytest.fail(f"{canon} maps to no broker symbol matching {broker_sym}")


def test_index_rows_are_charged_exactly_zero_commission(rows):
    """GATE_G1B_RECEIPT §5.2a: commission is zero on the measured index CFDs, on both
    accounts. A regression here would mean the class fit had drifted."""
    for acct in ("FTMO", "redacted_account"):
        idx = [r for r in rows if r["sleeve"] == "idxrev"
               and r[f"cost_{acct}"]["status"] == "priced"]
        assert idx, f"no priced idxrev rows on {acct}"
        assert all(r[f"cost_{acct}"]["commission_r"] == 0.0 for r in idx)


def test_unpriced_rows_are_never_charged_zero(rows):
    """The F38 failure mode itself: an unavailable cost must be *absent*, not free."""
    for acct in ("FTMO", "redacted_account"):
        for r in rows:
            c = r[f"cost_{acct}"]
            assert c["status"] in ("priced", "transferred", "unpriced")
            if c["status"] == "unpriced":
                assert "total_r" not in c or c.get("coverage") == "ABSENT"
            if c["status"] == "transferred":
                assert c["transferred_from"]


def test_row_status_partitions_the_book_by_set_difference(rows):
    """Coverage is derived, not accumulated: the three statuses must sum to the full book."""
    for acct in ("FTMO", "redacted_account"):
        counts = collections.Counter(r[f"cost_{acct}"]["status"] for r in rows)
        assert sum(counts.values()) == len(rows)
        assert set(counts) <= {"priced", "transferred", "unpriced"}


def test_night_ceilings_come_from_rollover_nights_not_a_weekday_fraction(rows):
    """A full week charges SEVEN nights, not five.

    `rollover_nights` skips Saturday and Sunday midnights (`:239`) and then collects the
    weekend on the triple-swap weekday at weight 3.0 (`:241-243`). An earlier version of
    this pipeline scaled horizons by 5/7 on the first half of that rule alone, understating
    every H4 sleeve's ceiling by 1.40x and capping the JPY sleeves at 1.0 night — while a
    12 h hold that crosses a Wednesday midnight charges exactly 3.
    """
    base = dt.datetime(2026, 3, 2, 12, 0, tzinfo=dt.timezone.utc)
    week = [rollover_nights(base + dt.timedelta(hours=k), 168.0, server="FTMO-Server3",
                            rollover3days_weekday=3)[0] for k in range(168)]
    assert statistics.fmean(week) == pytest.approx(7.0, abs=0.1)
    assert recost.SLEEVE_MAX_NIGHTS["fx_jpy"] == 3.0
    assert recost.SLEEVE_MEAN_NIGHTS["fx_jpy"] == pytest.approx(0.506, abs=0.01)
    assert recost.SLEEVE_MAX_NIGHTS["metals_core"] == 14.0
    assert recost.SLEEVE_MEAN_NIGHTS["metals_core"] == pytest.approx(13.369, abs=0.01)
    # and the clip still binds: a sleeve cannot be charged past its own ceiling.
    #
    # This used to take a PRICED `fx_jpy` row. Since wave 21 (`7d6bbca7a`) the cost layer
    # refuses every JPY-denominated cash-per-lot commission that arrives without an
    # `entry_utc` -- a 2026 symbol-spec snapshot is not a historical USD/JPY rate -- so all
    # 530 `fx_jpy` rows are NOT_EVALUABLE and `next(...)` raised StopIteration. The clip is
    # a property of `row_cost`, not of that one sleeve, so exercise it on a sleeve that is
    # still priced and whose ceiling still binds below the sweep.
    # The row must actually carry swap, or the clip is unobservable: `idxrev`'s priced rows
    # have `swap_r_per_night == 0`, so every sweep point returns the same number and an
    # equality assertion on them proves nothing.
    clipped, row = next(
        (sl, r)
        for sl in ("metals_core", "crypto", "sub_xvol_pullback")
        for r in rows
        if r["sleeve"] == sl
        and r["cost_FTMO"]["status"] == "priced"
        and r["cost_FTMO"]["swap_r_per_night"] > 1e-9
        and recost.SLEEVE_MAX_NIGHTS[sl] < 20.0
    )
    cap = recost.SLEEVE_MAX_NIGHTS[clipped]
    at_cap, _ = recost.row_cost(row, "FTMO", cap, "sleeve_median", {})
    past_cap, _ = recost.row_cost(row, "FTMO", cap + 6.0, "sleeve_median", {})
    assert at_cap == pytest.approx(past_cap)
    # ...and it is not vacuous: below the ceiling the sweep still moves the cost.
    below, _ = recost.row_cost(row, "FTMO", cap / 2.0, "sleeve_median", {})
    assert below != pytest.approx(at_cap)


def test_transferred_rows_carry_a_swap_rate_that_scales_with_the_sweep(rows):
    """A transferred row must respond to the carry sweep like a priced one.

    Transferring the *total* cost froze the row at whatever `--nights` the run was built
    with, making up to 66 % of a sleeve's rows inert in exactly the column that decides
    survive/die — and pouring one night of carry into the published `true_cost_ex_swap_r`.
    """
    tr = next(r for r in rows if r["cost_FTMO"]["status"] == "transferred"
              and r["cost_FTMO"]["transfer_swap_r_per_night"] > 0)
    c0, _ = recost.row_cost(tr, "FTMO", 0.0, "sleeve_median", {})
    c2, _ = recost.row_cost(tr, "FTMO", 2.0, "sleeve_median", {})
    assert c2 > c0, "transferred row is inert to the carry sweep"
    assert c2 - c0 == pytest.approx(2 * tr["cost_FTMO"]["transfer_swap_r_per_night"], rel=1e-6)


def test_price_derivation_refuses_a_timeframe_mismatch(rows):
    """`resolve_price` must not invert an M15-scale stop through an H4 `atr_frac`.

    `attach_stops` already refuses this; the price path did not, and the error runs 4-5x on
    the JPY sleeves. Any row that falls back to a derived price must have matched timeframes.
    """
    for r in rows:
        if r["price_basis"] == "P2_SELF_ATRFRAC":
            assert recost.SLEEVE_TF[r["sleeve"]] == "H4"
    jpy_derived = [r for r in rows if r["sleeve"] in ("fx_jpy", "fx_jpy_ny")
                   and r["price_basis"] == "P2_SELF_ATRFRAC"]
    assert jpy_derived == [], "JPY rows still derive a price through an H4 atr_frac"


def test_jpy_sleeve_stop_is_m15_not_h4(rows):
    """fx_jpy/fx_jpy_ny stop at 1.0 x ATR14(M15). Reading an H4 ATR for them inflates the
    stop ~5x and silently divides their commission by 5 -- the defect this guard exists for.
    """
    jpy = [r["sl_price"] for r in rows
           if r["sleeve"] == "fx_jpy_ny" and r["sym"] == "USDJPY" and r["sl_price"]]
    ref = [r["sl_price"] for r in rows
           if r["sleeve"] == "fx_jpy" and r["sym"] == "USDJPY" and r["sl_price"]]
    assert jpy and ref
    assert statistics.median(jpy) == pytest.approx(statistics.median(ref), rel=0.5)


def test_pipeline_reproduces_published_base_variant(state, rows):
    """The machinery's own null control.

    Charge every row exactly what the validation charged, rebuild the 11-column matrix, and
    the result must equal `INTEG_W7_FINAL_RESULT.json`'s published `base` variant. This is
    what licenses every restated number in this session.
    """
    W2 = recost._route_mc()
    for r in rows:
        r["R_legacy"] = r["R"]
    _, _, _, sd_book = recost.build_matrix_from(rows, "R_legacy")
    got = recost.variant_stats(rows, "R_legacy", sd_book, W2, dials=(0.015,))["flat"]
    pub = json.loads((recost.ROUTE / "INTEG_W7_FINAL_RESULT.json").read_text())
    assert got["mean"] == pytest.approx(pub["variant_daily"]["base"]["mean"], abs=5e-5)
    assert got["std"] == pytest.approx(pub["variant_daily"]["base"]["std"], abs=5e-5)
    assert got["n_days"] == pub["n_days"]
    assert sd_book == pytest.approx(pub["sd_book"], abs=5e-5)


def test_the_jpy_class_is_not_evaluable_and_says_so_rather_than_charging_zero(rows):
    """B112's USDJPY commission is NOT_EVALUABLE in this driver, and that must fail CLOSED.

    B112 measured that the receipt's per-symbol R values are window-specific and are NOT
    rates: the validation's USDJPY stop is ~1.9x the live scalp stop, so its commission was
    near 0.10 R rather than the 0.1948 R measured on the live fills. This test asserted that
    number directly.

    It cannot any more, and the reason is a deliberate upstream tightening rather than a
    regression. Wave 21 (`7d6bbca7a`, `src/costs/model.py:1233-1240`) refuses a
    JPY-denominated cash-per-lot commission that arrives with no `entry_utc`, because
    converting it needs a date-indexed USD-per-price-unit rate and the 2026 symbol-spec
    snapshot is not a historical default. This driver prices at `holding_hours=24.0` with no
    entry instant on purpose -- that is what keeps its swap term a per-night band the book can
    be swept over -- so the whole `jpy_fx` class is now NOT_EVALUABLE here. Threading a real
    `entry_utc` through would also switch swap from modelled nights to exact rollover counting
    and move the published W7 numbers, which is a research decision and not a test's to make.

    So what is asserted is the property that matters: the refusal is VISIBLE and it does not
    become a cheap sleeve. The number B112 measured is preserved above in prose; if the dated
    conversion is ever supplied, this test fails and the original assertion comes back.
    """
    usd = [r for r in rows if r["sleeve"] == "fx_jpy" and r["sym"] == "USDJPY"]
    assert usd, "the USDJPY rows themselves must still be in the book"
    assert all(r["cost_FTMO"]["status"] == "unpriced" for r in usd)
    assert all(r["cost_FTMO"]["coverage"] == "ABSENT" for r in usd)
    # And no JPY row silently acquired a commission number from somewhere else.
    assert not any("commission_r" in r["cost_FTMO"] for r in usd)


def test_live_carry_is_derived_from_the_deal_records_not_transcribed(state):
    """The live carry table must come from `LIVE_TRADE_ROWS.jsonl`, so it moves if the file does.

    Three of the eleven sleeves fired live. Their carry is measured from the broker's own
    realized `swap` field per position — not modelled, and not a constant pasted into the
    source.
    """
    lc = recost.LIVE_CARRY
    assert set(lc) == {"idxrev", "fx_jpy", "fx_jpy_ny"}
    assert lc["fx_jpy"]["n"] == 32 and lc["fx_jpy"]["n_paid_swap"] == 0
    assert lc["fx_jpy_ny"]["n"] == 9 and lc["fx_jpy_ny"]["n_paid_swap"] == 0
    assert lc["idxrev"]["n"] == 59 and lc["idxrev"]["n_paid_swap"] == 39
    assert lc["fx_jpy"]["measured_nights"] == 0.0
    assert lc["idxrev"]["measured_nights"] > 0.5


def test_only_a_structural_bound_promotes_a_sleeve_out_of_carry_conditional(state):
    """A favourable live sample is not a bound.

    The live window never reached any sleeve's exit ceiling (max hold 7.36 h against 12 h),
    so it cannot testify about carry there. `fx_jpy` is promoted because its entry hour and
    48-bar ceiling put its close at 21:00 broker — zero rollovers, structurally. `fx_jpy_ny`
    shares the ceiling but enters at 16:00, so its ceiling is 04:00 the *next* broker day;
    its nine zero-swap positions are an observation, and it stays conditional.
    """
    assert recost.CARRY_STRUCTURAL == {"fx_jpy"}
    table = recost.sleeve_table(state["rows"], "FTMO", {})
    tiers = {sl: v["survivor_tier"] for sl, v in table.items()}
    assert tiers["metals_softband"] == "CARRY_CONDITIONAL"

    # The two JPY sleeves used to be MEASURED_LIVE_CARRY and CARRY_CONDITIONAL_LIVE_SUPPORTED.
    # They are NOT_EVALUABLE now, and the route from there to here is the finding: wave 21's
    # cost layer refuses the whole `jpy_fx` class without a dated FX conversion
    # (`src/costs/model.py:1233-1240`), so every one of their 530 + 197 rows is `unpriced` --
    # and `sleeve_table` used to impute an unpriced row at `class_medians.get(sl, 0.0)` ex-swap
    # and ZERO swap per night. With no priced row anywhere in the class both fall back to
    # 0.0, `net_r` at max carry becomes plain gross, and BOTH SLEEVES WERE PUBLISHED
    # `UNCONDITIONAL` -- the most permissive survivor tier -- because their cost was unknown.
    # An upstream layer that fails closed, turned fail-open one function downstream, in the
    # column that decides survive/die.
    for sleeve in ("fx_jpy", "fx_jpy_ny"):
        assert tiers[sleeve] == "NOT_EVALUABLE_NO_COST_COVERAGE"
        assert table[sleeve]["cost_evaluable"] is False
        assert table[sleeve]["priced_or_transferred_rows"] == 0
        assert table[sleeve]["n"] > 0, "the rows are still there; only their cost is not"
    # The guard is not a blanket: every sleeve with coverage still gets a real tier.
    for sleeve, row in table.items():
        if row["priced_or_transferred_rows"]:
            assert row["survivor_tier"] != "NOT_EVALUABLE_NO_COST_COVERAGE"


def test_structural_sleeves_do_not_publish_an_averaged_break_even_hold(state):
    """`_hours_for_nights` averages over all 168 entry instants. For a sleeve with a fixed
    entry hour that average is not a threshold the sleeve can reach, so publishing it would
    invite exactly the wrong reading."""
    t = recost.sleeve_table(state["rows"], "FTMO", {})
    assert t["fx_jpy"]["break_even_hold_hours"] is None
    assert t["fx_jpy"]["break_even_note"]
    assert t["metals_softband"]["break_even_hold_hours"] > 100
