from __future__ import annotations

import json

from scripts.repair_jsonl_invalid_rows import repair_file


def test_repair_jsonl_invalid_rows_quarantines_before_rewrite(tmp_path):
    path = tmp_path / "shadow_logs" / "sample.jsonl"
    quarantine = tmp_path / "research" / "quarantine.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text('{"ok": 1}\nfragment\n{"ok": 2}\n', encoding="utf-8")

    dry = repair_file(path, quarantine=quarantine, apply=False)

    assert dry["status"] == "INVALID_ROWS_FOUND"
    assert dry["invalid_line_numbers"] == [2]
    assert "fragment" in path.read_text(encoding="utf-8")
    assert not quarantine.exists()

    applied = repair_file(path, quarantine=quarantine, apply=True)

    assert applied["status"] == "REPAIRED"
    assert [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] == [
        {"ok": 1},
        {"ok": 2},
    ]
    quarantined = [json.loads(line) for line in quarantine.read_text(encoding="utf-8").splitlines()]
    assert quarantined[0]["raw_line"] == "fragment"
    assert quarantined[0]["repair_applied"] is True
