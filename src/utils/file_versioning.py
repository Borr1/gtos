"""File versioning utility — timestamped filenames, no overwrites.

Usage:
    from src.utils.file_versioning import get_versioned_path

    path = get_versioned_path("knowledge_base_backtest/analysis", "replay_blitz_report", ".md")
    # → "knowledge_base_backtest/analysis/replay_blitz_report_0_1730.md"
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def get_versioned_path(
    base_dir: str | Path,
    name: str,
    ext: str = ".md",
    *,
    timestamp: datetime | None = None,
) -> Path:
    """Return a timestamped file path guaranteed not to overwrite.

    Format: ``{base_dir}/{name}_{YYYYMMDD_HHMM}{ext}``

    If the path already exists, appends ``_2``, ``_3``, etc.

    Parameters
    ----------
    base_dir : path to the output directory (created if missing)
    name : base filename without extension
    ext : file extension including dot (default ``.md``)
    timestamp : override for deterministic tests (default: now UTC)
    """
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)

    ts = timestamp or datetime.now(timezone.utc)
    ts_str = ts.strftime("%Y%m%d_%H%M")

    candidate = base / f"{name}_{ts_str}{ext}"
    if not candidate.exists():
        return candidate

    # Collision: append incrementing suffix
    for i in range(2, 1000):
        candidate = base / f"{name}_{ts_str}_{i}{ext}"
        if not candidate.exists():
            return candidate

    raise RuntimeError(f"Could not find unique path for {name} in {base_dir}")
