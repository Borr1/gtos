"""M1 intrabar realism check of the baseline winning geometry.

THE QUESTION
------------
The confirmed baseline edge (+0.69R/trade, ~57% win, positive every year) uses a
0.5*ATR(H4) stop and a 2R (=1.0*ATR) target, resolved by FIRST-TOUCH over <=60
H4 bars with a pessimistic same-bar tie (stop wins). But a 0.5*ATR(H4) stop is
SUB-BAR-RANGE: it is smaller than the typical H4 bar's high-low span. So an H4
bar that "reaches the target" may, intrabar, have first dipped to the tight stop
and only later run to target. H4 bar-level first-touch can therefore UNDERSTATE
stop hits and OVERSTATE the edge.

This study re-resolves the SAME geometry at M1 resolution. For every H4 entry in
the M1-covered window (2025-06 .. 2026-06) we:
  1. detect entries with the shared recipe (identical to structural_geometry_study),
  2. compute H4 bar-level first-touch outcome (the reference number), and
  3. walk the actual M1 path after the H4 entry bar's close and record whether the
     0.5ATR stop or the 1.0ATR target is touched FIRST at 1-minute resolution.

We then compare M1-resolved win-rate and per-trade R to the H4 bar-level numbers,
per year and per asset class, and quantify the degradation. Same-bar ambiguity is
handled three ways to BOUND the effect:
  - pessimistic (stop wins same-minute ties)  <- primary, matches baseline posture
  - optimistic  (target wins same-minute ties)
  - midpoint    (count same-minute double-touch as 0.5 win / 0.5 loss)

Costs: real per-asset-class cost from ULTIMATE_REAL_COST_MAP.json (R-units),
subtracted from every closed trade exactly as the baseline does.

Output: ULTIMATE_M1_INTRABAR_REALISM.json + console summary.
"""
import csv, json, statistics, sys, collections, bisect
from pathlib import Path
from datetime import datetime, timedelta

ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

COST = json.loads((ROUTE / "ULTIMATE_REAL_COST_MAP.json").read_text())
GCOST = COST.get("_global_median", 0.0953)

H4_DIR = REPO_ROOT / "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
M1_BASE = REPO_ROOT / "data/mt5_research_exports"

# Baseline winning geometry (confirmed): stop=0.5*ATR, target=2R=1.0*ATR
STOP_ATR = 0.5
TARGET_R = 2.0          # in risk units; absolute target = TARGET_R*STOP_ATR*ATR = 1.0*ATR
MAXBARS_H4 = 60         # <=60 H4 bars horizon
M1_PER_H4 = 240         # 4h * 60min
MAX_M1 = MAXBARS_H4 * M1_PER_H4   # 14400 minutes horizon (same wall-clock as 60 H4 bars)

# M1 covered window: union of std + ext monthly dirs, 2025-06 .. 2026-06
M1_MONTHS = ["202506", "202507", "202508", "202509", "202510", "202511", "202512",
             "202601", "202602", "202603", "202604", "202605", "202606"]

FMT = "%Y-%m-%d %H:%M:%S"


def load_h4(path):
    rows = []
    for r in csv.DictReader(open(path)):
        if not (r.get("close") and r.get("volume")):
            continue
        rows.append((str(r["time"])[:19], float(r["open"]), float(r["high"]),
                     float(r["low"]), float(r["close"]), float(r["volume"])))
    return rows


def load_m1(sym):
    """Load and concatenate M1 across all monthly dirs (std + ext). Returns sorted
    parallel arrays (epoch_seconds, high, low). De-dups by timestamp."""
    seen = {}
    for mon in M1_MONTHS:
        for sub in (f"bridge_ftmo_m1_{mon}", f"bridge_ftmo_ext_m1_{mon}"):
            p = M1_BASE / sub / f"{sym}_M1.csv"
            if not p.exists():
                continue
            for r in csv.DictReader(open(p)):
                t = r.get("time")
                h = r.get("high"); lo = r.get("low")
                if not (t and h and lo):
                    continue
                ts = str(t)[:19]
                if ts in seen:
                    continue
                try:
                    ep = int(datetime.strptime(ts, FMT).timestamp())
                    seen[ts] = (ep, float(h), float(lo))
                except Exception:
                    continue
    arr = sorted(seen.values())
    ts = [x[0] for x in arr]
    hi = [x[1] for x in arr]
    lo = [x[2] for x in arr]
    return ts, hi, lo


def h4_entry_close_epoch(time_str):
    """H4 bar timestamp T covers [T, T+4h). Entry at H4 close == T+4h.
    Forward first-touch walk begins at the first M1 bar with ts >= T+4h."""
    dt = datetime.strptime(time_str, FMT) + timedelta(hours=4)
    return int(dt.timestamp())


