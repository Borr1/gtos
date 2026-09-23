"""KB7_router_robustness.py — adversarial hardening of the confluence-Kelly router.

Three checks the router must survive before it justifies a book change:
  (A) VOL-MATCHED 1.5x STRESS verdict (the doctrine verdict). Even though the GROWTH
      mandate's primary verdict is matched-ruin speed (NOT vol-matched), the book-change
      doctrine says the verdict changes on the vol-matched challenge-pass + maxDD-fail MC.
      So we ALSO report it: vol-match the routed book to the flat book and check the 1.5x
      left-tail stress pass-rate is NOT degraded (KB6's router FAILED exactly here).
  (B) GATE-EDGE SENSITIVITY. The Kelly magnitudes (GATE_EDGE) are a-priori from the KBs,
      not fit — but are they load-bearing? Re-run the book matched-ruin speed under
      (i) the documented edges, (ii) a COARSE binary map (gate=2.0x base, anti=0.33x,
      base=1.0x — no per-cell tuning), (iii) a CONSERVATIVE map (all edges halved toward
      base). If the speed lift survives the coarse/conservative maps, it is the SIGN +
      direction doing the work, not fitted magnitudes.
  (C) SHUFFLED-GATE NULL. Randomly permute which trades get the high/low multiplier
      (preserving the multiplier DISTRIBUTION) 200x; the real gate assignment's book
      speed/Pareto lift must beat the shuffled null. If a random size tilt does as well,
      the gates carry no information and the lift is just leverage.
"""
from __future__ import annotations
import sys, json, statistics, collections, pickle, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3
import KB7_confluence_kelly_router as K7

mc_series = W2.mc_series
FWD_MIN = 2025
random.seed(71)


def book_series(conf_sleeve_daily, daily_sleeve, book_sleeves, cand, CLEAN3, all_days, conf_conf=0.45):
    comb = []
    for day in all_days:
        v = sum(daily_sleeve[sl].get(day, 0.0) for sl in book_sleeves)
        v += CLEAN3["vp_euidx_pocgrav"] * cand["vp_euidx_pocgrav"].get(day, 0.0)
        v += CLEAN3["sub_mid_dn_revert"] * cand["sub_mid_dn_revert"].get(day, 0.0)
        v += conf_conf * conf_sleeve_daily.get(day, 0.0)
        comb.append(v)
    return comb


def routed_daily(rows, mult_fn):
    num = collections.defaultdict(float); cnt = collections.defaultdict(int)
    for r in rows:
        num[r["date"]] += mult_fn(r) * r["R"]; cnt[r["date"]] += 1
    return {d: num[d] / cnt[d] for d in cnt}


