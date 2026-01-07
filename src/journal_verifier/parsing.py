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


def _has_meaningful_content(lines: list[str]) -> bool:
    for line in lines:
        if not line.strip():
            continue
        match = BULLET_RE.match(line)
        if match:
            if match.group(1).strip():
                return True
            continue
        return True
    return False


def _entry_has_main_content(entry: Entry) -> bool:
    section = entry.sections.get("What happened today")
    if not section:
        return False
    content = _content_lines(section.content_lines)
    return _has_meaningful_content(content)


def _add_problem(
    entry: Entry,
    code: str,
    message: str,
    line_no: int | None,
    context: dict[str, str] | None = None,
) -> None:
    entry.problems.append(
        Problem(
            code=code,
            message=message,
            line_no=line_no,
            context=context or {},
        )
    )


def _collect_headings(block: list[str]) -> list[tuple[int, str, str]]:
    headings: list[tuple[int, str, str]] = []
    for idx, line in enumerate(block):
        match = HEADING_RE.match(line)
        if match:
            level, title = match.groups()
            headings.append((idx, level, title.strip()))
    return headings


def _unexpected_heading_problem(entry: Entry, title: str, line_no: int) -> None:
    _add_problem(
        entry,
        ProblemCode.UNEXPECTED_HEADING,
        f"unexpected heading '{title}'",
        line_no,
        {"heading_title": title},
    )


def _heading_level_problem(entry: Entry, title: str, expected: str, found: str, line_no: int) -> None:
    _add_problem(
        entry,
        ProblemCode.HEADING_LEVEL,
        f"heading '{title}' should be level {expected}",
        line_no,
        {
            "heading_title": title,
            "expected_level": expected,
            "found_level": found,
        },
    )


def _duplicate_heading_problem(entry: Entry, title: str, line_no: int) -> None:
    _add_problem(
        entry,
        ProblemCode.DUPLICATE_HEADING,
        f"duplicate heading '{title}'",
        line_no,
        {"heading_title": title},
    )


def _heading_order_problem(entry: Entry, title: str, line_no: int) -> None:
    _add_problem(
        entry,
        ProblemCode.HEADING_ORDER,
        f"heading '{title}' is out of order",
        line_no,
        {"heading_title": title},
    )


def _process_heading(
    entry: Entry,
    rel_idx: int,
    level: str,
    title: str,
    offset: int,
    seen_titles: set[str],
    expected_pos: int,
) -> tuple[bool, int]:
    line_no = offset + rel_idx + 1
    if title not in EXPECTED_LEVEL:
        _unexpected_heading_problem(entry, title, line_no)
        return False, expected_pos

    expected_level = EXPECTED_LEVEL[title]
    if level != expected_level:
        _heading_level_problem(entry, title, expected_level, level, line_no)

    if title in seen_titles:
        _duplicate_heading_problem(entry, title, line_no)

    seen_titles.add(title)
    section_index = EXPECTED_INDEX[title]
    if section_index < expected_pos:
        _heading_order_problem(entry, title, line_no)
    next_expected = max(expected_pos, section_index + 1)
    return True, next_expected


def _validate_headings(
    entry: Entry,
    headings: list[tuple[int, str, str]],
    offset: int,
) -> tuple[set[str], list[tuple[int, str, str]]]:
    seen_titles: set[str] = set()
    expected_pos = 0
    filtered: list[tuple[int, str, str]] = []

    for rel_idx, level, title in headings:
        is_expected, expected_pos = _process_heading(
            entry,
            rel_idx,
            level,
            title,
            offset,
            seen_titles,
            expected_pos,
        )
        if is_expected:
            filtered.append((rel_idx, level, title))

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
        _add_problem(
            entry,
            ProblemCode.MISSING_SHORT_TERM,
            "missing 'Short-term' item in 'What I'm looking forward to'",
            section.line_no,
            {"section_title": section.title},
        )
    if not any(LONG_TERM_RE.match(line) for line in content):
        _add_problem(
            entry,
            ProblemCode.MISSING_LONG_TERM,
            "missing 'Long-term' item in 'What I'm looking forward to'",
            section.line_no,
            {"section_title": section.title},
        )


def _validate_signals(entry: Entry, section: SectionInfo, content: list[str]) -> None:
    if not any(HELPED_RE.match(line) for line in content):
        _add_problem(
            entry,
            ProblemCode.MISSING_HELPED,
            "missing 'Helped today' item in 'Signals'",
            section.line_no,
            {"section_title": section.title},
        )
    if not any(HURT_RE.match(line) for line in content):
        _add_problem(
            entry,
            ProblemCode.MISSING_HURT,
            "missing 'Hurt today' item in 'Signals'",
            section.line_no,
            {"section_title": section.title},
        )


