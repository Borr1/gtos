from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from src.utils.file_io import atomic_write


def test_atomic_write_serializes_datetime_and_path(tmp_path):
    target = tmp_path / "state.json"

    atomic_write(target, {
        "time": datetime(2026, 5, 28, 19, 30, tzinfo=timezone.utc),
        "path": target,
    })

    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved["time"] == "2026-05-28T19:30:00+00:00"
    assert saved["path"].endswith("state.json")
    assert not list(tmp_path.glob("*.tmp"))


def test_atomic_write_removes_tmp_on_serialization_failure(tmp_path):
    class NotSerializable:
        pass

    target = tmp_path / "bad.json"

    with pytest.raises(TypeError):
        atomic_write(target, {"bad": NotSerializable()})

    assert not target.exists()
    assert not list(tmp_path.glob("*.tmp"))
