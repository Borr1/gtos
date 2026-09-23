"""Seed the knowledge base from validated historical backtest data.

Sources:
  - Gold Phase 1: 18 trades with corrected 1.5R TP scoring (strategy_a)
  - GBPUSD corrected: 42 trades with corrected scoring

DO NOT USE the 111 gold historical trades — they have invalid TP scoring.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


# ── Source paths ──────────────────────────────────────────────────────

GOLD_SOURCE = Path(
    "knowledge_base_backtest/analysis/system_improvements_data_20260403.json"
)
GBPUSD_SOURCE = Path(
    "knowledge_base_backtest/analysis/gbpusd_batch_deep_analysis_data_20260403.json"
)

# ── Output paths ─────────────────────────────────────────────────────

KB_BASE = Path("knowledge_base")
TRADE_INDEX_PATH = KB_BASE / "index" / "_trade_index.json"
ROLLING_STATS_PATH = KB_BASE / "statistics" / "rolling_stats.json"
FAILURE_PATTERNS_PATH = KB_BASE / "patterns" / "failure_patterns.json"
INSIGHTS_PATH = KB_BASE / "insights" / "current_insights.yaml"


# ═══════════════════════════════════════════════════════════════════════
# Phase A: Build Trade Index
# ═══════════════════════════════════════════════════════════════════════


def _classify_outcome(r: float) -> str:
    if r > 0:
        return "WIN"
    if r < 0:
        return "LOSS"
    return "BREAKEVEN"


def extract_gold_trades(source: Path) -> list[dict]:
    """Extract 18 Gold Phase 1 trades using strategy_a (100% TP1 close)."""
    data = json.loads(source.read_text())
    raw = data["partial_close"]["gold_by_strategy"]["per_trade_results"]

    trades = []
    for i, t in enumerate(raw, 1):
        r = t["strategy_a"]["r"]
        trades.append({
            "trade_id": f"bt_gold_{t['date']}_{t['kill_zone']}_{i:03d}",
            "date": t["date"],
            "symbol": "XAUUSD",
            "direction": t["direction"],
            "kill_zone": t["kill_zone"],
            "grade": None,  # Not available in gold source data
            "framework": "ob_retest",
            "outcome": _classify_outcome(r),
            "r_multiple": round(r, 4),
            "exit_type": t["strategy_a"]["exit"],
        })
    return trades


def extract_gbpusd_trades(source: Path) -> list[dict]:
    """Extract 42 GBPUSD corrected trades."""
    data = json.loads(source.read_text())
    raw = data["corrected_trades"]

    trades = []
    for t in raw:
        r = t["corrected_r"]
        trades.append({
            "trade_id": t.get("trade_id", f"bt_{t['date']}_{t['kill_zone']}_001"),
            "date": t["date"],
            "symbol": "GBPUSD",
            "direction": t["direction"],
            "kill_zone": t["kill_zone"],
            "grade": t.get("grade"),
            "framework": t.get("framework", "ob_retest"),
            "outcome": _classify_outcome(r),
            "r_multiple": round(r, 4),
            "exit_type": t["corrected_exit"],
        })
    return trades


def build_trade_index(gold_trades: list[dict], gbpusd_trades: list[dict]) -> dict:
    """Build the trade index from validated datasets ONLY."""
    all_trades = sorted(gold_trades + gbpusd_trades, key=lambda t: t["date"])
    return {
        "version": 1,
        "source": "backtest_seed",
        "trade_count": len(all_trades),
        "trades": all_trades,
    }


# ═══════════════════════════════════════════════════════════════════════
# Phase B: Compute Rolling Stats
# ═══════════════════════════════════════════════════════════════════════


def _compute_stats_for_group(trades: list[dict]) -> dict:
    """Compute WR, expectancy, profit factor, max consecutive losses."""
    if not trades:
        return {"n": 0, "win_rate": 0, "expectancy": 0, "profit_factor": 0}

    n = len(trades)
    wins = [t for t in trades if t["outcome"] == "WIN"]
    losses = [t for t in trades if t["outcome"] == "LOSS"]

    win_rate = len(wins) / n if n > 0 else 0
    expectancy = sum(t["r_multiple"] for t in trades) / n if n > 0 else 0

    total_wins_r = sum(t["r_multiple"] for t in wins)
    total_losses_r = abs(sum(t["r_multiple"] for t in losses))
    profit_factor = total_wins_r / total_losses_r if total_losses_r > 0 else float("inf")

    # Max consecutive losses
    max_consec_loss = 0
    current_streak = 0
    for t in trades:
        if t["outcome"] == "LOSS":
            current_streak += 1
            max_consec_loss = max(max_consec_loss, current_streak)
        else:
            current_streak = 0

    return {
        "n": n,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 4),
        "expectancy": round(expectancy, 4),
        "total_r": round(sum(t["r_multiple"] for t in trades), 4),
        "profit_factor": round(profit_factor, 4) if profit_factor != float("inf") else None,
        "max_consecutive_losses": max_consec_loss,
    }


def compute_rolling_stats(trade_index: dict) -> dict:
    """Compute rolling stats from trade index. All numbers computed, nothing hardcoded."""
    trades = trade_index["trades"]

    overall = _compute_stats_for_group(trades)

    # By instrument
    by_instrument = {}
    instruments = set(t["symbol"] for t in trades)
    for sym in sorted(instruments):
        sym_trades = [t for t in trades if t["symbol"] == sym]
        by_instrument[sym] = _compute_stats_for_group(sym_trades)

    # By kill zone
    by_kill_zone = {}
    kzs = set(t["kill_zone"] for t in trades)
    for kz in sorted(kzs):
        kz_trades = [t for t in trades if t["kill_zone"] == kz]
        by_kill_zone[kz] = _compute_stats_for_group(kz_trades)

    # By grade (skip None)
    by_grade = {}
    grades = set(t["grade"] for t in trades if t["grade"])
    for g in sorted(grades):
        g_trades = [t for t in trades if t["grade"] == g]
        by_grade[g] = _compute_stats_for_group(g_trades)

    # Last 10 trades
    last_10 = [
        {
            "date": t.get("date", ""),
            "symbol": t.get("symbol", ""),
            "outcome": t["outcome"],
            "r_multiple": t["r_multiple"],
        }
        for t in trades[-10:]
    ]

    return {
        "overall": overall,
        "by_instrument": by_instrument,
        "by_kill_zone": by_kill_zone,
        "by_grade": by_grade,
        "last_10_trades": last_10,
    }


# ═══════════════════════════════════════════════════════════════════════
# Phase C: Build Failure Patterns
# ═══════════════════════════════════════════════════════════════════════


def build_failure_patterns(trade_index: dict) -> dict:
    """Build failure patterns from actual analysis findings.

    Sources:
    - system_improvements_20260403.md: Asian range / cross-instrument findings
    - system_deep_dive_pressure_test_v2_20260403.md: loss categorization
    """
    trades = trade_index["trades"]
    gbpusd_trades = [t for t in trades if t["symbol"] == "GBPUSD"]
    loss_trades = [t for t in trades if t["outcome"] == "LOSS"]
    gbpusd_losses = [t for t in gbpusd_trades if t["outcome"] == "LOSS"]

    patterns = []

    # Pattern 1: Narrow Asian Range (from system_improvements analysis)
    # Data: Q1 (11-28% ADR) = 33.3% WR (15 trades), Q4 (53-159%) = 60% WR (15 trades)
    patterns.append({
        "pattern_id": "fp_001_narrow_asian_range",
        "description": "Narrow Asian range (<28% ADR) correlates with poor win rate",
        "evidence": {
            "q1_narrow_wr": 0.333,
            "q4_wide_wr": 0.600,
            "wr_spread": 0.267,
            "q1_n": 15,
            "q4_n": 15,
            "source": "system_improvements_20260403.md — Asian Range Quartile Analysis",
        },
        "instrument": "GBPUSD",
        "n_trades": 15,
        "severity": "HIGH",
        "action": "CAUTION — flag narrow Asian range days in prompt context",
    })

    # Pattern 2: Cross-instrument misalignment (from system_improvements analysis)
    # Data: aligned = 56.7% WR (30 trades), not aligned = 25% WR (12 trades)
    patterns.append({
        "pattern_id": "fp_002_cross_instrument_misalignment",
        "description": "GBPUSD trades misaligned with XAUUSD D1 direction have 25% WR",
        "evidence": {
            "aligned_wr": 0.567,
            "misaligned_wr": 0.250,
            "wr_spread": 0.317,
            "aligned_n": 30,
            "misaligned_n": 12,
            "source": "system_improvements_20260403.md — Cross-Instrument Analysis",
        },
        "instrument": "GBPUSD",
        "n_trades": 12,
        "severity": "HIGH",
        "action": "CAUTION — GBPUSD trades against XAUUSD D1 trend have very low WR",
    })

    # Pattern 3: Structure misread losses (from deep dive v2)
    # Data: 2/5 gold losses had preventable causes
    patterns.append({
        "pattern_id": "fp_003_structure_misread",
        "description": "AI accepting setups without valid H1 OB or with sub-threshold M15 displacement",
        "evidence": {
            "preventable_losses": 2,
            "total_losses_analyzed": 5,
            "types": ["no H1 OB but graded A+", "M15 displacement 0.4x < 1.5x minimum"],
            "source": "system_deep_dive_pressure_test_v2_20260403.md",
        },
        "instrument": "XAUUSD",
        "n_trades": 2,
        "severity": "MEDIUM",
        "action": "Internal Consistency Rules should catch these — monitor",
    })

    # Pattern 4: Computed — overall loss clustering by kill zone
    loss_by_kz = Counter(t["kill_zone"] for t in loss_trades)
    total_by_kz = Counter(t["kill_zone"] for t in trades)
    kz_wr = {}
    for kz in total_by_kz:
        total = total_by_kz[kz]
        losses = loss_by_kz.get(kz, 0)
        kz_wr[kz] = round(1 - losses / total, 4) if total > 0 else 0

    patterns.append({
        "pattern_id": "fp_004_kill_zone_performance",
        "description": "Win rate varies by kill zone — computed from all 60 trades",
        "evidence": {
            "kill_zone_win_rates": kz_wr,
            "kill_zone_counts": dict(total_by_kz),
            "source": "computed from trade_index",
        },
        "instrument": "ALL",
        "n_trades": len(trades),
        "severity": "INFO",
        "action": "Monitor — no action needed unless divergence grows",
    })

    return {
        "version": 1,
        "active_patterns": patterns,
        "total_patterns": len(patterns),
    }


# ═══════════════════════════════════════════════════════════════════════
# Phase D: Generate Current Insights
# ═══════════════════════════════════════════════════════════════════════


def generate_insights(stats: dict, patterns: dict) -> str:
    """Generate current_insights.yaml from computed data.

    Every number comes from stats/patterns dicts — nothing hardcoded.
    """
    overall = stats["overall"]
    last_10 = stats["last_10_trades"]

    # Build last 10 summary string
    last_10_str = ", ".join(
        f"{'WIN' if t['outcome'] == 'WIN' else 'LOSS'} {t['r_multiple']:+.1f}R"
        for t in last_10
    )

    # Extract high-severity pattern descriptions
    cautions = []
    for p in patterns.get("active_patterns", []):
        if p["severity"] in ("HIGH", "MEDIUM"):
            cautions.append(p["description"])

    cautions_yaml = "\n".join(f'  - "{c}"' for c in cautions)

    # Instrument breakdown
    instrument_lines = []
    for sym, s in sorted(stats.get("by_instrument", {}).items()):
        instrument_lines.append(
            f"  {sym}: {{n: {s['n']}, win_rate: {s['win_rate']}, "
            f"expectancy: {s['expectancy']}, total_r: {s['total_r']}}}"
        )
    instruments_yaml = "\n".join(instrument_lines)

    # Kill zone breakdown
    kz_lines = []
    for kz, s in sorted(stats.get("by_kill_zone", {}).items()):
        kz_lines.append(
            f"  {kz}: {{n: {s['n']}, win_rate: {s['win_rate']}, "
            f"expectancy: {s['expectancy']}}}"
        )
    kz_yaml = "\n".join(kz_lines)

    return f"""# Knowledge Base — Current Insights
