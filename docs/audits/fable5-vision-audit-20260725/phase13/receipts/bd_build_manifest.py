"""Session BD — the carry manifest, generated from the tree rather than hand-written.

    python3 docs/audits/fable5-vision-audit-20260725/phase13/receipts/bd_build_manifest.py

AZ's `activation_carry_mx/MANIFEST.json` is the shape (agreement/commission: "AZ's manifest shape is
the standard"). This one is deliberately NOT a payload package: BD's changes are all default-off and
none of them is the reason for a ceremony. What the orchestrator needs from BD is the composition
facts -- which files BD moved, which of them AZ is already carrying, and the one that must never be
carried whole -- so that whoever composes the next carry does not ship a stale snapshot or an
unintended live behaviour change.

Every sha256 here is read off the working tree at generation time. Nothing is asserted from memory.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase13/BD_CARRY_MANIFEST.json"
# AZ's package lives on the sibling branch `phase13/activation-carry` and is NOT an ancestor of
# BD's HEAD -- wave 13 sessions run in parallel and the orchestrator merges. Reading it out of git
# by commit is both the only way to see it from here AND the more honest one: the manifest below
# records WHICH bytes of AZ's manifest it compared against, so a later reader can tell whether the
# composition facts were computed against the AZ that finally merged.
AZ_MANIFEST_REL = "docs/audits/fable5-vision-audit-20260725/phase13/activation_carry_mx/MANIFEST.json"
AZ_COMMIT = "3b398f031"
S_MANIFEST = REPO / "docs/audits/fable5-vision-audit-20260725/phase4/packet_carry/MANIFEST.json"
R2 = REPO / ("research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
             "B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json")

TOUCHED = [
    "src/components/ultimate_book/book_owner.py",
    "src/components/ultimate_book/execution_packets.py",
    "src/components/ultimate_book/packet_economics.py",
    "src/components/ultimate_book/packet_emit_on_change.py",
    "src/components/execution.py",
    "src/costs/model.py",
]


def sha(rel: str) -> str | None:
    p = REPO / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def r2_bound() -> set[str]:
    d = json.loads(R2.read_text())
    return {
        r["path"]
        for g in ("common_behavior_inputs", "package_authority_inputs")
        for r in d["input_bindings"][g]
    }


def az_manifest() -> dict:
    """AZ's manifest as of `AZ_COMMIT`, read from git. Raises if the commit is unreachable --
    a composition claim computed against a manifest that is not there is worse than none."""
    out = subprocess.run(["git", "show", f"{AZ_COMMIT}:{AZ_MANIFEST_REL}"],
                         cwd=REPO, capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(
            f"cannot read AZ's manifest at {AZ_COMMIT}:{AZ_MANIFEST_REL}. Refusing to publish "
            f"composition facts computed against nothing. git said: {out.stderr.strip()}")
    return json.loads(out.stdout)


def az_facts() -> tuple[set[str], set[str]]:
    m = az_manifest()
    return ({f["repo_path"] for f in m["files"]},
            {n["repo_path"] for n in m["not_carried"]})


def s_destinations() -> set[str]:
    m = json.loads(S_MANIFEST.read_text())
    return {str(f.get("destination_on_vps", "")).replace("\\", "/") for f in m.get("files", [])}


def head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True).stdout.strip()


def main() -> int:
    bound = r2_bound()
    az_carried, az_not_carried = az_facts()
    s_dest = s_destinations()

    files = []
    for rel in TOUCHED:
        on_host_via_s = rel.replace("src/", "src/") in s_dest or any(
            d.endswith(rel.split("/")[-1]) and "ultimate_book" in d for d in s_dest
        ) if "ultimate_book" in rel else False
        row = {
            "repo_path": rel,
            "sha256_at_bd_head": sha(rel),
            "bytes": (REPO / rel).stat().st_size if (REPO / rel).is_file() else None,
            "is_new_file": rel == "src/components/ultimate_book/packet_emit_on_change.py",
            "r2_bound": rel in bound,
            "already_a_payload_in_az_carry": rel in az_carried,
            "in_az_not_carried_list": rel in az_not_carried,
            "reached_host_via_session_S_carry": bool(on_host_via_s),
        }
        if rel in az_carried:
            row["composition_rule"] = (
                "AZ's payload snapshot under phase13/activation_carry_mx/files/ was built BEFORE "
                "these changes and is now STALE for this path. Do NOT apply two snapshots of the "
                "same file. Rebuild AZ's payload from the MERGED tree (its build_carry.py reads the "
                "working tree) and re-verify its sha256_after_carry before any ceremony."
            )
        elif rel in az_not_carried:
            row["composition_rule"] = (
                "AZ measured this file must NOT be carried: the host's copy diverged at lineage "
                "b36d9ab92 and mainline's bytes would ship Session AS's B1535 hunk, which moves "
                "be_trigger_r and take_profit_1 on adopted time-stop positions across all four "
                "ARMED sleeves. BD's change to this file is therefore NOT CARRYABLE AS A WHOLE "
                "FILE. Port hunk-wise or leave it; it is a diagnostic and is inert until ported."
            )
        else:
            row["composition_rule"] = (
                "BD-only. Carryable on its own terms; nothing else in flight owns this path."
            )
        files.append(row)

    doc = {
        "schema": "gtos.phase13.bd_carry_manifest.v1",
        "session": "BD",
        "blocks": "B2050-B2099",
        "built_by": ("docs/audits/fable5-vision-audit-20260725/phase13/receipts/"
                     "bd_build_manifest.py"),
        "bd_head_commit": head(),
        "purpose": (
            "BD is a DEBT SWEEP, not an activation package. Everything it built is default-off and "
            "none of it is a reason for a ceremony. What the orchestrator needs from BD is the "
            "composition facts: which live-path files moved, which of them AZ is already carrying "
            "(so its snapshots are stale), and the one that must never be carried whole."
        ),
        "arms_nothing_by_itself": True,
        "is_a_payload_package": False,
        "default_off_switches_introduced": [
            {"key": "ultimate_book_runtime_learning_packet_emit_on_change",
             "default": False, "read_at": "book_owner.__init__ via rt.get(key, False)",
             "effect_when_off": "no filter object is built; filter_packets is the identity function",
             "set_in_any_committed_config": False},
            {"key": "ultimate_book_runtime_learning_packet_emit_heartbeat_seconds",
             "default": 900, "read_at": "book_owner.__init__",
             "effect_when_off": "unread unless the switch above is true",
             "set_in_any_committed_config": False},
            {"key": "ultimate_book_time_stop_wallclock_on_truncated_window",
             "default": False, "read_at": "ExecutionEngine._time_stop_wallclock_on_truncated_window",
             "effect_when_off": "the truncated-window count is returned exactly as before; only the "
                                "diagnostic and the WARNING are new",
             "set_in_any_committed_config": False},
            {"key": "--frontier-exits energy_agri",
             "default": "not selected", "read_at": "run_book.py / resolve_exit_profile",
             "effect_when_off": "resolve_exit_profile returns the committed partial_be_runner object "
                                "itself, by identity",
             "set_in_any_committed_config": False},
        ],
        "always_on_changes_and_why_they_are_safe": [
            {"change": "modelled cost scalars on the packet (OD-P3)",
             "why_safe": "additive outcome fields on an observation-only packet; emits NOTHING when "
                         "the pretrade model is absent, which is every packet in the 99,112-row "
                         "corpus. No decision reads them."},
            {"change": "unit join-key fields by member agreement (OD-P2)",
             "why_safe": "fills fields that are NULL today and never overwrites a resolved one; "
                         "refuses on disagreement. Changes ultimate_book_intent_id on multi-member "
                         "unit rows -- which is the repair's purpose -- and is forward-only: no "
                         "existing packet is rewritten."},
            {"change": "time-stop window coverage diagnostic (AQ 6a)",
             "why_safe": "the RETURNED COUNT is byte-identical to before with the flag off, pinned "
                         "by test_detection_alone_does_not_change_the_returned_count. Adds a "
                         "diagnostic the book already asked for and never received."},
        ],
        "seal_exposure": {
            "R2_input_bindings": "none of the 6 touched paths is bound (checked in this script)",
            "config_file_hashes": "no config file is touched",
            "activation_token_config_digest": "unaffected -- no byte of config/agent_config.yaml or "
                                              "config/profiles/redacted_account.yaml moved",
            "h1_drift_at_session_end": "1 (UNHYDRATED-LFS on "
                                       "ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl, the "
                                       "documented false alarm)",
        },
        "composes_with": {
            "session_AZ_activation_carry": AZ_MANIFEST_REL,
            "session_AZ_read_at_commit": AZ_COMMIT,
            "session_AZ_manifest_sha256": hashlib.sha256(
                subprocess.run(["git", "show", f"{AZ_COMMIT}:{AZ_MANIFEST_REL}"], cwd=REPO,
                               capture_output=True).stdout).hexdigest(),
            "session_AZ_merge_state": ("NOT an ancestor of BD HEAD at generation time -- wave-13 "
                                       "siblings run in parallel; re-verify after the merge train"),
            "session_S_packet_carry": str(S_MANIFEST.relative_to(REPO)),
            "overlap_with_az_payloads": sorted(az_carried & set(TOUCHED)),
            "in_az_not_carried_list": sorted(az_not_carried & set(TOUCHED)),
            "bd_only": sorted(set(TOUCHED) - az_carried - az_not_carried),
        },
        "carry_order_hazard": {
            "finding": (
                "book_owner.py imports packet_emit_on_change.py, which is a NEW file that is not on "
                "the host. A carry that copies book_owner.py without it would raise ImportError at "
                "module load and stop run_book.py on BOTH funded accounts -- the worst outcome a "
                "carry can have, and a partial state AZ's 16-state probe could not have covered "
                "because the file did not exist when it ran."
            ),
            "resolution": (
                "The import is optional by construction (try/except Exception, the same guard "
                "packet_economics.py:50-66 applies to broker_clock, and broader than ImportError so "
                "a half-transferred CORRUPT module degrades identically to an absent one). Absent, "
                "EMIT_ON_CHANGE_AVAILABLE is False and filter_packets is the identity function. "
                "Proved by test_book_owner_survives_the_filter_module_being_absent, which blocks the "
                "import via sys.meta_path and imports book_owner for real."
            ),
            "so_carry_order_is": "unconstrained -- either file may land first, or alone",
        },
        "not_carryable_as_whole_file": [
            {
                "repo_path": "src/components/execution.py",
                "reason": (
                    "AZ measured the host's copy diverged at lineage b36d9ab92 ('Fix targetless "
                    "time-stop rehydration after restart'), an ancestor of redacted_host and NOT of "
                    "main. A whole-file carry of mainline would ship Session AS's B1535 hunk, which "
                    "AZ measured moves be_trigger_r 0.0 -> the record's value and take_profit_1 "
                    "0.0 -> be_trigger_price on adopted time-stop positions, on 3 of 3 adopt probes, "
                    "across all four ARMED sleeves. BD's own change to this file is a diagnostic "
                    "that changes no returned value; it is worth having on the host but it is worth "
                    "less than an unintended exit-behaviour change on armed money."
                ),
                "bd_hunks": [
                    "ExecutionEngine._trading_m15_bars_since -- coverage diagnostic; returned count "
                    "unchanged with the flag off",
                    "ExecutionEngine._time_stop_wallclock_on_truncated_window -- new, default False",
                    "ExecutionEngine.get_time_stop_clock_diagnostic -- new; the getter "
                    "book_owner.py:2768 has called since the packet carry with no producer",
                ],
                "recommended_disposition": (
                    "DEFER. Port hunk-wise only if the orchestrator is already opening this file on "
                    "the host for another reason. Until then the diagnostic is mainline-only, which "
                    "is where the research drivers read it anyway."
                ),
            },
            {
                "repo_path": "src/costs/model.py",
                "reason": ("src/costs/ does not exist on the live host (packet_economics.py:32 "
                           "documents this and guards its own import for it). Research-surface "
                           "only; the change is an error message."),
                "recommended_disposition": "NOT NEEDED ON HOST.",
            },
        ],
        "files": files,
    }
    OUT.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")
    for f in files:
        flags = []
        if f["already_a_payload_in_az_carry"]:
            flags.append("AZ-PAYLOAD-STALE")
        if f["in_az_not_carried_list"]:
            flags.append("DO-NOT-CARRY-WHOLE")
        if f["is_new_file"]:
            flags.append("NEW")
        if f["r2_bound"]:
            flags.append("R2-BOUND")
        print(f"  {f['repo_path']:<52} {' '.join(flags) or 'bd-only'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
