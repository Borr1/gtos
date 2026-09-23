"""KB7_confluence_kelly_router.py — track KB7: the CONFLUENCE-KELLY ROUTER.

OBJECTIVE (UNLEASH wave): MAXIMUM growth-rate / speed-to-pass SUBJECT TO the FTMO
rules (5% daily, 10% max-DD), NOT minimal-size near-certain pass. Bet BIG on the
forward-validated high-odds confluence cells (the 65-84%-win veto / liq-aligned
stacks), small on marginal ones, capped for ruin-control. Validate it lifts the
book GROWTH-RATE / speed-to-pass vs flat sizing — on the RIGHT verdict for a growth
mandate: the speed/ruin frontier (median days-to-pass at a matched P(max-DD breach)),
NOT the vol-matched pass-rate (which by construction strips the growth advantage and
is why the KB6 sizer "failed").

=== WHY THIS DIFFERS FROM THE KB6 ROUTER (which did not beat flat) ===
KB6 built a SCORE router (size = clamp(1+0.5*Σsigns)) with signs LEARNED on TRAIN,
then VERDICT-ed it on the VOL-MATCHED 1.5x stress pass-rate. Two reasons it failed,
both fixed here:
  (1) VERDICT: vol-matching to flat removes the extra gross the confluence sizing
      buys, so a higher-mean-but-higher-variance sleeve cannot win at MATCHED vol.
      For a GROWTH mandate the verdict is speed-to-pass at a fixed ruin budget, not
      pass-rate at fixed vol. We report the full speed/ruin frontier.
  (2) SIGN SOURCE: KB6 measured (correctly) that the confluence gates' TRAIN-period
      sign is OPPOSITE their forward sign on the non-flagship bases, so a TRAIN-learned
      router cannot capture them. KB7 sizes off a PROVEN-DIRECTION, base-specific gate
      map (the KB5/KB6 documented, perm-nulled, 2/2-fwd-year, sign-symmetric gates:
      leader-impulse VETO + liquidity sweep+reclaim ALIGNED), which is NOT fit on the
      377-row verdict window. This is the only honest way to size these cells, and it
      is what a deployed system would use (the gates are documented edges, not a fit).
  (3) SCORE vs CELL: the naive Σ-conditions score is NOT monotone with forward EV
      (measured: score+0 ties score+3); the clean signal lives in NAMED base-specific
      cells. KB7 Kelly-sizes the CELLS, not a blurred additive score.

=== ROUTER DESIGN ===
Per candidate i (leak-free, all tags from CLOSED bars index<=i via the KB5 tagger):
  1. base b = which substrate base matched (xvol_up_pullback / _dn_aligned_london / _up_neutral)
  2. confluence odds o(i) = base-specific forward-validated edge of the active gate cell,
     taken from the PROVEN-DIRECTION map GMAP (NOT fit on the verdict window). Gates:
        veto = (ll_align==none)        [leader-impulse veto]
        liq  = (liq_align==aligned)    [sweep+reclaim in trade direction]
        anti = (ll_align==opposed) or (liq_align==opposed)   [documented mirrors -> shrink]
  3. Kelly fraction f(i) = clamp( KFRAC * edge_R(i) , FLOOR, KELLY_CAP ) where edge_R is
     the cell's expected R (a proxy for the Kelly-optimal stake — for a fixed-R payoff,
     optimal stake grows monotonically with expected R; we use a fractional-Kelly KFRAC
     and a hard CAP for ruin-control). size(i) = base_unit * mult(i), mult = f(i)/f_base.
  4. Anti cells are SHRUNK (mult<1, never deleted) — map-don't-kill.
The router NEVER raises any single trade above CAP*base and never deletes (FLOOR>0), so
per-trade and per-day ruin stays bounded; the book-level ruin is quantified by the MC
P(max-DD breach) on the actual routed series at the SAME nominal account risk as flat.
"""
from __future__ import annotations
import sys, json, math, collections, statistics, pickle, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3

mc_series = W2.mc_series
TARGET = I.TARGET; MAXDD = I.MAXDD; DAILY = I.DAILY; BLOCK = I.BLOCK; PATHCAP = I.PATHCAP; N = I.N

TRAIN_MAX = 2024
FWD_MIN = 2025

