"""DAILY.md v2 owner-page tests: era split, overshoot ledger, FAILED
RECONCILIATION line, same-bar clusters, fill dedupe, TELEGRAM.txt."""
import json
import os
import subprocess
import sys

import pytest

DAY = "2026-08-24"
SCRIPT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "scripts", "f5_harvest",
    "summarize_f5_daily.py"))


def ledger_row(ticket, era, net, risk, symbol="XAUUSD", sleeve="s",
               exit_ts="2026-08-24T13:12:07Z", outcome="FILLED_CLOSED",
               mfe_r=None, direction="SHORT",
               fill_ts="2026-08-24T13:03:39Z"):
    exc = {"status": "not_computed"}
    if mfe_r is not None:
        exc = {"status": "ok", "mfe_r": mfe_r, "mfe_usd": round(mfe_r * risk, 2)}
    return {"schema": "gtos.f5.outcome_ledger.v1",
            "candidate_id": "W7_BOOK::c::%s::2026-08-24::%s::%s" % (symbol, direction, sleeve),
            "namespace": "operator", "symbol": symbol, "sleeve": sleeve,
            "direction": direction, "decision_day": DAY,
            "outcome_class": outcome, "era": era,
            "later_known": {
                "fill": {"ticket": ticket, "broker_fill_time_utc": fill_ts,
                         "broker_entry_price": 4650.0,
                         "f5_intended_risk_usd": era,
                         "f5_actual_risk_usd": risk},
                "lifecycle": ({"status": "CLOSED",
                               "broker_exit_time_utc": exit_ts,
                               "dollars": {"net_usd": net},
                               "realised_r": (net / risk) if risk else None}
                              if outcome == "FILLED_CLOSED"
                              else {"status": "OPEN_OR_UNKNOWN"}),
                "excursion": exc},
            "join_quality": {"flags": [], "joined_end_to_end": True,
                             "sources_present": {}}}


def fill_event(ticket, ts, sleeve, cand, symbol, risk=75.0, intended=75.0,
               bar="2026-08-24T13:00:00+00:00"):
    return {"event": "f5_fill", "ticket": ticket, "ts_utc": ts,
            "sleeve": sleeve, "candidate_id": cand, "symbol": symbol,
            "decision_bar_iso": bar, "decision_day": DAY,
            "f5_actual_risk_usd": risk, "f5_intended_risk_usd": intended,
            "namespace": "operator",
            "schema": "gtos.f5.minimal_size_event.v1"}


