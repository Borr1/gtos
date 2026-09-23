#!/usr/bin/env python3
"""Build Session CN's CE-style, VPS-lineage live-cost carry without touching the VPS.

The live host is not mainline.  Existing files therefore start from the last committed host
bytes and receive only anchored CN changes.  New cost-layer files are copied byte-for-byte from
mainline.  ``--check`` rebuilds everything in memory and refuses stale package bytes.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
FILES = HERE / "files"
DIFFS = HERE / "diffs"
MANIFEST = HERE / "MANIFEST.json"
LINEAGE = "redacted_host87668c5d503b52925d10be7dfb66540"
AUDIT = "docs/audits/fable5-vision-audit-20260725"

ENGINE_PATH = "src/components/broker_net_cost_engine.py"
ECON_PATH = "src/components/ultimate_book/packet_economics.py"
OWNER_PATH = "src/components/ultimate_book/book_owner.py"
TRUTH_PATH = (
    "research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json"
)
SEAL_PATH = (
    "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "B7_5_POST_ACCELERATION_EXECUTION_SEAL.json"
)
R2_PATH = (
    "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json"
)

HOST_BASES = {
    ENGINE_PATH: ("git", LINEAGE),
    ECON_PATH: (
        "file",
        f"{AUDIT}/phase4/packet_carry/files/packet_economics.py",
    ),
    OWNER_PATH: (
        # Recomposed at wave-17 integration (2026-08-01), per this ceremony's own §1:
        # Session CO's package also carries book_owner.py, so CN's two anchored owner
        # additions are rebuilt on CO's after-bytes (CE spread-floor lineage + CO lane
        # weights) instead of the raw CE bytes. Never last-copy-wins. The pre-recompose
        # base was phase15/activation_carry_spread_floor/files/book_owner.py.
        "file",
        f"{AUDIT}/phase17/lane_weights_ceremony/files/book_owner.py",
    ),
}

NEW_FILES = (
    "src/costs/coverage.py",
    TRUTH_PATH,
    "src/costs/model.py",
    "src/costs/__init__.py",
)

#: The mainline revision the NEW_FILES copies were taken from.
#:
#: These were read from the WORKING TREE, while every `HOST_BASES` entry is pinned to
#: `LINEAGE` or to a committed file. The asymmetry made this package's `--check` a question
#: about today's mainline rather than about the package: wave 21 legitimately rewrote
#: `src/costs/model.py` and `src/costs/__init__.py` (`7d6bbca7a`, `e4fa4ca6f`, `e59bf1b10`,
#: `ef8533e1c`) and `--check` then reported STALE_OR_MISSING for a carry that had already
#: been EXECUTED on both books on 2026-08-06. Rebuilding it against current mainline would
#: have silently redefined what CN carried, which is worse than the red test.
#:
#: `870d4cb53` is the revision that reproduces EVERY value the committed MANIFEST.json
#: records from a working tree — all three payload copies byte-for-byte, both `not_carried`
#: config hashes, and `seal_exposure.mainline_sha256_after_CN` at CN's own after-bytes
#: (`f599f25f…`). Found by searching history for the commit that satisfies all six at once,
#: not by assuming one. A carry package describes one moment; pin it like the host bases
#: already are.
NEW_FILES_REVISION = "870d4cb535ed225faa587b9823ca9c28320dcdd2"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_show(revision: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def host_bytes(path: str) -> bytes:
    kind, source = HOST_BASES[path]
    if kind == "git":
        return git_show(source, path)
    return (REPO / source).read_bytes()


def replace_once(text: str, old: str, new: str, *, what: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"ANCHOR_NOT_UNIQUE:{what}:matches={count}")
    return text.replace(old, new)


def between(text: str, start: str, end: str, *, what: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise SystemExit(f"EXTRACTION_ANCHOR_NOT_UNIQUE:{what}")
    start_at = text.index(start)
    end_at = text.index(end, start_at)
    return text[start_at:end_at]


def assert_python(path: str, data: bytes) -> None:
    ast.parse(data.decode("utf-8"), filename=path)


def build_engine() -> bytes:
    """Apply the CN commission term to the VPS engine while preserving its swap-source guard."""
    base = host_bytes(ENGINE_PATH).decode("utf-8")
    current = (REPO / ENGINE_PATH).read_text()

    base = replace_once(
        base,
        "from src.utils.broker_profile import broker_account_namespace, sanitize_namespace\n",
        "from src.costs.model import commission_usd_per_lot_for_packet\n"
        "from src.utils.broker_profile import broker_account_namespace, sanitize_namespace\n",
        what="engine model import",
    )
    constants = between(
        current,
        'BROKER_TRUE_COMMISSION_MODE = "broker_true_commission_default_v1"\n',
        "DEFAULT_ALLOWED_COMMISSION_STATUSES = {\n",
        what="engine commission constants",
    )
    base = replace_once(
        base,
        'PRETRADE_COST_PACKET_SCHEMA_VERSION = "gtos_v4_pretrade_broker_net_cost_packet_v1"\n',
        'PRETRADE_COST_PACKET_SCHEMA_VERSION = "gtos_v4_pretrade_broker_net_cost_packet_v1"\n'
        + constants,
        what="engine constants",
    )
    commission_function = between(
        current,
        "def _commission_cost_packet(\n",
        "def build_pretrade_cost_packet(\n",
        what="engine commission function",
    )
    base = replace_once(
        base,
        "def build_pretrade_cost_packet(\n",
        commission_function + "def build_pretrade_cost_packet(\n",
        what="engine commission function insertion",
    )
    base = replace_once(
        base,
        "    asof_utc: str | None = None,\n) -> dict[str, Any]:\n",
        "    asof_utc: str | None = None,\n"
        "    commission_mode: str = BROKER_TRUE_COMMISSION_MODE,\n"
        ") -> dict[str, Any]:\n",
        what="engine explicit comparator argument",
    )
    swap_call = """    swap_cost = _swap_cost_packet(
        runtime_cfg=runtime_cfg,
        trade_params=trade_params,
        spec=spec,
        swap_value=swap_value,
        entry_price=entry_price,
        sl_distance=sl_distance,
    )
