"""h6 step 9 — ADVERSARIAL: re-price every paying cell at HOUR-TRUE broker spread.

The swarm's cost basis (e_lib.real_cost_parts) charges `spread_bps_median` — ONE flat
number per symbol. The same tick artifact carries `spread_bps_median_by_broker_hour`,
and inside a symbol that varies up to ~9x (the rollover hour). If the cells that pay sit
in cheap hours the flat model UNDERSTATES them; if they sit at the rollover it is
manufacturing the whole result. Nobody has checked.

Broker wall clock = America/New_York + 7 h (CLAUDE.md §4, VPS-measured over 81 weekly
session boundaries). That is UTC+2 in Jan/Feb/early-Mar 2026 and UTC+3 from 2026-03-08
(US DST). l10's artifacts used a flat +3; both are computed here.
"""
import json, os, sys, time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h6_lib as H  # noqa: E402
import e_lib  # noqa: E402

TICK = json.load(open(f"{D}/L10X_TICK_SPREAD_V1.json"))
NY = ZoneInfo("America/New_York")


def broker_hour_true(dt_iso, plus_min=0):
    t = datetime.fromisoformat(dt_iso).replace(tzinfo=timezone.utc) + timedelta(minutes=plus_min)
    return (t.astimezone(NY) + timedelta(hours=7)).hour


