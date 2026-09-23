"""HALLUC-4 audit script — quantify cross_instrument_context impact on hallucination.

Reads:
  knowledge_base/trade_records/{INSTRUMENT}/*.json

For each record, extracts:
  - cross_instrument_context block (presence, content)
  - AI reasoning + trade_parameters
  - whether AI rationale cites "XAU"/"gold"/"dollar"
  - whether poi_price_level / entry_price aligns with candidate instrument's OB list
    OR XAU's OB list (cross-instrument anchoring)
  - per-instrument 2x2 matrix (cross_context_present × hallucination_outcome)

Hallucination = poi_price_level OR entry_price falls OUTSIDE the candidate's
H1 OB list AND outside any structural anchor in MSO. Tolerance: 5x model_a.equal_level_tolerance.

Output:
  results.json — full per-record audit
  per_instrument_2x2.csv
  xau_rationale_audit.csv
  report.md — synthesis
"""

from __future__ import annotations

import csv
import json
import os
import re
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TR_BASE = REPO_ROOT / "knowledge_base" / "trade_records"
OUT_DIR = Path(__file__).resolve().parent

# Per-instrument OB midpoint tolerance for "is poi_price aligned with OB list" check
# Using ATR-tier figures. 5x equal_level_tolerance from agent_config.
PRICE_TOLERANCE = {
    "XAUUSD": 12.50,  # 5 * 2.5
    "GBPUSD": 0.001005,  # 5 * 0.000201
    "USDJPY": 0.110,  # 5 * 0.022
    "GBPJPY": 0.140,  # 5 * 0.028
    "US30_cash": 37.50,  # 5 * 7.5
    "NAS100": 39.35,  # 5 * 7.87
    "XAGUSD": 0.10,  # rough (XAGUSD doesn't have explicit equal_level_tolerance in config we read)
    "EURUSD": 0.000830,  # 5 * 0.000166
}

# Loose XAU price band — for detecting XAU anchoring on non-XAU instruments
XAU_PRICE_BAND = (1500.0, 5500.0)
INSTRUMENT_PRICE_BANDS = {
    "XAUUSD": (1500.0, 5500.0),
    "GBPUSD": (1.0, 2.0),
    "USDJPY": (100.0, 200.0),
    "GBPJPY": (150.0, 250.0),
    "US30_cash": (25000.0, 50000.0),
    "NAS100": (10000.0, 30000.0),
    "XAGUSD": (15.0, 60.0),
    "EURUSD": (1.0, 1.5),
}

XAU_RATIONALE_PATTERNS = [
    # XAU/XAUUSD/XAUSD — capture any XAU prefix not embedded mid-word
    re.compile(r"\bXAU(?:USD)?\b", re.I),
    re.compile(r"\bgold\b", re.I),
    re.compile(r"\bdollar\s+(weak|strong|str|wk|flow)", re.I),
    re.compile(r"\bDXY\b", re.I),
    re.compile(r"\busd\s+(weak|strong)", re.I),
    # XAU-anchored macro phrasing — appears verbatim in the cross_instrument
    # block's DECISION GUIDANCE so we'd want to flag echoes of it.
    re.compile(r"macro\s+head ?wind", re.I),
    re.compile(r"dollar\s+(weakness|strength)", re.I),
]


def extract_h1_ob_midpoints(mso: dict) -> list[float]:
    """Return list of H1 OB midpoints from MSO."""
    if not mso:
        return []
    tfs = mso.get("timeframes", {}) or {}
    h1 = tfs.get("H1", {}) or {}
    obs = h1.get("order_blocks") or h1.get("ob") or h1.get("OBs") or []
    midpoints = []
    if isinstance(obs, list):
        for ob in obs:
            if not isinstance(ob, dict):
                continue
            mid = ob.get("midpoint") or ob.get("mid")
            if mid is None:
                hi = ob.get("high") or ob.get("top")
                lo = ob.get("low") or ob.get("bottom")
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


def is_in_band(price: float, band: tuple[float, float]) -> bool:
    return band[0] <= price <= band[1]


