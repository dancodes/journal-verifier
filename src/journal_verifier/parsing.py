"""Parsing and section validation for journal entries."""

from __future__ import annotations

from datetime import date

from .constants import (
    BULLET_RE,
    BULLET_REQUIRED,
    DAY_HEADER_RE,
    EXPECTED_INDEX,
    EXPECTED_LEVEL,
    EXPECTED_TITLES,
    HEADING_RE,
    HELPED_RE,
    HURT_RE,
    LONG_TERM_RE,
    SCORE_RE,
    SHORT_TERM_RE,
    VALID_WEEKDAYS,
    WEEKDAY_PREFIX_RE,
)
from .models import Entry, SectionInfo
from .problems import Problem, ProblemCode


def _content_lines(lines: list[str]) -> list[str]:
    return [line for line in lines if line.strip() != "---"]


def _has_bullet(lines: list[str]) -> bool:
    return any(BULLET_RE.match(line) for line in lines)


def _collect_headings(block: list[str]) -> list[tuple[int, str, str]]:
    headings: list[tuple[int, str, str]] = []
    for idx, line in enumerate(block):
        match = HEADING_RE.match(line)
        if match:
            level, title = match.groups()
            headings.append((idx, level, title.strip()))
    return headings


def _validate_headings(
    entry: Entry,
    headings: list[tuple[int, str, str]],
    offset: int,
) -> tuple[set[str], list[tuple[int, str, str]]]:
    seen_titles: set[str] = set()
    expected_pos = 0
    filtered: list[tuple[int, str, str]] = []

    for rel_idx, level, title in headings:
        line_no = offset + rel_idx + 1
        if title not in EXPECTED_LEVEL:
            entry.errors.append((line_no, f"unexpected heading '{title}'"))
            continue
        filtered.append((rel_idx, level, title))
        if level != EXPECTED_LEVEL[title]:
            entry.errors.append((line_no, f"heading '{title}' should be level {EXPECTED_LEVEL[title]}"))
        if title in seen_titles:
            entry.errors.append((line_no, f"duplicate heading '{title}'"))
        seen_titles.add(title)
        section_index = EXPECTED_INDEX[title]
        if section_index < expected_pos:
            entry.errors.append((line_no, f"heading '{title}' is out of order"))
        expected_pos = max(expected_pos, section_index + 1)

    return seen_titles, filtered


def _check_missing_sections(entry: Entry, seen_titles: set[str]) -> None:
    for title in EXPECTED_TITLES:
        if title not in seen_titles:
            entry.problems.append(_missing_section_problem(entry, title))


def _missing_section_problem(entry: Entry, title: str) -> Problem:
    context = {
        "section_title": title,
        "date": entry.date_str,
        "weekday_header": entry.weekday_header,
    }
    return Problem(
        code=ProblemCode.MISSING_SECTION,
        message=f"missing section '{title}'",
        line_no=entry.line_no,
        context=context,
    )


def _record_sections(
    entry: Entry,
    headings: list[tuple[int, str, str]],
    block: list[str],
    offset: int,
) -> None:
    headings.sort(key=lambda item: item[0])
    for idx, (rel_idx, level, title) in enumerate(headings):
        start = rel_idx + 1
        end = headings[idx + 1][0] if idx + 1 < len(headings) else len(block)
        content = block[start:end]
        entry.sections[title] = SectionInfo(
            title=title,
            level=level,
            line_no=offset + rel_idx + 1,
            content_lines=content,
        )


def _validate_looking_forward(entry: Entry, section: SectionInfo, content: list[str]) -> None:
    if not any(SHORT_TERM_RE.match(line) for line in content):
        entry.errors.append((section.line_no, "missing 'Short-term' item in 'What I'm looking forward to'"))
    if not any(LONG_TERM_RE.match(line) for line in content):
        entry.errors.append((section.line_no, "missing 'Long-term' item in 'What I'm looking forward to'"))


def _validate_signals(entry: Entry, section: SectionInfo, content: list[str]) -> None:
    if not any(HELPED_RE.match(line) for line in content):
        entry.errors.append((section.line_no, "missing 'Helped today' item in 'Signals'"))
    if not any(HURT_RE.match(line) for line in content):
        entry.errors.append((section.line_no, "missing 'Hurt today' item in 'Signals'"))


def _validate_score_line(entry: Entry, section: SectionInfo, line: str) -> None:
    match = SCORE_RE.match(line)
    if not match:
        return
    raw_score = match.group(1)
    if raw_score is None:
        return
    try:
        score_val = int(raw_score)
    except ValueError:
        entry.errors.append((section.line_no, "invalid score value in 'Final score (1/5)'"))
        return
    if not 0 <= score_val <= 5:
        entry.errors.append((section.line_no, "score must be between 0 and 5"))