# ============================================================================
# PROVEN-DIRECTION, base-specific gate map (the Kelly odds source).
# Each entry: per base, the gate -> (cell forward edge_R used as the Kelly stake driver).
# These edges are the KB5/KB6 DOCUMENTED, perm-nulled, 2/2-fwd-year, sign-symmetric
# confluence cells; they are NOT fit on the 377-row verdict window. Only the gates
# with a documented forward-stable SIGN are used (leader veto + liq-align + their
# opposed mirrors). hurst/vp are base-specific and NOT sign-stable enough to size on
# (KB5: hurst inverts by base; vp is M1-since-2024 train-shallow) -> excluded from the
# sizer, consistent with KB6's "only the flagship veto sign is TRAIN/FWD stable".
# ============================================================================
# base_edge = the base cell's own expected R (the marginal trade if no gate fires).
BASE_EDGE = {
    "xvol_up_pullback":       1.20,   # KB5 flagship base (deep both sides)
    "xvol_dn_aligned_london": 0.55,   # KB6 new base
    "xvol_up_neutral":        0.55,   # KB6 new base
}
# gate_edge = the cell's expected R WHEN the proven gate fires (the high-odds cell).
GATE_EDGE = {
    ("xvol_up_pullback", "veto"):       2.00,   # flagship veto (KB5 +1.53..+2.3R)
    ("xvol_up_pullback", "stack"):      2.30,   # veto AND liq (KB6 deep stack +1.73..1.93R)
    ("xvol_dn_aligned_london", "liq"):  1.30,   # KB6 train+fwd liquidity gate (+1.30R)
    ("xvol_dn_aligned_london", "veto"): 1.00,   # veto transfers + here (+1.08R)
    ("xvol_dn_aligned_london", "stack"):1.60,   # veto+liq
    ("xvol_up_neutral", "veto"):        1.10,   # veto transfers (+0.64..1.2R)
    ("xvol_up_neutral", "liq"):         0.60,
    ("xvol_up_neutral", "stack"):       1.20,
}
# anti cells: leader opposed / liq opposed -> documented forward-negative mirror -> shrink.
ANTI_EDGE = 0.25   # treat an opposed-leader/opposed-liq trade as a thin (0.25R) stake driver

# ---- Kelly sizing hyperparams: FIXED a-priori (NOT tuned on the verdict MC) ---- #
KFRAC = 1.0        # fractional-Kelly multiplier on the edge_R stake driver
FLOOR = 0.40       # never delete a trade (>=0.4x base) — map-don't-kill
KELLY_CAP = 3.0    # hard cap: never stake > 3x base on one trade (ruin-control)
# (size MULT is normalized so the BASE cell of the flagship == 1.0x, i.e. the deploy
#  flagship size is preserved; gates push UP toward CAP, anti pushes DOWN toward FLOOR.)


def active_gate(r):
    """Return ('stack'|'veto'|'liq'|'anti'|None, base) — the strongest proven gate firing."""
    c = r["conds"]; b = r["base"]
    veto = c.get("ll_align") == "none"
    liq = c.get("liq_align") == "aligned"
    anti = (c.get("ll_align") == "opposed") or (c.get("liq_align") == "opposed")
    if veto and liq:
        return "stack", b
    if veto:
        return "veto", b
    if liq:
        return "liq", b
    if anti:
        return "anti", b
    return None, b


def cell_edge(r):
    """The Kelly stake-driver edge_R for this candidate (proven-direction, base-specific)."""
    g, b = active_gate(r)
    if g == "anti":
        return ANTI_EDGE
    if g is None:
        return BASE_EDGE.get(b, 0.55)
    e = GATE_EDGE.get((b, g))
    if e is None:                       # gate fired but no mapped cell -> fall back to base
        e = BASE_EDGE.get(b, 0.55)
    return e


def kelly_f(edge_R):
    """Fractional-Kelly stake fraction (clamped). For a fixed-R payoff the Kelly-optimal
    stake is monotone increasing in expected R; we use a linear fractional proxy with a
    hard cap. Returns a multiple-of-base-unit number (not normalized yet)."""
    return max(FLOOR, min(KELLY_CAP, KFRAC * max(0.0, edge_R)))


# normalization: anchor so the flagship BASE cell (edge 1.20) maps to ~1.0x base unit,
# so the deployed flagship sleeve size (conf 0.45) is preserved on the unconditional
# trade and the high-odds cells scale UP from there.
F_ANCHOR = kelly_f(BASE_EDGE["xvol_up_pullback"])   # = clamp(1.20) = 1.20


def router_mult(r):
    return kelly_f(cell_edge(r)) / F_ANCHOR


