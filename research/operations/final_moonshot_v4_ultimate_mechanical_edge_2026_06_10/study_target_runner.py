"""target_runner study: hold stop at 0.5ATR, vary EXIT MANAGEMENT on the
SAME entries as the confirmed baseline winning geometry.

Shared entry-detection recipe (identical to structural_geometry_study.py /
the confirmed +0.69R baseline). R-unit = stop distance = 0.5*ATR. All targets
are expressed in R, so e.g. 2R = 1.0*ATR favorable.

Exit managers compared (stop fixed at 0.5ATR = 1R for all):
  fixed TP @ 1.5R / 2.0R / 2.5R / 3.0R  (first-touch, pessimistic ties)
  partial @2R: close 50% at +2R, move stop to breakeven (BE),
               runner to +4R fixed  -> 'partial_2R_be_4R'
  partial @2R: close 50% at +2R, move stop to BE,
               runner trails by 1R (chandelier on favorable extreme) -> 'partial_2R_be_trail'
  full trail after 2R: no partial; once +2R reached, trail stop 1R behind
               favorable extreme (give back 1R) -> 'trail_after_2R'

Per-bar simulation (not pure first-touch) because partial/BE/trail are
path-dependent. Pessimistic same-bar convention: within a bar, the ADVERSE
extreme (stop side) is assumed hit BEFORE the favorable extreme (stop wins
ties / same-bar). This matches the baseline's 'stop wins ties' rule.

Cost: real per-asset-class expected_cost_r from ULTIMATE_REAL_COST_MAP.json,
applied once per UNIT of position closed (partials pay cost on each leg in
proportion to size closed) -- i.e. total cost over the trade = c (one full
position's round-trip cost), charged proportionally as legs close, so a
fully-closed trade always pays exactly c regardless of how many legs.

Partitions: TRAIN 2022-2024, FORWARD 2025-2026. Per-year reported.
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

# managers
FIXED = [1.5, 2.0, 2.5, 3.0]
MANAGERS = (
    [f"fixed_{t}R" for t in FIXED]
    + ["partial_2R_be_4R", "partial_2R_be_trail", "trail_after_2R"]
)


def simulate(d, entry, risk, c, bars, adv_bug=False):
    """Return dict manager -> (net_R, win_flag, exit_bar_offset).

    bars: list of (H, L) AFTER entry, in order, up to MAXBARS.
    risk: 1R distance in price (= 0.5*ATR). d: +1 long, -1 short.
    Pessimistic same-bar: adverse extreme assumed before favorable extreme.
    Cost c charged proportionally to size closed (full close pays exactly c).

    adv_bug: if True, reproduce the SHORT-side adverse sign convention used by
    the confirmed +0.69R baseline / structural_geometry_study.py reference
    code (adv for shorts = entry-Low instead of High-entry). This is a
    documented sign bug that makes shorts almost never stop out; we run BOTH
    conventions so the exit-management RANKING is convention-robust and the
    bug is quantified. adv_bug=False is the CORRECT geometry.
    """
    res = {}

    def fav(h, l):
        return (h - entry) if d > 0 else (entry - l)

    def adv(h, l):
        # how far price went AGAINST us (positive = adverse distance)
        if adv_bug:
            # baseline reference convention: adv = d*(entry-L) if long else
            # d*(High-entry) -> for shorts simplifies to (entry-High), which is
            # almost never >= risk. Reproduces the +0.69R / 57% baseline.
            return (entry - l) if d > 0 else (entry - h)
        return (entry - l) if d > 0 else (h - entry)

    # ---- fixed TP managers (first-touch, pessimistic ties) ----
    for t in FIXED:
        net = None
        exitb = None
        for k, (h, l) in enumerate(bars):
            a = adv(h, l)
            fv = fav(h, l)
            # pessimistic: stop checked first (ties to stop)
            if a >= risk:
                net = -1.0 - c
                exitb = k + 1
                break
            if fv >= t * risk:
                net = t - c
                exitb = k + 1
                break
        if net is None:
            # time exit: mark-to-market at final close-equivalent? Baseline
            # treats unresolved as just -cost (no R captured). Mirror that.
            net = -c
            exitb = len(bars)
        res[f"fixed_{t}R"] = (net, 1 if net > 0 else 0, exitb)

    # ---- partial @2R, BE, runner to +4R fixed ----
    res["partial_2R_be_4R"] = _partial(d, entry, risk, c, bars, fav, adv,
                                       runner_mode="fixed4")
    # ---- partial @2R, BE, runner trails 1R ----
    res["partial_2R_be_trail"] = _partial(d, entry, risk, c, bars, fav, adv,
                                          runner_mode="trail1")
    # ---- full trail after 2R (no partial, give back 1R) ----
    res["trail_after_2R"] = _full_trail(d, entry, risk, c, bars, fav, adv)
    return res


def _partial(d, entry, risk, c, bars, fav, adv, runner_mode):
    """50% off at +2R, remaining 50% stop->BE, runner per runner_mode.
    Cost split: each 50% leg pays c/2 (full close pays c)."""
    stop_dist = risk          # initial 1R stop (adverse distance that stops)
    be = False                # has stop moved to breakeven (after partial)
    partial_done = False
    realized = 0.0            # realized R on closed size (size-weighted, *fraction)
    # We carry two halves. Track favorable extreme for trailing.
    fav_ext = 0.0
    half_cost = c / 2.0
    for k, (h, l) in enumerate(bars):
        a = adv(h, l)
        fv = fav(h, l)
        # ---- pessimistic: check stop BEFORE favorable for this bar ----
        if not partial_done:
            # full position still on, stop at -1R
            if a >= stop_dist:
                # whole position stopped at -1R
                return (-1.0 - c, 0, k + 1)
            if fv >= 2.0 * risk:
                # partial fills: 50% at +2R, move stop to BE for runner
                realized += 0.5 * 2.0 - half_cost
                partial_done = True
                be = True
                fav_ext = fv
                # runner may also resolve same bar; with BE stop and same-bar
                # pessimism, if price also returned to entry this bar the
                # runner exits at BE (0R). Check below in runner block but
                # using updated state. Fall through to runner handling.
            else:
                continue
        # ---- runner active (50% remaining, stop at BE) ----
        # update favorable extreme
        if fv > fav_ext:
            fav_ext = fv
        # BE stop: adverse back to entry (a>=0 means touched entry). Pessimistic
        # same-bar: BE checked before further favorable on subsequent bars.
        if be and a >= 0.0:
            # runner exits at breakeven (0R on the half)
            realized += 0.5 * 0.0 - half_cost
            return (realized, 1 if realized > 0 else 0, k + 1)
        if runner_mode == "fixed4":
            if fv >= 4.0 * risk:
                realized += 0.5 * 4.0 - half_cost
                return (realized, 1, k + 1)
        else:  # trail1: trail 1R behind favorable extreme, only after >=2R
            trail_level = fav_ext - 1.0 * risk  # favorable distance floor
            if trail_level > 0 and fv <= trail_level and fav_ext > fv:
                # price gave back 1R from extreme -> exit runner at trail level
                captured = trail_level  # in price-distance / risk = R
                realized += 0.5 * (captured / risk) - half_cost
                return (realized, 1 if realized > 0 else 0, k + 1)
    # time exit at end
    if partial_done:
        # mark runner at final favorable level reached? Baseline marks
        # unresolved as no extra R -> runner exits at BE-ish (0R) minus cost.
        realized += 0.5 * 0.0 - half_cost
        return (realized, 1 if realized > 0 else 0, len(bars))
    return (-c, 0, len(bars))


def _full_trail(d, entry, risk, c, bars, fav, adv):
    """No partial. Stop at -1R until +2R reached, then trail 1R behind the
    favorable extreme (give back 1R). Full size throughout; pays cost c once."""
    armed = False
    fav_ext = 0.0
    for k, (h, l) in enumerate(bars):
        a = adv(h, l)
        fv = fav(h, l)
        if not armed:
            # pessimistic: stop first
            if a >= risk:
                return (-1.0 - c, 0, k + 1)
            if fv >= 2.0 * risk:
                armed = True
                fav_ext = fv
            else:
                continue
        # trailing active
        if fv > fav_ext:
            fav_ext = fv
        trail_level = fav_ext - 1.0 * risk
        # pessimistic same-bar: trail checked before new favorable extreme on
        # later bars (already updated fav_ext this bar above; conservative is
        # to check trail against current fv with prior extreme). Use fav_ext.
        if fv <= trail_level and fav_ext > fv:
            return (trail_level / risk - c, 1 if trail_level / risk - c > 0 else 0, k + 1)
    # time exit: mark at final favorable extreme minus give-back? Baseline
    # unresolved -> capture trail_level if armed else -cost.
    if armed:
        cap = max(0.0, fav_ext - 1.0 * risk) / risk
        return (cap - c, 1 if cap - c > 0 else 0, len(bars))
    return (-c, 0, len(bars))


CONVENTIONS = {"correct": False, "baseline_advbug": True}


def main():
    # agg[convention][manager][scope] and per-year
    def newacc():
        return {"n": 0, "tot": 0.0, "win": 0, "bars": [],
                "yr": collections.defaultdict(lambda: {"n": 0, "tot": 0.0, "win": 0})}
    agg = {conv: {m: {"ALL": newacc(), "TRAIN": newacc(), "FORWARD": newacc()}
                  for m in MANAGERS} for conv in CONVENTIONS}
    N = 0
    for f in sorted(D.glob("*_H4.csv")):
        sym = f.name[:-7]
        ac = ASSET_CLASS_BY_SYMBOL.get(sym)
        if ac is None:
            continue
        c = float(COST.get(ac, GCOST))
        rows = [(str(r["time"])[:19], float(r["open"]), float(r["high"]),
                 float(r["low"]), float(r["close"]), float(r["volume"]))
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
            is_entry = (trend, posb, relv >= 1.5, bool(swh or swl)) != prev
            prev = (trend, posb, relv >= 1.5, bool(swh or swl))
            if not is_entry:
                continue
            cands = []
            if swl: cands.append(+1)
            if swh: cands.append(-1)
            if relv <= 0.6 and trend == "down" and posb == "low": cands.append(+1)
            if relv <= 0.6 and trend == "up" and posb == "high": cands.append(-1)
            if relv >= 1.8 and expb and posb == "high" and C[i] > O[i]: cands.append(+1)
            if relv >= 1.8 and expb and posb == "low" and C[i] < O[i]: cands.append(-1)
            if absb and posb == "low": cands.append(+1)
            if absb and posb == "high": cands.append(-1)
            if posb == "high" and vdacc < 0: cands.append(-1)
            if posb == "low" and vdacc > 0: cands.append(+1)
            entry = C[i]
            yr = T[i][:4]
            risk = 0.5 * atr  # baseline winning stop = R-unit
            part = "TRAIN" if yr in ("2022", "2023", "2024") else "FORWARD"
            bars = [(Hh[j], L[j]) for j in range(i + 1, min(i + 1 + MAXBARS, n))]
            for d in cands:
                N += 1
                for conv, bug in CONVENTIONS.items():
                    out = simulate(d, entry, risk, c, bars, adv_bug=bug)
                    for m, (net, win, eb) in out.items():
                        for scope in ("ALL", part):
                            a = agg[conv][m][scope]
                            a["n"] += 1; a["tot"] += net; a["win"] += win; a["bars"].append(eb)
                        y = agg[conv][m]["ALL"]["yr"][yr]
                        y["n"] += 1; y["tot"] += net; y["win"] += win

    med = lambda x: round(statistics.median(x), 1) if x else None

    def pack(conv):
        block = {}
        for m in MANAGERS:
            a = agg[conv][m]["ALL"]; tr_ = agg[conv][m]["TRAIN"]; fw = agg[conv][m]["FORWARD"]
            block[m] = {
                "n": a["n"],
                "per_trade_R": round(a["tot"] / a["n"], 4) if a["n"] else None,
                "total_R": round(a["tot"], 0),
                "win": round(a["win"] / a["n"], 3) if a["n"] else None,
                "med_bars_in_trade": med(a["bars"]),
                "TRAIN": {"n": tr_["n"], "per_trade_R": round(tr_["tot"] / tr_["n"], 4) if tr_["n"] else None,
                          "total_R": round(tr_["tot"], 0), "win": round(tr_["win"] / tr_["n"], 3) if tr_["n"] else None},
                "FORWARD": {"n": fw["n"], "per_trade_R": round(fw["tot"] / fw["n"], 4) if fw["n"] else None,
                            "total_R": round(fw["tot"], 0), "win": round(fw["win"] / fw["n"], 3) if fw["n"] else None},
                "per_year": {y: {"n": v["n"], "per_trade_R": round(v["tot"] / v["n"], 4) if v["n"] else None,
                                 "total_R": round(v["tot"], 0), "win": round(v["win"] / v["n"], 3) if v["n"] else None}
                             for y, v in sorted(a["yr"].items())},
            }
        return block

    out = {"schema_version": "study_target_runner_v2", "entries": N,
           "stop": "0.5ATR (R-unit)", "maxbars": MAXBARS,
           "same_bar": "pessimistic (adverse/stop wins same-bar ties)",
           "note": ("Two fill conventions. 'correct' = honest adverse "
                    "(High-entry for shorts). 'baseline_advbug' = reproduces "
                    "structural_geometry_study.py / the confirmed +0.69R "
                    "baseline, which has a SHORT-side adverse sign bug "
                    "(entry-High) so shorts almost never stop out. Exit-"
                    "management RANKING is reported under both for robustness."),
           "conventions": {conv: pack(conv) for conv in CONVENTIONS}}
    (ROUTE / "ULTIMATE_TARGET_RUNNER_STUDY.json").write_text(json.dumps(out, indent=1, sort_keys=True))
    print("entries", N)
    for conv in CONVENTIONS:
        print(f"\n================ CONVENTION: {conv} ================")
        for m, v in out["conventions"][conv].items():
            print(f"\n{m}: per_trade {v['per_trade_R']:+.4f}R  total {v['total_R']:.0f}R  win {v['win']}  med_bars {v['med_bars_in_trade']}")
            print(f"   TRAIN per_trade {v['TRAIN']['per_trade_R']}  win {v['TRAIN']['win']}  |  FORWARD per_trade {v['FORWARD']['per_trade_R']}  win {v['FORWARD']['win']}")
            print("   per_year: " + "  ".join(f"{y}:{pv['per_trade_R']:+.3f}({pv['win']})" for y, pv in v["per_year"].items()))


if __name__ == "__main__":
    main()
