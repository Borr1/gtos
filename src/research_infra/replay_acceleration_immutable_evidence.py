"""Fail-closed primitives for immutable replay authority artifacts."""

from __future__ import annotations

import errno
import hashlib
import os
import secrets
import stat
from dataclasses import dataclass
from pathlib import Path


class ImmutableEvidenceError(RuntimeError):
    pass


@dataclass(frozen=True)
class RegularFileIdentity:
    device: int
    inode: int
    size: int
    mtime_ns: int
    ctime_ns: int
    link_count: int


def lexical_path(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _identity(state: os.stat_result) -> RegularFileIdentity:
    return RegularFileIdentity(
        device=state.st_dev,
        inode=state.st_ino,
        size=state.st_size,
        mtime_ns=state.st_mtime_ns,
        ctime_ns=state.st_ctime_ns,
        link_count=state.st_nlink,
    )


def _open_directory_chain(path: Path, *, code: str) -> int:
    lexical = lexical_path(path)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    descriptor = -1
    try:
        descriptor = os.open(lexical.anchor, flags)
        for component in lexical.parts[1:]:
            next_descriptor = os.open(
                component,
                flags | nofollow,
                dir_fd=descriptor,
            )
            opened = os.fstat(next_descriptor)
            if not stat.S_ISDIR(opened.st_mode):
                os.close(next_descriptor)
                raise ImmutableEvidenceError(code)
            os.close(descriptor)
            descriptor = next_descriptor
        opened = os.fstat(descriptor)
        if opened.st_uid != os.getuid():
            raise ImmutableEvidenceError(code)
        return descriptor
    except (OSError, ImmutableEvidenceError):
        if descriptor >= 0:
            os.close(descriptor)
        raise ImmutableEvidenceError(code) from None


def open_regular_nofollow(
    path: Path,
    *,
    code: str,
) -> tuple[int, RegularFileIdentity]:
    lexical = lexical_path(path)
    parent_descriptor = _open_directory_chain(lexical.parent, code=code)
    try:
        descriptor = os.open(
            lexical.name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_descriptor,
        )
    except OSError:
        os.close(parent_descriptor)
        raise ImmutableEvidenceError(code) from None
    os.close(parent_descriptor)
    opened = os.fstat(descriptor)
    if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
        os.close(descriptor)
        raise ImmutableEvidenceError(code)
    return descriptor, _identity(opened)


def read_regular_nofollow(
    path: Path,
    *,
    code: str,
) -> tuple[bytes, RegularFileIdentity]:
    descriptor, opened = open_regular_nofollow(path, code=code)
    try:
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        completed = _identity(os.fstat(descriptor))
        if completed != opened:
            raise ImmutableEvidenceError(code)
        return b"".join(chunks), opened
    finally:
        os.close(descriptor)


def assert_regular_identity(
    path: Path,
    expected: RegularFileIdentity,
    *,
    code: str,
) -> None:
    descriptor, observed = open_regular_nofollow(path, code=code)
    os.close(descriptor)
    if observed != expected:
        raise ImmutableEvidenceError(code)


def immutable_write_bytes(path: Path, payload: bytes, *, code: str) -> None:
    """Publish new bytes atomically without ever replacing a destination."""

    lexical = lexical_path(path)
    if lexical.name in {"", ".", ".."}:
        raise ImmutableEvidenceError(code)
    parent_descriptor = _open_directory_chain(lexical.parent, code=code)
    temporary_name = f".{lexical.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
    descriptor = -1
    linked = False
    try:
        try:
            os.stat(
                lexical.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            pass
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise ImmutableEvidenceError(code) from None
        else:
            raise ImmutableEvidenceError(code)
        descriptor = os.open(
            temporary_name,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=parent_descriptor,
        )
        view = memoryview(payload)
        offset = 0
        while offset < len(view):
            written = os.write(descriptor, view[offset:])
            if written <= 0:
                raise ImmutableEvidenceError(code)
            offset += written
        os.fsync(descriptor)
        temporary_state = os.fstat(descriptor)
        if (
            not stat.S_ISREG(temporary_state.st_mode)
            or temporary_state.st_nlink != 1
            or temporary_state.st_size != len(payload)
        ):
            raise ImmutableEvidenceError(code)
        os.close(descriptor)
        descriptor = -1
        try:
            os.link(
                temporary_name,
                lexical.name,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except OSError:
            raise ImmutableEvidenceError(code) from None
        linked = True
        os.unlink(temporary_name, dir_fd=parent_descriptor)
        os.fsync(parent_descriptor)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if not linked:
            try:
                os.unlink(temporary_name, dir_fd=parent_descriptor)
            except FileNotFoundError:
                pass
        os.close(parent_descriptor)
    observed, identity = read_regular_nofollow(lexical, code=code)
    if observed != payload or hashlib.sha256(observed).digest() != hashlib.sha256(
        payload
    ).digest() or identity.link_count != 1:
        raise ImmutableEvidenceError(code)
