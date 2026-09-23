"""Ledger-builder extension tests: dedupe, era, broker-deals join, excursion
fallback, reconciliation, multi-dir bars. Fixture rows copy the REAL event /
ledger / dump shapes observed on 2026-08-24 (tickets renumbered)."""
import json
import os
from datetime import datetime, timedelta, timezone

import pytest


def _utc(y, mo, d, h, mi=0, s=0):
    return datetime(y, mo, d, h, mi, s, tzinfo=timezone.utc)


def _broker_epoch(dt_utc, offset_h=3):
    """Broker-wall MT5 epoch for an aware UTC datetime (summer: UTC+3)."""
    return int((dt_utc + timedelta(hours=offset_h)).timestamp()
               - dt_utc.utcoffset().total_seconds()
               if False else (dt_utc + timedelta(hours=offset_h)).timestamp())


CAND = "W7_BOOK::dsp_c_isospike::XAUUSD::2026-08-24::SHORT::dsp_isolated_spike_high"


def fill_event(ticket, ts, sleeve, cand=CAND, symbol="XAUUSD", risk=73.04,
               intended=75.0):
    # real schema: gtos.f5.minimal_size_event.v1 f5_fill (2026-08-24 sample)
    return {"account_login": 0, "broker_mutation": True,
            "candidate_id": cand, "decision_bar_iso": "2026-08-24T11:30:00+00:00",
            "decision_day": "2026-08-24", "event": "f5_fill",
            "f5_actual_risk_usd": risk, "f5_intended_risk_usd": intended,
            "f5_nominal_risk_usd": 170.69, "namespace": "operator",
            "schema": "gtos.f5.minimal_size_event.v1", "sleeve": sleeve,
            "symbol": symbol, "ticket": ticket, "ts_utc": ts}


def close_event(ticket, ts, net, cand=CAND, symbol="XAUUSD", risk=73.04,
                intended=75.0):
    return {"account_login": 0, "broker_mutation": False,
            "broker_net_pnl_usd": net, "epoch": 1, "event": "f5_trade_closed",
            "f5_actual_risk_usd": risk, "f5_intended_risk_usd": intended,
            "namespace": "operator", "realised_r": net / risk,
            "schema": "gtos.f5.minimal_size_event.v1",
            "sleeve": "dsp_isolated_spike_high", "symbol": symbol,
            "ticket": ticket, "ts_utc": ts}


def placed_row(ticket, cand=CAND, sleeve="dsp_isolated_spike_high",
               symbol="XAUUSD"):
    # real placed_decisions.jsonl shape
    return {"sleeve": sleeve, "symbol": symbol,
            "decision_bar_iso": "2026-08-24T11:30:00+00:00",
            "decision_day": "2026-08-24", "cluster": "dsp_c_isospike",
            "candidate_id": cand, "ticket": ticket,
            "ts": "2026-08-24T11:31:00.000000+00:00"}


# --------------------------------------------------------------------- dedupe
def test_dual_sleeve_attribution_one_row_flagged(builder):
    """178147925-shape: two f5_fill events, same ms, different sleeve."""
    events = [
        fill_event(900001, "2026-08-24T13:03:39.595742+00:00",
                   "dsp_isolated_flush_to_20low_snap"),
        fill_event(900001, "2026-08-24T13:03:39.632157+00:00",
                   "dsp_isolated_spike_high"),
        close_event(900001, "2026-08-24T13:12:07.712619+00:00", -75.91),
    ]
    rows = builder.build_rows([], events, [], [placed_row(900001)], {},
                              builder.BarStore(None))
    assert len(rows) == 1
    r = rows[0]
    assert r["sleeve"] == "dsp_isolated_spike_high"     # placement-ledger sleeve
    flags = r["join_quality"]["flags"]
    assert "duplicate_sleeve_attribution_fill_events" in flags
    assert "duplicate_fill_event_same_day" in flags
    # the kept fill event carries the candidate-tail sleeve
    assert r["later_known"]["fill"]["ticket"] == 900001


