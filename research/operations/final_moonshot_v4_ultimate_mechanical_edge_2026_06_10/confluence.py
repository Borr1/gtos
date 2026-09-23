"""confluence.py — CONFLUENCE SCORER LAYER (track: confluence)
===========================================================
A reusable engine that stacks INDEPENDENT condition-families into a confluence
score and quantifies how co-occurring conditions COMPOUND forward odds.

DOCTRINE (enforced here):
  - NO LOOKAHEAD: every condition is a pure function of CLOSED bars index<=i.
    Outcomes are labeled ONLY by geometry_lib.simulate (the leak-free pessimistic
    same-bar-stop labeler). R-unit = stop_dist; real per-asset cost via w1.cost_for.
  - NO AVERAGES AS VERDICTS: every cell reports TRAIN(<=2024) vs FORWARD(2025-26)
    odds + sample size n, plus per-YEAR. A cell is only trusted if it holds forward
    AND n>=N_MIN (default 40).
  - HIGH ODDS COME FROM CONFLUENCE: we measure pairwise correlation between the
    condition signals (independence check) and report the odds-LIFT each added
    condition contributes. Thin cells are never presented as edges.

ARCHITECTURE
  A "probe" is a base entry generator: it yields candidate (sym, i, direction,
  stop_dist, target_dist) at closed bar i. We reuse the audited FVG-retest probe
  (gold_sleeve.fvg_signals across the universe) and a sweep+reclaim probe. For each
  candidate we:
    1. evaluate every CONDITION (a directional boolean: does this family AGREE with
       the trade direction at bar i, using only data<=i),
    2. label the outcome with geometry_lib.simulate (win = R>0 net cost),
    3. record (year, asset_class, condition-vector, R).
  Then the analyzer:
    - measures pairwise phi-correlation of the condition booleans (independence),
    - measures each condition's marginal odds-lift (base-rate -> rate|cond),
    - sweeps confluence COUNT (k conditions agree) -> win-rate & mean-R, TRAIN vs FWD,
    - enumerates the TOP confluent cells (specific condition combos), n-gated, and
      reports the per-condition incremental lift inside the best stack.

This module is importable: build_dataset(...) returns the labeled candidate table;
CONDITIONS is the registry of independent families; analyze(...) produces the map.
"""
from __future__ import annotations
import sys, os, json, math, statistics, collections, argparse
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from geometry_lib import Bar, atr14, simulate
import wave1_structure_setups_ict as w1
import compounding_sleeve as cs   # cs.autocorr(B,i,60), cs.vol_ratio(atrs,i)
import gold_sleeve_strategy as g  # g.fvg_signals (vol-gated FVG-retest)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

N_MIN = 40            # sample-size gate for trusting a cell
TARGET_R = 2.0        # default fixed target for probes that need one
WIN = lambda r: r > 0.0

# ---------------------------------------------------------------------------
# Precomputed per-symbol feature context (all index<=i, no lookahead)
# ---------------------------------------------------------------------------
class SymCtx:
    """Holds bars + precomputed series used by conditions. Pure functions of bars."""
    __slots__ = ("sym","T","B","n","atrs","cost","cls","pdh","pdl","psh","psl","vol_sma")
    def __init__(self, sym):
        self.sym = sym
        self.T, self.B = w1.load(sym)
        self.n = len(self.B)
        self.atrs = [atr14(self.B, i) for i in range(self.n)]
        self.cost = w1.cost_for(sym)
        self.cls = ASSET_CLASS_BY_SYMBOL.get(sym) or "other"
        self.pdh, self.pdl, self.psh, self.psl = w1.levels(self.T, self.B)
        # rolling 100-bar volume SMA (for volume-location condition); 0 where no vol data
        vs = [0.0]*self.n
        run = 0.0
        for i in range(self.n):
            run += self.B[i].v
            if i >= 100: run -= self.B[i-100].v
            denom = min(i+1, 100)
            vs[i] = run/denom if denom else 0.0
        self.vol_sma = vs

# ---------------------------------------------------------------------------
# CONDITION FAMILIES — each: ctx,i,direction -> bool (AGREES with direction?)
# Each must be computable from data index<=i ONLY. They are designed to be as
# INDEPENDENT as possible; analyze() empirically checks the correlation.
# ---------------------------------------------------------------------------
def c_persistence(ctx, i, d):
    """Momentum persistence: 60-bar return autocorrelation positive (trending serial
    structure) -> continuation-favorable regardless of direction sign."""
    ac = cs.autocorr(ctx.B, i, 60)
    return ac is not None and ac >= 0.10