"""
    commission_call = """    commission_cost = _commission_cost_packet(
        mode=commission_mode,
        profile=profile,
        broker_symbol=clean_broker_symbol,
        entry_price=entry_price,
        sl_distance=sl_distance,
        spec=spec,
    )
"""
    base = replace_once(
        base,
        swap_call,
        swap_call + commission_call,
        what="engine commission calculation",
    )
    old_total = """    total_cost_r = None
    if tick_cost["spread_r"] is not None:
        total_cost_r = (
            float(tick_cost["spread_r"])
            + float(expected_slippage_r or 0.0)
            + float(swap_cost.get("cost_r") or 0.0)
        )
"""
    new_total = """    total_cost_r = None
    commission_r = _as_float(commission_cost.get("cost_r"))
    commission_term_ready = (
        commission_mode == LEGACY_ZERO_COMMISSION_COMPARATOR_MODE
        or commission_r is not None
    )
    if tick_cost["spread_r"] is not None and commission_term_ready:
        total_cost_r = (
            float(tick_cost["spread_r"])
            + float(expected_slippage_r or 0.0)
            + float(swap_cost.get("cost_r") or 0.0)
            + float(commission_r or 0.0)
        )
"""
    base = replace_once(base, old_total, new_total, what="engine four-term total")
    base = replace_once(
        base,
        '        "model_version": "vnext_selected_cell_pretrade_cost_model_v2",\n',
        '        "model_version": "vnext_selected_cell_pretrade_cost_model_v3",\n'
        '        "authority": "broker_calibrated_replay_cost",\n'
        '        "cost_authority": "broker_calibrated_replay_cost",\n',
        what="engine v3 model stamp",
    )
    allowed_anchor = '        "allowed_commission_model_statuses": sorted(allowed_commission_statuses),\n'
    commission_fields = """        "commission_cost": commission_cost,
        "commission_r": commission_r,
        "commission_cost_model_required": (
            required and commission_mode == BROKER_TRUE_COMMISSION_MODE
        ),
        "commission_cost_authority": "broker_true_costs_v1",
        "commission_cost_provenance": commission_cost.get("provenance"),
        "commission_mode": commission_mode,
"""
    base = replace_once(
        base,
        allowed_anchor,
        allowed_anchor + commission_fields,
        what="engine commission packet provenance",
    )
    old_components = """        "total_cost_components": {
            "spread_r": tick_cost["spread_r"],
            "expected_slippage_r": expected_slippage_r,
            "swap_cost_r": swap_cost.get("cost_r"),
        },
