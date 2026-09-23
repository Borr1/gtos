#!/usr/bin/env python3
"""Session AT — per-test triage of the standing failure set.

Produces `TEST_TRIAGE_V1.json`: one row per failing test with a bucket, a
disposition, a reason and the authority the disposition rests on.

The two measurements it is built on, because both were wrong before:

1. **Bucket by evidence, not by exception type.** `IMPLEMENTATION_STATE.md` B372
   partitioned the 660 by exception class and put 197 under "code-shaped —
   AssertionError". A large share of those are `assert 0 == 386` where the 0 is a
   ledger that loaded no rows because the file is not on disk. Data absence wearing
   an AssertionError. This classifier reads the failing SOURCE LINE and the reason
   text together, so `assert 0 == N`, bare `StopIteration` from `next(...)` over an
   empty load, and `FileNotFoundError` all land in the same bucket when the cause is
   the same.

2. **Reachability by SYMBOL, not by module.** `run_book.py` imports
   `src.utils.config`, which imports exactly two pure functions out of
   `gtos_vnext_runtime.py`'s 18,090 lines. Module-level reachability calls that whole
   module live and would keep ~300 tests that protect nothing. The closure here walks
   (module, symbol) pairs from the entrypoints **measured running on the VPS**, not
   from the entrypoints one might assume.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# receipts/ -> phase6/ -> fable5-vision-audit-20260725/ -> audits/ -> docs/ -> repo
REPO = Path(__file__).resolve().parents[5]
assert (REPO / "run_book.py").is_file(), f"repo root misresolved: {REPO}"

# ---------------------------------------------------------------------------
# The live surface, measured rather than assumed.
#
# `vps-export-20260725/extracted/27_runtime_snapshot/processes_full.json` lists 17
# python processes on the VPS. Four are `run_book.py` (two per account), two
# `.tools/monitor_books.py`, two `scripts/run_ai_companion_supervisor.py`, two
# `scripts/build_runtime_learning_daily_advisory.py`. **Zero `run_agent.py`.**
# ---------------------------------------------------------------------------
LIVE_ENTRYPOINT_FILES = ["run_book.py", ".tools/monitor_books.py"]

#: The two live processes whose source is NOT in this repository (the live-lineage
#: fork the second audit recorded). Their first-party imports were read from the
#: read-only VPS export at `21_scripts/`; the closure below continues through THIS
#: repo's `src/`, which is an approximation — S measured 25 of 519 shared `src/`
#: files differ by sha256 between the trees (B292).
LIVE_OFFREPO_SEEDS = [
    ("src.components.ai_companion.control_state", "ai_companion_config"),
    ("src.components.ai_companion.supervisor", "AICompanionSupervisor"),
    ("src.components.ultimate_book.runtime_learning_packet", "*"),
]

#: Second lineage: present in the repo, launched by `start_all.bat`, and measured
#: NOT running on the VPS. Tracked separately so a "reachable" claim never blurs the
#: two.
SECONDARY_ENTRYPOINT_FILES = ["run_agent.py"]

FIRST_PARTY = ("src", "scripts", "config", "run_book", "run_agent")


# --------------------------------------------------------------------------- AST
def mod_path(mod: str) -> Path | None:
    rel = mod.replace(".", "/")
    for c in (REPO / f"{rel}.py", REPO / rel / "__init__.py"):
        if c.is_file():
            return c
    return None


def path_mod(p: Path) -> str:
    parts = list(p.relative_to(REPO).parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)


class ModInfo:
    def __init__(self, path: Path):
        self.path = path
        self.mod = path_mod(path)
        self.tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
        self.bindings: dict[str, tuple] = {}
        self.defs: dict[str, ast.AST] = {}
        pkg = self.mod.rsplit(".", 1)[0] if "." in self.mod else ""
        for node in self.tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.defs[node.name] = node
                self.bindings[node.name] = ("local", self.mod, node.name)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        self.defs.setdefault(t.id, node)
                        self.bindings[t.id] = ("local", self.mod, t.id)
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    base = pkg.split(".")
                    base = base[: len(base) - (node.level - 1)] if node.level > 1 else base
                    src = ".".join([*base, node.module]) if node.module else ".".join(base)
                else:
                    src = node.module or ""
                for a in node.names:
                    self.bindings[a.asname or a.name] = ("import", src, a.name)
            elif isinstance(node, ast.Import):
                for a in node.names:
                    self.bindings[a.asname or a.name.split(".")[0]] = ("module", a.name, None)

    @staticmethod
    def names_in(node: ast.AST) -> set[str]:
        out: set[str] = set()
        for n in ast.walk(node):
            if isinstance(n, ast.Name):
                out.add(n.id)
            elif isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
                out.add(f"{n.value.id}.{n.attr}")
        return out


_CACHE: dict[str, ModInfo | None] = {}


def info(mod: str) -> ModInfo | None:
    if mod not in _CACHE:
        p = mod_path(mod)
        try:
            _CACHE[mod] = ModInfo(p) if p else None
        except SyntaxError:
            _CACHE[mod] = None
    return _CACHE[mod]


def resolve(mi: ModInfo, name: str) -> tuple | None:
    if "." in name:
        head, attr = name.split(".", 1)
        b = mi.bindings.get(head)
        if b and b[0] in ("module", "import") and (b[0] == "module" or b[2] is None):
            return (b[1], attr.split(".")[0])
        return None
    b = mi.bindings.get(name)
    if not b:
        return None
    if b[0] == "local":
        return (mi.mod, name)
    if b[0] == "import":
        return (b[1], b[2])
    if b[0] == "module":
        return (b[1], "*")
    return None


def first_party(mod: str) -> bool:
    return mod.split(".")[0] in FIRST_PARTY


def closure(seeds: set[tuple]) -> set[tuple]:
    seen: set[tuple] = set()
    stack = list(seeds)
    while stack:
        mod, sym = stack.pop()
        if (mod, sym) in seen or not first_party(mod):
            continue
        seen.add((mod, sym))
        mi = info(mod)
        if mi is None:
            continue
        if sym == "*":
            stack.extend((mod, n) for n in mi.defs if (mod, n) not in seen)
            continue
        node = mi.defs.get(sym)
        if node is None:
            b = mi.bindings.get(sym)
            if b and b[0] == "import":
                stack.append((b[1], b[2]))
            elif b and b[0] == "module":
                stack.append((b[1], "*"))
            continue
        for nm in ModInfo.names_in(node):
            r = resolve(mi, nm)
            if r and first_party(r[0]) and r not in seen:
                stack.append(r)
    return seen


def entry_seeds(rel: str) -> set[tuple]:
    mi = ModInfo(REPO / rel)
    out = set()
    for nm in ModInfo.names_in(mi.tree):
        r = resolve(mi, nm)
        if r and first_party(r[0]):
            out.add(r)
    return out


# ----------------------------------------------------------------- test indexing
def test_file_modules(test_file: Path) -> set[str]:
    """Every first-party module the FILE imports, however the tests use it.

    Deliberately coarser than the symbol index. `tests/test_sl_beyond_ob_precision_aware.py`
    imports `apply_instrument_overrides` from `src/utils/config.py` -- a live symbol -- at
    module level, but the failing test bodies never name it, so the symbol index scored the
    file zero and the fallback rule proposed deleting a NAS100 precision test. The keep side
    of the rule uses this set instead: coarse in the direction that costs a report line
    rather than coverage.
    """
    try:
        mi = ModInfo(test_file)
    except (SyntaxError, OSError):
        return set()
    out = set()
    for binding in mi.bindings.values():
        if binding[0] in ("import", "module") and first_party(binding[1]):
            out.add(binding[1])
            if binding[0] == "import" and binding[2]:
                sub = f"{binding[1]}.{binding[2]}"
                if mod_path(sub) is not None:
                    out.add(sub)
    return out


def test_symbol_index(test_file: Path) -> dict[str, set[tuple]]:
    """test function name -> first-party (module, symbol) pairs it references."""
    try:
        mi = ModInfo(test_file)
    except (SyntaxError, OSError):
        return {}
    out: dict[str, set[tuple]] = {}

    def collect(node) -> set[tuple]:
        syms = set()
        for nm in ModInfo.names_in(node):
            r = resolve(mi, nm)
            if r and first_party(r[0]):
                syms.add(r)
        return syms

    for node in ast.walk(mi.tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            out[node.name] = collect(node)
    # module-level references (fixtures, constants) count for every test in the file
    module_level = set()
    for node in mi.tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            module_level |= collect(node)
    for k in out:
        out[k] |= module_level
    return out


# -------------------------------------------------------------------- reasons
#: Read the failing source line from the BASE commit, not the worktree.
#:
#: The bucket for `assert 0 == 386` and for a bare `StopIteration` depends on what the
#: failing LINE says -- and once the DELETE rows are applied, those files are gone.
#: Re-running the classifier afterwards silently reclassified 27 rows from
#: `absent_data_as_stopiteration` to `code_other`, because `next(` could no longer be
#: found in a file that no longer exists. The artifact must describe the failure set as
#: it WAS, so the source comes from `git show <base>:<path>` whenever the worktree copy
#: is missing. Set `AT_TRIAGE_BASE` to pin the ref; defaults to HEAD.
_BASE_REF = "AT_TRIAGE_BASE"
_SRC_CACHE: dict[str, list[str] | None] = {}


def _source_lines(path: str) -> list[str] | None:
    if path in _SRC_CACHE:
        return _SRC_CACHE[path]
    import os

    p = Path(path)
    text: str | None = None
    ref = os.environ.get(_BASE_REF)
    if ref:
        # Always prefer the ref, never the worktree. Deleting 188 functions out of a
        # 20,623-line file does not remove it -- it RENUMBERS it, so reading line 14738
        # from the current copy returns unrelated code and buckets the row on a lie.
        # Absence was only the visible half of this bug.
        try:
            rel = p.resolve().relative_to(REPO).as_posix()
        except ValueError:
            rel = None
        if rel:
            out = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=REPO,
                                 capture_output=True, text=True)
            text = out.stdout if out.returncode == 0 else None
    if text is None and p.is_file():
        text = p.read_text(encoding="utf-8", errors="replace")
    _SRC_CACHE[path] = text.splitlines() if text is not None else None
    return _SRC_CACHE[path]


def parse_reasons(jsonl: Path) -> dict[str, dict]:
    """nodeid -> {reason, where, where_src} from the `at_reasons_plugin` JSONL.

    Do NOT go back to parsing `-q --tb=line` stdout for this. pytest truncates the
    short-summary line to terminal width, so long node ids come back cut off; pairing
    the traceback lines against them by index misattributed the reason on **461 of
    665** rows (69%) when it was tried here. The plugin reads the report objects, so
    nodeid and longrepr cannot drift apart.
    """
    out: dict[str, dict] = {}
    for line in jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        where = rec.get("where")
        where_src = None
        if where and ":" in where:
            path, _, lineno = where.rpartition(":")
            src = _source_lines(path)
            if src is not None:
                try:
                    where_src = src[int(lineno) - 1].strip()[:200]
                except (IndexError, ValueError):
                    where_src = None
        prev = out.get(rec["id"])
        # setup failures and call failures can both fire; keep the first, which is the
        # one that actually stopped the test.
        if prev is None:
            out[rec["id"]] = {
                "reason": (rec.get("reason") or "").strip(),
                "where": (Path(where.rpartition(":")[0]).name + ":" + where.rpartition(":")[2])
                         if where and ":" in where else None,
                "where_src": where_src,
                "when": rec.get("when"),
            }
    return out


_MISSING_PATH = re.compile(r"((?:research|data|shadow_logs|pipeline_state)[\\/][^\s'\"\),]+)")


def bucket_for(reason: str, where_src: str | None) -> tuple[str, str | None]:
    """Bucket by the CAUSE, which is often not the exception class.

    `assert 0 == 386` is not a code failure when the 0 is a ledger that loaded no rows
    because the file is not on disk; `StopIteration` from `next(r for r in rows ...)`
    over that same empty load is the same failure again. B372 counted both as
    code-shaped.
    """
    r = reason or ""
    src = where_src or ""
    m = _MISSING_PATH.search(r) or _MISSING_PATH.search(src)
    path = m.group(1).replace("\\", "/").rstrip("'\"") if m else None
    if "ModuleNotFoundError" in r or "ImportError" in r:
        return "absent_dependency", path
    if "FileNotFoundError" in r or "No such file" in r:
        return "absent_data", path
    if "JSONDecodeError" in r or "Expecting value" in r or "Extra data" in r:
        return "absent_data_unparseable", path
    if re.search(r"missing_paths=\(", r):
        return "absent_data_as_assertion", path
    if re.search(r"assert 0 == [1-9]", r) or re.search(r"assert \[\] ==", r) or \
       re.search(r"assert Counter\(\) ==", r) or re.search(r"^assert not \[", r) or \
       re.search(r"assert \{\} ==", r):
        return "absent_data_as_assertion", path
    if "StopIteration" in r:
        return ("absent_data_as_stopiteration" if ("next(" in src or "next (" in src)
                else "code_other"), path
    if "AssertionError" in r or r.lstrip().startswith("assert"):
        return "code_assertion", path
    return "code_other", path


# ---------------------------------------------------------------------------
# Supersession table. `CLAUDE.md` §8 permits deleting stale pollution **after
# proof** -- so every DELETE row must name the authority that superseded its route,
# not assert that one exists. Each entry below is a (prefix, status, authority) the
# reader can check.
# ---------------------------------------------------------------------------
ROUTE_AUTHORITY: list[tuple[str, str, str]] = [
    ("research/operations/final_moonshot_market_expansion_", "ABSENT_FROM_MAINLINE",
     "the route is not in HEAD at all (`git ls-tree -r HEAD research/operations/ | grep "
     "market_expansion` -> 0). It exists only on the VPS lineage, last touched by "
     "96f53b63d 'vps: package conditioned expansion parity'. A mainline test cannot guard "
     "an artifact mainline has never carried; git history is the archive (CLAUDE.md §8)."),
    ("research/operations/final_moonshot_candidate_", "ABSENT_FROM_MAINLINE",
     "as above -- absent from HEAD, VPS lineage only (96f53b63d)."),
    ("research/operations/replay_acceleration_", "PARKED_RESUMABLE",
     "the B7.5 campaign is PARKED WITH A PRICE and banked (CLAUDE.md §4): ~36 machine-hours "
     "to finish, and the option expires at the first bound-file edit. Its tests still guard "
     "a resumable asset, so they are skipped with the hydration path named, not deleted."),
    ("research/operations/final_moonshot_b7_5_", "PARKED_RESUMABLE",
     "B7.5 campaign, parked with a price (CLAUDE.md §4). Not superseded."),
    ("research/operations/final_moonshot_ultimate_system_denominator_to_deployment", "COLD_DEMOTED",
     "cold-demoted 2026-07-26 (CLAUDE.md §4, B53) and explicitly load-bearing BY ABSENCE -- "
     "two REPLAY_EXTENSION_* paths there must stay missing. Never delete or hydrate blind."),
    ("research/operations/vnext_absolute_moonshot_selector_v3", "SUPERSEDED",
     "Selector V3 is `false`/default-off (CLAUDE.md §4)."),
    ("research/operations/vnext_absolute_moonshot_scheduler_v3", "SUPERSEDED",
     "Scheduler V3 is `false`/default-off (CLAUDE.md §4)."),
    ("research/science_program_2026_05/", "SUPERSEDED",
     "the live decision surface is the `ultimate_book` W7 book, not the vNext research-to-"
     "runtime engine these ledgers feed (CLAUDE.md §4; `.context/00_core/"
     "live_system_of_record.md` 2026-06-16, which states it overrides any config or doc that "
     "disagrees). MEASURED: the engine's entry points are called only from "
     "`src/components/orchestrator.py`, which is reachable only from `run_agent.py` -- and "
     "the VPS runtime snapshot lists 17 python processes with ZERO `run_agent.py` "
     "(`vps-export-20260725/extracted/27_runtime_snapshot/processes_full.json`)."),
    ("research/a2_v2_active_backtest", "HISTORICAL", "CLAUDE.md §10 -- A2-V2 era is historical."),
    ("research/program_control/", "HISTORICAL",
     "CLAUDE.md §10 -- 'old program-control reports ... are not current authority'."),
    ("research/ml_program/", "HISTORICAL",
     "CLAUDE.md §10; the ML program predates the W7 book and no current artifact labels it active."),
    ("research/academic_pipeline", "HISTORICAL", "CLAUDE.md §10 -- pre-book research era."),
    ("research/phase_3_external_feed_validation", "HISTORICAL", "CLAUDE.md §10 -- pre-book research era."),
    ("research/instrument_expansion_2026-04-25", "HISTORICAL", "CLAUDE.md §4/§10 -- April-era."),
    ("research/lira_ab_backtest", "HISTORICAL", "CLAUDE.md §10 -- pre-book research era."),
    ("research/t7_live_simulation", "HISTORICAL", "CLAUDE.md §10 -- pre-book research era."),
    ("research/rejected_candidates_value_mining", "HISTORICAL", "CLAUDE.md §10 -- pre-book research era."),
    ("research/accepted_candidates_loser_mining", "HISTORICAL", "CLAUDE.md §10 -- pre-book research era."),
    ("research/pre_ai_gate_optimization", "HISTORICAL", "CLAUDE.md §10 -- pre-book research era."),
    ("research/kap_outputs", "HISTORICAL", "CLAUDE.md §10 -- pre-book research era."),
    ("research/diagnostics", "HISTORICAL", "CLAUDE.md §10 -- pre-book research era."),
    ("research/a1_adr005_backtest", "HISTORICAL", "CLAUDE.md §4 -- April/WF-1 era is historical."),
    ("research/f3_backtest_", "HISTORICAL", "CLAUDE.md §4 -- April-era backtest."),
    ("research/t2_1_", "HISTORICAL", "CLAUDE.md §4 -- April-era study."),
    ("research/t3_2_", "HISTORICAL", "CLAUDE.md §4 -- April-era study."),
    ("research/b_deep_audit_", "HISTORICAL", "CLAUDE.md §4 -- April-era audit."),
    ("research/q62_", "HISTORICAL", "CLAUDE.md §4 -- April-era study."),
]

#: Third-party packages that are simply not installed here. Absence of an optional
#: dependency is an environment fact, not a defect in the test -- `importorskip` is
#: the repair, and it is durable where a sparse-checkout hydration is not.
OPTIONAL_DEPENDENCIES = ("sentence_transformers", "fastapi", "pytest_asyncio", "mplfinance",
                         "torch", "sklearn", "statsmodels", "plotly", "seaborn", "uvicorn")


#: Per-file authority for failures that name no research path -- code-shaped failures
#: whose subject has to be judged on reachability instead. Filled in by hand, one
#: entry per file, because "this test protects nothing" is a claim and each one needs
#: its own evidence.
FILE_AUTHORITY: dict[str, tuple[str, str]] = {
    "tests/test_gtos_vnext_master_conversion_ledger.py": ("SUPERSEDED",
     "subject is `scripts/build_gtos_vnext_master_conversion_ledger.py`. MEASURED: it "
     "contributes ZERO symbols to the live closure from either entrypoint -- nothing the "
     "live book or the legacy agent runs imports it. Its ledgers are science_program_2026_05 "
     "(superseded; see the route table). Hydrating what it reads costs 1,657 MB."),
    "tests/test_gtos_vnext_runtime.py": ("SUPERSEDED",
     "MEASURED: `run_book.py` reaches exactly EIGHT symbols of this 18,090-line module, all of "
     "them symbol-key normalisation, through `src/utils/config.py:12`. None of the failing "
     "tests references any of the eight; the 15 prop-safe-selector tests and the other 192 in "
     "this file PASS and are untouched. The failing tests drive `evaluate_vnext_route_event` "
     "and the CP281/moonshot rule enrichers, whose only caller is "
     "`src/components/orchestrator.py:2196,2413,8581,8777` -- reachable only from "
     "`run_agent.py`, which the VPS runtime snapshot shows is NOT running."),
    "tests/test_wave4r_v4_vs_v3_frozen_replay_results_gate.py": ("SUPERSEDED",
     "V4-vs-V3 frozen replay gate. `CLAUDE.md` §4: Selector V3 and Scheduler V3 are "
     "`false`/default-off, and Selector/Scheduler V4 run with `live_activation_allowed: "
     "false` so `permissions.py:930` returns None for every candidate. MEASURED: zero "
     "overlap with the live module set, let alone the live symbol set."),
    "tests/test_j46_j49_policy.py": ("HISTORICAL",
     "`CLAUDE.md` §4 names J46/J49 explicitly as historical."),
    "tests/test_vnext_broader_origin_orchestrator.py": ("SUPERSEDED",
     "asserts on `v3_package_authority_*` states; V3 is `false`/default-off (`CLAUDE.md` §4)."),
    "tests/test_wave3_5_v4_authority_activation.py": ("SUPERSEDED",
     "V4 authority activation; V4 holds no live authority (`CLAUDE.md` §4)."),
    "tests/research_infra/test_scheduler_v4_learned_ranking.py": ("SUPERSEDED",
     "Scheduler V4 learned ranking; V4 `live_activation_allowed: false` (`CLAUDE.md` §4)."),
    "tests/test_moonshot_candidate_quality_selector.py": ("SUPERSEDED",
     "the broad moonshot selector, superseded by the `ultimate_book` W7 book as the live "
     "decision surface (`CLAUDE.md` §4)."),
    "tests/test_analyze_b7_5_extended_history_behavior.py": ("PARKED_RESUMABLE",
     "B7.5 extended-history analysis; the campaign is parked with a price, not superseded."),
    "tests/test_b7_5_extended_history_source_window_contract.py": ("PARKED_RESUMABLE",
     "B7.5 source-window contract; campaign parked with a price, not superseded."),
    "tests/test_b7_5_neutral_selection_factorial.py": ("PARKED_RESUMABLE",
     "B7.5 neutral-selection factorial; campaign parked with a price, not superseded."),
    "tests/test_b7_5_post_acceleration_contract.py": ("PARKED_RESUMABLE",
     "asserts the decision contract's own input-drift guard -- the H1 mechanism itself. "
     "Never delete this one; it is the alarm."),
}


#: Collection errors -- the module never imports, so pytest reports ONE id for the whole
#: file and there is no per-test row to reason about. The generic rules mis-handle them
#: twice over: the delete tool has no function node to remove, and the conftest skip hook
#: cannot mark an item that was never collected. Each is therefore decided by hand, and
#: NONE of them is a deletion: a module that fails to import is hiding every test it
#: defines, and the count of what is hidden is the finding.
ID_OVERRIDES: dict[str, tuple[str, str]] = {
    "tests/research_infra/test_moonshot_unified_execution_scorer.py": ("KEEP-REAL",
     "**223 tests that have never once collected.** The module imports "
     "`aggregate_reduction_rows` from `src/research_infra/moonshot_expanded_market_leakage_"
     "reduction.py`, and that name has never existed there in ANY revision -- `git log -S` "
     "finds it only in the commit that added this test file (f3e0dc3a1). The sibling import "
     "`aggregate_execution_rows` is missing from its module too, so this is an unwritten API "
     "surface, not a rename. Deliberately NOT deleted: retiring 223 tests on one probe is a "
     "bigger claim than this session measured, and the repair (write the two functions, or "
     "cut the imports and see what the 223 actually assert) is a well-specified next task."),
    "tests/test_retest_geometry_study.py": ("HYDRATE",
     "**95 tests** dark behind one absent module. `research/retest_geometry` is COMMITTED in "
     "HEAD (45 files) and simply not in the sparse profile. `git sparse-checkout add "
     "/research/retest_geometry/` restores them."),
    "tests/test_vnext_ftmo_local_profile_and_vps_dual_prod_prep.py": ("HYDRATE",
     "2 tests dark behind an absent module. "
     "`research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02` is "
     "COMMITTED in HEAD (29 files) and not in the sparse profile."),
    "tests/test_vnext_moonshot_lane10_portfolio_scheduler_v2.py": ("KEEP-REAL",
     "7 tests dark: `ModuleNotFoundError: No module named 'portfolio_scheduler_v2'`. The name "
     "is unqualified, so this is an import-path defect in the test rather than absent data."),
    "tests/test_chart_renderer.py": ("SKIP-WITH-REASON",
     "collection error from an uninstalled optional dependency. NOTE: the conftest hook cannot "
     "reach it -- `pytest_collection_modifyitems` only sees items that collected, and this "
     "module never does. It needs `pytest.importorskip` at the top of the file to go quiet."),
    "tests/test_a1_analyze.py": ("HYDRATE",
     "18 tests dark behind `research/a1_adr005_backtest/analyze.py`, read at module import. "
     "April-era route (CLAUDE.md §4, historical) -- hydratable, but nothing current consumes "
     "it, so hydrating is optional and deleting would need the per-test look this session did "
     "not get to do on a module that cannot import."),
    "tests/test_vnext_absolute_moonshot_lane16_historical_microscope_scale.py": ("HYDRATE",
     "3 tests dark behind an absent route artifact read at module import."),
    "tests/test_vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design.py": ("HYDRATE",
     "5 tests dark behind an absent route artifact read at module import "
     "(`research/operations/vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_"
     "design_*`). Same shape as lane16 and scheduler_v3 below."),
    "tests/test_vnext_absolute_moonshot_scheduler_v3.py": ("HYDRATE",
     "6 tests dark behind an absent route artifact read at module import. Scheduler V3 is "
     "`false`/default-off (CLAUDE.md §4), so the route is superseded and these are the "
     "cheapest possible deletion candidates for a follow-up -- but the module must import "
     "before anyone can say what its 6 tests assert."),
}

#: Whole test-file families whose authority follows from the file name. Kept separate
#: from FILE_AUTHORITY so the pattern -- and therefore the blast radius of the rule --
#: is visible rather than repeated 12 times.
FILE_PREFIX_AUTHORITY: list[tuple[str, str, str]] = [
    ("tests/test_replay_acceleration_", "PARKED_RESUMABLE",
     "B7.5 replay-acceleration infrastructure. The campaign is PARKED WITH A PRICE and "
     "banked (CLAUDE.md §4) -- ~36 machine-hours to finish, and the option expires at the "
     "first bound-file edit. Deleting its harness would quietly convert a priced option "
     "into a dead one, so these are skipped with the input named, not retired."),
    ("tests/test_mc_firm_rules", "CURRENT",
     "Session Q's Monte Carlo at each firm's MEASURED prop rules is a wave-4 deliverable "
     "cited in CLAUDE.md §4 (`MC_FIRM_TRUE_V1.json`). Current, not superseded."),
]


def route_status(path: str | None) -> tuple[str | None, str | None]:
    if not path:
        return None, None
    for prefix, status, authority in ROUTE_AUTHORITY:
        if path.startswith(prefix):
            return status, authority
    return None, None


def file_status(file_part: str) -> tuple[str | None, str | None]:
    if file_part in FILE_AUTHORITY:
        return FILE_AUTHORITY[file_part]
    for prefix, status, authority in FILE_PREFIX_AUTHORITY:
        if file_part.startswith(prefix):
            return status, authority
    return None, None


def main() -> int:
    scratch = Path(sys.argv[1])          # dir holding failset json + reasons log
    failset = json.loads((scratch / sys.argv[2]).read_text())
    reasons = parse_reasons(scratch / sys.argv[3])
    out_path = Path(sys.argv[4])

    ids = sorted(set(failset["failed"]) | set(failset["errored"])) \
        if isinstance(failset, dict) else sorted(set(failset))

    live = set()
    for f in LIVE_ENTRYPOINT_FILES:
        live |= closure(entry_seeds(f))
    live |= closure(set(LIVE_OFFREPO_SEEDS))
    live_modules = {m for m, _ in live}
    secondary = set()
    for f in SECONDARY_ENTRYPOINT_FILES:
        if (REPO / f).is_file():
            secondary |= closure(entry_seeds(f))

    tracked = set(subprocess.run(["git", "ls-files", "research/"], cwd=REPO,
                                 capture_output=True, text=True).stdout.split())

    sym_index: dict[str, dict[str, set[tuple]]] = {}
    file_mods: dict[str, set[str]] = {}
    rows = []
    for nid in ids:
        file_part = nid.split("::")[0]
        func = nid.split("::")[-1].split("[")[0] if "::" in nid else None
        tf = REPO / file_part
        if file_part not in sym_index:
            sym_index[file_part] = test_symbol_index(tf) if tf.is_file() else {}
            file_mods[file_part] = test_file_modules(tf) if tf.is_file() else set()
        syms = sym_index[file_part].get(func, set())
        if not syms:  # class-based test: fall back to the union for the file
            syms = set().union(*sym_index[file_part].values()) if sym_index[file_part] else set()
        r = reasons.get(nid, {"reason": "", "where": None, "where_src": None})
        bucket, mpath = bucket_for(r["reason"], r["where_src"])
        live_hits = sorted(f"{m}::{s}" for m, s in (syms & live))
        sec_hits = sorted(f"{m}::{s}" for m, s in (syms & secondary))
        status, authority = route_status(mpath)
        if status is None:
            status, authority = file_status(file_part)
        dep = next((d for d in OPTIONAL_DEPENDENCIES if d in (r["reason"] or "")), None)
        if dep is None and "not natively supported" in (r["reason"] or ""):
            dep = "pytest_asyncio"
        live_mod_overlap = (file_mods.get(file_part, set()) | {m for m, _ in syms}) & live_modules

        if nid in ID_OVERRIDES:
            disp, why = ID_OVERRIDES[nid]
        elif live_hits and bucket.startswith("absent_data"):
            disp, why = "HYDRATE", (
                f"exercises live code ({live_hits[0]}) and is blocked only by an absent file "
                f"that IS committed in HEAD" if mpath in tracked else
                f"exercises live code ({live_hits[0]}); its input is absent and not in HEAD")
        elif live_hits and dep:
            disp, why = "SKIP-WITH-REASON", (
                f"optional dependency `{dep}` is not installed; the test itself is sound")
        elif live_hits:
            disp, why = "KEEP-REAL", (
                f"code-shaped failure on a path the live book reaches ({live_hits[0]})")
        elif dep:
            disp, why = "SKIP-WITH-REASON", (
                f"optional dependency `{dep}` is not installed; nothing about the test is wrong")
        elif status == "CURRENT":
            disp, why = "KEEP-REAL", authority
        elif status in ("PARKED_RESUMABLE", "COLD_DEMOTED"):
            disp, why = "SKIP-WITH-REASON", authority
        elif status in ("SUPERSEDED", "HISTORICAL", "ABSENT_FROM_MAINLINE"):
            disp, why = "DELETE", authority
        elif live_mod_overlap:
            # No symbol the live book reaches, but the test's subject MODULE is one the
            # live book loads. Symbol-level reachability is an under-approximation --
            # dynamic dispatch and getattr are invisible to it -- so this band is kept
            # and reported rather than deleted. Erring here costs a line in a report;
            # erring the other way removes coverage from a module the armed book imports.
            disp, why = "KEEP-REAL", (
                f"no live SYMBOL, but the subject module is loaded by the live book "
                f"({sorted(live_mod_overlap)[:3]}); symbol-level reachability is an "
                f"under-approximation, so this is reported, not retired")
        else:
            disp, why = "DELETE", (
                f"MEASURED unreachable: none of the {len(syms)} first-party symbols this test "
                f"references is in the live closure ({len(live)} (module,symbol) pairs from "
                f"run_book.py + .tools/monitor_books.py + the two VPS-only entrypoints), and "
                f"no module it imports is loaded by the live book either")
        rows.append({
            "id": nid,
            "file": file_part,
            "bucket": bucket,
            "disposition": disp,
            "reason_for_disposition": why,
            "route_status": status,
            "failure_reason": r["reason"][:300],
            "where": r["where"],
            "where_src": r["where_src"],
            "missing_path": mpath,
            "missing_path_committed": (mpath in tracked) if mpath else None,
            "live_symbols": live_hits[:8],
            "live_symbol_count": len(live_hits),
            "secondary_symbol_count": len(sec_hits),
        })
    out_path.write_text(json.dumps({
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase6/receipts/at_triage.py",
        "live_entrypoints_measured": LIVE_ENTRYPOINT_FILES + [
            "scripts/run_ai_companion_supervisor.py (VPS-only source)",
            "scripts/build_runtime_learning_daily_advisory.py (VPS-only source)"],
        "live_symbol_pairs": len(live),
        "secondary_symbol_pairs": len(secondary),
        "rows": rows,
    }, indent=1) + "\n")
    print(f"{len(rows)} rows -> {out_path}")
    from collections import Counter
    print(Counter(r["bucket"] for r in rows).most_common())
    print("rows touching a LIVE symbol:", sum(1 for r in rows if r["live_symbol_count"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
