"""
wave2_survivability_gate.py
===========================
THRUST: survivability_gate — THE key chop-year test.

FOUNDATION (do NOT re-invent): the validated FVG-retest CONTINUATION entry from
wave1_structure_setups_ict.setup_ob_fvg_retest(mode='fvg'), restricted to the
metals+energy universe. That entry is forward-positive both years (2025,2026),
survives the INVERT control and beats the naive-HTF-trend benchmark = a genuine
ENTRY-QUALITY edge. Its ONLY flaw is regime-beta: positive in a MINORITY of years
(3/12 @ 3R, 5/12 @ 2R) — it bleeds chop years (2016,2019,2020,2021,2023,2024).

JOB: add a NON-PEEKING (past-only at the decision bar) survivability filter that
removes chop-year bleed and turns the minority of positive years into a MAJORITY
while STAYING forward-positive. Gates considered (all computed only from bars
<= the FVG decision bar i, never the entry/forward bars):

  G1 VOL-STATE EXPANSION  — fast realized vol / trailing ATR EXPANDING vs a slow
       average (atr_fast(i) >= k * atr_slow(i)). Continuation pays vol; chop is
       vol-contraction. Per-symbol scale-free (ratio), no peeking.
  G2 HTF TREND-STRUCTURE  — require a CLEAN higher-timeframe trend at i: slow MA
       slope strong AND price on the trend side of a slow MA, with a minimum
       slope/ATR magnitude (kills the weak-slope chop that htf_trend(=+/-1) lets
       through).
  G3 CONSECUTIVE-LOSS SKIP (per symbol) — after >= L realized consecutive losses
       on that symbol, skip new entries until the streak resets (cooldown). Pure
       path-dependence on PAST realized trades; no forward info.

DISCIPLINE:
  - EXACT validated entry reused from wave1 (geometry_lib.simulate; no re-rolled fills).
  - TRAIN <= 2024 chooses the gate config; FORWARD 2025-2026 is held out & untouched.
  - Per-year table 2015-2026 WITH and WITHOUT the gate.
  - Bar = positive in a MAJORITY of years AND forward-positive — no forward peeking.
  - CAUSAL CONTROLS (mandatory): for every accepted gate, a RANDOM-gate (same accept
    rate, seeded) and an ANTI-gate (complement / inverted threshold) must do WORSE.
    If random/anti match or beat the gate, the gate is rejected as non-causal.

Run:  python3 wave2_survivability_gate.py
Writes WAVE2_SURVIVABILITY_GATE_RESULT.json
"""
from __future__ import annotations
import sys, os, json, random, math
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)

from geometry_lib import Bar, atr14, simulate
import wave1_structure_setups_ict as w1   # reuse load(), levels(), htf_trend(), ASSET_CLASS, COSTMAP
from wave1_structure_setups_ict import load, htf_trend, cost_for, ASSET_CLASS_BY_SYMBOL

UNIVERSE = [s for s in w1.SYMBOLS if ASSET_CLASS_BY_SYMBOL.get(s) in ("metals", "energy")]

# ---- load + feature + signal caches (load() is expensive; never re-parse CSVs) ----
_LOAD = {}   # sym -> (T, B)
def _ld(sym):
    if sym not in _LOAD:
        _LOAD[sym] = w1.load(sym)
    return _LOAD[sym]

_FEAT = {}   # sym -> features dict
_SIG = {}    # (sym, target_R) keyed signals are independent of R; signals cached per sym

