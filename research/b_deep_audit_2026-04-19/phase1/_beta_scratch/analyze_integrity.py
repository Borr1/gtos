"""Beta AI-integrity audit — main analyzer.

Deliverables:
1. Hallucination tally (model_used, bias_source, cited OB)
2. Degenerate output rate (entry==SL, entry==TP, SL==TP)
3. L2 gate failure rates by l2_reason (self-contradiction proxies)
4. sl_buffer_applied=0.0 universality check
5. Prompt-blindspot smoke test (MSO keys not in rendered prompt)
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

from load_data import (
    CAND_FEATURES_LOG,
    MALFORMED_LOG,
    PROMPT_PATH,
    load_eurusd,
    load_nas100,
    load_xauusd,
    parse_raw_response,
)

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
OUT = ROOT / "research/b_deep_audit_2026-04-19/phase1/_beta_scratch"
OUT.mkdir(parents=True, exist_ok=True)

EPS = 1e-6


def tag(records):
    """Enrich each record with parsed raw_response and convenience fields."""
    for r in records:
        r["_parsed"] = parse_raw_response(r.get("raw_response"))
    return records


# ── 1. HALLUCINATION TALLY ──────────────────────────────────────────

def hallucination_tally(records, instrument):
    models = Counter()
    bias_sources = Counter()
    has_parse = 0
    bias_non_mso = 0  # bias_source claims a TF that doesn't exist in MSO
    for r in records:
        parsed = r.get("_parsed")
        if parsed is None:
            continue
        has_parse += 1
        mu = parsed.get("model_used")
        if mu is not None:
            models[mu] += 1
        # bias_source captured in the top-level result (set by pipeline) NOT by AI
        bs = r.get("bias_source")
        if bs:
            bias_sources[bs] += 1
    return {
        "instrument": instrument,
        "parseable_raw_response": has_parse,
        "total_records": len(records),
        "model_used_distribution": dict(models),
        "bias_source_distribution": dict(bias_sources),
    }


# ── 2. DEGENERATE OUTPUT RATE ────────────────────────────────────────

def degenerate_analysis(records, instrument):
    """entry==SL, entry==TP, SL==TP within 1e-6 tol.
    Use flat fields (entry_price, stop_loss, take_profit_1) which are the pipeline-
    extracted values (same for NAS100/EURUSD records).
    """
    with_params = 0
    entry_eq_sl = []
    entry_eq_tp = []
    sl_eq_tp = []
    all_three = []
    any_degen = []
    for r in records:
        e = r.get("entry_price")
        sl = r.get("stop_loss")
        tp = r.get("take_profit_1")
        if e is None or sl is None or tp is None:
            continue
        try:
            e, sl, tp = float(e), float(sl), float(tp)
        except (TypeError, ValueError):
            continue
        # Skip zero-init rows (no AI output, pipeline default)
        if e == 0.0 and sl == 0.0 and tp == 0.0:
            continue
        with_params += 1
        a = abs(e - sl) < EPS
        b = abs(e - tp) < EPS
        c = abs(sl - tp) < EPS
        if a:
            entry_eq_sl.append(r)
        if b:
            entry_eq_tp.append(r)
        if c:
            sl_eq_tp.append(r)
        if a and b and c:
            all_three.append(r)
        if a or b or c:
            any_degen.append(r)
    out = {
        "instrument": instrument,
        "records_with_trade_params": with_params,
        "entry_eq_sl": len(entry_eq_sl),
        "entry_eq_tp": len(entry_eq_tp),
        "sl_eq_tp": len(sl_eq_tp),
        "all_three_equal": len(all_three),
        "any_degenerate": len(any_degen),
        "degenerate_pct": (len(any_degen) / with_params * 100) if with_params else 0,
    }
    # Outcome correlation on degenerates (entry_eq_sl subset, since those have well-defined result)
    deg_w = sum(1 for r in any_degen if r.get("outcome") == "WIN")
    deg_l = sum(1 for r in any_degen if r.get("outcome") == "LOSS")
    deg_u = sum(1 for r in any_degen if r.get("outcome") in ("UNFILLED", "UNRESOLVED", "OPEN"))
    deg_r = 0.0
    n_r = 0
    for r in any_degen:
        rm = r.get("r_multiple")
        if rm is not None:
            try:
                deg_r += float(rm)
                n_r += 1
            except (TypeError, ValueError):
                pass
    out["degenerate_W_L_U"] = (deg_w, deg_l, deg_u)
    out["degenerate_total_R"] = deg_r
    out["degenerate_outcomes_resolved"] = deg_w + deg_l
    # By decision
    by_dec = Counter()
    for r in any_degen:
        by_dec[r.get("decision", "?")] += 1
    out["degenerate_by_decision"] = dict(by_dec)
    return out, any_degen


# ── 3. L2 GATE FAILURE RATES ─────────────────────────────────────────

def l2_failure_rates(records, instrument):
    rl2 = [r for r in records if r.get("decision") == "REJECTED_L2"]
    by_reason = Counter()
    by_reason_family = Counter()
    for r in rl2:
        reason = r.get("l2_reason", "<none>")
        by_reason[reason] += 1
        # Bucket into families (reason often has trailing specific detail)
        if reason.startswith("sl_beyond_ob") or reason.startswith("sl_inside_OB") or reason.startswith("sl="):
            family = "sl_beyond_ob/inside_OB"
        elif reason.startswith("poi_self_contradict"):
            family = "poi_self_contradict"
        elif reason.startswith("poi_cited_no_matching_OB"):
            family = "poi_cited_no_matching_OB"
        elif reason.startswith("entry_in_ob"):
            family = "entry_in_ob"
        elif reason.startswith("m15_choch_exists"):
            family = "m15_choch_exists"
        elif "|" in reason:
            family = reason.split("|", 1)[0]
        else:
            family = reason.split(":", 1)[0] if ":" in reason else reason
        by_reason_family[family] += 1

    total = len(rl2)
    pct = {k: (v / total * 100 if total else 0) for k, v in by_reason_family.items()}
    return {
        "instrument": instrument,
        "total_L2_rejects": total,
        "by_reason_family": dict(by_reason_family),
        "by_reason_family_pct": pct,
        "top_20_raw_reasons": dict(by_reason.most_common(20)),
    }


# ── 4. sl_buffer_applied UNIVERSALITY ──────────────────────────────

def sl_buffer_check(records, instrument):
    with_tp = 0
    zero = 0
    nonzero = 0
    missing = 0
    nonzero_samples = []
    for r in records:
        parsed = r.get("_parsed")
        if parsed is None:
            continue
        tp = parsed.get("trade_parameters")
        if tp is None or not isinstance(tp, dict):
            continue
        with_tp += 1
        if "sl_buffer_applied" not in tp:
            missing += 1
            continue
        try:
            v = float(tp["sl_buffer_applied"])
        except (TypeError, ValueError):
            missing += 1
            continue
        if v == 0.0:
            zero += 1
        else:
            nonzero += 1
            if len(nonzero_samples) < 10:
                nonzero_samples.append({
                    "candle_time": r.get("candle_time"),
                    "decision": r.get("decision"),
                    "sl_buffer_applied": v,
                })
    return {
        "instrument": instrument,
        "records_with_trade_parameters_dict": with_tp,
        "sl_buffer_eq_zero": zero,
        "sl_buffer_nonzero": nonzero,
        "sl_buffer_missing": missing,
        "sl_buffer_zero_pct": (zero / with_tp * 100) if with_tp else 0,
        "nonzero_samples": nonzero_samples,
    }


# ── Helper: OB citation mismatch check on a small sample ─────────────

def ob_citation_check(records, instrument, sample_n=30):
    """For records where the parsed raw_response provides poi_price_level,
    check whether it falls near the entry_price (within a fraction of |entry - SL|).
    This is a soft proxy for 'cited OB matches entry geometry'.
    True OB-matching would require the MSO's OB list; that's not embedded in this JSON,
    so we can only do geometric plausibility."""
    out = []
    candidates = [r for r in records if r.get("decision") == "CANDIDATE"]
    for r in candidates[:sample_n]:
        parsed = r.get("_parsed")
        if parsed is None:
            continue
        reasoning = parsed.get("reasoning", {})
        h1 = reasoning.get("h1_setup", {}) if isinstance(reasoning, dict) else {}
        poi_price = h1.get("poi_price_level") or 0
        e = r.get("entry_price") or 0
        sl = r.get("stop_loss") or 0
        if not e or not sl or not poi_price:
            continue
        risk = abs(e - sl)
        if risk == 0:
            continue
        # poi_price is the OB midpoint; |entry - poi_price| should typically be within risk distance
        plausible = abs(float(e) - float(poi_price)) <= 1.5 * risk
        out.append({
            "candle_time": r.get("candle_time"),
            "poi_price_level": float(poi_price),
            "entry": float(e),
            "sl": float(sl),
            "abs_delta_pct_of_risk": abs(float(e) - float(poi_price)) / risk if risk else None,
            "plausible_within_1.5R": plausible,
        })
    return out


# ── Output formatter ────────────────────────────────────────────────

def main():
    xau = tag(load_xauusd())
    eur = tag(load_eurusd())
    nas = tag(load_nas100())

    summary = {}

    for label, records in (("XAUUSD", xau), ("EURUSD", eur), ("NAS100", nas)):
        summary[label] = {
            "hallucination": hallucination_tally(records, label),
            "l2_families": l2_failure_rates(records, label),
            "sl_buffer": sl_buffer_check(records, label),
        }
        deg, deg_list = degenerate_analysis(records, label)
        summary[label]["degenerate"] = deg
        summary[label]["ob_citation_sample"] = ob_citation_check(records, label)

    with open(OUT / "integrity_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    # Print a compact summary
    print(json.dumps(summary, indent=2, default=str)[:6000])
    print("...")
    print(f"wrote {OUT / 'integrity_summary.json'}")


if __name__ == "__main__":
    main()
