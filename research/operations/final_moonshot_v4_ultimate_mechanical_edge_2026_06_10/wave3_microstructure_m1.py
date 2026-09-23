"""WAVE 3 — MICROSTRUCTURE (M1) THRUST.

Question: do M1-derived microstructure / order-flow-proxy features, computed over
the JUST-CLOSED H4 bar and therefore KNOWN at the H4 close decision instant,
improve a simple H4 continuation entry FORWARD?

Hard anti-leak design (two prior subagent "wins" were leaks):
  * ALL fills go through the tested geometry_lib.simulate / simulate_detail.
  * NO LOOKAHEAD. An H4 bar labelled time T covers the M1 interval [T, T+4h).
    Its close is observed at T+4h. We DECIDE at the H4 close (bars[i].c), i.e.
    at wall-clock time T+4h. The M1 features that describe interval [T, T+4h)
    are therefore fully observable AT the decision instant — they describe the
    bar we are deciding ON, not any future bar. The continuation trade then runs
    over H4 bars i+1.. (simulate only ever looks at bars after i). No feature
    reads any M1 minute at or after T+4h.
  * NO path-dependent peeking: features here are pure functions of the closed
    H4 bar's own M1 minutes; no streak/drawdown state across trades is used.
  * TRAIN/FORWARD: M1 data only exists 2024-01..2026-06. We LOCK any threshold
    / sign choice on TRAIN = 2024 only, then read out FORWARD = 2025..2026.
    Per-year reported for every year we have (2024,2025,2026). H4 price history
    pre-2024 cannot carry M1 features, so it is irrelevant to this thrust.
  * Negative controls: invert the feature gate, randomise the gate (matched rate),
    and an anti-gate. A real edge must beat baseline AND beat random; the invert
    must move the opposite way.

Quote-only tick limit: gold ticks are bid/ask quotes with no traded volume.
M1 'volume' is MT5 tick-count (number of quote updates in the minute), NOT real
traded volume. We treat M1 volume strictly as a QUOTE-INTENSITY proxy and label
it as such; we never call it real order flow.
"""
from __future__ import annotations
import csv, os, sys, json, math, gzip, random
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
OP = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0, OP)
from geometry_lib import Bar, atr14, simulate, simulate_detail  # tested lib

DATA = ROOT + "/data/mt5_research_exports"
COST_MAP = json.load(open(OP + "/ULTIMATE_REAL_COST_MAP.json"))

ASSET_CLASS = {
    "XAUUSD":"metals","XAGUSD":"metals","BTCUSD":"crypto","ETHUSD":"crypto",
    "GER40":"index","JP225":"index","NAS100":"index","SPX500":"index",
    "UK100":"index","US30_cash":"index","UKOIL_cash":"energy","USOIL_cash":"energy",
    "AUDJPY":"jpy_fx","CHFJPY":"jpy_fx","EURJPY":"jpy_fx","GBPJPY":"jpy_fx",
    "USDJPY":"jpy_fx","AUDUSD":"fx","EURGBP":"fx","EURUSD":"fx","GBPUSD":"fx",
    "NZDUSD":"fx","USDCAD":"fx","USDCHF":"fx",
}
def cost_for(sym):
    return COST_MAP.get(ASSET_CLASS.get(sym), COST_MAP["_global_median"])

# Symbols that have real M1 (skip empty crypto stub months automatically by size).
M1_SYMBOLS = sorted(ASSET_CLASS.keys())

# ----------------------------------------------------------------------------
# Loaders
# ----------------------------------------------------------------------------
def _parse_dt(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

def load_h4(sym):
    """Return list of (dt, Bar) sorted, merged across both H4 archives."""
    out = {}
    for arch in ("bridge_ftmo_deep_h4_2015_2022", "bridge_ftmo_deep_h4_2022_2026"):
        p = f"{DATA}/{arch}/{sym}_H4.csv"
        if not os.path.exists(p): continue
        with open(p) as f:
            r = csv.reader(f); next(r, None)
            for row in r:
                if len(row) < 6: continue
                try:
                    dt = _parse_dt(row[0])
                    out[dt] = Bar(float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5]))
                except Exception:
                    continue
    items = sorted(out.items())
    return [d for d,_ in items], [b for _,b in items]

