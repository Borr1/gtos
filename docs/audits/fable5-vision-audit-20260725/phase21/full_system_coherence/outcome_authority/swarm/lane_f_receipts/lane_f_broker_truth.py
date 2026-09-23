#!/usr/bin/env python3
"""LANE F - read-only broker-truth extraction from both live MT5 terminals.

STRICTLY READ-ONLY. Calls used: initialize / account_info / positions_get /
history_deals_get / symbol_info / terminal_info / shutdown.
There is no order_send, order_check, order_calc, or any mutating call in this file.

Writes its output OUTSIDE the live tree. Imports the live tree's broker_clock only,
with PYTHONDONTWRITEBYTECODE set by the caller so no .pyc lands in the live tree.
"""
import os
import sys
import json
import hashlib
import datetime as dt

REPO = r"C:\Users\MSI\Documents\ai-trading-agent"
OUT = sys.argv[1] if len(sys.argv) > 1 else r"host-local\lane_f_20260811"
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, REPO)
import MetaTrader5 as mt5  # noqa: E402
from src.utils.broker_clock import broker_epoch_to_utc, resolve_rule  # noqa: E402

ACCOUNTS = [
    ("FTMO", r"C:\MT5\FTMO\terminal64.exe", "FTMO-Server3"),
    ("redacted_account", r"C:\MT5\redacted_account\terminal64.exe", "redacted_account-Server 2"),
]

# Wide enough that the broker-wall-clock interpretation of these bounds cannot
# clip anything: from well before either account existed to well past now.
START = dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc)
END = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=3)


def redact(value):
    if value is None:
        return None
    h = hashlib.sha256(str(value).encode()).hexdigest()[:12]
    return "redacted:" + h


def as_dict(obj, fields):
    out = {}
    for f in fields:
        v = getattr(obj, f, None)
        if v is None:
            continue
        try:
            json.dumps(v)
        except (TypeError, ValueError):
            v = str(v)
        out[f] = v
    return out


DEAL_FIELDS = ("ticket", "order", "position_id", "entry", "time", "time_msc", "type",
               "volume", "price", "profit", "commission", "swap", "fee", "magic",
               "reason", "symbol", "comment", "external_id")
POS_FIELDS = ("ticket", "time", "time_msc", "time_update", "type", "magic", "identifier",
              "reason", "volume", "price_open", "sl", "tp", "price_current", "swap",
              "profit", "symbol", "comment", "external_id")
ACC_FIELDS = ("login", "trade_mode", "leverage", "limit_orders", "margin_so_mode",
              "trade_allowed", "trade_expert", "margin_mode", "currency_digits",
              "fifo_close", "balance", "credit", "profit", "equity", "margin",
              "margin_free", "margin_level", "margin_so_call", "margin_so_so",
              "balance_clean", "currency", "server", "company", "name")

result = {"schema": "gtos.lane_f.broker_truth.v1",
          "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
          "read_only": True,
          "accounts": {}}

for label, path, server_str in ACCOUNTS:
    rec = {"label": label, "server_string": server_str}
    if not mt5.initialize(path=path, portable=True):
        rec["error"] = "connect_fail:%s" % (mt5.last_error(),)
        result["accounts"][label] = rec
        continue
    try:
        ti = mt5.terminal_info()
        rec["terminal"] = as_dict(ti, ("build", "connected", "trade_allowed", "path",
                                       "data_path", "company", "name")) if ti else None
        info = mt5.account_info()
        if not info:
            rec["error"] = "account_info_none"
            result["accounts"][label] = rec
            continue
        acc = as_dict(info, ACC_FIELDS)
        acc["login_redacted"] = redact(acc.pop("login", None))
        acc["name_redacted"] = redact(acc.pop("name", None))
        rec["account"] = acc

        srv_rule = resolve_rule(server_str)
        rec["server_offset_hours_now"] = (
            broker_epoch_to_utc(int(dt.datetime.now(dt.timezone.utc).timestamp()), srv_rule)
            - dt.datetime.now(dt.timezone.utc)).total_seconds() / 3600.0

        positions = mt5.positions_get() or []
        pos_rows = []
        for p in positions:
            d = as_dict(p, POS_FIELDS)
            d["time_utc"] = broker_epoch_to_utc(int(p.time), srv_rule).isoformat()
            si = mt5.symbol_info(p.symbol)
            if si:
                d["_symbol"] = as_dict(si, ("trade_tick_value", "trade_tick_size",
                                            "trade_contract_size", "digits", "point"))
                if si.trade_tick_size:
                    vpp = si.trade_tick_value / si.trade_tick_size
                    d["_value_per_price_unit"] = vpp
                    if p.sl and p.price_open:
                        d["_risk_usd_at_sl"] = p.volume * abs(p.price_open - p.sl) * vpp
            pos_rows.append(d)
        rec["positions"] = pos_rows

        deals = mt5.history_deals_get(START, END) or []
        deal_rows = []
        for d in deals:
            row = as_dict(d, DEAL_FIELDS)
            row["time_utc"] = broker_epoch_to_utc(int(d.time), srv_rule).isoformat()
            row["time_broker_wall"] = dt.datetime.utcfromtimestamp(int(d.time)).isoformat()
            deal_rows.append(row)
        rec["deals"] = deal_rows
        rec["n_deals"] = len(deal_rows)
        rec["n_positions_open"] = len(pos_rows)
        print("[%s] deals=%d open=%d bal=%.2f eq=%.2f" %
              (label, len(deal_rows), len(pos_rows), info.balance, info.equity))
    finally:
        mt5.shutdown()
    result["accounts"][label] = rec

dst = os.path.join(OUT, "BROKER_TRUTH_RAW.json")
with open(dst, "w", encoding="utf-8") as fh:
    json.dump(result, fh, indent=1, sort_keys=True, default=str)
print("WROTE " + dst)
