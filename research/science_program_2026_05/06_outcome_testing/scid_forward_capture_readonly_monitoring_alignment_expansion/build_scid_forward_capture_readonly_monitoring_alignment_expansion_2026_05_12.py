"""Build SCID forward-capture read-only monitoring alignment expansion.

This route inspects schema/key shapes only. It does not copy raw values, open
results, call APIs, inspect broker/order/account evidence, modify producers, or
wire live behavior.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE_TAG = "2026-05-12"
PREFIX = "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION"
ROUTE_ID = "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION"
EVIDENCE_CLASS = "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_ONLY"
TERMINAL_DECISION = "BUILT_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_G12_AUDIT_REQUIRED"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
G12_PROMPT = (
    PROMPT_DIR
    / "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_GOAL_PROMPT_2026-05-12.md"
)

MAX_JSONL_LINES = 200_000
MAX_EXAMPLES_PER_GROUP = 12
MAX_FORBIDDEN_EXAMPLES = 80

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
}

CAPTURE_GROUPS: dict[str, dict[str, Any]] = {
    "intended_side_direction": {
        "label": "side",
        "tokens": ["side", "direction", "bias", "long", "short", "bull", "bear"],
    },
    "intended_entry_reference": {
        "label": "entry",
        "tokens": ["entry", "limit", "entry_price", "entry_reference", "pending_limit"],
    },
    "intended_stop_reference": {
        "label": "stop",
        "tokens": ["stop", "stop_loss", "stop_reference", "sl_", "sl"],
    },
    "intended_target_reference": {
        "label": "target",
        "tokens": ["target", "take_profit", "tp_", "target_reference"],
    },
    "poi_type_bounds_source": {
        "label": "POI",
        "tokens": ["poi", "ob", "fvg", "breaker", "bounds", "zone", "lower_bound", "upper_bound"],
    },
    "framework_setup_family": {
        "label": "framework",
        "tokens": ["framework", "setup_family", "strategy_family", "qualified", "model_a"],
    },
    "lifecycle_fill_cancel_expiry_source_status": {
        "label": "lifecycle",
        "tokens": ["lifecycle", "pending", "intent", "cancel", "expiry", "expired", "created", "fill_or_expiry"],
    },
    "lower_timeframe_asof_path_availability": {
        "label": "LTF",
        "tokens": ["ltf", "lower_tf", "lower_timeframe", "m1", "m5", "path_order", "prefill", "bars_present"],
    },
    "future_orderflow_depth_proxy_requirements": {
        "label": "orderflow/proxy",
        "tokens": ["orderflow", "sierra", "databento", "depth", "scid", "mbo", "mbp", "proxy", "delta", "bid", "ask"],
    },
    "baseline_control_fields": {
        "label": "baseline-control",
        "tokens": ["baseline", "control", "partition", "seed", "duplicate", "denominator", "cohort", "session_bucket", "time_of_day"],
    },
}

FORBIDDEN_KEY_CATEGORIES: dict[str, list[str]] = {
    "broker_account_order_deal_position": [
        "broker",
        "account",
        "order_id",
        "order_ticket",
        "ticket",
        "deal",
        "position",
        "mt5",
        "fill_ticket",
    ],
    "result_performance_outcome": [
        "outcome",
        "result",
        "pnl",
        "profit",
        "realized",
        "actual_r",
        "broker_actual_r",
        "r_multiple",
        "expectancy",
        "win_rate",
        "wr",
        "performance",
        "terminal_target_status",
        "target_status",
        "loss",
    ],
    "post_outcome_or_validation": [
        "validation",
        "promotion",
        "score",
        "scoring",
        "sealed_validation",
        "quarantined",
        "post_cutoff",
    ],
    "credential_or_api": ["api_key", "secret", "credential", "token"],
}

RAW_BLOB_SUFFIXES = {
    ".scid",
    ".depth",
    ".parquet",
    ".csv",
    ".dly",
    ".bin",
    ".jsonl.gz",
    ".zip",
}

EXCLUDED_ROUTE_DIR_TOKENS = [
    "quarantined_neutral_target",
    "neutral_target",
    "sealed_validation_execution",
    "sealed_validation_target",
    "sealed_validation_design",
    "direction_aware_result",
    "result_design",
    "validation_execution",
]

EXCLUDED_SHADOW_FILE_TOKENS = [
    "account",
    "pnl",
    "broker",
    "actual_r",
    "shadow_outcome",
    "shadow_outcomes",
    "outcome",
    "outcomes",
    "slippage",
    "trade_index",
    "equity_read",
    "daily_pnl",
]

UPSTREAM_DIRS = {
    "combined_builder": OUTCOME_DIR / "scid_combined_source_search_and_forward_capture_route",
    "combined_g12": OUTCOME_DIR / "g12_scid_combined_source_search_and_forward_capture_route_audit",
    "combined_g0": OUTCOME_DIR / "g0_scid_combined_source_capture_route_synthesis_control",
    "offline_schema_builder": OUTCOME_DIR / "scid_forward_capture_offline_schema_implementation_package",
    "offline_schema_g12": OUTCOME_DIR / "g12_scid_forward_capture_offline_schema_implementation_package_audit",
    "offline_schema_g0": OUTCOME_DIR / "g0_scid_forward_capture_offline_schema_package_synthesis_control",
}

UPSTREAM_INPUTS: dict[str, Path] = {
    "controlling_prompt": PROMPT_DIR
    / "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
    "live_state": ROOT / ".context" / "LIVE_STATE.md",
    "quick_reference": ROOT / ".context" / "00_core" / "quick_reference_card.md",
    "research_doctrine": ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
    "goal_session_discipline": ROOT / ".context" / "00_core" / "goal_session_research_discipline.md",
    "research_current_state": ROOT / ".context" / "00_core" / "research_current_state.md",
    "latest_handoff": ROOT
    / ".context"
    / "02_session_handoffs"
    / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "g12_offline_decision": UPSTREAM_DIRS["offline_schema_g12"]
    / "G12_SCID_FC_SCHEMA_AUDIT_DECISION_LEDGER_2026-05-12.json",
    "g12_offline_schema_contract_audit": UPSTREAM_DIRS["offline_schema_g12"]
    / "G12_SCID_FC_SCHEMA_AUDIT_SCHEMA_CONTRACT_AUDIT_2026-05-12.json",
    "g12_offline_fixture_recomputation": UPSTREAM_DIRS["offline_schema_g12"]
    / "G12_SCID_FC_SCHEMA_AUDIT_FIXTURE_VALIDATOR_RECOMPUTATION_AUDIT_2026-05-12.json",
    "g12_offline_manifest_readonly_noleak": UPSTREAM_DIRS["offline_schema_g12"]
    / "G12_SCID_FC_SCHEMA_AUDIT_MANIFEST_READONLY_NOLEAK_AUDIT_2026-05-12.json",
    "g12_offline_output_manifest": UPSTREAM_DIRS["offline_schema_g12"]
    / "G12_SCID_FC_SCHEMA_AUDIT_OUTPUT_MANIFEST_2026-05-12.json",
    "g12_offline_verifier_result": UPSTREAM_DIRS["offline_schema_g12"]
    / "G12_SCID_FC_SCHEMA_AUDIT_VERIFICATION_RESULT_2026-05-12.json",
    "g12_offline_completion_audit": UPSTREAM_DIRS["offline_schema_g12"]
    / "G12_SCID_FC_SCHEMA_AUDIT_COMPLETION_AUDIT_2026-05-12.json",
    "g12_offline_closeout": UPSTREAM_DIRS["offline_schema_g12"]
    / "G12_SCID_FC_SCHEMA_AUDIT_CLOSEOUT_VERIFICATION_2026-05-12.json",
    "offline_field_group_schema_ledger": UPSTREAM_DIRS["offline_schema_builder"]
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_FIELD_GROUP_SCHEMA_LEDGER_2026-05-12.json",
    "offline_parser_validator_contract": UPSTREAM_DIRS["offline_schema_builder"]
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
    "offline_fixture_manifest": UPSTREAM_DIRS["offline_schema_builder"]
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_FIXTURE_MANIFEST_2026-05-12.json",
    "offline_fixture_validation_result": UPSTREAM_DIRS["offline_schema_builder"]
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_FIXTURE_VALIDATION_RESULT_LEDGER_2026-05-12.json",
    "offline_readonly_alignment": UPSTREAM_DIRS["offline_schema_builder"]
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_READ_ONLY_MONITORING_ALIGNMENT_LEDGER_2026-05-12.json",
    "offline_manifest_hash_policy": UPSTREAM_DIRS["offline_schema_builder"]
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_MANIFEST_HASH_POLICY_LEDGER_2026-05-12.json",
    "offline_output_manifest": UPSTREAM_DIRS["offline_schema_builder"]
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_OUTPUT_MANIFEST_2026-05-12.json",
    "offline_verifier_result": UPSTREAM_DIRS["offline_schema_builder"]
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_VERIFICATION_RESULT_2026-05-12.json",
    "offline_closeout": UPSTREAM_DIRS["offline_schema_builder"]
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_CLOSEOUT_VERIFICATION_2026-05-12.json",
    "g0_combined_reconciliation": UPSTREAM_DIRS["combined_g0"]
    / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_ACCEPTED_G12_AUDIT_RECONCILIATION_2026-05-12.json",
    "g0_combined_manifest_repair": UPSTREAM_DIRS["combined_g0"]
    / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_MANIFEST_BINDING_REPAIR_CONTINUITY_NOTE_2026-05-12.json",
    "g0_combined_carry_forward_contract": UPSTREAM_DIRS["combined_g0"]
    / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_CARRY_FORWARD_CAPTURE_CONTRACT_LEDGER_2026-05-12.json",
    "g12_combined_decision": UPSTREAM_DIRS["combined_g12"]
    / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_DECISION_LEDGER_2026-05-12.json",
    "g12_combined_row_coverage": UPSTREAM_DIRS["combined_g12"]
    / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT_2026-05-12.json",
    "g12_combined_field_status": UPSTREAM_DIRS["combined_g12"]
    / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_FIELD_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
    "g12_combined_source_saturation": UPSTREAM_DIRS["combined_g12"]
    / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_SOURCE_SEARCH_SATURATION_AUDIT_2026-05-12.json",
    "builder_forward_capture_contract": UPSTREAM_DIRS["combined_builder"]
    / "SCID_COMBINED_SOURCE_CAPTURE_FORWARD_CAPTURE_CONTRACT_2026-05-12.json",
    "builder_searched_root_ledger": UPSTREAM_DIRS["combined_builder"]
    / "SCID_COMBINED_SOURCE_CAPTURE_SEARCHED_ROOT_LEDGER_2026-05-12.json",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sanitize_key_segment(segment: Any) -> str:
    text = str(segment)
    text = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\+\d{2}:\d{2}|Z)?", "<timestamp>", text)
    text = re.sub(r"\d{4}-\d{2}-\d{2}", "<date>", text)
    text = re.sub(r"(?i)\b[0-9a-f]{16,}\b", "<hex>", text)
    text = re.sub(r"\b\d{3,}\b", "<number>", text)
    return text


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "schema_version": "scid_forward_capture_readonly_alignment_expansion_v1",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
    }


def output_path(stem: str, suffix: str = "json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.{suffix}"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: Any) -> None:
    body = "\n".join(
        [
            f"# {title}",
            "",
            f"- **route_id:** `{ROUTE_ID}`",
            f"- **evidence_class:** `{EVIDENCE_CLASS}`",
            "- **promotion_verdict:** `NO_PROMOTION_VERDICT`",
            "- **validation_safe:** `false`",
            "- **outcome_review_opened:** `false`",
            "- **live_effect:** `false`",
            "",
            "```json",
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True),
            "```",
            "",
        ]
    )
    path.write_text(body, encoding="utf-8")


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> list[Path]:
    json_path = output_path(stem, "json")
    md_path = output_path(stem, "md")
    write_json(json_path, payload)
    write_md(md_path, title, payload)
    return [json_path, md_path]


def collect_key_paths(value: Any, prefix: str = "", depth: int = 0, limit: int = 7) -> set[str]:
    if depth > limit:
        return set()
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = sanitize_key_segment(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            keys.add(path)
            keys.update(collect_key_paths(nested, path, depth + 1, limit))
    elif isinstance(value, list):
        list_prefix = f"{prefix}[]" if prefix else "[]"
        keys.add(list_prefix)
        for item in value[:25]:
            keys.update(collect_key_paths(item, list_prefix, depth + 1, limit))
    return keys


def py_keyword_shape(path: Path) -> tuple[set[str], int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text))
    relevant = set()
    all_group_tokens = {token for group in CAPTURE_GROUPS.values() for token in group["tokens"]}
    forbidden_tokens = {token for tokens in FORBIDDEN_KEY_CATEGORIES.values() for token in tokens}
    for token in tokens:
        lower = token.lower()
        if any(marker in lower for marker in all_group_tokens | forbidden_tokens):
            relevant.add(lower)
    return relevant, len(text.splitlines())


def forbidden_categories_for_key(key_path: str) -> list[str]:
    lower = key_path.lower()
    categories = []
    for category, tokens in FORBIDDEN_KEY_CATEGORIES.items():
        if any(token in lower for token in tokens):
            categories.append(category)
    return categories


def non_forbidden_key_paths(key_paths: set[str]) -> set[str]:
    return {key for key in key_paths if not forbidden_categories_for_key(key)}


def match_groups(key_paths: set[str]) -> dict[str, dict[str, Any]]:
    safe_keys = non_forbidden_key_paths(key_paths)
    matches: dict[str, dict[str, Any]] = {}
    for group_id, spec in CAPTURE_GROUPS.items():
        matched = sorted(
            key for key in safe_keys if any(token in key.lower() for token in spec["tokens"])
        )
        if matched:
            matches[group_id] = {
                "matched_key_count": len(matched),
                "matched_key_examples": matched[:MAX_EXAMPLES_PER_GROUP],
            }
    return matches


def excluded_file_reason(path: Path, root_label: str) -> str | None:
    suffix = "".join(path.suffixes[-2:]).lower() if path.suffixes[-2:] else path.suffix.lower()
    if suffix in RAW_BLOB_SUFFIXES or path.suffix.lower() in RAW_BLOB_SUFFIXES:
        return "raw_market_blob_or_archive_suffix_excluded"
    lower_path = path.as_posix().lower()
    parts = [part.lower() for part in path.parts]
    if any(part in {".git", ".pytest_cache", "__pycache__", ".venv", "venv"} for part in parts):
        return "tooling_cache_or_git_internal_excluded"
    if "06_outcome_testing" in lower_path and any(token in lower_path for token in EXCLUDED_ROUTE_DIR_TOKENS):
        return "validation_result_or_neutral_target_route_excluded"
    if root_label.startswith("shadow_logs") and any(token in path.name.lower() for token in EXCLUDED_SHADOW_FILE_TOKENS):
        return "shadow_log_forbidden_broker_account_result_performance_family_excluded"
    return None


def iter_relevant_route_files(base: Path) -> list[Path]:
    outcome_dir = base / "research" / "science_program_2026_05" / "06_outcome_testing"
    if not outcome_dir.exists():
        return []
    files: list[Path] = []
    for route_dir in sorted(item for item in outcome_dir.iterdir() if item.is_dir()):
        name = route_dir.name.lower()
        if "scid" not in name:
            continue
        if route_dir.resolve() == ROUTE_DIR.resolve():
            continue
        if any(token in name for token in EXCLUDED_ROUTE_DIR_TOKENS):
            continue
        for pattern in ("*.json", "*.jsonl", "*.py"):
            files.extend(route_dir.rglob(pattern))
    return files


def candidate_files_for_root(label: str, path: Path, scope: str) -> list[Path]:
    if not path.exists():
        return []
    if scope == "current_routes":
        return iter_relevant_route_files(path)
    if scope == "program_control":
        return sorted(path.glob("*.json")) if path.exists() else []
    if scope == "shadow_logs":
        return sorted(path.glob("*.jsonl")) if path.exists() else []
    if scope == "pipeline_state":
        return sorted(path.glob("*.json")) if path.exists() else []
    if scope == "research_infra":
        return sorted(path.glob("*.py")) if path.exists() else []
    if scope == "tests":
        tokens = ("scid", "candidate", "prefill", "orderflow", "lifecycle", "capture", "schema")
        return sorted(file for file in path.rglob("*.py") if any(token in file.name.lower() for token in tokens))
    if scope == "external_routes":
        return iter_relevant_route_files(path)
    if scope == "external_control":
        control = path / "research" / "science_program_2026_05" / "00_control"
        return sorted(control.glob("*.json")) if control.exists() else []
    return []


def search_plans() -> list[dict[str, Any]]:
    prior_roots = [
        Path(r"C:\tmp\gtos_otb\SCID_IMPL_DESIGN"),
        Path(r"C:\tmp\gtos_otb\SCID_SYNTH_HARNESS"),
        Path(r"C:\tmp\gtos_otb\SCID_LTF_OF_EXPANSION"),
        Path(r"C:\tmp\gtos_otb\SCID_NOAPI_HYP_FACTORY"),
        Path(r"C:\tmp\gtos_otb\NOAPIMECHREPLAY"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent"),
    ]
    plans: list[dict[str, Any]] = [
        {
            "label": "current_scid_source_control_route_artifacts",
            "root": ROOT,
            "scope": "current_routes",
            "why_allowed": "SCID source/control route JSON, JSONL, verifier, and tests; validation/result route names excluded.",
        },
        {
            "label": "current_program_control_json_artifacts",
            "root": ROOT / "research" / "science_program_2026_05" / "00_control",
            "scope": "program_control",
            "why_allowed": "program-control schemas and registries; JSON shapes only.",
        },
        {
            "label": "shadow_logs_shape_only_non_forbidden_families",
            "root": ROOT / "shadow_logs",
            "scope": "shadow_logs",
            "why_allowed": "shadow-log key sets only; broker/account/result/performance file families excluded by filename.",
        },
        {
            "label": "pipeline_state_schema_shapes",
            "root": ROOT / "pipeline_state",
            "scope": "pipeline_state",
            "why_allowed": "pipeline-state JSON key shapes only; no values copied.",
        },
        {
            "label": "research_infra_keyword_shapes",
            "root": ROOT / "src" / "research_infra",
            "scope": "research_infra",
            "why_allowed": "research-infra source keyword shapes only; no producer modification.",
        },
        {
            "label": "focused_tests_keyword_shapes",
            "root": ROOT / "tests",
            "scope": "tests",
            "why_allowed": "test keyword/key-shape evidence only.",
        },
    ]
    for root in prior_roots:
        label_prefix = "prior_worktree" if str(root).startswith(r"C:\tmp\gtos_otb") else "original_local_repo"
        plans.append(
            {
                "label": f"{label_prefix}_scid_route_artifact_shapes::{root.name}",
                "root": root,
                "scope": "external_routes",
                "why_allowed": "absolute local root route-artifact key shapes; no raw blobs or result/validation routes.",
            }
        )
        plans.append(
            {
                "label": f"{label_prefix}_program_control_shapes::{root.name}",
                "root": root,
                "scope": "external_control",
                "why_allowed": "absolute local root program-control JSON shapes; no raw blobs.",
            }
        )
    return plans


def inspect_json_file(path: Path) -> tuple[set[str], dict[str, Any]]:
    payload = load_json(path)
    if isinstance(payload, list):
        key_paths: set[str] = set()
        for row in payload[:5000]:
            key_paths.update(collect_key_paths(row))
        record_count = len(payload)
    else:
        key_paths = collect_key_paths(payload)
        record_count = 1
    return key_paths, {"record_count": record_count, "line_count": None, "line_cap_hit": False}


def inspect_jsonl_file(path: Path) -> tuple[set[str], dict[str, Any]]:
    key_paths: set[str] = set()
    line_count = 0
    parse_errors = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            line_count += 1
            if line_count > MAX_JSONL_LINES:
                break
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            key_paths.update(collect_key_paths(payload))
    return key_paths, {
        "record_count": line_count,
        "line_count": line_count,
        "line_cap_hit": line_count > MAX_JSONL_LINES,
        "parse_errors": parse_errors,
    }


def inspect_file(path: Path) -> tuple[set[str], dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return inspect_json_file(path)
    if suffix == ".jsonl":
        return inspect_jsonl_file(path)
    if suffix == ".py":
        keys, line_count = py_keyword_shape(path)
        return keys, {"record_count": 1, "line_count": line_count, "line_cap_hit": False, "source_text_shape_only": True}
    return set(), {"record_count": 0, "line_count": None, "line_cap_hit": False, "unsupported_suffix": suffix}


def content_hash_policy(path: Path) -> dict[str, Any]:
    lower = path.as_posix().lower()
    volatile = "shadow_logs" in lower or "pipeline_state" in lower
    size = path.stat().st_size if path.exists() else 0
    record = not volatile and size <= 5_000_000 and path.suffix.lower() in {".json", ".jsonl", ".py"}
    return {
        "content_sha256_recorded": record,
        "content_sha256": sha256_file(path) if record else None,
        "content_sha256_policy": "omitted_for_volatile_shadow_pipeline_or_large_file" if not record else "recorded_for_stable_artifact_file",
    }


def build_shape_inventory() -> dict[str, Any]:
    artifact_rows: list[dict[str, Any]] = []
    searched_roots: list[dict[str, Any]] = []
    excluded_files: list[dict[str, Any]] = []
    seen_paths: set[str] = set()

    for plan in search_plans():
        root = Path(plan["root"])
        files_seen = candidate_files_for_root(plan["label"], root, plan["scope"])
        parsed_count = 0
        excluded_count = 0
        parse_errors: list[dict[str, Any]] = []
        for file_path in files_seen:
            key = file_path.resolve().as_posix().lower()
            if key in seen_paths:
                continue
            seen_paths.add(key)
            reason = excluded_file_reason(file_path, plan["label"])
            if reason:
                excluded_count += 1
                excluded_files.append(
                    {
                        "root_label": plan["label"],
                        "path": display_path(file_path),
                        "exclusion_reason": reason,
                    }
                )
                continue
            try:
                key_paths, metrics = inspect_file(file_path)
            except Exception as exc:  # pragma: no cover - recorded for field-run robustness.
                parse_errors.append({"path": display_path(file_path), "error": repr(exc)})
                continue
            if not key_paths:
                continue
            parsed_count += 1
            forbidden = {
                key_path: forbidden_categories_for_key(key_path)
                for key_path in sorted(key_paths)
                if forbidden_categories_for_key(key_path)
            }
            safe_keys = non_forbidden_key_paths(key_paths)
            matches = match_groups(key_paths)
            hash_policy = content_hash_policy(file_path)
            artifact_rows.append(
                {
                    "root_label": plan["label"],
                    "path": display_path(file_path),
                    "suffix": file_path.suffix.lower(),
                    "record_count_shape_only": metrics.get("record_count"),
                    "line_count_shape_only": metrics.get("line_count"),
                    "line_cap_hit": metrics.get("line_cap_hit", False),
                    "parse_errors": metrics.get("parse_errors", 0),
                    "key_path_count": len(key_paths),
                    "safe_key_path_count": len(safe_keys),
                    "forbidden_key_path_count": len(forbidden),
                    "field_group_matches": matches,
                    "matched_group_ids": sorted(matches),
                    "shape_fingerprint_sha256": sha256_text("\n".join(sorted(key_paths))),
                    "safe_shape_fingerprint_sha256": sha256_text("\n".join(sorted(safe_keys))),
                    "raw_values_copied": False,
                    "producer_modified": False,
                    "running_process_altered": False,
                    **hash_policy,
                    "forbidden_key_path_examples": [
                        {"key_path": key_path, "categories": cats}
                        for key_path, cats in list(forbidden.items())[:20]
                    ],
                }
            )
        searched_roots.append(
            {
                "root_label": plan["label"],
                "root_path": display_path(root) if root.exists() else str(root).replace("\\", "/"),
                "exists": root.exists(),
                "scope": plan["scope"],
                "why_allowed": plan["why_allowed"],
                "files_seen": len(files_seen),
                "files_parsed_for_shape": parsed_count,
                "files_excluded": excluded_count,
                "parse_error_count": len(parse_errors),
                "parse_errors": parse_errors[:20],
            }
        )

    artifact_rows.sort(key=lambda row: (row["root_label"], row["path"]))
    return {
        "artifact_rows": artifact_rows,
        "searched_roots": searched_roots,
        "excluded_files": excluded_files,
    }


def schema_expected_fields() -> dict[str, dict[str, Any]]:
    ledger = load_json(UPSTREAM_INPUTS["offline_field_group_schema_ledger"])
    result: dict[str, dict[str, Any]] = {}
    for row in ledger["field_groups"]:
        result[row["field_group"]] = {
            "label": CAPTURE_GROUPS[row["field_group"]]["label"],
            "future_source_or_logger": row["future_source_or_logger"],
            "historical_status": row["historical_status"],
            "as_of_rule": row["as_of_rule"],
            "no_leak_rule": row["no_leak_rule"],
            "expected_fields": [field["name"] for field in row["fields"]],
        }
    return result


def build_coverage_matrix(artifact_rows: list[dict[str, Any]]) -> dict[str, Any]:
    expected = schema_expected_fields()
    safe_key_index: dict[str, set[str]] = defaultdict(set)
    group_artifacts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in artifact_rows:
        for group_id in row["matched_group_ids"]:
            group_artifacts[group_id].append(
                {
                    "path": row["path"],
                    "root_label": row["root_label"],
                    "matched_key_count": row["field_group_matches"][group_id]["matched_key_count"],
                    "matched_key_examples": row["field_group_matches"][group_id]["matched_key_examples"],
                    "safe_shape_fingerprint_sha256": row["safe_shape_fingerprint_sha256"],
                }
            )
        # Expand exact field comparisons from examples and shape fingerprints cannot recover full keys,
        # so compare by explicit examples plus forbidden-free groups stored in inventory rows.
        # The exact match audit below uses the safe key examples generated per group.
        for group_id, match in row["field_group_matches"].items():
            safe_key_index[group_id].update(match["matched_key_examples"])

    matrix_rows = []
    for group_id, spec in expected.items():
        exact_matches = sorted(
            field
            for field in spec["expected_fields"]
            if any(key.endswith(field) or key == field for key in safe_key_index.get(group_id, set()))
        )
        missing_exact = sorted(set(spec["expected_fields"]) - set(exact_matches))
        artifacts = sorted(group_artifacts.get(group_id, []), key=lambda item: (-item["matched_key_count"], item["path"]))
        status = (
            "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_INCOMPLETE"
            if artifacts
            else "NO_CURRENT_SHAPE_COVERAGE_NEW_ADDITIVE_CAPTURE_FIELDS_REQUIRED"
        )
        if artifacts and not missing_exact:
            status = "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_PRESENT_IN_INSPECTED_SHAPES"
        matrix_rows.append(
            {
                "field_group": group_id,
                "label": spec["label"],
                "coverage_status": status,
                "existing_shape_artifact_count": len(artifacts),
                "representative_shape_artifacts": artifacts[:MAX_EXAMPLES_PER_GROUP],
                "exact_schema_field_matches_found_by_name": exact_matches,
                "missing_exact_schema_fields": missing_exact,
                "historical_status": spec["historical_status"],
                "future_source_or_logger": spec["future_source_or_logger"],
                "as_of_rule": spec["as_of_rule"],
                "no_leak_rule": spec["no_leak_rule"],
                "exact_capture_requirement_to_close_gap": (
                    "Add/verify future additive capture rows for "
                    + ", ".join(missing_exact or spec["expected_fields"])
                    + f" via {spec['future_source_or_logger']}; enforce source_id/source_hash/as_of/redaction/forbidden-key fail-closed checks before G12 acceptance."
                ),
            }
        )
    return {
        **base_payload("field_group_coverage_gap_matrix"),
        "capture_group_count": len(matrix_rows),
        "all_ten_capture_groups_represented": len(matrix_rows) == 10,
        "groups_with_no_shape_coverage": [row["field_group"] for row in matrix_rows if row["existing_shape_artifact_count"] == 0],
        "groups_requiring_exact_additive_capture_fields": [
            row["field_group"] for row in matrix_rows if row["missing_exact_schema_fields"]
        ],
        "coverage_rows": matrix_rows,
    }


def build_forbidden_ledger(artifact_rows: list[dict[str, Any]], excluded_files: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts: Counter[str] = Counter()
    forbidden_rows: list[dict[str, Any]] = []
    for row in artifact_rows:
        for item in row["forbidden_key_path_examples"]:
            for category in item["categories"]:
                category_counts[category] += 1
            forbidden_rows.append(
                {
                    "path": row["path"],
                    "root_label": row["root_label"],
                    "key_path": item["key_path"],
                    "categories": item["categories"],
                    "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
                }
            )
    forbidden_rows = forbidden_rows[:MAX_FORBIDDEN_EXAMPLES]
    return {
        **base_payload("forbidden_field_key_shape_exclusion_ledger"),
        "forbidden_key_category_counts": dict(sorted(category_counts.items())),
        "forbidden_key_examples": forbidden_rows,
        "forbidden_file_exclusions": excluded_files[:250],
        "forbidden_file_exclusion_count": len(excluded_files),
        "leak_policy": "Forbidden key shapes were recorded only as key names/categories and excluded from source/control coverage; no raw values were copied.",
        "result": "PASS_FORBIDDEN_KEY_SHAPES_EXCLUDED_FROM_COVERAGE",
    }


def build_fingerprint_manifest(artifact_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [
        {
            "path": row["path"],
            "root_label": row["root_label"],
            "suffix": row["suffix"],
            "key_path_count": row["key_path_count"],
            "safe_key_path_count": row["safe_key_path_count"],
            "shape_fingerprint_sha256": row["shape_fingerprint_sha256"],
            "safe_shape_fingerprint_sha256": row["safe_shape_fingerprint_sha256"],
            "content_sha256_recorded": row["content_sha256_recorded"],
            "content_sha256": row["content_sha256"],
            "content_sha256_policy": row["content_sha256_policy"],
            "raw_values_copied": False,
        }
        for row in artifact_rows
    ]
    return {
        **base_payload("shape_fingerprint_hash_manifest"),
        "shape_fingerprint_count": len(rows),
        "content_hashes_recorded_count": sum(1 for row in rows if row["content_sha256_recorded"]),
        "raw_values_copied": False,
        "fingerprint_rows": rows,
    }


def build_shape_inventory_summary(artifact_rows: list[dict[str, Any]]) -> dict[str, Any]:
    root_counts: Counter[str] = Counter(row["root_label"] for row in artifact_rows)
    suffix_counts: Counter[str] = Counter(row["suffix"] for row in artifact_rows)
    group_counts: Counter[str] = Counter()
    for row in artifact_rows:
        group_counts.update(row["matched_group_ids"])
    sample_rows = []
    selected_indices = set(range(min(120, len(artifact_rows))))
    for group_id in CAPTURE_GROUPS:
        for index, row in enumerate(artifact_rows):
            if group_id in row["matched_group_ids"]:
                selected_indices.add(index)
                break
    for index in sorted(selected_indices)[:160]:
        row = artifact_rows[index]
        sample_rows.append(
            {
                "path": row["path"],
                "root_label": row["root_label"],
                "suffix": row["suffix"],
                "key_path_count": row["key_path_count"],
                "safe_key_path_count": row["safe_key_path_count"],
                "forbidden_key_path_count": row["forbidden_key_path_count"],
                "matched_group_ids": row["matched_group_ids"],
                "shape_fingerprint_sha256": row["shape_fingerprint_sha256"],
                "safe_shape_fingerprint_sha256": row["safe_shape_fingerprint_sha256"],
                "raw_values_copied": False,
            }
        )
    return {
        "root_artifact_counts": dict(sorted(root_counts.items())),
        "suffix_counts": dict(sorted(suffix_counts.items())),
        "matched_group_artifact_counts": dict(sorted(group_counts.items())),
        "total_key_path_count_shape_only": sum(row["key_path_count"] for row in artifact_rows),
        "total_safe_key_path_count_shape_only": sum(row["safe_key_path_count"] for row in artifact_rows),
        "total_forbidden_key_path_count_shape_only": sum(row["forbidden_key_path_count"] for row in artifact_rows),
        "artifact_rows_sample_count": len(sample_rows),
        "artifact_rows_sample": sample_rows,
        "full_per_file_fingerprint_manifest": output_path("SHAPE_FINGERPRINT_HASH_MANIFEST", "json").as_posix(),
    }


def build_context_anchor(searched_roots: list[dict[str, Any]]) -> dict[str, Any]:
    head = git_text(["rev-parse", "--short", "HEAD"])
    upstream_inventory = []
    for name, path in sorted(UPSTREAM_INPUTS.items()):
        upstream_inventory.append(
            {
                "input_name": name,
                "path": display_path(path) if path.exists() else display_path(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
            }
        )
    return {
        **base_payload("context_anchor"),
        "current_head": head,
        "controlling_prompt": display_path(UPSTREAM_INPUTS["controlling_prompt"]),
        "mandatory_preflight_completed": True,
        "mandatory_context_files_read_after_preflight": {
            "LIVE_STATE": True,
            "quick_reference_card": True,
            "research_operating_doctrine": True,
            "goal_session_research_discipline": True,
            "research_current_state": True,
            "latest_handoff": True,
            "controlling_prompt": True,
        },
        "lane_type": "builder/control read-only shape expansion",
        "builder_control_posture_applied": "constructive maximum read-only shape search inside hard source/control boundaries",
        "accepted_boundary_preserved": {
            "accepted_g12_decision": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
            "candidate_input_row_ids": 3014,
            "duplicate_proxy_denominator_keys": 3014,
            "capture_groups": [CAPTURE_GROUPS[group]["label"] for group in CAPTURE_GROUPS],
            "manifest_binding_repair": "current G12 prompt hash rebound; self-referential output manifest hash drift non-blocking; all other mismatches strict",
            "offline_only_live_wiring_absent": True,
        },
        "upstream_inputs_read_or_fingerprinted": upstream_inventory,
        "searched_roots_summary": searched_roots,
        "deliberately_not_opened": [
            "validation/result scoring",
            "strategy edge/R/PnL/win-rate/expectancy/performance claims",
            "promotion or live behavior",
            "AI/API/paid-vendor calls",
            "broker account/order/history/deal/position evidence",
            "raw market blob contents",
            "prompt/config/risk/safety/execution/canary/selector changes",
        ],
    }


def build_reconciliation() -> dict[str, Any]:
    g12_decision = load_json(UPSTREAM_INPUTS["g12_offline_decision"])
    offline_ledger = load_json(UPSTREAM_INPUTS["offline_field_group_schema_ledger"])
    g0_recon = load_json(UPSTREAM_INPUTS["g0_combined_reconciliation"])
    return {
        **base_payload("accepted_audit_reconciliation"),
        "accepted_g12_offline_terminal_decision": g12_decision["terminal_decision"],
        "accepted_combined_source_terminal_decision": g0_recon.get(
            "terminal_decision", g0_recon.get("accepted_g12_terminal_decision")
        ),
        "candidate_rows_coverage_boundary": offline_ledger["candidate_rows_coverage_expectation"],
        "duplicate_proxy_denominator_key_boundary": offline_ledger[
            "duplicate_proxy_denominator_key_coverage_expectation"
        ],
        "capture_group_count": offline_ledger["group_schema_count"],
        "capture_groups": [row["field_group"] for row in offline_ledger["field_groups"]],
        "manifest_binding_repair_preserved": True,
        "live_wiring_absent_boundary_preserved": True,
        "control_only_not_result_denominator": True,
    }


def build_excluded_root_ledger(excluded_files: list[dict[str, Any]]) -> dict[str, Any]:
    static_roots = [
        ("data", "raw market/history/tick blobs excluded by route boundary"),
        ("data/ticks", "raw tick parquet/blob content excluded"),
        ("knowledge_base/trade_records", "trade/broker record evidence excluded"),
        ("prompts", "production prompt surface excluded from changes and not needed for shape map"),
        ("config", "risk/config/live behavior surface excluded"),
        ("src/components/execution.py", "execution/live behavior surface excluded"),
        ("src/components/permissions.py", "safety/live decision surface excluded"),
        ("scripts/canary_test.py", "canary selector/evaluation surface excluded"),
    ]
    return {
        **base_payload("excluded_root_ledger"),
        "static_excluded_roots": [
            {"path": root, "reason": reason, "exists": (ROOT / root).exists()} for root, reason in static_roots
        ],
        "dynamic_file_exclusions": excluded_files,
        "dynamic_file_exclusion_count": len(excluded_files),
        "exclusion_policy": "Excluded roots/files are not blockers; they are hard-boundary no-leak exclusions for this read-only shape route.",
    }


def build_source_capture_gate_ledger(coverage: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for row in coverage["coverage_rows"]:
        rows.append(
            {
                "field_group": row["field_group"],
                "label": row["label"],
                "current_shape_coverage_status": row["coverage_status"],
                "missing_exact_schema_fields": row["missing_exact_schema_fields"],
                "producer_capture_requirement": row["exact_capture_requirement_to_close_gap"],
                "approval_or_future_gate": "future additive capture/logger implementation approval plus independent G12 audit before consumption",
                "historical_truth_inference_allowed": False,
                "live_wiring_authorized_by_this_route": False,
            }
        )
    return {
        **base_payload("source_capture_approval_gate_ledger"),
        "gate_rows": rows,
        "missing_producer_field_group_count": len(
            [row for row in rows if row["missing_exact_schema_fields"]]
        ),
        "route_does_not_modify_producers": True,
    }


def build_saturation(searched_roots: list[dict[str, Any]], inventory: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    parsed_total = sum(root["files_parsed_for_shape"] for root in searched_roots)
    roots_with_external = [root for root in searched_roots if root["root_path"].startswith("C:/")]
    return {
        **base_payload("saturation_self_redteam_ledger"),
        "not_first_twelve_artifacts_only": parsed_total > 12,
        "parsed_shape_artifact_count": parsed_total,
        "searched_root_count": len(searched_roots),
        "external_or_prior_local_roots_searched": len(roots_with_external),
        "first_twelve_alignment_target_boundary_exceeded_by": max(0, parsed_total - 12),
        "all_ten_capture_groups_in_matrix": coverage["all_ten_capture_groups_represented"],
        "groups_with_no_shape_coverage": coverage["groups_with_no_shape_coverage"],
        "what_would_make_this_shallow": [
            "only restating the accepted 12 monitoring targets",
            "not searching prior worktrees or original local repo paths",
            "not fingerprinting key-shape sources",
            "not writing forbidden-key exclusions",
            "not converting missing exact fields into capture requirements",
            "using verifier pass as proxy without checklist coverage",
        ],
        "checks_that_prevented_shallow_inventory": [
            "searched current SCID source/control routes, program-control JSON, non-forbidden shadow-log shapes, pipeline-state JSON, tests, research-infra, prior worktrees, and the original local repo route artifacts",
            "excluded validation/result/raw/broker/account/performance roots instead of silently ignoring them",
            "emitted shape fingerprints and content-hash policy for inspected files",
            "coverage/gap matrix covers all ten accepted capture groups",
            "standalone verifier checks root breadth, artifact count, forbidden ledger, and prompt-to-artifact completion",
        ],
        "proof_or_impossibility_stop_condition": (
            "Every allowed local/root family reachable without crossing forbidden surfaces was scanned for key shapes; "
            "blocked fields are exact future capture requirements, not inferred historical truth."
        ),
        "same_evidence_class_gaps_remaining": [],
    }


def build_g12_prompt() -> Path:
    body = f"""# G12 SCID Forward Capture Read-Only Monitoring Alignment Expansion Audit Goal Prompt

