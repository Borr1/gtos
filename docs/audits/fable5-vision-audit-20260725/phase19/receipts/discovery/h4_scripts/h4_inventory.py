import json, io, subprocess, collections, os, sys, gzip

OUT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"

def zread(p):
    proc = subprocess.Popen(["zstd","-dc",p], stdout=subprocess.PIPE)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8", errors="replace"):
        yield line
    proc.wait()

def read(p):
    if p.endswith(".zst"): 
        yield from zread(p); return
    if p.endswith(".gz"):
        with gzip.open(p,"rt",errors="replace") as fh:
            yield from fh
        return
    with open(p, errors="replace") as fh:
        yield from fh

P = "/Users/borr/gtos-vps-archive-20260803/shadow_logs/ultimate_book_runtime_learning_packets.jsonl.zst"
ev = collections.Counter(); ns = collections.Counter(); days = collections.Counter()
placement = collections.Counter()
fieldpresent = collections.Counter()
COSTF = ["slippage_r","slippage_price","spread_r","spread_price","commission","commission_r","swap","swap_r",
         "fill_price","requested_price","entry_price","realized_cost_r","broker_commission","fill_latency_ms"]
samples = {}
n=0
for line in read(P):
    line=line.strip()
    if not line: continue
    try: r=json.loads(line)
    except: continue
    n+=1
    e=r.get("event_type"); ev[e]+=1
    ns[r.get("namespace")]+=1
    ca=r.get("created_at_utc") or ""
    days[ca[:10]]+=1
    placement[r.get("placement_status")]+=1
    flat={}
    def flat_walk(d,pre=""):
        for k,v in d.items():
            if isinstance(v,dict): flat_walk(v,pre+k+".")
            else: flat[pre+k]=v
    flat_walk(r)
    for f in COSTF:
        for k in flat:
            if k.split(".")[-1]==f and flat[k] not in (None,""):
                fieldpresent[f]+=1; break
    if e not in samples: samples[e]=sorted(flat.keys())
print("TOTAL", n)
print("EVENT_TYPES", ev.most_common(30))
print("NAMESPACES", ns.most_common())
print("PLACEMENT", placement.most_common(20))
print("DAYS_RANGE", min(days), max(days), "ndays", len(days))
print("COSTFIELD_NONNULL", fieldpresent.most_common())
json.dump({"total":n,"events":dict(ev),"namespaces":dict(ns),"placement":dict(placement),
           "days":dict(days),"costfields":dict(fieldpresent),
           "sample_keys":{k:v for k,v in samples.items()}},
          open(OUT+"/h4_packet_inventory.json","w"), indent=1, default=str)
