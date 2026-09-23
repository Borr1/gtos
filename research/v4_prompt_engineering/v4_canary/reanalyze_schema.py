#!/usr/bin/env python3
"""Re-analyze schema enforcement using a more robust JSON extractor.

The original `extract_no_trade_reason` in run_v4_canary.py inherits the
V3 canary's fence-strip logic which doesn't handle V4's BIAS PRECEDENCE
preamble before the JSON. This script re-runs schema analysis on the
saved raw responses with a fallback regex extractor.
"""
import json
import re
import sys
from pathlib import Path

OUT_DIR = Path(__file__).parent
RAW = OUT_DIR / "v4_canary_raw_responses.jsonl"
SUMMARY = OUT_DIR / "v4_canary_results.json"

V4_NTR_ENUM = {
    "c1_failed", "c2_m15_opposing", "c3_direction_mismatch",
    "no_qualifying_h1_poi", "self_check_failed", "wrong_side_sl",
    "degenerate_trade_parameters", "ai_output_malformed",
}


def robust_extract_json(text: str) -> dict | None:
    """Extract embedded JSON object from text containing preamble and fences.

    Tries: direct parse, fence-stripped parse, regex-find first {...} block.
    """
    # Strategy 1: regex-find the first balanced JSON-looking block
    # Find first '{' that has a matching '}' and parses cleanly
    candidates = []
    # Simple: find ```json ... ``` block first
    fence_match = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fence_match:
        candidates.append(fence_match.group(1))
    # Fall back: find first { through last }
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        candidates.append(text[first:last+1])
    for c in candidates:
        try:
            return json.loads(c)
        except json.JSONDecodeError:
            continue
    return None


def main():
    rows = []
    with open(RAW, "r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))

    ntr_distribution = {}
    enum_violations = []
    schema_failures = []
    no_trade_count = 0

    for r in rows:
        if r["decision"] != "NO_TRADE":
            continue
        no_trade_count += 1
        data = robust_extract_json(r["raw_response"])
        if data is None:
            schema_failures.append({"label": r["label"], "issue": "JSON_unparseable"})
            ntr_distribution["JSON_FAIL"] = ntr_distribution.get("JSON_FAIL", 0) + 1
            continue
        ntr = data.get("no_trade_reason")
        if ntr is None:
            schema_failures.append({"label": r["label"], "issue": "no_trade_reason_missing_or_null"})
            ntr_distribution["null"] = ntr_distribution.get("null", 0) + 1
            continue
        ntr_distribution[ntr] = ntr_distribution.get(ntr, 0) + 1
        if ntr not in V4_NTR_ENUM:
            enum_violations.append({"label": r["label"], "no_trade_reason": ntr})

    print(f"Total NO_TRADE responses: {no_trade_count}")
    print()
    print("Robust no_trade_reason distribution:")
    for k, v in sorted(ntr_distribution.items()):
        flag = "OK" if k in V4_NTR_ENUM else ("schema-FAIL" if k in ("null", "JSON_FAIL") else "OFF-ENUM")
        print(f"  {k!r:35s} -> {v:3d}  [{flag}]")
    print()
    print(f"Schema enforcement failures: {len(schema_failures)}")
    for sf in schema_failures:
        print(f"  - {sf['label']:55s} | {sf['issue']}")
    print()
    print(f"Off-enum reasons (V4 should reject these): {len(enum_violations)}")
    for v in enum_violations:
        print(f"  - {v['label']:55s} | {v['no_trade_reason']}")

    # Update summary file
    summary = json.load(open(SUMMARY))
    summary["robust_schema_analysis"] = {
        "no_trade_responses": no_trade_count,
        "ntr_distribution": ntr_distribution,
        "schema_enforcement_failures": schema_failures,
        "ntr_enum_violations_robust": enum_violations,
    }
    with open(SUMMARY, "w") as f:
        json.dump(summary, f, indent=2)
    print()
    print(f"Updated summary: {SUMMARY}")


if __name__ == "__main__":
    main()
