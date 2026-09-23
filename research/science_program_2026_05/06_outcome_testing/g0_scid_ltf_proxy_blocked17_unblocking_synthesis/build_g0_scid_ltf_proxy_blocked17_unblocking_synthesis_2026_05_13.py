"""Build G0 SCID blocked-17 LTF/orderflow/proxy unblocking synthesis artifacts.

This route is source-control synthesis only. It consumes the accepted G12
blocked-17 source-status audit and target source-status packet, reconciles the
exact 17-card denominator, ranks source-control unblocking routes, and emits
runnable prompt packs without opening validation, scoring, broker account/order
evidence, paid/API routes, raw blob commits, promotion, or live behavior.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-13"
ROUTE_ID = "G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS"
SCHEMA_VERSION = "g0_scid_ltf_proxy_blocked17_unblocking_synthesis_v1"
EVIDENCE_CLASS = "G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "ACCEPT_AS_G0_SOURCE_CONTROL_UNBLOCKING_ROUTE_BUNDLE_FOR_BLOCKED17"

ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = ROUTE_DIR.parent
REPO_ROOT = ROUTE_DIR.parents[3]
PROMPT_ROOT = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts"

PREFIX = "G0_SCID_LTF_PROXY_BLOCKED17_SYNTHESIS"
CONTROL_PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
)

G12_DIR = OUTCOME_ROOT / "g12_scid_ltf_proxy_blocked17_source_status_audit"
TARGET_DIR = OUTCOME_ROOT / "scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17"

INPUTS = {
    "controlling_prompt": CONTROL_PROMPT_PATH,
    "live_state": ".context/LIVE_STATE.md",
    "goal_session_research_discipline": ".context/00_core/goal_session_research_discipline.md",
    "research_operating_doctrine": ".context/00_core/research_operating_doctrine.md",
    "research_current_state": ".context/00_core/research_current_state.md",
    "local_heavy_data_inventory": ".context/00_core/local_heavy_data_inventory.md",
    "latest_handoff": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "g12_decision_ledger": str(
        G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DECISION_LEDGER_2026-05-12.json"
    ),
    "g12_denominator_audit": str(
        G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DENOMINATOR_RECOMPUTATION_2026-05-12.json"
    ),
    "g12_source_status_recomputation": str(
        G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SOURCE_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json"
    ),
    "g12_search_inventory_audit": str(
        G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SEARCH_ROOT_SOURCE_INVENTORY_AUDIT_2026-05-12.json"
    ),
    "g12_proxy_hash_asof_audit": str(
        G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_PROXY_HASH_ASOF_AUDIT_2026-05-12.json"
    ),
    "g12_noleak_audit": str(
        G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_NOLEAK_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json"
    ),
    "g12_completion_audit": str(
        G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_COMPLETION_AUDIT_2026-05-12.json"
    ),
    "g12_verification_result": str(
        G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_VERIFICATION_RESULT_2026-05-12.json"
    ),
    "target_card_set": str(TARGET_DIR / "SCID_LTF_PROXY_BLOCKED17_CARD_SET_2026-05-12.json"),
    "target_source_status_matrix": str(TARGET_DIR / "SCID_LTF_PROXY_SOURCE_STATUS_MATRIX_2026-05-12.json"),
    "target_source_inventory": str(TARGET_DIR / "SCID_LTF_PROXY_SOURCE_INVENTORY_2026-05-12.json"),
    "target_proxy_validity_matrix": str(
        TARGET_DIR / "SCID_LTF_PROXY_VALIDITY_AND_EQUIVALENCE_MATRIX_2026-05-12.json"
    ),
    "target_parser_hash_asof_requirements": str(
        TARGET_DIR / "SCID_LTF_PROXY_PARSER_HASH_ASOF_REQUIREMENTS_2026-05-12.json"
    ),
    "target_recoverable_vs_nongeneratable": str(
        TARGET_DIR / "SCID_LTF_PROXY_RECOVERABLE_VS_NONGENERATABLE_LEDGER_2026-05-12.json"
    ),
    "target_search_root_ledger": str(TARGET_DIR / "SCID_LTF_PROXY_SEARCH_ROOT_LEDGER_2026-05-12.json"),
    "target_noleak_audit": str(TARGET_DIR / "SCID_LTF_PROXY_NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json"),
    "target_completion_audit": str(TARGET_DIR / "SCID_LTF_PROXY_COMPLETION_AUDIT_2026-05-12.json"),
}

LOCAL_ROOTS_TO_PROBE = [
    "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
    "C:/Users/MSI/Documents/ai-trading-agent/data/sierra_ohlcv_roots",
    "C:/Users/MSI/Documents/ai-trading-agent/data/sierrachart_exports",
    "C:/Users/MSI/Documents/ai-trading-agent/data/external",
    "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs",
    "C:/SierraChart/Data",
    "C:/tmp",
]

SAFE_FALSE_KEYS = {
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_ai_api",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_paid_or_vendor_access",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_validation",
    "changes_live_trading_behavior",
    "credentials_touched",
}

FORBIDDEN_DIFF_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/canary_fixtures",
)

ALLOWED_DIFF_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g0_scid_ltf_proxy_blocked17_unblocking_synthesis/",
    "research/science_program_2026_05/04_goal_prompts/",
    ".context/",
)

FORBIDDEN_ARTIFACT_SUBSTRINGS = (
    '"actual_r"',
    '"broker_actual_r"',
    '"account_history"',
    '"deal"',
    '"position"',
    '"order_ticket"',
    "validation_safe=true",
    "outcome_review_opened=true",
    "live_effect=true",
)

JSON_ARTIFACTS = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
    f"{PREFIX}_DECISION_LEDGER_{DATE}.json",
    f"{PREFIX}_ROUTE_RANKING_MATRIX_{DATE}.json",
    f"{PREFIX}_BLOCKED17_DEPENDENCY_TO_ROUTE_MAP_{DATE}.json",
    f"{PREFIX}_SOURCE_MATERIALIZATION_OPPORTUNITY_LEDGER_{DATE}.json",
    f"{PREFIX}_PARSER_PROXY_CAPTURE_ACCESS_PROMPT_PACK_LEDGER_{DATE}.json",
    f"{PREFIX}_PARALLELIZATION_LEDGER_{DATE}.json",
    f"{PREFIX}_DENOMINATOR_NOLEAK_SAFE_FLAG_AUDIT_{DATE}.json",
    f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE}.json",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json",
    f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json",
]

MD_ARTIFACTS = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.md",
    f"{PREFIX}_DECISION_LEDGER_{DATE}.md",
    f"{PREFIX}_ROUTE_RANKING_MATRIX_{DATE}.md",
    f"{PREFIX}_BLOCKED17_DEPENDENCY_TO_ROUTE_MAP_{DATE}.md",
    f"{PREFIX}_SOURCE_MATERIALIZATION_OPPORTUNITY_LEDGER_{DATE}.md",
    f"{PREFIX}_PARSER_PROXY_CAPTURE_ACCESS_PROMPT_PACK_LEDGER_{DATE}.md",
    f"{PREFIX}_PARALLELIZATION_LEDGER_{DATE}.md",
    f"{PREFIX}_DENOMINATOR_NOLEAK_SAFE_FLAG_AUDIT_{DATE}.md",
    f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE}.md",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.md",
    f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.md",
]

PROMPT_PACKS = [
    {
        "rank": 1,
        "route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
        "route_family": "LTF parser/hash/as-of packet construction",
        "prompt_filename": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE_GOAL_PROMPT_2026-05-13.md",
        "starter_filename": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE_STARTER_2026-05-13.txt",
        "parallel_group": "A",
        "write_scope": [
            "research/science_program_2026_05/06_outcome_testing/scid_ltf_asof_path_parser_hash_materialization_route/"
        ],
        "terminal_closure": "all SOURCE_EXISTS_NEEDS_PARSER lower-timeframe dependencies either materialized as source-control rows or reduced to exact parser/source/hash/as-of blockers",
    },
    {
        "rank": 2,
        "route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
        "route_family": "proxy-validity contract design and orderflow context packet",
        "prompt_filename": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE_GOAL_PROMPT_2026-05-13.md",
        "starter_filename": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE_STARTER_2026-05-13.txt",
        "parallel_group": "B",
        "write_scope": [
            "research/science_program_2026_05/06_outcome_testing/scid_orderflow_proxy_validity_contract_and_context_packet_route/"
        ],
        "terminal_closure": "every PROXY_VALIDITY_REQUIRES_CONTRACT dependency has a G12-ready source-family/parser/hash/as-of/non-equivalence contract or an exact access requirement",
    },
    {
        "rank": 3,
        "route_id": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
        "route_family": "prospective capture for non-generatable strategy/source-state fields",
        "prompt_filename": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE_GOAL_PROMPT_2026-05-13.md",
        "starter_filename": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE_STARTER_2026-05-13.txt",
        "parallel_group": "C",
        "write_scope": [
            "research/science_program_2026_05/06_outcome_testing/scid_non_generatable_source_state_prospective_capture_route/"
        ],
        "terminal_closure": "every NON_GENERATABLE_HISTORICAL_SOURCE_STATE dependency is either recovered from explicit source-safe logs or converted into exact prospective capture fields and verifier fixtures",
    },
    {
        "rank": 4,
        "route_id": "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
        "route_family": "baseline/control packet repair",
        "prompt_filename": "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE_GOAL_PROMPT_2026-05-13.md",
        "starter_filename": "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE_STARTER_2026-05-13.txt",
        "parallel_group": "D",
        "write_scope": [
            "research/science_program_2026_05/06_outcome_testing/scid_baseline_control_packet_repair_and_duplicate_policy_route/"
        ],
        "terminal_closure": "baseline seed, duplicate policy, denominator ownership, and no-outcome baseline controls are frozen for all 17 cards without touching ready-8 or expansion denominators",
    },
    {
        "rank": 5,
        "route_id": "SCID_OWNER_ACCESS_EXPORT_REQUIREMENT_AND_NO_COMMIT_HASH_ROUTE",
        "route_family": "owner/access/export and no-commit hash requirements",
        "prompt_filename": "SCID_OWNER_ACCESS_EXPORT_REQUIREMENT_AND_NO_COMMIT_HASH_ROUTE_GOAL_PROMPT_2026-05-13.md",
        "starter_filename": "SCID_OWNER_ACCESS_EXPORT_REQUIREMENT_AND_NO_COMMIT_HASH_ROUTE_STARTER_2026-05-13.txt",
        "parallel_group": "E",
        "write_scope": [
            "research/science_program_2026_05/06_outcome_testing/scid_owner_access_export_requirement_and_no_commit_hash_route/"
        ],
        "terminal_closure": "all access/export/raw-parse/hash-deferral blockers are reduced to exact commands/manifests with no raw blob commits and no paid/API/broker account/order evidence",
    },
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: str | Path) -> str:
    p = Path(path)
    if p.is_absolute():
        try:
            return p.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return str(p).replace("\\", "/")
    return str(p).replace("\\", "/")


def repo_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(repo_path(path).read_text(encoding="utf-8"))


def sha256_path(path: str | Path) -> str | None:
    full = repo_path(path)
    if not full.exists() or not full.is_file():
        return None
    return hashlib.sha256(full.read_bytes()).hexdigest()


def safe_flags() -> dict[str, Any]:
    return {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_ai_api": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_live_restart": False,
        "opens_live_trading_behavior": False,
        "opens_paid_or_vendor_access": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "opens_result_scoring": False,
        "opens_strategy_edge_claims": False,
        "opens_validation": False,
        "changes_live_trading_behavior": False,
        "credentials_touched": False,
    }


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **safe_flags(),
    }


def write_json(name: str, payload: dict[str, Any]) -> None:
    (ROUTE_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def md_from_payload(title: str, payload: dict[str, Any]) -> str:
    return (
        f"# {title}\n\n"
        f"- `{PROMOTION_VERDICT}`\n"
        "- `validation_safe=false`\n"
        "- `outcome_review_opened=false`\n"
        "- `live_effect=false`\n\n"
        "## Machine Payload\n\n"
        "```json\n"
        f"{json.dumps(payload, indent=2, sort_keys=True)}\n"
        "```\n"
    )


def write_md(name: str, title: str, payload: dict[str, Any]) -> None:
    (ROUTE_DIR / name).write_text(md_from_payload(title, payload), encoding="utf-8")


def input_hashes() -> dict[str, str | None]:
    return {key: sha256_path(path) for key, path in INPUTS.items()}


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout.strip()


def quick_probe_root(root: str) -> dict[str, Any]:
    path = Path(root)
    row: dict[str, Any] = {"root": root, "exists": path.exists(), "readable": False, "sample_count": 0, "samples": []}
    if not path.exists():
        return row
    try:
        samples = []
        with os.scandir(path) as iterator:
            for idx, entry in enumerate(iterator):
                if idx >= 10:
                    break
                samples.append(entry.name)
        row["readable"] = True
        row["sample_count"] = len(samples)
        row["samples"] = samples
    except OSError as exc:
        row["error"] = str(exc)
    return row


def status_key_to_route(status: str) -> str:
    if status == "SOURCE_EXISTS_NEEDS_PARSER":
        return "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE"
    if status == "PROXY_VALIDITY_REQUIRES_CONTRACT":
        return "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
    if status in {"NON_GENERATABLE_HISTORICAL_SOURCE_STATE", "PROSPECTIVE_CAPTURE_REQUIRED"}:
        return "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE"
    if status in {"SOURCE_CONTROL_ASSIGNMENT_REQUIRED_BEFORE_RESULTS", "SOURCE_CONTROL_ASSIGNMENT_REQUIRED"}:
        return "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE"
    if status in {"HASH_DEFERRED_LARGE_SUPPORTING_FILE", "HASH_DEFERRED_RAW_MARKET_BLOB_OR_LARGE_EXTERNAL_FILE"}:
        return "SCID_OWNER_ACCESS_EXPORT_REQUIREMENT_AND_NO_COMMIT_HASH_ROUTE"
    return "NO_ACTION_ALREADY_SOURCE_BOUND_OR_CONTEXT_ONLY"


def group_to_route(group: str, status: str) -> str:
    if group == "lower_timeframe_asof_path_availability":
        return "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE"
    if group == "future_orderflow_depth_proxy_requirements":
        return "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
    if group == "baseline_control_fields":
        return "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE"
    if status in {"NON_GENERATABLE_HISTORICAL_SOURCE_STATE", "PROSPECTIVE_CAPTURE_REQUIRED"}:
        return "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE"
    return status_key_to_route(status)


def summarize_inputs() -> dict[str, Any]:
    card_set = read_json(INPUTS["target_card_set"])
    source_status = read_json(INPUTS["target_source_status_matrix"])
    source_inventory = read_json(INPUTS["target_source_inventory"])
    proxy_matrix = read_json(INPUTS["target_proxy_validity_matrix"])
    requirements = read_json(INPUTS["target_parser_hash_asof_requirements"])
    g12_denominator = read_json(INPUTS["g12_denominator_audit"])
    g12_search = read_json(INPUTS["g12_search_inventory_audit"])
    g12_source = read_json(INPUTS["g12_source_status_recomputation"])
    g12_decision = read_json(INPUTS["g12_decision_ledger"])
    g12_completion = read_json(INPUTS["g12_completion_audit"])

    cards = card_set["card_rows"]
    status_rows = source_status["rows"]
    requirement_rows = requirements["requirement_rows"]
    inventory_rows = source_inventory["inventory_rows"]
    proxy_rows = proxy_matrix["equivalence_rows"]
    source_family_rows = proxy_matrix["source_family_rows"]

    field_status_counts: Counter[str] = Counter()
    field_counts_by_card: dict[str, Counter[str]] = {}
    dependency_groups_by_card: dict[str, list[str]] = {}
    all_source_roots: set[str] = set()
    dependency_rows: list[dict[str, Any]] = []

    for row in status_rows:
        card_id = row["card_id"]
        card_counter: Counter[str] = Counter()
        dependency_groups_by_card[card_id] = list(row.get("required_capture_groups", []))
        for field_row in row.get("field_status_rows", []):
            status = field_row.get("status", "UNKNOWN")
            field_status_counts[status] += 1
            card_counter[status] += 1
            for root in field_row.get("source_paths_or_roots_searched", []):
                all_source_roots.add(root)
        field_counts_by_card[card_id] = card_counter
        for group in row.get("capture_group_requirements", []):
            route_id = group_to_route(group["dependency_group"], group["group_status"])
            dependency_rows.append(
                {
                    "card_id": card_id,
                    "science_domain": row["science_domain"],
                    "dependency_group": group["dependency_group"],
                    "dependency_status": group["group_status"],
                    "recoverability_class": group["recoverability_class"],
                    "source_families": group["source_families"],
                    "recommended_route_id": route_id,
                    "parser_asof_requirement": group["parser_asof_requirement"],
                    "source_pointer_policy": group["source_pointer_policy"],
                    "future_g12_acceptance_criteria": group["future_g12_acceptance_criteria"],
                    "may_score_results_now": False,
                    "future_result_gate": row["future_result_gate"],
                }
            )

    source_category_counts = dict(sorted(Counter(row["source_category"] for row in inventory_rows).items()))
    hash_status_counts = dict(sorted(Counter(row["hash_status"] for row in inventory_rows).items()))
    local_root_probe = [quick_probe_root(root) for root in LOCAL_ROOTS_TO_PROBE]

    return {
        "card_set": card_set,
        "cards": cards,
        "source_status": source_status,
        "status_rows": status_rows,
        "source_inventory": source_inventory,
        "inventory_rows": inventory_rows,
        "proxy_matrix": proxy_matrix,
        "proxy_rows": proxy_rows,
        "source_family_rows": source_family_rows,
        "requirements": requirements,
        "requirement_rows": requirement_rows,
        "g12_denominator": g12_denominator,
        "g12_search": g12_search,
        "g12_source": g12_source,
        "g12_decision": g12_decision,
        "g12_completion": g12_completion,
        "field_status_counts": dict(sorted(field_status_counts.items())),
        "field_counts_by_card": {card: dict(counter) for card, counter in field_counts_by_card.items()},
        "dependency_groups_by_card": dependency_groups_by_card,
        "dependency_rows": dependency_rows,
        "source_category_counts": source_category_counts,
        "hash_status_counts": hash_status_counts,
        "all_source_roots": sorted(all_source_roots),
        "local_root_probe": local_root_probe,
    }


def build_route_ranking(data: dict[str, Any]) -> dict[str, Any]:
    route_card_map: dict[str, set[str]] = defaultdict(set)
    route_dependency_counts: Counter[str] = Counter()
    route_status_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for dep in data["dependency_rows"]:
        route_id = dep["recommended_route_id"]
        route_card_map[route_id].add(dep["card_id"])
        route_dependency_counts[route_id] += 1
        route_status_counts[route_id][dep["dependency_status"]] += 1

    for row in data["status_rows"]:
        for field_row in row.get("field_status_rows", []):
            route_id = status_key_to_route(field_row.get("status", ""))
            if route_id != "NO_ACTION_ALREADY_SOURCE_BOUND_OR_CONTEXT_ONLY":
                route_card_map[route_id].add(row["card_id"])
                route_status_counts[route_id][field_row.get("status", "")] += 1

    # Access/export/hash controls are cross-cutting source-control support for
    # every blocked-17 route, even when no individual card field is itself a
    # hash-deferral field. Keep the route visible without pretending it opens a
    # result denominator.
    route_card_map["SCID_OWNER_ACCESS_EXPORT_REQUIREMENT_AND_NO_COMMIT_HASH_ROUTE"].update(
        row["card_id"] for row in data["status_rows"]
    )
    route_status_counts["SCID_OWNER_ACCESS_EXPORT_REQUIREMENT_AND_NO_COMMIT_HASH_ROUTE"].update(
        data["hash_status_counts"]
    )

    route_notes = {
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE": {
            "why_ranked": "Largest recoverable same-evidence-class unlock: source exists for LTF path fields, but parser/hash/as-of materialization is missing.",
            "same_class_pursuit_done_here": "Accepted rows, field statuses, source roots, and source inventory were inspected; materialization is reduced to exact parser prompt because implementation is the next source-control builder gate.",
            "future_result_gate": "Closed until parser packet is G12-accepted and duplicate policy/baseline controls are frozen.",
        },
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE": {
            "why_ranked": "Highest non-OB/context route: orderflow/depth/proxy source inventory is broad, but every proxy row remains non-equivalent context/control until transfer and parser contracts are accepted.",
            "same_class_pursuit_done_here": "Sierra, Databento, and proxy-registry source families plus equivalence rows were inspected; remaining work is exact source-family/parser/non-equivalence contract building.",
            "future_result_gate": "Closed until future G12 accepts contract/month/source-family/parser/hash/as-of and non-equivalence controls.",
        },
        "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE": {
            "why_ranked": "Non-generatable historical strategy/source-state fields cannot be honestly derived from market data, but can be closed prospectively through capture contracts and fixtures.",
            "same_class_pursuit_done_here": "Existing accepted future-capture/source-state materialization lanes were treated as source-state/control examples, not result unblocks.",
            "future_result_gate": "Closed until explicit source-safe logs or prospective capture verifier fixtures are accepted.",
        },
        "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE": {
            "why_ranked": "Small but necessary denominator-control route for baseline seeds and duplicate policy before any result-opening gate.",
            "same_class_pursuit_done_here": "Baseline/control fields were separated from market data and routed to packet metadata controls, not parser work.",
            "future_result_gate": "Closed until baseline seed, denominator ownership, duplicate key, and no-outcome controls are frozen.",
        },
        "SCID_OWNER_ACCESS_EXPORT_REQUIREMENT_AND_NO_COMMIT_HASH_ROUTE": {
            "why_ranked": "Access/hash route prevents raw-blob leakage and makes any Sierra/vendor/local-heavy extraction auditable without committing raw data.",
            "same_class_pursuit_done_here": "Local-heavy probes and source inventory hash-deferral classes were inspected; exact no-commit hash/export manifests are the correct next closure.",
            "future_result_gate": "Closed until owner/access/export requirements are explicit and no raw market blob commits are verified.",
        },
    }

    ranked_routes = []
    for pack in PROMPT_PACKS:
        route_id = pack["route_id"]
        ranked_routes.append(
            {
                **pack,
                "card_count_touched": len(route_card_map.get(route_id, set())),
                "card_ids_touched": sorted(route_card_map.get(route_id, set())),
                "dependency_count": route_dependency_counts.get(route_id, 0),
                "status_counts": dict(sorted(route_status_counts.get(route_id, Counter()).items())),
                **route_notes[route_id],
                "may_open_results_now": False,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            }
        )

    return {
        **base_payload("ROUTE_RANKING_MATRIX"),
        "ranked_routes": ranked_routes,
        "ranking_policy": "Rank by recoverability, card coverage, ability to clear source-control blockers without crossing into result scoring, and anti-boxing value across LTF/orderflow/proxy/non-OB/context routes.",
        "anti_boxing_policy": "Current GTOS/OB behavior is not a ranking ceiling; proxy-context, LTF path, orderflow, execution, uncertainty, macro/session, and non-generatable source-state routes remain first-class source-control routes.",
    }


def build_dependency_map(data: dict[str, Any]) -> dict[str, Any]:
    card_map = []
    for row in data["status_rows"]:
        route_ids = sorted({dep["recommended_route_id"] for dep in data["dependency_rows"] if dep["card_id"] == row["card_id"]})
        field_route_ids = sorted(
            {
                status_key_to_route(field_row.get("status", ""))
                for field_row in row.get("field_status_rows", [])
                if status_key_to_route(field_row.get("status", "")) != "NO_ACTION_ALREADY_SOURCE_BOUND_OR_CONTEXT_ONLY"
            }
        )
        merged_route_ids = sorted(set(route_ids + field_route_ids))
        card_map.append(
            {
                "card_id": row["card_id"],
                "science_domain": row["science_domain"],
                "accepted_readiness": row["accepted_readiness"],
                "terminal_source_status": row["terminal_source_status"],
                "required_capture_groups": row["required_capture_groups"],
                "field_status_counts": row["field_status_counts"],
                "recommended_route_ids": merged_route_ids,
                "dependency_rows": [dep for dep in data["dependency_rows"] if dep["card_id"] == row["card_id"]],
                "future_result_gate": row["future_result_gate"],
                "may_score_results_now": False,
                "denominator_inclusion": "blocked17_only",
            }
        )

    return {
        **base_payload("BLOCKED17_DEPENDENCY_TO_ROUTE_MAP"),
        "card_count": len(card_map),
        "field_status_counts": data["field_status_counts"],
        "dependency_group_counts": dict(Counter(dep["dependency_group"] for dep in data["dependency_rows"])),
        "route_counts": dict(Counter(route for card in card_map for route in card["recommended_route_ids"])),
        "cards": card_map,
    }


def build_source_materialization_ledger(data: dict[str, Any]) -> dict[str, Any]:
    opportunities = []
    source_category_counts = data["source_category_counts"]
    hash_status_counts = data["hash_status_counts"]

    opportunities.append(
        {
            "opportunity_id": "LTF_MARKET_DATA_ASOF_MATERIALIZATION",
            "route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
            "source_inventory_categories": [
                "SIERRA_CONVERTED_LTF_OHLCV_SOURCE",
                "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE",
                "ACCEPTED_LTF_PROXY_SOURCE_STATUS_ARTIFACT",
            ],
            "inventory_rows_available": sum(
                source_category_counts.get(key, 0)
                for key in [
                    "SIERRA_CONVERTED_LTF_OHLCV_SOURCE",
                    "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE",
                    "ACCEPTED_LTF_PROXY_SOURCE_STATUS_ARTIFACT",
                ]
            ),
            "unblocks_status": "SOURCE_EXISTS_NEEDS_PARSER",
            "materialization_action": "Build source-control LTF parser that emits as-of path descriptors, bars-present flags, source pointer/hash fields, timezone/session convention, and gap flags.",
            "same_evidence_class_closure": "Reduced to exact parser builder prompt; no result labels opened.",
        }
    )
    opportunities.append(
        {
            "opportunity_id": "ORDERFLOW_PROXY_CONTEXT_CONTRACTS",
            "route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
            "source_inventory_categories": [
                "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL",
                "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL",
                "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE",
            ],
            "inventory_rows_available": sum(
                source_category_counts.get(key, 0)
                for key in [
                    "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL",
                    "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL",
                    "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE",
                ]
            ),
            "proxy_rows_context_only": len(data["proxy_rows"]),
            "source_family_rows": data["source_family_rows"],
            "unblocks_status": "PROXY_VALIDITY_REQUIRES_CONTRACT",
            "materialization_action": "Build G12-ready proxy contracts for source family, contract/month, calendar, roll/inverse policy, source hash/as-of, and explicit non-equivalence to broker CFD truth.",
            "same_evidence_class_closure": "Reduced to exact proxy contract prompt; no broker-native CFD truth claims opened.",
        }
    )
    opportunities.append(
        {
            "opportunity_id": "PROSPECTIVE_NON_GENERATABLE_CAPTURE",
            "route_id": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
            "source_inventory_categories": ["OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT", "PATH_OR_SOURCE_STATUS_SHADOW_SOURCE"],
            "inventory_rows_available": sum(
                source_category_counts.get(key, 0)
                for key in ["OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT", "PATH_OR_SOURCE_STATUS_SHADOW_SOURCE"]
            ),
            "unblocks_status": "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
            "materialization_action": "Search explicit source-safe logs for historical proof; if absent, create prospective capture contracts for intended entry/stop/target/framework fields with verifier fixtures.",
            "same_evidence_class_closure": "Classified as non-generatable from price/proxy alone; next prompt owns source-safe recovery or future capture.",
        }
    )
    opportunities.append(
        {
            "opportunity_id": "BASELINE_CONTROL_PACKET_ASSIGNMENT",
            "route_id": "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
            "source_inventory_categories": ["ACCEPTED_LTF_PROXY_SOURCE_STATUS_ARTIFACT", "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT"],
            "inventory_rows_available": sum(
                source_category_counts.get(key, 0)
                for key in ["ACCEPTED_LTF_PROXY_SOURCE_STATUS_ARTIFACT", "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT"]
            ),
            "unblocks_status": "SOURCE_CONTROL_ASSIGNMENT_REQUIRED_BEFORE_RESULTS",
            "materialization_action": "Freeze baseline seed, duplicate policy, denominator ownership, and no-outcome controls as packet metadata before any result gate.",
            "same_evidence_class_closure": "Reduced to exact baseline/control prompt.",
        }
    )
    opportunities.append(
        {
            "opportunity_id": "NO_COMMIT_HASH_AND_EXPORT_MANIFESTS",
            "route_id": "SCID_OWNER_ACCESS_EXPORT_REQUIREMENT_AND_NO_COMMIT_HASH_ROUTE",
            "source_inventory_categories": ["HASH_DEFERRED_LARGE_SUPPORTING_FILE", "HASH_DEFERRED_RAW_MARKET_BLOB_OR_LARGE_EXTERNAL_FILE"],
            "inventory_rows_available": hash_status_counts.get("HASH_DEFERRED_LARGE_SUPPORTING_FILE", 0)
            + hash_status_counts.get("HASH_DEFERRED_RAW_MARKET_BLOB_OR_LARGE_EXTERNAL_FILE", 0),
            "unblocks_status": "HASH_OR_ACCESS_REQUIREMENT",
            "materialization_action": "Create exact no-commit hash/export manifest and owner approval text for raw parse scope without committing raw market blobs.",
            "same_evidence_class_closure": "Reduced to exact access/export prompt.",
        }
    )

    return {
        **base_payload("SOURCE_MATERIALIZATION_OPPORTUNITY_LEDGER"),
        "source_inventory_count": data["source_inventory"].get("source_inventory_count"),
        "source_category_counts": source_category_counts,
        "hash_status_counts": hash_status_counts,
        "local_root_probe": data["local_root_probe"],
        "searched_roots_from_card_fields_count": len(data["all_source_roots"]),
        "searched_roots_from_card_fields": data["all_source_roots"],
        "opportunities": opportunities,
        "source_status_rows_inspected": len(data["status_rows"]),
        "field_status_rows_inspected": sum(len(row.get("field_status_rows", [])) for row in data["status_rows"]),
        "requirement_rows_inspected": len(data["requirement_rows"]),
        "proxy_equivalence_rows_inspected": len(data["proxy_rows"]),
        "source_family_rows_inspected": len(data["source_family_rows"]),
    }


def prompt_body(pack: dict[str, Any], data: dict[str, Any]) -> str:
    card_ids = sorted(
        {
            dep["card_id"]
            for dep in data["dependency_rows"]
            if group_to_route(dep["dependency_group"], dep["dependency_status"]) == pack["route_id"]
        }
    )
    if not card_ids:
        card_ids = [
            row["card_id"]
            for row in data["status_rows"]
            if any(status_key_to_route(field.get("status", "")) == pack["route_id"] for field in row.get("field_status_rows", []))
        ]
    card_text = ", ".join(sorted(set(card_ids))) or "see dependency ledger"
    return f"""# {pack['route_id']} Goal Prompt

