"""Q1 adaptive risk-unit floor: repaired live semantics and default-off identity."""

from __future__ import annotations

import dataclasses
import math
import tempfile
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.components.ultimate_book.admission import TradeIntent
from src.components.ultimate_book.book_engine import (
    UltimateBookLiveEngine,
    effective_generation_sleeve_names,
)
from src.components.ultimate_book.book_owner import UltimateBookOwner
from src.components.ultimate_book.execution_packets import build_book_trade_params
from src.components.ultimate_book.risk_unit_floor import (
    FloorParams,
    OFF_POLICY,
    RiskUnitFloorError,
    RiskUnitFloorPolicy,
    apply_floor,
    bar_range_median_at_cutoff,
    floored_risk_distance,
    parse_risk_unit_floor,
    policy_from_args,
    project_broker_grid,
)
from tests.ultimate_book.test_book_engine import _FakeMT5, _cfg, _fixture_now
from tests.ultimate_book.test_spread_geometry_floor import _MT5WithTick


def _intent(*, sleeve="crypto", stop=1.0, target=2.0):
    return TradeIntent(
        sleeve=sleeve,
        symbol="BTCUSD" if sleeve == "crypto" else "GER40",
        direction=1,
        decision_day="2026-08-12",
        stop_dist=stop,
        target_dist=target,
    )


# ---------------------------------------------------------------- launch contract
def test_off_is_the_only_implicit_mode():
    assert policy_from_args(
        "off", None, known_sleeves={"crypto"}, effective_sleeves={"crypto"}
    ) is OFF_POLICY
    with pytest.raises(RiskUnitFloorError, match="supplied.*off"):
        policy_from_args(
            "off", "crypto", known_sleeves={"crypto"}, effective_sleeves={"crypto"}
        )
    with pytest.raises(RiskUnitFloorError, match="requires --risk-unit-floor"):
        policy_from_args(
            "shadow", None, known_sleeves={"crypto"}, effective_sleeves={"crypto"}
        )


def test_active_policy_is_validated_against_effective_tags_not_registry_union():
    known = {"crypto", "energy_agri"}
    with pytest.raises(RiskUnitFloorError, match="effective --tags"):
        policy_from_args(
            "shadow", "energy_agri", known_sleeves=known, effective_sleeves=("crypto",)
        )
    policy = policy_from_args(
        "shadow", "crypto", known_sleeves=known, effective_sleeves=("crypto",)
    )
    assert policy.mode == "shadow" and set(policy.sleeves) == {"crypto"}


def test_effective_tags_compose_include_flags_allowlists_and_admission_registry():
    disabled = {
        "ultimate_book_include_clean3": False,
        "ultimate_book_include_candidate_book": False,
        "ultimate_book_include_market_expansion_book": False,
    }
    assert effective_generation_sleeve_names(
        disabled, ("sub_xvol_pullback", "asia_pdl_fade")
    ) == set()

    candidate = {
        **disabled,
        "ultimate_book_include_candidate_book": True,
        "ultimate_book_candidate_book_sleeves": ["asia_pdl_fade"],
    }
    assert effective_generation_sleeve_names(
        candidate, ("asia_pdl_fade", "vol_compression")
    ) == {"asia_pdl_fade"}


def test_effective_tags_require_a_profile_supported_symbol():
    class _Resolver:
        def __call__(self, symbol):
            return symbol

        @staticmethod
        def supports(symbol):
            return symbol != "BTCUSD" and symbol != "DASHUSD" and symbol != "ETHUSD"

    effective = effective_generation_sleeve_names(
        {"ultimate_book_include_clean3": False},
        ("crypto", "energy_agri"),
        _Resolver(),
    )
    assert effective == {"energy_agri"}
    with pytest.raises(RiskUnitFloorError, match="effective --tags"):
        policy_from_args(
            "shadow",
            "crypto",
            known_sleeves={"crypto", "energy_agri"},
            effective_sleeves=effective,
        )