def _validate_score_line(entry: Entry, section: SectionInfo, line: str) -> None:
    match = SCORE_RE.match(line)
    if not match:
        return
    raw_score = match.group(1)
    if raw_score is None:
        return
    try:
        score_val = float(raw_score)
    except ValueError:
        _add_problem(
            entry,
            ProblemCode.INVALID_SCORE,
            "invalid score value in 'Final score (1/5)'",
            section.line_no,
            {"score": raw_score},
        )
        return
    if not 0 <= score_val <= 5:
        _add_problem(
            entry,
            ProblemCode.SCORE_OUT_OF_RANGE,
            "score must be between 0 and 5",
            section.line_no,
            {"score": raw_score},
        )


def _validate_score(entry: Entry, section: SectionInfo, content: list[str]) -> None:
    actual_scores = []
    for line in content:
        match = SCORE_RE.match(line)
        if match and match.group(1) is not None:
            actual_scores.append(line)
    if actual_scores:
        for line in actual_scores:
            _validate_score_line(entry, section, line)
        return
    if _entry_has_main_content(entry):
        _add_problem(
            entry,
            ProblemCode.MISSING_SCORE,
            "missing score entry in 'Final score (1/5)'",
            section.line_no,
            {"section_title": section.title},
        )


def _validate_section_content(entry: Entry) -> None:
    for title, section in entry.sections.items():
        content = _content_lines(section.content_lines)
        if title in BULLET_REQUIRED and not _has_bullet(content):
            _add_problem(
                entry,
                ProblemCode.MISSING_BULLET,
                f"section '{title}' has no list items",
                section.line_no,
                {"section_title": title},
            )
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


def _weekday_error(weekday_header: str) -> str:
    allowed = "Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday"
    return (
        f"invalid weekday header '{weekday_header}': "
        f"must start with one of {allowed} (extra text allowed after the weekday)"
    )


def _parse_entry_header(entry: Entry) -> None:
    try:
        entry.date = date.fromisoformat(entry.date_str)
    except ValueError:
        _add_problem(
            entry,
            ProblemCode.INVALID_DATE,
            f"invalid date '{entry.date_str}'",
            entry.line_no,
            {"date": entry.date_str},
        )

    weekday_name = _extract_weekday(entry.weekday_header)
    entry.weekday_name = None
    if weekday_name is None:
        _add_problem(
            entry,
            ProblemCode.INVALID_WEEKDAY,
            _weekday_error(entry.weekday_header),
            entry.line_no,
            {"weekday_header": entry.weekday_header},
        )
        return

    weekday_key = weekday_name.lower()
    if weekday_key not in VALID_WEEKDAYS:
        _add_problem(
            entry,
            ProblemCode.INVALID_WEEKDAY,
            _weekday_error(entry.weekday_header),
            entry.line_no,
            {"weekday_header": entry.weekday_header},
        )
        return
    entry.weekday_name = VALID_WEEKDAYS[weekday_key]


def _build_entry(
    lines: list[str],
    header: tuple[int, str, str],
    end: int,
) -> Entry:
    line_idx, date_str, weekday_header = header
    entry = Entry(
        date=None,
        date_str=date_str,
        weekday_header=weekday_header,
        weekday_name=None,
        line_no=line_idx + 1,
    )
    _parse_entry_header(entry)
    block = lines[line_idx + 1 : end]
    _parse_entry_sections(entry, block, line_idx + 1)
    return entry


def _build_entries(
    lines: list[str],
    headers: list[tuple[int, str, str]],
) -> list[Entry]:
    entries: list[Entry] = []
    for idx, header in enumerate(headers):
        end = headers[idx + 1][0] if idx + 1 < len(headers) else len(lines)
        entries.append(_build_entry(lines, header, end))
    return entries


def _duplicate_date_problems(entries: list[Entry]) -> list[Problem]:
    seen_dates: dict[date, int] = {}
    problems: list[Problem] = []
    for entry in entries:
        if entry.date is None:
            continue
        if entry.date in seen_dates:
            problems.append(
                Problem(
                    code=ProblemCode.DUPLICATE_DATE,
                    message=(
                        f"duplicate date '{entry.date.isoformat()}' "
                        f"(first at line {seen_dates[entry.date]})"
                    ),
                    line_no=entry.line_no,
                    context={
                        "date": entry.date.isoformat(),
                        "first_line": str(seen_dates[entry.date]),
                    },
                )
            )
        else:
            seen_dates[entry.date] = entry.line_no
    return problems


def parse_journal(
    lines: list[str],
) -> tuple[list[Entry], list[Problem]]:
    headers = _find_headers(lines)
    if not headers:
        return [], [
            Problem(
                code=ProblemCode.NO_HEADERS,
                message="no day headers found",
                line_no=None,
                context={},
            )
        ]
    entries = _build_entries(lines, headers)
    problems = _duplicate_date_problems(entries)
    return entries, problems
