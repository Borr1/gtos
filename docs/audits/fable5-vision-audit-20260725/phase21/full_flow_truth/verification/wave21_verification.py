#!/usr/bin/env python3
"""Offline verification controls for the Wave 21 sparse worktree.

This file never imports or executes trading entrypoints.  It reads Git objects,
the local worktree and pytest capture receipts to make an A/B comparison's
environment and evidence boundary explicit.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts/pytest_failset.py").is_file():
            return parent
    raise RuntimeError("cannot locate repository root")


REPO = _repo_root()
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
DEFAULT_BASE = "9392e9bbddb9eddfb5dc51ef36bc2d7ff7e8f285"
LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1\n"
OVERSIZED_BYTES = 5 * 1024 * 1024
DENOMINATOR_ROUTE = (
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
)

STATIC_REQUIRED_FIXTURES = {
    (
        "research/operations/"
        "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
        "B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json"
    ): "armed-set and decision-contract verification",
    f"{DENOMINATOR_ROUTE}/ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl": (
        "selector/package permission tests; exact LFS object required"
    ),
    (
        "research/operations/"
        "final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19/"
        "FINAL_PACKAGE_SLEEVE_CANDIDATE_LEDGER.jsonl"
    ): "selector/package unit-test source ledger",
    (
        "research/operations/"
        "final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19/"
        "FINAL_PACKAGE_SLEEVE_MEMBER_LEDGER.jsonl"
    ): "selector/package unit-test member ledger",
    (
        "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
        "INTEG_W3_streams_cache.pkl"
    ): "W7 recost tests",
    (
        "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
        "INTEG_W5_new_streams_cache.pkl"
    ): "W7 recost tests",
    (
        "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
        "D4_COMBINED_TRADE_LEDGER.jsonl"
    ): "W7 recost stop-distance witness",
    (
        "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
        "ULTIMATE_REAL_COST_MAP.json"
    ): "W7 recost legacy-charge witness",
    (
        "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
        "INTEG_W7_FINAL_RESULT.json"
    ): "W7 recost pipeline-parity witness",
}

IMPORT_ENTRYPOINTS = {
    "full_flow_live": ["run_book.py"],
    "candidate_generation": [
        "src/components/broader_origin_generators.py",
        "src/components/ultimate_book/book_owner.py",
    ],
    "selector": ["src/components/selector_v4.py"],
    "scheduler_and_permission": [
        "src/research/moonshot_scheduler_v4_best_trade_allocator.py",
        "src/components/permissions.py",
    ],
    "quote_and_execution": [
        "src/research_infra/walkforward/quote_side.py",
        "src/components/execution.py",
    ],
    "cost_truth": [
        "src/components/broker_net_cost_engine.py",
        "src/costs/model.py",
    ],
    "w7_recost": ["scripts/recost_w7_validation.py"],
}

FOCUSED_SUITES = {
    "candidate_generation": [
        "tests/test_candidate_path_contract.py",
        "tests/test_universal_candidate_origin_registry.py",
        "tests/test_broad_origin_emission_repairs.py",
    ],
    "selector": ["tests/test_selector_v4.py", "tests/test_permissions.py"],
    "scheduler_and_risk": [
        "tests/test_moonshot_scheduler_v4_best_trade_allocator.py",
        "tests/test_timewarp_scheduler_materialization.py",
    ],
    "quote_execution_lifecycle": [
        "tests/research_infra/test_quote_side.py",
        "tests/test_execution.py",
        "tests/test_lifecycle.py",
        "tests/test_exit_policy_v4.py",
    ],
    "cost_truth": [
        "tests/test_broker_net_cost_engine.py",
        "tests/test_costs_layer.py",
    ],
    "full_flow_live_offline": [
        "tests/test_run_book_importable.py",
        "tests/test_run_book_account_identity.py",
        "tests/ultimate_book/test_book_owner.py",
        "tests/safety/test_armed_set_single_source.py",
    ],
    "w7_and_divergence": ["tests/test_w7_recost.py", "tests/test_divergence_matrix.py"],
    "verification_tooling": [
        "tests/scripts/test_pytest_failset_parsing.py",
        "tests/phase21/test_wave21_verification.py",
    ],
}

SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b"),
    "openai_key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "slack_token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "stripe_live_key": re.compile(r"\bsk_live_[A-Za-z0-9]{16,}\b"),
    "google_api_key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
}


def _run(
    argv: list[str], *, check: bool = True, text: bool = True, cwd: Path = REPO
) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=text, check=check)


def _git(*args: str, check: bool = True, text: bool = True) -> subprocess.CompletedProcess:
    return _run(["git", *args], check=check, text=text)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _canonical_hash(value: Any) -> str:
    return _sha256(_canonical_bytes(value))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _tree_rows(ref: str) -> dict[str, dict[str, Any]]:
    proc = _git("ls-tree", "-r", "-l", ref)
    rows: dict[str, dict[str, Any]] = {}
    for line in proc.stdout.splitlines():
        try:
            meta, path = line.split("\t", 1)
            mode, kind, oid, size_text = meta.split()
        except ValueError:
            continue
        if kind != "blob" or size_text == "-":
            continue
        rows[path] = {"mode": mode, "oid": oid, "size": int(size_text)}
    return rows


def _oversized_inventory(head: str, base: str, threshold: int) -> dict[str, Any]:
    current = _tree_rows(head)
    prior = _tree_rows(base)
    big = [
        {"path": path, **row}
        for path, row in current.items()
        if row["size"] > threshold
    ]
    big.sort(key=lambda row: (-row["size"], row["path"]))
    prior_keys = {(path, row["oid"]) for path, row in prior.items() if row["size"] > threshold}
    new = [row for row in big if (row["path"], row["oid"]) not in prior_keys]
    families = Counter(row["path"].split("/", 3)[0] for row in big)
    return {
        "threshold_bytes": threshold,
        "current_count": len(big),
        "current_bytes": sum(row["size"] for row in big),
        "current_inventory_sha256": _canonical_hash(big),
        "new_since_base_count": len(new),
        "new_since_base": new,
        "top_50": big[:50],
        "top_level_families": dict(sorted(families.items())),
        "gate": "PASS" if not new else "FAIL_NEW_OVERSIZED_NORMAL_GIT_BLOB",
    }


def _parse_lfs_pointer(data: bytes) -> tuple[str, int] | None:
    if not data.startswith(LFS_POINTER_PREFIX):
        return None
    oid = re.search(rb"^oid sha256:([0-9a-f]{64})$", data, re.M)
    size = re.search(rb"^size (\d+)$", data, re.M)
    if not oid or not size:
        return None
    return oid.group(1).decode(), int(size.group(1))


def _lfs_inventory() -> dict[str, Any]:
    proc = _run(["git", "lfs", "ls-files", "--long"], check=False)
    if proc.returncode:
        return {
            "available": False,
            "error": (proc.stderr or "git lfs ls-files failed").strip(),
            "comparison_sha256": _canonical_hash({"available": False}),
        }
    rows = []
    counts = Counter()
    malformed = []
    for line in proc.stdout.splitlines():
        match = re.match(r"^([0-9a-f]{64}) ([*-]) (.+)$", line)
        if not match:
            malformed.append(line[:200])
            continue
        oid, marker, path = match.groups()
        local = REPO / path
        if not local.exists():
            state = "sparse_absent"
            size = None
        else:
            size = local.stat().st_size
            prefix = local.read_bytes() if size <= 1024 else local.open("rb").read(256)
            parsed = _parse_lfs_pointer(prefix)
            state = "pointer" if parsed else "hydrated"
        counts[state] += 1
        rows.append({"path": path, "oid_sha256": oid, "marker": marker,
                     "worktree_state": state, "worktree_size": size})
    rows.sort(key=lambda row: row["path"])
    compact = [{k: row[k] for k in ("path", "oid_sha256", "worktree_state")} for row in rows]
    return {
        "available": True,
        "tracked_count": len(rows),
        "counts": dict(sorted(counts.items())),
        "malformed_lines": malformed,
        "inventory_sha256": _canonical_hash(compact),
        "comparison_sha256": _canonical_hash(compact),
    }


def _head_blob(path: str) -> bytes | None:
    proc = _git("cat-file", "blob", f"HEAD:{path}", check=False, text=False)
    return proc.stdout if proc.returncode == 0 else None


def _required_fixture_paths(tree: dict[str, dict[str, Any]]) -> dict[str, str]:
    paths = dict(STATIC_REQUIRED_FIXTURES)
    for path in tree:
        if path.startswith(DENOMINATOR_ROUTE + "/") and path.endswith(".py"):
            paths[path] = "denominator-route imports and unit tests"
    return dict(sorted(paths.items()))


def _fixture_inventory(tree: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for path, reason in _required_fixture_paths(tree).items():
        blob = _head_blob(path)
        if blob is None:
            rows.append({"path": path, "reason": reason, "committed": False,
                         "state": "not_committed"})
            continue
        pointer = _parse_lfs_pointer(blob)
        local = REPO / path
        row: dict[str, Any] = {
            "path": path,
            "reason": reason,
            "committed": True,
            "git_oid": tree[path]["oid"],
            "git_blob_size": tree[path]["size"],
        }
        if pointer:
            expected_hash, expected_size = pointer
            row.update(kind="lfs", expected_sha256=expected_hash,
                       expected_hydrated_size=expected_size)
        else:
            expected_hash = _sha256(blob)
            row.update(kind="normal_git", expected_sha256=expected_hash,
                       expected_hydrated_size=len(blob))
        if not local.exists():
            row["state"] = "sparse_absent"
        else:
            size = local.stat().st_size
            if size <= 1024:
                local_bytes = local.read_bytes()
                local_pointer = _parse_lfs_pointer(local_bytes)
            else:
                local_bytes = None
                local_pointer = None
            if local_pointer:
                row["state"] = "lfs_pointer"
                row["working_sha256"] = local_pointer[0]
                row["matches_expected"] = local_pointer[0] == expected_hash
            else:
                working_hash = _sha256(local.read_bytes())
                row["state"] = "materialized"
                row["working_sha256"] = working_hash
                row["matches_expected"] = working_hash == expected_hash
            row["working_size"] = size
        rows.append(row)
    counts = Counter(row["state"] for row in rows)
    comparison = [
        {k: row.get(k) for k in
         ("path", "kind", "expected_sha256", "state", "working_sha256", "matches_expected")}
        for row in rows
    ]
    return {
        "count": len(rows),
        "counts": dict(sorted(counts.items())),
        "rows": rows,
        "comparison_sha256": _canonical_hash(comparison),
        "reviewed_fixture_tier_ready": all(
            row.get("state") == "materialized" and row.get("matches_expected")
            for row in rows
        ),
    }


def _sparse_inventory() -> dict[str, Any]:
    enabled = _git("config", "--bool", "core.sparseCheckout", check=False).stdout.strip() == "true"
    cone = _git("config", "--bool", "core.sparseCheckoutCone", check=False).stdout.strip() == "true"
    listing = _git("sparse-checkout", "list", check=False)
    # Non-cone sparse patterns follow gitignore ordering rules, so reordering
    # identical lines can change the checkout.  Preserve the exact sequence.
    patterns = [line for line in listing.stdout.splitlines() if line]
    tagged = _git("ls-files", "-v", "-z").stdout.split("\0")
    skipped = sorted(entry[2:] for entry in tagged if entry.startswith("S "))
    materialized = sorted(entry[2:] for entry in tagged if entry.startswith("H "))
    comparison = {
        "enabled": enabled,
        "cone": cone,
        "patterns": patterns,
    }
    diagnostic_inventory = {
        "skip_worktree_paths_sha256": _canonical_hash(skipped),
        "materialized_paths_sha256": _canonical_hash(materialized),
    }
    return {
        **comparison,
        **diagnostic_inventory,
        "pattern_count": len(patterns),
        "skip_worktree_count": len(skipped),
        "materialized_count": len(materialized),
        "comparison_sha256": _canonical_hash(comparison),
        # These paths are tree-relative diagnostics.  An expected added file
        # changes them even when both worktrees use exactly the same sparse
        # configuration, so they must not define A/B context identity.
        "diagnostic_inventory_sha256": _canonical_hash(diagnostic_inventory),
    }


def _parse_pytest_selection(pytest_args: Any) -> dict[str, Any]:
    """Pure closed parser shared by inspection and the untrusted receipt guard."""

    entries: dict[str, str] = {}
    bound = pytest_args is not None
    if not bound:
        return {
            "bound": False,
            "entries": [],
            "selection_roots": [],
            "all_supported": False,
        }
    if not isinstance(pytest_args, list):
        entries[f"pytest_args:invalid_{type(pytest_args).__name__}"] = (
            "unsupported_argument"
        )
    else:
        for index, arg in enumerate(pytest_args):
            if not isinstance(arg, str):
                entries[f"argument[{index}]:non_string"] = "unsupported_argument"
                continue
            if arg.startswith("-") or arg.startswith("@"):
                # A/B receipts intentionally support a closed grammar: literal
                # repository paths and nodeids only.  Pytest options can redirect
                # collection (--pyargs, -c, --rootdir) or load mutable indirect
                # selectors (@argfile).  Guessing which options are harmless is a
                # fail-open parser, so every option form is refused.
                entries[f"argument[{index}]:{arg}"] = "unsupported_argument"
                continue
            raw_path = arg.split("::", 1)[0].replace("\\", "/")
            candidate = Path(raw_path)
            if candidate.is_absolute():
                try:
                    raw_path = candidate.relative_to(REPO).as_posix()
                except ValueError:
                    entries[candidate.as_posix()] = "outside_repo"
                    continue
            while raw_path.startswith("./"):
                raw_path = raw_path[2:]
            raw_path = raw_path.rstrip("/") or "."
            if raw_path == ".." or raw_path.startswith("../"):
                entries[raw_path] = "outside_repo"
            else:
                entries[raw_path] = "literal"
        if not entries:
            entries["tests"] = "literal"
    parsed_entries = [
        {"path": path, "parse_kind": kind}
        for path, kind in sorted(entries.items())
    ]
    return {
        "bound": True,
        "entries": parsed_entries,
        "selection_roots": [entry["path"] for entry in parsed_entries],
        "all_supported": bool(parsed_entries) and all(
            entry["parse_kind"] == "literal" for entry in parsed_entries
        ),
    }


def _selected_test_availability(
    pytest_args: Any,
    tree: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Bind the materialization of the pytest roots selected by a capture.

    Test *content* may intentionally differ across an A/B.  The guard instead
    proves that each side can resolve the same selected file or directory.  It
    does not hash every tracked test path: doing so would make an unrelated new
    test or audit document invalidate an otherwise equal execution context.
    """

    parsed = _parse_pytest_selection(pytest_args)

    rows: list[dict[str, Any]] = []
    tree_paths = set(tree)
    for entry in parsed["entries"]:
        path = entry["path"]
        parse_kind = entry["parse_kind"]
        if parse_kind != "literal":
            rows.append({
                "path": path,
                "expected_kind": parse_kind,
                "available": False,
            })
            continue
        prefix = "" if path == "." else path.rstrip("/") + "/"
        committed_file = path in tree_paths
        committed_directory = not committed_file and any(
            item.startswith(prefix) for item in tree_paths
        )
        local = REPO / path
        if committed_file:
            expected_kind = "file"
            available = local.is_file() and not local.is_symlink()
        elif committed_directory:
            expected_kind = "directory"
            descendants = (item for item in tree_paths if item.startswith(prefix))
            available = (
                local.is_dir()
                and not local.is_symlink()
                and all((REPO / item).is_file() for item in descendants)
            )
        else:
            expected_kind = "missing"
            available = False
        rows.append({
            "path": path,
            "expected_kind": expected_kind,
            "available": available,
        })

    payload = {
        "bound": parsed["bound"],
        "selection_roots": parsed["selection_roots"],
        "rows": rows,
    }
    return {
        **payload,
        "pytest_args_sha256": (
            _canonical_hash(pytest_args) if pytest_args is not None else None
        ),
        "all_available": bool(
            parsed["all_supported"]
            and rows
            and all(row["available"] for row in rows)
        ),
        "inventory_sha256": _canonical_hash(payload),
    }