@pytest.mark.parametrize(
    "raw",
    [
        "crypto:bar=nan",
        "crypto:bar=inf",
        "crypto:cost=-inf",
        "crypto:cap=nan",
        "crypto:cap=inf",
        "crypto:cap=1",
        "crypto:target=hold",
        "crypto,",
        "crypto,crypto",
    ],
)
def test_all_numeric_and_structural_config_failures_are_launch_refusals(raw):
    with pytest.raises(RiskUnitFloorError):
        parse_risk_unit_floor(
            raw, known_sleeves={"crypto"}, effective_sleeves={"crypto"}
        )


def test_literal_target_preservation_is_the_default_and_weld_is_explicit():
    default = parse_risk_unit_floor(
        "crypto", known_sleeves={"crypto"}, effective_sleeves={"crypto"}
    )["crypto"]
    welded = parse_risk_unit_floor(
        "crypto:target=weld", known_sleeves={"crypto"}, effective_sleeves={"crypto"}
    )["crypto"]
    assert default.target_policy == "preserve"
    assert welded.target_policy == "weld"


# ---------------------------------------------------------------- instrument and arithmetic
def test_m15_instrument_is_cut_at_decision_time_not_evaluation_time():
    cutoff = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)
    first_open = cutoff - timedelta(minutes=24 * 15)
    times = [first_open + timedelta(minutes=15 * index) for index in range(40)]
    bars = []
    for index in range(40):
        # The 24 bars completed at the decision are range=2. Later bars are range=200.
        width = 2.0 if index < 24 else 200.0
        bars.append(SimpleNamespace(h=100.0 + width, l=100.0))
    value, detail = bar_range_median_at_cutoff(
        bars,
        times,
        decision_cutoff=cutoff,
    )
    assert value == pytest.approx(2.0)
    assert detail["n"] == 24
    assert detail["eligible_completed_bars"] == 24


@pytest.mark.parametrize(
    "risk0,bar24,cost,want",
    [
        (1.0, 2.0, 0.1, 2.0),
        (1.0, 0.2, 0.4, 2.0),
        (4.0, 2.0, 0.1, 4.0),
    ],
)
def test_a2_scalar_floor_identity(risk0, bar24, cost, want):
    got, _ = floored_risk_distance(
        risk0,
        bar24=bar24,
        rt_cost_price=cost,
        params=FloorParams(1.0, 5.0),
    )
    assert got == want


def test_poc_literal_target_price_survives_default_floor_through_packet_build():
    intent = _intent(sleeve="vp_euidx_pocgrav", stop=10.0, target=17.0)
    proposed, observation = apply_floor(
        intent,
        bar24=20.0,
        rt_cost_price=1.0,
        params=FloorParams(),
    )
    assert proposed.stop_dist == 20.0
    assert proposed.target_dist == 17.0
    assert observation["target_policy_effective"] == "preserve"

    unit = SimpleNamespace(
        risk_pct_per_trade=0.01,
        cluster="volprofile",
        sleeve_members=("vp_euidx_pocgrav",),
        confidence=0.3,
        n_trades=1,
    )
    account = {
        "current_equity": 100000.0,
        "balance": 100000.0,
        "account_login": 1,
        "day_start_equity_or_balance_baseline": 100000.0,
        "daily_reset_window_id": "2026-08-12",
    }
    before = build_book_trade_params(
        unit,
        intent,
        {"entry_price": 1000.0, "risk_distance": intent.stop_dist},
        account,
        profile_namespace="operator_profile",
    )
    after = build_book_trade_params(
        unit,
        proposed,
        {"entry_price": 1000.0, "risk_distance": proposed.stop_dist},
        account,
        profile_namespace="operator_profile",
    )
    assert after["take_profit_1"] == before["take_profit_1"] == pytest.approx(1017.0)


def test_explicit_weld_scales_the_target_with_the_stop():
    intent = _intent(stop=1.0, target=2.0)
    proposed, observation = apply_floor(
        intent,
        bar24=4.0,
        rt_cost_price=0.1,
        params=FloorParams(target_policy="weld"),
    )
    assert proposed.stop_dist == 4.0
    assert proposed.target_dist == 8.0
    assert observation["target_policy_effective"] == "weld"


