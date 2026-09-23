"""A3 — Per-Month Per-Session Per-Regime [Per-Side] Stratification CLI runner.

Loads realized-R outcomes from the available trade data sources and writes
``strata.jsonl`` + ``change_points.json`` + ``report.md`` into the output
directory.

By default the runner stratifies across the F2 4-axis schema
``(instrument, month, session, regime, side)``. Pass
``--no-side-stratification`` to fall back to the legacy 3-axis schema
``(instrument, month, session, regime)`` — that mode is bit-identical to
the historical output and is preserved for any caller that consumed
strata rows before F2 shipped.

Trade data sources (in priority order)
--------------------------------------
1. **Research backtest slices** —
   ``research/**/all_results.json`` rows that carry ``r_multiple`` +
   ``candle_time``. This is the **primary** source — every modern
   backtest writes the canonical schema (``candle_time`` ISO-8601,
   ``r_multiple``, ``direction``, ``symbol``).

2. **Live trade records** —
   ``knowledge_base/trade_records/{INSTRUMENT}/*.json``. Live records
   carry full pipeline state but their realized R is not embedded
   per-record (it is rolled up in ``knowledge_base/index/_trade_index.json``).
   The CLI cross-references the index by ``trade_id`` shape — anything
   matching the live ``YYYY-MM-DD_session_HHMM`` filename pattern that
   is also present in the index gets its r_multiple from the index.

3. **Unified historical CSV** (fallback) —
   ``research/b_deep_audit_2026-04-19/phase1/_delta_scratch/trades_unified.csv``
   if present. Provides per-day historical r_multiples but no exact
   timestamp; falls back to assigning the trade to ``Off`` session
   when the kill_zone column does not allow direct mapping.

Usage
-----

    # Default — side-stratified into a separate sibling directory
    python scripts/research/run_a3_stratification.py \\
        --output-dir research/decay_diagnostic/A3_stratification_side

    # Filter to specific instruments
    python scripts/research/run_a3_stratification.py \\
        --output-dir <dir> --symbols XAUUSD,USDJPY

    # Legacy 3-axis output (no side)
    python scripts/research/run_a3_stratification.py \\
        --output-dir <dir> --no-side-stratification

Outputs
-------
``strata.jsonl``         — one row per stratum
``change_points.json``   — list of identified WR shifts (Bonferroni-corrected)
``report.md``            — heatmap-friendly summary table
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import logging
import os
import sys
from collections import defaultdict
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

from src.research_infra.stratification import (  # noqa: E402
    DEFAULT_KILL_ZONES,
    ChangePoint,
    StratifiedOutcomes,
    StratumKey,
    StratumOutcomes,
    coverage_summary,
    find_change_points,
    stratified_to_rows,
    stratify,
)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Trade loaders
# ---------------------------------------------------------------------------


def _load_research_slices(project_root: Path) -> list[dict[str, Any]]:
    """Pull every ``all_results.json`` row that carries an ``r_multiple``."""
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
            if "r_multiple" not in row:
                continue
            ts = row.get("candle_time") or row.get("timestamp_utc") or row.get("ts")
            sym = row.get("symbol")
            r = row.get("r_multiple")
            direction = row.get("direction")
            if ts is None or sym is None or r is None:
                continue
            out.append(
                {
                    "candle_close_time": ts,
                    "symbol": sym,
                    "r_multiple": r,
                    "direction": direction,
                    "_source": f"research:{Path(path).relative_to(project_root)}",
                }
            )
    return out


def _load_unified_csv(project_root: Path) -> list[dict[str, Any]]:
    """Read the historical trades_unified.csv (per-day; no exact UTC timestamp).

    We synthesize a ``candle_close_time`` at noon UTC on the trade ``date``
    so the month bucket is correct. Session is derived from the
    ``kill_zone`` column directly rather than via ``assign_session`` — the
    historical row doesn't have an exact UTC time. To force the
    stratifier to use the kill_zone label, we set the synthetic time to
    the start of the configured kill zone for that instrument, falling
    back to noon UTC if the instrument has no kill-zone for that label.
    """
    out: list[dict[str, Any]] = []
    csv_path = (
        project_root
        / "research"
        / "b_deep_audit_2026-04-19"
        / "phase1"
        / "_delta_scratch"
        / "trades_unified.csv"
    )
    if not csv_path.exists():
        return out
    try:
        with csv_path.open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                date_s = row.get("date")
                sym = row.get("symbol")
                r_s = row.get("r_multiple")
                kz = (row.get("kill_zone") or "").lower()
                direction = row.get("direction")
                if not (date_s and sym and r_s):
                    continue
                try:
                    r_val = float(r_s)
                except ValueError:
                    continue
                # Map kill-zone label to its UTC start so the stratifier's
                # session lookup hits the configured window.
                inst_zones = DEFAULT_KILL_ZONES.get(sym, {})
                window = inst_zones.get(kz)
                if window is not None and "start_utc" in window:
                    hh, mm = window["start_utc"].split(":")
                    iso = f"{date_s}T{int(hh):02d}:{int(mm):02d}:00Z"
                else:
                    iso = f"{date_s}T12:00:00Z"
                out.append(
                    {
                        "candle_close_time": iso,
                        "symbol": sym,
                        "r_multiple": r_val,
                        "direction": direction or None,
                        "_source": "unified_csv",
                    }
                )
    except OSError as e:
        logger.warning("could not read %s: %s", csv_path, e)
    return out


def _load_trade_index(project_root: Path) -> list[dict[str, Any]]:
    """Read knowledge_base/index/_trade_index.json (batch + live trade index).

    The index doesn't carry exact UTC timestamps either — only ``date``
    and ``kill_zone``. We synthesize the timestamp from the kill-zone
    start (same approach as the unified CSV).
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
        sym = t.get("symbol")
        date_s = t.get("date")
        r = t.get("r_multiple")
        kz = (t.get("kill_zone") or "").lower()
        direction = t.get("direction")
        if not (sym and date_s and r is not None):
            continue
        try:
            r_val = float(r)
        except (TypeError, ValueError):
            continue
        inst_zones = DEFAULT_KILL_ZONES.get(sym, {})
        window = inst_zones.get(kz)
        if window is not None and "start_utc" in window:
            hh, mm = window["start_utc"].split(":")
            iso = f"{date_s}T{int(hh):02d}:{int(mm):02d}:00Z"
        else:
            iso = f"{date_s}T12:00:00Z"
        out.append(
            {
                "candle_close_time": iso,
                "symbol": sym,
                "r_multiple": r_val,
                "direction": direction or None,
                "_source": "trade_index",
            }
        )
    return out


