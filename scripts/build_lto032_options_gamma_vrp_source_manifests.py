#!/usr/bin/env python3
"""Build LTO-032 options/gamma/VRP source manifest artifacts.

No data is fetched by this script. It reads the source-contract registry,
inventories local FlashAlpha/FRED-style evidence, and writes manifest artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_lto031_lto032_free_public_source_manifests import load_or_build_registry  # noqa: E402
from src.research_infra.lto_options_gamma_vrp_source_manifests import (  # noqa: E402
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_payload,
    write_outputs,
)

DEFAULT_REGISTRY_JSON = Path("research/program_control/LTO031_LTO032_SOURCE_CONTRACT_REGISTRY_2026-05-06.json")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LTO032_OPTIONS_GAMMA_VRP_SOURCE_MANIFESTS_2026-05-06.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LTO032_OPTIONS_GAMMA_VRP_SOURCE_MANIFESTS_2026-05-06.md")
DEFAULT_OPERATIONS_MD = Path("research/operations/LTO032_OPTIONS_GAMMA_VRP_SOURCE_MANIFESTS_2026-05-06.md")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--registry-json", type=Path, default=DEFAULT_REGISTRY_JSON)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--operations-md", type=Path, default=DEFAULT_OPERATIONS_MD)
    parser.add_argument("--generated-at-utc", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry = load_or_build_registry(args.registry_json, args.generated_at_utc)
    payload = build_payload(
        registry,
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
                "source_row_count": payload["source_row_count"],
                "source_status_counts": payload["source_status_counts"],
                "validation_safe_counts": payload["validation_safe_counts"],
                "historical_validation_allowed_counts": payload["historical_validation_allowed_counts"],
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
