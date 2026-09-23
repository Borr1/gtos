"""DONE_OUTSIDE — completion and side-effect checks are non-Jev.

Jev may Choice DONE / CONTINUE / BLOCKED. Code owns whether an artifact
exists and matches contract. Confidence cannot prove a save / send / order.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from .veto import JevPlacePathVeto, is_broker_or_payout_action

ADVISORY_DONE = frozenset({"DONE", "done", "COMPLETE", "complete"})


@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    reason: str
    path: str | None = None
    details: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "reason": self.reason,
            "path": self.path,
            "details": list(self.details),
        }


def verify_artifact(
    path: Path | str | None,
    *,
    required_keys: Sequence[str] = (),
    required_consts: Mapping[str, object] | None = None,
) -> VerifyResult:
    """Independent check: file exists and contract keys match."""

    if path is None:
        return VerifyResult(False, "artifact_path_missing")
    target = Path(path)
    if not target.is_file():
        return VerifyResult(False, "artifact_missing", str(target))
    try:
        doc = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return VerifyResult(False, f"artifact_unreadable:{type(exc).__name__}", str(target))
    if not isinstance(doc, dict):
        return VerifyResult(False, "artifact_not_object", str(target))
    missing = [key for key in required_keys if key not in doc]
    if missing:
        return VerifyResult(
            False, "artifact_missing_keys", str(target), tuple(missing)
        )
    mismatches: list[str] = []
    for key, expected in (required_consts or {}).items():
        if doc.get(key) != expected:
            mismatches.append(f"{key}!={expected!r}")
    if mismatches:
        return VerifyResult(
            False, "artifact_const_mismatch", str(target), tuple(mismatches)
        )
    return VerifyResult(True, "artifact_matches_contract", str(target))


def verify_side_effect(
    kind: str,
    *,
    path: Path | str | None = None,
    required_keys: Sequence[str] = (),
    required_consts: Mapping[str, object] | None = None,
) -> VerifyResult:
    """Verify a named side effect. Broker kinds are refused, not 'verified'."""

    if is_broker_or_payout_action(kind):
        raise JevPlacePathVeto(
            f"VETO PLACE_PATH: done_outside never verifies {kind}"
        )
    if kind in {"shadow_log", "label_draft", "file_write", "queue_handoff"}:
        return verify_artifact(
            path, required_keys=required_keys, required_consts=required_consts
        )
    return VerifyResult(False, f"unknown_side_effect:{kind}")


def completion_truth(
    *,
    jev_choice: str | None,
    verify: VerifyResult,
) -> str:
    """Code owns DONE. Jev DONE is advisory only."""

    advisory = str(jev_choice or "").strip()
    if verify.ok:
        return "DONE"
    if advisory in ADVISORY_DONE:
        return "NOT_DONE_JEV_ADVISORY_ONLY"
    return "NOT_DONE"
