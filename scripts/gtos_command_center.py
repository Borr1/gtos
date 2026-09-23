#!/usr/bin/env python3
"""gtos_command_center.py — the whole live system on ONE page, from a read-only host export.

READ-ONLY, and structurally so: this file imports no broker module, opens no socket, writes no
config, and contains no order-sending code path. It reads files someone else produced from a
read-only VPS export, cross-checks them against each other, and prints a page. It cannot arm,
disarm, resize, flatten, or restart anything. Every action it can ever recommend is a ceremony the
orchestrator performs and the owner authorises.

    python3 scripts/gtos_command_center.py --export-root /path/to/vps-export-YYYYMMDD/extracted

Everything is optional. What is missing reports UNCHECKED and exits 3 — never 0. "Nothing is wrong"
and "nothing was checked" are different states, and collapsing them is how `.tools/monitor_books.py`
sat mute through the window it was meant to be watching.

Exit codes, matching `canary_watch.py` and `book_sleeve_telemetry.py` so all three sit behind the
same thing:  0 clean · 1 a WARN, ALERT or STOP · 3 clean, but something could not be checked.

--------------------------------------------------------------------------------------------------
WHY THIS EXISTS WHEN TWO OPERATOR PAGES ALREADY DO

`canary_watch.py` answers *is it armed, is it alive, what is the headroom, is the cost model still
right*. `book_sleeve_telemetry.py` answers *what is each armed sleeve doing, has any reached its
line*. Both are correct and both are kept — this page composes the second one rather than restating
it (see `_sleeve_panel`).

What neither could do is the thing that actually goes wrong, because both ask the OPERATOR for the
two answers that matter most:

  * `canary_watch.py --launch-tags` and `book_sleeve_telemetry.py --launch-tags-ftmo` take the armed
    set as a STRING THE OPERATOR TYPES. The tool then checks the operator's belief against the
    expectation. In the failure mode the check exists for — the operator misremembers, or reads a
    `.ps1` on disk that a running worker was not launched from — the check passes while the book
    trades a different set. It is a tautology exactly where it needs to be a measurement.
  * `canary_watch.py --account-state` takes equity, balance and the drawdown floor the same way, as
    a hand-written JSON blob.

The export already contains both, as machine-readable facts:

  * `27_runtime_snapshot/processes_full.json` carries the **running worker's full command line**,
    which is where `--tags` actually lives (`run_book.py:340-343`);
  * `05_shadow_logs/ultimate_book_launcher.jsonl` carries, every cycle, the sleeve set and the
    authority gates **as the running process resolved them** (`launcher.py:337-346`);
  * `09_mt5_api/*_account_info.json` carries equity, balance and the broker's own account identity.

So this page takes the operator out of the evidence path for those checks and puts three
INDEPENDENT reads of the armed set beside each other. Agreement is the signal; disagreement is the
alarm. That is the contribution, and it is the reason the page is worth a third tool.

--------------------------------------------------------------------------------------------------
THE TRAP IN THE LAUNCHER LOG, MEASURED — read this before trusting the `tags` field

`launcher.py:328` builds a cycle record's `tags` as

    tags = tuple(t for tf in advanced for t in self._tf_tags[tf])

— the tags **whose decision timeframe advanced on that tick**, NOT the armed set. `_tf_tags` is the
whole resolved book grouped by timeframe (`:106-108`); a tick that only advances H4 emits only the
H4 sleeves.

Measured on the 2026-07-25 export (5,237 cycle records over 2026-06-18..07-25):

    last cycle record   FTMO 22 tags · redacted_account 10 tags
    union over the log  FTMO 32      · redacted_account 32

A page that read the last record and called it "the armed set" would under-report redacted_account by
3.2x — and under-reporting is the FAIL-OPEN direction wearing a clean read's clothes, because a
smaller set looks safer. So this file takes the **union over a window**, and refuses to call that
union complete unless every decision timeframe present in the window actually advanced inside it
(`_armed_set_from_launcher`). When a timeframe never advanced, the count is published as a LOWER
BOUND and says so.

Second half of the same trap, in the other direction: the launcher's `_active_specs` does **not**
apply the DF-1 filter at `book_engine.py:452-453`, so its union is the pre-DF-1 candidate set — 32
where only 29 can generate under `include_clean3: false`. The union OVER-reports what can fire by
exactly the sleeves the engine drops. Both errors are named on the page rather than silently
reconciled, because the reconciliation depends on a config flag whose live value is itself one of
the things being checked.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# `scripts/` is deliberately NOT put on sys.path, and neither appending nor ordering fixes it.
# `research/` at the repo root is a NAMESPACE package (no __init__.py); `scripts/research/` is a
# REGULAR one (it has an __init__.py). Python's finder lets a regular package win over namespace
# portions **regardless of sys.path position**, so merely having `scripts/` anywhere on the path
# makes `import research.operations...` fail for the rest of the process.
#
# A first cut inserted `scripts/` at position 0 and silently turned two passing tests in
# `test_defect_register_repairs.py` into SKIPS (they use `pytest.importorskip`). Appending it
# instead did not help, for the reason above. Sibling modules are therefore loaded by FILE PATH —
# the same pattern `tests/ultimate_book/test_book_sleeve_telemetry.py` already uses — which has no
# global side effect at all.


def _load_sibling(name: str):
    """Import a module from `scripts/` by path, without touching `sys.path`."""
    import importlib.util
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {name} from scripts/")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

AUDIT = REPO / "docs/audits/fable5-vision-audit-20260725"
FIRM_RULES = REPO / "research/operations/broker_truth_layer_2026_07_27/FIRM_RULES_V1.json"
DEFAULT_CONDITIONS = AUDIT / "phase11/receipts/FIVE_SLEEVE_STOP_CONDITIONS_V1.json"
DEFAULT_BASIS = AUDIT / "phase11/receipts/AS_LIVE_SLEEVE_BASIS_V1.json"
DEFAULT_QUIET_BASIS = AUDIT / "phase15/receipts/CH_QUIET_BOOK_THRESHOLDS_V1.json"

#: namespace -> the account name the rest of the estate uses. The namespaces are read off the live
#: workers' own command lines in the export; they are stable identifiers, not guesses.
NAMESPACE_ACCOUNT = {
    "operator_profile": "FTMO",
    "redacted_account_live_bee34003": "redacted_account",
}
ACCOUNTS = ("FTMO", "redacted_account")
EXPORT_KEY = {"FTMO": "ftmo", "redacted_account": "redacted_account"}

#: The profile each live worker is launched with (`run_book_supervisor.ps1:86-87`). Panel 6 needs
#: it to build the canonical->broker resolver the book itself uses.
ACCOUNT_PROFILE = {"FTMO": "operator_profile", "redacted_account": "redacted_account"}

CLEAN, UNCHECKED, WARN, ALERT, STOP = "CLEAN", "UNCHECKED", "WARN", "ALERT", "STOP"
_RANK = {CLEAN: 0, UNCHECKED: 1, WARN: 2, ALERT: 3, STOP: 4}

GATE_KEYS = (
    "ultimate_book_enabled",
    "ultimate_book_apply_to_execution",
    "ultimate_book_live_activation_allowed",
    "ultimate_book_live_broker_authority",
)

#: The three sleeves `book_engine.py:452-453` (DF-1) drops when `include_clean3` is false. Named
#: here so the launcher union's over-report is quantified rather than hand-waved.
CLEAN3_SLEEVES = ("sub_mid_dn_revert", "sub_xvol_pullback", "vp_euidx_pocgrav")


class Finding:
    __slots__ = ("panel", "level", "scope", "text", "why")

    def __init__(self, panel, level, scope, text, why=""):
        self.panel, self.level, self.scope = panel, level, scope
        self.text, self.why = text, why

    def as_dict(self):
        return {"panel": self.panel, "level": self.level, "scope": self.scope,
                "text": self.text, "why": self.why}


# ---------------------------------------------------------------------------
# small readers
# ---------------------------------------------------------------------------
def _open(path: Path):
    return gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" \
        else open(path, "r", encoding="utf-8")


def read_jsonl(path: Path | None) -> list[dict]:
    if path is None or not path.is_file():
        return []
    rows = []
    with _open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return rows


def read_json(path: Path | None):
    """JSON, tolerating the UTF-8 BOM PowerShell's ``ConvertTo-Json`` writes.

    Not a nicety: every file the VPS export produced through PowerShell carries one, and
    ``json.load`` raises on it. A reader that dies on the BOM would report the entire runtime
    snapshot as absent — which reads as "nothing to see" rather than "I could not look".
    """
    if path is None or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError):
        return None


def parse_utc(value):
    if not value:
        return None
    s = str(value).strip().replace("Z", "+00:00")
    try:
        d = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def parse_dotnet_date(value):
    """``/Date(1783151881890)/`` -> aware UTC datetime. PowerShell's JSON date format."""
    if not value:
        return None
    m = re.search(r"/Date\((-?\d+)", str(value))
    if not m:
        return parse_utc(value)
    return dt.datetime.fromtimestamp(int(m.group(1)) / 1000.0, dt.timezone.utc)


def _age_hours(then, now):
    if then is None or now is None:
        return None
    return (now - then).total_seconds() / 3600.0


# ---------------------------------------------------------------------------
# the export
# ---------------------------------------------------------------------------
class Export:
    """A VPS export directory. Every accessor returns None/[] rather than raising.

    Accepts either the `extracted/` directory or its parent — the archives on this machine are
    unpacked both ways and a tool that only understands one of them fails on the day it is needed.
    """

    def __init__(self, root: Path | None):
        self.root = None
        self.missing: list[str] = []
        if root is None:
            return
        root = Path(root).expanduser()
        for cand in (root, root / "extracted"):
            if (cand / "09_mt5_api").is_dir() or (cand / "27_runtime_snapshot").is_dir():
                self.root = cand
                break
        if self.root is None:
            self.missing.append(f"{root} does not look like a VPS export "
                                f"(no 09_mt5_api/ or 27_runtime_snapshot/ under it)")

    def path(self, *parts) -> Path | None:
        if self.root is None:
            return None
        p = self.root.joinpath(*parts)
        return p if p.exists() else None

    def first(self, *candidates) -> Path | None:
        for parts in candidates:
            p = self.path(*parts)
            if p is not None:
                return p
        return None

    # -- individual surfaces ------------------------------------------------
    def account_info(self, account):
        return read_json(self.path("09_mt5_api", f"{EXPORT_KEY[account]}_account_info.json"))

    def terminal_info(self, account):
        return read_json(self.path("09_mt5_api", f"{EXPORT_KEY[account]}_terminal_info.json"))

    def positions(self, account):
        return read_jsonl(self.path("09_mt5_api", f"{EXPORT_KEY[account]}_positions_get.jsonl"))

    def pending(self, account):
        return read_jsonl(self.path("09_mt5_api", f"{EXPORT_KEY[account]}_orders_get_pending.jsonl"))

    def deals(self, account):
        return read_jsonl(self.path("09_mt5_api", f"{EXPORT_KEY[account]}_history_deals_get.jsonl"))

    def processes(self):
        return read_json(self.path("27_runtime_snapshot", "processes_full.json")) or []

    def kill_flags(self):
        return read_json(self.path("01_flags_and_safety", "KILL_FLAG_PROBE.json"))

    def launcher_log(self) -> Path | None:
        return self.first(("05_shadow_logs", "ultimate_book_launcher.jsonl.gz"),
                          ("05_shadow_logs", "ultimate_book_launcher.jsonl"))

    def config(self) -> Path | None:
        return self.path("03_config", "agent_config.yaml")

    def pull_summary(self):
        return read_json(self.path("09_mt5_api", "_MT5_PULL_SUMMARY.json"))

    def symbols(self, account) -> list[dict]:
        """The broker's own answer to `symbols_get()` — the tree the book must resolve into."""
        return read_jsonl(self.path("09_mt5_api", f"{EXPORT_KEY[account]}_symbols_get.jsonl"))

    def profile(self, name) -> Path | None:
        """The profile AS THE HOST CARRIES IT. Falls back to this repo's copy, and the panel says
        which it used — a repo profile is a claim about the host, not a reading of it."""
        return self.path("03_config", "profiles", f"{name}.yaml")


