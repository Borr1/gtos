"""Session AZ (B1850-B1899) — the `mx_btcusd` activation carry, pinned.

WHAT THESE PROTECT, AND WHY IT IS NOT THE OBVIOUS THING

The package under test does not run on this machine. It runs, once, on a live funded Windows
host with two armed books on it, and the operator's only feedback loop is the verifier it
ships with. So the properties worth pinning here are the ones that would make that single
execution wrong in a way nobody notices:

  1. the payloads still rebuild BYTE-IDENTICALLY from their declared sources, so a later edit
     to `execution_packets.py` or to a prior carry's file cannot leave a stale payload behind
     that the manifest still vouches for;
  2. the `run_book.py` variant table is still EXACTLY the set of committed versions the host's
     `book_owner.py` can accept, so preflight cannot recognise a version that would kill the
     book at startup, nor fail to recognise one that would work;
  3. `execution.py` is still correctly OUT of the carry, which rests on a claim about two
     files' contents (`AZ_CARRY_ENUMERATION.md` section 3) and would silently rot;
  4. the launch banner still renders for every wired frontier sleeve — B1852, where six of the
     eight killed the worker AFTER validation had accepted the name.

The economic assertions (`mx_btcusd @ target_5R` is the admitting cell, the armed four do not
move) live in `test_frontier_exit_contracts.py` and are exercised again by
`verify_carry.py --check behaviour` on the host itself.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "docs/audits/fable5-vision-audit-20260725"
PKG = AUDIT / "phase13/activation_carry_mx"
LINEAGE = "redacted_host"

BTC = "mx_btcusd_d1_donchian_20_breakout"
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_show(rev: str, path: str) -> bytes:
    r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=REPO, capture_output=True)
    if r.returncode:
        pytest.skip(f"git object {rev}:{path} unavailable in this checkout")
    return r.stdout


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads((PKG / "MANIFEST.json").read_text(encoding="utf-8"))


# =====================================================================================
# 1. the package is what it says it is
# =====================================================================================

def test_the_shipped_payloads_match_their_manifest():
    """REWRITTEN AT THE WAVE-13 TRAIN, the hour after the ceremony ran. The original ran
    `build_carry.py --check` (payloads re-derive from CURRENT mainline) -- the right guard
    BEFORE shipping, and wrong the moment mainline legitimately moves on (AY's floor and BD's
    detection landed in the same files at the same train). The package is now a SHIPPED
    HISTORICAL ARTIFACT: the host runs these exact bytes (host CARRIED_STATE.json,
    ceremony receipt MX_ACTIVATION_20260731.md). The guard that survives shipping is
    IMMUTABILITY: every payload byte-matches the sha256 its own manifest vouches for. The
    host-vs-mainline gap is the NEXT carry's job, read from CARRIED_STATE.json."""
    manifest = json.loads((PKG / "MANIFEST.json").read_text(encoding="utf-8"))
    for rec in manifest["files"]:
        payload = PKG.parent / rec["source_in_this_repo"].split("activation_carry_mx/")[-1]
        payload = PKG / rec["source_in_this_repo"].split("activation_carry_mx/")[-1]
        got = sha(payload.read_bytes())
        assert got == rec["sha256_after_carry"], (
            f"{payload.name}: shipped payload no longer matches its manifest "
            f"({got[:12]} != {rec['sha256_after_carry'][:12]}) -- the artifact was edited "
            f"after shipping, which the ceremony receipt forbids")


def test_every_payload_parses_and_carries_no_crlf(manifest):
    """A CRLF payload lands on a Windows host that runs LF files; a payload that does not parse
    is a module-load death on both namespaces."""
    payloads = sorted(PKG.glob("files/*.py"))
    assert payloads, "the package has no payloads"
    for p in payloads:
        raw = p.read_bytes()
        assert b"\r\n" not in raw, f"{p.name} carries CRLF"
        ast.parse(raw.decode("utf-8"), filename=p.name)


