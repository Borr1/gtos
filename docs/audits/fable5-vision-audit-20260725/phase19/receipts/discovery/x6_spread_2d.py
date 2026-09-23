"""x6 pass 2: is the minute-of-hour spread premium a BAR-BOUNDARY effect, or just the
known daily ROLLOVER premium leaking into the pooled profile?

Buckets jointly by (broker_hour, minute_of_hour). One observation per (symbol, broker-minute)
= median spread of that minute's ticks (time-weighted, not tick-weighted).
Raw epochs in these files are BROKER WALL CLOCK, so hour = (epoch//3600)%24 is the broker hour
directly -- the same axis the estate's hour-aware cost model uses.
"""
import gzip, json, os, statistics, sys
from concurrent.futures import ProcessPoolExecutor
TICKROOT = "/Users/borr/GTOSActive/vps-ticks-20260726"

def one_file(path):
    sym = os.path.basename(path).split("_ticks_")[0]
    cur=None; buf=[]; cells={}
    def flush(m, vals):
        h=(m//60)%24; moh=m%60
        cells.setdefault((h,moh),[]).append(statistics.median(vals))
    try:
        with gzip.open(path,"rt") as fh:
            fh.readline()
            for line in fh:
                p=line.split(",")
                if len(p)<6: continue
                try: b=float(p[1]); a=float(p[2]); tms=int(p[5])
                except ValueError: continue
                if b<=0.0 or a<=0.0 or a<=b: continue
                m=tms//60000
                if m!=cur:
                    if cur is not None and buf: flush(cur,buf)
                    cur=m; buf=[]
                buf.append(a-b)
            if cur is not None and buf: flush(cur,buf)
    except Exception as e:
        return {"symbol":sym,"error":repr(e)}
    return {"symbol":sym,
            "cell_median":{f"{h}|{mo}":statistics.median(v) for (h,mo),v in cells.items()},
            "cell_n":{f"{h}|{mo}":len(v) for (h,mo),v in cells.items()}}

if __name__=="__main__":
    broker=sys.argv[1]
    files=sorted(f"{TICKROOT}/{broker}/{f}" for f in os.listdir(f"{TICKROOT}/{broker}") if f.endswith(".csv.gz"))
    out=[]
    with ProcessPoolExecutor(max_workers=6) as ex:
        for r in ex.map(one_file,files):
            out.append(r); print("done",r.get("symbol"),flush=True)
    json.dump({"broker":broker,"symbols":out},open(f"/tmp/x6/X6_SPREAD_2D_{broker}.json","w"))
