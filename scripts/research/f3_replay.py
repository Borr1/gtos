"""L58 — F3-replay CLI driver.

Drives :mod:`src.research_infra.f3_replay_engine` from the command line:

  - resolves the named evaluators (``recorded`` | ``mock_seed_<N>``;
    ``live`` is opt-in behind ``GTOS_F3_REPLAY_ALLOW_LIVE=1``),
  - loads historical candidates with date / instrument filters,
  - optionally joins realized R from a trade-records directory,
  - runs the paired replay (or prints the plan in ``--dry-run`` mode),
  - writes ``replay_results.jsonl``, ``replay_summary.md``, and
    ``run_metadata.json`` to the caller-supplied ``--output`` directory.

NON-GOALS
---------
- Calling the real Anthropic API. ``--evaluator-* live`` is gated behind
  the env variable above and Wave 1 deliberately does not exercise it.
- Modifying production code under ``src/components/``. The CLI imports
  the engine, the engine imports nothing from production.

Examples
--------
Pure dry-run (lists planned candidates, no API, no writes)::

    python scripts/research/f3_replay.py \\
        --evaluator-a recorded \\
        --evaluator-b mock_seed_42 \\
        --since 2026-04-01 --until 2026-04-25 \\
        --instruments XAUUSD,GBPJPY \\
        --output research/f3_replay_smoke \\
        --dry-run

Real run (mocked evaluators only — Wave 1)::

    python scripts/research/f3_replay.py \\
        --evaluator-a recorded \\
        --evaluator-b mock_seed_1 \\
        --instruments XAUUSD \\
        --output research/f3_replay_xau_baseline \\
        --realized-r-join knowledge_base/trade_records \\
        --run-tag phase1_l58_xau_smoke
"""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import Optional, Sequence

# Allow running as `python scripts/research/f3_replay.py` from the
# project root (preferred) or via `python -m scripts.research.f3_replay`.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.f3_replay_engine import (  # noqa: E402
    DEFAULT_EVAL_DIR,
    HARNESS_VERSION,
    HistoricalCandidate,
    LiveReplayEvaluator,
    MockReplayEvaluator,
    RecordedReplayEvaluator,
    ReplayEvaluator,
    ReplayRun,
    load_historical_candidates,
)


logger = logging.getLogger("f3_replay")


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def _setup_logging(verbose: bool = False) -> None:
    if logger.handlers:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)


# ---------------------------------------------------------------------------
# Evaluator resolution
# ---------------------------------------------------------------------------


_MOCK_RE = re.compile(r"^mock_seed_(\d+)$")


def resolve_evaluator(name: str) -> ReplayEvaluator:
    """Resolve a CLI ``--evaluator-*`` name to a concrete evaluator.

    Built-in names:
      * ``recorded`` — :class:`RecordedReplayEvaluator`
      * ``mock_seed_<N>`` — :class:`MockReplayEvaluator(seed=N)` for any
        non-negative integer ``N``
      * ``live`` — :class:`LiveReplayEvaluator`. Construction raises
        unless ``GTOS_F3_REPLAY_ALLOW_LIVE=1`` AND a configured Anthropic
        client is available. Wave 1 does NOT exercise this path.
    """
    if name == "recorded":
        return RecordedReplayEvaluator()
    m = _MOCK_RE.match(name)
    if m:
        return MockReplayEvaluator(seed=int(m.group(1)))
    if name == "live":
        # Live evaluator requires an Anthropic client; CLI Wave 1 does
        # not wire one. Always fail fast with a precise message.
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError:
            raise RuntimeError(
                "--evaluator-* live requires the `anthropic` SDK and "
                "GTOS_F3_REPLAY_ALLOW_LIVE=1 — neither path is "
                "exercised in Wave 1."
            )
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "--evaluator-* live requires ANTHROPIC_API_KEY env var."
            )
        client = Anthropic(api_key=api_key)
        return LiveReplayEvaluator(client=client)
    raise ValueError(
        f"Unknown evaluator name {name!r}. "
        "Built-ins: 'recorded', 'mock_seed_<N>'. "
        "'live' is gated behind GTOS_F3_REPLAY_ALLOW_LIVE=1."
    )


# ---------------------------------------------------------------------------
# Filter helpers
# ---------------------------------------------------------------------------


