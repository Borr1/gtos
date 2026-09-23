"""Independent reproduction of r2's blast-radius refusal count: |past_stop U stale|."""
import bisect, collections, csv, datetime as dt, glob, gzip, json, os
BARS=("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
      "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m15_20250601_20260610")
ROSTERS={"202510":"/tmp/f1/roster_202510","202511":"/tmp/f1/roster_202511","202512":"/tmp/f1/roster_202512",
         "202601":"/tmp/d4/rosters/202601","202602":"/tmp/d4/rosters/202602","202603":"/tmp/d4/rosters/202603",
         "202604":"/tmp/f1/roster_202604","202605":"/tmp/f1/roster_202605"}
POI={"current_fvg_fill","current_ob_retest","current_breaker_re_entry"}
S={}
for p in sorted(glob.glob(os.path.join(BARS,"*_M15.csv"))):
    sym=os.path.basename(p)[:-len("_M15.csv")]; rows=[]
    with open(p,newline="") as fh:
        for r in csv.DictReader(fh):
            rows.append((dt.datetime.fromisoformat(r["time"]).replace(tzinfo=None),float(r["close"])))
    rows.sort(); S[sym]=([r[0] for r in rows],[r[1] for r in rows])
n=ps=stale=both=union=noser=0
per=collections.Counter()
for win,rd in sorted(ROSTERS.items()):
    wn=wu=0
    for f in sorted(glob.glob(os.path.join(rd,"*.jsonl.gz"))):
        if not os.path.exists(f.replace(".jsonl.gz",".stats.json")): continue
        for line in gzip.open(f,"rt"):
            r=json.loads(line)
            if r["k"]!=15: continue
            n+=1; wn+=1
            s=S.get(r["s"])
            if s is None: noser+=1; continue
            T=dt.datetime.fromisoformat(r["t"]).replace(tzinfo=None)
            i=bisect.bisect_right(s[0],T-dt.timedelta(minutes=15)+dt.timedelta(seconds=2))-1
            if i<0: noser+=1; continue
            age=(T-(s[0][i]+dt.timedelta(minutes=15))).total_seconds()
            st = age>=900
            p_stop=False
            if r["f"] in POI:
                e,sl=r["e"],r["sl"]; risk=abs(e-sl)
                if risk>0:
                    g=(s[1][i]-e)/risk*(1.0 if r["d"]=="L" else -1.0)
                    p_stop = g < -1
            if st: stale+=1
            if p_stop: ps+=1
            if st and p_stop: both+=1
            if st or p_stop: union+=1; wu+=1
    per[win]=(wn,wu)
print(json.dumps({"rows":n,"no_series":noser,"past_stop":ps,"stale_ge_1period":stale,
                  "both":both,"union_refused":union,"per_window":{k:{"rows":v[0],"refused":v[1]} for k,v in per.items()}},indent=1))