def detect_xau_anchoring(price: float, candidate_sym: str) -> bool:
    """Return True if a price for non-XAU instrument falls in XAU's price band."""
    if candidate_sym == "XAUUSD":
        return False
    if not isinstance(price, (int, float)):
        return False
    return is_in_band(float(price), XAU_PRICE_BAND)


def is_aligned_with_ob(price: float, midpoints: list[float], tol: float) -> bool:
    if not isinstance(price, (int, float)):
        return False
    for m in midpoints:
        if abs(price - m) <= tol:
            return True
    return False


def count_xau_rationale_hits(text: str) -> int:
    if not isinstance(text, str) or not text:
        return 0
    return sum(1 for pat in XAU_RATIONALE_PATTERNS if pat.search(text))


def gather_full_rationale(ai_resp: dict) -> str:
    """Combine all AI rationale fields into one searchable string."""
    if not isinstance(ai_resp, dict):
        return ""
    parts = []
    reasoning = ai_resp.get("reasoning")
    if isinstance(reasoning, dict):
        for k, v in reasoning.items():
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, dict):
                for vv in v.values():
                    if isinstance(vv, str):
                        parts.append(vv)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, str):
                        parts.append(item)
                    elif isinstance(item, dict):
                        for vv in item.values():
                            if isinstance(vv, str):
                                parts.append(vv)
    elif isinstance(reasoning, str):
        parts.append(reasoning)
    for k in ("no_trade_reason", "wait_reason"):
        v = ai_resp.get(k)
        if isinstance(v, str):
            parts.append(v)
    return " ".join(parts)


def audit_one_record(fp: Path) -> dict | None:
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            d = json.load(f)
    except Exception as e:
        return None
    meta = d.get("metadata", {}) or {}
    sym = meta.get("symbol")
    if not sym:
        sym = fp.parts[-2]
    candle_time = meta.get("candle_time")
    date = meta.get("date") or (str(candle_time)[:10] if candle_time else "unknown")
    ctx = d.get("context_at_decision", {}) or {}
    ci_block = ctx.get("cross_instrument_context", "") or ""
    ci_present = bool(ci_block.strip())

    # Extract XAU direction text from CI block, if present
    xau_dir = None
    if ci_present:
        m = re.search(r"XAUUSD\s+D1\s+structure:\s*(\w+)", ci_block)
        if m:
            xau_dir = m.group(1).lower()

    prompt = d.get("prompt", {}) or {}
    if isinstance(prompt, dict):
        sp = prompt.get("system_prompt", "") or ""
        um = prompt.get("user_message", "") or ""
    else:
        sp = ""
        um = str(prompt) if prompt else ""

    ai_resp = d.get("ai_response", {}) or {}
    decision = ai_resp.get("decision")
    direction = None
    entry_price = None
    poi_price = None
    stop_loss = None
    if ai_resp:
        tp = ai_resp.get("trade_parameters") or {}
        direction = tp.get("direction")
        entry_price = tp.get("entry_price")
        stop_loss = tp.get("stop_loss")
        # poi_price_level is in reasoning.h1_setup
        rh = ai_resp.get("reasoning") or {}
        if isinstance(rh, dict):
            h1_setup = rh.get("h1_setup") or {}
            if isinstance(h1_setup, dict):
                poi_price = h1_setup.get("poi_price_level")

    full_rationale = gather_full_rationale(ai_resp)
    xau_rationale_hits = count_xau_rationale_hits(full_rationale)
    has_xau_in_rationale = xau_rationale_hits > 0

    # Extract OBs from MSO
    mso = d.get("mso", {}) or {}
    h1_obs = extract_h1_ob_midpoints(mso)
    tol = PRICE_TOLERANCE.get(sym, 0.0)

    # Hallucination checks
    poi_in_xau_band = detect_xau_anchoring(poi_price, sym) if poi_price is not None else False
    entry_in_xau_band = detect_xau_anchoring(entry_price, sym) if entry_price is not None else False
    poi_aligned_with_candidate_ob = (
        is_aligned_with_ob(float(poi_price), h1_obs, tol)
        if isinstance(poi_price, (int, float)) else False
    )
    in_band = INSTRUMENT_PRICE_BANDS.get(sym)
    poi_in_candidate_band = (
        in_band is not None and isinstance(poi_price, (int, float))
        and is_in_band(float(poi_price), in_band)
    )

    # Rough hallucination signal:
    #   POI price exists, doesn't align with any H1 OB midpoint, and falls OUTSIDE
    #   the candidate's normal price band — this is the strongest XAU-cross-bleed
    #   pattern we'd expect.  POI exists but doesn't align with H1 OB but IS
    #   in candidate band is "internal" hallucination (not cross-instrument).
    cross_anchor_hallucination = bool(
        decision == "CANDIDATE"
        and poi_price is not None
        and not poi_in_candidate_band
        and (poi_in_xau_band or entry_in_xau_band)
    )
    internal_hallucination = bool(
        decision == "CANDIDATE"
        and poi_price is not None
        and poi_in_candidate_band
        and not poi_aligned_with_candidate_ob
    )

    # Rationale signal: did AI output cite XAU at all?
    cited_xau = has_xau_in_rationale

    return {
        "file": fp.name,
        "symbol": sym,
        "date": date,
        "candle_time": candle_time,
        "ci_block_present": ci_present,
        "xau_d1_dir_in_block": xau_dir,
        "decision": decision,
        "direction": direction,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "poi_price": poi_price,
        "n_h1_obs": len(h1_obs),
        "h1_ob_midpoints": h1_obs,
        "tolerance": tol,
        "poi_aligned_with_candidate_ob": poi_aligned_with_candidate_ob,
        "poi_in_candidate_band": poi_in_candidate_band,
        "poi_in_xau_band": poi_in_xau_band,
        "entry_in_xau_band": entry_in_xau_band,
        "cross_anchor_hallucination": cross_anchor_hallucination,
        "internal_hallucination": internal_hallucination,
        "xau_rationale_hits": xau_rationale_hits,
        "cited_xau_in_rationale": cited_xau,
        "rationale_excerpt": full_rationale[:500],
    }


