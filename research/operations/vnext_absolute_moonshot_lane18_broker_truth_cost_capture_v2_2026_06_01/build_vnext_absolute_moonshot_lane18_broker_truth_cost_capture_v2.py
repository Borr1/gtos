from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
ROUTE_ID = "vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2_2026_06_01"

PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_ABSOLUTE_MOONSHOT_LANE18_BROKER_TRUTH_COST_CAPTURE_V2_GOAL_PROMPT_2026-06-01.md"
)
STARTER_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_ABSOLUTE_MOONSHOT_LANE18_BROKER_TRUTH_COST_CAPTURE_V2_STARTER_2026-06-01.txt"
)

LANE07_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01"
LANE06_LABEL_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane06_label_store_v1_2026_06_01"
LANE08_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane08_digital_twin_replay_engine_2026_06_01"
LANE10_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane10_scheduler_replay_engine_v3_2026_06_01"
LANE10B_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane10b_multiticket_lifecycle_scheduler_v3_2026_06_01"
LANE11_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane11_execution_policy_engine_v2_2026_06_01"
LIVE_COMPANION_DIR = REPO_ROOT / "research/operations/vnext_live_activation_active_repair_companion_2026_05_28"
MT5_CACHE_DIR = REPO_ROOT / "research/operations/vnext_mt5_local_cache_preservation_2026_06_01"
VPS_DIR = REPO_ROOT / "research/operations/vnext_compliant_vps_data_preservation_broker_portability_2026_06_01"

ACTIVE_SYMBOLS = [
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
]

BROKER_SYMBOL_ALIASES = {
    "GER40": "GER30",
    "NAS100": "NDX100",
    "UKOIL_cash": "UKOUSD",
    "US30_cash": "US30",
    "USOIL_cash": "USOUSD",
}

OUTPUTS = {
    "context_anchor": ROUTE_DIR / "LANE18_CONTEXT_ANCHOR.json",
    "universal_contract": ROUTE_DIR / "LANE18_UNIVERSAL_BROKER_TRUTH_COST_CAPTURE_CONTRACT.json",
    "source_inventory": ROUTE_DIR / "LANE18_SOURCE_INVENTORY_LEDGER.jsonl",
    "source_gap": ROUTE_DIR / "LANE18_SOURCE_GAP_LEDGER.jsonl",
    "prospective_capture": ROUTE_DIR / "LANE18_PROSPECTIVE_CAPTURE_REQUIREMENTS.jsonl",
    "cost_calibration": ROUTE_DIR / "LANE18_COST_CALIBRATION_V2_LEDGER.jsonl",
    "downstream_contract": ROUTE_DIR / "LANE18_DOWNSTREAM_CONTRACTS.json",
    "source_use_state": ROUTE_DIR / "LANE18_SOURCE_USE_STATE.json",
    "result_use_status": ROUTE_DIR / "LANE18_RESULT_USE_STATUS.json",
    "runtime_effect_boundary": ROUTE_DIR / "LANE18_RUNTIME_EFFECT_BOUNDARY.json",
    "implementation_decisions": ROUTE_DIR / "LANE18_IMPLEMENTATION_DECISION_LEDGER.jsonl",
    "branch_decisions": ROUTE_DIR / "LANE18_BRANCH_DECISION_LEDGER.jsonl",
    "saturation_self_red_team": ROUTE_DIR / "LANE18_SATURATION_SELF_RED_TEAM.md",
    "completion_audit": ROUTE_DIR / "LANE18_COMPLETION_AUDIT.json",
    "manifest": ROUTE_DIR / "LANE18_OUTPUT_MANIFEST.json",
    "verification": ROUTE_DIR / "LANE18_VERIFICATION_RESULT.json",
    "focused_test_result": ROUTE_DIR / "LANE18_FOCUSED_TEST_RESULT.xml",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict):
                    row["_source_path"] = rel(path)
                    row["_source_line"] = line_no
                    rows.append(row)
    except OSError:
        return []
    return rows


