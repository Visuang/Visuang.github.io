#!/usr/bin/env python3
"""Fetch Google Scholar metrics and update the homepage and CV source safely."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
SCHOLAR_ID = "ePe0rG4AAAAJ"
PROFILE_URL = "https://scholar.google.com/citations?" + urllib.parse.urlencode(
    {"user": SCHOLAR_ID, "hl": "en"}
)


class MetricsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_metric_cell = False
        self.current: list[str] = []
        self.values: list[int] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = dict(attrs).get("class", "") or ""
        if tag == "td" and "gsc_rsb_std" in classes.split():
            self.in_metric_cell = True
            self.current = []

    def handle_data(self, data: str) -> None:
        if self.in_metric_cell:
            self.current.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self.in_metric_cell:
            text = "".join(self.current).strip().replace(",", "")
            if text.isdigit():
                self.values.append(int(text))
            self.in_metric_cell = False


def fetch_metrics() -> tuple[int, int]:
    request = urllib.request.Request(
        PROFILE_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "Chrome/131.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Google Scholar request failed: {exc}") from exc

    if "gsc_rsb_std" not in html or "unusual traffic" in html.lower():
        raise RuntimeError("Google Scholar returned a block, CAPTCHA, or unexpected page")

    parser = MetricsParser()
    parser.feed(html)
    if len(parser.values) < 4:
        raise RuntimeError(f"Could not parse Scholar metrics; found {parser.values!r}")

    # The table is: citations(all, recent), h-index(all, recent), i10-index(...).
    return parser.values[0], parser.values[2]


def replace_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1)
    if count != 1:
        raise RuntimeError(f"Expected one {label} match, found {count}")
    return updated


def update_files(citations: int, h_index: int) -> bool:
    index_path = ROOT / "index.html"
    zh_path = ROOT / "zh.html"
    tex_path = ROOT / "resume_latex_shuangli" / "ShuangLi.tex"
    state_path = ROOT / "data" / "scholar_metrics.json"

    index = index_path.read_text(encoding="utf-8")
    current_match = re.search(
        r"Google Scholar: (\d+) citations · H-index: (\d+)", index
    )
    if not current_match:
        raise RuntimeError("Current metrics were not found in index.html")
    current_citations, current_h = map(int, current_match.groups())

    if citations < current_citations or h_index < current_h:
        raise RuntimeError(
            "Refusing to decrease metrics: "
            f"current={current_citations}/{current_h}, fetched={citations}/{h_index}"
        )
    if citations > 10_000_000 or h_index > 10_000:
        raise RuntimeError("Fetched metrics failed the sanity check")
    if citations == current_citations and h_index == current_h:
        print(f"No change: citations={citations}, h-index={h_index}")
        return False

    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    version = f"{now:%Y%m%d}-citations{citations}"

    index = replace_once(
        index,
        r"Google Scholar: \d+ citations · H-index: \d+",
        f"Google Scholar: {citations} citations · H-index: {h_index}",
        "English metrics",
    )
    index = re.sub(
        r"files/ShuangLi\.pdf\?v=[^\"]+",
        f"files/ShuangLi.pdf?v={version}",
        index,
    )

    zh = zh_path.read_text(encoding="utf-8")
    zh = replace_once(
        zh,
        r"Google Scholar：\d+ 次引用 · H-index：\d+",
        f"Google Scholar：{citations} 次引用 · H-index：{h_index}",
        "Chinese metrics",
    )
    zh = re.sub(
        r"files/ShuangLi\.pdf\?v=[^\"]+",
        f"files/ShuangLi.pdf?v={version}",
        zh,
    )

    tex = tex_path.read_text(encoding="utf-8")
    tex = replace_once(
        tex,
        r"Google Scholar 引用数 = \d+，H 指数 = \d+（截至\d{4}年\d{1,2}月）",
        f"Google Scholar 引用数 = {citations}，H 指数 = {h_index}（截至{now.year}年{now.month}月）",
        "CV metrics",
    )

    index_path.write_text(index, encoding="utf-8")
    zh_path.write_text(zh, encoding="utf-8")
    tex_path.write_text(tex, encoding="utf-8")
    state_path.write_text(
        json.dumps(
            {
                "citations": citations,
                "h_index": h_index,
                "scholar_id": SCHOLAR_ID,
                "updated_at": now.strftime("%Y-%m-%d"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Updated: citations={citations}, h-index={h_index}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--citations", type=int, help="Use a supplied value instead of fetching")
    parser.add_argument("--h-index", type=int, help="Use a supplied value instead of fetching")
    args = parser.parse_args()
    if (args.citations is None) != (args.h_index is None):
        parser.error("--citations and --h-index must be supplied together")

    try:
        metrics = (
            (args.citations, args.h_index)
            if args.citations is not None
            else fetch_metrics()
        )
        update_files(*metrics)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
