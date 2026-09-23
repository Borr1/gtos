from src.judgment.apply_size import (
    CHALLENGE_LOGIN,
    CHALLENGE_NS,
    F5_INTENDED_BASELINE_USD,
    MinimalSizeScaler,
    apply_f5_scaler_to_risk_amount,
    apply_named_tilts,
    haircut_challenge_unit,
    honor_f5_scaler_risk,
    is_challenge_account,
    maybe_haircut_unit,
    physical_apply_allowed,
    unit_size_snapshot,
)
from src.judgment.compose import compose_shadow, cost_hurtful_size_tilt


def _cost_state():
    return {
        "identity": {"side": "short", "family_class": "study", "symbol": "XAUUSD", "sleeve": "dsp_two_bar_t"},
        "completeness": {"state_sufficient_for_live": False, "cost": True},
        "news": {"spine_empty": False},
        "cost": {"spread_r_of_stop": 0.10},
        "timeframes": {},
    }


def _f5_unit():
    return {
        "cluster": "book",
        "sleeve_members": ["dsp_two_bar_thrust_into_20high_continues"],
        "n_trades": 1,
        "confidence": 1.0,
        "risk_pct_per_trade": 0.0015,
        "unit_risk_pct": 0.0015,
        "sized": True,
        "reason": "ok",
    }


def test_challenge_account_and_physical_gate(monkeypatch):
    assert is_challenge_account() is False
    assert is_challenge_account(ns="operator_profile") is False
    assert is_challenge_account(ns=CHALLENGE_NS) is True
    assert is_challenge_account(login=CHALLENGE_LOGIN) is True
    assert is_challenge_account(login=CHALLENGE_LOGIN, ns="redacted_account") is False
    monkeypatch.delenv("GTOS_JEV_APPLY_LIVE", raising=False)
    assert physical_apply_allowed(login=CHALLENGE_LOGIN, ns=CHALLENGE_NS) is False
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    assert physical_apply_allowed(login=CHALLENGE_LOGIN, ns=CHALLENGE_NS) is True
    assert physical_apply_allowed(login=CHALLENGE_LOGIN, ns=CHALLENGE_NS, ticket="293332188") is False
    assert physical_apply_allowed(ns="operator_profile") is False


def test_haircut_noop_without_env_or_compose(monkeypatch):
    composed = compose_shadow(_cost_state())
    monkeypatch.delenv("GTOS_JEV_APPLY_LIVE", raising=False)
    assert maybe_haircut_unit(2.0, composed, login=CHALLENGE_LOGIN, ns=CHALLENGE_NS) == 2.0
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    assert maybe_haircut_unit(2.0, None, login=CHALLENGE_LOGIN, ns=CHALLENGE_NS) == 2.0
    # W7 ns never mutates even with compose + env
    assert maybe_haircut_unit(2.0, composed, ns="operator_profile") == 2.0
    cut = maybe_haircut_unit({"volume": 2.0}, composed, login=CHALLENGE_LOGIN, ns=CHALLENGE_NS)
    assert cut["volume"] < 2.0
    assert cut["volume"] >= 2.0 * 0.70 * 0.70
    held = maybe_haircut_unit(
        {"volume": 2.0},
        composed,
        ticket="293332188",
        login=CHALLENGE_LOGIN,
        ns=CHALLENGE_NS,
    )
    assert held["volume"] == 2.0


