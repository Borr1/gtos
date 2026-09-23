#!/usr/bin/env python3
"""Build Session CL's fail-closed, zero-mutation pass-surface ceremony package.

The economic receipts are the authority.  This builder deliberately refuses to emit an
activation package if either receipt approves anything: a non-empty decision needs a new
package with an actual supervisor diff, a decision-day plan and its own rollback payload.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
AUDIT = ROOT / "docs/audits/fable5-vision-audit-20260725"
PRICING = AUDIT / "phase17/receipts/CL_PASS_SURFACE_PRICING_V1.json"
INCUBATION = AUDIT / "phase17/receipts/CL_INCUBATION_PROPOSALS_V1.json"
RESTRICTED_CONFIGS = (
    ROOT / "config/agent_config.yaml",
    ROOT / "config/profiles/redacted_account.yaml",
)

FTMO_TAGS = [
    "crypto",
    "energy_agri",
    "sub_xvol_pullback",
    "sub_mid_dn_revert",
    "mx_btcusd_d1_donchian_20_breakout",
]
FN_TAGS = FTMO_TAGS[:-1]
SPREAD_FLOOR = ["sub_mid_dn_revert", "sub_xvol_pullback"]
FRONTIER = ["mx_btcusd_d1_donchian_20_breakout"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def main() -> int:
    pricing = json.loads(PRICING.read_text(encoding="utf-8"))
    incubation = json.loads(INCUBATION.read_text(encoding="utf-8"))
    direct = pricing.get("approved_direct_additions")
    ready = incubation.get("approved_for_arming_now")
    if direct != {"FTMO": [], "redacted_account": []}:
        raise SystemExit(f"REFUSED: pricing receipt has non-empty direct approvals: {direct!r}")
    if ready != []:
        raise SystemExit(f"REFUSED: incubation receipt has ceremony-ready proposals: {ready!r}")

    accounts = {
        "FTMO": {
            "namespace": "operator_profile",
            "profile": "operator_profile",
            "tags": FTMO_TAGS,
            "frontier_exits": FRONTIER,
            "spread_geometry_floor": SPREAD_FLOOR,
            "decision_timeframes_derived": [16388, 16408],
            "token_config_digest_prefix": "ffe16657feaf",
        },
        "redacted_account": {
            "namespace": "redacted_account_live_bee34003",
            "profile": "redacted_account",
            "tags": FN_TAGS,
            "frontier_exits": [],
            "spread_geometry_floor": SPREAD_FLOOR,
            "decision_timeframes_derived": [16388],
            "token_config_digest_prefix": "e184a81d3b1b",
        },
    }
    approved = {
        "schema": "gtos.phase17.cl.pass_surface_approved_set.v1",
        "session": "CL",
        "blocks": "B2680-B2689",
        "decision": "STOP_AFTER_PREFLIGHT_NO_MUTATION",
        "arms_nothing": True,
        "approved_direct_additions": direct,
        "incubation_ready_for_live_arming": ready,
        "proposal_ids_not_ready": [p["incubant_id"] for p in incubation["proposals"]],
        "reason": (
            "No direct extension clears the evidence gates and neither bounded incubation "
            "proposal clears its pre-registered live vetoes. The current armed set is the "
            "only approved set."
        ),
        "accounts_before": accounts,
        "accounts_after": accounts,
        "supervisor_edit": {
            "file_byte_delta": [],
            "hashtable_key_delta": [],
            "argument_delta": [],
            "firing_ledger_action": "NONE",
            "restart_action": "NONE",
            "timeframe_argument_note": (
                "There is no --timeframes CLI flag. BookLauncher derives the exact lists "
                "above from --tags; the startup tfs line is the independent proof."
            ),
            "host_hashtable_keys": (
                "CAPTURE_FROM_ACTUAL_HOST_BYTES; all keys and their source block must be "
                "byte-identical pre/post because this package has an empty diff."
            ),
        },
        "host_baseline_receipt": {
            "branch": "vps/ultimate-conditioned-expansion-minimal-2026-06-18",
            "head_prefix": "267cccc94",
            "supervisor_sha256_prefix": "63079cec",
            "authority": rel(AUDIT / "phase15/receipts/SPREAD_FLOOR_ARMED_20260731.md"),
            "limitation": (
                "Only prefixes were committed. HOST_PREFLIGHT.json supplies the full current "
                "values; a prefix mismatch is a hard stop, never an overwrite instruction."
            ),
        },
    }
    dump(HERE / "APPROVED_SET.json", approved)

    diff = "# Session CL supervisor-argument diff — exact no-op\n\n"
    diff += "Decision: **STOP AFTER PREFLIGHT; MUTATE NOTHING.** The exact file-byte, "
    diff += "hashtable-key and worker-argument diffs are all the empty set.\n\n"
    diff += "| account | hashtable-key delta | `--tags` before → after | `--frontier-exits` before → after | `--spread-geometry-floor` before → after | derived `tfs` before → after |\n"
    diff += "|---|---|---|---|---|---|\n"
    for name in ("FTMO", "redacted_account"):
        a = accounts[name]
        tags = ",".join(a["tags"])
        frontier = ",".join(a["frontier_exits"]) or "ABSENT"
        floor = ",".join(a["spread_geometry_floor"])
        tfs = str(a["decision_timeframes_derived"])
        diff += f"| {name} | `∅` | `{tags}` → same | `{frontier}` → same | `{floor}` → same | `{tfs}` → same |\n"
    diff += """\nThe host supervisor is a fork whose full current bytes and spread-floor field name were not
