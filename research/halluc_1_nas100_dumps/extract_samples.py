"""HALLUC-1 forensic extraction.

Builds 10 sample dumps from NAS100 hallucinated CANDIDATEs on 2026-04-27.

Data sources:
- knowledge_base/live_evaluations/NAS100/2026-04-27.jsonl (summary fields)
- logs/nas100.log (live SYSTEM demotion messages with full L2 reason)

Note: full system_prompt + raw_response are NOT persisted by current arch
because trade_capture only fires on CANDIDATE, and the inconsistent_pois
guard demotes CANDIDATE → NO_TRADE BEFORE trade_capture is called. Sample
dumps document everything that IS persisted, plus the prompt template
excerpts and config values that drive the hallucination.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]  # research/halluc_1_nas100_dumps/extract_samples.py -> repo root
EVAL_FILE = REPO / "knowledge_base" / "live_evaluations" / "NAS100" / "2026-04-27.jsonl"
LOG_FILE = REPO / "logs" / "nas100.log"
OUT_DIR = REPO / "research" / "halluc_1_nas100_dumps" / "samples"

OUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_log_demotions() -> list[dict]:
    """Parse NAS100 log for SYSTEM demotion lines."""
    pattern = re.compile(
        r"^(?P<wall_ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*?"
        r"CANDIDATE has inconsistent POI references . demoting to NO_TRADE: "
        r"poi_price_level (?P<poi>\S+) maps to OB \[(?P<low>[\d.]+), (?P<high>[\d.]+)\] "
        r"\(touches=(?P<touches>\d+)\), but: (?P<reasons>.*)$"
    )
    out = []
    for line in LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        m = pattern.search(line)
        if m:
            out.append({
                "wall_ts": m.group("wall_ts"),
                "poi_price_level": float(m.group("poi")),
                "ob_low": float(m.group("low")),
                "ob_high": float(m.group("high")),
                "ob_touches": int(m.group("touches")),
                "l2_failure_reasons": m.group("reasons"),
            })
    return out


def parse_log_api_calls() -> list[dict]:
    """Parse httpx POST anthropic responses to find API call timing per candle."""
    pat = re.compile(
        r"^(?P<wall_ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*?HTTP Request: POST https://api\.anthropic\.com.*?\"(?P<status>HTTP/[\d.]+ \d+)"
    )
    out = []
    for line in LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        m = pat.search(line)
        if m:
            out.append({"wall_ts": m.group("wall_ts"), "status": m.group("status")})
    return out


def load_evals() -> list[dict]:
    out = []
    with EVAL_FILE.open(encoding="utf-8") as f:
        for line in f:
            out.append(json.loads(line))
    return out


def find_eval_for_demotion(evals: list[dict], demotion: dict) -> dict | None:
    """Match log demotion (wall clock) → eval JSONL entry (UTC timestamp).

    Wall clock = UTC + 8 (Asia/Singapore-ish, per system clock when log was
    written). Live evals stamp the actual UTC `timestamp` field.
    """
    # Wall clock format: 2026-04-27 15:19:53,633
    # Eval timestamp:    2026-04-27T07:19:53.637075+00:00
    # Difference: ~8h (UTC+8 server local) — match by HH:MM:SS proximity.
    wall = demotion["wall_ts"]
    # Try matching by best HH:MM:SS within +/-2 sec
    wall_hms = wall[11:19]  # "15:19:53"
    wall_h = int(wall_hms[:2])
    utc_h = (wall_h - 8) % 24
    target_hms = f"{utc_h:02d}:{wall_hms[3:]}"  # "07:19:53"
    best = None
    best_dt = 999
    for e in evals:
        et = e.get("timestamp", "")
        ehms = et[11:19]
        if ehms[3:] == target_hms[3:]:  # MM:SS match
            # Compute second diff
            ws = int(wall_hms[6:8])
            es = int(ehms[6:8])
            diff = abs(ws - es)
            if diff < best_dt:
                best = e
                best_dt = diff
    return best


def categorize_hypothesis(demotion: dict) -> str:
    """Label which hypothesis explains this sample."""
    poi = demotion["poi_price_level"]
    low = demotion["ob_low"]
    high = demotion["ob_high"]
    reasons = demotion["l2_failure_reasons"]

    # Extract entry_price from "entry_price 27262.2 outside ..."
    m = re.search(r"entry_price ([\d.]+) outside", reasons)
    if m:
        entry = float(m.group(1))
        # Distance from OB high (LONG case)
        delta = entry - high
        # Match against rounding error: high.1f rounded
        rounded_high = round(high, 1)
        if abs(entry - rounded_high) < 0.005 and 0 < delta < 0.1:
            return "H2_index_pricing_precision"  # the AI rounded OB high to .1f
    return "H_other"


def build_sample(idx: int, demotion: dict, evals: list[dict],
                 system_prompt_excerpt: str) -> dict:
    eval_entry = find_eval_for_demotion(evals, demotion)
    hypothesis = categorize_hypothesis(demotion)
    reasons = demotion["l2_failure_reasons"]
    # Parse entry_price + sl from reasons
    em = re.search(r"entry_price ([\d.]+)", reasons)
    sm = re.search(r"stop_loss ([\d.]+)", reasons)
    entry_price = float(em.group(1)) if em else None
    stop_loss = float(sm.group(1)) if sm else None

    sample = {
        "sample_id": idx,
        "candle_time_utc": eval_entry.get("timestamp", "?") if eval_entry else "?",
        "wall_ts": demotion["wall_ts"],
        "symbol": "NAS100",
        "kill_zone": eval_entry.get("kill_zone", "?") if eval_entry else "?",

        # Forensic core data
        "system_prompt_excerpt": system_prompt_excerpt,
        "MSO_excerpt_note": (
            "Full MSO not persisted (NO_TRADE path skips trade_capture). "
            "Live evaluation summary fields shown below capture analyzer's "
            "report. The MSO _format_tf rendering uses `.1f` precision for "
            "NAS100 (config:agent_config.yaml:685), so the AI saw the OB as "
            f"'{demotion['ob_high']:.1f}-{demotion['ob_low']:.1f}' (rendered) "
            f"while guard_candidate_inconsistent_pois reads the underlying "
            f"floats {demotion['ob_high']}-{demotion['ob_low']} from "
            "mso.timeframes[H1].order_blocks[i]."
        ),
        "live_eval_summary": {
            "decision": eval_entry.get("decision") if eval_entry else None,
            "no_trade_reason": eval_entry.get("no_trade_reason") if eval_entry else None,
            "framework": eval_entry.get("framework") if eval_entry else None,
            "h1_poi_identified": eval_entry.get("h1_poi_identified") if eval_entry else None,
            "h1_poi_type": eval_entry.get("h1_poi_type") if eval_entry else None,
            "h1_zone": eval_entry.get("h1_zone") if eval_entry else None,
            "h1_causing_event": eval_entry.get("h1_causing_event") if eval_entry else None,
            "setup_grade": eval_entry.get("setup_grade") if eval_entry else None,
            "confidence_score": eval_entry.get("confidence_score") if eval_entry else None,
            "reasoning_word_count": eval_entry.get("reasoning_word_count") if eval_entry else None,
            "reasoning_price_count": eval_entry.get("reasoning_price_count") if eval_entry else None,
            "overall_reasoning": eval_entry.get("overall_reasoning", "")[:1500] if eval_entry else None,
            "spread": eval_entry.get("spread") if eval_entry else None,
        },
        "AI_full_response_note": (
            "Full raw response NOT persisted by current arch — trade_capture "
            "(orchestrator.py:889) only fires on `decision == CANDIDATE`, and "
            "guard_candidate_inconsistent_pois (primary_analyzer.py:836) flips "
            "CANDIDATE→NO_TRADE BEFORE the orchestrator sees the result. The "
            "AI's emitted entry_price + stop_loss + poi_price_level are "
            "reconstructed from the SYSTEM demotion message embedded into "
            "overall_reasoning, plus the live_evaluations h1_setup summary."
        ),
        "AI_emitted_fields": {
            "decision_pre_demotion": "CANDIDATE",
            "framework": eval_entry.get("framework") if eval_entry else None,
            "direction": "LONG",  # all 13 cases LONG bullish
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "poi_price_level": demotion["poi_price_level"],
            "h1_poi_type": eval_entry.get("h1_poi_type") if eval_entry else None,
            "setup_grade": eval_entry.get("setup_grade") if eval_entry else None,
            "confidence_score": eval_entry.get("confidence_score") if eval_entry else None,
        },
        "L2_reason": "ai_output_inconsistent_pois (guard_candidate_inconsistent_pois)",
        "L2_full_failure_reasons": reasons,
        "OB_list_from_MSO_h1_matched": {
            "low": demotion["ob_low"],
            "high": demotion["ob_high"],
            "touches": demotion["ob_touches"],
            "rendered_in_prompt_as": f"{demotion['ob_high']:.1f}-{demotion['ob_low']:.1f}",
        },
        "OB_referenced_by_AI": {
            "poi_price_level": demotion["poi_price_level"],
            "midpoint_of_matched_OB": (demotion["ob_low"] + demotion["ob_high"]) / 2,
            "matches_matched_OB": demotion["ob_low"] <= demotion["poi_price_level"] <= demotion["ob_high"],
        },
        "precision_audit": {
            "instrument_price_format": ".1f",
            "underlying_OB_high": demotion["ob_high"],
            "rendered_OB_high_in_prompt": round(demotion["ob_high"], 1),
            "AI_emitted_entry_price": entry_price,
            "delta_entry_minus_high_underlying": (entry_price - demotion["ob_high"]) if entry_price else None,
            "delta_entry_minus_high_rendered": (entry_price - round(demotion["ob_high"], 1)) if entry_price else None,
            "is_entry_equal_to_rendered_high": (entry_price == round(demotion["ob_high"], 1)) if entry_price else None,
            "ob_high_last_digit_geq_5": (round(demotion["ob_high"] * 100) % 10) >= 5,
        },
        "sl_audit": ({
            "AI_emitted_stop_loss": stop_loss,
            "underlying_OB_low": demotion["ob_low"],
            "delta_sl_minus_low": stop_loss - demotion["ob_low"],
            "sl_inside_OB": demotion["ob_low"] < stop_loss < demotion["ob_high"],
            "sl_below_OB_low": stop_loss < demotion["ob_low"],
            "note": (
                "Pattern B cases: SL is INSIDE the OB by 14-21 points (hundreds "
                "of ticks above OB low). This is NOT a precision rounding issue "
                "— it's a separate AI-side error where the model uses the H1 "
                "swing low (the basis described in TRADE PARAMETERS) instead of "
                "OB low. The 0.25xATR(14) buffer math checks out: e.g. ATR~80, "
                "buffer=20, swing-low~27024, sl=27003.5 — but ob_low=26988.25, "
                "so sl ends up inside the OB body. Geometry-wise valid (SL < "
                "entry), but `guard_candidate_inconsistent_pois` enforces "
                "stricter SL-beyond-OB-low for LONG."
            ) if stop_loss and stop_loss > demotion["ob_low"] else None,
        }) if stop_loss else {"AI_emitted_stop_loss": None, "note": "SL not parsed"},
        "hypothesis_label": hypothesis,
        "hypothesis_evidence": (
            f"AI emitted entry_price={entry_price}; underlying OB.high="
            f"{demotion['ob_high']}; rendered_in_prompt={round(demotion['ob_high'], 1)}; "
            f"AI's emit MATCHES rendered value (={entry_price == round(demotion['ob_high'], 1)}). "
            f"Strict guard: {entry_price} <= {demotion['ob_high']} = "
            f"{entry_price <= demotion['ob_high'] if entry_price else 'N/A'}. "
            f"Mathematical impossibility: when ob_high last decimal >=5, ROUND-HALF-UP "
            f"to .1f produces a value > underlying."
        ),
        "token_usage_note": (
            "Live evaluation summary does not log token usage per call. "
            "primary_analyzer._last_usage is in-memory and overwritten per "
            "candle. Inferred from prompt size: system prompt ~26-30k tokens "
            "(cached); user message MSO ~3-5k tokens; AI response observed "
            "~70 words → output well under max_tokens=2000 budget. No "
            "evidence of max_tokens truncation. Note: the system prompt "
            "itself is the cache hit — `cache_control: ttl=1h` block."
        ),
        "max_tokens_truncation_inferred": False,
        "thinking_budget_exhausted_inferred": False,
    }
    return sample


def main():
    print("Parsing log demotions...")
    demotions = parse_log_demotions()
    print(f"Found {len(demotions)} SYSTEM demotion events in nas100.log")

    print("Loading evals...")
    evals = load_evals()
    print(f"Loaded {len(evals)} live_evaluation entries")

    print("Loading prompt excerpt...")
    prompt_text = (REPO / "src" / "prompts" / "primary_analyzer_prompt.py").read_text(encoding="utf-8")
    # Extract only the TRADE PARAMETERS + SELF-CHECK + PRECISION sections
    trade_params_idx = prompt_text.find("## TRADE PARAMETERS")
    self_check_idx = prompt_text.find("## BEFORE RETURNING")
    end_idx = prompt_text.find("CANDIDATE response: under 600")
    excerpt = prompt_text[trade_params_idx:end_idx + 200] if trade_params_idx > 0 else "[excerpt fetch failed]"

    # Pick 10 distinct samples from 13 demotions:
    # Strategy: take first 4 (Pattern A — entry-only error) + 6 of the 9 Pattern B
    # (entry + SL error). Sample evenly across times of day.
    pattern_a = [d for d in demotions if "stop_loss" not in d["l2_failure_reasons"]]
    pattern_b = [d for d in demotions if "stop_loss" in d["l2_failure_reasons"]]
    print(f"Pattern A (entry-only): {len(pattern_a)}")
    print(f"Pattern B (entry+SL):   {len(pattern_b)}")

    chosen = pattern_a[:4]  # all 4 of Pattern A
    # take 6 Pattern B evenly spaced
    if pattern_b:
        step = max(1, len(pattern_b) // 6)
        chosen.extend(pattern_b[::step][:6])
    chosen = chosen[:10]

    print(f"\nWriting {len(chosen)} samples...")
    for i, d in enumerate(chosen, 1):
        sample = build_sample(i, d, evals, excerpt)
        out_path = OUT_DIR / f"sample_{i}.json"
        out_path.write_text(json.dumps(sample, indent=2), encoding="utf-8")
        print(f"  wrote {out_path.name}: {sample['hypothesis_label']}")

    # Hypothesis distribution CSV
    csv_path = OUT_DIR.parent / "hypothesis_distribution.csv"
    counts = {}
    for d in demotions:
        h = categorize_hypothesis(d)
        counts[h] = counts.get(h, 0) + 1

    with csv_path.open("w", encoding="utf-8") as f:
        f.write("hypothesis_label,count,fraction_of_13\n")
        for h, c in sorted(counts.items(), key=lambda kv: -kv[1]):
            f.write(f"{h},{c},{c/13:.3f}\n")
    print(f"\nWrote hypothesis distribution: {csv_path}")
    print(f"Distribution: {counts}")


if __name__ == "__main__":
    main()
