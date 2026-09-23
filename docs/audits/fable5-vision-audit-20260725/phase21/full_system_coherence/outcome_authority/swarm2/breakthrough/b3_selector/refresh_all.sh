#!/bin/zsh
# B3 -- regenerate every evaluation from whatever walk-forward stages are COMPLETE.
# Safe to re-run at any time; arms are admitted only when their stage has all 100
# scored days checkpointed (b3_lib.complete_stages).
set -e
cd "$(dirname "$0")"
O=/Users/borr/.claude/jobs/adb9e69b/tmp/b3/out
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}
rm -f $O/eval_*.json                       # per-arm evals are cached; force refresh
python3 b3_evaluate.py
python3 b4_economics.py
python3 b5_paired_economics.py
python3 b6_adversarial.py
python3 b7_decile.py
mkdir -p receipts
cp $O/{ADVERSARIAL_V1,ECONOMICS_V1,PAIRED_ECONOMICS_V1,EVAL_V1,DECILE_V1}.json receipts/
cp $O/eval_*.json receipts/
python3 - <<'PY'
import hashlib, json, pathlib
d = pathlib.Path("receipts"); prov = {}
for f in sorted(d.glob("*.json")):
    if f.name != "PROVENANCE.json": prov[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
for f in sorted(pathlib.Path(".").glob("*.py")) + sorted(pathlib.Path(".").glob("*.json")):
    prov[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
(d / "PROVENANCE.json").write_text(json.dumps(prov, indent=1, sort_keys=True) + "\n")
print(len(prov), "files hashed")
PY
python3 - <<'PY'
import json, pathlib
p = json.load(open("/Users/borr/.claude/jobs/adb9e69b/tmp/b3/out/PAIRED_ECONOMICS_V1.json"))
print(f"{'arm':16s} {'E1 sum':>9s} {'E1 p':>6s} {'selterm':>9s} {'p':>6s} {'capture':>9s} {'mkt%':>6s}")
for a, r in sorted(p["arms"].items(), key=lambda kv: -kv[1]["E2_selection_term"]["point"]):
    s, e = r["E2_selection_term"], r["E1_paired_vs_shipped"]
    print(f"{a:16s} {e['sum_r']:+9.2f} {e['boot']['p_two_sided_sign']:6.3f} "
          f"{s['point']:+9.5f} {s['p_two_sided_sign']:6.3f} {r['E3_ceiling_capture']:+9.4f} "
          f"{r['E2_market_top_share']*100:6.2f}")
PY
