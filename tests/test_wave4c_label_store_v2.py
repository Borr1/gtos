from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.research_infra import wave4c_label_store_v2 as wave4c


ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Input-presence guard (2026-07-27)
# ---------------------------------------------------------------------------
# Every test below calls ``wave4c.load_inputs(ROOT)`` or
# ``wave4c.build_artifacts(ROOT, ...)``. Both read the nine WAVE4A ledgers
# listed here (``wave4c_label_store_v2.py:268-285``) plus every WAVE2 material
# source (``:253-265``). The WAVE4A route is absent, so all four tests fail
# with ``FileNotFoundError`` — indistinguishable from a real defect.
#
# The skip is conditional on the ACTUAL absence of those files, never on a
# marker meaning "we know this is broken". If the route is restored or
# regenerated, `_MISSING_WAVE4C_INPUTS` is empty and these tests run again with
# no edit here. An unconditional ``@pytest.mark.skip`` would report "not
# applicable" forever — the false-green shape this guard exists to avoid.
#
# See tests/test_wave4b_feature_store_v2.py for the full recoverability
# finding: the route is in no tree object in this repository's history, but is
# regenerable from the (sparse-masked, tracked-at-HEAD) WAVE2 route — the
# rebuilt canonical universe reproduces `wave4c.CANONICAL_UNIVERSE_HASH`
# exactly, 15,679 rows.
_WAVE4A_ROUTE = "research/operations/final_moonshot_wave4a_digital_twin_historical_microscope_2026_06_05"

_WAVE4C_REQUIRED_WAVE4A_FILES = (
    "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl",
    "WAVE4A_DIGITAL_TWIN_EVENT_LEDGER.jsonl",
    "WAVE4A_PATH_CLOCK_FORENSIC_LEDGER.jsonl",
    "WAVE4A_ACCEPTED_REJECTED_OPPORTUNITY_LEDGER.jsonl",
    "WAVE4A_LOSER_MFE_HARVEST_LEDGER.jsonl",
    "WAVE4A_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl",
    "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_OUTPUT_MANIFEST.json",
    "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_VERIFICATION_RESULT.json",
    "WAVE4A_COVERAGE_MATRIX.json",
)

_MISSING_WAVE4C_INPUTS = [
    str(wave4c.WAVE4A_ROUTE / name)
    for name in _WAVE4C_REQUIRED_WAVE4A_FILES
    if not (ROOT / wave4c.WAVE4A_ROUTE / name).exists()
] + [
    spec.path
    for spec in wave4c.wave4a.MATERIAL_SOURCE_SPECS
    if not (ROOT / spec.path).is_file()
]

if _MISSING_WAVE4C_INPUTS:
    pytest.skip(
        f"wave4c inputs are absent: {len(_MISSING_WAVE4C_INPUTS)} required source files "
        f"do not exist, headed by {_WAVE4A_ROUTE}/ "
        f"(first missing: {_MISSING_WAVE4C_INPUTS[0]}). "
        f"That route is in no tree object in this repository's history; it is regenerable "
        f"from research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/ "
        f"(tracked at HEAD, sparse-masked). This skip lifts automatically once the inputs "
        f"are on disk.",
        allow_module_level=True,
    )


def test_wave4c_builds_full_row_label_ledgers_in_temp_route():
    with tempfile.TemporaryDirectory(prefix="wave4c_test_") as tmp:
        route_dir = Path(tmp) / "route"
        summary = wave4c.build_artifacts(ROOT, route_dir)
        label_rows = list(wave4c.wave4a.iter_jsonl(route_dir / "WAVE4C_LABEL_LEDGER.jsonl"))

    assert summary["canonical_rows"] == wave4c.CANONICAL_ROW_COUNT
    assert len(label_rows) == wave4c.CANONICAL_ROW_COUNT
    assert all(count == wave4c.CANONICAL_ROW_COUNT for count in summary["ledger_counts"].values())


def test_wave4c_evidence_classes_keep_cash_and_r_separate():
    inputs = wave4c.load_inputs(ROOT)
    ledgers = wave4c.build_label_rows(inputs)
    evidence_rows = ledgers["WAVE4C_EVIDENCE_CLASS_LABEL_LEDGER.jsonl"]

    cash_rows = [
        row
        for row in evidence_rows
        if row["evidence_class_labels"]["broker_real_cash_pnl"]["value"] is not None
    ]
    exact_rows = [
        row
        for row in evidence_rows
        if row["evidence_class_labels"]["exact_r"]["value"] is not None
    ]

    assert cash_rows
    assert exact_rows
    assert all(row["evidence_class_labels"]["broker_real_cash_pnl"]["unit"] == "cash" for row in cash_rows)
    assert all(row["evidence_class_labels"]["exact_r"]["unit"] == "R" for row in exact_rows)


def test_wave4c_labels_are_banned_from_feature_store_inputs():
    inputs = wave4c.load_inputs(ROOT)
    ledgers = wave4c.build_label_rows(inputs)
    label_rows = ledgers["WAVE4C_LABEL_LEDGER.jsonl"]

    assert len(label_rows) == wave4c.CANONICAL_ROW_COUNT
    assert all(row["labels_never_asof_features"] is True for row in label_rows)
    assert {row["feature_store_exclusion"] for row in label_rows} == {wave4c.FEATURE_STORE_EXCLUSION}


def test_wave4c_required_label_families_and_source_trace_are_complete():
    schema = wave4c.label_schema()
    inputs = wave4c.load_inputs(ROOT)
    ledgers = wave4c.build_label_rows(inputs)

    assert set(wave4c.LABEL_FAMILIES).issubset(schema["label_families"])
    for row in ledgers["WAVE4C_LABEL_LEDGER.jsonl"][:100]:
        trace = row["source_trace"]
        for key in (
            "source_key",
            "source_path",
            "source_sha256",
            "source_row_id",
            "source_row_hash",
            "source_completeness_state",
            "capture_status",
        ):
            assert trace[key]
