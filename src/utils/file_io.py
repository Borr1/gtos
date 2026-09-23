"""Atomic file I/O utilities for pipeline state persistence."""

from __future__ import annotations

import json
import os
import random
import time
from datetime import date, datetime
from pathlib import Path
from typing import Union

import yaml


KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge_base"


def _json_default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def atomic_write(filepath: Union[str, Path], data: dict, max_retries: int = 3) -> None:
    """Write data to file atomically using temp file + os.replace().

    Writes JSON or YAML based on file extension.
    Retries on PermissionError (Windows file lock contention between processes).
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    # Use PID in tmp name to avoid cross-process collisions
    tmp_path = filepath.with_suffix(f".{os.getpid()}.tmp")
    for attempt in range(max_retries):
        try:
            with open(tmp_path, "w") as f:
                if filepath.suffix in (".yaml", ".yml"):
                    yaml.dump(data, f, default_flow_style=False)
                else:
                    json.dump(data, f, indent=2, default=_json_default)
            os.replace(tmp_path, filepath)
            return
        except PermissionError:
            if attempt < max_retries - 1:
                time.sleep(0.1 + random.random() * 0.3)
            else:
                # Clean up tmp on final failure
                try:
                    tmp_path.unlink(missing_ok=True)
                except OSError:
                    pass
                raise
        except Exception:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise


def load_json(filepath: Union[str, Path]) -> dict:
    """Load and return parsed JSON. Returns empty dict if file doesn't exist."""
    filepath = Path(filepath)
    if not filepath.exists():
        return {}
    with open(filepath, "r") as f:
        return json.load(f)


def load_yaml(filepath: Union[str, Path]) -> dict:
    """Load and return parsed YAML. Returns empty dict if file doesn't exist."""
    filepath = Path(filepath)
    if not filepath.exists():
        return {}
    with open(filepath, "r") as f:
        return yaml.safe_load(f) or {}


def write_pipeline(filename: str, data: dict) -> None:
    """Convenience wrapper that writes to knowledge_base/pipeline_state/."""
    filepath = KNOWLEDGE_BASE_DIR / "pipeline_state" / filename
    atomic_write(filepath, data)