def test_the_manifest_hashes_describe_the_shipped_bytes(manifest):
    for rec in manifest["files"]:
        if rec["repo_path"] == "run_book.py":
            for state in rec["accepted_before_states"]:
                p = REPO / state["payload_file"]
                assert p.is_file(), f"missing payload {state['payload_file']}"
                assert sha(p.read_bytes()) == state["sha256_after_carry"]
            continue
        p = REPO / rec["source_in_this_repo"]
        assert p.is_file(), f"missing payload {rec['source_in_this_repo']}"
        assert sha(p.read_bytes()) == rec["sha256_after_carry"]


def test_no_orphan_payload(manifest):
    """A file in `files/` that the manifest does not name is a file an operator might copy."""
    declared = set()
    for rec in manifest["files"]:
        declared.add(Path(rec["source_in_this_repo"]).name)
        for state in rec.get("accepted_before_states", []):
            declared.add(state["payload_basename"])
    on_disk = {p.name for p in PKG.glob("files/*")}
    assert on_disk == declared, f"orphans: {sorted(on_disk ^ declared)}"


# =====================================================================================
# 2. the before-bytes are the host's, from committed evidence
# =====================================================================================

def test_book_owner_before_bytes_are_session_S_after_bytes(manifest):
    """The host's `book_owner.py` is Session S's packet-carry payload -- verified at
    after-carry bytes on the running host on 2026-07-30. If that stops being true, this carry's
    anchored edits are being applied to the wrong base and the after-sha is fiction."""
    s_manifest = json.loads((AUDIT / "phase4/packet_carry/MANIFEST.json").read_text())
    s_after = next(r["sha256_after_carry"] for r in s_manifest["files"]
                   if r["destination_on_vps"].endswith("book_owner.py"))
    rec = next(r for r in manifest["files"] if r["repo_path"].endswith("book_owner.py"))
    assert rec["sha256_before_expected"] == s_after
    assert manifest["composes_with"]["book_owner_supersedes"]["session_S_after_carry"] == s_after


@pytest.mark.parametrize("repo_path", [
    "src/components/ultimate_book/execution_packets.py",
    "src/components/ultimate_book/order_router.py",
])
def test_the_whole_file_payloads_are_mainline_and_their_base_is_the_lineage(manifest, repo_path):
    """Half rewritten at the wave-13 train: the 'payload == mainline current' half held until
    the ceremony shipped and mainline moved past it in the same train (by design). What
    survives: the payload matches the manifest it shipped under, and the host's BASE is still
    the lineage's immutable bytes. Mainline's newer bytes for these paths ride the NEXT carry."""
    rec = next(r for r in manifest["files"] if r["repo_path"] == repo_path)
    payload = PKG / ("files/" + repo_path.split("/")[-1])
    assert sha(payload.read_bytes()) == rec["sha256_after_carry"], \
        "the SHIPPED payload no longer matches its own manifest -- edited after shipping"
    assert sha(git_show(LINEAGE, repo_path)) == rec["sha256_before_expected"], \
        "the host's base for this path is no longer the lineage's bytes"


def test_the_two_whole_file_payloads_import_only_what_the_lineage_already_imports():
    """A whole-file copy is only safe if its import closure is already satisfied on the host.
    Both files' `import` statements must be a subset of the lineage version's.

    REWRITTEN 2026-08-25 (root cause: STALE EXPECTATION — the same wave-13 correction its two
    sibling tests already received). The original read the CURRENT tree's files, which was
    right before the ceremony shipped and wrong the moment mainline legitimately moved past it:
    `order_router.py` gained `from math import isfinite` on the live lineage (FrozenPriceIntent
    V1, `a86c18f20`), long after the carry executed (MX_ACTIVATION_20260731.md; the sleeve was
    then disarmed 2026-08-05, MX_DISABLE_RECEIPT.md). The invariant that survives shipping is
    the SHIPPED PAYLOADS' import closure against the lineage base they were applied to — the
    bytes the manifest vouches for and the host ran. Current-tree bytes ride the NEXT carry."""
    for repo_path in ("src/components/ultimate_book/execution_packets.py",
                      "src/components/ultimate_book/order_router.py"):
        def imports(src: str) -> set[str]:
            out = set()
            for node in ast.walk(ast.parse(src)):
                if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    out |= {f"{node.module}.{a.name}" for a in node.names}
                elif isinstance(node, ast.ImportFrom) and node.level:
                    out |= {f".{'.' * (node.level - 1)}{node.module or ''}.{a.name}"
                            for a in node.names}
                elif isinstance(node, ast.Import):
                    out |= {a.name for a in node.names}
            return out
        payload = PKG / ("files/" + repo_path.split("/")[-1])
        new = imports(payload.read_text(encoding="utf-8"))
        old = imports(git_show(LINEAGE, repo_path).decode("utf-8"))
        assert not (new - old), \
            f"{repo_path} shipped payload would need {sorted(new - old)} on the host, " \
            f"which the lineage lacks"


