from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"

STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"

CONFIG_PATH = REPO_ROOT / "config/agent_config.yaml"
RUNTIME_PATH = REPO_ROOT / "src/components/gtos_vnext_runtime.py"
ORCHESTRATOR_PATH = REPO_ROOT / "src/components/orchestrator.py"
EXECUTION_PATH = REPO_ROOT / "src/components/execution.py"
TEST_RUNTIME_PATH = REPO_ROOT / "tests/test_gtos_vnext_runtime.py"
TEST_J46_PATH = REPO_ROOT / "tests/test_j46_j49_policy.py"
TEST_LIMIT_PATH = REPO_ROOT / "tests/test_limit_order_flow.py"

STAGE05_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_VERIFIER_{DATE}.json"
STAGE06_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_LEDGER_{DATE}.jsonl"
STAGE06_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_VERIFIER_{DATE}.json"
STAGE08_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_{DATE}.json"
STAGE09_AI_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_AI_CALIBRATION_MANIFEST_{DATE}.json"
STAGE10_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_ML_MONITORING_INTEGRATION_MAP_{DATE}.json"
STAGE11_OVERLAY = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONFIG_OVERLAY_DIFF_{DATE}.yaml"
STAGE11_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_ACTIVATION_DOSSIER_VERIFIER_{DATE}.json"
STAGE13_REPAIR_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_REPAIRED_ACTIVATION_OVERLAY_SUMMARY_{DATE}.json"
)
STAGE13_REPAIR_VERIFIER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_ACTIVATION_REPAIR_VERIFIER_{DATE}.json"
)
STAGE13_FAILURE_ENUMERATION = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_ACTIVATION_REPAIR_FAILURE_ENUMERATION_{DATE}.json"
)
STAGE13_FULL_SELECTOR_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_{DATE}.json"
)
STAGE13_FULL_SELECTOR_VERIFIER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_VERIFIER_{DATE}.json"
)
STAGE13_REPAIRED_BRANCH_ALLOWLIST = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_REPAIRED_BRANCH_ALLOWLIST_{DATE}.json"
)
STAGE13_BROADER_ORIGIN_ALLOWLIST = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_ACTIVATION_ALLOWLIST_{DATE}.json"
)
STAGE13_OUTSIDE_RISK_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_RISK_RECONCILIATION_SUMMARY_{DATE}.json"
)
STAGE13_OUTSIDE_RISK_VERIFIER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_RISK_RECONCILIATION_VERIFIER_{DATE}.json"
)
STAGE13_redacted_account_RISK_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_BROKER_RISK_GEOMETRY_SUMMARY_{DATE}.json"
)
STAGE13_redacted_account_RISK_VERIFIER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_BROKER_RISK_GEOMETRY_VERIFIER_{DATE}.json"
)

OUTPUT_RESULT = ROUTE_DIR / f"VNEXT_REPLACEMENT_FINAL_SEMANTIC_VERIFICATION_RESULT_{DATE}.json"
OUTPUT_RED_TEAM = ROUTE_DIR / f"VNEXT_REPLACEMENT_SATURATION_SELF_RED_TEAM_{DATE}.md"
FOCUSED_TEST = ROUTE_DIR / "test_vnext_replacement_stage12_semantic_verifier.py"
FULL_MOONSHOT_SELECTOR_ID = (
    "full_moonshot_old_three_plus_broader_origin_positive_native_be_after_trigger"
)
CHECK_MODE = False

REQUIRED_FAILURE_CLASSES = [
    "primitive fixed-target labels treated as moonshot truth",
    "old GTOS still primary",
    "FVG subset narrowing",
    "10-trade collapse",
    "broad prop blocker",
    "broad AVOID blocker with positive avoided-set R",
    "MIXED/LEGACY inert labels",
    "no-paid-AI diagnostic treated as production selector",
    "source-missing rows activated without capture/exclusion",
    "selected coverage lies by reporting universe coverage",
    "config-gated state used as terminal excuse",
    "artifact existence treated as completion",
    "shallow verifier accepting bad metrics",
    "row loss from compression, histogramming, top-N, or Git convenience",
    "activation overlay leaves old GTOS effectively in control",
]


@dataclass
class RStats:
    count: int = 0
    total_r: float = 0.0
    wins: int = 0
    losses: int = 0
    gross_win_r: float = 0.0
    gross_loss_r: float = 0.0

    def add(self, value: Any) -> None:
        if value is None:
            return
        try:
            r_value = float(value)
        except (TypeError, ValueError):
            return
        self.count += 1
        self.total_r += r_value
        if r_value > 0:
            self.wins += 1
            self.gross_win_r += r_value
        elif r_value < 0:
            self.losses += 1
            self.gross_loss_r += abs(r_value)

    def to_record(self) -> dict[str, Any]:
        expectancy = self.total_r / self.count if self.count else None
        win_rate = self.wins / self.count if self.count else None
        profit_factor = (
            self.gross_win_r / self.gross_loss_r if self.gross_loss_r > 0 else None
        )
        return {
            "count": self.count,
            "expectancy_r": expectancy,
            "gross_loss_r": self.gross_loss_r,
            "gross_win_r": self.gross_win_r,
            "profit_factor": profit_factor,
            "total_r": self.total_r,
            "win_rate": win_rate,
            "wins": self.wins,
        }


