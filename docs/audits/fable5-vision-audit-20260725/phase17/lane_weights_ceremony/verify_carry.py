#!/usr/bin/env python3
"""Offline/host verifier for Session CO's signed lane-weight carry.

This verifier never imports or executes ``run_book.py`` and has no MT5/broker
imports.  ``preflight`` and ``postflight`` inspect bytes only.  ``behaviour``
loads the two pure payload modules under isolated names and exercises signature,
neutral failure, daily latching, and packet provenance.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
MANIFEST = json.loads((HERE / "MANIFEST.json").read_text(encoding="utf-8"))
RESULTS: list[dict] = []


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition: bool, message: str, errors: list[str]) -> None:
    RESULTS.append({"ok": bool(condition), "check": message.strip()})
    print(("ok  " if condition else "FAIL") + message)
    if not condition:
        errors.append(message)


def _payload_path(row: dict) -> Path:
    return REPO / row["source_in_this_repo"]


def _destination(root: Path, row: dict) -> Path:
    return root / row["repo_path"]


def package_check(key_path: Path | None, errors: list[str]) -> None:
    for row in MANIFEST["files"]:
        path = _payload_path(row)
        check(path.is_file(), f" payload exists: {row['repo_path']}", errors)
        if not path.is_file():
            continue
        check(sha(path) == row["sha256_after_carry"], f" payload hash: {row['repo_path']}", errors)
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            parsed = True
        except Exception:
            parsed = False
        check(parsed, f" payload parses: {row['repo_path']}", errors)
        check(b"\r\n" not in path.read_bytes(), f" payload LF-only: {row['repo_path']}", errors)
    for row in MANIFEST["signed_weight_files"]:
        path = REPO / row["source_in_this_repo"]
        check(path.is_file() and sha(path) == row["sha256"], f" signed bytes: {row['namespace']}", errors)
    check((HERE / "SUPERVISOR_ARGS.diff").is_file(), " supervisor semantic diff exists", errors)
    if key_path is not None:
        lane = _load_module(HERE / "files/lane_weights.py", "co_lane_weights_package")
        key = lane.load_signing_key(key_path)
        for row in MANIFEST["signed_weight_files"]:
            envelope = json.loads((REPO / row["source_in_this_repo"]).read_text())
            verified = lane.verify_envelope(
                envelope,
                key=key,
                namespace=row["namespace"],
                expected_sleeves=envelope["scope_sleeves"],
            )
            check(
                verified["source_digest_sha256"] == row["source_digest_sha256"],
                f" signature + source digest: {row['namespace']}",
                errors,
            )


def preflight(root: Path, errors: list[str]) -> None:
    for row in MANIFEST["files"]:
        path = _destination(root, row)
        if row["new_file"]:
            check(not path.exists(), f" host new path absent: {row['repo_path']}", errors)
        else:
            check(
                path.is_file() and sha(path) == row["sha256_before_expected"],
                f" host before bytes: {row['repo_path']}",
                errors,
            )
    supervisor = root / "scripts/run_book_supervisor.ps1"
    check(supervisor.is_file(), " host supervisor exists", errors)
    if supervisor.is_file():
        got = sha(supervisor)
        check(
            got.startswith(MANIFEST["host_state_of_record"]["supervisor_sha256_prefix"]),
            f" host supervisor receipt prefix ({got[:12]})",
            errors,
        )
        _check_current_contracts(supervisor.read_text(encoding="utf-8", errors="replace"), errors)


def postflight(root: Path, errors: list[str]) -> None:
    for row in MANIFEST["files"]:
        path = _destination(root, row)
        check(
            path.is_file() and sha(path) == row["sha256_after_carry"],
            f" host after bytes: {row['repo_path']}",
            errors,
        )


def _check_current_contracts(source: str, errors: list[str]) -> None:
    checks = (
        "crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout",
        "crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert",
        "mx_btcusd_d1_donchian_20_breakout",
        "sub_mid_dn_revert,sub_xvol_pullback",
    )
    for text in checks:
        check(text in source, f" supervisor current contract contains {text}", errors)


def _check_windows_acl(key_path: Path, errors: list[str]) -> None:
    if os.name != "nt":
        return
    result = subprocess.run(["icacls", str(key_path)], capture_output=True, text=True)
    output = (result.stdout + result.stderr).lower()
    broad = any(name in output for name in ("everyone:", "builtin\\users:", "authenticated users:"))
    check(result.returncode == 0 and not broad, " external key ACL excludes broad principals", errors)


def activated(root: Path, key_path: Path, errors: list[str]) -> None:
    postflight(root, errors)
    weights_root = Path(r"C:\ProgramData\GTOS\lane-weights") if os.name == "nt" else HERE / "files"
    for row in MANIFEST["signed_weight_files"]:
        path = weights_root / Path(row["destination_on_vps"]).name
        check(path.is_file() and sha(path) == row["sha256"], f" deployed signed file: {row['namespace']}", errors)
    check(key_path.is_file() and len(key_path.read_bytes()) == 32, " external key exists at 32 bytes", errors)
    _check_windows_acl(key_path, errors)
    supervisor = root / "scripts/run_book_supervisor.ps1"
    source = supervisor.read_text(encoding="utf-8", errors="replace") if supervisor.is_file() else ""
    _check_current_contracts(source, errors)
    for token in (
        "--lane-weights",
        "--lane-weights-key",
        "operator_profile.json",
        "redacted_account_live_bee34003.json",
        "lane_weights.key",
    ):
        check(token in source, f" supervisor activation contains {token}", errors)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def behaviour(key_path: Path, errors: list[str]) -> None:
    lane = _load_module(HERE / "files/lane_weights.py", "co_lane_weights_behaviour")
    key = lane.load_signing_key(key_path)
    ftmo_row = next(row for row in MANIFEST["signed_weight_files"] if row["namespace"].startswith("ftmo"))
    source = REPO / ftmo_row["source_in_this_repo"]
    with tempfile.TemporaryDirectory(prefix="co-lane-probe-") as td:
        temp = Path(td)
        controller = lane.LaneWeightController(
            namespace=ftmo_row["namespace"],
            expected_sleeves=json.loads(source.read_text())["scope_sleeves"],
            repo_root=temp,
            weights_path=source,
            key_path=key_path,
        )
        active = controller.snapshot(datetime.fromisoformat("2026-08-02T00:01:00+00:00"))
        check(active["status"] == "active", " signed vector activates", errors)
        check(active["weights"]["crypto"] == 1.15, " crypto applies x1.15", errors)
        check(active["weights"]["mx_btcusd_d1_donchian_20_breakout"] == 1.15, " mx applies x1.15", errors)
        check(max(active["weights"].values()) <= 1.15, " declared up-band enforced", errors)
        check(
            lane.format_active_log(active)
            == "LANE WEIGHTS ACTIVE: crypto=1.15 energy_agri=1.00 "
               "mx_btcusd_d1_donchian_20_breakout=1.15 sub_mid_dn_revert=1.00 "
               "sub_xvol_pullback=1.00",
            " proving log line exact",
            errors,
        )
        # Replace the file after the latch; a fresh controller must recover the persisted
        # original, not the intraday replacement.
        replacement_path = temp / "replacement.json"
        replacement = json.loads(source.read_text())
        replacement["weights"]["crypto"] = 0.5
        replacement = lane.sign_envelope(replacement, key)
        replacement_path.write_text(json.dumps(replacement), encoding="utf-8")
        restarted = lane.LaneWeightController(
            namespace=ftmo_row["namespace"],
            expected_sleeves=active["scope_sleeves"],
            repo_root=temp,
            weights_path=replacement_path,
            key_path=key_path,
        ).snapshot(datetime.fromisoformat("2026-08-02T12:00:00+00:00"))
        check(restarted["source_digest_sha256"] == active["source_digest_sha256"], " restart reuses day latch", errors)
        # Bad signature in a fresh namespace/root becomes a complete neutral vector.
        bad = dict(json.loads(source.read_text()))
        bad["signature_hmac_sha256"] = "0" * 64
        bad_path = temp / "bad.json"
        bad_path.write_text(json.dumps(bad), encoding="utf-8")
        neutral = lane.LaneWeightController(
            namespace=ftmo_row["namespace"],
            expected_sleeves=active["scope_sleeves"],
            repo_root=temp / "bad-root",
            weights_path=bad_path,
            key_path=key_path,
        ).snapshot(datetime.fromisoformat("2026-08-02T00:01:00+00:00"))
        check(neutral["status"] == "neutral", " bad signature fails neutral", errors)
        check(set(neutral["weights"].values()) == {1.0}, " bad signature is all-or-neutral", errors)

    # Packet payload is loaded under the real package hierarchy so its relative
    # placement_ledger import resolves, without importing the broker-capable launcher.
    packet = _load_module(
        HERE / "files/runtime_learning_packet.py",
        "src.components.ultimate_book.runtime_learning_packet_co_payload",
    )
    built = packet.build_runtime_learning_packet(
        namespace=ftmo_row["namespace"],
        event_type="unit_shadow",
        ts="2026-08-02T00:01:00+00:00",
        bridge={"runtime_effect_now": False, "lane_weights": active},
        unit={"sleeve_members": ["crypto"]},
        outcome={"sleeve": "crypto", "placement_status": "shadow"},
    )
    valid, issues = packet.validate_runtime_learning_packet(built)
    check(valid, f" packet payload validates ({issues})", errors)
    check(built.get("lane_weight") == 1.15, " packet stamps applied weight", errors)
    check(
        (built.get("lane_weight_provenance") or {}).get("source_digest_sha256")
        == active["source_digest_sha256"],
        " packet stamps signed-source provenance",
        errors,
    )

    for filename, required in {
        "book_engine.py": ("lane_weight_controller", "ultimate_book_learning_rerate", "lane_weights"),
        "book_owner.py": ("lane_weight_controller", 'bridge["lane_weights"]', 'summary["lane_weights"]'),
        "run_book.py": ("--lane-weights", "--lane-weights-key", "lane_weight_controller"),
    }.items():
        text = (HERE / "files" / filename).read_text(encoding="utf-8")
        check(all(item in text for item in required), f" carried wiring anchors: {filename}", errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", choices=("package", "preflight", "postflight", "behaviour", "all", "activated"), required=True)
    parser.add_argument("--root", default=str(REPO))
    parser.add_argument("--key", default=None)
    parser.add_argument("--receipt", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    key = Path(args.key).resolve() if args.key else None
    errors: list[str] = []
    if args.check == "package":
        package_check(key, errors)
    elif args.check == "preflight":
        preflight(root, errors)
    elif args.check == "postflight":
        postflight(root, errors)
    elif args.check == "behaviour":
        if key is None:
            parser.error("--key is required for behaviour")
        behaviour(key, errors)
    elif args.check == "all":
        if key is None:
            parser.error("--key is required for all")
        package_check(key, errors)
        postflight(root, errors)
        behaviour(key, errors)
    elif args.check == "activated":
        if key is None:
            parser.error("--key is required for activated")
        activated(root, key, errors)
        behaviour(key, errors)
    passed = not errors
    print(f"RESULT: {'PASS' if passed else 'FAIL'} ({len(errors)} errors)")
    if args.receipt:
        proving_lines = []
        for row in MANIFEST["signed_weight_files"]:
            envelope = json.loads((REPO / row["source_in_this_repo"]).read_text())
            rendered = " ".join(
                f"{s}={float(envelope['weights'][s]):.2f}"
                for s in sorted(envelope["weights"])
            )
            proving_lines.append({
                "namespace": row["namespace"],
                "line": "LANE WEIGHTS ACTIVE: " + rendered,
            })
        receipt = {
            "schema": "gtos.phase17.co_carry_probe.v1",
            "check": args.check,
            "ok": passed,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "manifest_sha256": sha(HERE / "MANIFEST.json"),
            "key_secret_or_digest_recorded": False,
            "checks": RESULTS,
            "errors": errors,
            "proving_log_lines": proving_lines,
        }
        receipt_path = Path(args.receipt)
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = receipt_path.with_name(f".{receipt_path.name}.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, receipt_path)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