def _parse_date(s: Optional[str]) -> Optional[dt.datetime]:
    """Parse an ISO-8601 date or datetime string. Naive values are
    treated as UTC. Returns ``None`` when ``s`` is falsy."""
    if not s:
        return None
    txt = s.strip()
    if txt.endswith("Z"):
        txt = txt[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(txt)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid ISO-8601 date {s!r}: {exc}"
        )
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def _parse_instruments(s: Optional[str]) -> Optional[list[str]]:
    """Parse a comma-separated instruments string. Returns ``None`` when
    the user did not pass ``--instruments``."""
    if not s:
        return None
    out = [tok.strip().upper() for tok in s.split(",") if tok.strip()]
    return out or None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="f3_replay",
        description=(
            "F3-replay CLI: replay historical candidates through paired "
            "evaluators and emit results + summary. "
            "(Phase 1 — Wave 1 mocked-only.)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Built-in evaluator names:
              recorded         — return the historical decision verbatim
              mock_seed_<N>    — deterministic mock with seed N
              live             — gated behind GTOS_F3_REPLAY_ALLOW_LIVE=1
                                 (NOT used in Wave 1)
            """
        ).strip(),
    )
    parser.add_argument(
        "--evaluator-a",
        required=True,
        help=(
            "Name of evaluator A. Built-ins: 'recorded', "
            "'mock_seed_<N>', 'live' (gated)."
        ),
    )
    parser.add_argument(
        "--evaluator-b",
        required=True,
        help="Name of evaluator B (same options as --evaluator-a).",
    )
    parser.add_argument(
        "--eval-dir",
        default=str(DEFAULT_EVAL_DIR),
        help=(
            "Directory containing live_evaluations JSONL files. "
            f"Default: {DEFAULT_EVAL_DIR}"
        ),
    )
    parser.add_argument(
        "--realized-r-join",
        default=None,
        help=(
            "Optional path to a trade-records dir (e.g. "
            "knowledge_base/trade_records). When provided, realized R "
            "is joined into each candidate via L56's "
            "(symbol, candle_close_time, side) contract."
        ),
    )
    parser.add_argument(
        "--since",
        default=None,
        help=(
            "Inclusive lower bound on candle_close_time (ISO-8601). "
            "Naive values treated as UTC."
        ),
    )
    parser.add_argument(
        "--until",
        default=None,
        help="Inclusive upper bound on candle_close_time (ISO-8601).",
    )
    parser.add_argument(
        "--instruments",
        default=None,
        help=(
            "Comma-separated instrument list (e.g. 'XAUUSD,USDJPY'). "
            "Case-insensitive. Default: all instruments under --eval-dir."
        ),
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory.",
    )
    parser.add_argument(
        "--run-tag",
        default="phase1_l58_replay",
        help=(
            "Stable tag for run_metadata.json + (future) cost-tracker "
            "joins. Default: phase1_l58_replay."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print plan + counts and exit; no API calls, no writes.",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser


def _print_dry_run(
    args: argparse.Namespace,
    candidates: Sequence[HistoricalCandidate],
    evaluator_a: ReplayEvaluator,
    evaluator_b: ReplayEvaluator,
) -> None:
    print("=== F3 Replay DRY-RUN PLAN ===")
    print(f"harness:        {HARNESS_VERSION}")
    print(f"evaluator_a:    {evaluator_a.evaluator_id}")
    print(f"evaluator_b:    {evaluator_b.evaluator_id}")
    print(f"eval_dir:       {args.eval_dir}")
    print(f"realized_r_join: {args.realized_r_join}")
    print(f"since:          {args.since}")
    print(f"until:          {args.until}")
    print(f"instruments:    {args.instruments}")
    print(f"output:         {args.output}")
    print(f"run_tag:        {args.run_tag}")
    print(f"n_candidates:   {len(candidates)}")
    n_with_r = sum(1 for c in candidates if c.realized_r is not None)
    print(f"n_with_realized_r: {n_with_r}")
    if candidates:
        first = candidates[0]
        last = candidates[-1]
        print(
            f"first:          {first.cand_id} ({first.framework_used or '-'})"
        )
        print(
            f"last:           {last.cand_id} ({last.framework_used or '-'})"
        )
    print("(skipping evaluator + write — dry-run)")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    # 1. Resolve evaluators (fail-fast on bad names)
    try:
        evaluator_a = resolve_evaluator(args.evaluator_a)
        evaluator_b = resolve_evaluator(args.evaluator_b)
    except (ValueError, RuntimeError) as exc:
        logger.error("%s", exc)
        return 2

    # 2. Parse filters
    try:
        since = _parse_date(args.since)
        until = _parse_date(args.until)
    except argparse.ArgumentTypeError as exc:
        logger.error("%s", exc)
        return 2
    instruments = _parse_instruments(args.instruments)

    # 3. Load candidates
    eval_dir = Path(args.eval_dir)
    trade_records_dir: Optional[Path] = (
        Path(args.realized_r_join) if args.realized_r_join else None
    )
    candidates = load_historical_candidates(
        eval_dir=eval_dir,
        trade_records_dir=trade_records_dir,
        since=since,
        until=until,
        instruments=instruments,
    )

    # 4. Dry-run short-circuit
    if args.dry_run:
        _print_dry_run(args, candidates, evaluator_a, evaluator_b)
        return 0

    if not candidates:
        logger.error(
            "No candidates loaded — refusing to write empty run. "
            "Check --eval-dir / --since / --until / --instruments."
        )
        return 2

    # 5. Run
    output_dir = Path(args.output)
    run = ReplayRun(
        candidates=candidates,
        evaluator_a=evaluator_a,
        evaluator_b=evaluator_b,
        output_dir=output_dir,
        run_tag=args.run_tag,
    )
    metrics = run.run()
    logger.info(
        "F3 replay done: %d candidates, %d decision diffs, "
        "%d realized-R joined.",
        metrics.n_candidates,
        metrics.n_decision_diff,
        metrics.n_with_realized_r,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
