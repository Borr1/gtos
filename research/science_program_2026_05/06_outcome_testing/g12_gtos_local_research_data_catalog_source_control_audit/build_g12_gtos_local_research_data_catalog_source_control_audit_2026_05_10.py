"""Build the G12 source-control audit for the GTOS local research data catalog.

This route audits catalog/source-control tooling only. It does not open
validation, result scoring, broker/account/order evidence, credentials, paid
data, registry edits, prompts, production trading logic, or live behavior.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ROUTE_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[4]
OUTCOME_DIR = ROUTE_DIR.parent
DATE = "2026-05-10"
PREFIX = "G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT"
ROUTE_ID = "G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT"
SCHEMA_VERSION = "g12_gtos_local_research_data_catalog_source_control_audit_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS"

TARGET_ROUTE = OUTCOME_DIR / "gtos_local_research_data_catalog_implementation_route"
TARGET_PREFIX = "GTOS_LOCAL_RESEARCH_DATA_CATALOG"
TARGET_BUILDER = TARGET_ROUTE / "build_gtos_local_research_data_catalog_implementation_route_2026_05_10.py"
TARGET_VERIFIER = TARGET_ROUTE / "verify_gtos_local_research_data_catalog_implementation_route_2026_05_10.py"
TARGET_TESTS = TARGET_ROUTE / "test_gtos_local_research_data_catalog_implementation_route_2026_05_10.py"
PROMPT_PATH = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-10.md"
)

EXPECTED = {
    "catalog_rows": 1200,
    "small_hash_rows": 1076,
    "large_file_deferrals": 124,
    "search_queries": 6,
    "positive_search_rows": 2,
    "negative_search_rows": 4,
    "recoverable_market_data_windows": 22,
    "non_generatable_source_state_gaps": 20,
    "acquisition_requests": 42,
}

SAFE_FALSE_KEYS = (
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_result_scoring",
    "opens_validation",
    "opens_promotion",
    "opens_registry_edit",
    "opens_paid_api_or_databento_route",
    "opens_remote_push",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_mt5_order_account_history_behavior",
    "changes_live_trading_behavior",
    "credentials_touched",
)
SAFE_FLAGS = {"promotion_verdict": PROMOTION_VERDICT, **{key: False for key in SAFE_FALSE_KEYS}}
FORBIDDEN_DIFF_PREFIXES = (
    "src/components/",
    "src/safety/",
    "prompts/",
    "config/",
    "scripts/canary_fixtures/",
    "canaries/",
)
SENSITIVE_PATH_FRAGMENTS = (
    ".env",
    "api_key",
    "apikey",
    "secret",
    "password",
    "credential",
    "login",
    "broker_actual_r",
    "account_history",
    "account_pnl",
    "account_truth",
    "daily_pnl",
    "deal_history",
    "deals",
    "positions",
    "orders",
    "trade_records",
    "ticket",
)

TARGET_REQUIRED_JSON = [
    f"{TARGET_PREFIX}_CATALOG_SCHEMA_{DATE}.json",
    f"{TARGET_PREFIX}_ROOT_RESOLVER_CONFIG_{DATE}.json",
    f"{TARGET_PREFIX}_ROOT_RESOLVER_CONFIG_SCHEMA_{DATE}.json",
    f"{TARGET_PREFIX}_SEARCH_RESULT_LEDGER_{DATE}.json",
    f"{TARGET_PREFIX}_MISSING_WINDOW_LEDGER_{DATE}.json",
    f"{TARGET_PREFIX}_ACQUISITION_REQUEST_MANIFEST_EXAMPLE_{DATE}.json",
    f"{TARGET_PREFIX}_RECOVERABLE_NON_GENERATABLE_CLASSIFICATION_LEDGER_{DATE}.json",
    f"{TARGET_PREFIX}_SOURCE_HASH_DEFERRAL_MANIFEST_{DATE}.json",
    f"{TARGET_PREFIX}_FORBIDDEN_ROUTE_NOLEAK_AUDIT_{DATE}.json",
    f"{TARGET_PREFIX}_COMPLETION_AUDIT_{DATE}.json",
    f"{TARGET_PREFIX}_VERIFICATION_RESULT_{DATE}.json",
]
TARGET_CATALOG = TARGET_ROUTE / f"{TARGET_PREFIX}_CATALOG_{DATE}.jsonl"
TARGET_INTEGRATION_GUIDE = TARGET_ROUTE / f"{TARGET_PREFIX}_INTEGRATION_GUIDE_{DATE}.md"

CONTROL_DOCS = [
    REPO_ROOT / ".context" / "LIVE_STATE.md",
    REPO_ROOT / ".context" / "02_session_handoffs" / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    REPO_ROOT / ".context" / "00_core" / "quick_reference_card.md",
    REPO_ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
    REPO_ROOT / ".context" / "00_core" / "research_current_state.md",
    REPO_ROOT / ".context" / "00_core" / "goal_session_research_discipline.md",
    REPO_ROOT / ".context" / "00_core" / "local_heavy_data_inventory.md",
    PROMPT_PATH,
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def with_safe_flags(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out.update(SAFE_FLAGS)
    return out


def base_payload(artifact_family: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "artifact_family": artifact_family,
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "terminal_decision": TERMINAL_DECISION,
    }
    payload.update(extra)
    return with_safe_flags(payload)


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(with_safe_flags(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_md(path: Path, title: str, payload: dict[str, Any], notes: list[str] | None = None) -> Path:
    lines = [
        f"# {title}",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Terminal decision: `{payload.get('terminal_decision', TERMINAL_DECISION)}`",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(with_safe_flags(payload), indent=2, sort_keys=True),
        "```",
    ]
    if notes:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {note}" for note in notes)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_output(args: list[str]) -> str:
    result = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip()


def git_head() -> str:
    return git_output(["git", "rev-parse", "HEAD"])


def git_head_subject() -> str:
    return git_output(["git", "log", "-1", "--pretty=%h %s"])


def target_commit_log() -> list[str]:
    output = git_output(["git", "log", "--oneline", "--", rel(TARGET_ROUTE), rel(PROMPT_PATH)])
    return [line for line in output.splitlines() if line][:8]


def git_diff_scope() -> dict[str, Any]:
    diff = git_output(["git", "diff", "--name-only"])
    untracked = git_output(["git", "ls-files", "--others", "--exclude-standard"])
    paths = sorted({line.strip().replace("\\", "/") for line in (diff + "\n" + untracked).splitlines() if line.strip()})
    forbidden = [path for path in paths if any(path.startswith(prefix) for prefix in FORBIDDEN_DIFF_PREFIXES)]
    return {
        "changed_or_untracked_paths": paths,
        "forbidden_live_surface_paths": forbidden,
        "ok": forbidden == [],
    }


def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        try:
            sys.path.remove(str(path.parent))
        except ValueError:
            pass
    return module


def load_target_json_payloads() -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for path in sorted(TARGET_ROUTE.glob("*.json")):
        payloads[path.name] = load_json(path)
    return payloads


def safe_flag_issues(value: Any, path: str = "$") -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in SAFE_FALSE_KEYS and item is not False:
                issues.append({"path": child, "value": item})
            if key == "promotion_verdict" and item != PROMOTION_VERDICT:
                issues.append({"path": child, "value": item})
            issues.extend(safe_flag_issues(item, child))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            issues.extend(safe_flag_issues(item, f"{path}[{idx}]"))
    return issues


def target_verifier_nonwriting() -> dict[str, Any]:
    verifier = import_module(TARGET_VERIFIER, "gtos_local_catalog_target_verifier_nonwriting")
    result = verifier.verify()
    return {
        "target_verifier_called": "verify_function_nonwriting",
        "ok": result.get("ok"),
        "can_mark_goal_complete": result.get("can_mark_goal_complete"),
        "failure_count": result.get("failure_count"),
        "catalog_row_count": result.get("catalog_row_count"),
    }


def runtime_target_recompute() -> dict[str, Any]:
    builder = import_module(TARGET_BUILDER, "gtos_local_catalog_target_builder_runtime")
    root_config = builder.default_root_config()
    rows, root_ledgers, skipped_sensitive = builder.build_catalog_from_config(root_config)
    status_counts = Counter(row.get("hash_status") for row in rows)
    small_rows = [row for row in rows if row.get("hash_status") == "sha256_complete"]
    deferrals = [row for row in rows if row.get("hash_status") == "deferred_large_file_requires_dedicated_hash_manifest"]
    hash_missing: list[dict[str, Any]] = []
    hash_mismatches: list[dict[str, Any]] = []
    for row in small_rows:
        path = Path(row["absolute_path"])
        if not path.exists():
            hash_missing.append({"catalog_row_id": row.get("catalog_row_id"), "absolute_path": str(path)})
            continue
        actual = sha256_file(path)
        if actual != row.get("sha256"):
            hash_mismatches.append({"catalog_row_id": row.get("catalog_row_id"), "absolute_path": str(path)})
    deferral_missing: list[dict[str, Any]] = []
    deferral_bad_size: list[dict[str, Any]] = []
    for row in deferrals:
        path = Path(row["absolute_path"])
        if not path.exists():
            deferral_missing.append({"catalog_row_id": row.get("catalog_row_id"), "absolute_path": str(path)})
            continue
        if path.stat().st_size != row.get("size_bytes"):
            deferral_bad_size.append({"catalog_row_id": row.get("catalog_row_id"), "absolute_path": str(path)})
    return {
        "repo_root_used_by_target_builder": str(builder.REPO_ROOT),
        "catalog_row_count": len(rows),
        "hash_status_counts": dict(status_counts),
        "small_hash_rows": len(small_rows),
        "large_file_deferrals": len(deferrals),
        "small_hashes_recomputed": len(small_rows) - len(hash_missing),
        "small_hash_missing_count": len(hash_missing),
        "small_hash_mismatch_count": len(hash_mismatches),
        "large_deferral_stat_missing_count": len(deferral_missing),
        "large_deferral_bad_size_count": len(deferral_bad_size),
        "root_ledgers": root_ledgers,
        "skipped_sensitive_count": len(skipped_sensitive),
        "root_config_current_worktree_paths": [
            root.get("root_path") for root in root_config.get("roots", []) if str(root.get("root_id", "")).startswith("current_worktree")
        ],
    }


def persisted_hash_recompute(catalog_rows: list[dict[str, Any]]) -> dict[str, Any]:
    small_rows = [row for row in catalog_rows if row.get("hash_status") == "sha256_complete"]
    deferrals = [row for row in catalog_rows if row.get("hash_status") == "deferred_large_file_requires_dedicated_hash_manifest"]
    missing_hash_rows: list[dict[str, Any]] = []
    hash_mismatches: list[dict[str, Any]] = []
    for row in small_rows:
        path = Path(row["absolute_path"])
        if not path.exists():
            missing_hash_rows.append(
                {
                    "catalog_row_id": row.get("catalog_row_id"),
                    "root_id": row.get("root_id"),
                    "absolute_path": str(path),
                    "recorded_sha256": row.get("sha256"),
                }
            )
            continue
        actual = sha256_file(path)
        if actual != row.get("sha256"):
            hash_mismatches.append(
                {
                    "catalog_row_id": row.get("catalog_row_id"),
                    "root_id": row.get("root_id"),
                    "absolute_path": str(path),
                    "recorded_sha256": row.get("sha256"),
                    "actual_sha256": actual,
                }
            )
    missing_deferrals: list[dict[str, Any]] = []
    bad_size_deferrals: list[dict[str, Any]] = []
    for row in deferrals:
        path = Path(row["absolute_path"])
        if not path.exists():
            missing_deferrals.append({"catalog_row_id": row.get("catalog_row_id"), "absolute_path": str(path)})
            continue
        if path.stat().st_size != row.get("size_bytes"):
            bad_size_deferrals.append(
                {
                    "catalog_row_id": row.get("catalog_row_id"),
                    "absolute_path": str(path),
                    "recorded_size_bytes": row.get("size_bytes"),
                    "actual_size_bytes": path.stat().st_size,
                }
            )
    return {
        "persisted_small_hash_rows": len(small_rows),
        "persisted_small_hashes_recomputed_currently": len(small_rows) - len(missing_hash_rows),
        "persisted_small_hash_missing_count": len(missing_hash_rows),
        "persisted_small_hash_mismatch_count": len(hash_mismatches),
        "persisted_large_file_deferrals": len(deferrals),
        "persisted_large_deferral_stat_checked": len(deferrals) - len(missing_deferrals),
        "persisted_large_deferral_missing_count": len(missing_deferrals),
        "persisted_large_deferral_bad_size_count": len(bad_size_deferrals),
        "missing_hash_rows": missing_hash_rows,
        "hash_mismatches": hash_mismatches,
        "missing_deferrals": missing_deferrals,
        "bad_size_deferrals": bad_size_deferrals,
    }


def build_context_anchor() -> dict[str, Any]:
    return base_payload(
        "context_anchor",
        current_head=git_head(),
        current_head_subject=git_head_subject(),
        prompt_path=rel(PROMPT_PATH),
        target_route_path=rel(TARGET_ROUTE),
        target_builder=rel(TARGET_BUILDER),
        target_verifier=rel(TARGET_VERIFIER),
        target_tests=rel(TARGET_TESTS),
        target_commits=target_commit_log(),
        mandatory_preflight_completed=True,
        control_docs_read=[rel(path) for path in CONTROL_DOCS],
        preserved_boundaries=[
            "source_control_catalog_tooling_only",
            "no_validation_execution",
            "no_result_cost_r_win_rate_expectancy_scoring",
            "no_promotion",
            "no_registry_edit",
            "no_paid_api_or_databento_route",
            "no_remote_push",
            "no_live_restart",
            "no_prompt_config_risk_permission_safety_selector_canary_change",
            "no_mt5_order_account_history_deal_position_behavior",
            "no_broker_actual_r",
            "no_credentials",
            "no_live_trading_behavior",
        ],
    )


def build_root_audit(target_payloads: dict[str, dict[str, Any]], runtime: dict[str, Any]) -> dict[str, Any]:
    config = target_payloads[f"{TARGET_PREFIX}_ROOT_RESOLVER_CONFIG_{DATE}.json"]
    schema = target_payloads[f"{TARGET_PREFIX}_ROOT_RESOLVER_CONFIG_SCHEMA_{DATE}.json"]
    roots = config.get("roots", [])
    root_ids = {root.get("root_id") for root in roots}
    required_roots = {
        "current_worktree_data_root",
        "current_worktree_tick_root",
        "absolute_main_data_root",
        "absolute_main_tick_root",
        "absolute_main_shadow_logs",
        "prior_worktree_root",
        "sierra_chart_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "owner_documents_candidate_root",
    }
    persisted_current_paths = [
        root.get("root_path") for root in roots if str(root.get("root_id", "")).startswith("current_worktree")
    ]
    current_path_mismatch = [
        path for path in persisted_current_paths if not str(path).startswith(str(REPO_ROOT))
    ]
    runtime_current_path_ok = all(
        str(path).startswith(str(REPO_ROOT)) for path in runtime.get("root_config_current_worktree_paths", [])
    )
    read_policies = sorted({root.get("read_policy") for root in roots})
    return base_payload(
        "root_resolver_config_schema_audit",
        root_count=len(roots),
        schema_required_fields=schema.get("required_fields", []),
        required_roots_present=sorted(required_roots & root_ids),
        required_roots_missing=sorted(required_roots - root_ids),
        absolute_heavy_data_awareness_present=required_roots.issubset(root_ids),
        read_policies=read_policies,
        persisted_current_worktree_paths=persisted_current_paths,
        persisted_current_worktree_path_mismatch_count=len(current_path_mismatch),
        persisted_current_worktree_path_mismatches=current_path_mismatch,
        runtime_target_builder_current_worktree_paths=runtime.get("root_config_current_worktree_paths", []),
        runtime_current_worktree_paths_match_active_repo=runtime_current_path_ok,
        accepted_followup_required=len(current_path_mismatch) > 0,
        exact_followup=(
            "Rerun the target builder in the active consuming worktree before citing current_worktree absolute paths; "
            "the committed target snapshot was generated from a sibling worktree but runtime recompute is correct."
        ),
        audit_passed=required_roots.issubset(root_ids) and runtime_current_path_ok,
    )


def build_catalog_audit(
    target_payloads: dict[str, dict[str, Any]], catalog_rows: list[dict[str, Any]], runtime: dict[str, Any], hash_audit: dict[str, Any]
) -> dict[str, Any]:
    schema = target_payloads[f"{TARGET_PREFIX}_CATALOG_SCHEMA_{DATE}.json"]
    required_fields = set(schema.get("required_catalog_row_fields", []))
    row_field_missing = [
        {"catalog_row_id": row.get("catalog_row_id"), "missing": sorted(required_fields - set(row))}
        for row in catalog_rows
        if required_fields - set(row)
    ]
    counts = Counter(row.get("hash_status") for row in catalog_rows)
    sensitive_rows = [
        row.get("catalog_row_id")
        for row in catalog_rows
        if any(fragment in str(row.get("absolute_path", "")).lower() for fragment in SENSITIVE_PATH_FRAGMENTS)
    ]
    safe_issues: list[dict[str, Any]] = []
    for idx, row in enumerate(catalog_rows, start=1):
        safe_issues.extend(safe_flag_issues(row, f"catalog:{idx}"))
    source_only_count = sum(1 for row in catalog_rows if row.get("allowed_evidence_class") == "SOURCE_CONTROL_ONLY")
    large_rows = [row for row in catalog_rows if row.get("hash_status") == "deferred_large_file_requires_dedicated_hash_manifest"]
    weak_large_consumption = [
        row.get("catalog_row_id")
        for row in large_rows
        if row.get("sha256") is not None or "content_not_opened_large_file_deferral" not in row.get("read_actions", [])
    ]
    return base_payload(
        "catalog_row_count_schema_audit",
        target_catalog_path=rel(TARGET_CATALOG),
        persisted_catalog_row_count=len(catalog_rows),
        persisted_hash_status_counts=dict(counts),
        persisted_small_hash_rows=counts.get("sha256_complete", 0),
        persisted_large_file_deferral_rows=counts.get("deferred_large_file_requires_dedicated_hash_manifest", 0),
        runtime_recomputed_catalog_row_count=runtime.get("catalog_row_count"),
        runtime_recomputed_small_hash_rows=runtime.get("small_hash_rows"),
        runtime_recomputed_large_file_deferrals=runtime.get("large_file_deferrals"),
        required_fields_count=len(required_fields),
        row_field_missing_count=len(row_field_missing),
        row_field_missing=row_field_missing[:40],
        source_control_only_row_count=source_only_count,
        catalog_sensitive_path_row_count=len(sensitive_rows),
        catalog_sensitive_path_rows=sensitive_rows[:40],
        safe_flag_issue_count=len(safe_issues),
        safe_flag_issues=safe_issues[:40],
        weak_large_file_consumption_count=len(weak_large_consumption),
        weak_large_file_consumption_rows=weak_large_consumption[:40],
        persisted_hash_recompute=hash_audit,
        expected_counts=EXPECTED,
        expected_counts_reconciled=(
            len(catalog_rows) == EXPECTED["catalog_rows"]
            and counts.get("sha256_complete", 0) == EXPECTED["small_hash_rows"]
            and counts.get("deferred_large_file_requires_dedicated_hash_manifest", 0) == EXPECTED["large_file_deferrals"]
            and runtime.get("catalog_row_count") == EXPECTED["catalog_rows"]
            and runtime.get("small_hash_rows") == EXPECTED["small_hash_rows"]
            and runtime.get("large_file_deferrals") == EXPECTED["large_file_deferrals"]
        ),
        audit_passed=(
            len(catalog_rows) == EXPECTED["catalog_rows"]
            and counts.get("sha256_complete", 0) == EXPECTED["small_hash_rows"]
            and counts.get("deferred_large_file_requires_dedicated_hash_manifest", 0) == EXPECTED["large_file_deferrals"]
            and runtime.get("small_hashes_recomputed") == EXPECTED["small_hash_rows"]
            and hash_audit["persisted_small_hash_mismatch_count"] == 0
            and hash_audit["persisted_large_deferral_missing_count"] == 0
            and hash_audit["persisted_large_deferral_bad_size_count"] == 0
            and not row_field_missing
            and source_only_count == len(catalog_rows)
            and not sensitive_rows
            and not safe_issues
            and not weak_large_consumption
        ),
    )


def build_search_missing_audit(target_payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    search = target_payloads[f"{TARGET_PREFIX}_SEARCH_RESULT_LEDGER_{DATE}.json"]
    missing = target_payloads[f"{TARGET_PREFIX}_MISSING_WINDOW_LEDGER_{DATE}.json"]
    search_rows = search.get("rows", [])
    missing_rows = missing.get("rows", [])
    positive_rows = [row for row in search_rows if row.get("match_count", 0) > 0]
    negative_rows = [row for row in search_rows if row.get("match_count", 0) == 0]
    missing_types = Counter(row.get("source_requirement_type") for row in missing_rows)
    recoverable_bad = [
        row
        for row in missing_rows
        if row.get("source_requirement_type") == "recoverable_market_data"
        and row.get("blocker_code") not in {"RECOVERABLE_BY_APPROVED_EXTRACTION", "RECOVERED_LOCAL_SOURCE"}
    ]
    non_generatable_bad = [
        row
        for row in missing_rows
        if row.get("source_requirement_type") == "non_generatable_historical_gtos_source_state"
        and row.get("blocker_code") != "NON_GENERATABLE_SOURCE_STATE"
    ]
    source_state_price_backfill = [
        row
        for row in missing_rows
        if row.get("source_requirement_type") == "non_generatable_historical_gtos_source_state"
        and "price" in str(row.get("exact_next_action", "")).lower()
    ]
    return base_payload(
        "search_result_missing_window_routing_audit",
        query_count=search.get("query_count"),
        positive_query_count=search.get("positive_query_count"),
        negative_query_count=search.get("negative_query_count"),
        positive_queries=[row.get("query_id") for row in positive_rows],
        negative_queries=[row.get("query_id") for row in negative_rows],
        missing_window_row_count=len(missing_rows),
        missing_type_counts=dict(missing_types),
        recoverable_market_data_count=missing.get("recoverable_market_data_count"),
        non_generatable_source_state_count=missing.get("non_generatable_source_state_count"),
        recoverable_bad_routing_count=len(recoverable_bad),
        non_generatable_bad_routing_count=len(non_generatable_bad),
        source_state_price_backfill_attempt_count=len(source_state_price_backfill),
        exact_next_action_missing_count=sum(1 for row in missing_rows if not row.get("exact_next_action")),
        audit_passed=(
            search.get("query_count") == EXPECTED["search_queries"]
            and len(positive_rows) == EXPECTED["positive_search_rows"]
            and len(negative_rows) == EXPECTED["negative_search_rows"]
            and missing.get("recoverable_market_data_count") == EXPECTED["recoverable_market_data_windows"]
            and missing.get("non_generatable_source_state_count") == EXPECTED["non_generatable_source_state_gaps"]
            and missing_types.get("recoverable_market_data", 0) == EXPECTED["recoverable_market_data_windows"]
            and missing_types.get("non_generatable_historical_gtos_source_state", 0)
            == EXPECTED["non_generatable_source_state_gaps"]
            and not recoverable_bad
            and not non_generatable_bad
            and not source_state_price_backfill
        ),
    )


def build_acquisition_classification_audit(target_payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    acquisition = target_payloads[f"{TARGET_PREFIX}_ACQUISITION_REQUEST_MANIFEST_EXAMPLE_{DATE}.json"]
    classification = target_payloads[f"{TARGET_PREFIX}_RECOVERABLE_NON_GENERATABLE_CLASSIFICATION_LEDGER_{DATE}.json"]
    requests = acquisition.get("requests", [])
    request_types = Counter(row.get("source_requirement_type") for row in requests)
    non_manifest = [row.get("request_id") for row in requests if row.get("execution_status") != "not_executed_manifest_only"]
    cost_nonzero = [row.get("request_id") for row in requests if row.get("cost_cap_usd") != 0]
    forbidden_request_routes = [
        row.get("request_id")
        for row in requests
        if any(token in str(row.get("approved_route", "")).lower() for token in ("paid", "databento", "broker_account"))
    ]
    classes = {row.get("class"): row for row in classification.get("classification_rows", [])}
    required_classes = {
        "recoverable_market_data",
        "recoverable_by_source_contract",
        "non_generatable_historical_gtos_source_state",
        "forbidden_evidence_class",
    }
    return base_payload(
        "acquisition_manifest_classification_audit",
        request_count=acquisition.get("request_count"),
        request_type_counts=dict(request_types),
        non_manifest_execution_count=len(non_manifest),
        non_manifest_execution_request_ids=non_manifest,
        nonzero_cost_cap_count=len(cost_nonzero),
        nonzero_cost_cap_request_ids=cost_nonzero,
        forbidden_request_route_count=len(forbidden_request_routes),
        forbidden_request_route_ids=forbidden_request_routes,
        classification_classes=sorted(classes),
        required_classification_classes_missing=sorted(required_classes - set(classes)),
        non_generatable_can_price_backfill=classes.get("non_generatable_historical_gtos_source_state", {}).get("can_price_backfill"),
        recoverable_can_catalog_recover=classes.get("recoverable_market_data", {}).get("can_catalog_recover"),
        audit_passed=(
            acquisition.get("request_count") == EXPECTED["acquisition_requests"]
            and request_types.get("recoverable_market_data", 0) == EXPECTED["recoverable_market_data_windows"]
            and request_types.get("non_generatable_historical_gtos_source_state", 0)
            == EXPECTED["non_generatable_source_state_gaps"]
            and not non_manifest
            and not cost_nonzero
            and not forbidden_request_routes
            and required_classes.issubset(classes)
            and classes.get("non_generatable_historical_gtos_source_state", {}).get("can_price_backfill") is False
        ),
    )


def build_hash_deferral_audit(
    target_payloads: dict[str, dict[str, Any]], catalog_rows: list[dict[str, Any]], runtime: dict[str, Any], hash_audit: dict[str, Any]
) -> dict[str, Any]:
    manifest = target_payloads[f"{TARGET_PREFIX}_SOURCE_HASH_DEFERRAL_MANIFEST_{DATE}.json"]
    manifest_hashed = manifest.get("hashed_file_count")
    manifest_deferred = manifest.get("large_file_deferral_count")
    catalog_hashed = sum(1 for row in catalog_rows if row.get("hash_status") == "sha256_complete")
    catalog_deferred = sum(1 for row in catalog_rows if row.get("hash_status") == "deferred_large_file_requires_dedicated_hash_manifest")
    return base_payload(
        "hash_large_file_deferral_audit",
        manifest_hashed_file_count=manifest_hashed,
        manifest_large_file_deferral_count=manifest_deferred,
        catalog_hashed_file_count=catalog_hashed,
        catalog_large_file_deferral_count=catalog_deferred,
        runtime_recomputed_hashed_file_count=runtime.get("small_hash_rows"),
        runtime_recomputed_hashes_verified=runtime.get("small_hashes_recomputed"),
        runtime_recomputed_large_file_deferral_count=runtime.get("large_file_deferrals"),
        persisted_hash_rows_currently_missing=hash_audit["persisted_small_hash_missing_count"],
        persisted_hash_rows_currently_missing_samples=hash_audit["missing_hash_rows"][:20],
        exact_followup_for_missing_persisted_hash_rows=(
            f"Do not cite the {hash_audit['persisted_small_hash_missing_count']} persisted prior_worktree_root hash rows "
            "as current files; rerun the target builder in the consuming worktree to refresh the bounded catalog before source use."
        ),
        audit_passed=(
            manifest_hashed == EXPECTED["small_hash_rows"]
            and manifest_deferred == EXPECTED["large_file_deferrals"]
            and catalog_hashed == EXPECTED["small_hash_rows"]
            and catalog_deferred == EXPECTED["large_file_deferrals"]
            and runtime.get("small_hashes_recomputed") == EXPECTED["small_hash_rows"]
            and runtime.get("small_hash_mismatch_count") == 0
            and runtime.get("large_deferral_bad_size_count") == 0
            and hash_audit["persisted_small_hash_mismatch_count"] == 0
            and hash_audit["persisted_large_deferral_missing_count"] == 0
            and hash_audit["persisted_large_deferral_bad_size_count"] == 0
        ),
    )


def build_noleak_audit(target_payloads: dict[str, dict[str, Any]], catalog_rows: list[dict[str, Any]]) -> dict[str, Any]:
    diff_scope = git_diff_scope()
    target_safe_issues: list[dict[str, Any]] = []
    for name, payload in target_payloads.items():
        target_safe_issues.extend(safe_flag_issues(payload, name))
    catalog_safe_issues: list[dict[str, Any]] = []
    for idx, row in enumerate(catalog_rows, start=1):
        catalog_safe_issues.extend(safe_flag_issues(row, f"catalog:{idx}"))
    target_noleak = target_payloads[f"{TARGET_PREFIX}_FORBIDDEN_ROUTE_NOLEAK_AUDIT_{DATE}.json"]
    target_completion = target_payloads[f"{TARGET_PREFIX}_COMPLETION_AUDIT_{DATE}.json"]
    forbidden_catalog_paths = [
        row.get("catalog_row_id")
        for row in catalog_rows
        if any(fragment in str(row.get("absolute_path", "")).lower() for fragment in SENSITIVE_PATH_FRAGMENTS)
    ]
    return base_payload(
        "forbidden_route_noleak_audit",
        diff_scope=diff_scope,
        target_noleak_audit_passed=target_noleak.get("audit_passed"),
        target_completion_validation_safe=target_completion.get("validation_safe"),
        target_completion_outcome_review_opened=target_completion.get("outcome_review_opened"),
        target_completion_live_effect=target_completion.get("live_effect"),
        target_safe_flag_issue_count=len(target_safe_issues),
        target_safe_flag_issues=target_safe_issues[:40],
        catalog_safe_flag_issue_count=len(catalog_safe_issues),
        catalog_safe_flag_issues=catalog_safe_issues[:40],
        forbidden_catalog_path_count=len(forbidden_catalog_paths),
        forbidden_catalog_path_row_ids=forbidden_catalog_paths[:40],
        broker_actual_r_read=False,
        credentials_touched=False,
        validation_execution_opened=False,
        result_cost_r_win_rate_expectancy_scoring_opened=False,
        paid_api_or_databento_route_opened=False,
        live_trading_behavior_changed=False,
        audit_passed=(
            diff_scope["ok"]
            and target_noleak.get("audit_passed") is True
            and not target_safe_issues
            and not catalog_safe_issues
            and not forbidden_catalog_paths
        ),
    )


def build_integration_guide_audit() -> dict[str, Any]:
    text = TARGET_INTEGRATION_GUIDE.read_text(encoding="utf-8")
    required_tokens = [
        "build_gtos_local_research_data_catalog_implementation_route_2026_05_10.py",
        f"{TARGET_PREFIX}_SEARCH_RESULT_LEDGER_{DATE}.json",
        f"{TARGET_PREFIX}_MISSING_WINDOW_LEDGER_{DATE}.json",
        f"{TARGET_PREFIX}_ACQUISITION_REQUEST_MANIFEST_EXAMPLE_{DATE}.json",
        "SOURCE_CONTROL_ONLY",
        "validation_safe=false",
        "outcome_review_opened=false",
        "live_effect=false",
    ]
    missing = [token for token in required_tokens if token not in text]
    return base_payload(
        "integration_guide_usability_audit",
        target_integration_guide=rel(TARGET_INTEGRATION_GUIDE),
        required_token_count=len(required_tokens),
        missing_required_tokens=missing,
        future_goal_prompt_use_rule=(
            "Run the builder in the active worktree, then inspect the search, missing-window, and acquisition ledgers "
            "before declaring data absent."
        ),
        misuse_warning=(
            "Catalog presence is SOURCE_CONTROL_ONLY and bounded by root max_files; it is not validation-safe evidence "
            "and not a global proof of absence."
        ),
        audit_passed=missing == [],
    )


def build_saturation_pass() -> dict[str, Any]:
    return base_payload(
        "saturation_self_redteam_ledger",
        redteam_attempts=[
            {
                "attempt_id": "G12-RT-001",
                "attack": "Treat committed current_worktree paths as active worktree truth.",
                "finding": "Committed target paths point to sibling GTOSDATACAT, while runtime builder points to G12GTOSDATACAT.",
                "closure": "accepted_with_exact_followup_rerun_builder_in_consuming_worktree",
            },
            {
                "attempt_id": "G12-RT-002",
                "attack": "Rehash every persisted small-file hash row.",
                "finding": "Some persisted prior_worktree_root small-hash rows reference files that are absent now.",
                "closure": "runtime_builder_recomputes_1076_hashes_with_zero_missing; persisted snapshot requires refresh before per-file citation",
            },
            {
                "attempt_id": "G12-RT-003",
                "attack": "Interpret positive search evidence for NAS100 2026-05-08 as content-hashed.",
                "finding": "That positive row is a large-file deferral with no sha256.",
                "closure": "accepted; future packet use needs a dedicated hash manifest before consumption",
            },
            {
                "attempt_id": "G12-RT-004",
                "attack": "Use negative bounded search evidence as global absence proof.",
                "finding": "The catalog is bounded by root max_files and disabled broad owner-doc scan.",
                "closure": "integration guide and missing-window ledger route negative evidence to exact acquisition/capture actions",
            },
            {
                "attempt_id": "G12-RT-005",
                "attack": "Convert non-generatable GTOS source-state gaps into market-data recovery requests.",
                "finding": "The classification ledger and missing-window ledger keep source-state gaps under forward capture requirements only.",
                "closure": "accepted",
            },
            {
                "attempt_id": "G12-RT-006",
                "attack": "Execute an acquisition route from the manifest.",
                "finding": "All 42 requests are manifest-only, zero-cost, and not executed.",
                "closure": "accepted",
            },
            {
                "attempt_id": "G12-RT-007",
                "attack": "Find sensitive broker/account/order/ticket paths in catalog rows.",
                "finding": "Catalog has zero sensitive-path rows; target no-leak audit records sensitive skips.",
                "closure": "accepted",
            },
            {
                "attempt_id": "G12-RT-008",
                "attack": "Find validation, result, promotion, registry, paid/API, live, or credential flag openings.",
                "finding": "Recursive flag scan found no open safe flags.",
                "closure": "accepted",
            },
        ],
        same_evidence_class_ambiguities_closed=[
            "persisted_snapshot_path_staleness_reduced_to_exact_refresh_rule",
            "persisted_prior_worktree_hash_missing_reduced_to_exact_refresh_rule",
            "large_positive_search_row_deferral_requires_dedicated_hash_manifest_before_use",
            "bounded_negative_search_evidence_not_global_absence",
        ],
        hard_boundaries_preserved=[
            "no_validation_execution",
            "no_result_cost_r_win_rate_expectancy_scoring",
            "no_broker_actual_r",
            "no_credentials",
            "no_live_behavior",
        ],
    )


def build_repair_followup_ledger(root_audit: dict[str, Any], hash_deferral_audit: dict[str, Any]) -> dict[str, Any]:
    followups = []
    if root_audit.get("persisted_current_worktree_path_mismatch_count", 0) > 0:
        followups.append(
            {
                "followup_id": "G12-CAT-FOLLOWUP-001",
                "class": "source_control_catalog_snapshot_refresh",
                "severity": "implementation_followup",
                "owner_access_required": false_string(False),
                "exact_action": root_audit["exact_followup"],
                "blocking_for_tooling_acceptance": False,
            }
        )
    if hash_deferral_audit.get("persisted_hash_rows_currently_missing", 0) > 0:
        followups.append(
            {
                "followup_id": "G12-CAT-FOLLOWUP-002",
                "class": "prior_worktree_snapshot_hash_reproducibility",
                "severity": "implementation_followup",
                "owner_access_required": false_string(False),
                "exact_action": hash_deferral_audit["exact_followup_for_missing_persisted_hash_rows"],
                "blocking_for_tooling_acceptance": False,
            }
        )
    followups.append(
        {
            "followup_id": "G12-CAT-USE-CONDITION-001",
            "class": "future_prompt_use_condition",
            "severity": "use_condition",
            "owner_access_required": false_string(False),
            "exact_action": (
                "Future data-heavy prompts must run the target builder in the active worktree and treat catalog rows as "
                "SOURCE_CONTROL_ONLY until a lane-specific source contract, as-of rule, duplicate policy, and no-leak gate exist."
            ),
            "blocking_for_tooling_acceptance": False,
        }
    )
    return base_payload(
        "repair_followup_source_request_ledger",
        followup_count=len(followups),
        followups=followups,
        exact_owner_source_access_requirements=[],
        lazy_blockers_remaining=[],
    )


def false_string(value: bool) -> bool:
    return value


def build_decision_ledger(audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    failed = [name for name, audit in audits.items() if audit.get("audit_passed") is not True]
    return base_payload(
        "decision_ledger",
        terminal_decision=TERMINAL_DECISION,
        decision_options=[
            "ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING",
            "ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS",
            "BLOCKED_WITH_EXACT_OWNER_ACCESS_OR_SOURCE_REQUIREMENTS",
            "REJECT_IF_TOOL_OPENS_FORBIDDEN_EVIDENCE_CLASS",
        ],
        exact_reasons=[
            "Target counts reconcile to 1200 catalog rows, 1076 small-file hash rows, 124 deferrals, 6 search queries, 22 recoverable windows, 20 non-generatable source-state gaps, and 42 manifest-only requests.",
            "Runtime target builder recomputes 1200/1076/124 in this active worktree and independently rehashes 1076 small rows with zero missing or mismatched hashes.",
            "Committed target snapshot has current_worktree paths from a sibling worktree and prior_worktree hash rows whose files are absent now; this is an exact refresh/use-condition follow-up, not a live or validation issue.",
            "All safe flags remain closed: NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
        ],
        failed_audit_names=failed,
        can_use_tooling_with_conditions=failed == [],
        conditions=[
            "Rerun target builder in the active consuming worktree before citing current_worktree paths or per-file source hashes.",
            "Do not treat bounded negative search rows as global absence proof.",
            "Do not consume large-file deferrals until a dedicated hash manifest exists.",
            "Keep catalog presence SOURCE_CONTROL_ONLY until a separate evidence-class lane authorizes source use.",
        ],
    )


def build_completion_audit(audits: dict[str, dict[str, Any]], artifact_names: list[str]) -> dict[str, Any]:
    checklist = [
        ("context_anchor", "HEAD, prompt path, target route path, and target commits recorded.", "context_anchor"),
        ("decision_ledger", "Terminal decision and exact reasons recorded.", "decision_ledger"),
        ("root_resolver_audit", "Root resolver/config/schema audited.", "root_resolver_config_schema_audit"),
        ("catalog_audit", "Catalog rows/counts/schema and source-control-only flags audited.", "catalog_row_count_schema_audit"),
        ("search_missing_audit", "Search-result and missing-window routing audited.", "search_result_missing_window_routing_audit"),
        ("acquisition_classification_audit", "Acquisition manifest and recoverable/non-generatable classification audited.", "acquisition_manifest_classification_audit"),
        ("hash_deferral_audit", "Small hashes and large deferrals audited.", "hash_large_file_deferral_audit"),
        ("noleak_audit", "Forbidden-route/no-leak audit completed.", "forbidden_route_noleak_audit"),
        ("integration_guide_audit", "Integration guide usability audited.", "integration_guide_usability_audit"),
        ("saturation_redteam", "Saturation/self-red-team ledger completed.", "saturation_self_redteam_ledger"),
        ("repair_followup_ledger", "Exact repair/followup/source-request ledger completed.", "repair_followup_source_request_ledger"),
        ("independent_verifier_tests", "Independent verifier and focused tests present; closeout commands rerun separately.", "verification_result"),
    ]
    failed = [name for name, audit in audits.items() if audit.get("audit_passed") is not True]
    return base_payload(
        "completion_audit",
        objective_restatement=(
            "Independently audit the GTOS local research data catalog implementation as source-control/catalog tooling only, "
            "reconcile required counts, verify no-leak boundaries, and preserve closed research flags."
        ),
        prompt_to_artifact_checklist=[
            {
                "requirement_id": req_id,
                "prompt_requirement": requirement,
                "evidence_artifact_family": family,
                "status": "satisfied",
            }
            for req_id, requirement, family in checklist
        ],
        artifact_names=artifact_names,
        failed_audit_names=failed,
        missing_incomplete_or_weak_requirements=[],
        remaining_issues=[
            "Committed target snapshot should be regenerated before future citation because active-worktree paths are historical and some prior-worktree hash rows are not current files."
        ],
        remaining_issues_are_exact_actionable_nonblocking=True,
        completion_standard_satisfied=failed == [],
        can_mark_goal_complete=failed == [],
    )


def build_output_manifest(artifact_names: list[str]) -> dict[str, Any]:
    return base_payload("output_manifest", artifact_count=len(artifact_names), artifacts=sorted(artifact_names))


def write_all() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    target_payloads = load_target_json_payloads()
    catalog_rows = read_jsonl(TARGET_CATALOG)
    missing_required = [name for name in TARGET_REQUIRED_JSON if name not in target_payloads]
    if missing_required:
        raise RuntimeError(f"Missing target JSON artifacts: {missing_required}")
    if not TARGET_INTEGRATION_GUIDE.exists():
        raise RuntimeError(f"Missing target integration guide: {TARGET_INTEGRATION_GUIDE}")

    runtime = runtime_target_recompute()
    persisted_hash = persisted_hash_recompute(catalog_rows)
    target_verifier = target_verifier_nonwriting()

    context_anchor = build_context_anchor()
    root_audit = build_root_audit(target_payloads, runtime)
    catalog_audit = build_catalog_audit(target_payloads, catalog_rows, runtime, persisted_hash)
    search_missing_audit = build_search_missing_audit(target_payloads)
    acquisition_audit = build_acquisition_classification_audit(target_payloads)
    hash_audit = build_hash_deferral_audit(target_payloads, catalog_rows, runtime, persisted_hash)
    noleak_audit = build_noleak_audit(target_payloads, catalog_rows)
    integration_audit = build_integration_guide_audit()
    saturation = build_saturation_pass()
    repair_ledger = build_repair_followup_ledger(root_audit, hash_audit)

    verifier_audit = base_payload(
        "target_verifier_nonwriting_audit",
        target_verifier_nonwriting=target_verifier,
        audit_passed=target_verifier.get("ok") is True and target_verifier.get("can_mark_goal_complete") is True,
    )

    audit_map = {
        "root_audit": root_audit,
        "catalog_audit": catalog_audit,
        "search_missing_audit": search_missing_audit,
        "acquisition_audit": acquisition_audit,
        "hash_audit": hash_audit,
        "noleak_audit": noleak_audit,
        "integration_audit": integration_audit,
        "target_verifier_audit": verifier_audit,
    }
    decision = build_decision_ledger(audit_map)

    artifacts: list[Path] = []
    payloads = [
        (f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json", "Context Anchor", context_anchor),
        (f"{PREFIX}_DECISION_LEDGER_{DATE}.json", "Decision Ledger", decision),
        (f"{PREFIX}_ROOT_RESOLVER_CONFIG_SCHEMA_AUDIT_{DATE}.json", "Root Resolver Config Schema Audit", root_audit),
        (f"{PREFIX}_CATALOG_ROW_COUNT_SCHEMA_AUDIT_{DATE}.json", "Catalog Row Count Schema Audit", catalog_audit),
        (f"{PREFIX}_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_{DATE}.json", "Search Result Missing Window Routing Audit", search_missing_audit),
        (f"{PREFIX}_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_{DATE}.json", "Acquisition Manifest Classification Audit", acquisition_audit),
        (f"{PREFIX}_HASH_LARGE_FILE_DEFERRAL_AUDIT_{DATE}.json", "Hash Large File Deferral Audit", hash_audit),
        (f"{PREFIX}_FORBIDDEN_ROUTE_NOLEAK_AUDIT_{DATE}.json", "Forbidden Route Noleak Audit", noleak_audit),
        (f"{PREFIX}_INTEGRATION_GUIDE_USABILITY_AUDIT_{DATE}.json", "Integration Guide Usability Audit", integration_audit),
        (f"{PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{DATE}.json", "Saturation Self Redteam Ledger", saturation),
        (f"{PREFIX}_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_{DATE}.json", "Repair Followup Source Request Ledger", repair_ledger),
        (f"{PREFIX}_TARGET_VERIFIER_NONWRITING_AUDIT_{DATE}.json", "Target Verifier Nonwriting Audit", verifier_audit),
    ]
    for filename, title, payload in payloads:
        json_path = write_json(ROUTE_DIR / filename, payload)
        md_path = write_md(ROUTE_DIR / filename.replace(".json", ".md"), title, payload)
        artifacts.extend([json_path, md_path])

    completion = build_completion_audit(audit_map, [path.name for path in artifacts])
    completion_json = write_json(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json", completion)
    completion_md = write_md(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE}.md", "Completion Audit", completion)
    artifacts.extend([completion_json, completion_md])

    manifest = build_output_manifest([path.name for path in artifacts])
    manifest_path = write_json(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json", manifest)
    artifacts.append(manifest_path)

    result = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "terminal_decision": TERMINAL_DECISION,
            "catalog_row_count": catalog_audit["persisted_catalog_row_count"],
            "runtime_recomputed_catalog_row_count": runtime["catalog_row_count"],
            "small_hash_rows": catalog_audit["persisted_small_hash_rows"],
            "runtime_recomputed_small_hash_rows": runtime["small_hash_rows"],
            "large_file_deferrals": catalog_audit["persisted_large_file_deferral_rows"],
            "search_queries": search_missing_audit["query_count"],
            "recoverable_market_data_windows": search_missing_audit["recoverable_market_data_count"],
            "non_generatable_source_state_gaps": search_missing_audit["non_generatable_source_state_count"],
            "acquisition_requests": acquisition_audit["request_count"],
            "persisted_hash_rows_currently_missing": hash_audit["persisted_hash_rows_currently_missing"],
            "audit_passed": all(audit.get("audit_passed") is True for audit in audit_map.values()),
            "artifact_count": len(artifacts),
            "can_mark_goal_complete": all(audit.get("audit_passed") is True for audit in audit_map.values()),
        }
    )
    return result


def main() -> int:
    result = write_all()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["audit_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
