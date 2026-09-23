"""Behavioural tests for the B7.5 diagnostic-pool reader (Session AW, B1751).

These run on synthetic ledgers written to tmp_path, so they pass on a machine that does
not hold the 7.6 GB sealed arms. The seal comparison against the real ledgers is a
separate, machine-bound receipt (`AW_POOL_SEAL_V1.json`) — a test that needs a 7.6 GB
file in another worktree would be a test nobody can run.
"""

from __future__ import annotations

import gzip
import json

import pytest

from src.research_infra import b7_5_diagnostic_pool as DP


def _row(**over):
    """A minimally complete diagnostic-scoreable ledger row."""

    row = {
        "canonical_replay_candidate_instance_key": "cand_a@@2026-01-02T00:15:00+00:00",
        "candidate_id": "cand_a",
        "decision_window_id": "timewarp:2026-01-02T00:15:00+00:00",
        "candidate_set_id": "set:2026-01-02T00:15:00+00:00",
        "stable_decision_window_id": "decision_window:AUDJPY:LONG:2026-01-02T00:15:00+00:00",
        "decision_time_utc": "2026-01-02T00:15:00+00:00",
        "trading_day": "2026-01-02",
        "split": "development",
        "chunk_id": "chunk-1",
        "symbol": "AUDJPY",
        "direction": "LONG",
        "origin_family": "liquidity_sweep_reclaim",
        "framework": "origin_liquidity_sweep_reclaim",
        "session_bucket": "tokyo",
        "utc_hour_bucket": "h00_01",
        "spread_r": 0.16,
        "cost_r": 0.18,
        "commission_r": 0.0,
        "swap_cost_r": 0.0,
        "candidate_probability": 0.83,
        "candidate_ev_r": 1.04,
        "candidate_confidence": 0.55,
        "entry_price": 100.0,
        "stop_loss": 99.0,
        "take_profit_1": 102.0,
        "policy_target_r": 2.0,
        "candidate_decision_quality": {
            "entry_quality_fill_probability": 0.90,
            "execution_fill_probability": 0.92,
            "limit_fillability_probability": 0.92,
        },
        "missed_opportunity_non_executable_diagnostic_scoreable": True,
        "missed_opportunity_r_scoreability_status": "diagnostic_opportunity_r_scoreable",
        "opportunity_net_proxy_r": -1.18,
        "opportunity_gross_r": -1.0,
        "opportunity_close_reason": "stop_reached_before_target",
        "terminal_outcome": "stop_reached_before_target",
        "counterfactual_order_close_time_utc": "2026-01-02T02:15:00+00:00",
    }
    row.update(over)
    return row


def _write(path, rows):
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


@pytest.fixture()
def arm(tmp_path):
    spec = DP.ArmSpec("S0R0", "JANUARY_2026", "PFX")
    (tmp_path / "PFX_MISSED_OPPORTUNITY_LEDGER.jsonl")  # path shape documented by the spec
    return spec, tmp_path


# --- projection -------------------------------------------------------------------------


def test_project_reads_nested_payload_and_derives_geometry():
    out = DP.project(_row(), arm=DP.ARMS["S0R0"])
    assert out["execution_fill_probability"] == 0.92
    assert out["entry_quality_fill_probability"] == 0.90
    assert out["stop_distance_frac"] == pytest.approx(0.01)
    assert out["rr_ratio"] == pytest.approx(2.0)
    assert out["cost_over_rr"] == pytest.approx(0.09)
    assert out["ev_minus_cost"] == pytest.approx(0.86)
    assert out["decision_hour_utc"] == 0.0
    assert out["decision_dow"] == 4.0  # 2026-01-02 is a Friday
    assert out["outcome_hold_hours"] == pytest.approx(2.0)


def test_f31_is_charged_on_level_exits_and_not_on_mark_exits():
    level = DP.project(_row(), arm=DP.ARMS["S0R0"])
    assert level["outcome_is_level_exit"] is True
    assert level["outcome_net_proxy_r_f31"] == pytest.approx(
        -1.18 + DP.F31_GAP_THROUGH_R_PER_LEVEL_EXIT_ROW
    )
    mark = DP.project(
        _row(terminal_outcome="path_end_mark_to_market"), arm=DP.ARMS["S0R0"]
    )
    assert mark["outcome_is_level_exit"] is False
    assert mark["outcome_net_proxy_r_f31"] == pytest.approx(-1.18)
    assert DP.F31_GAP_THROUGH_R_PER_LEVEL_EXIT_ROW < 0, "F31 is adverse; sign matters"


def test_feature_names_carry_no_outcome_column():
    assert not [n for n in DP.FEATURE_NAMES if n.startswith("outcome_")]
    assert "outcome_net_proxy_r" in DP.OUTCOME_NAMES
    assert "outcome_net_proxy_r_f31" in DP.OUTCOME_NAMES
    # identity columns are not offered as features either
    for ident in ("candidate_id", "candidate_instance_key", "trading_day"):
        assert ident not in DP.FEATURE_NAMES