def main():
    # Per (year, ac, mode) accumulators. mode in {h4, h4_opt, m1_pess, m1_opt, m1_mid}
    #   h4      = H4 bar-level first-touch, PESSIMISTIC same-bar (stop wins ties) -> baseline posture
    #   h4_opt  = H4 bar-level first-touch, OPTIMISTIC same-bar (target wins ties) -> upper H4 bound
    classes = ["h4", "h4_opt", "m1_pess", "m1_opt", "m1_mid"]
    # long/short split (correct stop logic both directions) to expose the structural-study bug
    side = {c: {"long": {"n": 0, "win": 0.0, "R": 0.0}, "short": {"n": 0, "win": 0.0, "R": 0.0}}
            for c in ("h4", "m1_pess")}
    # aggregate buckets
    by_year = {c: collections.defaultdict(lambda: {"n": 0, "win": 0.0, "R": 0.0,
                                                   "open": 0, "stop": 0, "tgt": 0,
                                                   "same_bar": 0}) for c in classes}
    by_ac = {c: collections.defaultdict(lambda: {"n": 0, "win": 0.0, "R": 0.0}) for c in classes}
    overall = {c: {"n": 0, "win": 0.0, "R": 0.0, "open": 0, "same_bar_double": 0} for c in classes}
    # M1 path diagnostics
    diag = {"m1_minutes_to_stop": [], "m1_minutes_to_tgt": [],
            "h4_says_win_m1_says_loss": 0, "h4_says_loss_m1_says_win": 0,
            "agree_win": 0, "agree_loss": 0, "agree_open": 0,
            "entries_total": 0, "entries_with_m1": 0, "entries_no_m1_path": 0}
    skipped_no_m1 = collections.Counter()

    for f in sorted(H4_DIR.glob("*_H4.csv")):
        sym = f.name[:-7]
        ac = ASSET_CLASS_BY_SYMBOL.get(sym)
        if ac is None:
            continue
        c = float(COST.get(ac, GCOST))
        rows = load_h4(f)
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

        # Only load M1 if this symbol has any entry in window (load once)
        m1ts = m1hi = m1lo = None

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
            if not cands:
                continue

            entry = C[i]
            yr = T[i][:4]
            # Restrict to entries whose forward walk lives in the M1-covered window.
            # M1 starts 2025-06-02; require entry close on/after 2025-06-03 to have a path.
            entry_close_ep = h4_entry_close_epoch(T[i])
            if entry_close_ep < int(datetime(2025, 6, 3).timestamp()):
                continue

            risk = STOP_ATR * atr           # absolute stop distance
            tgt_dist = TARGET_R * risk      # = 1.0*ATR absolute favorable distance

            for d in cands:
                diag["entries_total"] += 1
                # ---- H4 bar-level first-touch (reference), pessimistic same-bar ----
                if d > 0:
                    stop_px = entry - risk; tgt_px = entry + tgt_dist
                else:
                    stop_px = entry + risk; tgt_px = entry - tgt_dist
                h4_out = None       # pessimistic same-bar (baseline posture)
                h4_opt_out = None   # optimistic same-bar (target wins ties) -> upper H4 bound
                for j in range(i + 1, min(i + MAXBARS_H4 + 1, n)):
                    hit_stop = (L[j] <= stop_px) if d > 0 else (Hh[j] >= stop_px)
                    hit_tgt = (Hh[j] >= tgt_px) if d > 0 else (L[j] <= tgt_px)
                    if hit_stop and hit_tgt:
                        if h4_out is None:
                            h4_out = "loss"        # pessimistic: stop wins ties
                        if h4_opt_out is None:
                            h4_opt_out = "win"     # optimistic: target wins ties
                        break
                    if hit_stop:
                        if h4_out is None: h4_out = "loss"
                        if h4_opt_out is None: h4_opt_out = "loss"
                        break
                    if hit_tgt:
                        if h4_out is None: h4_out = "win"
                        if h4_opt_out is None: h4_opt_out = "win"
                        break
                if h4_out is None:
                    h4_out = "open"
                if h4_opt_out is None:
                    h4_opt_out = "open"

                # ---- M1-resolved first-touch ----
                if m1ts is None:
                    m1ts, m1hi, m1lo = load_m1(sym)
                # find first M1 bar with ts >= entry_close_ep
                start = bisect.bisect_left(m1ts, entry_close_ep)
                m1_pess = m1_opt = m1_mid = None
                mins_to_stop = mins_to_tgt = None
                if start >= len(m1ts):
                    diag["entries_no_m1_path"] += 1
                    skipped_no_m1[sym] += 1
                else:
                    diag["entries_with_m1"] += 1
                    end = min(start + MAX_M1, len(m1ts))
                    horizon_end_ep = entry_close_ep + MAX_M1 * 60
                    for k in range(start, end):
                        if m1ts[k] >= horizon_end_ep:
                            break
                        H = m1hi[k]; Lk = m1lo[k]
                        hit_stop = (Lk <= stop_px) if d > 0 else (H >= stop_px)
                        hit_tgt = (H >= tgt_px) if d > 0 else (Lk <= tgt_px)
                        mins = (m1ts[k] - entry_close_ep) // 60
                        if hit_stop and hit_tgt:
                            # same-minute double touch: ambiguous at 1-min
                            m1_pess = "loss"; m1_opt = "win"; m1_mid = "half"
                            mins_to_stop = mins; mins_to_tgt = mins
                            overall["m1_pess"]["same_bar_double"] += 1
                            break
                        if hit_stop:
                            m1_pess = m1_opt = m1_mid = "loss"
                            mins_to_stop = mins
                            break
                        if hit_tgt:
                            m1_pess = m1_opt = m1_mid = "win"
                            mins_to_tgt = mins
                            break
                    if m1_pess is None:
                        m1_pess = m1_opt = m1_mid = "open"

                # ---- record outcomes ----
                def rec(mode, out):
                    a_y = by_year[mode][yr]; a_c = by_ac[mode][ac]; a_o = overall[mode]
                    for bucket in (a_y, a_c, a_o):
                        bucket["n"] += 1
                    if out == "win":
                        R = TARGET_R - c
                        for bucket in (a_y, a_c, a_o):
                            bucket["win"] += 1; bucket["R"] += R
                        a_y["tgt"] += 1
                    elif out == "loss":
                        R = -1.0 - c
                        for bucket in (a_y, a_c, a_o):
                            bucket["R"] += R
                        a_y["stop"] += 1
                    elif out == "half":
                        # midpoint: 0.5 win + 0.5 loss, cost once
                        R = 0.5 * TARGET_R + 0.5 * (-1.0) - c
                        for bucket in (a_y, a_c, a_o):
                            bucket["win"] += 0.5; bucket["R"] += R
                    else:  # open -> closed at horizon at -cost (no MTM, baseline drops it as -c)
                        R = -c
                        for bucket in (a_y, a_c, a_o):
                            bucket["R"] += R
                        a_y["open"] += 1
                        a_o["open"] += 1

                def rec_side(mode, out):
                    sd_ = "long" if d > 0 else "short"
                    b = side[mode][sd_]; b["n"] += 1
                    if out == "win":
                        b["win"] += 1; b["R"] += TARGET_R - c
                    elif out == "loss":
                        b["R"] += -1.0 - c
                    elif out == "half":
                        b["win"] += 0.5; b["R"] += 0.5 * TARGET_R + 0.5 * (-1.0) - c
                    else:
                        b["R"] += -c

                rec("h4", h4_out)
                rec("h4_opt", h4_opt_out)
                rec_side("h4", h4_out)
                # only credit M1 modes when an M1 path existed; else mirror nothing
                if start < len(m1ts):
                    rec("m1_pess", m1_pess)
                    rec_side("m1_pess", m1_pess if m1_pess != "half" else "loss")
                    rec("m1_opt", m1_opt)
                    rec("m1_mid", m1_mid)
                    # diagnostics on agreement (compare H4 pess vs M1 pess)
                    if mins_to_stop is not None:
                        diag["m1_minutes_to_stop"].append(mins_to_stop)
                    if mins_to_tgt is not None:
                        diag["m1_minutes_to_tgt"].append(mins_to_tgt)
                    hp = h4_out
                    mp = m1_pess if m1_pess != "half" else "loss"  # pess treats half as loss
                    if hp == "win" and mp == "loss":
                        diag["h4_says_win_m1_says_loss"] += 1
                    elif hp == "loss" and mp == "win":
                        diag["h4_says_loss_m1_says_win"] += 1
                    elif hp == "win" and mp == "win":
                        diag["agree_win"] += 1
                    elif hp == "loss" and mp == "loss":
                        diag["agree_loss"] += 1
                    elif hp == "open" and mp == "open":
                        diag["agree_open"] += 1

    # ---- assemble report ----
    def summarize(mode):
        a = overall[mode]
        n = a["n"]
        return {
            "n": n,
            "win_rate": round(a["win"] / n, 4) if n else None,
            "per_trade_R": round(a["R"] / n, 4) if n else None,
            "total_R": round(a["R"], 1),
            "open_at_horizon": a["open"],
        }

    def per_year(mode):
        out = {}
        for y, a in sorted(by_year[mode].items()):
            nn = a["n"]
            out[y] = {"n": nn,
                      "win_rate": round(a["win"] / nn, 4) if nn else None,
                      "per_trade_R": round(a["R"] / nn, 4) if nn else None,
                      "stop": a["stop"], "tgt": a["tgt"], "open": a["open"]}
        return out

    def per_ac(mode):
        out = {}
        for k, a in sorted(by_ac[mode].items()):
            nn = a["n"]
            out[k] = {"n": nn,
                      "win_rate": round(a["win"] / nn, 4) if nn else None,
                      "per_trade_R": round(a["R"] / nn, 4) if nn else None}
        return out

    med = lambda x: round(statistics.median(x), 1) if x else None
    mean = lambda x: round(statistics.mean(x), 1) if x else None

    h4o = summarize("h4"); mpo = summarize("m1_pess")
    degr_pt = (mpo["per_trade_R"] - h4o["per_trade_R"]) if (h4o["per_trade_R"] is not None and mpo["per_trade_R"] is not None) else None
    degr_win = (mpo["win_rate"] - h4o["win_rate"]) if (h4o["win_rate"] is not None and mpo["win_rate"] is not None) else None

    report = {
        "schema_version": "m1_intrabar_realism_v1",
        "question": "Does +0.69R baseline geometry (0.5ATR stop, 2R target) survive M1 intrabar ordering?",
        "geometry": {"stop_atr": STOP_ATR, "target_R": TARGET_R, "abs_target_atr": STOP_ATR * TARGET_R,
                     "h4_horizon_bars": MAXBARS_H4, "m1_horizon_minutes": MAX_M1,
                     "same_bar_rule_baseline": "pessimistic (stop wins ties)"},
        "window": "2025-06-03 .. 2026-06-09 (M1-covered)",
        "cost_map": {k: v for k, v in COST.items() if not k.startswith("_n")},
        "overall": {
            "h4_bar_level_pessimistic": h4o,
            "h4_bar_level_optimistic": summarize("h4_opt"),
            "m1_pessimistic": mpo,
            "m1_optimistic": summarize("m1_opt"),
            "m1_midpoint": summarize("m1_mid"),
        },
        "long_short_split_correct_stops": {
            mode: {sd_: {"n": side[mode][sd_]["n"],
                        "win_rate": round(side[mode][sd_]["win"] / side[mode][sd_]["n"], 4) if side[mode][sd_]["n"] else None,
                        "per_trade_R": round(side[mode][sd_]["R"] / side[mode][sd_]["n"], 4) if side[mode][sd_]["n"] else None}
                   for sd_ in ("long", "short")}
            for mode in ("h4", "m1_pess")
        },
        "RECONCILIATION_NOTE": (
            "The claimed +0.69R/57%-win baseline (structural_geometry_study.py atr05/TP2.0) is an "
            "ARTIFACT of a sign bug: for SHORT trades that script computes adv=d*(entry-L[j]) with d=-1, "
            "i.e. adv=entry-Hh[j] which is <=0, so the stop condition adv>=risk NEVER fires on shorts. "
            "Shorts are therefore never stopped and inflate the win rate. This study applies the stop "
            "correctly to BOTH directions via explicit price levels (stop_px/tgt_px). With correct stops "
            "the SAME 0.5ATR/2R geometry is ~33% win and NEGATIVE expectancy at H4 bar level "
            "(2:1 payoff needs >33.3% win just to break even before cost). The M1 intrabar check is run "
            "against the CORRECT H4 resolution."
        ),
        "degradation_pess_vs_h4": {
            "per_trade_R_delta": round(degr_pt, 4) if degr_pt is not None else None,
            "per_trade_R_pct": round(100 * degr_pt / h4o["per_trade_R"], 1) if (degr_pt is not None and h4o["per_trade_R"]) else None,
            "win_rate_delta": round(degr_win, 4) if degr_win is not None else None,
        },
        "per_year": {
            "h4_bar_level": per_year("h4"),
            "m1_pessimistic": per_year("m1_pess"),
            "m1_optimistic": per_year("m1_opt"),
        },
        "per_asset_class": {
            "h4_bar_level": per_ac("h4"),
            "m1_pessimistic": per_ac("m1_pess"),
        },
        "m1_path_diagnostics": {
            "entries_total": diag["entries_total"],
            "entries_with_m1_path": diag["entries_with_m1"],
            "entries_no_m1_path": diag["entries_no_m1_path"],
            "agree_win": diag["agree_win"],
            "agree_loss": diag["agree_loss"],
            "agree_open": diag["agree_open"],
            "h4_win_BUT_m1_loss": diag["h4_says_win_m1_says_loss"],
            "h4_loss_BUT_m1_win": diag["h4_says_loss_m1_says_win"],
            "median_minutes_to_stop": med(diag["m1_minutes_to_stop"]),
            "median_minutes_to_tgt": med(diag["m1_minutes_to_tgt"]),
            "mean_minutes_to_stop": mean(diag["m1_minutes_to_stop"]),
            "mean_minutes_to_tgt": mean(diag["m1_minutes_to_tgt"]),
        },
    }
    (ROUTE / "ULTIMATE_M1_INTRABAR_REALISM.json").write_text(json.dumps(report, indent=1, sort_keys=True))

    # ---- console ----
    print("=" * 78)
    print("M1 INTRABAR REALISM CHECK — baseline geometry 0.5ATR stop / 2R target")
    print("=" * 78)
    print(f"window: {report['window']}   entries scored: {h4o['n']}")
    print()
    print(f"{'mode':<22}{'n':>7}{'win_rate':>11}{'per_trade_R':>14}{'total_R':>11}{'open':>7}")
    for label, key in [("H4 pess (baseline)", "h4_bar_level_pessimistic"),
                       ("H4 optimistic", "h4_bar_level_optimistic"),
                       ("M1 pessimistic", "m1_pessimistic"),
                       ("M1 optimistic", "m1_optimistic"), ("M1 midpoint", "m1_midpoint")]:
        s = report["overall"][key]
        print(f"{label:<22}{s['n']:>7}{s['win_rate']:>11}{s['per_trade_R']:>14}{s['total_R']:>11}{s['open_at_horizon']:>7}")
    print()
    dg = report["degradation_pess_vs_h4"]
    print(f"M1 vs H4 DELTA (pess): per_trade_R {dg['per_trade_R_delta']:+} R "
          f"({dg['per_trade_R_pct']}%)   win_rate {dg['win_rate_delta']:+}  "
          f"(NOTE: positive => M1 BETTER than H4, not worse)")
    print()
    print("LONG vs SHORT (correct stops, exposes structural-study sign bug):")
    for mode in ("h4", "m1_pess"):
        ls = report["long_short_split_correct_stops"][mode]
        print(f"  {mode:<8} long: n={ls['long']['n']} win={ls['long']['win_rate']} R={ls['long']['per_trade_R']}"
              f"   short: n={ls['short']['n']} win={ls['short']['win_rate']} R={ls['short']['per_trade_R']}")
    print("  -> structural_geometry_study.py disabled stops on shorts (adv sign bug) => fake high short win-rate")
    print()
    print("PER YEAR (H4 bar-level -> M1 pessimistic):")
    yrs = sorted(set(report["per_year"]["h4_bar_level"]) | set(report["per_year"]["m1_pessimistic"]))
    for y in yrs:
        h = report["per_year"]["h4_bar_level"].get(y, {})
        m = report["per_year"]["m1_pessimistic"].get(y, {})
        print(f"  {y}: n={h.get('n')}  H4 win={h.get('win_rate')} R={h.get('per_trade_R')}  "
              f"->  M1 win={m.get('win_rate')} R={m.get('per_trade_R')}")
    print()
    print("PER ASSET CLASS (H4 -> M1 pess per_trade_R):")
    for k in sorted(report["per_asset_class"]["h4_bar_level"]):
        h = report["per_asset_class"]["h4_bar_level"][k]
        m = report["per_asset_class"]["m1_pessimistic"].get(k, {})
        print(f"  {k:<8} n={h['n']:>5}  H4 R={h['per_trade_R']:+.3f}  ->  M1 R={m.get('per_trade_R')}  "
              f"(H4 win {h['win_rate']} -> M1 win {m.get('win_rate')})")
    print()
    d = report["m1_path_diagnostics"]
    print("M1 PATH DIAGNOSTICS:")
    print(f"  agree win/loss/open: {d['agree_win']}/{d['agree_loss']}/{d['agree_open']}")
    print(f"  H4 WIN but M1 LOSS (intrabar stop-then-target): {d['h4_win_BUT_m1_loss']}")
    print(f"  H4 LOSS but M1 WIN: {d['h4_loss_BUT_m1_win']}")
    print(f"  median minutes to stop: {d['median_minutes_to_stop']}  to target: {d['median_minutes_to_tgt']}")
    print()
    print("wrote ULTIMATE_M1_INTRABAR_REALISM.json")


if __name__ == "__main__":
    main()
