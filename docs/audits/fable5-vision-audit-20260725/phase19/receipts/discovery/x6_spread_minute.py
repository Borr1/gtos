"""x6: does the spread an order pays depend on the MINUTE within the M15 bar?

The estate's cost model is HOUR-aware, not minute-aware. The wave's headline lever moves
entries off the bar boundary by ~5 minutes. If the spread at the boundary differs from the
spread 5 minutes later, the hour-aware model mis-prices the lever by exactly that amount.

Instrument: one observation per (symbol, broker-minute) = the MEDIAN spread of the ticks in
that minute. That is time-weighted (one order placed at one moment), not tick-weighted --
tick ARRIVAL RATE itself varies by minute-offset, so a tick-weighted median would be
contaminated by the very effect being measured.

Minute-of-hour is INVARIANT between broker clock and UTC (the offset is a whole number of
hours: new_york_plus_7 => UTC+3/+2), so the offset buckets need no clock conversion. The
HOUR bucket does, and uses src.utils.broker_clock.
"""
import gzip, json, os, statistics, sys
from concurrent.futures import ProcessPoolExecutor

TICKROOT = "/Users/borr/GTOSActive/vps-ticks-20260726"

def one_file(path):
    sym = os.path.basename(path).split("_ticks_")[0]
    # per-minute medians
    minute_med = {}        # minute_idx -> median spread
    minute_n = {}          # minute_idx -> tick count
    cur = None; buf = []
    bad = 0; tot = 0
    try:
        with gzip.open(path, "rt") as fh:
            fh.readline()  # header
            for line in fh:
                # time,bid,ask,last,volume,time_msc,flags,volume_real
                p = line.split(",")
                if len(p) < 6: continue
                tot += 1
                try:
                    b = float(p[1]); a = float(p[2]); tms = int(p[5])
                except ValueError:
                    bad += 1; continue
                if b <= 0.0 or a <= 0.0 or a <= b:
                    bad += 1; continue
                m = tms // 60000
                if m != cur:
                    if cur is not None and buf:
                        minute_med[cur] = statistics.median(buf); minute_n[cur] = len(buf)
                    cur = m; buf = []
                buf.append(a - b)
            if cur is not None and buf:
                minute_med[cur] = statistics.median(buf); minute_n[cur] = len(buf)
    except Exception as e:
        return {"symbol": sym, "path": path, "error": repr(e)}
    if not minute_med:
        return {"symbol": sym, "path": path, "error": "no_valid_minutes"}

    # bucket by minute-within-M15 and minute-of-hour
    by_m15 = {i: [] for i in range(15)}
    by_moh = {i: [] for i in range(60)}
    n_by_m15 = {i: [] for i in range(15)}
    by_hour = {}
    for m, sp in minute_med.items():
        moh = m % 60
        by_m15[m % 15].append(sp)
        by_moh[moh].append(sp)
        n_by_m15[m % 15].append(minute_n[m])
        h = (m // 60) % 24                      # BROKER hour (raw epoch is broker wall clock)
        by_hour.setdefault(h, []).append(sp)
    allsp = list(minute_med.values())
    med_all = statistics.median(allsp)

    def med(v): return statistics.median(v) if v else None
    res = {
        "symbol": sym,
        "n_minutes": len(minute_med),
        "n_ticks_parsed": tot,
        "n_ticks_rejected": bad,
        "median_spread_all": med_all,
        "m15_offset_median": {str(i): med(by_m15[i]) for i in range(15)},
        "m15_offset_n": {str(i): len(by_m15[i]) for i in range(15)},
        "m15_offset_ticks_per_min_median": {str(i): med(n_by_m15[i]) for i in range(15)},
        "moh_median": {str(i): med(by_moh[i]) for i in range(60)},
        "broker_hour_median": {str(h): med(v) for h, v in sorted(by_hour.items())},
    }
    # the lever's price: spread at offset 0 vs the +1..+5 window and the whole non-boundary bar
    o0 = res["m15_offset_median"]["0"]
    w15 = [med_all]
    res["ratio_offset0_to_all"] = (o0 / med_all) if med_all else None
    for k, rng in (("1_5", range(1, 6)), ("1_14", range(1, 15)), ("5", [5])):
        vals = [x for i in rng for x in by_m15[i]]
        m = med(vals)
        res[f"median_offset_{k}"] = m
        res[f"ratio_offset0_over_{k}"] = (o0 / m) if m else None
    return res

def main():
    broker = sys.argv[1] if len(sys.argv) > 1 else "ftmo"
    files = sorted(f"{TICKROOT}/{broker}/{f}" for f in os.listdir(f"{TICKROOT}/{broker}")
                   if f.endswith(".csv.gz"))
    out = []
    with ProcessPoolExecutor(max_workers=6) as ex:
        for r in ex.map(one_file, files):
            out.append(r)
            print(f"done {r.get('symbol')}: n_min={r.get('n_minutes')} "
                  f"ratio0/1-5={r.get('ratio_offset0_over_1_5')}", flush=True)
    json.dump({"broker": broker, "symbols": out},
              open(f"/tmp/x6/X6_SPREAD_MINUTE_{broker}.json", "w"), indent=1)

if __name__ == "__main__":
    main()