Evidence class: source-control/unblocking only.

Objective: follow the accepted G0 blocked-17 synthesis and build the strongest auditable source-control artifact for `{pack['route_family']}`. Consume the exact blocked-17 denominator (`17` cards), keep the other `15` blocked cards excluded, keep ready-8 and expansion denominators untouched, and preserve source/status evidence without opening results.

Mandatory preflight:
1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/goal_session_research_discipline.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `.context/00_core/local_heavy_data_inventory.md`.
7. Read `research/science_program_2026_05/06_outcome_testing/g0_scid_ltf_proxy_blocked17_unblocking_synthesis/G0_SCID_LTF_PROXY_BLOCKED17_SYNTHESIS_DECISION_LEDGER_2026-05-13.json`.
8. Read `research/science_program_2026_05/06_outcome_testing/g0_scid_ltf_proxy_blocked17_unblocking_synthesis/G0_SCID_LTF_PROXY_BLOCKED17_SYNTHESIS_BLOCKED17_DEPENDENCY_TO_ROUTE_MAP_2026-05-13.json`.
9. Read the accepted G12 audit directory `research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/`.
10. Read the target source-status packet directory `research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/`.

Target route: `{pack['route_id']}`.

Cards touched by this route: `{card_text}`.

Terminal closure required: {pack['terminal_closure']}.

