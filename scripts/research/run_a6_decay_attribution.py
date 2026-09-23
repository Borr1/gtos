"""A6 — Bayesian Decay Attribution CLI.

Reads the A1 dumb-baseline replay output (per-CAND realized R) plus
A5 regime tags (when joinable) and decomposes the H1->H2 XAUUSD WR
decay across the components we have the data to stratify on.

Why XAUUSD-only by default
==========================
Per A2 verdict: 5/7 instruments are INSUFFICIENT_N for the rolling-50
window. XAUUSD is the dominant trade-flow instrument and the focus of
the H1->H2 decay concern (CLAUDE.md item #4).

Data joinability (verified 2026-04-26)
======================================
* A1 ``results.jsonl`` (133 XAUUSD CANDs, 121 with realized R)
  carries: ``framework``, ``kill_zone``, ``side``, ``period_month``,
  ``ai_realized_r``, ``mechanical_realized_r``, ``mechanical_outcome``.
* A5 ``cands_with_regime.jsonl`` (107 XAUUSD CANDs) carries:
  ``regime``, ``setup_grade``, ``bias``, ``l2_passed``, ``direction``.
* A1 + A5 joined on (symbol, candle_close_time): only 1/133 matches
  by HH:MM — A5's source population is the older
  ``_trade_index.json`` (130 trades total), not the full A1
  backtest population. A5 enrichment is therefore SKIPPED in the
  default run; the components attributed are those visible in A1
  alone (framework, kill_zone, side).
* For displacement / FVG / touch_count we have no per-CAND
  features in the joined dataset — these are properties of the
  underlying market_state snapshot, not exposed through A1/A5/the
  session JSONs. They are documented as data gaps in
  ``src/research_infra/docs/A6_decay_attribution.md`` and will
  surface in the report's caveats.

Usage
=====
``python scripts/research/run_a6_decay_attribution.py [--output-dir DIR]``

Default output directory: ``research/decay_diagnostic/A6_attribution``.

Outputs
=======
* ``attribution.json`` — full machine-readable per-component decay
  attribution + 95% credible intervals + sanity check.
* ``report.md`` — strategic verdict block in the format requested by
  the brief.

The script is offline-only (no MT5, no Anthropic API, $0 spend).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Optional

# Make the worktree's project root importable.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.research_infra.bayesian_decay_attribution import (  # noqa: E402
    DEFAULT_PRIOR_A,
    DEFAULT_PRIOR_B,
    LOW_N_THRESHOLD,
    MISSING_VALUE,
    AttributionReport,
    ComponentAttribution,
    StratumStats,
    attribute_decay,
)
from src.research_infra.regime_matrix import (  # noqa: E402
    iter_cands_from_all_results,
)

logger = logging.getLogger("a6_decay_attribution")

DEFAULT_OUTPUT_DIR = "research/decay_diagnostic/A6_attribution"
DEFAULT_A1_RESULTS = "research/decay_diagnostic/A1_dumb_baseline/results.jsonl"
DEFAULT_A5_REGIME = "research/decay_diagnostic/A5_regime_matrix/cands_with_regime.jsonl"
DEFAULT_TRADE_INDEX = "knowledge_base/index/_trade_index.json"
DEFAULT_ALL_RESULTS_GLOB = "research/**/all_results*.json"
DEFAULT_SYMBOL = "XAUUSD"

H1_MONTHS: tuple[str, ...] = ("2026-01", "2026-02")
H2_MONTHS: tuple[str, ...] = ("2026-03", "2026-04")

#: Components we attempt to attribute. Order is preserved in the
#: report. Each must appear as a key on the trade dicts produced by
#: :func:`load_trades_from_all_results` or :func:`load_trades_from_a1`.
#:
#: The brief calls for: OB-zone, displacement, FVG, touch_count,
#: framework, session. `kill_zone` plays the role of `session`.
#: `side` and `setup_grade` (when joined) are bonus components.
#: `bias` and `l2_passed` are richer proxies present in the
#: `all_results` source — they enter the family when available.
DEFAULT_COMPONENTS: tuple[str, ...] = (
    "framework",
    "kill_zone",  # = session
    "side",
    "ob_zone",  # synthesized from framework
    "displacement_quality",  # joined from trade_index when available
    "fvg_present",  # synthesized from framework
    "touch_count",  # data gap (MISSING_VALUE)
    "setup_grade",  # joined from A5 / present in all_results
    "bias",  # bullish/bearish/neutral (all_results source)
    "l2_passed",  # pass/fail (all_results source)
    "regime",  # bullish/bearish/transitional/UNTAGGED (joined from A5)
)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def _norm_iso(t: str) -> str:
    """Normalise an ISO-8601 timestamp to 'Z' suffix form for join keys."""
    if not isinstance(t, str) or not t:
        return ""
    s = t.strip()
    if s.endswith("+00:00"):
        s = s[:-6] + "Z"
    return s


def load_trades_from_all_results(
    glob_pattern: str,
    *,
    symbol: str = DEFAULT_SYMBOL,
) -> list[dict]:
    """Read every ``all_results*.json`` matching ``glob_pattern`` and return
    XAUUSD CANDIDATE rows with realized R.

    This is the richer realized-R source compared to A1: it covers the
    backtest / simulation outputs that produced the population
    behind the H1->H2 WR decay finding (CLAUDE.md item #4).

    Each output dict carries:
    * ``symbol``, ``candle_close_time``, ``period_month``
    * ``kill_zone``, ``setup_grade``, ``bias`` (from row)
    * ``direction`` -> ``side``  (LONG/SHORT)
    * ``l2_passed`` -> 'pass' / 'fail'
    * ``r_multiple`` (numeric)
    * ``framework`` ('ob_retest' is the only framework these rows record)
    * ``ob_zone`` ('ob_pullback') and ``fvg_present`` ('no_fvg_required'):
      synthesized from framework, same convention as the A1 loader.
    * ``touch_count``: None (data gap, surfaces as MISSING_VALUE).

    The CAND population is filtered to ``decision == 'CANDIDATE'`` and
    ``r_multiple`` numeric (per :func:`iter_cands_from_all_results`'s
    ``realised_only`` default).
    """
    import glob as _glob

    paths: list[Path] = []
    for p in _glob.glob(glob_pattern, recursive=True):
        paths.append(Path(p))
    if not paths:
        logger.warning("No all_results*.json files matched glob %s", glob_pattern)
        return []

    trades: list[dict] = []
    for cand in iter_cands_from_all_results(paths, realised_only=True):
        if cand.get("symbol") != symbol:
            continue
        ct = cand.get("candle_close_time") or cand.get("candle_time") or ""
        if not ct or not str(ct).startswith("2026-"):
            continue  # restrict to 2026 (the H1/H2 windows of interest)
        period_month = str(ct)[:7]
        # Framework: most all_results.json rows are pre-multi-framework
        # and don't carry framework explicitly; we treat absent as
        # 'ob_retest' (the legacy single-framework default) but only
        # for the synthesized `ob_zone` / `fvg_present` proxies.
        framework = cand.get("framework") or "ob_retest"
        ob_zone = "ob_pullback" if framework == "ob_retest" else "other"
        fvg_present = (
            "fvg" if framework == "fvg_fill"
            else "no_fvg_required" if framework == "ob_retest"
            else "unknown"
        )
        direction = cand.get("direction")
        side = direction if direction in ("LONG", "SHORT") else None
        l2_passed = cand.get("l2_passed")
        l2_str = (
            "pass" if l2_passed is True
            else "fail" if l2_passed is False
            else None
        )
        trades.append(
            {
                "symbol": cand.get("symbol"),
                "candle_close_time": ct,
                "period_month": period_month,
                "framework": framework,
                "kill_zone": cand.get("kill_zone"),
                "side": side,
                "ob_zone": ob_zone,
                "fvg_present": fvg_present,
                "touch_count": None,
                "regime": None,  # filled by enrich_with_a5_regime
                "setup_grade": cand.get("setup_grade"),
                "bias": cand.get("bias"),
                "l2_passed": l2_str,
                "displacement_quality": None,  # filled by trade-index enrichment
                "r_multiple": float(cand["r_multiple"]),
                "outcome": cand.get("outcome"),
                "source_file": cand.get("source_file"),
                "ai_outcome_resolved": True,  # realised_only filter ensures this
            }
        )
    return trades


def load_trades_from_a1(
    a1_path: Path,
    *,
    symbol: str = DEFAULT_SYMBOL,
) -> list[dict]:
    """Read A1 results.jsonl and return trades for ``symbol`` with realized R.

    Each output dict carries:
    * ``cand_id``, ``symbol``, ``candle_close_time``, ``period_month``
    * ``framework``, ``kill_zone``, ``side``
    * ``r_multiple`` — the AI's realized R (if present); else None
    * ``mechanical_r`` — the mechanical baseline's realized R (if present)
    * ``ob_zone`` — synthesized: 'ob_pullback' if framework == ob_retest
    * ``fvg_present`` — synthesized: 'fvg' iff framework == fvg_fill
    * ``touch_count`` — None (unrecorded; will surface as MISSING_VALUE)

    Trades without a realized AI R are kept (so the reader sees the
    fill-rate decay separately) but their ``r_multiple`` is None and
    they are dropped from rate aggregations by ``_wins_losses``.
    """
    if not a1_path.exists():
        logger.warning("A1 input not found at %s; returning empty trade list", a1_path)
        return []
    trades: list[dict] = []
    with a1_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                logger.debug("A1: skipping malformed JSONL line")
                continue
            if row.get("symbol") != symbol:
                continue
            framework = row.get("framework")
            ob_zone = "ob_pullback" if framework == "ob_retest" else "other"
            fvg_present = (
                "fvg" if framework == "fvg_fill"
                else "no_fvg_required" if framework == "ob_retest"
                else "unknown"
            )
            r_ai = row.get("ai_realized_r")
            r_mech = row.get("mechanical_realized_r")
            trades.append(
                {
                    "cand_id": row.get("cand_id"),
                    "symbol": row.get("symbol"),
                    "candle_close_time": row.get("candle_close_time"),
                    "period_month": row.get("period_month"),
                    "framework": framework,
                    "kill_zone": row.get("kill_zone"),
                    "side": row.get("side"),
                    "ob_zone": ob_zone,
                    "fvg_present": fvg_present,
                    "touch_count": None,  # not joinable
                    "r_multiple": float(r_ai) if r_ai is not None else None,
                    "mechanical_r": float(r_mech) if r_mech is not None else None,
                    "ai_outcome_resolved": bool(row.get("ai_outcome_resolved")),
                }
            )
    return trades


def enrich_with_a5_regime(
    trades: list[dict],
    a5_path: Path,
    *,
    symbol: str = DEFAULT_SYMBOL,
) -> tuple[int, int]:
    """Mutate ``trades`` to add ``regime`` and ``setup_grade`` from A5.

    Returns ``(n_trades_processed, n_matched_to_a5)``. Unmatched trades
    keep ``regime = None`` (-> MISSING_VALUE in the attribution).
    """
    if not a5_path.exists():
        logger.warning("A5 input not found at %s; regime+setup_grade unavailable", a5_path)
        return (len(trades), 0)
    a5_idx: dict[tuple[str, str], dict] = {}
    with a5_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("symbol") != symbol:
                continue
            ct_norm = _norm_iso(row.get("candle_close_time", ""))
            if not ct_norm:
                continue
            a5_idx[(row["symbol"], ct_norm)] = row
    matched = 0
    for t in trades:
        key = (t["symbol"], _norm_iso(t.get("candle_close_time", "")))
        a5 = a5_idx.get(key)
        if a5 is None:
            continue
        t["regime"] = a5.get("regime")
        t["setup_grade"] = a5.get("setup_grade")
        matched += 1
    return (len(trades), matched)


def enrich_with_trade_index(
    trades: list[dict],
    trade_index_path: Path,
    *,
    symbol: str = DEFAULT_SYMBOL,
) -> tuple[int, int]:
    """Add ``displacement_quality`` from the trade index, joined on (symbol, date).

    Multiple trades may share a date; we apply the first available
    record's displacement_quality to all matching trades on that date
    (fanned-out join). Returns ``(n_trades_processed, n_matched)``.
    """
    if not trade_index_path.exists():
        logger.warning("Trade index not found at %s; displacement_quality unavailable", trade_index_path)
        return (len(trades), 0)
    with trade_index_path.open("r", encoding="utf-8") as fh:
        idx = json.load(fh)
    by_date: dict[str, dict] = {}
    for t in idx.get("trades", []):
        if t.get("symbol") != symbol:
            continue
        d = t.get("date")
        if not d:
            continue
        if d not in by_date:
            by_date[d] = t
    matched = 0
    for t in trades:
        ct = t.get("candle_close_time", "")
        if not ct:
            continue
        date = ct[:10]
        idx_row = by_date.get(date)
        if idx_row is None:
            continue
        disp = idx_row.get("displacement_quality")
        if disp:
            t["displacement_quality"] = disp
            matched += 1
    return (len(trades), matched)


def split_h1_h2(
    trades: list[dict],
    *,
    h1_months: tuple[str, ...] = H1_MONTHS,
    h2_months: tuple[str, ...] = H2_MONTHS,
) -> tuple[list[dict], list[dict]]:
    """Partition trades into H1 (Jan-Feb) and H2 (Mar-Apr) for 2026.

    Trades outside both windows (e.g. 2024 / 2025 / earlier 2026
    months not in either set) are excluded.
    """
    h1: list[dict] = []
    h2: list[dict] = []
    for t in trades:
        pm = t.get("period_month") or ""
        if pm in h1_months:
            h1.append(t)
        elif pm in h2_months:
            h2.append(t)
    return h1, h2


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------


def _stratum_to_dict(s: StratumStats) -> dict:
    return {
        "value": s.value,
        "n": s.n,
        "wins": s.wins,
        "wr": None if s.n == 0 else round(s.wr, 4),
        "posterior_alpha": round(s.posterior_alpha, 4),
        "posterior_beta": round(s.posterior_beta, 4),
        "posterior_mean": round(s.posterior_mean, 4),
        "ci_lo": round(s.ci_lo, 4),
        "ci_hi": round(s.ci_hi, 4),
        "low_n": s.low_n,
        "missing": s.missing,
    }


def _component_to_dict(c: ComponentAttribution) -> dict:
    return {
        "component": c.component,
        "h1": {v: _stratum_to_dict(s) for v, s in c.h1.items()},
        "h2": {v: _stratum_to_dict(s) for v, s in c.h2.items()},
        "attributed_decay_pp": round(c.attributed_decay_pp, 3),
        "attributed_decay_ci": (
            None
            if c.attributed_decay_ci is None
            else [round(c.attributed_decay_ci[0], 3), round(c.attributed_decay_ci[1], 3)]
        ),
        "used_strata": c.used_strata,
        "skipped_strata": [list(t) for t in c.skipped_strata],
        "raw_p": round(c.raw_p, 6),
        "bonf_p": round(c.bonf_p, 6),
        "family_size": c.family_size,
    }


def report_to_dict(report: AttributionReport) -> dict:
    return {
        "h1_n": report.h1_n,
        "h1_wins": report.h1_wins,
        "h1_wr": round(report.h1_wr, 4),
        "h2_n": report.h2_n,
        "h2_wins": report.h2_wins,
        "h2_wr": round(report.h2_wr, 4),
        "observed_delta_pp": round(report.observed_delta_pp, 3),
        "total_attributed_pp": round(report.total_attributed_pp, 3),
        "residual_pp": round(report.residual_pp, 3),
        "family_size": report.family_size,
        "prior": list(report.prior),
        "low_n_threshold": report.low_n_threshold,
        "components": [_component_to_dict(c) for c in report.components],
    }


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------


def _fmt_strata_wrs(stat_map: dict[str, StratumStats]) -> str:
    """Render per-stratum WRs as 'value: 60.0% (n=30)' parts."""
    parts: list[str] = []
    for v in sorted(stat_map.keys()):
        s = stat_map[v]
        if s.n == 0 or s.value == MISSING_VALUE:
            continue
        wr_pct = 100.0 * (s.wins / s.n) if s.n > 0 else 0.0
        parts.append(f"{v}: {wr_pct:.1f}% (n={s.n})")
    return ", ".join(parts) if parts else "-"


def _fmt_ci(ci: Optional[tuple[float, float]]) -> str:
    if ci is None:
        return "-"
    return f"[{ci[0]:.2f}, {ci[1]:.2f}]"


def render_report_md(
    report: AttributionReport,
    *,
    symbol: str,
    a1_path: str,
    a5_match_count: int,
    trade_index_match_count: int,
    n_trades_total: int,
    n_unfilled_h2: int,
    data_gaps: list[str],
) -> str:
    lines: list[str] = []
    lines.append(f"# A6 — Bayesian Decay Attribution ({symbol})")
    lines.append("")
    lines.append(
        f"Decomposes the H1->H2 2026 WR decay across "
        f"{report.family_size} components. Beta-binomial conjugate-prior "
        f"(Beta({report.prior[0]}, {report.prior[1]}) prior). 95% credible "
        f"intervals via Monte Carlo composition. Bonferroni correction "
        f"applied across the family of components."
    )
    lines.append("")
    lines.append("## Top-line counts")
    lines.append("")
    lines.append("| Period | n | wins | WR |")
    lines.append("|---|---:|---:|---:|")
    lines.append(f"| H1 (2026-01..02) | {report.h1_n} | {report.h1_wins} | {report.h1_wr * 100:.1f}% |")
    lines.append(f"| H2 (2026-03..04) | {report.h2_n} | {report.h2_wins} | {report.h2_wr * 100:.1f}% |")
    lines.append(f"| **Observed delta** | | | **{report.observed_delta_pp:+.2f}pp** |")
    lines.append("")
    lines.append("## Decay attribution")
    lines.append("")
    lines.append(
        "| Component | H1 stratum WRs | H2 stratum WRs | attributed pp | "
        "95% CI | raw_p | bonf_p |"
    )
    lines.append("|---|---|---|---:|---|---:|---:|")
    for c in report.components:
        h1_wrs = _fmt_strata_wrs(c.h1)
        h2_wrs = _fmt_strata_wrs(c.h2)
        ci = _fmt_ci(c.attributed_decay_ci)
        lines.append(
            f"| {c.component} | {h1_wrs} | {h2_wrs} | {c.attributed_decay_pp:+.2f} | "
            f"{ci} | {c.raw_p:.4f} | {c.bonf_p:.4f} |"
        )
    lines.append(
        f"| **Total attributed (mean)** | | | **{report.total_attributed_pp:+.2f}** | | | |"
    )
    lines.append(
        f"| **Observed delta** | | | **{report.observed_delta_pp:+.2f}** | | | |"
    )
    lines.append(
        f"| **Residual (unexplained)** | | | **{report.residual_pp:+.2f}** | | | |"
    )
    lines.append("")

    # Per-stratum tables
    lines.append("## Per-component stratum detail")
    lines.append("")
    for c in report.components:
        lines.append(f"### {c.component}")
        lines.append("")
        lines.append(
            "| Value | H1 n | H1 wins | H1 WR | H1 mean (post.) | "
            "H2 n | H2 wins | H2 WR | H2 mean (post.) | flag |"
        )
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
        all_keys = sorted(set(c.h1.keys()) | set(c.h2.keys()))
        for k in all_keys:
            s1 = c.h1.get(k)
            s2 = c.h2.get(k)
            if s1 is None or s2 is None:
                continue
            wr1 = f"{(s1.wins / s1.n) * 100:.1f}%" if s1.n > 0 else "-"
            wr2 = f"{(s2.wins / s2.n) * 100:.1f}%" if s2.n > 0 else "-"
            flag_parts: list[str] = []
            if s1.low_n or s2.low_n:
                flag_parts.append("LOW_N")
            if s1.missing or s2.missing:
                flag_parts.append("MISSING")
            if k in c.used_strata:
                flag_parts.append("USED")
            else:
                # Try to find skip reason
                for sv, reason in c.skipped_strata:
                    if sv == k:
                        flag_parts.append(reason)
                        break
            lines.append(
                f"| {k} | {s1.n} | {s1.wins} | {wr1} | "
                f"{s1.posterior_mean:.3f} | {s2.n} | {s2.wins} | {wr2} | "
                f"{s2.posterior_mean:.3f} | {' / '.join(flag_parts) or '-'} |"
            )
        lines.append("")

    # Strategic verdict
    lines.append("## Strategic verdict")
    # Top driver
    drivers = [(c, abs(c.attributed_decay_pp)) for c in report.components if c.used_strata]
    drivers.sort(key=lambda x: x[1], reverse=True)
    if drivers:
        top, top_mag = drivers[0]
        # Total magnitude across components for share calculation
        total_mag = sum(d[1] for d in drivers) or 1.0
        share = top_mag / total_mag * 100.0
        lines.append("")
        lines.append(
            f"**Top decay driver:** `{top.component}` "
            f"({top.attributed_decay_pp:+.2f}pp, {share:.0f}% of total "
            f"absolute attributable mass; raw_p={top.raw_p:.4f}, "
            f"bonf_p={top.bonf_p:.4f})."
        )
        lines.append("")
        if abs(report.observed_delta_pp) < 0.5:
            lines.append(
                "Observed delta is near zero — no decay to attribute on this "
                "filtered sample (`r_multiple` only)."
            )
        else:
            ranked = ", ".join(
                f"`{d[0].component}` ({d[0].attributed_decay_pp:+.1f}pp)"
                for d in drivers[:5]
            )
            lines.append(f"Ranked by absolute magnitude: {ranked}.")
    else:
        lines.append("No component had usable strata in BOTH H1 and H2 — attribution is empty.")
    lines.append("")

    # Methodology + caveats
    lines.append("## Methodology")
    lines.append("")
    lines.append(
        f"- Beta(α₀, β₀) = ({report.prior[0]}, {report.prior[1]}) "
        f"uninformed prior. Posterior per stratum: "
        f"`Beta(α₀ + wins, β₀ + losses)`."
    )
    lines.append(
        f"- Per-component attribution: "
        f"`sum_strata( (WR_h1 - WR_h2) * n_share_h2 )` over strata "
        f"with n ≥ {report.low_n_threshold} in BOTH H1 and H2."
    )
    lines.append(
        "- 95% credible interval via 4000 Monte Carlo draws of "
        "WR_h1, WR_h2 ~ Beta posteriors, recomputing the weighted sum."
    )
    lines.append(
        "- Chi-square sum-of-2x2 contingency over used strata for "
        "raw_p; Bonferroni correction across the component family."
    )
    lines.append(
        "- `Total attributed (mean)` averages across components rather "
        "than summing — each component is an alternative full "
        "decomposition over its own strata. Summing would double-count."
    )
    lines.append("")
    lines.append("## Caveats")
    lines.append("")
    lines.append(f"- Inputs: A1 results.jsonl ({a1_path}); n_trades_total={n_trades_total}.")
    lines.append(
        f"- A5 regime/setup_grade join: {a5_match_count} / {n_trades_total} "
        "matched on (symbol, candle_close_time). A5's source population is the "
        "older `_trade_index.json`, NOT the full A1 backtest population — this "
        "limits regime/setup_grade attribution power and most strata flag MISSING."
    )
    lines.append(
        f"- Trade-index displacement_quality join: {trade_index_match_count} / "
        f"{n_trades_total} matched on (symbol, date). 2026 trade-index rows "
        "carry no displacement_quality; coverage is therefore zero on the "
        "decay window of interest."
    )
    lines.append(
        f"- `touch_count` and authentic `fvg_present` are NOT recoverable from A1 / A5 / "
        "session JSONs (they're properties of the underlying market_state "
        "snapshot). Both surface as MISSING_VALUE for all rows; their stratum "
        "rows will be skipped from the attribution sum. The synthesized "
        "`fvg_present` here is a coarse proxy keyed off framework only."
    )
    lines.append(
        f"- `n_unfilled_h2`={n_unfilled_h2}: H2 rows with `ai_outcome_resolved=False` "
        "(no realized R recorded). These do NOT enter the rate aggregation. "
        "If H2 fill-rate dropped, the attribution analyzes the survivor cohort only."
    )
    if data_gaps:
        lines.append("- Additional notes:")
        for g in data_gaps:
            lines.append(f"  - {g}")
    lines.append(
        "- `r_multiple` proxy: AI realized R from A1 (`ai_realized_r` field). "
        "Trades without recorded realized R are dropped from rate aggregations "
        "(neither win nor loss)."
    )
    lines.append("- Per memory `feedback_walk_level_evidence_not_predictive`: this analysis is realized-R based.")
    lines.append("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "A6 — Bayesian decay attribution. Reads A1 + A5 + trade index, "
            "decomposes H1->H2 WR decay across components, emits "
            "attribution.json + report.md."
        )
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=(
            f"Directory to write attribution.json + report.md "
            f"(default: {DEFAULT_OUTPUT_DIR})."
        ),
    )
    parser.add_argument(
        "--source",
        choices=("all_results", "a1"),
        default="all_results",
        help=(
            "Realized-R source. 'all_results' (default) is the richer "
            "research/**/all_results*.json corpus (~107 XAUUSD 2026 "
            "CANDs with realized R); 'a1' is the A1 dumb-baseline output "
            "(~33 XAUUSD 2026 CANDs with realized R)."
        ),
    )
    parser.add_argument(
        "--a1-results",
        default=DEFAULT_A1_RESULTS,
        help=f"Path to A1 results.jsonl (default: {DEFAULT_A1_RESULTS}).",
    )
    parser.add_argument(
        "--all-results-glob",
        default=DEFAULT_ALL_RESULTS_GLOB,
        help=f"Glob for all_results*.json files (default: {DEFAULT_ALL_RESULTS_GLOB}).",
    )
    parser.add_argument(
        "--a5-regime",
        default=DEFAULT_A5_REGIME,
        help=f"Path to A5 cands_with_regime.jsonl (default: {DEFAULT_A5_REGIME}).",
    )
    parser.add_argument(
        "--trade-index",
        default=DEFAULT_TRADE_INDEX,
        help=f"Path to KB trade index (default: {DEFAULT_TRADE_INDEX}).",
    )
    parser.add_argument(
        "--symbol",
        default=DEFAULT_SYMBOL,
        help=f"Symbol to attribute (default: {DEFAULT_SYMBOL}).",
    )
    parser.add_argument(
        "--low-n-threshold",
        type=int,
        default=LOW_N_THRESHOLD,
        help=f"Stratum n floor for inclusion (default: {LOW_N_THRESHOLD}).",
    )
    parser.add_argument(
        "--ci-samples",
        type=int,
        default=4000,
        help="Monte Carlo samples for the per-component decay CI (default: 4000).",
    )
    parser.add_argument(
        "--ci-seed",
        type=int,
        default=20260426,
        help="Deterministic seed for the Monte Carlo CI.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational logging (errors still surface).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    a1_path = Path(args.a1_results)
    a5_path = Path(args.a5_regime)
    ti_path = Path(args.trade_index)
    if not a1_path.is_absolute():
        a1_path = _PROJECT_ROOT / a1_path
    if not a5_path.is_absolute():
        a5_path = _PROJECT_ROOT / a5_path
    if not ti_path.is_absolute():
        ti_path = _PROJECT_ROOT / ti_path

    if args.source == "all_results":
        glob_str = args.all_results_glob
        if not Path(glob_str).is_absolute():
            glob_str = str(_PROJECT_ROOT / glob_str)
        logger.info(
            "Loading all_results trades for %s from glob %s",
            args.symbol, glob_str,
        )
        trades = load_trades_from_all_results(glob_str, symbol=args.symbol)
        source_path = glob_str
        logger.info("Loaded %d %s trades from all_results", len(trades), args.symbol)
    else:
        logger.info("Loading A1 trades for %s from %s", args.symbol, a1_path)
        trades = load_trades_from_a1(a1_path, symbol=args.symbol)
        source_path = str(a1_path)
        logger.info("Loaded %d %s trades from A1", len(trades), args.symbol)

    logger.info("Enriching with A5 regime + setup_grade ...")
    n_total, n_a5 = enrich_with_a5_regime(trades, a5_path, symbol=args.symbol)
    logger.info("A5 join: %d / %d matched", n_a5, n_total)

    logger.info("Enriching with trade-index displacement_quality ...")
    n_total, n_ti = enrich_with_trade_index(trades, ti_path, symbol=args.symbol)
    logger.info("Trade-index join: %d / %d matched", n_ti, n_total)

    h1_trades, h2_trades = split_h1_h2(trades)
    n_unfilled_h2 = sum(
        1 for t in h2_trades if not t.get("ai_outcome_resolved")
    )
    logger.info(
        "H1 rows: %d (with R: %d) | H2 rows: %d (with R: %d, unresolved: %d)",
        len(h1_trades),
        sum(1 for t in h1_trades if t.get("r_multiple") is not None),
        len(h2_trades),
        sum(1 for t in h2_trades if t.get("r_multiple") is not None),
        n_unfilled_h2,
    )

    components = list(DEFAULT_COMPONENTS)

    report = attribute_decay(
        h1_trades,
        h2_trades,
        components=components,
        prior_a=DEFAULT_PRIOR_A,
        prior_b=DEFAULT_PRIOR_B,
        low_n_threshold=args.low_n_threshold,
        ci_n_samples=args.ci_samples,
        ci_seed=args.ci_seed,
    )

    # Dump the attribution.json
    attribution_path = output_dir / "attribution.json"
    payload = report_to_dict(report)
    payload["run_metadata"] = {
        "symbol": args.symbol,
        "source": args.source,
        "source_path": source_path,
        "a1_results_path": str(a1_path),
        "a5_regime_path": str(a5_path),
        "trade_index_path": str(ti_path),
        "h1_months": list(H1_MONTHS),
        "h2_months": list(H2_MONTHS),
        "components": components,
        "n_trades_total": n_total,
        "n_h1": len(h1_trades),
        "n_h2": len(h2_trades),
        "n_unfilled_h2": n_unfilled_h2,
        "n_a5_matched": n_a5,
        "n_trade_index_matched": n_ti,
        "ci_samples": args.ci_samples,
        "ci_seed": args.ci_seed,
        "harness_version": "A6-v1",
    }
    attribution_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote %s", attribution_path)

    # Dump the markdown report
    data_gaps = [
        f"`{c}` is synthesized from `framework`, not measured directly."
        for c in ("ob_zone", "fvg_present")
    ]
    md = render_report_md(
        report,
        symbol=args.symbol,
        a1_path=source_path,
        a5_match_count=n_a5,
        trade_index_match_count=n_ti,
        n_trades_total=n_total,
        n_unfilled_h2=n_unfilled_h2,
        data_gaps=data_gaps,
    )
    report_path = output_dir / "report.md"
    report_path.write_text(md, encoding="utf-8")
    logger.info("Wrote %s", report_path)

    # Print verdict block to stdout for caller convenience.
    if not args.quiet:
        print()
        print(f"[A6] {args.symbol} H1 vs H2 2026 attribution")
        print(f"  observed delta: {report.observed_delta_pp:+.2f}pp")
        print(f"  total attributed (mean across components): {report.total_attributed_pp:+.2f}pp")
        print(f"  residual: {report.residual_pp:+.2f}pp")
        for c in report.components:
            ci_str = (
                f"[{c.attributed_decay_ci[0]:+.2f}, {c.attributed_decay_ci[1]:+.2f}]"
                if c.attributed_decay_ci is not None
                else "n/a"
            )
            print(
                f"    {c.component:<22s} attributed={c.attributed_decay_pp:+6.2f}pp "
                f"CI={ci_str} bonf_p={c.bonf_p:.4f} "
                f"used={len(c.used_strata)} skipped={len(c.skipped_strata)}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
