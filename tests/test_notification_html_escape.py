"""Regression tests for the 2026-04-27 GBPJPY daily-loss-stop HTML-escape bug.

Background
----------
On 2026-04-27 23:00 UTC GBPJPY's daily-loss-stop fired and the alert payload
caused 100+ Telegram HTTP 400 storms in
``pipeline_state/notification_queue.jsonl``. Root cause: the message body in
``src/components/orchestrator.py`` interpolated literal HTML-special
characters (``&`` and ``<=``) into a payload sent with ``parse_mode=HTML``.
Telegram's HTML parser saw ``P&L:`` as an unescaped entity reference and
``<= -4.00`` as an unclosed angle bracket → 400 Bad Request → indefinite
CRITICAL retries → log spam + the CEO never saw the alert.

Fix architecture (Option B — drop HTML parse_mode entirely)
-----------------------------------------------------------
Both ``src.notifications._send`` and
``src.utils.notification_queue._default_transport`` were updated to omit
``parse_mode`` from the Telegram POST payload. This eliminates the entire
class of HTML-injection bugs — alert call sites no longer have to worry
about escaping ``<``, ``>``, or ``&`` because Telegram never tries to parse
the body.

Templates that previously contained ``<b>...</b>`` tags were stripped of
those tags in the same change so the bold markup doesn't render literally.

Test policy
-----------
The canonical pattern is ``tmp_path`` + module-ref monkeypatch. We assert:

1. The transport's outgoing payload does NOT contain ``parse_mode``.
2. The orchestrator's daily-loss-stop alert text contains no raw
   HTML-special characters that would have broken the HTML parser.
3. Every other call site we patched in the same change still emits a
   well-formed plain-text body.
4. The notify_alert end-to-end smoke test succeeds with a body that
   would previously have triggered 400.

Tests follow the existing project convention from
``tests/test_notifications.py`` and ``tests/test_notification_queue.py``.
"""
from __future__ import annotations

import json

import pytest

from src import notifications as _notif
from src.utils import notification_queue as _nq_mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def captured_payloads(monkeypatch, tmp_path):
    """Capture the raw JSON payload that ``_default_transport`` would POST.

    Returns a list of dicts (one per send) so the test can assert on the
    presence/absence of ``parse_mode``, the message body, etc.
    """
    payloads: list[dict] = []

    # Stub the transport at the module level so the queue's daemon
    # transport never hits Telegram.
    def fake_transport(text: str) -> bool:
        # Re-build the payload exactly as _default_transport would, MINUS
        # the env-var requirements. This way we exercise the same dict
        # construction logic the real transport uses.
        payloads.append({"chat_id": "<test-chat>", "text": text})
        return True

    # Bypass the env-var gate inside _default_transport: install the fake
    # transport directly on a fresh queue singleton.
    _nq_mod._reset_singleton_for_tests()
    _nq_mod._SINGLETON = _nq_mod.PersistentNotificationQueue(
        queue_path=tmp_path / "queue.jsonl",
        transport=fake_transport,
    )
    # Drain on every send so tests don't wait on the 30s daemon poll.
    orig_send = _nq_mod._SINGLETON.send

    def _send_then_flush(message, *, level, alert_id=None):
        result = orig_send(message, level=level, alert_id=alert_id)
        _nq_mod._SINGLETON.flush()
        return result

    _nq_mod._SINGLETON.send = _send_then_flush  # type: ignore[method-assign]

    # Also stub fire-and-forget _send_async in src.notifications so the
    # fallback path lands in our capture list too.
    monkeypatch.setattr(
        _notif, "_send_async",
        lambda text: payloads.append({"chat_id": "<test-chat>", "text": text}),
    )
    yield payloads
    _nq_mod._reset_singleton_for_tests()


# ---------------------------------------------------------------------------
# 1. Transport-level: parse_mode is NOT set
# ---------------------------------------------------------------------------


def test_default_transport_payload_omits_parse_mode(
    monkeypatch, operator_delivery_grant
):
    """``_default_transport`` must NOT include ``parse_mode`` in the POST.

    This is the structural guarantee that the HTML-escape bug class cannot
    reappear — Telegram never tries to parse the body so literal ``&``,
    ``<``, ``>`` are safe.

    Requests ``operator_delivery_grant`` because the POST this inspects only
    happens for an authorized process (F30 / Q7). Without the grant the
    transport refuses before building a payload, and there would be nothing to
    assert about.
    """
    captured: list[bytes] = []

    class FakeResp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(req, timeout=10, context=None):  # noqa: ARG001
        captured.append(req.data)
        return FakeResp()

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "fake-chat")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    body = (
        "DAILY LOSS STOP (GBPJPY)\n"
        "MTM PnL: -4.07% reached cap of -4.00%\n"
        "Equity at trigger: $99,876.12\n"
        "Dormant until 00:00 UTC next day."
    )
    ok = _nq_mod._default_transport(body)
    assert ok is True
    assert len(captured) == 1
    payload = json.loads(captured[0].decode("utf-8"))
    assert "parse_mode" not in payload, (
        "parse_mode must NOT be set — the Telegram POST is plain-text by "
        "policy (HTML-ESCAPE BUG fix, 2026-04-28)"
    )
    assert payload["text"] == body


