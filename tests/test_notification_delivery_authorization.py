"""Behavioural proof that the test suite cannot page the operator (F30 / Q7).

These tests run the real notification transports in-process with real Telegram
credentials in the environment, and assert that **no operator-facing delivery
is attempted** — no HTTPS request, and no trade-shaped record written to the
``pipeline_state/UNDELIVERED_CRITICAL_ALERTS.jsonl`` sidecar that
``monitor_books`` watches.

Nothing here greps source. Every assertion is made by driving the transport and
observing whether it reached the network layer, so the tests still fail if the
guard is present but wired to the wrong place.

The non-vacuity check is ``test_authorized_process_does_reach_the_network``: it
opens the gate and asserts the very same call *does* reach ``urlopen``. Without
it, every other test here would pass just as happily against a transport that
was simply broken.
"""

from __future__ import annotations

import urllib.request

import pytest

import src.notifications as notifications
import src.safety.notification_authorization as notification_authorization
import src.utils.notification_queue as notification_queue


# A message shaped exactly like the ones F30 found on disk.
TRADE_SHAPED_ALERT = (
    "[FTMO] \U0001F7E2 LONG BTCUSD · Crypto momentum · "
    "entry 61234.5 · risk 0.40% (~$397)"
)


@pytest.fixture
def network_spy(monkeypatch):
    """Record every ``urllib.request.urlopen`` call instead of performing it.

    Both transports build their request through ``urllib.request``
    (``notification_queue._default_transport`` imports it inside the function;
    ``notifications._send`` at module import), so patching the attribute on the
    module object covers both. Any call is a delivery attempt.
    """
    calls: list[object] = []

    def _spy(req, *args, **kwargs):  # pragma: no cover - body asserted, not run
        calls.append(req)
        raise AssertionError(
            "a real HTTPS request was issued to the Telegram API from the test suite"
        )

    monkeypatch.setattr(urllib.request, "urlopen", _spy)
    return calls


@pytest.fixture
def telegram_credentials_present(monkeypatch):
    """Put live-shaped Telegram credentials in scope for both transports.

    This is the condition F30 identified as the only thing standing between the
    suite and the operator's phone. With credentials present, credential-gating
    alone lets the message through; only the authorization gate can stop it.
    """
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "090:TEST-TOKEN-NOT-REAL")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-1000000000000")
    # notifications.py snapshots these at import time into module globals.
    monkeypatch.setattr(notifications, "_TOKEN", "090:TEST-TOKEN-NOT-REAL")
    monkeypatch.setattr(notifications, "_CHAT_ID", "-1000000000000")


# ---------------------------------------------------------------------------
# The gate itself
# ---------------------------------------------------------------------------


def test_delivery_is_denied_by_default():
    """A process that never authorized itself may not deliver."""
    decision = notification_authorization.delivery_authorization()

    assert decision.allowed is False
    assert decision.source == "none"
    assert notification_authorization.is_delivery_authorized() is False


def test_environment_grant_does_not_arm_the_test_suite(monkeypatch):
    """An exported env grant must not authorize a pytest process.

    Defence in depth on top of default-deny: a developer who sourced the live
    ``.env`` into their shell must not thereby arm every test they run.
    """
    monkeypatch.setenv(notification_authorization.ENV_VAR, "authorized")

    decision = notification_authorization.delivery_authorization()

    assert decision.allowed is False
    assert decision.source == "pytest_veto"


def test_require_delivery_authorization_raises_when_unauthorized():
    with pytest.raises(notification_authorization.OperatorDeliveryNotAuthorized):
        notification_authorization.require_delivery_authorization("telegram")


def test_grant_requires_an_attributable_reason():
    """An unattributed grant is refused — delivery rights must be traceable."""
    with pytest.raises(ValueError):
        notification_authorization.authorize_operator_delivery(reason="  ")

    assert notification_authorization.is_delivery_authorized() is False


