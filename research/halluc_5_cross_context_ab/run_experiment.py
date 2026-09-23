"""HALLUC-5 — A/B test: cross_instrument_context block presence.

Goal: turn HALLUC-4's observational finding (Apr 14 GBPUSD CI block disabled →
XAU citation rate dropped 31.2% → 0%) into an experimental test.

Approach:
  - Sample 12 GBPUSD historical CANDIDATE trade records.
  - For each, replay through Sonnet 4.6 effort=max twice:
      A (control): exact production prompt (no CI block) — what was actually sent.
      B (treatment): same prompt + cross_instrument_context block injected
                     (mirrors pre-Apr-14 production behavior).
  - Measure per variant:
      * decision (CANDIDATE vs NO_TRADE)
      * rationale: cites XAU/gold/macro?
      * poi_price_level: aligns with GBPUSD OB list or XAU price band?
      * token usage / cost

Cost cap: $10 USD HARD. Aborts and emits partial results if exceeded.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import anthropic

# ─────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]
TR_BASE = REPO_ROOT / "knowledge_base" / "trade_records" / "GBPUSD"
OUT_DIR = Path(__file__).resolve().parent

MODEL = "claude-sonnet-4-6"
EFFORT = "max"
MAX_TOKENS = 2000
COST_CAP_USD = 10.00

# Sonnet 4.6 pricing (per 1M tokens)
PRICE_INPUT = 3.00
PRICE_OUTPUT = 15.00
PRICE_CACHE_READ = 0.30   # ~10% of input
PRICE_CACHE_WRITE_5M = 3.75  # 1.25× input
PRICE_CACHE_WRITE_1H = 6.00  # 2.0× input

# 12 GBPUSD CANDIDATE records spread across days (4-13 → 4-22).
# Picked to maximize date diversity.
SELECTED_RECORDS = [
    "2026-04-13_london_0730.json",
    "2026-04-13_london_1100.json",
    "2026-04-13_ny_1330.json",
    "2026-04-14_london_0730.json",
    "2026-04-14_ny_1400.json",
    "2026-04-15_london_0730.json",
    "2026-04-17_ny_1330.json",
    "2026-04-17_ny_1415.json",
    "2026-04-20_london_0716.json",
    "2026-04-20_ny_1531.json",
    "2026-04-21_london_1015.json",
    "2026-04-22_london_0716.json",
]

# ─────────────────────────────────────────────────────────────────────────
# Synthetic CI block (mirrors format_cross_instrument_context output)
# ─────────────────────────────────────────────────────────────────────────

# We use a BEARISH XAU bias as the test treatment. The hypothesis is that
# this "macro headwind" should bias the AI toward NO_TRADE on LONG GBPUSD
# CANDIDATEs (which is what the production CI block was designed to do).
# Bearish was chosen because the GBPUSD CANDIDATEs in our sample are mostly
# LONG (consistent with the post-Apr-14 production data).
SYNTHETIC_CI_BLOCK_BEARISH = """## Cross-Instrument & Volatility Context
XAUUSD D1 structure: bearish (indicates dollar strong)
Asian session range: 0.00287 = 31% of ADR (normal)

