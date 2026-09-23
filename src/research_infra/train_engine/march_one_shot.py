"""The March 2026 one-shot authorization — explicit, default-off, span-bounded.

March 2026 is the estate's only outcome-unread month, and three independent
fuses protect it:

1. `trainer_partitions.PartitionRegistry.reserved_blackout` — checked before any
   role lookup, so no role can unlock it (`guard.assert_no_blackout`);
2. `trainer_partitions.SurfaceMap.blackout` — checked before any band lookup, so
   the VAL band that *does* span 2026-03 (`val_selection_surface_2025_2026H1`,
   2025-01-01..2026-05-31) never gets consulted;
3. `lane_rematerialization.LaneInputRegistry`'s `march_window_registered is not
   False` refusal, plus the simple absence of a `march_2026` lane window.

`MARCH_PREREG_V1` (`docs/audits/fable5-vision-audit-20260725/phase19/receipts/
forensic/MARCH_PREREG_V1.md`) is the frozen protocol for opening them exactly
once, and OD-FA2-1 makes Borhen the sole trigger. This module is how that
opening is expressed in code, and every property of it is deliberate:

* **Default-off.** `current()` returns `None` unless the process environment
  arms it. Nothing here changes any default object, so every other session, test
  and tool keeps all three fuses at full strength. The committed tests that pin
  March as refused (`test_training_lane_protocol.py`) stay green unarmed.
* **Possession of the prereg is the key.** Arming requires
  `GTOS_MARCH_ONE_SHOT_PREREG_SHA256` to equal the sha256 of the committed
  prereg *file on disk*. A wrong value is a hard refusal, not a silent
  no-arm — an operator who meant to arm and mistyped must not get a quiet
  "March still blacked out" and think the fuse blew for a different reason.
* **Span-bounded.** The authorization covers exactly 2026-03-01..2026-03-31, and
  `authorized_registry`/`authorized_surfaces` assert that the blackout they are
  clearing is that span and nothing else. If a future session widens the
  blackout to protect a second month, this module refuses rather than silently
  unlocking it too.
* **Purpose-bounded.** Only `PURPOSE_LANE_ITERATION`. There is no arming under
  which a March day becomes trainable: `TRAINABLE_ROLES` is untouched, and
  March's partition role stays `RESERVED_UNREAD`, which is not in it. The
  one-shot buys the right to *iterate* the lane over March; it never buys the
  right to fit on it.
* **Self-naming in receipts.** The authorized surface map's `map_id` and the
  authorized registry's `registry_id` both carry a `+march_one_shot:` suffix, so
  every `WindowAuthorization`, every lane receipt and every iteration-ledger row
  produced under the arming says so in a field a reader already looks at. No
  separate disclosure to remember to write.

What this module is NOT: it is not a way to make March cheaper to read a second
time. The prereg's decode event is one event; a second one needs a new owner
word, and the honest place to record that is the prereg's successor, not a
looser default here.
"""

from __future__ import annotations

import dataclasses
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.research_infra import trainer_partitions
from src.research_infra.trainer_partitions import (
    DEFAULT_REGISTRY,
    DEFAULT_SURFACE_MAP,
    RESERVED_UNREAD_MARCH_2026,
    PartitionRegistry,
    SurfaceMap,
)

__all__ = [
    "ENV_PREREG_SHA256",
    "MARCH_PREREG_REPO_RELPATH",
    "MarchOneShotAuthorization",
    "MarchOneShotRefused",
    "authorized_registry",
    "authorized_surfaces",
    "current",
]

#: The environment variable that arms the one-shot. Its value must equal the
#: sha256 of the committed prereg; see the module docstring.
ENV_PREREG_SHA256 = "GTOS_MARCH_ONE_SHOT_PREREG_SHA256"

MARCH_PREREG_REPO_RELPATH = (
    "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/"
    "MARCH_PREREG_V1.md"
)

#: Borhen, 2026-08-05, recorded in `phase19/SESSION_MARCH_EXECUTOR.md`.
OWNER_WORD_UTC = "2026-08-05"

REPO_ROOT = Path(__file__).resolve().parents[3]


class MarchOneShotRefused(RuntimeError):
    """The arming was attempted and did not authenticate. Never silent."""


