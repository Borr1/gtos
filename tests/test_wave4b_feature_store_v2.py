from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.research_infra import wave4b_feature_store_v2 as wave4b


ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Input-presence guard (2026-07-27)
# ---------------------------------------------------------------------------
# Every test below calls ``wave4b.load_wave4a_inputs(ROOT)`` (directly, or via
# ``build_artifacts``), which requires all of ``wave4b.WAVE4A_REQUIRED_FILES``
# under the WAVE4A route. That route is absent, so all four tests fail with
# ``FileNotFoundError`` — indistinguishable from a real defect.
#
# The skip is conditional on the ACTUAL absence of those files, never on a
# marker meaning "we know this is broken". If the route is ever restored or
# regenerated, `_MISSING_WAVE4A_INPUTS` is empty and these tests run again with
# no edit here. An unconditional ``@pytest.mark.skip`` would report "not
# applicable" forever — the same false-green shape this guard exists to avoid.
#
# Recoverability, verified 2026-07-27:
#   * The route exists in NO tree object anywhere in this repository's history
#     (full `git cat-file --batch-all-objects` scan: 0 hits). It is not
#     restorable by checkout, and it is not in LFS.
#   * It IS regenerable from
#     research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/
#     (tracked at HEAD, sparse-masked) via `wave4a.build_artifacts` +
#     `wave4a.write_verification_result`: the rebuilt canonical universe is
#     byte-identical to the sealed one — sha256
#     fef22580d4b641243d166bb2ce3d24535826436f5d0f818ad2a3dbab1c53bab6,
#     15,679 rows, matching `wave4c.CANONICAL_UNIVERSE_HASH`.
#   * Two of the twelve required files —
#     WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_FOCUSED_TEST_RESULT.json and
#     WAVE4A_ORCHESTRATOR_ACCEPTANCE_REVIEW.md — have no producer in the tree
#     and no git object. They are existence-gated only (never read), so they
#     block regeneration without contributing any data.
_WAVE4A_ROUTE = "research/operations/final_moonshot_wave4a_digital_twin_historical_microscope_2026_06_05"

_MISSING_WAVE4A_INPUTS = [
    name
    for name in wave4b.WAVE4A_REQUIRED_FILES
    if not (ROOT / wave4b.WAVE4A_ROUTE / name).exists()
]

if _MISSING_WAVE4A_INPUTS:
    pytest.skip(
        f"wave4b inputs are absent: {len(_MISSING_WAVE4A_INPUTS)} of "
        f"{len(wave4b.WAVE4A_REQUIRED_FILES)} required artifacts under "
        f"{_WAVE4A_ROUTE}/ do not exist "
        f"(first missing: {_MISSING_WAVE4A_INPUTS[0]}). "
        f"That route is in no tree object in this repository's history; it is regenerable "
        f"from research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/ "
        f"(tracked at HEAD, sparse-masked) except for two existence-gated provenance files "
        f"that have no producer. This skip lifts automatically once the route is on disk.",
        allow_module_level=True,
    )


def test_wave4b_builds_one_feature_row_per_wave4a_canonical_row():
    inputs = wave4b.load_wave4a_inputs(ROOT)
    raw_by_key = wave4b.load_raw_sources(ROOT, inputs["inventory"])
    canonical = inputs["canonical"][0]
    event = inputs["events"][canonical["canonical_row_id"]]
    row = wave4b.make_feature_row(
        canonical,
        event,
        raw_by_key[wave4b.raw_row_key(canonical)],
        inputs["path_clock"][canonical["canonical_row_id"]],
        inputs["opportunity"].get(canonical["canonical_row_id"]),
    )

    assert len(inputs["canonical"]) == 15679
    assert set(row["features"]) == set(wave4b.FAMILY_NAMES)
    assert row["feature_hash"]
    assert row["features"]["source_completeness"]["numeric_features"]["upstream_label_values_excluded_flag"] == 1.0


def test_wave4b_feature_values_exclude_forbidden_label_tokens():
    inputs = wave4b.load_wave4a_inputs(ROOT)
    raw_by_key = wave4b.load_raw_sources(ROOT, inputs["inventory"])
    rows = []
    for canonical in inputs["canonical"][:50]:
        canonical_id = canonical["canonical_row_id"]
        rows.append(
            wave4b.make_feature_row(
                canonical,
                inputs["events"][canonical_id],
                raw_by_key[wave4b.raw_row_key(canonical)],
                inputs["path_clock"][canonical_id],
                inputs["opportunity"].get(canonical_id),
            )
        )

    forbidden = set()
    for row in rows:
        for family_row in row["features"].values():
            for field in family_row["numeric_features"]:
                for token in wave4b.FORBIDDEN_LABEL_FIELD_TOKENS:
                    if token in field.casefold():
                        forbidden.add(field)
    assert forbidden == set()


def test_wave4b_build_and_verify_temp_route():
    with tempfile.TemporaryDirectory(prefix="wave4b_test_") as tmp:
        route_dir = Path(tmp) / "route"
        summary = wave4b.build_artifacts(ROOT, route_dir)
        result = wave4b.verify_route(ROOT, route_dir)

    assert summary["row_counts"]["feature_rows"] == 15679
    assert summary["row_counts"]["feature_family_rows"] == 15679 * len(wave4b.FAMILY_NAMES)
    assert result["ok"] is True


def test_wave4b_probability_and_confluence_gaps_are_explicit():
    inputs = wave4b.load_wave4a_inputs(ROOT)
    raw_by_key = wave4b.load_raw_sources(ROOT, inputs["inventory"])
    canonical = next(row for row in inputs["canonical"] if row["source_key"] == "candidate_causal_microscope")
    canonical_id = canonical["canonical_row_id"]
    feature = wave4b.make_feature_row(
        canonical,
        inputs["events"][canonical_id],
        raw_by_key[wave4b.raw_row_key(canonical)],
        inputs["path_clock"][canonical_id],
        inputs["opportunity"].get(canonical_id),
    )

    probability = feature["features"]["probability_debate"]
    confluence = feature["features"]["numeric_confluence"]
    assert "broker_net_ev_fill_probability_source_missing" in probability["source_gap_codes"]
    assert "follow_avoid_mixed_numeric_source_absent_for_row" in confluence["source_gap_codes"]