def _validate_score(entry: Entry, section: SectionInfo, content: list[str]) -> None:
    score_lines = [line for line in content if SCORE_RE.match(line)]
    if not score_lines:
        entry.errors.append((section.line_no, "missing score entry in 'Final score (1/5)'"))
        return
    for line in score_lines:
        _validate_score_line(entry, section, line)


def _validate_section_content(entry: Entry) -> None:
    for title, section in entry.sections.items():
        content = _content_lines(section.content_lines)
        if title in BULLET_REQUIRED and not _has_bullet(content):
            entry.errors.append((section.line_no, f"section '{title}' has no list items"))
        if title == "What I'm looking forward to":
            _validate_looking_forward(entry, section, content)
        elif title == "Signals":
            _validate_signals(entry, section, content)
        elif title == "Final score (1/5)":
            _validate_score(entry, section, content)


def _parse_entry_sections(entry: Entry, block: list[str], offset: int) -> None:
    headings = _collect_headings(block)
    seen_titles, filtered = _validate_headings(entry, headings, offset)
    _check_missing_sections(entry, seen_titles)
    _record_sections(entry, filtered, block, offset)
    _validate_section_content(entry)


def _find_headers(lines: list[str]) -> list[tuple[int, str, str]]:
    headers: list[tuple[int, str, str]] = []
    for idx, line in enumerate(lines):
        match = DAY_HEADER_RE.match(line)
        if match:
            headers.append((idx, match.group(1), match.group(2).strip()))
    return headers


def _extract_weekday(weekday_header: str) -> str | None:
    match = WEEKDAY_PREFIX_RE.match(weekday_header.strip())
    if not match:
        return None
    return match.group(1).strip()


def _weekday_debug_details(weekday_header: str) -> str:
    escaped = weekday_header.encode("unicode_escape").decode("ascii")
    codepoints = " ".join(f"U+{ord(ch):04X}" for ch in weekday_header)
    return f"raw={escaped}, len={len(weekday_header)}, codepoints={codepoints}"


def _weekday_error(weekday_header: str, debug_weekday: bool) -> str:
    allowed = "Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday"
    message = (
        f"invalid weekday header '{weekday_header}': "
        f"must start with one of {allowed} (extra text allowed after the weekday)"
    )
    if not debug_weekday:
        return message
    return f"{message} [debug: {_weekday_debug_details(weekday_header)}]"


def _parse_entry_header(entry: Entry, debug_weekday: bool) -> None:
    try:
        entry.date = date.fromisoformat(entry.date_str)
    except ValueError:
        entry.errors.append((entry.line_no, f"invalid date '{entry.date_str}'"))

    weekday_name = _extract_weekday(entry.weekday_header)
    entry.weekday_name = None
    if weekday_name is None:
        entry.errors.append((entry.line_no, _weekday_error(entry.weekday_header, debug_weekday)))
        return

    weekday_key = weekday_name.lower()
    if weekday_key not in VALID_WEEKDAYS:
        entry.errors.append((entry.line_no, _weekday_error(entry.weekday_header, debug_weekday)))
        return
    entry.weekday_name = VALID_WEEKDAYS[weekday_key]


def _build_entry(
    lines: list[str],
    header: tuple[int, str, str],
    end: int,
    debug_weekday: bool,
) -> Entry:
    line_idx, date_str, weekday_header = header
    entry = Entry(
        date=None,
        date_str=date_str,
        weekday_header=weekday_header,
        weekday_name=None,
        line_no=line_idx + 1,
    )
    _parse_entry_header(entry, debug_weekday)
    block = lines[line_idx + 1 : end]
    _parse_entry_sections(entry, block, line_idx + 1)
    return entry


def _build_entries(
    lines: list[str],
    headers: list[tuple[int, str, str]],
    debug_weekday: bool,
) -> list[Entry]:
    entries: list[Entry] = []
    for idx, header in enumerate(headers):
        end = headers[idx + 1][0] if idx + 1 < len(headers) else len(lines)
        entries.append(_build_entry(lines, header, end, debug_weekday))
    return entries


def _duplicate_date_errors(entries: list[Entry]) -> list[tuple[int, str]]:
    seen_dates: dict[date, int] = {}
    errors: list[tuple[int, str]] = []
    for entry in entries:
        if entry.date is None:
            continue
        if entry.date in seen_dates:
            errors.append(
                (
                    entry.line_no,
                    f"duplicate date '{entry.date.isoformat()}' (first at line {seen_dates[entry.date]})",
                )
            )
        else:
            seen_dates[entry.date] = entry.line_no
    return errors


def parse_journal(
    lines: list[str],
    debug_weekday: bool = False,
) -> tuple[list[Entry], list[tuple[int, str]]]:
    headers = _find_headers(lines)
    if not headers:
        return [], [(0, "no day headers found")]
    entries = _build_entries(lines, headers, debug_weekday)
    errors = _duplicate_date_errors(entries)
    return entries, errors
