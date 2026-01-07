"""Apply autofixable solutions."""

from __future__ import annotations

from dataclasses import dataclass

from .constants import EXPECTED_INDEX
from .fix_models import FixContext, FixResult
from .problems import Problem, ProblemCode
from .solutions import get_solution


@dataclass
class FixReport:
    lines: list[str]
    results: list[FixResult]


def _fixable_items(problems: list[Problem]) -> list[tuple[Problem, object]]:
    items: list[tuple[Problem, object]] = []
    for problem in problems:
        solution = get_solution(problem.code)
        if not solution or not solution.auto_fixable or not solution.apply_fix:
            continue
        items.append((problem, solution))
    return items


def _missing_section_key(problem: Problem) -> tuple[int, int]:
    line_no = problem.line_no or 0
    title = problem.context.get("section_title", "")
    return (-line_no, EXPECTED_INDEX.get(title, 999))


def _apply_fix(context: FixContext, problem: Problem, solution) -> FixResult:
    return solution.apply_fix(context, problem)


def apply_fixes(lines: list[str], problems: list[Problem]) -> FixReport:
    context = FixContext(lines=list(lines))
    results: list[FixResult] = []
    fixable = _fixable_items(problems)

    missing = [(problem, solution) for problem, solution in fixable if problem.code == ProblemCode.MISSING_SECTION]
    for problem, solution in sorted(missing, key=lambda item: _missing_section_key(item[0])):
        results.append(_apply_fix(context, problem, solution))

    return FixReport(lines=context.lines, results=results)


def _fix_summary(results: list[FixResult]) -> str:
    applied = sum(1 for result in results if result.applied)
    skipped = len(results) - applied
    return f"Fixes: applied {applied}, skipped {skipped}"


def fix_report_lines(results: list[FixResult]) -> list[str]:
    if not results:
        return []
    lines = [_fix_summary(results)]
    for result in results:
        if result.applied:
            continue
        label = f"- line {result.problem.line_no}: " if result.problem.line_no else "- "
        lines.append(f"{label}{result.message}")
    return lines
