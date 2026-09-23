from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "ai_decision_trace_trade_record_backfill_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def iter_trade_record_paths(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*.json")
        if path.is_file() and path.name != "_pending_records_index.json"
    )


def _record_id(record: dict[str, Any], path: Path) -> str:
    return str(
        record.get("trade_id")
        or (record.get("metadata") or {}).get("trade_id")
        or path.stem
    )


def _symbol(record: dict[str, Any], path: Path) -> str:
    return str(
        record.get("symbol")
        or (record.get("metadata") or {}).get("symbol")
        or path.parent.name
    )


def _decision_time(record: dict[str, Any]) -> str | None:
    metadata = record.get("metadata") or {}
    context = record.get("context_at_decision") or {}
    return (
        metadata.get("candle_close_utc")
        or metadata.get("decision_time_utc")
        or context.get("timestamp_utc")
        or context.get("current_time")
    )


def build_trade_record_ai_trace_backfill_row(
    path: Path,
    record: dict[str, Any],
    *,
    source_root: Path | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    prompt = record.get("prompt") or {}
    ai_response = record.get("ai_response")
    decision_pipeline = record.get("decision_pipeline") or {}
    system_prompt = str(prompt.get("system_prompt") or "")
    user_message = str(prompt.get("user_message") or "")
    response_text = stable_json(ai_response) if ai_response is not None else ""
    prompt_bundle = stable_json(
        {
            "system_prompt_sha256": sha256_text(system_prompt),
            "user_message_sha256": sha256_text(user_message),
        }
    )
    source_path = path
    source_sha = sha256_path(path) if path.exists() else None
    trace_payload = {
        "source_path": str(source_path if source_root is None else source_path.relative_to(source_root)).replace("\\", "/"),
        "source_sha256": source_sha,
        "trade_id": _record_id(record, path),
        "symbol": _symbol(record, path),
        "decision_time_utc": _decision_time(record),
        "ai_decision": decision_pipeline.get("ai_decision"),
        "final_outcome": decision_pipeline.get("final_outcome"),
        "prompt_bundle_sha256": sha256_text(prompt_bundle),
        "ai_response_sha256": sha256_text(response_text) if response_text else None,
    }
    row_key = sha256_text(stable_json(trace_payload))
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": row_key,
        "generated_at_utc": generated_at_utc or datetime.now(timezone.utc).isoformat(),
        "source_path": trace_payload["source_path"],
        "source_sha256": source_sha,
        "trade_id": trace_payload["trade_id"],
        "symbol": trace_payload["symbol"],
        "decision_time_utc": trace_payload["decision_time_utc"],
        "ai_decision": trace_payload["ai_decision"],
        "ai_grade": decision_pipeline.get("ai_grade"),
        "ai_confidence": decision_pipeline.get("ai_confidence"),
        "ai_direction": decision_pipeline.get("ai_direction"),
        "ai_framework": decision_pipeline.get("ai_framework"),
        "final_outcome": trace_payload["final_outcome"],
        "model_used": (ai_response or {}).get("model_used") if isinstance(ai_response, dict) else None,
        "prompt_fingerprint": {
            "system_prompt_sha256": sha256_text(system_prompt) if system_prompt else None,
            "user_message_sha256": sha256_text(user_message) if user_message else None,
            "prompt_bundle_sha256": trace_payload["prompt_bundle_sha256"],
            "system_prompt_length": len(system_prompt),
            "user_message_length": len(user_message),
        },
        "ai_response_sha256": trace_payload["ai_response_sha256"],
        "ai_response_length": len(response_text),
        "capture_status": (
            "TRADE_RECORD_AI_TRACE_HASH_BACKFILL_COMPLETE"
            if system_prompt and user_message and response_text
            else "TRADE_RECORD_AI_TRACE_HASH_BACKFILL_INCOMPLETE_SOURCE"
        ),
        "stores_full_prompt_or_response_text": False,
        "promotion_verdict": PROMOTION_VERDICT,
        "research_boundary": {
            "source_trade_record_backfill_only": True,
            "runtime_trace_stream_write": False,
            "runtime_trading_or_live_broker_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
            "stores_full_prompt_or_response_text": False,
        },
    }


def build_trade_record_ai_trace_backfill_rows(
    paths: Iterable[Path],
    *,
    source_root: Path | None = None,
    generated_at_utc: str | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(record, dict):
            rows.append(
                build_trade_record_ai_trace_backfill_row(
                    path,
                    record,
                    source_root=source_root,
                    generated_at_utc=generated_at_utc,
                )
            )
    return rows


def summarize_trade_record_ai_trace_backfill(rows: list[dict[str, Any]]) -> dict[str, Any]:
    complete_rows = [row for row in rows if row.get("capture_status") == "TRADE_RECORD_AI_TRACE_HASH_BACKFILL_COMPLETE"]
    return {
        "schema_version": SCHEMA_VERSION,
        "rows": len(rows),
        "complete_rows": len(complete_rows),
        "incomplete_rows": len(rows) - len(complete_rows),
        "unique_prompt_bundle_hashes": len({row.get("prompt_fingerprint", {}).get("prompt_bundle_sha256") for row in complete_rows}),
        "unique_ai_response_hashes": len({row.get("ai_response_sha256") for row in complete_rows if row.get("ai_response_sha256")}),
        "symbol_counts": dict(sorted(_counts(row.get("symbol") for row in rows).items())),
        "ai_decision_counts": dict(sorted(_counts(row.get("ai_decision") for row in rows).items())),
        "final_outcome_counts": dict(sorted(_counts(row.get("final_outcome") for row in rows).items())),
        "stores_full_prompt_or_response_text_rows": sum(bool(row.get("stores_full_prompt_or_response_text")) for row in rows),
        "runtime_trace_stream_write_rows": sum(bool((row.get("research_boundary") or {}).get("runtime_trace_stream_write")) for row in rows),
        "paid_api_or_vendor_call_rows": sum(bool((row.get("research_boundary") or {}).get("paid_api_or_vendor_call")) for row in rows),
        "broker_operation_rows": sum(bool((row.get("research_boundary") or {}).get("broker_operation")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(
            bool((row.get("research_boundary") or {}).get("runtime_candidate_use_permitted")) for row in rows
        ),
    }


def _counts(values: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value if value is not None else "UNKNOWN")
        counts[key] = counts.get(key, 0) + 1
    return counts
