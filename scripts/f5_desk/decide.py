#!/usr/bin/env python3
"""Nightly DECISIONS (Fable 5.1, Contract v3). Read-only. Challenge LIVE only.

Turns the night's measurements into KEEP/RELAX/OFF at n≥40 and |mean R| > 2·SE.
Nothing here touches the writer. CHAIR reads DECISIONS.md at 07:00 ICT.

Study body must be Challenge login 0. Verification 0 is
quarantined and fail-closes. No broker-send. redacted_account is out of scope.
"""
from __future__ import annotations

import collections
import datetime
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

_THIS = Path(__file__).resolve()
_REPO_ROOT = _THIS.parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from scripts.f5_desk.challenge_identity import (
        CHALLENGE_LOGIN,
        LIVE,
        ChallengeLoginRequired,
        VerificationLoginQuarantined,
        extract_payload_login,
        filter_challenge_rows,
        identity_stamp,
        refuse_verification_payload,
    )
except ImportError:  # VPS: python scripts/f5_desk/decide.py
    from challenge_identity import (  # type: ignore
        CHALLENGE_LOGIN,
        LIVE,
        ChallengeLoginRequired,
        VerificationLoginQuarantined,
        extract_payload_login,
        filter_challenge_rows,
        identity_stamp,
        refuse_verification_payload,
    )

DEFAULT_SRC = Path(os.environ.get("F5_STUDY_SRC") or r"C:\Users\trader\redacted_host")