# ---------------------------------------------------------------- broker-grid truth
def test_production_broker_grid_refuses_subminimum_instead_of_shedding():
    info = SimpleNamespace(volume_min=0.01, volume_step=0.01, volume_max=100.0)
    projection = project_broker_grid(
        0.005,
        info,
        intended_risk_usd=10.0,
        cash_risk_for_volume=lambda volume: volume * 2000.0,
    )
    assert projection["placement_allowed"] is False
    assert projection["status"] == "requested_lots_below_broker_min"


def test_f5_exact_10_dollar_projection_records_min_lot_inflation():
    """Q1 can widen a $10 F5 unit below volume_min; the explicit F5 rule keeps it but
    the exact $10 -> $20 inflation is carried, never hidden behind one filled trade."""
    info = SimpleNamespace(volume_min=0.01, volume_step=0.01, volume_max=100.0)
    projection = project_broker_grid(
        0.005,
        info,
        intended_risk_usd=10.0,
        cash_risk_for_volume=lambda volume: volume * 2000.0,
        allow_min_round_up=True,
    )
    assert projection["placement_allowed"] is True
    assert projection["status"] == "f5_min_round_up_instrumented"
    assert projection["normalized_lots"] == pytest.approx(0.01)
    assert projection["intended_risk_usd"] == pytest.approx(10.0)
    assert projection["actual_risk_usd"] == pytest.approx(20.0)
    assert projection["risk_inflation_factor"] == pytest.approx(2.0)


def test_broker_step_is_applied_from_minimum_and_shortfall_is_visible():
    info = SimpleNamespace(volume_min=0.01, volume_step=0.01, volume_max=100.0)
    projection = project_broker_grid(
        0.027,
        info,
        intended_risk_usd=27.0,
        cash_risk_for_volume=lambda volume: volume * 1000.0,
    )
    assert projection["placement_allowed"] is True
    assert projection["normalized_lots"] == pytest.approx(0.02)
    assert projection["actual_risk_usd"] == pytest.approx(20.0)
    assert projection["risk_shortfall_fraction"] == pytest.approx(7.0 / 27.0)


# ---------------------------------------------------------------- engine ordering and identity
def _intent_bytes(result):
    return [dataclasses.asdict(intent) for intent in result["intents"]]


def test_default_off_engine_is_behavior_identical_and_performs_no_q1_fetch():
    class CountingMT5(_FakeMT5):
        def __init__(self):
            super().__init__()
            self.calls = []

        def get_candles(self, symbol, timeframe, count):
            self.calls.append((symbol, timeframe, count))
            return super().get_candles(symbol, timeframe, count)

    now = _fixture_now()
    control_mt5 = CountingMT5()
    explicit_mt5 = CountingMT5()
    control = UltimateBookLiveEngine(
        _cfg(True), control_mt5, tempfile.mkdtemp()
    ).evaluate(tags=("crypto",), now_utc=now)
    explicit = UltimateBookLiveEngine(
        _cfg(True),
        explicit_mt5,
        tempfile.mkdtemp(),
        risk_unit_floor_policy=OFF_POLICY,
    ).evaluate(tags=("crypto",), now_utc=now)
    assert _intent_bytes(explicit) == _intent_bytes(control)
    assert explicit["meta"] == control["meta"]
    assert explicit_mt5.calls == control_mt5.calls
    assert "risk_unit_floor" not in explicit["generation"]


def test_preexisting_spread_refusal_happens_before_q1_and_cannot_be_rescued():
    mt5 = _MT5WithTick(spread=5000.0)
    now = _fixture_now(mt5)
    policy = RiskUnitFloorPolicy("apply", {"crypto": FloorParams()})
    result = UltimateBookLiveEngine(
        _cfg(True),
        mt5,
        tempfile.mkdtemp(),
        namespace="operator_profile",
        spread_geometry_floor={"crypto": None},
        risk_unit_floor_policy=policy,
    ).evaluate(tags=("crypto",), now_utc=now)
    assert result["n_intents"] == 0
    assert result["generation"]["spread_geometry_floor"]["refused"] >= 1
    assert "risk_unit_floor" not in result["generation"]
    assert not any(meta.get("risk_unit_floor") for meta in result["meta"])