def test_haircut_scales_f5_risk_pct_not_just_lots(monkeypatch, tmp_path):
    """Host verdict B: F5 unit has no volume — only risk_pct_per_trade reaches the router."""
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    monkeypatch.setenv("GTOS_JEV_APPLY_RECEIPT_PATH", str(tmp_path / "apply_receipt.jsonl"))
    composed = compose_shadow(_cost_state())
    named = apply_named_tilts(composed)
    assert named["combined"] == 0.70
    unit = _f5_unit()
    cut = maybe_haircut_unit(
        unit,
        composed,
        login=CHALLENGE_LOGIN,
        ns=CHALLENGE_NS,
        symbol="XAUUSD",
        sleeve="dsp_two_bar_thrust_into_20high_continues",
    )
    assert cut["risk_pct_per_trade"] == 0.0015 * 0.70
    assert cut["unit_risk_pct"] == 0.0015 * 0.70
    assert "volume" not in cut
    assert cut["jev_combined_live_tilt"] == 0.70
    assert cut["jev_risk_pct_before"] == 0.0015
    assert cut["jev_risk_pct_after"] == 0.0015 * 0.70
    # $150 baseline * 0.70 = $105 intended if equity is $100k
    assert abs(100000.0 * cut["risk_pct_per_trade"] - 105.0) < 1e-9
    assert cut["f5_intended_risk_usd"] == 105.0
    receipt = (tmp_path / "apply_receipt.jsonl").read_text(encoding="utf-8")
    assert "risk_pct_per_trade" in receipt
    assert "0.7" in receipt
    assert "XAUUSD" in receipt


def test_haircut_w7_and_leave_orig_do_not_touch_risk(monkeypatch):
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    composed = compose_shadow(_cost_state())
    w7 = maybe_haircut_unit(_f5_unit(), composed, ns="operator_profile")
    assert w7["risk_pct_per_trade"] == 0.0015
    held = maybe_haircut_unit(
        _f5_unit(),
        composed,
        ticket="293332188",
        login=CHALLENGE_LOGIN,
        ns=CHALLENGE_NS,
    )
    assert held["risk_pct_per_trade"] == 0.0015


def test_named_tilts_cost_never_above_one():
    composed = compose_shadow(_cost_state())
    named = apply_named_tilts(composed)
    assert named["cost"] <= 1.0
    assert named["cost"] == 0.70
    assert named["apply_this_row"] is True
    held = apply_named_tilts(composed, ticket="293332188")
    assert held["flow"] == 1.0
    assert held["cost"] == 1.0
    assert held["combined"] == 1.0
    assert held["leave_orig"] is True


def test_continuous_noul_maps_cost_tilt():
    assert cost_hurtful_size_tilt(0.20, jev_noul=False) == 1.0
    assert cost_hurtful_size_tilt(0.01, jev_noul=True) == 0.70
    assert cost_hurtful_size_tilt(None, jev_noul=0.0) == 1.0
    assert cost_hurtful_size_tilt(None, jev_noul=1.0) == 0.70
    mid = cost_hurtful_size_tilt(None, jev_noul=0.5)
    assert 0.84 <= mid <= 0.86
    composed = compose_shadow(
        _cost_state(),
        {"cost_hurtful": {"noul": 0.5}},
    )
    assert composed["cost_hurtful_used"] == 0.5
    assert composed["cost_hurtful_source"] == "jev"
    assert composed["shadow_cost_tilt"] == mid


def test_haircut_challenge_unit_passes_answers(monkeypatch):
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    cut = haircut_challenge_unit(
        _f5_unit(),
        state=_cost_state(),
        answers={"cost_hurtful": {"noul": 0.5}},
        login=CHALLENGE_LOGIN,
        ns=CHALLENGE_NS,
        evaluate_jev=False,
    )
    # evaluate_jev False + answers 0.5 → cost 0.85, flow 1 (state insufficient)
    assert cut["risk_pct_per_trade"] == 0.0015 * 0.85
    assert unit_size_snapshot(cut)["risk_pct_per_trade"] == 0.0015 * 0.85


class _Hard150Scaler:
    """Host bug: always return $150 and stamp that as intended."""

    target_risk_usd = 150.0

    def __init__(self) -> None:
        self.last = {}

    def risk_usd_for(self, symbol=None, sleeve=None):
        return 150.0

    def scaled_risk_amount(self, nominal, trade_params=None):
        self.last = {"f5_intended_risk_usd": 150.0, "f5_nominal_risk_usd": nominal}
        return 150.0


