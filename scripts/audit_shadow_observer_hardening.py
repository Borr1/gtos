#!/usr/bin/env python3
"""Audit LTO-035 shadow-observer hardening and source registry.

This script writes source-status evidence only. It does not call MT5, AI,
canaries, Databento, Sierra, order, or execution code.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.forward_capture import append_jsonl  # noqa: E402
from src.research_infra.shadow_observer_hardening import (  # noqa: E402
    DEFAULT_AGENT_CONFIG_PATH,
    DEFAULT_OBSERVER_REGISTRY_PATH,
    DEFAULT_STATE_PATH,
    DEFAULT_STATUS_LOG_PATH,
    DEFAULT_STRATEGY_EVALUATIONS_PATH,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_report_payload,
    load_inputs,
    render_markdown,
    render_source_registry_markdown,
)

DEFAULT_HARDENING_STATUS_LOG = Path("shadow_logs/shadow_observer_hardening_status.jsonl")
DEFAULT_SOURCE_REGISTRY_JSON = Path("research/program_control/LTO035_SHADOW_OBSERVER_SOURCE_REGISTRY_2026-05-05.json")
DEFAULT_SOURCE_REGISTRY_MD = Path("research/program_control/LTO035_SHADOW_OBSERVER_SOURCE_REGISTRY_2026-05-05.md")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LTO035_SHADOW_OBSERVER_HARDENING_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LTO035_SHADOW_OBSERVER_HARDENING_2026-05-05.md")


def read_jsonl_with_lines(path: Path) -> list[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return []
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append((line_no, row))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def append_status_row_if_missing(row: dict[str, Any], path: Path) -> int:
    row_key = str(row.get("row_key") or "")
    existing = {str(item.get("row_key") or "") for _, item in read_jsonl_with_lines(path)}
    if not row_key or row_key in existing:
        return 0
    append_jsonl(path, row)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observer-registry", type=Path, default=DEFAULT_OBSERVER_REGISTRY_PATH)
    parser.add_argument("--agent-config", type=Path, default=DEFAULT_AGENT_CONFIG_PATH)
    parser.add_argument("--observer-state", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--observer-status-log", type=Path, default=DEFAULT_STATUS_LOG_PATH)
    parser.add_argument("--strategy-evaluations", type=Path, default=DEFAULT_STRATEGY_EVALUATIONS_PATH)
    parser.add_argument("--status-log", type=Path, default=DEFAULT_HARDENING_STATUS_LOG)
    parser.add_argument("--source-registry-json", type=Path, default=DEFAULT_SOURCE_REGISTRY_JSON)
    parser.add_argument("--source-registry-md", type=Path, default=DEFAULT_SOURCE_REGISTRY_MD)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    observer_registry, agent_config, observer_state = load_inputs(
        observer_registry_path=args.observer_registry,
        agent_config_path=args.agent_config,
        state_path=args.observer_state,
    )
    payload = build_report_payload(
        observer_registry=observer_registry,
        agent_config=agent_config,
        observer_state=observer_state,
        status_rows=read_jsonl_with_lines(args.observer_status_log),
        strategy_rows=read_jsonl_with_lines(args.strategy_evaluations),
        generated_at_utc=generated_at,
    )
    appended = append_status_row_if_missing(payload["status_row"], args.status_log)
    write_json(args.source_registry_json, payload["source_registry"])
    args.source_registry_md.parent.mkdir(parents=True, exist_ok=True)
    args.source_registry_md.write_text(
        render_source_registry_markdown(payload["source_registry"]),
        encoding="utf-8",
    )
    write_json(args.output_json, payload)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "promotion_verdict": PROMOTION_VERDICT,
                "status": payload["status"],
                "rows_appended": appended,
                "active_observers": payload["completion_evidence"]["active_observers"],
                "source_registry_entries": payload["completion_evidence"]["source_registry_entries"],
                "stale_action_required": payload["completion_evidence"]["stale_action_required"],
                "ger40_closeout_confirmed": payload["completion_evidence"]["ger40_closeout_confirmed"],
                "status_log": str(args.status_log),
                "source_registry_json": str(args.source_registry_json),
                "output_json": str(args.output_json),
                "output_md": str(args.output_md),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
