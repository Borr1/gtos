#!/usr/bin/env python3
"""Divergence weekly sampler — pulls a stratified classification batch
from ``shadow_logs/structure_detector_divergences.jsonl`` and renders a
markdown digest for CEO to tick through.

Context
-------
The live fleet flipped to ``market_state.detector_version: v2_shadow`` on
2026-04-24 ~11:49 UTC (``4e56e8a``). Promotion to ``v2`` production
requires ≥100 manually-classified divergences with ≥80% v2-correct rate
over ≥14 days. This script produces the weekly batch the CEO classifies.

Flow (invoked from Windows Task Scheduler, once per week):

    1. Read state file ``shadow_logs/.divergence_sampling_state.json``
       for the highest ``logged_at`` already sampled.
    2. Stream the JSONL, keep rows with ``mode == "shadow"`` and
       ``logged_at > last_sampled_logged_at``.
    3. If fewer than 20 rows: write a short "insufficient sample" digest
       explaining the state and exit — no promotion math to do yet.
    4. Stratify: ~5 per instrument × prefer H1+M15 over H4+D1.
       Bearish-v2 rows are oversampled over transitional-v2 rows within a
       stratum slot (they're the novel divergence we most want to
       classify).
    5. Render markdown digest with window-context from the
       ``data/historical_2026/`` CSVs (price range, last-10-close delta,
       last BOS direction+time). One section per sampled row with four
       Classification checkboxes.
    6. Persist new ``last_sampled_logged_at`` (max of sampled batch).
    7. Leave the digest + state update on disk by default. Git staging/commit is
       explicit opt-in via ``--git`` or ``GTOS_DIVERGENCE_SAMPLER_GIT_COMMIT=1``.

Safety
------
* Observation-only. Never touches production trading paths.
* Filesystem paths are module-level constants (testable via
  ``monkeypatch.setattr(mod, "SHADOW_LOG_PATH", tmp_path / "x.jsonl")``).
* ``mode: "live_v2"`` rows are explicitly excluded — those are F3
  backtest artifacts, not production shadow observations.
* Empty ``symbol`` strings (legacy F3 sim rows) are tolerated — they
  bucket under an ``"unknown"`` stratum and generally get dropped by
  the target-count cap.

Windows task pattern
--------------------
Mirrors the ``GTOS_Watchdog`` launcher: a VBS wrapper runs
``python scripts/divergence_weekly_sample.py --no-git`` with no visible window.
See ``scripts/divergence_weekly_sampler_launcher.vbs`` + the
PowerShell installer ``scripts/install_divergence_sampler_task.ps1``.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

# ---------------------------------------------------------------------------
# Project-root importability
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.safety.runtime_halt import read_runtime_halt_state


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Module-level constants (tests monkeypatch these)
# ---------------------------------------------------------------------------

SHADOW_LOG_PATH: Path = _PROJECT_ROOT / "shadow_logs" / "structure_detector_divergences.jsonl"
STATE_PATH: Path = _PROJECT_ROOT / "shadow_logs" / ".divergence_sampling_state.json"
DIGEST_DIR: Path = _PROJECT_ROOT / "research" / "divergence_sampling"
HISTORICAL_DATA_DIR: Path = _PROJECT_ROOT / "data" / "historical_2026"
RUNTIME_HALT_CONFIG = {
    "runtime_control": {
        "enabled": True,
        "audit_log_path": "pipeline_state/runtime_control_atomic_halt_audit.jsonl",
    }
}

TARGET_SAMPLE_SIZE: int = 25
MIN_SAMPLE_THRESHOLD: int = 20  # below this, emit insufficient-sample digest

# Preferred instruments + TFs (in priority order for stratification).
PREFERRED_INSTRUMENTS: list[str] = ["XAUUSD", "USDJPY", "GBPJPY", "US30_cash", "GBPUSD"]
# H1 + M15 preferred over H4 + D1 (trading-relevant TFs).
TF_PRIORITY: dict[str, int] = {"H1": 0, "M15": 1, "H4": 2, "D1": 3}

# Window-context render: last N candles before ts.
WINDOW_CANDLES: int = 50


# ---------------------------------------------------------------------------
# State file
# ---------------------------------------------------------------------------


def load_state(path: Path = None) -> dict[str, Any]:
    """Return sampling state, defaulting to ``{"last_sampled_logged_at": None}``.

    Corrupt / missing files silently reset to the default (warn). The state
    is advisory; worst case is we re-sample a few rows, which is harmless.
    """
    p = Path(path) if path is not None else STATE_PATH
    if not p.exists():
        return {"last_sampled_logged_at": None}
    try:
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            logger.warning("State file %s is not a dict — resetting.", p)
            return {"last_sampled_logged_at": None}
        return {"last_sampled_logged_at": data.get("last_sampled_logged_at")}
    except Exception as exc:
        logger.warning("State file %s corrupt (%s) — resetting.", p, exc)
        return {"last_sampled_logged_at": None}


def save_state(state: dict[str, Any], path: Path = None) -> None:
    """Write state atomically via tmpfile + os.replace."""
    p = Path(path) if path is not None else STATE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + f".tmp.{os.getpid()}")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, sort_keys=True)
        os.replace(tmp, p)
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# JSONL reader
# ---------------------------------------------------------------------------


def _row_is_shadow(row: dict[str, Any]) -> bool:
    """Shadow-mode filter. Excludes F3 sim artifacts (mode=live_v2)."""
    return row.get("mode") == "shadow"


def _logged_at_after(row: dict[str, Any], cutoff: Optional[str]) -> bool:
    """Return True when the row's ``logged_at`` is strictly after ``cutoff``.

    String-compare works because ISO-8601 timestamps collate chronologically.
    None cutoff (first run) always returns True.
    """
    if cutoff is None:
        return True
    la = row.get("logged_at")
    if not isinstance(la, str):
        return False
    return la > cutoff


def load_shadow_rows(
    path: Path = None,
    after_logged_at: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Stream the JSONL, keep ``mode=shadow`` rows after the cutoff.

    Malformed lines (non-JSON, missing mode/logged_at) are silently
    dropped with a warning — we do not want one bad row to break the
    weekly run. The shadow logger is best-effort on the live side, so
    the sampler should be tolerant too.
    """
    p = Path(path) if path is not None else SHADOW_LOG_PATH
    if not p.exists():
        logger.info("Shadow log %s does not exist yet — zero rows.", p)
        return []
    out: list[dict[str, Any]] = []
    malformed = 0
    with open(p, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if not isinstance(row, dict):
                malformed += 1
                continue
            if not _row_is_shadow(row):
                continue
            if not _logged_at_after(row, after_logged_at):
                continue
            out.append(row)
    if malformed:
        logger.warning("Skipped %d malformed shadow-log lines.", malformed)
    logger.info(
        "Loaded %d shadow rows (mode=shadow, after=%s) from %s",
        len(out), after_logged_at, p,
    )
    return out


# ---------------------------------------------------------------------------
# Stratified sampling
# ---------------------------------------------------------------------------


def _stratum_key(row: dict[str, Any]) -> tuple[str, str]:
    """Return (symbol, timeframe). Empty symbol → "unknown"."""
    sym = row.get("symbol") or "unknown"
    tf = row.get("timeframe") or "unknown"
    return (str(sym), str(tf))


def _row_priority(row: dict[str, Any]) -> tuple[int, int]:
    """Within-stratum priority (lower = picked first).

    * Bearish v2_direction is preferred (novel divergence, high info value).
    * Higher v2_score magnitude (further from dead zone) is preferred
      because those are the "cleanest" classifications.
    """
    v2_dir = row.get("v2_direction", "")
    dir_priority = 0 if v2_dir == "bearish" else 1 if v2_dir == "transitional" else 2
    score_mag = abs(int(row.get("v2_score", 0)))
    # Bigger score_mag first → negate for ascending sort.
    return (dir_priority, -score_mag)


def stratified_sample(
    rows: list[dict[str, Any]],
    target: int = TARGET_SAMPLE_SIZE,
) -> list[dict[str, Any]]:
    """Balanced sample across (symbol, timeframe) strata.

    Algorithm: group rows by (symbol, tf); within each stratum sort by
    ``_row_priority`` (bearish-v2 first, then higher-magnitude scores).
    Round-robin across strata in priority order until ``target`` rows are
    selected or all strata are empty.

    Stratum ordering for round-robin (first pass preferred):
    1. ``(sym, tf)`` where sym in ``PREFERRED_INSTRUMENTS`` and tf in
       ``TF_PRIORITY`` → sorted by (sym_idx, tf_idx).
    2. Anything else ("unknown" symbol, exotic TFs) → appended.

    Empty strata are silently skipped. If total rows < target, we return
    every row — no padding, no crash.
    """
    if not rows:
        return []
    if target <= 0:
        return []

    # Bucket rows by stratum.
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        buckets[_stratum_key(r)].append(r)

    # Sort each bucket by priority (stable within equal keys).
    for key in buckets:
        buckets[key].sort(key=_row_priority)

    # Build stratum order.
    def _strat_order(key: tuple[str, str]) -> tuple[int, int, int, str, str]:
        sym, tf = key
        sym_idx = (
            PREFERRED_INSTRUMENTS.index(sym)
            if sym in PREFERRED_INSTRUMENTS
            else len(PREFERRED_INSTRUMENTS)
        )
        tf_idx = TF_PRIORITY.get(tf, len(TF_PRIORITY))
        # Primary: preferred sym; secondary: preferred tf; rest deterministic.
        return (sym_idx, tf_idx, 0, sym, tf)

    strata = sorted(buckets.keys(), key=_strat_order)

    # Round-robin draw.
    picked: list[dict[str, Any]] = []
    while len(picked) < target:
        progressed = False
        for key in strata:
            if len(picked) >= target:
                break
            bucket = buckets[key]
            if bucket:
                picked.append(bucket.pop(0))
                progressed = True
        if not progressed:
            break  # all strata empty

    return picked


# ---------------------------------------------------------------------------
# Window context (historical CSV)
# ---------------------------------------------------------------------------


def _parse_csv_time(s: str) -> Optional[datetime]:
    """Parse a CSV timestamp to UTC datetime; accept a few common formats."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _parse_iso_utc(s: str) -> Optional[datetime]:
    """Parse an ISO-8601 UTC timestamp (with Z or offset)."""
    if not isinstance(s, str):
        return None
    try:
        # Normalise trailing Z to +00:00 for fromisoformat.
        s2 = s.replace("Z", "+00:00") if s.endswith("Z") else s
        dt = datetime.fromisoformat(s2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def load_candle_window(
    symbol: str,
    timeframe: str,
    before_ts: str,
    n_candles: int = WINDOW_CANDLES,
    data_dir: Path = None,
) -> list[dict[str, Any]]:
    """Load up to ``n_candles`` candles strictly BEFORE ``before_ts``.

    Returns [] if the CSV is missing or the timestamp isn't parseable.
    Candles are dicts with float open/high/low/close + str time.
    """
    dd = Path(data_dir) if data_dir is not None else HISTORICAL_DATA_DIR
    csv_path = dd / f"{symbol}_{timeframe}.csv"
    if not csv_path.exists():
        return []
    target = _parse_iso_utc(before_ts)
    if target is None:
        return []

    out: list[dict[str, Any]] = []
    try:
        with open(csv_path, "r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                t = _parse_csv_time(row.get("time", ""))
                if t is None:
                    continue
                if t >= target:
                    continue
                try:
                    out.append({
                        "time": row["time"],
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                    })
                except (KeyError, ValueError, TypeError):
                    continue
    except Exception as exc:
        logger.warning("Failed reading %s: %s", csv_path, exc)
        return []

    if not out:
        return []
    return out[-n_candles:]


def window_summary_lines(
    symbol: str,
    timeframe: str,
    before_ts: str,
    n_candles: int = WINDOW_CANDLES,
    data_dir: Path = None,
) -> list[str]:
    """Render a short window-context block as markdown-indent bullets.

    Lines (all prefixed ``- ``):
      * Price range: min_close → max_close (close LAST)
      * Last 10 candles: close delta X.XX (bullish/bearish tilt)
      * Last BOS (best-effort via ``detect_structure_breaks``); skipped
        if primitives unavailable or no BOS in window.

    Zero-candle / unparseable window → single "- No window context
    available (missing CSV or parse failure)" line.
    """
    candles = load_candle_window(symbol, timeframe, before_ts, n_candles, data_dir)
    if not candles:
        return ["- No window context available (missing CSV or parse failure)"]

    closes = [c["close"] for c in candles]
    lows = [c["low"] for c in candles]
    highs = [c["high"] for c in candles]
    price_min = min(lows)
    price_max = max(highs)
    last_close = closes[-1]
    t_first = candles[0]["time"]
    t_last = candles[-1]["time"]

    # Last 10 candles close delta.
    delta10: Optional[float] = None
    if len(closes) >= 11:
        delta10 = closes[-1] - closes[-11]
    elif len(closes) >= 2:
        delta10 = closes[-1] - closes[0]
    tilt = ""
    if delta10 is not None:
        if delta10 > 0:
            tilt = " (bullish tilt)"
        elif delta10 < 0:
            tilt = " (bearish tilt)"
        else:
            tilt = " (flat)"

    # Precision: XAUUSD/US30 2dp; FX pairs 5dp (3dp for JPY pairs).
    if symbol.endswith("JPY") or symbol.endswith("JPY_CROSS"):
        fmt = "{:.3f}"
    elif symbol in ("XAUUSD", "US30_cash"):
        fmt = "{:.2f}"
    else:
        fmt = "{:.5f}"

    lines = [
        f"**Window context** ({len(candles)} candles, {t_first} → {t_last}):",
        f"- Price range: {fmt.format(price_min)} → {fmt.format(price_max)} (close {fmt.format(last_close)})",
    ]
    if delta10 is not None:
        lines.append(f"- Last 10 candles: close delta {delta10:+.4f}{tilt}")
    else:
        lines.append(f"- Last 10 candles: insufficient history{tilt}")

    # Best-effort BOS via market_state primitives.
    bos_line = _try_last_bos_line(candles, fmt)
    if bos_line is not None:
        lines.append(bos_line)

    return lines


def _try_last_bos_line(candles: list[dict[str, Any]], fmt: str) -> Optional[str]:
    """Return a ``- Last BOS: ...`` line or None if primitives unavailable.

    Defensive: if ``detect_swings`` / ``detect_structure_breaks`` fail or
    produce no BOS event, return None — window context is still useful
    without this line.
    """
    try:
        from src.components.market_state import detect_structure_breaks, detect_swings, identify_structure
    except Exception:
        return None

    try:
        swings = detect_swings(candles)
        if not swings:
            return None
        structure = identify_structure(swings)
        events = detect_structure_breaks(candles, swings, structure)
    except Exception:
        return None

    if not events:
        return None

    # Find the latest BOS event.
    bos_events = [e for e in events if getattr(e, "event_type", None) == "BOS"]
    if not bos_events:
        return None
    latest = bos_events[-1]
    direction = getattr(latest, "direction", "?")
    ev_time = getattr(latest, "event_time", "?")
    broken_price = getattr(latest, "broken_swing_price", None)
    try:
        broken_str = fmt.format(float(broken_price)) if broken_price is not None else "?"
    except (TypeError, ValueError):
        broken_str = "?"
    return f"- Last BOS: {direction} @ {ev_time} (broke {broken_str})"


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


def render_sample_section(idx: int, row: dict[str, Any], data_dir: Path = None) -> str:
    """Render a single sample section. Format MUST match the aggregator's
    parser — any change here requires an update to
    ``scripts/divergence_classification_summary.py``.
    """
    symbol = row.get("symbol") or "unknown"
    tf = row.get("timeframe") or "unknown"
    ts_raw = row.get("ts") or ""
    # Friendly date: "2026-04-24 14:15 UTC".
    dt = _parse_iso_utc(ts_raw)
    if dt is not None:
        ts_str = dt.strftime("%Y-%m-%d %H:%M UTC")
    else:
        ts_str = ts_raw or "?"

    v1 = row.get("v1_direction", "?")
    v2 = row.get("v2_direction", "?")
    score = row.get("v2_score", "?")
    dead_zone = row.get("v2_dead_zone", "?")
    counts = row.get("counts", {}) or {}
    hh = counts.get("hh", "?")
    hl = counts.get("hl", "?")
    lh = counts.get("lh", "?")
    ll = counts.get("ll", "?")
    production = row.get("production_label", "?")

    window_lines = window_summary_lines(symbol, tf, ts_raw, WINDOW_CANDLES, data_dir)
    window_block = "\n".join(window_lines)

    return (
        f"## Sample {idx} — {symbol} {tf} {ts_str}\n"
        "\n"
        f"- **v1 direction:** {v1} | **v2 direction:** {v2}\n"
        f"- **score:** {score} | **dead_zone:** {dead_zone} | "
        f"**counts:** hh={hh} hl={hl} lh={lh} ll={ll}\n"
        f"- **production_label:** {production} (v1 drives in v2_shadow mode)\n"
        "\n"
        f"{window_block}\n"
        "\n"
        "**Classification** (check ONE):\n"
        "- [ ] v1 correct (bullish was right)\n"
        "- [ ] v2 correct (bearish was right)\n"
        "- [ ] both wrong (should have been transitional/ranging)\n"
        "- [ ] ambiguous (genuinely could go either way)\n"
        "\n"
        "---\n"
    )


def render_digest(
    sample: list[dict[str, Any]],
    week_label: str,
    data_dir: Path = None,
) -> str:
    """Render the full weekly digest markdown."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = (
        f"# Divergence Sampling — week {week_label}\n"
        "\n"
        f"- **Generated:** {now}\n"
        f"- **Sample size:** {len(sample)} divergences\n"
        "- **Task:** check ONE classification box per sample, then commit "
        "the file. Run `python scripts/divergence_classification_summary.py` "
        "to aggregate progress toward the promotion gate.\n"
        "\n"
        "---\n"
        "\n"
    )
    sections = [
        render_sample_section(i + 1, row, data_dir) for i, row in enumerate(sample)
    ]
    return header + "\n".join(sections)