def runtime_block(config_path: Path | None) -> tuple[dict, str | None]:
    """The config sub-dict carrying the ultimate_book keys, whatever its nesting.

    Same shape as `canary_watch.runtime_block`; duplicated rather than imported because importing
    `canary_watch` pulls `src.safety.activation_token` at module scope on some paths, and this page
    must remain runnable when the token layer is not importable.
    """
    if config_path is None:
        return {}, "no config in this export"
    try:
        import yaml
        loaded = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {}, f"{type(exc).__name__}: {exc}"

    def find(node):
        if isinstance(node, dict):
            if "ultimate_book_enabled" in node:
                return node
            for value in node.values():
                got = find(value)
                if got is not None:
                    return got
        return None

    block = find(loaded)
    if block is None:
        return {}, "no ultimate_book_enabled key anywhere in this config"
    return block, None


# ---------------------------------------------------------------------------
# PANEL 1 — the armed set, read three independent ways
# ---------------------------------------------------------------------------
def _tags_from_cmdline(cmdline: str) -> tuple[list[str] | None, str]:
    """Extract `--tags` from a worker command line.

    Returns (tags, state) where state is one of:
      absent        no --tags at all -> the book runs the WHOLE include-flag registry (fail-open)
      empty         --tags "" -> falsy at run_book.py:340, ALSO the whole registry (fail-open)
      present       a real list
    """
    m = re.search(r'--tags[=\s]+("([^"]*)"|\'([^\']*)\'|(\S+))', cmdline)
    if not m:
        return None, "absent"
    raw = m.group(2) if m.group(2) is not None else \
        (m.group(3) if m.group(3) is not None else (m.group(4) or ""))
    tags = [t.strip() for t in raw.split(",") if t.strip()]
    return (tags, "present") if tags else ([], "empty")


def workers_from_processes(export: Export, now) -> dict:
    """Every running `run_book.py` worker, keyed by namespace.

    A worker's `--tags` is the ONLY mechanism that bounds the book (`run_book.py:340-343`), and the
    command line of the running process is the only place it can be observed after the fact — the
    `.ps1` on disk records what a FUTURE launch would do, which is a different question and has
    been the wrong answer at least once (B327: the committed supervisor passes none).
    """
    out: dict[str, dict] = {}
    for proc in export.processes():
        if not isinstance(proc, dict):
            continue
        cl = str(proc.get("CommandLine") or "")
        if "run_book.py" not in cl or str(proc.get("Name", "")).lower() != "python.exe":
            continue
        ns = None
        m = re.search(r"--namespace[=\s]+\"?([A-Za-z0-9_\-]+)", cl)
        if m:
            ns = m.group(1)
        tags, state = _tags_from_cmdline(cl)
        started = parse_dotnet_date(proc.get("CreationDate"))
        row = out.setdefault(ns or "(unknown)", {"pids": [], "tags": tags, "tags_state": state,
                                                 "cmdlines": set(), "started_utc": None,
                                                 "max_working_set_bytes": 0})
        row["pids"].append(proc.get("ProcessId"))
        row["cmdlines"].add(cl)
        row["max_working_set_bytes"] = max(row["max_working_set_bytes"],
                                           int(proc.get("WorkingSetSize") or 0))
        if started and (row["started_utc"] is None or started < row["started_utc"]):
            row["started_utc"] = started
        # If two workers for one namespace disagree on --tags, that is itself the finding.
        if row["tags_state"] != state or (row["tags"] or []) != (tags or []):
            row["tags_disagree"] = True
    for ns, row in out.items():
        row["cmdlines"] = sorted(row["cmdlines"])
        row["n_processes"] = len(row["pids"])
        row["uptime_hours"] = _age_hours(row["started_utc"], now)
        row["started_utc"] = row["started_utc"].isoformat() if row["started_utc"] else None
    return out


def _armed_set_from_launcher(rows: list[dict], window_hours: float, now) -> dict:
    """The union of cycle `tags` over a window, plus the validity condition for calling it complete.

    See the module docstring: a single cycle record is the tags whose TIMEFRAME ADVANCED, so the
    union is the only honest read — and the union is only complete over a window in which every
    decision timeframe advanced at least once. That condition is CHECKED here rather than assumed,
    and when it fails the count is published as a lower bound.
    """
    per_ns: dict[str, dict] = {}
    cutoff = now - dt.timedelta(hours=window_hours) if now else None
    for r in rows:
        if r.get("action") != "cycle":
            continue
        ns = r.get("namespace") or "(unknown)"
        ts = parse_utc(r.get("ts"))
        blk = per_ns.setdefault(ns, {
            "union_all_time": set(), "union_window": set(), "tf_all_time": set(),
            "tf_window": set(), "n_cycles_all_time": 0, "n_cycles_window": 0,
            "last_ts": None, "first_ts": None, "last_record_tag_count": None,
            "min_tag_count_window": None, "max_tag_count_window": None,
        })
        tags = set(r.get("tags") or [])
        tfs = set(r.get("advanced_tf") or [])
        blk["union_all_time"] |= tags
        blk["tf_all_time"] |= tfs
        blk["n_cycles_all_time"] += 1
        if ts and (blk["last_ts"] is None or ts > blk["last_ts"]):
            blk["last_ts"] = ts
            blk["last_record_tag_count"] = len(tags)
        if ts and (blk["first_ts"] is None or ts < blk["first_ts"]):
            blk["first_ts"] = ts
        if cutoff is None or (ts is not None and ts >= cutoff):
            blk["union_window"] |= tags
            blk["tf_window"] |= tfs
            blk["n_cycles_window"] += 1
            n = len(tags)
            blk["min_tag_count_window"] = n if blk["min_tag_count_window"] is None \
                else min(blk["min_tag_count_window"], n)
            blk["max_tag_count_window"] = n if blk["max_tag_count_window"] is None \
                else max(blk["max_tag_count_window"], n)

    out = {}
    for ns, blk in per_ns.items():
        # The completeness condition. `tf_all_time` is the best available estimate of the book's
        # declared timeframe set from the log alone; if the window did not see all of them, sleeves
        # at the unseen timeframes cannot be in the window union.
        missing_tf = sorted(blk["tf_all_time"] - blk["tf_window"])
        out[ns] = {
            "union_window": sorted(blk["union_window"]),
            "n_union_window": len(blk["union_window"]),
            "union_all_time": sorted(blk["union_all_time"]),
            "n_union_all_time": len(blk["union_all_time"]),
            "timeframes_seen_all_time": sorted(blk["tf_all_time"]),
            "timeframes_seen_in_window": sorted(blk["tf_window"]),
            "timeframes_missing_from_window": missing_tf,
            "union_is_complete": not missing_tf and blk["n_cycles_window"] > 0,
            "n_cycles_window": blk["n_cycles_window"],
            "n_cycles_all_time": blk["n_cycles_all_time"],
            "last_cycle_utc": blk["last_ts"].isoformat() if blk["last_ts"] else None,
            "first_cycle_utc": blk["first_ts"].isoformat() if blk["first_ts"] else None,
            "last_record_tag_count": blk["last_record_tag_count"],
            "per_record_tag_count_range_in_window":
                [blk["min_tag_count_window"], blk["max_tag_count_window"]],
        }
    return out


def armed_panel(export, launcher_rows, workers, cfg, cfg_error, expect_tags,
                window_hours, now) -> tuple[dict, list[Finding]]:
    """Three independent reads of what the book is authorised to trade, cross-checked."""
    findings: list[Finding] = []
    by_ns = _armed_set_from_launcher(launcher_rows, window_hours, now)
    panel = {"window_hours": window_hours, "expected_tags": sorted(expect_tags or []),
             "per_account": {}, "config_error": cfg_error}

    for ns, account in NAMESPACE_ACCOUNT.items():
        launcher = by_ns.get(ns)
        worker = workers.get(ns)
        row: dict = {"namespace": ns, "reads": {}, "state": UNCHECKED}

        # -- read A: the running worker's own command line -------------------
        if worker is None:
            row["reads"]["worker_cmdline"] = {"state": UNCHECKED,
                                              "reason": "no running run_book.py worker for this "
                                                        "namespace in the export's process list"}
        else:
            st = worker["tags_state"]
            row["reads"]["worker_cmdline"] = {
                "state": CLEAN if st == "present" else STOP,
                "tags_state": st, "tags": worker["tags"],
                "n_processes": worker["n_processes"],
                "uptime_hours": worker["uptime_hours"],
                "started_utc": worker["started_utc"],
                "meaning": {
                    "absent": "NO --tags on the command line: the book runs the WHOLE include-flag "
                              "registry, not a bounded set. Fail-open, and every log reads healthy.",
                    "empty": "--tags \"\" is falsy at run_book.py:340 and means ALL BUILT sleeves. "
                             "Fail-open, and it looks like a deliberate restriction.",
                    "present": "a bounded set, as intended",
                }[st],
            }
            if st in ("absent", "empty"):
                findings.append(Finding(
                    "ARMED", STOP, account,
                    f"the running worker has NO effective --tags ({st}) — it is trading the whole "
                    f"registry, not a bounded set",
                    "run_book.py:340 treats an empty --tags as falsy and falls back to every BUILT "
                    "sleeve. Nothing else on this page means anything until this is right. Read the "
                    "launch command on the host with your own eyes before believing any figure."))
            if worker.get("tags_disagree"):
                findings.append(Finding(
                    "ARMED", STOP, account,
                    "two running workers for this namespace were launched with DIFFERENT --tags",
                    "Two books on one account under two contracts. Which one placed a given order "
                    "is not recoverable from the fill alone."))

        # -- read B: the launcher log's own resolved set ---------------------
        if launcher is None:
            row["reads"]["launcher_union"] = {"state": UNCHECKED,
                                              "reason": "no launcher cycle records for this "
                                                        "namespace"}
        else:
            complete = launcher["union_is_complete"]
            row["reads"]["launcher_union"] = {
                "state": CLEAN if complete else UNCHECKED,
                "n_sleeves": launcher["n_union_window"],
                "sleeves": launcher["union_window"],
                "is_lower_bound": not complete,
                "timeframes_missing_from_window": launcher["timeframes_missing_from_window"],
                "last_record_tag_count": launcher["last_record_tag_count"],
                "per_record_tag_count_range_in_window":
                    launcher["per_record_tag_count_range_in_window"],
                "caveat": "the UNION over the window, never a single record — launcher.py:328 "
                          "emits only the tags whose timeframe advanced that tick. This union is "
                          "also PRE-DF-1: book_engine.py:452-453 drops the clean_3 sleeves when "
                          "ultimate_book_include_clean3 is false, so it over-reports what can fire "
                          "by up to three.",
            }
            if not complete and launcher["n_cycles_window"] > 0:
                findings.append(Finding(
                    "ARMED", UNCHECKED, account,
                    f"the launcher union over the last {window_hours:.0f} h is a LOWER BOUND: "
                    f"timeframe(s) {launcher['timeframes_missing_from_window']} never advanced "
                    f"inside the window",
                    "Sleeves whose decision timeframe did not advance cannot appear in the union. "
                    "Widen --window-hours past one bar of the slowest timeframe (D1 needs > 24 h, "
                    "and more across a weekend)."))
            # The single-record trap, quantified for this export rather than asserted.
            lo, hi = launcher["per_record_tag_count_range_in_window"]
            if lo is not None and hi is not None and lo != hi:
                row["reads"]["launcher_union"]["single_record_would_have_said"] = \
                    f"between {lo} and {hi} depending which tick you read; the union says " \
                    f"{launcher['n_union_window']}"

        # -- read C: the config's include flags ------------------------------
        if cfg_error:
            row["reads"]["config_flags"] = {"state": UNCHECKED, "reason": cfg_error}
        else:
            flags = {k: cfg.get(k, "ABSENT") for k in (
                "ultimate_book_include_clean3", "ultimate_book_include_clean4",
                "ultimate_book_include_candidate_book",
                "ultimate_book_include_market_expansion_book")}
            row["reads"]["config_flags"] = {"state": CLEAN, "flags": flags,
                                            "note": "the config on disk in the export. It bounds "
                                                    "what --tags can intersect; it can never ADD a "
                                                    "sleeve --tags left out."}

        # -- the cross-check -------------------------------------------------
        row.update(_cross_check(row, expect_tags, launcher, account, findings))
        panel["per_account"][account] = row
    return panel, findings


