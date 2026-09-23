"""GOLIVE_vps — KILL-SWITCH (halt file + size_cap=0). Default safe.

Two independent, redundant stop mechanisms — either alone flattens new entries:

  1. HALT FILE   — writes the repo's physical halt flag (the same flag
                   ``src/safety/runtime_halt.py`` reads). This is the PRIMARY,
                   process-independent control: once written, every runtime that
                   honours the halt guard refuses new order intents / order_send.
  2. SIZE CAP 0  — writes a ``size_cap_override`` sidecar that the deploy module's
                   governor reads as ``operator_circuit_breaker=True`` ->
                   ``size_cap_multiplier=0`` (``evaluate_governor`` returns
                   allow_new_entries=False). A second belt-and-braces stop wired
                   into the sizing path itself.

This module ONLY writes/reads local files. It performs NO broker / order / position
work. Engaging the kill-switch is always safe; disengaging requires explicit owner
intent and is audited.

Halt flag content/format mirrors the existing pipeline_state/*.flag files.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Mirror src/safety/runtime_halt.DEFAULT_HALT_FLAG_PATHS
HARD_HALT_FLAG = "pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag"
RESEARCH_HALT_FLAG = "pipeline_state/RESEARCH_RUNTIME_HALT.flag"
SIZE_CAP_SIDECAR = "pipeline_state/GTOS_OPERATOR_SIZE_CAP_OVERRIDE.json"
KILL_AUDIT_LOG = "pipeline_state/operator_kill_switch_audit.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_root(repo_root: Optional[str | Path]) -> Path:
    if repo_root:
        return Path(repo_root)
    # this file: <root>/research/operations/<route>/GOLIVE_vps_deploy/monitoring/
    # monitoring=0, GOLIVE_vps_deploy=1, route=2, operations=3, research=4, root=5
    return Path(__file__).resolve().parents[5]


def _audit(action: str, detail: dict[str, Any], repo_root: Optional[str | Path]) -> None:
    root = _repo_root(repo_root)
    path = root / KILL_AUDIT_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"recorded_at_utc": _now(), "action": action, "detail": detail,
           "boundary": "local_repo_files_only_no_broker_account_order"}
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def engage_kill_switch(*, reason: str, operator: str = "owner",
                       repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    """Engage BOTH stops: write the hard halt flag AND the size_cap=0 sidecar."""
    root = _repo_root(repo_root)
    halt = root / HARD_HALT_FLAG
    halt.parent.mkdir(parents=True, exist_ok=True)
    halt.write_text(
        "GTOS HARD PRODUCTION HALT\n"
        f"created_utc={_now()}\n"
        f"reason={reason}\n"
        f"operator={operator}\n"
        "source=operator_kill_switch\n",
        encoding="utf-8",
    )
    sidecar = root / SIZE_CAP_SIDECAR
    sidecar.write_text(json.dumps({
        "size_cap_override": 0.0,
        "operator_circuit_breaker": True,
        "engaged_at_utc": _now(),
        "reason": reason,
        "operator": operator,
    }, indent=2), encoding="utf-8")
    detail = {"halt_flag": str(halt), "size_cap_sidecar": str(sidecar),
              "size_cap_override": 0.0, "reason": reason}
    _audit("engage", detail, repo_root)
    return {"status": "kill_switch_engaged", **detail}


def disengage_kill_switch(*, approval_token: str, operator: str = "owner",
                          repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    """Disengage the size-cap sidecar (sets override back to 1.0). Does NOT remove
    the hard halt flag — flag removal is a deliberate, separate owner action so the
    physical halt control is never silently cleared by a script.

    ``approval_token`` must be the non-empty owner-supplied token; without it this
    refuses (fail-closed)."""
    if not approval_token or approval_token == "PLACEHOLDER":
        raise PermissionError("disengage requires an explicit owner approval_token")
    root = _repo_root(repo_root)
    sidecar = root / SIZE_CAP_SIDECAR
    sidecar.write_text(json.dumps({
        "size_cap_override": 1.0,
        "operator_circuit_breaker": False,
        "disengaged_at_utc": _now(),
        "operator": operator,
        "approval_token_present": True,
    }, indent=2), encoding="utf-8")
    halt_present = (root / HARD_HALT_FLAG).exists()
    detail = {"size_cap_sidecar": str(sidecar), "size_cap_override": 1.0,
              "hard_halt_flag_still_present": halt_present,
              "note": "halt flag NOT auto-removed; remove manually to fully clear"}
    _audit("disengage", detail, repo_root)
    return {"status": "size_cap_restored", **detail}


def kill_switch_state(repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    """Read-only: report whether either stop is engaged. Fail-closed default."""
    root = _repo_root(repo_root)
    hard = (root / HARD_HALT_FLAG).exists()
    research = (root / RESEARCH_HALT_FLAG).exists()
    sidecar_path = root / SIZE_CAP_SIDECAR
    size_cap = 1.0
    cb = False
    if sidecar_path.exists():
        try:
            data = json.loads(sidecar_path.read_text(encoding="utf-8"))
            size_cap = float(data.get("size_cap_override", 1.0))
            cb = bool(data.get("operator_circuit_breaker", False))
        except (ValueError, OSError):
            # unreadable sidecar -> fail closed
            size_cap, cb = 0.0, True
    engaged = bool(hard or research or cb or size_cap == 0.0)
    return {
        "kill_switch_engaged": engaged,
        "hard_halt_flag": hard,
        "research_halt_flag": research,
        "operator_circuit_breaker": cb,
        "size_cap_override": size_cap,
        "new_entries_allowed": (not engaged),
        "checked_at_utc": _now(),
        "boundary": "local_repo_files_only",
    }


def load_size_cap_override(repo_root: Optional[str | Path] = None) -> float:
    """Helper the runtime calls to fold the operator sidecar into the governor.
    Returns the size_cap multiplier (0.0 = flatten new entries). Fail-closed."""
    return float(kill_switch_state(repo_root)["size_cap_override"])


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="GTOS operator kill-switch")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("engage"); e.add_argument("--reason", required=True)
    e.add_argument("--operator", default="owner")
    d = sub.add_parser("disengage"); d.add_argument("--approval-token", required=True)
    d.add_argument("--operator", default="owner")
    sub.add_parser("state")
    a = ap.parse_args()
    if a.cmd == "engage":
        print(json.dumps(engage_kill_switch(reason=a.reason, operator=a.operator), indent=2))
    elif a.cmd == "disengage":
        print(json.dumps(disengage_kill_switch(approval_token=a.approval_token, operator=a.operator), indent=2))
    else:
        print(json.dumps(kill_switch_state(), indent=2))