# =====================================================================================
# 3. the run_book.py variant table
# =====================================================================================

def _owner_kwargs(src: str) -> list[str]:
    m = re.search(r"owner = UltimateBookOwner\((.*?)\)\n", src, re.S)
    return re.findall(r"(\w+)=", m.group(1)) if m else []


def test_the_variant_table_is_exactly_the_owner_compatible_versions(manifest):
    """The host's `book_owner.__init__` accepts only `namespace=` beyond the positionals, so a
    run_book that passes `recover_pre_gap_bar=` or `vol_level_tilt=` would raise TypeError at
    STARTUP on both namespaces. Both books are alive, so the host cannot be on one of those.

    This test re-derives the eligible set from git rather than trusting the table: a new
    run_book version that is owner-compatible must be added, and one that is not must never be
    accepted by preflight.
    """
    rec = next(r for r in manifest["files"] if r["repo_path"] == "run_book.py")
    declared = {s["sha256_before_expected"] for s in rec["accepted_before_states"]}

    commits = subprocess.run(["git", "log", "--all", "--format=%H", "--full-history", "--",
                              "run_book.py"], cwd=REPO, capture_output=True, text=True).stdout.split()
    if not commits:
        pytest.skip("run_book.py history unavailable in this checkout")
    eligible, seen = set(), set()
    for c in commits:
        blob = subprocess.run(["git", "rev-parse", f"{c}:run_book.py"], cwd=REPO,
                              capture_output=True, text=True)
        if blob.returncode or blob.stdout.strip() in seen:
            continue
        seen.add(blob.stdout.strip())
        src = subprocess.run(["git", "cat-file", "blob", blob.stdout.strip()], cwd=REPO,
                             capture_output=True).stdout
        text = src.decode("utf-8")
        kwargs = _owner_kwargs(text)
        # eligible == constructs the owner with namespace only AND declares the token context
        # (which the host demonstrably has: it logs `config_digest=` at startup)
        if kwargs == ["namespace"] and "set_activation_context" in text:
            eligible.add(sha(src))
    assert declared == eligible, (
        f"the accepted-before-state table has drifted from git.\n"
        f"  missing from the table: {sorted(eligible - declared)}\n"
        f"  in the table but not eligible: {sorted(declared - eligible)}")


def test_no_accepted_variant_would_pass_a_kwarg_the_host_owner_rejects(manifest):
    """The negative case, stated directly rather than left implicit in the derivation above."""
    host_owner = (AUDIT / "phase4/packet_carry/files/book_owner.py").read_text(encoding="utf-8")
    m = re.search(r"class UltimateBookOwner:\n\s+def __init__\((.*?)\):", host_owner, re.S)
    accepted = set(re.findall(r"(\w+)\s*[:=]", m.group(1)))
    rec = next(r for r in manifest["files"] if r["repo_path"] == "run_book.py")
    for state in rec["accepted_before_states"]:
        src = git_show(state["source_commit"], "run_book.py").decode("utf-8")
        for kw in _owner_kwargs(src):
            assert kw in accepted, \
                f"{state['source_commit']} passes {kw}=, which the host's owner rejects"


