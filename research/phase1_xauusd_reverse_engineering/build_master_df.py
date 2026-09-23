"""Build master dataframe for Phase 1 Track D sniper-subset analysis.

Aggregates three data sources:
1. knowledge_base/index/_trade_index.json (129 enriched)
2. knowledge_base_backtest/sessions/**/*.json (259 unique via candle_evaluations)
3. research/f3_backtest_2026-04-24/<slice>/all_results.json (32 filled fleet-wide)
4. knowledge_base/trade_records/** filled live trades (extract target-OB touch_count)

Sniper cell: (setup_grade=A+, touch_count=1, m5_refined=true, realized_RR >= 2.0).
"""
import json
import os
from pathlib import Path
import re

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
OUT = ROOT / "research" / "phase1_xauusd_reverse_engineering"
OUT.mkdir(parents=True, exist_ok=True)

rows = []

# -------------------------------------------------------------------
# Source 1: trade_index.json (129 enriched)
# -------------------------------------------------------------------
idx = json.loads((ROOT / "knowledge_base" / "index" / "_trade_index.json").read_text())
for t in idx["trades"]:
    rows.append({
        "source": "batch_index",
        "trade_id": t.get("trade_id"),
        "symbol": t.get("symbol"),
        "direction": t.get("direction"),
        "setup_grade": t.get("setup_grade") or t.get("grade"),
        "outcome": t.get("outcome"),
        "r_multiple": t.get("r_multiple"),
        "touch_count": None,
        "m5_refined": None,
        "notes": "no touch_count or m5_refined available",
    })
print(f"[src1] batch_index: {len(rows)} rows")

# -------------------------------------------------------------------
# Source 2: unified_trades_v2_20260331.json (111 XAUUSD-only with planned_rr)
# For cross-referencing, we'll pull in fields that exist
# -------------------------------------------------------------------
uf = ROOT / "knowledge_base_backtest" / "analysis" / "unified_trades_v2_20260331.json"
unified = json.loads(uf.read_text())
# merge planned_rr + displacement_quality into trade_index by trade_id
id_to_planned = {}
id_to_displacement = {}
for t in unified:
    tid = t.get("trade_id")
    if tid:
        id_to_planned[tid] = t.get("planned_rr")
        id_to_displacement[tid] = t.get("displacement_quality")
for r in rows:
    # trade_index IDs have _xauusd suffix -- strip to match unified
    tid = r["trade_id"]
    if tid and tid.endswith("_xauusd"):
        base = tid.rsplit("_", 1)[0]
        if base in id_to_planned:
            r["planned_rr"] = id_to_planned[base]
            r["displacement_quality"] = id_to_displacement.get(base)

# -------------------------------------------------------------------
# Source 3: F3 backtest filled CANDIDATEs with touch_count via regex
# -------------------------------------------------------------------
TOUCH_RE = re.compile(r"touches\s*=\s*(\d+)")

f3_root = ROOT / "research" / "f3_backtest_2026-04-24"
f3_rows_before = len(rows)
for slice_dir in sorted(f3_root.iterdir()):
    if not slice_dir.is_dir():
        continue
    allf = slice_dir / "all_results.json"
    if not allf.exists():
        continue
    data = json.loads(allf.read_text())
    # symbol from slice name
    slice_name = slice_dir.name
    symbol = "XAUUSD" if slice_name.startswith("xauusd") else ("USDJPY" if slice_name.startswith("usdjpy") else "?")
    for rec in data["results"]:
        if rec.get("decision") != "CANDIDATE":
            continue
        # only include if order actually filled (outcome WIN/LOSS)
        out = rec.get("outcome")
        if out not in ("WIN", "LOSS", "BE", "BREAKEVEN"):
            continue
        # extract touch_count from raw_response
        raw = rec.get("raw_response", "")
        tc = None
        # Look for "touches=N" patterns specifically mentioning the chosen OB zone
        # Use the first mention as proxy for the target OB
        m = TOUCH_RE.search(raw)
        if m:
            tc = int(m.group(1))
        rows.append({
            "source": "f3_backtest",
            "trade_id": f"{slice_name}_{rec.get('candle_time')}",
            "symbol": rec.get("symbol") or symbol,
            "direction": rec.get("direction"),
            "setup_grade": rec.get("setup_grade"),
            "outcome": out if out not in ("BE",) else "BREAKEVEN",
            "r_multiple": rec.get("r_multiple"),
            "touch_count": tc,
            "m5_refined": None,  # F3 backtest does not run M5 refinement
            "slice": slice_name,
        })
