#!/usr/bin/env python3
"""GOLIVE_vps — monitor-cycle runner (systemd/docker entrypoint).

Reads the per-account equity snapshot the runtime writes, runs the monitoring
cycle (DD watch + parity + alert routing), and prints/append the report. It uses
the deploy module's GovernorLimits as the single source of truth when importable.

This script makes NO broker calls. It is safe to run while halted (it will simply
report the halt/kill-switch state). Equity inputs come from a local JSON snapshot
the runtime maintains; if absent, it reports 'no_snapshot' and exits 0.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Make the route dir + monitoring importable regardless of CWD.
_HERE = Path(__file__).resolve()
_ROUTE = _HERE.parents[2]                 # the route operations dir
_MON = _ROUTE / "GOLIVE_vps_deploy" / "monitoring"
sys.path.insert(0, str(_MON))
sys.path.insert(0, str(_ROUTE))           # for ultimate_book_live_package

import monitor as M                        # noqa: E402
import kill_switch as K                    # noqa: E402

EQUITY_SNAPSHOT = "pipeline_state/{ns}/golive_equity_snapshot.json"


def _repo_root() -> Path:
    # deploy=0, GOLIVE_vps_deploy=1, route=2, operations=3, research=4, root=5
    return _HERE.parents[5]


def _load_limits():
    try:
        import ultimate_book_live_package as u  # noqa: PLC0415
        return u.DEFAULT_LIMITS
    except Exception:
        return None


def one_cycle(namespace: str) -> dict:
    root = _repo_root()
    ks = K.kill_switch_state(repo_root=root)
    if ks["kill_switch_engaged"]:
        rep = {"namespace": namespace, "kill_switch": ks, "action": "halted_no_monitor_trade_action"}
        M.send_alert("Kill-switch engaged", severity="info", detail=ks,
                     namespace=namespace, repo_root=root)
        return rep
    snap_path = root / EQUITY_SNAPSHOT.format(ns=namespace)
    if not snap_path.exists():
        return {"namespace": namespace, "status": "no_snapshot", "path": str(snap_path)}
    snap = json.loads(snap_path.read_text(encoding="utf-8"))
    return M.run_monitor_cycle(
        equity=float(snap["equity"]),
        day_start_balance=float(snap["day_start_balance"]),
        high_water=float(snap["high_water"]),
        namespace=namespace, limits=_load_limits(), repo_root=root)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--namespace", default="default", help="account namespace")
    ap.add_argument("--loop", type=int, default=0, help="seconds between cycles (0=once)")
    a = ap.parse_args()
    while True:
        rep = one_cycle(a.namespace)
        print(json.dumps(rep, sort_keys=True))
        if a.loop <= 0:
            break
        time.sleep(a.loop)


if __name__ == "__main__":
    main()
