"""Generate .context/LIVE_STATE.md — the single source of truth for *current* GTOS state.

Derives everything from git, config files, and source code. No narrative,
no opinions. Overwrites .context/LIVE_STATE.md on each run.

Run at session start:
    python scripts/generate_live_state.py

Run before producing any status/backlog synthesis:
    python scripts/generate_live_state.py

Exit code: 0 on success, 1 on missing config/repo.
"""

from __future__ import annotations

import subprocess
import sys
import os
import signal
import shutil
from datetime import datetime, timezone
from pathlib import Path
import re

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / ".context" / "LIVE_STATE.md"

RESEARCH_DOCTRINE = REPO_ROOT / ".context" / "00_core" / "research_operating_doctrine.md"
RESEARCH_CURRENT_STATE = REPO_ROOT / ".context" / "00_core" / "research_current_state.md"
RESEARCH_CONTEXT_REFERENCES = [
    REPO_ROOT / "CLAUDE.md",
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / ".context" / "00_core" / "quick_reference_card.md",
    REPO_ROOT / ".context" / "00_READING_ORDER.md",
]
RESEARCH_RELEVANT_PATHS = [
    "research/",
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/",
    "src/research_infra/",
    "src/components/gtos_vnext_runtime.py",
    "src/components/orchestrator.py",
    "config/agent_config.yaml",
    "tests/test_gtos_vnext_runtime.py",
    "scripts/run_raw_ohlc_path_ablation_v0.py",
    "scripts/run_raw_ohlc_path_ablation_v1_mtf.py",
    "scripts/run_raw_ohlc_path_scaling_v2_structural_levels.py",
    "scripts/run_raw_ohlc_path_scaling_v2b_prospective.py",
    "scripts/run_raw_ohlc_prequential_replay.py",
    "scripts/fetch_databento_futures.py",
    "scripts/fetch_databento_manifest.py",
    "scripts/build_orderflow_event_manifest.py",
    "scripts/analyze_orderflow_event_features.py",
    "scripts/analyze_orderflow_asof_symbol_diagnostics.py",
    "scripts/analyze_orderflow_depth_mbp1_features.py",
    "scripts/analyze_orderflow_depth_mbp10_features.py",
    "scripts/join_orderflow_features_to_candidate_outcomes.py",
    "scripts/audit_orderflow_actual_outcome_coverage.py",
    "scripts/audit_orderflow_limit_intent_reconciliation.py",
    "scripts/audit_orderflow_nas100_hypothesis_readiness.py",
    "scripts/audit_phase3_research_claim_ledger.py",
    "scripts/audit_usdjpy_6j_followup_validation.py",
    "tests/test_raw_ohlc_path_ablation_v0.py",
    "tests/test_raw_ohlc_path_ablation_v1_mtf.py",
    "tests/test_orderflow_features.py",
    "tests/test_orderflow_candidate_outcome_join.py",
    "tests/test_orderflow_asof_symbol_diagnostics.py",
    "tests/test_phase3_research_claim_ledger.py",
    "tests/test_usdjpy_6j_followup_audit.py",
]

GIT_LFS_POINTER_HEADER = "version https://git-lfs.github.com/spec/v1"
SOURCE_GREP_IGNORED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "node_modules",
}
SOURCE_GREP_TEXT_SUFFIXES = {
    ".py",
    ".pyi",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".md",
    ".sh",
    ".ps1",
    ".bat",
    ".txt",
    ".cfg",
    ".ini",
}
SOURCE_GREP_DEFAULT_PATHS = [
    "src/components",
    "src/research",
    "src/mt5",
    "src/llm_backend.py",
    "src/notifications.py",
]
SOURCE_GREP_LINE_CACHE: dict[str, list[str]] = {}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(1, value)


DEFAULT_GIT_TIMEOUT_SECONDS = _env_int("GTOS_LIVE_STATE_GIT_TIMEOUT_SECONDS", 20)
DEFAULT_LFS_TIMEOUT_SECONDS = _env_int("GTOS_LIVE_STATE_LFS_TIMEOUT_SECONDS", 8)
DEFAULT_DIFF_STAT_TIMEOUT_SECONDS = _env_int("GTOS_LIVE_STATE_DIFF_STAT_TIMEOUT_SECONDS", 5)
DEFAULT_DIFF_STAT_LARGE_FILE_BYTES = _env_int(
    "GTOS_LIVE_STATE_DIFF_STAT_LARGE_FILE_BYTES",
    25_000_000,
)
DEFAULT_DIFF_STAT_MAX_PATHS = _env_int("GTOS_LIVE_STATE_DIFF_STAT_MAX_PATHS", 120)
FULL_LFS_INVENTORY = os.environ.get("GTOS_LIVE_STATE_FULL_LFS", "").strip().lower() in {
    "1",
    "true",
    "yes",
}

