"""CONTRACT V3 (Fable 5.1, 2026-09-02): real-account floor, cross-timeframe keep-one, expiration fix, no CLI judge."""
import importlib
import io
from pathlib import Path
from types import SimpleNamespace

from tests.ultimate_book.test_f5_auto_be_dedup import _owner, _MT5, NOW

REPO = Path(__file__).resolve().parents[2]


# ------------------------------------------------------------------ constants / source pins
def test_real_floor_constants():
    ms = importlib.import_module("src.components.ultimate_book.minimal_size")
    assert ms.F5_REAL_FLATTEN_FLOOR_USD == 90_600.0
    assert ms.F5_REAL_DAILY_FLATTEN_PCT == 0.045


def test_expiration_block_uses_the_raw_module_and_expiration_mode():
    src = io.open(REPO / "src/components/execution.py", encoding="utf-8").read()
    assert '_raw = getattr(self.mt5, "_mt5", None)' in src
    assert "_tick = self._mt5.symbol_info_tick(self.symbol)" not in src
    assert "f5_native_limit_expiration" in src
    ms_src = io.open(REPO / "src/components/ultimate_book/minimal_size.py", encoding="utf-8").read()
    assert "expiration_mode" in ms_src and "SYMBOL_EXPIRATION_SPECIFIED" in ms_src


def test_adapter_has_no_cli_provider():
    import sys
    sys.path.insert(0, str(REPO))
    adapter = importlib.import_module("scripts.f5_desk.adapter")
    assert adapter.default_providers() == []


# ------------------------------------------------------------------ real-account breach verdict
class _EqMT5(_MT5):
    def __init__(self, equity):
        super().__init__()
        self._eq = equity

    def get_account_equity(self):
        return self._eq


def _owner_with_equity(tmp_path, equity, day_start=None, namespace="operator"):
    owner = _owner(tmp_path, namespace=namespace, mt5=_EqMT5(equity))
    owner.engine.broker_day_start_balance = lambda _now: day_start
    return owner


def test_real_verdict_flattens_at_the_static_floor(tmp_path):
    owner = _owner_with_equity(tmp_path, 90_500.0, day_start=93_000.0)
    v = owner._f5_real_account_breach_verdict(NOW)
    assert v["flatten"] is True and "floor" in v["reason"]


def test_real_verdict_flattens_on_real_daily_loss(tmp_path):
    owner = _owner_with_equity(tmp_path, 92_000.0, day_start=97_000.0)   # -5.15%
    v = owner._f5_real_account_breach_verdict(NOW)
    assert v["flatten"] is True and "real day" in v["reason"]


def test_real_verdict_quiet_when_healthy(tmp_path):
    owner = _owner_with_equity(tmp_path, 92_827.0, day_start=93_121.0)
    v = owner._f5_real_account_breach_verdict(NOW)
    assert v["flatten"] is False and v["reason"] is None


def test_real_verdict_none_when_equity_unreadable(tmp_path):
    owner = _owner_with_equity(tmp_path, 0.0)
    assert owner._f5_real_account_breach_verdict(NOW) is None


def test_apply_breach_uses_real_verdict_on_f5(tmp_path, monkeypatch):
    owner = _owner_with_equity(tmp_path, 92_827.0, day_start=93_121.0)
    called = {"engine": 0}
    monkeypatch.setattr(owner.engine, "breach_flatten_check", lambda *_a, **_k: called.__setitem__("engine", called["engine"] + 1) or {"flatten": True, "reason": "notional"})
    monkeypatch.setattr(owner, "_flatten_flag_present", lambda: False)
    flattened = []
    monkeypatch.setattr(owner, "_flatten_all_engines", lambda summary, reason: flattened.append(reason))
    owner._apply_breach_flatten(NOW, {})
    assert called["engine"] == 0          # the notional governor is not consulted on F5
    assert flattened == []                # healthy real account -> nothing flattened


def test_apply_breach_still_uses_engine_on_production(tmp_path, monkeypatch):
    owner = _owner_with_equity(tmp_path, 92_827.0, namespace="operator_profile")
    monkeypatch.setattr(owner.engine, "breach_flatten_check", lambda *_a, **_k: None)
    monkeypatch.setattr(owner, "_flatten_flag_present", lambda: False)
    owner._apply_breach_flatten(NOW, {})   # must not raise, must reach the engine path


# ------------------------------------------------------------------ cross-timeframe keep-one
def _pos(comment, ticket=None):
    return SimpleNamespace(comment=comment, ticket=ticket, symbol="US30.cash")


def test_cross_tf_filter_drops_other_timeframe_position(tmp_path):
    owner = _owner(tmp_path)
    owner._comment_prefix = "F5:"
    kept = owner._f5_cross_tf_filter([_pos("F5:idxrev")], "dsp_walked_high_accepted_through")
    assert kept == []                     # H4 idxrev open, M15 dsp intent -> not blocked


def test_cross_tf_filter_keeps_same_timeframe_position(tmp_path):
    owner = _owner(tmp_path)
    owner._comment_prefix = "F5:"
    p = _pos("F5:dsp_isolated_")            # 13-char stub -> dsp_isolated_spike_high (M15)
    assert owner._f5_cross_tf_filter([p], "dsp_walked_high_accepted_through") == [p]


def test_cross_tf_filter_blocks_on_unknown_sleeve_and_on_stack_cap(tmp_path):
    owner = _owner(tmp_path)
    owner._comment_prefix = "F5:"
    unknown = _pos("F5:???")
    assert owner._f5_cross_tf_filter([unknown], "dsp_walked_high_accepted_through") == [unknown]
    two = [_pos("F5:idxrev"), _pos("F5:mx_ger40_cash")]
    assert owner._f5_cross_tf_filter(two, "dsp_walked_high_accepted_through") == two


def test_cross_tf_filter_uses_ledger_ticket_first(tmp_path, monkeypatch):
    owner = _owner(tmp_path)
    owner._comment_prefix = "F5:"
    monkeypatch.setattr(owner._ledger, "sleeve_symbol_for_ticket", lambda t: ("idxrev", "US30_cash") if t == 77 else None)
    assert owner._f5_cross_tf_filter([_pos("F5:UNTAGGED", ticket=77)], "dsp_walked_high_accepted_through") == []


def test_cross_tf_filter_untouched_on_production(tmp_path):
    owner = _owner(tmp_path, namespace="operator_profile")
    owner._comment_prefix = "W7:"
    p = _pos("W7:idxrev")
    assert owner._f5_cross_tf_filter([p], "dsp_walked_high_accepted_through") == [p]


def test_sleeve_timeframes_cover_the_live_surface(tmp_path):
    owner = _owner(tmp_path)
    tfs = owner._f5_sleeve_timeframes()
    assert tfs.get("idxrev") == 16388 and tfs.get("dsp_walked_high_accepted_through") == 15
    assert tfs.get("mx_ger40_cash_d1_volume_surge_reversal") == 16408
