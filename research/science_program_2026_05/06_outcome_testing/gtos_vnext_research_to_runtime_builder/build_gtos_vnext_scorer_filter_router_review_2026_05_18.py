from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "GTOS_VNEXT_SCORER_FILTER_ROUTER_REVIEW"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.gtos_vnext_default_off_registry import (  # noqa: E402
    DEFAULT_SCORER_FILTER_ROUTER_LEDGER,
    GTOSVNextDefaultOffRegistry,
    SURFACE,
    build_review_rows_from_event_rollups,
    summarize_review_rows,
)
from src.research_infra.gtos_vnext_evidence_system import (  # noqa: E402
    SCHEMA_VERSION,
    read_jsonl,
    sha256_path,
    write_json,
    write_jsonl,
)


EVENT_SCOPE_ROLLUP = ROUTE_DIR / f"GTOS_VNEXT_SCORER_FILTER_ROUTER_EVENT_VALIDATION_SCOPE_ROLLUP_LEDGER_{DATE}.jsonl"
REVIEW_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
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
    registry = GTOSVNextDefaultOffRegistry.from_jsonl(REPO / DEFAULT_SCORER_FILTER_ROUTER_LEDGER)
    rollups = read_jsonl(EVENT_SCOPE_ROLLUP)
    review_rows = build_review_rows_from_event_rollups(registry, rollups)
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "main_repo_head_at_build": run_git("rev-parse", "HEAD"),
        "event_scope_rollup_source": {
            "path": display_path(EVENT_SCOPE_ROLLUP),
            "lines": count_lines(EVENT_SCOPE_ROLLUP),
            "sha256": sha256_path(EVENT_SCOPE_ROLLUP),
        },
        "registry_source_ledger": {
            "path": display_path(REPO / DEFAULT_SCORER_FILTER_ROUTER_LEDGER),
            "lines": count_lines(REPO / DEFAULT_SCORER_FILTER_ROUTER_LEDGER),
            "sha256": sha256_path(REPO / DEFAULT_SCORER_FILTER_ROUTER_LEDGER),
        },
        "code_surfaces": [
            code_surface(REPO / SURFACE),
            code_surface(REPO / "tests/research_infra/test_gtos_vnext_default_off_registry.py"),
            code_surface(Path(__file__)),
        ],
        **summarize_review_rows(review_rows),
        "all_event_scope_rollups_preserved": len(review_rows) == len(rollups),
        "review_use_boundary": "DEFAULT_OFF_REVIEW_ONLY_NOT_RUNTIME_RANKING",
        "can_continue_to_review_dossier_or_runtime_config_surface": True,
    }
    write_jsonl(REVIEW_LEDGER, review_rows)
    write_json(SUMMARY, summary)
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "outputs": [output_surface(REVIEW_LEDGER), output_surface(SUMMARY)],
        "review_ledger_sha256": sha256_path(REVIEW_LEDGER),
        "event_scope_rollup_source_sha256": sha256_path(EVENT_SCOPE_ROLLUP),
        "registry_source_ledger_sha256": sha256_path(REPO / DEFAULT_SCORER_FILTER_ROUTER_LEDGER),
    }
    write_json(MANIFEST, manifest)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