def test_engine_apply_mode_still_hands_original_intent_to_admission():
    """APPLY is an owner routing mode, not a generation/admission mutation."""
    class M15MT5(_MT5WithTick):
        def get_candles(self, symbol, timeframe, count):
            if timeframe != 15:
                return super().get_candles(symbol, timeframe, count)
            now = _fixture_now(self)
            start = now - timedelta(minutes=15 * (count - 1))
            return [
                {
                    "time": (start + timedelta(minutes=15 * index)).isoformat(),
                    "open": 60000.0,
                    "high": 61000.0,
                    "low": 59000.0,
                    "close": 60000.0,
                    "volume": 1.0,
                }
                for index in range(count)
            ]

    mt5 = M15MT5(spread=1.0)
    now = _fixture_now(mt5)
    control = UltimateBookLiveEngine(
        _cfg(True), mt5, tempfile.mkdtemp(), namespace="operator_profile"
    ).evaluate(tags=("crypto",), now_utc=now)
    policy = RiskUnitFloorPolicy("apply", {"crypto": FloorParams()})
    applied = UltimateBookLiveEngine(
        _cfg(True),
        mt5,
        tempfile.mkdtemp(),
        namespace="operator_profile",
        risk_unit_floor_policy=policy,
    ).evaluate(tags=("crypto",), now_utc=now)
    assert _intent_bytes(applied) == _intent_bytes(control)
    assert applied["n_intents"] == control["n_intents"]
    assert applied["generation"]["risk_unit_floor"]["evaluated"] >= 1
    assert any(meta.get("risk_unit_floor") for meta in applied["meta"])


def test_shadow_instrumentation_runs_only_after_original_admission():
    class CountingMT5(_MT5WithTick):
        def __init__(self):
            super().__init__(spread=1.0)
            self.calls = []

        def get_candles(self, symbol, timeframe, count):
            self.calls.append((symbol, timeframe, count))
            return super().get_candles(symbol, timeframe, count)

    cfg = _cfg(True)
    cfg["ultimate_book_learning_rerate"] = {"crypto": 0.0}
    mt5 = CountingMT5()
    policy = RiskUnitFloorPolicy("shadow", {"crypto": FloorParams()})
    result = UltimateBookLiveEngine(
        cfg,
        mt5,
        tempfile.mkdtemp(),
        namespace="operator_profile",
        risk_unit_floor_policy=policy,
    ).evaluate(tags=("crypto",), now_utc=_fixture_now(mt5))

    assert result["n_intents"] >= 1  # source candidate existed
    assert not any(
        bool(unit.get("sized")) and float(unit.get("risk_pct_per_trade", 0) or 0) > 0
        for unit in result["decision"].would_units
    )
    assert not any(timeframe == 15 for _symbol, timeframe, _count in mt5.calls)
    assert "risk_unit_floor" not in result["generation"]
    assert not any(meta.get("risk_unit_floor") for meta in result["meta"])


# ---------------------------------------------------------------- owner apply/shadow choke point
class _Router:
    def __init__(self):
        self.placed_intents = []

    def account_state(self, *args, **kwargs):
        return {"current_equity": 100000.0, "balance": 100000.0}

    def build_trade_params(self, unit, intent, tick, account_state):
        entry = float(tick.ask)
        return {
            "entry_price": entry,
            "stop_loss": entry - float(intent.stop_dist),
            "direction": "LONG",
            "risk_pct_override": float(unit.risk_pct_per_trade) * 100.0,
        }

    def place(self, execution_engine, unit, intent, tick, account_state, balance):
        self.placed_intents.append(intent)
        return {
            "placed": False,
            "trade_state": None,
            "trade_params": self.build_trade_params(unit, intent, tick, account_state),
            "candidate_id": None,
            "reason": "test_capture_only",
        }


class _ExecutionGeometry:
    def __init__(self, *, cash_per_lot, scaler=None):
        self.cash_per_lot = float(cash_per_lot)
        self._f5_scaler = scaler
        self.active_trade = None

    def _mt5_symbol_info(self):
        return SimpleNamespace(volume_min=0.01, volume_step=0.01, volume_max=100.0)

    def _calculate_lots(self, distance, risk, **kwargs):
        return float(risk) / self.cash_per_lot

    def _broker_cash_risk_amount(self, *, volume, **kwargs):
        return float(volume) * self.cash_per_lot


