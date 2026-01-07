"""Report and CSV generation."""

from __future__ import annotations

import csv
from datetime import date

from .constants import EXPECTED_TITLES
from .models import Entry
from .problems import Problem
from .solutions import solution_hint


def _format_missing_dates(dates: list[date], limit: int) -> str:
    if not dates:
        return "none"
    if limit == 0 or len(dates) <= limit:
        return ", ".join(d.isoformat() for d in dates)
    visible = ", ".join(d.isoformat() for d in dates[:limit])
    remaining = len(dates) - limit
    return f"{visible} (+{remaining} more)"


def _sorted_problems(problems: list[Problem]) -> list[Problem]:
    return sorted(problems, key=lambda item: (item.line_no is None, item.line_no or 0))


def _syntax_report_lines(problems: list[Problem]) -> list[str]:
    if not problems:
        return ["Syntax errors: none"]

    report_lines = ["Syntax errors:"]
    for problem in _sorted_problems(problems):
        label = f"- line {problem.line_no}: " if problem.line_no else "- "
        report_lines.append(f"{label}{problem.message}")
    return report_lines


def _missing_report_lines(
    missing_dates: dict[str, list[date]],
    missing_limit: int,
) -> list[str]:
    if not any(dates for dates in missing_dates.values()):
        return ["Missing dates: none"]

    report_lines = ["Missing dates:"]
    for label, dates in missing_dates.items():
        if not dates:
            continue
        formatted = _format_missing_dates(dates, missing_limit)
        report_lines.append(f"- {label}: {len(dates)} missing")
        report_lines.append(f"  {formatted}")
    return report_lines


def _weekday_report_lines(mismatches: list[tuple[Entry, str]]) -> list[str]:
    if not mismatches:
        return ["Weekday mismatches: none"]

    report_lines = ["Weekday mismatches:"]
    for entry, actual in mismatches:
        report_lines.append(
            f"- {entry.date_str}: header '{entry.weekday_header}' vs actual '{actual}'"
        )
    return report_lines


def _solution_report_lines(problems: list[Problem]) -> list[str]:
    hints = []
    for problem in _sorted_problems(problems):
        hint = solution_hint(problem)
        if hint:
            label = f"- line {problem.line_no}: " if problem.line_no else "- "
            hints.append(f"{label}{hint}")
    if not hints:
        return []
    return ["Solutions:"] + hints


def build_report(
    structural_problems: list[Problem],
    coverage_problems: list[Problem],
    missing_dates: dict[str, list[date]],
    mismatches: list[tuple[Entry, str]],
    missing_limit: int,
) -> list[str]:
    all_problems = list(structural_problems) + list(coverage_problems)
    report_lines: list[str] = []
    report_lines.extend(_syntax_report_lines(structural_problems))
    report_lines.extend(_missing_report_lines(missing_dates, missing_limit))
    report_lines.extend(_weekday_report_lines(mismatches))
    report_lines.extend(_solution_report_lines(all_problems))
    return report_lines


def _csv_row(entry: Entry) -> list[str]:
    actual = entry.date.strftime("%A") if entry.date else ""
    matches = ""
    if entry.date and entry.weekday_name:
        matches = "true" if entry.weekday_name.lower() == actual.lower() else "false"
    present = [title for title in EXPECTED_TITLES if title in entry.sections]
    missing = [title for title in EXPECTED_TITLES if title not in entry.sections]
    return [
        entry.date_str,
        entry.weekday_header,
        actual,
        matches,
        "; ".join(present),
        "; ".join(missing),
    ]


def write_csv(entries: list[Entry], output) -> None:
    writer = csv.writer(output)
    writer.writerow(
        [
            "date",
            "weekday_header",
            "weekday_actual",
            "weekday_matches",
            "sections_present",
            "sections_missing",
        ]
    )
    for entry in entries:
        writer.writerow(_csv_row(entry))
