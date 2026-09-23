"""d5 — build the confirm-minute feature table on the ROSTER (the correct population).

The observable, taken verbatim from x4_RESULT.md S5:
    c0_close_fav_r = s * (close of M1 bar [T, T+1m) - entry_price) / risk_distance
                     s = +1 LONG, -1 SHORT.  Negative => price already ran AGAINST the entry
                     inside the first minute after the decision instant.
x4 established (V1) that this is byte-identical to w0cap2_DECISION_ANCHOR_V1.mkt_r_close.

Everything is computed on the SEALED ROSTER (Session PB's reproduction), k=15 rows only
(the shipped close-decision contract), NOT on the 27,658-row counterfactual pool.

Per row we stamp:
  PRE      (legal for an order placed AT T)      mkt_r0, geo, bar-range, atr, hour, risk bps
  CONFIRM  (legal for an action at T+1m)         c0 and its intra-minute extremes, touch flag
  CONFIRM+ (legal at T+2m / T+5m)                c1, c4, 5-minute excursions
  OUTCOME  honest resting-order walk from T      gross R, first-touch offset j, reason, cost
  REANCHOR market order at the close of [T,T+1m) with the same risk distance
"""
from __future__ import annotations
import bisect, csv, glob, gzip, json, os, sys, time
from datetime import datetime, timezone
import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0, PBG); sys.path.insert(0, REPO)
os.chdir(REPO)
import pbg_lib as L
import pbg_econ as E

HOR = 120
NEXT = {"2025-10": "202511", "2025-11": "202512", "2025-12": "202601", "2026-01": "202602",
        "2026-02": "202603", "2026-03": "202604", "2026-04": "202605", "2026-05": None}
ROSTER = {
    "2025-10": "/tmp/f1/roster_202510", "2025-11": "/tmp/f1/roster_202511",
    "2025-12": "/tmp/f1/roster_202512", "2026-01": "/tmp/pbg_full_jan",
    "2026-02": "/tmp/pbg_full_feb", "2026-03": "/tmp/pbg_full_mar",
    "2026-04": "/tmp/f1/roster_202604", "2026-05": "/tmp/f1/roster_202605",
}
REASONS = ["target", "stop", "path_end", "no_fill"]


