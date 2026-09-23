#!/usr/bin/env python3
"""l12: scan the decision-path source for haircut/floor/cap/default constants.

Emits a JSON register. Prints only counts.
"""
import json
import os
import re
import sys

ROOT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"

FILES = [
    "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
    "src/components/selector_v4.py",
    "src/components/broker_net_cost_engine.py",
    "src/research/moonshot_scheduler_v4_best_trade_allocator.py",
    "src/components/poi_execution_lifecycle.py",
    "src/components/probability_debate_v4.py",
    "src/components/ultimate_candidate_package.py",
    "src/components/learned_edge_layer_v4.py",
    "src/components/executable_value_semantics.py",
    "src/research/dynamic_execution_policy.py",
    "src/components/dynamic_target_stop_geometry_v4.py",
    "src/costs/spread_model.py",
    "src/research/moonshot_default_off_policy_router.py",
    "src/components/same_symbol_lifecycle_v4.py",
    "src/components/candidate_geometry.py",
    "src/components/confidence_scorer.py",
]

FLOAT = re.compile(r"(?<![\w.])(?:0\.\d+|1\.\d+|[2-9]\.\d+|\d{1,3}\.\d+)(?![\w.])")
KIND_PATTERNS = [
    ("MULT_HAIRCUT", re.compile(r"\*\s*(?:0\.\d+)\b")),
    ("MULT_BOOST", re.compile(r"\*\s*(?:1\.[1-9]\d*|[2-9]\.\d+)\b")),
    ("FLOOR_MAX", re.compile(r"\bmax\(\s*[^)]*\d\.\d")),
    ("CAP_MIN", re.compile(r"\bmin\(\s*[^)]*\d\.\d")),
    ("CLAMP", re.compile(r"clamp|_clamp|bound\(|_bounded")),
    ("KEYWORD", re.compile(
        r"haircut|discount|penalt|shrink|damp|floor|ceiling|multiplier|"
        r"fallback|DEFAULT_|default_|_default\b|weight|scale_factor|factor\b|"
        r"conservat|degrade|derate|throttle|attenuat", re.I)),
]


def main():
    out = {}
    total = 0
    for rel in FILES:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            continue
        rows = []
        with open(p, "r", errors="replace") as fh:
            for i, line in enumerate(fh, 1):
                s = line.rstrip("\n")
                stripped = s.strip()
                if stripped.startswith("#"):
                    continue
                if not FLOAT.search(s):
                    continue
                kinds = [k for k, rx in KIND_PATTERNS if rx.search(s)]
                if not kinds:
                    continue
                rows.append({
                    "line": i,
                    "kinds": kinds,
                    "floats": sorted(set(FLOAT.findall(s))),
                    "text": stripped[:220],
                })
        out[rel] = rows
        total += len(rows)
    dest = os.path.join(
        ROOT,
        "docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/"
        "l12_CONSTANT_SCAN_V1.json")
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)
    for rel, rows in out.items():
        print("%-90s %5d" % (rel.split("/")[-1], len(rows)))
    print("TOTAL", total)
    print("WROTE", dest)


if __name__ == "__main__":
    main()