def c_vol_expansion(ctx, i, d):
    """Volatility regime: current ATR expanded vs its 100-bar mean (>=1.2x). Expansion
    favours follow-through / breakout setups."""
    return cs.vol_ratio(ctx.atrs, i) >= 1.2

def c_trend_align(ctx, i, d):
    """HTF trend (30-bar slope vs ATR) agrees with the trade direction."""
    tr = w1.htf_trend(ctx.B, i, 30)
    return (tr > 0 and d > 0) or (tr < 0 and d < 0)

def c_range_position(ctx, i, d):
    """Range position: for a LONG, price in the LOWER 40% of the trailing 50-bar range
    (room to run up / discount); for a SHORT, in the UPPER 40% (premium). Independent
    of trend — measures location, not momentum."""
    if i < 50: return False
    win = ctx.B[i-49:i+1]
    hi = max(b.h for b in win); lo = min(b.l for b in win)
    if hi <= lo: return False
    pos = (ctx.B[i].c - lo) / (hi - lo)   # 0=bottom 1=top
    if d > 0: return pos <= 0.40
    return pos >= 0.60

def c_struct_proximity(ctx, i, d):
    """Structural-level proximity: entry close is within 0.5*ATR of the relevant prior-day
    extreme in the trade's favour direction (long near prior-day LOW = support reclaim
    zone; short near prior-day HIGH = resistance). A discrete structural-magnet condition."""
    a = ctx.atrs[i]
    if a <= 0: return False
    c = ctx.B[i].c
    if d > 0:
        lvl = ctx.pdl[i]
        return lvl is not None and abs(c - lvl) <= 0.5*a
    lvl = ctx.pdh[i]
    return lvl is not None and abs(c - lvl) <= 0.5*a

def c_liquidity_sweep(ctx, i, d):
    """Liquidity-sweep+reclaim flag on bar i in the trade direction: for a LONG, the bar
    swept below the prior-day low and closed back above it (stops grabbed, reclaimed up);
    mirror for SHORT. A behavioral MM footprint, independent of trend/vol/persistence."""
    a = ctx.atrs[i]
    if a <= 0: return False
    b = ctx.B[i]
    if d > 0:
        lvl = ctx.pdl[i]
        return lvl is not None and b.l < lvl and b.c > lvl and (b.c - lvl) >= 0.05*a
    lvl = ctx.pdh[i]
    return lvl is not None and b.h > lvl and b.c < lvl and (lvl - b.c) >= 0.05*a

def c_volume_location(ctx, i, d):
    """Volume location: bar i traded with ABOVE-average volume (>=1.2x 100-bar mean) —
    participation/conviction. Only meaningful where volume data exists; returns False
    when the symbol carries no volume (so it simply never fires, never falsely lifts)."""
    vs = ctx.vol_sma[i]
    if vs <= 0: return False
    return ctx.B[i].v >= 1.2 * vs

CONDITIONS = [
    ("persistence",  c_persistence),
    ("vol_expand",   c_vol_expansion),
    ("trend_align",  c_trend_align),
    ("range_pos",    c_range_position),
    ("struct_prox",  c_struct_proximity),
    ("liq_sweep",    c_liquidity_sweep),
    ("vol_loc",      c_volume_location),
]
COND_NAMES = [c[0] for c in CONDITIONS]

# ---------------------------------------------------------------------------
# PROBES — base entry generators. Yield (ctx, i, d, stop_dist, target_dist).
# These define WHERE we look; conditions define HOW GOOD the spot is.
# ---------------------------------------------------------------------------
def probe_fvg(ctxs):
    """Audited vol-gated FVG-retest continuation across the WHOLE universe (not just
    metals). Reuses gold_sleeve.fvg_signals' geometry; we re-derive on ctx to avoid a
    second load. Target = 2R (fixed) so confluence, not the exit, drives odds."""
    for ctx in ctxs.values():
        B = ctx.B; atrs = ctx.atrs; n = ctx.n
        for i in range(60, n-1):
            a = atrs[i]
            if a <= 0 or i < 100: continue
            sma100 = sum(atrs[i-99:i+1]) / 100
            if sma100 <= 0 or a < g.GATE_K*sma100: continue
            tr = w1.htf_trend(B, i, 30); b = B[i]
            if tr == 1:
                for k in range(i-2, max(i-9, 60), -1):
                    gap_top = B[k].l; gap_bot = B[k-2].h
                    if gap_top - gap_bot < 0.10*a: continue
                    if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                        sd = max((b.c - min(b.l, gap_bot)) + g.STOP_BUF*a, g.ATR_STOP_FLOOR*a)
                        yield (ctx, i, +1, sd, TARGET_R*sd); break
            elif tr == -1:
                for k in range(i-2, max(i-9, 60), -1):
                    gap_bot = B[k].h; gap_top = B[k-2].l
                    if gap_top - gap_bot < 0.10*a: continue
                    if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                        sd = max((max(b.h, gap_top) - b.c) + g.STOP_BUF*a, g.ATR_STOP_FLOOR*a)
                        yield (ctx, i, -1, sd, TARGET_R*sd); break

