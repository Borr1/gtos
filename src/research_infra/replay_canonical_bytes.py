"""One authoritative canonical-JSON encoder for replay evidence comparison.

Why this module exists
----------------------
`canonical_bytes` / `canonical_json_bytes` / `_canonical_bytes` is defined 40
times across `src/` and `research/` with **six** distinct `json.dumps`
signatures.  The three definitions used by the semantic-parity comparators
(`replay_semantic_parity`, `replay_acceleration_task2_semantic_acceptance`,
`b7_5_post_acceleration_semantic_verifier`) were the only ones configured with
``allow_nan=True``.

That divergence was not cosmetic.  Under ``allow_nan=True`` a non-finite float
serialises to the bare token ``NaN`` / ``Infinity`` / ``-Infinity``.  Parity is
then decided on *bytes*, and ``b"NaN" == b"NaN"`` is true — so two runs that
both produced an undefined economic value compared **equal** and the comparator
reported zero differences.  Every one of the 28 sealing encoders, by contrast,
uses ``allow_nan=False`` and raises on the same input.  The parity gate was
therefore strictly weaker than the sealing gate on exactly the class of value
that most reliably indicates a broken computation.

This module fails closed instead, and names the offending path so the failure
is diagnosable rather than merely loud.  No accepted artifact is affected: a
scan of the materialised Phase-D January S1R1 ledgers (order, trade, oracle,
bucket, source) found zero non-finite tokens, so on all existing evidence this
encoder is byte-identical to the encoder it replaces.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

__all__ = [
    "NonFiniteCanonicalValueError",
    "canonical_bytes",
    "canonical_sha256",
    "non_finite_paths",
]

_MAX_REPORTED_PATHS = 8


class NonFiniteCanonicalValueError(ValueError):
    """A payload carried NaN/Infinity where a finite economic value is required."""


def non_finite_paths(value: Any, *, _path: str = "$") -> list[str]:
    """Return dotted paths of every non-finite float leaf, depth-first.

    Cycle-safe: ``json.dumps`` raises ``ValueError("Circular reference detected")``
    on a self-referential payload, and this runs inside that handler, so it must
    not recurse forever on the same input.
    """

    found: list[str] = []
    stack: list[tuple[Any, str]] = [(value, _path)]
    seen: set[int] = set()
    while stack:
        node, path = stack.pop()
        if isinstance(node, float):
            if not math.isfinite(node):
                found.append(f"{path}={node!r}")
            continue
        if isinstance(node, (dict, list, tuple)):
            marker = id(node)
            if marker in seen:
                continue
            seen.add(marker)
        if isinstance(node, dict):
            for key in reversed(list(node)):
                stack.append((node[key], f"{path}.{key}"))
        elif isinstance(node, (list, tuple)):
            for index in range(len(node) - 1, -1, -1):
                stack.append((node[index], f"{path}[{index}]"))
    return found


def canonical_bytes(value: Any) -> bytes:
    """Deterministic canonical JSON bytes; fails closed on non-finite floats.

    Signature is identical to the 28 sealing encoders in this package
    (`sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=True`,
    `allow_nan=False`) so that comparison bytes and seal bytes agree.
    """

    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except ValueError as exc:
        paths = non_finite_paths(value)
        if not paths:
            raise
        shown = ", ".join(paths[:_MAX_REPORTED_PATHS])
        suffix = "" if len(paths) <= _MAX_REPORTED_PATHS else f", +{len(paths) - _MAX_REPORTED_PATHS} more"
        raise NonFiniteCanonicalValueError(
            f"non_finite_canonical_value:{shown}{suffix}"
        ) from exc


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()
