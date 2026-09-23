import json
from pathlib import Path

from src.judgment.jev_client import (
    redacted_account_KEY_FINGERPRINT,
    api_key,
    calls_enabled,
    calls_used,
    evaluate,
    key_fingerprint,
    key_source,
    reset_call_budget,
)


def test_key_sources_env_and_file(monkeypatch, tmp_path):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_KEY_FILE", raising=False)
    monkeypatch.delenv("GTOS_JEV_A1_CALL", raising=False)
    monkeypatch.setattr("src.judgment.jev_client._HOME_KEY", tmp_path / "no_home_key")
    monkeypatch.setattr("src.judgment.jev_client._SECRET_FILES", ())
    monkeypatch.setattr("src.judgment.jev_client.REPO_ROOT", tmp_path)
    assert api_key() is None
    assert key_fingerprint() is None

    monkeypatch.setenv("TYPESAFE_KEY", "beta-key")
    assert api_key() == "beta-key"
    assert key_source() == "env:TYPESAFE_KEY"
    assert key_fingerprint() == key_fingerprint("beta-key")
    assert key_fingerprint() != redacted_account_KEY_FINGERPRINT

    monkeypatch.setenv("TYPESAFE_API_KEY", "alpha-key")
    assert api_key() == "alpha-key"
    assert key_source() == "env:TYPESAFE_API_KEY"

    monkeypatch.delenv("TYPESAFE_API_KEY")
    monkeypatch.delenv("TYPESAFE_KEY")
    key_file = tmp_path / "api_key"
    key_file.write_text("# comment\nfile-key\n", encoding="utf-8")
    monkeypatch.setenv("TYPESAFE_KEY_FILE", str(key_file))
    monkeypatch.setenv("GTOS_JEV_A1_CALL", "0")
    assert api_key() == "file-key"
    assert key_source() == "file:TYPESAFE_KEY_FILE"
    skipped = evaluate({"x": 1})
    assert skipped["skipped"] == "GTOS_JEV_A1_CALL_off"
    assert "file-key" not in json.dumps(skipped)


def test_default_on_when_key_present_explicit_off(monkeypatch, tmp_path):
    monkeypatch.setenv("TYPESAFE_API_KEY", "k")
    monkeypatch.delenv("TYPESAFE_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_KEY_FILE", raising=False)
    monkeypatch.delenv("GTOS_JEV_A1_CALL", raising=False)
    monkeypatch.setattr("src.judgment.jev_client._HOME_KEY", tmp_path / "no_home_key")
    monkeypatch.setattr("src.judgment.jev_client._SECRET_FILES", ())
    monkeypatch.setattr("src.judgment.jev_client.REPO_ROOT", tmp_path)
    assert calls_enabled() is True
    monkeypatch.setenv("GTOS_JEV_A1_CALL", "0")
    assert calls_enabled() is False
    monkeypatch.delenv("TYPESAFE_API_KEY")
    monkeypatch.delenv("GTOS_JEV_A1_CALL", raising=False)
    assert calls_enabled() is False


def test_budget_and_mocked_post(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "super-secret-key-xyz")
    monkeypatch.delenv("GTOS_JEV_A1_CALL", raising=False)
    monkeypatch.setenv("GTOS_JEV_MAX_CALLS", "2")
    reset_call_budget()

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"model":"jev-1.13.0","answers":{"admit":{"choice":"abstain"}}}'

    monkeypatch.setattr("src.judgment.jev_client.urllib.request.urlopen", lambda *a, **k: _Resp())
    first = evaluate({"identity": {"symbol": "XAUUSD"}})
    assert first["ok"] is True
    assert first["answers"]["admit"]["choice"] == "abstain"
    assert calls_used() == 1
    dumped = json.dumps(first)
    assert "super-secret-key-xyz" not in dumped
    assert "Bearer" not in dumped
    second = evaluate({"identity": {"symbol": "XAUUSD"}})
    assert second["ok"] is True
    third = evaluate({"identity": {"symbol": "XAUUSD"}})
    assert third["ok"] is False
    assert third["skipped"] == "call_budget_exhausted"
    assert calls_used() == 2


def test_absent_key_is_skip_not_http(monkeypatch, tmp_path):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_KEY_FILE", raising=False)
    monkeypatch.setattr("src.judgment.jev_client._HOME_KEY", tmp_path / "no_home_key")
    monkeypatch.setattr("src.judgment.jev_client._SECRET_FILES", ())
    monkeypatch.setattr("src.judgment.jev_client.REPO_ROOT", tmp_path)
    reset_call_budget()
    row = evaluate({"identity": {"symbol": "XAUUSD"}})
    assert row["ok"] is False
    assert row["skipped"] == "TYPESAFE_key_absent"
    assert "error" not in row or row.get("error") is None
    assert calls_used() == 0


def test_vps_host_secret_file_and_env_typesafe(monkeypatch, tmp_path):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_KEY_FILE", raising=False)
    monkeypatch.setattr("src.judgment.jev_client.REPO_ROOT", tmp_path)
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    (secrets / "TYPESAFE_API_KEY.txt").write_text("vps-file-key\n", encoding="utf-8")
    assert api_key() == "vps-file-key"
    assert key_source() == "file:secrets/TYPESAFE_API_KEY.txt"
    (secrets / "TYPESAFE_API_KEY.txt").unlink()
    (tmp_path / ".env.typesafe").write_text("TYPESAFE_API_KEY=env-file-key\n", encoding="utf-8")
    assert api_key() == "env-file-key"
    assert key_source() == "file:.env.typesafe"
    monkeypatch.setenv("GTOS_JEV_A1_CALL", "0")
    skipped = evaluate({"x": 1})
    assert skipped["skipped"] == "GTOS_JEV_A1_CALL_off"
    assert "env-file-key" not in json.dumps(skipped)
    assert "vps-file-key" not in json.dumps(skipped)


def test_home_config_key(monkeypatch, tmp_path):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_KEY_FILE", raising=False)
    cfg = tmp_path / "api_key"
    cfg.write_text("home-secret\n", encoding="utf-8")
    monkeypatch.setattr("src.judgment.jev_client._HOME_KEY", cfg)
    assert api_key() == "home-secret"
    assert key_source() == "file:~/.config/typesafe/api_key"
    assert Path.home()  # path object still used only as label
