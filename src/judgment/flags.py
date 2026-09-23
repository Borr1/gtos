"""Default-off shadow / APPLY flags for Challenge fluid gates.

APPLY reuses the Alive-organism prove classes (A1 / A2 / A3 / W_named).
A0 is house-only (no Jev effect). B-forbidden is never a prove class.
Flags default off: missing env and missing receipt both mean SHADOW only.

``GTOS_JEV_EVERYWHERE_SHADOW`` is an alias of ``GTOS_JEV_FLUID_GATES_SHADOW``
(same sidecar write). Dig E 2026-09-21 stamped it APPLY_CANDIDATE
ALREADY_LIVE — not an open IN_PROVE dual-flag pair.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .veto import is_broker_or_payout_action

SHADOW_ENV = "GTOS_JEV_FLUID_GATES_SHADOW"
EVERYWHERE_ENV = "GTOS_JEV_EVERYWHERE_SHADOW"
APPLY_ENV = "GTOS_JEV_FLUID_GATES_APPLY"
PROVE_DIR_ENV = "GTOS_JEV_FLUID_GATES_PROVE_DIR"

# Dig E board APPLY_KILL_RECEIPTS_DUAL_FLAGS_CHALLENGE_20260921 (login 0).
DIG_E_BOARD = "APPLY_KILL_RECEIPTS_DUAL_FLAGS_CHALLENGE_20260921"
EVERYWHERE_IS_FLUID_GATES_ALIAS = True
EVERYWHERE_VERDICT = "APPLY_CANDIDATE_ALREADY_LIVE"
EVERYWHERE_OPEN_IN_PROVE = False
TRAIN_HARVEST_VERDICT = "ALREADY_LIVE"
TRAIN_HARVEST_SHADOW = 1
TRAIN_HARVEST_CALL = 1
TRAIN_HARVEST_APPLY = 0
# Confirm only — no TRAIN_HARVEST env exists. SHADOW labels + cycle harvest=
# CALL already live; live_multiplier stays 1.0; ready_to_apply stays false.
TRAIN_HARVEST_ENV = None
TRAIN_HARVEST_LIVE_MULTIPLIER = 1.0
TRAIN_HARVEST_READY_TO_APPLY = False
# Challenge prove-only dual-flag track: SHADOW/APPLY pairs still open for prove.
# EVERYWHERE is the fluid-gate alias (not a second pair). S16 DIG_MULTI_STAGE_GUARD
# was KILL'd off this track 2026-09-21.
CHALLENGE_PROVE_ONLY_DUAL_FLAGS = frozenset({SHADOW_ENV, APPLY_ENV})

LEGAL_WIRE_CLASSES = frozenset({"A1", "A2", "A3", "W_named"})
FORBIDDEN_WIRE_CLASSES = frozenset({"A0", "B-forbidden", "B_forbidden", "B"})

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _env_on(name: str, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get(name, "")).strip().lower() in _TRUTHY


def shadow_enabled(*, environ: Mapping[str, str] | None = None, force: bool = False) -> bool:
    """Chair enables Challenge shadow with ``GTOS_JEV_FLUID_GATES_SHADOW=1``.

    ``GTOS_JEV_EVERYWHERE_SHADOW=1`` is the same sidecar write (fan-out
    extension), not a parallel place path.
    """

    if force:
        return True
    return _env_on(SHADOW_ENV, environ) or _env_on(EVERYWHERE_ENV, environ)


def everywhere_shadow_enabled(*, environ: Mapping[str, str] | None = None, force: bool = False) -> bool:
    """Per-site Jev rows. Honors either everywhere or fluid-gate shadow.

    Dig E: this is the FLUID_GATES_SHADOW alias (ALREADY_LIVE). It is not a
    separate open IN_PROVE dual-flag pair.
    """

    return shadow_enabled(environ=environ, force=force)


def everywhere_is_open_in_prove() -> bool:
    """False after Dig E — alias is APPLY_CANDIDATE ALREADY_LIVE."""

    return EVERYWHERE_OPEN_IN_PROVE


def train_harvest_already_live() -> dict[str, object]:
    """Dig E confirm: harvest attach + cycle CALL, APPLY stays 0. No new env."""

    return {
        "verdict": TRAIN_HARVEST_VERDICT,
        "shadow": TRAIN_HARVEST_SHADOW,
        "call": TRAIN_HARVEST_CALL,
        "apply": TRAIN_HARVEST_APPLY,
        "env": TRAIN_HARVEST_ENV,
        "env_invented": False,
        "live_multiplier": TRAIN_HARVEST_LIVE_MULTIPLIER,
        "ready_to_apply": TRAIN_HARVEST_READY_TO_APPLY,
    }


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

# Dig D land consume (PR #47) — Dig E KILL reaffirm
CHALLENGE_PROVE_ONLY_DUAL_FLAGS = frozenset({SHADOW_ENV, APPLY_ENV, EVERYWHERE_ENV})
DIG_MULTI_STAGE_GUARD_OFF_PROVE_TRACK = frozenset(
    {
        "GTOS_DIG_MULTI_STAGE_GUARD_SHADOW",
        "GTOS_DIG_MULTI_STAGE_GUARD_APPLY",
    }
)

LEGAL_WIRE_CLASSES = frozenset({"A1", "A2", "A3", "W_named"})
FORBIDDEN_WIRE_CLASSES = frozenset({"A0", "B-forbidden", "B_forbidden", "B"})

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _env_on(name: str, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get(name, "")).strip().lower() in _TRUTHY


def shadow_enabled(*, environ: Mapping[str, str] | None = None, force: bool = False) -> bool:
    """Chair enables Challenge shadow with ``GTOS_JEV_FLUID_GATES_SHADOW=1``.

    ``GTOS_JEV_EVERYWHERE_SHADOW=1`` is the same sidecar write (fan-out
    extension), not a parallel place path.
    """
