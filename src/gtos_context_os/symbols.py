"""Live Python symbol map for GTOS Context OS."""

from __future__ import annotations

import re
import select
import subprocess
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

from src.gtos_context_os.catalog import query_terms, utc_now


DEFAULT_SYMBOL_ROOTS = (
    "src",
    "scripts",
    "tests",
)
EXCLUDE_DIR_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}
CLASS_RE = re.compile(r"^(?P<indent>\s*)class\s+(?P<name>[A-Za-z_]\w*)\b")
FUNCTION_RE = re.compile(r"^(?P<indent>\s*)(?P<async>async\s+)?def\s+(?P<name>[A-Za-z_]\w*)\s*\(")
TRIPLE_QUOTES = ('"""', "'''")


def build_symbol_index(
    *,
    repo: Path | str = ".",
    roots: Sequence[str] = DEFAULT_SYMBOL_ROOTS,
    max_files: int = 5000,
) -> dict[str, Any]:
    """Scan live Python files and return a compact symbol index."""

    repo_path = Path(repo).resolve()
    symbols: list[dict[str, Any]] = []
    parsed_files = 0
    skipped_files = 0
    errors: list[dict[str, Any]] = []
    for path in _iter_python_files(repo_path, roots):
        if parsed_files >= max_files:
            break
        parsed_files += 1
        rel = _relative_to_repo(repo_path, path)
        try:
            symbols.extend(_symbols_from_file(path, rel))
        except (OSError, UnicodeError) as exc:
            skipped_files += 1
            errors.append({"path": rel, "error_type": type(exc).__name__, "error": str(exc)[:300]})
            continue
    return {
        "schema_version": "gtos_context_symbol_index_v1",
        "generated_at_utc": utc_now(),
        "repo": repo_path.as_posix(),
        "roots": list(roots),
        "parse_mode": "streaming_definition_scan",
        "parsed_files": parsed_files,
        "skipped_files": skipped_files,
        "symbol_count": len(symbols),
        "symbols": symbols,
        "errors": errors[:20],
        "truncated_errors": len(errors) > 20,
        "use_boundary": "symbol_index_is_live_code_navigation_verify_source_before_claims",
    }


def search_symbols(
    query: str,
    *,
    repo: Path | str = ".",
    roots: Sequence[str] = DEFAULT_SYMBOL_ROOTS,
    limit: int = 20,
    max_files: int = 5000,
    max_file_bytes: int = 750_000,
    max_elapsed_seconds: float | None = 5.0,
) -> dict[str, Any]:
    """Search live Python symbols by name, qualified name, file, and docstring."""

    repo_path = Path(repo).resolve()
    terms = query_terms(query)
    candidates, prefilter = _prefilter_python_files(
        repo_path,
        roots,
        terms,
        max_files=max_files,
    )
    symbols: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    parsed_files = 0
    skipped_files = 0
    skipped_large_files: list[dict[str, Any]] = []
    started = time.perf_counter()
    truncated_by_time = False
    for path in candidates:
        if parsed_files >= max_files:
            break
        rel = _relative_to_repo(repo_path, path)
        if max_elapsed_seconds is not None and time.perf_counter() - started >= max_elapsed_seconds:
            truncated_by_time = True
            break
        try:
            size_bytes = path.stat().st_size
        except OSError:
            size_bytes = 0
        if (
            max_file_bytes > 0
            and size_bytes > max_file_bytes
            and _path_query_score(rel, terms) <= 0
        ):
            skipped_large_files.append({"path": rel, "size_bytes": size_bytes})
            continue
        parsed_files += 1
        try:
            symbols.extend(_symbols_from_file(path, rel))
        except (OSError, UnicodeError) as exc:
            skipped_files += 1
            errors.append({"path": rel, "error_type": type(exc).__name__, "error": str(exc)[:300]})
    hits: list[dict[str, Any]] = []
    for symbol in symbols:
        score = _symbol_score(symbol, terms)
        if score <= 0:
            continue
        item = dict(symbol)
        item["score"] = score
        hits.append(item)
    hits.sort(key=lambda item: (-int(item["score"]), item["path"], int(item["line"])))
    return {
        "schema_version": "gtos_context_symbol_search_v1",
        "generated_at_utc": utc_now(),
        "query": query,
        "terms": terms,
        "repo": repo_path.as_posix(),
        "roots": list(roots),
        "prefilter": prefilter,
        "parse_mode": "rg_prefiltered_streaming_definition_scan",
        "parsed_files": parsed_files,
        "skipped_files": skipped_files,
        "skipped_large_files": skipped_large_files[:20],
        "truncated_large_files": len(skipped_large_files) > 20,
        "truncated_by_time": truncated_by_time,
        "max_file_bytes": max_file_bytes,
        "max_elapsed_seconds": max_elapsed_seconds,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "symbol_count": len(symbols),
        "hit_count": len(hits),
        "hits": hits[:limit],
        "errors": errors[:20],
        "use_boundary": "symbol_search_is_navigation_intelligence_open_source_before_claims",
    }


