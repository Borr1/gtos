import gzip, json, os, re, pathlib
ROOT=pathlib.Path("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
POOL=ROOT/"docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
with gzip.open(POOL,'rt') as f: keys=list(json.loads(f.readline()).keys())
alias={"broker_pretrade_diag_expected_cost_r":"broker_pretrade_cost_non_executable_diagnostic_expected_cost_r",
 "confidence_default_applied":"confidence_missing_degraded_default_applied",
 "matched_sleeve_count":"ultimate_package_matched_sleeve_count",
 "effective_admission_count":"ultimate_package_effective_admission_count",
 "final_blocker_class":"missed_package_replay_order_executable_final_blocker_class",
 "same_symbol_exposure_risk_pct":"same_symbol_lifecycle_exposure_risk_pct"}
allnames=sorted(set(keys)|set(alias.values()),key=len,reverse=True)
rx=re.compile("|".join(map(re.escape,allnames)))
byname={n:[] for n in allnames}
files=sorted((ROOT/"src").rglob("*.py")); nl=0
for fp in files:
    try: txt=fp.read_text(errors="replace")
    except Exception: continue
    if not rx.search(txt): continue
    rel=str(fp.relative_to(ROOT))
    for i,t in enumerate(txt.splitlines(),1):
        nl+=1
        ms=set(rx.findall(t))
        if not ms: continue
        for m in ms:
            w=bool(re.search(r'["\']%s["\']\s*:'%m,t)) or bool(re.search(r'(^|[^.\w])%s\s*=[^=]'%m,t))
            g=bool(re.search(r'\.get\(\s*["\']%s["\']'%m,t))
            byname[m].append({"f":rel,"l":i,"t":t.strip()[:170],"writer":w,"getter":g})
out={}
for k in keys:
    ns=[k]+([alias[k]] if k in alias else [])
    hits=[]
    for n in ns:
        for h in byname[n]:
            h=dict(h); h["as"]=n; hits.append(h)
    hits.sort(key=lambda h:(not h["writer"], h["f"], h["l"]))
    out[k]={"n":len(hits),"n_writer":sum(h["writer"] for h in hits),
            "files":sorted({h["f"] for h in hits}),"hits":hits[:14]}
json.dump({"keys":keys,"alias":alias,"trace":out,"files_scanned":len(files)},
          open(os.environ["TMPDIR"]+"/w0d/trace.json","w"),indent=1)
z=[k for k in keys if out[k]["n"]==0]; zw=[k for k in keys if out[k]["n_writer"]==0]
print("files",len(files),"zero-hit",len(z),z)
print("zero-writer",len(zw),zw)