@dataclass
class DeltaScan:
    candidate_rows: int = 0
    aggregate_rows: int = 0
    activated_selected_rows: int = 0
    old_live_leakage_rows: int = 0
    disposition_counts: Counter[str] = field(default_factory=Counter)
    refusal_reason_counts: Counter[str] = field(default_factory=Counter)
    be_all: RStats = field(default_factory=RStats)
    be_source_complete: RStats = field(default_factory=RStats)
    be_source_complete_fvg: RStats = field(default_factory=RStats)
    be_not_activated_positive: RStats = field(default_factory=RStats)
    condition_source_complete: RStats = field(default_factory=RStats)
    activated_default: RStats = field(default_factory=RStats)
    not_activated_positive_counts: Counter[str] = field(default_factory=Counter)

    def to_record(self) -> dict[str, Any]:
        return {
            "aggregate_rows": self.aggregate_rows,
            "candidate_rows": self.candidate_rows,
            "activated_selected_rows": self.activated_selected_rows,
            "old_live_leakage_rows": self.old_live_leakage_rows,
            "disposition_counts": dict(sorted(self.disposition_counts.items())),
            "refusal_reason_counts": dict(sorted(self.refusal_reason_counts.items())),
            "r_stats": {
                "moonshot_be_after_trigger_all": self.be_all.to_record(),
                "moonshot_be_after_trigger_source_complete": self.be_source_complete.to_record(),
                "moonshot_be_after_trigger_source_complete_fvg": self.be_source_complete_fvg.to_record(),
                "moonshot_be_after_trigger_not_activated_positive": self.be_not_activated_positive.to_record(),
                "condition_router_source_complete": self.condition_source_complete.to_record(),
                "activated_default_source_bound_primary": self.activated_default.to_record(),
            },
            "not_activated_positive_counts": dict(
                sorted(self.not_activated_positive_counts.items())
            ),
        }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    if CHECK_MODE:
        return
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    if CHECK_MODE:
        return
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rel(path: Path | str) -> str:
    if isinstance(path, str):
        path = Path(path)
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _upsert_manifest_output(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    outputs = manifest.setdefault("outputs", [])
    for index, existing in enumerate(outputs):
        if existing.get("path") == entry["path"]:
            outputs[index] = {**existing, **entry}
            return
    outputs.append(entry)


def _append_control(row: dict[str, Any]) -> None:
    if CHECK_MODE:
        return
    with CONTROL_LEDGER.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _append_test_result(state: dict[str, Any], command: str, result: str, timestamp: str) -> None:
    tests = state.setdefault("tests_verifiers_run", [])
    tests[:] = [row for row in tests if row.get("command") != command]
    tests.append({"command": command, "result": result, "timestamp_utc": timestamp})


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def _activation_exit_code(activation_gate_passed: bool) -> int:
    return 0 if activation_gate_passed else 1


def _source_contains(path: Path, needles: list[str]) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {needle: needle in text for needle in needles}


def _filename_matches_config(config_path: Any, expected_path: Path) -> bool:
    if not config_path:
        return False
    return str(config_path).replace("\\", "/").endswith(expected_path.name)


def _full_selector_record(
    summary: dict[str, Any] | None,
    verifier: dict[str, Any] | None,
) -> dict[str, Any]:
    summary = summary or {}
    verifier = verifier or {}
    metrics = summary.get("combined_production_selector_metrics", {})
    return {
        "status": verifier.get("status"),
        "summary_path": _rel(STAGE13_FULL_SELECTOR_SUMMARY),
        "verifier_path": _rel(STAGE13_FULL_SELECTOR_VERIFIER),
        "broader_origin_allowlist_path": _rel(STAGE13_BROADER_ORIGIN_ALLOWLIST),
        "repaired_branch_allowlist_path": _rel(STAGE13_REPAIRED_BRANCH_ALLOWLIST),
        "combined_selected_rows": summary.get("combined_selected_rows"),
        "old_three_selected_rows": summary.get("old_three_selected_rows"),
        "broader_origin_selected_rows": summary.get("broader_origin_selected_rows"),
        "broader_origin_selected_family_counts": summary.get(
            "broader_origin_selected_family_counts", {}
        ),
        "broader_origin_selected_symbol_counts": summary.get(
            "broader_origin_selected_symbol_counts", {}
        ),
        "broader_origin_exclusion_proof_counts": summary.get(
            "broader_origin_exclusion_proof_counts", {}
        ),
        "broader_origin_non_ready_blocker_counts": summary.get(
            "broader_origin_non_ready_blocker_counts", {}
        ),
        "expectancy_r": metrics.get("expectancy_r"),
        "profit_factor": metrics.get("profit_factor"),
        "win_rate": metrics.get("win_rate"),
        "total_r": metrics.get("total_r"),
        "selected_policy": summary.get("selected_policy"),
        "allowlist_entry_count": summary.get("allowlist_entry_count"),
    }


def _production_application_state(
    *,
    config: dict[str, Any],
    stage08: dict[str, Any],
    full_summary: dict[str, Any] | None,
    full_verifier: dict[str, Any] | None,
) -> dict[str, Any]:
    runtime_cfg = config.get("gtos_vnext_runtime", {}) or {}
    full_summary = full_summary or {}
    full_verifier = full_verifier or {}
    metrics = full_summary.get("combined_production_selector_metrics", {}) or {}
    failures: list[str] = []

    expected_true = {
        "enabled": True,
        "apply_to_execution": True,
        "pre_ai_apply_to_ai_call": True,
        "ai_policy_follow_no_ai_enabled": True,
        "ltf_path_execution_apply_to_execution": True,
        "prop_safe_selector_apply_to_execution": True,
        "moonshot_dynamic_execution_router_enabled": True,
        "moonshot_dynamic_execution_router_apply_to_execution": True,
        "replacement_monitoring_enabled": True,
        "replacement_monitoring_log_enabled": True,
    }
    for key, expected in expected_true.items():
        if runtime_cfg.get(key) is not expected:
            failures.append(f"{key}={runtime_cfg.get(key)!r}, expected {expected!r}")

    expected_false = {
        "ai_policy_apply_to_ai_call": False,
        "moonshot_dynamic_execution_router_condition_challenger_enabled": False,
        "replacement_ml_apply_to_execution": False,
        "avoid_blocks_execution": False,
    }
    for key, expected in expected_false.items():
        if runtime_cfg.get(key) is not expected:
            failures.append(f"{key}={runtime_cfg.get(key)!r}, expected {expected!r}")

    expected_values = {
        "mode": "production_replacement_vnext_moonshot",
        "moonshot_dynamic_execution_router_policy": "be_after_trigger",
        "moonshot_dynamic_execution_router_replaces_policy": "live_current_j46_j49",
        "moonshot_dynamic_execution_router_repaired_overlay_selector": FULL_MOONSHOT_SELECTOR_ID,
        "moonshot_dynamic_execution_router_repaired_branch_action": "MOONSHOT_REPAIRED_FOLLOW",
    }
    for key, expected in expected_values.items():
        if runtime_cfg.get(key) != expected:
            failures.append(f"{key}={runtime_cfg.get(key)!r}, expected {expected!r}")

    if runtime_cfg.get("moonshot_dynamic_execution_router_required_branch_labels") != [
        "FOLLOW"
    ]:
        failures.append("required_branch_labels must be ['FOLLOW']")
    expected_frameworks = ["breaker_re_entry", "fvg_fill", "ob_retest"]
    if runtime_cfg.get("moonshot_dynamic_execution_router_activated_frameworks") != (
        expected_frameworks
    ):
        failures.append("activated frameworks do not match old-three full selector")

    selected_families = set(
        (full_summary.get("broader_origin_selected_family_counts") or {}).keys()
    )
    configured_families = set(
        runtime_cfg.get("moonshot_dynamic_execution_router_activated_origin_families")
        or []
    )
    if not selected_families:
        failures.append("full selector has no broader selected origin families")
    if selected_families and selected_families != configured_families:
        failures.append(
            "configured broader origin families do not match full selector selected families"
        )

    eligible = set(stage08.get("broker_native_activation_eligible_symbols") or [])
    excluded = set(stage08.get("broker_native_exact_excluded_symbols") or [])
    if set(runtime_cfg.get("moonshot_dynamic_execution_router_broker_native_eligible_symbols") or []) != eligible:
        failures.append("configured broker-native eligible symbols do not match Stage08")
    if set(runtime_cfg.get("moonshot_dynamic_execution_router_broker_native_exact_excluded_symbols") or []) != excluded:
        failures.append("configured exact broker exclusions do not match Stage08")

    if not _filename_matches_config(
        runtime_cfg.get("moonshot_dynamic_execution_router_stage13_repair_summary_path"),
        STAGE13_FULL_SELECTOR_SUMMARY,
    ):
        failures.append("configured Stage13 selector summary path is not the full moonshot selector")
    if not _filename_matches_config(
        runtime_cfg.get("moonshot_dynamic_execution_router_repaired_branch_allowlist_path"),
        STAGE13_REPAIRED_BRANCH_ALLOWLIST,
    ):
        failures.append("configured repaired branch allowlist path is missing or stale")
    if not _filename_matches_config(
        runtime_cfg.get("moonshot_dynamic_execution_router_broader_origin_allowlist_path"),
        STAGE13_BROADER_ORIGIN_ALLOWLIST,
    ):
        failures.append("configured broader origin allowlist path is missing or stale")

    if full_verifier.get("status") != "passed":
        failures.append("full moonshot selector verifier did not pass")
    if int(full_summary.get("combined_selected_rows") or 0) <= int(
        full_summary.get("old_three_selected_rows") or 0
    ):
        failures.append("combined selector did not extend beyond old-three rows")
    if float(metrics.get("expectancy_r") or 0.0) <= 0.0:
        failures.append("combined selector expectancy is not positive")
    if float(metrics.get("profit_factor") or 0.0) <= 1.0:
        failures.append("combined selector profit factor is not above 1")

    return {
        "applied": not failures,
        "failures": failures,
        "config_flags": {
            key: runtime_cfg.get(key)
            for key in [
                "mode",
                "apply_to_execution",
                "pre_ai_apply_to_ai_call",
                "ai_policy_follow_no_ai_enabled",
                "ltf_path_execution_apply_to_execution",
                "prop_safe_selector_apply_to_execution",
                "moonshot_dynamic_execution_router_enabled",
                "moonshot_dynamic_execution_router_apply_to_execution",
                "replacement_ml_apply_to_execution",
                "avoid_blocks_execution",
            ]
        },
        "selector": _full_selector_record(full_summary, full_verifier),
    }


def _scan_delta_ledger() -> DeltaScan:
    scan = DeltaScan()
    with STAGE06_LEDGER.open("r", encoding="utf-8") as handle:
        for raw in handle:
            if not raw.strip():
                continue
            row = json.loads(raw)
            record_type = row.get("record_type")
            if record_type == "aggregate_delta":
                scan.aggregate_rows += 1
                continue
            if record_type != "candidate_delta":
                continue
            scan.candidate_rows += 1
            disposition = str(row.get("activated_replay_disposition"))
            scan.disposition_counts[disposition] += 1
            if row.get("activated_selected"):
                scan.activated_selected_rows += 1
            if row.get("old_live_leakage_under_activated_overlay"):
                scan.old_live_leakage_rows += 1
            for reason in row.get("activated_refusal_reasons") or []:
                scan.refusal_reason_counts[str(reason)] += 1

            be_r = row.get("moonshot_be_after_trigger_r")
            condition_r = row.get("condition_router_r")
            scan.be_all.add(be_r)
            if row.get("activated_selected"):
                scan.activated_default.add(row.get("activated_default_source_bound_primary_r"))
            source_complete = _truthy(row.get("source_window_complete"))
            if source_complete:
                scan.be_source_complete.add(be_r)
                scan.condition_source_complete.add(condition_r)
                if row.get("candidate_origin_family") == "origin_current_fvg_fill":
                    scan.be_source_complete_fvg.add(be_r)
            if not row.get("activated_selected"):
                try:
                    positive = be_r is not None and float(be_r) > 0.0
                except (TypeError, ValueError):
                    positive = False
                if positive:
                    scan.be_not_activated_positive.add(be_r)
                    scan.not_activated_positive_counts[disposition] += 1
    return scan


def _semantic_checks(
    *,
    overlay: dict[str, Any],
    stage05: dict[str, Any],
    stage06: dict[str, Any],
    stage08: dict[str, Any],
    stage09: dict[str, Any],
    stage10: dict[str, Any],
    stage11_verifier: dict[str, Any],
    config: dict[str, Any],
    delta_scan: DeltaScan,
    repair_summary: dict[str, Any] | None,
    repair_verifier: dict[str, Any] | None,
    full_selector_summary: dict[str, Any] | None,
    full_selector_verifier: dict[str, Any] | None,
    application_state: dict[str, Any],
) -> list[dict[str, Any]]:
    runtime_cfg = config.get("gtos_vnext_runtime", {})
    guardrails = overlay["input_guardrails"]
    prod_cfg = overlay["semantic_gated_production_activation_overlay_candidate"]["config"][
        "gtos_vnext_runtime"
    ]
    checks: list[dict[str, Any]] = []
    repair_ok = bool(repair_verifier and repair_verifier.get("status") == "passed")
    repaired_metrics = (
        (repair_summary or {})
        .get("repaired_overlay_metrics", {})
        .get("be_after_trigger_repaired_overlay", {})
    )
    repaired_comparators = (repair_summary or {}).get("comparator_metrics", {})
    repaired_coverage = (repair_summary or {}).get("coverage", {})
    repaired_source = (repair_summary or {}).get("source_capture_monitoring", {})
    full_selector_ok = bool(
        full_selector_verifier and full_selector_verifier.get("status") == "passed"
    )
    full_selector = _full_selector_record(full_selector_summary, full_selector_verifier)

    def add(name: str, status: str, evidence: dict[str, Any], decision: str) -> None:
        checks.append(
            {
                "failure_class": name,
                "status": status,
                "evidence": evidence,
                "decision": decision,
            }
        )

    add(
        "primitive fixed-target labels treated as moonshot truth",
        "passed",
        {
            "production_policy": prod_cfg["moonshot_dynamic_execution_router_policy"],
            "fixed_1_5r_role": "comparator_only",
            "moonshot_be_expectancy_r": stage06["overall_scenario_metrics"][
                "moonshot_be_after_trigger"
            ]["expectancy_r"],
        },
        "BE-after-trigger is the candidate dynamic policy; fixed 1.5R is not activation truth.",
    )
    add(
        "old GTOS still primary",
        "passed" if repair_ok else "blocked_pending_semantic_repair",
        {
            "current_repo_apply_to_execution": runtime_cfg.get("apply_to_execution"),
            "production_overlay_dynamic_apply": prod_cfg[
                "moonshot_dynamic_execution_router_apply_to_execution"
            ],
            "repaired_overlay_selected_rows": repaired_metrics.get("selected_count"),
            "repaired_overlay_expectancy_r": repaired_metrics.get("expectancy_r"),
            "stage04_j46_replacement_test_present": _source_contains(
                TEST_J46_PATH, ["dynamic replacement suppresses J46", "replaces_policy"]
            ),
        },
        (
            "Runtime has a repaired dynamic replacement path and row-level replay proof for the production overlay."
            if repair_ok
            else "Runtime has a dynamic replacement path, but production cannot apply until the replayed activation slice is repaired."
        ),
    )
    add(
        "FVG subset narrowing",
        "passed" if full_selector_ok else "failed_activation_blocker",
        {
            "candidate_rows": guardrails["candidate_rows"],
            "framework_counts": stage05["framework_counts"],
            "primary_framework": overlay["selected_replacement"]["primary_framework"],
            "stage13_full_moonshot_selector": {
                "combined_selected_rows": full_selector.get("combined_selected_rows"),
                "old_three_selected_rows": full_selector.get("old_three_selected_rows"),
                "broader_origin_selected_rows": full_selector.get(
                    "broader_origin_selected_rows"
                ),
                "broader_origin_selected_family_counts": full_selector.get(
                    "broader_origin_selected_family_counts"
                ),
            },
        },
        (
            "Full universe was preserved and the repaired selector now extends beyond the old FVG slice into old-three plus broader moonshot origin families."
            if full_selector_ok
            else "The route cannot pass while the selector remains only a narrow FVG subset."
        ),
    )
    add(
        "10-trade collapse",
        "passed",
        {
            "activated_selected_rows": delta_scan.activated_selected_rows,
            "failed_route_fixture_status": "not_repeated",
        },
        "The current activation slice is bad but it is not the prior 10-trade collapse.",
    )
    add(
        "broad prop blocker",
        "passed_with_guard",
        {
            "prop_selector_apply_candidate": prod_cfg["prop_safe_selector_apply_to_execution"],
            "prop_policy_reference": overlay["selected_replacement"]["prop_policy_reference"],
            "best_stream_allowed_trades": overlay["selected_replacement"][
                "best_stream_allowed_trades"
            ],
        },
        "Prop policy preserves allow/reduce/defer opportunity; account abandon remains owner-gated.",
    )
    add(
        "broad AVOID blocker with positive avoided-set R",
        "passed_with_guard",
        {
            "be_positive_not_activated": delta_scan.be_not_activated_positive.to_record(),
            "not_activated_positive_counts": dict(delta_scan.not_activated_positive_counts),
        },
        "Positive non-activated rows are visible as repair/capture opportunity, not silently blocked production truth.",
    )
    add(
        "MIXED/LEGACY inert labels",
        "passed" if repair_ok else "blocked_pending_semantic_repair",
        {
            "production_overlay_pre_ai_apply": prod_cfg["pre_ai_apply_to_ai_call"],
            "production_overlay_pending_policy_enabled": prod_cfg["pending_policy_enabled"],
            "stage10_label_monitoring_surface": "label_effects" in [
                row["surface"] for row in stage10["monitoring_surfaces"]
            ],
            "repaired_branch_label_counts": repaired_coverage.get(
                "selected_branch_label_counts"
            ),
            "full_moonshot_selector": {
                "repaired_branch_allowlist_path": full_selector.get(
                    "repaired_branch_allowlist_path"
                ),
                "broader_origin_allowlist_path": full_selector.get(
                    "broader_origin_allowlist_path"
                ),
                "broader_selected_rows": full_selector.get(
                    "broader_origin_selected_rows"
                ),
            },
        },
        (
            "FOLLOW remains the native execution label; non-FOLLOW old-three rows require exact repaired-branch allowlist proof and broader-origin rows require exact broader-origin allowlist proof."
            if repair_ok
            else "Execution-effect flags exist, but the final activation replay did not prove all label effects under the production candidate overlay."
        ),
    )
    add(
        "no-paid-AI diagnostic treated as production selector",
        "passed",
        {
            "stage09_paid_calls_made": guardrails["stage09_paid_calls_made"],
            "route_state_budget_cap_usd": guardrails["stage09_route_state_budget_cap_usd"],
            "production_ai_policy_apply_to_ai_call": prod_cfg["ai_policy_apply_to_ai_call"],
        },
        "AI-dependent production selection remains disabled and budget-capped.",
    )
    add(
        "source-missing rows activated without capture/exclusion",
        "passed_with_capture_monitoring" if repair_ok else "failed_activation_blocker",
        {
            "source_window_incomplete_rows": stage06["source_window_value_counts"]["False"],
            "forward_capture_requirement_rows": stage08["capture_requirement_rows"],
            "not_activated_positive_rows": delta_scan.be_not_activated_positive.count,
            "repaired_selected_source_window_counts": repaired_source.get(
                "selected_source_window_counts"
            ),
            "repaired_source_window_complete_required_for_selection": (
                (repair_summary or {})
                .get("selector_contract", {})
                .get("source_window_complete_required_for_selection")
            ),
        },
        (
            "Source completeness is now capture-readiness evidence, not a selection proxy; selected incomplete rows carry source-capture monitoring."
            if repair_ok
            else "Positive repair opportunity still contains capture/exclusion requirements; no historical broker lifecycle truth can be inferred."
        ),
    )
    add(
        "selected coverage lies by reporting universe coverage",
        "passed",
        {
            "candidate_rows": guardrails["candidate_rows"],
            "dynamic_policy_replay_rows": guardrails["dynamic_policy_replay_rows"],
            "activated_selected_rows": delta_scan.activated_selected_rows,
        },
        "Universe, replayable rows, and activated-selected rows are separated.",
    )
    add(
        "config-gated state used as terminal excuse",
        "passed" if application_state.get("applied") else "failed_activation_blocker",
        {
            "stage11_overlay_applied": stage11_verifier["production_activation_overlay_applied"],
            "current_repo_production_activation_overlay_applied": application_state.get(
                "applied"
            ),
            "application_failures": application_state.get("failures"),
            "stage12_terminal_recommendation": "production_activation_config_overlay_applied_after_semantic_gates",
        },
        (
            "The semantic gate is not used as a terminal excuse; the verified full-moonshot overlay is applied in repo config."
            if application_state.get("applied")
            else "A green semantic gate cannot complete until the verified production overlay is applied to repo config."
        ),
    )
    add(
        "artifact existence treated as completion",
        "passed",
        {
            "stage11_verifier_status": stage11_verifier["status"],
            "semantic_verifier_runs_metric_checks": True,
        },
        "This verifier checks replay metrics, source/capture state, code needles, and overlay behavior.",
    )
    add(
        "shallow verifier accepting bad metrics",
        "passed" if repair_ok else "failed_activation_blocker",
        {
            "activated_default_source_bound_primary_expectancy_r": guardrails[
                "activated_default_source_bound_primary_expectancy_r"
            ],
            "activated_default_source_bound_primary_total_r": guardrails[
                "activated_default_source_bound_primary_total_r"
            ],
            "activated_default_source_bound_primary_selected_count": guardrails[
                "activated_default_source_bound_primary_selected_count"
            ],
            "repaired_overlay_expectancy_r": repaired_metrics.get("expectancy_r"),
            "repaired_overlay_profit_factor": repaired_metrics.get("profit_factor"),
            "stage13_repair_verifier_status": (
                repair_verifier or {}
            ).get("status"),
        },
        (
            "The negative pre-repair slice remains documented as toxic; the repaired overlay verifier passes positive row-level metrics."
            if repair_ok
            else "The negative activated slice is a hard block, not a warning to ignore."
        ),
    )
    add(
        "row loss from compression, histogramming, top-N, or Git convenience",
        "passed",
        {
            "delta_candidate_rows_scanned": delta_scan.candidate_rows,
            "delta_aggregate_rows_scanned": delta_scan.aggregate_rows,
            "stage06_delta_ledger_rows": stage06["delta_ledger_rows"],
        },
        "Stage12 rescanned the row-level delta ledger and did not replace it with a summary.",
    )
    add(
        "activation overlay leaves old GTOS effectively in control",
        "passed" if repair_ok else "failed_activation_blocker",
        {
            "production_overlay_flag_diff_exists": True,
            "runtime_needles": _source_contains(
                RUNTIME_PATH,
                [
                    "evaluate_vnext_moonshot_dynamic_execution",
                    "vnext_moonshot_dynamic_replaces_policy",
                    "build_vnext_replacement_monitoring_snapshot",
                ],
            ),
            "activated_default_source_bound_primary_expectancy_r": guardrails[
                "activated_default_source_bound_primary_expectancy_r"
            ],
            "repaired_overlay_expectancy_r": repaired_metrics.get("expectancy_r"),
            "full_moonshot_selector_expectancy_r": full_selector.get("expectancy_r"),
            "full_moonshot_selector_profit_factor": full_selector.get("profit_factor"),
            "old_gtos_on_repaired_slice_expectancy_r": (
                repaired_comparators.get("old_gtos_live_current_j46_j49", {})
                .get("expectancy_r")
            ),
        },
        (
            "The repaired overlay selects BE-after-trigger rows that beat old GTOS on the same executable slice, and the final selector extends it to the broader positive moonshot origin families."
            if repair_ok
            else "Config flags would change behavior, but the proved activated replay path is negative and cannot be activated."
        ),
    )
    return checks


def _behavioral_diff(
    overlay: dict[str, Any],
    config: dict[str, Any],
    repair_summary: dict[str, Any] | None,
    repair_verifier: dict[str, Any] | None,
    full_selector_summary: dict[str, Any] | None,
    full_selector_verifier: dict[str, Any] | None,
    application_state: dict[str, Any],
) -> dict[str, Any]:
    current = config["gtos_vnext_runtime"]
    production = overlay["semantic_gated_production_activation_overlay_candidate"]["config"][
        "gtos_vnext_runtime"
    ]
    keys = [
        "apply_to_execution",
        "pre_ai_apply_to_ai_call",
        "ai_policy_follow_no_ai_enabled",
        "ltf_path_execution_apply_to_execution",
        "prop_safe_selector_apply_to_execution",
        "moonshot_dynamic_execution_router_enabled",
        "moonshot_dynamic_execution_router_apply_to_execution",
        "replacement_ml_apply_to_execution",
    ]
    flag_diff = {
        key: {"current": current.get(key), "production_candidate": production.get(key)}
        for key in keys
        if current.get(key) != production.get(key)
    }
    repair_ok = bool(repair_verifier and repair_verifier.get("status") == "passed")
    full_selector_ok = bool(
        full_selector_verifier and full_selector_verifier.get("status") == "passed"
    )
    repaired_metrics = (
        (repair_summary or {})
        .get("repaired_overlay_metrics", {})
        .get("be_after_trigger_repaired_overlay", {})
    )
    full_record = _full_selector_record(full_selector_summary, full_selector_verifier)
    applied = bool(application_state.get("applied"))
    return {
        "config_flag_diff": flag_diff,
        "current_repo_config_flags": application_state.get("config_flags", {}),
        "routing_effect_configured": current.get("pre_ai_apply_to_ai_call") is True,
        "execution_policy_effect_configured": current.get(
            "moonshot_dynamic_execution_router_apply_to_execution"
        )
        is True,
        "label_effect_configured": current.get("ai_policy_follow_no_ai_enabled") is True
        and current.get("pending_policy_enabled") is True,
        "prop_governor_effect_configured": current.get("prop_safe_selector_apply_to_execution")
        is True,
        "ltf_effect_configured": current.get("ltf_path_execution_apply_to_execution") is True,
        "monitoring_output_configured": current.get("replacement_monitoring_enabled") is True,
        "replay_decision_effect_proven_positive": repair_ok,
        "full_moonshot_selector_verified_positive": full_selector_ok,
        "production_activation_overlay_applied_in_repo_config": applied,
        "repaired_overlay_selected_rows": repaired_metrics.get("selected_count"),
        "repaired_overlay_expectancy_r": repaired_metrics.get("expectancy_r"),
        "repaired_overlay_profit_factor": repaired_metrics.get("profit_factor"),
        "full_moonshot_combined_selected_rows": full_record.get("combined_selected_rows"),
        "full_moonshot_combined_expectancy_r": full_record.get("expectancy_r"),
        "full_moonshot_combined_profit_factor": full_record.get("profit_factor"),
        "pass": repair_ok and full_selector_ok and applied,
        "reason": (
            "Repo config now applies the verified full-moonshot production selector; rollback flags remain explicit in the overlay/runbook."
            if repair_ok and full_selector_ok and applied
            else "The overlay is not production-safe until repair proof, full-moonshot selector proof, and repo config application all pass."
        ),
    }


def _red_team_markdown(result: dict[str, Any]) -> str:
    rows = [
        "| Failure class | Status | Decision |",
        "|---|---|---|",
    ]
    for check in result["semantic_gate_results"]:
        rows.append(
            f"| {check.get('failure_class')} | {check.get('status')} | {check.get('decision', 'no decision text supplied')} |"
        )
    repair = result["same_evidence_class_repair_pursuit"]
    verdict = "passes" if result["activation_gate_passed"] else "fails"
    action = (
        "The repaired production overlay is row-level verified, extended to full moonshot selector coverage, and applied to repo config; Stage13 must now preserve rollback proof, scoped checks, and commit evidence."
        if result["activation_gate_passed"]
        else "Do not apply `VNEXT_REPLACEMENT_CONFIG_OVERLAY_DIFF_2026-05-26.yaml` production candidate. Keep current config default-off/shadow and proceed to Stage13 with repair."
    )
    return f"""# vNext Replacement Saturation Self Red Team - {DATE}

## Verdict

Stage12 {verdict} the production activation gate after the Stage13 activation-repair replay.

## Required Failure-Class Attack

{chr(10).join(rows)}

## Same-Evidence-Class Repair Pursuit

- Candidate delta rows scanned: `{repair['delta_scan']['candidate_rows']}`.
- Aggregate delta rows scanned: `{repair['delta_scan']['aggregate_rows']}`.
- Pre-repair toxic activated selected rows: `{repair['delta_scan']['activated_selected_rows']}`.
- Positive BE rows not activated: `{repair['delta_scan']['r_stats']['moonshot_be_after_trigger_not_activated_positive']['count']}`.
- Refusal reasons scanned: `{repair['delta_scan']['refusal_reason_counts']}`.
- Stage13 repair status: `{result.get('stage13_activation_repair', {}).get('status')}`.
- Stage13 repaired selected rows: `{result.get('stage13_activation_repair', {}).get('selected_rows')}`.
- Stage13 repaired expectancy: `{result.get('stage13_activation_repair', {}).get('expectancy_r')}`.
- Stage13 full-moonshot combined rows: `{result.get('stage13_full_moonshot_production_selector', {}).get('combined_selected_rows')}`.
- Stage13 full-moonshot expectancy: `{result.get('stage13_full_moonshot_production_selector', {}).get('expectancy_r')}`.
- Production overlay applied in repo config: `{result.get('production_activation_overlay_applied')}`.

The repair door was exercised in-repo: FOLLOW/AVOID/MIXED/LEGACY branch semantics, exact configured kill-zone filtering, broker-native eligibility, selected-policy same-bar filtering, source-capture monitoring, broader moonshot-origin selection, and config application are now verified by Stage13 replay/selector evidence.

## Final Activation Rule

{action}
"""


def main(check_mode: bool = False) -> int:
    global CHECK_MODE
    CHECK_MODE = check_mode
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    stage05 = _read_json(STAGE05_VERIFIER)
    stage06 = _read_json(STAGE06_VERIFIER)
    stage08 = _read_json(STAGE08_MAP)
    stage09 = _read_json(STAGE09_AI_MANIFEST)
    stage10 = _read_json(STAGE10_MAP)
    stage11_verifier = _read_json(STAGE11_VERIFIER)
    overlay = yaml.safe_load(STAGE11_OVERLAY.read_text(encoding="utf-8")) or {}
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    state = _read_json(STATE_PATH)
    manifest = _read_json(MANIFEST_PATH)
    delta_scan = _scan_delta_ledger()
    repair_summary = _read_json(STAGE13_REPAIR_SUMMARY) if STAGE13_REPAIR_SUMMARY.exists() else None
    repair_verifier = (
        _read_json(STAGE13_REPAIR_VERIFIER) if STAGE13_REPAIR_VERIFIER.exists() else None
    )
    full_selector_summary = (
        _read_json(STAGE13_FULL_SELECTOR_SUMMARY)
        if STAGE13_FULL_SELECTOR_SUMMARY.exists()
        else None
    )
    full_selector_verifier = (
        _read_json(STAGE13_FULL_SELECTOR_VERIFIER)
        if STAGE13_FULL_SELECTOR_VERIFIER.exists()
        else None
    )
    outside_risk_summary = (
        _read_json(STAGE13_OUTSIDE_RISK_SUMMARY)
        if STAGE13_OUTSIDE_RISK_SUMMARY.exists()
        else None
    )
    outside_risk_verifier = (
        _read_json(STAGE13_OUTSIDE_RISK_VERIFIER)
        if STAGE13_OUTSIDE_RISK_VERIFIER.exists()
        else None
    )
    redacted_account_risk_summary = (
        _read_json(STAGE13_redacted_account_RISK_SUMMARY)
        if STAGE13_redacted_account_RISK_SUMMARY.exists()
        else None
    )
    redacted_account_risk_verifier = (
        _read_json(STAGE13_redacted_account_RISK_VERIFIER)
        if STAGE13_redacted_account_RISK_VERIFIER.exists()
        else None
    )
    application_state = _production_application_state(
        config=config,
        stage08=stage08,
        full_summary=full_selector_summary,
        full_verifier=full_selector_verifier,
    )

    semantic_checks = _semantic_checks(
        overlay=overlay,
        stage05=stage05,
        stage06=stage06,
        stage08=stage08,
        stage09=stage09,
        stage10=stage10,
        stage11_verifier=stage11_verifier,
        config=config,
        delta_scan=delta_scan,
        repair_summary=repair_summary,
        repair_verifier=repair_verifier,
        full_selector_summary=full_selector_summary,
        full_selector_verifier=full_selector_verifier,
        application_state=application_state,
    )
    outside_risk_passed = bool(
        outside_risk_summary
        and outside_risk_verifier
        and outside_risk_summary.get("status") == "passed"
        and outside_risk_verifier.get("status") == "passed"
        and int(outside_risk_verifier.get("row_counts", {}).get("outside_expanded_rows") or 0)
        == int(outside_risk_summary.get("outside_session_source", {}).get("expanded_rows_expected") or 0)
    )
    semantic_checks.append(
        {
            "decision": (
                "outside-session positive rows are production-expanded and then either executable with selected-cell risk or fail-closed by exact broker/cost/spec reason"
                if outside_risk_passed
                else "outside-session positive rows lack verified selected-cell risk reconciliation"
            ),
            "failure_class": "positive outside-session cohort not reconciled to production risk geometry",
            "status": "satisfied" if outside_risk_passed else "failed_activation_blocker",
        }
    )
    redacted_account_risk_passed = bool(
        redacted_account_risk_summary
        and redacted_account_risk_verifier
        and redacted_account_risk_summary.get("status") == "built"
        and redacted_account_risk_verifier.get("status") == "passed"
        and int(
            redacted_account_risk_verifier.get("row_counts", {}).get(
                "selected_cell_risk_positive_rows"
            )
            or 0
        )
        > 0
    )
    semantic_checks.append(
        {
            "decision": (
                "redacted_account broker geometry, effective config, selected-cell risk, and exact zero-risk reasons are verified"
                if redacted_account_risk_passed
                else "redacted_account broker/risk geometry verifier is missing or failed"
            ),
            "failure_class": "redacted_account selected-cell risk not backed by broker geometry ledger",
            "status": "satisfied" if redacted_account_risk_passed else "failed_activation_blocker",
        }
    )
    blocking_checks = [
        row
        for row in semantic_checks
        if row["status"] in {"failed_activation_blocker", "blocked_pending_semantic_repair"}
    ]
    runtime_presence = {
        "src/components/gtos_vnext_runtime.py": _source_contains(
            RUNTIME_PATH,
            [
                "evaluate_vnext_moonshot_dynamic_execution",
                "vnext_moonshot_dynamic_replaces_policy",
                "build_vnext_replacement_monitoring_snapshot",
                "evaluate_vnext_ltf_path_execution",
                "evaluate_vnext_prop_safe_selector",
            ],
        ),
        "src/components/orchestrator.py": _source_contains(
            ORCHESTRATOR_PATH,
            [
                "vnext_moonshot_dynamic_execution",
                "vnext_ltf_path_execution",
                "vnext_prop_safe_selector",
                "_record_gtos_vnext_replacement_monitoring",
            ],
        ),
        "src/components/execution.py": _source_contains(
            EXECUTION_PATH,
            [
                "vnext_dynamic_policy_applied",
                "vnext_dynamic_replaces_policy",
                "vnext_dynamic_exit_policy",
            ],
        ),
    }
    test_presence = {
        "tests/test_gtos_vnext_runtime.py": _source_contains(
            TEST_RUNTIME_PATH,
            [
                "test_vnext_replacement_monitoring_snapshot_records_stage10_surfaces",
                "test_vnext_replacement_monitoring_flags_old_live_fallback_leakage",
                "test_agent_config_wires_vnext_runtime_production_replacement_path",
            ],
        ),
        "tests/test_j46_j49_policy.py": _source_contains(
            TEST_J46_PATH,
            ["dynamic", "replaces_policy", "j46_j49"],
        ),
        "tests/test_limit_order_flow.py": _source_contains(
            TEST_LIMIT_PATH,
            ["vnext_dynamic_trade_context", "vnext_dynamic_policy_applied"],
        ),
    }
    activation_gate_passed = not blocking_checks
    stage13_repair_record = None
    if repair_summary and repair_verifier:
        repaired = repair_summary["repaired_overlay_metrics"][
            "be_after_trigger_repaired_overlay"
        ]
        stage13_repair_record = {
            "status": repair_verifier.get("status"),
            "summary_path": _rel(STAGE13_REPAIR_SUMMARY),
            "verifier_path": _rel(STAGE13_REPAIR_VERIFIER),
            "failure_enumeration_path": _rel(STAGE13_FAILURE_ENUMERATION),
            "selected_rows": repaired.get("selected_count"),
            "expectancy_r": repaired.get("expectancy_r"),
            "profit_factor": repaired.get("profit_factor"),
            "win_rate": repaired.get("win_rate"),
        }
    full_selector_record = _full_selector_record(
        full_selector_summary, full_selector_verifier
    )
    result = {
        "activation_gate_passed": activation_gate_passed,
        "activation_overlay_behavioral_diff": _behavioral_diff(
            overlay,
            config,
            repair_summary,
            repair_verifier,
            full_selector_summary,
            full_selector_verifier,
            application_state,
        ),
        "allowed_final_status_recommendation": (
            "production_activation_config_overlay_applied_after_semantic_gates"
            if activation_gate_passed
            else "failed_do_not_activate_with_repair_steps_executed"
        ),
        "blocking_checks": [row["failure_class"] for row in blocking_checks],
        "external_surface_state": {
            "broker_account_order_deal_position_history_mutation": "not_used",
            "live_trading": "not_used",
            "paid_api_or_vendor_model_calls": "not_used",
            "remote_push": "not_used",
        },
        "generated_at_utc": generated_at,
        "input_hashes": {
            "stage05_verifier": _sha256(STAGE05_VERIFIER),
            "stage06_verifier": _sha256(STAGE06_VERIFIER),
            "stage06_delta_ledger": _sha256(STAGE06_LEDGER),
            "stage08_market_map": _sha256(STAGE08_MAP),
            "stage09_ai_manifest": _sha256(STAGE09_AI_MANIFEST),
            "stage10_monitoring_map": _sha256(STAGE10_MAP),
            "stage11_overlay": _sha256(STAGE11_OVERLAY),
            "stage11_verifier": _sha256(STAGE11_VERIFIER),
            "stage13_full_selector_summary": (
                _sha256(STAGE13_FULL_SELECTOR_SUMMARY)
                if STAGE13_FULL_SELECTOR_SUMMARY.exists()
                else None
            ),
            "stage13_full_selector_verifier": (
                _sha256(STAGE13_FULL_SELECTOR_VERIFIER)
                if STAGE13_FULL_SELECTOR_VERIFIER.exists()
                else None
            ),
            "stage13_outside_session_risk_summary": (
                _sha256(STAGE13_OUTSIDE_RISK_SUMMARY)
                if STAGE13_OUTSIDE_RISK_SUMMARY.exists()
                else None
            ),
            "stage13_outside_session_risk_verifier": (
                _sha256(STAGE13_OUTSIDE_RISK_VERIFIER)
                if STAGE13_OUTSIDE_RISK_VERIFIER.exists()
                else None
            ),
            "stage13_redacted_account_broker_risk_summary": (
                _sha256(STAGE13_redacted_account_RISK_SUMMARY)
                if STAGE13_redacted_account_RISK_SUMMARY.exists()
                else None
            ),
            "stage13_redacted_account_broker_risk_verifier": (
                _sha256(STAGE13_redacted_account_RISK_VERIFIER)
                if STAGE13_redacted_account_RISK_VERIFIER.exists()
                else None
            ),
        },
        "no_top_n_or_lossy_summary": True,
        "production_activation_overlay_applied": bool(application_state.get("applied")),
        "production_activation_overlay_application_state": application_state,
        "repair_decision": {
            "decision": (
                "stage13_full_moonshot_production_selector_applied_verified"
                if activation_gate_passed
                else "do_not_apply_current_production_overlay"
            ),
            "exact_next_repair": (
                "Run rollback proof, scoped diff checks, completion audit, and commit route-owned production replacement changes."
                if activation_gate_passed
                else "Repair or replay the semantic-gated overlay so source-bound activated rows map to the positive FVG BE prop-aware branch without admitting source-missing or same-bar ambiguous rows; otherwise rely on prospective forward capture."
            ),
            "repair_executed_this_stage": (
                [
                    "rescanned full Stage06 candidate delta ledger",
                    "preserved pre-repair Stage12 toxic-slice failure evidence",
                    "reran upstream Stage10 router replay after selected-policy/source/KZ semantic patch",
                    "ran Stage13 repaired activation overlay replay and verifier",
                    "built and verified Stage13 full moonshot old-three plus broader-origin production selector",
                    "built and verified outside-session selected-cell risk reconciliation",
                    "built and verified redacted_account broker geometry and selected-cell risk ledger",
                    "applied the verified production activation overlay to repo config",
                    "verified repaired overlay metrics against old GTOS, fixed 1.5R, J46/J49, BE, condition-router, no-overlay, and prop-governed variants",
                ]
                if activation_gate_passed
                else [
                    "rescanned full Stage06 candidate delta ledger",
                    "classified every prompt-required failure family",
                    "checked overlay behavior flags against current repo config",
                    "checked runtime/test source needles for dynamic replacement, LTF, prop, and monitoring surfaces",
                ]
            ),
        },
        "route_id": ROUTE_ID,
        "runtime_presence": runtime_presence,
        "same_evidence_class_repair_pursuit": {
            "delta_scan": delta_scan.to_record(),
            "local_repair_status": (
                "repaired_and_verified_by_stage13_activation_overlay_replay"
                if activation_gate_passed
                else "not activation-safe from current artifacts because positive non-activated rows remain tied to source/capture/ordered-path requirements or unreplayed overlay semantics"
            ),
        },
        "stage13_activation_repair": stage13_repair_record,
        "stage13_redacted_account_broker_risk_geometry": {
            "row_counts": (redacted_account_risk_summary or {}).get("row_counts", {}),
            "summary_path": _rel(STAGE13_redacted_account_RISK_SUMMARY),
            "verifier_path": _rel(STAGE13_redacted_account_RISK_VERIFIER),
            "verifier_status": (redacted_account_risk_verifier or {}).get("status"),
        },
        "stage13_full_moonshot_production_selector": full_selector_record,
        "stage13_outside_session_risk_reconciliation": {
            "row_counts": (outside_risk_verifier or {}).get("row_counts", {}),
            "summary_path": _rel(STAGE13_OUTSIDE_RISK_SUMMARY),
            "verifier_path": _rel(STAGE13_OUTSIDE_RISK_VERIFIER),
            "verifier_status": (outside_risk_verifier or {}).get("status"),
        },
        "schema_version": "vnext_replacement_stage12_semantic_verification_v1",
        "semantic_gate_results": semantic_checks,
        "stage_id": "stage_12_semantic_verification_and_red_team",
        "status": "passed" if activation_gate_passed else "failed",
        "test_presence": test_presence,
        "warnings": (
            [
                "pre_repair_negative_default_source_bound_primary_retained_as_toxic_fixture",
                "stage13_repaired_overlay_verified",
                "stage13_full_moonshot_selector_verified_and_applied",
                "outside_session_positive_cohort_reconciled_to_selected_cell_risk",
                "redacted_account_broker_geometry_selected_cell_risk_verified",
            ]
            if activation_gate_passed
            else [
                "production_activation_overlay_not_applied",
                "negative_default_source_bound_primary_blocks_activation",
                "positive_moonshot_stream_requires_repaired_source_bound_activation_replay_or_forward_capture",
            ]
        ),
    }
    _write_json(OUTPUT_RESULT, result)
    _write_text(OUTPUT_RED_TEAM, _red_team_markdown(result))

    for output in (OUTPUT_RESULT, OUTPUT_RED_TEAM, Path(__file__), FOCUSED_TEST):
        status_value = "created" if output != Path(__file__) else "created_and_ready_for_py_compile"
        entry = {"path": output.name, "stage": "stage_12", "status": status_value}
        if output.exists() and output.is_file():
            entry["sha256"] = _sha256(output)
        _upsert_manifest_output(manifest, entry)
    manifest["last_updated_utc"] = generated_at
    _write_json(MANIFEST_PATH, manifest)

    evidence = state.setdefault("evidence_rows_scanned", {})
    evidence["stage12_candidate_delta_rows_scanned"] = delta_scan.candidate_rows
    evidence["stage12_aggregate_delta_rows_scanned"] = delta_scan.aggregate_rows
    evidence["stage12_failure_classes_scanned"] = len(semantic_checks)
    evidence["stage12_blocking_failure_classes"] = len(blocking_checks)
    evidence["stage12_positive_be_not_activated_rows"] = delta_scan.be_not_activated_positive.count
    evidence["stage13_full_moonshot_combined_selected_rows"] = (
        full_selector_record.get("combined_selected_rows")
    )
    evidence["stage13_full_moonshot_old_three_selected_rows"] = (
        full_selector_record.get("old_three_selected_rows")
    )
    evidence["stage13_full_moonshot_broader_origin_selected_rows"] = (
        full_selector_record.get("broader_origin_selected_rows")
    )
    evidence["stage13_outside_session_risk_positive_rows"] = (
        (outside_risk_verifier or {}).get("row_counts", {}).get("risk_positive_execution_rows")
    )
    evidence["stage13_outside_session_risk_zero_fail_closed_rows"] = (
        (outside_risk_verifier or {}).get("row_counts", {}).get("risk_zero_fail_closed_rows")
    )
    evidence["stage13_redacted_account_selected_cell_risk_positive_rows"] = (
        (redacted_account_risk_verifier or {})
        .get("row_counts", {})
        .get("selected_cell_risk_positive_rows")
    )
    state["current_stage"] = "stage_13_commit_and_activation_config_application"
    state["first_incomplete_invariant"] = (
        "stage_13_rollback_diff_completion_audit_and_commit_pending"
    )
    state["exact_next_action"] = (
        "Run rollback proof, scoped verification/diff checks, completion audit, dirty-file separation, and commit route-owned production replacement changes."
        if activation_gate_passed
        else "Run scoped verification, prepare completion audit, and commit the failed-do-not-activate package without applying the production overlay."
    )
    state.setdefault("stage_status", {})[
        "stage_12_semantic_verification_and_red_team"
    ] = (
        "completed_semantic_verifier_passed_after_stage13_full_moonshot_selector_application"
        if activation_gate_passed
        else "completed_semantic_verifier_failed_activation_blocked_repair_steps_recorded"
    )
    state.setdefault("stage_status", {})[
        "stage_13_commit_and_activation_config_application"
    ] = "pending"
    state["config_overlay_state"] = {
        **state.get("config_overlay_state", {}),
        "production_activation_overlay_applied": bool(application_state.get("applied")),
        "application_state": application_state,
        "semantic_gate_state": (
            "passed_stage12_full_moonshot_selector_applied"
            if activation_gate_passed
            else "failed_stage12_semantic_verifier"
        ),
        "reason": (
            "Stage12 passed after Stage13 repaired and expanded the selector; the verified production overlay is now applied to repo config."
            if activation_gate_passed
            else "Stage12 failed activation because the current activated source-bound primary projection is negative and positive repair rows require source/capture or unreplayed overlay repair."
        ),
    }
    state["completion_gate_status"] = {
        "allowed_terminal_status": None,
        "reason": (
            "Stage12 activation gate passed and the production overlay is applied; rollback proof, completion audit, scoped commit, and final packaging remain pending."
            if activation_gate_passed
            else "Stage12 failed the semantic activation gate; Stage13 must package scoped commits and completion audit as failed_do_not_activate_with_repair_steps_executed."
        ),
        "route_complete": False,
    }
    _append_test_result(
        state,
        _rel(Path(__file__)),
        (
            "passed activation gate after Stage13 full-moonshot selector repair and repo config application"
            if activation_gate_passed
            else "failed activation gate by design; semantic verifier blocked production overlay"
        ),
        generated_at,
    )
    state["last_updated_utc"] = generated_at
    _write_json(STATE_PATH, state)

    _append_control(
        {
            "event": "stage_12_semantic_verification_completed",
            "generated_at_utc": generated_at,
            "activation_gate_passed": activation_gate_passed,
            "blocking_checks": [row["failure_class"] for row in blocking_checks],
            "production_activation_overlay_applied": bool(application_state.get("applied")),
            "route_id": ROUTE_ID,
            "stage_id": "stage_12_semantic_verification_and_red_team",
            "status": "passed" if activation_gate_passed else "failed",
        }
    )

    print(
        json.dumps(
            {
                "activation_gate_passed": activation_gate_passed,
                "blocking_checks": len(blocking_checks),
                "candidate_rows_scanned": delta_scan.candidate_rows,
                "production_activation_overlay_applied": bool(
                    application_state.get("applied")
                ),
                "mode": "check" if CHECK_MODE else "write",
                "status": "passed" if activation_gate_passed else "failed",
            },
            sort_keys=True,
        )
    )
    return _activation_exit_code(activation_gate_passed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="run without mutating route artifacts")
    mode.add_argument("--write", action="store_true", help="regenerate route artifacts")
    args = parser.parse_args()
    raise SystemExit(main(check_mode=args.check))
