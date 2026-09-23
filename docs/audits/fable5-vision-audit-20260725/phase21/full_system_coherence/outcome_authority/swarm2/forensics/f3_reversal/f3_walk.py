#!/usr/bin/env python3
"""F3 reversal walker — captures the PATH, not just the endpoints.

Built on lane2_receipts/walk.py, which reproduces
`resolve_post_submission_m1_lifecycle` (src/research_infra/walkforward/quote_side.py:1032)
byte-exactly at the sealed horizon (VALIDATE_1X.json: 0.0 max deviation on 146,736 fills).
The fill logic, the exit-side quote transform, the invalid-gap guard and the barrier scan
are copied verbatim.  What is added is the excursion path:

  * every NEW RUNNING HIGH in the favourable coordinate,
  * the retrace that followed it before the next new high,
  * which of those was terminal (the peak that was never exceeded).

That yields, per trade, one TERMINAL stall (the reversal point the owner is asking about)
and 0..K NON-TERMINAL stalls (advances that retraced by the same amount and then RESUMED).
The non-terminal stalls are the matched control for every structural claim in F3: same
symbol, same day, same trade, same volatility, same retrace magnitude — differing only in
whether the move resumed.

Emits per month:
  f3_trades_<m>.pkl.gz  one row per filled trade
  f3_stalls_<m>.pkl.gz  one row per stall (kind = "peak" | "pause")
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
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f3")
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
MONTH_SRC = {"feb": ["202602", "202603"], "apr": ["202604", "202605"],
             "may": ["202605", "202606"], "jun": ["202606", "202607"],
             "jul": ["202607"]}
DELTA = float(os.environ.get("DELTA", "0.25"))   # retrace that defines a "stall", in R
MAXPAUSE = 12
T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def mins(t):
    return int((t - EPOCH).total_seconds() // 60)


def at(s):
    return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def load_symbol_series(month):
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


def walk_month(month):
    ser = load_symbol_series(month)
    log(stage="bars_loaded", month=month, symbols=len(ser),
        rows=int(sum(len(v["t"]) for v in ser.values())))
    geom = {}
    with gzip.open(GEOM / f"geom_{month}.jsonl.gz", "rt") as fh:
        for line in fh:
            r = json.loads(line)
            geom[r["k"]] = r
    rows = pickle.load(gzip.open(CACHE % month, "rb"))
    log(stage="joined", month=month, cache=len(rows), geom=len(geom))

    trades, stalls = [], []
    for row in rows:
        g = geom.get(row["candidate_occurrence_key"])
        if g is None:
            continue
        sym = g["symbol"]; S = ser.get(sym)
        if S is None:
            continue
        d = 1 if str(g["side"]).upper() == "LONG" else -1
        entry = float(g["entry_price"]); stop = float(g["stop_loss"]); target = float(g["take_profit_1"])
        risk = abs(entry - stop)
        sub = at(g["decision_time_utc"]); exp = at(g["limit_first_expiry_utc"])
        sm, em = mins(sub), mins(exp)
        H1 = em - sm
        t = S["t"]
        i = int(np.searchsorted(t, sm, side="right")) - 1
        ot = row["proposed_order_type"]
        if i < 0 or t[i] != sm:
            continue
        eoff = 0.0 if d > 0 else S["s"]
        aoff = S["s"] if d > 0 else 0.0
        n = len(t)
        # ---- fill (verbatim from lane2 walk.py) ----------------------------
        succ = i + 1
        if succ >= n or t[succ] != sm + 1:
            continue
        if ot == "MARKET":
            if t[succ] >= em:
                continue
            fi = succ; fp = S["o"][succ] + (aoff[succ] if d > 0 else 0.0); fill_at_open = True
        else:
            def ebar(j):
                a = aoff[j] if d > 0 else 0.0
                return (S["o"][j] + a, S["h"][j] + a, S["l"][j] + a, S["c"][j] + a)
            v0 = ebar(i)
            if (v0[2] <= entry) if d > 0 else (v0[1] >= entry):
                continue
            prev, cur, fi = i, succ, None
            while True:
                if cur >= n or t[cur] != t[prev] + 1:
                    break
                op = t[cur]
                if op >= em:
                    break
                v = ebar(cur)
                fav_ = (v[0] <= entry) if d > 0 else (v[0] >= entry)
                tou = (v[2] <= entry) if d > 0 else (v[1] >= entry)
                if fav_:
                    fi, fp, fill_at_open = cur, v[0], True; break
                if op + 1 > em:
                    break
                if tou:
                    fi, fp, fill_at_open = cur, entry, False; break
                if op + 1 == em:
                    break
                prev, cur = cur, cur + 1
            if fi is None:
                continue
        xo = S["o"][fi] + (eoff[fi] if d < 0 else 0.0)
        if fill_at_open and (d * (stop - fp) / risk >= 0 or d * (target - fp) / risk <= 0
                             or ((xo <= stop) if d > 0 else (xo >= stop))
                             or ((xo >= target) if d > 0 else (xo <= target))):
            continue
        # ---- barrier scan (verbatim) ---------------------------------------
        maxend = min(n, fi + 1 + 60 * 24 * 40)
        sl = slice(fi, maxend)
        off = eoff[sl] if d < 0 else 0.0
        O = S["o"][sl] + off; H = S["h"][sl] + off; L = S["l"][sl] + off; C = S["c"][sl] + off
        Hr = S["h"][sl]; Lr = S["l"][sl]                     # RAW prices, for level tests
        TT = t[sl]
        if d > 0:
            so = O <= stop; to = O >= target; hs = L <= stop; ht = H >= target
        else:
            so = O >= stop; to = O <= target; hs = H >= stop; ht = L <= target
        ev = np.zeros(len(TT), dtype=np.int8); px = np.zeros(len(TT))
        ev[hs & ht] = 3
        ev[hs & ~ht] = 1; px[hs & ~ht] = stop
        ev[ht & ~hs] = 2; px[ht & ~hs] = target
        ev[to] = 2; px[to] = O[to]
        ev[so] = 1; px[so] = O[so]
        ev[0] = 0
        if hs[0] or ht[0]:
            ev[0] = 3 if (not fill_at_open or (hs[0] and ht[0])) else (1 if hs[0] else 2)
            px[0] = stop if ev[0] == 1 else (target if ev[0] == 2 else 0.0)
        nz = np.nonzero(ev)[0]
        ev_j = int(nz[0]) if len(nz) else None
        ev_kind = int(ev[nz[0]]) if len(nz) else 0
        ev_px = float(px[nz[0]]) if len(nz) else None
        ev_min = (int(TT[nz[0]]) + (0 if (so[nz[0]] or to[nz[0]]) else 1)) if len(nz) else None
        # ---- terminal at the SEALED 1x horizon ------------------------------
        hz = sm + H1
        jj = int(np.searchsorted(TT, hz - 1, side="right")) - 1
        if jj < 0:
            continue
        if ev_j is not None and TT[ev_j] < hz and ev_min <= hz:
            jT = ev_j
            kind = {1: "STOP", 2: "TARGET", 3: "CENSOR"}[ev_kind]
            gross = d * (ev_px - fp) / risk if ev_kind in (1, 2) else None
            endm = ev_min
        else:
            jT = jj; kind = "TIME_STOP"; gross = float(d * (C[jj] - fp) / risk); endm = int(TT[jj]) + 1
        if gross is None:      # CENSOR — no economic terminal
            continue
        # ---- the excursion path ---------------------------------------------
        fav = (H[:jT + 1] - fp) * d / risk if d > 0 else (L[:jT + 1] - fp) * d / risk
        rlo = (L[:jT + 1] - fp) * d / risk if d > 0 else (H[:jT + 1] - fp) * d / risk
        pk_raw = Hr[:jT + 1] if d > 0 else Lr[:jT + 1]
        cum = np.maximum.accumulate(fav)
        mfe = float(cum[-1]); mae = float(np.minimum.accumulate(rlo)[-1])
        newhi = np.nonzero(np.concatenate([[True], fav[1:] > cum[:-1]]))[0]
        peak_j = int(newhi[-1])
        recs = []
        for a in range(len(newhi)):
            j = int(newhi[a])
            nxt = int(newhi[a + 1]) if a + 1 < len(newhi) else jT + 1
            trough = float(np.min(rlo[j:nxt])) if nxt > j else float(rlo[j])
            retr = float(fav[j]) - trough
            is_peak = (j == peak_j)
            if is_peak:
                retr = float(fav[j]) - float(gross)     # give-back to the terminal mark
            if not is_peak and retr < DELTA:
                continue
            recs.append(dict(j=j, minute=int(TT[j]), px=float(pk_raw[j]), fav=float(fav[j]),
                             retr=retr, peak=is_peak, bars=j))
        pauses = [r for r in recs if not r["peak"]][-MAXPAUSE:]
        pk = [r for r in recs if r["peak"]][0]
        tr = dict(k=row["candidate_occurrence_key"], month=month, sym=sym, fam=row["origin_family"],
                  ot=ot, side=g["side"], day=g["trading_day"], sub=sm, H1=H1, fill_min=int(TT[0]),
                  fp=float(fp), entry=entry, stop=stop, target=target, risk=risk,
                  ded=float(row.get("deductible_cost_r") or 0.0),
                  term_kind=kind, term_min=int(endm), term_gross=float(gross),
                  mfe=mfe, mae=mae, peak_min=pk["minute"], peak_px=pk["px"], peak_bars=pk["bars"],
                  give_back=float(mfe) - float(gross), n_pause=len(pauses),
                  sealed_status=row["lifecycle_label_status"], sealed_net=row.get("sealed_net"),
                  utc_hour=row.get("utc_hour"), sess=row.get("utc_session"))
        trades.append(tr)
        for r in [pk] + pauses:
            stalls.append(dict(k=tr["k"], month=month, sym=sym, side=g["side"], fam=tr["fam"],
                               day=tr["day"], kind="peak" if r["peak"] else "pause",
                               minute=r["minute"], px=r["px"], fav=r["fav"], retr=r["retr"],
                               bars=r["bars"], risk=risk, fp=float(fp), entry=entry,
                               stop=stop, target=target, term_kind=kind,
                               term_gross=float(gross), mfe=mfe))
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT / f"f3_trades_{month}.pkl.gz", "wb") as fh:
        pickle.dump(trades, fh, protocol=5)
    with gzip.open(OUT / f"f3_stalls_{month}.pkl.gz", "wb") as fh:
        pickle.dump(stalls, fh, protocol=5)
    log(stage="month_done", month=month, trades=len(trades), stalls=len(stalls))


if __name__ == "__main__":
    for m in sys.argv[1:] or ["feb", "apr", "may", "jun", "jul"]:
        walk_month(m)
    log(stage="ALL_DONE")
