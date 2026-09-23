"""Shared fixtures for the F5 desk suite.

Everything runs against a THROWAWAY repo root under tmp_path — the project
conftest's production-write guard (pipeline_state/, shadow_logs/, ...) is never
touched. Stream fixtures are trimmed REAL rows from the 2026-08-24 harvest
(tests/fixtures/f5_desk/), so the composer is tested against the live formats.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "f5_desk"

# All fixture stream rows are 2026-08-24; this instant is after the last of them
# (23:19:23Z) and inside the 90-minute pre-midnight window on purpose — the
# composer tests exercise the same clock the dual-write logic keys on.
FIXED_NOW = datetime(2026, 8, 24, 23, 45, 0, tzinfo=timezone.utc)
MIDDAY_NOW = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)

# Tickets in the events fixture (real 2026-08-24 rows):
OPEN_TICKET = 178351322      # EURUSD fill + stop_move, never closed
CLOSED_TICKET = 178351323    # LTCUSD fill then f5_trade_closed (the forensic exhibit)
ADOPTED_TICKET = 178058089   # EURUSD, launcher manage-row adopted[]


def build_desk_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    events = root / "shadow_logs" / "f5_minimal" / "operator" / "events.jsonl"
    events.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES / "events_sample.jsonl", events)
    launcher = root / "shadow_logs" / "ultimate_book_launcher.jsonl"
    shutil.copy(FIXTURES / "launcher_tailday_sample.jsonl", launcher)
    calendar = root / "data" / "news_calendar.json"
    calendar.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES / "calendar_sample.json", calendar)
    return root


@pytest.fixture
def desk_repo(tmp_path: Path) -> Path:
    return build_desk_repo(tmp_path)


@pytest.fixture
def desk_cfg(desk_repo: Path):
    from scripts.f5_desk import composer

    return composer.ComposerConfig(repo_root=desk_repo)
