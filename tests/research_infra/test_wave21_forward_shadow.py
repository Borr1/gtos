"""Unit tests for the wave-21 forward-shadow lane.

Covers the frozen-rule mechanics that must hold on the VPS without any market
connection: closed-bar discipline, dual-lane selection semantics (abstain,
minimum-prediction, occupancy), cost fail-closure, namespace refusal, state
resume, and the feature contract's mirror-fidelity against the committed
research scorer bytes (estate-guarded).
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.research_infra.wave21_forward_shadow.feature_contract import (
    LANE_GENERAL,
    LANE_SCOPED_LSR,
    LIMIT_FAMILIES,
    LSR_FAMILY,
    MAX_COST_R,
    MIN_EXPECTED_NET_R,
    PREDECISION_FEATURE_KEYS,
    eligible,
    order_type_for_family,
    shadow_feature_row,
)
from src.research_infra.wave21_forward_shadow.mt5_read_only import (
    ShadowReadOnlyMT5Adapter,
    ShadowMutationRefused,
    aggregate_h1_rows_from_m15_rows,
)
from src.research_infra.wave21_forward_shadow.namespace_guard import (
    NamespaceCollisionError,
    assert_namespace_safe,
    claim_namespace,
    release_namespace,
)
from src.research_infra.wave21_forward_shadow.shadow_lifecycle import WouldBeOrder
from src.research_infra.wave21_forward_shadow.shadow_select import (
    occupancy_end_for_selection,
    prune_occupancy,
    select_market_top_abstain,
)
from src.research_infra.wave21_forward_shadow.state import ShadowState

UTC = timezone.utc
T0 = datetime(2026, 8, 12, 12, 15, tzinfo=UTC)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def make_raw(
    *,
    symbol: str = "EURUSD",
    family: str = "displacement_continuation",
    key_suffix: str = "aa",
    cost_r: float = 0.05,
    decision: datetime = T0,
) -> dict:
    features = {name: 0.5 for name in PREDECISION_FEATURE_KEYS}
    features["trend_state_m15"] = "UP"
    features["trend_transition_flag"] = "False"
    return {
        "canonical_replay_candidate_instance_key": "candidate_occurrence_"
        + (key_suffix * 32)[:64],
        "candidate_id": f"broadorigin_{key_suffix}",
        "symbol": symbol,
        "side": "LONG",
        "origin_family": family,
        "session_bucket": "london",
        "session": "london",
        "decision_time_utc": decision.isoformat(),
        "limit_first_expiry_utc": (decision + timedelta(minutes=120)).isoformat(),
        "entry_price": 1.1000,
        "stop_loss": 1.0950,
        "take_profit_1": 1.1100,
        "risk_reward_ratio": 2.0,
        "cost_r": cost_r,
        "spread_r": cost_r - 0.038,
        "expected_slippage_r": 0.02,
        "swap_cost_r": 0.0,
        "commission_r": 0.018,
        "decision_window_id": f"forward_shadow:{decision.isoformat()}",
        "trading_day": decision.date().isoformat(),
        "predecision_limit_fillability": {
            "available": True,
            "atr14": 0.0011,
            "distance_to_limit_atr": 0.0,
            "distance_to_limit_risk": 0.0,
            "limit_marketable_at_decision": True,
        },
        "poi_state": None,
        "predecision_features": features,
    }


def feature_row_for(**kwargs) -> dict:
    return shadow_feature_row(make_raw(**kwargs))


# ---------------------------------------------------------------------------
# feature contract
# ---------------------------------------------------------------------------


class TestFeatureContract:
    def test_order_type_projection_matches_funnel(self):
        for family in LIMIT_FAMILIES:
            assert order_type_for_family(family) == "LIMIT"
        assert order_type_for_family(LSR_FAMILY) == "MARKET"
        assert order_type_for_family("displacement_continuation") == "MARKET"

    def test_row_shape_and_derived_features(self):
        row = feature_row_for()
        assert row["proposed_order_type"] == "MARKET"
        assert row["utc_hour"] == "12"
        assert row["weekday"] == str(T0.weekday())
        assert row["symbol_x_family"] == "EURUSD|displacement_continuation"
        risk = abs(1.1000 - 1.0950)
        assert row["risk_over_atr"] == pytest.approx(risk / 0.0011)
        assert row["risk_fraction_of_entry"] == pytest.approx(risk / 1.1000)
        assert row["predecision_geometry_valid"] is True
        # poi fields absent -> NaN numerics, sentinel categorical
        assert math.isnan(row["poi_age_hours"])
        assert row["poi_mitigation_status"] == "not_applicable"

    def test_missing_predecision_features_refused(self):
        raw = make_raw()
        del raw["predecision_features"]["sweep_depth_atr"]
        with pytest.raises(Exception):
            shadow_feature_row(raw)

    def test_predecision_feature_keys_pin_production_module(self):
        bog = pytest.importorskip("src.components.broader_origin_generators")
        assert tuple(bog.PREDECISION_FEATURE_KEYS) == PREDECISION_FEATURE_KEYS

    def test_eligibility_gate(self):
        row = feature_row_for(cost_r=0.05)
        assert eligible(row, cost_complete=True) == (True, None)
        assert eligible(row, cost_complete=False) == (
            False,
            "cost_incomplete_fail_closed",
        )
        row_high = feature_row_for(cost_r=0.25)
        assert eligible(row_high, cost_complete=True) == (False, "cost_above_0p20")
        row_nan = feature_row_for(cost_r=math.nan)
        assert eligible(row_nan, cost_complete=True) == (False, "cost_not_finite")
        assert MAX_COST_R == 0.20 and MIN_EXPECTED_NET_R == 0.10


# ---------------------------------------------------------------------------
# selection: rank, minimum, abstain, occupancy — the frozen semantics
# ---------------------------------------------------------------------------


class TestSelection:
    def test_rank_and_trade(self):
        rows = [
            feature_row_for(symbol="EURUSD", key_suffix="aa"),
            feature_row_for(symbol="XAUUSD", key_suffix="bb"),
        ]
        chosen, dispositions, _ = select_market_top_abstain(
            rows, [0.2, 0.4], active={}, decision_at=T0
        )
        assert chosen is not None and chosen["symbol"] == "XAUUSD"
        assert dispositions == {"trade": 1}

    def test_minimum_predicted_net_r(self):
        rows = [feature_row_for()]
        chosen, dispositions, _ = select_market_top_abstain(
            rows, [0.0999999], active={}, decision_at=T0
        )
        assert chosen is None
        assert dispositions == {"top_below_0p10": 1}

    def test_top_limit_abstains_never_substitutes(self):
        rows = [
            feature_row_for(symbol="EURUSD", family="current_fvg_fill", key_suffix="aa"),
            feature_row_for(symbol="XAUUSD", key_suffix="bb"),
        ]
        # LIMIT candidate ranks first; MARKET second — the rule must abstain.
        chosen, dispositions, _ = select_market_top_abstain(
            rows, [0.5, 0.4], active={}, decision_at=T0
        )
        assert chosen is None
        assert dispositions == {"top_limit_abstain": 1}

    def test_tie_breaks_cost_then_key(self):
        low_cost = feature_row_for(symbol="EURUSD", key_suffix="aa", cost_r=0.04)
        high_cost = feature_row_for(symbol="XAUUSD", key_suffix="bb", cost_r=0.06)
        chosen, _, _ = select_market_top_abstain(
            [high_cost, low_cost], [0.3, 0.3], active={}, decision_at=T0
        )
        assert chosen["symbol"] == "EURUSD"  # same prediction, lower cost wins
        key_a = feature_row_for(symbol="EURUSD", key_suffix="aa", cost_r=0.05)
        key_z = feature_row_for(symbol="XAUUSD", key_suffix="zz", cost_r=0.05)
        chosen, _, _ = select_market_top_abstain(
            [key_a, key_z], [0.3, 0.3], active={}, decision_at=T0
        )
        assert chosen["symbol"] == "XAUUSD"  # same pred+cost, key desc wins

    def test_occupied_symbol_excluded_and_freed_strictly(self):
        rows = [feature_row_for(symbol="EURUSD")]
        active = {"EURUSD": T0 + timedelta(minutes=30)}
        chosen, dispositions, _ = select_market_top_abstain(
            rows, [0.5], active=active, decision_at=T0
        )
        assert chosen is None and dispositions == {"no_available_candidate": 1}
        # end == decision_at frees the symbol (strict inequality, research rule)
        assert prune_occupancy({"EURUSD": T0}, T0) == {}
        assert prune_occupancy({"EURUSD": T0 + timedelta(seconds=1)}, T0) != {}

    def test_occupancy_end_defaults_to_expiry(self):
        row = feature_row_for()
        assert occupancy_end_for_selection(row) == T0 + timedelta(minutes=120)


# ---------------------------------------------------------------------------
# closed-bar discipline through the read-only adapter
# ---------------------------------------------------------------------------


class FakeRates:
    """MT5-shaped rates rows (broker epoch seconds, UTC+7h-in-summer clock)."""

    def __init__(self, rows):
        self.rows = rows

    def __iter__(self):
        return iter(self.rows)


class FakeMT5:
    def __init__(self, rates_by_request):
        self.rates_by_request = rates_by_request
        self.order_send_calls = 0

    def copy_rates_from_pos(self, symbol, timeframe, start, count):
        rows = self.rates_by_request.get((symbol, int(timeframe)), [])
        return FakeRates(rows[-int(count):])

    def symbol_info_tick(self, symbol):
        return None


def _broker_epoch(utc_dt: datetime) -> float:
    # FTMO-Server3 wall clock == America/New_York + 7h; in August that is
    # UTC-4+7 = UTC+3.  MT5 epochs are broker wall time labeled as UTC.
    return (utc_dt + timedelta(hours=3)).timestamp()


def _m15_rate(open_utc: datetime, price: float = 1.0):
    return {
        "time": _broker_epoch(open_utc),
        "open": price,
        "high": price + 0.001,
        "low": price - 0.001,
        "close": price,
        "tick_volume": 10.0,
    }


class TestClosedBarDiscipline:
    def test_forming_bar_never_served_and_witness_attached(self):
        opens = [T0 - timedelta(minutes=15 * i) for i in range(5, 0, -1)]
        rates = [_m15_rate(open_dt) for open_dt in opens]  # last opens at T0-15m
        rates.append(_m15_rate(T0))  # the forming bar at the boundary
        adapter = ShadowReadOnlyMT5Adapter(
            FakeMT5({("EURUSD", 15): rates}), server="FTMO-Server3"
        )
        adapter.set_cycle_context(asof=T0)
        served = adapter.get_candles("EURUSD", 15, 4)
        # The forming bar (open == T0) is witness evidence only, never served.
        assert [row["time_utc"] for row in served] == [
            open_dt.isoformat() for open_dt in opens[-4:]
        ]
        from src.research_infra.completed_bar_witness import ROW_WITNESS_FIELD

        for row in served:
            witness = row[ROW_WITNESS_FIELD]
            assert witness["successor_market_values_consumed"] is False

    def test_bar_without_successor_excluded(self):
        opens = [T0 - timedelta(minutes=15 * i) for i in range(4, 0, -1)]
        rates = [_m15_rate(open_dt) for open_dt in opens]  # no bar at T0 yet
        adapter = ShadowReadOnlyMT5Adapter(
            FakeMT5({("EURUSD", 15): rates}), server="FTMO-Server3"
        )
        adapter.set_cycle_context(asof=T0)
        served = adapter.get_candles("EURUSD", 15, 4)
        # The newest closed bar (T0-15m) has no successor: excluded.
        assert [row["time_utc"] for row in served] == [
            open_dt.isoformat() for open_dt in opens[:-1]
        ]

    def test_broker_clock_conversion_is_dst_aware(self):
        winter_open = datetime(2026, 1, 12, 12, 0, tzinfo=UTC)
        # Winter: NY is UTC-5, broker wall = UTC+2.
        rate = {
            "time": (winter_open + timedelta(hours=2)).timestamp(),
            "open": 1.0,
            "high": 1.0,
            "low": 1.0,
            "close": 1.0,
            "tick_volume": 1.0,
        }
        successor = dict(rate, time=(winter_open + timedelta(hours=2, minutes=15)).timestamp())
        adapter = ShadowReadOnlyMT5Adapter(
            FakeMT5({("EURUSD", 15): [rate, successor]}), server="FTMO-Server3"
        )
        adapter.set_cycle_context(asof=winter_open + timedelta(minutes=16))
        served = adapter.get_candles("EURUSD", 15, 2)
        assert served[0]["time_utc"] == winter_open.isoformat()

    def test_h1_derived_from_m15_with_hour_witness(self):
        base = T0.replace(minute=0) - timedelta(hours=3)  # 09:00
        m15_opens = [base + timedelta(minutes=15 * i) for i in range(13)]
        # 09:00..12:00 — hour 12 has exactly one M15 bar (12:00), in progress.
        rates = [_m15_rate(open_dt, price=1.0 + i * 0.01) for i, open_dt in enumerate(m15_opens)]
        adapter = ShadowReadOnlyMT5Adapter(
            FakeMT5({("EURUSD", 15): rates}), server="FTMO-Server3"
        )
        adapter.set_cycle_context(asof=T0)
        served = adapter.get_candles("EURUSD", 16385, 2)
        # Hours 09,10 complete-and-witnessed; hour 11 witnessed by 12:00 open.
        assert [row["time_utc"] for row in served] == [
            (base + timedelta(hours=1)).isoformat(),
            (base + timedelta(hours=2)).isoformat(),
        ]
        hour_11 = served[-1]
        assert hour_11["open"] == pytest.approx(1.08)
        assert hour_11["close"] == pytest.approx(1.11)
        assert hour_11["high"] == pytest.approx(1.111)
        assert hour_11["low"] == pytest.approx(1.079)

    def test_h1_aggregation_matches_replay_derivation(self):
        pytest.importorskip("numpy")
        try:
            from src.research_infra.replay_acceleration_attempt5_typed_sparse_runner import (
                aggregate_h1_from_m15,
            )
        except Exception:
            pytest.skip("sealed replay runner not importable here")
        base = datetime(2026, 8, 12, 9, 0, tzinfo=UTC)
        rows = [
            {
                "time_utc": (base + timedelta(minutes=15 * i)).isoformat(),
                "open": 1.0 + i * 0.5,
                "high": 2.0 + i,
                "low": 0.5 - i * 0.01,
                "close": 1.5 + i,
                "volume": float(i),
            }
            for i in range(8)
        ]
        mine = aggregate_h1_rows_from_m15_rows(rows, symbol="EURUSD")
        theirs = aggregate_h1_from_m15(rows, symbol="EURUSD")
        assert len(mine) == len(theirs) == 2
        for a, b in zip(mine, theirs):
            for key in ("time_utc", "open", "high", "low", "close", "volume"):
                assert a[key] == b[key], key

    def test_mutation_surface_raises(self):
        adapter = ShadowReadOnlyMT5Adapter(
            FakeMT5({}), server="FTMO-Server3"
        )
        with pytest.raises(ShadowMutationRefused):
            adapter.order_send({"action": 1})

    def test_unregistered_server_fails_closed(self):
        with pytest.raises(Exception):
            ShadowReadOnlyMT5Adapter(FakeMT5({}), server="Some-Unknown-Server17")


# ---------------------------------------------------------------------------
# cost fail-closure
# ---------------------------------------------------------------------------


class TestCostFailClosure:
    def test_refused_quote_is_ineligible_never_defaulted(self):
        from src.research_infra.wave21_forward_shadow.shadow_costs import (
            stamp_live_pretrade_cost,
        )

        candidate = {
            "symbol": "NO_SUCH_SYMBOL_ZZZ",
            "side": "LONG",
            "entry_price": 1.0,
            "stop_loss": 0.99,
            "take_profit_1": 1.02,
            "risk_reward_ratio": 2.0,
            "candidate_id": "x",
        }
        result = stamp_live_pretrade_cost(
            candidate,
            config={"gtos_vnext_runtime": {}},  # no broker profile on purpose
            live_quote=None,
            asof_utc=T0.isoformat(),
        )
        assert result["complete"] is False
        assert result["cost_r"] is None
        assert "refusal_reason" in result

    def test_stale_live_tick_not_used(self):
        from src.research_infra.wave21_forward_shadow.shadow_costs import (
            _tick_from_live_quote,
        )

        tick, meta = _tick_from_live_quote(
            {"bid": 1.0, "ask": 1.0002, "stale_seconds": 5000.0, "time_utc": "x"},
            max_staleness_seconds=900.0,
        )
        assert tick is None and meta["live_tick_status"] == "stale"

    def test_fresh_live_tick_used(self):
        from src.research_infra.wave21_forward_shadow.shadow_costs import (
            _tick_from_live_quote,
        )

        tick, meta = _tick_from_live_quote(
            {"bid": 1.0, "ask": 1.0002, "stale_seconds": 3.0, "time_utc": "x"},
            max_staleness_seconds=900.0,
        )
        assert tick == {"bid": 1.0, "ask": 1.0002, "time_utc": "x"}
        assert meta["live_tick_status"] == "used"

    def test_inverted_bid_ask_rejected(self):
        from src.research_infra.wave21_forward_shadow.shadow_costs import (
            _tick_from_live_quote,
        )

        tick, meta = _tick_from_live_quote(
            {"bid": 1.0002, "ask": 1.0, "stale_seconds": 1.0},
            max_staleness_seconds=900.0,
        )
        assert tick is None and meta["live_tick_status"] == "invalid_bid_ask"


# ---------------------------------------------------------------------------
# namespace guard
# ---------------------------------------------------------------------------


class TestNamespaceGuard:
    def test_live_book_trees_refused(self, tmp_path):
        repo = tmp_path
        for bad in (
            repo / "pipeline_state" / "ultimate_book" / "x",
            repo / "shadow_logs" / "gtos_vnext_runtime_decisions.jsonl",
            repo / "shadow_logs" / "gtos_vnext_anything",
        ):
            with pytest.raises(NamespaceCollisionError):
                assert_namespace_safe(bad, repo_root=repo)

    def test_own_namespace_allowed_and_locked(self, tmp_path):
        namespace = tmp_path / "shadow_logs" / "funnel_shadow"
        lock = claim_namespace(namespace, repo_root=tmp_path)
        assert (namespace / "FORWARD_SHADOW_NAMESPACE.json").is_file()
        with pytest.raises(NamespaceCollisionError):
            claim_namespace(namespace, repo_root=tmp_path)  # second live pid
        release_namespace(lock)
        lock2 = claim_namespace(namespace, repo_root=tmp_path)  # re-claim ok
        release_namespace(lock2)

    def test_foreign_directory_not_adopted(self, tmp_path):
        namespace = tmp_path / "shadow_logs" / "funnel_shadow"
        namespace.mkdir(parents=True)
        (namespace / "somebody_elses_file.txt").write_text("x")
        with pytest.raises(NamespaceCollisionError):
            claim_namespace(namespace, repo_root=tmp_path)

    def test_other_lane_marker_refused(self, tmp_path):
        namespace = tmp_path / "shadow_logs" / "funnel_shadow"
        namespace.mkdir(parents=True)
        (namespace / "FORWARD_SHADOW_NAMESPACE.json").write_text(
            json.dumps({"lane_id": "some_other_lane"})
        )
        with pytest.raises(NamespaceCollisionError):
            claim_namespace(namespace, repo_root=tmp_path)


# ---------------------------------------------------------------------------
# state: resume + per-lane occupancy
# ---------------------------------------------------------------------------


def _order(key: str, symbol: str, lanes=("general",), family="displacement_continuation"):
    return WouldBeOrder(
        candidate_occurrence_key=key,
        decision_window_id=f"forward_shadow:{T0.isoformat()}",
        trading_day=T0.date().isoformat(),
        symbol=symbol,
        side="LONG",
        proposed_order_type="MARKET",
        submission_utc=T0,
        expiry_utc=T0 + timedelta(minutes=120),
        entry_price=1.1,
        stop_loss=1.09,
        take_profit_1=1.12,
        deductible_cost_r=0.038,
        predicted_net_r=0.25,
        cost_r=0.05,
        origin_family=family,
        lanes=tuple(lanes),
    )


class TestStateResume:
    def test_open_orders_and_per_lane_occupancy(self, tmp_path):
        state = ShadowState(tmp_path / "ns")
        general = _order("k1", "EURUSD", lanes=("general",))
        both = _order("k2", "XAUUSD", lanes=("general", "scoped_lsr"), family=LSR_FAMILY)
        state.write_would_be_order(general, context={"scoped_lsr_selected": False})
        state.write_would_be_order(both, context={"scoped_lsr_selected": True})
        # resolve k1 early: outcome tightens general occupancy
        state.write_order_outcome(
            general,
            {
                "final": True,
                "lifecycle_label_status": "RESOLVED_FILLED_STOP",
                "occupancy_end_utc": (T0 + timedelta(minutes=30)).isoformat(),
            },
        )
        opened = state.load_open_orders()
        assert [order.candidate_occurrence_key for order in opened] == ["k2"]
        assert opened[0].lanes == ("general", "scoped_lsr")
        assert opened[0].origin_family == LSR_FAMILY

        now = T0 + timedelta(minutes=45)
        general_occ = state.load_occupancy(now_utc=now, lane=LANE_GENERAL)
        scoped_occ = state.load_occupancy(now_utc=now, lane=LANE_SCOPED_LSR)
        # k1 resolved at +30m -> free by +45m in the general lane
        assert "EURUSD" not in general_occ
        # k2 still open in BOTH lanes until expiry
        assert general_occ["XAUUSD"] == T0 + timedelta(minutes=120)
        assert scoped_occ == {"XAUUSD": T0 + timedelta(minutes=120)}

    def test_outcome_rows_carry_scoping_fields(self, tmp_path):
        state = ShadowState(tmp_path / "ns")
        both = _order("k9", "BTCUSD", lanes=("general", "scoped_lsr"), family=LSR_FAMILY)
        state.write_order_outcome(both, {"final": True, "occupancy_end_utc": T0.isoformat()})
        row = json.loads(state.order_outcomes_path.read_text().strip())
        assert row["origin_family"] == LSR_FAMILY
        assert row["scoped_lsr_selected"] is True
        assert row["lanes"] == ["general", "scoped_lsr"]

    def test_processed_windows_idempotency(self, tmp_path):
        state = ShadowState(tmp_path / "ns")
        state.write_decision_packet(
            {"trading_day": "2026-08-12", "decision_window_id": "forward_shadow:x"}
        )
        assert state.processed_window_ids(trading_day="2026-08-12") == {
            "forward_shadow:x"
        }


# ---------------------------------------------------------------------------
# dual-lane semantics at the runner's selection layer
# ---------------------------------------------------------------------------


class TestDualLane:
    def test_lanes_can_diverge_and_scoped_ignores_general_occupancy(self):
        # General lane: XAUUSD occupied -> general picks EURUSD (displacement).
        # Scoped lane: fresh occupancy -> picks the LSR XAUUSD candidate.
        lsr = feature_row_for(symbol="XAUUSD", family=LSR_FAMILY, key_suffix="cc")
        other = feature_row_for(symbol="EURUSD", key_suffix="dd")
        general_active = {"XAUUSD": T0 + timedelta(minutes=60)}
        general_chosen, _, _ = select_market_top_abstain(
            [lsr, other], [0.5, 0.4], active=general_active, decision_at=T0
        )
        assert general_chosen["symbol"] == "EURUSD"
        scoped_chosen, _, _ = select_market_top_abstain(
            [lsr], [0.5], active={}, decision_at=T0
        )
        assert scoped_chosen["symbol"] == "XAUUSD"
        assert scoped_chosen["origin_family"] == LSR_FAMILY

    def test_scoped_lane_is_market_only_family(self):
        # liquidity_sweep_reclaim is a MARKET family: the scoped lane can never
        # abstain on order type, only on the 0.10 floor or occupancy.
        assert order_type_for_family(LSR_FAMILY) == "MARKET"


# ---------------------------------------------------------------------------
# modelled lifecycle: causal early-final vs pending vs full-horizon
# ---------------------------------------------------------------------------


class TestShadowLifecycle:
    @staticmethod
    def _order(**overrides):
        base = dict(
            candidate_occurrence_key="candidate_occurrence_" + "ab" * 32,
            decision_window_id=f"forward_shadow:{T0.isoformat()}",
            trading_day=T0.date().isoformat(),
            symbol="EURUSD",
            side="LONG",
            proposed_order_type="MARKET",
            submission_utc=T0,
            expiry_utc=T0 + timedelta(minutes=120),
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profit_1=1.1100,
            deductible_cost_r=0.038,
            predicted_net_r=0.25,
            cost_r=0.05,
            origin_family=LSR_FAMILY,
            lanes=("general", "scoped_lsr"),
        )
        base.update(overrides)
        return WouldBeOrder(**base)

    @staticmethod
    def _m1(open_dt, o, h, l, c):
        from src.components.ultimate_book.primitives import Bar

        return open_dt, Bar(o, h, l, c)

    def _resolve(self, order, bars_spec, now=None):
        from src.research_infra.wave21_forward_shadow.shadow_lifecycle import (
            resolve_would_be_order,
        )

        times = [t for t, _ in bars_spec]
        bars = [b for _, b in bars_spec]
        spreads = [0.00002] * len(bars)
        return resolve_would_be_order(
            order,
            m1_times=times,
            m1_bars=bars,
            spreads=spreads,
            now_utc=now or (times[-1] if times else T0),
        )

    def test_pending_before_any_causal_bar(self):
        order = self._order()
        spec = [self._m1(T0 - timedelta(minutes=1), 1.1, 1.1, 1.1, 1.1)]
        result = self._resolve(order, spec)
        assert result["final"] is False
        assert result["phase"] == "pending_no_causal_m1_yet"

    def test_truncated_probe_stays_pending_without_terminal(self):
        # 10 flat minutes after submission: no target, no stop -> pending.
        spec = [self._m1(T0 - timedelta(minutes=1), 1.1, 1.1005, 1.0995, 1.1)]
        for i in range(10):
            spec.append(
                self._m1(T0 + timedelta(minutes=i), 1.1, 1.1005, 1.0995, 1.1)
            )
        result = self._resolve(self._order(), spec)
        assert result["final"] is False
        assert result["phase"] == "pending_truncated_probe"

    def test_early_final_on_target_hit(self):
        spec = [self._m1(T0 - timedelta(minutes=1), 1.1, 1.1005, 1.0995, 1.1)]
        for i in range(5):
            spec.append(self._m1(T0 + timedelta(minutes=i), 1.1, 1.1005, 1.0995, 1.1))
        # target 1.1100 tagged on the sixth post-submission minute
        spec.append(self._m1(T0 + timedelta(minutes=5), 1.1, 1.1150, 1.0999, 1.1120))
        spec.append(self._m1(T0 + timedelta(minutes=6), 1.112, 1.113, 1.111, 1.112))
        result = self._resolve(self._order(), spec)
        assert result["final"] is True
        assert result["phase"] == "final_early_bar_local"
        assert result["lifecycle_label_status"] == "RESOLVED_FILLED_TARGET"
        assert result["cost_label_status"] == "COMPLETE"
        # net = gross - deductible, gross ~ +2R less spread effects
        assert result["terminal_net_r"] == pytest.approx(
            result["terminal_gross_r"] - 0.038
        )
        # occupancy freed at the causal terminal, not expiry
        assert result["occupancy_end_utc"] < (T0 + timedelta(minutes=120)).isoformat()

    def test_early_final_on_stop_hit(self):
        spec = [self._m1(T0 - timedelta(minutes=1), 1.1, 1.1005, 1.0995, 1.1)]
        spec.append(self._m1(T0, 1.1, 1.1005, 1.0995, 1.1))
        spec.append(self._m1(T0 + timedelta(minutes=1), 1.1, 1.1005, 1.0940, 1.0945))
        spec.append(self._m1(T0 + timedelta(minutes=2), 1.0945, 1.095, 1.094, 1.0945))
        result = self._resolve(self._order(), spec)
        assert result["final"] is True
        assert result["lifecycle_label_status"] == "RESOLVED_FILLED_STOP"
        assert result["terminal_gross_r"] == pytest.approx(-1.0, abs=0.05)

    def test_full_horizon_time_stop(self):
        # Flat tape through the whole 2h horizon + one bar past it.
        spec = [self._m1(T0 - timedelta(minutes=1), 1.1, 1.1005, 1.0995, 1.1)]
        for i in range(122):
            spec.append(
                self._m1(T0 + timedelta(minutes=i), 1.1, 1.1005, 1.0995, 1.1)
            )
        result = self._resolve(self._order(), spec)
        assert result["final"] is True
        assert result["phase"] == "final_full_horizon"
        assert result["lifecycle_label_status"] == "RESOLVED_FILLED_TIME_STOP"

    def test_m1_gap_censors_at_full_horizon_only(self):
        # A 3-minute hole mid-stream: truncated probe censors -> stays pending;
        # at full coverage the research resolver censors it for real.
        spec = [self._m1(T0 - timedelta(minutes=1), 1.1, 1.1005, 1.0995, 1.1)]
        for i in range(30):
            if 10 <= i < 13:
                continue
            spec.append(
                self._m1(T0 + timedelta(minutes=i), 1.1, 1.1005, 1.0995, 1.1)
            )
        pending = self._resolve(self._order(), spec)
        assert pending["final"] is False
        spec_full = [self._m1(T0 - timedelta(minutes=1), 1.1, 1.1005, 1.0995, 1.1)]
        for i in range(122):
            if 10 <= i < 13:
                continue
            spec_full.append(
                self._m1(T0 + timedelta(minutes=i), 1.1, 1.1005, 1.0995, 1.1)
            )
        final = self._resolve(self._order(), spec_full)
        assert final["final"] is True
        assert final["lifecycle_label_status"].startswith("CENSORED_")
        assert final["cost_label_status"] == "INCOMPLETE_OTHER_EXPLICIT_REASON"
