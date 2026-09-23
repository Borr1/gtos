"""Presence-of-authorization gate for broker-mutating requests.

Why this exists
---------------
The legacy brake is *absence-of-halt*: three flag files whose presence stops the
system (``runtime_halt.py``). Second-audit F2 measured the consequence — the
flags exist in **no local working tree** (they are tracked but skip-worktree
masked), halt semantics are missing-flag-means-clear and CWD-relative, so any
live-capable process launched from any checkout on this machine reports
``runtime_halt_clear``. A fresh clone is *maximally* unprotected, which is
exactly backwards.

This module inverts it. A broker mutation that would increase exposure requires
an **activation token** to be present, valid, unexpired, and bound to the
account it is about to trade. No token, no order. A fresh clone has no token,
so a fresh clone cannot trade — fail-closed by construction, with nothing to
remember to turn on.

The one thing the token may never do
------------------------------------
**It must never be able to trap the account in an open position.** A token
lapses by expiry; positions do not. So every request classified as
risk-reducing — closing or partially closing a position, cancelling a pending
order, tightening a stop — is allowed **without any token at all**. The token
governs new exposure, and only new exposure.

(This is a different mechanism from the book's fourth authority gate
``ultimate_book_live_broker_authority``, which the owner decided on 2026-07-26
*does* suppress flatten. That gate is an intentional revocation by an operator
who is present; this token can lapse while nobody is watching. Different
failure modes, different rules — see B21 in the implementation state file.)

What the signature does and does not buy
----------------------------------------
Tokens are HMAC-SHA256 signed with a machine-local key so that hand-editing a
token — extending ``expires_utc`` in a text editor, retargeting an account —
invalidates it, forcing re-issue through the mint path that actually re-checks
the bindings. It is **tamper-evidence against accident, not defence against an
adversary with write access to the token directory**: the key lives beside the
tokens. Stated plainly because an overclaimed security property is worse than
none.

Where tokens live
-----------------
``$GTOS_ACTIVATION_TOKEN_DIR`` if set, else ``~/.gtos/activation``. Deliberately
**outside the repository**: F30 measured that the test suite writes into
``pipeline_state/`` (and ``tests/conftest.py`` guards that tree), so a token
there would be both fragile and one ``git add -A`` from being committed. Outside
the repo also means the authorization travels with the *machine that is allowed
to trade*, not with the code.
"""

from __future__ import annotations

import functools
import hashlib
import hmac
import json
import math
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from src.mt5.mt5_interface import (
    MAGIC_F5_MINIMAL,
    TRADE_ACTION_DEAL,
    TRADE_ACTION_MODIFY,
    TRADE_ACTION_PENDING,
    TRADE_ACTION_REMOVE,
    TRADE_ACTION_SLTP,
)
from src.utils.broker_profile import sha256_text

TOKEN_VERSION = "gtos_activation_token_v1"
TOKEN_DIR_ENV_VAR = "GTOS_ACTIVATION_TOKEN_DIR"
DEFAULT_TOKEN_DIR = "~/.gtos/activation"
SIGNING_KEY_FILENAME = "signing.key"
AUDIT_LOG_FILENAME = "activation_audit.jsonl"
F5_LAUNCH_CONTRACT_SCHEMA = "gtos.f5.launch_contract.v1"

# An activation that never expires is the flag file again, wearing a different
# hat. Authorization is a deliberate, time-bounded act; 30 days is generous
# against a prop-challenge cadence measured in weeks.
MAX_TOKEN_LIFETIME_HOURS = 24 * 30

# Fields covered by the signature. Any field added later must be added here or
# it is unsigned and therefore editable without detection.
_SIGNED_FIELDS = (
    "token_version",
    "schema_version",
    "namespace",
    "account_login_sha256",
    "config_digest_sha256",
    "issued_utc",
    "not_before_utc",
    "expires_utc",
    "issued_by",
    "note",
)


class ActivationTokenError(RuntimeError):
    """Raised when a broker-mutating request is not authorized."""

    def __init__(self, decision: "ActivationDecision"):
        self.decision = decision
        super().__init__(
            f"broker mutation refused: {decision.reason}"
            + (f" [{decision.classification}]" if decision.classification else "")
            + (f" ({decision.detail})" if decision.detail else "")
        )


class PositionsUnavailable(RuntimeError):
    """A positions provider could not read the broker.

    Raised by a provider so the gate can tell *"the broker says there are no
    positions"* from *"I could not ask the broker"*. Collapsing those two is
    what made the never-strand fail-safe unreachable through the real adapter:
    ``MetaTrader5.positions_get`` signals failure by returning ``None``, not by
    raising, and ``RealMT5.get_positions`` turned that ``None`` into ``[]``. A
    close then looked like a deal against a position that no longer exists —
    new exposure — and was refused with no token present. See B101.

    Any exception out of a provider has the same effect; this type exists so
    the intent is legible at the raise site.
    """


def strict_positions_provider(provider: Callable) -> Callable:
    """Mark a provider as able to distinguish "none" from "could not read".

    An empty result from a **marked** provider is evidence of absence. An empty
    result from an **unmarked** one is treated as *unverified*, because a
    provider that masks a failed read as ``[]`` would otherwise turn a broker
    outage into a refused flatten.

    Defaulting the unmarked case to "unverified" is what makes the never-strand
    invariant structural instead of a convention every future provider has to
    remember. The failure this repairs was not a missing check — it was a
    correct check fed by a lossy reader.
    """

    provider.gtos_strict_positions_provider = True
    return provider


