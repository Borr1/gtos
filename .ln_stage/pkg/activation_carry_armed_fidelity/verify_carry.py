#!/usr/bin/env python3
"""Offline verifier for Session CM's one-file armed-fidelity carry.

This verifier imports only the pure packet builder.  It never imports MetaTrader5, opens a
terminal, constructs a broker client, calls an order path, or writes runtime state.  The
launcher checks read ``run_book_supervisor.ps1`` as text; they never start or stop a process.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
REFUSE = 3
PROBLEMS: list[str] = []


def say(ok: bool | None, message: str) -> None:
    label = {True: "  ok  ", False: " FAIL ", None: "  --  "}[ok]
    print(f"[{label}] {message}")
    if ok is False:
        PROBLEMS.append(message)


def digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def manifest() -> dict:
    return json.loads((HERE / "MANIFEST.json").read_text(encoding="utf-8"))


def repo_root(raw: str | None) -> Path:
    root = Path(raw).resolve() if raw else HERE.parents[4]
    missing = [p for p in ("src", "scripts", "config") if not (root / p).exists()]
    if missing:
        raise SystemExit(f"REFUSE: {root} is not a GTOS root; missing {missing}")
    return root


def check_file(root: Path, man: dict, *, stage: str) -> None:
    rec = man["files"][0]
    path = root / rec["repo_path"]
    got = digest(path)
    wanted = rec["sha256_before_expected" if stage in {"preflight", "rollback"}
                 else "sha256_after_carry"]
    if stage == "preflight" and got == rec["sha256_after_carry"]:
        say(None, f"{rec['repo_path']}: already carried at {got[:12]}")
        return
    say(got == wanted,
        f"{rec['repo_path']}: {got[:12] if got else 'ABSENT'} "
        f"({'==' if got == wanted else '!='} {stage} {wanted[:12]})")


def _load_packet_module(root: Path):
    path = root / "src/components/ultimate_book/execution_packets.py"
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location("gtos_cm_execution_packets_verify", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _params(ep, selection=()):
    sleeve = "crypto"
    sized = SimpleNamespace(cluster="book", sleeve_members=[sleeve], n_trades=1,
                            confidence=1.0, risk_pct_per_trade=0.005)
    intent = SimpleNamespace(sleeve=sleeve, symbol="BTCUSD", direction=1,
                             decision_day="2026-07-31", stop_dist=10.0, target_dist=40.0)
    geometry = {"entry_price": 3000.0, "risk_distance": 10.0,
                "stop_loss": 2990.0, "take_profit_1": 3040.0}
    account = {"current_equity": 100000.0, "balance": 100000.0,
               "account_login": 531325516,
               "day_start_equity_or_balance_baseline": 100000.0,
               "daily_reset_window_id": "2026-07-31"}
    return ep.build_book_trade_params(
        sized, intent, geometry, account,
        profile_namespace="operator_profile", frontier_exits=selection)


def check_behaviour(root: Path) -> None:
    print("\n== pure packet behaviour (no MT5, no broker, no runtime writes) ==")
    try:
        ep = _load_packet_module(root)
    except Exception as exc:  # noqa: BLE001
        say(False, f"execution_packets import failed: {exc!r}")
        return
    mx = "mx_btcusd_d1_donchian_20_breakout"
    crypto = "crypto"
    try:
        selected = ep.parse_frontier_exits(f"{mx},{crypto}")
        say(selected == (mx, crypto), f"combined FTMO selection parses exactly: {selected}")
        say("stop distance x1.5" in ep.describe_frontier_contract(crypto),
            f"launch banner names the width change: {ep.describe_frontier_contract(crypto)!r}")
        off = _params(ep)
        on = _params(ep, (crypto,))
    except Exception as exc:  # noqa: BLE001
        say(False, f"selected contract failed to construct: {exc!r}")
        return
    say(off["stop_loss"] == 2990.0 and off["take_profit_1"] == 3040.0,
        "default crypto path remains native SL 2990 / TP 3040")
    say(on["stop_loss"] == 2985.0 and on["take_profit_1"] == 3060.0,
        "selected crypto path is SL 2985 / TP 3060 (1.5R stop, target scaled at 4R)")
    risk = on["gtos_vnext_dynamic_target_stop_geometry_v4"]["stop_invalidation"]["risk_distance"]
    say(risk == 15.0, f"geometry contract carries scaled risk_distance={risk}")
    say(on["risk_pct_override"] == off["risk_pct_override"],
        f"risk percentage is unchanged at {on['risk_pct_override']}%; live sizing reduces lots")
    provenance = on["gtos_vnext_source_event_details"].get("exit_contract", {})
    say(provenance.get("frontier_cell") == "stop_1p5x_target_scale",
        f"placement provenance records {provenance.get('frontier_cell')!r}")
    say("exit_contract" not in off["gtos_vnext_source_event_details"],
        "default placement carries no frontier provenance")
    text = (root / "src/components/ultimate_book/execution_packets.py").read_text(encoding="utf-8")
    say("MetaTrader5" not in text and "order_send(" not in text,
        "carried module has no MT5 import and no order_send call")


def launcher_values(text: str, field: str) -> list[str]:
    # The funded fork keeps the per-book hashtables on one line; do not assume line layout.
    pat = re.compile(rf"(?i)(?<![A-Za-z0-9_]){re.escape(field)}\s*=\s*\"([^\"]*)\"")
    return pat.findall(text)


def check_launcher(root: Path, man: dict, *, stage: str) -> None:
    print(f"\n== launcher {stage}: semantic supervisor state ==")
    path = root / "scripts/run_book_supervisor.ps1"
    if not path.is_file():
        say(False, f"{path} is absent")
        return
    text = path.read_text(encoding="utf-8-sig")
    sel = man["selection"]
    tags = launcher_values(text, "tags")
    frontier = [v for v in launcher_values(text, "frontier") if v]
    expected_tags = sorted([sel["ftmo_tags_before_and_after"],
                            sel["redacted_account_tags_before_and_after"]])
    say(sorted(tags) == expected_tags,
        f"per-book tags are exact and unchanged: {tags}")
    wanted_frontier = (sel["ftmo_frontier_before"] if stage == "pre"
                       else sel["ftmo_frontier_after"])
    say(frontier == [wanted_frontier],
        f"only FTMO has a non-empty frontier selection: {frontier}")
    say("--frontier-exits" in text, "supervisor emits --frontier-exits only from its field")
    floor = sel["spread_geometry_floor_both_before_and_after"]
    say(floor in text and "--spread-geometry-floor" in text,
        "the already-armed spread floor remains present")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", required=True,
                    choices=("preflight", "postflight", "behaviour", "launcher-pre",
                             "launcher-post", "all", "rollback"))
    ap.add_argument("--repo-root", help="explicit reconstructed/host repo root")
    args = ap.parse_args()
    root = repo_root(args.repo_root)
    man = manifest()
    if args.check == "preflight":
        check_file(root, man, stage="preflight")
        check_launcher(root, man, stage="pre")
    elif args.check == "postflight":
        check_file(root, man, stage="postflight")
    elif args.check == "behaviour":
        check_behaviour(root)
    elif args.check == "launcher-pre":
        check_launcher(root, man, stage="pre")
    elif args.check == "launcher-post":
        check_launcher(root, man, stage="post")
    elif args.check == "rollback":
        check_file(root, man, stage="rollback")
        check_launcher(root, man, stage="pre")
    else:
        check_file(root, man, stage="postflight")
        check_behaviour(root)
        check_launcher(root, man, stage="post")
    print(f"\nRESULT: {'FAIL' if PROBLEMS else 'PASS'} ({len(PROBLEMS)} problem(s))")
    return 1 if PROBLEMS else 0


if __name__ == "__main__":
    raise SystemExit(main())
