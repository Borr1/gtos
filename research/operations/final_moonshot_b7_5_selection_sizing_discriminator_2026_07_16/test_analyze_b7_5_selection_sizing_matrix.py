from __future__ import annotations

import copy
import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = Path(__file__).with_name("analyze_b7_5_selection_sizing_matrix.py")
SPEC = importlib.util.spec_from_file_location("matrix_analyzer_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
analyzer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = analyzer
SPEC.loader.exec_module(analyzer)


class FakeVerifier:
    class ExactRelationalCandidateSource:
        def __init__(self, paths: tuple[Path, ...]) -> None:
            self.paths = paths

    def __init__(self, bad_scan: str | None = None) -> None:
        self.bad_scan = bad_scan
        self.calls: list[str] = []

    def __getattr__(self, name: str) -> Any:
        if name in analyzer.SCAN_FUNCTIONS:
            def scan(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
                self.calls.append(name)
                if name == self.bad_scan:
                    return {"bad_counts": {"synthetic_failure": 1}}
                return {"bad_counts": {}, "status": "synthetic_clean"}

            return scan
        if name in analyzer.SUMMARY_ISSUE_FUNCTIONS:
            def issues(*_args: Any, **_kwargs: Any) -> list[str]:
                self.calls.append(name)
                return []

            return issues
        raise AttributeError(name)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def synthetic_hash(seed: str) -> str:
    return analyzer.sha256_bytes(seed.encode("utf-8"))


def synthetic_shared_execution_payload(arm_id: str) -> dict[str, Any]:
    return {
        "schema": "synthetic_shared_execution_contract",
        "arm_id": arm_id,
        "code_authority": [
            {
                "path": analyzer.VERIFIER_CODE_AUTHORITY_PATH,
                "sha256": analyzer.FROZEN_VERIFIER_SHA256,
            }
        ],
        "missing_code_paths": [],
    }


def make_controls(root: Path) -> tuple[Path, Path, analyzer.FrozenBindings]:
    denominator = {
        "initial_equity_cash": 100000.0,
        "fixed_account_risk_unit_pct": 0.1,
        "fixed_account_risk_unit_cash": 100.0,
        "fixed_denominator_portfolio_r_cash": 100.0,
    }
    matched_risk = {
        "same_ex_ante_rules_all_arms": True,
        "daily_accepted_risk_pct_cap": 4.0,
        "peak_open_plus_pending_risk_pct_cap": 4.0,
        "cluster_risk_pct_cap": 1.5,
        "opening_window_risk_pct_cap": 1.0,
        "pending_to_open_transfer_once": True,
        "expiry_or_close_release_once": True,
        "ex_post_rescaling_forbidden": True,
    }
    protocol_path = root / "protocol.json"
    protocol = {
        "schema": "gtos.b7_5.selection_sizing_experiment_protocol.v1",
        "status": "SEALED_BEFORE_IMPLEMENTATION_OUTCOMES_UNREAD",
    }
    write_json(protocol_path, protocol)
    protocol_hash = analyzer.sha256_file(protocol_path)

    contract_path = root / "contract.json"
    contract = {
        "schema": "gtos.b7_5.selection_sizing_decision_contract.v2",
        "status": "SEALED_REPLAY_FREE_DECISION_CONTRACT_VALID",
        "valid": True,
        "replay_free_builder": True,
        "run_campaign_call_count": 0,
        "outcome_ledger_read_count": 0,
        "outcome_artifact_read_count": 0,
        "march_outcome_read": False,
        "denominator": denominator,
        "matched_risk": matched_risk,
        "factorial_contract": {
            "attribution": {
                "selection": "S1R0-S0R0",
                "sizing": "S0R1-S0R0",
                "interaction": "S1R1-S1R0-S0R1+S0R0",
                "total_incumbent_value": "S1R1-S0R0",
            }
        },
        "self_hash": {
            "algorithm": "sha256",
            "canonicalization": "synthetic",
            "excluded_path": "self_hash.sha256",
        },
    }
    contract_self_hash = analyzer.stable_sha256(contract)
    contract["self_hash"]["sha256"] = contract_self_hash
    write_json(contract_path, contract)
    contract_file_hash = analyzer.sha256_file(contract_path)

    frozen = analyzer.FrozenBindings(
        source_plan_sha256=synthetic_hash("source-plan"),
        contract_file_sha256=contract_file_hash,
        contract_self_hash_sha256=contract_self_hash,
        common_execution_input_sha256=synthetic_hash("common-input"),
        protocol_file_sha256=protocol_hash,
        protocol_economics_digest_sha256=synthetic_hash("economics"),
        neutral_selection_seed_sha256=synthetic_hash("neutral-seed"),
        arm_fingerprints={arm: synthetic_hash(f"fingerprint-{arm}") for arm in analyzer.ARM_ORDER},
        binding_payloads={arm: synthetic_hash(f"binding-{arm}") for arm in analyzer.ARM_ORDER},
        shared_execution_contracts={
            arm: analyzer.stable_sha256(synthetic_shared_execution_payload(arm))
            for arm in analyzer.ARM_ORDER
        },
        denominator=denominator,
        matched_risk=matched_risk,
        expected_candidate_count=2,
        expected_decision_count=1,
        expected_scorecard_count=1,
        expected_symbol_count=1,
        expected_profile="synthetic_profile",
    )
    return protocol_path, contract_path, frozen


def arm_binding(arm_id: str, frozen: analyzer.FrozenBindings) -> dict[str, Any]:
    selection, sizing, selection_mode, sizing_mode = analyzer.arm_factors(arm_id)
    return {
        "valid": True,
        "arm_id": arm_id,
        "arm_fingerprint_sha256": frozen.arm_fingerprints[arm_id],
        "binding_payload_sha256": frozen.binding_payloads[arm_id],
        "common_execution_input_digest_sha256": frozen.common_execution_input_sha256,
        "decision_contract_sha256": frozen.contract_self_hash_sha256,
        "protocol_economics_digest_sha256": frozen.protocol_economics_digest_sha256,
        "neutral_selection_seed_sha256": frozen.neutral_selection_seed_sha256,
        "selection_factor": selection,
        "sizing_factor": sizing,
        "selection_mode": selection_mode,
        "sizing_mode": sizing_mode,
        "denominator": dict(frozen.denominator),
        "matched_risk": dict(frozen.matched_risk),
        "uses_outcome_fields": False,
        "broker_mutation_enabled": False,
        "live_broker_authority": False,
        "final_selection_claim": False,
    }


def summary_payload(
    arm_id: str,
    prefix: str,
    frozen: analyzer.FrozenBindings,
    *,
    risk_cash: float,
    risk_pct: float,
) -> dict[str, Any]:
    pnl_cash = risk_cash * 0.1
    lifecycle = {
        "required": True,
        "valid": True,
        "status": "factorial_risk_lifecycle_contract_valid",
        "arm_id": arm_id,
        "matched_risk": dict(frozen.matched_risk),
        "failure_count": 0,
        "failures": [],
        "accepted_order_count": 1,
        "pending_to_open_transfer_count": 1,
        "close_or_expiry_event_count": 1,
        "close_or_expiry_release_count": 1,
        "peak_daily_accepted_risk_pct": risk_pct,
        "peak_open_plus_pending_risk_pct": risk_pct,
        "peak_opening_window_risk_pct": risk_pct,
        "peak_cluster_risk_pct": {"synthetic": risk_pct},
        "terminal_daily_accepted_risk_pct": 0.0,
        "terminal_pending_risk_pct": 0.0,
        "terminal_open_risk_pct": 0.0,
        "uses_outcome_fields_for_selection_or_sizing": False,
        "broker_mutation_enabled": False,
        "live_broker_authority": False,
    }
    return {
        "schema": "synthetic_summary",
        "status": "broad_live_as_if_replay_materialized_broker_live_closed",
        "output_prefix": prefix,
        "date_start": "2026-06-04",
        "date_end": "2026-06-04",
        "configured_symbol_count": 1,
        "active_replay_symbol_count": 1,
        "candidate_rows": 2,
        "scorecard_rows": 1,
        "order_rows": 2,
        "trade_rows": 1,
        "missed_opportunity_rows": 1,
        "candidate_ledger_omitted": True,
        "candidate_index_ledger_omitted": True,
        "packet_sidecar_ledger_omitted": True,
        "broker_mutation_enabled": False,
        "live_broker_authority": False,
        "final_selection_claim": False,
        "order_send_attempts": 0,
        "profiles": ["synthetic_profile"],
        "ledger_write_row_counts": {
            "source": 1,
            "decision": 1,
            "scorecard": 1,
            "order": 2,
            "trade": 1,
            "missed": 1,
            "oracle": 1,
            "bucket": 1,
            "comparison": 0,
        },
        "b7_5_contract_binding": {
            "valid": True,
            "expected_source_plan_digest_sha256": frozen.source_plan_sha256,
            "actual_source_plan_digests_sha256": [frozen.source_plan_sha256],
            "expected_shared_execution_contract_digest_sha256": frozen.shared_execution_contracts[arm_id],
            "actual_shared_execution_contract_digest_sha256": frozen.shared_execution_contracts[arm_id],
        },
        "b7_5_selection_sizing_factorial_arm_binding": arm_binding(arm_id, frozen),
        "b7_5_selection_sizing_factorial_risk_lifecycle": lifecycle,
        "shared_execution_contract": {
            **synthetic_shared_execution_payload(arm_id),
            "valid": True,
            "status": "shared_execution_contract_bound",
            "shared_execution_contract_digest_sha256": frozen.shared_execution_contracts[arm_id],
        },
        "split_profile_stats": [
            {
                "profile": "synthetic_profile",
                "decision_rows": 1,
                "headline_net_r": 0.1,
                "physical_risk_cash": risk_cash,
                "physical_risk_pct": risk_pct,
                "physical_scoreable_trade_rows": 1,
                "physical_unscoreable_trade_rows": 0,
                "physical_cash_pnl": pnl_cash,
                "physical_net_r": 0.1,
                "physical_gross_r": 0.12,
                "physical_expected_cost_r": 0.02,
                "physical_stress": {
                    "raw_net_r": 0.1,
                    "trade_count": 1,
                    "guarded_stress_rows": [
                        {
                            "stress_id": "extra_cost_0.05r_per_trade",
                            "net_r": 0.05,
                            "min_trade_r": 0.05,
                            "loss_count": 0,
                        },
                        {
                            "stress_id": "extra_cost_0.10r_per_trade",
                            "net_r": 0.0,
                            "min_trade_r": 0.0,
                            "loss_count": 0,
                        },
                        {
                            "stress_id": "extra_cost_0.20r_per_trade",
                            "net_r": -0.1,
                            "min_trade_r": -0.1,
                            "loss_count": 1,
                        },
                    ],
                },
            }
        ],
    }


def make_arm(
    root: Path,
    arm_id: str,
    prefix: str,
    frozen: analyzer.FrozenBindings,
) -> None:
    fixed = arm_id.endswith("R0")
    risk_cash = 100.0 if fixed else 200.0
    risk_pct = 0.1 if fixed else 0.2
    flat = analyzer.expected_flat_binding(arm_id, frozen)
    paths = analyzer.namespace_paths(root, prefix)
    write_json(paths["summary"], summary_payload(arm_id, prefix, frozen, risk_cash=risk_cash, risk_pct=risk_pct))
    write_json(
        paths["partial_summary"],
        {
            "schema": analyzer.COMPLETED_PARTIAL_SUMMARY_SCHEMA,
            "output_prefix": prefix,
            "partial_summary_semantics": (
                "synthetic_salvage_checkpoint_"
                + analyzer.COMPLETED_PARTIAL_SUMMARY_SEMANTICS_SUFFIX
            ),
        },
    )
    pool_keys = ["candidate-1"]
    rows = {
        "source": [{**flat, "symbol": "TEST"}],
        "decision": [{**flat, "decision_time_utc": "2026-06-04T10:00:00+00:00"}],
        "scorecard": [
            {
                **flat,
                "decision_window_id": "window-1",
                "selected_candidate_instance_key": "candidate-1",
                "selected_scheduler_canonical_replay_candidate_instance_key": (
                    "candidate-1"
                ),
                "selected_scheduler_selected_candidate_instance_key": "candidate-1",
                "risk_admitted_scheduler_finalizer": {
                    "b7_5_selection_sizing_factorial_decision_window_id": "window-1",
                    "b7_5_selection_sizing_factorial_hard_eligible_pool_count": 1,
                    "b7_5_selection_sizing_factorial_hard_eligible_instance_keys": pool_keys,
                    "b7_5_selection_sizing_factorial_hard_eligible_pool_digest_sha256": analyzer.stable_sha256(pool_keys),
                },
            }
        ],
        "order": [
            {
                **flat,
                "canonical_replay_candidate_instance_key": "candidate-1",
                "simulated_order_id": "order-1",
                "decision_window_id": "window-1",
                "order_event_stage": "accepted_pending",
                "order_status": "pending_accepted",
                "risk_cash": risk_cash,
                "risk_pct": risk_pct,
                "reserved_risk_pct": risk_pct,
            },
            {
                **flat,
                "canonical_replay_candidate_instance_key": "candidate-1",
                "simulated_order_id": "order-1",
                "decision_window_id": "window-1",
                "order_event_stage": "terminal_filled",
                "order_status": "filled",
                "fill_status": "filled",
                "risk_cash": risk_cash,
                "risk_pct": risk_pct,
            },
        ],
        "trade": [
            {
                **flat,
                "canonical_replay_candidate_instance_key": "candidate-1",
                "simulated_order_id": "order-1",
                "simulated_trade_id": "trade-1",
                "risk_cash": risk_cash,
                "risk_pct": risk_pct,
                "net_proxy_r": 0.1,
                "gross_r": 0.12,
                "expected_cost_r": 0.02,
                "pnl_cash": risk_cash * 0.1,
                "exit_time_utc": "2026-06-04T11:00:00+00:00",
            }
        ],
        "missed": [
            {
                **flat,
                "canonical_replay_candidate_instance_key": "candidate-2",
                "missed_opportunity_r_scoreability_status": "diagnostic_opportunity_r_scoreable",
                "missed_opportunity_non_executable_diagnostic_scoreable": True,
                "missed_opportunity_headline_r_scoreable": False,
                "opportunity_net_proxy_r": 0.5,
                "net_proxy_r": None,
                "gross_r": None,
                "pnl_cash": None,
            }
        ],
        "oracle": [{**flat, "simulated_trade_id": "trade-1"}],
        "bucket": [{**flat, "bucket": "synthetic"}],
        "comparison": [],
    }
    for kind, ledger_rows in rows.items():
        write_jsonl(paths[kind], ledger_rows)


def make_config(tmp_path: Path) -> analyzer.AnalyzerConfig:
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    protocol, contract, frozen = make_controls(tmp_path)
    prefixes = {arm: f"SYNTHETIC_{arm}" for arm in analyzer.ARM_ORDER}
    for arm in analyzer.ARM_ORDER:
        make_arm(artifact_root, arm, prefixes[arm], frozen)
    return analyzer.AnalyzerConfig(
        artifact_root=artifact_root,
        protocol_path=protocol,
        contract_path=contract,
        output_path=tmp_path / "matrix_audit.json",
        prefixes=prefixes,
        frozen=frozen,
    )


def mutate_json(path: Path, mutator: Any) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutator(payload)
    write_json(path, payload)


def mutate_jsonl(path: Path, mutator: Any) -> None:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    mutator(rows)
    write_jsonl(path, rows)


def failure_codes(audit: dict[str, Any]) -> set[str]:
    return {row["code"] for row in audit["failures"]}


def relational_failure_reasons(
    audit: dict[str, Any],
    arm_id: str,
) -> set[str]:
    return {
        failure["reason"]
        for failure in audit["arms"][arm_id][
            "candidate_scorecard_order_fill_identity"
        ]["failures"]
    }


def completed_s0r0_surface(*, root: Path | None = None) -> analyzer.ArmSurface:
    source_paths = analyzer.namespace_paths(
        analyzer.DENOMINATOR_ROUTE,
        analyzer.DEFAULT_PREFIXES["S0R0"],
    )
    if root is None:
        paths = source_paths
    else:
        paths = {
            "order": root / "S0R0_ORDER_LEDGER.jsonl",
            "trade": root / "S0R0_TRADE_LEDGER.jsonl",
        }
        for ledger_name in ("order", "trade"):
            paths[ledger_name].write_bytes(source_paths[ledger_name].read_bytes())
    return analyzer.ArmSurface(
        arm_id="S0R0",
        prefix=analyzer.DEFAULT_PREFIXES["S0R0"],
        summary={},
        paths=paths,
        artifacts={},
    )


def raw_atomicity_scan(surface: analyzer.ArmSurface) -> dict[str, Any]:
    verifier = analyzer.load_verifier()
    return verifier.scan_broad_executable_risk_and_fillability_atomicity(
        {
            "order": surface.paths["order"],
            "trade": surface.paths["trade"],
        }
    )


def mutate_first_order_authority(
    surface: analyzer.ArmSurface,
    mutator: Any,
) -> None:
    def apply(rows: list[dict[str, Any]]) -> None:
        mutator(rows[0], rows[0]["risk_authority"])

    mutate_jsonl(surface.paths["order"], apply)


def rehash_atom(atom: dict[str, Any]) -> None:
    payload = dict(atom)
    payload.pop("atom_hash_sha256", None)
    material = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    atom["atom_hash_sha256"] = analyzer.sha256_bytes(material.encode("utf-8"))


def reconciliation_row_reasons(reconciliation: dict[str, Any]) -> set[str]:
    reasons: set[str] = set()
    for failure in reconciliation["failures"]:
        reasons.update(failure.get("reasons", []))
    return reasons


def test_clean_matrix_is_deterministic_and_calls_exact_verifier_surface(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    verifier = FakeVerifier()
    first = analyzer.build_audit(config, verifier_module=verifier)
    second = analyzer.build_audit(config, verifier_module=FakeVerifier())
    analyzer.namespace_paths(config.artifact_root, config.prefixes["S1R1"])[
        "bucket"
    ].touch()
    after_mtime_only_change = analyzer.build_audit(
        config,
        verifier_module=FakeVerifier(),
    )

    assert first == second
    assert first == after_mtime_only_change
    assert first["valid"] is True
    assert first["status"] == "PASS_TEST_ONLY_NON_PRODUCTION_AUDIT"
    assert first["disposition"]["development_windows_authorized"] is False
    assert first["control_inputs"]["verifier"]["production_audit_authority"] is False
    assert first["control_inputs"]["verifier"][
        "scan_results_attributed_to_frozen_verifier"
    ] is False
    assert analyzer.verify_self_hash(first) is True
    assert config.output_path.exists() is False
    assert set(analyzer.SCAN_FUNCTIONS).issubset(set(verifier.calls))
    assert set(analyzer.SUMMARY_ISSUE_FUNCTIONS).issubset(set(verifier.calls))
    assert first["factorial_effects"]["scalar_effects"][
        "cash_per_accepted_risk_dollar"
    ] == {
        "selection": 0.0,
        "sizing": 0.0,
        "interaction": 0.0,
        "total_incumbent_value": 0.0,
    }

    analyzer.write_audit(config.output_path, first)
    assert analyzer.verify_self_hash(json.loads(config.output_path.read_text())) is True


def test_incomplete_namespace_fails_before_any_artifact_read_or_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = make_config(tmp_path)
    paths = analyzer.namespace_paths(config.artifact_root, config.prefixes["S1R0"])
    paths["summary"].unlink()
    verifier = FakeVerifier()
    artifact_read_attempts: list[Path] = []

    def forbid_artifact_read(path: Path) -> Any:
        artifact_read_attempts.append(path)
        raise AssertionError(f"artifact opened before namespace completeness: {path}")

    monkeypatch.setattr(analyzer, "read_json_object", forbid_artifact_read)

    with pytest.raises(analyzer.IncompleteNamespaceError, match="S1R0:summary:missing"):
        analyzer.build_audit(config, verifier_module=verifier)

    assert artifact_read_attempts == []
    assert verifier.calls == []
    assert config.output_path.exists() is False


def test_check_mode_never_calls_writer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = make_config(tmp_path)
    audit = analyzer.build_audit(config, verifier_module=FakeVerifier())
    args = analyzer.argparse.Namespace(
        artifact_root=config.artifact_root,
        protocol=config.protocol_path,
        decision_contract=config.contract_path,
        output=config.output_path,
        s0r0_prefix=config.prefixes["S0R0"],
        s1r0_prefix=config.prefixes["S1R0"],
        s0r1_prefix=config.prefixes["S0R1"],
        s1r1_prefix=config.prefixes["S1R1"],
        check=True,
    )
    monkeypatch.setattr(analyzer, "parse_args", lambda: args)
    monkeypatch.setattr(analyzer, "build_audit", lambda _config: audit)

    def forbid_write(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("--check attempted to write an audit")

    monkeypatch.setattr(analyzer, "write_audit", forbid_write)

    assert analyzer.main() == 0
    assert config.output_path.exists() is False


def test_partial_preflight_marker_blocks_before_ledgers_or_verifier(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    paths = analyzer.namespace_paths(config.artifact_root, config.prefixes["S0R1"])
    mutate_json(
        paths["partial_summary"],
        lambda payload: payload.update(
            {
                "schema": (
                    "gtos.final_moonshot.broad_live_as_if_replay_harness."
                    "partial_summary.runtime_input_preflight.v1"
                ),
                "partial_summary_semantics": (
                    "runtime_input_preflight_only_run_campaign_not_entered"
                ),
            }
        ),
    )
    verifier = FakeVerifier()

    with pytest.raises(
        analyzer.IncompleteNamespaceError,
        match="S0R1:partial_summary:completion_schema_invalid",
    ):
        analyzer.build_audit(config, verifier_module=verifier)

    assert verifier.calls == []
    assert config.output_path.exists() is False


def test_namespace_mutation_during_verifier_scan_blocks_matrix(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    target = analyzer.namespace_paths(
        config.artifact_root,
        config.prefixes["S0R0"],
    )["trade"]

    class MutatingVerifier(FakeVerifier):
        def __init__(self) -> None:
            super().__init__()
            self.mutated = False

        def __getattr__(self, name: str) -> Any:
            base = super().__getattr__(name)
            if name != "scan_broad_factorial_risk_lifecycle_summary":
                return base

            def scan(*args: Any, **kwargs: Any) -> dict[str, Any]:
                if not self.mutated:
                    target.write_text(
                        target.read_text(encoding="utf-8") + "\n",
                        encoding="utf-8",
                    )
                    self.mutated = True
                return base(*args, **kwargs)

            return scan

    audit = analyzer.build_audit(config, verifier_module=MutatingVerifier())

    assert audit["valid"] is False
    assert "namespace_artifact_mutated_during_audit" in failure_codes(audit)
    assert audit["namespace_stability"]["all_artifacts_stable"] is False


def test_symlinked_namespace_artifact_is_rejected_before_read(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    path = analyzer.namespace_paths(
        config.artifact_root,
        config.prefixes["S1R0"],
    )["bucket"]
    external = tmp_path / "external_bucket.jsonl"
    external.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(external)

    with pytest.raises(analyzer.IncompleteNamespaceError, match="symlink_forbidden"):
        analyzer.build_audit(config, verifier_module=FakeVerifier())


def test_summary_nested_authority_is_blocked(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    path = analyzer.namespace_paths(
        config.artifact_root,
        config.prefixes["S1R1"],
    )["summary"]
    mutate_json(
        path,
        lambda payload: payload.update(
            {
                "synthetic_nested_boundary": {
                    "deployment_authority": True,
                    "broker_live_authority": "true",
                    "broker_send_attempts": 0.5,
                }
            }
        ),
    )

    audit = analyzer.build_audit(config, verifier_module=FakeVerifier())

    assert audit["valid"] is False
    assert "recursive_authority_violation" in failure_codes(audit)


def test_real_verifier_api_loads_without_outcome_access() -> None:
    verifier = analyzer.load_verifier()

    assert all(hasattr(verifier, name) for name in analyzer.SCAN_FUNCTIONS)
    assert all(hasattr(verifier, name) for name in analyzer.SUMMARY_ISSUE_FUNCTIONS)
    assert hasattr(verifier, "ExactRelationalCandidateSource")


def test_fractional_integer_field_is_rejected() -> None:
    with pytest.raises(analyzer.MatrixAuditError, match="integer_missing_or_invalid"):
        analyzer.integer(1.9, label="synthetic_count")


def test_fractional_verifier_bad_count_is_a_recorded_failure(tmp_path: Path) -> None:
    config = make_config(tmp_path)

    class FractionalBadCountVerifier(FakeVerifier):
        def __getattr__(self, name: str) -> Any:
            if name != "scan_broad_order_trade_cost_authority":
                return super().__getattr__(name)

            def scan(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
                self.calls.append(name)
                return {"bad_counts": {"fractional_bad_count": 0.5}}

            return scan

    audit = analyzer.build_audit(
        config,
        verifier_module=FractionalBadCountVerifier(),
    )

    failures = [
        row
        for row in audit["failures"]
        if row["code"] == "verifier_scan_failed"
    ]
    assert audit["valid"] is False
    assert any(
        row["bad_counts"].get("fractional_bad_count")
        == "invalid_non_integer:0.5"
        for row in failures
    )


def test_positive_effect_with_removed_trade_is_nonclaimable(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    paths = analyzer.namespace_paths(config.artifact_root, config.prefixes["S1R0"])

    def replace_trade(rows: list[dict[str, Any]]) -> None:
        row = rows[0]
        row["canonical_replay_candidate_instance_key"] = "candidate-2"
        row["net_proxy_r"] = 0.3
        row["gross_r"] = 0.32
        row["pnl_cash"] = 30.0

    def replace_orders(rows: list[dict[str, Any]]) -> None:
        for row in rows:
            row["canonical_replay_candidate_instance_key"] = "candidate-2"

    def replace_missed(rows: list[dict[str, Any]]) -> None:
        row = rows[0]
        row["canonical_replay_candidate_instance_key"] = "candidate-1"
        row["opportunity_net_proxy_r"] = -0.1

    def replace_summary(summary: dict[str, Any]) -> None:
        stats = summary["split_profile_stats"][0]
        stats["headline_net_r"] = 0.3
        stats["physical_cash_pnl"] = 30.0
        stats["physical_net_r"] = 0.3
        stats["physical_gross_r"] = 0.32

    mutate_jsonl(paths["trade"], replace_trade)
    mutate_jsonl(paths["order"], replace_orders)
    mutate_jsonl(paths["missed"], replace_missed)
    mutate_json(paths["summary"], replace_summary)

    audit = analyzer.build_audit(config, verifier_module=FakeVerifier())

    transition = audit["suppression_and_missed_reconciliation"]["transitions"][
        "selection_at_r0"
    ]
    assert transition["primary_q_delta"] == 0.2
    assert transition["execution_suppression_present"] is True
    assert transition["order_suppression_present"] is True
    assert transition["removed_order_instance_keys"] == ["candidate-1"]
    assert transition["added_order_instance_keys"] == ["candidate-2"]
    assert transition["removed_order_instances"]["order_instance_count"] == 1
    assert transition["removed_order_instances"]["order_event_count"] == 2
    assert transition["removed_trade_to_candidate_missed_reconciliation"][
        "missing_keys"
    ] == []
    assert transition["added_trade_from_baseline_missed_reconciliation"][
        "missing_keys"
    ] == []
    assert audit["factorial_effects"]["primary_classification"]["selection"] == (
        "non_claimable_positive_with_execution_suppression"
    )
    assert "cross_arm_trade_missed_diagnostic_r_mismatch" in failure_codes(audit)


def test_direct_verifier_bad_count_blocks_matrix(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    audit = analyzer.build_audit(
        config,
        verifier_module=FakeVerifier("scan_broad_order_trade_cost_authority"),
    )

    assert audit["valid"] is False
    assert "verifier_scan_failed" in failure_codes(audit)
    assert audit["disposition"]["development_windows_authorized"] is False


def test_absolute_coverage_floor_blocks_matrix(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    prefix = config.prefixes["S0R0"]
    paths = analyzer.namespace_paths(config.artifact_root, prefix)

    def make_trade_unscoreable(rows: list[dict[str, Any]]) -> None:
        rows[0]["net_proxy_r"] = None
        rows[0]["gross_r"] = None
        rows[0]["pnl_cash"] = None

    mutate_jsonl(paths["trade"], make_trade_unscoreable)

    def repair_summary(summary: dict[str, Any]) -> None:
        stats = summary["split_profile_stats"][0]
        stats.update(
            {
                "headline_net_r": 0.0,
                "physical_scoreable_trade_rows": 0,
                "physical_unscoreable_trade_rows": 1,
                "physical_cash_pnl": 0.0,
                "physical_net_r": 0.0,
                "physical_gross_r": 0.0,
            }
        )

    mutate_json(paths["summary"], repair_summary)
    audit = analyzer.build_audit(config, verifier_module=FakeVerifier())

    assert audit["valid"] is False
    assert "arm_scoreable_risk_coverage_below_floor" in failure_codes(audit)
    assert "cross_arm_scoreable_risk_coverage_gap_exceeded" in failure_codes(audit)


def test_selection_pair_hard_pool_mismatch_blocks_matrix(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    paths = analyzer.namespace_paths(config.artifact_root, config.prefixes["S1R0"])

    def change_pool(rows: list[dict[str, Any]]) -> None:
        finalizer = rows[0]["risk_admitted_scheduler_finalizer"]
        finalizer["b7_5_selection_sizing_factorial_hard_eligible_instance_keys"] = [
            "candidate-2"
        ]
        finalizer[
            "b7_5_selection_sizing_factorial_hard_eligible_pool_digest_sha256"
        ] = analyzer.stable_sha256(["candidate-2"])

    mutate_jsonl(paths["scorecard"], change_pool)
    audit = analyzer.build_audit(config, verifier_module=FakeVerifier())

    assert audit["valid"] is False
    assert "selection_pair_hard_pool_mismatch" in failure_codes(audit)


def test_r0_fractional_risk_drift_blocks_matrix(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    paths = analyzer.namespace_paths(config.artifact_root, config.prefixes["S0R0"])

    def drift_trade(rows: list[dict[str, Any]]) -> None:
        rows[0]["risk_cash"] = 90.0
        rows[0]["risk_pct"] = 0.09
        rows[0]["pnl_cash"] = 9.0

    def drift_orders(rows: list[dict[str, Any]]) -> None:
        for row in rows:
            row["risk_cash"] = 90.0
            row["risk_pct"] = 0.09
        rows[0]["reserved_risk_pct"] = 0.09

    def drift_summary(summary: dict[str, Any]) -> None:
        stats = summary["split_profile_stats"][0]
        stats["physical_risk_cash"] = 90.0
        stats["physical_risk_pct"] = 0.09
        stats["physical_cash_pnl"] = 9.0
        lifecycle = summary["b7_5_selection_sizing_factorial_risk_lifecycle"]
        lifecycle["peak_daily_accepted_risk_pct"] = 0.09
        lifecycle["peak_open_plus_pending_risk_pct"] = 0.09
        lifecycle["peak_opening_window_risk_pct"] = 0.09
        lifecycle["peak_cluster_risk_pct"] = {"synthetic": 0.09}

    mutate_jsonl(paths["trade"], drift_trade)
    mutate_jsonl(paths["order"], drift_orders)
    mutate_json(paths["summary"], drift_summary)
    audit = analyzer.build_audit(config, verifier_module=FakeVerifier())

    assert audit["valid"] is False
    assert "r0_trade_risk_cash_not_fixed" in failure_codes(audit)
    assert "r0_trade_risk_pct_not_fixed" in failure_codes(audit)
    assert "r0_accepted_order_risk_not_fixed" in failure_codes(audit)


def test_contract_hash_drift_blocks_without_changing_input_scope(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    frozen = replace(config.frozen, contract_file_sha256=synthetic_hash("wrong-contract"))
    drifted = replace(config, frozen=frozen)
    audit = analyzer.build_audit(drifted, verifier_module=FakeVerifier())

    assert audit["valid"] is False
    assert "decision_contract_file_hash_mismatch" in failure_codes(audit)


def test_production_audit_refuses_injected_verifier_module() -> None:
    with pytest.raises(
        analyzer.MatrixAuditError,
        match="production_verifier_module_injection_forbidden",
    ):
        analyzer.build_audit(
            analyzer.AnalyzerConfig(),
            verifier_module=FakeVerifier(),
        )


def test_summary_verifier_code_authority_tamper_blocks_matrix(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    path = analyzer.namespace_paths(
        config.artifact_root,
        config.prefixes["S0R0"],
    )["summary"]

    def tamper(summary: dict[str, Any]) -> None:
        summary["shared_execution_contract"]["code_authority"][0]["sha256"] = (
            "0" * 64
        )

    mutate_json(path, tamper)
    audit = analyzer.build_audit(config, verifier_module=FakeVerifier())

    assert audit["valid"] is False
    assert "shared_execution_contract_verifier_authority_invalid" in failure_codes(
        audit
    )
    assert "shared_execution_contract_invalid" in failure_codes(audit)


def test_shared_execution_contract_payload_digest_tamper_blocks_matrix(
    tmp_path: Path,
) -> None:
    config = make_config(tmp_path)
    path = analyzer.namespace_paths(
        config.artifact_root,
        config.prefixes["S1R1"],
    )["summary"]
    mutate_json(
        path,
        lambda summary: summary["shared_execution_contract"].update(
            {"synthetic_unhashed_payload_tamper": True}
        ),
    )

    audit = analyzer.build_audit(config, verifier_module=FakeVerifier())
    failures = [
        failure
        for failure in audit["failures"]
        if failure["code"] == "shared_execution_contract_invalid"
        and failure["arm_id"] == "S1R1"
    ]

    assert failures
    assert failures[0]["declared_sha256"] != failures[0]["recomputed_sha256"]


@pytest.mark.parametrize(
    ("tamper_kind", "expected_reason"),
    [
        ("terminal_stage", "terminal_expired_status_invalid"),
        ("trade_order_id", "trade_order_id_transfer_mismatch"),
        ("scorecard_selected", "scorecard_selected_identity_outside_hard_pool"),
        ("duplicate_order_split", "order_accepted_terminal_event_cardinality_invalid"),
    ],
)
def test_candidate_scorecard_order_fill_identity_tamper_fails_closed(
    tmp_path: Path,
    tamper_kind: str,
    expected_reason: str,
) -> None:
    config = make_config(tmp_path)
    paths = analyzer.namespace_paths(
        config.artifact_root,
        config.prefixes["S0R0"],
    )
    if tamper_kind == "terminal_stage":
        mutate_jsonl(
            paths["order"],
            lambda rows: rows[1].update(
                {"order_event_stage": "terminal_expired_unfilled"}
            ),
        )
    elif tamper_kind == "trade_order_id":
        mutate_jsonl(
            paths["trade"],
            lambda rows: rows[0].update({"simulated_order_id": "wrong-order"}),
        )
    elif tamper_kind == "scorecard_selected":
        def tamper_scorecard(rows: list[dict[str, Any]]) -> None:
            for field_name in (
                "selected_candidate_instance_key",
                "selected_scheduler_canonical_replay_candidate_instance_key",
                "selected_scheduler_selected_candidate_instance_key",
            ):
                rows[0][field_name] = "candidate-2"

        mutate_jsonl(paths["scorecard"], tamper_scorecard)
    else:
        mutate_jsonl(
            paths["order"],
            lambda rows: rows[1].update({"simulated_order_id": "order-2"}),
        )

    audit = analyzer.build_audit(config, verifier_module=FakeVerifier())

    assert audit["valid"] is False
    assert "candidate_scorecard_order_fill_identity_invalid" in failure_codes(audit)
    assert expected_reason in relational_failure_reasons(audit, "S0R0")


def test_scoreable_trade_cash_and_summary_collusion_fails_cash_r_identity(
    tmp_path: Path,
) -> None:
    config = make_config(tmp_path)
    paths = analyzer.namespace_paths(
        config.artifact_root,
        config.prefixes["S1R0"],
    )
    mutate_jsonl(
        paths["trade"],
        lambda rows: rows[0].update({"pnl_cash": 20.0}),
    )
    mutate_json(
        paths["summary"],
        lambda summary: summary["split_profile_stats"][0].update(
            {"physical_cash_pnl": 20.0}
        ),
    )

    audit = analyzer.build_audit(config, verifier_module=FakeVerifier())

    assert audit["valid"] is False
    assert "scoreable_trade_cash_r_identity_mismatch" in relational_failure_reasons(
        audit,
        "S1R0",
    )


def test_unscoreable_trade_economic_imputation_fails_closed(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    paths = analyzer.namespace_paths(
        config.artifact_root,
        config.prefixes["S0R1"],
    )
    mutate_jsonl(
        paths["trade"],
        lambda rows: rows[0].update({"net_proxy_r": None}),
    )

    def repair_summary_counts(summary: dict[str, Any]) -> None:
        stats = summary["split_profile_stats"][0]
        stats.update(
            {
                "physical_scoreable_trade_rows": 0,
                "physical_unscoreable_trade_rows": 1,
                "physical_cash_pnl": 0.0,
                "physical_net_r": 0.0,
                "physical_gross_r": 0.0,
                "physical_stress": {
                    "trade_count": 0,
                    "raw_net_r": 0.0,
                    "guarded_stress_rows": [],
                },
            }
        )

    mutate_json(paths["summary"], repair_summary_counts)
    audit = analyzer.build_audit(config, verifier_module=FakeVerifier())

    assert audit["valid"] is False
    assert (
        "unscoreable_trade_economic_imputation_forbidden"
        in relational_failure_reasons(audit, "S0R1")
    )


@pytest.mark.parametrize("tamper_kind", ["missing", "nonfinite", "scenario"])
def test_physical_stress_missing_malformed_or_nonfinite_fails_closed(
    tmp_path: Path,
    tamper_kind: str,
) -> None:
    config = make_config(tmp_path)
    path = analyzer.namespace_paths(
        config.artifact_root,
        config.prefixes["S1R0"],
    )["summary"]

    def tamper(summary: dict[str, Any]) -> None:
        stats = summary["split_profile_stats"][0]
        if tamper_kind == "missing":
            stats.pop("physical_stress")
        elif tamper_kind == "nonfinite":
            stats["physical_stress"]["raw_net_r"] = float("nan")
        else:
            stats["physical_stress"]["guarded_stress_rows"][0]["net_r"] = 9.0

    mutate_json(path, tamper)
    audit = analyzer.build_audit(config, verifier_module=FakeVerifier())

    assert audit["valid"] is False
    assert "physical_stress_contract_invalid" in failure_codes(audit)


def test_physical_stress_contrasts_are_explicit_and_structured(tmp_path: Path) -> None:
    audit = analyzer.build_audit(
        make_config(tmp_path),
        verifier_module=FakeVerifier(),
    )
    stress = audit["factorial_effects"]["physical_stress_effects"]

    assert audit["valid"] is True
    assert stress["raw_net_r"]["contrasts"] == {
        "selection": 0.0,
        "sizing": 0.0,
        "interaction": 0.0,
        "total_incumbent_value": 0.0,
    }
    assert stress["extra_cost_0.20r_per_trade.net_r"]["status"] == (
        "exact_structured_contrast"
    )
    assert stress["extra_cost_0.20r_per_trade.loss_count"]["classification"][
        "selection"
    ] == "flat"


def test_completed_s0r0_fixed_basis_reconciles_exact_real_surface() -> None:
    surface = completed_s0r0_surface()
    raw = raw_atomicity_scan(surface)
    raw_before = copy.deepcopy(raw)

    reconciliation = analyzer.reconcile_r0_fixed_dollar_atomicity(
        surface,
        raw,
        analyzer.DEFAULT_FROZEN,
    )

    assert raw == raw_before
    assert raw["row_counts"] == {
        "order_rows": 12,
        "order_execution_bound_rows": 12,
        "order_atomic_rows_valid": 2,
        "trade_rows": 6,
        "trade_execution_bound_rows": 6,
        "trade_atomic_rows_valid": 1,
    }
    assert raw["bad_counts"] == {
        "order:executable_risk_fillability_atomicity_leak": 10,
        "order:risk_cash_not_bound_to_final_risk_pct": 10,
        "trade:executable_risk_fillability_atomicity_leak": 5,
        "trade:risk_cash_not_bound_to_final_risk_pct": 5,
    }
    assert len(raw["sample_bad"]) == 15
    assert reconciliation["valid"] is True
    assert reconciliation["execution_bound_row_count"] == 18
    assert reconciliation["generic_false_positive_row_count"] == 15
    assert reconciliation["raw_bad_counts"] == raw["bad_counts"]
    assert reconciliation["reconciled_bad_counts"] == raw["bad_counts"]
    assert reconciliation["unreconciled_bad_counts"] == {}
    assert reconciliation["effective_bad_counts"] == {}
    assert reconciliation["failure_count"] == 0
    assert len(reconciliation["execution_row_complete_proof_sha256"]) == 64


def test_verifier_gate_preserves_raw_s0r0_counts_and_has_zero_unreconciled() -> None:
    surface = completed_s0r0_surface()
    raw = raw_atomicity_scan(surface)

    class AtomicityResultVerifier(FakeVerifier):
        def scan_broad_executable_risk_and_fillability_atomicity(
            self,
            _paths: dict[str, Path],
        ) -> dict[str, Any]:
            self.calls.append("scan_broad_executable_risk_and_fillability_atomicity")
            return copy.deepcopy(raw)

    failures: list[dict[str, Any]] = []
    scans, summary_issues = analyzer.run_verifier_scans(
        surface,
        AtomicityResultVerifier(),
        failures,
        analyzer.DEFAULT_FROZEN,
    )
    record = scans[analyzer.EXECUTABLE_RISK_ATOMICITY_SCAN]

    assert failures == []
    assert all(not issues for issues in summary_issues.values())
    assert record["bad_counts"] == raw["bad_counts"]
    assert record["sample_bad"] == raw["sample_bad"]
    assert record["effective_bad_counts"] == {}
    reconciliation = record["r0_fixed_dollar_basis_reconciliation"]
    assert reconciliation["raw_bad_counts"] == raw["bad_counts"]
    assert reconciliation["reconciled_bad_counts"] == raw["bad_counts"]
    assert reconciliation["unreconciled_bad_counts"] == {}


@pytest.mark.parametrize("sample_mode", ["empty", "truncated", "malformed"])
def test_sample_bad_is_diagnostic_only_for_exact_independent_proof(
    sample_mode: str,
) -> None:
    surface = completed_s0r0_surface()
    raw = raw_atomicity_scan(surface)
    if sample_mode == "empty":
        raw["sample_bad"] = []
    elif sample_mode == "truncated":
        raw["sample_bad"] = raw["sample_bad"][:1]
    else:
        raw["sample_bad"] = [{"reasons": ["synthetic_wrong_diagnostic"]}]

    reconciliation = analyzer.reconcile_r0_fixed_dollar_atomicity(
        surface,
        raw,
        analyzer.DEFAULT_FROZEN,
    )

    assert reconciliation["valid"] is True
    assert reconciliation["unreconciled_bad_counts"] == {}
    assert reconciliation["sample_bad_diagnostic_only"][
        "acceptance_dependency"
    ] is False


def tamper_missing_basis_source(row: dict[str, Any], authority: dict[str, Any]) -> None:
    del authority[analyzer.R0_FIXED_CASH_DETAIL_FIELD]["cash_basis_source"]


def tamper_wrong_basis_source(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority[analyzer.R0_FIXED_CASH_DETAIL_FIELD]["cash_basis_source"] = (
        "current_balance"
    )


def tamper_detail_cash(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority[analyzer.R0_FIXED_CASH_DETAIL_FIELD]["risk_cash"] = 99.0


def tamper_detail_pct(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority[analyzer.R0_FIXED_CASH_DETAIL_FIELD][
        "fixed_account_risk_unit_pct"
    ] = 0.2


def tamper_detail_equity(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority[analyzer.R0_FIXED_CASH_DETAIL_FIELD][
        "fixed_account_risk_initial_equity_cash"
    ] = 99999.0


def tamper_detail_arithmetic(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority[analyzer.R0_FIXED_CASH_DETAIL_FIELD][
        "fixed_account_risk_unit_cash"
    ] = 99.0


def tamper_ignored_balance(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority[analyzer.R0_FIXED_CASH_DETAIL_FIELD][
        "fixed_account_risk_current_balance_ignored"
    ] += 1.0


def tamper_fixed_cash_applied(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority[analyzer.R0_FIXED_CASH_DETAIL_FIELD][
        "fixed_equal_account_risk_cash_applied"
    ] = False


def tamper_detail_pct_nan(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority[analyzer.R0_FIXED_CASH_DETAIL_FIELD][
        "fixed_account_risk_unit_pct"
    ] = float("nan")


def tamper_outer_cash_alias(row: dict[str, Any], authority: dict[str, Any]) -> None:
    row["risk_cash"] = 99.0


def tamper_outer_cash_infinite(row: dict[str, Any], authority: dict[str, Any]) -> None:
    row["risk_cash"] = float("inf")


def tamper_nested_risk_cash(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority["risk_cash"] = 99.0


def tamper_nested_order_risk_cash(
    row: dict[str, Any], authority: dict[str, Any]
) -> None:
    authority["order_risk_cash"] = 99.0


def tamper_outer_risk_alias(row: dict[str, Any], authority: dict[str, Any]) -> None:
    row["runtime_final_risk_pct"] = 0.2


def tamper_nested_risk_alias(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority["runtime_final_risk_pct"] = 0.2


def tamper_binding_arm_fingerprint(
    row: dict[str, Any], authority: dict[str, Any]
) -> None:
    authority[analyzer.R0_FACTORIAL_BINDING_FIELD]["arm_fingerprint_sha256"] = (
        "0" * 64
    )


def tamper_binding_arm_id(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority[analyzer.R0_FACTORIAL_BINDING_FIELD]["arm_id"] = "S1R0"


def tamper_binding_common_input(
    row: dict[str, Any], authority: dict[str, Any]
) -> None:
    authority[analyzer.R0_FACTORIAL_BINDING_FIELD][
        "common_execution_input_digest_sha256"
    ] = "0" * 64


def tamper_binding_contract(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority[analyzer.R0_FACTORIAL_BINDING_FIELD]["decision_contract_sha256"] = (
        "0" * 64
    )


def tamper_binding_selection(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority[analyzer.R0_FACTORIAL_BINDING_FIELD]["selection_mode"] = (
        "quality_ranked_current"
    )


def tamper_binding_denominator(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority[analyzer.R0_FACTORIAL_BINDING_FIELD]["denominator"][
        "initial_equity_cash"
    ] = 99999.0


def tamper_binding_matched_risk(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority[analyzer.R0_FACTORIAL_BINDING_FIELD]["matched_risk"][
        "daily_accepted_risk_pct_cap"
    ] = 3.9


def tamper_binding_payload(row: dict[str, Any], authority: dict[str, Any]) -> None:
    binding = authority[analyzer.R0_FACTORIAL_BINDING_FIELD]
    binding["binding_payload"]["selection_mode"] = "quality_ranked_current"
    binding["binding_payload_sha256"] = analyzer.stable_sha256(
        binding["binding_payload"]
    )


def tamper_binding_declared_hash(
    row: dict[str, Any], authority: dict[str, Any]
) -> None:
    authority[analyzer.R0_FACTORIAL_BINDING_FIELD]["binding_payload_sha256"] = (
        "0" * 64
    )


def tamper_atom_fixed_enforced(row: dict[str, Any], authority: dict[str, Any]) -> None:
    atom = authority["canonical_executable_final_risk_atom"]
    atom["b7_5_selection_sizing_factorial_fixed_unit_enforced"] = False
    rehash_atom(atom)


def tamper_atom_hash(row: dict[str, Any], authority: dict[str, Any]) -> None:
    authority["canonical_executable_final_risk_atom"]["atom_hash_sha256"] = (
        "0" * 64
    )


def tamper_atom_fixed_unavailable(
    row: dict[str, Any], authority: dict[str, Any]
) -> None:
    atom = authority["canonical_executable_final_risk_atom"]
    atom["b7_5_selection_sizing_factorial_fixed_unit_unavailable"] = True
    rehash_atom(atom)


@pytest.mark.parametrize(
    ("tamper", "expected_reason"),
    [
        (tamper_missing_basis_source, "r0_fixed_cash_basis_source_mismatch"),
        (tamper_wrong_basis_source, "r0_fixed_cash_basis_source_mismatch"),
        (tamper_detail_cash, "r0_fixed_cash_detail_risk_cash_mismatch"),
        (tamper_detail_pct, "r0_fixed_cash_detail_fixed_account_risk_unit_pct_mismatch"),
        (
            tamper_detail_equity,
            "r0_fixed_cash_detail_fixed_account_risk_initial_equity_cash_mismatch",
        ),
        (tamper_detail_arithmetic, "r0_frozen_basis_arithmetic_mismatch"),
        (tamper_ignored_balance, "r0_current_balance_ignored_provenance_mismatch"),
        (tamper_fixed_cash_applied, "r0_fixed_cash_applied_not_true"),
        (
            tamper_detail_pct_nan,
            "r0_fixed_cash_detail_fixed_account_risk_unit_pct_mismatch",
        ),
        (tamper_outer_cash_alias, "outer_risk_cash_mismatch"),
        (tamper_outer_cash_infinite, "outer_risk_cash_mismatch"),
        (tamper_nested_risk_cash, "nested_risk_cash_mismatch"),
        (tamper_nested_order_risk_cash, "nested_order_risk_cash_mismatch"),
        (tamper_outer_risk_alias, "outer_runtime_final_risk_pct_mismatch"),
        (tamper_nested_risk_alias, "nested_runtime_final_risk_pct_mismatch"),
        (tamper_binding_arm_id, "r0_factorial_binding_arm_id_mismatch"),
        (
            tamper_binding_arm_fingerprint,
            "r0_factorial_binding_arm_fingerprint_sha256_mismatch",
        ),
        (
            tamper_binding_common_input,
            "r0_factorial_binding_common_execution_input_digest_sha256_mismatch",
        ),
        (
            tamper_binding_contract,
            "r0_factorial_binding_decision_contract_sha256_mismatch",
        ),
        (tamper_binding_selection, "r0_factorial_binding_selection_mode_mismatch"),
        (tamper_binding_denominator, "r0_factorial_binding_denominator_mismatch"),
        (tamper_binding_matched_risk, "r0_factorial_binding_matched_risk_mismatch"),
        (tamper_binding_payload, "r0_factorial_binding_payload_mismatch"),
        (
            tamper_binding_declared_hash,
            "r0_factorial_binding_binding_payload_sha256_mismatch",
        ),
        (
            tamper_atom_hash,
            "canonical_final_risk_atom_hash_invalid",
        ),
        (
            tamper_atom_fixed_enforced,
            "canonical_final_risk_atom_fixed_unit_not_enforced",
        ),
        (
            tamper_atom_fixed_unavailable,
            "canonical_final_risk_atom_fixed_unit_unavailable",
        ),
    ],
)
def test_r0_fixed_basis_evidence_tamper_fails_closed(
    tmp_path: Path,
    tamper: Any,
    expected_reason: str,
) -> None:
    surface = completed_s0r0_surface(root=tmp_path)
    mutate_first_order_authority(surface, tamper)
    raw = raw_atomicity_scan(surface)

    reconciliation = analyzer.reconcile_r0_fixed_dollar_atomicity(
        surface,
        raw,
        analyzer.DEFAULT_FROZEN,
    )

    assert reconciliation["valid"] is False
    assert reconciliation["reconciled_bad_counts"] == {}
    assert reconciliation["unreconciled_bad_counts"] == reconciliation[
        "raw_bad_counts"
    ]
    assert expected_reason in reconciliation_row_reasons(reconciliation)


@pytest.mark.parametrize(
    ("tamper_kind", "expected_failure"),
    [
        ("unexpected_nonzero_key", "unexpected_atomicity_bad_count_keys"),
        ("wrong_bad_count", "paired_atomicity_bad_counts_mismatch"),
        ("wrong_row_count", "atomicity_row_counts_mismatch"),
        ("fractional_bad_count", "raw_bad_counts_count_not_exact_integer"),
    ],
)
def test_r0_atomicity_report_tamper_fails_closed(
    tamper_kind: str,
    expected_failure: str,
) -> None:
    surface = completed_s0r0_surface()
    raw = raw_atomicity_scan(surface)
    if tamper_kind == "unexpected_nonzero_key":
        raw["bad_counts"]["order:outer_risk_cash_missing"] = 1
    elif tamper_kind == "wrong_bad_count":
        raw["bad_counts"]["order:risk_cash_not_bound_to_final_risk_pct"] = 9
    elif tamper_kind == "wrong_row_count":
        raw["row_counts"]["order_rows"] = 11
    else:
        raw["bad_counts"]["order:risk_cash_not_bound_to_final_risk_pct"] = 9.5

    reconciliation = analyzer.reconcile_r0_fixed_dollar_atomicity(
        surface,
        raw,
        analyzer.DEFAULT_FROZEN,
    )

    assert reconciliation["valid"] is False
    assert expected_failure in {row["code"] for row in reconciliation["failures"]}
    assert reconciliation["unreconciled_bad_counts"] == reconciliation[
        "raw_bad_counts"
    ]


def test_zero_valued_unexpected_bad_count_key_is_normalized_away() -> None:
    surface = completed_s0r0_surface()
    raw = raw_atomicity_scan(surface)
    raw["bad_counts"]["order:synthetic_zero_only"] = 0

    reconciliation = analyzer.reconcile_r0_fixed_dollar_atomicity(
        surface,
        raw,
        analyzer.DEFAULT_FROZEN,
    )

    assert reconciliation["valid"] is True
    assert "order:synthetic_zero_only" not in reconciliation["raw_bad_counts"]
    assert reconciliation["unreconciled_bad_counts"] == {}


def test_r1_can_never_use_fixed_dollar_reconciliation() -> None:
    r0_surface = completed_s0r0_surface()
    raw = raw_atomicity_scan(r0_surface)
    r1_surface = replace(r0_surface, arm_id="S0R1")

    reconciliation = analyzer.reconcile_r0_fixed_dollar_atomicity(
        r1_surface,
        raw,
        analyzer.DEFAULT_FROZEN,
    )

    assert reconciliation["valid"] is False
    assert reconciliation["status"] == "failed_r1_reconciliation_forbidden"
    assert reconciliation["reconciled_bad_counts"] == {}
    assert reconciliation["unreconciled_bad_counts"] == reconciliation[
        "raw_bad_counts"
    ]
