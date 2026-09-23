#!/usr/bin/env python3
"""Extract raw trade geometry from the five sealed candidate roots."""
import gzip, json, sys, time
from pathlib import Path

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
sys.path.insert(0, str(WT))
from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink

HOLD = Path("/Users/borr/GTOSActive/hermes-evidence-hold-20260727")
ROOTS = {
  "feb": HOLD/"w21-tmp-lab-recovery-20260810/w21-market-top-feb-r2",
  "apr": HOLD/"w21-tmp-lab-recovery-20260810/w21-market-top-aprmay-r3",
  "may": HOLD/"w21-tmp-lab-recovery-20260810/w21-market-top-aprmay-r3",
  "jun": HOLD/"w21-junjul-r4-roots-20260812",
  "jul": HOLD/"w21-junjul-r4-roots-20260812",
}
PREREG = Path("/Users/borr/GTOSActive/worktrees/three-sleeve-restatement-20260811/docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority/JUNE_JULY_MARKET_TOP_CHOICE_PREREG_V1_3.json")
pre = json.loads(PREREG.read_text())
tr = pre["training"]
DAYS = {"feb": tr["february_days"], "apr": tr["april_days"], "may": tr["may_days"]}
for w in pre["validation"]["windows"]:
    DAYS["jun" if w["window_id"]=="june_2026" else "jul"] = w["days"]

FIELDS = ("entry_price","stop_loss","take_profit_1","decision_time_utc",
          "limit_first_expiry_utc","symbol","side","origin_family","trading_day")
T0=time.time()
out = {}
for month, days in DAYS.items():
    root = ROOTS[month]
    n = 0
    rows = []
    for day in days:
        summary = json.loads((root/day/"run_summary.json").read_text())
        sink = ReplayCompactEventSink.open_sealed(
            root=root/day/"compact_events",
            expected_authority_root_sha256=summary["authority_root_sha256"])
        for raw in sink.ledger("missed"):
            rec = {"k": raw["canonical_replay_candidate_instance_key"]}
            for f in FIELDS:
                rec[f] = raw.get(f)
            rows.append(rec); n += 1
        print(json.dumps({"t":round(time.time()-T0,1),"month":month,"day":day,"n":n}), flush=True)
    p = Path(f"geom_{month}.jsonl.gz")
    with gzip.open(p,"wt") as fh:
        for rec in rows: fh.write(json.dumps(rec)+"\n")
    out[month] = n
    print(json.dumps({"t":round(time.time()-T0,1),"month_done":month,"rows":n}), flush=True)
json.dump(out, open("geom_counts.json","w"), indent=1)
print("DONE", out, flush=True)
