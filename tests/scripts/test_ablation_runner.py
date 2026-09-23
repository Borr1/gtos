"""Tests for L57 ablation framework + runner.

Coverage
========
- Manifest schema validation (missing keys, unknown transformation,
  duplicate names, bad params).
- Each transformation type: hand-verified expected output.
- Idempotence: applying the same transformation twice ≡ once.
- replace_text: literal; regex_remove: regex.
- AblationRun end-to-end with a mocked harness subprocess.
- Realized-R join missing → verdict_suppressed in summary + report.
- Pre-registration sentinel: pin SHA of ablation_default_v1.yaml.
- --dry-run: exits 0, no harness subprocess spawned.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from unittest import mock

import pytest
import yaml

# Resolve project root so we can import without install
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.research_infra.ablation_framework import (  # noqa: E402
    AblationApplicator,
    AblationEntry,
    AblationManifest,
    AblationRun,
    ManifestSchemaError,
    TransformationError,
    UnsafeRegexError,
)
from scripts.research import ablation_runner  # noqa: E402


MANIFEST_DEFAULT_V1 = (
    _PROJECT_ROOT / "scripts" / "research" / "manifests"
    / "ablation_default_v1.yaml"
)
DEFAULT_METRICS = (
    _PROJECT_ROOT / "scripts" / "research" / "metrics"
    / "prompt_ab_default.yaml"
)


# HARDCODED pin — SHA256 of scripts/research/manifests/ablation_default_v1.yaml
# at the moment of authoring this test. The hash is computed over the
# LF-normalized bytes (CRLF -> LF, no trailing CRLF) so the sentinel
# survives Git's autocrlf checkouts on Windows. If you EDIT the manifest,
# this constant does NOT update, so the sentinel test fails by design —
# copy to ablation_default_v2.yaml and update manifest_set_id rather than
# mutating v1 in place. See L57_ablation_framework.md.
#
# To intentionally update after a CEO-approved manifest edit:
#   python -c "import hashlib,pathlib; \
#     b=pathlib.Path('scripts/research/manifests/ablation_default_v1.yaml').read_bytes(); \
#     print(hashlib.sha256(b.replace(b'\\r\\n',b'\\n')).hexdigest())"
# and paste the new digest here.
ABLATION_DEFAULT_V1_SHA256 = (
    "f583d0d187386e7af3623dcda6b7e60dd546a2df78cc5a142920da3630d4985e"
)


def _manifest_normalized_sha(path: Path) -> str:
    """Read manifest bytes and SHA256 over LF-normalized content. Makes
    the sentinel survive Git autocrlf checkouts on Windows."""
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_manifest_yaml(tmp_path: Path, entries: list[dict],
                        manifest_set_id: str = "test_manifest") -> Path:
    p = tmp_path / "manifest.yaml"
    body = {
        "manifest_set_id": manifest_set_id,
        "description": "test manifest",
        "ablations": entries,
    }
    p.write_text(yaml.safe_dump(body), encoding="utf-8")
    return p


def _make_prompt(tmp_path: Path, body: str, name: str = "p.md") -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


SAMPLE_PROMPT = """\
# System Prompt

Some preamble text.

## OB Zone Mechanism

The order block zone is the last opposing candle before the structural
break. Wait for confirmation before emitting CANDIDATE.

## Cross-Instrument Context

XAU D1 direction is bullish today.

## Kill Zone Schedule

London: 07:00-10:30. NY: 13:00-17:00.

## Confidence Scoring

Emit a confidence score 0-100.

## Framework Prioritization

Prioritize ob_retest, then fvg_fill, then breaker_re_entry.

## Liquidity Sweep Heuristic

A sweep above the recent high is the trigger.

## Footer

