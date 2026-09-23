#!/usr/bin/env python3
"""Build Session CM's one-file, default-off armed-fidelity carry.

The funded host is not mainline.  Its current ``execution_packets.py`` is the exact
after-payload of Session AZ's executed MX ceremony; Session CE's later spread-floor carry did
not touch this path.  This builder therefore starts from AZ's recorded host bytes and applies
five exact, single-match edits.  It never reads a broker, config value, token, or live state.

Run from the repository root::

    python3 docs/audits/fable5-vision-audit-20260725/phase17/activation_carry_armed_fidelity/build_carry.py
    python3 docs/audits/fable5-vision-audit-20260725/phase17/activation_carry_armed_fidelity/build_carry.py --check
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import py_compile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
AZ = ROOT / "docs/audits/fable5-vision-audit-20260725/phase13/activation_carry_mx"
BEFORE_PATH = AZ / "files/execution_packets.py"
FILES = HERE / "files"
DIFFS = HERE / "diffs"

HOST_BEFORE_SHA256 = "06a301bff0db7b2b902cf70384f033d46ee8ba2ba2b9b5215bf580281ebdeb10"
HOST_BEFORE_BYTES = 38_376


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def anchored(src: str, old: str, new: str, *, name: str) -> str:
    count = src.count(old)
    if count != 1:
        raise SystemExit(
            f"ABORT: {name} anchor matched {count} times, expected exactly one.\n"
            f"--- anchor ---\n{old}\n--------------"
        )
    return src.replace(old, new, 1)


OVERRIDE_OLD = '''    "sub_xvol_pullback": dict(
        final_target_r=4.0,
        final_from_intent=False,
        frontier_cell="target_4R",
        frontier_evidence="phase8/receipts/AK_EXIT_FRONTIER_V2.json",
    ),
}'''

OVERRIDE_NEW = '''    "sub_xvol_pullback": dict(
        final_target_r=4.0,
        final_from_intent=False,
        frontier_cell="target_4R",
        frontier_evidence="phase8/receipts/AK_EXIT_FRONTIER_V2.json",
    ),
    # Session CM (B2700-B2749): AD's measured-best stop-width cell, re-read through the
    # production crypto generator on CJ's true-UTC TRAIN/VAL lane. FTMO RECORDED improves by
    # +0.2527 R/day at the mid band, the latest fold remains +0.0355 better, and 4/5 paired
    # folds improve at every cost band. redacted_account's latest fold is negative, so the ceremony
    # selects this name on FTMO only. The multiplier rebuilds BOTH broker SL and TP from the
    # scaled risk unit, exactly matching AD's stop_1.5x_tgtscale cell.
    "crypto": dict(
        stop_distance_multiplier=1.5,
        frontier_cell="stop_1p5x_target_scale",
        frontier_evidence="phase17/receipts/CM_REVERIFY_V1.json",
    ),
}'''

KINDS_OLD = 'FRONTIER_CELL_KINDS: tuple[str, ...] = ("target_", "time_stop_")'
KINDS_NEW = '''#: ``stop_`` is a stop-width contract: both broker SL and TP must be rebuilt from R.
FRONTIER_CELL_KINDS: tuple[str, ...] = ("target_", "time_stop_", "stop_")'''

DESCRIBE_OLD = '''    bars = over.get("time_stop_bars")
    if bars is not None:
        parts.append(f"time stop {int(bars)} printed M15 bars")
    return ", ".join(parts) if parts else "contract override"
'''
DESCRIBE_NEW = '''    bars = over.get("time_stop_bars")
    if bars is not None:
        parts.append(f"time stop {int(bars)} printed M15 bars")
    stop_mult = over.get("stop_distance_multiplier")
    if stop_mult is not None:
        parts.append(f"stop distance x{float(stop_mult):g} with target scaled")
    return ", ".join(parts) if parts else "contract override"
'''

RISK_OLD = '''    entry_price = float(_g(geometry, "entry_price"))
    risk_distance = float(_g(geometry, "risk_distance", intent.stop_dist))

    # ---- per-sleeve native exit profile (replaces the forced momentum_exhaustion 2R) ----
    prof = resolve_exit_profile(getattr(intent, "sleeve", None), frontier_exits=frontier_exits)
    policy = str(prof["policy"])
'''
RISK_NEW = '''    entry_price = float(_g(geometry, "entry_price"))
    base_risk_distance = float(_g(geometry, "risk_distance", intent.stop_dist))

    # ---- per-sleeve native exit profile (replaces the forced momentum_exhaustion 2R) ----
    prof = resolve_exit_profile(getattr(intent, "sleeve", None), frontier_exits=frontier_exits)
    stop_distance_multiplier = float(prof.get("stop_distance_multiplier", 1.0))
    if stop_distance_multiplier <= 0:
        raise ValueError(
            f"stop_distance_multiplier must be > 0, got {stop_distance_multiplier!r}"
        )
    risk_distance = base_risk_distance * stop_distance_multiplier
    policy = str(prof["policy"])
'''

STOP_OLD = '    stop_loss = float(_g(geometry, "stop_loss", entry_price - sign * risk_distance))\n'
STOP_NEW = '''    # A selected width cell must rebuild the broker SL from scaled R. With multiplier
    # 1.0 the caller-supplied stop_loss still wins, preserving the exact default path.
    stop_loss = (
        float(_g(geometry, "stop_loss", entry_price - sign * risk_distance))
        if stop_distance_multiplier == 1.0
        else entry_price - sign * risk_distance
    )
'''


def build_payload() -> tuple[bytes, bytes]:
    before = BEFORE_PATH.read_bytes()
    if sha(before) != HOST_BEFORE_SHA256 or len(before) != HOST_BEFORE_BYTES:
        raise SystemExit("ABORT: Session AZ's recorded host payload moved")
    src = before.decode("utf-8")
    src = anchored(src, OVERRIDE_OLD, OVERRIDE_NEW, name="crypto override")
    src = anchored(src, KINDS_OLD, KINDS_NEW, name="frontier cell vocabulary")
    src = anchored(src, DESCRIBE_OLD, DESCRIBE_NEW, name="launch banner")
    src = anchored(src, RISK_OLD, RISK_NEW, name="scaled risk distance")
    src = anchored(src, STOP_OLD, STOP_NEW, name="scaled broker stop")
    after = src.encode("utf-8")
    return before, after


def render_diff(before: bytes, after: bytes) -> bytes:
    lines = difflib.unified_diff(
        before.decode().splitlines(keepends=True),
        after.decode().splitlines(keepends=True),
        fromfile="a/src/components/ultimate_book/execution_packets.py",
        tofile="b/src/components/ultimate_book/execution_packets.py",
    )
    return "".join(lines).encode("utf-8")


def manifest(after: bytes, diff: bytes) -> dict:
    return {
        "schema_version": "gtos-activation-carry-v1",
        "session": "CM",
        "built_utc_day": "2026-08-01",
        "purpose": "FTMO-only crypto stop_1p5x_target_scale fidelity selection",
        "authority": "phase17/OD_ALL_IN_20260801.md",
        "host_lineage": {
            "latest_verified_host_commit": "267cccc94",
            "latest_verified_receipt": "phase15/receipts/SPREAD_FLOOR_ARMED_20260731.md",
            "before_bytes_source": "phase13/activation_carry_mx/files/execution_packets.py",
            "before_bytes_receipt": "phase13/receipts/MX_ACTIVATION_20260731.md",
            "why_still_current": "Session CE's later executed carry changed spread_geometry.py, book_engine.py, book_owner.py, run_book.py, and the supervisor; it did not touch execution_packets.py.",
        },
        "selection": {
            "ftmo_tags_before_and_after": "crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout",
            "ftmo_frontier_before": "mx_btcusd_d1_donchian_20_breakout",
            "ftmo_frontier_after": "mx_btcusd_d1_donchian_20_breakout,crypto",
            "redacted_account_tags_before_and_after": "crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert",
            "redacted_account_frontier_before_and_after": None,
            "spread_geometry_floor_both_before_and_after": "sub_mid_dn_revert,sub_xvol_pullback",
        },
        "supervisor": {
            "latest_receipt_sha256_prefix": "63079cec",
            "rule": "The orchestrator must record the full current SHA-256 and byte count before editing, prove the recorded semantic before-state, then record the full after SHA-256. No packaged whole-file replacement exists for this host-forked launcher.",
        },
        "files": [{
            "copy_order": 1,
            "repo_path": "src/components/ultimate_book/execution_packets.py",
            "destination_on_vps": "src\\components\\ultimate_book\\execution_packets.py",
            "payload_basename": "execution_packets.py",
            "source_in_this_repo": "docs/audits/fable5-vision-audit-20260725/phase17/activation_carry_armed_fidelity/files/execution_packets.py",
            "diff_in_this_repo": "docs/audits/fable5-vision-audit-20260725/phase17/activation_carry_armed_fidelity/diffs/src_components_ultimate_book_execution_packets.py.diff",
            "sha256_before_expected": HOST_BEFORE_SHA256,
            "bytes_before": HOST_BEFORE_BYTES,
            "sha256_after_carry": sha(after),
            "bytes_after": len(after),
            "sha256_diff": sha(diff),
            "crlf_present": b"\r\n" in after,
            "source_kind": "executed-host payload + five exact anchored edits",
            "default_effect": "INERT until --frontier-exits selects crypto; all multiplier-1 paths are identity-preserved",
        }],
        "forbidden_paths": [
            "config/agent_config.yaml",
            "config/profiles/redacted_account.yaml",
            "activation token files",
            "broker/VPS state outside the orchestrator ceremony",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    before, after = build_payload()
    diff = render_diff(before, after)
    man_bytes = (json.dumps(manifest(after, diff), indent=2, sort_keys=True) + "\n").encode()
    outputs = {
        FILES / "execution_packets.py": after,
        DIFFS / "src_components_ultimate_book_execution_packets.py.diff": diff,
        HERE / "MANIFEST.json": man_bytes,
    }
    if args.check:
        moved = [str(path.relative_to(ROOT)) for path, data in outputs.items()
                 if not path.is_file() or path.read_bytes() != data]
        if moved:
            raise SystemExit("ABORT: generated carry drifted: " + ", ".join(moved))
    else:
        FILES.mkdir(parents=True, exist_ok=True)
        DIFFS.mkdir(parents=True, exist_ok=True)
        for path, data in outputs.items():
            path.write_bytes(data)
    with tempfile.TemporaryDirectory(prefix="gtos_cm_carry_") as td:
        py_compile.compile(str(FILES / "execution_packets.py"),
                           cfile=str(Path(td) / "execution_packets.pyc"), doraise=True)
    print(
        f"CM carry {'CHECKED' if args.check else 'BUILT'}: "
        f"{HOST_BEFORE_SHA256[:12]} ({len(before)} B) -> {sha(after)[:12]} ({len(after)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
