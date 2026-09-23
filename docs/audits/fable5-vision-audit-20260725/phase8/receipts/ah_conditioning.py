"""Session AH items 3, 4 and 6 -- member conditioning on the 23 mixture families.

    python3 .../ah_conditioning.py all

AF routed 23 of 30 families `MEMBER_CONDITIONING_NOT_BREADTH`: dispersion ratio > 1, so the
members are a mixture and the question is which member carries the edge and why. This answers
it with five tests, and the FIRST one is the one that decides whether the other four matter.

C1  CARRIER STABILITY -- the decisive test, and it is deliberately hostile
    A mixture family has positive members. Selecting them is only a strategy if the SAME
    members are positive out of sample. Per family, the trade series is cut into five
    chronological folds and the carrier set (members with positive mean gross R) is measured
    in each. Two statistics:
      * `carrier_jaccard_adjacent` -- mean Jaccard overlap of the carrier set between
        consecutive folds. 1.0 = the same members carry it every time; ~k_pos/k = coin flips.
      * `sign_persistence` -- the fraction of members whose fold-1..4 sign equals their
        fold-5 sign, i.e. would picking on history have picked right.
    A family that fails C1 cannot be repaired by choosing members, and saying so is the point.

C2  THE PRE-DECLARED DIAL -- declared in `PRE_DECLARED` below, BEFORE any of this ran
    A mechanism should want a specific tape: a breakout wants persistence (which is what the
    armed `crypto` sleeve already gates on, `crypto.py:25`, AC_THR 0.15), a reversion wants
    the opposite. AF ran that gate at family level. This runs it at MEMBER level and asks the
    two-clause coherence question again inside the bucket: does the family cohere there?

C3  THE CRYPTO DONCHIAN SPLIT -- vintage, liquidity, or noise, as three falsifiable tests
C4  `mx_nzdjpy`'s DATED 2025 BREAK -- the post-hoc bucket tested per era, not promoted
C5  THE VOLUME-SURGE INDEX FAMILY -- does a dial explain folds 2-4 (AF §5.2)

Everything reads bars at or before each trade's own decision bar, through AF's own
`label_regimes`, so every conditioning rule here is one the live book could apply at decision
time. Nothing is a post-hoc filter on an outcome.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import math
import random
import statistics
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
AFDIR = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(AFDIR))

from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import load_broker_true_costs  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward import family as fam  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

import af_repairs as AFR  # noqa: E402  -- AF's DIALS, bucket(), label_regimes(), to_records()

TRADES = AFDIR / "AF_FAMILY_TRADES.json.gz"
QUEUE_AF = AFDIR / "REPAIR_QUEUE_AF.json"
OUT = HERE / "CONDITIONING_MAP_V1.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
SERVER = "FTMO-Server3"
N_FOLDS = 5

#: **DECLARED BEFORE ANY RESULT IN THIS FILE WAS COMPUTED.** One dial bucket per mechanism,
#: chosen from what the mechanism IS and from a production precedent where one exists -- never
#: from a table of outcomes. AF's own §8 item 2 is the cautionary case: its first revision
#: picked the best bucket under an `n >= 100` floor and thereby excluded
#: `PERSISTENCE == trend`, the bucket a breakout should want and the one `crypto.py:25`
#: already gates on, in favour of one six trades larger and 0.08 R worse.
PRE_DECLARED = {
    "donchian_20_breakout": ("PERSISTENCE", "trend",
                             "a breakout needs the move to continue; crypto.py:25 gates its "
                             "own donchian on autocorr(60) >= 0.15"),
    "crypto_h4_donchian_ac60": ("PERSISTENCE", "trend",
                                "same mechanism, and its production form ALREADY carries "
                                "this gate -- so the bucket is the sleeve's own contract"),
    "atr_mean_reversion": ("PERSISTENCE", "revert",
                           "mean reversion needs a mean-reverting tape; AB's `revert` band "
                           "(< -0.10) is the pre-declared home of it"),
    "volume_surge_reversal": ("PERSISTENCE", "revert",
                              "it is a reversal rule: it needs the exhaustion to revert, "
                              "not to trend"),
    "energy_fvg_retest": ("PERSISTENCE", "trend",
                          "a retest is a continuation entry -- the gap is expected to fill "
                          "and the move to resume"),
}


def load_all() -> tuple[dict, dict, dict]:
    with gzip.open(TRADES, "rt") as fh:
        art = json.load(fh)
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    series, _files = AFR.load_archive(res)
    regimes = AFR.label_regimes(art, series)
    return art, series, regimes


def members_of(art: dict) -> dict[str, list[str]]:
    """family -> its member names, from AF's own grid."""
    out = {}
    for f, info in art["grid"]["families"].items():
        key = f.split("_", 1)[1].rsplit("_", 2)[0]
        tf = {"D1": 16408, "H4": 16388}[info["timeframe"]]
        out[f] = [fam.member_name(key, s, tf) for s in info["symbols"]]
    return out


def reachable(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["engine_reachable"]]


def folds_of(rows: list[dict], n: int = N_FOLDS) -> list[list[dict]]:
    """Chronological equal-count folds on the pooled family series."""
    rs = sorted(rows, key=lambda r: r["entry_utc"])
    if not rs:
        return [[] for _ in range(n)]
    size = math.ceil(len(rs) / n)
    return [rs[i * size:(i + 1) * size] for i in range(n)]


def dispersion(means: dict[str, float]) -> tuple[float, int, int]:
    """AF's two-clause coherence test: sd/|mean| and the count of positive members."""
    vals = [v for v in means.values() if v is not None]
    if len(vals) < 2:
        return float("nan"), sum(1 for v in vals if v > 0), len(vals)
    m = statistics.mean(vals)
    sd = statistics.pstdev(vals)
    return (sd / abs(m) if m else float("inf"),
            sum(1 for v in vals if v > 0), len(vals))


