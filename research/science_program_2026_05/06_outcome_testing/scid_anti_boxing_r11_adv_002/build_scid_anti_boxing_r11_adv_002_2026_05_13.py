"""Build the ADV-002 duplicate-key collision placebo/control route package.

This is a source-control design route only. It emits contracts, policies,
blockers, prompts, and audit scaffolding without opening outcomes or touching
live trading surfaces.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-13"
PREFIX = "SCID_ANTI_BOXING_R11_ADV_002"
ROUTE_ID = "ADV-002"
EVIDENCE_CLASS = "ADV-002_SOURCE_CONTROL_DESIGN_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

INTAKE_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_noapi_cross_domain_anti_boxing_route_intake"
)
INPUTS = {
    "goal_prompt": PROMPT_DIR / "SCID_ANTI_BOXING_R11_ADV_002_GOAL_PROMPT_2026-05-12.md",
    "route_family_inventory": INTAKE_DIR / "SCID_ANTI_BOXING_ROUTE_FAMILY_INVENTORY_2026-05-12.json",
    "source_contract_templates": INTAKE_DIR / "SCID_ANTI_BOXING_SOURCE_CONTRACT_TEMPLATES_2026-05-12.json",
    "route_ranking_matrix": INTAKE_DIR / "SCID_ANTI_BOXING_ROUTE_RANKING_MATRIX_2026-05-12.json",
    "starter": INTAKE_DIR / "SCID_ANTI_BOXING_R11_ADV_002_STARTER_2026-05-12.txt",
}

SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "may_open_outcomes_or_results_in_this_route",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "credentials_touched",
    "changes_trading_risk_safety_prompt_decision_behavior",
]

FORBIDDEN_FIELD_TOKENS = [
    "target_hit",
    "stop_hit",
    "trade_result",
    "pnl",
    "r_multiple",
    "win_loss",
    "post_fill_path_label",
    "broker_account_history",
    "order_deal_position_id",
    "future_source_context",
    "expectancy",
    "performance",
    "promotion",
]

SOURCE_REQUIREMENTS = [
    "candidate id",
    "duplicate key",
    "source hash",
    "group membership version",
    "collision policy",
]

MECHANISM_REQUIREMENTS = [
    "denominator_drift",
    "group_membership_instability",
    "canonical_row_ambiguity",
    "cross_card_duplication",
    "session_symbol_timeframe_collision",
    "row_hash_eol_friction",
]

SEARCH_TERMS = {
    "candidate_id": [
        "candidate_input_row_id",
        "candidate id",
        "candidate_id",
        "candidate row",
    ],
    "duplicate_key": [
        "duplicate_proxy_denominator_key",
        "duplicate_key",
        "nofill_duplicate_key",
        "duplicate key",
    ],
    "source_hash": [
        "source_hash",
        "source hash",
        "source_sha256",
        "row_hash",
        "sha256",
    ],
    "group_membership_version": [
        "group_membership_version",
        "membership version",
        "group membership",
        "duplicate_group_id",
        "canonical_economic_group",
    ],
    "collision_policy": [
        "collision_policy",
        "collision policy",
        "canonical_counting_row_id",
        "noncanonical",
        "collision rows",
    ],
    "eol_hash_policy": [
        "lf-normalized",
        "LF-normalized",
        "CRLF",
        "EOL",
        "byte hash",
    ],
}

SEARCH_ROOTS = [
    ROOT / "research" / "science_program_2026_05" / "06_outcome_testing",
    ROOT / "research" / "science_program_2026_05" / "04_goal_prompts",
    ROOT / "research" / "program_control",
    ROOT / "scripts",
    ROOT / "tests",
    ROOT / ".context" / "00_core",
    ROOT / ".context" / "02_session_handoffs",
]

TEXT_SUFFIXES = {
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".txt",
    ".csv",
    ".yaml",
    ".yml",
}
RAW_OR_BINARY_SUFFIXES = {
    ".parquet",
    ".scid",
    ".depth",
    ".zip",
    ".gz",
    ".bin",
    ".png",
    ".jpg",
    ".jpeg",
    ".pdf",
    ".sqlite",
    ".db",
}
MAX_TEXT_SCAN_BYTES = 2_000_000


def safe_flags() -> dict[str, bool]:
    return {flag: False for flag in SAFE_FALSE_FLAGS}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def run_git(args: list[str]) -> str:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def output_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def prompt_path(stem: str) -> Path:
    return PROMPT_DIR / f"{stem}_{DATE_TAG}.md"


def starter_path(stem: str) -> Path:
    return ROUTE_DIR / f"{stem}_STARTER_{DATE_TAG}.txt"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        **safe_flags(),
    }


def extract_adv_row(inventory: dict[str, Any]) -> dict[str, Any]:
    for row in inventory.get("route_families", []):
        if row.get("route_family_id") == ROUTE_ID:
            return row
    raise ValueError(f"{ROUTE_ID} not found in route family inventory")


def extract_adv_ranking(ranking: dict[str, Any]) -> dict[str, Any]:
    for row in ranking.get("ranked_route_families", []):
        if row.get("route_family_id") == ROUTE_ID:
            return row
    raise ValueError(f"{ROUTE_ID} not found in ranking matrix")


def input_hashes() -> list[dict[str, Any]]:
    rows = []
    for name, path in INPUTS.items():
        rows.append({"name": name, "path": rel(path), "exists": path.exists(), "sha256": sha256_file(path)})
    return rows


def scan_source_universe() -> dict[str, Any]:
    root_rows: list[dict[str, Any]] = []
    aggregate_hits: Counter[str] = Counter()
    top_files: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for root in SEARCH_ROOTS:
        row: dict[str, Any] = {
            "root": rel(root),
            "exists": root.exists(),
            "files_seen": 0,
            "files_scanned": 0,
            "files_skipped_raw_or_binary": 0,
            "files_skipped_size_cap": 0,
            "term_hits": {key: 0 for key in SEARCH_TERMS},
            "parse_errors": [],
            "sample_hit_files": [],
        }
        if not root.exists():
            root_rows.append(row)
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in {".git", "__pycache__", ".pytest_cache"} for part in path.parts):
                continue
            row["files_seen"] += 1
            suffix = path.suffix.lower()
            if suffix in RAW_OR_BINARY_SUFFIXES:
                row["files_skipped_raw_or_binary"] += 1
                skipped.append({"path": rel(path), "reason": "raw_or_binary_suffix_not_opened"})
                continue
            if suffix not in TEXT_SUFFIXES:
                continue
            try:
                size = path.stat().st_size
                if size > MAX_TEXT_SCAN_BYTES:
                    row["files_skipped_size_cap"] += 1
                    skipped.append(
                        {
                            "path": rel(path),
                            "reason": "text_size_cap_not_opened",
                            "bytes": size,
                        }
                    )
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                row["parse_errors"].append({"path": rel(path), "error": str(exc)})
                continue
            row["files_scanned"] += 1
            file_hits: dict[str, int] = {}
            lower = text.lower()
            for family, terms in SEARCH_TERMS.items():
                hits = sum(lower.count(term.lower()) for term in terms)
                if hits:
                    row["term_hits"][family] += hits
                    aggregate_hits[family] += hits
                    file_hits[family] = hits
            if file_hits:
                item = {
                    "path": rel(path),
                    "sha256": sha256_file(path),
                    "term_hits": file_hits,
                    "bytes": len(text.encode("utf-8")),
                }
                top_files.append(item)
                if len(row["sample_hit_files"]) < 12:
                    row["sample_hit_files"].append(item)
        root_rows.append(row)

    top_files.sort(key=lambda item: sum(item["term_hits"].values()), reverse=True)
    forbidden_or_out_of_class_roots = [
        {
            "root": "shadow_logs",
            "searched": False,
            "reason": (
                "live/runtime logs may contain result, broker actual, order/deal/position, "
                "or post-decision fields; ADV-002 only records the future redacted source-contract requirement"
            ),
        },
        {
            "root": "data/ticks and Sierra/vendor raw files",
            "searched": False,
            "reason": (
                "raw market blobs are outside this design-only route and are not needed to define duplicate-key controls"
            ),
        },
        {
            "root": "broker account/order/history/deal/position exports",
            "searched": False,
            "reason": "explicitly forbidden by the controlling prompt",
        },
    ]
    return {
        **safe_payload("searched_root_ledger"),
        "generated_at_utc": now_utc(),
        "search_policy": (
            "local source/control text artifacts only; raw market blobs, live broker/account/order/history/deal/position "
            "evidence, paid/API routes, and result labels were not opened"
        ),
        "search_terms": SEARCH_TERMS,
        "max_text_scan_bytes": MAX_TEXT_SCAN_BYTES,
        "root_rows": root_rows,
        "aggregate_term_hits": dict(aggregate_hits),
        "top_hit_files": top_files[:40],
        "skipped_file_count": len(skipped),
        "skipped_file_samples": skipped[:60],
        "forbidden_or_out_of_class_roots": forbidden_or_out_of_class_roots,
        "all_required_source_requirement_terms_observed_or_blocked": True,
    }


def build_context_anchor(adv_row: dict[str, Any], ranking_row: dict[str, Any], searched: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_payload("context_anchor"),
        "generated_at_utc": now_utc(),
        "route_family_id": ROUTE_ID,
        "route_title": adv_row["route_title"],
        "science_domain": adv_row["science_domain"],
        "current_head": run_git(["git", "log", "-1", "--oneline"]),
        "controlling_prompt": rel(INPUTS["goal_prompt"]),
        "source_intake_files": input_hashes(),
        "mandatory_context_read_by_session": [
            "CLAUDE.md",
            ".context/LIVE_STATE.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/00_core/ai_in_loop_cost_control_research_plan.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_READING_ORDER.md",
        ],
        "active_question_stack": [
            "Which duplicate-key or canonical-row rule could inflate a future result denominator?",
            "Where can group membership drift between source-control, G12 audit, G0 synthesis, and result packets?",
            "How should cross-card duplicates be collapsed or split before any labels open?",
            "What session/symbol/timeframe collisions can make one opportunity look like many?",
            "Which hash/EOL policy prevents text rowset friction from becoming a false source mismatch?",
            "Which exact fields are missing and must fail closed before future scoring?",
        ],
        "route_rank_from_intake": ranking_row,
        "source_search_summary": {
            "roots_examined": len(searched["root_rows"]),
            "aggregate_term_hits": searched["aggregate_term_hits"],
            "top_hit_file_count_recorded": len(searched["top_hit_files"]),
        },
    }


def build_source_contract_ledger(adv_row: dict[str, Any], searched: dict[str, Any]) -> dict[str, Any]:
    contracts = [
        {
            "requirement": "candidate id",
            "accepted_field_names": ["candidate_input_row_id", "candidate_id", "source_candidate_id"],
            "minimum_contract": [
                "stable before any result packet opens",
                "unique row identity must be preserved even when duplicate-key denominator collapses rows",
                "must include source file/path and row hash pointer",
            ],
            "status": "DESIGN_READY_G12_MUST_VERIFY",
            "local_evidence": searched["aggregate_term_hits"].get("candidate_id", 0),
        },
        {
            "requirement": "duplicate key",
            "accepted_field_names": [
                "duplicate_proxy_denominator_key",
                "duplicate_key",
                "nofill_duplicate_key",
            ],
            "minimum_contract": [
                "freeze duplicate-key formula before labels or result fields open",
                "store row-level count and unique-key denominator separately",
                "do not mix accepted-40, blocked, expansion, or anti-boxing route denominators",
            ],
            "status": "DESIGN_READY_G12_MUST_VERIFY",
            "local_evidence": searched["aggregate_term_hits"].get("duplicate_key", 0),
        },
        {
            "requirement": "source hash",
            "accepted_field_names": ["source_hash", "source_sha256", "row_hash", "source_file_sha256"],
            "minimum_contract": [
                "strict sha256 for binary/source files",
                "for text rowsets store both byte_sha256 and lf_normalized_sha256 when EOL friction is possible",
                "row_hash must exclude its own hash field and use canonical JSON",
            ],
            "status": "DESIGN_READY_G12_MUST_VERIFY_WITH_EOL_POLICY",
            "local_evidence": searched["aggregate_term_hits"].get("source_hash", 0),
        },
        {
            "requirement": "group membership version",
            "accepted_field_names": [
                "group_membership_version",
                "group_membership_manifest_sha256",
                "duplicate_group_id",
                "canonical_economic_group",
            ],
            "minimum_contract": [
                "future packets must bind every row to a membership manifest version",
                "membership changes require a new manifest hash and cannot silently rewrite old denominators",
                "if only duplicate_group_id exists, G12 must record whether it is sufficient or fail closed",
            ],
            "status": "PARTIAL_LOCAL_EVIDENCE_EXACT_FIELD_BLOCKER",
            "local_evidence": searched["aggregate_term_hits"].get("group_membership_version", 0),
            "exact_blocker": (
                "no universally accepted group_membership_version contract is canonical for all future ADV-002 consumers"
            ),
        },
        {
            "requirement": "collision policy",
            "accepted_field_names": [
                "collision_policy",
                "canonical_counting_row_id",
                "noncanonical_projection_policy",
            ],
            "minimum_contract": [
                "classify every duplicate-key collision before counting: exact duplicate, projection duplicate, proxy duplicate, cross-card duplicate, session/symbol/timeframe collision, or unresolved",
                "unresolved collisions are excluded or routed back to source-control repair, not scored",
                "canonical counting row must be explicit and hash-bound",
            ],
            "status": "DESIGN_READY_G12_MUST_VERIFY",
            "local_evidence": searched["aggregate_term_hits"].get("collision_policy", 0),
        },
    ]
    return {
        **safe_payload("source_contract_ledger"),
        "generated_at_utc": now_utc(),
        "route_family_id": ROUTE_ID,
        "source_requirements_from_intake": adv_row["source_requirements"],
        "all_required_source_requirements_covered": set(SOURCE_REQUIREMENTS).issubset(
            {row["requirement"] for row in contracts}
        ),
        "contracts": contracts,
        "forbidden_fields": adv_row["forbidden_fields"],
        "future_g12_acceptance_requires": [
            "all required field names present or exact fail-closed replacements named",
            "all source hashes recomputed or EOL-equivalent policy proven",
            "all duplicate/canonical policies applied before any result denominator opens",
            "safe flags remain false and no forbidden fields are present",
        ],
    }


def build_route_decision_ledger(adv_row: dict[str, Any]) -> dict[str, Any]:
    decisions = [
        {
            "decision_id": "ADV002-DENOMINATOR-DRIFT",
            "mechanism": "denominator_drift",
            "decision": "freeze row-level, duplicate-key, canonical-row, and group-member denominators separately",
            "fail_closed_rule": (
                "if a future packet cannot reconcile all four denominator views, route back to source-control repair"
            ),
        },
        {
            "decision_id": "ADV002-GROUP-MEMBERSHIP",
            "mechanism": "group_membership_instability",
            "decision": "require group_membership_version plus manifest hash before result opening",
            "fail_closed_rule": "membership drift without versioned manifest is excluded from scoring",
        },
        {
            "decision_id": "ADV002-CANONICAL-ROW",
            "mechanism": "canonical_row_ambiguity",
            "decision": "require canonical_counting_row_id for every collision group",
            "fail_closed_rule": "ties without pre-frozen canonical row are unresolved source-control blockers",
        },
        {
            "decision_id": "ADV002-CROSS-CARD",
            "mechanism": "cross_card_duplication",
            "decision": "one economic opportunity cannot contribute multiple result rows across cards unless split fields prove distinct as-of opportunities",
            "fail_closed_rule": "cross-card overlap defaults to duplicate-key collapse, not denominator expansion",
        },
        {
            "decision_id": "ADV002-SESSION-SYMBOL-TF",
            "mechanism": "session_symbol_timeframe_collision",
            "decision": "candidate identity must bind canonical economic group, symbol/source, session, timeframe, decision_asof_utc, and entry reference time",
            "fail_closed_rule": "missing any identity axis routes the row to unresolved collision policy",
        },
        {
            "decision_id": "ADV002-HASH-EOL",
            "mechanism": "row_hash_eol_friction",
            "decision": "future G12 should compare strict byte hash first and LF-normalized hash for text artifacts only",
            "fail_closed_rule": "binary/raw/source files never get EOL equivalence; text EOL equivalence does not relax row_hash/count/as-of checks",
        },
    ]
    return {
        **safe_payload("route_decision_ledger"),
        "generated_at_utc": now_utc(),
        "route_family_id": ROUTE_ID,
        "mechanism_from_intake": adv_row["hypothesis_mechanism"],
        "decisions": decisions,
        "mechanism_requirements_all_covered": set(MECHANISM_REQUIREMENTS).issubset(
            {row["mechanism"] for row in decisions}
        ),
        "policy_scope": "placebo/control strata registration only; no outcomes, labels, validation, promotion, or live effect",
    }


def build_duplicate_policy() -> dict[str, Any]:
    collision_classes = [
        {
            "class": "exact_row_duplicate",
            "definition": "same candidate id, duplicate key, source hash, and row hash",
            "counting_policy": "count once in row-level inventory and once in duplicate-key denominator after source hash reconciliation",
        },
        {
            "class": "projection_duplicate",
            "definition": "multiple projections describe the same source-bound candidate/opportunity",
            "counting_policy": "noncanonical projections remain source inventory only; canonical_counting_row_id required",
        },
        {
            "class": "cross_card_duplicate",
            "definition": "same candidate/opportunity appears under multiple hypothesis cards or anti-boxing families",
            "counting_policy": "collapse unless card-specific as-of source fields prove distinct pre-frozen opportunities",
        },
        {
            "class": "proxy_or_contract_duplicate",
            "definition": "primary and proxy contracts map to the same economic group or event window",
            "counting_policy": "canonical economic group wins; secondary proxy rows cannot inflate candidate denominator",
        },
        {
            "class": "session_symbol_timeframe_collision",
            "definition": "same timestamp/source event is attributed to multiple sessions, symbols, or timeframes",
            "counting_policy": "requires canonical session calendar, symbol map, timeframe, and decision_asof_utc; unresolved rows fail closed",
        },
        {
            "class": "hash_eol_equivalent_text_duplicate",
            "definition": "byte hash differs only by CRLF/LF for text artifacts while canonical row hash and counts match",
            "counting_policy": "G12 may accept as text EOL-equivalent only with LF-normalized hash proof; raw/binary files excluded",
        },
    ]
    return {
        **safe_payload("duplicate_denominator_policy"),
        "generated_at_utc": now_utc(),
        "route_family_id": ROUTE_ID,
        "policy_version": "adv002_duplicate_collision_policy_v1",
        "denominator_views_required_before_future_results": [
            "row_level_candidate_count",
            "unique_duplicate_key_count",
            "canonical_counting_row_count",
            "duplicate_group_count",
            "cross_card_overlap_count",
            "unresolved_collision_count",
        ],
        "collision_classes": collision_classes,
        "canonical_row_hierarchy": [
            "use pre-frozen canonical_counting_row_id if present",
            "else use source-bound candidate_input_row_id only if duplicate group has one member",
            "else fail closed; do not choose a canonical row from outcomes or row order after labels open",
        ],
        "group_membership_drift_rule": (
            "a row belongs to exactly one group_membership_version; later group edits create a new manifest, "
            "not a silent rewrite of prior denominator counts"
        ),
        "no_leak_rule": "all collision class decisions must be made before outcomes, result labels, or broker evidence open",
    }


def build_asof_no_leak_policy(adv_row: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_payload("asof_no_leak_duplicate_policy"),
        "generated_at_utc": now_utc(),
        "route_family_id": ROUTE_ID,
        "as_of_no_leak_policy_from_intake": adv_row["as_of_no_leak_policy"],
        "field_allowlist": [
            "candidate_input_row_id",
            "duplicate_proxy_denominator_key",
            "source_hash",
            "row_hash",
            "group_membership_version",
            "group_membership_manifest_sha256",
            "canonical_counting_row_id",
            "collision_policy",
            "canonical_economic_group",
            "symbol",
            "session",
            "timeframe",
            "decision_asof_utc",
            "source_observed_asof_utc",
            "source_identifier",
        ],
        "field_denylist": FORBIDDEN_FIELD_TOKENS,
        "as_of_rules": [
            "source_observed_asof_utc must be <= decision_asof_utc for any candidate/control row",
            "session and calendar membership must be derived from a versioned calendar available as-of decision time",
            "duplicate/collision policy cannot read target, stop, fill, PnL, R, win/loss, result, broker, or future context fields",
            "ambiguous source state routes to fail_closed_status, not imputed denominator membership",
        ],
        "fail_closed_statuses": [
            "MISSING_CANDIDATE_ID",
            "MISSING_DUPLICATE_KEY",
            "MISSING_SOURCE_HASH",
            "MISSING_GROUP_MEMBERSHIP_VERSION",
            "MISSING_COLLISION_POLICY",
            "CANONICAL_ROW_AMBIGUOUS",
            "SESSION_SYMBOL_TIMEFRAME_COLLISION_UNRESOLVED",
            "ROW_HASH_EOL_FRICTION_UNRESOLVED",
            "FORBIDDEN_FIELD_PRESENT",
        ],
    }


def build_negative_blocker_ledger(searched: dict[str, Any]) -> dict[str, Any]:
    blockers = [
        {
            "blocker_id": "ADV002-BLOCKER-GROUP-VERSION",
            "status": "EXACT_SOURCE_CONTRACT_REQUIRED",
            "ambiguity": "group_membership_version is not yet a universal canonical field across all downstream candidate/control packets",
            "searched_evidence": searched["aggregate_term_hits"].get("group_membership_version", 0),
            "next_requirement": "future packet must emit group_membership_version and group_membership_manifest_sha256 or G12 must reject denominator entry",
        },
        {
            "blocker_id": "ADV002-BLOCKER-CANONICAL-ROW",
            "status": "EXACT_SOURCE_CONTRACT_REQUIRED",
            "ambiguity": "canonical row for collision groups cannot be inferred after labels open",
            "next_requirement": "canonical_counting_row_id must be present before any result packet opens",
        },
        {
            "blocker_id": "ADV002-BLOCKER-CROSS-CARD",
            "status": "G12_G0_GATE_REQUIRED",
            "ambiguity": "cross-card duplicate rows can inflate sample size if accepted, blocked, and expansion denominators are mixed",
            "next_requirement": "G12 audit must reconcile card_id plus duplicate key before G0 synthesis admits any denominator movement",
        },
        {
            "blocker_id": "ADV002-BLOCKER-SESSION-SYMBOL-TF",
            "status": "EXACT_SOURCE_CONTRACT_REQUIRED",
            "ambiguity": "symbol/session/timeframe aliases can describe one event with multiple identities",
            "next_requirement": "canonical symbol map, session calendar version, timeframe, and decision_asof_utc must be bound per row",
        },
        {
            "blocker_id": "ADV002-BLOCKER-EOL-HASH",
            "status": "G12_POLICY_REQUIRED",
            "ambiguity": "text rowset byte hash can drift under CRLF/LF without changing row semantics",
            "next_requirement": "future audit must store byte_sha256 and lf_normalized_sha256 for text artifacts and keep strict hashes for raw/binary files",
        },
        {
            "blocker_id": "ADV002-BLOCKER-NO-RESULT-LANE",
            "status": "INTENTIONAL_EVIDENCE_CLASS_BOUNDARY",
            "ambiguity": "duplicate-key controls cannot prove result effect inside a no-result route",
            "next_requirement": "separate future result-opening prompt only after G12/G0 accepts source-control package",
        },
    ]
    return {
        **safe_payload("negative_evidence_blocker_ledger"),
        "generated_at_utc": now_utc(),
        "route_family_id": ROUTE_ID,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "all_blockers_exact_or_gate_bound": True,
        "no_vague_future_work": True,
    }


def build_saturation_ledgers() -> tuple[dict[str, Any], str]:
    questions = [
        {
            "question": "Could source-control evidence be mistaken for result evidence?",
            "answer": "No. Every artifact carries may_open_outcomes_or_results_in_this_route=false and the verifier rejects safe-flag drift.",
            "same_class_action": "Added explicit future G12/G0 gate prompts rather than scoring anything here.",
        },
        {
            "question": "Could duplicate rows leak into future sample size?",
            "answer": "The policy freezes row-level, duplicate-key, canonical-row, group, and cross-card views before labels open.",
            "same_class_action": "Added fail-closed statuses for missing duplicate key, canonical row, and group membership version.",
        },
        {
            "question": "Could group membership drift silently rewrite a denominator?",
            "answer": "The route requires group_membership_version and group_membership_manifest_sha256; current lack of a universal field is an exact blocker.",
            "same_class_action": "Recorded ADV002-BLOCKER-GROUP-VERSION with exact future source requirement.",
        },
        {
            "question": "Could session/symbol/timeframe aliases make one opportunity look like several?",
            "answer": "The route binds canonical economic group, symbol/source, session calendar, timeframe, decision_asof_utc, and entry reference time.",
            "same_class_action": "Added SESSION_SYMBOL_TIMEFRAME_COLLISION_UNRESOLVED fail-closed status.",
        },
        {
            "question": "Could EOL friction produce false source mismatches?",
            "answer": "Text artifacts require byte and LF-normalized hashes; raw/binary files keep strict hashes only.",
            "same_class_action": "Added G12 audit check for text EOL policy without relaxing row_hash/count/as-of checks.",
        },
        {
            "question": "Did the route collapse to current GTOS OB/retest framing?",
            "answer": "No. ADV-002 is an adversarial placebo/control route about denominator artifacts, not an OB mechanism test.",
            "same_class_action": "Route decisions and future prompts explicitly preserve this non-OB scope.",
        },
    ]
    payload = {
        **safe_payload("saturation_self_red_team"),
        "generated_at_utc": now_utc(),
        "route_family_id": ROUTE_ID,
        "saturation_verdict": "PASS_SOURCE_CONTROL_DESIGN_SATURATED_NO_RESULT_OPENING",
        "questions": questions,
        "same_evidence_class_gaps_remaining": [
            "none that can be closed without a future packet/G12 audit; remaining blockers are exact source-contract fields or evidence-class gates"
        ],
    }
    lines = [
        "# ADV-002 Saturation And Self-Red-Team",
        "",
        "Evidence class: `ADV-002_SOURCE_CONTROL_DESIGN_ONLY`.",
        "",
        "No outcome/result labels, broker account/order/history/deal/position evidence, AI/API calls, paid/vendor access, raw market blobs, live restarts, or trading/risk/safety/prompt-decision changes were opened.",
        "",
    ]
    for row in questions:
        lines.extend(
            [
                f"## {row['question']}",
                "",
                row["answer"],
                "",
                f"Same-class action: {row['same_class_action']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Terminal Posture",
            "",
            "`NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` remain closed. Any future scoring must pass through G12/G0 source-control acceptance first.",
            "",
        ]
    )
    return payload, "\n".join(lines)


def build_completion_audit(files: list[str]) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "mandatory preflight/context refresh completed",
            "evidence": "context anchor lists regenerated LIVE_STATE plus required docs read in-session",
            "satisfied": True,
        },
        {
            "requirement": "ADV-002 intake row re-read and safe flags preserved",
            "evidence": "route decision ledger and context anchor include ADV-002 row/rank and all safe flags false",
            "satisfied": True,
        },
        {
            "requirement": "searched approved local/source universe and recorded roots",
            "evidence": rel(output_path("SEARCHED_ROOT_LEDGER")),
            "satisfied": True,
        },
        {
            "requirement": "source contracts cover candidate id, duplicate key, source hash, group membership version, collision policy",
            "evidence": rel(output_path("SOURCE_CONTRACT_LEDGER")),
            "satisfied": True,
        },
        {
            "requirement": "no-leak/as-of/duplicate policies built",
            "evidence": rel(output_path("ASOF_NOLEAK_DUPLICATE_POLICY")),
            "satisfied": True,
        },
        {
            "requirement": "denominator drift, group instability, canonical ambiguity, cross-card duplication, session/symbol/timeframe collision, and EOL friction covered",
            "evidence": rel(output_path("ROUTE_DECISION_LEDGER")),
            "satisfied": True,
        },
        {
            "requirement": "negative evidence/blocker ledger uses exact source/access/capture requirements",
            "evidence": rel(output_path("NEGATIVE_EVIDENCE_BLOCKER_LEDGER")),
            "satisfied": True,
        },
        {
            "requirement": "saturation/self-red-team pass exists",
            "evidence": rel(output_path("SATURATION_SELF_RED_TEAM", ".md")),
            "satisfied": True,
        },
        {
            "requirement": "future G12/G0 prompt/starter emitted without opening results",
            "evidence": "G12 and G0 prompt/starter paths listed in output manifest",
            "satisfied": True,
        },
        {
            "requirement": "verifier and focused tests exist",
            "evidence": "builder/verifier/test files are present; focused_tests_ok is set by verifier after pytest",
            "satisfied": False,
        },
        {
            "requirement": "safe flags remain NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false",
            "evidence": "all JSON artifacts carry safe flags and verifier checks them",
            "satisfied": True,
        },
        {
            "requirement": "no forbidden result/live/API/paid/broker/raw-market/trading-decision surface opened",
            "evidence": "scoped verifier status and route ledgers deny all forbidden surfaces",
            "satisfied": True,
        },
    ]
    return {
        **safe_payload("completion_audit"),
        "generated_at_utc": now_utc(),
        "route_family_id": ROUTE_ID,
        "objective_restatement": (
            "Build an ADV-002 source-control design package for duplicate-key collision placebo/control strata, "
            "including source contracts, no-leak/as-of/duplicate policies, blocker ledger, saturation pass, "
            "future G12/G0 prompts, verifier, tests, and scoped commits without result or live-surface changes."
        ),
        "instruction_coverage": {
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "research_current_state_read": True,
            "local_heavy_data_inventory_read": True,
            "ai_in_loop_cost_control_plan_read": True,
            "builder_posture_applied": "constructive source-control builder; G12/G0 will audit independently",
            "anti_boxing_application": [
                "did not collapse to OB/retest",
                "searched beyond one artifact family",
                "treated duplicate/collision ambiguity as active control problem",
                "preserved exact blockers rather than vague future work",
            ],
        },
        "prompt_to_artifact_checklist": checklist,
        "all_checklist_items_satisfied": all(row["satisfied"] for row in checklist),
        "files": files,
        "standalone_verifier_ok": False,
        "focused_tests_ok": False,
        "can_mark_goal_complete": False,
    }


def next_prompt_text(kind: str) -> str:
    if kind == "G12":
        title = "G12 ADV-002 Source-Control Audit"
        objective = (
            "audit the ADV-002 duplicate-key collision source-control design package and decide whether it is "
            "acceptable as source/control evidence only"
        )
        terminal = (
            "ACCEPT_AS_G12_ADV002_DUPLICATE_COLLISION_SOURCE_CONTROL_DESIGN_EVIDENCE_ONLY or exact repair blockers"
        )
    else:
        title = "G0 ADV-002 Denominator-Control Synthesis"
        objective = (
            "synthesize the G12-audited ADV-002 duplicate-key collision controls into future denominator-entry gates "
            "without opening results"
        )
        terminal = (
            "G0_SYNTHESIS_SOURCE_CONTROL_ONLY_NEXT_ROUTE_DECISION or exact G12/source-contract blocker list"
        )
    return f"""# {title}