def _cross_check(row, expect_tags, launcher, account, findings) -> dict:
    """Compare the reads against each other and against the expected armed set."""
    worker = row["reads"].get("worker_cmdline") or {}
    lu = row["reads"].get("launcher_union") or {}
    out: dict = {"cross_check": {}}
    wt = worker.get("tags")
    exp = sorted(expect_tags or [])

    if exp and wt is not None and worker.get("tags_state") == "present":
        ok = sorted(wt) == exp
        out["cross_check"]["worker_vs_expected"] = {
            "state": CLEAN if ok else STOP, "observed": sorted(wt), "expected": exp}
        if not ok:
            findings.append(Finding(
                "ARMED", STOP, account,
                f"the running worker's --tags {sorted(wt)} is not the expected armed set {exp}",
                "This is the measurement the two older operator pages could only ask the operator "
                "to type. It is read off the running process, so it cannot be a misremembering."))
    elif exp:
        out["cross_check"]["worker_vs_expected"] = {
            "state": UNCHECKED, "reason": "no usable --tags read from a running worker"}

    # The launcher union should be a SUPERSET of the worker's --tags (the launcher resolves
    # --tags against the include flags, then emits per-timeframe subsets of the result).
    if wt and lu.get("sleeves") is not None and lu.get("state") == CLEAN:
        extra = sorted(set(wt) - set(lu["sleeves"]))
        out["cross_check"]["worker_subset_of_launcher"] = {
            "state": CLEAN if not extra else ALERT,
            "tagged_but_never_seen_generating": extra}
        if extra:
            findings.append(Finding(
                "ARMED", ALERT, account,
                f"{extra} appear in --tags but never appeared in a launcher cycle over the window",
                "A tag the engine cannot resolve is dropped silently (registry.py:144 drops unknown "
                "tags with no fallback and no error), and a clean_3 sleeve is dropped by DF-1 when "
                "ultimate_book_include_clean3 is false. Either way the sleeve is not trading and "
                "nothing says so."))
    if lu.get("state") == CLEAN and not wt:
        out["cross_check"]["worker_subset_of_launcher"] = {
            "state": UNCHECKED, "reason": "no --tags to compare"}

    states = [b.get("state") for b in list(row["reads"].values())
              + list(out["cross_check"].values()) if isinstance(b, dict)]
    row_state = CLEAN
    for s in states:
        if s and _RANK.get(s, 0) > _RANK[row_state]:
            row_state = s
    out["state"] = row_state
    return out


# ---------------------------------------------------------------------------
# PANEL 2 — the accounts: equity, headroom, distance to target, positions
# ---------------------------------------------------------------------------
def _firm_rules() -> tuple[dict, str | None]:
    d = read_json(FIRM_RULES)
    if d is None:
        return {}, f"firm rules artifact missing: {FIRM_RULES}"
    return d, None


def _detect_phase(product: str | None) -> tuple[int | None, str]:
    """Phase from the broker's own product string, with the evidence quoted.

    Guessing the phase silently would be the worst kind of error on this page: phase 1 and phase 2
    have DIFFERENT profit targets at both firms, so a wrong phase moves distance-to-target by
    thousands of dollars while every other number stays right.
    """
    if not product:
        return None, "no product string in the export's account_info"
    p = product.lower()
    if re.search(r"\bp2\b|phase\s*2|step\s*2\b", p):
        return 2, f"from the broker's own product string {product!r}"
    if re.search(r"\bp1\b|phase\s*1", p):
        return 1, f"from the broker's own product string {product!r}"
    if "2-step" in p or "2 step" in p:
        return 1, (f"product {product!r} names the PROGRAMME (2-Step) but not the current phase; "
                   f"assuming phase 1 — override with --phase if the account has advanced")
    return None, f"could not read a phase from product {product!r}"


#: MT5 deal types that are a real market trade. 2 is DEAL_TYPE_BALANCE (the "Initial account
#: balance" row and every credit/withdrawal), which carries an empty symbol and is not a trading day.
_TRADE_DEAL_TYPES = (0, 1)


def _trading_days(export, account, server, window_note, findings) -> dict:
    """Distinct TRADING days in the export's deal history, on the FIRM's own reset calendar.

    Three things this has to get right, and a first cut got all three wrong by taking `str(time)[:10]`
    of a field that is an epoch INTEGER — which made every deal at a distinct second look like a
    distinct day and reported 240 trading days over a 33-day history.

    1. `time` is a broker-clock epoch, converted with `broker_clock.broker_epoch_to_utc`, which
       fails closed on an unregistered server rather than guessing (never hardcode +3; the two
       calendars disagree ~4 weeks a year).
    2. A "trading day" is a day with a real market deal. Balance operations are excluded.
    3. Both firms define the day on their OWN reset calendar — FTMO 00:00 CE(S)T, redacted_account 00:00
       server time — not on UTC. A UTC count is a different number and would be wrong at the edges.
    """
    out: dict = {}
    deals = export.deals(account)
    if not deals:
        out["trading_days_state"] = UNCHECKED
        out["trading_days_reason"] = "no deal history in this export"
        return out
    try:
        from src.utils.broker_clock import (UnknownBrokerClockError, daily_reset_offset_hours,
                                            resolve_rule)
        rule = resolve_rule(server)
    except UnknownBrokerClockError as exc:
        out["trading_days_state"] = UNCHECKED
        out["trading_days_reason"] = f"broker clock fails closed for server {server!r}: {exc}"
        findings.append(Finding(
            "ACCOUNTS", UNCHECKED, account,
            f"trading-day count UNCHECKED — no clock rule for server {server!r}",
            "broker_clock fails closed rather than guessing. A wrong day boundary is invisible "
            "until it decides whether a phase requirement was met."))
        return out
    except Exception as exc:  # noqa: BLE001
        out["trading_days_state"] = UNCHECKED
        out["trading_days_reason"] = f"broker clock unavailable: {exc!r}"
        return out

    from src.utils.broker_clock import broker_epoch_to_utc
    reset_rule = {"FTMO": "CE(S)T"}.get(account)   # redacted_account resets at server midnight
    days_firm, days_utc, first, last = set(), set(), None, None
    for d in deals:
        if d.get("type") not in _TRADE_DEAL_TYPES or not d.get("symbol"):
            continue
        t = d.get("time")
        if t is None:
            continue
        try:
            inst = broker_epoch_to_utc(float(t), rule)
        except Exception:  # noqa: BLE001
            continue
        first = inst if first is None or inst < first else first
        last = inst if last is None or inst > last else last
        days_utc.add(inst.date().isoformat())
        off = daily_reset_offset_hours(inst, reset_rule) if reset_rule else None
        if off is None:
            # redacted_account: the firm day IS the server day, so the broker-wall date is the key.
            days_firm.add((inst + dt.timedelta(
                seconds=_offset_seconds(inst, rule))).date().isoformat())
        else:
            days_firm.add((inst + dt.timedelta(hours=off)).date().isoformat())
    out.update({
        "trading_days_state": CLEAN,
        "distinct_trading_days_in_export": len(days_firm),
        "distinct_trading_days_utc": len(days_utc),
        "trading_day_calendar": reset_rule or f"server midnight ({server})",
        "deal_history_span_utc": [first.isoformat() if first else None,
                                  last.isoformat() if last else None],
        "minimum_trading_days_window": window_note,
        "minimum_trading_days_note": (
            "counted over the WHOLE deal history in this export, not the current phase — the "
            "export carries no phase boundary, so read it as an upper bound on progress toward "
            "the requirement, never as satisfaction of it. Balance operations are excluded; the "
            "day boundary is the firm's own reset calendar, not UTC."),
    })
    return out


def _offset_seconds(inst, rule):
    from src.utils.broker_clock import offset_seconds_at_utc
    try:
        return offset_seconds_at_utc(inst, rule)
    except Exception:  # noqa: BLE001
        return 0


