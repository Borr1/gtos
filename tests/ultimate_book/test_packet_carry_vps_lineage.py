"""The packet carry, tested against the lineage it will actually run on.

Session P's carry was correct on `main` and **unlandable on the VPS**. Three files were held
because `book_owner.py` imports `convergence_advisory.py`, a module the live lineage has never
had; the failure would have been an `ImportError` at module load on both namespaces, and the
supervisor only ever *starts* a missing book, never stops one -- a 5-minute restart loop with
`manage_open_positions` off on every open position.

`PACKET_EMITTER_CARRY.md` §A4 runs exactly this audit for `broker_clock.py` and calls a module-load
failure propagating through `book_owner` *"the single worst outcome this carry could have had"* --
and then does not run it for `convergence_advisory`, because that session was on `main` and could
not see the VPS lineage. So these tests do not assert against `main`. They reconstruct the VPS tree
from its own commit and assert against that.

Every test here is behavioural or graph-based. None of them greps the carried source for a
substring, because a substring assertion passes against a wrong implementation.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CARRY = REPO / "docs/audits/fable5-vision-audit-20260725/phase4/packet_carry"
FILES = CARRY / "files"

# The VPS lineage's own commit. Verified in B291 to be byte-identical to the 2026-07-26 VPS
# working-tree export across src/components/ultimate_book/, src/utils/ and src/mt5/ -- 63 of 63
# files -- so it is a faithful proxy for the live host and not merely a nearby branch.
VPS_COMMIT = "redacted_host87668c5d503b52925d10be7dfb66540"

# Where the carried files land on the VPS, in copy order.
CARRY_MAP = {
    "broker_clock.py": "src/utils/broker_clock.py",
    "runtime_learning_packet.py": "src/components/ultimate_book/runtime_learning_packet.py",
    "packet_economics.py": "src/components/ultimate_book/packet_economics.py",
    "packet_guard.py": "src/components/ultimate_book/packet_guard.py",
    "book_owner.py": "src/components/ultimate_book/book_owner.py",
}


def _have_vps_commit() -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{VPS_COMMIT}^{{commit}}"],
        cwd=REPO, capture_output=True,
    ).returncode == 0


requires_lineage = pytest.mark.skipif(
    not _have_vps_commit(),
    reason=f"VPS lineage commit {VPS_COMMIT[:9]} not in this clone's object store",
)


def _materialise(dest: Path, *, with_carry: bool, with_broker_clock: bool = True) -> Path:
    """Lay down the VPS `src/` tree, optionally with the carry applied over it."""
    dest.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ["git", "archive", VPS_COMMIT, "src/"], cwd=REPO, capture_output=True, check=True
    ).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)
    if with_carry:
        for fname, rel in CARRY_MAP.items():
            if fname == "broker_clock.py" and not with_broker_clock:
                continue
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((FILES / fname).read_bytes())
    return dest


@pytest.fixture(scope="module")
def vps_plain(tmp_path_factory) -> Path:
    """The VPS lineage exactly as it is today."""
    return _materialise(tmp_path_factory.mktemp("vps_plain"), with_carry=False)


@pytest.fixture(scope="module")
def vps_carried(tmp_path_factory) -> Path:
    """The VPS lineage with the carry applied -- what the host becomes."""
    return _materialise(tmp_path_factory.mktemp("vps_carried"), with_carry=True)


@pytest.fixture(scope="module")
def vps_carried_no_clock(tmp_path_factory) -> Path:
    """The carry landed WITHOUT `broker_clock.py`, i.e. a partial or reordered copy."""
    return _materialise(
        tmp_path_factory.mktemp("vps_noclock"), with_carry=True, with_broker_clock=False
    )


def _run_in_tree(tree: Path, code: str) -> subprocess.CompletedProcess:
    """Execute `code` with `tree` as the import root -- the same thing the VPS does."""
    return subprocess.run(
        [sys.executable, "-c", code], cwd=tree, capture_output=True, text=True
    )


# --------------------------------------------------------------------------------------
# 1. The block itself
# --------------------------------------------------------------------------------------

@requires_lineage
def test_the_carry_introduces_no_import_the_vps_lineage_cannot_satisfy(vps_carried: Path):
    """The A4 audit P ran for broker_clock and not for convergence_advisory.

    Walks the transitive intra-repo import graph of all four carried modules against the
    reconstructed VPS tree. An import that cannot be resolved AND is not inside a `try:` or an
    `if TYPE_CHECKING:` is a module-load failure on the live host.
    """
    root = vps_carried

    def mod_path(mod: str) -> Path | None:
        base = root / mod.replace(".", "/")
        for cand in (base.with_suffix(".py"), base / "__init__.py"):
            if cand.is_file():
                return cand
        return None

    def imported(node: ast.AST, cur: str) -> list[str]:
        if isinstance(node, ast.Import):
            return [a.name for a in node.names]
        if isinstance(node, ast.ImportFrom):
            if node.level:
                parts = cur.split(".")
                base = parts[: -node.level] if node.level <= len(parts) else []
                prefix = ".".join(base + ([node.module] if node.module else []))
                return [prefix] + [f"{prefix}.{a.name}" for a in node.names]
            if node.module:
                return [node.module]
        return []

    def is_guarded(tree: ast.AST, lineno: int) -> bool:
        for n in ast.walk(tree):
            if isinstance(n, (ast.Try, ast.If)):
                for c in ast.walk(n):
                    if isinstance(c, (ast.Import, ast.ImportFrom)) and c.lineno == lineno:
                        return True
        return False

    seeds = [
        "src.components.ultimate_book.book_owner",
        "src.components.ultimate_book.packet_guard",
        "src.components.ultimate_book.packet_economics",
        "src.components.ultimate_book.runtime_learning_packet",
    ]
    seen: set[str] = set()
    unguarded: list[str] = []
    parse_errors: list[str] = []
    stack = list(seeds)
    while stack:
        mod = stack.pop()
        if mod in seen:
            continue
        seen.add(mod)
        path = mod_path(mod)
        if path is None:
            continue
        try:
            # utf-8-sig: at least one VPS module carries a BOM and Python imports it fine.
            # Reading it as plain utf-8 raises SyntaxError and would silently truncate this walk.
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        except SyntaxError as exc:  # pragma: no cover - would be a real lineage defect
            parse_errors.append(f"{mod}: {exc}")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            for name in imported(node, mod):
                if not name.startswith("src."):
                    continue
                if mod_path(name) is not None:
                    stack.append(name)
                    continue
                if mod_path(".".join(name.split(".")[:-1])) is not None:
                    continue  # a symbol inside a module that does exist
                if not is_guarded(tree, node.lineno):
                    unguarded.append(f"{name}  <- {mod}:{node.lineno}")

    assert not parse_errors, f"import walk was truncated, so coverage is unproven: {parse_errors}"
    assert len(seen) > 50, f"import walk only reached {len(seen)} modules; it did not run"
    assert not unguarded, (
        "the carry imports something the VPS lineage does not have, unguarded. This is the "
        f"defect that blocked the carry:\n  " + "\n  ".join(sorted(set(unguarded)))
    )


@requires_lineage
def test_book_owner_does_not_reach_convergence_advisory_on_this_lineage(vps_carried: Path):
    """The specific module that blocked the carry, asserted as a graph property, not a grep."""
    root = vps_carried
    assert not (root / "src/components/ultimate_book/convergence_advisory.py").exists(), (
        "the VPS lineage has grown convergence_advisory.py -- this test's premise changed"
    )
    tree = ast.parse(
        (root / "src/components/ultimate_book/book_owner.py").read_text(encoding="utf-8-sig")
    )
    reached = [
        f"{node.module}:{node.lineno}"
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("convergence_advisory")
    ]
    assert not reached, f"carried book_owner still imports convergence_advisory: {reached}"


@requires_lineage
def test_every_symbol_packet_guard_imports_exists_in_the_carried_emitter(vps_carried: Path):
    """`packet_guard` needs `build_packet_rejected_marker` and `PACKET_ECONOMICS_KEY`, and the
    live emitter has neither. Landing the guard without the emitter is an ImportError."""
    root = vps_carried
    emitter = ast.parse(
        (root / "src/components/ultimate_book/runtime_learning_packet.py").read_text()
    )
    defined: set[str] = set()
    for node in emitter.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Assign):
            defined.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            defined.add(node.target.id)

    guard = ast.parse((root / "src/components/ultimate_book/packet_guard.py").read_text())
    wanted = [
        a.name
        for node in ast.walk(guard)
        if isinstance(node, ast.ImportFrom) and node.module == "runtime_learning_packet"
        for a in node.names
    ]
    assert wanted, "packet_guard stopped importing from the emitter; this test is now vacuous"
    assert not [w for w in wanted if w not in defined], (
        f"packet_guard imports names the carried emitter does not define: "
        f"{[w for w in wanted if w not in defined]}"
    )


# --------------------------------------------------------------------------------------
# 2. Backward compatibility -- 99,112 live packets are the only evidence the programme has
# --------------------------------------------------------------------------------------

_HASH_PROBE = r"""
import json, sys
sys.path.insert(0, ".")
from src.components.ultimate_book.runtime_learning_packet import build_runtime_learning_packet
p = build_runtime_learning_packet(
    namespace="operator_profile",
    event_type="position_managed",
    ts="2026-07-20T12:00:00+00:00",
    bridge={"profile": "clean3_w7_ceiling_nom2p00"},
    outcome={"action": "hold", "placement_status": "managed", "sleeve": "fx_jpy"},
    decision_bar_iso="2026-07-20T11:45:00+00:00",
    decision_day="2026-07-20",
)
print(json.dumps({
    "hash": p.get("packet_hash_sha256"),
    "keys": sorted(p.keys()),
    "has_advisory": "ultimate_convergence_advisory" in p,
    "has_economics": "economics" in p,
}))
"""


@requires_lineage
def test_a_packet_with_no_economics_is_byte_identical_to_what_the_live_book_emits_today(
    vps_plain: Path, vps_carried: Path
):
    """The regression floor. 79 % of the stream is `position_managed` with nothing to cost.

    Those packets must come out of the carried emitter *identical* -- same keys, same hash. If
    the hash moves for a packet whose content did not change, the carry has rewritten the shape
    of the live stream for no information gain. That is precisely what carrying
    `convergence_advisory` would have done: it adds `"ultimate_convergence_advisory": None`
    unconditionally, and `stable_hash` serialises the whole packet.
    """
    before = _run_in_tree(vps_plain, _HASH_PROBE)
    after = _run_in_tree(vps_carried, _HASH_PROBE)
    assert before.returncode == 0, f"VPS emitter failed to run: {before.stderr}"
    assert after.returncode == 0, f"carried emitter failed to run: {after.stderr}"
    b, a = json.loads(before.stdout), json.loads(after.stdout)

    assert a["hash"] == b["hash"], (
        "the carry moved the packet hash for a packet that gained no information.\n"
        f"  live lineage: {b['hash']}\n  after carry:  {a['hash']}\n"
        f"  keys added:   {sorted(set(a['keys']) - set(b['keys']))}"
    )
    assert a["keys"] == b["keys"], f"key set changed: {sorted(set(a['keys']) ^ set(b['keys']))}"
    assert not a["has_advisory"], "the carry reintroduced the convergence-advisory key"
    assert not a["has_economics"], (
        "an empty economics block was attached. An always-present block of nulls is "
        "indistinguishable from one that was never filled -- absence must stay absence."
    )


@requires_lineage
def test_the_emitter_signature_only_grows_optional_keyword_arguments(
    vps_plain: Path, vps_carried: Path
):
    """Every existing VPS call site must keep working untouched."""

    def sig(root: Path) -> ast.arguments:
        tree = ast.parse(
            (root / "src/components/ultimate_book/runtime_learning_packet.py").read_text()
        )
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "build_runtime_learning_packet":
                return node.args
        raise AssertionError("build_runtime_learning_packet not found")

    before, after = sig(vps_plain), sig(vps_carried)
    b_names = [a.arg for a in before.kwonlyargs]
    a_names = [a.arg for a in after.kwonlyargs]
    assert not set(b_names) - set(a_names), (
        f"the carry removed keyword arguments the live book passes: {set(b_names) - set(a_names)}"
    )
    assert not before.args and not after.args, "a positional parameter appeared; call sites break"
    added = [n for n in a_names if n not in b_names]
    for name in added:
        idx = a_names.index(name)
        assert after.kw_defaults[idx] is not None, f"new parameter {name!r} has no default"
    assert added == ["economics"], f"unexpected new parameters: {added}"


CORPUS = Path(
    "/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs"
    "/ultimate_book_runtime_learning_packets.jsonl.gz"
)


@pytest.mark.skipif(not CORPUS.exists(), reason="live packet export not on this machine")
def test_every_historical_packet_still_reproduces_its_own_recorded_hash():
    """Measured, not inferred: all 99,112 live packets must re-hash to what they already carry.

    This is the same check `SCHEMA_VERSION` is deliberately not bumped for -- bumping it would
    fail every historical packet on read and destroy the only live evidence the programme has.
    """
    import gzip

    def stable_hash(value, prefix="ub"):
        text = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(f"{prefix}:{text}".encode("utf-8")).hexdigest()

    total = reproduced = 0
    carries_advisory = 0
    with gzip.open(CORPUS, "rt", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            try:
                packet = json.loads(raw)
            except json.JSONDecodeError:
                continue
            total += 1
            if "ultimate_convergence_advisory" in packet:
                carries_advisory += 1
            body = {k: v for k, v in packet.items() if k != "packet_hash_sha256"}
            if stable_hash(body, "runtime_learning_packet") == packet.get("packet_hash_sha256"):
                reproduced += 1

    assert total > 90_000, f"corpus looks truncated: {total} packets"
    assert reproduced == total, f"{total - reproduced} of {total} packets failed to re-hash"
    assert carries_advisory == 0, (
        f"{carries_advisory} historical packets already carry the advisory key -- the premise "
        "that it is absent on this lineage is wrong"
    )


# --------------------------------------------------------------------------------------
# 3. Failure modes: the carry must degrade, never raise into a live book
# --------------------------------------------------------------------------------------

@requires_lineage
def test_the_carry_survives_a_host_that_never_receives_broker_clock(vps_carried_no_clock: Path):
    """File 1 is optional by construction, so copy order cannot brick the host.

    `broker_clock.py` does not exist on the VPS lineage. If `packet_economics` imported it at
    module scope, the import would propagate through `book_owner` and take both books down.
    """
    probe = (
        "import sys; sys.path.insert(0, '.');"
        "from src.components.ultimate_book import packet_economics as pe;"
        "import src.components.ultimate_book.packet_guard;"
        "print('BROKER_CLOCK_AVAILABLE', pe.BROKER_CLOCK_AVAILABLE)"
    )
    result = _run_in_tree(vps_carried_no_clock, probe)
    assert result.returncode == 0, (
        f"the carry raised on a host with no broker_clock module:\n{result.stderr}"
    )
    assert "BROKER_CLOCK_AVAILABLE False" in result.stdout, result.stdout


@requires_lineage
def test_the_economics_block_refuses_rather_than_guesses_without_a_broker_clock(
    vps_carried_no_clock: Path,
):
    """A missing clock must yield a labelled refusal, never a guessed night count."""
    probe = (
        "import sys, json; sys.path.insert(0, '.');"
        "from src.components.ultimate_book.packet_economics import build_economics_block;"
        "row = {'broker_fill_time_utc': '2026-07-20T21:00:00+00:00',"
        " 'broker_exit_time_utc': '2026-07-22T09:00:00+00:00',"
        " 'action': 'close', 'sleeve': 'fx_jpy'};"
        "print(json.dumps(build_economics_block(row, server='FTMO-Server3')))"
    )
    result = _run_in_tree(vps_carried_no_clock, probe)
    assert result.returncode == 0, result.stderr
    block = json.loads(result.stdout)
    holding = block.get("holding") or {}
    assert holding.get("rollover_nights") is None, (
        f"a night count was produced with no broker clock available: {holding}"
    )
    assert "broker_clock_module_unavailable" in json.dumps(block), (
        f"the refusal is unlabelled, so a reader cannot tell it from a real zero: {block}"
    )


@requires_lineage
def test_the_carried_files_match_their_manifest(vps_carried: Path):
    """The manifest is what the runbook's Get-FileHash step verifies against. If it drifts from
    the files, the operator's only integrity check on a live host silently passes."""
    manifest = json.loads((CARRY / "MANIFEST.json").read_text())
    assert manifest["convergence_advisory_carried"] is False
    assert manifest["vps_base_commit"] == VPS_COMMIT
    for entry in manifest["files"]:
        blob = (REPO / entry["source_in_this_repo"]).read_bytes()
        assert hashlib.sha256(blob).hexdigest() == entry["sha256_after_carry"], (
            f"manifest hash is stale for {entry['destination_on_vps']}"
        )
        assert not entry["crlf_present"], (
            f"{entry['destination_on_vps']} carries CRLF; the hash the operator computes on "
            "Windows will not match unless the transfer preserves bytes exactly"
        )
