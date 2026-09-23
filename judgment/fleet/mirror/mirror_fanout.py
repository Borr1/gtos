#!/usr/bin/env python3
"""Host keep entry: bind friend_copy, then run judgment.fleet.mirror_fanout.

Drop this file over ``judgment/fleet/mirror/mirror_fanout.py`` on redacted_host.
Keep already launches that path. Loads friend_copy by file path so the
heavy ``src.judgment`` package (and book_owner) never enter the observer.
Agents do not order_send. Challenge / redacted_account stay off this process.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BIND_PATH = ROOT / "src" / "judgment" / "friend_copy_bind.py"
if not BIND_PATH.is_file():
    BIND_PATH = Path(__file__).resolve().parent / "friend_copy_bind.py"


def _load_bind():
    spec = importlib.util.spec_from_file_location("gtos_friend_copy_bind", BIND_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit(f"friend_copy_bind missing: {BIND_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_bind = _load_bind()
from judgment.fleet.mirror_adapter import DemoMirrorAdapter  # noqa: E402

_bind.install(DemoMirrorAdapter)

from judgment.fleet.mirror_fanout import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
