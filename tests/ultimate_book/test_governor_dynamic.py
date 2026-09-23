"""Challenge governor: a score is not a protect reason, and our caps are not anchors."""

from src.components.gtos_vnext_runtime import evaluate_vnext_prop_safe_selector
from src.components.ultimate_book.admission import (
    GovernorLimits,
    GovernorState,
    _challenge_governor,
)


def _below():
    return GovernorState(
        equity=98000.0,
        high_water=100000.0,
        realized_today_pct=-0.01,
        open_risk_pct=0.002,
        max_dd_reference_equity=100000.0,
    )


def test_profit_score_below_reference_does_not_stamp_protect(monkeypatch):
    monkeypatch.setenv("GTOS_NAMESPACE", "operator")
    seen = {}

    def fake_score(role, instructions, facts):
        seen[role] = dict(facts)
        if role == "profit_target_mult":
            return 0.5
        return None

    monkeypatch.setattr(
        "src.components.ultimate_book.admission._admit_score",
        fake_score,
    )
    monkeypatch.setattr(
        "src.components.ultimate_book.admission._pack",
        lambda facts, questions: {},
    )
    decision = _challenge_governor(
        _below(),
        GovernorLimits(profit_target_pct=0.10, profit_target_derisk_mult=0.25),
    )
    assert decision.reason != "profit_target_protect_derisk"
    assert decision.size_cap_multiplier == 1.0
    assert decision.allow_new_entries is True
    card = seen["profit_target_mult"]
    assert "recorded_profit_target_derisk_mult" not in card
    assert "recorded_gross_open_risk_cap_pct" not in card
    assert "recorded_soft_daily_stop_pct" not in card
    assert card["recorded_hard_daily_limit_pct"] == 0.05
    assert card["recorded_max_dd_limit_pct"] == 0.10
    assert card["gain"] < 0


def test_protect_choice_applies_the_multiplier(monkeypatch):
    monkeypatch.setenv("GTOS_NAMESPACE", "operator")

    def fake_score(role, instructions, facts):
        if role == "profit_target_mult":
            return 0.5
        return None

    monkeypatch.setattr(
        "src.components.ultimate_book.admission._admit_score",
        fake_score,
    )
    monkeypatch.setattr(
        "src.components.ultimate_book.admission._pack",
        lambda facts, questions: {"profit_target_protect": "protect_derisk"},
    )
    decision = _challenge_governor(
        _below(),
        GovernorLimits(profit_target_pct=0.10, profit_target_derisk_mult=0.25),
    )
    assert decision.reason == "profit_target_protect_derisk"
    assert decision.size_cap_multiplier == 0.5
    assert decision.allow_new_entries is True


def test_empty_protect_choice_does_not_restore_the_shrink(monkeypatch):
    monkeypatch.setenv("GTOS_NAMESPACE", "operator")
    monkeypatch.setattr(
        "src.components.ultimate_book.admission._admit_score",
        lambda role, instructions, facts: None,
    )
    monkeypatch.setattr(
        "src.components.ultimate_book.admission._pack",
        lambda facts, questions: {},
    )
    decision = _challenge_governor(
        _below(),
        GovernorLimits(profit_target_pct=0.10, profit_target_derisk_mult=0.25),
    )
    assert decision.size_cap_multiplier == 1.0
    assert decision.reason == "ok"
    assert decision.available_gross_risk_pct is None


def _selector_decision():
    from src.components.gtos_vnext_runtime import GTOSVNextRuntimeDecision

    return GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD", "route_session": "ny_kz"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="overlay_room",
        evidence={"matched_rows": 1, "metrics": {}},
    )


def _selector_account():
    return {
        "initial_balance": 100000.0,
        "current_balance": 100000.0,
        "current_equity": 100000.0,
        "risk_base_amount": 100000.0,
        "day_start_equity_or_balance_baseline": 100000.0,
        "open_position_risk_pct": 0.0,
        "pending_order_risk_pct": 0.0,
        "new_trade_sl_risk_pct": 1.0,
        "spread_slippage_commission_buffer_pct": 0.0,
        "day_trade_count": 0,
        "session_trade_count": 0,
        "symbol_day_trade_count": 0,
        "symbol_session_trade_count": 0,
        "simultaneous_candidate_count": 1,
    }


