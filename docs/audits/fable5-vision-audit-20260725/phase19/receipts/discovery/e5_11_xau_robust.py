"""e5 step 11 — robustness of the one surviving cohort.

Per trading day, per family, per session, per hour; concentration in the tail; sensitivity
to an extra exit-slippage charge; and the pseudo-replication control (w0-F1: candidate_id
is not a primary key, so a repeated setup can inflate a cohort).
Writes E5_XAU_ROBUST_V1.json
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)

OUT = os.path.join(D, "E5_XAU_ROBUST_V1.json")
MONTHS = ["january", "february", "march"]
SYM = "XAUUSD"


def load(m, sym=None):
    rows = []
    with gzip.open(os.path.join(D, "e5_%s_WS_V1.jsonl.gz" % m), "rt") as f:
        for ln in f:
            r = json.loads(ln)
            if sym and r["symbol"] != sym:
                continue
            mk = r["mkt_r_prev_close"]
            if mk is not None and mk <= -1.0:
                continue
            adv = r["adv"]
            fb = next((i for i in range(len(adv)) if adv[i] <= 1e-12), None)
            if fb is None:
                continue
            sp = float(r.get("spread_r") or 0); cm = float(r.get("commission_r") or 0)
            sw = float(r.get("swap_cost_r") or 0); sl = float(r.get("expected_slippage_r") or 0)
            rows.append({"fav": r["fav"], "adv": adv, "cls": r["cls"], "fb": fb,
                         "tgt": (r.get("policy_target_r") or 2.0),
                         "cid": r["candidate_id"], "dt": r["decision_time_utc"],
                         "day": r["decision_time_utc"][:10], "hour": r["decision_time_utc"][11:13],
                         "fam": r.get("origin_family"), "sess": r.get("session_bucket"),
                         "side": r.get("side"), "sp": sp, "cm": cm, "sww": sw, "sl": sl,
                         "c73": sp / 7.3 + cm + sw + sl, "cfr": sp + cm + sw + sl})
    return rows


def walk(e, trail):
    fav, adv, cls, fb, tgt = e["fav"], e["adv"], e["cls"], e["fb"], e["tgt"]
    stop = -1.0; peak = -1e18
    for i in range(fb, len(fav)):
        f, a = fav[i], adv[i]
        if a <= stop + 1e-12:
            return stop
        if f >= tgt - 1e-12:
            return tgt
        if f > peak:
            peak = f
        if trail is not None and peak >= trail:
            stop = max(stop, peak - trail)
    return cls[-1]


def stats(sub, trail=0.10, extra_slip=0.0):
    n = len(sub)
    v = [walk(e, trail) - e["c73"] - extra_slip for e in sub]
    v.sort()
    tot = sum(v)
    top1 = sum(v[-max(1, n // 100):])
    top5 = sum(v[-max(1, n // 20):])
    return {"n": n, "mean": round(tot / n, 6), "median": round(v[n // 2], 6),
            "pos_pct": round(100 * sum(1 for x in v if x > 0) / n, 2),
            "top1pct_share_of_total": (round(100 * top1 / tot, 2) if abs(tot) > 1e-9 else None),
            "top5pct_share_of_total": (round(100 * top5 / tot, 2) if abs(tot) > 1e-9 else None)}


res = {"schema": "gtos.e5.xau_robust.v1", "symbol": SYM}
for m in MONTHS:
    sub = load(m, SYM)
    mm = {"n": len(sub)}
    for tr in (0.10, 0.25):
        mm["t%.2f" % tr] = stats(sub, tr)
        mm["t%.2f_extra_slip_0p02" % tr] = stats(sub, tr, 0.02)
        mm["t%.2f_extra_slip_0p05" % tr] = stats(sub, tr, 0.05)
        mm["t%.2f_frozen_cost" % tr] = {
            "mean": round(sum(walk(e, tr) - e["cfr"] for e in sub) / len(sub), 6)}
    # per day
    days = {}
    for e in sub:
        days.setdefault(e["day"], []).append(e)
    dd = {d: round(sum(walk(e, 0.10) - e["c73"] for e in s) / len(s), 6) for d, s in sorted(days.items())}
    mm["per_day_t010"] = dd
    mm["days"] = len(dd)
    mm["days_positive"] = sum(1 for v in dd.values() if v > 0)
    # per family / session / hour / side
    for lab, kf in (("by_family", lambda e: e["fam"]), ("by_session", lambda e: e["sess"]),
                    ("by_hour", lambda e: e["hour"]), ("by_side", lambda e: e["side"])):
        g = {}
        grp = {}
        for e in sub:
            k = kf(e)
            if k:
                grp.setdefault(str(k), []).append(e)
        for k, s in grp.items():
            if len(s) < 40:
                continue
            g[k] = stats(s, 0.10)
        mm[lab] = dict(sorted(g.items(), key=lambda kv: -kv[1]["mean"]))
    # pseudo-replication control
    seen = {}
    for e in sub:
        seen.setdefault(e["cid"], []).append(e)
    firsts = [min(s, key=lambda e: e["dt"]) for s in seen.values()]
    mm["dedup"] = {"distinct_cid": len(seen), "rows": len(sub),
                   "repeat_rows_pct": round(100 * (len(sub) - len(seen)) / len(sub), 3),
                   "first_emission_only_t010": stats(firsts, 0.10)}
    res[m] = mm
    print("%-9s n=%4d | t0.10 %+0.5f (pos %.1f%%, med %+0.4f, top5%%=%s%% of total) | "
          "+slip0.02 %+0.5f | +slip0.05 %+0.5f | frozen %+0.5f | days %d/%d positive | dedup n=%d %+0.5f"
          % (m, mm["n"], mm["t0.10"]["mean"], mm["t0.10"]["pos_pct"], mm["t0.10"]["median"],
             mm["t0.10"]["top5pct_share_of_total"], mm["t0.10_extra_slip_0p02"]["mean"],
             mm["t0.10_extra_slip_0p05"]["mean"], mm["t0.10_frozen_cost"]["mean"],
             mm["days_positive"], mm["days"], mm["dedup"]["first_emission_only_t010"]["n"],
             mm["dedup"]["first_emission_only_t010"]["mean"]))

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT)