def test_projection_names_are_unique():
    names = [f.name for f in DP.PROJECTION + DP.DERIVED + DP.OUTCOME_PROJECTION]
    assert len(names) == len(set(names))


# --- the predicate and the byte prefilter -------------------------------------------------


def test_diagnostic_predicate_matches_the_analyzer():
    assert DP.is_diagnostic_scoreable(_row()) is True
    assert (
        DP.is_diagnostic_scoreable(
            _row(
                missed_opportunity_non_executable_diagnostic_scoreable=False,
                missed_opportunity_r_scoreability_status="diagnostic_opportunity_r_scoreable",
            )
        )
        is True
    )
    assert (
        DP.is_diagnostic_scoreable(
            _row(
                missed_opportunity_non_executable_diagnostic_scoreable=False,
                missed_opportunity_r_scoreability_status="path_auditable_r_unscoreable",
            )
        )
        is False
    )


def test_prefilter_and_full_parse_agree_row_for_row(tmp_path):
    """The prefilter is an optimisation. If it ever drops a row the pool is wrong."""

    rows = [
        _row(canonical_replay_candidate_instance_key="a"),
        _row(
            canonical_replay_candidate_instance_key="b",
            missed_opportunity_non_executable_diagnostic_scoreable=False,
            missed_opportunity_r_scoreability_status="path_auditable_r_unscoreable",
            opportunity_net_proxy_r=None,
        ),
        _row(canonical_replay_candidate_instance_key="c", opportunity_net_proxy_r=1.5),
        _row(
            canonical_replay_candidate_instance_key="d",
            missed_opportunity_non_executable_diagnostic_scoreable=False,
            opportunity_net_proxy_r=0.0,
        ),
    ]
    spec = DP.ArmSpec("S0R0", "JANUARY_2026", "PFX")
    _write(tmp_path / "PFX_MISSED_OPPORTUNITY_LEDGER.jsonl", rows)

    fast = [r["candidate_instance_key"] for r in DP.iter_arm_rows(spec, root=tmp_path)]
    slow = [
        r["candidate_instance_key"]
        for r in DP.iter_arm_rows(spec, root=tmp_path, prefilter=False)
    ]
    assert fast == slow == ["a", "c", "d"]


def test_counts_reproduce_the_sealed_field_semantics(tmp_path):
    rows = [
        _row(canonical_replay_candidate_instance_key="a", opportunity_net_proxy_r=-1.18),
        _row(canonical_replay_candidate_instance_key="b", opportunity_net_proxy_r=1.5),
        _row(canonical_replay_candidate_instance_key="c", opportunity_net_proxy_r=0.0),
        _row(
            canonical_replay_candidate_instance_key="d",
            missed_opportunity_non_executable_diagnostic_scoreable=False,
            missed_opportunity_r_scoreability_status="path_auditable_r_unscoreable",
        ),
    ]
    spec = DP.ArmSpec("S0R0", "JANUARY_2026", "PFX")
    _write(tmp_path / "PFX_MISSED_OPPORTUNITY_LEDGER.jsonl", rows)
    counts = DP.ArmCounts()
    list(DP.iter_arm_rows(spec, root=tmp_path, counts=counts))
    assert counts.as_dict() == {
        "rows": 4,
        "diagnostic_scoreable_rows": 3,
        "diagnostic_positive_rows": 1,
        "diagnostic_negative_rows": 1,
        "diagnostic_flat_rows": 1,
        "diagnostic_positive_net_r": 1.5,
        "diagnostic_negative_net_r": -1.18,
    }


def test_duplicate_identity_fails_closed(tmp_path):
    spec = DP.ArmSpec("S0R0", "JANUARY_2026", "PFX")
    _write(tmp_path / "PFX_MISSED_OPPORTUNITY_LEDGER.jsonl", [_row(), _row()])
    with pytest.raises(DP.DiagnosticPoolError, match="missed_identity_duplicate"):
        list(DP.iter_arm_rows(spec, root=tmp_path))


def test_diagnostic_row_without_outcome_fails_closed(tmp_path):
    spec = DP.ArmSpec("S0R0", "JANUARY_2026", "PFX")
    _write(
        tmp_path / "PFX_MISSED_OPPORTUNITY_LEDGER.jsonl",
        [_row(opportunity_net_proxy_r=None)],
    )
    counts = DP.ArmCounts()
    with pytest.raises(DP.DiagnosticPoolError, match="diagnostic_row_without_net_proxy_r"):
        list(DP.iter_arm_rows(spec, root=tmp_path, counts=counts))


def test_missing_ledger_fails_closed(tmp_path):
    spec = DP.ArmSpec("S0R0", "JANUARY_2026", "ABSENT")
    with pytest.raises(DP.DiagnosticPoolError, match="ledger_missing"):
        list(DP.iter_arm_rows(spec, root=tmp_path))


