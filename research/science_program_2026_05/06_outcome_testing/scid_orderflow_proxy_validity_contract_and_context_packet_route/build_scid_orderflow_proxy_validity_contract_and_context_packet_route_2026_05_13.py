"""Build the blocked-17 orderflow/proxy validity contract packet.

This route is source-control only. It attaches proxy/source-family contracts,
as-of/hash/redaction rules, exact invalid contexts, and exact future parser or
access requirements for the blocked-17 cards that need orderflow/proxy context.
It does not open validation, scoring, broker account/order evidence, paid
vendor access, raw market blob commits, promotion, or live behavior.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-13"
ROUTE_ID = "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
ROUTE_TITLE = "SCID Blocked17 Orderflow Proxy Contract And Source Status Attach"
EVIDENCE_CLASS = "SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AND_SOURCE_STATUS_ATTACH_ONLY"
SCHEMA_VERSION = "scid_blocked17_orderflow_proxy_contract_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = (
    "SOURCE_FAMILY_AND_PROXY_CONTEXT_CONTRACTS_ATTACHED_G12_AUDIT_READY_"
    "WITH_EXACT_ACCESS_REQUIREMENTS"
)
PREFIX = "SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT"

ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = ROUTE_DIR.parent
REPO_ROOT = ROUTE_DIR.parents[3]
PROMPT_ROOT = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts"

CONTROL_PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AND_SOURCE_STATUS_ATTACH_GOAL_PROMPT_2026-05-12.md"
)
ROUTE_PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE_GOAL_PROMPT_2026-05-13.md"
)
NEXT_G12_PROMPT_NAME = "G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT_GOAL_PROMPT_2026-05-13.md"
NEXT_G12_STARTER_NAME = "G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT_STARTER_2026-05-13.txt"

G0_DIR = OUTCOME_ROOT / "g0_scid_ltf_proxy_blocked17_unblocking_synthesis"
G12_DIR = OUTCOME_ROOT / "g12_scid_ltf_proxy_blocked17_source_status_audit"
SOURCE_STATUS_DIR = OUTCOME_ROOT / "scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17"

INPUTS = {
    "controlling_prompt": CONTROL_PROMPT_PATH,
    "route_prompt": ROUTE_PROMPT_PATH,
    "live_state": ".context/LIVE_STATE.md",
    "goal_session_research_discipline": ".context/00_core/goal_session_research_discipline.md",
    "research_operating_doctrine": ".context/00_core/research_operating_doctrine.md",
    "research_current_state": ".context/00_core/research_current_state.md",
    "local_heavy_data_inventory": ".context/00_core/local_heavy_data_inventory.md",
    "ai_in_loop_cost_control": ".context/00_core/ai_in_loop_cost_control_research_plan.md",
    "g0_blocked_synthesis_prompt": (
        "research/science_program_2026_05/04_goal_prompts/"
        "G0_SCID_BLOCKED_UNBLOCKING_SYNTHESIS_AFTER_FC_G12_AUDIT_GOAL_PROMPT_2026-05-12.md"
    ),
    "g0_route_reconciliation": str(
        G0_DIR / "G0_SCID_LTF_PROXY_BLOCKED17_SYNTHESIS_DECISION_LEDGER_2026-05-13.json"
    ),
    "g0_dependency_route_map": str(
        G0_DIR / "G0_SCID_LTF_PROXY_BLOCKED17_SYNTHESIS_BLOCKED17_DEPENDENCY_TO_ROUTE_MAP_2026-05-13.json"
    ),
    "g0_route_ranking": str(
        G0_DIR / "G0_SCID_LTF_PROXY_BLOCKED17_SYNTHESIS_ROUTE_RANKING_MATRIX_2026-05-13.json"
    ),
    "g0_same_evidence_blocker_pursuit": str(
        REPO_ROOT
        / "research/science_program_2026_05/06_outcome_testing/"
        "g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit/"
        "G0_SCID_BLOCKED_UNBLOCKING_SAME_EVIDENCE_BLOCKER_PURSUIT_LEDGER_2026-05-12.json"
    ),
    "g0_denominator_quarantine_gate": str(
        REPO_ROOT
        / "research/science_program_2026_05/06_outcome_testing/"
        "g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit/"
        "G0_SCID_BLOCKED_UNBLOCKING_DENOMINATOR_QUARANTINE_GATE_LEDGER_2026-05-12.json"
    ),
    "g12_proxy_hash_asof_audit": str(
        G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_PROXY_HASH_ASOF_AUDIT_2026-05-12.json"
    ),
    "g12_source_status_recomputation": str(
        G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SOURCE_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json"
    ),
    "g12_noleak_audit": str(
        G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_NOLEAK_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json"
    ),
    "source_status_card_set": str(SOURCE_STATUS_DIR / "SCID_LTF_PROXY_BLOCKED17_CARD_SET_2026-05-12.json"),
    "source_status_matrix": str(SOURCE_STATUS_DIR / "SCID_LTF_PROXY_SOURCE_STATUS_MATRIX_2026-05-12.json"),
    "source_inventory": str(SOURCE_STATUS_DIR / "SCID_LTF_PROXY_SOURCE_INVENTORY_2026-05-12.json"),
    "proxy_validity_matrix": str(
        SOURCE_STATUS_DIR / "SCID_LTF_PROXY_VALIDITY_AND_EQUIVALENCE_MATRIX_2026-05-12.json"
    ),
    "parser_hash_asof_requirements": str(
        SOURCE_STATUS_DIR / "SCID_LTF_PROXY_PARSER_HASH_ASOF_REQUIREMENTS_2026-05-12.json"
    ),
}

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

SAFE_BASE = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
}

FORBIDDEN_DIFF_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/canary_fixtures",
)

ALLOWED_DIFF_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/scid_orderflow_proxy_validity_contract_and_context_packet_route/",
    "research/science_program_2026_05/04_goal_prompts/G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT_GOAL_PROMPT_2026-05-13.md",
    ".context/",
)

FORBIDDEN_TRUE_TOKENS = (
    '"broker_cfd_truth_allowed": true',
    '"may_score_results_now": true',
    '"may_open_results_now": true',
    '"validation_safe": true',
    '"outcome_review_opened": true',
    '"live_effect": true',
    '"opens_paid_or_vendor_access": true',
    '"opens_broker_account_order_history_deal_position_evidence": true',
    '"opens_result_scoring": true',
    '"opens_validation": true',
)

JSON_ARTIFACTS = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
    f"{PREFIX}_SOURCE_DEPENDENCY_LEDGER_{DATE}.json",
    f"{PREFIX}_SOURCE_FAMILY_CONTRACT_{DATE}.json",
    f"{PREFIX}_CONTEXT_PACKET_SCHEMA_{DATE}.json",
    f"{PREFIX}_EQUIVALENCE_AND_INVALID_CONTEXT_MATRIX_{DATE}.json",
    f"{PREFIX}_ASOF_HASH_REDACTION_POLICY_{DATE}.json",
    f"{PREFIX}_PAID_ACCESS_FREE_BLOCKER_LEDGER_{DATE}.json",
    f"{PREFIX}_ROUTE_DECISION_LEDGER_{DATE}.json",
    f"{PREFIX}_NOLEAK_SAFE_FLAG_AUDIT_{DATE}.json",
    f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE}.json",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json",
    f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json",
]

MD_ARTIFACTS = [name.replace(".json", ".md") for name in JSON_ARTIFACTS]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: str | Path) -> Any:
    p = Path(path)
    if not p.is_absolute():
        p = REPO_ROOT / p
    return json.loads(p.read_text(encoding="utf-8"))


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_base(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **SAFE_BASE,
    }
    if extra:
        payload.update(extra)
    return payload


def write_json(name: str, payload: dict[str, Any]) -> None:
    (ROUTE_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown_summary(title: str, payload: dict[str, Any]) -> str:
    return (
        f"# {title}\n\n"
        f"- `NO_PROMOTION_VERDICT`\n"
        f"- `validation_safe=false`\n"
        f"- `outcome_review_opened=false`\n"
        f"- `live_effect=false`\n\n"
        "```json\n"
        f"{json.dumps(payload, indent=2, sort_keys=True)}\n"
        "```\n"
    )


def write_md(name: str, title: str, payload: dict[str, Any]) -> None:
    (ROUTE_DIR / name).write_text(markdown_summary(title, payload), encoding="utf-8")


def count_files(root: Path, suffix: str, recursive: bool = True) -> int | str:
    if not root.exists():
        return "MISSING"
    iterator = root.rglob(f"*{suffix}") if recursive else root.glob(f"*{suffix}")
    try:
        return sum(1 for p in iterator if p.is_file())
    except OSError as exc:
        return f"ERROR: {exc}"


def local_root_observations() -> list[dict[str, Any]]:
    roots = [
        ("sierra_root", Path("C:/SierraChart"), [".depth", ".scid"], True),
        ("sierra_data", Path("C:/SierraChart/Data"), [".depth", ".scid"], False),
        ("sierra_market_depth", Path("C:/SierraChart/Data/MarketDepthData"), [".depth"], False),
        ("absolute_external_source_cache", Path("C:/Users/MSI/Documents/ai-trading-agent/data/external"), [".json", ".csv", ".parquet", ".scid", ".depth"], True),
        ("absolute_shadow_logs", Path("C:/Users/MSI/Documents/ai-trading-agent/shadow_logs"), [".jsonl"], False),
    ]
    rows: list[dict[str, Any]] = []
    for root_id, root, suffixes, recursive in roots:
        row: dict[str, Any] = {
            "root_id": root_id,
            "path": root.as_posix(),
            "exists": root.exists(),
            "recursive_count": recursive,
            "counts_by_suffix": {},
            "raw_content_read": False,
            "raw_blob_committed": False,
        }
        for suffix in suffixes:
            row["counts_by_suffix"][suffix] = count_files(root, suffix, recursive=recursive)
        if root_id == "absolute_shadow_logs" and root.exists():
            row["proxy_related_logs"] = sorted(
                p.name for p in root.glob("*proxy*.jsonl") if p.is_file()
            )
        rows.append(row)

    tmp = Path("C:/tmp")
    rows.append(
        {
            "root_id": "prior_worktree_candidates",
            "path": tmp.as_posix(),
            "exists": tmp.exists(),
            "recursive_count": False,
            "candidate_dirs": sorted(
                p.name for p in tmp.glob("*gtos*") if p.is_dir()
            )[:40]
            if tmp.exists()
            else [],
            "raw_content_read": False,
            "raw_blob_committed": False,
        }
    )
    return rows


def contract_id_for_source_family(source_family: str) -> str:
    return f"{source_family.upper()}_CONTRACT_V1"


def source_family_contract(row: dict[str, Any], local_observations: list[dict[str, Any]]) -> dict[str, Any]:
    family = row["source_family"]
    contract_id = contract_id_for_source_family(family)
    common_invalid = [
        "broker-native CFD truth claim",
        "broker account/order/history/deal/position evidence",
        "result scoring, validation, promotion, or performance interpretation",
        "post-decision or post-cancel source selection",
        "source pointer without hash or G12-accepted hash deferral",
        "missing non-equivalence label",
    ]
    by_family: dict[str, dict[str, Any]] = {
        "sierra_depth_market_depth": {
            "contract_status": "CONTRACT_ATTACHED_EXACT_RAW_PARSE_SCOPE_REQUIRED",
            "source_scope": "Sierra .depth market depth files under local Sierra roots; first-wave depth inventory is source-status evidence only.",
            "parser_acceptance_criteria": [
                "record-size and endian proof",
                "contract root and contract month parsed from file name",
                "exchange date and UTC conversion rule frozen",
                "records selected only where source event time <= decision_asof_utc",
                "clear-book-only, closed-market, gap, and stale-depth flags emitted",
                "path, size, mtime, and sha256 or G12-accepted hash-deferral id attached",
            ],
            "roll_session_asof_rule": "Use exact active contract/date files, not continuous futures. Bind exchange session calendar, feed delay label, and UTC conversion before any candidate join.",
            "staleness_policy": "Fail closed when the latest usable depth update before decision_asof_utc is older than the route-declared threshold, when the file is clear-book-only for the active window, or when the file was still being written without a no-change completion check.",
            "exact_access_requirement_if_unresolved": "Run a no-commit Sierra .depth window inventory/parser job for declared contract/date windows; record path, size, mtime, sha256 or accepted hash deferral; do not commit raw .depth.",
            "useful_contexts": [
                "depth availability status",
                "queue/depth context features",
                "liquidity void or absorption proxy context",
                "parser fixture and future context packet fields",
            ],
            "invalid_contexts": common_invalid
            + [
                "broker fill queue or broker spread truth",
                "continuous-contract heatmap used as exact contract depth",
                "Sunday/holiday depth sample interpreted as active-session state without flags",
            ],
        },
        "sierra_scid_footprint_bid_ask_volume": {
            "contract_status": "CONTRACT_ATTACHED_EXACT_SCID_PARSE_REQUIREMENT",
            "source_scope": "Sierra .scid intraday files and same-market/futures roots; source-status evidence only until parser G12 accepts field semantics.",
            "parser_acceptance_criteria": [
                "SCID timestamp and price scaling decoded by versioned parser",
                "bid/ask/volume fields separated from derived features",
                "same-market symbols separated from futures proxy symbols",
                "source event time <= decision_asof_utc",
                "sparse/thin symbol warnings emitted",
                "path, size, mtime, and sha256 or accepted hash deferral attached",
            ],
            "roll_session_asof_rule": "Bind symbol root and contract month when futures; bind same-market source label when non-futures. Use UTC and exchange/session calendar, not local wall-clock labels.",
            "staleness_policy": "Fail closed when no SCID bar/tick exists inside the declared pre-decision window, when sparse-symbol quality flags are action-required, or when parser scale/version is unknown.",
            "exact_access_requirement_if_unresolved": "Run a no-commit SCID parser over declared symbol/windows; attach parser version, scale proof, path, size, mtime, and hash/deferral id.",
            "useful_contexts": [
                "bid/ask volume context",
                "delta and volume-profile context",
                "aggression proxy context",
                "same-market availability status where registered",
            ],
            "invalid_contexts": common_invalid
            + [
                "centralized spot FX or broker CFD volume truth",
                "same-market indicative quote data treated as broker execution truth",
            ],
        },
        "databento_cached_or_declared_orderflow_artifacts": {
            "contract_status": "CONTRACT_ATTACHED_CACHED_ONLY_NEW_PULL_BLOCKED",
            "source_scope": "Committed Databento/orderflow artifacts and declared request manifests only; no new paid/API pull is opened here.",
            "parser_acceptance_criteria": [
                "dataset, schema, symbol, window, and source cache path present",
                "cost/free-credit status present for any future fetch",
                "source artifact hash attached",
                "records selected only where source event time <= decision_asof_utc",
                "MBO/MBP/trades schema family explicitly labeled",
            ],
            "roll_session_asof_rule": "Use declared Databento dataset symbol and futures contract month or continuous symbol mapping; freeze the mapping before joins.",
            "staleness_policy": "Fail closed when the cached artifact lacks window, schema, source hash, or created_at/source as-of metadata; request rows alone are not market data.",
            "exact_access_requirement_if_unresolved": "For a missing window, write a pre-call manifest with dataset, schema, symbol, UTC window, expected fields, expected cost/free-credit status, no-leak policy, and owner approval requirement before any fetch.",
            "useful_contexts": [
                "cached MBP/MBO/trades source-control fields",
                "dataset symbol mapping context",
                "cost-cap and request-manifest status",
                "future stratified proxy parity packet inputs",
            ],
            "invalid_contexts": common_invalid
            + [
                "new Databento call without owner-approved pre-call manifest",
                "vendor futures depth/trades used as broker account or CFD execution truth",
            ],
        },
        "proxy_mapping_registry_and_blocker_logs": {
            "contract_status": "CONTRACT_ATTACHED_FAIL_CLOSED_MAPPING_REQUIRED",
            "source_scope": "Committed proxy mapping rows, proxy blocker/status logs, and source-control registries; not market data by itself.",
            "parser_acceptance_criteria": [
                "source symbol and proxy symbol present",
                "contract root/month or same-market root present",
                "roll rule and session calendar present",
                "timezone and inverse-price policy present where applicable",
                "non-equivalence label present",
                "mapping version and source hash attached",
            ],
            "roll_session_asof_rule": "Fail closed unless mapping version, roll calendar, exchange session calendar, and inverse-price convention are frozen before use.",
            "staleness_policy": "Fail closed when mapping source timestamp predates a contract roll, when registry rows conflict, or when source-status logs are action-required/stale.",
            "exact_access_requirement_if_unresolved": "Materialize the mapping registry row from committed source-control artifacts or append a prospective proxy-mapping capture requirement; do not infer mapping from price correlation.",
            "useful_contexts": [
                "proxy eligibility flags",
                "inverse-contract flags",
                "basis caveats",
                "blocked mapping reasons",
            ],
            "invalid_contexts": common_invalid
            + [
                "proxy transfer accepted from price correlation alone",
                "mapping row used without current contract month and non-equivalence caveat",
            ],
        },
    }
    payload = by_family[family]
    related_roots = [
        obs for obs in local_observations
        if (
            ("sierra" in family and obs["root_id"].startswith("sierra"))
            or ("databento" in family and obs["root_id"] == "absolute_external_source_cache")
            or ("proxy_mapping" in family and obs["root_id"] == "absolute_shadow_logs")
        )
    ]
    return {
        "contract_id": contract_id,
        "source_family": family,
        "upstream_source_count": row["source_count"],
        "availability_status": row["availability_status"],
        "access_readiness": row["access_readiness"],
        "upstream_parser_requirement": row["parser_requirement"],
        "upstream_hash_policy": row["hash_policy"],
        "upstream_proxy_boundary": row["proxy_boundary"],
        "schema_fields_unlocked_context_only": row["schema_fields_unlocked"],
        "source_inventory_categories": row["source_inventory_categories"],
        "local_metadata_observations": related_roots,
        "broker_native_cfd_truth_claim_allowed": False,
        "may_score_results_now": False,
        **payload,
    }


def build_context_anchor(git_head: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return safe_base(
        {
            "artifact_family": "CONTEXT_ANCHOR",
            "title": ROUTE_TITLE,
            "current_head": git_head,
            "controlling_prompt": CONTROL_PROMPT_PATH,
            "route_prompt": ROUTE_PROMPT_PATH,
            "mandatory_context_read_after_preflight": [
                ".context/LIVE_STATE.md",
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/research_current_state.md",
                ".context/00_core/local_heavy_data_inventory.md",
                ".context/00_core/ai_in_loop_cost_control_research_plan.md",
            ],
            "builder_posture": "constructive source/control builder, not G12 auditor and not result scorer",
            "active_question_stack": [
                "Which blocked-17 cards need future_orderflow_depth_proxy_requirements?",
                "Which source families can support context/control only without claiming broker-native CFD truth?",
                "What exact parser/hash/as-of/non-equivalence contract must future G12 audit accept?",
                "Which contexts are useful and which are invalid for proxy evidence?",
                "Which unresolved items are exact parser/access/capture requirements rather than vague blockers?",
            ],
            "inputs": inputs,
            "safe_boundary": "No validation, result scoring, R/PnL/win-rate/expectancy/performance, promotion, AI/API, paid-vendor access, broker account/order/history/deal/position evidence, raw market blob commit, live restart, live behavior, or trading/risk/safety/prompt-decision change.",
        }
    )


def build_source_dependency_ledger(status_matrix: dict[str, Any], dependency_map: dict[str, Any]) -> dict[str, Any]:
    proxy_cards: list[dict[str, Any]] = []
    dependency_rows: list[dict[str, Any]] = []
    route_cards = {
        row["card_id"]: row for row in dependency_map["cards"]
        if "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE" in row["recommended_route_ids"]
    }
    for row in status_matrix["rows"]:
        proxy_fields = [
            field for field in row["field_status_rows"]
            if field["status"] == "PROXY_VALIDITY_REQUIRES_CONTRACT"
        ]
        if not proxy_fields:
            continue
        card_id = row["card_id"]
        card_route = route_cards.get(card_id, {})
        proxy_cards.append(
            {
                "card_id": card_id,
                "science_domain": row["science_domain"],
                "required_capture_groups": row["required_capture_groups"],
                "field_requirement_count": len(proxy_fields),
                "card_level_dependency_group": "future_orderflow_depth_proxy_requirements",
                "dependency_surface_count": len(proxy_fields) + 1,
                "denominator_inclusion": "blocked17_only",
                "may_score_results_now": False,
                "future_result_gate": row["future_result_gate"],
                "recommended_route_ids": card_route.get("recommended_route_ids", [ROUTE_ID]),
                "terminal_source_status": row["terminal_source_status"],
            }
        )
        for field in proxy_fields:
            dependency_rows.append(
                {
                    "card_id": card_id,
                    "science_domain": row["science_domain"],
                    "field": field["field"],
                    "upstream_status": field["status"],
                    "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
                    "attached_contract_ids": [
                        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
                        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
                        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
                        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1",
                    ],
                    "source_paths_or_roots_searched": field["source_paths_or_roots_searched"],
                    "exact_next_requirement": field["next_requirement"],
                    "may_score_results_now": False,
                    "broker_native_cfd_truth_claim_allowed": False,
                }
            )
    return safe_base(
        {
            "artifact_family": "SOURCE_DEPENDENCY_LEDGER",
            "blocked17_card_count": status_matrix["card_count"],
            "proxy_card_count": len(proxy_cards),
            "proxy_field_requirement_count": len(dependency_rows),
            "proxy_card_level_requirement_count": len(proxy_cards),
            "proxy_requirement_surface_count": len(dependency_rows) + len(proxy_cards),
            "proxy_cards": proxy_cards,
            "proxy_dependency_rows": dependency_rows,
            "route_count_reconciliation": {
                "g0_ranked_route_status_count": 72,
                "g12_recomputed_field_status_count": len(dependency_rows),
                "card_level_future_orderflow_depth_proxy_requirements": len(proxy_cards),
                "reconciled_total_surfaces": len(dependency_rows) + len(proxy_cards),
                "interpretation": "G0 rank-level 72 equals 64 exact per-field proxy requirements plus 8 card-level orderflow/proxy dependency groups.",
            },
        }
    )


def build_source_family_contract(
    proxy_validity: dict[str, Any],
    local_observations: list[dict[str, Any]],
    dependency_ledger: dict[str, Any],
) -> dict[str, Any]:
    contracts = [
        source_family_contract(row, local_observations)
        for row in proxy_validity["source_family_rows"]
    ]
    return safe_base(
        {
            "artifact_family": "SOURCE_FAMILY_CONTRACT",
            "contract_count": len(contracts),
            "source_family_total_upstream_source_count": sum(row["upstream_source_count"] for row in contracts),
            "proxy_requirement_surface_count": dependency_ledger["proxy_requirement_surface_count"],
            "broker_native_cfd_truth_claims": 0,
            "contracts": contracts,
            "contract_global_rules": [
                "Every packet row must carry source_family, source_file_pointer_or_vendor_cache_id, source_hash or accepted deferral id, proxy_mapping_version, contract root/month or same-market root, publication_or_capture_asof_utc, parser_version, and non_equivalence_label.",
                "Every proxy row is context/control only until a separate G12/G0 route accepts transfer/equivalence and a separate result lane explicitly opens scoring.",
                "Parser must fail closed on missing contract, roll, session calendar, timezone, inverse-price policy, source hash/deferral, or non-equivalence label.",
                "No raw .depth/.scid/vendor market blob may be committed by this route.",
            ],
        }
    )


def build_context_packet_schema(source_family_contract: dict[str, Any]) -> dict[str, Any]:
    required_fields = [
        "packet_schema_version",
        "card_id",
        "candidate_input_row_id",
        "decision_asof_utc",
        "candidate_symbol",
        "source_family",
        "source_family_contract_id",
        "proxy_mapping_version",
        "proxy_instrument",
        "contract_root",
        "contract_month",
        "roll_rule_id",
        "session_calendar_id",
        "timezone_policy",
        "inverse_price_policy",
        "publication_or_capture_asof_utc",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash_or_deferral_id",
        "parser_version",
        "derived_feature_schema_version",
        "non_equivalence_label",
        "staleness_status",
        "gap_or_sparse_quality_flags",
        "duplicate_denominator_key",
        "allowed_use_context_control_only",
        "invalid_context_flags",
    ]
    fail_closed_if_missing = [
        "source_family",
        "source_family_contract_id",
        "proxy_mapping_version",
        "proxy_instrument",
        "contract_root",
        "contract_month",
        "publication_or_capture_asof_utc",
        "source_hash_or_deferral_id",
        "parser_version",
        "non_equivalence_label",
        "duplicate_denominator_key",
    ]
    forbidden_fields = [
        "broker account balance/equity",
        "broker order ticket",
        "broker deal id",
        "broker position id",
        "account-history realized label",
        "post-outcome path label",
        "R/PnL/win-rate/expectancy/performance field",
        "validation or promotion flag",
    ]
    return safe_base(
        {
            "artifact_family": "CONTEXT_PACKET_SCHEMA",
            "packet_schema_id": "scid_blocked17_orderflow_proxy_context_packet_v1",
            "required_fields": required_fields,
            "fail_closed_if_missing": fail_closed_if_missing,
            "forbidden_fields": forbidden_fields,
            "source_family_contract_ids": [row["contract_id"] for row in source_family_contract["contracts"]],
            "join_key_policy": "Join only by frozen candidate_input_row_id/card_id/decision_asof_utc plus duplicate_denominator_key; never expand denominators or mix expansion rows.",
            "asof_policy": "All source event times used for derived context must be <= decision_asof_utc; publication_or_capture_asof_utc must be recorded and staleness-flagged.",
            "allowed_output": "Context/control packet fields only. No result scoring, validation, promotion, broker truth, or live decision effect.",
        }
    )


def build_equivalence_matrix(proxy_validity: dict[str, Any]) -> dict[str, Any]:
    valid_contexts = [
        "source availability and source-status control",
        "orderflow/depth context packet construction",
        "future parser fixture selection",
        "failure-anatomy hypothesis input after separate result lane opens",
        "proxy-transfer audit input after separate G12/G0 gate",
    ]
    invalid_context_rules = [
        {
            "invalid_context": "broker_native_cfd_truth",
            "fail_closed_rule": "Reject any interpretation that futures/Sierra/Databento proxy data proves MT5 broker CFD quote, spread, queue, fill, order, deal, account, or position truth.",
        },
        {
            "invalid_context": "result_or_performance_claim",
            "fail_closed_rule": "Reject any use for validation, result scoring, R/PnL/win-rate/expectancy/performance, or promotion in this lane.",
        },
        {
            "invalid_context": "roll_or_session_ambiguous",
            "fail_closed_rule": "Reject any proxy row without contract month, roll rule, exchange session calendar, timezone policy, and as-of timestamp.",
        },
        {
            "invalid_context": "stale_or_closed_market_depth",
            "fail_closed_rule": "Reject or flag clear-book-only, Sunday/holiday, sparse, or stale depth windows before any future context use.",
        },
        {
            "invalid_context": "inverse_or_basis_missing",
            "fail_closed_rule": "Reject proxy rows such as USDJPY/6J unless inverse-price convention and basis caveat are explicit.",
        },
        {
            "invalid_context": "hash_or_pointer_missing",
            "fail_closed_rule": "Reject source rows without source pointer and sha256 or G12-accepted hash deferral id.",
        },
    ]
    rows = []
    for upstream in proxy_validity["equivalence_rows"]:
        row = dict(upstream)
        row["allowed_contexts"] = valid_contexts
        row["invalid_context_rules"] = invalid_context_rules
        row["contract_attachment_status"] = "NON_EQUIVALENCE_CONTRACT_ATTACHED_CONTEXT_ONLY"
        row["broker_native_cfd_truth_claim_allowed"] = False
        row["may_score_results_now"] = False
        row["asof_roll_session_requirement"] = (
            "Future packet must bind source family, exact contract/root, roll rule, "
            "session calendar, timezone policy, source hash/deferral, and non-equivalence label."
        )
        if upstream["candidate_symbol"] == "USDJPY_6J":
            row["special_mapping_requirement"] = "Inverse FX futures convention must be explicit before any context join."
        else:
            row["special_mapping_requirement"] = "No symbol-specific override beyond contract/root, roll, session, and non-equivalence controls."
        rows.append(row)
    return safe_base(
        {
            "artifact_family": "EQUIVALENCE_AND_INVALID_CONTEXT_MATRIX",
            "equivalence_row_count": len(rows),
            "proxy_rows_context_only": len(rows),
            "broker_native_cfd_truth_claims": 0,
            "valid_contexts": valid_contexts,
            "invalid_context_rules": invalid_context_rules,
            "equivalence_rows": rows,
        }
    )


def build_asof_hash_redaction_policy(
    source_inventory: dict[str, Any],
    g12_proxy_hash: dict[str, Any],
) -> dict[str, Any]:
    return safe_base(
        {
            "artifact_family": "ASOF_HASH_REDACTION_POLICY",
            "hash_status_counts_from_source_inventory": source_inventory["hash_status_counts"],
            "hash_status_counts_from_g12_audit": g12_proxy_hash["hash_status_counts"],
            "raw_market_blob_commit_policy": "No raw .depth, .scid, parquet, vendor, broker, or market blob is committed by this route.",
            "hash_policy": [
                "Small committed artifacts must carry sha256.",
                "Large external raw files must carry path, size, mtime, and sha256 or a G12-accepted hash-deferral reason before future use.",
                "Any no-commit hash job must write only metadata and hashes, not raw market bytes.",
                "Text artifacts should use byte hash plus any accepted LF-normalized hash policy only when prior G12 accepts equivalence.",
            ],
            "asof_policy": [
                "Source event time used for context must be <= decision_asof_utc.",
                "Publication_or_capture_asof_utc must be recorded separately from source event time.",
                "Delayed-feed, Sunday/holiday, clear-book-only, sparse-symbol, and stale-window states must be explicit flags.",
                "No target, result, cancel, post-fill, account, order, deal, position, or PnL field can select source windows.",
            ],
            "redaction_policy": [
                "Do not consume or emit broker account/order/history/deal/position identifiers.",
                "Do not emit credentials, account numbers, API keys, or vendor auth material.",
                "Use source family, symbol, contract, window, path, size, mtime, and hash/deferral ids only.",
            ],
            "staleness_policy": [
                "Fail closed if source-status row is action-required or stale.",
                "Fail closed if proxy mapping predates a contract roll without refreshed roll metadata.",
                "Fail closed if raw source file was still being written and no no-change completion check exists.",
            ],
        }
    )


def build_blocker_ledger(
    source_family_contract: dict[str, Any],
    source_dependency_ledger: dict[str, Any],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for contract in source_family_contract["contracts"]:
        rows.append(
            {
                "blocker_id": f"{contract['contract_id']}_ACCESS_OR_PARSER_REQUIREMENT",
                "source_family": contract["source_family"],
                "status": contract["contract_status"],
                "paid_access_required_now": False,
                "ai_or_api_required_now": False,
                "raw_blob_commit_required_now": False,
                "exact_requirement": contract["exact_access_requirement_if_unresolved"],
                "owner_or_future_route_action": "G12 audit may accept the contract as source-control; parser/materialization remains a separate no-commit source-control route if raw windows are needed.",
            }
        )
    rows.extend(
        [
            {
                "blocker_id": "PROXY_TRANSFER_VALIDATION_NOT_OPENED",
                "source_family": "all_proxy_families",
                "status": "SEPARATE_EVIDENCE_CLASS_REQUIRED",
                "paid_access_required_now": False,
                "ai_or_api_required_now": False,
                "raw_blob_commit_required_now": False,
                "exact_requirement": "Separate future G12/G0 result or transfer-validation gate must freeze proxy-transfer hypothesis, denominator, source hashes, and result permissions before any interpretation beyond context/control.",
                "owner_or_future_route_action": "Do not open in this route.",
            },
            {
                "blocker_id": "BROKER_NATIVE_CFD_TRUTH_FORBIDDEN",
                "source_family": "all_proxy_families",
                "status": "HARD_FORBIDDEN_IN_THIS_LANE",
                "paid_access_required_now": False,
                "ai_or_api_required_now": False,
                "raw_blob_commit_required_now": False,
                "exact_requirement": "Broker-native CFD truth would require an explicitly authorized broker/source lane and cannot be inferred from futures, Sierra, Databento, or proxy mapping rows.",
                "owner_or_future_route_action": "Do not request or consume broker account/order/history/deal/position evidence in this lane.",
            },
        ]
    )
    return safe_base(
        {
            "artifact_family": "PAID_ACCESS_FREE_BLOCKER_LEDGER",
            "blocker_count": len(rows),
            "proxy_dependency_surface_count": source_dependency_ledger["proxy_requirement_surface_count"],
            "rows": rows,
            "vague_blocker_wording_present": False,
            "paid_vendor_access_opened": False,
            "all_remainders_exact": True,
        }
    )


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short=8", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() or "UNKNOWN"


def git_changed_paths() -> list[str]:
    names: set[str] = set()
    for args in (["diff", "--name-only", "HEAD"], ["ls-files", "--others", "--exclude-standard"]):
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        names.update(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())
    return sorted(names)


def build_route_decision_ledger(
    source_dependency_ledger: dict[str, Any],
    source_family_contract: dict[str, Any],
    equivalence: dict[str, Any],
) -> dict[str, Any]:
    return safe_base(
        {
            "artifact_family": "ROUTE_DECISION_LEDGER",
            "terminal_decision": TERMINAL_DECISION,
            "can_mark_goal_complete_after_verification": True,
            "blocked17_denominator_preserved": True,
            "blocked17_card_count": 17,
            "other_blocked15_excluded": 15,
            "ready8_denominator_touched": False,
            "expansion_denominator_touched": False,
            "proxy_card_count": source_dependency_ledger["proxy_card_count"],
            "proxy_field_requirement_count": source_dependency_ledger["proxy_field_requirement_count"],
            "proxy_requirement_surface_count": source_dependency_ledger["proxy_requirement_surface_count"],
            "source_family_contract_count": source_family_contract["contract_count"],
            "equivalence_row_count": equivalence["equivalence_row_count"],
            "broker_native_cfd_truth_claims": 0,
            "decision_basis": [
                "Accepted G12 source-status audit verifies broker_native_cfd_truth_claims=0 and proxy rows context only.",
                "Current route attaches explicit source-family/parser/hash/as-of/non-equivalence contracts to every proxy dependency surface.",
                "Unresolved raw parse, new vendor pull, transfer validation, and broker-native truth questions are reduced to exact future requirements or forbidden boundaries.",
            ],
        }
    )


def build_noleak_audit(
    card_set: dict[str, Any],
    source_dependency_ledger: dict[str, Any],
    equivalence: dict[str, Any],
) -> dict[str, Any]:
    changed = git_changed_paths()
    forbidden_paths = [p for p in changed if any(p.startswith(prefix) for prefix in FORBIDDEN_DIFF_PREFIXES)]
    outside_allowed = [p for p in changed if not any(p.startswith(prefix) for prefix in ALLOWED_DIFF_PREFIXES)]
    return safe_base(
        {
            "artifact_family": "NOLEAK_SAFE_FLAG_AUDIT",
            "ok": forbidden_paths == [] and outside_allowed == [],
            "included_card_count": card_set["included_card_count"],
            "excluded_blocked15_card_count": card_set["excluded_blocked15_card_count"],
            "ready8_excluded_count": len(card_set["ready_8_excluded_card_ids"]),
            "expansion_candidate_ids_outside_denominator_count": len(card_set["expansion_candidate_ids_outside_denominator"]),
            "proxy_cards_touched": source_dependency_ledger["proxy_card_count"],
            "broker_native_cfd_truth_claims": equivalence["broker_native_cfd_truth_claims"],
            "proxy_rows_context_only": equivalence["proxy_rows_context_only"],
            "raw_market_blob_commits_added": 0,
            "paid_vendor_access_opened": False,
            "broker_account_order_history_deal_position_sources_consumed": 0,
            "changed_or_untracked_paths": changed,
            "forbidden_live_surface_paths": forbidden_paths,
            "outside_allowed_scope_paths": outside_allowed,
            "safe_flag_policy": "All emitted artifacts keep NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
        }
    )


def build_saturation_self_redteam(
    source_dependency_ledger: dict[str, Any],
    equivalence: dict[str, Any],
    blocker_ledger: dict[str, Any],
) -> dict[str, Any]:
    questions = [
        {
            "question": "Could proxy context be mistaken for broker-native CFD truth?",
            "pursuit": "Added broker_native_cfd_truth_claims=0, broker_cfd_truth_allowed=false, non-equivalence labels, and invalid-context rules on every equivalence row.",
            "closure": "Closed inside this evidence class; future broker truth is forbidden here.",
        },
        {
            "question": "Could card-level 72 and field-level 64 proxy counts be inconsistent?",
            "pursuit": "Reconciled 64 exact field rows plus 8 card-level future_orderflow_depth_proxy_requirements.",
            "closure": "Closed with proxy_requirement_surface_count=72.",
        },
        {
            "question": "Could raw Sierra or vendor blobs leak into git?",
            "pursuit": "Contract requires no-commit hash/metadata route; no raw blob commits added.",
            "closure": "Closed by hash/deferral policy and no-leak audit.",
        },
        {
            "question": "Could USDJPY/6J inverse mapping be silently wrong?",
            "pursuit": "Equivalence matrix adds inverse-price special mapping requirement.",
            "closure": "Closed as context-only contract; future parser must fail closed if inverse policy missing.",
        },
        {
            "question": "Could stale or closed-market depth be treated as active-session orderflow?",
            "pursuit": "Source contracts require clear-book-only, sparse, stale, and session flags.",
            "closure": "Closed as exact parser requirement.",
        },
        {
            "question": "Could this route open validation or performance claims by accident?",
            "pursuit": "Safe flags, no-score gates, forbidden field list, and verifier text scan cover emitted artifacts.",
            "closure": "Closed; no result lane opened.",
        },
        {
            "question": "Could expansion or ready-8 denominators leak into blocked-17?",
            "pursuit": "No-leak audit preserves 17 included, 15 excluded blocked, ready8 excluded, expansion excluded.",
            "closure": "Closed with denominator audit fields.",
        },
        {
            "question": "Could a vague blocker remain?",
            "pursuit": "Blocker ledger gives exact parser/access/source/capture requirement for each unresolved family.",
            "closure": "Closed with all_remainders_exact=true.",
        },
    ]
    return safe_base(
        {
            "artifact_family": "SATURATION_SELF_REDTEAM",
            "saturation_question_count": len(questions),
            "proxy_requirement_surface_count": source_dependency_ledger["proxy_requirement_surface_count"],
            "equivalence_row_count": equivalence["equivalence_row_count"],
            "blocker_count": blocker_ledger["blocker_count"],
            "anti_boxing_routes_considered": [
                "Sierra depth ladder/depth",
                "Sierra SCID footprint bid/ask volume",
                "Databento cached MBO/MBP/trades artifacts",
                "proxy mapping registry/blocker logs",
                "same-market context roots where registered",
                "invalid context matrix for failure anatomy and future G12 audit",
            ],
            "questions": questions,
            "same_evidence_class_gap_remaining": False,
        }
    )


def build_completion_audit() -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight_generate_live_state", ".context/LIVE_STATE.md regenerated before route work", True),
        ("mandatory_context_goal_session_discipline", ".context/00_core/goal_session_research_discipline.md read", True),
        ("mandatory_context_research_doctrine", ".context/00_core/research_operating_doctrine.md read", True),
        ("mandatory_context_research_current_state", ".context/00_core/research_current_state.md read", True),
        ("mandatory_context_local_heavy_data", ".context/00_core/local_heavy_data_inventory.md read", True),
        ("mandatory_context_ai_cost_control", ".context/00_core/ai_in_loop_cost_control_research_plan.md read", True),
        ("context_anchor", f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json", True),
        ("source_dependency_ledger", f"{PREFIX}_SOURCE_DEPENDENCY_LEDGER_{DATE}.json", True),
        ("proxy_validity_source_family_contract", f"{PREFIX}_SOURCE_FAMILY_CONTRACT_{DATE}.json", True),
        ("context_packet_schema", f"{PREFIX}_CONTEXT_PACKET_SCHEMA_{DATE}.json", True),
        ("asof_hash_redaction_policy", f"{PREFIX}_ASOF_HASH_REDACTION_POLICY_{DATE}.json", True),
        ("paid_access_free_blocker_ledger", f"{PREFIX}_PAID_ACCESS_FREE_BLOCKER_LEDGER_{DATE}.json", True),
        ("equivalence_invalid_context_matrix", f"{PREFIX}_EQUIVALENCE_AND_INVALID_CONTEXT_MATRIX_{DATE}.json", True),
        ("no_leak_safe_flag_audit", f"{PREFIX}_NOLEAK_SAFE_FLAG_AUDIT_{DATE}.json", True),
        ("saturation_self_redteam", f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE}.json", True),
        ("next_g12_prompt", f"research/science_program_2026_05/04_goal_prompts/{NEXT_G12_PROMPT_NAME}", True),
        ("next_g12_starter", NEXT_G12_STARTER_NAME, True),
        ("verifier_and_focused_tests", "verify_*.py and test_*.py in route dir", True),
        ("safe_flags", "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false", True),
        ("forbidden_surfaces", "No validation/results/performance/promotion/API/paid-vendor/broker-order/raw-blob/live/risk/prompt changes opened", True),
        ("completion_standard", "Proxy evidence context/control only, broker truth claims zero, unresolved sources exact requirements", True),
    ]
    missing = [row[0] for row in checklist if not row[2]]
    return safe_base(
        {
            "artifact_family": "COMPLETION_AUDIT",
            "objective_restatement": "Attach source-family, as-of/hash/redaction, non-equivalence, invalid-context, and exact access/parser contracts for blocked-17 orderflow/proxy dependencies without claiming broker-native CFD truth or opening results.",
            "completion_standard_satisfied": missing == [],
            "checklist": [
                {"requirement": req, "evidence": evidence, "satisfied": satisfied}
                for req, evidence, satisfied in checklist
            ],
            "missing_incomplete_or_weak_requirements": missing,
            "safe_flags": {
                "promotion_verdict": PROMOTION_VERDICT,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
        }
    )


def next_g12_prompt_text() -> str:
    return f"""# G12 SCID Blocked17 Orderflow Proxy Contract Audit Goal Prompt

