"""Behavioral pins for Session CH's outcome-unread lever measurements."""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[2]
DRIVER = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts"
    / "ch_lever_measurements.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("ch_lever_measurements_undertest", DRIVER)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


CH = _load()


def _epoch(day: str) -> int:
    return int(dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc).timestamp())


def _archive(tmp_path: Path, rows: list[str]) -> Path:
    path = tmp_path / "USDJPY_M15.csv"
    path.write_text("time,open,high,low,close,tick_volume,spread,real_volume\n" + "\n".join(rows) + "\n")
    Path(str(path) + ".timebase.json").write_text(json.dumps({
        "schema_version": "gtos_timebase_sidecar_v1",
        "time_column_basis": "broker_server_local",
        "broker_clock_server": "FTMO-Server3",
        "declares": path.name,
    }))
    return path


def test_bridge_numpy_float_literal_is_parsed_without_eval():
    assert CH._number("np.float64(136.242)") == 136.242
    assert CH._number("float32(2.5)") == 2.5
    with pytest.raises(ValueError):
        CH._number("__import__('os').system('false')")


def test_march_row_is_dropped_before_any_ohlc_cell_is_touched(tmp_path):
    path = _archive(tmp_path, [
        f"{_epoch('2026-02-15T00:00:00')},1,2,0.5,1.5,7,0,0",
        f"{_epoch('2026-03-15T00:00:00')},OUTCOME,OUTCOME,OUTCOME,OUTCOME,OUTCOME,0,0",
        f"{_epoch('2026-04-15T00:00:00')},2,3,1.5,2.5,8,0,0",
    ])
    got = CH.load_safe_series(path, symbol="USDJPY", timeframe=15, server="FTMO-Server3")
    assert got.rows_seen == 3
    assert len(got.bars) == 2
    assert got.rows_blackout_dropped_before_ohlc == 1
    assert all(t.date().month != 3 for t in got.times)


def test_bad_outcome_cell_outside_march_fails_loudly(tmp_path):
    path = _archive(tmp_path, [
        f"{_epoch('2026-02-15T00:00:00')},OUTCOME,2,0.5,1.5,7,0,0",
    ])
    with pytest.raises(ValueError):
        CH.load_safe_series(path, symbol="USDJPY", timeframe=15, server="FTMO-Server3")


class PoisonOutcome(dict):
    def __getitem__(self, key):
        if key in {"r_gross", "exit_utc", "mfe_r", "mae_r", "exit_reason"}:
            raise AssertionError(f"outcome field accessed: {key}")
        return super().__getitem__(key)

    def get(self, key, default=None):
        if key in {"r_gross", "exit_utc", "mfe_r", "mae_r", "exit_reason"}:
            raise AssertionError(f"outcome field accessed: {key}")
        return super().get(key, default)


def test_intent_projection_cannot_carry_or_read_stored_outcomes():
    row = PoisonOutcome({
        "sleeve": "sub_mid_dn_revert", "symbol": "USDJPY", "symbol_canonical": "USDJPY",
        "direction": 1, "sl_distance_price": 0.2, "target_dist": 0.6,
        "decision_bar_iso": "2025-01-01T00:00:00+00:00", "decision_day": "2025-01-01",
        "entry_utc": "2025-01-01T04:00:00+00:00", "timeframe": 16388,
        "r_gross": 999, "exit_utc": "poison",
    })
    out = CH._intent_projection(row)
    assert set(out) == {"sleeve", "symbol", "symbol_canonical", "direction",
                        "sl_distance_price", "target_dist", "decision_bar_iso",
                        "decision_day", "entry_utc", "timeframe"}


def test_maximum_horizon_intersection_is_inclusive_and_order_independent():
    utc = dt.timezone.utc
    assert CH.interval_hits_blackout(dt.datetime(2026, 2, 28, tzinfo=utc),
                                     dt.datetime(2026, 3, 1, tzinfo=utc))
    assert CH.interval_hits_blackout(dt.date(2026, 4, 1), dt.date(2026, 3, 31))
    assert not CH.interval_hits_blackout(dt.date(2026, 2, 1), dt.date(2026, 2, 28))


def test_entry_hour_selection_is_the_live_h4_semantics():
    selection = CH.parse_entry_hour(CH.SUBMID, known_sleeves={CH.SUBMID},
                                    timeframe_of={CH.SUBMID: CH.TF_H4})
    assert selection == {CH.SUBMID: 1}
    close = dt.datetime(2026, 2, 2, 0)
    assert CH.deferral_reason(CH.SUBMID, close, close, selection)
    assert CH.deferral_reason(CH.SUBMID, close, close + dt.timedelta(hours=1), selection) is None


def test_quiet_calibration_compresses_the_protected_span_and_counts_fills_not_days():
    days = [dt.date(2025, 1, 6), dt.date(2025, 1, 8), dt.date(2025, 1, 10),
            dt.date(2025, 1, 13), dt.date(2025, 1, 15)]
    out = CH.calibrate_silence(days, start=dt.date(2025, 1, 1), end=dt.date(2025, 2, 28),
                               censored=[(dt.date(2025, 2, 3), dt.date(2025, 2, 7))],
                               seed=7, n_fills=10)
    assert out["weekday_sessions_uncensored"] == 38
    assert out["expected_fills_per_week"] == round(10 / 38 * 5, 4)
    assert out["warn_after_silent_weekday_sessions"] <= out["alert_after_silent_weekday_sessions"]


def test_current_account_sets_are_the_commissioned_five_and_four():
    assert len(CH.CURRENT["FTMO"]) == 5 and CH.MX_BTC in CH.CURRENT["FTMO"]
    assert len(CH.CURRENT["redacted_account"]) == 4 and CH.MX_BTC not in CH.CURRENT["redacted_account"]


def test_generation_port_surface_has_no_order_method_and_can_select_only_mx_btc():
    runtime = {
        "ultimate_book_include_clean3": False,
        "ultimate_book_include_market_expansion_book": True,
        "ultimate_book_market_expansion_policy": "explicit_allowlist",
        "ultimate_book_market_expansion_sleeves": [CH.MX_BTC],
    }
    port = CH.GenerationPort(runtime, CH.InMemoryBarSource(), namespace="ch_test")
    assert CH.MX_BTC in port.active_sleeve_names()
    assert not hasattr(port._mt5, "order_send")


def test_paired_summary_separates_population_average_from_affected_rows():
    def priced(row_id, member, gross, cost, net):
        trade = SimpleNamespace(features={"row_id": row_id, "member": member}, r_gross=gross)
        return SimpleNamespace(status="priced", trade=trade, cost_r=cost, r_net=net)

    base = SimpleNamespace(priced_by_sleeve={CH.SUBMID: [
        priced("affected", "AUDJPY", 0.0, 0.3, -0.3),
        priced("unchanged", "AUDJPY", 0.0, 0.2, -0.2),
    ]})
    arm = SimpleNamespace(priced_by_sleeve={CH.SUBMID: [
        priced("affected", "AUDJPY", 1.0, 0.1, 0.9),
        priced("unchanged", "AUDJPY", 0.0, 0.2, -0.2),
    ]})
    got = CH._paired_summary(arm, base, affected_ids={"affected"})
    assert got["pooled"]["n"] == 2
    assert got["pooled"]["net_delta_r_per_trade"] == pytest.approx(0.6)
    assert got["affected_only"]["pooled"]["n"] == 1
    assert got["affected_only"]["pooled"]["net_delta_r_per_trade"] == pytest.approx(1.2)