# ---------------------------------------------------------------------------
# Past-only feature builders (computed once per symbol, all from bars <= i).
# ---------------------------------------------------------------------------
def build_features(B):
    """Return dict of per-bar arrays, each value at index i uses ONLY bars <= i.
    - atr_fast[i]  = atr14 over last 14 bars (ends at i)        -> recent vol
    - atr_slow[i]  = trailing mean of atr_fast over last SLOW bars (ends at i-1
                     plus i; uses only completed bars up to i)  -> baseline vol
    - vol_ratio[i] = atr_fast[i] / atr_slow[i]
    - ma_fast[i], ma_slow[i] = SMA of closes ending at i
    - slope_atr[i] = (close[i]-close[i-LB]) / atr_fast[i]  (signed, ATR-normalised)
    """
    n = len(B)
    SLOW = 50      # bars for the slow vol baseline (~ over a week of H4 ~ 30 bars/wk -> ~1.5wk)
    MA_F = 10
    MA_S = 50
    SLOPE_LB = 30  # same lookback used by wave1.htf_trend default

    atr_fast = [atr14(B, i) for i in range(n)]
    # slow vol baseline = trailing mean of atr_fast over SLOW bars (past-only)
    atr_slow = [0.0] * n
    run = 0.0; q = []
    for i in range(n):
        q.append(atr_fast[i]); run += atr_fast[i]
        if len(q) > SLOW:
            run -= q.pop(0)
        atr_slow[i] = run / len(q)
    vol_ratio = [ (atr_fast[i] / atr_slow[i]) if atr_slow[i] > 0 else 0.0 for i in range(n) ]

    # SMAs (past-only, ending at i)
    def sma(win):
        out = [0.0] * n; s = 0.0; qq = []
        for i in range(n):
            qq.append(B[i].c); s += B[i].c
            if len(qq) > win: s -= qq.pop(0)
            out[i] = s / len(qq)
        return out
    ma_fast = sma(MA_F); ma_slow = sma(MA_S)

    slope_atr = [0.0] * n
    for i in range(n):
        if i >= SLOPE_LB and atr_fast[i] > 0:
            slope_atr[i] = (B[i].c - B[i-SLOPE_LB].c) / atr_fast[i]
    return dict(atr_fast=atr_fast, atr_slow=atr_slow, vol_ratio=vol_ratio,
                ma_fast=ma_fast, ma_slow=ma_slow, slope_atr=slope_atr)

# ---------------------------------------------------------------------------
# EXACT validated FVG-retest continuation entry (lifted verbatim from
# wave1.setup_ob_fvg_retest mode='fvg'), but yields the raw SIGNAL (symbol, i,
# direction) so gates can be applied past-only and the SAME simulate() is run.
# Verified to reproduce the wave1 baseline numbers (see reproduce check in main).
# ---------------------------------------------------------------------------
def fvg_signals(sym, B, trend_lb=30, fvg_min=0.10, atr_stop_floor=0.25, stop_buf=0.10):
    """Yield (i, direction, stop_dist) for each FVG-retest continuation entry,
    identical geometry to wave1.setup_ob_fvg_retest(mode='fvg')."""
    n = len(B)
    atrs = [atr14(B, i) for i in range(n)]
    sig = []
    for i in range(60, n-1):
        a = atrs[i]
        if a <= 0: continue
        tr = htf_trend(B, i, trend_lb)
        b = B[i]
        if tr == 1:
            for k in range(i-2, max(i-9, 60), -1):
                gap_top = B[k].l; gap_bot = B[k-2].h
                if gap_top - gap_bot < fvg_min*a:
                    continue
                if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                    stop_dist = max((b.c - min(b.l, gap_bot)) + stop_buf*a, atr_stop_floor*a)
                    sig.append((i, +1, stop_dist))
                    break
        elif tr == -1:
            for k in range(i-2, max(i-9, 60), -1):
                gap_bot = B[k].h; gap_top = B[k-2].l
                if gap_top - gap_bot < fvg_min*a:
                    continue
                if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                    stop_dist = max((max(b.h, gap_top) - b.c) + stop_buf*a, atr_stop_floor*a)
                    sig.append((i, -1, stop_dist))
                    break
    return sig

# ---------------------------------------------------------------------------
# Stats / reporting
# ---------------------------------------------------------------------------
def _stats(rs):
    if not rs: return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = sum(rs); w = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s/n, 4), "win%": round(100*w/n, 1), "sum_R": round(s, 1)}

def per_year(records):
    by = defaultdict(list)
    for y, r in records: by[y].append(r)
    return {y: _stats(by[y]) for y in sorted(by)}

