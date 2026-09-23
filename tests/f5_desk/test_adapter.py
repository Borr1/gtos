"""Provider adapter: extraction, failover, timeout — via fake shell providers.

The fakes are invoked as ``["/bin/bash", script]`` so no exec bit is needed;
POSIX-only (the VPS runs the real CLIs; these tests run on the Mac/CI).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from scripts.f5_desk import adapter

from .conftest import FIXTURES

posix_only = pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX fake providers")


def fake(name: str, script: str) -> dict:
    return {"name": name, "argv": ["/bin/bash", str(FIXTURES / script)]}


# ---------------------------------------------------------------------------
# extraction (pure)
# ---------------------------------------------------------------------------
VERDICT = {"schema": "gtos.f5.judge.verdict.v1", "slate_id": "abc", "verdicts": [], "manage": []}


def test_extract_plain_object():
    obj, reason = adapter.extract_verdict(json.dumps(VERDICT))
    assert reason == "ok" and obj["slate_id"] == "abc"


def test_extract_from_surrounding_prose():
    text = "Sure! Here is my judgment:\n" + json.dumps(VERDICT) + "\nHope this helps."
    obj, reason = adapter.extract_verdict(text)
    assert reason == "ok" and obj["schema"] == adapter.VERDICT_SCHEMA


def test_extract_from_cli_json_envelope():
    # claude -p --output-format json wraps the reply text under "result"
    envelope = {"type": "result", "result": "prose then " + json.dumps(VERDICT), "cost_usd": 0}
    obj, reason = adapter.extract_verdict(json.dumps(envelope))
    assert reason == "ok" and obj["slate_id"] == "abc"


def test_extract_rejects_wrong_schema():
    obj, reason = adapter.extract_verdict(json.dumps({"schema": "wrong.schema", "x": 1}))
    assert obj is None and reason == "schema_mismatch"


def test_extract_rejects_garbage():
    obj, reason = adapter.extract_verdict("sorry {{{ not json ]")
    assert obj is None and reason == "no_json_object"


def test_extract_empty():
    obj, reason = adapter.extract_verdict("")
    assert obj is None and reason == "empty_output"


# ---------------------------------------------------------------------------
# calls + failover
# ---------------------------------------------------------------------------
@posix_only
def test_ok_provider_returns_verdict(tmp_path):
    verdict, meta = adapter.call_with_failover(
        'prompt with "slate_id": "deadbeefdeadbeef" inside',
        providers=[fake("ok", "fake_provider_ok.sh")], timeout_s=30,
    )
    assert verdict is not None
    assert verdict["schema"] == adapter.VERDICT_SCHEMA
    assert verdict["slate_id"] == "deadbeefdeadbeef"  # echoed back from the prompt
    assert meta["provider"] == "ok"
    assert meta["attempts"][0]["ok"] is True
    assert meta["attempts"][0]["latency_ms"] is not None


@posix_only
def test_malformed_provider_fails_over_to_ok(tmp_path):
    verdict, meta = adapter.call_with_failover(
        '"slate_id": "feedfacefeedface"',
        providers=[fake("bad", "fake_provider_malformed.sh"),
                   fake("ok", "fake_provider_ok.sh")],
        timeout_s=30,
    )
    assert verdict is not None and meta["provider"] == "ok"
    assert meta["attempts"][0]["ok"] is False
    assert meta["attempts"][0]["fail_reason"] == "no_json_object"


@posix_only
def test_all_dark_returns_none(tmp_path):
    verdict, meta = adapter.call_with_failover(
        "prompt",
        providers=[fake("bad", "fake_provider_malformed.sh")], timeout_s=30,
    )
    assert verdict is None
    assert len(meta["attempts"]) == 1 and meta["provider"] is None


@posix_only
def test_timeout_fails_over(tmp_path):
    verdict, meta = adapter.call_with_failover(
        '"slate_id": "009abcdef"',
        providers=[fake("slow", "fake_provider_slow.sh"),
                   fake("ok", "fake_provider_ok.sh")],
        timeout_s=1,
    )
    assert verdict is not None and meta["provider"] == "ok"
    assert meta["attempts"][0]["fail_reason"].startswith("timeout_")


def test_missing_executable_fails_over_cleanly(tmp_path):
    verdict, meta = adapter.call_with_failover(
        "prompt",
        providers=[{"name": "ghost", "argv": ["/definitely/not/a/binary/xyz"]}],
        timeout_s=5,
    )
    assert verdict is None
    assert meta["attempts"][0]["fail_reason"] == "executable_not_found"


def test_marked_missing_provider_skipped_without_exec(tmp_path):
    verdict, meta = adapter.call_with_failover(
        "prompt",
        providers=[{"name": "claude", "argv": ["claude"], "missing": True}],
        timeout_s=5,
    )
    assert verdict is None
    assert meta["attempts"][0]["fail_reason"] == "executable_not_found"


@posix_only
def test_call_log_written(tmp_path):
    log_path = tmp_path / "adapter_calls.jsonl"
    adapter.call_with_failover(
        "prompt", providers=[fake("ok", "fake_provider_ok.sh")],
        timeout_s=30, log_path=log_path,
    )
    rows = [json.loads(l) for l in log_path.read_text().splitlines()]
    assert rows and rows[0]["kind"] == "adapter_call"
    assert rows[0]["name"] == "ok" and rows[0]["ok"] is True
    assert "verdict" not in rows[0] and "prompt" not in rows[0]


def test_default_providers_ordered_claude_first():
    providers = adapter.default_providers()
    assert [p["name"] for p in providers] == ["claude", "cursor-agent", "codex"]
    for p in providers:
        assert isinstance(p["argv"], list) and p["argv"]