committed back to this repository. `capture_host_preflight.ps1` therefore records the actual
`$books` block, its hash and every hashtable key from those bytes. Because the authorized diff
is empty, exactness does not depend on guessing the field name: the full block must compare
byte-for-byte equal in preflight and postflight. The live worker command lines remain the
behavioural authority and are checked against the selections above.

An empty `--tags` is not an empty book; it selects all built sleeves. An all-typo non-empty
selection is a mute book. `verify_pass_surface.py` refuses both by requiring the exact,
non-empty strings and their independent `BookLauncher starting: tfs=...` lines.
"""
    (HERE / "SUPERVISOR_ARGS_DIFF.md").write_text(diff, encoding="utf-8")

    package_paths = [
        HERE / "APPROVED_SET.json",
        HERE / "SUPERVISOR_ARGS_DIFF.md",
        HERE / "PASS_SURFACE_CEREMONY.md",
        HERE / "capture_host_preflight.ps1",
        HERE / "verify_pass_surface.py",
        HERE / "build_package.py",
    ]
    manifest = {
        "schema": "gtos.phase17.cl.pass_surface_ceremony_manifest.v1",
        "session": "CL",
        "blocks": "B2680-B2689",
        "purpose": (
            "Fail closed on the measured no-addition decision. Verify the exact live baseline "
            "and prove zero mutation; carry no source, config or supervisor payload."
        ),
        "decision": "STOP_AFTER_PREFLIGHT_NO_MUTATION",
        "arms_nothing": True,
        "payload_files": [],
        "copy_order": [],
        "authority_inputs": {
            rel(PRICING): sha256(PRICING),
            rel(INCUBATION): sha256(INCUBATION),
        },
        "restricted_config_worktree_guard": {
            rel(p): sha256(p) for p in RESTRICTED_CONFIGS
        },
        "token_config_digest_prefixes": {
            "FTMO": "ffe16657feaf",
            "redacted_account": "e184a81d3b1b",
        },
        "known_host_baseline": {
            "branch": "vps/ultimate-conditioned-expansion-minimal-2026-06-18",
            "head_prefix": "267cccc94",
            "supervisor_sha256_prefix": "63079cec",
            "full_values": "MUST_BE_CAPTURED_FROM_HOST; not present in the committed receipt",
        },
        "package_files": {rel(p): sha256(p) for p in package_paths},
        "explicitly_forbidden_actions": [
            "edit either token-bound config",
            "edit or replace scripts/run_book_supervisor.ps1",
            "clear firing_sleeves.json",
            "hold or release kill flags",
            "stop or restart any process or scheduled task",
            "copy runtime payloads",
            "inspect or modify activation-token contents",
        ],
    }
    dump(HERE / "MANIFEST.json", manifest)
    print(f"wrote {HERE / 'APPROVED_SET.json'}")
    print(f"wrote {HERE / 'SUPERVISOR_ARGS_DIFF.md'}")
    print(f"wrote {HERE / 'MANIFEST.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