@pytest.fixture()
def harvest(tmp_path):
    root = tmp_path / "hroot"
    dated = root / DAY
    (dated / "outbox").mkdir(parents=True)
    # events: two fills same bar (cluster), one duplicated dual-sleeve, one
    # deviation-breach event, one slate
    cand_a = "W7_BOOK::c::XAUUSD::2026-08-24::SHORT::dsp_isolated_spike_high"
    cand_b = "W7_BOOK::c::USDJPY::2026-08-24::SHORT::dsp_wide"
    events = [
        fill_event(1, "2026-08-24T13:03:39.5+00:00",
                   "dsp_isolated_flush_to_20low_snap", cand_a, "XAUUSD"),
        fill_event(1, "2026-08-24T13:03:39.6+00:00",
                   "dsp_isolated_spike_high", cand_a, "XAUUSD"),
        fill_event(2, "2026-08-24T13:05:00+00:00", "dsp_wide", cand_b, "USDJPY"),
        {"event": "f5_fill_deviation_breach", "ticket": 1,
         "ts_utc": "2026-08-24T13:03:40+00:00", "symbol": "XAUUSD",
         "reason": "entry_slippage_1.48x_stop"},
        {"event": "f5_slate", "ts_utc": "2026-08-24T14:00:00+00:00",
         "f5_notional": {"real_pnl_usd_cumulative": -1007.17,
                         "trades_recorded": 29, "notional_equity": 96439.56}},
    ]
    with open(dated / "events.jsonl", "w") as fh:
        for e in events:
            fh.write(json.dumps(e) + "\n")
    # cumulative ledger: one $75 overshoot loser (the LTCUSD shape), one $10
    # plain loser, one $75 winner, one open position
    rows = [
        ledger_row(1, 75.0, -307.53, 74.93, symbol="LTCUSD",
                   sleeve="asia_pdl_fade", mfe_r=0.4),
        ledger_row(2, 10.0, -9.5, 10.0, symbol="EURUSD", sleeve="asian_fade"),
        ledger_row(3, 75.0, 150.0, 75.0, symbol="GBPUSD", sleeve="asian_fade"),
        ledger_row(4, 75.0, None, 75.0, symbol="BTCUSD",
                   sleeve="vol_compression", outcome="FILLED_OPEN"),
    ]
    with open(root / "f5_outcome_ledger_cumulative.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    # reconciliation: today FAILED by $50
    recon = {"schema": "gtos.f5.broker_reconciliation.v1",
             "days": {DAY: {"broker_net_usd": -217.03, "broker_n_closed": 3,
                            "ledger_net_usd": -167.03, "ledger_n_closed": 3,
                            "diff_usd": -50.0,
                            "broker_net_by_era": {"$75": -207.53, "$10": -9.5},
                            "ledger_net_by_era": {"$75": -157.53, "$10": -9.5},
                            "tickets_broker_only": [99],
                            "tickets_ledger_only": [],
                            "status": "FAILED"}},
             "n_failed": 1}
    with open(root / "f5_broker_reconciliation.json", "w") as fh:
        json.dump(recon, fh)
    return root


def run_summarizer(root):
    out = subprocess.run(
        [sys.executable, SCRIPT, str(root / DAY), "--date", DAY],
        capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    daily = (root / DAY / "DAILY.md").read_text()
    telegram = (root / DAY / "TELEGRAM.txt").read_text()
    return daily, telegram


def test_owner_page_dollars_era_and_failed_reconciliation(harvest):
    daily, telegram = run_summarizer(harvest)
    # dollars first, broker authority for the day, era-stratified
    assert "Day net 2026-08-24: -$217.03" in daily
    assert "$75: -$207.53" in daily and "$10: -$9.50" in daily
    assert "source: broker deals dump (authority)" in daily
    # cumulative era split from the ledger
    assert "$75: -$157.53" in daily and "$10: -$9.50" in daily
    # FAILED RECONCILIATION line with the diff
    assert "FAILED RECONCILIATION 2026-08-24" in daily
    assert "diff -$50.00" in daily
    # overshoot: LTCUSD lost 307.53 on 74.93 risk -> -232.60 beyond -1R
    assert "-$232.60" in daily
    assert "0.40R" in daily            # MFE before loss rendered
    # deviation breach section sees the event
    assert "entry_slippage_1.48x_stop" in daily
    # same-bar cluster: tickets 1+2 share bar 13:00
    assert "2 fills" in daily
    # dedupe: dual-sleeve fill listed once, flagged
    assert daily.count("ticket 1 ") == 1 or "[dual-sleeve attribution]" in daily
    # open-position map
    assert "BTCUSD" in daily and "vol_compression" in daily


def test_telegram_six_lines(harvest):
    _, telegram = run_summarizer(harvest)
    lines = [l for l in telegram.strip().splitlines()]
    assert len(lines) == 6
    assert lines[0].startswith("F5 2026-08-24 day net -$217.03")
    assert "RECON FAILED x1" in lines[5]
    # plain text, no HTML tags (notifications policy)
    assert "<" not in telegram


def test_summarizer_degrades_without_recon_and_ledger(tmp_path):
    """Absent ledger + recon + events -> page still writes, labelled absent."""
    root = tmp_path / "empty"
    (root / DAY / "outbox").mkdir(parents=True)
    daily, telegram = run_summarizer(root)
    assert "no broker-deals reconciliation on record" in daily
    assert "recon absent" in telegram
