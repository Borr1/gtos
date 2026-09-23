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
    numeric_router_source_repair_slippage_identity_adapter_for_contract,
    summarize_numeric_router_source_repair_slippage_identity_adapters,
)


JOIN_CONTRACT_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_JOIN_CONTRACT_LEDGER_{DATE}.jsonl"
)
JOIN_CONTRACT_SUMMARY = (
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_JOIN_CONTRACT_SUMMARY_{DATE}.json"
)
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_IDENTITY_ADAPTER_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_IDENTITY_ADAPTER_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_IDENTITY_ADAPTER_MANIFEST_{DATE}.json"

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


def build() -> dict[str, Any]:
    join_contract_sha = sha256_path(JOIN_CONTRACT_LEDGER)
    contracts = read_jsonl(JOIN_CONTRACT_LEDGER)
    join_summary = read_json(JOIN_CONTRACT_SUMMARY)
    adapters = [
        numeric_router_source_repair_slippage_identity_adapter_for_contract(
            row,
            adapter_row_id=f"MAIN-ORCH48-NUMERIC-ROUTER-SOURCE-REPAIR-SLIPPAGE-IDENTITY-{index:08d}",
            source_artifact=str(JOIN_CONTRACT_LEDGER.relative_to(REPO)).replace("\\", "/"),
            source_line_no=index,
            source_sha256=join_contract_sha,
        )
        for index, row in enumerate(contracts, start=1)
    ]
    write_jsonl(OUTPUT_LEDGER, adapters)

    adapter_summary = summarize_numeric_router_source_repair_slippage_identity_adapters(adapters)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_IDENTITY_ADAPTER",
        "schema_version": "main_orch48_numeric_router_source_repair_slippage_identity_adapter_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_slippage_join_contract_ledger": {
            "path": str(JOIN_CONTRACT_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rows": len(contracts),
            "sha256": join_contract_sha,
        },
        "input_slippage_join_contract_summary": {
            "path": str(JOIN_CONTRACT_SUMMARY.relative_to(REPO)).replace("\\", "/"),
            "contract_rows": join_summary.get("contract_rows"),
            "sha256": sha256_path(JOIN_CONTRACT_SUMMARY),
            "slippage_row_identity_binding_required_rows": join_summary.get(
                "slippage_row_identity_binding_required_rows"
            ),
        },
        "code_surfaces": code_surface_summary(),
        "adapter_rows": adapter_summary["rows"],
        "input_action_rows": adapter_summary["input_action_rows"],
        "slippage_identity_adapter_status_counts": adapter_summary[
            "slippage_identity_adapter_status_counts"
        ],
        "slippage_identity_adapter_status_input_action_counts": adapter_summary[
            "slippage_identity_adapter_status_input_action_counts"
        ],
        "payload_ready_rows": adapter_summary["payload_ready_rows"],
        "trade_params_patch_rows": adapter_summary["trade_params_patch_rows"],
        "requires_explicit_future_source_repair_row_selection_rows": adapter_summary[
            "requires_explicit_future_source_repair_row_selection_rows"
        ],
        "exact_r_repaired_by_this_adapter_rows": adapter_summary["exact_r_repaired_by_this_adapter_rows"],
        "runtime_score_allowed_rows": adapter_summary["runtime_score_allowed_rows"],
        "runtime_candidate_use_permitted_rows": adapter_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": adapter_summary["candidate_use_allowed_now_rows"],
        "unconditional_scalar_use_allowed_rows": adapter_summary["unconditional_scalar_use_allowed_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": adapter_summary[
            "replay_r_reference_counted_as_new_main_result_rows"
        ],
        "implementation_effect": {
            "prospective_trade_params_identity_payload_available": True,
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
        "adapter_rows": summary["adapter_rows"],
        "slippage_identity_adapter_status_counts": summary["slippage_identity_adapter_status_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
