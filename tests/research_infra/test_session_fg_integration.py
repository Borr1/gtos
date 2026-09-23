from __future__ import annotations

import importlib.util
import pathlib


REPO = pathlib.Path(__file__).resolve().parents[2]
VERIFIER = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase19/receipts"
    / "verify_session_fg_integration.py"
)


def _module():
    spec = importlib.util.spec_from_file_location("verify_session_fg_integration", VERIFIER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_session_fg_integrated_evidence_and_default_off_boundaries():
    result = _module().verify()
    assert result["status"] == "PASS", result["failures"]
    assert result["checks_failed"] == 0
    assert result["metrics"]["source_commits_mapped"] == 66
    assert result["claims"]["activation_authority"] is False
    assert result["claims"]["family_kill_authority"] is False
