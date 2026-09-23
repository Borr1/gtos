import hashlib
from pathlib import Path

import pytest

from src.judgment.news_calendar_sync import (
    JUNE_WEEK_OF_RECORD,
    JuneWeekOfRecordError,
    refuse_june_overwrite,
    sync_from_spine,
)

REPO = Path(__file__).resolve().parents[2]


def test_june_week_of_record_is_still_june():
    raw = JUNE_WEEK_OF_RECORD.read_text(encoding="utf-8")
    assert '"week_of": "2026-05-31"' in raw
    assert "2026-06-01" in raw


def test_refuse_june_overwrite():
    with pytest.raises(JuneWeekOfRecordError):
        refuse_june_overwrite(JUNE_WEEK_OF_RECORD)


def test_sync_from_spine_writes_13_and_leaves_june(tmp_path):
    before = hashlib.sha256(JUNE_WEEK_OF_RECORD.read_bytes()).hexdigest()
    dest = tmp_path / "news_calendar_f5_synced_from_spine.json"
    stub = tmp_path / "stub.json"
    stub.write_text(
        """{"events":[{"scheduled_utc":"2026-09-17T11:00:00Z","name":"BOE Rate Decision","tickets":[1,2]}]}""",
        encoding="utf-8",
    )
    snap = sync_from_spine(out_path=dest, stub_path=stub, write=True)
    assert snap["n_events"] == 13
    assert snap["invented"] is False
    assert snap["status"] == "synced_from_high_spine"
    assert snap["stub_tickets_mapped"] == 1
    names = [e["event"] for e in snap["events"]]
    assert "US Nonfarm Payrolls (NFP September 2026)" in names
    assert "US CPI (September 2026)" in names
    boe = next(e for e in snap["events"] if e["event"] == "BOE Rate Decision")
    assert boe["tickets"] == [1, 2]
    # no exact name+clock match → no guessed tickets
    warsh = next(e for e in snap["events"] if "Warsh" in e["event"])
    assert warsh["tickets"] is None
    after = hashlib.sha256(JUNE_WEEK_OF_RECORD.read_bytes()).hexdigest()
    assert after == before
    with pytest.raises(JuneWeekOfRecordError):
        sync_from_spine(out_path=JUNE_WEEK_OF_RECORD, write=True)