# ---------------------------------------------------------------------------
# The two transports, driven for real
# ---------------------------------------------------------------------------


def test_queue_transport_does_not_reach_the_network_unauthorized(
    network_spy, telegram_credentials_present
):
    """``notification_queue._default_transport`` must not POST to Telegram."""
    delivered = notification_queue._default_transport(TRADE_SHAPED_ALERT)

    assert network_spy == []
    # False, not True: an undelivered CRITICAL must never be marked DELIVERED.
    assert delivered is False


def test_queue_transport_does_not_write_the_undelivered_sidecar(
    tmp_path, monkeypatch, network_spy, telegram_credentials_present
):
    """No trade-shaped record may land in ``pipeline_state/``.

    The sidecar is written relative to CWD, so the test chdirs into ``tmp_path``
    and asserts the path stays absent there. That also proves the guard runs
    *before* the sidecar write rather than only before the POST — the pre-guard
    code wrote the sidecar on exactly the branch that skipped the POST.
    """
    monkeypatch.chdir(tmp_path)
    # Remove credentials so the pre-guard code would take the sidecar branch.
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    notification_queue._default_transport(TRADE_SHAPED_ALERT)

    sidecar = tmp_path / "pipeline_state" / "UNDELIVERED_CRITICAL_ALERTS.jsonl"
    assert not sidecar.exists()
    assert not (tmp_path / "pipeline_state").exists()


def test_legacy_send_does_not_reach_the_network_unauthorized(
    network_spy, telegram_credentials_present
):
    """``notifications._send`` is the fallback every ``notify_*`` helper uses."""
    notifications._send(TRADE_SHAPED_ALERT)

    assert network_spy == []


def test_queue_send_end_to_end_delivers_nothing(
    tmp_path, network_spy, telegram_credentials_present
):
    """Drive the public queue API the way production code does.

    ``Level.LOW`` transports synchronously in the calling process;
    ``Level.HIGH`` persists and is transported by ``flush()``. Neither may
    reach the operator from a test process.
    """
    queue = notification_queue.PersistentNotificationQueue(
        queue_path=tmp_path / "notification_queue.jsonl",
    )

    queue.send(TRADE_SHAPED_ALERT, level=notification_queue.Level.LOW)
    queue.send(TRADE_SHAPED_ALERT, level=notification_queue.Level.HIGH)
    delivered = queue.flush()

    assert network_spy == []
    assert delivered == 0


def test_notify_alert_helper_delivers_nothing(
    tmp_path, monkeypatch, network_spy, telegram_credentials_present
):
    """The top-level helper an orchestrator actually calls stays silent."""
    monkeypatch.setattr(
        notification_queue, "_DEFAULT_QUEUE_PATH",
        str(tmp_path / "notification_queue.jsonl"),
    )
    notification_queue._reset_singleton_for_tests()
    try:
        notifications.notify_alert(TRADE_SHAPED_ALERT)
        notification_queue.get_default_queue().flush()
    finally:
        notification_queue._reset_singleton_for_tests()

    assert network_spy == []


def test_every_direct_telegram_poster_is_gated(network_spy, telegram_credentials_present):
    """The three transports that POST outside the queue must refuse too.

    ``rg 'api\\.telegram\\.org'`` finds five senders. Two go through the guarded
    paths above; these three build and POST their own request, so each carries
    its own gate. Missing one would leave a live page-the-operator path open
    from a test process.
    """
    import importlib

    from src.safety import heartbeat_monitor

    api_refusal_monitor = importlib.import_module("scripts.api_refusal_monitor")
    no_data_alert_monitor = importlib.import_module("scripts.no_data_alert_monitor")

    assert api_refusal_monitor.send_telegram("tok", "chat", TRADE_SHAPED_ALERT) is False
    assert no_data_alert_monitor.send_telegram("tok", "chat", TRADE_SHAPED_ALERT) is False
    assert heartbeat_monitor.send_telegram_alert(TRADE_SHAPED_ALERT) is False

    assert network_spy == []


