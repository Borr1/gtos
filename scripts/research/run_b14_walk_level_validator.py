"""B14 — Walk-Level vs Realized-R Systematic Study CLI runner.

Loads filled CANDIDATE outcomes (with their walk-level signals) from the
research data sources and writes ``evaluation.json`` + ``report.md`` into the
output directory.

Trade data sources (in priority order)
--------------------------------------
1. **Phase 1 full extraction merged data** —
   ``research/phase1_full_extraction/merged_data.jsonl`` is the canonical
   walk-level + outcome join produced by the A1 backtest pipeline. It
   carries every walk-level signal in MSO ``raw_data`` along with
   ``out_outcome`` and ``out_r_multiple`` for filled CANDIDATEs. This is
   the **primary** source.

2. **Research backtest slice all_results.json** —
   ``research/**/all_results.json`` rows that carry ``r_multiple``. Used
   as a secondary source. Walk-level signals on these rows are sparser
   than merged_data but framework / regime / session is usable.

3. **Live trade records + index** —
   ``knowledge_base/index/_trade_index.json`` cross-referenced with
   per-trade walk-level snapshots in ``knowledge_base/live_evaluations/``.
   When the per-trade snapshot is unavailable, only categorical signals
   (framework, kill_zone, setup_grade) are usable.

Usage
-----

    python scripts/research/run_b14_walk_level_validator.py \\
        --output-dir research/ai_behavior/B14_walk_level

    # Restrict to specific signals (e.g. for a follow-up sweep)
    python scripts/research/run_b14_walk_level_validator.py \\
        --output-dir <dir> --signals touch_count,ob_retest_distance_atr

    # Tighter min stratum n (research stress test)
    python scripts/research/run_b14_walk_level_validator.py \\
        --output-dir <dir> --min-stratum-n 15

Outputs
-------
``evaluation.json``  — full ValidatorReport.to_dict() for downstream
``report.md``        — markdown table with per-signal status + verdict block
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

# Allow running from anywhere — locate project root by walking up until we
# see ``pyproject.toml`` so the ``src/`` import works without PYTHONPATH.
_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent
while _PROJECT_ROOT != _PROJECT_ROOT.parent:
    if (_PROJECT_ROOT / "pyproject.toml").exists():
        break
    _PROJECT_ROOT = _PROJECT_ROOT.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.research_infra.walk_level_validator import (  # noqa: E402
    SIGNAL_REGISTRY,
    SignalReport,
    ValidatorReport,
    evaluate_signals,
)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Trade loaders
# ---------------------------------------------------------------------------


def _load_phase1_merged(project_root: Path) -> list[dict[str, Any]]:
    """Read ``research/phase1_full_extraction/merged_data.jsonl``.

    Filters to filled CANDIDATEs (``out_outcome`` in WIN/LOSS/BE) and
    normalizes the field names so the registry can find them.
    """
    path = project_root / "research" / "phase1_full_extraction" / "merged_data.jsonl"
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning("merged_data line %d: malformed JSON: %s", line_no, e)
                    continue
                if row.get("out_outcome") not in ("WIN", "LOSS", "BE"):
                    continue
                r = row.get("out_r_multiple")
                try:
                    r_val = float(r)
                except (TypeError, ValueError):
                    continue
                # Build a normalized trade dict: keep the original fields
                # AND surface canonical aliases the registry looks at.
                t = dict(row)
                t["r_multiple"] = r_val
                # direction normalization: phase1 uses out_direction; the
                # registry uses 'direction' as the primary key with
                # ai_direction_evaluated as a secondary.
                if "direction" not in t:
                    t["direction"] = row.get("out_direction") or row.get(
                        "ai_direction_evaluated"
                    )
                if not t.get("framework"):
                    t["framework"] = row.get("logger_framework") or row.get(
                        "framework_id"
                    )
                if not t.get("session"):
                    t["session"] = row.get("kill_zone")
                if not t.get("setup_grade"):
                    t["setup_grade"] = row.get("logger_setup_grade") or row.get(
                        "out_setup_grade"
                    )
                # regime tag: A1 merged data carries detector_version /
                # mso_h1_structure_direction but no canonical regime label.
                # The structure_direction is a usable proxy.
                if not t.get("regime"):
                    sd = row.get("mso_h1_structure_direction")
                    if isinstance(sd, str):
                        t["regime"] = sd
                t["_source"] = "phase1_merged"
                out.append(t)
    except OSError as e:
        logger.warning("could not read %s: %s", path, e)
    return out


def _load_research_slices(project_root: Path) -> list[dict[str, Any]]:
    """Pull every ``all_results.json`` row that carries an ``r_multiple``.

    Walk-level signal coverage on these rows is sparse — they typically
    only have framework + symbol + decision + r_multiple. Useful for
    framework_id + session + setup_grade signals; not useful for
    structural (touch_count, distance, FVG overlap) signals.
    """
    out: list[dict[str, Any]] = []
    pattern = str(project_root / "research" / "**" / "all_results.json")
    for path in glob.iglob(pattern, recursive=True):
        try:
            with open(path, "r", encoding="utf-8") as f:
                doc = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("could not read %s: %s", path, e)
            continue
        results = doc.get("results", [])
        if not isinstance(results, list):
            continue
        for row in results:
            if not isinstance(row, dict):
                continue
            r = row.get("r_multiple")
            if r is None:
                continue
            try:
                r_val = float(r)
            except (TypeError, ValueError):
                continue
            outcome = row.get("outcome")
            if outcome not in ("WIN", "LOSS", "BE"):
                # Some slice writers omit outcome; r_multiple suffices.
                pass
            t = dict(row)
            t["r_multiple"] = r_val
            t["_source"] = f"research_slice:{Path(path).relative_to(project_root)}"
            out.append(t)
    return out


def _load_trade_index(project_root: Path) -> list[dict[str, Any]]:
    """Read ``knowledge_base/index/_trade_index.json``.

    The index carries date / kill_zone / framework / r_multiple but no
    structural walk-level signals. So this source is only useful for
    framework_id / session_id / setup_grade signals. We still pull it
    in to give Bonferroni a larger fleet n.
    """
    out: list[dict[str, Any]] = []
    path = project_root / "knowledge_base" / "index" / "_trade_index.json"
    if not path.exists():
        return out
    try:
        with path.open("r", encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("could not read %s: %s", path, e)
        return out
    trades = doc.get("trades", [])
    if not isinstance(trades, list):
        return out
    for t in trades:
        if not isinstance(t, dict):
            continue
        r = t.get("r_multiple")
        if r is None:
            continue
        try:
            r_val = float(r)
        except (TypeError, ValueError):
            continue
        out.append(
            {
                "r_multiple": r_val,
                "symbol": t.get("symbol"),
                "direction": t.get("direction"),
                "framework": t.get("framework"),
                "session": t.get("kill_zone"),
                "setup_grade": t.get("grade"),
                "_source": "trade_index",
            }
        )
    return out


def _dedupe(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop duplicates by (symbol, candle_close_time, r_multiple).

    Research slices often re-export rows from batch sessions. The triple
    is unique per scenario so collisions are the same trade routed via
    two paths.
    """
    seen: set[tuple[str, str, float]] = set()
    out: list[dict[str, Any]] = []
    for t in trades:
        try:
            r = float(t.get("r_multiple"))
        except (TypeError, ValueError):
            continue
        ts = (
            t.get("candle_close_time")
            or t.get("timestamp_utc")
            or t.get("candle_time")
            or t.get("ts")
            or ""
        )
        key = (str(t.get("symbol")), str(ts), round(r, 6))
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------