Done.
"""


# ===========================================================================
# Manifest schema validation
# ===========================================================================


def test_manifest_loads_default_v1():
    """The default manifest loads cleanly."""
    m = AblationManifest.load(MANIFEST_DEFAULT_V1)
    assert m.manifest_set_id == "ablation_default_v1"
    assert len(m) == 10
    assert all(isinstance(e, AblationEntry) for e in m)


def test_manifest_missing_top_level_set_id_rejected(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump({
        "description": "no set_id here",
        "ablations": [{
            "name": "x", "description": "y", "transformation": "drop_section",
            "params": {"heading": "h"},
        }],
    }), encoding="utf-8")
    with pytest.raises(ManifestSchemaError,
                       match="manifest_set_id"):
        AblationManifest.load(p)


def test_manifest_missing_ablations_list_rejected(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump({
        "manifest_set_id": "x",
        "description": "no entries",
    }), encoding="utf-8")
    with pytest.raises(ManifestSchemaError, match="ablations"):
        AblationManifest.load(p)


def test_manifest_missing_required_entry_key_rejected(tmp_path):
    p = _make_manifest_yaml(tmp_path, [
        {"name": "x", "description": "y", "transformation": "drop_section"},
    ])
    with pytest.raises(ManifestSchemaError, match="missing required key"):
        AblationManifest.load(p)


def test_manifest_unknown_transformation_rejected(tmp_path):
    p = _make_manifest_yaml(tmp_path, [
        {"name": "x", "description": "y", "transformation": "explode",
         "params": {}},
    ])
    with pytest.raises(ManifestSchemaError, match="unknown transformation"):
        AblationManifest.load(p)


def test_manifest_missing_required_params_rejected(tmp_path):
    p = _make_manifest_yaml(tmp_path, [
        # drop_section needs `heading`
        {"name": "x", "description": "y", "transformation": "drop_section",
         "params": {}},
    ])
    with pytest.raises(ManifestSchemaError, match="requires params.heading"):
        AblationManifest.load(p)


def test_manifest_duplicate_names_rejected(tmp_path):
    p = _make_manifest_yaml(tmp_path, [
        {"name": "dupe", "description": "a", "transformation": "drop_section",
         "params": {"heading": "H1"}},
        {"name": "dupe", "description": "b", "transformation": "drop_section",
         "params": {"heading": "H2"}},
    ])
    with pytest.raises(ManifestSchemaError, match="duplicate name"):
        AblationManifest.load(p)


def test_manifest_unknown_suffix_rejected(tmp_path):
    p = tmp_path / "manifest.toml"
    p.write_text("manifest_set_id = 'x'", encoding="utf-8")
    with pytest.raises(ManifestSchemaError, match=".yaml/.yml/.json"):
        AblationManifest.load(p)


def test_manifest_top_level_must_be_mapping(tmp_path):
    p = tmp_path / "list.yaml"
    p.write_text(yaml.safe_dump([1, 2, 3]), encoding="utf-8")
    with pytest.raises(ManifestSchemaError, match="top-level must be a mapping"):
        AblationManifest.load(p)


def test_manifest_run_hash_combines_filename_and_content(tmp_path):
    """Same content but different filenames → different run_hash."""
    body = yaml.safe_dump({
        "manifest_set_id": "same",
        "ablations": [{
            "name": "n", "description": "d", "transformation": "drop_section",
            "params": {"heading": "h"},
        }],
    })
    p1 = tmp_path / "a.yaml"
    p1.write_text(body, encoding="utf-8")
    p2 = tmp_path / "b.yaml"
    p2.write_text(body, encoding="utf-8")
    m1 = AblationManifest.load(p1)
    m2 = AblationManifest.load(p2)
    assert m1.sha256 == m2.sha256
    assert m1.run_hash != m2.run_hash


# ===========================================================================
# AblationApplicator transformations — hand-verified
# ===========================================================================


def test_drop_section_removes_target_section_only():
    out = AblationApplicator.apply(SAMPLE_PROMPT, AblationEntry(
        name="t", description="t", transformation="drop_section",
        params={"heading": "Cross-Instrument Context"},
    ))
    assert "## Cross-Instrument Context" not in out
    assert "XAU D1 direction" not in out
    # Adjacent sections preserved
    assert "## OB Zone Mechanism" in out
    assert "## Kill Zone Schedule" in out
    assert "## Footer" in out


def test_drop_section_removes_terminal_section():
    """A section at the end of the file should be removed cleanly."""
    out = AblationApplicator.apply(SAMPLE_PROMPT, AblationEntry(
        name="t", description="t", transformation="drop_section",
        params={"heading": "Footer"},
    ))
    assert "## Footer" not in out
    assert "Done." not in out
    assert "## Liquidity Sweep Heuristic" in out


def test_drop_section_missing_heading_returns_input_unchanged():
    out = AblationApplicator.apply(SAMPLE_PROMPT, AblationEntry(
        name="t", description="t", transformation="drop_section",
        params={"heading": "DOES_NOT_EXIST"},
    ))
    assert out == SAMPLE_PROMPT


def test_drop_section_idempotent():
    """Applying drop_section twice ≡ once."""
    entry = AblationEntry(
        name="t", description="t", transformation="drop_section",
        params={"heading": "Confidence Scoring"},
    )
    once = AblationApplicator.apply(SAMPLE_PROMPT, entry)
    twice = AblationApplicator.apply(once, entry)
    assert once == twice


def test_replace_text_literal_replacement():
    out = AblationApplicator.apply(SAMPLE_PROMPT, AblationEntry(
        name="t", description="t", transformation="replace_text",
        params={"find": "Wait for confirmation before emitting CANDIDATE.",
                "replace": "Emit CANDIDATE if conditions are met."},
    ))
    assert "Wait for confirmation" not in out
    assert "Emit CANDIDATE if conditions are met." in out


def test_replace_text_empty_find_rejected():
    with pytest.raises(TransformationError, match="non-empty"):
        AblationApplicator.apply("hello", AblationEntry(
            name="t", description="t", transformation="replace_text",
            params={"find": "", "replace": "world"},
        ))


def test_replace_text_idempotent():
    """If find is no longer present after first apply, second apply is a
    no-op."""
    entry = AblationEntry(
        name="t", description="t", transformation="replace_text",
        params={"find": "London", "replace": "Asia"},
    )
    once = AblationApplicator.apply(SAMPLE_PROMPT, entry)
    twice = AblationApplicator.apply(once, entry)
    assert once == twice
    assert "London" not in once
    assert "Asia" in once


def test_regex_remove_basic():
    out = AblationApplicator.apply(SAMPLE_PROMPT, AblationEntry(
        name="t", description="t", transformation="regex_remove",
        params={"pattern": r"D1\s+direction\s+is\s+\w+\s+today\."},
    ))
    assert "D1 direction" not in out
    assert "## Cross-Instrument Context" in out  # only the sentence dropped


def test_regex_remove_invalid_pattern_raises():
    with pytest.raises(TransformationError, match="invalid pattern"):
        AblationApplicator.apply(SAMPLE_PROMPT, AblationEntry(
            name="t", description="t", transformation="regex_remove",
            params={"pattern": "[unclosed"},
        ))


@pytest.mark.parametrize("forbidden", [
    "(?=lookahead)abc",      # positive lookahead
    "abc(?<!neg)def",        # negative lookbehind
    "(a)+*",                  # quantifier-on-quantifier
])
def test_regex_remove_sandbox_rejects_forbidden_patterns(forbidden):
    with pytest.raises(UnsafeRegexError):
        AblationApplicator.apply("test", AblationEntry(
            name="t", description="t", transformation="regex_remove",
            params={"pattern": forbidden},
        ))


def test_regex_remove_idempotent():
    entry = AblationEntry(
        name="t", description="t", transformation="regex_remove",
        params={"pattern": r"NY:\s*[\d:]+\-[\d:]+\."},
    )
    once = AblationApplicator.apply(SAMPLE_PROMPT, entry)
    twice = AblationApplicator.apply(once, entry)
    assert once == twice


def test_drop_framework_strips_matching_lines():
    out = AblationApplicator.apply(SAMPLE_PROMPT, AblationEntry(
        name="t", description="t", transformation="drop_framework",
        params={"framework": "ob_retest", "target_file": "config/agent_config.yaml"},
    ))
    assert "ob_retest" not in out
    # Other content preserved
    assert "## Kill Zone Schedule" in out


def test_drop_framework_idempotent():
    entry = AblationEntry(
        name="t", description="t", transformation="drop_framework",
        params={"framework": "fvg_fill", "target_file": "config/agent_config.yaml"},
    )
    once = AblationApplicator.apply(SAMPLE_PROMPT, entry)
    twice = AblationApplicator.apply(once, entry)
    assert once == twice


def test_drop_gate_removes_sentences_containing_gate_name():
    text = ("Foo bar baz. The touch_count gate rejects high-touch zones. "
            "Other sentence remains.\nNew line continues.\n")
    out = AblationApplicator.apply(text, AblationEntry(
        name="t", description="t", transformation="drop_gate",
        params={"gate": "touch_count"},
    ))
    assert "touch_count" not in out
    assert "Foo bar baz." in out
    assert "Other sentence remains." in out
    assert "New line continues." in out


def test_drop_gate_removes_line_when_only_sentence():
    text = "Line one.\ntouch_count is the only thing here.\nLine three.\n"
    out = AblationApplicator.apply(text, AblationEntry(
        name="t", description="t", transformation="drop_gate",
        params={"gate": "touch_count"},
    ))
    assert "touch_count" not in out
    assert "Line one." in out
    assert "Line three." in out


def test_drop_gate_idempotent():
    text = "The touch_count gate enforces N <= 1. Other sentence stays."
    entry = AblationEntry(
        name="t", description="t", transformation="drop_gate",
        params={"gate": "touch_count"},
    )
    once = AblationApplicator.apply(text, entry)
    twice = AblationApplicator.apply(once, entry)
    assert once == twice


def test_unknown_transformation_at_apply_raises():
    with pytest.raises(TransformationError, match="Unknown transformation"):
        AblationApplicator.apply("text", {
            "transformation": "nonsense", "params": {}
        })


# ===========================================================================
# AblationRun end-to-end with mocked harness subprocess
# ===========================================================================


def _stub_harness_runner(harness_dir: Path, *,
                         metrics_report: dict | None = None) -> None:
    """Write a fake harness output dir as if the L56 harness had run."""
    harness_dir.mkdir(parents=True, exist_ok=True)
    if metrics_report is None:
        metrics_report = {
            "n_fixtures": 5,
            "n_with_realized_r": 0,
            "bonferroni_denominator": 4,
            "metrics": [
                {
                    "name": "decision_label_diff",
                    "test": "sign",
                    "value": {"a_cand_b_no": 1, "a_no_b_cand": 0},
                    "n": 1, "p_value": 1.0,
                    "underpowered": True,
                    "significant_raw": False,
                    "significant_corrected": False,
                    "alpha_raw": 0.05,
                    "alpha_bonferroni": 0.0125,
                    "bonferroni_corrected": True,
                    "requires_realized_r": False,
                },
                {
                    "name": "cr_rate_compare",
                    "test": "mcnemar",
                    "value": {
                        "a_cand_b_cand": 2,
                        "a_cand_b_no": 1,
                        "a_no_b_cand": 0,
                        "a_no_b_no": 2,
                    },
                    "n": 5, "p_value": 0.5,
                    "underpowered": True,
                    "significant_raw": False,
                    "significant_corrected": False,
                    "bonferroni_corrected": True,
                    "requires_realized_r": False,
                },
                {
                    "name": "realized_r_paired_t",
                    "test": "paired_t",
                    "skipped": True,
                    "skip_reason": "realized_r_join_not_provided",
                    "n": 0, "p_value": None,
                    "underpowered": False,
                    "significant_raw": False,
                    "significant_corrected": False,
                    "bonferroni_corrected": True,
                    "requires_realized_r": True,
                },
            ],
        }
    (harness_dir / "metrics_report.json").write_text(
        json.dumps(metrics_report, indent=2), encoding="utf-8")
    (harness_dir / "results.jsonl").write_text("", encoding="utf-8")
    (harness_dir / "decision_diff.md").write_text("# diff", encoding="utf-8")
    (harness_dir / "run_metadata.json").write_text("{}", encoding="utf-8")


def test_ablation_run_end_to_end_with_mocked_harness(tmp_path):
    """AblationRun.execute() loops over manifest, invokes (mocked)
    harness, aggregates summary."""
    prompt = _make_prompt(tmp_path, SAMPLE_PROMPT)
    manifest_path = _make_manifest_yaml(tmp_path, [
        {"name": "drop_ob", "description": "d",
         "transformation": "drop_section",
         "params": {"heading": "OB Zone Mechanism"}},
        {"name": "drop_kz", "description": "d",
         "transformation": "drop_section",
         "params": {"heading": "Kill Zone Schedule"}},
    ])
    manifest = AblationManifest.load(manifest_path)

    out_dir = tmp_path / "out"

    def fake_subprocess_run(cmd, **kwargs):
        # Parse --output to find which entry's harness dir to populate
        out_idx = cmd.index("--output")
        harness_dir = Path(cmd[out_idx + 1])
        _stub_harness_runner(harness_dir)

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""
        return Result()

    with mock.patch("src.research_infra.ablation_framework.subprocess.run",
                    side_effect=fake_subprocess_run) as mock_run:
        run = AblationRun(
            baseline_prompt=prompt,
            manifest=manifest,
            fixtures_spec="historical_cands",
            metrics_path=DEFAULT_METRICS,
            output_dir=out_dir,
            seed=1,
        )
        summary = run.execute()

    # Two harness invocations (one per ablation)
    assert mock_run.call_count == 2

    # Summary structure
    assert summary["framework_version"] == "L57-v1"
    assert summary["manifest"]["n_entries"] == 2
    assert len(summary["ablations"]) == 2
    assert summary["has_realized_r"] is False
    assert summary["verdict_suppressed"] == "realized_r_join_not_provided"

    for ent in summary["ablations"]:
        assert ent["error"] is None
        assert ent["walk_level_metrics"], (
            f"walk metrics missing for {ent['name']}"
        )
        assert "realized_r_paired_t" in ent["realized_r_metrics"]

    # Files written
    assert (out_dir / "ablation_summary.json").exists()
    assert (out_dir / "ablation_report.md").exists()
    assert (out_dir / "ablated_prompts" / "drop_ob.md").exists()
    assert (out_dir / "ablated_prompts" / "drop_kz.md").exists()


def test_ablation_run_realized_r_join_present_no_verdict_suppression(tmp_path):
    prompt = _make_prompt(tmp_path, SAMPLE_PROMPT)
    manifest_path = _make_manifest_yaml(tmp_path, [
        {"name": "drop_ob", "description": "d",
         "transformation": "drop_section",
         "params": {"heading": "OB Zone Mechanism"}},
    ])
    manifest = AblationManifest.load(manifest_path)

    out_dir = tmp_path / "out"
    sim_path = tmp_path / "sim.json"
    sim_path.write_text(json.dumps({"results": []}), encoding="utf-8")

    def fake_subprocess_run(cmd, **kwargs):
        out_idx = cmd.index("--output")
        harness_dir = Path(cmd[out_idx + 1])
        _stub_harness_runner(harness_dir, metrics_report={
            "n_fixtures": 5,
            "n_with_realized_r": 3,
            "bonferroni_denominator": 4,
            "metrics": [
                {
                    "name": "realized_r_paired_t",
                    "test": "paired_t",
                    "value": {"mean_delta_r_a_minus_b": 0.42,
                              "t_statistic": 1.5},
                    "n": 3, "p_value": 0.21,
                    "underpowered": False,
                    "significant_raw": False,
                    "significant_corrected": False,
                    "bonferroni_corrected": True,
                    "requires_realized_r": True,
                },
            ],
        })

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""
        return Result()

    with mock.patch("src.research_infra.ablation_framework.subprocess.run",
                    side_effect=fake_subprocess_run):
        run = AblationRun(
            baseline_prompt=prompt,
            manifest=manifest,
            fixtures_spec="historical_cands",
            metrics_path=DEFAULT_METRICS,
            output_dir=out_dir,
            realized_r_join=sim_path,
            seed=1,
        )
        summary = run.execute()

    # Realized-R join provided → no top-level suppression
    assert summary["has_realized_r"] is True
    assert "verdict_suppressed" not in summary
    # And the ablation entry surfaces the realized-R numbers
    rt = summary["ablations"][0]["realized_r_metrics"]["realized_r_paired_t"]
    assert rt["n"] == 3
    assert rt["p_value"] == pytest.approx(0.21)


def test_ablation_run_harness_failure_recorded(tmp_path):
    prompt = _make_prompt(tmp_path, SAMPLE_PROMPT)
    manifest_path = _make_manifest_yaml(tmp_path, [
        {"name": "drop_ob", "description": "d",
         "transformation": "drop_section",
         "params": {"heading": "OB Zone Mechanism"}},
    ])
    manifest = AblationManifest.load(manifest_path)

    def fake_subprocess_run(cmd, **kwargs):
        class Result:
            returncode = 2
            stdout = ""
            stderr = "metrics yaml missing required key"
        return Result()

    with mock.patch("src.research_infra.ablation_framework.subprocess.run",
                    side_effect=fake_subprocess_run):
        run = AblationRun(
            baseline_prompt=prompt,
            manifest=manifest,
            fixtures_spec="historical_cands",
            metrics_path=DEFAULT_METRICS,
            output_dir=tmp_path / "out",
            seed=1,
        )
        summary = run.execute()

    assert summary["ablations"][0]["error"] is not None
    assert "harness exit 2" in summary["ablations"][0]["error"]


def test_ablation_run_apply_failure_records_error_and_continues(tmp_path):
    """A bad regex on one entry should not abort the whole run — record
    the error on that entry and proceed."""
    prompt = _make_prompt(tmp_path, SAMPLE_PROMPT)
    manifest_path = _make_manifest_yaml(tmp_path, [
        {"name": "good", "description": "d",
         "transformation": "drop_section",
         "params": {"heading": "OB Zone Mechanism"}},
        {"name": "bad", "description": "d",
         "transformation": "regex_remove",
         "params": {"pattern": "[unclosed"}},  # invalid regex
    ])
    manifest = AblationManifest.load(manifest_path)

    def fake_subprocess_run(cmd, **kwargs):
        out_idx = cmd.index("--output")
        _stub_harness_runner(Path(cmd[out_idx + 1]))

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""
        return Result()

    with mock.patch("src.research_infra.ablation_framework.subprocess.run",
                    side_effect=fake_subprocess_run):
        run = AblationRun(
            baseline_prompt=prompt,
            manifest=manifest,
            fixtures_spec="historical_cands",
            metrics_path=DEFAULT_METRICS,
            output_dir=tmp_path / "out",
            seed=1,
        )
        summary = run.execute()

    by_name = {a["name"]: a for a in summary["ablations"]}
    assert by_name["good"]["error"] is None
    assert by_name["bad"]["error"] is not None
    assert "apply" in by_name["bad"]["error"]


# ===========================================================================
# Pre-registration sentinel — pin the v1 manifest SHA
# ===========================================================================


def test_manifest_default_v1_sentinel_pinned():
    """If you EDIT scripts/research/manifests/ablation_default_v1.yaml,
    this test fails by design.

    Per L57 docs, post-hoc manifest editing is post-hoc hypothesis
    formation (CLAUDE.md prohibited #5). To run a different ablation
    set, COPY the manifest to ablation_default_v2.yaml with a fresh
    manifest_set_id and reference the new file. Do NOT mutate v1.

    To deliberately update the sentinel after a CEO-approved manifest
    edit, recompute ABLATION_DEFAULT_V1_SHA256 with:

        sha256sum scripts/research/manifests/ablation_default_v1.yaml
    """
    actual = _manifest_normalized_sha(MANIFEST_DEFAULT_V1)
    assert actual == ABLATION_DEFAULT_V1_SHA256, (
        "ablation_default_v1.yaml SHA256 changed.\n"
        f"  pinned: {ABLATION_DEFAULT_V1_SHA256}\n"
        f"  actual: {actual}\n"
        "If the change is intentional, copy the manifest to "
        "ablation_default_v2.yaml with a fresh manifest_set_id "
        "instead of mutating v1. See L57_ablation_framework.md."
    )


def test_manifest_default_v1_set_id_pinned():
    """The manifest_set_id is its identifier; pin it. Authors should
    bump the id together with a new filename."""
    m = AblationManifest.load(MANIFEST_DEFAULT_V1)
    assert m.manifest_set_id == "ablation_default_v1"


# ===========================================================================
# CLI: --dry-run skips harness subprocess
# ===========================================================================


def test_dry_run_exits_zero_no_subprocess(tmp_path, capsys):
    prompt = _make_prompt(tmp_path, SAMPLE_PROMPT)
    out_dir = tmp_path / "out_dry"

    with mock.patch("src.research_infra.ablation_framework.subprocess.run") as mock_run:
        rc = ablation_runner.main([
            "--baseline-prompt", str(prompt),
            "--manifest", str(MANIFEST_DEFAULT_V1),
            "--fixtures", "historical_cands",
            "--metrics", str(DEFAULT_METRICS),
            "--output", str(out_dir),
            "--dry-run",
        ])

    assert rc == 0
    assert mock_run.call_count == 0, (
        "dry-run must NOT spawn the harness subprocess"
    )
    # The plan must mention the manifest set_id and at least one ablation
    captured = capsys.readouterr()
    assert "DRY-RUN PLAN" in captured.out
    assert "ablation_default_v1" in captured.out
    assert "drop_ob_zone_section" in captured.out
    assert "(skipping harness invocations" in captured.out


def test_dry_run_does_not_create_output_dir(tmp_path):
    prompt = _make_prompt(tmp_path, SAMPLE_PROMPT)
    out_dir = tmp_path / "no_such_dir_yet"

    with mock.patch("src.research_infra.ablation_framework.subprocess.run") as mock_run:
        rc = ablation_runner.main([
            "--baseline-prompt", str(prompt),
            "--manifest", str(MANIFEST_DEFAULT_V1),
            "--fixtures", "historical_cands",
            "--metrics", str(DEFAULT_METRICS),
            "--output", str(out_dir),
            "--dry-run",
        ])
    assert rc == 0
    assert mock_run.call_count == 0
    # AblationRun never gets to .execute(), so the output dir stays unmade.
    assert not out_dir.exists()


def test_runner_main_passes_realized_r_join_through(tmp_path):
    prompt = _make_prompt(tmp_path, SAMPLE_PROMPT)
    manifest_path = _make_manifest_yaml(tmp_path, [
        {"name": "drop_ob", "description": "d",
         "transformation": "drop_section",
         "params": {"heading": "OB Zone Mechanism"}},
    ])
    out_dir = tmp_path / "out"
    sim_path = tmp_path / "sim.json"
    sim_path.write_text(json.dumps({"results": []}), encoding="utf-8")

    captured_cmds: list[list[str]] = []

    def fake_subprocess_run(cmd, **kwargs):
        captured_cmds.append(cmd)
        out_idx = cmd.index("--output")
        _stub_harness_runner(Path(cmd[out_idx + 1]))

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""
        return Result()

    with mock.patch("src.research_infra.ablation_framework.subprocess.run",
                    side_effect=fake_subprocess_run):
        rc = ablation_runner.main([
            "--baseline-prompt", str(prompt),
            "--manifest", str(manifest_path),
            "--fixtures", "historical_cands",
            "--metrics", str(DEFAULT_METRICS),
            "--output", str(out_dir),
            "--realized-r-join", str(sim_path),
        ])

    assert rc == 0
    assert len(captured_cmds) == 1
    # The realized-r-join must be forwarded
    assert "--realized-r-join" in captured_cmds[0]
    rrj_idx = captured_cmds[0].index("--realized-r-join")
    assert captured_cmds[0][rrj_idx + 1] == str(sim_path)


def test_runner_subprocess_command_shape(tmp_path):
    """Verify the subprocess command shape so future edits to the
    harness CLI don't silently break the runner."""
    prompt = _make_prompt(tmp_path, SAMPLE_PROMPT)
    manifest_path = _make_manifest_yaml(tmp_path, [
        {"name": "drop_ob", "description": "d",
         "transformation": "drop_section",
         "params": {"heading": "OB Zone Mechanism"}},
    ])
    manifest = AblationManifest.load(manifest_path)

    captured_cmds: list[list[str]] = []

    def fake_subprocess_run(cmd, **kwargs):
        captured_cmds.append(cmd)
        out_idx = cmd.index("--output")
        _stub_harness_runner(Path(cmd[out_idx + 1]))

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""
        return Result()

    with mock.patch("src.research_infra.ablation_framework.subprocess.run",
                    side_effect=fake_subprocess_run):
        run = AblationRun(
            baseline_prompt=prompt,
            manifest=manifest,
            fixtures_spec="historical_cands",
            metrics_path=DEFAULT_METRICS,
            output_dir=tmp_path / "out",
            seed=42,
        )
        run.execute()

    assert len(captured_cmds) == 1
    cmd = captured_cmds[0]
    # Required flags all present
    for required in ("--prompt-a", "--prompt-b", "--fixtures",
                     "--metrics", "--output", "--seed"):
        assert required in cmd, f"missing harness flag: {required}"
    # --live should NOT be present unless explicitly requested
    assert "--live" not in cmd
    # Seed forwarded
    seed_idx = cmd.index("--seed")
    assert cmd[seed_idx + 1] == "42"


# ===========================================================================
# Report output regression
# ===========================================================================


def test_ablation_report_md_includes_verdict_suppression_banner(tmp_path):
    prompt = _make_prompt(tmp_path, SAMPLE_PROMPT)
    manifest_path = _make_manifest_yaml(tmp_path, [
        {"name": "drop_ob", "description": "d",
         "transformation": "drop_section",
         "params": {"heading": "OB Zone Mechanism"}},
    ])
    manifest = AblationManifest.load(manifest_path)
    out_dir = tmp_path / "out"

    def fake_subprocess_run(cmd, **kwargs):
        out_idx = cmd.index("--output")
        _stub_harness_runner(Path(cmd[out_idx + 1]))

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""
        return Result()

    with mock.patch("src.research_infra.ablation_framework.subprocess.run",
                    side_effect=fake_subprocess_run):
        run = AblationRun(
            baseline_prompt=prompt,
            manifest=manifest,
            fixtures_spec="historical_cands",
            metrics_path=DEFAULT_METRICS,
            output_dir=out_dir,
            seed=1,
        )
        run.execute()

    report = (out_dir / "ablation_report.md").read_text(encoding="utf-8")
    assert "VERDICT SUPPRESSED" in report
    assert "realized-R join not provided" in report
    # Table header present
    assert "ablation" in report
    assert "transformation" in report
