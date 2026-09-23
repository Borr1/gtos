#!/usr/bin/env python3
"""Dumb-momentum-baseline live shadow vs real fills comparison.

Companion to ``src/components/dumb_baseline_shadow_logger.py``.

What this script does
---------------------
Aligns the dumb-baseline hypotheticals JSONL (one row per fired hypothesis)
with the production trade records (``knowledge_base/trade_records/<sym>/*.json``)
by (symbol, candle date) and produces three views:

    1. Per-day count: real CANDIDATEs vs dumb hypotheticals.
    2. Overlap analysis: when both fire on the same day, did decisions match?
       Did outcomes match?
    3. Disjoint analysis: when dumb fires but the AI does not — what was the
       AI's last decision that day, and what was the dumb hypothetical's
       outcome?

Outputs
-------
Two artifacts under ``research/dumb_baseline_live/``:

* ``comparison.csv`` — per-day rolled-up table of real CAND counts vs dumb
  hypothetical counts vs WR-each-side vs Exp-R-each-side.
* ``summary.md`` — narrative summary (top-line counts + per-symbol breakdown).

The script is read-only: it reads the JSONL + trade records and writes only
the two output files.

Usage
-----
    python scripts/dumb_baseline_compare.py \
        [--shadow-log shadow_logs/dumb_baseline_hypotheticals.jsonl] \
        [--trade-dir knowledge_base/trade_records] \
        [--output-dir research/dumb_baseline_live]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def _iter_jsonl_records(path: Path) -> Iterable[dict]:
    """Yield each JSON object from a JSONL file, skipping unparseable lines."""
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _date_from_iso(iso_ts: Optional[str]) -> Optional[str]:
    """Return YYYY-MM-DD or None for any unparseable input."""
    if not iso_ts:
        return None
    try:
        ts = datetime.fromisoformat(str(iso_ts).replace("Z", "+00:00"))
        return ts.strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def _load_hypotheticals(path: Path) -> list[dict]:
    """Parse the dumb-baseline JSONL. Each entry is a hypothesis record."""
    return list(_iter_jsonl_records(path))


def _load_trade_records(trade_dir: Path) -> list[dict]:
    """Walk knowledge_base/trade_records/<sym>/*.json and return trade dicts.

    Each record is annotated with `{"_symbol": <symbol>, "_filename": <name>,
    "_date": <YYYY-MM-DD or None>}` for downstream grouping.
    """
    out: list[dict] = []
    if not trade_dir.exists():
        return out

    for symbol_dir in sorted(trade_dir.iterdir()):
        if not symbol_dir.is_dir():
            continue
        for fp in sorted(symbol_dir.glob("*.json")):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    rec = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(rec, dict):
                continue
            md = rec.get("metadata") if isinstance(rec.get("metadata"), dict) else {}
            sym = md.get("symbol") or symbol_dir.name
            iso_ct = md.get("candle_time")
            d = _date_from_iso(iso_ct) or md.get("date")
            rec["_symbol"] = sym
            rec["_filename"] = fp.name
            rec["_date"] = d
            out.append(rec)
    return out


# ---------------------------------------------------------------------------
# Decision extraction
# ---------------------------------------------------------------------------


def _ai_decision_of(record: dict) -> str:
    """Pull the AI gate decision from a trade record. Returns 'CANDIDATE'/'NO_TRADE'/'UNKNOWN'."""
    pipeline = record.get("decision_pipeline") if isinstance(record.get("decision_pipeline"), dict) else {}
    val = pipeline.get("ai_decision")
    if val in ("CANDIDATE", "NO_TRADE"):
        return val
    return "UNKNOWN"


def _final_outcome_of(record: dict) -> str:
    """Pull the trade record's final outcome. Returns the literal string or 'UNKNOWN'."""
    val = record.get("final_outcome")
    return str(val) if val else "UNKNOWN"


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _bucket_by_symbol_date(items: list[dict], date_key: str = "_date", symbol_key: str = "_symbol") -> dict[tuple[str, str], list[dict]]:
    """Group records by (symbol, YYYY-MM-DD)."""
    out: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for it in items:
        sym = it.get(symbol_key)
        d = it.get(date_key)
        if not sym or not d:
            continue
        out[(sym, d)].append(it)
    return out


def _hyp_bucket(hypotheticals: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """Group hypotheticals by (symbol, candle_time YYYY-MM-DD)."""
    out: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for h in hypotheticals:
        sym = h.get("symbol")
        d = _date_from_iso(h.get("candle_time")) or _date_from_iso(h.get("timestamp_utc"))
        if not sym or not d:
            continue
        out[(sym, d)].append(h)
    return out


def _summary_block(records: list[dict], r_field: str = "realized_r", outcome_field: str = "outcome") -> dict:
    """WR / Exp R / total R block. `records` need ``outcome_field`` + ``r_field`` populated."""
    resolved = [r for r in records if r.get(outcome_field) in ("TP", "SL", "TIMEOUT")]
    n = len(resolved)
    wins = sum(1 for r in resolved if r.get(outcome_field) == "TP")
    rs = [float(r.get(r_field) or 0.0) for r in resolved]
    total = round(sum(rs), 3)
    exp = round(total / n, 3) if n else 0.0
    wr = round(wins / n * 100, 1) if n else 0.0
    return {
        "n": n, "wins": wins, "losses": n - wins,
        "wr_pct": wr, "expectancy_r": exp, "total_r": total,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Dumb-baseline live shadow vs real-fill comparison")
    parser.add_argument(
        "--shadow-log",
        default="shadow_logs/dumb_baseline_hypotheticals.jsonl",
        help="Path to the dumb-baseline JSONL (default: shadow_logs/...).",
    )
    parser.add_argument(
        "--trade-dir",
        default="knowledge_base/trade_records",
        help="Path to the per-symbol trade-records directory.",
    )
    parser.add_argument(
        "--output-dir",
        default="research/dumb_baseline_live",
        help="Directory for the comparison.csv + summary.md outputs.",
    )
    args = parser.parse_args()

    shadow_path = Path(args.shadow_log)
    trade_dir = Path(args.trade_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    hypotheticals = _load_hypotheticals(shadow_path)
    trade_records = _load_trade_records(trade_dir)

    print(f"Loaded {len(hypotheticals)} dumb hypotheticals from {shadow_path}")
    print(f"Loaded {len(trade_records)} trade records from {trade_dir}")

    # Bucket by (symbol, day).
    hyp_buckets = _hyp_bucket(hypotheticals)
    trade_buckets = _bucket_by_symbol_date(trade_records)

    # Per-day comparison rows.
    all_keys = sorted(set(hyp_buckets.keys()) | set(trade_buckets.keys()))
    rows: list[dict] = []
    for (sym, day) in all_keys:
        hyps = hyp_buckets.get((sym, day), [])
        recs = trade_buckets.get((sym, day), [])
        ai_cands = sum(1 for r in recs if _ai_decision_of(r) == "CANDIDATE")
        ai_no_trades = sum(1 for r in recs if _ai_decision_of(r) == "NO_TRADE")
        rows.append({
            "symbol": sym,
            "date": day,
            "real_evaluations": len(recs),
            "real_ai_candidates": ai_cands,
            "real_ai_no_trades": ai_no_trades,
            "dumb_hypotheticals": len(hyps),
            "dumb_resolved": sum(1 for h in hyps if h.get("outcome") in ("TP", "SL", "TIMEOUT")),
            "dumb_open": sum(1 for h in hyps if not h.get("outcome")),
            "ratio_dumb_over_real_cand": (
                round(len(hyps) / max(ai_cands, 1), 2) if ai_cands else None
            ),
        })

    # Write per-day CSV.
    csv_path = out_dir / "comparison.csv"
    fieldnames = [
        "symbol", "date", "real_evaluations", "real_ai_candidates",
        "real_ai_no_trades", "dumb_hypotheticals", "dumb_resolved",
        "dumb_open", "ratio_dumb_over_real_cand",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Wrote {csv_path} ({len(rows)} rows)")

    # Aggregate dumb-only stats.
    dumb_overall = _summary_block(hypotheticals)
    per_symbol_dumb: dict[str, dict] = {}
    by_sym_hyps: dict[str, list[dict]] = defaultdict(list)
    for h in hypotheticals:
        sym = h.get("symbol")
        if sym:
            by_sym_hyps[sym].append(h)
    for sym, hyps in sorted(by_sym_hyps.items()):
        per_symbol_dumb[sym] = _summary_block(hyps)

    # Overlap analysis: same (symbol, day) sees both a real CAND and a dumb fire.
    overlap_days = []
    for (sym, day) in sorted(set(hyp_buckets.keys()) & set(trade_buckets.keys())):
        hyps = hyp_buckets[(sym, day)]
        recs = trade_buckets[(sym, day)]
        ai_cand_recs = [r for r in recs if _ai_decision_of(r) == "CANDIDATE"]
        if ai_cand_recs and hyps:
            overlap_days.append({
                "symbol": sym, "date": day,
                "dumb_count": len(hyps),
                "real_cand_count": len(ai_cand_recs),
                "real_outcomes": [_final_outcome_of(r) for r in ai_cand_recs],
                "dumb_outcomes": [h.get("outcome") for h in hyps],
            })

    # Disjoint analysis: dumb fires but no real CAND that day.
    disjoint_dumb_only = []
    for (sym, day), hyps in sorted(hyp_buckets.items()):
        recs = trade_buckets.get((sym, day), [])
        if not any(_ai_decision_of(r) == "CANDIDATE" for r in recs):
            for h in hyps:
                disjoint_dumb_only.append({
                    "symbol": sym, "date": day,
                    "direction": h.get("direction"),
                    "outcome": h.get("outcome"),
                    "realized_r": h.get("realized_r"),
                })

    # Write summary.md.
    md_path = out_dir / "summary.md"
    md_lines: list[str] = []
    md_lines.append("# Dumb-baseline live shadow vs real fills")
    md_lines.append("")
    md_lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    md_lines.append("")
    md_lines.append("## Top line")
    md_lines.append("")
    md_lines.append(f"- Dumb hypotheticals fired: **{len(hypotheticals)}**")
    md_lines.append(f"- Dumb resolved: **{dumb_overall['n']}** "
                    f"(wins={dumb_overall['wins']} losses={dumb_overall['losses']} "
                    f"WR={dumb_overall['wr_pct']}% Exp R={dumb_overall['expectancy_r']:+.3f} "
                    f"total={dumb_overall['total_r']:+.2f}R)")
    md_lines.append(f"- Real trade records: **{len(trade_records)}**")
    md_lines.append(f"- Days with both: **{len(overlap_days)}**")
    md_lines.append(f"- Days with dumb-only: **{len({(d['symbol'], d['date']) for d in disjoint_dumb_only})}**")
    md_lines.append("")
    md_lines.append("## Per-symbol dumb-baseline breakdown")
    md_lines.append("")
    md_lines.append("| Symbol | n | Wins | Losses | WR | Exp R | Total R |")
    md_lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for sym, blk in sorted(per_symbol_dumb.items()):
        md_lines.append(
            f"| {sym} | {blk['n']} | {blk['wins']} | {blk['losses']} | "
            f"{blk['wr_pct']}% | {blk['expectancy_r']:+.3f} | {blk['total_r']:+.2f} |"
        )
    md_lines.append("")
    md_lines.append("## Overlap days (real CAND + dumb fire)")
    md_lines.append("")
    if not overlap_days:
        md_lines.append("_None yet — accumulate live data to compare._")
    else:
        md_lines.append("| Symbol | Date | Real CAND n | Dumb n | Real outcomes | Dumb outcomes |")
        md_lines.append("|---|---|---:|---:|---|---|")
        for d in overlap_days:
            md_lines.append(
                f"| {d['symbol']} | {d['date']} | {d['real_cand_count']} | "
                f"{d['dumb_count']} | {','.join(d['real_outcomes'])} | "
                f"{','.join(str(x) for x in d['dumb_outcomes'])} |"
            )
    md_lines.append("")
    md_lines.append("## Disjoint days — dumb fired without any real CAND")
    md_lines.append("")
    if not disjoint_dumb_only:
        md_lines.append("_None yet — accumulate live data to compare._")
    else:
        md_lines.append(f"Total disjoint dumb fires: **{len(disjoint_dumb_only)}**")
        md_lines.append("")
        md_lines.append("First 25:")
        md_lines.append("")
        md_lines.append("| Symbol | Date | Direction | Outcome | R |")
        md_lines.append("|---|---|---|---|---:|")
        for d in disjoint_dumb_only[:25]:
            r_val = d['realized_r']
            r_disp = f"{r_val:+.2f}" if isinstance(r_val, (int, float)) else "-"
            md_lines.append(
                f"| {d['symbol']} | {d['date']} | {d['direction']} | "
                f"{d['outcome'] or 'OPEN'} | {r_disp} |"
            )

    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"Wrote {md_path}")

    # Print headline so this can be hooked into a watchdog cron.
    print("\n" + "=" * 60)
    print("DUMB-BASELINE LIVE SHADOW vs REAL FILLS — HEADLINE")
    print(f"  Dumb fires:    {len(hypotheticals)}")
    print(f"  Dumb resolved: {dumb_overall['n']} "
          f"(WR={dumb_overall['wr_pct']}% Exp={dumb_overall['expectancy_r']:+.3f}R)")
    print(f"  Real records:  {len(trade_records)}")
    print(f"  Overlap days:  {len(overlap_days)}")
    print(f"  Disjoint days: {len({(d['symbol'], d['date']) for d in disjoint_dumb_only})}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
