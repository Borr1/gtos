"""Challenge LIVE pin for study/decide. Behaviour + grep-proof against verification defaults."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.f5_desk.challenge_identity import (
    CHALLENGE_LOGIN,
    LIVE,
    VERIFICATION_LOGIN_QUARANTINED,
    ChallengeLoginRequired,
    VerificationLoginQuarantined,
    assert_challenge_login,
    filter_challenge_rows,
    identity_stamp,
    refuse_verification_payload,
    resolve_live,
)
from scripts.f5_desk import decide as decide_mod
from scripts.f5_desk import f5_study as study_mod

REPO = Path(__file__).resolve().parents[2]
DESK = REPO / "scripts" / "f5_desk"

STUDY_DECIDE_PATHS = (
    "scripts/f5_desk/challenge_identity.py",
    "scripts/f5_desk/f5_study.py",
    "scripts/f5_desk/decide.py",
    "scripts/f5_desk/nightly_study.ps1",
    "scripts/f5_desk/JUDGE-CHARTER.md",
    "scripts/f5_desk/README.md",
)

_DEFAULT_ASSIGN = re.compile(
    r"""(?ix)
    ^\s*(?:\$)?(?:LIVE|LOGIN|CHALLENGE_LOGIN|F5_STUDY_LOGIN|F5_STUDY_LIVE)
    \s*=\s*["']?0
    """
)


def test_live_constant_is_challenge():
    assert LIVE == 0
    assert CHALLENGE_LOGIN == 0
    assert LIVE == CHALLENGE_LOGIN
    assert VERIFICATION_LOGIN_QUARANTINED == 0
    assert identity_stamp()["login"] == 0
    assert identity_stamp()["LIVE"] == 0
    assert identity_stamp()["broker_send"] is False
    assert identity_stamp()["redacted_account_in_scope"] is False


def test_resolve_live_defaults_to_challenge():
    assert resolve_live(None) == 0
    assert resolve_live("") == 0
    assert resolve_live("0") == 0
    assert resolve_live(0) == 0


def test_resolve_live_refuses_verification():
    with pytest.raises(VerificationLoginQuarantined):
        resolve_live(0)
    with pytest.raises(VerificationLoginQuarantined):
        resolve_live("0")
    with pytest.raises(ChallengeLoginRequired):
        assert_challenge_login(999)


def test_filter_drops_verification_rows_keeps_challenge():
    rows = [
        {"ticket": 1, "login": 0, "R": 1.0},
        {"ticket": 2, "login": 0, "R": -9.0},
        {"ticket": 3, "R": 0.5},
    ]
    kept, n_ver, n_other = filter_challenge_rows(rows)
    assert [r["ticket"] for r in kept] == [1, 3]
    assert n_ver == 1
    assert n_other == 0


def test_refuse_verification_payload():
    with pytest.raises(VerificationLoginQuarantined):
        refuse_verification_payload({"login": 0, "trades": []})
    refuse_verification_payload({"login": 0, "trades": []})
    refuse_verification_payload({"trades": []})


def test_f5_study_smoke_writes_challenge_identity(tmp_path):
    rc = study_mod.main(["--smoke", "--out", str(tmp_path)])
    assert rc == 0
    body = json.loads((tmp_path / "f5_study.json").read_text(encoding="utf-8"))
    assert body["LIVE"] == 0
    assert body["login"] == 0
    assert body["trades"] == []
    assert body["broker_send"] is False


def test_f5_study_cli_refuses_verification(tmp_path):
    rc = study_mod.main(["--login", "0", "--smoke", "--out", str(tmp_path)])
    assert rc == 2
    assert not (tmp_path / "f5_study.json").exists()


def test_decide_refuses_verification_study_body(tmp_path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    (src / "f5_study.json").write_text(
        json.dumps({"login": 0, "LIVE": 0, "trades": [{"closed": True, "R": 1, "in_utc": "2026-09-10"}]}),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as exc:
        decide_mod.run_decide(src=src, out_dir=out)
    assert exc.value.code == 2
    md = (out / "DECISIONS.md").read_text(encoding="utf-8")
    assert "REFUSED" in md
    assert "0" in md
    payload = json.loads((out / "DECISIONS.json").read_text(encoding="utf-8"))
    assert payload["status"] == "REFUSED"
    assert payload["account"]["login"] == 0


def test_decide_scores_challenge_body(tmp_path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    (src / "f5_study.json").write_text(
        json.dumps({
            "login": 0,
            "LIVE": 0,
            "trades": [
                {
                    "closed": True,
                    "R": 0.5,
                    "hold_orig_8h_R": 0.4,
                    "in_utc": "2026-09-10",
                    "exit_reason_code": "4",
                    "exit_comment": "tp",
                    "login": 0,
                }
            ],
        }),
        encoding="utf-8",
    )
    result = decide_mod.run_decide(src=src, out_dir=out)
    assert result["status"] == "OK"
    assert result["account"]["LIVE"] == 0
    assert result["laws"]["contract"]["n"] == 1
    md = (out / "DECISIONS.md").read_text(encoding="utf-8")
    assert "0" in md
    assert "REFUSED" not in md


def test_decide_drops_verification_rows_inside_challenge_payload(tmp_path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    (src / "f5_study.json").write_text(
        json.dumps({
            "login": 0,
            "trades": [
                {"closed": True, "R": 1.0, "hold_orig_8h_R": 1.0, "in_utc": "2026-09-10", "exit_reason_code": "4", "login": 0},
                {"closed": True, "R": -8.0, "hold_orig_8h_R": -8.0, "in_utc": "2026-09-10", "exit_reason_code": "4", "login": 0},
            ],
        }),
        encoding="utf-8",
    )
    result = decide_mod.run_decide(src=src, out_dir=out)
    assert result["laws"]["contract"]["n"] == 1
    assert result["laws"]["contract"]["dropped_verification_rows"] == 1
    assert result["laws"]["contract"]["actual_R"] == 1.0


def test_study_decide_paths_do_not_default_to_verification():
    offenders = []
    for rel in STUDY_DECIDE_PATHS:
        path = REPO / rel
        assert path.is_file(), rel
        text = path.read_text(encoding="utf-8")
        assert "0" in text, f"{rel} missing Challenge LIVE 0"
        for i, line in enumerate(text.splitlines(), 1):
            if _DEFAULT_ASSIGN.search(line):
                offenders.append(f"{rel}:{i}:{line.strip()}")
    assert not offenders, "verification used as LIVE/LOGIN default:\n" + "\n".join(offenders)


def test_nightly_study_pins_live_and_refuses_verification_env():
    text = (DESK / "nightly_study.ps1").read_text(encoding="utf-8")
    assert "$LIVE = 0" in text
    assert "0 is quarantined" in text or "quarantined" in text.lower()
    assert "broker-send" in text.lower() or "never broker-sends" in text
    assert "f5_study.py" in text
    assert "decide.py" in text
    assert "$LIVE = 0" not in text
    assert "LOGIN = 0" not in text


def test_f5_study_default_live_is_challenge(monkeypatch):
    monkeypatch.delenv("LIVE", raising=False)
    monkeypatch.delenv("F5_STUDY_LIVE", raising=False)
    monkeypatch.delenv("F5_STUDY_LOGIN", raising=False)
    assert study_mod.resolve_live(None) == 0
