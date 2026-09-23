"""T3.2 XAUUSD sl_beyond_ob cross-instrument audit.

Mirrors the NAS100 analysis (`research/t3_1_eurusd_nas100_validation_2026-04-19/
analysis/_scratch/gen_tables.py`) on the XAUUSD full-2026 T7 simulation.

Source data:
  - research/t7_live_simulation/all_results_jan_apr10.json (Jan 2 - Apr 10 2026,
    n_evaluated=2100, symbol=XAUUSD; this is the combined (Jan-Mar11 + Mar11-Apr10)
    T7 simulation file, 2100 records).
  - data/historical_2026/XAUUSD_M15.csv (OHLC for counterfactual outcomes).

Output:
  - extracted_xauusd_bit_exact_rejects.json — the bit-exact records + parsed fields.
  - counterfactual_tables.json — L2 sub-category counterfactual outcomes (no-timeout +
    2h timeout-BE) mirroring NAS100 Q1b tables.
  - sl_buffer_universality.json — does every record ship sl_buffer_applied=0.0?
  - global_sl_buffer_check.json — confirm no_trade_reason / decision distribution.

Run:
    cd C:/Users/MSI/Documents/ai-trading-agent
    python research/t3_2_sl_beyond_ob_cross_instrument_audit/extract.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
ROOT = Path(r"C:/Users/MSI/Documents/ai-trading-agent")
OUT_DIR = ROOT / "research" / "t3_2_sl_beyond_ob_cross_instrument_audit"
SIM_PATH = ROOT / "research" / "t7_live_simulation" / "all_results_jan_apr10.json"
CSV_PATH = ROOT / "data" / "historical_2026" / "XAUUSD_M15.csv"

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Load M15 bars for outcome simulation + candle_close lookup
# ---------------------------------------------------------------------------

m15: list[dict] = []
with open(CSV_PATH) as f:
    rdr = csv.DictReader(f)
    for row in rdr:
        t = row["time"].replace(" ", "T") + "Z"
        m15.append({
            "time": t,
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
        })
time_idx = {c["time"]: i for i, c in enumerate(m15)}
print(f"Loaded {len(m15)} M15 bars from {CSV_PATH.name}")


def compute_outcome(entry, sl, tp, direction, candle_close, candle_time, timeout=None):
    """Replicates the NAS100 T3.1 counterfactual engine verbatim.

    Same logic as `scripts/simulate_t7_live_period.py::compute_outcome`:
      - EPS=0.05: if |entry - candle_close| <= EPS, treat as at-market fill now.
      - Otherwise wait for the next candle whose low/high crosses entry.
      - SL-first, TP-second tie-break within a candle (conservative LOSS on tie).
      - Optional 2 h timeout → BE (WIN/LOSS can still trigger inside the 2h window).
    """
    if not entry or not sl or not tp:
        return {"outcome": "UNKNOWN", "r": 0}
    EPS = 0.05
    needs_fill_check = candle_close is not None and abs(entry - candle_close) > EPS
    entry_filled = not needs_fill_check
    fill_time = candle_time if entry_filled else None
    if candle_time not in time_idx:
        return {"outcome": "UNKNOWN", "r": 0}
    start = time_idx[candle_time]
    for i in range(start + 1, len(m15)):
        c = m15[i]
        h, l = c["high"], c["low"]
        if not entry_filled:
            if direction == "LONG":
                if entry < candle_close and l <= entry:
                    entry_filled = True
                    fill_time = c["time"]
                elif entry > candle_close and h >= entry:
                    entry_filled = True
                    fill_time = c["time"]
            else:
                if entry > candle_close and h >= entry:
                    entry_filled = True
                    fill_time = c["time"]
                elif entry < candle_close and l <= entry:
                    entry_filled = True
                    fill_time = c["time"]
            if not entry_filled:
                continue
        if timeout is not None and fill_time is not None:
            ft = datetime.fromisoformat(fill_time.replace("Z", "+00:00"))
            ct = datetime.fromisoformat(c["time"].replace("Z", "+00:00"))
            if (ct - ft).total_seconds() / 3600.0 >= timeout:
                if direction == "LONG":
                    if l <= sl:
                        return {"outcome": "LOSS", "r": -1.0}
                    if h >= tp:
                        d = entry - sl
                        return {"outcome": "WIN", "r": round((tp - entry) / d, 2) if d > 0 else 0}
                else:
                    if h >= sl:
                        return {"outcome": "LOSS", "r": -1.0}
                    if l <= tp:
                        d = sl - entry
                        return {"outcome": "WIN", "r": round((entry - tp) / d, 2) if d > 0 else 0}
                return {"outcome": "BE", "r": 0}
        if direction == "LONG":
            if l <= sl:
                return {"outcome": "LOSS", "r": -1.0}
            if h >= tp:
                d = entry - sl
                return {"outcome": "WIN", "r": round((tp - entry) / d, 2) if d > 0 else 0}
        else:
            if h >= sl:
                return {"outcome": "LOSS", "r": -1.0}
            if l <= tp:
                d = sl - entry
                return {"outcome": "WIN", "r": round((entry - tp) / d, 2) if d > 0 else 0}
    if not entry_filled:
        return {"outcome": "UNFILLED", "r": 0}
    return {"outcome": "OPEN", "r": 0}


# ---------------------------------------------------------------------------
# Load T7 sim results
# ---------------------------------------------------------------------------
with open(SIM_PATH) as f:
    sim = json.load(f)

print(f"Loaded {len(sim['results'])} records from {SIM_PATH.name}")
print(f"  period: {sim.get('period')}")
print(f"  symbol: {sim.get('symbol')}")
print(f"  total_cost: ${sim.get('total_cost', 0):.2f}")

decisions = Counter(r.get("decision") for r in sim["results"])
print(f"  decisions: {dict(decisions)}")

# XAUUSD T7 sim does NOT include candle_close per record — pull from CSV.
for r in sim["results"]:
    ct = r.get("candle_time")
    if ct and ct in time_idx:
        r["candle_close"] = m15[time_idx[ct]]["close"]
    else:
        r["candle_close"] = None


# ---------------------------------------------------------------------------
# Parse raw_response to extract sl_buffer_applied etc.
# ---------------------------------------------------------------------------

def parse_raw(r):
    raw = r.get("raw_response", "")
    if not raw:
        return None
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Filter sl_beyond_ob rejects + classify bit-exact vs inside-zone
# ---------------------------------------------------------------------------

def sl_subgroup(r):
    reason = r.get("l2_reason") or ""
    if not reason.startswith("sl_beyond_ob"):
        return None
    m = re.search(r"SL ([\d.]+) is NOT (below|above) OB (low|high) ([\d.]+)", reason)
    if not m:
        return "sl_beyond_ob_unparsed"
    sl_claim = float(m.group(1))
    ob_lvl = float(m.group(4))
    if sl_claim == ob_lvl:
        return "sl=OB_bound_exact"
    return "sl_inside_OB_zone"


def poi_subgroup(r):
    reason = r.get("l2_reason") or ""
    if not reason.startswith("h1_poi_exists"):
        return None
    if "poi_identified=False" in reason:
        return "poi_self_contradict_False"
    if "AI cites H1 POI" in reason:
        return "poi_cited_no_matching_OB"
    return "poi_other"


def subcat(r):
    s = sl_subgroup(r) or poi_subgroup(r)
    if s:
        return s
    reason = r.get("l2_reason") or ""
    return reason.split(":")[0].split(" (")[0].strip()


rej = [r for r in sim["results"] if r.get("decision") == "REJECTED_L2"]
sl_beyond = [r for r in rej if (r.get("l2_reason") or "").startswith("sl_beyond_ob")]
bit_exact = [r for r in sl_beyond if sl_subgroup(r) == "sl=OB_bound_exact"]
inside_zone = [r for r in sl_beyond if sl_subgroup(r) == "sl_inside_OB_zone"]

print()
print(f"REJECTED_L2 total:      {len(rej)}")
print(f"  sl_beyond_ob:         {len(sl_beyond)}")
print(f"    bit-exact SL=OB:    {len(bit_exact)}")
print(f"    inside OB zone:     {len(inside_zone)}")
print(f"    unparsed:           {len(sl_beyond) - len(bit_exact) - len(inside_zone)}")
print()

dir_counts_bit_exact = Counter(r.get("direction") for r in bit_exact)
dir_counts_sl_beyond_all = Counter(r.get("direction") for r in sl_beyond)
print(f"Bit-exact direction split: {dict(dir_counts_bit_exact)}")
print(f"All sl_beyond_ob direction split: {dict(dir_counts_sl_beyond_all)}")
print()


# ---------------------------------------------------------------------------
# Extract the records (save for evidence file)
# ---------------------------------------------------------------------------

def extract_record(r):
    p = parse_raw(r)
    tp = (p.get("trade_parameters") if p else None) or {}
    reasoning = (p.get("reasoning") if p else {}) or {}
    h1_setup = reasoning.get("h1_setup", {}) or {}
    return {
        "candle_time": r.get("candle_time"),
        "date": r.get("date"),
        "kill_zone": r.get("kill_zone"),
        "symbol": r.get("symbol"),
        "direction": r.get("direction"),
        "entry_price": r.get("entry_price"),
        "stop_loss": r.get("stop_loss"),
        "take_profit_1": r.get("take_profit_1"),
        "l2_reason": r.get("l2_reason"),
        "setup_grade": r.get("setup_grade"),
        "h1_direction": r.get("h1_direction"),
        "bias": r.get("bias"),
        "bias_source": r.get("bias_source"),
        "candle_close": r.get("candle_close"),
        # from parsed raw_response
        "sl_buffer_applied": tp.get("sl_buffer_applied"),
        "risk_reward_ratio": tp.get("risk_reward_ratio"),
        "poi_type": h1_setup.get("poi_type"),
        "poi_zone": h1_setup.get("zone"),
        "causing_event_type": h1_setup.get("causing_event_type"),
        "model_used": p.get("model_used") if p else None,
        "confidence_score": p.get("confidence_score") if p else None,
    }


extracted_bit_exact = [extract_record(r) for r in bit_exact]
extracted_inside = [extract_record(r) for r in inside_zone]
extracted_all_sl_beyond = [extract_record(r) for r in sl_beyond]


# ---------------------------------------------------------------------------
# Counterfactual outcomes (no timeout + 2h timeout-BE)
# ---------------------------------------------------------------------------

def run_bucket(recs, catfn, timeout):
    buckets = defaultdict(list)
    for r in recs:
        o = compute_outcome(
            r["entry_price"], r["stop_loss"], r["take_profit_1"], r["direction"],
            r.get("candle_close"), r["candle_time"], timeout=timeout,
        )
        buckets[catfn(r)].append(o)
    rows = []
    tw = tl = tu = to = tbe = 0
    tr = 0.0
    for k in sorted(buckets):
        ps = buckets[k]
        w = sum(1 for p in ps if p["outcome"] == "WIN")
        l = sum(1 for p in ps if p["outcome"] == "LOSS")
        u = sum(1 for p in ps if p["outcome"] == "UNFILLED")
        op = sum(1 for p in ps if p["outcome"] == "OPEN")
        be = sum(1 for p in ps if p["outcome"] == "BE")
        rs = sum(p.get("r", 0) for p in ps if p["outcome"] in ("WIN", "LOSS", "BE"))
        resolved = w + l + be
        wr = 100 * w / resolved if resolved else 0
        exp = rs / resolved if resolved else 0
        rows.append({"cat": k, "N": len(ps), "W": w, "L": l, "U": u, "O": op, "BE": be,
                     "WR": wr, "sumR": rs, "exp": exp})
        tw += w; tl += l; tu += u; to += op; tbe += be; tr += rs
    resolved = tw + tl + tbe
    rows.append({"cat": "TOTAL", "N": len(recs), "W": tw, "L": tl, "U": tu, "O": to, "BE": tbe,
                 "WR": 100 * tw / resolved if resolved else 0,
                 "sumR": tr, "exp": tr / resolved if resolved else 0})
    return rows


# Run the same subcat function as NAS100 on full REJECTED_L2 population
tables = {}
for tmo, tkey in [(None, "no_timeout"), (2, "timeout_2h")]:
    tables[f"REJECTED_L2_{tkey}"] = run_bucket(rej, subcat, tmo)

# Also run on the bit-exact only (so we have a clean counterfactual for the decision)
for tmo, tkey in [(None, "no_timeout"), (2, "timeout_2h")]:
    tables[f"bit_exact_only_{tkey}"] = run_bucket(
        bit_exact, lambda r: "sl=OB_bound_exact", tmo,
    )

# Per-record bit-exact outcomes (for the verdict table)
per_record = []
for r in bit_exact:
    o_no = compute_outcome(
        r["entry_price"], r["stop_loss"], r["take_profit_1"], r["direction"],
        r.get("candle_close"), r["candle_time"], timeout=None,
    )
    o_2h = compute_outcome(
        r["entry_price"], r["stop_loss"], r["take_profit_1"], r["direction"],
        r.get("candle_close"), r["candle_time"], timeout=2,
    )
    per_record.append({
        "candle_time": r["candle_time"],
        "direction": r["direction"],
        "entry": r["entry_price"],
        "sl": r["stop_loss"],
        "tp": r["take_profit_1"],
        "outcome_no_timeout": o_no,
        "outcome_2h_timeout": o_2h,
    })


# ---------------------------------------------------------------------------
# Universality check: sl_buffer_applied == 0.0 across all records w/ trade_params?
# ---------------------------------------------------------------------------

with_params = 0
buffer_zero = 0
buffer_nonzero = 0
buffer_none = 0
examples_nonzero = []
for r in sim["results"]:
    p = parse_raw(r)
    if not p:
        continue
    tp = p.get("trade_parameters")
    if not isinstance(tp, dict):
        continue
    with_params += 1
    buf = tp.get("sl_buffer_applied")
    if buf is None:
        buffer_none += 1
    elif buf == 0 or buf == 0.0:
        buffer_zero += 1
    else:
        buffer_nonzero += 1
        if len(examples_nonzero) < 10:
            examples_nonzero.append({
                "candle_time": r.get("candle_time"),
                "decision": r.get("decision"),
                "sl_buffer_applied": buf,
                "direction": tp.get("direction"),
                "entry": tp.get("entry_price"),
                "sl": tp.get("stop_loss"),
            })

universality = {
    "records_with_trade_parameters": with_params,
    "sl_buffer_equals_zero": buffer_zero,
    "sl_buffer_gt_zero": buffer_nonzero,
    "sl_buffer_missing": buffer_none,
    "percent_zero": 100 * buffer_zero / with_params if with_params else 0,
    "examples_nonzero": examples_nonzero,
}

# ---------------------------------------------------------------------------
# Persist outputs
# ---------------------------------------------------------------------------
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Raw records
with open(OUT_DIR / "extracted_xauusd_bit_exact_rejects.json", "w", encoding="utf-8") as f:
    json.dump({
        "source": "research/t7_live_simulation/all_results_jan_apr10.json",
        "source_period": sim.get("period"),
        "source_symbol": sim.get("symbol"),
        "n_evaluated": len(sim["results"]),
        "n_rejected_l2": len(rej),
        "n_sl_beyond_ob": len(sl_beyond),
        "n_bit_exact": len(bit_exact),
        "n_inside_zone": len(inside_zone),
        "bit_exact_records": extracted_bit_exact,
        "inside_zone_records": extracted_inside,
        "all_sl_beyond_records": extracted_all_sl_beyond,
        "direction_split_bit_exact": dict(dir_counts_bit_exact),
        "direction_split_sl_beyond_all": dict(dir_counts_sl_beyond_all),
    }, f, indent=2)
print(f"Wrote extracted_xauusd_bit_exact_rejects.json")

with open(OUT_DIR / "counterfactual_tables.json", "w", encoding="utf-8") as f:
    json.dump({
        "tables": tables,
        "per_record_bit_exact": per_record,
    }, f, indent=2)
print(f"Wrote counterfactual_tables.json")

with open(OUT_DIR / "sl_buffer_universality.json", "w", encoding="utf-8") as f:
    json.dump(universality, f, indent=2)
print(f"Wrote sl_buffer_universality.json")

# ---------------------------------------------------------------------------
# Print summary (for console reference)
# ---------------------------------------------------------------------------
print()
print("=" * 72)
print("SUMMARY")
print("=" * 72)
print(f"XAUUSD T7 sim (Jan 2 - Apr 10 2026): {len(sim['results'])} candles")
print(f"  REJECTED_L2 total:              {len(rej)}")
print(f"  sl_beyond_ob rejects:           {len(sl_beyond)}")
print(f"    bit-exact SL=OB_bound:        {len(bit_exact)}  (direction: {dict(dir_counts_bit_exact)})")
print(f"    inside OB zone:               {len(inside_zone)}")
print()
print(f"sl_buffer_applied universality:")
print(f"  records with trade_parameters: {with_params}")
print(f"  sl_buffer == 0.0:              {buffer_zero} ({100*buffer_zero/with_params if with_params else 0:.1f}%)")
print(f"  sl_buffer  > 0.0:              {buffer_nonzero}")
print(f"  sl_buffer  missing:            {buffer_none}")
print()
print("Bit-exact per-record counterfactual (no timeout):")
w_count = sum(1 for p in per_record if p["outcome_no_timeout"]["outcome"] == "WIN")
l_count = sum(1 for p in per_record if p["outcome_no_timeout"]["outcome"] == "LOSS")
sum_r = sum(p["outcome_no_timeout"].get("r", 0) for p in per_record
            if p["outcome_no_timeout"]["outcome"] in ("WIN", "LOSS", "BE"))
resolved = w_count + l_count
print(f"  N={len(per_record)} W={w_count} L={l_count} WR={100*w_count/resolved if resolved else 0:.1f}% sumR={sum_r:+.2f} Exp={sum_r/resolved if resolved else 0:+.3f}")
print()
print("Per-record detail:")
for p in per_record:
    o1 = p["outcome_no_timeout"]
    o2 = p["outcome_2h_timeout"]
    print(f"  {p['candle_time']} {p['direction']:5s} entry={p['entry']:.2f} sl={p['sl']:.2f} tp={p['tp']:.2f} "
          f"no-tmo={o1['outcome']:8s} r={o1['r']:+.2f}  2h-tmo={o2['outcome']:8s} r={o2['r']:+.2f}")
