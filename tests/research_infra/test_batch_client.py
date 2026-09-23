"""Unit tests for ``src.research_infra.batch_client.BatchClient``.

All tests inject a fake SDK client via ``sdk_client=``. NO real network calls
or ANTHROPIC_API_KEY usage. Anthropic exception classes ARE imported here
because the wrapper's retry classifier inspects exception types — we need
the real types to exercise the retry path.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
from anthropic import APIConnectionError, InternalServerError

from src.research_infra.batch_client import (
    BatchClient,
    BatchNotEndedError,
    BatchRequest,
    BatchResult,
    BatchTerminalError,
    MAX_REQUESTS_PER_BATCH,
)


# ---------------------------------------------------------------------------
# Fakes — minimal stand-ins for the SDK shape the wrapper consumes
# ---------------------------------------------------------------------------


class _FakeRequestCounts:
    def __init__(self, processing=0, succeeded=0, errored=0, canceled=0, expired=0):
        self.processing = processing
        self.succeeded = succeeded
        self.errored = errored
        self.canceled = canceled
        self.expired = expired

    def model_dump(self):
        return {
            "processing": self.processing,
            "succeeded": self.succeeded,
            "errored": self.errored,
            "canceled": self.canceled,
            "expired": self.expired,
        }


class _FakeMessageBatch:
    def __init__(
        self,
        batch_id: str,
        processing_status: str = "in_progress",
        request_counts: _FakeRequestCounts | None = None,
    ):
        self.id = batch_id
        self.processing_status = processing_status
        self.request_counts = request_counts or _FakeRequestCounts()


class _FakeUsage:
    def __init__(
        self,
        input_tokens=0,
        output_tokens=0,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=0,
    ):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_creation_input_tokens = cache_creation_input_tokens
        self.cache_read_input_tokens = cache_read_input_tokens


class _FakeContentBlock:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _FakeMessage:
    def __init__(self, text: str, stop_reason: str = "end_turn", usage=None):
        self.content = [_FakeContentBlock(text)]
        self.stop_reason = stop_reason
        self.usage = usage or _FakeUsage(input_tokens=10, output_tokens=5)


class _FakeIndividualResponse:
    """Mimics MessageBatchIndividualResponse with a simple ``result``."""

    def __init__(self, custom_id: str, result_obj: Any):
        self.custom_id = custom_id
        self.result = result_obj


class _FakeSucceededResult:
    def __init__(self, message: _FakeMessage):
        self.type = "succeeded"
        self.message = message


class _FakeErroredResult:
    def __init__(self, error_dict: dict):
        self.type = "errored"
        self.error = error_dict


class _FakeBatchesResource:
    """Stand-in for ``client.messages.batches``.

    Holds a script of behaviors that ``submit_batch`` / ``poll_status`` /
    ``fetch_results`` consume in order. Tests register the script with one of
    the helper builders below.
    """

    def __init__(self):
        self.create_calls: list[Any] = []
        self.retrieve_calls: list[str] = []
        self.results_calls: list[str] = []
        self._create_responses: list[Any] = []
        self._retrieve_responses: list[Any] = []
        self._results_responses: list[Any] = []

    # script setters
    def queue_create(self, *responses):
        self._create_responses.extend(responses)

    def queue_retrieve(self, *responses):
        self._retrieve_responses.extend(responses)

    def queue_results(self, *responses):
        self._results_responses.extend(responses)

    # SDK-shaped methods
    def create(self, *, requests):  # noqa: D401 — match SDK signature
        self.create_calls.append(list(requests))
        if not self._create_responses:
            raise AssertionError("FakeBatches.create called with empty queue")
        resp = self._create_responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp

    def retrieve(self, batch_id):
        self.retrieve_calls.append(batch_id)
        if not self._retrieve_responses:
            raise AssertionError("FakeBatches.retrieve called with empty queue")
        resp = self._retrieve_responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp

    def results(self, batch_id):
        self.results_calls.append(batch_id)
        if not self._results_responses:
            raise AssertionError("FakeBatches.results called with empty queue")
        resp = self._results_responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp


class _FakeMessagesResource:
    def __init__(self):
        self.batches = _FakeBatchesResource()


class _FakeAnthropic:
    def __init__(self):
        self.messages = _FakeMessagesResource()


@pytest.fixture
def fake_client():
    return _FakeAnthropic()


@pytest.fixture
def batch_client(fake_client):
    # polling_interval=0 keeps the wait_and_fetch tests instant
    return BatchClient(
        sdk_client=fake_client, polling_interval_seconds=1, max_wait_seconds=5
    )


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    """Replace time.sleep in batch_client with a no-op so tests are fast.

    Retries and polling intervals invoke time.sleep; we don't want real wall
    time. The monkeypatch only affects the module under test.
    """
    import src.research_infra.batch_client as mod

    monkeypatch.setattr(mod.time, "sleep", lambda _s: None)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_submit_poll_fetch_happy_path(batch_client, fake_client):
    """Submit two requests → poll moves in_progress → ended → fetch returns
    one BatchResult per custom_id with content_text + usage populated."""
    fake_batches = fake_client.messages.batches

    # 1. submit
    fake_batches.queue_create(_FakeMessageBatch(batch_id="batch_abc"))

    # 2. poll: first in_progress, then ended
    fake_batches.queue_retrieve(
        _FakeMessageBatch(
            batch_id="batch_abc",
            processing_status="in_progress",
            request_counts=_FakeRequestCounts(processing=2),
        ),
        _FakeMessageBatch(
            batch_id="batch_abc",
            processing_status="ended",
            request_counts=_FakeRequestCounts(succeeded=2),
        ),
        # fetch_results internally calls poll_status one more time
        _FakeMessageBatch(
            batch_id="batch_abc",
            processing_status="ended",
            request_counts=_FakeRequestCounts(succeeded=2),
        ),
    )

    # 3. results jsonl
    fake_batches.queue_results(
        iter(
            [
                _FakeIndividualResponse(
                    "req-1",
                    _FakeSucceededResult(
                        _FakeMessage(
                            "OK one",
                            stop_reason="end_turn",
                            usage=_FakeUsage(
                                input_tokens=11,
                                output_tokens=2,
                                cache_creation_input_tokens=0,
                                cache_read_input_tokens=11,
                            ),
                        )
                    ),
                ),
                _FakeIndividualResponse(
                    "req-2",
                    _FakeSucceededResult(
                        _FakeMessage(
                            "OK two",
                            stop_reason="end_turn",
                            usage=_FakeUsage(input_tokens=12, output_tokens=3),
                        )
                    ),
                ),
            ]
        )
    )

    requests = [
        BatchRequest(
            custom_id="req-1",
            model="claude-haiku-4-5-20251001",
            messages=[{"role": "user", "content": "say one"}],
            max_tokens=10,
        ),
        BatchRequest(
            custom_id="req-2",
            model="claude-haiku-4-5-20251001",
            messages=[{"role": "user", "content": "say two"}],
            max_tokens=10,
        ),
    ]
    batch_id = batch_client.submit_batch(requests)
    assert batch_id == "batch_abc"

    results = batch_client.wait_and_fetch(batch_id)
    assert set(results.keys()) == {"req-1", "req-2"}
    assert results["req-1"].content_text == "OK one"
    assert results["req-1"].error is None
    assert results["req-1"].usage["input_tokens"] == 11
    assert results["req-1"].usage["cache_read_input_tokens"] == 11
    assert results["req-2"].content_text == "OK two"
    assert fake_batches.create_calls, "create() should have been invoked"


def test_submit_passes_request_shape_to_sdk(batch_client, fake_client):
    fake_batches = fake_client.messages.batches
    fake_batches.queue_create(_FakeMessageBatch(batch_id="batch_x"))

    req = BatchRequest(
        custom_id="r1",
        model="claude-haiku-4-5-20251001",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=20,
        system="you are a test bot",
        temperature=0.0,
    )
    batch_client.submit_batch([req])

    assert fake_batches.create_calls, "create() should have been called"
    sent = fake_batches.create_calls[0]
    assert len(sent) == 1
    assert sent[0]["custom_id"] == "r1"
    params = sent[0]["params"]
    assert params["model"] == "claude-haiku-4-5-20251001"
    assert params["max_tokens"] == 20
    assert params["messages"] == [{"role": "user", "content": "hi"}]
    assert params["system"] == "you are a test bot"
    assert params["temperature"] == 0.0


# ---------------------------------------------------------------------------
# Cache-control + effort passthrough
# ---------------------------------------------------------------------------


def test_cache_control_1h_passthrough(batch_client, fake_client):
    """Caller embeds 1h cache_control inside system blocks. Wrapper must
    forward the blocks verbatim (no rewrite, no drop). ``cache_ttl`` on the
    BatchRequest is informational and does NOT alter the content blocks."""
    fake_batches = fake_client.messages.batches
    fake_batches.queue_create(_FakeMessageBatch(batch_id="batch_cache"))

    system_blocks = [
        {
            "type": "text",
            "text": "long static context",
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        },
    ]
    req = BatchRequest(
        custom_id="r1",
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "go"}],
        max_tokens=50,
        system=system_blocks,
        cache_ttl="1h",
    )
    batch_client.submit_batch([req])

    sent_params = fake_batches.create_calls[0][0]["params"]
    assert sent_params["system"] == system_blocks
    # Verify exact ttl literal preserved
    assert sent_params["system"][0]["cache_control"]["ttl"] == "1h"


def test_cache_control_5m_default_ttl_passthrough(batch_client, fake_client):
    fake_batches = fake_client.messages.batches
    fake_batches.queue_create(_FakeMessageBatch(batch_id="batch_cache_5m"))

    system_blocks = [
        {
            "type": "text",
            "text": "static",
            "cache_control": {"type": "ephemeral"},  # default 5m, no ttl key
        }
    ]
    req = BatchRequest(
        custom_id="r1",
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "go"}],
        max_tokens=50,
        system=system_blocks,
        cache_ttl="5m",
    )
    batch_client.submit_batch([req])
    sent_params = fake_batches.create_calls[0][0]["params"]
    assert sent_params["system"] == system_blocks
    assert "ttl" not in sent_params["system"][0]["cache_control"]


def test_effort_max_passthrough(batch_client, fake_client):
    """``output_config={"effort":"max"}`` reaches the SDK as
    ``params.output_config``."""
    fake_batches = fake_client.messages.batches
    fake_batches.queue_create(_FakeMessageBatch(batch_id="batch_effort"))

    req = BatchRequest(
        custom_id="r1",
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "go"}],
        max_tokens=2000,
        output_config={"effort": "max"},
    )
    batch_client.submit_batch([req])

    sent_params = fake_batches.create_calls[0][0]["params"]
    assert sent_params["output_config"] == {"effort": "max"}


# ---------------------------------------------------------------------------
# Validation: dedup, empty, oversize
# ---------------------------------------------------------------------------


def test_duplicate_custom_id_rejected(batch_client):
    requests = [
        BatchRequest(
            custom_id="dup",
            model="m",
            messages=[{"role": "user", "content": "a"}],
            max_tokens=10,
        ),
        BatchRequest(
            custom_id="dup",
            model="m",
            messages=[{"role": "user", "content": "b"}],
            max_tokens=10,
        ),
    ]
    with pytest.raises(ValueError, match="Duplicate custom_id"):
        batch_client.submit_batch(requests)


def test_empty_custom_id_rejected(batch_client):
    requests = [
        BatchRequest(
            custom_id="",
            model="m",
            messages=[{"role": "user", "content": "a"}],
            max_tokens=10,
        ),
    ]
    with pytest.raises(ValueError, match="custom_id must be a non-empty string"):
        batch_client.submit_batch(requests)


def test_empty_batch_rejected(batch_client):
    with pytest.raises(ValueError, match="non-empty list of requests"):
        batch_client.submit_batch([])


def test_oversize_batch_rejected(batch_client):
    """Construct ``MAX_REQUESTS_PER_BATCH + 1`` cheap stubs; pre-network
    validation must reject before any SDK call. We do NOT materialize the
    full BatchRequest list of 100k+1 — instead we verify the bound itself by
    crafting a list one over the limit using a generator-realized list. This
    keeps the test fast (~ms) and faithful to the production limit constant."""
    over_limit = MAX_REQUESTS_PER_BATCH + 1
    # Build a tight structure — share the same dict to keep memory flat.
    requests = [
        BatchRequest(
            custom_id=f"r{i}",
            model="m",
            messages=[{"role": "user", "content": "a"}],
            max_tokens=10,
        )
        for i in range(over_limit)
    ]
    with pytest.raises(ValueError, match="exceeds API limit"):
        batch_client.submit_batch(requests)


# ---------------------------------------------------------------------------
# Premature fetch
# ---------------------------------------------------------------------------


def test_fetch_before_ended_raises(batch_client, fake_client):
    fake_batches = fake_client.messages.batches
    fake_batches.queue_retrieve(
        _FakeMessageBatch(
            batch_id="b",
            processing_status="in_progress",
            request_counts=_FakeRequestCounts(processing=3),
        )
    )
    with pytest.raises(BatchNotEndedError):
        batch_client.fetch_results("b")


# ---------------------------------------------------------------------------
# Retry path: 5xx, then success
# ---------------------------------------------------------------------------


def _make_503_error() -> InternalServerError:
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages/batches")
    resp = httpx.Response(503, request=req)
    return InternalServerError("server overloaded", response=resp, body=None)


def test_retry_on_5xx_then_success(batch_client, fake_client):
    fake_batches = fake_client.messages.batches
    fake_batches.queue_create(_make_503_error(), _FakeMessageBatch(batch_id="batch_r"))

    req = BatchRequest(
        custom_id="r1",
        model="m",
        messages=[{"role": "user", "content": "x"}],
        max_tokens=10,
    )
    batch_id = batch_client.submit_batch([req])

    assert batch_id == "batch_r"
    # Two attempts: the 503 + the success
    assert len(fake_batches.create_calls) == 2


def test_retry_on_connection_error_then_success(batch_client, fake_client):
    fake_batches = fake_client.messages.batches
    req_obj = httpx.Request(
        "POST", "https://api.anthropic.com/v1/messages/batches"
    )
    fake_batches.queue_create(
        APIConnectionError(request=req_obj),
        _FakeMessageBatch(batch_id="batch_conn"),
    )
    req = BatchRequest(
        custom_id="r1",
        model="m",
        messages=[{"role": "user", "content": "x"}],
        max_tokens=10,
    )
    assert batch_client.submit_batch([req]) == "batch_conn"
    assert len(fake_batches.create_calls) == 2


def test_retry_exhausted_reraises(batch_client, fake_client):
    """Four 5xx in a row → after 3 retries we re-raise the last one."""
    fake_batches = fake_client.messages.batches
    fake_batches.queue_create(
        _make_503_error(), _make_503_error(), _make_503_error(), _make_503_error()
    )
    req = BatchRequest(
        custom_id="r1",
        model="m",
        messages=[{"role": "user", "content": "x"}],
        max_tokens=10,
    )
    with pytest.raises(InternalServerError):
        batch_client.submit_batch([req])
    # 1 initial + 3 retries == 4 attempts
    assert len(fake_batches.create_calls) == 4


def test_4xx_not_retried(batch_client, fake_client):
    """A non-retryable error (e.g. ValueError from arg-checking inside the
    SDK) propagates immediately without retry."""
    fake_batches = fake_client.messages.batches
    fake_batches.queue_create(ValueError("bad request"))
    req = BatchRequest(
        custom_id="r1",
        model="m",
        messages=[{"role": "user", "content": "x"}],
        max_tokens=10,
    )
    with pytest.raises(ValueError, match="bad request"):
        batch_client.submit_batch([req])
    assert len(fake_batches.create_calls) == 1


# ---------------------------------------------------------------------------
# Terminal error states
# ---------------------------------------------------------------------------


def test_canceled_batch_raises_via_wait_and_fetch(batch_client, fake_client):
    fake_batches = fake_client.messages.batches
    fake_batches.queue_retrieve(
        _FakeMessageBatch(
            batch_id="b",
            processing_status="ended",
            request_counts=_FakeRequestCounts(canceled=3),
        )
    )
    with pytest.raises(BatchTerminalError, match="canceled"):
        batch_client.wait_and_fetch("b")


def test_expired_batch_raises_via_wait_and_fetch(batch_client, fake_client):
    fake_batches = fake_client.messages.batches
    fake_batches.queue_retrieve(
        _FakeMessageBatch(
            batch_id="b",
            processing_status="ended",
            request_counts=_FakeRequestCounts(expired=2),
        )
    )
    with pytest.raises(BatchTerminalError, match="expired"):
        batch_client.wait_and_fetch("b")


def test_errored_batch_raises_via_wait_and_fetch(batch_client, fake_client):
    fake_batches = fake_client.messages.batches
    fake_batches.queue_retrieve(
        _FakeMessageBatch(
            batch_id="b",
            processing_status="ended",
            request_counts=_FakeRequestCounts(errored=4),
        )
    )
    with pytest.raises(BatchTerminalError, match="errored"):
        batch_client.wait_and_fetch("b")


def test_mixed_results_partial_errors_returns_per_request(batch_client, fake_client):
    """When the batch has both succeeded and errored results, status should be
    ``ended`` and ``fetch_results`` returns a BatchResult per custom_id with
    .error populated for the failed ones."""
    fake_batches = fake_client.messages.batches
    fake_batches.queue_retrieve(
        # wait_and_fetch poll
        _FakeMessageBatch(
            batch_id="b",
            processing_status="ended",
            request_counts=_FakeRequestCounts(succeeded=1, errored=1),
        ),
        # fetch_results internal poll
        _FakeMessageBatch(
            batch_id="b",
            processing_status="ended",
            request_counts=_FakeRequestCounts(succeeded=1, errored=1),
        ),
    )
    fake_batches.queue_results(
        iter(
            [
                _FakeIndividualResponse(
                    "ok",
                    _FakeSucceededResult(_FakeMessage("good", usage=_FakeUsage(1, 1))),
                ),
                _FakeIndividualResponse(
                    "fail",
                    _FakeErroredResult({"type": "invalid_request_error", "message": "x"}),
                ),
            ]
        )
    )
    results = batch_client.wait_and_fetch("b")
    assert results["ok"].content_text == "good"
    assert results["ok"].error is None
    assert results["fail"].content_text is None
    assert results["fail"].error is not None
    assert results["fail"].error["type"] == "errored"


# ---------------------------------------------------------------------------
# Polling timeout
# ---------------------------------------------------------------------------


def test_wait_and_fetch_honors_max_wait(fake_client, monkeypatch):
    """If polling never reaches a terminal state and max_wait_seconds elapses,
    BatchTimeoutError is raised. We force the deadline by mocking
    ``time.monotonic`` to jump past the deadline after the first poll."""
    from src.research_infra.batch_client import BatchTimeoutError
    import src.research_infra.batch_client as mod

    fake_batches = fake_client.messages.batches
    # Always in_progress
    for _ in range(50):
        fake_batches.queue_retrieve(
            _FakeMessageBatch(
                batch_id="b",
                processing_status="in_progress",
                request_counts=_FakeRequestCounts(processing=5),
            )
        )

    # Sequence: first call returns 0 (when wait_and_fetch establishes
    # deadline = 0 + max_wait = 5), second call returns 999999 (well past
    # the deadline) so the inner-loop check trips.
    times = iter([0.0, 999999.0])
    monkeypatch.setattr(mod.time, "monotonic", lambda: next(times))

    client = BatchClient(
        sdk_client=fake_client, polling_interval_seconds=1, max_wait_seconds=5
    )
    with pytest.raises(BatchTimeoutError):
        client.wait_and_fetch("b")


def test_progress_callback_invoked(batch_client, fake_client):
    fake_batches = fake_client.messages.batches
    fake_batches.queue_retrieve(
        _FakeMessageBatch(
            batch_id="b",
            processing_status="in_progress",
            request_counts=_FakeRequestCounts(processing=2),
        ),
        _FakeMessageBatch(
            batch_id="b",
            processing_status="ended",
            request_counts=_FakeRequestCounts(succeeded=2),
        ),
        # fetch_results internal poll
        _FakeMessageBatch(
            batch_id="b",
            processing_status="ended",
            request_counts=_FakeRequestCounts(succeeded=2),
        ),
    )
    fake_batches.queue_results(iter([]))

    seen: list[tuple] = []

    def cb(status, counts):
        seen.append((status, dict(counts)))

    batch_client.wait_and_fetch("b", progress_callback=cb)
    statuses = [s for s, _ in seen]
    assert statuses == ["in_progress", "ended"]


def test_progress_callback_exception_does_not_break_polling(batch_client, fake_client):
    fake_batches = fake_client.messages.batches
    fake_batches.queue_retrieve(
        _FakeMessageBatch(
            batch_id="b",
            processing_status="ended",
            request_counts=_FakeRequestCounts(succeeded=0),
        ),
        _FakeMessageBatch(
            batch_id="b",
            processing_status="ended",
            request_counts=_FakeRequestCounts(succeeded=0),
        ),
    )
    fake_batches.queue_results(iter([]))

    def boom(status, counts):
        raise RuntimeError("observer crashed")

    # Must complete, even though callback raises.
    results = batch_client.wait_and_fetch("b", progress_callback=boom)
    assert results == {}


# ---------------------------------------------------------------------------
# Constructor argument validation
# ---------------------------------------------------------------------------


def test_constructor_validates_polling_interval(fake_client):
    with pytest.raises(ValueError):
        BatchClient(sdk_client=fake_client, polling_interval_seconds=0)


def test_constructor_validates_max_wait(fake_client):
    with pytest.raises(ValueError):
        BatchClient(sdk_client=fake_client, max_wait_seconds=0)


# ---------------------------------------------------------------------------
# Result parsing edge cases
# ---------------------------------------------------------------------------


def test_succeeded_result_with_multiple_text_blocks_concatenates(
    batch_client, fake_client
):
    fake_batches = fake_client.messages.batches
    fake_batches.queue_retrieve(
        _FakeMessageBatch(
            batch_id="b",
            processing_status="ended",
            request_counts=_FakeRequestCounts(succeeded=1),
        )
    )

    # Build a message with two text content blocks.
    msg = MagicMock()
    block_a = MagicMock()
    block_a.type = "text"
    block_a.text = "part A "
    block_b = MagicMock()
    block_b.type = "text"
    block_b.text = "part B"
    msg.content = [block_a, block_b]
    msg.stop_reason = "end_turn"
    msg.usage = _FakeUsage(input_tokens=1, output_tokens=2)

    succeeded = MagicMock()
    succeeded.type = "succeeded"
    succeeded.message = msg

    fake_batches.queue_results(
        iter([_FakeIndividualResponse("multi", succeeded)])
    )

    results = batch_client.fetch_results("b")
    assert results["multi"].content_text == "part A part B"
