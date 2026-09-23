from __future__ import annotations

import datetime as dt
import gzip
import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[5]
SCRIPT = HERE / "w7_current_recost.py"


def _load_driver():
    spec = importlib.util.spec_from_file_location("wave21_w7_current_recost", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


W = _load_driver()


def _rows():
    with gzip.open(W.OUT_ROWS, "rt") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def test_armed_set_is_resolved_only_from_authority_api():
    W.assert_consistent()
    declaration = W.declared_arming()
    assert set(declaration) == set(W.ACCOUNT_META)
    for namespace in declaration:
        armed = set(W.armed_sleeves(namespace))
        assert armed == set(W.GENERATOR)
        assert armed == set(declaration[namespace].armed)


def test_current_exit_contract_is_native_and_80_h4_bars():
    for sleeve in sorted(W.GENERATOR):
        policy, doc = W._exit_policy(sleeve, (), 10.0)
        assert policy.maxbars == 80
        assert policy.time_stop_bars == 80
        assert doc["resolved_profile"].get("frontier_cell") is None
        if sleeve == "energy_agri":
            assert policy.partial_at_r == 2.0
            assert policy.partial_frac == 0.5
            assert policy.target_dist == 40.0
        else:
            assert policy.partial_at_r is None


def test_gap_fill_uses_adverse_open_for_plain_stop():
    bars = [W.Bar(100, 101, 99, 100)]
    bars.extend([W.Bar(100, 101, 99, 100), W.Bar(85, 95, 80, 90)])
    result = W.PathResult(
        r_gross=-1.0, exit_index=2, exit_reason="stop", mfe_r=0.0, mae_r=-2.0,
        bars_to_mfe=0, bars_held=2, detail={"entry_price": 100.0},
    )
    policy = W.ExitPolicy(target_dist=30.0, maxbars=80)
    got, detail = W._gap_conservative(bars, 100.0, 1, 10.0, policy, result)
    assert got == -1.5
    assert detail["gap_leg"] == "stop"
    assert detail["gap_level"] == 90.0


def test_gap_fill_uses_breakeven_level_after_partial():
    bars = [W.Bar(100, 101, 99, 100)]
    bars.extend([W.Bar(100, 121, 99, 120), W.Bar(95, 99, 90, 96)])
    result = W.PathResult(
        r_gross=1.0, exit_index=2, exit_reason="stop", mfe_r=2.1, mae_r=-1.0,
        bars_to_mfe=1, bars_held=2,
        detail={"entry_price": 100.0, "partial_banked_r": 1.0,
                "partial_frac_taken": 0.5, "raw_remainder_r": 0.0},
    )
    policy = W.ExitPolicy(
        target_dist=40.0, maxbars=80, partial_at_r=2.0, partial_frac=0.5,
        be_stop_after_partial=True,
    )
    got, detail = W._gap_conservative(bars, 100.0, 1, 10.0, policy, result)
    assert got == pytest.approx(0.75)
    assert detail["gap_leg"] == "breakeven_stop"
    assert detail["gap_level"] == 100.0


def test_source_selection_prefers_native_then_named_ftmo_transfer():
    index = {
        ("redacted_account-Server 2", "BTCUSD", "H4"): {"file": "native"},
        ("FTMO-Server3", "BTCUSD", "H4"): {"file": "ftmo"},
        ("FTMO-Server3", "XAUUSD", "H4"): {"file": "ftmo-gold"},
    }
    row, cls, account = W._source_for(
        "redacted_account", "redacted_account-Server 2", "BTCUSD", index
    )
    assert row["file"] == "native" and cls == "MEASURED" and account == "redacted_account"
    row, cls, account = W._source_for(
        "redacted_account", "redacted_account-Server 2", "XAUUSD", index
    )
    assert row["file"] == "ftmo-gold" and cls == "TRANSFERRED" and account == "FTMO"
    assert W._source_for("FTMO", "FTMO-Server3", "NOPE", index) == (None, None, None)


def test_coverage_weakest_never_strengthens():
    assert W._coverage_weakest("MEASURED", "TRANSFERRED") == "TRANSFERRED"
    assert W._coverage_weakest("TRANSFERRED", "MODELLED") == "MODELLED"
    assert W._coverage_weakest("MODELLED", "NOT_EVALUABLE") == "NOT_EVALUABLE"


def test_bootstrap_is_deterministic_and_day_clustered():
    rows = [
        {"entry_utc": f"2025-01-0{day}T00:00:00+00:00", "x": float(day + j)}
        for day in range(1, 6) for j in range(2)
    ]
    a = W.moving_block_cluster_ci(rows, "x", reps=100)
    b = W.moving_block_cluster_ci(rows, "x", reps=100)
    assert a == b
    assert a["n_days"] == 5 and a["n_trades"] == 10


def test_prior_reconciliation_matches_counts_and_refuses_fake_exact_join():
    doc = json.loads(W.OUT_PRIOR.read_text())
    assert doc["authoritative_current_comparator"] is False
    assert "NOT_A_COMPARATOR" in doc["authority_status"]
    assert doc["pipeline_parity_all_true"] is True
    assert all(row["n_matches_published"] for row in doc["sleeves"].values())
    assert any(not row["exact_rejoinable_from_cache_key"] for row in doc["sleeves"].values())
    assert doc["sleeves"]["crypto"]["cache_rows"] == 104
    assert doc["sleeves"]["energy_agri"]["cache_rows"] == 162


def test_result_ledger_has_exact_band_triplets_and_current_arithmetic():
    result = json.loads(W.OUT_RESULT.read_text())
    rows = _rows()
    assert result["scope"]["selector_v4_decisions_measured"] is False
    assert result["scope"]["scheduler_v4_decisions_measured"] is False
    assert result["scope"]["broad_v4_result_inferred"] is False
    assert W.sha256_path(W.OUT_ROWS) == result["row_ledger"]["sha256"]

    triplets = {}
    for row in rows:
        armed = W.armed_sleeves(row["namespace"])
        assert row["sleeve"] in armed
        key = (
            row["namespace"], row["sleeve"], row["symbol_canonical"],
            row["decision_bar_iso"], row.get("direction"),
        )
        triplets.setdefault(key, set()).add(row["band"])
        assert row["coverage"] in {"MEASURED", "TRANSFERRED", "MODELLED", "NOT_EVALUABLE"}
        assert row["quote_authority_status"] == "MODELLED"
        assert row["quote_lifecycle_coverage"] == "MODELLED"
        assert row["quote_lifecycle_model"] == W.QUOTE_LIFECYCLE_MODEL
        assert row["coverage"] in {"MODELLED", "NOT_EVALUABLE"}
        if row["cost_authority_status"] != "COMPLETE":
            assert row.get("r_net_current_clip") is None
            continue
        components = row["cost_components"]
        nonspread = sum(components[k]["value"] for k in (
            "commission_r", "swap_r", "slippage_r"
        ))
        assert row["counterfactual_pre_floor_r_net_current_clip"] == pytest.approx(
            row["r_quote_gap_validation_clip"] - nonspread
        )
        assert row["cost_total_all_four_r"] == pytest.approx(
            nonspread + components["spread_r"]["value"]
        )
        if row["status"] == "REFUSED_BY_CURRENT_FLOOR":
            assert row["sleeve"] in {"sub_xvol_pullback", "sub_mid_dn_revert"}
            assert row["floor_status"] == "REFUSED"
            assert row.get("r_net_current_clip") is None
        else:
            assert row["status"] == "EVALUABLE"
            assert row["r_net_current_clip"] == pytest.approx(
                row["counterfactual_pre_floor_r_net_current_clip"]
            )
    assert all(bands == set(W.BANDS) for bands in triplets.values())


def test_floor_refusals_only_apply_to_declared_sleeves():
    rows = _rows()
    declared = W.declared_arming()
    for row in rows:
        if row["status"] == "REFUSED_BY_CURRENT_FLOOR":
            assert row["sleeve"] in declared[row["namespace"]].spread_geometry_floor


def test_band_disposition_marks_model_sensitivity_and_missing_high_band():
    result = json.loads(W.OUT_RESULT.read_text())
    fn = result["accounts"]["redacted_account_live_bee34003"]["band_robustness"]
    assert fn["energy_agri"]["disposition"] == "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
    assert fn["sub_xvol_pullback"]["disposition"] == "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP"
    assert fn["sub_mid_dn_revert"]["disposition"] == (
        "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
    )


def test_redacted_account_high_band_floor_exclusion_and_disclosed_cost_refusals():
    """Post-integration re-pin (POST_INTEGRATION_WAVE21_COST_QUOTE_TRUTH).

    Pre-integration this cell had cost authority COMPLETE on every row and the test
    pinned ``cost_authority_not_evaluable == 0`` to prove the zero-survivor high band
    was a floor exclusion, not a cost-authority hole.  Under the integrated
    artifact-bound fail-closed slippage authority, symbols without a reconciled
    price-domain sample REFUSE (UKOIL_cash/USOIL_cash here), so the cell now carries
    a real, disclosed cost narrowing.  The floor pins are unchanged: the zero-survivor
    claim is still fully explained by the floor (every row floor-refused), and the
    cost refusals are pinned explicitly rather than hidden.
    """
    result = json.loads(W.OUT_RESULT.read_text())
    high = result["accounts"]["redacted_account_live_bee34003"]["bands"]["high"]
    xvol = high["sub_xvol_pullback"]
    assert xvol["n_emitted"] == 52
    assert xvol["cost_authority_complete"] == 40
    assert xvol["cost_authority_not_evaluable"] == 12
    assert xvol["spread_floor_survivors"] == 0
    assert xvol["spread_floor_refused"] == 52
    assert xvol["conditional_survivor_evaluable"] == 0
    mid = high["sub_mid_dn_revert"]
    assert mid["n_emitted"] == 268
    assert mid["cost_authority_complete"] == 155
    assert mid["cost_authority_not_evaluable"] == 113
    assert mid["spread_floor_survivors"] == 35
    assert mid["spread_floor_refused"] == 233
    assert mid["conditional_survivor_evaluable"] == 8


def test_each_band_summary_has_unconditional_and_conditional_hash_bound_economics():
    result = json.loads(W.OUT_RESULT.read_text())
    assert result["headline_status"] == "W7_NOT_EVALUABLE_HIGHER_INFORMATION_STOP"
    assert result["headline_eligible"] is False
    assert result["shared_repair_dependency"]["locally_duplicated_repairs"] == []
    for account in result["accounts"].values():
        assert account["current_mid_band"]["final_post_integration_headline"] is False
        for band in W.BANDS:
            for row in account["bands"][band].values():
                assert row["n_emitted"] == (
                    row["cost_authority_complete"] + row["cost_authority_not_evaluable"]
                )
                assert row["n_emitted"] == (
                    row["quote_authority_modelled"] + row["quote_authority_not_evaluable"]
                )
                assert row["quote_authority_complete"] == 0
                assert row["headline_eligible"] is False
                assert row["spread_floor_survivors"] >= row["conditional_survivor_evaluable"]
                assert "unconditional_roster" in row
                assert "conditional_survivor_economics" in row
                for src in row["unconditional_roster"]["source_hash_class_records"]:
                    assert len(src["sha256"]) == 64
                    assert len(src["sidecar_sha256"]) == 64
                for component in ("commission_r", "swap_r", "spread_r", "slippage_r"):
                    coverage = row["unconditional_roster"][
                        "component_costs_all_emitted_with_not_evaluable_explicit"
                    ][component]["coverage"]
                    assert set(coverage) == set(W.COVERAGE_CLASSES)


def test_source_gaps_are_explicit_not_evaluable_requirements():
    result = json.loads(W.OUT_RESULT.read_text())
    missing = [r for r in result["source_gaps"] if r["source_status"] == "MISSING_SOURCE"]
    assert missing
    assert all("source" in r["reason"] for r in missing)
    assert all(r["full_window_candidate_emissions"] is None for r in missing)
    assert all(
        r["candidate_occurrence_completeness"]
        == "NOT_EVALUABLE_MISSING_SOURCE_UNKNOWN_NOT_ZERO"
        for r in missing
    )


def test_source_cell_ledger_preserves_roster_without_inventing_calendar_completeness():
    result = json.loads(W.OUT_RESULT.read_text())
    with W.OUT_SOURCE_CELLS.open() as fh:
        cells = [json.loads(line) for line in fh if line.strip()]
    expected = {
        (namespace, sleeve, symbol)
        for namespace in W.declared_arming()
        for sleeve in W.armed_sleeves(namespace)
        for symbol in W.SURFACE[sleeve]
    }
    actual = {
        (row["namespace"], row["sleeve"], row["symbol_canonical"])
        for row in cells
    }
    assert len(cells) == len(actual)
    assert actual == expected
    assert all(row["nominal_window_calendar_days_inclusive"] == W.CALENDAR_DAYS for row in cells)
    assert all(
        row["calendar_schedule_authority_status"]
        == "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
        for row in cells
    )
    assert all(row["calendar_denominator_claimed_unconditional"] is False for row in cells)
    assert all(
        row["observed_candidate_emissions"] == 0
        for row in cells
        if row["source_status"] == "LOADED_OBSERVED_ROWS_NO_EMISSION"
    )
    assert all(
        row["full_window_candidate_emissions"] is None
        for row in cells
        if row["profile_support_status"] == "SUPPORTED"
    )
    assert result["source_cell_ledger"]["sha256"] == W.sha256_path(W.OUT_SOURCE_CELLS)


def test_exact_supported_gaps_propagate_to_every_corresponding_result_level():
    result = json.loads(W.OUT_RESULT.read_text())
    missing = [r for r in result["source_gaps"] if r["source_status"] == "MISSING_SOURCE"]
    counts = {}
    for namespace in W.declared_arming():
        counts[namespace] = sum(row["namespace"] == namespace for row in missing)
    assert counts == {
        "operator_profile": 7,
        "redacted_account_live_bee34003": 3,
    }
    for row in missing:
        account = result["accounts"][row["namespace"]]
        assert account["evaluation_status"] == "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP"
        for band in W.BANDS:
            assert account["band_status"][band]["evaluation_status"] == (
                "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP"
            )
            sleeve = account["bands"][band][row["sleeve"]]
            assert sleeve["evaluation_status"] == "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP"
            assert sleeve["headline_eligible"] is False
    assert result["aggregate_evaluation"] == {
        "evaluation_status": "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP",
        "headline_eligible": False,
        "missing_supported_source_cells": 10,
        "stream_schedule_status": "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND",
        "numeric_scope": "OBSERVED_SOURCE_ROWS_PARTIAL_DIAGNOSTIC_ONLY",
    }


def test_a_single_supported_missing_cell_adversarially_forces_sleeve_ne():
    cell = {
        "source_cell_id": "ns::crypto::BTCUSD",
        "profile_support_status": "SUPPORTED",
        "source_status": "MISSING_SOURCE",
        "symbol_canonical": "BTCUSD",
        "observed_candidate_emissions": None,
        "full_window_candidate_emissions": None,
        "exact_requirement": "exact committed source",
    }
    doc = W._sleeve_summary([], [cell])
    assert doc["evaluation_status"] == "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP"
    assert doc["headline_eligible"] is False
    assert doc["source_cell_denominators"]["full_window_candidate_emissions"] is None
    assert doc["source_cell_denominators"][
        "unknown_full_window_candidate_count_is_not_zero"
    ] is True


def test_loaded_zero_observed_emissions_never_becomes_full_window_no_op():
    cell = {
        "source_cell_id": "ns::crypto::BTCUSD",
        "profile_support_status": "SUPPORTED",
        "source_status": "LOADED_OBSERVED_ROWS_NO_EMISSION",
        "symbol_canonical": "BTCUSD",
        "observed_candidate_emissions": 0,
        "full_window_candidate_emissions": None,
        "exact_requirement": None,
    }
    doc = W._sleeve_summary([], [cell])
    assert doc["evaluation_status"] == "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
    assert doc["source_cell_denominators"]["observed_loaded_candidate_emissions"] == 0
    assert doc["source_cell_denominators"]["full_window_candidate_emissions"] is None
    assert doc["headline_eligible"] is False


def test_native_w7_graph_and_execution_packet_shim_boundary_are_explicit():
    result = json.loads(W.OUT_RESULT.read_text())
    truth = result["native_flow_truth"]
    assert truth["overall_status"] == "NOT_EVALUABLE_NATIVE_GRAPH_INCOMPLETE"
    statuses = {row["stage"]: row["status"] for row in truth["stages"]}
    assert statuses["production sleeve Generator"] == (
        "RECOMPUTED_DIRECT_GENERATOR_ON_OBSERVED_ROWS_"
        "RUNTIME_SLOT_CONSERVATION_NOT_EVALUABLE"
    )
    assert statuses["admission.admit_and_size"] == "NOT_EVALUABLE_HISTORICAL_STATE_MISSING"
    assert statuses["BookOwner router/risk/trade parameters"] == (
        "NOT_EVALUABLE_HISTORICAL_STATE_MISSING"
    )
    shims = truth["execution_packet_selector_scheduler_fields"]
    assert shims["status"] == "COMPATIBILITY_SHIMS_NOT_SHARED_DECISIONS"
    assert shims["selector_v4_decision_measured"] is False
    assert shims["scheduler_v4_decision_measured"] is False
    slot_conservation = truth["production_wrapper_slot_conservation"]
    assert slot_conservation["status"] == (
        "NOT_EVALUABLE_NO_TYPED_DECISION_ORDINAL_TERMINALS"
    )
    assert slot_conservation[
        "full_scheduled_or_native_wrapper_opportunity_denominator_complete"
    ] is False
    admission = next(
        row for row in truth["stages"] if row["stage"] == "admission.admit_and_size"
    )
    assert "first-fit-descending" in admission["evidence"]
    assert "does not transfer" in admission["evidence"]


def test_local_and_host_runtime_surfaces_diverge_without_live_parity_claim():
    result = json.loads(W.OUT_RESULT.read_text())
    parity = result["native_flow_truth"]["runtime_parity"]
    for namespace in ("operator_profile", "redacted_account_live_bee34003"):
        doc = parity[namespace]
        assert doc["live_parity_claimed"] is False
        assert doc["effective_registry_matches"] is False
        assert doc["local_committed_surface"]["include_clean3"] is False
        assert doc["local_committed_surface"][
            "effective_registry_intersection"
        ] == ["crypto", "energy_agri"]
        assert doc["latest_durable_host_observation"]["include_clean3"] is True
        assert doc["latest_durable_host_observation"][
            "effective_registry_intersection"
        ] == [
            "crypto", "energy_agri", "sub_mid_dn_revert", "sub_xvol_pullback",
        ]
    assert parity["operator_profile"]["frontier_exit_selection_matches"] is False
    assert parity["operator_profile"]["local_committed_surface"][
        "frontier_exits"
    ] == []
    assert parity["operator_profile"]["latest_durable_host_observation"][
        "frontier_exits"
    ] == ["crypto"]
    assert parity["redacted_account_live_bee34003"][
        "frontier_exit_selection_matches"
    ] is True


def test_sleeve_scorecard_preserves_partial_diagnostics_and_fail_closed_dispositions():
    result = json.loads(W.OUT_RESULT.read_text())
    scorecard = result["sleeve_scorecard"]
    assert scorecard["schema"] == W.SLEEVE_SCORECARD_SCHEMA
    assert scorecard["headline_eligible"] is False
    assert scorecard["arming_or_composition_change_authorized"] is False
    assert scorecard["allowed_recommendations"] == list(W.SCORECARD_RECOMMENDATIONS)
    assert scorecard["recommendation_counts"] == {
        "KEEP": 0,
        "REPAIR": 0,
        "RESEARCH_ONLY": 4,
        "NE": 4,
    }
    assert len(scorecard["rows"]) == 8
    for card in scorecard["rows"]:
        missing = card["missing_supported_source_cells"]
        assert card["headline_eligible"] is False
        assert card["native_graph_status"] == "NOT_EVALUABLE_NATIVE_GRAPH_INCOMPLETE"
        assert card["arming_or_composition_change_authorized"] is False
        assert card["emissions_activity"]["full_window_candidate_emissions"] is None
        assert card["emissions_activity"][
            "full_window_candidate_count_unknown_not_zero"
        ] is True
        assert card["coherent_source_coverage"][
            "calendar_denominator_claimed_unconditional"
        ] is False
        exit_mismatch = not card["runtime_parity"][
            "exit_contract_matches_latest_host_observation"
        ]
        if missing or exit_mismatch:
            assert card["recommendation"] == "NE"
        else:
            assert card["recommendation"] == "RESEARCH_ONLY"
        if missing:
            assert card["evaluation_status"] == "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP"
        else:
            assert card["evaluation_status"] == "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
        for band in W.BANDS:
            diag = card["modelled_gross_net_diagnostics_by_band"][band]
            assert diag["quote_lifecycle_coverage"] == "MODELLED"
            assert diag["numeric_scope"] == (
                "OBSERVED_SOURCE_ROWS_PARTIAL_DIAGNOSTIC_ONLY"
            )
            assert diag["observed_emitted"] == card["emissions_activity"][
                "observed_scored_rows_by_band"
            ][band]


def test_no_scorecard_row_promotes_partial_loaded_rows_to_keep_or_repair():
    result = json.loads(W.OUT_RESULT.read_text())
    recommendations = {
        row["recommendation"] for row in result["sleeve_scorecard"]["rows"]
    }
    assert recommendations == {"NE", "RESEARCH_ONLY"}
