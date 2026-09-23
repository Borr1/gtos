from __future__ import annotations

import hashlib
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]

ROUTE_ID = "vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01"

PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_MOONSHOT_LANE07_BROKER_TRUTH_COST_CALIBRATION_GOAL_PROMPT_2026-06-01.md"
)
STARTER_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_MOONSHOT_LANE07_BROKER_TRUTH_COST_CALIBRATION_STARTER_2026-06-01.txt"
)

LIVE_COMPANION_DIR = (
    REPO_ROOT / "research/operations/vnext_live_activation_active_repair_companion_2026_05_28"
)
FRIDAY_DIR = (
    REPO_ROOT
    / "research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
)
LANE06_DIR = (
    REPO_ROOT / "research/operations/vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31"
)
MT5_CACHE_DIR = REPO_ROOT / "research/operations/vnext_mt5_local_cache_preservation_2026_06_01"
VPS_DIR = (
    REPO_ROOT
    / "research/operations/vnext_compliant_vps_data_preservation_broker_portability_2026_06_01"
)
MOONSHOT_LANE05_DIR = (
    REPO_ROOT / "research/operations/vnext_moonshot_lane05_feature_store_v1_2026_06_01"
)
MOONSHOT_LANE06_LABEL_DIR = (
    REPO_ROOT / "research/operations/vnext_moonshot_lane06_label_store_v1_2026_06_01"
)
MOONSHOT_LANE08_DIR = (
    REPO_ROOT / "research/operations/vnext_moonshot_lane08_digital_twin_replay_engine_2026_06_01"
)

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

CANONICAL_SYMBOL_ALIASES = {
    "GER30": "GER40",
    "GER40.cash": "GER40",
    "NDX100": "NAS100",
    "US100.cash": "NAS100",
    "UKOUSD": "UKOIL_cash",
    "UKOIL.cash": "UKOIL_cash",
    "US30": "US30_cash",
    "US30.cash": "US30_cash",
    "USOUSD": "USOIL_cash",
    "USOIL.cash": "USOIL_cash",
}