def _dependency_inventory() -> dict[str, Any]:
    distributions: dict[str, str] = {}
    for dist in importlib.metadata.distributions():
        name = (dist.metadata.get("Name") or "").lower().replace("_", "-")
        if name:
            distributions[name] = dist.version
    all_rows = sorted(distributions.items())
    selected_names = (
        "pytest", "numpy", "pandas", "scipy", "scikit-learn", "pyarrow",
        "pyyaml", "pytest-asyncio", "anyio", "orjson",
    )
    imports = {}
    for module in (
        "numpy", "pandas", "scipy", "sklearn", "pyarrow", "yaml",
        "pytest_asyncio", "MetaTrader5", "torch", "sentence_transformers",
    ):
        try:
            spec = importlib.util.find_spec(module)
            imports[module] = bool(spec)
        except (ImportError, ValueError):
            imports[module] = False
    comparison = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "machine": platform.machine(),
        "distributions_sha256": _canonical_hash(all_rows),
        "imports": imports,
    }
    return {
        **comparison,
        "executable": sys.executable,
        "distribution_count": len(all_rows),
        "selected_versions": {name: distributions.get(name) for name in selected_names},
        "comparison_sha256": _canonical_hash(comparison),
    }


def _secret_hits(ref: str) -> list[dict[str, Any]]:
    hits = []
    for kind, regex in SECRET_PATTERNS.items():
        proc = _git("grep", "-I", "-n", "-P", "-e", regex.pattern, ref, "--", check=False)
        if proc.returncode not in (0, 1):
            raise RuntimeError(f"git grep failed for {kind}: {proc.stderr.strip()}")
        for line in proc.stdout.splitlines():
            match = re.match(r"^[^:]+:(.*?):(\d+):(.*)$", line)
            if not match:
                continue
            path, line_no, content = match.groups()
            secret = regex.search(content)
            if not secret:
                continue
            # Never persist or print the matched credential bytes.
            hits.append({
                "kind": kind,
                "path": path,
                "line": int(line_no),
                "match_sha256": _sha256(secret.group(0).encode()),
            })
    return sorted(hits, key=lambda row: (row["path"], row["line"], row["kind"]))


