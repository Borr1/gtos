"""Walk-forward lock enforcement.

Prevents prompt changes during a walk-forward evaluation window
by computing SHA256 of the primary analyzer prompt file and comparing
against a stored lock. Emits a warning (not a hard block) on mismatch
to allow emergency fixes.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

LOCK_PATH = "knowledge_base/meta/walk_forward_lock.json"
PROMPT_PATH = "src/prompts/primary_analyzer_prompt.py"


def compute_prompt_hash(prompt_path: str = PROMPT_PATH) -> str:
    """Compute SHA256 of the primary analyzer prompt file."""
    with open(prompt_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_lock(lock_path: str = LOCK_PATH) -> dict | None:
    """Load the walk-forward lock file, or None if it doesn't exist."""
    path = Path(lock_path)
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def save_lock(lock_data: dict, lock_path: str = LOCK_PATH):
    """Save the walk-forward lock file."""
    path = Path(lock_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(lock_data, f, indent=2)


def check_walk_forward_lock(
    prompt_path: str = PROMPT_PATH,
    lock_path: str = LOCK_PATH,
) -> bool:
    """Check if the prompt matches the walk-forward lock.

    Returns True if everything is fine (no lock, or lock matches, or lock expired).
    Returns False if there's a violation (logs a prominent warning).
    """
    lock = load_lock(lock_path)
    if lock is None:
        logger.debug("No walk-forward lock found — skipping check")
        return True

    # Check if lock has expired
    expires = lock.get("lock_expires")
    if expires:
        try:
            expires_dt = datetime.fromisoformat(expires)
            if expires_dt.tzinfo is None:
                expires_dt = expires_dt.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_dt:
                logger.info("Walk-forward lock expired at %s — no enforcement", expires)
                return True
        except (ValueError, TypeError):
            pass

    # Compute current hash
    try:
        current_hash = compute_prompt_hash(prompt_path)
    except FileNotFoundError:
        logger.warning("Prompt file not found at %s — cannot verify walk-forward lock",
                        prompt_path)
        return True

    locked_hash = lock.get("prompt_hash", "")
    window = lock.get("window", "unknown")
    lock_expires = lock.get("lock_expires", "unknown")

    if current_hash != locked_hash:
        logger.warning(
            "\n"
            "=" * 70 + "\n"
            "⚠️  WALK-FORWARD VIOLATION: Prompt has changed during %s window.\n"
            "    Lock expires %s.\n"
            "    Expected hash: %s\n"
            "    Current hash:  %s\n"
            "    This is a WARNING only — trading will continue.\n"
            "    If this is an emergency fix, document the reason.\n"
            + "=" * 70,
            window, lock_expires, locked_hash[:16] + "...", current_hash[:16] + "...",
        )
        return False

    logger.info("Walk-forward lock OK: %s (hash matches, expires %s)",
                window, lock_expires)
    return True


def create_lock(
    window: str,
    months: int = 3,
    prompt_path: str = PROMPT_PATH,
    lock_path: str = LOCK_PATH,
    prompt_version: str = "v1.0_multi_instrument",
) -> dict:
    """Create a new walk-forward lock.

    Args:
        window: Window identifier (e.g. "WF-1")
        months: Lock duration in months
        prompt_path: Path to prompt file to hash
        lock_path: Where to save the lock
        prompt_version: Human-readable version tag

    Returns:
        The lock data dict
    """
    now = datetime.now(timezone.utc)
    # Approximate months as 30 days each
    from datetime import timedelta
    expires = now + timedelta(days=months * 30)

    prompt_hash = compute_prompt_hash(prompt_path)

    lock_data = {
        "window": window,
        "prompt_hash": prompt_hash,
        "locked_at": now.isoformat(),
        "lock_expires": expires.isoformat(),
        "prompt_version": prompt_version,
    }

    save_lock(lock_data, lock_path)
    logger.info("Walk-forward lock created: %s (expires %s)", window, expires.isoformat())
    return lock_data
