"""h2_cash — the EX-ANTE conditioning rule: trade an instrument only while its own
underlying cash market is open.

Motivation, and why this is not a fitted cell.  The broker-hour spread table shows the
cheap hours and the high-edge hours are the SAME hours, and they are the hours the
underlying exchange is open.  That is a mechanism, so it can be written down without
looking at any P&L: each instrument's window is defined in its EXCHANGE's own local
time (Europe/Berlin, Europe/London, America/New_York, Asia/Tokyo), converted per-day, so
it is correct through the 2026-03-08..03-28 window where the US and EU DST calendars
disagree -- exactly the window inside the March month.

Costs are HOUR-TRUE (h2_hourcost).  Nothing here selects on the outcome column.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h2_lib as H  # noqa: E402
import h2_scan  # noqa: E402
import h2_hourcost as HC  # noqa: E402

BERLIN, LONDON, NY, TOKYO = (ZoneInfo("Europe/Berlin"), ZoneInfo("Europe/London"),
                             ZoneInfo("America/New_York"), ZoneInfo("Asia/Tokyo"))

# (tz, open_hhmm, close_hhmm) in the exchange's own local wall clock.
CASH = {
    "GER40": (BERLIN, 9.0, 17.5),        # Xetra 09:00-17:30 CET/CEST
    "UK100": (LONDON, 8.0, 16.5),        # LSE 08:00-16:30 London
    "US30_cash": (NY, 9.5, 16.0),        # NYSE 09:30-16:00 New York
    "NAS100": (NY, 9.5, 16.0),
    "SPX500": (NY, 9.5, 16.0),
    "JP225": (TOKYO, 9.0, 15.0),         # TSE 09:00-15:00 Tokyo
    "USOIL_cash": (NY, 9.0, 14.5),       # NYMEX floor 09:00-14:30 New York
    "UKOIL_cash": (LONDON, 8.0, 17.5),   # ICE Europe
    "XAUUSD": (LONDON, 8.0, 21.0),       # London fix through NY close
    "XAGUSD": (LONDON, 8.0, 21.0),
}
# FX: the London->NY liquid window, defined in London local time.
FX = {"EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
      "EURJPY", "GBPJPY", "AUDJPY", "CHFJPY", "EURGBP"}
FX_WIN = (LONDON, 8.0, 17.0)
CRYPTO = {"BTCUSD", "ETHUSD"}            # 24/7, no window


def in_cash(r):
    sym = r["symbol"]
    if sym in CRYPTO:
        return True
    spec = CASH.get(sym) or (FX_WIN if sym in FX else None)
    if spec is None:
        return None
    tz, o, c = spec
    lt = datetime.fromisoformat(r["dt"]).astimezone(tz)
    if lt.weekday() >= 5:
        return False
    h = lt.hour + lt.minute / 60.0
    return o <= h < c


def main():
    rows = h2_scan.build()
    cov = HC.attach(rows)
    for r in rows:
        r["cash"] = in_cash(r)
    out = {"coverage": cov,
           "unmapped_symbols": sorted({r["symbol"] for r in rows if r["cash"] is None})}

    inn = [r for r in rows if r["cash"] is True]
    off = [r for r in rows if r["cash"] is False]
    out["book"] = {"all": HC.restat(rows), "cash_open": HC.restat(inn),
                   "cash_closed": HC.restat(off),
                   "share_in_cash": round(len(inn) / len(rows), 5)}
    out["book_flatcost"] = {"all": HC.restat(rows, False), "cash_open": HC.restat(inn, False),
                            "cash_closed": HC.restat(off, False)}

    # per symbol, in/out
    sy = {}
    for s, v in sorted(H.group(rows, lambda r: r["symbol"]).items()):
        a = [r for r in v if r["cash"] is True]
        b = [r for r in v if r["cash"] is False]
        sy[s] = {"in": HC.restat(a), "out": HC.restat(b),
                 "share_in": round(len(a) / len(v), 4)}
    out["symbols"] = sy

    # the cash-open book, conditioned further
    C = {}
    for name, fn in (("session", lambda r: r["session"]), ("side", lambda r: r["side"]),
                     ("family", lambda r: r["family"]), ("vol", lambda r: r["vol"]),
                     ("month", lambda r: r["month"]), ("dow", lambda r: r["dow"])):
        C[name] = {k: HC.restat(v) for k, v in sorted(H.group(inn, fn).items()) if len(v) >= 50}
    out["cash_open_conditioned"] = C

    # symbol x cash-open x side
    grid = {}
    for k, v in sorted(H.group(inn, lambda r: "%s|%s" % (r["symbol"], r["side"])).items()):
        if len(v) >= 50:
            grid[k] = HC.restat(v)
    out["cash_open_symbol_side"] = grid

    # ---- OOS: the rule is fixed a priori, so the only question is whether it holds forward
    jan = [r for r in inn if r["month"] == "2026-01"]
    fm = [r for r in inn if r["month"] != "2026-01"]
    out["oos_fixed_rule"] = {"january": HC.restat(jan), "feb_mar": HC.restat(fm)}
    # and per symbol
    o2 = {}
    for s in sorted({r["symbol"] for r in inn}):
        a = [r for r in jan if r["symbol"] == s]
        b = [r for r in fm if r["symbol"] == s]
        if len(a) >= 30 and len(b) >= 30:
            o2[s] = {"jan": HC.restat(a), "feb_mar": HC.restat(b)}
    out["oos_fixed_rule_per_symbol"] = o2

    # ---- the composed candidate: cash-open AND positive-margin instruments, chosen on Jan only
    jpos = sorted([s for s, v in o2.items() if v["jan"]["net_r"] > 0])
    out["jan_positive_within_cash"] = {
        "symbols": jpos,
        "feb_mar": HC.restat([r for r in fm if r["symbol"] in set(jpos)]) if jpos else None}

    with open(os.path.join(D, "H2_CASH_V1.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    b = out["book"]
    print("CASH-SESSION RULE (ex-ante, exchange-local, hour-true cost)")
    print("  whole book   n=%-6d gross=%+.6f cost=%.6f net=%+.6f tclu=%+.2f d+%d/%d"
          % (b["all"]["n"], b["all"]["gross_r"], b["all"]["cost_r"], b["all"]["net_r"],
             b["all"]["t_net_clu"], b["all"]["days_pos_net"], b["all"]["days"]))
    print("  cash OPEN    n=%-6d gross=%+.6f cost=%.6f net=%+.6f tclu=%+.2f d+%d/%d  (%.1f%% of book) months %s"
          % (b["cash_open"]["n"], b["cash_open"]["gross_r"], b["cash_open"]["cost_r"],
             b["cash_open"]["net_r"], b["cash_open"]["t_net_clu"], b["cash_open"]["days_pos_net"],
             b["cash_open"]["days"], 100 * b["share_in_cash"], b["cash_open"]["months"]))
    print("  cash CLOSED  n=%-6d gross=%+.6f cost=%.6f net=%+.6f tclu=%+.2f"
          % (b["cash_closed"]["n"], b["cash_closed"]["gross_r"], b["cash_closed"]["cost_r"],
             b["cash_closed"]["net_r"], b["cash_closed"]["t_net_clu"]))
    print("\nper symbol, cash-OPEN only (hour-true), sorted by net:")
    print("%-11s %6s %9s %9s %9s %8s %8s %7s %6s %s" %
          ("symbol", "n_in", "gross_r", "cost_r", "net_r", "gbps", "cbps", "margin", "tclu", "m+"))
    for s, v in sorted(sy.items(), key=lambda kv: -(kv[1]["in"]["net_r"] if kv[1]["in"] else -9)):
        i = v["in"]
        if not i:
            continue
        print("%-11s %6d %+9.5f %9.5f %+9.5f %+8.4f %8.4f %+7.4f %6.2f %d/3"
              % (s, i["n"], i["gross_r"], i["cost_r"], i["net_r"], i["gross_bps"],
                 i["cost_bps"], i["margin_bps"], i["t_net_clu"] or 0,
                 sum(1 for x in i["months"].values() if x > 0)))
    o = out["oos_fixed_rule"]
    print("\nfixed-rule OOS: January n=%d net=%+.6f | Feb+Mar n=%d net=%+.6f tclu=%+.2f months %s"
          % (o["january"]["n"], o["january"]["net_r"], o["feb_mar"]["n"], o["feb_mar"]["net_r"],
             o["feb_mar"]["t_net_clu"], o["feb_mar"]["months"]))
    jp = out["jan_positive_within_cash"]
    print("  symbols net-positive in January inside the rule: %s" % (", ".join(jp["symbols"]) or "NONE"))
    if jp["feb_mar"]:
        f = jp["feb_mar"]
        print("    -> Feb+Mar n=%d net=%+.6f tclu=%+.2f d+%d/%d months %s"
              % (f["n"], f["net_r"], f["t_net_clu"] or 0, f["days_pos_net"], f["days"], f["months"]))
    print("\ncash-open x side cells n>=50 that pay:")
    for k, v in sorted(grid.items(), key=lambda kv: -kv[1]["net_r"]):
        if v["net_r"] > 0:
            print("  %-22s n=%-5d g=%+.5f c=%.5f net=%+.5f tclu=%+5.2f margin=%+7.3f m+%d/3"
                  % (k, v["n"], v["gross_r"], v["cost_r"], v["net_r"], v["t_net_clu"] or 0,
                     v["margin_bps"], sum(1 for x in v["months"].values() if x > 0)))


if __name__ == "__main__":
    main()