@dataclass(frozen=True)
class MarchOneShotAuthorization:
    """Proof that this process may iterate the lane over the March blackout."""

    prereg_repo_relpath: str
    prereg_sha256: str
    owner_word_utc: str
    span: tuple[str, str] = RESERVED_UNREAD_MARCH_2026
    protocol: str = "MARCH_PREREG_V1"
    decision: str = "OD-FA2-1"

    @property
    def suffix(self) -> str:
        return f"+march_one_shot:{self.protocol}:{self.prereg_sha256[:16]}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "march_one_shot_armed": True,
            "protocol": self.protocol,
            "owner_decision": self.decision,
            "owner_word_utc": self.owner_word_utc,
            "prereg_repo_relpath": self.prereg_repo_relpath,
            "prereg_sha256": self.prereg_sha256,
            "authorized_span": list(self.span),
            "authorized_purpose": "LANE_ITERATION",
            "trainable_roles_unchanged": sorted(trainer_partitions.TRAINABLE_ROLES),
        }


def _prereg_sha256(repo_root: Path | None = None) -> tuple[Path, str]:
    root = REPO_ROOT if repo_root is None else Path(repo_root)
    path = root / MARCH_PREREG_REPO_RELPATH
    if not path.is_file() or path.is_symlink():
        raise MarchOneShotRefused(f"march_one_shot_prereg_missing:{path}")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def current(
    *, env: dict[str, str] | None = None, repo_root: Path | None = None
) -> MarchOneShotAuthorization | None:
    """The authorization this process carries, or `None` when unarmed.

    Fails closed and LOUD: an armed-but-wrong digest raises rather than
    returning `None`, so a mistyped arming can never be read as "March is
    still protected for the ordinary reason".
    """

    source = os.environ if env is None else env
    raw = str(source.get(ENV_PREREG_SHA256) or "").strip()
    if not raw:
        return None
    path, actual = _prereg_sha256(repo_root)
    if raw.lower() != actual:
        raise MarchOneShotRefused(
            f"march_one_shot_prereg_digest_mismatch: {ENV_PREREG_SHA256} carries "
            f"{raw!r} but {path} hashes to {actual!r}. The arming key is the "
            f"prereg's own bytes; refusing rather than running unarmed."
        )
    return MarchOneShotAuthorization(
        prereg_repo_relpath=MARCH_PREREG_REPO_RELPATH,
        prereg_sha256=actual,
        owner_word_utc=OWNER_WORD_UTC,
    )


def _assert_clears_only_march(
    blackout: tuple[tuple[str, str], ...],
    authorization: MarchOneShotAuthorization,
    *,
    what: str,
) -> None:
    declared = tuple(tuple(row) for row in blackout)
    if declared != (tuple(authorization.span),):
        raise MarchOneShotRefused(
            f"march_one_shot_span_mismatch:{what}: this authorization clears "
            f"{authorization.span} and only that, but the {what} blackout is "
            f"{declared}. Refusing — widening the one-shot to cover a range it "
            f"was never priced for is exactly what it exists to prevent."
        )


def authorized_registry(
    authorization: MarchOneShotAuthorization,
    *,
    base: PartitionRegistry = DEFAULT_REGISTRY,
) -> PartitionRegistry:
    """`base` with the March blackout cleared, and nothing else changed.

    March's partition role stays `RESERVED_UNREAD`, which is not in
    `TRAINABLE_ROLES`, so `assert_trainable` still refuses every March day. This
    only removes the pre-role refusal.
    """

    _assert_clears_only_march(base.reserved_blackout, authorization, what="partition-registry")
    return dataclasses.replace(
        base,
        registry_id=f"{base.registry_id}{authorization.suffix}",
        reserved_blackout=(),
        blackout_reason=(
            f"{base.blackout_reason} CLEARED FOR ONE EVENT by "
            f"{authorization.protocol} ({authorization.decision}, owner word "
            f"{authorization.owner_word_utc}); LANE_ITERATION only, "
            f"TRAINABLE_ROLES unchanged."
        ),
        _by_role={},
    )


def authorized_surfaces(
    authorization: MarchOneShotAuthorization,
    *,
    base: SurfaceMap = DEFAULT_SURFACE_MAP,
) -> SurfaceMap:
    """`base` with the March blackout cleared, and nothing else changed.

    With the blackout gone March falls through to the band that already covers
    it — `val_selection_surface_2025_2026H1`, surface `VAL` — so it is iterable
    and carries that band's used-once disclosure, exactly like January.
    """

    _assert_clears_only_march(base.blackout, authorization, what="surface-map")
    return dataclasses.replace(
        base,
        map_id=f"{base.map_id}{authorization.suffix}",
        blackout=(),
        note=(
            f"{base.note} March 2026 blackout cleared for one event by "
            f"{authorization.protocol} ({authorization.decision}); the day falls "
            f"through to its VAL band and carries that band's disclosure."
        ),
    )