# --- seal comparison -----------------------------------------------------------------------


def test_compare_to_seal_flags_a_drifted_field():
    counts = DP.ArmCounts(
        rows=10, diagnostic_scoreable_rows=4, diagnostic_positive_rows=1,
        diagnostic_negative_rows=3, diagnostic_positive_net_r=1.0,
        diagnostic_negative_net_r=-2.0,
    )
    sealed = {
        "rows": 10, "diagnostic_scoreable_rows": 4, "diagnostic_positive_rows": 2,
        "diagnostic_negative_rows": 3, "diagnostic_flat_rows": 0,
        "diagnostic_positive_net_r": 1.0, "diagnostic_negative_net_r": -2.0,
    }
    out = DP.compare_to_seal("S0R0", counts, sealed)
    assert out["matches_seal"] is False
    assert [m["field"] for m in out["mismatches"]] == ["diagnostic_positive_rows"]


def test_sealed_arm_counts_reads_the_real_audit():
    """The sealed audit IS in this repo, so this one is not synthetic."""

    sealed = DP.sealed_arm_counts()
    assert set(sealed) == {"S0R0", "S0R1", "S1R0", "S1R1"}
    assert sealed["S0R0"]["diagnostic_scoreable_rows"] == 28519
    assert sealed["S0R0"]["diagnostic_positive_rows"] == 8006
    assert sealed["S0R0"]["diagnostic_negative_rows"] == 20513
    assert sealed["S0R0"]["diagnostic_positive_net_r"] == pytest.approx(6916.94750286)
    assert sealed["S0R0"]["diagnostic_negative_net_r"] == pytest.approx(-31400.82177687)


# --- build and summary ----------------------------------------------------------------------


def test_build_pool_writes_and_reloads(tmp_path, monkeypatch):
    spec = DP.ArmSpec("S0R0", "JANUARY_2026", "PFX")
    monkeypatch.setitem(DP.ARMS, "S0R0", spec)
    _write(
        tmp_path / "PFX_MISSED_OPPORTUNITY_LEDGER.jsonl",
        [
            _row(canonical_replay_candidate_instance_key="a", opportunity_net_proxy_r=-1.18),
            _row(canonical_replay_candidate_instance_key="b", opportunity_net_proxy_r=1.5),
        ],
    )
    out = tmp_path / "pool.jsonl.gz"
    manifest = DP.build_pool(
        ["S0R0"], out_path=out, root=tmp_path, audit_path=False
    )
    assert manifest["arms"]["S0R0"]["diagnostic_scoreable_rows"] == 2
    assert manifest["all_arms_match_seal"] is False  # nothing compared
    rows = DP.load_pool(out)
    assert [r["candidate_instance_key"] for r in rows] == ["a", "b"]
    with gzip.open(out, "rt") as handle:
        assert sum(1 for _ in handle) == 2


def test_pool_summary_states_the_breakeven_precision():
    rows = [
        {"outcome_net_proxy_r": 1.0},
        {"outcome_net_proxy_r": 1.0},
        {"outcome_net_proxy_r": -2.0},
    ]
    got = DP.pool_summary(rows)
    assert got["base_rate"] == pytest.approx(2 / 3)
    assert got["mean_positive_r"] == pytest.approx(1.0)
    assert got["mean_negative_r"] == pytest.approx(-2.0)
    # a selector must be right 2/3 of the time to break even at these conditional means
    assert got["breakeven_precision"] == pytest.approx(2 / 3)
    assert got["pool_net_r"] == pytest.approx(0.0)


def test_pool_summary_can_run_on_the_f31_charged_column():
    rows = [
        {"outcome_net_proxy_r": 1.0, "outcome_net_proxy_r_f31": 0.9},
        {"outcome_net_proxy_r": -1.0, "outcome_net_proxy_r_f31": -1.1},
    ]
    raw = DP.pool_summary(rows)
    charged = DP.pool_summary(rows, outcome="outcome_net_proxy_r_f31")
    assert raw["pool_net_r"] == pytest.approx(0.0)
    assert charged["pool_net_r"] == pytest.approx(-0.2)
    assert charged["outcome_column"] == "outcome_net_proxy_r_f31"


def test_arm_registry_covers_the_four_january_arms_and_april():
    assert DP.JANUARY_ARMS == ("S0R0", "S1R0", "S0R1", "S1R1")
    assert set(DP.ARMS) == set(DP.JANUARY_ARMS) | {"APR_S1R1_PARTIAL"}
    april = DP.ARMS["APR_S1R1_PARTIAL"]
    assert april.subdir.startswith("attempt_5_typed_sparse/PHASE_D_APRIL_S1R1_R1_")
    assert april.ledger_path(root="/x").as_posix().endswith(
        "_SOURCE_REPAIRED_R5_CAP_R2_MISSED_OPPORTUNITY_LEDGER.jsonl"
    )