def accounts_panel(export, args, now) -> tuple[dict, list[Finding]]:
    findings: list[Finding] = []
    rules, rules_err = _firm_rules()
    panel = {"firm_rules_artifact": str(FIRM_RULES), "firm_rules_error": rules_err,
             "per_account": {}}
    if rules_err:
        findings.append(Finding("ACCOUNTS", UNCHECKED, "both",
                                "firm rules artifact is missing; headroom and distance-to-target "
                                "cannot be computed", rules_err))

    for account in ACCOUNTS:
        info = export.account_info(account)
        term = export.terminal_info(account)
        row: dict = {"state": UNCHECKED}
        if info is None:
            row["reason"] = ("no account_info in this export — equity, headroom and "
                             "distance-to-target are UNCHECKED, not clear")
            panel["per_account"][account] = row
            findings.append(Finding("ACCOUNTS", UNCHECKED, account,
                                    "no account state in the export",
                                    "Every economic figure on this row is unavailable. This is not "
                                    "a clean bill."))
            continue

        equity = info.get("equity")
        balance = info.get("balance")
        row.update({
            "login": info.get("login"), "product": info.get("name"),
            "server": info.get("server"), "company": info.get("company"),
            "currency": info.get("currency"),
            "balance": balance, "equity": equity,
            "open_pl": info.get("profit"),
            "margin_used": info.get("margin"), "margin_free": info.get("margin_free"),
            "trade_allowed_account": info.get("trade_allowed"),
            "trade_expert": info.get("trade_expert"),
            "provenance": "[MEASURED] 09_mt5_api/*_account_info.json — the broker's own numbers, "
                          "not an operator input",
        })
        if term:
            row.update({"terminal_connected": term.get("connected"),
                        "terminal_trade_allowed": term.get("trade_allowed"),
                        "terminal_build": term.get("build"),
                        "terminal_ping_ms": term.get("ping_last")})
            if term.get("connected") is False:
                findings.append(Finding("ACCOUNTS", ALERT, account, "terminal reports NOT connected",
                                        "No orders can be placed or managed while the link is down."))
            if term.get("trade_allowed") is False:
                findings.append(Finding(
                    "ACCOUNTS", STOP, account, "terminal reports trade_allowed = false",
                    "The broker or the terminal has disabled algorithmic trading. Exit management "
                    "stops too, which is the half that costs money."))

        positions = export.positions(account)
        pending = export.pending(account)
        row["n_open_positions"] = len(positions)
        row["n_pending_orders"] = len(pending)
        row["open_positions"] = [
            {"ticket": p.get("ticket"), "symbol": p.get("symbol"), "volume": p.get("volume"),
             "type": p.get("type"), "price_open": p.get("price_open"), "sl": p.get("sl"),
             "tp": p.get("tp"), "profit": p.get("profit"), "swap": p.get("swap"),
             "magic": p.get("magic"), "comment": p.get("comment"),
             "time_utc": p.get("time")} for p in positions]
        # A position with no broker-side stop is the one open-position fact that changes what an
        # operator does, so it is surfaced rather than left in the table.
        naked = [p for p in positions if not p.get("sl")]
        if naked:
            findings.append(Finding(
                "ACCOUNTS", ALERT, account,
                f"{len(naked)} open position(s) carry NO broker-side stop loss",
                "H8's consolation — that a gated position still rides the broker SL/TP set at entry "
                "(execution.py:3488) — does not apply to a position that has no SL at the broker."))

        firm = (rules.get("firms") or {}).get(account) or {}
        frules = firm.get("rules") or {}
        initial = firm.get("initial_balance_usd")
        phase, phase_why = (args.phase, "supplied with --phase") if args.phase \
            else _detect_phase(info.get("name"))
        row["phase"] = phase
        row["phase_provenance"] = phase_why

        if initial and equity is not None:
            # --- overall drawdown floor -------------------------------------
            mo = frules.get("max_overall_loss_pct") or {}
            floor = mo.get("floor_usd")
            if floor is None and mo.get("value") is not None:
                floor = float(initial) * (1.0 - float(mo["value"]) / 100.0)
            if floor is not None:
                row["static_dd_floor_usd"] = floor
                row["static_headroom_usd"] = float(equity) - float(floor)
                row["static_headroom_pct_of_initial"] = \
                    (float(equity) - float(floor)) / float(initial) * 100.0
                row["max_dd_basis"] = mo.get("kind") or "unstated"
                row["max_dd_coverage"] = mo.get("coverage")
                if mo.get("coverage") != "MEASURED":
                    row["max_dd_caveat"] = (
                        f"the max-DD BASIS for {account} is {mo.get('coverage')} "
                        f"({mo.get('provenance_kind')}), not a captured page. If it is TRAILING "
                        f"rather than static, this floor rises with every new equity peak and the "
                        f"headroom above is an over-statement.")
                    findings.append(Finding(
                        "ACCOUNTS", UNCHECKED, account,
                        f"max-DD basis is {mo.get('coverage')}, not MEASURED — the headroom figure "
                        f"assumes a STATIC floor",
                        row["max_dd_caveat"]))

            # --- today's daily allowance ------------------------------------
            md = frules.get("max_daily_loss_pct") or {}
            if md.get("value") is not None:
                allowance = float(initial) * float(md["value"]) / 100.0
                row["daily_allowance_usd"] = allowance
                row["daily_allowance_denominator"] = md.get("denominator")
                row["daily_reset"] = md.get("reset")
                if args.day_start_equity and account in args.day_start_equity:
                    ds = float(args.day_start_equity[account])
                    used = max(0.0, ds - float(equity))
                    row["day_start_equity"] = ds
                    row["daily_used_usd"] = used
                    row["daily_fraction_consumed"] = used / allowance if allowance else None
                    if allowance and used / allowance > 0.5:
                        findings.append(Finding(
                            "ACCOUNTS", ALERT, account,
                            f"{used / allowance:.0%} of today's daily-loss allowance is used "
                            f"(${used:,.0f} of ${allowance:,.0f})", ""))
                else:
                    row["daily_used_usd"] = None
                    row["daily_note"] = (
                        "today's CONSUMED daily loss needs the day-start equity on this firm's own "
                        "reset calendar, which no export field carries. Supply "
                        "--day-start-equity ACCOUNT=VALUE, or read it off the terminal. The "
                        "ALLOWANCE above is a firm rule and is exact.")

            # --- distance to the phase target -------------------------------
            pt = frules.get("profit_target_pct") or {}
            tgt_pct = pt.get(f"phase{phase}") if phase else None
            if tgt_pct is not None:
                target_equity = float(initial) * (1.0 + float(tgt_pct) / 100.0)
                row["phase_target_pct"] = tgt_pct
                row["phase_target_equity_usd"] = target_equity
                row["distance_to_target_usd"] = target_equity - float(equity)
                row["distance_to_target_pct_of_initial"] = \
                    (target_equity - float(equity)) / float(initial) * 100.0
                row["profit_target_coverage"] = pt.get("coverage")
            elif phase:
                row["phase_target_note"] = f"no phase{phase} target in the firm rules artifact"

            # --- minimum trading days: a pass condition nothing else tracks ---
            mtd = frules.get("minimum_trading_days") or {}
            if mtd.get("value") is not None:
                row["minimum_trading_days_required"] = mtd["value"]
                row.update(_trading_days(export, account, info.get("server"),
                                         mtd.get("window"), findings))

        row["state"] = CLEAN
        panel["per_account"][account] = row
    return panel, findings


# ---------------------------------------------------------------------------
# PANEL 3 — authority: gates as the process resolved them, flags, tokens
# ---------------------------------------------------------------------------
def authority_panel(export, launcher_rows, cfg, cfg_error, args, now
                    ) -> tuple[dict, list[Finding]]:
    findings: list[Finding] = []
    panel: dict = {"per_account": {}, "kill_flags": None, "token": None}

    # the last `bridge` block per namespace: the gates AS THE RUNNING PROCESS RESOLVED THEM.
    last_bridge: dict[str, dict] = {}
    last_bridge_ts: dict[str, dt.datetime] = {}
    for r in launcher_rows:
        if r.get("action") != "cycle" or not r.get("bridge"):
            continue
        ns = r.get("namespace") or "(unknown)"
        ts = parse_utc(r.get("ts"))
        if ts and (ns not in last_bridge_ts or ts > last_bridge_ts[ns]):
            last_bridge_ts[ns], last_bridge[ns] = ts, r["bridge"]

    for ns, account in NAMESPACE_ACCOUNT.items():
        row: dict = {"namespace": ns}
        br = last_bridge.get(ns)
        if br is None:
            row["resolved_gates"] = {"state": UNCHECKED,
                                     "reason": "no launcher bridge block for this namespace"}
        else:
            gates = {
                "ultimate_book_enabled": br.get("enabled"),
                "ultimate_book_apply_to_execution": br.get("apply_to_execution"),
                "ultimate_book_live_activation_allowed": br.get("live_activation_allowed_by_config"),
                "ultimate_book_live_broker_authority": br.get("live_broker_authority"),
            }
            row["resolved_gates"] = {
                "state": CLEAN, "gates": gates,
                "as_of_utc": last_bridge_ts[ns].isoformat(),
                "runtime_effect_now": br.get("runtime_effect_now"),
                "decision_status": br.get("decision_status"),
                "profile": br.get("profile"),
                "include_clean3": br.get("include_clean3"),
                "include_candidate_book": br.get("include_candidate_book"),
                "include_market_expansion_book": br.get("include_market_expansion_book"),
                "provenance": "[MEASURED] the gates the RUNNING worker resolved, from its own "
                              "launcher record — not the config file on disk. When the two "
                              "disagree, the process is right and the file is what a restart "
                              "would apply.",
            }
            row["armed_by_gates"] = bool(br.get("live_activation_allowed_by_config")
                                         and br.get("live_broker_authority"))

        # config-on-disk, and the disagreement between it and the process
        if cfg_error:
            row["config_gates"] = {"state": UNCHECKED, "reason": cfg_error}
        else:
            cg = {k: ("ABSENT" if k not in cfg else cfg[k]) for k in GATE_KEYS}
            row["config_gates"] = {"state": CLEAN, "gates": cg,
                                   "note": "ABSENT is printed as ABSENT, never as false — "
                                           "rendering absence as false makes a fresh clone look "
                                           "like the live host."}
            if br is not None:
                dis = {k: {"process": row["resolved_gates"]["gates"].get(k), "config_file": cg.get(k)}
                       for k in GATE_KEYS
                       if row["resolved_gates"]["gates"].get(k) != cg.get(k)}
                row["gate_disagreement"] = dis
                if dis:
                    findings.append(Finding(
                        "AUTHORITY", ALERT, account,
                        f"the running worker and the config file on disk disagree on "
                        f"{sorted(dis)}",
                        "The process is authoritative for what is happening NOW; the file is what "
                        "the next restart applies. A restart would silently change authority."))
        panel["per_account"][account] = row

    # kill / halt flags
    kf = export.kill_flags()
    if kf is None:
        panel["kill_flags"] = {"state": UNCHECKED, "reason": "no KILL_FLAG_PROBE.json in export"}
    else:
        present = [f for f in kf if f.get("exists")]
        panel["kill_flags"] = {"state": CLEAN, "probed": len(kf),
                               "present": [{"path": f.get("relative_path"),
                                            "mtime_utc": f.get("mtime_utc")} for f in present],
                               "note": "absence of a kill flag is the NORMAL running state; it is "
                                       "not a brake. The brake is the gates plus the activation "
                                       "token."}
        for f in present:
            findings.append(Finding(
                "AUTHORITY", ALERT, "host",
                f"flag present on the host: {f.get('relative_path')} "
                f"(mtime {f.get('mtime_utc')})",
                "A kill or halt flag is a deliberate operator act. If it was not yours, treat it "
                "as an incident; if it was, the book is not trading and the quiet panel below will "
                "look like a silent book rather than a stopped one."))

    # activation tokens — local dir only; the host's tokens live on the host
    panel["token"] = _token_panel(args, now, findings)
    return panel, findings


def _token_panel(args, now, findings) -> dict:
    """Token expiries, read from a token directory this machine can see.

    Deliberately honest about scope: the tokens that authorise the LIVE books live on the VPS, in
    `$GTOS_ACTIVATION_TOKEN_DIR` or `~/.gtos/activation`, and are outside every export by design
    (the whole point of the token layer is that it is not in the repo). So on this laptop this panel
    is UNCHECKED unless the operator points `--token-dir` at a directory that actually holds them.
    Reporting "no token" as an alert here would cry wolf on every laptop run.
    """
    out: dict = {"token_dir": args.token_dir}
    if not args.token_dir:
        out.update({"state": UNCHECKED,
                    "reason": "no --token-dir supplied. The live books' tokens are on the VPS, "
                              "outside every export by design. Expiry is UNCHECKED here — read it "
                              "on the host with scripts/gtos_activation_token.py list."})
        return out
    try:
        from src.safety import activation_token as at
    except Exception as exc:  # noqa: BLE001
        out.update({"state": UNCHECKED, "reason": f"activation_token not importable: {exc!r}"})
        return out
    tokens = []
    d = Path(args.token_dir).expanduser()
    if not d.is_dir():
        out.update({"state": UNCHECKED, "reason": f"{d} is not a directory"})
        return out
    for p in sorted(d.glob("*.token.json")):
        raw = read_json(p)
        if not raw:
            continue
        exp = parse_utc(raw.get("expires_utc"))
        hours = _age_hours(now, exp)
        tokens.append({"file": p.name,
                       "account_login_sha256": raw.get("account_login_sha256"),
                       "expires_utc": raw.get("expires_utc"),
                       "hours_until_expiry": hours,
                       "expired": (hours is not None and hours < 0)})
        if hours is not None and 0 <= hours < float(args.token_expiry_alert_hours):
            findings.append(Finding(
                "AUTHORITY", ALERT, raw.get("account_login_sha256", "?")[:12],
                f"activation token expires in {hours:.1f} h ({raw.get('expires_utc')})",
                "An expired token cannot strand a position — risk-reducing requests never need one "
                "— but the book stops being able to OPEN. Re-mint before it lapses if the book is "
                "meant to keep trading."))
        if hours is not None and hours < 0:
            findings.append(Finding(
                "AUTHORITY", ALERT, raw.get("account_login_sha256", "?")[:12],
                f"activation token EXPIRED {abs(hours):.1f} h ago ({raw.get('expires_utc')})",
                "Exposure-increasing requests are refused. Closes, partial closes and stop "
                "tightenings still pass — the token layer never strands a position."))
    out.update({"state": CLEAN if tokens else UNCHECKED, "tokens": tokens,
                "signature_verified": False,
                "note": "expiry is read from the token file's own `expires_utc`. This page does "
                        "NOT verify the HMAC — a hand-edited expiry would read as valid here and "
                        "be refused by the engine. Verification is "
                        "scripts/gtos_activation_token.py's job, on the host that holds the key."})
    if not tokens:
        out["reason"] = f"no *.token.json under {d}"
    return out


