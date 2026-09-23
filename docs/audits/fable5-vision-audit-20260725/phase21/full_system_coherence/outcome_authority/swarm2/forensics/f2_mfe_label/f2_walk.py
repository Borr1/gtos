#!/usr/bin/env python3
"""F2 excursion census -- the per-trade path statistics the estate has never used.

Fill logic is copied VERBATIM from swarm2/lane2_receipts/walk.py, which Lane 2
validated reproduces the sealed `resolve_post_submission_m1_lifecycle` label at
the 1x horizon.  The POST-FILL scan is replaced: Lane 2 walked to the first of
{stop, target}; this walks to the first of {stop, horizon} with NO take-profit
barrier, so favourable excursion is not truncated at 2R.

Emits, per filled candidate:
    mfe_pre / mfe_incl   running max favourable excursion in R (excl./incl. the stop bar)
    mae_pre / mae_incl   running min adverse excursion in R
    t_mfe                minutes from fill to the bar achieving the running max
    hit_<k>              absolute minute at which level k is first passed (0 = never)
    amb_<k>              level k first passed in the same bar as the stop (ordering ambiguous)
    stop_min             absolute minute the stop is hit (0 = not hit within the scan)
    mark_h1 / mark_h2    mark-to-close R at the sealed horizon and at 2x
    mfe_capped_h1        MFE truncated by the 2R target -- cross-check against Lane 2

Bound by PREREG_V1.json payload_sha256
8b038d866c95412baba06ddf420267ac2d254bdaffa28cf2de8b2b3b38025ff4
"""
import csv, gzip, json, os, pickle, sys, time
import datetime as dt
from pathlib import Path
import numpy as np

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
sys.path.insert(0, str(WT))
from src.research_infra.walkforward.quote_side import spread_for

HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
BARS = HOLD / ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars"
CACHE = "/private/tmp/w21-puzzle-cache/rows_%s.pkl.gz"
GEOM = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane2")
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f2")
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
MONTH_SRC = {"feb": ["202602", "202603"], "apr": ["202604", "202605"],
             "may": ["202605", "202606"], "jun": ["202606", "202607"],
             "jul": ["202607"],
             # frozen bootstrap: Oct/Nov 2025 development + January 2026
             "dev": ["202510", "202511"], "jan": ["202601", "202602"]}
