#!/usr/bin/env python3
"""F1 excursion census walker.

Extends the Lane 2 walker (swarm2/lane2_receipts/walk.py), which reproduces
`resolve_post_submission_m1_lifecycle`
(src/research_infra/walkforward/quote_side.py:1032) at 1.000000 status agreement
on feb/may and 0.0 max deviation on terminal net R for every filled row in all
five months (lane2_receipts/VALIDATE_1X.json).

What this adds, per FILLED candidate:
  * MFE / MAE in R from the actual fill price, with time-to-each in minutes,
    both inclusive of the exit bar (upper bound) and strictly before it
    (path-unambiguous lower bound).
  * ordering (did MAE precede MFE)
  * R at each decile of the holding period (path shape)
  * give-back (MFE surrendered before exit)
  * near-miss ladder (max level touched before the exit bar)
  * winner fragility (how close the MAE came to the stop)
  * a TARGET LADDER re-walk: the same fill, same 1R stop, same clock, resolved
    against 9 alternative take-profit levels, at the sealed 1x horizon and at a
    12x (24 h) horizon.

Conventions inherited verbatim from the sealed resolver:
  entry side  -- LONG pays ASK (raw + spread), SHORT sells BID (raw)
  exit side   -- LONG exits BID (raw),         SHORT exits ASK (raw + spread)
  MARKET fill -- open of the first complete successor bar
  LIMIT fill  -- favourable open, else intrabar touch at the limit price
  same-bar both-barriers-touched -> CENSOR
  mark        -- close of the last complete bar strictly before the horizon
"""
import gzip, json, os, pickle, sys, time
import datetime as dt
from pathlib import Path
import numpy as np

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
sys.path.insert(0, str(WT))
from src.research_infra.walkforward.quote_side import spread_for  # noqa: E402

LANE2 = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane2")
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f1")
OUT.mkdir(parents=True, exist_ok=True)
HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
BARS = HOLD / ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars"
CACHE = "/private/tmp/w21-puzzle-cache/rows_%s.pkl.gz"
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
MONTH_SRC = {"feb": ["202602", "202603"], "apr": ["202604", "202605"],
             "may": ["202605", "202606"], "jun": ["202606", "202607"],
             "jul": ["202607"]}

# target ladder, in R from the DECLARED entry (the estate ships 2.0)
TARGETS = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
# near-miss ladder levels, in R from the DECLARED entry
LEVELS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 1.8, 1.9, 2.0]
EXT_MULT = 12.0            # extended horizon arm = 12x the sealed clock (24 h)
EXT_BARS = 1600            # bar cap for the extended arm

T0 = time.time()
def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)

