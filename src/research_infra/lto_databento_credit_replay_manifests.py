"""P2 Databento historical-credit replay manifests for LTO-031/LTO-032.

This module creates request contracts and local-cache inventory only. It does
not call Databento, estimate vendor cost, fetch data, start live collectors,
call AI/canaries/MT5, place orders, or change live behavior.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research_infra.lto_source_contract_registry import (
    PROMOTION_VERDICT,
    NO_ACTION_COUNTERS,
)

SCHEMA_VERSION = "lto031_lto032_databento_credit_replay_manifests_v1"
STATUS_READY = "DATABENTO_CREDIT_REPLAY_MANIFESTS_READY_ESTIMATE_REQUIRED"
DATASET = "GLBX.MDP3"
CREDIT_POLICY = {
    "use_existing_credits_only": True,
    "no_new_cash_spend": True,
    "estimate_before_fetch": True,
    "initial_total_credit_cap_usd": 25.0,
    "initial_daily_credit_cap_usd": 8.0,
    "initial_per_request_cap_usd": 1.0,
    "schema_order": ["trades", "mbp-10", "mbo"],
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(*parts: Any) -> str:
    payload = "|".join(json.dumps(part, sort_keys=True, default=str) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _parse_databento_filename(path: Path) -> dict[str, str] | None:
    # GLBX.MDP3.mbp-10.NQ.v.0.2026-04-28T..._2026-...full.dbn.zst
    name = path.name
    prefix = f"{DATASET}."
    if not name.startswith(prefix) or not name.endswith(".dbn.zst"):
        return None
    rest = name[len(prefix) : -len(".full.dbn.zst")]
    parts = rest.split(".")
    if len(parts) < 5:
        return None
    schema = parts[0]
    remainder = ".".join(parts[1:])
    marker = ".20"
    idx = remainder.find(marker)
    if idx == -1:
        return None
    symbols = remainder[:idx].strip(".")
    window = remainder[idx + 1 :]
    return {"schema": schema, "symbols": symbols, "window": window}


def inventory_databento_raw(raw_root: Path, *, repo_root: Path) -> dict[str, Any]:
    files = [path for path in raw_root.rglob("*.dbn.zst") if path.is_file()] if raw_root.exists() else []
    meta_files = [path for path in raw_root.rglob("*.meta.json") if path.is_file()] if raw_root.exists() else []
    by_schema: Counter[str] = Counter()
    by_symbol: Counter[str] = Counter()
    by_schema_symbol: Counter[str] = Counter()
    latest: list[dict[str, Any]] = []
    total_bytes = 0
    for path in files:
        total_bytes += path.stat().st_size
        parsed = _parse_databento_filename(path)
        if not parsed:
            continue
        by_schema[parsed["schema"]] += 1
        by_symbol[parsed["symbols"]] += 1
        by_schema_symbol[f"{parsed['schema']}:{parsed['symbols']}"] += 1
    for path in sorted(files, key=lambda item: item.stat().st_mtime, reverse=True)[:12]:
        parsed = _parse_databento_filename(path) or {}
        latest.append(
            {
                "path": _safe_rel(path, repo_root),
                "size_bytes": path.stat().st_size,
                "schema": parsed.get("schema"),
                "symbols": parsed.get("symbols"),
            }
        )
    return {
        "raw_root": _safe_rel(raw_root, repo_root),
        "raw_file_count": len(files),
        "metadata_file_count": len(meta_files),
        "total_size_mb": round(total_bytes / (1024 * 1024), 6),
        "files_by_schema": dict(sorted(by_schema.items())),
        "files_by_symbol": dict(sorted(by_symbol.items())),
        "files_by_schema_symbol": dict(sorted(by_schema_symbol.items())),
        "latest_files": latest,
    }


def _request(
    request_id: str,
    *,
    priority: int,
    gtos_symbol: str,
    raw_symbols: list[str],
    schema: str,
    status: str = "WAITING_FOR_COST_ESTIMATE",
    caveats: list[str] | None = None,
) -> dict[str, Any]:
    estimate_ready = False
    fetch_allowed = False
    return {
        "request_id": request_id,
        "priority": priority,
        "dataset": DATASET,
        "schema": schema,
        "stype_in": "continuous",
        "gtos_symbol": gtos_symbol,
        "raw_symbols": raw_symbols,
        "window_template": {
            "start_utc": "DYNAMIC_CANDIDATE_DECISION_TIME_MINUS_60M_UTC",
            "decision_cutoff_utc": "DYNAMIC_CANDIDATE_DECISION_TIME_UTC",
            "end_utc": "DYNAMIC_CANDIDATE_DECISION_TIME_PLUS_15M_UTC",
        },
        "decision_time_feature_policy": (
            "Feature extraction may read only records with ts_event <= decision_cutoff_utc. "
            "Records after decision_cutoff_utc are post-event labels only."
        ),
        "post_event_label_policy": (
            "Post-decision rows may label fill/no-fill, adverse excursion, and synthetic path diagnostics, "
            "but must not be mixed into decision-time features."
        ),
        "estimated_cost_usd": None,
        "estimate_ready": estimate_ready,
        "fetch_allowed": fetch_allowed,
        "fetch_blockers": [
            "VENDOR_COST_ESTIMATE_NOT_RUN",
            "MANIFEST_ONLY_NO_FETCH_IN_THIS_PHASE",
            "OWNER_APPROVAL_REQUIRED_BEFORE_ANY_NEW_CASH_OR_LIVE_COLLECTOR",
            *(caveats or []),
        ],
        "per_request_cap_usd": CREDIT_POLICY["initial_per_request_cap_usd"],
        "status": status,
        "promotion_verdict": PROMOTION_VERDICT,
    }


def build_request_templates() -> list[dict[str, Any]]:
    return [
        _request(
            "P2_NAS100_NQ_TRADES_DECISION_WINDOW_V1",
            priority=1,
            gtos_symbol="NAS100",
            raw_symbols=["NQ.v.0"],
            schema="trades",
        ),
        _request(
            "P2_NAS100_NQ_MBP10_DECISION_WINDOW_V1",
            priority=2,
            gtos_symbol="NAS100",
            raw_symbols=["NQ.v.0"],
            schema="mbp-10",
        ),
        _request(
            "P2_US30_YM_ES_MBP10_DECISION_WINDOW_V1",
            priority=3,
            gtos_symbol="US30",
            raw_symbols=["YM.v.0", "ES.v.0"],
            schema="mbp-10",
        ),
        _request(
            "P2_XAUUSD_GC_MBP10_DECISION_WINDOW_V1",
            priority=4,
            gtos_symbol="XAUUSD",
            raw_symbols=["GC.v.0"],
            schema="mbp-10",
        ),
        _request(
            "P2_XAGUSD_SI_MBP10_DECISION_WINDOW_V1",
            priority=5,
            gtos_symbol="XAGUSD",
            raw_symbols=["SI.v.0"],
            schema="mbp-10",
            status="BLOCKED_SOURCE_DEFINITION_BEFORE_ESTIMATE",
            caveats=["SI_SOURCE_DEPTH_DEFINITION_BLOCKED"],
        ),
        _request(
            "P2_USDJPY_6J_TRADES_DECISION_WINDOW_V1",
            priority=6,
            gtos_symbol="USDJPY",
            raw_symbols=["6J.v.0"],
            schema="trades",
            status="BLOCKED_PROXY_TRANSFER_REVIEW_BEFORE_ESTIMATE",
            caveats=["USDJPY_6J_INVERSE_TRANSFER_POLICY_OPEN"],
        ),
        _request(
            "P2_GBPUSD_6B_TRADES_DECISION_WINDOW_V1",
            priority=7,
            gtos_symbol="GBPUSD",
            raw_symbols=["6B.v.0"],
            schema="trades",
            status="BLOCKED_ALIGNMENT_POLICY_BEFORE_ESTIMATE",
            caveats=["GBPUSD_6B_COMMON_SECOND_ALIGNMENT_REQUIRED"],
        ),
        _request(
            "P2_NAS100_NQ_MBO_QUEUE_FOLLOWUP_V1",
            priority=8,
            gtos_symbol="NAS100",
            raw_symbols=["NQ.v.0"],
            schema="mbo",
            status="DEFERRED_UNTIL_MBP10_LEAVES_QUEUE_QUESTION",
            caveats=["MBO_ONLY_AFTER_TRADES_OR_MBP10_UNANSWERED_QUEUE_QUESTION"],
        ),
    ]


def validate_requests(requests: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for row in requests:
        request_id = str(row.get("request_id") or "UNKNOWN")
        if row.get("fetch_allowed") and not row.get("estimate_ready"):
            issues.append(f"{request_id}:FETCH_ALLOWED_WITHOUT_ESTIMATE")
        if row.get("fetch_allowed") and row.get("estimated_cost_usd") is None:
            issues.append(f"{request_id}:FETCH_ALLOWED_WITHOUT_COST")
        estimated = row.get("estimated_cost_usd")
        if estimated is not None and float(estimated) > float(row.get("per_request_cap_usd") or 0):
            issues.append(f"{request_id}:ESTIMATE_EXCEEDS_PER_REQUEST_CAP")
        if row.get("promotion_verdict") != PROMOTION_VERDICT:
            issues.append(f"{request_id}:PROMOTION_VERDICT_NOT_NO_PROMOTION")
        policy = str(row.get("decision_time_feature_policy") or "")
        if "ts_event <= decision_cutoff_utc" not in policy:
            issues.append(f"{request_id}:MISSING_DECISION_CUTOFF_POLICY")
    return issues


def build_payload(
    *,
    repo_root: Path,
    raw_root: Path | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    raw = raw_root or (repo_root / "data/external/raw/databento")
    inventory = inventory_databento_raw(raw, repo_root=repo_root)
    requests = build_request_templates()
    issues = validate_requests(requests)
    status_counts = Counter(row["status"] for row in requests)
    schema_counts = Counter(row["schema"] for row in requests)
    fetch_ready = sum(1 for row in requests if row["fetch_allowed"])
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated,
        "status": STATUS_READY if not issues else "DATABENTO_CREDIT_REPLAY_MANIFESTS_ACTION_REQUIRED",
        "promotion_verdict": PROMOTION_VERDICT,
        "scope": "P2 Databento historical-credit replay manifests and local-cache inventory only",
        "credit_policy": CREDIT_POLICY,
        "live_collector_enabled": False,
        "request_count": len(requests),
        "request_status_counts": dict(sorted(status_counts.items())),
        "request_schema_counts": dict(sorted(schema_counts.items())),
        "fetch_ready_count": fetch_ready,
        "validation_issues": issues,
        "local_databento_inventory": inventory,
        "requests": requests,
        "source_separation_policy": {
            "decision_time_features": "records with ts_event <= decision_cutoff_utc only",
            "post_event_labels": "records after decision_cutoff_utc used only for labels/outcome diagnostics",
            "actual_r": "broker actual-R remains separate from synthetic path-R",
            "historical_replay": "evidence for live-subscription value, not live operational validation",
        },
        "next_allowed_command_template": (
            "python scripts/fetch_databento_manifest.py --schema {schema} "
            "--max-group-cost-usd 1 --max-total-cost-usd 8"
        ),
        "dependency_signature": stable_hash(requests, inventory),
        **NO_ACTION_COUNTERS,
    }
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
    inventory = payload["local_databento_inventory"]
    lines = [
        "# LTO031 / LTO032 Databento Credit Replay Manifests - 2026-05-06",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Generated:** `{payload['generated_at_utc']}`",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Purpose",
        "",
        (
            "P2 Databento historical-credit replay request contracts. Requests are predeclared and intentionally "
            "not fetch-ready until vendor cost estimates exist and caps pass."
        ),
        "",
        "No Databento API call, paid fetch, live collector, AI/canary call, or live trading behavior change occurred.",
        "",
        "## Credit Policy",
        "",
        f"- Existing credits only: `{payload['credit_policy']['use_existing_credits_only']}`",
        f"- New external cash: `{not payload['credit_policy']['no_new_cash_spend']}`",
        f"- Estimate before fetch: `{payload['credit_policy']['estimate_before_fetch']}`",
        f"- Total cap: `${payload['credit_policy']['initial_total_credit_cap_usd']}`",
        f"- Daily cap: `${payload['credit_policy']['initial_daily_credit_cap_usd']}`",
        f"- Per-request cap: `${payload['credit_policy']['initial_per_request_cap_usd']}`",
        "",
        "## Local Cache Inventory",
        "",
        f"- Raw files: `{inventory['raw_file_count']}`",
        f"- Metadata files: `{inventory['metadata_file_count']}`",
        f"- Total size MB: `{inventory['total_size_mb']}`",
        f"- Files by schema: `{inventory['files_by_schema']}`",
        "",
        "## Requests",
        "",
        *_table(
            ["Request", "Priority", "GTOS", "Raw symbols", "Schema", "Status", "Fetch ready"],
            [
                [
                    row["request_id"],
                    row["priority"],
                    row["gtos_symbol"],
                    row["raw_symbols"],
                    row["schema"],
                    row["status"],
                    row["fetch_allowed"],
                ]
                for row in payload["requests"]
            ],
        ),
        "",
        "## Source Separation",
        "",
        *[f"- {key}: {value}" for key, value in payload["source_separation_policy"].items()],
        "",
        "## Validation",
        "",
        f"- Fetch-ready requests: `{payload['fetch_ready_count']}`",
        f"- Validation issues: `{payload['validation_issues']}`",
        "",
        "## Safety Counters",
        "",
        f"- Paid data calls: `{payload['paid_data_calls']}`",
        f"- Paid fetch attempted: `{payload['paid_fetch_attempted']}`",
        f"- AI calls: `{payload['ai_calls']}`",
        f"- Order calls: `{payload['order_calls']}`",
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "Historical replay manifests are source planning only and do not promote Databento or any trading rule.",
    ]
    return "\n".join(lines) + "\n"


def render_operations_summary(payload: dict[str, Any]) -> str:
    inventory = payload["local_databento_inventory"]
    lines = [
        "# LTO031 / LTO032 Databento Credit Replay Manifest Result - 2026-05-06",
        "",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Result",
        "",
        (
            "P2 Databento replay requests are predeclared under existing-credit-only caps. "
            "No request is fetch-ready yet because vendor cost estimates were not run in this phase."
        ),
        "",
        "## Counts",
        "",
        f"- Requests: `{payload['request_count']}`",
        f"- Request status counts: `{payload['request_status_counts']}`",
        f"- Request schema counts: `{payload['request_schema_counts']}`",
        f"- Fetch-ready requests: `{payload['fetch_ready_count']}`",
        f"- Local raw Databento files inventoried: `{inventory['raw_file_count']}`",
        f"- Local raw Databento size MB: `{inventory['total_size_mb']}`",
        "",
        "## Boundaries",
        "",
        "- Estimate-before-fetch is enforced by manifest invariants.",
        "- Live Databento collector remains disabled.",
        "- Decision-time features and post-event labels are separated in every request.",
        "- SI/XAGUSD, USDJPY/6J, GBPUSD/6B, and NAS100/MBO queue follow-up retain explicit blockers.",
        "",
        "## Verification",
        "",
        "- `python -m py_compile src/research_infra/lto_databento_credit_replay_manifests.py scripts/build_lto031_lto032_databento_credit_replay_manifests.py`",
        "- `python -m pytest tests/test_lto_databento_credit_replay_manifests.py -q -p no:cacheprovider --basetemp C:\\tmp\\pytest_phase3_lto_databento_credit_manifests`",
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "This is replay planning only. No Databento call or live behavior change occurred.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(payload: dict[str, Any], output_json: Path, output_md: Path, operations_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    operations_md.parent.mkdir(parents=True, exist_ok=True)
    operations_md.write_text(render_operations_summary(payload), encoding="utf-8")
