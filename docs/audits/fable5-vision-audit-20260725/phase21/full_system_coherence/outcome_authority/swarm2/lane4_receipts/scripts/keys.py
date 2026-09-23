import gzip, pickle, json
from collections import Counter
p="/private/tmp/w21-puzzle-cache/rows_feb.pkl.gz"
rows=pickle.load(gzip.open(p,"rb"))
print("n_rows",len(rows))
k=Counter()
for r in rows[:5000]:
    k.update(r.keys())
print("n_distinct_keys",len(k))
for key,c in sorted(k.items()):
    print(f"  {key}  ({c})")
print("\n--- SAMPLE ROW ---")
r=rows[0]
for key in sorted(r.keys()):
    v=r[key]
    s=repr(v)
    print(f"{key} = {s[:200]}")
