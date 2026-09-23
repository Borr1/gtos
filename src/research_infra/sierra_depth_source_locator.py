"""Locate local Sierra Chart ``.depth`` source files for research routes.

This module is read-only research infrastructure. It never opens Sierra Chart,
never contacts a broker/vendor, and never mutates source directories. The
scanner is deterministic and cursor-aware so large local roots can be resumed
between route runs without materializing a full tree listing.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

DEFAULT_DEPTH_ROOTS: tuple[Path, ...] = (
    Path("C:/SierraChart/Data/MarketDepthData"),
    Path("C:/SierraChart/Data"),
    Path("data/sierrachart_exports"),
    Path("research/sierrachart_data_source_research_2026-05-02"),
)

CLASS_EXACT = "exact"
CLASS_NEAR = "near"
CLASS_DELAYED = "delayed"
CLASS_NO_LOCAL = "no_local"
CLASS_PERMISSION = "permission"

_DEPTH_FILENAME_RE = re.compile(
    r"^(?P<symbol>.+?)[._](?P<date>\d{4}-?\d{2}-?\d{2})(?P<suffix>[^\\/]*)\.depth$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SierraDepthFilename:
    """Normalized parts from a Sierra ``.depth`` filename."""

    original_name: str
    source_symbol: str
    source_date: str
    suffix: str = ""

    @property
    def normalized_filename(self) -> str:
        return f"{self.source_symbol}.{self.source_date}{self.suffix}.depth"

    @property
    def is_delayed(self) -> bool:
        return "delayed" in self.suffix.lower()

    def as_dict(self) -> dict[str, object]:
        return asdict(self) | {
            "normalized_filename": self.normalized_filename,
            "is_delayed": self.is_delayed,
        }


@dataclass(frozen=True)
class SierraDepthMatch:
    """A located local depth file plus immutable source metadata."""

    classification: str
    path: str
    filename: SierraDepthFilename
    size_bytes: int
    mtime_utc: str
    sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "classification": self.classification,
            "path": self.path,
            "filename": self.filename.as_dict(),
            "size_bytes": self.size_bytes,
            "mtime_utc": self.mtime_utc,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class SierraDepthScanError:
    """A non-fatal scan or metadata access error."""

    path: str
    error_type: str
    message: str

    @property
    def is_permission(self) -> bool:
        return self.error_type in {"PermissionError", "PermissionDenied"}

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SierraDepthScanEvent:
    """One scanner event: either a file path or a recoverable error."""

    path: Path | None = None
    error: SierraDepthScanError | None = None


@dataclass(frozen=True)
class SierraDepthLocatorResult:
    """Result for one requested Sierra source symbol/date."""

    requested_source_symbol: str
    requested_source_date: str
    expected_filename: str
    classification: str
    roots: tuple[str, ...]
    exact_matches: tuple[SierraDepthMatch, ...] = ()
    delayed_matches: tuple[SierraDepthMatch, ...] = ()
    near_matches: tuple[SierraDepthMatch, ...] = ()
    permission_errors: tuple[SierraDepthScanError, ...] = ()
    other_errors: tuple[SierraDepthScanError, ...] = ()
    files_seen: int = 0
    candidate_files_seen: int = 0
    scan_complete: bool = True
    resume_after: str | None = None

    @property
    def matches(self) -> tuple[SierraDepthMatch, ...]:
        return self.exact_matches + self.delayed_matches + self.near_matches

    def as_dict(self) -> dict[str, object]:
        return {
            "requested_source_symbol": self.requested_source_symbol,
            "requested_source_date": self.requested_source_date,
            "expected_filename": self.expected_filename,
            "classification": self.classification,
            "roots": list(self.roots),
            "exact_matches": [row.as_dict() for row in self.exact_matches],
            "delayed_matches": [row.as_dict() for row in self.delayed_matches],
            "near_matches": [row.as_dict() for row in self.near_matches],
            "permission_errors": [row.as_dict() for row in self.permission_errors],
            "other_errors": [row.as_dict() for row in self.other_errors],
            "files_seen": self.files_seen,
            "candidate_files_seen": self.candidate_files_seen,
            "scan_complete": self.scan_complete,
            "resume_after": self.resume_after,
        }


@dataclass
class _Accumulator:
    exact: list[SierraDepthMatch] = field(default_factory=list)
    delayed: list[SierraDepthMatch] = field(default_factory=list)
    near: list[SierraDepthMatch] = field(default_factory=list)
    permission_errors: list[SierraDepthScanError] = field(default_factory=list)
    other_errors: list[SierraDepthScanError] = field(default_factory=list)
    files_seen: int = 0
    candidate_files_seen: int = 0
    scan_complete: bool = True
    resume_after: str | None = None


def normalize_source_symbol(source_symbol: str) -> str:
    """Return a stable comparison form for Sierra contract/source symbols."""

    return str(source_symbol or "").strip().upper()


def normalize_source_date(value: str | date | datetime) -> str:
    """Normalize date-like values to ``YYYY-MM-DD``."""

    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    raw = str(value or "").strip()
    if re.fullmatch(r"\d{8}", raw):
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    parsed = date.fromisoformat(raw)
    return parsed.isoformat()


def normalize_sierra_depth_filename(path_or_name: str | Path) -> SierraDepthFilename | None:
    """Parse and normalize a Sierra ``.depth`` filename.

    Accepted source-date separators are ``.`` and ``_``. Dates may be
    ``YYYY-MM-DD`` or ``YYYYMMDD``. Extra text after the date is preserved as a
    suffix so delayed/suffixed files are visible instead of silently treated as
    exact source truth.
    """

    name = Path(path_or_name).name
    match = _DEPTH_FILENAME_RE.match(name)
    if not match:
        return None
    try:
        source_date = normalize_source_date(match.group("date"))
    except ValueError:
        return None
    return SierraDepthFilename(
        original_name=name,
        source_symbol=normalize_source_symbol(match.group("symbol")),
        source_date=source_date,
        suffix=match.group("suffix") or "",
    )


def expected_depth_filename(source_symbol: str, source_date: str | date | datetime) -> str:
    """Return the normalized exact Sierra source filename for a request."""

    return f"{normalize_source_symbol(source_symbol)}.{normalize_source_date(source_date)}.depth"


def iter_sierra_depth_files(
    roots: Iterable[str | Path] = DEFAULT_DEPTH_ROOTS,
    *,
    resume_after: str | Path | None = None,
) -> Iterator[SierraDepthScanEvent]:
    """Stream ``.depth`` files from roots in deterministic DFS order.

    ``resume_after`` is a path cursor returned by ``locate_sierra_depth_source``.
    It skips files whose normalized path key is less than or equal to the
    cursor. Directory-level permission errors are yielded and scanning
    continues through remaining roots.
    """

    cursor = _path_key(resume_after) if resume_after is not None else None
    for root in sorted((Path(item) for item in roots), key=_path_key):
        yield from _walk_depth_root(root, cursor)


def locate_sierra_depth_source(
    source_symbol: str,
    source_date: str | date | datetime,
    *,
    roots: Iterable[str | Path] = DEFAULT_DEPTH_ROOTS,
    resume_after: str | Path | None = None,
    max_scan_entries: int | None = None,
) -> SierraDepthLocatorResult:
    """Locate exact, delayed, and near local Sierra depth files.

    The helper hashes only files that match the requested symbol/date family.
    If ``max_scan_entries`` is set, the scan stops after that many ``.depth``
    files and returns a cursor in ``resume_after`` for continuation.
    """

    requested_symbol = normalize_source_symbol(source_symbol)
    requested_date = normalize_source_date(source_date)
    root_tuple = tuple(str(Path(item)) for item in roots)
    acc = _Accumulator()

    for event in iter_sierra_depth_files(root_tuple, resume_after=resume_after):
        if event.error is not None:
            _append_error(acc, event.error)
            continue
        if event.path is None:
            continue

        acc.files_seen += 1
        acc.resume_after = str(event.path)
        should_stop = max_scan_entries is not None and acc.files_seen >= max_scan_entries
        parts = normalize_sierra_depth_filename(event.path)
        if parts is None:
            if should_stop:
                acc.scan_complete = False
                break
            continue
        match_class = _classify_parts(parts, requested_symbol, requested_date)
        if match_class is None:
            if should_stop:
                acc.scan_complete = False
                break
            continue
        acc.candidate_files_seen += 1
        match, error = _build_match(event.path, parts, match_class)
        if error is not None:
            _append_error(acc, error)
        elif match_class == CLASS_EXACT:
            acc.exact.append(match)
        elif match_class == CLASS_DELAYED:
            acc.delayed.append(match)
        elif match_class == CLASS_NEAR:
            acc.near.append(match)

        if should_stop:
            acc.scan_complete = False
            break

    classification = _result_classification(acc)
    return SierraDepthLocatorResult(
        requested_source_symbol=requested_symbol,
        requested_source_date=requested_date,
        expected_filename=expected_depth_filename(requested_symbol, requested_date),
        classification=classification,
        roots=root_tuple,
        exact_matches=tuple(acc.exact),
        delayed_matches=tuple(acc.delayed),
        near_matches=tuple(acc.near),
        permission_errors=tuple(acc.permission_errors),
        other_errors=tuple(acc.other_errors),
        files_seen=acc.files_seen,
        candidate_files_seen=acc.candidate_files_seen,
        scan_complete=acc.scan_complete,
        resume_after=acc.resume_after,
    )


def _classify_parts(parts: SierraDepthFilename, requested_symbol: str, requested_date: str) -> str | None:
    if parts.source_symbol != requested_symbol or parts.source_date != requested_date:
        return None
    if not parts.suffix:
        return CLASS_EXACT
    if parts.is_delayed:
        return CLASS_DELAYED
    return CLASS_NEAR


def _result_classification(acc: _Accumulator) -> str:
    if acc.exact:
        return CLASS_EXACT
    if acc.delayed:
        return CLASS_DELAYED
    if acc.near:
        return CLASS_NEAR
    if acc.permission_errors:
        return CLASS_PERMISSION
    return CLASS_NO_LOCAL


def _walk_depth_root(root: Path, cursor: str | None) -> Iterator[SierraDepthScanEvent]:
    try:
        if not root.exists():
            return
        root_is_file = root.is_file()
    except OSError as exc:
        yield SierraDepthScanEvent(error=_scan_error(root, exc))
        return
    if root_is_file:
        if root.suffix.lower() == ".depth" and _path_key(root) > (cursor or ""):
            yield SierraDepthScanEvent(path=root)
        return

    stack = [root]
    while stack:
        current = stack.pop()
        try:
            current_is_file = current.is_file()
        except OSError as exc:
            yield SierraDepthScanEvent(error=_scan_error(current, exc))
            continue
        if current_is_file:
            if current.suffix.lower() == ".depth" and _path_key(current) > (cursor or ""):
                yield SierraDepthScanEvent(path=current)
            continue
        try:
            children = sorted(_scandir_children(current), key=lambda item: item[0])
        except OSError as exc:
            yield SierraDepthScanEvent(error=_scan_error(current, exc))
            continue
        for _, child, _, _ in reversed(children):
            stack.append(child)


def _scandir_children(path: Path) -> list[tuple[str, Path, bool, bool]]:
    children: list[tuple[str, Path, bool, bool]] = []
    with os.scandir(path) as entries:
        for entry in entries:
            child = Path(entry.path)
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
                is_file = entry.is_file(follow_symlinks=False)
            except OSError:
                continue
            is_depth_file = is_file and child.suffix.lower() == ".depth"
            if is_dir or is_depth_file:
                children.append((_path_key(child), child, is_dir, is_depth_file))
    return children


def _build_match(
    path: Path,
    filename: SierraDepthFilename,
    classification: str,
) -> tuple[SierraDepthMatch | None, SierraDepthScanError | None]:
    try:
        stat = path.stat()
        return (
            SierraDepthMatch(
                classification=classification,
                path=str(path),
                filename=filename,
                size_bytes=stat.st_size,
                mtime_utc=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                sha256=_sha256(path),
            ),
            None,
        )
    except OSError as exc:
        return None, _scan_error(path, exc)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _append_error(acc: _Accumulator, error: SierraDepthScanError) -> None:
    if error.is_permission:
        acc.permission_errors.append(error)
    else:
        acc.other_errors.append(error)


def _scan_error(path: Path, exc: OSError) -> SierraDepthScanError:
    return SierraDepthScanError(
        path=str(path),
        error_type=exc.__class__.__name__,
        message=str(exc),
    )


def _path_key(path: str | Path | None) -> str:
    if path is None:
        return ""
    return str(Path(path)).replace("\\", "/").casefold()