KEY_LFS_READINESS_PATHS = [
    "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl",
    "shadow_logs/gtos_vnext_runtime_decisions.jsonl",
    "shadow_logs/strategy_follow_evaluations.jsonl",
    "shadow_logs/gtos_vnext_replacement_monitoring.jsonl",
    "shadow_logs/pending_limit_lifecycle.jsonl",
    "shadow_logs/ml_shadow_predictions.jsonl",
    "shadow_logs/v2b_forward_pair_resolution_audit.jsonl",
    "shadow_logs/live_candidate_strategy_rollups.jsonl",
    "shadow_logs/prefill_delivery_path_audit.jsonl",
    "research/program_control/SHADOW_LOG_INTEGRITY_VERIFICATION_2026-05-04.json",
]

NON_OPERATIONAL_DOC_COMMIT_RE = re.compile(
    r"\bdocs: add unit\d+ .+ handoff\b",
    re.IGNORECASE,
)

# Config flags we want enforcement-checked. Each entry is
# (config_path, grep_pattern, description).
# A flag with 0 matches in src/ is SUSPICIOUS — it may be cosmetic.
ENFORCEMENT_CHECKS = [
    ("deployment.phase", r"deployment.*phase|\[.deployment.\].*phase|deployment_phase",
     "Paper/live mode flag"),
    ("gate1.ob_retest_sl_exception", r"ob_retest_sl_exception",
     "sl_too_tight OB bypass"),
    ("gate1.ob_retest_sl_min_buffer_atr", r"ob_retest_sl_min_buffer_atr",
     "Apr 16 sweep margin (inside exception)"),
    ("gate1.sl_liquidity_cluster_enabled", r"sl_liquidity_cluster_enabled",
     "Liquidity cluster reject gate"),
    ("session_memory_enabled", r"session_memory_enabled",
     "T2b session memory disable"),
    ("news_filter.enabled", r"news_filter",
     "News filter toggle"),
    ("drawdown_reduction.threshold", r"drawdown_reduction",
     "H29 DD risk reduction"),
    ("budget.monthly_cap_usd", r"monthly_cap_usd|budget",
     "API budget cap"),
    ("filters.max_gap_pct", r"max_gap_pct",
     "Gap filter"),
    ("confidence_filter_mode", r"confidence_filter_mode",
     "Confidence filter (shadow/live)"),
]

# Leaf config keys to surface in the 'Active config' table.
SURFACED_CONFIG_KEYS = [
    ("Framework(s) enabled", "model_a.enabled_frameworks"),
    ("Risk % / trade", "risk.risk_per_trade_pct"),
    # T2.8 (session 33): ``risk.max_daily_losses`` removed in favor of
    # ``risk.max_daily_loss_pct`` (MTM daily-loss stop) + derived/pinned
    # ``risk.max_concurrent`` (concurrent cap = floor(loss/risk)).
    ("Max daily loss %", "risk.max_daily_loss_pct"),
    ("Max concurrent positions", "risk.max_concurrent"),
    ("Min R:R", "risk.min_rr"),
    ("SL absolute min", "risk.sl_absolute_min"),
    ("DD reduction threshold", "drawdown_reduction.threshold"),
    ("DD reduced risk %", "drawdown_reduction.reduced_risk_pct"),
    ("Gap filter max %", "filters.max_gap_pct"),
    ("OB SL exception", "gate1.ob_retest_sl_exception"),
    ("OB SL min buffer ATR", "gate1.ob_retest_sl_min_buffer_atr"),
    ("Liquidity cluster gate", "gate1.sl_liquidity_cluster_enabled"),
    ("Liquidity cluster margin ATR", "gate1.sl_liquidity_cluster_margin_atr"),
    ("AI primary model", "ai.primary_model"),
    ("AI effort", "ai.primary_effort"),
    ("API timeout (s)", "ai.api_timeout_seconds"),
    ("Session memory", "session_memory_enabled"),
    ("Confidence filter mode", "confidence_filter_mode"),
    ("News filter", "news_filter.enabled"),
    ("Deployment phase", "deployment.phase"),
    ("Budget monthly cap (USD)", "budget.monthly_cap_usd"),
]


