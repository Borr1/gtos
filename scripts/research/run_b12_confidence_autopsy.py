"""B12 — Confidence Scorer Deep Autopsy CLI runner.

Loads CANDIDATE rows from every available source that carries BOTH a
realized R AND an AI-emitted ``confidence_score``, stratifies them, runs
permutation Spearman tests, applies Bonferroni correction, and writes::

    research/ai_behavior/B12_confidence/autopsy.json
    research/ai_behavior/B12_confidence/report.md

Usage
-----

    python scripts/research/run_b12_confidence_autopsy.py \\
        --output-dir research/ai_behavior/B12_confidence

    # Tighter min-n
    python scripts/research/run_b12_confidence_autopsy.py \\
        --output-dir <dir> --min-n 30

    # Custom strata cross
    python scripts/research/run_b12_confidence_autopsy.py \\
        --output-dir <dir> --strata-axes symbol,setup_grade,kill_zone

Trade data sources
------------------
1. **Research backtest slices** — ``research/**/all_results.json``.
   Confidence is parsed out of the ``raw_response`` JSON blob; realized
   R sits on the row as ``r_multiple`` for filled trades.
2. **Backtest sessions** —
   ``knowledge_base_backtest/sessions/*.json``. The XAUUSD-only batch
   simulator emits per-candle ``confidence`` directly + a per-session
   ``trade_summary.r_multiple``. We fold the trade outcome onto the
   triggering CANDIDATE row.

Out-of-scope
============
* No live trade records (``knowledge_base/index/_trade_index.json``)
  because that index does NOT carry the AI-emitted ``confidence`` —
  the live agent stores confidence in per-candidate JSONs not the
  rolled-up index. Including the index would silently drop confidence
  to None for all live trades and fabricate an empty axis. The B12
  brief assumes shadow-mode-style data; live confidence enrichment is
  a downstream task (memory ``project_trade_records_enrichment_gap``).
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Locate project root by walking up until pyproject.toml so the src/ import works.
_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent
while _PROJECT_ROOT != _PROJECT_ROOT.parent:
    if (_PROJECT_ROOT / "pyproject.toml").exists():
        break
    _PROJECT_ROOT = _PROJECT_ROOT.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.research_infra.confidence_autopsy import (  # noqa: E402
    DEFAULT_STRATA_AXES,
    VALID_STRATA_AXES,
    AutopsyReport,
    StratumResult,
    stratify_and_test,
)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers — confidence + framework + setup_grade extraction from raw_response
# ---------------------------------------------------------------------------


_CONF_RE = re.compile(r'"confidence_score"\s*:\s*([0-9.]+)')
_FW_RE = re.compile(r'"framework"\s*:\s*"([^"]+)"')
_GRADE_RE = re.compile(r'"setup_grade"\s*:\s*"([^"]+)"')
_DIRECTION_RE = re.compile(r'"direction"\s*:\s*"([^"]+)"')


def _extract_from_raw(raw: Any) -> dict[str, Any]:
    """Pull confidence + framework + setup_grade out of the raw_response blob.

    The AI emits its trade plan as JSON inside a fenced ```json``` block.
    We use focused regexes rather than parsing the JSON because the
    fence sometimes carries trailing junk and partial responses.
    Returns ``{}`` if ``raw`` is non-string.
    """
    if not isinstance(raw, str):
        return {}
    out: dict[str, Any] = {}
    if (m := _CONF_RE.search(raw)):
        try:
            out["confidence"] = float(m.group(1))
        except ValueError:
            pass
    if (m := _FW_RE.search(raw)):
        out["framework"] = m.group(1)
    if (m := _GRADE_RE.search(raw)):
        out["setup_grade"] = m.group(1)
    if (m := _DIRECTION_RE.search(raw)):
        out["direction_raw"] = m.group(1)
    return out


def _hour_of_day(candle_time: Any) -> Optional[int]:
    """Parse the UTC hour from an ISO-8601 ``candle_time``."""
    if not isinstance(candle_time, str):
        return None
    s = candle_time.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).hour


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def _load_research_slices(project_root: Path) -> list[dict[str, Any]]:
    """Pull CANDIDATE rows from research/**/all_results.json.

    A row qualifies when:
      - decision == "CANDIDATE"
      - outcome is filled (WIN/LOSS/BE/PARTIAL) AND r_multiple is numeric
      - raw_response carries a parseable confidence_score

    The framework + setup_grade come from raw_response when available;
    setup_grade also exists as a top-level field in some slices and we
    prefer that when both are present.
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
        results = doc.get("results", []) if isinstance(doc, dict) else []
        for row in results:
            if not isinstance(row, dict):
                continue
            if row.get("decision") != "CANDIDATE":
                continue
            outcome = row.get("outcome")
            if outcome not in ("WIN", "LOSS", "BE", "PARTIAL"):
                continue
            r = row.get("r_multiple")
            if r is None:
                continue
            try:
                r_val = float(r)
            except (TypeError, ValueError):
                continue
            extracted = _extract_from_raw(row.get("raw_response"))
            if "confidence" not in extracted:
                # No confidence in raw_response — skip; we cannot stratify
                # what we cannot measure.
                continue
            ts = row.get("candle_time")
            sym = row.get("symbol")
            if not (ts and sym):
                continue
            framework = extracted.get("framework") or row.get("framework")
            setup_grade = row.get("setup_grade") or extracted.get("setup_grade")
            direction = row.get("direction") or extracted.get("direction_raw")
            kill_zone = row.get("kill_zone")
            out.append(
                {
                    "symbol": sym,
                    "candle_time": ts,
                    "kill_zone": kill_zone,
                    "regime": None,  # Not directly available in this source.
                    "framework": framework,
                    "setup_grade": setup_grade,
                    "direction": direction,
                    "hour_of_day": _hour_of_day(ts),
                    "confidence": extracted["confidence"],
                    "r_multiple": r_val,
                    "outcome": outcome,
                    "source": f"research:{Path(path).relative_to(project_root)}",
                }
            )
    return out


