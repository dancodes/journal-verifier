"""CLI entry point for verifying journal markdown structure."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from .coverage import (
    find_missing_dates,
    find_weekday_mismatches,
    missing_date_problems,
    weekday_mismatch_problems,
)
from .parsing import parse_journal
from .reporting import build_report, write_csv


def _open_output(path_value: str | None, default_stream):
    if path_value is None:
        return default_stream, False
    if path_value == "-":
        return sys.stdout, False
    return open(path_value, "w", encoding="utf-8", newline=""), True


def _write_lines(lines: list[str], path_value: str | None, default_stream) -> None:
    stream, should_close = _open_output(path_value, default_stream)
    try:
        for line in lines:
            stream.write(f"{line}\n")
    finally:
        if should_close:
            stream.close()


def _write_csv_output(entries, path_value: str) -> None:
    stream, should_close = _open_output(path_value, sys.stdout)
    try:
        write_csv(entries, stream)
    finally:
        if should_close:
            stream.close()


def _parse_date_arg(value: str, parser: argparse.ArgumentParser, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        parser.error(f"invalid {label} date '{value}', expected YYYY-MM-DD")
        raise exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate journal.md structure, date coverage, and weekday accuracy.",
    )
    parser.add_argument("path", help="Path to journal markdown file")
    parser.add_argument(
        "--csv",
        default="-",
        help="CSV output path (default: stdout; use '-' for stdout)",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Report output path (default: stderr; use '-' for stdout)",
    )
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--year",
        type=int,
        help="Shortcut for --start/--end for a full year (e.g. 2026)",
    )
    parser.add_argument(
        "--missing-limit",
        type=int,
        default=20,
        help="Max missing dates to list per range (0 = all)",
    )
    parser.add_argument(
        "--debug-weekday",
        action="store_true",
        help="Include weekday debug details for invalid headers",
    )
    return parser


def _resolve_range(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> tuple[date | None, date | None]:
    if args.year and (args.start or args.end):
        parser.error("--year cannot be used with --start or --end")
    if (args.start and not args.end) or (args.end and not args.start):
        parser.error("--start and --end must be provided together")
    if args.year:
        return date(args.year, 1, 1), date(args.year, 12, 31)
    if args.start and args.end:
        start_date = _parse_date_arg(args.start, parser, "start")
        end_date = _parse_date_arg(args.end, parser, "end")
        if start_date > end_date:
            parser.error("--start must be earlier than or equal to --end")
        return start_date, end_date
    return None, None


def _load_lines(path: Path, parser: argparse.ArgumentParser) -> list[str]:
    if not path.exists():
        parser.error(f"file not found: {path}")
    return path.read_text(encoding="utf-8").splitlines()


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    start_date, end_date = _resolve_range(args, parser)

    lines = _load_lines(Path(args.path), parser)
    entries, global_problems = parse_journal(lines, debug_weekday=args.debug_weekday)
    mismatches = find_weekday_mismatches(entries)
    missing_dates = find_missing_dates(entries, start_date, end_date)

    structural_problems = list(global_problems)
    for entry in entries:
        structural_problems.extend(entry.problems)

    coverage_problems = weekday_mismatch_problems(mismatches)
    coverage_problems.extend(missing_date_problems(missing_dates, args.missing_limit))

    report_lines = build_report(
        structural_problems,
        coverage_problems,
        missing_dates,
        mismatches,
        args.missing_limit,
    )
    _write_lines(report_lines, args.report, sys.stderr)
    _write_csv_output(entries, args.csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
