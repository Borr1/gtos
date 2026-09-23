"""Differential harness: *where* do two replay arm outputs differ?

Phase 2 of ``FULL_VISION_PLAN.md`` rebuilds the replay around one policy-plural
decision core.  Every parity claim about that rebuild is an assertion until
something can take two arm outputs and say *these differ at row X, field Y* --
or prove that they do not.  This module is that something.

**It is a driver, not a new comparison semantics.**  That distinction is the
whole design.  The difference engine, the volatility allowlist, the value-class
rules and the runtime-hash preimage validation are imported *unchanged* from
:mod:`src.research_infra.replay_acceleration_task2_semantic_acceptance`
(``task2`` below), whose ``compare_role_rows`` has been the acceptance
comparator since Task 2 closed.  Redesigning those rules here would destroy the
comparability that makes a differential harness worth having, so this module
adds exactly four things ``task2`` does not have:

1. **Arm resolution that is not bound to one worktree or one arm.**  ``task2``'s
   ``PREFIX`` (``task2:31-34``) is a module constant naming the ``S0R0`` arm, and
   ``_role_path`` (``task2:2375-2376``) builds every ledger path from it, so it
   can address exactly one of the four sealed January arms.  :class:`ArmOutputs`
   discovers the prefix from the directory on disk instead.  Hazard H4 says
   sealed authority binds absolute paths; a comparator that only works in one
   directory is half a comparator, so nothing here resolves an arm against a
   repo root.

2. **Reading the cold archives.**  Three roles -- ``decision``, ``scorecard``
   and ``missed`` -- exist on the sealed arms only as ``*.jsonl.cold/`` zstd
   shard directories.  ``task2._role_rows`` (``task2:2395-2400``) routes to an
   archive only when a *zero-byte* flat ``.jsonl`` exists alongside a
   ``streaming-proof-archive/CAMPAIGN_ARCHIVE_MANIFEST.json``; on the sealed
   arms neither is true, so it raises ``FileNotFoundError``.  We resolve
   raw-or-cold through ``b7_5_cold_evidence.RawOrColdResolver``, the reader for
   the format the sealed arms actually use.  It is unbound by either decision
   contract and streams through the ``zstd`` binary.

3. **Enumerating differences instead of raising on the first one.**
   ``compare_role_rows`` raises ``SemanticAcceptanceError`` the moment it meets
   an unclassified path (``task2:962-967``).  That is right for an acceptance
   gate and useless for localisation.  Here every difference is accumulated and
   reported, using ``task2._difference_paths``, ``task2._entry_for_path`` and
   ``task2._validate_runtime_hash_preimages`` so the *classification* is
   literally the same code.  **Every condition on which ``task2`` raises maps to
   an ``UNKNOWN`` finding here** -- that equivalence is the correctness property
   of this module, and `tests/test_replay_differential_harness.py` pins it by
   running both comparators over the same fixtures.

4. **Identity alignment.**  ``compare_role_rows`` zips positionally
   (``task2:943-948``) and raises ``semantic_row_count_mismatch`` when the
   streams differ in length.  Positional is correct for its original purpose --
   the same arm re-run on a faster engine -- and it stays the default here.  But
   two *different* arms emit different row counts, so :func:`compare_arms` also
   offers alignment on a declared, runtime-verified identity key.

Fail-closed rules, which are the point of the thing
---------------------------------------------------

A comparator that never reports a difference is worse than none, so every path
that cannot establish equivalence must refuse to claim it:

* A difference with no allowlist entry is ``UNKNOWN``.  Mirrors ``task2:962-967``.
* For ``task2.EXACT_ROLES`` -- ``source``, ``decision``, ``bucket``,
  ``candidate`` -- *every* difference is ``UNKNOWN`` regardless of the
  allowlist.  Mirrors ``task2:958-959``.
* An allowlisted slot whose value is not a valid UTC timestamp or a valid
  SHA-256 is ``UNKNOWN``.  Mirrors ``task2:970-982``: you cannot smuggle an
  economic number through an allowlisted path.
* An allowlisted *hash* whose closure is not proven is ``UNKNOWN``.  Mirrors
  ``task2:1013-1021``.  "Proven" means what ``task2`` means: a self-proving
  local preimage, the ``risk_authority`` alias **with a Mapping actually present
  on both sides** (``task2:987-993``), or a supplied proof class.
* A row whose declared runtime hashes contradict their own preimages is
  ``UNKNOWN``, per ``task2._validate_runtime_hash_preimages``
  (``task2:862-902``, run at ``task2:951-952``).  Without this the allowlist
  would wave through exactly the defect a rebuilt engine is most likely to
  introduce -- a recomputed packet hash over slightly different material.
* A ``NaN`` anywhere is ``UNKNOWN`` **even when both sides carry one**.  Under
  the pre-``e5c7ce30a`` encoder ``b"NaN" == b"NaN"``, so two runs that both
  produced an undefined economic value compared equal; see
  ``replay_canonical_bytes``.  Reporting it is this module's version of that
  fix (it cannot simply refuse, see "Non-finite values" below).
* A role that cannot be read, or that yields **zero rows on both sides**, is
  ``UNAVAILABLE`` and the run is ``INCOMPLETE``.  Zero rows is the same
  "compared nothing" failure one level down, and it is reachable: a zero-byte
  flat ledger is this campaign's archive-demotion marker (``task2:2397``).
* A run that compared **zero roles** is ``INCOMPLETE``.
* Any per-role difference list that had to be **truncated** blocks
  ``EQUIVALENT`` for that role, and the cap is recorded in the receipt so
  ``differences_truncated`` is interpretable.

``EQUIVALENT`` therefore requires at least one role compared, every role
readable and non-empty, no unmatched rows, no truncation, and zero unknown
differences.  A proven ``DIFFER`` outranks ``INCOMPLETE``: once a difference is
established, saying "could not establish" would understate it.

Non-finite values
-----------------

``task2.canonical_bytes`` refuses non-finite floats (``allow_nan=False`` since
``e5c7ce30a``).  That is right for a *sealing* encoder and fatal for a *diff*:
``scorecard`` rows carry ``Infinity`` as a "no ceiling" sentinel -- measured in
26 of the first 40 rows of every sealed January arm -- so canonicalising them
raises and no report is produced at all.  ``replay_canonical_bytes``' claim that
a scan "found zero non-finite tokens" is true only of the five flat roles it
names; the cold roles were not scanned.

So the diff encoder here is *total*: non-finite floats are replaced by stable
markers before comparison, which makes ``inf == inf`` and lets the role be
compared.  ``NaN`` is additionally reported as ``UNKNOWN`` at its own path even
when both sides agree, and every non-finite leaf is counted in the receipt.
Nothing non-finite is ever hashed into an authority digest here.

Economic disclosure
-------------------

Differing *values* are reported as the SHA-256 of their canonical bytes by
default, so a receipt can be committed without exposing economic values --
the convention ``task2`` follows with ``economic_values_exposed`` in its own
receipt.  Pass ``expose_values=True`` (CLI ``--expose-values``) for interactive
debugging; the receipt then says so.

This module never writes to a broker, never imports MetaTrader5, and only ever
opens arm outputs for reading.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import zip_longest
from pathlib import Path
from typing import Any

from src.research_infra import (
    replay_acceleration_task2_semantic_acceptance as task2,
)

SCHEMA = "gtos.phase2.replay_differential_harness.v1"

#: Repo root of *this* module, used only to locate the cold-evidence reader.
#: Arm outputs are never resolved against it -- see H4.
_MODULE_ROOT = Path(__file__).resolve().parents[2]
_COLD_EVIDENCE_READER = _MODULE_ROOT / (
    "research/operations/"
    "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "b7_5_cold_evidence.py"
)

#: Marker for "this path is absent on this side".  ``_difference_paths`` reports
#: a path when a key exists on only one side (``task2:784-785``), and
#: ``task2._path_value`` would raise on the missing side.  It is a unique
#: object, not a string, so no row value can collide with it.
MISSING = object()

_NONFINITE_MARKERS = {
    "inf": "<NONFINITE:inf>",
    "-inf": "<NONFINITE:-inf>",
    "nan": "<NONFINITE:nan>",
}

#: Roles whose identity key has been *measured* unique across all four sealed
#: January arms.  A role absent here cannot use identity alignment unless the
#: caller declares a key; guessing one would be a silent correctness risk.
#:
#: ``order`` needs the lifecycle stage: each candidate instance emits an
#: ``accepted_pending`` row and a terminal row, so the instance key alone is
#: duplicated exactly once per candidate (measured 182 rows / 91 keys on S0R0).
ROLE_IDENTITY_KEYS: dict[str, tuple[str, ...]] = {
    "order": ("canonical_replay_candidate_instance_key", "order_event_stage"),
    "trade": ("canonical_replay_candidate_instance_key",),
    "oracle": ("canonical_replay_candidate_instance_key",),
}

CLASSIFICATION_ALLOWLISTED_CLOCK = "ALLOWLISTED_VOLATILE_CLOCK"
CLASSIFICATION_ALLOWLISTED_HASH = "ALLOWLISTED_DERIVED_HASH_PROVEN"
CLASSIFICATION_UNKNOWN = "UNKNOWN"

#: Classifications that do NOT block equivalence.  Everything else does.
_BENIGN_CLASSIFICATIONS = frozenset(
    {CLASSIFICATION_ALLOWLISTED_CLOCK, CLASSIFICATION_ALLOWLISTED_HASH}
)

STATUS_EQUIVALENT = "EQUIVALENT"
STATUS_DIFFER = "DIFFER"
STATUS_UNAVAILABLE = "UNAVAILABLE"

VERDICT_EQUIVALENT = "EQUIVALENT"
VERDICT_DIFFER = "DIFFER"
VERDICT_INCOMPLETE = "INCOMPLETE"

_PROVEN_CLOSURE_CLASSES = frozenset(
    {
        "PREIMAGE",
        "IDENTITY_ALIAS",
        "HISTORICAL_HASH_ONLY_NONCAUSAL",
        "TRANSITIVE_RUNTIME_ONLY_DERIVED_HASH",
    }
)

_ARM_ID_PATTERN = re.compile(r"_(S[01]R[01])_")


class DifferentialHarnessError(ValueError):
    """The harness could not establish what it was asked to establish."""


def _load_cold_evidence_reader() -> Any:
    """Import the unbound cold-archive reader from the B7.5 route.

    The route directory is not a package, so the repo's own convention is an
    ``importlib`` load under a distinct module name (see
    ``analyze_b7_5_selection_sizing_development_january.py:420-445``).  The name
    is distinct and set once; we never delete a module from ``sys.modules`` and
    re-import, which creates a second module object that ``multiprocessing``
    then refuses to pickle functions from.
    """

    module_name = "b7_5_cold_evidence_for_differential_harness"
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    if not _COLD_EVIDENCE_READER.is_file():
        raise DifferentialHarnessError(
            f"cold_evidence_reader_missing:{_COLD_EVIDENCE_READER}"
        )
    spec = importlib.util.spec_from_file_location(
        module_name, _COLD_EVIDENCE_READER
    )
    if spec is None or spec.loader is None:
        raise DifferentialHarnessError("cold_evidence_reader_import_spec_invalid")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    for required in ("RawOrColdResolver", "ColdEvidenceError"):
        if not hasattr(module, required):
            raise DifferentialHarnessError(
                f"cold_evidence_reader_contract_divergent:{required}"
            )
    return module


def sanitize_row(value: Any) -> tuple[Any, list[str], int]:
    """Return ``(diffable, nan_paths, nonfinite_count)``.

    Replaces non-finite floats with stable markers so the whole row can be
    canonicalised.  ``nan_paths`` are reported separately because two ``NaN``s
    must never be silently equal -- see the module docstring.
    """

    nan_paths: list[str] = []
    count = 0

    def walk(node: Any, path: str) -> Any:
        nonlocal count
        if isinstance(node, Mapping):
            return {str(k): walk(v, f"{path}/{k}") for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v, f"{path}/{i}") for i, v in enumerate(node)]
        if isinstance(node, float) and not math.isfinite(node):
            count += 1
            if math.isnan(node):
                nan_paths.append(path.lstrip("/"))
                return _NONFINITE_MARKERS["nan"]
            return _NONFINITE_MARKERS["inf" if node > 0 else "-inf"]
        return node

    return walk(value, ""), nan_paths, count


def _value_digest(value: Any) -> str | None:
    """Digest a reported value.

    Sanitised first: a differing leaf can itself be non-finite (``scorecard``
    carries ``Infinity`` sentinels), and hashing it raw would raise inside the
    reporting path -- turning a localised difference into a dead run.
    """

    if value is MISSING:
        return None
    diffable, _, _ = sanitize_row(value)
    return hashlib.sha256(task2.canonical_bytes(diffable)).hexdigest()


def _safe_path_value(row: Any, path: Sequence[str]) -> Any:
    """``task2._path_value`` but returning :data:`MISSING` instead of raising."""

    current: Any = row
    for key in path:
        if isinstance(current, Mapping):
            if key not in current:
                return MISSING
            current = current[key]
        elif isinstance(current, list):
            try:
                index = int(key)
            except ValueError:
                return MISSING
            if index >= len(current) or index < -len(current):
                return MISSING
            current = current[index]
        else:
            return MISSING
    return current


def _resolve_proof_class(
    proof: Any,
    *,
    left_row: Mapping[str, Any],
    right_row: Mapping[str, Any],
    role: str,
) -> Any:
    """Resolve a supplied proof entry, including ``task2``'s Mapping form.

    ``task2:999-1012`` allows a proof value to be a Mapping keyed by row
    identity, and requires both sides to agree on that identity.  Testing such a
    value for set membership raises ``TypeError``, so it is resolved first.
    """

    if not isinstance(proof, Mapping):
        return proof
    try:
        left_identity = task2._identity_key(left_row, label=f"{role}:left")
        right_identity = task2._identity_key(right_row, label=f"{role}:right")
    except task2.SemanticAcceptanceError:
        return None
    if left_identity != right_identity:
        return None
    return proof.get(left_identity)


def classify_difference(
    role: str,
    path: Sequence[str],
    left_value: Any,
    right_value: Any,
    *,
    left_row: Mapping[str, Any],
    right_row: Mapping[str, Any],
    derived_hash_proofs: Mapping[str, Any] | None = None,
) -> tuple[str, str]:
    """Classify one differing leaf path exactly as ``task2`` would.

    Returns ``(classification, reason)``.  Every branch on which ``task2`` would
    have raised maps to :data:`CLASSIFICATION_UNKNOWN`, so this is fail-closed by
    construction: a classification is benign only when ``task2`` would have
    normalised the path, *and* the value survived its class check, *and* -- for a
    hash -- its closure is proven against the rows themselves.
    """

    path = tuple(str(part) for part in path)

    # task2:958-959 -- the exact roles never consult the allowlist at all.
    if role in task2.EXACT_ROLES:
        return CLASSIFICATION_UNKNOWN, "exact_role_admits_no_normalization"

    entry = task2._entry_for_path(role, path)
    if entry is None:
        return CLASSIFICATION_UNKNOWN, "no_allowlist_entry"

    pattern = "/".join(entry["path"])

    # task2:970-977 -- an allowlisted clock slot must hold a real UTC stamp.
    if entry["value_class"] == "wall_clock_timestamp":
        if not task2._is_utc_timestamp(left_value) or not task2._is_utc_timestamp(
            right_value
        ):
            return CLASSIFICATION_UNKNOWN, "volatile_timestamp_invalid"
        return CLASSIFICATION_ALLOWLISTED_CLOCK, pattern

    # task2:979-982 -- an allowlisted hash slot must hold a real SHA-256.
    if not task2._is_sha256(left_value) or not task2._is_sha256(right_value):
        return CLASSIFICATION_UNKNOWN, "derived_hash_invalid"

    # task2:985-1021 -- and its closure must be proven.
    if pattern in task2._LOCAL_PREIMAGE_DERIVED_PATTERNS:
        return CLASSIFICATION_ALLOWLISTED_HASH, f"PREIMAGE:{pattern}"
    if (
        pattern == "risk_authority_packet_hash_sha256"
        and role in {"order", "trade"}
        # task2:990-991 -- the alias only proves anything when the nested packet
        # it aliases is actually present on both sides.
        and isinstance(left_row.get("risk_authority"), Mapping)
        and isinstance(right_row.get("risk_authority"), Mapping)
    ):
        return CLASSIFICATION_ALLOWLISTED_HASH, f"PREIMAGE:{pattern}"
    proof = (derived_hash_proofs or {}).get(
        f"{role}:{pattern}", (derived_hash_proofs or {}).get(pattern)
    )
    proof_class = _resolve_proof_class(
        proof, left_row=left_row, right_row=right_row, role=role
    )
    if proof_class in _PROVEN_CLOSURE_CLASSES:
        return CLASSIFICATION_ALLOWLISTED_HASH, f"{proof_class}:{pattern}"
    return CLASSIFICATION_UNKNOWN, f"derived_hash_closure_unproven:{pattern}"


@dataclass(frozen=True)
class RowDifference:
    """One differing leaf path in one aligned row pair."""

    role: str
    row_key: str
    left_index: int | None
    right_index: int | None
    path: tuple[str, ...]
    classification: str
    reason: str
    left_value_sha256: str | None
    right_value_sha256: str | None
    left_present: bool = True
    right_present: bool = True
    left_value: Any = None
    right_value: Any = None
    values_exposed: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "role": self.role,
            "row_key": self.row_key,
            "left_row_index": self.left_index,
            "right_row_index": self.right_index,
            "field_path": "/".join(self.path),
            "classification": self.classification,
            "reason": self.reason,
            "left_present": self.left_present,
            "right_present": self.right_present,
            "left_value_sha256": self.left_value_sha256,
            "right_value_sha256": self.right_value_sha256,
        }
        if self.values_exposed:
            payload["left_value"] = self.left_value if self.left_present else None
            payload["right_value"] = self.right_value if self.right_present else None
        return payload


class _DifferenceBuffer:
    """Bounded store that never drops an UNKNOWN in favour of a benign one.

    Counts are kept for *every* difference; only the retained detail list is
    capped.  Reporting a capped count as a total is how a receipt ends up saying
    ``unknown_difference_count: 0`` on a run that found two economic changes.
    """

    def __init__(self, cap: int) -> None:
        self.cap = max(0, int(cap))
        self.unknown_total = 0
        self.benign_total = 0
        self.truncated = False
        self._unknown: list[RowDifference] = []
        self._benign: list[RowDifference] = []

    def add(self, difference: RowDifference) -> None:
        unknown = difference.classification not in _BENIGN_CLASSIFICATIONS
        if unknown:
            self.unknown_total += 1
        else:
            self.benign_total += 1
        if len(self._unknown) + len(self._benign) < self.cap:
            (self._unknown if unknown else self._benign).append(difference)
            return
        if unknown and self._benign:
            # An unknown displaces a benign entry rather than being dropped.
            self._benign.pop()
            self._unknown.append(difference)
        self.truncated = True

    @property
    def total(self) -> int:
        return self.unknown_total + self.benign_total

    def as_list(self) -> list[dict[str, Any]]:
        return [d.as_dict() for d in (self._unknown + self._benign)]


class ArmOutputs:
    """One replay arm's output directory, addressable by role.

    Unlike ``task2._role_path`` this discovers the ledger prefix from the
    directory rather than carrying it as a module constant, and it resolves
    raw-or-cold rather than assuming a flat ``.jsonl``.  It performs no
    validation against any repo root, so an arm produced in another worktree is
    readable -- which is the whole point of not inheriting H4.
    """

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).expanduser().resolve()
        if not self.root.is_dir():
            raise DifferentialHarnessError(f"arm_root_not_a_directory:{self.root}")
        self.prefix = self._discover_prefix()
        self._reader = _load_cold_evidence_reader()
        self._resolver = None  # constructed lazily: zstd is only needed for cold

    def _discover_prefix(self) -> str:
        """Derive the shared ledger prefix from what is actually on disk.

        Every ledger in an arm is ``{PREFIX}_{ROLE_SUFFIX}``.  Candidates come
        from flat files and ``.cold`` directories, and must agree -- an arm
        directory holding two prefixes is ambiguous and we refuse it rather than
        pick one.  Dot-prefixed names are skipped: copying evidence to exFAT or
        SMB (the normal way an arm moves between this laptop and the VPS) leaves
        an AppleDouble ``._NAME`` sidecar beside every file, and counting those
        would make every relocated arm ambiguous.
        """

        prefixes: set[str] = set()
        for suffix in task2.ROLE_SUFFIXES.values():
            for candidate in self.root.glob(f"*_{suffix}"):
                if candidate.name.startswith("."):
                    continue
                prefixes.add(candidate.name[: -(len(suffix) + 1)])
            for candidate in self.root.glob(f"*_{suffix}.cold"):
                if candidate.name.startswith(".") or not candidate.is_dir():
                    continue
                prefixes.add(candidate.name[: -(len(suffix) + 6)])
        prefixes.discard("")
        if not prefixes:
            raise DifferentialHarnessError(f"arm_ledger_prefix_absent:{self.root}")
        if len(prefixes) > 1:
            raise DifferentialHarnessError(
                f"arm_ledger_prefix_ambiguous:{self.root}:{sorted(prefixes)}"
            )
        return prefixes.pop()

    @property
    def resolver(self) -> Any:
        if self._resolver is None:
            self._resolver = self._reader.RawOrColdResolver()
        return self._resolver

    @property
    def arm_id(self) -> str | None:
        match = _ARM_ID_PATTERN.search(self.prefix)
        return match.group(1) if match else None

    def logical_path(self, role: str) -> Path:
        if role not in task2.ROLE_SUFFIXES:
            raise DifferentialHarnessError(f"role_unknown:{role}")
        return self.root / f"{self.prefix}_{task2.ROLE_SUFFIXES[role]}"

    def storage_mode(self, role: str) -> str:
        """``raw``, ``cold``, ``zst``, ``archive_stub``, ``ambiguous`` or ``absent``.

        ``archive_stub`` is a zero-byte flat ledger for one of
        ``task2.ARCHIVE_ROLES`` with no archive beside it.  That shape is this
        campaign's demotion marker (``task2:2397`` routes exactly it to the
        streaming-proof archive), so reading the empty file and calling the role
        equivalent would be a false green on the largest surfaces.

        ``zst`` is a whole-file zstd ledger -- ``<ledger>.jsonl.zst`` rather than the
        sharded ``<ledger>.jsonl.cold/`` directory.  It was added 2026-08-12: the
        storage-reclamation pass compressed sealed arm ledgers in place (its own
        manifest records
        ``PHASE_D_JANUARY_S0R0_R2_.../..._ORDER_LEDGER.jsonl.zst``, 2,013,145 bytes),
        and until this branch existed such a role reported ``absent``.  That is the
        dangerous shape: sealed evidence that is present on disk, invisible to its own
        comparator, and degrading ``compare_arms`` to INCOMPLETE rather than to a
        refusal.  A compression must not be able to silence a ledger.
        """

        path = self.logical_path(role)
        cold = Path(str(path) + ".cold")
        zst = Path(str(path) + ".zst")
        raw_exists = path.exists() or path.is_symlink()
        cold_exists = cold.is_dir()
        zst_exists = zst.is_file()
        if sum((raw_exists, cold_exists, zst_exists)) > 1:
            return "ambiguous"
        if zst_exists:
            return "zst"
        if raw_exists:
            if (
                role in task2.ARCHIVE_ROLES
                and path.is_file()
                and path.stat().st_size == 0
            ):
                return "archive_stub"
            return "raw"
        if cold_exists:
            return "cold"
        return "absent"

    def available_roles(self) -> list[str]:
        return [
            role
            for role in task2.ROLE_SUFFIXES
            if self.storage_mode(role) in {"raw", "cold", "zst"}
        ]

    def iter_role_rows(
        self, role: str, *, end_day: str | None = None
    ) -> Iterator[dict[str, Any]]:
        """Stream one role's rows.  Two rows resident at a time, never a ledger.

        Memory is the binding constraint on this machine (H3), and the cold
        surfaces are 15.6 GB logical per arm, so nothing here materialises a
        ledger.  ``end_day`` reuses ``task2.rows_through``, which is how a
        day-bounded comparison is expressed -- the cheapest available answer to
        H5's "debugging one day costs a full arm".
        """

        path = self.logical_path(role)
        mode = self.storage_mode(role)
        if mode in {"absent", "archive_stub", "ambiguous"}:
            raise DifferentialHarnessError(f"role_evidence_{mode}:{role}:{path}")
        if mode == "zst":
            yield from self._iter_zst_rows(path, role=role, end_day=end_day)
            return
        handle = self.resolver.open_binary(path)
        try:
            rows = self._iter_json_lines(handle, role=role)
            if end_day is not None:
                rows = task2.rows_through(rows, end_day=end_day)
            yield from rows
        finally:
            handle.close()

    def _iter_zst_rows(
        self, path: Path, *, role: str, end_day: str | None
    ) -> Iterator[dict[str, Any]]:
        """Stream a whole-file ``.zst`` ledger, still two rows resident at a time.

        Decompressed through the `zstd` BINARY, which is what the cold reader beside it
        already does (`b7_5_cold_evidence._find_zstd`, resolved via `shutil.which`) -- no
        Python zstd binding is installed on this machine and adding one as a hard dependency
        for a reader that already has a working mechanism would be the wrong trade. Streamed,
        never materialised: these are ~2 MB compressed and hundreds of MB expanded, and H3
        makes memory the binding constraint here.
        """

        import subprocess

        archive = Path(str(path) + ".zst")
        zstd = self._reader._find_zstd()
        process = subprocess.Popen(
            [str(zstd), "-dc", "--", str(archive)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            rows = self._iter_json_lines(process.stdout, role=role)
            if end_day is not None:
                rows = task2.rows_through(rows, end_day=end_day)
            yield from rows
            # Only a fully consumed stream can be checked; a bounded read is a deliberate
            # early exit and the `finally` kills it.
            if process.stdout.read() == b"" and process.wait() != 0:
                raise DifferentialHarnessError(
                    f"zstd_decompress_failed:{role}:{archive}:"
                    f"{process.stderr.read().decode('utf-8', 'replace')[:200]}"
                )
        finally:
            if process.poll() is None:
                process.kill()
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
            process.wait()

    @staticmethod
    def _iter_json_lines(handle: Any, *, role: str) -> Iterator[dict[str, Any]]:
        for index, raw in enumerate(handle):
            if not raw.endswith(b"\n"):
                raise DifferentialHarnessError(
                    f"jsonl_framing_invalid:{role}:{index}"
                )
            try:
                row = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise DifferentialHarnessError(
                    f"jsonl_row_invalid:{role}:{index}"
                ) from None
            if not isinstance(row, dict):
                raise DifferentialHarnessError(f"jsonl_row_invalid:{role}:{index}")
            yield row

    def describe(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "prefix": self.prefix,
            "arm_id": self.arm_id,
            "role_storage": {
                role: self.storage_mode(role) for role in task2.ROLE_SUFFIXES
            },
        }


def _identity_of(row: Mapping[str, Any], fields: Sequence[str]) -> str:
    parts: list[str] = []
    for name in fields:
        value = row.get(name)
        if value is None:
            raise DifferentialHarnessError(f"identity_key_field_absent:{name}")
        text = str(value)
        if "\x1f" in text:
            raise DifferentialHarnessError(f"identity_key_field_separator:{name}")
        parts.append(text)
    return "\x1f".join(parts)


@dataclass
class _RoleOutcome:
    role: str
    status: str
    detail: dict[str, Any] = field(default_factory=dict)
    differences: list[dict[str, Any]] = field(default_factory=list)


def _diff_row_pair(
    role: str,
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    row_key: str,
    left_index: int | None,
    right_index: int | None,
    derived_hash_proofs: Mapping[str, Any] | None,
    expose_values: bool,
    buffer: _DifferenceBuffer,
) -> tuple[bool, int]:
    """Field-level diff of one aligned pair.  Returns ``(differed, nonfinite)``.

    Uses ``task2``'s own difference engine and preimage validator, so the only
    behavioural change against ``task2.compare_role_rows`` is that findings are
    recorded rather than raised.
    """

    def record(path: tuple[str, ...], classification: str, reason: str,
               left_value: Any, right_value: Any) -> None:
        buffer.add(
            RowDifference(
                role=role,
                row_key=row_key,
                left_index=left_index,
                right_index=right_index,
                path=path,
                classification=classification,
                reason=reason,
                left_present=left_value is not MISSING,
                right_present=right_value is not MISSING,
                left_value_sha256=_value_digest(left_value),
                right_value_sha256=_value_digest(right_value),
                left_value=left_value if expose_values else None,
                right_value=right_value if expose_values else None,
                values_exposed=expose_values,
            )
        )

    differed = False

    # task2:951-952 -- both rows' declared runtime hashes must match their own
    # preimages before any comparison is meaningful. Without this the allowlist
    # grants PREIMAGE on a pattern match and never checks the preimage.
    for side, row in (("left", left), ("right", right)):
        try:
            task2._validate_runtime_hash_preimages(role, row, row_index=left_index or 0)
        except task2.SemanticAcceptanceError as exc:
            differed = True
            record((f"<{side}_row_preimage>",), CLASSIFICATION_UNKNOWN,
                   f"row_preimage_invalid:{side}:{exc}", MISSING, MISSING)

    left_diffable, left_nan, left_nonfinite = sanitize_row(left)
    right_diffable, right_nan, right_nonfinite = sanitize_row(right)

    # A NaN is never silently equal, even when both sides carry one.
    for nan_path in sorted(set(left_nan) | set(right_nan)):
        differed = True
        parts = tuple(nan_path.split("/")) if nan_path else ("<root>",)
        record(parts, CLASSIFICATION_UNKNOWN, "non_finite_undefined_value",
               _safe_path_value(left, parts), _safe_path_value(right, parts))

    for path in task2._difference_paths(left_diffable, right_diffable):
        differed = True
        path = tuple(str(part) for part in path)
        left_value = _safe_path_value(left, path)
        right_value = _safe_path_value(right, path)
        classification, reason = classify_difference(
            role, path, left_value, right_value,
            left_row=left, right_row=right,
            derived_hash_proofs=derived_hash_proofs,
        )
        record(path, classification, reason, left_value, right_value)

    return differed, left_nonfinite + right_nonfinite


def _row_digest(row: Mapping[str, Any]) -> str:
    diffable, _, _ = sanitize_row(row)
    return hashlib.sha256(task2.canonical_bytes(diffable)).hexdigest()


def _compare_role_positional(
    role: str,
    left_arm: ArmOutputs,
    right_arm: ArmOutputs,
    *,
    end_day: str | None,
    derived_hash_proofs: Mapping[str, Any] | None,
    max_differences: int,
    expose_values: bool,
) -> _RoleOutcome:
    """Lockstep comparison -- the ``compare_role_rows`` discipline, accumulating.

    This is the mode for the Phase-2 use case: the *same* arm, old engine
    against new engine.  Row order is part of what is being asserted, so a
    count mismatch is a finding rather than something to align away.
    """

    sentinel = object()
    left_rows = left_arm.iter_role_rows(role, end_day=end_day)
    right_rows = right_arm.iter_role_rows(role, end_day=end_day)
    buffer = _DifferenceBuffer(max_differences)
    rows_with_differences = 0
    nonfinite = 0
    left_count = 0
    right_count = 0

    for index, (left, right) in enumerate(
        zip_longest(left_rows, right_rows, fillvalue=sentinel)
    ):
        if left is sentinel or right is sentinel:
            # A length mismatch under positional alignment: report it and stop.
            # Continuing would compare misaligned rows and manufacture noise.
            if left is not sentinel:
                left_count += 1
            if right is not sentinel:
                right_count += 1
            left_count += sum(1 for _ in left_rows)
            right_count += sum(1 for _ in right_rows)
            return _RoleOutcome(
                role=role,
                status=STATUS_DIFFER,
                detail={
                    "alignment": "positional",
                    "left_row_count": left_count,
                    "right_row_count": right_count,
                    "row_count_mismatch": True,
                    "first_unmatched_index": index,
                    "rows_with_differences": rows_with_differences,
                    "unknown_difference_count": buffer.unknown_total,
                    "allowlisted_difference_count": buffer.benign_total,
                    "non_finite_leaf_count": nonfinite,
                    "differences_truncated": buffer.truncated,
                    "max_differences_per_role": buffer.cap,
                    "note": (
                        "positional alignment stopped at the first length "
                        "mismatch; use identity alignment to localise which "
                        "rows are unmatched"
                    ),
                },
                differences=buffer.as_list(),
            )
        left_count += 1
        right_count += 1
        differed, row_nonfinite = _diff_row_pair(
            role, left, right,
            row_key=str(index), left_index=index, right_index=index,
            derived_hash_proofs=derived_hash_proofs,
            expose_values=expose_values, buffer=buffer,
        )
        nonfinite += row_nonfinite
        if differed:
            rows_with_differences += 1

    if left_count == 0 and right_count == 0:
        return _RoleOutcome(
            role=role,
            status=STATUS_UNAVAILABLE,
            detail={
                "reason": "no_rows_compared",
                "note": (
                    "both sides yielded zero rows; an empty comparison is not "
                    "evidence of equivalence"
                ),
            },
        )

    equivalent = buffer.unknown_total == 0 and not buffer.truncated
    return _RoleOutcome(
        role=role,
        status=STATUS_EQUIVALENT if equivalent else STATUS_DIFFER,
        detail={
            "alignment": "positional",
            "left_row_count": left_count,
            "right_row_count": right_count,
            "row_count_mismatch": False,
            "rows_with_differences": rows_with_differences,
            "unknown_difference_count": buffer.unknown_total,
            "allowlisted_difference_count": buffer.benign_total,
            "non_finite_leaf_count": nonfinite,
            "differences_truncated": buffer.truncated,
            "max_differences_per_role": buffer.cap,
        },
        differences=buffer.as_list(),
    )


def _index_by_identity(
    arm: ArmOutputs,
    role: str,
    fields: Sequence[str],
    *,
    end_day: str | None,
) -> tuple[dict[str, str], dict[str, int]]:
    """Pass one: key -> row digest, and key -> row index.  Rows are not kept."""

    digests: dict[str, str] = {}
    indices: dict[str, int] = {}
    for index, row in enumerate(arm.iter_role_rows(role, end_day=end_day)):
        key = _identity_of(row, fields)
        if key in digests:
            raise DifferentialHarnessError(f"identity_key_not_unique:{role}:{key}")
        digests[key] = _row_digest(row)
        indices[key] = index
    return digests, indices


def _compare_role_identity(
    role: str,
    left_arm: ArmOutputs,
    right_arm: ArmOutputs,
    *,
    fields: Sequence[str],
    end_day: str | None,
    derived_hash_proofs: Mapping[str, Any] | None,
    max_differences: int,
    max_detailed_rows: int,
    max_reported_keys: int,
    expose_values: bool,
) -> _RoleOutcome:
    """Key-joined comparison, for two arms whose row sets legitimately differ.

    Pass one keeps only digests.  Pass two materialises at most
    ``max_detailed_rows`` left rows at a time -- **that bound is load-bearing**:
    the ``missed`` surface is 154,299 rows averaging 49 KB (7.6 GB logical) and
    ``scorecard`` rows average 1.95 MB, so an unbounded pass two would exceed
    this 16 GiB machine on either.  Peak is ``max_detailed_rows`` x the largest
    row, and any changed row beyond the bound is counted but not detailed, which
    blocks ``EQUIVALENT`` for the role.
    """

    left_digests, left_indices = _index_by_identity(
        left_arm, role, fields, end_day=end_day
    )
    right_digests, right_indices = _index_by_identity(
        right_arm, role, fields, end_day=end_day
    )

    left_only = sorted(set(left_digests) - set(right_digests))
    right_only = sorted(set(right_digests) - set(left_digests))
    shared = set(left_digests) & set(right_digests)
    changed = {key for key in shared if left_digests[key] != right_digests[key]}

    if not left_digests and not right_digests:
        return _RoleOutcome(
            role=role,
            status=STATUS_UNAVAILABLE,
            detail={
                "reason": "no_rows_compared",
                "note": (
                    "both sides yielded zero rows; an empty comparison is not "
                    "evidence of equivalence"
                ),
            },
        )

    buffer = _DifferenceBuffer(max_differences)
    detailed = sorted(changed)[: max(0, int(max_detailed_rows))]
    not_detailed = len(changed) - len(detailed)
    detailed_set = set(detailed)
    rows_with_differences = 0
    nonfinite = 0

    if detailed_set:
        left_rows: dict[str, Mapping[str, Any]] = {}
        for row in left_arm.iter_role_rows(role, end_day=end_day):
            key = _identity_of(row, fields)
            if key in detailed_set:
                left_rows[key] = row
        for row in right_arm.iter_role_rows(role, end_day=end_day):
            key = _identity_of(row, fields)
            if key not in detailed_set:
                continue
            differed, row_nonfinite = _diff_row_pair(
                role, left_rows[key], row,
                row_key=key,
                left_index=left_indices[key], right_index=right_indices[key],
                derived_hash_proofs=derived_hash_proofs,
                expose_values=expose_values, buffer=buffer,
            )
            nonfinite += row_nonfinite
            if differed:
                rows_with_differences += 1

    # The same equivalence rule as positional: a row-level digest change that
    # turns out to be entirely allowlisted is not a difference. Two real runs
    # always differ in wall-clock, so deciding on digests alone would make
    # identity alignment unable to certify the case it exists for.
    equivalent = (
        not left_only
        and not right_only
        and not not_detailed
        and buffer.unknown_total == 0
        and not buffer.truncated
    )
    return _RoleOutcome(
        role=role,
        status=STATUS_EQUIVALENT if equivalent else STATUS_DIFFER,
        detail={
            "alignment": "identity",
            "identity_key_fields": list(fields),
            "left_row_count": len(left_digests),
            "right_row_count": len(right_digests),
            "matched_row_count": len(shared),
            "left_only_row_count": len(left_only),
            "right_only_row_count": len(right_only),
            "left_only_keys": left_only[:max_reported_keys],
            "right_only_keys": right_only[:max_reported_keys],
            "keys_truncated": (
                len(left_only) > max_reported_keys
                or len(right_only) > max_reported_keys
            ),
            "rows_changed_by_digest": len(changed),
            "rows_with_differences": rows_with_differences,
            "rows_changed_not_detailed": not_detailed,
            "max_detailed_rows": max(0, int(max_detailed_rows)),
            "unknown_difference_count": buffer.unknown_total,
            "allowlisted_difference_count": buffer.benign_total,
            "non_finite_leaf_count": nonfinite,
            "differences_truncated": buffer.truncated,
            "max_differences_per_role": buffer.cap,
        },
        differences=buffer.as_list(),
    )


def compare_arms(
    left: ArmOutputs | Path | str,
    right: ArmOutputs | Path | str,
    *,
    roles: Sequence[str] | None = None,
    alignment: str = "positional",
    identity_keys: Mapping[str, Sequence[str]] | None = None,
    end_day: str | None = None,
    derived_hash_proofs: Mapping[str, Any] | None = None,
    max_differences_per_role: int = 200,
    max_detailed_rows: int = 200,
    max_reported_keys: int = 50,
    expose_values: bool = False,
    generated_utc: str | None = None,
) -> dict[str, Any]:
    """Compare two arm outputs and report *where* they differ.

    ``roles`` defaults to the roles readable in **both** arms.  A role requested
    but unreadable is reported ``UNAVAILABLE`` and blocks ``EQUIVALENT`` -- it is
    never quietly dropped, because a comparator that skips what it cannot read is
    the failure mode this harness exists to prevent.
    """

    if alignment not in {"positional", "identity"}:
        raise DifferentialHarnessError(f"alignment_unknown:{alignment}")
    left_arm = left if isinstance(left, ArmOutputs) else ArmOutputs(left)
    right_arm = right if isinstance(right, ArmOutputs) else ArmOutputs(right)
    keys = dict(ROLE_IDENTITY_KEYS)
    if identity_keys:
        keys.update({str(k): tuple(v) for k, v in identity_keys.items()})

    if roles is None:
        requested = [
            role
            for role in task2.ROLE_SUFFIXES
            if role in set(left_arm.available_roles())
            & set(right_arm.available_roles())
        ]
    else:
        seen: list[str] = []
        for role in roles:
            if role not in task2.ROLE_SUFFIXES:
                raise DifferentialHarnessError(f"role_unknown:{role}")
            if role not in seen:
                seen.append(role)
        requested = seen

    outcomes: list[_RoleOutcome] = []
    for role in requested:
        unreadable = None
        for arm, side in ((left_arm, "left"), (right_arm, "right")):
            mode = arm.storage_mode(role)
            if mode not in {"raw", "cold", "zst"}:
                unreadable = _RoleOutcome(
                    role=role,
                    status=STATUS_UNAVAILABLE,
                    detail={
                        "reason": f"role_evidence_{mode}_on_{side}",
                        "path": str(arm.logical_path(role)),
                    },
                )
                break
        if unreadable is not None:
            outcomes.append(unreadable)
            continue
        if alignment == "identity" and role not in keys:
            outcomes.append(
                _RoleOutcome(
                    role=role,
                    status=STATUS_UNAVAILABLE,
                    detail={
                        "reason": "identity_key_undeclared",
                        "note": (
                            "no measured-unique identity key for this role; "
                            "pass one explicitly or use positional alignment"
                        ),
                    },
                )
            )
            continue
        try:
            if alignment == "identity":
                outcomes.append(
                    _compare_role_identity(
                        role, left_arm, right_arm,
                        fields=keys[role], end_day=end_day,
                        derived_hash_proofs=derived_hash_proofs,
                        max_differences=max_differences_per_role,
                        max_detailed_rows=max_detailed_rows,
                        max_reported_keys=max_reported_keys,
                        expose_values=expose_values,
                    )
                )
            else:
                outcomes.append(
                    _compare_role_positional(
                        role, left_arm, right_arm, end_day=end_day,
                        derived_hash_proofs=derived_hash_proofs,
                        max_differences=max_differences_per_role,
                        expose_values=expose_values,
                    )
                )
        except Exception as exc:  # noqa: BLE001 - see below
            # A role must not be able to abandon a multi-hour run. task2 and the
            # cold reader raise siblings of ValueError/RuntimeError that are not
            # ours (NonFiniteCanonicalValueError, ColdEvidenceError,
            # SemanticAcceptanceError, OSError). Every one becomes UNAVAILABLE,
            # which blocks EQUIVALENT, so catching broadly cannot manufacture a
            # false green.
            outcomes.append(
                _RoleOutcome(
                    role=role,
                    status=STATUS_UNAVAILABLE,
                    detail={
                        "reason": f"{type(exc).__name__}:{exc}",
                    },
                )
            )

    compared = [o for o in outcomes if o.status != STATUS_UNAVAILABLE]
    unavailable = [o for o in outcomes if o.status == STATUS_UNAVAILABLE]
    differing = [o for o in compared if o.status != STATUS_EQUIVALENT]
    if differing:
        # A proven difference outranks an incomplete one: saying "could not
        # establish" when a difference HAS been established understates it.
        verdict = VERDICT_DIFFER
    elif not compared or unavailable:
        verdict = VERDICT_INCOMPLETE
    else:
        verdict = VERDICT_EQUIVALENT

    role_reports: dict[str, Any] = {}
    for outcome in outcomes:
        role_reports[outcome.role] = {
            "status": outcome.status,
            **outcome.detail,
            "differences": outcome.differences,
        }

    report = {
        "schema": SCHEMA,
        "generated_utc": generated_utc
        or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verdict": verdict,
        "left": left_arm.describe(),
        "right": right_arm.describe(),
        "same_root": left_arm.root == right_arm.root,
        "alignment": alignment,
        "end_day": end_day,
        "roles_requested": requested,
        "roles_compared": [o.role for o in compared],
        "roles_unavailable": [o.role for o in unavailable],
        "roles": role_reports,
        "limits": {
            "max_differences_per_role": int(max_differences_per_role),
            "max_detailed_rows": int(max_detailed_rows),
            "max_reported_keys": int(max_reported_keys),
        },
        "totals": {
            "unknown_difference_count": sum(
                o.detail.get("unknown_difference_count", 0) for o in outcomes
            ),
            "allowlisted_difference_count": sum(
                o.detail.get("allowlisted_difference_count", 0) for o in outcomes
            ),
            "non_finite_leaf_count": sum(
                o.detail.get("non_finite_leaf_count", 0) for o in outcomes
            ),
            "any_truncated": any(
                o.detail.get("differences_truncated") for o in outcomes
            ),
            "roles_compared": len(compared),
            "roles_unavailable": len(unavailable),
        },
        "allowlist_root_sha256": task2.ALLOWLIST_RECEIPT["allowlist_root_sha256"],
        "derived_hash_proofs_root_sha256": (
            task2.canonical_sha256(dict(derived_hash_proofs))
            if derived_hash_proofs
            else None
        ),
        "economic_values_exposed": bool(expose_values),
        "acceptance_authorized": False,
    }
    report["report_root_sha256"] = task2.canonical_sha256(report)
    return report


def _parse_identity_key_overrides(values: Sequence[str]) -> dict[str, tuple[str, ...]]:
    out: dict[str, tuple[str, ...]] = {}
    for item in values:
        if "=" not in item:
            raise DifferentialHarnessError(f"identity_key_spec_invalid:{item}")
        role, _, fields = item.partition("=")
        out[role.strip()] = tuple(f.strip() for f in fields.split(",") if f.strip())
    return out


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Report where two replay arm outputs differ, at row and field "
            "level, failing closed on any difference it cannot classify."
        )
    )
    parser.add_argument("--left", required=True, help="left arm output directory")
    parser.add_argument("--right", required=True, help="right arm output directory")
    parser.add_argument(
        "--role",
        action="append",
        dest="roles",
        help="restrict to this role (repeatable); default is every shared role",
    )
    parser.add_argument(
        "--alignment",
        choices=("positional", "identity"),
        default="positional",
        help=(
            "positional (default) is the same-arm engine-vs-engine discipline; "
            "identity joins on a measured-unique key for cross-arm work"
        ),
    )
    parser.add_argument(
        "--identity-key",
        action="append",
        default=[],
        metavar="ROLE=field1,field2",
        help="declare or override the identity key for a role",
    )
    parser.add_argument("--end-day", default=None, help="compare rows up to this day")
    parser.add_argument(
        "--max-differences", type=int, default=200, help="per-role difference cap"
    )
    parser.add_argument(
        "--max-detailed-rows",
        type=int,
        default=200,
        help="identity alignment: changed rows held in memory for field diffing",
    )
    parser.add_argument(
        "--expose-values",
        action="store_true",
        help="include raw differing values (marks the receipt as exposing them)",
    )
    parser.add_argument("--output", default=None, help="write the receipt here")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    report = compare_arms(
        args.left,
        args.right,
        roles=args.roles,
        alignment=args.alignment,
        identity_keys=_parse_identity_key_overrides(args.identity_key),
        end_day=args.end_day,
        max_differences_per_role=args.max_differences,
        max_detailed_rows=args.max_detailed_rows,
        expose_values=args.expose_values,
    )
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        destination = Path(args.output)
        if destination.exists():
            raise DifferentialHarnessError(
                f"differential_output_must_be_new:{destination}"
            )
        destination.write_text(text + "\n", encoding="utf-8")
    print(text)
    # 0 only when equivalence was actually established.
    return 0 if report["verdict"] == VERDICT_EQUIVALENT else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