def _iter_python_files(repo: Path, roots: Sequence[str]) -> Iterable[Path]:
    for raw in roots:
        root = repo / raw
        if not root.exists():
            continue
        if root.is_file():
            if root.suffix == ".py" and not _excluded(root):
                yield root
            continue
        for path in sorted(root.rglob("*.py")):
            if path.is_file() and not _excluded(path):
                yield path


def _excluded(path: Path) -> bool:
    return bool(EXCLUDE_DIR_PARTS & set(path.parts))


def _relative_to_repo(repo: Path, path: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return path.as_posix()


def _prefilter_python_files(
    repo: Path,
    roots: Sequence[str],
    terms: Sequence[str],
    *,
    max_files: int,
) -> tuple[list[Path], dict[str, Any]]:
    root_args = [str(root) for root in roots if (repo / root).exists() or Path(root).is_absolute()]
    if not root_args:
        return [], {
            "mode": "no_existing_roots",
            "candidate_files": 0,
            "terms": list(terms),
        }
    all_files, all_status = _rg_python_files(repo, root_args, max_files=max_files)
    content_matches, content_status = _rg_content_matches(
        repo,
        root_args,
        terms,
        max_files=max_files,
    )
    if all_files:
        all_by_rel = {_relative_to_repo(repo, path): path for path in all_files}
    else:
        all_by_rel = {_relative_to_repo(repo, path): path for path in _iter_python_files(repo, roots)}
    path_matches = [
        path
        for rel, path in all_by_rel.items()
        if terms and any(term in rel.lower() for term in terms)
    ]

    ordered: list[Path] = []
    seen: set[Path] = set()
    for path in sorted(
        [*path_matches, *content_matches],
        key=lambda item: (-_path_query_score(_relative_to_repo(repo, item), terms), _relative_to_repo(repo, item)),
    ):
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(resolved)
        if len(ordered) >= max_files:
            break

    if not ordered and not content_matches:
        fallback_limit = min(max_files, 250)
        for rel, path in sorted(
            all_by_rel.items(),
            key=lambda item: (-_path_query_score(item[0], terms), item[0]),
        )[:fallback_limit]:
            ordered.append(path.resolve())

    return ordered, {
        "mode": _prefilter_mode(content_status, bool(content_matches)),
        "terms": list(terms),
        "all_file_status": all_status,
        "content_match_status": content_status,
        "all_python_files": len(all_by_rel),
        "path_match_files": len(path_matches),
        "content_match_files": len(content_matches),
        "candidate_files": len(ordered),
        "max_files": max_files,
    }


def _prefilter_mode(content_status: dict[str, Any], has_content_matches: bool) -> str:
    status = str(content_status.get("status") or "")
    if status == "ok":
        return "rg_prefilter"
    if has_content_matches:
        return f"rg_prefilter_{status or 'partial'}"
    return "python_fallback"


def _rg_python_files(repo: Path, root_args: Sequence[str], *, max_files: int) -> tuple[list[Path], dict[str, Any]]:
    cmd = ["rg", "--files", "--glob", "*.py", *root_args]
    return _run_rg_paths(repo, cmd, timeout_seconds=1.0, max_paths=max_files)


def _rg_content_matches(
    repo: Path,
    root_args: Sequence[str],
    terms: Sequence[str],
    *,
    max_files: int,
) -> tuple[list[Path], dict[str, Any]]:
    rg_terms = sorted(
        [term for term in terms if len(term) >= 3],
        key=lambda term: (("_" in term), len(term), term),
        reverse=True,
    )[:6]
    if not rg_terms:
        return [], {"status": "skipped", "reason": "no_terms"}
    paths: list[Path] = []
    seen: set[Path] = set()
    term_statuses: list[dict[str, Any]] = []
    target_paths = min(max_files, 300)
    for term in rg_terms:
        if len(paths) >= target_paths:
            break
        cmd = ["rg", "-l", "-i", "--fixed-strings", "--glob", "*.py", "-e", term, *root_args]
        term_paths, status = _run_rg_paths(
            repo,
            cmd,
            timeout_seconds=0.25,
            max_paths=max(20, min(100, target_paths - len(paths))),
        )
        status["term"] = term
        term_statuses.append(status)
        for path in term_paths:
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            paths.append(resolved)
            if len(paths) >= target_paths:
                break
    if paths:
        status = "partial" if any(item.get("terminated") for item in term_statuses) else "ok"
    elif any(item.get("status") == "timeout" for item in term_statuses):
        status = "timeout"
    else:
        status = "ok"
    return paths, {
        "status": status,
        "path_count": len(paths),
        "term_statuses": term_statuses,
    }


def _run_rg_paths(
    repo: Path,
    cmd: Sequence[str],
    *,
    timeout_seconds: float,
    max_paths: int,
) -> tuple[list[Path], dict[str, Any]]:
    try:
        process = subprocess.Popen(
            list(cmd),
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        return [], {"status": "unavailable", "error": "rg_not_found"}
    paths: list[Path] = []
    started = time.perf_counter()
    deadline = started + timeout_seconds
    terminated = False
    assert process.stdout is not None
    while len(paths) < max_paths:
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            break
        ready, _, _ = select.select([process.stdout], [], [], remaining)
        if not ready:
            break
        raw = process.stdout.readline()
        if raw == "":
            if process.poll() is not None:
                break
            continue
        if not raw.strip():
            continue
        path = Path(raw.strip())
        resolved = path if path.is_absolute() else repo / path
        if resolved.exists() and resolved.is_file():
            paths.append(resolved.resolve())
    if process.poll() is None:
        terminated = True
        process.terminate()
        try:
            process.wait(timeout=0.2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1.0)
    returncode = process.returncode
    stderr = ""
    if process.stderr is not None:
        try:
            stderr = process.stderr.read(500)
        except OSError:
            stderr = ""
    if returncode not in (0, 1, -15) and not paths:
        return [], {
            "status": "error",
            "returncode": returncode,
            "stderr": stderr[:500],
            "terminated": terminated,
        }
    elapsed = round(time.perf_counter() - started, 6)
    status = "ok"
    if terminated and paths:
        status = "partial"
    elif terminated:
        status = "timeout"
    return paths, {
        "status": status,
        "returncode": returncode,
        "path_count": len(paths),
        "elapsed_seconds": elapsed,
        "terminated": terminated,
    }


def _path_query_score(rel_path: str, terms: Sequence[str]) -> int:
    lowered = rel_path.lower()
    score = 0
    for term in terms:
        if term in lowered:
            score += 20
    if "gtos_context_os" in lowered:
        score += 8
    if lowered.startswith("src/"):
        score += 5
    if lowered.startswith("tests/"):
        score += 3
    return score


def _symbols_from_file(path: Path, rel_path: str) -> list[dict[str, Any]]:
    symbols: list[dict[str, Any]] = []
    class_stack: list[tuple[int, str]] = []
    pending_doc: tuple[int, int] | None = None

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.expandtabs(4).rstrip("\n")
            stripped = line.strip()
            indent = len(line) - len(line.lstrip(" "))

            if pending_doc and stripped and not stripped.startswith("#"):
                symbol_index, owner_indent = pending_doc
                if indent > owner_indent and stripped.startswith(TRIPLE_QUOTES):
                    symbols[symbol_index]["doc"] = _one_line_docstring(stripped)
                pending_doc = None

            if not stripped or stripped.startswith("#"):
                continue

            while class_stack and indent <= class_stack[-1][0]:
                class_stack.pop()

            class_match = CLASS_RE.match(line)
            if class_match:
                name = class_match.group("name")
                qualname = ".".join([*(item[1] for item in class_stack), name])
                symbols.append(
                    _symbol_record(
                        rel_path=rel_path,
                        name=name,
                        qualname=qualname,
                        kind="class",
                        line=line_no,
                    )
                )
                pending_doc = (len(symbols) - 1, indent)
                class_stack.append((indent, name))
                continue

            function_match = FUNCTION_RE.match(line)
            if function_match:
                name = function_match.group("name")
                parents = [item[1] for item in class_stack]
                qualname = ".".join([*parents, name])
                if parents:
                    kind = "async_method" if function_match.group("async") else "method"
                else:
                    kind = "async_function" if function_match.group("async") else "function"
                symbols.append(
                    _symbol_record(
                        rel_path=rel_path,
                        name=name,
                        qualname=qualname,
                        kind=kind,
                        line=line_no,
                    )
                )
                pending_doc = (len(symbols) - 1, indent)

    return symbols


def _symbol_record(*, rel_path: str, name: str, qualname: str, kind: str, line: int) -> dict[str, Any]:
    return {
        "path": rel_path,
        "name": name,
        "qualname": qualname,
        "kind": kind,
        "line": line,
        "end_line": line,
        "doc": "",
    }


def _one_line_docstring(stripped_line: str) -> str:
    quote = next((item for item in TRIPLE_QUOTES if stripped_line.startswith(item)), "")
    if not quote:
        return ""
    body = stripped_line[len(quote):]
    if quote in body:
        body = body.split(quote, 1)[0]
    return body.strip()[:240]


def _symbol_score(symbol: dict[str, Any], terms: Sequence[str]) -> int:
    if not terms:
        return 0
    name = str(symbol.get("name") or "").lower()
    qualname = str(symbol.get("qualname") or "").lower()
    path = str(symbol.get("path") or "").lower()
    doc = str(symbol.get("doc") or "").lower()
    haystack = "\n".join([name, qualname, path, doc])
    if not any(term in haystack for term in terms):
        return 0
    score = 0
    for term in terms:
        if term == name:
            score += 80
        if term in name:
            score += 35
        if term in qualname:
            score += 25
        if term in path:
            score += 10
        if term in doc:
            score += 5
    if all(term in haystack for term in terms):
        score += 40
    return score
