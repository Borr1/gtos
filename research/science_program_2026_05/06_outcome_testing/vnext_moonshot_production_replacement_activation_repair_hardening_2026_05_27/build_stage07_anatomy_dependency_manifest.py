from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-27"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
ANATOMY_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26"
)
QUESTION_STACK = ANATOMY_DIR / "VNEXT_ACTIVATION_QUESTION_STACK_LEDGER_2026-05-26.jsonl"
SUMMARY_OUT = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE07_ANATOMY_INPUT_DEPENDENCY_MANIFEST_{DATE}.json"
FILE_MANIFEST_OUT = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE07_ANATOMY_INPUT_FILE_MANIFEST_{DATE}.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_CONTROL_LEDGER_{DATE}.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    rows = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            rows += chunk.count(b"\n")
    return rows


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> int:
    generated_at = utc_now()
    files = sorted(path for path in ANATOMY_DIR.rglob("*") if path.is_file())
    rows: list[dict[str, Any]] = []
    extension_counts: dict[str, int] = defaultdict(int)
    extension_sizes: dict[str, int] = defaultdict(int)
    total_size = 0
    for path in files:
        size = path.stat().st_size
        total_size += size
        suffix = path.suffix.lower() or "<none>"
        extension_counts[suffix] += 1
        extension_sizes[suffix] += size
        rows.append(
            {
                "path": rel(path),
                "relative_to_anatomy_dir": path.relative_to(ANATOMY_DIR).as_posix(),
                "size_bytes": size,
                "sha256": sha256_file(path),
                "extension": suffix,
            }
        )

    with FILE_MANIFEST_OUT.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")

    question_stack_row = next(
        (row for row in rows if Path(row["path"]).name == QUESTION_STACK.name),
        None,
    )
    stage04_consumed = []
    if question_stack_row:
        stage04_consumed.append(
            {
                "path": question_stack_row["path"],
                "relationship": "stage04_prior_intelligence_source_consumed_into_canonical_ledger",
                "rows": count_lines(QUESTION_STACK),
                "sha256": question_stack_row["sha256"],
                "size_bytes": question_stack_row["size_bytes"],
            }
        )

    summary = {
        "schema_version": "vnext_activation_repair_stage07_anatomy_dependency_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": generated_at,
        "status": "completed_anatomy_dependency_manifest" if ANATOMY_DIR.exists() else "missing_anatomy_dir",
        "anatomy_dir": rel(ANATOMY_DIR),
        "file_count": len(rows),
        "total_size_bytes": total_size,
        "extension_counts": dict(sorted(extension_counts.items())),
        "extension_size_bytes": dict(sorted(extension_sizes.items())),
        "file_manifest_path": rel(FILE_MANIFEST_OUT),
        "stage04_consumed_files": stage04_consumed,
        "committed_route_verifiable_without_untracked_anatomy": True,
        "committed_route_fully_rederivable_from_head_without_untracked_anatomy": False,
        "rederive_limitation": (
            "The committed repair route can be verified from committed outputs, but Stage04 "
            "cannot be independently rebuilt from HEAD alone unless the untracked anatomy "
            "question stack ledger is retained or packaged."
        ),
        "minimum_external_evidence_dependency_for_stage04_rederive": stage04_consumed,
        "retention_packaging_path": (
            "Package the minimum consumed question-stack jsonl plus this manifest in an "
            "external evidence bundle or large-file store before any cleanup of the 18.724 GiB "
            "anatomy input directory."
        ),
    }
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_jsonl(
        CONTROL_LEDGER,
        {
            "event": "stage07_anatomy_dependency_manifest_written",
            "file_count": len(rows),
            "generated_at_utc": generated_at,
            "output": rel(SUMMARY_OUT),
            "route_id": ROUTE_ID,
            "stage04_rederive_requires_untracked_anatomy": True,
            "total_size_bytes": total_size,
        },
    )
    print(json.dumps({"output": rel(SUMMARY_OUT), "file_count": len(rows), "total_size_bytes": total_size}))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
