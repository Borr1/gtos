"""Route-aware artifact intelligence for GTOS Context OS."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from src.gtos_context_os.catalog import DEFAULT_DB_PATH, fetch_documents


IMPORTANT_DOC_TYPES = (
    "SUMMARY",
    "MANIFEST",
    "VERIFICATION",
    "VERIFY",
    "AUDIT",
    "DOSSIER",
    "REPORT",
    "RESULT",
    "PLAN",
    "README",
)
MAX_ROUTE_FILESYSTEM_FILES = 5000


def route_overview(
    route: str,
    *,
    repo: Path | str = ".",
    db_path: Path | str = DEFAULT_DB_PATH,
    limit: int = 25,
) -> dict[str, Any]:
    """Return a deterministic overview for one route.

    The overview intentionally separates compact current artifacts from cold raw
    evidence pointers so agents know what to read first and what to hydrate only
    by exact need.
    """

    rows = fetch_documents(
        db_path=db_path,
        repo=repo,
        where="route = ?",
        params=(route,),
        order_by="path",
    )
    had_catalog_rows = bool(rows)
    manifest = route_filesystem_manifest(route, repo=repo, limit=limit)
    if not rows and manifest["route_exists"]:
        rows = _manifest_rows_for_overview(manifest)
    overview = route_overview_from_rows(route, rows, limit=limit)
    overview["filesystem_manifest"] = manifest
    overview["source"] = (
        "catalog"
        if had_catalog_rows and not manifest["route_exists"]
        else "catalog_plus_exact_route_filesystem"
        if had_catalog_rows and manifest["route_exists"]
        else "exact_route_filesystem"
        if manifest["route_exists"]
        else "catalog_empty_route_missing"
    )
    return overview


def route_filesystem_manifest(
    route: str,
    *,
    repo: Path | str = ".",
    limit: int = 25,
    max_files: int = MAX_ROUTE_FILESYSTEM_FILES,
) -> dict[str, Any]:
    """Return exact route artifact pointers without requiring a deep catalog.

    This scans only `research/operations/<route>` and records metadata pointers.
    It does not read raw ledger bodies.
    """

    repo_path = Path(repo).resolve()
    rel_route = _safe_route_path(route)
    route_path = repo_path / "research" / "operations" / rel_route
    if not route_path.exists() or not route_path.is_dir():
        return {
            "schema_version": "gtos_context_route_filesystem_manifest_v1",
            "route": route,
            "route_exists": False,
            "route_path": route_path.as_posix(),
            "scanned_files": 0,
            "truncated": False,
            "read_first": [],
            "compact_artifacts": [],
            "cold_raw_pointers": [],
            "counts_by_kind": {},
            "use_boundary": "exact_route_filesystem_manifest_is_pointer_intelligence_verify_files_before_claims",
        }

    documents: list[dict[str, Any]] = []
    truncated = False
    scanned = 0
    for path in sorted(route_path.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if scanned >= max_files:
            truncated = True
            break
        documents.append(_route_file_doc(repo_path, path))
        scanned += 1

    compact = [doc for doc in documents if doc["kind"] != "cold_raw"]
    cold_raw = [doc for doc in documents if doc["kind"] == "cold_raw"]
    read_first = [doc for doc in compact if doc["read_priority"] < 50]
    read_first.sort(key=lambda doc: (doc["read_priority"], -int(doc.get("mtime_ns") or 0), doc["path"]))
    compact.sort(key=lambda doc: (doc["read_priority"], -int(doc.get("mtime_ns") or 0), doc["path"]))
    cold_raw.sort(key=lambda doc: (-int(doc["size_bytes"] or 0), doc["path"]))
    counts = Counter(str(doc["kind"]) for doc in documents)
    return {
        "schema_version": "gtos_context_route_filesystem_manifest_v1",
        "route": route,
        "route_exists": True,
        "route_path": route_path.as_posix(),
        "scanned_files": len(documents),
        "truncated": truncated,
        "read_first": read_first[:limit],
        "compact_artifacts": compact[:limit],
        "cold_raw_pointers": cold_raw[: min(limit, 10)],
        "counts_by_kind": dict(sorted(counts.items())),
        "use_boundary": "exact_route_filesystem_manifest_is_pointer_intelligence_verify_files_before_claims",
    }


def route_overview_from_rows(route: str, rows: list[dict[str, object]], *, limit: int = 25) -> dict[str, Any]:
    by_authority = Counter(str(row["authority_tier"]) for row in rows)
    by_evidence = Counter(str(row["evidence_class"]) for row in rows)
    by_status = Counter(str(row["content_status"]) for row in rows)
    raw = [row for row in rows if str(row["authority_tier"]) == "cold_raw_evidence"]
    compact = [row for row in rows if str(row["authority_tier"]) != "cold_raw_evidence"]
    important = [
        row
        for row in compact
        if any(token in Path(str(row["path"])).name.upper() for token in IMPORTANT_DOC_TYPES)
    ]
    important.sort(
        key=lambda row: (
            authority_rank(str(row["authority_tier"])),
            read_priority(row),
            -route_mtime(row),
            str(row["path"]),
        )
    )
    compact.sort(
        key=lambda row: (
            authority_rank(str(row["authority_tier"])),
            read_priority(row),
            -route_mtime(row),
            str(row["path"]),
        )
    )
    raw.sort(key=lambda row: (-int(row["size_bytes"] or 0), str(row["path"])))
    return {
        "route": route,
        "total_documents": len(rows),
        "compact_documents": len(compact),
        "cold_raw_pointers": len(raw),
        "authority_tiers": dict(sorted(by_authority.items())),
        "evidence_classes": dict(sorted(by_evidence.items())),
        "content_statuses": dict(sorted(by_status.items())),
        "read_first": project_docs(important[:limit]),
        "compact_artifacts": project_docs(compact[:limit]),
        "largest_cold_raw_pointers": project_docs(raw[: min(limit, 10)], include_snippet=False),
    }


def authority_rank(authority_tier: str) -> int:
    order = {
        "platinum_current_disk_authority": 0,
        "gold_active_code_config_test": 1,
        "gold_route_summary_manifest": 2,
        "silver_route_artifact": 3,
        "bronze_chat_or_memory": 4,
        "cold_raw_evidence": 5,
        "unknown": 6,
    }
    return order.get(authority_tier, 9)


def read_priority(row: dict[str, object]) -> int:
    try:
        value = row.get("read_priority")
        return 50 if value is None else int(value)
    except (TypeError, ValueError):
        return 50


def route_mtime(row: dict[str, object]) -> int:
    try:
        return int(row.get("mtime_ns") or 0)
    except (TypeError, ValueError):
        return 0


def project_docs(rows: list[dict[str, object]], *, include_snippet: bool = True) -> list[dict[str, object]]:
    projected = []
    for row in rows:
        item = {
            "path": row["path"],
            "title": row["title"],
            "authority_tier": row["authority_tier"],
            "evidence_class": row["evidence_class"],
            "freshness": row["freshness"],
            "content_status": row["content_status"],
            "size_bytes": row["size_bytes"],
            "sha256": row["sha256"],
        }
        if include_snippet:
            item["snippet"] = row.get("snippet", "")
        projected.append(item)
    return projected


def _safe_route_path(route: str) -> Path:
    rel = Path(route)
    if not route or rel.is_absolute() or ".." in rel.parts:
        raise ValueError("route must be a non-empty route name relative to research/operations")
    return rel


def _route_file_doc(repo_path: Path, path: Path) -> dict[str, Any]:
    rel = path.relative_to(repo_path).as_posix()
    stat = path.stat()
    classification = classify_route_file(rel, path.name)
    return {
        "path": rel,
        "title": path.name,
        "authority_tier": classification["authority_tier"],
        "evidence_class": classification["evidence_class"],
        "freshness": classification["freshness"],
        "content_status": classification["content_status"],
        "size_bytes": stat.st_size,
        "sha256": None,
        "snippet": "",
        "kind": classification["kind"],
        "read_priority": classification["read_priority"],
        "mtime_ns": stat.st_mtime_ns,
    }


def classify_route_file(rel: str, name: str) -> dict[str, Any]:
    upper = name.upper()
    suffixes = [suffix.lower() for suffix in Path(name).suffixes]
    is_jsonl = ".jsonl" in suffixes
    is_gzip = ".gz" in suffixes
    is_python = suffixes[-1:] == [".py"]
    if is_jsonl or is_gzip:
        return {
            "kind": "cold_raw",
            "authority_tier": "cold_raw_evidence",
            "evidence_class": "raw_or_large_evidence_pointer",
            "freshness": "cold_unless_route_manifest_requires",
            "content_status": "filesystem_cold_raw_pointer",
            "read_priority": 90,
        }
    if is_python:
        return {
            "kind": "route_script",
            "authority_tier": "silver_route_artifact",
            "evidence_class": "route_artifact",
            "freshness": "route_artifact_verify_against_current_manifest",
            "content_status": "filesystem_route_script_pointer",
            "read_priority": 70,
        }
    if any(token in upper for token in ("MANIFEST", "SUMMARY", "VERIFICATION", "VERIFY", "AUDIT")):
        return {
            "kind": "route_summary_manifest",
            "authority_tier": "gold_route_summary_manifest",
            "evidence_class": "route_summary_manifest_or_verification",
            "freshness": "route_current_if_referenced_by_live_state_or_manifest",
            "content_status": "filesystem_compact_artifact_pointer",
            "read_priority": _important_read_priority(upper),
        }
    if any(token in upper for token in IMPORTANT_DOC_TYPES):
        return {
            "kind": "compact_route_artifact",
            "authority_tier": "silver_route_artifact",
            "evidence_class": "route_artifact",
            "freshness": "route_artifact_verify_against_current_manifest",
            "content_status": "filesystem_compact_artifact_pointer",
            "read_priority": _important_read_priority(upper),
        }
    return {
        "kind": "other_route_artifact",
        "authority_tier": "silver_route_artifact",
        "evidence_class": "route_artifact",
        "freshness": "route_artifact_verify_against_current_manifest",
        "content_status": "filesystem_artifact_pointer",
        "read_priority": 75,
    }


def _important_read_priority(upper_name: str) -> int:
    if upper_name == "ROUTE_SUMMARY.JSON":
        return 0
    if "COMPLETION_AUDIT" in upper_name:
        return 0
    if upper_name == "VERIFICATION_RESULT.JSON" or upper_name.endswith("_VERIFICATION.JSON"):
        return 1
    if upper_name == "OUTPUT_MANIFEST.JSON" or "OUTPUT_MANIFEST" in upper_name:
        return 2
    if upper_name.endswith("_MANIFEST.JSON") or "MANIFEST" in upper_name:
        return 3
    if "DENOMINATOR_TO_DEPLOYMENT_EXECUTION_SUMMARY" in upper_name:
        return 4
    if "ULTIMATE_CANDIDATE_PACKAGE" in upper_name and "SUMMARY" in upper_name:
        return 5
    if "RECONSTRUCTED_PROXY" in upper_name and "SUMMARY" in upper_name:
        return 6
    if upper_name == "SOURCE_BOUND_TO_EXECUTED_PARITY_SUMMARY.JSON":
        return 7
    if "BROAD_LIVE_AS_IF_REPLAY" in upper_name and "PARTIAL_SUMMARY" in upper_name:
        return 55
    if "BROAD_LIVE_AS_IF_REPLAY" in upper_name and "SUMMARY" in upper_name:
        return 45
    priority = {
        "README": 0,
        "SUMMARY": 20,
        "MANIFEST": 3,
        "VERIFICATION": 1,
        "VERIFY": 18,
        "AUDIT": 10,
        "DOSSIER": 25,
        "REPORT": 30,
        "RESULT": 35,
        "PLAN": 40,
    }
    for token, value in priority.items():
        if token in upper_name:
            return value
    return 50


def _manifest_rows_for_overview(manifest: dict[str, Any]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for bucket in ("read_first", "compact_artifacts", "cold_raw_pointers"):
        for doc in manifest.get(bucket, []):
            if any(row["path"] == doc["path"] for row in rows):
                continue
            rows.append(doc)
    return rows
