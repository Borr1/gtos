"""Fast-forward the converted tree, then stop.

Run only after the in-place conversion, and only with --apply.
The real live tree also requires SOT_CONFIRM_LIVE=1.
``git pull --ff-only origin main`` updates files that are clean.
It does not hard-reset, stash, or clean. A dirty file that main also
changed stops the pull and leaves the working tree as it was.

``--import`` compiles and imports run_book. Import executes the module
body and does not call main(). The cutover motion does not pass
``--import``; the coordinator's reload is what starts the writer.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REAL_LIVE = Path(r"host-local\redacted_host\repo")
LIVE = Path(os.environ.get("SOT_LIVE", str(REAL_LIVE)))


def git_env() -> dict:
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        env.pop(key, None)
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def run(args: list[str], env: dict | None = None) -> None:
    subprocess.check_call(args, cwd=LIVE, env=env)


def main() -> int:
    if "--apply" not in sys.argv:
        print("refusing: pass --apply only when the coordinator has said go")
        print("plan: fetch, pull --ff-only origin main, stop")
        print("optional: --import compiles and imports run_book without calling main()")
        return 2
    try:
        if LIVE.resolve() == REAL_LIVE.resolve() and os.environ.get("SOT_CONFIRM_LIVE") != "1":
            raise SystemExit("refusing: set SOT_CONFIRM_LIVE=1 to deploy the live tree")
    except OSError:
        pass
    env = git_env()
    run(["git", "fetch", "origin", "main"], env)
    run(["git", "pull", "--ff-only", "origin", "main"], env)
    if "--import" in sys.argv:
        py = sys.executable
        run([py, "-m", "compileall", "-q", "run_book.py", "src", "scripts"], env)
        run([py, "-c", "import run_book; print('import_ok', run_book.__file__)"], env)
    print("stop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