DECISION GUIDANCE:
- If your proposed trade direction CONFLICTS with XAUUSD D1 direction (e.g., you want LONG GBPUSD but gold D1 is bearish), this is a significant macro headwind. Both instruments respond to USD flows. Require exceptionally strong H1+M15 confluence to proceed with a conflicting direction. If confluence is not exceptional, output NO_TRADE.
- If Asian range is narrow (<28% of ADR), the pre-London session built minimal liquidity. Displacement setups in narrow-range environments have historically shown 33% win rate. Require stronger-than-normal displacement quality (>2.5x average body) to proceed.
- If both signals are unfavorable (conflicting direction AND narrow Asian range), output NO_TRADE regardless of other factors."""

# XAU rationale detection patterns (mirrors HALLUC-4 build_audit.py)
XAU_RATIONALE_PATTERNS = [
    re.compile(r"\bXAU(?:USD)?\b", re.I),
    re.compile(r"\bgold\b", re.I),
    re.compile(r"\bdollar\s+(weak|strong|str|wk|flow)", re.I),
    re.compile(r"\bDXY\b", re.I),
    re.compile(r"\busd\s+(weak|strong)", re.I),
    re.compile(r"macro\s+head ?wind", re.I),
    re.compile(r"dollar\s+(weakness|strength)", re.I),
]

# GBPUSD price band — a poi_price outside this is wildly off-instrument
GBPUSD_BAND = (1.0, 2.0)
XAU_BAND = (1500.0, 5500.0)
GBPUSD_OB_TOLERANCE = 0.001005  # 5× equal_level_tolerance


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def calc_cost(usage) -> float:
    """Compute USD cost from response.usage."""
    inp = (getattr(usage, "input_tokens", 0) or 0) / 1_000_000
    out = (getattr(usage, "output_tokens", 0) or 0) / 1_000_000
    cr = (getattr(usage, "cache_read_input_tokens", 0) or 0) / 1_000_000
    cw = (getattr(usage, "cache_creation_input_tokens", 0) or 0) / 1_000_000
    # Trade records cached system blocks at 1h — assume 1h write pricing.
    return (inp * PRICE_INPUT
            + out * PRICE_OUTPUT
            + cr * PRICE_CACHE_READ
            + cw * PRICE_CACHE_WRITE_1H)


def gather_full_rationale(parsed: dict) -> str:
    """Combine all AI rationale fields into one searchable string."""
    parts: list[str] = []
    reasoning = parsed.get("reasoning")
    if isinstance(reasoning, dict):
        for v in reasoning.values():
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, dict):
                for vv in v.values():
                    if isinstance(vv, str):
                        parts.append(vv)
    elif isinstance(reasoning, str):
        parts.append(reasoning)
    for k in ("no_trade_reason", "wait_reason", "overall_reasoning"):
        v = parsed.get(k)
        if isinstance(v, str):
            parts.append(v)
        # also nested
        if isinstance(reasoning, dict):
            v2 = reasoning.get(k)
            if isinstance(v2, str):
                parts.append(v2)
    return " ".join(parts)


def count_xau_hits(text: str) -> int:
    if not text:
        return 0
    return sum(1 for pat in XAU_RATIONALE_PATTERNS if pat.search(text))


def extract_h1_ob_midpoints(mso: dict) -> list[float]:
    """Return list of H1 OB midpoints from MSO."""
    if not mso:
        return []
    tfs = mso.get("timeframes", {}) or {}
    h1 = tfs.get("H1", {}) or {}
    obs = h1.get("order_blocks") or []
    midpoints: list[float] = []
    for ob in obs:
        if not isinstance(ob, dict):
            continue
        mid = ob.get("midpoint")
        if mid is None:
            hi, lo = ob.get("high"), ob.get("low")
            if hi is not None and lo is not None:
                try:
                    mid = (float(hi) + float(lo)) / 2.0
                except (TypeError, ValueError):
                    pass
        if mid is not None:
            try:
                midpoints.append(float(mid))
            except (TypeError, ValueError):
                pass
    return midpoints


def is_aligned_with_ob(price, midpoints: list[float], tol: float) -> bool:
    if not isinstance(price, (int, float)):
        return False
    return any(abs(price - m) <= tol for m in midpoints)


def in_band(price, band: tuple) -> bool:
    if not isinstance(price, (int, float)):
        return False
    return band[0] <= price <= band[1]


def strip_json_fences(s: str) -> str:
    """Best-effort JSON fence stripper."""
    s = s.strip()
    if s.startswith("```"):
        # Find first newline, drop the fence line; drop closing fence
        nl = s.find("\n")
        if nl > 0:
            s = s[nl + 1:]
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()


def parse_response(raw: str) -> dict:
    """Parse AI response JSON; tolerate fences."""
    cleaned = strip_json_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find first { ... } block
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        return {"_parse_error": True, "_raw": cleaned[:1000]}


# ─────────────────────────────────────────────────────────────────────────
# Variant A/B builders
# ─────────────────────────────────────────────────────────────────────────

def build_user_msg_variant_a(record: dict) -> str:
    """Variant A (control): use the exact user message from the trade record.
    All sampled records have CI block ABSENT (post-Apr-14), so this faithfully
    mirrors current production behavior.
    """
    return record["prompt"]["user_message"]


def build_user_msg_variant_b(record: dict) -> str:
    """Variant B (treatment): inject the synthetic CI block into the user
    message at the same location ``build_user_message`` would place it.

    The user message has structure:
      {kb_block}## Dynamic Market Data...
      {dynamic}
      {session_block}{ci_block}{extra_block}
      ## Current Time: ...

    We inject before the "## Current Time:" marker, prefixed with a newline
    (mirroring ``ci_block = f"\\n{cross_instrument_context}\\n"``).
    """
    user_msg = record["prompt"]["user_message"]
    marker = "## Current Time:"
    if marker not in user_msg:
        # Fallback: append at end
        return user_msg + "\n\n" + SYNTHETIC_CI_BLOCK_BEARISH
    pre, _, post = user_msg.partition(marker)
    return f"{pre.rstrip()}\n\n{SYNTHETIC_CI_BLOCK_BEARISH}\n\n{marker}{post}"


# ─────────────────────────────────────────────────────────────────────────
# API caller
# ─────────────────────────────────────────────────────────────────────────

def call_api(client: anthropic.Anthropic, system_prompt: str, user_msg: str) -> dict:
    """Make one API call. Returns dict with raw text + usage + cost."""
    # System prompt cached at 1h TTL (matches production primary_analyzer.py)
    system_blocks = [
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        }
    ]
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system_blocks,
        messages=[{"role": "user", "content": user_msg}],
        output_config={"effort": EFFORT},
        timeout=120,
    )
    raw = response.content[0].text if response.content else ""
    cost = calc_cost(response.usage)
    return {
        "raw_text": raw,
        "input_tokens": getattr(response.usage, "input_tokens", 0),
        "output_tokens": getattr(response.usage, "output_tokens", 0),
        "cache_read_tokens": getattr(response.usage, "cache_read_input_tokens", 0) or 0,
        "cache_create_tokens": getattr(response.usage, "cache_creation_input_tokens", 0) or 0,
        "cost_usd": cost,
        "stop_reason": response.stop_reason,
        "model_returned": getattr(response, "model", None),
    }


# ─────────────────────────────────────────────────────────────────────────
# Per-MSO experiment
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class VariantResult:
    variant: str
    decision: Optional[str] = None
    direction: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    poi_price: Optional[float] = None
    framework: Optional[str] = None
    setup_grade: Optional[str] = None
    no_trade_reason: Optional[str] = None
    rationale: str = ""
    xau_hits: int = 0
    cited_xau: bool = False
    poi_aligned_with_gbpusd_ob: bool = False
    poi_in_gbpusd_band: bool = False
    poi_in_xau_band: bool = False
    parse_error: bool = False
    raw_text_excerpt: str = ""
    usage: dict = field(default_factory=dict)


def run_one_mso(client: anthropic.Anthropic, record: dict, fname: str,
                cumulative_cost: float) -> tuple[VariantResult, VariantResult, float]:
    """Run both variants for one MSO; returns (A, B, new_cumulative_cost)."""
    sys_prompt = record["prompt"]["system_prompt"]
    h1_obs = extract_h1_ob_midpoints(record.get("mso", {}))

    # ── Variant A (control) ───────────────────────────────────────
    user_a = build_user_msg_variant_a(record)
    print(f"  [{fname}] Variant A (control) ...", end=" ", flush=True)
    api_a = call_api(client, sys_prompt, user_a)
    print(f"${api_a['cost_usd']:.4f}")
    cumulative_cost += api_a["cost_usd"]

    parsed_a = parse_response(api_a["raw_text"])
    a = build_variant_result("A", parsed_a, api_a, h1_obs)

    if cumulative_cost >= COST_CAP_USD:
        print(f"  ABORT: cumulative cost ${cumulative_cost:.2f} >= cap ${COST_CAP_USD}")
        # Return B as empty
        b_empty = VariantResult(variant="B", parse_error=True,
                                raw_text_excerpt="ABORTED: cost cap")
        return a, b_empty, cumulative_cost

    # ── Variant B (treatment) ─────────────────────────────────────
    user_b = build_user_msg_variant_b(record)
    print(f"  [{fname}] Variant B (treatment) ...", end=" ", flush=True)
    api_b = call_api(client, sys_prompt, user_b)
    print(f"${api_b['cost_usd']:.4f}")
    cumulative_cost += api_b["cost_usd"]

    parsed_b = parse_response(api_b["raw_text"])
    b = build_variant_result("B", parsed_b, api_b, h1_obs)

    return a, b, cumulative_cost


def build_variant_result(variant: str, parsed: dict, api: dict,
                         h1_obs: list[float]) -> VariantResult:
    if parsed.get("_parse_error"):
        return VariantResult(
            variant=variant,
            parse_error=True,
            raw_text_excerpt=parsed.get("_raw", "")[:400],
            usage={k: api[k] for k in ("input_tokens", "output_tokens",
                                        "cache_read_tokens", "cache_create_tokens",
                                        "cost_usd", "stop_reason", "model_returned")},
        )
    decision = parsed.get("decision")
    tp = parsed.get("trade_parameters") or {}
    direction = tp.get("direction") if isinstance(tp, dict) else None
    entry_price = tp.get("entry_price") if isinstance(tp, dict) else None
    stop_loss = tp.get("stop_loss") if isinstance(tp, dict) else None
    framework = parsed.get("framework")

    reasoning = parsed.get("reasoning") or {}
    setup_grade = reasoning.get("setup_grade") if isinstance(reasoning, dict) else None
    h1_setup = reasoning.get("h1_setup") if isinstance(reasoning, dict) else {}
    poi_price = h1_setup.get("poi_price_level") if isinstance(h1_setup, dict) else None

    no_trade_reason = parsed.get("no_trade_reason")
    full_rationale = gather_full_rationale(parsed)
    xau_hits = count_xau_hits(full_rationale)

    poi_aligned = is_aligned_with_ob(poi_price, h1_obs, GBPUSD_OB_TOLERANCE) if poi_price else False
    poi_in_gbp = in_band(poi_price, GBPUSD_BAND) if poi_price else False
    poi_in_xau = in_band(poi_price, XAU_BAND) if poi_price else False

    return VariantResult(
        variant=variant,
        decision=decision,
        direction=direction,
        entry_price=entry_price,
        stop_loss=stop_loss,
        poi_price=poi_price,
        framework=framework,
        setup_grade=setup_grade,
        no_trade_reason=no_trade_reason,
        rationale=full_rationale[:600],
        xau_hits=xau_hits,
        cited_xau=xau_hits > 0,
        poi_aligned_with_gbpusd_ob=poi_aligned,
        poi_in_gbpusd_band=poi_in_gbp,
        poi_in_xau_band=poi_in_xau,
        parse_error=False,
        raw_text_excerpt=api["raw_text"][:400],
        usage={k: api[k] for k in ("input_tokens", "output_tokens",
                                    "cache_read_tokens", "cache_create_tokens",
                                    "cost_usd", "stop_reason", "model_returned")},
    )


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return 1
    client = anthropic.Anthropic(api_key=api_key, timeout=120)

    print(f"HALLUC-5: A/B test cross_instrument_context block presence")
    print(f"Model: {MODEL}, effort={EFFORT}, max_tokens={MAX_TOKENS}")
    print(f"Cost cap: ${COST_CAP_USD:.2f}")
    print(f"Selected records: {len(SELECTED_RECORDS)} GBPUSD CANDIDATEs")
    print()

    cumulative_cost = 0.0
    results = []
    cost_breakdown = []

    for i, fname in enumerate(SELECTED_RECORDS, 1):
        print(f"[{i}/{len(SELECTED_RECORDS)}] {fname} (cumulative ${cumulative_cost:.4f})")
        fp = TR_BASE / fname
        try:
            with open(fp) as f:
                record = json.load(f)
        except Exception as e:
            print(f"  ERROR loading: {e}")
            continue

        if cumulative_cost >= COST_CAP_USD:
            print(f"  STOP: cost cap reached")
            break

        a, b, cumulative_cost = run_one_mso(client, record, fname, cumulative_cost)

        results.append({
            "fname": fname,
            "candle_time": record.get("metadata", {}).get("candle_time"),
            "kill_zone": record.get("metadata", {}).get("kill_zone"),
            "production_decision": record.get("ai_response", {}).get("decision"),
            "production_direction": (record.get("ai_response", {}).get("trade_parameters") or {}).get("direction"),
            "n_h1_obs": len(extract_h1_ob_midpoints(record.get("mso", {}))),
            "variant_a": a.__dict__,
            "variant_b": b.__dict__,
        })
        cost_breakdown.append({
            "fname": fname,
            "variant": "A",
            **a.usage,
        })
        cost_breakdown.append({
            "fname": fname,
            "variant": "B",
            **b.usage,
        })

        # Save partial after each MSO in case of abort
        write_partial(results, cost_breakdown, cumulative_cost)

    # ── Aggregate ───────────────────────────────────────────────
    summary = aggregate(results)
    summary["cumulative_cost_usd"] = cumulative_cost
    summary["cost_cap_usd"] = COST_CAP_USD
    summary["model"] = MODEL
    summary["effort"] = EFFORT
    summary["n_msos_completed"] = len([r for r in results if not r["variant_b"].get("parse_error")])
    summary["timestamp"] = datetime.now(timezone.utc).isoformat()

    write_outputs(results, cost_breakdown, summary)
    print()
    print(f"=== HALLUC-5 COMPLETE ===")
    print(f"Total cost: ${cumulative_cost:.4f} / ${COST_CAP_USD:.2f}")
    print(f"MSOs run: {summary['n_msos_completed']}/{len(SELECTED_RECORDS)}")
    print(f"Variant A: {summary['variant_a']}")
    print(f"Variant B: {summary['variant_b']}")
    print(f"Decision agreement: {summary['decision_agreement_pct']:.1f}%")
    return 0


def aggregate(results: list) -> dict:
    """Compute aggregate metrics."""
    n = len(results)
    if n == 0:
        return {"_error": "no results"}
    a_decisions = [r["variant_a"].get("decision") for r in results]
    b_decisions = [r["variant_b"].get("decision") for r in results]
    a_xau_cited = [r["variant_a"].get("cited_xau") for r in results]
    b_xau_cited = [r["variant_b"].get("cited_xau") for r in results]

    n_a_cand = sum(1 for d in a_decisions if d == "CANDIDATE")
    n_b_cand = sum(1 for d in b_decisions if d == "CANDIDATE")
    n_a_nt = sum(1 for d in a_decisions if d == "NO_TRADE")
    n_b_nt = sum(1 for d in b_decisions if d == "NO_TRADE")
    n_a_parse = sum(1 for r in results if r["variant_a"].get("parse_error"))
    n_b_parse = sum(1 for r in results if r["variant_b"].get("parse_error"))
    n_a_xau = sum(1 for c in a_xau_cited if c)
    n_b_xau = sum(1 for c in b_xau_cited if c)

    n_agree = sum(1 for a, b in zip(a_decisions, b_decisions) if a == b and a is not None)

    n_a_anchored = sum(
        1 for r in results
        if r["variant_a"].get("poi_in_xau_band") and not r["variant_a"].get("poi_in_gbpusd_band")
    )
    n_b_anchored = sum(
        1 for r in results
        if r["variant_b"].get("poi_in_xau_band") and not r["variant_b"].get("poi_in_gbpusd_band")
    )

    return {
        "n_msos": n,
        "variant_a": {
            "n_candidate": n_a_cand,
            "n_no_trade": n_a_nt,
            "n_parse_error": n_a_parse,
            "candidate_rate_pct": 100.0 * n_a_cand / n if n else 0,
            "n_cited_xau": n_a_xau,
            "xau_citation_rate_pct": 100.0 * n_a_xau / n if n else 0,
            "n_xau_anchored_poi": n_a_anchored,
        },
        "variant_b": {
            "n_candidate": n_b_cand,
            "n_no_trade": n_b_nt,
            "n_parse_error": n_b_parse,
            "candidate_rate_pct": 100.0 * n_b_cand / n if n else 0,
            "n_cited_xau": n_b_xau,
            "xau_citation_rate_pct": 100.0 * n_b_xau / n if n else 0,
            "n_xau_anchored_poi": n_b_anchored,
        },
        "decision_agreement_n": n_agree,
        "decision_agreement_pct": 100.0 * n_agree / n if n else 0,
    }


def write_partial(results, cost_breakdown, cum_cost):
    """Write partial outputs (in case of abort)."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "results_partial.json", "w") as f:
        json.dump({"results": results, "cumulative_cost_usd": cum_cost}, f, indent=2, default=str)