def _selector_cfg():
    return {
        "risk": {"max_daily_loss_pct": 4.0},
        "gtos_vnext_runtime": {
            "prop_safe_selector_enabled": True,
            "prop_safe_selector_apply_to_execution": True,
            "prop_safe_selector_external_daily_loss_limit_pct": 5.0,
            "prop_safe_selector_external_overall_max_loss_pct": 10.0,
            "prop_safe_selector_internal_daily_overlay_enabled": True,
            "prop_safe_selector_internal_overlay_applies_to_budget": True,
            "prop_safe_selector_internal_daily_overlay_pct": 4.0,
            "prop_safe_selector_spread_slippage_commission_buffer_pct": 0.10,
            "prop_safe_selector_min_reduced_risk_pct": 0.25,
            "prop_safe_selector_daily_reset_timezone_offset_hours": 3.0,
            "prop_safe_selector_malaysia_timezone_offset_hours": 8.0,
        },
    }


_RULES = {
    "gtos_vnext_runtime": {
        "prop_safe_selector_initial_balance": 100000.0,
        "prop_safe_selector_external_daily_loss_limit_pct": 5.0,
        "prop_safe_selector_external_overall_max_loss_pct": 10.0,
    }
}


def _chair(monkeypatch, day):
    monkeypatch.setattr(
        "src.judgment.equity_frame.read_chair_day_start",
        lambda *_args, **_kwargs: dict(day),
    )


def test_room_uses_the_chair_and_the_size_hop(monkeypatch):
    monkeypatch.setenv("GTOS_NAMESPACE", "operator")
    monkeypatch.setattr(
        "src.components.ultimate_book.admission._admit_score",
        lambda role, instructions, facts: None,
    )
    monkeypatch.setattr(
        "src.components.ultimate_book.admission._pack",
        lambda facts, questions: {},
    )
    chair = {
        "day_start_balance": 93670.92,
        "day_start_equity": 93678.44,
        "day_start_reset_utc": "2026-09-21T22:00:00Z",
        "day_start_source": "chair_day_baseline",
        "day_start_equity_source": "chair_day_baseline",
    }
    _chair(monkeypatch, chair)
    from src.judgment.apply_size import binding_room_usd
    from src.components.ultimate_book.admission import (
        GovernorLimits,
        _challenge_binding_facts,
        evaluate_governor,
    )

    hop = {
        "login": 0,
        "equity": 93522.57,
        "open_risk_usd": 0.0,
        "positions_total": 0,
        "initial_balance": 100000.0,
        "overall_loss_pct": 10.0,
        "daily_percent_external": 5.0,
        "day_start_balance": 1.0,
        "day_start_equity": 1.0,
        "day_start_reset_utc": "not-the-chair",
    }
    size_facts = dict(hop)
    size_facts["day_start_balance"] = chair["day_start_balance"]
    size_facts["day_start_equity"] = chair["day_start_equity"]
    usd, read = binding_room_usd(size_facts, size_facts["equity"])
    state = _below()
    facts = _challenge_binding_facts(state, _RULES, hop)
    got = evaluate_governor(
        state,
        limits=GovernorLimits(profit_target_pct=0.10),
        rules=_RULES,
        hop_facts=hop,
    )
    assert read == "bound"
    assert facts["equity"] == 93522.57
    assert facts["open_risk_usd"] == 0.0
    assert facts["day_start_equity"] == 93678.44
    assert facts["day_start_reset_utc"] == "2026-09-21T22:00:00Z"
    assert facts["day_start_source"] == "chair_day_baseline"
    assert facts["initial_balance"] == 100000.0
    assert "max_dd_reference_equity" not in facts
    assert facts["equity"] != state.equity
    gov_usd, gov_read = binding_room_usd(facts, facts["equity"])
    assert gov_read == read
    assert gov_usd == usd
    assert got.available_gross_risk_pct == round(usd / facts["equity"], 6)
    drifted = _below()
    drifted.equity = 50000.0
    drifted.realized_today_pct = -0.2
    drifted.open_risk_pct = 0.5
    drifted.max_dd_reference_equity = 50000.0
    again = _challenge_binding_facts(drifted, _RULES, hop)
    assert again["day_start_reset_utc"] == "2026-09-21T22:00:00Z"
    assert again["equity"] == 93522.57
    assert binding_room_usd(again, again["equity"])[0] == usd