def _secret_inventory(head: str, base: str) -> dict[str, Any]:
    current = _secret_hits(head)
    prior = _secret_hits(base)
    old = {(row["kind"], row["match_sha256"]) for row in prior}
    new = [row for row in current if (row["kind"], row["match_sha256"]) not in old]
    return {
        "scanner": "high-confidence tracked Git text; matched values are never emitted",
        "current_hit_count": len(current),
        "current_hits_redacted": current,
        "new_since_base_count": len(new),
        "new_since_base_redacted": new,
        "inventory_sha256": _canonical_hash(current),
        "gate": "PASS" if not new else "FAIL_NEW_HIGH_CONFIDENCE_SECRET",
    }


def _module_name(path: Path) -> str | None:
    try:
        rel = path.relative_to(REPO)
    except ValueError:
        return None
    if rel.suffix != ".py":
        return None
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _module_path(name: str) -> Path | None:
    rel = Path(*name.split("."))
    for candidate in (REPO / rel.with_suffix(".py"), REPO / rel / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def _imports(path: Path) -> tuple[set[str], set[str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return set(), set()
    current = _module_name(path) or ""
    package = current if path.name == "__init__.py" else current.rpartition(".")[0]
    resolved: set[str] = set()
    unresolved: set[str] = set()
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = package.split(".") if package else []
                keep = max(0, len(parts) - (node.level - 1))
                base = ".".join(parts[:keep] + ([base] if base else []))
            if base:
                names.append(base)
                names.extend(f"{base}.{alias.name}" for alias in node.names if alias.name != "*")
        for name in names:
            candidate = _module_path(name)
            if candidate:
                resolved.add(name)
            elif name.split(".")[0] in {"src", "scripts", "run_book", "run_agent"}:
                unresolved.add(name)
    return resolved, unresolved


def _closure(entrypoint: str) -> dict[str, Any]:
    start = REPO / entrypoint
    if not start.is_file():
        return {"entrypoint": entrypoint, "status": "MISSING", "paths": [],
                "unresolved_first_party": []}
    seen: set[Path] = set()
    unresolved: set[str] = set()
    stack = [start]
    while stack:
        path = stack.pop()
        if path in seen:
            continue
        seen.add(path)
        imports, missing = _imports(path)
        unresolved |= missing
        for name in imports:
            candidate = _module_path(name)
            if candidate and candidate not in seen:
                stack.append(candidate)
    paths = sorted(str(path.relative_to(REPO)) for path in seen)
    content = []
    for path in paths:
        content.append({"path": path, "sha256": _sha256((REPO / path).read_bytes())})
    return {
        "entrypoint": entrypoint,
        "status": "OK",
        "path_count": len(paths),
        "paths": paths,
        "unresolved_first_party": sorted(unresolved),
        "closure_sha256": _canonical_hash(content),
    }


def _import_closures() -> dict[str, Any]:
    lanes = {lane: [_closure(path) for path in paths]
             for lane, paths in IMPORT_ENTRYPOINTS.items()}
    missing = [row["entrypoint"] for rows in lanes.values() for row in rows
               if row["status"] != "OK"]
    return {
        "method": "static AST first-party closure; no trading module executed",
        "lanes": lanes,
        "missing_entrypoints": missing,
        "gate": "PASS" if not missing else "FAIL_MISSING_ENTRYPOINT",
        "inventory_sha256": _canonical_hash(lanes),
    }


def _baseline_summary(path: Path | None, wall: float | None, max_rss: int | None) -> dict[str, Any] | None:
    if path is None:
        return None
    doc = json.loads(path.read_text(encoding="utf-8"))
    failed = doc.get("failed") or []
    errored = doc.get("errored") or []
    bad = sorted(set(failed) | set(errored))
    files = Counter(node.split("::", 1)[0] for node in bad)
    return {
        "capture_path": str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path),
        "commit": doc.get("commit"),
        "dirty_at_start": doc.get("dirty"),
        "pytest_args": doc.get("pytest_args"),
        "pytest_returncode": doc.get("pytest_returncode"),
        "totals": doc.get("totals"),
        "parse_complete": doc.get("parse_complete"),
        "usable_as_baseline": doc.get("usable_as_baseline"),
        "bad_count": len(bad),
        "bad_nodeids_sha256": _canonical_hash(bad),
        "bad_files": len(files),
        "bad_by_file": dict(files.most_common()),
        "wall_seconds": wall,
        "maximum_resident_set_size_bytes": max_rss,
    }


def _focused_suites() -> dict[str, Any]:
    out = {}
    for lane, paths in FOCUSED_SUITES.items():
        missing = [path for path in paths if not (REPO / path).is_file()]
        out[lane] = {
            "pytest_args": paths,
            "missing": missing,
            "command": "env NO_COLOR=1 PY_COLORS=0 PYTHONDONTWRITEBYTECODE=1 "
                       "python3 scripts/pytest_failset.py capture -o <capture.json> -- "
                       + " ".join(paths),
        }
    return out


def build_inspection(
    *, base: str, baseline: Path | None, wall_seconds: float | None,
    max_rss_bytes: int | None,
) -> dict[str, Any]:
    head = _git("rev-parse", "HEAD").stdout.strip()
    tree = _tree_rows("HEAD")
    dependency = _dependency_inventory()
    sparse = _sparse_inventory()
    lfs = _lfs_inventory()
    fixtures = _fixture_inventory(tree)
    baseline_summary = _baseline_summary(baseline, wall_seconds, max_rss_bytes)
    selected_tests = _selected_test_availability(
        baseline_summary.get("pytest_args") if baseline_summary else None,
        tree,
    )
    comparison_contract = {
        "dependency": dependency["comparison_sha256"],
        "sparse": sparse["comparison_sha256"],
        "lfs": lfs["comparison_sha256"],
        "fixtures": fixtures["comparison_sha256"],
        "selected_tests": selected_tests,
        "environment_controls": {
            key: os.environ.get(key) for key in
            ("PYTHONHASHSEED", "PYTHONDONTWRITEBYTECODE", "NO_COLOR", "PY_COLORS")
        },
    }
    report: dict[str, Any] = {
        "schema": "gtos.wave21.sparse_verification.v2",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authority": {
            "live_or_broker_action": False,
            "activation_authority": False,
            "result_bearing_replay_run": False,
            "host_contacted": False,
        },
        "git": {
            "head": head,
            "branch": _git("branch", "--show-current").stdout.strip(),
            "base": _git("rev-parse", base).stdout.strip(),
            # The caller supplies the reviewed comparator.  Do not rediscover a
            # merge base here: on this generated-evidence history that graph walk
            # consumed ~2 GiB and a full core, while adding no verification value.
            "base_role": "caller_supplied_reviewed_comparator",
            "dirty": bool(_git("status", "--porcelain").stdout),
        },
        "environment": dependency,
        "sparse": sparse,
        "lfs": lfs,
        "required_fixtures": fixtures,
        "selected_test_availability": selected_tests,
        "oversized_git_blobs": _oversized_inventory("HEAD", base, OVERSIZED_BYTES),
        "secret_scan": _secret_inventory("HEAD", base),
        "import_closure": _import_closures(),
        "focused_suites": _focused_suites(),
        "baseline": baseline_summary,
        "comparison_contract": comparison_contract,
        "comparison_contract_sha256": _canonical_hash(comparison_contract),
    }
    stable = {key: value for key, value in report.items() if key != "generated_at_utc"}
    report["deterministic_payload_sha256"] = _canonical_hash(stable)
    gates = (
        report["oversized_git_blobs"]["gate"],
        report["secret_scan"]["gate"],
        report["import_closure"]["gate"],
    )
    report["integrity_gate"] = "PASS" if all(gate == "PASS" for gate in gates) else "FAIL"
    return report


def _load_capture(path: Path) -> dict[str, Any]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("usable_as_baseline") is not True or doc.get("parse_complete") is not True:
        raise ValueError(f"unusable pytest capture: {path}")
    if not doc.get("totals"):
        raise ValueError(f"pytest capture has no totals: {path}")
    return doc


def build_ab_guard(
    before_capture: Path, after_capture: Path, before_inspection: Path, after_inspection: Path
) -> tuple[dict[str, Any], int]:
    before = _load_capture(before_capture)
    after = _load_capture(after_capture)
    bctx = json.loads(before_inspection.read_text(encoding="utf-8"))
    actx = json.loads(after_inspection.read_text(encoding="utf-8"))
    required_context = {
        "dependency", "sparse", "lfs", "fixtures", "selected_tests",
        "environment_controls",
    }
    mismatches = []
    if before.get("pytest_args") != after.get("pytest_args"):
        mismatches.append("pytest_args")
    before_contract = bctx.get("comparison_contract", {})
    after_contract = actx.get("comparison_contract", {})
    if not isinstance(before_contract, dict) or not required_context.issubset(before_contract):
        mismatches.append("before_context_contract_incomplete")
        before_contract = before_contract if isinstance(before_contract, dict) else {}
    elif set(before_contract) != required_context:
        mismatches.append("before_context_contract_keys_invalid")
    if not isinstance(after_contract, dict) or not required_context.issubset(after_contract):
        mismatches.append("after_context_contract_incomplete")
        after_contract = after_contract if isinstance(after_contract, dict) else {}
    elif set(after_contract) != required_context:
        mismatches.append("after_context_contract_keys_invalid")
    if bctx.get("comparison_contract_sha256") != _canonical_hash(before_contract):
        mismatches.append("before_context_contract_hash_invalid")
    if actx.get("comparison_contract_sha256") != _canonical_hash(after_contract):
        mismatches.append("after_context_contract_hash_invalid")

    def validate_selected_tests(
        label: str,
        capture: dict[str, Any],
        contract: dict[str, Any],
    ) -> None:
        selected = contract.get("selected_tests")
        if not isinstance(selected, dict):
            mismatches.append(f"{label}_selected_test_contract_invalid")
            return
        selected_keys_valid = set(selected) == {
            "bound", "selection_roots", "rows", "pytest_args_sha256",
            "all_available", "inventory_sha256",
        }
        rows = selected.get("rows")
        roots = selected.get("selection_roots")
        parsed = _parse_pytest_selection(capture.get("pytest_args"))
        parsed_by_path = {
            entry["path"]: entry["parse_kind"] for entry in parsed["entries"]
        }
        payload = {
            "bound": selected.get("bound"),
            "selection_roots": roots,
            "rows": rows,
        }
        rows_valid = (
            isinstance(rows, list)
            and bool(rows)
            and all(
                isinstance(row, dict)
                and isinstance(row.get("path"), str)
                and row.get("expected_kind") in {
                    "file", "directory", "missing", "outside_repo",
                    "unsupported_argument",
                }
                and isinstance(row.get("available"), bool)
                for row in rows
            )
        )
        roots_valid = (
            isinstance(roots, list)
            and all(isinstance(root, str) for root in roots)
            and roots == sorted(set(roots))
            and rows_valid
            and roots == sorted(row["path"] for row in rows)
        )
        selection_matches_capture = bool(
            roots_valid
            and selected.get("bound") is parsed["bound"]
            and roots == parsed["selection_roots"]
            and all(
                (
                    parsed_by_path[row["path"]] == "literal"
                    and row["expected_kind"] in {"file", "directory", "missing"}
                )
                or row["expected_kind"] == parsed_by_path[row["path"]]
                for row in rows
            )
        )
        computed_available = bool(
            parsed["bound"] is True
            and parsed["all_supported"]
            and rows_valid
            and roots_valid
            and selection_matches_capture
            and all(row["expected_kind"] in {"file", "directory"} for row in rows)
            and all(row["available"] for row in rows)
        )
        if (
            not selected_keys_valid
            or not roots_valid
            or selected.get("inventory_sha256") != _canonical_hash(payload)
            or selected.get("all_available") is not computed_available
        ):
            mismatches.append(f"{label}_selected_test_contract_invalid")
        if not selection_matches_capture:
            mismatches.append(f"{label}_selected_test_selection_mismatch")
        if selected.get("pytest_args_sha256") != _canonical_hash(
            capture.get("pytest_args")
        ):
            mismatches.append(f"{label}_selected_test_args_mismatch")
        if not computed_available:
            mismatches.append(f"{label}_selected_test_unavailable")

    validate_selected_tests("before", before, before_contract)
    validate_selected_tests("after", after, after_contract)
    if before_contract != after_contract:
        for key in sorted(required_context):
            if before_contract.get(key) != after_contract.get(key):
                mismatches.append(key)
    before_scope = {"pytest_args": before.get("pytest_args"), **before_contract}
    after_scope = {"pytest_args": after.get("pytest_args"), **after_contract}
    before_scope_hash = _canonical_hash(before_scope)
    after_scope_hash = _canonical_hash(after_scope)
    if before_scope_hash != after_scope_hash:
        mismatches.append("scope_contract")
    bbad = set(before.get("failed", [])) | set(before.get("errored", []))
    abad = set(after.get("failed", [])) | set(after.get("errored", []))
    regressed = sorted(abad - bbad)
    fixed = sorted(bbad - abad)
    status = "REFUSED_CONTEXT_MISMATCH" if mismatches else (
        "REGRESSION" if regressed else "NO_REGRESSION"
    )
    comparable = not mismatches
    def _identity_summary(values: list[str]) -> dict[str, Any]:
        by_file = Counter(value.split("::", 1)[0] for value in values)
        return {
            "count": len(values),
            "nodeids_sha256": _canonical_hash(values),
            "by_file": dict(by_file.most_common()),
        }
    result = {
        "schema": "gtos.wave21.equal_scope_ab.v2",
        "status": status,
        "same_scope": comparable,
        "context_mismatches": sorted(set(mismatches)),
        "before_scope_sha256": before_scope_hash,
        "after_scope_sha256": after_scope_hash,
        "before_capture_usable": before.get("usable_as_baseline") is True,
        "after_capture_usable": after.get("usable_as_baseline") is True,
        "before_parse_complete": before.get("parse_complete") is True,
        "after_parse_complete": after.get("parse_complete") is True,
        "pytest_args": before.get("pytest_args") if comparable else None,
        "bad_before": len(bbad),
        "bad_after": len(abad),
        "unchanged": len(bbad & abad),
        "fixed": fixed if comparable else [],
        "regressed": regressed if comparable else [],
        "diagnostic_only_incomparable_removed": (
            _identity_summary(fixed) if not comparable else None
        ),
        "diagnostic_only_incomparable_added": (
            _identity_summary(regressed) if not comparable else None
        ),
        "flake_rule": (
            "No failure is suppressed here. A suspected flake remains a regression until the "
            "exact node and containing module are rerun at both commits with recorded attempts."
        ),
    }
    return result, 0 if status == "NO_REGRESSION" else 1


def compact_inspection(report: dict[str, Any]) -> dict[str, Any]:
    """Retain every comparison root and gate while dropping bulky inherited rows."""

    fixtures = report.get("required_fixtures", {})
    fixture_rows = [
        {key: row.get(key) for key in (
            "path", "reason", "kind", "state", "expected_sha256",
            "expected_hydrated_size", "working_sha256", "matches_expected",
        )}
        for row in fixtures.get("rows", [])
    ]
    import_source = report.get("import_closure", {})
    import_lanes = {}
    for lane, entries in import_source.get("lanes", {}).items():
        import_lanes[lane] = [{
            "entrypoint": entry.get("entrypoint"),
            "status": entry.get("status"),
            "path_count": entry.get("path_count"),
            "closure_sha256": entry.get("closure_sha256"),
            "unresolved_first_party_count": len(entry.get("unresolved_first_party", [])),
            "unresolved_first_party_sha256": _canonical_hash(
                entry.get("unresolved_first_party", [])
            ),
        } for entry in entries]
    compact = {
        "schema": "gtos.wave21.sparse_verification_compact.v1",
        "source_schema": report.get("schema"),
        "source_deterministic_payload_sha256": report.get("deterministic_payload_sha256"),
        "generated_at_utc": report.get("generated_at_utc"),
        "authority": report.get("authority"),
        "git": report.get("git"),
        "environment": report.get("environment"),
        "sparse": report.get("sparse"),
        "lfs": report.get("lfs"),
        "selected_test_availability": report.get("selected_test_availability"),
        "required_fixtures": {
            "count": fixtures.get("count"),
            "counts": fixtures.get("counts"),
            "comparison_sha256": fixtures.get("comparison_sha256"),
            "reviewed_fixture_tier_ready": fixtures.get("reviewed_fixture_tier_ready"),
            "rows": fixture_rows,
        },
        "oversized_git_blobs": {
            key: report.get("oversized_git_blobs", {}).get(key) for key in (
                "threshold_bytes", "current_count", "current_bytes",
                "current_inventory_sha256", "new_since_base_count", "new_since_base", "gate",
            )
        },
        "secret_scan": {
            key: report.get("secret_scan", {}).get(key) for key in (
                "scanner", "current_hit_count", "current_hits_redacted", "inventory_sha256",
                "new_since_base_count", "new_since_base_redacted", "gate",
            )
        },
        "import_closure": {
            "method": import_source.get("method"),
            "gate": import_source.get("gate"),
            "inventory_sha256": import_source.get("inventory_sha256"),
            "missing_entrypoints": import_source.get("missing_entrypoints"),
            "lanes": import_lanes,
        },
        "focused_suites": report.get("focused_suites"),
        "baseline": report.get("baseline"),
        "comparison_contract": report.get("comparison_contract"),
        "comparison_contract_sha256": report.get("comparison_contract_sha256"),
        "integrity_gate": report.get("integrity_gate"),
    }
    stable = {key: value for key, value in compact.items() if key != "generated_at_utc"}
    compact["deterministic_payload_sha256"] = _canonical_hash(stable)
    return compact


def build_determinism_check(first_path: Path, second_path: Path) -> tuple[dict[str, Any], int]:
    first = json.loads(first_path.read_text(encoding="utf-8"))
    second = json.loads(second_path.read_text(encoding="utf-8"))
    first_hash = first.get("deterministic_payload_sha256")
    second_hash = second.get("deterministic_payload_sha256")
    valid = all(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
                for value in (first_hash, second_hash))
    same = valid and first_hash == second_hash
    result = {
        "schema": "gtos.wave21.determinism_check.v1",
        "status": "PASS" if same else "FAIL",
        "first": str(first_path),
        "second": str(second_path),
        "first_deterministic_payload_sha256": first_hash,
        "second_deterministic_payload_sha256": second_hash,
        "hashes_well_formed": valid,
        "generated_timestamp_excluded_by_contract": True,
    }
    return result, 0 if same else 1


def build_shards(count: int) -> tuple[dict[str, Any], int]:
    env = os.environ.copy()
    env.pop("FORCE_COLOR", None)
    env.update(NO_COLOR="1", PY_COLORS="0", PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--color=no",
         "-p", "no:cacheprovider", "--continue-on-collection-errors", "tests/"],
        cwd=REPO, capture_output=True, text=True, env=env,
    )
    nodeids = sorted({line.strip() for line in proc.stdout.splitlines()
                      if line.startswith("tests/") and "::" in line})
    weights = Counter(node.split("::", 1)[0] for node in nodeids)
    all_files = sorted({str(path.relative_to(REPO)) for pattern in ("test_*.py", "*_test.py")
                        for path in (REPO / "tests").rglob(pattern) if path.is_file()})
    bins = [{"weight": 0, "files": []} for _ in range(count)]
    for path in sorted(all_files, key=lambda item: (-max(1, weights[item]), item)):
        target = min(range(count), key=lambda index: (bins[index]["weight"], index))
        bins[target]["files"].append(path)
        bins[target]["weight"] += max(1, weights[path])
    shards = []
    for index, row in enumerate(bins, 1):
        files = sorted(row["files"])
        shards.append({
            "id": f"shard_{index:02d}",
            "estimated_collected_nodes": row["weight"],
            "pytest_args": files,
            "pytest_args_sha256": _canonical_hash(files),
            "execution": "sequential_by_default",
        })
    result = {
        "schema": "gtos.wave21.pytest_shards.v1",
        "collection_returncode": proc.returncode,
        "collection_node_count": len(nodeids),
        "collection_nodeids_sha256": _canonical_hash(nodeids),
        "test_file_count": len(all_files),
        "shards": shards,
        "coverage": {
            "overlap_count": sum(len(row["files"]) for row in bins) - len(all_files),
            "missing_files": sorted(set(all_files) - {p for row in bins for p in row["files"]}),
        },
        "resource_policy": {
            "default": "run shards sequentially; one pytest process",
            "thread_caps": "OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1",
            "certification": "a final monolithic run remains required for suite-order effects",
        },
    }
    usable = not result["coverage"]["overlap_count"] and not result["coverage"]["missing_files"]
    result["usable"] = usable
    return result, 0 if usable else 2