def sha256_file(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def line_count(path: Path) -> int | None:
    try:
        with path.open("rb") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return None


def stable_hash(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:32]


def git_head() -> dict[str, Any]:
    try:
        full = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
        short = subprocess.check_output(
            ["git", "rev-parse", "--short=9", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
        subject = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%s"],
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
        return {"head": full, "head_short": short, "head_subject": subject}
    except (OSError, subprocess.CalledProcessError) as exc:
        return {"head": None, "error": str(exc)}


def source_ref(row: dict[str, Any]) -> str | None:
    if row.get("_source_path") and row.get("_source_line"):
        return f"{row['_source_path']}:{row['_source_line']}"
    if row.get("_source_path"):
        return str(row["_source_path"])
    return None


def num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def broker_symbol(symbol: str) -> str:
    return BROKER_SYMBOL_ALIASES.get(symbol, symbol)


def source_status(path: Path) -> dict[str, Any]:
    exists = path.exists()
    file_count = None
    bytes_used = None
    if exists and path.is_dir():
        files = [candidate for candidate in path.rglob("*") if candidate.is_file()]
        file_count = len(files)
        bytes_used = sum(candidate.stat().st_size for candidate in files)
    return {
        "path": rel(path) if path.is_absolute() and str(path).startswith(str(REPO_ROOT)) else str(path),
        "exists": exists,
        "bytes": bytes_used if bytes_used is not None else path.stat().st_size if exists else None,
        "file_count": file_count,
        "line_count": line_count(path) if exists and path.is_file() and path.suffix in {".jsonl", ".md", ".txt", ".py"} else None,
        "sha256": sha256_file(path) if exists and path.is_file() else None,
    }


def load_sources() -> dict[str, Any]:
    return {
        "lane07_broker_truth": read_jsonl(LANE07_DIR / "LANE07_BROKER_TRUTH_LEDGER.jsonl"),
        "lane07_cost": read_jsonl(LANE07_DIR / "LANE07_COST_CALIBRATION_LEDGER.jsonl"),
        "lane07_symbol_spec": read_jsonl(LANE07_DIR / "LANE07_SYMBOL_SPEC_SESSION_LEDGER.jsonl"),
        "lane07_source_gap": read_jsonl(LANE07_DIR / "LANE07_SOURCE_GAP_LEDGER.jsonl"),
        "lane07_source_use_state": read_json(LANE07_DIR / "LANE07_SOURCE_USE_STATE.json", {}),
        "mt5_remaining_requirements": read_jsonl(MT5_CACHE_DIR / "MT5_REMAINING_VPS_EXPORT_REQUIREMENTS.jsonl"),
        "vps_missing_requirements": read_jsonl(VPS_DIR / "MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl"),
        "vps_portability_map": read_json(VPS_DIR / "BROKER_PORTABILITY_MAP.json", {}),
        "active_repair_state": read_json(LIVE_COMPANION_DIR / "ACTIVE_REPAIR_STATE.json", {}),
        "live_replay_parity": read_json(LIVE_COMPANION_DIR / "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json", {}),
    }


def build_context_anchor(now: str) -> dict[str, Any]:
    return {
        "schema_version": "lane18_context_anchor_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "git": git_head(),
        "controlling_prompt": PROMPT_PATH,
        "starter": STARTER_PATH,
        "builder_posture": "broker_truth_cost_capture_v2_contract_and_default_off_prospective_capture",
        "active_symbols": ACTIVE_SYMBOLS,
        "hard_boundaries": [
            "no live broker order/deal/position mutation",
            "no order_send/order_check/order_close/order_cancel called by this route",
            "no paid API or vendor calls",
            "no credential, remote, risk, selector, prompt, canary, or live config change",
            "new runtime helper is default-off append-only capture only",
        ],
    }


def build_universal_contract(now: str) -> dict[str, Any]:
    universal_fields = [
        "schema_version",
        "row_id",
        "source_family",
        "source_path",
        "source_line",
        "source_capture_utc",
        "event_time_utc",
        "lifecycle_event_type",
        "symbol",
        "broker_symbol",
        "ticket",
        "order_id",
        "deal_id",
        "position_id",
        "ticket_identity_status",
        "broker_real_or_proxy_state",
        "request",
        "result",
        "retcode",
        "retcode_external",
        "request_id",
        "volume",
        "fill_price",
        "close_price",
        "commission",
        "swap",
        "broker_profit",
        "spread_at_action",
        "stop_freeze_context",
        "account_snapshot",
        "false_local_close_classification",
        "telegram_parity_status",
        "cost_source_reason",
        "source_refs",
        "no_leak_status",
        "runtime_effect_boundary",
    ]
    event_contracts = {
        "account_snapshot": {
            "ticket_identity_required": False,
            "required_fields": ["account_snapshot.balance", "account_snapshot.equity", "source_family", "source_refs"],
        },
        "order_request": {
            "ticket_identity_required": True,
            "required_fields": ["order_id", "request", "spread_at_action", "stop_freeze_context"],
        },
        "order_result": {
            "ticket_identity_required": True,
            "required_fields": ["order_id", "retcode", "retcode_external", "request_id", "result"],
        },
        "deal": {
            "ticket_identity_required": True,
            "required_fields": ["deal_id", "order_id", "position_id", "fill_price", "volume", "broker_profit"],
        },
        "position_snapshot": {
            "ticket_identity_required": True,
            "required_fields": ["ticket", "position_id", "volume", "source_capture_utc"],
        },
        "entry_fill": {
            "ticket_identity_required": True,
            "required_fields": ["ticket", "order_id", "deal_id", "fill_price", "spread_at_action"],
        },
        "partial_close": {
            "ticket_identity_required": True,
            "required_fields": ["ticket", "deal_id", "position_id", "volume", "close_price", "broker_profit"],
        },
        "residual_position": {
            "ticket_identity_required": True,
            "required_fields": ["ticket", "position_id", "volume", "residual_ticket_chain"],
        },
        "modify_request": {
            "ticket_identity_required": True,
            "required_fields": ["ticket", "position_id", "request", "stop_freeze_context", "spread_at_action"],
        },
        "modify_result": {
            "ticket_identity_required": True,
            "required_fields": ["ticket", "position_id", "retcode", "retcode_external", "request_id", "result"],
        },
        "rejection": {
            "ticket_identity_required": True,
            "required_fields": ["order_id", "retcode", "comment", "stop_freeze_context", "spread_at_action"],
        },
        "close": {
            "ticket_identity_required": True,
            "required_fields": ["ticket", "deal_id", "position_id", "close_price", "broker_profit", "cost_source_reason"],
        },
        "cost": {
            "ticket_identity_required": True,
            "required_fields": ["deal_id", "commission", "swap", "broker_profit", "cost_source_reason"],
        },
        "manual_client_intervention": {
            "ticket_identity_required": True,
            "required_fields": ["ticket", "position_id", "source_family", "source_refs"],
        },
        "false_local_close": {
            "ticket_identity_required": True,
            "required_fields": ["ticket", "position_id", "false_local_close_classification", "source_refs"],
        },
        "telegram_parity": {
            "ticket_identity_required": True,
            "required_fields": ["ticket", "telegram_parity_status", "source_refs"],
        },
    }
    return {
        "schema_version": "lane18_universal_broker_truth_cost_capture_contract_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "universal_row_schema_version": "broker_truth_cost_capture_v2_lifecycle_row_v1",
        "universal_fields": universal_fields,
        "event_contracts": event_contracts,
        "broker_real_or_proxy_state_values": [
            "BROKER_REAL",
            "BROKER_READONLY_SNAPSHOT",
            "PROSPECTIVE_CAPTURE",
            "SOURCE_GAP",
            "PROXY_ONLY",
        ],
        "source_identity_rule": "every row must carry source_family and either source_path/source_line or source_refs",
        "ticket_identity_rule": (
            "every order/deal/position/fill/partial/residual/modify/rejection/close/"
            "cost/manual/false-close/telegram row must carry at least one of ticket, order_id, deal_id, position_id"
        ),
        "projection_boundary": {
            "forbidden_as_broker_truth": [
                "projected_pnl",
                "projected_profit",
                "projected_r",
                "local_projected_r",
                "local_risk_dollar_projection",
                "synthetic_r",
            ],
            "allowed_only_as_proxy_with_label": ["cost prior", "spread proxy", "source-bound replay R"],
        },
        "false_local_close_required_classifications": [
            "BROKER_CONTRADICTION_OPEN_POSITION_FALSE_CLOSE_NOTIFICATION",
            "BROKER_HISTORY_CONFIRMED_CLOSE_LOCAL_NOTIFICATION_VALID",
            "UNRESOLVED_ACCOUNT_HISTORY_REQUIRED",
        ],
    }


def build_source_inventory(now: str) -> list[dict[str, Any]]:
    source_paths = {
        "controlling_prompt": REPO_ROOT / PROMPT_PATH,
        "starter": REPO_ROOT / STARTER_PATH,
        "moonshot_vision": REPO_ROOT / ".context/00_core/vnext_absolute_moonshot_vision_and_limitations.md",
        "master_source_authority": REPO_ROOT / "research/operations/vnext_absolute_moonshot_master_orchestration_2026_06_01/ABSOLUTE_MASTER_SOURCE_AUTHORITY_MAP.json",
        "master_output_contracts": REPO_ROOT / "research/operations/vnext_absolute_moonshot_master_orchestration_2026_06_01/ABSOLUTE_MASTER_OUTPUT_SCHEMA_CONTRACTS.json",
        "lane07_broker_truth": LANE07_DIR / "LANE07_BROKER_TRUTH_LEDGER.jsonl",
        "lane07_cost": LANE07_DIR / "LANE07_COST_CALIBRATION_LEDGER.jsonl",
        "lane07_source_gap": LANE07_DIR / "LANE07_SOURCE_GAP_LEDGER.jsonl",
        "lane07_symbol_spec": LANE07_DIR / "LANE07_SYMBOL_SPEC_SESSION_LEDGER.jsonl",
        "live_active_repair_state": LIVE_COMPANION_DIR / "ACTIVE_REPAIR_STATE.json",
        "live_replay_gate_stack_parity": LIVE_COMPANION_DIR / "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json",
        "mt5_cache_coverage_summary": MT5_CACHE_DIR / "MT5_LOCAL_CACHE_COVERAGE_SUMMARY.json",
        "mt5_remaining_vps_export_requirements": MT5_CACHE_DIR / "MT5_REMAINING_VPS_EXPORT_REQUIREMENTS.jsonl",
        "vps_missing_source_export_requirements": VPS_DIR / "MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl",
        "vps_broker_portability_map": VPS_DIR / "BROKER_PORTABILITY_MAP.json",
        "slippage_shadow_log": REPO_ROOT / "shadow_logs/slippage.jsonl",
        "daily_pnl_history": REPO_ROOT / "shadow_logs/daily_pnl_history.jsonl",
        "account_truth_reconciliation_status": REPO_ROOT / "shadow_logs/account_truth_reconciliation_status.jsonl",
        "mt5_interface": REPO_ROOT / "src/mt5/mt5_interface.py",
        "mt5_real": REPO_ROOT / "src/mt5/mt5_real.py",
        "execution_engine": REPO_ROOT / "src/components/execution.py",
        "capture_helper": REPO_ROOT / "src/components/broker_truth_cost_capture_v2.py",
        "notifications": REPO_ROOT / "src/notifications.py",
        "account_pnl_truth_reconciler": REPO_ROOT / "src/research_infra/account_pnl_truth_reconciler.py",
        "broker_actual_r_audit": REPO_ROOT / "src/research_infra/broker_actual_r_audit.py",
    }
    source_surfaces = {
        "route_evidence": ["controlling_prompt", "starter", "master_source_authority", "lane07_broker_truth"],
        "shadow_logs": ["slippage_shadow_log", "daily_pnl_history", "account_truth_reconciliation_status"],
        "account_truth_logs": ["account_pnl_truth_reconciler", "broker_actual_r_audit"],
        "mt5_local_cache": ["mt5_cache_coverage_summary", "mt5_remaining_vps_export_requirements"],
        "broker_exports_when_present": ["lane07_broker_truth", "vps_missing_source_export_requirements"],
        "symbol_specs_sessions_stops_freeze_tick_value_contract_margin_spread_commission_swap": [
            "lane07_symbol_spec",
            "lane07_source_gap",
            "vps_broker_portability_map",
        ],
        "order_deal_position_history": ["lane07_broker_truth", "mt5_remaining_vps_export_requirements"],
        "partial_residual_modify_close_reason_false_close_telegram": [
            "execution_engine",
            "notifications",
            "live_active_repair_state",
            "live_replay_gate_stack_parity",
        ],
    }
    rows = []
    for source_id, path in source_paths.items():
        rows.append(
            {
                "schema_version": "lane18_source_inventory_v1",
                "route_id": ROUTE_ID,
                "generated_at_utc": now,
                "source_id": source_id,
                "source_status": source_status(path),
                "source_family": next(
                    (family for family, ids in source_surfaces.items() if source_id in ids),
                    "supporting_code_or_context",
                ),
                "broker_truth_use": "source_bound_contract_or_gap_evidence",
                "projection_as_truth_allowed": False,
            }
        )
    return rows


def gap_row(
    now: str,
    *,
    symbol: str | None,
    lifecycle_surface: str,
    source_surface: str,
    field: str,
    missing_source_class: str,
    source_state: str,
    recoverability: str,
    required_action: str,
    proof_required: str,
    source_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "lane18_source_gap_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "source_gap_id": stable_hash(ROUTE_ID, symbol, lifecycle_surface, source_surface, field, source_state),
        "symbol": symbol,
        "broker_symbol": broker_symbol(symbol) if symbol else None,
        "lifecycle_surface": lifecycle_surface,
        "source_surface": source_surface,
        "field": field,
        "missing_source_class": missing_source_class,
        "source_state": source_state,
        "recoverability": recoverability,
        "required_action": required_action,
        "proof_required": proof_required,
        "proxy_policy": "explicit_proxy_only_never_broker_truth" if "PROXY" in source_state else "no_proxy_may_replace_broker_truth",
        "downstream_blocking": False,
        "source_refs": list(source_refs or []),
    }


def build_source_gaps(sources: dict[str, Any], now: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    symbol_fields = [
        ("symbol_info_full_export", "broker_symbol_info", "RECOVERABLE_BY_READONLY_SYMBOL_INFO_EXPORT"),
        ("broker_trading_sessions_by_weekday", "broker_sessions", "RECOVERABLE_BY_READONLY_SYMBOL_SESSION_EXPORT"),
        ("broker_holiday_calendar", "broker_sessions", "RECOVERABLE_BY_BROKER_VENDOR_EXPORT_OR_OFFICIAL_NOTICE"),
        ("stops_level_time_series", "stop_freeze", "RECOVERABLE_ONLY_BY_FORWARD_CAPTURE"),
        ("freeze_level_time_series", "stop_freeze", "RECOVERABLE_ONLY_BY_FORWARD_CAPTURE"),
        ("trade_tick_value_profit_loss", "broker_symbol_info", "RECOVERABLE_BY_READONLY_SYMBOL_INFO_EXPORT"),
        ("trade_tick_size", "broker_symbol_info", "RECOVERABLE_BY_READONLY_SYMBOL_INFO_EXPORT"),
        ("contract_size", "broker_symbol_info", "RECOVERABLE_BY_READONLY_SYMBOL_INFO_EXPORT"),
        ("point", "broker_symbol_info", "RECOVERABLE_BY_READONLY_SYMBOL_INFO_EXPORT"),
        ("volume_min_step_max", "broker_symbol_info", "RECOVERABLE_BY_READONLY_SYMBOL_INFO_EXPORT"),
        ("margin_initial_maintenance_hedged", "margin", "RECOVERABLE_BY_READONLY_SYMBOL_INFO_EXPORT"),
        ("commission_schedule", "cost", "NON_GENERATABLE_FROM_MARKET_DATA_BROKER_EXPORT_REQUIRED"),
        ("swap_long_short_mode_triple_day_rollover", "cost", "NON_GENERATABLE_FROM_MARKET_DATA_BROKER_EXPORT_REQUIRED"),
        ("time_varying_spread_samples", "spread", "RECOVERABLE_ONLY_BY_FORWARD_TICK_CAPTURE"),
        ("filling_order_expiration_modes", "broker_symbol_info", "RECOVERABLE_BY_READONLY_SYMBOL_INFO_EXPORT"),
        ("server_timezone_and_dst", "broker_server", "RECOVERABLE_BY_BROKER_TERMINAL_EXPORT"),
        ("broker_symbol_alias", "broker_symbol_map", "RECOVERABLE_BY_READONLY_SYMBOL_INFO_EXPORT"),
    ]
    lifecycle_fields = [
        ("history_orders_full_window", "orders", "BROKER_SERVER_HISTORY_EXPORT_REQUIRED"),
        ("history_deals_full_window", "deals", "BROKER_SERVER_HISTORY_EXPORT_REQUIRED"),
        ("orders_get_open_pending", "orders", "BROKER_SERVER_OPEN_ORDER_EXPORT_REQUIRED"),
        ("positions_get_open", "positions", "BROKER_SERVER_POSITION_EXPORT_REQUIRED"),
        ("partial_close_residual_ticket_chain", "partials", "PROSPECTIVE_RUNTIME_CAPTURE_REQUIRED"),
        ("modify_request_retcode_external", "modifies", "PROSPECTIVE_RUNTIME_CAPTURE_REQUIRED"),
        ("manual_client_intervention", "manual_client", "BROKER_SERVER_HISTORY_EXPORT_REQUIRED"),
        ("telegram_parity_event_id", "telegram_parity", "PROSPECTIVE_RUNTIME_CAPTURE_REQUIRED"),
        ("account_baseline_balance_equity", "account_snapshot", "PROSPECTIVE_RUNTIME_CAPTURE_REQUIRED"),
        ("false_local_close_broker_contradiction_proof", "false_local_close", "PROSPECTIVE_RUNTIME_CAPTURE_REQUIRED"),
    ]
    lane07_gap_refs = [
        source_ref(row)
        for row in sources["lane07_source_gap"][:5]
        if source_ref(row)
    ]
    for symbol in ACTIVE_SYMBOLS:
        for field, surface, recoverability in symbol_fields:
            rows.append(
                gap_row(
                    now,
                    symbol=symbol,
                    lifecycle_surface="symbol_constraints_and_costs",
                    source_surface=surface,
                    field=field,
                    missing_source_class="BROKER_SPEC_FIELD_GAP",
                    source_state="MISSING_OR_SINGLE_SNAPSHOT_ONLY_EXPLICIT_GAP",
                    recoverability=recoverability,
                    required_action="capture read-only broker symbol/session/spec export and hash manifest from compliant VPS",
                    proof_required="symbol_info/session/export jsonl with source timestamp and no order calls",
                    source_refs=lane07_gap_refs,
                )
            )
        for field, surface, source_state in lifecycle_fields:
            rows.append(
                gap_row(
                    now,
                    symbol=symbol,
                    lifecycle_surface=surface,
                    source_surface="broker_order_deal_position_lifecycle",
                    field=field,
                    missing_source_class="BROKER_LIFECYCLE_FIELD_GAP",
                    source_state=source_state,
                    recoverability=(
                        "NON_GENERATABLE_FROM_MARKET_DATA_RECOVERABLE_BY_BROKER_EXPORT"
                        if "HISTORY" in source_state or "BROKER_SERVER" in source_state
                        else "RECOVERABLE_ONLY_BY_FORWARD_DEFAULT_OFF_CAPTURE"
                    ),
                    required_action="capture ticket-bound universal lifecycle row or read-only broker export",
                    proof_required="ticket/order/deal/position keyed jsonl with source path/hash and capture timestamp",
                    source_refs=[
                        rel(REPO_ROOT / "src/components/broker_truth_cost_capture_v2.py"),
                        rel(REPO_ROOT / "src/components/execution.py"),
                    ],
                )
            )
    for requirement in sources["mt5_remaining_requirements"] + sources["vps_missing_requirements"]:
        field = requirement.get("source_family") or requirement.get("field") or requirement.get("requirement_id")
        rows.append(
            gap_row(
                now,
                symbol=requirement.get("symbol"),
                lifecycle_surface=str(requirement.get("surface") or "mt5_export_requirement"),
                source_surface=str(requirement.get("source_family") or "broker_export"),
                field=str(field or "unknown_broker_export_requirement"),
                missing_source_class="UPSTREAM_PRESERVATION_EXPORT_REQUIREMENT",
                source_state=str(requirement.get("state") or requirement.get("status") or "EXPORT_REQUIRED"),
                recoverability="RECOVERABLE_BY_COMPLIANT_READONLY_VPS_EXPORT",
                required_action=str(requirement.get("required_action") or "run default-off read-only MT5 export"),
                proof_required=str(requirement.get("proof_required") or "hash manifest plus no-order-call proof"),
                source_refs=[source_ref(requirement)] if source_ref(requirement) else [],
            )
        )
    return rows


def build_prospective_capture_requirements(now: str) -> list[dict[str, Any]]:
    surfaces = [
        (
            "order_request_result",
            ["request", "retcode", "retcode_external", "request_id", "spread_at_action", "stop_freeze_context"],
            ["src/mt5/mt5_interface.py", "src/mt5/mt5_real.py", "src/components/execution.py"],
        ),
        (
            "modify_request_retcode_details",
            ["ticket", "position_id", "request", "retcode", "retcode_external", "request_id", "positions_before_after"],
            ["src/components/execution.py", "src/components/broker_truth_cost_capture_v2.py"],
        ),
        (
            "stop_freeze_context",
            ["trade_stops_level", "trade_freeze_level", "point", "trade_tick_size", "trade_tick_value"],
            ["src/components/broker_truth_cost_capture_v2.py", "src/components/execution.py"],
        ),
        (
            "spread_at_action",
            ["bid", "ask", "spread_price", "tick_time_utc", "source_state"],
            ["src/components/broker_truth_cost_capture_v2.py", "src/components/slippage_shadow_logger.py"],
        ),
        (
            "cost_fields",
            ["commission", "swap", "broker_profit", "cash_risk_amount", "cost_source_reason"],
            ["src/components/slippage_shadow_logger.py", "src/research_infra/broker_actual_r_audit.py"],
        ),
        (
            "ticket_identity",
            ["ticket", "order_id", "deal_id", "position_id", "ticket_identity_status"],
            ["src/components/broker_truth_cost_capture_v2.py", "src/mt5/mt5_real.py"],
        ),
        (
            "partial_residual_lifecycle",
            ["closed_ticket", "new_residual_ticket", "deal_id", "position_id", "remaining_volume"],
            ["src/components/execution.py"],
        ),
        (
            "false_local_close_proof",
            ["ticket", "position_snapshot", "broker_history_close_deal", "false_local_close_classification"],
            ["src/components/execution.py", "src/components/broker_truth_cost_capture_v2.py"],
        ),
        (
            "account_baseline_balance_equity",
            ["balance", "equity", "margin", "account_login", "server", "source_capture_utc"],
            ["src/mt5/mt5_real.py", "src/notifications.py"],
        ),
        (
            "telegram_parity_source",
            ["telegram_event_id", "trade_id", "ticket", "notification_context", "account_truth_status"],
            ["src/notifications.py"],
        ),
    ]
    rows = []
    for surface, fields, code_refs in surfaces:
        rows.append(
            {
                "schema_version": "lane18_prospective_capture_requirement_v1",
                "route_id": ROUTE_ID,
                "generated_at_utc": now,
                "capture_requirement_id": stable_hash(ROUTE_ID, surface, fields),
                "capture_surface": surface,
                "required_fields": fields,
                "code_refs": code_refs,
                "default_off_status": "DEFAULT_OFF_NO_LIVE_EFFECT",
                "current_implementation_status": (
                    "patched_order_result_metadata_and_default_off_helper"
                    if surface in {"order_request_result", "ticket_identity", "stop_freeze_context", "spread_at_action"}
                    else "prospective_capture_contract_emitted_forward_capture_required"
                ),
                "source_identity_rule": "source_family plus source_path/source_line or source_refs required",
                "ticket_identity_rule": "ticket/order/deal/position id required for ticket-bound lifecycle surfaces",
                "runtime_effect_boundary": "append_only_when_explicitly_enabled_no_order_effect",
            }
        )
    return rows


def build_cost_calibration(sources: dict[str, Any], now: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, source in enumerate(sources["lane07_cost"], 1):
        row_type = str(source.get("row_type") or "")
        broker_realized = source.get("broker_realized_net_r")
        broker_mark = source.get("broker_mark_to_market_net_r")
        if "broker_real" in row_type or broker_realized is not None or broker_mark is not None:
            state = "BROKER_REAL"
            reason = "Lane07 broker history/order/deal cost row with account-history fields where present"
        elif "proxy" in row_type or source.get("cost_status") in {"SPREAD_SNAPSHOT_PROXY", "PROXY"}:
            state = "PROXY_ONLY"
            reason = "Lane07 source-bound cost proxy row; not broker truth"
        else:
            state = "SOURCE_GAP"
            reason = "Lane07 cost row documents missing broker cost source"
        rows.append(
            {
                "schema_version": "lane18_cost_calibration_v2_v1",
                "route_id": ROUTE_ID,
                "generated_at_utc": now,
                "row_id": stable_hash("lane18_cost", index, source_ref(source), source.get("symbol"), row_type),
                "source_row_type": row_type,
                "symbol": source.get("symbol"),
                "broker_symbol": source.get("broker_symbol") or source.get("symbol"),
                "session_label": source.get("session_label") or source.get("session") or "source_row_session_unspecified",
                "regime_label": source.get("regime_label") or source.get("regime") or "source_row_regime_unspecified",
                "time_utc": source.get("time_utc") or source.get("event_time_utc"),
                "commission": source.get("commission"),
                "swap": source.get("swap"),
                "spread_price": source.get("spread_price") or source.get("spread_sample_price"),
                "slippage_price": source.get("slippage_price"),
                "broker_profit": source.get("broker_profit") or source.get("profit"),
                "broker_realized_net_r": broker_realized,
                "broker_mark_to_market_net_r": broker_mark,
                "broker_real_or_proxy_state": state,
                "cost_source_reason": reason,
                "proxy_allowed_for_decision_prior": state == "PROXY_ONLY",
                "projection_as_broker_truth_allowed": False,
                "source_refs": [source_ref(source)] if source_ref(source) else [],
            }
        )
    existing_symbols = {row.get("symbol") for row in rows if row.get("symbol")}
    sessions = ["asia", "london", "new_york", "rollover"]
    for symbol in ACTIVE_SYMBOLS:
        if symbol in existing_symbols:
            continue
        for session in sessions:
            rows.append(
                {
                    "schema_version": "lane18_cost_calibration_v2_v1",
                    "route_id": ROUTE_ID,
                    "generated_at_utc": now,
                    "row_id": stable_hash("lane18_cost_proxy", symbol, session),
                    "source_row_type": "symbol_session_cost_source_gap",
                    "symbol": symbol,
                    "broker_symbol": broker_symbol(symbol),
                    "session_label": session,
                    "regime_label": "unobserved_broker_cost",
                    "time_utc": None,
                    "commission": None,
                    "swap": None,
                    "spread_price": None,
                    "slippage_price": None,
                    "broker_profit": None,
                    "broker_realized_net_r": None,
                    "broker_mark_to_market_net_r": None,
                    "broker_real_or_proxy_state": "SOURCE_GAP",
                    "cost_source_reason": "No broker-real commission/swap/slippage row exists for symbol-session; VPS export or forward capture required",
                    "proxy_allowed_for_decision_prior": False,
                    "projection_as_broker_truth_allowed": False,
                    "source_refs": [rel(LANE07_DIR / "LANE07_SOURCE_GAP_LEDGER.jsonl")],
                }
            )
    return rows


def build_downstream_contract(now: str) -> dict[str, Any]:
    consumers = {
        "Scheduler V3": {
            "allowed_predecision": ["account_snapshot", "open_positions", "symbol_constraints", "cost_priors_with_proxy_labels"],
            "forbidden": ["future_close_profit", "future_deal_reason", "projected_pnl_as_truth"],
        },
        "Execution V3": {
            "allowed_predecision": ["stop_freeze_context", "spread_at_action", "lot_geometry", "default_off_forward_capture_schema"],
            "forbidden": ["production behavior change from Lane18 without separate approval"],
        },
        "Digital Twin V2": {
            "allowed": ["broker_real_lifecycle_when_ticket_bound", "proxy_cost_rows_when_labeled", "source_gap_rows"],
            "precedence": "broker-real ticket/deal rows dominate local projections",
        },
        "ML labels": {
            "allowed_post_split": ["broker_real_net_r", "close_reason", "manual_intervention", "false_local_close_classification"],
            "forbidden_features": ["broker_realized_net_r", "final_profit", "post_fill_slippage", "manual_close_outcome"],
        },
        "Repair Companion": {
            "allowed": ["capture_requirements", "source_gap_rows", "false_close_proof_requirements", "modify_retcode_gaps"],
        },
        "Command Center": {
            "allowed": ["account_truth_status", "open positions", "source gaps", "cost capture status", "telegram parity status"],
        },
    }
    return {
        "schema_version": "lane18_downstream_contracts_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "join_keys": ["symbol", "broker_symbol", "ticket", "order_id", "deal_id", "position_id", "trade_id", "candidate_id"],
        "consumer_contracts": consumers,
        "missing_data_rule": "missing broker truth remains source_gap or prospective_capture_required, never generic cost gap",
        "broker_real_proxy_separation_rule": "BROKER_REAL and PROXY_ONLY rows are disjoint and must never be coalesced",
        "no_leak_rule": "post-decision broker truth may feed labels/reconciliation only, not predecision features",
    }


def build_source_use_state(sources: dict[str, Any], now: str) -> dict[str, Any]:
    return {
        "schema_version": "lane18_source_use_state_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "source_use_state": "existing_read_only_route_shadow_account_mt5_cache_vps_gap_evidence_consumed",
        "fresh_broker_server_export_executed": False,
        "fresh_broker_server_export_reason": "Lane18 is default-off/local artifact work; remaining server-only fields stay exact VPS export requirements",
        "input_counts": {
            "lane07_broker_truth_rows": len(sources["lane07_broker_truth"]),
            "lane07_cost_rows": len(sources["lane07_cost"]),
            "lane07_source_gap_rows": len(sources["lane07_source_gap"]),
            "mt5_remaining_requirements": len(sources["mt5_remaining_requirements"]),
            "vps_missing_requirements": len(sources["vps_missing_requirements"]),
        },
    }


def build_runtime_effect_boundary(now: str) -> dict[str, Any]:
    return {
        "schema_version": "lane18_runtime_effect_boundary_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "runtime_effect_boundary": "default_off_append_only_capture_and_offline_artifacts_no_live_behavior_change",
        "default_off_code_paths": ["src/components/broker_truth_cost_capture_v2.py"],
        "forbidden_surface_attestation": {
            "order_placement": False,
            "order_modification": False,
            "position_close": False,
            "order_cancel": False,
            "paid_api_vendor_call": False,
            "credential_change": False,
            "remote_push": False,
            "production_prompt_config_risk_execution_selector_change": False,
            "live_runtime_restart": False,
        },
    }


def build_result_use_status(now: str) -> dict[str, Any]:
    return {
        "schema_version": "lane18_result_use_status_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "result_use_status": "broker_truth_cost_capture_contract_not_live_activation_not_production_decision",
        "may_use_for": ["offline verifier", "downstream schema contract", "repair companion capture checklist"],
        "may_not_use_for": ["live scaling", "order placement", "claiming projected PnL as broker truth"],
    }


def build_decision_rows(now: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    implementation = [
        {
            "schema_version": "lane18_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": now,
            "decision_id": "order_result_metadata_extension",
            "decision": "extend OrderResult and RealMT5.order_send with request_id and retcode_external",
            "runtime_effect": "field capture only; no live behavior change",
            "code_refs": ["src/mt5/mt5_interface.py", "src/mt5/mt5_real.py", "src/components/execution.py"],
        },
        {
            "schema_version": "lane18_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": now,
            "decision_id": "default_off_capture_helper",
            "decision": "add append-only lifecycle row builder guarded by broker_truth_cost_capture_v2.enabled",
            "runtime_effect": "disabled by default; no order/check/close calls",
            "code_refs": ["src/components/broker_truth_cost_capture_v2.py"],
        },
    ]
    branch = [
        {
            "schema_version": "lane18_branch_decision_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": now,
            "branch_decision": "do_not_attempt_to_generate_missing_historical_broker_truth_from_market_data",
            "reason": "historical broker intent/order/deal/partial/manual intervention truth is non-generatable without broker export",
        },
        {
            "schema_version": "lane18_branch_decision_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": now,
            "branch_decision": "separate_broker_real_cost_rows_from_proxy_rows",
            "reason": "downstream ML/twin/scheduler contracts require broker-real/proxy labels to remain disjoint",
        },
    ]
    return implementation, branch


def build_self_red_team(now: str) -> str:
    return (
        "# Lane18 Saturation Self Red Team\n\n"
        f"Generated: {now}\n\n"
        "- Projected PnL is explicitly forbidden as broker truth. Verifier checks cost rows and the universal contract.\n"
        "- Ticket-bound lifecycle surfaces require ticket/order/deal/position identity and source identity.\n"
        "- False local close rows require a broker contradiction or unresolved account-history classification.\n"
        "- Generic cost gaps are replaced by symbol/window/field/source rows.\n"
        "- Runtime changes are limited to default-off append-only capture helpers and extra MT5 result metadata fields.\n"
    )


def build_completion_audit(now: str, counts: dict[str, int], verification: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "lane18_completion_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "status": "complete_pending_verification" if verification is None else "complete" if verification.get("ok") else "verification_failed",
        "instruction_coverage": {
            "mandatory_preflight_completed": True,
            "moonshot_master_lanes_live_companion_mt5_preservation_read": True,
            "broker_execution_notification_account_code_read": True,
            "universal_contracts_emitted": True,
            "source_gap_ledgers_are_field_symbol_source_specific": True,
            "default_off_capture_code_added": True,
            "downstream_contracts_emitted": True,
        },
        "counts": counts,
        "requirements": [
            {"requirement": "universal_contract", "status": "complete", "evidence": rel(OUTPUTS["universal_contract"])},
            {"requirement": "source_inventory", "status": "complete", "rows": counts["source_inventory_rows"], "evidence": rel(OUTPUTS["source_inventory"])},
            {"requirement": "source_gaps", "status": "complete", "rows": counts["source_gap_rows"], "evidence": rel(OUTPUTS["source_gap"])},
            {"requirement": "prospective_capture", "status": "complete", "rows": counts["prospective_capture_rows"], "evidence": rel(OUTPUTS["prospective_capture"])},
            {"requirement": "cost_calibration_v2", "status": "complete", "rows": counts["cost_rows"], "evidence": rel(OUTPUTS["cost_calibration"])},
            {"requirement": "downstream_contracts", "status": "complete", "evidence": rel(OUTPUTS["downstream_contract"])},
            {"requirement": "verifier_and_tests", "status": "pending_after_test_run" if verification is None else "complete", "evidence": [rel(OUTPUTS["verification"]), rel(OUTPUTS["focused_test_result"])]},
            {"requirement": "scoped_commit", "status": "pending_after_verification"},
        ],
        "verification": verification,
    }


def build_manifest(now: str) -> dict[str, Any]:
    artifacts = []
    for name, path in OUTPUTS.items():
        if name == "manifest":
            continue
        artifacts.append(
            {
                "name": name,
                "path": rel(path),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else None,
                "line_count": line_count(path) if path.suffix in {".jsonl", ".md", ".py", ".txt", ".xml"} else None,
                "sha256": sha256_file(path),
            }
        )
    manifest = {
        "schema_version": "lane18_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "git": git_head(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    write_json(OUTPUTS["manifest"], manifest)
    return manifest


def build_artifacts(write: bool = True) -> dict[str, Any]:
    now = now_iso()
    sources = load_sources()
    context_anchor = build_context_anchor(now)
    universal_contract = build_universal_contract(now)
    source_inventory = build_source_inventory(now)
    source_gap = build_source_gaps(sources, now)
    prospective_capture = build_prospective_capture_requirements(now)
    cost_calibration = build_cost_calibration(sources, now)
    downstream_contract = build_downstream_contract(now)
    source_use_state = build_source_use_state(sources, now)
    result_use_status = build_result_use_status(now)
    runtime_effect_boundary = build_runtime_effect_boundary(now)
    implementation, branch = build_decision_rows(now)
    self_red_team = build_self_red_team(now)
    counts = {
        "source_inventory_rows": len(source_inventory),
        "source_gap_rows": len(source_gap),
        "prospective_capture_rows": len(prospective_capture),
        "cost_rows": len(cost_calibration),
        "implementation_decision_rows": len(implementation),
        "branch_decision_rows": len(branch),
    }
    completion = build_completion_audit(now, counts, None)
    artifacts = {
        "context_anchor": context_anchor,
        "universal_contract": universal_contract,
        "source_inventory": source_inventory,
        "source_gap": source_gap,
        "prospective_capture": prospective_capture,
        "cost_calibration": cost_calibration,
        "downstream_contract": downstream_contract,
        "source_use_state": source_use_state,
        "result_use_status": result_use_status,
        "runtime_effect_boundary": runtime_effect_boundary,
        "implementation_decisions": implementation,
        "branch_decisions": branch,
        "saturation_self_red_team": self_red_team,
        "completion_audit": completion,
        "counts": counts,
    }
    if write:
        write_json(OUTPUTS["context_anchor"], context_anchor)
        write_json(OUTPUTS["universal_contract"], universal_contract)
        write_jsonl(OUTPUTS["source_inventory"], source_inventory)
        write_jsonl(OUTPUTS["source_gap"], source_gap)
        write_jsonl(OUTPUTS["prospective_capture"], prospective_capture)
        write_jsonl(OUTPUTS["cost_calibration"], cost_calibration)
        write_json(OUTPUTS["downstream_contract"], downstream_contract)
        write_json(OUTPUTS["source_use_state"], source_use_state)
        write_json(OUTPUTS["result_use_status"], result_use_status)
        write_json(OUTPUTS["runtime_effect_boundary"], runtime_effect_boundary)
        write_jsonl(OUTPUTS["implementation_decisions"], implementation)
        write_jsonl(OUTPUTS["branch_decisions"], branch)
        OUTPUTS["saturation_self_red_team"].write_text(self_red_team, encoding="utf-8")
        write_json(OUTPUTS["completion_audit"], completion)
        build_manifest(now)
    return artifacts


def main() -> int:
    artifacts = build_artifacts(write=True)
    print(json.dumps({"route_id": ROUTE_ID, **artifacts["counts"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
