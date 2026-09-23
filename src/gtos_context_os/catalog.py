"""SQLite catalog and search engine for GTOS Context OS."""

from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import sqlite3
import subprocess
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Sequence, TypeVar

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX fallback.
    fcntl = None  # type: ignore[assignment]

from src.gtos_context_os.classifier import AUTHORITY_WEIGHT, classify_path, normalize_relative_path


SCHEMA_VERSION = "gtos_context_catalog_v1"
DEFAULT_DB_PATH = Path(".context/context_os/catalog.sqlite")
CURRENT_CONTEXT_ROOTS = (
    ".context/LIVE_STATE.md",
    ".context/00_core",
    ".context/context_os/ACTIVE_SESSION_STATE.json",
    ".context/context_os/CURRENT_ROOT_CAUSE_MAP.json",
    ".context/context_os/CONTINUATION_CURSOR.json",
    "config",
    "scripts/gtos_context.py",
    "src/gtos_context_os",
    "tests/test_gtos_context_os.py",
    "AGENTS.md",
    "CLAUDE.md",
    "pyproject.toml",
    "requirements.txt",
)
DEEP_CONTEXT_ROOTS = (
    ".context",
    "config",
    "scripts/gtos_context.py",
    "src/gtos_context_os",
    "tests/test_gtos_context_os.py",
    "AGENTS.md",
    "CLAUDE.md",
    "pyproject.toml",
    "requirements.txt",
    "research/operations",
)
DEFAULT_ROOTS = CURRENT_CONTEXT_ROOTS
DEFAULT_TEXT_SUFFIXES = {
    ".cfg",
    ".csv",
    ".ini",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
EXCLUDE_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "gold_agent.egg-info",
}
DEFAULT_MAX_FILE_BYTES = 1_000_000
DEFAULT_MAX_TEXT_BYTES = 64_000
DEFAULT_FILE_READ_TIMEOUT_SECONDS = 5.0
ROUTE_METADATA_ONLY_NAME_TOKENS = (
    "SMOKE",
    "PARTIAL",
    "LEDGER",
    "TRADE_LEDGER",
    "ORDER_LEDGER",
    "MISSED",
    "BUCKET",
    "FLOW",
)
FRESHNESS_ANCHORS = (
    ".context/LIVE_STATE.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/gtos_context_os.md",
    ".context/00_core/gtos_second_brain.md",
    "AGENTS.md",
    "CLAUDE.md",
)
T = TypeVar("T")