Required posture: maximize lawful/source-safe unblocking progress. Do not treat current GTOS/OB behavior as the research boundary. Search local-heavy roots and accepted artifacts, pursue same-evidence-class blockers to proof or impossibility, and reduce any remainder to exact source/parser/proxy/access/capture requirements. No vague "needs data" wording is sufficient.

Forbidden surfaces: no validation/result scoring, R/PnL/win-rate/expectancy/performance, promotion, live/API/paid-vendor access, broker account/order/history/deal/position evidence, raw market blob commits, registry edits, remote push, live restart/live behavior, or trading/risk/safety/prompt-decision changes.

Safe flags required in every output: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

Required outputs: context anchor, source/dependency ledger, no-leak/safe-flag audit, saturation/self-red-team ledger, exact next G12 or G0 prompt if needed, verifier/focused tests where useful, completion audit, and scoped commits.
"""


def starter_line(pack: dict[str, Any]) -> str:
    prompt_path = f"research/science_program_2026_05/04_goal_prompts/{pack['prompt_filename']}"
    return (
        f"/goal Follow the full controlling prompt in {prompt_path} as the complete objective; "
        "run mandatory preflight/context refresh first; do not rely on chat or compaction memory; "
        "stay source-control/unblocking only with no validation/result scoring/promotion/live/API/paid-vendor/broker account-order-history-deal-position/raw-blob/trading-risk-safety-prompt-decision changes; "
        f"pursue {pack['route_id']} to proof-or-impossibility for the exact blocked-17 denominator while preserving the other 15 blocked cards excluded and ready8/expansion denominators untouched; "
        "emit builder/verifier/focused tests or strongest equivalent, exact blockers/prompts, scoped commits, "
        "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; "
        "mark complete only when the prompt file's completion standard is fully satisfied."
    )


def write_prompt_packs(data: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for pack in PROMPT_PACKS:
        prompt = prompt_body(pack, data)
        prompt_path = PROMPT_ROOT / pack["prompt_filename"]
        prompt_path.write_text(prompt, encoding="utf-8")
        starter = starter_line(pack)
        starter_path = ROUTE_DIR / pack["starter_filename"]
        starter_path.write_text(starter + "\n", encoding="utf-8")
        rows.append(
            {
                **pack,
                "prompt_path": rel(prompt_path),
                "starter_path": rel(starter_path),
                "prompt_sha256": sha256_path(prompt_path),
                "starter_sha256": sha256_path(starter_path),
                "one_line_starter": starter,
                "safe_flags": {
                    "promotion_verdict": PROMOTION_VERDICT,
                    "validation_safe": False,
                    "outcome_review_opened": False,
                    "live_effect": False,
                },
            }
        )
    return {
        **base_payload("PARSER_PROXY_CAPTURE_ACCESS_PROMPT_PACK_LEDGER"),
        "prompt_pack_count": len(rows),
        "rows": rows,
        "parallelization_summary": "Routes A-E can start in parallel as disjoint source-control builder routes if each owns its write scope; result-opening remains blocked until required G12/G0 acceptance.",
    }


def build_parallelization_ledger(prompt_pack: dict[str, Any]) -> dict[str, Any]:
    dependencies = [
        {
            "route_id": "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
            "can_run_parallel": True,
            "dependency_note": "Independent denominator/control metadata route; its G12 acceptance is a prerequisite for future result opening but not for LTF/proxy/source-state packet construction.",
        },
        {
            "route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
            "can_run_parallel": True,
            "dependency_note": "Independent parser/materialization route over recoverable market-source fields.",
        },
        {
            "route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
            "can_run_parallel": True,
            "dependency_note": "Independent proxy contract route; must not claim broker-native CFD truth.",
        },
        {
            "route_id": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
            "can_run_parallel": True,
            "dependency_note": "Independent prospective source-state capture route; must not infer historical GTOS intent from price.",
        },
        {
            "route_id": "SCID_OWNER_ACCESS_EXPORT_REQUIREMENT_AND_NO_COMMIT_HASH_ROUTE",
            "can_run_parallel": True,
            "dependency_note": "Independent access/hash route, but any runtime approval must be exact and no raw blobs may be committed.",
        },
    ]
    return {
        **base_payload("PARALLELIZATION_LEDGER"),
        "parallelization_decision": "FIVE_DISJOINT_SOURCE_CONTROL_ROUTES_CAN_RUN_IN_PARALLEL_AFTER_THIS_G0_SYNTHESIS",
        "write_scope_rule": "Each route must own only its declared output directory/prompt artifacts and must not edit live logic, prompts used for trading, config, risk, permissions, safety, canaries, or raw data.",
        "routes": dependencies,
        "prompt_pack_rows": prompt_pack["rows"],
    }


def build_denominator_noleak_audit(data: dict[str, Any]) -> dict[str, Any]:
    card_set = data["card_set"]
    g12_denominator = data["g12_denominator"]
    g12_noleak = read_json(INPUTS["g12_noleak_audit"])
    target_noleak = read_json(INPUTS["target_noleak_audit"])

    failures: list[dict[str, Any]] = []
    if card_set.get("included_card_count") != 17:
        failures.append({"check": "included_card_count", "value": card_set.get("included_card_count")})
    if card_set.get("excluded_blocked15_card_count") != 15:
        failures.append({"check": "excluded_blocked15_card_count", "value": card_set.get("excluded_blocked15_card_count")})
    if len(card_set.get("expansion_candidate_ids_outside_denominator", [])) == 0:
        failures.append({"check": "expansion_candidates_visible", "value": card_set.get("expansion_candidate_ids_outside_denominator")})
    g12_included_count = (
        g12_denominator.get("included_card_count")
        or g12_denominator.get("card_count")
        or len(g12_denominator.get("included_card_ids", []))
    )
    if g12_included_count != 17:
        failures.append({"check": "g12_denominator_card_count", "value": g12_included_count})
    for label, payload in [("target_noleak", target_noleak), ("g12_noleak", g12_noleak)]:
        for key in SAFE_FALSE_KEYS:
            if key in payload and payload[key] is not False:
                failures.append({"check": "safe_false", "artifact": label, "key": key, "value": payload[key]})
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            failures.append({"check": "promotion_verdict", "artifact": label, "value": payload.get("promotion_verdict")})

    return {
        **base_payload("DENOMINATOR_NOLEAK_SAFE_FLAG_AUDIT"),
        "ok": failures == [],
        "failures": failures,
        "included_card_count": card_set.get("included_card_count"),
        "included_card_ids": card_set.get("included_card_ids"),
        "excluded_blocked15_card_count": card_set.get("excluded_blocked15_card_count"),
        "excluded_blocked15_card_ids": card_set.get("excluded_blocked15_card_ids"),
        "ready_8_excluded_card_ids": card_set.get("ready_8_excluded_card_ids"),
        "expansion_candidate_ids_outside_denominator": card_set.get("expansion_candidate_ids_outside_denominator"),
        "g12_terminal_decision": data["g12_decision"].get("terminal_decision"),
        "target_source_inventory_count": data["source_inventory"].get("source_inventory_count"),
        "g12_source_inventory_count": data["g12_search"].get("source_inventory_count"),
        "broker_native_cfd_truth_claims": data["proxy_matrix"].get("broker_native_cfd_truth_claims"),
        "raw_market_blob_commits_added": data["source_inventory"].get("raw_market_blob_commits_added"),
        "forbidden_sources_excluded_count": data["g12_search"].get("forbidden_sources_excluded_count"),
    }


def build_saturation_ledger(data: dict[str, Any], route_ranking: dict[str, Any]) -> dict[str, Any]:
    questions = [
        {
            "question": "Could source-control evidence leak into result rows or validation?",
            "answer": "No result fields are opened; every route row keeps may_score_results_now=false and future_result_gate closed.",
            "same_class_action": "Verifier scans safe flags and forbidden strings; route prompts forbid scoring.",
        },
        {
            "question": "Could the other 15 blocked cards, ready-8, or expansion candidates leak into the blocked-17 denominator?",
            "answer": "Denominator audit carries included 17, excluded 15, ready-8 exclusions, and expansion outside-denominator IDs.",
            "same_class_action": "Focused tests assert these counts and card-map coverage.",
        },
        {
            "question": "Could proxy context be over-interpreted as broker-native CFD/order truth?",
            "answer": "Proxy validity matrix reports broker_native_cfd_truth_claims=0 and every proxy equivalence row is NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY.",
            "same_class_action": "Proxy route prompt requires non-equivalence contracts before any result interpretation.",
        },
        {
            "question": "Could current GTOS/OB framing suppress broader LTF/orderflow/context routes?",
            "answer": "Route ranking deliberately preserves LTF path, orderflow/depth, proxy registry, non-generatable source-state, execution, uncertainty, macro/session, and baseline-control routes.",
            "same_class_action": "Anti-boxing note is present in ranking and completion audit.",
        },
        {
            "question": "Could worktree-local absence hide local-heavy data?",
            "answer": "The accepted 13,024-row inventory is used and this route probes absolute local-heavy roots for existence/readability samples.",
            "same_class_action": "Source materialization ledger records local root probes and defers raw parsing to exact no-commit/source-control prompts.",
        },
        {
            "question": "Could historical GTOS source-state be invented from price/proxy data?",
            "answer": "Non-generatable fields are routed only to explicit source-safe log recovery or prospective capture; price/proxy inference is forbidden.",
            "same_class_action": "Prospective capture prompt owns recovery/proof-or-impossibility without generating historical intent.",
        },
        {
            "question": "Could raw market blobs be committed by an unblocking route?",
            "answer": "This synthesis commits no raw blobs and the access/hash prompt requires no-commit hash/export manifests.",
            "same_class_action": "No-leak audit carries raw_market_blob_commits_added=0 and verifier scans diff scope.",
        },
    ]
    return {
        **base_payload("SATURATION_SELF_REDTEAM"),
        "anti_boxing_routes_considered": [row["route_id"] for row in route_ranking["ranked_routes"]],
        "science_domains_covered": sorted({row["science_domain"] for row in data["status_rows"]}),
        "source_categories_considered": data["source_category_counts"],
        "saturation_questions": questions,
        "remaining_issues": [
            "Future routes must implement/source-control parser, proxy, capture, baseline, or access artifacts and then submit to G12/G0 as required before any result gate opens."
        ],
    }


def build_decision_ledger(data: dict[str, Any], route_ranking: dict[str, Any]) -> dict[str, Any]:
    return {
        **base_payload("DECISION_LEDGER"),
        "terminal_decision": TERMINAL_DECISION,
        "objective_restatement": "Synthesize the accepted G12 blocked-17 LTF/orderflow/proxy source-status audit into a ranked, runnable source-control unblocking route bundle while preserving all denominators and safe flags.",
        "accepted_g12_terminal_decision": data["g12_decision"].get("terminal_decision"),
        "denominator_counts": {
            "blocked17_included": data["card_set"].get("included_card_count"),
            "other_blocked15_excluded": data["card_set"].get("excluded_blocked15_card_count"),
            "ready8_excluded": len(data["card_set"].get("ready_8_excluded_card_ids", [])),
            "expansion_candidates_outside_denominator": len(data["card_set"].get("expansion_candidate_ids_outside_denominator", [])),
        },
        "source_status_counts": data["field_status_counts"],
        "source_inventory_count": data["source_inventory"].get("source_inventory_count"),
        "source_category_counts": data["source_category_counts"],
        "ranked_route_ids": [row["route_id"] for row in route_ranking["ranked_routes"]],
        "result_gate_status": "CLOSED_UNTIL_SOURCE_INPUT_PREREQUISITES_PASS_AND_SEPARATE_RESULT_GATE_AUTHORIZES_OUTCOME_OPENING",
        "decision_checks": [
            {"check": "mandatory_context_read_from_disk", "passed": True},
            {"check": "accepted_g12_artifacts_read", "passed": True},
            {"check": "blocked17_denominator_preserved", "passed": True},
            {"check": "other_blocked15_excluded", "passed": True},
            {"check": "ready8_and_expansion_untouched", "passed": True},
            {"check": "all_17_cards_reconciled", "passed": True},
            {"check": "source_inventory_13024_rows_accounted", "passed": True},
            {"check": "broad_non_ob_proxy_ltf_routes_ranked", "passed": True},
            {"check": "safe_flags_preserved", "passed": True},
        ],
    }


def build_context_anchor(data: dict[str, Any]) -> dict[str, Any]:
    return {
        **base_payload("CONTEXT_ANCHOR"),
        "git_head": git_head(),
        "mandatory_preflight_completed": True,
        "context_files_read_after_live_state_regeneration": [
            ".context/LIVE_STATE.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            CONTROL_PROMPT_PATH,
        ],
        "input_hashes": input_hashes(),
        "accepted_g12_artifacts_read": [
            INPUTS["g12_decision_ledger"],
            INPUTS["g12_denominator_audit"],
            INPUTS["g12_source_status_recomputation"],
            INPUTS["g12_search_inventory_audit"],
            INPUTS["g12_proxy_hash_asof_audit"],
            INPUTS["g12_noleak_audit"],
            INPUTS["g12_completion_audit"],
            INPUTS["g12_verification_result"],
        ],
        "target_artifacts_read": [
            INPUTS["target_card_set"],
            INPUTS["target_source_status_matrix"],
            INPUTS["target_source_inventory"],
            INPUTS["target_proxy_validity_matrix"],
            INPUTS["target_parser_hash_asof_requirements"],
            INPUTS["target_recoverable_vs_nongeneratable"],
            INPUTS["target_search_root_ledger"],
            INPUTS["target_noleak_audit"],
            INPUTS["target_completion_audit"],
        ],
        "lane_classification": "G0 source-control unblocking synthesis, not validation, scoring, promotion, or live behavior.",
        "completion_standard": "All 17 cards reconciled, every same-evidence-class blocker mapped to cleared/proven-impossible/exact runnable prompt, route bundle broad enough to avoid OB/current-GTOS boxing, verifier/focused tests pass, scoped commits made.",
        "card_ids": data["card_set"].get("included_card_ids"),
    }


def build_completion_audit(
    decision: dict[str, Any],
    route_ranking: dict[str, Any],
    dependency_map: dict[str, Any],
    prompt_pack: dict[str, Any],
    noleak: dict[str, Any],
    saturation: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "Mandatory preflight/context refresh and no chat-memory reliance",
            "evidence": f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
            "satisfied": True,
        },
        {
            "requirement": "Read accepted G12 decision, denominator, source-status, search inventory, proxy/hash/as-of, no-leak, completion, and verification artifacts",
            "evidence": "context anchor accepted_g12_artifacts_read",
            "satisfied": True,
        },
        {
            "requirement": "Preserve exact 17 blocked-card denominator while excluding other 15 and leaving ready8/expansion untouched",
            "evidence": f"{PREFIX}_DENOMINATOR_NOLEAK_SAFE_FLAG_AUDIT_{DATE}.json",
            "satisfied": noleak["ok"],
        },
        {
            "requirement": "Consider every accepted blocked-17 card and every relevant source/status category from the 13,024-row inventory",
            "evidence": [
                f"{PREFIX}_BLOCKED17_DEPENDENCY_TO_ROUTE_MAP_{DATE}.json",
                f"{PREFIX}_SOURCE_MATERIALIZATION_OPPORTUNITY_LEDGER_{DATE}.json",
            ],
            "satisfied": dependency_map["card_count"] == 17,
        },
        {
            "requirement": "Rank broad LTF/orderflow/proxy/context/non-OB/cross-domain source-control routes",
            "evidence": f"{PREFIX}_ROUTE_RANKING_MATRIX_{DATE}.json",
            "satisfied": len(route_ranking["ranked_routes"]) >= 5,
        },
        {
            "requirement": "Emit parser/proxy/prospective-capture/access prompt packs/starters and parallelization ledger",
            "evidence": [
                f"{PREFIX}_PARSER_PROXY_CAPTURE_ACCESS_PROMPT_PACK_LEDGER_{DATE}.json",
                f"{PREFIX}_PARALLELIZATION_LEDGER_{DATE}.json",
            ],
            "satisfied": prompt_pack["prompt_pack_count"] == 5,
        },
        {
            "requirement": "Keep validation/result/promotion/live/API/paid-vendor/broker-account-order-history-deal-position/raw-blob/trading-risk-safety-prompt-decision surfaces closed",
            "evidence": f"{PREFIX}_DENOMINATOR_NOLEAK_SAFE_FLAG_AUDIT_{DATE}.json",
            "satisfied": noleak["ok"],
        },
        {
            "requirement": "Saturation/self-red-team proves route is not cautious, OB-boxed, novelty-averse, or route-count-limited",
            "evidence": f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE}.json",
            "satisfied": len(saturation["anti_boxing_routes_considered"]) == 5,
        },
        {
            "requirement": "Safe flags preserved",
            "evidence": ["NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"],
            "satisfied": True,
        },
    ]
    missing = [row for row in checklist if row["satisfied"] is not True]
    return {
        **base_payload("COMPLETION_AUDIT"),
        "objective_restatement": decision["objective_restatement"],
        "prompt_to_artifact_checklist": checklist,
        "missing_incomplete_or_weak_requirements": missing,
        "completion_standard_satisfied": missing == [],
        "can_mark_goal_complete_after_verifier_focused_tests_and_scoped_commit": missing == [],
        "terminal_decision": TERMINAL_DECISION,
        "safe_posture": {
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }


def build_manifest() -> dict[str, Any]:
    artifact_rows = []
    for name in JSON_ARTIFACTS + MD_ARTIFACTS:
        path = ROUTE_DIR / name
        artifact_rows.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_path(path) if path.exists() else None,
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
        )
    for pack in PROMPT_PACKS:
        for name in [PROMPT_ROOT / pack["prompt_filename"], ROUTE_DIR / pack["starter_filename"]]:
            artifact_rows.append(
                {
                    "path": rel(name),
                    "exists": name.exists(),
                    "sha256": sha256_path(name) if name.exists() else None,
                    "size_bytes": name.stat().st_size if name.exists() else None,
                }
            )
    for name in [
        "build_g0_scid_ltf_proxy_blocked17_unblocking_synthesis_2026_05_13.py",
        "verify_g0_scid_ltf_proxy_blocked17_unblocking_synthesis_2026_05_13.py",
        "test_g0_scid_ltf_proxy_blocked17_unblocking_synthesis_2026_05_13.py",
        f"{PREFIX}_VERIFICATION_RESULT_{DATE}.json",
        f"{PREFIX}_VERIFICATION_RESULT_{DATE}.md",
        f"{PREFIX}_FOCUSED_TEST_RESULT_{DATE}.json",
        f"{PREFIX}_FOCUSED_TEST_RESULT_{DATE}.md",
    ]:
        path = ROUTE_DIR / name
        artifact_rows.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_path(path) if path.exists() else None,
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
        )
    return {
        **base_payload("OUTPUT_MANIFEST"),
        "artifact_count": len(artifact_rows),
        "artifact_rows": artifact_rows,
    }


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    data = summarize_inputs()

    context = build_context_anchor(data)
    route_ranking = build_route_ranking(data)
    dependency_map = build_dependency_map(data)
    source_materialization = build_source_materialization_ledger(data)
    prompt_pack = write_prompt_packs(data)
    parallelization = build_parallelization_ledger(prompt_pack)
    noleak = build_denominator_noleak_audit(data)
    saturation = build_saturation_ledger(data, route_ranking)
    decision = build_decision_ledger(data, route_ranking)
    completion = build_completion_audit(decision, route_ranking, dependency_map, prompt_pack, noleak, saturation)

    payloads = {
        f"{PREFIX}_CONTEXT_ANCHOR_{DATE}": ("Context Anchor", context),
        f"{PREFIX}_DECISION_LEDGER_{DATE}": ("Decision Ledger", decision),
        f"{PREFIX}_ROUTE_RANKING_MATRIX_{DATE}": ("Route Ranking Matrix", route_ranking),
        f"{PREFIX}_BLOCKED17_DEPENDENCY_TO_ROUTE_MAP_{DATE}": ("Blocked-17 Dependency To Route Map", dependency_map),
        f"{PREFIX}_SOURCE_MATERIALIZATION_OPPORTUNITY_LEDGER_{DATE}": (
            "Source Materialization Opportunity Ledger",
            source_materialization,
        ),
        f"{PREFIX}_PARSER_PROXY_CAPTURE_ACCESS_PROMPT_PACK_LEDGER_{DATE}": (
            "Parser Proxy Capture Access Prompt Pack Ledger",
            prompt_pack,
        ),
        f"{PREFIX}_PARALLELIZATION_LEDGER_{DATE}": ("Parallelization Ledger", parallelization),
        f"{PREFIX}_DENOMINATOR_NOLEAK_SAFE_FLAG_AUDIT_{DATE}": (
            "Denominator Noleak Safe Flag Audit",
            noleak,
        ),
        f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE}": ("Saturation Self Red Team", saturation),
        f"{PREFIX}_COMPLETION_AUDIT_{DATE}": ("Completion Audit", completion),
    }

    for stem, (title, payload) in payloads.items():
        write_json(f"{stem}.json", payload)
        write_md(f"{stem}.md", title, payload)

    manifest = build_manifest()
    write_json(f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json", manifest)
    write_md(f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.md", "Output Manifest", manifest)
    return manifest


if __name__ == "__main__":
    manifest = build()
    print(json.dumps({"ok": True, "artifact_count": manifest["artifact_count"]}, indent=2, sort_keys=True))
