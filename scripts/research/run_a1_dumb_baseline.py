"""A1 — Full Historical Dumb-Baseline Replay (CLI driver).

Drives :mod:`src.research_infra.dumb_baseline` over every historical
trade record we have, computing the mechanical 80%-retrace OB-pullback
arm and joining to AI realized R. Outputs the per-CAND ``results.jsonl``,
the aggregate ``summary.json``, and the human-readable ``report.md``
ending with the strategic verdict block.

Phase 1 = $0 API. This script makes NO Anthropic / OpenRouter calls.

Usage
-----
Default full historical replay across all instruments::

    python scripts/research/run_a1_dumb_baseline.py \\
        --output-dir research/decay_diagnostic/A1_dumb_baseline

Filtered run::

    python scripts/research/run_a1_dumb_baseline.py \\
        --output-dir research/decay_diagnostic/A1_dumb_baseline \\
        --symbols XAUUSD,USDJPY \\
        --start 2026-01-01 --end 2026-04-30

Dry-run (no writes; prints plan; exits 0)::

    python scripts/research/run_a1_dumb_baseline.py \\
        --output-dir /tmp/scratch --dry-run

Environment / .env note
=======================
Per memory ``project_research_scripts_missing_dotenv.md`` research scripts
do NOT auto-load ``.env``. This script does not read ANY environment
variable (no API keys are needed — Phase 1 is $0). Run it directly:

    python scripts/research/run_a1_dumb_baseline.py --output-dir <dir>

If a future iteration adds env-driven config, prefix with::

    set -a && source .env && set +a
    python scripts/research/run_a1_dumb_baseline.py ...
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path

# Make the project root importable when this script is invoked as a file.
_THIS = Path(__file__).resolve()
_PROJECT_ROOT = _THIS.parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.research_infra.dumb_baseline import (  # noqa: E402
    DEFAULT_OHLCV_DIR,
    DEFAULT_TRADE_RECORDS_DIR,
    HARNESS_VERSION,
    BaselineConfig,
    BatchSessionReplay,
    DumbBaselineReplay,
    _count_batch_records,
    aggregate,
    write_report_md,
    write_results_jsonl,
    write_summary_json,
)

#: Default location of batch sessions (alternative to trade_records).
DEFAULT_BATCH_SESSIONS_DIR = _PROJECT_ROOT / "knowledge_base_backtest" / "sessions"


def _parse_date(s: str) -> dt.datetime:
    """Parse a YYYY-MM-DD string to a UTC datetime at 00:00."""
    parsed = dt.datetime.strptime(s, "%Y-%m-%d")
    return parsed.replace(tzinfo=dt.timezone.utc)


def _parse_symbols(s: str) -> list[str]:
    return [p.strip() for p in s.split(",") if p.strip()]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_a1_dumb_baseline",
        description=(
            "A1 — Full Historical Dumb-Baseline Replay. "
            "Mechanical 80%-retrace OB-pullback baseline; pure OHLCV replay; no API calls."
        ),
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for results.jsonl + summary.json + report.md.",
    )
    p.add_argument(
        "--symbols",
        type=_parse_symbols,
        default=None,
        help=(
            "Comma-separated list of instruments to include. "
            "Default: every directory under knowledge_base/trade_records/."
        ),
    )
    p.add_argument(
        "--start",
        type=_parse_date,
        default=None,
        help="Earliest candle_close_time (YYYY-MM-DD inclusive). Default: no floor.",
    )
    p.add_argument(
        "--end",
        type=_parse_date,
        default=None,
        help="Latest candle_close_time (YYYY-MM-DD inclusive). Default: no ceiling.",
    )
    p.add_argument(
        "--source",
        choices=("trade_records", "batch_sessions", "both"),
        default="both",
        help=(
            "Where to read CANDs from. "
            "`trade_records` uses knowledge_base/trade_records/ (full MSO; "
            "but realized AI R is rarely populated). "
            "`batch_sessions` uses knowledge_base_backtest/sessions/{SYMBOL}/ "
            "(realized AI R + candle_time + trade_id; no MSO so the "
            "mechanical arm derives the OB target from raw OHLCV). "
            "`both` (default) runs both and concatenates."
        ),
    )
    p.add_argument(
        "--trade-records-dir",
        type=Path,
        default=DEFAULT_TRADE_RECORDS_DIR,
        help="Override for knowledge_base/trade_records/.",
    )
    p.add_argument(
        "--batch-sessions-dir",
        type=Path,
        default=DEFAULT_BATCH_SESSIONS_DIR,
        help="Override for knowledge_base_backtest/sessions/.",
    )
    p.add_argument(
        "--ohlcv-dir",
        type=Path,
        default=DEFAULT_OHLCV_DIR,
        help="Override for data/historical_2026/.",
    )
    p.add_argument(
        "--max-hold-bars",
        type=int,
        default=None,
        help=(
            "M15 bars to walk forward before declaring TIMEOUT. "
            "Default: 96 (24h)."
        ),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Plan only — count records that would be replayed, list filters, "
            "exit 0 without writing to --output-dir."
        ),
    )
    p.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG / INFO / WARNING). Default: INFO.",
    )
    return p


def _count_records(replay: DumbBaselineReplay) -> int:
    """Count records that would be replayed under the current filter."""
    n = 0
    from src.research_infra.dumb_baseline import _iter_trade_records  # internal
    for _, _ in _iter_trade_records(replay.trade_records_dir, replay.instruments):
        n += 1
    return n


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    log = logging.getLogger("a1")

    # Build the replay
    cfg = BaselineConfig.from_yaml()
    if args.max_hold_bars is not None:
        cfg = BaselineConfig(
            sl_buffer_atr_multiplier=cfg.sl_buffer_atr_multiplier,
            sl_buffer_min_ticks=cfg.sl_buffer_min_ticks,
            min_rr=cfg.min_rr,
            retrace_pct=cfg.retrace_pct,
            max_hold_bars=int(args.max_hold_bars),
        )

    tr_replay = DumbBaselineReplay(
        trade_records_dir=args.trade_records_dir,
        ohlcv_dir=args.ohlcv_dir,
        cfg=cfg,
        instruments=args.symbols,
        since=args.start,
        until=args.end,
    )
    bs_replay = BatchSessionReplay(
        sessions_root=args.batch_sessions_dir,
        ohlcv_dir=args.ohlcv_dir,
        cfg=cfg,
        instruments=args.symbols,
        since=args.start,
        until=args.end,
    )

    # Plan summary
    log.info("Harness version: %s", HARNESS_VERSION)
    log.info("source: %s", args.source)
    log.info("trade_records_dir: %s", tr_replay.trade_records_dir.resolve())
    log.info("batch_sessions_dir: %s", bs_replay.sessions_root.resolve())
    log.info("ohlcv_dir: %s", tr_replay.ohlcv_dir.resolve())
    log.info("output_dir: %s", args.output_dir.resolve())
    log.info("symbols filter: %s", args.symbols or "ALL")
    log.info("start: %s, end: %s", args.start, args.end)
    log.info(
        "config: retrace_pct=%.2f, atr_mult=%.2f, min_ticks=%d, min_rr=%.2f, "
        "max_hold_bars=%d",
        cfg.retrace_pct,
        cfg.sl_buffer_atr_multiplier,
        cfg.sl_buffer_min_ticks,
        cfg.min_rr,
        cfg.max_hold_bars,
    )

    tr_count = _count_records(tr_replay) if args.source in ("trade_records", "both") else 0
    bs_count = _count_batch_records(bs_replay) if args.source in ("batch_sessions", "both") else 0
    log.info(
        "Records that match the filter: trade_records=%d, batch_sessions=%d",
        tr_count, bs_count,
    )

    if args.dry_run:
        log.info("--dry-run: not writing anything; exiting 0.")
        # Print machine-readable plan to stdout for piping
        plan = {
            "harness_version": HARNESS_VERSION,
            "source": args.source,
            "output_dir": str(args.output_dir.resolve()),
            "symbols": args.symbols,
            "start": args.start.isoformat() if args.start else None,
            "end": args.end.isoformat() if args.end else None,
            "record_count": tr_count + bs_count,
            "trade_records_count": tr_count,
            "batch_sessions_count": bs_count,
            "config": asdict(cfg),
            "dry_run": True,
        }
        print(json.dumps(plan, indent=2, default=str))
        return 0

    # Run
    rows = []
    if args.source in ("trade_records", "both"):
        log.info("Replaying %d trade-records...", tr_count)
        rows.extend(tr_replay.run())
    if args.source in ("batch_sessions", "both"):
        log.info("Replaying %d batch-session CANDs...", bs_count)
        rows.extend(bs_replay.run())
    log.info("Replay produced %d rows", len(rows))
    summary = aggregate(rows)

    # Add run metadata
    summary["run_metadata"] = {
        "harness_version": HARNESS_VERSION,
        "source": args.source,
        "output_dir": str(args.output_dir.resolve()),
        "symbols_filter": args.symbols,
        "start": args.start.isoformat() if args.start else None,
        "end": args.end.isoformat() if args.end else None,
        "trade_records_dir": str(args.trade_records_dir.resolve()),
        "batch_sessions_dir": str(args.batch_sessions_dir.resolve()),
        "ohlcv_dir": str(args.ohlcv_dir.resolve()),
        "config": asdict(cfg),
        "trade_records_count": tr_count,
        "batch_sessions_count": bs_count,
        "row_count": len(rows),
    }

    out = args.output_dir
    write_results_jsonl(rows, out / "results.jsonl")
    write_summary_json(summary, out / "summary.json")
    write_report_md(rows, summary, out / "report.md")

    verdict = summary.get("verdict", {})
    log.info(
        "Verdict: %s — %s",
        verdict.get("diagnosis", "?"),
        verdict.get("reasoning", ""),
    )
    log.info("Wrote: %s", (out / "results.jsonl").resolve())
    log.info("Wrote: %s", (out / "summary.json").resolve())
    log.info("Wrote: %s", (out / "report.md").resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
