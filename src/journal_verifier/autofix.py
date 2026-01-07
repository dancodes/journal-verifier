"""Autofix implementations for supported problems."""

from __future__ import annotations

from .constants import (
    DAY_HEADER_RE,
    EXPECTED_INDEX,
    EXPECTED_LEVEL,
    HEADING_RE,
    SECTION_TEMPLATES,
)
from .fix_models import FixContext, FixResult
from .problems import Problem


def _entry_end_index(lines: list[str], start_idx: int) -> int:
    for idx in range(start_idx + 1, len(lines)):
        if DAY_HEADER_RE.match(lines[idx]):
            return idx
    return len(lines)


def _section_exists(block: list[str], title: str) -> bool:
    for line in block:
        match = HEADING_RE.match(line)
        if match and match.group(2).strip() == title:
            return True
    return False


def _content_end(block: list[str]) -> int:
    for idx, line in enumerate(block):
        if line.strip() == "---":
            return idx
    return len(block)


def _insert_index(block: list[str], title: str) -> int:
    content_end = _content_end(block)
    target_index = EXPECTED_INDEX[title]
    for idx, line in enumerate(block[:content_end]):
        match = HEADING_RE.match(line)
        if not match:
            continue
        heading_title = match.group(2).strip()
        if heading_title not in EXPECTED_INDEX:
            continue
        if EXPECTED_INDEX[heading_title] > target_index:
            return idx
    return content_end


def _adjust_for_leading_blanks(block: list[str], insert_at: int) -> int:
    if insert_at != 0:
        return insert_at
    while insert_at < len(block) and block[insert_at].strip() == "":
        insert_at += 1
    return insert_at


def _needs_blank_before(block: list[str], insert_at: int) -> bool:
    if insert_at == 0:
        return False
    return block[insert_at - 1].strip() != ""


def _needs_blank_after(block: list[str], insert_at: int) -> bool:
    if insert_at >= len(block):
        return False
    return block[insert_at].strip() != ""


def _section_lines(block: list[str], insert_at: int, title: str) -> list[str]:
    heading = f"{EXPECTED_LEVEL[title]} {title}"
    lines = []
    if _needs_blank_before(block, insert_at):
        lines.append("")
    lines.append(heading)
    lines.extend(SECTION_TEMPLATES.get(title, []))
    if _needs_blank_after(block, insert_at):
        lines.append("")
    return lines


def fix_missing_section(context: FixContext, problem: Problem) -> FixResult:
    title = problem.context.get("section_title")
    if not title or title not in EXPECTED_INDEX:
        return FixResult(problem, False, "missing section title metadata")
    if problem.line_no is None:
        return FixResult(problem, False, "missing entry line number")

    start_idx = problem.line_no - 1
    if start_idx < 0 or start_idx >= len(context.lines):
        return FixResult(problem, False, "entry header line out of range")

    end_idx = _entry_end_index(context.lines, start_idx)
    block = context.lines[start_idx + 1 : end_idx]
    if _section_exists(block, title):
        return FixResult(problem, False, "section already present")

    insert_at = _insert_index(block, title)
    insert_at = _adjust_for_leading_blanks(block, insert_at)
    block[insert_at:insert_at] = _section_lines(block, insert_at, title)
    context.lines[start_idx + 1 : end_idx] = block
    return FixResult(problem, True, f"inserted '{title}' section")