def _load_backtest_sessions(project_root: Path) -> list[dict[str, Any]]:
    """Pull XAUUSD CANDIDATEs from knowledge_base_backtest/sessions/*.json.

    Each session is one calendar day, XAUUSD only. The schema:

        candle_evaluations: [{candle_time, decision, confidence, setup_grade, ...}]
        trade_summary:       {trade_taken, outcome, r_multiple, trade_id}

    We attribute the trade_summary's outcome to the FIRST CANDIDATE in
    candle_evaluations (the session simulator only takes one trade per
    day). Subsequent CANDIDATEs are skipped with a debug log because we
    cannot match them to a realized R.
    """
    out: list[dict[str, Any]] = []
    pattern = str(project_root / "knowledge_base_backtest" / "sessions" / "*.json")
    for path in sorted(glob.iglob(pattern)):
        try:
            with open(path, "r", encoding="utf-8") as f:
                doc = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("could not read %s: %s", path, e)
            continue
        if not isinstance(doc, dict):
            continue
        cands = doc.get("candle_evaluations", [])
        if not isinstance(cands, list):
            continue
        ts_summary = doc.get("trade_summary") or {}
        outcome = ts_summary.get("outcome")
        r = ts_summary.get("r_multiple")
        if outcome not in ("WIN", "LOSS", "BE", "PARTIAL"):
            continue
        if r is None:
            continue
        try:
            r_val = float(r)
        except (TypeError, ValueError):
            continue
        # Find the first CANDIDATE in the evaluations.
        first_cand = None
        for ce in cands:
            if isinstance(ce, dict) and ce.get("decision") == "CANDIDATE":
                first_cand = ce
                break
        if first_cand is None:
            continue
        conf = first_cand.get("confidence")
        if conf is None:
            continue
        try:
            conf_val = float(conf)
        except (TypeError, ValueError):
            continue
        ts = first_cand.get("candle_time")
        if not isinstance(ts, str):
            continue
        out.append(
            {
                "symbol": "XAUUSD",
                "candle_time": ts,
                "kill_zone": None,  # Not stored at row level.
                "regime": None,
                "framework": first_cand.get("framework"),
                "setup_grade": first_cand.get("setup_grade"),
                "direction": None,
                "hour_of_day": _hour_of_day(ts),
                "confidence": conf_val,
                "r_multiple": r_val,
                "outcome": outcome,
                "source": f"backtest_session:{Path(path).relative_to(project_root)}",
            }
        )
    return out


