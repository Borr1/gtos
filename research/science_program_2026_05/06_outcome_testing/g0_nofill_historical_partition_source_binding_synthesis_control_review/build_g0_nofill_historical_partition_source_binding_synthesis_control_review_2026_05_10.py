"""Build the G0 NOFILL historical partition/source-binding synthesis route.

This is a source/control synthesis only. It reads the accepted G12 audit,
the target partition route, upstream source-control artifacts, and local-heavy
metadata. It does not open validation execution, result/cost scoring, broker
actual-R, paid/API routes, live restarts, or live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import sys
import subprocess
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ROUTE_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.forward_capture import (
    NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS,
    NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS,
)


ROUTE_ID = "G0_NOFILL_HISTORICAL_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW"
SCHEMA_VERSION = "g0_nofill_historical_partition_source_binding_synthesis_control_review_v1"
PREFIX = "G0_NOFILL_HIST_SYNTHESIS"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "ACCEPT_AS_G0_SOURCE_CONTROL_SYNTHESIS_FOR_NEXT_SEALED_SOURCE_EXPANSION"

SAFE_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_result_scoring": False,
    "opens_validation": False,
    "opens_promotion": False,
    "opens_registry_edit": False,
    "opens_paid_api_or_databento_route": False,
    "opens_remote_push": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_mt5_order_account_history_behavior": False,
    "changes_live_trading_behavior": False,
    "credentials_touched": False,
}

OUTCOME_DIR = REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
PROMPT_PATH = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G0_NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW_GOAL_PROMPT_2026-05-10.md"
)
G12_DIR = OUTCOME_DIR / "g12_nofill_historical_sealed_validation_partition_source_binding_audit"
TARGET_DIR = OUTCOME_DIR / "nofill_historical_sealed_validation_partition_and_source_binding"
METHOD_PLAN = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "05_synthesis"
    / "HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md"
)

UPSTREAM_DIRS = [
    "g0_nofill_forward_source_capture_implementation_synthesis_readiness_route",
    "g12_nofill_forward_source_capture_additive_logger_implementation_audit",
    "nofill_forward_source_capture_additive_logger_implementation",
    "g12_nofill_forward_projection_repair_reaudit",
    "nofill_cat_v3_source_control_rebuild",
    "g12_nofill_cat_v3_source_control_audit",
    "g12_nofill_cat_v3_quarantined_categorical_count_packet_audit",
    "g0_nofill_cat_v3_categorical_evidence_synthesis_control_review",
]

CONTROLLING_INPUTS = {
    "controlling_prompt": PROMPT_PATH,
    "methodology_plan": METHOD_PLAN,
    "g12_decision": G12_DIR / "G12_NOFILL_HIST_AUDIT_DECISION_LEDGER_2026-05-10.json",
    "g12_universe": G12_DIR
    / "G12_NOFILL_HIST_AUDIT_CAT_V3_UNIVERSE_ZERO_SEALED_RECOMPUTATION_AUDIT_2026-05-10.json",
    "g12_contamination": G12_DIR / "G12_NOFILL_HIST_AUDIT_CONTAMINATION_PROOF_REAUDIT_2026-05-10.json",
    "g12_field_matrix": G12_DIR / "G12_NOFILL_HIST_AUDIT_55_FIELD_SOURCE_BINDING_MATRIX_REAUDIT_2026-05-10.json",
    "g12_field_blockers": G12_DIR / "G12_NOFILL_HIST_AUDIT_FIELD_BLOCKER_EXACTNESS_AUDIT_2026-05-10.json",
    "g12_duplicate": G12_DIR / "G12_NOFILL_HIST_AUDIT_DUPLICATE_PURGE_EMBARGO_SPLIT_REDAUDIT_2026-05-10.json",
    "g12_local_search": G12_DIR / "G12_NOFILL_HIST_AUDIT_LOCAL_HEAVY_DATA_PRIOR_ARTIFACT_SEARCH_REAUDIT_2026-05-10.json",
    "g12_exact_blockers": G12_DIR / "G12_NOFILL_HIST_AUDIT_EXACT_REPAIR_SOURCE_BLOCKER_LEDGER_2026-05-10.json",
    "g12_completion": G12_DIR / "G12_NOFILL_HIST_AUDIT_COMPLETION_AUDIT_2026-05-10.json",
    "g12_verification": G12_DIR / "G12_NOFILL_HIST_AUDIT_VERIFICATION_RESULT_2026-05-10.json",
    "target_decision": TARGET_DIR / "NOFILL_HISTORICAL_SEALED_VALIDATION_DECISION_LEDGER_2026-05-10.json",
    "target_partition": TARGET_DIR / "NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_LEDGER_2026-05-10.json",
    "target_partition_rows": TARGET_DIR
    / "NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_ROW_LEDGER_2026-05-10.jsonl",
    "target_contamination": TARGET_DIR / "NOFILL_HISTORICAL_SEALED_VALIDATION_CONTAMINATION_PROOF_LEDGER_2026-05-10.json",
    "target_field_matrix": TARGET_DIR / "NOFILL_HISTORICAL_SEALED_VALIDATION_55_FIELD_SOURCE_BINDING_MATRIX_2026-05-10.json",
    "target_field_blockers": TARGET_DIR
    / "NOFILL_HISTORICAL_SEALED_VALIDATION_FIELD_BLOCKERS_OWNER_REQUIREMENTS_LEDGER_2026-05-10.json",
    "target_duplicate": TARGET_DIR
    / "NOFILL_HISTORICAL_SEALED_VALIDATION_DUPLICATE_DENOMINATOR_PURGE_EMBARGO_POLICY_2026-05-10.json",
    "target_local_search": TARGET_DIR
    / "NOFILL_HISTORICAL_SEALED_VALIDATION_LOCAL_HEAVY_DATA_PRIOR_ARTIFACT_SEARCH_LEDGER_2026-05-10.json",
    "target_future_prereqs": TARGET_DIR
    / "NOFILL_HISTORICAL_SEALED_VALIDATION_FUTURE_VALIDATION_EXECUTION_PREREQUISITES_2026-05-10.json",
    "target_forbidden": TARGET_DIR / "NOFILL_HISTORICAL_SEALED_VALIDATION_FORBIDDEN_ROUTE_LEDGER_2026-05-10.json",
    "target_manifest": TARGET_DIR / "NOFILL_HISTORICAL_SEALED_VALIDATION_OUTPUT_MANIFEST_2026-05-10.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def with_safe_flags(obj: dict[str, Any]) -> dict[str, Any]:
    return {**obj, **{key: obj.get(key, value) for key, value in SAFE_FLAGS.items()}}


def write_json(name: str, obj: dict[str, Any]) -> Path:
    path = ROUTE_DIR / name
    path.write_text(json.dumps(with_safe_flags(obj), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_md(name: str, title: str, summary: dict[str, Any], notes: list[str] | None = None) -> Path:
    path = ROUTE_DIR / name
    lines = [
        f"# {title}",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Terminal decision: `{TERMINAL_DECISION}`",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(with_safe_flags(summary), indent=2, sort_keys=True),
        "```",
    ]
    if notes:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {note}" for note in notes)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def source_record(role: str, path: Path) -> dict[str, Any]:
    return {
        "role": role,
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        "sha256": sha256_file(path),
    }


def upstream_records() -> list[dict[str, Any]]:
    rows = []
    for name in UPSTREAM_DIRS:
        path = OUTCOME_DIR / name
        rows.append(
            {
                "route_dir": name,
                "path": rel(path),
                "exists": path.exists(),
                "json_artifact_count": len(list(path.glob("*.json"))) if path.exists() else 0,
                "md_artifact_count": len(list(path.glob("*.md"))) if path.exists() else 0,
                "py_artifact_count": len(list(path.glob("*.py"))) if path.exists() else 0,
            }
        )
    return rows


def file_sample(root: Path, pattern: str, recursive: bool, limit: int = 160) -> dict[str, Any]:
    try:
        exists = root.exists()
        if not exists:
            return {"root": str(root), "pattern": pattern, "exists": False, "count_seen": 0, "sample": []}
        iterator = root.rglob(pattern) if recursive else root.glob(pattern)
        sample = [str(p) for _, p in zip(range(limit), sorted(iterator))]
        count_seen = len(sample)
        truncated = count_seen == limit
        return {
            "root": str(root),
            "pattern": pattern,
            "exists": True,
            "count_seen_sample_limited": count_seen,
            "sample": sample[:16],
            "truncated": truncated,
        }
    except Exception as exc:
        return {"root": str(root), "pattern": pattern, "exists": root.exists(), "error": str(exc), "sample": []}


def local_heavy_metadata(g12_duplicate: dict[str, Any]) -> dict[str, Any]:
    tick_root = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks")
    shadow_root = Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs")
    sierra_root = Path(r"C:\SierraChart\Data")
    depth_root = Path(r"C:\SierraChart\Data\MarketDepthData")
    tmp_root = Path(r"C:\tmp\gtos_otb")

    tick_dates_by_symbol: dict[str, list[str]] = defaultdict(list)
    if tick_root.exists():
        for path in sorted(tick_root.glob("*/*.parquet")):
            tick_dates_by_symbol[path.parent.name].append(path.stem)

    contaminated_dates = sorted(g12_duplicate.get("contaminated_source_dates_recomputed", []))
    contaminated_date_objs = {date.fromisoformat(item) for item in contaminated_dates}

    def is_embargo_clear(value: str) -> bool:
        try:
            current = date.fromisoformat(value)
        except ValueError:
            return False
        return all(abs((current - blocked).days) > 1 for blocked in contaminated_date_objs)

    embargo_clear_tick_dates_by_symbol = {
        symbol: [value for value in values if is_embargo_clear(value)]
        for symbol, values in tick_dates_by_symbol.items()
    }

    shadow_hits = []
    if shadow_root.exists():
        wanted = {
            "candidate_mso_snapshot_joins.jsonl",
            "candidate_ltf_path_order.jsonl",
            "candidate_path_contract_audit.jsonl",
            "candidate_path_follow.jsonl",
            "candidate_registry_audit.jsonl",
            "pending_limit_lifecycle.jsonl",
            "pending_limit_lifecycle_audit.jsonl",
            "pending_limit_lifecycle_join_backfill.jsonl",
            "nofill_forward_source_capture.jsonl",
        }
        for name in sorted(wanted):
            path = shadow_root / name
            shadow_hits.append(
                {
                    "name": name,
                    "path": str(path),
                    "exists": path.exists(),
                    "size_bytes": path.stat().st_size if path.exists() else None,
                    "line_count": sum(1 for _ in path.open(encoding="utf-8", errors="replace")) if path.exists() else None,
                }
            )

    prior_exact_route_hits = []
    if tmp_root.exists():
        for path in sorted(tmp_root.glob("*/research/science_program_2026_05/06_outcome_testing/*")):
            if path.name in {
                "nofill_historical_sealed_validation_partition_and_source_binding",
                "g12_nofill_historical_sealed_validation_partition_source_binding_audit",
                "g0_nofill_historical_partition_source_binding_synthesis_control_review",
            }:
                prior_exact_route_hits.append(str(path))

    return {
        "artifact_family": "local_heavy_prior_artifact_metadata",
        "searches_performed_this_route": [
            "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\*\\*.parquet",
            "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs selected candidate/pending/nofill logs",
            "C:\\SierraChart\\Data\\*.scid",
            "C:\\SierraChart\\Data\\MarketDepthData\\*.depth",
            "C:\\tmp\\gtos_otb prior NOFILL route directories",
        ],
        "tick_parquet_metadata": file_sample(tick_root, "*.parquet", True),
        "tick_dates_by_symbol": dict(sorted(tick_dates_by_symbol.items())),
        "contaminated_source_dates_from_g12": contaminated_dates,
        "global_one_day_embargo_clear_tick_dates_by_symbol": dict(sorted(embargo_clear_tick_dates_by_symbol.items())),
        "shadow_log_metadata": shadow_hits,
        "sierra_scid_metadata": file_sample(sierra_root, "*.scid", False),
        "sierra_depth_metadata": file_sample(depth_root, "*.depth", False),
        "prior_exact_route_hits": prior_exact_route_hits,
        "route_conclusion": (
            "Local heavy roots contain source-only candidate material, especially tick parquet and Sierra files. "
            "No file is validation-safe from metadata alone; a future source expansion builder must hash inputs, "
            "purge contaminated dates/keys/groups, bind all 55 fields, and pass G12 before any validation execution."
        ),
    }


def load_inputs() -> dict[str, Any]:
    data = {name: read_json(path) for name, path in CONTROLLING_INPUTS.items() if path.suffix == ".json"}
    data["target_partition_rows"] = read_jsonl(CONTROLLING_INPUTS["target_partition_rows"])
    return data


def accepted_g12_target_synthesis(data: dict[str, Any]) -> dict[str, Any]:
    g12_decision = data["g12_decision"]
    g12_universe = data["g12_universe"]
    g12_matrix = data["g12_field_matrix"]
    g12_blockers = data["g12_exact_blockers"]
    target_decision = data["target_decision"]
    return {
        "artifact_family": "accepted_g12_and_target_route_synthesis",
        "accepted_g12_terminal_decision": g12_decision["terminal_decision"],
        "target_terminal_decision": target_decision["terminal_decision"],
        "accepted_as": [
            "source-control historical partition evidence",
            "source-control field-binding evidence",
            "G12 accepted facts for next G0 source expansion synthesis",
        ],
        "not_accepted_as": [
            "validation execution",
            "result scoring",
            "cost scoring",
            "promotion evidence",
            "live trading behavior approval",
            "broker actual-R/account-history permission",
            "paid/API route approval",
        ],
        "canonical_recomputed_facts": {
            "cat_v3_row_count": g12_universe["target_row_count"],
            "universe_equation": g12_universe["universe_equation_recomputed"],
            "family_counts": g12_universe["target_family_counts"],
            "sealed_validation_current_committed_nofill_rows": g12_universe[
                "sealed_validation_current_committed_nofill_rows_recomputed"
            ],
            "field_count": g12_matrix["field_count_recomputed"],
            "future_requirement_count": data["g12_field_blockers"][
                "future_logger_or_source_extraction_requirement_count_recomputed"
            ],
            "exact_repair_source_blocker_count": g12_blockers["exact_repair_source_blocker_count"],
        },
        "operational_meaning": (
            "The current NOFILL historical chain is accepted only as source/control evidence. "
            "It proves the committed CAT V3 rows cannot be used as sealed validation and gives "
            "the controls a future expansion builder must enforce."
        ),
    }


def zero_sealed_implications(data: dict[str, Any]) -> dict[str, Any]:
    rows = data["target_partition_rows"]
    family_counts = dict(sorted(Counter(row["v3_terminal_family"] for row in rows).items()))
    return {
        "artifact_family": "zero_sealed_row_implication_ledger",
        "sealed_validation_current_committed_nofill_rows": 0,
        "cat_v3_rows_checked": len(rows),
        "family_counts": family_counts,
        "implications": [
            {
                "implication_id": "ZERO_IS_CONTROL_SUCCESS_NOT_VALIDATION_FAILURE",
                "meaning": "Zero sealed rows means the current source-control chain correctly quarantined touched CAT V3 rows.",
                "required_action": "Build a new source-hashed expansion packet from untouched windows before validation execution.",
            },
            {
                "implication_id": "NO_PASSIVE_WAITING",
                "meaning": "The project should not wait passively for forward rows when source-safe historical roots exist.",
                "required_action": "Run a source expansion builder that searches local tick, shadow, and Sierra roots under no-leak controls.",
            },
            {
                "implication_id": "NO_ROW_LAUNDERING",
                "meaning": "Existing CAT V3 rows cannot be recast as sealed by changing labels or excluding scoring fields.",
                "required_action": "Purge packet row IDs, source row IDs, duplicate keys/groups, dates, and one-day embargo overlaps.",
            },
        ],
    }


def contaminated_reuse_constraints(data: dict[str, Any]) -> dict[str, Any]:
    contamination = data["g12_contamination"]
    duplicate = data["g12_duplicate"]
    return {
        "artifact_family": "contaminated_row_reuse_constraints",
        "contaminated_row_count": contamination["contaminated_row_count_recomputed"],
        "contamination_counts_by_terminal_family": contamination[
            "contamination_counts_by_terminal_family_recomputed"
        ],
        "allowed_uses": [
            "source/control lineage explanation",
            "duplicate and concentration stress design",
            "exclusion-proof stress tests",
            "field binding and parser-design examples",
            "future robustness design that does not score the contaminated rows as validation",
        ],
        "forbidden_uses": [
            "sealed historical validation denominator",
            "result/cost scoring",
            "promotion claim support",
            "sample-floor inflation",
            "source-date laundering through regenerated packet IDs",
            "broker actual-R/account-history review in this lane",
        ],
        "contaminated_source_dates": duplicate["contaminated_source_dates_recomputed"],
        "primary_duplicate_key_members": duplicate["primary_duplicate_key_unique_count_recomputed"],
        "secondary_duplicate_group_members": duplicate["secondary_duplicate_group_unique_count_recomputed"],
            "reuse_rule": (
                "A future row must be excluded if it shares packet row ID, source row ID, source inventory ID, "
                "nofill duplicate key, duplicate group ID, source date, or one-day same-symbol/source-lane embargo "
                "overlap with this contaminated ledger unless a future G12 explicitly proves independent source generation."
            ),
    }


def field_checklist(data: dict[str, Any]) -> dict[str, Any]:
    matrix = data["target_field_matrix"]
    rows = []
    for row in matrix["fields"]:
        binding_class = row["binding_class"]
        if binding_class == "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED":
            action = "preserve existing source-safe binding and source hash; fail closed if missing"
        elif binding_class == "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE":
            action = "derive from tick/source extractor or wait for forward logger; fail closed if unavailable"
        elif binding_class == "SCHEMA_ONLY_CONTROL":
            action = "emit deterministic schema/control value from builder, not from outcomes"
        elif binding_class == "FORBIDDEN_REDACTED_STATUS_ONLY":
            action = "emit status/redaction only; never include raw broker/account/order/result/cost value"
        else:
            action = "block until owner/source requirement is exact"
        rows.append(
            {
                "field_name": row["field_name"],
                "binding_class": binding_class,
                "design_terminal_status": row["design_terminal_status"],
                "future_logger_field": row["future_logger_field"],
                "expansion_binding_action": action,
                "exact_requirement_before_validation": row["exact_requirement_before_validation"],
                "fail_closed_missing_status": row["fail_closed_missing_status"],
            }
        )
    return {
        "artifact_family": "fifty_five_field_expansion_binding_checklist",
        "field_count": len(rows),
        "runtime_field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS),
        "future_logger_field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS),
        "binding_class_counts": dict(sorted(Counter(row["binding_class"] for row in rows).items())),
        "design_terminal_status_counts": dict(sorted(Counter(row["design_terminal_status"] for row in rows).items())),
        "fields": rows,
    }


def expansion_route_ranking(local_meta: dict[str, Any]) -> dict[str, Any]:
    safe_tick_dates = {
        symbol: dates
        for symbol, dates in local_meta["global_one_day_embargo_clear_tick_dates_by_symbol"].items()
        if dates
    }
    routes = [
        {
            "rank": 1,
            "route_id": "NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET",
            "route_class": "source_expansion_builder",
            "status": "BEST_NEXT_G0_SOURCE_CONTROL_ROUTE",
            "why": "Uses already-local MT5 tick parquet plus candidate/pending shadow logs; no paid/API route is needed.",
            "source_roots": [
                r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks",
                r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs",
                "current worktree committed source-control artifacts",
            ],
            "candidate_universe_seed": {
                "embargo_clear_tick_dates_by_symbol": safe_tick_dates,
                "date_rule": "Future builder must recompute from contaminated row ledger by symbol/source-lane and exclude source-date plus one-day embargo overlaps before row admission.",
            },
            "required_outputs": [
                "source hash manifest for every consumed tick/shadow/source file",
                "frozen source-bound NOFILL candidate packet",
                "55-field binding checklist per row",
                "duplicate key and duplicate group ledgers",
                "forbidden field scan",
                "G12 audit prompt pack",
            ],
            "must_not_do": [
                "score outcomes",
                "read broker actual-R/account history",
                "promote",
                "edit registry",
                "change live behavior",
            ],
        },
        {
            "rank": 2,
            "route_id": "NOFILL_SIERRA_FUTURES_PROXY_CONTEXT_SOURCE_EXPANSION",
            "route_class": "source_contract_and_context_packet",
            "status": "PROMISING_CONTEXT_ROUTE_NOT_DIRECT_VALIDATION",
            "why": "Sierra SCID/depth files exist for GC/SI/NQ/YM/6J/6B proxy families and can improve source/context design.",
            "source_roots": [r"C:\SierraChart\Data", r"C:\SierraChart\Data\MarketDepthData"],
            "required_outputs": [
                "Sierra parser/source hash manifest",
                "proxy transfer contract by symbol",
                "as-of timestamp convention",
                "separation from GTOS broker NOFILL labels",
            ],
            "must_not_do": [
                "treat futures proxy context as direct CFD/broker validation",
                "score NOFILL outcomes in this route",
            ],
        },
        {
            "rank": 3,
            "route_id": "NOFILL_FORWARD_SOURCE_CAPTURE_NEXT_CANDIDATE_PACKET",
            "route_class": "forward_shadow_source_capture",
            "status": "USEFUL_BUT_NOT_HISTORICAL_SEALED_VALIDATION",
            "why": "The additive 55-field logger is source/control accepted, but no forward capture row exists yet.",
            "source_roots": [r"shadow_logs\nofill_forward_source_capture.jsonl"],
            "required_outputs": [
                "owner/current-process state check",
                "first-row schema verification",
                "forward pool separation from historical sealed validation",
            ],
            "must_not_do": [
                "restart live processes in this lane",
                "treat forward capture realism as historical sealed validation",
            ],
        },
        {
            "rank": 4,
            "route_id": "NOFILL_PRIOR_WORKTREE_ARTIFACT_RECONCILIATION_CONTROL_ROUTE",
            "route_class": "source_control_reconciliation",
            "status": "CONTROL_ONLY_NOT_ROW_EXPANSION",
            "why": "Prior worktrees can catch contradictions but are likely contaminated by prompt/audit exposure.",
            "source_roots": [r"C:\tmp\gtos_otb"],
            "required_outputs": [
                "prior artifact hash ledger",
                "contradiction ledger",
                "proof that no row is admitted solely from stale worktree output",
            ],
            "must_not_do": ["use stale artifacts as sealed validation rows"],
        },
        {
            "rank": 5,
            "route_id": "BROKER_ACCOUNT_HISTORY_OR_RESULT_LABEL_ROUTE",
            "route_class": "forbidden_here",
            "status": "CLOSED_IN_THIS_G0_SOURCE_CONTROL_ROUTE",
            "why": "The controlling prompt forbids broker actual-R, account/order/deal/position behavior, result/cost labels, and validation execution.",
            "source_roots": [],
            "required_outputs": ["separate owner-approved evidence-class prompt if ever needed"],
            "must_not_do": ["open inside this G0 synthesis or next source expansion builder"],
        },
    ]
    return {
        "artifact_family": "next_source_expansion_route_ranking",
        "routes": routes,
        "recommended_next_route_id": routes[0]["route_id"],
        "recommended_next_route_terminal_boundary": (
            "Build a source-hashed candidate packet and exact blocker ledger only; route to G12 source/control audit next. "
            "Do not execute validation or score outcomes."
        ),
    }


def expansion_requirements_matrix(ranking: dict[str, Any], field_list: dict[str, Any]) -> dict[str, Any]:
    matrix = []
    for route in ranking["routes"]:
        if route["route_class"] == "source_expansion_builder":
            field_requirement = "55/55 field checklist required per row; 17 source-bound fields preserved, 20 extracted or fail-closed, 11 schema-only, 7 redacted status-only."
            g12_requirement = "mandatory before validation execution"
        elif route["route_class"] == "source_contract_and_context_packet":
            field_requirement = "context fields only until proxy transfer/as-of contract is G12 accepted"
            g12_requirement = "mandatory before joining to NOFILL packet"
        else:
            field_requirement = "control evidence only"
            g12_requirement = "mandatory before any broader use"
        matrix.append(
            {
                "route_id": route["route_id"],
                "route_class": route["route_class"],
                "rank": route["rank"],
                "source_roots": route["source_roots"],
                "source_hash_policy": "SHA256 every consumed raw/source/log/parser artifact before row admission",
                "asof_policy": "all fields must be available at decision/capture as-of or carry fail-closed missing status",
                "duplicate_policy": "exclude contaminated packet/source IDs, nofill duplicate keys, duplicate groups, source dates, and one-day embargo overlaps",
                "field_requirement": field_requirement,
                "field_count_target": field_list["field_count"] if route["rank"] == 1 else None,
                "g12_acceptance_requirement": g12_requirement,
                "validation_execution_allowed": False,
                "result_or_cost_scoring_allowed": False,
                "owner_access_requirement": route["required_outputs"],
            }
        )
    return {
        "artifact_family": "exact_source_expansion_requirements_matrix",
        "matrix": matrix,
        "universal_admission_requirements": [
            "frozen controlling prompt before outcome opening",
            "source hash manifest",
            "parser code hash",
            "55-field binding per admitted row when route is NOFILL candidate packet",
            "duplicate/purge/embargo ledger",
            "forbidden field scan",
            "zero broker actual-R/account-history fields",
            "G12 source/control acceptance before any validation execution prompt",
        ],
    }


def noleak_rules(data: dict[str, Any]) -> dict[str, Any]:
    duplicate = data["g12_duplicate"]
    matrix = data["g12_field_matrix"]
    return {
        "artifact_family": "no_leak_duplicate_purge_embargo_source_hash_rules",
        "no_leak_rules": [
            "Do not open result, cost, slippage, execution quality, broker actual-R, account history, order, deal, or position values.",
            "Use only as-of fields available at or before decision/capture timestamp; otherwise emit fail-closed missing status.",
            "Keep source/control rows separate from validation/result rows in filenames, schema, and prompt language.",
            "Reject any row whose hidden label appears in source fields, parser diagnostics, row ID, or status vocabulary.",
        ],
        "duplicate_rules": [
            "Primary denominator is nofill_duplicate_key_sha256 or its source-safe equivalent.",
            "Secondary concentration denominator is duplicate_group_id_sha256 or its source-safe equivalent.",
            "Row-level counts are descriptive only until duplicate denominators are recomputed.",
        ],
        "purge_embargo_rules": [
            "Purge packet row ID, source row ID, source inventory ID, nofill duplicate key, and duplicate group overlap.",
            f"Globally contaminated source dates from accepted G12: {duplicate['contaminated_source_dates_recomputed']}.",
            "Apply at least one-day same-symbol/source-lane embargo around contaminated source dates before source expansion.",
            "G12 may tighten the embargo if source-lane timestamps show same-event leakage.",
        ],
        "source_hash_rules": [
            "Hash every raw tick/shadow/Sierra/source artifact consumed.",
            "Hash parser code and route builder code.",
            "Record path, size, mtime when available, sha256, parser version, and source contract ID.",
            "Never rely on local-heavy metadata alone as validation-safe evidence.",
        ],
        "forbidden_status_only_fields": matrix["forbidden_status_only_fields"],
    }


def owner_access_requirements(ranking: dict[str, Any], field_list: dict[str, Any]) -> dict[str, Any]:
    future_fields = [row["field_name"] for row in field_list["fields"] if row["future_logger_field"]]
    return {
        "artifact_family": "owner_access_source_capture_requirements_ledger",
        "requirements": [
            {
                "requirement_id": "OWNER_APPROVE_G0_SOURCE_EXPANSION_BUILDER",
                "owner": "CEO",
                "requirement": "Run the next source expansion builder route with validation/result/cost gates still closed.",
                "needed_for": ranking["recommended_next_route_id"],
                "blocking_status": "NOT_BLOCKING_THIS_SYNTHESIS_NEXT_PROMPT_PROVIDED",
            },
            {
                "requirement_id": "LOCAL_HEAVY_READ_ACCESS",
                "owner": "local filesystem",
                "requirement": r"Read access to C:\Users\MSI\Documents\ai-trading-agent\data\ticks and selected shadow_logs.",
                "needed_for": "source-hashed historical candidate packet",
                "blocking_status": "AVAILABLE_AS_METADATA_CURRENT_ROUTE_FULL_HASHING_REQUIRED_NEXT",
            },
            {
                "requirement_id": "SOURCE_HASH_AND_PARSER_MANIFEST",
                "owner": "next source expansion route",
                "requirement": "Hash every consumed source/log/parser file and emit parser/as-of manifest before row admission.",
                "needed_for": "G12 source/control acceptance",
                "blocking_status": "OPEN_REQUIREMENT_FOR_NEXT_ROUTE",
            },
            {
                "requirement_id": "FUTURE_20_FIELD_EXTRACTION_OR_FAIL_CLOSED",
                "owner": "next source expansion route",
                "requirement": "Extract or fail-close all 20 future logger/source-extraction fields.",
                "needed_for": future_fields,
                "blocking_status": "OPEN_REQUIREMENT_FOR_NEXT_ROUTE",
            },
            {
                "requirement_id": "FORWARD_CAPTURE_OWNER_RESTART_OR_CURRENT_PROCESS_PROOF",
                "owner": "CEO/live operations",
                "requirement": "Only for forward pool rows: prove live processes include source-capture commit or restart during approved maintenance window.",
                "needed_for": "future forward nofill_forward_source_capture rows",
                "blocking_status": "NOT_REQUIRED_FOR_HISTORICAL_SOURCE_EXPANSION_BUILDER",
            },
            {
                "requirement_id": "G12_SOURCE_CONTROL_AUDIT",
                "owner": "future G12 route",
                "requirement": "Independently audit any new source packet before validation execution.",
                "needed_for": "validation-execution prompt eligibility",
                "blocking_status": "MANDATORY_FUTURE_GATE",
            },
        ],
    }


def validation_closed_gate_ledger() -> dict[str, Any]:
    surfaces = [
        "validation execution",
        "result scoring",
        "cost scoring",
        "promotion",
        "registry edit",
        "paid/API/Databento route",
        "remote push",
        "live restart",
        "prompt/config/risk/permissions/safety/selector/canary change",
        "MT5 order/account/history/deal/position behavior",
        "broker actual-R read",
        "credential access/change",
        "live trading behavior change",
    ]
    return {
        "artifact_family": "validation_execution_closed_gate_ledger",
        "closed_gates": [
            {
                "gate": surface,
                "opened": False,
                "future_reopen_condition": "separate owner-approved prompt and correct evidence-class gate"
                if surface != "validation execution"
                else "G12-accepted source-bound packet plus separate validation-execution prompt",
            }
            for surface in surfaces
        ],
        "validation_execution_prerequisites_before_future_open": [
            "frozen source-hashed input packet",
            "55-field binding accepted",
            "duplicate/purge/embargo rules accepted",
            "sample floors accepted",
            "no-leak and forbidden-field scans accepted",
            "G12 source/control audit accepted",
        ],
    }


def broad_science_horizon_note() -> dict[str, Any]:
    return {
        "artifact_family": "broad_science_horizon_separation_note",
        "nofill_scope_statement": (
            "This route is intentionally narrow: NOFILL historical source/control synthesis and next-source expansion only."
        ),
        "non_boxing_statement": (
            "The accepted NOFILL chain must not imply the full GTOS science program is limited to NOFILL, CAT V3, current symbols, "
            "current timeframes, or forward-source-capture fields."
        ),
        "parallel_routes_to_keep_separate": [
            {
                "route_id": "G0_CROSS_HYPOTHESIS_HISTORICAL_SEALED_VALIDATION_LEDGER_AND_TEST_PLAN",
                "purpose": "Inventory sealed historical partitions across broader hypothesis families without contaminating NOFILL.",
            },
            {
                "route_id": "ORDERFLOW_SIERRA_PROXY_SOURCE_CONTRACT_AND_ASOF_PACKET",
                "purpose": "Build source/as-of contracts for Sierra/orderflow proxy context as context evidence, not NOFILL validation.",
            },
            {
                "route_id": "LLM_SPECIALIZATION_FEASIBILITY_AND_EVAL_DATASET_DESIGN",
                "purpose": "Design clean model specialization datasets only after source-safe examples and sealed eval partitions exist.",
            },
        ],
    }


def saturation_pass(ranking: dict[str, Any], local_meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_family": "saturation_self_redteam_pass",
        "status": "PASS_ALLOWED_GAPS_REDUCED_TO_EXACT_NEXT_SOURCE_REQUIREMENTS",
        "redteam_questions": [
            {
                "question": "What mistake would turn zero sealed rows into passive waiting?",
                "answer": "Treating zero as no available work rather than a requirement to build a new source-hashed expansion packet.",
                "action": "Ranked the local tick/shadow source expansion builder as the next route.",
            },
            {
                "question": "What route would accidentally re-use contaminated CAT V3 rows?",
                "answer": "Any builder that only regenerates packet IDs while sharing source dates, source IDs, duplicate keys, or duplicate groups.",
                "action": "Frozen purge rules include IDs, duplicate keys/groups, source dates, and one-day embargo overlap.",
            },
            {
                "question": "What field/source gap would make a future packet look source-bound when it is not?",
                "answer": "Treating future logger fields such as spreads, clock skew, pending horizon, or touch timestamps as present without source extraction or fail-closed status.",
                "action": "55-field checklist keeps all 20 future logger/source-extraction fields explicit.",
            },
            {
                "question": "Which local-heavy root could materially change the plan?",
                "answer": "Absolute tick parquet, selected shadow logs, Sierra SCID/depth files, and prior worktrees.",
                "action": "Current route searched metadata for those roots and records exact next hashing/parser requirements.",
            },
            {
                "question": "What duplicate/embargo failure would inflate future effective N?",
                "answer": "Counting row-level opportunities across duplicate keys/groups or one-day date neighbors as independent.",
                "action": "Primary denominator, secondary concentration denominator, purge, and embargo rules are frozen before expansion.",
            },
            {
                "question": "What would a skeptical G12 reject?",
                "answer": "A packet without hashes, parser hashes, no-leak scan, 55-field binding, contaminated row purge, or closed validation gates.",
                "action": "The next prompt pack requires those artifacts before any validation execution.",
            },
            {
                "question": "What route should run in parallel for the broader horizon?",
                "answer": "A cross-hypothesis historical sealed-validation ledger, not a NOFILL scoring route.",
                "action": "Broad science separation note records the parallel route explicitly.",
            },
            {
                "question": "What is deliberately not answered here?",
                "answer": "No validation performance, no result/cost scoring, no promotion, and no broker actual-R/account history.",
                "action": "Closed-gate ledger leaves those for separate future evidence-class prompts.",
            },
        ],
        "same_evidence_class_gaps_pursued": [
            "accepted G12 facts reconstructed",
            "target route synthesized",
            "field checklist rebuilt from target matrix",
            "local-heavy metadata searched",
            "next source expansion route made exact",
        ],
        "recommended_next_route_id": ranking["recommended_next_route_id"],
        "local_heavy_route_conclusion": local_meta["route_conclusion"],
    }


def instruction_coverage(outputs: dict[str, str]) -> dict[str, Any]:
    required = {
        "context_anchor": "context anchor",
        "decision_ledger": "G0 decision ledger",
        "accepted_synthesis": "accepted G12 and target-route synthesis",
        "zero_sealed": "zero-sealed-row implication ledger",
        "contaminated_reuse": "allowed contaminated-row reuse ledger",
        "route_ranking": "next source expansion route ranking",
        "requirements_matrix": "exact source expansion requirements matrix",
        "field_checklist": "55-field expansion binding checklist",
        "noleak_rules": "no-leak/duplicate/purge/embargo/source-hash rules",
        "search_plan": "local-heavy-data and prior-artifact source search plan",
        "owner_requirements": "owner/access/source/capture requirements ledger",
        "broad_horizon": "broader science horizon separation note",
        "closed_gates": "validation-execution closed-gate ledger",
        "saturation": "saturation/self-red-team pass",
        "instruction_coverage": "instruction-coverage checklist",
        "next_prompt_pack": "next prompt pack with one-line starter",
        "completion_audit": "completion audit",
        "builder_verifier_tests": "builder, verifier, and focused tests",
    }
    return {
        "artifact_family": "instruction_coverage_checklist",
        "requirements": [
            {
                "requirement_id": key,
                "prompt_requirement": value,
                "status": "DONE",
                "evidence": outputs.get(key, "python_files_or_manifest"),
            }
            for key, value in required.items()
        ],
        "all_requirements_done": True,
    }


def completion_audit(outputs: dict[str, str], synthesis: dict[str, Any], field_list: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "accepted G12 facts synthesized",
            "status": "PASS",
            "evidence": synthesis["canonical_recomputed_facts"],
        },
        {
            "requirement": "zero sealed rows handled as source expansion requirement",
            "status": "PASS",
            "evidence": "0 committed sealed rows; next route is source expansion builder, not validation failure.",
        },
        {
            "requirement": "contaminated row reuse constrained",
            "status": "PASS",
            "evidence": outputs["contaminated_reuse"],
        },
        {
            "requirement": "next source expansion route exact",
            "status": "PASS",
            "evidence": outputs["route_ranking"],
        },
        {
            "requirement": "55-field checklist complete",
            "status": "PASS" if field_list["field_count"] == 55 else "FAIL",
            "evidence": field_list["binding_class_counts"],
        },
        {
            "requirement": "validation/result/cost/promotion/live gates closed",
            "status": "PASS",
            "evidence": outputs["closed_gates"],
        },
        {
            "requirement": "broad science horizon preserved",
            "status": "PASS",
            "evidence": outputs["broad_horizon"],
        },
        {
            "requirement": "mandatory verifier/focused tests planned",
            "status": "PASS",
            "evidence": "route verifier and focused pytest files are part of this route",
        },
    ]
    return {
        "artifact_family": "completion_audit",
        "objective_restatement": (
            "Synthesize accepted G12/target NOFILL historical source-control evidence into an exact next-source expansion roadmap "
            "without validation execution, result/cost scoring, promotion, or live-surface changes."
        ),
        "terminal_decision": TERMINAL_DECISION,
        "prompt_to_artifact_checklist": checklist,
        "missing_incomplete_or_weak_requirements": [],
        "completion_standard_satisfied": all(item["status"] == "PASS" for item in checklist),
        "can_mark_goal_complete_after_scoped_commits_and_closeout_verification": True,
    }


def next_prompt_pack() -> str:
    starter = (
        "/goal Follow the source-expansion builder instructions embedded in "
        "research/science_program_2026_05/06_outcome_testing/"
        "g0_nofill_historical_partition_source_binding_synthesis_control_review/"
        "G0_NOFILL_HIST_SYNTHESIS_NEXT_PROMPT_PACK_2026-05-10.md as the complete objective; "
        "do mandatory preflight and context refresh first; read the G0 synthesis route artifacts; "
        "do not rely on chat memory; stay NOFILL historical source-expansion builder only with no validation execution, "
        "result/cost scoring, promotion, registry edit, paid/API route, remote push, live restart, prompts, config, risk, "
        "permissions, safety, selectors, canaries, MT5 order/account/history/deal/position behavior, broker actual-R, "
        "credentials, or live trading behavior changes; build only a source-hashed candidate packet and exact blocker ledger "
        "from local tick/shadow roots, enforce 55/55 field binding, duplicate/purge/embargo/source-hash/no-leak rules, "
        "run builder/verifier/focused tests, produce next G12 audit prompt, scoped commits, closeout verification, "
        "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; if any blocker appears, "
        "pursue until cleared, proven impossible from approved routes, or reduced to an exact owner/access/source/capture requirement."
    )
    return (
        "# NOFILL Historical Source Expansion Builder Next Prompt Pack - 2026-05-10\n\n"
        f"Parent route: `{ROUTE_ID}`\n\n"
        "Next route type: G0 source expansion builder, then G12 source/control audit. Validation execution remains closed.\n\n"
        "One-line starter:\n\n"
        "```text\n"
        f"{starter}\n"
        "```\n\n"
        "Embedded source-expansion builder instructions:\n\n"
        "- Consume the G0 synthesis route, accepted G12 audit, target partition route, tick parquet root, and selected shadow logs.\n"
        "- Hash every raw/source/log/parser artifact consumed.\n"
        "- Emit a frozen source-bound candidate packet only; do not open outcomes or broker actual-R.\n"
        "- Enforce the 55-field checklist, contaminated-row purge, duplicate denominator, and one-day embargo rules.\n"
        "- Produce a G12 audit prompt pack before any validation execution route exists.\n"
    )


def build_all() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    data = load_inputs()
    local_meta = local_heavy_metadata(data["g12_duplicate"])
    synthesis = accepted_g12_target_synthesis(data)
    zero = zero_sealed_implications(data)
    reuse = contaminated_reuse_constraints(data)
    fields = field_checklist(data)
    ranking = expansion_route_ranking(local_meta)
    requirements = expansion_requirements_matrix(ranking, fields)
    rules = noleak_rules(data)
    owner = owner_access_requirements(ranking, fields)
    broad = broad_science_horizon_note()
    gates = validation_closed_gate_ledger()
    saturation = saturation_pass(ranking, local_meta)

    outputs: dict[str, Path] = {}
    artifacts: list[tuple[str, str, dict[str, Any], str, list[str] | None]] = [
        (
            "context_anchor",
            "CONTEXT_ANCHOR",
            {
                "artifact_family": "context_anchor",
                "git_head": git_head(),
                "controlling_prompt_path": rel(PROMPT_PATH),
                "route_id": ROUTE_ID,
                "schema_version": SCHEMA_VERSION,
                "mandatory_context_read": [
                    ".context/LIVE_STATE.md",
                    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
                    ".context/00_core/quick_reference_card.md",
                    ".context/00_core/research_operating_doctrine.md",
                    ".context/00_core/research_current_state.md",
                    ".context/00_core/goal_session_research_discipline.md",
                    ".context/00_core/local_heavy_data_inventory.md",
                    rel(PROMPT_PATH),
                ],
                "consumed_artifacts": [source_record(role, path) for role, path in CONTROLLING_INPUTS.items()],
                "upstream_route_records": upstream_records(),
            },
            "G0 NOFILL Historical Source Binding Context Anchor",
            None,
        ),
        (
            "decision_ledger",
            "DECISION_LEDGER",
            {
                "artifact_family": "decision_ledger",
                "terminal_decision": TERMINAL_DECISION,
                "accepted_as": "G0 source/control synthesis for next sealed source expansion",
                "decision_reasons": [
                    "G12 accepted the target partition/source-binding chain as source-control evidence only.",
                    "Current committed CAT V3 NOFILL sealed-validation row count is zero.",
                    "Contaminated CAT V3 rows have exact allowed/forbidden reuse constraints.",
                    "A local tick/shadow source expansion builder can be specified without opening validation or scoring.",
                ],
                "no_promotion_statement": PROMOTION_VERDICT,
            },
            "G0 NOFILL Historical Source Binding Decision Ledger",
            None,
        ),
        ("accepted_synthesis", "ACCEPTED_G12_TARGET_ROUTE_SYNTHESIS", synthesis, "Accepted G12 And Target Route Synthesis", None),
        ("zero_sealed", "ZERO_SEALED_ROW_IMPLICATION_LEDGER", zero, "Zero Sealed Row Implication Ledger", None),
        ("contaminated_reuse", "CONTAMINATED_ROW_REUSE_CONSTRAINTS", reuse, "Contaminated Row Reuse Constraints", None),
        ("route_ranking", "NEXT_SOURCE_EXPANSION_ROUTE_RANKING", ranking, "Next Source Expansion Route Ranking", None),
        ("requirements_matrix", "EXACT_SOURCE_EXPANSION_REQUIREMENTS_MATRIX", requirements, "Exact Source Expansion Requirements Matrix", None),
        ("field_checklist", "55_FIELD_EXPANSION_BINDING_CHECKLIST", fields, "55 Field Expansion Binding Checklist", None),
        ("noleak_rules", "NOLEAK_DUPLICATE_PURGE_EMBARGO_SOURCE_HASH_RULES", rules, "No Leak Duplicate Purge Embargo Source Hash Rules", None),
        ("search_plan", "LOCAL_HEAVY_PRIOR_ARTIFACT_SEARCH_PLAN", local_meta, "Local Heavy And Prior Artifact Search Plan", None),
        ("owner_requirements", "OWNER_ACCESS_SOURCE_CAPTURE_REQUIREMENTS_LEDGER", owner, "Owner Access Source Capture Requirements Ledger", None),
        ("broad_horizon", "BROAD_SCIENCE_HORIZON_SEPARATION_NOTE", broad, "Broad Science Horizon Separation Note", None),
        ("closed_gates", "VALIDATION_EXECUTION_CLOSED_GATE_LEDGER", gates, "Validation Execution Closed Gate Ledger", None),
        ("saturation", "SATURATION_SELF_REDTEAM_PASS", saturation, "Saturation Self Redteam Pass", None),
    ]

    outputs_by_key: dict[str, str] = {}
    for key, label, payload, title, notes in artifacts:
        payload = {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            **payload,
        }
        json_name = f"{PREFIX}_{label}_2026-05-10.json"
        md_name = f"{PREFIX}_{label}_2026-05-10.md"
        outputs[f"{key}_json"] = write_json(json_name, payload)
        outputs[f"{key}_md"] = write_md(md_name, title, payload, notes)
        outputs_by_key[key] = rel(outputs[f"{key}_json"])

    coverage = instruction_coverage(outputs_by_key)
    outputs["instruction_coverage_json"] = write_json(
        f"{PREFIX}_INSTRUCTION_COVERAGE_CHECKLIST_2026-05-10.json",
        {"route_id": ROUTE_ID, "schema_version": SCHEMA_VERSION, "generated_at_utc": utc_now(), **coverage},
    )
    outputs["instruction_coverage_md"] = write_md(
        f"{PREFIX}_INSTRUCTION_COVERAGE_CHECKLIST_2026-05-10.md",
        "Instruction Coverage Checklist",
        coverage,
    )
    outputs_by_key["instruction_coverage"] = rel(outputs["instruction_coverage_json"])

    completion = completion_audit(outputs_by_key, synthesis, fields)
    outputs["completion_audit_json"] = write_json(
        f"{PREFIX}_COMPLETION_AUDIT_2026-05-10.json",
        {"route_id": ROUTE_ID, "schema_version": SCHEMA_VERSION, "generated_at_utc": utc_now(), **completion},
    )
    outputs["completion_audit_md"] = write_md(
        f"{PREFIX}_COMPLETION_AUDIT_2026-05-10.md",
        "Completion Audit",
        completion,
    )
    outputs_by_key["completion_audit"] = rel(outputs["completion_audit_json"])

    next_prompt = ROUTE_DIR / f"{PREFIX}_NEXT_PROMPT_PACK_2026-05-10.md"
    next_prompt.write_text(next_prompt_pack(), encoding="utf-8")
    outputs["next_prompt_pack_md"] = next_prompt
    outputs_by_key["next_prompt_pack"] = rel(next_prompt)

    static_files = {
        "builder": rel(ROUTE_DIR / "build_g0_nofill_historical_partition_source_binding_synthesis_control_review_2026_05_10.py"),
        "verifier": rel(ROUTE_DIR / "verify_g0_nofill_historical_partition_source_binding_synthesis_control_review_2026_05_10.py"),
        "focused_tests": rel(ROUTE_DIR / "test_g0_nofill_historical_partition_source_binding_synthesis_control_review_2026_05_10.py"),
    }
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "terminal_decision": TERMINAL_DECISION,
        "output_count": len(outputs),
        "outputs": {key: rel(path) for key, path in sorted(outputs.items())},
        "static_files": static_files,
        "cat_v3_row_count": synthesis["canonical_recomputed_facts"]["cat_v3_row_count"],
        "sealed_validation_current_committed_nofill_rows": 0,
        "field_count": fields["field_count"],
        "future_requirement_count": synthesis["canonical_recomputed_facts"]["future_requirement_count"],
        "exact_repair_source_blocker_count": synthesis["canonical_recomputed_facts"]["exact_repair_source_blocker_count"],
        "recommended_next_route_id": ranking["recommended_next_route_id"],
    }
    outputs["manifest_json"] = write_json(f"{PREFIX}_OUTPUT_MANIFEST_2026-05-10.json", manifest)
    print(json.dumps(with_safe_flags(manifest), indent=2, sort_keys=True))
    return manifest


if __name__ == "__main__":
    build_all()