BOOT_MONTHS = ("dev", "jan")
LADDER = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0]
SCAN_MIN = 60 * 24 * 3          # three days of M1 past the fill
T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def mins(t):
    return int((t - EPOCH).total_seconds() // 60)


def at(s):
    return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def load_symbol_series(month):
    """Concatenated M1 for the month and its successor, per symbol. Verbatim from Lane 2."""
    per = {}
    for tag in MONTH_SRC[month]:
        d = BARS / f"bridge_ftmo_m1_{tag}"
        for p in sorted(d.glob("*_M1.csv")):
            sym = p.name[:-7]
            rows = per.setdefault(sym, [])
            with p.open(newline="") as fh:
                for row in csv.DictReader(fh):
                    rows.append((row["time"], row["open"], row["high"], row["low"], row["close"]))
    out = {}
    for sym, rows in per.items():
        rows = sorted(set(rows), key=lambda r: r[0])
        tm = np.array([mins(at(r[0])) for r in rows], dtype=np.int64)
        keep = np.concatenate([[True], np.diff(tm) > 0])
        rows = [r for r, k in zip(rows, keep) if k]
        tm = tm[keep]
        o = np.array([float(r[1]) for r in rows]); h = np.array([float(r[2]) for r in rows])
        lo = np.array([float(r[3]) for r in rows]); c = np.array([float(r[4]) for r in rows])
        cache, spr = {}, np.empty(len(rows))
        for i, r in enumerate(rows):
            hr = at(r[0]).replace(minute=0, second=0, microsecond=0)
            if hr not in cache:
                cache[hr] = spread_for(sym, hr, account="FTMO", band="mid")
            spr[i] = cache[hr]
        out[sym] = dict(t=tm, o=o, h=h, l=lo, c=c, s=spr)
    return out


FIELDS_I = ["sub", "H1", "fill_min", "stop_min", "t_mfe", "hz1", "hz2", "nbars_scanned",
            "first_gap_min", "stop_amb_fill_bar", "runout"]
FIELDS_F = ["risk", "ded", "sealed_net", "fp", "mfe_pre", "mfe_incl", "mae_pre", "mae_incl",
            "mark_h1", "mark_h2", "mfe_capped_h1", "stop_gross"]
FIELDS_S = ["key", "month", "sym", "fam", "ot", "side", "day", "sealed_status", "disp"]


def load_rows(month):
    """Candidate rows for a month. Bootstrap months come from B3's frozen
    bootstrap corpus (the same object the shipped rule trains on)."""
    if month not in BOOT_MONTHS:
        return pickle.load(gzip.open(CACHE % month, "rb"))
    with open("/Users/borr/.claude/jobs/adb9e69b/tmp/b3/out/bootstrap_rows.pkl", "rb") as fh:
        boot = pickle.load(fh)
    if month == "dev":
        return list(boot["initial"])
    out = []
    for day in boot["jan_runs"]:
        out.extend(boot["january"][day])
    return out


def walk_month(month):
    ser = load_symbol_series(month)
    log(stage="bars_loaded", month=month, symbols=len(ser),
        rows=int(sum(len(v["t"]) for v in ser.values())))
    geom = {}
    gpath = (OUT / "geom_boot.jsonl.gz") if month in BOOT_MONTHS else (GEOM / f"geom_{month}.jsonl.gz")
    with gzip.open(gpath, "rt") as fh:
        for line in fh:
            r = json.loads(line)
            geom[r["k"]] = r
    rows = load_rows(month)
    log(stage="joined", month=month, cache=len(rows), geom=len(geom))

    acc = {k: [] for k in FIELDS_I + FIELDS_F + FIELDS_S}
    hitcols = {f"hit_{k}": [] for k in LADDER}
    ambcols = {f"amb_{k}": [] for k in LADDER}

    def emit(base, disp, extra=None):
        base = dict(base); base["disp"] = disp
        if extra:
            base.update(extra)
        for k in FIELDS_I:
            acc[k].append(int(base.get(k) or 0))
        for k in FIELDS_F:
            v = base.get(k)
            acc[k].append(float("nan") if v is None else float(v))
        for k in FIELDS_S:
            acc[k].append(str(base.get(k) or ""))
        hv = base.get("_hit") or {}
        av = base.get("_amb") or {}
        for k in LADDER:
            hitcols[f"hit_{k}"].append(int(hv.get(k) or 0))
            ambcols[f"amb_{k}"].append(bool(av.get(k) or False))

    for row in rows:
        g = geom.get(row["candidate_occurrence_key"])
        if g is None:
            continue
        sym = g["symbol"]; S = ser.get(sym)
        base = dict(key=row["candidate_occurrence_key"], month=month, sym=sym,
                    fam=row["origin_family"], ot=row["proposed_order_type"], side=g["side"],
                    day=g["trading_day"], sealed_status=row["lifecycle_label_status"],
                    ded=float(row.get("deductible_cost_r") or 0.0),
                    sealed_net=row.get("terminal_net_r"))
        if S is None:
            emit(base, "no_series"); continue
        d = 1 if str(g["side"]).upper() == "LONG" else -1
        entry = float(g["entry_price"]); stop = float(g["stop_loss"]); target = float(g["take_profit_1"])
        risk = abs(entry - stop)
        sub = at(g["decision_time_utc"]); exp = at(g["limit_first_expiry_utc"])
        sm, em = mins(sub), mins(exp)
        H1 = em - sm
        base.update(sub=sm, H1=H1, risk=risk, hz1=em, hz2=sm + 2 * H1)
        t = S["t"]
        i = int(np.searchsorted(t, sm, side="right")) - 1
        if i < 0 or t[i] != sm:
            emit(base, "submission_bar_missing"); continue

        eoff = 0.0 if d > 0 else S["s"]
        aoff = S["s"] if d > 0 else 0.0
        n = len(t)
        # ------------------------- fill: VERBATIM from Lane 2 ----------------
        succ = i + 1
        if succ >= n or t[succ] != sm + 1:
            emit(base, "no_contiguous_successor"); continue
        if base["ot"] == "MARKET":
            if t[succ] >= em:
                emit(base, "market_expires_before_successor"); continue
            fi = succ; fp = S["o"][succ] + (aoff[succ] if d > 0 else 0.0); fill_at_open = True
        else:
            def ebar(j):
                a = aoff[j] if d > 0 else 0.0
                return (S["o"][j] + a, S["h"][j] + a, S["l"][j] + a, S["c"][j] + a)
            v0 = ebar(i)
            if (v0[2] <= entry) if d > 0 else (v0[1] >= entry):
                emit(base, "CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_ORDERING"); continue
            prev, cur, fi, why = i, succ, None, None
            while True:
                if cur >= n or t[cur] != t[prev] + 1:
                    why = "gap_before_limit_expiry"; break
                op = t[cur]
                if op >= em:
                    why = "NO_FILL"; break
                v = ebar(cur)
                fav_ = (v[0] <= entry) if d > 0 else (v[0] >= entry)
                tou = (v[2] <= entry) if d > 0 else (v[1] >= entry)
                if fav_:
                    fi, fp, fill_at_open = cur, v[0], True; break
                if op + 1 > em:
                    why = "CENSORED_ORDERING_AMBIGUITY" if tou else "NO_FILL"; break
                if tou:
                    fi, fp, fill_at_open = cur, entry, False; break
                if op + 1 == em:
                    why = "NO_FILL"; break
                prev, cur = cur, cur + 1
            if fi is None:
                emit(base, why); continue
        xo = S["o"][fi] + (eoff[fi] if d < 0 else 0.0)
        if fill_at_open and (d * (stop - fp) / risk >= 0 or d * (target - fp) / risk <= 0
                             or ((xo <= stop) if d > 0 else (xo >= stop))
                             or ((xo >= target) if d > 0 else (xo <= target))):
            emit(base, "CENSORED_INVALID_GAP_THROUGH_SL_OR_TP"); continue
        base.update(fi=int(fi), fp=float(fp), fill_min=int(t[fi]))

        # ------------------- STOP-ONLY scan (the F2 change) -------------------
        maxend = min(n, fi + 1 + SCAN_MIN)
        sl = slice(fi, maxend)
        off = eoff[sl] if d < 0 else 0.0
        O = S["o"][sl] + off; H = S["h"][sl] + off; L = S["l"][sl] + off; C = S["c"][sl] + off
        TT = t[sl]
        m = len(TT)
        gapj = np.nonzero(np.diff(TT) != 1)[0]
        first_gap = int(gapj[0]) + 1 if len(gapj) else m
        base["first_gap_min"] = int(TT[first_gap - 1]) + 1 if first_gap < m else 0
        base["nbars_scanned"] = m

        if d > 0:
            so = O <= stop; hs = L <= stop
            fav = (H - fp) / risk; adv = (L - fp) / risk
            lvl_px = fp + np.asarray(LADDER) * risk
        else:
            so = O >= stop; hs = H >= stop
            fav = (fp - L) / risk; adv = (fp - H) / risk
            lvl_px = fp - np.asarray(LADDER) * risk

        # stop event index. Fill bar: an intrabar LIMIT fill touching the stop in
        # the same bar is ordering-ambiguous (Lane 2 censors it); a fill at open
        # takes the stop.
        hs_eff = hs.copy()
        stop_amb_fill = False
        if hs[0] and not fill_at_open:
            stop_amb_fill = True
        base["stop_amb_fill_bar"] = int(stop_amb_fill)
        nzs = np.nonzero(hs_eff)[0]
        stop_j = int(nzs[0]) if len(nzs) else None
        if stop_j is not None:
            stop_min = int(TT[stop_j]) + (0 if so[stop_j] else 1)
            base["stop_min"] = stop_min
            base["stop_gross"] = float(d * ((O[stop_j] if so[stop_j] else stop) - fp) / risk)
        else:
            stop_min = None
            base["runout"] = 1

        cum_fav = np.maximum.accumulate(fav)
        cum_adv = np.minimum.accumulate(adv)

        # last complete bar strictly before each horizon
        def last_before(hz):
            jj = int(np.searchsorted(TT, hz - 1, side="right")) - 1
            return jj
        j1 = last_before(em)
        j2 = last_before(sm + 2 * H1)
        base["mark_h1"] = float(d * (C[j1] - fp) / risk) if j1 >= 0 else float("nan")
        base["mark_h2"] = float(d * (C[j2] - fp) / risk) if j2 >= 0 else float("nan")

        # excursion window: up to the stop bar, and up to the sealed horizon
        end_incl = m - 1 if stop_j is None else stop_j
        end_incl = min(end_incl, j1) if j1 >= 0 else 0
        end_pre = max(0, (m - 1 if stop_j is None else stop_j - 1))
        end_pre = min(end_pre, j1) if j1 >= 0 else 0
        base["mfe_pre"] = float(cum_fav[end_pre]); base["mae_pre"] = float(cum_adv[end_pre])
        base["mfe_incl"] = float(cum_fav[end_incl]); base["mae_incl"] = float(cum_adv[end_incl])
        base["t_mfe"] = int(TT[int(np.argmax(fav[:end_pre + 1]))] - TT[0])

        # target-capped MFE at h1 (Lane 2 equivalence check)
        if d > 0:
            ht = H >= target
        else:
            ht = L <= target
        nzt = np.nonzero(ht)[0]
        tgt_j = int(nzt[0]) if len(nzt) else None
        cap_end = end_incl if tgt_j is None else min(end_incl, tgt_j)
        base["mfe_capped_h1"] = float(cum_fav[max(0, cap_end)])

        # ladder first passage. cum_fav is monotone non-decreasing, so the first
        # index reaching level k is a binary search.
        hit, amb = {}, {}
        for kk, k in enumerate(LADDER):
            idx = int(np.searchsorted(cum_fav, k, side="left"))
            if idx >= m:
                hit[k] = 0; amb[k] = False; continue
            gap_open = (O[idx] >= lvl_px[kk]) if d > 0 else (O[idx] <= lvl_px[kk])
            hit[k] = int(TT[idx]) + (0 if gap_open else 1)
            amb[k] = bool(stop_j is not None and idx == stop_j)
        base["_hit"] = hit; base["_amb"] = amb
        emit(base, "FILLED")

    out = {}
    for k in FIELDS_I:
        out[k] = np.asarray(acc[k], dtype=np.int64)
    for k in FIELDS_F:
        out[k] = np.asarray(acc[k], dtype=np.float64)
    for k in FIELDS_S:
        out[k] = np.asarray(acc[k], dtype=object)
    for k, v in hitcols.items():
        out[k] = np.asarray(v, dtype=np.int64)
    for k, v in ambcols.items():
        out[k] = np.asarray(v, dtype=bool)
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT / f"exc_{month}.pkl.gz", "wb") as fh:
        pickle.dump(out, fh, protocol=5)
    from collections import Counter
    log(stage="month_done", month=month, n=len(out["key"]),
        disp=dict(Counter(out["disp"].tolist())))


if __name__ == "__main__":
    for m in sys.argv[1:] or ["feb", "apr", "may", "jun", "jul"]:
        walk_month(m)
    log(stage="ALL_DONE")
