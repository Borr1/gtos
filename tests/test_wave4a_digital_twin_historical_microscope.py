from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.research_infra import wave4a_digital_twin_historical_microscope as wave4a


ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Input-presence guard (2026-07-27)
# ---------------------------------------------------------------------------
# Every test below reads the WAVE2 route through
# ``wave4a.MATERIAL_SOURCE_SPECS``. In a sparse checkout that route is not
# materialised on disk and all four tests fail with ``FileNotFoundError``,
# which is indistinguishable from a real defect.
#
# The skip is conditional on the ACTUAL absence of the declared inputs, never
# on a "we are in a degraded checkout" marker: the moment the route is
# materialised, `_MISSING_WAVE2_INPUTS` is empty and all four tests run again
# with no edit to this file. An unconditional ``@pytest.mark.skip`` would be
# the same false-green failure mode as a passing-but-vacuous test — it would
# report "not applicable" forever, including after the inputs came back.
#
# THIS INPUT IS RECOVERABLE. All 151 files of the WAVE2 route are tracked at
# HEAD with real (non-LFS) content and are absent only because this worktree
# uses git sparse-checkout (all 151 carry the skip-worktree flag). Verified
# 2026-07-27: `git cat-file -p HEAD:<path>` returns each of the 14 source
# ledgers below, and every one has exactly the row count
# ``MATERIAL_SOURCE_SPECS`` declares (15,679 rows total).
_WAVE2_ROUTE = "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04"

_MISSING_WAVE2_INPUTS = [
    spec.path for spec in wave4a.MATERIAL_SOURCE_SPECS if not (ROOT / spec.path).is_file()
]

if _MISSING_WAVE2_INPUTS:
    pytest.skip(
        f"wave4a inputs are not materialised in this checkout: "
        f"{len(_MISSING_WAVE2_INPUTS)} of {len(wave4a.MATERIAL_SOURCE_SPECS)} source ledgers "
        f"under {_WAVE2_ROUTE}/ are absent "
        f"(first missing: {_MISSING_WAVE2_INPUTS[0]}). "
        f"RECOVERABLE — that route is tracked at HEAD (151 files, real content) and is "
        f"skip-worktree-masked by sparse-checkout, not deleted. Restore with "
        f"`git sparse-checkout add {_WAVE2_ROUTE}` (~69 MB) and these tests run again "
        f"automatically; no change to this file is required.",
        allow_module_level=True,
    )


def test_wave4a_material_source_contract_preserves_all_rows():
    entries, inventory, _ = wave4a.load_material_entries(ROOT)

    assert len(entries) == sum(spec.expected_rows for spec in wave4a.MATERIAL_SOURCE_SPECS)
    assert len({row["canonical_row_id"] for row in entries}) == len(entries)
    assert {row["source_key"] for row in inventory} == {
        spec.source_key for spec in wave4a.MATERIAL_SOURCE_SPECS
    }
    assert all(row["row_count_status"] == "matches_expected" for row in inventory)


def test_wave4a_asof_event_excludes_path_and_result_labels():
    entries, _, _ = wave4a.load_material_entries(ROOT)
    broker_entry = next(row for row in entries if row["source_key"] == "broker_trade_causal_microscope")
    event = wave4a.digital_twin_event(broker_entry)

    assert event["result_use_status"] == "deterministic_asof_replay_event_not_outcome_score"
    assert event["label_boundary"]["broker_real"]["available"] is True
    forbidden = set(event["asof_observation"]) & wave4a.FORBIDDEN_LABEL_FIELDS
    assert forbidden == set()


def test_wave4a_build_and_verify_temp_route():
    with tempfile.TemporaryDirectory(prefix="wave4a_test_") as tmp:
        route_dir = Path(tmp) / "route"
        summary = wave4a.build_artifacts(ROOT, route_dir)
        result = wave4a.verify_route(ROOT, route_dir)

    assert summary["canonical_rows"] == sum(spec.expected_rows for spec in wave4a.MATERIAL_SOURCE_SPECS)
    assert result["ok"] is True


def test_wave4a_loser_mfe_coverage_preserves_source_gaps():
    entries, _, raw_by_canonical = wave4a.load_material_entries(ROOT)
    loser_rows = wave4a.loser_mfe_rows(entries, raw_by_canonical)

    source_supported = [
        row for row in loser_rows if row["source_support_status"] == "source_supported_loser_mfe_row"
    ]
    broker_loss_gaps = [
        row for row in loser_rows if row["source_support_status"] == "broker_loss_without_loser_mfe_source_row"
    ]
    assert len(source_supported) == 29
    assert len(broker_loss_gaps) == 17
    assert all(row["result_use_status"] in {"loser_mfe_path_label_not_asof_feature", "source_gap_for_loser_mfe_path_label"} for row in loser_rows)
