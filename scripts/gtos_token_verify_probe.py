#!/usr/bin/env python3
"""Read-only activation-token verify probe.

Three bindings, every fire:

* F5 (``activation-f5``): profile ``operator_profile`` / ns
  ``operator`` / launch-contract args taken from the RUNNING worker
  argv via the same extract as ``f5_true_contract_mint.ps1`` (tags, q1
  mode/selection, q2). Config bytes come from the F5 tree, CWD-independent.
  If that argv is unreadable, the F5 row is ``UNKNOWN`` — the probe
  never invents ``--tags`` or any other contract field.
* Production (``activation``): both books, MSI repo
  ``C:\\Users\\MSI\\Documents\\ai-trading-agent``, config + profile only
  (no launch contract). CWD-independent.

Never mints. Never writes, rotates, or deletes a token. Never imports
``build_token`` / ``write_token`` / ``cmd_mint``.

On any ``valid:false`` or ``UNKNOWN``: one alert line through the same
notifier path ``.tools/monitor_books.py:send`` uses, plus an append-only
JSONL row. On all ``valid:true``: the log row only.

The scheduled-task wrapper is ``scripts/gtos_token_verify_probe.ps1``.
This module is the parse + verify + alert engine so the parsing can be
synthetic-tested on the Mac. The orchestrator deploys tonight; this file
registers nothing.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.mt5.mt5_interface import magic_for_namespace  # noqa: E402
from src.safety.activation_token import (  # noqa: E402
    config_digest_for,
    launch_contract_digest_for,
    normalized_f5_launch_contract,
    profile_path_for,
    read_token,
    verify_token,
)

SCHEMA = "gtos.token_verify_probe.v1"
F5_PROFILE = "operator_profile"
F5_NAMESPACE = "operator"
PROD_FTMO = {
    "book": "prod_ftmo",
    "profile": "operator_profile",
    "namespace": "operator_profile",
}
PROD_FN = {
    "book": "prod_fn",
    "profile": "redacted_account",
    "namespace": "redacted_account_live_bee34003",
}

# Flags that bind the F5 launch contract. Missing required flags => UNKNOWN.
_F5_REQUIRED_FLAGS = ("namespace", "profile", "f5-minimal-size-usd", "tags")
_STORE_TRUE = frozenset({
    "event-clock-shadow",
    "frozen-intent-reprice",
    "judgment-rescue",
    "once",
    "recover-pre-gap-bar",
    "vol-level-tilt",
})

# Canonical true-contract extract — lockstep with
# host-local\gtos-agent-sessions\f5_true_contract_mint.ps1
# (--risk-unit-floor-mode also starts with --risk-unit-floor; the bare-flag
# regex requires whitespace after the name, so it cannot eat the mode flag.)
_RE_TRUE_TAGS = re.compile(r"--tags\s+(\S+)")
_RE_TRUE_Q1_MODE = re.compile(r"--risk-unit-floor-mode\s+(\S+)")
_RE_TRUE_Q1_SEL = re.compile(r"--risk-unit-floor\s+([a-z0-9_,]+)")
_RE_TRUE_Q2 = re.compile(r"--event-clock-shadow(?:\s|$)")


# ---------------------------------------------------------------------------
# Parsing (synthetic-tested; this is the "don't guess" surface)
# ---------------------------------------------------------------------------

def split_windows_command_line(command_line: str | None) -> list[str]:
    """Split a Win32 CommandLine on unquoted whitespace.

    Good enough for ``run_book.py`` argv: a quoted python path, an optional
    quoted script path, unquoted ``--flags``, comma-separated ``--tags``.
    Does not implement the full CommandLineToArgvW backslash table — F5
    tags and paths do not need it.
    """
    if command_line is None:
        return []
    text = str(command_line).strip()
    if not text:
        return []
    out: list[str] = []
    buf: list[str] = []
    in_quote = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '"':
            in_quote = not in_quote
            i += 1
            continue
        if ch in " \t" and not in_quote:
            if buf:
                out.append("".join(buf))
                buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    if buf:
        out.append("".join(buf))
    return out


def parse_run_book_flags(argv: list[str]) -> dict[str, Any]:
    """Extract ``--flag value`` / ``--flag`` / ``--flag=value`` from argv.

    Unknown flags are kept. Missing flags are absent — callers must not
    fill them in from a ceremony pack.
    """
    flags: dict[str, Any] = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if not tok.startswith("--"):
            i += 1
            continue
        body = tok[2:]
        if "=" in body:
            name, value = body.split("=", 1)
            flags[name] = True if name in _STORE_TRUE else value
            i += 1
            continue
        if body in _STORE_TRUE:
            flags[body] = True
            i += 1
            continue
        if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            flags[body] = argv[i + 1]
            i += 2
            continue
        flags[body] = ""
        i += 1
    return flags


def extract_true_contract_from_command_line(command_line: str | None) -> dict[str, Any]:
    """Extract tags / q1 / q2 exactly as ``f5_true_contract_mint.ps1`` does.

    Law (2026-08-18): any F5 mint/verify must carry the full launch contract
    taken from the RUNNING worker CommandLine. The mint recipe is the
    canonical extract; this function is its Python twin. Missing tags stay
    ``None`` — callers must not invent them.
    """
    text = str(command_line or "")
    tags_m = _RE_TRUE_TAGS.search(text)
    q1_mode_m = _RE_TRUE_Q1_MODE.search(text)
    q1_sel_m = _RE_TRUE_Q1_SEL.search(text)
    return {
        "tags": tags_m.group(1) if tags_m else None,
        "q1_mode": q1_mode_m.group(1) if q1_mode_m else "off",
        "q1_selection": q1_sel_m.group(1) if q1_sel_m else None,
        "q2_enabled": bool(_RE_TRUE_Q2.search(text)),
    }


def apply_true_contract_to_flags(flags: dict[str, Any], command_line: str | None) -> dict[str, Any]:
    """Overlay the mint-recipe extract onto parsed flags (q1/q2/tags only)."""
    true = extract_true_contract_from_command_line(command_line)
    if true["tags"]:
        flags["tags"] = true["tags"]
    flags["risk-unit-floor-mode"] = true["q1_mode"]
    if true["q1_selection"]:
        flags["risk-unit-floor"] = true["q1_selection"]
    elif flags.get("risk-unit-floor") == "":
        flags["risk-unit-floor"] = None
    if true["q2_enabled"]:
        flags["event-clock-shadow"] = True
    else:
        flags.pop("event-clock-shadow", None)
    return flags


def resolve_config_path(config: str | Path, repo_root: Path) -> Path:
    """Bind a (usually relative) --config to the book tree, CWD-independent.

    ``config_digest_for`` hashes ``Path(config)`` as given. A relative
    ``config/agent_config.yaml`` is therefore a CWD hash. The scheduled
    probe (empty WorkingDirectory → System32) and any fire from
    grok-jobs then get ``None`` and report a false
    ``activation_token_config_digest_unsatisfied``. The token was minted
    against the book tree; verify against those same bytes.
    """
    path = Path(config)
    if not path.is_absolute():
        path = Path(repo_root) / path
    return path


def repo_root_from_argv(argv: list[str]) -> Path | None:
    """Repo root from an absolute run_book.py path, only if that tree exists.

    A Windows path harvested on the Mac test host must not displace the
    explicit ``--f5-repo`` / ``--prod-repo``. On the VPS the path exists
    and is the tree the worker actually loaded.
    """
    for tok in argv:
        cleaned = tok.strip().strip('"')
        if cleaned.endswith("run_book.py"):
            path = Path(cleaned)
            if path.is_absolute() and path.is_file():
                return path.parent
    return None


def f5_contract_from_flags(flags: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Build the verify kwargs for the F5 launch contract, or an UNKNOWN reason.

    Reproduces ``run_book.py`` defaults only for flags the worker actually
    omitted (so the digest matches what the process bound). A missing
    *required* flag is UNKNOWN, never filled from a sidecar.
    """
    missing = [name for name in _F5_REQUIRED_FLAGS if not str(flags.get(name) or "").strip()]
    if missing:
        return None, "f5_argv_missing:" + ",".join(missing)
    namespace = str(flags["namespace"]).strip()
    if namespace != F5_NAMESPACE:
        return None, f"f5_argv_namespace_not_f5:{namespace}"
    profile = str(flags["profile"]).strip()
    try:
        size = float(flags["f5-minimal-size-usd"])
    except (TypeError, ValueError):
        return None, "f5_argv_size_unreadable"
    notional_raw = flags.get("f5-notional-initial-usd")
    if notional_raw in (None, ""):
        notional = 100000.0  # run_book.py default; worker omitted the flag
    else:
        try:
            notional = float(notional_raw)
        except (TypeError, ValueError):
            return None, "f5_argv_notional_unreadable"
    q1_mode = str(flags.get("risk-unit-floor-mode") or "off")
    q1_selection = flags.get("risk-unit-floor")
    if q1_selection == "":
        q1_selection = None
    try:
        contract = normalized_f5_launch_contract(
            f5_enabled=True,
            target_risk_usd=size,
            notional_initial_usd=notional,
            tags=str(flags["tags"]),
            namespace=namespace,
            magic=magic_for_namespace(namespace),
            profile=profile,
            q1_mode=q1_mode,
            q1_selection=q1_selection,
            q2_enabled=bool(flags.get("event-clock-shadow")),
        )
    except ValueError as exc:
        return None, f"f5_launch_contract_refused:{exc}"
    return {
        "profile": profile,
        "namespace": namespace,
        "config": str(flags.get("config") or "config/agent_config.yaml"),
        "launch_contract": contract,
    }, None


