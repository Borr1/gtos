from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_FROZEN_UNIVERSE_CONSUMPTION"
SCHEMA_VERSION = "main_orch48_frozen_universe_consumption_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
MOONSHOT_ROOT = Path("C:/tmp/")
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_frozen_universe_main_consumption import (  # noqa: E402
    SCHEMA_VERSION as CONSUMPTION_SCHEMA_VERSION,
    build_artifact_consumption_rows,
    build_consumption_order_rows,
    build_count_check_rows,
    load_packet,
    moonshot_route_dir,
    summarize_consumption,
)


HELPER = REPO / "src/research_infra/moonshot_frozen_universe_main_consumption.py"
TEST_FILE = REPO / "tests/research_infra/test_moonshot_frozen_universe_main_consumption.py"
OUTPUT_ARTIFACT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_ARTIFACT_LEDGER_{DATE}.jsonl"
OUTPUT_ORDER_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_ORDER_LEDGER_{DATE}.jsonl"
OUTPUT_COUNT_CHECK_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_COUNT_CHECK_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"

EXPECTED_TEST_NAMES = [
    "test_artifact_consumption_rows_preserve_owner_and_boundaries",
    "test_order_and_count_rows_keep_source_checks",
    "test_summary_carries_cp280_cp281_cp282_key_counts",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def run_git_in_moonshot(*args: str) -> dict[str, Any]:
    result = subprocess.run(
        ["git", "-c", "safe.directory=C:/tmp/", "-C", str(MOONSHOT_ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "args": ["git", "-c", "safe.directory=C:/tmp/", "-C", str(MOONSHOT_ROOT), *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def code_surface(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "bytes": path.stat().st_size,
        "lines": count_lines(path),
        "sha256": sha256_path(path),
    }


def test_coverage(test_text: str) -> dict[str, bool]:
    return {name: name in test_text for name in EXPECTED_TEST_NAMES}


def build() -> dict[str, Any]:
    generated_at = utc_now()
    moonshot_head_result = run_git_in_moonshot("rev-parse", "HEAD")
    moonshot_status_result = run_git_in_moonshot("status", "--short")
    moonshot_head = moonshot_head_result["stdout"]
    moonshot_status_clean = moonshot_status_result["returncode"] == 0 and not moonshot_status_result["stdout"]
    route_dir = moonshot_route_dir(MOONSHOT_ROOT)
    packet = load_packet(route_dir)

    artifact_rows = build_artifact_consumption_rows(
        packet["artifact_rows"],
        packet["consumption_order_rows"],
        moonshot_head=moonshot_head,
        moonshot_status_clean=moonshot_status_clean,
    )
    order_rows = build_consumption_order_rows(
        packet["consumption_order_rows"],
        moonshot_head=moonshot_head,
        moonshot_status_clean=moonshot_status_clean,
    )
    count_rows = build_count_check_rows(
        packet["count_check_rows"],
        moonshot_head=moonshot_head,
        moonshot_status_clean=moonshot_status_clean,
    )

    write_jsonl(OUTPUT_ARTIFACT_LEDGER, artifact_rows)
    write_jsonl(OUTPUT_ORDER_LEDGER, order_rows)
    write_jsonl(OUTPUT_COUNT_CHECK_LEDGER, count_rows)

    tests = test_coverage(TEST_FILE.read_text(encoding="utf-8"))
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated_at,
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "moonshot_git_head": moonshot_head_result,
        "moonshot_git_status": moonshot_status_result,
        "code_surfaces": [
            code_surface(HELPER),
            code_surface(TEST_FILE),
            code_surface(Path(__file__)),
        ],
        **summarize_consumption(
            packet=packet,
            artifact_rows=artifact_rows,
            order_rows=order_rows,
            count_rows=count_rows,
            moonshot_root=MOONSHOT_ROOT,
            moonshot_head=moonshot_head,
            moonshot_status_clean=moonshot_status_clean,
        ),
        "consumption_schema_version": CONSUMPTION_SCHEMA_VERSION,
        "expected_test_name_coverage": tests,
        "expected_test_names_covered_rows": sum(tests.values()),
        "stale_cp215_cp223_not_controlling": True,
        "can_continue_to_cp281_row_mapping": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [
        OUTPUT_ARTIFACT_LEDGER,
        OUTPUT_ORDER_LEDGER,
        OUTPUT_COUNT_CHECK_LEDGER,
        OUTPUT_SUMMARY,
    ]
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated_at,
        "outputs": [
            {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "lines": count_lines(path),
                "sha256": sha256_path(path),
            }
            for path in outputs
        ],
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return {
        "ok": True,
        "route_id": ROUTE_ID,
        "artifact_rows": len(artifact_rows),
        "consumption_order_rows": len(order_rows),
        "count_check_rows": len(count_rows),
        "moonshot_head": moonshot_head,
        "moonshot_status_clean": moonshot_status_clean,
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
