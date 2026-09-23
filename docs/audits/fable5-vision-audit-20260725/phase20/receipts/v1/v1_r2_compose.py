#!/usr/bin/env python3
"""Do the two repaired lanes COMPOSE?

r2's past-stop refusal asks "is the market beyond the stop" with
`current_price = the SELECTED BAR's CLOSE`. r1 settled that that close is the BID.
A LONG buy limit transacts on the ASK, so the malformed-order test for a long is
`ask < stop`, i.e. `gap_bid < -1 - spread/risk`; r2 refuses at `gap_bid < -1`. For a
SHORT the sell limit transacts on the BID and r2's test is exact.

This measures the resulting over-refusal band on the WHOLE POI population, plus an
independent reproduction of r2's own bin census.
"""
from __future__ import annotations
import bisect, collections, csv, datetime as dt, glob, gzip, json, os, statistics, sys, time
from pathlib import Path

REPO = Path("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
sys.path.insert(0, str(REPO)); os.chdir(REPO)
from src.research_infra.walkforward.quote_side import spread_for, SpreadUnavailable  # noqa: E402

BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/"
        "bridge_ftmo_m15_20250601_20260610")
ROSTERS = {"202510": "/tmp/f1/roster_202510", "202511": "/tmp/f1/roster_202511",
           "202512": "/tmp/f1/roster_202512", "202601": "/tmp/d4/rosters/202601",
           "202602": "/tmp/d4/rosters/202602", "202603": "/tmp/d4/rosters/202603",
           "202604": "/tmp/f1/roster_202604", "202605": "/tmp/f1/roster_202605"}
RR = 1.5
POI = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}
SPREAD_NAME = {"GER40": "GER40.cash", "JP225": "JP225.cash", "NAS100": "US100.cash",
               "SPX500": "US500.cash", "UK100": "UK100.cash", "US30_cash": "US30.cash",
               "UKOIL_cash": "UKOIL.cash", "USOIL_cash": "USOIL.cash"}


class Series:
    __slots__ = ("t", "o", "h", "l", "c")
    def __init__(self, rows):
        self.t = [r[0] for r in rows]; self.o = [r[1] for r in rows]
        self.h = [r[2] for r in rows]; self.l = [r[3] for r in rows]; self.c = [r[4] for r in rows]


