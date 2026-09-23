"""G4 from packets alone: did the silent sleeves generate nothing, or generate and get filtered?

Classification is source-grounded, not guessed:
  PRE-GENERATOR  -- emitted by book_engine._generate_intents before spec.generator() is called.
                    Exactly two reasons exist (book_engine.py:446-458 and :490-497).
  POST-GENERATION-- every other skip reason is a placement gate in book_owner.run_cycle
                    (:1551-1749), which only ever runs on an intent that already exists.
A generator that runs and returns None leaves NO packet at all (book_engine.py:528-529),
so "generator invoked" must be derived, not read.
"""
import gzip, json, collections, sys

PKT = "/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/ultimate_book_runtime_learning_packets.jsonl.gz"
PRE_GENERATOR = {"profile_missing_instrument_config", "future_decision_bar_time"}

def reason_family(r):
    if not r: return None
    for f in PRE_GENERATOR:
        if r.startswith(f): return f
    return r.split(":")[0]

per_sleeve = collections.defaultdict(lambda: collections.Counter())
per_sleeve_sym = collections.defaultdict(lambda: collections.Counter())
cand_ids = collections.defaultdict(set)
cycles_by_ns = collections.defaultdict(set)   # ns -> set(created_at) for cycle-bearing rows
evt = collections.Counter()

for line in gzip.open(PKT, "rt"):
    r = json.loads(line)
    et = r.get("event_type"); evt[et] += 1
    ns = r.get("namespace")
    b = r.get("bridge") or {}
    if "n_candidates_in" in b:
        cycles_by_ns[ns].add(r.get("created_at_utc"))
    sl = r.get("sleeve")
    if et in ("unit_skipped","unit_admitted","unit_shadow","unit_placed") and sl:
        fam = reason_family(r.get("skip_reason"))
        bucket = ("PRE" if fam in PRE_GENERATOR else "POST")
        if et != "unit_skipped": bucket = "POST"
        per_sleeve[sl][f"{bucket}:{et}"] += 1
        per_sleeve[sl][f"reason:{fam}"] += 1
        per_sleeve[sl]["total"] += 1
        per_sleeve_sym[sl][(ns, r.get("symbol"), bucket)] += 1
        if r.get("candidate_id"): cand_ids[sl].add(r["candidate_id"])
    # candidates named inside units (recover sleeve for null-sleeve rows)
    for key in ("would_units","realized_units"):
        for u in (b.get(key) or []):
            for m in (u.get("sleeve_members") or []):
                cand_ids[m].add("UNIT")

print("event_type census:", dict(evt))
print("\ncycle-bearing rows per namespace:", {k: len(v) for k,v in cycles_by_ns.items()})

SILENT = ["metals_core","metals_softband","metals_ob_micro","crypto","energy_agri"]
print("\n" + "="*100)
print("THE FIVE HIGH-CONFIDENCE CORE SLEEVES")
print("="*100)
for s in SILENT:
    c = per_sleeve[s]
    pre  = sum(v for k,v in c.items() if k.startswith("PRE:"))
    post = sum(v for k,v in c.items() if k.startswith("POST:"))
    print(f"\n{s}:  total packets={c['total']}   PRE-generator={pre}   POST-generation={post}")
    print("   reasons:", {k[7:]:v for k,v in c.items() if k.startswith('reason:')})
    print("   evidence of a generated intent (candidate_id or unit membership):",
          "YES" if cand_ids[s] else "NONE")
    bysym = collections.Counter()
    for (ns,sym,bucket),n in per_sleeve_sym[s].items(): bysym[(ns,sym,bucket)] = n
    for k in sorted(bysym): print(f"     {k[0]:26s} {str(k[1]):10s} {k[2]:4s} {bysym[k]}")

print("\n" + "="*100)
print("ALL SLEEVES: did any intent ever exist?")
print("="*100)
print(f"{'sleeve':38s} {'pkts':>6s} {'PRE':>6s} {'POST':>6s}  intent_evidence")
for s in sorted(per_sleeve, key=lambda x: -per_sleeve[x]['total']):
    c = per_sleeve[s]
    pre  = sum(v for k,v in c.items() if k.startswith("PRE:"))
    post = sum(v for k,v in c.items() if k.startswith("POST:"))
    print(f"{s:38s} {c['total']:6d} {pre:6d} {post:6d}  {'YES' if cand_ids[s] else 'NONE'}")