def mins(t): return int((t - EPOCH).total_seconds() // 60)
def at(s): return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def load_symbol_series(month):
    """Concatenated true-UTC M1 for the month and its successor, per symbol."""
    import csv
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


def resolve(openR, favR, advR, closeR, TT, stop_r, tgt_r, fill_at_open, hz_min):
    """Generalised barrier resolution in R space, mirroring the sealed resolver.

    Returns (kind, gross_r, end_min, exit_idx).  `hz_min` is the horizon in absolute
    minutes; the mark is the close of the last complete bar strictly before it.
    """
    n = len(TT)
    so = openR <= stop_r          # open gapped through the stop
    to = openR >= tgt_r           # open gapped through the target
    hs = advR <= stop_r           # intrabar stop touch
    ht = favR >= tgt_r            # intrabar target touch
    ev = np.zeros(n, dtype=np.int8)   # 0 none 1 stop 2 target 3 censor
    px = np.zeros(n)
    ev[hs & ht] = 3
    m = hs & ~ht; ev[m] = 1; px[m] = stop_r
    m = ht & ~hs; ev[m] = 2; px[m] = tgt_r
    ev[to] = 2; px[to] = openR[to]
    ev[so] = 1; px[so] = openR[so]
    # fill bar: no open-gap rule (guarded upstream); a limit fill that also touches
    # in its own bar is ordering-ambiguous -> censor
    ev[0] = 0; px[0] = 0.0
    if hs[0] or ht[0]:
        if (not fill_at_open) or (hs[0] and ht[0]):
            ev[0] = 3
        else:
            ev[0] = 1 if hs[0] else 2
            px[0] = stop_r if hs[0] else tgt_r
    nz = np.nonzero(ev)[0]
    if len(nz):
        j = int(nz[0])
        # the barrier event lands ON the bar open (so/to) or somewhere inside it
        on_open = bool(so[j] or to[j])
        end = int(TT[j]) + (0 if on_open else 1)
        if TT[j] < hz_min and end <= hz_min:
            kind = {1: "STOP", 2: "TARGET", 3: "CENSOR"}[int(ev[j])]
            return kind, (float(px[j]) if ev[j] in (1, 2) else None), end, j
    jj = int(np.searchsorted(TT, hz_min - 1, side="right")) - 1
    if jj < 0:
        return None, None, None, None
    return "TIME_STOP", float(closeR[jj]), int(TT[jj]) + 1, jj


def walk_month(month):
    ser = load_symbol_series(month)
    log(stage="bars_loaded", month=month, symbols=len(ser),
        rows=int(sum(len(v["t"]) for v in ser.values())))
    geom = {}
    with gzip.open(LANE2 / f"geom_{month}.jsonl.gz", "rt") as fh:
        for line in fh:
            g = json.loads(line); geom[g["k"]] = g
    rows = pickle.load(gzip.open(CACHE % month, "rb"))
    log(stage="joined", month=month, cache=len(rows), geom=len(geom))

    recs, skips = [], {}
    def skip(why):
        skips[why] = skips.get(why, 0) + 1

    for row in rows:
        g = geom.get(row["candidate_occurrence_key"])
        if g is None:
            skip("no_geom"); continue
        sym = g["symbol"]; S = ser.get(sym)
        if S is None:
            skip("no_series"); continue
        d = 1 if str(g["side"]).upper() == "LONG" else -1
        entry = float(g["entry_price"]); stop = float(g["stop_loss"]); target = float(g["take_profit_1"])
        risk = abs(entry - stop)
        if not risk > 0:
            skip("zero_risk"); continue
        sub = at(g["decision_time_utc"]); exp = at(g["limit_first_expiry_utc"])
        sm, em = mins(sub), mins(exp)
        t = S["t"]
        i = int(np.searchsorted(t, sm, side="right")) - 1
        if i < 0 or t[i] != sm:
            skip("submission_bar_missing"); continue
        eoff = 0.0 if d > 0 else S["s"]
        aoff = S["s"] if d > 0 else 0.0
        n = len(t)
        ot = row["proposed_order_type"]
        # ---------------- fill ------------------------------------------------
        succ = i + 1
        if succ >= n or t[succ] != sm + 1:
            skip("no_contiguous_successor"); continue
        if ot == "MARKET":
            if t[succ] >= em:
                skip("market_expires_before_successor"); continue
            fi = succ; fp = S["o"][succ] + (aoff[succ] if d > 0 else 0.0); fill_at_open = True
        else:
            def ebar(j):
                a = aoff[j] if d > 0 else 0.0
                return (S["o"][j] + a, S["h"][j] + a, S["l"][j] + a, S["c"][j] + a)
            v0 = ebar(i)
            if (v0[2] <= entry) if d > 0 else (v0[1] >= entry):
                skip("CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_ORDERING"); continue
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
                skip(why); continue
        # invalid-gap guard (fill at open only)
        xo = S["o"][fi] + (eoff[fi] if d < 0 else 0.0)
        if fill_at_open and (d * (stop - fp) / risk >= 0 or d * (target - fp) / risk <= 0
                             or ((xo <= stop) if d > 0 else (xo >= stop))
                             or ((xo >= target) if d > 0 else (xo <= target))):
            skip("CENSORED_INVALID_GAP_THROUGH_SL_OR_TP"); continue

        # ---------------- R-space arrays over the extended window -------------
        maxend = min(n, fi + 1 + EXT_BARS)
        sl = slice(fi, maxend)
        off = eoff[sl] if d < 0 else 0.0
        O = S["o"][sl] + off; H = S["h"][sl] + off; L = S["l"][sl] + off; C = S["c"][sl] + off
        TT = t[sl]
        openR = d * (O - fp) / risk
        closeR = d * (C - fp) / risk
        favR = (d * (H - fp) / risk) if d > 0 else (d * (L - fp) / risk)
        advR = (d * (L - fp) / risk) if d > 0 else (d * (H - fp) / risk)
        stop_r = d * (stop - fp) / risk       # ~ -1, shifted by fill slippage
        tgt_r = d * (target - fp) / risk      # ~ +2, shifted by fill slippage
        gapj = np.nonzero(np.diff(TT) != 1)[0]
        first_gap = int(gapj[0]) + 1 if len(gapj) else len(TT)

        hz1 = em                               # sealed 1x horizon (absolute minute)
        hzE = sm + (em - sm) * EXT_MULT        # extended arm

        kind, gross, endm, je = resolve(openR, favR, advR, closeR, TT,
                                        stop_r, tgt_r, fill_at_open, hz1)
        if kind is None:
            skip("no_bar_before_horizon"); continue

        # ---- sealed-status reproduction (lane2_receipts/validate.py::sealed_1x) ----
        # The committed resolver walks bar-by-bar and censors the moment it needs a bar
        # past an M1 interval gap. Apply the identical post-hoc rule so the retained
        # population is exactly the sealed corpus's own filled rows.
        if em - sm <= 0:
            skip("CENSORED_GEOMETRY"); continue
        if int(TT[0]) + 1 > hz1:
            skip("fill_bar_incomplete_at_horizon"); continue
        fg = int(TT[first_gap - 1]) + 1 if first_gap < len(TT) else None
        reach = min(endm, hz1)
        if fg is not None and fg <= reach and fg <= hz1:
            if endm > fg or (kind == "TIME_STOP" and fg <= hz1):
                skip("CENSORED_SOURCE_INTERVAL_GAP"); continue
        if kind == "CENSOR":
            skip("CENSORED_ORDERING_AMBIGUITY"); continue
        walk_status = "RESOLVED_FILLED_" + kind
        if walk_status != row["lifecycle_label_status"]:
            skip("status_mismatch:%s->%s" % (row["lifecycle_label_status"], walk_status)); continue

        rec = dict(
            k=row["candidate_occurrence_key"], month=month, trading_day=g["trading_day"],
            symbol=sym, family=row["origin_family"], order_type=ot, side=g["side"],
            session=row.get("utc_session"), utc_hour=int(row.get("utc_hour") or 0),
            weekday=int(row.get("weekday") or 0),
            sealed_status=row["lifecycle_label_status"],
            sealed_net_r=(float(row["terminal_net_r"]) if row.get("terminal_net_r") not in (None, "", "None") else None),
            cost_r=float(row.get("deductible_cost_r") or 0.0),
            spread_r=float(row.get("spread_r") or 0.0),
            slippage_r=float(row.get("expected_slippage_r") or 0.0),
            swap_r=float(row.get("swap_cost_r") or 0.0),
            commission_r=float(row.get("commission_r") or 0.0),
            risk_price=float(risk), entry_price=entry, stop_price=stop, target_price=target,
            fill_price=float(fp), fill_at_open=bool(fill_at_open),
            sub_min=int(sm), fill_min=int(TT[0]), horizon_min=int(em),
            fill_delay_min=int(TT[0] - sm),
            stop_r=float(stop_r), target_r=float(tgt_r),
            entry_slip_r=float(d * (entry - fp) / risk),   # >0 = filled better than declared entry
            risk_over_atr=float(row.get("risk_over_atr") or np.nan),
            atr14_over_atr50=float(row.get("atr14_over_atr50") or np.nan),
            vol_8_over_48=float(row.get("close_to_close_vol_8_over_48") or np.nan),
            risk_frac_entry=float(row.get("risk_fraction_of_entry") or np.nan),
            exit_kind=kind, gross_r=(None if gross is None else float(gross)),
            exit_min=int(endm), hold_min=int(endm - TT[0]), exit_idx=int(je),
            gapped=bool(je >= first_gap),
            first_gap_min=(None if fg is None else int(fg)),
        )
        rec["net_r"] = None if gross is None else float(gross) - rec["cost_r"]

        # ---------------- excursion census -----------------------------------
        cf = np.maximum.accumulate(favR[:je + 1])
        ca = np.minimum.accumulate(advR[:je + 1])
        rec["mfe_r"] = float(cf[-1]); rec["mae_r"] = float(ca[-1])
        i_mfe = int(np.argmax(favR[:je + 1] >= cf[-1] - 1e-12))
        i_mae = int(np.argmax(advR[:je + 1] <= ca[-1] + 1e-12))
        rec["t_mfe_min"] = int(TT[i_mfe] - TT[0]); rec["t_mae_min"] = int(TT[i_mae] - TT[0])
        rec["mfe_bar_idx"] = i_mfe; rec["mae_bar_idx"] = i_mae
        rec["mae_before_mfe"] = bool(i_mae < i_mfe)
        if je > 0:
            rec["mfe_pre_exit_r"] = float(cf[je - 1]); rec["mae_pre_exit_r"] = float(ca[je - 1])
        else:
            rec["mfe_pre_exit_r"] = None; rec["mae_pre_exit_r"] = None
        # give-back: MFE surrendered by exit
        rec["giveback_r"] = None if gross is None else float(rec["mfe_r"] - gross)
        # winner fragility / loser proximity, in R of headroom above the stop
        rec["mae_headroom_r"] = float(rec["mae_r"] - stop_r)
        rec["mfe_headroom_r"] = float(tgt_r - rec["mfe_r"])
        # near-miss ladder (strictly before the exit bar = path-unambiguous)
        pre = rec["mfe_pre_exit_r"]
        for lv in LEVELS:
            tag = ("l%g" % lv).replace(".", "p")
            rec["reach_" + tag] = bool(rec["mfe_r"] >= lv)
            rec["reachpre_" + tag] = bool(pre is not None and pre >= lv)
        # path shape: R at deciles of the holding period
        for q in range(1, 11):
            idx = int(round(q / 10.0 * je))
            rec["p%d" % (q * 10)] = float(closeR[min(idx, je)])

        # ---- barrier-FREE excursion: a property of the price path, not the exit rule.
        # Needed because MFE conditioned on the shipped 2R/1R outcome is circular
        # (a TARGET trade has MFE >= 2 by construction).
        jfull = int(np.searchsorted(TT, hz1 - 1, side="right")) - 1
        jfull = max(jfull, 0)
        rec["mfe_full_r"] = float(favR[:jfull + 1].max())
        rec["mae_full_r"] = float(advR[:jfull + 1].min())
        rec["t_mfe_full_min"] = int(TT[int(np.argmax(favR[:jfull + 1]))] - TT[0])
        rec["t_mae_full_min"] = int(TT[int(np.argmin(advR[:jfull + 1]))] - TT[0])
        rec["close_full_r"] = float(closeR[jfull])   # barrier-free mark at the sealed horizon
        rec["full_gapped"] = bool(jfull >= first_gap)
        # The two quote-transform offsets, in R, so the barrier-free mark can be restated
        # on the RAW (untransformed) archive basis without re-walking. Direction and
        # spread are then separable by measurement rather than by inference.
        _ao = (aoff[fi] if d > 0 else 0.0)
        _eo = (eoff[jfull] if d < 0 else 0.0)
        rec["entry_off_r"] = float(_ao / risk)
        rec["exit_off_r"] = float(_eo / risk)
        rec["close_full_raw_r"] = float(closeR[jfull] + (_ao + _eo) / risk)
        for w in (5, 15, 30, 60):
            jw = int(np.searchsorted(TT, TT[0] + w, side="right")) - 1
            jw = max(jw, 0)
            rec["mfe%d_r" % w] = float(favR[:jw + 1].max())
            rec["mae%d_r" % w] = float(advR[:jw + 1].min())
        jE = int(np.searchsorted(TT, hzE - 1, side="right")) - 1
        jE = max(jE, 0)
        rec["mfe_ext_r"] = float(favR[:jE + 1].max())
        rec["mae_ext_r"] = float(advR[:jE + 1].min())
        rec["ext_bars"] = int(jE + 1)

        # ---------------- target ladder --------------------------------------
        for T in TARGETS:
            tag = ("t%g" % T).replace(".", "p")
            # target level T measured from the DECLARED entry, shifted to fill basis
            tr = T + d * (entry - fp) / risk
            k1, g1, e1, j1 = resolve(openR, favR, advR, closeR, TT, stop_r, tr, fill_at_open, hz1)
            rec[tag + "_kind"] = k1
            rec[tag + "_gross"] = None if g1 is None else float(g1)
            rec[tag + "_hold"] = None if e1 is None else int(e1 - TT[0])
            kE, gE, eE, jE = resolve(openR, favR, advR, closeR, TT, stop_r, tr, fill_at_open, hzE)
            rec[tag + "_kindE"] = kE
            rec[tag + "_grossE"] = None if gE is None else float(gE)
            rec[tag + "_holdE"] = None if eE is None else int(eE - TT[0])
        recs.append(rec)

    with gzip.open(OUT / f"f1walk_{month}.pkl.gz", "wb") as fh:
        pickle.dump(recs, fh, protocol=5)
    json.dump(skips, open(OUT / f"f1skips_{month}.json", "w"), indent=1, sort_keys=True)
    log(stage="month_done", month=month, recs=len(recs), skipped=int(sum(skips.values())))
    return len(recs)


if __name__ == "__main__":
    for m in sys.argv[1:] or ["feb", "apr", "may", "jun", "jul"]:
        walk_month(m)
    log(stage="ALL_DONE")
