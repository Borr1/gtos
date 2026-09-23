from pathlib import Path

from scripts.validate_goal_prompt_hardening import validate_prompt


def test_validate_goal_prompt_hardening_rejects_weak_prompt(tmp_path: Path) -> None:
    prompt = tmp_path / "WEAK.md"
    prompt.write_text("Summarize the route and list top 3 issues later.", encoding="utf-8")

    result = validate_prompt(prompt)

    assert result["ok"] is False
    assert "mandatory_goal_discipline_context" in result["missing"]
    assert "result_materialization_standard_present" in result["missing"]
    assert "no_arbitrary_top_n" in result["missing"]


def test_validate_goal_prompt_hardening_rejects_boundary_false_positive(
    tmp_path: Path,
) -> None:
    prompt = tmp_path / "PROMPT.md"
    prompt.write_text(
        "\n".join(
            [
                "goal_session_research_discipline.md",
                "research_operating_doctrine.md",
                "do not rely on chat memory",
                "proof-or-impossibility",
                "same-evidence-class",
                "no arbitrary top-N; full ledger",
                "not conservative; constructive curiosity",
                "active instructions, not background",
                "result materialization with exact R, proxy R, source completeness, and implementation decision",
                "deliver capital without real boundary words",
                "completion audit, verifier, focused test, ledger, manifest, artifact",
            ]
        ),
        encoding="utf-8",
    )

    result = validate_prompt(prompt)

    assert result["ok"] is False
    assert "forbidden_surfaces_core_present" in result["missing"]
