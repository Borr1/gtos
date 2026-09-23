"""Data loaders for the beta AI-integrity audit.

Three T7 simulation corpora:
- XAUUSD: research/t7_live_simulation/all_results_jan_apr10.json (2100)
- NAS100: merge of 5 slices under research/t3_1_eurusd_nas100_validation_2026-04-19/nas100_slice_{1..5}/NAS100_t7_simulation.json
- EURUSD: research/t7_live_simulation/EURUSD_t7_simulation.json (~2280)

Raw responses are markdown-fenced JSON (```json\n...\n```).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")

XAUUSD_PATH = ROOT / "research/t7_live_simulation/all_results_jan_apr10.json"
EURUSD_PATH = ROOT / "research/t7_live_simulation/EURUSD_t7_simulation.json"
NAS100_SLICE_PATHS = [
    ROOT / f"research/t3_1_eurusd_nas100_validation_2026-04-19/nas100_slice_{i}/NAS100_t7_simulation.json"
    for i in range(1, 6)
]

MALFORMED_LOG = ROOT / "shadow_logs/malformed_responses.jsonl"
CAND_FEATURES_LOG = ROOT / "shadow_logs/candidate_features_log.jsonl"
PROMPT_PATH = ROOT / "src/prompts/primary_analyzer_prompt.py"


_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?|\n?```\s*$", re.MULTILINE)


def parse_raw_response(s):
    """Parse raw_response which may be fenced markdown."""
    if s is None:
        return None
    if isinstance(s, dict):
        return s
    if not isinstance(s, str):
        return None
    # Strip fences
    cleaned = _FENCE_RE.sub("", s.strip()).strip()
    if not cleaned:
        return None
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # try to find first { ... last }
        i = cleaned.find("{")
        j = cleaned.rfind("}")
        if i == -1 or j == -1:
            return None
        try:
            return json.loads(cleaned[i : j + 1])
        except json.JSONDecodeError:
            return None


def load_xauusd():
    with open(XAUUSD_PATH, "r", encoding="utf-8") as f:
        d = json.load(f)
    return d["results"]


def load_eurusd():
    with open(EURUSD_PATH, "r", encoding="utf-8") as f:
        d = json.load(f)
    if isinstance(d, dict) and "results" in d:
        return d["results"]
    return d


def load_nas100():
    all_records = []
    for p in NAS100_SLICE_PATHS:
        if not p.exists():
            print(f"WARN: missing {p}")
            continue
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and "results" in d:
            all_records.extend(d["results"])
        elif isinstance(d, list):
            all_records.extend(d)
    # De-duplicate by (candle_time, kill_zone) preserving first
    seen = set()
    out = []
    for r in all_records:
        key = (r.get("candle_time"), r.get("kill_zone"))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def inspect(records, label):
    from collections import Counter
    decisions = Counter([r.get("decision") for r in records])
    print(f"\n=== {label} ===")
    print(f"  total: {len(records)}")
    for k, v in decisions.most_common():
        print(f"    {k}: {v}")


if __name__ == "__main__":
    xau = load_xauusd()
    eur = load_eurusd()
    nas = load_nas100()
    inspect(xau, "XAUUSD")
    inspect(eur, "EURUSD")
    inspect(nas, "NAS100")
