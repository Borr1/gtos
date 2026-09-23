from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from scripts import build_expanded_oos_control_artifacts as control


def _scratch_dir() -> Path:
    root = Path(".test_expanded_oos_control_artifacts_tmp")
    root.mkdir(exist_ok=True)
    path = root / uuid.uuid4().hex
    path.mkdir()
    return path


def test_depth_inventory_groups_by_symbol_and_flags_missing() -> None:
    tmp_path = _scratch_dir()
    depth_dir = tmp_path / "MarketDepthData"
    depth_dir.mkdir()
    try:
        (depth_dir / "NQM26-CME.2026-04-03.depth").write_bytes(b"abc")
        (depth_dir / "NQM26-CME.2026-04-04.depth").write_bytes(b"defgh")
        (depth_dir / "CLM26-NYMEX.2026-04-03.depth").write_bytes(b"x")

        payload = control.summarize_sierra_depth(depth_dir)

        by_symbol = {row["symbol"]: row for row in payload["symbols"]}
        assert payload["file_count"] == 3
        assert by_symbol["NQM26-CME"]["files"] == 2
        assert by_symbol["NQM26-CME"]["first_date"] == "2026-04-03"
        assert by_symbol["NQM26-CME"]["last_date"] == "2026-04-04"
        assert "MNQM26-CME" in payload["missing_first_wave_depth_symbols"]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_mt5_manifest_summary_preserves_symbol_timeframe_rows() -> None:
    tmp_path = _scratch_dir()
    manifest_dir = tmp_path / "mt5_research_exports" / "sample"
    manifest_dir.mkdir(parents=True)
    manifest = {
        "label": "sample",
        "created_at_utc": "2026-05-03T00:00:00+00:00",
        "start_utc": "2026-04-01T00:00:00+00:00",
        "end_utc": "2026-04-02T00:00:00+00:00",
        "read_only": True,
        "account": {"server": "demo"},
        "files": {
            "XAUUSD_M15": {
                "file_symbol": "XAUUSD",
                "mt5_symbol": "XAUUSD",
                "timeframe": "M15",
                "rows": 96,
                "first": "2026-04-01 00:00:00",
                "last": "2026-04-01 23:45:00",
                "gap_count": 0,
                "max_gap_seconds": 0.0,
            }
        },
    }
    try:
        (manifest_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        payload = control.summarize_mt5_manifests(tmp_path)

        assert payload["manifest_count"] == 1
        assert payload["datasets"][0]["rows"] == 96
        assert payload["by_symbol_timeframe"][0]["symbol"] == "XAUUSD"
        assert payload["by_symbol_timeframe"][0]["timeframe"] == "M15"
        assert payload["by_symbol_timeframe"][0]["first"] == "2026-04-01 00:00:00"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_candidate_registry_is_frozen_no_promotion() -> None:
    payload = control.candidate_registry()

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["frozen_before_expanded_outcome_runs"] is True
    assert payload["trial_accounting"]["opened_outcome_slices_at_registration"] == 0
    assert payload["trial_accounting"]["rule_tuning_allowed_after_outcome_open"] is False
    assert payload["candidate_count"] == len(payload["candidates"])
    assert any(
        row.get("variant_id") == "V3_FVG_ONLY_RESCUE_RISK_BANK"
        for row in payload["candidates"]
    )


def test_markdown_writers_include_no_promotion() -> None:
    tmp_path = _scratch_dir()
    registry = control.candidate_registry()
    registry_md = tmp_path / "registry.md"
    try:
        control.write_registry_markdown(registry_md, registry)

        text = registry_md.read_text(encoding="utf-8")
        assert "NO_PROMOTION_VERDICT" in text
        assert "Frozen Candidates" in text
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)
