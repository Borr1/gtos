#!/usr/bin/env python3
"""Verify Session CN's live-cost carry without importing or calling a broker adapter.

The verifier never imports ``run_book.py``, never constructs ``RealMT5``, and shadows the
``MetaTrader5`` module in every import probe.  ``payload`` operates only on package bytes.
``preflight``/``postflight``/``all`` are for the orchestrator's staged host ceremony.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
MANIFEST_PATH = HERE / "MANIFEST.json"
FILES = HERE / "files"
REFUSE = 3
BROKER_CLOCK_HOST_SHA = "0f97bbb64bc55b0213e47a018c2e884d83b2059b61de7941a171fd3cf2fef552"

_problems: list[str] = []


def say(ok: bool | None, message: str) -> None:
    label = {True: "  ok  ", False: " FAIL ", None: "  --  "}[ok]
    print(f"[{label}] {message}")
    if ok is False:
        _problems.append(message)


def sha_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def default_repo_root() -> Path:
    root = HERE.parents[4]
    if not (root / "config/agent_config.yaml").is_file():
        raise SystemExit(f"NOT_A_GTOS_ROOT:{root}")
    return root


def check_payload(man: dict) -> int:
    mark = len(_problems)
    print("\n== payload hashes, syntax, and truth artifact ==")
    for rec in man["files"]:
        payload = FILES / rec["payload_basename"]
        got = sha_file(payload)
        say(
            got == rec["sha256_after_carry"],
            f"{rec['repo_path']}: payload {got[:12] if got else 'ABSENT'} "
            f"({'==' if got == rec['sha256_after_carry'] else '!='} manifest after)",
        )
        if payload.suffix == ".py" and payload.is_file():
            try:
                py_compile.compile(
                    str(payload),
                    cfile=str(Path(tempfile.mkdtemp(prefix="gtos_cn_pyc_")) / "probe.pyc"),
                    doraise=True,
                )
                say(True, f"{rec['repo_path']}: compiles")
            except Exception as exc:  # noqa: BLE001
                say(False, f"{rec['repo_path']}: compile failed: {exc!r}")
    try:
        truth = json.loads((FILES / "BROKER_TRUE_COSTS_V1.json").read_text())
        accounts = truth.get("accounts") or {}
        say(
            set(accounts) == {"FTMO", "redacted_account"},
            f"broker truth account keys = {sorted(accounts)}",
        )
        say(
            all(accounts[a].get("instruments") for a in accounts),
            "both broker-truth accounts have priced instruments",
        )
    except Exception as exc:  # noqa: BLE001
        say(False, f"broker truth artifact failed to parse: {exc!r}")
    return len(_problems) - mark


def _classify(rec: dict, got: str | None) -> str:
    if got == rec["sha256_after_carry"]:
        return "after"
    if rec["is_new_file_on_vps"] and got is None:
        return "before"
    if not rec["is_new_file_on_vps"] and got == rec["sha256_before_expected"]:
        return "before"
    return "unknown"


def check_preflight(root: Path, man: dict) -> int:
    mark = len(_problems)
    print("\n== preflight: exact host bytes before any copy ==")
    for rec in man["files"]:
        got = sha_file(root / rec["repo_path"])
        state = _classify(rec, got)
        if state == "before":
            expected = "ABSENT" if got is None else got[:12]
            say(True, f"{rec['repo_path']}: expected before-state {expected}")
        elif state == "after":
            say(None, f"{rec['repo_path']}: already at after-bytes {got[:12]}")
        else:
            say(
                False,
                f"{rec['repo_path']}: UNRECOGNISED {got[:12] if got else 'ABSENT'}; "
                "do not overwrite—rebuild against these host bytes",
            )
    clock = sha_file(root / "src/utils/broker_clock.py")
    say(
        clock == BROKER_CLOCK_HOST_SHA,
        f"src/utils/broker_clock.py prerequisite = {clock[:12] if clock else 'ABSENT'} "
        f"(expected carried {BROKER_CLOCK_HOST_SHA[:12]})",
    )
    for rec in man["not_carried"]:
        path = root / rec["repo_path"]
        got = sha_file(path)
        say(
            got is not None,
            f"READ-ONLY ceremony capture {rec['repo_path']} = {got[:12] if got else 'ABSENT'}; "
            "record this value and require byte identity post-copy",
        )
    return len(_problems) - mark


def check_postflight(root: Path, man: dict) -> int:
    mark = len(_problems)
    print("\n== postflight: every destination at manifest after-bytes ==")
    for rec in man["files"]:
        got = sha_file(root / rec["repo_path"])
        ok = got == rec["sha256_after_carry"]
        say(
            ok,
            f"{rec['repo_path']}: {got[:12] if got else 'ABSENT'} "
            f"({'==' if ok else '!='} after {rec['sha256_after_carry'][:12]})",
        )
    return len(_problems) - mark


def check_deps(root: Path, man: dict) -> int:
    mark = len(_problems)
    print("\n== dependency and interrupted-copy ordering ==")
    records = {rec["repo_path"]: rec for rec in man["files"]}
    states = {
        path: _classify(rec, sha_file(root / path)) for path, rec in records.items()
    }
    after = {path for path, state in states.items() if state == "after"}
    dependencies = (
        ("src/costs/model.py", "src/costs/coverage.py"),
        ("src/costs/__init__.py", "src/costs/model.py"),
        (
            "src/components/ultimate_book/book_owner.py",
            "src/components/ultimate_book/packet_economics.py",
        ),
        ("src/components/broker_net_cost_engine.py", "src/costs/model.py"),
        ("src/components/broker_net_cost_engine.py", "src/costs/coverage.py"),
        (
            "src/components/broker_net_cost_engine.py",
            "research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json",
        ),
    )
    for dependent, prerequisite in dependencies:
        safe = dependent not in after or prerequisite in after
        say(
            safe,
            f"{dependent} after requires {prerequisite} after "
            f"(states {states[dependent]}/{states[prerequisite]})",
        )
    engine_state = states["src/components/broker_net_cost_engine.py"]
    if engine_state == "before" and after:
        say(None, "prerequisites may be present while the engine is before-bytes: economically inert")
    unknown = sorted(path for path, state in states.items() if state == "unknown")
    say(not unknown, f"all carry paths recognised; unknown={unknown}")
    return len(_problems) - mark


IMPORT_PROBE = r'''
import sys, types
sys.modules["MetaTrader5"] = types.ModuleType("MetaTrader5")
import src.costs.model
import src.components.broker_net_cost_engine
import src.components.ultimate_book.packet_economics
import src.components.ultimate_book.book_owner
print("IMPORTS_OK")
'''


def _run_probe(root: Path, source: str, *, name: str) -> bool:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root)
    result = subprocess.run(
        [sys.executable, "-c", source],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        say(False, f"{name} failed rc={result.returncode}: {result.stderr[-1500:]}")
        return False
    say(True, f"{name}: {result.stdout.strip().splitlines()[-1]}")
    return True


def check_imports(root: Path, man: dict) -> int:
    mark = len(_problems)
    print("\n== imports: broker module shadowed, no book or broker constructed ==")
    for rec in man["files"]:
        if not rec["repo_path"].endswith(".py"):
            continue
        try:
            py_compile.compile(
                str(root / rec["repo_path"]),
                cfile=str(Path(tempfile.mkdtemp(prefix="gtos_cn_host_pyc_")) / "probe.pyc"),
                doraise=True,
            )
            say(True, f"{rec['repo_path']}: compiles on staged root")
        except Exception as exc:  # noqa: BLE001
            say(False, f"{rec['repo_path']}: compile failed: {exc!r}")
    _run_probe(root, IMPORT_PROBE, name="isolated import closure")
    return len(_problems) - mark


BEHAVIOUR_PROBE = r'''
import ast
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Any

sys.modules["MetaTrader5"] = types.ModuleType("MetaTrader5")

from src.components.broker_net_cost_engine import (
    BROKER_TRUE_COMMISSION_MODE,
    LEGACY_ZERO_COMMISSION_COMPARATOR_MODE,
    build_pretrade_cost_packet,
)
from src.components.ultimate_book.packet_economics import build_cost_block

ROOT = Path.cwd()


def cfg(namespace="redacted_account_live_bee34003", server="redacted_account-Server 2"):
    return {
        "gtos_vnext_runtime": {
            "enabled": True,
            "apply_to_execution": True,
            "mode": "production_replacement_vnext_moonshot",
            "selected_cell_pretrade_cost_model_required": True,
            "selected_cell_pretrade_max_spread_r": 0.10,
            "selected_cell_pretrade_max_total_cost_r": 0.15,
            "selected_cell_commission_model_required": True,
            "selected_cell_swap_model_required": True,
            "selected_cell_swap_cost_model_required": True,
            "selected_cell_swap_cost_live_symbol_info_required": True,
            "selected_cell_swap_cost_minutes_per_bar": 15,
            "selected_cell_swap_cost_horizon_days_cap": 1.0,
            "selected_cell_default_expected_slippage_r": 0.0,
            "selected_cell_profile_namespace_required": True,
        },
        "runtime": {
            "profile_namespace": namespace,
            "broker_account_namespace": namespace,
        },
        "broker_profile": {"broker": "redacted_account", "server": server},
    }


symbol_info = {
    "point": 0.001,
    "trade_tick_size": 0.001,
    "trade_tick_value": 0.1,
    "trade_contract_size": 100.0,
    "volume_min": 0.01,
    "volume_max": 100.0,
    "volume_step": 0.01,
    "trade_stops_level": 0,
    "trade_freeze_level": 0,
    "trade_mode": 4,
    "filling_mode": 1,
    "swap_long": -5.083,
    "swap_short": -42.38,
    "swap_mode": 1,
    "swap_rollover3days": 5,
}
trade = {
    "direction": "LONG",
    "entry_price": 80.038,
    "stop_loss": 79.238,
    "gtos_vnext_production_execution_path": True,
    "gtos_vnext_selected_cell_risk_pct": 0.1,
    "gtos_vnext_selected_cell_risk_cell_id": "CN::energy_agri::USOIL_cash",
    "gtos_vnext_selected_cell_risk_decision_basis": "carry_behaviour_probe",
    "gtos_vnext_commission_model_status": "COMMISSION_INCLUDED_IN_SELECTED_CELL_RISK",
    "gtos_vnext_dynamic_time_stop_bars": 32,
    "gtos_vnext_source_event_details": {"sleeve": "energy_agri"},
}
common = dict(
    config=cfg(),
    trade_params=trade,
    tick=SimpleNamespace(bid=79.962, ask=80.038, spread_cents=7.6, time="2024-06-03T14:00:00Z"),
    symbol="USOIL_cash",
    broker_symbol="USOUSD",
    entry_price=80.038,
    stop_loss=79.238,
    sl_distance=0.8,
    risk_pct=0.1,
    symbol_info=symbol_info,
    asof_utc="2024-06-03T14:00:00Z",
)
old = build_pretrade_cost_packet(
    **common, commission_mode=LEGACY_ZERO_COMMISSION_COMPARATOR_MODE
)
new = build_pretrade_cost_packet(**common)
assert old["status"] == "PASSED", old
assert new["status"] == "REFUSED", new
assert abs(new["commission_r"] - 0.0625) < 1e-12, new["commission_r"]
assert new["commission_mode"] == BROKER_TRUE_COMMISSION_MODE
assert new["model_version"].endswith("_v3")
assert new["cost_excludes"] == []
assert new["total_cost_components_expected"][-1] == "commission_r"
assert new["commission_cost"]["source_status"] == "captured"
assert old["cost_excludes"] == ["commission"]

unknown_common = dict(common)
unknown_common["config"] = cfg(namespace="unknown", server="Unknown-Server")
unknown = build_pretrade_cost_packet(**unknown_common)
assert unknown["status"] == "REFUSED"
assert unknown["total_cost_r"] is None
assert any(
    reason.startswith("missing_broker_true_commission_cost_r_conversion")
    for reason in unknown["refusal_reasons"]
)

# Preserve the VPS-lineage guard CN deliberately built on: config fallback swap is not accepted
# as a live symbol-info capture.
fallback_cfg = cfg()
fallback_cfg["market"] = dict(symbol_info)
fallback_common = dict(common)
fallback_common["config"] = fallback_cfg
fallback_common["symbol_info"] = None
fallback = build_pretrade_cost_packet(
    **fallback_common, commission_mode=LEGACY_ZERO_COMMISSION_COMPARATOR_MODE
)
assert any(
    reason.startswith("swap_cost_requires_live_symbol_info")
    for reason in fallback["refusal_reasons"]
), fallback

# Execute the exact static method body from the carried owner without importing or constructing
# the owner (and therefore without reaching any runtime or broker-capable dependency).
owner_path = ROOT / "src/components/ultimate_book/book_owner.py"
tree = ast.parse(owner_path.read_text(), filename=str(owner_path))
method = next(
    node for node in ast.walk(tree)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name == "_runtime_learning_modelled_cost"
)
method.decorator_list = []
module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
ns = {
    "Any": Any,
    "MODELLED_COST_COMPONENTS": ("spread_r", "expected_slippage_r", "swap_cost_r", "commission_r"),
    "MODELLED_COST_EXCLUDES": (),
    "LEGACY_MODELLED_COST_COMPONENTS": ("spread_r", "expected_slippage_r", "swap_cost_r"),
    "LEGACY_MODELLED_COST_EXCLUDES": ("commission",),
}
exec(compile(module, str(owner_path), "exec"), ns)
flatten = ns["_runtime_learning_modelled_cost"]
flat = flatten({"gtos_vnext_pretrade_cost_model": new})
assert flat["modelled_cost_model_version"].endswith("_v3")
assert flat["modelled_commission_mode"] == BROKER_TRUE_COMMISSION_MODE
assert flat["modelled_commission_cost_source_status"] == "captured"
assert flat["modelled_commission_cost_artifact"] == "BROKER_TRUE_COSTS_V1.json"
assert flat["modelled_cost_components"]["commission_r"] == new["commission_r"]
assert flat["modelled_cost_excludes"] == []

v2_flat = flatten({"gtos_vnext_pretrade_cost_model": {
    "model_version": "vnext_selected_cell_pretrade_cost_model_v2",
    "status": "PASSED",
    "total_cost_r": 0.1,
    "total_cost_components": {
        "spread_r": 0.08, "expected_slippage_r": 0.01, "swap_cost_r": 0.01,
    },
}})
assert v2_flat["modelled_cost_excludes"] == ["commission"]
assert v2_flat["modelled_cost_components_expected"] == [
    "spread_r", "expected_slippage_r", "swap_cost_r"
]

v2_econ = build_cost_block({
    **v2_flat,
    "broker_entry_commission": -2.5,
    "broker_exit_commission": -2.5,
})
v3_econ = build_cost_block({
    **flat,
    "broker_entry_commission": -2.5,
    "broker_exit_commission": -2.5,
})
assert v2_econ["modelled_vs_realized_comparable"] is False
assert v3_econ["modelled_vs_realized_comparable"] is True

print(json.dumps({
    "status": "BEHAVIOUR_OK",
    "old": old["status"],
    "new": new["status"],
    "commission_r": new["commission_r"],
    "unknown": unknown["status"],
    "v2_readable": True,
    "v3_comparable": True,
}, sort_keys=True))
'''


def _payload_tree(source_root: Path, man: dict) -> tempfile.TemporaryDirectory:
    tmp = tempfile.TemporaryDirectory(prefix="gtos_cn_payload_")
    root = Path(tmp.name)
    for marker in ("src/__init__.py", "src/utils/__init__.py"):
        src = source_root / marker
        dst = root / marker
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            shutil.copy2(src, dst)
        else:
            dst.write_text("")
    for dep in ("src/utils/broker_profile.py", "src/utils/broker_clock.py"):
        src = source_root / dep
        if not src.is_file():
            raise RuntimeError(f"payload probe prerequisite absent: {src}")
        dst = root / dep
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    for rec in man["files"]:
        src = FILES / rec["payload_basename"]
        dst = root / rec["repo_path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return tmp


def check_behaviour(root: Path, man: dict, *, payload: bool = False) -> int:
    mark = len(_problems)
    print("\n== behaviour: same-input comparator/default, failure closure, v2/v3 schema ==")
    temp = None
    probe_root = root
    try:
        if payload:
            temp = _payload_tree(root, man)
            probe_root = Path(temp.name)
        _run_probe(probe_root, BEHAVIOUR_PROBE, name="offline carry behaviour probe")
    except Exception as exc:  # noqa: BLE001
        say(False, f"could not construct/run behaviour probe: {exc!r}")
    finally:
        if temp is not None:
            temp.cleanup()
    return len(_problems) - mark


def check_rollback(root: Path, man: dict) -> int:
    mark = len(_problems)
    print("\n== rollback: existing files restored; new dependencies absent or retained intentionally ==")
    for rec in man["files"]:
        got = sha_file(root / rec["repo_path"])
        if rec["is_new_file_on_vps"]:
            ok = got in (None, rec["sha256_after_carry"])
            say(
                ok,
                f"{rec['repo_path']}: {got[:12] if got else 'ABSENT'}; it must be ABSENT iff "
                "the ceremony preflight recorded ABSENT, otherwise retain the pre-existing after-byte",
            )
        else:
            ok = got == rec["sha256_before_expected"]
            say(
                ok,
                f"{rec['repo_path']}: {got[:12] if got else 'ABSENT'} "
                f"({'==' if ok else '!='} before {rec['sha256_before_expected'][:12]})",
            )
    return len(_problems) - mark


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        required=True,
        choices=("payload", "preflight", "postflight", "deps", "imports", "behaviour", "rollback", "all"),
    )
    parser.add_argument("--repo-root", type=Path)
    args = parser.parse_args()
    root = (args.repo_root or default_repo_root()).resolve()
    man = manifest()

    if args.check == "payload":
        check_payload(man)
        check_behaviour(root, man, payload=True)
    elif args.check == "preflight":
        check_preflight(root, man)
        check_deps(root, man)
    elif args.check == "postflight":
        check_postflight(root, man)
    elif args.check == "deps":
        check_deps(root, man)
    elif args.check == "imports":
        check_imports(root, man)
    elif args.check == "behaviour":
        check_behaviour(root, man)
    elif args.check == "rollback":
        check_rollback(root, man)
    elif args.check == "all":
        check_payload(man)
        check_postflight(root, man)
        check_deps(root, man)
        check_imports(root, man)
        check_behaviour(root, man)

    if _problems:
        print(f"\nREFUSED: {len(_problems)} problem(s)")
        return REFUSE
    print("\nPASS: requested CN carry checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