def test_adapter_login_is_the_attached_account():
    from src.components.ultimate_book.admission import _adapter_login

    class Info:
        login = 0

    class Adapter:
        def account_info(self):
            return Info()

    assert _adapter_login(Adapter()) == 0
    assert _adapter_login(type("A", (), {"get_account_login": lambda self: 0})()) == 0


def test_missing_chair_or_initial_leaves_the_room_unset(monkeypatch):
    monkeypatch.setenv("GTOS_NAMESPACE", "operator")
    _chair(monkeypatch, {})
    from src.components.ultimate_book.admission import GovernorLimits, _challenge_binding_room

    hop = {
        "equity": 93522.57,
        "open_risk_usd": 0.0,
        "positions_total": 0,
        "initial_balance": 100000.0,
        "overall_loss_pct": 10.0,
        "daily_percent_external": 5.0,
    }
    limits = GovernorLimits(hard_daily_limit_pct=0.05, max_dd_limit_pct=0.10)
    room, read, usd = _challenge_binding_room(_below(), limits, _RULES, hop)
    assert room is None and usd is None and read == "unset"
    _chair(monkeypatch, {
        "day_start_balance": 100000.0,
        "day_start_equity": 100000.0,
        "day_start_reset_utc": "2026-09-21T22:00:00Z",
    })
    bare = {"equity": 93522.57, "open_risk_usd": 0.0, "positions_total": 0}
    room, read, usd = _challenge_binding_room(_below(), limits, {}, bare)
    assert room is None and usd is None and read == "unset"
    room, read, usd = _challenge_binding_room(_below(), limits, _RULES, None)
    assert room is None and usd is None and read == "unset"
    foreign = dict(hop)
    foreign["login"] = 0
    room, read, usd = _challenge_binding_room(_below(), limits, _RULES, foreign)
    assert room is None and usd is None and read == "unset"


def test_challenge_unset_day_start_does_not_reconstruct(monkeypatch):
    from datetime import datetime, timezone

    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine

    monkeypatch.setattr(
        "src.judgment.equity_frame.read_chair_day_start",
        lambda *_a, **_k: {"day_start_balance": None, "day_start_equity": None},
    )
    engine = object.__new__(UltimateBookLiveEngine)
    engine._namespace = "operator"
    engine._f5_ledger = object()
    engine._mt5 = type("M", (), {
        "get_account_login": lambda self: 0,
        "get_account_balance": lambda self: 93522.57,
    })()
    called = {"n": 0}

    def reconstruct(*_a, **_k):
        called["n"] += 1
        return 999.0

    engine._governor = type("G", (), {
        "_reset_rule": "ftmo",
        "_effective_offset_h": lambda self, now: 3.0,
        "reconstruct_day_start_balance": staticmethod(reconstruct),
    })()
    now = datetime(2026, 9, 23, 6, 15, tzinfo=timezone.utc)
    assert engine._f5_day_start_balance(now) is None
    assert engine.broker_day_start_balance(now) is None
    assert called["n"] == 0
    engine._lane_weight_controller = None
    engine._generate_intents = lambda tags, at: ([], {})
    engine._equity = lambda: 93522.57
    engine._deal_capable = lambda: False
    engine._last_generation_telemetry = {}
    engine._last_generation_skips = []
    engine._last_generation_terminals = []
    engine._last_lane_weights_snapshot = {}
    out = engine.evaluate(now_utc=now)
    assert out["reason"] == "day_baseline_unavailable"
    assert out["governor_state"] is None
    assert out["decision"] is None
    assert engine.compute_governor_state(now) is None


def test_challenge_day_start_is_only_the_shared_read(monkeypatch):
    from datetime import datetime, timezone

    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine

    monkeypatch.setattr(
        "src.judgment.equity_frame.read_chair_day_start",
        lambda *_a, **_k: {"day_start_balance": 93670.92},
    )
    engine = object.__new__(UltimateBookLiveEngine)
    engine._namespace = "operator"
    engine._f5_ledger = object()
    engine._mt5 = type("M", (), {"get_account_login": lambda self: 0})()

    def reconstruct(*_a, **_k):
        raise AssertionError("reconstruct")

    engine._governor = type("G", (), {
        "_reset_rule": "ftmo",
        "_effective_offset_h": lambda self, now: 3.0,
        "reconstruct_day_start_balance": staticmethod(reconstruct),
    })()
    now = datetime(2026, 9, 23, 6, 15, tzinfo=timezone.utc)
    assert engine._f5_day_start_balance(now) == 93670.92
    assert engine.broker_day_start_balance(now) == 93670.92