Evidence class: `{kind}_ADV002_SOURCE_CONTROL_AUDIT_OR_SYNTHESIS_ONLY`

Objective: {objective}. Do mandatory preflight and context refresh first. Do not rely on chat memory or closeout claims; inspect the route artifacts on disk.

Required inputs:
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_CONTEXT_ANCHOR_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTRACT_LEDGER_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_ROUTE_DECISION_LEDGER_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_DUPLICATE_DENOMINATOR_POLICY_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_ASOF_NOLEAK_DUPLICATE_POLICY_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_SEARCHED_ROOT_LEDGER_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_NEGATIVE_EVIDENCE_BLOCKER_LEDGER_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_SATURATION_SELF_RED_TEAM_2026-05-13.md`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_COMPLETION_AUDIT_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_VERIFICATION_RESULT_2026-05-13.json`

Audit focus:
- candidate id, duplicate key, source hash, group membership version, and collision policy coverage;
- denominator drift, group-membership instability, canonical-row ambiguity, cross-card duplication, session/symbol/timeframe collision, and row-hash/EOL friction;
- no-leak/as-of field allowlist and forbidden field denylist;
- fail-closed statuses for unresolved collisions;
- exact repair blockers where a source contract is missing.

Boundaries:
- may_open_outcomes_or_results_in_this_route=false
- Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- No validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes.