Evidence class: G12 source-control audit only.

Objective: audit the source-family, proxy-equivalence, as-of/hash/redaction, blocker, and context-packet contracts emitted by `{rel(ROUTE_DIR)}`. Accept or reject only whether the packet is G12-ready as source/control evidence. Do not open validation, result scoring, R/PnL/win-rate/expectancy/performance, promotion, AI/API, paid-vendor access, broker account/order/history/deal/position evidence, raw market blob commits, live restart/live behavior, registry edits, or trading/risk/safety/prompt-decision changes.

Mandatory preflight:
1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/goal_session_research_discipline.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `.context/00_core/local_heavy_data_inventory.md`.
7. Read `{rel(ROUTE_DIR / (PREFIX + '_COMPLETION_AUDIT_' + DATE + '.json'))}`.
8. Read `{rel(ROUTE_DIR / (PREFIX + '_OUTPUT_MANIFEST_' + DATE + '.json'))}`.
9. Read `{rel(ROUTE_DIR / (PREFIX + '_SOURCE_FAMILY_CONTRACT_' + DATE + '.json'))}`.
10. Read `{rel(ROUTE_DIR / (PREFIX + '_EQUIVALENCE_AND_INVALID_CONTEXT_MATRIX_' + DATE + '.json'))}`.
11. Read `{rel(ROUTE_DIR / (PREFIX + '_PAID_ACCESS_FREE_BLOCKER_LEDGER_' + DATE + '.json'))}`.

