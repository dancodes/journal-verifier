"""Date coverage and weekday checks."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

from .models import Entry
from .problems import Problem, ProblemCode


def _iter_dates(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def find_weekday_mismatches(entries: list[Entry]) -> list[tuple[Entry, str]]:
    mismatches: list[tuple[Entry, str]] = []
    for entry in entries:
        if entry.date is None:
            continue
        actual = entry.date.strftime("%A")
        if entry.weekday_name is None:
            continue
        if entry.weekday_name.lower() != actual.lower():
            mismatches.append((entry, actual))
    return mismatches


def _weekday_mismatch_problem(entry: Entry, actual: str) -> Problem:
    return Problem(
        code=ProblemCode.WEEKDAY_MISMATCH,
        message=f"weekday mismatch: header '{entry.weekday_header}' vs actual '{actual}'",
        line_no=entry.line_no,
        context={
            "date": entry.date_str,
            "weekday_header": entry.weekday_header,
            "actual": actual,
        },
    )


def weekday_mismatch_problems(mismatches: list[tuple[Entry, str]]) -> list[Problem]:
    return [_weekday_mismatch_problem(entry, actual) for entry, actual in mismatches]


def _missing_for_range(dates: set[date], start: date, end: date) -> dict[str, list[date]]:
    missing_range = [d for d in _iter_dates(start, end) if d not in dates]
    label = f"{start.isoformat()} to {end.isoformat()}"
    return {label: missing_range}


def _missing_for_years(dates: set[date]) -> dict[str, list[date]]:
    missing: dict[str, list[date]] = {}
    years = sorted({d.year for d in dates})
    for year in years:
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        missing_days = [d for d in _iter_dates(year_start, year_end) if d not in dates]
        missing[str(year)] = missing_days
    return missing


def find_missing_dates(
    entries: list[Entry],
    start: date | None,
    end: date | None,
) -> dict[str, list[date]]:
    dates = {entry.date for entry in entries if entry.date is not None}
    if start and end:
        return _missing_for_range(dates, start, end)
    return _missing_for_years(dates)


def _missing_date_problem(day: date, label: str) -> Problem:
    date_str = day.isoformat()
    return Problem(
        code=ProblemCode.MISSING_DATE,
        message=f"missing date {date_str}",
        line_no=None,
        context={
            "date": date_str,
            "range": label,
        },
    )


def missing_date_problems(missing_dates: dict[str, list[date]], limit: int) -> list[Problem]:
    problems: list[Problem] = []
    for label, dates in missing_dates.items():
        selected = dates if limit == 0 else dates[:limit]
        for day in selected:
            problems.append(_missing_date_problem(day, label))
    return problems