def parse_f5_worker_command_line(
    command_line: str | None,
) -> tuple[dict[str, Any] | None, str | None, list[str]]:
    """Return ``(contract_kwargs, unknown_reason, argv)``.

    ``unknown_reason`` set means: do not guess, emit UNKNOWN.
    """
    argv = split_windows_command_line(command_line)
    if not argv:
        return None, "f5_worker_argv_unreadable", []
    if not any(tok.endswith("run_book.py") or tok.endswith("run_book.py\"") for tok in argv):
        if not any("run_book.py" in tok for tok in argv):
            return None, "f5_worker_argv_unreadable", argv
    flags = parse_run_book_flags(argv)
    apply_true_contract_to_flags(flags, command_line)
    contract, reason = f5_contract_from_flags(flags)
    return contract, reason, argv


# ---------------------------------------------------------------------------
# Verify (read-only)
# ---------------------------------------------------------------------------

def _load_profile_login_digest(profile: str, repo_root: Path) -> str:
    import yaml

    path = profile_path_for(profile, repo_root=repo_root)
    if not path.is_file():
        raise FileNotFoundError(f"profile not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    expected = ((data.get("broker_profile") or {}).get("expected_account") or {})
    digest = str(expected.get("login_sha256") or "")
    if not digest:
        raise ValueError(f"{path} has no broker_profile.expected_account.login_sha256")
    return digest


def verify_binding(
    *,
    book: str,
    profile: str,
    namespace: str,
    token_dir: Path,
    repo_root: Path,
    config: str = "config/agent_config.yaml",
    launch_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One read-only verify_token. Never writes."""
    row: dict[str, Any] = {
        "book": book,
        "profile": profile,
        "namespace": namespace,
        "token_dir": str(token_dir),
        "repo_root": str(repo_root),
        "valid": False,
        "reason": "",
        "detail": "",
        "path": None,
        "expires_utc": None,
        "live_config_digest_sha256": None,
        "launch_contract_digest_sha256": None,
        "config_resolved": None,
    }
    config_path = resolve_config_path(config, repo_root)
    row["config_resolved"] = str(config_path)
    try:
        digest = _load_profile_login_digest(profile, repo_root)
    except (OSError, ValueError) as exc:
        row["reason"] = "profile_unreadable"
        row["detail"] = str(exc)
        return row
    token, status, path = read_token(digest, directory=token_dir)
    row["path"] = str(path)
    if token is None:
        row["reason"] = status or "activation_token_absent"
        present = sorted(p.name for p in token_dir.glob("*.token.json")) if token_dir.is_dir() else []
        row["detail"] = (
            f"queried_login_sha256={digest}; "
            f"present_tokens={present}; status={status}"
        )
        return row
    row["expires_utc"] = token.get("expires_utc")
    config_digest = config_digest_for(
        config_path, profile, repo_root=repo_root, launch_contract=launch_contract,
    )
    row["live_config_digest_sha256"] = config_digest
    if launch_contract is not None:
        row["launch_contract_digest_sha256"] = launch_contract_digest_for(launch_contract)
    ok, reason, detail = verify_token(
        token,
        account_login_sha256=digest,
        namespace=namespace,
        config_digest_sha256=config_digest,
        require_namespace_binding=launch_contract is not None,
        require_config_digest_binding=launch_contract is not None,
        directory=token_dir,
    )
    row["valid"] = bool(ok)
    row["reason"] = reason
    row["detail"] = detail
    return row


def unknown_row(book: str, detail: str, **extra: Any) -> dict[str, Any]:
    row = {
        "book": book,
        "valid": False,
        "reason": "UNKNOWN",
        "detail": detail,
    }
    row.update(extra)
    return row


def run_probe(
    *,
    f5_command_line: str | None,
    f5_token_dir: Path,
    f5_repo: Path,
    prod_token_dir: Path,
    prod_repo: Path,
    prod_ftmo_command_line: str | None = None,
    prod_fn_command_line: str | None = None,
) -> dict[str, Any]:
    bindings: list[dict[str, Any]] = []

    f5_contract, f5_unknown, f5_argv = parse_f5_worker_command_line(f5_command_line)
    if f5_unknown or f5_contract is None:
        bindings.append(unknown_row(
            "f5",
            f5_unknown or "f5_worker_argv_unreadable",
            token_dir=str(f5_token_dir),
            argv_present=bool(f5_argv),
        ))
    else:
        # F5 tree is the F5 repo. A relative run_book.py in argv must not
        # displace it (workers launch with cwd=repo and a relative script).
        bindings.append(verify_binding(
            book="f5",
            profile=f5_contract["profile"],
            namespace=f5_contract["namespace"],
            token_dir=f5_token_dir,
            repo_root=f5_repo,
            config=f5_contract["config"],
            launch_contract=f5_contract["launch_contract"],
        ))

    for spec, live_cl in (
        (PROD_FTMO, prod_ftmo_command_line),
        (PROD_FN, prod_fn_command_line),
    ):
        # Law: prod verifies against the MSI tree, config + profile only.
        # Never compose a launch contract. Never let a relative run_book.py
        # or a foreign argv displace C:\Users\MSI\Documents\ai-trading-agent.
        repo = prod_repo
        namespace = spec["namespace"]
        profile = spec["profile"]
        config = "config/agent_config.yaml"
        if live_cl:
            argv = split_windows_command_line(live_cl)
            flags = parse_run_book_flags(argv)
            if flags.get("namespace"):
                namespace = str(flags["namespace"])
            if flags.get("profile"):
                profile = str(flags["profile"])
            if flags.get("config"):
                # filename / relative path only; still resolved under MSI.
                raw_cfg = Path(str(flags["config"]))
                config = raw_cfg.name if raw_cfg.is_absolute() else str(raw_cfg)
        bindings.append(verify_binding(
            book=spec["book"],
            profile=profile,
            namespace=namespace,
            token_dir=prod_token_dir,
            repo_root=repo,
            config=config,
        ))

    failing = [row for row in bindings if not row.get("valid")]
    return {
        "schema": SCHEMA,
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "bindings": bindings,
        "any_invalid": bool(failing),
        "failing_books": [row["book"] for row in failing],
    }


# ---------------------------------------------------------------------------
# Alert + log (monitor_books notifier path; never mint)
# ---------------------------------------------------------------------------

def send_monitor_alert(message: str, *, queue_path: Path | None = None) -> None:
    """One line through the path ``.tools/monitor_books.py:send`` uses.

    Grant first: without ``authorize_operator_delivery`` the queue refuses
    delivery even when Telegram creds are present (F30 polarity).

    Queue path is the F5-tree file, CWD-independent. Empty scheduled-task
    WorkingDirectory otherwise appends HIGH rows under System32 (measured
    08-21 06:00Z through 08-23 06:00Z). Flush once: HIGH is polled at 30s
    and this process exits in seconds, so enqueue-without-flush never
    attempts transport.
    """
    try:
        from src.safety.notification_authorization import authorize_operator_delivery
        authorize_operator_delivery(reason="scripts/gtos_token_verify_probe.py")
    except Exception:
        pass
    if queue_path is not None:
        os.environ["GTOS_NOTIFICATION_QUEUE_PATH"] = str(Path(queue_path).resolve())
    try:
        from src.utils.notification_queue import Level, send as _q, get_default_queue
        _q(message, level=Level.HIGH)
        get_default_queue().flush()
        return
    except Exception:
        pass
    try:
        from src.notifications import _send_async
        _send_async(message)
    except Exception:
        pass


def format_alert(payload: dict[str, Any]) -> str:
    parts = []
    for row in payload.get("bindings") or []:
        if row.get("valid"):
            continue
        parts.append(
            f"{row.get('book')}:{row.get('reason')}"
            + (f" ({row.get('detail')})" if row.get("detail") else "")
        )
    joined = "; ".join(parts) or "unknown"
    return f"🚨 TOKEN-VERIFY: valid:false — {joined}"


def append_log(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, sort_keys=True, default=str)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--f5-command-line", default=None,
                        help="Win32 CommandLine of the running operator worker")
    parser.add_argument("--f5-token-dir", required=True)
    parser.add_argument("--f5-repo", required=True)
    parser.add_argument("--prod-token-dir", required=True)
    parser.add_argument("--prod-repo", required=True)
    parser.add_argument("--prod-ftmo-command-line", default=None)
    parser.add_argument("--prod-fn-command-line", default=None)
    parser.add_argument(
        "--log",
        default=None,
        help="append-only JSONL (default <f5-repo>/shadow_logs/token_verify_probe.jsonl)",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="log as usual; do not send the alert")
    args = parser.parse_args(argv)

    payload = run_probe(
        f5_command_line=args.f5_command_line,
        f5_token_dir=Path(args.f5_token_dir),
        f5_repo=Path(args.f5_repo),
        prod_token_dir=Path(args.prod_token_dir),
        prod_repo=Path(args.prod_repo),
        prod_ftmo_command_line=args.prod_ftmo_command_line,
        prod_fn_command_line=args.prod_fn_command_line,
    )
    log_path = Path(args.log) if args.log else (
        Path(args.f5_repo) / "shadow_logs" / "token_verify_probe.jsonl"
    )
    append_log(log_path, payload)
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    if payload["any_invalid"] and not args.dry_run:
        send_monitor_alert(
            format_alert(payload),
            queue_path=Path(args.f5_repo) / "pipeline_state" / "notification_queue.jsonl",
        )
    return 1 if payload["any_invalid"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
