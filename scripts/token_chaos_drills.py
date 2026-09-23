#!/usr/bin/env python3
"""Run the token chaos drills specified in ``phase3/TOKEN_CHAOS_DRILLS.md``.

**Read-only, broker-free.** This script never imports the real ``MetaTrader5``
package, never constructs a connected adapter, and never writes anywhere except
a temporary directory and the receipt path it is asked to write. Every drill
that needs an MT5 module is given a fake one that fails the way the real module
documents itself as failing (``positions_get`` returns ``None``).

Why a harness rather than more unit tests
-----------------------------------------
``tests/safety/test_activation_never_strand.py`` already covers the *mechanism*.
The drill spec asks for the *end-to-end* version and, crucially, for a **raw
observation** per drill rather than an assertion — because two of the eight can
only fail in ways that cost money, and a green test tells an operator nothing
about which of three MT5 behaviours actually occurred.

So each drill here records what it saw, then judges it. The receipt carries the
observation whether the verdict is PASS or FAIL, and a drill that cannot run on
this machine says so explicitly instead of being silently skipped — a skipped
drill and a passed drill are indistinguishable in a summary line, which is the
same defect as an alert that never fires.

Usage:
    python3 scripts/token_chaos_drills.py                       # run + print
    python3 scripts/token_chaos_drills.py --receipts-dir DIR    # write receipts

Exit codes: 0 = every runnable drill passed; 1 = at least one FAIL; 2 = harness
could not evaluate.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import stat
import sys
import tempfile
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.safety import activation_token as at  # noqa: E402
from src.safety.activation_token import (  # noqa: E402
    ActivationTokenError,
    PositionsUnavailable,
    account_digest,
    strict_positions_provider,
)
from src.mt5.mt5_real import RealMT5  # noqa: E402

TRADE_ACTION_DEAL = 1
TRADE_ACTION_SLTP = 6
TRADE_ACTION_REMOVE = 8

TICKET = 777_001
LOGIN = 531_325_516                      # the live FTMO login, digest only; nothing connects
DIGEST = account_digest(LOGIN)

CLOSE_LONG = {"action": TRADE_ACTION_DEAL, "symbol": "XAUUSD", "type": 1,
              "volume": 0.10, "position": TICKET}
TIGHTEN_STOP = {"action": TRADE_ACTION_SLTP, "symbol": "XAUUSD",
                "position": TICKET, "sl": 1940.0}
CANCEL_PENDING = {"action": TRADE_ACTION_REMOVE, "symbol": "XAUUSD", "order": 4242}
NEW_ENTRY = {"action": TRADE_ACTION_DEAL, "symbol": "XAUUSD", "type": 0,
             "volume": 0.10, "sl": 1900.0, "tp": 2000.0}


# --------------------------------------------------------------------------
# Broker stand-ins
# --------------------------------------------------------------------------


class FakePosition:
    def __init__(self, ticket=TICKET, symbol="XAUUSD", type=0, volume=0.10, sl=1900.0):
        self.ticket = ticket
        self.symbol = symbol
        self.type = type
        self.volume = volume
        self.price_open = 1950.0
        self.sl = sl
        self.tp = 2000.0
        self.profit = 0.0
        self.magic = 20260401
        self.comment = ""
        self.time = 1_750_000_000


class FakeResult:
    retcode, order, volume, price = 10009, 12345, 0.10, 1950.0
    comment, deal, request_id, retcode_external = "done", 999, 1, None


class FakeMT5Module:
    """A ``MetaTrader5`` stand-in that fails the way the real one documents.

    ``positions_mode``: ``ok`` returns the list; ``none`` returns ``None`` (the
    real module's failure signal); ``raise`` raises; ``stale`` returns a
    non-empty tuple that does **not** contain the live ticket — the answer D-8
    calls dangerous, modelled here so the consequence is measurable without a
    terminal.
    """

    def __init__(self, positions=None, positions_mode="ok", login=LOGIN):
        self.sent: list[dict] = []
        self._positions = [FakePosition()] if positions is None else positions
        self._mode = positions_mode
        self._login = login
        self.positions_get_calls = 0

    def order_send(self, request):
        self.sent.append(dict(request))
        return FakeResult()

    def positions_get(self, symbol=None):
        self.positions_get_calls += 1
        if self._mode == "raise":
            raise RuntimeError("broker read failed")
        if self._mode == "none":
            return None
        if self._mode == "stale":
            return (FakePosition(ticket=TICKET + 9_999),)
        return list(self._positions)

    def account_info(self):
        return types.SimpleNamespace(login=self._login)


def adapter_for(module: FakeMT5Module) -> RealMT5:
    """A ``RealMT5`` wired to a fake module. Never calls ``connect()``."""

    adapter = RealMT5.__new__(RealMT5)
    adapter._mt5 = module
    adapter._connected = True
    adapter._broker_offset_detected = True
    adapter._broker_offset_seconds = 0
    adapter.set_activation_context()
    return adapter


def send_through_adapter(adapter: RealMT5, request: dict) -> dict:
    """Drive the real choke point and record what came back, raw."""

    try:
        result = adapter.order_send(dict(request))
        return {"reached_broker": True, "retcode": getattr(result, "retcode", None),
                "raised": None, "reason": None}
    except ActivationTokenError as exc:
        return {"reached_broker": False, "retcode": None,
                "raised": "ActivationTokenError", "reason": exc.decision.reason,
                "classification": exc.decision.classification,
                "positions_verified": exc.decision.positions_verified}
    except BaseException as exc:  # noqa: BLE001 — an unexpected raise IS the finding
        return {"reached_broker": False, "retcode": None,
                "raised": type(exc).__name__, "reason": repr(exc)[:300]}


def mint(directory: Path, *, hours=1.0, digest=DIGEST, now=None, namespace=None) -> Path:
    issued = now or datetime.now(timezone.utc)
    token = at.build_token(
        account_login_sha256=digest,
        expires_utc=issued + timedelta(hours=hours),
        namespace=namespace,
        issued_by="token_chaos_drills",
        note="drill",
        now=issued,
    )
    return at.write_token(token, directory=directory)


def mint_and_reload(directory: Path, body: dict) -> dict:
    """Write a token body, then read back what a live process would read.

    ``write_token`` signs a **copy** (``signed = dict(token)``), so the caller's
    dict never gains a ``signature``. Verifying the caller's dict therefore
    reports ``activation_token_signature_invalid`` for every sub-case and hides
    whatever the drill was actually testing — which is what the first run of
    D-4 did, three false FAILs in a row.
    """

    at.write_token(body, directory=directory)
    token, status, _path = at.read_token(str(body["account_login_sha256"]), directory=directory)
    if token is None:
        raise RuntimeError(f"token unreadable straight after mint: {status}")
    return token


# --------------------------------------------------------------------------
# Receipt shape
# --------------------------------------------------------------------------


def receipt(drill_id, title, environment, status, criteria, observations, failure_means, notes=None):
    return {
        "schema": "gtos.token_chaos_drill_receipt.v1",
        "drill": drill_id,
        "title": title,
        "environment_required": environment,
        "environment_here": "macOS laptop, no MT5 terminal, no broker connection",
        "status": status,
        "criteria": criteria,
        "observations": observations,
        "what_a_failure_means": failure_means,
        "notes": notes or [],
    }


def judge(criteria):
    return "PASS" if all(c["ok"] for c in criteria) else "FAIL"


# --------------------------------------------------------------------------
# D-1 — Gate flip without a token
# --------------------------------------------------------------------------


def _import_monitor_books():
    """Import ``.tools/monitor_books.py`` with the broker package stubbed.

    The module is on the never-execute list and imports ``MetaTrader5`` at line
    24. Importing it under a stub runs no broker code — ``main()`` is behind
    ``__main__`` — and is the same pattern ``tests/safety/test_gate_tripwire.py``
    uses.
    """

    stub = types.ModuleType("MetaTrader5")
    for name in ("initialize", "shutdown", "account_info", "positions_get",
                 "history_deals_get", "symbol_info", "last_error"):
        setattr(stub, name, lambda *a, **k: None)
    saved = sys.modules.get("MetaTrader5")
    sys.modules["MetaTrader5"] = stub
    try:
        spec = importlib.util.spec_from_file_location(
            "_monitor_books_drill", REPO / ".tools" / "monitor_books.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, saved
    except BaseException:
        if saved is None:
            sys.modules.pop("MetaTrader5", None)
        else:
            sys.modules["MetaTrader5"] = saved
        raise


def drill_d1(tmp: Path) -> dict:
    """Four gates true, no token: does it trade, and does anyone find out?"""

    obs, crit = [], []
    token_dir = tmp / "d1_activation"
    token_dir.mkdir(parents=True, exist_ok=True)
    os.environ[at.TOKEN_DIR_ENV_VAR] = str(token_dir)

    # (a)/(b) the request itself
    module = FakeMT5Module()
    entry = send_through_adapter(adapter_for(module), NEW_ENTRY)
    obs.append({"step": "a/b — entry with all gates true and an empty token dir",
                "raw": entry, "fake_module_order_send_calls": len(module.sent)})
    crit.append({"criterion": "(a) the request does not reach the broker module",
                 "expected": "no order_send call", "observed": f"{len(module.sent)} call(s)",
                 "ok": len(module.sent) == 0})
    crit.append({"criterion": "(b) the refusal reason is activation_token_absent",
                 "expected": "activation_token_absent", "observed": entry.get("reason"),
                 "ok": entry.get("reason") == "activation_token_absent"})

    # (c) does the tripwire see the edited config?
    scratch = tmp / "d1_repo"
    (scratch / "config").mkdir(parents=True, exist_ok=True)
    text = (REPO / "config" / "agent_config.yaml").read_text(encoding="utf-8")
    flipped = (text
               .replace("ultimate_book_live_activation_allowed: false",
                        "ultimate_book_live_activation_allowed: true")
               .replace("ultimate_book_apply_to_execution: true",
                        "ultimate_book_apply_to_execution: true\n  "
                        "ultimate_book_live_broker_authority: true"))
    (scratch / "config" / "agent_config.yaml").write_text(flipped, encoding="utf-8")

    monitor, saved_mt5 = _import_monitor_books()
    try:
        original_root = monitor.REPO_ROOT
        monitor.REPO_ROOT = str(scratch)
        try:
            alerts = list(monitor.gate_tripwire())
        finally:
            monitor.REPO_ROOT = original_root
        gate_alerts = [a for a in alerts if "AUTHORITY GATE CHANGED ON DISK" in a]
        naming_activation = [a for a in gate_alerts if "live_activation_allowed" in a]
        obs.append({"step": "c — gate_tripwire() against the flipped config",
                    "raw": alerts[:8], "n_alerts": len(alerts)})
        crit.append({"criterion": "(c) at least one AUTHORITY GATE CHANGED alert naming "
                                  "live_activation_allowed",
                     "expected": ">=1", "observed": len(naming_activation),
                     "ok": len(naming_activation) >= 1})

        # (d) does that alert reach send()?
        delivered: list[str] = []
        original_send = monitor.send
        try:
            from src.safety import notification_authorization as na
            auth_before = na.delivery_authorization()
            auth_detail = {"authorized": bool(auth_before.authorized),
                           "detail": getattr(auth_before, "detail", None),
                           "reason": getattr(auth_before, "reason", None)}
        except Exception as exc:  # noqa: BLE001
            auth_detail = {"error": repr(exc)}

        monitor.send = lambda msg: delivered.append(msg)
        try:
            for alert in gate_alerts:
                monitor.send(alert)
        finally:
            monitor.send = original_send
        obs.append({"step": "d — delivery path", "raw": {
            "monitor.send is callable": callable(original_send),
            "alerts handed to send()": len(delivered),
            "notification delivery authorization in THIS process": auth_detail,
        }})
        crit.append({"criterion": "(d) the alert reaches send()",
                     "expected": "every gate alert handed to send()",
                     "observed": f"{len(delivered)}/{len(gate_alerts)}",
                     "ok": bool(gate_alerts) and len(delivered) == len(gate_alerts)})
    finally:
        if saved_mt5 is None:
            sys.modules.pop("MetaTrader5", None)
        else:
            sys.modules["MetaTrader5"] = saved_mt5

    return receipt(
        "D-1", "Gate flip without a token", "laptop", judge(crit), crit, obs,
        "the presence-of-authorization design does not hold: config alone is sufficient to "
        "trade. That is the entire premise of Stage 0, so a failure here stops the programme.",
        notes=[
            "The config edit is made in a SCRATCH copy; config/agent_config.yaml is "
            "R2-decision-contract-bound (H1) and is never touched.",
            "(d) proves the alert reaches the send() seam. Whether send() then delivers "
            "depends on this process holding a notification-delivery grant "
            "(src/safety/notification_authorization.py); the observed grant state is recorded above. "
            "This harness deliberately does NOT grant it — a drill must not page the owner.",
        ])


# --------------------------------------------------------------------------
# D-2 — Expiry mid-position + a broker fetch error
# --------------------------------------------------------------------------


def drill_d2(tmp: Path) -> dict:
    """The half of D-2 that is decidable without a terminal.

    D-2 asks two questions welded together: *does a lapsed token plus a failed
    read block a close* (Python-side, decidable here) and *does killing a real
    terminal actually produce the ``None`` the mechanism assumes* (D-8, not
    decidable here). This runs the first and says so.
    """

    obs, crit = [], []
    token_dir = tmp / "d2_activation"
    token_dir.mkdir(parents=True, exist_ok=True)
    os.environ[at.TOKEN_DIR_ENV_VAR] = str(token_dir)

    # A token that has already lapsed: minted in the past, expiring in the past.
    past = datetime.now(timezone.utc) - timedelta(hours=3)
    token = at.build_token(account_login_sha256=DIGEST,
                           expires_utc=past + timedelta(hours=1),
                           issued_by="token_chaos_drills", now=past)
    path = at.write_token(token, directory=token_dir)
    obs.append({"step": "setup", "raw": {"token": str(path),
                                         "expires_utc": token["expires_utc"],
                                         "state": "expired before the drill begins"}})

    module = FakeMT5Module(positions_mode="none")     # positions_get -> None
    adapter = adapter_for(module)
    close = send_through_adapter(adapter, CLOSE_LONG)
    obs.append({"step": "close, token expired, positions_get returns None",
                "raw": close, "order_send_calls": len(module.sent)})
    crit.append({"criterion": "the close is allowed", "expected": "reaches the broker",
                 "observed": close, "ok": close["reached_broker"] is True})
    crit.append({"criterion": "order_send is actually called once",
                 "expected": 1, "observed": len(module.sent), "ok": len(module.sent) == 1})

    # The decision itself, for reason + positions_verified.
    decision = at.authorize_broker_mutation(
        dict(CLOSE_LONG), account_login_sha256=DIGEST,
        positions_provider=adapter.positions_for_activation, directory=token_dir, audit=False)
    obs.append({"step": "ActivationDecision for that close", "raw": decision.to_dict()})
    crit.append({"criterion": "reason is risk_reducing_position_close_unverified",
                 "expected": "risk_reducing_position_close_unverified",
                 "observed": decision.reason,
                 "ok": decision.reason == "risk_reducing_position_close_unverified"})
    crit.append({"criterion": "positions_verified is False",
                 "expected": False, "observed": decision.positions_verified,
                 "ok": decision.positions_verified is False})

    # The same state must still refuse new exposure.
    entry = send_through_adapter(adapter_for(FakeMT5Module(positions_mode="none")), NEW_ENTRY)
    obs.append({"step": "control — a new entry in the identical state", "raw": entry})
    crit.append({"criterion": "an entry is still refused (the escape hatch is not a bypass)",
                 "expected": "activation_token_expired", "observed": entry.get("reason"),
                 "ok": entry.get("reason") == "activation_token_expired"})

    return receipt(
        "D-2", "Expiry mid-position, plus a broker fetch error", "demo account",
        judge(crit), crit, obs,
        "the never-strand invariant is broken in exactly the state it exists for.",
        notes=[
            "PARTIAL. The Python-side half ran here with a fake module returning None. "
            "The half that needs a demo terminal is D-8's question — whether killing "
            "terminal64.exe actually produces None rather than an exception, a hang, or a "
            "stale tuple. See the D-8 receipt: the stale-tuple branch is measured here and "
            "it STRANDS the close.",
        ])


# --------------------------------------------------------------------------
# D-3 — Activation directory unreadable
# --------------------------------------------------------------------------


def drill_d3(tmp: Path) -> dict:
    """Four broken token directories. A close must survive all four."""

    obs, crit = [], []

    regular_file = tmp / "d3_regular_file"
    regular_file.write_text("not a directory\n", encoding="utf-8")

    broken_link = tmp / "d3_broken_symlink"
    try:
        broken_link.symlink_to(tmp / "does_not_exist_ever")
    except OSError:
        broken_link = None

    no_perm = tmp / "d3_no_permissions"
    no_perm.mkdir(parents=True, exist_ok=True)
    os.chmod(no_perm, 0o000)

    cases = [
        ("a. token dir is a regular file", regular_file),
        ("b. token dir is a broken symlink", broken_link),
        ("c. token dir has no permissions", no_perm),
        ("d. token dir under a nonexistent user's home", Path("~nosuchuser/act")),
    ]

    try:
        for label, directory in cases:
            if directory is None:
                obs.append({"step": label, "raw": "could not create the fixture on this filesystem"})
                continue
            os.environ[at.TOKEN_DIR_ENV_VAR] = str(directory)

            # Instrument read_token: on the risk-reducing path it must not be called at all.
            calls: list[str] = []
            original_read = at.read_token
            at.read_token = lambda *a, **k: (calls.append("read_token"), original_read(*a, **k))[1]
            try:
                module = FakeMT5Module()
                close = send_through_adapter(adapter_for(module), dict(CLOSE_LONG))
                close_reads = len(calls)
                calls.clear()
                entry = send_through_adapter(adapter_for(FakeMT5Module()), dict(NEW_ENTRY))
                entry_reads = len(calls)
            finally:
                at.read_token = original_read

            obs.append({"step": label, "raw": {
                "token_dir": str(directory), "close": close, "entry": entry,
                "read_token calls during the close": close_reads,
                "read_token calls during the entry": entry_reads}})
            crit.append({"criterion": f"{label}: the close is allowed",
                         "expected": "reaches the broker", "observed": close,
                         "ok": close["reached_broker"] is True})
            crit.append({"criterion": f"{label}: read_token is NOT called for the close",
                         "expected": 0, "observed": close_reads, "ok": close_reads == 0})
            crit.append({"criterion": f"{label}: the entry is refused",
                         "expected": "refused", "observed": entry.get("reason"),
                         "ok": entry["reached_broker"] is False})
            crit.append({"criterion": f"{label}: nothing raises but ActivationTokenError",
                         "expected": "ActivationTokenError or nothing",
                         "observed": {"close": close.get("raised"), "entry": entry.get("raised")},
                         "ok": close.get("raised") in (None, "ActivationTokenError")
                               and entry.get("raised") in (None, "ActivationTokenError")})
    finally:
        try:
            os.chmod(no_perm, 0o700)
        except OSError:
            pass

    return receipt(
        "D-3", "Activation directory unreadable", "laptop", judge(crit), crit, obs,
        "the risk-reducing return is not actually ahead of the filesystem work, and a "
        "misconfigured directory can strand a position.",
        notes=["read_token is instrumented rather than inferred: the pass criterion is that "
               "the close returns BEFORE any token I/O, which a reason string alone cannot show."])


# --------------------------------------------------------------------------
# D-4 — Clock skew
# --------------------------------------------------------------------------


def drill_d4(tmp: Path) -> dict:
    obs, crit = [], []
    token_dir = tmp / "d4_activation"
    token_dir.mkdir(parents=True, exist_ok=True)
    os.environ[at.TOKEN_DIR_ENV_VAR] = str(token_dir)
    true_now = datetime.now(timezone.utc)

    # (a) minted on a clock four years fast, verified at the true time.
    skewed = true_now + timedelta(days=365 * 4)
    token_a = mint_and_reload(token_dir, at.build_token(
        account_login_sha256=DIGEST, expires_utc=skewed + timedelta(hours=1),
        issued_by="drill", now=skewed))
    ok_a, reason_a, detail_a = at.verify_token(
        token_a, account_login_sha256=DIGEST, directory=token_dir, now=true_now)
    obs.append({"step": "a — mint on a clock 4 years fast, verify at true time",
                "raw": {"issued_utc": token_a["issued_utc"], "not_before_utc": token_a["not_before_utc"],
                        "expires_utc": token_a["expires_utc"],
                        "verify": {"ok": ok_a, "reason": reason_a, "detail": detail_a}}})
    crit.append({"criterion": "(a) a fast mint cannot buy a valid future token",
                 "expected": "activation_token_not_yet_valid", "observed": reason_a,
                 "ok": (not ok_a) and reason_a == "activation_token_not_yet_valid"})

    # (b) minted normally, verified on a clock far in the future.
    token_b = mint_and_reload(token_dir, at.build_token(
        account_login_sha256=DIGEST, expires_utc=true_now + timedelta(hours=1),
        issued_by="drill", now=true_now))
    ok_b, reason_b, _ = at.verify_token(
        token_b, account_login_sha256=DIGEST, directory=token_dir,
        now=true_now + timedelta(days=365 * 4))
    obs.append({"step": "b — verify on a clock 4 years fast",
                "raw": {"ok": ok_b, "reason": reason_b}})
    crit.append({"criterion": "(b) a fast verify clock expires the token",
                 "expected": "activation_token_expired", "observed": reason_b,
                 "ok": (not ok_b) and reason_b == "activation_token_expired"})

    # (c) an expiry carrying a broker-local offset instead of Z.
    offset_tz = timezone(timedelta(hours=3))
    body_c = at.build_token(account_login_sha256=DIGEST,
                            expires_utc=true_now + timedelta(hours=1),
                            issued_by="drill", now=true_now)
    body_c["expires_utc"] = (true_now + timedelta(hours=1)).astimezone(offset_tz).isoformat()
    token_c = mint_and_reload(token_dir, body_c)
    ok_c, reason_c, _ = at.verify_token(
        token_c, account_login_sha256=DIGEST, directory=token_dir, now=true_now)
    ok_c_late, reason_c_late, _ = at.verify_token(
        token_c, account_login_sha256=DIGEST, directory=token_dir,
        now=true_now + timedelta(hours=2))
    parsed = at._parse_utc(token_c["expires_utc"])
    obs.append({"step": "c — expiry stamped +03:00 rather than Z",
                "raw": {"expires_utc_field": token_c["expires_utc"],
                        "parsed_as_utc": parsed.isoformat() if parsed else None,
                        "verify_before_expiry": {"ok": ok_c, "reason": reason_c},
                        "verify_after_expiry": {"ok": ok_c_late, "reason": reason_c_late}}})
    crit.append({"criterion": "(c) an offset-stamped expiry parses aware and compares against UTC",
                 "expected": "valid before expiry, expired after",
                 "observed": {"before": reason_c, "after": reason_c_late},
                 "ok": ok_c and (not ok_c_late) and reason_c_late == "activation_token_expired"})

    # Beyond the spec: a naive (tz-less) expiry must not become a wildcard.
    body_d = at.build_token(account_login_sha256=DIGEST,
                            expires_utc=true_now + timedelta(hours=1),
                            issued_by="drill", now=true_now)
    body_d["expires_utc"] = (true_now - timedelta(hours=1)).replace(tzinfo=None).isoformat()
    token_d = mint_and_reload(token_dir, body_d)
    ok_d, reason_d, _ = at.verify_token(
        token_d, account_login_sha256=DIGEST, directory=token_dir, now=true_now)
    obs.append({"step": "d (beyond spec) — a naive, already-past expiry",
                "raw": {"expires_utc_field": token_d["expires_utc"],
                        "ok": ok_d, "reason": reason_d}})
    crit.append({"criterion": "(d) a naive expiry is read as UTC and still fails closed "
                              "on EXPIRY, not merely on signature",
                 "expected": "activation_token_expired", "observed": reason_d,
                 "ok": (not ok_d) and reason_d == "activation_token_expired"})

    return receipt(
        "D-4", "Clock skew", "laptop", judge(crit), crit, obs,
        "in (a): a clock change is an authorization bypass, which is a far cheaper attack "
        "than editing a signed token.",
        notes=["Sub-case (d) is not in the spec. It was added because `_parse_utc` "
               "back-fills a missing tzinfo with UTC, and a token whose expiry lost its "
               "suffix in transit must not become unbounded."])


# --------------------------------------------------------------------------
# D-5 — Revoke and restore
# --------------------------------------------------------------------------


def drill_d5(tmp: Path) -> dict:
    obs, crit = [], []
    token_dir = tmp / "d5_activation"
    token_dir.mkdir(parents=True, exist_ok=True)
    os.environ[at.TOKEN_DIR_ENV_VAR] = str(token_dir)

    def entry_reason():
        return send_through_adapter(adapter_for(FakeMT5Module()), dict(NEW_ENTRY))

    path = mint(token_dir)
    first = entry_reason()
    obs.append({"step": "1 — mint, then send an entry", "raw": first})
    crit.append({"criterion": "a minted token authorizes an entry",
                 "expected": "reaches the broker", "observed": first,
                 "ok": first["reached_broker"] is True})

    path.unlink()                                    # revoke == remove the token
    revoked = entry_reason()
    obs.append({"step": "2 — revoke (token removed), send again", "raw": revoked})
    crit.append({"criterion": "revocation is effective on the very next request, no restart",
                 "expected": "activation_token_absent", "observed": revoked.get("reason"),
                 "ok": revoked.get("reason") == "activation_token_absent"})

    mint(token_dir)
    remint = entry_reason()
    obs.append({"step": "3 — re-mint, send again", "raw": remint})
    crit.append({"criterion": "re-authorization works after a revoke",
                 "expected": "reaches the broker", "observed": remint,
                 "ok": remint["reached_broker"] is True})

    # The harder half: delete the signing key with a token still on disk.
    surviving = at.token_path_for(DIGEST, directory=token_dir).read_text(encoding="utf-8")
    at.signing_key_path(token_dir).unlink()
    no_key = entry_reason()
    obs.append({"step": "4 — signing.key deleted, old token still present", "raw": no_key})
    crit.append({"criterion": "with no key present the old token does not verify",
                 "expected": "not allowed", "observed": no_key.get("reason"),
                 "ok": no_key["reached_broker"] is False})

    # A fresh mint generates a new key; the surviving old token must then be invalid,
    # not "valid under the new key".
    mint(token_dir)
    at.token_path_for(DIGEST, directory=token_dir).write_text(surviving, encoding="utf-8")
    stale = entry_reason()
    obs.append({"step": "5 — new key minted, then the OLD token restored on top", "raw": stale})
    crit.append({"criterion": "the old token reports signature_invalid, not valid",
                 "expected": "activation_token_signature_invalid", "observed": stale.get("reason"),
                 "ok": stale.get("reason") == "activation_token_signature_invalid"})

    # (e) a corrupt, non-UTF-8 key must not brick the mint path.
    at.signing_key_path(token_dir).write_bytes(b"\xff\xfe\x00")
    try:
        mint(token_dir)
        minted_over_corrupt, mint_error = True, None
    except BaseException as exc:  # noqa: BLE001
        minted_over_corrupt, mint_error = False, repr(exc)[:200]
    recovered = entry_reason()
    obs.append({"step": "e — corrupt (non-UTF-8) signing.key, then mint",
                "raw": {"mint_succeeded": minted_over_corrupt, "error": mint_error,
                        "entry_after": recovered}})
    crit.append({"criterion": "(e) a corrupt key file does not brick the mint path",
                 "expected": "mint succeeds and the operator can re-authorize",
                 "observed": {"mint": minted_over_corrupt, "entry": recovered.get("reason")},
                 "ok": minted_over_corrupt and recovered["reached_broker"] is True})

    # And the invariant that outranks all of it: none of these states blocks a close.
    closes = []
    for state in ("after revoke", "after key deletion", "after corrupt key"):
        closes.append({"state": state,
                       "close": send_through_adapter(adapter_for(FakeMT5Module()), dict(CLOSE_LONG))})
    obs.append({"step": "invariant — a close in each broken state", "raw": closes})
    crit.append({"criterion": "no step leaves a position unclosable",
                 "expected": "every close reaches the broker",
                 "observed": [c["close"]["reached_broker"] for c in closes],
                 "ok": all(c["close"]["reached_broker"] for c in closes)})

    return receipt(
        "D-5", "Revoke and restore", "laptop", judge(crit), crit, obs,
        "revocation is not immediate, or an operator can be left unable to re-authorize.",
        notes=["'Revoke' is modelled as removing the token file — the operation "
               "scripts/gtos_activation_token.py exposes. There is no revocation list; "
               "absence IS revocation, which is why step 2 is the whole test."])


# --------------------------------------------------------------------------
# D-6 — Wrong user
# --------------------------------------------------------------------------


def drill_d6(tmp: Path) -> dict:
    """The portable half of D-6: does the default token dir follow the user?"""

    obs, crit = [], []
    os.environ.pop(at.TOKEN_DIR_ENV_VAR, None)

    home_a, home_b = tmp / "home_userA", tmp / "home_userB"
    for home in (home_a, home_b):
        (home / ".gtos" / "activation").mkdir(parents=True, exist_ok=True)

    saved_home = os.environ.get("HOME")
    try:
        os.environ["HOME"] = str(home_a)
        dir_a = at.token_dir()
        mint(None)                                    # into user A's default dir
        minted_at = at.token_path_for(DIGEST)
        a_exists = minted_at.is_file()

        os.environ["HOME"] = str(home_b)
        dir_b = at.token_dir()
        entry_as_b = send_through_adapter(adapter_for(FakeMT5Module()), dict(NEW_ENTRY))
        close_as_b = send_through_adapter(adapter_for(FakeMT5Module()), dict(CLOSE_LONG))
        state_b = at.describe_activation_state(DIGEST)
    finally:
        if saved_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = saved_home

    obs.append({"step": "token_dir() resolved per user", "raw": {
        "user A": str(dir_a), "user B": str(dir_b),
        "A's token written": str(minted_at), "exists": a_exists}})
    obs.append({"step": "the book running as user B", "raw": {
        "entry": entry_as_b, "close": close_as_b,
        "describe_activation_state(): token_dir": state_b["token_dir"],
        "queried_account_has_token": state_b.get("queried_account_has_token")}})

    crit.append({"criterion": "the two users resolve different token directories",
                 "expected": "different", "observed": [str(dir_a), str(dir_b)],
                 "ok": str(dir_a) != str(dir_b)})
    crit.append({"criterion": "user B does not see user A's token; new exposure is refused",
                 "expected": "activation_token_absent", "observed": entry_as_b.get("reason"),
                 "ok": entry_as_b.get("reason") == "activation_token_absent"})
    crit.append({"criterion": "the failure mode is a DENIAL, not a crash",
                 "expected": "ActivationTokenError", "observed": entry_as_b.get("raised"),
                 "ok": entry_as_b.get("raised") == "ActivationTokenError"})
    crit.append({"criterion": "and user B can still close",
                 "expected": "reaches the broker", "observed": close_as_b,
                 "ok": close_as_b["reached_broker"] is True})
    crit.append({"criterion": "the resolved token_dir is machine-readable for the operator",
                 "expected": "describe_activation_state reports the dir it actually read",
                 "observed": state_b["token_dir"],
                 "ok": str(dir_b) == state_b["token_dir"]})

    # Does the live entrypoint print the directory it resolved? That is D-6's other half.
    run_book = (REPO / "run_book.py").read_text(encoding="utf-8")
    prints_dir = "token_dir" in run_book
    obs.append({"step": "run_book.py logs the token_dir it resolved",
                "raw": {"'token_dir' appears in run_book.py": prints_dir,
                        "lines": [ln.strip() for ln in run_book.splitlines()
                                  if "token_dir" in ln][:6]}})
    crit.append({"criterion": "run_book.py surfaces the resolved token_dir so a 2 a.m. "
                              "operator can see WHY nothing trades",
                 "expected": "present", "observed": prints_dir, "ok": prints_dir})

    return receipt(
        "D-6", "Wrong user", "demo account (Windows)", judge(crit), crit, obs,
        "either the token is shared more widely than intended, or the operator mints into a "
        "directory the live process never reads, believes the system is authorized, and "
        "cannot understand why nothing trades.",
        notes=[
            "PARTIAL, and the residual is named. The mechanism — `token_dir()` reads "
            "`$GTOS_ACTIVATION_TOKEN_DIR`, else expands `~/.gtos/activation` at call time — "
            "is measured here by moving HOME. What CANNOT be measured on macOS is how "
            "Windows expands `~` for a scheduled task running as SYSTEM or a service "
            "account: `Path.expanduser()` there consults USERPROFILE/HOMEDRIVE+HOMEPATH, and "
            "SYSTEM's profile is C:\\Windows\\System32\\config\\systemprofile. That is a real "
            "difference in kind, not degree, and it stays UNVERIFIED until run on the host.",
        ])


# --------------------------------------------------------------------------
# D-7 / D-8 — the two that need a terminal, plus what IS decidable about them
# --------------------------------------------------------------------------


def drill_d7(tmp: Path) -> dict:
    """Not runnable here. But the Python-side consequence is measured."""

    obs, crit = [], []
    token_dir = tmp / "d7_activation"
    token_dir.mkdir(parents=True, exist_ok=True)
    os.environ[at.TOKEN_DIR_ENV_VAR] = str(token_dir)

    # The B103 strand: the broker reduced the position out-of-band, the engine's
    # in-memory volume is stale, and the close it builds is over-volume.
    module = FakeMT5Module(positions=[FakePosition(type=0, volume=0.01)])
    over = dict(CLOSE_LONG, volume=0.03)
    result = send_through_adapter(adapter_for(module), over)
    exact = send_through_adapter(adapter_for(FakeMT5Module(positions=[FakePosition(type=0, volume=0.01)])),
                                 dict(CLOSE_LONG, volume=0.01))
    obs.append({"step": "over-volume close against a broker-reduced position (no token)",
                "raw": {"request_volume": 0.03, "broker_volume": 0.01, "outcome": result}})
    obs.append({"step": "control — the correctly-sized close", "raw": exact})
    crit.append({"criterion": "the over-volume close is refused TODAY (the strand exists)",
                 "expected": "refused", "observed": result.get("reason"),
                 "ok": result["reached_broker"] is False})
    crit.append({"criterion": "the correctly-sized close is allowed",
                 "expected": "reaches the broker", "observed": exact,
                 "ok": exact["reached_broker"] is True})

    return receipt(
        "D-7", "What MT5 does with an over-volume close", "demo account",
        "NOT_RUNNABLE_HERE", crit, obs,
        "if MT5 opens new opposing exposure on an over-volume DEAL, the current conservative "
        "refusal is correct and must stay; if it rejects or truncates, the refusal is a "
        "gratuitous strand.",
        notes=[
            "CANNOT RUN. The question is what the BROKER does with the request, which no "
            "fake module can answer — a stand-in would only replay whichever of the three "
            "outcomes I chose to encode, which is assuming the answer.",
            "What IS measured: the strand is real and reachable at HEAD. A position reduced "
            "out-of-band to 0.01 while the engine believes 0.03 produces a refused close with "
            "no token present. The exposure is bounded by how long the engine's in-memory "
            "volume can stay stale.",
            "Cheapest partial mitigation that needs NO drill: re-read the position volume "
            "immediately before building a close. That is the fix the spec prescribes for "
            "outcome (3) and it is safe under all three outcomes — it is not blocked on D-7.",
            "Until then flatten_all_positions.py (deliberately ungated) is the manual hatch.",
        ])


def drill_d8(tmp: Path) -> dict:
    """Not runnable here. The consequence of the dangerous answer IS measured."""

    obs, crit = [], []
    token_dir = tmp / "d8_activation"
    token_dir.mkdir(parents=True, exist_ok=True)
    os.environ[at.TOKEN_DIR_ENV_VAR] = str(token_dir)

    outcomes = {}
    for mode, label in (("none", "positions_get returns None"),
                        ("raise", "positions_get raises"),
                        ("stale", "positions_get returns a STALE non-empty tuple")):
        module = FakeMT5Module(positions_mode=mode)
        adapter = adapter_for(module)
        close = send_through_adapter(adapter, dict(CLOSE_LONG))
        decision = at.authorize_broker_mutation(
            dict(CLOSE_LONG), account_login_sha256=DIGEST,
            positions_provider=adapter.positions_for_activation,
            directory=token_dir, audit=False)
        outcomes[mode] = {"label": label, "close": close, "reason": decision.reason,
                          "positions_verified": decision.positions_verified}
    obs.append({"step": "each MT5 failure shape, driven end-to-end", "raw": outcomes})

    crit.append({"criterion": "None -> the close survives",
                 "expected": "allowed", "observed": outcomes["none"]["reason"],
                 "ok": outcomes["none"]["close"]["reached_broker"] is True})
    crit.append({"criterion": "an exception -> the close survives",
                 "expected": "allowed", "observed": outcomes["raise"]["reason"],
                 "ok": outcomes["raise"]["close"]["reached_broker"] is True})
    crit.append({"criterion": "a STALE tuple -> the close is STRANDED (the dangerous answer)",
                 "expected": "documented, not passed",
                 "observed": outcomes["stale"]["reason"],
                 "ok": outcomes["stale"]["close"]["reached_broker"] is False})

    return receipt(
        "D-8", "Does killing a terminal really produce None?", "demo account",
        "NOT_RUNNABLE_HERE", crit, obs,
        "if positions_get can return a stale non-empty tuple, the reader is confidently "
        "wrong rather than unavailable, and neither the raise-on-None fix nor the strict "
        "provider marker catches it.",
        notes=[
            "CANNOT RUN. Which of {None, (), stale tuple, exception, hang} the real module "
            "produces when terminal64.exe dies is a property of the MT5 IPC layer. "
            "`mt5_real.py:449-450` asserts None; nothing has measured it.",
            "What IS measured here: the three shapes' CONSEQUENCES, driven through the real "
            "adapter. None and exception both survive. A stale tuple that omits the live "
            "ticket STRANDS the close — `positions_for_activation` is marked "
            "@strict_positions_provider, so 'ticket absent' is read as authoritative absence, "
            "the close classifies as exposure_increasing_deal_on_position, and with no token "
            "it is refused.",
            "SCOPE, corrected (B335). This is the only path found that can refuse a close "
            "INSIDE THE ACTIVATION-TOKEN LAYER. It is not the only one in the system, and "
            "saying so without the qualifier turned a true measurement into a false "
            "guarantee. Above this layer, `execution.py`'s close-volume gate refused ~11 % of "
            "position sizes outright (B333, fixed), `live_broker_authority: false` suppresses "
            "flatten entirely (B334), and a runtime halt's risk-reducing carve-out reads "
            "positions through the lossy reader B101 repaired here (B334). Every drill in "
            "this file exercises the token layer, and the token layer was not where the risk "
            "was.",
            "So D-8 is not merely unanswered — its dangerous branch is the one reachable "
            "strand in this layer, and the cost of leaving it unmeasured is now priced.",
            "Run D-8 before D-2, as the spec says.",
        ])


# --------------------------------------------------------------------------
# Beyond the eight: attack the never-strand invariant directly
# --------------------------------------------------------------------------


def drill_x1(tmp: Path) -> dict:
    """Every close-shaped request the repo can produce, against a hostile gate.

    The spec's eight drills test the states the DESIGN anticipates. This one
    tests the assumption underneath them: that
    ``deal_request_is_structurally_a_close`` accepts what the engine's close
    producers actually build. Its docstring lists eleven call sites and asserts
    none carries ``sl``/``tp``. That is a claim about source that drifts the
    moment somebody adds a field, and a drift there is silent — the close simply
    starts requiring a token.
    """

    obs, crit = [], []
    token_dir = tmp / "x1_activation"
    token_dir.mkdir(parents=True, exist_ok=True)
    os.environ[at.TOKEN_DIR_ENV_VAR] = str(token_dir)

    # 1. Re-measure the docstring's claim against source, rather than trusting it.
    import re
    producers = {
        "src/components/execution.py": None,
        "src/safety/heartbeat_monitor.py": None,
        "flatten_all_positions.py": None,
        "emergency_close_and_stop_redacted_account.py": None,
        "fn_smoke_trade.py": None,
    }
    found = []
    for rel in producers:
        path = REPO / rel
        if not path.is_file():
            found.append({"file": rel, "status": "ABSENT from this working tree"})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        # A CLOSE is a dict literal carrying `"position":` AND `TRADE_ACTION_DEAL`.
        # The action test is not optional: the first version of this check keyed
        # on `"action"` alone and reported execution.py:9707 and :9861 as closes
        # carrying sl+tp. They are `TRADE_ACTION_SLTP` stop/target modifies, which
        # are classified down a different branch entirely and are SUPPOSED to
        # carry both fields. Two false positives on the one claim the drill exists
        # to check — recorded so the next reader does not re-derive it.
        hits = []
        for match in re.finditer(r'"position"\s*:', text):
            start = text.rfind("{", 0, match.start())
            end = text.find("}", match.end())
            if start < 0 or end < 0:
                continue
            block = text[start:end + 1]
            if "TRADE_ACTION_DEAL" not in block:
                continue
            line = text[:match.start()].count("\n") + 1
            hits.append({"line": line,
                         "carries_sl": '"sl"' in block, "carries_tp": '"tp"' in block})
        found.append({"file": rel, "close_shaped_deal_dicts": len(hits),
                      "any_with_sl_or_tp": [h for h in hits if h["carries_sl"] or h["carries_tp"]]})
    offenders = [f for f in found if f.get("any_with_sl_or_tp")]
    obs.append({"step": "re-measure: do any close producers carry sl/tp?", "raw": found})
    crit.append({"criterion": "no close-shaped request in the repo carries sl or tp",
                 "expected": "none", "observed": offenders, "ok": not offenders})

    # 2. The consequence, if one ever did.
    with_sl = send_through_adapter(adapter_for(FakeMT5Module()), dict(CLOSE_LONG, sl=1940.0))
    obs.append({"step": "consequence — a close carrying sl", "raw": with_sl})
    crit.append({"criterion": "a close carrying sl IS refused (so the claim above is load-bearing)",
                 "expected": "refused", "observed": with_sl.get("reason"),
                 "ok": with_sl["reached_broker"] is False})

    # 3. The other risk-reducing shapes must survive an empty token dir.
    shapes = {
        "market close": dict(CLOSE_LONG),
        "partial close": dict(CLOSE_LONG, volume=0.05),
        "stop tighten": dict(TIGHTEN_STOP),
        "pending cancel": dict(CANCEL_PENDING),
    }
    survived = {}
    for label, request in shapes.items():
        survived[label] = send_through_adapter(adapter_for(FakeMT5Module()), request)
    obs.append({"step": "the four risk-reducing shapes, no token present", "raw": survived})
    crit.append({"criterion": "all four risk-reducing shapes pass with no token",
                 "expected": "all reach the broker",
                 "observed": {k: v["reached_broker"] for k, v in survived.items()},
                 "ok": all(v["reached_broker"] for v in survived.values())})

    # 4. A close must survive a broken audit sink too — the audit is on the
    #    risk-reducing path (`_finish` runs before the return).
    audit_blocked = tmp / "x1_audit_blocked"
    audit_blocked.mkdir(parents=True, exist_ok=True)
    (audit_blocked / at.AUDIT_LOG_FILENAME).mkdir(exist_ok=True)   # a DIRECTORY where the log goes
    os.environ[at.TOKEN_DIR_ENV_VAR] = str(audit_blocked)
    audit_case = send_through_adapter(adapter_for(FakeMT5Module()), dict(CLOSE_LONG))
    obs.append({"step": "audit log path is a directory, so the append cannot succeed",
                "raw": audit_case})
    crit.append({"criterion": "an unwritable audit sink does not block a close",
                 "expected": "reaches the broker", "observed": audit_case,
                 "ok": audit_case["reached_broker"] is True})

    # 5. A provider raising a BaseException that is NOT an Exception.
    os.environ[at.TOKEN_DIR_ENV_VAR] = str(token_dir)

    @strict_positions_provider
    def hostile(symbol=""):
        raise KeyboardInterrupt("terminal killed mid-read")

    base_case = {}
    try:
        decision = at.authorize_broker_mutation(
            dict(CLOSE_LONG), account_login_sha256=DIGEST,
            positions_provider=hostile, directory=token_dir, audit=False)
        base_case = {"raised": None, "reason": decision.reason, "allowed": decision.allowed}
    except BaseException as exc:  # noqa: BLE001
        base_case = {"raised": type(exc).__name__, "reason": repr(exc)[:200], "allowed": None}
    obs.append({"step": "provider raises a BaseException (KeyboardInterrupt)", "raw": base_case})
    crit.append({"criterion": "a non-Exception raise out of the provider is REPORTED, not silently "
                              "swallowed — recorded either way",
                 "expected": "documented",
                 "observed": base_case,
                 "ok": True})

    return receipt(
        "X-1", "Direct attack on the never-strand invariant", "laptop",
        judge(crit), crit, obs,
        "any path where a live position cannot be closed. This drill exists because the "
        "eight specified ones test anticipated states, and the strand risk lives in the "
        "unanticipated ones.",
        notes=[
            "Not in TOKEN_CHAOS_DRILLS.md. Added because the session prompt ranks the "
            "never-strand invariant above everything else in it.",
            "Criterion 5 is recorded rather than judged: `_read_positions` catches "
            "`Exception`, so a `BaseException` from a provider propagates and would block "
            "the close. No real MT5 path raises one — `positions_for_activation` wraps its "
            "own call in `except Exception` — so this is a latent shape, not a live defect. "
            "It is written down so a future provider author sees the boundary.",
        ])


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------


DRILLS = [
    ("D-1", drill_d1), ("D-2", drill_d2), ("D-3", drill_d3), ("D-4", drill_d4),
    ("D-5", drill_d5), ("D-6", drill_d6), ("D-7", drill_d7), ("D-8", drill_d8),
    ("X-1", drill_x1),
]


def run_all(tmp: Path, drills=None) -> list[dict]:
    receipts = []
    saved_env = os.environ.get(at.TOKEN_DIR_ENV_VAR)
    try:
        for drill_id, fn in (DRILLS if drills is None else drills):
            try:
                receipts.append(fn(tmp))
            except BaseException as exc:  # noqa: BLE001 — a harness crash is a result
                receipts.append(receipt(
                    drill_id, f"{drill_id} (harness error)", "laptop", "FAIL",
                    [{"criterion": "the drill runs at all", "expected": "no exception",
                      "observed": repr(exc)[:400], "ok": False}],
                    [{"step": "harness", "raw": repr(exc)[:2000]}],
                    "the drill could not be evaluated; treat as unproven, not as passing."))
    finally:
        if saved_env is None:
            os.environ.pop(at.TOKEN_DIR_ENV_VAR, None)
        else:
            os.environ[at.TOKEN_DIR_ENV_VAR] = saved_env
    return receipts


def summarize(receipts: list[dict]) -> str:
    lines = ["# Token chaos drills — run receipts", "",
             f"Run {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} on a macOS laptop with "
             "no MT5 terminal and no broker connection.", "",
             # Both columns, deliberately. The header used to read `environment` over
             # `environment_required`, so D-2, D-6, D-7 and D-8 rendered as "demo account" in a table
             # whose own first line says every drill ran on a laptop with no terminal and no broker.
             # A reader scanning the table read "PASS on a demo account" for drills that never
             # touched one — the false-green class this whole session was built to hunt, produced by
             # a column header. Fixed 2026-07-29 at wave-4 integration (B367).
             "| drill | title | environment required | ran on | verdict | criteria met |",
             "|---|---|---|---|---|---|"]
    for r in receipts:
        met = sum(1 for c in r["criteria"] if c["ok"])
        lines.append(f"| {r['drill']} | {r['title']} | {r['environment_required']} | "
                     f"{r.get('environment_here', 'unrecorded')} | "
                     f"**{r['status']}** | {met}/{len(r['criteria'])} |")
    lines += ["", "## What each drill found", ""]
    for r in receipts:
        lines.append(f"### {r['drill']} — {r['title']} — {r['status']}")
        for c in r["criteria"]:
            lines.append(f"- {'PASS' if c['ok'] else 'FAIL'} — {c['criterion']} "
                         f"(expected `{c['expected']}`, observed `{c['observed']}`)")
        for note in r["notes"]:
            lines.append(f"- NOTE: {note}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--receipts-dir", type=Path, default=None,
                    help="write one JSON receipt per drill plus SUMMARY.md here")
    ap.add_argument("--only", action="append", default=[],
                    help="run only these drill ids (repeatable)")
    args = ap.parse_args()

    if "MetaTrader5" in sys.modules and not isinstance(
            sys.modules["MetaTrader5"], types.ModuleType):
        print("REFUSING: a real MetaTrader5 module is loaded", file=sys.stderr)
        return 2

    selected = [(d, f) for d, f in DRILLS if not args.only or d in args.only]
    tmp = Path(tempfile.mkdtemp(prefix="gtos_token_chaos_"))
    try:
        receipts = run_all(tmp, selected)
    finally:
        # chmod back anything the drills locked, then remove.
        for root, dirs, _files in os.walk(tmp):
            for d in dirs:
                try:
                    os.chmod(os.path.join(root, d), stat.S_IRWXU)
                except OSError:
                    pass
        shutil.rmtree(tmp, ignore_errors=True)

    text = summarize(receipts)
    print(text)
    if args.receipts_dir:
        args.receipts_dir.mkdir(parents=True, exist_ok=True)
        for r in receipts:
            (args.receipts_dir / f"{r['drill']}.json").write_text(
                json.dumps(r, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        (args.receipts_dir / "SUMMARY.md").write_text(text, encoding="utf-8")
        print(f"wrote {len(receipts)} receipts to {args.receipts_dir}")

    failed = [r for r in receipts if r["status"] == "FAIL"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
