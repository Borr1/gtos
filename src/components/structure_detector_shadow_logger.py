"""Structure detector shadow logger (F2.3) — observation-only.

Logs every divergence between the production ``identify_structure`` (v1) and
the candidate ``identify_structure_v2`` (ADR-004 Option D net-score
classifier) at M15-candle-close cadence across every timeframe (D1, H4,
H1, M15). v1 remains the production path in shadow mode; v2 is computed
in parallel and its label + score metadata are logged when the two
disagree.

This logger writes a row **only on divergence** — agreement cases are the
overwhelming majority on realistic production windows (~99.8% of V1 H1
snapshots are bullish under v1 per ADR-004 §3) and would dominate the log
without adding signal. The aggregate divergence rate, per-instrument label
distribution, and per-TF split are reconstructible from the JSONL.

Design references
-----------------
* ADR-004 §7.1 — shadow-mode requirements (row every M15 candle; v1 drives
  production; v2 log-only; CEO approval gate for cutover).
* ``proximity_shadow_logger.py`` / ``be_shadow_logger.py`` — pattern for
  JSONL-based observation-only loggers with tmp_path-safe ``log_path``
  parameterisation and try/except crash-safety around the write.

Promotion criteria (copied from ADR-004 §7.3 + task brief; not enforced
here — this module only produces the data)::

    * >= 7 days shadow running
    * >= 100 sampled divergences manually classified
    * v2-correct rate >= 80% on sampled divergences
    * F3 shadow-replay backtest criteria met (expectancy preservation or
      improvement)

    THEN flip ``market_state.detector_version: v2`` and restart.

The analysis script that turns this log into the per-instrument /
per-timeframe divergence summary lives separately
(``scripts/structure_v2_divergence_report.py``, to be added alongside F3).
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.models.market_state_models import StructureAnalysis
from src.utils.jsonl_rotation import RotatingJsonlWriter

logger = logging.getLogger(__name__)

SHADOW_LOG_PATH = "shadow_logs/structure_detector_divergences.jsonl"

# Defaults mirror config/agent_config.yaml (shadow_loggers.structure_detector.rotation).
# These are fallbacks when no config dict is passed; the production caller
# (``orchestrator``) wires the configured values through.
_DEFAULT_ROTATION_SIZE_MB: int = 50
_DEFAULT_RETENTION_DAYS: int = 14
_DEFAULT_ARCHIVE_DIR: str = "research/archive/structure_detector_divergences"

# Module-level singletons keyed by ``log_path`` so concurrent callers (one
# per orchestrator process) all share the same RotatingJsonlWriter when they
# point at the same default sink. Each writer carries its own RLock — see
# ``src/utils/jsonl_rotation.py``.
_WRITERS: dict[str, RotatingJsonlWriter] = {}
_WRITERS_LOCK = threading.Lock()


def _get_writer(
    log_path: str,
    *,
    size_mb: int = _DEFAULT_ROTATION_SIZE_MB,
    retention_days: int = _DEFAULT_RETENTION_DAYS,
    archive_dir: str = _DEFAULT_ARCHIVE_DIR,
) -> RotatingJsonlWriter:
    """Return a process-wide singleton writer for ``log_path``.

    The cache key is the resolved ``log_path`` string so a test that injects
    a tmp_path-derived sink gets a fresh writer per ``tmp_path`` invocation
    rather than reusing the production singleton.
    """
    with _WRITERS_LOCK:
        existing = _WRITERS.get(log_path)
        if existing is None:
            existing = RotatingJsonlWriter(
                base_path=log_path,
                size_mb=size_mb,
                retention_days=retention_days,
                archive_dir=archive_dir,
            )
            _WRITERS[log_path] = existing
        return existing


def _reset_writers_for_tests() -> None:
    """Drop the cached writers — invoked by test fixtures that swap log_path."""
    with _WRITERS_LOCK:
        _WRITERS.clear()


def configure_rotation_from_config(config: dict | None) -> None:
    """Apply ``shadow_loggers.structure_detector.rotation`` overrides.

    Reads the optional rotation block::

        shadow_loggers:
          structure_detector:
            rotation:
              size_mb: 50
              retention_days: 14
              archive_dir: "research/archive/structure_detector_divergences"

    and overrides the module-level defaults. Must be called BEFORE the
    first ``log_structure_divergence`` call to take effect — typically
    once at orchestrator startup. Missing / partial blocks fall back to
    module defaults; an entirely missing block is a no-op (defaults stay).

    A side effect: drops the writer cache so the next ``_get_writer`` call
    picks up the new defaults.
    """
    global _DEFAULT_ROTATION_SIZE_MB, _DEFAULT_RETENTION_DAYS, _DEFAULT_ARCHIVE_DIR
    if not isinstance(config, dict):
        return
    sl_cfg = config.get("shadow_loggers")
    if not isinstance(sl_cfg, dict):
        return
    sd_cfg = sl_cfg.get("structure_detector")
    if not isinstance(sd_cfg, dict):
        return
    rot_cfg = sd_cfg.get("rotation")
    if not isinstance(rot_cfg, dict):
        return
    if "size_mb" in rot_cfg:
        try:
            _DEFAULT_ROTATION_SIZE_MB = int(rot_cfg["size_mb"])
        except (TypeError, ValueError):
            logger.warning(
                "structure_detector_shadow_logger: invalid size_mb=%r; keeping default",
                rot_cfg["size_mb"],
            )
    if "retention_days" in rot_cfg:
        try:
            _DEFAULT_RETENTION_DAYS = int(rot_cfg["retention_days"])
        except (TypeError, ValueError):
            logger.warning(
                "structure_detector_shadow_logger: invalid retention_days=%r; keeping default",
                rot_cfg["retention_days"],
            )
    if "archive_dir" in rot_cfg:
        archive_dir = rot_cfg["archive_dir"]
        if isinstance(archive_dir, str) and archive_dir:
            _DEFAULT_ARCHIVE_DIR = archive_dir
    _reset_writers_for_tests()


# ---------------------------------------------------------------------------
# Mode helpers
# ---------------------------------------------------------------------------

_VALID_MODES = ("v1", "v2_shadow", "v2")


def resolve_detector_mode(config: dict | None) -> str:
    """Return the active detector mode from ``config`` (default ``"v1"``).

    Invalid / missing config defaults to ``"v1"`` — the production path is
    preserved under any config shape. An explicit unknown value is logged
    once at ``WARNING`` and downgraded to ``"v1"``; the logger does not
    want to fail a production candle because of a typo in ``agent_config.yaml``.
    """
    if not isinstance(config, dict):
        return "v1"
    ms_cfg = config.get("market_state")
    if not isinstance(ms_cfg, dict):
        return "v1"
    mode = ms_cfg.get("detector_version", "v1")
    if mode not in _VALID_MODES:
        logger.warning(
            "STRUCTURE_DETECTOR: unknown detector_version=%r; falling back to 'v1'. "
            "Valid values: %s",
            mode,
            _VALID_MODES,
        )
        return "v1"
    return mode


def is_dual_compute_mode(mode: str) -> bool:
    """True when the mode runs both v1 and v2 in parallel.

    Only ``"v1"`` is single-compute (v2 skipped). ``"v2_shadow"`` computes
    both but v1 drives production. ``"v2"`` computes both but v2 drives
    production — the inverse of shadow, used as a rollback-sanity window
    after flipping to v2 so we still log any late-surfacing divergences.
    """
    return mode in ("v2_shadow", "v2")


def pick_production_label(
    mode: str,
    v1_label: StructureAnalysis,
    v2_label: Optional[StructureAnalysis],
) -> StructureAnalysis:
    """Return the label that drives the downstream pipeline.

    * ``v1`` or ``v2_shadow`` -> v1 (v1 is the production path).
    * ``v2`` -> v2 if non-None, otherwise v1 (fail-open to the known-working
      path if v2 computation somehow skipped).
    """
    if mode == "v2" and v2_label is not None:
        return v2_label
    return v1_label


# ---------------------------------------------------------------------------
# Divergence logger
# ---------------------------------------------------------------------------


def _counts_dict(label: StructureAnalysis) -> dict[str, int]:
    """Return the hh/hl/lh/ll counts from a StructureAnalysis.

    The StructureAnalysis pydantic model uses default 0 for each count
    field (same for v1 and v2 labels), so this is always well-defined.
    """
    return {
        "hh": int(label.hh_count or 0),
        "hl": int(label.hl_count or 0),
        "lh": int(label.lh_count or 0),
        "ll": int(label.ll_count or 0),
    }


def compute_v2_score_metadata(v2_label: StructureAnalysis) -> dict[str, int]:
    """Reconstruct the (score, dead_zone) tuple from v2 counts.

    Mirrors the arithmetic in ``identify_structure_v2`` exactly so the
    log row carries enough information to re-derive the classification
    decision without re-running detection. ``min_swings`` is recovered
    from ``max(hh+lh, hl+ll)`` — the number of transitions on each side.
    """
    hh = int(v2_label.hh_count or 0)
    hl = int(v2_label.hl_count or 0)
    lh = int(v2_label.lh_count or 0)
    ll = int(v2_label.ll_count or 0)
    score = (hh + hl) - (lh + ll)
    # Mirrors identify_structure_v2: min_swings = min(len(highs)-1, len(lows)-1).
    # With count decomposition: hh + lh == len(highs) - 1 (when no NaN-induced
    # misses) and hl + ll == len(lows) - 1. Take the min.
    high_transitions = hh + lh
    low_transitions = hl + ll
    min_swings = min(high_transitions, low_transitions)
    dead_zone = max(2, min_swings // 4)
    return {"score": score, "dead_zone": dead_zone}


def build_divergence_row(
    *,
    symbol: str,
    timeframe: str,
    v1_label: StructureAnalysis,
    v2_label: StructureAnalysis,
    detector_version_config: str,
    production_label: StructureAnalysis,
    candle_time: str,
    logged_at: Optional[str] = None,
) -> dict[str, Any]:
    """Assemble the JSONL row for a v1/v2 divergence.

    All inputs are required except ``logged_at`` which defaults to
    ``datetime.now(timezone.utc)`` in ISO-8601. ``candle_time`` is the
    M15 candle close UTC timestamp (what the live pipeline stamps into
    ``raw_data["timestamp_utc"]``).

    Schema::

        {
          "ts": "2026-04-24T14:15:00Z",           # candle close (UTC)
          "logged_at": "2026-04-24T14:15:02Z",    # when the row was written
          "symbol": "XAUUSD",
          "timeframe": "H1",
          "v1_direction": "bullish",
          "v2_direction": "transitional",
          "v2_score": -4,
          "v2_dead_zone": 8,
          "counts": {"hh": 12, "hl": 10, "lh": 15, "ll": 11},
          "detector_version_config": "v2_shadow",
          "mode": "shadow",
          "production_label": "bullish"
        }

    The ``mode`` field collapses the ``detector_version_config`` value to
    ``"shadow"`` when v1 drives production (``v1`` or ``v2_shadow``) and
    ``"live_v2"`` when v2 drives production (``v2``). This is the label
    an operator wants at a glance; the full config string is preserved
    for precise replay reconstruction.
    """
    if logged_at is None:
        logged_at = datetime.now(timezone.utc).isoformat()
    mode_field = "live_v2" if detector_version_config == "v2" else "shadow"
    return {
        "ts": candle_time,
        "logged_at": logged_at,
        "symbol": symbol,
        "timeframe": timeframe,
        "v1_direction": v1_label.direction,
        "v2_direction": v2_label.direction,
        "counts": _counts_dict(v2_label),
        **compute_v2_score_metadata(v2_label),
        "detector_version_config": detector_version_config,
        "mode": mode_field,
        "production_label": production_label.direction,
    }


# Rename the v2 score-metadata keys when the row is assembled so the
# JSON keys match the task brief ("v2_score", "v2_dead_zone") while the
# helper still returns simple ("score", "dead_zone") tuple-like dict for
# unit-test readability.
def _finalize_row(row: dict[str, Any]) -> dict[str, Any]:
    """Rename v2 metadata keys to the stable public schema."""
    out = dict(row)
    if "score" in out:
        out["v2_score"] = out.pop("score")
    if "dead_zone" in out:
        out["v2_dead_zone"] = out.pop("dead_zone")
    return out


def log_structure_divergence(
    *,
    symbol: str,
    timeframe: str,
    v1_label: StructureAnalysis,
    v2_label: StructureAnalysis,
    detector_version_config: str,
    production_label: StructureAnalysis,
    candle_time: str,
    log_path: str = SHADOW_LOG_PATH,
    logged_at: Optional[str] = None,
) -> None:
    """Append a divergence row to the JSONL log.

    Crash-safety: every IO operation is wrapped in try/except; any
    failure logs a WARNING and returns — the caller's production path
    must continue regardless. This is an observation-only side channel.

    Intended call pattern (from ``_build_timeframe_state``)::

        if v1_label.direction != v2_label.direction:
            log_structure_divergence(
                symbol=symbol, timeframe=tf, ...
            )

    Skipping the call when ``v1 == v2`` is the caller's responsibility —
    this function will happily write an "agreement" row if asked to. Keeps
    the logger dumb so the dual-compute wrapper can decide what counts as
    interesting.
    """
    try:
        row = build_divergence_row(
            symbol=symbol,
            timeframe=timeframe,
            v1_label=v1_label,
            v2_label=v2_label,
            detector_version_config=detector_version_config,
            production_label=production_label,
            candle_time=candle_time,
            logged_at=logged_at,
        )
        row = _finalize_row(row)
        # Route through RotatingJsonlWriter so the shadow log self-rotates
        # (50 MB / UTC-midnight whichever first) + retains 14 daily archives.
        # See src/utils/jsonl_rotation.py for the policy.
        writer = _get_writer(log_path)
        writer.write(row)
        logger.info(
            "STRUCTURE_DIVERGENCE: symbol=%s tf=%s v1=%s v2=%s score=%d dead_zone=%d",
            symbol,
            timeframe,
            v1_label.direction,
            v2_label.direction,
            row["v2_score"],
            row["v2_dead_zone"],
        )
    except Exception as e:  # pragma: no cover — defensive; unit-tested
        # Never allow a logging failure to break the production v1 path.
        logger.warning(
            "STRUCTURE_DIVERGENCE: failed to write shadow log (non-blocking): %s",
            e,
        )