def load_series():
    out = {}
    for p in sorted(glob.glob(os.path.join(BARS, "*_M15.csv"))):
        sym = os.path.basename(p)[: -len("_M15.csv")]
        rows = []
        with open(p, newline="") as fh:
            for r in csv.DictReader(fh):
                rows.append((dt.datetime.fromisoformat(r["time"]).replace(tzinfo=None),
                             float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"])))
        rows.sort(); out[sym] = Series(rows)
    return out


def binof(g):
    return ("past_stop" if g < -1 else "marketable" if g < 0 else
            "resting" if g < RR else "target_through")


def main():
    S = load_series()
    t0 = time.time()
    fam = collections.defaultdict(lambda: {
        "n": 0, "bins": collections.Counter(), "bins_ask": collections.Counter(),
        "long": 0, "short": 0, "n_spread": 0, "no_spread": 0,
        "long_over_refused": 0, "long_past_stop_bid": 0, "long_past_stop_ask": 0,
        "short_past_stop": 0, "s_over_risk": [], "band_gaps": [],
    })
    scache: dict = {}
    for win, rd in sorted(ROSTERS.items()):
        for f in sorted(glob.glob(os.path.join(rd, "*.jsonl.gz"))):
            if not os.path.exists(f.replace(".jsonl.gz", ".stats.json")):
                continue
            for line in gzip.open(f, "rt"):
                r = json.loads(line)
                if r["k"] != 15 or r["f"] not in POI:
                    continue
                s = S.get(r["s"])
                if s is None:
                    continue
                a = fam[r["f"]]
                T = dt.datetime.fromisoformat(r["t"]).replace(tzinfo=None)
                i = bisect.bisect_right(s.t, T - dt.timedelta(minutes=15) + dt.timedelta(seconds=2)) - 1
                if i < 0:
                    continue
                cp = s.c[i]; e, sl = r["e"], r["sl"]
                risk = abs(e - sl)
                if risk <= 0:
                    continue
                a["n"] += 1
                L = (r["d"] == "L")
                a["long" if L else "short"] += 1
                sgn = 1.0 if L else -1.0
                gap = (cp - e) / risk * sgn
                a["bins"][binof(gap)] += 1
                spname = SPREAD_NAME.get(r["s"], r["s"])
                at = T.replace(tzinfo=dt.timezone.utc)
                ck = (spname, at.date(), at.hour)
                sp = scache.get(ck)
                if sp is None:
                    try:
                        sp = spread_for(spname, at, account="FTMO", band="mid")
                    except SpreadUnavailable:
                        sp = -1.0
                    scache[ck] = sp
                if sp < 0:
                    a["no_spread"] += 1
                    a["bins_ask"][binof(gap)] += 1
                    continue
                a["n_spread"] += 1
                sr = sp / risk
                a["s_over_risk"].append(sr)
                gap_t = gap + sr if L else gap      # LONG transacts on the ask; SHORT on the bid
                a["bins_ask"][binof(gap_t)] += 1
                if L:
                    a["long_past_stop_bid"] += int(gap < -1)
                    a["long_past_stop_ask"] += int(gap_t < -1)
                    if gap < -1 <= gap_t:
                        a["long_over_refused"] += 1
                        a["band_gaps"].append(gap)
                else:
                    a["short_past_stop"] += int(gap < -1)
        print(f"  {win} done {time.time()-t0:.0f}s", flush=True)

    out = {"what": "r1 x r2 composition: the past-stop test on the quote side that transacts",
           "population": "all POI-limit emissions, 8 windows, no sampling",
           "families": {}}
    tot = collections.Counter(); tot_ask = collections.Counter()
    tot_over = tot_long_ps = tot_short_ps = 0
    for name, a in sorted(fam.items()):
        tot.update(a["bins"]); tot_ask.update(a["bins_ask"])
        tot_over += a["long_over_refused"]
        tot_long_ps += a["long_past_stop_bid"]; tot_short_ps += a["short_past_stop"]
        out["families"][name] = {
            "n": a["n"], "long": a["long"], "short": a["short"],
            "bins_r2_as_shipped_bid": dict(a["bins"]),
            "bins_quote_side_corrected": dict(a["bins_ask"]),
            "long_past_stop_bid": a["long_past_stop_bid"],
            "long_past_stop_ask": a["long_past_stop_ask"],
            "long_over_refused": a["long_over_refused"],
            "short_past_stop_exact": a["short_past_stop"],
            "spread_over_risk_median": (round(statistics.median(a["s_over_risk"]), 6)
                                        if a["s_over_risk"] else None),
            "band_gap_median": (round(statistics.median(a["band_gaps"]), 6)
                                if a["band_gaps"] else None),
            "rows_without_spread": a["no_spread"],
        }
    out["totals"] = {
        "bins_r2_as_shipped_bid": dict(tot), "bins_quote_side_corrected": dict(tot_ask),
        "long_past_stop_refusals": tot_long_ps, "short_past_stop_refusals": tot_short_ps,
        "long_over_refusals": tot_over,
        "over_refusal_share_of_all_past_stop": (round(tot_over / tot["past_stop"], 6)
                                                if tot["past_stop"] else None),
    }
    dest = sys.argv[1] if len(sys.argv) > 1 else "/tmp/v1_r2_compose.json"
    json.dump(out, open(dest, "w"), indent=1)
    print(json.dumps(out["totals"], indent=1))
    print("WROTE", dest)


if __name__ == "__main__":
    main()
