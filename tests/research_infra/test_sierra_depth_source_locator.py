from __future__ import annotations

import hashlib
from pathlib import Path

from src.research_infra import sierra_depth_source_locator as mod


def _write_depth(path: Path, payload: bytes = b"depth-bytes") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def test_normalize_sierra_depth_filename_accepts_date_forms_and_suffixes():
    exact = mod.normalize_sierra_depth_filename("NQM26-CME.2026-05-01.depth")
    delayed = mod.normalize_sierra_depth_filename("nqm26-cme_20260501_delayed.depth")

    assert exact is not None
    assert exact.source_symbol == "NQM26-CME"
    assert exact.source_date == "2026-05-01"
    assert exact.suffix == ""
    assert exact.normalized_filename == "NQM26-CME.2026-05-01.depth"

    assert delayed is not None
    assert delayed.source_symbol == "NQM26-CME"
    assert delayed.source_date == "2026-05-01"
    assert delayed.suffix == "_delayed"
    assert delayed.is_delayed is True
    assert mod.normalize_sierra_depth_filename("NQM26-CME.2026-05-01.scid") is None


def test_locate_exact_depth_file_recursively_with_hash_size_and_mtime(tmp_path: Path):
    payload = b"exact-depth"
    path = _write_depth(tmp_path / "nested" / "NQM26-CME.2026-05-01.depth", payload)
    _write_depth(tmp_path / "nested" / "NQM26-CME.2026-05-01_delayed.depth", b"delayed")

    result = mod.locate_sierra_depth_source("nqm26-cme", "20260501", roots=[tmp_path])

    assert result.classification == mod.CLASS_EXACT
    assert result.expected_filename == "NQM26-CME.2026-05-01.depth"
    assert len(result.exact_matches) == 1
    assert len(result.delayed_matches) == 1
    match = result.exact_matches[0]
    assert match.path == str(path)
    assert match.size_bytes == len(payload)
    assert match.sha256 == hashlib.sha256(payload).hexdigest()
    assert match.mtime_utc.endswith("+00:00")
    assert result.as_dict()["exact_matches"][0]["sha256"] == match.sha256


def test_locate_classifies_delayed_before_near_when_no_exact_file(tmp_path: Path):
    _write_depth(tmp_path / "NQM26-CME.2026-05-01_delayed.depth", b"delayed")
    _write_depth(tmp_path / "NQM26-CME.2026-05-01_copy.depth", b"copy")

    result = mod.locate_sierra_depth_source("NQM26-CME", "2026-05-01", roots=[tmp_path])

    assert result.classification == mod.CLASS_DELAYED
    assert [row.classification for row in result.delayed_matches] == [mod.CLASS_DELAYED]
    assert [row.classification for row in result.near_matches] == [mod.CLASS_NEAR]


def test_locate_classifies_near_suffix_when_no_exact_or_delayed_file(tmp_path: Path):
    _write_depth(tmp_path / "NQM26-CME.2026-05-01_archive.depth", b"archive")
    _write_depth(tmp_path / "NQM26-CME.2026-05-02.depth", b"wrong-date")
    _write_depth(tmp_path / "YMM26-CBOT.2026-05-01.depth", b"wrong-symbol")

    result = mod.locate_sierra_depth_source("NQM26-CME", "2026-05-01", roots=[tmp_path])

    assert result.classification == mod.CLASS_NEAR
    assert len(result.near_matches) == 1
    assert result.near_matches[0].filename.suffix == "_archive"


def test_locate_classifies_no_local_for_empty_or_missing_roots(tmp_path: Path):
    result = mod.locate_sierra_depth_source(
        "NQM26-CME",
        "2026-05-01",
        roots=[tmp_path / "empty", tmp_path / "missing"],
    )

    assert result.classification == mod.CLASS_NO_LOCAL
    assert result.matches == ()
    assert result.scan_complete is True


def test_locate_classifies_permission_errors_without_raising(monkeypatch):
    def fake_scan(*_args, **_kwargs):
        yield mod.SierraDepthScanEvent(
            error=mod.SierraDepthScanError(
                path="blocked-root",
                error_type="PermissionError",
                message="denied",
            )
        )

    monkeypatch.setattr(mod, "iter_sierra_depth_files", fake_scan)

    result = mod.locate_sierra_depth_source("NQM26-CME", "2026-05-01", roots=["blocked-root"])

    assert result.classification == mod.CLASS_PERMISSION
    assert len(result.permission_errors) == 1
    assert result.permission_errors[0].path == "blocked-root"


def test_scan_can_resume_after_cursor(tmp_path: Path):
    first = _write_depth(tmp_path / "AAM26-CME.2026-05-01.depth", b"first")
    second = _write_depth(tmp_path / "NQM26-CME.2026-05-01.depth", b"second")

    partial = mod.locate_sierra_depth_source(
        "NQM26-CME",
        "2026-05-01",
        roots=[tmp_path],
        max_scan_entries=1,
    )
    resumed = mod.locate_sierra_depth_source(
        "NQM26-CME",
        "2026-05-01",
        roots=[tmp_path],
        resume_after=partial.resume_after,
    )

    assert partial.scan_complete is False
    assert partial.resume_after == str(first)
    assert resumed.scan_complete is True
    assert resumed.classification == mod.CLASS_EXACT
    assert resumed.exact_matches[0].path == str(second)
