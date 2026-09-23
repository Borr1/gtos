"""Provider adapter — subscription CLIs behind one failover seam.

Config-driven ordered provider list (claude -> cursor-agent -> codex). Each call:
build argv, feed the prompt via STDIN (never argv — argv length caps were a
measured failure mode of the retired bot runtime), per-call timeout, capture
stdout, extract the outermost verdict JSON, strict schema-key check. Per-call
log line: provider, latency_ms, ok/fail, bytes. Failover down the list; all
providers dark -> ``None`` (the caller writes nothing — seam fail-open).

Windows (the VPS) and macOS (tests) both work: executables are resolved via
PATH first, then known absolute fallbacks (claude lives at
``C:\\Users\\Administrator\\.local\\bin\\claude.exe`` on the VPS). Tests inject
fake providers (``argv=["/bin/bash", script]``) — nothing here shells out to a
real model in CI.

``--smoke`` sends a trivial prompt to each configured provider and prints
latency — run it on the VPS before arming the scheduled task.
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

_REPO_FOR_IMPORT = Path(__file__).resolve().parents[2]
if str(_REPO_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_REPO_FOR_IMPORT))

from scripts.f5_desk import common

_log = logging.getLogger("f5_desk.adapter")

VERDICT_SCHEMA = "gtos.f5.judge.verdict.v1"
DEFAULT_TIMEOUT_S = 240
MAX_STDOUT_BYTES = 4 * 1024 * 1024  # never scan more than 4 MB of provider output

# Known absolute locations per provider, tried after PATH. Order matters.
_WINDOWS_FALLBACKS = {
    "claude": [
        r"host-local\.local\bin\claude.exe",
        r"host-local\AppData\Roaming\npm\claude.cmd",
    ],
    "cursor-agent": [
        r"host-local\AppData\Local\cursor-agent\cursor-agent.ps1",
        r"host-local\AppData\Local\cursor-agent\cursor-agent.cmd",   # CONTRACT V2: the chair loop's own binary
        r"host-local\.local\bin\cursor-agent.exe",
        r"host-local\AppData\Roaming\npm\cursor-agent.cmd",
    ],
    "codex": [
        r"host-local\.local\bin\codex.exe",
        r"host-local\AppData\Roaming\npm\codex.cmd",
    ],
}
_POSIX_FALLBACKS = {
    "claude": ["~/.local/bin/claude"],
    "cursor-agent": ["~/.local/bin/cursor-agent"],
    "codex": ["~/.local/bin/codex"],
}


def _resolve_exe(name: str) -> Optional[str]:
    found = shutil.which(name)
    if found:
        return found
    table = _WINDOWS_FALLBACKS if sys.platform.startswith("win") else _POSIX_FALLBACKS
    for candidate in table.get(name, []):
        p = Path(candidate).expanduser()
        if p.is_file():
            return str(p)
    return None


def _argv_for(name: str, exe: Optional[str]) -> list[str]:
    """Build argv. A .ps1 must be invoked through powershell so Windows
    actually runs it. --trust is required for cursor-agent on this host."""
    if exe and str(exe).lower().endswith(".ps1"):
        base = [
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", exe,
        ]
    elif exe and str(exe).lower().endswith((".cmd", ".bat")):
        base = ["cmd.exe", "/c", exe]   # CONTRACT V2: run batch wrappers through cmd explicitly
    else:
        base = [exe or name]
    if name == "claude":
        return base + ["-p", "--output-format", "json"]
    if name == "cursor-agent":
        return base + ["--trust", "-p", "--output-format", "text"]
    if name == "codex":
        return base + ["exec", "-"]
    return base


def default_providers() -> list[dict]:
    """Intelligence is Grok Bot only (owner 2026-08-27). Claude, Cursor,
    and Codex subscription CLIs are not this layer. Empty list =>
    call_with_failover returns None (fail-open, page). Grok writes
    verdicts through the chair/shim, not these CLIs."""
    # CONTRACT V2 (Fable 5.1, 2026-09-02): Grok Bot has been dark on usage since 1 Sep and a judge
    # with no provider is a monitor. The subscription CLIs already on this host are tried in order;
    # call_with_failover skips a missing exe. Owner word 2 Sep: every updated intelligence into it.
    out = []
    # Owner 2026-09-02 12:23 ICT: Grok / Grok Bot / Cursor / Fable-advisor. No Codex sub. Claude not this layer.
    # CONTRACT V3 (Fable 5.1, 2026-09-02 07:30Z): cursor-agent -p never returned -- 72 of 72 cycles today
    # timed out at 240 s with 0 bytes (adapter_calls.jsonl) while the loop spawned 5-9 minute zombies.
    # The judge's intelligence is the Grok Bot chair writing judgment/inbox/verdict.json (provider
    # 'grok-inbox', the path that produced every real verdict on 31 Aug). No CLI provider here.
    for name in ():
        exe = _resolve_exe(name)
        if exe is None:
            continue
        out.append({"name": name, "argv": _argv_for(name, exe), "missing": False})
    return out


# ---------------------------------------------------------------------------
# verdict extraction — outermost JSON object with the right schema key
# ---------------------------------------------------------------------------
def _iter_json_objects(text: str, *, max_objects: int = 50) -> list[Any]:
    """Every parseable top-level JSON object found in ``text``, in order.
    Balanced-scan via raw_decode from each '{'; skips over parsed spans."""
    decoder = json.JSONDecoder()
    out: list[Any] = []
    idx = 0
    n = len(text)
    while idx < n and len(out) < max_objects:
        start = text.find("{", idx)
        if start < 0:
            break
        try:
            obj, end = decoder.raw_decode(text, start)
        except ValueError:
            idx = start + 1
            continue
        out.append(obj)
        idx = end
    return out


def _unwrap_strings(obj: Any, depth: int = 0) -> list[str]:
    """String payloads a CLI envelope might hide the verdict inside
    ({"result": "..."}, {"content":[{"text": "..."}]}, nested)."""
    if depth > 3:
        return []
    found: list[str] = []
    if isinstance(obj, str):
        if "{" in obj:
            found.append(obj)
    elif isinstance(obj, dict):
        for key in ("result", "text", "content", "output", "message", "response", "completion"):
            if key in obj:
                found.extend(_unwrap_strings(obj[key], depth + 1))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_unwrap_strings(item, depth + 1))
    return found


def extract_verdict(text: str) -> tuple[Optional[dict], str]:
    """(verdict_dict, "ok") or (None, reason). Strict: the object must carry
    ``schema == gtos.f5.judge.verdict.v1``. Never raises."""
    try:
        if not text or not text.strip():
            return None, "empty_output"
        if len(text) > MAX_STDOUT_BYTES:
            text = text[-MAX_STDOUT_BYTES:]
        queue = [text]
        seen_objects = 0
        for _pass in range(4):  # text -> objects -> wrapped strings -> ...
            next_queue: list[str] = []
            for chunk in queue:
                for obj in _iter_json_objects(chunk):
                    seen_objects += 1
                    if isinstance(obj, dict) and obj.get("schema") == VERDICT_SCHEMA:
                        return obj, "ok"
                    next_queue.extend(_unwrap_strings(obj))
            if not next_queue:
                break
            queue = next_queue
        if seen_objects:
            return None, "schema_mismatch"
        return None, "no_json_object"
    except Exception as exc:
        _log.warning("adapter: extract_verdict failed (%r)", exc)
        return None, "extract_error"


# ---------------------------------------------------------------------------
# calls
# ---------------------------------------------------------------------------
def call_provider(provider: dict, prompt: str,
                  timeout_s: float = DEFAULT_TIMEOUT_S) -> dict:
    """One provider, one prompt. Returns
    {name, ok, latency_ms, stdout_bytes, fail_reason, verdict}. Never raises."""
    name = str(provider.get("name") or "?")
    result: dict[str, Any] = {
        "name": name, "ok": False, "latency_ms": None,
        "stdout_bytes": 0, "stdout_sha16": None, "fail_reason": None, "verdict": None,
    }
    if provider.get("missing"):
        result["fail_reason"] = "executable_not_found"
        return result
    argv = provider.get("argv")
    if not isinstance(argv, list) or not argv:
        result["fail_reason"] = "bad_provider_config"
        return result
    started = time.monotonic()
    try:
        proc = subprocess.run(
            [str(a) for a in argv],
            input=prompt.encode("utf-8", errors="replace"),
            capture_output=True,
            timeout=float(timeout_s),
        )
        result["latency_ms"] = round((time.monotonic() - started) * 1000.0, 1)
        stdout = (proc.stdout or b"")[:MAX_STDOUT_BYTES].decode("utf-8", errors="replace")
        result["stdout_bytes"] = len(proc.stdout or b"")
        result["stdout_sha16"] = common.sha256_hex(proc.stdout or b"")[:16]
        verdict, reason = extract_verdict(stdout)
        if verdict is not None:
            result["ok"] = True
            result["verdict"] = verdict
        else:
            result["fail_reason"] = reason if proc.returncode == 0 else f"rc{proc.returncode}_{reason}"
    except subprocess.TimeoutExpired:
        result["latency_ms"] = round((time.monotonic() - started) * 1000.0, 1)
        result["fail_reason"] = f"timeout_{int(timeout_s)}s"
    except FileNotFoundError:
        result["fail_reason"] = "executable_not_found"
    except Exception as exc:
        result["latency_ms"] = round((time.monotonic() - started) * 1000.0, 1)
        result["fail_reason"] = f"exec_error_{type(exc).__name__}"
    return result


def call_with_failover(prompt: str, providers: Optional[list[dict]] = None,
                       timeout_s: float = DEFAULT_TIMEOUT_S,
                       log_path: Optional[Path] = None,
                       log_fn: Optional[Callable[[dict], None]] = None,
                       ) -> tuple[Optional[dict], dict]:
    """Try providers in order; first extracted verdict wins.

    Returns ``(verdict_or_None, meta)``. ``meta['attempts']`` carries one entry
    per provider tried (name/ok/latency_ms/bytes/fail_reason — never the
    verdict body, never the prompt). ALL dark -> (None, meta).
    """
    if providers is None:
        providers = default_providers()
    meta: dict[str, Any] = {"attempts": [], "provider": None}
    for provider in providers:
        outcome = call_provider(provider, prompt, timeout_s=timeout_s)
        attempt = {k: outcome[k] for k in ("name", "ok", "latency_ms", "stdout_bytes",
                                           "stdout_sha16", "fail_reason")}
        attempt["at_utc"] = common.iso_utc()
        meta["attempts"].append(attempt)
        if log_fn is not None:
            try:
                log_fn(attempt)
            except Exception:
                pass
        if log_path is not None:
            common.append_jsonl(log_path, {"kind": "adapter_call", **attempt})
        level = logging.INFO if outcome["ok"] else logging.WARNING
        _log.log(level, "adapter: provider=%s ok=%s latency_ms=%s bytes=%s reason=%s",
                 attempt["name"], attempt["ok"], attempt["latency_ms"],
                 attempt["stdout_bytes"], attempt["fail_reason"])
        if outcome["ok"]:
            meta["provider"] = outcome["name"]
            return outcome["verdict"], meta
    _log.warning("adapter: ALL providers dark (%d tried) -> None",
                 len(meta["attempts"]))
    return None, meta


# ---------------------------------------------------------------------------
# smoke
# ---------------------------------------------------------------------------
_SMOKE_PROMPT = (
    "You are a connectivity probe. Reply with ONLY this exact JSON and nothing "
    'else: {"schema":"gtos.f5.judge.verdict.v1","slate_id":"smoke",'
    '"verdicts":[],"manage":[],"notes":"smoke"}'
)


def smoke(providers: Optional[list[dict]] = None,
          timeout_s: float = 60.0) -> list[dict]:
    results = []
    for provider in providers if providers is not None else default_providers():
        outcome = call_provider(provider, _SMOKE_PROMPT, timeout_s=timeout_s)
        results.append(outcome)
        print(json.dumps({
            "provider": outcome["name"],
            "ok": outcome["ok"],
            "latency_ms": outcome["latency_ms"],
            "stdout_bytes": outcome["stdout_bytes"],
            "fail_reason": outcome["fail_reason"],
        }))
    return results


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="F5 desk provider adapter.")
    parser.add_argument("--smoke", action="store_true",
                        help="send a trivial prompt to each provider and print latency")
    parser.add_argument("--timeout-s", type=float, default=60.0)
    args = parser.parse_args(argv)
    common.setup_logging()
    if args.smoke:
        results = smoke(timeout_s=args.timeout_s)
        return 0 if any(r["ok"] for r in results) else 1
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