def probe_sweep(ctxs):
    """Sweep+reclaim probe (prior-day): take the reclaim direction. Wide net so the
    confluence layer can show which co-conditions make it pay. Stop beyond the swept
    wick (+0.10 ATR, floor 0.20 ATR); target 2R fixed."""
    for ctx in ctxs.values():
        B = ctx.B; atrs = ctx.atrs; n = ctx.n
        for i in range(60, n-1):
            a = atrs[i]
            if a <= 0: continue
            b = B[i]; lo = ctx.pdl[i]; hi = ctx.pdh[i]
            if lo is not None and b.l < lo and b.c > lo and (b.c-lo) >= 0.05*a:
                sd = max((b.c - b.l) + 0.10*a, 0.20*a)
                yield (ctx, i, +1, sd, TARGET_R*sd)
            if hi is not None and b.h > hi and b.c < hi and (hi-b.c) >= 0.05*a:
                sd = max((b.h - b.c) + 0.10*a, 0.20*a)
                yield (ctx, i, -1, sd, TARGET_R*sd)

PROBES = {"fvg": probe_fvg, "sweep": probe_sweep}

# ---------------------------------------------------------------------------
# DATASET BUILD — label every candidate, record condition vector + outcome
# ---------------------------------------------------------------------------
def build_dataset(probe="fvg", symbols=None, classes=None):
    """Returns list of records: dict(sym, cls, year, d, R, win, conds=[bool,...]).
    Pure: conditions index<=i, outcome via simulate (leak-free)."""
    if symbols is None:
        symbols = w1.SYMBOLS
    if classes is not None:
        symbols = [s for s in symbols if (ASSET_CLASS_BY_SYMBOL.get(s) or "other") in classes]
    ctxs = {}
    for s in symbols:
        try:
            ctx = SymCtx(s)
        except Exception:
            continue
        if ctx.n >= 200:
            ctxs[s] = ctx
    gen = PROBES[probe](ctxs)
    out = []
    for (ctx, i, d, sd, td) in gen:
        r = simulate(ctx.B, i, d, stop_dist=sd, target_dist=td, cost=ctx.cost)
        conds = [fn(ctx, i, d) for _, fn in CONDITIONS]
        out.append(dict(sym=ctx.sym, cls=ctx.cls, year=ctx.T[i].year,
                        d=d, R=round(r, 5), win=WIN(r), conds=conds))
    return out

# ---------------------------------------------------------------------------
# ANALYSIS
# ---------------------------------------------------------------------------
def _split(recs):
    tr = [r for r in recs if r["year"] <= 2024]
    fw = [r for r in recs if r["year"] >= 2025]
    return tr, fw

def _odds(recs):
    n = len(recs)
    if n == 0: return dict(n=0, win=0.0, meanR=0.0)
    w = sum(1 for r in recs if r["win"]) / n
    m = sum(r["R"] for r in recs) / n
    return dict(n=n, win=round(100*w, 1), meanR=round(m, 4))

def _phi(a, b):
    """Phi (Matthews) correlation between two boolean lists — independence check."""
    n = len(a)
    if n == 0: return 0.0
    n11 = sum(1 for x, y in zip(a, b) if x and y)
    n10 = sum(1 for x, y in zip(a, b) if x and not y)
    n01 = sum(1 for x, y in zip(a, b) if (not x) and y)
    n00 = n - n11 - n10 - n01
    num = n11*n00 - n10*n01
    den = math.sqrt((n11+n10)*(n01+n00)*(n11+n01)*(n10+n00))
    return num/den if den > 0 else 0.0

