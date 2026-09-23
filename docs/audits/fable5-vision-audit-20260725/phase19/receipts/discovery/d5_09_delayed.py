"""d5-09 — ENUMERATE THE ACHIEVABLE FILLS.

The confirm-minute observable c0 is legal only from T+1m.  Three actions are physically
available to a book that learns it at T+1m, and exactly one more is available at T:

  A0  BASELINE          rest the limit at e from T                      (the shipped contract)
  A2  CANCEL            rest from T, cancel at T+1m if c0<=th and NOT YET FILLED
  A3  DELAYED PLACEMENT place nothing at T; at T+1m place the same limit if c0>th
                        (so every fill that happened inside [T,T+1m) is forgone)
  A3b DELAYED, UNCONDITIONAL  isolates the pure cost of waiting one minute
  A4  MARKET AT T+1m    at T+1m, if c0>th, buy/sell at the confirm close with the same risk
  A5  PRE REFUSAL       at T, refuse rows whose entry is not at price improvement (mkt_r0<=0)
                        -- fully achievable, zero delay, needs no confirm minute at all

Everything is walked on the same M1 tape, same 120-minute absolute path cap measured from T,
same 2.0R target, same conservative same-bar tie to the stop, same broker-true cost model.
"""
from __future__ import annotations
import glob, gzip, json, os, sys, time
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
    "2025-12": "/tmp/f1/roster_202512", "2026-01": "/tmp/d5/roster_202601",
    "2026-02": "/tmp/d5/roster_202602", "2026-03": "/tmp/d5/roster_202603",
    "2026-04": "/tmp/f1/roster_202604", "2026-05": "/tmp/f1/roster_202605",
}
REASONS = ["target", "stop", "path_end", "no_fill"]


def limit_walk(tape, sym, i, *, entry, stop, long, start, cap, need_low=None):
    """Resting order live from stamp `start`; absolute path cap at stamp `cap`.

    `need_low=None` reproduces the estate's convention (a BUY always fills on low<=entry,
    a SELL always on high>=entry) — which fills an entry the market has ALREADY passed.
    `need_low=True/False` selects the touch side explicitly, which is what a broker does:
    a BUY LIMIT (entry below market) fills on low<=entry, a BUY STOP (entry above market)
    fills on high>=entry.
    Returns (r, reason_idx, j_abs); j_abs is the fill bar's offset from i, -1 if never."""
    H = tape.h[sym]; Lo = tape.l[sym]
    b = min(cap, tape.n)
    if start >= b:
        return 0.0, 3, -1
    hs = H[start:b]; ls = Lo[start:b]
    ok = ~np.isnan(hs)
    if not ok.any():
        return 0.0, 3, -1
    idxs = np.nonzero(ok)[0]
    if need_low is None:
        need_low = bool(long)
    tch = (ls[idxs] <= entry) if need_low else (hs[idxs] >= entry)
    if not tch.any():
        return 0.0, 3, -1
    k = int(idxs[int(np.argmax(tch))])
    a = start + k
    res = E.walk(tape, sym, a, entry=entry, stop=stop, long=long,
                 target_r=2.0, horizon=max(b - a - 1, 0))
    if res is None:
        return 0.0, 3, -1
    return float(res[0]), REASONS.index(res[1]), int(a - i)


