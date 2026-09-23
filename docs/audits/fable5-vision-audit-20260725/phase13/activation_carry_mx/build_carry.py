#!/usr/bin/env python3
"""Build the Session AZ `mx_btcusd` activation carry (wave 13, B1850-B1899).

Run from the repo root of THIS laptop worktree:

    python3 docs/audits/fable5-vision-audit-20260725/phase13/activation_carry_mx/build_carry.py
    python3 .../build_carry.py --check      # rebuild into memory and assert nothing moved

What this produces is the package the orchestrator carries to the VPS so that

    run_book.py --tags crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout \
                --frontier-exits mx_btcusd_d1_donchian_20_breakout

runs the estate's ONE standing admission at the exit contract its evidence is measured at.
The package ARMS NOTHING by itself: every carried default is byte-identical to what the host
runs today, and the activation is two launcher arguments the orchestrator sets separately.

------------------------------------------------------------------------------------------
THE HOST'S BYTES, AND WHY THIS IS NOT A WHOLE-TREE COPY
------------------------------------------------------------------------------------------
The host is the VPS lineage `redacted_host`
(`origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18`) plus three already-executed
carries, and its `src/` has FORKED from mainline in ways mainline never received. Two of them
are load-bearing for this carry and both were found by diffing rather than by assuming:

  * `src/components/execution.py` on the host has a `selected_policy == "time_stop"` branch in
    `hydrate_vnext_dynamic_policy_from_record` (commit `b36d9ab92`, "Fix targetless time-stop
    rehydration after restart" -- an ancestor of the LINEAGE and NOT of `main`). So the
    `KeyError('trigger_r')` Session AS fixed on mainline **cannot occur on the host**, and
    mainline's replacement of that branch would change two live behaviours on adopted
    positions for no benefit. `execution.py` is therefore NOT in this carry; see
    `AZ_CARRY_ENUMERATION.md` section 3.
  * the host's `check_time_stop_and_close` carries a whole time-stop clock DIAGNOSTIC layer
    mainline does not have, while `_trading_m15_bars_since` is byte-identical -- so AQ's
    repaired 7680 is consumed on the host by exactly the code its measurement describes.

Every payload is therefore either (a) a mainline file whose diff against the lineage is
EXACTLY the change being carried and whose import closure is byte-identical, or (b) the host's
own bytes plus named, anchored edits.

------------------------------------------------------------------------------------------
`run_book.py` AND THE ONE FILE WHOSE HOST BYTES NOBODY RECORDED
------------------------------------------------------------------------------------------
`run_book.py` was carried by the Stage-0 token ceremony (`phase3/TOKEN_CARRY.md`), which
recorded LINE COUNTS and no sha256. So the host's bytes are not pinned by any artifact. They
are, however, BOUNDED: the host's `book_owner.__init__` (the phase4 packet-carry payload,
sha256 `2b9aab7b...`) accepts neither `recover_pre_gap_bar` nor `vol_level_tilt`, so any
run_book that passes them would raise `TypeError` at startup on both namespaces -- and both
books are alive. That eliminates every version from Session AI onward and leaves exactly the
four committed versions built here, each with its own payload and its own exact after-sha256.
`verify_carry.py --check preflight` reads the host's actual sha256 and names the variant; an
unrecognised one is a STOP, not a guess.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
FILES = HERE / "files"
DIFFS = HERE / "diffs"
RECEIPTS = HERE / "receipts"

LINEAGE = "redacted_host"
AUDIT = "docs/audits/fable5-vision-audit-20260725"

# The two prior carries' payload files ARE the host's current bytes for those paths: the
# 2026-07-30 ceremony verified all of them at after-carry hashes on the running host
# (`phase8/receipts/VPS_CEREMONY_COMPLETED.md`).
HOST_OVERLAY = {
    "src/utils/broker_clock.py": f"{AUDIT}/phase5/activation_carry/files/broker_clock.py",
    "src/components/ultimate_book/governor_state.py": f"{AUDIT}/phase5/activation_carry/files/governor_state.py",
    "src/components/ultimate_book/book_engine.py": f"{AUDIT}/phase5/activation_carry/files/book_engine.py",
    "src/components/execution.py": f"{AUDIT}/phase5/activation_carry/files/execution.py",
    "src/components/ultimate_book/book_owner.py": f"{AUDIT}/phase4/packet_carry/files/book_owner.py",
    "src/components/ultimate_book/runtime_learning_packet.py": f"{AUDIT}/phase4/packet_carry/files/runtime_learning_packet.py",
    "src/components/ultimate_book/packet_economics.py": f"{AUDIT}/phase4/packet_carry/files/packet_economics.py",
    "src/components/ultimate_book/packet_guard.py": f"{AUDIT}/phase4/packet_carry/files/packet_guard.py",
}

#: Every committed `run_book.py` whose owner construction passes ONLY `namespace=`, i.e. every
#: version compatible with the host's `book_owner.py`. Keyed by the sha256 preflight will read.
RUN_BOOK_VARIANTS = {
    "262014f24dee8fa7709612fa4cd4db6c45b3bf26ca2c7fc682fce26d61e7aa80": {
        "commit": "7c85c3105", "bytes": 18032,
        "label": "Phase 0 item 4 — the activation-token invert (the Stage-0 carry's own branch state)",
    },
    "96ac1b566dc8a24f293c4357ed48fe4a961b7ea5fc1aa9b5b0702e8053f9b401": {
        "commit": "52aa3fb34", "bytes": 19218,
        "label": "Session I safety spine — never-strand + four token holes",
    },
    "a850baf45caba8347225bc09832a2427f0f96b3e0750e2448efdbaffc182e146": {
        "commit": "637e2e094", "bytes": 18700,
        "label": "Session M — F30/Q7 notification authorization",
    },
    "014ce9df03fa141def0d5912ee3ad28e0b733e99e21daa042835e9d0ce44a420": {
        "commit": "dcb54cbab", "bytes": 19886,
        "label": "wave-3 integration (I+M merged) — the MOST LIKELY host state; CLAUDE.md records "
                 "run_book.py at 19,886 bytes at that HEAD",
        "primary": True,
    },
}

# ------------------------------------------------------------------------------------------
# the anchored edits
# ------------------------------------------------------------------------------------------

RB_ANCHOR_ONCE = '    p.add_argument("--once", action="store_true", help="Run a single tick and exit (wiring check)")\n'
RB_ANCHOR_OWNER = '    owner = UltimateBookOwner(merged, mt5, ".", namespace=args.namespace)\n'

RB_ARG = '''    p.add_argument("--frontier-exits", default=None,
                   help="Comma-separated sleeves to run on their WAVE-12 frontier exit contract "
                        "instead of the committed one (Session AU, B1550). The one this host is "
                        "carried for is mx_btcusd_d1_donchian_20_breakout -> target_5R: broker TP "
                        "5R instead of the generator's 2R, which is the exit the estate's ONE "
                        "standing admission is measured at (p 0.0011, admits at two of three cost "
                        "bands on the ratified RECORDED population, and REJECTS at all four bands "
                        "at the 2R the spec runs). sub_xvol_pullback -> target_4R is also wired and "
                        "IS ARMED ON BOTH ACCOUNTS at 3R -- it REJECTS at all four bands at the "
                        "ratified rule (Session AU section 1.3), so do not select it. Six further "
                        "default-off time-stop cells are wired and none of them is armed. Empty by "
                        "default. An empty string is REFUSED rather than read as 'all' (the --tags "
                        "fail-open, B359), and an unknown sleeve name is REFUSED rather than "
                        "dropped. FLIP AT A FLAT BOOK: a position adopted with no trade record is "
                        "rehydrated from the sleeve identity, so a pre-flip position's broker TP "
                        "would move. Set here rather than in agent_config.yaml or "
                        "profiles/redacted_account.yaml because BOTH are hashed into a live activation "
                        "token's config digest, and a byte moved there stops the armed book "
                        "placing until the token is re-minted.")
'''

RB_OWNER = '''    # Validated at LAUNCH, before any engine exists: an unparseable selection must stop the
    # worker, not degrade to the committed contract at every tick in silence.
    # `parse_frontier_exits` raises on an empty string and on an unknown sleeve name
    # (Session AU, B1550). Exit 4 is this file's existing "refusing to start" code.
    from src.components.ultimate_book.execution_packets import (
        FRONTIER_EXIT_OVERRIDES, FrontierExitSelectionError, describe_frontier_contract,
        parse_frontier_exits,
    )
    try:
        frontier_exits = parse_frontier_exits(args.frontier_exits)
    except FrontierExitSelectionError as exc:
        logging.error("--frontier-exits refused: %s", exc)
        return 4
    owner = UltimateBookOwner(merged, mt5, ".", namespace=args.namespace,
                              frontier_exits=frontier_exits)
    for _s in frontier_exits:
        # B1852: this banner used to render `float(_o["final_target_r"])`, which SIX of the eight
        # wired sleeves do not carry -- so naming one of them killed the worker AFTER
        # `parse_frontier_exits` had accepted it. `describe_frontier_contract` renders whichever
        # contract keys the override actually has.
        logging.warning("FRONTIER EXIT CONTRACT IS ON for %s: %s (%s). This changes WHERE or WHEN "
                        "this book exits that sleeve; positions already open are managed from "
                        "their own trade record, but one adopted WITHOUT a record is rehydrated at "
                        "this contract.", _s, FRONTIER_EXIT_OVERRIDES[_s]["frontier_cell"],
                        describe_frontier_contract(_s))
'''

BO_ANCHOR_SIG = (
    '    def __init__(self, base_config: dict, mt5, repo_root: str, namespace: str = "operator_profile",\n'
    '                 engine_factory: Optional[Callable[[str], Any]] = None):\n'
)
BO_SIG = (
    '    def __init__(self, base_config: dict, mt5, repo_root: str, namespace: str = "operator_profile",\n'
    '                 engine_factory: Optional[Callable[[str], Any]] = None,\n'
    '                 frontier_exits: tuple = ()):\n'
    '        # `frontier_exits` is a SET OF SLEEVE NAMES reached from `run_book.py --frontier-exits`\n'
    '        # (Session AU, B1550; carried by Session AZ, B1850). It is not a boolean because the two\n'
    '        # target-override sleeves are in opposite live states -- `mx_btcusd` is not in either\n'
    '        # account\'s `--tags` today, while `sub_xvol_pullback` IS armed at 3R on both accounts --\n'
    '        # so one switch would force a ceremony to change armed money in order to make the\n'
    '        # admission\'s own contract runnable. It reaches the PLACEMENT path (the router) and the\n'
    '        # ADOPT-rehydration path, and nothing else. It is an explicit constructor argument and\n'
    '        # NOT a config key: `config/agent_config.yaml` and `config/profiles/redacted_account.yaml` are\n'
    '        # both hashed into a live activation token\'s config digest, so a key in either would\n'
    '        # stop the armed book placing until the token was re-minted. Default () ==\n'
    '        # byte-identical to what this host runs today.\n'
)
BO_ANCHOR_SELF = '        self.base_config = base_config or {}\n'
BO_SELF = (
    '        self.base_config = base_config or {}\n'
    '        self._frontier_exits = tuple(frontier_exits or ())\n'
)
BO_ANCHOR_ROUTER = '        self.router = UltimateBookOrderRouter(self.base_config, namespace=namespace)\n'
BO_ROUTER = (
    '        self.router = UltimateBookOrderRouter(self.base_config, namespace=namespace,\n'
    '                                              frontier_exits=self._frontier_exits)\n'
)
BO_ANCHOR_NPI = '                rec = {"instrumentation": native_policy_instrumentation(sleeve),\n'
BO_NPI = (
    '                rec = {"instrumentation": native_policy_instrumentation(\n'
    '                           sleeve, frontier_exits=self._frontier_exits),\n'
)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_show(rev: str, path: str) -> bytes:
    out = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=REPO,
                         capture_output=True, check=True)
    return out.stdout


def host_bytes(repo_path: str) -> bytes:
    """The bytes this host runs today for `repo_path`, from committed evidence only."""
    over = HOST_OVERLAY.get(repo_path)
    if over:
        return (REPO / over).read_bytes()
    return git_show(LINEAGE, repo_path)


def apply_once(text: str, anchor: str, replacement: str, what: str) -> str:
    n = text.count(anchor)
    if n != 1:
        raise SystemExit(f"ANCHOR NOT UNIQUE ({n} matches) for {what}:\n{anchor!r}")
    return text.replace(anchor, replacement)


def build_run_book(base: bytes) -> bytes:
    text = base.decode("utf-8")
    if "\r\n" in text:
        raise SystemExit("run_book.py base carries CRLF; the anchors assume LF")
    text = apply_once(text, RB_ANCHOR_ONCE, RB_ANCHOR_ONCE + RB_ARG, "run_book --frontier-exits arg")
    text = apply_once(text, RB_ANCHOR_OWNER, RB_OWNER, "run_book owner construction")
    return text.encode("utf-8")


def build_book_owner(base: bytes) -> bytes:
    text = base.decode("utf-8")
    if "\r\n" in text:
        raise SystemExit("book_owner.py base carries CRLF; the anchors assume LF")
    text = apply_once(text, BO_ANCHOR_SIG, BO_SIG, "book_owner __init__ signature")
    text = apply_once(text, BO_ANCHOR_SELF, BO_SELF, "book_owner _frontier_exits assignment")
    text = apply_once(text, BO_ANCHOR_ROUTER, BO_ROUTER, "book_owner router construction")
    text = apply_once(text, BO_ANCHOR_NPI, BO_NPI, "book_owner adopt-rehydration call")
    return text.encode("utf-8")


def unified(before: bytes, after: bytes, path: str) -> str:
    return "".join(difflib.unified_diff(
        before.decode("utf-8").splitlines(keepends=True),
        after.decode("utf-8").splitlines(keepends=True),
        fromfile=f"a/{path}  (HOST today)", tofile=f"b/{path}  (after this carry)", n=4))


def assert_parses(name: str, data: bytes) -> None:
    try:
        ast.parse(data.decode("utf-8"), filename=name)
    except SyntaxError as exc:
        raise SystemExit(f"payload {name} does not parse: {exc}")


# ------------------------------------------------------------------------------------------
# the plan
# ------------------------------------------------------------------------------------------

def build_plan() -> tuple[list[dict], dict]:
    plan: list[dict] = []

    # ---- 1 + 2: mainline files whose diff against the lineage is EXACTLY the carried change ----
    for order, repo_path, note in [
        (1, "src/components/ultimate_book/execution_packets.py",
         "AQ's mx_* time-stop unit repair (96 -> 7680, B1404) + AU's frontier-exit registry "
         "(B1550) + AZ's launch-banner renderer (B1852). Carried WHOLE: its diff against the "
         "lineage is exactly those three changes and its import header is BYTE-IDENTICAL to the "
         "lineage's, so its closure is already satisfied on the host. Unbound by R2, R1, "
         "code_authority_paths and config_file_hashes (Session AS section 0.2, re-checked here)."),
        (2, "src/components/ultimate_book/order_router.py",
         "AU's two frontier hunks and nothing else -- the whole-file diff against the lineage is "
         "14 lines. Carried WHOLE for the same reason. MUST land AFTER execution_packets.py: it "
         "passes `frontier_exits=` to `build_book_trade_params`, which the lineage's signature "
         "does not accept, and that failure lands at PLACEMENT rather than at startup."),
    ]:
        before = host_bytes(repo_path)
        after = (REPO / repo_path).read_bytes()
        assert_parses(repo_path, after)
        plan.append(dict(
            copy_order=order, stage="A", repo_path=repo_path,
            destination_on_vps=repo_path.replace("/", "\\"),
            source_in_this_repo=f"{AUDIT}/phase13/activation_carry_mx/files/{Path(repo_path).name}",
            diff_in_this_repo=f"{AUDIT}/phase13/activation_carry_mx/diffs/"
                              f"{repo_path.replace('/', '_')}.diff",
            is_new_file_on_vps=False,
            sha256_before_expected=sha(before), sha256_after_carry=sha(after),
            bytes_before=len(before), bytes_after=len(after),
            crlf_present=b"\r\n" in after,
            host_bytes_provenance="lineage redacted_host (never carried)",
            source_kind="mainline byte-identical", note=note,
            _payload=after, _before=before,
        ))

    # ---- 3: book_owner.py, the host's own bytes + four anchored edits ----
    repo_path = "src/components/ultimate_book/book_owner.py"
    before = host_bytes(repo_path)
    after = build_book_owner(before)
    assert_parses(repo_path, after)
    plan.append(dict(
        copy_order=3, stage="A", repo_path=repo_path,
        destination_on_vps=repo_path.replace("/", "\\"),
        source_in_this_repo=f"{AUDIT}/phase13/activation_carry_mx/files/book_owner.py",
        diff_in_this_repo=f"{AUDIT}/phase13/activation_carry_mx/diffs/"
                          f"{repo_path.replace('/', '_')}.diff",
        is_new_file_on_vps=False,
        sha256_before_expected=sha(before), sha256_after_carry=sha(after),
        bytes_before=len(before), bytes_after=len(after),
        crlf_present=b"\r\n" in after,
        host_bytes_provenance="Session S packet carry, after-bytes verified on the running host "
                              "2026-07-30 (phase8/receipts/VPS_CEREMONY_COMPLETED.md)",
        source_kind="host file + 4 anchored edits",
        note="MAINLINE'S book_owner.py MUST NOT BE COPIED: it is 4,100+ lines and ~330 lines of "
             "diff ahead of the host, including wave 5-12 work whose closure this host does not "
             "have. The four edits are the whole of AU's threading: the `frontier_exits` kwarg, "
             "the instance field, the router construction, and the adopt-rehydration call. MUST "
             "land AFTER order_router.py -- it passes `frontier_exits=` to the router's "
             "constructor, and the lineage router raises TypeError there, at STARTUP, on both "
             "namespaces.",
        _payload=after, _before=before,
    ))

    # ---- 4: run_book.py, one payload per accepted host state ----
    rb_variants = []
    for before_sha, meta in RUN_BOOK_VARIANTS.items():
        base = git_show(meta["commit"], "run_book.py")
        if sha(base) != before_sha:
            raise SystemExit(f"run_book variant {meta['commit']} no longer hashes to {before_sha}")
        after = build_run_book(base)
        assert_parses("run_book.py", after)
        name = ("run_book.py" if meta.get("primary")
                else f"run_book.variant_{before_sha[:12]}.py")
        rb_variants.append(dict(
            payload_file=f"{AUDIT}/phase13/activation_carry_mx/files/{name}",
            payload_basename=name,
            sha256_before_expected=before_sha, sha256_after_carry=sha(after),
            bytes_before=len(base), bytes_after=len(after),
            source_commit=meta["commit"], label=meta["label"],
            is_primary=bool(meta.get("primary")),
            _payload=after, _before=base,
        ))
    primary = next(v for v in rb_variants if v["is_primary"])
    plan.append(dict(
        copy_order=4, stage="A", repo_path="run_book.py", destination_on_vps="run_book.py",
        source_in_this_repo=primary["payload_file"],
        diff_in_this_repo=f"{AUDIT}/phase13/activation_carry_mx/diffs/run_book.py.diff",
        is_new_file_on_vps=False,
        sha256_before_expected=primary["sha256_before_expected"],
        sha256_after_carry=primary["sha256_after_carry"],
        bytes_before=primary["bytes_before"], bytes_after=primary["bytes_after"],
        crlf_present=b"\r\n" in primary["_payload"],
        host_bytes_provenance="Stage-0 token carry (phase3/TOKEN_CARRY.md), which recorded LINE "
                              "COUNTS and no sha256 -- so the host's exact bytes are NOT pinned by "
                              "any artifact. `accepted_before_states` is the complete set of "
                              "committed versions compatible with the host's book_owner.py; "
                              "preflight reads the host's sha256 and selects.",
        source_kind="host file + 2 anchored edits (variant-selected)",
        accepted_before_states=[{k: v for k, v in d.items() if not k.startswith("_")}
                               for d in rb_variants],
        note="LAST, and that ordering is the whole of the safety argument: run_book.py is the only "
             "carried file whose failure is a MODULE-LOAD or STARTUP death on both namespaces, and "
             "every other file in this carry is inert until it exists. It imports "
             "`parse_frontier_exits` from execution_packets (ImportError without file 1) and "
             "passes `frontier_exits=` to UltimateBookOwner (TypeError without file 3).",
        _payload=primary["_payload"], _before=primary["_before"], _variants=rb_variants,
    ))
    return plan, {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="rebuild and assert every committed payload/manifest byte is unchanged")
    args = ap.parse_args()

    plan, _ = build_plan()
    written: dict[str, bytes] = {}

    for rec in plan:
        for variant in rec.get("_variants", [{"payload_basename": Path(rec["repo_path"]).name,
                                              "_payload": rec["_payload"]}]):
            written[f"files/{variant['payload_basename']}"] = variant["_payload"]
        written[f"diffs/{rec['repo_path'].replace('/', '_')}.diff"] = unified(
            rec["_before"], rec["_payload"], rec["repo_path"]).encode("utf-8")

    manifest = {
        "schema": "gtos.phase13.activation_carry_mx_manifest.v1",
        "session": "AZ",
        "blocks": "B1850-B1899",
        "built_by": f"{AUDIT}/phase13/activation_carry_mx/build_carry.py",
        "purpose": "Make `mx_btcusd_d1_donchian_20_breakout @ target_5R` -- the estate's ONE "
                   "standing admission at the ratified rule -- RUNNABLE on the live host. The "
                   "package arms nothing: it carries the capability, and the activation is "
                   "`--tags ...,mx_btcusd_d1_donchian_20_breakout` plus "
                   "`--frontier-exits mx_btcusd_d1_donchian_20_breakout` on the supervisor line.",
        "vps_base_ref": "origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18",
        "vps_base_commit": "redacted_host87668c5d503b52925d10be7dfb66540",
        "host_repo_root": "C:\\Users\\MSI\\Documents\\ai-trading-agent",
        "host_interpreter": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.venv-gtos\\Scripts\\python.exe",
        "host_interpreter_version": "3.13.13",
        "host_branch_head_at_build_time": "7017c6745 (the fx_jpy pull, 2026-07-30 ~14:57Z)",
        "arms_nothing_by_itself": True,
        "composes_with": {
            "session_S_packet_carry": f"{AUDIT}/phase4/packet_carry/MANIFEST.json",
            "session_AC_activation_carry": f"{AUDIT}/phase5/activation_carry/MANIFEST.json",
            "rule": "Both are ALREADY APPLIED on the host and verified at after-bytes on "
                    "2026-07-30 (phase8/receipts/VPS_CEREMONY_COMPLETED.md). This carry reads "
                    "their after-bytes as its OWN before-bytes for book_owner.py, and does not "
                    "re-carry any file either of them owns. It shares NO destination path with "
                    "the AC carry and exactly ONE with the S carry (book_owner.py), which it "
                    "supersedes.",
            "book_owner_supersedes": {
                "session_S_after_carry": "2b9aab7b0ff652647fd5cd304559ca20f900cd2e7b4c480e2c07cd557acf87e2",
                "this_carry_after": next(r["sha256_after_carry"] for r in plan
                                         if r["repo_path"].endswith("book_owner.py")),
            },
        },
        "not_carried": [
            {
                "repo_path": "src/components/execution.py",
                "reason": "MEASURED, and it inverts the commission's premise. Session AS's "
                          "`KeyError('trigger_r')` adopt-path defect is REAL ON MAINLINE and "
                          "UNREACHABLE ON THIS HOST: the host's execution.py carries an explicit "
                          "`if selected_policy == \"time_stop\":` branch (lineage commit "
                          "b36d9ab92, 'Fix targetless time-stop rehydration after restart', an "
                          "ancestor of redacted_host and NOT of main) that sets trigger_r = 0.0 and "
                          "guards final_target_r. Carrying mainline's hunk would fix nothing and "
                          "would change two live behaviours on adopted time-stop positions -- "
                          "`be_trigger_r` 0.0 -> the record's value, and `take_profit_1` 0.0 -> "
                          "`be_trigger_price` -- on four of the four armed sleeves. See "
                          "AZ_CARRY_ENUMERATION.md section 3.",
            },
            {
                "repo_path": "config/agent_config.yaml",
                "reason": "Hashed into the live activation token's config digest. One byte stops "
                          "the armed book placing until the token is re-minted. Nothing in this "
                          "carry needs it: the frontier selection is deliberately not a config "
                          "key, and mx_btcusd_d1_donchian_20_breakout is ALREADY in the host's "
                          "effective registry via `ultimate_book_include_market_expansion_book: "
                          "true` + policy `positive_weighted12_after_swap` (12 sleeves, measured).",
            },
            {
                "repo_path": "config/profiles/redacted_account.yaml",
                "reason": "Same. And the redacted_account account is out of scope for this activation.",
            },
        ],
        "seal_exposure": {
            "R2_input_bindings": "none of the 4 carried paths is bound",
            "R1_input_bindings": "none",
            "code_authority_paths": "none",
            "config_file_hashes": "no config file is touched",
            "checked_at": "session AZ, against "
                          "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py "
                          "and both contracts",
        },
        "files": [{k: v for k, v in rec.items() if not k.startswith("_")} for rec in plan],
    }
    written["MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")

    if args.check:
        bad = 0
        for rel, data in sorted(written.items()):
            p = HERE / rel
            got = p.read_bytes() if p.is_file() else None
            if got != data:
                print(f"[ FAIL ] {rel}: {'absent' if got is None else 'differs'}")
                bad += 1
            else:
                print(f"[  ok  ] {rel}")
        print(f"\n{'REBUILD IS NOT REPRODUCIBLE' if bad else 'reproducible: every byte identical'}")
        return 2 if bad else 0

    FILES.mkdir(parents=True, exist_ok=True)
    DIFFS.mkdir(parents=True, exist_ok=True)
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    for rel, data in sorted(written.items()):
        (HERE / rel).write_bytes(data)
        print(f"wrote {rel:64s} {len(data):8d} B  sha256 {sha(data)[:16]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
