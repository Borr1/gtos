#!/usr/bin/env python3
"""Aggregator for the weekly divergence classification digests.

Walks ``research/divergence_sampling/week_*.md``, parses each ``Sample N``
block's four checkbox options (matched by the "(check ONE)" list), and
reports progress toward the promotion gate:

    - Total classified (≥100 required)
    - Per-outcome breakdown: v1_correct / v2_correct / both_wrong / ambiguous
    - Per-instrument + per-timeframe tables
    - Overall v2-correct rate = v2_correct / (v2_correct + v1_correct + both_wrong)
    - Per-instrument v2-correct rate (for symmetry / outlier detection)
    - PROMOTION-READY verdict

Parsing contract
----------------
The sampler emits each sample as a self-contained block starting with
a level-2 heading::

    ## Sample N — SYMBOL TIMEFRAME YYYY-MM-DD HH:MM UTC

followed by metadata bullets, a window-context block, and the
classification section::

    **Classification** (check ONE):
    - [ ] v1 correct (bullish was right)
    - [ ] v2 correct (bearish was right)
    - [ ] both wrong (should have been transitional/ranging)
    - [ ] ambiguous (genuinely could go either way)

CEO flips ``[ ]`` to ``[x]`` on exactly one line. Zero or multiple
checks → the sample is skipped with a warning, so the CEO can see what
needs re-classifying.

Output
------
Markdown summary printed to stdout by default. Use ``--output FILE`` to
also write to a file (e.g., ``research/divergence_sampling/SUMMARY.md``).

Exit codes
----------
    0 — ran successfully (classifications may or may not meet gate)
    2 — internal error (e.g., digest directory missing)
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)

DIGEST_DIR: Path = _PROJECT_ROOT / "research" / "divergence_sampling"

# Promotion gate thresholds (from ADR-004 §7.3 + task brief).
PROMOTION_MIN_CLASSIFICATIONS: int = 100
PROMOTION_MIN_V2_CORRECT_RATE: float = 0.80
PROMOTION_MIN_PER_INSTRUMENT_RATE: float = 0.60

# Canonical category labels. Order matters for report tables.
CATEGORIES: list[str] = ["v1_correct", "v2_correct", "both_wrong", "ambiguous"]

# Heading regex: "## Sample 7 — XAUUSD H1 2026-04-24 14:15 UTC"
# Groups: idx, symbol, timeframe, rest-of-heading.
_HEADING_RE = re.compile(
    r"^##\s+Sample\s+(\d+)\s+[—\-]\s+(\S+)\s+(\S+)\s+(.*)$"
)

# Checkbox: "- [x] v1 correct ..." (case-insensitive).
_CHECKBOX_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s+(.*)$")

# Label → canonical category mapping (first few tokens of the box line).
_LABEL_MAP: dict[str, str] = {
    "v1 correct": "v1_correct",
    "v2 correct": "v2_correct",
    "both wrong": "both_wrong",
    "ambiguous": "ambiguous",
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Classification:
    symbol: str
    timeframe: str
    category: str  # one of CATEGORIES
    week: str
    sample_index: int


@dataclass
class ParseResult:
    classifications: list[Classification] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    total_samples: int = 0  # total Sample headings seen
    unclassified: int = 0  # zero boxes checked
    malformed: int = 0  # >= 2 boxes checked, or unknown category


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def _label_to_category(text: str) -> Optional[str]:
    """Match the opening tokens of a checkbox line against the canonical map.

    Tolerant to trailing parenthetical explanations (e.g., "v1 correct
    (bullish was right)"). Unknown label returns None.
    """
    lower = text.strip().lower()
    for prefix, cat in _LABEL_MAP.items():
        if lower.startswith(prefix):
            return cat
    return None


def parse_digest(path: Path) -> ParseResult:
    """Parse a single ``week_*.md`` digest.

    Algorithm: walk lines, track the current Sample block via the heading
    regex. Within a block, collect every ``- [x|X]`` checkbox line. At
    end of block (either next heading or EOF), decide:

      * 0 checks → unclassified
      * 1 check → classification recorded
      * >= 2 checks → malformed (warning, skipped)
      * unknown label → malformed (warning, skipped)
    """
    out = ParseResult()
    week_stem = path.stem  # e.g., "week_2026-17"
    week_label = week_stem[len("week_"):] if week_stem.startswith("week_") else week_stem

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        out.warnings.append(f"[{path.name}] read failure: {exc}")
        return out

    current_sample: Optional[dict] = None

    def _close(sample: dict) -> None:
        """Close the current block and update the parse result."""
        out.total_samples += 1
        checks: list[str] = sample["checked"]
        if len(checks) == 0:
            out.unclassified += 1
            return
        if len(checks) >= 2:
            out.warnings.append(
                f"[{week_label} Sample {sample['idx']}] {len(checks)} boxes "
                f"checked — skipped (must be exactly 1)"
            )
            out.malformed += 1
            return
        # Exactly one check.
        cat = _label_to_category(checks[0])
        if cat is None:
            out.warnings.append(
                f"[{week_label} Sample {sample['idx']}] unknown label "
                f"{checks[0]!r} — skipped"
            )
            out.malformed += 1
            return
        out.classifications.append(
            Classification(
                symbol=sample["symbol"],
                timeframe=sample["timeframe"],
                category=cat,
                week=week_label,
                sample_index=sample["idx"],
            )
        )

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            if current_sample is not None:
                _close(current_sample)
            current_sample = {
                "idx": int(m.group(1)),
                "symbol": m.group(2),
                "timeframe": m.group(3),
                "checked": [],
            }
            continue
        if current_sample is None:
            continue
        cb = _CHECKBOX_RE.match(line)
        if cb:
            mark, text = cb.group(1), cb.group(2)
            if mark.lower() == "x":
                current_sample["checked"].append(text)

    if current_sample is not None:
        _close(current_sample)

    return out


def parse_all(digest_dir: Path = None) -> ParseResult:
    """Walk every ``week_*.md`` under ``digest_dir`` and aggregate."""
    dd = Path(digest_dir) if digest_dir is not None else DIGEST_DIR
    combined = ParseResult()
    if not dd.exists():
        combined.warnings.append(f"digest dir does not exist: {dd}")
        return combined
    digests = sorted(dd.glob("week_*.md"))
    for p in digests:
        sub = parse_digest(p)
        combined.classifications.extend(sub.classifications)
        combined.warnings.extend(sub.warnings)
        combined.total_samples += sub.total_samples
        combined.unclassified += sub.unclassified
        combined.malformed += sub.malformed
    return combined


# ---------------------------------------------------------------------------
# Aggregations
# ---------------------------------------------------------------------------


def compute_overall_stats(classifications: list[Classification]) -> dict:
    """Overall counts + v2-correct rate (ambiguous excluded from denominator)."""
    counts = Counter(c.category for c in classifications)
    total = sum(counts.values())
    # Denominator excludes "ambiguous" (explicit "cannot decide" bucket).
    denom_cats = {"v1_correct", "v2_correct", "both_wrong"}
    denom = sum(counts.get(c, 0) for c in denom_cats)
    v2_correct = counts.get("v2_correct", 0)
    rate = v2_correct / denom if denom > 0 else 0.0
    return {
        "total": total,
        "counts": dict(counts),
        "rate_denom": denom,
        "v2_correct_rate": rate,
    }


def compute_per_instrument(classifications: list[Classification]) -> dict[str, dict]:
    """Per-instrument stats (same structure as ``compute_overall_stats``)."""
    by_sym: dict[str, list[Classification]] = defaultdict(list)
    for c in classifications:
        by_sym[c.symbol].append(c)
    return {sym: compute_overall_stats(v) for sym, v in by_sym.items()}


def compute_per_timeframe(classifications: list[Classification]) -> dict[str, dict]:
    """Per-timeframe stats."""
    by_tf: dict[str, list[Classification]] = defaultdict(list)
    for c in classifications:
        by_tf[c.timeframe].append(c)
    return {tf: compute_overall_stats(v) for tf, v in by_tf.items()}


def check_promotion_ready(
    overall: dict,
    per_instrument: dict[str, dict],
) -> tuple[bool, list[str]]:
    """Apply the three-gate promotion rule. Returns (ready, reasons_not_ready)."""
    reasons: list[str] = []
    total = overall.get("total", 0)
    if total < PROMOTION_MIN_CLASSIFICATIONS:
        reasons.append(
            f"total_classified {total} < {PROMOTION_MIN_CLASSIFICATIONS}"
        )
    rate = overall.get("v2_correct_rate", 0.0)
    if rate < PROMOTION_MIN_V2_CORRECT_RATE:
        reasons.append(
            f"overall_v2_correct_rate {rate*100:.1f}% < "
            f"{PROMOTION_MIN_V2_CORRECT_RATE*100:.0f}%"
        )
    # Per-instrument: every instrument with any decisive classifications
    # must clear the floor (excludes "ambiguous" from denominator).
    for sym, stats in sorted(per_instrument.items()):
        denom = stats.get("rate_denom", 0)
        if denom == 0:
            continue  # no decisive classifications yet
        sym_rate = stats.get("v2_correct_rate", 0.0)
        if sym_rate < PROMOTION_MIN_PER_INSTRUMENT_RATE:
            reasons.append(
                f"{sym} v2_correct_rate {sym_rate*100:.1f}% < "
                f"{PROMOTION_MIN_PER_INSTRUMENT_RATE*100:.0f}% (symmetry floor)"
            )
    return (len(reasons) == 0 and total >= PROMOTION_MIN_CLASSIFICATIONS), reasons


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _fmt_stats_line(name: str, stats: dict) -> str:
    """One-row table line for a group (sym/tf)."""
    total = stats["total"]
    counts = stats["counts"]
    denom = stats["rate_denom"]
    rate = stats["v2_correct_rate"] * 100
    v1 = counts.get("v1_correct", 0)
    v2 = counts.get("v2_correct", 0)
    both = counts.get("both_wrong", 0)
    amb = counts.get("ambiguous", 0)
    return (
        f"| {name} | {total} | {v2} | {v1} | {both} | {amb} | "
        f"{rate:.1f}% ({v2}/{denom}) |"
    )


def render_summary(result: ParseResult) -> str:
    """Produce the markdown summary string."""
    overall = compute_overall_stats(result.classifications)
    per_sym = compute_per_instrument(result.classifications)
    per_tf = compute_per_timeframe(result.classifications)
    ready, reasons = check_promotion_ready(overall, per_sym)

    lines: list[str] = []
    lines.append("# Divergence classification summary")
    lines.append("")
    lines.append(f"- **Total classified:** {overall['total']}")
    lines.append(f"- **Total samples seen:** {result.total_samples} "
                 f"(unclassified: {result.unclassified}, malformed: {result.malformed})")
    lines.append(
        f"- **Overall v2-correct rate:** {overall['v2_correct_rate']*100:.1f}% "
        f"({overall['counts'].get('v2_correct', 0)}/{overall['rate_denom']}, "
        "ambiguous excluded from denominator)"
    )
    lines.append("")
    lines.append("## Per-outcome")
    lines.append("")
    lines.append("| Outcome | Count |")
    lines.append("|---|---|")
    for cat in CATEGORIES:
        lines.append(f"| {cat} | {overall['counts'].get(cat, 0)} |")
    lines.append("")

    lines.append("## Per-instrument")
    lines.append("")
    lines.append("| Instrument | Total | v2_correct | v1_correct | both_wrong | ambiguous | v2-correct rate |")
    lines.append("|---|---|---|---|---|---|---|")
    for sym in sorted(per_sym.keys()):
        lines.append(_fmt_stats_line(sym, per_sym[sym]))
    lines.append("")

    lines.append("## Per-timeframe")
    lines.append("")
    lines.append("| Timeframe | Total | v2_correct | v1_correct | both_wrong | ambiguous | v2-correct rate |")
    lines.append("|---|---|---|---|---|---|---|")
    for tf in sorted(per_tf.keys()):
        lines.append(_fmt_stats_line(tf, per_tf[tf]))
    lines.append("")

    lines.append("## Promotion gate")
    lines.append("")
    lines.append(f"Required: ≥{PROMOTION_MIN_CLASSIFICATIONS} classifications, "
                 f"≥{PROMOTION_MIN_V2_CORRECT_RATE*100:.0f}% overall v2-correct rate, "
                 f"≥{PROMOTION_MIN_PER_INSTRUMENT_RATE*100:.0f}% per-instrument rate.")
    lines.append("")
    if ready:
        lines.append("**Status: READY — v2 promotion criteria met.** Trigger the "
                     "`v2_cutover` agent to ship `detector_version: v2` + rolling restart.")
    else:
        lines.append("**Status: NOT READY.**")
        for r in reasons:
            lines.append(f"- {r}")
    lines.append("")

    if result.warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in result.warnings:
            lines.append(f"- {w}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Aggregate weekly divergence classifications.",
    )
    p.add_argument(
        "--digest-dir", type=str, default=None,
        help="Digest directory (default: research/divergence_sampling/).",
    )
    p.add_argument(
        "--output", "-o", type=str, default=None,
        help="Also write the summary to this file path.",
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    dd = Path(args.digest_dir) if args.digest_dir else DIGEST_DIR
    result = parse_all(dd)
    rendered = render_summary(result)
    # Force UTF-8 encoding on stdout so non-ASCII chars (≥, —) survive
    # on Windows consoles where the default codec is cp1252.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Python 3.7+; no-op if already UTF-8
    except (AttributeError, OSError):
        pass
    try:
        sys.stdout.write(rendered + ("\n" if not rendered.endswith("\n") else ""))
    except UnicodeEncodeError:
        # Last-ditch fallback: write as bytes to the underlying buffer.
        sys.stdout.buffer.write((rendered + "\n").encode("utf-8", errors="replace"))
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        logger.info("Wrote summary to %s", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
