"""Deeper hallucination analysis:
- AI's daily_bias.direction vs pipeline bias (mismatches = AI contradicting deterministic bias)
- AI's h1_setup.poi_price_level vs AI's entry_price (mismatches = self-contradiction geometry)
- poi_identified=True but no OB cited near entry (hallucinated POI)
- The L2 reason strings ALREADY tally "poi_cited_no_matching_OB" — but let me enumerate for XAUUSD/EURUSD.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from load_data import load_eurusd, load_nas100, load_xauusd, parse_raw_response

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
OUT = ROOT / "research/b_deep_audit_2026-04-19/phase1/_beta_scratch"


def check_ai_pipeline_bias_contradiction(records, instrument):
    """The pipeline injects a deterministic bias into the prompt's additional_context.
    The AI then reports its own daily_bias.direction in reasoning. Check mismatch rate.
    """
    mismatch = 0
    agree = 0
    ai_ranging = 0
    no_parse = 0
    for r in records:
        parsed = r.get("_parsed")
        if parsed is None:
            no_parse += 1
            continue
        pipeline_bias = r.get("bias")  # bullish|bearish|no_bias
        reasoning = parsed.get("reasoning", {}) if isinstance(parsed, dict) else {}
        if not isinstance(reasoning, dict):
            continue
        daily = reasoning.get("daily_bias", {}) if isinstance(reasoning, dict) else {}
        ai_dir = daily.get("direction") if isinstance(daily, dict) else None
        if pipeline_bias is None or ai_dir is None:
            continue
        if ai_dir == "ranging":
            ai_ranging += 1
        elif pipeline_bias == ai_dir:
            agree += 1
        else:
            mismatch += 1
    return {
        "instrument": instrument,
        "agree": agree,
        "mismatch": mismatch,
        "ai_ranging_while_pipeline_directional": ai_ranging,
        "no_parse": no_parse,
    }


def ob_cited_no_match_tally(records, instrument):
    """L2 'h1_poi_exists' reason family explicitly enumerates cited-POI not found cases.
    Enumerate those for cross-instrument hallucination severity."""
    pat = re.compile(
        r"h1_poi_exists: AI cites H1 POI at ([\d.]+) but no unmitigated H1 OB found"
    )
    pat_poi_false = re.compile(
        r"h1_poi_exists: AI reports poi_identified=False"
    )
    bad_cite = 0
    poi_false = 0
    total_h1_poi = 0
    for r in records:
        if r.get("decision") != "REJECTED_L2":
            continue
        reason = r.get("l2_reason", "")
        if reason.startswith("h1_poi_exists"):
            total_h1_poi += 1
            if pat.search(reason):
                bad_cite += 1
            elif pat_poi_false.search(reason):
                poi_false += 1
    return {
        "instrument": instrument,
        "total_h1_poi_exists_rejects": total_h1_poi,
        "hallucinated_poi_cited_at_price_no_ob_there": bad_cite,
        "claimed_no_poi_but_mso_had_one": poi_false,
    }


def entry_in_ob_direction_check(records, instrument):
    """L2 'entry_in_ob' reason enumerates cases where AI's entry is outside the OB zone
    the verifier found nearest. This is AI self-contradiction in the h1_setup vs trade_parameters."""
    pat = re.compile(
        r"entry_in_ob: Entry ([\d.]+) is outside OB zone ([\d.]+)-([\d.]+)"
    )
    total = 0
    parseable = 0
    outside_pct_sum = 0.0
    magnitudes = []
    for r in records:
        if r.get("decision") != "REJECTED_L2":
            continue
        reason = r.get("l2_reason", "")
        if not reason.startswith("entry_in_ob"):
            continue
        total += 1
        m = pat.search(reason)
        if not m:
            continue
        parseable += 1
        entry, zl, zh = float(m.group(1)), float(m.group(2)), float(m.group(3))
        # distance outside zone (if inside, 0)
        if zl <= entry <= zh:
            dist = 0.0
        else:
            dist = min(abs(entry - zl), abs(entry - zh))
        zone_width = zh - zl
        if zone_width > 0:
            outside_pct_sum += dist / zone_width
            magnitudes.append(dist / zone_width)
    return {
        "instrument": instrument,
        "total_entry_in_ob_rejects": total,
        "parseable": parseable,
        "mean_dist_in_zone_widths": (sum(magnitudes) / len(magnitudes)) if magnitudes else 0,
        "median_dist_in_zone_widths": (sorted(magnitudes)[len(magnitudes) // 2]) if magnitudes else 0,
        "max_dist_in_zone_widths": max(magnitudes) if magnitudes else 0,
    }


def poi_self_contradict_tally(records, instrument):
    """Explicit L2 rejection for poi_self_contradict_False."""
    n = sum(
        1 for r in records
        if r.get("decision") == "REJECTED_L2"
        and r.get("l2_reason", "").startswith("poi_self_contradict")
    )
    return {"instrument": instrument, "poi_self_contradict_rejects": n}


def model_used_check(records, instrument):
    """Exhaustive model_used tally with bogus-flag."""
    BOGUS = {"claude-opus-4-5", "claude-opus-4-1-20250805", "claude-opus-4-5-20250715",
             "gpt-4.1", "gpt-4o", "structural-bias-evaluator-v1", "ob-retest-analyzer-v1",
             "anthropic/claude-opus-4", "structural-bias-evaluator"}
    VALID = {"claude-sonnet-4-6", "claude-sonnet-4-6-20250907", "claude-sonnet-4.5",
             "claude-sonnet-4-5-20250929"}
    from collections import defaultdict
    tally = Counter()
    bogus_n = 0
    valid_n = 0
    unknown_n = 0
    for r in records:
        parsed = r.get("_parsed")
        if parsed is None:
            continue
        mu = parsed.get("model_used")
        if mu is None:
            continue
        tally[mu] += 1
        if mu in BOGUS:
            bogus_n += 1
        elif mu in VALID:
            valid_n += 1
        else:
            unknown_n += 1
    return {
        "instrument": instrument,
        "model_used_tally": dict(tally),
        "bogus_hallucinated": bogus_n,
        "correctly_named_sonnet": valid_n,
        "unclassified_strings": unknown_n,
    }


def main():
    def tag(recs):
        for r in recs:
            r["_parsed"] = parse_raw_response(r.get("raw_response"))
        return recs

    xau = tag(load_xauusd())
    eur = tag(load_eurusd())
    nas = tag(load_nas100())

    out = {}
    for label, recs in (("XAUUSD", xau), ("EURUSD", eur), ("NAS100", nas)):
        out[label] = {
            "model_used": model_used_check(recs, label),
            "ai_pipeline_bias_disagreement": check_ai_pipeline_bias_contradiction(recs, label),
            "h1_poi_hallucinations": ob_cited_no_match_tally(recs, label),
            "entry_in_ob_magnitudes": entry_in_ob_direction_check(recs, label),
            "poi_self_contradict": poi_self_contradict_tally(recs, label),
        }

    with open(OUT / "hallucination_detail.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)

    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