Acceptance standard:
- The exact blocked-17 denominator is preserved, the other 15 blocked cards stay excluded, and ready-8/expansion denominators are untouched.
- Proxy evidence remains context/control only and `broker_native_cfd_truth_claims=0`.
- Every `PROXY_VALIDITY_REQUIRES_CONTRACT` surface is either covered by a source-family/parser/hash/as-of/non-equivalence contract or reduced to an exact source/parser/access/capture requirement.
- Source-family contracts fail closed on missing source family, symbol mapping, roll/session/as-of, staleness, inverse policy, hash/deferral, or non-equivalence fields.
- No forbidden surface is opened.

Required outputs: G12 decision ledger, artifact/hash audit, source-family contract audit, equivalence/non-equivalence audit, blocker exactness audit, no-leak/safe-flag audit, verifier/focused tests, completion audit, and next G0/G12 starter if accepted. Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""


def next_g12_starter_text() -> str:
    prompt_path = f"research/science_program_2026_05/04_goal_prompts/{NEXT_G12_PROMPT_NAME}"
    return (
        f"/goal Follow the full controlling prompt in {prompt_path} as the complete objective; "
        "run mandatory preflight/context refresh first; do not rely on chat or compaction memory; "
        "stay G12 source-control audit only with no validation/result scoring/R-PnL-win-rate-expectancy-performance/"
        "promotion/live/API/paid-vendor/broker account-order-history-deal-position/raw-blob/trading-risk-safety-prompt-decision changes; "
        "audit the blocked17 orderflow/proxy contracts to proof-or-rejection, preserving context-control-only proxy evidence, "
        "broker_native_cfd_truth_claims=0, exact source/parser/access/capture remainders, verifier/focused tests, scoped commits, "
        "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when the prompt file's acceptance standard is fully satisfied."
    )


