"""Tests for walk-forward lock enforcement (Task 3)."""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.components.walk_forward import (
    compute_prompt_hash,
    check_walk_forward_lock,
    create_lock,
    load_lock,
    save_lock,
)


@pytest.fixture
def tmp_dir(tmp_path):
    """Provide temp directory with a fake prompt file."""
    prompt = tmp_path / "prompt.py"
    prompt.write_text("# Original prompt content\nPROMPT = 'analyze gold'")
    lock_path = str(tmp_path / "walk_forward_lock.json")
    return tmp_path, str(prompt), lock_path


class TestComputePromptHash:
    def test_deterministic(self, tmp_dir):
        _, prompt_path, _ = tmp_dir
        h1 = compute_prompt_hash(prompt_path)
        h2 = compute_prompt_hash(prompt_path)
        assert h1 == h2
        assert len(h1) == 64  # SHA256 hex digest

    def test_changes_with_content(self, tmp_dir):
        tmp_path, prompt_path, _ = tmp_dir
        h1 = compute_prompt_hash(prompt_path)
        Path(prompt_path).write_text("# Modified prompt\nPROMPT = 'analyze silver'")
        h2 = compute_prompt_hash(prompt_path)
        assert h1 != h2


class TestCheckWalkForwardLock:
    def test_no_lock_file_passes(self, tmp_dir):
        _, prompt_path, lock_path = tmp_dir
        assert check_walk_forward_lock(prompt_path, lock_path) is True

    def test_matching_hash_passes(self, tmp_dir):
        _, prompt_path, lock_path = tmp_dir
        lock = create_lock("WF-TEST", months=3, prompt_path=prompt_path,
                           lock_path=lock_path)
        assert check_walk_forward_lock(prompt_path, lock_path) is True

    def test_mismatched_hash_warns(self, tmp_dir):
        tmp_path, prompt_path, lock_path = tmp_dir
        create_lock("WF-TEST", months=3, prompt_path=prompt_path,
                    lock_path=lock_path)
        # Modify the prompt
        Path(prompt_path).write_text("# Changed prompt!")
        assert check_walk_forward_lock(prompt_path, lock_path) is False

    def test_expired_lock_passes(self, tmp_dir):
        tmp_path, prompt_path, lock_path = tmp_dir
        create_lock("WF-TEST", months=3, prompt_path=prompt_path,
                    lock_path=lock_path)
        # Backdate the lock to make it expired
        lock = load_lock(lock_path)
        lock["lock_expires"] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        save_lock(lock, lock_path)
        # Modify prompt
        Path(prompt_path).write_text("# Changed prompt!")
        # Should pass because lock is expired
        assert check_walk_forward_lock(prompt_path, lock_path) is True

    def test_prompt_file_missing_passes(self, tmp_dir):
        _, _, lock_path = tmp_dir
        save_lock({
            "window": "WF-1",
            "prompt_hash": "abc123",
            "lock_expires": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
        }, lock_path)
        # Non-existent prompt path
        assert check_walk_forward_lock("/nonexistent/prompt.py", lock_path) is True


class TestCreateLock:
    def test_creates_lock_file(self, tmp_dir):
        _, prompt_path, lock_path = tmp_dir
        lock = create_lock("WF-1", months=3, prompt_path=prompt_path,
                           lock_path=lock_path)
        assert Path(lock_path).exists()
        assert lock["window"] == "WF-1"
        assert len(lock["prompt_hash"]) == 64
        assert "locked_at" in lock
        assert "lock_expires" in lock

    def test_lock_duration(self, tmp_dir):
        _, prompt_path, lock_path = tmp_dir
        lock = create_lock("WF-2", months=6, prompt_path=prompt_path,
                           lock_path=lock_path)
        locked = datetime.fromisoformat(lock["locked_at"])
        expires = datetime.fromisoformat(lock["lock_expires"])
        delta = expires - locked
        # 6 months ~ 180 days
        assert 175 <= delta.days <= 185

    def test_creates_parent_dirs(self, tmp_dir):
        tmp_path, prompt_path, _ = tmp_dir
        deep_lock = str(tmp_path / "deep" / "nested" / "lock.json")
        lock = create_lock("WF-1", months=3, prompt_path=prompt_path,
                           lock_path=deep_lock)
        assert Path(deep_lock).exists()