def test_reemitted_fill_keeps_earliest_day(builder):
    """177951277-shape: restart re-emission must not move the fill day."""
    cand = "W7_BOOK::liquidity_sweep::GBPJPY::2026-08-23::LONG::asia_pdl_fade"
    events = [
        fill_event(900002, "2026-08-23T22:00:25+00:00", "asia_pdl_fade",
                   cand=cand, symbol="GBPJPY", risk=74.99),
        fill_event(900002, "2026-08-24T04:13:12+00:00", "asia_pdl_fade",
                   cand=cand, symbol="GBPJPY", risk=74.99),
        fill_event(900002, "2026-08-24T06:16:20+00:00", "asia_pdl_fade",
                   cand=cand, symbol="GBPJPY", risk=74.99),
    ]
    rows = builder.build_rows([], events, [],
                              [placed_row(900002, cand=cand,
                                          sleeve="asia_pdl_fade",
                                          symbol="GBPJPY")],
                              {}, builder.BarStore(None))
    assert len(rows) == 1
    flags = rows[0]["join_quality"]["flags"]
    assert "fill_event_reemitted_on_later_day" in flags
    assert "duplicate_sleeve_attribution_fill_events" not in flags


# ------------------------------------------------------------------------ era
def test_era_field_stratifies_10_vs_75(builder):
    e10 = fill_event(900010, "2026-08-18T10:00:00+00:00", "asian_fade",
                     cand="W7_BOOK::x::EURUSD::2026-08-18::LONG::asian_fade",
                     symbol="EURUSD", risk=9.98, intended=10.0)
    e75 = fill_event(900011, "2026-08-24T10:00:00+00:00", "asian_fade",
                     cand="W7_BOOK::x::GBPUSD::2026-08-24::LONG::asian_fade",
                     symbol="GBPUSD", risk=75.0, intended=75.0)
    rows = builder.build_rows([], [e10, e75], [], [], {},
                              builder.BarStore(None))
    eras = {r["later_known"]["fill"]["ticket"]: r["era"] for r in rows}
    assert eras == {900010: 10.0, 900011: 75.0}


# -------------------------------------------------- broker-deals join + MFE
def _deals_dump(tmp_path, ticket, entry_utc, exit_utc, entry_price, exit_price,
                sl, symbol="XAUUSD", profit=-75.91, commission=-0.62,
                direction_type=1):
    """Write a dump_f5_deals.py-shaped file. Times are broker-wall epochs."""
    def ep(dt):
        return (dt + timedelta(hours=3)).timestamp()
    doc = {
        "schema": "gtos.f5.broker_deals_dump.v1", "magic": 0,
        "timebase": {"time_column_basis": "broker_wall"},
        "deals": [
            {"ticket": 5000001, "order": 6000001, "position_id": ticket,
             "entry": 0, "time": ep(entry_utc), "type": direction_type,
             "volume": 0.05, "price": entry_price, "profit": 0.0,
             "commission": commission / 2, "swap": 0.0, "fee": 0.0,
             "magic": 0, "symbol": symbol, "comment": "F5:dsp_iso"},
            {"ticket": 5000002, "order": 6000002, "position_id": ticket,
             "entry": 1, "time": ep(exit_utc), "type": 1 - direction_type,
             "volume": 0.05, "price": exit_price, "profit": profit,
             "commission": commission / 2, "swap": 0.0, "fee": 0.0,
             "magic": 0, "symbol": symbol, "comment": "[sl]"},
        ],
        "orders": [
            {"ticket": 6000001, "position_id": ticket,
             "time_setup": ep(entry_utc), "type": 1, "state": 4,
             "magic": 0, "volume_initial": 0.05,
             "price_open": entry_price, "sl": sl, "tp": 0.0,
             "symbol": symbol}],
    }
    p = tmp_path / ("deals_f5_test_%d.json" % ticket)
    p.write_text(json.dumps(doc))
    return str(p)


def _bars_csv(dirpath, symbol, start_utc, n_bars, hi, lo, base=4600.0):
    """Broker-wall M15 CSV covering [start, start + n_bars*15m)."""
    os.makedirs(str(dirpath), exist_ok=True)
    path = os.path.join(str(dirpath), "%s_M15.csv" % symbol)
    with open(path, "w") as fh:
        fh.write("time,open,high,low,close,tick_volume\n")
        for i in range(n_bars):
            t = start_utc + timedelta(minutes=15 * i) + timedelta(hours=3)
            fh.write("%s,%s,%s,%s,%s,100\n" % (
                t.strftime("%Y-%m-%d %H:%M:%S"), base, hi, lo, base))
    return path


