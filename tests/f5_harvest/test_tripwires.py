"""Each tripwire fires and holds on synthetic inputs; delivery reuses the
notification-queue enqueue-row schema; dd_distance reuses the governor's
firm-rule arithmetic (5% of initial balance, 00:00 Europe/Prague reset)."""
import json
import os
from datetime import datetime, timedelta, timezone

import pytest

DAY = "2026-08-24"


def _utc(y, mo, d, h, mi=0):
    return datetime(y, mo, d, h, mi, tzinfo=timezone.utc)


def _wall_epoch(dt_utc, off=3):
    return (dt_utc + timedelta(hours=off)).timestamp()


def _write_jsonl(path, rows):
    os.makedirs(os.path.dirname(str(path)), exist_ok=True)
    with open(str(path), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _inputs(events=None, launcher=None, deal_dumps=None, judge_files=None,
            sidecars=None, breach_files=None, ledger=None):
    return {"events": events, "launcher": launcher,
            "deal_dumps": deal_dumps or [],
            "judge_files": judge_files or [], "sidecars": sidecars or [],
            "breach_counter_files": breach_files or [], "ledger": ledger}


# ------------------------------------------------------------------ (a) day_net
def _deals_doc(day_utc_hour_nets):
    deals = []
    for i, (hour, net) in enumerate(day_utc_hour_nets):
        deals.append({"ticket": 7000 + i, "position_id": 8000 + i, "entry": 1,
                      "time": _wall_epoch(_utc(2026, 8, 24, hour)), "type": 0,
                      "price": 1.0, "profit": net, "commission": 0.0,
                      "swap": 0.0, "fee": 0.0, "magic": 0,
                      "symbol": "EURUSD"})
    return {"schema": "gtos.f5.broker_deals_dump.v1", "deals": deals, "orders": []}


def test_day_net_fires_below_limit_from_dump(tripwires, tmp_path):
    p = tmp_path / "deals_f5_test.json"
    p.write_text(json.dumps(_deals_doc([(10, -400.0), (12, -700.0)])))
    w = tripwires.wire_day_net(DAY, _inputs(deal_dumps=[str(p)]), None, -1000.0)
    assert w["fired"] is True
    assert w["day_net_usd"] == pytest.approx(-1100.0)
    assert "-$1100.00" in w["message"]


def test_day_net_holds_above_limit(tripwires, tmp_path):
    p = tmp_path / "deals_f5_test.json"
    p.write_text(json.dumps(_deals_doc([(10, -400.0), (12, -500.0)])))
    w = tripwires.wire_day_net(DAY, _inputs(deal_dumps=[str(p)]), None, -1000.0)
    assert w["fired"] is False


def test_day_net_falls_back_to_close_events(tripwires, tmp_path):
    ev = tmp_path / "events.jsonl"
    _write_jsonl(ev, [
        {"event": "f5_trade_closed", "ticket": 1, "broker_net_pnl_usd": -1200.5,
         "ts_utc": "2026-08-24T13:00:00+00:00"},
        {"event": "f5_trade_closed", "ticket": 2, "broker_net_pnl_usd": 100.0,
         "ts_utc": "2026-08-23T13:00:00+00:00"},   # other day: excluded
    ])
    w = tripwires.wire_day_net(DAY, _inputs(events=str(ev)), None, -1000.0)
    assert w["source"] == "f5_trade_closed_events"
    assert w["day_net_usd"] == pytest.approx(-1200.5)
    assert w["fired"] is True


# -------------------------------------------------------------- (b) dd_distance
class FakeMT5:
    """history_deals_get + account_info, deal times broker-wall epochs."""
    class _Acct:
        def __init__(self, balance, equity):
            self.balance = balance
            self.equity = equity

    class _Deal:
        def __init__(self, time_epoch, profit, dtype=0):
            self.time = time_epoch
            self.profit = profit
            self.commission = 0.0
            self.swap = 0.0
            self.fee = 0.0
            self.type = dtype
            self.magic = 0

    def __init__(self, balance, equity, deals):
        self._acct = self._Acct(balance, equity)
        self._deals = deals

    def account_info(self):
        return self._acct

    def history_deals_get(self, *a, **k):
        return self._deals


def test_dd_distance_fires_inside_2000(tripwires):
    # 2026-08-24 is CEST: the FTMO window began 2026-08-23T22:00Z.
    # balance 96,600 now; realized today -3,400 => day-start balance 100,000.
    # equity 96,500 => loss_today 3,500; limit 5,000; remaining 1,500 < 2,000.
    deals = [FakeMT5._Deal(_wall_epoch(_utc(2026, 8, 24, 6)), -3400.0)]
    mt5 = FakeMT5(balance=96600.0, equity=96500.0, deals=deals)
    state = {}
    w = tripwires.wire_dd_distance(_inputs(), mt5, None, 2000.0, state,
                                   now_utc=_utc(2026, 8, 24, 12))
    assert w["status"] == "ok"
    assert w["daily_limit_usd"] == pytest.approx(5000.0)
    assert w["loss_today_usd"] == pytest.approx(3500.0)
    assert w["remaining_usd"] == pytest.approx(1500.0)
    assert w["fired"] is True
    assert w["boundary_utc"].endswith("T22:00:00Z")
    assert state["dd_anchor"]["baseline"] == pytest.approx(100000.0)


def test_dd_distance_holds_with_room(tripwires):
    deals = [FakeMT5._Deal(_wall_epoch(_utc(2026, 8, 24, 6)), -500.0)]
    mt5 = FakeMT5(balance=99500.0, equity=99400.0, deals=deals)
    w = tripwires.wire_dd_distance(_inputs(), mt5, None, 2000.0, {},
                                   now_utc=_utc(2026, 8, 24, 12))
    assert w["fired"] is False
    assert w["remaining_usd"] == pytest.approx(4400.0)


def test_dd_distance_excludes_pre_boundary_deals_and_balance_ops(tripwires):
    deals = [
        FakeMT5._Deal(_wall_epoch(_utc(2026, 8, 23, 12)), -9000.0),  # yesterday
        FakeMT5._Deal(_wall_epoch(_utc(2026, 8, 24, 6)), -100.0),
        FakeMT5._Deal(_wall_epoch(_utc(2026, 8, 24, 7)), 5000.0, dtype=2),  # balance op
    ]
    mt5 = FakeMT5(balance=99900.0, equity=99900.0, deals=deals)
    w = tripwires.wire_dd_distance(_inputs(), mt5, None, 2000.0, {},
                                   now_utc=_utc(2026, 8, 24, 12))
    # day-start balance = 99900 - (-100) = 100000; loss = 100
    assert w["loss_today_usd"] == pytest.approx(100.0)
    assert w["fired"] is False


def test_dd_distance_without_mt5_never_fires(tripwires):
    w = tripwires.wire_dd_distance(_inputs(), None, None, 2000.0, {})
    assert w["status"] == "account_data_unavailable"
    assert w["fired"] is False


def test_dd_anchor_never_trusts_stale_low(tripwires):
    """Mirrors governor_state._balance_anchor: max(stored, fresh)."""
    deals = [FakeMT5._Deal(_wall_epoch(_utc(2026, 8, 24, 6)), -3400.0)]
    mt5 = FakeMT5(balance=96600.0, equity=96500.0, deals=deals)
    state = {"dd_anchor": {"date": "2026-08-23", "baseline": 90000.0}}  # old day
    w = tripwires.wire_dd_distance(_inputs(), mt5, None, 2000.0, state,
                                   now_utc=_utc(2026, 8, 24, 12))
    assert state["dd_anchor"]["baseline"] == pytest.approx(100000.0)
    state2 = {"dd_anchor": {"date": w["boundary_utc"][:10], "baseline": 90000.0}}
    w2 = tripwires.wire_dd_distance(_inputs(), mt5, None, 2000.0, state2,
                                    now_utc=_utc(2026, 8, 24, 12))
    assert w2["baseline_usd"] == pytest.approx(100000.0)   # stale-low ignored


# ------------------------------------------------------------ (c) judgment_dark
def _launcher(tmp_path, cycle_ts_intents):
    p = tmp_path / "launcher.jsonl"
    _write_jsonl(p, [{"namespace": "operator", "ts": ts,
                      "action": "cycle", "n_intents": n}
                     for ts, n in cycle_ts_intents])
    return str(p)


def test_judgment_dark_fires_on_two_dark_cycles(tripwires, tmp_path):
    lp = _launcher(tmp_path, [("2026-08-24T10:00:00+00:00", 2),
                              ("2026-08-24T10:15:00+00:00", 1),
                              ("2026-08-24T10:30:00+00:00", 0)])
    w = tripwires.wire_judgment_dark(DAY, _inputs(launcher=lp))
    assert w["fired"] is True
    assert w["cycles_since_last_judge_row"] == 2


def test_judgment_dark_holds_when_judge_wrote_after_cycles(tripwires, tmp_path):
    lp = _launcher(tmp_path, [("2026-08-24T10:00:00+00:00", 2),
                              ("2026-08-24T10:15:00+00:00", 1)])
    jp = tmp_path / ("judge_%s.jsonl" % DAY)
    _write_jsonl(jp, [{"written_at_utc": "2026-08-24T10:16:00+00:00",
                       "verdict": "approve", "join_key": "X"}])
    w = tripwires.wire_judgment_dark(
        DAY, _inputs(launcher=lp, judge_files=[str(jp)]))
    assert w["fired"] is False
    assert w["cycles_since_last_judge_row"] == 0


def test_judgment_dark_holds_on_single_dark_cycle(tripwires, tmp_path):
    lp = _launcher(tmp_path, [("2026-08-24T10:00:00+00:00", 1)])
    w = tripwires.wire_judgment_dark(DAY, _inputs(launcher=lp))
    assert w["fired"] is False


# -------------------------------------------------------------- (d) hold_breach
CAND = "W7_BOOK::c::LTCUSD::2026-08-24::LONG::asia_pdl_fade"


def _hold_sidecar(tmp_path, written, ttl=600.0):
    p = tmp_path / ("flow_%s.json" % DAY)
    p.write_text(json.dumps({CAND: {"action": "HOLD", "verdict": "veto",
                                    "written_at_utc": written,
                                    "ttl_s": ttl,
                                    "namespace": "operator"}}))
    return str(p)


def _fill_events_file(tmp_path, ts):
    p = tmp_path / "events.jsonl"
    _write_jsonl(p, [{"event": "f5_fill", "ticket": 178351323,
                      "candidate_id": CAND, "ts_utc": ts,
                      "symbol": "LTCUSD", "sleeve": "asia_pdl_fade"}])
    return str(p)


def test_hold_breach_fires_on_fill_inside_ttl(tripwires, tmp_path):
    sc = _hold_sidecar(tmp_path, "2026-08-24T23:10:00+00:00")
    ev = _fill_events_file(tmp_path, "2026-08-24T23:16:18+00:00")
    w = tripwires.wire_hold_breach(DAY, _inputs(events=ev, sidecars=[sc]))
    assert w["fired"] is True
    assert w["breaches"][0]["ticket"] == 178351323


def test_hold_breach_holds_when_ttl_expired(tripwires, tmp_path):
    sc = _hold_sidecar(tmp_path, "2026-08-24T22:00:00+00:00", ttl=600.0)
    ev = _fill_events_file(tmp_path, "2026-08-24T23:16:18+00:00")
    w = tripwires.wire_hold_breach(DAY, _inputs(events=ev, sidecars=[sc]))
    assert w["fired"] is False


def test_hold_breach_from_judge_rows(tripwires, tmp_path):
    jp = tmp_path / ("judge_%s.jsonl" % DAY)
    _write_jsonl(jp, [{"written_at_utc": "2026-08-24T23:12:00+00:00",
                       "verdict": "hold", "join_key": CAND, "ttl_s": 600}])
    ev = _fill_events_file(tmp_path, "2026-08-24T23:16:18+00:00")
    w = tripwires.wire_hold_breach(DAY, _inputs(events=ev,
                                                judge_files=[str(jp)]))
    assert w["fired"] is True


# ----------------------------------------------------------- (e) adapter_breach
def test_adapter_breach_fires_on_growth_and_holds_flat(tripwires, tmp_path):
    ev = tmp_path / "events.jsonl"
    _write_jsonl(ev, [{"event": "f5_fill_deviation_breach", "ticket": 1,
                       "ts_utc": "2026-08-24T13:00:00+00:00"}])
    state = {}
    w1 = tripwires.wire_adapter_breach(DAY, _inputs(events=str(ev)), state)
    assert w1["count"] == 1 and w1["fired"] is True         # first nonzero
    w2 = tripwires.wire_adapter_breach(DAY, _inputs(events=str(ev)), state)
    assert w2["fired"] is False                             # unchanged
    _write_jsonl(ev, [{"event": "f5_fill_deviation_breach", "ticket": 1,
                       "ts_utc": "2026-08-24T13:00:00+00:00"},
                      {"event": "f5_fill_deviation_breach", "ticket": 2,
                       "ts_utc": "2026-08-24T14:00:00+00:00"}])
    w3 = tripwires.wire_adapter_breach(DAY, _inputs(events=str(ev)), state)
    assert w3["fired"] is True and w3["count"] == 2         # growth


def test_adapter_breach_reads_counter_files(tripwires, tmp_path):
    cf = tmp_path / "adapter_breach_counter.json"
    cf.write_text(json.dumps({"count": 3}))
    state = {"adapter_breach_count": 3}
    w = tripwires.wire_adapter_breach(DAY, _inputs(breach_files=[str(cf)]),
                                      state)
    assert w["count"] == 3 and w["fired"] is False
    cf.write_text(json.dumps({"count": 5}))
    w2 = tripwires.wire_adapter_breach(DAY, _inputs(breach_files=[str(cf)]),
                                       state)
    assert w2["count"] == 5 and w2["fired"] is True


# ------------------------------------------------------------------- delivery
def test_deliver_appends_queue_row_schema(tripwires, tmp_path):
    q = tmp_path / "queue" / "notification_queue.jsonl"
    alerts = [{"wire": "day_net", "message": "F5 TRIPWIRE day_net: -$1100.00"}]
    res = tripwires.deliver(alerts, str(q), None, dry_run=False)
    assert res[0]["delivery"] == "queue_row_append"
    rows = [json.loads(l) for l in open(str(q))]
    assert len(rows) == 1
    row = rows[0]
    # exact enqueue-row schema from src/utils/notification_queue.py
    assert set(row) == {"alert_id", "ts_utc", "level", "message",
                        "retry_count", "last_attempt_utc"}
    assert row["level"] == "CRITICAL" and row["retry_count"] == 0
    # deterministic id -> the queue dedupes a 10-min cron
    res2 = tripwires.deliver(alerts, str(q), None, dry_run=False)
    assert res2[0]["alert_id"] == res[0]["alert_id"]


def test_deliver_dry_run_writes_nothing(tripwires, tmp_path):
    q = tmp_path / "queue.jsonl"
    res = tripwires.deliver([{"wire": "x", "message": "m"}], str(q), None,
                            dry_run=True)
    assert res[0]["delivery"] == "dry_run"
    assert not q.exists()