def load_vol(months, symbols, t0, n):
    """M1 volume array per symbol (the Tape does not carry it)."""
    out = {}
    for sym in symbols:
        v = np.full(n, np.nan)
        for mm in months:
            p = L.m1_dir(mm) / ("%s_M1.csv" % sym)
            if not p.is_file():
                continue
            with p.open("r", newline="") as fh:
                rd = csv.reader(fh)
                hdr = next(rd, None)
                for row in rd:
                    ts = datetime.fromisoformat(row[0])
                    i = int((ts - t0).total_seconds() // 60)
                    if 0 <= i < n:
                        v[i] = float(row[5])
        out[sym] = v
    return out


def walk_from(tape, sym, a, *, entry, stop, long, target_r, horizon):
    """E.walk but path starts at stamp a (exclusive of a itself: a+1..)."""
    return E.walk(tape, sym, a, entry=entry, stop=stop, long=long,
                  target_r=target_r, horizon=horizon)


def run(w):
    t_start = time.time()
    mons = [w.replace("-", "")] + ([NEXT[w]] if NEXT.get(w) else [])
    syms = list(L.SYMBOLS)
    tape = E.Tape(syms, mons)
    vol = load_vol(mons, syms, tape.t0, tape.n)
    cm = E.CostModel()
    sys.stderr.write("%s tape+vol %.0fs n=%d\n" % (w, time.time() - t_start, tape.n))

    rows = []
    for f in sorted(glob.glob(ROSTER[w] + "/*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] != 15:
                    continue
                rows.append(r)
    sys.stderr.write("%s roster k15 rows=%d\n" % (w, len(rows)))

    symids, famids = {}, {}
    drop = {"sym_not_in_tape": 0, "idx_range": 0, "risk_zero": 0, "no_prev_close": 0,
            "no_confirm_close": 0, "no_forward_bars": 0}
    rec = {k: [] for k in (
        "sym", "fam", "dayi", "hour", "side", "e", "d_px", "risk_bps",
        "mkt_r0", "geo", "barrng_r", "atr60_r", "c0", "c0_fav", "c0_adv", "c0_rng",
        "touch0", "vol0_ratio", "c1", "c4", "fav5", "adv5",
        "g", "j", "reason", "cost_r", "ra_g", "ra_cost_r", "nbars")}
    days = {}

    for r in rows:
        sym = r["s"]
        if sym not in tape.c:
            drop["sym_not_in_tape"] += 1; continue
        i = tape.idx(r["t"])
        if not (0 < i < tape.n - 2):
            drop["idx_range"] += 1; continue
        e = float(r["e"]); sl = float(r["sl"])
        d = abs(e - sl)
        if not (d > 0):
            drop["risk_zero"] += 1; continue
        lng = r["d"] == "L"
        s = 1.0 if lng else -1.0
        C = tape.c[sym]; H = tape.h[sym]; Lo = tape.l[sym]; V = vol[sym]
        mkt0 = C[i - 1]
        if mkt0 != mkt0:
            drop["no_prev_close"] += 1; continue
        c0v = C[i]
        if c0v != c0v:
            drop["no_confirm_close"] += 1; continue
        # ---- PRE: the 15 M1 bars composing the decision M15 bar are [i-15, i)
        a0 = max(i - 15, 0)
        hh = H[a0:i]; ll = Lo[a0:i]
        okp = ~np.isnan(hh)
        if okp.sum() >= 5:
            bh = float(np.nanmax(hh)); bl = float(np.nanmin(ll))
            brng = bh - bl
        else:
            brng = float("nan")
        a60 = max(i - 60, 0)
        h60 = H[a60:i]; l60 = Lo[a60:i]
        if (~np.isnan(h60)).sum() >= 10:
            atr60 = float(np.nanmax(h60) - np.nanmin(l60))
        else:
            atr60 = float("nan")
        # ---- CONFIRM: the single M1 bar labelled T
        hi0 = H[i]; lo0 = Lo[i]
        fav0 = (hi0 if lng else lo0)
        adv0 = (lo0 if lng else hi0)
        touched0 = bool((lo0 <= e) if lng else (hi0 >= e))
        v0 = V[i]
        vprev = V[a0:i]
        vm = float(np.nanmean(vprev)) if (~np.isnan(vprev)).sum() >= 5 else float("nan")
        # ---- CONFIRM+ : minute 2 and minute 5, and the 5-minute excursion
        c1v = C[i + 1] if i + 1 < tape.n else float("nan")
        c4v = C[i + 4] if i + 4 < tape.n else float("nan")
        b5 = min(i + 5, tape.n)
        h5 = H[i:b5]; l5 = Lo[i:b5]
        if (~np.isnan(h5)).any():
            f5 = float(np.nanmax(h5)) if lng else float(np.nanmin(l5))
            a5 = float(np.nanmin(l5)) if lng else float(np.nanmax(h5))
        else:
            f5 = a5 = float("nan")
        # ---- OUTCOME: honest resting order live from stamp i (missing minute INCLUDED)
        b = min(i + HOR, tape.n)
        hs = H[i:b]; ls = Lo[i:b]
        okw = ~np.isnan(hs)
        if not okw.any():
            drop["no_forward_bars"] += 1; continue
        idxs = np.nonzero(okw)[0]
        tch = (ls[idxs] <= e) if lng else (hs[idxs] >= e)
        if not tch.any():
            g, reason, j, nb = 0.0, "no_fill", -1, int(okw.sum())
            cost_r = 0.0
        else:
            j = int(idxs[int(np.argmax(tch))])
            res = walk_from(tape, sym, i + j, entry=e, stop=sl, long=lng,
                            target_r=2.0, horizon=HOR - j - 1)
            if res is None:
                g, reason, nb = 0.0, "no_fill", 0
                cost_r = 0.0
                j = -1
            else:
                g, reason, _, nb = res
                px, _t = cm.cost_px(sym, r["t"], e, lng, hold_min=HOR)
                cost_r = px / d
        # ---- RE-ANCHOR: market order at the close of the confirm minute, same risk distance
        e2 = float(c0v)
        sl2 = e2 - s * d
        res2 = walk_from(tape, sym, i, entry=e2, stop=sl2, long=lng,
                         target_r=2.0, horizon=HOR - 1)
        if res2 is None:
            ra_g = float("nan"); ra_cost = float("nan")
        else:
            ra_g = res2[0]
            px2, _ = cm.cost_px(sym, r["t"], e2, lng, hold_min=HOR)
            ra_cost = px2 / d

        symids.setdefault(sym, len(symids))
        famids.setdefault(r["f"], len(famids))
        day = r["t"][:10]
        days.setdefault(day, len(days))
        rec["sym"].append(symids[sym]); rec["fam"].append(famids[r["f"]])
        rec["dayi"].append(days[day]); rec["hour"].append(int(r["t"][11:13]))
        rec["side"].append(s); rec["e"].append(e); rec["d_px"].append(d)
        rec["risk_bps"].append(d / e * 1e4)
        rec["mkt_r0"].append(s * (mkt0 - e) / d)
        rec["geo"].append(d / brng if brng and brng == brng and brng > 0 else float("nan"))
        rec["barrng_r"].append(brng / d if brng == brng else float("nan"))
        rec["atr60_r"].append(atr60 / d if atr60 == atr60 else float("nan"))
        rec["c0"].append(s * (c0v - e) / d)
        rec["c0_fav"].append(s * (fav0 - e) / d)
        rec["c0_adv"].append(s * (adv0 - e) / d)
        rec["c0_rng"].append(abs(hi0 - lo0) / d)
        rec["touch0"].append(1 if touched0 else 0)
        rec["vol0_ratio"].append(v0 / vm if vm == vm and vm > 0 else float("nan"))
        rec["c1"].append(s * (c1v - e) / d)
        rec["c4"].append(s * (c4v - e) / d)
        rec["fav5"].append(s * (f5 - e) / d)
        rec["adv5"].append(s * (a5 - e) / d)
        rec["g"].append(float(g)); rec["j"].append(int(j))
        rec["reason"].append(REASONS.index(reason)); rec["cost_r"].append(float(cost_r))
        rec["ra_g"].append(float(ra_g)); rec["ra_cost_r"].append(float(ra_cost))
        rec["nbars"].append(int(nb))

    arr = {k: np.asarray(v, dtype=(np.int32 if k in ("sym", "fam", "dayi", "hour", "touch0",
                                                     "j", "reason", "nbars") else np.float64))
           for k, v in rec.items()}
    np.savez_compressed("/tmp/d5/out/D5_%s.npz" % w, **arr)
    meta = dict(window=w, n=int(len(rec["g"])), n_roster_k15=len(rows), drops=drop,
                symids=symids, famids=famids,
                days=days, reasons=REASONS, months=mons, horizon=HOR)
    json.dump(meta, open("/tmp/d5/out/D5_%s_meta.json" % w, "w"))
    sys.stderr.write("%s DONE n=%d %.0fs\n" % (w, len(rec["g"]), time.time() - t_start))


if __name__ == "__main__":
    run(sys.argv[1])