def _owner_shell(policy):
    owner = object.__new__(UltimateBookOwner)
    owner._risk_unit_floor_policy = policy
    owner.router = _Router()
    return owner


def _proposal():
    return {"bar24": 4.0, "round_trip_cost_price": 0.1, "applied": True, "touched": True}


def test_shadow_route_can_project_but_cannot_replace_the_intent():
    policy = RiskUnitFloorPolicy("shadow", {"crypto": FloorParams()})
    owner = _owner_shell(policy)
    original = _intent(stop=1.0, target=2.0)
    routed, observation, block = owner._risk_unit_floor_route(
        original,
        _proposal(),
        SimpleNamespace(risk_pct_per_trade=0.02),
        SimpleNamespace(bid=99.0, ask=100.0),
        {},
        100000.0,
        _ExecutionGeometry(cash_per_lot=400.0),
    )
    assert routed is original
    assert block is None
    assert observation["route_status"] == "shadow_only"
    assert observation["broker_grid"]["placement_allowed"] is True


def test_shadow_trade_param_projection_error_still_routes_identical_original_intent():
    """A shadow-only projection failure cannot suppress or rewrite the real route."""
    policy = RiskUnitFloorPolicy("shadow", {"crypto": FloorParams()})
    owner = _owner_shell(policy)
    original = _intent(stop=1.0, target=2.0)

    class _ProjectionRaisesRouter(_Router):
        def build_trade_params(self, unit, intent, tick, account_state):
            if intent is not original:
                raise RuntimeError("proposed_geometry_unavailable")
            return super().build_trade_params(unit, intent, tick, account_state)

    owner.router = _ProjectionRaisesRouter()
    unit = SimpleNamespace(risk_pct_per_trade=0.02)
    tick = SimpleNamespace(bid=99.0, ask=100.0)
    routed, observation, block = owner._risk_unit_floor_route(
        original, _proposal(), unit, tick, {}, 100000.0,
        _ExecutionGeometry(cash_per_lot=400.0),
    )
    assert routed is original
    assert block is None
    assert observation["route_status"] == "broker_grid_refused"
    assert observation["broker_grid"]["status"].startswith("trade_params_error:RuntimeError")

    result = owner.router.place(None, unit, routed, tick, {}, 100000.0)
    assert result["reason"] == "test_capture_only"
    assert owner.router.placed_intents == [original]
    assert owner.router.placed_intents[0].stop_dist == 1.0
    assert owner.router.placed_intents[0].target_dist == 2.0


def test_apply_route_replaces_only_after_representable_broker_projection():
    policy = RiskUnitFloorPolicy("apply", {"crypto": FloorParams()})
    owner = _owner_shell(policy)
    original = _intent(stop=1.0, target=2.0)
    routed, observation, block = owner._risk_unit_floor_route(
        original,
        _proposal(),
        SimpleNamespace(risk_pct_per_trade=0.02),
        SimpleNamespace(bid=99.0, ask=100.0),
        {},
        100000.0,
        _ExecutionGeometry(cash_per_lot=400.0),
    )
    assert block is None
    assert routed is not original and routed.stop_dist == 4.0
    assert observation["route_status"] == "applied"
    assert observation["route_effect"] == "intent_replaced"


def test_apply_route_refuses_nonrepresentable_production_lot_by_name():
    policy = RiskUnitFloorPolicy("apply", {"crypto": FloorParams()})
    owner = _owner_shell(policy)
    original = _intent(stop=1.0, target=2.0)
    routed, observation, block = owner._risk_unit_floor_route(
        original,
        _proposal(),
        SimpleNamespace(risk_pct_per_trade=0.0001),  # $10 on $100k
        SimpleNamespace(bid=99.0, ask=100.0),
        {},
        100000.0,
        _ExecutionGeometry(cash_per_lot=2000.0),
    )
    assert routed is original
    assert block == "risk_unit_floor:requested_lots_below_broker_min"
    assert observation["route_status"] == "broker_grid_refused"