def provider_is_authoritative(provider: Any) -> bool:
    """Whether ``provider``'s answer may be treated as the broker's own.

    Unwraps the usual indirections, because the marker is a function attribute
    and a bound method, ``functools.partial`` or decorator wrapper drops it
    silently — and dropping it is fail-open on the exposure side (B102/F-3).
    Unwrapping does not make an unmarked provider authoritative; it only stops a
    marked one from losing its promise on the way through a wrapper.
    """

    seen = 0
    candidate = provider
    while candidate is not None and seen < 8:
        if getattr(candidate, "gtos_strict_positions_provider", False):
            return True
        seen += 1
        if isinstance(candidate, functools.partial):
            candidate = candidate.func
            continue
        nxt = getattr(candidate, "__wrapped__", None) or getattr(candidate, "__func__", None)
        if nxt is None or nxt is candidate:
            return False
        candidate = nxt
    return False


@dataclass(frozen=True)
class ActivationDecision:
    """Mechanical record of one authorization decision."""

    allowed: bool
    reason: str
    risk_direction: str          # "reducing" | "increasing" | "unknown"
    decided_at_utc: str
    account_login_sha256: str | None = None
    namespace: str | None = None
    token_path: str | None = None
    token_expires_utc: str | None = None
    detail: str = ""
    request_summary: dict[str, Any] = field(default_factory=dict)
    # Why the request was classified the way it was. On a denial ``reason``
    # carries the *token* status ("activation_token_absent"), which sends an
    # operator to the token directory even when the real cause was the
    # classification — a close that did not look like one because the broker
    # read came back empty. Recording both makes that diagnosable from the
    # audit row alone.
    classification: str = ""
    positions_verified: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "risk_direction": self.risk_direction,
            "classification": self.classification,
            "positions_verified": self.positions_verified,
            "decided_at_utc": self.decided_at_utc,
            "account_login_sha256": self.account_login_sha256,
            "namespace": self.namespace,
            "token_path": self.token_path,
            "token_expires_utc": self.token_expires_utc,
            "detail": self.detail,
            "request_summary": self.request_summary,
        }


# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------


def token_dir(override: str | Path | None = None) -> Path:
    """Resolve the activation directory. Never inside the repository."""

    if override is not None:
        return Path(override).expanduser()
    env = os.environ.get(TOKEN_DIR_ENV_VAR)
    if env:
        return Path(env).expanduser()
    return Path(DEFAULT_TOKEN_DIR).expanduser()


def token_dir_display(directory: str | Path | None = None) -> str:
    """``token_dir`` for a message. Never raises.

    ``Path.expanduser()`` raises ``RuntimeError('Could not determine home
    directory.')`` when ``~`` cannot be resolved — no ``HOME``, no passwd entry,
    or a Windows service account with no ``USERPROFILE``. That is not exotic: the
    module's own default is ``~/.gtos/activation``, and D-6 is the drill about a
    scheduled task running as ``SYSTEM``.

    It escaped through ``authorize_broker_mutation``, whose docstring says
    "Never raises", because the *denial* branch re-computed the path outside the
    guard that had just caught the same exception (measured by D-3 sub-case (d),
    B321). The escape is on the exposure-increasing path only — a close returns
    before any of this — so it never stranded a position; it turned a clean
    ``ActivationTokenError`` into an unhandled ``RuntimeError`` inside the book
    worker, and crashed the operator's read-only ``status`` command, which is
    the same shape as B103/J1.
    """

    try:
        return str(token_dir(directory))
    except (OSError, RuntimeError, ValueError) as exc:
        raw = directory if directory is not None else os.environ.get(
            TOKEN_DIR_ENV_VAR) or DEFAULT_TOKEN_DIR
        return f"<unresolvable: {raw!r} ({type(exc).__name__}: {exc})>"


def repo_root_for_activation(repo_root: str | Path | None = None) -> Path:
    return (Path(repo_root) if repo_root is not None
            else Path(__file__).resolve().parents[2])


def token_dir_is_inside_repo(
    directory: str | Path | None = None,
    *,
    repo_root: str | Path | None = None,
) -> bool:
    """Is the activation directory inside the working tree?

    It must not be, and the docstring at the top of this module has always said
    so — but nothing enforced it, and the consequence was worse than an untidy
    layout. ``run_book.py`` calls ``load_dotenv(override=True)`` at line 24,
    **before** it imports this module at line 32, and ``token_dir()`` reads the
    environment at call time. So a single line in the repo's own untracked
    ``.env``::

        GTOS_ACTIVATION_TOKEN_DIR=<anywhere>

    relocates the authorization root, and ``ensure_signing_key`` will happily
    mint a fresh signing key there — no prior secret needed. The account digest
    is published in-tree (``config/profiles/operator_profile.yaml``), so a
    self-issued token for the live account verifies.

    That breaks the property this module claims for itself: that authorization
    "travels with the machine that is allowed to trade, not with the code."
    Write access to the **repository** was sufficient, not write access to the
    token directory. Measured and filed as B103.
    """

    try:
        resolved = token_dir(directory).expanduser().resolve()
        root = repo_root_for_activation(repo_root).resolve()
    except (OSError, RuntimeError, ValueError):
        # An unresolvable path is not a proof of safety. Say so; the caller
        # denies exposure-increasing requests, and risk-reducing ones never get
        # this far because they return before any token I/O.
        return True
    return resolved == root or root in resolved.parents


def token_path_for(account_login_sha256: str, *, directory: str | Path | None = None) -> Path:
    """One token per account. The filename is the account digest, so a token
    minted for one account cannot be silently consumed by another."""

    return token_dir(directory) / f"{account_login_sha256}.token.json"


def signing_key_path(directory: str | Path | None = None) -> Path:
    return token_dir(directory) / SIGNING_KEY_FILENAME


def audit_log_path(directory: str | Path | None = None) -> Path:
    return token_dir(directory) / AUDIT_LOG_FILENAME


