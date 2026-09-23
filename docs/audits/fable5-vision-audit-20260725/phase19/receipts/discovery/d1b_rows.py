"""d1 — per-window row builder on the ROSTER (close-only candidate emissions).

For every roster emission it walks BOTH sides of the identical geometry
(the real side, and its exact mirror about the entry price) at BOTH targets
(1.5R = the generator's own emitted take_profit_1 with risk.min_rr=1.5, and
2.0R = the shipped downstream geometry f1/f2 priced), under the honest
resting-limit fill contract (pbg_econ.walk_limit semantics as f1 used them).

The mirrored arm is the exact conditional expectation input for a coin-flip
control: E[coin flip | row] = (real + flipped) / 2, with ZERO Monte-Carlo noise.

Output: /tmp/d1/rows3/D1_<window>.npz  (integer-coded columns + legend json)
"""
from __future__ import annotations
import sys, os, json, gzip, glob, math
from datetime import datetime, timedelta, timezone
import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
DISC = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
sys.path.insert(0, PBG); sys.path.insert(0, REPO); os.chdir(REPO)
import pbg_lib as L
import pbg_econ as E

HOR = 120
TARGETS = (1.5, 2.0)

NEXT = {"2025-10": "202511", "2025-11": "202512", "2025-12": "202601", "2026-01": "202602",
        "2026-02": "202603", "2026-03": "202604", "2026-04": "202605", "2026-05": None}
SRC = {"2025-10": "/tmp/f1/roster_202510", "2025-11": "/tmp/f1/roster_202511",
       "2025-12": "/tmp/f1/roster_202512", "2026-01": "/tmp/pbg_full_jan",
       "2026-02": "/tmp/pbg_full_feb", "2026-03": "/tmp/pbg_full_mar",
       "2026-04": "/tmp/f1/roster_202604", "2026-05": "/tmp/f1/roster_202605"}

ATMARKET = {"cross_asset_lead_lag", "displacement_continuation", "liquidity_sweep_reclaim",
            "regime_transition_break", "session_open_range_break",
            "structural_distance_extreme", "volatility_compression_expansion",
            "range_extreme_reversion"}

FAMS = ["cross_asset_lead_lag", "current_breaker_re_entry", "current_fvg_fill",
        "current_ob_retest", "displacement_continuation", "liquidity_sweep_reclaim",
        "regime_transition_break", "session_open_range_break",
        "structural_distance_extreme", "volatility_compression_expansion",
        "range_extreme_reversion"]
FIDX = {f: i for i, f in enumerate(FAMS)}
REASON = ["no_fill", "stop", "target", "path_end"]
RIDX = {r: i for i, r in enumerate(REASON)}


def walk_arm(hi, lo, cl, n, i, entry, stop, long, horizon=HOR):
    """Honest resting-limit fill + forward walk at BOTH targets.

    Returns (filled, touch_j, r15, reason15, r20, reason20, bars).
    Semantics identical to f1_walk.walk_limit2 -> pbg_econ.walk.
    """
    d = abs(entry - stop)
    if not (d > 0):
        return None
    a = i; b = min(a + horizon, n)
    if a >= b:
        return None
    H = hi[a:b]; Lo = lo[a:b]
    ok = ~np.isnan(H)
    if not ok.any():
        return None
    idxs = np.nonzero(ok)[0]
    touched = (Lo[idxs] <= entry) if long else (H[idxs] >= entry)
    if not touched.any():
        return (0, -1, 0.0, 0, 0.0, 0, int(ok.sum()))
    j = int(idxs[int(np.argmax(touched))])
    a2 = a + j + 1
    if a2 >= b:
        return (0, j, 0.0, 0, 0.0, 0, 0)
    H2 = hi[a2:b]; L2 = lo[a2:b]; C2 = cl[a2:b]
    ok2 = ~np.isnan(C2)
    if not ok2.any():
        return (0, j, 0.0, 0, 0.0, 0, 0)
    H2 = H2[ok2]; L2 = L2[ok2]; C2 = C2[ok2]
    if long:
        hit_s = L2 <= stop
        t15 = H2 >= entry + 1.5 * d
        t20 = H2 >= entry + 2.0 * d
    else:
        hit_s = H2 >= stop
        t15 = L2 <= entry - 1.5 * d
        t20 = L2 <= entry - 2.0 * d
    iss = int(np.argmax(hit_s)) if hit_s.any() else None
    i15 = int(np.argmax(t15)) if t15.any() else None
    i20 = int(np.argmax(t20)) if t20.any() else None
    last = float(C2[-1])
    rp = (last - entry) / d if long else (entry - last) / d
    out = []
    for tgt, it in ((1.5, i15), (2.0, i20)):
        if iss is not None and (it is None or iss <= it):
            out.append((-1.0, RIDX["stop"]))
        elif it is not None:
            out.append((float(tgt), RIDX["target"]))
        else:
            out.append((rp, RIDX["path_end"]))
    return (1, j, out[0][0], out[0][1], out[1][0], out[1][1], int(len(C2)))