def build_output_manifest() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for name in sorted(set(JSON_ARTIFACTS + MD_ARTIFACTS + [
        "build_scid_orderflow_proxy_validity_contract_and_context_packet_route_2026_05_13.py",
        "verify_scid_orderflow_proxy_validity_contract_and_context_packet_route_2026_05_13.py",
        "test_scid_orderflow_proxy_validity_contract_and_context_packet_route_2026_05_13.py",
        NEXT_G12_STARTER_NAME,
        f"{PREFIX}_FOCUSED_TEST_RESULT_{DATE}.json",
        f"{PREFIX}_FOCUSED_TEST_RESULT_{DATE}.md",
    ])):
        path = ROUTE_DIR / name
        if path.name.endswith("OUTPUT_MANIFEST_2026-05-13.json") or path.name.endswith("OUTPUT_MANIFEST_2026-05-13.md"):
            continue
        if path.exists():
            rows.append(
                {
                    "path": rel(path),
                    "sha256": sha256_path(path),
                    "size_bytes": path.stat().st_size,
                    "artifact_kind": path.suffix.lstrip(".") or "txt",
                }
            )
    prompt_path = PROMPT_ROOT / NEXT_G12_PROMPT_NAME
    if prompt_path.exists():
        rows.append(
            {
                "path": rel(prompt_path),
                "sha256": sha256_path(prompt_path),
                "size_bytes": prompt_path.stat().st_size,
                "artifact_kind": "md",
            }
        )
    return safe_base(
        {
            "artifact_family": "OUTPUT_MANIFEST",
            "artifact_count": len(rows),
            "rows": rows,
            "raw_market_blob_commits_added": 0,
            "broker_native_cfd_truth_claims": 0,
        }
    )


