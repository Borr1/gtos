"""`run_book.py` -- the live book entrypoint -- must stay importable on mainline.

Why this test exists
--------------------
`run_book.py` lived only on the VPS branch until 2026-07-26. Vendoring it failed on a
single unresolved name, `bridge.config_bool_value`, so every claim about live halt
coverage, account identity or namespace isolation was unverifiable from this repo.
That helper has landed and the entrypoint is now here; this test is what stops it
silently rotting again, because nothing else on mainline imports it.

Why a subprocess
----------------
`run_book.py` is on the never-execute list -- it drives a real broker. Importing it in
the pytest process is still not safe enough: at module scope it calls
`load_dotenv(override=True)`, which would push whatever `.env` holds into the test
process's environment, and `install_runtime_monitoring()`. So the import runs in a
child process rooted at an empty cwd with `PYTHONPATH` pointed at the repo. That
reaches every `src.*` import while leaving no `.env` for `load_dotenv` to find.

`main()` is never reached: it is guarded by `if __name__ == "__main__"`, and an
imported module's `__name__` is `run_book`. The assertions below pin that.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_BOOK = REPO_ROOT / "run_book.py"


def test_run_book_is_vendored_on_mainline():
    assert RUN_BOOK.is_file(), (
        "run_book.py is missing from mainline again. It is the live entrypoint; "
        "without it, live halt coverage and account identity are unverifiable here."
    )


def test_run_book_imports_cleanly_in_isolation():
    """Import it for real, in a child process, with no .env reachable."""
    with tempfile.TemporaryDirectory() as empty_cwd:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(REPO_ROOT)
        env.pop("GTOS_MODE", None)
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                "import importlib; m = importlib.import_module('run_book');"
                " print('NAME=' + m.__name__);"
                " print('HAS_MAIN=' + str(callable(getattr(m, 'main', None))))",
            ],
            cwd=empty_cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

    assert proc.returncode == 0, (
        "run_book.py no longer imports at HEAD.\n"
        f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
    )
    # Imported as a module, so the __main__ guard did not fire and main() never ran.
    assert "NAME=run_book" in proc.stdout
    assert "HAS_MAIN=True" in proc.stdout


def test_run_book_does_not_place_orders_at_import_time():
    """Module scope must stay side-effect-light: no broker calls outside main()."""
    source = RUN_BOOK.read_text(encoding="utf-8-sig")
    tree = compile(source, str(RUN_BOOK), "exec", flags=1024, dont_inherit=True)  # ast.PyCF_ONLY_AST
    import ast

    module_level_calls = [
        node
        for node in tree.body
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
    ]
    called = set()
    for node in module_level_calls:
        func = node.value.func
        called.add(func.id if isinstance(func, ast.Name) else getattr(func, "attr", ""))

    forbidden = {"main", "connect", "order_send", "run", "run_cycle", "start"}
    assert not (called & forbidden), (
        f"run_book.py gained a module-level call to {sorted(called & forbidden)}. "
        "Importing the live entrypoint must never reach the broker."
    )


@pytest.mark.parametrize(
    "symbol",
    ["UltimateBookOwner", "BookLauncher", "config_bool_value", "RealMT5",
     "assert_mt5_account_matches_profile"],
)
def test_run_book_still_binds_its_live_dependencies(symbol):
    """The names whose absence broke vendoring. config_bool_value is the one that did."""
    assert symbol in RUN_BOOK.read_text(encoding="utf-8-sig")
