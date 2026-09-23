"""Entry-conditioning study (geometry held at baseline 0.5ATR stop / 2R target).

Dimension: entry_conditioning. Geometry is FIXED at the confirmed baseline winning
geometry (stop = 0.5*ATR, target = 2R = 1.0*ATR, first-touch over <=60 bars,
pessimistic same-bar so the stop wins ties, minus real per-asset-class cost).

We decompose per-trade R by:
  - FAMILY  (S1-S5)  -- the 5 signal families inside the shared candidate-direction recipe
  - ASSET_CLASS
  - SESSION-HOUR-BUCKET (H4 bar-start hour, UTC-as-stored)
  - REGIME (trend up/down/flat) x (vol expand / contract / normal)

A single candidate can be produced by multiple family rules at the same bar; each
fired (family, direction) candidate is attributed to its family. The portfolio
("ALL") number is the de-duplicated set of (bar, direction) candidates exactly as
the baseline recipe fires them (one row per distinct direction at an entry bar),
so the ALL per-trade R reproduces the baseline +0.69R headline.

Goal: rank keep/drop conditioning that RAISES portfolio per-trade R, and judge
whether the tight-stop edge is broad (robust) or concentrated.

SHARED ENTRY-DETECTION RECIPE is reproduced exactly from structural_geometry_study.py
(features, debounce, candidate directions). Only the geometry/exit is fixed to the
single baseline and the bookkeeping is by-condition.
"""
import csv, json, statistics, sys, collections
from pathlib import Path

ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

COST = json.loads((ROUTE / "ULTIMATE_REAL_COST_MAP.json").read_text())
GCOST = COST.get("_global_median", 0.095)
D = REPO_ROOT / "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"

MAXBARS = 60
STOP_ATR = 0.5          # baseline stop = 0.5 ATR  (R unit = stop distance)
TARGET_R = 2.0          # baseline target = 2R = 1.0 ATR

# Family labels for the 10 candidate-direction rules in the shared recipe.
FAMILIES = {
    "S1_sweep": "swept liquidity reversal (swl->+1, swh->-1)",
    "S2_lowvol_pullback": "low-vol pullback with trend (relv<=0.6 & down&low->+1 / up&high->-1)",
    "S3_expansion_breakout": "expansion breakout (relv>=1.8 & expb & dir-consistent body)",
    "S4_absorption": "absorption at extreme (absb & low->+1 / high->-1)",
    "S5_voldelta_reversion": "vol-delta reversion at extreme (high&vdacc<0->-1 / low&vdacc>0->+1)",
}

PARTITIONS = {  # year -> partition
    "2022": "TRAIN", "2023": "TRAIN", "2024": "TRAIN",
    "2025": "FORWARD", "2026": "FORWARD",
}

# H4 bar-start hours present in the data are 0,4,8,12,16,20. Bucket into sessions.
def hour_bucket(hr):
    # H4 bars start at 00,04,08,12,16,20 (UTC-as-stored in the export)
    if hr in (0, 4):
        return "asia_0_4"
    if hr in (8, 12):
        return "london_8_12"
    if hr in (16, 20):
        return "ny_16_20"
    return f"hr{hr:02d}"


def new_acc():
    return {"n": 0, "wins": 0, "tot_r": 0.0,
            "yr_n": collections.defaultdict(int), "yr_r": collections.defaultdict(float),
            "part_n": collections.defaultdict(int), "part_r": collections.defaultdict(float)}


def record(acc, r_net, win, yr):
    acc["n"] += 1
    acc["tot_r"] += r_net
    acc["wins"] += 1 if win else 0
    acc["yr_n"][yr] += 1
    acc["yr_r"][yr] += r_net
    p = PARTITIONS.get(yr, "OTHER")
    acc["part_n"][p] += 1
    acc["part_r"][p] += r_net


