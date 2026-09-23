#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_vps_active_supervision_repair_artifacts import (
    REPO_ROOT,
    ROUTE,
    collect_broker_snapshot,
    collect_process_snapshot,
    iso,
    stamp,
    utc_now,
    write_json,
)


NAMESPACES = ("operator_profile", "redacted_account_live_bee34003")


def run_powershell(script: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    command = (
        "$ErrorActionPreference='Stop'; "
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
        f"{script}"
    )
    return subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def list_book_workers() -> list[dict[str, Any]]:
    script = (
        "Get-CimInstance Win32_Process | Where-Object { "
        "$_.Name -eq 'python.exe' -and $_.CommandLine -like '*run_book.py*' "
        "} | Select-Object ProcessId,ParentProcessId,CreationDate,CommandLine | "
        "ConvertTo-Json -Depth 6"
    )
    proc = run_powershell(script)
    if proc.returncode != 0:
        return [{"error": proc.stderr.strip(), "returncode": proc.returncode}]
    text = proc.stdout.strip()
    if not text:
        return []
    parsed = json.loads(text)
    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        return [row for row in parsed if isinstance(row, dict)]
    return [{"error": "unexpected_powershell_json", "raw": text[:500]}]


def config_hash() -> str:
    data = (REPO_ROOT / "config" / "agent_config.yaml").read_bytes()
    return hashlib.sha256(data).hexdigest()


def heartbeat_state(now: datetime) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for namespace in NAMESPACES:
        path = REPO_ROOT / "pipeline_state" / "ultimate_book" / namespace / "heartbeat.json"
        row: dict[str, Any] = {"path": str(path.relative_to(REPO_ROOT)), "exists": path.exists()}
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                row["error"] = repr(exc)
            else:
                ts = payload.get("ts")
                row["payload"] = payload
                try:
                    parsed = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(timezone.utc)
                    row["timestamp_utc"] = iso(parsed)
                    row["age_seconds"] = round((now - parsed).total_seconds(), 3)
                except Exception:  # noqa: BLE001
                    row["timestamp_utc"] = None
                    row["age_seconds"] = None
                row["last_write_time_utc"] = iso(datetime.fromtimestamp(path.stat().st_mtime, timezone.utc))
        rows[namespace] = row
    return rows


def namespace_worker_counts(processes: list[dict[str, Any]]) -> dict[str, int]:
    counts = {namespace: 0 for namespace in NAMESPACES}
    for process in processes:
        cmd = str(process.get("CommandLine") or process.get("command_line") or "")
        for namespace in NAMESPACES:
            if namespace in cmd:
                counts[namespace] += 1
    return counts


def stop_book_workers(processes: list[dict[str, Any]]) -> dict[str, Any]:
    ids = sorted(
        {
            int(process["ProcessId"])
            for process in processes
            if str(process.get("ProcessId") or "").isdigit()
        }
    )
    if not ids:
        return {"requested_pids": [], "returncode": 0, "stdout": "", "stderr": ""}
    joined = ",".join(str(pid) for pid in ids)
    proc = run_powershell(
        f"$ids=@({joined}); foreach ($id in $ids) {{ Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }}",
        timeout=30,
    )
    return {
        "requested_pids": ids,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def wait_for_recovery(started_at: datetime, timeout_seconds: int, poll_seconds: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    observations: list[dict[str, Any]] = []
    while True:
        now = utc_now()
        processes = list_book_workers()
        counts = namespace_worker_counts(processes)
        heartbeats = heartbeat_state(now)
        healthy_heartbeats = {
            namespace: (
                bool(row.get("exists"))
                and row.get("age_seconds") is not None
                and row.get("age_seconds") <= 120
                and str(row.get("timestamp_utc") or "") >= iso(started_at)
            )
            for namespace, row in heartbeats.items()
        }
        observation = {
            "observed_at_utc": iso(now),
            "worker_counts": counts,
            "heartbeats": heartbeats,
            "healthy_heartbeats": healthy_heartbeats,
        }
        observations.append(observation)
        if all(counts.get(namespace, 0) >= 2 for namespace in NAMESPACES) and all(healthy_heartbeats.values()):
            return {
                "recovered": True,
                "recovered_at_utc": iso(now),
                "observations": observations,
                "final_processes": processes,
            }
        if time.monotonic() >= deadline:
            return {
                "recovered": False,
                "timed_out_at_utc": iso(now),
                "observations": observations,
                "final_processes": processes,
            }
        time.sleep(poll_seconds)


def broker_position_key(snapshot: dict[str, Any]) -> dict[str, list[str]]:
    profiles = snapshot.get("profiles") or {}
    result: dict[str, list[str]] = {}
    for namespace, profile in profiles.items():
        positions = profile.get("positions") or []
        result[namespace] = sorted(str(position.get("ticket")) for position in positions)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-seconds", type=int, default=240)
    parser.add_argument("--poll-seconds", type=int, default=10)
    args = parser.parse_args(argv)

    started_at = utc_now()
    before_hash = config_hash()
    before_process = collect_process_snapshot(started_at)
    before_workers = list_book_workers()
    before_broker = collect_broker_snapshot(started_at)
    stop_result = stop_book_workers(before_workers)
    recovery = wait_for_recovery(started_at, args.timeout_seconds, args.poll_seconds)
    ended_at = utc_now()
    after_hash = config_hash()
    after_process = collect_process_snapshot(ended_at)
    after_broker = collect_broker_snapshot(ended_at)

    broker_positions_before = broker_position_key(before_broker)
    broker_positions_after = broker_position_key(after_broker)
    proof = {
        "schema": "gtos.vps_active_supervision_repair.reload_proof.v1",
        "started_at_utc": iso(started_at),
        "ended_at_utc": iso(ended_at),
        "runtime_effect_boundary": "controlled_book_worker_reload_no_broker_mutation",
        "broker_mutation_status": "none",
        "process_mutation_scope": "stopped_only_python_run_book_workers_supervisor_respawned",
        "config_hash_before": before_hash,
        "config_hash_after": after_hash,
        "before_workers": before_workers,
        "stop_result": stop_result,
        "recovery": recovery,
        "before_process_snapshot": before_process,
        "after_process_snapshot": after_process,
        "before_broker_snapshot": before_broker,
        "after_broker_snapshot": after_broker,
        "broker_position_tickets_before": broker_positions_before,
        "broker_position_tickets_after": broker_positions_after,
        "ok": (
            stop_result.get("returncode") == 0
            and recovery.get("recovered") is True
            and before_hash == after_hash
            and before_broker.get("ok") is True
            and after_broker.get("ok") is True
            and broker_positions_before == broker_positions_after
        ),
    }
    path = ROUTE / f"VPS_ACTIVE_SUPERVISION_REPAIR_RELOAD_PROOF_{stamp(started_at)}.json"
    write_json(path, proof)
    print(json.dumps({"ok": proof["ok"], "path": path.name}, indent=2, sort_keys=True))
    return 0 if proof["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
