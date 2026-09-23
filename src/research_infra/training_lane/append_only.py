"""Append-only JSONL and atomic JSON, shared by all three lane artifacts.

One implementation, three consumers (iteration ledger, graduation ledger, incubation
registry), so the durability story is stated once and cannot drift between them.

WHY THIS IS NOT `trial_budget_ledger.TrialLedger._append`
---------------------------------------------------------
Same append discipline, opposite failure policy, and the difference is deliberate.

`TrialLedger` swallows write errors on purpose — its own docstring says a ledger that raises
"would become a brake", and the wave-6 agreement forbids it braking a measurement. That is
right for a ledger whose only job is to count.

This ledger is a **provenance chain**: `graduation.graduate()` reads it and refuses a candidate
with no rows. A silently-lost row here is a graduation that fails hours later with a refusal
nobody can explain, so the default is `strict=True` and a write error raises at the point of
loss. `strict=False` is available for a caller that genuinely wants the counting-only
behaviour, and it counts the loss in `write_errors` rather than hiding it.

Reusing `_append` would have meant reusing the policy too, and the private-name access would
have coupled two artifacts that must never share a path or a schema.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable

__all__ = ["append_row", "atomic_write_json", "read_rows", "AppendError"]


class AppendError(OSError):
    """A row could not be durably appended. Raised only when `strict` is true."""


#: A sanity ceiling on one row, not an atomicity boundary. Several sessions share these ledger
#: paths from separate worktrees; a row that carries a whole artifact inline is both a tearing
#: risk and a sign the artifact wants a `receipt` path instead.
MAX_ROW_BYTES = 64 * 1024


def append_row(path: str | Path, row: dict, *, strict: bool = True) -> bool:
    """Append one JSON object as one line. Returns True iff it was durably written.

    `O_APPEND` plus exactly ONE `os.write` per row. The guarantee that matters here is POSIX's
    `O_APPEND`: the seek-to-end and the write are a single atomic step with respect to other
    writers, so concurrent sessions sharing a ledger path cannot interleave and no locking is
    needed.

    **A short write is checked, not assumed away.** `trial_budget_ledger._append` cites
    `PIPE_BUF` for this, which is the guarantee for *pipes*; for a regular file the honest
    statement is that a single `write()` may in principle return short, and retrying the tail
    is exactly what would tear the row. So the return count is compared against the payload and
    a short write RAISES rather than being completed — the caller learns the row is torn
    instead of the file quietly containing half of it.
    """
    line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
    blob = line.encode("utf-8")
    if len(blob) > MAX_ROW_BYTES:
        raise AppendError(
            f"row is {len(blob)} bytes, above the {MAX_ROW_BYTES}-byte per-row ceiling. Move "
            f"the bulk into a sidecar artifact and reference it by path — that is what the "
            f"`receipt` fields on these rows are for."
        )
    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            written = os.write(fd, blob)
        finally:
            os.close(fd)
        if written != len(blob):
            raise AppendError(
                f"short append to {p}: {written} of {len(blob)} bytes. The row is TORN. Not "
                f"retrying the tail — a second write would append it after whatever another "
                f"session wrote in between and corrupt both rows."
            )
        return True
    except OSError as exc:
        if strict:
            raise AppendError(f"could not append to {p}: {exc}") from exc
        return False


def read_rows(path: str | Path) -> list[dict]:
    """Every parseable row, in file order. A torn line is preserved as `{"_unparseable": ...}`
    rather than dropped: a reader counting looks must be able to see that something was lost."""
    p = Path(path)
    if not p.is_file():
        return []
    out: list[dict] = []
    with p.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                out.append({"_unparseable": line[:200]})
                continue
            out.append(obj if isinstance(obj, dict) else {"_unparseable": line[:200]})
    return out


def atomic_write_json(path: str | Path, obj: Any, *, indent: int = 1) -> Path:
    """Write JSON via a temp file in the SAME directory plus `os.replace`.

    Same directory because `os.replace` is only atomic within a filesystem. The graduation
    biller uses this for the new family declaration, which is the point at which a look is
    billed: a half-written declaration would be a family whose size nobody can read, and
    `load_candidate_family` fails closed on unreadable JSON, so the whole estate's billing
    would stop. Either the old declaration or the new one is on disk, never a prefix of one.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=f".{p.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=indent, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, p)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return p


def rows_matching(path: str | Path, **equals: Any) -> list[dict]:
    """Rows whose fields all equal the given values. Convenience for provenance lookup."""
    return [
        r for r in read_rows(path)
        if "_unparseable" not in r and all(r.get(k) == v for k, v in equals.items())
    ]


def count_unparseable(rows: Iterable[dict]) -> int:
    return sum(1 for r in rows if "_unparseable" in r)