@dataclass(frozen=True)
class CatalogBuildResult:
    db_path: Path
    indexed_documents: int
    metadata_only_documents: int
    skipped_paths: int
    roots: tuple[str, ...]
    generated_at_utc: str
    reused_existing: bool = False


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def catalog_build_lock(db_path: Path) -> Iterable[None]:
    """Serialize catalog rebuilds across parallel agents.

    Context OS is a preflight helper.  Multiple subagents may start together,
    but they must not all write the same SQLite database at once.  The lock is
    advisory on POSIX; non-POSIX falls back to atomic replacement without the
    extra serialization.
    """

    lock_path = db_path.with_suffix(db_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a", encoding="utf-8")
    try:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS catalog_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS documents (
            path TEXT PRIMARY KEY,
            abs_path TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            mtime_ns INTEGER NOT NULL,
            sha256 TEXT,
            suffix TEXT NOT NULL,
            doc_type TEXT NOT NULL,
            authority_tier TEXT NOT NULL,
            evidence_class TEXT NOT NULL,
            freshness TEXT NOT NULL,
            route TEXT,
            title TEXT NOT NULL,
            search_text TEXT NOT NULL,
            content_status TEXT NOT NULL,
            indexed_at_utc TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_documents_authority
            ON documents(authority_tier);
        CREATE INDEX IF NOT EXISTS idx_documents_route
            ON documents(route);
        CREATE INDEX IF NOT EXISTS idx_documents_evidence
            ON documents(evidence_class);
        """
    )


def _iter_roots(repo: Path, roots: Sequence[str]) -> Iterable[Path]:
    for raw in roots:
        path = repo / raw
        if path.exists():
            yield path


def _iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        parts = set(path.parts)
        if EXCLUDE_DIRS & parts:
            continue
        yield path


def _is_text_candidate(path: Path, include_jsonl: bool) -> bool:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return include_jsonl
    return suffix in DEFAULT_TEXT_SUFFIXES


def _metadata_only_by_default(relative_path: str, path: Path) -> bool:
    """Keep volatile route evidence cold unless a caller explicitly asks for it.

    Context OS should make agent work faster and safer.  Broad replay smoke,
    partial, bucket, missed, order, trade, and ledger artifacts are exact-path
    evidence, not default prompt/search text.  They can be inspected directly
    when a route needs them, but one slow or active artifact must not stall a
    normal catalog build.
    """

    parts = Path(relative_path).parts
    if len(parts) < 3 or parts[0] != "research" or parts[1] != "operations":
        return False
    upper_name = path.name.upper()
    if path.suffix.lower() == ".jsonl":
        return True
    return any(token in upper_name for token in ROUTE_METADATA_ONLY_NAME_TOKENS)


def _relative_to_repo(repo: Path, path: Path) -> str:
    try:
        return normalize_relative_path(path.relative_to(repo))
    except ValueError:
        return path.as_posix()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_text_sample(path: Path, max_text_bytes: int) -> tuple[str, str]:
    with path.open("rb") as handle:
        raw = handle.read(max_text_bytes)
    text = raw.decode("utf-8", errors="replace")
    status = "indexed_text"
    if path.stat().st_size > max_text_bytes:
        status = "indexed_text_truncated"
    return text, status


class CatalogFileReadTimeout(TimeoutError):
    """Raised when one catalog file read exceeds the per-file budget."""


def _with_file_timeout(
    label: str,
    callback: Callable[[], T],
    timeout_seconds: float = DEFAULT_FILE_READ_TIMEOUT_SECONDS,
) -> T:
    if timeout_seconds <= 0 or threading.current_thread() is not threading.main_thread():
        return callback()

    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, 0.0)

    def _raise_timeout(_signum: int, _frame: object) -> None:
        raise CatalogFileReadTimeout(f"catalog file operation timed out: {label}")

    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, timeout_seconds)
    try:
        return callback()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, *previous_timer)


def _title_from_text(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()[:220] or path.name
        return stripped[:220]
    return path.name


def build_catalog(
    repo: Path | str = ".",
    db_path: Path | str = DEFAULT_DB_PATH,
    *,
    roots: Sequence[str] = DEFAULT_ROOTS,
    include_jsonl: bool = False,
    include_cold_metadata: bool = True,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_text_bytes: int = DEFAULT_MAX_TEXT_BYTES,
    hash_indexed_text: bool = False,
    reuse_fresh: bool = True,
) -> CatalogBuildResult:
    """Build a deterministic SQLite catalog.

    The default build indexes current context/code/config/test text and compact
    route summaries.  Large raw ledgers stay out of prompt/search text, but are
    still represented as metadata pointers unless disabled by the caller.
    """

    repo_path = Path(repo).resolve()
    db = repo_path / db_path if not Path(db_path).is_absolute() else Path(db_path)
    generated_at = utc_now()
    indexed = 0
    metadata_only = 0
    skipped = 0
    tmp_db = db.with_name(f"{db.name}.tmp.{os.getpid()}")
    normalized_roots = tuple(roots)
    build_options = {
        "include_jsonl": include_jsonl,
        "include_cold_metadata": include_cold_metadata,
        "max_file_bytes": max_file_bytes,
        "max_text_bytes": max_text_bytes,
        "hash_indexed_text": hash_indexed_text,
    }

    with catalog_build_lock(db):
        if reuse_fresh:
            reusable = _catalog_result_if_reusable(
                db,
                repo_path=repo_path,
                roots=normalized_roots,
                build_options=build_options,
            )
            if reusable is not None:
                return reusable

        _remove_sqlite_sidecars(tmp_db)
        try:
            with connect(tmp_db) as conn:
                init_schema(conn)
                conn.execute(
                    "INSERT INTO catalog_meta(key, value) VALUES (?, ?)",
                    ("schema_version", SCHEMA_VERSION),
                )
                conn.execute(
                    "INSERT INTO catalog_meta(key, value) VALUES (?, ?)",
                    ("repo", repo_path.as_posix()),
                )
                conn.execute(
                    "INSERT INTO catalog_meta(key, value) VALUES (?, ?)",
                    ("generated_at_utc", generated_at),
                )
                conn.execute(
                    "INSERT INTO catalog_meta(key, value) VALUES (?, ?)",
                    ("roots", json.dumps(list(normalized_roots))),
                )
                conn.execute(
                    "INSERT INTO catalog_meta(key, value) VALUES (?, ?)",
                    ("build_options", json.dumps(build_options, sort_keys=True)),
                )
                for key, value in _freshness_meta(repo_path).items():
                    conn.execute("INSERT INTO catalog_meta(key, value) VALUES (?, ?)", (key, value))

                for root in _iter_roots(repo_path, normalized_roots):
                    for path in _iter_files(root):
                        rel = _relative_to_repo(repo_path, path)
                        try:
                            stat = path.stat()
                        except OSError:
                            skipped += 1
                            continue
                        suffix = path.suffix.lower()
                        text = ""
                        sha256: str | None = None
                        title = path.name
                        content_status = ""
                        force_metadata_only = _metadata_only_by_default(rel, path)

                        if (
                            not force_metadata_only
                            and _is_text_candidate(path, include_jsonl)
                            and stat.st_size <= max_file_bytes
                        ):
                            try:
                                text, content_status = _with_file_timeout(
                                    f"read:{rel}",
                                    lambda path=path: _read_text_sample(path, max_text_bytes),
                                )
                                title = _title_from_text(path, text)
                                indexed += 1
                                if hash_indexed_text:
                                    try:
                                        sha256 = _with_file_timeout(
                                            f"sha256:{rel}",
                                            lambda path=path: _sha256_file(path),
                                        )
                                    except (CatalogFileReadTimeout, OSError):
                                        sha256 = None
                                        content_status = f"{content_status}_sha256_unavailable"
                            except (CatalogFileReadTimeout, OSError, UnicodeError) as exc:
                                text = ""
                                sha256 = None
                                title = path.name
                                content_status = (
                                    "metadata_only_read_error:"
                                    f"{type(exc).__name__}"
                                )
                                metadata_only += 1
                        else:
                            if suffix == ".jsonl" and not include_cold_metadata and not include_jsonl:
                                skipped += 1
                                continue
                            if stat.st_size > max_file_bytes or include_cold_metadata:
                                content_status = (
                                    "metadata_only_large_file"
                                    if stat.st_size > max_file_bytes
                                    else "metadata_only_cold_file"
                                )
                                metadata_only += 1
                            else:
                                skipped += 1
                                continue

                        classification = classify_path(rel, text)
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO documents (
                                path, abs_path, size_bytes, mtime_ns, sha256, suffix,
                                doc_type, authority_tier, evidence_class, freshness,
                                route, title, search_text, content_status, indexed_at_utc
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                rel,
                                path.resolve().as_posix(),
                                stat.st_size,
                                stat.st_mtime_ns,
                                sha256,
                                suffix,
                                classification.doc_type,
                                classification.authority_tier,
                                classification.evidence_class,
                                classification.freshness,
                                classification.route,
                                title,
                                text,
                                content_status,
                                generated_at,
                            ),
                        )
            _remove_sqlite_journals(db)
            tmp_db.replace(db)
            _remove_sqlite_journals(db)
        finally:
            _remove_sqlite_sidecars(tmp_db)

    return CatalogBuildResult(
        db_path=db,
        indexed_documents=indexed,
        metadata_only_documents=metadata_only,
        skipped_paths=skipped,
        roots=normalized_roots,
        generated_at_utc=generated_at,
    )


def _remove_sqlite_sidecars(db_path: Path) -> None:
    for path in (
        db_path,
        Path(f"{db_path}-journal"),
        Path(f"{db_path}-wal"),
        Path(f"{db_path}-shm"),
    ):
        try:
            path.unlink()
        except FileNotFoundError:
            continue
        except OSError:
            continue


def _remove_sqlite_journals(db_path: Path) -> None:
    for path in (
        Path(f"{db_path}-journal"),
        Path(f"{db_path}-wal"),
        Path(f"{db_path}-shm"),
    ):
        try:
            path.unlink()
        except FileNotFoundError:
            continue
        except OSError:
            continue


def _catalog_result_if_reusable(
    db: Path,
    *,
    repo_path: Path,
    roots: tuple[str, ...],
    build_options: dict[str, object],
) -> CatalogBuildResult | None:
    if not db.exists():
        return None
    try:
        with connect(db) as conn:
            meta = {
                row["key"]: row["value"]
                for row in conn.execute("SELECT key, value FROM catalog_meta")
            }
            stored_roots = tuple(json.loads(meta.get("roots", "[]")))
            stored_options = json.loads(meta.get("build_options", "{}"))
            total_documents = int(
                conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            )
            indexed_documents = int(
                conn.execute(
                    "SELECT COUNT(*) FROM documents WHERE content_status LIKE 'indexed_text%'"
                ).fetchone()[0]
            )
    except (OSError, sqlite3.DatabaseError, json.JSONDecodeError, TypeError, ValueError):
        return None

    if stored_roots != roots:
        return None
    if stored_options != build_options:
        return None

    current = _freshness_meta(repo_path)
    if meta.get("git_head") != current.get("git_head"):
        return None
    if meta.get("freshness_anchors") != current.get("freshness_anchors"):
        return None

    return CatalogBuildResult(
        db_path=db,
        indexed_documents=indexed_documents,
        metadata_only_documents=max(0, total_documents - indexed_documents),
        skipped_paths=0,
        roots=roots,
        generated_at_utc=meta.get("generated_at_utc") or utc_now(),
        reused_existing=True,
    )


TOKEN_RE = re.compile(r"[A-Za-z0-9_./:-]+")


def query_terms(query: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(query) if len(token) >= 2]


def _term_score(text: str, terms: Sequence[str]) -> int:
    lowered = text.lower()
    return sum(lowered.count(term) for term in terms)


def _row_score(row: sqlite3.Row, terms: Sequence[str]) -> int:
    title = str(row["title"] or "")
    path = str(row["path"] or "")
    body = str(row["search_text"] or "")
    authority = AUTHORITY_WEIGHT.get(str(row["authority_tier"]), 0)
    return (
        authority
        + 12 * _term_score(title, terms)
        + 8 * _term_score(path, terms)
        + 2 * _term_score(body, terms)
    )


def fetch_documents(
    db_path: Path | str = DEFAULT_DB_PATH,
    *,
    repo: Path | str = ".",
    where: str = "",
    params: Sequence[object] = (),
    order_by: str = "authority_tier, path",
    limit: int | None = None,
) -> list[dict[str, object]]:
    """Fetch catalog rows as dictionaries.

    ``where`` and ``order_by`` are internal CLI/query surfaces, not user input
    SQL.  Public commands call this with fixed strings.
    """

    repo_path = Path(repo).resolve()
    db = repo_path / db_path if not Path(db_path).is_absolute() else Path(db_path)
    query = "SELECT * FROM documents"
    if where:
        query += f" WHERE {where}"
    if order_by:
        query += f" ORDER BY {order_by}"
    if limit is not None:
        query += " LIMIT ?"
        params = tuple(params) + (limit,)
    with connect(db) as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
    return [_row_to_dict(row, 0) for row in rows]


class StaleCatalogError(RuntimeError):
    """Raised when a context catalog no longer matches current disk authority."""


def _git_head(repo: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _file_signature(repo: Path, rel: str) -> dict[str, object] | None:
    path = repo / rel
    if not path.exists() or not path.is_file():
        return None
    stat = path.stat()
    return {
        "path": rel,
        "mtime_ns": stat.st_mtime_ns,
        "size_bytes": stat.st_size,
        "sha256": _sha256_file(path),
    }


def _freshness_meta(repo: Path) -> dict[str, str]:
    anchors = {
        rel: signature
        for rel in FRESHNESS_ANCHORS
        if (signature := _file_signature(repo, rel)) is not None
    }
    return {
        "git_head": _git_head(repo),
        "freshness_anchors": json.dumps(anchors, sort_keys=True),
    }


def catalog_freshness(db_path: Path | str = DEFAULT_DB_PATH, *, repo: Path | str = ".") -> dict[str, object]:
    repo_path = Path(repo).resolve()
    db = repo_path / db_path if not Path(db_path).is_absolute() else Path(db_path)
    if not db.exists():
        return {
            "status": "missing",
            "fresh": False,
            "reasons": ["catalog_missing"],
            "db_path": db.as_posix(),
        }
    with connect(db) as conn:
        meta = {row["key"]: row["value"] for row in conn.execute("SELECT key, value FROM catalog_meta")}
    current = _freshness_meta(repo_path)
    reasons: list[str] = []
    if meta.get("git_head") != current.get("git_head"):
        reasons.append("git_head_changed")
    if meta.get("freshness_anchors") != current.get("freshness_anchors"):
        reasons.append("authority_anchor_changed")
    return {
        "status": "fresh" if not reasons else "stale",
        "fresh": not reasons,
        "reasons": reasons,
        "db_path": db.as_posix(),
        "catalog_git_head": meta.get("git_head"),
        "current_git_head": current.get("git_head"),
        "catalog_generated_at_utc": meta.get("generated_at_utc"),
    }


def ensure_catalog_fresh(
    db_path: Path | str = DEFAULT_DB_PATH,
    *,
    repo: Path | str = ".",
    allow_stale: bool = False,
) -> dict[str, object]:
    freshness = catalog_freshness(db_path=db_path, repo=repo)
    if not freshness["fresh"] and not allow_stale:
        raise StaleCatalogError(
            "GTOS Context OS catalog is stale or missing: "
            + ",".join(str(reason) for reason in freshness.get("reasons", []))
            + ". Run `python3 scripts/gtos_context.py build` or pass --allow-stale explicitly."
        )
    return freshness


def search_catalog(
    query: str,
    db_path: Path | str = DEFAULT_DB_PATH,
    *,
    repo: Path | str = ".",
    limit: int = 12,
    require_all_terms: bool = True,
) -> list[dict[str, object]]:
    repo_path = Path(repo).resolve()
    db = repo_path / db_path if not Path(db_path).is_absolute() else Path(db_path)
    terms = query_terms(query)
    if not terms:
        return []
    with connect(db) as conn:
        rows = conn.execute("SELECT * FROM documents").fetchall()
    scored: list[tuple[int, sqlite3.Row]] = []
    for row in rows:
        searchable = "\n".join(
            [
                str(row["path"] or ""),
                str(row["title"] or ""),
                str(row["authority_tier"] or ""),
                str(row["evidence_class"] or ""),
                str(row["route"] or ""),
                str(row["search_text"] or ""),
            ]
        ).lower()
        if require_all_terms and not all(term in searchable for term in terms):
            continue
        if not require_all_terms and not any(term in searchable for term in terms):
            continue
        score = _row_score(row, terms)
        scored.append((score, row))
    scored.sort(key=lambda item: (-item[0], str(item[1]["path"])))
    return [_row_to_dict(row, score) for score, row in scored[:limit]]


def get_documents(
    paths: Sequence[str],
    db_path: Path | str = DEFAULT_DB_PATH,
    *,
    repo: Path | str = ".",
) -> list[dict[str, object]]:
    repo_path = Path(repo).resolve()
    db = repo_path / db_path if not Path(db_path).is_absolute() else Path(db_path)
    if not paths:
        return []
    placeholders = ",".join("?" for _ in paths)
    with connect(db) as conn:
        rows = conn.execute(f"SELECT * FROM documents WHERE path IN ({placeholders})", list(paths)).fetchall()
    by_path = {str(row["path"]): row for row in rows}
    return [_row_to_dict(by_path[path], 0) for path in paths if path in by_path]


def catalog_stats(db_path: Path | str = DEFAULT_DB_PATH, *, repo: Path | str = ".") -> dict[str, object]:
    repo_path = Path(repo).resolve()
    db = repo_path / db_path if not Path(db_path).is_absolute() else Path(db_path)
    with connect(db) as conn:
        total = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        meta = {row["key"]: row["value"] for row in conn.execute("SELECT key, value FROM catalog_meta")}
        tiers = {
            row["authority_tier"]: row["count"]
            for row in conn.execute("SELECT authority_tier, COUNT(*) AS count FROM documents GROUP BY authority_tier")
        }
        statuses = {
            row["content_status"]: row["count"]
            for row in conn.execute("SELECT content_status, COUNT(*) AS count FROM documents GROUP BY content_status")
        }
    return {
        "total_documents": total,
        "meta": meta,
        "authority_tiers": tiers,
        "content_statuses": statuses,
        "freshness": catalog_freshness(db_path=db_path, repo=repo),
    }


def _snippet(text: str, max_chars: int = 800) -> str:
    normalized = "\n".join(line.rstrip() for line in text.splitlines())
    return normalized[:max_chars]


def _row_to_dict(row: sqlite3.Row, score: int) -> dict[str, object]:
    return {
        "path": row["path"],
        "abs_path": row["abs_path"],
        "title": row["title"],
        "score": score,
        "authority_tier": row["authority_tier"],
        "evidence_class": row["evidence_class"],
        "freshness": row["freshness"],
        "doc_type": row["doc_type"],
        "route": row["route"],
        "size_bytes": row["size_bytes"],
        "sha256": row["sha256"],
        "content_status": row["content_status"],
        "snippet": _snippet(str(row["search_text"] or "")),
    }