def analyze(recs, n_min=N_MIN, top=12):
    """Full confluence map: independence corr, marginal lifts, count sweep, top combos."""
    res = {}
    base_tr, base_fw = _split(recs)
    res["base"] = dict(train=_odds(base_tr), fwd=_odds(base_fw), total_n=len(recs))
    cn = COND_NAMES; K = len(cn)

    # 1) independence: pairwise phi over the FULL candidate set
    cols = [[r["conds"][k] for r in recs] for k in range(K)]
    fire_rate = [round(100*sum(col)/len(col), 1) if col else 0.0 for col in cols]
    corr = {}
    for a in range(K):
        for b in range(a+1, K):
            corr[f"{cn[a]}~{cn[b]}"] = round(_phi(cols[a], cols[b]), 3)
    res["fire_rate_pct"] = dict(zip(cn, fire_rate))
    res["pairwise_phi"] = corr
    res["max_abs_phi"] = round(max((abs(v) for v in corr.values()), default=0.0), 3)

    # 2) marginal odds-lift per condition (base-rate -> rate when condition true), FWD too
    marg = {}
    for k in range(K):
        on = [r for r in recs if r["conds"][k]]
        on_tr, on_fw = _split(on)
        marg[cn[k]] = dict(
            train=_odds(on_tr), fwd=_odds(on_fw),
            train_lift=round(_odds(on_tr)["win"] - _odds(base_tr)["win"], 1),
            fwd_lift=round(_odds(on_fw)["win"] - _odds(base_fw)["win"], 1),
        )
    res["marginal"] = marg

    # 3) confluence COUNT sweep: k = number of conditions that agree
    cnt_sweep = {}
    for kk in range(0, K+1):
        sel = [r for r in recs if sum(r["conds"]) == kk]
        if not sel: continue
        st, sf = _split(sel)
        cnt_sweep[kk] = dict(train=_odds(st), fwd=_odds(sf))
    res["count_sweep_exact"] = cnt_sweep
    # cumulative >=k (the practical "require at least k confluences")
    cum = {}
    for kk in range(0, K+1):
        sel = [r for r in recs if sum(r["conds"]) >= kk]
        if not sel: continue
        st, sf = _split(sel)
        cum[kk] = dict(train=_odds(st), fwd=_odds(sf))
    res["count_sweep_atleast"] = cum

    # 4) TOP confluent COMBOS: enumerate all subsets of size 2..4, require the conditions
    #    in the combo to be TRUE; rank by FWD win-rate among n-gated, forward-holding cells.
    from itertools import combinations
    combos = []
    for size in (2, 3, 4):
        for combo in combinations(range(K), size):
            sel = [r for r in recs if all(r["conds"][k] for k in combo)]
            st, sf = _split(sel)
            ot, of = _odds(st), _odds(sf)
            # n-gate on BOTH sides; trust requires forward holding
            if of["n"] >= n_min and ot["n"] >= max(20, n_min//2):
                combos.append(dict(
                    conds=[cn[k] for k in combo],
                    train=ot, fwd=of,
                    fwd_minus_base=round(of["win"] - res["base"]["fwd"]["win"], 1),
                    holds_fwd=(of["win"] >= res["base"]["fwd"]["win"] and of["meanR"] > 0),
                ))
    combos.sort(key=lambda c: (-c["fwd"]["win"], -c["fwd"]["n"]))
    res["top_combos"] = combos[:top]

    # 5) for the single BEST forward-holding combo, per-year + per-class + incremental
    #    odds-lift of each condition added (ablation within the stack)
    best = next((c for c in combos if c["holds_fwd"] and c["fwd"]["win"] >= 60), None)
    if best is None and combos:
        best = combos[0]
    if best:
        cidx = [cn.index(x) for x in best["conds"]]
        sel = [r for r in recs if all(r["conds"][k] for k in cidx)]
        # per-year
        by = collections.defaultdict(list)
        for r in sel: by[r["year"]].append(r)
        best["per_year"] = {str(y): _odds(by[y]) for y in sorted(by)}
        # per-class forward
        byc = collections.defaultdict(list)
        for r in sel:
            if r["year"] >= 2025: byc[r["cls"]].append(r)
        best["per_class_fwd"] = {c: _odds(byc[c]) for c in sorted(byc)}
        # incremental lift: add conditions one at a time (in combo order), FWD win each step
        steps = []
        for j in range(1, len(cidx)+1):
            sub = cidx[:j]
            s = [r for r in recs if all(r["conds"][k] for k in sub)]
            _, sf = _split(s)
            o = _odds(sf)
            steps.append(dict(added=cn[cidx[j-1]], fwd_win=o["win"], fwd_n=o["n"],
                              fwd_meanR=o["meanR"]))
        best["incremental_fwd"] = steps
        res["best_stack"] = best
    return res

# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------
def run(probe="fvg", symbols=None, classes=None, n_min=N_MIN, top=12, label=None):
    recs = build_dataset(probe=probe, symbols=symbols, classes=classes)
    res = analyze(recs, n_min=n_min, top=top)
    res["probe"] = probe
    res["classes"] = classes
    res["label"] = label or probe
    return recs, res

def _print(res):
    b = res["base"]
    print(f"\n========== CONFLUENCE [{res['label']}] (probe={res['probe']}, classes={res['classes']}) ==========")
    print(f"  BASE  total_n={b['total_n']}  TRAIN n={b['train']['n']} win={b['train']['win']}% R={b['train']['meanR']:+.3f}"
          f"  | FWD n={b['fwd']['n']} win={b['fwd']['win']}% R={b['fwd']['meanR']:+.3f}")
    print(f"  condition fire-rate %: " + "  ".join(f"{k}={v}" for k,v in res['fire_rate_pct'].items()))
    print(f"  INDEPENDENCE max|phi|={res['max_abs_phi']}  (pairs |phi|>=0.3):")
    for k,v in sorted(res['pairwise_phi'].items(), key=lambda x:-abs(x[1])):
        if abs(v) >= 0.3: print(f"      {k}: phi={v:+.3f}")
    print("  MARGINAL odds-lift (win% when condition TRUE, vs base):")
    for k,m in res['marginal'].items():
        print(f"      {k:12s} TRAIN n={m['train']['n']:5d} win={m['train']['win']:5.1f}% (lift{m['train_lift']:+.1f}) "
              f"| FWD n={m['fwd']['n']:5d} win={m['fwd']['win']:5.1f}% (lift{m['fwd_lift']:+.1f})")
    print("  CONFLUENCE COUNT (>=k conditions agree):")
    for kk,o in sorted(res['count_sweep_atleast'].items()):
        print(f"      >={kk}: TRAIN n={o['train']['n']:5d} win={o['train']['win']:5.1f}% R={o['train']['meanR']:+.3f} "
              f"| FWD n={o['fwd']['n']:5d} win={o['fwd']['win']:5.1f}% R={o['fwd']['meanR']:+.3f}")
    print(f"  TOP CONFLUENT COMBOS (n_fwd>=gate, ranked by FWD win%):")
    for c in res['top_combos'][:10]:
        flag = "HOLDS" if c['holds_fwd'] else "     "
        print(f"      {flag} {'+'.join(c['conds']):42s} TRAIN n={c['train']['n']:4d} {c['train']['win']:5.1f}% "
              f"| FWD n={c['fwd']['n']:4d} {c['fwd']['win']:5.1f}% R={c['fwd']['meanR']:+.3f} (vs base{c['fwd_minus_base']:+.1f})")
    if res.get("best_stack"):
        bs = res["best_stack"]
        print(f"  >>> BEST STACK: {'+'.join(bs['conds'])}")
        print(f"      incremental FWD: " + " -> ".join(f"+{s['added']}={s['fwd_win']}%(n{s['fwd_n']})" for s in bs['incremental_fwd']))
        print(f"      per-year: " + " ".join(f"{y}:{o['win']}%(n{o['n']})" for y,o in bs['per_year'].items()))
        print(f"      per-class FWD: " + " ".join(f"{c}:{o['win']}%(n{o['n']})" for c,o in bs['per_class_fwd'].items()))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", default="both", choices=["fvg","sweep","both"])
    ap.add_argument("--nmin", type=int, default=N_MIN)
    ap.add_argument("--out", default=str(HERE/"KB4_CONFLUENCE_RESULT.json"))
    args = ap.parse_args()

    all_res = {}
    probes = ["fvg","sweep"] if args.probe=="both" else [args.probe]
    # class buckets to mine confluence within (independent + asset-class views)
    views = [
        ("ALL", None),
        ("metals", ["metals"]),
        ("energy", ["energy"]),
        ("fx_jpy", ["fx","jpy_fx"]),
        ("index", ["index"]),
        ("crypto", ["crypto"]),
    ]
    for probe in probes:
        for label, classes in views:
            try:
                _, res = run(probe=probe, classes=classes, n_min=args.nmin, label=f"{probe}:{label}")
            except Exception as e:
                print(f"  [skip {probe}:{label}] {e}")
                continue
            _print(res)
            all_res[f"{probe}:{label}"] = res
    with open(args.out, "w") as f:
        json.dump(all_res, f, indent=1)
    print(f"\nWROTE {args.out}")

if __name__ == "__main__":
    main()
