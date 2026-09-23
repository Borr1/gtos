#!/usr/bin/env python3
"""LANE 3 step 1: validate the cache reproduction against the sealed reads,
and characterise the label/censoring surface by order type."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import funnel_lib as F

OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane3/out")
OUT.mkdir(exist_ok=True)
SEALED = Path(
    "/Users/borr/GTOSActive/worktrees/three-sleeve-restatement-20260811/docs/audits/"
    "fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority"
)

report = {}
allrows = {}
for month in F.MONTHS:
    rows = F.load_month(month)
    allrows[month] = rows
    sel, disp, death = F.run_funnel(rows)
    stat = Counter(r["lifecycle_label_status"] for r in rows)
    by_ot = defaultdict(Counter)
    for r in rows:
        by_ot[r["proposed_order_type"]][r["state"] or "CENSORED"] += 1
    # NO_FILL terminal_net_r distribution
    nofill = [float(r.get("terminal_net_r") or 0.0) for r in rows if r["state"] == "NO_FILL"]
    report[month] = {
        "occurrences": len(rows),
        "eligible": sum(1 for r in rows if F.is_eligible(r)[0]),
        "resolved_eligible": sum(1 for r in rows if F.is_eligible(r)[0] and r["resolved"]),
        "dispositions_reproduced": disp,
        "portfolio_reproduced": F.portfolio(sel),
        "lifecycle_label_status_counts": dict(sorted(stat.items())),
        "state_by_order_type": {k: dict(sorted(v.items())) for k, v in sorted(by_ot.items())},
        "no_fill_terminal_net_r": {
            "n": len(nofill),
            "min": min(nofill) if nofill else None,
            "max": max(nofill) if nofill else None,
            "mean": (sum(nofill) / len(nofill)) if nofill else None,
            "nonzero": sum(1 for v in nofill if v != 0.0),
        },
    }
    print(json.dumps({month: {k: report[month][k] for k in
                              ("occurrences", "eligible", "resolved_eligible",
                               "dispositions_reproduced")}}, sort_keys=True), flush=True)

# --- sealed comparison ---
sealed = {}
for fn, months in (
    ("FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json", ["feb"]),
    ("APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json", ["apr", "may"]),
    ("JUNE_JULY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json", ["jun", "jul"]),
):
    d = json.load(open(SEALED / fn))
    tot = Counter()
    for _day, dd in d["days"].items():
        for k, v in dd["policies"]["market_top_abstain"]["dispositions"].items():
            tot[k] += v
    sealed[fn] = {
        "months": months,
        "sealed_dispositions": dict(sorted(tot.items())),
        "sealed_pooled": {p: {k: d["pooled"][p].get(k) for k in
                              ("selected", "resolved", "censored", "actual_net_r", "worst_case_net_r")}
                          for p in ("market_top_abstain", "mixed", "market_rerank")},
        "sealed_population": d.get("population"),
        "reproduced_dispositions_sum": dict(sorted(
            sum((Counter(report[m]["dispositions_reproduced"]) for m in months), Counter()).items())),
        "reproduced_pooled_abstain": {
            "selected": sum(report[m]["portfolio_reproduced"]["selected"] for m in months),
            "resolved": sum(report[m]["portfolio_reproduced"]["resolved"] for m in months),
            "censored": sum(report[m]["portfolio_reproduced"]["censored"] for m in months),
            "actual_net_r": round(sum(report[m]["portfolio_reproduced"]["actual_net_r"] for m in months), 6),
            "worst_case_net_r": round(sum(report[m]["portfolio_reproduced"]["worst_case_net_r"] for m in months), 6),
        },
        "reproduced_population": {
            "occurrences": sum(report[m]["occurrences"] for m in months),
            "eligible_occurrences": sum(report[m]["eligible"] for m in months),
            "resolved_eligible_occurrences": sum(report[m]["resolved_eligible"] for m in months),
        },
    }

(OUT / "step1_validation.json").write_text(
    json.dumps({"per_month": report, "sealed_comparison": sealed}, indent=1, sort_keys=True))
print(json.dumps(sealed, indent=1, sort_keys=True))