# ------------------------------------------------------------------ C1

def carrier_stability(art: dict, fams: dict[str, list[str]]) -> dict:
    out = {}
    for f, mem in sorted(fams.items()):
        rows = {m: reachable(art["trades"].get(m, [])) for m in mem}
        allrows = [dict(r, _m=m) for m, rs in rows.items() for r in rs]
        fl = folds_of(allrows)
        per_fold = []
        for k, chunk in enumerate(fl):
            by = collections.defaultdict(list)
            for r in chunk:
                by[r["_m"]].append(r["r_gross"])
            means = {m: statistics.mean(v) for m, v in by.items() if len(v) >= 5}
            carriers = sorted(m for m, v in means.items() if v > 0)
            per_fold.append({"fold": k, "n_trades": len(chunk),
                             "n_members_scored": len(means),
                             "carriers": carriers,
                             "means": {m: round(v, 5) for m, v in sorted(means.items())}})
        jac = []
        for a, b in zip(per_fold, per_fold[1:]):
            sa, sb = set(a["carriers"]), set(b["carriers"])
            if sa or sb:
                jac.append(len(sa & sb) / len(sa | sb))
        # Would picking on folds 0-3 have picked right in fold 4?
        early = collections.defaultdict(list)
        for k in range(N_FOLDS - 1):
            for m, v in per_fold[k]["means"].items():
                early[m].append(v)
        last = per_fold[-1]["means"]
        agree = [1 if (statistics.mean(v) > 0) == (last[m] > 0) else 0
                 for m, v in early.items() if m in last]
        full = {m: statistics.mean([r["r_gross"] for r in rs]) for m, rs in rows.items() if rs}
        ratio, npos, k = dispersion(full)
        out[f] = {
            "k_members": k, "dispersion_ratio_full": round(ratio, 4) if ratio == ratio else None,
            "members_positive_full": npos,
            "carrier_jaccard_adjacent": round(statistics.mean(jac), 4) if jac else None,
            "carrier_jaccard_n_pairs": len(jac),
            "holdout_sign_agreement": round(statistics.mean(agree), 4) if agree else None,
            "holdout_n_members": len(agree),
            "chance_jaccard": round(_chance_jaccard(per_fold, k), 4),
            "member_means_full": {m: round(v, 5) for m, v in sorted(full.items())},
            "per_fold": per_fold,
        }
    return out


def _chance_jaccard(per_fold: list[dict], k: int) -> float:
    """What Jaccard would two INDEPENDENT draws of the same-sized carrier sets give?

    Without a baseline the overlap number is unreadable: a family where 8 of 9 members are
    positive every fold scores ~0.9 by arithmetic, not by stability.

    **CORRECTED after an adversarial pass on this session's own claim.** The first version drew
    both subsets from `k` = every member with at least one trade over the family's whole
    history, and used `E|A n B| / E|A u B|`. Two errors, both flattering:

    * a fold's carriers can only come from the members SCORED IN THAT FOLD (>= 5 trades there),
      and that universe grows 2 or 3 -> 9 across folds in six of the 23 mixtures because the
      instruments came online at different dates. Drawing from the lifetime universe makes
      chance overlap look smaller than it is;
    * `E|A n B| / E|A u B|` is not `E[|A n B| / |A u B|]`, worth another 0.01-0.05.

    Both are fixed here: the null draws A uniformly from fold i's scored set and B from fold
    i+1's, and the Jaccard is averaged over draws. The decisive case the skeptic found: a pair
    with a=3 drawn from a 4-member scored set and b=4 from a 4-member set has a TRUE chance
    Jaccard of exactly 0.75 -- every possible draw gives 3/4, i.e. literally zero information --
    where the old formula returned 0.235.
    """
    import itertools

    folds = [p for p in per_fold if p["n_members_scored"]]
    if len(folds) < 2:
        return float("nan")
    vals = []
    for a_f, b_f in zip(folds, folds[1:]):
        sa, sb = sorted(a_f["means"]), sorted(b_f["means"])
        na, nb = len(a_f["carriers"]), len(b_f["carriers"])
        if not sa or not sb or (na + nb) == 0:
            continue
        # Exact when the universes are small enough to enumerate, which they are here
        # (k <= 14, so at most C(14,7)^2 ~ 1.2e7 -- capped, with a seeded sample beyond).
        combos_a = list(itertools.combinations(sa, min(na, len(sa))))
        combos_b = list(itertools.combinations(sb, min(nb, len(sb))))
        pairs = len(combos_a) * len(combos_b)
        acc = []
        if pairs <= 200_000:
            for A in combos_a:
                setA = set(A)
                for B in combos_b:
                    u = setA | set(B)
                    acc.append(len(setA & set(B)) / len(u) if u else 0.0)
        else:
            rng = random.Random(20260730)
            for _ in range(20_000):
                setA = set(rng.choice(combos_a))
                setB = set(rng.choice(combos_b))
                u = setA | setB
                acc.append(len(setA & setB) / len(u) if u else 0.0)
        if acc:
            vals.append(statistics.mean(acc))
    return statistics.mean(vals) if vals else float("nan")


