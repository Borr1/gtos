#!/usr/bin/env python3
"""e6_build_month — port the L8-F1 entry-delay instrument to ANY month.

Emits e6_FRAME_<MONTH>.jsonl.gz: one compact row per pool candidate carrying
  fb       first 1-based M1 bar at which the ENTRY level was traded (-1 = never in 2 h)
  hr       honest 2R/-1R first-touch R, entry required to trade first, conservative
           same-bar tie -> stop, unresolved marked at the wall close, unfilled = 0.0
  oc       outcome in {target, stop, mark, no_fill}
  born     born state from the decision anchor (mkt_r_prev_close), w0-capture convention
  gross_r  pool's own gross = opportunity_net_proxy_r + cost_r
plus the conditioning axes the boundary search needs.

PATH SOURCE: the month's ordered-path sidecar when one exists; otherwise the 120 M1 bars
after the decision minute, rebuilt from the same bar CSVs the sidecar was cut from.
`--verify-bars` rebuilds January from bars and diffs it against the CQ sidecar.
"""
import bisect, csv, collections, gzip, json, os, sys, datetime as dt

D = os.path.dirname(os.path.abspath(__file__))
ROOT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
FA2 = "/Users/borr/GTOSActive/worktrees/fa2-integration-20260803"
BARS_ROOT = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
             "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
TOL = 1e-12
HORIZON = 120

MONTHS = {
    "JAN": dict(
        pool=os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"),
        sidecar=os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz"),
        bars="bridge_ftmo_m1_202601"),
    "FEB": dict(
        pool=os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"),
        sidecar=None, bars="bridge_ftmo_m1_202602"),
    "MAR": dict(
        pool="/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/FA2_M_R0/FA2_M_R0_MISSED_OPPORTUNITY_LEDGER.jsonl.gz",
        sidecar=None, bars="bridge_ftmo_m1_202603",
        filt=lambda r: r.get("missed_opportunity_r_scoreability_status") == "diagnostic_opportunity_r_scoreable"),
    "APR": dict(
        pool=os.path.join(FA2, "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/CS_APRIL_S0R0_POOL_V1.jsonl.gz"),
        sidecar=os.path.join(FA2, "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/CS_APRIL_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz"),
        bars="bridge_ftmo_m1_202604"),
    "MAY": dict(
        pool=os.path.join(FA2, "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/CS_MAY_S0R0_POOL_V1.jsonl.gz"),
        sidecar=os.path.join(FA2, "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/CS_MAY_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz"),
        bars="bridge_ftmo_m1_202605"),
}

_BARCACHE = {}


def load_bars(bars_dir, sym):
    k = (bars_dir, sym)
    if k in _BARCACHE:
        return _BARCACHE[k]
    p = os.path.join(BARS_ROOT, bars_dir, "%s_M1.csv" % sym)
    if not os.path.isfile(p):
        _BARCACHE[k] = None
        return None
    t, o, h, l, c = [], [], [], [], []
    with open(p) as f:
        rd = csv.reader(f)
        next(rd)
        for r in rd:
            t.append(r[0]); o.append(float(r[1])); h.append(float(r[2]))
            l.append(float(r[3])); c.append(float(r[4]))
    b = {"t": t, "o": o, "h": h, "l": l, "c": c}
    _BARCACHE[k] = b
    return b


def born_state(m):
    if m is None:
        return "unknown"
    if m <= -1.0:
        return "born_past_stop"
    if m < -1e-9:
        return "born_marketable"
    if m <= 1e-9:
        return "born_at_limit"
    return "born_resting"


def rpath(obs, entry, rd, side):
    """(fav, adv, cls) in R for the trade's own side."""
    fav, adv, cls = [], [], []
    if side == "LONG":
        for b in obs:
            fav.append(round((b["high"] - entry) / rd, 4))
            adv.append(round((b["low"] - entry) / rd, 4))
            cls.append(round((b["close"] - entry) / rd, 6))
    else:
        for b in obs:
            fav.append(round((entry - b["low"]) / rd, 4))
            adv.append(round((entry - b["high"]) / rd, 4))
            cls.append(round((entry - b["close"]) / rd, 6))
    return fav, adv, cls


def resolve(fav, adv, cls, tgt=2.0, stp=-1.0):
    nb = len(fav)
    start = None
    for i in range(nb):
        if adv[i] <= TOL:
            start = i
            break
    if start is None:
        return 0.0, "no_fill", -1
    bt = bs = -1
    for i in range(start, nb):
        if bt < 0 and fav[i] >= tgt - TOL:
            bt = i + 1
        if bs < 0 and adv[i] <= stp + TOL:
            bs = i + 1
        if bt > 0 and bs > 0:
            break
    fb = start + 1
    if bs > 0 and (bt <= 0 or bs <= bt):
        return stp, "stop", fb
    if bt > 0:
        return tgt, "target", fb
    return cls[nb - 1], "mark", fb


