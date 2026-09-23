"""Parse quantlabsnet.com blog sitemap XML into a tagged URL manifest.

Reads a sitemap XML file and emits a pipe-delimited URL manifest with
relevance tags applied via URL-slug keyword matching (title/body are NOT
fetched — extraction agents do that later).

Tags:
  SKIP     — hard-skip categories (matlab, crypto/bitcoin/ethereum, polymarket)
  JOBS     — careers/salaries/interviews content (low priority; kept but deprioritized)
  OPTIONS  — options-focused content; CEO wants this skipped unless
             it's an instruments-general "futures-options" article
  KEEP     — default (AI/trading/bot/code/strategy/HFT/microstructure/macro)
  PRIORITY — high-signal slug keywords: mt5, metatrader, ibkr, forex, fx,
             gold, xau, eurusd, usdjpy, gbpjpy, gbpusd, nas100, nasdaq, us30,
             claude, prop-firm, ftmo, backtest-engine (live relevance for GTOS)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

# URL substring sets (matched case-insensitively against slug after /post/)
HARD_SKIP = {
    "matlab",
    "crypto",
    "bitcoin",
    "ethereum",
    "-btc-",
    "btc-",
    "eth-",
    "-eth-",
    "polymarket",
    "stablecoin",
    "tether",
    "usdt",
    "altcoin",
    "dogecoin",
    "xrp",
}
JOBS = {
    "quant-job",
    "quant-jobs",
    "salary",
    "salaries",
    "intern",
    "recruitment",
    "compensation",
    "career",
    "careers",
    "jane-st",
    "citadel-job",
    "goldman-sachs-careers",
    "de-shaw-careers",
    "hudson-river-trading",
    "jane-street-insight",
    "citadel-jobs",
    "point72-careers",
    "renaissance-tech",
    "hedge-fund-jobs",
    "hsbc-goldman-sachs",
    "steven-cohen",
    "ken-griffin",
    "hrt",
}
OPTIONS_ONLY = {
    "options-trading",
    "option-trading",
    "option-volatility",
    "option-pricing",
    "options-chain",
    "option-chain",
    "options-contracts",
    "vix-call",
    "options-arbitrage",
}
# These override OPTIONS_ONLY (keep because futures/general trading)
OPTIONS_OVERRIDE = {
    "futures-options",
    "futures-and-options",
    "options-and-futures",
}
PRIORITY = {
    "mt5",
    "metatrader",
    "ibkr",
    "interactive-brokers",
    "forex",
    "-fx-",
    "fx-",
    "eurusd",
    "usdjpy",
    "gbpjpy",
    "gbpusd",
    "-gold",
    "gold-",
    "xau",
    "nas100",
    "nasdaq",
    "us30",
    "dxy",
    "claude",
    "anthropic",
    "prop-firm",
    "ftmo",
    "institutional-trading",
    "order-flow",
    "orderbook",
    "order-book",
    "microstructure",
    "liquidity",
    "backtest",
    "hidden-markov",
    "avellaneda",
    "ict-trading",
}


def slug_of(url: str) -> str:
    m = re.search(r"/post/([^?#]+)", url)
    return (m.group(1) if m else url).lower()


def any_in(needles: set[str], hay: str) -> bool:
    return any(n in hay for n in needles)


def tag_url(url: str) -> str:
    s = slug_of(url)
    if any_in(HARD_SKIP, s):
        return "SKIP"
    if any_in(JOBS, s):
        return "JOBS"
    # OPTIONS check with override
    if any_in(OPTIONS_ONLY, s) and not any_in(OPTIONS_OVERRIDE, s):
        return "OPTIONS"
    if any_in(PRIORITY, s):
        return "PRIORITY"
    return "KEEP"


def parse_sitemap(xml_path: Path) -> list[tuple[str, str]]:
    """Return list of (url, lastmod) pairs."""
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    tree = ET.parse(xml_path)
    root = tree.getroot()
    out: list[tuple[str, str]] = []
    for url_el in root.findall("s:url", ns):
        loc_el = url_el.find("s:loc", ns)
        mod_el = url_el.find("s:lastmod", ns)
        if loc_el is None or loc_el.text is None:
            continue
        lastmod = (mod_el.text or "") if mod_el is not None else ""
        # Trim YYYY-MM-DD from timestamp if present
        lastmod = lastmod[:10]
        out.append((loc_el.text.strip(), lastmod))
    return out


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: build_blog_manifest.py <sitemap.xml> <out.txt>", file=sys.stderr)
        return 2
    sitemap_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    entries = parse_sitemap(sitemap_path)
    # Dedup by URL, keep first occurrence
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for url, mod in entries:
        if url in seen:
            continue
        seen.add(url)
        unique.append((url, mod))

    # Tag each
    tagged = [(url, mod, tag_url(url)) for url, mod in unique]
    # Sort by lastmod DESC (newest first) for extraction priority
    tagged.sort(key=lambda r: r[1], reverse=True)

    counts: dict[str, int] = {}
    for _, _, t in tagged:
        counts[t] = counts.get(t, 0) + 1

    with out_path.open("w", encoding="utf-8") as f:
        f.write("# URL | LASTMOD | TAG\n")
        f.write(f"# Total: {len(tagged)} | ")
        f.write(" | ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        f.write("\n")
        for url, mod, tag in tagged:
            f.write(f"{url} | {mod} | {tag}\n")

    print(f"Wrote {len(tagged)} entries to {out_path}")
    print("Tag counts:", counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
