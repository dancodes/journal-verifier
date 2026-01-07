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
from .fixing import apply_fixes, fix_report_lines
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


def _write_csv_output(entries, path_value: str | None) -> None:
    if path_value is None:
        return
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


def _add_output_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--csv",
        default=None,
        help="CSV output path (default: no CSV output; use '-' for stdout)",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Report output path (default: stderr; use '-' for stdout)",
    )


def _add_range_flags(parser: argparse.ArgumentParser) -> None:
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


def _add_fix_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--debug-weekday",
        action="store_true",
        help="Include weekday debug details for invalid headers",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply autofixes for supported problems",
    )
    parser.add_argument(
        "--fix-dry-run",
        action="store_true",
        help="Show autofix summary without writing changes",
    )


def _add_cli_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", help="Path to journal markdown file")
    _add_output_flags(parser)
    _add_range_flags(parser)
    _add_fix_flags(parser)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate journal.md structure, date coverage, and weekday accuracy.",
    )
    _add_cli_flags(parser)
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


def _collect_problem_sets(
    entries,
    global_problems,
    mismatches,
    missing_dates,
    missing_limit: int,
) -> tuple[list, list]:
    structural = list(global_problems)
    for entry in entries:
        structural.extend(entry.problems)
    coverage = weekday_mismatch_problems(mismatches)
    coverage.extend(missing_date_problems(missing_dates, missing_limit))
    return structural, coverage


def _parse_and_collect(lines, args, start_date, end_date):
    entries, global_problems = parse_journal(lines, debug_weekday=args.debug_weekday)
    mismatches = find_weekday_mismatches(entries)
    missing_dates = find_missing_dates(entries, start_date, end_date)
    structural, coverage = _collect_problem_sets(
        entries,
        global_problems,
        mismatches,
        missing_dates,
        args.missing_limit,
    )
    return entries, structural, coverage, mismatches, missing_dates


def _maybe_apply_fixes(path: Path, args, lines, structural, coverage, start_date, end_date):
    if not args.fix and not args.fix_dry_run:
        return lines, [], None
    fix_report = apply_fixes(lines, structural + coverage)
    fix_lines = fix_report_lines(fix_report.results)
    lines = fix_report.lines
    if args.fix:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    updated = _parse_and_collect(lines, args, start_date, end_date)
    return lines, fix_lines, updated


def _report_lines(
    structural,
    coverage,
    missing_dates,
    mismatches,
    missing_limit: int,
    fix_lines: list[str],
) -> list[str]:
    lines = build_report(
        structural,
        coverage,
        missing_dates,
        mismatches,
        missing_limit,
    )
    lines.extend(fix_lines)
    return lines


def _execute(args, parser: argparse.ArgumentParser):
    start_date, end_date = _resolve_range(args, parser)
    path = Path(args.path)
    lines = _load_lines(path, parser)
    entries, structural, coverage, mismatches, missing_dates = _parse_and_collect(
        lines,
        args,
        start_date,
        end_date,
    )
    lines, fix_lines, updated = _maybe_apply_fixes(
        path,
        args,
        lines,
        structural,
        coverage,
        start_date,
        end_date,
    )
    if updated is not None:
        entries, structural, coverage, mismatches, missing_dates = updated
    report_lines = _report_lines(
        structural,
        coverage,
        missing_dates,
        mismatches,
        args.missing_limit,
        fix_lines,
    )
    return report_lines, entries


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    if args.fix and args.fix_dry_run:
        parser.error("--fix and --fix-dry-run cannot be used together")
    report_lines, entries = _execute(args, parser)
    _write_lines(report_lines, args.report, sys.stderr)
    _write_csv_output(entries, args.csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