"""
    new_components = """        "total_cost_components": {
            "spread_r": tick_cost["spread_r"],
            "expected_slippage_r": expected_slippage_r,
            "swap_cost_r": swap_cost.get("cost_r"),
            "commission_r": commission_r,
        },
        "total_cost_components_expected": list(TOTAL_COST_COMPONENTS),
        "cost_excludes": (
            ["commission"]
            if commission_mode == LEGACY_ZERO_COMMISSION_COMPARATOR_MODE
            else []
        ),
"""
    base = replace_once(
        base,
        old_components,
        new_components,
        what="engine total component declaration",
    )
    refusal_block = between(
        current,
        '    if packet.get("commission_cost_model_required"):\n',
        '    if requirements.get("profile_namespace_required")',
        what="engine commission refusal",
    )
    base = replace_once(
        base,
        '    if requirements.get("profile_namespace_required")',
        refusal_block + '    if requirements.get("profile_namespace_required")',
        what="engine fail-closed commission refusal",
    )
    data = base.encode("utf-8")
    assert_python(ENGINE_PATH, data)
    return data


def build_owner() -> bytes:
    """Add only the scalar cost projection to CE's current host owner bytes."""
    base = host_bytes(OWNER_PATH).decode("utf-8")
    current = (REPO / OWNER_PATH).read_text()
    base = replace_once(
        base,
        "from .packet_economics import build_economics_block\n",
        "from .packet_economics import (\n"
        "    LEGACY_MODELLED_COST_COMPONENTS,\n"
        "    LEGACY_MODELLED_COST_EXCLUDES,\n"
        "    MODELLED_COST_COMPONENTS,\n"
        "    MODELLED_COST_EXCLUDES,\n"
        "    build_economics_block,\n"
        ")\n",
        what="owner packet-economics imports",
    )
    method = between(
        current,
        "    @staticmethod\n    def _runtime_learning_modelled_cost",
        "    @staticmethod\n    def _runtime_learning_trade_context",
        what="owner modelled-cost method",
    )
    base = replace_once(
        base,
        "    @staticmethod\n    def _runtime_learning_trade_context",
        method + "    @staticmethod\n    def _runtime_learning_trade_context",
        what="owner modelled-cost method insertion",
    )
    policy_anchor = (
        "        ctx.update(UltimateBookOwner._runtime_learning_policy_clock_context(policy_clock))\n"
    )
    base = replace_once(
        base,
        policy_anchor,
        "        ctx.update(UltimateBookOwner._runtime_learning_modelled_cost(tp))\n"
        + policy_anchor,
        what="owner modelled-cost emission",
    )
    data = base.encode("utf-8")
    assert_python(OWNER_PATH, data)
    return data


def build_payloads() -> dict[str, bytes]:
    payloads = {path: git_show(NEW_FILES_REVISION, path) for path in NEW_FILES}
    payloads[ECON_PATH] = (REPO / ECON_PATH).read_bytes()
    payloads[OWNER_PATH] = build_owner()
    payloads[ENGINE_PATH] = build_engine()
    assert_python(ECON_PATH, payloads[ECON_PATH])
    return payloads


def payload_basename(path: str) -> str:
    if path == "src/costs/__init__.py":
        return "costs___init__.py"
    return Path(path).name


def diff_basename(path: str) -> str:
    return path.replace("/", "_") + ".diff"


def unified(before: bytes, after: bytes, path: str) -> str:
    lines = difflib.unified_diff(
        before.decode("utf-8").splitlines(keepends=True),
        after.decode("utf-8").splitlines(keepends=True),
        fromfile=f"a/{path} (host before CN)",
        tofile=f"b/{path} (host after CN)",
        n=5,
    )
    # A nested unified diff represents a blank context row as one space, which
    # an outer ``git diff --check`` correctly sees as trailing whitespace.  The
    # exact/applicable bytes live in ``files/``; this is the human audit view.
    return "".join("\n" if not line.strip() else line for line in lines)