def walk_market(hi, lo, cl, n, i, entry, stop, long, horizon=HOR):
    """Immediate market fill at `entry`; forward path = stamps i+1 .. i+horizon.
    Identical to pbg_econ.walk (include_fill_minute=False), both targets at once."""
    d = abs(entry - stop)
    if not (d > 0):
        return None
    a = i + 1; b = min(i + 1 + horizon, n)
    if a >= b:
        return None
    H = hi[a:b]; L2 = lo[a:b]; C = cl[a:b]
    ok = ~np.isnan(C)
    if not ok.any():
        return None
    H = H[ok]; L2 = L2[ok]; C = C[ok]
    if long:
        hit_s = L2 <= stop
        t15 = H >= entry + 1.5 * d
        t20 = H >= entry + 2.0 * d
    else:
        hit_s = H >= stop
        t15 = L2 <= entry - 1.5 * d
        t20 = L2 <= entry - 2.0 * d
    iss = int(np.argmax(hit_s)) if hit_s.any() else None
    i15 = int(np.argmax(t15)) if t15.any() else None
    i20 = int(np.argmax(t20)) if t20.any() else None
    last = float(C[-1])
    rp = (last - entry) / d if long else (entry - last) / d
    out = []
    for tgt, it in ((1.5, i15), (2.0, i20)):
        if iss is not None and (it is None or iss <= it):
            out.append((-1.0, RIDX["stop"]))
        elif it is not None:
            out.append((float(tgt), RIDX["target"]))
        else:
            out.append((rp, RIDX["path_end"]))
    return (1, 0, out[0][0], out[0][1], out[1][0], out[1][1], int(len(C)))


class FastCost:
    """pbg_econ.CostModel with per-instant caching of broker hour and swap nights."""

    def __init__(self):
        self.cm = E.CostModel()
        self._inst = {}
        self._sp = {}

    def inst(self, iso):
        v = self._inst.get(iso)
        if v is not None:
            return v
        u = datetime.fromisoformat(iso)
        if u.tzinfo is None:
            u = u.replace(tzinfo=timezone.utc)
        w0 = self.cm._to_broker(u, self.cm.server)
        w1 = w0 + timedelta(minutes=HOR)
        nights, d = 0.0, w0.date()
        while True:
            d = d + timedelta(days=1)
            b = datetime(d.year, d.month, d.day)
            if b > w1:
                break
            nights += 3.0 if b.weekday() == 3 else 1.0
        v = (w0.hour, nights)
        self._inst[iso] = v
        return v

    def spread_bps(self, sym, h):
        k = (sym, h)
        v = self._sp.get(k)
        if v is None:
            v = self.cm.spread_bps(sym, h)
            self._sp[k] = v
        return v

    def px(self, sym, iso, price, long):
        h, nights = self.inst(iso)
        sp = self.spread_bps(sym, h) / 1e4 * price
        cmx = self.cm.comm_px(sym, price)
        sl = self.cm.slip_bps.get(sym, ("MODELLED", 0.0))[1] / 1e4 * price
        sw = 0.0
        if nights:
            rec = self.cm.bt.get(self.cm.bmap.get(sym, sym))
            if rec is not None:
                spec = rec.get("spec") or {}
                raw = spec.get("swap_long" if long else "swap_short")
                mode = spec.get("swap_mode")
                if raw is not None and mode is not None and float(raw) < 0:
                    adv = abs(float(raw))
                    if int(mode) == 1:
                        pt = spec.get("point")
                        per_night = adv * float(pt) if pt else 0.0
                    elif int(mode) in (5, 6):
                        per_night = float(price) * (adv / 100.0) / 360.0
                    else:
                        per_night = 0.0
                    sw = per_night * nights
        return sp + cmx + sl + sw


