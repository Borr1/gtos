from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_numeric_router_system_recommendations import (
    numeric_router_source_repair_slippage_selection_event_from_adapter,
    summarize_numeric_router_source_repair_slippage_selection_events,
)


IDENTITY_ADAPTER_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_IDENTITY_ADAPTER_LEDGER_{DATE}.jsonl"
)
IDENTITY_ADAPTER_SUMMARY = (
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_IDENTITY_ADAPTER_SUMMARY_{DATE}.json"
)
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_SELECTION_BRIDGE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_SELECTION_BRIDGE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_SELECTION_BRIDGE_MANIFEST_{DATE}.json"

CODE_SURFACES = [
    Path("src/research_infra/moonshot_numeric_router_system_recommendations.py"),
    Path("tests/research_infra/test_moonshot_numeric_router_system_recommendations.py"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


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


def code_surface_summary() -> list[dict[str, Any]]:
    return [
        {
            "path": str(path).replace("\\", "/"),
            "bytes": (REPO / path).stat().st_size,
            "lines": count_lines(REPO / path),
            "sha256": sha256_path(REPO / path),
        }
        for path in CODE_SURFACES
    ]


def selection_row_for_adapter(adapter: dict[str, Any]) -> dict[str, Any]:
    payload = adapter.get("source_repair_identity_payload")
    return payload if isinstance(payload, dict) else {}


def build() -> dict[str, Any]:
    adapter_sha = sha256_path(IDENTITY_ADAPTER_LEDGER)
    adapters = read_jsonl(IDENTITY_ADAPTER_LEDGER)
    adapter_summary = read_json(IDENTITY_ADAPTER_SUMMARY)
    events = [
        numeric_router_source_repair_slippage_selection_event_from_adapter(
            row,
            selection_row_for_adapter(row),
            selection_event_row_id=f"MAIN-ORCH48-NUMERIC-ROUTER-SOURCE-REPAIR-SLIPPAGE-SELECTION-{index:08d}",
        )
        | {
            "source_artifact": str(IDENTITY_ADAPTER_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_line_no": index,
            "source_sha256": adapter_sha,
            "self_check_selection_row_source": "adapter_payload" if row.get("source_repair_identity_payload") else "not_applicable_empty_selection",
        }
        for index, row in enumerate(adapters, start=1)
    ]
    write_jsonl(OUTPUT_LEDGER, events)

    event_summary = summarize_numeric_router_source_repair_slippage_selection_events(events)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_SELECTION_BRIDGE",
        "schema_version": "main_orch48_numeric_router_source_repair_slippage_selection_bridge_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_slippage_identity_adapter_ledger": {
            "path": str(IDENTITY_ADAPTER_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rows": len(adapters),
            "sha256": adapter_sha,
        },
        "input_slippage_identity_adapter_summary": {
            "path": str(IDENTITY_ADAPTER_SUMMARY.relative_to(REPO)).replace("\\", "/"),
            "adapter_rows": adapter_summary.get("adapter_rows"),
            "sha256": sha256_path(IDENTITY_ADAPTER_SUMMARY),
            "payload_ready_rows": adapter_summary.get("payload_ready_rows"),
            "trade_params_patch_rows": adapter_summary.get("trade_params_patch_rows"),
        },
        "code_surfaces": code_surface_summary(),
        "selection_event_rows": event_summary["rows"],
        "slippage_selection_event_status_counts": event_summary["slippage_selection_event_status_counts"],
        "trade_params_patch_rows": event_summary["trade_params_patch_rows"],
        "requires_explicit_future_source_repair_row_selection_rows": event_summary[
            "requires_explicit_future_source_repair_row_selection_rows"
        ],
        "exact_r_repaired_by_this_selection_event_rows": event_summary[
            "exact_r_repaired_by_this_selection_event_rows"
        ],
        "runtime_score_allowed_rows": event_summary["runtime_score_allowed_rows"],
        "runtime_candidate_use_permitted_rows": event_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": event_summary["candidate_use_allowed_now_rows"],
        "unconditional_scalar_use_allowed_rows": event_summary["unconditional_scalar_use_allowed_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": event_summary[
            "replay_r_reference_counted_as_new_main_result_rows"
        ],
        "implementation_effect": {
            "default_off_selection_to_trade_params_identity_patch_self_check": True,
            "runtime_logging_schema_effect_if_runtime_reenabled": False,
            "runtime_trading_or_live_broker_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": summary["route_id"],
        "generated_utc": summary["generated_utc"],
        "outputs": [
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
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
        "route_id": summary["route_id"],
        "selection_event_rows": summary["selection_event_rows"],
        "slippage_selection_event_status_counts": summary["slippage_selection_event_status_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