# ---------------------------------------------------------------------------
# PANEL 4 — liveness and the abnormally-quiet alarm
# ---------------------------------------------------------------------------
def liveness_panel(export, launcher_rows, workers, args, now) -> tuple[dict, list[Finding]]:
    """Alive and quiet are DIFFERENT questions and are never merged.

    *Alive* is the cycle stream: a book that stopped emitting is broken. *Quiet* is fills: a book
    that emits every tick and fills nothing is, for this estate, NORMAL — roughly 7 book-days a
    month. Merging them is how a stopped book hides behind "well, it is a quiet strategy".
    """
    findings: list[Finding] = []
    panel: dict = {"per_account": {}, "quiet_basis": None}

    quiet_basis = read_json(Path(args.quiet_basis)) if args.quiet_basis else None
    if quiet_basis is None:
        panel["quiet_basis"] = {
            "state": UNCHECKED,
            "reason": "no --quiet-basis artifact. Session CH measured separate current-set "
                      "weekday-session thresholds for both accounts; pass or restore its "
                      "gtos.live.quiet_basis.v1 receipt rather than substituting a literal.",
            "expected_schema": QUIET_BASIS_SCHEMA,
        }
    else:
        panel["quiet_basis"] = {"state": CLEAN, "artifact": str(args.quiet_basis),
                                "schema": quiet_basis.get("schema"),
                                "generated_utc": quiet_basis.get("generated_utc")}

    by_ns: dict[str, dict] = defaultdict(lambda: {
        "last_cycle": None, "last_place_true": None, "last_intent": None,
        "last_placed": None, "n_cycles": 0, "n_intents_total": 0, "n_placed_total": 0,
        "last_manage": None, "n_errors": 0, "last_error": None, "last_error_ts": None})
    for r in launcher_rows:
        ns = r.get("namespace") or "(unknown)"
        ts = parse_utc(r.get("ts"))
        blk = by_ns[ns]
        act = r.get("action")
        if act == "error":
            blk["n_errors"] += 1
            if ts and (blk["last_error_ts"] is None or ts > blk["last_error_ts"]):
                blk["last_error_ts"], blk["last_error"] = ts, r.get("error")
            continue
        if act == "manage":
            if ts and (blk["last_manage"] is None or ts > blk["last_manage"]):
                blk["last_manage"] = ts
            continue
        if act != "cycle":
            continue
        blk["n_cycles"] += 1
        if ts and (blk["last_cycle"] is None or ts > blk["last_cycle"]):
            blk["last_cycle"] = ts
        if r.get("place") and ts and (blk["last_place_true"] is None or ts > blk["last_place_true"]):
            blk["last_place_true"] = ts
        n_int = int(r.get("n_intents") or 0)
        blk["n_intents_total"] += n_int
        if n_int and ts and (blk["last_intent"] is None or ts > blk["last_intent"]):
            blk["last_intent"] = ts
        placed = r.get("placed") or []
        blk["n_placed_total"] += len(placed)
        if placed and ts and (blk["last_placed"] is None or ts > blk["last_placed"]):
            blk["last_placed"] = ts

    for ns, account in NAMESPACE_ACCOUNT.items():
        blk = by_ns.get(ns)
        row: dict = {"namespace": ns}
        if not blk or blk["n_cycles"] == 0:
            row.update({"state": UNCHECKED,
                        "reason": "no launcher cycle records for this namespace in the export"})
            panel["per_account"][account] = row
            findings.append(Finding(
                "LIVENESS", UNCHECKED, account,
                "no launcher records — liveness is UNCHECKED, not clear", ""))
            continue

        age = _age_hours(blk["last_cycle"], now)
        row.update({
            "state": CLEAN,
            "last_cycle_utc": blk["last_cycle"].isoformat() if blk["last_cycle"] else None,
            "heartbeat_age_hours": age,
            "n_cycles_in_log": blk["n_cycles"],
            "n_intents_total": blk["n_intents_total"],
            "n_placed_total": blk["n_placed_total"],
            "last_intent_utc": blk["last_intent"].isoformat() if blk["last_intent"] else None,
            "last_placed_utc": blk["last_placed"].isoformat() if blk["last_placed"] else None,
            "days_since_last_intent": (_age_hours(blk["last_intent"], now) or 0) / 24.0
                                      if blk["last_intent"] else None,
            "days_since_last_placement": (_age_hours(blk["last_placed"], now) or 0) / 24.0
                                         if blk["last_placed"] else None,
            "last_manage_utc": blk["last_manage"].isoformat() if blk["last_manage"] else None,
            "n_launcher_errors": blk["n_errors"],
            "last_error": blk["last_error"],
        })
        wk = workers.get(ns)
        if wk:
            row["worker_uptime_hours"] = wk["uptime_hours"]
            row["worker_pids"] = wk["pids"]

        # ALIVE
        if age is not None and age > float(args.heartbeat_alert_hours):
            findings.append(Finding(
                "LIVENESS", ALERT, account,
                f"last launcher cycle was {age:.1f} h ago (alert above "
                f"{args.heartbeat_alert_hours} h)",
                "This is the ALIVE question, not the quiet one. A book that stopped emitting is "
                "broken; check the supervisor. NOTE: the age is measured against the EXPORT, so a "
                "stale export produces a stale heartbeat — read the export age at the top of the "
                "page before treating this as a live outage."))
        if blk["n_errors"]:
            findings.append(Finding(
                "LIVENESS", ALERT, account,
                f"{blk['n_errors']} launcher tick error(s) in this log; last: {blk['last_error']}",
                "The loop survives any cycle error by design (launcher.py:352-356), so errors do "
                "not stop the book and do not show up as an outage."))

        # QUIET
        row["quiet"] = _quiet_verdict(quiet_basis, account, row, findings, now=now)
        panel["per_account"][account] = row
    return panel, findings


QUIET_BASIS_SCHEMA = {
    "schema": "gtos.live.quiet_basis.v1",
    "generated_utc": "<iso>",
    "provenance": "<what measured it>",
    "book_level": {
        "<ACCOUNT>": {
            "expected_fills_per_week": "<float>",
            "warn_after_silent_weekday_sessions": "<int — block-bootstrap p95>",
            "alert_after_silent_weekday_sessions": "<int — block-bootstrap p99>",
            "alarm_false_trip_probability": {"warn": 0.05, "alert": 0.01},
        }
    },
    "per_account_sleeve": {
        "<ACCOUNT>::<sleeve>": {
            "expected_fills_per_week": "<float>",
            "alarm_days_without_fill": "<float>",
            "alarm_false_trip_probability": "<float>",
        }
    },
}


def _quiet_verdict(basis, account, row, findings, *, now=None) -> dict:
    """Adopt Session BB's threshold if it exists; otherwise report the metric and say it is unjudged.

    The false-alarm rate is REQUIRED alongside the threshold, and a basis that omits it is refused.
    That is not pedantry — it is the lesson `FIVE_SLEEVE_OPERATOR_PAGE.md` §S1 paid for: a floor
    that fires 74 % of the time on a healthy sleeve is a coin flip wearing a threshold's clothes,
    and the only way anyone found out was by computing the number that had already been claimed.
    """
    days = row.get("days_since_last_placement")
    out = {"days_since_last_placement": days,
           "days_since_last_intent": row.get("days_since_last_intent")}
    if basis is None:
        out.update({"state": UNCHECKED,
                    "reason": "no quiet basis; silence is UNJUDGED. For this estate long silences "
                              "are normal — expect roughly 7 book-days a month — so an "
                              "uncalibrated alarm here would be worse than none."})
        return out
    blk = ((basis.get("book_level") or {}).get(account)) or {}
    warn = blk.get("warn_after_silent_weekday_sessions")
    alert = blk.get("alert_after_silent_weekday_sessions")
    fp = blk.get("alarm_false_trip_probability")
    if not isinstance(warn, int) or not isinstance(alert, int) or warn > alert:
        out.update({"state": UNCHECKED, "reason": f"quiet basis carries no book-level threshold "
                                                  f"for {account}"})
        return out
    if not isinstance(fp, dict) or fp.get("warn") is None or fp.get("alert") is None:
        out.update({"state": UNCHECKED,
                    "reason": "quiet basis declares a threshold with no measured false-trip "
                              "probability. REFUSED: an alarm whose false-alarm rate is unknown "
                              "cannot be read either way."})
        return out
    out.update({"warn_after_silent_weekday_sessions": warn,
                "alert_after_silent_weekday_sessions": alert,
                "alarm_false_trip_probability": fp,
                "expected_fills_per_week": blk.get("expected_fills_per_week")})
    last = parse_utc(row.get("last_placed_utc"))
    now = parse_utc(now) if not isinstance(now, dt.datetime) else now
    if last is None or now is None:
        out.update({"state": UNCHECKED, "reason": "no placement has ever been recorded in this "
                                                  "log (or no evaluation clock), so silence has "
                                                  "no weekday-session origin"})
        return out
    sil = _load_sibling("book_silence_check").weekday_sessions_between(last.date(), now.date())
    out["silent_weekday_sessions"] = sil
    out["state"] = ALERT if sil >= alert else (WARN if sil >= warn else CLEAN)
    if out["state"] in (WARN, ALERT):
        level = out["state"]
        limit = alert if level == ALERT else warn
        rate = fp["alert" if level == ALERT else "warn"]
        findings.append(Finding(
            "LIVENESS", level, account,
            f"{sil} silent weekday sessions, at the calibrated {level} threshold {limit}",
            f"This threshold has tail probability {rate:.0%} on a healthy book. It is a message, not a "
            f"verdict: check the ALIVE row above first — a stopped book and a quiet book look "
            f"identical from the fill stream alone."))
    return out


# ---------------------------------------------------------------------------
# PANEL 5 — per-sleeve economics, composed from book_sleeve_telemetry
# ---------------------------------------------------------------------------
def _sleeve_panel(args) -> tuple[dict, list[Finding]]:
    """Delegate to `book_sleeve_telemetry.build_page` rather than restate it.

    Composition, not duplication: that tool owns the pre-registered stop conditions, the two floors,
    the day-blocked sign-flip and its resolution floor. Re-implementing any of that here would
    create a second, drifting truth about armed money — which is the exact failure the estate keeps
    finding in its own artifacts.
    """
    findings: list[Finding] = []
    if not args.fills:
        return {"state": UNCHECKED,
                "reason": "no --fills. Per-sleeve R, the stop conditions and every economic "
                          "statement about the armed set are UNCHECKED. Build the file with "
                          "scripts/w7_live_forensics.py --export-root <export> --out-dir <dir>."}, \
            [Finding("SLEEVES", UNCHECKED, "both",
                     "no fills file — every pre-registered stop condition is unevaluated", "")]
    try:
        bst = _load_sibling("book_sleeve_telemetry")
    except Exception as exc:  # noqa: BLE001
        return {"state": UNCHECKED, "reason": f"book_sleeve_telemetry not importable: {exc!r}"}, \
            [Finding("SLEEVES", UNCHECKED, "both", "sleeve telemetry unavailable", repr(exc))]

    ns = argparse.Namespace(
        fills=Path(args.fills), conditions=Path(args.conditions), basis=Path(args.basis),
        armed_utc=args.armed_utc, launch_tags_ftmo=None, launch_tags_redacted_account=None,
        output=None, json=None)
    if not Path(ns.conditions).is_file():
        return {"state": UNCHECKED, "reason": f"stop-conditions artifact missing: {ns.conditions}"}, \
            [Finding("SLEEVES", UNCHECKED, "both", "stop-conditions artifact missing",
                     str(ns.conditions))]
    try:
        page = bst.build_page(ns)
    except Exception as exc:  # noqa: BLE001
        return {"state": UNCHECKED, "reason": f"sleeve telemetry failed: {exc!r}"}, \
            [Finding("SLEEVES", UNCHECKED, "both", "sleeve telemetry raised", repr(exc))]

    # S6 is answered by PANEL 1 from the process command line, which is strictly better evidence
    # than the operator-typed --launch-tags this delegate would otherwise use. Dropping its S6
    # findings here avoids two different answers to one question on one page.
    for f in page.get("findings", []):
        if f.get("condition") == "S6":
            continue
        lvl = f.get("level") if f.get("level") in (ALERT, STOP, UNCHECKED) else ALERT
        findings.append(Finding("SLEEVES", lvl, f.get("scope", ""), f.get("text", ""),
                                f.get("why", "")))
    return {"state": page.get("verdict", UNCHECKED), "delegate": "scripts/book_sleeve_telemetry.py",
            "armed_tags": page.get("armed_tags"), "armed_utc": page.get("armed_utc"),
            "n_rows_read": page.get("n_rows_read"),
            "n_post_arming_fills": page.get("n_post_arming_fills"),
            "per_sleeve": page.get("per_sleeve"), "findings": page.get("findings"),
            "de_arm": page.get("de_arm")}, findings