def file_record(path: str, data: bytes, copy_order: int) -> dict:
    new = path in NEW_FILES
    rec = {
        "copy_order": copy_order,
        "stage": "A",
        "repo_path": path,
        "destination_on_vps": path.replace("/", "\\"),
        "payload_basename": payload_basename(path),
        "source_in_this_repo": (
            f"{AUDIT}/phase17/activation_carry_live_cost_truth/files/{payload_basename(path)}"
        ),
        "is_new_file_on_vps": new,
        "sha256_before_expected": None if new else sha(host_bytes(path)),
        "bytes_before": 0 if new else len(host_bytes(path)),
        "sha256_after_carry": sha(data),
        "bytes_after": len(data),
        "crlf_present": b"\r\n" in data,
    }
    if not new:
        rec["diff_in_this_repo"] = (
            f"{AUDIT}/phase17/activation_carry_live_cost_truth/diffs/{diff_basename(path)}"
        )
    provenance = {
        ENGINE_PATH: (
            "VPS lineage redacted_host; no committed carry through CE owns this path. CN's variant "
            "preserves the lineage-only live-symbol-info swap-source guard."
        ),
        ECON_PATH: (
            "Session S packet carry after-bytes cc8353ec4a12, already applied and verified on "
            "the host; no later committed carry owns this path."
        ),
        OWNER_PATH: (
            "Session CE spread-floor carry after-bytes b7a82dc3d241, the latest committed host "
            "state; CN adds only modelled-cost scalar emission."
        ),
    }
    rec["host_bytes_provenance"] = (
        "ABSENT from lineage redacted_host and every committed carry through Session CE."
        if new
        else provenance[path]
    )
    rec["source_kind"] = (
        "mainline byte-identical new dependency"
        if new
        else "mainline byte-identical"
        if path == ECON_PATH
        else "committed host bytes + anchored CN edits"
    )
    return rec


