#!/usr/bin/env python3
"""In-repo F5 study entry. Challenge LIVE=0. No broker-send.

Chair retargeted VPS ``f5_study`` LIVE to Challenge ``0``. This file
is the GitHub pin so nightly/study cannot drift back to verification
``0``.

On the VPS, if ``F5_STUDY_IMPL`` or ``<src>/f5_study.py`` exists and is not
this wrapper, the wrapper exports LIVE / F5_STUDY_LOGIN and execs that file
after the login check. This process never imports MetaTrader5 and never
sends. redacted_account is out of scope.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import runpy
import sys
from pathlib import Path

_THIS = Path(__file__).resolve()
_REPO_ROOT = _THIS.parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from scripts.f5_desk.challenge_identity import (
        CHALLENGE_LOGIN,
        LIVE,
        VERIFICATION_LOGIN_QUARANTINED,
        VerificationLoginQuarantined,
        identity_stamp,
        resolve_live,
    )
except ImportError:  # VPS: python scripts/f5_desk/f5_study.py
    from challenge_identity import (  # type: ignore
        CHALLENGE_LOGIN,
        LIVE,
        VERIFICATION_LOGIN_QUARANTINED,
        VerificationLoginQuarantined,
        identity_stamp,
        resolve_live,
    )


def _now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_src() -> Path:
    env = os.environ.get("F5_STUDY_SRC")
    if env:
        return Path(env)
    return Path(r"C:\Users\trader\redacted_host")


def resolve_impl(src: Path) -> Path | None:
    env = os.environ.get("F5_STUDY_IMPL")
    if env:
        path = Path(env)
        return path if path.is_file() else None
    candidate = src / "f5_study.py"
    if candidate.is_file() and candidate.resolve() != _THIS:
        return candidate
    return None


def write_identity_study(out_dir: Path, *, live: int, delegated: bool) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_utc": _now_utc(),
        **identity_stamp(),
        "login": live,
        "LIVE": live,
        "trades": [],
        "rows": [],
        "delegated": delegated,
        "note": (
            "identity-only study body; VPS impl not present on this host. "
            "No tickets invented. No broker-send."
        ),
    }
    path = out_dir / "f5_study.json"
    path.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    return path


def export_live_env(live: int) -> None:
    os.environ["LIVE"] = str(live)
    os.environ["F5_STUDY_LIVE"] = str(live)
    os.environ["F5_STUDY_LOGIN"] = str(live)
    os.environ["F5_CHALLENGE_LOGIN"] = str(CHALLENGE_LOGIN)
    os.environ["F5_VERIFICATION_LOGIN_QUARANTINED"] = str(VERIFICATION_LOGIN_QUARANTINED)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="F5 study — Challenge LIVE 0 only.")
    parser.add_argument("--login", default=None, help="Must be Challenge 0 if set.")
    parser.add_argument("--src", default=None, help="Fable study source dir (host-local).")
    parser.add_argument("--out", default=None, help="Output directory for f5_study.json.")
    parser.add_argument(
        "--delegate",
        action="store_true",
        help="Require a VPS/redacted_host impl after the login pin.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Write an identity-only study JSON and exit 0. Never talks to a broker.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        live = resolve_live(args.login or os.environ.get("F5_STUDY_LOGIN") or os.environ.get("F5_STUDY_LIVE") or os.environ.get("LIVE"))
    except VerificationLoginQuarantined as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    export_live_env(live)
    src = Path(args.src) if args.src else default_src()
    out_dir = Path(args.out) if args.out else src

    if args.smoke:
        path = write_identity_study(out_dir, live=live, delegated=False)
        print(f"LIVE={live} smoke wrote {path}")
        return 0

    impl = resolve_impl(src)
    if impl is not None:
        print(f"LIVE={live} delegating to {impl} (wrapper does not broker-send)")
        sys.path.insert(0, str(impl.parent))
        runpy.run_path(str(impl), run_name="__main__")
        return 0

    if args.delegate:
        print(
            f"REFUSED: --delegate set but no F5_STUDY_IMPL / {src / 'f5_study.py'} found",
            file=sys.stderr,
        )
        return 2

    path = write_identity_study(out_dir, live=live, delegated=False)
    print(f"LIVE={live} identity-only study wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
