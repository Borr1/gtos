from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest


ROUTE = Path(__file__).resolve().parent
MODULE_PATH = ROUTE / "analyze_b7_5_selection_sizing_development_january.py"
SPEC = importlib.util.spec_from_file_location(
    "january_matrix_analyzer_under_test",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
analyzer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = analyzer
SPEC.loader.exec_module(analyzer)

COLD_WRITER_PATH = ROUTE / "archive_b7_5_cold_evidence.py"
COLD_WRITER_SPEC = importlib.util.spec_from_file_location(
    "january_cold_evidence_writer_for_adapter_test",
    COLD_WRITER_PATH,
)
assert COLD_WRITER_SPEC is not None and COLD_WRITER_SPEC.loader is not None
sys.modules.setdefault("b7_5_cold_evidence", analyzer.COLD_EVIDENCE)
cold_writer = importlib.util.module_from_spec(COLD_WRITER_SPEC)
sys.modules[COLD_WRITER_SPEC.name] = cold_writer
COLD_WRITER_SPEC.loader.exec_module(cold_writer)

JUNE_TEST_PATH = ROUTE / "test_analyze_b7_5_selection_sizing_matrix.py"
JUNE_SPEC = importlib.util.spec_from_file_location(
    "june_matrix_test_fixture_for_january",
    JUNE_TEST_PATH,
)
assert JUNE_SPEC is not None and JUNE_SPEC.loader is not None
june_fixture = importlib.util.module_from_spec(JUNE_SPEC)
sys.modules[JUNE_SPEC.name] = june_fixture
JUNE_SPEC.loader.exec_module(june_fixture)


class CoverageAwareFakeVerifier(june_fixture.FakeVerifier):
    """Retain the core fake while reporting rows consumed by the two scans."""

    def __getattr__(self, name: str) -> Any:
        if name == "scan_cross_ledger_candidate_instance_identity":
            def candidate_identity(
                sources: dict[str, Any],
                *_args: Any,
                **_kwargs: Any,
            ) -> dict[str, Any]:
                self.calls.append(name)
                if name == self.bad_scan:
                    return {"bad_counts": {"synthetic_failure": 1}}
                return {
                    "bad_counts": {},
                    "status": "synthetic_clean",
                    "counts": {
                        f"{artifact}_rows": sum(
                            1 for _row in sources[artifact]
                        )
                        for artifact in (
                            "scorecard",
                            "order",
                            "trade",
                            "missed",
                        )
                    },
                }

            return candidate_identity
        if name == "scan_broad_entry_fill_terminal_r_lifecycle_contract":
            def entry_fill_terminal_lifecycle(
                sources: dict[str, Any],
                *_args: Any,
                **_kwargs: Any,
            ) -> dict[str, Any]:
                self.calls.append(name)
                if name == self.bad_scan:
                    return {"bad_counts": {"synthetic_failure": 1}}
                return {
                    "bad_counts": {},
                    "status": "synthetic_clean",
                    "row_counts": {
                        f"{artifact}_rows": sum(
                            1 for _row in sources[artifact]
                        )
                        for artifact in ("order", "trade")
                    },
                }

            return entry_fill_terminal_lifecycle
        return super().__getattr__(name)


def mutate_json(path: Path, mutator: Any) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutator(payload)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def mutate_jsonl(path: Path, mutator: Any) -> None:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    mutator(rows)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def make_january_test_config(tmp_path: Path) -> analyzer.AnalyzerConfig:
    june_config = june_fixture.make_config(tmp_path)
    for arm_id in analyzer.ARM_ORDER:
        paths = june_fixture.analyzer.namespace_paths(
            june_config.artifact_root,
            june_config.prefixes[arm_id],
        )
        mutate_json(
            paths["summary"],
            lambda payload: payload.update(
                {
                    "date_start": analyzer.WINDOW_START,
                    "date_end": analyzer.WINDOW_END,
                }
            ),
        )
        for kind in ("decision", "scorecard", "order", "trade", "missed"):
            mutate_jsonl(
                paths[kind],
                lambda rows: [
                    row.update(
                        {"decision_time_utc": "2026-01-15T10:00:00+00:00"}
                    )
                    for row in rows
                ],
            )
    return analyzer.AnalyzerConfig(
        artifact_root=june_config.artifact_root,
        protocol_path=june_config.protocol_path,
        contract_path=june_config.contract_path,
        control_path=tmp_path / "test-only-control-not-read.json",
        output_path=june_config.output_path,
        prefixes=june_config.prefixes,
        frozen=june_config.frozen,
    )


def demote_test_jsonl_to_cold(path: Path, tmp_path: Path) -> None:
    zstd = shutil.which("zstd")
    if zstd is None:
        pytest.skip("zstd is required for cold-evidence adapter coverage")
    cold_writer.demote_jsonl_paths(
        paths=[path],
        repo_root=tmp_path,
        allowed_root=tmp_path,
        operation_manifest_path=tmp_path / f"{path.name}.operation.json",
        apply=True,
        zstd_path=Path(zstd),
        compression_level=3,
        shard_max_bytes=4096,
        minimum_free_reserve_bytes=0,
    )


REAL_VERIFIER_FIXTURE_TIME = "2026-01-15T10:00:00+00:00"


def make_real_verifier_fixture(
    root: Path,
) -> tuple[dict[str, Path], dict[str, dict[str, Any]]]:
    root.mkdir()

    def identity_row(candidate_id: str, **extra: Any) -> dict[str, Any]:
        return {
            "profile": "repaired_package_conversion_v3",
            "candidate_id": candidate_id,
            "decision_time_utc": REAL_VERIFIER_FIXTURE_TIME,
            "canonical_replay_candidate_instance_key": (
                f"{candidate_id}@@{REAL_VERIFIER_FIXTURE_TIME}"
            ),
            "candidate_instance_identity_status": "materialized",
            **extra,
        }

    rows = {
        "missed": identity_row("c1"),
        "order": identity_row(
            "c2",
            simulated_order_id="o1",
            order_intent_materialized=True,
            entry_fill_executable=True,
            terminal_r_scoreable=False,
            order_event_stage="accepted_pending",
            order_status="pending_accepted",
        ),
        "trade": identity_row(
            "c2",
            simulated_order_id="o1",
            simulated_trade_id="t1",
            order_intent_materialized=True,
            entry_fill_executable=True,
            terminal_r_scoreable=True,
            order_status="filled",
            net_proxy_r=1.0,
        ),
        "scorecard": {
            "profile": "repaired_package_conversion_v3",
            "risk_admitted_final_selected_candidate_instance_keys": [
                f"missing@@{REAL_VERIFIER_FIXTURE_TIME}"
            ],
        },
    }
    paths: dict[str, Path] = {}
    for kind, row in rows.items():
        path = root / f"{kind}.jsonl"
        path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")
        paths[kind] = path
    return paths, rows


def real_verifier_fixture_paths(
    tmp_path: Path,
    storage_mode: str,
) -> tuple[Any, dict[str, Path], dict[str, Any], dict[str, dict[str, Any]]]:
    verifier = analyzer.CORE.load_verifier()
    baseline_paths, rows = make_real_verifier_fixture(tmp_path / "baseline")
    logical_paths, _ = make_real_verifier_fixture(tmp_path / "facade")
    if storage_mode == "cold":
        for path in logical_paths.values():
            demote_test_jsonl_to_cold(path, tmp_path)
    resolver = analyzer.COLD_EVIDENCE.RawOrColdResolver()
    facades = {
        kind: analyzer.RawOrColdLogicalPath(path, resolver)
        for kind, path in logical_paths.items()
    }
    assert {facade._mode() for facade in facades.values()} == {storage_mode}
    return verifier, baseline_paths, facades, rows


def scan_real_candidate_identity(verifier: Any, paths: dict[str, Any]) -> dict[str, Any]:
    candidate_source = verifier.ExactRelationalCandidateSource(
        (paths["missed"], paths["order"], paths["trade"])
    )
    return verifier.scan_cross_ledger_candidate_instance_identity(
        {
            "candidate": candidate_source,
            "scorecard": paths["scorecard"],
            "order": paths["order"],
            "trade": paths["trade"],
            "missed": paths["missed"],
        }
    )


def failure_codes(audit: dict[str, Any]) -> set[str]:
    return {row["code"] for row in audit["failures"]}


def make_synthetic_receipt_bindings(
    audit: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    bindings: dict[str, dict[str, Any]] = {}
    for arm_id in analyzer.ARM_ORDER:
        arm = audit["arms"][arm_id]
        prefix = arm["prefix"]
        producer_artifacts: dict[str, dict[str, Any]] = {}
        logical_identities: dict[str, dict[str, Any]] = {}
        for role, suffix in analyzer.POST_ACCELERATION_ROLE_SUFFIXES.items():
            artifact = arm["artifacts"][role]
            name = f"{prefix}{suffix}"
            producer = {
                "path": name,
                "bytes": artifact["bytes"],
                "sha256": artifact["sha256"],
            }
            logical = {
                "logical_path": name,
                "bytes": artifact["bytes"],
                "sha256": artifact["sha256"],
            }
            if role in analyzer.POST_ACCELERATION_JSONL_ROLES:
                producer["rows"] = artifact["rows"]
                logical["rows"] = artifact["rows"]
            producer_artifacts[role] = producer
            logical_identities[role] = logical
        inventory_core = {
            "artifact_count": len(producer_artifacts),
            "artifacts": producer_artifacts,
        }
        inventory = {
            **inventory_core,
            "inventory_root_sha256": analyzer.CORE.stable_sha256(
                inventory_core
            ),
        }
        bindings[arm_id] = {
            "producer_artifact_inventory": inventory,
            "artifact_inventory_root_sha256": inventory[
                "inventory_root_sha256"
            ],
            "verified_artifact_identity_root_sha256": (
                analyzer.CORE.stable_sha256(logical_identities)
            ),
            "artifact_count": len(producer_artifacts),
        }
    return bindings


def make_surface(arm_id: str = "S0R0") -> Any:
    return analyzer.CORE.ArmSurface(
        arm_id=arm_id,
        prefix=f"test-{arm_id}",
        summary={},
        paths={},
        artifacts={},
    )


def load_real_controls() -> tuple[dict[str, Any], dict[str, Any]]:
    protocol = json.loads(analyzer.PROTOCOL_PATH.read_text(encoding="utf-8"))
    contract = json.loads(analyzer.CONTRACT_PATH.read_text(encoding="utf-8"))
    return protocol, contract


def load_real_amendment() -> dict[str, Any]:
    return json.loads(
        analyzer.SOURCE_AUTHORITY_AMENDMENT_PATH.read_text(encoding="utf-8")
    )


def test_clean_january_adapter_retains_full_core_and_is_test_only(
    tmp_path: Path,
) -> None:
    config = make_january_test_config(tmp_path)
    verifier = CoverageAwareFakeVerifier()

    first = analyzer.build_audit(config, verifier_module=verifier)
    second = analyzer.build_audit(
        config,
        verifier_module=CoverageAwareFakeVerifier(),
    )

    assert first == second
    assert first["valid"] is True
    assert first["status"] == "PASS_TEST_ONLY_NON_PRODUCTION_JANUARY_AUDIT"
    assert first["scope"] == {
        "window_id": "development_january",
        "window_role": "development",
        "window_start": "2026-01-01",
        "window_end": "2026-01-31",
        "arms": ["S0R0", "S1R0", "S0R1", "S1R1"],
        "replay_launched_by_builder": False,
        "outcome_artifact_glob_used": False,
        "march_outcome_read": False,
        "audit_mode": "test_only_non_production",
    }
    assert first["window_membership"]["valid"] is True
    assert first["namespace_storage"]["valid"] is True
    assert first["namespace_storage"]["verified_jsonl_artifact_count"] == 36
    assert first["namespace_storage"]["storage_mode_counts"] == {"raw": 36}
    assert first["disposition"]["adverse_development_april_authorized"] is False
    assert first["disposition"]["next_protocol_window"] is None
    assert first["disposition"]["factor_or_policy_promotion_authorized"] is False
    assert first["disposition"]["challenge_window_authorized"] is False
    assert first["factorial_effects"]["formulas"] == {
        "selection": "S1R0-S0R0",
        "sizing": "S0R1-S0R0",
        "interaction": "S1R1-S1R0-S0R1+S0R0",
        "total_incumbent_value": "S1R1-S0R0",
    }
    assert set(analyzer.CORE.SCAN_FUNCTIONS).issubset(set(verifier.calls))
    assert set(analyzer.CORE.SUMMARY_ISSUE_FUNCTIONS).issubset(
        set(verifier.calls)
    )
    assert analyzer.verify_self_hash(first) is True
    assert config.output_path.exists() is False


def test_frozen_verifier_row_coverage_reconciles_exact_24_clean_counts(
    tmp_path: Path,
) -> None:
    config = make_january_test_config(tmp_path)

    audit = analyzer.build_audit(
        config,
        verifier_module=CoverageAwareFakeVerifier(),
    )

    coverage = audit["frozen_verifier_row_coverage_reconciliation"]
    assert coverage["valid"] is True
    assert coverage["status"] == (
        "PASS_FROZEN_VERIFIER_ROW_COVERAGE_RECONCILED"
    )
    assert coverage["expected_check_count"] == 24
    assert coverage["passed_check_count"] == 24
    assert coverage["failure_count"] == 0
    assert len(coverage["checks"]) == 24
    assert coverage["failures"] == []
    assert all(
        check["expected_rows"] == check["observed_rows"]
        for check in coverage["checks"]
    )
    assert analyzer.verify_self_hash(audit) is True


def test_production_control_and_immutable_june_core_are_exact() -> None:
    assert analyzer.sha256_file(analyzer.CORE_ANALYZER_PATH) == (
        analyzer.CORE_ANALYZER_SHA256
    )
    assert analyzer.sha256_file(analyzer.CONTROL_PATH) == (
        analyzer.CONTROL_FILE_SHA256
    )
    assert analyzer.sha256_file(analyzer.COLD_EVIDENCE_READER_PATH) == (
        analyzer.COLD_EVIDENCE_READER_FILE_SHA256
    )
    records = analyzer.validate_production_control(analyzer.DEFAULT_CONFIG)
    assert records["selected_window_binding"]["next_protocol_step"] == (
        "adverse_development_april_all_four_arms"
    )
    assert records["window_control"]["self_hash_valid"] is True
    assert records["cold_evidence_reader"]["sha256"] == (
        analyzer.COLD_EVIDENCE_READER_FILE_SHA256
    )
    assert records["source_authority_amendment_r3"]["self_hash_valid"] is True
    assert records["source_authority_binding"] == {
        "active_amendment": "R3",
        "amendment_path": analyzer.SOURCE_AUTHORITY_BINDING["path"],
        "amendment_file_sha256": (
            analyzer.SOURCE_AUTHORITY_AMENDMENT_FILE_SHA256
        ),
        "amendment_self_hash_sha256": (
            analyzer.SOURCE_AUTHORITY_AMENDMENT_SELF_HASH_SHA256
        ),
        "protocol_source_plan_digest_sha256": (
            analyzer.PROTOCOL_SOURCE_PLAN_SHA256
        ),
        "active_source_plan_digest_sha256": analyzer.SOURCE_PLAN_SHA256,
        "replay_free_reproduction": True,
        "common_across_all_arms": True,
        "march_outcome_read": False,
    }
    protocol, contract = load_real_controls()
    protocol_january = next(
        row for row in protocol["windows"] if row["id"] == analyzer.WINDOW_ID
    )
    contract_january = next(
        row
        for row in contract["window_source_plan_bindings"]
        if row["window_id"] == analyzer.WINDOW_ID
    )
    assert protocol_january["source_plan_digest_sha256"] == (
        analyzer.PROTOCOL_SOURCE_PLAN_SHA256
    )
    assert contract_january["source_plan_digest_sha256"] == (
        analyzer.SOURCE_PLAN_SHA256
    )
    assert analyzer.PROTOCOL_SOURCE_PLAN_SHA256 != analyzer.SOURCE_PLAN_SHA256


def test_post_acceleration_core_path_guard_uses_successor_contract() -> None:
    config = analyzer._core_config(analyzer.DEFAULT_CONFIG)
    analyzer.validate_post_acceleration_core_paths(config)
    with pytest.raises(
        analyzer.JanuaryAuditError,
        match="decision_contract:sealed_path_mismatch",
    ):
        analyzer.validate_post_acceleration_core_paths(
            replace(
                config,
                contract_path=analyzer.PREDECESSOR_CONTRACT_PATH,
            )
        )


@pytest.mark.parametrize(
    "mutator",
    [
        lambda config, tmp: replace(config, artifact_root=tmp),
        lambda config, tmp: replace(config, protocol_path=tmp / "protocol.json"),
        lambda config, tmp: replace(config, contract_path=tmp / "contract.json"),
        lambda config, tmp: replace(
            config,
            source_authority_amendment_path=tmp / "amendment-r3.json",
        ),
        lambda config, tmp: replace(config, control_path=tmp / "control.json"),
        lambda config, tmp: replace(config, output_path=tmp / "audit.json"),
        lambda config, tmp: replace(
            config,
            prefixes={
                **analyzer.JANUARY_PREFIXES,
                "S1R1": analyzer.CORE.DEFAULT_PREFIXES["S1R1"],
            },
        ),
        lambda config, tmp: replace(
            config,
            frozen=replace(
                analyzer.JANUARY_FROZEN,
                expected_candidate_count=154391,
            ),
        ),
    ],
)
def test_every_production_override_is_rejected(
    tmp_path: Path,
    mutator: Any,
) -> None:
    config = mutator(analyzer.DEFAULT_CONFIG, tmp_path)
    with pytest.raises(analyzer.JanuaryAuditError, match="production_config_invalid"):
        analyzer.validate_production_config(config)


@pytest.mark.parametrize(
    ("target", "mutator", "expected"),
    [
        (
            "protocol",
            lambda payload: payload.update(
                {
                    "windows": [
                        row
                        for row in payload["windows"]
                        if row.get("id") != "development_january"
                    ]
                }
            ),
            "protocol_development_january_binding_count_invalid",
        ),
        (
            "contract",
            lambda payload: payload["window_source_plan_bindings"].append(
                copy.deepcopy(
                    next(
                        row
                        for row in payload["window_source_plan_bindings"]
                        if row.get("window_id") == "development_january"
                    )
                )
            ),
            "decision_contract_development_january_binding_count_invalid",
        ),
        (
            "protocol",
            lambda payload: next(
                row
                for row in payload["windows"]
                if row.get("id") == "development_january"
            ).update({"source_plan_digest_sha256": "0" * 64}),
            "protocol_development_january_binding_divergent",
        ),
        (
            "contract",
            lambda payload: next(
                row
                for row in payload["window_source_plan_bindings"]
                if row.get("window_id") == "development_january"
            ).update({"end": "2026-01-30"}),
            "decision_contract_development_january_binding_divergent",
        ),
        (
            "protocol",
            lambda payload: payload["execution_order"].reverse(),
            "development_execution_order_binding_divergent",
        ),
    ],
)
def test_missing_or_divergent_selected_window_bindings_are_rejected(
    target: str,
    mutator: Any,
    expected: str,
) -> None:
    protocol, contract = load_real_controls()
    mutator(protocol if target == "protocol" else contract)
    with pytest.raises(analyzer.JanuaryAuditError, match=expected):
        analyzer.validate_selected_window_bindings(protocol, contract)


def test_window_neutral_contract_drift_is_rejected() -> None:
    _protocol, contract = load_real_controls()
    next(
        row
        for row in contract["factorial_contract"]["arms"]
        if row["arm_id"] == "S0R1"
    )["arm_fingerprint_sha256"] = "0" * 64

    with pytest.raises(
        analyzer.JanuaryAuditError,
        match="window_neutral_contract_divergent:.*arm_fingerprints",
    ):
        analyzer.validate_window_neutral_contract_bindings(contract)


@pytest.mark.parametrize(
    ("target", "mutator", "expected"),
    [
        (
            "amendment",
            lambda payload: payload["active_source_plan_transition"].update(
                {"current_reproduced_source_plan_digest_sha256": "0" * 64}
            ),
            "development_january_r3_amendment_divergent",
        ),
        (
            "amendment",
            lambda payload: payload["outcome_boundary"].update(
                {"replay_launched_at_seal": True}
            ),
            "development_january_r3_amendment_divergent",
        ),
        (
            "contract",
            lambda payload: payload["source_plan_authority"].update(
                {"development_january": "0" * 64}
            ),
            "development_january_contract_r3_binding_divergent",
        ),
        (
            "contract",
            lambda payload: payload["source_amendment_chain"]["r3"].update(
                {"file_sha256": "0" * 64}
            ),
            "development_january_contract_r3_binding_divergent",
        ),
    ],
)
def test_r3_amendment_or_contract_chain_drift_is_rejected(
    target: str,
    mutator: Any,
    expected: str,
) -> None:
    amendment = load_real_amendment()
    _protocol, contract = load_real_controls()
    mutator(amendment if target == "amendment" else contract)

    with pytest.raises(analyzer.JanuaryAuditError, match=expected):
        analyzer.validate_source_authority_amendment_bindings(
            amendment,
            contract,
        )


def test_mixed_window_row_blocks_matrix_but_preserves_core_findings(
    tmp_path: Path,
) -> None:
    config = make_january_test_config(tmp_path)
    paths = analyzer.CORE.namespace_paths(
        config.artifact_root,
        config.prefixes["S1R1"],
    )
    mutate_jsonl(
        paths["decision"],
        lambda rows: rows[0].update(
            {"decision_time_utc": "2026-06-04T10:00:00+00:00"}
        ),
    )

    audit = analyzer.build_audit(
        config,
        verifier_module=CoverageAwareFakeVerifier(),
    )

    assert audit["valid"] is False
    assert audit["status"] == "FAIL_TEST_ONLY_NON_PRODUCTION_JANUARY_AUDIT"
    assert "january_window_membership_invalid" in failure_codes(audit)
    assert audit["window_membership"]["failure_count"] == 1
    assert audit["factorial_effects"]["scalar_effects"]
    assert audit["disposition"]["adverse_development_april_authorized"] is False
    assert analyzer.verify_self_hash(audit) is True


def test_post_acceleration_shared_contract_projection_is_narrow_and_fail_closed() -> None:
    summary_path = (
        analyzer.DENOMINATOR_ROUTE
        / (
            analyzer.JANUARY_PREFIXES["S0R0"]
            + "_SUMMARY.json"
        )
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    failures: list[dict[str, Any]] = []

    projected = analyzer.project_post_acceleration_summary_for_frozen_core(
        "S0R0",
        summary,
        failures,
    )

    assert failures == []
    assert (
        "exact_profile_config_roots_sha256"
        not in projected["shared_execution_contract"]
    )
    assert (
        "exact_risk_profile_bindings"
        not in projected["shared_execution_contract"]
    )
    shared = copy.deepcopy(projected["shared_execution_contract"])
    declared = shared.pop("shared_execution_contract_digest_sha256")
    shared.pop("valid")
    shared.pop("status")
    assert analyzer.CORE.stable_sha256(shared) == declared

    tampered = copy.deepcopy(summary)
    tampered["shared_execution_contract"][
        "exact_profile_config_roots_sha256"
    ]["repaired_package_conversion_v3"] = "0" * 64
    tamper_failures: list[dict[str, Any]] = []
    analyzer.project_post_acceleration_summary_for_frozen_core(
        "S0R0",
        tampered,
        tamper_failures,
    )
    assert {
        row["code"] for row in tamper_failures
    } == {"post_acceleration_exact_profile_config_root_mismatch"}


def test_multi_selected_scorecard_identity_binds_every_economic_selection() -> None:
    surface = make_surface()
    hard_pool = {"keys": ["a", "b", "c"]}
    row = {
        "selected_candidate_instance_key": "a",
        "selected_scheduler_selected_candidate_instance_key": "a",
        "selected_scheduler_canonical_replay_candidate_instance_key": "b",
        "selected_scheduler_selected_candidate_instance_keys": ["a", "b"],
        "risk_admitted_final_selected_candidate_instance_keys": ["b", "a"],
    }

    analyzer.update_scorecard_identity_set(
        surface,
        row,
        window="w1",
        hard_pool=hard_pool,
        line_number=1,
    )

    assert surface.relational_identity_failures == []
    assert set(surface.scorecard_selected) == {"a", "b"}
    assert {
        binding["candidate_instance_key"]
        for binding in surface.scorecard_selected.values()
    } == {"a", "b"}

    bad = make_surface()
    row["risk_admitted_final_selected_candidate_instance_keys"] = ["a", "c"]
    analyzer.update_scorecard_identity_set(
        bad,
        row,
        window="w1",
        hard_pool=hard_pool,
        line_number=1,
    )
    assert bad.relational_identity_failures[0]["reason"] == (
        "scorecard_selected_identity_set_mismatch"
    )


def test_hard_pool_divergence_is_valid_only_after_factor_selected_state_diverges() -> None:
    valid = analyzer.reconcile_hard_pool_sequences(
        "S0R0",
        "S1R0",
        [
            {
                "window": "w2",
                "sort_key": "2026-01-01T00:00:00+00:00",
                "hard_pool_keys": ["a", "b"],
                "selected_keys": ["a"],
            },
            {
                "window": "w10",
                "sort_key": "2026-01-01T00:15:00+00:00",
                "hard_pool_keys": ["c"],
                "selected_keys": [],
            },
        ],
        [
            {
                "window": "w2",
                "sort_key": "2026-01-01T00:00:00+00:00",
                "hard_pool_keys": ["a", "b"],
                "selected_keys": ["b"],
            },
            {
                "window": "w10",
                "sort_key": "2026-01-01T00:15:00+00:00",
                "hard_pool_keys": ["d"],
                "selected_keys": [],
            },
        ],
    )
    assert valid["valid"] is True
    assert valid["first_selected_state_divergence_window"] == "w2"
    assert valid["post_divergence_hard_pool_mismatch_count"] == 1
    assert valid["pre_divergence_hard_pool_mismatch_count"] == 0
    assert valid["causal_sequence_equal"] is True

    invalid = analyzer.reconcile_hard_pool_sequences(
        "S0R0",
        "S1R0",
        [
            {
                "window": "w1",
                "sort_key": "2026-01-01T00:00:00+00:00",
                "hard_pool_keys": ["a"],
                "selected_keys": ["a"],
            }
        ],
        [
            {
                "window": "w1",
                "sort_key": "2026-01-01T00:00:00+00:00",
                "hard_pool_keys": ["b"],
                "selected_keys": ["b"],
            }
        ],
    )
    assert invalid["valid"] is False
    assert invalid["pre_divergence_hard_pool_mismatch_count"] == 1


def test_hard_pool_reconciliation_rejects_cross_arm_causal_order_drift() -> None:
    result = analyzer.reconcile_hard_pool_sequences(
        "S0R0",
        "S1R0",
        [
            {
                "window": "w2",
                "sort_key": "2026-01-01T00:00:00+00:00",
                "hard_pool_keys": ["a"],
                "selected_keys": ["a"],
            },
            {
                "window": "w10",
                "sort_key": "2026-01-01T00:15:00+00:00",
                "hard_pool_keys": ["b"],
                "selected_keys": ["b"],
            },
        ],
        [
            {
                "window": "w2",
                "sort_key": "2026-01-01T00:15:00+00:00",
                "hard_pool_keys": ["a"],
                "selected_keys": ["a"],
            },
            {
                "window": "w10",
                "sort_key": "2026-01-01T00:30:00+00:00",
                "hard_pool_keys": ["b"],
                "selected_keys": ["b"],
            },
        ],
    )

    assert result["valid"] is False
    assert result["causal_sequence_equal"] is False
    assert result["causal_sequence_mismatch_count"] == 2


def test_physical_trade_and_non_executable_missed_diagnostic_are_distinct_objects() -> None:
    missed = make_surface("S0R0")
    source = make_surface("S1R0")
    missed.missed_by_key["candidate"] = {
        "diagnostic_scoreable": True,
        "headline_scoreable": False,
        "non_executable_diagnostic_scoreable": True,
        "diagnostic_net_r": -1.08,
        "scoreability_status": "diagnostic_opportunity_r_scoreable",
    }
    source.trades["candidate"] = {"scoreable": True, "net_r": 0.76}

    result = analyzer.missed_transition_rollup_distinct_economics(
        analyzer.CORE.missed_transition_rollup,
        missed,
        source,
        ["candidate"],
    )

    assert result["trade_missed_r_mismatch_keys"] == []
    assert result["physical_vs_non_executable_diagnostic_count"] == 1
    assert result["physical_vs_non_executable_diagnostic_differences"] == [
        {
            "candidate_instance_key": "candidate",
            "physical_trade_net_r": 0.76,
            "counterfactual_missed_diagnostic_net_r": -1.08,
            "net_r_delta": 1.84,
        }
    ]

    missed.missed_by_key["candidate"]["headline_scoreable"] = True
    rejected = analyzer.missed_transition_rollup_distinct_economics(
        analyzer.CORE.missed_transition_rollup,
        missed,
        source,
        ["candidate"],
    )
    assert rejected["trade_missed_r_mismatch_keys"] == ["candidate"]


def make_terminal_no_session_label(symbol: str) -> dict[str, Any]:
    authority_hash = ("a" * 40) + f"{len(symbol):024x}"
    path = (
        "/Users/borr/Documents/gtos/repo/ai-trading-agent/data/"
        f"mt5_research_exports/bridge_ftmo_m1_202601/{symbol}_M1.csv"
    )
    return {
        "absolute_min_rows": 1000,
        "candidate_source_count": 1,
        "diagnostic_fallback_only": False,
        "effective_min_rows": 0,
        "evidence_class": "source_bound_asof_timewarp_decision_input",
        "expected_m1_rows_from_m15_session": 0,
        "m15_day_rows": 0,
        "m1_to_m15_expected_coverage_ratio": None,
        "mapped_symbol": symbol,
        "no_session_reference": "m1_and_m15_zero_rows_for_symbol_day",
        "not_redacted_account_native": True,
        "path": path,
        "path_replay_allowed": False,
        "populated_candidate_source_count": 0,
        "row_count": 0,
        "rows": 0,
        "session_scaled_floor_applied": False,
        "session_scaled_min_rows": None,
        "sha256": "b" * 64,
        "source_broker": "FTMO",
        "source_day_authority_hash_sha256": authority_hash,
        "source_day_authority_id": f"source_day:{authority_hash[:24]}",
        "source_family": "bridge_ftmo_m1_202601",
        "source_gaps": [],
        "source_overlap_consistent": True,
        "source_path": path,
        "source_role": "owner_authorized_research_hydration",
        "source_session_status": "ftmo_verified_no_session_day",
        "source_truth_scope": (
            "ordered_price_path_only_not_broker_order_lifecycle_truth"
        ),
        "symbol": symbol,
        "terminal_lifecycle_close_allowed": False,
        "timeframe": "M1",
        "trading_day": "2026-01-31",
    }


def make_terminal_no_session_sentinel() -> dict[str, Any]:
    symbols = list(analyzer.JANUARY_TERMINAL_NO_SESSION_SYMBOLS)
    return {
        **analyzer.CORE.expected_flat_binding(
            "S0R0",
            analyzer.JANUARY_FROZEN,
        ),
        **analyzer.JANUARY_TERMINAL_SENTINEL_FIXED_VALUES,
        "campaign": analyzer.JANUARY_TERMINAL_SENTINEL_CAMPAIGNS["S0R0"],
        "symbol": analyzer.JANUARY_TERMINAL_DECISION_SYMBOLS[0],
        "surface_contract": copy.deepcopy(
            analyzer.JANUARY_TERMINAL_SURFACE_CONTRACT
        ),
        "decision_time_utc": "2026-02-01T00:00:00+00:00",
        "trading_day": "2026-01-31",
        "row_type": "asof_decision",
        "candidate_count": 0,
        "raw_data_status": "calendar_no_session_breadth_guard_day_skipped",
        "source_session_status": "calendar_no_session_breadth_stress_day",
        "no_future_decision_rows": True,
        "m1_or_tick_attached_to_decision": False,
        "broker_mutation_enabled": False,
        "live_broker_authority": False,
        "final_selection_claim": False,
        "calendar_no_session_breadth_guard": {
            "active": True,
            "enabled": True,
            "trading_day": "2026-01-31",
            "reason": "calendar_no_session_breadth_guard_active",
            "source_boundary": "source_bound_asof_timewarp_decision_input",
            "min_symbols": 1,
            "no_session_symbol_count": len(symbols),
            "no_session_symbols": symbols,
            "no_session_labels": [
                make_terminal_no_session_label(symbol) for symbol in symbols
            ],
        },
    }


def test_january_terminal_no_session_sentinel_is_exactly_typed() -> None:
    row = make_terminal_no_session_sentinel()

    assert analyzer.is_january_terminal_no_session_sentinel(
        row,
        arm_id="S0R0",
        frozen=analyzer.JANUARY_FROZEN,
    )

    row["candidate_count"] = 1
    assert not analyzer.is_january_terminal_no_session_sentinel(
        row,
        arm_id="S0R0",
        frozen=analyzer.JANUARY_FROZEN,
    )
    row["candidate_count"] = 0
    row["candidate_id"] = "hidden-economic-row"
    assert not analyzer.is_january_terminal_no_session_sentinel(
        row,
        arm_id="S0R0",
        frozen=analyzer.JANUARY_FROZEN,
    )


@pytest.mark.parametrize(
    "mutator",
    [
        lambda row: row.update({"profile": "other"}),
        lambda row: row.update({"split": "challenge"}),
        lambda row: row.update({"evidence_class": "proxy"}),
        lambda row: row["calendar_no_session_breadth_guard"].update(
            {
                "no_session_symbol_count": 0,
                "no_session_symbols": [],
                "no_session_labels": [],
            }
        ),
        lambda row: row["calendar_no_session_breadth_guard"][
            "no_session_labels"
        ][0].update({"symbol": "MISMATCH"}),
        lambda row: row["calendar_no_session_breadth_guard"][
            "no_session_labels"
        ][0].update({"unexpected_nested_field": True}),
    ],
)
def test_january_terminal_no_session_sentinel_rejects_incomplete_or_open_shapes(
    mutator: Any,
) -> None:
    row = make_terminal_no_session_sentinel()
    mutator(row)

    assert not analyzer.is_january_terminal_no_session_sentinel(
        row,
        arm_id="S0R0",
        frozen=analyzer.JANUARY_FROZEN,
    )


def test_receipt_bound_artifacts_reject_coherent_current_namespace_drift() -> None:
    producer_artifacts: dict[str, dict[str, Any]] = {}
    current_artifacts: dict[str, dict[str, Any]] = {}
    namespace_entries: list[dict[str, Any]] = []
    logical_identities: dict[str, dict[str, Any]] = {}
    prefix = "JANUARY_TEST_S0R0"
    for index, (role, suffix) in enumerate(
        analyzer.POST_ACCELERATION_ROLE_SUFFIXES.items(),
        start=1,
    ):
        path = f"{prefix}{suffix}"
        producer = {
            "path": path,
            "bytes": index,
            "sha256": f"{index:064x}",
        }
        current = {
            **producer,
            "path": f"/sealed/current/{path}",
            "namespace_initial_sha256": producer["sha256"],
            "namespace_post_audit_sha256": producer["sha256"],
            "stable_pre_parse_post": True,
        }
        identity = {
            "logical_path": path,
            "bytes": index,
            "sha256": producer["sha256"],
        }
        if role in analyzer.POST_ACCELERATION_JSONL_ROLES:
            producer["rows"] = index
            current["rows"] = index
            identity["rows"] = index
            namespace_entries.append(
                {
                    "arm_id": "S0R0",
                    "artifact": role,
                    "path": f"/sealed/current/{path}",
                    "logical_bytes": index,
                    "sha256": producer["sha256"],
                    "physical_line_count": index,
                    "json_object_row_count": index,
                    "blank_line_count": 0,
                    "ends_with_lf": True,
                    "full_logical_reverification": True,
                }
            )
        elif role == "partial_summary":
            producer["status"] = "partial_in_progress_not_final_proof"
        else:
            producer["status"] = (
                "broad_live_as_if_replay_materialized_broker_live_closed"
            )
        producer_artifacts[role] = producer
        current_artifacts[role] = current
        logical_identities[role] = identity

    inventory_core = {
        "all_artifacts_regular_non_symlink_files": True,
        "all_expected_artifacts_present": True,
        "artifact_count": len(producer_artifacts),
        "artifacts": producer_artifacts,
        "completed_summary_status": (
            "broad_live_as_if_replay_materialized_broker_live_closed"
        ),
        "ledger_counts_reconciled_to_completed_summary": True,
        "ledger_row_counts": {
            role: producer_artifacts[role]["rows"]
            for role in analyzer.POST_ACCELERATION_JSONL_ROLES
        },
        "order_send_attempts_by_profile": {
            "repaired_package_conversion_v3": 0
        },
        "partial_summary_status": "partial_in_progress_not_final_proof",
        "zero_real_order_send_attempts_reconciled": True,
    }
    inventory = {
        **inventory_core,
        "inventory_root_sha256": analyzer.CORE.stable_sha256(inventory_core),
    }
    binding = {
        "producer_artifact_inventory": inventory,
        "artifact_inventory_root_sha256": inventory[
            "inventory_root_sha256"
        ],
        "verified_artifact_identity_root_sha256": (
            analyzer.CORE.stable_sha256(logical_identities)
        ),
        "artifact_count": len(producer_artifacts),
    }
    audit = {
        "arms": {
            "S0R0": {
                "prefix": prefix,
                "artifacts": current_artifacts,
            }
        }
    }
    namespace_storage = {
        "valid": True,
        "entries": namespace_entries,
    }

    exact = analyzer.reconcile_analyzed_artifacts_to_receipts(
        audit,
        {"S0R0": binding},
        namespace_storage,
        arm_order=("S0R0",),
    )
    assert exact["valid"] is True

    current_artifacts["decision"]["sha256"] = "f" * 64
    current_artifacts["decision"]["namespace_initial_sha256"] = "f" * 64
    current_artifacts["decision"]["namespace_post_audit_sha256"] = "f" * 64
    decision_entry = next(
        row
        for row in namespace_entries
        if row["artifact"] == "decision"
    )
    decision_entry["sha256"] = "f" * 64
    drifted = analyzer.reconcile_analyzed_artifacts_to_receipts(
        audit,
        {"S0R0": binding},
        namespace_storage,
        arm_order=("S0R0",),
    )
    assert drifted["valid"] is False
    assert drifted["failure_count"] >= 1
    assert {
        row["reason"] for row in drifted["failures"]
    } >= {
        "producer_current_artifact_identity_mismatch",
        "verified_artifact_identity_root_mismatch",
    }


def test_cold_jsonl_is_logically_identical_to_raw_namespace(
    tmp_path: Path,
) -> None:
    config = make_january_test_config(tmp_path)
    paths = analyzer.CORE.namespace_paths(
        config.artifact_root,
        config.prefixes["S0R0"],
    )
    decision_path = paths["decision"]
    raw_sha256 = analyzer.sha256_file(decision_path)
    raw_bytes = decision_path.stat().st_size
    demote_test_jsonl_to_cold(decision_path, tmp_path)

    audit = analyzer.build_audit(
        config,
        verifier_module=CoverageAwareFakeVerifier(),
    )

    assert audit["valid"] is True
    storage = audit["namespace_storage"]
    assert storage["valid"] is True
    assert storage["storage_mode_counts"] == {
        "cold_zstd_shards": 1,
        "raw": 35,
    }
    cold_entry = next(
        row
        for row in storage["entries"]
        if row["arm_id"] == "S0R0" and row["artifact"] == "decision"
    )
    assert cold_entry["storage_mode"] == "cold_zstd_shards"
    assert cold_entry["sha256"] == raw_sha256
    assert cold_entry["logical_bytes"] == raw_bytes
    assert cold_entry["full_logical_reverification"] is True
    assert cold_entry["manifest_file_sha256"]
    assert cold_entry["manifest_self_hash_sha256"]
    assert analyzer.verify_self_hash(audit) is True


@pytest.mark.parametrize("storage_mode", ("raw", "cold"))
def test_real_verifier_candidate_identity_reiterates_logical_facade_rows(
    tmp_path: Path,
    storage_mode: str,
) -> None:
    verifier, baseline_paths, facades, rows = real_verifier_fixture_paths(
        tmp_path,
        storage_mode,
    )

    assert list(facades["order"]) == [rows["order"]]
    assert list(facades["order"]) == [rows["order"]]

    baseline = scan_real_candidate_identity(verifier, baseline_paths)
    observed = scan_real_candidate_identity(verifier, facades)
    expected_counts = {
        "candidate_rows": 2,
        "scorecard_rows": 1,
        "order_rows": 1,
        "trade_rows": 1,
        "missed_rows": 1,
    }
    expected_bad_counts = {
        "scorecard:selected_instance_not_unique_candidate": 1,
        "order:instance_not_final_selected": 1,
    }

    assert baseline["counts"] == expected_counts
    assert observed["counts"] == expected_counts
    assert baseline["bad_counts"] == expected_bad_counts
    assert observed["bad_counts"] == expected_bad_counts


@pytest.mark.parametrize("storage_mode", ("raw", "cold"))
def test_real_verifier_lifecycle_reiterates_logical_facade_rows(
    tmp_path: Path,
    storage_mode: str,
) -> None:
    verifier, baseline_paths, facades, _rows = real_verifier_fixture_paths(
        tmp_path,
        storage_mode,
    )

    baseline = verifier.scan_broad_entry_fill_terminal_r_lifecycle_contract(
        {"order": baseline_paths["order"], "trade": baseline_paths["trade"]}
    )
    observed = verifier.scan_broad_entry_fill_terminal_r_lifecycle_contract(
        {"order": facades["order"], "trade": facades["trade"]}
    )
    expected_row_counts = {
        "order_rows": 1,
        "order_contract_rows": 1,
        "order_entry_fill_executable_rows": 1,
        "order_terminal_r_not_scoreable_rows": 1,
        "order_terminal_r_unscoreable_rows": 1,
        "trade_rows": 1,
        "trade_contract_rows": 1,
        "trade_entry_fill_executable_rows": 1,
        "trade_terminal_r_scoreable_rows": 1,
        "unique_materialized_order_intents": 1,
    }
    expected_bad_counts = {
        "trade:entry_fill_trade_missing_risk_consumption": 1,
        "trade:entry_fill_trade_releases_daily_accepted_risk": 1,
        "trade:entry_fill_trade_missing_fill_risk_transition": 1,
        "trade:terminal_r_scoreable_trade_not_closed": 1,
        "trade:terminal_r_scoreable_trade_result_scoreable_not_true": 1,
        "cross_stage:materialized_intent_terminal_row_count_0": 1,
    }

    assert baseline["row_counts"] == expected_row_counts
    assert observed["row_counts"] == expected_row_counts
    assert baseline["bad_counts"] == expected_bad_counts
    assert observed["bad_counts"] == expected_bad_counts


def test_raw_and_cold_namespace_ambiguity_fails_before_output(
    tmp_path: Path,
) -> None:
    config = make_january_test_config(tmp_path)
    paths = analyzer.CORE.namespace_paths(
        config.artifact_root,
        config.prefixes["S0R0"],
    )
    decision_path = paths["decision"]
    original = decision_path.read_bytes()
    demote_test_jsonl_to_cold(decision_path, tmp_path)
    decision_path.write_bytes(original)

    with pytest.raises(
        analyzer.JanuaryAuditError,
        match="raw_and_cold_evidence_ambiguous",
    ):
        analyzer.build_audit(
            config,
            verifier_module=CoverageAwareFakeVerifier(),
        )
    assert config.output_path.exists() is False


def test_cold_namespace_shard_tamper_fails_before_output(
    tmp_path: Path,
) -> None:
    config = make_january_test_config(tmp_path)
    paths = analyzer.CORE.namespace_paths(
        config.artifact_root,
        config.prefixes["S0R0"],
    )
    decision_path = paths["decision"]
    demote_test_jsonl_to_cold(decision_path, tmp_path)
    archive_dir = analyzer.COLD_EVIDENCE.cold_archive_dir(decision_path)
    shard = sorted(archive_dir.glob("part-*.jsonl.zst"))[0]
    content = bytearray(shard.read_bytes())
    content[len(content) // 2] ^= 0x01
    shard.write_bytes(content)

    with pytest.raises(
        analyzer.JanuaryAuditError,
        match="cold_shard_compressed_hash_mismatch",
    ):
        analyzer.build_audit(
            config,
            verifier_module=CoverageAwareFakeVerifier(),
        )
    assert config.output_path.exists() is False


def test_production_disposition_authorizes_april_only(tmp_path: Path) -> None:
    config = make_january_test_config(tmp_path)
    audit = analyzer.build_audit(
        config,
        verifier_module=CoverageAwareFakeVerifier(),
    )
    base = copy.deepcopy(audit)
    base.pop("self_hash")
    base["control_inputs"]["verifier"].update(
        {
            "production_audit_authority": True,
            "injected_verifier_module": False,
            "frozen_sha256_match": True,
        }
    )
    base = analyzer.CORE.finalize_self_hash(base)

    production = analyzer.finalize_january_audit(
        base,
        production=True,
        control_record={
            "synthetic": "control",
            "post_cold_arm_verification_bindings": (
                make_synthetic_receipt_bindings(base)
            ),
        },
        window_membership=audit["window_membership"],
        namespace_storage=audit["namespace_storage"],
        adapter_initial_sha256="a" * 64,
        adapter_final_sha256="a" * 64,
    )

    assert production["status"] == (
        "PASS_DEVELOPMENT_JANUARY_MATRIX_ADVERSE_DEVELOPMENT_APRIL_AUTHORIZED"
    )
    disposition = production["disposition"]
    assert disposition["adverse_development_april_authorized"] is True
    assert disposition["next_protocol_window"] == "adverse_development_april"
    assert disposition["factor_or_policy_promotion_authorized"] is False
    assert disposition["broker_mutation_enabled"] is False
    assert disposition["live_broker_authority"] is False
    assert disposition["canary_authority"] is False
    assert disposition["final_selection_claim"] is False
    assert disposition["challenge_window_authorized"] is False
    assert disposition["march_outcome_read"] is False
    assert analyzer.verify_self_hash(production) is True


@pytest.mark.parametrize(
    (
        "scan_name",
        "count_container_name",
        "artifact_name",
        "mutation",
        "expected_reason",
    ),
    [
        (
            "candidate_instance_identity",
            "counts",
            "scorecard",
            "missing",
            "observed_verifier_row_count_missing",
        ),
        (
            "entry_fill_terminal_lifecycle",
            "row_counts",
            "trade",
            "mismatch",
            "verifier_artifact_row_count_mismatch",
        ),
    ],
)
def test_frozen_verifier_row_coverage_fails_closed_with_clean_bad_counts(
    tmp_path: Path,
    scan_name: str,
    count_container_name: str,
    artifact_name: str,
    mutation: str,
    expected_reason: str,
) -> None:
    config = make_january_test_config(tmp_path)
    audit = analyzer.build_audit(
        config,
        verifier_module=CoverageAwareFakeVerifier(),
    )
    base = copy.deepcopy(audit)
    base.pop("self_hash")
    scan = base["arms"]["S0R0"]["verification"]["direct_scans"][
        scan_name
    ]
    assert scan["bad_counts"] == {}
    counts = scan[count_container_name]
    row_count_key = f"{artifact_name}_rows"
    if mutation == "missing":
        counts.pop(row_count_key)
    else:
        counts[row_count_key] += 1
    base["control_inputs"]["verifier"].update(
        {
            "production_audit_authority": True,
            "injected_verifier_module": False,
            "frozen_sha256_match": True,
        }
    )
    base = analyzer.CORE.finalize_self_hash(base)

    production = analyzer.finalize_january_audit(
        base,
        production=True,
        control_record={
            "synthetic": "control",
            "post_cold_arm_verification_bindings": (
                make_synthetic_receipt_bindings(base)
            ),
        },
        window_membership=audit["window_membership"],
        namespace_storage=audit["namespace_storage"],
        adapter_initial_sha256="a" * 64,
        adapter_final_sha256="a" * 64,
    )

    coverage = production["frozen_verifier_row_coverage_reconciliation"]
    assert coverage["valid"] is False
    assert coverage["status"] == (
        "FAIL_FROZEN_VERIFIER_ROW_COVERAGE_INCOMPLETE"
    )
    assert coverage["expected_check_count"] == 24
    assert coverage["passed_check_count"] == 23
    assert coverage["failure_count"] == 1
    assert len(coverage["checks"]) == 24
    failure = coverage["failures"][0]
    assert failure["arm_id"] == "S0R0"
    assert failure["scan"] == scan_name
    assert failure["artifact"] == artifact_name
    assert failure["reason"] == expected_reason
    aggregate = next(
        row
        for row in production["failures"]
        if row["code"] == "january_frozen_verifier_row_coverage_invalid"
    )
    assert aggregate["count"] == 1
    assert aggregate["mismatch_count"] == 1
    assert aggregate["samples"] == coverage["failures"]
    assert production["failure_count"] == 1
    assert production["valid"] is False
    assert production["status"] == (
        "FAIL_DEVELOPMENT_JANUARY_MATRIX_"
        "ADVERSE_DEVELOPMENT_APRIL_BLOCKED"
    )
    disposition = production["disposition"]
    assert disposition["development_january_matrix_hard_valid"] is False
    assert (
        disposition["window_matrix_accepted_for_pooled_development_analysis"]
        is False
    )
    assert disposition["adverse_development_april_authorized"] is False
    assert disposition["next_protocol_window"] is None
    assert disposition["factor_or_policy_promotion_authorized"] is False
    assert analyzer.verify_self_hash(production) is True


def test_incomplete_namespace_still_fails_before_output(tmp_path: Path) -> None:
    config = make_january_test_config(tmp_path)
    paths = analyzer.CORE.namespace_paths(
        config.artifact_root,
        config.prefixes["S0R1"],
    )
    paths["trade"].unlink()

    with pytest.raises(
        analyzer.CORE.IncompleteNamespaceError,
        match="S0R1:trade:missing",
    ):
        analyzer.build_audit(
            config,
            verifier_module=CoverageAwareFakeVerifier(),
        )
    assert config.output_path.exists() is False


def test_check_mode_never_calls_writer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = make_january_test_config(tmp_path)
    audit = analyzer.build_audit(
        config,
        verifier_module=CoverageAwareFakeVerifier(),
    )
    monkeypatch.setattr(analyzer, "parse_args", lambda: analyzer.argparse.Namespace(check=True))
    monkeypatch.setattr(analyzer, "build_audit", lambda _config: audit)

    def forbid_write(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("--check attempted to write an audit")

    monkeypatch.setattr(analyzer, "write_audit", forbid_write)

    before = (
        analyzer.OUTPUT_PATH.stat().st_mtime_ns
        if analyzer.OUTPUT_PATH.exists()
        else None
    )
    assert analyzer.main() == 0
    after = (
        analyzer.OUTPUT_PATH.stat().st_mtime_ns
        if analyzer.OUTPUT_PATH.exists()
        else None
    )
    assert after == before


def test_production_verifier_injection_is_rejected_before_namespace_read() -> None:
    with pytest.raises(
        analyzer.JanuaryAuditError,
        match="production_verifier_module_injection_forbidden",
    ):
        analyzer.build_audit(
            analyzer.DEFAULT_CONFIG,
            verifier_module=CoverageAwareFakeVerifier(),
        )
