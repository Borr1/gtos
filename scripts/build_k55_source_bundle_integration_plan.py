#!/usr/bin/env python3
"""Build the K55 source-bundle integration plan for LTO-031/LTO-032 artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.k55_source_bundle_integration_plan import (  # noqa: E402
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_payload,
    write_outputs,
)

DEFAULT_OUTPUT_JSON = Path("research/program_control/K55_SOURCE_BUNDLE_INTEGRATION_PLAN_2026-05-06.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/K55_SOURCE_BUNDLE_INTEGRATION_PLAN_2026-05-06.md")
DEFAULT_OPERATIONS_MD = Path("research/operations/K55_SOURCE_BUNDLE_INTEGRATION_PLAN_2026-05-06.md")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--operations-md", type=Path, default=DEFAULT_OPERATIONS_MD)
    parser.add_argument("--generated-at-utc", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(
        repo_root=args.repo_root,
        generated_at_utc=args.generated_at_utc,
    )
    write_outputs(payload, args.output_json, args.output_md, args.operations_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "promotion_verdict": PROMOTION_VERDICT,
                "schema": SCHEMA_VERSION,
                "source_bundle_count": payload["source_bundle_count"],
                "source_bundle_ready_for_numeric_features": payload["source_bundle_ready_for_numeric_features"],
                "validation_issues": payload["validation_issues"],
                "paid_data_calls": payload["paid_data_calls"],
                "paid_fetch_attempted": payload["paid_fetch_attempted"],
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