def regimes(tape, syms, days):
    """Per (symbol, day): prior-24h realised range in bps and prior-24h return sign.

    Strictly pre-decision: the window ends at the day's 00:00 stamp.
    Vol terciles are cut PER SYMBOL over the window's own days.
    """
    raw = {}
    for sym in syms:
        if sym not in tape.c:
            continue
        hi, lo, cl = tape.h[sym], tape.l[sym], tape.c[sym]
        for day in days:
            i = tape.idx(day + "T00:00:00+00:00")
            a = max(0, i - 1440)
            if a >= i:
                continue
            H = hi[a:i]; Lo = lo[a:i]; C = cl[a:i]
            ok = ~np.isnan(C)
            if ok.sum() < 60:
                continue
            C = C[ok]
            rng = float(np.nanmax(H) - np.nanmin(Lo))
            last = float(C[-1]); first = float(C[0])
            if not (last > 0):
                continue
            raw[(sym, day)] = (rng / last * 1e4, (last - first) / last * 1e4)
    out = {}
    for sym in syms:
        vals = [(d, v[0]) for (s, d), v in raw.items() if s == sym]
        if not vals:
            continue
        arr = np.array([v for _, v in vals])
        q1, q2 = np.percentile(arr, [33.3333, 66.6667])
        for d, v in vals:
            vt = 0 if v <= q1 else (1 if v <= q2 else 2)
            tr = raw[(sym, d)][1]
            out[(sym, d)] = (vt, 0 if tr < 0 else 1)
    return out