def test_measured_card_does_not_take_a_file_equity():
    from src.judgment.remaining_ifs_tree import measured_account_card

    assert measured_account_card({
        "account": {"present": True, "equity": 96520.44, "login": 0},
    }) is None
    assert measured_account_card(None) is None
    card = measured_account_card({
        "account": {"present": True, "equity": 93522.57, "login": 0, "balance": 93522.57},
    })
    assert card["equity"] == 93522.57
    assert int(card["login"]) == 0


def test_unset_room_is_not_read_as_no_limit(monkeypatch):
    monkeypatch.setenv("GTOS_NAMESPACE", "operator")
    monkeypatch.setattr(
        "src.components.ultimate_book.admission._admit_score",
        lambda role, instructions, facts: None,
    )
    monkeypatch.setattr(
        "src.components.ultimate_book.admission._pack",
        lambda facts, questions: {},
    )
    _chair(monkeypatch, {})
    decision = _challenge_governor(_below(), GovernorLimits())
    assert decision.allow_new_entries is True
    assert decision.available_gross_risk_pct is None
    # A released block writes zero room. It does not drop the field.
    assert max(0.0, float(decision.available_gross_risk_pct or 0.0)) == 0.0
    try:
        headroom = float({"available_gross_risk_pct": None}.get("available_gross_risk_pct"))
    except (TypeError, ValueError):
        headroom = None
    assert headroom is None
    from src.judgment.apply_size import honor_f5_scaler_risk

    honored, stamp = honor_f5_scaler_risk(
        100.0,
        trade_params={"equity": 98000.0},
        login=0,
        ns="operator",
    )
    assert honored is None
    assert stamp["binding_room_usd"] is None
    assert stamp["f5_scaler_honor"] == "size_not_decided"


def test_typed_overlay_is_not_the_budget(monkeypatch):
    asked = []
    monkeypatch.setattr(
        "src.judgment.nineteen.score",
        lambda *args, **kwargs: asked.append(kwargs.get("question_id")),
    )
    selector = evaluate_vnext_prop_safe_selector(
        decision=_selector_decision(),
        config=_selector_cfg(),
        current_risk_pct=1.0,
        account_state=_selector_account(),
        current_time_utc="2026-05-25T12:00:00+00:00",
    )
    assert "internal_daily_overlay_room" not in asked
    assert selector.external_rule_projection["binding_budget_name"] != "gtos_internal_daily_overlay"
    assert selector.external_rule_projection["binding_room_usd"] == 5000.0
    assert selector.external_rule_projection["binding_room_read"] == "bound"
    assert selector.internal_overlay_projection["source"] == "binding_room_usd"
    assert selector.internal_overlay_projection["daily_loss_limit_pct"] is None
    assert selector.internal_overlay_projection["applies_to_selector_budget"] is False
    assert selector.action == "ALLOW"
    assert selector.external_rule_projection["rule_sources"]["daily_loss_limit_pct"] == (
        "account_rule_typed"
    )


def _governor_state(**overrides):
    from src.components.ultimate_book.admission import GovernorState

    fields = dict(
        equity=93522.57,
        high_water=100000.0,
        realized_today_pct=-0.01,
        open_risk_pct=0.0,
        max_dd_reference_equity=100000.0,
    )
    fields.update(overrides)
    return GovernorState(**fields)


def test_challenge_skips_the_unused_joint_gross_cap_ask(monkeypatch):
    asked = []

    def spy(*args, **_kwargs):
        asked.append(args[0] if args else None)
        return 0.00384

    monkeypatch.setattr(
        "src.components.ultimate_book.book_engine._fraction_score",
        spy,
    )
    from src.components.ultimate_book.admission import GovernorLimits
    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine

    class Book:
        _namespace = "operator"

    base = GovernorLimits()
    got = UltimateBookLiveEngine._joint_daily_limits(Book(), base, _governor_state())
    assert asked == []
    assert base.gross_open_risk_cap_pct == 0.04
    assert got.gross_open_risk_cap_pct is None
    assert got.hard_daily_limit_pct == 0.05
    assert got.max_dd_limit_pct == 0.10
    assert got.profit_target_pct == base.profit_target_pct


