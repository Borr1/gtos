"""Presence-of-authorization gate for operator-facing notification delivery.

Why this exists
---------------
F30 (2026-07-26) measured that running the test suite creates
``pipeline_state/notification_queue.jsonl`` and
``pipeline_state/UNDELIVERED_CRITICAL_ALERTS.jsonl`` holding trade-shaped
alerts — ``"[FTMO] 🟢 LONG BTCUSD · Crypto momentum … risk 0.40% (~$397)"``.
The *only* thing that stopped those from reaching Borhen's phone was
``"reason": "telegram_creds_missing"``. Both transports gate on credential
presence and nothing else::

    src/utils/notification_queue.py:304-306   token/chat_id empty -> skip POST
    src/notifications.py:113-114              token/chat_id empty -> return

On any machine where ``TELEGRAM_BOT_TOKEN`` and ``TELEGRAM_CHAT_ID`` are set —
the live VPS, or any developer who sourced the live ``.env`` — ``pytest`` would
page the operator with fabricated trades. Credential presence is not an
authorization decision; it is a coincidence of environment.

The shape of the fix
--------------------
This module is deliberately the same shape as ``activation_token.py``, and for
the same reason. The tempting fix is to make the notifier check for a "we are
running under test" marker and stay quiet. That is **fail-open**: the marker's
absence means *deliver*, so every context nobody thought about — a script, a
notebook, a subprocess, a fixture that runs after teardown removed the marker —
silently gets delivery rights. That is exactly the F2 mistake this programme
already made once with the halt flags, where absence-of-halt meant "clear" and
a fresh clone was therefore maximally unprotected.

So the polarity is inverted: **delivery is refused unless this process has been
positively authorized.** A process that never authorizes cannot page anybody, no
matter what is in its environment, and nothing has to be remembered to turn it
off.

Granting authorization
----------------------
Two grant sources, in order of strength:

1. **Programmatic, in-process** — ``authorize_operator_delivery(reason=...)``.
   The live entrypoints call this at startup, right after ``load_dotenv``:

   * ``src/utils/notification_queue.py`` ``main()`` — the ``--worker`` /
     ``--drain-once`` CLI. This is *the* live delivery path: the queue's
     drain daemon is launched by ``scripts/watchdog.ps1:1516`` as
     ``python -m src.utils.notification_queue --worker``, and it owns every
     HIGH/CRITICAL transport call in production.
   * ``run_book.py`` ``main()`` and ``run_agent.py`` ``main()`` — these emit
     ``Level.LOW`` alerts, which the queue transports synchronously in-process
     rather than handing to the worker, and they fall back to
     ``notifications._send_async`` if the queue subsystem is unavailable.

2. **Environment** — ``GTOS_OPERATOR_NOTIFICATION_DELIVERY=authorized``. For
   launchers, supervisors and one-off operator tooling that should deliver
   without a code change. Weaker on purpose: see the veto below.

Neither grant is a config key. There is no ``agent_config.yaml`` flag that
turns delivery on, by design — a SHA-bound config file is the wrong place for a
per-process runtime capability, and B26 established that a single YAML boolean
is not a brake anybody is watching.

The pytest veto, and what it is NOT
-----------------------------------
Running under pytest additionally **vetoes the environment grant**. A developer
who exported the live ``GTOS_OPERATOR_NOTIFICATION_DELIVERY`` in their shell
must not thereby arm every test they run from that shell.

This veto is defence in depth, **not the mechanism**. It is deliberately not
the thing that keeps the suite quiet — the default-deny above already does
that, and would still do it if this veto were deleted. Stated explicitly
because a reader who mistakes the veto for the mechanism will "simplify" it
back into the fail-open marker check this module exists to avoid.

The veto does not override an explicit in-process
``authorize_operator_delivery()`` call, so a test can still exercise the
authorized branch — that grant is a deliberate statement in the test body, not
an ambient condition inherited from the environment.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


# Environment grant. Must equal _ENV_GRANT_VALUE exactly — a truthy-ish "1" or
# "true" is not accepted, so the variable cannot be armed by a generic
# "enable everything" sweep over the environment.
ENV_VAR = "GTOS_OPERATOR_NOTIFICATION_DELIVERY"
_ENV_GRANT_VALUE = "authorized"


class OperatorDeliveryNotAuthorized(RuntimeError):
    """Raised when a delivery is attempted without authorization."""


@dataclass(frozen=True)
class DeliveryAuthorization:
    """The authorization decision for the current process.

    Attributes:
        allowed: True iff operator-facing delivery may be attempted.
        source: Which grant decided this — ``"process"``, ``"environment"``,
            ``"none"`` (default deny), or ``"pytest_veto"``.
        detail: Human-readable reason, suitable for a log line.
    """

    allowed: bool
    source: str
    detail: str


_lock = threading.RLock()
_process_grant_reason: Optional[str] = None


def _under_pytest() -> bool:
    """True when this process is a pytest run.

    Checked two ways because neither alone is reliable: ``PYTEST_CURRENT_TEST``
    is only set while a test is actually executing (not at import time, not in
    session fixtures), and ``sys.modules`` misses a subprocess that pytest
    spawned without importing itself.
    """
    return "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ


def authorize_operator_delivery(*, reason: str) -> None:
    """Grant this process the right to deliver operator-facing notifications.

    Call once at startup from a live entrypoint. ``reason`` is recorded and
    logged so an audit of a delivering process can say which entrypoint armed
    it.

    Raises:
        ValueError: if ``reason`` is empty. An unattributed grant is not
            acceptable — the whole point is that delivery rights are traceable
            to a named entrypoint.
    """
    reason = (reason or "").strip()
    if not reason:
        raise ValueError(
            "authorize_operator_delivery requires a non-empty reason naming the "
            "entrypoint taking responsibility for delivery"
        )
    global _process_grant_reason
    with _lock:
        _process_grant_reason = reason
    logger.info("operator notification delivery AUTHORIZED for this process: %s", reason)


def revoke_operator_delivery() -> None:
    """Drop the in-process grant. Idempotent.

    Used by test teardown to guarantee no grant leaks between tests, and
    available to a runtime that wants to stop paging without exiting.
    """
    global _process_grant_reason
    with _lock:
        had = _process_grant_reason is not None
        _process_grant_reason = None
    if had:
        logger.info("operator notification delivery revoked for this process")


def delivery_authorization() -> DeliveryAuthorization:
    """Return the current authorization decision. Never raises."""
    with _lock:
        process_grant = _process_grant_reason

    if process_grant is not None:
        return DeliveryAuthorization(
            allowed=True,
            source="process",
            detail=f"in-process grant: {process_grant}",
        )

    env_value = os.environ.get(ENV_VAR, "").strip()
    if env_value == _ENV_GRANT_VALUE:
        if _under_pytest():
            return DeliveryAuthorization(
                allowed=False,
                source="pytest_veto",
                detail=(
                    f"{ENV_VAR}={_ENV_GRANT_VALUE} is present but vetoed: this process is "
                    f"a pytest run. Environment grants do not arm the test suite. A test "
                    f"that genuinely needs the authorized branch must call "
                    f"authorize_operator_delivery() explicitly."
                ),
            )
        return DeliveryAuthorization(
            allowed=True,
            source="environment",
            detail=f"{ENV_VAR}={_ENV_GRANT_VALUE}",
        )

    return DeliveryAuthorization(
        allowed=False,
        source="none",
        detail=(
            "no operator-delivery authorization for this process (default deny). "
            f"Grant it by calling "
            f"src.safety.notification_authorization.authorize_operator_delivery(reason=...) "
            f"at entrypoint startup, or by setting {ENV_VAR}={_ENV_GRANT_VALUE}."
        ),
    )


def is_delivery_authorized() -> bool:
    """True iff operator-facing delivery may be attempted by this process."""
    return delivery_authorization().allowed


def require_delivery_authorization(channel: str) -> None:
    """Raise ``OperatorDeliveryNotAuthorized`` unless this process is authorized.

    Args:
        channel: Short name of the transport being guarded, for the message
            (e.g. ``"telegram"``, ``"notification_queue.transport"``).
    """
    decision = delivery_authorization()
    if not decision.allowed:
        raise OperatorDeliveryNotAuthorized(
            f"refusing to deliver an operator notification via {channel}: {decision.detail}"
        )


@contextmanager
def operator_delivery_authorized(*, reason: str) -> Iterator[None]:
    """Scoped in-process grant; restores the previous state on exit.

    Intended for tests that must exercise the authorized branch, and for
    short-lived operator tooling that should not leave the grant standing.
    """
    global _process_grant_reason
    with _lock:
        previous = _process_grant_reason
    authorize_operator_delivery(reason=reason)
    try:
        yield
    finally:
        with _lock:
            _process_grant_reason = previous