def _run_subprocess(
    cmd: str | list[str],
    *,
    shell: bool,
    cwd: Path = REPO_ROOT,
    timeout: int = DEFAULT_GIT_TIMEOUT_SECONDS,
) -> str:
    """Run a bounded subprocess and kill its process group on timeout."""
    try:
        proc = subprocess.Popen(
            cmd,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
            encoding="utf-8",
            errors="replace",
            start_new_session=True,
        )
        stdout, _stderr = proc.communicate(timeout=timeout)
        return stdout.rstrip()
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            pass
        try:
            proc.communicate(timeout=1)
        except Exception:
            pass
        return f"[TIMEOUT after {timeout}s]"
    except Exception as e:
        return f"[ERROR: {e}]"


def run(cmd: str, cwd: Path = REPO_ROOT, timeout: int = DEFAULT_GIT_TIMEOUT_SECONDS) -> str:
    """Run shell command, return stdout stripped. Empty string on failure."""
    return _run_subprocess(cmd, shell=True, cwd=cwd, timeout=timeout)


def run_args(args: list[str], cwd: Path = REPO_ROOT, timeout: int = DEFAULT_GIT_TIMEOUT_SECONDS) -> str:
    """Run command without shell interpolation, return stdout stripped."""
    return _run_subprocess(args, shell=False, cwd=cwd, timeout=timeout)


def git_head() -> str:
    return run("git log -1 --oneline")


def git_status_short() -> str:
    out = run_args(["git", "status", "--short", "--untracked-files=normal"])
    if not out or out.startswith("["):
        return out
    lines = [
        line
        for line in out.splitlines()
        if line[3:].replace("\\", "/") != ".context/LIVE_STATE.md"
    ]
    return "\n".join(lines)


def recent_commits(n: int = 20) -> str:
    raw = run_args(["git", "log", "--oneline", f"-{n}"])
    if raw.startswith("["):
        return raw
    commits = [
        line
        for line in raw.splitlines()
        if line.strip() and not NON_OPERATIONAL_DOC_COMMIT_RE.search(line)
    ]
    return "\n".join(commits[:n])