def render_report_md(report: ValidatorReport) -> str:
    """Build a markdown report from the ValidatorReport."""
    lines: list[str] = []
    lines.append("# B14 — Walk-Level vs Realized-R Systematic Study")
    lines.append("")
    lines.append(f"_Generated: {report.generated_at}_")
    lines.append("")
    lines.append(
        f"**n_trades_total = {report.n_trades_total}** | "
        f"**family_size = {report.family_size}** "
        "(tested signals — Bonferroni denominator)"
    )
    lines.append("")
    lines.append(
        "Memory `feedback_walk_level_evidence_not_predictive` recorded that "
        "walk-level statistical evidence does NOT translate into realized-R "
        "differences. B14 stress-tests the inverse: across the full family of "
        "walk-level signals, is there ANY where the walk-level partition "
        "ALSO partitions realized R AND the direction matches?"
    )
    lines.append("")

    # Walk-level signal evaluation table
    lines.append("## Walk-level signal evaluation")
    lines.append("")
    lines.append(
        "| Signal | strata | min n | KW p (raw) | KW p (Bonferroni) | "
        "direction-consistent | status |"
    )
    lines.append(
        "| --- | --- | --- | --- | --- | --- | --- |"
    )
    for sig in report.signals:
        if sig.kw_p_raw is None:
            p_raw_s = "n/a"
            p_bonf_s = "n/a"
        else:
            p_raw_s = f"{sig.kw_p_raw:.4g}"
            p_bonf_s = f"{sig.kw_p_bonferroni:.4g}"
        if sig.direction_consistent is True:
            dc_s = "yes"
        elif sig.direction_consistent is False:
            dc_s = "**no**"
        else:
            dc_s = "n/a"
        lines.append(
            f"| `{sig.signal}` | {sig.n_strata_tested} | {sig.min_stratum_n} | "
            f"{p_raw_s} | {p_bonf_s} | {dc_s} | {sig.status} |"
        )
    lines.append("")

    # Strategic verdict
    lines.append("## Strategic verdict")
    lines.append("")
    n_survivors = len(report.survivors)
    n_total = len(report.signals)
    lines.append(f"Survivor signals: **{n_survivors} / {n_total}**")
    lines.append("")
    if report.survivors:
        most_pred = sorted(
            report.survivors,
            key=lambda s: (s.kw_p_bonferroni or 1.0),
        )[0]
        lines.append(f"Most-predictive (smallest p): `{most_pred.signal}` "
                     f"(KW p_bonferroni = {most_pred.kw_p_bonferroni:.4g})")
        lines.append("")
        lines.append(
            "Reasoning: ≥1 walk-level signal SURVIVED the realized-R cross-check "
            "(KW p_bonferroni < 0.05 AND direction-consistent with the a-priori "
            "walk-level ranking). Memory `feedback_walk_level_evidence_not_predictive` "
            "should be REFINED — at least the surviving signal is a candidate to "
            "feed K54 (ML classifier training pipeline) as a high-priority feature. "
            "The surviving signal's stratum table below shows where the realized "
            "edge concentrates."
        )
    else:
        # Find the smallest p that we did test, even if non-survivor.
        tested = [s for s in report.signals if s.kw_p_bonferroni is not None]
        smallest = (
            sorted(tested, key=lambda s: s.kw_p_bonferroni)[0] if tested else None
        )
        most_pred_str = (
            f"`{smallest.signal}` (KW p_bonferroni = {smallest.kw_p_bonferroni:.4g}, "
            f"direction-consistent = "
            f"{ {True: 'yes', False: 'no', None: 'n/a'}[smallest.direction_consistent] })"
            if smallest
            else "none (no signal had >=2 strata with n>=min)"
        )
        lines.append(f"Most-predictive (smallest p): {most_pred_str}")
        lines.append("")
        lines.append(
            "Reasoning: NO walk-level signal in this family survived the "
            "realized-R cross-check (KW p_bonferroni < 0.05 AND "
            "direction-consistent). Memory `feedback_walk_level_evidence_not_predictive` "
            "is REINFORCED — walk-level evidence remains a misleading prior for "
            "realized R. K54 (ML classifier training pipeline) should NOT use "
            "these walk-level signals as direct features without first "
            "validating on out-of-sample realized R."
        )
    lines.append("")

    # Per-signal stratum tables (only for tested signals; INSUFFICIENT_N
    # signals get a one-liner so the report stays readable).
    lines.append("## Per-signal stratum detail")
    lines.append("")
    for sig in report.signals:
        rows = report.strata_by_signal.get(sig.signal, [])
        lines.append(f"### `{sig.signal}` — {sig.status}")
        lines.append("")
        if not rows:
            lines.append(f"_{sig.notes or 'no strata observed'}_")
            lines.append("")
            continue
        if sig.notes:
            lines.append(f"_{sig.notes}_")
            lines.append("")
        if sig.walk_ranking:
            lines.append(
                "Walk-level ranking (best→worst): "
                + " → ".join(f"`{s}`" for s in sig.walk_ranking)
            )
        if sig.realized_ranking:
            lines.append(
                "Realized-R ranking (best→worst): "
                + " → ".join(f"`{s}`" for s in sig.realized_ranking)
            )
        lines.append("")
        lines.append("| Stratum | n | mean R | median R | WR | WR 95% CI | total R | rank (walk) | rank (real) |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for r in rows:
            walk_rank_s = str(r.rank_walk) if r.rank_walk is not None else "—"
            ci_s = f"[{r.wr_lo:.2f}, {r.wr_hi:.2f}]"
            lines.append(
                f"| `{r.stratum}` | {r.n} | {r.mean_r:+.3f} | {r.median_r:+.3f} | "
                f"{r.wr:.1%} | {ci_s} | {r.total_r:+.2f} | {walk_rank_s} | "
                f"{r.rank_realized} |"
            )
        lines.append("")

    # K54 handoff section
    lines.append("## K54 handoff")
    lines.append("")
    if report.survivors:
        lines.append(
            "Per the research program kickoff, K54 (ML classifier training) takes "
            "Phase 1 feature outputs as inputs. The walk-level survivors below "
            "are HIGH-PRIORITY features for the K54 training set:"
        )
        lines.append("")
        for s in report.survivors:
            lines.append(
                f"- `{s.signal}` — KW p_bonferroni = {s.kw_p_bonferroni:.4g}; "
                f"realized ranking matches walk ranking "
                f"({' → '.join(s.realized_ranking)})"
            )
    else:
        lines.append(
            "No survivors. K54 should NOT add these walk-level signals as direct "
            "features without first validating against out-of-sample realized R "
            "(per memory `feedback_walk_level_evidence_not_predictive`)."
        )
    lines.append("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument(
        "--output-dir",
        type=Path,
        default=Path("research/ai_behavior/B14_walk_level"),
        help="Directory to write evaluation.json + report.md",
    )
    p.add_argument(
        "--signals",
        type=str,
        default=None,
        help=(
            "Comma-separated subset of signals to evaluate (default: all in "
            "SIGNAL_REGISTRY). Useful for follow-up sweeps."
        ),
    )
    p.add_argument(
        "--min-stratum-n",
        type=int,
        default=10,
        help="Minimum n per stratum for KW testing (default 10)",
    )
    p.add_argument(
        "--p-threshold",
        type=float,
        default=0.05,
        help="Significance threshold for SURVIVOR status (default 0.05)",
    )
    p.add_argument(
        "--symbols",
        type=str,
        default=None,
        help=(
            "Optional symbol filter (comma-separated). When set, restricts "
            "the evaluation to trades whose symbol matches."
        ),
    )
    p.add_argument(
        "--no-research-slices",
        action="store_true",
        help="Skip research/**/all_results.json (debug)",
    )
    p.add_argument(
        "--no-trade-index",
        action="store_true",
        help="Skip knowledge_base/index/_trade_index.json (debug)",
    )
    p.add_argument(
        "--no-phase1-merged",
        action="store_true",
        help="Skip research/phase1_full_extraction/merged_data.jsonl (debug)",
    )
    p.add_argument(
        "--project-root",
        type=Path,
        default=_PROJECT_ROOT,
        help="Project root (auto-detected; override for tests)",
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    args = _parse_args(argv)
    project_root: Path = args.project_root.resolve()
    output_dir: Path = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load trades.
    all_trades: list[dict[str, Any]] = []
    if not args.no_phase1_merged:
        merged = _load_phase1_merged(project_root)
        logger.info("loaded %d trades from phase1_merged", len(merged))
        all_trades.extend(merged)
    if not args.no_research_slices:
        slice_trades = _load_research_slices(project_root)
        logger.info("loaded %d trades from research slices", len(slice_trades))
        all_trades.extend(slice_trades)
    if not args.no_trade_index:
        idx_trades = _load_trade_index(project_root)
        logger.info("loaded %d trades from trade index", len(idx_trades))
        all_trades.extend(idx_trades)

    all_trades = _dedupe(all_trades)
    logger.info("total trades after dedupe: %d", len(all_trades))

    # 2. Optional symbol filter.
    if args.symbols:
        wanted = {s.strip() for s in args.symbols.split(",") if s.strip()}
        all_trades = [t for t in all_trades if t.get("symbol") in wanted]
        logger.info("after symbol filter %s: %d trades", wanted, len(all_trades))

    # 3. Resolve signal list.
    if args.signals:
        signals = [s.strip() for s in args.signals.split(",") if s.strip()]
    else:
        signals = list(SIGNAL_REGISTRY.keys())

    # 4. Evaluate.
    report = evaluate_signals(
        all_trades,
        signals,
        min_stratum_n=args.min_stratum_n,
        p_threshold=args.p_threshold,
    )

    # 5. Write outputs.
    eval_path = output_dir / "evaluation.json"
    report_path = output_dir / "report.md"

    with eval_path.open("w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, sort_keys=True)
    report_path.write_text(render_report_md(report), encoding="utf-8")

    # 6. Stdout summary so the runner shows progress without scraping files.
    n_survivors = len(report.survivors)
    logger.info(
        "wrote %s + %s | n_trades=%d family_size=%d survivors=%d",
        eval_path,
        report_path,
        report.n_trades_total,
        report.family_size,
        n_survivors,
    )
    if n_survivors:
        for s in report.survivors:
            logger.info(
                "SURVIVOR: %s (p_bonf=%.4g)",
                s.signal,
                s.kw_p_bonferroni,
            )
    else:
        logger.info("No survivors — walk-level evidence policy reinforced.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
