"""SYNTHESIS — one uniform whole-population off-configured-session census for ALL TEN
broad-origin families that emit, on the same 8-window roster every lane used.

Why: g2 measured it for 3 families, g4/g1 for others on the January pool only. Borhen asked
for the irrelevant-by-construction fraction PER FAMILY. This makes the denominator identical.

off_configured_session is hard-rejected unconditionally at selector_v4.py:2553-2570
(config/agent_config.yaml:816-817 block_off_configured_session_entries: true, action reject),
decidable from the bar timestamp alone at the moment of generation.
"""
from __future__ import annotations
import gzip, glob, json, os, sys
from collections import defaultdict
from datetime import datetime
RCPT="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts"
REPO="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
sys.path.insert(0,RCPT+"/discovery/d3"); sys.path.insert(0,REPO)
import d3_tape as D
from src.research_infra.v4_timewarp_simulated_live_research_loop import derive_session

cnt=defaultdict(lambda: dict(n=0, off=0, off_crypto_collision=0, off_genuine=0))
seen_by_win={}
for win,indir in sorted(D.WINDOWS.items()):
    seen={}
    for p in sorted(glob.glob(os.path.join(indir,"pbg_*.jsonl.gz"))):
        with gzip.open(p,"rt") as fh:
            for line in fh:
                r=json.loads(line)
                if r["k"]!=15: continue
                k=D.setup_key(r)
                if k in seen: continue
                seen[k]=1
                f=r["f"]; s=r["s"]
                sess=derive_session(s, datetime.fromisoformat(r["t"]))
                c=cnt[f]; c["n"]+=1
                if sess=="off_configured_session":
                    c["off"]+=1
                    if s in ("BTCUSD","ETHUSD"): c["off_crypto_collision"]+=1
                    else: c["off_genuine"]+=1
out={"schema":"syn_offsession_v1",
     "population":"phase19 d3 8-window close-only roster, k==15, deduped by d3_tape.setup_key",
     "definition":"off_configured_session per src.research_infra.v4_timewarp_simulated_live_research_loop.derive_session; hard-rejected at selector_v4.py:2553-2570",
     "windows":sorted(D.WINDOWS.keys()),
     "families":{}}
tot=totoff=0
for f,c in sorted(cnt.items(), key=lambda x:-x[1]["n"]):
    c=dict(c); c["off_share"]=c["off"]/c["n"] if c["n"] else None
    c["off_crypto_collision_share_of_off"]=c["off_crypto_collision"]/c["off"] if c["off"] else None
    out["families"][f]=c; tot+=c["n"]; totoff+=c["off"]
    print(f"{f:36s} n={c['n']:8d} off={c['off']:8d} ({c['off_share']:.4f})  collision={c['off_crypto_collision']:6d}")
out["pool_total"]=tot; out["pool_off"]=totoff; out["pool_off_share"]=totoff/tot
print(f"{'POOL':36s} n={tot:8d} off={totoff:8d} ({totoff/tot:.4f})")
json.dump(out, open("syn_receipts/SYN_OFFSESSION_V1.json","w"), indent=1)
