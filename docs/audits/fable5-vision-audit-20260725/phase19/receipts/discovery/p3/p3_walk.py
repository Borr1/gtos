"""p3 — ADVERSARIAL reproduction of d5's "the gross is ZERO at the broker-correct
fill contract" on the reproduced sealed rosters.

Written from the DATA (roster jsonl.gz + raw M1 CSVs), not from d5's script.
Only shared estate artifact reused: pbg_econ.CostModel (the h1 four-term broker-true
cost basis) — the quantity under attack is GROSS, and re-deriving the cost basis
would break comparability with every published number.

Per row it walks EIGHT contracts:

  EST        estate baseline: one-sided fill test from stamp i (long fills on low<=e),
             walk from fill_bar+1, stop wins ties, horizon [i, i+120)
  BC         d5 broker-correct: fill test chosen by the side of the market at T
             (mkt_r0>0 -> resting limit, ==0 -> at-market at i, <0 -> STOP entry)
  REFUSE     BC but every mkt_r0<0 row is never placed (books 0.0, no cost)
  MKT        BC but every 0>mkt_r0>-1 row is filled AT MARKET at stamp i (price
             c[i-1]) with the emitted stop/target levels held; mkt_r0<=-1 refused
  SPRSYM     BC + d8x's SYMMETRIC quote-side shift: stop trigger at d-s, target at
             T*d+s (booked R unchanged at -1/+T: the shift moves WHICH happens)
  SPRMT5     BC + the side/order-type-aware MT5 shift:
               long  : entry trigger level e-s ; exits unshifted
               short : entry trigger level e   ; exit levels sl-s and tp-s
  TIETGT     BC with the same-bar tie resolved to TARGET (bar-resolution probe)
  MIRROR     BC with the side flipped (entry held, stop/target mirrored)

Outputs one npz per window with per-row primitives + per-contract (filled, R).
"""
from __future__ import annotations

import glob
import gzip
import json
import os
import sys
import time
from datetime import datetime, timezone

import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
sys.path.insert(0, PBG)
sys.path.insert(0, REPO)
os.chdir(REPO)
import pbg_econ as E  # noqa: E402  (CostModel only)

HOR = 120
TGT_R = float(os.environ.get("P3_TGT", "2.0"))
NEXT = {"202510": "202511", "202511": "202512", "202512": "202601", "202601": "202602",
        "202602": "202603", "202603": "202604", "202604": "202605", "202605": None}
ROSTER = {"202510": "/tmp/f1/roster_202510", "202511": "/tmp/f1/roster_202511",
          "202512": "/tmp/f1/roster_202512", "202601": "/tmp/pbg_full_jan",
          "202602": "/tmp/pbg_full_feb", "202603": "/tmp/pbg_full_mar",
          "202604": "/tmp/f1/roster_202604", "202605": "/tmp/f1/roster_202605"}
CONTRACTS = ["EST", "BC", "REFUSE", "MKT", "SPRSYM", "SPRMT5", "TIETGT", "MIRROR"]


