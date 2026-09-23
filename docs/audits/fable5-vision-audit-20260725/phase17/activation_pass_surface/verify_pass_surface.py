#!/usr/bin/env python3
"""Verify Session CL's zero-mutation pass-surface ceremony package and captures."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
MANIFEST = HERE / "MANIFEST.json"
APPROVED = HERE / "APPROVED_SET.json"


class Refusal(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise Refusal(message)


def validate_approved(doc: dict[str, Any]) -> None:
    require(doc.get("decision") == "STOP_AFTER_PREFLIGHT_NO_MUTATION", "decision is not no-op")
    require(doc.get("arms_nothing") is True, "arms_nothing is not true")
    require(
        doc.get("approved_direct_additions") == {"FTMO": [], "redacted_account": []},
        "direct approval set is non-empty or malformed",
    )
    require(doc.get("incubation_ready_for_live_arming") == [], "an incubant is live-ready")
    require(doc.get("accounts_before") == doc.get("accounts_after"), "account args have a delta")
    edit = doc.get("supervisor_edit", {})
    for key in ("file_byte_delta", "hashtable_key_delta", "argument_delta"):
        require(edit.get(key) == [], f"authorized {key} is non-empty")
    require(edit.get("firing_ledger_action") == "NONE", "firing ledger action is not NONE")
    require(edit.get("restart_action") == "NONE", "restart action is not NONE")


def restricted_config_drift() -> list[str]:
    """Guarded config paths whose worktree bytes have moved since the ceremony sealed them.

    Split out of :func:`check_package` because it answers a different question. The other
    checks are properties of the PACKAGE -- it is empty, it copies nothing, its own files
    hash to their recorded values -- and those are true forever. This one is a PRECONDITION
    that held at execution time on 2026-08-01: "nothing has edited a restricted config in
    this worktree". Live arming decisions since (the F5 landing, OD-AI-*) legitimately edit
    `config/agent_config.yaml`, so as a standing assertion it can only go false, and it would
    take the ceremony's own package proof down with it.
    """

    manifest = load(MANIFEST)
    drifted = []
    for relative, expected in manifest["restricted_config_worktree_guard"].items():
        path = ROOT / relative
        require(path.is_file(), f"restricted config missing: {relative}")
        if sha256(path) != expected:
            drifted.append(relative)
    return drifted


def check_package(*, restricted_config_guard: bool = True) -> None:
    manifest = load(MANIFEST)
    require(manifest.get("decision") == "STOP_AFTER_PREFLIGHT_NO_MUTATION", "manifest is not no-op")
    require(manifest.get("payload_files") == [], "manifest contains runtime payloads")
    require(manifest.get("copy_order") == [], "manifest contains a copy order")
    for relative, expected in manifest["authority_inputs"].items():
        path = ROOT / relative
        require(path.is_file(), f"authority input missing: {relative}")
        require(sha256(path) == expected, f"authority input drift: {relative}")
    if restricted_config_guard:
        drifted = restricted_config_drift()
        require(not drifted,
                f"restricted config changed in worktree: {', '.join(drifted)}")
    for relative, expected in manifest["package_files"].items():
        path = ROOT / relative
        require(path.is_file(), f"package file missing: {relative}")
        require(sha256(path) == expected, f"package hash mismatch: {relative}")
    validate_approved(load(APPROVED))


def cli_value(command: str, flag: str) -> str | None:
    match = re.search(rf"(?:^|\s){re.escape(flag)}(?:\s+|=)(?:\"([^\"]*)\"|'([^']*)'|([^\s]+))", command)
    if not match:
        return None
    return next(value for value in match.groups() if value is not None)


def one_process(capture: dict[str, Any], namespace: str) -> dict[str, Any]:
    """One BOOK per namespace — which on the live host is a parent/child PAIR.

    Repaired at wave-17 integration (2026-08-01) against the first real host capture:
    each `run_book.py` worker runs as two python processes with byte-identical command
    lines created ~12 ms apart (FTMO 2380/1172, FN 4708/7080). CM's ceremony §5-6 has
    always required proving "four fresh book Python processes (two parent/child pairs)";
    this check's original `len(rows) == 1` modelled the pair as drift. The repaired
    contract keeps the protective intent: 1-2 rows, ALL command lines identical, and
    creation times within 60 s — a stale survivor from an earlier restart (CE's 01:23
    hazard) differs in either and still refuses.
    """
    rows = capture.get("books", {}).get(namespace, [])
    require(isinstance(rows, list) and len(rows) in (1, 2),
            f"{namespace}: expected one book process (or its parent/child pair)")
    for row in rows:
        require(row.get("command_line"), f"{namespace}: command line absent")
        require(row.get("creation_date"), f"{namespace}: creation time absent")
    commands = {row["command_line"] for row in rows}
    require(len(commands) == 1,
            f"{namespace}: {len(rows)} processes with differing command lines — stale survivor")
    if len(rows) == 2:
        times = sorted(datetime.fromisoformat(row["creation_date"]) for row in rows)
        require((times[1] - times[0]).total_seconds() <= 60.0,
                f"{namespace}: pair creation times differ by more than 60s — stale survivor")
    return sorted(rows, key=lambda row: row["creation_date"])[0]


def assert_log(capture: dict[str, Any], namespace: str, needle: str) -> None:
    lines = capture.get("log_proofs", {}).get(namespace, [])
    require(any(needle in line for line in lines), f"{namespace}: proving line absent: {needle}")


def validate_host(capture: dict[str, Any], approved: dict[str, Any] | None = None) -> None:
    approved = approved or load(APPROVED)
    validate_approved(approved)
    require(capture.get("schema") == "gtos.phase17.cl.host_pass_surface_capture.v1", "wrong host capture schema")
    baseline = approved["host_baseline_receipt"]
    require(capture.get("git_branch") == baseline["branch"], "host branch drift")
    require(str(capture.get("git_head", "")).startswith(baseline["head_prefix"]), "host HEAD drift")
    supervisor = capture.get("files", {}).get("supervisor", {})
    require(supervisor.get("present") is True, "host supervisor absent")
    require(str(supervisor.get("sha256", "")).startswith(baseline["supervisor_sha256_prefix"]), "host supervisor bytes drift")
    require(capture.get("supervisor_books_block"), "host $books block absent")
    require(capture.get("supervisor_books_block_sha256"), "host $books block hash absent")
    require(capture.get("supervisor_book_hashtable_keys"), "host hashtable keys absent")

    by_ns = {a["namespace"]: (name, a) for name, a in approved["accounts_before"].items()}
    proposal_ids = approved["proposal_ids_not_ready"]
    for namespace, (account_name, account) in by_ns.items():
        row = one_process(capture, namespace)
        command = row["command_line"]
        tags = cli_value(command, "--tags")
        expected_tags = ",".join(account["tags"])
        require(tags is not None and tags != "", f"{account_name}: --tags absent/empty (fail-open all)")
        require(tags == expected_tags, f"{account_name}: --tags is not the exact approved set (typo/extra/missing)")
        frontier = cli_value(command, "--frontier-exits")
        expected_frontier = ",".join(account["frontier_exits"]) or None
        require(frontier == expected_frontier, f"{account_name}: frontier selection drift")
        floor = cli_value(command, "--spread-geometry-floor")
        require(floor == ",".join(account["spread_geometry_floor"]), f"{account_name}: spread-floor selection drift")
        for proposal_id in proposal_ids:
            sleeve = proposal_id.split("@", 1)[0]
            require(sleeve not in command, f"{account_name}: unapproved incubant appears live: {sleeve}")
        tfs = account["decision_timeframes_derived"]
        assert_log(capture, namespace, f"BookLauncher starting: tfs={tfs}")
        for sleeve in account["spread_geometry_floor"]:
            assert_log(capture, namespace, f"SPREAD-GEOMETRY FLOOR IS ON for {sleeve} ")
        if expected_frontier:
            assert_log(capture, namespace, f"FRONTIER EXIT CONTRACT IS ON for {expected_frontier}: target_5R")


def stable_projection(capture: dict[str, Any]) -> dict[str, Any]:
    """Fields that the no-op ceremony requires to be bit/identity stable."""
    return {
        "files": capture.get("files"),
        "supervisor_books_block": capture.get("supervisor_books_block"),
        "supervisor_books_block_sha256": capture.get("supervisor_books_block_sha256"),
        "supervisor_book_hashtable_keys": capture.get("supervisor_book_hashtable_keys"),
        "books": capture.get("books"),
        "firing_ledgers": capture.get("firing_ledgers"),
    }


def validate_postflight(before: dict[str, Any], after: dict[str, Any]) -> None:
    validate_host(before)
    validate_host(after)
    require(stable_projection(before) == stable_projection(after), "pre/post host state changed during no-op ceremony")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", choices=("package", "preflight", "postflight", "all"), default="all")
    parser.add_argument("--host-preflight", type=Path)
    parser.add_argument("--host-postflight", type=Path)
    args = parser.parse_args()
    try:
        if args.check in {"package", "all"}:
            check_package()
            print("ok: package hashes, authorities, protected worktree configs, empty approval")
        if args.check in {"preflight", "all"}:
            require(args.host_preflight is not None, "--host-preflight is required")
            validate_host(load(args.host_preflight))
            print("ok: host matches approved no-op baseline")
        if args.check == "postflight":
            require(args.host_preflight is not None, "--host-preflight is required")
            require(args.host_postflight is not None, "--host-postflight is required")
            validate_postflight(load(args.host_preflight), load(args.host_postflight))
            print("ok: pre/post state is identical")
    except Refusal as exc:
        print(f"RESULT: REFUSED — {exc}")
        return 2
    if args.check in {"preflight", "all"}:
        print("RESULT: PASS — HOST MATCHES APPROVED NO-OP BASELINE")
    elif args.check == "postflight":
        print("RESULT: PASS — ZERO MUTATION PROVED")
    else:
        print("RESULT: PASS — PACKAGE IS SEALED NO-OP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
