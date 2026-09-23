from __future__ import annotations

import json
from pathlib import Path

from scripts.repair_shadow_jsonl import parse_jsonl_lines, repair_file


def test_parse_jsonl_lines_separates_invalid_fragments():
    valid, invalid = parse_jsonl_lines(
        [
            '{"timestamp":"2026-04-29T09:00:05+00:00","symbol":"USDJPY"}',
            "20}",
        ]
    )

    assert len(valid) == 1
    assert invalid[0]["line"] == 2
    assert invalid[0]["raw_fragment"] == "20}"


def test_repair_file_preserves_backup_and_quarantines_invalid(tmp_path):
    source = tmp_path / "d1_bias_lag.jsonl"
    source.write_text(
        "\n".join(
            [
                '{"timestamp":"2026-04-29T08:45:05+00:00","symbol":"USDJPY","rolling_N_consecutive":19}',
                "20}",
                '{"timestamp":"2026-04-29T09:15:05+00:00","symbol":"USDJPY","rolling_N_consecutive":21}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = repair_file(
        source=source,
        backup_dir=tmp_path / "backup",
        quarantine_jsonl=tmp_path / "recovery.jsonl",
        report_json=tmp_path / "report.json",
        report_md=tmp_path / "report.md",
        in_place=True,
    )

    assert report["invalid_rows"] == 1
    assert Path(report["backup_path"]).exists()
    cleaned_lines = source.read_text(encoding="utf-8").splitlines()
    assert len(cleaned_lines) == 2
    assert all(json.loads(line)["symbol"] == "USDJPY" for line in cleaned_lines)

    recovery = json.loads((tmp_path / "recovery.jsonl").read_text(encoding="utf-8"))
    assert recovery["schema_version"] == "d1_bias_lag_recovery_v1"
    assert recovery["fragment_tail_rolling_N_consecutive"] == 20
    assert recovery["candidate_sequence_inferences"][0]["symbol"] == "USDJPY"