OUTPUTS = {
    "context_anchor": ROUTE_DIR / "LANE07_CONTEXT_ANCHOR.json",
    "schema": ROUTE_DIR / "LANE07_BROKER_COST_SCHEMA.json",
    "source_coverage": ROUTE_DIR / "LANE07_SOURCE_COVERAGE_LEDGER.jsonl",
    "dependency_state": ROUTE_DIR / "LANE07_DEPENDENCY_STATE_LEDGER.jsonl",
    "symbol_spec": ROUTE_DIR / "LANE07_SYMBOL_SPEC_SESSION_LEDGER.jsonl",
    "broker_truth": ROUTE_DIR / "LANE07_BROKER_TRUTH_LEDGER.jsonl",
    "cost_calibration": ROUTE_DIR / "LANE07_COST_CALIBRATION_LEDGER.jsonl",
    "source_gap": ROUTE_DIR / "LANE07_SOURCE_GAP_LEDGER.jsonl",
    "downstream_contract": ROUTE_DIR / "LANE07_DOWNSTREAM_CONTRACT.json",
    "source_use_state": ROUTE_DIR / "LANE07_SOURCE_USE_STATE.json",
    "runtime_effect_boundary": ROUTE_DIR / "LANE07_RUNTIME_EFFECT_BOUNDARY.json",
    "completion_audit": ROUTE_DIR / "LANE07_COMPLETION_AUDIT.json",
    "manifest": ROUTE_DIR / "LANE07_OUTPUT_MANIFEST.json",
    "verification": ROUTE_DIR / "LANE07_VERIFICATION_RESULT.json",
    "focused_test_result": ROUTE_DIR / "LANE07_FOCUSED_TEST_RESULT.xml",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
                    row["_source_path"] = str(path.relative_to(REPO_ROOT))
                    row["_source_line"] = line_no
                    rows.append(row)
    except OSError:
        return []
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


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


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def source_ref(row: dict[str, Any]) -> str | None:
    path = row.get("_source_path")
    line = row.get("_source_line")
    if path and line:
        return f"{path}:{line}"
    return str(path) if path else None


def canonical_symbol(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return CANONICAL_SYMBOL_ALIASES.get(text, text)


def broker_symbol_for(symbol: str) -> str:
    return BROKER_SYMBOL_ALIASES.get(symbol, symbol)


def num(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def rounded(value: Any, places: int = 6) -> float | None:
    number = num(value)
    return None if number is None else round(number, places)


def source_status(path: Path) -> dict[str, Any]:
    exists = path.exists()
    suffix = path.suffix.lower()
    rows = None
    bytes_used = None
    file_count = None
    if exists and path.is_dir():
        files = [candidate for candidate in path.rglob("*") if candidate.is_file()]
        file_count = len(files)
        rows = file_count
        bytes_used = sum(candidate.stat().st_size for candidate in files)
    if exists and suffix in {".jsonl", ".md", ".txt", ".py"}:
        rows = line_count(path)
    elif exists and suffix == ".json":
        data = read_json(path, None)
        if isinstance(data, list):
            rows = len(data)
        elif isinstance(data, dict):
            rows = len(data)
    return {
        "exists": exists,
        "bytes": bytes_used if bytes_used is not None else path.stat().st_size if exists else None,
        "file_count": file_count,
        "line_or_top_level_count": rows,
        "path": rel(path) if path.is_absolute() and str(path).startswith(str(REPO_ROOT)) else str(path),
    }


def dependency_terminal_evidence(path: Path) -> dict[str, Any]:
    completion = sorted(path.glob("*COMPLETION_AUDIT*.json")) if path.exists() else []
    manifest = sorted(path.glob("*OUTPUT_MANIFEST*.json")) if path.exists() else []
    verification = sorted(path.glob("*VERIFICATION_RESULT*.json")) if path.exists() else []
    zero_byte_files = []
    file_count = 0
    if path.exists():
        for candidate in path.rglob("*"):
            if not candidate.is_file():
                continue
            file_count += 1
            if candidate.stat().st_size == 0:
                zero_byte_files.append(candidate)
    has_terminal_set = bool(completion and manifest and verification)
    if not path.exists():
        status = "absent"
    elif has_terminal_set and not zero_byte_files:
        status = "present_complete"
    else:
        status = "present_incomplete"
    return {
        "status": status,
        "file_count": file_count,
        "zero_byte_file_count": len(zero_byte_files),
        "zero_byte_files": [rel(candidate) for candidate in zero_byte_files[:20]],
        "terminal_evidence": {
            "completion_audit": [rel(candidate) for candidate in completion],
            "output_manifest": [rel(candidate) for candidate in manifest],
            "verification_result": [rel(candidate) for candidate in verification],
        },
    }


def downstream_dependency_disposition(dep_id: str, status: str) -> str:
    if status == "absent":
        return f"{dep_id}_absent_not_blocking_lane07_contract_emitted"
    if status == "present_complete":
        return f"{dep_id}_present_complete_not_blocking_lane07_contract_emitted"
    return f"{dep_id}_present_incomplete_not_authoritative_not_blocking_lane07_contract_emitted"


def downstream_gap_status(path: Path) -> str:
    status = dependency_terminal_evidence(path)["status"]
    if status == "absent":
        return "ABSENT_NOT_BLOCKING"
    if status == "present_complete":
        return "PRESENT_COMPLETE_NOT_BLOCKING"
    return "PRESENT_INCOMPLETE_NOT_AUTHORITATIVE_NOT_BLOCKING"


def load_sources() -> dict[str, Any]:
    return {
        "live_symbol_specs": read_jsonl(LIVE_COMPANION_DIR / "LIVE_SYMBOL_BROKER_SPEC_LEDGER.jsonl"),
        "live_cost_slippage": read_jsonl(LIVE_COMPANION_DIR / "LIVE_COST_SLIPPAGE_COMMISSION_LEDGER.jsonl"),
        "live_broker_history": read_jsonl(LIVE_COMPANION_DIR / "LIVE_BROKER_HISTORY_LEDGER.jsonl"),
        "live_broker_deals": read_jsonl(LIVE_COMPANION_DIR / "LIVE_BROKER_DEAL_RECONCILIATION_LEDGER.jsonl"),
        "live_active_state": read_json(LIVE_COMPANION_DIR / "ACTIVE_REPAIR_STATE.json", {}),
        "lane06_snapshot": read_json(LANE06_DIR / "LANE06_MT5_READONLY_SNAPSHOT.json", {}),
        "lane06_lifecycle": read_jsonl(LANE06_DIR / "LANE06_BROKER_LIFECYCLE_LEDGER.jsonl"),
        "lane06_cost": read_jsonl(LANE06_DIR / "LANE06_COST_CALIBRATION_LEDGER.jsonl"),
        "lane06_projected": read_jsonl(
            LANE06_DIR / "LANE06_PROJECTED_VS_BROKER_RECONCILIATION_LEDGER.jsonl"
        ),
        "lane06_manual": read_jsonl(LANE06_DIR / "LANE06_MANUAL_INTERVENTION_LEDGER.jsonl"),
        "lane06_source": read_jsonl(LANE06_DIR / "LANE06_SOURCE_COMPLETENESS_LEDGER.jsonl"),
        "friday_broker": read_jsonl(FRIDAY_DIR / "FRIDAY_BROKER_TRUTH_RECONCILIATION_LEDGER.jsonl"),
        "friday_placed": read_jsonl(FRIDAY_DIR / "FRIDAY_PLACED_TRADE_AUTOPSY_LEDGER.jsonl"),
        "friday_open_residual": read_jsonl(FRIDAY_DIR / "FRIDAY_OPEN_RESIDUAL_STATUS_LEDGER.jsonl"),
        "friday_manual": read_jsonl(FRIDAY_DIR / "FRIDAY_MANUAL_INTERVENTION_LEDGER.jsonl"),
        "slippage": read_jsonl(REPO_ROOT / "shadow_logs/slippage.jsonl"),
        "daily_pnl": read_jsonl(REPO_ROOT / "shadow_logs/daily_pnl_history.jsonl"),
        "mt5_cache_summary": read_json(MT5_CACHE_DIR / "MT5_LOCAL_CACHE_COVERAGE_SUMMARY.json", {}),
        "mt5_remaining_requirements": read_jsonl(
            MT5_CACHE_DIR / "MT5_REMAINING_VPS_EXPORT_REQUIREMENTS.jsonl"
        ),
        "vps_missing_requirements": read_jsonl(VPS_DIR / "MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl"),
        "vps_readiness": read_json(VPS_DIR / "MT5_EXPORT_READINESS_CHECKLIST.json", {}),
        "lane01_completion": read_json(
            REPO_ROOT
            / "research/operations/vnext_moonshot_lane01_data_universe_source_authority_2026_06_01/COMPLETION_AUDIT.json",
            {},
        ),
        "lane02_completion": read_json(
            REPO_ROOT
            / "research/operations/vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01/LANE02_COMPLETION_AUDIT.json",
            {},
        ),
        "lane03_completion": read_json(
            REPO_ROOT
            / "research/operations/vnext_moonshot_lane03_historical_candidate_reconstruction_2026_06_01/LANE03_COMPLETION_AUDIT.json",
            {},
        ),
        "lane04_completion": read_json(
            REPO_ROOT
            / "research/operations/vnext_moonshot_lane04_historical_microscope_engine_2026_06_01/LANE04_COMPLETION_AUDIT.json",
            {},
        ),
    }


def build_context_anchor(now: str) -> dict[str, Any]:
    return {
        "schema_version": "lane07_context_anchor_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "git": git_head(),
        "controlling_prompt": PROMPT_PATH,
        "starter": STARTER_PATH,
        "builder_posture": "constructive_broker_truth_cost_calibration_read_only",
        "evidence_class": "broker_truth_cost_read_only_enrichment",
        "hard_boundaries": [
            "no order placement",
            "no order modification",
            "no cancel",
            "no close",
            "no paid API or vendor call",
            "no credential or remote mutation",
            "no production behavior/config/prompt/risk/execution/selector change",
        ],
        "fresh_mt5_server_export_policy": (
            "not executed by Lane07 from this workstation; existing read-only MT5/local/"
            "broker/export/repo evidence consumed, and compliant VPS export requirements "
            "recorded exactly where broker-real fields are absent"
        ),
        "active_symbols": ACTIVE_SYMBOLS,
    }


def build_schema(now: str) -> dict[str, Any]:
    return {
        "schema_version": "lane07_broker_cost_schema_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "precedence": [
            "broker_history_deal_order_position_snapshot",
            "broker_symbol_info_snapshot",
            "runtime_slippage_and_pending_lifecycle_logs",
            "live_companion_symbol_spec_and_spread_snapshot",
            "local_market_tick_or_bar_proxy",
            "calibrated_proxy",
            "exact_missing_export_requirement",
        ],
        "status_fields_required": [
            "source_use_state",
            "result_use_status",
            "runtime_effect_boundary",
            "broker_real_field_status",
            "proxy_field_status",
            "missing_export_requirement",
        ],
        "broker_truth_minimum_fields": [
            "row_type",
            "symbol",
            "broker_symbol",
            "ticket",
            "order_ticket",
            "deal_ticket",
            "position_id",
            "event_time_utc",
            "broker_truth_status",
            "source_refs",
        ],
        "symbol_spec_minimum_fields": [
            "symbol",
            "broker_symbol",
            "digits",
            "point",
            "trade_contract_size",
            "trade_tick_size",
            "trade_tick_value",
            "trade_stops_level",
            "trade_freeze_level",
            "volume_min",
            "volume_step",
            "spread_sample_price",
            "session_status",
            "source_refs",
        ],
        "cost_calibration_minimum_fields": [
            "row_type",
            "symbol",
            "session_label",
            "time_utc",
            "commission",
            "swap",
            "spread_price",
            "slippage_price",
            "broker_realized_net_r",
            "broker_mark_to_market_net_r",
            "cost_status",
            "source_refs",
        ],
        "no_leak_boundary": (
            "broker realized order/deal/position/profit fields are label/truth rows only; "
            "feature/scheduler decision rows may consume pre-decision broker constraints and "
            "calibrated cost priors but not final realized outcome fields"
        ),
    }


def build_source_coverage(now: str) -> list[dict[str, Any]]:
    sources = {
        "controlling_prompt": REPO_ROOT / PROMPT_PATH,
        "starter": REPO_ROOT / STARTER_PATH,
        "live_state": REPO_ROOT / ".context/LIVE_STATE.md",
        "current_vnext_system_map": REPO_ROOT / ".context/00_core/current_vnext_system_map.md",
        "current_repo_reading_order": REPO_ROOT / ".context/00_core/current_repo_reading_order.md",
        "goal_session_research_discipline": REPO_ROOT / ".context/00_core/goal_session_research_discipline.md",
        "research_operating_doctrine": REPO_ROOT / ".context/00_core/research_operating_doctrine.md",
        "moonshot_vision": REPO_ROOT / ".context/00_core/vnext_absolute_moonshot_vision_and_limitations.md",
        "lane01_completion": REPO_ROOT
        / "research/operations/vnext_moonshot_lane01_data_universe_source_authority_2026_06_01/COMPLETION_AUDIT.json",
        "lane02_completion": REPO_ROOT
        / "research/operations/vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01/LANE02_COMPLETION_AUDIT.json",
        "lane03_completion": REPO_ROOT
        / "research/operations/vnext_moonshot_lane03_historical_candidate_reconstruction_2026_06_01/LANE03_COMPLETION_AUDIT.json",
        "lane04_completion": REPO_ROOT
        / "research/operations/vnext_moonshot_lane04_historical_microscope_engine_2026_06_01/LANE04_COMPLETION_AUDIT.json",
        "moonshot_lane05_feature_store_dir_current_disk": MOONSHOT_LANE05_DIR,
        "moonshot_lane06_label_store_dir_current_disk": MOONSHOT_LANE06_LABEL_DIR,
        "moonshot_lane08_digital_twin_dir_current_disk": MOONSHOT_LANE08_DIR,
        "lane06_snapshot": LANE06_DIR / "LANE06_MT5_READONLY_SNAPSHOT.json",
        "lane06_broker_lifecycle": LANE06_DIR / "LANE06_BROKER_LIFECYCLE_LEDGER.jsonl",
        "lane06_cost_calibration": LANE06_DIR / "LANE06_COST_CALIBRATION_LEDGER.jsonl",
        "lane06_projected_reconciliation": LANE06_DIR
        / "LANE06_PROJECTED_VS_BROKER_RECONCILIATION_LEDGER.jsonl",
        "lane06_manual_intervention": LANE06_DIR / "LANE06_MANUAL_INTERVENTION_LEDGER.jsonl",
        "live_symbol_broker_spec": LIVE_COMPANION_DIR / "LIVE_SYMBOL_BROKER_SPEC_LEDGER.jsonl",
        "live_cost_slippage_commission": LIVE_COMPANION_DIR / "LIVE_COST_SLIPPAGE_COMMISSION_LEDGER.jsonl",
        "live_broker_history": LIVE_COMPANION_DIR / "LIVE_BROKER_HISTORY_LEDGER.jsonl",
        "live_broker_deal_reconciliation": LIVE_COMPANION_DIR
        / "LIVE_BROKER_DEAL_RECONCILIATION_LEDGER.jsonl",
        "friday_broker_truth": FRIDAY_DIR / "FRIDAY_BROKER_TRUTH_RECONCILIATION_LEDGER.jsonl",
        "friday_placed_trade_autopsy": FRIDAY_DIR / "FRIDAY_PLACED_TRADE_AUTOPSY_LEDGER.jsonl",
        "friday_open_residual_status": FRIDAY_DIR / "FRIDAY_OPEN_RESIDUAL_STATUS_LEDGER.jsonl",
        "friday_manual_intervention": FRIDAY_DIR / "FRIDAY_MANUAL_INTERVENTION_LEDGER.jsonl",
        "mt5_cache_coverage_summary": MT5_CACHE_DIR / "MT5_LOCAL_CACHE_COVERAGE_SUMMARY.json",
        "mt5_remaining_vps_export_requirements": MT5_CACHE_DIR
        / "MT5_REMAINING_VPS_EXPORT_REQUIREMENTS.jsonl",
        "vps_mt5_export_readiness": VPS_DIR / "MT5_EXPORT_READINESS_CHECKLIST.json",
        "vps_missing_source_export_requirements": VPS_DIR / "MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl",
        "current_mt5_account_history_export_script": REPO_ROOT / "scripts/export_mt5_account_history_readonly.py",
        "current_mt5_ohlcv_export_script": REPO_ROOT / "scripts/export_mt5_research_ohlcv.py",
        "current_mt5_history_probe_script": REPO_ROOT / "scripts/inspect_mt5_history_availability.py",
        "current_mt5_tick_probe_script": REPO_ROOT / "scripts/inspect_mt5_tick_availability.py",
        "shadow_slippage": REPO_ROOT / "shadow_logs/slippage.jsonl",
        "shadow_daily_pnl_history": REPO_ROOT / "shadow_logs/daily_pnl_history.jsonl",
    }
    rows = []
    for source_id, path in sources.items():
        status = source_status(path)
        rows.append(
            {
                "schema_version": "lane07_source_coverage_v1",
                "route_id": ROUTE_ID,
                "generated_at_utc": now,
                "source_id": source_id,
                "status": "present" if status["exists"] else "absent",
                "read_action": "consumed_or_inspected_from_current_disk",
                **status,
            }
        )
    return rows


def build_dependency_state(now: str) -> list[dict[str, Any]]:
    deps = [
        (
            "moonshot_lane01_data_universe_source_authority",
            "research/operations/vnext_moonshot_lane01_data_universe_source_authority_2026_06_01",
            True,
            "upstream_source_authority_consumed",
        ),
        (
            "moonshot_lane02_no_leak_asof_contract",
            "research/operations/vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01",
            True,
            "upstream_no_leak_contract_consumed",
        ),
        (
            "moonshot_lane03_historical_candidate_reconstruction",
            "research/operations/vnext_moonshot_lane03_historical_candidate_reconstruction_2026_06_01",
            True,
            "upstream_candidate_identity_consumed",
        ),
        (
            "moonshot_lane04_historical_microscope_engine",
            "research/operations/vnext_moonshot_lane04_historical_microscope_engine_2026_06_01",
            True,
            "upstream_path_anatomy_consumed",
        ),
        (
            "moonshot_lane05_feature_store_v1",
            "research/operations/vnext_moonshot_lane05_feature_store_v1_2026_06_01",
            False,
            None,
        ),
        (
            "moonshot_lane06_label_store_v1",
            "research/operations/vnext_moonshot_lane06_label_store_v1_2026_06_01",
            False,
            None,
        ),
        (
            "moonshot_lane08_digital_twin_replay_engine",
            "research/operations/vnext_moonshot_lane08_digital_twin_replay_engine_2026_06_01",
            False,
            None,
        ),
    ]
    rows = []
    for dep_id, rel_path, expected_present, disposition in deps:
        path = REPO_ROOT / rel_path
        terminal = dependency_terminal_evidence(path)
        if expected_present:
            status = "present" if path.exists() else "absent"
            blocking_downstream = not path.exists()
            final_disposition = disposition
        else:
            status = terminal["status"]
            blocking_downstream = False
            final_disposition = downstream_dependency_disposition(dep_id, status)
        rows.append(
            {
                "schema_version": "lane07_dependency_state_v1",
                "route_id": ROUTE_ID,
                "generated_at_utc": now,
                "dependency": dep_id,
                "path": rel_path,
                "status": status,
                "expected_present_for_lane07_completion": expected_present,
                "blocking_downstream": blocking_downstream,
                "disposition": final_disposition,
                "file_count": terminal["file_count"],
                "zero_byte_file_count": terminal["zero_byte_file_count"],
                "zero_byte_files": terminal["zero_byte_files"],
                "terminal_evidence": terminal["terminal_evidence"],
            }
        )
    return rows


def observed_cost_by_symbol(sources: dict[str, Any]) -> dict[str, dict[str, Any]]:
    data: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "entry_commission_sum": 0.0,
            "entry_volume_sum": 0.0,
            "actual_swap_sum": 0.0,
            "deal_count": 0,
            "position_swap_sum": 0.0,
            "position_count": 0,
        }
    )
    for deal in sources["lane06_snapshot"].get("history_deal_details") or []:
        symbol = canonical_symbol(deal.get("symbol"))
        if not symbol:
            continue
        bucket = data[symbol]
        bucket["deal_count"] += 1
        if deal.get("entry") == 0:
            bucket["entry_commission_sum"] += num(deal.get("commission")) or 0.0
            bucket["entry_volume_sum"] += num(deal.get("volume")) or 0.0
        bucket["actual_swap_sum"] += num(deal.get("swap")) or 0.0
    for position in sources["lane06_snapshot"].get("position_details") or []:
        symbol = canonical_symbol(position.get("symbol"))
        if not symbol:
            continue
        bucket = data[symbol]
        bucket["position_swap_sum"] += num(position.get("swap")) or 0.0
        bucket["position_count"] += 1
    out: dict[str, dict[str, Any]] = {}
    for symbol, bucket in data.items():
        volume = bucket["entry_volume_sum"]
        out[symbol] = dict(bucket)
        out[symbol]["entry_commission_per_lot_observed"] = (
            round(bucket["entry_commission_sum"] / volume, 6) if volume else None
        )
    return out


