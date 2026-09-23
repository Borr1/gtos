"""p3-4 — WOULD THE LIVE BOOK EVEN PLACE IT? Every wick-stop sleeve against the send gate.

    python3 .../p3/p3_sendgate.py

THE QUESTION NO ARTIFACT IN THIS ESTATE HAS ASKED
--------------------------------------------------
Every economic number this programme publishes for a sleeve is computed on a walk. The live
book does not place from a walk; it places through a pre-trade cost gate that refuses on a
ratio the walk never computes:

    spread_r = (ask - bid) / sl_distance_price  >  selected_cell_pretrade_max_spread_r

`broker_net_cost_engine.py:689-690` reads the limit (and its per-sleeve override map);
`book_owner.py:4700` defaults it to **0.10** when the key is absent; `spread_geometry.py:88`
carries the same 0.10 as `SPREAD_GEOMETRY_FLOOR_DEFAULT_LIMIT` for exactly the reason that
"if the config key is ever absent, both layers must fall back to the same number".
`spread_geometry.py:30-31` records it FIRING in production: 136 legs in the read-only
2026-07-25 VPS export's own launcher log, at observed `spread_r` up to 16.543.

So a sleeve can carry a positive published expectancy and still be a sleeve the live book
would decline to place, and nothing in `SLEEVE_DOSSIER_V1.json`, `AK_EXIT_FRONTIER_V2.json`
or `SLEEVE_FORENSIC_V1.json` records which. **That is the gap this file closes**, and it is
the second-order half of the p3 finding: the stop-coupling defect does not only make the
broker's cut large, it makes it large enough to cross a refusal threshold the estate
already owns and already enforces.

WHAT IS MEASURED
----------------
Every sleeve with rows in AA's estate walk (32) plus AK's four supply sleeves, whole
populations, no sampling. For each trade: the modelled quoted spread at the entry instant
(`walkforward.quote_side.spread_for`, band mid — the estate's era-aware measured model,
which is the same object lane r1's walker correction uses) divided by the stored stop
distance. Then:

  frac_refused_at_0p10   the share of the sleeve's own history the send gate would refuse
  median / mean / p95    the distribution
  k_needed_for_median    the ATR floor that would drag the MEDIAN under the limit, i.e.
                         `median(spread_r) / limit * median(stop_atr)` — reported because
                         it is the honest answer to "could the p3 repair fix this", and on
                         two sleeves the answer it gives is absurd on its face

CAVEAT, STATED BECAUSE IT CUTS BOTH WAYS
-----------------------------------------
`spread_for` is a MODEL — a tick-measured anchor times a bar-measured era ratio (Session AG)
— not the tick the book will actually read. On deep history it is the only defensible
source; on 2026 rows it is close to the tick truth lane r1 verified. It is used here for the
whole archive because a per-sleeve verdict computed on two different spread sources would be
uninterpretable. The direction of any model error is not known a priori, so no claim here
rests on a small margin: the two sleeves this file names are 2.4x and 6.6x the limit at the
MEDIAN, not near it.

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

from src.components.ultimate_book.primitives import atr14  # noqa: E402
from src.research_infra.walkforward.quote_side import (  # noqa: E402
    SpreadUnavailable, spread_for,
)

HERE = Path(__file__).resolve().parent
P6 = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
P8 = REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts"
P9 = REPO / "docs/audits/fable5-vision-audit-20260725/phase9/receipts"
AA_IN = P6 / "AA_ESTATE_TRADES.json.gz"
AK_IN = P8 / "AK_SUPPLY_TRADES.json.gz"
AM_SUBMID = P9 / "AM_SUBMID_TRADES.json.gz"
CENSUS = HERE / "P3_STOP_COUPLING_V1.json"
OUT = HERE / "P3_SENDGATE_V1.json"

ACCOUNT = "FTMO"
TF_MINUTES = {15: 15, 16385: 15, 16388: 240, 16408: 1440}

#: The live limit. Read from the same place both live layers read it, so this file cannot
#: drift from the gate it is measuring against.
from src.components.ultimate_book.spread_geometry import (  # noqa: E402
    SPREAD_GEOMETRY_FLOOR_DEFAULT_LIMIT as LIMIT,
)

#: The armed set, established from the launcher rather than from prose — lane m3's
#: `armed_from_launcher` found all three wave-20 lanes had it wrong.
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert")


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, int(round(p * (len(xs) - 1)))))]


def main() -> int:
    t0 = time.time()
    print("loading bars ...", flush=True)
    series, index, _ = AD.load_bars()
    print(f"  {len(series)} series in {time.time()-t0:.1f}s", flush=True)

    trades = dict(json.load(gzip.open(AA_IN, "rt"))["trades"])
    for k, v in json.load(gzip.open(AK_IN, "rt"))["trades"].items():
        trades.setdefault(k, v)
    if AM_SUBMID.exists():
        am = json.load(gzip.open(AM_SUBMID, "rt"))
        rows = am.get("trades") or am.get("rows")
        if isinstance(rows, dict):
            rows = rows.get("sub_mid_dn_revert")
        if rows:
            trades["sub_mid_dn_revert"] = rows

    census = json.load(open(CENSUS))["census"]
    out: dict[str, dict] = {}

    for sleeve, rows in sorted(trades.items()):
        sr, stop_atr = [], []
        by_era: dict[str, list[float]] = {"pre2015": [], "2015_2019": [],
                                          "2020_2023": [], "2024_plus": []}
        skips = collections.Counter()
        for r in rows:
            tf = int(r["timeframe"])
            key = (r["symbol"], tf)
            if key not in index:
                skips["no_series"] += 1
                continue
            i = index[key].get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
            if i is None:
                skips["bar_not_found"] += 1
                continue
            bars, times = series[key]
            a = atr14(bars, i)
            if a <= 0:
                skips["zero_atr"] += 1
                continue
            sd = float(r["sl_distance_price"])
            entry_utc = times[i] + dt.timedelta(minutes=TF_MINUTES[tf])
            try:
                s = spread_for(r["symbol"], entry_utc, account=ACCOUNT, band="mid")
            except SpreadUnavailable as e:
                skips[f"spread:{str(e)[:40]}"] += 1
                continue
            sr.append(s / sd)
            stop_atr.append(sd / a)
            y = entry_utc.year
            bucket = ("pre2015" if y < 2015 else "2015_2019" if y < 2020
                      else "2020_2023" if y < 2024 else "2024_plus")
            by_era[bucket].append(s / sd)
        if not sr:
            continue
        med_sr, med_sa = statistics.median(sr), statistics.median(stop_atr)
        eras = {k: {"n": len(v),
                    "median_spread_r": round(statistics.median(v), 5),
                    "p95_spread_r": round(q(v, 0.95), 5),
                    "frac_refused_at_limit": round(sum(1 for x in v if x > LIMIT) / len(v), 5)}
                for k, v in by_era.items() if v}
        rec = {
            "n": len(sr), "skips": dict(skips),
            "kind": (census.get(sleeve) or {}).get("kind"),
            "coupled": (census.get(sleeve) or {}).get("kind") in
                       ("WICK_UNFLOORED", "RANGE_UNFLOORED", "WICK_FLOORED", "RANGE_FLOORED"),
            "armed": sleeve in ARMED,
            "median_spread_r": round(med_sr, 5),
            "mean_spread_r": round(statistics.fmean(sr), 5),
            "p95_spread_r": round(q(sr, 0.95), 5),
            "max_spread_r": round(max(sr), 5),
            "frac_refused_at_limit": round(sum(1 for x in sr if x > LIMIT) / len(sr), 5),
            "median_stop_atr": round(med_sa, 5),
            "k_needed_for_median_under_limit": round(med_sr / LIMIT * med_sa, 4),
            #: THE COUPLING'S SIGNATURE AT THE SEND GATE. A stop built from an ATR gives a
            #: `spread_r` whose spread is the whole variance; a stop built from a wick adds
            #: the wick's own variance to the DENOMINATOR, which is a fat right tail. So the
            #: coupled sleeves are identified by p95/median, not by the median.
            "p95_over_median": round(q(sr, 0.95) / med_sr, 4) if med_sr > 0 else None,
            "by_era": eras,
        }
        out[sleeve] = rec

    ordered = sorted(out.items(), key=lambda kv: -kv[1]["frac_refused_at_limit"])
    print(f"\n{'sleeve':30s} {'n':>5s} {'medSR':>8s} {'p95SR':>9s} {'p95/med':>8s} "
          f"{'refused':>8s} {'ref24+':>7s} {'coupled':>8s} {'armed':>6s}")
    for s, v in ordered:
        m = (v["by_era"].get("2024_plus") or {})
        print(f"{s:30s} {v['n']:5d} {v['median_spread_r']:8.4f} {v['p95_spread_r']:9.4f} "
              f"{(v['p95_over_median'] or 0):8.2f} {v['frac_refused_at_limit']:8.4f} "
              f"{(m.get('frac_refused_at_limit', float('nan'))):7.3f} "
              f"{str(v['coupled']):>8s} {str(v['armed']):>6s}")

    coup = [v for v in out.values() if v["coupled"]]
    unc = [v for v in out.values() if not v["coupled"]]
    doc = {
        "schema": "gtos.wave20.p3.sendgate.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "generated_utc": dt.datetime.now(dt.UTC).isoformat(),
        "limit": LIMIT,
        "limit_source": [
            "src/components/broker_net_cost_engine.py:689 selected_cell_pretrade_max_spread_r",
            "src/components/ultimate_book/book_owner.py:4700 default 0.10",
            "src/components/ultimate_book/spread_geometry.py:88 "
            "SPREAD_GEOMETRY_FLOOR_DEFAULT_LIMIT",
        ],
        "spread_source": "walkforward.quote_side.spread_for(band='mid') — Session AG's "
                         "era-aware measured model, the same object lane r1's walker uses",
        "armed_set": list(ARMED),
        "sleeves": out,
        "summary": {
            "n_sleeves": len(out),
            "n_over_limit_at_median": sum(1 for v in out.values()
                                          if v["median_spread_r"] > LIMIT),
            "over_limit_at_median": sorted(s for s, v in out.items()
                                           if v["median_spread_r"] > LIMIT),
            "median_frac_refused_coupled": (round(statistics.median(
                [v["frac_refused_at_limit"] for v in coup]), 5) if coup else None),
            "median_frac_refused_uncoupled": (round(statistics.median(
                [v["frac_refused_at_limit"] for v in unc]), 5) if unc else None),
            "n_coupled": len(coup), "n_uncoupled": len(unc),
            "median_p95_over_median_coupled": (round(statistics.median(
                [v["p95_over_median"] for v in coup if v["p95_over_median"]]), 4)
                if coup else None),
            "median_p95_over_median_uncoupled": (round(statistics.median(
                [v["p95_over_median"] for v in unc if v["p95_over_median"]]), 4)
                if unc else None),
            "reading": (
                "TWO HONEST NEGATIVES, BOTH AGAINST THIS LANE'S OWN HYPOTHESIS. (1) The "
                "MEDIAN refusal fraction does NOT separate coupled from uncoupled — "
                "0.1392 vs 0.1376 — so the send-gate problem is an instrument-and-"
                "timeframe property, not a stop-expression property, and the coupling is "
                "not its cause. (2) The TAIL ratio p95/median separates the two GROUPS in "
                "the median (6.23 coupled vs 2.77 uncoupled, 2.25x) but does NOT classify "
                "an individual sleeve: the single highest value in the estate, 30.82, is "
                "`crypto`, which is uncoupled, and it comes from the 2015-2019 crypto "
                "spread regime rather than from any stop expression. "
                "BETWEEN-sleeve comparison cannot isolate the coupling, because spread_r's "
                "variance is dominated by the spread's own (era, symbol, session) and not "
                "by the stop's. The coupling is established WITHIN sleeve, by the decile "
                "table in P3_ESTATE_FLOOR_V1.json, where instrument and era are held "
                "fixed and the thinnest-stop decile pays 2.5-3.5x the widest on all four "
                "generators."),
        },
        "seconds": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(doc, indent=1))
    print(f"\nover limit at the MEDIAN: {doc['summary']['over_limit_at_median']}")
    print(f"median frac refused — coupled {doc['summary']['median_frac_refused_coupled']} "
          f"vs uncoupled {doc['summary']['median_frac_refused_uncoupled']}")
    print(f"wrote {OUT}  ({time.time()-t0:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
