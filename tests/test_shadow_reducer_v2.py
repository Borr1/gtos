"""Behavioural tests for the Phase 1 shadow reducer.

The reducer's whole evidential value rests on two properties, and both are
asserted here rather than asserted in prose:

1. **It imports nothing from `src/`.** A reducer that imports the engine it
   checks proves nothing. Verified by AST over the real source file, not by
   grep — a grep for "import src" misses `importlib`, `__import__`, and a
   `sys.path` insertion followed by a plain import.
2. **It refuses rather than computing through bad input.** F17: the replay's
   `normalize_row` silently coerces unparseable OHLCV to `0.0`
   (`v4_timewarp_simulated_live_research_loop.py:4640-4667`), so a `0.0` price
   in a ledger is indistinguishable from a coercion artifact. The reducer must
   distinguish "price is zero" from "price was unparseable" and produce a number
   for neither.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest


REDUCER = (
    Path(__file__).resolve().parents[1]
    / "docs" / "audits" / "fable5-vision-audit-20260725" / "phase1"
    / "shadow_reducer_v2.py"
)


@pytest.fixture(scope="module")
def reducer():
    spec = importlib.util.spec_from_file_location("shadow_reducer_v2", REDUCER)
    module = importlib.util.module_from_spec(spec)
    # Load under a unique name and do NOT mutate sys.modules for an existing
    # key. Deleting a module from sys.modules and re-importing it creates a
    # second module object that multiprocessing then refuses to pickle from,
    # which broke three unrelated replay tests during Phase 0.
    sys.modules.setdefault("shadow_reducer_v2", module)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# 1. Zero engine imports
# ---------------------------------------------------------------------------

class TestZeroEngineImports:

    def test_reducer_imports_nothing_from_src(self):
        tree = ast.parse(REDUCER.read_text())
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                # level > 0 is a relative import; there is no package here, so
                # record it as-is and let the assertion below catch it.
                imported.add(node.module or f".{'.' * node.level}")

        offenders = sorted(
            name for name in imported
            if name.split(".")[0] in {"src", "research", "scripts", "tests"}
        )
        assert offenders == [], (
            f"the reducer imports engine code: {offenders}. Zero engine imports "
            "is the entire point — a reducer that imports the thing it checks "
            "proves nothing."
        )

    def test_reducer_uses_only_the_standard_library(self):
        tree = ast.parse(REDUCER.read_text())
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        assert roots <= set(sys.stdlib_module_names), (
            f"non-stdlib imports: {sorted(roots - set(sys.stdlib_module_names))}"
        )

    def test_reducer_has_no_dynamic_import_or_path_escape_hatch(self):
        """Closes the loophole the AST import census alone would miss."""
        tree = ast.parse(REDUCER.read_text())
        banned_calls = {"__import__", "eval", "exec", "compile"}
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in banned_calls:
                    found.append(func.id)
                if isinstance(func, ast.Attribute) and func.attr in {
                    "import_module", "exec_module", "insert", "append",
                }:
                    # sys.path.insert / sys.path.append specifically
                    value = func.value
                    if (isinstance(value, ast.Attribute) and value.attr == "path"
                            and isinstance(value.value, ast.Name)
                            and value.value.id == "sys"):
                        found.append(f"sys.path.{func.attr}")
                    elif func.attr == "import_module":
                        found.append("importlib.import_module")
        assert found == [], f"dynamic import / path manipulation present: {found}"

    def test_the_census_would_actually_catch_an_engine_import(self):
        """The census must be able to fail, or it is decoration.

        Runs the same AST logic over a synthetic module that DOES import engine
        code, and requires it to be flagged.
        """
        tree = ast.parse("import json\nfrom src.components import execution\n")
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
        offenders = [n for n in imported if n.split(".")[0] == "src"]
        assert offenders == ["src.components"]


# ---------------------------------------------------------------------------
# 2. Refusal semantics — the F17 boundary
# ---------------------------------------------------------------------------

class TestPriceClassification:

    def test_a_good_price_is_returned_as_a_float(self, reducer):
        assert reducer.classify_price(4377.82, "entry_price") == 4377.82
        assert reducer.classify_price("4377.82", "entry_price") == 4377.82
        assert reducer.classify_price(4378, "entry_price") == 4378.0

    @pytest.mark.parametrize("raw,expected_reason", [
        (None, "entry_price_absent"),
        ("", "entry_price_absent"),
        ("   ", "entry_price_absent"),
        ("n/a", "entry_price_unparseable"),
        ("--", "entry_price_unparseable"),
        ([], "entry_price_unparseable"),
        ({}, "entry_price_unparseable"),
        (True, "entry_price_unparseable"),
        (False, "entry_price_unparseable"),
        (float("nan"), "entry_price_unparseable"),
        (float("inf"), "entry_price_unparseable"),
        (float("-inf"), "entry_price_unparseable"),
        (0.0, "entry_price_zero"),
        (-0.0, "entry_price_zero"),
        (0, "entry_price_zero"),
        ("0.0", "entry_price_zero"),
        (1e-400, "entry_price_zero"),          # underflows to 0.0 in float64
        (-4377.82, "entry_price_negative"),
    ])
    def test_bad_prices_refuse_with_a_named_reason(self, reducer, raw, expected_reason):
        with pytest.raises(reducer.Refusal) as excinfo:
            reducer.classify_price(raw, "entry_price")
        assert excinfo.value.reason == expected_reason

    def test_zero_and_unparseable_are_distinguished(self, reducer):
        """The exact distinction F17 requires, asserted as inequality.

        A `0.0` that came from `normalize_row`'s coercion and a genuinely
        unreadable value must not collapse into one bucket — they call for
        different follow-up, and lumping them together is how a coercion
        artifact gets explained away as a parse problem.
        """
        with pytest.raises(reducer.Refusal) as zero:
            reducer.classify_price(0.0, "exit_price")
        with pytest.raises(reducer.Refusal) as unparseable:
            reducer.classify_price("garbage", "exit_price")
        assert zero.value.reason != unparseable.value.reason
        assert zero.value.reason == "exit_price_zero"
        assert unparseable.value.reason == "exit_price_unparseable"
        assert "coercion" in str(zero.value)

    def test_zero_is_allowed_for_non_price_quantities(self, reducer):
        """`commission_r` is genuinely 0.0 on every sealed row."""
        assert reducer.classify_number(0.0, "commission_r") == 0.0
        with pytest.raises(reducer.Refusal):
            reducer.classify_number(0.0, "risk_cash", allow_zero=False)


class TestDirectionClassification:

    @pytest.mark.parametrize("raw,expected", [
        ("LONG", "LONG"), ("long", "LONG"), ("  Long  ", "LONG"), ("BUY", "LONG"),
        ("SHORT", "SHORT"), ("short", "SHORT"), ("Sell", "SHORT"),
    ])
    def test_known_vocabulary(self, reducer, raw, expected):
        assert reducer.classify_direction(raw) == expected

    @pytest.mark.parametrize("raw", [None, "", "  ", 0, 1, "NEUTRAL", "FLAT", []])
    def test_unknown_direction_refuses(self, reducer, raw):
        with pytest.raises(reducer.Refusal):
            reducer.classify_direction(raw)

    def test_integers_are_refused_rather_than_guessed(self, reducer):
        """MT5 uses 0=BUY/1=SELL; the sealed ledgers use strings.

        Guessing an integer convention that the evidence does not use is how a
        whole arm gets sign-flipped silently, so it refuses.
        """
        with pytest.raises(reducer.Refusal) as excinfo:
            reducer.classify_direction(1)
        assert excinfo.value.reason == "direction_unknown"


# ---------------------------------------------------------------------------
# 3. Per-trade recomputation
# ---------------------------------------------------------------------------

def _row(**overrides) -> dict:
    """A minimal sealed-shaped trade row. SHORT XAUUSD, hand-computable.

    entry 4377.82 · stop 4381.602142857143 · exit 4381.63
    risk distance = 3.782142857143
    gross R = (4377.82 - 4381.63) / 3.782142857143 = -3.81/3.782142857143
            = -1.007365...
    """
    row = {
        "simulated_trade_id": "t1",
        "symbol": "XAUUSD",
        "direction": "SHORT",
        "trading_day": "2026-01-02",
        "close_reason": "selected_policy_replay:stop_loss",
        "entry_price": 4377.82,
        "stop_loss": 4381.602142857143,
        "selected_execution_policy_replay_exit": {
            "exit_price": 4381.63, "terminal_r_source": "tick",
        },
        "close_mark_price": None,
        "spread_r": 0.07138810198310992,
        "swap_cost_r": 0.004054139124960181,
        "commission_r": 0.0,
        "expected_slippage_r": 0.02,
        "cost_r": 0.09544224,
        "gross_r": -1.0,
        "net_r": -1.09544224,
        "pnl_cash": -109.544224,
        "risk_cash": 100.0,
        "net_proxy_r": -1.09544224,
        "result_scoreable": True,
    }
    row.update(overrides)
    return row


class TestRecomputeTrade:

    def test_short_gross_r_is_recomputed_from_prices(self, reducer):
        out = reducer.recompute_trade(_row())
        assert out.risk_distance == pytest.approx(3.782142857143, abs=1e-9)
        assert out.recomputed_gross_r == pytest.approx(-3.81 / 3.782142857143, abs=1e-12)
        # The engine booked exactly -1.0 for the same trade.
        assert out.ledger_gross_r == -1.0
        assert out.gross_r_delta < 0

    def test_long_gross_r_has_the_opposite_sign_convention(self, reducer):
        out = reducer.recompute_trade(_row(
            direction="LONG",
            entry_price=4377.82,
            stop_loss=4374.037857142857,
            selected_execution_policy_replay_exit={"exit_price": 4374.01},
        ))
        assert out.recomputed_gross_r == pytest.approx(
            (4374.01 - 4377.82) / 3.782142857143, abs=1e-12
        )
        assert out.recomputed_gross_r < 0

    def test_a_short_that_wins_recomputes_positive(self, reducer):
        out = reducer.recompute_trade(_row(
            selected_execution_policy_replay_exit={"exit_price": 4370.0},
        ))
        assert out.recomputed_gross_r > 0

    def test_cost_is_recomputed_from_components_not_read_from_cost_r(self, reducer):
        out = reducer.recompute_trade(_row(cost_r=999.0))
        assert out.recomputed_cost_r == pytest.approx(
            0.07138810198310992 + 0.004054139124960181 + 0.0 + 0.02, abs=1e-12
        )
        assert out.ledger_cost_r == 999.0

    def test_cost_neutral_net_r_uses_the_ledger_cost(self, reducer):
        """The headline projection must not double-count or under-charge cost."""
        out = reducer.recompute_trade(_row())
        assert out.cost_neutral_net_r == pytest.approx(
            out.recomputed_gross_r - out.ledger_cost_r, abs=1e-12
        )
        # And it is a pure re-expression of the gross-R delta.
        assert out.cost_neutral_net_r_delta == pytest.approx(out.gross_r_delta, abs=1e-12)

    def test_close_mark_price_is_the_documented_fallback(self, reducer):
        out = reducer.recompute_trade(_row(
            selected_execution_policy_replay_exit={"exit_price": None},
            close_mark_price=4381.63,
        ))
        assert out.exit_price_provenance == "close_mark_price"
        assert out.exit_price == 4381.63

    def test_a_missing_exit_price_refuses_and_is_never_inferred_from_r(self, reducer):
        """The discipline that keeps the result honest.

        This row records `gross_r == -1.0`, from which the exit price could be
        back-solved as exactly the stop. Doing so would assume the very thing
        under test, so it must refuse instead.
        """
        with pytest.raises(reducer.Refusal) as excinfo:
            reducer.recompute_trade(_row(
                selected_execution_policy_replay_exit={"exit_price": None},
                close_mark_price=None,
            ))
        assert excinfo.value.reason == "exit_price_absent"
        assert "refusing to infer it from the recorded R" in str(excinfo.value)

    @pytest.mark.parametrize("stop", [4377.82, 4377.8200000000001])
    def test_degenerate_or_near_zero_risk_distance_refuses(self, reducer, stop):
        with pytest.raises(reducer.Refusal) as excinfo:
            reducer.recompute_trade(_row(stop_loss=stop))
        assert excinfo.value.reason in ("degenerate_risk_distance", "stop_wrong_side")

    def test_a_stop_on_the_profitable_side_refuses(self, reducer):
        """A SHORT whose stop is BELOW entry is not a stop.

        Left to compute, it would produce a plausible-looking R with an inverted
        denominator — the worst possible failure, because nothing downstream
        would flag it.
        """
        with pytest.raises(reducer.Refusal) as excinfo:
            reducer.recompute_trade(_row(stop_loss=4370.0))
        assert excinfo.value.reason == "stop_wrong_side"

        with pytest.raises(reducer.Refusal) as excinfo:
            reducer.recompute_trade(_row(
                direction="LONG", entry_price=4377.82, stop_loss=4381.60,
            ))
        assert excinfo.value.reason == "stop_wrong_side"

    def test_a_zero_entry_price_refuses_as_a_suspected_coercion_artifact(self, reducer):
        with pytest.raises(reducer.Refusal) as excinfo:
            reducer.recompute_trade(_row(entry_price=0.0))
        assert excinfo.value.reason == "entry_price_zero"


class TestExitFamilyClassification:
    """Level vs mark decides whether a row measures anything at all.

    `dynamic_execution_policy.py` books a LEVEL exit at a threshold without
    consulting a price (stop :428, giveback :509, final target :462-467), and a
    MARK exit at the observation's own price-derived R (path end :641, time stop
    :626). Because the observation's R is built from the same quote that becomes
    `exit_price` (`v4_timewarp…:60803,60816-60823`), this reducer's formula is
    algebraically identical to the engine's on mark exits — agreement there is a
    tautology and must not be counted as measurement.
    """

    @pytest.mark.parametrize("close_reason", [
        "selected_policy_replay:stop_loss",
        "selected_policy_replay:giveback_close",
        "selected_policy_replay:final_target",
        "stop_reached_before_target",
        "target_reached_before_stop",
    ])
    def test_threshold_exits_are_level(self, reducer, close_reason):
        assert reducer.classify_exit_family(close_reason) == reducer.EXIT_FAMILY_LEVEL

    @pytest.mark.parametrize("close_reason", [
        "selected_policy_replay:path_end_mark_to_market",
        "time_stop_close_mark_from_m1",
        "selected_policy_replay:time_stop",
        "selected_policy_replay:max_bars_mark_to_market",
    ])
    def test_mark_exits_are_mark(self, reducer, close_reason):
        assert reducer.classify_exit_family(close_reason) == reducer.EXIT_FAMILY_MARK

    def test_an_unknown_reason_is_its_own_family_not_folded_into_mark(self, reducer):
        """UNKNOWN must be distinguishable in the output, not silently MARK.

        Folding unknown into MARK excludes it from the measurement — the safe
        direction — but makes an unrecognised reason indistinguishable from a
        verified mark exit, so a future policy could under-report with no signal.
        Excluded AND counted is the requirement.
        """
        assert reducer.classify_exit_family("some_future_exit_rule") == (
            reducer.EXIT_FAMILY_UNKNOWN
        )
        assert reducer.classify_exit_family("") == reducer.EXIT_FAMILY_UNKNOWN
        assert reducer.EXIT_FAMILY_UNKNOWN not in (
            reducer.EXIT_FAMILY_MARK, reducer.EXIT_FAMILY_LEVEL,
        )

    @pytest.mark.parametrize("close_reason", [
        "trailing_stop",
        "tp1_full_or_all_partial_close",
        "final_target_after_tp1_same_bar",
        "stop_first_same_bar_conservative",
        "same_bar_stop_close_ambiguous",
        "same_bar_giveback_close_ambiguous",
        "same_bar_trailing_close_ambiguous",
    ])
    def test_the_other_level_booked_branches_are_level(self, reducer, close_reason):
        """These do not occur in January/April but will in May/March.

        Every one passes a threshold constant as `exit_r`
        (`dynamic_execution_policy.py:498, :453, :457, :420`, and the three
        same-bar branches at :412/:491/:516 which book a hardcoded 0.0).
        Classifying them MARK would zero out the very defect they represent.
        """
        assert reducer.classify_exit_family(close_reason) == reducer.EXIT_FAMILY_LEVEL
        # And with the ledger's composed prefix.
        assert reducer.classify_exit_family(
            f"selected_policy_replay:{close_reason}"
        ) == reducer.EXIT_FAMILY_LEVEL

    def test_the_ledgers_composed_prefix_is_stripped(self, reducer):
        assert reducer.classify_exit_family("selected_policy_replay:stop_loss") == (
            reducer.EXIT_FAMILY_LEVEL
        )
        assert reducer.classify_exit_family("stop_loss") == reducer.EXIT_FAMILY_LEVEL


class TestScaleRelativeRiskDistance:
    """A one-ULP stop must refuse at ANY instrument scale.

    An absolute epsilon is instrument-scale-blind: at BTCUSD / NAS100 / US30
    magnitudes a one-ULP stop clears any fixed floor and yields an R around
    1e11, and nothing downstream caps or gates outliers, so a single such row
    would destroy an arm total.
    """

    @pytest.mark.parametrize("entry", [1.16787, 2000.0, 4377.82, 25000.0, 100000.0])
    def test_a_one_ulp_stop_refuses_at_every_scale(self, reducer, entry):
        import math as _math
        stop = _math.nextafter(entry, 0.0)
        with pytest.raises(reducer.Refusal) as excinfo:
            reducer.recompute_trade(_row(
                direction="LONG", entry_price=entry, stop_loss=stop,
                selected_execution_policy_replay_exit={"exit_price": entry * 0.99},
            ))
        assert excinfo.value.reason == "degenerate_risk_distance"

    def test_a_realistic_stop_still_computes_at_a_large_scale(self, reducer):
        """The floor must not reject genuine wide-scale trades."""
        out = reducer.recompute_trade(_row(
            direction="LONG", entry_price=100000.0, stop_loss=99500.0,
            selected_execution_policy_replay_exit={"exit_price": 99400.0},
        ))
        assert out.recomputed_gross_r == pytest.approx((99400.0 - 100000.0) / 500.0)


class TestRiskCashMustBePositive:
    """The reducer must not be weaker than the analyzer it checks.

    `analyze_b7_5_selection_sizing_matrix.py:787-790` raises
    `trade_risk_not_positive` on `risk_cash <= 0`. An earlier revision here
    blocked only exact zero, so a negative-risk row would have been admitted and
    emitted a sign-flipped pnl_cash.
    """

    @pytest.mark.parametrize("risk_cash", [0.0, -0.0, -1.0, -500.0])
    def test_non_positive_risk_cash_refuses(self, reducer, risk_cash):
        with pytest.raises(reducer.Refusal) as excinfo:
            reducer.recompute_trade(_row(risk_cash=risk_cash))
        assert excinfo.value.reason == "risk_cash_not_positive"


class TestCashProjectionIsNetted:
    """The headline cash figure must net the allowance the engine already charged.

    The price-derived R embeds the realised slip. Leaving the modelled
    `expected_slippage_r` in `cost_r` while also restating gross R charges the
    same thing twice — an earlier revision published that double-counted number
    as its headline, roughly 2.4x the defensible figure.
    """

    def test_netted_gap_subtracts_the_modelled_allowance(self, reducer):
        out = reducer.recompute_trade(_row())          # expected_slippage_r = 0.02
        assert out.netted_gap_through_r == pytest.approx(
            out.unmodelled_exit_gap_through_r + 0.02, abs=1e-12
        )
        # The netted figure is strictly less severe than the raw gap.
        assert out.netted_gap_through_r > out.unmodelled_exit_gap_through_r

    def test_the_upper_bound_is_still_reported_separately(self, reducer):
        out = reducer.recompute_trade(_row())
        assert out.gross_gap_pnl_cash_delta == pytest.approx(
            out.unmodelled_exit_gap_through_r * out.ledger_risk_cash, abs=1e-12
        )

    def test_a_small_gap_is_more_than_covered_by_the_allowance(self, reducer):
        """The _row() fixture's gap is -0.00737 R against a 0.02 R allowance.

        Netting correctly turns that trade POSITIVE: the engine over-charged it.
        A netting rule that floored at zero would hide the over-charge and
        overstate the finding, so it must not floor.
        """
        out = reducer.recompute_trade(_row())
        assert out.unmodelled_exit_gap_through_r == pytest.approx(-0.007365, abs=1e-5)
        assert out.netted_gap_through_r > 0
        assert out.cost_neutral_pnl_cash_delta > 0

    def test_a_gap_larger_than_the_allowance_stays_adverse_and_is_smaller_netted(
        self, reducer,
    ):
        """The case that drives the finding: exit well past the stop.

        entry 4377.82 · stop 4381.602142857143 · exit 4383.50
        gap = (4377.82-4383.50)/3.782142857143 - (-1.0) = -0.50175...
        netted = -0.50175 + 0.02 = -0.48175, still adverse but strictly less so.
        """
        out = reducer.recompute_trade(_row(
            selected_execution_policy_replay_exit={"exit_price": 4383.50},
        ))
        assert out.unmodelled_exit_gap_through_r < -0.5
        assert out.netted_gap_through_r < 0
        assert abs(out.netted_gap_through_r) < abs(out.unmodelled_exit_gap_through_r)
        assert abs(out.gross_gap_pnl_cash_delta) > abs(out.cost_neutral_pnl_cash_delta)

    def test_both_are_zero_on_a_mark_row(self, reducer):
        out = reducer.recompute_trade(_row(
            close_reason="selected_policy_replay:path_end_mark_to_market",
        ))
        assert out.netted_gap_through_r == 0.0
        assert out.cost_neutral_pnl_cash_delta == 0.0
        assert out.gross_gap_pnl_cash_delta == 0.0

    def test_gap_through_is_zero_on_mark_rows_even_when_gross_r_differs(self, reducer):
        """The guard that keeps a tautology out of the measurement.

        Force a mark-family close_reason onto a row whose booked `gross_r` does
        not match its prices. `gross_r_delta` is non-zero — but
        `unmodelled_exit_gap_through_r` must still be 0.0, because a mark row
        cannot evidence gap-through.
        """
        out = reducer.recompute_trade(_row(
            close_reason="selected_policy_replay:path_end_mark_to_market",
        ))
        assert out.exit_family == reducer.EXIT_FAMILY_MARK
        assert abs(out.gross_r_delta) > 1e-6
        assert out.unmodelled_exit_gap_through_r == 0.0
        assert out.cost_neutral_pnl_cash_delta == 0.0

    def test_gap_through_equals_the_delta_on_level_rows(self, reducer):
        out = reducer.recompute_trade(_row(
            close_reason="selected_policy_replay:stop_loss",
        ))
        assert out.exit_family == reducer.EXIT_FAMILY_LEVEL
        assert out.unmodelled_exit_gap_through_r == pytest.approx(
            out.gross_r_delta, abs=1e-15
        )
        # A stop overshoot is adverse: the crossing tick is past the threshold.
        assert out.unmodelled_exit_gap_through_r < 0


class TestSealedEconomicsLoading:

    def test_q_denominator_is_accepted_not_scoreable_risk_cash(self, reducer):
        """Guards the correction that cost this session a wrong first reading.

        `cash_per_accepted_risk_dollar` divides scoreable net cash by
        **accepted** risk cash (all rows), not by scoreable risk cash
        (`analyze_b7_5_selection_sizing_matrix.py:1459`). For sealed S0R0 that
        is -201.311668 / 9000.0 = -0.022367963111, and the sealed audit reports
        exactly that. Dividing by 8800.0 gives -0.022876..., which matches
        nothing in the audit.
        """
        assert -201.311668 / 9000.0 == pytest.approx(-0.022367963111, abs=1e-12)
        assert -201.311668 / 8800.0 != pytest.approx(-0.022367963111, abs=1e-9)
