#!/usr/bin/env python3
"""Dig C harvest emitter — LIVE path default-off (Dig absorb xhigh 2026-09-21).

SHADOW JSONL always available. When GTOS_JEV_TRAIN_HARVEST_CALL=1 also runs
train_row_harvest helpers if importable. Never order_send / APPLY.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ENV = "GTOS_JEV_TRAIN_HARVEST_SHADOW"
CALL_ENV = "GTOS_JEV_TRAIN_HARVEST_CALL"
DEFAULT_JSONL = Path("/workspace/gtos/close_loop/war_room_20260920/shadow_dig_c_harvest.jsonl")


def harvest_shadow_enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get(ENV, "")).strip().lower() in {"1", "true", "yes", "on"}


def harvest_call_enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return harvest_shadow_enabled(environ) and str(env.get(CALL_ENV, "")).strip().lower() in {"1", "true", "yes", "on"}


def append_harvest_row(row: Mapping[str, Any] | None = None, *, path: Path | str | None = None, environ: Mapping[str, str] | None = None) -> Path | None:
    if not harvest_shadow_enabled(environ):
        return None
    out = Path(path) if path is not None else DEFAULT_JSONL
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "gtos.dig_c.harvest_emitter.live_default_off.v1",
        "stub_id": "SHADOW_DIG_C_HARVEST_EMITTER",
        "logged_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "place": False,
        "apply": False,
        "APPLY_proposed": False,
        "never_broker_send": True,
        "row": dict(row or {}),
    }
    if harvest_call_enabled(environ):
        try:
            from src.judgment.train_row_harvest import harvest_enabled  # type: ignore
            payload["train_row_harvest_import"] = True
            payload["train_row_harvest_enabled"] = bool(harvest_enabled())
        except Exception as exc:  # noqa: BLE001
            payload["train_row_harvest_import"] = False
            payload["train_row_harvest_error"] = type(exc).__name__
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, separators=(",", ":")) + "\n")
    return out