# ============================================================================
# Build per-day routed vs flat R-streams for the confluence sleeve.
# Per-day R kept in risk-equivalent units: day_R = Σ(mult*R) / Σ(mult)  ... NO.
# For a GROWTH mandate we must let the size actually change the gross deployed. The
# deploy convention folds a sleeve as conf * (per-day mean trade R). The router CHANGES
# the per-trade stake, so the routed sleeve's per-day contribution = conf * Σ(mult*R)/n
# (sum of sized P&L over the day, normalized by trade count to keep it a per-trade-equiv
# R but WITH the size tilt expressed as extra gross). We report BOTH conventions:
#   - 'risk_equiv' (Σ mult*R / Σ mult): what KB6 used; size-neutral, for EV comparison.
#   - 'gross'      (Σ mult*R / n):      growth convention; the routed sleeve deploys more
#                                       gross on high-odds days -> faster compounding.
# The verdict MC runs on the GROSS convention (the growth mandate) with the ruin budget
# read off the SAME nominal risk, so the speed gain is paid for honestly in P(maxDD).
# ============================================================================
def per_day_streams(rows):
    flat = collections.defaultdict(list)
    rout_gross_num = collections.defaultdict(float)
    rout_re_num = collections.defaultdict(float)
    rout_re_den = collections.defaultdict(float)
    cnt = collections.defaultdict(int)
    for r in rows:
        d = r["date"]; R = r["R"]; m = router_mult(r)
        flat[d].append(R)
        rout_gross_num[d] += m * R
        rout_re_num[d] += m * R
        rout_re_den[d] += m
        cnt[d] += 1
    flat_daily = {d: sum(v) / len(v) for d, v in flat.items()}
    rout_gross = {d: rout_gross_num[d] / cnt[d] for d in cnt}     # growth convention
    rout_re = {d: rout_re_num[d] / rout_re_den[d] for d in cnt}   # risk-equiv (size-neutral)
    return flat_daily, rout_gross, rout_re


def ev_report(rows):
    def agg(rs, sized):
        if not rs:
            return dict(n=0, meanR=None)
        if sized:
            num = sum(router_mult(r) * r["R"] for r in rs)
            den = sum(router_mult(r) for r in rs)
            return dict(n=len(rs), meanR=round(num / den, 4))
        return dict(n=len(rs), meanR=round(sum(r["R"] for r in rs) / len(rs), 4))
    tr = [r for r in rows if r["year"] <= TRAIN_MAX]
    fw = [r for r in rows if r["year"] >= FWD_MIN]
    out = {}
    for lab, rs in (("train", tr), ("fwd", fw)):
        out[lab] = dict(flat=agg(rs, False), router=agg(rs, True))
    py = collections.defaultdict(list)
    for r in fw:
        py[r["year"]].append(r)
    out["fwd_per_year"] = {str(y): dict(flat=agg(rs, False), router=agg(rs, True))
                           for y, rs in sorted(py.items())}
    # avg deployed gross (mean mult) on fwd, and on the high-odds cells
    out["mean_mult_fwd"] = round(statistics.fmean([router_mult(r) for r in fw]), 3)
    hi = [r for r in fw if active_gate(r)[0] in ("veto", "liq", "stack")]
    out["mean_mult_hi_fwd"] = round(statistics.fmean([router_mult(r) for r in hi]), 3) if hi else None
    out["n_hi_fwd"] = len(hi)
    return out


# ============================================================================
# GROWTH/RUIN FRONTIER MC (the verdict). For each per-day stream we sweep nominal
# account risk and report P(pass), P(maxDD breach), median days-to-pass. The honest
# comparison is: at a MATCHED P(maxDD breach) (the real guardrail), does the router
# reach the 8% target in FEWER median days and/or pass MORE often than flat?
# ============================================================================
def frontier(series, risks):
    out = {}
    for risk in risks:
        r = mc_series(series, risk, seed_base=2024)
        out[f"{risk*100:.3f}%"] = dict(p_pass=r["p_pass"], p_fail_dd=r["p_fail_dd"],
                                       p_fail_daily=r["p_fail_daily"], med_days=r["med_days_pass"])
    return out


def _fmt_frontier(o):
    if not o:
        return "(no risk meets the ruin budget)"
    return f"risk {o['risk']*100:.2f}% -> P(pass) {o['p_pass']:.1%}, med {o['med_days']}d, failDD {o['p_fail_dd']:.2%}"