f3_added = len(rows) - f3_rows_before
print(f"[src3] f3_backtest filled: {f3_added} rows")

# -------------------------------------------------------------------
# Source 4: Live trade_records — extract target OB touch_count
# Only filled records have outcomes, but inspection shows records are all LIMIT_PLACED / EXECUTION_FAILED
# So we capture the CANDIDATE-level data but outcome is typically unavailable
# -------------------------------------------------------------------
LIVE_ROOT = ROOT / "knowledge_base" / "trade_records"
live_added_counts = {}
for sym_dir in LIVE_ROOT.iterdir():
    if not sym_dir.is_dir():
        continue
    if sym_dir.name == "_pending_records_index.json":
        continue
    sym = sym_dir.name
    live_added_counts[sym] = 0
    for fp in sym_dir.iterdir():
        if not fp.name.endswith(".json"):
            continue
        try:
            data = json.loads(fp.read_text())
        except Exception:
            continue
        dp = data.get("decision_pipeline") or {}
        final = dp.get("final_outcome") or ""
        # only rows where we have some trade execution
        if final.startswith("REJECTED") or final == "NO_TRADE":
            continue
        if not data.get("trade_parameters"):
            continue
        grade = dp.get("ai_grade")
        direction = dp.get("ai_direction")
        tp = data.get("trade_parameters", {})
        entry = tp.get("entry_price")
        sl = tp.get("stop_loss")
        tp1 = tp.get("take_profit_1")
        # compute realized_RR placeholder (we don't have exit outcome in these)
        planned_rr = None
        if entry and sl and tp1 and (entry != sl):
            planned_rr = abs(tp1 - entry) / abs(entry - sl)
        # try to extract target OB touch_count by matching entry_price to H1 OBs in MSO
        tc = None
        mso = data.get("mso", {})
        h1 = (mso.get("timeframes") or {}).get("H1", {})
        obs = h1.get("order_blocks", [])
        if entry is not None and obs:
            for ob in obs:
                if ob.get("mitigated"):
                    continue
                hi = ob.get("high"); lo = ob.get("low")
                if hi is None or lo is None:
                    continue
                # target OB: entry should be at ob_high (LONG) or ob_low (SHORT)
                if direction == "LONG" and abs(entry - hi) < 0.01 * max(hi, 1):
                    tc = ob.get("touch_count")
                    break
                if direction == "SHORT" and abs(entry - lo) < 0.01 * max(lo, 1):
                    tc = ob.get("touch_count")
                    break
            if tc is None:
                # fallback: any OB whose zone contains entry
                for ob in obs:
                    if ob.get("mitigated"):
                        continue
                    hi = ob.get("high"); lo = ob.get("low")
                    if hi is not None and lo is not None and lo <= entry <= hi:
                        tc = ob.get("touch_count")
                        break
        rows.append({
            "source": "live_trade_record",
            "trade_id": f"{sym}/{fp.stem}",
            "symbol": sym,
            "direction": direction,
            "setup_grade": grade,
            "outcome": None,  # not captured in these records
            "r_multiple": None,
            "touch_count": tc,
            "m5_refined": None,
            "planned_rr": planned_rr,
            "final_outcome": final,
        })
        live_added_counts[sym] += 1
print(f"[src4] live_trade_record: {live_added_counts}")

# -------------------------------------------------------------------
# Persist
# -------------------------------------------------------------------
out = OUT / "master_df.jsonl"
with out.open("w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
print(f"wrote {len(rows)} rows -> {out}")

# Summary stats by source
by_src = {}
for r in rows:
    by_src.setdefault(r["source"], 0)
    by_src[r["source"]] += 1
print("by_source:", by_src)