def test_honor_scaler_ticket_293611741(monkeypatch):
    """Prove C: tilt 0.7467 must stamp ~$112, not hard $150."""
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    nominal = 150.0 * 0.7467
    params = {"jev_combined_live_tilt": 0.7467, "symbol": "XAUUSD"}
    broken = _Hard150Scaler()
    assert broken.scaled_risk_amount(nominal, params) == 150.0
    honored, stamp = honor_f5_scaler_risk(
        nominal,
        scaler=broken,
        trade_params=params,
        login=CHALLENGE_LOGIN,
        ns=CHALLENGE_NS,
    )
    assert abs(honored - 112.005) < 1e-9
    assert stamp["f5_intended_risk_usd"] != F5_INTENDED_BASELINE_USD
    assert abs(stamp["f5_intended_risk_usd"] - 112.005) < 1e-9
    assert stamp["f5_scaler_honor"] == "target_times_tilt"
    assert broken.last["f5_intended_risk_usd"] == stamp["f5_intended_risk_usd"]


def test_honor_scaler_uses_nominal_when_tilt_missing(monkeypatch):
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    honored, stamp = honor_f5_scaler_risk(
        112.005,
        scaler=_Hard150Scaler(),
        trade_params={"symbol": "XAUUSD"},
        login=CHALLENGE_LOGIN,
        ns=CHALLENGE_NS,
    )
    assert abs(honored - 112.005) < 1e-9
    assert stamp["f5_scaler_honor"] == "haircutted_nominal"


def test_honor_scaler_leave_orig_and_w7_stay_150(monkeypatch):
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    held, stamp = honor_f5_scaler_risk(
        112.0,
        scaler=_Hard150Scaler(),
        trade_params={"jev_combined_live_tilt": 0.7467},
        login=CHALLENGE_LOGIN,
        ns=CHALLENGE_NS,
        ticket="293332188",
    )
    assert held == 150.0
    assert stamp["f5_intended_risk_usd"] == 150.0
    w7, w7s = honor_f5_scaler_risk(
        112.0,
        scaler=_Hard150Scaler(),
        trade_params={"jev_combined_live_tilt": 0.7467},
        ns="operator_profile",
    )
    assert w7 == 150.0
    assert w7s["f5_intended_risk_usd"] == 150.0


def test_honor_scaler_off_without_apply_env(monkeypatch):
    monkeypatch.delenv("GTOS_JEV_APPLY_LIVE", raising=False)
    honored, stamp = honor_f5_scaler_risk(
        112.0,
        scaler=_Hard150Scaler(),
        trade_params={"jev_combined_live_tilt": 0.7467},
        login=CHALLENGE_LOGIN,
        ns=CHALLENGE_NS,
    )
    assert honored == 150.0
    assert stamp["f5_scaler_honor"] == "scaler_target"


def test_minimal_size_scaler_and_open_trade_hook(monkeypatch):
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    scaler = MinimalSizeScaler(
        150.0, login=CHALLENGE_LOGIN, ns=CHALLENGE_NS
    )
    params = {"jev_combined_live_tilt": 0.7467}
    assert abs(scaler.scaled_risk_amount(150.0 * 0.7467, params) - 112.005) < 1e-9
    assert scaler.last["f5_intended_risk_usd"] != 150.0

    class _Engine:
        _f5_scaler = scaler
        _runtime_namespace = CHALLENGE_NS
        mt5 = None

    hooked = apply_f5_scaler_to_risk_amount(
        150.0 * 0.7467,
        engine=_Engine(),
        trade_params=params,
        login=CHALLENGE_LOGIN,
        ns=CHALLENGE_NS,
    )
    assert abs(hooked - 112.005) < 1e-9
    assert params["f5_intended_risk_usd"] != 150.0
    class _W7:
        _f5_scaler = None

    assert apply_f5_scaler_to_risk_amount(150.0, engine=_W7(), trade_params={}) == 150.0
