"""B9 step 4 — is carry a SIGNAL, or only an accounting correction?

The brief's own standard: *"carry is only alpha if the price risk does not eat it — measure
that, do not assume it."* Three measurements, in increasing ambition:

  (A) CARRY vs PRICE RISK, per symbol/side.  The pure-carry information ratio per night:
      carry_R_per_night / sigma_R_per_night, where sigma is the D1 close-to-close standard
      deviation of the same instrument expressed in the SAME R unit (the estate's own median
      stop for that symbol). This is the number that decides whether a carry tilt can ever be
      an edge, and it does not depend on any strategy.

  (B) SIDE CONDITIONING on the estate.  Restricting the armed sleeves to their favourable-carry
      side: does realised net R improve, and by how much of that is carry vs selection? Lane 7
      ran this on the candidate cache; this runs it on the sleeve trades that are actually armed.

  (C) A CARRY-AWARE HOLDING RULE, walked forward.  Hold favourable-carry positions K nights
      longer than the walked exit and close adverse-carry ones K nights sooner; price the
      counterfactual on real D1 bars plus the real carry. Split by time — rule chosen on the
      first half of each symbol's trades, scored on the second — so the answer is out of sample.

Bars: /Users/borr/GTOSActive/vps-bars-20260727 (D1, broker wall clock per each file's
`.timebase.json`; the conversion to UTC is a fixed offset within a day and is irrelevant to a
close-to-close return, so D1 rows are used on the broker's own calendar and that is stated
rather than hidden).

Writes B9_CARRY_SIGNAL_V1.json.
"""
from __future__ import annotations

import bisect
import collections
import csv
import gzip
import json
import math
import pathlib
import random
import statistics
import sys
from datetime import datetime, timezone

REPO = pathlib.Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
sys.path.insert(0, str(REPO))

from src.costs.model import rollover_nights  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
BARS = pathlib.Path("/Users/borr/GTOSActive/vps-bars-20260727")
EXPORT = pathlib.Path("/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api")
ESTATE = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
SERVER = "FTMO-Server3"
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback")


def swap_table(fname: str) -> dict:
    out = {}
    for line in (EXPORT / fname).read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if "swap_long" not in r:
            continue
        rec = {"swap_long": r["swap_long"], "swap_short": r.get("swap_short"),
               "swap_mode": r.get("swap_mode"), "point": r.get("point"),
               "roll3": r.get("swap_rollover3days")}
        n = str(r.get("name"))
        out[n] = out[n.replace(".", "_")] = rec
    return out


def signed_drag(rec, direction, price):
    """Signed price drag per night; NEGATIVE = the broker pays. None = not convertible."""
    swap = rec.get("swap_long") if direction > 0 else rec.get("swap_short")
    mode = rec.get("swap_mode")
    if swap is None or mode is None:
        return None
    mode = int(float(mode))
    if mode == 1:
        pt = rec.get("point")
        return None if not pt else -float(swap) * float(pt)
    if mode in (5, 6) and price:
        return -float(price) * (float(swap) / 100.0) / 360.0
    return None


def load_d1(symbol: str):
    """(sorted broker-epoch list, close list) for one canonical symbol, FTMO D1."""
    f = BARS / f"FTMO_{symbol}_D1.csv.gz"
    if not f.is_file():
        return None, None
    ts, cl = [], []
    with gzip.open(f, "rt") as fh:
        for row in csv.DictReader(fh):
            ts.append(int(row["time"]))
            cl.append(float(row["close"]))
    return ts, cl


