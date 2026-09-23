#!/usr/bin/env python3
"""Rebuild Session CO's payloads from the last host-proven carried bytes.

The VPS tree is a composed carry lineage, not mainline.  Copying current
``book_engine.py``/``book_owner.py``/``run_book.py`` would import years of unrelated
surface.  This builder applies only CO's anchored edits to the exact files proven live by
the 2026-07-31 spread-floor ceremony, and to Session S's still-current packet file.

It never imports run_book, MT5, or a broker adapter.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
AUDIT = REPO / "docs/audits/fable5-vision-audit-20260725"
CE = AUDIT / "phase15/activation_carry_spread_floor/files"
S = AUDIT / "phase4/packet_carry/files"
FILES = HERE / "files"
DIFFS = HERE / "diffs"

BASES = {
    "src/components/ultimate_book/runtime_learning_packet.py": (
        S / "runtime_learning_packet.py",
        "1941472b4eac6e0b88f25e60d7a90c455c7e1999e94ef4a600fb3d949f3e025b",
    ),
    "src/components/ultimate_book/book_engine.py": (
        CE / "book_engine.py",
        "42c1bd6c78f3eb1f160aae096c3a635c27002fa3124149d3715439424a4e33f5",
    ),
    "src/components/ultimate_book/book_owner.py": (
        CE / "book_owner.py",
        "b7a82dc3d241eaca09f9a430c66ec9f67705c0013554ade6409ddacc663a4cec",
    ),
    "run_book.py": (
        CE / "run_book.py",
        "39ddfd513d976d966611d2af7f2a388f4701cd98c8c1ba55de7ecc6220cf2419",
    ),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def section(text: str, start: str, end: str) -> str:
    left = text.index(start)
    right = text.index(end, left)
    return text[left:right].rstrip()


def patch_packet(base: str) -> str:
    current = (REPO / "src/components/ultimate_book/runtime_learning_packet.py").read_text()
    helper = section(current, "def _lane_weight_packet_fields(", "def _hashable_ticket_key(")
    update = section(current, "    packet.update(\n        _lane_weight_packet_fields(", "    # Attached only")
    out = replace_once(
        base,
        "\n\ndef _hashable_ticket_key(lk: str) -> str | None:",
        f"\n\n{helper}\n\ndef _hashable_ticket_key(lk: str) -> str | None:",
        "packet helper",
    )
    return replace_once(
        out,
        "    # Attached only when populated.",
        f"{update}\n    # Attached only when populated.",
        "packet fields",
    )


def patch_engine(base: str) -> str:
    out = replace_once(
        base,
        "from .edge_reconciler import closed_book_deals\n",
        "from .edge_reconciler import closed_book_deals\nfrom .lane_weights import neutral_snapshot\n",
        "engine import",
    )
    out = replace_once(
        out,
        "                 spread_geometry_floor=None):\n        self.config = config or {}\n        self._mt5 = mt5\n",
        "                 spread_geometry_floor=None, lane_weight_controller=None):\n"
        "        self.config = config or {}\n"
        "        self._mt5 = mt5\n"
        "        # Signed external learning-lane carrier. It reaches the existing sizing seam;\n"
        "        # no activation-token-bound config/profile byte moves.\n"
        "        self._lane_weight_controller = lane_weight_controller\n"
        "        self._last_lane_weights_snapshot = neutral_snapshot(\n"
        "            namespace, \"unobserved\", (), \"lane_weights_not_observed\", status=\"disabled\"\n"
        "        )\n",
        "engine constructor",
    )
    out = replace_once(
        out,
        "        try:\n            intents, meta = self._generate_intents(tags, now)\n",
        "        try:\n"
        "            if self._lane_weight_controller is not None:\n"
        "                self._last_lane_weights_snapshot = self._lane_weight_controller.snapshot(now)\n"
        "            intents, meta = self._generate_intents(tags, now)\n",
        "engine snapshot",
    )
    old = '''            decision = evaluate_vnext_ultimate_book_admission(
                config={"gtos_vnext_runtime": self.config}, intents=intents,
                governor_state=gs, account=self._account,
                limits=self._joint_daily_limits(self._governor_limits(), gs),
                n_active_override=self._running_conviction_override(intents),
                stress_state=self._stress_derisk_state(now))
            return {"ok": True, "decision": decision, "intents": intents, "meta": meta,
                    "governor_state": gs, "n_intents": len(intents),
'''
    new = '''            runtime_overrides = {}
            if (
                self._lane_weight_controller is not None
                and bool(getattr(self._lane_weight_controller, "enabled", False))
            ):
                # An invalid/stale source is already a complete x1.00 vector here; partial
                # application is impossible because validation is all-or-neutral.
                runtime_overrides["ultimate_book_learning_rerate"] = dict(
                    self._last_lane_weights_snapshot.get("weights") or {}
                )
            rt_cfg = dict(self.config, **runtime_overrides) if runtime_overrides else self.config
            decision = evaluate_vnext_ultimate_book_admission(
                config={"gtos_vnext_runtime": rt_cfg}, intents=intents,
                governor_state=gs, account=self._account,
                limits=self._joint_daily_limits(self._governor_limits(), gs),
                n_active_override=self._running_conviction_override(intents),
                stress_state=self._stress_derisk_state(now))
            return {"ok": True, "decision": decision, "intents": intents, "meta": meta,
                    "governor_state": gs, "n_intents": len(intents),
                    "lane_weights": dict(self._last_lane_weights_snapshot),
'''
    out = replace_once(out, old, new, "engine sizing injection")
    return replace_once(
        out,
        '                "generation_skips": list(getattr(self, "_last_generation_skips", []) or []),\n'
        '                "governor_state": None, "n_intents": 0, "runtime_effect_now": False, "reason": reason}',
        '                "generation_skips": list(getattr(self, "_last_generation_skips", []) or []),\n'
        '                "lane_weights": dict(getattr(self, "_last_lane_weights_snapshot", {}) or {}),\n'
        '                "governor_state": None, "n_intents": 0, "runtime_effect_now": False, "reason": reason}',
        "engine safe result",
    )


def patch_owner(base: str) -> str:
    out = replace_once(
        base,
        "                 frontier_exits: tuple = (), spread_geometry_floor=None):",
        "                 frontier_exits: tuple = (), spread_geometry_floor=None,\n"
        "                 lane_weight_controller=None):",
        "owner constructor signature",
    )
    out = replace_once(
        out,
        "        self._spread_geometry_floor = dict(spread_geometry_floor or {})\n        self._mt5 = mt5\n",
        "        self._spread_geometry_floor = dict(spread_geometry_floor or {})\n"
        "        self._lane_weight_controller = lane_weight_controller\n"
        "        self._mt5 = mt5\n",
        "owner field",
    )
    out = replace_once(
        out,
        "                                             broker_symbol=self._broker_symbol,\n"
        "                                             spread_geometry_floor=self._spread_geometry_floor)\n",
        "                                             broker_symbol=self._broker_symbol,\n"
        "                                             spread_geometry_floor=self._spread_geometry_floor,\n"
        "                                             lane_weight_controller=self._lane_weight_controller)\n",
        "owner engine pass",
    )
    out = replace_once(
        out,
        '        bridge = summary.get("bridge") or self._runtime_learning_bridge_context(decision)\n',
        '        bridge = dict(summary.get("bridge") or self._runtime_learning_bridge_context(decision))\n'
        '        if isinstance(summary.get("lane_weights"), dict):\n'
        '            bridge["lane_weights"] = dict(summary["lane_weights"])\n',
        "owner cycle packet bridge",
    )
    out = replace_once(
        out,
        "    def _emit_management_runtime_learning(self, summary: dict, now: datetime) -> None:\n"
        "        bridge = self._runtime_learning_bridge_context()\n",
        "    def _emit_management_runtime_learning(self, summary: dict, now: datetime) -> None:\n"
        "        bridge = self._runtime_learning_bridge_context()\n"
        "        if self._lane_weight_controller is not None:\n"
        "            lane_weights = self._lane_weight_controller.snapshot(now)\n"
        "        else:\n"
        "            lane_weights = dict(getattr(self.engine, \"_last_lane_weights_snapshot\", {}) or {})\n"
        "        summary[\"lane_weights\"] = lane_weights\n"
        "        bridge[\"lane_weights\"] = lane_weights\n",
        "owner management packet bridge",
    )
    return replace_once(
        out,
        '                   "skipped": [], "bar_consumable": True}\n'
        '        summary["skipped"].extend(res.get("generation_skips", []) or [])\n',
        '                   "skipped": [], "bar_consumable": True}\n'
        '        summary["lane_weights"] = dict(res.get("lane_weights") or {})\n'
        '        summary["skipped"].extend(res.get("generation_skips", []) or [])\n',
        "owner cycle summary",
    )


def patch_run_book(base: str) -> str:
    out = replace_once(
        base,
        '    p.add_argument("--tags", default=None, help="Comma-separated sleeve tags to run (default: all BUILT)")\n',
        '    p.add_argument("--tags", default=None, help="Comma-separated sleeve tags to run (default: all BUILT)")\n'
        '    p.add_argument("--lane-weights", default=None,\n'
        '                   help="Signed gtos.lane_weights.v1 file; requires --lane-weights-key "\n'
        '                        "and explicit --tags. Invalid/stale input becomes x1.00 everywhere.")\n'
        '    p.add_argument("--lane-weights-key", default=None,\n'
        '                   help="External HMAC verification key for --lane-weights.")\n',
        "run_book args",
    )
    controller = '''    tags = tuple(t.strip() for t in args.tags.split(",") if t.strip()) if args.tags else None
    # Validate and latch the external sizing carrier before opening an MT5 connection.
    from src.components.ultimate_book.lane_weights import (
        LaneWeightController,
        LaneWeightsConfigurationError,
    )
    try:
        lane_weight_controller = LaneWeightController(
            namespace=args.namespace,
            expected_sleeves=tags or (),
            repo_root=".",
            weights_path=args.lane_weights,
            key_path=args.lane_weights_key,
        )
    except LaneWeightsConfigurationError as exc:
        logging.error("lane-weight launch arguments refused: %s", exc)
        return 4
    lane_weight_snapshot = lane_weight_controller.snapshot()
    if lane_weight_snapshot.get("status") != "active" and lane_weight_controller.enabled:
        logging.error(
            "LANE WEIGHTS NOT ACTIVE: status=%s reason=%s; every --tags sleeve is x1.00",
            lane_weight_snapshot.get("status"),
            lane_weight_snapshot.get("reason"),
        )

'''
    out = replace_once(
        out,
        '    merged["broker_account_namespace"] = args.namespace\n\n'
        '    # notification queue',
        '    merged["broker_account_namespace"] = args.namespace\n\n'
        + controller
        + '    # notification queue',
        "run_book controller",
    )
    out = replace_once(
        out,
        '    tags = tuple(t.strip() for t in args.tags.split(",")) if args.tags else None\n',
        "",
        "run_book late tags",
    )
    return replace_once(
        out,
        "    owner = UltimateBookOwner(merged, mt5, \".\", namespace=args.namespace,\n"
        "                              frontier_exits=frontier_exits,\n"
        "                              spread_geometry_floor=spread_geometry_floor)\n",
        "    owner = UltimateBookOwner(merged, mt5, \".\", namespace=args.namespace,\n"
        "                              frontier_exits=frontier_exits,\n"
        "                              spread_geometry_floor=spread_geometry_floor,\n"
        "                              lane_weight_controller=lane_weight_controller)\n",
        "run_book owner pass",
    )


PATCHERS = {
    "src/components/ultimate_book/runtime_learning_packet.py": patch_packet,
    "src/components/ultimate_book/book_engine.py": patch_engine,
    "src/components/ultimate_book/book_owner.py": patch_owner,
    "run_book.py": patch_run_book,
}


def write_payload(repo_path: str, base_path: Path, expected_sha: str) -> dict:
    raw = base_path.read_bytes()
    if sha(raw) != expected_sha:
        raise RuntimeError(f"base drift: {repo_path}")
    base = raw.decode("utf-8")
    after = PATCHERS[repo_path](base)
    ast.parse(after, filename=repo_path)
    payload = FILES / Path(repo_path).name
    payload.parent.mkdir(parents=True, exist_ok=True)
    payload.write_text(after, encoding="utf-8", newline="\n")
    DIFFS.mkdir(parents=True, exist_ok=True)
    diff = "".join(difflib.unified_diff(
        base.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"host-before/{repo_path}",
        tofile=f"session-co/{repo_path}",
    ))
    diff_path = DIFFS / (repo_path.replace("/", "_") + ".diff")
    diff_path.write_text(diff, encoding="utf-8", newline="\n")
    data = payload.read_bytes()
    return {
        "repo_path": repo_path,
        "destination_on_vps": repo_path.replace("/", "\\"),
        "source_in_this_repo": str(payload.relative_to(REPO)),
        "diff_in_this_repo": str(diff_path.relative_to(REPO)),
        "sha256_before_expected": expected_sha,
        "sha256_after_carry": sha(data),
        "bytes_after": len(data),
        "new_file": False,
    }


def write_new(repo_path: str) -> dict:
    source = REPO / repo_path
    data = source.read_bytes()
    ast.parse(data.decode("utf-8"), filename=repo_path)
    payload = FILES / Path(repo_path).name
    payload.parent.mkdir(parents=True, exist_ok=True)
    payload.write_bytes(data)
    return {
        "repo_path": repo_path,
        "destination_on_vps": repo_path.replace("/", "\\"),
        "source_in_this_repo": str(payload.relative_to(REPO)),
        "sha256_before_expected": None,
        "sha256_after_carry": sha(data),
        "bytes_after": len(data),
        "new_file": True,
    }


def main() -> int:
    records = [write_new("src/components/ultimate_book/lane_weights.py")]
    for repo_path in (
        "src/components/ultimate_book/runtime_learning_packet.py",
        "src/components/ultimate_book/book_engine.py",
        "src/components/ultimate_book/book_owner.py",
        "run_book.py",
    ):
        records.append(write_payload(repo_path, *BASES[repo_path]))
    records.append(write_new("scripts/gtos_lane_weights.py"))
    for index, record in enumerate(records, 1):
        record["copy_order"] = index

    signed = []
    for path in sorted((HERE / "files").glob("*.json")):
        data = path.read_bytes()
        row = json.loads(data)
        signed.append({
            "namespace": row["namespace"],
            "source_in_this_repo": str(path.relative_to(REPO)),
            "destination_on_vps": (
                "C:\\ProgramData\\GTOS\\lane-weights\\" + path.name
            ),
            "sha256": sha(data),
            "bytes": len(data),
            "source_digest_sha256": hashlib.sha256(
                json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
            "effective_decision_day": row["effective_decision_day"],
            "expires_after_decision_day": row["expires_after_decision_day"],
        })

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    manifest = {
        "schema": "gtos.phase17.lane_weights_carry_manifest.v1",
        "session": "CO",
        "blocks": "B2800-B2849",
        "built_from_commit": head,
        "host_state_of_record": {
            "commit": "267cccc94",
            "receipt": "docs/audits/fable5-vision-audit-20260725/phase15/receipts/SPREAD_FLOOR_ARMED_20260731.md",
            "supervisor_sha256_prefix": "63079cec",
            "note": "The commit object is not present locally; the receipt and prior carry manifests provide the exact code-file bytes. Host preflight is mandatory.",
        },
        "purpose": "Carry the signed, [0.50,1.15]-bounded, decision-day-latched learning vector. No config/profile byte moves. Supervisor edit is the separate final arming step.",
        "arms_nothing_until_supervisor_edit": True,
        "activation_token_config_bytes_unchanged": [
            "config/agent_config.yaml",
            "config/profiles/redacted_account.yaml",
        ],
        "R2_input_bindings": "none of the carried source paths is bound",
        "files": records,
        "signed_weight_files": signed,
        "external_key": {
            "local_staging_path": "/Users/borr/GTOSActive/ceremony-secrets/session-co-20260801/lane_weights.key",
            "destination_on_vps": "C:\\ProgramData\\GTOS\\lane-weights\\lane_weights.key",
            "committed": False,
            "required_bytes": 32,
            "secret_or_digest_recorded": False,
            "windows_acl_preflight_required": True,
        },
        "supervisor_edit": {
            "kind": "host-anchored manual edit after postflight",
            "diff": str((HERE / "SUPERVISOR_ARGS.diff").relative_to(REPO)),
            "reason_not_full_payload": "The live supervisor is a host-specific fork; only an 8-hex receipt hash is available locally. Overwriting it from mainline would discard live ceremony history.",
        },
    }
    (HERE / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({
        "ok": True,
        "schema": manifest["schema"],
        "payload_count": len(records),
        "signed_weight_count": len(signed),
        "manifest_sha256": sha((HERE / "MANIFEST.json").read_bytes()),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