# --------------------------------------------------------------------------
# Signing
# --------------------------------------------------------------------------


def load_signing_key(directory: str | Path | None = None) -> bytes | None:
    try:
        # Inside the try, not before it. `signing_key_path` -> `token_dir` ->
        # `Path.expanduser()`, which raises `RuntimeError` when `~` cannot be
        # resolved — so computing the path was itself a raise out of a function
        # contracted to return `None` when the key is unusable (B321).
        raw = signing_key_path(directory).read_text(encoding="utf-8").strip()
    except Exception:  # noqa: BLE001
        # Not just OSError. A key file with non-UTF-8 bytes raises
        # UnicodeDecodeError (a ValueError), which propagated out of
        # `authorize_broker_mutation` — documented as "Never raises" — and, worse,
        # out of `ensure_signing_key`, bricking the mint path so the operator
        # could not re-authorize without deleting the file by hand (B103/J3).
        return None
    return raw.encode("utf-8") if raw else None


def ensure_signing_key(directory: str | Path | None = None) -> bytes:
    """Return the signing key, creating a fresh random one if absent."""

    existing = load_signing_key(directory)
    if existing:
        return existing
    path = signing_key_path(directory)
    _mkdir_private(path.parent)
    key = secrets.token_hex(32)
    path.write_text(key + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return key.encode("utf-8")


def _mkdir_private(directory: Path) -> None:
    """Create the activation directory owner-only.

    ``mkdir`` used the default mode, leaving the directory 0o755 while the files
    inside it were 0o600 — so the signing key's own directory was world-readable
    and world-traversable. The files are what matter, but a 0o700 directory is
    free and removes the umask race between create and ``chmod`` (B103/#12).
    """

    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        directory.chmod(0o700)
    except OSError:
        pass


def canonical_payload(token: dict[str, Any]) -> str:
    """The exact bytes the signature covers."""

    return json.dumps(
        {name: token.get(name) for name in _SIGNED_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def sign_token(token: dict[str, Any], key: bytes) -> str:
    return hmac.new(key, canonical_payload(token).encode("utf-8"), hashlib.sha256).hexdigest()


# --------------------------------------------------------------------------
# Minting
# --------------------------------------------------------------------------


def build_token(
    *,
    account_login_sha256: str,
    expires_utc: datetime,
    namespace: str | None = None,
    config_digest_sha256: str | None = None,
    issued_by: str = "",
    note: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Assemble an unsigned token body. Raises on an unusable lifetime."""

    issued = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    expiry = expires_utc.astimezone(timezone.utc)
    lifetime_hours = (expiry - issued).total_seconds() / 3600.0
    if lifetime_hours <= 0:
        raise ValueError("activation token expiry must be in the future")
    if lifetime_hours > MAX_TOKEN_LIFETIME_HOURS:
        raise ValueError(
            f"activation token lifetime {lifetime_hours:.1f}h exceeds the "
            f"{MAX_TOKEN_LIFETIME_HOURS}h maximum; re-issue instead of extending"
        )
    return {
        "token_version": TOKEN_VERSION,
        "schema_version": 1,
        "namespace": namespace or None,
        "account_login_sha256": account_login_sha256,
        "config_digest_sha256": config_digest_sha256 or None,
        "issued_utc": issued.isoformat(),
        "not_before_utc": issued.isoformat(),
        "expires_utc": expiry.isoformat(),
        "issued_by": issued_by or "",
        "note": note or "",
    }


def write_token(token: dict[str, Any], *, directory: str | Path | None = None) -> Path:
    """Sign and persist a token. Returns the path written."""

    key = ensure_signing_key(directory)
    signed = dict(token)
    signed["signature"] = sign_token(signed, key)
    path = token_path_for(str(signed["account_login_sha256"]), directory=directory)
    _mkdir_private(path.parent)
    # Write-then-rename. An in-place truncate meant a concurrent reader could see
    # a half-written file: measured at ~1.2 % `activation_token_malformed` over
    # two seconds of concurrent mint+read, each one a legitimate entry refused
    # (B103/G2). Both books share one token directory, so the race is real.
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(signed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        tmp.chmod(0o600)
    except OSError:
        pass
    os.replace(str(tmp), str(path))
    return path


# --------------------------------------------------------------------------
# Request classification
# --------------------------------------------------------------------------


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value if value is not None else default)
    except (TypeError, ValueError):
        return default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except (TypeError, ValueError):
        return default


def _position_field(position: Any, name: str, default: Any = None) -> Any:
    """Positions arrive as ``PositionInfo`` from the adapter and as plain dicts
    from some callers/tests; read both the same way."""

    if isinstance(position, dict):
        return position.get(name, default)
    return getattr(position, name, default)


def _matching_position(positions: Iterable[Any], ticket: int) -> Any | None:
    for position in positions or ():
        if _int(_position_field(position, "ticket", 0)) == ticket:
            return position
    return None


def deal_request_is_structurally_a_close(request: dict) -> bool:
    """The conditions answerable without reading the broker.

    DEAL action, a real position ticket, positive volume — plus two bounds that
    exist because this predicate also gates the **unverified** escape hatch. When
    the broker cannot be read, a request that passes here is allowed with no
    token; so "structurally a close" has to actually exclude things that are
    structurally an opening, or the escape hatch is unbounded (B102/F-2).

    * ``type`` must be a market order type (0 BUY / 1 SELL). A close is always
      a market DEAL; every pending type is an opening.
    * the request must carry **no ``sl`` and no ``tp``**. Verified against all
      six close-request producers in this repo — ``execution.py:8147, 8201,
      8319, 8393, 8467, 8532, 8588``, ``heartbeat_monitor.py:693``,
      ``flatten_all_positions.py:46``, ``emergency_close_and_stop_redacted_account.py:289``,
      ``fn_smoke_trade.py:216`` — **none** carries either, while the entry
      request at ``execution.py:3444`` carries both and no ``position``. Opening
      geometry on a request claiming to be a close is a contradiction, and
      refusing it costs nothing real.
    """

    if _int(request.get("action")) != TRADE_ACTION_DEAL:
        return False
    if _int(request.get("position")) <= 0:
        return False
    if _float(request.get("volume")) <= 0:
        return False
    if _int(request.get("type"), -1) not in (0, 1):
        return False
    if _float(request.get("sl")) > 0 or _float(request.get("tp")) > 0:
        return False
    return True


def deal_reduces_existing_position(request: dict, positions: Sequence[Any]) -> bool:
    """The conditions from ``execution.py`` ``_request_reduces_existing_position``.

    DEAL + a real position ticket + positive volume + volume not exceeding the
    live position's volume + an opposing order type — **and the same symbol**. A
    two-condition approximation is materially weaker (C4), so this is the whole
    test and it is the single definition both call sites use.

    The symbol condition is not decoration. The activation provider reads the
    whole account rather than one symbol (so a magic- or symbol-filtered view
    cannot hide a position from a close), and ``_matching_position`` keys on
    ticket alone — so without this, a DEAL that **opens** a 1.00-lot EURUSD
    short while quoting an open XAUUSD long's ticket classified as
    ``risk_reducing_position_close`` and was allowed with no token (B102/F-1).
    Lots are not comparable across instruments either, so the volume bound is
    meaningless once the symbols differ.

    The check applies when **both** sides declare a symbol. A request with no
    symbol is not rejected here, because MT5 requires one on a DEAL and the
    codepath that would produce a symbol-less close does not exist; the residual
    is recorded rather than papered over.
    """

    if not deal_request_is_structurally_a_close(request):
        return False
    ticket = _int(request.get("position"))
    request_type = _int(request.get("type"), -1)
    volume = _float(request.get("volume"))
    position = _matching_position(positions, ticket)
    if position is None:
        return False
    request_symbol = str(request.get("symbol") or "")
    position_symbol = str(_position_field(position, "symbol", "") or "")
    if request_symbol and position_symbol and request_symbol != position_symbol:
        return False
    pos_type = _int(_position_field(position, "type", -1), -1)
    pos_volume = _float(_position_field(position, "volume", 0.0))
    # A non-finite position volume makes the bound vacuous: `100.0 - nan` is
    # `nan`, and `nan > 1e-9` is False, so an oversized "close" slipped through
    # (B102/F-8). A volume we cannot compare is a condition we cannot satisfy.
    if not math.isfinite(pos_volume) or not math.isfinite(volume):
        return False
    if volume - pos_volume > 1e-9:
        return False
    if pos_type == 0:
        return request_type == 1
    if pos_type == 1:
        return request_type == 0
    return False


def sltp_reduces_or_preserves_risk(request: dict, position: Any) -> bool:
    """A stop that moves toward the entry (or appears where there was none)
    reduces risk; widening or removing it does not. Take-profit changes do not
    move the loss side and so never make a modify exposure-increasing."""

    desired = _float(request.get("sl"))
    current = _float(_position_field(position, "sl", 0.0))
    if desired <= 0:
        # Clearing an EXISTING stop is risk-increasing and needs a token.
        # Carrying no stop where the position already has none is not: MT5's
        # SLTP sets both fields at once, so `execution._modify_tp` round-trips
        # `sl` unchanged (`execution.py:9833-9835`), and on a stopless position
        # that round-tripped value is 0. Refusing it would make a take-profit
        # *tighten* require a token — a risk-reducing act blocked by the token,
        # which is the failure this module exists to prevent.
        return current <= 0
    if current <= 0:
        return True
    # An unknown side fails CLOSED, matching `deal_reduces_existing_position`.
    # This used to default to 0 (LONG), so a SHORT whose stop was widened
    # *upward* read as tightened and passed with no token — the same field with
    # two different missing-value defaults, in opposite directions (B102/F-7).
    # A real MT5 position record always carries `type`, so nothing legitimate
    # lands here; it is the dict-shaped path `_position_field` exists to accept.
    pos_type = _int(_position_field(position, "type", -1), -1)
    if pos_type == 0:
        return desired >= current
    if pos_type == 1:
        return desired <= current
    return False


def classify_request(
    request: dict,
    positions_provider: Callable[[str], Sequence[Any]] | None = None,
) -> tuple[str, str, bool | None]:
    """Return ``(risk_direction, reason, positions_verified)`` for one request.

    ``positions_provider`` is called at most once, and only for the actions
    whose classification genuinely needs live position state — so a new entry
    (the common case) costs no extra broker round-trip.

    ``positions_verified`` is ``None`` when no position read was needed, ``True``
    when the broker's answer can be trusted, and ``False`` when the read could
    not be trusted (see ``_read_positions``). It exists so the audit row records
    *whether the classification rested on a real broker read* — which is the
    fact an operator needs when a flatten is refused.
    """

    action = _int(request.get("action"), -1)
    symbol = str(request.get("symbol") or "")

    if action == TRADE_ACTION_REMOVE:
        # Cancelling a working order removes potential exposure.
        return "reducing", "risk_reducing_pending_cancel", None

    if action == TRADE_ACTION_PENDING:
        return "increasing", "exposure_increasing_pending_placement", None

    if action == TRADE_ACTION_DEAL:
        if not deal_request_is_structurally_a_close(request):
            return "increasing", "exposure_increasing_new_deal", None
        positions, authoritative = _read_positions(positions_provider, symbol)
        if _matching_position(positions, _int(request.get("position"))) is None:
            if not authoritative:
                # Deliberate asymmetry. A DEAL naming an existing position ticket
                # is structurally a close; refusing it because the broker read
                # could not be trusted would let this mechanism block a flatten,
                # which is the one thing it must never do.
                return "reducing", "risk_reducing_position_close_unverified", False
            # An authoritative reader looked at the whole account and the ticket
            # is not there. That is not a close.
            return "increasing", "exposure_increasing_deal_on_position", True
        if deal_reduces_existing_position(request, positions):
            return "reducing", "risk_reducing_position_close", True
        return "increasing", "exposure_increasing_deal_on_position", True

    if action == TRADE_ACTION_SLTP:
        ticket = _int(request.get("position"))
        if ticket <= 0:
            return "increasing", "exposure_increasing_sltp_without_position", None
        positions, authoritative = _read_positions(positions_provider, symbol)
        position = _matching_position(positions, ticket)
        if position is None:
            if not authoritative:
                return "reducing", "risk_reducing_stop_modify_unverified", False
            return "increasing", "exposure_increasing_sltp_unknown_position", True
        if sltp_reduces_or_preserves_risk(request, position):
            return "reducing", "risk_reducing_stop_tightened", True
        return "increasing", "exposure_increasing_stop_widened", True

    if action == TRADE_ACTION_MODIFY:
        # Modifying a working order can move its entry, size or stop in either
        # direction; nothing here proves it reduces risk.
        return "increasing", "exposure_increasing_order_modify", None

    return "unknown", "exposure_increasing_unknown_action", None


def _read_positions(
    positions_provider: Callable[[str], Sequence[Any]] | None,
    symbol: str,
) -> tuple[Sequence[Any], bool]:
    """Return ``(positions, authoritative)``.

    ``authoritative`` answers one question only: **may "this ticket is not in
    the list" be read as "the broker does not have this position"?** It is True
    only when the read succeeded *and* the provider is marked
    ``@strict_positions_provider`` — i.e. it has promised to raise rather than
    return a lossy list when it cannot see the account.

    That is the repair. ``MetaTrader5.positions_get`` reports failure by
    returning ``None``; a provider that turns that into ``[]`` hands the gate a
    list indistinguishable from "the position is gone", and a close then
    classifies as new exposure and is refused with no token — the never-strand
    invariant failing in exactly the state it exists for (B101).

    Note it governs the *empty* and the *partial* case alike (B102/F-4). An
    unmarked provider returning three positions is no more trustworthy about a
    fourth one's absence than one returning none, so absence is never concluded
    from an unmarked reader. A ticket that IS present is decidable either way —
    finding it is positive evidence regardless of who did the looking.
    """

    if positions_provider is None:
        return (), False
    try:
        positions = positions_provider(symbol) or ()
    except Exception:  # noqa: BLE001 — a broker read failure must not raise here
        return (), False
    try:
        _ = len(positions)
    except Exception:  # noqa: BLE001 — a container we cannot even size is not an answer
        return (), False
    return positions, provider_is_authoritative(positions_provider)


# --------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------


def _parse_utc(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def read_token(
    account_login_sha256: str,
    *,
    directory: str | Path | None = None,
) -> tuple[dict[str, Any] | None, str, Path]:
    """Load one account's token. Returns ``(token, status, path)``."""

    path = token_path_for(account_login_sha256, directory=directory)
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, "activation_token_absent", path
    except Exception:  # noqa: BLE001 — a token file with non-UTF-8 bytes raises
        # UnicodeDecodeError, not OSError, and it escaped a function whose whole
        # contract is to return a status (B103/J2).
        return None, "activation_token_unreadable", path
    try:
        token = json.loads(raw)
    except (ValueError, TypeError):
        return None, "activation_token_malformed", path
    if not isinstance(token, dict):
        return None, "activation_token_malformed", path
    return token, "ok", path


def verify_token(
    token: dict[str, Any],
    *,
    account_login_sha256: str,
    namespace: str | None = None,
    config_digest_sha256: str | None = None,
    require_namespace_binding: bool = False,
    require_config_digest_binding: bool = False,
    directory: str | Path | None = None,
    now: datetime | None = None,
) -> tuple[bool, str, str]:
    """Return ``(ok, reason, detail)`` for a loaded token."""

    if str(token.get("token_version") or "") != TOKEN_VERSION:
        return False, "activation_token_version_unsupported", str(token.get("token_version"))

    key = load_signing_key(directory)
    if not key:
        return False, "activation_token_signing_key_absent", str(signing_key_path(directory))
    signature = str(token.get("signature") or "")
    try:
        # `hmac.compare_digest` raises TypeError on a non-ASCII str, so a token
        # whose signature field contains one crashed the gate instead of denying
        # it — including inside the operator's read-only `status` command
        # (B103/J1). A signature that is not a hex digest cannot match anyway.
        signature_matches = bool(signature) and hmac.compare_digest(signature, sign_token(token, key))
    except (TypeError, ValueError):
        signature_matches = False
    if not signature_matches:
        return False, "activation_token_signature_invalid", ""

    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    expires = _parse_utc(token.get("expires_utc"))
    if expires is None:
        return False, "activation_token_expiry_missing", ""
    if moment >= expires:
        return False, "activation_token_expired", f"expired {expires.isoformat()}"
    not_before = _parse_utc(token.get("not_before_utc"))
    if not_before is not None and moment < not_before:
        return False, "activation_token_not_yet_valid", f"valid from {not_before.isoformat()}"

    if str(token.get("account_login_sha256") or "") != str(account_login_sha256):
        return False, "activation_token_account_mismatch", ""

    # A binding the token declares must be satisfiable by the process. Being
    # unable to answer is a denial, never a pass — that is what keeps a token
    # minted for one namespace from authorizing a process that cannot say which
    # namespace it is.
    token_namespace = token.get("namespace")
    if require_namespace_binding and not token_namespace:
        return False, "activation_token_namespace_binding_required", str(namespace or "")
    if token_namespace:
        if not namespace:
            return False, "activation_token_namespace_unsatisfied", str(token_namespace)
        if str(namespace) != str(token_namespace):
            return False, "activation_token_namespace_mismatch", f"{namespace} != {token_namespace}"

    token_digest = token.get("config_digest_sha256")
    if require_config_digest_binding and not token_digest:
        return False, "activation_token_config_digest_binding_required", ""
    if token_digest:
        if not config_digest_sha256:
            return False, "activation_token_config_digest_unsatisfied", str(token_digest)
        if str(config_digest_sha256) != str(token_digest):
            return False, "activation_token_config_digest_mismatch", ""

    return True, "activation_token_valid", ""


# --------------------------------------------------------------------------
# The gate
# --------------------------------------------------------------------------


def authorize_broker_mutation(
    request: dict,
    *,
    account_login_sha256: str | None,
    positions_provider: Callable[[str], Sequence[Any]] | None = None,
    namespace: str | None = None,
    config_digest_sha256: str | None = None,
    require_namespace_binding: bool = False,
    require_config_digest_binding: bool = False,
    directory: str | Path | None = None,
    now: datetime | None = None,
    audit: bool = True,
) -> ActivationDecision:
    """Decide whether one broker request may proceed. Never raises."""

    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    summary = {
        "action": _int(request.get("action"), -1) if isinstance(request, dict) else None,
        "symbol": str((request or {}).get("symbol") or "") if isinstance(request, dict) else "",
        "type": _int((request or {}).get("type"), -1) if isinstance(request, dict) else None,
        "volume": _float((request or {}).get("volume")) if isinstance(request, dict) else None,
        "position": _int((request or {}).get("position")) if isinstance(request, dict) else None,
    }

    def _finish(decision: ActivationDecision) -> ActivationDecision:
        if audit:
            append_activation_audit(decision, directory=directory)
        return decision

    if not isinstance(request, dict):
        return _finish(ActivationDecision(
            allowed=False, reason="activation_request_malformed", risk_direction="unknown",
            decided_at_utc=moment.isoformat(), namespace=namespace, request_summary=summary,
        ))

    direction, classification, verified = classify_request(request, positions_provider)
    if direction == "reducing":
        return _finish(ActivationDecision(
            allowed=True, reason=classification, risk_direction=direction,
            decided_at_utc=moment.isoformat(), account_login_sha256=account_login_sha256,
            namespace=namespace, request_summary=summary,
            classification=classification, positions_verified=verified,
            detail="risk-reducing requests never require a token",
        ))

    if not account_login_sha256:
        return _finish(ActivationDecision(
            allowed=False, reason="activation_token_account_identity_unavailable",
            risk_direction=direction, decided_at_utc=moment.isoformat(),
            namespace=namespace, request_summary=summary,
            classification=classification, positions_verified=verified,
            detail="cannot identify the account this order would trade",
        ))

    # The authorization root must not live in the working tree. Checked HERE,
    # after the risk-reducing return above, so a misconfigured directory can
    # refuse new exposure but can never block a close (B103).
    if token_dir_is_inside_repo(directory):
        return _finish(ActivationDecision(
            allowed=False, reason="activation_token_dir_inside_repository",
            risk_direction=direction, decided_at_utc=moment.isoformat(),
            account_login_sha256=account_login_sha256, namespace=namespace,
            token_path=token_dir_display(directory), request_summary=summary,
            classification=classification, positions_verified=verified,
            detail=(f"{TOKEN_DIR_ENV_VAR} resolves inside the repository; authorization must "
                    f"travel with the machine, not with the code"),
        ))

    token, status, path = read_token(account_login_sha256, directory=directory)
    if token is None:
        return _finish(ActivationDecision(
            allowed=False, reason=status, risk_direction=direction,
            decided_at_utc=moment.isoformat(), account_login_sha256=account_login_sha256,
            namespace=namespace, token_path=str(path), request_summary=summary,
            classification=classification, positions_verified=verified,
        ))

    ok, reason, detail = verify_token(
        token,
        account_login_sha256=account_login_sha256,
        namespace=namespace,
        config_digest_sha256=config_digest_sha256,
        require_namespace_binding=require_namespace_binding,
        require_config_digest_binding=require_config_digest_binding,
        directory=directory,
        now=moment,
    )
    return _finish(ActivationDecision(
        allowed=ok, reason=reason, risk_direction=direction,
        decided_at_utc=moment.isoformat(), account_login_sha256=account_login_sha256,
        namespace=namespace, token_path=str(path),
        token_expires_utc=str(token.get("expires_utc") or "") or None,
        classification=classification, positions_verified=verified,
        detail=detail, request_summary=summary,
    ))


def enforce_broker_mutation_authorized(request: dict, **kwargs: Any) -> ActivationDecision:
    """``authorize_broker_mutation`` that raises ``ActivationTokenError`` on denial."""

    decision = authorize_broker_mutation(request, **kwargs)
    if not decision.allowed:
        raise ActivationTokenError(decision)
    return decision


def authorize_raw_broker_request(
    request: dict,
    *,
    mt5_module: Any,
    namespace: str | None = None,
    config: dict | None = None,
    config_digest_sha256: str | None = None,
    directory: str | Path | None = None,
    action: str = "raw_broker_order_send",
) -> ActivationDecision:
    """The same gate, for the scripts that drive the raw ``MetaTrader5`` module.

    ``fn_smoke_trade.py``, ``dual_broker_execution_follower.py`` and friends do
    not go through ``RealMT5``, so the choke-point check inside
    ``RealMT5.order_send`` cannot see them. They call this instead, and get the
    identical classification and the identical token rules.

    Two mechanisms compose here, and they deliberately differ:

    * the **halt** blocks everything, risk-reducing included. It is an
      intentional act by an operator who is present — the same reading the owner
      decided for the book's broker-authority gate on 2026-07-26, and the same
      one ``heartbeat_monitor.py:702-725`` already implements.
    * the **token** blocks only exposure-increasing requests, because it can
      lapse by expiry while nobody is watching, and an expired token must never
      be the reason a position cannot be closed.

    Raises ``RuntimeHaltError`` or ``ActivationTokenError``. Returns the decision
    on success.
    """

    from src.safety.runtime_halt import enforce_runtime_not_halted

    enforce_runtime_not_halted(
        action=action,
        config=config,
        context={
            "namespace": namespace,
            "symbol": (request or {}).get("symbol") if isinstance(request, dict) else None,
            "raw_module_path": True,
        },
        enabled_default=True,   # a raw-module script has no engine config to arm it
    )

    login_digest = None
    positions_provider = None
    if mt5_module is not None:
        try:
            info = mt5_module.account_info()
            login = getattr(info, "login", None) if info is not None else None
            if login:
                login_digest = account_digest(login)
        except Exception:  # noqa: BLE001
            login_digest = None

        @strict_positions_provider
        def positions_provider(symbol: str):  # noqa: F811
            # Unfiltered and unmasked, for the two reasons in
            # ``RealMT5.positions_for_activation``: the gate's question is
            # "does this ticket exist at the broker", and a ``None`` return is
            # a failed read, not an empty account. The previous
            # ``positions_get(symbol=symbol) or ()`` answered both wrongly.
            positions = mt5_module.positions_get()
            if positions is None:
                raise PositionsUnavailable(
                    "positions_get returned None — the broker read failed"
                )
            return positions

    return enforce_broker_mutation_authorized(
        request,
        account_login_sha256=login_digest,
        positions_provider=positions_provider,
        namespace=namespace,
        config_digest_sha256=config_digest_sha256,
        directory=directory,
    )


def append_activation_audit(
    decision: ActivationDecision,
    *,
    directory: str | Path | None = None,
) -> bool:
    """Best-effort JSONL audit row. Never raises: an unwritable audit directory
    must not be able to block a flatten."""

    try:
        path = audit_log_path(directory)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(decision.to_dict(), sort_keys=True, ensure_ascii=True) + "\n")
        return True
    except Exception:  # noqa: BLE001
        return False


def describe_activation_state(
    account_login_sha256: str | None = None,
    *,
    directory: str | Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Operator-facing summary. Read-only; touches no broker."""

    try:
        directory_path: Path | None = token_dir(directory)
    except (OSError, RuntimeError, ValueError):
        # An operator's read-only status command must not crash on the state it
        # exists to explain — an unresolvable activation directory is precisely
        # when they most need to be told which path was tried (B321).
        directory_path = None
    state: dict[str, Any] = {
        "token_dir": token_dir_display(directory),
        "token_dir_exists": bool(directory_path is not None and directory_path.is_dir()),
        "signing_key_present": load_signing_key(directory) is not None,
        "checked_at_utc": (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(),
        "tokens": [],
    }
    try:
        candidates = sorted(directory_path.glob("*.token.json")) if directory_path else []
    except OSError:
        candidates = []
    for candidate in candidates:
        digest = candidate.name.split(".", 1)[0]
        token, status, _path = read_token(digest, directory=directory)
        row: dict[str, Any] = {"path": str(candidate), "account_login_sha256": digest, "status": status}
        if token is not None:
            ok, reason, detail = verify_token(
                token,
                account_login_sha256=digest,
                namespace=token.get("namespace"),
                config_digest_sha256=token.get("config_digest_sha256"),
                directory=directory,
                now=now,
            )
            row.update({
                "valid": ok,
                "reason": reason,
                "detail": detail,
                "namespace": token.get("namespace"),
                "expires_utc": token.get("expires_utc"),
                "issued_utc": token.get("issued_utc"),
                "issued_by": token.get("issued_by"),
                "binds_config_digest": bool(token.get("config_digest_sha256")),
            })
        state["tokens"].append(row)
    if account_login_sha256:
        state["queried_account_login_sha256"] = account_login_sha256
        state["queried_account_has_token"] = any(
            row.get("account_login_sha256") == account_login_sha256 for row in state["tokens"]
        )
    return state


def account_digest(login: Any) -> str:
    """The account digest convention, identical to the one the profiles carry
    in ``broker_profile.expected_account.login_sha256``."""

    return sha256_text(login)


def profile_path_for(profile: str, *, repo_root: str | Path | None = None) -> Path:
    """``--profile operator_profile`` -> ``config/profiles/operator_profile.yaml``.
    An explicit path is passed through unchanged."""

    candidate = Path(profile)
    if candidate.suffix in {".yaml", ".yml"}:
        return candidate
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[2]
    return root / "config" / "profiles" / f"{profile}.yaml"


def _normalized_positive_decimal(value: Any, *, field_name: str) -> str:
    """Canonical finite positive decimal text for an authorization contract."""

    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field_name} must be a finite positive number, got {value!r}") from None
    if not decimal.is_finite() or decimal <= 0:
        raise ValueError(f"{field_name} must be a finite positive number, got {value!r}")
    normalized = format(decimal.normalize(), "f")
    return "0" if normalized in {"-0", "-0.0"} else normalized


def _normalized_tags(tags: str | Sequence[str] | None) -> tuple[str, ...]:
    if isinstance(tags, str):
        values = tags.split(",")
    elif tags is None:
        values = ()
    else:
        values = tags
    normalized = tuple(sorted({str(value).strip() for value in values if str(value).strip()}))
    if not normalized:
        raise ValueError(
            "an F5 launch contract requires an explicit non-empty --tags surface; "
            "omission is the launcher's fail-open all-sleeves route"
        )
    return normalized


def _optional_contract_decimal(value: Any) -> str | None:
    """Positive amounts stay canonical. Empty is absent.

    Missing, blank, and non-positive values are not a launch refuse and are
    not replaced with a planted amount.
    """

    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        return _normalized_positive_decimal(value, field_name="F5 contract field")
    except ValueError:
        return None


def normalized_f5_launch_contract(
    *,
    f5_enabled: bool,
    target_risk_usd: Any,
    notional_initial_usd: Any,
    tags: str | Sequence[str] | None,
    namespace: str | None,
    magic: Any,
    profile: str | None,
    q1_mode: str = "off",
    q1_selection: str | None = None,
    q2_enabled: bool = False,
) -> dict[str, Any] | None:
    """Return the semantic F5 argv contract, or ``None`` for a non-F5 worker.

    The contract is intentionally narrower than the whole command line: it binds
    the controls that define whether the F5 surface exists, what it can select,
    how much it can risk, and whether the two Phase-22 overlays can observe or
    apply. Poll cadence, terminal path, log paths and kill-flag paths do not alter
    that execution contract.

    A namespace ending in ``_f5_minimal`` is itself an F5 identity. A missing
    size or notional is omitted from the contract. It does not raise, and it
    is not filled in. When the argv still carries a size and a notional, those
    fields stay in the hashed JSON.
    """

    namespace_text = str(namespace or "").strip()
    try:
        magic_value = int(magic)
    except (TypeError, ValueError):
        raise ValueError(f"F5 broker magic is not an integer: {magic!r}") from None
    f5_identity = namespace_text.endswith("_f5_minimal") or magic_value == MAGIC_F5_MINIMAL
    if not f5_enabled and not f5_identity:
        return None
    if not namespace_text or not namespace_text.endswith("_f5_minimal"):
        raise ValueError(
            "--f5-minimal-size-usd requires a dedicated *_f5_minimal namespace"
        )
    if magic_value != MAGIC_F5_MINIMAL:
        raise ValueError(
            f"--f5-minimal-size-usd requires broker magic {MAGIC_F5_MINIMAL}, got {magic_value}"
        )
    profile_text = str(profile or "").strip()
    if not profile_text:
        raise ValueError("an F5 launch contract requires an explicit profile")
    selected_tags = _normalized_tags(tags)

    # Reuse Q1's parser so harmless argv reordering/default spelling hashes to
    # one contract while shadow -> apply or any policy change necessarily moves
    # it. The live launcher performs the stricter registry/profile intersection
    # immediately afterwards; this layer's job is canonical authorization.
    from src.components.ultimate_book.risk_unit_floor import policy_from_args

    q1_policy = policy_from_args(
        q1_mode,
        q1_selection,
        known_sleeves=selected_tags,
        effective_sleeves=selected_tags,
    )
    q1_sleeves = {
        sleeve: q1_policy.sleeves[sleeve].as_dict()
        for sleeve in sorted(q1_policy.sleeves)
    }
    f5_fields: dict[str, Any] = {"enabled": True}
    target_risk_text = _optional_contract_decimal(target_risk_usd)
    notional_text = _optional_contract_decimal(notional_initial_usd)
    if target_risk_text is not None:
        f5_fields["target_risk_usd"] = target_risk_text
    if notional_text is not None:
        f5_fields["notional_initial_usd"] = notional_text
    return {
        "schema": F5_LAUNCH_CONTRACT_SCHEMA,
        "f5": f5_fields,
        "selected_tags": list(selected_tags),
        "namespace": namespace_text,
        "magic": magic_value,
        "profile": profile_path_for(profile_text).name,
        "q1": {"mode": q1_policy.mode, "sleeves": q1_sleeves},
        "q2": {
            "enabled": bool(q2_enabled),
            "effect": "observation_only" if q2_enabled else "off",
        },
    }


def launch_contract_digest_for(contract: Mapping[str, Any]) -> str:
    """SHA-256 of a normalized launch contract's canonical JSON bytes."""

    if not isinstance(contract, Mapping):
        raise TypeError("launch contract must be a mapping")
    payload = json.dumps(
        dict(contract),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def config_digest_for(
    config_path: str | Path,
    profile: str | None = None,
    *,
    repo_root: str | Path | None = None,
    launch_contract: Mapping[str, Any] | None = None,
) -> str | None:
    """Digest of the config that defines the live decision surface.

    Deliberately over **file bytes**, not a merged dict: the mint tool and the
    running entrypoint must agree exactly, and reproducing the merge in two
    places is how they would silently drift. Hashing the base config plus the
    active profile overlay means any edit to the risk dial, the gates, or the
    account contract invalidates the token and forces re-authorization — which
    is the property worth having. An F5 caller additionally supplies its
    normalized argv contract; its digest is composed into the same signed token
    field, so existing non-F5 digests and tokens remain byte-for-byte compatible.
    Returns ``None`` if a file cannot be read, so the caller reports "cannot
    bind" rather than binding to a wrong value.
    """

    parts: list[str] = []
    for path in (Path(config_path), profile_path_for(profile, repo_root=repo_root) if profile else None):
        if path is None:
            continue
        try:
            parts.append(f"{path.name}:{hashlib.sha256(path.read_bytes()).hexdigest()}")
        except OSError:
            return None
    if launch_contract is not None:
        parts.append(f"launch_contract:{launch_contract_digest_for(launch_contract)}")
    if not parts:
        return None
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