def test_other_books_still_tighten_the_recorded_gross_cap(monkeypatch):
    asked = []

    def spy(*args, **_kwargs):
        asked.append(args[0] if args else None)
        return 0.00384

    monkeypatch.setattr(
        "src.components.ultimate_book.book_engine._fraction_score",
        spy,
    )
    from src.components.ultimate_book.admission import GovernorLimits
    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine

    class Book:
        _namespace = "research_book"

    base = GovernorLimits()
    flat = UltimateBookLiveEngine._joint_daily_limits(
        Book(), base, _governor_state(realized_today_pct=0.0),
    )
    got = UltimateBookLiveEngine._joint_daily_limits(
        Book(), base, _governor_state(realized_today_pct=-0.029),
    )
    hard = float(base.hard_daily_limit_pct)
    expected = min(base.gross_open_risk_cap_pct, max(0.0, hard - 0.029 - 0.005))
    assert asked == []
    assert flat.gross_open_risk_cap_pct == base.gross_open_risk_cap_pct
    assert abs(got.gross_open_risk_cap_pct - expected) < 1e-9
    assert got.hard_daily_limit_pct == 0.05
    assert got.max_dd_limit_pct == 0.10


def test_admit_and_size_does_not_copy_planted_caps(monkeypatch):
    monkeypatch.setenv("GTOS_NAMESPACE", "operator")
    monkeypatch.setattr(
        "src.components.ultimate_book.admission._admit_score",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "src.components.ultimate_book.admission._pack",
        lambda *_args, **_kwargs: {},
    )
    seen = {}

    def spy(_intents, **kwargs):
        seen["card"] = kwargs.get("equity_card")
        return []

    monkeypatch.setattr(
        "src.components.ultimate_book.admission.size_correlated_units",
        spy,
    )
    from src.components.ultimate_book.admission import (
        DEFAULT_PROFILE,
        GovernorLimits,
        _PLANTED_GOVERNOR_FACTS,
        admit_and_size,
    )

    admit_and_size(
        [],
        _below(),
        profile=DEFAULT_PROFILE,
        limits=GovernorLimits(profit_target_pct=0.10),
        room_facts={"recorded_gross_open_risk_cap_pct": 0.04, "initial_balance": 100000.0},
    )
    card = seen["card"]
    assert card["recorded_hard_daily_limit_pct"] == 0.05
    assert card["recorded_max_dd_limit_pct"] == 0.10
    assert card["recorded_profit_target_pct"] == 0.10
    assert card["initial_balance"] == 100000.0
    for key in _PLANTED_GOVERNOR_FACTS:
        assert key not in card


def test_risk_units_drop_planted_caps(monkeypatch):
    captured = {}

    def spy(facts, _questions):
        captured["facts"] = facts
        return {}

    monkeypatch.setattr("src.components.ultimate_book.admission._pack", spy)
    from src.components.ultimate_book.admission import (
        _PLANTED_GOVERNOR_FACTS,
        _challenge_risk_units,
    )

    class Intent:
        symbol = "XAUUSD"
        stop_dist = 1.0
        direction = 1
        intra_size = 1.0
        sleeve = "metals_core"
        details = {}
        ll_impulse = None
        decision_hour = None
        vr = None

    class Spec:
        confidence = 1.0

    card = {key: 0.04 for key in _PLANTED_GOVERNOR_FACTS}
    card["recorded_hard_daily_limit_pct"] = 0.05
    card["equity"] = 93522.57
    _challenge_risk_units(
        [("2026-09-23", "metals", [Intent()], ("metals_core",), 1)],
        registry={"metals_core": Spec()},
        base_risk=0.0075,
        equity_card=card,
        room=None,
        sqrt_n_pooling=False,
        kelly_lite=False,
        kelly_conservative=False,
        n_active_by_day={},
        stress_derisk=False,
        stress_state=None,
        overlays=False,
    )
    facts = captured["facts"]
    assert facts["recorded_hard_daily_limit_pct"] == 0.05
    for key in _PLANTED_GOVERNOR_FACTS:
        assert key not in facts
