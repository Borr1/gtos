"""w0-capture pass 2: the wall, the fill, and the money on the table.

Pass 1 (w0cap_mfe_forensics.py) established that 89.7 % of the January S0R0 pool
reconciles to the PLAIN fixed-target walk with a 120-minute wall, and that the
`momentum_exhaustion` policy declared on 100 % of rows is not terminal authority
on an M1 path.

This pass measures, with the day-end cap applied consistently everywhere:

  1. FILL LIFE          expiry - fill_time.  The pending-ORDER expiry doubles as
                        the trade HORIZON (v4_timewarp...py:92468-92478), so a
                        limit that fills late gets a truncated trade.
  2. GAP-THROUGH FILLS  `_entry_touched` is a bar-range test, so a bar that gaps
                        clean through the limit counts as a fill and the trade
                        starts already underwater
                        (wave4r_replay_microstructure.py:1176-1183).
  3. STEP 4/5           MFE forensics with the wall applied correctly, split
                        before vs after the recorded exit.
  4. REPAIR ARMS        budget the horizon FROM THE FILL instead of from the
                        decision, and price each.
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import json
from pathlib import Path

import numpy as np

LANE_ROOT = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence"
    "/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
REPO = Path(__file__).resolve().parents[6]
POOL = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools"
    / "CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
)
M1_DIR = LANE_ROOT / "sources/bars/bridge_ftmo_m1_202601"
OUT = Path(__file__).resolve().parent / "W0CAP_WALL_FORENSICS_V1.json"

WALL_MIN = 120
FROM_FILL = [120, 240, 480, 1440]
MAXH = 14400


def load_bars():
    out = {}
    for path in sorted(M1_DIR.glob("*_M1.csv")):
        sym = path.name[: -len("_M1.csv")]
        ts, o, h, lo, c = [], [], [], [], []
        with path.open(newline="") as fh:
            for row in csv.DictReader(fh):
                ts.append(int(dt.datetime.fromisoformat(row["time"]).timestamp()))
                o.append(float(row["open"]))
                h.append(float(row["high"]))
                lo.append(float(row["low"]))
                c.append(float(row["close"]))
        t = np.asarray(ts, np.int64)
        k = np.argsort(t, kind="stable")
        out[sym] = {
            "t": t[k],
            "o": np.asarray(o)[k],
            "h": np.asarray(h)[k],
            "l": np.asarray(lo)[k],
            "c": np.asarray(c)[k],
        }
    return out


def first_true(m):
    if m.size == 0:
        return -1
    i = int(np.argmax(m))
    return i if bool(m[i]) else -1


def dist(v):
    a = np.asarray([x for x in v if x is not None], float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return {"n": 0}
    return {
        "n": int(a.size),
        "mean": float(a.mean()),
        "p05": float(np.percentile(a, 5)),
        "p25": float(np.percentile(a, 25)),
        "median": float(np.median(a)),
        "p75": float(np.percentile(a, 75)),
        "p90": float(np.percentile(a, 90)),
        "p95": float(np.percentile(a, 95)),
        "max": float(a.max()),
    }


def pct(a, b):
    return (a / b) if b else None


def main():
    bars = load_bars()
    rows = []
    with gzip.open(POOL, "rt") as fh:
        for line in fh:
            rows.append(json.loads(line))

    recs = []
    for row in rows:
        b = bars.get(row["symbol"])
        if b is None:
            continue
        side = str(row["side"]).upper()
        entry = float(row["entry_price"])
        stop = float(row["stop_loss"])
        tp1 = float(row["take_profit_1"])
        risk = abs(entry - stop)
        if risk <= 0:
            continue
        target_r = abs(tp1 - entry) / risk
        asof = dt.datetime.fromisoformat(row["decision_time_utc"])
        a_s = int(asof.timestamp())
        day_end = int(
            (
                dt.datetime(asof.year, asof.month, asof.day, tzinfo=dt.timezone.utc)
                + dt.timedelta(days=1)
            ).timestamp()
        )
        wall = min(a_s + WALL_MIN * 60, day_end)

        t = b["t"]
        i0 = int(np.searchsorted(t, a_s, side="right"))
        i1 = int(np.searchsorted(t, a_s + MAXH * 60, side="right"))
        if i1 <= i0:
            continue
        tt = t[i0:i1]
        hi, lo, cl = b["h"][i0:i1], b["l"][i0:i1], b["c"][i0:i1]
        if side == "LONG":
            fav = (hi - entry) / risk
            adv = (lo - entry) / risk
            touch = lo <= entry
        else:
            fav = (entry - lo) / risk
            adv = (entry - hi) / risk
            touch = hi >= entry
        clr = (cl - entry) / risk if side == "LONG" else (entry - cl) / risk

        nwall = int(np.searchsorted(tt, wall, side="right"))
        f = first_true(touch[:nwall])
        rec = {
            "cid": row["candidate_id"],
            "sym": row["symbol"],
            "fam": row.get("origin_family"),
            "blocker": row.get("final_blocker_class"),
            "target_r": target_r,
            "net": row.get("opportunity_net_proxy_r"),
            "cost": row.get("cost_r"),
            "filled": f >= 0,
        }
        if f < 0:
            recs.append(rec)
            continue

        rec["fill_min_after_decision"] = float((tt[f] - a_s) / 60.0)
        rec["life_min_to_wall"] = float((wall - tt[f]) / 60.0)
        rec["wall_truncated_by_day_end"] = bool(wall < a_s + WALL_MIN * 60)
        # gap-through: the fill bar never traded back to the limit price
        rec["fill_bar_fav_r"] = float(fav[f])
        rec["fill_bar_adv_r"] = float(adv[f])
        rec["gap_through_fill"] = bool(fav[f] < 0.0)

        stop_m = adv <= -1.0
        tgt_m = fav >= target_r

        def resolve(lo_i, hi_i, clamp=True):
            """engine PLAIN walk over bars [lo_i, hi_i)"""
            if hi_i <= lo_i:
                return None
            js = first_true(stop_m[lo_i:hi_i])
            jt = first_true(tgt_m[lo_i:hi_i])
            if js < 0 and jt < 0:
                v = float(clr[hi_i - 1])
                return (min(max(v, -1.0), target_r) if clamp else v, "mark_at_horizon")
            if js >= 0 and (jt < 0 or js < jt):
                return (-1.0, "stop_1R")
            if jt >= 0 and (js < 0 or jt < js):
                return (float(target_r), "target")
            return (-1.0, "same_bar_conservative_stop")

        rec["engine"] = resolve(f, nwall)
        # repair arm: budget the horizon FROM THE FILL
        for H in FROM_FILL:
            n = int(np.searchsorted(tt, int(tt[f]) + H * 60, side="right"))
            rec[f"fromfill_{H}"] = resolve(f, n)
        # unbounded (10 day) reference
        rec["unbounded"] = resolve(f, tt.size)

        # MFE inside the wall, and over the full path
        rec["mfe_in_wall"] = float(np.max(fav[f:nwall]))
        rec["mfe_full"] = float(np.max(fav[f:]))
        rec["mae_in_wall"] = float(np.min(adv[f:nwall]))
        js_all = first_true(stop_m[f:])
        rec["stopped_ever"] = js_all >= 0
        rec["mfe_before_first_stop"] = (
            float(np.max(fav[f : f + js_all + 1])) if js_all >= 0 else None
        )
        jt_all = first_true(tgt_m[f:])
        rec["min_to_target"] = None if jt_all < 0 else float((tt[f + jt_all] - tt[f]) / 60.0)
        rec["min_to_stop"] = None if js_all < 0 else float((tt[f + js_all] - tt[f]) / 60.0)
        recs.append(rec)

    ok = [r for r in recs if r.get("filled")]
    out = {
        "schema": "gtos-w0cap-wall-forensics-v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "billed": False,
        "april_may_packs_read": False,
        "february_economics_read": False,
        "broker_live_authority": False,
        "pool_rows": len(rows),
        "walkable_filled": len(ok),
        "not_filled_in_wall": len(recs) - len(ok),
    }

    # ---------------------------------------------------------- 1 FILL LIFE
    out["fill_life"] = {
        "fill_minutes_after_decision": dist([r["fill_min_after_decision"] for r in ok]),
        "trade_life_minutes_to_wall": dist([r["life_min_to_wall"] for r in ok]),
        "share_wall_truncated_by_day_end": pct(
            sum(1 for r in ok if r["wall_truncated_by_day_end"]), len(ok)
        ),
        "share_life_under_30min": pct(
            sum(1 for r in ok if r["life_min_to_wall"] < 30), len(ok)
        ),
        "share_life_under_60min": pct(
            sum(1 for r in ok if r["life_min_to_wall"] < 60), len(ok)
        ),
        "share_filled_at_first_bar": pct(
            sum(1 for r in ok if r["fill_min_after_decision"] <= 1.0), len(ok)
        ),
    }

    # ------------------------------------------------------ 2 GAP-THROUGH
    gp = [r for r in ok if r["gap_through_fill"]]
    ngp = [r for r in ok if not r["gap_through_fill"]]

    def bookof(rs, key):
        v = [r[key][0] for r in rs if r.get(key)]
        if not v:
            return {"n": 0}
        a = np.asarray(v)
        w, l = a[a > 0], a[a <= 0]
        return {
            "n": int(a.size),
            "gross_mean_R": float(a.mean()),
            "win_rate": float(w.size / a.size),
            "mean_winner_R": float(w.mean()) if w.size else None,
            "mean_loser_R": float(l.mean()) if l.size else None,
        }

    out["gap_through_fill"] = {
        "n": len(gp),
        "share_of_filled": pct(len(gp), len(ok)),
        "fill_bar_fav_r_dist_gap_rows": dist([r["fill_bar_fav_r"] for r in gp]),
        "engine_book_gap_rows": bookof(gp, "engine"),
        "engine_book_clean_rows": bookof(ngp, "engine"),
        "unbounded_book_gap_rows": bookof(gp, "unbounded"),
        "unbounded_book_clean_rows": bookof(ngp, "unbounded"),
        "R_per_pool_trade_if_gap_rows_never_traded": (
            float(
                np.mean([r["engine"][0] for r in ngp if r.get("engine")])
                - np.mean([r["engine"][0] for r in ok if r.get("engine")])
            )
        ),
    }

    # --------------------------------------------------- 3 STEP 4 / STEP 5
    sub = [
        r
        for r in ok
        if r.get("engine") and 0.0 < r["engine"][0] < r["target_r"] - 1e-9
    ]
    out["step4_sub_target_winners_own_walk"] = {
        "n": len(sub),
        "share_of_filled": pct(len(sub), len(ok)),
        "exit_reasons": {
            k: sum(1 for r in sub if r["engine"][1] == k)
            for k in {r["engine"][1] for r in sub}
        },
        "recorded_value_dist": dist([r["engine"][0] for r in sub]),
        "mfe_inside_wall_dist": dist([r["mfe_in_wall"] for r in sub]),
        "mfe_full_path_dist": dist([r["mfe_full"] for r in sub]),
        "mfe_reached_target_INSIDE_wall": [
            sum(1 for r in sub if r["mfe_in_wall"] >= r["target_r"]),
            pct(sum(1 for r in sub if r["mfe_in_wall"] >= r["target_r"]), len(sub)),
        ],
        "mfe_reached_target_AFTER_wall_only": [
            sum(
                1
                for r in sub
                if r["mfe_full"] >= r["target_r"] and r["mfe_in_wall"] < r["target_r"]
            ),
            pct(
                sum(
                    1
                    for r in sub
                    if r["mfe_full"] >= r["target_r"]
                    and r["mfe_in_wall"] < r["target_r"]
                ),
                len(sub),
            ),
        ],
        "mfe_never_reached_target_in_10d": [
            sum(1 for r in sub if r["mfe_full"] < r["target_r"]),
            pct(sum(1 for r in sub if r["mfe_full"] < r["target_r"]), len(sub)),
        ],
        "of_those_that_reach_after_the_wall_what_happens_unbounded": {
            k: sum(
                1
                for r in sub
                if r["mfe_full"] >= r["target_r"]
                and r["mfe_in_wall"] < r["target_r"]
                and r.get("unbounded")
                and r["unbounded"][1] == k
            )
            for k in ("target", "stop_1R", "mark_at_horizon", "same_bar_conservative_stop")
        },
        "minutes_from_fill_to_target_for_after_wall_rows": dist(
            [
                r["min_to_target"]
                for r in sub
                if r["mfe_full"] >= r["target_r"]
                and r["mfe_in_wall"] < r["target_r"]
                and r["min_to_target"] is not None
            ]
        ),
        "unbounded_value_of_the_sub_target_winner_population": (
            float(np.mean([r["unbounded"][0] for r in sub if r.get("unbounded")]))
        ),
        "engine_value_of_the_same_population": float(np.mean([r["engine"][0] for r in sub])),
    }

    stops = [r for r in ok if r.get("engine") and r["engine"][1] in ("stop_1R", "same_bar_conservative_stop")]
    mfe_b = [r["mfe_before_first_stop"] for r in stops if r["mfe_before_first_stop"] is not None]
    out["step5_full_stops_own_walk"] = {
        "n": len(stops),
        "share_of_filled": pct(len(stops), len(ok)),
        "mfe_before_first_stop_dist": dist(mfe_b),
        "share_mfe_before_stop_negative_gap_through": pct(
            sum(1 for v in mfe_b if v < 0), len(mfe_b)
        ),
        **{
            f"share_mfe_before_stop_ge_{thr}R": pct(
                sum(1 for v in mfe_b if v >= thr), len(mfe_b)
            )
            for thr in (0.25, 0.5, 1.0, 1.5, 2.0)
        },
        "R_per_POOL_trade_recoverable_if_every_stop_row_with_mfe_ge_1R_exited_at_1R": (
            float(sum(2.0 for v in mfe_b if v >= 1.0) / len(ok))
        ),
        "R_per_POOL_trade_recoverable_if_every_stop_row_with_mfe_ge_0.5R_exited_at_0.5R": (
            float(sum(1.5 for v in mfe_b if v >= 0.5) / len(ok))
        ),
    }

    # ------------------------------------------------------- 4 REPAIR ARMS
    arms = {}
    for key in ["engine"] + [f"fromfill_{H}" for H in FROM_FILL] + ["unbounded"]:
        arms[key] = bookof(ok, key)
        arms[key]["exit_reasons"] = {
            k: sum(1 for r in ok if r.get(key) and r[key][1] == k)
            for k in ("target", "stop_1R", "mark_at_horizon", "same_bar_conservative_stop")
        }
    base = arms["engine"]["gross_mean_R"]
    for key in arms:
        arms[key]["delta_vs_engine_R_per_trade"] = arms[key]["gross_mean_R"] - base
    out["repair_arms"] = arms

    # ------------------------------------------------------- family detail
    fams = sorted({r.get("fam") or "?" for r in ok})
    out["per_family"] = {}
    for fm in fams:
        rs = [r for r in ok if (r.get("fam") or "?") == fm]
        out["per_family"][fm] = {
            "n": len(rs),
            "engine": bookof(rs, "engine"),
            "fromfill_480": bookof(rs, "fromfill_480"),
            "unbounded": bookof(rs, "unbounded"),
            "gap_through_share": pct(sum(1 for r in rs if r["gap_through_fill"]), len(rs)),
        }

    OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=str))
    print(json.dumps({k: out[k] for k in ("fill_life", "repair_arms")}, indent=1, default=str))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
