"""Build the January e-stack base table: one row per candidate carrying every quantity
the combined scorer needs, so the 64-arm enumeration is pure filtering afterwards.

Inputs   w0_WORKING_SET.jsonl.gz + w0_R_PATHS.jsonl.gz + w0cap2_DECISION_ANCHOR_V1.jsonl.gz
Output   e_JAN_BASE_V1.jsonl.gz
"""
import gzip, json, os, sys, time

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e_lib  # noqa: E402

TICK = json.load(open(f"{D}/L10X_TICK_SPREAD_V1.json"))
LIVE = json.load(open(f"{D}/L10X_LIVE_COST_PRICEUNITS_V1.json"))

t0 = time.time()
# ---- anchors (born state, no look-ahead: close of the M1 bar stamped decision-1min)
anch = {}
for line in gzip.open(f"{D}/w0cap2_DECISION_ANCHOR_V1.jsonl.gz", "rt"):
    a = json.loads(line)
    anch[(a["candidate_id"], a["decision_time_utc"])] = a["mkt_r_prev_close"]

# ---- pool rows
pool = {}
for line in gzip.open(f"{D}/w0_WORKING_SET.jsonl.gz", "rt"):
    r = json.loads(line)
    pool[(r["candidate_id"], r["decision_time_utc"])] = r
print("pool", len(pool), "anchored", len(anch), round(time.time() - t0, 1), flush=True)


def born(m):
    if m is None:
        return "unanchored"
    return ("born_past_stop" if m <= -1.0 else
            "born_marketable" if m < 0.0 else
            "born_at_limit" if m == 0.0 else "born_resting")


out = gzip.open(f"{D}/e_JAN_BASE_V1.jsonl.gz", "wt")
nw = 0
miss_cost = 0
for line in gzip.open(f"{D}/w0_R_PATHS.jsonl.gz", "rt"):
    rp = json.loads(line)
    k = (rp["candidate_id"], rp["decision_time_utc"])
    r = pool[k]
    fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
    s1 = e_lib.first_touch(adv, 0)
    s2 = e_lib.first_touch(adv, 1)
    m = anch.get(k)
    sym = r["symbol"]
    rc = e_lib.real_cost_parts(sym, r["entry_price"], r["risk_distance"], TICK, LIVE)
    if rc is None:
        miss_cost += 1
        rc = (None, None, None)
    o = {
        "cid": rp["candidate_id"], "dt": rp["decision_time_utc"],
        "day": rp["decision_time_utc"][:10], "hour": int(rp["decision_time_utc"][11:13]),
        "symbol": sym, "side": r["side"], "family": r.get("origin_family"),
        "session": r.get("route_session"), "is_first": bool(r.get("is_first_emission")),
        "dup_count": r.get("setup_dup_count"),
        "risk_distance": r["risk_distance"], "entry_price": r["entry_price"],
        "rdp": r["risk_distance"] / r["entry_price"] if r["entry_price"] else None,
        "mkt_r": m, "born": born(m),
        "n_bars": len(fav), "t_first": (s1 + 1) if s1 is not None else None,
        "t_delay1": (s2 + 1) if s2 is not None else None,
        "mfe_r": r.get("mfe_r"), "mae_r": r.get("mae_r"), "r_end": r.get("r_at_path_end"),
        "gross_r": r["gross_r"],
        # cost bases
        "cost_frozen": r["expected_cost_r"], "spread_r": r["spread_r"],
        "commission_r": r.get("commission_r"), "swap_r": r.get("swap_cost_r"),
        "slip_r": r.get("expected_slippage_r"),
        "real_spread_r": rc[0], "real_comm_r": rc[1], "real_slip_r": rc[2],
        # belief / engine fields the conditioning levers use
        "efp": r.get("execution_fill_probability"), "prob": r.get("candidate_probability"),
        "ev_r": r.get("candidate_ev_r"), "blocker": r.get("final_blocker_class"),
        "sched": r.get("scheduler_materialization_status"),
    }
    o["cost_corr73"] = (o["spread_r"] / 7.3 + (o["commission_r"] or 0.0)
                        + (o["slip_r"] or 0.0) + (o["swap_r"] or 0.0))
    o["cost_true"] = (None if rc[0] is None else rc[0] + rc[1] + rc[2])
    for name, (tg, st, tr, mb, _) in e_lib.CONTRACTS.items():
        r1, x1, b1 = e_lib.walk(fav, adv, cls, s1, tg, st, tr, mb)
        r2, x2, b2 = e_lib.walk(fav, adv, cls, s2, tg, st, tr, mb)
        o["R_" + name] = round(r1, 8)
        o["X_" + name] = x1
        o["D_" + name] = round(r2, 8)   # patient-placement (wait 1 min, then rest)
    out.write(json.dumps(o) + "\n")
    nw += 1
out.close()
print("written", nw, "missing_true_cost", miss_cost, round(time.time() - t0, 1), flush=True)
json.dump({"rows": nw, "missing_true_cost": miss_cost,
           "contracts": list(e_lib.CONTRACTS),
           "seconds": round(time.time() - t0, 1)},
          open(f"{D}/e_JAN_BASE_BUILD_V1.json", "w"), indent=1)