def test_every_variant_payload_carries_the_flag_and_only_the_flag(manifest):
    """Each payload must add `--frontier-exits` and the one owner kwarg, and must NOT introduce
    `recover_pre_gap_bar` or `vol_level_tilt` -- those reach an owner that has no such
    parameters."""
    rec = next(r for r in manifest["files"] if r["repo_path"] == "run_book.py")
    for state in rec["accepted_before_states"]:
        text = (REPO / state["payload_file"]).read_text(encoding="utf-8")
        assert '"--frontier-exits"' in text
        assert _owner_kwargs(text) == ["namespace", "frontier_exits"], state["payload_basename"]
        assert "recover_pre_gap_bar" not in text, state["payload_basename"]
        assert "vol_level_tilt" not in text, state["payload_basename"]
        assert "describe_frontier_contract" in text, state["payload_basename"]


# =====================================================================================
# 4. B1852 — the launch banner cannot kill the worker
# =====================================================================================

def test_every_wired_frontier_sleeve_renders_a_launch_banner():
    """B1852. `run_book.py` rendered `float(_o["final_target_r"])` unconditionally and SIX of
    the eight wired sleeves carry no such key, so naming one of them raised KeyError at LAUNCH
    -- after `parse_frontier_exits` had accepted it. The worker dies before `BookLauncher`, the
    supervisor restarts a missing book forever, and `manage_open_positions` never runs on
    either namespace. A new override kind must not reintroduce it."""
    from src.components.ultimate_book import execution_packets as EP
    for sleeve, over in EP.FRONTIER_EXIT_OVERRIDES.items():
        text = EP.describe_frontier_contract(sleeve)
        assert text and text != "no wired override", sleeve
        # and it must name a CONTRACT key, not just be non-empty
        assert any(k in text for k in (
            "TP", "time stop", "exit policy", "scale-out", "stop distance"
        )), \
            f"{sleeve} renders {text!r}"
        assert set(over) - {"frontier_cell", "frontier_evidence"}, \
            f"{sleeve} carries provenance only -- it overrides nothing"