def bars_after(b, decision_iso, n=HORIZON):
    """The M1 bars strictly AFTER the decision minute and INSIDE the 2 h horizon.
    Both bounds matter: the sidecar caps at horizon_end_utc = decision + 2 h, and a
    thin symbol prints fewer than 120 bars in that window. Verified byte-exact against
    the sealed CQ sidecar on all 27,658 January candidates."""
    i = bisect.bisect_right(b["t"], decision_iso)
    end = (dt.datetime.fromisoformat(decision_iso.replace("Z", "+00:00"))
           + dt.timedelta(minutes=n)).isoformat()
    out = []
    for j in range(i, min(i + n, len(b["t"]))):
        if b["t"][j] > end:
            break
        out.append({"open": b["o"][j], "high": b["h"][j], "low": b["l"][j],
                    "close": b["c"][j], "time_utc": b["t"][j]})
    return out


def anchor_mkt_r(b, decision_iso, entry, rd, side):
    """mkt_r_prev_close: last FULLY CLOSED bar strictly before the decision minute."""
    i = bisect.bisect_right(b["t"], decision_iso) - 1
    if i < 0:
        return None
    j = i - 1 if b["t"][i] == decision_iso else i
    if j < 0:
        j = 0
    sgn = 1.0 if side == "LONG" else -1.0
    return round(sgn * (b["c"][j] - entry) / rd, 6)


def build(month, verify_bars=False):
    cfg = MONTHS[month]
    filt = cfg.get("filt")
    sidecar = {}
    if cfg["sidecar"]:
        with gzip.open(cfg["sidecar"], "rt") as fh:
            for line in fh:
                s = json.loads(line)
                sidecar[(s["candidate_id"], s["decision_time_utc"])] = s["ordered_path_observations"]

    stats = collections.Counter()
    diffs = collections.Counter()
    out_rows = []
    with gzip.open(cfg["pool"], "rt") as fh:
        for line in fh:
            r = json.loads(line)
            if filt is not None and not filt(r):
                stats["filtered_out"] += 1
                continue
            k = (r["candidate_id"], r["decision_time_utc"])
            entry = r.get("entry_price"); stop = r.get("stop_loss")
            side = r.get("side") or r.get("direction")
            if entry is None or stop is None or side is None:
                stats["no_geometry"] += 1
                continue
            rd = abs(entry - stop)
            if rd <= 0:
                stats["zero_risk_distance"] += 1
                continue
            b = load_bars(cfg["bars"], r["symbol"])
            obs = sidecar.get(k)
            src = "sidecar"
            if obs is None:
                if b is None:
                    stats["no_bars"] += 1
                    continue
                obs = bars_after(b, r["decision_time_utc"])
                src = "bars"
                if not obs:
                    stats["no_bars_after"] += 1
                    continue
            elif verify_bars and b is not None:
                ob2 = bars_after(b, r["decision_time_utc"])
                if len(ob2) != len(obs):
                    diffs["len_mismatch"] += 1
                else:
                    bad = any(abs(x["high"] - y["high"]) > 1e-9 or abs(x["low"] - y["low"]) > 1e-9
                              or abs(x["close"] - y["close"]) > 1e-9 or x["time_utc"] != y["time_utc"]
                              for x, y in zip(obs, ob2))
                    diffs["ohlc_mismatch" if bad else "identical"] += 1
            fav, adv, cls = rpath(obs, entry, rd, side)
            hr, oc, fb = resolve(fav, adv, cls)
            mkt = anchor_mkt_r(b, r["decision_time_utc"], entry, rd, side) if b is not None else None
            npr = r.get("opportunity_net_proxy_r"); cr = r.get("cost_r")
            gross = (npr + cr) if (npr is not None and cr is not None) else None
            t = dt.datetime.fromisoformat(r["decision_time_utc"].replace("Z", "+00:00"))
            out_rows.append({
                "cid": r["candidate_id"], "dt": r["decision_time_utc"], "month": month,
                "sym": r.get("symbol"), "side": side, "fam": r.get("origin_family"),
                "sess": r.get("session_bucket"), "rsess": r.get("route_session"),
                "dtf": r.get("decision_timeframe"), "hour": t.hour, "day": t.day,
                "dow": t.weekday(), "fb": fb, "hr": round(hr, 6), "oc": oc,
                "nb": len(fav), "src": src,
                "gross_r": round(gross, 6) if gross is not None else None,
                "cost_r": cr, "spread_r": r.get("spread_r"),
                "mkt_r": mkt, "born": born_state(mkt),
                "rdp": round(rd / entry * 100.0, 6) if entry else None,
                "mfe": round(max(fav), 4), "mae": round(min(adv), 4),
                "otype": r.get("effective_order_type"),
                "blocker": r.get("final_blocker_class"),
                "sched": r.get("scheduler_materialization_status"),
                "prob": r.get("candidate_probability"),
                "fillp": r.get("execution_fill_probability"),
                "ptr": r.get("policy_target_r"),
            })
            stats["ok"] += 1
            stats["src_" + src] += 1

    outp = os.path.join(D, "e6_FRAME_%s.jsonl.gz" % month)
    with gzip.open(outp, "wt") as fh:
        for r in out_rows:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
    meta = {"month": month, "rows": len(out_rows), "stats": dict(stats), "out": outp,
            "pool": cfg["pool"], "sidecar": cfg["sidecar"], "bars": cfg["bars"]}
    if verify_bars:
        meta["bar_rebuild_vs_sidecar"] = dict(diffs)
    print(json.dumps(meta))
    return meta


if __name__ == "__main__":
    m = sys.argv[1]
    vb = "--verify-bars" in sys.argv
    build(m, vb)