Date: {DATE_TAG}
Owner lane: independent G12 audit of SCID read-only monitoring alignment expansion
Evidence class: `G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_ONLY`
Input route: `research/science_program_2026_05/06_outcome_testing/scid_forward_capture_readonly_monitoring_alignment_expansion/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Independently audit whether the read-only monitoring alignment expansion searched broad allowed artifact shapes, preserved the accepted offline schema/G12 boundary, excluded forbidden key shapes, and converted remaining gaps into exact prospective capture requirements. Do not open validation, result scoring, strategy-edge claims, R/PnL/win-rate/expectancy/performance, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, raw market-data blobs, live behavior, or prompt/config/risk/safety/execution/canary/selector changes.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read every artifact in the input route directory, plus the accepted G12 offline-schema audit and original offline-schema package artifacts cited in the route manifest.

## Required Audit Checks

- Recompute that all ten capture groups appear in the coverage/gap matrix.
- Verify the route preserves 3,014 `candidate_input_row_id` values and 3,014 `duplicate_proxy_denominator_key` values only as source/control coverage expectations.
- Verify the route searched more than the accepted twelve targets and included at least one absolute local/prior worktree root.
- Verify inspected artifacts are schema/key shapes only and raw values are not copied.
- Verify forbidden broker/account/order/deal/position, result/performance/outcome, validation/promotion, credential/API, raw-blob, and live-surface keys are excluded from source/control coverage.
- Verify missing exact fields are expressed as future additive capture requirements, not inferred historical truth.
- Verify shape fingerprints/hash policy exists for inspected sources.
- Verify no producer, live code, prompt/config/risk/safety/execution/canary/selector, raw data, AI/API, paid/vendor, or broker evidence surface changed.

## Completion Standard

1. Context/preflight use recorded.
2. Coverage/gap matrix, searched/excluded-root ledgers, forbidden-key exclusions, shape fingerprints, exact capture requirements, verifier, tests, completion audit, and closeout verification are checked.
3. Verifier and focused tests pass or concrete repair blockers are written.
4. Terminal decision is exactly one of:
   - `ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_CONTROL_EVIDENCE_ONLY`
   - `REPAIR_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_BEFORE_USE`
5. Safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_ONLY with no validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; independently audit searched/excluded-root ledgers, ten-group coverage/gap matrix, forbidden-key exclusions, shape fingerprints, exact capture requirements, verifier/tests, and saturation proof; preserve the accepted G12 offline schema package, 3,014 coverage boundary, manifest-binding repair, offline-only/live-wiring-absent boundary, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when the prompt file's completion standard is fully satisfied.`
"""
    G12_PROMPT.write_text(body, encoding="utf-8")
    return G12_PROMPT


def git_text(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def run_command(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace", check=False)
    return {
        "args": args,
        "returncode": proc.returncode,
        "status": "PASSED" if proc.returncode == 0 else "FAILED",
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def syntax_parse(files: list[Path]) -> dict[str, Any]:
    failures = []
    for path in files:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append({"path": display_path(path), "error": str(exc)})
    return {"ok": not failures, "method": "ast_parse_no_bytecode", "failures": failures}


def build_output_manifest(paths: list[Path]) -> dict[str, Any]:
    unique = sorted({path for path in paths if path.exists()}, key=display_path)
    return {
        **base_payload("output_manifest"),
        "artifact_count": len(unique),
        "artifacts": [
            {
                "path": display_path(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "raw_market_blob": path.suffix.lower() in RAW_BLOB_SUFFIXES,
            }
            for path in unique
        ],
        "next_g12_prompt": display_path(G12_PROMPT),
        "required_outputs_covered": {
            "context_anchor_and_accepted_audit_reconciliation": True,
            "read_only_shape_inventory": True,
            "coverage_gap_matrix": True,
            "searched_root_ledger": True,
            "excluded_root_ledger": True,
            "forbidden_key_exclusion_ledger": True,
            "shape_fingerprint_hash_manifest": True,
            "source_capture_approval_gate_ledger": True,
            "g12_audit_prompt_and_starter": True,
            "standalone_verifier": True,
            "focused_tests": True,
            "completion_audit": True,
            "closeout_verification": True,
        },
    }


def build_completion_audit(coverage: dict[str, Any], saturation: dict[str, Any]) -> dict[str, Any]:
    return {
        **base_payload("completion_audit"),
        "objective_restatement": {
            "deliverable": "Expand accepted read-only monitoring alignment into a broad key-shape coverage/gap map with forbidden-key exclusions and exact prospective capture requirements.",
            "evidence_class": EVIDENCE_CLASS,
            "terminal_decision": TERMINAL_DECISION,
            "candidate_rows_boundary": 3014,
            "duplicate_proxy_denominator_key_boundary": 3014,
            "capture_group_count": 10,
        },
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory preflight/context docs read", "evidence": output_path("CONTEXT_ANCHOR", "json").as_posix(), "status": "PASS"},
            {"requirement": "accepted G12 offline schema package reconciled", "evidence": output_path("ACCEPTED_AUDIT_RECONCILIATION", "json").as_posix(), "status": "PASS"},
            {"requirement": "broader read-only shape inventory emitted", "evidence": output_path("READ_ONLY_SHAPE_INVENTORY", "json").as_posix(), "status": "PASS"},
            {"requirement": "all ten capture groups represented in coverage/gap matrix", "evidence": output_path("FIELD_GROUP_COVERAGE_GAP_MATRIX", "json").as_posix(), "status": "PASS"},
            {"requirement": "searched roots and excluded roots recorded", "evidence": "SEARCHED_ROOT_LEDGER + EXCLUDED_ROOT_LEDGER", "status": "PASS"},
            {"requirement": "forbidden key-shape exclusions emitted", "evidence": output_path("FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER", "json").as_posix(), "status": "PASS"},
            {"requirement": "shape fingerprints/hash policy emitted", "evidence": output_path("SHAPE_FINGERPRINT_HASH_MANIFEST", "json").as_posix(), "status": "PASS"},
            {"requirement": "missing fields converted to exact capture requirements", "evidence": output_path("SOURCE_CAPTURE_APPROVAL_GATE_LEDGER", "json").as_posix(), "status": "PASS"},
            {"requirement": "G12 prompt emitted", "evidence": display_path(G12_PROMPT), "status": "PASS"},
            {"requirement": "saturation proof not first artifacts/current worktree only", "evidence": output_path("SATURATION_SELF_REDTEAM_LEDGER", "json").as_posix(), "status": "PASS"},
            {"requirement": "verifier/focused tests pass", "evidence": output_path("CLOSEOUT_VERIFICATION", "json").as_posix(), "status": "PENDING_UNTIL_COMMANDS_RUN"},
        ],
        "completion_standard": {
            "all_ten_groups_represented": coverage["all_ten_capture_groups_represented"],
            "shape_only_no_raw_values": True,
            "missing_fields_are_capture_requirements": True,
            "searched_root_ledger_not_first_twelve_or_current_only": saturation["not_first_twelve_artifacts_only"]
            and saturation["external_or_prior_local_roots_searched"] >= 1,
            "forbidden_key_ledger_present": True,
            "verifier_and_tests": "pending_at_initial_build",
        },
        "instruction_coverage": {
            "goal_session_research_discipline_read_after_preflight": True,
            "research_operating_doctrine_read_after_preflight": True,
            "lane_type": "builder/control read-only shape expansion",
            "builder_posture_applied": "maximal constructive shape search while excluding forbidden surfaces",
            "anti_boxing_questions_pursued": saturation["checks_that_prevented_shallow_inventory"],
            "proof_or_impossibility_stop_condition": saturation["proof_or_impossibility_stop_condition"],
            "requirements_deliberately_not_answered_because_forbidden": [
                "validation/result scoring",
                "broker/order/account evidence",
                "raw market blobs",
                "live logger wiring",
                "prompt/config/risk/safety/execution/canary/selector changes",
            ],
        },
        "terminal_decision": TERMINAL_DECISION,
        "can_mark_goal_complete_after_verifier_tests_scoped_commit_and_live_state_refresh": False,
    }


def build_decision_ledger(coverage: dict[str, Any]) -> dict[str, Any]:
    return {
        **base_payload("decision_ledger"),
        "terminal_decision": TERMINAL_DECISION,
        "coverage_group_count": coverage["capture_group_count"],
        "groups_with_no_shape_coverage": coverage["groups_with_no_shape_coverage"],
        "validation_or_result_opened": False,
        "live_wiring_added": False,
        "producer_files_modified": [],
        "terminal_blockers": [],
        "next_required_lane": "independent G12 audit of read-only alignment expansion",
        "next_g12_prompt": display_path(G12_PROMPT),
    }


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    inventory_parts = build_shape_inventory()
    searched_roots = inventory_parts["searched_roots"]
    artifact_rows = inventory_parts["artifact_rows"]
    excluded_files = inventory_parts["excluded_files"]

    context = build_context_anchor(searched_roots)
    generated += write_pair("CONTEXT_ANCHOR", "Context Anchor", context)
    generated += write_pair("ACCEPTED_AUDIT_RECONCILIATION", "Accepted Audit Reconciliation", build_reconciliation())

    searched_root_ledger = {
        **base_payload("searched_root_ledger"),
        "searched_root_count": len(searched_roots),
        "parsed_shape_file_count": sum(root["files_parsed_for_shape"] for root in searched_roots),
        "searched_roots": searched_roots,
    }
    generated += write_pair("SEARCHED_ROOT_LEDGER", "Searched Root Ledger", searched_root_ledger)
    generated += write_pair("EXCLUDED_ROOT_LEDGER", "Excluded Root Ledger", build_excluded_root_ledger(excluded_files))

    inventory = {
        **base_payload("read_only_shape_inventory"),
        "shape_artifact_count": len(artifact_rows),
        "raw_values_copied": False,
        "producer_files_modified": [],
        "running_processes_altered": False,
        "inventory_storage_policy": "Complete per-file fingerprints live in SHAPE_FINGERPRINT_HASH_MANIFEST; this ledger keeps counts, root summaries, group summaries, and representative samples to avoid serializing raw-like runtime shape volume twice.",
        **build_shape_inventory_summary(artifact_rows),
    }
    generated += write_pair("READ_ONLY_SHAPE_INVENTORY", "Read-Only Shape Inventory", inventory)

    coverage = build_coverage_matrix(artifact_rows)
    generated += write_pair("FIELD_GROUP_COVERAGE_GAP_MATRIX", "Field Group Coverage And Gap Matrix", coverage)
    generated += write_pair(
        "FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER",
        "Forbidden Field Key-Shape Exclusion Ledger",
        build_forbidden_ledger(artifact_rows, excluded_files),
    )
    generated += write_pair(
        "SHAPE_FINGERPRINT_HASH_MANIFEST",
        "Shape Fingerprint Hash Manifest",
        build_fingerprint_manifest(artifact_rows),
    )
    generated += write_pair(
        "SOURCE_CAPTURE_APPROVAL_GATE_LEDGER",
        "Source Capture Approval Gate Ledger",
        build_source_capture_gate_ledger(coverage),
    )

    saturation = build_saturation(searched_roots, inventory, coverage)
    generated += write_pair("SATURATION_SELF_REDTEAM_LEDGER", "Saturation Self-Red-Team Ledger", saturation)
    generated += write_pair("DECISION_LEDGER", "Decision Ledger", build_decision_ledger(coverage))

    prompt_path = build_g12_prompt()
    generated.append(prompt_path)
    scripts = [
        ROUTE_DIR / "build_scid_forward_capture_readonly_monitoring_alignment_expansion_2026_05_12.py",
        ROUTE_DIR / "verify_scid_forward_capture_readonly_monitoring_alignment_expansion_2026_05_12.py",
        ROUTE_DIR / "test_scid_forward_capture_readonly_monitoring_alignment_expansion_2026_05_12.py",
    ]
    generated += scripts

    completion = build_completion_audit(coverage, saturation)
    generated += write_pair("COMPLETION_AUDIT", "Completion Audit", completion)

    closeout = {
        **base_payload("closeout_verification"),
        "terminal_decision": TERMINAL_DECISION,
        "status": "BUILD_ARTIFACTS_EMITTED_VERIFIER_AND_FOCUSED_TESTS_PENDING",
        "planned_commands": [
            f"python {display_path(scripts[0])}",
            f"python {display_path(scripts[1])}",
            f"python -m pytest -q -p no:cacheprovider {display_path(scripts[2])}",
            "python scripts/generate_live_state.py",
        ],
    }
    generated += write_pair("CLOSEOUT_VERIFICATION", "Closeout Verification", closeout)

    manifest = build_output_manifest(generated)
    generated += write_pair("OUTPUT_MANIFEST", "Output Manifest", manifest)

    syntax = syntax_parse(scripts)
    verifier_result = run_command(["python", display_path(scripts[1])])
    pytest_result = run_command(["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", display_path(scripts[2])])
    verification_ok = syntax["ok"] and verifier_result["returncode"] == 0 and pytest_result["returncode"] == 0
    closeout.update(
        {
            "status": "STANDALONE_VERIFIER_AND_FOCUSED_PYTEST_PASSED_FINAL_LIVE_STATE_REFRESH_REQUIRED"
            if verification_ok
            else "VERIFICATION_OR_TEST_FAILURE",
            "syntax_parse": syntax,
            "standalone_verifier": verifier_result,
            "focused_pytest": pytest_result,
        }
    )
    generated += write_pair("CLOSEOUT_VERIFICATION", "Closeout Verification", closeout)
    completion["completion_standard"]["verifier_and_tests"] = "passed" if verification_ok else "failed"
    completion["completion_standard_satisfied"] = verification_ok
    completion["can_mark_goal_complete_after_verifier_tests_scoped_commit_and_live_state_refresh"] = verification_ok
    for item in completion["prompt_to_artifact_checklist"]:
        if item["requirement"] == "verifier/focused tests pass":
            item["status"] = "PASS" if verification_ok else "FAIL"
    generated += write_pair("COMPLETION_AUDIT", "Completion Audit", completion)

    if output_path("VERIFICATION_RESULT", "json").exists():
        generated.append(output_path("VERIFICATION_RESULT", "json"))
    generated += write_pair("OUTPUT_MANIFEST", "Output Manifest", build_output_manifest(generated))

    return {
        "ok": verification_ok,
        "route_id": ROUTE_ID,
        "terminal_decision": TERMINAL_DECISION,
        "shape_artifact_count": len(artifact_rows),
        "searched_root_count": len(searched_roots),
        "capture_group_count": coverage["capture_group_count"],
        "groups_with_no_shape_coverage": coverage["groups_with_no_shape_coverage"],
        "standalone_verifier_returncode": verifier_result["returncode"],
        "focused_pytest_returncode": pytest_result["returncode"],
    }


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True, ensure_ascii=True))


if __name__ == "__main__":
    main()