def test_apply_route_refuses_an_unresolved_floor_instead_of_silently_using_original():
    policy = RiskUnitFloorPolicy("apply", {"crypto": FloorParams()})
    owner = _owner_shell(policy)
    original = _intent(stop=1.0, target=2.0)
    routed, observation, block = owner._risk_unit_floor_route(
        original,
        {"bar24": None, "round_trip_cost_price": 0.1},
        SimpleNamespace(risk_pct_per_trade=0.02),
        SimpleNamespace(bid=99.0, ask=100.0),
        {},
        100000.0,
        _ExecutionGeometry(cash_per_lot=400.0),
    )
    assert routed is original
    assert observation["route_status"] == "proposal_unresolved_refused"
    assert block == "risk_unit_floor:proposal_unresolved:floor_inputs_unresolved"


def test_apply_route_f5_uses_exact_10_dollar_policy_and_instruments_inflation():
    scaler = SimpleNamespace(round_up_enabled=True, target_risk_usd=10.0)
    policy = RiskUnitFloorPolicy("apply", {"crypto": FloorParams()})
    owner = _owner_shell(policy)
    original = _intent(stop=1.0, target=2.0)
    routed, observation, block = owner._risk_unit_floor_route(
        original,
        _proposal(),
        SimpleNamespace(risk_pct_per_trade=0.02),  # nominal unit stays at production dial
        SimpleNamespace(bid=99.0, ask=100.0),
        {},
        100000.0,
        _ExecutionGeometry(cash_per_lot=2000.0, scaler=scaler),
    )
    grid = observation["broker_grid"]
    assert block is None and routed.stop_dist == 4.0
    assert grid["status"] == "f5_min_round_up_instrumented"
    assert grid["intended_risk_usd"] == pytest.approx(10.0)
    assert grid["actual_risk_usd"] == pytest.approx(20.0)


@pytest.mark.parametrize("include_proposal", [True, False], ids=("resolved", "missing"))
def test_run_cycle_apply_hands_repaired_intent_or_refuses_missing_proposal(
    tmp_path, include_proposal
):
    """The full owner sequence keeps admission on the original and replaces only the object
    handed to ``router.place`` after every pre-existing guard and cost refusal has cleared."""
    now = datetime(2026, 8, 12, 12, 16, tzinfo=timezone.utc)
    bar = "2026-08-12T12:00:00+00:00"
    original = _intent(stop=100.0, target=200.0)
    unit = {
        "sleeve_members": ["crypto"],
        "risk_pct_per_trade": 0.02,
        "unit_risk_pct": 0.02,
        "sized": True,
        "cluster": "crypto",
    }

    class _AdmittedOriginalEngine:
        config = {"ultimate_book_max_entry_lateness_frac": 0.5}

        def evaluate(self, *, now_utc=None, tags=None):
            decision = SimpleNamespace(
                runtime_effect_now=True,
                candidate_use_allowed_now=True,
                decision_status="execute_now",
                reason="unit_test",
                realized_units=[unit],
                would_units=[unit],
                governor={"new_entries_allowed": True},
            )
            meta_row = {
                "tag": "crypto",
                "symbol": "BTCUSD",
                "decision_bar_iso": bar,
                "timeframe": 15,
            }
            if include_proposal:
                meta_row["risk_unit_floor"] = {
                    "bar24": 400.0,
                    "round_trip_cost_price": 0.1,
                    "applied": True,
                    "touched": True,
                }
            return {
                "ok": True,
                "reason": "unit_test",
                "n_intents": 1,
                "runtime_effect_now": True,
                "decision": decision,
                "governor_state": SimpleNamespace(
                    equity=100000.0, realized_today_pct=0.0
                ),
                "intents": [original],
                "meta": [meta_row],
                "generation": {},
                "generation_skips": [],
            }

        @staticmethod
        def reset_window_date(current):
            return current.date().isoformat()

    geometry = _ExecutionGeometry(cash_per_lot=400.0)
    policy = RiskUnitFloorPolicy("apply", {"crypto": FloorParams()})
    owner_cfg = {
        "market": {"symbol": "BTCUSD", "mt5_symbol": "BTCUSD"},
        "instruments": {"BTCUSD": {"market": {"mt5_symbol": "BTCUSD"}}},
        "gtos_vnext_runtime": _cfg(True),
    }
    owner = UltimateBookOwner(
        owner_cfg,
        _MT5WithTick(spread=10.0),
        str(tmp_path),
        namespace="ftmo_test",
        engine_factory=lambda _symbol: geometry,
        risk_unit_floor_policy=policy,
    )
    owner.engine = _AdmittedOriginalEngine()
    owner.router = _Router()

    summary = owner.run_cycle(now_utc=now, tags=("crypto",))

    if not include_proposal:
        assert owner.router.placed_intents == []
        assert any(
            item.get("reason") == "risk_unit_floor:proposal_missing"
            for item in summary["skipped"]
            if isinstance(item, dict)
        )
        return
    assert owner.router.placed_intents, summary["skipped"]
    routed = owner.router.placed_intents[0]
    assert routed is not original
    assert routed.stop_dist == pytest.approx(400.0)
    assert routed.target_dist == pytest.approx(200.0)
    assert original.stop_dist == pytest.approx(100.0)
    assert summary["risk_unit_floor"][0]["route_status"] == "applied"
    routed_skip = next(
        item
        for item in summary["skipped"]
        if isinstance(item, dict) and item.get("reason") == "test_capture_only"
    )
    assert routed_skip["risk_unit_floor"] == summary["risk_unit_floor"][0]
    assert routed_skip["risk_unit_floor"]["broker_grid"]["normalized_lots"] == pytest.approx(5.0)