def test_missing_trade_record_recovers_excursion_from_deals(builder, tmp_path):
    """The 20-of-23 fix: closed loser, NO trade record, NO slippage row —
    broker deals + fresh bars must still produce entry, stop and MFE/MAE."""
    t_fill = _utc(2026, 8, 24, 13, 3)
    t_exit = _utc(2026, 8, 24, 13, 12)
    events = [
        fill_event(900020, "2026-08-24T13:03:39+00:00", "dsp_isolated_spike_high"),
        close_event(900020, "2026-08-24T13:12:07+00:00", -75.91),
    ]
    dump = _deals_dump(tmp_path, 900020, t_fill, t_exit,
                       entry_price=4650.0, exit_price=4663.4, sl=4663.3)
    deals, meta = builder.load_broker_deals([dump])
    assert 900020 in deals
    bd = deals[900020]
    assert bd["entry_price"] == 4650.0
    assert bd["stop_distance_price"] == pytest.approx(13.3)
    assert bd["net_usd"] == pytest.approx(-76.53)
    bars_dir = tmp_path / "bars"
    _bars_csv(bars_dir, "XAUUSD", _utc(2026, 8, 24, 12, 0), 8,
              hi=4655.0, lo=4640.0)
    store = builder.BarStore([str(bars_dir)])
    rows = builder.build_rows([], events, [], [placed_row(900020)], {},
                              store, broker_deals=deals)
    assert len(rows) == 1
    lk = rows[0]["later_known"]
    assert lk["lifecycle"]["status"] == "CLOSED"
    flags = rows[0]["join_quality"]["flags"]
    assert "trade_record_missing_for_ticket" in flags
    assert "entry_price_from_broker_deals" in flags
    exc = lk["excursion"]
    assert exc["status"] == "ok", exc
    # SHORT from 4650: MFE = entry - low = 10.0; MAE = high - entry = 5.0
    assert exc["mfe_price"] == pytest.approx(10.0)
    assert exc["mae_price"] == pytest.approx(5.0)
    assert exc["mfe_r"] == pytest.approx(10.0 / 13.3, rel=1e-6)
    assert exc["mfe_usd"] == pytest.approx(10.0 / 13.3 * 73.04, rel=1e-6)
    assert lk["broker_truth"]["exit_price"] == 4663.4
    assert rows[0]["join_quality"]["sources_present"]["broker_deals"] is True


def test_bars_multi_dir_merge_extends_stale_tape(builder, tmp_path):
    """A fresh bars_f5 dump must EXTEND a stale tape, not be shadowed by it."""
    stale = tmp_path / "stale"
    fresh = tmp_path / "fresh"
    _bars_csv(stale, "XAUUSD", _utc(2026, 8, 21, 0, 0), 4, hi=4610.0, lo=4600.0)
    _bars_csv(fresh, "XAUUSD", _utc(2026, 8, 24, 12, 0), 4, hi=4660.0, lo=4630.0)
    store = builder.BarStore([str(stale), str(fresh)])
    bars, src = store.bars("XAUUSD", None)
    assert bars is not None
    days = {b[0].strftime("%Y-%m-%d") for b in bars}
    assert days == {"2026-08-21", "2026-08-24"}
    assert "XAUUSD_M15.csv" in src