# --------------------------------------------------------------- own tape loader
def load_tape(months):
    t0 = datetime(int(months[0][:4]), int(months[0][4:]), 1, tzinfo=timezone.utc)
    ly, lm = int(months[-1][:4]), int(months[-1][4:])
    y2, m2 = (ly + 1, 1) if lm == 12 else (ly, lm + 1)
    t1 = datetime(y2, m2, 1, tzinfo=timezone.utc)
    n = int((t1 - t0).total_seconds() // 60)
    syms = sorted({os.path.basename(p)[:-7]
                   for mm in months
                   for p in glob.glob(f"{BARS}/bridge_ftmo_m1_{mm}/*_M1.csv")})
    O = {}
    H = {}
    L = {}
    C = {}
    for sym in syms:
        o = np.full(n, np.nan)
        h = np.full(n, np.nan)
        lo = np.full(n, np.nan)
        c = np.full(n, np.nan)
        for mm in months:
            p = f"{BARS}/bridge_ftmo_m1_{mm}/{sym}_M1.csv"
            if not os.path.isfile(p):
                continue
            with open(p, "r") as fh:
                fh.readline()
                for line in fh:
                    f = line.rstrip("\n").split(",")
                    ts = datetime.fromisoformat(f[0])
                    i = int((ts - t0).total_seconds() // 60)
                    if 0 <= i < n:
                        o[i] = float(f[1]); h[i] = float(f[2])
                        lo[i] = float(f[3]); c[i] = float(f[4])
        O[sym], H[sym], L[sym], C[sym] = o, h, lo, c
    return t0, n, O, H, L, C


# ------------------------------------------------------------------- own walker
def outcome(h, l, c, ok, a, b, long, entry, stop, tgt, d, tie_stop=True):
    """Path bars [a,b).  Returns (r, code) code 0=stop 1=target 2=path_end."""
    if a >= b:
        return None
    hh = h[a:b]; ll = l[a:b]; cc = c[a:b]; oo = ok[a:b]
    if not oo.any():
        return None
    hh = hh[oo]; ll = ll[oo]; cc = cc[oo]
    if long:
        hs = ll <= stop
        ht = hh >= tgt
    else:
        hs = hh >= stop
        ht = ll <= tgt
    any_s = hs.any(); any_t = ht.any()
    i_s = int(np.argmax(hs)) if any_s else -1
    i_t = int(np.argmax(ht)) if any_t else -1
    if any_s and (not any_t or (i_s < i_t) or (i_s == i_t and tie_stop)):
        return ((stop - entry) / d if long else (entry - stop) / d), 0
    if any_t:
        return ((tgt - entry) / d if long else (entry - tgt) / d), 1
    last = float(cc[-1])
    return ((last - entry) / d if long else (entry - last) / d), 2


def fill_index(h, l, ok, a, b, level, from_below):
    """First stamp in [a,b) whose bar reaches `level`.
    from_below=True  -> need high >= level ; False -> need low <= level."""
    if a >= b:
        return -1
    hh = h[a:b]; ll = l[a:b]; oo = ok[a:b]
    if not oo.any():
        return -1
    idx = np.nonzero(oo)[0]
    hit = (hh[idx] >= level) if from_below else (ll[idx] <= level)
    if not hit.any():
        return -1
    return a + int(idx[int(np.argmax(hit))])


def run(win):
    t_start = time.time()
    months = [win] + ([NEXT[win]] if NEXT.get(win) else [])
    t0, n, O, H, L, C = load_tape(months)
    sys.stderr.write("%s tape %.0fs n=%d syms=%d\n" % (win, time.time() - t_start, n, len(C)))
    cm = E.CostModel()
    hour_cache = {}
    spread_cache = {}

    rows = []
    for f in sorted(glob.glob(ROSTER[win] + "/*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] == 15:
                    rows.append(r)
    lim = int(os.environ.get("P3_LIMIT", "0"))
    if lim:
        rows = rows[:lim]
    sys.stderr.write("%s roster k15 %d\n" % (win, len(rows)))

    symids, famids, dayids = {}, {}, {}
    out = {k: [] for k in ("sym", "fam", "day", "hour", "side", "e", "d", "riskbps",
                           "mkt_r0", "sp_px", "cost_r")}
    for cn in CONTRACTS:
        out["f_" + cn] = []
        out["r_" + cn] = []
    drops = {"sym": 0, "idx": 0, "d0": 0, "prev": 0, "fwd": 0}

    okc = {s: ~np.isnan(C[s]) for s in C}
    for r in rows:
        sym = r["s"]
        if sym not in C:
            drops["sym"] += 1
            continue
        ts = datetime.fromisoformat(r["t"])
        i = int((ts - t0).total_seconds() // 60)
        if not (0 < i < n - 2):
            drops["idx"] += 1
            continue
        e = float(r["e"]); sl = float(r["sl"]); d = abs(e - sl)
        if not (d > 0):
            drops["d0"] += 1
            continue
        lng = r["d"] == "L"
        s = 1.0 if lng else -1.0
        c = C[sym]; h = H[sym]; l = L[sym]; ok = okc[sym]
        m0 = c[i - 1]
        if m0 != m0:
            drops["prev"] += 1
            continue
        b = min(i + HOR, n)
        if not ok[i:b].any():
            drops["fwd"] += 1
            continue
        mkt = s * (m0 - e) / d
        key = r["t"][:13]
        bh = hour_cache.get(key)
        if bh is None:
            bh = cm.broker_hour(r["t"])
            hour_cache[key] = bh
        skey = (sym, bh)
        sb = spread_cache.get(skey)
        if sb is None:
            sb = cm.spread_bps(sym, bh)
            spread_cache[skey] = sb
        sp = sb / 1e4 * e
        cost_px, _ = cm.cost_px(sym, r["t"], e, lng, hold_min=HOR)
        cost_r = cost_px / d

        tgt = e + s * TGT_R * d
        res = {}

        # ---- EST : one-sided fill test (long fills on low<=e) from stamp i
        fi = fill_index(h, l, ok, i, b, e, from_below=not lng)
        if fi < 0:
            res["EST"] = (0, 0.0)
        else:
            o1 = outcome(h, l, c, ok, fi + 1, b, lng, e, sl, tgt, d, True)
            res["EST"] = (0, 0.0) if o1 is None else (1, o1[0])

        # ---- order type at T
        atmkt = abs(mkt) < 1e-12
        limit = mkt > 1e-12          # entry at price improvement
        stopent = mkt < -1e-12       # entry beyond the market in the losing direction

        # ---- BC : broker-correct fill side
        if atmkt:
            fi_bc = i
        elif limit:
            fi_bc = fill_index(h, l, ok, i, b, e, from_below=not lng)
        else:
            fi_bc = fill_index(h, l, ok, i, b, e, from_below=lng)
        if fi_bc < 0:
            res["BC"] = (0, 0.0)
        else:
            o1 = outcome(h, l, c, ok, fi_bc + 1, b, lng, e, sl, tgt, d, True)
            res["BC"] = (0, 0.0) if o1 is None else (1, o1[0])

        # ---- REFUSE : never place a stop-entry row
        res["REFUSE"] = (0, 0.0) if stopent else res["BC"]

        # ---- MKT : marketable-limit reading (fill NOW at the achievable price)
        if stopent and mkt > -1.0:
            o1 = outcome(h, l, c, ok, i + 1, b, lng, m0, sl, tgt, d, True)
            res["MKT"] = (0, 0.0) if o1 is None else (1, o1[0])
        elif stopent:
            res["MKT"] = (0, 0.0)          # born past its own stop -> never placed
        else:
            res["MKT"] = res["BC"]

        # ---- SPRSYM : d8x symmetric quote-side shift on the EXIT triggers
        if fi_bc < 0:
            res["SPRSYM"] = (0, 0.0)
        else:
            sl2 = e - s * (d - sp)
            tg2 = e + s * (TGT_R * d + sp)
            o1 = outcome(h, l, c, ok, fi_bc + 1, b, lng, e, sl2, tg2, d, True)
            if o1 is None:
                res["SPRSYM"] = (0, 0.0)
            else:
                rr = -1.0 if o1[1] == 0 else (TGT_R if o1[1] == 1 else o1[0])
                res["SPRSYM"] = (1, rr)

        # ---- SPRMT5 : side/order-type aware MT5 trigger sides
        if lng:
            lvl = e - sp
            if atmkt:
                fi_s = i
            elif limit:
                fi_s = fill_index(h, l, ok, i, b, lvl, from_below=False)
            else:
                fi_s = fill_index(h, l, ok, i, b, lvl, from_below=True)
            sl3, tg3 = sl, tgt
        else:
            fi_s = fi_bc                      # short entry triggers on the bid: unshifted
            sl3, tg3 = sl - sp, tgt - sp
        if fi_s < 0:
            res["SPRMT5"] = (0, 0.0)
        else:
            o1 = outcome(h, l, c, ok, fi_s + 1, b, lng, e, sl3, tg3, d, True)
            if o1 is None:
                res["SPRMT5"] = (0, 0.0)
            else:
                rr = -1.0 if o1[1] == 0 else (TGT_R if o1[1] == 1 else o1[0])
                res["SPRMT5"] = (1, rr)

        # ---- TIETGT : BC with the same-bar tie given to the target
        if fi_bc < 0:
            res["TIETGT"] = (0, 0.0)
        else:
            o1 = outcome(h, l, c, ok, fi_bc + 1, b, lng, e, sl, tgt, d, False)
            res["TIETGT"] = (0, 0.0) if o1 is None else (1, o1[0])

        # ---- MIRROR : same entry, side flipped (stop and target mirrored)
        mlng = not lng
        ms = -s
        msl = e - ms * d
        mtg = e + ms * TGT_R * d
        # the fill trigger depends only on where the market sits relative to the
        # LEVEL, so the mirror fills at exactly the same instant as the real order.
        fi_m = fi_bc
        if fi_m < 0:
            res["MIRROR"] = (0, 0.0)
        else:
            o1 = outcome(h, l, c, ok, fi_m + 1, b, mlng, e, msl, mtg, d, True)
            res["MIRROR"] = (0, 0.0) if o1 is None else (1, o1[0])

        symids.setdefault(sym, len(symids))
        famids.setdefault(r["f"], len(famids))
        day = r["t"][:10]
        dayids.setdefault(day, len(dayids))
        out["sym"].append(symids[sym]); out["fam"].append(famids[r["f"]])
        out["day"].append(dayids[day]); out["hour"].append(int(r["t"][11:13]))
        out["side"].append(s); out["e"].append(e); out["d"].append(d)
        out["riskbps"].append(d / e * 1e4); out["mkt_r0"].append(mkt)
        out["sp_px"].append(sp); out["cost_r"].append(cost_r)
        for cn in CONTRACTS:
            out["f_" + cn].append(res[cn][0])
            out["r_" + cn].append(res[cn][1])

    arrs = {k: np.asarray(v, dtype=np.float64) for k, v in out.items()}
    np.savez_compressed("/tmp/p3/P3_%s.npz" % win,
                        symnames=np.array(sorted(symids, key=symids.get)),
                        famnames=np.array(sorted(famids, key=famids.get)),
                        daynames=np.array(sorted(dayids, key=dayids.get)),
                        drops=np.array([drops[k] for k in sorted(drops)]),
                        dropkeys=np.array(sorted(drops)),
                        **arrs)
    sys.stderr.write("%s DONE rows=%d %.0fs drops=%s\n"
                     % (win, len(out["sym"]), time.time() - t_start, drops))


if __name__ == "__main__":
    run(sys.argv[1])