# ---------------------------------------------------------------------------
# Non-vacuity: the same call DOES reach the network once the gate opens
# ---------------------------------------------------------------------------


def test_authorized_process_does_reach_the_network(
    monkeypatch, telegram_credentials_present
):
    """Open the gate and the identical call reaches ``urlopen``.

    Without this, every test above would also pass against a transport that was
    merely broken, or against a guard wired somewhere harmless. This pins the
    refusals to the authorization gate specifically.

    The grant is scoped by the context manager, so the autouse conftest fixture
    still observes an unauthorized process at teardown.
    """
    attempts: list[str] = []

    class _Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def _capture(req, *args, **kwargs):
        attempts.append(req.full_url)
        return _Response()

    monkeypatch.setattr(urllib.request, "urlopen", _capture)

    with notification_authorization.operator_delivery_authorized(
        reason="behavioural test: authorized branch"
    ):
        assert notification_authorization.is_delivery_authorized() is True
        delivered = notification_queue._default_transport(TRADE_SHAPED_ALERT)

    assert delivered is True
    assert len(attempts) == 1
    assert "api.telegram.org" in attempts[0]
    # And the grant did not survive the scope.
    assert notification_authorization.is_delivery_authorized() is False


# NOTE on what is deliberately NOT tested here.
#
# "The repo's pipeline_state/ contains no alert artifacts" is not asserted. It
# is not a property of this change — a pre-guard leftover on disk would make it
# red for reasons no code in this file controls — and the invariant it is
# reaching for is already enforced better by ``tests/conftest.py``: Layer 2
# snapshots every file under ``pipeline_state/`` at session start and fails the
# session in ``pytest_sessionfinish`` if the session added, deleted or modified
# any of them. That is a session-level check attributed to no single test,
# which is the correct shape. This file stays on the per-call behaviour.


# ---------------------------------------------------------------------------
# The other half of the gate: every long-lived PRODUCER must take the grant.
#
# Added at wave-3 integration (Session O, B186) after the merge produced exactly
# the defect this covers. Session M inverted delivery to presence-of-
# authorization and granted every producer it knew about. Session I, in
# parallel, extended `.tools/monitor_books.py` with `gate_tripwire()` -- which
# per CLAUDE.md §4 is the ONLY thing anywhere that would notice the live
# authority gate being flipped. `.tools/` is not `scripts/*_monitor.py`, so it
# was missed, and every alert that daemon raises was refused, retried five
# times, marked FAILED and dropped -- while its heartbeat kept reporting
# healthy. Neither branch is wrong alone.
#
# The tests above prove the TRANSPORTS refuse when ungranted. Nothing proved
# the producers are granted, so the merge could silence the alerting path
# without a single test going red.
#
# Discovery-based on purpose: a NEW producer added later is caught without
# anyone remembering to extend a list.
# ---------------------------------------------------------------------------

import ast as _ast
import pathlib as _pathlib

_REPO = _pathlib.Path(__file__).resolve().parents[1]

#: Symbols whose use means "this module can page a human".
_DELIVERY_SYMBOLS = frozenset({
    "send_telegram", "send_telegram_alert", "notify_critical", "notify_alert",
    "_send_async", "enqueue_notification",
})

