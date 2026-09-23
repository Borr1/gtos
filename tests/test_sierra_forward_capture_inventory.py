from __future__ import annotations

from pathlib import Path

from scripts import build_sierra_forward_capture_inventory as mod
from scripts import inspect_sierra_scid


def test_infer_symbol_handles_contract_names():
    assert mod.infer_symbol(Path("NQM26-CME.scid")) == "NQ"
    assert mod.infer_symbol(Path("6BM26-CME.depth")) == "6B"
    assert mod.infer_symbol(Path("VXMM26-CFE.scid")) == "VXMM"
    assert mod.infer_symbol(Path("XAUUSD_2026-04-15_scid.csv")) == "XAUUSD"


def test_default_roots_include_live_sierra_data_root():
    assert "C:/SierraChart/Data" in mod.DEFAULT_ROOTS


def test_inventory_classifies_scid_and_depth(tmp_path):
    root = tmp_path / "sierra"
    root.mkdir()
    (root / "NQM26-CME_scid.csv").write_text("time,open\n1,2\n", encoding="utf-8")
    (root / "NQM26-CME.depth").write_bytes(b"not-a-real-depth-but-present")
    (root / "6BM26-CME_scid.csv").write_text("time,open\n1,2\n", encoding="utf-8")

    payload = mod.build_inventory(roots=[root], expected_symbols=["NQ", "6B", "SI"])

    by_symbol = {row["symbol_root"]: row for row in payload["symbols"]}
    assert by_symbol["NQ"]["status"] == "READY_SCID_AND_DEPTH_PRESENT"
    assert by_symbol["6B"]["status"] == "CAUTION_SCID_PRESENT_DEPTH_MISSING"
    assert by_symbol["SI"]["status"] == "BLOCKED_MISSING_LOCAL_SIERRA_FILES"
    assert by_symbol["NQ"]["scid_record_count_total"] == 1
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_native_scid_record_count_uses_current_parser(tmp_path):
    scid_path = tmp_path / "NQM26-CME.scid"
    header = inspect_sierra_scid.HEADER_STRUCT.pack(
        b"SCID",
        inspect_sierra_scid.HEADER_STRUCT.size,
        inspect_sierra_scid.RECORD_STRUCT.size,
        1,
        0,
        0,
        b"\x00" * 36,
    )
    record = inspect_sierra_scid.RECORD_STRUCT.pack(0, 1.0, 1.0, 1.0, 1.0, 1, 1, 1, 1)
    scid_path.write_bytes(header + record)

    assert mod._record_count(scid_path) == 1


def test_render_md_contains_operator_boundary(tmp_path):
    payload = mod.build_inventory(roots=[tmp_path], expected_symbols=["NQ"])
    md = mod.render_md(payload)
    assert "NO_PROMOTION_VERDICT" in md
    assert "Operator Boundary" in md