# ---------------------------------------------------------------------------
# PANEL 6 — symbol resolution: can the book still NAME what it trades?
# ---------------------------------------------------------------------------
def _armed_tags_for(armed_panel_result, account):
    """The armed set to judge severity against, preferring the running worker's own command line.

    Returns None when no read is usable — which `build_slots` treats as "assume everything is
    armed", so an unknown armed set can only over-report. The launcher union is the fallback and
    is a known over-report itself (F-BC-3: it does not apply DF-1), which is the safe direction.
    """
    row = ((armed_panel_result or {}).get("per_account") or {}).get(account) or {}
    reads = row.get("reads") or {}
    w = reads.get("worker_cmdline") or {}
    if w.get("tags_state") == "present" and w.get("tags"):
        return list(w["tags"])
    lu = reads.get("launcher_union") or {}
    if lu.get("sleeves"):
        return list(lu["sleeves"])
    return None


def symbols_panel(export, armed) -> tuple[dict, list[Finding]]:
    """Diff each account's RESOLVED broker symbol names against that broker's own symbol tree.

    The one check on this page that would have caught a real broker rename — and the one that
    must never be built the obvious way. On 2026-07-31 a live probe compared GTOS **canonical**
    names (`SPX500`, `GER40`, …) against FTMO's tree, found them absent, and reported four armed
    members muted by an overnight rename. They were not: those are registry names, the FTMO
    profile has always mapped them to `US500.cash`/`GER40.cash`, and all five targets were in
    FTMO's tree in the 2026-07-25 export — six days before the "rename". Comparing canonical
    names raises that false alarm against every correctly-configured cross-broker mapping GTOS
    has, so this panel resolves through `symbol_map.build_broker_symbol_resolver` — the same
    crossing `book_engine.py:543` fetches bars with — and compares only resolved names.

    Worth a panel because the true failure is SILENT: `bar_provider.py:120-125` swallows every
    feed error into `([], [])` and `book_engine.py:563` `continue`s on empty bars with no log and
    no counter. A vanished broker symbol mutes a member forever while the heartbeat, the launcher
    records and the equity read all stay healthy.
    """
    findings: list[Finding] = []
    panel: dict = {"per_account": {}, "note": (
        "Resolved broker names, not canonical registry names — comparing canonical names is the "
        "error that produced the 2026-07-31 false alarm.")}

    try:
        from src.components.ultimate_book.sleeves.registry import (
            BUILT, CANDIDATE_BUILT, MARKET_EXPANSION_BUILT,
        )
        from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
        from src.components.ultimate_book.symbol_resolution_watch import (
            build_slots, rename_candidates, watch,
        )
        import yaml as _yaml
    except Exception as exc:                                     # pragma: no cover - import guard
        panel["state"] = UNCHECKED
        panel["reason"] = f"registry/watch not importable here: {exc}"
        findings.append(Finding("SYMBOLS", UNCHECKED, "host",
                                "symbol resolution could not be checked",
                                panel["reason"]))
        return panel, findings

    specs = {}
    specs.update(BUILT)
    specs.update(CANDIDATE_BUILT)
    specs.update(MARKET_EXPANSION_BUILT)

    worst = CLEAN
    for account in ACCOUNTS:
        name = ACCOUNT_PROFILE[account]
        path, source = export.profile(name), "export"
        if path is None:
            path, source = REPO / "config" / "profiles" / f"{name}.yaml", "repo"
        row: dict = {"profile": str(path), "profile_source": source}
        if not path.is_file():
            row.update({"state": UNCHECKED, "reason": f"profile {name}.yaml not found"})
            findings.append(Finding("SYMBOLS", UNCHECKED, account,
                                    f"no profile {name}.yaml to resolve symbols with", ""))
            panel["per_account"][account] = row
            worst = max(worst, UNCHECKED, key=lambda s: _RANK[s])
            continue

        try:
            prof = _yaml.safe_load(path.read_text(encoding="utf-8"))
            resolve = build_broker_symbol_resolver(prof)
        except Exception as exc:
            row.update({"state": UNCHECKED, "reason": f"profile unreadable: {exc}"})
            findings.append(Finding("SYMBOLS", UNCHECKED, account,
                                    "profile could not be parsed to resolve symbols", str(exc)))
            panel["per_account"][account] = row
            worst = max(worst, UNCHECKED, key=lambda s: _RANK[s])
            continue

        tags = _armed_tags_for(armed, account)
        tree = [r.get("name") or r.get("symbol") for r in export.symbols(account)]
        out = watch(build_slots(specs.values(), resolve, armed_tags=tags), tree or None,
                    account=account)
        out["armed_tags_read"] = tags
        out["armed_tags_basis"] = ("worker command line / launcher union" if tags
                                   else "UNKNOWN — every sleeve treated as armed (over-reports)")
        if out["unresolvable"]:
            out["rename_candidates"] = rename_candidates(out["unresolvable"], tree)
        row.update(out)
        panel["per_account"][account] = row
        worst = max(worst, out["state"], key=lambda s: _RANK[s])

        if out["state"] in (ALERT, STOP):
            findings.append(Finding(
                "SYMBOLS", out["state"], account, out["summary"],
                "A member whose broker symbol no longer exists generates NOTHING and says nothing: "
                "bar_provider.py:120-125 turns the failed fetch into ([], []) and book_engine.py:563 "
                "skips it with no log and no counter. Confirm against the terminal's own symbol "
                "list before changing anything — and note the repair is a token-bound profile edit, "
                "so it is an owner ceremony, not a hot fix."))
        elif out["state"] == UNCHECKED:
            findings.append(Finding(
                "SYMBOLS", UNCHECKED, account, out["summary"],
                "No symbol tree in the export for this account, so a rename could not be ruled "
                "out. Re-export with symbols_get() included."))

    panel["state"] = worst
    return panel, findings


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------
def build_page(args) -> dict:
    now = parse_utc(args.now_utc) or dt.datetime.now(dt.timezone.utc)
    export = Export(Path(args.export_root) if args.export_root else None)
    launcher_path = export.launcher_log()
    launcher_rows = read_jsonl(launcher_path)
    workers = workers_from_processes(export, now)
    cfg, cfg_error = runtime_block(export.config())

    expect = None
    if args.expect_tags is not None:
        expect = [t.strip() for t in args.expect_tags.split(",") if t.strip()]
    else:
        conds = read_json(Path(args.conditions))
        if conds:
            expect = list(conds.get("armed_tags") or [])

    findings: list[Finding] = []
    armed, f1 = armed_panel(export, launcher_rows, workers, cfg, cfg_error, expect,
                            float(args.window_hours), now)
    accounts, f2 = accounts_panel(export, args, now)
    authority, f3 = authority_panel(export, launcher_rows, cfg, cfg_error, args, now)
    liveness, f4 = liveness_panel(export, launcher_rows, workers, args, now)
    sleeves, f5 = _sleeve_panel(args)
    symbols, f6 = symbols_panel(export, armed)
    findings = f1 + f2 + f3 + f4 + f5 + f6

    # export freshness — every "age" on this page is measured against the export, not the host
    pull = export.pull_summary()
    export_utc = parse_utc((pull or {}).get("generated_utc"))
    export_age = _age_hours(export_utc, now)
    if export.root is None:
        findings.insert(0, Finding(
            "EXPORT", UNCHECKED, "host",
            "no --export-root: nothing about the live host could be read",
            "This page is a reader of exported host state. With no export it has no facts about "
            "the running system at all."))
    elif export_age is not None and export_age > float(args.export_stale_hours):
        findings.insert(0, Finding(
            "EXPORT", ALERT, "host",
            f"this export is {export_age / 24.0:.1f} days old "
            f"(generated {(pull or {}).get('generated_utc')})",
            "Every age, equity and gate on this page describes the host AS OF THAT MOMENT. A stale "
            "export makes a healthy book look dead and a changed gate look unchanged. Re-export "
            "before acting on anything time-sensitive."))

    worst = max([_RANK[f.level] for f in findings], default=0)
    if worst >= _RANK[ALERT]:
        verdict, code = (STOP if worst == _RANK[STOP] else ALERT), 1
    elif worst == _RANK[WARN]:
        verdict, code = WARN, 1
    elif worst == _RANK[UNCHECKED]:
        verdict, code = UNCHECKED, 3
    else:
        verdict, code = CLEAN, 0

    return {
        "schema": "gtos.live.command_center.v1",
        "generated_utc": now.isoformat(),
        "export_root": str(export.root) if export.root else None,
        "export_generated_utc": (pull or {}).get("generated_utc"),
        "export_age_hours": export_age,
        "launcher_log": str(launcher_path) if launcher_path else None,
        "n_launcher_rows": len(launcher_rows),
        "verdict": verdict,
        "exit_code": code,
        "panels": {"armed": armed, "accounts": accounts, "authority": authority,
                   "liveness": liveness, "sleeves": sleeves, "symbols": symbols},
        "findings": [f.as_dict() for f in findings],
        "read_only_assertion": (
            "This page imported no broker module, opened no socket, and wrote no config. It cannot "
            "arm, disarm, resize, flatten or restart anything."),
    }


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------
def _n(v, fmt="{:,.2f}", dash="—"):
    return dash if v is None else fmt.format(v)


def _badge(state):
    return {CLEAN: "✅ CLEAN", WARN: "⚠️ WARN", ALERT: "⚠️ ALERT", STOP: "⛔ STOP",
            UNCHECKED: "❔ UNCHECKED"}.get(state, str(state))


