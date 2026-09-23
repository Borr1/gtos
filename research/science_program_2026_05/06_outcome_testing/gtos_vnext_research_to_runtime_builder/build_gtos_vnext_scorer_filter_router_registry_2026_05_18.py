from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "GTOS_VNEXT_SCORER_FILTER_ROUTER_REGISTRY"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.gtos_vnext_default_off_registry import (  # noqa: E402
    DEFAULT_SCORER_FILTER_ROUTER_LEDGER,
    GTOSVNextDefaultOffRegistry,
    SURFACE,
    summarize_default_off_registry,
)
from src.research_infra.gtos_vnext_evidence_system import (  # noqa: E402
    SCHEMA_VERSION,
    sha256_path,
    write_json,
    write_jsonl,
)


CATALOG = ROUTE_DIR / f"{ROUTE_ID}_CATALOG_LEDGER_{DATE}.jsonl"
SELF_CHECK = ROUTE_DIR / f"{ROUTE_ID}_SELF_CHECK_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def run_git(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def output_surface(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "bytes": path.stat().st_size,
        "lines": count_lines(path),
        "sha256": sha256_path(path),
    }


def code_surface(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "bytes": path.stat().st_size,
        "lines": count_lines(path),
        "sha256": sha256_path(path),
    }


def build() -> dict[str, Any]:
    generated = utc_now()
    source_path = REPO / DEFAULT_SCORER_FILTER_ROUTER_LEDGER
    registry = GTOSVNextDefaultOffRegistry.from_jsonl(source_path)
    catalog_rows = registry.build_catalog_rows()
    self_check_rows = registry.build_self_check_rows()
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "main_repo_head_at_build": run_git("rev-parse", "HEAD"),
        "source_ledger": {
            "path": display_path(source_path),
            "lines": count_lines(source_path),
            "sha256": sha256_path(source_path),
        },
        "code_surfaces": [
            code_surface(REPO / SURFACE),
            code_surface(REPO / "tests/research_infra/test_gtos_vnext_default_off_registry.py"),
            code_surface(Path(__file__)),
        ],
        **summarize_default_off_registry(registry, self_check_rows),
        "can_continue_to_replay_validator": True,
    }

    write_jsonl(CATALOG, catalog_rows)
    write_jsonl(SELF_CHECK, self_check_rows)
    write_json(SUMMARY, summary)
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "outputs": [output_surface(CATALOG), output_surface(SELF_CHECK), output_surface(SUMMARY)],
        "source_ledger_sha256": sha256_path(source_path),
        "catalog_sha256": sha256_path(CATALOG),
        "self_check_sha256": sha256_path(SELF_CHECK),
    }
    write_json(MANIFEST, manifest)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
