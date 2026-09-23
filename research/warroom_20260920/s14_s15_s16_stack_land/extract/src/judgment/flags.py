"""Default-off shadow / APPLY flags for Challenge fluid gates.

APPLY reuses the Alive-organism prove classes (A1 / A2 / A3 / W_named).
A0 is house-only (no Jev effect). B-forbidden is never a prove class.
Flags default off: missing env and missing receipt both mean SHADOW only.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .veto import is_broker_or_payout_action

SHADOW_ENV = "GTOS_JEV_FLUID_GATES_SHADOW"
APPLY_ENV = "GTOS_JEV_FLUID_GATES_APPLY"
PROVE_DIR_ENV = "GTOS_JEV_FLUID_GATES_PROVE_DIR"

LEGAL_WIRE_CLASSES = frozenset({"A1", "A2", "A3", "W_named"})
FORBIDDEN_WIRE_CLASSES = frozenset({"A0", "B-forbidden", "B_forbidden", "B"})

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _env_on(name: str, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get(name, "")).strip().lower() in _TRUTHY


def shadow_enabled(*, environ: Mapping[str, str] | None = None, force: bool = False) -> bool:
    """Chair enables Challenge shadow with ``GTOS_JEV_FLUID_GATES_SHADOW=1``."""

    if force:
        return True
    return _env_on(SHADOW_ENV, environ)


def apply_enabled(*, environ: Mapping[str, str] | None = None, force: bool = False) -> bool:
    """APPLY stays off unless Chair sets ``GTOS_JEV_FLUID_GATES_APPLY=1``.

    Even then, :func:`apply_authorized` still requires a legal prove receipt
    and a non-broker stake. Default is False.
    """

    if force:
        return True
    return _env_on(APPLY_ENV, environ)


def default_prove_dir(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else Path(__file__).resolve().parents[2]
    override = os.environ.get(PROVE_DIR_ENV, "").strip()
    if override:
        return Path(override)
    return root / "judgment" / "live" / "prove"


@dataclass(frozen=True)
class ProveReceipt:
    """Named live-wire / chair-sit prove row. Missing file => not proven."""

    site_id: str
    wire_class: str
    proven: bool
    owner_word: str = ""
    named_at: str | None = None
    path: str | None = None

    @property
    def legal_wire(self) -> bool:
        return self.wire_class in LEGAL_WIRE_CLASSES


def load_prove_receipt(
    site_id: str,
    *,
    prove_dir: Path | str | None = None,
) -> ProveReceipt | None:
    if not site_id:
        return None
    directory = Path(prove_dir) if prove_dir is not None else default_prove_dir()
    path = directory / f"{site_id}.json"
    if not path.is_file():
        return None
    doc = json.loads(path.read_text(encoding="utf-8"))
    return ProveReceipt(
        site_id=str(doc.get("site_id") or site_id),
        wire_class=str(doc.get("wire_class") or ""),
        proven=bool(doc.get("proven")),
        owner_word=str(doc.get("owner_word") or ""),
        named_at=doc.get("named_at"),
        path=str(path),
    )


@dataclass(frozen=True)
class ApplyDecision:
    """Whether a LABEL/REVIEW draft may be written. Never a broker send."""

    apply: bool
    reason: str
    mode: str  # shadow | review | apply_label | veto

    def as_dict(self) -> dict[str, object]:
        return {"apply": self.apply, "reason": self.reason, "mode": self.mode}


def apply_authorized(
    *,
    stake: str,
    apply_flag: bool,
    receipt: ProveReceipt | None,
    band: str,
    required_band: str,
) -> ApplyDecision:
    """APPLY is LABEL/REVIEW file write only, behind prove + flag + band.

    Confidence never authorizes side effects on its own (CONF_GATE).
    """

    if is_broker_or_payout_action(stake):
        return ApplyDecision(False, "veto_place_path", "veto")
    # S15 logs costs beside size_tilt candidates. APPLY of size_tilt still waits
    # Chair NAME after the historical calibration sheet — never live size.
    if str(stake or "").strip().lower() == "size_tilt":
        return ApplyDecision(False, "s15_shadow_only_no_size_tilt_apply", "shadow")
    if not apply_flag:
        return ApplyDecision(False, "apply_flag_off", "shadow")
    if receipt is None or not receipt.proven:
        return ApplyDecision(False, "prove_receipt_missing_or_unproven", "shadow")
    if receipt.wire_class in FORBIDDEN_WIRE_CLASSES or not receipt.legal_wire:
        return ApplyDecision(False, f"illegal_wire_class:{receipt.wire_class}", "veto")
    if _band_rank(band) < _band_rank(required_band):
        return ApplyDecision(False, f"band_{band}_below_{required_band}", "review")
    return ApplyDecision(True, "label_draft_only", "apply_label")


def _band_rank(band: str) -> int:
    return {"LOW": 0, "MED": 1, "HIGH": 2, "VETO": 99}.get(str(band).upper(), -1)