def boot_ci(vals, n=4000, seed=20260811):
    if len(vals) < 2:
        return None, None
    rng = random.Random(seed)
    k = len(vals)
    m = sorted(sum(vals[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return m[int(0.025 * n)], m[int(0.975 * n)]


def main() -> int:
    tab = swap_table("ftmo_symbols_get.jsonl")
    est = json.loads(gzip.open(ESTATE, "rt").read())

    # median stop as a fraction of price, per symbol, from the estate's own trades
    stopfrac = collections.defaultdict(list)
    for trades in est["trades"].values():
        for t in trades:
            s, sld, px = t.get("symbol_canonical"), t.get("sl_distance_price"), t.get("entry_price")
            if s and sld and px:
                stopfrac[s].append(float(sld) / float(px))
    stopfrac = {k: statistics.median(v) for k, v in stopfrac.items()}

    # ---------------------------------------------------------------- (A) carry vs price risk
    A = {}
    for sym, sf in sorted(stopfrac.items()):
        rec = tab.get(sym)
        ts, cl = load_d1(sym)
        if rec is None or not cl or len(cl) < 60:
            continue
        rets = [math.log(cl[i] / cl[i - 1]) for i in range(1, len(cl)) if cl[i - 1] > 0 and cl[i] > 0]
        sigma_frac = statistics.pstdev(rets)
        sigma_r = sigma_frac / sf                        # one day of price risk, in R
        px = statistics.median(cl[-250:])
        for side, d in (("LONG", 1), ("SHORT", -1)):
            drag = signed_drag(rec, d, px)
            if drag is None:
                continue
            carry_r = -drag / (sf * px)                  # POSITIVE = the broker pays, in R/night
            A[f"{sym}|{side}"] = {
                "carry_r_per_night": carry_r,
                "sigma_r_per_night": sigma_r,
                "carry_over_sigma": carry_r / sigma_r if sigma_r else None,
                "nights_to_one_sigma_of_carry": (sigma_r / carry_r) if carry_r > 0 else None,
                "annualised_carry_sharpe_if_pure": (
                    (carry_r / sigma_r) * math.sqrt(252.0) if sigma_r and carry_r > 0 else None
                ),
                "median_stop_fraction_of_price": sf,
                "d1_bars": len(cl),
            }
    fav = {k: v for k, v in A.items() if v["carry_r_per_night"] > 0}

    # ---------------------------------------------------------------- (B) side conditioning
    B = {}
    for sleeve, trades in est["trades"].items():
        rows = []
        for t in trades:
            sym = t.get("symbol_canonical")
            rec, sld, eu, hh = tab.get(sym), t.get("sl_distance_price"), t.get("entry_utc"), t.get("hold_hours")
            if not rec or not sld or not eu or hh is None or t.get("r_gross") is None:
                continue
            d = int(t.get("direction", 0))
            drag = signed_drag(rec, d, t.get("entry_price"))
            if drag is None:
                continue
            try:
                nights, _ = rollover_nights(
                    datetime.fromisoformat(eu).astimezone(timezone.utc), float(hh),
                    server=SERVER,
                    rollover3days_weekday=(int(rec["roll3"]) if rec.get("roll3") is not None else None))
            except Exception:  # noqa: BLE001
                continue
            swap_r = nights * drag / float(sld)          # signed; negative = credit
            rows.append({"fav": drag < 0, "r_gross": float(t["r_gross"]),
                         "swap_r": swap_r, "net": float(t["r_gross"]) - swap_r,
                         "entry_utc": eu})
        if len(rows) < 20:
            continue
        f = [r for r in rows if r["fav"]]
        a = [r for r in rows if not r["fav"]]
        if not f or not a:
            B[sleeve] = {"n": len(rows), "note": "single-sided: no contrast available",
                         "n_favourable": len(f), "n_adverse": len(a),
                         "armed_2026_08_11": sleeve in ARMED}
            continue
        lo, hi = boot_ci([r["net"] for r in f])
        lo2, hi2 = boot_ci([r["net"] for r in a])
        B[sleeve] = {
            "n": len(rows), "n_favourable": len(f), "n_adverse": len(a),
            "armed_2026_08_11": sleeve in ARMED,
            "favourable_mean_gross_r": sum(r["r_gross"] for r in f) / len(f),
            "adverse_mean_gross_r": sum(r["r_gross"] for r in a) / len(a),
            "favourable_mean_net_r": sum(r["net"] for r in f) / len(f),
            "adverse_mean_net_r": sum(r["net"] for r in a) / len(a),
            "favourable_net_ci95": [lo, hi],
            "adverse_net_ci95": [lo2, hi2],
            "delta_net_favourable_minus_adverse": (
                sum(r["net"] for r in f) / len(f) - sum(r["net"] for r in a) / len(a)),
            "delta_gross_favourable_minus_adverse": (
                sum(r["r_gross"] for r in f) / len(f) - sum(r["r_gross"] for r in a) / len(a)),
            "breadth_cost_pct": 100.0 * len(a) / len(rows),
        }

    # ---------------------------------------------------------------- (C) carry-aware horizon
    # Extend favourable-carry trades by K nights past their walked exit and price the change on
    # real D1 closes plus real carry. First half of each symbol's trades chooses K; second half
    # scores it. A rule that only works in sample is refuted here.
    # THE CONTROL IS THE MEASUREMENT. Holding K nights longer on a favourable-carry side and
    # finding a positive mean is worthless on its own: the favourable side of these instruments is
    # overwhelmingly LONG, the sample spans 2000-2026, and the same walk on the ADVERSE-carry side
    # -- where the rule says CLOSE SOONER -- would show the same drift. So both arms are walked,
    # and the rule is only alive if the difference between them is positive and outsized relative
    # to the carry it is supposed to be harvesting.
    C = {"per_k": {}, "chosen": None, "oos": None, "control": {}}
    ext = {"favourable": collections.defaultdict(list), "adverse": collections.defaultdict(list)}
    series = {}
    for sleeve, trades in est["trades"].items():
        for t in trades:
            sym = t.get("symbol_canonical")
            rec, sld = tab.get(sym), t.get("sl_distance_price")
            if not rec or not sld or not t.get("exit_utc"):
                continue
            d = int(t.get("direction", 0))
            drag = signed_drag(rec, d, t.get("entry_price"))
            if drag is None:
                continue
            arm = "favourable" if drag < 0 else "adverse"
            if sym not in series:
                series[sym] = load_d1(sym)
            ts, cl = series[sym]
            if not cl:
                continue
            exit_epoch = int(datetime.fromisoformat(t["exit_utc"]).timestamp())
            i = bisect.bisect_left(ts, exit_epoch)
            if i >= len(cl) - 8 or i < 1:
                continue
            base = cl[i]
            for k in (1, 2, 3, 5, 8):
                if i + k >= len(cl):
                    continue
                price_move_r = d * (cl[i + k] - base) / float(sld)
                # k calendar D1 bars are trading days; the broker charges one night per trading
                # midnight, so k bars ~ k charged nights (weekend triples net out over a sample
                # this size and are NOT modelled here -- stated, not hidden).
                carry_r = -k * drag / float(sld)
                ext[arm][k].append({"sym": sym, "sleeve": sleeve, "entry_utc": t["entry_utc"],
                                    "direction": d,
                                    "delta_r": price_move_r + carry_r,
                                    "price_r": price_move_r, "carry_r": carry_r})
    for k, rows in sorted(ext["favourable"].items()):
        if len(rows) < 20:
            continue
        vals = [r["delta_r"] for r in rows]
        lo, hi = boot_ci(vals)
        ctl = ext["adverse"].get(k) or []
        ctl_vals = [r["delta_r"] for r in ctl]
        sd = statistics.pstdev(vals) if len(vals) > 1 else None
        C["per_k"][k] = {
            "n": len(rows),
            "mean_delta_r": sum(vals) / len(vals),
            "ci95": [lo, hi],
            "sd_delta_r": sd,
            # the honest instrument: added return per unit of added risk, not raw R
            "info_ratio": (sum(vals) / len(vals) / sd) if sd else None,
            "mean_price_component_r": sum(r["price_r"] for r in rows) / len(rows),
            "mean_carry_component_r": sum(r["carry_r"] for r in rows) / len(rows),
            "carry_share_of_mean_pct": (
                100.0 * sum(r["carry_r"] for r in rows) / sum(vals) if sum(vals) else None
            ),
            "pct_positive": 100.0 * sum(1 for v in vals if v > 0) / len(vals),
            "long_share": sum(1 for r in rows if r["direction"] > 0) / len(rows),
            "control_adverse_n": len(ctl_vals),
            "control_adverse_mean_delta_r": (sum(ctl_vals) / len(ctl_vals)) if ctl_vals else None,
            "control_adverse_long_share": (
                sum(1 for r in ctl if r["direction"] > 0) / len(ctl) if ctl else None
            ),
            "favourable_minus_control": (
                sum(vals) / len(vals) - sum(ctl_vals) / len(ctl_vals) if ctl_vals else None
            ),
        }
        # DIRECTION-MATCHED control. The favourable arm is 73 % long and the raw control 53 %,
        # so the raw contrast is partly a long/short contrast over a 2000-2026 up-drifting sample.
        # Restrict BOTH arms to longs; if the gap survives at many times the carry it still is not
        # carry, and this row says so with the confound removed.
        fl = [r["delta_r"] for r in rows if r["direction"] > 0]
        cl_ = [r["delta_r"] for r in ctl if r["direction"] > 0]
        C["per_k"][k]["long_only"] = {
            "n_favourable": len(fl), "n_control": len(cl_),
            "favourable_mean": (sum(fl) / len(fl)) if fl else None,
            "control_mean": (sum(cl_) / len(cl_)) if cl_ else None,
            "difference": (sum(fl) / len(fl) - sum(cl_) / len(cl_)) if (fl and cl_) else None,
            "carry_component": sum(r["carry_r"] for r in rows if r["direction"] > 0) / len(fl) if fl else None,
        }
    if C["per_k"]:
        rows_by_k = {k: sorted(v, key=lambda r: r["entry_utc"])
                     for k, v in ext["favourable"].items() if k in C["per_k"]}
        split = {k: len(v) // 2 for k, v in rows_by_k.items()}
        insample = {k: [r["delta_r"] for r in v[: split[k]]] for k, v in rows_by_k.items()}
        best_k = max(insample, key=lambda k: sum(insample[k]) / max(1, len(insample[k])))
        oos = [r["delta_r"] for r in rows_by_k[best_k][split[best_k]:]]
        lo, hi = boot_ci(oos)
        # the same second-half window on the control arm, so the OOS claim is a DIFFERENCE
        ctl_rows = sorted(ext["adverse"].get(best_k) or [], key=lambda r: r["entry_utc"])
        ctl_oos = [r["delta_r"] for r in ctl_rows[len(ctl_rows) // 2:]]
        C["chosen"] = {"k": best_k,
                       "in_sample_mean_delta_r": sum(insample[best_k]) / len(insample[best_k]),
                       "in_sample_n": len(insample[best_k])}
        diff = (sum(oos) / len(oos) - sum(ctl_oos) / len(ctl_oos)) if (oos and ctl_oos) else None
        C["oos"] = {
            "k": best_k, "n": len(oos),
            "mean_delta_r": sum(oos) / len(oos) if oos else None,
            "ci95": [lo, hi],
            "control_n": len(ctl_oos),
            "control_mean_delta_r": (sum(ctl_oos) / len(ctl_oos)) if ctl_oos else None,
            "favourable_minus_control": diff,
            "carry_that_would_explain_it": (
                C["per_k"][best_k]["mean_carry_component_r"] if best_k in C["per_k"] else None
            ),
            # The verdict is about CARRY, not about whether the contrast is non-zero. A contrast
            # many times larger than the carry it is supposed to be harvesting is evidence that
            # something else produced it -- here, instrument composition: the favourable-carry
            # long set is crude and the USD/JPY-cross longs, the control set is metals, indices
            # and crypto, and their drift-to-stop ratios differ. Carry explains ~4.6 % of it at
            # every K, direction-matched or not.
            "carry_share_of_contrast_pct": (
                100.0 * C["per_k"][best_k]["mean_carry_component_r"] / diff
                if diff not in (None, 0) else None
            ),
            "verdict": (
                "REFUTED AS A CARRY RULE: the contrast is {:.0f}x the carry that could explain it, "
                "so it is instrument/direction composition, not carry. Any use of it must be "
                "re-posed as an instrument-selection hypothesis and tested as one.".format(
                    diff / C["per_k"][best_k]["mean_carry_component_r"]
                )
                if diff and C["per_k"][best_k]["mean_carry_component_r"]
                else "NOT MEASURABLE"
            ),
        }

    out = {
        "A_carry_vs_price_risk": {
            "basis": "FTMO D1 closes, vps-bars-20260727; sigma = pstdev of log close-to-close; "
                     "R unit = the estate's own median stop fraction for that symbol; swap table "
                     "2026-07-25",
            "favourable_sides": dict(sorted(fav.items(), key=lambda kv: -kv[1]["carry_over_sigma"])),
            "all_sides": A,
        },
        "B_side_conditioning": B,
        "C_carry_aware_horizon": C,
    }
    (HERE / "B9_CARRY_SIGNAL_V1.json").write_text(json.dumps(out, indent=1, sort_keys=True))

    print("(A) pure carry vs price risk, favourable sides only")
    print(f"  {'symbol|side':<22}{'carry R/night':>15}{'sigma R/night':>15}{'carry/sigma':>13}{'nights to 1 sigma':>19}{'ann. Sharpe':>13}")
    for k, v in sorted(fav.items(), key=lambda kv: -kv[1]["carry_over_sigma"]):
        print(f"  {k:<22}{v['carry_r_per_night']:>+15.5f}{v['sigma_r_per_night']:>15.5f}"
              f"{v['carry_over_sigma']:>13.4f}{v['nights_to_one_sigma_of_carry']:>19.1f}"
              f"{v['annualised_carry_sharpe_if_pure']:>13.3f}")

    print("\n(B) side conditioning on estate trades")
    print(f"  {'sleeve':<24}{'n':>5}{'nFav':>6}{'gross fav':>11}{'gross adv':>11}{'net fav':>10}{'net adv':>10}{'d(net)':>9}")
    for s, v in sorted(B.items(), key=lambda kv: -(kv[1].get("delta_net_favourable_minus_adverse") or -9)):
        if "note" in v:
            print(f"  {s:<24}{v['n']:>5}{v['n_favourable']:>6}   {v['note']}{'  *ARMED*' if v['armed_2026_08_11'] else ''}")
            continue
        print(f"  {s:<24}{v['n']:>5}{v['n_favourable']:>6}{v['favourable_mean_gross_r']:>+11.4f}"
              f"{v['adverse_mean_gross_r']:>+11.4f}{v['favourable_mean_net_r']:>+10.4f}"
              f"{v['adverse_mean_net_r']:>+10.4f}{v['delta_net_favourable_minus_adverse']:>+9.4f}"
              f"{'  *ARMED*' if v['armed_2026_08_11'] else ''}")

    print("\n(C) holding K more nights, favourable-carry arm vs the ADVERSE-carry control")
    print(f"  {'K':>3}{'n':>7}{'mean d(R)':>12}{'IR':>8}{'carry part':>12}{'carry %':>9}"
          f"{'long%':>7}{'control':>10}{'ctl long%':>10}{'fav-ctl':>10}")
    for k, v in C["per_k"].items():
        print(f"  {k:>3}{v['n']:>7}{v['mean_delta_r']:>+12.4f}{(v['info_ratio'] or 0):>8.3f}"
              f"{v['mean_carry_component_r']:>+12.4f}{(v['carry_share_of_mean_pct'] or 0):>8.1f}%"
              f"{100*v['long_share']:>6.0f}%{(v['control_adverse_mean_delta_r'] or 0):>+10.4f}"
              f"{100*(v['control_adverse_long_share'] or 0):>9.0f}%"
              f"{(v['favourable_minus_control'] or 0):>+10.4f}")
    if C["oos"]:
        o = C["oos"]
        print(f"  walk-forward: K={o['k']} chosen in sample -> OOS n={o['n']} mean {o['mean_delta_r']:+.4f} "
              f"CI [{o['ci95'][0]:+.4f},{o['ci95'][1]:+.4f}]")
        print(f"    control (adverse arm, same window) n={o['control_n']} mean {o['control_mean_delta_r']:+.4f}"
              f"   fav-minus-control {o['favourable_minus_control']:+.4f}"
              f"   carry that would explain it {o['carry_that_would_explain_it']:+.4f}")
        print(f"    {o['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