def load_m1_month(sym, ym):
    """Return list of (dt, o,h,l,c,vol) for one YYYYMM, or [] if stub/missing."""
    p = f"{DATA}/bridge_ftmo_m1_{ym}/{sym}_M1.csv"
    if not os.path.exists(p) or os.path.getsize(p) < 1000:
        return []
    out = []
    with open(p) as f:
        r = csv.reader(f); next(r, None)
        for row in r:
            if len(row) < 6: continue
            try:
                dt = _parse_dt(row[0])
                out.append((dt, float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5])))
            except Exception:
                continue
    return out

def months_2024_2026():
    out = []
    for y in (2024,2025,2026):
        for m in range(1,13):
            ym = f"{y}{m:02d}"
            if os.path.isdir(f"{DATA}/bridge_ftmo_m1_{ym}"):
                out.append(ym)
    return out

# ----------------------------------------------------------------------------
# M1 microstructure features per H4 bar.
# An H4 bar labelled T covers M1 minutes [T, T+4h). Features computed ONLY from
# those minutes -> known at the H4 close (= T+4h decision instant).
# ----------------------------------------------------------------------------
H4 = timedelta(hours=4)

def m1_features_for_h4(sym):
    """Map H4-bar-start-datetime -> dict of M1 microstructure features.
    Only H4 bars in 2024-01..2026-06 (where M1 exists) get features.
    """
    feats = {}
    # accumulate all M1 across months into a single time-sorted array once
    all_m1 = []
    for ym in months_2024_2026():
        all_m1.extend(load_m1_month(sym, ym))
    if not all_m1:
        return feats
    all_m1.sort(key=lambda x: x[0])
    # group M1 minutes into H4 buckets keyed by floor to 4h grid
    buckets = defaultdict(list)
    for rec in all_m1:
        dt = rec[0]
        h4_start = dt.replace(minute=0, second=0, microsecond=0,
                              hour=(dt.hour // 4) * 4)
        buckets[h4_start].append(rec)
    for h4_start, mins in buckets.items():
        mins.sort(key=lambda x: x[0])
        n = len(mins)
        if n < 8:   # too few minutes (illiquid/holiday) -> no reliable micro feature
            continue
        o = mins[0][1]; c = mins[-1][4]
        hi = max(m[2] for m in mins); lo = min(m[3] for m in mins)
        rng = hi - lo
        if rng <= 0:
            continue
        # --- intrabar momentum / persistence ---
        # net move as fraction of intrabar range, signed
        net = (c - o)
        net_over_range = net / rng                      # in [-1,1]
        # fraction of up minutes (close>open) — directional persistence proxy
        up = sum(1 for m in mins if m[4] > m[1])
        dn = sum(1 for m in mins if m[4] < m[1])
        up_frac = up / n
        persistence = (up - dn) / n                     # signed [-1,1]
        # path efficiency: |net| / sum(|minute moves|). high = trending intrabar
        gross = sum(abs(m[4]-m[1]) for m in mins) or 1e-12
        efficiency = abs(net) / gross
        # close location within intrabar range (0=at low,1=at high)
        close_loc = (c - lo) / rng
        # --- late-bar drift: last quarter of minutes net move / range, signed ---
        q = max(1, n // 4)
        late = mins[-q:]
        late_net = (late[-1][4] - late[0][1]) / rng
        early = mins[:q]
        early_net = (early[-1][4] - early[0][1]) / rng
        # --- quote-intensity proxy (M1 'volume' = tick-update count) ---
        vols = [m[5] for m in mins]
        tot_v = sum(vols)
        late_v = sum(m[5] for m in late)
        early_v = sum(m[5] for m in early)
        # late vs early quote-intensity ratio (acceleration of activity)
        vintensity_late = (late_v / (tot_v + 1e-12))    # share of activity late
        # max single-minute range as share of intrabar range (spike proxy)
        max_min_rng = max((m[2]-m[3]) for m in mins) / rng
        feats[h4_start] = {
            "net_over_range": net_over_range,
            "up_frac": up_frac,
            "persistence": persistence,
            "efficiency": efficiency,
            "close_loc": close_loc,
            "late_net": late_net,
            "early_net": early_net,
            "vintensity_late": vintensity_late,
            "max_min_rng": max_min_rng,
            "n_min": n,
        }
    return feats

# ----------------------------------------------------------------------------
# Base continuation strategy on H4.
# Decision at H4 close i: direction = sign of (close-open) of the just-closed
# bar (continuation). stop = 1.0*ATR14, target = 1.5*ATR14, maxbars 60.
# This is a deliberately SIMPLE H4 continuation entry (per the brief).
# ----------------------------------------------------------------------------
def build_signals(sym, dts, bars):
    """Yield candidate continuation signals: (i, dt, direction, stop_dist).
    Only where ATR is defined. No M1 needed here; M1 gate applied later.
    """
    out = []
    for i in range(15, len(bars)-1):
        a = atr14(bars, i)
        if a <= 0: continue
        b = bars[i]
        body = b.c - b.o
        if body == 0: continue
        direction = 1 if body > 0 else -1
        out.append((i, dts[i], direction, a))
    return out

def year_of(dt): return dt.year

def run_set(signals, bars, sym, gate_fn):
    """Run simulate over signals filtered by gate_fn(sig)->bool. Returns
    per-year dict year-> [list of R]. cost from class map."""
    cost = cost_for(sym)
    per_year = defaultdict(list)
    for sig in signals:
        if not gate_fn(sig): continue
        i, dt, direction, a = sig
        R = simulate(bars, i, direction, stop_dist=1.0*a, target_dist=1.5*a,
                     maxbars=60, cost=cost)
        per_year[year_of(dt)].append(R)
    return per_year

def stats(rs):
    n = len(rs)
    if n == 0: return (0,0.0,0.0,0.0)
    m = sum(rs)/n
    wins = sum(1 for r in rs if r > 0)
    sd = (sum((r-m)**2 for r in rs)/n)**0.5 if n>1 else 0.0
    return (n, m, wins/n, sd)

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    random.seed(20260614)
    report = {"thrust":"microstructure_m1","symbols":[], "feature_pool":[],
              "train_locked":{}, "results":{}, "negative_controls":{}, "notes":[]}

    # 1) Load all symbols, build H4 signals + attach M1 features.
    # We collect signals across ALL symbols into one pooled dataset (with each
    # signal carrying its symbol's features + cost). Features only exist 2024+,
    # so any signal before 2024 has no M1 feature and is excluded from the M1 test.
    POOL = []   # (sym, i, dt, direction, a, feat_dict)
    sym_bars = {}
    for sym in M1_SYMBOLS:
        dts, bars = load_h4(sym)
        if len(bars) < 50:
            continue
        sym_bars[sym] = (dts, bars)
        feats = m1_features_for_h4(sym)
        if not feats:
            continue
        report["symbols"].append(sym)
        sigs = build_signals(sym, dts, bars)
        for (i, dt, direction, a) in sigs:
            h4_start = dt   # H4 label == bar-start; features keyed by bar-start
            f = feats.get(h4_start)
            if f is None:
                continue   # no M1 coverage for this bar -> exclude from micro test
            POOL.append((sym, i, dt, direction, a, f))

    report["notes"].append(f"pooled M1-covered H4 continuation signals: {len(POOL)}")

    # Per-year baseline (all signals, no micro gate) — uses each sym's own bars.
    def baseline_run():
        per_year = defaultdict(list)
        for (sym, i, dt, direction, a, f) in POOL:
            cost = cost_for(sym)
            R = simulate(sym_bars[sym][1], i, direction, stop_dist=1.0*a,
                         target_dist=1.5*a, maxbars=60, cost=cost)
            per_year[dt.year].append(R)
        return per_year
    base_py = baseline_run()
    report["results"]["baseline_continuation"] = {
        str(y): dict(zip(("n","meanR","winrate","sd"), stats(base_py[y])))
        for y in sorted(base_py)}

    # 2) Candidate micro features to test as a CONTINUATION-CONFIRMING gate.
    # Hypothesis for a continuation entry: take the trade only when the just-closed
    # bar's M1 micro-structure CONFIRMS the H4 direction (trend persisted intrabar,
    # closed strongly in trade direction, late-bar drift agrees). We test each
    # feature as a directional-confirmation gate. Sign of feature is flipped by
    # trade direction so the gate means "intrabar agreed with the H4 move".
    FEATURES = ["net_over_range","persistence","efficiency","close_loc",
                "late_net","early_net","vintensity_late","max_min_rng","up_frac"]
    report["feature_pool"] = FEATURES

    def directional_value(f, feat, direction):
        """Return the feature value oriented so 'positive = confirms direction'.
        For symmetric features (efficiency, vintensity, max_min_rng, n) there is
        no natural sign; we use raw value. For signed/locational ones we flip by
        direction so high = intrabar agreed with the H4 close direction."""
        v = f[feat]
        if feat in ("net_over_range","persistence","late_net","early_net"):
            return v * direction
        if feat in ("close_loc","up_frac"):
            # close_loc 1=high,0=low; up_frac 1=all up. For a SHORT the confirming
            # version is (1-v). Map so positive=confirms direction.
            return (v - 0.5) * direction
        return v  # efficiency, vintensity_late, max_min_rng

    # TRAIN = 2024 only. We pick, per feature, a threshold quantile that LOCKS on
    # 2024 (top-half confirmation). Then read out forward.
    train = [s for s in POOL if s[2].year == 2024]
    report["train_locked"]["train_n"] = len(train)

    feat_results = {}
    for feat in FEATURES:
        # training distribution of oriented value
        tvals = sorted(directional_value(f, feat, d) for (_,_,_,d,_,f) in train)
        if len(tvals) < 100:
            continue
        # lock the gate: take signals whose oriented value is in the TOP HALF
        # (i.e. >= train median). Threshold LOCKED on 2024 only.
        thr = tvals[len(tvals)//2]
        def gate(s, _thr=thr, _feat=feat):
            return directional_value(s[5], _feat, s[3]) >= _thr
        # run gated across all years (forward read-out 2025/2026)
        py = defaultdict(list)
        rate_py = defaultdict(lambda: [0,0])  # year -> [passed, total]
        for s in POOL:
            rate_py[s[2].year][1]+=1
            if gate(s):
                rate_py[s[2].year][0]+=1
                cost = cost_for(s[0])
                R = simulate(sym_bars[s[0]][1], s[1], s[3], stop_dist=1.0*s[4],
                             target_dist=1.5*s[4], maxbars=60, cost=cost)
                py[s[2].year].append(R)
        feat_results[feat] = {
            "threshold_2024_locked": thr,
            "per_year": {str(y): dict(zip(("n","meanR","winrate","sd"), stats(py[y])))
                          for y in sorted(py)},
            "pass_rate": {str(y): (rate_py[y][0]/rate_py[y][1] if rate_py[y][1] else 0)
                           for y in sorted(rate_py)},
        }
    report["results"]["gated_by_feature"] = feat_results

    # 3) Negative controls on the BEST forward feature.
    # "Best" chosen by FORWARD mean R lift vs baseline over 2025+2026 combined,
    # but we report ALL features so cherry-picking is transparent. We then run:
    #   (a) invert gate (bottom half) — should move OPPOSITE if feature is real
    #   (b) random gate matched to feature's overall pass rate — should be ~baseline
    #   (c) anti gate already = invert; plus a fully random direction sanity check.
    def fwd_mean(d):
        rs=[]
        for y in ("2025","2026"):
            yd = d["per_year"].get(y)
            if yd: rs.append((yd["meanR"], yd["n"]))
        if not rs: return -9, 0
        tot_n = sum(n for _,n in rs)
        if tot_n==0: return -9,0
        return sum(m*n for m,n in rs)/tot_n, tot_n
    base_fwd = []
    for y in (2025,2026):
        base_fwd += base_py[y]
    base_fwd_mean = sum(base_fwd)/len(base_fwd) if base_fwd else 0.0
    report["results"]["baseline_forward_meanR_2025_2026"] = base_fwd_mean
    report["results"]["baseline_forward_n_2025_2026"] = len(base_fwd)

    ranked = sorted(feat_results.items(), key=lambda kv: fwd_mean(kv[1])[0], reverse=True)
    report["results"]["forward_ranking"] = [
        {"feature":k, "fwd_meanR":round(fwd_mean(v)[0],4), "fwd_n":fwd_mean(v)[1],
         "lift_vs_base":round(fwd_mean(v)[0]-base_fwd_mean,4)} for k,v in ranked]

    if ranked:
        best_feat, best_d = ranked[0]
        thr = best_d["threshold_2024_locked"]
        # invert gate
        def inv_gate(s):
            return directional_value(s[5], best_feat, s[3]) < thr
        # overall pass rate of best gate (across all pooled) for random match
        passed = sum(1 for s in POOL if directional_value(s[5],best_feat,s[3])>=thr)
        rate = passed/len(POOL) if POOL else 0.0
        def rnd_gate(s):
            return random.random() < rate
        def run_gate(gfn):
            py=defaultdict(list)
            for s in POOL:
                if gfn(s):
                    cost=cost_for(s[0])
                    R=simulate(sym_bars[s[0]][1], s[1], s[3], stop_dist=1.0*s[4],
                               target_dist=1.5*s[4], maxbars=60, cost=cost)
                    py[s[2].year].append(R)
            return py
        inv_py = run_gate(inv_gate)
        rnd_py = run_gate(rnd_gate)
        report["negative_controls"]["best_feature"] = best_feat
        report["negative_controls"]["match_rate"] = rate
        report["negative_controls"]["invert_gate_per_year"] = {
            str(y): dict(zip(("n","meanR","winrate","sd"), stats(inv_py[y])))
            for y in sorted(inv_py)}
        report["negative_controls"]["random_gate_per_year"] = {
            str(y): dict(zip(("n","meanR","winrate","sd"), stats(rnd_py[y])))
            for y in sorted(rnd_py)}

    # 4) GOLD TICK micro dynamics (quote-only, 2025-10..2026-04).
    # We compute per-H4-bar spread + quote-intensity dynamics from raw ticks and
    # test a spread/quote gate on XAUUSD continuation forward. Quote-only -> we
    # ONLY use spread and update-count dynamics, never infer traded volume.
    report["results"]["gold_ticks"] = run_gold_ticks(sym_bars)

    out_path = OP + "/WAVE3_MICROSTRUCTURE_M1_RESULT.json"
    json.dump(report, open(out_path,"w"), indent=1, default=float)
    print("WROTE", out_path)
    print_summary(report)

def run_gold_ticks(sym_bars):
    """XAUUSD: per-H4-bar tick spread/quote-intensity features known at H4 close,
    gate on a simple continuation. Tiny sample (Oct25-Apr26) -> honest about it."""
    tp = (DATA + "/bridge_ftmo_ticks_micro_2025_2026/ticks/XAUUSD/"
          "microstructure_ticks.jsonl.gz")
    if not os.path.exists(tp) or "XAUUSD" not in sym_bars:
        return {"status":"no_tick_or_h4"}
    dts, bars = sym_bars["XAUUSD"]
    idx_by_dt = {d:i for i,d in enumerate(dts)}
    # bucket ticks into H4 windows [T, T+4h)
    bucket = defaultdict(lambda: {"spreads":[], "n":0, "first_ms":None,
                                   "last_ms":None, "mid_first":None,"mid_last":None,
                                   "early_n":0,"late_n":0})
    cnt=0
    with gzip.open(tp,"rt") as f:
        for line in f:
            try:
                d = json.loads(line)
                ts = d["ts_utc"]
                dt = datetime.fromisoformat(ts)
                bid=d["bid"]; ask=d["ask"]
            except Exception:
                continue
            if bid<=0 or ask<=0: continue
            h4 = dt.replace(minute=0, second=0, microsecond=0,
                            hour=(dt.hour//4)*4)
            b = bucket[h4]
            sp = ask-bid
            b["spreads"].append(sp); b["n"]+=1
            mid=(ask+bid)/2
            if b["mid_first"] is None: b["mid_first"]=mid; b["first_ms"]=d["time_msc"]
            b["mid_last"]=mid; b["last_ms"]=d["time_msc"]
            cnt+=1
    # convert buckets to features; split early/late by ms midpoint of the window
    feats={}
    for h4,b in bucket.items():
        if b["n"]<50: continue
        sps=b["spreads"]
        avg_sp=sum(sps)/len(sps)
        med_sp=sorted(sps)[len(sps)//2]
        # quote update intensity = ticks per minute over the window
        feats[h4]={"avg_spread":avg_sp,"med_spread":med_sp,"n_ticks":b["n"]}
    # build continuation signals on XAUUSD H4 over the tick window only
    res={"n_h4_buckets":len(feats),"tick_lines":cnt}
    sigs=[]
    for h4,f in feats.items():
        i=idx_by_dt.get(h4)
        if i is None or i<15 or i>=len(bars)-1: continue
        a=atr14(bars,i)
        if a<=0: continue
        body=bars[i].c-bars[i].o
        if body==0: continue
        direction=1 if body>0 else -1
        sigs.append((i,h4,direction,a,f))
    cost=cost_for("XAUUSD")
    if not sigs:
        res["status"]="no_signals_in_tick_window"; return res
    # baseline over tick window
    base=[simulate(bars,i,d,stop_dist=a,target_dist=1.5*a,maxbars=60,cost=cost)
          for (i,_,d,a,_) in sigs]
    res["baseline"]=dict(zip(("n","meanR","winrate","sd"),stats(base)))
    # gate: take continuation only when spread is in the LOW half (tight = clean)
    med_sps=sorted(s[4]["med_spread"] for s in sigs)
    thr=med_sps[len(med_sps)//2]
    tight=[simulate(bars,i,d,stop_dist=a,target_dist=1.5*a,maxbars=60,cost=cost)
           for (i,_,d,a,f) in sigs if f["med_spread"]<=thr]
    wide=[simulate(bars,i,d,stop_dist=a,target_dist=1.5*a,maxbars=60,cost=cost)
          for (i,_,d,a,f) in sigs if f["med_spread"]>thr]
    res["tight_spread_gate"]=dict(zip(("n","meanR","winrate","sd"),stats(tight)))
    res["wide_spread_gate"]=dict(zip(("n","meanR","winrate","sd"),stats(wide)))
    res["note"]=("quote-only ticks; spread+tick-count only, no traded volume; "
                 "sample = Oct2025..Apr2026 (in-FORWARD, tiny). Read as exploratory.")
    return res

def print_summary(rep):
    print("\n=== WAVE 3 MICROSTRUCTURE M1 — SUMMARY ===")
    print("symbols with M1:", len(rep["symbols"]))
    print("pooled signals note:", rep["notes"])
    print("\nBASELINE continuation per year:")
    for y,d in rep["results"]["baseline_continuation"].items():
        print(f"  {y}: n={d['n']:5d} meanR={d['meanR']:+.4f} wr={d['winrate']:.3f}")
    print(f"\nbaseline FORWARD(25-26) meanR={rep['results']['baseline_forward_meanR_2025_2026']:+.4f} "
          f"n={rep['results']['baseline_forward_n_2025_2026']}")
    print("\nFORWARD ranking (feature gate, threshold locked on 2024):")
    for r in rep["results"]["forward_ranking"]:
        print(f"  {r['feature']:16s} fwd_meanR={r['fwd_meanR']:+.4f} "
              f"lift={r['lift_vs_base']:+.4f} n={r['fwd_n']}")
    nc=rep.get("negative_controls",{})
    if nc:
        print(f"\nNEG CONTROLS on best='{nc.get('best_feature')}' (match_rate={nc.get('match_rate'):.3f}):")
        print("  invert per year:", {y:round(d['meanR'],4) for y,d in nc.get("invert_gate_per_year",{}).items()})
        print("  random per year:", {y:round(d['meanR'],4) for y,d in nc.get("random_gate_per_year",{}).items()})
    g=rep["results"]["gold_ticks"]
    print("\nGOLD TICKS:", {k:v for k,v in g.items() if k in ("status","n_h4_buckets","tick_lines")})
    if "baseline" in g:
        print("  base:", {k:round(v,4) if isinstance(v,float) else v for k,v in g["baseline"].items()})
        print("  tight spread:", {k:round(v,4) if isinstance(v,float) else v for k,v in g["tight_spread_gate"].items()})
        print("  wide  spread:", {k:round(v,4) if isinstance(v,float) else v for k,v in g["wide_spread_gate"].items()})

if __name__ == "__main__":
    main()
