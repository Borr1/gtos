from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import pytest

import src.components.live_decision_packet_v4 as packet_module


def test_json_sha256_preserves_existing_canonical_bytes_without_safe_copy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "schema": "test",
        "nested": {
            "tuple": ("a", 2, None),
            "timestamp": datetime(2026, 1, 2, 3, 4, tzinfo=timezone.utc),
        },
        "rows": [{"value": 1.25, "active": True}],
    }
    expected_bytes = json.dumps(
        packet_module._json_safe(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    expected_digest = hashlib.sha256(expected_bytes).hexdigest()

    def recursive_safe_copy_forbidden(_value: object) -> object:
        raise AssertionError("recursive json-safe copy entered hash hot path")

    monkeypatch.setattr(
        packet_module,
        "_json_safe",
        recursive_safe_copy_forbidden,
    )

    assert packet_module._json_sha256(payload) == expected_digest


def test_deferred_packet_hash_material_rebuilds_exact_eager_packet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        packet_module,
        "utc_now_iso",
        lambda: "2026-01-02T03:04:05+00:00",
    )
    kwargs = {
        "record": {},
        "legacy_packet": {
            "candidate_identity": {
                "candidate_id": "candidate-1",
                "symbol": "XAUUSD",
            }
        },
        "candidate": {},
        "raw_data": {},
        "runtime_config": {},
    }

    eager = packet_module.build_live_decision_packet_v4(**kwargs)
    deferred = packet_module.build_live_decision_packet_v4(
        **kwargs,
        defer_packet_hash=True,
    )
    preimage = deferred.pop(
        packet_module.DEFERRED_PACKET_HASH_PREIMAGE_KEY
    )
    assert isinstance(preimage, bytes)
    deferred["packet_hash_sha256"] = hashlib.sha256(preimage).hexdigest()

    assert deferred == eager