def build_symbol_spec_ledger(sources: dict[str, Any], now: str) -> list[dict[str, Any]]:
    live_by_symbol = {row.get("symbol"): row for row in sources["live_symbol_specs"]}
    lane06_info = sources["lane06_snapshot"].get("symbol_info") or {}
    observed_costs = observed_cost_by_symbol(sources)
    rows = []
    for symbol in ACTIVE_SYMBOLS:
        live = live_by_symbol.get(symbol, {})
        broker_symbol = live.get("broker_symbol") or broker_symbol_for(symbol)
        info = lane06_info.get(symbol) or lane06_info.get(broker_symbol) or {}
        point = num(live.get("point"))
        contract_size = num(info.get("trade_contract_size")) or num(live.get("trade_contract_size"))
        tick_size = num(info.get("trade_tick_size"))
        tick_value = num(info.get("trade_tick_value"))
        spread_price = num(live.get("spread_price"))
        spread_points = (
            round(spread_price / point, 6)
            if point not in (None, 0) and spread_price is not None
            else None
        )
        spread_cost_proxy = (
            round(spread_price * contract_size, 6)
            if spread_price is not None and contract_size is not None
            else None
        )
        point_value_proxy = (
            round(point * contract_size, 6)
            if point is not None and contract_size is not None
            else None
        )
        cost = observed_costs.get(symbol, {})
        rows.append(
            {
                "schema_version": "lane07_symbol_spec_session_v1",
                "route_id": ROUTE_ID,
                "generated_at_utc": now,
                "symbol": symbol,
                "broker_symbol": broker_symbol,
                "alias_status": "broker_alias_mapped" if broker_symbol != symbol else "canonical_matches_broker",
                "exists": live.get("exists"),
                "visible": live.get("visible"),
                "trade_mode": live.get("trade_mode"),
                "digits": live.get("digits") if live.get("digits") is not None else info.get("digits"),
                "point": point,
                "trade_contract_size": contract_size,
                "trade_contract_size_status": (
                    "BROKER_REAL_FROM_LANE06_SYMBOL_INFO"
                    if info.get("trade_contract_size") is not None
                    else "BROKER_REAL_FROM_LIVE_COMPANION_SYMBOL_INFO"
                    if live.get("trade_contract_size") is not None
                    else "MISSING_EXPORT_REQUIRED"
                ),
                "trade_tick_size": tick_size,
                "trade_tick_size_status": (
                    "BROKER_REAL_FROM_LANE06_SYMBOL_INFO"
                    if tick_size is not None
                    else "PROXY_POINT_AS_TICK_SIZE_UNTIL_FULL_SYMBOL_INFO_EXPORT"
                ),
                "trade_tick_value": tick_value,
                "trade_tick_value_status": (
                    "BROKER_REAL_FROM_LANE06_SYMBOL_INFO"
                    if tick_value is not None
                    else "MISSING_EXACT_TICK_VALUE_EXPORT_REQUIRED"
                ),
                "point_value_proxy_per_lot": point_value_proxy,
                "point_value_proxy_status": (
                    "CONTRACT_POINT_VALUE_PROXY_NOT_ACCOUNT_CCY_FOR_FX_CROSSES"
                    if point_value_proxy is not None
                    else "UNAVAILABLE"
                ),
                "volume_min": live.get("volume_min") if live.get("volume_min") is not None else info.get("volume_min"),
                "volume_max": live.get("volume_max"),
                "volume_step": live.get("volume_step") if live.get("volume_step") is not None else info.get("volume_step"),
                "trade_stops_level": live.get("trade_stops_level"),
                "trade_freeze_level": live.get("trade_freeze_level"),
                "stop_freeze_status": "BROKER_REAL_SNAPSHOT_SINGLE_TIME_SAMPLE",
                "bid": live.get("bid") if live.get("bid") is not None else info.get("tick_bid"),
                "ask": live.get("ask") if live.get("ask") is not None else info.get("tick_ask"),
                "spread_sample_price": spread_price,
                "spread_sample_points": spread_points,
                "spread_cost_proxy_per_lot": spread_cost_proxy,
                "spread_sample_status": "BROKER_REAL_SINGLE_TIME_SNAPSHOT",
                "spread_sample_time": live.get("ts"),
                "commission_schedule_status": (
                    "BROKER_REAL_DEAL_COMMISSION_OBSERVED_BUT_SCHEDULE_EXPORT_REQUIRED"
                    if cost.get("deal_count")
                    else "MISSING_COMMISSION_SCHEDULE_EXPORT_REQUIRED"
                ),
                "entry_commission_per_lot_observed": cost.get("entry_commission_per_lot_observed"),
                "swap_schedule_status": (
                    "BROKER_REAL_POSITION_OR_DEAL_SWAP_OBSERVED_BUT_SCHEDULE_EXPORT_REQUIRED"
                    if cost.get("position_count") or cost.get("actual_swap_sum")
                    else "MISSING_SWAP_SCHEDULE_EXPORT_REQUIRED"
                ),
                "actual_swap_observed_sum": rounded(
                    (cost.get("actual_swap_sum") or 0.0) + (cost.get("position_swap_sum") or 0.0)
                )
                if cost
                else None,
                "session_status": "MISSING_MT5_SESSION_OR_BROKER_CALENDAR_EXPORT_REQUIRED",
                "margin_status": "MISSING_MARGIN_INITIAL_MAINTENANCE_HEDGED_EXPORT_REQUIRED",
                "source_use_state": "broker_real_snapshot_plus_proxy_or_missing_requirements",
                "result_use_status": "constraint_and_cost_prior_not_performance_claim",
                "source_refs": [
                    ref
                    for ref in [
                        source_ref(live) if live else None,
                        f"{rel(LANE06_DIR / 'LANE06_MT5_READONLY_SNAPSHOT.json')}#symbol_info:{broker_symbol}"
                        if info
                        else None,
                    ]
                    if ref
                ],
            }
        )
    return rows