def main():
    rows = pickle.load(open(HERE / "KB6_router_signals.pkl", "rb"))
    streams_w3 = pickle.load(open(HERE / "INTEG_W3_streams_cache.pkl", "rb"))
    days_w3, M_w3 = W3.W2.build_matrix(streams_w3)
    book_sleeves = W3.SLEEVES
    daily_sleeve = {sl: {} for sl in book_sleeves}
    for di, day in enumerate(days_w3):
        for si, sl in enumerate(book_sleeves):
            daily_sleeve[sl][day] = M_w3[di][si]
    new_streams = pickle.load(open(HERE / "INTEG_W5_new_streams_cache.pkl", "rb"))
    CLEAN3 = {"sub_xvol_pullback": 0.45, "vp_euidx_pocgrav": 0.30, "sub_mid_dn_revert": 0.20}

    def cand_daily(rws):
        by = collections.defaultdict(list)
        for r in rws:
            by[r["date"]].append(r["R"])
        return {d: sum(v) / len(v) for d, v in by.items()}
    cand = {nm: cand_daily(new_streams[nm]) for nm in CLEAN3}

    flat_d, rout_gross, _ = K7.per_day_streams(rows)
    all_days = sorted(set(days_w3) | set().union(*[set(cand[n]) for n in CLEAN3]) | set(rout_gross))
    fwd_mask = [d.year >= FWD_MIN for d in all_days]

    def fwd(series): return [v for v, f in zip(series, fwd_mask) if f]

    cf = book_series(flat_d, daily_sleeve, book_sleeves, cand, CLEAN3, all_days)
    cr = book_series(rout_gross, daily_sleeve, book_sleeves, cand, CLEAN3, all_days)
    cf_f, cr_f = fwd(cf), fwd(cr)

    report = {"track": "KB7_router_robustness"}

    # ---------- (A) VOL-MATCHED 1.5x STRESS verdict (the doctrine verdict) ----------
    print("=== (A) VOL-MATCHED 1.5x STRESS verdict (router vol-matched to flat) ===")
    sd_f = statistics.pstdev(cf_f); sd_r = statistics.pstdev(cr_f)
    vm = sd_f / sd_r if sd_r > 0 else 1.0
    def stress(v): return [(x * 1.5 if x < 0 else x) for x in v]
    report["volmatched_stress"] = dict(flat_std=round(sd_f, 4), router_std=round(sd_r, 4), router_volscale=round(vm, 4), rows={})
    print(f"  (flat std {sd_f:.4f}, router std {sd_r:.4f} -> router scaled x{vm:.3f} to match flat)")
    print(f"  {'risk':>7} {'FLAT pass':>10} {'ROUT pass(vm)':>14} | {'FLAT str1.5':>12} {'ROUT str1.5(vm)':>16}")
    for risk in (0.01, 0.015, 0.02):
        pf = mc_series(cf_f, risk, seed_base=1)["p_pass"]
        pr = mc_series(cr_f, risk * vm, seed_base=1)["p_pass"]
        sf = mc_series(stress(cf_f), risk, seed_base=999)["p_pass"]
        sr = mc_series(stress(cr_f), risk * vm, seed_base=999)["p_pass"]
        report["volmatched_stress"]["rows"][f"{risk*100:.2f}%"] = dict(flat_pass=pf, router_pass_vm=pr, flat_stress15=sf, router_stress15_vm=sr)
        print(f"  {risk*100:6.2f}% {pf:>10.2%} {pr:>14.2%} | {sf:>12.2%} {sr:>16.2%}")
    print("  READING: at MATCHED vol the router should be >= flat on BOTH pass and stress")
    print("           (unlike KB6's sizer, which dropped stress at matched vol).")

    # ---------- (B) GATE-EDGE SENSITIVITY ----------
    print("\n=== (B) GATE-EDGE SENSITIVITY (does the speed lift survive coarse/conservative maps?) ===")
    def mult_documented(r): return K7.router_mult(r)
    def make_coarse():
        def f(r):
            g, b = K7.active_gate(r)
            if g == "anti": return 0.40
            if g in ("veto", "liq", "stack"): return 2.0
            return 1.0
        return f
    def make_conservative():
        # halve every cell's edge TOWARD its base, then renormalize like K7
        def f(r):
            g, b = K7.active_gate(r)
            base = K7.BASE_EDGE.get(b, 0.55)
            if g == "anti":
                e = 0.5 * (K7.ANTI_EDGE + base)   # halfway base<-anti
            elif g in ("veto", "liq", "stack"):
                e = base + 0.5 * (K7.GATE_EDGE.get((b, g), base) - base)
            else:
                e = base
            return K7.kelly_f(e) / K7.F_ANCHOR
        return f
    maps = {"documented": mult_documented, "coarse_binary": make_coarse(), "conservative_half": make_conservative()}
    report["gate_edge_sensitivity"] = {}
    for nm, mf in maps.items():
        rd = routed_daily(rows, mf)
        cr_m = fwd(book_series(rd, daily_sleeve, book_sleeves, cand, CLEAN3, all_days))
        spds = {}
        for budget in (0.005, 0.01, 0.02):
            m = K7.matched_ruin_speed(cf_f, cr_m, ruin_budget=budget)
            spds[f"{budget*100:.1f}%"] = m.get("router") and m["router"].get("med_days")
            sl = None
            if m["flat"] and m["router"] and m["flat"]["med_days"] and m["router"]["med_days"]:
                sl = round(100 * (1 - m["router"]["med_days"] / m["flat"]["med_days"]), 1)
            spds[f"speed_{budget*100:.1f}%"] = sl
        report["gate_edge_sensitivity"][nm] = spds
        print(f"  {nm:18}: speed lift @0.5%/1%/2% ruin = "
              f"{spds.get('speed_0.5%')}% / {spds.get('speed_1.0%')}% / {spds.get('speed_2.0%')}%")

    # ---------- (C) SHUFFLED-GATE NULL ----------
    print("\n=== (C) SHUFFLED-GATE NULL (200 perms; real gate assignment vs random size tilt) ===")
    # observed multiplier list (preserve distribution), shuffle assignment to trades
    mults = [K7.router_mult(r) for r in rows]
    def shuffled_daily(perm_mults):
        num = collections.defaultdict(float); cnt = collections.defaultdict(int)
        for r, m in zip(rows, perm_mults):
            num[r["date"]] += m * r["R"]; cnt[r["date"]] += 1
        return {d: num[d] / cnt[d] for d in cnt}
    # metric = router-book P(pass) at 2% risk (the binding-ish growth point) on fwd
    def metric(series_fwd):
        return mc_series(series_fwd, 0.02, seed_base=55)["p_pass"]
    real_metric = metric(cr_f)
    rng = random.Random(7)
    null = []
    for _ in range(200):
        pm = mults[:]; rng.shuffle(pm)
        sd = shuffled_daily(pm)
        cm = fwd(book_series(sd, daily_sleeve, book_sleeves, cand, CLEAN3, all_days))
        null.append(metric(cm))
    flat_metric = metric(cf_f)
    ge = sum(1 for x in null if x >= real_metric)
    report["shuffled_gate_null"] = dict(
        metric="book P(pass)@2% risk fwd", flat=round(flat_metric, 4), real_router=round(real_metric, 4),
        null_mean=round(statistics.fmean(null), 4), null_p95=round(sorted(null)[int(0.95 * len(null))], 4),
        n_null_ge_real=ge, perm_p=round((ge + 1) / (len(null) + 1), 4))
    print(f"  flat book           P(pass)@2% = {flat_metric:.2%}")
    print(f"  REAL gate-routed    P(pass)@2% = {real_metric:.2%}")
    print(f"  shuffled-tilt null  mean {statistics.fmean(null):.2%}  p95 {sorted(null)[int(0.95*len(null))]:.2%}")
    print(f"  perm-p (P[null >= real]) = {report['shuffled_gate_null']['perm_p']}  "
          f"-> {'gates carry information' if report['shuffled_gate_null']['perm_p']<0.05 else 'NOT distinguishable from random tilt'}")

    (HERE / "KB7_ROUTER_ROBUSTNESS.json").write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote KB7_ROUTER_ROBUSTNESS.json")
    return report


if __name__ == "__main__":
    main()