def write_outputs(results: list, cost_breakdown: list, summary: dict):
    """Write final outputs: results.json + per_mso_ab.csv + cost_breakdown.csv."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "results.json", "w") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2, default=str)

    # per-MSO A/B comparison CSV
    with open(OUT_DIR / "per_mso_ab.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "fname", "candle_time", "kill_zone", "production_decision",
            "n_h1_obs",
            "A_decision", "A_direction", "A_framework", "A_setup_grade",
            "A_poi_price", "A_poi_in_gbpusd_band", "A_poi_aligned_with_gbpusd_ob",
            "A_poi_in_xau_band", "A_cited_xau", "A_xau_hits",
            "A_no_trade_reason", "A_parse_error",
            "B_decision", "B_direction", "B_framework", "B_setup_grade",
            "B_poi_price", "B_poi_in_gbpusd_band", "B_poi_aligned_with_gbpusd_ob",
            "B_poi_in_xau_band", "B_cited_xau", "B_xau_hits",
            "B_no_trade_reason", "B_parse_error",
            "decision_changed",
        ])
        for r in results:
            a = r["variant_a"]
            b = r["variant_b"]
            w.writerow([
                r["fname"], r["candle_time"], r["kill_zone"], r["production_decision"],
                r["n_h1_obs"],
                a.get("decision"), a.get("direction"), a.get("framework"), a.get("setup_grade"),
                a.get("poi_price"), a.get("poi_in_gbpusd_band"), a.get("poi_aligned_with_gbpusd_ob"),
                a.get("poi_in_xau_band"), a.get("cited_xau"), a.get("xau_hits"),
                a.get("no_trade_reason"), a.get("parse_error"),
                b.get("decision"), b.get("direction"), b.get("framework"), b.get("setup_grade"),
                b.get("poi_price"), b.get("poi_in_gbpusd_band"), b.get("poi_aligned_with_gbpusd_ob"),
                b.get("poi_in_xau_band"), b.get("cited_xau"), b.get("xau_hits"),
                b.get("no_trade_reason"), b.get("parse_error"),
                a.get("decision") != b.get("decision"),
            ])

    # cost breakdown CSV
    with open(OUT_DIR / "cost_breakdown.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["fname", "variant", "input_tokens", "output_tokens",
                    "cache_read_tokens", "cache_create_tokens", "cost_usd",
                    "stop_reason", "model_returned"])
        for row in cost_breakdown:
            w.writerow([row["fname"], row["variant"],
                        row.get("input_tokens"), row.get("output_tokens"),
                        row.get("cache_read_tokens"), row.get("cache_create_tokens"),
                        row.get("cost_usd"),
                        row.get("stop_reason"), row.get("model_returned")])


if __name__ == "__main__":
    sys.exit(main())