#: Producers that are deliberately ungranted, each with the reason, so the
#: exemption is visible and arguable rather than implicit.
_UNGRANTED_BY_DESIGN: dict[str, str] = {
    "src/utils/notification_queue.py": (
        "Defines the transport and takes the grant in its --worker entrypoint "
        "(:1038). Importing it must never grant."
    ),
    "src/notifications.py": (
        "Transport module, not an entrypoint. Its callers hold the grant."
    ),
    "src/safety/notification_authorization.py": (
        "The gate itself."
    ),
    # The discriminator is LONG-LIVED vs SHORT-LIVED, and the transport says so itself:
    # `notification_queue.send` (:docstring) starts the in-process poller "as a defense-in-depth
    # fallback for long-lived processes... Short-lived cron scripts that exit after enqueueing rely
    # on the worker -- the lazy in-process daemon dies with them."
    #
    # For a long-lived daemon an absent grant is DESTRUCTIVE: the poller exhausts 5 retries, writes a
    # terminal FAILED marker, and the authorized worker then skips the entry too. For a one-shot cron
    # it is INERT: the process exits long before retry 5, the entry stays pending, and the authorized
    # worker delivers it.
    "scripts/correlation_shock_monitor.py": (
        "One-shot cron, not a daemon: enqueues at HIGH via notify_alert and exits, so the authorized "
        "worker drains it. LATENT, not introduced by wave 3: the retry ladder reaches the terminal "
        "FAILED marker at ~13 min, so if this ever runs longer than that it would drop its own alert. "
        "Granting it would remove the ambiguity for one line; deliberately NOT done at integration to "
        "keep the merge's blast radius to the defect it found. Flagged for wave 4."
    ),
    "scripts/refresh_economic_calendar.py": (
        "Same shape and same latent bound as scripts/correlation_shock_monitor.py above."
    ),
}


def _module_entrypoints() -> list[_pathlib.Path]:
    """Files with a __main__ guard that reference a delivery symbol."""
    roots = [_REPO / "scripts", _REPO / ".tools", _REPO / "src" / "safety",
             _REPO / "src" / "utils"]
    found = []
    for f in [*_REPO.glob("*.py")] + [p for r in roots for p in r.rglob("*.py")]:
        try:
            src = f.read_text(encoding="utf-8", errors="replace")
            tree = _ast.parse(src)
        except (OSError, SyntaxError):
            continue
        if "__main__" not in src:
            continue
        used = {n.id for n in _ast.walk(tree) if isinstance(n, _ast.Name)}
        used |= {n.attr for n in _ast.walk(tree) if isinstance(n, _ast.Attribute)}
        used |= {a.asname or a.name for n in _ast.walk(tree)
                 if isinstance(n, _ast.ImportFrom) for a in n.names}
        if used & _DELIVERY_SYMBOLS:
            found.append(f)
    return sorted(found)


def test_the_producer_scan_finds_producers_at_all():
    """Positive control. The assertion below is vacuous against an empty list."""
    found = _module_entrypoints()
    rels = {p.relative_to(_REPO).as_posix() for p in found}
    assert len(found) >= 5, f"producer scan found only {rels}"
    # The one the merge broke must be in scope, or this test would not have caught it.
    assert ".tools/monitor_books.py" in rels


def test_every_long_lived_alert_producer_takes_the_delivery_grant():
    """A producer that cannot deliver is worse than one that does not exist.

    It reports healthy and pages nobody.
    """
    ungranted = []
    for f in _module_entrypoints():
        rel = f.relative_to(_REPO).as_posix()
        if rel in _UNGRANTED_BY_DESIGN:
            continue
        if "authorize_operator_delivery" not in f.read_text(encoding="utf-8", errors="replace"):
            ungranted.append(rel)
    assert not ungranted, (
        "alert producer(s) with no operator-delivery grant — every alert they raise is "
        "refused, retried, marked FAILED and dropped, while their heartbeat reports healthy:\n"
        + "\n".join(f"  {u}" for u in ungranted)
        + "\n\nAdd `authorize_operator_delivery(reason=...)` at the entrypoint, or list it in "
          "_UNGRANTED_BY_DESIGN with the reason."
    )


def test_the_ungranted_exemption_list_does_not_go_stale():
    """An exemption for a file that no longer exists silently excuses a real gap."""
    missing = [rel for rel in _UNGRANTED_BY_DESIGN if not (_REPO / rel).is_file()]
    assert not missing, f"_UNGRANTED_BY_DESIGN names files that no longer exist: {missing}"
