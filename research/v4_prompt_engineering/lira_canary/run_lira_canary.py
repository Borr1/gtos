#!/usr/bin/env python3
"""LIRA canary runner — apples-to-apples to V3 baseline on production 60 fixtures.

Mirrors `scripts/canary_test.py` closely but:
  - Replaces each fixture's pre-rendered V3 `system_prompt` with a freshly
    built LIRA system prompt at the same instrument precision / sl_min.
  - Sends raw text response through `schema_adapter.adapt_variant_response`
    so we capture both LIRA-native parse outcomes and the V3-equivalent
    PrimaryAnalysisOutput each row would produce in production.
  - Compares LIRA decision against the saved V3 baseline (same 60-fixture
    file the production canary already validates).
  - Emits a per-fixture JSONL log + a summary JSON for the report.

Sonnet 4.6 effort=max temperature=0 — production AI config.

This script does NOT modify production canary code. It is a read-only
LIRA-shaped wrapper that invokes the schema adapter from the dp4_lira
artifacts.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

# Use the main repo as project root (LIRA artifacts + canary fixtures live there)
_PROJECT_ROOT = Path(r"C:/Users/MSI/Documents/ai-trading-agent")
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env", override=True)

from anthropic import Anthropic

from research.v4_prompt_engineering.dp4_lira.prompt_lira import (
    build_system_prompt as lira_build_system_prompt,
)
from research.v4_prompt_engineering.dp4_lira.schema_adapter import (
    adapt_variant_response,
)

# ---------------------------------------------------------------------------
# Per-instrument config table (mirrors agent_config.yaml `instruments` overrides)
# ---------------------------------------------------------------------------
_INSTRUMENT_CONFIG = {
    "XAUUSD":   {"price_format": ".2f",  "sl_absolute_min": 5.0},
    "GBPUSD":   {"price_format": ".5f",  "sl_absolute_min": 0.0003},
    "EURUSD":   {"price_format": ".5f",  "sl_absolute_min": 0.0003},
    "NAS100":   {"price_format": ".1f",  "sl_absolute_min": 30.0},
    "XAGUSD":   {"price_format": ".3f",  "sl_absolute_min": 0.1},
    "USDJPY":   {"price_format": ".3f",  "sl_absolute_min": 0.085},
    "US30_cash":{"price_format": ".2f",  "sl_absolute_min": 27.0},
    "GBPJPY":   {"price_format": ".3f",  "sl_absolute_min": 0.118},
    "NZDUSD":   {"price_format": ".5f",  "sl_absolute_min": 0.00043},
}

_DEFAULT_KILL_ZONES = {
    "london": {"start_utc": "07:00", "end_utc": "10:30"},
    "ny":     {"start_utc": "13:00", "end_utc": "17:00"},
}

FIXTURES_DIR = _PROJECT_ROOT / "scripts" / "canary_fixtures"
BASELINE_PATH = FIXTURES_DIR / "baseline.json"

OUT_DIR = Path(r"C:/Users/MSI/Documents/ai-trading-agent/.claude/worktrees/agent-a8ef8c0ae63fc0069/research/v4_prompt_engineering/lira_canary")
PER_FIXTURE_LOG = OUT_DIR / "per_fixture.jsonl"
SUMMARY_PATH = OUT_DIR / "summary.json"

MODEL = "claude-sonnet-4-6"
EFFORT = "max"
MAX_CONCURRENT = 5

# Borderline tier prefix (mirrors canary_test.py).
BORDERLINE_PREFIX = "borderline_"


def _infer_symbol(fixture: dict) -> str:
    """Infer instrument symbol from fixture metadata.

    Newer fixtures carry an explicit `symbol` field. Older ones (the
    london_/ny_ XAUUSD set + 4 borderline_xauusd_* fixtures) do not — those
    are all XAUUSD and their pre-rendered system_prompt has 'EXACTLY 2
    decimal' as a deterministic tell.
    """
    sym = fixture.get("symbol")
    if sym:
        return sym
    label = fixture.get("label", "")
    if "xauusd" in label.lower():
        return "XAUUSD"
    # Conservative fallback: extract from label
    for s in _INSTRUMENT_CONFIG:
        if s.lower() in label.lower():
            return s
    # Final guess: read decimals tag from V3 system prompt (always set)
    sp = fixture.get("system_prompt", "")
    m = re.search(r"EXACTLY (\d+) decimal", sp)
    if m:
        dp = int(m.group(1))
        if dp == 2:
            return "XAUUSD"
        if dp == 5:
            return "EURUSD"
        if dp == 3:
            return "USDJPY"
        if dp == 1:
            return "NAS100"
    return "XAUUSD"  # ultra-safe default


def build_lira_system_prompt(symbol: str) -> str:
    """Build a LIRA system prompt for the given symbol using its config."""
    sym_cfg = _INSTRUMENT_CONFIG.get(symbol, _INSTRUMENT_CONFIG["XAUUSD"])
    cfg = {
        "market": {"symbol": symbol, "kill_zones": _DEFAULT_KILL_ZONES},
        "risk": {"sl_absolute_min": sym_cfg["sl_absolute_min"]},
        "prompt": {"price_format": sym_cfg["price_format"]},
    }
    return lira_build_system_prompt(cfg)


def load_fixtures() -> list[dict]:
    manifest = json.load(open(FIXTURES_DIR / "manifest.json"))
    fixtures = []
    for label in manifest["fixtures"]:
        fp = FIXTURES_DIR / f"{label}.json"
        if fp.exists():
            fixtures.append(json.load(open(fp)))
    return fixtures


def load_baseline() -> dict:
    return json.load(open(BASELINE_PATH))


def extract_decision(text: str) -> str:
    """Extract decision from a JSON response. Mirrors canary_test.extract_decision."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t[3:]
        if t.endswith("```"):
            t = t[:-3]
        t = t.strip()
    try:
        d = json.loads(t)
        decision = (d.get("decision") or "").upper()
        if decision in ("CANDIDATE", "NO_TRADE"):
            return decision
    except json.JSONDecodeError:
        pass
    upper = t.upper()
    if '"CANDIDATE"' in upper:
        return "CANDIDATE"
    if '"NO_TRADE"' in upper:
        return "NO_TRADE"
    return "UNKNOWN"


