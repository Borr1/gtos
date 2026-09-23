"""e5 — build a month's fill-honest R-path working set from a diagnostic pool + true-UTC M1.

Same contract as CQ's January sidecar (cq_path_pool_grid.py:490-511):
  * observations STRICTLY AFTER the decision minute, through decision + 120 min
  * true-UTC M1 from the lane hold, 24 symbols
  * fav/adv/cls signed for the trade's own side, denominated by risk_distance
  * mkt_r_prev_close = close of the last fully-closed bar STRICTLY BEFORE the decision
    minute (bars are OPEN-stamped, so the bar stamped at the decision minute is entirely
    post-decision -- see w0-capture's self-correction). born_past_stop := that <= -1.0

usage:  python3 e5_build_month.py <january|february|march> [--limit N]
writes  e5_<month>_WS_V1.jsonl.gz  and  e5_<month>_BUILD_V1.json
"""
from __future__ import annotations
import sys, os, json, gzip, csv, bisect, hashlib

D = os.path.dirname(os.path.abspath(__file__))
LANE = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
FA2 = ("/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/research/operations/"
       "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
       "attempt_5_typed_sparse")

MONTHS = {
    "january": {
        "m1": "bridge_ftmo_m1_202601",
        "pool": os.path.join(REPO, "docs/audits/fable5-vision-audit-20260725/phase16/"
                                   "receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"),
        "kind": "pool",
    },
    "february": {
        "m1": "bridge_ftmo_m1_202602",
        "pool": os.path.join(REPO, "docs/audits/fable5-vision-audit-20260725/phase18/"
                                   "receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"),
        "kind": "pool",
    },
    "march": {
        "m1": "bridge_ftmo_m1_202603",
        "pool": os.path.join(FA2, "FA2_M_R0/FA2_M_R0_MISSED_OPPORTUNITY_LEDGER.jsonl.gz"),
        "kind": "ledger",
    },
}
HORIZON_MIN = 120
KEEP = ("candidate_id", "decision_time_utc", "symbol", "origin_family", "session_bucket",
        "route_session", "policy_target_r", "raw_target_r", "spread_r", "commission_r",
        "swap_cost_r", "expected_slippage_r", "cost_r", "opportunity_net_proxy_r",
        "entry_price", "stop_loss", "take_profit_1", "final_blocker_class",
        "risk_per_trade_pct", "utc_hour_bucket", "terminal_outcome")


def load_bars(m1dir):
    out = {}
    for fn in sorted(os.listdir(m1dir)):
        if not fn.endswith("_M1.csv"):
            continue
        sym = fn[:-7]
        t, o, h, l, c = [], [], [], [], []
        with open(os.path.join(m1dir, fn), newline="") as fh:
            rd = csv.reader(fh)
            hdr = next(rd)
            ix = {k: hdr.index(k) for k in ("time", "open", "high", "low", "close")}
            for row in rd:
                t.append(row[ix["time"]])
                o.append(float(row[ix["open"]]))
                h.append(float(row[ix["high"]]))
                l.append(float(row[ix["low"]]))
                c.append(float(row[ix["close"]]))
        out[sym] = {"t": t, "o": o, "h": h, "l": l, "c": c}
    return out


def horizon_iso(dt_iso, minutes):
    # ISO 'YYYY-MM-DDTHH:MM:SS+00:00' -> add minutes, stay in ISO for lexical bisect
    import datetime as dtm
    d = dtm.datetime.fromisoformat(dt_iso)
    return (d + dtm.timedelta(minutes=minutes)).isoformat()


def build(month, limit=None):
    cfg = MONTHS[month]
    bars = load_bars(os.path.join(LANE, cfg["m1"]))
    st = {"month": month, "m1_source": cfg["m1"], "m1_symbols": len(bars),
          "pool": cfg["pool"], "pool_rows": 0, "kept": 0, "skip_not_scoreable": 0,
          "skip_no_symbol": 0, "skip_bad_geometry": 0, "skip_no_path": 0,
          "skip_short_path": 0, "past_stop": 0, "no_fill": 0}
    outp = os.path.join(D, "e5_%s_WS_V1.jsonl.gz" % month)
    seen = set()
    with gzip.open(cfg["pool"], "rt") as fin, gzip.open(outp, "wt") as fout:
        for ln in fin:
            if not ln.strip():
                continue
            r = json.loads(ln)
            st["pool_rows"] += 1
            if limit and st["pool_rows"] > limit:
                break
            if cfg["kind"] == "ledger":
                # reproduce the January pool's own scoreability gate (dictionary D3)
                if r.get("missed_opportunity_r_scoreability_status") != "diagnostic_opportunity_r_scoreable":
                    st["skip_not_scoreable"] += 1
                    continue
                if r.get("opportunity_net_proxy_r") is None:
                    st["skip_not_scoreable"] += 1
                    continue
            sym = r.get("symbol")
            b = bars.get(sym)
            if b is None:
                st["skip_no_symbol"] += 1
                continue
            side = (r.get("side") or r.get("direction") or "").upper()
            try:
                entry = float(r["entry_price"]); stop = float(r["stop_loss"])
            except (TypeError, ValueError, KeyError):
                st["skip_bad_geometry"] += 1
                continue
            d = abs(entry - stop)
            if not (d > 0):
                st["skip_bad_geometry"] += 1
                continue
            dt = r["decision_time_utc"]
            hz = horizon_iso(dt, HORIZON_MIN)
            i0 = bisect.bisect_right(b["t"], dt)
            i1 = bisect.bisect_right(b["t"], hz)
            if i1 <= i0:
                st["skip_no_path"] += 1
                continue
            sgn = 1.0 if side.startswith("L") else -1.0
            fav = []; adv = []; cls = []
            for i in range(i0, i1):
                hi, lo, cl = b["h"][i], b["l"][i], b["c"][i]
                a = sgn * (hi - entry) / d
                z = sgn * (lo - entry) / d
                fav.append(round(max(a, z), 5))
                adv.append(round(min(a, z), 5))
                cls.append(round(sgn * (b["c"][i] - entry) / d, 5))
            # anchor: last fully-closed bar strictly before the decision minute
            j = bisect.bisect_right(b["t"], dt) - 1
            if j >= 0 and b["t"][j] == dt:
                j -= 1
            mkt = (round(sgn * (b["c"][j] - entry) / d, 6) if j >= 0 else None)
            if mkt is not None and mkt <= -1.0:
                st["past_stop"] += 1
            if not any(x <= 1e-12 for x in adv):
                st["no_fill"] += 1
            row = {k: r.get(k) for k in KEEP}
            row["side"] = side
            row["risk_distance"] = d
            row["mkt_r_prev_close"] = mkt
            row["fav"] = fav; row["adv"] = adv; row["cls"] = cls
            row["path_bars"] = len(fav)
            key = (row["candidate_id"], dt)
            row["dup_key_seen"] = key in seen
            seen.add(key)
            fout.write(json.dumps(row) + "\n")
            st["kept"] += 1
    st["distinct_keys"] = len(seen)
    st["out"] = outp
    st["out_bytes"] = os.path.getsize(outp)
    with open(os.path.join(D, "e5_%s_BUILD_V1.json" % month), "w") as fh:
        json.dump(st, fh, indent=1)
    return st


if __name__ == "__main__":
    m = sys.argv[1]
    lim = None
    if "--limit" in sys.argv:
        lim = int(sys.argv[sys.argv.index("--limit") + 1])
    s = build(m, lim)
    print(json.dumps(s))
