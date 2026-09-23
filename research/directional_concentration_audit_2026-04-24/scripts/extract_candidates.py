"""
Extract all CANDIDATE rows from April 2026 live_evaluations.
Count per-instrument LONG vs SHORT and aggregate daily_bias direction.
"""
from __future__ import annotations
import json
import glob
from collections import Counter, defaultdict
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
EVAL_DIR = ROOT / "knowledge_base" / "live_evaluations"


def direction_from_reasoning(text: str | None) -> str | None:
    """Heuristic extraction of LONG / SHORT from overall_reasoning or no_trade_reason."""
    if not text:
        return None
    t = text.upper()
    long_hits = len(re.findall(r"\bLONG\b|\bBULLISH\b|\bBUY\b", t))
    short_hits = len(re.findall(r"\bSHORT\b|\bBEARISH\b|\bSELL\b", t))
    if long_hits and short_hits == 0:
        return "LONG"
    if short_hits and long_hits == 0:
        return "SHORT"
    if long_hits > short_hits:
        return "LONG_MIXED"
    if short_hits > long_hits:
        return "SHORT_MIXED"
    return None


def main() -> int:
    candidates = defaultdict(list)
    all_evals = defaultdict(list)
    daily_bias_distribution = defaultdict(lambda: defaultdict(Counter))  # symbol -> day -> bias_counter

    for fp in sorted(glob.glob(str(EVAL_DIR / "*" / "2026-04-*.jsonl"))):
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                sym = d.get("symbol") or "UNKNOWN"
                day = (d.get("candle_time") or d.get("timestamp") or "")[:10]
                bias = d.get("daily_bias_direction") or "missing"
                all_evals[sym].append(d)
                daily_bias_distribution[sym][day][bias] += 1
                if d.get("decision") == "CANDIDATE":
                    candidates[sym].append(d)

    print("=" * 80)
    print("CANDIDATE COUNTS PER INSTRUMENT (April 2026)")
    print("=" * 80)
    total_long = 0
    total_short = 0
    total_mixed = 0
    total_none = 0
    for sym in sorted(candidates):
        rows = candidates[sym]
        print(f"\n-- {sym} ({len(rows)} candidates) --")
        bias_counter = Counter(r.get("daily_bias_direction", "none") for r in rows)
        print(f"  daily_bias_direction distribution: {dict(bias_counter)}")
        dir_counter = Counter()
        for r in rows:
            dir_hint = direction_from_reasoning(r.get("overall_reasoning"))
            dir_counter[dir_hint or "unknown"] += 1
        print(f"  direction inferred from reasoning: {dict(dir_counter)}")
        for b, c in bias_counter.items():
            if b == "bullish":
                total_long += c
            elif b == "bearish":
                total_short += c
            else:
                total_mixed += c

    print("\n" + "=" * 80)
    print("AGGREGATE — ALL 4 LIVE INSTRUMENTS (XAUUSD+US30+USDJPY+GBPJPY)")
    print("  GBPUSD observer excluded")
    print("=" * 80)
    live = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY"]
    long_count = short_count = neutral_count = 0
    for sym in live:
        for r in candidates.get(sym, []):
            b = r.get("daily_bias_direction")
            if b == "bullish":
                long_count += 1
            elif b == "bearish":
                short_count += 1
            else:
                neutral_count += 1
    total = long_count + short_count + neutral_count
    print(f"  LONG (bullish bias): {long_count}/{total} = {100*long_count/max(total,1):.1f}%")
    print(f"  SHORT (bearish bias): {short_count}/{total} = {100*short_count/max(total,1):.1f}%")
    print(f"  NEUTRAL/OTHER: {neutral_count}/{total} = {100*neutral_count/max(total,1):.1f}%")

    # Post-FN-kickoff (2026-04-20 onwards)
    print("\n  Post-redacted_account-kickoff (2026-04-20 through 04-23):")
    fn_long = fn_short = fn_other = 0
    for sym in live:
        for r in candidates.get(sym, []):
            day = (r.get("candle_time") or "")[:10]
            if day < "2026-04-20":
                continue
            b = r.get("daily_bias_direction")
            if b == "bullish":
                fn_long += 1
            elif b == "bearish":
                fn_short += 1
            else:
                fn_other += 1
    fn_total = fn_long + fn_short + fn_other
    print(f"    LONG: {fn_long}/{fn_total} = {100*fn_long/max(fn_total,1):.1f}%")
    print(f"    SHORT: {fn_short}/{fn_total} = {100*fn_short/max(fn_total,1):.1f}%")
    print(f"    OTHER: {fn_other}/{fn_total}")

    print("\n" + "=" * 80)
    print("DAILY BIAS DISTRIBUTION (ALL EVALS, not only CANDIDATE) — April 2026")
    print("=" * 80)
    for sym in sorted(all_evals):
        total_rows = 0
        agg = Counter()
        for day, ctr in daily_bias_distribution[sym].items():
            for k, v in ctr.items():
                agg[k] += v
                total_rows += v
        print(f"\n-- {sym} (n={total_rows} evals) --")
        for k, v in agg.most_common():
            print(f"   {k}: {v}  ({100*v/max(total_rows,1):.1f}%)")

    print("\n" + "=" * 80)
    print("PER-DAY DOMINANT D1 BIAS (all evals, per-symbol)")
    print("=" * 80)
    bearish_day_rows = []
    for sym in sorted(all_evals):
        print(f"\n-- {sym} --")
        for day in sorted(daily_bias_distribution[sym]):
            ctr = daily_bias_distribution[sym][day]
            if not ctr:
                continue
            dominant = ctr.most_common(1)[0][0]
            tot = sum(ctr.values())
            dom_frac = ctr[dominant] / tot
            marker = ""
            if dominant == "bearish":
                marker = "  <-- BEARISH day"
                bearish_day_rows.append((sym, day, dict(ctr)))
            print(f"   {day}: dominant={dominant} ({dom_frac:.0%}), total_evals={tot}, breakdown={dict(ctr)}{marker}")

    print("\n" + "=" * 80)
    print("BEARISH-BIAS DAYS — did any CANDIDATE emerge on those days?")
    print("=" * 80)
    for sym, day, breakdown in bearish_day_rows:
        cands_today = [r for r in candidates.get(sym, []) if (r.get("candle_time") or "")[:10] == day]
        cands_biases = Counter(r.get("daily_bias_direction") for r in cands_today)
        print(f"  {sym} {day}: breakdown={breakdown}, candidates_today={len(cands_today)}, "
              f"candidate_biases={dict(cands_biases)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
