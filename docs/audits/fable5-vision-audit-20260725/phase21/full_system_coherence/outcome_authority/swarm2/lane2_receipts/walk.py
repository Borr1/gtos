#!/usr/bin/env python3
"""Lane 2 horizon walker.

Reproduces `resolve_post_submission_m1_lifecycle` (src/research_infra/walkforward/
quote_side.py:1032) exactly at the sealed horizon, then re-resolves the same fill at
longer horizons. Two arms:
  SEALED  -- censors on any M1 interval gap, exactly as the committed resolver does.
  TOLERANT-- treats an M1 gap as unobserved time and keeps walking (declared deviation,
             required because a 4x/8x wall-clock horizon always crosses a session break).
Validation: at 1x the SEALED arm must reproduce the sealed corpus label.
"""
import bisect, csv, gzip, json, pickle, sys, time
import datetime as dt
from pathlib import Path
import numpy as np

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
sys.path.insert(0, str(WT))
from src.research_infra.walkforward.quote_side import spread_for

HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
BARS = HOLD / ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars"
MANI = HOLD / ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/manifests"
CACHE = "/private/tmp/w21-puzzle-cache/rows_%s.pkl.gz"
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
MONTH_SRC = {"feb": ["202602", "202603"], "apr": ["202604", "202605"],
             "may": ["202605", "202606"], "jun": ["202606", "202607"],
             "jul": ["202607"]}
import os
MULTS = [float(x) for x in os.environ.get("MULTS","1,2,4,8").split(",")]
TAG = os.environ.get("TAG","")
T0 = time.time()
def log(**kw): print(json.dumps({"t": round(time.time()-T0,1), **kw}, sort_keys=True), flush=True)

