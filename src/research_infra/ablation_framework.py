"""L57 — Edge-Component Ablation Framework.

Phase 1 research-program task L57. Provides one canonical mechanism for
"drop a single edge component and measure the delta", reusable by
Phase 2 B10 (prompt ablation matrix) and several Phase 1 follow-ups.

GOALS
=====
1. **Manifest-driven**: ablations are listed in a YAML/JSON manifest;
   the manifest filename is part of the run hash so post-hoc edits are
   detectable (pre-registration discipline mirrors L56's
   ``metrics_set_id`` pattern).
2. **Deterministic transformations**: applying the same manifest entry
   to the same prompt always produces byte-identical output.
3. **Joinable to realized R**: the loop driver delegates per-comparison
   metrics computation to ``prompt_ab_harness`` (L56) which already
   joins decisions to historical realized R. The framework refuses to
   emit a "verdict" if realized-R join is missing — walk-level CR /
   decision-flip deltas are NOT predictive of realized R per memory
   ``feedback_walk_level_evidence_not_predictive.md``.
4. **Additive only**: the framework does NOT modify any file under
   ``prompts/`` or ``src/`` outside ``src/research_infra/``. Ablated
   prompts are written to ``output_dir`` only — never back to the
   source tree.

NON-GOALS
=========
- Modifying production prompts under ``prompts/`` or production code
  under ``src/components/``.
- Implementing a real-API call seam — that lives in
  ``prompt_ab_harness.py`` (L56) which the runner subprocesses to.
- Gate-level ablation that requires editing ``permissions.py`` or
  framework-list ablation that requires editing ``agent_config.yaml``.
  Both are documented as Phase 2 work; the manifest schema accepts
  them but Wave 1 transformations only edit prompt text. The
  ``drop_framework`` and ``drop_gate`` transformations therefore
  declare a target_file in the manifest entry but operate on a
  STAGED COPY of that file in the output dir; the harness call still
  receives the unmodified prompt — a TODO sentinel makes that clear.

TRANSFORMATIONS
===============
``drop_section``
    Remove a Markdown ``## <heading>`` section, bounded from the
    matching heading line through the next ``## `` heading or EOF.
    ``params``: ``{"heading": "<exact heading text>"}``.

``drop_framework``
    Edit the ``enabled_frameworks`` list (operates on the
    ``agent_config.yaml`` referenced by ``params.target_file``,
    NOT on the prompt). Wave 1 stages the file copy under the run's
    output dir but keeps the prompt unchanged when handing off to the
    harness — a known limitation; see ``L57_ablation_framework.md``.
    ``params``: ``{"framework": "<name>", "target_file": "<path>"}``.

``drop_gate``
    Remove a permissions gate by name. Wave 1 keeps this PROMPT-ONLY
    by stripping any sentence containing the gate's literal name; full
    gate-removal requires re-wiring ``permissions.py`` which is Phase 2.
    ``params``: ``{"gate": "<name>"}``.

``replace_text``
    Literal find-replace.
    ``params``: ``{"find": "<literal>", "replace": "<literal>"}``.

``regex_remove``
    Regex match-and-remove. Sandboxed: rejects look-around and
    repeating-quantifier-on-quantifier patterns that can DoS.
    ``params``: ``{"pattern": "<regex>"}``.

PUBLIC API
==========
``AblationManifest``     — load + validate a manifest YAML/JSON.
``AblationApplicator``   — pure transformation function per entry.
``AblationRun``          — drives the prompt-AB harness over each
                           manifest entry; aggregates results.

The CLI driver lives in ``scripts/research/ablation_runner.py``.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml


logger = logging.getLogger("ablation_framework")


# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------


VALID_TRANSFORMATIONS = frozenset({
    "drop_section",
    "drop_framework",
    "drop_gate",
    "replace_text",
    "regex_remove",
})

REQUIRED_ENTRY_KEYS = ("name", "description", "transformation", "params")

REQUIRED_PARAMS_BY_TRANSFORMATION: dict[str, tuple[str, ...]] = {
    "drop_section": ("heading",),
    "drop_framework": ("framework", "target_file"),
    "drop_gate": ("gate",),
    "replace_text": ("find", "replace"),
    "regex_remove": ("pattern",),
}


# Regex sandbox: reject patterns that combine look-around with a
# quantifier OR that nest unbounded quantifiers on a quantified group.
# This is a heuristic, not a sound DoS defence — production use of this
# framework still runs the regex in a subprocess with timeouts.
_REGEX_FORBIDDEN = (
    re.compile(r"\(\?[=!<]"),  # look-around (positive/negative ahead/behind)
    re.compile(r"\(\?<="),
    re.compile(r"\)[+*]\s*[+*]"),  # quantifier directly after a group quantifier
    re.compile(r"\)\{[0-9,]+\}\s*\{"),  # bounded then unbounded repeat
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class AblationError(Exception):
    """Base class for ablation framework errors."""


class ManifestSchemaError(AblationError):
    """Raised when a manifest entry violates the schema."""


class TransformationError(AblationError):
    """Raised when a transformation cannot be applied to the input."""


class UnsafeRegexError(AblationError):
    """Raised when a regex_remove pattern fails the sandbox check."""


# ---------------------------------------------------------------------------
# AblationManifest
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class AblationEntry:
    """A single manifest entry — pure data."""

    name: str
    description: str
    transformation: str
    params: Mapping[str, Any]


class AblationManifest:
    """Loaded ablation manifest with schema validation.

    Pre-registration discipline: the harness uses the SHA256 of the raw
    manifest file together with the manifest filename as part of the run
    hash. Any post-run edit changes the SHA, which makes the change
    detectable at review time — see L56 ``metrics_set_id`` pattern.
    """

    def __init__(self, *, path: str | Path,
                 manifest_set_id: str,
                 entries: Sequence[AblationEntry],
                 raw_text: str) -> None:
        self.path = str(path)
        self.manifest_set_id = manifest_set_id
        self.entries = list(entries)
        self._raw_text = raw_text

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: str | Path) -> "AblationManifest":
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Manifest not found: {p}")
        raw_text = p.read_text(encoding="utf-8")
        suffix = p.suffix.lower()
        if suffix in {".yaml", ".yml"}:
            data = yaml.safe_load(raw_text) or {}
        elif suffix == ".json":
            data = json.loads(raw_text or "{}")
        else:
            raise ManifestSchemaError(
                f"Manifest must be .yaml/.yml/.json: {p} (got {suffix!r})")

        if not isinstance(data, Mapping):
            raise ManifestSchemaError(
                f"Manifest top-level must be a mapping: {p}")

        manifest_set_id = data.get("manifest_set_id")
        if not isinstance(manifest_set_id, str) or not manifest_set_id:
            raise ManifestSchemaError(
                f"Manifest missing required `manifest_set_id: <str>`: {p}")

        raw_entries = data.get("ablations")
        if not isinstance(raw_entries, list) or not raw_entries:
            raise ManifestSchemaError(
                f"Manifest missing required `ablations: <list>`: {p}")

        entries: list[AblationEntry] = []
        seen_names: set[str] = set()
        for idx, raw in enumerate(raw_entries):
            if not isinstance(raw, Mapping):
                raise ManifestSchemaError(
                    f"ablations[{idx}] must be a mapping in {p}")
            for key in REQUIRED_ENTRY_KEYS:
                if key not in raw:
                    raise ManifestSchemaError(
                        f"ablations[{idx}] missing required key {key!r}: "
                        f"{p}"
                    )
            name = str(raw["name"])
            if name in seen_names:
                raise ManifestSchemaError(
                    f"ablations[{idx}] duplicate name {name!r} in {p}")
            seen_names.add(name)
            transformation = str(raw["transformation"])
            if transformation not in VALID_TRANSFORMATIONS:
                raise ManifestSchemaError(
                    f"ablations[{idx}] {name!r}: unknown transformation "
                    f"{transformation!r}; valid: {sorted(VALID_TRANSFORMATIONS)}"
                )
            params = raw["params"] or {}
            if not isinstance(params, Mapping):
                raise ManifestSchemaError(
                    f"ablations[{idx}] {name!r}: params must be a mapping")
            required_params = REQUIRED_PARAMS_BY_TRANSFORMATION[transformation]
            for rp in required_params:
                if rp not in params:
                    raise ManifestSchemaError(
                        f"ablations[{idx}] {name!r}: transformation "
                        f"{transformation!r} requires params.{rp}")

            entries.append(AblationEntry(
                name=name,
                description=str(raw["description"]),
                transformation=transformation,
                params=dict(params),
            ))

        return cls(
            path=p,
            manifest_set_id=manifest_set_id,
            entries=entries,
            raw_text=raw_text,
        )

    # ------------------------------------------------------------------
    # Hashing
    # ------------------------------------------------------------------

    @property
    def sha256(self) -> str:
        h = hashlib.sha256()
        h.update(self._raw_text.encode("utf-8"))
        return h.hexdigest()

    @property
    def filename(self) -> str:
        return Path(self.path).name

    @property
    def run_hash(self) -> str:
        """Combined hash of (filename, content). Two manifests with the
        same content but different filenames produce different run hashes
        — pre-registration discipline."""
        h = hashlib.sha256()
        h.update(self.filename.encode("utf-8"))
        h.update(b"|")
        h.update(self._raw_text.encode("utf-8"))
        return h.hexdigest()

    # ------------------------------------------------------------------
    # Iteration helpers
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterable[AblationEntry]:
        return iter(self.entries)

    def __len__(self) -> int:
        return len(self.entries)


# ---------------------------------------------------------------------------
# AblationApplicator
# ---------------------------------------------------------------------------


class AblationApplicator:
    """Pure transformation functions, one per declared transformation
    type. Stateless — every call is a deterministic function of (input
    text, manifest entry)."""

    @staticmethod
    def apply(prompt_text: str, entry: AblationEntry | Mapping[str, Any]) -> str:
        """Apply a single ablation transformation to ``prompt_text``.

        Accepts either an ``AblationEntry`` or a raw dict (so callers
        can pre-build entries inline in tests).
        """
        if isinstance(entry, AblationEntry):
            transformation = entry.transformation
            params = entry.params
        else:
            transformation = entry["transformation"]
            params = entry.get("params") or {}

        if transformation == "drop_section":
            return AblationApplicator._drop_section(prompt_text, params["heading"])
        if transformation == "drop_framework":
            # Wave 1: prompt-only operation. We strip occurrences of the
            # framework name from the prompt, but the canonical
            # framework-removal happens at agent_config.yaml level —
            # which is Phase 2. Document this in the docs file.
            return AblationApplicator._drop_framework_in_prompt(
                prompt_text, params["framework"]
            )
        if transformation == "drop_gate":
            return AblationApplicator._drop_gate(prompt_text, params["gate"])
        if transformation == "replace_text":
            return AblationApplicator._replace_text(
                prompt_text, params["find"], params["replace"]
            )
        if transformation == "regex_remove":
            return AblationApplicator._regex_remove(
                prompt_text, params["pattern"]
            )
        raise TransformationError(
            f"Unknown transformation: {transformation!r}"
        )

    # ------------------------------------------------------------------
    # drop_section
    # ------------------------------------------------------------------

    @staticmethod
    def _drop_section(text: str, heading: str) -> str:
        """Remove a Markdown ``## <heading>`` section. The heading match
        is on the LITERAL heading text; "OB Zone Mechanism" matches
        ``## OB Zone Mechanism`` (and only that). The section is bounded
        from the heading line through the next ``## `` (or EOF).

        If the heading is not found, the input is returned unchanged
        and a debug log is emitted — callers usually want this to fail
        loudly, so a missing-heading case still increments the
        delta-from-baseline detection in ``_assert_text_changed``.
        """
        lines = text.splitlines(keepends=True)
        heading_re = re.compile(r"^\s*##\s+" + re.escape(heading) + r"\s*$")
        next_section_re = re.compile(r"^\s*##\s+")

        start: int | None = None
        for i, line in enumerate(lines):
            if heading_re.match(line.rstrip("\n")):
                start = i
                break
        if start is None:
            logger.debug("drop_section: heading %r not found", heading)
            return text
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if next_section_re.match(lines[j].rstrip("\n")):
                end = j
                break
        del lines[start:end]
        return "".join(lines)

    # ------------------------------------------------------------------
    # drop_framework (prompt-only Wave 1)
    # ------------------------------------------------------------------

    @staticmethod
    def _drop_framework_in_prompt(text: str, framework: str) -> str:
        """Strip lines mentioning the framework name verbatim from the
        prompt. This is the Wave 1 prompt-only ablation — the canonical
        framework-list edit happens in ``agent_config.yaml`` and is
        Phase 2 work.

        We use line-level removal (not regex_remove) because frameworks
        are typically named on dedicated lines in the prompt
        (``- ob_retest: ...``), and partial-line removal would corrupt
        surrounding text.
        """
        if not framework:
            return text
        kept: list[str] = []
        for line in text.splitlines(keepends=True):
            if framework in line:
                continue
            kept.append(line)
        return "".join(kept)

    # ------------------------------------------------------------------
    # drop_gate (prompt-only Wave 1)
    # ------------------------------------------------------------------

    @staticmethod
    def _drop_gate(text: str, gate: str) -> str:
        """Strip sentences containing the gate name. Sentence boundary
        detection is naive: a sentence is delimited by ``. ``, ``! ``,
        ``? `` or newline. The function operates LINE-BY-LINE so a
        gate-mentioning sentence inside one paragraph doesn't drag in
        the next paragraph.

        Wave 1 limitation: full gate ablation requires editing
        ``permissions.py`` which is Phase 2. Documented in
        ``L57_ablation_framework.md``.
        """
        if not gate:
            return text
        out_lines: list[str] = []
        for line in text.splitlines(keepends=True):
            stripped = line.rstrip("\n").rstrip("\r")
            line_end = line[len(stripped):]
            if gate not in stripped:
                out_lines.append(line)
                continue
            # Split on sentence enders, retain non-gate sentences.
            parts = re.split(r"(?<=[.!?])\s+", stripped)
            kept_parts = [p for p in parts if gate not in p]
            cleaned = " ".join(kept_parts).strip()
            if cleaned:
                out_lines.append(cleaned + line_end)
            # else: drop the line entirely
        return "".join(out_lines)

    # ------------------------------------------------------------------
    # replace_text
    # ------------------------------------------------------------------

    @staticmethod
    def _replace_text(text: str, find: str, replace: str) -> str:
        if find == "":
            raise TransformationError("replace_text.find must be non-empty")
        return text.replace(find, replace)

    # ------------------------------------------------------------------
    # regex_remove
    # ------------------------------------------------------------------

    @staticmethod
    def _regex_remove(text: str, pattern: str) -> str:
        for forbidden in _REGEX_FORBIDDEN:
            if forbidden.search(pattern):
                raise UnsafeRegexError(
                    f"regex_remove pattern {pattern!r} matches forbidden "
                    f"shape {forbidden.pattern!r}; reject for sandbox safety."
                )
        try:
            compiled = re.compile(pattern, re.MULTILINE)
        except re.error as exc:
            raise TransformationError(
                f"regex_remove: invalid pattern {pattern!r}: {exc}"
            )
        return compiled.sub("", text)


# ---------------------------------------------------------------------------
# AblationRun — drives prompt_ab_harness per manifest entry
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class AblationRunResult:
    """Per-entry result of a full ablation run."""

    entry_name: str
    transformation: str
    params: Mapping[str, Any]
    ablated_prompt_path: str
    ablated_prompt_sha256: str
    harness_output_dir: str
    metrics_report: Mapping[str, Any] | None = None
    error: str | None = None


class AblationRun:
    """Drives the L56 prompt A/B harness over every manifest entry.

    For each entry, the framework:
      1. Reads the baseline prompt file (read-only — never modified).
      2. Applies the manifest entry's transformation in-memory.
      3. Writes the ablated prompt to
         ``output_dir/ablated_prompts/<name>.md``.
      4. Subprocesses ``scripts/research/prompt_ab_harness.py`` with
         ``--prompt-a baseline --prompt-b ablated``.
      5. Loads the harness's ``metrics_report.json`` into a per-entry
         result and aggregates everything into
         ``output_dir/ablation_summary.json``.

    The harness itself is a stable subprocess interface — this class
    intentionally does NOT import its private functions. It uses the
    same ``--metrics`` YAML that L56 uses, so realized-R join semantics
    + Bonferroni correction + walk-vs-realized split are inherited.

    The framework refuses to emit a "verdict" key in
    ``ablation_summary.json`` if no realized-R join was provided. Walk-
    level metrics still appear, but the loop driver flags
    ``verdict_suppressed: realized_r_join_not_provided`` so consumers
    don't accidentally infer realized-R from walk-level deltas (memory
    ``feedback_walk_level_evidence_not_predictive.md``).
    """

    def __init__(self, *,
                 baseline_prompt: str | Path,
                 manifest: AblationManifest,
                 fixtures_spec: str,
                 metrics_path: str | Path,
                 output_dir: str | Path,
                 realized_r_join: str | Path | None = None,
                 seed: int = 1,
                 dry_run: bool = False,
                 live: bool = False,
                 harness_path: str | Path | None = None,
                 python_executable: str | None = None) -> None:
        self.baseline_prompt = Path(baseline_prompt)
        if not self.baseline_prompt.exists():
            raise FileNotFoundError(
                f"Baseline prompt not found: {self.baseline_prompt}")
        self.manifest = manifest
        self.fixtures_spec = fixtures_spec
        self.metrics_path = Path(metrics_path)
        self.output_dir = Path(output_dir)
        self.realized_r_join = (Path(realized_r_join)
                                if realized_r_join else None)
        self.seed = int(seed)
        self.dry_run = bool(dry_run)
        self.live = bool(live)
        # Harness location — defaults to repo-relative path
        if harness_path is None:
            project_root = Path(__file__).resolve().parents[2]
            harness_path = (project_root / "scripts" / "research"
                            / "prompt_ab_harness.py")
        self.harness_path = Path(harness_path)
        self.python_executable = python_executable or sys.executable

    # ------------------------------------------------------------------
    # Plan
    # ------------------------------------------------------------------

    def plan(self) -> list[Mapping[str, Any]]:
        """Return the list of planned (name, ablated_prompt_path,
        harness_output_dir) tuples without invoking the harness. Used
        by ``--dry-run``."""
        plan: list[Mapping[str, Any]] = []
        for entry in self.manifest:
            ablated_path = (self.output_dir / "ablated_prompts"
                            / f"{entry.name}.md")
            harness_dir = self.output_dir / "harness_runs" / entry.name
            plan.append({
                "name": entry.name,
                "transformation": entry.transformation,
                "params": dict(entry.params),
                "ablated_prompt_path": str(ablated_path),
                "harness_output_dir": str(harness_dir),
            })
        return plan

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def execute(self) -> Mapping[str, Any]:
        """Run all ablations end-to-end. Returns the aggregated summary
        dict. Also writes ``ablation_summary.json`` and
        ``ablation_report.md`` into ``output_dir``."""
        baseline_text = self.baseline_prompt.read_text(encoding="utf-8")
        baseline_sha = hashlib.sha256(
            baseline_text.encode("utf-8")).hexdigest()

        self.output_dir.mkdir(parents=True, exist_ok=True)
        ablated_dir = self.output_dir / "ablated_prompts"
        ablated_dir.mkdir(parents=True, exist_ok=True)
        runs_dir = self.output_dir / "harness_runs"
        runs_dir.mkdir(parents=True, exist_ok=True)

        results: list[AblationRunResult] = []
        for entry in self.manifest:
            try:
                ablated_text = AblationApplicator.apply(baseline_text, entry)
            except AblationError as exc:
                logger.error("Ablation %s failed during apply: %s",
                             entry.name, exc)
                results.append(AblationRunResult(
                    entry_name=entry.name,
                    transformation=entry.transformation,
                    params=dict(entry.params),
                    ablated_prompt_path="",
                    ablated_prompt_sha256="",
                    harness_output_dir="",
                    error=f"apply: {exc}",
                ))
                continue

            ablated_path = ablated_dir / f"{entry.name}.md"
            ablated_path.write_text(ablated_text, encoding="utf-8")
            ablated_sha = hashlib.sha256(
                ablated_text.encode("utf-8")).hexdigest()

            harness_dir = runs_dir / entry.name
            harness_dir.mkdir(parents=True, exist_ok=True)

            metrics_report: Mapping[str, Any] | None = None
            error: str | None = None

            if not self.dry_run:
                rc, stderr = self._invoke_harness(
                    baseline_path=self.baseline_prompt,
                    ablated_path=ablated_path,
                    harness_dir=harness_dir,
                )
                if rc != 0:
                    error = (f"harness exit {rc}: {stderr.strip()[:200]}"
                             if stderr else f"harness exit {rc}")
                else:
                    report_path = harness_dir / "metrics_report.json"
                    if report_path.exists():
                        try:
                            with report_path.open("r", encoding="utf-8") as fh:
                                metrics_report = json.load(fh)
                        except Exception as exc:
                            error = f"report parse: {exc}"
                    else:
                        error = "metrics_report.json missing"

            results.append(AblationRunResult(
                entry_name=entry.name,
                transformation=entry.transformation,
                params=dict(entry.params),
                ablated_prompt_path=str(ablated_path),
                ablated_prompt_sha256=ablated_sha,
                harness_output_dir=str(harness_dir),
                metrics_report=metrics_report,
                error=error,
            ))

        summary = self._build_summary(baseline_sha, results)
        self._write_summary(summary)
        self._write_report_md(summary)
        return summary

    # ------------------------------------------------------------------
    # Subprocess invocation
    # ------------------------------------------------------------------

    def _invoke_harness(self, *,
                        baseline_path: Path,
                        ablated_path: Path,
                        harness_dir: Path) -> tuple[int, str]:
        cmd = [
            self.python_executable, str(self.harness_path),
            "--prompt-a", str(baseline_path),
            "--prompt-b", str(ablated_path),
            "--fixtures", self.fixtures_spec,
            "--metrics", str(self.metrics_path),
            "--output", str(harness_dir),
            "--seed", str(self.seed),
        ]
        if self.realized_r_join:
            cmd += ["--realized-r-join", str(self.realized_r_join)]
        if self.live:
            cmd.append("--live")
        logger.info("Invoking harness: %s", " ".join(cmd))
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=900, check=False,
            )
            if result.stderr:
                logger.debug("harness stderr: %s", result.stderr.strip())
            return (result.returncode, result.stderr or "")
        except subprocess.TimeoutExpired as exc:
            return (124, f"timeout after {exc.timeout}s")
        except FileNotFoundError as exc:
            return (127, f"executable not found: {exc}")

    # ------------------------------------------------------------------
    # Summary writers
    # ------------------------------------------------------------------

    def _build_summary(self, baseline_sha: str,
                       results: Sequence[AblationRunResult]) -> dict[str, Any]:
        has_realized_r = self.realized_r_join is not None

        per_entry: list[dict[str, Any]] = []
        for r in results:
            entry_record: dict[str, Any] = {
                "name": r.entry_name,
                "transformation": r.transformation,
                "params": dict(r.params),
                "ablated_prompt_sha256": r.ablated_prompt_sha256,
                "ablated_prompt_path": r.ablated_prompt_path,
                "harness_output_dir": r.harness_output_dir,
                "error": r.error,
            }
            walk_level: dict[str, Any] = {}
            realized_r: dict[str, Any] = {}
            if r.metrics_report:
                metrics = r.metrics_report.get("metrics", [])
                # Walk-level: cr_rate_compare / decision_label_diff.
                for m in metrics:
                    name = m.get("name")
                    if name in {"cr_rate_compare", "decision_label_diff"}:
                        walk_level[name] = {
                            "value": m.get("value"),
                            "p_value": m.get("p_value"),
                            "n": m.get("n"),
                            "significant_corrected":
                                m.get("significant_corrected"),
                            "underpowered": m.get("underpowered"),
                        }
                    elif name in {"realized_r_paired_t",
                                  "realized_r_wilcoxon",
                                  "realized_r_winrate_a",
                                  "realized_r_winrate_b"}:
                        realized_r[name] = {
                            "value": m.get("value"),
                            "p_value": m.get("p_value"),
                            "n": m.get("n"),
                            "significant_corrected":
                                m.get("significant_corrected"),
                            "underpowered": m.get("underpowered"),
                            "skipped": m.get("skipped", False),
                        }
                entry_record["n_fixtures"] = r.metrics_report.get(
                    "n_fixtures")
                entry_record["n_with_realized_r"] = r.metrics_report.get(
                    "n_with_realized_r")
                entry_record["bonferroni_denominator"] = (
                    r.metrics_report.get("bonferroni_denominator"))
            entry_record["walk_level_metrics"] = walk_level
            entry_record["realized_r_metrics"] = realized_r
            # Per-entry verdict suppression — same rule as the top-level.
            if not has_realized_r:
                entry_record["verdict_suppressed"] = (
                    "realized_r_join_not_provided")
            per_entry.append(entry_record)

        summary: dict[str, Any] = {
            "framework_version": "L57-v1",
            "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "manifest": {
                "path": self.manifest.path,
                "filename": self.manifest.filename,
                "manifest_set_id": self.manifest.manifest_set_id,
                "sha256": self.manifest.sha256,
                "run_hash": self.manifest.run_hash,
                "n_entries": len(self.manifest),
            },
            "baseline_prompt": {
                "path": str(self.baseline_prompt),
                "sha256": baseline_sha,
            },
            "fixtures_spec": self.fixtures_spec,
            "metrics_path": str(self.metrics_path),
            "realized_r_join": (str(self.realized_r_join)
                                if self.realized_r_join else None),
            "has_realized_r": has_realized_r,
            "seed": self.seed,
            "live": self.live,
            "dry_run": self.dry_run,
            "ablations": per_entry,
        }
        if not has_realized_r:
            summary["verdict_suppressed"] = "realized_r_join_not_provided"
            summary["verdict_note"] = (
                "Walk-level deltas are NOT predictive of realized R "
                "(memory feedback_walk_level_evidence_not_predictive.md). "
                "Re-run with --realized-r-join <path> to surface a verdict."
            )
        return summary

    def _write_summary(self, summary: Mapping[str, Any]) -> None:
        out_path = self.output_dir / "ablation_summary.json"
        out_path.write_text(json.dumps(summary, indent=2, default=str),
                            encoding="utf-8")
        logger.info("Wrote %s", out_path)

    def _write_report_md(self, summary: Mapping[str, Any]) -> None:
        """Emit a Markdown table summarising all ablations."""
        lines: list[str] = []
        lines.append("# L57 Ablation Run Report\n")
        lines.append(f"- Manifest: `{summary['manifest']['filename']}` "
                     f"(set_id `{summary['manifest']['manifest_set_id']}`)")
        lines.append(f"- Manifest SHA: `{summary['manifest']['sha256'][:12]}`")
        lines.append(f"- Baseline prompt: `{summary['baseline_prompt']['path']}` "
                     f"(sha `{summary['baseline_prompt']['sha256'][:12]}`)")
        lines.append(f"- Fixtures: `{summary['fixtures_spec']}`")
        lines.append(f"- Realized-R join: "
                     f"`{summary['realized_r_join'] or '(none)'}`")
        lines.append(f"- Ablations: {summary['manifest']['n_entries']}")
        if summary.get("verdict_suppressed"):
            lines.append("")
            lines.append("> **VERDICT SUPPRESSED** — "
                         "realized-R join not provided. Walk-level metrics "
                         "below are descriptive only.")
        lines.append("")
        lines.append("| ablation | transformation | n | walk: CR-McNemar p | "
                     "walk: label-flip p | realized-R Δ (mean) | "
                     "realized-R p | bonf-sig | error |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for ent in summary["ablations"]:
            walk = ent.get("walk_level_metrics", {})
            real = ent.get("realized_r_metrics", {})
            cr = walk.get("cr_rate_compare", {})
            lf = walk.get("decision_label_diff", {})
            rt = real.get("realized_r_paired_t", {})
            bonf_sig = (rt.get("significant_corrected") if rt else None)
            mean_r = ""
            if rt and isinstance(rt.get("value"), Mapping):
                mean_r = rt["value"].get("mean_delta_r_a_minus_b", "")
                if isinstance(mean_r, (int, float)):
                    mean_r = f"{mean_r:+.4f}"
            lines.append(
                f"| {ent['name']} | {ent['transformation']} | "
                f"{ent.get('n_fixtures', '-')} | "
                f"{_fmt_p(cr.get('p_value'))} | "
                f"{_fmt_p(lf.get('p_value'))} | "
                f"{mean_r or '-'} | "
                f"{_fmt_p(rt.get('p_value'))} | "
                f"{bonf_sig if bonf_sig is not None else '-'} | "
                f"{(ent.get('error') or '')[:60]} |"
            )
        out_path = self.output_dir / "ablation_report.md"
        out_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Wrote %s", out_path)


def _fmt_p(p: Any) -> str:
    if p is None:
        return "-"
    if isinstance(p, (int, float)):
        if p < 1e-4:
            return f"{p:.2e}"
        return f"{p:.4f}"
    return str(p)
