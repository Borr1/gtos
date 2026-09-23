#!/usr/bin/env python3
"""Inspect V4 canary flip responses — extract BIAS PRECEDENCE preamble + key reasoning."""
import json
import sys
from pathlib import Path

OUT_DIR = Path(__file__).parent
RAW = OUT_DIR / "v4_canary_raw_responses.jsonl"

flip_labels = [
    "borderline_gbpusd_20260317T0800_fx_precision",
    "borderline_xauusd_20260227T0945_no_trade",
    "london_no_trade_c1_c2_fail_2026jan07",
    "london_no_trade_c1_fail_h1_bias_2026jan07",
    "london_no_trade_c2_fail_m15_opposing_2026jan23",
    "ny_candidate_2026mar10_loss",
    "ny_candidate_2026mar24_win",
    "ny_no_trade_c1_fail_h1_bias_2026jan27",
]

with open(RAW, "r", encoding="utf-8") as f:
    by_label = {json.loads(l)["label"]: json.loads(l) for l in f}

for label in flip_labels:
    r = by_label[label]
    text = r["raw_response"]
    print("=" * 70)
    print("FLIP:", label)
    print("decision:", r["decision"], "| ntr:", r.get("no_trade_reason"))
    print()
    # Extract preamble (everything before first JSON)
    json_start = text.find("```json")
    if json_start == -1:
        json_start = text.find("{")
    preamble = text[:json_start].strip()
    if preamble:
        print("--- PREAMBLE ---")
        print(preamble[:800])
        print()
    # Extract reasoning.daily_bias.explanation if present
    try:
        json_text = text[json_start:].lstrip("`").lstrip()
        if json_text.startswith("json"):
            json_text = json_text[4:].lstrip()
        # Find JSON end
        end = json_text.rfind("}")
        if end > 0:
            json_text = json_text[:end+1]
        data = json.loads(json_text)
        bias = data.get("reasoning", {}).get("daily_bias", {})
        c1 = data.get("frameworks_evaluated", {}).get("ob_retest", {}).get("reason", "")
        cc = data.get("confidence_computation", "")
        print("--- bias.explanation ---")
        print(bias.get("explanation", "(none)")[:400])
        print("--- ob_retest.reason ---")
        print(c1[:300])
        print("--- confidence_computation ---")
        print(cc[:300])
    except Exception as e:
        print(f"(JSON parse failed: {e})")
    print()