def _dirty_tracked_entries_from_status(status: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        code = line[:2]
        if code == "??":
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        path = path.replace("\\", "/")
        if path == ".context/LIVE_STATE.md":
            continue
        if path:
            entries.append((code, path))
    return entries


def _git_head_blob_size(path: str) -> int:
    out = run_args(
        ["git", "cat-file", "-s", f"HEAD:{path}"],
        timeout=DEFAULT_DIFF_STAT_TIMEOUT_SECONDS,
    )
    return int(out) if out.isdigit() else 0


def git_diff_stat(status: str | None = None) -> str:
    if os.environ.get("GTOS_LIVE_STATE_FULL_DIFF_STAT") == "1":
        return run(
            "git diff --no-ext-diff --no-textconv --stat HEAD -- . ':(exclude).context/LIVE_STATE.md'",
            timeout=DEFAULT_GIT_TIMEOUT_SECONDS,
        )

    status_text = status if status is not None else git_status_short()
    dirty_entries = _dirty_tracked_entries_from_status(status_text)
    if not dirty_entries:
        return ""

    diff_paths: list[str] = []
    skipped_large: list[str] = []
    skipped_max_paths: list[str] = []
    for code, path in dirty_entries:
        abs_path = REPO_ROOT / path
        try:
            worktree_size = abs_path.stat().st_size if abs_path.is_file() else 0
        except OSError:
            worktree_size = 0
        head_size = _git_head_blob_size(path) if "D" in code or not abs_path.exists() else 0
        size = max(worktree_size, head_size)
        if size > DEFAULT_DIFF_STAT_LARGE_FILE_BYTES:
            skipped_large.append(f"{path} ({size} bytes)")
            continue
        if len(diff_paths) >= DEFAULT_DIFF_STAT_MAX_PATHS:
            skipped_max_paths.append(path)
            continue
        diff_paths.append(path)

    sections: list[str] = []
    if diff_paths:
        out = run_args(
            [
                "git",
                "diff",
                "--no-ext-diff",
                "--no-textconv",
                "--stat",
                "HEAD",
                "--",
                *diff_paths,
            ],
            timeout=DEFAULT_DIFF_STAT_TIMEOUT_SECONDS,
        )
        if out.startswith("[TIMEOUT"):
            sections.append(
                "diff-stat-degraded: dirty-path diff stat timed out after "
                f"{DEFAULT_DIFF_STAT_TIMEOUT_SECONDS}s for {len(diff_paths)} tracked path(s)."
            )
        elif out.startswith("[ERROR"):
            sections.append(f"diff-stat-degraded: {out}")
        elif out:
            sections.append(out)

    if skipped_large:
        sections.append(
            "diff-stat-skipped-large-files: "
            f"{len(skipped_large)} tracked path(s) exceed "
            f"{DEFAULT_DIFF_STAT_LARGE_FILE_BYTES} bytes; set "
            "GTOS_LIVE_STATE_FULL_DIFF_STAT=1 for full whole-tree stat. "
            f"Skipped: {', '.join(skipped_large[:12])}"
            + (" ..." if len(skipped_large) > 12 else "")
        )
    if skipped_max_paths:
        sections.append(
            "diff-stat-skipped-path-cap: "
            f"{len(skipped_max_paths)} tracked path(s) skipped after the bounded "
            f"{DEFAULT_DIFF_STAT_MAX_PATHS}-path sample; set "
            "GTOS_LIVE_STATE_DIFF_STAT_MAX_PATHS higher for a wider sample or "
            "GTOS_LIVE_STATE_FULL_DIFF_STAT=1 for full whole-tree stat. "
            f"First skipped: {', '.join(skipped_max_paths[:12])}"
            + (" ..." if len(skipped_max_paths) > 12 else "")
        )
    return "\n".join(sections)


def latest_research_commit() -> str:
    return run_args(["git", "log", "-1", "--format=%h %s", "--", *RESEARCH_RELEVANT_PATHS])


def read_config() -> tuple[dict, Path]:
    cfg_path = REPO_ROOT / "config" / "agent_config.yaml"
    if not cfg_path.exists():
        print(f"ERROR: {cfg_path} not found", file=sys.stderr)
        sys.exit(1)
    with open(cfg_path, encoding="utf-8") as f:
        return yaml.safe_load(f), cfg_path.relative_to(REPO_ROOT)


def dig(d, path: str):
    """dig({'a': {'b': 1}}, 'a.b') -> 1. Returns None if missing."""
    for seg in path.split("."):
        if not isinstance(d, dict):
            return None
        d = d.get(seg)
        if d is None:
            return None
    return d


def source_grep_lines(path: str = "src/") -> list[str]:
    """Load operational source lines once per live-state run."""
    cache_key = path.strip("/")
    if cache_key in SOURCE_GREP_LINE_CACHE:
        return SOURCE_GREP_LINE_CACHE[cache_key]
    lines: list[str] = []
    scan_paths = SOURCE_GREP_DEFAULT_PATHS if cache_key == "src" else [cache_key]
    listed = run_args(["git", "ls-files", "--", *scan_paths], timeout=DEFAULT_GIT_TIMEOUT_SECONDS)
    if not listed or listed.startswith("["):
        SOURCE_GREP_LINE_CACHE[cache_key] = lines
        return lines
    for rel_path in listed.splitlines():
        file_path = REPO_ROOT / rel_path
        if not file_path.is_file():
            continue
        if any(part in SOURCE_GREP_IGNORED_DIRS for part in file_path.parts):
            continue
        if file_path.suffix.lower() not in SOURCE_GREP_TEXT_SUFFIXES:
            continue
        try:
            if file_path.stat().st_size > 2_000_000:
                continue
            with open(file_path, encoding="utf-8", errors="replace") as f:
                lines.extend(f)
        except OSError:
            continue
    SOURCE_GREP_LINE_CACHE[cache_key] = lines
    return lines


def grep_count(pattern: str, path: str = "src/") -> int:
    """Count matching source lines without spawning a long-lived git grep."""
    try:
        compiled = re.compile(pattern)
    except re.error:
        return 0
    scan_paths = SOURCE_GREP_DEFAULT_PATHS if str(path).rstrip("/") == "src" else [path]
    rg = shutil.which("rg")
    if rg:
        try:
            result = subprocess.run(
                [
                    rg,
                    "--count",
                    "--no-messages",
                    "--color",
                    "never",
                    "--glob",
                    "!*.jsonl",
                    "--glob",
                    "!*.json",
                    "--glob",
                    "!research/science_program_2026_05/**",
                    pattern,
                    *scan_paths,
                ],
                cwd=REPO_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=20,
                check=False,
            )
            if result.returncode in {0, 1}:
                total = 0
                for line in result.stdout.splitlines():
                    try:
                        total += int(line.rsplit(":", 1)[-1])
                    except ValueError:
                        continue
                return total
        except (OSError, subprocess.TimeoutExpired):
            pass
    return sum(1 for line in source_grep_lines(path) if compiled.search(line))


def list_permissions_gates() -> list[tuple[str, int]]:
    """Grep permissions.py for gate-function definitions."""
    perm = REPO_ROOT / "src" / "components" / "permissions.py"
    if not perm.exists():
        return []
    gates: list[tuple[str, int]] = []
    with open(perm, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped.startswith("def "):
                continue
            if (
                stripped.startswith("def _reject_")
                or stripped.startswith("def _ob_retest_sl_exception_applies")
                or stripped.startswith("def _log_inverted_tp")
                or stripped.startswith("def _log_liquidity_distance")
                or stripped.startswith("def check_")
            ):
                name = stripped.split("(")[0].replace("def ", "")
                gates.append((name, lineno))
    return gates


def detect_watchdog() -> tuple[Path | None, list[str]]:
    """Find the watchdog file and list monitor hooks by keyword."""
    candidates = [
        REPO_ROOT / "scripts" / "watchdog.ps1",
        REPO_ROOT / "scripts" / "watchdog.bat",
        REPO_ROOT / "scripts" / "run_watchdog.py",
    ]
    wd = next((p for p in candidates if p.exists()), None)
    if not wd:
        return None, []
    content = wd.read_text(encoding="utf-8", errors="replace")
    keywords = [
        "ob_continuation_monitor",
        "api_refusal_monitor",
        "session_volatility_monitor",
        "sweep_divergence_monitor",
        "audit_session_volatility_sweep_status",
        "audit_notification_queue_dead_zone",
        "audit_storage_retention",
        "displacement_logger",
        "--profile redacted_account",
        "--profile ftmo",
    ]
    hits = [k for k in keywords if k in content]
    return wd.relative_to(REPO_ROOT), hits


def is_lfs_pointer_file(path: Path) -> bool:
    """Return True when a checked-out file is only a Git LFS pointer."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.readline().strip() == GIT_LFS_POINTER_HEADER
    except Exception:
        return False


def sparse_checkout_paths() -> tuple[bool, list[str]]:
    """Return active sparse-checkout directories for this worktree."""
    out = run("git sparse-checkout list")
    if not out or out.startswith("[") or out.startswith("fatal:"):
        return False, []
    return True, [line.strip().rstrip("/") for line in out.splitlines() if line.strip()]


def path_is_in_sparse_checkout(path: str, sparse_paths: list[str]) -> bool:
    """Approximate cone-mode sparse membership from `git sparse-checkout list`."""
    normalized = path.replace("\\", "/").strip("/")
    if "/" not in normalized:
        return True
    for sparse_path in sparse_paths:
        sparse_normalized = sparse_path.replace("\\", "/").strip("/")
        if not sparse_normalized:
            continue
        if normalized == sparse_normalized or normalized.startswith(f"{sparse_normalized}/"):
            return True
    return False


def fallback_lfs_hydration_status(raw_status: str, sparse_active: bool, sparse_paths: list[str]) -> dict[str, object]:
    """Best-effort LFS status when full `git lfs ls-files` is too slow.

    This keeps mandatory preflight usable in sparse/heavy-LFS worktrees. It does
    not claim repository-wide LFS completeness; it only inspects critical paths
    that are present in the active checkout and records the degraded inventory.
    """
    key_paths: list[tuple[str, str]] = []
    sparse_excluded_count = 0
    pointer_count = 0
    checked_out_count = 0
    missing_checked_out_count = 0
    for path in KEY_LFS_READINESS_PATHS:
        if sparse_active and not path_is_in_sparse_checkout(path, sparse_paths):
            sparse_excluded_count += 1
            key_paths.append((path, "sparse_excluded_lfs_inventory_degraded"))
            continue
        full_path = REPO_ROOT / path
        if not full_path.exists():
            missing_checked_out_count += 1
            key_paths.append((path, "not_present_in_active_checkout_lfs_inventory_degraded"))
            continue
        if is_lfs_pointer_file(full_path):
            pointer_count += 1
            key_paths.append((path, "present_as_lfs_pointer_inventory_degraded"))
            continue
        checked_out_count += 1
        key_paths.append((path, "present_not_lfs_pointer_inventory_degraded"))
    return {
        "status": f"degraded_lfs_inventory:{raw_status}",
        "row_count": "unknown",
        "missing_count": "unknown",
        "hydrated_count": "unknown",
        "sparse_active": sparse_active,
        "sparse_excluded_count": sparse_excluded_count,
        "key_paths": key_paths,
        "inventory_degraded": True,
        "checked_key_path_count": checked_out_count,
        "pointer_key_path_count": pointer_count,
        "missing_checked_key_path_count": missing_checked_out_count,
    }


def git_lfs_hydration_status() -> dict[str, object]:
    """Summarize whether Git LFS payloads are hydrated in this checkout."""
    sparse_active, sparse_paths = sparse_checkout_paths()
    if sparse_active and not FULL_LFS_INVENTORY:
        return fallback_lfs_hydration_status(
            "full_lfs_inventory_skipped_in_sparse_checkout; set GTOS_LIVE_STATE_FULL_LFS=1 to force",
            sparse_active,
            sparse_paths,
        )
    out = run_args(["git", "lfs", "ls-files", "--long"], timeout=DEFAULT_LFS_TIMEOUT_SECONDS)
    if out.startswith("["):
        return fallback_lfs_hydration_status(out, sparse_active, sparse_paths)
    rows = [line for line in out.splitlines() if line.strip()]
    missing_count = 0
    hydrated_count = 0
    sparse_excluded_count = 0
    key_paths: list[tuple[str, str]] = []
    key_set = set(KEY_LFS_READINESS_PATHS)
    for line in rows:
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        marker = parts[1]
        path = parts[2].replace("\\", "/")
        if marker == "-":
            if sparse_active and not path_is_in_sparse_checkout(path, sparse_paths):
                sparse_excluded_count += 1
                status = "sparse_excluded_not_hydrated"
            else:
                missing_count += 1
                status = "missing_payload_pointer_only"
        else:
            hydrated_count += 1
            status = "hydrated"
        if path in key_set:
            key_paths.append((path, status))
    return {
        "status": "ok",
        "row_count": len(rows),
        "missing_count": missing_count,
        "hydrated_count": hydrated_count,
        "sparse_active": sparse_active,
        "sparse_excluded_count": sparse_excluded_count,
        "key_paths": key_paths,
        "inventory_degraded": False,
    }


def shadow_log_freshness() -> list[tuple[str, str, str]]:
    """List shadow_logs/ files with last-modified + bounded line count."""
    logs_dir = REPO_ROOT / "shadow_logs"
    if not logs_dir.exists():
        return []
    rows: list[tuple[str, str, str]] = []
    exact_count_max_bytes = 10_000_000
    for p in sorted(list(logs_dir.glob("*.jsonl")) + list(logs_dir.glob("*.csv"))):
        try:
            stat = p.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            if is_lfs_pointer_file(p):
                line_count = "lfs_pointer_not_hydrated"
            elif stat.st_size <= exact_count_max_bytes:
                with open(p, encoding="utf-8", errors="replace") as f:
                    line_count = str(sum(1 for _ in f))
            else:
                mb = stat.st_size / 1_000_000
                line_count = f"skipped_large_file_{mb:.1f}MB"
            rows.append((p.name, mtime.strftime("%Y-%m-%d %H:%M UTC"), line_count))
        except Exception:
            rows.append((p.name, "ERR", "0"))
    return rows


def latest_handoff() -> str:
    """Find the highest-numbered handoff file, return its filename."""
    handoff_dir = REPO_ROOT / ".context" / "02_session_handoffs"
    if not handoff_dir.exists():
        return "(handoff directory missing)"
    files = sorted(handoff_dir.glob("*.md"))
    if not files:
        return "(no handoffs found)"
    return files[-1].name


def captured_research_commit() -> str:
    if not RESEARCH_CURRENT_STATE.exists():
        return "(missing)"
    text = RESEARCH_CURRENT_STATE.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"Latest research commit captured:\s*`([^`]+)`", text)
    if not match:
        return "(not declared)"
    return match.group(1)


def _short_sha(value: str) -> str:
    if not value or value.startswith("(") or value.startswith("["):
        return value
    return value.split()[0]


def research_context_freshness() -> dict[str, str | bool]:
    latest = latest_research_commit()
    captured = captured_research_commit()
    latest_sha = _short_sha(latest)
    captured_sha = _short_sha(captured)
    refs_ok = True
    missing_refs: list[str] = []
    for path in RESEARCH_CONTEXT_REFERENCES:
        if not path.exists():
            refs_ok = False
            missing_refs.append(str(path.relative_to(REPO_ROOT)))
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for required_variants in (
            (
                ".context/00_core/research_operating_doctrine.md",
                "00_core/research_operating_doctrine.md",
            ),
            (
                ".context/00_core/research_current_state.md",
                "00_core/research_current_state.md",
            ),
        ):
            if not any(required in text for required in required_variants):
                refs_ok = False
                missing_refs.append(f"{path.relative_to(REPO_ROOT)} missing {required_variants[0]}")
    if not RESEARCH_DOCTRINE.exists() or not RESEARCH_CURRENT_STATE.exists():
        status = "MISSING_CONTEXT_DOC"
    elif latest_sha in {"", "(missing)", "(not declared)"} or latest_sha.startswith("["):
        status = "UNKNOWN_LATEST_RESEARCH_COMMIT"
    elif captured_sha in {"", "(missing)", "(not declared)"}:
        status = "MISSING_CAPTURED_RESEARCH_COMMIT"
    elif latest_sha == captured_sha:
        status = "FRESH"
    else:
        status = "STALE_UPDATE_RESEARCH_CURRENT_STATE"
    return {
        "status": status,
        "latest_research_commit": latest or "(none)",
        "captured_research_commit": captured,
        "doctrine_exists": RESEARCH_DOCTRINE.exists(),
        "current_state_exists": RESEARCH_CURRENT_STATE.exists(),
        "mandatory_references_ok": refs_ok,
        "missing_references": "; ".join(missing_refs) if missing_refs else "none",
    }


def build_report() -> str:
    cfg, cfg_path = read_config()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines: list[str] = []
    lines.append("# GTOS LIVE STATE (auto-generated — DO NOT HAND-EDIT)")
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**HEAD:** `{git_head()}`")
    lines.append(f"**Latest handoff on disk:** `.context/02_session_handoffs/{latest_handoff()}`")
    lines.append("")
    lines.append(
        "This file is the single source of truth for the _current_ GTOS state. "
        "It is rebuilt by `scripts/generate_live_state.py` from git + config + source. "
        "Handoffs are historical snapshots and will NOT reflect post-session changes; "
        "trust this file over any handoff when they disagree."
    )
    lines.append("")
    lines.append(
        "**Regenerate at session start, and again before producing any status/backlog synthesis.**"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # === RESEARCH CONTEXT FRESHNESS ===
    freshness = research_context_freshness()
    lines.append("## Research context freshness")
    lines.append("")
    lines.append(
        "Curated research context lives in `.context/00_core/research_operating_doctrine.md` "
        "and `.context/00_core/research_current_state.md`. These docs are agent-updated, "
        "not auto-generated; this section only audits whether the current-state doc is "
        "stale versus the latest research-relevant commit."
    )
    lines.append("")
    lines.append("| Check | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| Status | `{freshness['status']}` |")
    lines.append(f"| Latest research-relevant commit | `{freshness['latest_research_commit']}` |")
    lines.append(f"| Current-state captured commit | `{freshness['captured_research_commit']}` |")
    lines.append(f"| Doctrine doc exists | `{freshness['doctrine_exists']}` |")
    lines.append(f"| Current-state doc exists | `{freshness['current_state_exists']}` |")
    lines.append(f"| Mandatory references ok | `{freshness['mandatory_references_ok']}` |")
    lines.append(f"| Missing references | `{freshness['missing_references']}` |")
    lines.append("")
    if freshness["status"] != "FRESH" or not freshness["mandatory_references_ok"]:
        lines.append(
            "**Action:** read the newer research artifacts directly and update "
            "`.context/00_core/research_current_state.md` before relying on its summary."
        )
        lines.append("")

    # === GIT STATUS ===
    status = git_status_short()
    lines.append("## Git status")
    lines.append("")
    if not status:
        lines.append("Clean working tree.")
    else:
        lines.append("```")
        lines.append(status)
        lines.append("```")
        diff_stat = git_diff_stat(status)
        if diff_stat:
            lines.append("")
            lines.append("### Uncommitted diff (tracked files, bounded stat)")
            lines.append("```")
            lines.append(diff_stat)
            lines.append("```")
    lines.append("")

    # === GIT LFS HYDRATION ===
    lfs_status = git_lfs_hydration_status()
    lines.append("## Git LFS hydration")
    lines.append("")
    lines.append("| Check | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| Status | `{lfs_status['status']}` |")
    lines.append(f"| LFS tracked rows | `{lfs_status['row_count']}` |")
    lines.append(f"| Hydrated payload rows | `{lfs_status['hydrated_count']}` |")
    lines.append(f"| Sparse checkout active | `{lfs_status.get('sparse_active', False)}` |")
    lines.append(f"| Sparse-excluded LFS rows | `{lfs_status.get('sparse_excluded_count', 0)}` |")
    lines.append(f"| Missing pointer-only rows | `{lfs_status['missing_count']}` |")
    if lfs_status.get("inventory_degraded"):
        lines.append(f"| Checked key paths in degraded mode | `{lfs_status.get('checked_key_path_count', 0)}` |")
        lines.append(f"| Pointer key paths in degraded mode | `{lfs_status.get('pointer_key_path_count', 0)}` |")
        lines.append(f"| Missing key paths in degraded mode | `{lfs_status.get('missing_checked_key_path_count', 0)}` |")
    lines.append("")
    key_paths = lfs_status.get("key_paths") or []
    if key_paths:
        lines.append("Key runtime/research LFS paths:")
        lines.append("")
        lines.append("| Path | Hydration status |")
        lines.append("|------|------------------|")
        for path, status_value in key_paths:
            lines.append(f"| `{path}` | `{status_value}` |")
        lines.append("")
    if lfs_status.get("sparse_excluded_count"):
        lines.append(
            "**Sparse note:** sparse-excluded LFS rows are intentionally outside this "
            "worktree's active checkout. They are not evidence of current-branch LFS "
            "object loss; expand the sparse checkout or use a route-specific evidence "
            "cache before claiming row-level facts from those files."
        )
        lines.append("")

    if lfs_status.get("inventory_degraded"):
        lines.append(
            "**Action:** full `git lfs ls-files --long` did not finish inside the "
            "bounded live-state timeout. Treat repository-wide LFS counts as unknown "
            "in this run; use the key-path rows below plus route-specific selective "
            "hydration before claiming row-level facts from LFS-backed files."
        )
        lines.append("")
    elif lfs_status["missing_count"]:
        lines.append(
            "**Action:** missing LFS rows are committed pointers, not readable payloads. "
            "Use a route-specific local evidence cache or selective LFS hydration before "
            "claiming row-level facts from those files."
        )
        lines.append("")

    # === RECENT COMMITS ===
    lines.append("## Last 20 runtime/research commits")
    lines.append("")
    lines.append("```")
    lines.append(recent_commits(20))
    lines.append("```")
    lines.append("")

    # === ACTIVE CONFIG ===
    lines.append(f"## Active config (`{cfg_path}`)")
    lines.append("")
    lines.append("| Setting | Key | Value |")
    lines.append("|---------|-----|-------|")
    for label, key in SURFACED_CONFIG_KEYS:
        val = dig(cfg, key)
        val_str = "_missing_" if val is None else f"`{val}`"
        lines.append(f"| {label} | `{key}` | {val_str} |")
    lines.append("")

    # === ENFORCEMENT CHECK ===
    lines.append("## Config-flag enforcement check")
    lines.append("")
    lines.append(
        "For each flag: count of matches in `src/`. **`0` = flag may be cosmetic — investigate before relying on it.** "
        "A non-zero count is necessary but not sufficient — the grep can hit logging strings, etc. Treat this as a starter signal, not proof."
    )
    lines.append("")
    lines.append("| Flag | Config value | src/ matches | Description |")
    lines.append("|------|--------------|--------------|-------------|")
    for path, pattern, desc in ENFORCEMENT_CHECKS:
        val = dig(cfg, path)
        count = grep_count(pattern)
        flag = "**0 (suspicious)**" if count == 0 else str(count)
        val_str = "_missing_" if val is None else f"`{val}`"
        lines.append(f"| `{path}` | {val_str} | {flag} | {desc} |")
    lines.append("")

    # === PERMISSIONS GATES ===
    lines.append("## Active gates (`src/components/permissions.py`)")
    lines.append("")
    gates = list_permissions_gates()
    if gates:
        for name, lineno in gates:
            lines.append(f"- `{name}` — line {lineno}")
    else:
        lines.append("_permissions.py not readable_")
    lines.append("")

    # === WATCHDOG ===
    lines.append("## Watchdog integrations")
    lines.append("")
    wd_path, hits = detect_watchdog()
    if wd_path:
        lines.append(f"Watchdog file: `{wd_path}`")
        lines.append("")
        if hits:
            lines.append("Integrated hooks (substring matches):")
            for h in hits:
                lines.append(f"- `{h}`")
        else:
            lines.append("_no recognized monitor hooks found_")
    else:
        lines.append("_no watchdog script found_")
    lines.append("")

    # === SHADOW LOG FRESHNESS ===
    lines.append("## Shadow-log freshness (`shadow_logs/`)")
    lines.append("")
    rows = shadow_log_freshness()
    if rows:
        lines.append("| Log | Last modified | Lines |")
        lines.append("|-----|---------------|-------|")
        for name, mtime, n in rows:
            lines.append(f"| {name} | {mtime} | {n} |")
    else:
        lines.append("_no shadow_logs/ directory_")
    lines.append("")

    # === FOOTER ===
    lines.append("---")
    lines.append("")
    lines.append("## Verification flow when a doc says \"X is open\"")
    lines.append("")
    lines.append("1. Check **Git status** above — if claimed-uncommitted is not listed, the doc is stale.")
    lines.append("2. Scan **Last 20 runtime/research commits** — if a matching commit appears, the doc is stale.")
    lines.append("3. Grep the relevant code file — if enforcement exists, the doc is stale.")
    lines.append("4. Trust this file. Update the stale doc in the same session.")

    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(report, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