def test_the_banner_never_indexes_a_key_an_override_may_not_have():
    """The behavioural test above passes if `describe_frontier_contract` is right. This one
    fails if `run_book.py` stops using it and goes back to indexing the dict, which is the
    exact regression.

    Done over the AST, not the text: the first draft matched the substring and tripped on the
    COMMENT that explains the defect -- a source-string test doing exactly what the engineering
    rules say source-string tests do.
    """
    for path in [REPO / "run_book.py", *sorted(PKG.glob("files/run_book*.py"))]:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
        loops = [n for n in ast.walk(tree)
                 if isinstance(n, ast.For) and isinstance(n.target, ast.Name)
                 and isinstance(n.iter, ast.Name) and n.iter.id == "frontier_exits"]
        assert len(loops) == 1, f"{path.name}: expected one frontier banner loop, got {len(loops)}"
        body = loops[0]
        indexed = {n.slice.value for n in ast.walk(body)
                   if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant)
                   and isinstance(n.slice.value, str)}
        assert "final_target_r" not in indexed, \
            f"{path.name}: the launch banner indexes final_target_r again -- " \
            f"six wired sleeves lack it and the worker dies at launch"
        called = {n.func.id for n in ast.walk(body)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        assert "describe_frontier_contract" in called, path.name


def test_parse_accepts_exactly_what_the_banner_can_render():
    """The defect was a gap between what validation ACCEPTS and what the next line can HANDLE.
    Assert they are the same set, which is the invariant rather than the instance."""
    from src.components.ultimate_book import execution_packets as EP
    for sleeve in EP.FRONTIER_EXIT_OVERRIDES:
        assert EP.parse_frontier_exits(sleeve) == (sleeve,)
        EP.describe_frontier_contract(sleeve)          # must not raise


# =====================================================================================
# 5. execution.py is correctly NOT carried
# =====================================================================================

HOST_TIME_STOP_BRANCH = 'if selected_policy == "time_stop":'


def test_the_host_execution_py_cannot_raise_the_KeyError_AS_fixed(manifest):
    """The not-carried decision rests on a claim about two files. Pin it.

    Session AS fixed `KeyError('trigger_r')` on MAINLINE. The host's `execution.py` (the
    Session AC activation-carry payload, verified at after-bytes on the running host) carries
    an explicit `time_stop` branch that mainline never received -- lineage commit `b36d9ab92`,
    an ancestor of `redacted_host` and not of `main`. So on the host the defect is unreachable and
    mainline's hunk would be a live behaviour change on four armed sleeves, not a fix.
    """
    host = (AUDIT / "phase5/activation_carry/files/execution.py").read_text(encoding="utf-8")
    main = (REPO / "src/components/execution.py").read_text(encoding="utf-8")

    assert HOST_TIME_STOP_BRANCH in host, \
        "the host's execution.py no longer guards the time_stop rehydration -- RE-DERIVE the " \
        "not-carried decision before shipping this package"
    assert 'trigger_r = float(params["trigger_r"])' in host, \
        "the host branch's shape has changed; the control in az_carry_probe.py will not apply"
    # mainline's replacement: a .get() chain with no time_stop branch at that site
    assert 'trigger_r = params.get("trigger_r")' in main
    assert 'trigger_r = float(params["trigger_r"])' not in main

    declared = {row["repo_path"] for row in manifest["not_carried"]}
    assert "src/components/execution.py" in declared
    assert not any(r["repo_path"] == "src/components/execution.py" for r in manifest["files"])


def test_the_time_stop_engine_the_carry_relies_on_is_identical_on_the_host():
    """AQ's repaired 7680 is consumed by `_trading_m15_bars_since`. If the host's copy differed
    from the one AQ measured, the repair would not mean on the host what it means in the
    receipt. It does not differ -- and that is why `execution.py` needs no carry at all."""
    host = (AUDIT / "phase5/activation_carry/files/execution.py").read_text(encoding="utf-8")

    def body(src: str, name: str) -> str:
        i = src.index(f"def {name}(")
        j = src.index("\n    def ", i + 1)
        return src[i:j]
    # Rewritten at the wave-13 train: the original compared this body to CURRENT mainline,
    # which was true at ship time and false the same night -- Session BD extended mainline's
    # copy with the AQ 6a inertness DETECTION (observable-only), which rides the NEXT carry.
    # The host runs the phase5 bytes (host CARRIED_STATE.json), so the invariant that
    # survives is that THE HOST'S ENGINE BODY is byte-stable against this recorded pin.
    import hashlib as _h
    HOST_BODY_SHA = "85f81dcf17b8d00000a8030ffa07a9a00ff35deaa6bfb4ea125bd6787381bc38"
    assert _h.sha256(body(host, "_trading_m15_bars_since").encode()).hexdigest() == HOST_BODY_SHA, \
        "the phase5 payload's time-stop engine body changed -- it is the HOST's engine of record"


# =====================================================================================
# 6. the carry arms nothing
# =====================================================================================

def test_the_carry_arms_nothing_by_itself(manifest):
    """Every carried default must be what the host runs today. The activation is two launcher
    arguments the ceremony sets separately and an owner decision above them."""
    from src.components.ultimate_book import execution_packets as EP
    assert manifest["arms_nothing_by_itself"] is True
    assert EP.parse_frontier_exits(None) == ()
    for sleeve in ARMED:
        assert EP.resolve_exit_profile(sleeve, frontier_exits=(BTC,)) \
            is EP.SLEEVE_EXIT_PROFILES[sleeve]
    assert EP.SLEEVE_EXIT_PROFILES[BTC]["final_target_r"] == 2.0, \
        "the COMMITTED contract must stay 2R -- the 5R cell is a selection, not an edit"
    assert EP.SLEEVE_EXIT_PROFILES[BTC]["time_stop_bars"] == EP.time_stop_m15(80, "D1") == 7680


def test_no_config_file_is_in_the_carry(manifest):
    """`config/agent_config.yaml` and `config/profiles/redacted_account.yaml` are hashed into the live
    activation tokens' config digests: one byte and the armed book stops placing."""
    for rec in manifest["files"]:
        assert not rec["repo_path"].startswith("config/"), rec["repo_path"]
    declared = {row["repo_path"] for row in manifest["not_carried"]}
    assert {"config/agent_config.yaml", "config/profiles/redacted_account.yaml"} <= declared


def test_the_selection_is_not_a_config_key_in_the_carried_payload():
    """AR's failure shape: a runtime key read through `bridge._bool` against a `DEFAULT_CONFIG`
    that does not have it stands an armed book down every tick with a healthy heartbeat."""
    from src.components.ultimate_book import bridge
    assert not [k for k in getattr(bridge, "DEFAULT_CONFIG", {}) if "frontier" in str(k).lower()]
    for name in ("execution_packets.py", "order_router.py", "book_owner.py"):
        text = (PKG / "files" / name).read_text(encoding="utf-8")
        assert "ultimate_book_frontier" not in text, name


# =====================================================================================
# 7. the ordering invariants the ceremony depends on
# =====================================================================================

def test_the_copy_order_is_dependency_order(manifest):
    """`deps` in `verify_carry.py` asserts these on the host; assert here that the manifest's
    declared copy order actually satisfies them, so the runbook and the gate cannot disagree."""
    order = {r["repo_path"]: r["copy_order"] for r in manifest["files"]}
    ep = "src/components/ultimate_book/execution_packets.py"
    orr = "src/components/ultimate_book/order_router.py"
    bo = "src/components/ultimate_book/book_owner.py"
    assert order[ep] < order[orr] < order[bo] < order["run_book.py"]


def test_the_measured_state_grid_backs_the_ordering_claim():
    """`receipts/AZ_CARRY_PROBE_V1.json` is the measurement the ordering rests on. Assert it
    still says what the docs say: every prefix of the copy order is safe, and the states off
    that order are not."""
    probe = json.loads((PKG / "receipts/AZ_CARRY_PROBE_V1.json").read_text(encoding="utf-8"))
    by_set = {frozenset(r["applied"]): r["probe"] for r in probe["states"]["states"]}

    def fatal(applied) -> bool:
        p = by_set[frozenset(applied)]
        return not (p["run_book_all_imports"]["ok"] and p["construct_default"]["ok"]
                    and p["place_via_router"]["ok"])

    for prefix in [(), ("EP",), ("EP", "OR"), ("EP", "OR", "BO"), ("EP", "OR", "BO", "RB")]:
        assert not fatal(prefix), f"prefix {prefix} of the copy order is fatal"
    for bad in [("BO",), ("OR",), ("RB",), ("BO", "RB"), ("OR", "RB")]:
        assert fatal(bad), f"{bad} was expected fatal and is not -- re-derive the ordering"
    n_fatal = sum(fatal(frozenset(r["applied"])) for r in probe["states"]["states"])
    assert n_fatal == 9, f"the fatal-state count moved from 9 to {n_fatal}"


def test_the_blast_radius_is_the_mx_cohort_and_nothing_armed():
    """AQ's time-stop repair rides `execution_packets.py`. Measured on the HOST's own tree, it
    moves exactly the `mx_*` sleeves' `time_stop_bars` and nothing else -- and no armed sleeve
    at all."""
    probe = json.loads((PKG / "receipts/AZ_CARRY_PROBE_V1.json").read_text(encoding="utf-8"))
    blast = probe["blast_radius"]
    assert set(ARMED) <= set(blast["unchanged"]), \
        f"an ARMED sleeve moved: {sorted(set(ARMED) & set(blast['moved']))}"
    assert all(s.startswith("mx_") for s in blast["moved"]), sorted(blast["moved"])
    for sleeve, sections in blast["moved"].items():
        assert set(sections) <= {"profile", "instrumentation", "placement"}, sleeve
        for fields in sections.values():
            assert set(fields) <= {"time_stop_bars", "gtos_vnext_dynamic_time_stop_bars"}, \
                f"{sleeve} moved a field other than the time stop: {sorted(fields)}"
    assert blast["registry_size_before"] == blast["registry_size_after"], \
        "the carry changed how many sleeves the registry resolves"


# =====================================================================================
# 8. the verifier's byte gates, against a synthetic root
# =====================================================================================

@pytest.fixture(scope="module")
def verifier():
    import importlib.util
    spec = importlib.util.spec_from_file_location("az_verify", PKG / "verify_carry.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _synthetic_root(tmp_path: Path, manifest: dict, applied: set[str]) -> Path:
    """A root with only the four destinations plus the landmarks `resolve_repo_root` proves on.
    Enough for the three BYTE gates, which import nothing."""
    root = tmp_path / "root"
    for rec in manifest["files"]:
        p = root / rec["repo_path"]
        p.parent.mkdir(parents=True, exist_ok=True)
        if rec["repo_path"] == "run_book.py":
            state = next(s for s in rec["accepted_before_states"] if s["is_primary"])
            src = REPO / state["payload_file"] if "RB" in applied else None
            p.write_bytes(src.read_bytes() if src else
                          git_show(state["source_commit"], "run_book.py"))
        else:
            key = {"execution_packets.py": "EP", "order_router.py": "OR",
                   "book_owner.py": "BO"}[Path(rec["repo_path"]).name]
            if key in applied:
                data = (REPO / rec["source_in_this_repo"]).read_bytes()
            elif key == "BO":
                # the host's uncarried book_owner is Session S's PAYLOAD, not the lineage's
                # bytes -- the packet carry already landed. Getting this wrong in the first
                # draft made three states fail for the right reason on the wrong input.
                data = (AUDIT / "phase4/packet_carry/files/book_owner.py").read_bytes()
            else:
                data = git_show(LINEAGE, rec["repo_path"])
            assert sha(data) in (rec["sha256_before_expected"], rec["sha256_after_carry"])
            p.write_bytes(data)
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config/agent_config.yaml").write_text("{}\n")
    (root / "src/components/ultimate_book/book_engine.py").touch()
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "scripts/run_book_supervisor.ps1").write_text(
        '$bookCommand = "run_book.py --namespace operator_profile'
        + (' --frontier-exits mx_btcusd_d1_donchian_20_breakout' if "PS1" in applied else '')
        + '"\n')
    return root


@pytest.mark.parametrize("applied,deps_ok,post_ok,pre_ok", [
    (set(),                        True,  False, True),    # host today
    ({"EP"},                       True,  False, True),
    ({"EP", "OR"},                 True,  False, True),
    ({"EP", "OR", "BO"},           True,  False, True),
    ({"EP", "OR", "BO", "RB"},     True,  True,  True),    # the carry, complete
    ({"BO"},                       False, False, True),    # fatal at STARTUP
    ({"OR"},                       False, False, True),    # fatal at PLACEMENT
    ({"RB"},                       False, False, True),    # fatal at MODULE LOAD
    ({"EP", "BO"},                 False, False, True),
    ({"OR", "BO", "RB"},           False, False, True),
])
def test_the_verifier_byte_gates_score_each_state_correctly(
        verifier, manifest, tmp_path, applied, deps_ok, post_ok, pre_ok):
    """The `deps` decision table, which is the ceremony's safety argument, asserted directly.
    `preflight` passes in every partial state on purpose -- a half-applied carry is a state you
    resume from, not one you are refused for; `deps` is the gate that names it."""
    root = _synthetic_root(tmp_path, manifest, applied)
    verifier._problems.clear()
    assert (verifier.check_deps(root, manifest) == verifier.PASS) is deps_ok
    verifier._problems.clear()
    assert (verifier.check_postflight(root, manifest) == verifier.PASS) is post_ok
    verifier._problems.clear()
    assert (verifier.check_preflight(root, manifest) == verifier.PASS) is pre_ok
    verifier._problems.clear()


@pytest.mark.parametrize("applied,deps_ok", [
    ({"EP", "OR", "BO", "PS1"},        False),   # activated before run_book.py landed
    ({"EP", "OR", "BO", "RB", "PS1"},  True),    # the ceremony, complete
    ({"EP", "OR", "BO", "RB"},         True),    # carried, deliberately not armed
    ({"PS1"},                          False),   # rolled run_book back before the .ps1
])
def test_the_supervisor_line_invariant_bites_in_both_directions(
        verifier, manifest, tmp_path, applied, deps_ok):
    """The fourth invariant, and the one the 16-state file grid could not see because it lives
    in a fifth file. `--frontier-exits` on the supervisor line with an uncarried `run_book.py`
    is `argparse` exiting on an unrecognised argument at EVERY respawn of EVERY namespace --
    a permanent crash loop of both books with no exit management. Reachable on the way IN (step
    8 before step 6) and on the way OUT (restoring run_book.py before the .ps1)."""
    root = _synthetic_root(tmp_path, manifest, applied)
    verifier._problems.clear()
    assert (verifier.check_deps(root, manifest) == verifier.PASS) is deps_ok
    verifier._problems.clear()


def test_preflight_refuses_an_unrecognised_run_book(verifier, manifest, tmp_path):
    """The one file no artifact pins. An unknown sha256 must STOP rather than default to the
    primary payload, which is built from a different base and would silently revert the host."""
    root = _synthetic_root(tmp_path, manifest, set())
    p = root / "run_book.py"
    p.write_bytes(p.read_bytes() + b"\n# an operator edited this by hand\n")
    verifier._problems.clear()
    assert verifier.check_preflight(root, manifest) == verifier.FAIL
    assert any("UNRECOGNISED" in m for m in verifier._problems)
    verifier._problems.clear()


def test_the_order_router_failure_is_a_silent_outage_and_not_a_crash():
    """The claim the ceremony's §10 table and `--check deps` both make, kept honest.

    `UltimateBookOrderRouter.place` catches its own `TypeError` (*"the book NEVER breaks the
    live path"*), so `order_router` carried without `execution_packets` does not crash a book:
    every unit returns `placed: False, reason: router_exception:…` with a healthy process, a
    healthy heartbeat, and exit management still running. If that ever became a crash the
    ordering docs would be wrong in the *reassuring* direction, which is the bad one.
    """
    probe = json.loads((PKG / "receipts/AZ_CARRY_PROBE_V1.json").read_text(encoding="utf-8"))
    by_set = {frozenset(r["applied"]): r["probe"] for r in probe["states"]["states"]}
    broken = by_set[frozenset({"OR"})]["place_through_router_place"]
    assert broken["ok"] is True, "place() raised — it is supposed to catch"
    assert broken["value"]["placed"] is False
    assert "router_exception:TypeError" in broken["value"]["reason"]
    for good in ((), ("EP", "OR"), ("EP", "OR", "BO", "RB")):
        v = by_set[frozenset(good)]["place_through_router_place"]
        assert v["ok"] and v["value"]["placed"] is True and v["value"]["reason"] == "ok", good


def test_the_as_hunk_control_still_shows_it_would_move_armed_behaviour():
    """The evidence for the not-carried decision, kept alive."""
    probe = json.loads((PKG / "receipts/AZ_CARRY_PROBE_V1.json").read_text(encoding="utf-8"))
    ctl = probe["as_fix_control"]
    assert ctl["host_branch_present"] == {"rehydration_branch": 1, "take_profit_1_branch": 1}
    assert ctl["n_moved"] == 3
    crypto = ctl["adopt_probes_that_move_if_the_hunk_is_carried"]["adopt_time_stop_sleeve"]
    assert crypto["host_today"]["value"]["take_profit_1"] == 0.0
    assert crypto["with_AS_hunk"]["value"]["take_profit_1"] != 0.0, \
        "the control no longer demonstrates the behaviour change it justifies"
    assert crypto["host_today"]["ok"] is True, \
        "the host must NOT raise today -- that is the whole claim"
