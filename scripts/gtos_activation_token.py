#!/usr/bin/env python3
"""Mint, inspect and revoke GTOS activation tokens.

An activation token is what makes a broker-mutating request *possible*: without
one, `RealMT5.order_send` refuses anything that would increase exposure
(`src/safety/activation_token.py`). Risk-reducing requests — closes, partial
closes, pending cancels, stop tightenings — never need one, so this tool can
never be the reason an account is stuck in a position.

This script performs **no broker connection and no broker read**. It takes the
account's identity from the profile's own
`broker_profile.expected_account.login_sha256` contract, so no login or
credential is ever handled here.

Usage
-----
    # what is authorized right now
    python3 scripts/gtos_activation_token.py status

    # authorize the FTMO book for 24 hours, bound to the current config bytes
    python3 scripts/gtos_activation_token.py mint \\
        --profile operator_profile --namespace operator_profile \\
        --expires-in-hours 24 --issued-by borhen --note "canary day 1"

    # authorize F5 only for the exact launcher contract (tags abbreviated here)
    python3 scripts/gtos_activation_token.py mint \\
        --profile operator_profile --namespace operator \\
        --f5-minimal-size-usd 10 --f5-notional-initial-usd 100000 \\
        --tags "<the exact run_book.py --tags value>" \\
        --expires-in-hours 24 --issued-by borhen --note "F5 launch contract"

    # withdraw authorization immediately
    python3 scripts/gtos_activation_token.py revoke --profile operator_profile

Revoking stops new exposure at once. It does **not** close anything: use
`scripts/flatten_all_positions.py` for that, which is deliberately independent
of every gate in the system.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.safety.activation_token import (  # noqa: E402
    MAX_TOKEN_LIFETIME_HOURS,
    build_token,
    config_digest_for,
    describe_activation_state,
    launch_contract_digest_for,
    normalized_f5_launch_contract,
    profile_path_for,
    read_token,
    token_dir,
    token_path_for,
    verify_token,
    write_token,
)
from src.mt5.mt5_interface import magic_for_namespace  # noqa: E402


def _load_profile_account_digest(profile: str) -> tuple[str, Path]:
    """Read `broker_profile.expected_account.login_sha256` from a profile."""

    import yaml

    path = profile_path_for(profile, repo_root=REPO_ROOT)
    if not path.is_file():
        raise SystemExit(f"profile not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    expected = ((data.get("broker_profile") or {}).get("expected_account") or {})
    digest = str(expected.get("login_sha256") or "")
    if not digest:
        raise SystemExit(
            f"{path} carries no broker_profile.expected_account.login_sha256. A profile without an "
            "account contract cannot be authorized: there would be nothing to bind the token to, and "
            "the token would authorize whatever account the terminal happens to be logged into."
        )
    return digest, path


def _f5_launch_contract_from_args(args: argparse.Namespace) -> dict | None:
    """Build exactly the contract ``run_book.py`` declares at startup."""

    f5_enabled = args.f5_minimal_size_usd is not None
    if not f5_enabled:
        if (
            args.tags is not None
            or args.risk_unit_floor_mode != "off"
            or args.risk_unit_floor is not None
            or args.event_clock_shadow
        ):
            raise SystemExit(
                "--tags/--risk-unit-floor*/--event-clock-shadow on this token command "
                "require --f5-minimal-size-usd; refusing to ignore launch-contract fields"
            )
    try:
        return normalized_f5_launch_contract(
            f5_enabled=f5_enabled,
            target_risk_usd=args.f5_minimal_size_usd or 0,
            notional_initial_usd=args.f5_notional_initial_usd,
            tags=args.tags,
            namespace=args.namespace,
            magic=magic_for_namespace(args.namespace),
            profile=args.profile,
            q1_mode=args.risk_unit_floor_mode,
            q1_selection=args.risk_unit_floor,
            q2_enabled=args.event_clock_shadow,
        )
    except ValueError as exc:
        raise SystemExit(f"invalid F5 launch contract: {exc}") from None


def _add_f5_launch_contract_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--f5-minimal-size-usd",
        type=float,
        default=None,
        help="bind an F5 token to this fixed cash risk per trade",
    )
    parser.add_argument(
        "--f5-notional-initial-usd",
        type=float,
        default=100000.0,
        help="bind the F5 notional governor base (default 100000)",
    )
    parser.add_argument(
        "--tags",
        default=None,
        help="bind the exact comma-separated F5 sleeve surface (required for F5)",
    )
    parser.add_argument(
        "--risk-unit-floor-mode",
        choices=("off", "shadow", "apply"),
        default="off",
        help="bind Q1's exact runtime authority mode",
    )
    parser.add_argument(
        "--risk-unit-floor",
        default=None,
        help="bind Q1's normalized per-sleeve policy when its mode is shadow/apply",
    )
    parser.add_argument(
        "--event-clock-shadow",
        action="store_true",
        help="bind Q2 as enabled and observation-only",
    )


def cmd_status(args: argparse.Namespace) -> int:
    state = describe_activation_state(directory=args.token_dir)
    print(json.dumps(state, indent=2, sort_keys=True))
    if not state["tokens"]:
        print(
            f"\nNo activation tokens in {state['token_dir']} — every exposure-increasing "
            "broker request will be refused. This is the safe default state.",
            file=sys.stderr,
        )
    return 0


def cmd_mint(args: argparse.Namespace) -> int:
    digest, profile_path = _load_profile_account_digest(args.profile)
    launch_contract = _f5_launch_contract_from_args(args)
    if launch_contract is not None and not args.bind_config:
        raise SystemExit(
            "an F5 token must bind config plus its normalized launch contract; "
            "--no-bind-config is not available for F5"
        )

    config_digest = None
    if args.bind_config:
        config_digest = config_digest_for(
            args.config,
            args.profile,
            repo_root=REPO_ROOT,
            launch_contract=launch_contract,
        )
        if config_digest is None:
            raise SystemExit(
                f"cannot read {args.config} and/or {profile_path} to compute the config digest; "
                "refusing to mint an unbound token silently (pass --no-bind-config to mint one "
                "deliberately, understanding it will survive a config change)"
            )

    # One token per ACCOUNT, and the two FTMO profiles share a login_sha256
    # (`ftmo.yaml:53` and `operator_profile.yaml:55`). So `mint --profile ftmo`
    # writes to the same path as the live profile's token and silently replaces
    # it with one bound to different config bytes — revoking live authorization
    # with a success message. Make the operator say so out loud.
    existing = token_path_for(digest, directory=args.token_dir)
    if existing.exists() and not args.force:
        previous, status, _p = read_token(digest, directory=args.token_dir)
        raise SystemExit(
            f"a token already exists for this account at {existing}\n"
            f"  status:    {status}\n"
            f"  namespace: {(previous or {}).get('namespace')!r}\n"
            f"  expires:   {(previous or {}).get('expires_utc')!r}\n"
            f"  issued_by: {(previous or {}).get('issued_by')!r}\n"
            "Minting would REPLACE it — note that both FTMO profiles carry the same account "
            "digest, so --profile does not scope a token. Pass --force to replace, or "
            "`revoke` first if that is what you meant."
        )

    now = datetime.now(timezone.utc)
    token = build_token(
        account_login_sha256=digest,
        expires_utc=now + timedelta(hours=args.expires_in_hours),
        namespace=args.namespace,
        config_digest_sha256=config_digest,
        issued_by=args.issued_by,
        note=args.note,
        now=now,
    )
    path = write_token(token, directory=args.token_dir)

    print(json.dumps({
        "written": str(path),
        "account_login_sha256": digest,
        "namespace": args.namespace,
        "expires_utc": token["expires_utc"],
        "lifetime_hours": args.expires_in_hours,
        "binds_config_digest": bool(config_digest),
        "config_digest_sha256": config_digest,
        "launch_contract_digest_sha256": (
            launch_contract_digest_for(launch_contract) if launch_contract is not None else None
        ),
        "launch_contract": launch_contract,
        "profile": str(profile_path),
    }, indent=2, sort_keys=True))
    if not config_digest:
        print(
            "\nWARNING: this token does NOT bind the config. Editing the risk dial, the authority "
            "gates or the account contract will not revoke it.",
            file=sys.stderr,
        )
    if not args.namespace:
        # The unbound-config case warned; the unbound-NAMESPACE case did not, and
        # it is the wider hole of the two. `verify_token` enforces a namespace only
        # when the TOKEN declares one, so a namespace-less token authorizes every
        # process on that account -- including the dual-broker follower, and
        # including a `run_book.py` whose activation context failed to declare.
        print(
            "\nWARNING: this token binds NO namespace, so it authorizes ANY process running on "
            "this account, not just the book you minted it for. Pass "
            "--namespace <the run_book.py --namespace value> unless you specifically want that.",
            file=sys.stderr,
        )
    return 0


def cmd_revoke(args: argparse.Namespace) -> int:
    if args.account_sha256:
        digest = args.account_sha256
    elif args.profile:
        digest, _ = _load_profile_account_digest(args.profile)
    else:
        raise SystemExit("revoke needs --profile or --account-sha256")
    path = token_path_for(digest, directory=args.token_dir)
    if not path.exists():
        print(json.dumps({"revoked": False, "reason": "no_token_present", "path": str(path)}, indent=2))
        return 0
    path.unlink()
    print(json.dumps({"revoked": True, "path": str(path), "account_login_sha256": digest}, indent=2))
    print(
        "\nNew exposure is refused from now on. Open positions are UNTOUCHED and keep their broker-side "
        "stops; risk-reducing requests still pass without a token. To close positions use "
        "scripts/flatten_all_positions.py.",
        file=sys.stderr,
    )
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    digest, _ = _load_profile_account_digest(args.profile)
    launch_contract = _f5_launch_contract_from_args(args)
    token, status, path = read_token(digest, directory=args.token_dir)
    if token is None:
        print(json.dumps({"valid": False, "reason": status, "path": str(path)}, indent=2))
        return 1
    config_digest = config_digest_for(
        args.config,
        args.profile,
        repo_root=REPO_ROOT,
        launch_contract=launch_contract,
    )
    ok, reason, detail = verify_token(
        token,
        account_login_sha256=digest,
        namespace=args.namespace or token.get("namespace"),
        config_digest_sha256=config_digest,
        require_namespace_binding=launch_contract is not None,
        require_config_digest_binding=launch_contract is not None,
        directory=args.token_dir,
    )
    print(json.dumps({
        "valid": ok,
        "reason": reason,
        "detail": detail,
        "path": str(path),
        "expires_utc": token.get("expires_utc"),
        "namespace": token.get("namespace"),
        "live_config_digest_sha256": config_digest,
        "launch_contract_digest_sha256": (
            launch_contract_digest_for(launch_contract) if launch_contract is not None else None
        ),
        "launch_contract": launch_contract,
    }, indent=2, sort_keys=True))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--token-dir", default=None,
                        help=f"override the activation directory (default {token_dir()})")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="show what is currently authorized")
    p_status.set_defaults(func=cmd_status)

    p_mint = sub.add_parser("mint", help="authorize one account for a bounded window")
    p_mint.add_argument("--profile", required=True, help="profile name or path")
    p_mint.add_argument("--namespace", default=None,
                        help="bind the token to a run_book namespace (recommended)")
    p_mint.add_argument("--config", default="config/agent_config.yaml")
    p_mint.add_argument("--expires-in-hours", type=float, required=True,
                        help=f"token lifetime; maximum {MAX_TOKEN_LIFETIME_HOURS}h. Required: an "
                             "activation with no stated end is the halt flag again, inverted.")
    p_mint.add_argument("--issued-by", default="", help="who authorized this")
    p_mint.add_argument("--note", default="", help="why, in one line")
    p_mint.add_argument("--bind-config", dest="bind_config", action="store_true", default=True,
                        help="bind to the config bytes (default)")
    p_mint.add_argument("--no-bind-config", dest="bind_config", action="store_false",
                        help="do not bind the config; a config edit will NOT revoke the token")
    p_mint.add_argument("--force", action="store_true",
                        help="replace an existing token for this account (both FTMO profiles share "
                             "one account digest, so --profile alone does not scope a token)")
    _add_f5_launch_contract_arguments(p_mint)
    p_mint.set_defaults(func=cmd_mint)

    p_revoke = sub.add_parser("revoke", help="withdraw authorization now")
    p_revoke.add_argument("--profile", default=None)
    p_revoke.add_argument("--account-sha256", default=None)
    p_revoke.set_defaults(func=cmd_revoke)

    p_verify = sub.add_parser("verify", help="check a token exactly as the runtime would")
    p_verify.add_argument("--profile", required=True)
    p_verify.add_argument("--namespace", default=None)
    p_verify.add_argument("--config", default="config/agent_config.yaml")
    _add_f5_launch_contract_arguments(p_verify)
    p_verify.set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