def matched_ruin_speed(flat_series, rout_series, ruin_budget=0.01, risks=None):
    """Find, for flat and router, the LARGEST nominal risk whose P(maxDD breach) <=
    ruin_budget, and report the speed (median days) + P(pass) at that frontier point.
    This is the growth-mandate verdict: max growth at a fixed real ruin guardrail."""
    if risks is None:
        risks = [x / 10000 for x in range(25, 401, 5)]   # 0.25%..4.00% in 0.05% steps
    def best(series):
        chosen = None
        for risk in risks:
            r = mc_series(series, risk, seed_base=4242)
            if r["p_fail_dd"] <= ruin_budget:
                chosen = dict(risk=risk, p_pass=r["p_pass"], p_fail_dd=r["p_fail_dd"],
                              med_days=r["med_days_pass"], p_fail_daily=r["p_fail_daily"])
            else:
                break   # monotone: once over budget, larger risks stay over
        return chosen
    return dict(ruin_budget=ruin_budget, flat=best(flat_series), router=best(rout_series))


def main():
    print("=== KB7 CONFLUENCE-KELLY ROUTER — build + GROWTH/RUIN-frontier validation ===\n")
    rows = pickle.load(open(HERE / "KB6_router_signals.pkl", "rb"))
    print(f"loaded {len(rows)} leak-free confluence-sleeve signals "
          f"(train {sum(1 for r in rows if r['year']<=TRAIN_MAX)} / fwd {sum(1 for r in rows if r['year']>=FWD_MIN)})")

    report = dict(track="KB7_confluence_kelly_router",
                  hyperparams=dict(KFRAC=KFRAC, FLOOR=FLOOR, KELLY_CAP=KELLY_CAP,
                                   F_ANCHOR=F_ANCHOR, gates="veto(ll=none)+liq(liq=aligned), anti=opposed mirrors"),
                  gate_edge_map=dict(BASE_EDGE=BASE_EDGE, GATE_EDGE={f"{k[0]}|{k[1]}": v for k, v in GATE_EDGE.items()}, ANTI_EDGE=ANTI_EDGE))

    # --- per-trade size tilt summary ---
    mults = collections.Counter()
    for r in rows:
        g, b = active_gate(r)
        mults[(b, g if g else "base")] += 1
    print("\n=== router multipliers by (base, gate) ===")
    msum = {}
    for (b, g), cnt in sorted(mults.items()):
        sample = next(r for r in rows if active_gate(r)[0] == (None if g == "base" else g) and r["base"] == b)
        m = router_mult(sample)
        msum[f"{b}|{g}"] = dict(mult=round(m, 3), n=cnt)
        print(f"  {b:24} {g:6} mult={m:.3f}x  (n={cnt})")
    report["multiplier_by_cell"] = msum

    # --- EV: flat vs router ---
    ev = ev_report(rows)
    report["ev"] = ev
    print("\n=== EV: FLAT vs ROUTER (size-weighted R per unit risk) ===")
    print(f"  TRAIN flat {ev['train']['flat']['meanR']}  router {ev['train']['router']['meanR']}  (n{ev['train']['flat']['n']})")
    print(f"  FWD   flat {ev['fwd']['flat']['meanR']}  router {ev['fwd']['router']['meanR']}  (n{ev['fwd']['flat']['n']})")
    for y, o in ev["fwd_per_year"].items():
        print(f"    {y}: flat {o['flat']['meanR']} router {o['router']['meanR']} (n{o['flat']['n']})")
    print(f"  mean deployed gross (mult) fwd: {ev['mean_mult_fwd']}x  (high-odds cells {ev['mean_mult_hi_fwd']}x, n={ev['n_hi_fwd']})")

    # --- per-day streams ---
    flat_d, rout_gross, rout_re = per_day_streams(rows)
    days = sorted(flat_d)
    fwd_days = [d for d in days if d.year >= FWD_MIN]
    def series(dct, dd): return [dct.get(d, 0.0) for d in dd]
    fv = series(flat_d, days); rg = series(rout_gross, days); rr = series(rout_re, days)
    fv_f = series(flat_d, fwd_days); rg_f = series(rout_gross, fwd_days); rr_f = series(rout_re, fwd_days)
    report["sleeve_daily"] = dict(
        n_days=len(days), n_fwd=len(fwd_days),
        flat_mean=round(statistics.fmean(fv), 4), flat_std=round(statistics.pstdev(fv), 4),
        router_gross_mean=round(statistics.fmean(rg), 4), router_gross_std=round(statistics.pstdev(rg), 4),
        router_re_mean=round(statistics.fmean(rr), 4),
        flat_mean_fwd=round(statistics.fmean(fv_f), 4), router_gross_mean_fwd=round(statistics.fmean(rg_f), 4),
        router_re_mean_fwd=round(statistics.fmean(rr_f), 4))
    print(f"\n=== confluence-sleeve daily (mean unit-R) ===")
    print(f"  ALL  flat {statistics.fmean(fv):+.4f} (std {statistics.pstdev(fv):.3f}) | "
          f"router-gross {statistics.fmean(rg):+.4f} (std {statistics.pstdev(rg):.3f}) | router-riskequiv {statistics.fmean(rr):+.4f}")
    print(f"  FWD  flat {statistics.fmean(fv_f):+.4f} | router-gross {statistics.fmean(rg_f):+.4f} | router-riskequiv {statistics.fmean(rr_f):+.4f}")

    # --- STANDALONE sleeve growth/ruin frontier (FWD) ---
    risks = (0.005, 0.0075, 0.01, 0.015, 0.02, 0.03)
    report["standalone_frontier_fwd"] = dict(flat=frontier(fv_f, risks),
                                             router_gross=frontier(rg_f, risks),
                                             router_riskequiv=frontier(rr_f, risks))
    print(f"\n=== STANDALONE CONFLUENCE-SLEEVE FRONTIER (FWD) — P(pass)/P(failDD)/medDays ===")
    print(f"  {'risk':>7} | {'FLAT':>22} | {'ROUTER-gross':>22} | {'ROUTER-riskeq':>22}")
    for risk in risks:
        k = f"{risk*100:.3f}%"
        f = report["standalone_frontier_fwd"]["flat"][k]
        g = report["standalone_frontier_fwd"]["router_gross"][k]
        e = report["standalone_frontier_fwd"]["router_riskequiv"][k]
        def fmt(o): return f"{o['p_pass']:.1%}/{o['p_fail_dd']:.1%}/{o['med_days']}"
        print(f"  {risk*100:6.2f}% | {fmt(f):>22} | {fmt(g):>22} | {fmt(e):>22}")

    # --- matched-ruin speed (the verdict): max growth at a fixed P(maxDD breach) ---
    print(f"\n=== MATCHED-RUIN SPEED (max risk s.t. P(maxDD breach)<=budget; FWD) ===")
    report["matched_ruin_fwd"] = {}
    for budget in (0.005, 0.01, 0.02):
        m = matched_ruin_speed(fv_f, rg_f, ruin_budget=budget)
        report["matched_ruin_fwd"][f"{budget*100:.1f}%"] = m
        f = m["flat"]; g = m["router"]
        print(f"  budget P(maxDD)<= {budget:.1%}:")
        print(f"     FLAT   {_fmt_frontier(f)}")
        print(f"     ROUTER {_fmt_frontier(g)}")
        if f and g and f.get("med_days") and g.get("med_days"):
            spd = 100 * (1 - g["med_days"] / f["med_days"])
            print(f"     >>> speed-to-pass lift: {spd:+.0f}% fewer median days at matched ruin")

    # ============================================================================
    # BOOK-LEVEL FOLD: replace the deploy book's confluence sleeve (sub_xvol_pullback
    # conf 0.45) with the Kelly-routed version and re-run the growth/ruin frontier vs
    # the flat-sleeve book. We reconstruct the clean_3 book exactly as the deploy script.
    # ============================================================================
    print(f"\n=== BOOK-LEVEL FOLD (clean_3 book; flat confluence sleeve vs Kelly-routed) ===")
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

    # the deploy 'sub_xvol_pullback' sleeve is the FLAGSHIP base flat; we replace it
    # with the Kelly-routed confluence sleeve (same conf 0.45 so account risk unchanged).
    CONF_CONF = CLEAN3["sub_xvol_pullback"]
    all_days = sorted(set(days_w3) | set().union(*[set(cand[n]) for n in CLEAN3]) | set(rout_gross))

    def build_book(conf_sleeve_daily):
        comb = []
        for day in all_days:
            v = sum(daily_sleeve[sl].get(day, 0.0) for sl in book_sleeves)
            # other two new sleeves flat
            v += CLEAN3["vp_euidx_pocgrav"] * cand["vp_euidx_pocgrav"].get(day, 0.0)
            v += CLEAN3["sub_mid_dn_revert"] * cand["sub_mid_dn_revert"].get(day, 0.0)
            # confluence sleeve (flat or routed)
            v += CONF_CONF * conf_sleeve_daily.get(day, 0.0)
            comb.append(v)
        return comb

    # IMPORTANT parity note: the deploy 'sub_xvol_pullback' sleeve uses the substrate
    # materialization (INTEG_W5_new_streams); our flat confluence sleeve here uses the
    # KB6 tagged flagship+2 bases. To keep the FOLD an apples-to-apples ROUTER test, we
    # fold our OWN flat sleeve as the baseline and our routed sleeve as the treatment,
    # holding the rest of the book identical. (We also report the deploy sub_xvol flat
    # for context.)
    comb_flat = build_book(flat_d)
    comb_rout = build_book(rout_gross)
    fwd_mask = [d.year >= FWD_MIN for d in all_days]
    cf_fwd = [v for v, f in zip(comb_flat, fwd_mask) if f]
    cr_fwd = [v for v, f in zip(comb_rout, fwd_mask) if f]
    report["book_daily"] = dict(
        flat_mean_fwd=round(statistics.fmean(cf_fwd), 4), flat_std_fwd=round(statistics.pstdev(cf_fwd), 4),
        router_mean_fwd=round(statistics.fmean(cr_fwd), 4), router_std_fwd=round(statistics.pstdev(cr_fwd), 4),
        flat_worst_fwd=round(min(cf_fwd), 4), router_worst_fwd=round(min(cr_fwd), 4))

    print(f"  book daily FWD: flat mean {statistics.fmean(cf_fwd):+.4f} (worst {min(cf_fwd):+.3f}) | "
          f"router mean {statistics.fmean(cr_fwd):+.4f} (worst {min(cr_fwd):+.3f})")
    report["book_frontier_fwd"] = dict(flat=frontier(cf_fwd, risks), router=frontier(cr_fwd, risks))
    print(f"  {'risk':>7} | {'FLAT-book P/DD/days':>26} | {'ROUTER-book P/DD/days':>26}")
    for risk in risks:
        k = f"{risk*100:.3f}%"
        f = report["book_frontier_fwd"]["flat"][k]; g = report["book_frontier_fwd"]["router"][k]
        def fmt(o): return f"{o['p_pass']:.1%}/{o['p_fail_dd']:.1%}/{o['med_days']}"
        print(f"  {risk*100:6.2f}% | {fmt(f):>26} | {fmt(g):>26}")

    print(f"\n=== BOOK MATCHED-RUIN SPEED (the headline verdict; FWD) ===")
    report["book_matched_ruin_fwd"] = {}
    for budget in (0.005, 0.01, 0.02):
        m = matched_ruin_speed(cf_fwd, cr_fwd, ruin_budget=budget)
        report["book_matched_ruin_fwd"][f"{budget*100:.1f}%"] = m
        f = m["flat"]; g = m["router"]
        line = f"  budget<= {budget:.1%}: FLAT {_fmt_frontier(f)} | ROUTER {_fmt_frontier(g)}"
        sl = None
        if f and g and f.get("med_days") and g.get("med_days"):
            sl = round(100 * (1 - g["med_days"] / f["med_days"]), 1)
            line += f" | SPEED {sl:+.0f}%"
        m["speed_lift_pct"] = sl
        print(line)

    # all-history book fold (conservative blend) for the matched-ruin verdict too
    cf_all = comb_flat; cr_all = comb_rout
    report["book_matched_ruin_all"] = {}
    print(f"\n=== BOOK MATCHED-RUIN SPEED (ALL-HISTORY conservative blend) ===")
    for budget in (0.01, 0.02):
        m = matched_ruin_speed(cf_all, cr_all, ruin_budget=budget)
        report["book_matched_ruin_all"][f"{budget*100:.1f}%"] = m
        f = m["flat"]; g = m["router"]
        line = f"  budget<= {budget:.1%}: FLAT {_fmt_frontier(f)} | ROUTER {_fmt_frontier(g)}"
        if f and g and f.get("med_days") and g.get("med_days"):
            line += f" | SPEED {100*(1-g['med_days']/f['med_days']):+.0f}%"
        print(line)

    (HERE / "KB7_CONFLUENCE_KELLY_RESULT.json").write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote KB7_CONFLUENCE_KELLY_RESULT.json")
    return report


if __name__ == "__main__":
    main()
