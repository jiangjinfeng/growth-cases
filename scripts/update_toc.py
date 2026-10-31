#!/usr/bin/env python3
"""Rebuild the table of contents and README index from 增长案例集.md."""

import re
from datetime import date
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "增长案例集.md"
README = ROOT / "README.md"

# Sections that are part of the file but are not case entries.
EXCLUDE = {"待补充", "新增案例模板", "来源"}


def github_slug(text: str) -> str:
    """Approximate GitHub's heading slug for Chinese + Latin headings."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s\u4e00-\u9fff-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s", "-", text)
    return text


def display_label(heading: str) -> str:
    """Drop the leading section number from a heading for TOC/README labels."""
    return re.sub(r"^\d+\.\s*", "", heading)


def headings(md: str) -> list[str]:
    result = []
    in_fence = False
    for line in md.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and line.startswith("## "):
            heading = line[3:].strip()
            if heading and heading != "目录":
                result.append(heading)
    return result


def is_case(heading: str) -> bool:
    match = re.match(r"^\d+\.\s*(.+)$", heading)
    return bool(match) and match.group(1) not in EXCLUDE


def existing_labels(md: str) -> dict[str, str]:
    block = md.split("## 目录", 1)[1].split("\n---", 1)[0]
    return {
        unquote(href): label
        for label, href in re.findall(r"\[([^\]]+)\]\(#([^)]+)\)", block)
    }


def replace_toc(md: str, headings_list: list[str], labels: dict[str, str]) -> str:
    start = md.index("## 目录")
    end = md.index("\n---", start)
    lines = []
    for index, heading in enumerate(headings_list, 1):
        anchor = github_slug(heading)
        lines.append(f"{index}. [{labels.get(anchor, display_label(heading))}](#{anchor})")
    toc = "## 目录\n\n" + "\n".join(lines) + "\n"
    return md[:start] + toc + md[end:]


def replace_readme_index(readme: str, headings_list: list[str], labels: dict[str, str]) -> str:
    cases = [heading for heading in headings_list if is_case(heading)]
    start = readme.index("## 已收录")
    end = readme.index("## 说明", start)
    lines = []
    for index, heading in enumerate(cases, 1):
        anchor = github_slug(heading)
        lines.append(f"{index}. {labels.get(anchor, display_label(heading))}")
    block = "## 已收录\n\n" + "\n".join(lines) + "\n\n"
    return readme[:start] + block + readme[end:]


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    headings_list = headings(md)
    labels = existing_labels(md)

    md = replace_toc(md, headings_list, labels)
    md = re.sub(
        r"^> 更新：\d{4}-\d{2}-\d{2}$",
        f"> 更新：{date.today().isoformat()}",
        md,
        flags=re.M,
    )
    MD.write_text(md, encoding="utf-8")

    readme = README.read_text(encoding="utf-8")
    readme = replace_readme_index(readme, headings_list, labels)
    readme = re.sub(
        r"^更新：\d{4}-\d{2}-\d{2}$",
        f"更新：{date.today().isoformat()}",
        readme,
        flags=re.M,
    )
    README.write_text(readme, encoding="utf-8")

    print(f"Updated {len(headings_list)} TOC entries; {sum(is_case(h) for h in headings_list)} cases in README index.")


if __name__ == "__main__":
    main()