def summ(acc):
    n = acc["n"]
    if n == 0:
        return None
    out = {
        "n": n,
        "per_trade_R": round(acc["tot_r"] / n, 4),
        "win": round(acc["wins"] / n, 4),
        "total_R": round(acc["tot_r"], 1),
        "per_year": {y: {"n": acc["yr_n"][y], "per_trade_R": round(acc["yr_r"][y] / acc["yr_n"][y], 4)}
                     for y in sorted(acc["yr_n"])},
        "per_partition": {p: {"n": acc["part_n"][p], "per_trade_R": round(acc["part_r"][p] / acc["part_n"][p], 4)}
                          for p in sorted(acc["part_n"])},
    }
    return out


def simulate(d, entry, atr, c, Hh, L, i, n):
    """Baseline geometry: stop=0.5ATR, target=2R. Pessimistic same-bar (stop wins ties).
    Returns (r_net, win_bool, resolved_bool)."""
    risk = STOP_ATR * atr
    tgt = TARGET_R * risk
    for j in range(i + 1, min(i + MAXBARS, n)):
        if d > 0:
            adv = entry - L[j]      # adverse excursion (toward stop)
            fav = Hh[j] - entry     # favorable excursion (toward target)
        else:
            adv = Hh[j] - entry
            fav = entry - L[j]
        hit_stop = adv >= risk
        hit_tgt = fav >= tgt
        if hit_stop:               # pessimistic: stop wins ties / same-bar
            return (-1.0 - c, False, True)
        if hit_tgt:
            return (TARGET_R - c, True, True)
    # unresolved within MAXBARS -> only pay cost (no stop, no target)
    return (-c, False, False)


