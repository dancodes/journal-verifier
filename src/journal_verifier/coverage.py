"""Date coverage and weekday checks."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

from .models import Entry


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
