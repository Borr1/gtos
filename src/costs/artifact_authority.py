"""Runtime verification for compact Wave-21 cost input artifacts.

The manifest is an authority only when the runtime actually checks it.  This module
keeps that check in one place and deliberately verifies the current bytes *before*
returning anything that a parser cache may retain.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath

__all__ = [
    "COST_INPUTS_MANIFEST_SCHEMA",
    "DEFAULT_COST_INPUTS_MANIFEST",
    "CostInputAuthorityError",
    "CurrentFileBytes",
    "VerifiedCostInput",
    "read_current_file_bytes",
    "verify_cost_input",
]

REPO = Path(__file__).resolve().parents[2]
DEFAULT_COST_INPUTS_MANIFEST = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase21/cost/"
    "COST_INPUTS_MANIFEST_V1.json"
)
COST_INPUTS_MANIFEST_SCHEMA = "gtos.phase21.cost_inputs_manifest.v1"
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class CostInputAuthorityError(RuntimeError):
    """A compact input cannot be tied to its repository-contained manifest row."""


@dataclass(frozen=True)
class CurrentFileBytes:
    path: Path
    sha256: str
    data: bytes


@dataclass(frozen=True)
class VerifiedCostInput:
    key: str
    path: Path
    sha256: str
    data: bytes
    manifest_path: Path
    manifest_sha256: str
    manifest: dict


def _fingerprint(path: Path) -> tuple[int, int, int, int, int]:
    stat = path.stat()
    return (
        int(stat.st_dev),
        int(stat.st_ino),
        int(stat.st_size),
        int(stat.st_mtime_ns),
        int(stat.st_ctime_ns),
    )


@lru_cache(maxsize=32)
def _read_fingerprinted(
    path_str: str, fingerprint: tuple[int, int, int, int, int]
) -> tuple[bytes, str]:
    path = Path(path_str)
    if _fingerprint(path) != fingerprint:
        raise CostInputAuthorityError(
            f"authority file changed before verified read: {path}; NOT_EVALUABLE"
        )
    data = path.read_bytes()
    if _fingerprint(path) != fingerprint:
        raise CostInputAuthorityError(
            f"authority file changed during verified read: {path}; NOT_EVALUABLE"
        )
    return data, hashlib.sha256(data).hexdigest()


def read_current_file_bytes(path: Path | str, *, label: str) -> CurrentFileBytes:
    """Read/hash with a cache keyed by identity, size, mtime and ctime.

    The key is deliberately not a pathname.  Any ordinary in-place edit, replacement,
    symlink target change or size change produces a new key and therefore a new byte/hash
    read.  The before/after checks also refuse a file that moves during the read.
    """

    candidate = Path(path)
    try:
        resolved = candidate.resolve(strict=True)
        fp = _fingerprint(resolved)
        data, digest = _read_fingerprinted(str(resolved), fp)
    except CostInputAuthorityError:
        raise
    except (FileNotFoundError, OSError) as exc:
        raise CostInputAuthorityError(f"{label} missing or unreadable at {candidate}") from exc
    return CurrentFileBytes(path=resolved, sha256=digest, data=data)


def _contained(path: Path, root: Path, *, label: str, must_exist: bool = True) -> Path:
    try:
        resolved = path.resolve(strict=must_exist)
    except (FileNotFoundError, OSError) as exc:
        raise CostInputAuthorityError(f"{label} missing at {path}; NOT_EVALUABLE") from exc
    try:
        resolved.relative_to(root)
    except ValueError:
        raise CostInputAuthorityError(
            f"{label} escapes cost authority root {root}: {resolved}; NOT_EVALUABLE"
        ) from None
    return resolved


def _relative_binding(value: object, *, key: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise CostInputAuthorityError(
            f"cost input manifest output {key!r} has no non-empty relative path"
        )
    # Treat the manifest as platform-independent data.  Backslashes could become
    # separators on another runtime, so accepting them on POSIX would make containment
    # depend on the host that performs the check.
    if "\\" in value:
        raise CostInputAuthorityError(
            f"cost input manifest output {key!r} uses a non-portable path {value!r}"
        )
    rel = PurePosixPath(value)
    if rel.is_absolute() or not rel.parts or any(part in {"", ".", ".."} for part in rel.parts):
        raise CostInputAuthorityError(
            f"cost input manifest output {key!r} is not a contained normalized relative path: "
            f"{value!r}"
        )
    return rel


def verify_cost_input(
    key: str,
    *,
    path: Path | str | None = None,
    manifest_path: Path | str | None = None,
    authority_root: Path | str | None = None,
) -> VerifiedCostInput:
    """Return current bytes only after manifest schema/path/hash verification.

    ``path`` is not an override: when supplied it must resolve to the exact path named
    by the manifest.  Tests and offline consumers may inject a different manifest and
    root explicitly; production defaults remain repository-bound.
    """

    root = Path(authority_root or REPO).resolve(strict=True)
    manifest_candidate = Path(manifest_path or DEFAULT_COST_INPUTS_MANIFEST)
    manifest_resolved = _contained(manifest_candidate, root, label="cost input manifest")
    try:
        manifest_file = read_current_file_bytes(
            manifest_resolved, label="cost input manifest"
        )
        manifest = json.loads(manifest_file.data)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        raise CostInputAuthorityError(
            f"cost input manifest is not valid JSON at {manifest_resolved}; NOT_EVALUABLE"
        ) from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != COST_INPUTS_MANIFEST_SCHEMA:
        got = manifest.get("schema") if isinstance(manifest, dict) else type(manifest).__name__
        raise CostInputAuthorityError(
            f"unsupported cost input manifest schema {got!r}; expected "
            f"{COST_INPUTS_MANIFEST_SCHEMA!r}"
        )
    outputs = manifest.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        raise CostInputAuthorityError("cost input manifest has no outputs mapping")

    validated: dict[str, tuple[Path, str]] = {}
    seen_paths: set[Path] = set()
    for output_key, binding in outputs.items():
        if not isinstance(output_key, str) or not isinstance(binding, dict):
            raise CostInputAuthorityError("cost input manifest contains a malformed output row")
        rel = _relative_binding(binding.get("path"), key=output_key)
        expected_sha = binding.get("sha256")
        if not isinstance(expected_sha, str) or _SHA256_RE.fullmatch(expected_sha) is None:
            raise CostInputAuthorityError(
                f"cost input manifest output {output_key!r} has invalid sha256 "
                f"{expected_sha!r}"
            )
        # Validate every declared row's containment, but do not make one selected
        # component depend on unrelated outputs being materialised.  The selected row
        # is resolved strictly immediately below.
        resolved = _contained(
            root.joinpath(*rel.parts),
            root,
            label=f"cost input {output_key}",
            must_exist=False,
        )
        if resolved in seen_paths:
            raise CostInputAuthorityError(
                f"cost input manifest binds multiple output keys to {resolved}"
            )
        seen_paths.add(resolved)
        validated[output_key] = (resolved, expected_sha)

    if key not in validated:
        raise CostInputAuthorityError(f"cost input manifest has no output row {key!r}")
    bound_path, expected_sha = validated[key]
    bound_path = _contained(bound_path, root, label=f"cost input {key}")
    if path is not None:
        supplied = _contained(Path(path), root, label=f"supplied cost input {key}")
        if supplied != bound_path:
            raise CostInputAuthorityError(
                f"supplied cost input path {supplied} does not equal manifest-bound path "
                f"{bound_path}; NOT_EVALUABLE"
            )
    current = read_current_file_bytes(bound_path, label=f"manifest-bound cost input {key}")
    data = current.data
    actual_sha = current.sha256
    if actual_sha != expected_sha:
        raise CostInputAuthorityError(
            f"cost input {key!r} hash mismatch at {bound_path}: manifest binds "
            f"{expected_sha}, current bytes are {actual_sha}; NOT_EVALUABLE"
        )
    return VerifiedCostInput(
        key=key,
        path=bound_path,
        sha256=actual_sha,
        data=data,
        manifest_path=manifest_resolved,
        manifest_sha256=manifest_file.sha256,
        manifest=manifest,
    )