def carrier_holdout(art: dict, fams: dict[str, list[str]]) -> dict:
    """The only honest form of member selection: choose on history, score on what follows.

    Carriers are chosen on folds 0-3 (positive mean gross R there, >= 5 trades) and the
    resulting subset is scored on fold 4 ALONE. One look per family, the rule fixed before any
    fold-4 number was read, and the comparison is against the same fold-4 trades unselected --
    so the number is "what member selection would have bought", not "what the best members
    did". Every number here is GROSS R, never net of broker-true cost.
    """
    out = {}
    for f, mem in sorted(fams.items()):
        rows = {m: reachable(art["trades"].get(m, [])) for m in mem}
        allrows = [dict(r, _m=m) for m, rs in rows.items() for r in rs]
        fl = folds_of(allrows)
        early = collections.defaultdict(list)
        for k in range(N_FOLDS - 1):
            for r in fl[k]:
                early[r["_m"]].append(r["r_gross"])
        chosen = sorted(m for m, v in early.items()
                        if len(v) >= 5 and statistics.mean(v) > 0)
        held = fl[-1]
        sel = [r for r in held if r["_m"] in chosen]
        out[f] = {
            "carriers_chosen_on_folds_0_3": chosen,
            "n_chosen": len(chosen), "k_members": len(mem),
            "n_holdout_all": len(held), "n_holdout_selected": len(sel),
            "holdout_mean_all": round(statistics.mean(
                r["r_gross"] for r in held), 5) if held else None,
            "holdout_mean_selected": round(statistics.mean(
                r["r_gross"] for r in sel), 5) if sel else None,
            "selection_gain_r_gross": (
                round(statistics.mean(r["r_gross"] for r in sel)
                      - statistics.mean(r["r_gross"] for r in held), 5)
                if sel and held else None),
            "holdout_fold_mean_if_no_carrier_chosen": (
                round(statistics.mean(r["r_gross"] for r in held), 5)
                if held and not chosen else None),
        }
    # The per-family mean of `selection_gain_r_gross` is equal-weight and therefore hostage to
    # the thinnest holdout. An adversarial pass showed two families (20 and 32 selected trades)
    # carry it: dropping them moves the mean from -0.0355 to +0.0114. The trade-weighted
    # version is the one that cannot be moved that way, so it is published beside it.
    # Restricted to the MIXTURE families, because that is the population the claim is about.
    # Over all 30 the same statistic is smaller in magnitude, which would flatter the point.
    mix = _mixture_families()
    sel_all = [x for f in out if f in mix
               for x in _holdout_rows(art, fams, f, selected=True)]
    all_all = [x for f in out if f in mix
               for x in _holdout_rows(art, fams, f, selected=False)]
    out["_trade_weighted"] = {
        "scope": "the 23 MEMBER_CONDITIONING_NOT_BREADTH mixture families only",
        "units": "R GROSS per trade, never net of broker-true cost",
        "n_selected": len(sel_all), "n_all": len(all_all),
        "mean_selected": round(statistics.mean(sel_all), 6) if sel_all else None,
        "mean_all": round(statistics.mean(all_all), 6) if all_all else None,
        "gain": (round(statistics.mean(sel_all) - statistics.mean(all_all), 6)
                 if sel_all and all_all else None),
        "why": ("equal-weight-per-family and trade-weighted disagree by ~8x here; both are "
                "published because the equal-weight mean is the one a reader would quote and "
                "the trade-weighted one is the one that survives dropping the thin holdouts"),
    }
    return out


def _mixture_families() -> set[str]:
    return {r["sleeve"] for r in json.loads(QUEUE_AF.read_text())["rows"]
            if r["prescription"] == "MEMBER_CONDITIONING_NOT_BREADTH"}


def _holdout_rows(art: dict, fams: dict[str, list[str]], f: str, *,
                  selected: bool) -> list[float]:
    """Fold-4 gross R for one family, optionally restricted to the chosen carrier set."""
    if f.startswith("_"):
        return []
    mem = fams[f]
    rows = {m: reachable(art["trades"].get(m, [])) for m in mem}
    allrows = [dict(r, _m=m) for m, rs in rows.items() for r in rs]
    fl = folds_of(allrows)
    early = collections.defaultdict(list)
    for k in range(N_FOLDS - 1):
        for r in fl[k]:
            early[r["_m"]].append(r["r_gross"])
    chosen = {m for m, v in early.items() if len(v) >= 5 and statistics.mean(v) > 0}
    return [r["r_gross"] for r in fl[-1] if (not selected or r["_m"] in chosen)]


# ------------------------------------------------------------------ C2

def pre_declared_conditioning(art: dict, fams: dict[str, list[str]], regimes: dict) -> dict:
    out = {}
    for f, mem in sorted(fams.items()):
        key = f.split("_", 1)[1].rsplit("_", 2)[0]
        dial, want, why = PRE_DECLARED[key]
        gated_means, all_means, kept, total = {}, {}, 0, 0
        for m in mem:
            rs = reachable(art["trades"].get(m, []))
            reg = regimes.get(m, {})
            g = [r["r_gross"] for r in rs
                 if AFR.bucket(dial, reg.get(r["decision_bar_iso"], {}).get(dial)) == want]
            total += len(rs)
            kept += len(g)
            if rs:
                all_means[m] = statistics.mean(r["r_gross"] for r in rs)
            if len(g) >= 20:
                gated_means[m] = statistics.mean(g)
        r_all, p_all, k_all = dispersion(all_means)
        r_g, p_g, k_g = dispersion(gated_means)
        out[f] = {
            "dial": dial, "bucket": want, "basis": "pre_declared", "why": why,
            "n_trades_all": total, "n_trades_in_bucket": kept,
            "bucket_frac": round(kept / total, 4) if total else None,
            "ungated": {"dispersion_ratio": round(r_all, 4) if r_all == r_all else None,
                        "members_positive": p_all, "k_scored": k_all,
                        "mean_of_member_means": round(statistics.mean(all_means.values()), 5)
                        if all_means else None},
            "gated": {"dispersion_ratio": round(r_g, 4) if r_g == r_g else None,
                      "members_positive": p_g, "k_scored": k_g,
                      "mean_of_member_means": round(statistics.mean(gated_means.values()), 5)
                      if gated_means else None},
            "coheres_gated": bool(k_g >= 3 and r_g == r_g and r_g < 1.0 and p_g == k_g),
            "member_means_gated": {m: round(v, 5) for m, v in sorted(gated_means.items())},
        }
    return out


