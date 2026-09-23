"""Point the live VPS tree at main in place.

Run only after the coordinator says go. This file does nothing unless
``--apply`` is passed. Converting the real live tree also requires
``SOT_CONFIRM_LIVE=1``. Tests set ``SOT_LIVE`` and ``SOT_HOLD`` and
do not set that confirm variable.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REAL_LIVE = Path(r"host-local\redacted_host\repo")
LIVE = Path(os.environ.get("SOT_LIVE", str(REAL_LIVE)))
HOLD = Path(os.environ.get("SOT_HOLD", r"host-local\sot-hold-20260922"))
GIT = "git"
IGNORE_LINES = [
    "pipeline_state/",
    "shadow_logs/",
    ".venv/",
    ".venv-*/",
    "venv/",
    "__pycache__/",
    "*.pyc",
    ".env",
    ".env.*",
    "*.env",
    "secrets/",
    "ceremony-secrets/",
    "*.pem",
    "id_rsa",
    "judgment/**/*.jsonl",
    "judgment/**/*.csv",
    "*.jsonl",
    "*.parquet",
    "*.pkl",
]


def git_env() -> dict:
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        env.pop(key, None)
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def github_url(git_dir: Path) -> str:
    current = ""
    found = ""
    origin = ""
    for line in (git_dir / "config").read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped
            continue
        if not stripped.startswith("url ="):
            continue
        url = stripped.split("=", 1)[1].strip()
        if 'remote "origin"' in current:
            origin = url
        if "github.com" in url:
            if "github" in current:
                return url
            found = url
    if found:
        return found
    if origin:
        return origin
    raise SystemExit("no origin url in the .git/config")


def redact(text: str) -> str:
    text = re.sub(r"://[^/\s@]+@", "://", text)
    kept = []
    for line in text.splitlines():
        low = line.lower()
        if any(mark in low for mark in ("password=", "gho_", "ghs_", "ghp_", "github_pat")):
            kept.append("[redacted]")
        else:
            kept.append(line)
    return "\n".join(kept)


def run(args: list[str], env: dict) -> None:
    proc = subprocess.run([GIT, *args], cwd=LIVE, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        shown = " ".join("<url>" if "://" in arg or arg.startswith("git@") else arg for arg in args)
        raise RuntimeError(f"git {shown} failed\n{redact(proc.stdout + proc.stderr)}")


def init_main(env: dict) -> None:
    probe = subprocess.run([GIT, "init", "-b", "main"], cwd=LIVE, env=env, capture_output=True, text=True)
    if probe.returncode == 0:
        return
    run(["init"], env)
    run(["symbolic-ref", "HEAD", "refs/heads/main"], env)


def rollback(aside: Path, stamp: str) -> None:
    new_git = LIVE / ".git"
    if new_git.exists() and aside.exists():
        failed = HOLD / f"git-failed-{stamp}"
        if not failed.exists():
            shutil.move(str(new_git), str(failed))
    if aside.exists() and not (LIVE / ".git").exists():
        shutil.move(str(aside), str(LIVE / ".git"))


def main() -> int:
    if "--apply" not in sys.argv:
        print("refusing: pass --apply only when the coordinator has said go")
        print("plan: move .git aside, git init, fetch main, reset --mixed, branch main")
        print("never: checkout, clean, stash, reset --hard")
        return 2
    try:
        if LIVE.resolve() == REAL_LIVE.resolve() and os.environ.get("SOT_CONFIRM_LIVE") != "1":
            raise SystemExit("refusing: set SOT_CONFIRM_LIVE=1 to convert the live tree")
    except OSError:
        pass
    git_dir = LIVE / ".git"
    if not git_dir.is_dir():
        raise SystemExit(f"no .git directory at {git_dir}")
    url = github_url(git_dir)
    HOLD.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    aside = HOLD / f"git-aside-f5-live-{stamp}"
    if aside.exists():
        raise SystemExit(f"aside path already exists: {aside}")
    env = git_env()
    shutil.move(str(git_dir), str(aside))
    try:
        init_main(env)
        run(["config", "core.autocrlf", "false"], env)
        run(["config", "core.longpaths", "true"], env)
        run(["remote", "add", "origin", url], env)
        run(["fetch", "origin", "main"], env)
        run(["reset", "--mixed", "origin/main"], env)
        run(["branch", "-M", "main"], env)
        run(["branch", "--set-upstream-to=origin/main"], env)
    except Exception:
        rollback(aside, stamp)
        raise
    ignore = LIVE / ".gitignore"
    existing = ignore.read_text(encoding="utf-8", errors="replace").splitlines() if ignore.is_file() else []
    extra = [line for line in IGNORE_LINES if line not in existing]
    if extra:
        with ignore.open("a", encoding="utf-8", newline="\n") as handle:
            if existing and existing[-1] != "":
                handle.write("\n")
            handle.write("\n".join(extra) + "\n")
    print(f"index matches origin/main; old git dir is {aside}")
    print("working tree was not checked out, cleaned, stashed, or hard-reset")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