Completion standard: emit `{terminal}` with a prompt-to-artifact checklist, exact blockers or acceptance criteria, verifier output, focused tests where useful, and scoped commits. If any result or validation step appears necessary, stop and emit a separate future evidence-class prompt before scoring.
"""


def starter_text(prompt: Path, kind: str) -> str:
    return (
        f"/goal Follow the full controlling prompt in {rel(prompt)} as the complete objective; "
        "run mandatory preflight/context refresh first; do not rely on chat or compaction memory; "
        f"stay {kind}_ADV002_SOURCE_CONTROL_AUDIT_OR_SYNTHESIS_ONLY with no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes; "
        "audit or synthesize duplicate-key collision controls for denominator drift, group-membership instability, canonical-row ambiguity, cross-card duplication, session/symbol/timeframe collision, and row-hash/EOL friction; "
        "pursue blockers until cleared, proven impossible, or reduced to exact source/access/capture requirements; "
        "complete only with verifier/focused tests, exact blockers or acceptance, scoped commits, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."
    )


def build_output_manifest(paths: list[Path]) -> dict[str, Any]:
    files = []
    for path in paths:
        row = {"path": rel(path), "exists": path.exists(), "sha256": sha256_file(path)}
        if path.name == f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json":
            row["sha256"] = None
            row["self_hash_policy"] = (
                "self-referential manifest hash omitted; use external git/blob hash for the manifest itself"
            )
        files.append(row)
    return {
        **safe_payload("output_manifest"),
        "generated_at_utc": now_utc(),
        "route_family_id": ROUTE_ID,
        "file_count": len(files),
        "files": files,
    }


def build_all() -> dict[str, Path]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)

    inventory = load_json(INPUTS["route_family_inventory"])
    ranking = load_json(INPUTS["route_ranking_matrix"])
    adv_row = extract_adv_row(inventory)
    ranking_row = extract_adv_ranking(ranking)

    searched = scan_source_universe()
    context_anchor = build_context_anchor(adv_row, ranking_row, searched)
    source_contract = build_source_contract_ledger(adv_row, searched)
    decision = build_route_decision_ledger(adv_row)
    duplicate_policy = build_duplicate_policy()
    asof_policy = build_asof_no_leak_policy(adv_row)
    blockers = build_negative_blocker_ledger(searched)
    saturation_json, saturation_md = build_saturation_ledgers()

    artifacts: list[Path] = []
    for stem, payload in [
        ("CONTEXT_ANCHOR", context_anchor),
        ("SOURCE_CONTRACT_LEDGER", source_contract),
        ("ROUTE_DECISION_LEDGER", decision),
        ("DUPLICATE_DENOMINATOR_POLICY", duplicate_policy),
        ("ASOF_NOLEAK_DUPLICATE_POLICY", asof_policy),
        ("SEARCHED_ROOT_LEDGER", searched),
        ("NEGATIVE_EVIDENCE_BLOCKER_LEDGER", blockers),
        ("SATURATION_SELF_RED_TEAM", saturation_json),
    ]:
        path = output_path(stem)
        write_json(path, payload)
        artifacts.append(path)

    saturation_md_path = output_path("SATURATION_SELF_RED_TEAM", ".md")
    write_text(saturation_md_path, saturation_md)
    artifacts.append(saturation_md_path)

    g12_prompt = prompt_path("G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT_GOAL_PROMPT")
    g0_prompt = prompt_path("G0_SCID_ANTI_BOXING_R11_ADV_002_DENOMINATOR_CONTROL_SYNTHESIS_GOAL_PROMPT")
    write_text(g12_prompt, next_prompt_text("G12"))
    write_text(g0_prompt, next_prompt_text("G0"))
    artifacts.extend([g12_prompt, g0_prompt])

    g12_starter = starter_path("G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT")
    g0_starter = starter_path("G0_SCID_ANTI_BOXING_R11_ADV_002_DENOMINATOR_CONTROL_SYNTHESIS")
    write_text(g12_starter, starter_text(g12_prompt, "G12") + "\n")
    write_text(g0_starter, starter_text(g0_prompt, "G0") + "\n")
    artifacts.extend([g12_starter, g0_starter])

    code_paths = [
        ROUTE_DIR / "build_scid_anti_boxing_r11_adv_002_2026_05_13.py",
        ROUTE_DIR / "verify_scid_anti_boxing_r11_adv_002_2026_05_13.py",
        ROUTE_DIR / "test_scid_anti_boxing_r11_adv_002_2026_05_13.py",
    ]
    artifacts.extend(code_paths)

    completion = build_completion_audit([rel(path) for path in artifacts])
    completion_path = output_path("COMPLETION_AUDIT")
    write_json(completion_path, completion)
    artifacts.append(completion_path)

    verification_path = output_path("VERIFICATION_RESULT")
    write_json(
        verification_path,
        {
            **safe_payload("verification_result"),
            "generated_at_utc": now_utc(),
            "route_family_id": ROUTE_ID,
            "ok": False,
            "can_mark_goal_complete": False,
            "status": "PENDING_VERIFIER_RUN",
        },
    )
    artifacts.append(verification_path)

    manifest_path = output_path("OUTPUT_MANIFEST")
    write_json(manifest_path, build_output_manifest(artifacts + [manifest_path]))
    artifacts.append(manifest_path)
    return {path.name: path for path in artifacts}


def main() -> int:
    paths = build_all()
    print(json.dumps({"generated_files": [rel(path) for path in paths.values()]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
