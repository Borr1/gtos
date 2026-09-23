"""
Compare MSO deterministic D1/H1/M15 structure direction against AI-emitted
daily_bias_direction to detect any systematic asymmetry.
"""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FEAT_LOG = ROOT / "shadow_logs" / "candidate_features_log.jsonl"


def main() -> None:
    rows = []
    with open(FEAT_LOG, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            day = (r.get("timestamp_utc") or "")[:10]
            if day.startswith("2026-04-"):
                rows.append(r)

    print(f"Total candidate-feature rows (April 2026): {len(rows)}")
    if not rows:
        return

    # Per-symbol MSO D1 + H1 direction distribution
    syms = defaultdict(list)
    for r in rows:
        syms[r.get("symbol", "UNKNOWN")].append(r)

    print("\n" + "=" * 80)
    print("MSO D1 STRUCTURE DIRECTION (deterministic) vs AI daily_bias_direction")
    print("Per instrument, April 2026")
    print("=" * 80)
    for sym in sorted(syms):
        rr = syms[sym]
        print(f"\n-- {sym} (n={len(rr)}) --")
        d1 = Counter(r.get("mso_d1_structure_direction") for r in rr)
        h1 = Counter(r.get("mso_h1_structure_direction") for r in rr)
        m15 = Counter(r.get("mso_m15_structure_direction") for r in rr)
        ai = Counter(r.get("daily_bias_direction") for r in rr)
        print(f"  MSO D1 direction: {dict(d1)}")
        print(f"  MSO H1 direction: {dict(h1)}")
        print(f"  MSO M15 direction: {dict(m15)}")
        print(f"  AI daily_bias_direction: {dict(ai)}")

        # Confusion: AI says bullish while MSO D1 says what?
        print("\n  Cross-tab MSO D1 x AI daily_bias:")
        cross = Counter((r.get("mso_d1_structure_direction"), r.get("daily_bias_direction")) for r in rr)
        for (d1_dir, ai_dir), cnt in cross.most_common():
            print(f"    MSO D1={d1_dir} & AI={ai_dir}: {cnt}")

        # How often does H1 differ from AI-reported bias?
        print("\n  Cross-tab MSO H1 x AI daily_bias (prompt says AI should report H1 as bias):")
        cross_h1 = Counter((r.get("mso_h1_structure_direction"), r.get("daily_bias_direction")) for r in rr)
        for (h1_dir, ai_dir), cnt in cross_h1.most_common():
            print(f"    MSO H1={h1_dir} & AI={ai_dir}: {cnt}")

    # Overall aggregate
    print("\n" + "=" * 80)
    print("AGGREGATE — ALL INSTRUMENTS — MSO direction distributions (April 2026)")
    print("=" * 80)
    d1_all = Counter(r.get("mso_d1_structure_direction") for r in rows)
    h1_all = Counter(r.get("mso_h1_structure_direction") for r in rows)
    m15_all = Counter(r.get("mso_m15_structure_direction") for r in rows)
    ai_all = Counter(r.get("daily_bias_direction") for r in rows)
    print(f"  MSO D1: {dict(d1_all)}")
    print(f"  MSO H1: {dict(h1_all)}")
    print(f"  MSO M15: {dict(m15_all)}")
    print(f"  AI daily_bias: {dict(ai_all)}")

    # Pure sanity: on MSO D1=bearish rows, how does AI emit bias?
    print("\n" + "=" * 80)
    print("FOCUS — MSO D1 direction == 'bearish'")
    print("=" * 80)
    bear_d1 = [r for r in rows if r.get("mso_d1_structure_direction") == "bearish"]
    print(f"  Total rows with MSO D1=bearish: {len(bear_d1)}")
    if bear_d1:
        ai_on_bear = Counter(r.get("daily_bias_direction") for r in bear_d1)
        print(f"  AI bias on those rows: {dict(ai_on_bear)}")
        decisions = Counter(r.get("decision") for r in bear_d1)
        print(f"  Decisions on those rows: {dict(decisions)}")
        for r in bear_d1[:5]:
            print(f"   ex: {r.get('symbol')} {r.get('timestamp_utc')[:16]} "
                  f"mso_d1={r.get('mso_d1_structure_direction')} "
                  f"mso_h1={r.get('mso_h1_structure_direction')} "
                  f"mso_m15={r.get('mso_m15_structure_direction')} "
                  f"ai={r.get('daily_bias_direction')} "
                  f"decision={r.get('decision')}")

    # And MSO H1=bearish
    print("\n" + "=" * 80)
    print("FOCUS — MSO H1 direction == 'bearish' (prompt says report H1 as bias)")
    print("=" * 80)
    bear_h1 = [r for r in rows if r.get("mso_h1_structure_direction") == "bearish"]
    print(f"  Total rows with MSO H1=bearish: {len(bear_h1)}")
    if bear_h1:
        ai_on_bear = Counter(r.get("daily_bias_direction") for r in bear_h1)
        print(f"  AI bias on those rows: {dict(ai_on_bear)}")
        decisions = Counter(r.get("decision") for r in bear_h1)
        print(f"  Decisions on those rows: {dict(decisions)}")


if __name__ == "__main__":
    main()