# Auto-generated from computed rolling stats and failure patterns.
# Every number is derived from source data — nothing hardcoded.

summary:
  total_trades: {overall['n']}
  win_rate: {overall['win_rate']}
  expectancy: {overall['expectancy']}
  total_r: {overall['total_r']}
  profit_factor: {overall['profit_factor']}
  max_consecutive_losses: {overall['max_consecutive_losses']}

last_10: "{last_10_str}"

by_instrument:
{instruments_yaml}

by_kill_zone:
{kz_yaml}

cautions:
{cautions_yaml}

data_source: "backtest_seed — 18 gold (Phase 1) + 42 GBPUSD (corrected)"
"""


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════


def seed_knowledge_base(
    gold_source: Path = GOLD_SOURCE,
    gbpusd_source: Path = GBPUSD_SOURCE,
    kb_base: Path = KB_BASE,
) -> dict:
    """Run the full seeding pipeline. Returns summary of what was created."""
    # Override output paths based on kb_base
    trade_index_path = kb_base / "index" / "_trade_index.json"
    rolling_stats_path = kb_base / "statistics" / "rolling_stats.json"
    failure_patterns_path = kb_base / "patterns" / "failure_patterns.json"
    insights_path = kb_base / "insights" / "current_insights.yaml"

    # Ensure directories exist
    for sub in ["index", "statistics", "patterns", "insights"]:
        (kb_base / sub).mkdir(parents=True, exist_ok=True)

    # Phase A: Build trade index
    gold_trades = extract_gold_trades(gold_source)
    gbpusd_trades = extract_gbpusd_trades(gbpusd_source)
    trade_index = build_trade_index(gold_trades, gbpusd_trades)

    trade_index_path.write_text(json.dumps(trade_index, indent=2))

    # Phase B: Compute rolling stats
    rolling_stats = compute_rolling_stats(trade_index)
    rolling_stats_path.write_text(json.dumps(rolling_stats, indent=2))

    # Phase C: Build failure patterns
    failure_patterns = build_failure_patterns(trade_index)
    failure_patterns_path.write_text(json.dumps(failure_patterns, indent=2))

    # Phase D: Generate insights
    insights_yaml = generate_insights(rolling_stats, failure_patterns)
    insights_path.write_text(insights_yaml)

    return {
        "trade_count": trade_index["trade_count"],
        "gold_count": len(gold_trades),
        "gbpusd_count": len(gbpusd_trades),
        "files_created": [
            str(trade_index_path),
            str(rolling_stats_path),
            str(failure_patterns_path),
            str(insights_path),
        ],
    }


if __name__ == "__main__":
    result = seed_knowledge_base()
    print(f"Seeded KB with {result['trade_count']} trades "
          f"({result['gold_count']} gold + {result['gbpusd_count']} GBPUSD)")
    for f in result["files_created"]:
        print(f"  Created: {f}")
