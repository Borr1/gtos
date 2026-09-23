"""d4_zoneverify — check the POI families' claim against price, in the
candidate's OWN contract units.

The MSO's own mitigation convention (market_state.py:610, :635) scans only from
the BREAK index forward — the up-to-10-bar impulse leg between the order block's
formation candle and the structure break is deliberately blind — so "has the tape
touched the zone since formation" is not a fair test of `mitigated=False`.

These tests are convention-free because they are denominated in the candidate's
own geometry:

  STOP ALREADY TRADED     has price traded beyond THIS candidate's stop_loss at
                          any bar between the zone's formation and the decision?
  TARGET ALREADY TRADED   has price traded beyond THIS candidate's take_profit
                          in the same window?
  ENTRY ALREADY TRADED    has the limit level itself already been available?

A candidate whose stop has already been traded through is offering a stop the
market has demonstrably breached while the zone was supposedly live.
"""
from __future__ import annotations
import sys, os, gzip, json, glob, collections, bisect
from datetime import datetime, timedelta
sys.path.insert(0, "/tmp/d4")
import d4_lib as L


def sel(s, T):
    j = bisect.bisect_right(s.t, T - timedelta(minutes=15)) - 1
    return j if j >= 0 else None


def main(src_dir, out_path):
    S = L.load_series()
    agg = collections.defaultdict(lambda: {
        "n": 0, "no_zone": 0, "no_ft": 0, "stop_traded": 0, "tgt_traded": 0,
        "entry_traded": 0, "strict_overlap": 0, "closed_inside": 0,
        "mitfrac": [], "age_h": [], "tc": [], "mit": [], "gap": [],
        "cross": collections.Counter(), "nbars": []})
    files = [f for f in sorted(glob.glob(os.path.join(src_dir, "*.jsonl.gz")))
             if os.path.exists(f.replace(".jsonl.gz", ".stats.json"))]
    for f in files:
        for line in gzip.open(f, "rt"):
            r = json.loads(line)
            fam = r["f"]; a = agg[fam]; a["n"] += 1
            zl, zh, ft = r.get("zl"), r.get("zh"), r.get("ft")
            if zl is None or zh is None:
                a["no_zone"] += 1; continue
            s = S.get(r["s"])
            if s is None: continue
            T = datetime.fromisoformat(r["t"]).replace(tzinfo=None)
            i = sel(s, T)
            if i is None: continue
            fi = None
            if ft:
                try:
                    fdt = datetime.fromisoformat(str(ft).replace("Z", "+00:00")).replace(tzinfo=None)
                    fi = s.idx.get(fdt)
                    if fi is None:
                        fi = bisect.bisect_right(s.t, fdt) - 1
                    a["age_h"].append((s.t[i] - fdt).total_seconds() / 3600.0)
                except Exception:
                    fi = None
            else:
                a["no_ft"] += 1
            if fi is None or fi < 0:
                fi = max(0, i - 96)
            lo, hi = min(zl, zh), max(zl, zh)
            w = hi - lo
            e, sl_, tp = r["e"], r["sl"], r["tp"]
            lng = r["d"] == "L"
            deepest = 0.0; nb = 0; closed = 0
            hit_stop = hit_tgt = hit_entry = False
            for k in range(fi + 1, i + 1):
                bh, bl = s.h[k], s.l[k]
                if bl < hi and bh > lo:
                    nb += 1
                    pen = min(bh, hi) - max(bl, lo)
                    if w > 0: deepest = max(deepest, pen / w)
                if lo <= s.c[k] <= hi: closed += 1
                if lng:
                    if bl <= sl_: hit_stop = True
                    if bh >= tp: hit_tgt = True
                    if bl <= e: hit_entry = True
                else:
                    if bh >= sl_: hit_stop = True
                    if bl <= tp: hit_tgt = True
                    if bh >= e: hit_entry = True
            a["nbars"].append(nb)
            if nb: a["strict_overlap"] += 1
            if closed: a["closed_inside"] += 1
            if hit_stop: a["stop_traded"] += 1
            if hit_tgt: a["tgt_traded"] += 1
            if hit_entry: a["entry_traded"] += 1
            a["mitfrac"].append(deepest)
            if r.get("tc") is not None: a["tc"].append(r["tc"])
            if r.get("mit") is not None: a["mit"].append(r["mit"])
            d = abs(e - sl_)
            if d > 0 and r.get("cp"):
                g = (r["cp"] - e) / d * (1.0 if lng else -1.0)
                a["gap"].append(g)
                b = ("past_stop" if g < -1 else "marketable" if g < 0
                     else "resting" if g < 1.5 else "target_through")
                a["cross"][(b, hit_stop)] += 1

    def q(v, p):
        if not v: return None
        v = sorted(v); return v[min(len(v) - 1, int(p * len(v)))]

    out = {"source": src_dir, "families": {}}
    for fam, a in agg.items():
        n = a["n"]
        out["families"][fam] = {
            "n": n, "no_zone": a["no_zone"], "no_formation_time": a["no_ft"],
            "stop_already_traded_since_formation": a["stop_traded"],
            "stop_already_traded_rate": round(a["stop_traded"] / n, 6),
            "target_already_traded_since_formation": a["tgt_traded"],
            "target_already_traded_rate": round(a["tgt_traded"] / n, 6),
            "entry_level_already_traded_rate": round(a["entry_traded"] / n, 6),
            "zone_strictly_overlapped_rate": round(a["strict_overlap"] / n, 6),
            "m15_close_inside_zone_rate": round(a["closed_inside"] / n, 6),
            "tape_mitigation_fraction_median": q(a["mitfrac"], 0.5),
            "overlapping_bars_median": q(a["nbars"], 0.5),
            "zone_age_hours_median": q(a["age_h"], 0.5),
            "zone_age_hours_p95": q(a["age_h"], 0.95),
            "recorded_touch_count_median": q(a["tc"], 0.5),
            "recorded_max_mitigation_fraction_median": q(a["mit"], 0.5),
            "fill_gap_R_median": q(a["gap"], 0.5),
            "gapbin_x_stop_already_traded": {f"{k[0]}|stop_traded={k[1]}": v
                                             for k, v in sorted(a["cross"].items())},
        }
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=1)
    for fam, v in out["families"].items():
        print(f'{fam:26s} n={v["n"]:6d} stop_already_traded={v["stop_already_traded_rate"]:.4f} '
              f'tgt_already={v["target_already_traded_rate"]:.4f} '
              f'entry_already={v["entry_level_already_traded_rate"]:.4f} '
              f'age_h={v["zone_age_hours_median"]} tc={v["recorded_touch_count_median"]}')


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