def render_insufficient_digest(
    rows: list[dict[str, Any]],
    week_label: str,
) -> str:
    """Render a short "insufficient sample" page — no classification boxes.

    This file is still committed so the CEO sees "no batch this week" in
    ``git status`` without having to check the task scheduler log.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    n = len(rows)
    return (
        f"# Divergence Sampling — week {week_label} (insufficient sample)\n"
        "\n"
        f"- **Generated:** {now}\n"
        f"- **Available shadow rows since last sample:** {n}\n"
        f"- **Required threshold:** {MIN_SAMPLE_THRESHOLD}\n"
        "\n"
        "No classification batch produced this week. The shadow log has not "
        "accumulated enough `mode=shadow` rows since the last sampling run.\n"
        "\n"
        "Possible causes:\n"
        "\n"
        "- Live fleet is in dead zone / weekend — divergences only emit during trading.\n"
        "- Live fleet was restarted and the state file hasn't advanced because no new divergences logged.\n"
        "- `detector_version` was flipped back to `v1` — dual-compute disabled.\n"
        "\n"
        "The sampler will retry next Monday. If multiple weeks pass with zero rows, "
        "check `config/agent_config.yaml` → `market_state.detector_version` and "
        "the orchestrator log for dual-compute errors.\n"
    )


# ---------------------------------------------------------------------------
# Output + commit
# ---------------------------------------------------------------------------


def current_iso_week(today: Optional[date] = None) -> str:
    """Return ``YYYY-WW`` for ``today`` (defaults to UTC today)."""
    d = today or datetime.now(timezone.utc).date()
    iso = d.isocalendar()
    return f"{iso.year:04d}-{iso.week:02d}"


def write_digest(
    content: str,
    week_label: str,
    digest_dir: Path = None,
) -> Path:
    """Write ``content`` to ``digest_dir/week_<label>.md`` and return the path."""
    dd = Path(digest_dir) if digest_dir is not None else DIGEST_DIR
    dd.mkdir(parents=True, exist_ok=True)
    path = dd / f"week_{week_label}.md"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def _max_logged_at(sample: list[dict[str, Any]]) -> Optional[str]:
    """Return the max ``logged_at`` in ``sample``, or None if empty."""
    stamps = [r.get("logged_at") for r in sample if isinstance(r.get("logged_at"), str)]
    if not stamps:
        return None
    return max(stamps)


def _git_commit(paths: list[Path], message: str, cwd: Path = None) -> bool:
    """Best-effort git add + commit. Returns True on success, False otherwise.

    Never raises — a commit failure (e.g., running outside a git repo, or
    pre-commit hook rejection) must not prevent the digest from being
    available on disk. Logs a warning.
    """
    if not paths:
        return False
    root = Path(cwd) if cwd is not None else _PROJECT_ROOT
    try:
        subprocess.run(
            ["git", "add", "--"] + [str(p) for p in paths],
            cwd=str(root), check=True, capture_output=True, text=True,
        )
        # If nothing staged, skip the commit (e.g., file content unchanged).
        status = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=str(root), capture_output=True, text=True,
        )
        if status.returncode == 0:
            logger.info("Nothing staged after git add — skipping commit.")
            return False
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=str(root), check=True, capture_output=True, text=True,
        )
        logger.info("Committed: %s", message)
        return True
    except FileNotFoundError:
        logger.warning("git binary unavailable — skipping commit.")
        return False
    except subprocess.CalledProcessError as exc:
        logger.warning("git commit failed (non-fatal): %s", exc.stderr or exc)
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run(
    *,
    target_sample_size: int = TARGET_SAMPLE_SIZE,
    skip_git_commit: bool = True,
    week_label: Optional[str] = None,
) -> int:
    """Execute a single weekly sampling run. Returns exit code."""
    state = load_state()
    cutoff = state.get("last_sampled_logged_at")
    logger.info("Loaded state: last_sampled_logged_at=%s", cutoff)

    rows = load_shadow_rows(after_logged_at=cutoff)
    week = week_label or current_iso_week()

    committed_paths: list[Path] = []

    if len(rows) < MIN_SAMPLE_THRESHOLD:
        logger.info(
            "Only %d shadow rows available (< %d threshold) — writing insufficient-sample digest.",
            len(rows), MIN_SAMPLE_THRESHOLD,
        )
        digest = render_insufficient_digest(rows, week)
        path = write_digest(digest, week)
        committed_paths.append(path)
        # Do NOT advance state — we haven't sampled anything.
        if not skip_git_commit:
            _git_commit(
                committed_paths,
                f"sampling(divergence): week {week} insufficient sample — {len(rows)} rows",
            )
        return 0

    sample = stratified_sample(rows, target=target_sample_size)
    logger.info(
        "Selected %d rows from %d available via stratified_sample().",
        len(sample), len(rows),
    )

    digest = render_digest(sample, week)
    path = write_digest(digest, week)
    committed_paths.append(path)

    # Advance state to the max logged_at of the SAMPLED batch (not the
    # full available pool) — unsampled rows within this pool remain
    # eligible next week if they're still unclassified. Sampled rows
    # are effectively burned even if not in the final batch... wait,
    # that's wrong. Think again.
    #
    # Correct semantics: we advance cutoff past the max logged_at in
    # the full loaded pool. That's because any row with
    # logged_at <= max_loaded has either been sampled (and is in this
    # week's digest) or was rejected by the stratification (we don't
    # want to re-sample it endlessly). If we only advanced to the
    # sampled max, unsampled rows would keep being reconsidered every
    # week — mostly pointless (they got rejected for a reason: stratum
    # was already full) and the state file would barely move.
    #
    # Tradeoff: rows that missed the cut stay unclassified forever.
    # That's fine — with 5 instruments × 4 TFs × 25/week we'd sample
    # all strata eventually, and 100 classifications across ≥14 days
    # is the gate, not 100% coverage.
    max_loaded = _max_logged_at(rows)
    if max_loaded:
        state["last_sampled_logged_at"] = max_loaded
        save_state(state)
        committed_paths.append(STATE_PATH)
        logger.info("State advanced: last_sampled_logged_at=%s", max_loaded)

    if not skip_git_commit:
        _git_commit(
            committed_paths,
            f"sampling(divergence): week {week} digest — {len(sample)} divergences for classification",
        )

    return 0


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Weekly divergence sampler — pulls a stratified classification batch.",
    )
    p.add_argument(
        "--target-size", type=int, default=TARGET_SAMPLE_SIZE,
        help=f"Target sample size (default: {TARGET_SAMPLE_SIZE}).",
    )
    p.add_argument(
        "--no-git", action="store_true",
        help=(
            "Skip the git add + commit step. This is the default; kept for "
            "scheduled wrappers and old manual commands."
        ),
    )
    p.add_argument(
        "--git", action="store_true",
        help=(
            "Opt in to git add + commit. Default is no git mutation to avoid "
            "stale git-lfs filter-process helpers in large worktrees."
        ),
    )
    p.add_argument(
        "--week", type=str, default=None,
        help="Override the ISO week label (YYYY-WW). Default: current UTC week.",
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    # Force UTF-8 on stdout/stderr so non-ASCII chars in log messages
    # (→, —, ≥, bullet points) don't crash the process on Windows cp1252
    # consoles. File writes already use explicit encoding="utf-8".
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass
    halt_snapshot = read_runtime_halt_state(
        RUNTIME_HALT_CONFIG,
        repo_root=_PROJECT_ROOT,
    )
    if halt_snapshot.active:
        logger.info(
            "%s active; divergence weekly sampler exiting.",
            halt_snapshot.status,
        )
        return 0
    git_opt_in = args.git or os.getenv("GTOS_DIVERGENCE_SAMPLER_GIT_COMMIT") in {
        "1",
        "true",
        "TRUE",
        "yes",
        "YES",
        "on",
        "ON",
    }
    return run(
        target_sample_size=args.target_size,
        skip_git_commit=args.no_git or not git_opt_in,
        week_label=args.week,
    )


if __name__ == "__main__":
    sys.exit(main())
