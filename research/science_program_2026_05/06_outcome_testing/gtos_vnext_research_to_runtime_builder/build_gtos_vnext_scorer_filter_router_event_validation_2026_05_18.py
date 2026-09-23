from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "GTOS_VNEXT_SCORER_FILTER_ROUTER_EVENT_VALIDATION"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.gtos_vnext_default_off_registry import (  # noqa: E402
    DEFAULT_EVENT_SOURCE_PATHS,
    DEFAULT_SCORER_FILTER_ROUTER_LEDGER,
    GTOSVNextDefaultOffRegistry,
    SURFACE,
    summarize_event_validation,
    validate_event_source,
)
from src.research_infra.gtos_vnext_evidence_system import (  # noqa: E402
    SCHEMA_VERSION,
    sha256_path,
    write_json,
    write_jsonl,
)


SOURCE_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SOURCE_SUMMARY_LEDGER_{DATE}.jsonl"
SCOPE_ROLLUP = ROUTE_DIR / f"{ROUTE_ID}_SCOPE_ROLLUP_LEDGER_{DATE}.jsonl"
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


def source_surface(path: Path) -> dict[str, Any]:
    full = REPO / path
    return {
        "path": display_path(full),
        "exists": full.exists(),
        "bytes": full.stat().st_size if full.exists() else 0,
        "lines": count_lines(full) if full.exists() else 0,
        "sha256": sha256_path(full) if full.exists() else "",
    }


def build() -> dict[str, Any]:
    generated = utc_now()
    registry = GTOSVNextDefaultOffRegistry.from_jsonl(REPO / DEFAULT_SCORER_FILTER_ROUTER_LEDGER)
    source_summary_rows: list[dict[str, Any]] = []
    scope_rollup_rows: list[dict[str, Any]] = []
    for source in DEFAULT_EVENT_SOURCE_PATHS:
        source_summary, rollups = validate_event_source(registry, REPO / source, repo=REPO)
        source_summary_rows.append(source_summary)
        scope_rollup_rows.extend(rollups)

    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "main_repo_head_at_build": run_git("rev-parse", "HEAD"),
        "source_event_surfaces": [source_surface(path) for path in DEFAULT_EVENT_SOURCE_PATHS],
        "registry_source_ledger": source_surface(DEFAULT_SCORER_FILTER_ROUTER_LEDGER),
        "code_surfaces": [
            code_surface(REPO / SURFACE),
            code_surface(REPO / "tests/research_infra/test_gtos_vnext_default_off_registry.py"),
            code_surface(Path(__file__)),
        ],
        **summarize_event_validation(source_summary_rows, scope_rollup_rows),
        "full_source_rows_preserved_by": "source_path_line_counts_and_rollup_source_row_hashes_no_sampling",
        "can_continue_to_ranked_default_off_review_surface": True,
    }

    write_jsonl(SOURCE_SUMMARY, source_summary_rows)
    write_jsonl(SCOPE_ROLLUP, scope_rollup_rows)
    write_json(SUMMARY, summary)
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "outputs": [output_surface(SOURCE_SUMMARY), output_surface(SCOPE_ROLLUP), output_surface(SUMMARY)],
        "registry_source_ledger_sha256": sha256_path(REPO / DEFAULT_SCORER_FILTER_ROUTER_LEDGER),
        "source_summary_sha256": sha256_path(SOURCE_SUMMARY),
        "scope_rollup_sha256": sha256_path(SCOPE_ROLLUP),
    }
    write_json(MANIFEST, manifest)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
