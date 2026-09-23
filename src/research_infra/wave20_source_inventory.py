#!/usr/bin/env python3
"""Metadata-only source inventory for the frozen Wave 20 science DAG.

This tool never opens row ledgers, decodes outcomes, or creates a candidate
pool.  It authenticates only the manifest/receipt bytes named by the frozen
preregistration and exposes a deliberately small JSON metadata projection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "gtos.wave20.s0-source-inventory.v1"
DENOMINATOR_NODES = ("O1", "B1", "C0", "N1", "F1", "K1", "P1")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
GIT_OBJECT = re.compile(r"^([0-9a-f]{40}):(.+)$")
PLACEHOLDER = re.compile(r"^[A-Z][A-Z0-9_]+$")

DEFAULT_METADATA_KEYS = ("key_names", "schema", "declared_dates", "lineage")
FORBIDDEN_METADATA_TOKENS = (
    "economics",
    "expected_r",
    "final_r",
    "gross_r",
    "net_r",
    "outcome",
    "p_value",
    "pnl",
    "profit",
    "q_value",
    "r_multiple",
    "result",
    "trade_return",
)
DATE_KEYS = {
    "allowed_dates_and_roles",
    "capture_window",
    "capture_windows",
    "date_range",
    "date_span",
    "declaration_date",
    "declared_at",
    "first_scored_dates",
    "last_scored_dates",
    "reserved_blackout",
    "window",
    "windows",
}
LINEAGE_KEYS = {
    "commit",
    "implementation_head",
    "parent",
    "source_commit",
    "source_head",
    "source_parent",
    "supersedes",
    "supersedes_sha256",
}


class InventoryRefusal(ValueError):
    """A requested read crossed the metadata-only boundary."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_safe_metadata_value(value: Any, *, depth: int = 0) -> bool:
    if depth > 3:
        return False
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, (list, tuple)):
        return all(_is_safe_metadata_value(item, depth=depth + 1) for item in value)
    if isinstance(value, Mapping):
        return all(
            isinstance(key, str)
            and _is_safe_metadata_value(item, depth=depth + 1)
            for key, item in value.items()
        )
    return False


def _outcome_key(key: str) -> bool:
    normalized = str(key).strip().lower()
    return any(token in normalized for token in FORBIDDEN_METADATA_TOKENS)


def validate_metadata_keys(keys: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    normalized = tuple(dict.fromkeys(str(key).strip().lower() for key in keys if str(key).strip()))
    forbidden = tuple(key for key in normalized if _outcome_key(key))
    if forbidden:
        raise InventoryRefusal(
            "outcome_metadata_key_refused:" + ",".join(forbidden)
        )
    unknown = tuple(key for key in normalized if key not in DEFAULT_METADATA_KEYS)
    if unknown:
        raise InventoryRefusal("unsupported_metadata_key:" + ",".join(unknown))
    return normalized


def path_policy(path_text: str, *, role: str = "metadata_only") -> str | None:
    """Return the refusal reason without touching the requested path."""

    normalized = str(path_text).replace("\\", "/").lower()
    tokens = tuple(part for part in re.split(r"[/_.-]+", normalized) if part)
    if "march" in tokens or re.search(r"(?:^|[/_.-])2026[-_/]?03(?:[/_.-]|$)", normalized):
        return "march_path_refused_before_presence_or_byte_read"
    if "live_forward" in normalized or "live-forward" in normalized:
        return "live_forward_path_refused_before_presence_or_byte_read"
    is_february = "february" in tokens or bool(
        re.search(r"(?:^|[/_.-])2026[-_/]?02(?:[/_.-]|$)", normalized)
    )
    if is_february and role not in {"metadata_only", "attribution_only"}:
        return "february_economics_refused_before_presence_or_byte_read"
    return None


def _safe_json_metadata(data: bytes, requested: tuple[str, ...]) -> dict[str, Any]:
    try:
        payload = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"json_parse": "not_json_or_invalid_json"}
    if not isinstance(payload, dict):
        return {"json_parse": "valid_non_object_json"}

    metadata: dict[str, Any] = {"json_parse": "valid_object"}
    keys = sorted(str(key) for key in payload)
    if "key_names" in requested:
        metadata["top_level_key_names"] = keys
        metadata["outcome_key_names_present_values_not_read"] = [
            key for key in keys if _outcome_key(key)
        ]
    if "schema" in requested:
        schema = payload.get("schema")
        metadata["schema"] = schema if isinstance(schema, str) else None
    if "declared_dates" in requested:
        declared: dict[str, Any] = {}
        for key in sorted(DATE_KEYS):
            value = payload.get(key)
            if _is_safe_metadata_value(value):
                declared[key] = value
        capture = payload.get("capture_authority")
        if isinstance(capture, Mapping):
            capture_dates = {
                key: capture[key]
                for key in sorted(DATE_KEYS.intersection(capture))
                if _is_safe_metadata_value(capture[key])
            }
            if capture_dates:
                declared["capture_authority"] = capture_dates
        metadata["declared_dates"] = declared
    if "lineage" in requested:
        lineage = {
            key: value
            for key, value in sorted(payload.items())
            if (
                key in LINEAGE_KEYS
                or key.endswith("_head")
                or key.endswith("_parent")
            )
            and _is_safe_metadata_value(value)
        }
        metadata["lineage"] = lineage
    metadata["outcome_values_projected"] = False
    return metadata


