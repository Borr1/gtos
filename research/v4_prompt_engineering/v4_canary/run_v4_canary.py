#!/usr/bin/env python3
"""V4 canary runner — sweep production 60-fixture suite under V4 DRAFT prompt.

Loads V4 DRAFT (research/v4_prompt_engineering/primary_analyzer_prompt_v4_DRAFT.py),
rebuilds the system_prompt for each fixture using V4's build_system_prompt,
preserves user_message + any "## Static Context" tail from V3 fixture, sends
to API at temperature=0 effort=max, compares to V3 baseline at
scripts/canary_fixtures/baseline.json.

Outputs:
  - v4_canary_raw_responses.jsonl  (per-fixture full response)
  - v4_canary_results.json         (decision-level comparison)
  - V4_CANARY_REPORT.md            (executive summary, written separately)

This file is in worktree only and does NOT touch production.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
# .env lives in main repo (not worktree); try worktree first, then main repo
_env_paths = [
    _PROJECT_ROOT / ".env",
    Path("C:/Users/MSI/Documents/ai-trading-agent/.env"),
]
for _ep in _env_paths:
    if _ep.exists():
        load_dotenv(_ep, override=True)
        break

from anthropic import Anthropic
import yaml

from src.utils.config import apply_instrument_overrides

FIXTURES_DIR = _PROJECT_ROOT / "scripts" / "canary_fixtures"
V4_DRAFT_PATH = _PROJECT_ROOT / "research" / "v4_prompt_engineering" / "primary_analyzer_prompt_v4_DRAFT.py"
BASELINE_PATH = FIXTURES_DIR / "baseline.json"
CONFIG_PATH = _PROJECT_ROOT / "config" / "agent_config.yaml"
OUT_DIR = _PROJECT_ROOT / "research" / "v4_prompt_engineering" / "v4_canary"

MAX_CONCURRENT = 5
STATIC_CONTEXT_MARKER = "## Static Context (D1/H4/Session)"

# Sonnet input/output pricing (Apr 2026 published rates)
PRICE_IN_PER_MTOK = 3.00
PRICE_OUT_PER_MTOK = 15.00


def load_v4_module():
    """Import V4 DRAFT as a fresh module (no name collision with src.prompts)."""
    spec = importlib.util.spec_from_file_location(
        "v4_prompt_draft", V4_DRAFT_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def detect_symbol(fixture: dict) -> str:
    """Detect instrument symbol for a fixture.

    Priority: explicit `symbol` field > label prefix match > XAUUSD default.
    The 16 legacy fixtures (borderline_xauusd_*, london_*, ny_*) without
    a symbol field are all XAUUSD by historical inspection (see
    update_canary_system_prompts_v2.py).
    """
    sym = fixture.get("symbol")
    if sym:
        return sym

    label = fixture.get("label", "")
    label_lower = label.lower()
    for s in ("xauusd", "eurusd", "gbpusd", "usdjpy", "gbpjpy",
              "us30_cash", "nas100"):
        if s in label_lower:
            # Normalize back to canonical case
            return {"xauusd":"XAUUSD","eurusd":"EURUSD","gbpusd":"GBPUSD",
                    "usdjpy":"USDJPY","gbpjpy":"GBPJPY",
                    "us30_cash":"US30_cash","nas100":"NAS100"}[s]
    # Legacy london_*/ny_* are all XAUUSD
    if label_lower.startswith(("london_", "ny_")):
        return "XAUUSD"
    return "XAUUSD"  # safest fallback


def reconstruct_static_context(old_system_prompt: str) -> str:
    """Extract the static context block (if present) from V3 system_prompt."""
    if STATIC_CONTEXT_MARKER not in old_system_prompt:
        return ""
    idx = old_system_prompt.index(STATIC_CONTEXT_MARKER)
    return old_system_prompt[idx:]


def build_v4_system_prompt(v4_mod, symbol: str, raw_config: dict) -> str:
    """Build V4 system prompt for `symbol` using current config + overrides."""
    sym_config = apply_instrument_overrides(raw_config, symbol)
    return v4_mod.build_system_prompt(sym_config)


def extract_decision(response_text: str) -> str:
    """Extract CANDIDATE/NO_TRADE from response — copy of canary_test logic."""
    text = response_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    try:
        data = json.loads(text)
        decision = data.get("decision", "").upper()
        if decision in ("CANDIDATE", "NO_TRADE"):
            return decision
    except json.JSONDecodeError:
        pass
    upper = text.upper()
    if '"CANDIDATE"' in upper:
        return "CANDIDATE"
    if '"NO_TRADE"' in upper:
        return "NO_TRADE"
    return "UNKNOWN"


def extract_no_trade_reason(response_text: str) -> str | None:
    """Extract no_trade_reason field from JSON response (V4 schema check)."""
    text = response_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    try:
        data = json.loads(text)
        return data.get("no_trade_reason")
    except json.JSONDecodeError:
        return None


def classify_tier(label: str) -> str:
    return "borderline" if label.startswith("borderline_") else "baseline"


async def call_fixture(
    client,
    fixture: dict,
    v4_system_prompt: str,
    model: str,
    semaphore: asyncio.Semaphore,
    effort: str,
):
    label = fixture["label"]
    user_msg = fixture["user_message"]

    async with semaphore:
        try:
            loop = asyncio.get_event_loop()
            create_kwargs = dict(
                model=model,
                max_tokens=2000,
                temperature=0,
                system=v4_system_prompt,
                messages=[{"role": "user", "content": user_msg}],
            )
            if effort:
                create_kwargs["output_config"] = {"effort": effort}
            response = await loop.run_in_executor(
                None,
                lambda: client.messages.create(**create_kwargs),
            )
            raw_text = response.content[0].text
            decision = extract_decision(raw_text)
            ntr = extract_no_trade_reason(raw_text)
            return {
                "label": label,
                "decision": decision,
                "no_trade_reason": ntr,
                "raw_response": raw_text,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "error": None,
            }
        except Exception as exc:
            return {
                "label": label,
                "decision": "ERROR",
                "no_trade_reason": None,
                "raw_response": str(exc)[:500],
                "input_tokens": 0,
                "output_tokens": 0,
                "error": str(exc),
            }


async def run_all(client, prepared_fixtures, model, effort):
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    return await asyncio.gather(*[
        call_fixture(client, fx, sp, model, sem, effort)
        for fx, sp in prepared_fixtures
    ])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="claude-sonnet-4-6")
    p.add_argument("--effort", default="max")
    p.add_argument("--budget", type=float, default=10.0,
                   help="Hard USD cap; abort if estimate or actual exceeds")
    p.add_argument("--limit", type=int, default=None,
                   help="Smoke-test: process only first N fixtures")
    args = p.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"V4 CANARY — model={args.model} effort={args.effort} budget=${args.budget:.2f}")
    print(f"V4 DRAFT path: {V4_DRAFT_PATH}")
    print(f"Baseline:      {BASELINE_PATH}")
    print("-" * 70)

    # Load V3 baseline
    if not BASELINE_PATH.exists():
        print(f"ERROR: V3 baseline missing at {BASELINE_PATH}")
        sys.exit(2)
    baseline = json.load(open(BASELINE_PATH))
    baseline_map = {r["label"]: r for r in baseline["results"]}

    # Load fixtures via manifest
    manifest = json.load(open(FIXTURES_DIR / "manifest.json"))
    fixtures = []
    for label in manifest["fixtures"]:
        path = FIXTURES_DIR / f"{label}.json"
        if path.exists():
            fixtures.append(json.load(open(path)))

    if args.limit:
        fixtures = fixtures[:args.limit]
        print(f"LIMIT: processing first {args.limit} fixtures only")

    print(f"Loaded {len(fixtures)} fixtures")

    # Load V4 + raw config
    v4_mod = load_v4_module()
    raw_config = yaml.safe_load(open(CONFIG_PATH))
    print(f"V4 module loaded: {v4_mod.__file__}")

    # Build per-fixture V4 system prompt
    prepared = []
    symbol_counts = {}
    for fx in fixtures:
        symbol = detect_symbol(fx)
        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        v4_head = build_v4_system_prompt(v4_mod, symbol, raw_config)
        # Preserve V3's static context tail if present
        tail = reconstruct_static_context(fx.get("system_prompt", ""))
        if tail:
            v4_full = v4_head + "\n\n" + tail
        else:
            v4_full = v4_head
        prepared.append((fx, v4_full))
    print(f"Symbol distribution: {symbol_counts}")
    print()

    # Cost estimate before run
    avg_in = sum(len(sp) // 4 + len(fx.get("user_message", "")) // 4
                  for fx, sp in prepared) / len(prepared)
    est_in_tokens = sum(len(sp) // 4 + len(fx.get("user_message", "")) // 4
                        for fx, sp in prepared)
    est_out_tokens = len(prepared) * 800
    est_cost = (est_in_tokens / 1_000_000) * PRICE_IN_PER_MTOK + \
               (est_out_tokens / 1_000_000) * PRICE_OUT_PER_MTOK
    print(f"Estimated tokens: ~{est_in_tokens:,} in + ~{est_out_tokens:,} out")
    print(f"Estimated cost:   ~${est_cost:.2f} (budget ${args.budget:.2f})")
    if est_cost > args.budget * 1.5:
        print(f"ABORT: estimated cost {est_cost:.2f} exceeds budget by >50%")
        sys.exit(3)

    print()
    print("Starting API calls...")
    client = Anthropic()

    start = time.time()
    results = asyncio.run(run_all(client, prepared, args.model, args.effort))
    elapsed = time.time() - start

    # Compute cost
    total_in = sum(r["input_tokens"] for r in results)
    total_out = sum(r["output_tokens"] for r in results)
    actual_cost = (total_in / 1_000_000) * PRICE_IN_PER_MTOK + \
                  (total_out / 1_000_000) * PRICE_OUT_PER_MTOK

    # Compare against V3 baseline
    flips = []
    enum_violations = []
    errors = []
    parse_failures = []
    by_tier_match = {"baseline": [0, 0], "borderline": [0, 0]}  # [matches, total]
    by_tier_flips = {"baseline": [], "borderline": []}

    V4_NTR_ENUM = {
        "c1_failed", "c2_m15_opposing", "c3_direction_mismatch",
        "no_qualifying_h1_poi", "self_check_failed", "wrong_side_sl",
        "degenerate_trade_parameters", "ai_output_malformed",
    }

    for r in results:
        label = r["label"]
        tier = classify_tier(label)
        bl = baseline_map.get(label)
        if r["decision"] == "ERROR":
            errors.append(r)
            by_tier_match[tier][1] += 1
            continue
        if r["decision"] == "UNKNOWN":
            parse_failures.append(r)
            by_tier_match[tier][1] += 1
            continue

        if not bl:
            print(f"  WARN: {label} not in V3 baseline — skipping comparison")
            continue

        match = (r["decision"] == bl["decision"])
        by_tier_match[tier][1] += 1
        if match:
            by_tier_match[tier][0] += 1
        else:
            flip = {
                "label": label,
                "tier": tier,
                "v3_baseline_decision": bl["decision"],
                "v4_decision": r["decision"],
                "direction": (
                    "CAND→NO_TRADE" if bl["decision"] == "CANDIDATE" and r["decision"] == "NO_TRADE"
                    else "NO_TRADE→CAND" if bl["decision"] == "NO_TRADE" and r["decision"] == "CANDIDATE"
                    else f"{bl['decision']}→{r['decision']}"
                ),
                "v4_no_trade_reason": r.get("no_trade_reason"),
            }
            flips.append(flip)
            by_tier_flips[tier].append(flip)

        # V4 schema check: any NO_TRADE response with off-allow-list
        # no_trade_reason is a schema violation
        ntr = r.get("no_trade_reason")
        if r["decision"] == "NO_TRADE" and ntr and ntr not in V4_NTR_ENUM:
            enum_violations.append({
                "label": label,
                "no_trade_reason": ntr,
            })

    # PASS criteria from brief
    baseline_total = by_tier_match["baseline"][1]
    baseline_matches = by_tier_match["baseline"][0]
    baseline_flips = baseline_total - baseline_matches
    borderline_total = by_tier_match["borderline"][1]
    borderline_matches = by_tier_match["borderline"][0]
    borderline_flips = borderline_total - borderline_matches

    if baseline_flips <= 1 and borderline_flips <= 11:
        verdict = "PASS"
    elif baseline_flips <= 3 and borderline_flips <= 22:
        verdict = "MARGINAL"
    else:
        verdict = "FAIL"

    print()
    print("=" * 70)
    print(f"V4 CANARY RESULTS — {len(results)} fixtures, {elapsed:.1f}s elapsed")
    print(f"Baseline tier:   {baseline_matches}/{baseline_total} match  ({baseline_flips} flips)")
    print(f"Borderline tier: {borderline_matches}/{borderline_total} match  ({borderline_flips} flips)")
    print(f"Errors:          {len(errors)}")
    print(f"Parse failures:  {len(parse_failures)}")
    print(f"NTR enum vio:    {len(enum_violations)}")
    print(f"Total flips:     {len(flips)}")
    print(f"Tokens: {total_in:,} in + {total_out:,} out")
    print(f"Cost:   ${actual_cost:.2f} actual (${args.budget:.2f} budget)")
    print()
    print(f"VERDICT: {verdict}")
    print("=" * 70)

    if actual_cost > args.budget:
        print(f"WARNING: actual cost ${actual_cost:.2f} exceeded budget ${args.budget:.2f}")

    # Save raw responses
    raw_path = OUT_DIR / "v4_canary_raw_responses.jsonl"
    with open(raw_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"Raw saved: {raw_path}")

    # Save structured comparison
    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": args.model,
        "effort": args.effort,
        "v4_draft_path": str(V4_DRAFT_PATH.relative_to(_PROJECT_ROOT)),
        "v3_baseline_at": baseline.get("created_at"),
        "v3_baseline_model": baseline.get("model"),
        "v3_baseline_effort": baseline.get("effort"),
        "fixture_count": len(results),
        "elapsed_seconds": round(elapsed, 1),
        "tokens_in": total_in,
        "tokens_out": total_out,
        "actual_cost_usd": round(actual_cost, 4),
        "budget_usd": args.budget,
        "tier_results": {
            "baseline": {"matches": baseline_matches, "total": baseline_total, "flips": baseline_flips},
            "borderline": {"matches": borderline_matches, "total": borderline_total, "flips": borderline_flips},
        },
        "verdict": verdict,
        "flips": flips,
        "errors": errors,
        "parse_failures": parse_failures,
        "ntr_enum_violations": enum_violations,
        "symbol_distribution": symbol_counts,
    }
    summary_path = OUT_DIR / "v4_canary_results.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved: {summary_path}")

    return 0 if verdict == "PASS" else (1 if verdict == "MARGINAL" else 2)


if __name__ == "__main__":
    sys.exit(main())
