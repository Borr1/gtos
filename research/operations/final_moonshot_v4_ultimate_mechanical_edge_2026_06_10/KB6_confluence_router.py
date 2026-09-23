"""KB6_confluence_router.py — track KB6 GOAL 3: the CONFLUENCE-SCORE ROUTER.

A leak-free function that SIZES a candidate trade by the COUNT of agreeing,
positively-signed (per-class) orthogonal conditions present at the signal bar.
Signs are LEARNED on TRAIN(<=2024) only (per condition CLASS, dropping anti-confluent
ones per the W4/W5 lesson), then APPLIED unchanged to FORWARD(2025-26) — no forward
peeking. Validate the router lifts forward EV AND the vol-matched 1.5x stress
challenge-pass MC vs FLAT sizing, on the deploy book's confluence sleeve.

ROUTER DESIGN
  score(i) = sum over learned-positive conditions present at bar i of +1
           - sum over learned-negative (anti-confluent) conditions present of 1
  size(i)  = base_size * clamp(1 + GAIN*score, LO, HI)   (confidence sizing; deletes nothing)
The sign of each (dim=val) condition is learned from TRAIN forward-of-nothing rows:
sign = +1 if TRAIN meanR(cond) - TRAIN base meanR > +EPS, -1 if < -EPS, else 0 (ignored).
Crucially this is fit on TRAIN ONLY -> no lookahead into the forward verdict window.

The router operates on the PROVEN xvol-up-pullback long base (KB5 flagship, deep both
sides) plus whichever OTHER bases KB6 shows a positive veto/condition on, building a
single confluence sleeve. We compare, vol-matched:
  FLAT (size=base for every signal)  vs  ROUTER (size scaled by learned confluence score)
on forward EV, forward stress-pass, and the deploy-book joint stress-pass.
"""
from __future__ import annotations
import sys, json, math, collections, random, pickle, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

import substrate as sub
import wave1_structure_setups_ict as w1
import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL as AC

TRAIN_MAX = 2024
FWD_MIN = 2025
random.seed(17)

# router hyperparams (FIXED a-priori, not tuned on forward)
GAIN = 0.5         # size multiplier per net confluence point
LO, HI = 0.4, 2.0  # never delete (>=0.4x), cap upside (<=2.0x)
EPS = 0.15         # min |train lift| (R) to count a condition's sign as real
N_SIGN_MIN = 18    # min train rows for a per-class sign to be trusted

# conditions the router scores (leak-free categorical tags). We score the
# direction-relative / location atoms, NOT the base-defining substrate dims.
ROUTER_DIMS = ["ll_align", "vp_loc", "vp_poc_side", "hurst", "regime", "liq_align"]


def wins(r):
    return max(-1.3, min(5.0, r))


def load_router_signals():
    """Build the confluence sleeve's tagged signals = KB5 xvol family (per-class
    proven) + any KB6 other base that showed a positive orthogonal gate. We use the
    cached tagged signals (already leak-free) from both miners."""
    import KB5_cross_layer_miner as XL
    import KB6_veto_other_bases as K6
    # KB5 xvol bases (re-mine to get tagged rows; cheap relative to total)
    kb5 = XL.mine(verbose=False)
    kb6 = pickle.load(open(HERE / "KB6_other_base_signals.pkl", "rb"))
    return kb5, kb6, XL, K6


def learn_signs(rs, dims=ROUTER_DIMS):
    """Per condition CLASS (dim=val), learn its sign from TRAIN ONLY.
    sign = +1 / -1 / 0 (ignored). Returns {(dim,val): sign}."""
    tr = [r for r in rs if r["year"] <= TRAIN_MAX]
    if not tr:
        return {}
    base_mean = sum(r["R"] for r in tr) / len(tr)
    signs = {}
    by = collections.defaultdict(list)
    for r in tr:
        for d in dims:
            v = r["conds"].get(d)
            if v in (None, "na"):
                continue
            by[(d, v)].append(r["R"])
    for (d, v), Rs in by.items():
        if len(Rs) < N_SIGN_MIN:
            continue
        lift = sum(Rs) / len(Rs) - base_mean
        if lift > EPS:
            signs[(d, v)] = +1
        elif lift < -EPS:
            signs[(d, v)] = -1
    return signs


def score_row(r, signs, dims=ROUTER_DIMS):
    sc = 0
    for d in dims:
        v = r["conds"].get(d)
        if v in (None, "na"):
            continue
        sc += signs.get((d, v), 0)
    return sc


def router_size(score):
    return max(LO, min(HI, 1.0 + GAIN * score))


def build_streams(kb5, kb6, XL, K6):
    """Return per-day R streams (flat & router) for the confluence sleeve.
    Confluence sleeve = the flagship xvol-up-pullback long on the deploy 4-class
    universe (signs learned on TRAIN, applied fwd). Both flat and router share the
    SAME signal set; only the per-trade size differs. We also fold the broad
    xvol_up_conflict base rows under the same sign-map for breadth, and any KB6
    base whose veto/VP gate was forward-positive (decided after we see KB6 result)."""
    # use the flagship base rows (matches deploy sub_xvol_pullback universe)
    base = "xvol_up_pullback_L3R"
    rows_all = kb5[base]
    # restrict to deploy universe (drop crypto + jpy_fx as the deployed sleeve does)
    import KB5_fold_new_sleeves as FOLD
    rows = [r for r in rows_all if r["sym"] not in FOLD.DROP_XVOL]
    signs = learn_signs(rows)
    # materialize per-day streams
    flat_rows, router_rows = [], []
    for r in rows:
        sc = score_row(r, signs)
        sz = router_size(sc)
        d = r.get("date")
        # signals from XL.mine carry sym/year but not date; rebuild date via sym+i? -> XL stores year only.
        flat_rows.append(dict(sym=r["sym"], year=r["year"], R=wins(r["R"]), size=1.0, score=sc))
        router_rows.append(dict(sym=r["sym"], year=r["year"], R=wins(r["R"]), size=sz, score=sc))
    return rows, signs, flat_rows, router_rows


def ev_split(rows, sized=False):
    def agg(rs):
        if not rs:
            return (0, None)
        if sized:
            num = sum(x["R"] * x["size"] for x in rs)
            den = sum(x["size"] for x in rs)      # size-weighted mean R per unit risk
            return (len(rs), round(num / den, 4) if den else None)
        return (len(rs), round(sum(x["R"] for x in rs) / len(rs), 4))
    tr = [r for r in rows if r["year"] <= TRAIN_MAX]
    fw = [r for r in rows if r["year"] >= FWD_MIN]
    return agg(tr), agg(fw)


if __name__ == "__main__":
    print("KB6 confluence router — placeholder main (driven by KB6_router_validate.py)")
