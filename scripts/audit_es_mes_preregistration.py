#!/usr/bin/env python3
"""Audit LTO-029 ES/MES strategy-cohort preregistration.

The script writes preregistration/source-status evidence only. It does not
open outcomes, replay trades, call AI/canaries/MT5/orders, or use paid data.
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

from src.research_infra.es_mes_preregistration import (  # noqa: E402
    DEFAULT_CONVERSION_STATUS_PATH,
    DEFAULT_LABEL_STATUS_PATH,
    DEFAULT_PRIOR_PREREG_PATH,
    DEFAULT_REGISTRY_PATH,
    DEFAULT_SIERRA_INVENTORY_PATH,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_report_payload,
    default_registry_payload,
    render_markdown,
    render_registry_markdown,
)
from src.research_infra.forward_capture import append_jsonl  # noqa: E402

DEFAULT_STATUS_LOG = Path("shadow_logs/es_mes_preregistration_status.jsonl")
DEFAULT_REGISTRY_MD = Path("research/program_control/ES_MES_STRATEGY_COHORT_REGISTRY_2026-05-05.md")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LTO029_ES_MES_STRATEGY_COHORT_PREREGISTRATION_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LTO029_ES_MES_STRATEGY_COHORT_PREREGISTRATION_2026-05-05.md")


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def append_status_row_if_missing(row: dict[str, Any], path: Path) -> int:
    row_key = str(row.get("row_key") or "")
    existing = {str(item.get("row_key") or "") for _, item in read_jsonl_with_lines(path)}
    if not row_key or row_key in existing:
        return 0
    append_jsonl(path, row)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--registry-md", type=Path, default=DEFAULT_REGISTRY_MD)
    parser.add_argument("--prior-preregistration", type=Path, default=DEFAULT_PRIOR_PREREG_PATH)
    parser.add_argument("--conversion-status", type=Path, default=DEFAULT_CONVERSION_STATUS_PATH)
    parser.add_argument("--label-status", type=Path, default=DEFAULT_LABEL_STATUS_PATH)
    parser.add_argument("--sierra-inventory", type=Path, default=DEFAULT_SIERRA_INVENTORY_PATH)
    parser.add_argument("--status-log", type=Path, default=DEFAULT_STATUS_LOG)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    registry = read_json(args.registry) or default_registry_payload(generated_at)
    write_json(args.registry, registry)
    args.registry_md.parent.mkdir(parents=True, exist_ok=True)
    args.registry_md.write_text(render_registry_markdown(registry), encoding="utf-8")

    payload = build_report_payload(
        root=ROOT,
        registry=registry,
        prior_preregistration=read_json(args.prior_preregistration),
        conversion_status=read_json(args.conversion_status),
        label_status=read_json(args.label_status),
        sierra_inventory=read_json(args.sierra_inventory),
        registry_path=args.registry,
        generated_at_utc=generated_at,
    )
    appended = append_status_row_if_missing(payload["status_row"], args.status_log)
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
                "opened_outcome_slices_at_registration": payload["status_row"][
                    "opened_outcome_slices_at_registration"
                ],
                "opened_outcome_artifacts": payload["status_row"]["opened_outcome_artifacts"],
                "status_log": str(args.status_log),
                "registry": str(args.registry),
                "output_json": str(args.output_json),
                "output_md": str(args.output_md),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