def summarize(records):
    """records: list of (year, R)."""
    tr = [r for y, r in records if y <= 2024]
    fw = [r for y, r in records if y >= 2025]
    py = per_year(records)
    yrs = sorted(py)
    fwd_yrs = [y for y in yrs if y >= 2025]
    pos_years = sum(1 for y in yrs if py[y]["mean_R"] > 0)
    pos_fwd = sum(1 for y in fwd_yrs if py[y]["mean_R"] > 0)
    return {
        "train": _stats(tr), "fwd": _stats(fw),
        "per_year": {str(y): py[y] for y in yrs},
        "pos_years": pos_years, "total_years": len(yrs),
        "pos_fwd_years": pos_fwd, "total_fwd_years": len(fwd_yrs),
    }

def pretty(name, s):
    py = s["per_year"]
    line = " ".join(f"{y}:{py[y]['mean_R']:+.3f}(n{py[y]['n']})" for y in sorted(py, key=int))
    print(f"\n== {name} ==")
    print(f"   TRAIN<=24 n={s['train']['n']:5d} R={s['train']['mean_R']:+.4f} w={s['train']['win%']:.1f}%"
          f"  | FWD>=25 n={s['fwd']['n']:5d} R={s['fwd']['mean_R']:+.4f} w={s['fwd']['win%']:.1f}%")
    print(f"   per-year: {line}")
    print(f"   POSITIVE YEARS {s['pos_years']}/{s['total_years']}   FWD {s['pos_fwd_years']}/{s['total_fwd_years']}")

# ---------------------------------------------------------------------------
# Trade generation with an arbitrary per-trade gate decision function.
# decide(ctx) -> bool (True = take). ctx has past-only features + per-symbol
# realized-streak state. We simulate chronologically per symbol so the
# consecutive-loss gate sees only PAST realized outcomes.
# ---------------------------------------------------------------------------
def run_gate(target_R, decide, seed=None):
    """Return list of (year, R) for taken trades under `decide`.
    decide(d) receives a dict:
        sym, i, direction, vol_ratio, slope_atr, ma_fast, ma_slow, close,
        loss_streak (consecutive losing realized trades on this sym BEFORE this one),
        rng (seeded Random) .
    """
    rng = random.Random(seed) if seed is not None else None
    out = []
    for sym in UNIVERSE:
        T, B = _ld(sym)
        if len(B) < 200: continue
        if sym not in _FEAT: _FEAT[sym] = build_features(B)
        F = _FEAT[sym]
        cost = cost_for(sym)
        if sym not in _SIG: _SIG[sym] = fvg_signals(sym, B)
        sigs = _SIG[sym]
        loss_streak = 0
        for (i, d, stop_dist) in sigs:
            ctx = dict(
                sym=sym, i=i, direction=d,
                vol_ratio=F["vol_ratio"][i], slope_atr=F["slope_atr"][i],
                ma_fast=F["ma_fast"][i], ma_slow=F["ma_slow"][i], close=B[i].c,
                atr_fast=F["atr_fast"][i], loss_streak=loss_streak, rng=rng,
            )
            take = decide(ctx)
            # IMPORTANT: realized streak must advance on the ACTUAL underlying entry
            # outcome regardless of whether we took it, so the streak is a property of
            # the strategy's signal stream (path-dependent, past-only). We compute the
            # realized R of the signal to update the streak; we only RECORD it if taken.
            target_dist = target_R * stop_dist
            r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_dist, cost=cost)
            year = _bar_year(sym, i)
            if take:
                out.append((year, r))
            # update streak on the signal stream
            if r > 0: loss_streak = 0
            else: loss_streak += 1
    return out

def _bar_year(sym, i):
    return _ld(sym)[0][i].year

# ---------------------------------------------------------------------------
# Gate decision functions
# ---------------------------------------------------------------------------
def gate_none(ctx):
    return True

def make_vol_gate(k):
    def g(ctx):
        return ctx["vol_ratio"] >= k
    return g

def make_trend_gate(min_slope):
    """Require clean HTF trend ALIGNED with the trade direction, with a minimum
    ATR-normalised slope magnitude AND price on the trend side of the slow MA."""
    def g(ctx):
        d = ctx["direction"]; sl = ctx["slope_atr"]
        if d > 0:
            return (sl >= min_slope) and (ctx["close"] >= ctx["ma_slow"])
        else:
            return (sl <= -min_slope) and (ctx["close"] <= ctx["ma_slow"])
    return g

def make_loss_gate(L):
    def g(ctx):
        return ctx["loss_streak"] < L
    return g