def _read_git_blob(repo_root: Path, commit: str, path: str) -> tuple[bytes | None, str | None]:
    proc = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    if proc.returncode:
        return None, proc.stderr.decode("utf-8", errors="replace").strip()
    return proc.stdout, None


def _resolve_repo_path(repo_root: Path, path_text: str) -> Path:
    candidate = (repo_root / path_text).resolve()
    if not candidate.is_relative_to(repo_root.resolve()):
        raise InventoryRefusal("repo_path_escape_refused")
    return candidate


def _artifact_bytes(
    repo_root: Path,
    path_text: str,
) -> tuple[bytes | None, dict[str, Any], str | None]:
    git_match = GIT_OBJECT.fullmatch(path_text)
    if git_match:
        commit, repo_path = git_match.groups()
        data, error = _read_git_blob(repo_root, commit, repo_path)
        return data, {"kind": "exact_git_blob", "commit": commit, "path": repo_path}, error

    path = _resolve_repo_path(repo_root, path_text)
    if not path.is_file():
        return None, {"kind": "working_tree_file", "path": path_text}, "file_absent"
    try:
        return path.read_bytes(), {"kind": "working_tree_file", "path": path_text}, None
    except OSError as exc:
        return None, {"kind": "working_tree_file", "path": path_text}, str(exc)


