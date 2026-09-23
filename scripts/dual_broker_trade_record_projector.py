#!/usr/bin/env python3
"""Project primary trade records into the canonical dual-broker intent bus.

This bridge lets an already-running primary fleet feed secondary execution
without forcing a broad primary orchestrator reload. It is a bridge, not the
long-term preferred source; native orchestrator emission remains the primary
contract once workers naturally reload.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.dual_broker_intent_bus import (  # noqa: E402
    append_intent,
    build_intent_from_trade_record,
    resolve_intent_log_path,
    trade_record_projection_skip_reasons,
)
from src.components.mt5_daemon_runtime import (  # noqa: E402
    acquire_single_instance_lock,
    install_signal_handlers,
    release_single_instance_lock,
    write_daemon_heartbeat,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_SOURCE_ROOT = PROJECT_ROOT / "knowledge_base" / "redacted_account_live_bee34003" / "trade_records"
DEFAULT_SOURCE_PROFILE = "redacted_account"
DEFAULT_SOURCE_NAMESPACE = "redacted_account_live_bee34003"
DEFAULT_STATE_PATH = PROJECT_ROOT / "pipeline_state" / "dual_broker" / "trade_record_projector_state.json"
DEFAULT_ACTION_LOG = PROJECT_ROOT / "pipeline_state" / "dual_broker" / "trade_record_projector_actions.jsonl"
DEFAULT_MAX_FILLED_RECORD_PROJECTION_AGE_SECONDS = 120.0

_STOP = False


def _request_stop() -> None:
    global _STOP
    _STOP = True


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_utc_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    return str(value)


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(row)
    payload.setdefault("recorded_at_utc", _utcnow_iso())
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(_jsonable(payload), ensure_ascii=True, sort_keys=True) + "\n")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    data = json.dumps(_jsonable(payload), indent=2, sort_keys=True)
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            tmp.write_text(data, encoding="utf-8")
            os.replace(str(tmp), str(path))
            return
        except PermissionError as exc:
            if attempt >= max_attempts:
                LOGGER.error(
                    "json persistence skipped after transient file-lock retries: "
                    "path=%s tmp=%s error=%s",
                    path,
                    tmp,
                    exc,
                )
                return
            LOGGER.warning(
                "json persistence retry after file-lock: path=%s tmp=%s "
                "attempt=%s/%s error=%s",
                path,
                tmp,
                attempt,
                max_attempts,
                exc,
            )
            time.sleep(0.05 * attempt)
        except OSError as exc:
            LOGGER.error(
                "json persistence skipped after filesystem error: path=%s tmp=%s "
                "error=%s",
                path,
                tmp,
                exc,
            )
            return


def _file_signature(path: Path) -> dict[str, Any]:
    stat = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
        "sha256": digest.hexdigest(),
    }


def _legacy_signature_without_hash_matches(
    prior: Any,
    current: dict[str, Any],
) -> bool:
    if not isinstance(prior, dict):
        return False
    if prior.get("sha256"):
        return False
    return (
        prior.get("mtime_ns") == current.get("mtime_ns")
        and prior.get("size") == current.get("size")
    )


def _iter_recent_records(root: Path, limit: int) -> list[Path]:
    if not root.exists():
        return []
    paths = [
        path
        for path in root.rglob("*.json")
        if path.is_file() and not path.name.startswith("_")
    ]
    paths.sort(key=lambda item: item.stat().st_mtime_ns, reverse=True)
    return paths[: max(1, int(limit))]


def _load_record(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.warning("trade record projection skipped malformed file %s: %s", path, exc)
        return None
    return data if isinstance(data, dict) else None


def _record_execution_fill_time(record: dict[str, Any]) -> datetime | None:
    execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
    for field in (
        "fill_time_utc",
        "entry_time",
        "order_result_time_utc",
        "entry_slippage_source_ts",
    ):
        parsed = _parse_utc_datetime(execution.get(field))
        if parsed is not None:
            return parsed
    return None


def _record_has_filled_execution(record: dict[str, Any]) -> bool:
    execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
    fill_state = str(
        execution.get("broker_fill_state") or execution.get("fill_state") or ""
    ).strip().lower()
    if fill_state not in {"filled", "order_filled", "done"}:
        return False
    return any(
        execution.get(field) not in (None, "", 0, "0")
        for field in (
            "fill_time_utc",
            "entry_deal_ticket",
            "entry_order_ticket",
            "position_ticket",
            "ticket",
        )
    )


def _projection_freshness_skip_reason(
    record: dict[str, Any],
    *,
    prior_signature: dict[str, Any] | None,
    projection_not_before_utc: datetime | None,
    replay_existing: bool,
    max_filled_record_age_seconds: float | None,
    now_utc: datetime | None = None,
) -> str | None:
    if replay_existing or projection_not_before_utc is None:
        return None
    if not _record_has_filled_execution(record):
        return None
    fill_time = _record_execution_fill_time(record)
    if fill_time is None and prior_signature is not None:
        return "filled_record_changed_without_entry_event_time_after_projection_activation"
    if fill_time is not None and fill_time < projection_not_before_utc:
        return "filled_record_event_time_before_projection_activation"
    if fill_time is not None and max_filled_record_age_seconds:
        now = now_utc or datetime.now(timezone.utc)
        age_seconds = (now - fill_time).total_seconds()
        if age_seconds > float(max_filled_record_age_seconds):
            return "filled_record_event_time_too_old_for_live_projection"
    return None


def project_once(
    *,
    source_root: Path,
    intent_log: Path,
    state_path: Path,
    action_log: Path,
    source_profile: str,
    source_runtime_namespace: str,
    recent_file_limit: int,
    replay_existing: bool,
    max_filled_record_age_seconds: float | None = DEFAULT_MAX_FILLED_RECORD_PROJECTION_AGE_SECONDS,
) -> dict[str, Any]:
    state = _read_json(state_path)
    seen = state.get("seen") if isinstance(state.get("seen"), dict) else {}
    projection_outcomes = (
        state.get("projection_outcomes")
        if isinstance(state.get("projection_outcomes"), dict)
        else {}
    )
    projection_not_before_text = state.get("projection_not_before_utc")
    if not projection_not_before_text and state:
        projection_not_before_text = _utcnow_iso()
        state["projection_not_before_utc"] = projection_not_before_text
    projection_not_before_utc = _parse_utc_datetime(projection_not_before_text)
    if not state and not replay_existing:
        projection_not_before_text = _utcnow_iso()
        current_seen = {}
        current_outcomes = {}
        for path in _iter_recent_records(source_root, recent_file_limit):
            path_key = str(path)
            signature = _file_signature(path)
            current_seen[path_key] = signature
            current_outcomes[path_key] = {
                "signature": signature,
                "status": "start_at_end_baseline",
                "reason": "initialized_at_end_without_replay",
                "updated_at_utc": projection_not_before_text,
            }
        _write_json(
            state_path,
            {
                "updated_at_utc": _utcnow_iso(),
                "source_root": str(source_root),
                "intent_log": str(intent_log),
                "source_runtime_namespace": source_runtime_namespace,
                "projection_not_before_utc": projection_not_before_text,
                "seen": current_seen,
                "projection_outcomes": current_outcomes,
                "start_at_end": True,
            },
        )
        return {
            "status": "initialized_at_end",
            "records_seen": len(current_seen),
            "projected": 0,
            "duplicates": 0,
        }

    projected = 0
    duplicates = 0
    skipped = 0
    freshness_skipped = 0
    errors = 0
    for path in reversed(_iter_recent_records(source_root, recent_file_limit)):
        path_key = str(path)
        signature = _file_signature(path)
        prior = seen.get(path_key)
        prior_outcome = projection_outcomes.get(path_key)
        legacy_signature_match = _legacy_signature_without_hash_matches(
            prior,
            signature,
        )
        has_current_outcome = (
            isinstance(prior_outcome, dict)
            and prior_outcome.get("signature") == signature
            and bool(prior_outcome.get("status"))
        )
        state_repair_reason = None
        if prior == signature and has_current_outcome:
            continue
        if prior == signature and not has_current_outcome:
            state_repair_reason = "seen_signature_without_projection_outcome"
        elif legacy_signature_match:
            if isinstance(prior_outcome, dict) and prior_outcome.get("status"):
                state_repair_reason = "legacy_signature_without_content_hash"
            else:
                state_repair_reason = "seen_signature_without_projection_outcome"
        record = _load_record(path)
        if record is None:
            errors += 1
            seen[path_key] = signature
            projection_outcomes[path_key] = {
                "signature": signature,
                "status": "error",
                "reason": "record_load_failed",
                "state_repair_reason": state_repair_reason,
                "updated_at_utc": _utcnow_iso(),
            }
            continue
        freshness_skip_reason = _projection_freshness_skip_reason(
            record,
            prior_signature=prior,
            projection_not_before_utc=projection_not_before_utc,
            replay_existing=bool(replay_existing),
            max_filled_record_age_seconds=max_filled_record_age_seconds,
        )
        if freshness_skip_reason:
            skipped += 1
            freshness_skipped += 1
            _append_jsonl(
                action_log,
                {
                    "event": "trade_record_projection_skipped",
                    "record_path": str(path),
                    "reason": freshness_skip_reason,
                    "source_runtime_namespace": source_runtime_namespace,
                    "state_repair_reason": state_repair_reason,
                    "projection_not_before_utc": (
                        projection_not_before_utc.isoformat()
                        if projection_not_before_utc is not None
                        else None
                    ),
                    "fill_time_utc": (
                        _record_execution_fill_time(record).isoformat()
                        if _record_execution_fill_time(record) is not None
                        else None
                    ),
                },
            )
            seen[path_key] = signature
            projection_outcomes[path_key] = {
                "signature": signature,
                "status": "skipped",
                "reason": freshness_skip_reason,
                "state_repair_reason": state_repair_reason,
                "updated_at_utc": _utcnow_iso(),
            }
            continue
        intent = build_intent_from_trade_record(
            record,
            record_path=path,
            source_profile=source_profile,
            source_runtime_namespace=source_runtime_namespace,
        )
        if intent is None:
            skipped += 1
            _append_jsonl(
                action_log,
                {
                    "event": "trade_record_projection_skipped",
                    "record_path": str(path),
                    "reason": "intent_builder_returned_none",
                    "projection_skip_reasons": trade_record_projection_skip_reasons(record),
                    "source_runtime_namespace": source_runtime_namespace,
                    "state_repair_reason": state_repair_reason,
                },
            )
            seen[path_key] = signature
            projection_outcomes[path_key] = {
                "signature": signature,
                "status": "skipped",
                "reason": "intent_builder_returned_none",
                "state_repair_reason": state_repair_reason,
                "updated_at_utc": _utcnow_iso(),
            }
            continue
        result = append_intent(intent, intent_log, dedupe=True)
        if result.get("status") == "appended":
            projected += 1
        elif result.get("status") == "duplicate":
            duplicates += 1
        _append_jsonl(
            action_log,
            {
                "event": "trade_record_projected",
                "record_path": str(path),
                "intent_id": result.get("intent_id"),
                "append_status": result.get("status"),
                "intent_type": intent.get("intent_type"),
                "source_runtime_namespace": source_runtime_namespace,
                "state_repair_reason": state_repair_reason,
            },
        )
        seen[path_key] = signature
        projection_outcomes[path_key] = {
            "signature": signature,
            "status": result.get("status") or "unknown",
            "intent_id": result.get("intent_id"),
            "intent_type": intent.get("intent_type"),
            "state_repair_reason": state_repair_reason,
            "updated_at_utc": _utcnow_iso(),
        }

    current_record_keys = {
        str(path)
        for path in _iter_recent_records(source_root, recent_file_limit)
    }
    seen = {
        key: value
        for key, value in seen.items()
        if key in current_record_keys
    }
    projection_outcomes = {
        key: value
        for key, value in projection_outcomes.items()
        if key in current_record_keys
    }

    _write_json(
        state_path,
        {
            "updated_at_utc": _utcnow_iso(),
            "source_root": str(source_root),
            "intent_log": str(intent_log),
            "source_runtime_namespace": source_runtime_namespace,
            "projection_not_before_utc": projection_not_before_text,
            "seen": seen,
            "projection_outcomes": projection_outcomes,
        },
    )
    return {
        "status": "projected",
        "projected": projected,
        "duplicates": duplicates,
        "skipped": skipped,
        "freshness_skipped": freshness_skipped,
        "errors": errors,
        "tracked_files": len(seen),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--intent-log", type=Path, default=None)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--action-log", type=Path, default=DEFAULT_ACTION_LOG)
    parser.add_argument("--source-profile", default=DEFAULT_SOURCE_PROFILE)
    parser.add_argument("--source-runtime-namespace", default=DEFAULT_SOURCE_NAMESPACE)
    parser.add_argument("--recent-file-limit", type=int, default=250)
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    parser.add_argument("--replay-existing", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument(
        "--max-filled-record-age-seconds",
        type=float,
        default=DEFAULT_MAX_FILLED_RECORD_PROJECTION_AGE_SECONDS,
    )
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    intent_log = args.intent_log or resolve_intent_log_path({})
    lock_name = f"dual_broker_trade_record_projector_{args.source_runtime_namespace}"
    acquired, conflict = acquire_single_instance_lock(
        lock_name,
        argv_marker="dual_broker_trade_record_projector.py",
    )
    if not acquired:
        LOGGER.error("another trade-record projector is alive at PID %s", conflict)
        return 2
    try:
        last_progress = datetime.now(timezone.utc)
        while not _STOP:
            summary = project_once(
                source_root=args.source_root,
                intent_log=Path(intent_log),
                state_path=args.state,
                action_log=args.action_log,
                source_profile=args.source_profile,
                source_runtime_namespace=args.source_runtime_namespace,
                recent_file_limit=args.recent_file_limit,
                replay_existing=bool(args.replay_existing),
                max_filled_record_age_seconds=args.max_filled_record_age_seconds,
            )
            if summary.get("projected"):
                last_progress = datetime.now(timezone.utc)
            _append_jsonl(
                args.action_log,
                {
                    "event": "projector_cycle",
                    "summary": summary,
                    "intent_log": str(intent_log),
                    "source_root": str(args.source_root),
                    "source_runtime_namespace": args.source_runtime_namespace,
                },
            )
            write_daemon_heartbeat(
                lock_name,
                last_progress_at=last_progress,
                extra={
                    "intent_log": str(intent_log),
                    "source_root": str(args.source_root),
                    "state": str(args.state),
                    "action_log": str(args.action_log),
                    "source_runtime_namespace": args.source_runtime_namespace,
                },
            )
            if args.once:
                break
            time.sleep(max(0.25, float(args.poll_seconds)))
        return 0
    finally:
        release_single_instance_lock(lock_name)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    install_signal_handlers(_request_stop)
    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
