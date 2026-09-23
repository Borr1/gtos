"""p3-3 — THE FLOOR ON EVERY UNFLOORED GENERATOR, and the mechanism in one number.

    python3 .../p3/p3_estate_floor.py

WHY THIS EXISTS SEPARATELY FROM p3-2
-------------------------------------
p3-2 swept k on `asia_pdl_fade` and gated it. That answers "is this sleeve rescuable"
(it is not, and §2 of the result document says so). It does NOT answer the question the
repair actually turns on, which is **"is a stop floor the right default for the four
generators that are missing one"** — a question about four generators and one constant,
not about one sleeve and eight cells.

So this file does two things p3-2 cannot.

1. **THE MECHANISM, AS A SINGLE MEASURED RATIO.** The defect's whole claim is that a
   fixed PRICE cost divided by a coupled PRICE stop makes the broker's cut biggest exactly
   where the setup is cleanest. That is testable directly: `spread / stop_dist`, per trade,
   from the estate's own measured spread model. It is reported by decile of `stop/ATR`, and
   the top-vs-bottom-decile ratio IS the size of the defect. No walk, no gate, no p-value —
   arithmetic on two price numbers.

2. **THE FLOOR AT THE ESTATE'S OWN CONSTANT, ON ALL FOUR.** `ATR_STOP_FLOOR = 0.25` is
   applied to `asia_pdl_fade`, `liq_asia_up_low_metal`, `vol_squeeze` and
   `orb_crypto_london`, and the A/B is measured per sleeve: how many trades it binds on,
   what it does to mean gross R, mean cost R and mean net R. **0.25 is not chosen here.**
   It is read off `metals.py:34` / `metals_ob_micro.py:46` / `structural_retest.py:28`,
   where three earlier sessions put it for the same idiom — so on these four sleeves it is
   an out-of-sample constant, which is the only kind worth defaulting to.

   `orb_crypto_london` is the interesting one: its stop has **no ATR term at all**
   (`orb_crypto_london.py:115`), so a floor there is a new expression rather than a new
   clause. It is included because `a = atr14(bars, i)` is already computed and used at
   `:87-91`, so the floor costs nothing to add and the sleeve is otherwise the purest
   instance of the defect in the estate.

THE ARM CONVENTION IS LANE m3's, FOR ITS REASONS
-------------------------------------------------
Gross R is walked twice: `old` (bar close, the published convention) and `qs_mid` (fill
anchored — `entry_price = close + direction * spread`, lane r1's correction). Cost R is
the broker-true model. Under `qs_mid` the walk already charges the round-trip spread, so
the cost model's spread term is removed and NET is `gross_qs - (commission + swap +
slippage)`. Both are printed; the `old` pair is what every published number for these
sleeves was computed on, and the `qs_mid` pair is what is true.

Offline and pure. Writes one JSON. Changes nothing.
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(REPO))
AD_DIR = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
sys.path.insert(0, str(AD_DIR))

import ad_exit_sweep as AD  # noqa: E402

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.primitives import atr14  # noqa: E402
from src.costs import cost_r as COSTR  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.quote_side import (  # noqa: E402
    BarQuote, SpreadUnavailable, replay_anchor, spread_for,
)

HERE = Path(__file__).resolve().parent
P6 = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
P8 = REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts"
AA_IN = P6 / "AA_ESTATE_TRADES.json.gz"
AK_IN = P8 / "AK_SUPPLY_TRADES.json.gz"
OUT = HERE / "P3_ESTATE_FLOOR_V1.json"

ACCOUNT, SERVER = "FTMO", "FTMO-Server3"
MAXBARS = 80
TF_MINUTES = {15: 15, 16385: 15, 16388: 240, 16408: 1440}

#: THE ESTATE'S OWN CONSTANT. Not chosen here — see the module docstring.
ATR_STOP_FLOOR = 0.25

#: (source artifact, wick expression, ATR buffer, target multiple, target scales with stop)
#: The wick is recomputed from the archive; `buf` and `target_r` are read off the generator.
SLEEVES = {
    "asia_pdl_fade": dict(
        src="AA", buf=0.10, target_r=3.0,
        wick=lambda b, d: (b.c - b.l) if d > 0 else (b.h - b.c),
        site="sleeves/asia_pdl_fade.py:108"),
    "liq_asia_up_low_metal": dict(
        src="AA", buf=0.10, target_r=3.0,
        wick=lambda b, d: (b.c - b.l) if d > 0 else (b.h - b.c),
        site="sleeves/liq_asia_up_low_metal.py:192,205"),
    "vol_squeeze": dict(
        src="AK", buf=0.30, target_r=3.0,
        wick=lambda b, d: max((b.c - b.l) if d > 0 else (b.h - b.c), 0.0),
        site="sleeves/vol_squeeze.py:78,83"),
    "orb_crypto_london": dict(
        src="AA", buf=None, target_r=2.0, wick=None,
        site="sleeves/orb_crypto_london.py:115",
        note="no ATR term in the shipped stop; the floor is measured against the stored "
             "stop directly, which is exactly what the proposed repair would do"),
}


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, int(round(p * (len(xs) - 1)))))]


def main() -> int:
    t0 = time.time()
    print("loading bars ...", flush=True)
    series, index, _ = AD.load_bars()
    costs = AD.load_broker_true_costs(AD.COSTS)
    print(f"  {len(series)} series in {time.time()-t0:.1f}s", flush=True)

    aa = json.load(gzip.open(AA_IN, "rt"))["trades"]
    ak = json.load(gzip.open(AK_IN, "rt"))["trades"]
    src = {"AA": aa, "AK": ak}

    out: dict[str, dict] = {}
    mech: dict[str, dict] = {}

    for sleeve, cfg in SLEEVES.items():
        rows0 = src[cfg["src"]].get(sleeve) or []
        if not rows0:
            print(f"{sleeve}: NO ROWS in {cfg['src']}", flush=True)
            continue
        recs = []
        refusals = collections.Counter()
        for r in rows0:
            tf = int(r["timeframe"])
            key = (r["symbol"], tf)
            if key not in index:
                refusals["no_series"] += 1
                continue
            i = index[key].get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
            if i is None:
                refusals["bar_not_found"] += 1
                continue
            bars, times = series[key]
            if i + 2 >= len(bars):
                refusals["no_room"] += 1
                continue
            a = atr14(bars, i)
            if a <= 0:
                refusals["zero_atr"] += 1
                continue
            d = int(r["direction"])
            sd0 = float(r["sl_distance_price"])
            ivl = dt.timedelta(minutes=TF_MINUTES[tf])
            entry_utc = times[i] + ivl
            try:
                spread = spread_for(r["symbol"], entry_utc, account=ACCOUNT, band="mid")
            except SpreadUnavailable as e:
                refusals[f"spread:{str(e)[:40]}"] += 1
                continue
            recs.append({"r": r, "i": i, "key": key, "a": a, "d": d, "sd0": sd0,
                         "spread": spread, "entry_utc": entry_utc, "tf": tf})

        if not recs:
            continue

        # ---- 1. THE MECHANISM: spread as a fraction of the risk unit ------------------
        rows_sorted = sorted(recs, key=lambda x: x["sd0"] / x["a"])
        k10 = max(1, len(rows_sorted) // 10)
        dec = []
        for dd in range(10):
            lo, hi = dd * k10, (len(rows_sorted) if dd == 9 else (dd + 1) * k10)
            chunk = rows_sorted[lo:hi]
            if not chunk:
                continue
            dec.append({
                "decile": dd + 1, "n": len(chunk),
                "stop_atr_mid": round(chunk[len(chunk) // 2]["sd0"] / chunk[len(chunk) // 2]["a"], 4),
                "mean_spread_over_stop": round(
                    statistics.fmean(x["spread"] / x["sd0"] for x in chunk), 5),
            })
        ratio = (dec[0]["mean_spread_over_stop"] / dec[-1]["mean_spread_over_stop"]
                 if dec and dec[-1]["mean_spread_over_stop"] > 0 else None)
        mech[sleeve] = {
            "n": len(recs),
            "mean_spread_over_stop": round(
                statistics.fmean(x["spread"] / x["sd0"] for x in recs), 5),
            "median_spread_over_stop": round(
                statistics.median(x["spread"] / x["sd0"] for x in recs), 5),
            "p95_spread_over_stop": round(q([x["spread"] / x["sd0"] for x in recs], 0.95), 5),
            "deciles_by_stop_atr": dec,
            "thinnest_over_widest_decile_ratio": (round(ratio, 3) if ratio else None),
            "claim": ("the broker's cut as a fraction of the risk unit, by how thin the stop "
                      "is. The ratio is the defect's size in one number."),
        }

        # ---- 2. THE FLOOR A/B ---------------------------------------------------------
        arms = {}
        for arm in ("old", "qs_mid"):
            for label, floor_on in (("k=0.00", False), (f"k={ATR_STOP_FLOOR:.2f}", True)):
                g, c, net, bound, stops = [], [], [], 0, []
                for x in recs:
                    bars, times = series[x["key"]]
                    i, a, d = x["i"], x["a"], x["d"]
                    sd = x["sd0"]
                    if floor_on and ATR_STOP_FLOOR * a > sd:
                        sd = ATR_STOP_FLOOR * a
                        bound += 1
                    td = cfg["target_r"] * sd
                    anchor = (replay_anchor(bars[i].c, d, x["spread"], BarQuote.BID)
                              if arm == "qs_mid" else None)
                    pr = replay(bars, i, d, stop_dist=sd,
                                policy=ExitPolicy(target_dist=td, maxbars=MAXBARS,
                                                  label=label),
                                times=times, server=SERVER,
                                bar_minutes=TF_MINUTES[x["tf"]], entry_price=anchor)
                    rg = float(winsorize_R(pr.r_gross))
                    hold = (pr.exit_index - i) * TF_MINUTES[x["tf"]] / 60.0
                    try:
                        br = COSTR(x["r"]["symbol"], ACCOUNT, hold,
                                   sl_distance_price=sd,
                                   entry_price=(bars[i].c if anchor is None else anchor),
                                   side=("LONG" if d > 0 else "SHORT"),
                                   entry_utc=x["entry_utc"], costs=costs)
                        # under qs the walk already charges the spread as geometry
                        cr = (float(br.total_r.value) if arm == "old" else
                              float(br.commission_r.value) + float(br.swap_r.value)
                              + float(br.slippage_r.value))
                    except Exception:
                        continue
                    g.append(rg)
                    c.append(cr)
                    net.append(rg - cr)
                    stops.append(sd / a)
                arms[f"{arm}|{label}"] = {
                    "n": len(g), "n_floor_bound": bound,
                    "frac_floor_bound": round(bound / len(recs), 5),
                    "median_stop_atr": round(statistics.median(stops), 5) if stops else None,
                    "mean_gross_r": round(statistics.fmean(g), 6) if g else None,
                    "mean_cost_r": round(statistics.fmean(c), 6) if c else None,
                    "mean_net_r": round(statistics.fmean(net), 6) if net else None,
                }
        deltas = {}
        for arm in ("old", "qs_mid"):
            b = arms[f"{arm}|k=0.00"]
            f = arms[f"{arm}|k={ATR_STOP_FLOOR:.2f}"]
            deltas[arm] = {
                "d_gross_r": round(f["mean_gross_r"] - b["mean_gross_r"], 6),
                "d_cost_r": round(f["mean_cost_r"] - b["mean_cost_r"], 6),
                "d_net_r": round(f["mean_net_r"] - b["mean_net_r"], 6),
                "frac_bound": f["frac_floor_bound"],
            }
        out[sleeve] = {"site": cfg["site"], "note": cfg.get("note"),
                       "source_artifact": cfg["src"], "n_rows_in": len(rows0),
                       "n_priced": len(recs), "refusals": dict(refusals),
                       "arms": arms, "floor_delta": deltas}
        print(f"{sleeve:26s} n={len(recs):5d} bound={deltas['old']['frac_bound']:.4f} "
              f"dNet(old)={deltas['old']['d_net_r']:+.6f} "
              f"dNet(qs_mid)={deltas['qs_mid']['d_net_r']:+.6f} "
              f"spread/stop={mech[sleeve]['mean_spread_over_stop']:.4f} "
              f"thin/wide={mech[sleeve]['thinnest_over_widest_decile_ratio']}", flush=True)

    doc = {
        "schema": "gtos.wave20.p3.estate_floor.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "generated_utc": dt.datetime.now(dt.UTC).isoformat(),
        "atr_stop_floor": ATR_STOP_FLOOR,
        "floor_provenance": [
            "src/components/ultimate_book/sleeves/metals.py:34",
            "src/components/ultimate_book/sleeves/metals_ob_micro.py:46",
            "src/components/ultimate_book/sleeves/structural_retest.py:28",
        ],
        "mechanism": mech,
        "floor_ab": out,
        "arm_convention": {
            "old": "bar close anchored; cost model charges all four terms. The published "
                   "convention for every number these sleeves have ever carried.",
            "qs_mid": "fill anchored (close + direction*spread, band=mid, lane r1); the "
                      "cost model's spread term is dropped because the walk now charges it "
                      "as geometry. Lane m3's arithmetically-right arm.",
        },
        "seconds": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(doc, indent=1))
    print(f"\nwrote {OUT}  ({time.time()-t0:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