def _dedupe(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop duplicates by (symbol, candle_time, r_multiple, confidence).

    Mirror approach to A3's loader — collisions across sources usually
    mean the same trade routed twice (e.g. backtest session + research
    slice rerun on the same date).
    """
    seen: set[tuple[str, str, float, float]] = set()
    out: list[dict[str, Any]] = []
    for t in trades:
        key = (
            str(t.get("symbol")),
            str(t.get("candle_time")),
            round(float(t["r_multiple"]), 6),
            round(float(t["confidence"]), 6),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------


def _fmt_stratum(s: StratumResult) -> str:
    parts = []
    for axis, value in s.stratum:
        parts.append(f"{axis}={value}")
    return " | ".join(parts) or "(empty)"


def render_report_md(report: AutopsyReport, *, n_trades_loaded: int) -> str:
    lines: list[str] = []
    lines.append("# B12 — Confidence Scorer Deep Autopsy")
    lines.append("")
    lines.append(
        f"_Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}_"
    )
    lines.append("")

    d = report.distribution
    n = d.get("n", 0)
    lines.append("## Confidence distribution")
    lines.append("")
    if n == 0:
        lines.append(
            "_No trades found that carry BOTH an AI confidence score AND "
            "a realized R-multiple. Confirm at least one of "
            "research/**/all_results.json or knowledge_base_backtest/sessions/*.json "
            "exists with filled CANDIDATE rows._"
        )
    else:
        mean = d.get("mean")
        mode = d.get("mode")
        mode_frac = d.get("mode_fraction")
        at_80 = d.get("fraction_at_80")
        lines.append(f"- n trades evaluated: {n}")
        lines.append(f"- Trades scanned (loader): {n_trades_loaded}")
        if mean is not None:
            lines.append(f"- Mean: {mean:.2f}")
        if mode is not None and mode_frac is not None:
            lines.append(
                f"- Mode: {mode} (frequency {mode_frac * 100:.1f}%)"
            )
        if at_80 is not None:
            lines.append(f"- At confidence=80: {at_80 * 100:.1f}%")
        # Histogram
        hist = d.get("histogram") or {}
        if hist:
            lines.append("")
            lines.append("### Histogram")
            lines.append("")
            lines.append("| Confidence | Count |")
            lines.append("| --- | --- |")
            for k in sorted(hist.keys()):
                lines.append(f"| {k} | {hist[k]} |")
    lines.append("")

    # Predictive table
    lines.append(
        f"## Predictive conditionals "
        f"(|rho| >= {report.rho_threshold:.2f} AND p_corrected < {report.alpha:.2f} "
        f"AND n >= {report.min_n})"
    )
    lines.append("")
    if report.predictive:
        lines.append("| Stratum | n | rho | raw p | corrected p |")
        lines.append("| --- | --- | --- | --- | --- |")
        for s in report.predictive:
            rho_s = f"{s.rho:+.3f}" if s.rho is not None else "n/a"
            raw_s = f"{s.raw_p:.4f}" if s.raw_p is not None else "n/a"
            corr_s = f"{s.corrected_p:.4f}" if s.corrected_p is not None else "n/a"
            lines.append(
                f"| {_fmt_stratum(s)} | {s.n} | {rho_s} | {raw_s} | {corr_s} |"
            )
    else:
        lines.append("_No stratum met all three thresholds._")
    lines.append("")

    # Family / methodology
    lines.append("## Family + methodology")
    lines.append("")
    lines.append(f"- Stratification axes: {', '.join(report.strata_axes)}")
    lines.append(
        f"- Strata tested (Bonferroni family): {report.family_size}"
    )
    lines.append(f"- Total strata observed: {len(report.all_results)}")
    lines.append(f"- min_n = {report.min_n}")
    lines.append(f"- alpha (after Bonferroni) = {report.alpha}")
    lines.append(f"- |rho| threshold = {report.rho_threshold}")
    lines.append(
        f"- Permutation count = {report.n_perms} (seed={report.seed})"
    )
    lines.append("")

    # Strategic verdict
    lines.append("## Strategic verdict")
    lines.append("")
    n_predictive = len(report.predictive)
    lines.append(f"Predictive conditionals found: {n_predictive}")
    if n_predictive > 0:
        top = report.predictive[0]
        lines.append(f"Most predictive: {_fmt_stratum(top)} (rho={top.rho:+.3f})")
        lines.append("")
        lines.append(
            "Reasoning: at least one stratum survived Bonferroni-corrected "
            "permutation testing with the configured |rho| threshold. The CEO "
            "should evaluate whether *conditional* re-deployment of "
            "`confidence_filter_mode` (e.g. confidence-weighted sizing within "
            "the predictive stratum, scorer ignored elsewhere) is justified by "
            "this evidence size, or whether the stratum is an artifact of "
            "data slicing. Note: the A3 / decay program demonstrated that "
            "walk-level signals do not always survive realized-R replay; this "
            "scorer test IS already realized-R-based, but the corrected p "
            "still relies on a finite permutation null and the rho threshold "
            "is a judgment call."
        )
    else:
        lines.append("Most predictive: n/a")
        lines.append("")
        lines.append(
            "Reasoning: zero strata cleared the predictive bar after "
            "Bonferroni correction across the tested family. This corroborates "
            "the headline CLAUDE.md finding that the AI's `confidence_score` "
            "is a rubber stamp — its variance across strata is too small to "
            "discriminate winners from losers. `confidence_filter_mode: shadow` "
            "should remain in shadow, and any future hard filter on the "
            "scorer requires a fresh data collection (not a re-stratification "
            "of the same trades). K54 feature engineering should treat "
            "confidence_score as a noise feature."
        )
    lines.append("")

    # Per-stratum dump (compact) for auditability — n>=min_n strata only.
    lines.append("## All tested strata")
    lines.append("")
    tested = [r for r in report.all_results if r.flag in ("PREDICTIVE", "NOT_PREDICTIVE")]
    if not tested:
        lines.append("_No strata had n >= min_n; nothing was tested._")
    else:
        lines.append("| Stratum | n | rho | raw p | corrected p | flag |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        # Sort by n desc, then |rho| desc
        for s in sorted(
            tested,
            key=lambda r: (-r.n, -abs(r.rho or 0.0)),
        ):
            rho_s = f"{s.rho:+.3f}" if s.rho is not None else "n/a"
            raw_s = f"{s.raw_p:.4f}" if s.raw_p is not None else "n/a"
            corr_s = f"{s.corrected_p:.4f}" if s.corrected_p is not None else "n/a"
            lines.append(
                f"| {_fmt_stratum(s)} | {s.n} | {rho_s} | {raw_s} | {corr_s} | {s.flag} |"
            )
    lines.append("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _parse_axes(s: str) -> list[str]:
    parts = [a.strip() for a in s.split(",") if a.strip()]
    invalid = [p for p in parts if p not in VALID_STRATA_AXES]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"unknown axes {invalid!r}; valid: {sorted(VALID_STRATA_AXES)}"
        )
    return parts


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument(
        "--output-dir",
        type=Path,
        default=Path("research/ai_behavior/B12_confidence"),
        help="Output dir for autopsy.json + report.md",
    )
    p.add_argument(
        "--min-n",
        type=int,
        default=20,
        help="Minimum sample size for a stratum to be tested (default 20)",
    )
    p.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance threshold AFTER Bonferroni correction (default 0.05)",
    )
    p.add_argument(
        "--rho-threshold",
        type=float,
        default=0.2,
        help="Minimum |Spearman rho| for predictive flag (default 0.2)",
    )
    p.add_argument(
        "--n-perms",
        type=int,
        default=1000,
        help="Permutation count for empirical p-value (default 1000)",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=1,
        help="RNG seed for permutation reproducibility (default 1)",
    )
    p.add_argument(
        "--strata-axes",
        type=_parse_axes,
        default=None,
        help=(
            "Comma-separated stratification axes. Default: "
            f"{','.join(DEFAULT_STRATA_AXES)}. Valid: "
            f"{','.join(sorted(VALID_STRATA_AXES))}"
        ),
    )
    p.add_argument(
        "--no-research-slices",
        action="store_true",
        help="Skip research/**/all_results.json (debug)",
    )
    p.add_argument(
        "--no-backtest-sessions",
        action="store_true",
        help="Skip knowledge_base_backtest/sessions/*.json (debug)",
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

    # 1. Load.
    trades: list[dict[str, Any]] = []
    if not args.no_research_slices:
        sl = _load_research_slices(project_root)
        logger.info("loaded %d research-slice trades", len(sl))
        trades.extend(sl)
    if not args.no_backtest_sessions:
        bt = _load_backtest_sessions(project_root)
        logger.info("loaded %d backtest-session trades", len(bt))
        trades.extend(bt)

    n_loaded = len(trades)
    trades = _dedupe(trades)
    logger.info("after dedupe: %d trades", len(trades))

    # 2. Stratify + test.
    report = stratify_and_test(
        trades,
        strata_axes=args.strata_axes,
        min_n=args.min_n,
        alpha=args.alpha,
        rho_threshold=args.rho_threshold,
        n_perms=args.n_perms,
        seed=args.seed,
    )

    # 3. Write outputs.
    autopsy_path = output_dir / "autopsy.json"
    report_path = output_dir / "report.md"

    with autopsy_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "n_trades_loaded": n_loaded,
                "n_trades_after_dedupe": len(trades),
                **report.to_dict(),
                "generated_at": datetime.now(timezone.utc).isoformat(
                    timespec="seconds"
                ),
            },
            f,
            indent=2,
            sort_keys=True,
            default=str,
        )

    report_md = render_report_md(report, n_trades_loaded=n_loaded)
    report_path.write_text(report_md, encoding="utf-8")

    logger.info(
        "wrote %s + %s | strata_tested=%d predictive=%d",
        autopsy_path,
        report_path,
        report.family_size,
        len(report.predictive),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