def mins(t): return int((t - EPOCH).total_seconds() // 60)
def at(s): return dt.datetime.fromisoformat(str(s).replace("Z","+00:00"))

def load_symbol_series(month):
    """Concatenated M1 for the month and its successor, per symbol, with exit/entry offsets."""
    per = {}
    for tag in MONTH_SRC[month]:
        d = BARS / f"bridge_ftmo_m1_{tag}"
        for p in sorted(d.glob("*_M1.csv")):
            sym = p.name[:-7]
            rows = per.setdefault(sym, [])
            with p.open(newline="") as fh:
                rd = csv.DictReader(fh)
                for row in rd:
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
            if hr not in cache: cache[hr] = spread_for(sym, hr, account="FTMO", band="mid")
            spr[i] = cache[hr]
        out[sym] = dict(t=tm, o=o, h=h, l=lo, c=c, s=spr)
    return out

def walk_month(month):
    ser = load_symbol_series(month)
    log(stage="bars_loaded", month=month, symbols=len(ser),
        rows=int(sum(len(v["t"]) for v in ser.values())))
    geom = {}
    with gzip.open(f"geom_{month}.jsonl.gz", "rt") as fh:
        for line in fh:
            r = json.loads(line); geom[r["k"]] = r
    rows = pickle.load(gzip.open(CACHE % month, "rb"))
    log(stage="joined", month=month, cache=len(rows), geom=len(geom))

    recs = []
    for row in rows:
        g = geom.get(row["candidate_occurrence_key"])
        if g is None: continue
        sym = g["symbol"]; S = ser.get(sym)
        if S is None: continue
        d = 1 if str(g["side"]).upper() == "LONG" else -1
        entry = float(g["entry_price"]); stop = float(g["stop_loss"]); target = float(g["take_profit_1"])
        risk = abs(entry - stop)
        sub = at(g["decision_time_utc"]); exp = at(g["limit_first_expiry_utc"])
        sm, em = mins(sub), mins(exp)
        H1 = em - sm
        t = S["t"]
        i = int(np.searchsorted(t, sm, side="right")) - 1
        rec = dict(k=row["candidate_occurrence_key"], month=month, sym=sym,
                   fam=row["origin_family"], ot=row["proposed_order_type"], side=g["side"],
                   day=g["trading_day"], sub=sm, H1=H1,
                   ded=float(row.get("deductible_cost_r") or 0.0),
                   sealed_status=row["lifecycle_label_status"],
                   sealed_net=row.get("terminal_net_r"), risk=risk)
        if i < 0 or t[i] != sm:
            rec["err"] = "submission_bar_missing"; recs.append(rec); continue
        # exit-side and entry-side transformed arrays are built lazily per candidate slice
        eoff = 0.0 if d > 0 else S["s"]           # exit offset: BID basis -> long bid(0), short ask(+spread)
        aoff = S["s"] if d > 0 else 0.0           # entry offset: long ask(+spread), short bid(0)
        n = len(t)
        # ---- fill ----------------------------------------------------------
        succ = i + 1
        if succ >= n or t[succ] != sm + 1:
            rec["err"] = "no_contiguous_successor"; recs.append(rec); continue
        if rec["ot"] == "MARKET":
            if t[succ] >= em: rec["err"] = "market_expires_before_successor"; recs.append(rec); continue
            fi = succ; fp = S["o"][succ] + (aoff[succ] if d > 0 else 0.0); fill_at_open = True
        else:
            def ebar(j):
                a = aoff[j] if d > 0 else 0.0
                return (S["o"][j]+a, S["h"][j]+a, S["l"][j]+a, S["c"][j]+a)
            v0 = ebar(i)
            if (v0[2] <= entry) if d > 0 else (v0[1] >= entry):
                rec["err"] = "CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_ORDERING"; recs.append(rec); continue
            prev, cur, fi = i, succ, None
            while True:
                if cur >= n or t[cur] != t[prev] + 1:
                    rec["err"] = "gap_before_limit_expiry"; break
                op = t[cur]
                if op >= em: rec["err"] = "NO_FILL"; break
                v = ebar(cur)
                fav = (v[0] <= entry) if d > 0 else (v[0] >= entry)
                tou = (v[2] <= entry) if d > 0 else (v[1] >= entry)
                if fav: fi, fp, fill_at_open = cur, v[0], True; break
                if op + 1 > em:
                    rec["err"] = "CENSORED_ORDERING_AMBIGUITY" if tou else "NO_FILL"; break
                if tou: fi, fp, fill_at_open = cur, entry, False; break
                if op + 1 == em: rec["err"] = "NO_FILL"; break
                prev, cur = cur, cur + 1
            if fi is None: recs.append(rec); continue
        # invalid-gap guard (fill at open only)
        xo = S["o"][fi] + (eoff[fi] if d < 0 else 0.0)
        if fill_at_open and (d*(stop-fp)/risk >= 0 or d*(target-fp)/risk <= 0
                             or ((xo <= stop) if d > 0 else (xo >= stop))
                             or ((xo >= target) if d > 0 else (xo <= target))):
            rec["err"] = "CENSORED_INVALID_GAP_THROUGH_SL_OR_TP"; recs.append(rec); continue
        rec.update(fi=int(fi), fp=float(fp), fill_min=int(t[fi]), fill_at_open=bool(fill_at_open))
        # ---- barrier scan over the maximal window ---------------------------
        maxend = min(n, fi + 1 + 60*24*40)
        sl = slice(fi, maxend)
        off = eoff[sl] if d < 0 else 0.0
        O = S["o"][sl] + off; H = S["h"][sl] + off; L = S["l"][sl] + off; C = S["c"][sl] + off
        TT = t[sl]
        if d > 0:
            so = O <= stop; to = O >= target; hs = L <= stop; ht = H >= target
        else:
            so = O >= stop; to = O <= target; hs = H >= stop; ht = L <= target
        ev = np.zeros(len(TT), dtype=np.int8)          # 0 none 1 stop 2 target 3 censor
        px = np.zeros(len(TT))
        ev[hs & ht] = 3
        ev[hs & ~ht] = 1; px[hs & ~ht] = stop
        ev[ht & ~hs] = 2; px[ht & ~hs] = target
        ev[to] = 2; px[to] = O[to]
        ev[so] = 1; px[so] = O[so]
        # fill bar: no open-gap rule; intrabar limit fill + any touch -> censor
        ev[0] = 0
        if hs[0] or ht[0]:
            ev[0] = 3 if (not fill_at_open or (hs[0] and ht[0])) else (1 if hs[0] else 2)
            px[0] = stop if ev[0] == 1 else (target if ev[0] == 2 else 0.0)
        gapj = np.nonzero(np.diff(TT) != 1)[0]
        first_gap = int(gapj[0]) + 1 if len(gapj) else len(TT)   # first index not contiguous
        nz = np.nonzero(ev)[0]
        rec["first_gap_min"] = int(TT[first_gap-1]) + 1 if first_gap < len(TT) else None
        rec["ev_j"] = int(nz[0]) if len(nz) else None
        rec["ev_kind"] = int(ev[nz[0]]) if len(nz) else 0
        rec["ev_px"] = float(px[nz[0]]) if len(nz) else None
        rec["ev_min"] = int(TT[nz[0]]) + (0 if (len(nz) and (so[nz[0]] or to[nz[0]])) else 1) if len(nz) else None
        rec["last_min"] = int(TT[-1]); rec["nbars"] = int(len(TT))
        # per-horizon marks + MFE/MAE, TOLERANT arm
        fav = (H - fp)*d/risk if d > 0 else (L - fp)*d/risk
        adv = (L - fp)*d/risk if d > 0 else (H - fp)*d/risk
        cum_fav = np.maximum.accumulate(fav); cum_adv = np.minimum.accumulate(adv)
        for mlt in MULTS:
            hz = sm + H1*mlt
            # last complete bar strictly before horizon
            jj = int(np.searchsorted(TT, hz - 1, side="right")) - 1
            if jj < 0: rec[f"h{mlt}"] = None; continue
            if rec["ev_j"] is not None and TT[rec["ev_j"]] < hz and rec["ev_min"] <= hz:
                j = rec["ev_j"]
                kind = {1:"STOP",2:"TARGET",3:"CENSOR"}[rec["ev_kind"]]
                gross = d*(rec["ev_px"] - fp)/risk if rec["ev_kind"] in (1,2) else None
                endm = rec["ev_min"]
            else:
                j = jj; kind = "TIME_STOP"; gross = float(d*(C[jj]-fp)/risk); endm = int(TT[jj])+1
            rec[f"h{mlt}"] = dict(kind=kind, gross=gross, end=endm,
                                  mfe=float(cum_fav[j]), mae=float(cum_adv[j]),
                                  gapped=bool(j >= first_gap))
        # unbounded (to end of available bars)
        if rec["ev_j"] is not None:
            rec["hInf"] = dict(kind={1:"STOP",2:"TARGET",3:"CENSOR"}[rec["ev_kind"]],
                               gross=(d*(rec["ev_px"]-fp)/risk if rec["ev_kind"] in (1,2) else None),
                               end=rec["ev_min"], mfe=float(cum_fav[rec["ev_j"]]),
                               mae=float(cum_adv[rec["ev_j"]]),
                               gapped=bool(rec["ev_j"] >= first_gap))
        else:
            rec["hInf"] = dict(kind="RUNOUT", gross=float(d*(C[-1]-fp)/risk), end=int(TT[-1])+1,
                               mfe=float(cum_fav[-1]), mae=float(cum_adv[-1]), gapped=True)
        recs.append(rec)
    with gzip.open(f"walk{TAG}_{month}.pkl.gz","wb") as fh: pickle.dump(recs, fh, protocol=5)
    log(stage="month_done", month=month, recs=len(recs))
    return len(recs)

if __name__ == "__main__":
    for m in sys.argv[1:] or ["feb","apr","may","jun","jul"]:
        walk_month(m)
    log(stage="ALL_DONE")