# -------------------------------------------------------------- reconciliation
def test_reconciliation_detects_mismatch_and_reconciles(builder, tmp_path):
    t_fill = _utc(2026, 8, 24, 13, 3)
    t_exit = _utc(2026, 8, 24, 13, 12)
    events = [
        fill_event(900030, "2026-08-24T13:03:39+00:00", "dsp_isolated_spike_high"),
        close_event(900030, "2026-08-24T13:12:07+00:00", -76.53),
    ]
    dump = _deals_dump(tmp_path, 900030, t_fill, t_exit,
                       entry_price=4650.0, exit_price=4663.4, sl=4663.3)
    deals, meta = builder.load_broker_deals([dump])
    rows = builder.build_rows([], events, [], [placed_row(900030)], {},
                              builder.BarStore(None), broker_deals=deals)
    recon = builder.broker_reconciliation(deals, rows,
                                          window_utc=meta["window_utc"])
    assert recon["2026-08-24"]["status"] == "RECONCILED"
    assert recon["2026-08-24"]["ledger_net_by_era"] == {"$75": -76.53}

    # now a ledger that disagrees by $50 (close event says -26.53)
    events_bad = [
        fill_event(900030, "2026-08-24T13:03:39+00:00", "dsp_isolated_spike_high"),
        close_event(900030, "2026-08-24T13:12:07+00:00", -26.53),
    ]
    rows_bad = builder.build_rows([], events_bad, [], [placed_row(900030)], {},
                                  builder.BarStore(None), broker_deals=deals)
    recon_bad = builder.broker_reconciliation(deals, rows_bad,
                                              window_utc=meta["window_utc"])
    day = recon_bad["2026-08-24"]
    assert day["status"] == "FAILED"
    assert day["diff_usd"] == pytest.approx(-50.0)
    # and the row itself is flagged
    assert "net_pnl_mismatch_ledger_vs_broker_deals" in \
        rows_bad[0]["join_quality"]["flags"]


def test_reconciliation_day_outside_window_not_failed(builder, tmp_path):
    """A ledger close on a day the dump never covered must not read FAILED."""
    t_fill = _utc(2026, 8, 24, 13, 3)
    t_exit = _utc(2026, 8, 24, 13, 12)
    dump = _deals_dump(tmp_path, 900040, t_fill, t_exit,
                       entry_price=4650.0, exit_price=4663.4, sl=4663.3)
    deals, meta = builder.load_broker_deals([dump])
    cand_old = "W7_BOOK::x::EURUSD::2026-07-01::LONG::asian_fade"
    events = [
        fill_event(900040, "2026-08-24T13:03:39+00:00", "dsp_isolated_spike_high"),
        close_event(900040, "2026-08-24T13:12:07+00:00", -76.53),
        fill_event(900099, "2026-07-01T10:00:00+00:00", "asian_fade",
                   cand=cand_old, symbol="EURUSD"),
        close_event(900099, "2026-07-01T12:00:00+00:00", -12.0,
                    cand=cand_old, symbol="EURUSD"),
    ]
    rows = builder.build_rows([], events, [], [placed_row(900040)], {},
                              builder.BarStore(None), broker_deals=deals)
    recon = builder.broker_reconciliation(deals, rows,
                                          window_utc=meta["window_utc"])
    assert recon["2026-07-01"]["status"] == "NOT_COVERED_BY_DUMP"
    assert recon["2026-08-24"]["status"] == "RECONCILED"


# ---------------------------------------------- VPS live path + ticket ledger
def test_resolve_paths_finds_sibling_placed_decisions(builder, tmp_path):
    """Live VPS layout: placed_decisions.jsonl sits next to trade_records/, not in it."""
    book = tmp_path / "operator"
    recs = book / "trade_records"
    recs.mkdir(parents=True)
    placed = book / "placed_decisions.jsonl"
    placed.write_text("{}\n", encoding="utf-8")
    events = tmp_path / "events.jsonl"
    events.write_text("{}\n", encoding="utf-8")
    paths = builder.resolve_harvest_paths(
        dest=str(tmp_path / "no_such_dated"),
        records_dir=str(recs),
        events=[str(events)],
        vps_live=False,
        repo_root=str(tmp_path / "empty_repo"),
    )
    assert str(placed.resolve()) in [os.path.abspath(p) for p in paths["placed"]]
    assert str(events.resolve()) in [os.path.abspath(p) for p in paths["events"]]


def test_load_trade_records_skips_backup_suffixes(builder, tmp_path):
    recs = tmp_path / "trade_records"
    recs.mkdir()
    live = {"execution": {"ticket": 179221949, "broker_fill_time_utc": None},
            "trade_lifecycle_status": "closed", "marker": "live"}
    backup = {"execution": {"ticket": 179221949}, "marker": "backup"}
    (recs / "179221949.json").write_text(json.dumps(live), encoding="utf-8")
    (recs / "179221949.pre_sit_repair.json").write_text(json.dumps(backup), encoding="utf-8")
    loaded = builder.load_trade_records(str(recs))
    assert loaded[179221949]["marker"] == "live"