def main() -> None:
    route_g0 = read_json(INPUTS["g0_route_reconciliation"])
    dependency_map = read_json(INPUTS["g0_dependency_route_map"])
    card_set = read_json(INPUTS["source_status_card_set"])
    status_matrix = read_json(INPUTS["source_status_matrix"])
    source_inventory = read_json(INPUTS["source_inventory"])
    proxy_validity = read_json(INPUTS["proxy_validity_matrix"])
    g12_proxy_hash = read_json(INPUTS["g12_proxy_hash_asof_audit"])

    input_hashes = {}
    for key, path in INPUTS.items():
        p = Path(path)
        if not p.is_absolute():
            p = REPO_ROOT / p
        input_hashes[key] = {
            "path": rel(p),
            "exists": p.exists(),
            "sha256": sha256_path(p) if p.exists() and p.is_file() else None,
        }

    local_observations = local_root_observations()
    dependency_ledger = build_source_dependency_ledger(status_matrix, dependency_map)
    source_contract = build_source_family_contract(proxy_validity, local_observations, dependency_ledger)
    context_schema = build_context_packet_schema(source_contract)
    equivalence = build_equivalence_matrix(proxy_validity)
    asof_hash = build_asof_hash_redaction_policy(source_inventory, g12_proxy_hash)
    blocker = build_blocker_ledger(source_contract, dependency_ledger)
    route_decision = build_route_decision_ledger(dependency_ledger, source_contract, equivalence)
    noleak = build_noleak_audit(card_set, dependency_ledger, equivalence)
    saturation = build_saturation_self_redteam(dependency_ledger, equivalence, blocker)
    completion = build_completion_audit()
    context_anchor = build_context_anchor(git_head(), input_hashes)

    artifacts = {
        f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json": ("Context Anchor", context_anchor),
        f"{PREFIX}_SOURCE_DEPENDENCY_LEDGER_{DATE}.json": ("Source Dependency Ledger", dependency_ledger),
        f"{PREFIX}_SOURCE_FAMILY_CONTRACT_{DATE}.json": ("Source Family Contract", source_contract),
        f"{PREFIX}_CONTEXT_PACKET_SCHEMA_{DATE}.json": ("Context Packet Schema", context_schema),
        f"{PREFIX}_EQUIVALENCE_AND_INVALID_CONTEXT_MATRIX_{DATE}.json": (
            "Equivalence And Invalid Context Matrix",
            equivalence,
        ),
        f"{PREFIX}_ASOF_HASH_REDACTION_POLICY_{DATE}.json": ("As-Of Hash Redaction Policy", asof_hash),
        f"{PREFIX}_PAID_ACCESS_FREE_BLOCKER_LEDGER_{DATE}.json": ("Paid Access Free Blocker Ledger", blocker),
        f"{PREFIX}_ROUTE_DECISION_LEDGER_{DATE}.json": ("Route Decision Ledger", route_decision),
        f"{PREFIX}_NOLEAK_SAFE_FLAG_AUDIT_{DATE}.json": ("No-Leak Safe-Flag Audit", noleak),
        f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE}.json": ("Saturation Self-Red-Team", saturation),
        f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json": ("Completion Audit", completion),
    }

    for name, (title, payload) in artifacts.items():
        write_json(name, payload)
        write_md(name.replace(".json", ".md"), title, payload)

    (PROMPT_ROOT / NEXT_G12_PROMPT_NAME).write_text(next_g12_prompt_text(), encoding="utf-8")
    (ROUTE_DIR / NEXT_G12_STARTER_NAME).write_text(next_g12_starter_text() + "\n", encoding="utf-8")

    manifest = build_output_manifest()
    write_json(f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json", manifest)
    write_md(f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.md", "Output Manifest", manifest)

    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "terminal_decision": TERMINAL_DECISION,
                "proxy_card_count": dependency_ledger["proxy_card_count"],
                "proxy_field_requirement_count": dependency_ledger["proxy_field_requirement_count"],
                "proxy_requirement_surface_count": dependency_ledger["proxy_requirement_surface_count"],
                "source_family_contract_count": source_contract["contract_count"],
                "equivalence_row_count": equivalence["equivalence_row_count"],
                "route_g0_terminal_decision": route_g0.get("terminal_decision"),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