def run(w):
    t0 = time.time()
    mons = [w.replace("-", "")] + ([NEXT[w]] if NEXT.get(w) else [])
    tape = E.Tape(list(L.SYMBOLS), mons)
    cm = E.CostModel()
    rows = []
    for f in sorted(glob.glob(ROSTER[w] + "/*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] == 15:
                    rows.append(r)
    sys.stderr.write("%s tape %.0fs roster %d\n" % (w, time.time() - t0, len(rows)))
    keys = ("mkt_r0", "c0", "g0", "j0", "cost0", "r0", "gd", "jd", "costd", "rd",
            "gm", "costm", "rm", "gm0", "costm0", "rm0", "gs", "js", "rs",
            "dayi", "hour", "sym", "fam", "risk_bps")
    rec = {k: [] for k in keys}
    days, symids, famids = {}, {}, {}
    for r in rows:
        sym = r["s"]
        if sym not in tape.c:
            continue
        i = tape.idx(r["t"])
        if not (0 < i < tape.n - 2):
            continue
        e = float(r["e"]); sl = float(r["sl"]); d = abs(e - sl)
        if not (d > 0):
            continue
        lng = r["d"] == "L"; s = 1.0 if lng else -1.0
        C = tape.c[sym]
        m0 = C[i - 1]; c0v = C[i]
        if m0 != m0 or c0v != c0v:
            continue
        cap = i + HOR
        g0, r0, j0 = limit_walk(tape, sym, i, entry=e, stop=sl, long=lng, start=i, cap=cap)
        gd, rd, jd = limit_walk(tape, sym, i, entry=e, stop=sl, long=lng, start=i + 1, cap=cap)
        # SIDE-AWARE fill: the touch side is decided by which side of e the market sits on at T.
        # market on the favourable side -> resting LIMIT; market on the far side -> STOP entry.
        mr0 = s * (m0 - e) / d
        need_low = bool(lng) if mr0 >= 0 else (not lng)
        gs, rs, js = limit_walk(tape, sym, i, entry=e, stop=sl, long=lng, start=i, cap=cap,
                                need_low=need_low)
        e2 = float(c0v); sl2 = e2 - s * d
        res2 = E.walk(tape, sym, i, entry=e2, stop=sl2, long=lng, target_r=2.0, horizon=HOR - 1)
        if res2 is None:
            gm, rm = 0.0, 3
        else:
            gm, rm = float(res2[0]), REASONS.index(res2[1])
        # market order sent AT T: fills at the close of stamp i-1 (pbg_econ convention),
        # honest forward path from stamp i (the confirm minute is part of the trade).
        e3 = float(m0); sl3 = e3 - s * d
        res3 = E.walk(tape, sym, i - 1, entry=e3, stop=sl3, long=lng, target_r=2.0, horizon=HOR)
        if res3 is None:
            gm0, rm0 = 0.0, 3
        else:
            gm0, rm0 = float(res3[0]), REASONS.index(res3[1])
        cst = (cm.cost_px(sym, r["t"], e, lng, hold_min=HOR)[0] / d)
        cst2 = (cm.cost_px(sym, r["t"], e2, lng, hold_min=HOR)[0] / d)
        cst3 = (cm.cost_px(sym, r["t"], e3, lng, hold_min=HOR)[0] / d)
        day = r["t"][:10]
        days.setdefault(day, len(days)); symids.setdefault(sym, len(symids))
        famids.setdefault(r["f"], len(famids))
        rec["mkt_r0"].append(s * (m0 - e) / d); rec["c0"].append(s * (c0v - e) / d)
        rec["g0"].append(g0); rec["j0"].append(j0); rec["r0"].append(r0)
        rec["cost0"].append(cst if j0 >= 0 else 0.0)
        rec["gd"].append(gd); rec["jd"].append(jd); rec["rd"].append(rd)
        rec["costd"].append(cst if jd >= 0 else 0.0)
        rec["gm"].append(gm); rec["rm"].append(rm); rec["costm"].append(cst2)
        rec["gm0"].append(gm0); rec["rm0"].append(rm0); rec["costm0"].append(cst3)
        rec["gs"].append(gs); rec["rs"].append(rs); rec["js"].append(js)
        rec["dayi"].append(days[day]); rec["hour"].append(int(r["t"][11:13]))
        rec["sym"].append(symids[sym]); rec["fam"].append(famids[r["f"]])
        rec["risk_bps"].append(d / e * 1e4)
    ints = ("j0", "jd", "js", "r0", "rd", "rm", "rm0", "rs", "dayi", "hour", "sym", "fam")
    arr = {k: np.asarray(v, dtype=(np.int32 if k in ints else np.float64)) for k, v in rec.items()}
    np.savez_compressed("/tmp/d5/out/D9_%s.npz" % w, **arr)
    json.dump(dict(window=w, n=len(rec["g0"]), n_roster=len(rows), days=days,
                   symids=symids, famids=famids, months=mons, horizon=HOR, reasons=REASONS),
              open("/tmp/d5/out/D9_%s_meta.json" % w, "w"))
    sys.stderr.write("%s DONE n=%d %.0fs  base_gross=%.5f delayed_gross=%.5f mkt_gross=%.5f\n"
                     % (w, len(rec["g0"]), time.time() - t0,
                        float(np.mean(rec["g0"])), float(np.mean(rec["gd"])), float(np.mean(rec["gm"]))))


if __name__ == "__main__":
    run(sys.argv[1])