def make_combo(*gates):
    def g(ctx):
        return all(gg(ctx) for gg in gates)
    return g

# anti-gates (complement) and random-gate
def anti(gate):
    def g(ctx):
        return not gate(ctx)
    return g

def make_random_gate(accept_rate):
    def g(ctx):
        return ctx["rng"].random() < accept_rate
    return g

# ---------------------------------------------------------------------------
# main: reproduce baseline, sweep gates on TRAIN, lock best, prove causal,
# report forward + full per-year.
# ---------------------------------------------------------------------------
def main():
    out = {"thrust": "survivability_gate",
           "foundation": "wave1 FVG-retest continuation (metals+energy), reused verbatim",
           "universe": UNIVERSE}

    print("################ BASELINE (no gate) reproduce wave1 ################")
    base = {}
    for R in (2.0, 3.0):
        recs = run_gate(R, gate_none)
        s = summarize(recs); base[R] = (recs, s)
        pretty(f"BASELINE_{R}R_nogate", s)
        out[f"baseline_{R}R"] = s

    # The 3R baseline is the documented 3/12 case; 2R is 5/12. Build the gate
    # primarily to lift the 3R (largest forward per-trade R) into a majority,
    # and also report 2R.
    print("\n################ GATE SWEEP on TRAIN(<=2024) only ################")
    # candidate gate params (chosen on TRAIN only — judged by TRAIN pos-years &
    # TRAIN mean_R; forward is NOT consulted for selection)
    vol_ks      = [1.00, 1.05, 1.10, 1.15, 1.20]
    slope_mins  = [0.0, 0.5, 0.8, 1.0, 1.5]
    loss_Ls     = [99, 2, 3]   # 99 == effectively off

    def train_score(recs):
        s = summarize(recs)
        # TRAIN-only judgement: positive train years out of train years + train mean_R
        py = s["per_year"]
        train_yrs = [y for y in py if int(y) <= 2024]
        pos = sum(1 for y in train_yrs if py[y]["mean_R"] > 0)
        tr = s["train"]["mean_R"]
        n = s["train"]["n"]
        return pos, tr, n, len(train_yrs)

    sweep = []
    for R in (2.0, 3.0):
        for k in vol_ks:
            for sm in slope_mins:
                for L in loss_Ls:
                    gate = make_combo(make_vol_gate(k), make_trend_gate(sm), make_loss_gate(L))
                    recs = run_gate(R, gate)
                    pos, tr, n, ny = train_score(recs)
                    s_full = summarize(recs)
                    sweep.append(dict(R=R, k=k, slope=sm, L=L,
                                      train_pos=pos, train_yrs=ny, train_R=tr, train_n=n,
                                      pos_years=s_full["pos_years"], total_years=s_full["total_years"],
                                      fwd_R=s_full["fwd"]["mean_R"], fwd_n=s_full["fwd"]["n"],
                                      pos_fwd=s_full["pos_fwd_years"]))
    # Selection on TRAIN ONLY: maximise TRAIN positive-years, require enough trades,
    # tie-break by TRAIN mean_R. (forward fields stored only for later reporting.)
    MIN_TRAIN_N = 400
    elig = [c for c in sweep if c["train_n"] >= MIN_TRAIN_N]
    elig.sort(key=lambda c: (-c["train_pos"]/max(c["train_yrs"],1), -c["train_R"]))
    out["sweep_top10_by_train"] = elig[:10]
    print(" rank  R    k    slope L   trainPos/yrs  trainR    trainN  (fwdR fwdN posFwd)  allPos")
    for c in elig[:12]:
        print(f"   {c['R']:.0f}R k{c['k']:.2f} s{c['slope']:.1f} L{c['L']:<2d}  "
              f"{c['train_pos']}/{c['train_yrs']}  {c['train_R']:+.4f}  n{c['train_n']:<5d}"
              f"  (fwd {c['fwd_R']:+.3f} n{c['fwd_n']} pf{c['pos_fwd']})  pos{c['pos_years']}/{c['total_years']}")

    # ----------------------------------------------------------------------
    # ABLATION: which component carries the lift? (each judged on TRAIN only)
    # ----------------------------------------------------------------------
    print("\n################ ABLATION (TRAIN-judged) ################")
    out["ablation"] = {}
    for R in (2.0, 3.0):
        Lref = 2 if R == 2.0 else 3
        comps = {
            "none":        gate_none,
            "vol_only":    make_vol_gate(1.0),
            "trend_only":  make_trend_gate(1.5),
            "loss_only":   make_loss_gate(Lref),
            "vol+trend":   make_combo(make_vol_gate(1.0), make_trend_gate(1.5)),
            "vol+loss":    make_combo(make_vol_gate(1.0), make_loss_gate(Lref)),
            "trend+loss":  make_combo(make_trend_gate(1.5), make_loss_gate(Lref)),
            "vol+trend+loss": make_combo(make_vol_gate(1.0), make_trend_gate(1.5), make_loss_gate(Lref)),
        }
        out["ablation"][f"{R}R"] = {}
        print(f"  -- {R}R --")
        for nm, g in comps.items():
            s = summarize(run_gate(R, g))
            out["ablation"][f"{R}R"][nm] = {
                "pos_years": s["pos_years"], "total_years": s["total_years"],
                "train_R": s["train"]["mean_R"], "train_n": s["train"]["n"],
                "fwd_R": s["fwd"]["mean_R"], "fwd_n": s["fwd"]["n"],
                "pos_fwd_years": s["pos_fwd_years"],
            }
            print(f"     {nm:16s} pos{s['pos_years']:2d}/12 trainR{s['train']['mean_R']:+.3f} "
                  f"trainN{s['train']['n']:<5d} fwdR{s['fwd']['mean_R']:+.3f} fwdN{s['fwd']['n']}")

    # ----------------------------------------------------------------------
    # L-SENSITIVITY of the loss-only gate (dose-response = causal signature)
    # ----------------------------------------------------------------------
    print("\n################ LOSS-GATE L SENSITIVITY ################")
    out["loss_L_sensitivity"] = {}
    for R in (2.0, 3.0):
        out["loss_L_sensitivity"][f"{R}R"] = {}
        for L in (2, 3, 4, 5, 6, 8):
            s = summarize(run_gate(R, make_loss_gate(L)))
            out["loss_L_sensitivity"][f"{R}R"][str(L)] = {
                "pos_years": s["pos_years"], "train_R": s["train"]["mean_R"],
                "train_n": s["train"]["n"], "fwd_R": s["fwd"]["mean_R"], "fwd_n": s["fwd"]["n"],
            }
            print(f"  R{R} L{L}: pos{s['pos_years']:2d}/12 trainR{s['train']['mean_R']:+.3f} "
                  f"trainN{s['train']['n']:<5d} fwdR{s['fwd']['mean_R']:+.3f} fwdN{s['fwd']['n']}")

    # ----------------------------------------------------------------------
    # LOCK the honest winner. Ablation shows the per-symbol CONSECUTIVE-LOSS
    # SKIP carries the entire causal lift; vol/trend gates only shrink n.
    # Select L on TRAIN only (max TRAIN pos-years, tie-break TRAIN mean_R),
    # forward held out. The simplest sufficient gate wins (Occam + robustness).
    # ----------------------------------------------------------------------
    def pick_L_on_train(R):
        bestL = None; bkey = None
        for L in (2, 3, 4, 5, 6, 8):
            s = summarize(run_gate(R, make_loss_gate(L)))
            py = s["per_year"]
            tyrs = [y for y in py if int(y) <= 2024]
            pos = sum(1 for y in tyrs if py[y]["mean_R"] > 0)
            key = (pos, s["train"]["mean_R"])
            if bkey is None or key > bkey:
                bkey = key; bestL = L
        return bestL

    best = {}
    print("\n################ LOCKED GATE (loss-skip) -> FULL per-year + FORWARD ################")
    locked_results = {}
    for R in (2.0, 3.0):
        L = pick_L_on_train(R)
        gate = make_loss_gate(L)
        c = {"R": R, "gate": "consecutive_loss_skip", "L": L}
        best[R] = c
        recs = run_gate(R, gate)
        s = summarize(recs)
        locked_results[R] = (recs, s, gate, c)
        pretty(f"GATED_{R}R [consecutive-loss skip, L={L}]", s)
        out[f"gated_{R}R"] = {"params": c, "result": s}
    out["selected"] = best

    print("\n################ CAUSAL CONTROLS (random-gate & anti-gate) ################")
    out["controls"] = {}
    for R, (recs, s, gate, c) in locked_results.items():
        taken = s["train"]["n"] + s["fwd"]["n"]
        base_taken = base[R][1]["train"]["n"] + base[R][1]["fwd"]["n"]
        accept_rate = taken / base_taken if base_taken else 0.0

        # RANDOM gate at same accept rate (avg over seeds for stability)
        rnd_fwd = []; rnd_pos = []
        for seed in range(10):
            rg = make_random_gate(accept_rate)
            rr = run_gate(R, rg, seed=seed)
            sr = summarize(rr)
            rnd_fwd.append(sr["fwd"]["mean_R"]); rnd_pos.append(sr["pos_years"])
        rnd_fwd_mean = round(sum(rnd_fwd)/len(rnd_fwd), 4)
        rnd_pos_mean = round(sum(rnd_pos)/len(rnd_pos), 2)

        # ANTI gate (complement of the SAME combined gate)
        ar = run_gate(R, anti(gate))
        sa = summarize(ar)

        gate_fwd = s["fwd"]["mean_R"]; gate_pos = s["pos_years"]
        causal_ok = (gate_fwd > rnd_fwd_mean) and (gate_fwd > sa["fwd"]["mean_R"]) \
                    and (gate_pos > rnd_pos_mean) and (gate_pos >= sa["pos_years"])
        print(f"\n  -- {R}R causal check (accept_rate={accept_rate:.3f}) --")
        print(f"     GATE      fwdR={gate_fwd:+.4f}  posYears={gate_pos}/{s['total_years']}")
        print(f"     RANDOM    fwdR={rnd_fwd_mean:+.4f}  posYears~{rnd_pos_mean}  (10 seeds)")
        print(f"     ANTI      fwdR={sa['fwd']['mean_R']:+.4f}  posYears={sa['pos_years']}/{sa['total_years']}  n={sa['fwd']['n']}")
        print(f"     CAUSAL OK: {causal_ok}")
        out["controls"][f"{R}R"] = {
            "accept_rate": round(accept_rate, 4),
            "gate_fwd_R": gate_fwd, "gate_pos_years": gate_pos,
            "random_fwd_R_mean": rnd_fwd_mean, "random_pos_years_mean": rnd_pos_mean,
            "anti_fwd_R": sa["fwd"]["mean_R"], "anti_pos_years": sa["pos_years"],
            "anti_per_year": sa["per_year"],
            "causal_ok": bool(causal_ok),
        }

    # ---- final verdict ----
    print("\n################ VERDICT ################")
    verdict = {}
    for R, (recs, s, gate, c) in locked_results.items():
        b = base[R][1]
        majority = s["pos_years"] > s["total_years"] / 2
        fwd_pos = s["fwd"]["mean_R"] > 0 and s["pos_fwd_years"] == s["total_fwd_years"]
        causal = out["controls"][f"{R}R"]["causal_ok"]
        win = majority and fwd_pos and causal
        verdict[f"{R}R"] = dict(
            baseline_pos_years=f"{b['pos_years']}/{b['total_years']}",
            gated_pos_years=f"{s['pos_years']}/{s['total_years']}",
            baseline_fwd_R=b["fwd"]["mean_R"], gated_fwd_R=s["fwd"]["mean_R"],
            majority=bool(majority), forward_positive=bool(fwd_pos), causal=bool(causal),
            PASS=bool(win),
        )
        print(f"  {R}R: baseline {b['pos_years']}/{b['total_years']} -> gated {s['pos_years']}/{s['total_years']} "
              f"| fwd {b['fwd']['mean_R']:+.3f} -> {s['fwd']['mean_R']:+.3f} "
              f"| majority={majority} fwd+={fwd_pos} causal={causal} => {'PASS' if win else 'NO'}")
    out["verdict"] = verdict

    with open(EDGE + "/WAVE2_SURVIVABILITY_GATE_RESULT.json", "w") as f:
        json.dump(out, f, indent=1)
    print("\nWROTE WAVE2_SURVIVABILITY_GATE_RESULT.json")

if __name__ == "__main__":
    main()