# ------------------------------------------------------------------ C3

def crypto_donchian_split(art: dict, series: dict, fams: dict) -> dict:
    """DASH/ETH/XTZ/BTC positive vs ADA/DOT/XRP/LTC negative -- vintage, liquidity or noise?

    Three falsifiable tests, and the third is the null the first two have to beat.
    """
    res = {}
    for f in ("fam_donchian_20_breakout_crypto_d1", "fam_crypto_h4_donchian_ac60_crypto_h4"):
        mem = fams[f]
        per = {}
        for m in mem:
            rs = reachable(art["trades"].get(m, []))
            if not rs:
                continue
            sym = rs[0]["symbol_canonical"]
            tf = rs[0]["timeframe"]
            bars, times = series[(sym, tf)]
            vols = [b.v for b in bars if b.v]
            per[m] = {
                "symbol": sym, "n_trades": len(rs),
                "mean_r_gross": statistics.mean(r["r_gross"] for r in rs),
                # vintage: how much history the instrument has at all
                "first_bar": times[0].isoformat(), "n_bars": len(bars),
                "history_years": round((times[-1] - times[0]).days / 365.25, 2),
                # liquidity proxy: median bar tick_volume, the only one the archive carries
                "median_tick_volume": statistics.median(vols) if vols else None,
                # own-history split-half: does the member's sign persist within itself?
                "first_half_mean": statistics.mean(
                    r["r_gross"] for r in sorted(rs, key=lambda r: r["entry_utc"])[:len(rs)//2]),
                "second_half_mean": statistics.mean(
                    r["r_gross"] for r in sorted(rs, key=lambda r: r["entry_utc"])[len(rs)//2:]),
            }
        for m, v in per.items():
            v["split_half_sign_agrees"] = bool(
                (v["first_half_mean"] > 0) == (v["second_half_mean"] > 0))
        xs_v = [(v["history_years"], v["mean_r_gross"]) for v in per.values()]
        xs_l = [(math.log(v["median_tick_volume"]), v["mean_r_gross"])
                for v in per.values() if v["median_tick_volume"]]
        # noise null: permute the member labels over the pooled trades and ask how often a
        # cross-member dispersion this large arises by chance.
        pooled = [(m, r["r_gross"]) for m in per for r in reachable(art["trades"][m])]
        obs_sd = statistics.pstdev([v["mean_r_gross"] for v in per.values()])
        rng = random.Random(20260730)
        counts = [m for m, _ in pooled]
        vals = [x for _, x in pooled]
        hits = 0
        trials = 2000
        for _ in range(trials):
            rng.shuffle(counts)
            by = collections.defaultdict(list)
            for m, x in zip(counts, vals):
                by[m].append(x)
            sd = statistics.pstdev([statistics.mean(v) for v in by.values()])
            hits += int(sd >= obs_sd)
        res[f] = {
            "per_member": per,
            "_means_by_symbol": {v["symbol"]: v["mean_r_gross"] for v in per.values()},
            "vintage": _corr(xs_v),
            "liquidity_log_tick_volume": _corr(xs_l),
            "noise_null": {"observed_cross_member_sd": round(obs_sd, 5),
                           "permutation_p": (hits + 1) / (trials + 1), "trials": trials,
                           "what": ("member labels shuffled over the pooled trades, so the "
                                    "null is 'one mechanism, k identical members'")},
            "split_half_agreement": round(statistics.mean(
                [1.0 if v["split_half_sign_agrees"] else 0.0 for v in per.values()]), 4),
        }
    # THE DECISIVE STATISTIC, and it is not one the brief asked for: if the SAME nine symbols
    # rank differently at D1 and H4, then "which member carries the edge" cannot have a
    # symbol-level answer -- not maturity, not liquidity, not anything about the instrument --
    # because the instrument is the same in both.
    a = res["fam_donchian_20_breakout_crypto_d1"]["_means_by_symbol"]
    b = res["fam_crypto_h4_donchian_ac60_crypto_h4"]["_means_by_symbol"]
    shared = sorted(set(a) & set(b))
    ra = {s: i for i, s in enumerate(sorted(shared, key=lambda s: a[s]))}
    rb = {s: i for i, s in enumerate(sorted(shared, key=lambda s: b[s]))}
    res["d1_vs_h4_member_ranking"] = {
        "shared_symbols": shared,
        "spearman_r": _corr([(ra[s], rb[s]) for s in shared])["r"],
        "pearson_r_on_means": _corr([(a[s], b[s]) for s in shared])["r"],
        "sign_agreement": round(statistics.mean(
            [1.0 if (a[s] > 0) == (b[s] > 0) else 0.0 for s in shared]), 4),
        "d1_means": {s: round(a[s], 4) for s in shared},
        "h4_means": {s: round(b[s], 4) for s in shared},
    }
    for f in ("fam_donchian_20_breakout_crypto_d1", "fam_crypto_h4_donchian_ac60_crypto_h4"):
        res[f].pop("_means_by_symbol", None)
    return res


def _corr(pairs: list[tuple[float, float]]) -> dict:
    if len(pairs) < 4:
        return {"n": len(pairs), "r": None}
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    r = num / den if den else None
    n = len(pairs)
    t = (r * math.sqrt(n - 2) / math.sqrt(1 - r * r)) if (r is not None and abs(r) < 1) else None
    return {"n": n, "r": round(r, 4) if r is not None else None,
            "t": round(t, 3) if t is not None else None}


# ------------------------------------------------------------------ C4

def nzdjpy_break_by_era(art: dict, regimes: dict) -> dict:
    """AF's post-hoc `VOL_REGIME == hi` bucket, tested per era instead of promoted.

    AF measured the break at 2025 (permutation p 0.0005), found the PRE-DECLARED
    `PERSISTENCE == trend` gate gives -0.1953 (p 0.9011), and offered `VOL_REGIME == hi`
    (+0.2684, p 0.1005, n=81) as a conditioning-map entry explicitly NOT as a claim. The only
    thing that can rescue a post-hoc bucket is out-of-sample behaviour, and the only
    out-of-sample axis available on one sleeve is time. So: the same bucket, era by era, with
    the era boundaries fixed in advance at five-year marks.
    """
    m = "mxf_donchian_20_breakout_nzdjpy_d1"
    rs = reachable(art["trades"].get(m, []))
    reg = regimes.get(m, {})
    eras = [(2000, 2005), (2005, 2010), (2010, 2015), (2015, 2020), (2020, 2025), (2025, 2027)]
    out = {"member": m, "n_trades": len(rs), "eras": [], "buckets": {}}
    for dial, want in (("VOL_REGIME", "hi"), ("PERSISTENCE", "trend")):
        rows = []
        for lo, hi in eras:
            sel = [r for r in rs if lo <= dt.datetime.fromisoformat(r["entry_utc"]).year < hi]
            g = [r["r_gross"] for r in sel
                 if AFR.bucket(dial, reg.get(r["decision_bar_iso"], {}).get(dial)) == want]
            rows.append({"era": f"{lo}-{hi - 1}", "n_all": len(sel), "n_bucket": len(g),
                         "mean_all": round(statistics.mean(
                             [r["r_gross"] for r in sel]), 5) if sel else None,
                         "mean_bucket": round(statistics.mean(g), 5) if g else None})
        signed = [r for r in rows if r["mean_bucket"] is not None]
        out["buckets"][f"{dial}=={want}"] = {
            "basis": ("post_hoc_best (AF R5) -- tested here, not promoted"
                      if dial == "VOL_REGIME" else "pre_declared"),
            "by_era": rows,
            "eras_positive": sum(1 for r in signed if r["mean_bucket"] > 0),
            "eras_scored": len(signed),
            "holds_in_every_era": bool(signed and all(r["mean_bucket"] > 0 for r in signed)),
        }
    out["eras"] = [f"{lo}-{hi - 1}" for lo, hi in eras]
    return out


def nzdjpy_gate_under_both_repairs(regimes: dict) -> dict:
    """AF measured the pre-declared gate at -0.1953 R/day. That was a NET number under the
    old composition and the hour-00 entry -- both of which this session repaired.

    So the same pre-declared bucket is re-run on Session AH's own arm-C trades at the
    repaired composition. This is not a new hypothesis: the bucket is AF's pre-declared one,
    the sleeve is AF's, and the only things that moved are the two repairs.
    """
    shift = HERE / "AH_ENTRY_SHIFT_TRADES.json.gz"
    if not shift.is_file():
        return {"skipped": "AH_ENTRY_SHIFT_TRADES.json.gz absent -- run ah_entry_shift.py"}
    with gzip.open(shift, "rt") as fh:
        sa = json.load(fh)
    m = "mxf_donchian_20_breakout_nzdjpy_d1"
    reg = regimes.get(m, {})
    dial, want, _why = PRE_DECLARED["donchian_20_breakout"]
    costs = load_broker_true_costs(COSTS)
    out = {"member": m, "dial": dial, "bucket": want, "basis": "pre_declared",
           "af_published_gated_pooled_oos_mean_r": -0.1953,
           "af_basis": ("AF R5, same pre-declared bucket, hour-00 entry, "
                        "v1_multiplicative composition"),
           "arms": {}}
    # The arm-C v1 leg is here for a reason an adversarial pass supplied: at broker hour 04
    # NZDJPY's hour multiplier is 0.92-1.05, below PREMIUM_FLOOR, so `damped_intraweek_mult`
    # returns `mult_ref` unchanged and the two compositions must be BIT-IDENTICAL there. Running
    # it proves the two "repairs" are not additive -- the entry shift subsumes the composition
    # repair, because they are the same defect (a rollover premium x a 10x era ratio) reached
    # two ways. Without this leg the decomposition below reads as two independent gains.
    # SHARED-POPULATION legs. The 94-trade gated arm-A cell and the 83-trade gated arm-C cell
    # are different populations -- the 11 missing bars are Friday D1 closes whose next H4 close
    # is 51-53 h away (MAX_SHIFT_HOURS), and their arm-A gross mean is HIGHER than the
    # survivors', so comparing 94 against 83 flatters the middle step. Every arm is therefore
    # ALSO run restricted to the decision bars all arms share.
    shared = {r["decision_bar_iso"] for r in sa["trades"]
              if r["member"] == m and r["arm"] == "C_h4next_h4exit" and not r.get("dropped")
              and r["engine_reachable"]}
    for arm, comp, pop in [(a, c, p) for a, c in (
            ("A_d1close_d1exit", "v1_multiplicative"),
            ("A_d1close_d1exit", "v2_damped"),
            ("B_d1close_h4exit", "v2_damped"),
            ("C_h4next_h4exit", "v1_multiplicative"),
            ("C_h4next_h4exit", "v2_damped")) for p in ("own", "shared")]:
        rows = [r for r in sa["trades"]
                if r["member"] == m and r["arm"] == arm and not r.get("dropped")
                and r["engine_reachable"]
                and (pop == "own" or r["decision_bar_iso"] in shared)]
        gated = [r for r in rows
                 if AFR.bucket(dial, reg.get(r["decision_bar_iso"], {}).get(dial)) == want]
        cell = {"n_all": len(rows), "n_gated": len(gated),
                "mean_r_gross_all": round(statistics.mean(
                    r["r_gross"] for r in rows), 5) if rows else None,
                "mean_r_gross_gated": round(statistics.mean(
                    r["r_gross"] for r in gated), 5) if gated else None}
        for label, subset in (("all", rows), ("gated", gated)):
            if len(subset) < 30:
                continue
            recs = [AFR.TradeRecord(
                sleeve=f"{m}_{arm}_{label}", symbol=r["symbol"],
                entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
                exit_utc=dt.datetime.fromisoformat(r["exit_utc"]),
                direction=r["direction"], sl_distance_price=r["sl_distance_price"],
                entry_price=r["entry_price"], r_gross=r["r_gross"],
                features={"hold_hours": r["hold_hours"]}) for r in subset]
            spec = OPTIONS["C_exploratory"].with_(
                spec_id=f"C_exploratory_ah_nzdjpy_{arm}_{label}_{comp}_{pop}",
                spread_band="mid", spread_composition=comp, declared_family_size=456,
                sleeve_symbol_allowlist={f"{m}_{arm}_{label}": (subset[0]["symbol"],)})
            with fam.fidelity_scope(_one_member(m)):
                import src.research_infra.walkforward.fidelity as _fid
                _fid.register_surface_expansion(
                    f"{m}_{arm}_{label}", parent="mx_nzdjpy_d1_donchian_20_breakout",
                    symbol="NZDJPY", timeframe="D1",
                    surface_note=f"AH entry arm {arm}, {label}")
                g = run_gate({f"{m}_{arm}_{label}": recs}, spec, costs=costs, server=SERVER)
            v = g.verdicts[f"{m}_{arm}_{label}"]
            cell[label] = {"verdict": v.verdict.value, "n_trades": v.n_trades,
                           "pooled_oos_mean_r": v.pooled_oos_mean_r, "p_raw": v.p_raw,
                           "oos_positive_fold_frac": v.gates.get("stability", {})
                           .get("oos_positive_fold_frac"),
                           "first_reason": (v.reasons[0][:200] if v.reasons else None)}
        out["arms"][f"{arm}|{comp}|{pop}"] = cell
    def g(key):
        return (out["arms"].get(key) or {}).get("gated", {}).get("pooled_oos_mean_r")

    out["decomposition"] = {}
    for pop in ("own", "shared"):
        a1 = g(f"A_d1close_d1exit|v1_multiplicative|{pop}")
        a2 = g(f"A_d1close_d1exit|v2_damped|{pop}")
        c1 = g(f"C_h4next_h4exit|v1_multiplicative|{pop}")
        c2 = g(f"C_h4next_h4exit|v2_damped|{pop}")
        out["decomposition"][pop] = {
            "gated_v1_hour00": a1, "gated_v2_hour00": a2,
            "gated_v1_hour04": c1, "gated_v2_hour04": c2,
            "composition_repair_worth_at_hour00": (
                (a2 - a1) if a1 is not None and a2 is not None else None),
            "composition_repair_worth_at_hour04": (
                (c2 - c1) if c1 is not None and c2 is not None else None),
            "entry_shift_worth_under_v1": (
                (c1 - a1) if a1 is not None and c1 is not None else None),
            "entry_shift_worth_under_v2": (
                (c2 - a2) if a2 is not None and c2 is not None else None),
        }
    out["decomposition"]["reading"] = (
        "THE TWO REPAIRS ARE NOT ADDITIVE. At broker hour 04 the compositions are bit-identical "
        "(NZDJPY's hour multiplier is 0.92-1.05, below PREMIUM_FLOOR 1.5), so "
        "composition_repair_worth_at_hour04 is 0.000 and the entry shift alone reaches the same "
        "+0.219 under AF's own unrepaired v1. They are one defect -- a rollover premium times a "
        "10x era ratio -- reached two ways, and the entry shift subsumes the composition repair. "
        "Read the `shared` population, not `own`: the arm-A cell has 11 more trades (Friday D1 "
        "closes the shift cannot take) whose gross mean is higher, so `own` flatters the middle "
        "step. On `shared` the composition repair alone leaves the sleeve NEGATIVE.")
    return out


def _one_member(member: str):
    """A one-element FamilyMember list, so `fidelity_scope` can register the parent stamp."""
    return [fam.FamilyMember(
        member=member, mechanism_key="donchian_20_breakout", mechanism="donchian_20_breakout",
        parent_sleeve="mx_nzdjpy_d1_donchian_20_breakout", symbol="NZDJPY",
        broker_symbol="NZDJPY", timeframe=16408, asset_class="fx",
        is_authored_cell=True, profile_supported=True)]


# ------------------------------------------------------------------ C5

def volume_surge_index_folds(art: dict, fams: dict, regimes: dict) -> dict:  # noqa: PLR0915
    """AF §5.2: 6/6 members positive, constant composition, band-stable, fold means
    [+0.394, -0.131, -0.018, -0.090, +0.346]. Two good folds at the ends is a regime shape --
    so is the middle explained by a dial, and does a pre-declared gate lift the fold count?"""
    f = "fam_volume_surge_reversal_index_d1"
    mem = fams[f]
    rows = [dict(r, _m=m) for m in mem for r in reachable(art["trades"].get(m, []))]
    fl = folds_of(rows)
    dial_profile = []
    for k, chunk in enumerate(fl):
        prof = {"fold": k, "n": len(chunk),
                "mean_r_gross": round(statistics.mean(r["r_gross"] for r in chunk), 5)
                if chunk else None,
                "window": [min(r["entry_utc"] for r in chunk)[:10],
                           max(r["entry_utc"] for r in chunk)[:10]] if chunk else None}
        for dial in AFR.DIALS:
            vals, buckets = [], collections.Counter()
            for r in chunk:
                v = regimes.get(r["_m"], {}).get(r["decision_bar_iso"], {}).get(dial)
                if v is not None:
                    vals.append(v)
                    buckets[AFR.bucket(dial, v)] += 1
            prof[dial] = {"median": round(statistics.median(vals), 5) if vals else None,
                          "bucket_frac": {b: round(c / len(chunk), 3)
                                          for b, c in sorted(buckets.items())} if chunk else {}}
        dial_profile.append(prof)
    # per (dial, bucket): the fold-positive fraction inside the bucket, and the mean.
    cells = {}
    for dial in AFR.DIALS:
        for b in ("lo", "mid", "hi", "xhi", "revert", "random", "trend", "dn", "flat", "up"):
            sel = [r for r in rows
                   if AFR.bucket(dial, regimes.get(r["_m"], {})
                                 .get(r["decision_bar_iso"], {}).get(dial)) == b]
            if len(sel) < 60:
                continue
            sfl = folds_of(sel)
            fm = [statistics.mean(c["r_gross"] for c in ch) if ch else None for ch in sfl]
            scored = [x for x in fm if x is not None]
            cells[f"{dial}=={b}"] = {
                "n": len(sel), "mean_r_gross": round(statistics.mean(
                    r["r_gross"] for r in sel), 5),
                "fold_means": [round(x, 5) if x is not None else None for x in fm],
                "fold_positive_frac": round(sum(1 for x in scored if x > 0) / len(scored), 3)
                if scored else None,
                "basis": ("pre_declared" if (dial, b) == PRE_DECLARED[
                    "volume_surge_reversal"] else "enumerated"),
            }
    best = max((v for v in cells.values() if v["fold_positive_frac"] is not None),
               key=lambda v: (v["fold_positive_frac"], v["mean_r_gross"]), default=None)
    best_key = next((k for k, v in cells.items() if v is best), None)

    # The gate's OWN folds, which is what AF's [+0.394, -0.131, -0.018, -0.090, +0.346]
    # actually are -- walk-forward train/test folds, net of broker-true cost, NOT the
    # equal-count chronological quintiles above. Publishing the quintiles as if they were
    # AF's folds would be comparing two different partitions of two different quantities,
    # so the question "does a dial lift the fold-positive fraction" is asked of the gate.
    costs = load_broker_true_costs(COSTS)
    gated_runs = {}
    for label, sel in (("ungated", rows),
                       ("pre_declared:PERSISTENCE==revert",
                        [r for r in rows if AFR.bucket(
                            "PERSISTENCE", regimes.get(r["_m"], {})
                            .get(r["decision_bar_iso"], {}).get("PERSISTENCE")) == "revert"]),
                       (f"enumerated_best:{best_key}",
                        [r for r in rows if best_key and AFR.bucket(
                            best_key.split("==")[0], regimes.get(r["_m"], {})
                            .get(r["decision_bar_iso"], {})
                            .get(best_key.split("==")[0])) == best_key.split("==")[1]])):
        if len(sel) < 60:
            continue
        sleeve = f"{f}|{label}"
        recs = [AFR.TradeRecord(
            sleeve=sleeve, symbol=r["symbol"],
            entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
            exit_utc=dt.datetime.fromisoformat(r["exit_utc"]),
            direction=r["direction"], sl_distance_price=r["sl_distance_price"],
            entry_price=r["entry_price"], r_gross=r["r_gross"],
            features={"hold_hours": r["hold_hours"]}) for r in sel]
        spec = OPTIONS["C_exploratory"].with_(
            spec_id=f"C_exploratory_ah_vsi_{label}", spread_band="mid",
            declared_family_size=456,
            sleeve_symbol_allowlist={sleeve: tuple(sorted({r["symbol"] for r in sel}))})
        import src.research_infra.walkforward.fidelity as _fid
        _fid.register_surface_expansion(
            sleeve, parent="mx_jp225_cash_d1_volume_surge_reversal",
            symbol=f"{len(mem)} index symbols", timeframe="D1",
            surface_note=f"AH C5 {label}")
        try:
            g = run_gate({sleeve: recs}, spec, costs=costs, server=SERVER)
            v = g.verdicts[sleeve]
            gated_runs[label] = {
                "n_trades": v.n_trades, "verdict": v.verdict.value,
                "pooled_oos_mean_r": v.pooled_oos_mean_r, "p_raw": v.p_raw,
                "oos_positive_fold_frac": v.gates.get("stability", {})
                .get("oos_positive_fold_frac"),
                "fold_test_means": [fd.get("test_mean_r") for fd in v.folds],
                "first_reason": (v.reasons[0][:220] if v.reasons else None)}
        finally:
            _fid.clear_surface_expansions()
    return {"family": f,
            "chronological_quintile_means_gross": [p["mean_r_gross"] for p in dial_profile],
            "chronological_quintile_caveat": (
                "these are equal-count chronological quintiles of the pooled GROSS series. "
                "AF's [+0.394, -0.131, -0.018, -0.090, +0.346] are the GATE's walk-forward "
                "OOS folds NET of cost -- a different partition of a different quantity. The "
                "verdict question is answered by `gate_runs`, not by these."),
            "fold_dial_profile": dial_profile, "cells": cells,
            "best_enumerated_cell": best_key,
            "pre_declared_cell": "PERSISTENCE==revert",
            "gate_runs": gated_runs,
            "enumeration_bill": {
                "n_cells_enumerated": len(cells),
                "why": ("`VOL_REGIME==hi` is the best of the enumerated cells, so its raw p "
                        "carries the enumeration as its own bill. Reported both ways rather "
                        "than at its best."),
                "bonferroni_within_enumeration": (
                    min(1.0, (gated_runs.get(f"enumerated_best:{best_key}", {})
                              .get("p_raw") or 1.0) * len(cells))),
                "declared_family_size_that_would_admit": {
                    "bh_alpha_0.20": int(0.20 / p_) if (p_ := (
                        gated_runs.get(f"enumerated_best:{best_key}", {})
                        .get("p_raw") or 1.0)) else None,
                    "bonferroni_alpha_0.05": int(0.05 / p_) if p_ else None,
                },
            },
            "note": ("`cells` enumerates every dial bucket with n >= 60 and stamps the "
                     "pre-declared one. The enumerated best is a LOOK, logged to the ledger, "
                     "and is reported as 'which regime came closest' -- not as an admission.")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("all",))
    ap.parse_args()
    t0 = dt.datetime.now(dt.timezone.utc)
    art, series, regimes = load_all()
    fams = members_of(art)
    presc = {r["sleeve"]: r["prescription"]
             for r in json.loads(QUEUE_AF.read_text())["rows"]}
    print(f"{len(fams)} families, {sum(len(v) for v in fams.values())} members")

    print("C1 carrier stability ...", flush=True)
    C1 = carrier_stability(art, fams)
    print("C1b carrier holdout ...", flush=True)
    C1b = carrier_holdout(art, fams)
    print("C2 pre-declared conditioning ...", flush=True)
    C2 = pre_declared_conditioning(art, fams, regimes)
    print("C3 crypto donchian split ...", flush=True)
    C3 = crypto_donchian_split(art, series, fams)
    print("C4 nzdjpy break by era ...", flush=True)
    C4 = nzdjpy_break_by_era(art, regimes)
    print("C4b nzdjpy under both repairs ...", flush=True)
    C4b = nzdjpy_gate_under_both_repairs(regimes)
    print("C5 volume-surge index folds ...", flush=True)
    C5 = volume_surge_index_folds(art, fams, regimes)

    mixtures = sorted(f for f, p in presc.items()
                      if p == "MEMBER_CONDITIONING_NOT_BREADTH")
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AH")
    for f in sorted(fams):
        c2 = C2[f]
        if f.startswith("_"):
            continue
        ledger.record(
            mechanism=art["grid"]["families"][f]["mechanism"], sleeve=f,
            variant={"scope": "pre_declared_regime_gate", "dial": c2["dial"],
                     "bucket": c2["bucket"], "basis": "pre_declared"},
            window=art["grid"]["families"][f].get("window", ""),
            outcome=("positive" if (c2["gated"]["mean_of_member_means"] or 0) > 0
                     else "negative"),
            metric=c2["gated"]["mean_of_member_means"],
            metric_name="mean_of_member_means_r_gross",
            spec_sha256=hashlib.sha256(
                f"AH|C2|{f}|{c2['dial']}|{c2['bucket']}".encode()).hexdigest(),
            note="AH C2: the pre-declared dial bucket for this mechanism, member level")
    for k, v in C5["cells"].items():
        ledger.record(
            mechanism="volume_surge_reversal", sleeve=C5["family"],
            variant={"scope": "regime_cell", "cell": k, "basis": v["basis"]},
            window="", outcome=("positive" if v["mean_r_gross"] > 0 else "negative"),
            metric=v["mean_r_gross"], metric_name="mean_r_gross",
            spec_sha256=hashlib.sha256(f"AH|C5|{C5['family']}|{k}".encode()).hexdigest(),
            note="AH C5: dial-bucket enumeration on the index volume-surge family")

    out = {
        "schema": "gtos.ah.conditioning_map.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "generated_utc": t0.isoformat(),
        "trades_artifact": str(TRADES.relative_to(REPO)),
        "dials": AFR.DIALS,
        "pre_declared": {k: {"dial": v[0], "bucket": v[1], "why": v[2]}
                         for k, v in PRE_DECLARED.items()},
        "af_prescriptions": presc,
        "mixture_families": mixtures,
        "C1_carrier_stability": C1,
        "C1b_carrier_holdout": C1b,
        "C2_pre_declared_conditioning": C2,
        "C3_crypto_donchian_split": C3,
        "C4_nzdjpy_break_by_era": C4,
        "C4b_nzdjpy_under_both_repairs": C4b,
        "C5_volume_surge_index_folds": C5,
        "summary": {
            "n_mixture_families": len(mixtures),
            "n_carrier_stable_two_clause": sum(
                1 for f in mixtures
                if (C1[f]["carrier_jaccard_adjacent"] or 0) > (C1[f]["chance_jaccard"] or 1)
                and (C1[f]["holdout_sign_agreement"] or 0) >= 0.6),
            "n_coheres_under_pre_declared_dial": sum(
                1 for f in fams if C2[f]["coheres_gated"]),
            "coherent_families": sorted(f for f in fams if C2[f]["coheres_gated"]),
            "n_carrier_selection_helps_on_holdout": sum(
                1 for f in mixtures if (C1b[f]["selection_gain_r_gross"] or 0) > 0),
            "n_mixtures_scoreable_on_holdout": sum(
                1 for f in mixtures if C1b[f]["selection_gain_r_gross"] is not None),
            "carrier_selection_gain_trade_weighted": C1b["_trade_weighted"]["gain"],
            "n_overlap_beats_chance": sum(
                1 for f in mixtures
                if (C1[f]["carrier_jaccard_adjacent"] or 0) > (C1[f]["chance_jaccard"] or 1)),
            "n_overlap_below_chance": sum(
                1 for f in mixtures
                if (C1[f]["carrier_jaccard_adjacent"] or 1) < (C1[f]["chance_jaccard"] or 0)),
            "median_carrier_selection_gain_on_holdout": statistics.median(
                [C1b[f]["selection_gain_r_gross"] for f in mixtures
                 if C1b[f]["selection_gain_r_gross"] is not None]),
        },
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.2f} MB)")
    print(json.dumps(out["summary"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
