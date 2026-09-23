#!/usr/bin/env python3
"""Audit LTO-030 6B common-second and SI depth-definition source policy.

This script reads prior local Sierra/Databento sampling parity audit artifacts
and writes an append-only source-policy status lane. It does not parse Sierra
depth files, call Databento, call AI, call canaries, or touch order/execution
code.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.forward_capture import append_jsonl  # noqa: E402
from src.research_infra.sierra_6b_si_depth_policy import (  # noqa: E402
    PROMOTION_VERDICT,
    build_report_payload,
)

DEFAULT_6B_AUDIT = Path("research/program_control/EXPANDED_OOS_SIERRA_DEPTH_SAMPLING_AUDIT_GBPUSD_6B_2026-05-04.json")
DEFAULT_SI_AUDIT = Path("research/program_control/EXPANDED_OOS_SIERRA_DEPTH_SAMPLING_AUDIT_XAGUSD_SI_2026-05-04.json")
DEFAULT_SIL_AUDIT = Path("research/program_control/EXPANDED_OOS_SIERRA_DEPTH_SAMPLING_AUDIT_XAGUSD_SIL_TO_SI_2026-05-04.json")
DEFAULT_STATUS_LOG = Path("shadow_logs/sierra_6b_si_depth_policy_status.jsonl")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LTO030_6B_SI_DEPTH_POLICY_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LTO030_6B_SI_DEPTH_POLICY_2026-05-05.md")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            row = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def append_status_rows_if_missing(rows: list[dict[str, Any]], path: Path) -> int:
    existing = {str(row.get("row_key") or "") for row in read_jsonl(path)}
    appended = 0
    for row in rows:
        key = str(row.get("row_key") or "")
        if not key or key in existing:
            continue
        append_jsonl(path, row)
        existing.add(key)
        appended += 1
    return appended


def _fmt(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# LTO030 6B / SI Depth Policy - 2026-05-05",
        "",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Summary",
        "",
        payload["synthesis"]["summary"],
        "",
        "## Policy Rows",
        "",
        "| Symbol | Source | Futures | Status | Current depth use | After-policy depth use | Event15 common | Event15 common max delta |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in payload["status_rows"]:
        summary = row.get("validation_summary") or {}
        if row["symbol"] == "GBPUSD":
            event15 = ((summary.get("event15") or {}))
        else:
            event15 = (((summary.get("source") or {}).get("event15") or {}))
        lines.append(
            "| {symbol} | `{source}` | `{futures}` | `{status}` | {current} | {after} | {common} | {delta} |".format(
                symbol=row["symbol"],
                source=row.get("source_symbol"),
                futures=row.get("futures_symbol"),
                status=row["status"],
                current=str(row["depth_interpretation_allowed_current"]).lower(),
                after=str(row["depth_interpretation_allowed_after_policy"]).lower(),
                common=_fmt(event15.get("common_count")),
                delta=_fmt(event15.get("common_seconds_max_abs_delta")),
            )
        )
    lines.extend(
        [
            "",
            "## 6B Common-Second Policy",
            "",
            "- GBPUSD/6B depth features are not interpreted from unaligned Sierra-only seconds.",
            "- A future usable row must declare `sample_alignment_policy=6b_common_second_alignment_v1` and carry the reference-second source, common-second count, coverage Jaccard, all-seconds delta, and common-seconds delta.",
            "- Existing current rows keep source/depth blockers until an aligned feature row exists.",
            "",
            "## SI Depth Definition",
            "",
            "- SIM and SIL remain blocked for XAGUSD/SI depth interpretation.",
            "- Common-second masking did not remove material depth deltas, so this is not just a sampling-clock issue.",
            "- SI rows remain source-status evidence only until source/contract/depth semantics are registered and re-tested.",
            "",
            "## Boundary",
            "",
            "This is source-policy infrastructure only. It is not a live filter, signal, risk modifier, or promotion dossier.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-6b", default=str(DEFAULT_6B_AUDIT))
    parser.add_argument("--audit-si", default=str(DEFAULT_SI_AUDIT))
    parser.add_argument("--audit-sil", default=str(DEFAULT_SIL_AUDIT))
    parser.add_argument("--status-log", default=str(DEFAULT_STATUS_LOG))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    audit_paths = {
        "6b": Path(args.audit_6b),
        "si": Path(args.audit_si),
        "sil": Path(args.audit_sil),
    }
    payload = build_report_payload(audit_paths=audit_paths)
    status_log = Path(args.status_log)
    appended = append_status_rows_if_missing(payload["status_rows"], status_log)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "promotion_verdict": PROMOTION_VERDICT,
                "status_rows": len(payload["status_rows"]),
                "status_rows_appended": appended,
                "output_json": str(output_json),
                "output_md": str(output_md),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
