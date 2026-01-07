"""Autofix implementations for supported problems."""

from __future__ import annotations

from datetime import date

from .constants import (
    DAY_HEADER_RE,
    EXPECTED_INDEX,
    EXPECTED_LEVEL,
    EXPECTED_SECTIONS,
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


def _entry_header_line(day: date) -> str:
    weekday = day.strftime("%A")
    return f"## {day.isoformat()} ({weekday})"


def _entry_template_lines(day: date) -> list[str]:
    lines = [_entry_header_line(day), ""]
    for level, title in EXPECTED_SECTIONS:
        lines.append(f"{level} {title}")
        lines.extend(SECTION_TEMPLATES.get(title, []))
        lines.append("")
    lines.append("---")
    return lines


def _insert_entry_lines(lines: list[str], insert_at: int, entry_lines: list[str]) -> None:
    before = insert_at > 0 and lines[insert_at - 1].strip() != ""
    after = insert_at < len(lines) and lines[insert_at].strip() != ""
    payload = list(entry_lines)
    if before:
        payload.insert(0, "")
    if after:
        payload.append("")
    lines[insert_at:insert_at] = payload


def _extract_entry_dates(lines: list[str]) -> list[tuple[int, date]]:
    entries: list[tuple[int, date]] = []
    for idx, line in enumerate(lines):
        match = DAY_HEADER_RE.match(line)
        if not match:
            continue
        try:
            entries.append((idx, date.fromisoformat(match.group(1))))
        except ValueError:
            continue
    return entries


def _insert_index_for_date(lines: list[str], day: date) -> int:
    entries = _extract_entry_dates(lines)
    if not entries:
        return len(lines)
    entries.sort(key=lambda item: item[1])
    for idx, entry_date in entries:
        if day < entry_date:
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


def fix_missing_date(context: FixContext, problem: Problem) -> FixResult:
    date_str = problem.context.get("date")
    if not date_str:
        return FixResult(problem, False, "missing date metadata")
    try:
        day = date.fromisoformat(date_str)
    except ValueError:
        return FixResult(problem, False, f"invalid date '{date_str}'")
    insert_at = _insert_index_for_date(context.lines, day)
    entry_lines = _entry_template_lines(day)
    _insert_entry_lines(context.lines, insert_at, entry_lines)
    return FixResult(problem, True, f"inserted day {date_str}")
