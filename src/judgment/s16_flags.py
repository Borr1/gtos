"""S16 Dig/Chair multi-stage guard flags — Dig E KILL on APPLY.

Do **not** reuse ``GTOS_JEV_FLUID_GATES_*``. That surface is the Challenge
admit sidecar (PR29 / S14 / S15). S16 is a parallel Dig/Chair tool harness
and stays off the Challenge place scoreboard **and** off the Challenge
prove-only dual-flag track.

``GTOS_DIG_MULTI_STAGE_GUARD_APPLY`` is KILL: env and ``force`` cannot
enable APPLY. Shadow stays default-off for offline Dig/Chair fixtures.
Never place / broker / ``order_send``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

SHADOW_ENV = "GTOS_DIG_MULTI_STAGE_GUARD_SHADOW"
APPLY_ENV = "GTOS_DIG_MULTI_STAGE_GUARD_APPLY"
LOG_DIR_ENV = "GTOS_DIG_MULTI_STAGE_GUARD_LOG_DIR"
FIXTURES_ENV = "GTOS_DIG_MULTI_STAGE_GUARD_FIXTURES"

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _env_on(name: str, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get(name, "")).strip().lower() in _TRUTHY


def s16_shadow_enabled(*, environ: Mapping[str, str] | None = None, force: bool = False) -> bool:
    """Chair enables Dig/Chair S16 shadow with ``GTOS_DIG_MULTI_STAGE_GUARD_SHADOW=1``."""

    if force:
        return True
    return _env_on(SHADOW_ENV, environ)


def s16_apply_env_forbidden(*, environ: Mapping[str, str] | None = None) -> bool:
    """True when the dead APPLY env is present. Does not enable APPLY."""

    return _env_on(APPLY_ENV, environ)


def s16_apply_enabled(*, environ: Mapping[str, str] | None = None, force: bool = False) -> bool:
    """Dig E KILL: APPLY is forbidden. Env and force cannot enable it.

    Still never place / broker / order_send. Prove scripts refuse if the
    dead env is set (:func:`s16_apply_env_forbidden`).
    """

    del environ, force
    return False


def default_s16_log_dir(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else Path(__file__).resolve().parents[2]
    override = os.environ.get(LOG_DIR_ENV, "").strip()
    if override:
        return Path(override)
    return root / "judgment" / "live" / "s16_guard"


def default_s16_fixtures_dir(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else Path(__file__).resolve().parents[2]
    override = os.environ.get(FIXTURES_ENV, "").strip()
    if override:
        return Path(override)
    local = root / "judgment" / "astra" / "lab" / "s16_prove_fixtures"
    if local.is_dir():
        return local
    dig = root / "research" / "codila_absorb" / "war_room" / "s16_multi_stage_guard" / "prove_fixtures"
    return dig