def hydrate_required(*, apply: bool, max_bytes: int) -> tuple[dict[str, Any], int]:
    """Materialise only the reviewed fixture allowlist, without widening cone sparse rules."""

    tree = _tree_rows("HEAD")
    before = _fixture_inventory(tree)
    rows = before["rows"]
    paths = [row["path"] for row in rows]
    forbidden = [path for path in paths if "REPLAY_EXTENSION" in path]
    expected_bytes = sum(int(row.get("expected_hydrated_size") or 0) for row in rows)
    errors = []
    if forbidden:
        errors.append("forbidden_REPLAY_EXTENSION_path")
    if expected_bytes > max_bytes:
        errors.append("hydration_byte_cap_exceeded")
    if apply and not errors:
        proc = _git("checkout", "--ignore-skip-worktree-bits", "HEAD", "--", *paths, check=False)
        if proc.returncode:
            errors.append("git_checkout_failed: " + proc.stderr.strip())
        lfs_paths = [row["path"] for row in rows if row.get("kind") == "lfs"]
        if lfs_paths and not errors:
            lfs_proc = _run(["git", "lfs", "checkout", "--", *lfs_paths], check=False)
            if lfs_proc.returncode:
                errors.append("git_lfs_checkout_failed: " + lfs_proc.stderr.strip())
    after = _fixture_inventory(tree)
    result = {
        "schema": "gtos.wave21.exact_fixture_hydration.v1",
        "mode": "applied" if apply else "plan_only",
        "network_used": False,
        "sparse_rules_widened": False,
        "path_count": len(paths),
        "expected_hydrated_bytes": expected_bytes,
        "max_bytes": max_bytes,
        "forbidden_paths": forbidden,
        "paths": paths,
        "before_counts": before["counts"],
        "after_counts": after["counts"],
        "after_comparison_sha256": after["comparison_sha256"],
        "after_reviewed_fixture_tier_ready": after["reviewed_fixture_tier_ready"],
        "errors": errors,
    }
    if errors:
        return result, 2
    if apply and not after["reviewed_fixture_tier_ready"]:
        result["errors"].append("one_or_more_exact_fixtures_not_materialized_or_hash_mismatched")
        return result, 1
    return result, 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inspect_p = sub.add_parser("inspect", help="emit environment and repository verification")
    inspect_p.add_argument("--base", default=DEFAULT_BASE)
    inspect_p.add_argument(
        "--baseline",
        type=Path,
        help="pytest capture whose exact selected-test availability is bound for A/B use",
    )
    inspect_p.add_argument("--wall-seconds", type=float)
    inspect_p.add_argument("--max-rss-bytes", type=int)
    inspect_p.add_argument("-o", "--output", type=Path, required=True)
    compact_p = sub.add_parser("compact-inspection", help="compact a detailed inspection receipt")
    compact_p.add_argument("inspection", type=Path)
    compact_p.add_argument("-o", "--output", type=Path, required=True)
    deterministic_p = sub.add_parser("determinism-check", help="compare deterministic receipt hashes")
    deterministic_p.add_argument("first", type=Path)
    deterministic_p.add_argument("second", type=Path)
    deterministic_p.add_argument("-o", "--output", type=Path, required=True)
    shard_p = sub.add_parser("shards", help="build a deterministic whole-file shard plan")
    shard_p.add_argument("--count", type=int, default=4)
    shard_p.add_argument("-o", "--output", type=Path, required=True)
    ab_p = sub.add_parser("ab-guard", help="fail closed unless captures have equal context")
    ab_p.add_argument("--before-capture", type=Path, required=True)
    ab_p.add_argument("--after-capture", type=Path, required=True)
    ab_p.add_argument("--before-inspection", type=Path, required=True)
    ab_p.add_argument("--after-inspection", type=Path, required=True)
    ab_p.add_argument("-o", "--output", type=Path, required=True)
    pack_p = sub.add_parser("context-pack", help="persist the mandated ultimate Context OS pack")
    pack_p.add_argument("--task", required=True)
    pack_p.add_argument("--include-memory", action="store_true")
    pack_p.add_argument("--no-health", action="store_true")
    pack_p.add_argument("-o", "--output", type=Path, required=True)
    hydrate_p = sub.add_parser("hydrate-required", help="plan/apply exact offline fixture hydration")
    hydrate_p.add_argument("--apply", action="store_true")
    hydrate_p.add_argument("--max-bytes", type=int, default=20 * 1024 * 1024)
    hydrate_p.add_argument("-o", "--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "inspect":
        report = build_inspection(
            base=args.base, baseline=args.baseline, wall_seconds=args.wall_seconds,
            max_rss_bytes=args.max_rss_bytes,
        )
        _write_json(args.output, report)
        print(f"{report['integrity_gate']} {report['deterministic_payload_sha256']} -> {args.output}")
        return 0 if report["integrity_gate"] == "PASS" else 1
    if args.command == "compact-inspection":
        report = compact_inspection(json.loads(args.inspection.read_text(encoding="utf-8")))
        _write_json(args.output, report)
        print(f"{report['integrity_gate']} {report['deterministic_payload_sha256']} -> {args.output}")
        return 0 if report["integrity_gate"] == "PASS" else 1
    if args.command == "determinism-check":
        report, code = build_determinism_check(args.first, args.second)
        _write_json(args.output, report)
        print(f"{report['status']} {report['first_deterministic_payload_sha256']} -> {args.output}")
        return code
    if args.command == "shards":
        if args.count < 1:
            raise SystemExit("--count must be positive")
        report, code = build_shards(args.count)
        _write_json(args.output, report)
        print(f"{len(report['shards'])} shards / {report['collection_node_count']} nodes -> {args.output}")
        return code
    if args.command == "context-pack":
        from src.gtos_context_os.pack import build_context_pack, render_markdown_pack

        pack = build_context_pack(
            args.task,
            repo=REPO,
            profile="ultimate",
            include_memory=args.include_memory,
            include_health=not args.no_health,
            auto_build=True,
            auto_rebuild_stale=True,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_markdown_pack(pack), encoding="utf-8")
        print(f"ultimate Context OS pack -> {args.output}")
        return 0
    if args.command == "hydrate-required":
        report, code = hydrate_required(apply=args.apply, max_bytes=args.max_bytes)
        _write_json(args.output, report)
        print(f"{report['mode']} {report['path_count']} paths / "
              f"{report['expected_hydrated_bytes']} bytes -> {args.output}")
        return code
    report, code = build_ab_guard(
        args.before_capture, args.after_capture,
        args.before_inspection, args.after_inspection,
    )
    _write_json(args.output, report)
    print(f"{report['status']} -> {args.output}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