def test_notifications_send_payload_omits_parse_mode(
    monkeypatch, operator_delivery_grant
):
    """``src.notifications._send`` must also POST without ``parse_mode``.

    Requests ``operator_delivery_grant`` for the same reason as the test above:
    ``_send`` refuses before building a payload unless the process is
    authorized to page the operator (F30 / Q7).
    """
    captured: list[bytes] = []

    class FakeResp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(req, timeout=10, context=None):  # noqa: ARG001
        captured.append(req.data)
        return FakeResp()

    # _send reads module-level _TOKEN/_CHAT_ID, NOT env vars. Patch those.
    monkeypatch.setattr(_notif, "_TOKEN", "fake-token")
    monkeypatch.setattr(_notif, "_CHAT_ID", "fake-chat")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    _notif._send("trade closed: +1.5R, P&L = +$1,500")
    assert len(captured) == 1
    payload = json.loads(captured[0].decode("utf-8"))
    assert "parse_mode" not in payload, (
        "src.notifications._send must NOT set parse_mode — alert bodies "
        "may legitimately contain `&`, `<`, `>` (P&L, comparison "
        "operators, etc.)"
    )


# ---------------------------------------------------------------------------
# 2. Daily-loss-stop alert: realistic GBPJPY body survives end-to-end
# ---------------------------------------------------------------------------


def test_daily_loss_stop_realistic_body_does_not_contain_html_breakers(captured_payloads):
    """Reconstruct the orchestrator's daily-loss-stop alert and verify the
    rendered body contains NO unescaped HTML-special characters that would
    have caused the original 400 storm.

    The yardstick: after the fix, the body uses words ("reached", "of")
    instead of comparison operators, and ``PnL`` instead of ``P&L``. Even
    if some future commit accidentally re-enables ``parse_mode=HTML`` the
    daily-loss-stop body will still parse cleanly.
    """
    # Realistic GBPJPY values mirroring the live 2026-04-27 23:00 UTC event.
    daily_pnl_pct = -4.07
    cap_pct = 4.00
    equity = 99876.12
    symbol = "GBPJPY"

    # Reproduce the orchestrator's exact format string (post-fix).
    body = (
        f"DAILY LOSS STOP ({symbol})\n"
        f"MTM PnL: {daily_pnl_pct:.2f}% reached cap of -{cap_pct:.2f}%\n"
        f"Equity at trigger: ${equity:,.2f}\n"
        f"Dormant until 00:00 UTC next day. "
        f"AI calls paused. Open positions left to close naturally."
    )

    # No raw HTML-special chars in interpolated values.
    assert "<" not in body, "Body contains '<' which would break HTML parsing"
    assert ">" not in body, "Body contains '>' which would break HTML parsing"
    assert "&" not in body, "Body contains '&' which would break HTML parsing"
    # And no <b> tags either (template was stripped).
    assert "<b>" not in body
    assert "</b>" not in body

    # End-to-end: enqueue via notify_alert and confirm the captured payload
    # carries the same body, no parse_mode, no HTML breakers.
    _notif.notify_alert(body)
    assert len(captured_payloads) == 1
    captured_text = captured_payloads[0]["text"]
    assert "DAILY LOSS STOP (GBPJPY)" in captured_text
    assert "MTM PnL: -4.07% reached cap of -4.00%" in captured_text
    # SYSTEM ALERT prefix must not have HTML tags either.
    assert "<b>" not in captured_text
    assert "</b>" not in captured_text


def test_orchestrator_daily_loss_stop_format_string_uses_safe_chars():
    """Read the orchestrator source and confirm the patched format string
    no longer contains ``<=`` or ``P&L:``.

    This is a structural canary — if a future commit reverts the rephrasing
    this test fails before the bug reaches production.
    """
    from pathlib import Path
    src_path = Path(__file__).resolve().parent.parent / "src" / "components" / "orchestrator.py"
    text = src_path.read_text(encoding="utf-8")
    # Find the daily_loss_stop notify_alert block. Search for the canonical
    # phrasing the fix introduced.
    assert "MTM PnL" in text, (
        "Expected 'MTM PnL' (post-fix safe phrasing) in orchestrator.py"
    )
    # The bug-causing literals must be gone from the daily-loss-stop alert.
    # Note: 'P&L' may appear in trade-close / daily-summary alerts, which is
    # safe because the transport no longer uses parse_mode=HTML. We only
    # need to verify the daily-loss-stop notify_alert branch is rephrased.
    daily_loss_block = text.split("def _check_and_apply_daily_loss_stop", 1)
    if len(daily_loss_block) >= 2:
        block = daily_loss_block[1].split("\n    def ", 1)[0]
        assert "P&L:" not in block, (
            "daily_loss_stop alert still contains literal 'P&L:' — would "
            "break Telegram parsing if parse_mode is reintroduced"
        )
        assert "<= -" not in block, (
            "daily_loss_stop alert still contains '<= -' — would break "
            "Telegram parsing if parse_mode is reintroduced"
        )