def test_vps_ticket_row_joins_fill_event_and_placement(builder, tmp_path):
    t_fill = _utc(2026, 8, 28, 6, 0, 48)
    t_exit = _utc(2026, 8, 28, 6, 59, 40)
    cand = "W7_BOOK::dsp_c_microbounce::XAUUSD::2026-08-28::LONG::dsp_wide_down_then_micro_bounce_then_through"
    events = [
        fill_event(179563723, "2026-08-28T06:00:49.282686+00:00",
                   "dsp_wide_down_then_micro_bounce_then_through",
                   cand=cand, symbol="XAUUSD", risk=246.79, intended=250.0),
        close_event(179563723, "2026-08-28T06:59:40+00:00", 1478.32,
                    cand=cand, symbol="XAUUSD", risk=246.79, intended=250.0),
    ]
    rec = {
        "candidate_id": cand,
        "sleeve": "dsp_wide_down_then_micro_bounce_then_through",
        "cluster": "dsp_c_microbounce",
        "symbol": "XAUUSD",
        "trade_lifecycle_status": "closed",
        "close_action": "broker_closed",
        "broker_realized_pnl": 1478.32,
        "broker_position_aggregate_profit": 1480.83,
        "broker_position_aggregate_commission": -2.51,
        "broker_position_aggregate_swap": 0.0,
        "broker_position_aggregate_fee": 0.0,
        "execution": {
            "ticket": 179563723,
            "broker_symbol": "XAUUSD",
            "broker_fill_time_utc": "2026-08-28T06:00:48+00:00",
            "broker_entry_price": 4574.55,
            "broker_exit_time_utc": "2026-08-28T06:59:40+00:00",
            "broker_exit_price": 4612.52,
            "broker_position_planned_stop_loss": 4568.38,
            "broker_position_planned_take_profit": 4612.67,
            "placed_at_utc": "2026-08-28T06:00:30.285397+00:00",
        },
    }
    dump = _deals_dump(tmp_path, 179563723, t_fill, t_exit,
                       entry_price=4574.55, exit_price=4612.52, sl=4568.38,
                       profit=1480.83, commission=-2.51)
    deals, _ = builder.load_broker_deals([dump])
    dec = [{"action": "allow",
            "generated_at_utc": "2026-08-28T06:00:00+00:00",
            "identity": {"candidate_id": cand, "symbol": "XAUUSD",
                         "broker_symbol": "XAUUSD"}}]
    rows = builder.build_vps_ticket_rows(
        dec, events, [], [placed_row(179563723, cand=cand,
                                     sleeve="dsp_wide_down_then_micro_bounce_then_through")],
        {179563723: rec}, broker_deals=deals, since="2026-08-21")
    assert len(rows) == 1
    r = rows[0]
    assert r["schema"] == "gtos.f5.outcome_ledger.vps_ticket.v1"
    assert r["ticket"] == 179563723
    src = r["join_quality"]["sources_present"]
    assert src["fill_event"] is True
    assert src["placement_ledger"] is True
    assert src["exec_decision_rows"] == 1
    assert r["later_known"]["fill"]["f5_intended_risk_usd"] == 250.0
    bt = r["later_known"]["broker_truth"]
    assert bt["time_column_basis"] == "true_utc"
    assert str(bt["entry_time_utc"]).startswith("2026-08-28T06:00:48")
    # broker wall is +3h in August; must NOT be copied onto *_utc
    assert "09:00:48" in str(bt.get("entry_time_broker_wall") or "")
    assert "09:00:48" not in str(bt["entry_time_utc"])


def test_vps_ticket_since_drops_pre_window(builder):
    cand = "W7_BOOK::x::EURUSD::2026-08-18::LONG::asian_fade"
    events = [fill_event(900010, "2026-08-18T10:00:00+00:00", "asian_fade",
                         cand=cand, symbol="EURUSD")]
    rec = {"execution": {"ticket": 900010,
                         "broker_fill_time_utc": "2026-08-18T10:00:00+00:00"},
           "candidate_id": cand, "trade_lifecycle_status": "closed"}
    rows = builder.build_vps_ticket_rows(
        [], events, [], [placed_row(900010, cand=cand, sleeve="asian_fade",
                                    symbol="EURUSD")],
        {900010: rec}, since="2026-08-21")
    assert rows == []