def _dedupe(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop duplicate trades by (symbol, candle_close_time, r_multiple).

    Research slice rows tend to overlap with the unified CSV / trade index
    when slices were lifted from batch sessions. The triple
    (symbol, ts, r) is unique per backtest scenario; collisions are
    effectively the same trade routed through two ingestion paths.
    """
    seen: set[tuple[str, str, float]] = set()
    out: list[dict[str, Any]] = []
    for t in trades:
        try:
            r = float(t.get("r_multiple"))
        except (TypeError, ValueError):
            continue
        key = (
            str(t.get("symbol")),
            str(t.get("candle_close_time")),
            round(r, 6),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out


def _load_kill_zones_yaml(project_root: Path) -> Optional[dict]:
    """Load the per-instrument kill-zone schedule from agent_config.yaml.

    The YAML overlays the top-level ``market.kill_zones`` block with the
    per-instrument ``instruments.<SYMBOL>.market.kill_zones`` block — the
    overlay only includes zones that override the default. So XAUUSD's
    instruments block defines ``ny`` only, and London is inherited from
    the top-level. This loader merges both layers per instrument.

    Returns ``None`` if PyYAML is not installed or the file is missing —
    the stratifier falls back to ``DEFAULT_KILL_ZONES`` in that case
    (which is a faithful copy of the production config and tracked
    in this module).
    """
    try:
        import yaml  # type: ignore
    except ImportError:
        logger.info("PyYAML not installed; using DEFAULT_KILL_ZONES")
        return None
    path = project_root / "config" / "agent_config.yaml"
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        logger.warning("could not parse %s: %s", path, e)
        return None
    if not isinstance(cfg, dict):
        return None

    def _normalize_zones(raw: dict) -> dict[str, dict[str, str]]:
        out_zones: dict[str, dict[str, str]] = {}
        for zone_name, window in raw.items():
            if not isinstance(window, dict):
                continue
            if "start_utc" not in window or "end_utc" not in window:
                continue
            out_zones[zone_name] = {
                "start_utc": str(window["start_utc"]),
                "end_utc": str(window["end_utc"]),
            }
        return out_zones

    # Top-level market.kill_zones — the default schedule. In the production
    # config this happens to be the XAUUSD schedule (XAUUSD is the default
    # `market.symbol`). We use it as a baseline that per-instrument blocks
    # extend / override.
    top_market = cfg.get("market") or {}
    top_zones_raw = top_market.get("kill_zones") or {}
    top_default = (
        _normalize_zones(top_zones_raw) if isinstance(top_zones_raw, dict) else {}
    )
    default_symbol = top_market.get("symbol")

    instruments = cfg.get("instruments") or {}
    out: dict[str, dict[str, dict[str, str]]] = {}
    for sym, block in instruments.items():
        if not isinstance(block, dict):
            continue
        market = block.get("market") or {}
        zones = market.get("kill_zones") or {}
        per_inst = (
            _normalize_zones(zones) if isinstance(zones, dict) else {}
        )
        # If this is the default-symbol instrument, START from the top-level
        # default and let the per-instrument block overlay specific zones.
        # For non-default symbols, the per-instrument block is authoritative
        # (the production code does the same).
        if sym == default_symbol and top_default:
            merged = {**top_default, **per_inst}
        else:
            merged = per_inst
        if merged:
            out[sym] = merged

    # Always seed the default symbol entry from the top-level block when
    # the instruments overlay didn't list it. (The XAUUSD instruments
    # block exists but only defines `ny`; this keeps both london + ny.)
    if default_symbol and default_symbol not in out and top_default:
        out[default_symbol] = top_default

    return out or None


def _resolve_structure_log(project_root: Path) -> Optional[Path]:
    """Locate any structure-detector log the loader can consume.

    Returned path is a *seed* for ``stratification._load_structure_log``;
    that loader walks the path's parent directory + the conventional
    archive directory (``research/archive/structure_detector_divergences/``)
    looking for sibling ``.jsonl`` and ``.jsonl.gz`` files (live divergence
    log + rotated archives + offline backfill at
    ``shadow_logs/structure_detector_backfill_*.jsonl``). All matching
    files are merged with "latest write wins" semantics.

    Resolution order
    ----------------
    1. ``shadow_logs/structure_detector_divergences.jsonl`` — the production
       live log; opens the door to its sibling backfill + same-dir archives.
    2. ``shadow_logs/structure_detector_backfill_2026.jsonl`` — the offline
       backfill produced by ``backfill_v2_regime.py``. Selected when no
       live log exists (e.g. fresh worktree); the loader's companion
       walker still pulls in any archives the live log left behind.
    3. ``research/archive/structure_detector_divergences/`` — falls back
       to the most-recent rotated archive when neither live nor backfill
       lives in ``shadow_logs/``.
    4. ``None`` — every regime collapses to UNTAGGED.
    """
    shadow_dir = project_root / "shadow_logs"
    primary = shadow_dir / "structure_detector_divergences.jsonl"
    if primary.exists():
        return primary

    backfill = shadow_dir / "structure_detector_backfill_2026.jsonl"
    if backfill.exists():
        return backfill

    archive_dir = (
        project_root / "research" / "archive" / "structure_detector_divergences"
    )
    if archive_dir.exists():
        # Pick the newest archive file by mtime — the loader expands this
        # into the full archive directory automatically via its companion
        # walker, so we only need to seed it with one entry.
        candidates = sorted(
            archive_dir.glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            return candidates[0]
    return None


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------


def _earliest_backfill_ts(structure_log: Optional[Path]) -> Optional[str]:
    """Return the earliest ``ts`` in the structure log seed file.

    Used for the report's coverage caption so the "from XXXX onward"
    string tracks the actual backfill range without manual edits.
    Returns ``None`` on any error — the caller falls back to a generic
    caption.
    """
    if structure_log is None or not structure_log.exists():
        return None
    earliest: Optional[str] = None
    try:
        with structure_log.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = row.get("ts") or row.get("h4_start_iso")
                if ts is None:
                    continue
                if earliest is None or ts < earliest:
                    earliest = ts
    except OSError:
        return None
    return earliest


def render_report_md(
    *,
    stratified_by_inst: dict[str, StratifiedOutcomes],
    change_points: list[ChangePoint],
    coverage_by_inst: dict[str, dict[str, Any]],
    min_n: int,
    structure_log: Optional[Path] = None,
    side_stratified: bool,
) -> str:
    """Build a markdown report from the stratification output.

    The report shape adapts to ``side_stratified``:

    * Off  — the legacy 3-axis report (instrument-month-session-regime).
    * On   — adds a Side column to the change-points and per-instrument
             tables, plus a "Side-stratified change points (LONG breakdown)"
             section that pulls the LONG cells out for fast visual scan, and
             a SHORT-cells panel listing every (m, s, r, SHORT) cell with
             n ≥ 10. Section is the F2 deliverable header verbatim.
    """
    lines: list[str] = []
    if side_stratified:
        lines.append(
            "# A3 — Per-Month Per-Session Per-Regime Per-Side Stratification"
        )
    else:
        lines.append(
            "# A3 — Per-Month Per-Session Per-Regime Stratification"
        )
    lines.append("")
    lines.append(
        f"_Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}_"
    )
    lines.append(
        f"_Side stratification: {'ON (4-axis)' if side_stratified else 'OFF (3-axis legacy)'}_"
    )
    lines.append("")

    # Change points table
    lines.append("## Change points (>=15pp shift, n>=" + str(min_n) + " both sides)")
    lines.append("")
    if change_points:
        if side_stratified:
            lines.append(
                "| Instrument | Month transition | Session | Regime | Side | "
                "WR before | WR after | Δpp | n_before | n_after | bonf_p |"
            )
            lines.append(
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
            )
            for cp in change_points:
                lines.append(
                    "| {instr} | {mb} → {ma} | {sess} | {reg} | {side} | "
                    "{wb:.1%} | {wa:.1%} | {dp:+.1f} | {nb} | {na} | {bp:.4f} |".format(
                        instr=cp.instrument,
                        mb=cp.month_before,
                        ma=cp.month_after,
                        sess=cp.session,
                        reg=cp.regime,
                        side=cp.side,
                        wb=cp.wr_before,
                        wa=cp.wr_after,
                        dp=cp.delta_pp,
                        nb=cp.n_before,
                        na=cp.n_after,
                        bp=cp.bonf_p,
                    )
                )
        else:
            lines.append(
                "| Instrument | Month transition | Session | Regime | "
                "WR before | WR after | Δpp | n_before | n_after | bonf_p |"
            )
            lines.append(
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
            )
            for cp in change_points:
                lines.append(
                    "| {instr} | {mb} → {ma} | {sess} | {reg} | "
                    "{wb:.1%} | {wa:.1%} | {dp:+.1f} | {nb} | {na} | {bp:.4f} |".format(
                        instr=cp.instrument,
                        mb=cp.month_before,
                        ma=cp.month_after,
                        sess=cp.session,
                        reg=cp.regime,
                        wb=cp.wr_before,
                        wa=cp.wr_after,
                        dp=cp.delta_pp,
                        nb=cp.n_before,
                        na=cp.n_after,
                        bp=cp.bonf_p,
                    )
                )
    else:
        if side_stratified:
            lines.append(
                "_No (instrument, session, regime, side) pair shows a >=15pp "
                "month-over-month WR shift with n>={n} on both sides._".format(n=min_n)
            )
        else:
            lines.append(
                "_No (instrument, session, regime) pair shows a >=15pp month-over-month "
                "WR shift with n>={n} on both sides._".format(n=min_n)
            )
    lines.append("")

    # F2 verdict block — side-stratified change points (LONG breakdown).
    if side_stratified:
        long_cps = [cp for cp in change_points if cp.side == "LONG"]
        lines.append("## Side-stratified change points (LONG breakdown — H1 vs H2)")
        lines.append("")
        if long_cps:
            lines.append(
                "| Transition | Session | Regime | Side | "
                "WR before | WR after | Δpp | n_b/n_a |"
            )
            lines.append(
                "| --- | --- | --- | --- | --- | --- | --- | --- |"
            )
            for cp in long_cps:
                lines.append(
                    "| {mb} → {ma} | {sess} | {reg} | {side} | "
                    "{wb:.1%} | {wa:.1%} | {dp:+.1f} | {nb}/{na} |".format(
                        mb=cp.month_before,
                        ma=cp.month_after,
                        sess=cp.session,
                        reg=cp.regime,
                        side=cp.side,
                        wb=cp.wr_before,
                        wa=cp.wr_after,
                        dp=cp.delta_pp,
                        nb=cp.n_before,
                        na=cp.n_after,
                    )
                )
        else:
            lines.append(
                "_No LONG-side change point with n>={n} on both sides._".format(n=min_n)
            )
        lines.append("")

        # SHORT cells with n >= 10
        lines.append(f"## SHORT cells with n >= {min_n}")
        lines.append("")
        short_rows: list[dict[str, Any]] = []
        for strat in stratified_by_inst.values():
            for k, b in strat.items():
                if k.side == "SHORT" and b.n >= min_n:
                    short_rows.append(
                        {
                            "instrument": k.instrument,
                            "month": k.month,
                            "session": k.session,
                            "regime": k.regime,
                            "n": b.n,
                            "wr": b.wr,
                            "exp_r": b.exp_r,
                        }
                    )
        if short_rows:
            short_rows.sort(
                key=lambda r: (r["instrument"], r["month"], r["session"], r["regime"])
            )
            lines.append(
                "| Instrument | Month | Session | Regime | n | WR | Exp R |"
            )
            lines.append("| --- | --- | --- | --- | --- | --- | --- |")
            for r in short_rows:
                lines.append(
                    "| {instr} | {month} | {sess} | {reg} | {n} | "
                    "{wr:.1%} | {er:+.2f} |".format(
                        instr=r["instrument"],
                        month=r["month"],
                        sess=r["session"],
                        reg=r["regime"],
                        n=r["n"],
                        wr=r["wr"],
                        er=r["exp_r"],
                    )
                )
        else:
            lines.append(f"_No SHORT cells with n >= {min_n}._")
        lines.append("")

        # H2-2026 LONG breakdown — pinpoints WHERE LONG selectivity broke.
        # H2 = 2026-03 / 2026-04 in the brief.
        lines.append("## H2-2026 LONG breakdown (Mar+Apr)")
        lines.append("")
        h2_long_rows: list[dict[str, Any]] = []
        for strat in stratified_by_inst.values():
            for k, b in strat.items():
                if k.side != "LONG":
                    continue
                if k.month not in ("2026-03", "2026-04"):
                    continue
                h2_long_rows.append(
                    {
                        "instrument": k.instrument,
                        "month": k.month,
                        "session": k.session,
                        "regime": k.regime,
                        "n": b.n,
                        "wins": b.wins,
                        "wr": b.wr,
                        "exp_r": b.exp_r,
                        "total_r": b.total_r,
                    }
                )
        if h2_long_rows:
            h2_long_rows.sort(
                key=lambda r: (
                    r["instrument"],
                    r["month"],
                    r["session"],
                    r["regime"],
                )
            )
            lines.append(
                "| Instrument | Month | Session | Regime | n | WR | Exp R | Total R |"
            )
            lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
            for r in h2_long_rows:
                lines.append(
                    "| {instr} | {month} | {sess} | {reg} | {n} | "
                    "{wr:.1%} | {er:+.2f} | {tr:+.1f} |".format(
                        instr=r["instrument"],
                        month=r["month"],
                        sess=r["session"],
                        reg=r["regime"],
                        n=r["n"],
                        wr=r["wr"],
                        er=r["exp_r"],
                        tr=r["total_r"],
                    )
                )
        else:
            lines.append("_No H2-2026 LONG cells._")
        lines.append("")

    # Coverage summary across all instruments
    lines.append("## Stratum coverage")
    lines.append("")
    total_strata = sum(c["total_strata"] for c in coverage_by_inst.values())
    total_strata_ge_min_n = sum(
        c["strata_ge_min_n"] for c in coverage_by_inst.values()
    )
    total_trades = sum(c["total_trades"] for c in coverage_by_inst.values())
    untagged_trades = sum(
        c["untagged_trades"] for c in coverage_by_inst.values()
    )
    unknown_side_trades = sum(
        c.get("unknown_side_trades", 0) for c in coverage_by_inst.values()
    )
    untagged_pct = (
        untagged_trades / total_trades * 100.0 if total_trades else 0.0
    )
    unknown_side_pct = (
        unknown_side_trades / total_trades * 100.0 if total_trades else 0.0
    )
    lines.append(f"- Total strata observed: {total_strata}")
    lines.append(f"- Strata with n >= {min_n}: {total_strata_ge_min_n}")
    lines.append(f"- Total trades: {total_trades}")
    earliest = _earliest_backfill_ts(structure_log)
    if earliest is not None:
        # Surface only the date portion (YYYY-MM-DD) — finer granularity
        # is noise here.
        earliest_date = earliest[:10]
        coverage_caption = (
            "(blind spots; the offline backfill at "
            f"`{structure_log.name}` covers H4 "
            f"regimes from {earliest_date} onward — pre-backfill trades remain UNTAGGED)"
        )
    else:
        coverage_caption = (
            "(blind spots; the offline backfill is empty or unavailable — "
            "every trade is UNTAGGED)"
        )
    lines.append(
        f"- UNTAGGED-regime fraction: {untagged_pct:.1f}% {coverage_caption}"
    )

    # 2026-only coverage — the slice the offline backfill targets directly.
    n_2026 = 0
    untagged_2026 = 0
    for strat in stratified_by_inst.values():
        for k, b in strat.items():
            if k.month.startswith("2026"):
                n_2026 += b.n
                if k.regime == "UNTAGGED":
                    untagged_2026 += b.n
    pct_2026 = (untagged_2026 / n_2026 * 100.0) if n_2026 else 0.0
    lines.append(
        f"- 2026-window UNTAGGED-regime fraction: {pct_2026:.1f}% "
        f"({untagged_2026} / {n_2026} trades)"
    )
    lines.append(
        f"- UNKNOWN-side fraction: {unknown_side_pct:.1f}% "
        "(direction missing AND entry/SL inference failed)"
    )
    lines.append("")

    # Per-instrument heatmap-friendly tables
    for instr in sorted(stratified_by_inst):
        strat = stratified_by_inst[instr]
        cov = coverage_by_inst[instr]
        lines.append(f"## {instr}")
        lines.append("")
        lines.append(
            f"- {cov['total_strata']} strata, "
            f"{cov['strata_ge_min_n']} with n>={min_n}, "
            f"{cov['total_trades']} trades, "
            f"UNTAGGED {cov['untagged_pct']:.1f}%, "
            f"UNKNOWN-side {cov.get('unknown_side_pct', 0.0):.1f}%"
        )
        lines.append("")
        rows = stratified_to_rows(strat)
        if not rows:
            lines.append("_No trades for this instrument._")
            lines.append("")
            continue
        if side_stratified:
            lines.append(
                "| Month | Session | Regime | Side | n | WR | Exp R | Total R |"
            )
            lines.append(
                "| --- | --- | --- | --- | --- | --- | --- | --- |"
            )
            for r in rows:
                lines.append(
                    "| {month} | {sess} | {reg} | {side} | {n} | {wr:.1%} | "
                    "{er:+.2f} | {tr:+.1f} |".format(
                        month=r["month"],
                        sess=r["session"],
                        reg=r["regime"],
                        side=r.get("side", "AGGREGATE"),
                        n=r["n"],
                        wr=r["wr"],
                        er=r["exp_r"],
                        tr=r["total_r"],
                    )
                )
        else:
            lines.append(
                "| Month | Session | Regime | n | WR | Exp R | Total R | L/S |"
            )
            lines.append(
                "| --- | --- | --- | --- | --- | --- | --- | --- |"
            )
            for r in rows:
                lines.append(
                    "| {month} | {sess} | {reg} | {n} | {wr:.1%} | "
                    "{er:+.2f} | {tr:+.1f} | {ln}/{sn} |".format(
                        month=r["month"],
                        sess=r["session"],
                        reg=r["regime"],
                        n=r["n"],
                        wr=r["wr"],
                        er=r["exp_r"],
                        tr=r["total_r"],
                        ln=r["long_n"],
                        sn=r["short_n"],
                    )
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
        default=Path("research/decay_diagnostic/A3_stratification_side"),
        help=(
            "Directory to write strata.jsonl + change_points.json + report.md. "
            "Default sibling of the legacy A3 output so re-running F2 does not "
            "clobber the 3-axis run."
        ),
    )
    p.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated instrument filter (default: all observed)",
    )
    p.add_argument(
        "--min-n",
        type=int,
        default=10,
        help="Minimum n on each side of a month transition for change-point detection",
    )
    p.add_argument(
        "--delta-pp-threshold",
        type=float,
        default=15.0,
        help="Minimum WR delta (in percentage points) for change-point detection",
    )
    p.add_argument(
        "--no-side-stratification",
        action="store_true",
        help=(
            "Disable the F2 4th axis (side). Output reverts to the legacy "
            "3-axis schema (instrument, month, session, regime), "
            "bit-identical to the historical strata.jsonl rows."
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
        "--no-unified-csv",
        action="store_true",
        help="Skip research/**/trades_unified.csv (debug)",
    )
    p.add_argument(
        "--structure-log",
        type=Path,
        default=None,
        help="Override path to structure_detector_divergences.jsonl",
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

    # 1. Load trades from every available source.
    all_trades: list[dict[str, Any]] = []
    if not args.no_research_slices:
        slice_trades = _load_research_slices(project_root)
        logger.info("loaded %d trades from research slices", len(slice_trades))
        all_trades.extend(slice_trades)
    if not args.no_unified_csv:
        csv_trades = _load_unified_csv(project_root)
        logger.info("loaded %d trades from unified CSV", len(csv_trades))
        all_trades.extend(csv_trades)
    if not args.no_trade_index:
        idx_trades = _load_trade_index(project_root)
        logger.info("loaded %d trades from trade index", len(idx_trades))
        all_trades.extend(idx_trades)

    all_trades = _dedupe(all_trades)
    logger.info("total trades after dedupe: %d", len(all_trades))

    # 2. Resolve config + structure log.
    kill_zones_cfg = _load_kill_zones_yaml(project_root) or DEFAULT_KILL_ZONES
    structure_log = args.structure_log or _resolve_structure_log(project_root)
    if structure_log is not None:
        logger.info("using structure log: %s", structure_log)
    else:
        logger.info(
            "no structure_detector_divergences log present — every regime "
            "will be UNTAGGED until A5 backfills"
        )

    # 3. Determine instrument list.
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    else:
        observed = sorted({t["symbol"] for t in all_trades if t.get("symbol")})
        symbols = observed
    logger.info("stratifying for: %s", ", ".join(symbols))

    # 4. Stratify per-instrument.
    side_stratified = not args.no_side_stratification
    stratified_by_inst: dict[str, StratifiedOutcomes] = {}
    coverage_by_inst: dict[str, dict[str, Any]] = {}
    for sym in symbols:
        strat = stratify(
            all_trades,
            instrument=sym,
            kill_zones_config=kill_zones_cfg,
            structure_log_path=structure_log,
            side_stratified=side_stratified,
        )
        stratified_by_inst[sym] = strat
        coverage_by_inst[sym] = coverage_summary(strat, min_n=args.min_n)

    # 5. Find change points across the union (per-instrument family
    #    correction is enforced inside find_change_points by including
    #    every (i,s,r) trio in the family count).
    union: StratifiedOutcomes = {}
    for strat in stratified_by_inst.values():
        union.update(strat)
    change_points = find_change_points(
        union,
        min_n=args.min_n,
        delta_pp_threshold=args.delta_pp_threshold,
    )

    # 6. Write outputs.
    strata_path = output_dir / "strata.jsonl"
    cp_path = output_dir / "change_points.json"
    report_path = output_dir / "report.md"

    with strata_path.open("w", encoding="utf-8") as f:
        for sym in symbols:
            for row in stratified_to_rows(stratified_by_inst[sym]):
                f.write(json.dumps(row, sort_keys=True) + "\n")

    with cp_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "min_n": args.min_n,
                "delta_pp_threshold": args.delta_pp_threshold,
                "side_stratified": side_stratified,
                "family_size": (
                    change_points[0].family_size if change_points else 0
                ),
                "change_points": [cp.to_row() for cp in change_points],
                "generated_at": datetime.now(timezone.utc).isoformat(
                    timespec="seconds"
                ),
            },
            f,
            indent=2,
            sort_keys=True,
        )

    report_md = render_report_md(
        stratified_by_inst=stratified_by_inst,
        change_points=change_points,
        coverage_by_inst=coverage_by_inst,
        min_n=args.min_n,
        structure_log=structure_log,
        side_stratified=side_stratified,
    )
    report_path.write_text(report_md, encoding="utf-8")

    # Stdout summary so the runner shows progress without scraping files.
    cov_total = sum(c["total_trades"] for c in coverage_by_inst.values())
    cov_unt = sum(c["untagged_trades"] for c in coverage_by_inst.values())
    cov_pct = (cov_unt / cov_total * 100.0) if cov_total else 0.0
    logger.info(
        "wrote %s + %s + %s | strata=%d trades=%d UNTAGGED=%.1f%% change_points=%d",
        strata_path,
        cp_path,
        report_path,
        sum(c["total_strata"] for c in coverage_by_inst.values()),
        cov_total,
        cov_pct,
        len(change_points),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
