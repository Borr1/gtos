#!/usr/bin/env python3
"""Build the sealed, replay-free B7.5 selection/sizing decision contract.

The builder deliberately does not import the replay harness.  It hashes only
the declared predecision behavior/config/package inputs and projects window
metadata from the sealed experiment protocol.  It never opens a replay output
or outcome ledger.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]

SCHEMA = "gtos.b7_5.selection_sizing_decision_contract.v2"
PROTOCOL_SCHEMA = "gtos.b7_5.selection_sizing_experiment_protocol.v1"
PROTOCOL_RELATIVE_PATH = (
    "research/operations/"
    "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "B7_5_SELECTION_SIZING_EXPERIMENT_PROTOCOL.json"
)
AMENDMENT_R1_SCHEMA = (
    "gtos.b7_5.selection_sizing_source_authority_repair_amendment.v1"
)
AMENDMENT_R1_RELATIVE_PATH = (
    "research/operations/"
    "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "B7_5_SELECTION_SIZING_SOURCE_AUTHORITY_REPAIR_AMENDMENT_R1.json"
)
AMENDMENT_R2_SCHEMA = (
    "gtos.b7_5.selection_sizing_source_authority_repair_digest_correction.v1"
)
AMENDMENT_R2_RELATIVE_PATH = (
    "research/operations/"
    "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "B7_5_SELECTION_SIZING_SOURCE_AUTHORITY_REPAIR_AMENDMENT_R2.json"
)
AMENDMENT_R3_SCHEMA = (
    "gtos.b7_5.selection_sizing_january_source_authority_correction_r3.v1"
)
AMENDMENT_R3_RELATIVE_PATH = (
    "research/operations/"
    "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "B7_5_SELECTION_SIZING_SOURCE_AUTHORITY_REPAIR_AMENDMENT_R3.json"
)
OUTPUT_RELATIVE_PATH = (
    "research/operations/"
    "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "B7_5_SELECTION_SIZING_DECISION_CONTRACT.json"
)
OUTPUT_PATH = ROOT / OUTPUT_RELATIVE_PATH
EXPECTED_PROTOCOL_SHA256 = (
    "55ccc9a95647179fcf3e43acb2445b9b8ab4f2b146752cacc05b84bb8444be1a"
)
EXPECTED_AMENDMENT_R1_SHA256 = (
    "cd019fd2cb5db43838935c571d73b24b28e8c91fbbb1bd2d8f55a9416d4103e0"
)
EXPECTED_AMENDMENT_R1_SELF_HASH_SHA256 = (
    "880061b1154894599075994b723aba23aa3b5753dc341f3afedf47784e8fb713"
)
EXPECTED_AMENDMENT_R2_SHA256 = (
    "087811cb68736ed8f3daa924444a7bd09940f57b6dc3916efcc7c87232dbef66"
)
EXPECTED_AMENDMENT_R2_SELF_HASH_SHA256 = (
    "c6649eea6fbe83396aa25e6d978776567891f3f237e8d7a33a517b8e0cbb6a35"
)
EXPECTED_AMENDMENT_R3_SHA256 = (
    "853f4b09acd45918fc868588b7ecef18f46b3e360a225fe958e8ef8a0684e619"
)
EXPECTED_AMENDMENT_R3_SELF_HASH_SHA256 = (
    "55ef3a65c65723521706f78ebe3466929b04874722ed1c7b2c24d60b258a2e3e"
)
EXPECTED_DEVELOPMENT_JANUARY_PROTOCOL_SOURCE_PLAN_SHA256 = (
    "b41714da59188be2ca1c4d72797521589a594ceb000a5e7f58eb3ac2ea5147d2"
)
EXPECTED_DEVELOPMENT_JANUARY_R3_SOURCE_PLAN_SHA256 = (
    "85663876fababc9b69c1bd7041c2bd043b286b456c2e635b2a6fc2289192d4e5"
)
EXPECTED_JANUARY_SEALED_SOURCE_WINDOW_CONTRACT_SHA256 = (
    "13c19851a576ce1686de6857d953c2669eeae7a3e15cfea66ef702822b86c70d"
)
EXPECTED_JANUARY_STATIC_COMPONENT_SHA256 = (
    "ba2da8b7f85dc6bcf64254baf56901f67bf13f0a8506878e82e9b828447a6fde"
)
EXPECTED_JANUARY_M1_COMPONENT_SHA256 = (
    "7f02e7ecc24e30195cac67f15320e5249a732082b6a42c4ecf140067266c7ee4"
)
EXPECTED_JANUARY_OLD_TICK_COMPONENT_SHA256 = (
    "d2255d05d0b0f951e003966a480959ab2aa0004f69310cb91da982f0094e7dc3"
)
EXPECTED_JANUARY_R3_TICK_COMPONENT_SHA256 = (
    "391be51457ba42909db58724e13284aa2e490d7758666238e2f2ee2a056614d4"
)
EXPECTED_JANUARY_OLD_TICK_WINDOW_PLAN_SHA256 = (
    "ab8bf9fc9c7705ff1941a70daf22989b538bb55034b022944eaaaee15f0c76fa"
)
EXPECTED_JANUARY_R3_TICK_WINDOW_PLAN_SHA256 = (
    "75b78c4eb240b3a2223ceeb544814fb3e9e2de8db2d8249f1c2a6ef26d47b38a"
)
EXPECTED_ENGINEERING_JUNE_04_PROTOCOL_SOURCE_PLAN_SHA256 = (
    "a24fc9198b11cfc447f351a7e4db4430d5c03a511dba7cee79085200bd27f001"
)
EXPECTED_ENGINEERING_JUNE_04_R1_CONDITIONAL_SOURCE_PLAN_SHA256 = (
    "7e95536787006e94c1fad5fe21915879074b39655fb7d755c62883e8bed1e024"
)
EXPECTED_ENGINEERING_JUNE_04_ACTUAL_REPAIRED_SOURCE_PLAN_SHA256 = (
    "2a5f9e2444a8aebb039f78a7865e70cbffd9797f6da81c7c3172d24108bea434"
)
EXPECTED_R1_CONDITIONAL_TICK_COMPONENT_SHA256 = (
    "24ff5020fc66e093ff43865becaeecdf82cfd91ce2098d9d000ff74b317443e0"
)
EXPECTED_R1_CONDITIONAL_TICK_WINDOW_PLAN_SHA256 = (
    "17d4d9d55aa3d1124e0e0c6cca26d3ac681aaded1d0499f6793b54880810f24c"
)
EXPECTED_ACTUAL_REPAIRED_TICK_COMPONENT_SHA256 = (
    "dfcf7ecaee95f47ae9a3abf72eb1ecc17c9f1da0917b6e9363bffb2bcc1322b7"
)
EXPECTED_ACTUAL_REPAIRED_TICK_WINDOW_PLAN_SHA256 = (
    "0ec951d0759fe6e521e87ab918c10713f6024a6a27f33f010ce9ecdc183ada22"
)
EXPECTED_STATIC_COMPONENT_SHA256 = (
    "ed49a9fe48e72dfb766cba7951a48496fb8954a8ae8ed048ad2aab9d97451363"
)
EXPECTED_M1_COMPONENT_SHA256 = (
    "06f48e39610f924cd27ef81b8a2d169379248dcc1f46e779fdc9735eb676e5e5"
)
EXPECTED_REPAIRED_UKOIL_WINDOW_SHA256 = (
    "f0aa52a1251c7c717e5d54675ed492724199f08764ba9dd504f50ee07c3efb0b"
)
EXPECTED_UKOIL_SOURCE = {
    "symbol": "UKOIL_cash",
    "source_role": "owner_authorized_path_override",
    "path": (
        "data/mt5_research_exports/"
        "bridge_ftmo_ticks_v127_b7_3_20260601_20260605_full_plus_expiry/"
        "ticks/UKOIL_cash/v127_b7_3_nonhostile5d_ticks.jsonl"
    ),
    "sha256": "c9b1672454932af9600b331783b99ca83de7672ab236b63a5fd7547f8075a250",
    "rows": 282386,
    "first_timestamp_utc": "2026-06-01T03:05:00.017Z",
    "last_timestamp_utc": "2026-06-05T23:49:57.216Z",
    "ordered_price_path_authority": True,
    "redacted_account_native_authority": False,
    "broker_lifecycle_authority": False,
}
CANONICALIZATION = "utf8_json_sort_keys_compact_separators_ensure_ascii"

EXECUTION_ROUTE = (
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
)


class ContractValidationError(ValueError):
    """Raised when a sealed input or decision-contract invariant fails."""


@dataclass(frozen=True)
class InputSpec:
    input_id: str
    kind: str
    relative_path: str


COMMON_INPUT_SPECS = (
    InputSpec("sealed_experiment_protocol", "protocol", PROTOCOL_RELATIVE_PATH),
    InputSpec(
        "sealed_source_authority_repair_amendment_r1",
        "source_authority_amendment",
        AMENDMENT_R1_RELATIVE_PATH,
    ),
    InputSpec(
        "sealed_source_authority_repair_amendment_r2",
        "source_authority_digest_correction",
        AMENDMENT_R2_RELATIVE_PATH,
    ),
    InputSpec(
        "sealed_source_authority_repair_amendment_r3",
        "january_source_authority_correction",
        AMENDMENT_R3_RELATIVE_PATH,
    ),
    InputSpec(
        "broad_replay_harness",
        "behavior_code",
        f"{EXECUTION_ROUTE}/run_broad_live_as_if_replay_harness.py",
    ),
    InputSpec(
        "selected_package_replay_bridge",
        "behavior_code",
        f"{EXECUTION_ROUTE}/run_selected_package_replay_bridge.py",
    ),
    InputSpec(
        "v4_timewarp_simulated_live_research_loop",
        "behavior_code",
        "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
    ),
    InputSpec(
        "selector_v4",
        "behavior_code",
        "src/components/selector_v4.py",
    ),
    InputSpec(
        "moonshot_scheduler_v4_best_trade_allocator",
        "behavior_code",
        "src/research/moonshot_scheduler_v4_best_trade_allocator.py",
    ),
    InputSpec("agent_config", "config", "config/agent_config.yaml"),
    InputSpec(
        "ftmo_server3_profile",
        "config",
        "config/profiles/operator_profile.yaml",
    ),
)

PACKAGE_INPUT_SPECS = (
    InputSpec(
        "ultimate_candidate_package_sleeve_registry",
        "package_authority",
        f"{EXECUTION_ROUTE}/ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl",
    ),
    InputSpec(
        "ultimate_candidate_package_member_axis",
        "package_authority",
        f"{EXECUTION_ROUTE}/SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl",
    ),
)

EXPECTED_FACTORS = {
    "selection": {
        "S0": "neutral_hash_rank_after_identical_hard_eligibility",
        "S1": "current_quality_ranked_selector_scheduler",
    },
    "sizing": {
        "R0": "fixed_equal_account_risk_unit",
        "R1": "current_dynamic_runtime_allocator",
    },
}
EXPECTED_ARMS = (
    {
        "id": "S0R0",
        "selection": "S0",
        "sizing": "R0",
        "role": "reference",
    },
    {
        "id": "S1R0",
        "selection": "S1",
        "sizing": "R0",
        "role": "selection_only",
    },
    {
        "id": "S0R1",
        "selection": "S0",
        "sizing": "R1",
        "role": "sizing_only",
    },
    {
        "id": "S1R1",
        "selection": "S1",
        "sizing": "R1",
        "role": "joint_incumbent",
    },
)
EXPECTED_WINDOW_IDS = (
    "engineering_june_04",
    "development_january",
    "untouched_treatment_challenge_march",
    "adverse_development_april",
    "adverse_development_may",
)
EXPECTED_EXECUTION_ORDER = (
    "implementation_and_focused_tests",
    "engineering_june_04_S1R1_exact_parent_parity",
    "engineering_june_04_remaining_three_arms",
    "development_january_all_four_arms",
    "adverse_development_april_all_four_arms",
    "adverse_development_may_all_four_arms",
    "freeze_development_disposition_and_treatment",
    "untouched_treatment_challenge_march_all_four_arms_exactly_once",
)
EXPECTED_ATTRIBUTION = {
    "selection": "S1R0-S0R0",
    "sizing": "S0R1-S0R0",
    "interaction": "S1R1-S1R0-S0R1+S0R0",
    "total_incumbent_value": "S1R1-S0R0",
}
EXPECTED_FORBIDDEN_SELECTION_INPUTS = (
    "terminal_r",
    "cash_pnl",
    "pnl",
    "close_reason",
    "mfe",
    "mae",
    "future_bar",
    "future_tick",
    "postdecision_path",
)
EXPECTED_PROTOCOL_ECONOMICS = {
    "denominator": {
        "initial_equity_cash": 100000.0,
        "fixed_account_risk_unit_pct": 0.1,
        "fixed_account_risk_unit_cash": 100.0,
        "fixed_denominator_portfolio_r_cash": 100.0,
    },
    "matched_risk": {
        "same_ex_ante_rules_all_arms": True,
        "daily_accepted_risk_pct_cap": 4.0,
        "peak_open_plus_pending_risk_pct_cap": 4.0,
        "cluster_risk_pct_cap": 1.5,
        "opening_window_risk_pct_cap": 1.0,
        "pending_to_open_transfer_once": True,
        "expiry_or_close_release_once": True,
        "ex_post_rescaling_forbidden": True,
    },
}
EXPECTED_RESOLVER_REPAIR_REQUIREMENTS = (
    {
        "id": "window_scoped_cache",
        "requirement": "cache_by_symbol_and_sorted_source_authority_days",
    },
    {
        "id": "approved_multi_root_gather",
        "requirement": (
            "gather_manifest_valid_tick_components_across_both_approved_roots"
        ),
    },
    {
        "id": "window_overlap_filter",
        "requirement": (
            "retain_only_declared_intervals_overlapping_requested_authority_window"
        ),
    },
    {
        "id": "exact_hash_deduplication",
        "requirement": "deduplicate_identical_sha256_components_deterministically",
    },
    {
        "id": "conflict_fail_closed",
        "requirement": "fail_closed_on_conflicting_overlapping_tick_observations",
    },
    {
        "id": "window_proof",
        "requirement": (
            "prove_june_v127_selection_april_six_component_preservation_and_"
            "explicit_no_tick_on_no_overlap"
        ),
    },
)
EXPECTED_ACTIVE_WINDOW_MATERIALIZATION = {
    "mode": "manifest_declared_files_required_by_active_development_windows_only",
    "exact_path_sha256_row_count_and_bounds_required": True,
    "raw_data_duplication_for_convenience_forbidden": True,
    "source_file_read_by_contract_builder": False,
    "materialization_and_source_preflight_required_before_replay": True,
}
EXPECTED_UNCHANGED_PROTOCOL_FIELDS = (
    "neutral_selection_seed_sha256",
    "neutral_selection_key",
    "neutral_selection_forbidden_inputs",
    "factors",
    "arms",
    "denominator",
    "matched_risk",
    "execution_order",
    "attribution",
    "metrics",
    "thresholds",
    "actions",
    "truth_rules",
)
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")

# These markers identify replay-result surfaces, never contract inputs.  The
# two exact package-authority ledger paths above are the only ledgers opened by
# this builder.
FORBIDDEN_OUTCOME_PATH_MARKERS = (
    "_SCORECARD_",
    "_ORDER_LEDGER",
    "_FILL_LEDGER",
    "_TRADE_LEDGER",
    "_TERMINAL_",
    "_MISSED_OPPORTUNITY_",
    "_OUTCOME_",
    "_COMPARISON_",
    "_DECISION_LEDGER",
    "_BUCKET_LEDGER",
    "_ORACLE_LEDGER",
    "_SUMMARY.JSON",
)
ALLOWED_LEDGER_PATHS = frozenset(
    spec.relative_path for spec in PACKAGE_INPUT_SPECS
)


def canonical_json_bytes(payload: Any) -> bytes:
    """Return the one canonical byte representation used for all JSON hashes."""

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _require(condition: bool, issue: str) -> None:
    if not condition:
        raise ContractValidationError(issue)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and HEX_SHA256.fullmatch(value) is not None


def sealed_protocol_economics(protocol: Mapping[str, Any]) -> dict[str, Any]:
    """Project and validate the exact common economics sealed for every arm."""

    denominator = protocol.get("denominator")
    denominator = denominator if isinstance(denominator, Mapping) else {}
    matched_risk = protocol.get("matched_risk")
    matched_risk = matched_risk if isinstance(matched_risk, Mapping) else {}
    projection = {
        "denominator": {
            field: denominator.get(field)
            for field in EXPECTED_PROTOCOL_ECONOMICS["denominator"]
        },
        "matched_risk": {
            field: matched_risk.get(field)
            for field in EXPECTED_PROTOCOL_ECONOMICS["matched_risk"]
        },
    }
    for section, expected_fields in EXPECTED_PROTOCOL_ECONOMICS.items():
        for field, expected in expected_fields.items():
            actual = projection[section][field]
            _require(
                type(actual) is type(expected) and actual == expected,
                f"protocol_economics_mismatch:{section}.{field}",
            )
    _require(
        projection == EXPECTED_PROTOCOL_ECONOMICS,
        "protocol_economics_mismatch",
    )
    return copy.deepcopy(projection)


def _repo_file(root: Path, relative_path: str) -> Path:
    relative = Path(relative_path)
    _require(not relative.is_absolute(), f"absolute_input_path_forbidden:{relative_path}")
    root_resolved = root.resolve()
    candidate = (root_resolved / relative).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ContractValidationError(
            f"input_path_escapes_repo:{relative_path}"
        ) from exc
    _require(candidate.is_file(), f"input_file_missing:{relative_path}")
    return candidate


def _validate_input_specs(specs: Sequence[InputSpec]) -> None:
    ids = [spec.input_id for spec in specs]
    paths = [spec.relative_path for spec in specs]
    _require(len(ids) == len(set(ids)), "duplicate_input_id")
    _require(len(paths) == len(set(paths)), "duplicate_input_path")
    for spec in specs:
        upper_path = spec.relative_path.upper()
        if spec.relative_path in ALLOWED_LEDGER_PATHS:
            continue
        _require(
            not upper_path.endswith((".JSONL", ".JSONL.GZ")),
            f"undeclared_ledger_input_forbidden:{spec.relative_path}",
        )
        _require(
            not any(marker in upper_path for marker in FORBIDDEN_OUTCOME_PATH_MARKERS),
            f"outcome_artifact_input_forbidden:{spec.relative_path}",
        )


def _hash_file(path: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    size = 0
    line_count = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
            line_count += chunk.count(b"\n")
    return digest.hexdigest(), size, line_count


def hash_input_bindings(
    root: Path,
    specs: Sequence[InputSpec],
) -> list[dict[str, Any]]:
    """Hash a closed input set without parsing or interpreting its contents."""

    _validate_input_specs(specs)
    bindings: list[dict[str, Any]] = []
    for spec in specs:
        path = _repo_file(root, spec.relative_path)
        sha256, size, newline_count = _hash_file(path)
        bindings.append(
            {
                "input_id": spec.input_id,
                "kind": spec.kind,
                "path": spec.relative_path,
                "sha256": sha256,
                "bytes": size,
                "newline_count": newline_count,
            }
        )
    return bindings


def read_and_validate_protocol(root: Path = ROOT) -> tuple[dict[str, Any], str]:
    path = _repo_file(root, PROTOCOL_RELATIVE_PATH)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        protocol = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ContractValidationError(f"protocol_invalid_json:{exc.msg}") from exc
    _require(isinstance(protocol, dict), "protocol_not_mapping")
    validate_protocol(protocol, protocol_file_sha256=digest, root=root)
    return protocol, digest


def canonical_amendment_self_hash(payload: Mapping[str, Any]) -> str:
    """Hash an amendment after excluding only ``self_hash.sha256``."""

    projection = copy.deepcopy(dict(payload))
    self_hash = projection.get("self_hash")
    _require(isinstance(self_hash, dict), "amendment_self_hash_metadata_missing")
    self_hash.pop("sha256", None)
    return canonical_sha256(projection)


def verify_amendment_self_hash(payload: Mapping[str, Any]) -> bool:
    self_hash = payload.get("self_hash")
    if not isinstance(self_hash, Mapping) or not _is_sha256(self_hash.get("sha256")):
        return False
    return self_hash["sha256"] == canonical_amendment_self_hash(payload)


def read_and_validate_amendment_r1(
    root: Path = ROOT,
    *,
    protocol_file_sha256: str = EXPECTED_PROTOCOL_SHA256,
) -> tuple[dict[str, Any], str]:
    """Read only the sealed source-control amendment, never its tick source."""

    path = _repo_file(root, AMENDMENT_R1_RELATIVE_PATH)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        amendment = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ContractValidationError(f"amendment_invalid_json:{exc.msg}") from exc
    _require(isinstance(amendment, dict), "amendment_not_mapping")
    validate_amendment_r1(
        amendment,
        amendment_file_sha256=digest,
        protocol_file_sha256=protocol_file_sha256,
    )
    return amendment, digest


def validate_amendment_r1(
    amendment: Mapping[str, Any],
    *,
    amendment_file_sha256: str,
    protocol_file_sha256: str,
) -> None:
    """Fail closed unless the amendment changes only June source authority."""

    _require(
        amendment_file_sha256 == EXPECTED_AMENDMENT_R1_SHA256,
        "sealed_amendment_r1_sha256_mismatch",
    )
    _require(
        protocol_file_sha256 == EXPECTED_PROTOCOL_SHA256,
        "amendment_base_protocol_sha256_mismatch",
    )
    _require(
        amendment.get("schema") == AMENDMENT_R1_SCHEMA,
        "amendment_r1_schema_mismatch",
    )
    _require(
        amendment.get("status")
        == "SEALED_SOURCE_AUTHORITY_REPAIR_ONLY_BEFORE_REPAIRED_REPLAY",
        "amendment_status_mismatch",
    )
    _require(
        isinstance(amendment.get("sealed_at_utc"), str),
        "amendment_sealed_at_missing",
    )
    _require(verify_amendment_self_hash(amendment), "amendment_self_hash_mismatch")
    _require(
        amendment["self_hash"]["sha256"]
        == EXPECTED_AMENDMENT_R1_SELF_HASH_SHA256,
        "amendment_r1_self_hash_drift",
    )

    _require(
        amendment.get("scope")
        == {
            "window_id": "engineering_june_04",
            "start": "2026-06-04",
            "end": "2026-06-04",
            "repair_class": "source_authority_only",
            "factorial_treatment_change": False,
        },
        "amendment_scope_mismatch",
    )
    _require(
        amendment.get("base_protocol_binding")
        == {
            "path": PROTOCOL_RELATIVE_PATH,
            "file_sha256": EXPECTED_PROTOCOL_SHA256,
            "immutable": True,
            "mutation_forbidden": True,
        },
        "amendment_base_protocol_binding_mismatch",
    )
    _require(
        amendment.get("source_plan_transition")
        == {
            "window_id": "engineering_june_04",
            "protocol_source_plan_digest_sha256": (
                EXPECTED_ENGINEERING_JUNE_04_PROTOCOL_SOURCE_PLAN_SHA256
            ),
            "conditional_repaired_source_plan_digest_sha256": (
                EXPECTED_ENGINEERING_JUNE_04_R1_CONDITIONAL_SOURCE_PLAN_SHA256
            ),
            "binding_action": (
                "override_engineering_june_04_source_plan_binding_only"
            ),
            "condition": (
                "repaired_resolver_exact_file_materialization_and_fail_before_"
                "replay_source_preflight_reproduce_conditional_digest"
            ),
            "old_and_repaired_source_plan_arms_may_not_mix": True,
        },
        "amendment_source_plan_transition_mismatch",
    )
    _require(
        amendment.get("conditional_repaired_source_components")
        == {
            "tick_component_digest_sha256": (
                EXPECTED_R1_CONDITIONAL_TICK_COMPONENT_SHA256
            ),
            "tick_window_plan_digest_sha256": (
                EXPECTED_R1_CONDITIONAL_TICK_WINDOW_PLAN_SHA256
            ),
            "ukoil_cash_window_digest_sha256": (
                EXPECTED_REPAIRED_UKOIL_WINDOW_SHA256
            ),
        },
        "amendment_source_component_binding_mismatch",
    )
    _require(
        amendment.get("owner_authorized_source") == EXPECTED_UKOIL_SOURCE,
        "amendment_owner_authorized_source_mismatch",
    )
    _require(
        tuple(amendment.get("resolver_repair_requirements") or ())
        == EXPECTED_RESOLVER_REPAIR_REQUIREMENTS,
        "amendment_resolver_requirements_mismatch",
    )
    _require(
        amendment.get("active_window_materialization")
        == EXPECTED_ACTIVE_WINDOW_MATERIALIZATION,
        "amendment_materialization_contract_mismatch",
    )

    closure = amendment.get("immutable_factorial_closure")
    _require(isinstance(closure, Mapping), "amendment_factorial_closure_missing")
    _require(
        tuple(closure.get("protocol_fields_unchanged") or ())
        == EXPECTED_UNCHANGED_PROTOCOL_FIELDS,
        "amendment_unchanged_protocol_fields_mismatch",
    )
    for field in (
        "selection_factor_changed",
        "sizing_factor_changed",
        "neutral_selection_seed_changed",
        "thresholds_changed",
        "amendment_is_arm_varying_treatment",
    ):
        _require(closure.get(field) is False, f"amendment_closure_mismatch:{field}")

    _require(
        amendment.get("outcome_boundary")
        == {
            "old_source_june_outcomes_previously_inspected": True,
            "repaired_source_replay_outcomes_read_at_seal": False,
            "march_outcome_read": False,
            "march_outcome_gate_unchanged": (
                "development_disposition_and_treatment_frozen"
            ),
        },
        "amendment_outcome_boundary_mismatch",
    )
    _require(
        amendment.get("authority_boundary")
        == {
            "source_authority_repair_only": True,
            "replay_launched_by_amendment": False,
            "production_config_changed": False,
            "broker_mutation_enabled": False,
            "broker_authority": False,
            "live_authority": False,
            "canary_authority": False,
            "final_authority": False,
        },
        "amendment_authority_boundary_mismatch",
    )


def read_and_validate_amendment_r2(
    root: Path = ROOT,
    *,
    protocol_file_sha256: str = EXPECTED_PROTOCOL_SHA256,
) -> tuple[dict[str, Any], str]:
    """Read the hash-chained R2 correction without opening source or outcomes."""

    path = _repo_file(root, AMENDMENT_R2_RELATIVE_PATH)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        amendment = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ContractValidationError(f"amendment_r2_invalid_json:{exc.msg}") from exc
    _require(isinstance(amendment, dict), "amendment_r2_not_mapping")
    validate_amendment_r2(
        amendment,
        amendment_file_sha256=digest,
        protocol_file_sha256=protocol_file_sha256,
    )
    return amendment, digest


def validate_amendment_r2(
    amendment: Mapping[str, Any],
    *,
    amendment_file_sha256: str,
    protocol_file_sha256: str,
) -> None:
    """Fail closed unless R2 corrects only the pre-replay source digests."""

    _require(
        amendment_file_sha256 == EXPECTED_AMENDMENT_R2_SHA256,
        "sealed_amendment_r2_sha256_mismatch",
    )
    _require(
        protocol_file_sha256 == EXPECTED_PROTOCOL_SHA256,
        "amendment_r2_base_protocol_sha256_mismatch",
    )
    _require(
        amendment.get("schema") == AMENDMENT_R2_SCHEMA,
        "amendment_r2_schema_mismatch",
    )
    _require(
        amendment.get("status")
        == "SEALED_SOURCE_AUTHORITY_REPAIR_DIGEST_CORRECTION_BEFORE_REPAIRED_REPLAY",
        "amendment_r2_status_mismatch",
    )
    _require(
        isinstance(amendment.get("sealed_at_utc"), str),
        "amendment_r2_sealed_at_missing",
    )
    _require(
        verify_amendment_self_hash(amendment),
        "amendment_r2_self_hash_mismatch",
    )
    _require(
        amendment["self_hash"]["sha256"]
        == EXPECTED_AMENDMENT_R2_SELF_HASH_SHA256,
        "amendment_r2_self_hash_drift",
    )
    _require(
        amendment.get("base_protocol_binding")
        == {
            "path": PROTOCOL_RELATIVE_PATH,
            "file_sha256": EXPECTED_PROTOCOL_SHA256,
            "immutable": True,
            "mutation_forbidden": True,
        },
        "amendment_r2_base_protocol_binding_mismatch",
    )
    _require(
        amendment.get("superseded_r1_binding")
        == {
            "path": AMENDMENT_R1_RELATIVE_PATH,
            "file_sha256": EXPECTED_AMENDMENT_R1_SHA256,
            "self_hash_sha256": EXPECTED_AMENDMENT_R1_SELF_HASH_SHA256,
            "preserved_immutable": True,
            "disposition": (
                "historical_failed_conditional_digest_not_active_source_plan_"
                "authority"
            ),
        },
        "amendment_r2_r1_binding_mismatch",
    )

    correction = amendment.get("correction_evidence")
    _require(isinstance(correction, Mapping), "amendment_r2_correction_missing")
    _require(
        correction.get("evidence_class")
        == "replay_free_fail_before_replay_real_root_source_preflight",
        "amendment_r2_evidence_class_mismatch",
    )
    _require(
        correction.get("preflight_status")
        == "VALID_GLOBAL_WINDOW_FILTERED_PLAN_REPRODUCED",
        "amendment_r2_preflight_status_mismatch",
    )
    _require(
        correction.get("replay_launched_before_correction") is False
        and correction.get("outcome_artifact_read_by_correction") is False,
        "amendment_r2_preflight_boundary_mismatch",
    )
    _require(
        correction.get("r1_failed_conditional")
        == {
            "source_plan_digest_sha256": (
                EXPECTED_ENGINEERING_JUNE_04_R1_CONDITIONAL_SOURCE_PLAN_SHA256
            ),
            "tick_component_digest_sha256": (
                EXPECTED_R1_CONDITIONAL_TICK_COMPONENT_SHA256
            ),
            "tick_window_plan_digest_sha256": (
                EXPECTED_R1_CONDITIONAL_TICK_WINDOW_PLAN_SHA256
            ),
            "ukoil_cash_window_digest_sha256": (
                EXPECTED_REPAIRED_UKOIL_WINDOW_SHA256
            ),
        },
        "amendment_r2_failed_conditional_mismatch",
    )
    _require(
        correction.get("actual_repaired")
        == {
            "source_plan_digest_sha256": (
                EXPECTED_ENGINEERING_JUNE_04_ACTUAL_REPAIRED_SOURCE_PLAN_SHA256
            ),
            "static_component_digest_sha256": EXPECTED_STATIC_COMPONENT_SHA256,
            "m1_component_digest_sha256": EXPECTED_M1_COMPONENT_SHA256,
            "tick_component_digest_sha256": (
                EXPECTED_ACTUAL_REPAIRED_TICK_COMPONENT_SHA256
            ),
            "tick_window_plan_digest_sha256": (
                EXPECTED_ACTUAL_REPAIRED_TICK_WINDOW_PLAN_SHA256
            ),
            "ukoil_cash_window_digest_sha256": (
                EXPECTED_REPAIRED_UKOIL_WINDOW_SHA256
            ),
            "covered_symbol_count": 24,
            "covered_component_count": 24,
            "exactly_one_v127_component_per_symbol": True,
            "bad_row_count": 0,
        },
        "amendment_r2_actual_repaired_binding_mismatch",
    )
    _require(
        correction.get("cause")
        == {
            "r1_conditional_assumption": (
                "replace_only_ukoil_while_preserving_other_old_unfiltered_tick_rows"
            ),
            "required_resolver_semantics": (
                "global_authority_window_filter_across_all_24_symbols_with_full_"
                "manifest_materialization"
            ),
            "affected_scope": "all_24_symbols",
            "ukoil_window_digest_remained_exact": True,
            "static_component_digest_unchanged_from_old_plan": True,
            "m1_component_digest_unchanged_from_old_plan": True,
            "only_tick_component_tick_window_and_composite_plan_changed": True,
        },
        "amendment_r2_cause_mismatch",
    )
    _require(
        amendment.get("active_source_plan_transition")
        == {
            "window_id": "engineering_june_04",
            "protocol_source_plan_digest_sha256": (
                EXPECTED_ENGINEERING_JUNE_04_PROTOCOL_SOURCE_PLAN_SHA256
            ),
            "r1_failed_conditional_source_plan_digest_sha256": (
                EXPECTED_ENGINEERING_JUNE_04_R1_CONDITIONAL_SOURCE_PLAN_SHA256
            ),
            "actual_repaired_source_plan_digest_sha256": (
                EXPECTED_ENGINEERING_JUNE_04_ACTUAL_REPAIRED_SOURCE_PLAN_SHA256
            ),
            "binding_action": (
                "override_engineering_june_04_source_plan_binding_with_r2_"
                "actual_only"
            ),
            "old_r1_and_r2_source_plan_arms_may_not_mix": True,
        },
        "amendment_r2_source_plan_transition_mismatch",
    )
    _require(
        amendment.get("active_repaired_source_components")
        == {
            "static_component_digest_sha256": EXPECTED_STATIC_COMPONENT_SHA256,
            "m1_component_digest_sha256": EXPECTED_M1_COMPONENT_SHA256,
            "tick_component_digest_sha256": (
                EXPECTED_ACTUAL_REPAIRED_TICK_COMPONENT_SHA256
            ),
            "tick_window_plan_digest_sha256": (
                EXPECTED_ACTUAL_REPAIRED_TICK_WINDOW_PLAN_SHA256
            ),
            "ukoil_cash_window_digest_sha256": (
                EXPECTED_REPAIRED_UKOIL_WINDOW_SHA256
            ),
        },
        "amendment_r2_source_component_binding_mismatch",
    )
    _require(
        amendment.get("materialization_closure")
        == {
            "scope": (
                "full_manifest_materialization_required_by_active_development_"
                "windows"
            ),
            "global_window_filter_applies_to_all_24_symbols": True,
            "manifest_valid_components_only": True,
            "exact_path_sha256_row_count_and_bounds_required": True,
            "source_file_read_by_contract_builder": False,
        },
        "amendment_r2_materialization_closure_mismatch",
    )
    _require(
        amendment.get("immutable_factorial_closure")
        == {
            "r1_resolver_requirements_unchanged": True,
            "selection_factor_changed": False,
            "sizing_factor_changed": False,
            "neutral_selection_seed_changed": False,
            "thresholds_changed": False,
            "amendment_is_arm_varying_treatment": False,
        },
        "amendment_r2_factorial_closure_mismatch",
    )
    _require(
        amendment.get("outcome_boundary")
        == {
            "repaired_source_replay_outcomes_read_at_seal": False,
            "replay_launched_at_seal": False,
            "march_outcome_read": False,
            "march_outcome_gate_unchanged": (
                "development_disposition_and_treatment_frozen"
            ),
        },
        "amendment_r2_outcome_boundary_mismatch",
    )
    _require(
        amendment.get("authority_boundary")
        == {
            "source_authority_digest_correction_only": True,
            "production_config_changed": False,
            "broker_mutation_enabled": False,
            "broker_authority": False,
            "live_authority": False,
            "canary_authority": False,
            "final_authority": False,
        },
        "amendment_r2_authority_boundary_mismatch",
    )


def read_and_validate_amendment_r3(
    root: Path = ROOT,
    *,
    protocol_file_sha256: str = EXPECTED_PROTOCOL_SHA256,
    amendment_r1_file_sha256: str = EXPECTED_AMENDMENT_R1_SHA256,
    amendment_r2_file_sha256: str = EXPECTED_AMENDMENT_R2_SHA256,
) -> tuple[dict[str, Any], str]:
    """Read the sealed January R3 correction without resolving source/outcomes."""

    path = _repo_file(root, AMENDMENT_R3_RELATIVE_PATH)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        amendment = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ContractValidationError(f"amendment_r3_invalid_json:{exc.msg}") from exc
    _require(isinstance(amendment, dict), "amendment_r3_not_mapping")
    validate_amendment_r3(
        amendment,
        amendment_file_sha256=digest,
        protocol_file_sha256=protocol_file_sha256,
        amendment_r1_file_sha256=amendment_r1_file_sha256,
        amendment_r2_file_sha256=amendment_r2_file_sha256,
    )
    return amendment, digest


def validate_amendment_r3(
    amendment: Mapping[str, Any],
    *,
    amendment_file_sha256: str,
    protocol_file_sha256: str,
    amendment_r1_file_sha256: str,
    amendment_r2_file_sha256: str,
) -> None:
    """Fail closed unless R3 is hash-chained and January/tick/source only."""

    _require(
        amendment_file_sha256 == EXPECTED_AMENDMENT_R3_SHA256,
        "sealed_amendment_r3_sha256_mismatch",
    )
    _require(
        amendment.get("schema") == AMENDMENT_R3_SCHEMA,
        "amendment_r3_schema_mismatch",
    )
    _require(
        amendment.get("status")
        == "SEALED_JANUARY_ONLY_SOURCE_AUTHORITY_CORRECTION_BEFORE_REPLAY",
        "amendment_r3_status_mismatch",
    )
    _require(
        isinstance(amendment.get("sealed_at_utc"), str),
        "amendment_r3_sealed_at_missing",
    )
    _require(
        verify_amendment_self_hash(amendment),
        "amendment_r3_self_hash_mismatch",
    )
    _require(
        amendment["self_hash"]["sha256"]
        == EXPECTED_AMENDMENT_R3_SELF_HASH_SHA256,
        "amendment_r3_self_hash_drift",
    )
    _require(
        amendment.get("scope")
        == {
            "decision_window_id": "development_january",
            "source_window_contract_window_id": "b7_5_2026_01",
            "start": "2026-01-01",
            "end": "2026-01-31",
            "repair_class": "source_authority_only",
            "factorial_treatment_change": False,
            "all_other_decision_windows_unchanged": True,
        },
        "amendment_r3_scope_mismatch",
    )
    _require(
        protocol_file_sha256 == EXPECTED_PROTOCOL_SHA256
        and amendment_r1_file_sha256 == EXPECTED_AMENDMENT_R1_SHA256
        and amendment_r2_file_sha256 == EXPECTED_AMENDMENT_R2_SHA256,
        "amendment_r3_current_chain_input_mismatch",
    )
    _require(
        amendment.get("prior_chain_binding")
        == {
            "protocol": {
                "path": PROTOCOL_RELATIVE_PATH,
                "file_sha256": EXPECTED_PROTOCOL_SHA256,
                "preserved_immutable": True,
            },
            "r1": {
                "path": AMENDMENT_R1_RELATIVE_PATH,
                "file_sha256": EXPECTED_AMENDMENT_R1_SHA256,
                "self_hash_sha256": EXPECTED_AMENDMENT_R1_SELF_HASH_SHA256,
                "preserved_immutable": True,
            },
            "r2": {
                "path": AMENDMENT_R2_RELATIVE_PATH,
                "file_sha256": EXPECTED_AMENDMENT_R2_SHA256,
                "self_hash_sha256": EXPECTED_AMENDMENT_R2_SELF_HASH_SHA256,
                "preserved_immutable": True,
                "remains_active_for_window_id": "engineering_june_04",
            },
        },
        "amendment_r3_prior_chain_binding_mismatch",
    )

    source_contract = amendment.get("sealed_source_window_contract_binding")
    _require(
        isinstance(source_contract, Mapping)
        and source_contract.get("file_sha256")
        == EXPECTED_JANUARY_SEALED_SOURCE_WINDOW_CONTRACT_SHA256
        and source_contract.get("window_id") == "b7_5_2026_01"
        and source_contract.get("valid") is True
        and source_contract.get("replay_free_builder") is True
        and source_contract.get("run_campaign_call_count") == 0,
        "amendment_r3_source_window_contract_binding_mismatch",
    )
    audit = amendment.get("reproduction_audit")
    _require(isinstance(audit, Mapping), "amendment_r3_reproduction_audit_missing")
    _require(
        audit.get("evidence_class")
        == "replay_free_current_resolver_two_pass_exact_january_reproduction"
        and audit.get("resolver_run_count") == 2
        and audit.get("resolver_runs_identical") is True
        and audit.get("reproduced_source_plan_digest_sha256")
        == EXPECTED_DEVELOPMENT_JANUARY_R3_SOURCE_PLAN_SHA256
        and _is_sha256(audit.get("resolver_run_projection_sha256")),
        "amendment_r3_two_pass_reproduction_mismatch",
    )
    for field in (
        "run_campaign_call_count",
        "protocol_file_read_count",
        "amendment_r1_file_read_count",
        "amendment_r2_file_read_count",
        "outcome_ledger_read_count",
        "outcome_artifact_read_count",
        "march_window_evaluation_count",
        "march_window_replay_count",
        "march_outcome_artifact_read_count",
    ):
        _require(audit.get(field) == 0, f"amendment_r3_audit_count_mismatch:{field}")
    _require(
        audit.get("replay_launched") is False
        and audit.get("march_outcome_read") is False
        and audit.get(
            "selected_january_authority_file_integrity_hashes_may_traverse_"
            "multi_month_raw_source_containers"
        )
        is True
        and audit.get(
            "raw_source_container_byte_reads_are_not_march_outcome_evaluation"
        )
        is True,
        "amendment_r3_read_boundary_mismatch",
    )

    _require(
        amendment.get("active_source_plan_transition")
        == {
            "window_id": "development_january",
            "source_window_contract_window_id": "b7_5_2026_01",
            "protocol_and_sealed_contract_source_plan_digest_sha256": (
                EXPECTED_DEVELOPMENT_JANUARY_PROTOCOL_SOURCE_PLAN_SHA256
            ),
            "current_reproduced_source_plan_digest_sha256": (
                EXPECTED_DEVELOPMENT_JANUARY_R3_SOURCE_PLAN_SHA256
            ),
            "binding_action": (
                "override_development_january_source_plan_binding_with_r3_"
                "current_reproduced_digest_only"
            ),
            "old_and_r3_source_plan_arms_may_not_mix": True,
        },
        "amendment_r3_source_plan_transition_mismatch",
    )
    components = amendment.get("component_transition")
    _require(isinstance(components, Mapping), "amendment_r3_components_missing")
    _require(
        components.get("old_source_row_count") == 144
        and components.get("current_source_row_count") == 124
        and components.get("old_source_resolution_row_count") == 931
        and components.get("current_source_resolution_row_count") == 864
        and components.get("static_source_row_count") == 96
        and components.get("static_source_digest_sha256")
        == EXPECTED_JANUARY_STATIC_COMPONENT_SHA256
        and components.get("static_component_unchanged") is True
        and components.get("m1_symbol_day_authority_row_count") == 744
        and components.get("m1_day_plan_digest_sha256")
        == EXPECTED_JANUARY_M1_COMPONENT_SHA256
        and components.get("m1_component_unchanged") is True
        and components.get("tick_window_authority_row_count") == 24
        and components.get("old_tick_component_source_digest_sha256")
        == EXPECTED_JANUARY_OLD_TICK_COMPONENT_SHA256
        and components.get("current_tick_component_source_digest_sha256")
        == EXPECTED_JANUARY_R3_TICK_COMPONENT_SHA256
        and components.get("old_tick_window_plan_digest_sha256")
        == EXPECTED_JANUARY_OLD_TICK_WINDOW_PLAN_SHA256
        and components.get("current_tick_window_plan_digest_sha256")
        == EXPECTED_JANUARY_R3_TICK_WINDOW_PLAN_SHA256
        and components.get("changed_tick_authority_row_count") == 24
        and components.get("only_tick_component_tick_window_and_composite_plan_changed")
        is True
        and components.get("incomplete_sources") == []
        and components.get("tick_integrity_failure_symbols") == [],
        "amendment_r3_component_transition_mismatch",
    )
    _require(
        components.get("old_covered_tick_symbols") == ["USDJPY"]
        and components.get("current_covered_tick_symbols")
        == ["EURUSD", "USDJPY", "XAGUSD", "XAUUSD"],
        "amendment_r3_tick_coverage_transition_mismatch",
    )

    tick_rows = amendment.get("tick_authority_row_transition")
    expected_symbols = {
        "AUDJPY",
        "AUDUSD",
        "BTCUSD",
        "CHFJPY",
        "ETHUSD",
        "EURGBP",
        "EURJPY",
        "EURUSD",
        "GBPJPY",
        "GBPUSD",
        "GER40",
        "JP225",
        "NAS100",
        "NZDUSD",
        "SPX500",
        "UK100",
        "UKOIL_cash",
        "US30_cash",
        "USDCAD",
        "USDCHF",
        "USDJPY",
        "USOIL_cash",
        "XAGUSD",
        "XAUUSD",
    }
    _require(
        isinstance(tick_rows, list)
        and len(tick_rows) == 24
        and {row.get("symbol") for row in tick_rows if isinstance(row, Mapping)}
        == expected_symbols
        and all(
            isinstance(row, Mapping)
            and row.get("digest_changed") is True
            and _is_sha256(row.get("old_tick_window_authority_digest_sha256"))
            and _is_sha256(row.get("current_tick_window_authority_digest_sha256"))
            and row.get("current_integrity_valid") is True
            and row.get("current_integrity_failure_count") == 0
            for row in tick_rows
        ),
        "amendment_r3_tick_authority_rows_mismatch",
    )
    closure = amendment.get("immutable_factorial_closure")
    _require(isinstance(closure, Mapping), "amendment_r3_factorial_closure_missing")
    for field in (
        "selection_factor_changed",
        "sizing_factor_changed",
        "neutral_selection_seed_changed",
        "thresholds_changed",
        "amendment_is_arm_varying_treatment",
    ):
        _require(closure.get(field) is False, f"amendment_r3_closure_mismatch:{field}")
    _require(
        closure.get("protocol_preserved_byte_for_byte") is True
        and closure.get("r1_preserved_byte_for_byte") is True
        and closure.get("r2_preserved_byte_for_byte") is True
        and closure.get("engineering_june_04_r2_binding_unchanged") is True,
        "amendment_r3_preservation_closure_mismatch",
    )
    outcome = amendment.get("outcome_boundary")
    _require(
        isinstance(outcome, Mapping)
        and outcome.get("repaired_source_replay_outcomes_read_at_seal") is False
        and outcome.get("replay_launched_at_seal") is False
        and outcome.get("january_outcome_artifact_read") is False
        and outcome.get("june_outcome_artifact_read") is False
        and outcome.get("march_outcome_read") is False
        and outcome.get("march_outcome_gate_unchanged")
        == "development_disposition_and_treatment_frozen",
        "amendment_r3_outcome_boundary_mismatch",
    )
    authority = amendment.get("authority_boundary")
    _require(
        isinstance(authority, Mapping)
        and authority.get("january_source_authority_correction_only") is True
        and authority.get("production_config_changed") is False
        and authority.get("broker_mutation_enabled") is False
        and authority.get("broker_authority") is False
        and authority.get("live_authority") is False
        and authority.get("canary_authority") is False
        and authority.get("final_authority") is False,
        "amendment_r3_authority_boundary_mismatch",
    )


def validate_protocol(
    protocol: Mapping[str, Any],
    *,
    protocol_file_sha256: str,
    root: Path = ROOT,
) -> None:
    """Fail closed unless the committed preregistration remains exactly sealed."""

    _require(
        protocol_file_sha256 == EXPECTED_PROTOCOL_SHA256,
        "sealed_protocol_sha256_mismatch",
    )
    _require(protocol.get("schema") == PROTOCOL_SCHEMA, "protocol_schema_mismatch")
    _require(
        protocol.get("status") == "SEALED_BEFORE_IMPLEMENTATION_OUTCOMES_UNREAD",
        "protocol_not_sealed_outcomes_unread",
    )
    _require(
        protocol.get("implementation_status") == "NOT_STARTED_AT_SEAL_TIME",
        "protocol_seal_time_implementation_status_mismatch",
    )
    _require(
        protocol.get("execution_contract_path") == OUTPUT_RELATIVE_PATH,
        "protocol_execution_contract_path_mismatch",
    )

    goal = protocol.get("goal")
    _require(isinstance(goal, Mapping), "protocol_goal_missing")
    goal_path = str(goal.get("path") or "")
    _require(goal_path == ".context/00_core/GTOS_ULTRA_GOAL.md", "goal_path_mismatch")
    goal_sha256, _, _ = _hash_file(_repo_file(root, goal_path))
    _require(goal_sha256 == goal.get("sha256"), "goal_sha256_mismatch")

    _require(
        _is_sha256(protocol.get("neutral_selection_seed_sha256")),
        "neutral_selection_seed_invalid",
    )
    _require(
        protocol.get("neutral_selection_key")
        == "sha256(seed|decision_window_id|candidate_instance_key)",
        "neutral_selection_key_mismatch",
    )
    _require(
        tuple(protocol.get("neutral_selection_forbidden_inputs") or ())
        == EXPECTED_FORBIDDEN_SELECTION_INPUTS,
        "neutral_selection_forbidden_inputs_mismatch",
    )
    _require(protocol.get("factors") == EXPECTED_FACTORS, "factor_declaration_mismatch")
    _require(
        tuple(protocol.get("arms") or ()) == EXPECTED_ARMS,
        "four_arm_declaration_mismatch",
    )
    sealed_protocol_economics(protocol)

    denominator = protocol.get("denominator")
    _require(isinstance(denominator, Mapping), "denominator_missing")
    _require(denominator.get("initial_equity_cash") == 100000.0, "initial_equity_mismatch")
    _require(denominator.get("fixed_account_risk_unit_pct") == 0.1, "fixed_risk_pct_mismatch")
    _require(denominator.get("fixed_account_risk_unit_cash") == 100.0, "fixed_risk_cash_mismatch")
    _require(
        denominator.get("fixed_denominator_portfolio_r_cash") == 100.0,
        "fixed_portfolio_r_denominator_mismatch",
    )

    matched_risk = protocol.get("matched_risk")
    _require(isinstance(matched_risk, Mapping), "matched_risk_missing")
    for key, expected in (
        ("same_ex_ante_rules_all_arms", True),
        ("daily_accepted_risk_pct_cap", 4.0),
        ("peak_open_plus_pending_risk_pct_cap", 4.0),
        ("cluster_risk_pct_cap", 1.5),
        ("opening_window_risk_pct_cap", 1.0),
        ("pending_to_open_transfer_once", True),
        ("expiry_or_close_release_once", True),
        ("ex_post_rescaling_forbidden", True),
    ):
        _require(matched_risk.get(key) == expected, f"matched_risk_mismatch:{key}")

    windows = protocol.get("windows")
    _require(isinstance(windows, list), "windows_not_list")
    _require(
        tuple(str(window.get("id") or "") for window in windows)
        == EXPECTED_WINDOW_IDS,
        "window_identity_or_order_mismatch",
    )
    for window in windows:
        _require(isinstance(window, Mapping), "window_not_mapping")
        _require(
            isinstance(window.get("start"), str)
            and isinstance(window.get("end"), str)
            and window["start"] <= window["end"],
            f"invalid_window_dates:{window.get('id')}",
        )
        source_digest = window.get("source_plan_digest_sha256")
        _require(
            source_digest is None or _is_sha256(source_digest),
            f"invalid_source_plan_digest:{window.get('id')}",
        )
    by_id = {str(window["id"]): window for window in windows}
    _require(
        by_id["untouched_treatment_challenge_march"].get("outcome_read_gate")
        == "development_disposition_and_treatment_frozen",
        "march_outcome_read_gate_mismatch",
    )
    _require(
        by_id["untouched_treatment_challenge_march"].get(
            "outcomes_previously_inspected_for_this_treatment"
        )
        is False,
        "march_treatment_outcomes_not_sealed_unread",
    )
    _require(
        by_id["adverse_development_may"].get("source_plan_requirement")
        == "rebuild_and_seal_current_config_plan_before_replay",
        "may_source_plan_requirement_mismatch",
    )
    _require(
        tuple(protocol.get("execution_order") or ()) == EXPECTED_EXECUTION_ORDER,
        "execution_order_mismatch",
    )
    _require(protocol.get("attribution") == EXPECTED_ATTRIBUTION, "attribution_mismatch")

    truth_rules = protocol.get("truth_rules")
    _require(isinstance(truth_rules, Mapping), "truth_rules_missing")
    for key in (
        "positive_by_suppression_forbidden",
        "unscoreable_fill_economic_imputation_forbidden",
        "unscoreable_fill_risk_and_exposure_retained",
        "date_symbol_session_outcome_filters_forbidden",
        "production_or_broker_authority_change_forbidden",
    ):
        _require(truth_rules.get(key) is True, f"truth_rule_not_bound:{key}")


def build_window_bindings(
    protocol: Mapping[str, Any],
    amendment_r1: Mapping[str, Any],
    amendment_r2: Mapping[str, Any],
    amendment_r3: Mapping[str, Any],
    *,
    amendment_r1_file_sha256: str,
    amendment_r2_file_sha256: str,
    amendment_r3_file_sha256: str,
) -> list[dict[str, Any]]:
    """Apply R2 only to June and R3 only to January; preserve all others."""

    bindings: list[dict[str, Any]] = []
    for window in protocol["windows"]:
        source_digest = window.get("source_plan_digest_sha256")
        amended_engineering_window = window["id"] == "engineering_june_04"
        amended_january_window = window["id"] == "development_january"
        if amended_engineering_window:
            r1_transition = amendment_r1["source_plan_transition"]
            r2_transition = amendment_r2["active_source_plan_transition"]
            _require(
                source_digest
                == EXPECTED_ENGINEERING_JUNE_04_PROTOCOL_SOURCE_PLAN_SHA256,
                "engineering_june_04_protocol_source_plan_drift",
            )
            _require(
                r1_transition["protocol_source_plan_digest_sha256"] == source_digest
                and r2_transition["protocol_source_plan_digest_sha256"]
                == source_digest,
                "amendment_chain_protocol_source_plan_binding_mismatch",
            )
            _require(
                r2_transition[
                    "r1_failed_conditional_source_plan_digest_sha256"
                ]
                == r1_transition[
                    "conditional_repaired_source_plan_digest_sha256"
                ],
                "amendment_r2_failed_conditional_binding_mismatch",
            )
            source_digest = r2_transition[
                "actual_repaired_source_plan_digest_sha256"
            ]
        elif amended_january_window:
            r3_transition = amendment_r3["active_source_plan_transition"]
            _require(
                source_digest
                == EXPECTED_DEVELOPMENT_JANUARY_PROTOCOL_SOURCE_PLAN_SHA256,
                "development_january_protocol_source_plan_drift",
            )
            _require(
                r3_transition[
                    "protocol_and_sealed_contract_source_plan_digest_sha256"
                ]
                == source_digest,
                "amendment_r3_protocol_source_plan_binding_mismatch",
            )
            _require(
                r3_transition["window_id"] == "development_january",
                "amendment_r3_window_binding_mismatch",
            )
            source_digest = r3_transition[
                "current_reproduced_source_plan_digest_sha256"
            ]
        binding = {
            "window_id": window["id"],
            "role": window["role"],
            "start": window["start"],
            "end": window["end"],
            "source_plan_digest_sha256": source_digest,
            "source_plan_binding_status": (
                "sealed_actual_repaired_digest_bound_from_r2_correction"
                if amended_engineering_window
                else "sealed_current_reproduced_digest_bound_from_r3_correction"
                if amended_january_window
                else "sealed_digest_bound_from_protocol"
                if source_digest is not None
                else "source_plan_seal_required_before_window_replay"
            ),
            "source_plan_metadata_origin": (
                "sealed_source_authority_repair_amendment_r2"
                if amended_engineering_window
                else "sealed_source_authority_repair_amendment_r3"
                if amended_january_window
                else "sealed_experiment_protocol"
            ),
            "source_plan_artifact_read_by_builder": False,
            "outcome_artifact_read_by_builder": False,
        }
        if amended_engineering_window:
            binding.update(
                {
                    "protocol_source_plan_digest_sha256": (
                        EXPECTED_ENGINEERING_JUNE_04_PROTOCOL_SOURCE_PLAN_SHA256
                    ),
                    "r1_failed_conditional_source_plan_digest_sha256": (
                        EXPECTED_ENGINEERING_JUNE_04_R1_CONDITIONAL_SOURCE_PLAN_SHA256
                    ),
                    "source_authority_repair_amendment_r1_path": (
                        AMENDMENT_R1_RELATIVE_PATH
                    ),
                    "source_authority_repair_amendment_r1_file_sha256": (
                        amendment_r1_file_sha256
                    ),
                    "source_authority_repair_amendment_r2_path": (
                        AMENDMENT_R2_RELATIVE_PATH
                    ),
                    "source_authority_repair_amendment_r2_file_sha256": (
                        amendment_r2_file_sha256
                    ),
                    "r2_actual_digest_reproduced_by_fail_before_replay_"
                    "real_root_source_preflight": True,
                    "old_r1_and_r2_source_plan_arms_may_not_mix": True,
                }
            )
        elif amended_january_window:
            binding.update(
                {
                    "protocol_source_plan_digest_sha256": (
                        EXPECTED_DEVELOPMENT_JANUARY_PROTOCOL_SOURCE_PLAN_SHA256
                    ),
                    "source_authority_repair_amendment_r3_path": (
                        AMENDMENT_R3_RELATIVE_PATH
                    ),
                    "source_authority_repair_amendment_r3_file_sha256": (
                        amendment_r3_file_sha256
                    ),
                    "r3_current_digest_reproduced_by_two_replay_free_current_"
                    "resolver_passes": True,
                    "old_and_r3_source_plan_arms_may_not_mix": True,
                    "engineering_june_04_r2_binding_unchanged": True,
                }
            )
        for optional_key in (
            "outcomes_previously_inspected",
            "outcomes_previously_inspected_for_this_treatment",
            "pristine_model_holdout",
            "outcome_read_gate",
            "source_plan_requirement",
        ):
            if optional_key in window:
                binding[optional_key] = copy.deepcopy(window[optional_key])
        bindings.append(binding)
    return bindings


def declared_factor_deltas(
    protocol: Mapping[str, Any], arm: Mapping[str, Any]
) -> dict[str, Any]:
    """Return the complete and only arm-varying projection."""

    selection_level = str(arm.get("selection") or "")
    sizing_level = str(arm.get("sizing") or "")
    factors = protocol["factors"]
    _require(selection_level in factors["selection"], "unknown_selection_factor_level")
    _require(sizing_level in factors["sizing"], "unknown_sizing_factor_level")
    return {
        "selection": {
            "level": selection_level,
            "declared_behavior": factors["selection"][selection_level],
        },
        "sizing": {
            "level": sizing_level,
            "declared_behavior": factors["sizing"][sizing_level],
        },
    }


def arm_fingerprint(
    protocol: Mapping[str, Any],
    arm: Mapping[str, Any],
    *,
    common_execution_input_digest_sha256: str,
) -> dict[str, Any]:
    """Bind common inputs to only the protocol-declared factor deltas."""

    _require(
        _is_sha256(common_execution_input_digest_sha256),
        "common_execution_input_digest_invalid",
    )
    deltas = declared_factor_deltas(protocol, arm)
    protocol_economics = sealed_protocol_economics(protocol)
    delta_digest = canonical_sha256(deltas)
    fingerprint_payload = {
        "common_execution_input_digest_sha256": common_execution_input_digest_sha256,
        "declared_factor_deltas": deltas,
        "protocol_economics": protocol_economics,
    }
    return {
        "arm_id": arm["id"],
        "role": arm["role"],
        "declared_factor_deltas": deltas,
        "declared_factor_delta_digest_sha256": delta_digest,
        "arm_fingerprint_sha256": canonical_sha256(fingerprint_payload),
        "arm_fingerprint_projection": fingerprint_payload,
        "role_excluded_from_arm_fingerprint": True,
        "window_and_outcome_fields_excluded_from_arm_fingerprint": True,
    }


def canonical_contract_self_hash(payload: Mapping[str, Any]) -> str:
    """Hash a contract after excluding only ``self_hash.sha256``."""

    projection = copy.deepcopy(dict(payload))
    self_hash = projection.get("self_hash")
    _require(isinstance(self_hash, dict), "self_hash_metadata_missing")
    self_hash.pop("sha256", None)
    return canonical_sha256(projection)


def verify_contract_self_hash(payload: Mapping[str, Any]) -> bool:
    self_hash = payload.get("self_hash")
    if not isinstance(self_hash, Mapping) or not _is_sha256(self_hash.get("sha256")):
        return False
    return self_hash["sha256"] == canonical_contract_self_hash(payload)


def build_contract_payload(
    *,
    root: Path = ROOT,
    common_input_specs: Sequence[InputSpec] = COMMON_INPUT_SPECS,
    package_input_specs: Sequence[InputSpec] = PACKAGE_INPUT_SPECS,
) -> dict[str, Any]:
    protocol, protocol_sha256 = read_and_validate_protocol(root)
    amendment_r1, amendment_r1_sha256 = read_and_validate_amendment_r1(
        root,
        protocol_file_sha256=protocol_sha256,
    )
    amendment_r2, amendment_r2_sha256 = read_and_validate_amendment_r2(
        root,
        protocol_file_sha256=protocol_sha256,
    )
    amendment_r3, amendment_r3_sha256 = read_and_validate_amendment_r3(
        root,
        protocol_file_sha256=protocol_sha256,
        amendment_r1_file_sha256=amendment_r1_sha256,
        amendment_r2_file_sha256=amendment_r2_sha256,
    )
    common_inputs = hash_input_bindings(root, common_input_specs)
    package_inputs = hash_input_bindings(root, package_input_specs)
    for input_id, path, digest in (
        (
            "sealed_source_authority_repair_amendment_r1",
            AMENDMENT_R1_RELATIVE_PATH,
            amendment_r1_sha256,
        ),
        (
            "sealed_source_authority_repair_amendment_r2",
            AMENDMENT_R2_RELATIVE_PATH,
            amendment_r2_sha256,
        ),
        (
            "sealed_source_authority_repair_amendment_r3",
            AMENDMENT_R3_RELATIVE_PATH,
            amendment_r3_sha256,
        ),
    ):
        amendment_common_input = next(
            (row for row in common_inputs if row["input_id"] == input_id),
            None,
        )
        _require(
            isinstance(amendment_common_input, Mapping)
            and amendment_common_input.get("path") == path
            and amendment_common_input.get("sha256") == digest,
            f"amendment_common_input_binding_missing:{input_id}",
        )

    common_behavior_digest = canonical_sha256(common_inputs)
    package_authority_digest = canonical_sha256(package_inputs)
    common_execution_projection = {
        "common_behavior_input_digest_sha256": common_behavior_digest,
        "package_authority_input_digest_sha256": package_authority_digest,
    }
    common_execution_digest = canonical_sha256(common_execution_projection)
    protocol_economics = sealed_protocol_economics(protocol)
    windows = build_window_bindings(
        protocol,
        amendment_r1,
        amendment_r2,
        amendment_r3,
        amendment_r1_file_sha256=amendment_r1_sha256,
        amendment_r2_file_sha256=amendment_r2_sha256,
        amendment_r3_file_sha256=amendment_r3_sha256,
    )
    arms = [
        arm_fingerprint(
            protocol,
            arm,
            common_execution_input_digest_sha256=common_execution_digest,
        )
        for arm in protocol["arms"]
    ]
    _require(
        len({arm["arm_fingerprint_sha256"] for arm in arms}) == len(arms),
        "arm_fingerprints_not_unique",
    )

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "SEALED_REPLAY_FREE_DECISION_CONTRACT_VALID",
        "valid": True,
        "replay_free_builder": True,
        "run_campaign_call_count": 0,
        "outcome_ledger_read_count": 0,
        "outcome_artifact_read_count": 0,
        "march_outcome_read": False,
        "protocol_binding": {
            "path": PROTOCOL_RELATIVE_PATH,
            "file_sha256": protocol_sha256,
            "schema": protocol["schema"],
            "status": protocol["status"],
            "sealed_at_utc": protocol["sealed_at_utc"],
            "implementation_status_at_seal": protocol["implementation_status"],
        },
        "source_authority_repair_amendment_binding": {
            "active_amendment": "R3",
            "active_amendments_by_window": {
                "engineering_june_04": "R2",
                "development_january": "R3",
            },
            "r1_historical_failed_conditional": {
                "path": AMENDMENT_R1_RELATIVE_PATH,
                "file_sha256": amendment_r1_sha256,
                "self_hash_sha256": amendment_r1["self_hash"]["sha256"],
                "schema": amendment_r1["schema"],
                "status": amendment_r1["status"],
                "sealed_at_utc": amendment_r1["sealed_at_utc"],
                "disposition": amendment_r2["superseded_r1_binding"][
                    "disposition"
                ],
                "source_plan_transition": copy.deepcopy(
                    amendment_r1["source_plan_transition"]
                ),
                "conditional_repaired_source_components": copy.deepcopy(
                    amendment_r1["conditional_repaired_source_components"]
                ),
                "owner_authorized_source": copy.deepcopy(
                    amendment_r1["owner_authorized_source"]
                ),
            },
            "r2_active_digest_correction": {
                "path": AMENDMENT_R2_RELATIVE_PATH,
                "file_sha256": amendment_r2_sha256,
                "self_hash_sha256": amendment_r2["self_hash"]["sha256"],
                "schema": amendment_r2["schema"],
                "status": amendment_r2["status"],
                "sealed_at_utc": amendment_r2["sealed_at_utc"],
                "superseded_r1_binding": copy.deepcopy(
                    amendment_r2["superseded_r1_binding"]
                ),
                "correction_evidence": copy.deepcopy(
                    amendment_r2["correction_evidence"]
                ),
                "active_source_plan_transition": copy.deepcopy(
                    amendment_r2["active_source_plan_transition"]
                ),
                "active_repaired_source_components": copy.deepcopy(
                    amendment_r2["active_repaired_source_components"]
                ),
                "materialization_closure": copy.deepcopy(
                    amendment_r2["materialization_closure"]
                ),
            },
            "r3_active_january_correction": {
                "path": AMENDMENT_R3_RELATIVE_PATH,
                "file_sha256": amendment_r3_sha256,
                "self_hash_sha256": amendment_r3["self_hash"]["sha256"],
                "schema": amendment_r3["schema"],
                "status": amendment_r3["status"],
                "sealed_at_utc": amendment_r3["sealed_at_utc"],
                "scope": copy.deepcopy(amendment_r3["scope"]),
                "prior_chain_binding": copy.deepcopy(
                    amendment_r3["prior_chain_binding"]
                ),
                "sealed_source_window_contract_binding": copy.deepcopy(
                    amendment_r3["sealed_source_window_contract_binding"]
                ),
                "reproduction_audit": copy.deepcopy(
                    amendment_r3["reproduction_audit"]
                ),
                "active_source_plan_transition": copy.deepcopy(
                    amendment_r3["active_source_plan_transition"]
                ),
                "component_transition": copy.deepcopy(
                    amendment_r3["component_transition"]
                ),
                "resolver_code_cause": copy.deepcopy(
                    amendment_r3["resolver_code_cause"]
                ),
            },
            "common_across_all_arms": True,
            "amendment_is_arm_varying_treatment": False,
            "source_file_read_by_builder": False,
            "outcome_artifact_read_by_builder": False,
        },
        "input_bindings": {
            "common_behavior_inputs": common_inputs,
            "common_behavior_input_digest_sha256": common_behavior_digest,
            "package_authority_inputs": package_inputs,
            "package_authority_input_digest_sha256": package_authority_digest,
            "common_execution_input_projection": common_execution_projection,
            "common_execution_input_digest_sha256": common_execution_digest,
            "file_mtime_and_git_dirty_state_excluded": True,
        },
        "factorial_contract": {
            "neutral_selection_seed_sha256": protocol[
                "neutral_selection_seed_sha256"
            ],
            "neutral_selection_key": protocol["neutral_selection_key"],
            "neutral_selection_forbidden_inputs": copy.deepcopy(
                protocol["neutral_selection_forbidden_inputs"]
            ),
            "factors": copy.deepcopy(protocol["factors"]),
            "only_declared_factor_deltas_may_vary_between_arms": True,
            "source_authority_repair_amendment_is_arm_varying_treatment": False,
            "arms": arms,
            "attribution": copy.deepcopy(protocol["attribution"]),
        },
        "denominator": copy.deepcopy(protocol["denominator"]),
        "matched_risk": copy.deepcopy(protocol["matched_risk"]),
        "protocol_economics": protocol_economics,
        "protocol_economics_digest_sha256": canonical_sha256(
            protocol_economics
        ),
        "window_source_plan_bindings": windows,
        "window_source_plan_binding_digest_sha256": canonical_sha256(windows),
        "execution_order": copy.deepcopy(protocol["execution_order"]),
        "metrics": copy.deepcopy(protocol["metrics"]),
        "thresholds": copy.deepcopy(protocol["thresholds"]),
        "actions": copy.deepcopy(protocol["actions"]),
        "truth_rules": copy.deepcopy(protocol["truth_rules"]),
        "authority_boundary": {
            "decision_contract_only": True,
            "replay_launched": False,
            "outcomes_evaluated": False,
            "production_config_changed": False,
            "broker_live_final_authority": False,
            "broker_mutation_enabled": False,
            "canary_authority": False,
            "deployment_authority": False,
        },
        "self_hash": {
            "algorithm": "sha256",
            "canonicalization": CANONICALIZATION,
            "excluded_path": "self_hash.sha256",
        },
    }
    payload["self_hash"]["sha256"] = canonical_contract_self_hash(payload)
    _require(verify_contract_self_hash(payload), "contract_self_hash_failed")
    return payload


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
    ) + "\n"
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def check_existing_contract(path: Path, expected: Mapping[str, Any]) -> None:
    _require(path.is_file(), f"decision_contract_missing:{path}")
    try:
        actual = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractValidationError(f"decision_contract_invalid_json:{exc.msg}") from exc
    _require(isinstance(actual, dict), "decision_contract_not_mapping")
    _require(verify_contract_self_hash(actual), "decision_contract_self_hash_mismatch")
    _require(actual == expected, "decision_contract_stale_or_input_drifted")


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the existing output against current sealed inputs without writing",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_contract_payload()
    if args.check:
        check_existing_contract(args.output, payload)
    else:
        atomic_write_json(args.output, payload)
    print(
        json.dumps(
            {
                "status": "valid_current_contract" if args.check else payload["status"],
                "output": str(args.output),
                "self_hash_sha256": payload["self_hash"]["sha256"],
                "source_authority_repair_amendment_r1_sha256": payload[
                    "source_authority_repair_amendment_binding"
                ]["r1_historical_failed_conditional"]["file_sha256"],
                "source_authority_repair_amendment_r2_sha256": payload[
                    "source_authority_repair_amendment_binding"
                ]["r2_active_digest_correction"]["file_sha256"],
                "source_authority_repair_amendment_r3_sha256": payload[
                    "source_authority_repair_amendment_binding"
                ]["r3_active_january_correction"]["file_sha256"],
                "engineering_june_04_source_plan_digest_sha256": next(
                    row["source_plan_digest_sha256"]
                    for row in payload["window_source_plan_bindings"]
                    if row["window_id"] == "engineering_june_04"
                ),
                "development_january_source_plan_digest_sha256": next(
                    row["source_plan_digest_sha256"]
                    for row in payload["window_source_plan_bindings"]
                    if row["window_id"] == "development_january"
                ),
                "common_execution_input_digest_sha256": payload["input_bindings"][
                    "common_execution_input_digest_sha256"
                ],
                "arm_fingerprints": {
                    arm["arm_id"]: arm["arm_fingerprint_sha256"]
                    for arm in payload["factorial_contract"]["arms"]
                },
                "outcome_ledger_read_count": payload["outcome_ledger_read_count"],
                "march_outcome_read": payload["march_outcome_read"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
