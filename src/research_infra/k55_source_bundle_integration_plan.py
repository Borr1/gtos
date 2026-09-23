"""K55 source-bundle integration plan for LTO-031/LTO-032 artifacts.

This is a planning/control artifact only. It summarizes source-manifest outputs
and defines the whitelist/no-leak rules K55 must satisfy before any external
context feature becomes part of a shadow feature vector.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research_infra.k55_ml_shadow import (
    FEATURE_BUNDLE_VERSION as CURRENT_K55_FEATURE_BUNDLE_VERSION,
    FORBIDDEN_FEATURE_KEY_PARTS,
    TARGET_VERSION as CURRENT_K55_TARGET_VERSION,
)
from src.research_infra.lto_source_contract_registry import (
    NO_ACTION_COUNTERS,
    PROMOTION_VERDICT,
    stable_hash,
)

SCHEMA_VERSION = "k55_source_bundle_integration_plan_v1"
STATUS_READY = "K55_SOURCE_BUNDLE_INTEGRATION_PLAN_READY_SHADOW_ONLY"

SOURCE_BUNDLE_ARTIFACTS = (
    {
        "bundle_key": "p0_source_contract_registry",
        "artifact_path": "research/program_control/LTO031_LTO032_SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
        "phase": "P0",
        "k55_role": "SOURCE_CONTRACT_PROVENANCE_ONLY",
    },
    {
        "bundle_key": "p1_free_public_existing_feeds",
        "artifact_path": "research/program_control/LTO031_LTO032_FREE_PUBLIC_SOURCE_MANIFESTS_2026-05-06.json",
        "phase": "P1",
        "k55_role": "FUTURE_EXTERNAL_CONTEXT_SHADOW_ONLY_AFTER_ASOF_ROWS",
    },
    {
        "bundle_key": "p2_databento_credit_replay",
        "artifact_path": "research/program_control/LTO031_LTO032_DATABENTO_CREDIT_REPLAY_MANIFESTS_2026-05-06.json",
        "phase": "P2",
        "k55_role": "FUTURE_ORDERFLOW_CONTEXT_AFTER_ESTIMATE_FETCH_AND_ASOF_CACHE",
    },
    {
        "bundle_key": "p3_sierra_scid_footprint_profile",
        "artifact_path": "research/program_control/LTO031_LTO032_SIERRA_SCID_FOOTPRINT_PROFILE_PLAN_2026-05-06.json",
        "phase": "P3",
        "k55_role": "FUTURE_LOCAL_FOOTPRINT_CONTEXT_AFTER_EXTRACTOR_ROWS",
    },
    {
        "bundle_key": "p4_options_gamma_vrp",
        "artifact_path": "research/program_control/LTO032_OPTIONS_GAMMA_VRP_SOURCE_MANIFESTS_2026-05-06.json",
        "phase": "P4",
        "k55_role": "FUTURE_OPTIONS_VOL_CONTEXT_AFTER_SOURCE_ASOF_ROWS",
    },
)

WHITELISTED_FEATURE_PREFIXES = (
    "source_available__",
    "source_freshness_seconds__",
    "source_status_code__",
    "source_row_age_bars__",
    "context_numeric__",
    "context_flag__",
    "missing_source__",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _file_digest(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    return hashlib.sha256(data).hexdigest()[:32]


def feature_key_forbidden_by_external_bundle_policy(key: str) -> bool:
    lowered = key.lower()
    if not any(lowered.startswith(prefix) for prefix in WHITELISTED_FEATURE_PREFIXES):
        return True
    return any(part in lowered for part in FORBIDDEN_FEATURE_KEY_PARTS)


def artifact_count_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_contract_count": payload.get("source_contract_count"),
        "manifest_count": payload.get("manifest_count"),
        "request_count": payload.get("request_count"),
        "source_row_count": payload.get("source_row_count"),
        "csv_file_count": (payload.get("sierra_inventory") or {}).get("csv_file_count"),
        "validation_issues": payload.get("validation_issues", []),
        "validation_safe_counts": payload.get("validation_safe_counts"),
        "promotion_verdict": payload.get("promotion_verdict"),
        "status": payload.get("status"),
    }


def build_source_bundle_rows(
    repo_root: Path,
    artifacts: tuple[dict[str, str], ...] = SOURCE_BUNDLE_ARTIFACTS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in artifacts:
        path = repo_root / spec["artifact_path"]
        payload = _read_json(path)
        exists = bool(payload)
        validation_issues = payload.get("validation_issues", []) if exists else ["ARTIFACT_MISSING_OR_UNREADABLE"]
        promotion_verdict = payload.get("promotion_verdict") if exists else None
        status = payload.get("status") if exists else "ARTIFACT_MISSING"
        integration_status = "SOURCE_BUNDLE_PLAN_READY_NOT_NUMERIC_FEATURES"
        if not exists:
            integration_status = "SOURCE_BUNDLE_ARTIFACT_MISSING_ACTION_REQUIRED"
        elif validation_issues:
            integration_status = "SOURCE_BUNDLE_ARTIFACT_VALIDATION_ISSUES_ACTION_REQUIRED"
        elif spec["bundle_key"] == "p2_databento_credit_replay":
            integration_status = "SOURCE_BUNDLE_BLOCKED_ESTIMATE_AND_FETCH_REQUIRED"
        elif spec["bundle_key"] == "p3_sierra_scid_footprint_profile":
            integration_status = "SOURCE_BUNDLE_PLAN_READY_EXTRACTOR_ROWS_REQUIRED"
        elif spec["bundle_key"] == "p4_options_gamma_vrp":
            integration_status = "SOURCE_BUNDLE_PLAN_READY_HISTORICAL_SOURCE_BLOCKED"
        elif spec["bundle_key"] == "p1_free_public_existing_feeds":
            integration_status = "SOURCE_BUNDLE_PLAN_READY_ASOF_JOIN_ROWS_REQUIRED"

        rows.append(
            {
                "bundle_key": spec["bundle_key"],
                "phase": spec["phase"],
                "artifact_path": _safe_rel(path, repo_root),
                "artifact_exists": exists,
                "artifact_digest": _file_digest(path),
                "artifact_schema_version": payload.get("schema_version"),
                "artifact_status": status,
                "artifact_promotion_verdict": promotion_verdict,
                "count_summary": artifact_count_summary(payload),
                "k55_role": spec["k55_role"],
                "k55_integration_status": integration_status,
                "k55_provenance_flags_allowed": exists and promotion_verdict == PROMOTION_VERDICT,
                "k55_numeric_feature_allowed": False,
                "required_before_numeric_feature": [
                    "NORMALIZED_ASOF_SOURCE_ROWS_EXIST",
                    "SOURCE_FRESHNESS_POLICY_TESTED",
                    "CANDIDATE_JOIN_FIXTURES_PASS",
                    "FEATURE_KEYS_PASS_EXTERNAL_BUNDLE_WHITELIST",
                    "LABEL_AND_OUTCOME_FIELDS_EXCLUDED",
                ],
                "validation_issues": validation_issues,
            }
        )
    return rows


def stale_artifact_policy_rows() -> list[dict[str, Any]]:
    return [
        {
            "artifact_family": "k54_v2",
            "reuse_allowed": False,
            "status": "REJECTED_STALE_K54_ARTIFACT_NOT_K55_COMPATIBLE",
            "reason": "Archived K54 evidence is not a matching K55 target/feature-bundle artifact.",
        },
        {
            "artifact_family": "k54_v3",
            "reuse_allowed": False,
            "status": "REJECTED_STALE_K54_ARTIFACT_NOT_K55_COMPATIBLE",
            "reason": "K54 v3 failed current promotion gates and its offline feature catalog is not the live K55 bundle.",
        },
        {
            "artifact_family": "k54_v4",
            "reuse_allowed": False,
            "status": "REJECTED_STALE_K54_ARTIFACT_NOT_K55_COMPATIBLE",
            "reason": "K54 v4 architectures failed and cannot be silently reused for K55 inference.",
        },
        {
            "artifact_family": "k55_json_linear",
            "reuse_allowed": True,
            "status": "ALLOWED_ONLY_IF_TARGET_AND_FEATURE_BUNDLE_MATCH",
            "reason": "K55 inference requires matching target_version, feature_bundle_version, numeric weights, threshold, and no-leak keys.",
        },
    ]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for row in payload.get("source_bundle_rows") or []:
        key = str(row.get("bundle_key") or "unknown")
        if row.get("artifact_promotion_verdict") not in {PROMOTION_VERDICT, None}:
            issues.append(f"{key}:PROMOTION_VERDICT_NOT_NO_PROMOTION")
        if row.get("validation_issues"):
            issues.append(f"{key}:ARTIFACT_VALIDATION_ISSUES")
        if row.get("k55_numeric_feature_allowed") is True:
            issues.append(f"{key}:NUMERIC_FEATURE_ALLOWED_BEFORE_ASOF_ROWS")
        if row.get("k55_provenance_flags_allowed") and row.get("artifact_exists") is not True:
            issues.append(f"{key}:PROVENANCE_ALLOWED_WITHOUT_ARTIFACT")
    for row in payload.get("stale_artifact_policy") or []:
        family = str(row.get("artifact_family") or "unknown")
        if family.startswith("k54") and row.get("reuse_allowed") is True:
            issues.append(f"{family}:STALE_K54_REUSE_ALLOWED")
    for key in payload.get("example_forbidden_feature_keys") or []:
        if not feature_key_forbidden_by_external_bundle_policy(key):
            issues.append(f"{key}:FORBIDDEN_EXAMPLE_NOT_REJECTED")
    for key in payload.get("example_allowed_feature_keys") or []:
        if feature_key_forbidden_by_external_bundle_policy(key):
            issues.append(f"{key}:ALLOWED_EXAMPLE_REJECTED")
    return issues


def build_payload(
    *,
    repo_root: Path,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    rows = build_source_bundle_rows(repo_root)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated,
        "status": STATUS_READY,
        "promotion_verdict": PROMOTION_VERDICT,
        "scope": "P5 K55 source-bundle integration plan only; no K55 inference or live behavior change",
        "current_k55_target_version": CURRENT_K55_TARGET_VERSION,
        "current_k55_feature_bundle_version": CURRENT_K55_FEATURE_BUNDLE_VERSION,
        "proposed_external_context_bundle_version": "k55_external_context_source_bundle_v1_lto031_lto032_asof_plan_2026_05_06",
        "source_bundle_rows": rows,
        "source_bundle_count": len(rows),
        "source_bundle_ready_for_numeric_features": 0,
        "whitelisted_feature_prefixes": list(WHITELISTED_FEATURE_PREFIXES),
        "example_allowed_feature_keys": [
            "source_available__p1_free_public_existing_feeds",
            "source_freshness_seconds__flashalpha_basic_gex_forward_proxy",
            "context_flag__vix1d_vix9d_missing_required_terms",
            "missing_source__official_or_historical_aggregate_gex",
        ],
        "example_forbidden_feature_keys": [
            "broker_actual_r__p1_free_public_existing_feeds",
            "context_numeric__future_outcome_r",
            "path_label__databento_replay",
            "source_available_unprefixed",
        ],
        "stale_artifact_policy": stale_artifact_policy_rows(),
        "integration_rules": [
            "External context features must join by candidate_id, decision_time_utc/asof_cutoff_utc, source publication timestamp, and source dependency signature.",
            "Missing or blocked sources are encoded as availability/provenance flags, not fabricated numeric values.",
            "Post-decision labels, broker actual-R, synthetic path-R, path labels, PnL, and outcome fields are excluded from feature vectors.",
            "No stale K54 artifact can be reused unless converted into a K55 artifact with matching target and feature-bundle versions.",
            "K55 remains shadow-only until a separate promotion dossier exists.",
        ],
        "dependency_signature": stable_hash(rows, CURRENT_K55_TARGET_VERSION, CURRENT_K55_FEATURE_BUNDLE_VERSION),
        **NO_ACTION_COUNTERS,
    }
    payload["validation_issues"] = validate_payload(payload)
    if payload["validation_issues"]:
        payload["status"] = "K55_SOURCE_BUNDLE_INTEGRATION_PLAN_ACTION_REQUIRED"
    return payload


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value).replace("|", "/")
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True).replace("|", "/")
    return str(value).replace("|", "/")


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_fmt(item) for item in row) + " |")
    return out


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# K55 Source Bundle Integration Plan - 2026-05-06",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Generated:** `{payload['generated_at_utc']}`",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Purpose",
        "",
        (
            "P5 K55 source-bundle plan for LTO-031/LTO-032 artifacts. It defines the source-bundle whitelist, "
            "as-of provenance rules, freshness gates, and stale-K54 rejection policy before any external context "
            "becomes a K55 numeric feature."
        ),
        "",
        "No inference, retrain, model selection, live selector, prompt, risk, execution, or order behavior changed.",
        "",
        "## Source Bundles",
        "",
        *_table(
            ["Bundle", "Phase", "Artifact status", "K55 status", "Provenance flags", "Numeric feature"],
            [
                [
                    row["bundle_key"],
                    row["phase"],
                    row["artifact_status"],
                    row["k55_integration_status"],
                    row["k55_provenance_flags_allowed"],
                    row["k55_numeric_feature_allowed"],
                ]
                for row in payload["source_bundle_rows"]
            ],
        ),
        "",
        "## Feature Key Policy",
        "",
        f"- Whitelisted prefixes: `{payload['whitelisted_feature_prefixes']}`",
        f"- Allowed examples: `{payload['example_allowed_feature_keys']}`",
        f"- Rejected examples: `{payload['example_forbidden_feature_keys']}`",
        "",
        "## Stale Artifact Policy",
        "",
        *_table(
            ["Artifact family", "Reuse allowed", "Status", "Reason"],
            [
                [row["artifact_family"], row["reuse_allowed"], row["status"], row["reason"]]
                for row in payload["stale_artifact_policy"]
            ],
        ),
        "",
        "## Integration Rules",
        "",
        *[f"- {item}" for item in payload["integration_rules"]],
        "",
        "## Validation",
        "",
        f"- Validation issues: `{payload['validation_issues']}`",
        f"- Numeric-ready source bundles: `{payload['source_bundle_ready_for_numeric_features']}`",
        "",
        "## Safety Counters",
        "",
        f"- AI calls: `{payload['ai_calls']}`",
        f"- Canary calls: `{payload['canary_calls']}`",
        f"- Order calls: `{payload['order_calls']}`",
        f"- Paid data calls: `{payload['paid_data_calls']}`",
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "This is a K55 shadow-source integration plan only.",
    ]
    return "\n".join(lines) + "\n"


def render_operations_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# K55 Source Bundle Integration Plan Result - 2026-05-06",
        "",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Result",
        "",
        (
            "P5 K55 source-bundle integration plan is registered. The new LTO-031/LTO-032 source artifacts are "
            "allowed as provenance/freshness context only; no numeric external-source feature is K55-ready yet."
        ),
        "",
        "## Counts",
        "",
        f"- Source bundles: `{payload['source_bundle_count']}`",
        f"- Numeric-ready source bundles: `{payload['source_bundle_ready_for_numeric_features']}`",
        f"- Validation issues: `{payload['validation_issues']}`",
        "",
        "## Boundaries",
        "",
        "- External context must join as-of with source dependency signatures and freshness fields.",
        "- Missing or blocked sources become explicit provenance/missing-source flags.",
        "- Broker actual-R, synthetic path-R, path labels, PnL, and outcomes remain excluded from feature vectors.",
        "- Stale K54 v2/v3/v4 artifacts are rejected for direct K55 reuse.",
        "- No live behavior changed.",
        "",
        "## Verification",
        "",
        "- `python -m py_compile src/research_infra/k55_source_bundle_integration_plan.py scripts/build_k55_source_bundle_integration_plan.py`",
        "- `python -m pytest tests/test_k55_source_bundle_integration_plan.py -q -p no:cacheprovider --basetemp C:\\tmp\\pytest_phase3_k55_source_bundle_plan`",
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "This is source-bundle governance for future K55 shadow work only.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(payload: dict[str, Any], output_json: Path, output_md: Path, operations_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    operations_md.parent.mkdir(parents=True, exist_ok=True)
    operations_md.write_text(render_operations_summary(payload), encoding="utf-8")