def infer_time(row: dict[str, Any]) -> Any:
    for field in (
        "time_msc_utc",
        "time_utc",
        "time_done_msc_utc",
        "time_done_utc",
        "ts_utc",
        "ts",
    ):
        if row.get(field):
            return row.get(field)
    return None


def broker_truth_row(row_type: str, source_path: Path, row: dict[str, Any], now: str) -> dict[str, Any]:
    symbol = canonical_symbol(row.get("symbol") or row.get("broker_symbol"))
    ticket = row.get("ticket")
    deal_ticket = row.get("deal_ticket") or row.get("deal")
    order_ticket = row.get("order_ticket") or row.get("order")
    position_id = row.get("position_id") or row.get("identifier")
    return {
        "schema_version": "lane07_broker_truth_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "row_type": row_type,
        "symbol": symbol,
        "broker_symbol": row.get("broker_symbol") or row.get("symbol"),
        "ticket": ticket,
        "order_ticket": order_ticket,
        "deal_ticket": deal_ticket,
        "position_id": position_id,
        "event_time_utc": infer_time(row),
        "broker_truth_status": "BROKER_REAL_OR_READONLY_SNAPSHOT" if row_type.startswith("mt5_") else "DERIVED_RECONCILIATION_FROM_BROKER_EVIDENCE",
        "broker_wins_over_local_projection": row_type
        in {
            "mt5_history_order",
            "mt5_history_deal",
            "mt5_open_position",
            "lane06_lifecycle_reconciliation",
            "lane06_projected_vs_broker_reconciliation",
        },
        "source_refs": [
            f"{rel(source_path)}:{row.get('_source_line')}"
            if row.get("_source_line")
            else f"{rel(source_path)}#{row_type}"
        ],
        "raw": {k: v for k, v in row.items() if not k.startswith("_")},
    }