def load(name: str, *roots: Path) -> Any:
    for root in roots:
        path = root / name
        if not path.is_file():
            continue
        try:
            with path.open(encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return None
    return None


def stat(rs):
    n = len(rs)
    if n == 0:
        return 0, 0.0, float("nan")
    m = sum(rs) / n
    v = sum((x - m) ** 2 for x in rs) / max(1, n - 1)
    return n, m, math.sqrt(v / n) if n > 1 else float("nan")


def verdict(rs, positive_word="KEEP", negative_word="OFF"):
    n, m, se = stat(rs)
    if n < 40 or not (se == se) or se == 0:
        return f"WATCH (n={n}, mean R {m:+.2f})"
    if m > 2 * se:
        return f"{positive_word} (n={n}, mean R {m:+.2f}, SE {se:.2f})"
    if m < -2 * se:
        return f"{negative_word} (n={n}, mean R {m:+.2f}, SE {se:.2f})"
    return f"WATCH (n={n}, mean R {m:+.2f} within 2 SE {se:.2f})"


def _r(t, k):
    try:
        return float(t.get(k))
    except Exception:
        return None


def _write_refused(out_dir: Path, reason: str) -> dict[str, Any]:
    lines = [
        f"# F5 DECISIONS — {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%MZ')}",
        "",
        "## REFUSED",
        f"- {reason}",
        "- Challenge LIVE is 0. Verification 0 is quarantined.",
        "- No KEEP/OFF computed from a verification body.",
    ]
    out = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "REFUSED",
        "reason": reason,
        "account": identity_stamp(),
        "laws": {},
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "DECISIONS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / "DECISIONS.json").write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return out


def run_decide(*, src: Path, out_dir: Path) -> dict[str, Any]:
    src = Path(src)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    roots = (out_dir, src)

    study = load("f5_study.json", *roots)
    if isinstance(study, dict):
        try:
            refuse_verification_payload(study)
        except (VerificationLoginQuarantined, ChallengeLoginRequired) as exc:
            _write_refused(out_dir, str(exc))
            raise SystemExit(2) from exc

    lines = [
        f"# F5 DECISIONS — {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%MZ')}",
        "",
        f"- LIVE={LIVE} Challenge login {CHALLENGE_LOGIN}. Verification 0 quarantined.",
        "",
    ]
    out: dict[str, Any] = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "OK",
        "account": identity_stamp(),
        "laws": {},
    }

    if study and isinstance(study, dict):
        trades = study.get("trades") or study.get("rows") or []
        trades, n_ver, n_other = filter_challenge_rows(trades)
        if n_ver or n_other:
            lines += [
                f"- dropped verification-login rows: {n_ver}; dropped other-login rows: {n_other}",
            ]
        payload_login = extract_payload_login(study)
        if payload_login is None and n_ver and not trades:
            _write_refused(out_dir, "f5_study.json rows are verification-login only")
            raise SystemExit(2)

        closed = [t for t in trades if isinstance(t, dict) and t.get("closed")]
        era = [t for t in closed if str(t.get("in_utc") or t.get("t_in_iso") or "") >= "2026-09-02"]

        act = [_r(t, "R") for t in era if _r(t, "R") is not None]
        hold = [_r(t, "hold_orig_8h_R") for t in era if _r(t, "hold_orig_8h_R") is not None]
        breaches = [
            t for t in era
            if str(t.get("exit_reason_code")) not in ("4", "5")
            and "time_stop" not in str(t.get("exit_comment") or "")
            and "limit" not in str(t.get("exit_comment") or "")
        ]
        lines += [
            "## Contract since 2 Sep (Contract v1+)",
            f"- closed tickets: {len(era)}; actual R {sum(act):+.1f}; hold-to-orig 8h R {sum(hold):+.1f}",
            f"- exits that were not orig stop / TP / time stop / limit expiry (BREACH candidates): {len(breaches)}",
        ]
        for t in breaches[:10]:
            lines.append(
                f"  - {t.get('ticket')} {t.get('symbol')} {t.get('sleeve')} R {t.get('R')} exit={t.get('exit_comment')}"
            )
        out["laws"]["contract"] = {
            "n": len(era),
            "actual_R": sum(act),
            "hold8_R": sum(hold),
            "breaches": len(breaches),
            "dropped_verification_rows": n_ver,
            "dropped_other_login_rows": n_other,
        }
        lines.append("")

    rc = load("f5_refused_cf.json", *roots)
    if rc and isinstance(rc, dict):
        try:
            refuse_verification_payload(rc)
        except (VerificationLoginQuarantined, ChallengeLoginRequired) as exc:
            _write_refused(out_dir, f"f5_refused_cf.json: {exc}")
            raise SystemExit(2) from exc
        lines.append("## Refusal gates (walked to the sleeve horizon)")
        rows, _, _ = filter_challenge_rows(rc.get("rows") or [])
        for fam, _s in sorted((rc.get("summary") or {}).items()):
            fam_rows = [r for r in rows if not r.get("skip") and r.get("family") == fam and not r.get("dup")]
            rs = [float(r.get("cf_contract_R", 0)) for r in fam_rows]
            v = verdict(rs, positive_word="GATE COSTS MONEY -> REVIEW", negative_word="GATE PROTECTS -> KEEP")
            lines.append(f"- {fam}: {v}")
            out["laws"][f"refusal:{fam}"] = {"n": len(rs), "sum_R": sum(rs)}
        lines.append("")

    for name, title, pos_word, neg_word in (
        ("cf_silent2.json", "Silent drops by gate", "GATE COSTS MONEY -> RELAX", "GATE PROTECTS -> KEEP"),
        ("cf_apt.json", "Same-day re-fires refused", "RELAX", "KEEP"),
        ("keepone_walk.json", "Keep-one (nightly ledger)", "RELAX", "KEEP"),
    ):
        d = load(name, *roots)
        if not d:
            continue
        try:
            refuse_verification_payload(d)
        except (VerificationLoginQuarantined, ChallengeLoginRequired) as exc:
            _write_refused(out_dir, f"{name}: {exc}")
            raise SystemExit(2) from exc
        rows, _, _ = filter_challenge_rows(d.get("rows") or [])
        rows = [r for r in rows if isinstance(r, dict) and not r.get("skip")]
        if not rows:
            continue
        lines.append(f"## {title}")
        by = collections.defaultdict(list)
        for r in rows:
            key = r.get("gate") or r.get("tag") or "all"
            cls = "FX" if r.get("symbol") in ("EURUSD", "GBPUSD", "USDJPY", "GBPJPY", "USDCAD", "NZDUSD") else "METAL/INDEX"
            by[(cls, key)].append(float(r.get("cf_contract_R", 0)))
        for (cls, key), rs in sorted(by.items()):
            v = verdict(rs, positive_word=pos_word, negative_word=neg_word)
            lines.append(f"- {cls} · {key}: {v}")
            out["laws"][f"{name}:{cls}:{key}"] = {"n": len(rs), "sum_R": sum(rs)}
        lines.append("")

    lines += [
        "## Standing reminders",
        "- Writer holds the contract; chair silence on healthy runners is the default.",
        "- Any law marked WATCH needs the historical replay (J2), not more live weeks.",
        "- Study/decide LIVE is Challenge 0. Do not retarget to verification.",
    ]
    (out_dir / "DECISIONS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / "DECISIONS.json").write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return out


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    out_dir = Path(args[0]) if args else Path(os.environ.get("F5_STUDY_OUT") or DEFAULT_SRC)
    src = Path(args[1]) if len(args) > 1 else Path(os.environ.get("F5_STUDY_SRC") or DEFAULT_SRC)
    try:
        run_decide(src=src, out_dir=out_dir)
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