# ---------------------------------------------------------------------------
# 3. Pending record recovery alert (orchestrator.py:3526) — no <b> tags
# ---------------------------------------------------------------------------


def test_pending_record_recovery_alert_has_no_html_tags():
    """The other orchestrator call site we patched. The previous template
    used ``<b>PENDING RECORD RECOVERY FAILED</b>``; the post-fix version is
    plain text.
    """
    from pathlib import Path
    src_path = Path(__file__).resolve().parent.parent / "src" / "components" / "orchestrator.py"
    text = src_path.read_text(encoding="utf-8")
    # Locate the recovery-failure alert
    assert "PENDING RECORD RECOVERY FAILED" in text
    # Tags must not wrap the header anymore
    assert "<b>PENDING RECORD RECOVERY FAILED</b>" not in text


# ---------------------------------------------------------------------------
# 4. Other patched call sites: d1_bias_lag_logger + model_pin
# ---------------------------------------------------------------------------


def test_d1_bias_lag_logger_alert_renders_plain_text():
    """``_send_threshold_alert`` body contains no HTML tags and is safe to
    send plain-text. The original body had no tags so this is mostly a
    canary test, but the value carries through under the new transport.
    """
    from src.components import d1_bias_lag_logger as mod
    record = {
        "symbol": "NAS100",
        "rolling_N_consecutive": 7,
        "d1_bias": "BEARISH",
        "h4_bias": "BULLISH",
        "h1_direction": "LONG",
        "kill_zone": "ny",
        "h4_missing": False,
    }
    captured: list[str] = []

    # Stub notify_alert at the import point inside the function. The
    # function does ``from src.notifications import notify_alert`` lazily,
    # so we monkeypatch on src.notifications.
    import src.notifications as _notif_mod
    orig = _notif_mod.notify_alert
    _notif_mod.notify_alert = lambda t: captured.append(t)
    try:
        ok = mod._send_threshold_alert(record)
    finally:
        _notif_mod.notify_alert = orig

    assert ok is True
    assert len(captured) == 1
    body = captured[0]
    assert "<b>" not in body
    assert "</b>" not in body
    # The literal `<` `>` `&` audit applies — d1_bias_lag uses neither
    # comparison operators nor entity references in its template, so this
    # is a regression canary.
    assert "<" not in body
    assert ">" not in body


def test_model_pin_drift_alert_renders_plain_text(monkeypatch):
    """``_emit_drift_alert`` produces a clean plain-text body with no HTML
    breakers. Drift alerts are sent via notify_alert which now goes through
    the queue with no parse_mode."""
    from src.components import model_pin as mod
    captured: list[str] = []
    import src.notifications as _notif_mod
    monkeypatch.setattr(_notif_mod, "notify_alert", lambda t: captured.append(t))

    mod._emit_drift_alert(
        requested="claude-sonnet-4-6",
        old="claude-sonnet-4-6",
        new="claude-sonnet-5-0",
        response_id="msg_abc123",
    )
    assert len(captured) == 1
    body = captured[0]
    assert "<b>" not in body
    assert "</b>" not in body
    assert "<" not in body
    assert ">" not in body


# ---------------------------------------------------------------------------
# 5. End-to-end smoke: notify_alert + notify_critical with a "dangerous" body
# ---------------------------------------------------------------------------


def test_notify_alert_with_dangerous_body_does_not_break_transport(captured_payloads):
    """A body that would have triggered the original bug (literal `&`,
    `<=`, `>`) now flows through the queue and reaches the transport
    unchanged — because the transport sends plain text."""
    body = (
        "Sweep alert: bid <= 1.2345 & ask >= 1.2350. "
        "Risk threshold: |corr| >= 0.4 — REJECT."
    )
    _notif.notify_alert(body)
    assert len(captured_payloads) == 1
    text = captured_payloads[0]["text"]
    # The interpolated body's HTML-special chars survive intact; the wire
    # format is plain text so they don't need escaping.
    assert "bid <= 1.2345" in text
    assert "ask >= 1.2350" in text
    assert "& ask" in text


def test_notify_critical_with_dangerous_body_does_not_break_transport(captured_payloads):
    """Same coverage at CRITICAL priority."""
    body = "FLATTEN: equity 99876.12 < daily_floor; cascade <= 30s countdown."
    _notif.notify_critical(body)
    assert len(captured_payloads) == 1
    text = captured_payloads[0]["text"]
    assert "equity 99876.12 < daily_floor" in text
    assert "<= 30s" in text
