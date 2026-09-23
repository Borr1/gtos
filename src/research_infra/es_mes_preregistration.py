"""LTO-029 ES/MES strategy-cohort preregistration status.

This lane freezes the ES/MES source mapping, session windows, strategy family,
evidence class, and no-lookahead rules before any outcome opening. It does not
replay outcomes or alter live behavior.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "es_mes_preregistration_status_v1"
REGISTRY_SCHEMA_VERSION = "es_mes_strategy_cohort_registry_v1"
REPORT_SCHEMA_VERSION = "lto029_es_mes_strategy_cohort_preregistration_v1"
LTO_ID = "LTO-029"
FOLLOW_ID = "LIVE-FOLLOW-027"
ACTION_REQUIRED = "ES_MES_PREREGISTRATION_ACTION_REQUIRED"
STATUS_OK = "ES_MES_STRATEGY_COHORT_PREREGISTERED_SOURCE_STATUS_ONLY"

DEFAULT_REGISTRY_PATH = Path("research/program_control/ES_MES_STRATEGY_COHORT_REGISTRY_2026-05-05.json")
DEFAULT_PRIOR_PREREG_PATH = Path("research/program_control/ES_MES_PRE_REGISTRATION_2026-05-04.json")
DEFAULT_CONVERSION_STATUS_PATH = Path(
    "research/program_control/EXPANDED_OOS_FIRST_WAVE_BOUNDED_CONVERSION_STATUS_2026-05-04.json"
)
DEFAULT_LABEL_STATUS_PATH = Path("research/program_control/EXPANDED_OOS_FIRST_WAVE_LABEL_STATUS_AUDIT_2026-05-04.json")
DEFAULT_SIERRA_INVENTORY_PATH = Path("research/program_control/SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.json")

NO_DECISION_COUNTERS = {
    "ai_calls": 0,
    "canary_calls": 0,
    "order_calls": 0,
    "paid_data_calls": 0,
    "paid_fetch_attempted": False,
    "no_ai_calls": True,
    "no_canary_required": True,
    "no_execution": True,
}

OUTCOME_FILE_MARKERS = ("OUTCOME", "OUTCOMES", "REPLAY", "RESULT", "RESULTS", "VALIDATION")
ES_MES_NAME_MARKERS = ("ES_MES", "ES-MES", "ESMES", "SPX_ES", "SPX_MES")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(json.dumps(part, sort_keys=True, default=str) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _source_ref(path: Path | str, payload: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": bool(payload),
        "schema_version": (payload or {}).get("schema_version"),
        "status": (payload or {}).get("status"),
        "promotion_verdict": (payload or {}).get("promotion_verdict"),
    }


def default_registry_payload(generated_at_utc: str | None = None) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "created_at_utc": generated,
        "status": STATUS_OK,
        "scope": "research/tooling only",
        "lto_id": LTO_ID,
        "follow_id": FOLLOW_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "live_trading_behavior_changed": False,
        "family": "ES/MES",
        "registered_question_type": "equity-index context/control plus possible separate strategy family",
        "registered_question": (
            "Can ES/MES provide preregistered equity-index context/control evidence, and later a separate "
            "strategy cohort if event ids and scoring rules are frozen before outcomes?"
        ),
        "strategy_family": "ES_MES_EQUITY_INDEX_CONTEXT_CONTROL",
        "allowed_use": [
            "equity-index context/control around NAS100 and US30 diagnostics",
            "future standalone ES/MES strategy cohort only after a separate frozen event registry exists",
        ],
        "disallowed_use": [
            "direct broker-truth validation for NAS100 or US30",
            "promotion dossier input before broker/source/cost/lifecycle floors are met",
            "outcome mining from existing converted ES/MES rows",
        ],
        "source_mapping": [
            {
                "file_symbol": "SPX_ES",
                "source_symbol": "ESM26-CME",
                "symbol_root": "ES",
                "evidence_class": "FUTURES_PROXY_TRANSFER",
                "allowed_use": "S&P futures proxy/context source; not broker execution truth",
            },
            {
                "file_symbol": "SPX_MES",
                "source_symbol": "MESM26-CME",
                "symbol_root": "MES",
                "evidence_class": "FUTURES_PROXY_TRANSFER",
                "allowed_use": "Micro S&P futures proxy/context source; not broker execution truth",
            },
            {
                "file_symbol": "NAS100_US30_CONTEXT",
                "source_symbol": "ES/MES",
                "symbol_root": "ES_MES_CONTEXT",
                "evidence_class": "CROSS_INSTRUMENT_CONTEXT",
                "allowed_use": "same-session equity-index context only",
            },
        ],
        "session_windows_utc": [
            {
                "window_id": "NY_INDEX_CONTEXT",
                "start_utc": "13:30",
                "end_utc": "16:00",
                "reason": "aligns US30 NY context window; this is a research slice, not an exchange-hours claim",
            },
            {
                "window_id": "NY_BROAD_EQUITY_CONTEXT",
                "start_utc": "13:00",
                "end_utc": "17:00",
                "reason": "aligns broad GTOS NY decision context for future as-of joins",
            },
            {
                "window_id": "LONDON_INDEX_CONTEXT",
                "start_utc": "08:00",
                "end_utc": "10:30",
                "reason": "aligns US30 London context window for cross-index diagnostics",
            },
        ],
        "evidence_classes": ["FUTURES_PROXY_TRANSFER", "CROSS_INSTRUMENT_CONTEXT"],
        "no_lookahead_rules": [
            "Any future feature row must use source events with timestamp <= decision_time_utc/asof_cutoff_utc.",
            "Registry/status rows must not contain TP/SL hits, realized R, synthetic path labels, or replay lift.",
            "Outcome files stay closed until event ids, source files, hashes, session windows, and scoring spec are frozen.",
            "ES/MES evidence must remain labeled as transfer/context evidence, not broker actual-R.",
        ],
        "opened_outcome_slices": [],
        "reserved_holdout": (
            "Outcomes stay closed until event ids, as-of windows, source hashes, control-use rules, and scoring "
            "rules are registered in a later dossier."
        ),
    }


def find_opened_outcome_artifacts(root: Path) -> list[str]:
    search_roots = [root / "research", root / "shadow_logs"]
    matches: list[str] = []
    for search_root in search_roots:
        if not search_root.exists():
            continue
        for path in search_root.rglob("*"):
            if not path.is_file():
                continue
            name = path.name.upper()
            if not any(marker in name for marker in ES_MES_NAME_MARKERS):
                continue
            if any(marker in name for marker in OUTCOME_FILE_MARKERS):
                matches.append(str(path.relative_to(root)))
    return sorted(matches)


def _sierra_symbols(inventory: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    symbols = {}
    for row in (inventory or {}).get("symbols") or []:
        if isinstance(row, dict) and row.get("symbol_root"):
            symbols[str(row["symbol_root"]).upper()] = row
    return symbols


def _sierra_source_status(inventory: dict[str, Any] | None) -> dict[str, Any]:
    by_symbol = _sierra_symbols(inventory)
    watched = {}
    for symbol in ("ES", "MES"):
        row = by_symbol.get(symbol) or {}
        watched[symbol] = {
            "status": row.get("status") or "MISSING_FROM_SIERRA_INVENTORY",
            "scid_file_count": int(row.get("scid_file_count") or 0),
            "depth_file_count": int(row.get("depth_file_count") or 0),
            "latest_scid_utc": row.get("latest_scid_utc"),
            "latest_depth_utc": row.get("latest_depth_utc"),
            "evidence_class": "FUTURES_PROXY_TRANSFER",
        }
    return watched


def _conversion_rows(conversion_status: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows = []
    for row in (conversion_status or {}).get("m15_inventory") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("file_symbol") or "").upper() in {"SPX_ES", "SPX_MES"}:
            rows.append(row)
    return rows


def _label_status(label_status: dict[str, Any] | None) -> dict[str, Any]:
    for row in (label_status or {}).get("families") or []:
        if isinstance(row, dict) and "ES/MES" in str(row.get("family") or ""):
            return row
    return {}


def _gate(gate_id: str, required: str, observed: Any, passed: bool, blocker_code: str) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "required": required,
        "observed": observed,
        "passed": bool(passed),
        "blocker_code": "" if passed else blocker_code,
    }


def build_status_row(
    *,
    root: Path | str = Path("."),
    registry: dict[str, Any] | None = None,
    prior_preregistration: dict[str, Any] | None = None,
    conversion_status: dict[str, Any] | None = None,
    label_status: dict[str, Any] | None = None,
    sierra_inventory: dict[str, Any] | None = None,
    registry_path: Path | str = DEFAULT_REGISTRY_PATH,
    prior_prereg_path: Path | str = DEFAULT_PRIOR_PREREG_PATH,
    conversion_status_path: Path | str = DEFAULT_CONVERSION_STATUS_PATH,
    label_status_path: Path | str = DEFAULT_LABEL_STATUS_PATH,
    sierra_inventory_path: Path | str = DEFAULT_SIERRA_INVENTORY_PATH,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    root_path = Path(root)
    registry = registry or {}
    source_status = _sierra_source_status(sierra_inventory)
    conversion_rows = _conversion_rows(conversion_status)
    label_row = _label_status(label_status)
    registry_outcomes = registry.get("opened_outcome_slices") if isinstance(registry, dict) else []
    if not isinstance(registry_outcomes, list):
        registry_outcomes = []
    opened_artifacts = find_opened_outcome_artifacts(root_path)

    registry_present = bool(registry)
    registry_no_promotion = registry.get("promotion_verdict") == PROMOTION_VERDICT
    behavior_unchanged = registry.get("live_trading_behavior_changed") is False
    source_mapping_complete = {"SPX_ES", "SPX_MES"} <= {str(row.get("file_symbol") or "") for row in registry.get("source_mapping") or []}
    session_windows_complete = len(registry.get("session_windows_utc") or []) >= 2
    no_lookahead_complete = len(registry.get("no_lookahead_rules") or []) >= 3
    evidence_complete = {"FUTURES_PROXY_TRANSFER", "CROSS_INSTRUMENT_CONTEXT"} <= set(registry.get("evidence_classes") or [])
    source_files_ready = len(conversion_rows) == 2 and all(int(row.get("rows") or 0) > 0 for row in conversion_rows)
    sierra_ready = all(item["status"] == "READY_SCID_AND_DEPTH_PRESENT" for item in source_status.values())
    label_closed = (
        label_row.get("label_status") == "LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT"
        or label_row.get("replay_or_label_status") == "LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT"
    )
    outcomes_closed = len(registry_outcomes) == 0 and not opened_artifacts
    no_validation_claim = registry_no_promotion and "validation" not in str(registry.get("status") or "").lower()

    gates = [
        _gate(
            "G0_NO_LIVE_BEHAVIOR_OR_PAID_CALLS",
            "No AI, canary, order, paid-data, execution, prompt, risk, or trading behavior changes.",
            {"behavior_unchanged": behavior_unchanged, **NO_DECISION_COUNTERS},
            behavior_unchanged,
            "LIVE_BEHAVIOR_BOUNDARY_NOT_PROVEN",
        ),
        _gate(
            "G1_REGISTRY_FIELDS_FROZEN",
            "Registry freezes source mapping, session windows, strategy family, evidence classes, and no-lookahead rules.",
            {
                "registry_present": registry_present,
                "source_mapping_complete": source_mapping_complete,
                "session_windows_complete": session_windows_complete,
                "no_lookahead_complete": no_lookahead_complete,
                "evidence_complete": evidence_complete,
                "strategy_family": registry.get("strategy_family"),
            },
            all(
                (
                    registry_present,
                    source_mapping_complete,
                    session_windows_complete,
                    no_lookahead_complete,
                    evidence_complete,
                    bool(registry.get("strategy_family")),
                )
            ),
            "ES_MES_REGISTRY_FIELDS_INCOMPLETE",
        ),
        _gate(
            "G2_OUTCOMES_CLOSED_AT_REGISTRATION",
            "Opened outcome slices and ES/MES outcome/replay/result artifacts must be absent at registration.",
            {
                "opened_outcome_slices_at_registration": len(registry_outcomes),
                "opened_outcome_artifacts": opened_artifacts,
                "label_status": label_row.get("label_status") or label_row.get("replay_or_label_status"),
            },
            outcomes_closed and label_closed,
            "ES_MES_OUTCOMES_OPENED_OR_LABEL_STATUS_NOT_CLOSED",
        ),
        _gate(
            "G3_SOURCE_FILES_READY_FOR_FUTURE_ASOF_ROWS",
            "ES/MES converted rows plus Sierra SCID/depth source status are present before outcome opening.",
            {"conversion_rows": conversion_rows, "sierra_source_status": source_status},
            source_files_ready and sierra_ready,
            "ES_MES_SOURCE_FILES_NOT_READY",
        ),
        _gate(
            "G4_NO_LOOKAHEAD_RULES_EXPLICIT",
            "No-lookahead rules must forbid post-decision outcomes and require as-of cutoffs.",
            {"no_lookahead_rules": registry.get("no_lookahead_rules") or []},
            no_lookahead_complete,
            "ES_MES_NO_LOOKAHEAD_RULES_INCOMPLETE",
        ),
        _gate(
            "G5_NO_PROMOTION_OR_DIRECT_BROKER_TRUTH_CLAIM",
            "ES/MES may be context/control or a future separate cohort only; not direct NAS100/US30 broker truth.",
            {
                "promotion_verdict": registry.get("promotion_verdict"),
                "allowed_use": registry.get("allowed_use") or [],
                "disallowed_use": registry.get("disallowed_use") or [],
            },
            no_validation_claim,
            "ES_MES_PROMOTION_OR_DIRECT_VALIDATION_CLAIM_PRESENT",
        ),
    ]
    failed = [gate for gate in gates if not gate["passed"]]
    action_required_codes = [gate["blocker_code"] for gate in failed if gate["blocker_code"]]
    status = ACTION_REQUIRED if action_required_codes else STATUS_OK
    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        generated.split("T")[0],
        registry,
        prior_preregistration,
        conversion_rows,
        label_row,
        source_status,
        opened_artifacts,
        gates,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("es_mes_preregistration", source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated,
        "backfilled_at_utc": generated,
        "lto_id": LTO_ID,
        "follow_id": FOLLOW_ID,
        "status": status,
        "evidence_class": "CROSS_INSTRUMENT_CONTEXT",
        "promotion_verdict": PROMOTION_VERDICT,
        "registry_ref": _source_ref(registry_path, registry),
        "prior_preregistration_ref": _source_ref(prior_prereg_path, prior_preregistration),
        "conversion_status_ref": _source_ref(conversion_status_path, conversion_status),
        "label_status_ref": _source_ref(label_status_path, label_status),
        "sierra_inventory_ref": _source_ref(sierra_inventory_path, sierra_inventory),
        "registered_question": registry.get("registered_question"),
        "registered_question_type": registry.get("registered_question_type"),
        "strategy_family": registry.get("strategy_family"),
        "source_mapping": registry.get("source_mapping") or [],
        "session_windows_utc": registry.get("session_windows_utc") or [],
        "evidence_classes": registry.get("evidence_classes") or [],
        "no_lookahead_rules": registry.get("no_lookahead_rules") or [],
        "opened_outcome_slices_at_registration": len(registry_outcomes),
        "opened_outcome_slices": registry_outcomes,
        "opened_outcome_artifacts": opened_artifacts,
        "outcome_opening_status": "OUTCOMES_CLOSED" if outcomes_closed else "OUTCOMES_OPENED_ACTION_REQUIRED",
        "conversion_rows": conversion_rows,
        "label_status": label_row,
        "sierra_source_status": source_status,
        "validation_gates": gates,
        "gate_summary": {
            "passed": sum(1 for gate in gates if gate["passed"]),
            "failed": len(failed),
            "failed_gate_ids": [gate["gate_id"] for gate in failed],
            "failed_blocker_codes": action_required_codes,
        },
        "documented_limitation_codes": [],
        "action_required_codes": action_required_codes,
        "claim_boundary": (
            "LTO-029 preregisters ES/MES context/control and future separate-cohort rules only. "
            "It opens no outcomes and cannot validate or promote a strategy."
        ),
        **NO_DECISION_COUNTERS,
    }


def build_report_payload(
    *,
    root: Path | str = Path("."),
    registry: dict[str, Any] | None = None,
    prior_preregistration: dict[str, Any] | None = None,
    conversion_status: dict[str, Any] | None = None,
    label_status: dict[str, Any] | None = None,
    sierra_inventory: dict[str, Any] | None = None,
    registry_path: Path | str = DEFAULT_REGISTRY_PATH,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    row = build_status_row(
        root=root,
        registry=registry,
        prior_preregistration=prior_preregistration,
        conversion_status=conversion_status,
        label_status=label_status,
        sierra_inventory=sierra_inventory,
        registry_path=registry_path,
        generated_at_utc=generated,
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": generated,
        "promotion_verdict": PROMOTION_VERDICT,
        "status": row["status"],
        "registry": registry,
        "status_row": row,
        "completion_evidence": {
            "opened_outcome_slices_at_registration": row["opened_outcome_slices_at_registration"],
            "opened_outcome_artifacts": row["opened_outcome_artifacts"],
            "source_mapping_count": len(row["source_mapping"]),
            "session_window_count": len(row["session_windows_utc"]),
            "no_lookahead_rule_count": len(row["no_lookahead_rules"]),
            "new_ai_calls": 0,
            "new_canary_calls": 0,
            "new_order_calls": 0,
            "new_paid_data_calls": 0,
        },
        "synthesis": {
            "summary": (
                "ES/MES is now preregistered as context/control and future separate-cohort source status only. "
                "Outcome files remain unopened, and every future ES/MES row must be point-in-time/as-of."
            ),
        },
    }


def render_registry_markdown(registry: dict[str, Any]) -> str:
    lines = [
        "# ES/MES Strategy-Cohort Registry - 2026-05-05",
        "",
        f"**Status:** `{registry['status']}`",
        f"**Promotion verdict:** `{registry['promotion_verdict']}`",
        "",
        "## Question",
        "",
        registry["registered_question"],
        "",
        "## Source Mapping",
        "",
        "| File symbol | Source symbol | Evidence class | Allowed use |",
        "|---|---|---|---|",
    ]
    for row in registry["source_mapping"]:
        lines.append(
            f"| `{row['file_symbol']}` | `{row['source_symbol']}` | "
            f"`{row['evidence_class']}` | {row['allowed_use']} |"
        )
    lines.extend(["", "## Session Windows", "", "| Window | UTC | Reason |", "|---|---|---|"])
    for row in registry["session_windows_utc"]:
        lines.append(f"| `{row['window_id']}` | `{row['start_utc']}-{row['end_utc']}` | {row['reason']} |")
    lines.extend(["", "## No-Lookahead Rules", ""])
    lines.extend(f"- {rule}" for rule in registry["no_lookahead_rules"])
    lines.extend(["", "## Boundary", "", f"- Allowed use: `{registry['allowed_use']}`"])
    lines.append(f"- Disallowed use: `{registry['disallowed_use']}`")
    lines.append(f"- Opened outcome slices: `{registry['opened_outcome_slices']}`")
    return "\n".join(lines) + "\n"


def render_markdown(payload: dict[str, Any]) -> str:
    row = payload["status_row"]
    lines = [
        "# LTO029 ES/MES Strategy-Cohort Preregistration - 2026-05-05",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Summary",
        "",
        payload["synthesis"]["summary"],
        "",
        "## Registration",
        "",
        f"- Registered question: `{row['registered_question']}`",
        f"- Strategy family: `{row['strategy_family']}`",
        f"- Evidence classes: `{row['evidence_classes']}`",
        f"- Opened outcome slices at registration: `{row['opened_outcome_slices_at_registration']}`",
        f"- Opened outcome artifacts: `{row['opened_outcome_artifacts']}`",
        f"- Outcome opening status: `{row['outcome_opening_status']}`",
        "",
        "## Source Status",
        "",
        "| Source | Status | SCID files | Depth files |",
        "|---|---|---:|---:|",
    ]
    for symbol, status in row["sierra_source_status"].items():
        lines.append(
            f"| `{symbol}` | `{status['status']}` | {status['scid_file_count']} | {status['depth_file_count']} |"
        )
    lines.extend(
        [
            "",
            "## Gates",
            "",
            "| Gate | Passed | Observed | Blocker |",
            "|---|---:|---|---|",
        ]
    )
    for gate in row["validation_gates"]:
        observed = json.dumps(gate["observed"], sort_keys=True, default=str).replace("|", r"\|")
        lines.append(f"| `{gate['gate_id']}` | `{gate['passed']}` | `{observed}` | `{gate['blocker_code'] or '-'}` |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            row["claim_boundary"],
            "",
            "## Safety Counters",
            "",
            f"- ai_calls: `{row['ai_calls']}`",
            f"- canary_calls: `{row['canary_calls']}`",
            f"- order_calls: `{row['order_calls']}`",
            f"- paid_data_calls: `{row['paid_data_calls']}`",
        ]
    )
    return "\n".join(lines) + "\n"