def test_launcher_persists_broker_grid_observation_without_changing_off_shape(tmp_path):
    import json

    from src.components.ultimate_book.launcher import BookLauncher

    class _LauncherMT5:
        @staticmethod
        def get_candles(_symbol, _timeframe, _count):
            head = datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc)
            return [
                {
                    "time": (head - timedelta(hours=4 * offset)).isoformat(),
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.5,
                    "volume": 100.0,
                }
                for offset in (2, 1, 0)
            ]

    class _LauncherOwner:
        base_config = {}
        _namespace = "q1_test"

        @staticmethod
        def manage_open_positions(**_kwargs):
            return {"managed": [], "adopted": [], "closed": [], "errors": []}

        @staticmethod
        def run_cycle(**_kwargs):
            return {
                "ok": True,
                "reason": "unchanged",
                "n_intents": 1,
                "runtime_effect_now": True,
                "placed": [],
                "shadow": 0,
                "skipped": [],
                "risk_unit_floor": [{
                    "route_status": "shadow_only",
                    "broker_grid": {
                        "normalized_lots": 0.01,
                        "intended_risk_usd": 10.0,
                        "actual_risk_usd": 20.0,
                    },
                }],
            }

    launcher = BookLauncher(
        _LauncherOwner(),
        _LauncherMT5(),
        lambda symbol: symbol,
        repo_root=str(tmp_path),
        tags=("crypto",),
        poll_seconds=0.01,
    )
    record = launcher.tick(now_utc=datetime(2026, 8, 12, 16, 1, tzinfo=timezone.utc))
    assert record["risk_unit_floor"][0]["broker_grid"]["actual_risk_usd"] == 20.0
    path = tmp_path / "shadow_logs" / "ultimate_book_launcher.jsonl"
    persisted = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])
    assert persisted["risk_unit_floor"] == record["risk_unit_floor"]

    off_owner = _LauncherOwner()
    off_owner.run_cycle = lambda **_kwargs: {
        "ok": True,
        "reason": "unchanged",
        "n_intents": 0,
        "runtime_effect_now": True,
        "placed": [],
        "shadow": 0,
        "skipped": [],
    }
    off_launcher = BookLauncher(
        off_owner,
        _LauncherMT5(),
        lambda symbol: symbol,
        repo_root=str(tmp_path / "off"),
        tags=("crypto",),
        poll_seconds=0.01,
    )
    off_record = off_launcher.tick(
        now_utc=datetime(2026, 8, 12, 16, 1, tzinfo=timezone.utc)
    )
    assert "risk_unit_floor" not in off_record