def build_manifest(payloads: dict[str, bytes]) -> dict:
    order = (
        "src/costs/coverage.py",
        TRUTH_PATH,
        "src/costs/model.py",
        "src/costs/__init__.py",
        ECON_PATH,
        OWNER_PATH,
        ENGINE_PATH,
    )
    seal_doc = json.loads((REPO / SEAL_PATH).read_text())
    return {
        "schema": "gtos.phase17.activation_carry_live_cost_truth_manifest.v1",
        "session": "CN",
        "blocks": "B2750-B2799",
        "built_by": f"{AUDIT}/phase17/activation_carry_live_cost_truth/build_carry.py",
        "purpose": (
            "Charge account/symbol broker-true round-turn commission in the default live "
            "pretrade cost packet and preserve the explicit zero-commission behavior only as "
            "an offline comparator; emit additive v3 provenance while keeping v2 rows readable."
        ),
        "vps_base_ref": "origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18",
        "vps_base_commit": LINEAGE,
        "host_repo_root": r"C:\Users\MSI\Documents\ai-trading-agent",
        "host_interpreter": r"C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe",
        "host_branch_head_at_build_time": (
            "d6c9c4b19 plus Session CE carry evidence; preflight is authoritative and any "
            "unrecognised host byte is a STOP"
        ),
        "arms_nothing_new": True,
        "changes_existing_armed_decisions": True,
        "activation_boundary": (
            "The last file, broker_net_cost_engine.py, makes broker-true commission default-on "
            "for every already-required vnext cost packet. All prerequisites land first."
        ),
        "composes_with": {
            "session_CE_spread_floor": (
                f"{AUDIT}/phase15/activation_carry_spread_floor/MANIFEST.json"
            ),
            "session_CL_pass_surface": (
                "same orchestrator ceremony wave; run CN preflight again after CL and refuse on "
                "any shared-path drift"
            ),
            "session_CM_armed_fidelity": (
                "same orchestrator ceremony wave; run CN preflight again after CM and refuse on "
                "any shared-path drift"
            ),
            "shared_path_rule": (
                "CN does not carry run_book.py or the supervisor. It does carry book_owner.py; "
                "if CL or CM also changes that path, do not overwrite either package. Rebuild CN's "
                "anchored owner edit on the ceremony's resolved post-CL/CM owner bytes and rerun "
                "all CN checks."
            ),
        },
        "not_carried": [
            {
                "repo_path": "config/agent_config.yaml",
                "sha256_unchanged": sha(git_show(NEW_FILES_REVISION, "config/agent_config.yaml")),
                "reason": "Activation-token-bound and no commission config knob is needed.",
            },
            {
                "repo_path": "config/profiles/operator_profile.yaml",
                "sha256_unchanged": sha(
                    git_show(NEW_FILES_REVISION, "config/profiles/operator_profile.yaml")
                ),
                "reason": "Read-only live profile; commission truth resolves by namespace/server.",
            },
            {
                "repo_path": "config/profiles/redacted_account.yaml",
                "sha256_unchanged": sha(
                    git_show(NEW_FILES_REVISION, "config/profiles/redacted_account.yaml")
                ),
                "reason": "Activation-token-bound and explicitly forbidden to edit.",
            },
        ],
        "seal_exposure": {
            "changed_R2_bound_path": ENGINE_PATH,
            "R2_contract": R2_PATH,
            "R2_expected_sha256_before_CN": (
                "eb4ec5173ce28d4b2f6631fbe2e912a1dc5e20d392cd2a2517627d2cc2ab40d0"
            ),
            "mainline_sha256_after_CN": sha(git_show(NEW_FILES_REVISION, ENGINE_PATH)),
            "frozen_execution_seal_path": SEAL_PATH,
            "frozen_execution_seal_file_sha256_unchanged": sha((REPO / SEAL_PATH).read_bytes()),
            "frozen_execution_seal_root_sha256_unchanged": seal_doc[
                "execution_seal_root_sha256"
            ],
            "frozen_shared_execution_contract_digests_unchanged": {
                arm: row["shared_execution_contract_digest_sha256"]
                for arm, row in seal_doc["arms"].items()
            },
            "consequence": (
                "Future R2 replay use must regenerate authority and re-run affected windows. The "
                "frozen engine seal and accepted historical artifacts are untouched history."
            ),
        },
        "copy_order_rule": (
            "1-4 install the new cost layer and artifact; 5 installs the backward-compatible "
            "reader; 6 installs additive provenance emission; 7 activates broker-true commission."
        ),
        "files": [file_record(path, payloads[path], i + 1) for i, path in enumerate(order)],
        "proving_log_line": {
            "packet_outcome": "unit_placed",
            "required_fields": {
                "modelled_cost_model_version": "vnext_selected_cell_pretrade_cost_model_v3",
                "modelled_commission_mode": "broker_true_commission_default_v1",
                "modelled_commission_cost_source_status": "captured",
                "modelled_commission_cost_artifact": "BROKER_TRUE_COSTS_V1.json",
                "modelled_cost_excludes": [],
            },
            "numeric_required": [
                "modelled_cost_components.commission_r",
                "modelled_cost_r",
            ],
            "rule": (
                "The first post-restart placed packet on each namespace must carry these values. "
                "A v2 packet, comparator mode, source_gap, missing commission_r, or non-empty "
                "exclusion list is a STOP and rollback condition."
            ),
        },
        "stop_conditions": [
            "Any preflight hash is neither the recorded before-byte nor this carry's after-byte.",
            "Any dependency/order/import/behaviour verifier check fails.",
            "Either namespace fails to restart cleanly or the first placed packet lacks v3 captured commission provenance.",
            "A required broker-true schedule or cash-to-R geometry is missing: fail closed; do not substitute zero.",
            "Any config or activation-token digest differs from the ceremony's pre-copy capture.",
        ],
        "rollback": {
            "method": (
                "Stop both workers through the orchestrator's established service ceremony; restore "
                "all three existing files from the exact preflight backups; remove only the four "
                "new paths if their preflight state was ABSENT; verify rollback hashes; restart and "
                "prove both namespaces."
            ),
            "existing_paths": [ECON_PATH, OWNER_PATH, ENGINE_PATH],
            "new_paths_remove_only_if_preflight_absent": list(NEW_FILES),
            "config_rollback": "none -- no config byte moves",
        },
    }


def expected_outputs() -> dict[Path, bytes]:
    payloads = build_payloads()
    outputs: dict[Path, bytes] = {}
    for path, data in payloads.items():
        outputs[FILES / payload_basename(path)] = data
        if path in HOST_BASES:
            outputs[DIFFS / diff_basename(path)] = unified(
                host_bytes(path), data, path
            ).encode("utf-8")
    outputs[MANIFEST] = (
        json.dumps(build_manifest(payloads), indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = expected_outputs()
    if args.check:
        stale = [
            str(path.relative_to(REPO))
            for path, expected in outputs.items()
            if not path.is_file() or path.read_bytes() != expected
        ]
        if stale:
            raise SystemExit("STALE_OR_MISSING:\n" + "\n".join(stale))
        print(f"PASS carry package reproducible: {len(outputs)} files")
        return 0
    for path, data in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print(f"wrote carry package: {len(outputs)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