def render_markdown(page: dict) -> str:
    L: list[str] = []
    P = page["panels"]
    L.append("# GTOS command center")
    L.append("")
    L.append(f"**{_badge(page['verdict'])}** · exit code `{page['exit_code']}` · "
             f"generated `{page['generated_utc']}`")
    L.append("")
    if page["export_root"]:
        age = page.get("export_age_hours")
        L.append(f"Host state read from `{page['export_root']}`, exported "
                 f"`{page['export_generated_utc']}`"
                 + (f" — **{age / 24.0:.1f} days old**" if age is not None else ""))
    else:
        L.append("**No export supplied.** Nothing about the live host could be read.")
    L.append("")
    L.append("> Everything below is a MESSAGE. This page holds no broker connection and no "
             "authority: it cannot arm, disarm, resize, flatten or restart anything. Every action "
             "it names is a ceremony the orchestrator performs and Borhen authorises.")
    L.append("")
    L.append("> Every age on this page is measured against **the export**, not against now. A "
             "stale export makes a healthy book look dead.")
    L.append("")

    # -- findings first ----------------------------------------------------
    L.append("## What needs you")
    L.append("")
    if not page["findings"]:
        L.append("Nothing. Every check that could run, ran, and passed.")
    else:
        order = {STOP: 0, ALERT: 1, WARN: 2, UNCHECKED: 3}
        for f in sorted(page["findings"], key=lambda x: order.get(x["level"], 3)):
            L.append(f"- **{_badge(f['level'])}** · `{f['panel']}` · {f['scope']} — {f['text']}")
            if f["why"]:
                L.append(f"  <br>*{f['why']}*")
    L.append("")

    # -- 1 armed set -------------------------------------------------------
    a = P["armed"]
    L.append("## 1 · The armed set — three independent reads")
    L.append("")
    L.append(f"Expected: `{','.join(a['expected_tags']) or '(none declared)'}` · union window "
             f"{a['window_hours']:.0f} h")
    L.append("")
    L.append("| account | worker `--tags` (running process) | launcher union (window) | "
             "config include flags | verdict |")
    L.append("|---|---|---|---|---|")
    for acct, row in a["per_account"].items():
        w = row["reads"].get("worker_cmdline") or {}
        lu = row["reads"].get("launcher_union") or {}
        cf = row["reads"].get("config_flags") or {}
        wtxt = ("`" + ",".join(w.get("tags") or []) + "`") if w.get("tags") else \
            f"**{w.get('tags_state', 'unread').upper()}**"
        if w.get("state") == UNCHECKED:
            wtxt = "—"
        ltxt = (f"{lu.get('n_sleeves')}"
                + (" (lower bound)" if lu.get("is_lower_bound") else "")) \
            if lu.get("n_sleeves") is not None else "—"
        c3 = (cf.get("flags") or {}).get("ultimate_book_include_clean3", "—")
        L.append(f"| **{acct}** | {wtxt} | {ltxt} | `include_clean3={c3}` | "
                 f"{_badge(row.get('state'))} |")
    L.append("")
    for acct, row in a["per_account"].items():
        lu = row["reads"].get("launcher_union") or {}
        if lu.get("single_record_would_have_said"):
            L.append(f"- `{acct}` — reading a single launcher record instead of the union would "
                     f"have said {lu['single_record_would_have_said']}.")
    L.append("")
    L.append("**How to read this table.** The worker column is the only one that BOUNDS the book; "
             "it is read off the running process's command line, not typed by anyone. The launcher "
             "union is what the engine resolved, over a window — never a single record "
             "(`launcher.py:328` emits only the tags whose timeframe advanced that tick) — and it "
             "is **pre-DF-1**, so it over-reports what can actually fire by up to the three clean_3 "
             "sleeves when `include_clean3` is false. The two answer different questions and the "
             "page keeps them apart deliberately.")
    L.append("")

    # -- 2 accounts --------------------------------------------------------
    L.append("## 2 · The two accounts")
    L.append("")
    L.append("| | equity | balance | open P/L | positions | pending | to target | static headroom "
             "| daily allowance |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for acct, r in P["accounts"]["per_account"].items():
        if r.get("state") == UNCHECKED and "equity" not in r:
            L.append(f"| **{acct}** | — | — | — | — | — | — | — | — |")
            continue
        L.append(
            f"| **{acct}** | {_n(r.get('equity'), '${:,.2f}')} | "
            f"{_n(r.get('balance'), '${:,.2f}')} | {_n(r.get('open_pl'), '${:,.2f}')} | "
            f"{r.get('n_open_positions', '—')} | {r.get('n_pending_orders', '—')} | "
            f"{_n(r.get('distance_to_target_usd'), '${:,.0f}')} | "
            f"{_n(r.get('static_headroom_usd'), '${:,.0f}')} | "
            f"{_n(r.get('daily_allowance_usd'), '${:,.0f}')} |")
    L.append("")
    for acct, r in P["accounts"]["per_account"].items():
        if "equity" not in r:
            continue
        L.append(f"**{acct}** — {r.get('product')} · login `{r.get('login')}` · "
                 f"`{r.get('server')}` · terminal build `{r.get('terminal_build')}` · "
                 f"connected `{r.get('terminal_connected')}` · trade_allowed "
                 f"`{r.get('trade_allowed_account')}`")
        L.append("")
        tgt = r.get("phase_target_pct")
        if tgt is not None:
            L.append(f"- phase **{r.get('phase')}** ({r.get('phase_provenance')}); target "
                     f"{tgt}% = {_n(r.get('phase_target_equity_usd'), '${:,.0f}')}, "
                     f"**{_n(r.get('distance_to_target_usd'), '${:,.0f}')} to go** "
                     f"({_n(r.get('distance_to_target_pct_of_initial'), '{:+.2f}%')} of initial)")
        if r.get("static_dd_floor_usd") is not None:
            L.append(f"- max-DD floor {_n(r.get('static_dd_floor_usd'), '${:,.0f}')} "
                     f"({r.get('max_dd_basis')}, coverage {r.get('max_dd_coverage')}) — headroom "
                     f"**{_n(r.get('static_headroom_usd'), '${:,.0f}')}**")
            if r.get("max_dd_caveat"):
                L.append(f"  <br>*{r['max_dd_caveat']}*")
        if r.get("daily_allowance_usd") is not None:
            L.append(f"- daily allowance {_n(r.get('daily_allowance_usd'), '${:,.0f}')} "
                     f"({r.get('daily_allowance_denominator')}), resets {r.get('daily_reset')}"
                     + (f" — used {_n(r.get('daily_used_usd'), '${:,.0f}')}"
                        if r.get("daily_used_usd") is not None else ""))
            if r.get("daily_note"):
                L.append(f"  <br>*{r['daily_note']}*")
        if r.get("minimum_trading_days_required") is not None:
            if r.get("trading_days_state") == CLEAN:
                L.append(f"- minimum trading days required **{r['minimum_trading_days_required']}** "
                         f"· **{r.get('distinct_trading_days_in_export')}** distinct trading days "
                         f"in this export, on the {r.get('trading_day_calendar')} calendar "
                         f"({r.get('distinct_trading_days_utc')} on UTC)")
                L.append(f"  <br>*{r.get('minimum_trading_days_note')}*")
            else:
                L.append(f"- minimum trading days required "
                         f"**{r['minimum_trading_days_required']}** · count **UNCHECKED** — "
                         f"{r.get('trading_days_reason')}")
        if r.get("open_positions"):
            L.append("")
            L.append("  | ticket | symbol | vol | SL | TP | P/L | swap | magic |")
            L.append("  |---|---|---:|---:|---:|---:|---:|---|")
            for p in r["open_positions"]:
                L.append(f"  | {p.get('ticket')} | {p.get('symbol')} | {p.get('volume')} | "
                         f"{p.get('sl')} | {p.get('tp')} | {_n(p.get('profit'), '{:,.2f}')} | "
                         f"{_n(p.get('swap'), '{:,.2f}')} | {p.get('magic')} |")
        L.append("")

    # -- 3 authority -------------------------------------------------------
    L.append("## 3 · Authority — gates, flags, tokens")
    L.append("")
    L.append("| account | enabled | apply_to_execution | live_activation_allowed | "
             "live_broker_authority | as of | profile |")
    L.append("|---|---|---|---|---|---|---|")
    for acct, r in P["authority"]["per_account"].items():
        g = (r.get("resolved_gates") or {})
        gates = g.get("gates") or {}
        L.append(f"| **{acct}** | `{gates.get('ultimate_book_enabled', '—')}` | "
                 f"`{gates.get('ultimate_book_apply_to_execution', '—')}` | "
                 f"`{gates.get('ultimate_book_live_activation_allowed', '—')}` | "
                 f"`{gates.get('ultimate_book_live_broker_authority', '—')}` | "
                 f"{(g.get('as_of_utc') or '—')[:16]} | `{g.get('profile', '—')}` |")
    L.append("")
    L.append("*These are the gates the **running worker** resolved, from its own launcher record — "
             "not the config file on disk. When the two disagree the process is right about now and "
             "the file is what a restart would apply; the disagreement is reported above.*")
    L.append("")
    kf = P["authority"].get("kill_flags") or {}
    if kf.get("state") == CLEAN:
        L.append(f"- kill/halt flags probed: **{kf.get('probed')}**, present: "
                 f"**{len(kf.get('present') or [])}**"
                 + (f" — {[p['path'] for p in kf['present']]}" if kf.get("present") else ""))
        L.append(f"  <br>*{kf.get('note')}*")
    else:
        L.append(f"- kill/halt flags: **UNCHECKED** — {kf.get('reason')}")
    tok = P["authority"].get("token") or {}
    if tok.get("state") == CLEAN:
        for t in tok.get("tokens", []):
            h = t.get("hours_until_expiry")
            L.append(f"- token `{(t.get('account_login_sha256') or '?')[:12]}` expires "
                     f"`{t.get('expires_utc')}`"
                     + (f" — **{h:.1f} h**" if h is not None else ""))
        L.append(f"  <br>*{tok.get('note')}*")
    else:
        L.append(f"- activation tokens: **UNCHECKED** — {tok.get('reason')}")
    L.append("")

    # -- 4 liveness --------------------------------------------------------
    L.append("## 4 · Alive, and quiet — two different questions")
    L.append("")
    L.append("| account | last cycle | heartbeat age | cycles | intents | placed | "
             "silent weekday sessions | quiet |")
    L.append("|---|---|---:|---:|---:|---:|---:|---|")
    for acct, r in P["liveness"]["per_account"].items():
        q = r.get("quiet") or {}
        L.append(f"| **{acct}** | {(r.get('last_cycle_utc') or '—')[:16]} | "
                 f"{_n(r.get('heartbeat_age_hours'), '{:,.1f} h')} | "
                 f"{r.get('n_cycles_in_log', '—')} | {r.get('n_intents_total', '—')} | "
                 f"{r.get('n_placed_total', '—')} | "
                 f"{q.get('silent_weekday_sessions', '—')} | "
                 f"{_badge(q.get('state'))} |")
    L.append("")
    qb = P["liveness"].get("quiet_basis") or {}
    if qb.get("state") == UNCHECKED:
        L.append(f"*Quiet is **UNJUDGED**: {qb.get('reason')}*")
        L.append("")
        L.append("<details><summary>The artifact this page will adopt "
                 "(<code>gtos.live.quiet_basis.v1</code>)</summary>")
        L.append("")
        L.append("```json")
        L.append(json.dumps(qb.get("expected_schema"), indent=2))
        L.append("```")
        L.append("")
        L.append("A threshold with no measured `alarm_false_trip_probability` is **refused**, not "
                 "adopted. `FIVE_SLEEVE_OPERATOR_PAGE.md` §S1 is why: a floor that fires 74 % of "
                 "the time on a healthy sleeve is a coin flip wearing a threshold's clothes.")
        L.append("</details>")
    else:
        L.append(f"*Quiet judged against `{qb.get('artifact')}` ({qb.get('schema')}).*")
    L.append("")

    # -- 5 sleeves ---------------------------------------------------------
    s = P["sleeves"]
    L.append("## 5 · Per-sleeve economics and the pre-registered stop conditions")
    L.append("")
    if s.get("state") == UNCHECKED and not s.get("per_sleeve"):
        L.append(f"**UNCHECKED** — {s.get('reason')}")
    else:
        L.append(f"Delegated to `{s.get('delegate')}` (armed {s.get('armed_utc')}) · "
                 f"{s.get('n_rows_read')} rows read · "
                 f"**{s.get('n_post_arming_fills')}** post-arming fills.")
        L.append("")
        rows = [(k, v) for k, v in (s.get("per_sleeve") or {}).items() if v.get("n_fills")]
        if not rows:
            L.append("No post-arming fill of any armed sleeve is in this fills file. That is **not "
                     "a clean bill** — every economic condition is UNCHECKED. Expect roughly 7 "
                     "book-days a month; long silences are normal.")
        else:
            L.append("| sleeve · account | n | net R | gross R/fill (trade / day) | med hold | "
                     "conditions |")
            L.append("|---|---:|---:|---|---:|---|")
            for k, v in rows:
                t = v["telemetry"]
                chks = " ".join(f"{c}:{b['state'][0]}" for c, b in (v.get("checks") or {}).items())
                L.append(f"| `{k}` | {t['n_fills']} | {t['net_r_total']:+.3f} | "
                         f"{t['gross_r_per_fill_trade_weighted']:+.4f} / "
                         f"{t['gross_r_per_fill_day_weighted']:+.4f} | "
                         f"{t['median_hold_hours']:.2f} h | {chks} |")
        L.append("")
        da = s.get("de_arm") or {}
        if da:
            L.append("<details><summary>If you decide to take a sleeve back off</summary>")
            L.append("")
            for k in ("how", "what_it_stops", "what_it_does_NOT_stop",
                      "same_day_size_consequence", "never"):
                if da.get(k):
                    L.append(f"- **{k}** — {da[k]}")
            L.append("")
            L.append("</details>")
    L.append("")

    # -- 6 symbol resolution ----------------------------------------------
    sy = P.get("symbols") or {}
    L.append("## 6 · Symbol resolution — can the book still name what it trades?")
    L.append("")
    L.append("| account | state | resolved OK | broker tree | unresolvable | armed | profile |")
    L.append("|---|---|---:|---:|---:|---:|---|")
    for acct, r in (sy.get("per_account") or {}).items():
        L.append(f"| **{acct}** | {_badge(r.get('state'))} | {r.get('resolved_ok', '—')} | "
                 f"{r.get('n_tree', '—')} | {len(r.get('unresolvable') or [])} | "
                 f"{len(r.get('unresolvable_armed') or [])} | "
                 f"`{Path(r.get('profile', '—')).name}` ({r.get('profile_source', '?')}) |")
    L.append("")
    for acct, r in (sy.get("per_account") or {}).items():
        if r.get("unresolvable"):
            L.append(f"**{acct} — members that resolve to symbols the broker does not serve:**")
            L.append("")
            L.append("  | sleeve | canonical | resolves to | armed | broker offers instead |")
            L.append("  |---|---|---|---|---|")
            cands = r.get("rename_candidates") or {}
            for u in r["unresolvable"]:
                hints = ", ".join(cands.get(u.get("broker") or "", [])[:4]) or "—"
                L.append(f"  | `{u['sleeve']}` | `{u['canonical']}` | `{u['broker']}` | "
                         f"{'**YES**' if u['armed'] else 'no'} | {hints} |")
            L.append("")
        elif r.get("state") == CLEAN:
            L.append(f"- {r.get('summary')}"
                     + (f" · {len(r.get('profile_unsupported') or [])} slots have no instrument "
                        f"config on this profile (a standing config fact, reported by the engine "
                        f"as `profile_missing_instrument_config`, **not** a rename)"
                        if r.get("profile_unsupported") else ""))
    L.append("")
    L.append("*Resolved broker names, never canonical registry names. `SPX500` is a GTOS name; "
             "FTMO calls it `US500.cash`. Asking FTMO for `SPX500` returns nothing and always "
             "has — that read is what produced the 2026-07-31 false rename alarm, and this panel "
             "resolves through `symbol_map.build_broker_symbol_resolver`, the same crossing "
             "`book_engine.py:543` fetches bars with.*")
    L.append("")
    L.append("*Worth a panel because the real failure is silent: a vanished broker symbol makes a "
             "member generate nothing, with no log line and no counter anywhere "
             "(`bar_provider.py:120-125` → `book_engine.py:563`), while every heartbeat stays "
             "green.*")
    L.append("")
    L.append("---")
    L.append("")
    L.append(f"*{page['read_only_assertion']}*")
    L.append("")
    L.append("*Companion pages: `phase4/CANARY_OPERATOR_PAGE.md` (is it armed, is it alive, what "
             "is the headroom, is the cost model still right) and "
             "`phase11/FIVE_SLEEVE_OPERATOR_PAGE.md` (what is each armed sleeve doing). This page "
             "is the union of what they see plus the three reads neither could make without asking "
             "you to type the answer.*")
    return "\n".join(L)


_HTML_HEAD = """<meta charset="utf-8"><title>GTOS command center</title>
<style>
:root{color-scheme:light dark;--bg:#fff;--fg:#16181d;--mut:#5b6472;--line:#e3e6ea;--card:#f7f8fa;
--ok:#0a7d33;--warn:#a8620a;--stop:#b3211d;--unk:#5b6472}
@media(prefers-color-scheme:dark){:root{--bg:#0f1115;--fg:#e6e8ec;--mut:#9aa4b2;--line:#262a31;
--card:#171a20;--ok:#4ade80;--warn:#fbbf24;--stop:#f87171;--unk:#9aa4b2}}
*{box-sizing:border-box}
body{margin:0;padding:2rem 1.25rem 4rem;background:var(--bg);color:var(--fg);
font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif}
main{max-width:62rem;margin:0 auto}
h1{font-size:1.6rem;margin:0 0 .35rem}
h2{font-size:1.12rem;margin:2.4rem 0 .8rem;padding-bottom:.35rem;border-bottom:1px solid var(--line)}
p,li{margin:.4rem 0}
code{font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--card);
padding:.1rem .3rem;border-radius:3px}
pre{overflow-x:auto;background:var(--card);padding:.8rem;border-radius:6px;border:1px solid var(--line)}
pre code{background:none;padding:0}
.wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;min-width:34rem;margin:.6rem 0;font-size:13.5px}
th,td{border-bottom:1px solid var(--line);padding:.42rem .6rem;text-align:left;white-space:nowrap}
th{font-weight:600;color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.03em}
td:nth-child(n+2){font-variant-numeric:tabular-nums}
blockquote{margin:.8rem 0;padding:.55rem .9rem;border-left:3px solid var(--line);
background:var(--card);color:var(--mut);border-radius:0 4px 4px 0}
em{color:var(--mut)}
details{margin:.7rem 0;border:1px solid var(--line);border-radius:6px;padding:.5rem .8rem;
background:var(--card)}
summary{cursor:pointer;font-weight:600;font-size:13.5px}
.v{display:inline-block;padding:.28rem .7rem;border-radius:99px;font-weight:700;font-size:13px}
.v-CLEAN{background:color-mix(in srgb,var(--ok) 16%,transparent);color:var(--ok)}
.v-WARN{background:color-mix(in srgb,var(--warn) 18%,transparent);color:var(--warn)}
.v-ALERT{background:color-mix(in srgb,var(--warn) 18%,transparent);color:var(--warn)}
.v-STOP{background:color-mix(in srgb,var(--stop) 18%,transparent);color:var(--stop)}
.v-UNCHECKED{background:color-mix(in srgb,var(--unk) 16%,transparent);color:var(--unk)}
hr{border:0;border-top:1px solid var(--line);margin:2rem 0}
</style>
"""


def render_html(page: dict) -> str:
    """A standalone page. Deliberately a light wrapper over the markdown, not a second renderer.

    Two renderers drift; the estate has paid for that lesson in other artifacts. The markdown is the
    single source of the page's WORDS — this only converts it.
    """
    md = render_markdown(page)
    body = _md_to_html(md)
    return _HTML_HEAD + "<main>" + body + "</main>\n"


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(s: str) -> str:
    # order matters: escape first, then re-introduce the tiny markup subset we emit
    s = _esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    s = s.replace("&lt;br&gt;", "<br>")
    for st in (CLEAN, WARN, ALERT, STOP, UNCHECKED):
        for badge in (f"✅ {st}", f"⚠️ {st}", f"⛔ {st}", f"❔ {st}"):
            s = s.replace(f"<strong>{badge}</strong>", f'<span class="v v-{st}">{badge}</span>')
    return s


def _md_to_html(md: str) -> str:
    out: list[str] = []
    lines = md.split("\n")
    i, in_table, in_list, in_pre = 0, False, False, False
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        if line.startswith("```"):
            if in_pre:
                out.append("</code></pre>")
                in_pre = False
            else:
                if in_list:
                    out.append("</ul>")
                    in_list = False
                out.append("<pre><code>")
                in_pre = True
            i += 1
            continue
        if in_pre:
            out.append(_esc(raw))
            i += 1
            continue

        is_row = line.startswith("|") and line.endswith("|")
        if is_row and not in_table:
            if in_list:
                out.append("</ul>")
                in_list = False
            cells = [c.strip() for c in line.strip("|").split("|")]
            out.append('<div class="wrap"><table><thead><tr>'
                       + "".join(f"<th>{_inline(c)}</th>" for c in cells)
                       + "</tr></thead><tbody>")
            in_table = True
            if i + 1 < len(lines) and set(lines[i + 1].strip()) <= set("|-: "):
                i += 1
            i += 1
            continue
        if in_table:
            if is_row:
                cells = [c.strip() for c in line.strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in cells) + "</tr>")
                i += 1
                continue
            out.append("</tbody></table></div>")
            in_table = False

        if line.startswith("- ") and not in_list:
            out.append("<ul>")
            in_list = True
        elif in_list and not line.startswith("- ") and not raw.startswith("  "):
            out.append("</ul>")
            in_list = False

        if not line:
            i += 1
            continue
        if line.startswith("# "):
            out.append(f"<h1>{_inline(line[2:])}</h1>")
        elif line.startswith("## "):
            out.append(f"<h2>{_inline(line[3:])}</h2>")
        elif line.startswith("> "):
            out.append(f"<blockquote>{_inline(line[2:])}</blockquote>")
        elif line.startswith("- "):
            out.append(f"<li>{_inline(line[2:])}</li>")
        elif in_list and raw.startswith("  "):
            out.append(f"<div>{_inline(line)}</div>")
        elif line == "---":
            out.append("<hr>")
        elif line.startswith("<"):
            out.append(line)
        else:
            out.append(f"<p>{_inline(line)}</p>")
        i += 1
    if in_pre:
        out.append("</code></pre>")
    if in_table:
        out.append("</tbody></table></div>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


# ---------------------------------------------------------------------------
def _kv_pairs(values):
    out = {}
    for item in values or []:
        if "=" not in item:
            raise argparse.ArgumentTypeError(f"expected ACCOUNT=VALUE, got {item!r}")
        k, v = item.split("=", 1)
        out[k.strip()] = float(v)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="The whole live system on one page, from a read-only host export.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--export-root", default=None,
                    help="a VPS export directory (the `extracted/` dir, or its parent)")
    ap.add_argument("--fills", default=None,
                    help="LIVE_TRADE_ROWS.jsonl from scripts/w7_live_forensics.py")
    ap.add_argument("--conditions", default=str(DEFAULT_CONDITIONS))
    ap.add_argument("--basis", default=str(DEFAULT_BASIS))
    ap.add_argument("--armed-utc", default=None)
    ap.add_argument("--expect-tags", default=None,
                    help="the armed set to check the running worker against "
                         "(default: armed_tags from the stop-conditions artifact)")
    ap.add_argument("--quiet-basis", default=str(DEFAULT_QUIET_BASIS),
                    help="Session CH's per-account gtos.live.quiet_basis.v1 artifact")
    ap.add_argument("--token-dir", default=None,
                    help="a directory holding *.token.json (the live tokens are on the VPS)")
    ap.add_argument("--phase", type=int, default=None, choices=(1, 2),
                    help="override the challenge phase (default: read off the broker's product)")
    ap.add_argument("--day-start-equity", action="append", default=None, metavar="ACCOUNT=VALUE",
                    help="day-start equity on the firm's own reset calendar, for daily-loss used")
    ap.add_argument("--window-hours", type=float, default=168.0,
                    help="window for the launcher union (default 168 = 7 days, wide enough for D1 "
                         "to advance across a weekend)")
    ap.add_argument("--heartbeat-alert-hours", type=float, default=1.0)
    ap.add_argument("--export-stale-hours", type=float, default=24.0)
    ap.add_argument("--token-expiry-alert-hours", type=float, default=72.0)
    ap.add_argument("--now-utc", default=None, help="pin 'now' (for reproducible pages and tests)")
    ap.add_argument("-o", "--output", default=None, help="write markdown here")
    ap.add_argument("--html", default=None, help="write a standalone HTML page here")
    ap.add_argument("--json", default=None, help="write the full structured page here")
    ap.add_argument("--quiet", action="store_true", help="do not print the page to stdout")
    args = ap.parse_args()
    args.day_start_equity = _kv_pairs(args.day_start_equity)

    page = build_page(args)
    md = render_markdown(page)
    if not args.quiet:
        print(md)
    if args.output:
        Path(args.output).write_text(md + "\n", encoding="utf-8")
    if args.html:
        Path(args.html).write_text(render_html(page), encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps(page, indent=1, default=str) + "\n", encoding="utf-8")
    return page["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