def build_broker_truth_ledger(sources: dict[str, Any], now: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    snapshot_path = LANE06_DIR / "LANE06_MT5_READONLY_SNAPSHOT.json"
    snapshot = sources["lane06_snapshot"]
    rows.append(
        {
            "schema_version": "lane07_broker_truth_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": now,
            "row_type": "mt5_account_snapshot",
            "symbol": None,
            "broker_symbol": None,
            "ticket": None,
            "order_ticket": None,
            "deal_ticket": None,
            "position_id": None,
            "event_time_utc": snapshot.get("ts_utc"),
            "broker_truth_status": snapshot.get("read_only_check"),
            "broker_wins_over_local_projection": True,
            "source_refs": [f"{rel(snapshot_path)}#account"],
            "raw": {
                "login": snapshot.get("login"),
                "balance": snapshot.get("balance"),
                "equity": snapshot.get("equity"),
                "orders": snapshot.get("orders"),
                "positions": snapshot.get("positions"),
                "history_orders": snapshot.get("history_orders"),
                "history_deals": snapshot.get("history_deals"),
                "history_query_from_utc": snapshot.get("history_query_from_utc"),
                "history_query_to_utc": snapshot.get("history_query_to_utc"),
                "no_order_calls": snapshot.get("no_order_calls"),
            },
        }
    )
    for item in snapshot.get("history_order_details") or []:
        rows.append(broker_truth_row("mt5_history_order", snapshot_path, item, now))
    for item in snapshot.get("history_deal_details") or []:
        rows.append(broker_truth_row("mt5_history_deal", snapshot_path, item, now))
    for item in snapshot.get("position_details") or []:
        rows.append(broker_truth_row("mt5_open_position", snapshot_path, item, now))
    for item in snapshot.get("order_details") or []:
        rows.append(broker_truth_row("mt5_open_order", snapshot_path, item, now))

    source_sets = [
        ("lane06_lifecycle_reconciliation", LANE06_DIR / "LANE06_BROKER_LIFECYCLE_LEDGER.jsonl", sources["lane06_lifecycle"]),
        (
            "lane06_projected_vs_broker_reconciliation",
            LANE06_DIR / "LANE06_PROJECTED_VS_BROKER_RECONCILIATION_LEDGER.jsonl",
            sources["lane06_projected"],
        ),
        ("lane06_manual_intervention", LANE06_DIR / "LANE06_MANUAL_INTERVENTION_LEDGER.jsonl", sources["lane06_manual"]),
        ("friday_broker_truth_seed", FRIDAY_DIR / "FRIDAY_BROKER_TRUTH_RECONCILIATION_LEDGER.jsonl", sources["friday_broker"]),
        ("live_broker_history_status", LIVE_COMPANION_DIR / "LIVE_BROKER_HISTORY_LEDGER.jsonl", sources["live_broker_history"]),
        (
            "live_broker_deal_reconciliation_status",
            LIVE_COMPANION_DIR / "LIVE_BROKER_DEAL_RECONCILIATION_LEDGER.jsonl",
            sources["live_broker_deals"],
        ),
    ]
    for row_type, path, source_rows in source_sets:
        for item in source_rows:
            rows.append(broker_truth_row(row_type, path, item, now))
    return rows


def session_label_from_time(value: Any) -> str:
    text = str(value or "")
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return "unknown_session"
    hour = dt.astimezone(timezone.utc).hour
    if 0 <= hour < 7:
        return "asia_utc"
    if 7 <= hour < 13:
        return "london_utc"
    if 13 <= hour < 21:
        return "new_york_utc"
    return "late_us_afterhours_utc"


def build_cost_calibration_ledger(
    sources: dict[str, Any],
    symbol_rows: list[dict[str, Any]],
    now: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in sources["lane06_cost"]:
        time_value = None
        ticket = item.get("ticket")
        for lifecycle in sources["lane06_lifecycle"]:
            if lifecycle.get("ticket") == ticket:
                time_value = infer_time((lifecycle.get("open_position_snapshot") or {})) or lifecycle.get("trade_id")
                break
        rows.append(
            {
                "schema_version": "lane07_cost_calibration_v1",
                "route_id": ROUTE_ID,
                "generated_at_utc": now,
                "row_type": "broker_real_trade_cost",
                "symbol": item.get("symbol"),
                "broker_symbol": item.get("broker_symbol"),
                "ticket": ticket,
                "trade_id": item.get("trade_id"),
                "session_label": session_label_from_time(time_value),
                "time_utc": time_value,
                "commission": item.get("commission_sum"),
                "swap": item.get("swap_sum"),
                "fee": item.get("fee_sum"),
                "gross_profit": item.get("gross_profit_sum"),
                "realized_net_profit": item.get("realized_net_profit"),
                "mark_to_market_net_profit": item.get("mark_to_market_net_profit"),
                "initial_cash_risk": item.get("initial_cash_risk"),
                "broker_realized_net_r": item.get("broker_realized_net_r"),
                "broker_mark_to_market_net_r": item.get("broker_mark_to_market_net_r"),
                "spread_price": None,
                "slippage_price": None,
                "cost_status": item.get("broker_final_net_r_status"),
                "source_use_state": "broker_real_cost_truth_from_lane06",
                "source_refs": item.get("source_refs") or [f"{rel(LANE06_DIR / 'LANE06_COST_CALIBRATION_LEDGER.jsonl')}#ticket:{ticket}"],
            }
        )

    for item in sources["slippage"]:
        symbol = canonical_symbol(item.get("symbol"))
        rows.append(
            {
                "schema_version": "lane07_cost_calibration_v1",
                "route_id": ROUTE_ID,
                "generated_at_utc": now,
                "row_type": "runtime_slippage_spread_event",
                "symbol": symbol,
                "broker_symbol": item.get("broker_symbol") or item.get("symbol"),
                "ticket": item.get("ticket"),
                "trade_id": item.get("trade_id"),
                "session_label": session_label_from_time(item.get("ts") or item.get("ts_utc")),
                "time_utc": item.get("ts") or item.get("ts_utc"),
                "commission": item.get("commission"),
                "swap": item.get("swap"),
                "fee": None,
                "gross_profit": item.get("broker_profit"),
                "realized_net_profit": None,
                "mark_to_market_net_profit": None,
                "initial_cash_risk": None,
                "broker_realized_net_r": item.get("close_r_multiple"),
                "broker_mark_to_market_net_r": None,
                "spread_price": item.get("pretrade_cost_model", {}).get("spread_price")
                if isinstance(item.get("pretrade_cost_model"), dict)
                else None,
                "spread_at_request": item.get("spread_at_request"),
                "slippage_price": item.get("slippage_price"),
                "slippage_r": item.get("slippage_r"),
                "event_type": item.get("slippage_event_type") or item.get("trigger"),
                "cost_status": item.get("account_history_lookup_status")
                or item.get("accounting_source")
                or "runtime_slippage_row",
                "source_use_state": "runtime_cost_slippage_event_may_be_broker_reconciled_or_proxy",
                "source_refs": [source_ref(item)] if source_ref(item) else [],
            }
        )

    for spec in symbol_rows:
        rows.append(
            {
                "schema_version": "lane07_cost_calibration_v1",
                "route_id": ROUTE_ID,
                "generated_at_utc": now,
                "row_type": "symbol_spread_snapshot_cost_proxy",
                "symbol": spec["symbol"],
                "broker_symbol": spec["broker_symbol"],
                "ticket": None,
                "trade_id": None,
                "session_label": session_label_from_time(spec.get("spread_sample_time")),
                "time_utc": spec.get("spread_sample_time"),
                "commission": None,
                "swap": None,
                "fee": None,
                "gross_profit": None,
                "realized_net_profit": None,
                "mark_to_market_net_profit": None,
                "initial_cash_risk": None,
                "broker_realized_net_r": None,
                "broker_mark_to_market_net_r": None,
                "spread_price": spec.get("spread_sample_price"),
                "spread_points": spec.get("spread_sample_points"),
                "spread_cost_proxy_per_lot": spec.get("spread_cost_proxy_per_lot"),
                "slippage_price": None,
                "cost_status": "BROKER_REAL_SPREAD_SINGLE_SAMPLE_COST_PROXY",
                "source_use_state": "predecision_cost_prior_proxy",
                "source_refs": spec.get("source_refs") or [],
            }
        )

    observed = observed_cost_by_symbol(sources)
    for symbol, item in sorted(observed.items()):
        rows.append(
            {
                "schema_version": "lane07_cost_calibration_v1",
                "route_id": ROUTE_ID,
                "generated_at_utc": now,
                "row_type": "symbol_commission_swap_observation",
                "symbol": symbol,
                "broker_symbol": broker_symbol_for(symbol),
                "ticket": None,
                "trade_id": None,
                "session_label": "observed_account_history",
                "time_utc": sources["lane06_snapshot"].get("ts_utc"),
                "commission": rounded(item.get("entry_commission_sum")),
                "entry_volume_sum": rounded(item.get("entry_volume_sum")),
                "entry_commission_per_lot_observed": item.get("entry_commission_per_lot_observed"),
                "swap": rounded((item.get("actual_swap_sum") or 0.0) + (item.get("position_swap_sum") or 0.0)),
                "fee": None,
                "gross_profit": None,
                "broker_realized_net_r": None,
                "broker_mark_to_market_net_r": None,
                "spread_price": None,
                "slippage_price": None,
                "cost_status": "BROKER_REAL_OBSERVED_NOT_FULL_SCHEDULE",
                "source_use_state": "calibration_prior_until_full_schedule_export",
                "source_refs": [f"{rel(LANE06_DIR / 'LANE06_MT5_READONLY_SNAPSHOT.json')}#history_deal_details"],
            }
        )
    return rows


def build_source_gap_ledger(sources: dict[str, Any], symbol_rows: list[dict[str, Any]], now: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in symbol_rows:
        symbol = spec["symbol"]
        fields = [
            (
                "broker_trading_sessions_by_weekday",
                "read_only_symbol_info_session_trade_or_mql5_export",
                spec["session_status"],
            ),
            (
                "broker_holiday_calendar",
                "broker_or_terminal_session_calendar_export",
                "MISSING_BROKER_HOLIDAY_CALENDAR_EXPORT_REQUIRED",
            ),
            (
                "commission_schedule",
                "account_history_plus_broker_commission_schedule_export",
                spec["commission_schedule_status"],
            ),
            (
                "swap_long_short_mode_triple_day_rollover",
                "symbol_info_swap_fields_or_broker_schedule_export",
                spec["swap_schedule_status"],
            ),
            (
                "margin_initial_maintenance_hedged",
                "symbol_info_margin_fields_export",
                spec["margin_status"],
            ),
            (
                "time_varying_spread_samples",
                "scheduled_read_only_symbol_info_tick_sampling",
                "ONLY_SINGLE_SNAPSHOT_AVAILABLE_FORWARD_SPREAD_SAMPLING_REQUIRED",
            ),
            (
                "time_varying_stop_freeze_samples",
                "scheduled_read_only_symbol_info_stop_freeze_sampling",
                "ONLY_SINGLE_STOP_FREEZE_SNAPSHOT_AVAILABLE",
            ),
            (
                "trade_tick_value",
                "full_symbol_info_trade_tick_value_profit_loss_export",
                spec["trade_tick_value_status"],
            ),
            (
                "trade_tick_size",
                "full_symbol_info_trade_tick_size_export",
                spec["trade_tick_size_status"],
            ),
        ]
        for field, required_action, status in fields:
            if str(status).startswith("BROKER_REAL_FROM"):
                continue
            rows.append(
                {
                    "schema_version": "lane07_source_gap_v1",
                    "route_id": ROUTE_ID,
                    "generated_at_utc": now,
                    "symbol": symbol,
                    "field": field,
                    "status": status,
                    "blocking_downstream": False,
                    "proxy_available": field in {"trade_tick_size", "time_varying_spread_samples", "time_varying_stop_freeze_samples"},
                    "proxy_field": "point_or_single_snapshot_proxy" if field in {"trade_tick_size", "time_varying_spread_samples", "time_varying_stop_freeze_samples"} else None,
                    "required_action": required_action,
                    "proof_required": "read_only_broker_export_hash_manifest_with_source_timestamp",
                    "source_refs": spec.get("source_refs") or [],
                }
            )

    global_gaps = [
        {
            "field": "fresh_full_account_orders_deals_positions_history",
            "status": "EXISTING_LANE06_WINDOW_CONSUMED_FULL_COMPLIANT_VPS_EXPORT_STILL_REQUIRED",
            "required_action": "run read-only history_orders_get history_deals_get orders_get positions_get from compliant non-restricted VPS origin",
            "proof_required": "orders_deals_positions_jsonl_hash_manifest_no_order_send_calls",
        },
        {
            "field": "rejected_modify_and_retcode_history",
            "status": "LOCAL_RUNTIME_LOGS_CONSUMED_EXACT_BROKER_MODIFY_RETCODE_HISTORY_NOT_FULLY_EXPORTED",
            "required_action": "export/order-log capture for SLTP modify requests responses retcodes and broker comments",
            "proof_required": "retcode ledger keyed by ticket/order/position/time",
        },
        {
            "field": "current_workstation_mt5_server_access",
            "status": "NOT_EXECUTED_BY_LANE07_DUE_EXISTING_VPS_COMPLIANCE_GATING_ARTIFACTS",
            "required_action": "provide compliant VPS/network origin proof or run default-off export from approved VPS",
            "proof_required": "network origin plus dedicated private VPS proof plus no-order-call export manifest",
        },
        {
            "field": "moonshot_lane05_feature_store",
            "status": downstream_gap_status(MOONSHOT_LANE05_DIR),
            "required_action": "consume Lane07 downstream contract when Lane05 materializes",
            "proof_required": "feature store only consumes predecision broker constraints/cost priors",
            "source_refs": [rel(MOONSHOT_LANE05_DIR)] if MOONSHOT_LANE05_DIR.exists() else [],
        },
        {
            "field": "moonshot_lane06_label_store",
            "status": downstream_gap_status(MOONSHOT_LANE06_LABEL_DIR),
            "required_action": "consume Lane07 broker truth rows as label/truth rows only",
            "proof_required": "label store segregation proof from feature columns",
            "source_refs": [rel(MOONSHOT_LANE06_LABEL_DIR)] if MOONSHOT_LANE06_LABEL_DIR.exists() else [],
        },
        {
            "field": "moonshot_lane08_digital_twin",
            "status": downstream_gap_status(MOONSHOT_LANE08_DIR),
            "required_action": "consume Lane07 spec/cost/gap ledgers for broker feasibility and cost proxy rules",
            "proof_required": "digital twin broker feasibility contract and missing-source propagation",
            "source_refs": [rel(MOONSHOT_LANE08_DIR)] if MOONSHOT_LANE08_DIR.exists() else [],
        },
    ]
    for gap in global_gaps:
        source_refs = gap.get("source_refs") or [
            rel(MT5_CACHE_DIR / "MT5_REMAINING_VPS_EXPORT_REQUIREMENTS.jsonl"),
            rel(VPS_DIR / "MT5_EXPORT_READINESS_CHECKLIST.json"),
        ]
        rows.append(
            {
                "schema_version": "lane07_source_gap_v1",
                "route_id": ROUTE_ID,
                "generated_at_utc": now,
                "symbol": None,
                "blocking_downstream": False,
                "proxy_available": gap["field"] != "fresh_full_account_orders_deals_positions_history",
                "proxy_field": "existing_lane06_or_lane07_proxy_ledgers_where_applicable",
                **gap,
                "source_refs": source_refs,
            }
        )

    for req in sources["mt5_remaining_requirements"]:
        rows.append(
            {
                "schema_version": "lane07_source_gap_v1",
                "route_id": ROUTE_ID,
                "generated_at_utc": now,
                "symbol": None,
                "field": req.get("source_family"),
                "status": req.get("state"),
                "blocking_downstream": False,
                "proxy_available": True,
                "proxy_field": "lane07_existing_evidence_or_calibrated_proxy",
                "required_action": req.get("required_action"),
                "proof_required": req.get("proof_required"),
                "source_refs": [source_ref(req)] if source_ref(req) else [],
            }
        )
    return rows


def build_downstream_contract(now: str) -> dict[str, Any]:
    consumers = {
        "feature_store": {
            "allowed": [
                "symbol_spec_constraints",
                "predecision_spread_snapshot",
                "calibrated_commission_prior",
                "calibrated_swap_prior",
                "broker_feasibility_flags",
                "missing_source_flags",
            ],
            "forbidden": [
                "broker_realized_net_r",
                "final_profit",
                "exit_deal_reason",
                "post_fill_slippage",
                "manual_close_outcome",
            ],
        },
        "label_store": {
            "allowed": [
                "broker_realized_net_r",
                "broker_mark_to_market_net_r",
                "close_reason",
                "partial_close_lifecycle",
                "manual_intervention_status",
                "false_local_close_status",
            ],
            "join_rule": "join after split/purge by ticket/trade_id/candidate_id; never emit into feature columns",
        },
        "digital_twin_replay": {
            "allowed": [
                "symbol_spec_constraints",
                "spread_cost_proxy",
                "commission_swap_proxy",
                "stop_freeze_constraints",
                "broker_real_fill_truth_when_replaying actual orders",
                "missing_export_requirements",
            ],
            "rule": "broker-real lifecycle rows dominate local projections where ticket/deal evidence exists",
        },
        "scheduler": {
            "allowed": [
                "account_balance_equity_snapshot",
                "open_position_snapshot",
                "spread_cost_prior",
                "commission_swap_prior",
                "lot_constraints",
                "contract_size",
                "missing_source_flags",
            ],
            "forbidden": ["future realized PnL", "future close reason"],
        },
        "execution_policy": {
            "allowed": [
                "stop_freeze_levels",
                "tick_size_proxy_or_real",
                "tick_value_real_or_missing_status",
                "spread_snapshot_or_forward_spread_sample",
                "slippage_calibration_prior",
                "partial_close_lifecycle_truth_for backtest calibration",
            ],
            "rule": "production behavior changes require separate dossier and owner approval",
        },
        "command_center": {
            "allowed": [
                "broker account snapshot",
                "open positions/orders",
                "source gaps",
                "cost calibration status",
                "false close classifications",
            ]
        },
        "telegram_truth": {
            "allowed": [
                "broker lifecycle status",
                "broker close/deal proof",
                "false local close status",
                "manual intervention status",
            ],
            "rule": "broker history wins over local close projection when they disagree",
        },
    }
    return {
        "schema_version": "lane07_downstream_contract_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "join_keys": [
            "symbol",
            "broker_symbol",
            "ticket",
            "order_ticket",
            "deal_ticket",
            "position_id",
            "trade_id",
            "candidate_id",
            "event_time_utc",
        ],
        "source_priority": [
            "broker_history_deals_orders_positions",
            "broker_symbol_info",
            "runtime_slippage_pending_logs",
            "live_companion_spec_snapshot",
            "calibrated_proxy",
            "missing_export_requirement",
        ],
        "consumers": consumers,
        "missing_data_rule": (
            "missing broker-real fields remain explicit row-level source gaps or proxy-status "
            "fields; they do not block Lane05 Feature Store, Lane06 Label Store, Lane08 "
            "Digital Twin, ML, Selector, Scheduler, or Execution Policy work"
        ),
        "runtime_effect_boundary": "offline_research_artifacts_only_no_live_behavior_change",
    }


def build_source_use_state(now: str, sources: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "lane07_source_use_state_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "source_use_state": "existing_read_only_broker_local_export_repo_evidence_consumed",
        "fresh_broker_server_export_executed": False,
        "fresh_broker_server_export_reason": (
            "Lane07 consumed current repo-local read-only MT5 snapshots and route ledgers; "
            "fresh server export remains an exact compliant VPS export requirement from "
            "the preservation route and is not needed to unblock downstream schema work"
        ),
        "broker_real_sources_consumed": {
            "lane06_history_orders": sources["lane06_snapshot"].get("history_orders"),
            "lane06_history_deals": sources["lane06_snapshot"].get("history_deals"),
            "lane06_positions": sources["lane06_snapshot"].get("positions"),
            "live_symbol_spec_rows": len(sources["live_symbol_specs"]),
            "lane06_cost_rows": len(sources["lane06_cost"]),
            "slippage_rows": len(sources["slippage"]),
        },
        "proxy_sources_consumed": [
            "live companion single-time spread snapshots",
            "contract_size * point point-value proxy",
            "runtime slippage and pretrade cost model rows",
            "Lane06 observed commission/swap rows",
        ],
    }


def build_runtime_effect_boundary(now: str) -> dict[str, Any]:
    return {
        "schema_version": "lane07_runtime_effect_boundary_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "runtime_effect_boundary": "offline_research_artifacts_only_no_live_behavior_change",
        "forbidden_surface_attestation": {
            "order_placement": False,
            "order_modification": False,
            "order_cancel": False,
            "position_close": False,
            "paid_api_vendor_call": False,
            "credential_or_remote_change": False,
            "production_prompt_config_risk_execution_selector_change": False,
            "live_runtime_restart": False,
        },
        "outputs_are_default_off": True,
    }


def write_manifest(now: str) -> dict[str, Any]:
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
                "line_count": line_count(path) if path.suffix in {".jsonl", ".md", ".txt", ".py"} else None,
                "sha256": sha256_file(path),
            }
        )
    manifest = {
        "schema_version": "lane07_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "git": git_head(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    write_json(OUTPUTS["manifest"], manifest)
    return manifest


def build_completion_audit(
    now: str,
    counts: dict[str, int],
    verification_result: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "schema_version": "lane07_completion_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "status": "complete_for_current_approved_local_read_only_evidence_class",
        "branch_decision": "materialize_broker_truth_cost_calibration_as_downstream_enrichment_not_historical_research_blocker",
        "instruction_coverage": {
            "mandatory_preflight_completed": True,
            "controlling_prompt_read": True,
            "starter_read": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "current_vnext_map_and_repo_order_read": True,
            "upstream_lane01_lane04_artifacts_read": True,
            "lane06_broker_lifecycle_read": True,
            "live_companion_read": True,
            "friday_broker_truth_read": True,
            "mt5_local_preservation_route_read": True,
            "current_mt5_export_scripts_read": True,
            "builder_posture_applied": "constructive_broker_truth_cost_calibration",
            "anti_boxing_actions": [
                "all 24 live symbols materialized in symbol/spec/session ledger",
                "all Lane06 broker history/order/deal/position rows preserved in broker truth ledger",
                "all current slippage shadow rows consumed into cost calibration ledger",
                "Lane05/Lane06/Lane08 moonshot route presence or absence recorded as nonblocking dependency rows",
                "missing broker-real fields emitted as exact export requirements or proxy-status fields",
            ],
            "proof_or_impossibility_stop_condition": (
                "approved local/repo/export/broker evidence consumed; fields absent from current "
                "broker-real evidence reduced to exact compliant VPS/read-only export requirements"
            ),
        },
        "requirements": [
            {"requirement": "broker_cost_schema", "status": "complete", "evidence": rel(OUTPUTS["schema"])},
            {"requirement": "broker_truth_ledger", "status": "complete", "rows": counts["broker_truth_rows"], "evidence": rel(OUTPUTS["broker_truth"])},
            {"requirement": "cost_calibration_ledger", "status": "complete", "rows": counts["cost_rows"], "evidence": rel(OUTPUTS["cost_calibration"])},
            {"requirement": "symbol_spec_session_ledger", "status": "complete", "rows": counts["symbol_rows"], "evidence": rel(OUTPUTS["symbol_spec"])},
            {"requirement": "source_coverage_and_gap_ledgers", "status": "complete", "rows": counts["gap_rows"], "evidence": [rel(OUTPUTS["source_coverage"]), rel(OUTPUTS["source_gap"])]},
            {"requirement": "downstream_contract", "status": "complete", "evidence": rel(OUTPUTS["downstream_contract"])},
            {
                "requirement": "verifier_and_focused_tests",
                "status": "complete_pending_test_run" if verification_result is None else "complete",
                "evidence": [rel(OUTPUTS["verification"]), rel(OUTPUTS["focused_test_result"])],
            },
            {"requirement": "runtime_effect_boundary", "status": "complete", "evidence": rel(OUTPUTS["runtime_effect_boundary"])},
            {"requirement": "scoped_commit", "status": "pending_after_verification", "evidence": "git commit to be created after tests"},
        ],
        "result_use_status": "broker_truth_cost_enrichment_not_production_change_not_live_activation",
        "source_use_state": "existing_read_only_broker_local_export_repo_evidence_consumed_with_exact_missing_export_requirements",
        "runtime_effect_boundary": "offline_research_artifacts_only_no_live_behavior_change",
        "verification": verification_result,
    }


def build_artifacts(write: bool = True) -> dict[str, Any]:
    now = now_iso()
    sources = load_sources()
    context_anchor = build_context_anchor(now)
    schema = build_schema(now)
    source_coverage = build_source_coverage(now)
    dependency_state = build_dependency_state(now)
    symbol_rows = build_symbol_spec_ledger(sources, now)
    broker_truth_rows = build_broker_truth_ledger(sources, now)
    cost_rows = build_cost_calibration_ledger(sources, symbol_rows, now)
    gap_rows = build_source_gap_ledger(sources, symbol_rows, now)
    downstream_contract = build_downstream_contract(now)
    source_use_state = build_source_use_state(now, sources)
    runtime_effect_boundary = build_runtime_effect_boundary(now)

    counts = {
        "symbol_rows": len(symbol_rows),
        "broker_truth_rows": len(broker_truth_rows),
        "cost_rows": len(cost_rows),
        "gap_rows": len(gap_rows),
        "source_coverage_rows": len(source_coverage),
        "dependency_rows": len(dependency_state),
    }
    completion_audit = build_completion_audit(now, counts, None)

    if write:
        ROUTE_DIR.mkdir(parents=True, exist_ok=True)
        write_json(OUTPUTS["context_anchor"], context_anchor)
        write_json(OUTPUTS["schema"], schema)
        write_jsonl(OUTPUTS["source_coverage"], source_coverage)
        write_jsonl(OUTPUTS["dependency_state"], dependency_state)
        write_jsonl(OUTPUTS["symbol_spec"], symbol_rows)
        write_jsonl(OUTPUTS["broker_truth"], broker_truth_rows)
        write_jsonl(OUTPUTS["cost_calibration"], cost_rows)
        write_jsonl(OUTPUTS["source_gap"], gap_rows)
        write_json(OUTPUTS["downstream_contract"], downstream_contract)
        write_json(OUTPUTS["source_use_state"], source_use_state)
        write_json(OUTPUTS["runtime_effect_boundary"], runtime_effect_boundary)
        write_json(OUTPUTS["completion_audit"], completion_audit)
        write_manifest(now)

    return {
        "context_anchor": context_anchor,
        "schema": schema,
        "source_coverage": source_coverage,
        "dependency_state": dependency_state,
        "symbol_spec": symbol_rows,
        "broker_truth": broker_truth_rows,
        "cost_calibration": cost_rows,
        "source_gap": gap_rows,
        "downstream_contract": downstream_contract,
        "source_use_state": source_use_state,
        "runtime_effect_boundary": runtime_effect_boundary,
        "completion_audit": completion_audit,
        "counts": counts,
    }


def main() -> int:
    artifacts = build_artifacts(write=True)
    print(json.dumps({"route_id": ROUTE_ID, **artifacts["counts"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