def _find_nodes(plan: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    dag = plan.get("dag")
    nodes = dag.get("nodes") if isinstance(dag, Mapping) else None
    if not isinstance(nodes, list):
        raise InventoryRefusal("preregistration_dag_nodes_missing")
    by_id = {
        str(node.get("id")): node
        for node in nodes
        if isinstance(node, Mapping) and node.get("id")
    }
    missing = [node_id for node_id in DENOMINATOR_NODES if node_id not in by_id]
    if missing:
        raise InventoryRefusal("preregistration_denominator_node_missing:" + ",".join(missing))
    return by_id


def inventory_artifact(
    *,
    repo_root: Path,
    node_id: str,
    artifact_index: int,
    path_text: str,
    expected_sha256: str,
    requested_metadata: tuple[str, ...],
    role: str = "metadata_only",
    original_placeholder: str | None = None,
) -> dict[str, Any]:
    refusal = path_policy(path_text, role=role)
    base = {
        "node_id": node_id,
        "artifact_index": artifact_index,
        "declared_path": original_placeholder or path_text,
        "resolved_path": path_text if original_placeholder else None,
        "declared_sha256": expected_sha256,
        "role": role,
    }
    if refusal:
        return {
            **base,
            "classification": "forbidden",
            "reason": refusal,
            "path_touched": False,
            "presence_is_economic_evidence": False,
            "absence_is_rejection": False,
        }

    data, lineage, error = _artifact_bytes(repo_root, path_text)
    if data is None:
        return {
            **base,
            "classification": "absent",
            "reason": error or "file_absent",
            "lineage": lineage,
            "path_touched": True,
            "exact_capture_prerequisite": f"provide_and_hash_bind:{path_text}",
            "presence_is_economic_evidence": False,
            "absence_is_rejection": False,
        }

    actual = sha256_bytes(data)
    expected_is_concrete = bool(HEX64.fullmatch(expected_sha256))
    classification = (
        "present" if expected_is_concrete and actual == expected_sha256 else "conflicting"
    )
    reason = (
        "sha256_matches_declared_authority"
        if classification == "present"
        else "declared_sha256_missing_or_mismatch"
    )
    metadata = (
        _safe_json_metadata(data, requested_metadata)
        if path_text.split(":", 1)[-1].lower().endswith(".json")
        else {"json_parse": "not_requested_non_json", "outcome_values_projected": False}
    )
    return {
        **base,
        "classification": classification,
        "reason": reason,
        "lineage": lineage,
        "path_touched": True,
        "bytes": len(data),
        "observed_sha256": actual,
        "metadata": metadata,
        "presence_is_economic_evidence": False,
        "absence_is_rejection": False,
    }


def build_inventory(
    *,
    plan_path: Path,
    repo_root: Path,
    resolutions: Mapping[str, tuple[str, str | None]] | None = None,
    authority_supersessions: Mapping[str, Mapping[str, str]] | None = None,
    g0_binding: Mapping[str, str] | None = None,
    metadata_keys: tuple[str, ...] = DEFAULT_METADATA_KEYS,
    p1_adapter_exact_parent: str,
) -> dict[str, Any]:
    if not HEX40.fullmatch(p1_adapter_exact_parent):
        raise InventoryRefusal("p1_adapter_exact_parent_must_be_full_commit")
    requested = validate_metadata_keys(metadata_keys)
    plan_bytes = plan_path.read_bytes()
    plan = json.loads(plan_bytes)
    nodes = _find_nodes(plan)
    resolutions = dict(resolutions or {})
    authority_supersessions = dict(authority_supersessions or {})
    entries: list[dict[str, Any]] = []

    for node_id in DENOMINATOR_NODES:
        artifacts = nodes[node_id].get("prerequisite_artifacts")
        if not isinstance(artifacts, list):
            raise InventoryRefusal(f"prerequisite_artifacts_missing:{node_id}")
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, Mapping):
                raise InventoryRefusal(f"prerequisite_artifact_invalid:{node_id}:{index}")
            declared_path = str(artifact.get("path") or "")
            declared_sha = str(artifact.get("sha256") or "")
            if not declared_path:
                raise InventoryRefusal(f"prerequisite_path_missing:{node_id}:{index}")
            original_placeholder = None
            if PLACEHOLDER.fullmatch(declared_path):
                resolved = resolutions.get(declared_path)
                if resolved is None:
                    entries.append(
                        {
                            "node_id": node_id,
                            "artifact_index": index,
                            "declared_path": declared_path,
                            "resolved_path": None,
                            "declared_sha256": declared_sha,
                            "role": "metadata_only",
                            "classification": "absent",
                            "reason": "unresolved_preregistration_placeholder",
                            "path_touched": False,
                            "exact_capture_prerequisite": f"resolve_placeholder:{declared_path}",
                            "presence_is_economic_evidence": False,
                            "absence_is_rejection": False,
                        }
                    )
                    continue
                original_placeholder = declared_path
                declared_path, resolved_sha = resolved
                if resolved_sha:
                    if HEX64.fullmatch(declared_sha) and resolved_sha != declared_sha:
                        entries.append(
                            {
                                "node_id": node_id,
                                "artifact_index": index,
                                "declared_path": original_placeholder,
                                "resolved_path": declared_path,
                                "declared_sha256": declared_sha,
                                "resolution_sha256": resolved_sha,
                                "classification": "conflicting",
                                "reason": (
                                    "placeholder_resolution_sha_conflicts_with_preregistration"
                                ),
                                "path_touched": False,
                                "presence_is_economic_evidence": False,
                                "absence_is_rejection": False,
                            }
                        )
                        continue
                    declared_sha = resolved_sha
            row = inventory_artifact(
                repo_root=repo_root,
                node_id=node_id,
                artifact_index=index,
                path_text=declared_path,
                expected_sha256=declared_sha,
                requested_metadata=requested,
                original_placeholder=original_placeholder,
            )
            supersession = authority_supersessions.get(declared_path)
            if row["classification"] == "conflicting" and supersession:
                frozen_sha = str(supersession.get("frozen_preregistration_sha256") or "")
                integrated_sha = str(supersession.get("integrated_source_sha256") or "")
                authority = str(supersession.get("authority") or "")
                if (
                    frozen_sha == declared_sha
                    and integrated_sha == row.get("observed_sha256")
                    and authority
                ):
                    row["classification"] = "present"
                    row["reason"] = "sha256_superseded_by_exact_g0_integrated_source"
                    row["authority_resolution"] = dict(supersession)
            entries.append(row)

    counts = {
        classification: sum(row["classification"] == classification for row in entries)
        for classification in ("present", "absent", "conflicting", "forbidden")
    }
    expected_count = sum(
        len(nodes[node_id].get("prerequisite_artifacts") or [])
        for node_id in DENOMINATOR_NODES
    )
    if len(entries) != expected_count:
        raise InventoryRefusal("silent_denominator_omission_detected")
    if counts["conflicting"] or counts["forbidden"]:
        status = "SOURCE_AUTHORITY_CONFLICT_STOP"
    elif counts["absent"]:
        status = "SOURCE_ABSENT_WITH_EXACT_CAPTURE_PREREQUISITE"
    else:
        status = "SOURCE_INVENTORY_BOUND"

    return {
        "schema": SCHEMA,
        "session": "HK",
        "node": "S0",
        "status": status,
        "execution_authority": False,
        "activation_authority": False,
        "result_bearing_science_executed": False,
        "p1_adapter_exact_parent": p1_adapter_exact_parent,
        "preregistration": {
            "path": str(plan_path.resolve().relative_to(repo_root.resolve())),
            "sha256": sha256_bytes(plan_bytes),
        },
        "g0_binding": dict(g0_binding or {}),
        "denominator": {
            "nodes": list(DENOMINATOR_NODES),
            "declared_entries": expected_count,
            "reported_entries": len(entries),
            "silent_omissions": 0,
        },
        "counts": counts,
        "requested_metadata": list(requested),
        "entries": entries,
        "boundaries": {
            "metadata_only": True,
            "row_outcomes_opened": 0,
            "economic_aggregations": 0,
            "candidate_pool_created": False,
            "march_paths_touched": 0,
            "live_forward_paths_touched": 0,
            "february_economics_read": False,
            "outcome_values_projected": False,
            "presence_is_economic_evidence": False,
            "absence_is_rejection": False,
        },
    }


