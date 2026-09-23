"""w0-capture pass 3: the stale-limit / gap-through fill population.

Pass 2 measured that 36.4 % of filled January S0R0 rows are "fills" whose fill
bar never traded back to the limit price, and that removing them moves the pool
gross from -0.2414 to -0.0447 R/trade.

This pass answers the three questions that decide what that is:

  Q1  Does the ENGINE actually book those rows?  (reconcile them separately)
  Q2  Was the limit already on the wrong side of the market AT THE DECISION BAR
      -- i.e. born un-fillable-as-a-limit -- or did the market gap after?
  Q3  What is the book if the "limit; if it fills it fills, otherwise we do not
      trade" contract is honoured literally: the bar's range must CONTAIN the
      limit price (low <= entry <= high) for a resting limit to fill?

`_entry_touched` (wave4r_replay_microstructure.py:1162-1183) is a one-sided
range test: LONG -> low <= entry, SHORT -> high >= entry.  For a SHORT sell
limit that sits BELOW the market the test is satisfied by every bar, including
one whose entire range is far above the limit, and the oracle then books the
fill AT the limit price.
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
OUT = Path(__file__).resolve().parent / "W0CAP_STALE_LIMIT_V1.json"

WALL_MIN = 120
MAXH = 14400
TOL = 0.02


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
        "p95": float(np.percentile(a, 95)),
        "max": float(a.max()),
    }


def book(vals):
    a = np.asarray([v for v in vals if v is not None], float)
    if a.size == 0:
        return {"n": 0}
    w, l = a[a > 0], a[a <= 0]
    be = None
    if w.size and l.size:
        be = float(abs(l.mean()) / (w.mean() + abs(l.mean())))
    return {
        "n": int(a.size),
        "gross_mean_R": float(a.mean()),
        "win_rate": float(w.size / a.size),
        "mean_winner_R": float(w.mean()) if w.size else None,
        "mean_loser_R": float(l.mean()) if l.size else None,
        "payoff": float(w.mean() / abs(l.mean())) if w.size and l.size else None,
        "breakeven_win_rate": be,
        "win_rate_minus_breakeven_pp": (
            float((w.size / a.size - be) * 100.0) if be is not None else None
        ),
    }


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
        if i1 <= i0 or i0 == 0:
            continue
        # the decision bar: last closed bar at or before asof
        ref_close = float(b["c"][i0 - 1])
        tt, hi, lo, cl = t[i0:i1], b["h"][i0:i1], b["l"][i0:i1], b["c"][i0:i1]
        if side == "LONG":
            fav = (hi - entry) / risk
            adv = (lo - entry) / risk
            loose = lo <= entry              # engine rule
            contains = (lo <= entry) & (hi >= entry)
            # a LONG buy-limit is stale/marketable if the market is already BELOW it
            born_marketable = ref_close <= entry
        else:
            fav = (entry - lo) / risk
            adv = (entry - hi) / risk
            loose = hi >= entry              # engine rule
            contains = (lo <= entry) & (hi >= entry)
            born_marketable = ref_close >= entry
        clr = (cl - entry) / risk if side == "LONG" else (entry - cl) / risk
        nwall = int(np.searchsorted(tt, wall, side="right"))

        stop_m = adv <= -1.0
        tgt_m = fav >= target_r

        def resolve(f, hi_i):
            if f < 0 or hi_i <= f:
                return None
            js = first_true(stop_m[f:hi_i])
            jt = first_true(tgt_m[f:hi_i])
            if js < 0 and jt < 0:
                return (float(min(max(clr[hi_i - 1], -1.0), target_r)), "mark_at_horizon")
            if js >= 0 and (jt < 0 or js < jt):
                return (-1.0, "stop_1R")
            if jt >= 0 and (js < 0 or jt < js):
                return (float(target_r), "target")
            return (-1.0, "same_bar_conservative_stop")

        f_loose = first_true(loose[:nwall])
        f_strict = first_true(contains[:nwall])
        rec = {
            "cid": row["candidate_id"],
            "fam": row.get("origin_family"),
            "sym": row["symbol"],
            "blocker": row.get("final_blocker_class"),
            "net": row.get("opportunity_net_proxy_r"),
            "cost": row.get("cost_r"),
            "marketable_flag": row.get("limit_marketable_at_decision"),
            "born_marketable": bool(born_marketable),
            "ref_close_distance_R": float(
                (ref_close - entry) / risk if side == "LONG" else (entry - ref_close) / risk
            ),
            "target_r": target_r,
            "f_loose": f_loose,
            "f_strict": f_strict,
        }
        if f_loose >= 0:
            rec["gap_through"] = bool(fav[f_loose] < 0.0)
            rec["fill_bar_fav_r"] = float(fav[f_loose])
            rec["engine_wall"] = resolve(f_loose, nwall)
            rec["engine_unbounded"] = resolve(f_loose, tt.size)
        if f_strict >= 0:
            rec["strict_wall"] = resolve(f_strict, nwall)
            rec["strict_unbounded"] = resolve(f_strict, tt.size)
            rec["strict_fill_delay_min"] = float((tt[f_strict] - a_s) / 60.0)
        recs.append(rec)

    ok = [r for r in recs if r.get("f_loose", -1) >= 0]
    gap = [r for r in ok if r.get("gap_through")]
    clean = [r for r in ok if not r.get("gap_through")]

    out = {
        "schema": "gtos-w0cap-stale-limit-v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "billed": False,
        "april_may_packs_read": False,
        "february_economics_read": False,
        "broker_live_authority": False,
        "pool_rows": len(rows),
        "engine_filled": len(ok),
    }

    # ------------------------------------------------------------------- Q1
    def rate(rs):
        n = m = 0
        for r in rs:
            if r.get("net") is None or r.get("cost") is None or not r.get("engine_wall"):
                continue
            n += 1
            g = float(r["net"]) + float(r["cost"])
            m += abs(r["engine_wall"][0] - g) <= TOL
        return {"n": n, "matched": m, "rate": (m / n) if n else None}

    out["Q1_engine_books_these_rows"] = {
        "reconcile_all": rate(ok),
        "reconcile_gap_through_rows": rate(gap),
        "reconcile_clean_rows": rate(clean),
    }

    # ------------------------------------------------------------------- Q2
    bm = [r for r in ok if r["born_marketable"]]
    out["Q2_born_on_the_wrong_side_of_the_market"] = {
        "n_born_marketable": len(bm),
        "share_of_filled": len(bm) / len(ok),
        "share_of_gap_rows_born_marketable": (
            sum(1 for r in gap if r["born_marketable"]) / len(gap) if gap else None
        ),
        "share_of_clean_rows_born_marketable": (
            sum(1 for r in clean if r["born_marketable"]) / len(clean) if clean else None
        ),
        "pool_field_limit_marketable_at_decision_values": {
            str(k): sum(1 for r in ok if r["marketable_flag"] == k)
            for k in {r["marketable_flag"] for r in ok}
        },
        "decision_bar_close_distance_R_all": dist([r["ref_close_distance_R"] for r in ok]),
        "decision_bar_close_distance_R_gap_rows": dist(
            [r["ref_close_distance_R"] for r in gap]
        ),
        "book_born_marketable": book([r["engine_wall"][0] for r in bm if r.get("engine_wall")]),
        "book_born_resting": book(
            [r["engine_wall"][0] for r in ok if not r["born_marketable"] and r.get("engine_wall")]
        ),
    }

    # ------------------------------------------------------------------- Q3
    strict_ok = [r for r in recs if r.get("f_strict", -1) >= 0]
    out["Q3_strict_limit_contract"] = {
        "n_fills_engine_rule": len(ok),
        "n_fills_strict_rule": len(strict_ok),
        "fill_rate_engine": len(ok) / len(recs),
        "fill_rate_strict": len(strict_ok) / len(recs),
        "rows_engine_fills_but_strict_does_not": sum(
            1 for r in recs if r.get("f_loose", -1) >= 0 and r.get("f_strict", -1) < 0
        ),
        "book_engine_rule_wall": book([r["engine_wall"][0] for r in ok if r.get("engine_wall")]),
        "book_strict_rule_wall_filled_only": book(
            [r["strict_wall"][0] for r in strict_ok if r.get("strict_wall")]
        ),
        "book_strict_rule_wall_unfilled_as_zero": book(
            [
                (r["strict_wall"][0] if r.get("strict_wall") else 0.0)
                for r in recs
                if r.get("strict_wall") or r.get("f_strict", -1) < 0
            ]
        ),
        "book_engine_rule_unbounded": book(
            [r["engine_unbounded"][0] for r in ok if r.get("engine_unbounded")]
        ),
        "book_strict_rule_unbounded_filled_only": book(
            [r["strict_unbounded"][0] for r in strict_ok if r.get("strict_unbounded")]
        ),
        "strict_fill_delay_minutes": dist(
            [r.get("strict_fill_delay_min") for r in strict_ok]
        ),
    }

    # ---------------------------------------------------------- headline books
    out["books"] = {
        "ALL_engine_wall": book([r["engine_wall"][0] for r in ok if r.get("engine_wall")]),
        "GAP_engine_wall": book([r["engine_wall"][0] for r in gap if r.get("engine_wall")]),
        "CLEAN_engine_wall": book([r["engine_wall"][0] for r in clean if r.get("engine_wall")]),
        "CLEAN_unbounded": book(
            [r["engine_unbounded"][0] for r in clean if r.get("engine_unbounded")]
        ),
        "GAP_unbounded": book([r["engine_unbounded"][0] for r in gap if r.get("engine_unbounded")]),
        "ALL_unbounded": book([r["engine_unbounded"][0] for r in ok if r.get("engine_unbounded")]),
    }

    # -------------------------------------------------- per family, clean only
    fams = sorted({r.get("fam") or "?" for r in ok})
    out["per_family_clean_vs_gap"] = {}
    for fm in fams:
        g = [r for r in gap if (r.get("fam") or "?") == fm]
        c = [r for r in clean if (r.get("fam") or "?") == fm]
        out["per_family_clean_vs_gap"][fm] = {
            "n_gap": len(g),
            "n_clean": len(c),
            "gap_share": len(g) / (len(g) + len(c)) if (g or c) else None,
            "clean_wall": book([r["engine_wall"][0] for r in c if r.get("engine_wall")]),
            "clean_unbounded": book(
                [r["engine_unbounded"][0] for r in c if r.get("engine_unbounded")]
            ),
            "gap_wall": book([r["engine_wall"][0] for r in g if r.get("engine_wall")]),
        }

    # ------------------------------- net-of-cost view (frozen cost, as recorded)
    def netbook(rs, key):
        v = []
        for r in rs:
            if r.get(key) and r.get("cost") is not None:
                v.append(r[key][0] - float(r["cost"]))
        return book(v)

    out["net_of_frozen_cost"] = {
        "ALL_engine_wall": netbook(ok, "engine_wall"),
        "CLEAN_engine_wall": netbook(clean, "engine_wall"),
        "CLEAN_unbounded": netbook(clean, "engine_unbounded"),
    }

    OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=str))
    print(
        json.dumps(
            {
                k: out[k]
                for k in ("Q1_engine_books_these_rows", "Q2_born_on_the_wrong_side_of_the_market", "Q3_strict_limit_contract", "books")
            },
            indent=1,
            default=str,
        )
    )
    print("wrote", OUT)


if __name__ == "__main__":
    main()
