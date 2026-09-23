import json, subprocess, sys, os
code = r'''
import sys, json, importlib
before=set(sys.modules)
targets = ["src.components.ultimate_book.book_owner","src.components.ultimate_book.book_engine",
           "src.components.ultimate_book.admission","src.components.ultimate_book.sleeves.registry",
           "src.components.ultimate_book.order_router","src.components.execution",
           "src.components.execution_packets"]
ok=[]; bad={}
for t in targets:
    try: importlib.import_module(t); ok.append(t)
    except Exception as e: bad[t]=repr(e)[:200]
mods=sorted(k for k in sys.modules if k not in before)
# resolve armed sleeve generators
armed=["crypto","energy_agri","sub_xvol_pullback","sub_mid_dn_revert","mx_btcusd_d1_donchian_20_breakout"]
gen={}
try:
    reg=importlib.import_module("src.components.ultimate_book.sleeves.registry")
    specs=None
    for fn in ("active_specs",):
        if hasattr(reg,fn):
            specs=getattr(reg,fn)(None)
            break
    if specs is not None:
        for s in specs:
            nm=getattr(s,"name",None) or getattr(s,"sleeve",None)
            tags=getattr(s,"tags",None)
            g=getattr(s,"generator",None) or getattr(s,"gen",None) or getattr(s,"fn",None)
            gm=getattr(g,"__module__",None)
            gen[str(nm)]={"module":gm,"tags":list(tags) if tags else None}
except Exception as e:
    gen={"ERR":repr(e)[:300]}
print(json.dumps({"ok":ok,"bad":bad,"mods":mods,"gen":gen}))
'''
r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=os.getcwd())
sys.stderr.write(r.stderr[-3000:])
d=json.loads(r.stdout.strip().splitlines()[-1])
print("ok:",len(d["ok"]),d["ok"]); print("bad:",d["bad"])
mods=d["mods"]; print("total:",len(mods),"project:",len([m for m in mods if m.startswith('src.')]))
for needle in ("broader_origin_generators","broad_origin_emission_contract","walkforward","quote_side"):
    hit=[m for m in mods if needle in m]; print(f"  {needle:35s} -> {hit if hit else 'ABSENT'}")
json.dump(d, open("/tmp/v1_livecore_closure.json","w"), indent=1)
g=d["gen"]
print("registry entries:", len(g) if "ERR" not in g else g)