def run(w):
    mons = [w.replace("-", "")] + ([NEXT[w]] if NEXT.get(w) else [])
    syms = list(L.SYMBOLS)
    keep = set(json.load(open(DISC + "/f1_ARM_TRADING_DAYS_V1.json"))[w])
    rows = []
    for f in sorted(glob.glob(SRC[w] + "/*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] != 15:
                    continue
                if r["t"][:10] not in keep:
                    continue
                rows.append(r)
    print(w, "roster rows", len(rows), flush=True)
    tape = E.Tape(syms, mons)
    fc = FastCost()
    days = sorted(keep)
    reg = regimes(tape, syms, days)
    sidx = {s: i for i, s in enumerate(syms)}
    didx = {d: i for i, d in enumerate(days)}

    cols = {k: [] for k in ("day", "hour", "bhour", "sym", "fam", "side", "d_bps", "entry",
                            "rg", "rr15", "rrs15", "rr20", "rrs20", "rfil", "rtouch", "rpast",
                            "fg15", "fs15", "fg20", "fs20", "ffil", "ftouch", "fpast",
                            "rcost", "fcost", "vol", "trend",
                            "mr15", "mrs20", "mr20", "mfil", "mf15", "mf20", "mffil", "atm",
                            "af15", "af20", "afil", "afs20")}
    skipped = 0
    for r in rows:
        sym = r["s"]
        if sym not in tape.c:
            skipped += 1; continue
        i = tape.idx(r["t"])
        if not (0 < i < tape.n):
            skipped += 1; continue
        e = r["e"]; sl = r["sl"]
        d = abs(e - sl)
        if not (d > 0):
            skipped += 1; continue
        lng = r["d"] == "L"
        A = walk_arm(tape.h[sym], tape.l[sym], tape.c[sym], tape.n, i, e, sl, lng)
        if A is None:
            skipped += 1; continue
        sl_f = 2.0 * e - sl              # exact mirror about entry, same |d|
        B = walk_arm(tape.h[sym], tape.l[sym], tape.c[sym], tape.n, i, e, sl_f, not lng)
        if B is None:
            skipped += 1; continue
        mkt = tape.last_close_before(sym, i)
        pastA = (mkt <= sl) if lng else (mkt >= sl)
        pastB = (mkt <= sl_f) if (not lng) else (mkt >= sl_f)
        if mkt != mkt:
            pastA = pastB = False
        cA = (fc.px(sym, r["t"], e, lng) / d) if A[0] else 0.0
        cB = (fc.px(sym, r["t"], e, not lng) / d) if B[0] else 0.0
        vt, tr = reg.get((sym, r["t"][:10]), (-1, -1))
        cols["day"].append(didx[r["t"][:10]])
        cols["hour"].append(int(r["t"][11:13]))
        cols["bhour"].append(fc.inst(r["t"])[0])
        cols["sym"].append(sidx[sym])
        cols["fam"].append(FIDX.get(r["f"], len(FAMS)))
        cols["side"].append(1 if lng else 0)
        cols["d_bps"].append(d / e * 1e4)
        cols["entry"].append(e)
        cols["rg"].append(0.0)
        cols["rr15"].append(A[2]); cols["rrs15"].append(A[3])
        cols["rr20"].append(A[4]); cols["rrs20"].append(A[5])
        cols["rfil"].append(A[0]); cols["rtouch"].append(A[1]); cols["rpast"].append(1 if pastA else 0)
        cols["fg15"].append(B[2]); cols["fs15"].append(B[3])
        cols["fg20"].append(B[4]); cols["fs20"].append(B[5])
        cols["ffil"].append(B[0]); cols["ftouch"].append(B[1]); cols["fpast"].append(1 if pastB else 0)
        cols["rcost"].append(cA); cols["fcost"].append(cB)
        cols["vol"].append(vt); cols["trend"].append(tr)
        atm = 1 if r["f"] in ATMARKET else 0
        cols["atm"].append(atm)
        if atm:
            M = walk_market(tape.h[sym], tape.l[sym], tape.c[sym], tape.n, i, e, sl, lng)
            Mf = walk_market(tape.h[sym], tape.l[sym], tape.c[sym], tape.n, i, e, sl_f, not lng)
        else:
            M = Mf = None
        cols["mr15"].append(M[2] if M else 0.0); cols["mr20"].append(M[4] if M else 0.0)
        cols["mrs20"].append(M[5] if M else 0); cols["mfil"].append(1 if M else 0)
        cols["mf15"].append(Mf[2] if Mf else 0.0); cols["mf20"].append(Mf[4] if Mf else 0.0)
        cols["mffil"].append(1 if Mf else 0)
        # ANTI AT THE REAL FILL INSTANT — the only side control that is an order the
        # broker would actually accept for a POI level: a stop order at the same price
        # instead of a limit.  Same price, same trigger event, opposite side.
        AF = None
        if A[0] == 1 and A[1] >= 0:
            j = A[1]
            AF = walk_market(tape.h[sym], tape.l[sym], tape.c[sym], tape.n,
                             i + j, e, sl_f, not lng, horizon=HOR - j - 1)
        cols["af15"].append(AF[2] if AF else 0.0); cols["af20"].append(AF[4] if AF else 0.0)
        cols["afs20"].append(AF[5] if AF else 0); cols["afil"].append(1 if AF else 0)
    del cols["rg"]
    arr = {}
    f32 = {"d_bps", "rr15", "rr20", "fg15", "fg20", "rcost", "fcost",
           "mr15", "mr20", "mf15", "mf20", "af15", "af20"}
    f64 = {"entry"}
    for k, v in cols.items():
        if k in f64:
            arr[k] = np.asarray(v, dtype=np.float64)
        elif k in f32:
            arr[k] = np.asarray(v, dtype=np.float32)
        else:
            arr[k] = np.asarray(v, dtype=np.int16)
    os.makedirs("/tmp/d1/rows3", exist_ok=True)
    np.savez_compressed(f"/tmp/d1/rows3/D1_{w}.npz", **arr)
    json.dump({"window": w, "n": len(cols["day"]), "skipped": skipped, "days": days,
               "syms": syms, "fams": FAMS + ["__other__"], "reasons": REASON,
               "m1_months": mons},
              open(f"/tmp/d1/rows3/D1_{w}.legend.json", "w"))
    print(w, "wrote", len(cols["day"]), "skipped", skipped, flush=True)


if __name__ == "__main__":
    run(sys.argv[1])
