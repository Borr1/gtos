#!/usr/bin/env python3
"""Build the LTO-031/LTO-032 source-contract registry.

This is a P0 control artifact only. It does not fetch public sources, spend
Databento credits, call Sierra/MT5, call AI/canaries, place orders, or alter
live behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_lto031_lto032_source_unblocking_plan import build_source_contracts  # noqa: E402
from src.research_infra.lto_source_contract_registry import (  # noqa: E402
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_registry_payload,
    render_markdown,
    write_registry,
)

DEFAULT_OUTPUT_JSON = Path("research/program_control/LTO031_LTO032_SOURCE_CONTRACT_REGISTRY_2026-05-06.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LTO031_LTO032_SOURCE_CONTRACT_REGISTRY_2026-05-06.md")
DEFAULT_OPERATIONS_MD = Path("research/operations/LTO031_LTO032_SOURCE_CONTRACT_REGISTRY_2026-05-06.md")
DEFAULT_SOURCE_PLAN_PATH = "research/program_control/LTO031_LTO032_SOURCE_UNBLOCKING_AND_REPLAY_PLAN_2026-05-05.md"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def render_operations_summary(payload: dict) -> str:
    blockers = {
        row["source_key"]: row["validation_safe_blockers"]
        for row in payload["registry_rows"]
        if row.get("validation_safe_blockers")
    }
    lines = [
        "# LTO031 / LTO032 Source Contract Registry Result - 2026-05-06",
        "",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        f"**Schema:** `{payload['schema_version']}`",
        "",
        "## Result",
        "",
        (
            "P0 source-contract registry is built for all current LTO-031/LTO-032 source families. "
            "Every row now has URL/vendor, legal/access status, cache schema, publication timestamp rule, "
            "cost policy, allowed feature role, and validation-safety blockers."
        ),
        "",
        "No source is marked validation-safe. That is intentional: this artifact precedes ingest, as-of cache creation, "
        "parser tests, and candidate joins.",
        "",
        "## Counts",
        "",
        f"- Source contracts: `{payload['source_contract_count']}`",
        f"- By LTO: `{payload['source_contract_counts_by_lto']}`",
        f"- Source readiness: `{payload['source_readiness_status_counts']}`",
        f"- Validation-safe rows: `{payload['validation_safe_counts']}`",
        f"- Validation issues: `{payload['validation_issues']}`",
        "",
        "## Source-Safety Decisions",
        "",
        "- Free/public candidates remain planning-ready only until raw evidence and normalized point-in-time rows exist.",
        "- FlashAlpha Basic remains forward-context only, not historical gamma/VRP validation evidence.",
        "- Databento remains existing-credit-only and estimate-before-fetch.",
        "- Paid or licensed gamma sources remain blocked pending a separate future owner approval.",
        "- Sierra and Databento are not substitutes for COT, BIS, Fed/FRED, or official options/gamma source contracts.",
        "",
        "## Validation Blockers",
        "",
        f"`{blockers}`",
        "",
        "## Verification",
        "",
        "- `python -m py_compile src/research_infra/lto_source_contract_registry.py scripts/build_lto031_lto032_source_contract_registry.py`",
        "- `python -m pytest tests/test_lto_source_contract_registry.py tests/test_lto031_lto032_source_unblocking_plan.py -q -p no:cacheprovider --basetemp C:\\tmp\\pytest_phase3_lto_source_registry`",
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "This is research/source-readiness control work only. No live trading behavior changed.",
    ]
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--operations-md", type=Path, default=DEFAULT_OPERATIONS_MD)
    parser.add_argument("--source-plan-path", default=DEFAULT_SOURCE_PLAN_PATH)
    parser.add_argument("--generated-at-utc", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    generated = args.generated_at_utc or utc_now_iso()
    payload = build_registry_payload(
        build_source_contracts(),
        generated_at_utc=generated,
        source_plan_path=args.source_plan_path,
    )
    write_registry(payload, args.output_json, args.output_md)
    args.operations_md.parent.mkdir(parents=True, exist_ok=True)
    args.operations_md.write_text(render_operations_summary(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "promotion_verdict": PROMOTION_VERDICT,
                "schema": SCHEMA_VERSION,
                "source_contract_count": payload["source_contract_count"],
                "validation_safe_counts": payload["validation_safe_counts"],
                "validation_issues": payload["validation_issues"],
                "output_json": str(args.output_json),
                "output_md": str(args.output_md),
                "operations_md": str(args.operations_md),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