def test_unified_refusal_context_keeps_q1_when_trade_params_are_unavailable():
    observation = {
        "route_status": "floor_not_binding",
        "broker_grid": {"placement_allowed": True, "normalized_lots": 0.02},
    }
    context = UltimateBookOwner._runtime_learning_router_result_context({
        "trade_params": None,
        "risk_unit_floor": observation,
        "live_flow_execution": {"request_status": "not_reached"},
    })
    assert context["risk_unit_floor"] == observation
    assert context["gtos_live_flow_execution"]["request_status"] == "not_reached"


def test_run_book_help_exposes_mode_and_target_semantics():
    # test_vp_euidx intentionally prepends an archive checkout to sys.path. Drive this
    # worktree's file by absolute path so collection order cannot make us inspect an old
    # run_book module from that archive.
    import subprocess
    import sys
    from pathlib import Path

    entrypoint = Path(__file__).resolve().parents[2] / "run_book.py"
    completed = subprocess.run(
        [sys.executable, str(entrypoint), "--help"],
        cwd=entrypoint.parent,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    text = completed.stdout
    assert "--risk-unit-floor-mode" in text
    assert "{off,shadow,apply}" in text
    assert "target=preserve" in text


def _host_f5_wrapper_or_skip():
    """Return the live F5 wrapper path, or SKIP where it legitimately cannot exist.

    ENVIRONMENT (class c), classified 2026-08-25: `run_f5_ftmo.ps1` is HOST-only —
    uncommitted VPS bytes living BESIDE the repo checkout (the repo's parent
    directory, hence parents[3]), by design never committed (judgment-architecture
    2026-08-24; measured running argv docs/audits/fable-20260824/AUDIT-FINDINGS.md
    "The books themselves" table). It is not a sparse-checkout absence: the path is
    untracked everywhere, and /Users/borr/GTOSActive/repo was checked 2026-08-25 —
    not there either. On the VPS this helper returns the real file and every assert
    below still runs; on the research Mac the tests SKIP with this named reason.
    """
    from pathlib import Path

    wrapper = Path(__file__).resolve().parents[3] / "run_f5_ftmo.ps1"
    if not wrapper.is_file():
        pytest.skip(
            f"requires_data({wrapper}): live F5 wrapper is uncommitted host-only "
            "bytes beside the repo on the VPS; absent on the research Mac by design"
        )
    return wrapper


def test_live_f5_wrapper_selects_shadow_from_the_exact_launched_tag_variable():
    from pathlib import Path

    # Committed-tree half of the protection: runs UNCONDITIONALLY on every machine.
    repo_supervisor = Path("scripts/run_book_supervisor.ps1").read_text(encoding="utf-8")
    assert "--risk-unit-floor-mode" not in repo_supervisor
    # Host-only half: the wrapper file exists only beside the VPS checkout.
    wrapper = _host_f5_wrapper_or_skip()
    text = wrapper.read_text(encoding="utf-8")
    assert "--risk-unit-floor-mode apply" not in text
    assert "--risk-unit-floor-mode shadow" in text
    assert "--tags $F5_TAGS" in text
    assert "--risk-unit-floor $F5_TAGS" in text
    assert "--event-clock-shadow" in text


def test_live_f5_wrapper_clears_inherited_activation_critical_environment():
    # ENVIRONMENT (class c) 2026-08-25: host-only wrapper — see _host_f5_wrapper_or_skip.
    wrapper = _host_f5_wrapper_or_skip()
    text = wrapper.read_text(encoding="utf-8")
    launch_index = text.index("& $PY run_book.py")
    for variable in (
        "GTOS_PROFILE",
        "GTOS_UB_DERISK_MODE",
        "GTOS_MT5_TERMINAL_PATH",
    ):
        variable_index = text.index(f'"{variable}"')
        assert variable_index < launch_index
    assert 'Remove-Item -Path ("Env:" + $CriticalEnvName)' in text