def load_g0_binding(
    *,
    repo_root: Path,
    path: Path,
    p1_adapter_exact_parent: str,
) -> tuple[dict[str, Mapping[str, str]], dict[str, str]]:
    target = _resolve_repo_path(repo_root, str(path))
    data = target.read_bytes()
    payload = json.loads(data)
    if not isinstance(payload, Mapping):
        raise InventoryRefusal("g0_binding_json_object_required")
    required = {
        "schema": "gtos.wave20.g0-hia-binding.v1",
        "status": "G0_PASS_HIA_EXACT_SOURCE_BOUND",
        "execution_authority": False,
        "activation_authority": False,
        "result_bearing_science_executed": False,
        "p1_adapter_exact_parent": p1_adapter_exact_parent,
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            raise InventoryRefusal(f"g0_binding_{key}_mismatch")
    rows = payload.get("integrated_hash_supersessions")
    if not isinstance(rows, list):
        raise InventoryRefusal("g0_integrated_hash_supersessions_missing")
    by_path: dict[str, Mapping[str, str]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise InventoryRefusal(f"g0_hash_supersession_invalid:{index}")
        declared_path = str(row.get("path") or "")
        if not declared_path or declared_path in by_path:
            raise InventoryRefusal(f"g0_hash_supersession_path_invalid:{index}")
        if not HEX64.fullmatch(str(row.get("frozen_preregistration_sha256") or "")):
            raise InventoryRefusal(f"g0_hash_supersession_frozen_sha_invalid:{index}")
        if not HEX64.fullmatch(str(row.get("integrated_source_sha256") or "")):
            raise InventoryRefusal(f"g0_hash_supersession_integrated_sha_invalid:{index}")
        if not str(row.get("authority") or ""):
            raise InventoryRefusal(f"g0_hash_supersession_authority_missing:{index}")
        by_path[declared_path] = row
    return by_path, {
        "path": str(target.relative_to(repo_root.resolve())),
        "sha256": sha256_bytes(data),
        "status": str(payload.get("status")),
    }


def parse_resolution(text: str) -> tuple[str, tuple[str, str | None]]:
    if "=" not in text:
        raise InventoryRefusal("resolution_must_be_TOKEN=PATH::SHA256")
    token, value = text.split("=", 1)
    token = token.strip()
    if not PLACEHOLDER.fullmatch(token):
        raise InventoryRefusal("resolution_token_invalid")
    if "::" in value:
        path, digest = value.rsplit("::", 1)
        if not HEX64.fullmatch(digest):
            raise InventoryRefusal("resolution_sha256_invalid")
    else:
        path, digest = value, None
    if not path:
        raise InventoryRefusal("resolution_path_missing")
    return token, (path, digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-only", action="store_true", required=True)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--p1-parent", required=True)
    parser.add_argument("--g0-binding", type=Path)
    parser.add_argument("--metadata-key", action="append", default=[])
    parser.add_argument("--resolve", action="append", default=[])
    ns = parser.parse_args(argv)
    repo_root = Path.cwd().resolve()
    try:
        resolutions = dict(parse_resolution(item) for item in ns.resolve)
        requested = tuple(ns.metadata_key) or DEFAULT_METADATA_KEYS
        supersessions: dict[str, Mapping[str, str]] = {}
        g0_binding: dict[str, str] = {}
        if ns.g0_binding:
            supersessions, g0_binding = load_g0_binding(
                repo_root=repo_root,
                path=ns.g0_binding,
                p1_adapter_exact_parent=ns.p1_parent,
            )
        receipt = build_inventory(
            plan_path=ns.plan.resolve(),
            repo_root=repo_root,
            resolutions=resolutions,
            authority_supersessions=supersessions,
            g0_binding=g0_binding,
            metadata_keys=requested,
            p1_adapter_exact_parent=ns.p1_parent,
        )
    except (InventoryRefusal, json.JSONDecodeError, OSError) as exc:
        parser.error(str(exc))
    ns.out.parent.mkdir(parents=True, exist_ok=True)
    ns.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{receipt['status']}: {ns.out}")
    return 0 if receipt["status"] == "SOURCE_INVENTORY_BOUND" else 3


if __name__ == "__main__":
    raise SystemExit(main())