def main():
    t0 = time.time()
    P, M = H.load()
    import gzip
    rows = [json.loads(x) for x in gzip.open(f"{D}/h6_ATMKT_META.jsonl.gz", "rt") if x.strip()]
    n = len(rows)
    out = {}

    # ---- broker hours, both conventions
    for k in (0, 3, 5, 8, 10, 15, 20, 30):
        pass
    bh_true = np.array([broker_hour_true(r["dt"]) for r in rows], dtype=np.int32)
    bh_flat = np.array([(int(r["dt"][11:13]) + 3) % 24 for r in rows], dtype=np.int32)
    out["broker_hour_convention"] = {
        "agree_frac": float((bh_true == bh_flat).mean()),
        "n_disagree": int((bh_true != bh_flat).sum()),
        "per_month_agree": {m: float((bh_true[M["month"] == m] == bh_flat[M["month"] == m]).mean())
                            for m in ("2026-01", "2026-02", "2026-03")}}
    print("hour convention", json.dumps(out["broker_hour_convention"]), flush=True)

    # ---- hour-true spread in R
    sp_hour = np.full(n, np.nan)
    sp_flat_chk = np.full(n, np.nan)
    miss = 0
    for i, r in enumerate(rows):
        tk = TICK.get("ftmo:" + e_lib.TMAP.get(r["symbol"], r["symbol"]))
        if not tk:
            continue
        byh = tk.get("spread_bps_median_by_broker_hour") or {}
        v = byh.get(str(int(bh_true[i])))
        if v is None:
            v = tk["spread_bps_median"]
            miss += 1
        sp_hour[i] = v * r["entry_price"] / 1e4 / r["risk_distance"]
        sp_flat_chk[i] = tk["spread_bps_median"] * r["entry_price"] / 1e4 / r["risk_distance"]
    out["hours_missing_from_tick_table"] = miss
    ok = np.isfinite(sp_hour) & np.isfinite(M["spread_r"])
    out["flat_spread_reproduces"] = {
        "max_abs_diff": float(np.abs(sp_flat_chk[ok] - M["spread_r"][ok]).max()),
        "n": int(ok.sum())}

    cost_flat = M["cost_true"]
    cost_hour = sp_hour + M["comm_r"] + M["slip_r"]
    M2 = dict(M)
    M2["cost_true"] = cost_hour
    out["cost_basis"] = {
        "flat_mean": float(np.nanmean(cost_flat)), "hour_mean": float(np.nanmean(cost_hour)),
        "hour_over_flat": float(np.nanmean(cost_hour) / np.nanmean(cost_flat)),
        "frac_hour_gt_flat": float(np.nanmean(cost_hour > cost_flat + 1e-12)),
        "p50_ratio": float(np.nanmedian(cost_hour / cost_flat)),
        "p90_ratio": float(np.nanquantile(cost_hour / cost_flat, 0.90)),
        "p99_ratio": float(np.nanquantile(cost_hour / cost_flat, 0.99)),
        "max_ratio": float(np.nanmax(cost_hour / cost_flat))}
    print("cost basis", json.dumps(out["cost_basis"]), flush=True)

    # hour census of the cohort
    hz = {}
    for h in range(24):
        m = bh_true == h
        if not m.any():
            continue
        hz[str(h)] = {"n": int(m.sum()),
                      "cost_flat": float(np.nanmean(cost_flat[m])),
                      "cost_hour": float(np.nanmean(cost_hour[m])),
                      "ratio": float(np.nanmean(cost_hour[m]) / np.nanmean(cost_flat[m]))}
    out["per_broker_hour"] = hz

    # ---- re-price the cells that pay
    CELLS = [
        ("SWARM_k5_TRAIL025_ungated", dict(k=5, target=None, stop=-1.0, trail=0.25,
                                           maxbars=None), {}),
        ("k3_STOPONLY_bps<=0.6", dict(k=3, target=None, stop=-1.0, trail=None,
                                      maxbars=None), {"gate_bps": 0.6}),
        ("k3_STOPONLY_bps<=0.6_c0<=0.05", dict(k=3, target=None, stop=-1.0, trail=None,
                                               maxbars=None),
         {"gate_bps": 0.6, "entry_hi": 0.05}),
        ("k8_STOPONLY_bps<=0.6_|c0|<=0.10", dict(k=8, target=None, stop=-1.0, trail=None,
                                                 maxbars=None),
         {"gate_bps": 0.6, "entry_lo": -0.10, "entry_hi": 0.10}),
        ("k5_TRAIL025_gateR<=0.02", dict(k=5, target=None, stop=-1.0, trail=0.25,
                                         maxbars=None), {"gate_total": 0.02}),
        ("XAUUSD_k30_trail010_mb60", dict(k=30, target=None, stop=-1.0, trail=0.10,
                                          maxbars=60), {"symbols": ["XAUUSD"]}),
        ("GER40_k3_STOPONLY", dict(k=3, target=None, stop=-1.0, trail=None, maxbars=None),
         {"symbols": ["GER40"]}),
        ("US30_k3_STOPONLY", dict(k=3, target=None, stop=-1.0, trail=None, maxbars=None),
         {"symbols": ["US30_cash"]}),
        ("NAS100_k20_trail010", dict(k=20, target=None, stop=-1.0, trail=0.10, maxbars=None),
         {"symbols": ["NAS100"]}),
    ]
    res = {}
    for lab, cw, pw in CELLS:
        r, reason, _e, trd, c0 = H.walk_all(P, **cw)
        sel = H.population(M, trd, c0, **pw)
        a = H.score(r, M, sel, reason)
        selh = H.population(M2, trd, c0, **pw)
        b = H.score(r, M2, selh, reason)
        res[lab] = {"flat_cost": {k: (round(v, 6) if isinstance(v, float) else v)
                                  for k, v in a.items()},
                    "hour_true_cost": {k: (round(v, 6) if isinstance(v, float) else v)
                                       for k, v in b.items()},
                    "delta_net": round(b["net"] - a["net"], 6),
                    "delta_ratio_R": round((b["ratio_r"] or 0) - (a["ratio_r"] or 0), 4)}
        print(f"  {lab:<34} n {a['n']:>6}  net flat {a['net']:+.5f} -> hour {b['net']:+.5f}"
              f"   rr {a['ratio_r']:.2f} -> {b['ratio_r']:.2f}", flush=True)
    out["cells"] = res

    # ---- hour-aware GATE: does refusing expensive hours help?
    r, reason, _e, trd, c0 = H.walk_all(P, k=3, target=None, stop=-1.0, trail=None,
                                        maxbars=None)
    hg = []
    for cap in (None, 3.0, 2.0, 1.5, 1.2, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5):
        base = H.population(M2, trd, c0)
        if cap is not None:
            base &= (cost_hour * M["bpsfac"] <= cap + 1e-12)
        if base.sum() < 100:
            continue
        s = H.score(r, M2, base, reason)
        s["gate_hour_bps"] = cap
        s["symbols"] = sorted(set(M["symbol"][base].tolist()))
        for m in ("2026-01", "2026-02", "2026-03"):
            s2 = base & (M["month"] == m)
            if s2.sum():
                s["net_" + m[-2:]] = float((r[s2] - cost_hour[s2]).mean())
                s["n_" + m[-2:]] = int(s2.sum())
        hg.append({k: (round(v, 6) if isinstance(v, float) else v) for k, v in s.items()})
    out["hour_true_bps_gate_k3_STOPONLY"] = hg
    print("\n hour-true bps gate, k=3 STOPONLY:")
    for s in hg:
        print(f"   cap {str(s['gate_hour_bps']):>5}  n {s['n']:>6}  net {s['net']:+.5f}"
              f"  rr {s['ratio_r']:.2f}  rb {(s['ratio_bps'] or 0):.2f}"
              f"  mo {s.get('net_01',0):+.4f}/{s.get('net_02',0):+.4f}/{s.get('net_03',0):+.4f}")

    np.save(f"{D}/h6_cost_hour.npy", cost_hour)
    np.save(f"{D}/h6_broker_hour.npy", bh_true)
    json.dump(out, open(f"{D}/H6_HOURCOST_V1.json", "w"), indent=1)
    print("wrote H6_HOURCOST_V1.json", round(time.time() - t0, 1), flush=True)


if __name__ == "__main__":
    main()
