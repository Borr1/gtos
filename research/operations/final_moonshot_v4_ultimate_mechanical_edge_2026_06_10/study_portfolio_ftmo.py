"""Portfolio / FTMO study (dimension: portfolio_ftmo).

Using the CONFIRMED BASELINE GEOMETRY (stop=0.5*ATR, target=2R=1.0*ATR,
first-touch over <=60 bars, pessimistic same-bar with stop winning ties,
minus real per-asset-class cost), this builds the DAILY PORTFOLIO R curve
across all 46 symbols 2022-2026 and answers FTMO sizing.

Each trade contributes its R outcome on the calendar DAY IT RESOLVES (exit
bar's day) -- this is the day the realized P&L hits the prop account, which
is exactly what FTMO 5% daily-loss tracks. (We also report an alternative
attribution by ENTRY day as a robustness cross-check.)

Outputs per year:
  - total realized R
  - mean day R, worst day R, best day R
  - max peak-to-trough drawdown of the cumulative daily-R equity (in R)
  - largest same-day correlated cluster of STOPS (# trades stopped same day)

Then solves: per-trade risk % so that
  - worst single day stays inside FTMO 5% daily loss
  - max peak-to-trough drawdown stays inside FTMO 10% overall
and reports the implied monthly % return at that sizing.
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
STOP_ATR = 0.5      # baseline stop = 0.5*ATR  (R-unit = stop distance)
TARGET_R = 2.0      # baseline target = 2R = 1.0*ATR
FTMO_DAILY = 0.05   # 5% daily loss limit
FTMO_MAX = 0.10     # 10% max overall drawdown


def detect_trades():
    """Yield one dict per fired baseline trade with entry/exit dates and R."""
    trades = []
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
            cur = (trend, posb, relv >= 1.5, bool(swh or swl))
            is_entry = cur != prev
            prev = cur
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
            risk = STOP_ATR * atr           # R-unit = stop distance
            tgt = TARGET_R * risk           # favorable distance to 2R target
            for d in cands:
                # first-touch over <=60 bars, pessimistic same-bar: stop wins ties.
                # We resolve TWICE per trade:
                #   *_recipe : EXACTLY as the shared recipe / structural study wrote it
                #              (adv = d*(entry-L) long / d*(Hh-entry) short)  <- SHORT SIGN BUG
                #   *_fix    : sign-corrected adverse excursion (short stop = Hh-entry >= risk)
                # Primary FTMO numbers use *_recipe for cross-agent consistency; *_fix is the
                # disclosure of what the bug does to the portfolio.
                out_r = None; ebar_r = None
                out_f = None; ebar_f = None
                for j in range(i + 1, min(i + 1 + MAXBARS, n)):
                    fav = (Hh[j] - entry) if d > 0 else (entry - L[j])
                    adv_recipe = (entry - L[j]) if d > 0 else (entry - Hh[j])   # recipe (buggy short)
                    adv_fix = (entry - L[j]) if d > 0 else (Hh[j] - entry)      # corrected short
                    if out_r is None:
                        if adv_recipe >= risk:
                            out_r = -1.0 - c; ebar_r = j
                        elif fav >= tgt:
                            out_r = TARGET_R - c; ebar_r = j
                    if out_f is None:
                        if adv_fix >= risk:
                            out_f = -1.0 - c; ebar_f = j
                        elif fav >= tgt:
                            out_f = TARGET_R - c; ebar_f = j
                    if out_r is not None and out_f is not None:
                        break
                if out_r is None:
                    ebar_r = min(i + MAXBARS, n - 1); out_r = -c
                if out_f is None:
                    ebar_f = min(i + MAXBARS, n - 1); out_f = -c
                trades.append({
                    "sym": sym, "ac": ac, "dir": d,
                    "entry_day": T[i][:10], "exit_day": T[ebar_r][:10],
                    "exit_day_fix": T[ebar_f][:10],
                    "R": out_r, "R_fix": out_f,
                    "stopped": (out_r <= -1.0 - c + 1e-9),
                    "stopped_fix": (out_f <= -1.0 - c + 1e-9),
                    "year": T[ebar_r][:4], "year_fix": T[ebar_f][:4],
                })
    return trades


def equity_dd(daily_sorted_R):
    """Max peak-to-trough drawdown (in R) of the cumulative daily-R equity curve."""
    eq = 0.0; peak = 0.0; max_dd = 0.0
    for _, r in daily_sorted_R:
        eq += r
        if eq > peak:
            peak = eq
        dd = peak - eq
        if dd > max_dd:
            max_dd = dd
    return max_dd


def analyze(trades, attr="exit_day", rkey="R", skey="stopped"):
    by_day = collections.defaultdict(float)
    stops_by_day = collections.defaultdict(int)
    by_year_day = collections.defaultdict(lambda: collections.defaultdict(float))
    for t in trades:
        day = t[attr]
        by_day[day] += t[rkey]
        by_year_day[day[:4]][day] += t[rkey]
        if t[skey]:
            stops_by_day[t[attr]] += 1
    days_sorted = sorted(by_day.items())
    # Overall stats
    all_R = [r for _, r in days_sorted]
    overall = {
        "total_R": round(sum(all_R), 1),
        "n_active_days": len(all_R),
        "mean_day_R": round(statistics.mean(all_R), 4),
        "worst_day_R": round(min(all_R), 2),
        "best_day_R": round(max(all_R), 2),
        "std_day_R": round(statistics.pstdev(all_R), 3) if len(all_R) > 1 else 0.0,
        "max_dd_R": round(equity_dd(days_sorted), 2),
        "max_same_day_stops": max(stops_by_day.values()) if stops_by_day else 0,
    }
    # worst-day / max-cluster details
    worst_day = min(days_sorted, key=lambda kv: kv[1])
    worst_cluster_day = max(stops_by_day.items(), key=lambda kv: kv[1]) if stops_by_day else (None, 0)
    overall["worst_day"] = {"day": worst_day[0], "R": round(worst_day[1], 2)}
    overall["max_cluster_day"] = {"day": worst_cluster_day[0], "stops": worst_cluster_day[1]}
    # Per-year
    per_year = {}
    for yr in sorted(by_year_day.keys()):
        yd = sorted(by_year_day[yr].items())
        yR = [r for _, r in yd]
        ystops = collections.defaultdict(int)
        for t in trades:
            if t[attr][:4] == yr and t[skey]:
                ystops[t[attr]] += 1
        per_year[yr] = {
            "total_R": round(sum(yR), 1),
            "n_days": len(yR),
            "mean_day_R": round(statistics.mean(yR), 4) if yR else 0.0,
            "worst_day_R": round(min(yR), 2) if yR else 0.0,
            "best_day_R": round(max(yR), 2) if yR else 0.0,
            "max_dd_R": round(equity_dd(yd), 2),
            "max_same_day_stops": max(ystops.values()) if ystops else 0,
        }
    return overall, per_year, days_sorted


def solve_sizing(overall):
    """Per-trade risk % so worst day <= 5% and max DD <= 10%.

    Each trade risks p% of equity (1R loss = p%). A day with net D R moves
    equity by D*p%. Constraints:
      worst_day_R * p <= 5%   ->  p <= 5 / |worst_day_R|
      max_dd_R    * p <= 10%  ->  p <= 10 / max_dd_R
    Take the binding (smaller) limit. We also report a buffered (80%) sizing.
    """
    w = abs(overall["worst_day_R"])
    dd = overall["max_dd_R"]
    p_daily = FTMO_DAILY * 100 / w if w > 0 else float("inf")        # in %
    p_dd = FTMO_MAX * 100 / dd if dd > 0 else float("inf")           # in %
    p_max = min(p_daily, p_dd)
    binding = "daily_5pct" if p_daily <= p_dd else "max_dd_10pct"
    p_buf = p_max * 0.8   # 20% safety buffer (slippage, gaps, model drift)
    return {
        "worst_day_R": overall["worst_day_R"],
        "max_dd_R": overall["max_dd_R"],
        "p_limit_daily_5pct": round(p_daily, 4),
        "p_limit_maxdd_10pct": round(p_dd, 4),
        "binding_constraint": binding,
        "per_trade_risk_pct_max": round(p_max, 4),
        "per_trade_risk_pct_buffered_0p8": round(p_buf, 4),
    }


def monthly_return(overall, per_trade_pct, n_months):
    """Implied avg monthly % return at given per-trade risk % (linear R->%)."""
    total_pct = overall["total_R"] * per_trade_pct          # total account % over whole span
    return {
        "total_account_pct_over_span": round(total_pct, 2),
        "n_months_span": n_months,
        "avg_monthly_pct": round(total_pct / n_months, 3) if n_months else None,
    }


def main():
    trades = detect_trades()
    n = len(trades)
    n_stopped = sum(1 for t in trades if t["stopped"])
    n_win = sum(1 for t in trades if t["R"] > 0)
    per_trade_R = round(sum(t["R"] for t in trades) / n, 4) if n else 0.0

    # direction split + sign-corrected per-trade (bug disclosure)
    n_long = sum(1 for t in trades if t["dir"] > 0)
    n_short = n - n_long
    per_trade_R_fix = round(sum(t["R_fix"] for t in trades) / n, 4) if n else 0.0
    win_fix = round(sum(1 for t in trades if t["R_fix"] > 0) / n, 4) if n else 0.0
    short_win_recipe = round(sum(1 for t in trades if t["dir"] < 0 and t["R"] > 0) / n_short, 4) if n_short else 0.0
    short_win_fix = round(sum(1 for t in trades if t["dir"] < 0 and t["R_fix"] > 0) / n_short, 4) if n_short else 0.0

    overall_exit, per_year_exit, days_exit = analyze(trades, "exit_day")
    overall_entry, per_year_entry, _ = analyze(trades, "entry_day")
    # sign-corrected portfolio (what FTMO sizing would be on the real edge)
    overall_fix, per_year_fix, _ = analyze(trades, "exit_day_fix", rkey="R_fix", skey="stopped_fix")

    # span in months (use exit-day extent)
    all_days = sorted(set(t["exit_day"] for t in trades))
    d0, d1 = all_days[0], all_days[-1]
    months = (int(d1[:4]) - int(d0[:4])) * 12 + (int(d1[5:7]) - int(d0[5:7])) + 1

    sizing = solve_sizing(overall_exit)
    mret_max = monthly_return(overall_exit, sizing["per_trade_risk_pct_max"], months)
    mret_buf = monthly_return(overall_exit, sizing["per_trade_risk_pct_buffered_0p8"], months)

    # concurrency: max number of trades open on any calendar day (entry..exit span)
    open_count = collections.defaultdict(int)
    for t in trades:
        # count each active day cheaply via entry/exit endpoints span on calendar days
        from datetime import date
        a = date.fromisoformat(t["entry_day"]); b = date.fromisoformat(t["exit_day"])
        # cap span to keep it cheap; trades resolve <=60 H4 bars (~10 cal days typical)
        cur = a
        while cur <= b:
            open_count[cur.isoformat()] += 1
            cur = cur.fromordinal(cur.toordinal() + 1)
    max_concurrent = max(open_count.values()) if open_count else 0
    mean_concurrent = round(statistics.mean(open_count.values()), 2) if open_count else 0

    # FTMO sizing on the sign-corrected portfolio too
    sizing_fix = solve_sizing(overall_fix) if overall_fix["total_R"] > 0 else None

    out = {
        "schema_version": "study_portfolio_ftmo_v1",
        "geometry": {"stop_atr": STOP_ATR, "target_R": TARGET_R, "maxbars": MAXBARS,
                     "same_bar": "pessimistic_stop_wins_ties", "cost": "real_per_asset_class"},
        "universe_symbols": 46,
        "span": {"first_exit_day": d0, "last_exit_day": d1, "n_months": months},
        "recipe_integrity_flag": {
            "issue": "SHORT-SIDE ADVERSE-EXCURSION SIGN BUG in shared recipe / structural study",
            "detail": "Recipe scores short stop as adv=d*(Hh-entry)=entry-Hh, which is negative when "
                      "price rises against a short, so shorts almost never register a stop. This is the "
                      "sole source of the cited +0.69R/57% baseline.",
            "n_long": n_long, "n_short": n_short,
            "short_win_rate_recipe_buggy": short_win_recipe,
            "short_win_rate_sign_corrected": short_win_fix,
            "per_trade_R_recipe": per_trade_R,
            "per_trade_R_sign_corrected": per_trade_R_fix,
            "win_rate_sign_corrected": win_fix,
            "verdict": "Baseline +0.69R is a backtest artifact; corrected edge is negative. "
                       "All FTMO sizing below the recipe baseline inherits this artifact.",
        },
        "trades": {"n": n, "per_trade_R": per_trade_R,
                   "win_rate": round(n_win / n, 4) if n else 0.0,
                   "stop_rate": round(n_stopped / n, 4) if n else 0.0,
                   "n_stopped": n_stopped, "n_win": n_win,
                   "n_long": n_long, "n_short": n_short},
        "concurrency": {"max_concurrent_open_trades": max_concurrent,
                        "mean_concurrent_open_trades": mean_concurrent},
        "portfolio_by_exit_day": {"overall": overall_exit, "per_year": per_year_exit},
        "portfolio_by_entry_day_xcheck": {"overall": overall_entry, "per_year": per_year_entry},
        "ftmo_sizing": sizing,
        "implied_return_at_max_size": mret_max,
        "implied_return_at_buffered_size": mret_buf,
        "sign_corrected_portfolio": {
            "overall": overall_fix, "per_year": per_year_fix,
            "per_trade_R": per_trade_R_fix,
            "ftmo_sizing": sizing_fix,
            "note": "Edge is negative after sign fix; FTMO sizing is undefined/meaningless "
                    "(no positive expectancy to size).",
        },
    }
    (ROUTE / "ULTIMATE_PORTFOLIO_FTMO_STUDY.json").write_text(json.dumps(out, indent=1, sort_keys=True))

    # ---- console ----
    print(f"trades={n}  per_trade_R={per_trade_R:+.4f}  win={out['trades']['win_rate']:.3f}  stop={out['trades']['stop_rate']:.3f}")
    print(f"span {d0}..{d1} = {months} months | max_concurrent={max_concurrent} mean_concurrent={mean_concurrent}")
    print("\n=== DAILY PORTFOLIO R (attributed by EXIT day) ===")
    o = overall_exit
    print(f"OVERALL total_R={o['total_R']} mean_day={o['mean_day_R']:+.3f} worst_day={o['worst_day_R']} ({o['worst_day']['day']}) best_day={o['best_day_R']} maxDD_R={o['max_dd_R']} max_same_day_stops={o['max_same_day_stops']} ({o['max_cluster_day']['day']})")
    for yr, v in per_year_exit.items():
        print(f"  {yr}: total_R={v['total_R']:>7} mean_day={v['mean_day_R']:+.3f} worst_day={v['worst_day_R']:>6} best_day={v['best_day_R']:>6} maxDD_R={v['max_dd_R']:>6} max_same_day_stops={v['max_same_day_stops']}")
    print("\n=== ENTRY-day attribution (xcheck) ===")
    oe = overall_entry
    print(f"OVERALL total_R={oe['total_R']} mean_day={oe['mean_day_R']:+.3f} worst_day={oe['worst_day_R']} best_day={oe['best_day_R']} maxDD_R={oe['max_dd_R']} max_same_day_stops={oe['max_same_day_stops']}")
    print("\n=== FTMO SIZING ===")
    s = sizing
    print(f"worst_day={s['worst_day_R']}R  maxDD={s['max_dd_R']}R")
    print(f"p_limit from 5% daily = {s['p_limit_daily_5pct']}%/trade ; from 10% maxDD = {s['p_limit_maxdd_10pct']}%/trade")
    print(f"BINDING = {s['binding_constraint']} -> max per-trade risk = {s['per_trade_risk_pct_max']}%  (buffered 0.8x = {s['per_trade_risk_pct_buffered_0p8']}%)")
    print(f"implied avg monthly return @max = {mret_max['avg_monthly_pct']}%  @buffered = {mret_buf['avg_monthly_pct']}%  (total {mret_max['total_account_pct_over_span']}% / {mret_buf['total_account_pct_over_span']}% over {months}mo)")
    print("\n=== RECIPE INTEGRITY FLAG (short-side adverse SIGN BUG) ===")
    print(f"long={n_long} short={n_short} | short_win recipe(buggy)={short_win_recipe} -> sign-corrected={short_win_fix}")
    print(f"per_trade_R recipe={per_trade_R:+.4f}  ->  sign-corrected={per_trade_R_fix:+.4f}  (win {win_fix})")
    of = overall_fix
    print(f"sign-corrected portfolio: total_R={of['total_R']} mean_day={of['mean_day_R']:+.3f} worst_day={of['worst_day_R']} maxDD_R={of['max_dd_R']}")
    print("=> The cited +0.69R/57% baseline is a SHORT-SIDE BACKTEST ARTIFACT; real edge is NEGATIVE.")


if __name__ == "__main__":
    main()
