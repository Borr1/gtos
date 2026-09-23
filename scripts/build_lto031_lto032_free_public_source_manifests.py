#!/usr/bin/env python3
"""Build P1 free/public and existing-feed manifests for LTO-031/LTO-032.

No data is fetched by this script. It reads the P0 registry, inventories local
cache evidence, and writes source-control artifacts only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_lto031_lto032_source_unblocking_plan import build_source_contracts  # noqa: E402
from src.research_infra.lto_free_public_feed_manifests import (  # noqa: E402
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_manifest_payload,
    write_outputs,
)
from src.research_infra.lto_source_contract_registry import build_registry_payload  # noqa: E402

DEFAULT_REGISTRY_JSON = Path("research/program_control/LTO031_LTO032_SOURCE_CONTRACT_REGISTRY_2026-05-06.json")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LTO031_LTO032_FREE_PUBLIC_SOURCE_MANIFESTS_2026-05-06.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LTO031_LTO032_FREE_PUBLIC_SOURCE_MANIFESTS_2026-05-06.md")
DEFAULT_OPERATIONS_MD = Path("research/operations/LTO031_LTO032_FREE_PUBLIC_SOURCE_MANIFESTS_2026-05-06.md")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_or_build_registry(path: Path, generated_at_utc: str | None) -> dict:
    payload = read_json(path)
    if payload.get("registry_rows"):
        return payload
    return build_registry_payload(build_source_contracts(), generated_at_utc=generated_at_utc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--external-root", type=Path, default=None)
    parser.add_argument("--registry-json", type=Path, default=DEFAULT_REGISTRY_JSON)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--operations-md", type=Path, default=DEFAULT_OPERATIONS_MD)
    parser.add_argument("--generated-at-utc", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry = load_or_build_registry(args.registry_json, args.generated_at_utc)
    payload = build_manifest_payload(
        registry,
        repo_root=args.repo_root,
        external_root=args.external_root,
        generated_at_utc=args.generated_at_utc,
    )
    write_outputs(payload, args.output_json, args.output_md, args.operations_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "promotion_verdict": PROMOTION_VERDICT,
                "schema": SCHEMA_VERSION,
                "manifest_count": payload["manifest_count"],
                "manifest_status_counts": payload["manifest_status_counts"],
                "source_index_row_count": payload["source_index_row_count"],
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