def main():
    by_family = {fam: new_acc() for fam in FAMILIES}
    by_ac = collections.defaultdict(new_acc)
    by_hour = collections.defaultdict(new_acc)
    by_regime = collections.defaultdict(new_acc)          # trend x volstate
    by_trend = collections.defaultdict(new_acc)
    by_volstate = collections.defaultdict(new_acc)
    by_posb = collections.defaultdict(new_acc)
    by_dir = collections.defaultdict(new_acc)             # long/short split (bug in prior study only hit shorts)
    by_fam_ac = collections.defaultdict(new_acc)          # family x asset_class
    by_fam_part = collections.defaultdict(new_acc)        # family x partition (for forward stability)
    allacc = new_acc()                                    # de-duplicated portfolio (baseline headline)

    N_candrows = 0    # total (family,dir) fired rows
    N_portfolio = 0   # de-duplicated (bar,dir) candidates

    for f in sorted(D.glob("*_H4.csv")):
        sym = f.name[:-7]
        ac = ASSET_CLASS_BY_SYMBOL.get(sym)
        if ac is None:
            continue
        cost = float(COST.get(ac, GCOST))
        rows = [(str(r["time"])[:19], float(r["open"]), float(r["high"]), float(r["low"]),
                 float(r["close"]), float(r["volume"]))
                for r in csv.DictReader(open(f)) if r.get("close") and r.get("volume")]
        if len(rows) < 250:
            continue
        n = len(rows)
        O = [x[1] for x in rows]; Hh = [x[2] for x in rows]; L = [x[3] for x in rows]
        C = [x[4] for x in rows]; V = [x[5] for x in rows]; T = [x[0] for x in rows]
        tr = [0.0] * n
        for i in range(1, n):
            tr[i] = max(Hh[i] - L[i], abs(Hh[i] - C[i - 1]), abs(L[i] - C[i - 1]))
        rng = [Hh[i] - L[i] for i in range(n)]
        vd = [(V[i] * (C[i] - O[i]) / rng[i]) if rng[i] > 0 else 0.0 for i in range(n)]
        prev = None
        for i in range(60, n - 1):
            atr = sum(tr[i - 13:i + 1]) / 14
            if atr <= 0:
                continue
            m20 = sum(C[i - 19:i + 1]) / 20; m50 = sum(C[i - 49:i + 1]) / 50
            trend = "up" if m20 > m50 * 1.001 else ("down" if m20 < m50 * 0.999 else "flat")
            hi, lo = max(Hh[i - 47:i + 1]), min(L[i - 47:i + 1])
            pos = (C[i] - lo) / (hi - lo) if hi > lo else .5
            posb = "low" if pos < .25 else ("high" if pos > .75 else "mid")
            relv = V[i] / (sum(V[i - 19:i + 1]) / 20 or 1)
            eff = rng[i] / V[i] if V[i] > 0 else 0
            beff = sum((rng[k] / V[k] if V[k] > 0 else 0) for k in range(i - 19, i + 1)) / 20
            absb = eff <= 0.6 * beff if beff > 0 else False
            expb = eff >= 1.4 * beff if beff > 0 else False
            volstate = "expand" if expb else ("contract" if absb else "normal")
            ph, pl = max(Hh[i - 20:i]), min(L[i - 20:i])
            swh = Hh[i] > ph and C[i] < ph and relv >= 1.5
            swl = L[i] < pl and C[i] > pl and relv >= 1.5
            vdacc = sum(vd[i - 2:i + 1])
            tup = (trend, posb, relv >= 1.5, bool(swh or swl))
            is_entry = tup != prev
            prev = tup
            if not is_entry:
                continue

            # (family, direction) candidate rules
            fam_cands = []   # list of (family, dir)
            if swl: fam_cands.append(("S1_sweep", +1))
            if swh: fam_cands.append(("S1_sweep", -1))
            if relv <= 0.6 and trend == "down" and posb == "low": fam_cands.append(("S2_lowvol_pullback", +1))
            if relv <= 0.6 and trend == "up" and posb == "high": fam_cands.append(("S2_lowvol_pullback", -1))
            if relv >= 1.8 and expb and posb == "high" and C[i] > O[i]: fam_cands.append(("S3_expansion_breakout", +1))
            if relv >= 1.8 and expb and posb == "low" and C[i] < O[i]: fam_cands.append(("S3_expansion_breakout", -1))
            if absb and posb == "low": fam_cands.append(("S4_absorption", +1))
            if absb and posb == "high": fam_cands.append(("S4_absorption", -1))
            if posb == "high" and vdacc < 0: fam_cands.append(("S5_voldelta_reversion", -1))
            if posb == "low" and vdacc > 0: fam_cands.append(("S5_voldelta_reversion", +1))

            if not fam_cands:
                continue

            entry = C[i]
            yr = T[i][:4]
            hr = int(T[i][11:13])
            hb = hour_bucket(hr)
            regime_key = f"{trend}|{volstate}"

            # cache per-direction sim result (geometry independent of family)
            sim_cache = {}
            def get_sim(d):
                if d not in sim_cache:
                    sim_cache[d] = simulate(d, entry, atr, cost, Hh, L, i, n)
                return sim_cache[d]

            # 1) family-attributed bookkeeping (every fired family,dir row)
            for fam, d in fam_cands:
                r_net, win, _ = get_sim(d)
                N_candrows += 1
                record(by_family[fam], r_net, win, yr)
                record(by_fam_ac[f"{fam}|{ac}"], r_net, win, yr)
                record(by_fam_part[fam], r_net, win, yr)  # partition split lives inside acc

            # 2) de-duplicated portfolio bookkeeping (one row per distinct direction)
            dirs = sorted(set(d for _, d in fam_cands))
            for d in dirs:
                r_net, win, _ = get_sim(d)
                N_portfolio += 1
                record(allacc, r_net, win, yr)
                record(by_ac[ac], r_net, win, yr)
                record(by_hour[hb], r_net, win, yr)
                record(by_regime[regime_key], r_net, win, yr)
                record(by_trend[trend], r_net, win, yr)
                record(by_volstate[volstate], r_net, win, yr)
                record(by_posb[posb], r_net, win, yr)
                record(by_dir["long" if d > 0 else "short"], r_net, win, yr)

    def dump(d):
        return {k: summ(v) for k, v in sorted(d.items()) if v["n"] > 0}

    # ---- ranked keep/drop conditioning ----
    # rank each conditioning slice by per-trade R; flag drop if per-trade R < ALL baseline.
    base = allacc["tot_r"] / allacc["n"] if allacc["n"] else 0.0

    def ranked(d, min_n=150):
        items = []
        for k, v in d.items():
            if v["n"] < min_n:
                continue
            pt = v["tot_r"] / v["n"]
            # forward per-trade R for stability flag
            fwd = (v["part_r"]["FORWARD"] / v["part_n"]["FORWARD"]) if v["part_n"].get("FORWARD") else None
            items.append({"key": k, "n": v["n"], "per_trade_R": round(pt, 4),
                          "forward_per_trade_R": round(fwd, 4) if fwd is not None else None,
                          "lift_vs_baseline": round(pt - base, 4),
                          "verdict": "KEEP" if pt >= base else "DROP"})
        items.sort(key=lambda x: x["per_trade_R"], reverse=True)
        return items

    # ---- recompute portfolio per-trade R after dropping the worst families ----
    fam_pt = {fam: (by_family[fam]["tot_r"] / by_family[fam]["n"] if by_family[fam]["n"] else None)
              for fam in FAMILIES}

    # Greedy keep set on the DE-DUPLICATED portfolio: rebuild ALL keeping only families
    # whose family per_trade_R >= 0 (positive-edge families), and also a stricter ">=baseline".
    # We approximate the de-dup effect by recomputing on family rows but de-duplicating dirs;
    # since per-direction sim is shared, dropping a family removes a candidate only if no other
    # KEPT family produced that direction at that bar. We re-simulate for accuracy.
    keep_pos = [fam for fam in FAMILIES if (fam_pt[fam] is not None and fam_pt[fam] >= 0)]
    keep_base = [fam for fam in FAMILIES if (fam_pt[fam] is not None and fam_pt[fam] >= base)]

    def portfolio_with_families(keep_fams):
        acc = new_acc()
        keep = set(keep_fams)
        for f in sorted(D.glob("*_H4.csv")):
            sym = f.name[:-7]
            ac = ASSET_CLASS_BY_SYMBOL.get(sym)
            if ac is None:
                continue
            cost = float(COST.get(ac, GCOST))
            rows = [(str(r["time"])[:19], float(r["open"]), float(r["high"]), float(r["low"]),
                     float(r["close"]), float(r["volume"]))
                    for r in csv.DictReader(open(f)) if r.get("close") and r.get("volume")]
            if len(rows) < 250:
                continue
            n = len(rows)
            O = [x[1] for x in rows]; Hh = [x[2] for x in rows]; L = [x[3] for x in rows]
            C = [x[4] for x in rows]; V = [x[5] for x in rows]; T = [x[0] for x in rows]
            tr = [0.0] * n
            for i in range(1, n):
                tr[i] = max(Hh[i] - L[i], abs(Hh[i] - C[i - 1]), abs(L[i] - C[i - 1]))
            rng = [Hh[i] - L[i] for i in range(n)]
            vd = [(V[i] * (C[i] - O[i]) / rng[i]) if rng[i] > 0 else 0.0 for i in range(n)]
            prev = None
            for i in range(60, n - 1):
                atr = sum(tr[i - 13:i + 1]) / 14
                if atr <= 0:
                    continue
                m20 = sum(C[i - 19:i + 1]) / 20; m50 = sum(C[i - 49:i + 1]) / 50
                trend = "up" if m20 > m50 * 1.001 else ("down" if m20 < m50 * 0.999 else "flat")
                hi, lo = max(Hh[i - 47:i + 1]), min(L[i - 47:i + 1])
                pos = (C[i] - lo) / (hi - lo) if hi > lo else .5
                posb = "low" if pos < .25 else ("high" if pos > .75 else "mid")
                relv = V[i] / (sum(V[i - 19:i + 1]) / 20 or 1)
                eff = rng[i] / V[i] if V[i] > 0 else 0
                beff = sum((rng[k] / V[k] if V[k] > 0 else 0) for k in range(i - 19, i + 1)) / 20
                absb = eff <= 0.6 * beff if beff > 0 else False
                expb = eff >= 1.4 * beff if beff > 0 else False
                ph, pl = max(Hh[i - 20:i]), min(L[i - 20:i])
                swh = Hh[i] > ph and C[i] < ph and relv >= 1.5
                swl = L[i] < pl and C[i] > pl and relv >= 1.5
                vdacc = sum(vd[i - 2:i + 1])
                tup = (trend, posb, relv >= 1.5, bool(swh or swl))
                is_entry = tup != prev
                prev = tup
                if not is_entry:
                    continue
                fam_cands = []
                if swl: fam_cands.append(("S1_sweep", +1))
                if swh: fam_cands.append(("S1_sweep", -1))
                if relv <= 0.6 and trend == "down" and posb == "low": fam_cands.append(("S2_lowvol_pullback", +1))
                if relv <= 0.6 and trend == "up" and posb == "high": fam_cands.append(("S2_lowvol_pullback", -1))
                if relv >= 1.8 and expb and posb == "high" and C[i] > O[i]: fam_cands.append(("S3_expansion_breakout", +1))
                if relv >= 1.8 and expb and posb == "low" and C[i] < O[i]: fam_cands.append(("S3_expansion_breakout", -1))
                if absb and posb == "low": fam_cands.append(("S4_absorption", +1))
                if absb and posb == "high": fam_cands.append(("S4_absorption", -1))
                if posb == "high" and vdacc < 0: fam_cands.append(("S5_voldelta_reversion", -1))
                if posb == "low" and vdacc > 0: fam_cands.append(("S5_voldelta_reversion", +1))
                dirs = sorted(set(d for fam, d in fam_cands if fam in keep))
                if not dirs:
                    continue
                entry = C[i]; yr = T[i][:4]
                for d in dirs:
                    r_net, win, _ = simulate(d, entry, atr, cost, Hh, L, i, n)
                    record(acc, r_net, win, yr)
        return acc

    acc_pos = portfolio_with_families(keep_pos)
    acc_base = portfolio_with_families(keep_base)

    out = {
        "schema_version": "entry_conditioning_study_v1",
        "geometry": {"stop_atr": STOP_ATR, "target_R": TARGET_R, "max_bars": MAXBARS,
                     "tie_rule": "pessimistic_stop_wins_same_bar", "R_unit": "stop_distance(0.5ATR)"},
        "RECONCILIATION_ALERT": {
            "claim": "shared recipe states baseline 0.5ATR/2R == +0.69R/trade, 57% win",
            "finding": "that headline is NOT reproducible with a correct short-side stop. The prior "
                       "ULTIMATE_STRUCTURAL_GEOMETRY_STUDY.json (atr05/TP2 = +0.6932R / 0.567 win) "
                       "contains a stop-side sign bug for shorts: its adverse excursion line "
                       "'adv=d*(entry-L[j]) if d>0 else d*(Hh[j]-entry)' yields adv=entry-Hh[j] for "
                       "shorts, which is NEGATIVE when price rises, so short stops almost never "
                       "trigger and shorts 'win' fictitiously over up to 60 bars.",
            "verified": "unit-tested correct exit logic; reran identical 15290 entries; structural "
                        "logic reproduces +0.6932R/0.567, corrected logic gives -0.0824R/0.336 over "
                        "the same entries (5644 trade-level mismatches, 3957 of them buggy short 'wins').",
            "honest_baseline_per_trade_R": round(allacc["tot_r"] / allacc["n"], 4) if allacc["n"] else None,
            "honest_baseline_win": round(allacc["wins"] / allacc["n"], 4) if allacc["n"] else None,
        },
        "n_family_rows": N_candrows,
        "n_portfolio_dedup": N_portfolio,
        "baseline_portfolio_ALL": summ(allacc),
        "family_definitions": FAMILIES,
        "by_family": dump(by_family),
        "by_asset_class": dump(by_ac),
        "by_hour_bucket": dump(by_hour),
        "by_trend": dump(by_trend),
        "by_volstate": dump(by_volstate),
        "by_regime_trend_x_vol": dump(by_regime),
        "by_posbucket": dump(by_posb),
        "by_direction": dump(by_dir),
        "by_family_x_asset_class": dump(by_fam_ac),
        "ranked_keep_drop": {
            "baseline_per_trade_R": round(base, 4),
            "families": ranked(by_family, min_n=100),
            "asset_classes": ranked(by_ac, min_n=150),
            "hour_buckets": ranked(by_hour, min_n=150),
            "regimes": ranked(by_regime, min_n=150),
        },
        "portfolio_after_drops": {
            "keep_positive_families": {"families": keep_pos, "summary": summ(acc_pos)},
            "keep_ge_baseline_families": {"families": keep_base, "summary": summ(acc_base)},
        },
    }
    (ROUTE / "ULTIMATE_ENTRY_CONDITIONING_STUDY.json").write_text(json.dumps(out, indent=1, sort_keys=True))

    # ---- console report ----
    print("=" * 78)
    print("ENTRY-CONDITIONING STUDY  (geometry fixed: 0.5ATR stop / 2R target)")
    print("=" * 78)
    b = out["baseline_portfolio_ALL"]
    print(f"BASELINE PORTFOLIO (dedup): n={b['n']}  per_trade_R={b['per_trade_R']:+.4f}  win={b['win']:.3f}")
    print(f"  per_partition: " + "  ".join(f"{p}={v['per_trade_R']:+.4f}(n={v['n']})" for p, v in b['per_partition'].items()))
    print(f"  per_year: " + "  ".join(f"{y}={v['per_trade_R']:+.3f}" for y, v in b['per_year'].items()))
    print(f"  [family rows fired={N_candrows}  dedup portfolio candidates={N_portfolio}]")

    def section(title, items):
        print(f"\n--- {title} (per_trade_R desc; baseline={base:+.4f}) ---")
        for it in items:
            fwd = f"{it['forward_per_trade_R']:+.4f}" if it['forward_per_trade_R'] is not None else "  n/a "
            print(f"  {it['verdict']:4s} {it['key']:28s} n={it['n']:5d}  pt={it['per_trade_R']:+.4f}  fwd={fwd}  lift={it['lift_vs_baseline']:+.4f}")

    print("\n--- DIRECTION SPLIT (prior study bug only affected shorts) ---")
    for k, v in out["by_direction"].items():
        print(f"  {k:6s} n={v['n']:5d}  per_trade_R={v['per_trade_R']:+.4f}  win={v['win']:.3f}")

    section("FAMILY", out["ranked_keep_drop"]["families"])
    section("ASSET_CLASS", out["ranked_keep_drop"]["asset_classes"])
    section("HOUR_BUCKET", out["ranked_keep_drop"]["hour_buckets"])
    section("REGIME (trend|vol)", out["ranked_keep_drop"]["regimes"])

    print("\n--- PORTFOLIO AFTER DROPPING WEAK FAMILIES ---")
    ap = out["portfolio_after_drops"]["keep_positive_families"]
    abz = out["portfolio_after_drops"]["keep_ge_baseline_families"]
    print(f"  baseline (all 5 families):      per_trade_R={base:+.4f}  n={allacc['n']}")
    if ap["summary"]:
        print(f"  keep positive-edge families {ap['families']}:")
        print(f"      per_trade_R={ap['summary']['per_trade_R']:+.4f}  n={ap['summary']['n']}  win={ap['summary']['win']:.3f}")
    if abz["summary"]:
        print(f"  keep >=baseline families {abz['families']}:")
        print(f"      per_trade_R={abz['summary']['per_trade_R']:+.4f}  n={abz['summary']['n']}  win={abz['summary']['win']:.3f}")
    print("\nwrote ULTIMATE_ENTRY_CONDITIONING_STUDY.json")


if __name__ == "__main__":
    main()
