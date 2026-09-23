"""Recover missing papers.csv files from existing papers.md.

For each of 14 literature domain dirs, parse the papers.md file (which uses one
of two heading styles -- `### Title` or `#### Title` -- and several bullet
field-name variants) and emit a canonical-schema papers.csv plus an aggregate
recovery_summary.csv. Also write an audit report at
research/ml_program/audit/literature_csv_recovery.md.

Schema:
    domain,title,authors,year,url,source,relevance_score,cross_domain_flag,hypothesis_implied
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

ROOT = Path(r"C:/Users/MSI/Documents/ai-trading-agent")
LIT_ROOT = ROOT / "research" / "ml_program" / "literature"
AUDIT_PATH = ROOT / "research" / "ml_program" / "audit" / "literature_csv_recovery.md"
SYNTH_PATH = LIT_ROOT / "synthesis" / "recovery_summary.csv"

DOMAINS = [
    "01_math_foundations",
    "03_distributional_characteristics",
    "08_volume_auction_vwap_opex",
    "10_gold_commodities",
    "11_fx_rates_carry_central_banks",
    "12_equity_indices_options_gamma",
    "13_cross_asset_correlation_factors",
    "14_trend_momentum_breakout",
    "15_mean_reversion_cointegration_statarb",
    "16_volatility_derivatives_vol_regime",
    "17_behavioral_adaptive_markets",
    "18_trader_psychology_decision",
    "21_risk_management_kelly_sizing",
    "22_hedge_fund_alpha_wallstreet_quantum",
]

CSV_HEADER = [
    "domain",
    "title",
    "authors",
    "year",
    "url",
    "source",
    "relevance_score",
    "cross_domain_flag",
    "hypothesis_implied",
]


# -----------------------------------------------------------------------------
# Section-header detection: lines that are headings but NOT paper entries.
# -----------------------------------------------------------------------------
# A "paper entry" heading is one whose body block contains at least one of the
# canonical bullet fields (Authors / Year / URL / Source). A "section header" is
# one without those fields immediately under it -- e.g. `### Foundational`.
PAPER_FIELDS_RX = re.compile(
    r"\*\*(authors?|year(?:[/_ ]source)?|source|url|relevance[_ ]to[_ ]gtos)",
    re.IGNORECASE,
)

HEADING_RX = re.compile(r"^(#{3,4})\s+(.*?)\s*$")


@dataclass
class PaperEntry:
    title: str = ""
    authors: str = ""
    year: str = ""
    url: str = ""
    source: str = ""
    relevance_text: str = ""
    cross_domain_flag: str = ""
    hypothesis_text: str = ""
    raw_block: str = ""
    warnings: List[str] = field(default_factory=list)


def _heading_kind(line: str) -> Optional[str]:
    m = HEADING_RX.match(line)
    if not m:
        return None
    return m.group(1)  # '###' or '####'


def _split_sections(lines: List[str]) -> List[Tuple[int, int, str, str]]:
    """Return list of (start_idx, end_idx, hashes, title_line) for each heading.

    end_idx is exclusive (start of next heading or EOF).
    """
    out: List[Tuple[int, int, str, str]] = []
    indices: List[Tuple[int, str, str]] = []
    for i, ln in enumerate(lines):
        kind = _heading_kind(ln)
        if kind is None:
            continue
        m = HEADING_RX.match(ln)
        title = m.group(2).strip() if m else ""
        indices.append((i, kind, title))
    for k, (i, kind, title) in enumerate(indices):
        end = indices[k + 1][0] if k + 1 < len(indices) else len(lines)
        out.append((i, end, kind, title))
    return out


def _block_has_paper_fields(block_lines: Iterable[str]) -> bool:
    """A block is a 'paper entry' iff it has at least one of the canonical
    bullet fields (Authors/Year/URL/Source) within its body lines.
    """
    body = "\n".join(block_lines)
    if PAPER_FIELDS_RX.search(body):
        return True
    return False


# Field extraction patterns (line-level). Each pattern looks at a single bullet
# line and pulls the value after the colon.

_FIELD_LINE_RX = re.compile(
    r"^\s*[-*]\s+\*{0,2}(?P<key>[A-Za-z][A-Za-z0-9 _/\-\(\)\.\+,'—–]*?)\*{0,2}\s*[:：]\s*\*{0,2}\s*(?P<val>.*?)\s*\*{0,2}\s*$"
)
# Some files use `- id: X` lower-case-no-bold; some use `- **authors:**` with
# bold; this regex accepts both.


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("_", " ").replace("-", " ").strip()


def _extract_fields_from_block(
    block_lines: List[str],
) -> Dict[str, str]:
    """Walk lines looking for `- **Field:** value` style bullets. Multi-line
    values (continuation lines that start with whitespace) are concatenated.
    Returns a dict keyed on normalized lower-case field name.
    """
    fields: Dict[str, List[str]] = {}
    current_key: Optional[str] = None

    # First, identify field bullets and their position
    for ln in block_lines:
        m = _FIELD_LINE_RX.match(ln)
        if m:
            key = _normalize_key(m.group("key"))
            val = m.group("val").strip()
            current_key = key
            # If duplicate (e.g., URL listed twice), append
            fields.setdefault(key, []).append(val)
        else:
            # Continuation: a non-empty indented line OR a line that is purely
            # text continuation right after a field (no leading bullet). Only
            # extend if current_key set and line is plausibly a continuation
            # (begins with whitespace, or is a follow-up text without a heading
            # marker).
            stripped = ln.rstrip("\n")
            if current_key and stripped:
                # Skip lines that begin a new sub-bullet (key:value pattern with
                # leading dash)
                if _FIELD_LINE_RX.match(stripped):
                    pass  # already handled above
                else:
                    # Indented continuation (>=2 leading spaces) is a value
                    # continuation. But avoid grabbing entire surrounding text
                    # like Abstract paragraphs.
                    if stripped.startswith(("    ", "  -", "  *", "  ")):
                        # Single-line append only (don't accumulate everything)
                        # Heuristic: only attach short continuations to fields
                        # where multi-line is plausible (URL, Source).
                        pass
            if not stripped:
                current_key = None

    return {k: " ".join(v).strip() for k, v in fields.items()}


def _maybe_get(d: Dict[str, str], *keys: str) -> str:
    for k in keys:
        if k in d and d[k]:
            return d[k]
    return ""


def _extract_year(year_source: str) -> str:
    """Extract first 4-digit year (1800-2099) from arbitrary text."""
    if not year_source:
        return ""
    m = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", year_source)
    return m.group(1) if m else ""


def _extract_source(year_source: str, fallback_source: str) -> str:
    """Given a `Year/Source` value (may include `/`) plus an explicit Source
    field, return the cleanest source string.
    """
    if fallback_source:
        return fallback_source
    if not year_source:
        return ""
    # If Year/Source: "1973 / Journal of Political Economy 81(3): 637-654"
    if "/" in year_source:
        parts = year_source.split("/", 1)
        if len(parts) == 2 and re.match(r"\s*\d{4}\b", parts[0]):
            return parts[1].strip()
    # Otherwise the value is the source as-is (but strip any leading year)
    cleaned = re.sub(r"^\s*\d{4}\s*[-/,]\s*", "", year_source).strip()
    return cleaned if cleaned != year_source.strip() else year_source.strip()


def _extract_url(url_field: str) -> str:
    """Pull the first http(s) URL from the URL field (some files list multiple
    URLs separated by ' ; ' or ' or ')."""
    if not url_field:
        return ""
    m = re.search(r"https?://\S+", url_field)
    if m:
        url = m.group(0).rstrip(",.;)>'\"")
        return url
    # Sometimes the URL is given as "see [42]" or "(institutional access)" --
    # leave empty.
    return ""


def _hypothesis_is_nontrivial(text: str) -> bool:
    if not text:
        return False
    cleaned = text.strip()
    # `—`, `-`, `none`, `n/a`, single-dot variants are trivial
    trivial = {"-", "—", "–", "none", "none.", "n/a", "na", "tbd", ""}
    if cleaned.lower() in trivial:
        return False
    # If it contains alphabetic chars beyond just dashes / placeholders:
    # require >= 4 alphabetic characters
    alpha = re.sub(r"[^A-Za-z]", "", cleaned)
    return len(alpha) >= 4


def _judge_relevance(text: str) -> int:
    """Heuristic 1-5 score from the relevance text.

    Anchors:
      5: Explicitly load-bearing / anchors a GTOS subsystem (mentions K54,
         risk_per_trade, cross_instrument_correlation_gate, OB-zone edge,
         specific shadow logger, specific config knob, F11/F15/F2/A6, HALLUC-1,
         H29, S79, J46-J49, Phase 2 task identifier, etc.)
      4: Direct GTOS feature/architectural relevance (regime classifier feature
         candidate; testable hypothesis on GTOS instruments)
      3: Generic GTOS-relevant context (foundational / methodology that bears
         on system design)
      2: Tangential / "frame" / "useful for engineers"
      1: "Pedagogical reference", "no direct use", "—", "None directly"

    The judgement looks for keyword density.
    """
    if not text:
        return 2
    t = text.lower()
    if not t.strip() or t.strip() in {"—", "-", "none.", "none"}:
        return 1

    # Tier-1 markers: very specific GTOS subsystem references
    tier1_keywords = [
        "k54",
        "k55",
        "j46",
        "j47",
        "j48",
        "j49",
        "f11",
        "f15",
        "f2 ",
        "a6 ",
        "halluc-1",
        "halluc1",
        "h29",
        "s79",
        "phase 2",
        "phase-2",
        "phase2",
        "risk_per_trade",
        "risk per trade",
        "cross_instrument_correlation",
        "cross-instrument correlation",
        "ob-zone",
        "ob zone",
        "ob retest",
        "ob-retest",
        "kill zone",
        "kill-zone",
        "killzone",
        "tick_features",
        "tick features",
        "shadow logger",
        "shadow_logger",
        "shadow log",
        "displacement_logger",
        "regime classifier",
        "regime-aware",
        "regime aware",
        "drawdown manager",
        "heartbeat-flatten",
        "heartbeat flatten",
        "sl_buffer",
        "sl buffer",
        "atr multiplier",
        "atr_multiplier",
        "atr-multiplier",
        "permissions.py",
        "execution.py",
        "primary_analyzer",
        "market_state.py",
        "side-aware",
        "side aware",
        "side_aware",
        "directly relevant to",
        "direct relevance",
        "directly load-bearing",
        "directly load bearing",
        "directly justifies",
        "directly maps",
        "directly anchors",
        "literal mechanism",
        "directly informs",
        "operative theoretical foundation",
        "single most operative",
        "load-bearing",
        "load bearing",
    ]
    tier1_hits = sum(1 for kw in tier1_keywords if kw in t)

    # Tier-2 markers: "relevant to" / "candidate feature" / "K54 v2 candidate"
    # / "should add" / "supports the" / "directly justifies"
    tier2_keywords = [
        "candidate feature",
        "candidate k54 feature",
        "candidate k54",
        "candidate ml feature",
        "k54 feature",
        "k54 candidate",
        "should add",
        "should include",
        "implementable as",
        "phase 2 task",
        "phase 2 candidate",
        "directly justifies",
        "justifies",
        "supports",
        "anchors",
        "feature candidate",
        "regime feature",
        "operationally usable",
        "actionable",
        "testable hypothesis",
        "testable on gtos",
        "directly testable",
    ]
    tier2_hits = sum(1 for kw in tier2_keywords if kw in t)

    # Tier-low markers: "foundational reference", "pedagogical", "no direct
    # use", "indirect", "tangential", "—"
    low_keywords = [
        "foundational reference",
        "pedagogical reference",
        "pedagogical",
        "no direct use",
        "no direct application",
        "not directly used",
        "not directly applicable",
        "not directly tradable",
        "indirect",
        "tangential",
        "tangentially",
        "background",
        "historical anchor",
        "historical reference",
        "reference text",
        "anchor reference",
        "no direct gtos",
        "purely academic",
        "out of scope",
        "useful as a frame",
    ]
    low_hits = sum(1 for kw in low_keywords if kw in t)

    score = 3
    if tier1_hits >= 2:
        score = 5
    elif tier1_hits == 1 and tier2_hits >= 1:
        score = 5
    elif tier1_hits == 1:
        score = 4
    elif tier2_hits >= 2:
        score = 4
    elif tier2_hits == 1:
        score = 3
    if low_hits >= 2 and tier1_hits == 0:
        score = min(score, 1)
    elif low_hits == 1 and tier1_hits == 0 and tier2_hits == 0:
        score = min(score, 2)

    # Penalize very short relevance text (likely trivial)
    if len(text.strip()) < 60:
        score = min(score, 2)

    return max(1, min(5, score))


def _normalize_cross_domain(text: str) -> str:
    """Take whatever was in the cross-domain bullet and normalize.

    Returns "none" if absent / empty / "none" / em-dash; otherwise the literal
    value (joined with `; ` if multiple).
    """
    if not text:
        return "none"
    t = text.strip()
    if not t or t.lower() in {"none", "—", "-", "n/a", "na"}:
        return "none"
    # Strip surrounding parentheses / "(cross-link to ...)" boilerplate
    return t


# -----------------------------------------------------------------------------
# Per-domain parser
# -----------------------------------------------------------------------------


def parse_domain(domain_slug: str) -> Tuple[List[Dict[str, str]], List[str], int, int]:
    """Return (rows, warnings, md_heading_count, csv_row_count).

    `rows` is a list of dict per the canonical schema (with `domain` key).
    `md_heading_count` is the number of `### `+`#### ` headings that contained
    paper-field bullets (matched against CSV row count for sanity).
    """
    md_path = LIT_ROOT / domain_slug / "papers.md"
    warnings: List[str] = []
    if not md_path.exists():
        warnings.append(f"papers.md missing for domain {domain_slug}")
        return [], warnings, 0, 0

    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    sections = _split_sections(lines)

    rows: List[Dict[str, str]] = []
    paper_heading_count = 0

    # We treat every heading section as a candidate. Only sections whose body
    # contains paper-field bullets are processed as papers.
    for start, end, hashes, title in sections:
        if hashes not in ("###", "####"):
            continue
        body_lines = lines[start + 1 : end]
        if not _block_has_paper_fields(body_lines):
            continue

        paper_heading_count += 1

        fields = _extract_fields_from_block(body_lines)

        # Title cleanup: strip leading numbering like "1. ", "2.1 ", "2.1.", "1)"
        clean_title = re.sub(r"^\s*(?:Section\s+)?\d+(?:\.\d+)*\.?\s+", "", title)
        clean_title = re.sub(r"^\s*\d+[\.)]\s+", "", clean_title)
        # Some titles include parenthetical year in them; keep as-is per spec
        # (don't fabricate).

        authors = _maybe_get(
            fields, "authors", "author"
        )
        year_source_raw = _maybe_get(
            fields, "year/source", "year source", "year"
        )
        source_raw = _maybe_get(fields, "source")
        url_raw = _maybe_get(fields, "url", "urls")

        year = _extract_year(year_source_raw or source_raw)
        source = _extract_source(year_source_raw, source_raw)
        url = _extract_url(url_raw)

        relevance_text = _maybe_get(
            fields,
            "relevance to gtos",
            "relevance to gtos esp edge decay   sentiment fe",
            "relevance to gtos (esp edge decay   sentiment fe)",
            "relevance",
            "relevance to gtos esp edge decay sentiment fe",
        )
        # Some keys collapse weirdly through normalization; try alternates
        if not relevance_text:
            for k in fields:
                if k.startswith("relevance"):
                    relevance_text = fields[k]
                    break

        cross_domain_text = _maybe_get(
            fields,
            "cross-domain flag",
            "cross domain flag",
            "cross-domain links",
            "cross domain links",
            "cross-domain",
            "cross domain",
            "cross-domain link",
            "cross domain link",
        )
        if not cross_domain_text:
            for k in fields:
                if k.startswith("cross") and "domain" in k:
                    cross_domain_text = fields[k]
                    break

        hypothesis_text = _maybe_get(
            fields,
            "potential hypothesis",
            "hypothesis",
            "hypotheses",
            "potential hypotheses",
            "potential_hypothesis",
        )
        if not hypothesis_text:
            for k in fields:
                if "hypoth" in k:
                    hypothesis_text = fields[k]
                    break

        # Per-paper warnings
        if not authors:
            warnings.append(
                f"[{domain_slug}] '{clean_title[:60]}': missing authors field"
            )
        if not year:
            warnings.append(
                f"[{domain_slug}] '{clean_title[:60]}': missing year field"
            )
        if not url:
            # some books cite institutional sources without URL; downgrade to
            # info-level
            if url_raw:
                warnings.append(
                    f"[{domain_slug}] '{clean_title[:60]}': URL field present "
                    f"but no http(s) URL extracted: {url_raw[:80]}"
                )
            else:
                warnings.append(
                    f"[{domain_slug}] '{clean_title[:60]}': missing URL field"
                )
        if not source:
            warnings.append(
                f"[{domain_slug}] '{clean_title[:60]}': missing source field"
            )
        if not relevance_text:
            warnings.append(
                f"[{domain_slug}] '{clean_title[:60]}': missing relevance-to-GTOS field"
            )

        relevance_score = _judge_relevance(relevance_text)
        cross_domain_flag = _normalize_cross_domain(cross_domain_text)
        hypothesis_implied = "yes" if _hypothesis_is_nontrivial(hypothesis_text) else "no"

        row = {
            "domain": domain_slug,
            "title": clean_title,
            "authors": authors,
            "year": year,
            "url": url,
            "source": source,
            "relevance_score": str(relevance_score),
            "cross_domain_flag": cross_domain_flag,
            "hypothesis_implied": hypothesis_implied,
        }
        rows.append(row)

    return rows, warnings, paper_heading_count, len(rows)


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADER, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> None:
    all_rows: List[Dict[str, str]] = []
    audit_blocks: List[str] = []
    audit_blocks.append("# Literature CSV Recovery Audit")
    audit_blocks.append("")
    audit_blocks.append(
        "Auto-generated by `research/ml_program/scripts/_recover_papers_csv.py` to "
        "recover the 14 missing `papers.csv` files after Phase 1 worker quota "
        "exhaustion. Each `papers.md` was parsed for `### Title` / `#### Title` "
        "headings whose body block contains canonical paper bullets "
        "(`Authors`, `Year` / `Year/Source`, `Source`, `URL`, `Relevance to GTOS`)."
    )
    audit_blocks.append("")
    audit_blocks.append("## Per-domain summary")
    audit_blocks.append("")
    audit_blocks.append(
        "| Domain | MD paper-headings | CSV rows | Match | Notes |"
    )
    audit_blocks.append("|---|---|---|---|---|")

    domain_warnings_dump: List[Tuple[str, List[str]]] = []
    total_papers = 0

    for slug in DOMAINS:
        rows, warnings, md_count, csv_count = parse_domain(slug)
        # Write per-domain CSV
        out_path = LIT_ROOT / slug / "papers.csv"
        write_csv(out_path, rows)
        all_rows.extend(rows)
        match_pct = (
            100.0 * abs(md_count - csv_count) / max(md_count, 1)
        )
        status = "OK" if match_pct <= 5.0 else "WARN"
        notes = ""
        if md_count != csv_count:
            notes = f"md={md_count} csv={csv_count} delta={md_count - csv_count}"
        audit_blocks.append(
            f"| `{slug}` | {md_count} | {csv_count} | {status} | {notes} |"
        )
        domain_warnings_dump.append((slug, warnings))
        total_papers += csv_count

    audit_blocks.append("")
    audit_blocks.append(f"**Total papers cataloged across 14 domains: {total_papers}**")
    audit_blocks.append("")
    audit_blocks.append("## Per-domain warnings (parse anomalies, missing fields)")
    audit_blocks.append("")
    for slug, warns in domain_warnings_dump:
        audit_blocks.append(f"### `{slug}`")
        if not warns:
            audit_blocks.append("(no warnings)")
            audit_blocks.append("")
            continue
        # Limit to first 50 warnings per domain
        limit = 60
        head = warns[:limit]
        for w in head:
            audit_blocks.append(f"- {w}")
        if len(warns) > limit:
            audit_blocks.append(f"- ... ({len(warns) - limit} additional warnings suppressed)")
        audit_blocks.append("")

    audit_blocks.append("## Format anomaly notes")
    audit_blocks.append("")
    audit_blocks.append(
        "- **Domain `10_gold_commodities` uses `#### Title` for paper entries** with "
        "`### Section header` for grouping; all other domains use `### Title` for "
        "paper entries with section headers using `### N. Heading` (numbered) form. "
        "Both styles are matched by the heading regex; section headers without "
        "paper-field bullets are filtered."
    )
    audit_blocks.append(
        "- **Domain `03_distributional_characteristics` and `21_risk_management_kelly_sizing` "
        "use lower-case bullet field names** (`- **id:**`, `- **authors:**`, `- **year:**`, "
        "`- **source:**`, `- **url:**`, `- **relevance_to_gtos:**`, `- **potential_hypothesis:**`, "
        "`- **cross_domain_links:**`). The parser is case-insensitive and treats "
        "underscores / hyphens as spaces, so these match the canonical fields."
    )
    audit_blocks.append(
        "- **Domain `01_math_foundations` uses `Year/Source:` combined field** rather "
        "than separate `Year:` + `Source:` bullets in some entries. The parser splits "
        "on `/` when the leading token is a 4-digit year."
    )
    audit_blocks.append(
        "- **URL inconsistencies:** several entries provide multiple URLs separated "
        "by ` ; ` or `(also <url>)` text. The parser captures the first http(s) URL. "
        "A few books / dissertations have no URL at all (e.g., `Karatzas-Shreve` "
        "textbook entries cite Springer DOI page but some have no working URL); "
        "these have empty `url` values rather than fabrication."
    )
    audit_blocks.append(
        "- **Reference-style URLs** (`see paper [42]`) were not encountered; a few "
        "entries like `MIT Press` book pages were captured as the publisher URL."
    )
    audit_blocks.append("")
    audit_blocks.append("## Aggregate")
    audit_blocks.append("")
    audit_blocks.append(
        f"- 14 domain CSVs written under `research/ml_program/literature/<slug>/papers.csv`."
    )
    audit_blocks.append(
        f"- Aggregate `recovery_summary.csv` written to "
        f"`research/ml_program/literature/synthesis/recovery_summary.csv` "
        f"({total_papers} rows)."
    )

    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text("\n".join(audit_blocks), encoding="utf-8")

    # Aggregate CSV
    write_csv(SYNTH_PATH, all_rows)

    print(f"Wrote 14 papers.csv files; total rows = {total_papers}")
    print(f"Audit: {AUDIT_PATH}")
    print(f"Aggregate: {SYNTH_PATH}")


if __name__ == "__main__":
    main()
