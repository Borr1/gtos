"""Tests for ``src.components.model_pin`` — T1.4 model-id pinning + drift alert.

Canonical patterns (per session 21 canon):
- All writes redirect to ``tmp_path`` via module-ref monkeypatch on
  ``_mod.PIN_PATH`` (NOT on any ``from X import Y`` rebind). Writing directly
  to ``knowledge_base/meta/model_pin.json`` under the project root would
  trigger the ``ProductionWriteError`` guard installed by ``tests/conftest.py``.
- Telegram is never exercised over the wire — ``notify_alert`` is stubbed via
  monkeypatch.
- A small stub for the Anthropic response is used only where an end-to-end
  analyzer path is exercised (see ``TestPrimaryAnalyzerIntegration``); the
  direct ``record_served_model`` tests pass primitives.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.components import model_pin as _mod


# =============================================================================
# Common fixture — redirect PIN_PATH to tmp_path, stub Telegram
# =============================================================================


@pytest.fixture
def isolated_pin(tmp_path, monkeypatch):
    """Redirect the pin file and capture notify_alert calls."""
    pin_path = tmp_path / "model_pin.json"
    monkeypatch.setattr(_mod, "PIN_PATH", pin_path)

    alerts = []

    def _capture_alert(text: str) -> None:
        alerts.append(text)

    # Patch the lazy import target inside _emit_drift_alert. The import happens
    # at call-time so we patch on src.notifications where the name lives.
    import src.notifications as _notif_mod
    monkeypatch.setattr(_notif_mod, "notify_alert", _capture_alert)

    return {"path": pin_path, "alerts": alerts}


def _read_pin(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# =============================================================================
# First-call-silent: no prior pin → pin established, no alert
# =============================================================================


class TestFirstCallSilent:
    def test_no_pin_file_seeds_pin_and_does_not_alert(self, isolated_pin):
        result = _mod.record_served_model(
            "claude-sonnet-4-6",
            "claude-sonnet-4-6-20260101",
            "msg_abc123",
        )

        assert result["status"] == "pinned_first_time"
        assert result["pinned_model"] == "claude-sonnet-4-6-20260101"
        assert isolated_pin["alerts"] == []

        pin = _read_pin(isolated_pin["path"])
        assert pin["pinned_model"] == "claude-sonnet-4-6-20260101"
        assert pin["requested_model"] == "claude-sonnet-4-6"
        assert pin["last_response_id"] == "msg_abc123"
        assert pin["drift_history"] == []
        # Timestamps populated
        assert pin["first_seen_at"]
        assert pin["pinned_at"] == pin["first_seen_at"]
        assert pin["last_seen_at"] == pin["first_seen_at"]

    def test_pin_parent_dir_is_created_if_missing(self, tmp_path, monkeypatch):
        # Simulate a fresh install where knowledge_base/meta doesn't exist yet.
        deep_path = tmp_path / "a" / "b" / "c" / "model_pin.json"
        monkeypatch.setattr(_mod, "PIN_PATH", deep_path)

        assert not deep_path.parent.exists()
        result = _mod.record_served_model("sonnet", "sonnet-v1", "msg_1")
        assert result["status"] == "pinned_first_time"
        assert deep_path.exists()


# =============================================================================
# No-drift path: served matches pin → silent update of last_seen
# =============================================================================


class TestNoDrift:
    def test_served_matches_pin_no_alert(self, isolated_pin):
        _mod.record_served_model("claude-sonnet-4-6", "claude-sonnet-4-6-20260101", "msg_1")
        isolated_pin["alerts"].clear()

        result = _mod.record_served_model(
            "claude-sonnet-4-6",
            "claude-sonnet-4-6-20260101",
            "msg_2",
        )

        assert result["status"] == "no_drift"
        assert isolated_pin["alerts"] == []

        pin = _read_pin(isolated_pin["path"])
        assert pin["pinned_model"] == "claude-sonnet-4-6-20260101"
        assert pin["last_response_id"] == "msg_2"
        assert pin["drift_history"] == []
        # last_seen advanced, first_seen unchanged, no new drift entry
        assert pin["last_seen_at"] >= pin["first_seen_at"]
        assert pin["pinned_at"] == pin["first_seen_at"]

    def test_multiple_no_drift_calls_keep_history_empty(self, isolated_pin):
        # First call seeds, five subsequent matches
        for i in range(6):
            _mod.record_served_model("sonnet", "sonnet-v1", f"msg_{i}")

        pin = _read_pin(isolated_pin["path"])
        assert pin["drift_history"] == []
        assert isolated_pin["alerts"] == []


# =============================================================================
# Drift path: served differs from pin → alert + pin updated + history appended
# =============================================================================


class TestDriftTriggersAlert:
    def test_drift_fires_alert_and_updates_pin(self, isolated_pin):
        # Seed
        _mod.record_served_model("claude-sonnet-4-6", "claude-sonnet-4-6-20260101", "msg_1")
        isolated_pin["alerts"].clear()

        # Drift
        result = _mod.record_served_model(
            "claude-sonnet-4-6",
            "claude-sonnet-4-6-20260215",  # newer snapshot
            "msg_drift",
        )

        assert result["status"] == "drift"
        assert result["from"] == "claude-sonnet-4-6-20260101"
        assert result["to"] == "claude-sonnet-4-6-20260215"

        # Alert fired — single message with old + new
        assert len(isolated_pin["alerts"]) == 1
        msg = isolated_pin["alerts"][0]
        assert "MODEL DRIFT" in msg
        assert "claude-sonnet-4-6-20260101" in msg
        assert "claude-sonnet-4-6-20260215" in msg
        assert "msg_drift" in msg

        # Pin updated to new value, history appended
        pin = _read_pin(isolated_pin["path"])
        assert pin["pinned_model"] == "claude-sonnet-4-6-20260215"
        assert pin["last_response_id"] == "msg_drift"
        assert len(pin["drift_history"]) == 1
        entry = pin["drift_history"][0]
        assert entry["from"] == "claude-sonnet-4-6-20260101"
        assert entry["to"] == "claude-sonnet-4-6-20260215"
        assert entry["response_id"] == "msg_drift"

    def test_second_drift_does_not_realert_on_old_value(self, isolated_pin):
        # This is the regression guard: once we've detected A→B and updated
        # the pin, a follow-up call at B must NOT re-alert. It should only
        # alert if we drift again (B→C).
        _mod.record_served_model("sonnet", "v1", "msg_1")
        _mod.record_served_model("sonnet", "v2", "msg_2")  # A→B alert #1
        isolated_pin["alerts"].clear()

        _mod.record_served_model("sonnet", "v2", "msg_3")  # B→B no alert
        assert isolated_pin["alerts"] == []

        _mod.record_served_model("sonnet", "v3", "msg_4")  # B→C alert #2
        assert len(isolated_pin["alerts"]) == 1
        assert "v2" in isolated_pin["alerts"][0]
        assert "v3" in isolated_pin["alerts"][0]

        pin = _read_pin(isolated_pin["path"])
        assert pin["pinned_model"] == "v3"
        assert len(pin["drift_history"]) == 2
        assert pin["drift_history"][0]["from"] == "v1"
        assert pin["drift_history"][0]["to"] == "v2"
        assert pin["drift_history"][1]["from"] == "v2"
        assert pin["drift_history"][1]["to"] == "v3"

    def test_requested_model_change_does_not_alert_if_served_matches(self, isolated_pin):
        # Operator might swap requested model (alias) while served snapshot is
        # unchanged. We pin on SERVED, so this is NOT drift.
        _mod.record_served_model("claude-sonnet-4-6", "sonnet-4-6-snap1", "msg_1")
        isolated_pin["alerts"].clear()

        result = _mod.record_served_model("claude-sonnet-4-5", "sonnet-4-6-snap1", "msg_2")
        assert result["status"] == "no_drift"
        assert isolated_pin["alerts"] == []

        # But requested_model still updated for audit
        pin = _read_pin(isolated_pin["path"])
        assert pin["requested_model"] == "claude-sonnet-4-5"


# =============================================================================
# Pin-file-corrupt path: unreadable or malformed file → treat as unpinned
# =============================================================================


class TestPinFileCorrupt:
    def test_corrupt_json_treated_as_unpinned_first_call(self, isolated_pin):
        # Write garbage to the pin file, then call record
        isolated_pin["path"].parent.mkdir(parents=True, exist_ok=True)
        isolated_pin["path"].write_text("this is not json", encoding="utf-8")

        result = _mod.record_served_model("sonnet", "sonnet-v1", "msg_1")
        # Corrupt file should be silently replaced by a fresh first-call pin
        assert result["status"] == "pinned_first_time"
        assert isolated_pin["alerts"] == []

        pin = _read_pin(isolated_pin["path"])
        assert pin["pinned_model"] == "sonnet-v1"
        assert pin["drift_history"] == []

    def test_pin_file_non_dict_treated_as_unpinned(self, isolated_pin):
        isolated_pin["path"].parent.mkdir(parents=True, exist_ok=True)
        isolated_pin["path"].write_text("[1, 2, 3]", encoding="utf-8")

        result = _mod.record_served_model("sonnet", "sonnet-v1", "msg_1")
        assert result["status"] == "pinned_first_time"
        assert isolated_pin["alerts"] == []

    def test_pin_missing_pinned_model_key_seeds_fresh(self, isolated_pin):
        # Dict but with no pinned_model key (partial / legacy schema)
        isolated_pin["path"].parent.mkdir(parents=True, exist_ok=True)
        isolated_pin["path"].write_text(json.dumps({"foo": "bar"}), encoding="utf-8")

        result = _mod.record_served_model("sonnet", "sonnet-v1", "msg_1")
        assert result["status"] == "pinned_first_time"

    def test_write_failure_returns_false_does_not_raise(self, isolated_pin, monkeypatch):
        # If _save_pin returns False (disk full, permission denied, etc.),
        # record_served_model must still not raise. The pin just won't be
        # persisted — next call will see "no pin" and reseed as first-call.
        monkeypatch.setattr(_mod, "_save_pin", lambda *a, **k: False)
        result = _mod.record_served_model("sonnet", "sonnet-v1", "msg_1")
        # record_served_model must never raise
        assert result["status"] == "pinned_first_time"
        # And the file should not have been created
        assert not isolated_pin["path"].exists()

    def test_save_pin_raising_is_swallowed_by_outer_guard(self, isolated_pin, monkeypatch):
        # If _save_pin somehow raises (e.g. someone replaces it with a broken
        # stub), the outer try/except in record_served_model must catch it
        # so the trading pipeline never sees the exception.
        def _boom(*args, **kwargs):
            raise OSError("disk full")

        monkeypatch.setattr(_mod, "_save_pin", _boom)
        # Must not raise
        result = _mod.record_served_model("sonnet", "sonnet-v1", "msg_1")
        assert result["status"] == "skipped"
        assert "unexpected_error" in result.get("reason", "")


# =============================================================================
# Notify-fails path: Telegram send raises → pin still updates, no exception
# =============================================================================


class TestNotifyFailsSwallow:
    def test_notify_raises_does_not_break_pin_update(self, tmp_path, monkeypatch):
        pin_path = tmp_path / "model_pin.json"
        monkeypatch.setattr(_mod, "PIN_PATH", pin_path)

        def _explode(text: str) -> None:
            raise RuntimeError("telegram offline")

        import src.notifications as _notif_mod
        monkeypatch.setattr(_notif_mod, "notify_alert", _explode)

        # Seed
        _mod.record_served_model("sonnet", "v1", "msg_1")
        # Drift with a notify that raises
        result = _mod.record_served_model("sonnet", "v2", "msg_2")

        # Drift was still detected and pin still updated, even though notify
        # blew up. This is the fail-open invariant.
        assert result["status"] == "drift"
        pin = _read_pin(pin_path)
        assert pin["pinned_model"] == "v2"
        assert len(pin["drift_history"]) == 1

    def test_notifications_import_error_swallowed(self, tmp_path, monkeypatch):
        """If src.notifications cannot even be imported, we still update the pin."""
        pin_path = tmp_path / "model_pin.json"
        monkeypatch.setattr(_mod, "PIN_PATH", pin_path)

        # Monkeypatch the lazy import inside _emit_drift_alert by replacing
        # the emitter entirely with something that raises ImportError-like.
        def _fake_emit(*args, **kwargs):
            raise ImportError("no such module")

        monkeypatch.setattr(_mod, "_emit_drift_alert", _fake_emit)

        _mod.record_served_model("sonnet", "v1", "msg_1")
        result = _mod.record_served_model("sonnet", "v2", "msg_2")
        # Must not raise
        assert result["status"] == "drift"
        pin = _read_pin(pin_path)
        assert pin["pinned_model"] == "v2"


# =============================================================================
# Guard inputs — None / empty / non-string served model
# =============================================================================


class TestBadInputs:
    def test_none_served_model_skipped(self, isolated_pin):
        result = _mod.record_served_model("sonnet", None, "msg_1")
        assert result["status"] == "skipped"
        assert not isolated_pin["path"].exists()
        assert isolated_pin["alerts"] == []

    def test_empty_served_model_skipped(self, isolated_pin):
        result = _mod.record_served_model("sonnet", "", "msg_1")
        assert result["status"] == "skipped"
        assert not isolated_pin["path"].exists()

    def test_non_string_served_model_skipped(self, isolated_pin):
        result = _mod.record_served_model("sonnet", 42, "msg_1")
        assert result["status"] == "skipped"

    def test_none_response_id_accepted(self, isolated_pin):
        # response_id is optional — None must be acceptable
        result = _mod.record_served_model("sonnet", "sonnet-v1", None)
        assert result["status"] == "pinned_first_time"
        pin = _read_pin(isolated_pin["path"])
        assert pin["last_response_id"] is None


# =============================================================================
# Integration — primary_analyzer wires the pin call into _call_claude
# =============================================================================


class TestPrimaryAnalyzerIntegration:
    """Verify primary_analyzer.PrimaryAnalyzer._call_claude records the served model.

    We don't exercise the full analyze() path here — just _call_claude to
    confirm wiring. A small stub replaces the SDK client.
    """

    def _make_analyzer(self):
        from src.components import primary_analyzer as _pa_mod
        from src.components.primary_analyzer import PrimaryAnalyzer
        from src.components.knowledge_base import KnowledgeBase

        cfg = {"ai": {
            "primary_model": "claude-sonnet-4-6",
            "api_timeout_seconds": 30,
            "max_api_retries": 0,
        }}
        kb = MagicMock(spec=KnowledgeBase)
        analyzer = PrimaryAnalyzer(cfg, kb)
        return analyzer, _pa_mod

    def _make_sdk_response(self, model: str, response_id: str, text: str = "{}"):
        """Build a minimally-attribute response that matches SDK surface."""
        resp = MagicMock()
        resp.model = model
        resp.id = response_id
        resp.usage = MagicMock(
            input_tokens=100,
            output_tokens=50,
            cache_read_input_tokens=0,
            cache_creation_input_tokens=0,
        )
        content = MagicMock()
        content.text = text
        resp.content = [content]
        return resp

    def test_call_claude_records_first_served_model(self, tmp_path, monkeypatch):
        analyzer, _pa_mod = self._make_analyzer()

        # Redirect pin file
        pin_path = tmp_path / "model_pin.json"
        monkeypatch.setattr(_mod, "PIN_PATH", pin_path)

        # Stub the SDK client
        resp = self._make_sdk_response("claude-sonnet-4-6-20260101", "msg_first", '{"ok": true}')
        analyzer.client = MagicMock()
        analyzer.client.messages.create.return_value = resp

        out = analyzer._call_claude([{"type": "text", "text": "sys"}], "user")
        assert out == '{"ok": true}'

        # Pin file created from the first call
        assert pin_path.exists()
        pin = _read_pin(pin_path)
        assert pin["pinned_model"] == "claude-sonnet-4-6-20260101"
        assert pin["last_response_id"] == "msg_first"
        assert pin["drift_history"] == []

    def test_call_claude_fires_alert_on_drift(self, tmp_path, monkeypatch):
        analyzer, _pa_mod = self._make_analyzer()
        pin_path = tmp_path / "model_pin.json"
        monkeypatch.setattr(_mod, "PIN_PATH", pin_path)

        # Capture alerts
        alerts = []
        import src.notifications as _notif_mod
        monkeypatch.setattr(_notif_mod, "notify_alert", lambda t: alerts.append(t))

        # First call seeds pin
        r1 = self._make_sdk_response("sonnet-4-6-v1", "msg_1")
        analyzer.client = MagicMock()
        analyzer.client.messages.create.return_value = r1
        analyzer._call_claude([{"type": "text", "text": "sys"}], "u")
        assert alerts == []

        # Second call returns a different snapshot — drift
        r2 = self._make_sdk_response("sonnet-4-6-v2", "msg_2")
        analyzer.client.messages.create.return_value = r2
        analyzer._call_claude([{"type": "text", "text": "sys"}], "u")

        assert len(alerts) == 1
        assert "sonnet-4-6-v1" in alerts[0]
        assert "sonnet-4-6-v2" in alerts[0]

    def test_call_claude_survives_pin_module_exception(self, tmp_path, monkeypatch):
        """If record_served_model raises despite its internal try/except (e.g. a
        monkeypatched broken implementation), _call_claude MUST still return the
        response text. The outer try/except in primary_analyzer is the final
        line of defense for the trading pipeline."""
        analyzer, _pa_mod = self._make_analyzer()

        def _explode(*args, **kwargs):
            raise RuntimeError("pin module fatally broken")

        monkeypatch.setattr(_pa_mod._model_pin, "record_served_model", _explode)

        r = self._make_sdk_response("sonnet-4-6-v1", "msg_1", '{"decision":"NO_TRADE"}')
        analyzer.client = MagicMock()
        analyzer.client.messages.create.return_value = r

        # Must NOT raise despite pin module exploding
        text = analyzer._call_claude([{"type": "text", "text": "sys"}], "u")
        assert text == '{"decision":"NO_TRADE"}'

    def test_call_claude_handles_missing_model_attr(self, tmp_path, monkeypatch):
        """SDK response without .model or .id should not alert, should not raise."""
        analyzer, _pa_mod = self._make_analyzer()
        pin_path = tmp_path / "model_pin.json"
        monkeypatch.setattr(_mod, "PIN_PATH", pin_path)

        # Build a response with NO model / id attributes (fresh object, not MagicMock)
        class BareResponse:
            pass

        r = BareResponse()
        r.usage = MagicMock(
            input_tokens=10, output_tokens=5,
            cache_read_input_tokens=0, cache_creation_input_tokens=0,
        )
        content = MagicMock(); content.text = "{}"
        r.content = [content]

        analyzer.client = MagicMock()
        analyzer.client.messages.create.return_value = r

        # Must not raise; served is None → pin stays unset
        out = analyzer._call_claude([{"type": "text", "text": "sys"}], "u")
        assert out == "{}"
        # No pin created (bad input skipped)
        assert not pin_path.exists()
