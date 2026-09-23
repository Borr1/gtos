"""How wide is the seal's import hole? Modules a BOUND file imports that are themselves unbound."""
import json, os, subprocess, sys
REPO="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
os.chdir(REPO)
code = r'''
import sys, json, importlib
before=set(sys.modules)
ok=[];bad={}
for m in ("src.research_infra.v4_timewarp_simulated_live_research_loop",):
    try: importlib.import_module(m); ok.append(m)
    except Exception as e: bad[m]=repr(e)[:200]
mods=sorted(k for k in sys.modules if k not in before)
files={}
for m in mods:
    mod=sys.modules.get(m)
    f=getattr(mod,"__file__",None)
    if f: files[m]=f
print(json.dumps({"ok":ok,"bad":bad,"files":files}))
'''
r=subprocess.run([sys.executable,"-c",code],capture_output=True,text=True,cwd=REPO)
sys.stderr.write(r.stderr[-3000:])
d=json.loads(r.stdout.strip().splitlines()[-1])
print("imported:",d["ok"],"failed:",d["bad"])
files=d["files"]
proj={m:f for m,f in files.items() if f.startswith(REPO+"/") and "/site-packages/" not in f}
rel={m:os.path.relpath(f,REPO) for m,f in proj.items()}
C='research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json'
cd=json.load(open(C))
def walk(o):
    if isinstance(o,dict):
        if isinstance(o.get('path'),str): yield o['path']
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
bound=set(walk(cd))
# code_authority_paths, read literally from the runner
import re
src=open("src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py").read()
blk=src.split("code_authority_paths = (",1)[1].split(")\n",1)[0]
auth=set(re.findall(r'"([^"]+\.py)"', blk))
sealed = bound | auth
unbound = sorted(p for p in rel.values() if p not in sealed)
print(f"project modules reachable from the BOUND replay loop: {len(rel)}")
print(f"  of those SEALED (contract-bound or code_authority): {len(rel)-len(unbound)}")
print(f"  of those UNSEALED (editable with zero drift reported): {len(unbound)}")
for p in unbound[:12]: print("   ", p)
print("   ...")
print("broader_origin_generators unsealed:", "src/components/broader_origin_generators.py" in unbound)
json.dump({"reachable":sorted(rel.values()),"sealed_subset":sorted(set(rel.values())&sealed),
           "unsealed":unbound}, open("/tmp/v1_seal_hole.json","w"), indent=1)