async def call_one(
    client: Anthropic,
    fixture: dict,
    semaphore: asyncio.Semaphore,
) -> dict:
    label = fixture["label"]
    symbol = _infer_symbol(fixture)
    kill_zone = fixture.get("kill_zone") or "london"
    candle_time = fixture.get("candle_time") or ""
    user_msg = fixture["user_message"]

    # Build LIRA system prompt at the right precision for this instrument
    lira_sp = build_lira_system_prompt(symbol)

    async with semaphore:
        try:
            loop = asyncio.get_event_loop()
            create_kwargs = dict(
                model=MODEL,
                max_tokens=2000,
                temperature=0,
                system=lira_sp,
                messages=[{"role": "user", "content": user_msg}],
            )
            if EFFORT:
                create_kwargs["output_config"] = {"effort": EFFORT}
            response = await loop.run_in_executor(
                None,
                lambda: client.messages.create(**create_kwargs),
            )
            raw_text = response.content[0].text
            decision = extract_decision(raw_text)

            # Run LIRA -> PrimaryAnalysisOutput adapter
            adapter_report, pa_obj = adapt_variant_response(
                raw_text, candle_time, kill_zone, "lira",
            )
            adapter_ok = pa_obj is not None and adapter_report.get("decision") not in (
                "PARSE_ERROR", "ERROR",
            )

            return {
                "label": label,
                "symbol": symbol,
                "decision": decision,
                "raw_text": raw_text,
                "adapter_report": adapter_report,
                "adapter_ok": adapter_ok,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        except Exception as exc:
            return {
                "label": label,
                "symbol": symbol,
                "decision": "ERROR",
                "raw_text": "",
                "adapter_report": {"decision": "ERROR", "error": str(exc)},
                "adapter_ok": False,
                "error": str(exc),
            }


async def run_all(fixtures: list[dict]) -> list[dict]:
    client = Anthropic()
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    return await asyncio.gather(*[call_one(client, f, sem) for f in fixtures])


def main():
    parser = argparse.ArgumentParser(description="LIRA canary runner")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only run first N fixtures (smoke)")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fixtures = load_fixtures()
    if args.limit:
        fixtures = fixtures[: args.limit]
    print(f"LIRA canary -- {len(fixtures)} fixtures, model={MODEL}, effort={EFFORT}")

    baseline = load_baseline()
    baseline_map = {r["label"]: r for r in baseline["results"]}
    print(f"V3 baseline file: {BASELINE_PATH}")
    print(f"V3 baseline created: {baseline['created_at']} (model={baseline['model']}, effort={baseline.get('effort')})")
    print("-" * 60)

    start = time.time()
    results = asyncio.run(run_all(fixtures))
    elapsed = time.time() - start

    # Per-fixture log + comparison rows
    rows = []
    baseline_flips = 0
    borderline_flips = 0
    parse_errors = 0
    adapter_failures = 0
    candidate_to_no_trade = 0
    no_trade_to_candidate = 0

    with open(PER_FIXTURE_LOG, "w") as f_log:
        for r in results:
            label = r["label"]
            tier = "borderline" if label.startswith(BORDERLINE_PREFIX) else "baseline"
            v3_dec = (baseline_map.get(label) or {}).get("decision", "UNKNOWN")
            lira_dec = r["decision"]
            flipped = (v3_dec in ("CANDIDATE", "NO_TRADE") and lira_dec in ("CANDIDATE", "NO_TRADE")
                       and v3_dec != lira_dec)
            if flipped:
                if tier == "baseline":
                    baseline_flips += 1
                else:
                    borderline_flips += 1
                if v3_dec == "CANDIDATE" and lira_dec == "NO_TRADE":
                    candidate_to_no_trade += 1
                elif v3_dec == "NO_TRADE" and lira_dec == "CANDIDATE":
                    no_trade_to_candidate += 1

            if lira_dec == "UNKNOWN" or r["decision"] == "ERROR":
                parse_errors += 1
            if not r.get("adapter_ok", False):
                adapter_failures += 1

            row = {
                "label": label,
                "tier": tier,
                "symbol": r["symbol"],
                "v3_decision": v3_dec,
                "lira_decision": lira_dec,
                "flipped": flipped,
                "adapter_ok": r.get("adapter_ok", False),
                "adapter_decision": (r.get("adapter_report") or {}).get("decision"),
                "no_trade_reason": (r.get("adapter_report") or {}).get("no_trade_reason"),
                "setup_grade": (r.get("adapter_report") or {}).get("setup_grade"),
                "input_tokens": r.get("input_tokens"),
                "output_tokens": r.get("output_tokens"),
                "raw_preview": (r.get("raw_text") or "")[:200],
                "error": r.get("error"),
            }
            rows.append(row)
            f_log.write(json.dumps(row) + "\n")

    total_input = sum(r.get("input_tokens", 0) or 0 for r in results)
    total_output = sum(r.get("output_tokens", 0) or 0 for r in results)

    # Tiered thresholds (mirror canary_test.derive_thresholds)
    n_baseline = sum(1 for r in rows if r["tier"] == "baseline")
    n_borderline = sum(1 for r in rows if r["tier"] == "borderline")
    baseline_threshold = max(0, n_baseline - 1)
    borderline_threshold = -(-(3 * n_borderline) // 4)  # ceil(0.75 * N)
    baseline_matches = n_baseline - baseline_flips
    borderline_matches = n_borderline - borderline_flips
    baseline_pass = baseline_matches >= baseline_threshold
    borderline_pass = borderline_matches >= borderline_threshold

    if baseline_flips <= 1 and borderline_flips <= n_borderline - borderline_threshold:
        verdict = "PASS"
    elif baseline_flips <= 3 and borderline_flips <= 22:
        verdict = "MARGINAL"
    else:
        verdict = "FAIL"

    summary = {
        "model": MODEL,
        "effort": EFFORT,
        "elapsed_seconds": round(elapsed, 1),
        "fixtures_total": len(rows),
        "baseline_total": n_baseline,
        "borderline_total": n_borderline,
        "baseline_matches": baseline_matches,
        "borderline_matches": borderline_matches,
        "baseline_threshold": baseline_threshold,
        "borderline_threshold": borderline_threshold,
        "baseline_pass": baseline_pass,
        "borderline_pass": borderline_pass,
        "baseline_flips": baseline_flips,
        "borderline_flips": borderline_flips,
        "candidate_to_no_trade": candidate_to_no_trade,
        "no_trade_to_candidate": no_trade_to_candidate,
        "parse_errors": parse_errors,
        "adapter_failures": adapter_failures,
        "input_tokens": total_input,
        "output_tokens": total_output,
        "verdict": verdict,
    }
    with open(SUMMARY_PATH, "w") as f_sum:
        json.dump(summary, f_sum, indent=2)

    print("-" * 60)
    print(f"Verdict: {verdict}")
    print(f"Baseline tier: {baseline_matches}/{n_baseline} match (>= {baseline_threshold}) -> {'PASS' if baseline_pass else 'FAIL'}")
    print(f"Borderline tier: {borderline_matches}/{n_borderline} match (>= {borderline_threshold}) -> {'PASS' if borderline_pass else 'FAIL'}")
    print(f"Flips: baseline={baseline_flips}, borderline={borderline_flips}")
    print(f"  CANDIDATE->NO_TRADE: {candidate_to_no_trade}")
    print(f"  NO_TRADE->CANDIDATE: {no_trade_to_candidate}")
    print(f"Parse errors: {parse_errors}")
    print(f"Adapter failures: {adapter_failures}")
    print(f"Tokens: {total_input:,} in + {total_output:,} out")
    print(f"Time: {elapsed:.1f}s")
    print(f"Per-fixture log: {PER_FIXTURE_LOG}")
    print(f"Summary: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
