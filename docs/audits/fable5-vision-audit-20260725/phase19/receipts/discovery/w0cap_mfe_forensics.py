"""w0-capture lane: what closes a winning trade at +1.04 R when its target is 2 R?

Offline research tool. Reads only:
  * CJ re-clocked January S0R0 diagnostic pool (27,658 rows, true UTC)
  * the January M1 bar sources the sidecar was built from (sha-verified via manifest)

Never imports a broker module, never launches a replay, never writes into a sealed route.

Contracts implemented EXACTLY as read from source:

PLAIN (raw fixed target) -- v4_timewarp_simulated_live_research_loop.py
  * fill: first bar after asof whose LOW<=entry (LONG) / HIGH>=entry (SHORT)
    (wave4r_replay_microstructure.py:1162-1183 `_entry_touched`)
  * walk from the FILL BAR INCLUSIVE (wave4r_replay_microstructure.py:757-816)
  * stop_touched -> -1R; target_touched -> +target_r; both same bar -> -1R
  * neither before expiry -> close_mark = last bar close <= expiry, CLAMPED to
    [-1, target_r] (v4_timewarp...py:60349-60353, attach_close_mark :63323-63413)

MOMENTUM (selected execution policy replay, `momentum_exhaustion`)
  * dynamic_execution_policy.py:167-186 -> PolicySpec(final_target_r=2.0,
    trailing_trigger_r=1.0, giveback_close_r=0.4, stop_r=-1.0)
  * observations start STRICTLY AFTER the fill bar
    (v4_timewarp...py `selected_policy_replay_observations`, ts <= fill_time -> continue)
  * per bar, in order (dynamic_execution_policy.py:392-535):
      best_mfe = running max of high_r  (INCLUDES current bar)
      stop_hit (low_r <= stop_r)                       -> close -1
      final_hit (high_r >= 2.0)                        -> close +2.0
      giveback: best_mfe>=1.0 and low_r <= best_mfe-0.4 -> close best_mfe-0.4
  * path end -> mark to market at last close_r, NOT clamped

HORIZON
  expiry = min(asof + pending_expiry_minutes, day_start + 1 day)
  v4_timewarp_simulated_live_research_loop.py:92468-92478
  BASELINE_PENDING_EXPIRY_MINUTES=240, REPAIRED_PENDING_EXPIRY_MINUTES=120 (:377-378)
  The sidecar stamps horizon_end_utc = decision + 120 min, so S0R0 ran at 120.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import json
import os
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
OUT = Path(__file__).resolve().parent / "W0CAP_MFE_FORENSICS_V1.json"

ENGINE_HORIZON_MIN = 120
HORIZONS = [120, 240, 480, 1440, 4320, 14400]
TRIGGER_R = 1.0
GIVEBACK_R = 0.4
BIG = 1 << 60


def load_bars() -> dict[str, dict[str, np.ndarray]]:
    out: dict[str, dict[str, np.ndarray]] = {}
    for path in sorted(M1_DIR.glob("*_M1.csv")):
        sym = path.name[: -len("_M1.csv")]
        ts: list[int] = []
        o: list[float] = []
        h: list[float] = []
        lo: list[float] = []
        c: list[float] = []
        with path.open(newline="") as fh:
            rd = csv.DictReader(fh)
            for row in rd:
                ts.append(int(dt.datetime.fromisoformat(row["time"]).timestamp()))
                o.append(float(row["open"]))
                h.append(float(row["high"]))
                lo.append(float(row["low"]))
                c.append(float(row["close"]))
        arr_t = np.asarray(ts, dtype=np.int64)
        order = np.argsort(arr_t, kind="stable")
        out[sym] = {
            "t": arr_t[order],
            "o": np.asarray(o, dtype=np.float64)[order],
            "h": np.asarray(h, dtype=np.float64)[order],
            "l": np.asarray(lo, dtype=np.float64)[order],
            "c": np.asarray(c, dtype=np.float64)[order],
        }
    return out


def load_pool() -> list[dict]:
    rows = []
    with gzip.open(POOL, "rt") as fh:
        for line in fh:
            rows.append(json.loads(line))
    return rows


def first_true(mask: np.ndarray) -> int:
    idx = int(np.argmax(mask))
    return idx if mask.size and bool(mask[idx]) else -1


def walk(row: dict, bars: dict[str, dict[str, np.ndarray]]) -> dict | None:
    sym = row["symbol"]
    b = bars.get(sym)
    if b is None:
        return None
    side = str(row["side"]).upper()
    entry = float(row["entry_price"])
    stop = float(row["stop_loss"])
    tp1 = float(row["take_profit_1"])
    risk = abs(entry - stop)
    if risk <= 0:
        return None
    target_r = abs(tp1 - entry) / risk

    asof = dt.datetime.fromisoformat(row["decision_time_utc"])
    asof_s = int(asof.timestamp())
    day_end_s = int(
        (
            dt.datetime(asof.year, asof.month, asof.day, tzinfo=dt.timezone.utc)
            + dt.timedelta(days=1)
        ).timestamp()
    )

    t = b["t"]
    i0 = int(np.searchsorted(t, asof_s, side="right"))  # strictly after asof
    if i0 >= t.size:
        return None
    imax = int(np.searchsorted(t, asof_s + max(HORIZONS) * 60, side="right"))
    if imax <= i0:
        return None

    hi = b["h"][i0:imax]
    lo = b["l"][i0:imax]
    cl = b["c"][i0:imax]
    tt = t[i0:imax]

    if side == "LONG":
        fav_r = (hi - entry) / risk
        adv_r = (lo - entry) / risk
        touched = lo <= entry
    else:
        fav_r = (entry - lo) / risk
        adv_r = (entry - hi) / risk
        touched = hi >= entry
    close_r = (cl - entry) / risk if side == "LONG" else (entry - cl) / risk

    # the engine's own path window: fill must occur inside [asof, expiry_engine]
    exp_engine_s = min(asof_s + ENGINE_HORIZON_MIN * 60, day_end_s)
    n_engine = int(np.searchsorted(tt, exp_engine_s, side="right"))
    if n_engine <= 0:
        return None
    f = first_true(touched[:n_engine])
    if f < 0:
        return {"filled": False, "target_r": target_r, "symbol": sym}

    res: dict = {
        "filled": True,
        "symbol": sym,
        "target_r": target_r,
        "fill_idx": f,
        "fill_time_s": int(tt[f]),
        "bars_available": int(tt.size - f),
    }

    # ------------------------------------------------------------------ PLAIN
    stop_mask = adv_r <= -1.0
    tgt_mask = fav_r >= target_r
    for H in HORIZONS:
        exp_s = min(asof_s + H * 60, day_end_s) if H == ENGINE_HORIZON_MIN else (asof_s + H * 60)
        n = int(np.searchsorted(tt, exp_s, side="right"))
        if n <= f:
            res[f"plain_{H}"] = None
            continue
        sm = stop_mask[f:n]
        tm = tgt_mask[f:n]
        js = first_true(sm)
        jt = first_true(tm)
        if js < 0 and jt < 0:
            r = float(min(max(close_r[n - 1], -1.0), target_r))
            reason = "mark_at_horizon"
        elif js >= 0 and (jt < 0 or js < jt):
            r, reason = -1.0, "stop_1R"
        elif jt >= 0 and (js < 0 or jt < js):
            r, reason = float(target_r), "target"
        else:
            r, reason = -1.0, "same_bar_conservative_stop"
        res[f"plain_{H}"] = (r, reason)

    # --------------------------------------------------------------- MOMENTUM
    # observations start strictly after the fill bar
    for H in HORIZONS:
        exp_s = min(asof_s + H * 60, day_end_s) if H == ENGINE_HORIZON_MIN else (asof_s + H * 60)
        n = int(np.searchsorted(tt, exp_s, side="right"))
        s = f + 1
        if n <= s:
            res[f"mom_{H}"] = None
            continue
        fv = fav_r[s:n]
        av = adv_r[s:n]
        cr = close_r[s:n]
        runmax = np.maximum.accumulate(fv)
        m_stop = av <= -1.0
        m_tgt = fv >= 2.0
        m_give = (runmax >= TRIGGER_R) & (av <= (runmax - GIVEBACK_R))
        any_mask = m_stop | m_tgt | m_give
        j = first_true(any_mask)
        if j < 0:
            res[f"mom_{H}"] = (float(cr[-1]), "path_end_mark_to_market")
        elif m_stop[j]:
            res[f"mom_{H}"] = (-1.0, "stop_or_same_bar_conservative")
        elif m_tgt[j]:
            res[f"mom_{H}"] = (2.0, "final_target")
        else:
            res[f"mom_{H}"] = (float(runmax[j] - GIVEBACK_R), "giveback_close")

    # -------------------------------------------------------------- FORENSICS
    # MFE from the fill bar inclusive, over increasing windows
    for H in HORIZONS:
        exp_s = asof_s + H * 60
        n = int(np.searchsorted(tt, exp_s, side="right"))
        res[f"mfe_{H}"] = float(np.max(fav_r[f:n])) if n > f else None
        res[f"mae_{H}"] = float(np.min(adv_r[f:n])) if n > f else None

    # first touch of +1R, +2R, and of the -1R stop, in minutes since fill
    def first_min(mask: np.ndarray) -> float | None:
        j = first_true(mask[f:])
        return None if j < 0 else float((tt[f + j] - tt[f]) / 60.0)

    res["min_to_1R"] = first_min(fav_r >= 1.0)
    res["min_to_2R"] = first_min(fav_r >= 2.0)
    res["min_to_target"] = first_min(fav_r >= target_r)
    res["min_to_stop"] = first_min(adv_r <= -1.0)

    # MFE strictly BEFORE the first stop touch (money on the table, given back)
    js_all = first_true(stop_mask[f:])
    if js_all >= 0:
        res["mfe_before_stop"] = float(np.max(fav_r[f : f + js_all + 1]))
        res["mfe_strictly_before_stop_bar"] = (
            float(np.max(fav_r[f : f + js_all])) if js_all > 0 else float("nan")
        )
    else:
        res["mfe_before_stop"] = None
        res["mfe_strictly_before_stop_bar"] = None
    return res


def pct(a: int, b: int) -> float:
    return (a / b) if b else float("nan")


def dist(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    a = np.asarray(values, dtype=np.float64)
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    bars = load_bars()
    pool = load_pool()
    if args.limit:
        pool = pool[: args.limit]

    out: dict = {
        "schema": "gtos-w0cap-mfe-forensics-v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "pool_rows": len(pool),
        "m1_dir": str(M1_DIR),
        "billed": False,
        "april_may_packs_read": False,
        "february_economics_read": False,
        "broker_live_authority": False,
    }

    recs = []
    for row in pool:
        w = walk(row, bars)
        if w is None:
            recs.append(None)
            continue
        w["recorded_net"] = row.get("opportunity_net_proxy_r")
        w["cost_r"] = row.get("cost_r")
        w["family"] = row.get("origin_family")
        w["blocker"] = row.get("final_blocker_class")
        w["candidate_id"] = row.get("candidate_id")
        recs.append(w)

    ok = [r for r in recs if r is not None and r.get("filled")]
    nofill = [r for r in recs if r is not None and not r.get("filled")]
    missing = sum(1 for r in recs if r is None)
    out["walkable"] = len(ok)
    out["not_filled_in_engine_window"] = len(nofill)
    out["unwalkable"] = missing

    # -------------------------------------------------- RECONCILIATION
    rec_gross = []
    plain0 = []
    mom0 = []
    for r in ok:
        if r["recorded_net"] is None or r["cost_r"] is None:
            rec_gross.append(None)
            continue
        rec_gross.append(float(r["recorded_net"]) + float(r["cost_r"]))
    tol = 0.02
    n_match_plain = n_match_mom = n_match_either = n_match_neither = 0
    plain_only = mom_only = 0
    for r, g in zip(ok, rec_gross):
        if g is None:
            continue
        p = r.get(f"plain_{ENGINE_HORIZON_MIN}")
        m = r.get(f"mom_{ENGINE_HORIZON_MIN}")
        mp = p is not None and abs(p[0] - g) <= tol
        mm = m is not None and abs(m[0] - g) <= tol
        n_match_plain += mp
        n_match_mom += mm
        n_match_either += mp or mm
        n_match_neither += not (mp or mm)
        plain_only += mp and not mm
        mom_only += mm and not mp
    nrec = sum(1 for g in rec_gross if g is not None)
    out["reconciliation"] = {
        "tolerance_R": tol,
        "n_with_recorded": nrec,
        "match_plain_fixed_target": [n_match_plain, pct(n_match_plain, nrec)],
        "match_momentum_exhaustion": [n_match_mom, pct(n_match_mom, nrec)],
        "match_either": [n_match_either, pct(n_match_either, nrec)],
        "match_neither": [n_match_neither, pct(n_match_neither, nrec)],
        "plain_only": [plain_only, pct(plain_only, nrec)],
        "momentum_only": [mom_only, pct(mom_only, nrec)],
    }

    # -------------------------------------------------- ARM BOOKS
    def book(key: str, H: int) -> dict:
        vals = [r[f"{key}_{H}"][0] for r in ok if r.get(f"{key}_{H}") is not None]
        if not vals:
            return {"n": 0}
        a = np.asarray(vals)
        w = a[a > 0]
        l = a[a <= 0]
        reasons: dict[str, int] = {}
        for r in ok:
            v = r.get(f"{key}_{H}")
            if v is not None:
                reasons[v[1]] = reasons.get(v[1], 0) + 1
        return {
            "n": int(a.size),
            "gross_mean_R": float(a.mean()),
            "win_rate": float(w.size / a.size),
            "mean_winner_R": float(w.mean()) if w.size else None,
            "mean_loser_R": float(l.mean()) if l.size else None,
            "payoff": float(w.mean() / abs(l.mean())) if w.size and l.size else None,
            "exit_reasons": reasons,
        }

    out["arms"] = {}
    for H in HORIZONS:
        out["arms"][f"PLAIN_{H}m"] = book("plain", H)
        out["arms"][f"MOMENTUM_{H}m"] = book("mom", H)

    recorded_vals = [g for g in rec_gross if g is not None]
    a = np.asarray(recorded_vals)
    w = a[a > 0]
    l = a[a <= 0]
    out["arms"]["RECORDED_ENGINE"] = {
        "n": int(a.size),
        "gross_mean_R": float(a.mean()),
        "win_rate": float(w.size / a.size),
        "mean_winner_R": float(w.mean()),
        "mean_loser_R": float(l.mean()),
        "payoff": float(w.mean() / abs(l.mean())),
    }

    # ------------------------------------- STEP 4: SUB-TARGET WINNERS
    sub = []
    for r, g in zip(ok, rec_gross):
        if g is None:
            continue
        tr = r["target_r"]
        if 0.0 < g < tr - 1e-9:
            sub.append((r, g))
    out["step4_sub_target_winners"] = {"n": len(sub)}
    if sub:
        s4: dict = {"n": len(sub)}
        s4["recorded_gross_dist"] = dist([g for _, g in sub])
        for H in HORIZONS:
            mfes = [r[f"mfe_{H}"] for r, _ in sub if r.get(f"mfe_{H}") is not None]
            s4[f"mfe_{H}m"] = dist(mfes)
            reach2 = sum(1 for v in mfes if v >= 2.0)
            reachT = sum(
                1
                for (r, _) in sub
                if r.get(f"mfe_{H}") is not None and r[f"mfe_{H}"] >= r["target_r"]
            )
            s4[f"mfe_ge_2R_within_{H}m"] = [reach2, pct(reach2, len(mfes))]
            s4[f"mfe_ge_target_within_{H}m"] = [reachT, pct(reachT, len(mfes))]
        # before vs after the engine wall
        before = sum(
            1
            for r, _ in sub
            if r.get(f"mfe_{ENGINE_HORIZON_MIN}") is not None
            and r[f"mfe_{ENGINE_HORIZON_MIN}"] >= r["target_r"]
        )
        after_only = sum(
            1
            for r, _ in sub
            if r.get("mfe_14400") is not None
            and r["mfe_14400"] >= r["target_r"]
            and (
                r.get(f"mfe_{ENGINE_HORIZON_MIN}") is None
                or r[f"mfe_{ENGINE_HORIZON_MIN}"] < r["target_r"]
            )
        )
        never = len(sub) - before - after_only
        s4["target_reached_before_engine_wall"] = [before, pct(before, len(sub))]
        s4["target_reached_only_after_engine_wall"] = [after_only, pct(after_only, len(sub))]
        s4["target_never_reached_within_10d"] = [never, pct(never, len(sub))]
        s4["min_to_target_dist_for_after_wall"] = dist(
            [
                r["min_to_target"]
                for r, _ in sub
                if r.get("min_to_target") is not None and r["min_to_target"] > ENGINE_HORIZON_MIN
            ]
        )
        out["step4_sub_target_winners"] = s4

    # ------------------------------------- STEP 5: FULL-STOP POPULATION
    stops = [(r, g) for r, g in zip(ok, rec_gross) if g is not None and g <= -0.999]
    out["step5_full_stops"] = {"n": len(stops)}
    if stops:
        s5: dict = {"n": len(stops)}
        mfe_before = [
            r["mfe_before_stop"] for r, _ in stops if r.get("mfe_before_stop") is not None
        ]
        s5["n_with_a_measured_stop_touch"] = len(mfe_before)
        s5["mfe_before_stop_dist"] = dist(mfe_before)
        for thr in (0.5, 1.0, 1.5, 2.0):
            k = sum(1 for v in mfe_before if v >= thr)
            s5[f"mfe_before_stop_ge_{thr}R"] = [k, pct(k, len(mfe_before))]
        # money left on the table if we had exited at that MFE
        s5["sum_mfe_before_stop_R"] = float(np.nansum(np.asarray(mfe_before)))
        s5["R_per_pool_trade_if_captured_at_1R"] = float(
            sum(1.0 + 1.0 for v in mfe_before if v >= 1.0) / len(ok)
        )
        out["step5_full_stops"] = s5

    # ------------------------------------- STEP 6: (A) vs (B) decomposition
    def mean_of(key: str, H: int) -> float | None:
        vals = [r[f"{key}_{H}"][0] for r in ok if r.get(f"{key}_{H}") is not None]
        return float(np.mean(vals)) if vals else None

    rec_mean = float(np.mean(recorded_vals))
    dec = {
        "recorded_engine_gross_mean_R": rec_mean,
        "B_policy_repair_at_engine_wall": None,
        "A_horizon_lift_under_current_policy": None,
        "A_plus_B_plain_at_10d": None,
    }
    p120 = mean_of("plain", ENGINE_HORIZON_MIN)
    m120 = mean_of("mom", ENGINE_HORIZON_MIN)
    m14400 = mean_of("mom", 14400)
    p14400 = mean_of("plain", 14400)
    dec["plain_120m_mean_R"] = p120
    dec["momentum_120m_mean_R"] = m120
    dec["momentum_14400m_mean_R"] = m14400
    dec["plain_14400m_mean_R"] = p14400
    if p120 is not None and m120 is not None:
        dec["B_policy_repair_at_engine_wall"] = p120 - m120
    if m14400 is not None and m120 is not None:
        dec["A_horizon_lift_under_current_policy"] = m14400 - m120
    if p14400 is not None and m120 is not None:
        dec["A_plus_B_plain_at_10d"] = p14400 - m120
    out["step6_decomposition"] = dec

    # ------------------------------------- per-family plain-vs-momentum
    fam: dict[str, dict] = {}
    for r in ok:
        f_ = r.get("family") or "?"
        d = fam.setdefault(f_, {"n": 0, "plain": [], "mom": [], "plain10d": []})
        d["n"] += 1
        if r.get(f"plain_{ENGINE_HORIZON_MIN}"):
            d["plain"].append(r[f"plain_{ENGINE_HORIZON_MIN}"][0])
        if r.get(f"mom_{ENGINE_HORIZON_MIN}"):
            d["mom"].append(r[f"mom_{ENGINE_HORIZON_MIN}"][0])
        if r.get("plain_14400"):
            d["plain10d"].append(r["plain_14400"][0])
    out["per_family"] = {
        k: {
            "n": v["n"],
            "plain_120m_mean_R": float(np.mean(v["plain"])) if v["plain"] else None,
            "momentum_120m_mean_R": float(np.mean(v["mom"])) if v["mom"] else None,
            "plain_10d_mean_R": float(np.mean(v["plain10d"])) if v["plain10d"] else None,
            "delta_plain_minus_momentum_120m": (
                float(np.mean(v["plain"]) - np.mean(v["mom"]))
                if v["plain"] and v["mom"]
                else None
            ),
        }
        for k, v in sorted(fam.items())
    }

    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    print(json.dumps({k: out[k] for k in ("reconciliation", "step6_decomposition")}, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