def main():
    records = []
    for sym_dir in sorted(TR_BASE.iterdir()):
        if not sym_dir.is_dir():
            continue
        sym = sym_dir.name
        for fp in sorted(sym_dir.glob("*.json")):
            r = audit_one_record(fp)
            if r is not None:
                records.append(r)

    # Build per-instrument 2x2 matrix:
    #   rows: ci_block_present  (True/False)
    #   cols: cross_anchor_hallucination (True/False)
    matrix_2x2 = defaultdict(lambda: {
        "ci_yes_halluc_yes": 0,
        "ci_yes_halluc_no": 0,
        "ci_no_halluc_yes": 0,
        "ci_no_halluc_no": 0,
        "ci_yes_internal_halluc": 0,
        "ci_no_internal_halluc": 0,
        "ci_yes_total": 0,
        "ci_no_total": 0,
        "ci_yes_cited_xau": 0,
        "ci_no_cited_xau": 0,
        "ci_yes_cand": 0,
        "ci_no_cand": 0,
        "n_records": 0,
    })

    xau_rationale_rows = []
    for r in records:
        sym = r["symbol"]
        if r["ci_block_present"]:
            matrix_2x2[sym]["ci_yes_total"] += 1
            if r["cited_xau_in_rationale"]:
                matrix_2x2[sym]["ci_yes_cited_xau"] += 1
            if r["decision"] == "CANDIDATE":
                matrix_2x2[sym]["ci_yes_cand"] += 1
            if r["cross_anchor_hallucination"]:
                matrix_2x2[sym]["ci_yes_halluc_yes"] += 1
            else:
                matrix_2x2[sym]["ci_yes_halluc_no"] += 1
            if r["internal_hallucination"]:
                matrix_2x2[sym]["ci_yes_internal_halluc"] += 1
        else:
            matrix_2x2[sym]["ci_no_total"] += 1
            if r["cited_xau_in_rationale"]:
                matrix_2x2[sym]["ci_no_cited_xau"] += 1
            if r["decision"] == "CANDIDATE":
                matrix_2x2[sym]["ci_no_cand"] += 1
            if r["cross_anchor_hallucination"]:
                matrix_2x2[sym]["ci_no_halluc_yes"] += 1
            else:
                matrix_2x2[sym]["ci_no_halluc_no"] += 1
            if r["internal_hallucination"]:
                matrix_2x2[sym]["ci_no_internal_halluc"] += 1
        matrix_2x2[sym]["n_records"] += 1

        # Cross-instrument rationale audit row — only for non-XAU instruments
        if sym != "XAUUSD" and (r["cited_xau_in_rationale"] or r["ci_block_present"]):
            xau_rationale_rows.append({
                "file": r["file"],
                "symbol": sym,
                "ci_block_present": r["ci_block_present"],
                "xau_d1_dir_in_block": r["xau_d1_dir_in_block"],
                "decision": r["decision"],
                "direction": r["direction"],
                "cited_xau_in_rationale": r["cited_xau_in_rationale"],
                "xau_rationale_hits": r["xau_rationale_hits"],
                "poi_price": r["poi_price"],
                "poi_in_candidate_band": r["poi_in_candidate_band"],
                "cross_anchor_hallucination": r["cross_anchor_hallucination"],
                "rationale_excerpt": r["rationale_excerpt"],
            })

    # Write outputs
    with open(OUT_DIR / "results.json", "w", encoding="utf-8") as f:
        json.dump({"records": records, "matrix_2x2": dict(matrix_2x2)}, f, indent=2, default=str)

    with open(OUT_DIR / "per_instrument_2x2.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "symbol", "n_records",
            "ci_yes_total", "ci_no_total",
            "ci_yes_cand", "ci_no_cand",
            "ci_yes_cited_xau", "ci_no_cited_xau",
            "ci_yes_halluc_yes", "ci_yes_halluc_no",
            "ci_no_halluc_yes", "ci_no_halluc_no",
            "ci_yes_internal_halluc", "ci_no_internal_halluc",
        ])
        for sym, m in sorted(matrix_2x2.items()):
            w.writerow([
                sym, m["n_records"],
                m["ci_yes_total"], m["ci_no_total"],
                m["ci_yes_cand"], m["ci_no_cand"],
                m["ci_yes_cited_xau"], m["ci_no_cited_xau"],
                m["ci_yes_halluc_yes"], m["ci_yes_halluc_no"],
                m["ci_no_halluc_yes"], m["ci_no_halluc_no"],
                m["ci_yes_internal_halluc"], m["ci_no_internal_halluc"],
            ])

    with open(OUT_DIR / "xau_rationale_audit.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "file", "symbol", "ci_block_present", "xau_d1_dir_in_block",
            "decision", "direction",
            "cited_xau_in_rationale", "xau_rationale_hits",
            "poi_price", "poi_in_candidate_band", "cross_anchor_hallucination",
            "rationale_excerpt",
        ])
        for r in xau_rationale_rows:
            w.writerow([
                r["file"], r["symbol"], r["ci_block_present"],
                r["xau_d1_dir_in_block"], r["decision"], r["direction"],
                r["cited_xau_in_rationale"], r["xau_rationale_hits"],
                r["poi_price"], r["poi_in_candidate_band"],
                r["cross_anchor_hallucination"],
                r["rationale_excerpt"][:300],
            ])

    # Stats
    print("Total trade records audited:", len(records))
    print()
    print("Per-instrument 2x2 (ci_block × cross-anchor-hallucination):")
    for sym, m in sorted(matrix_2x2.items()):
        print(f"  {sym}: n={m['n_records']}")
        print(f"    ci_yes: total={m['ci_yes_total']}, cand={m['ci_yes_cand']}, "
              f"cited_XAU_in_rationale={m['ci_yes_cited_xau']}, "
              f"cross_halluc={m['ci_yes_halluc_yes']}, internal_halluc={m['ci_yes_internal_halluc']}")
        print(f"    ci_no:  total={m['ci_no_total']},  cand={m['ci_no_cand']},  "
              f"cited_XAU_in_rationale={m['ci_no_cited_xau']}, "
              f"cross_halluc={m['ci_no_halluc_yes']}, internal_halluc={m['ci_no_internal_halluc']}")

    return records, matrix_2x2, xau_rationale_rows


if __name__ == "__main__":
    main()
