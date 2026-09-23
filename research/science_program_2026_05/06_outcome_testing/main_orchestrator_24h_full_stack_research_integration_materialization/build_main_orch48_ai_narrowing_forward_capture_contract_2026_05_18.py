from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_NARROWING_FORWARD_CAPTURE_CONTRACT"
SCHEMA_VERSION = "main_orch48_ai_narrowing_forward_capture_contract_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.forward_capture import (  # noqa: E402
    COMMON_METADATA_FIELDS,
    build_strategy_follow_candidate_row,
)
from src.research_infra.moonshot_expanded_market_reduced_surface_execution import (  # noqa: E402
    AI_NARROWING_EVENT_REQUIRED_FIELDS,
    ai_narrowing_event_from_source_row,
)


FORWARD_CAPTURE_SOURCE = REPO / "src/research_infra/forward_capture.py"
ORCHESTRATOR_SOURCE = REPO / "src/components/orchestrator.py"
FORWARD_CAPTURE_TEST = REPO / "tests/test_forward_capture_shadow_loggers.py"
RUNTIME_HALT_FLAG = REPO / "pipeline_state/RESEARCH_RUNTIME_HALT.flag"
OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def source_contains(path: Path, text: str) -> bool:
    return text in path.read_text(encoding="utf-8-sig", errors="replace")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def synthetic_candidate_row() -> dict[str, Any]:
    return build_strategy_follow_candidate_row(
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        source_symbol="XAUUSD",
        market_timeframe="M15",
        route_session="ny",
        horizon_id="live_candidate_decision",
        source_component="primary_analyzer_live_candidate",
        selected_side="LONG",
        session="ny",
        kill_zone="ny",
        side="LONG",
        candidate_id="XAUUSD_2026-05-18T13:30:00+00:00",
        decision_time_utc="2026-05-18T13:30:00+00:00",
        analysis_decision="CANDIDATE",
        framework="ob_retest",
        final_outcome="REJECTED_L2",
        trade_parameters={"direction": "LONG"},
    )


def build() -> dict[str, Any]:
    row = synthetic_candidate_row()
    event = ai_narrowing_event_from_source_row(
        row,
        event_row_id="MAIN-ORCH48-AI-NARROWING-FORWARD-CAPTURE-SYNTHETIC-0001",
        source_kind="strategy_follow_candidate_forward_shadow",
        source_artifact="synthetic_build_strategy_follow_candidate_row",
        required_event_fields=AI_NARROWING_EVENT_REQUIRED_FIELDS,
    )
    required_fields_in_common_metadata = all(field in COMMON_METADATA_FIELDS for field in AI_NARROWING_EVENT_REQUIRED_FIELDS)
    required_fields_in_row = all(str(row.get(field) or "") for field in AI_NARROWING_EVENT_REQUIRED_FIELDS)
    orchestrator_passes_source_symbol = source_contains(ORCHESTRATOR_SOURCE, "source_symbol=self._symbol")
    forward_capture_test_asserts_fields = source_contains(FORWARD_CAPTURE_TEST, "horizon_id")
    runtime_halt_active = RUNTIME_HALT_FLAG.exists()

    rows = [
        {
            "contract_row_id": "MAIN-ORCH48-AI-NARROWING-FWD-CAPTURE-0001",
            "schema_version": SCHEMA_VERSION,
            "check": "COMMON_METADATA_EXPOSES_AI_NARROWING_FIELDS",
            "source_path": display_path(FORWARD_CAPTURE_SOURCE),
            "source_sha256": sha256_path(FORWARD_CAPTURE_SOURCE),
            "required_fields": list(AI_NARROWING_EVENT_REQUIRED_FIELDS),
            "required_fields_in_common_metadata": required_fields_in_common_metadata,
            "runtime_decision_effect": False,
            "prompt_risk_execution_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "contract_row_id": "MAIN-ORCH48-AI-NARROWING-FWD-CAPTURE-0002",
            "schema_version": SCHEMA_VERSION,
            "check": "SYNTHETIC_CANDIDATE_ROW_ADAPTS_TO_COMPLETE_EVENT",
            "candidate_schema_version": row.get("schema_version"),
            "event_schema_version": event.get("schema_version"),
            "event_adapter_status": event.get("event_adapter_status"),
            "missing_required_fields": event.get("missing_required_fields"),
            "required_fields_in_row": required_fields_in_row,
            "ai_call_skip_allowed_now": event.get("ai_call_skip_allowed_now"),
            "runtime_candidate_use_permitted": event.get("runtime_candidate_use_permitted"),
            "runtime_decision_effect": False,
            "prompt_risk_execution_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "contract_row_id": "MAIN-ORCH48-AI-NARROWING-FWD-CAPTURE-0003",
            "schema_version": SCHEMA_VERSION,
            "check": "ORCHESTRATOR_SOURCE_SYMBOL_AND_TEST_COVERAGE",
            "orchestrator_source_path": display_path(ORCHESTRATOR_SOURCE),
            "orchestrator_source_sha256": sha256_path(ORCHESTRATOR_SOURCE),
            "test_source_path": display_path(FORWARD_CAPTURE_TEST),
            "test_source_sha256": sha256_path(FORWARD_CAPTURE_TEST),
            "orchestrator_passes_source_symbol": orchestrator_passes_source_symbol,
            "forward_capture_test_asserts_fields": forward_capture_test_asserts_fields,
            "runtime_decision_effect": False,
            "prompt_risk_execution_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "contract_row_id": "MAIN-ORCH48-AI-NARROWING-FWD-CAPTURE-0004",
            "schema_version": SCHEMA_VERSION,
            "check": "SESSION_57_RUNTIME_HALT_BOUNDARY",
            "source_path": display_path(RUNTIME_HALT_FLAG),
            "runtime_halt_active": runtime_halt_active,
            "live_runtime_restart_now": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
        },
    ]
    write_jsonl(OUTPUT_LEDGER, rows)

    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "contract_rows": len(rows),
        "required_fields": list(AI_NARROWING_EVENT_REQUIRED_FIELDS),
        "required_fields_in_common_metadata": required_fields_in_common_metadata,
        "required_fields_in_synthetic_candidate_row": required_fields_in_row,
        "synthetic_event_adapter_status": event.get("event_adapter_status"),
        "synthetic_event_missing_required_fields": event.get("missing_required_fields"),
        "orchestrator_passes_source_symbol": orchestrator_passes_source_symbol,
        "forward_capture_test_asserts_fields": forward_capture_test_asserts_fields,
        "runtime_halt_active": runtime_halt_active,
        "implementation_effect": {
            "future_strategy_follow_candidate_rows_contract_complete": required_fields_in_row,
            "current_ai_runtime_behavior": "UNCHANGED_DEFAULT_AI_DECISION_GATE",
            "ai_call_skip_allowed_now": False,
            "production_change_opened_now": False,
            "live_ai_runtime_change_now": False,
            "live_selector_change_now": False,
            "runtime_candidate_use_permitted": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": summary["generated_utc"],
        "outputs": [
            {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "lines": count_lines(path),
                "sha256": sha256_path(path),
            }
            for path in outputs
        ],
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return {
        "ok": True,
        "route_id": ROUTE_ID,
        "contract_rows": len(rows),
        "synthetic_event_adapter_status": event.get("event_adapter_status"),
        "runtime_halt_active": runtime_halt_active,
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
