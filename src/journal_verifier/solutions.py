"""Solution catalog for detected problems."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .problems import Problem, ProblemCode


@dataclass(frozen=True)
class Solution:
    code: str
    title: str
    hint: Callable[[Problem], str]
    auto_fixable: bool = False


def _missing_section_hint(problem: Problem) -> str:
    section = problem.context.get("section_title", "(unknown)")
    date_str = problem.context.get("date", "(unknown date)")
    return f"Add the '{section}' heading under {date_str} to match the template."


MISSING_SECTION_SOLUTION = Solution(
    code=ProblemCode.MISSING_SECTION,
    title="Add missing section heading",
    hint=_missing_section_hint,
    auto_fixable=False,
)

_SOLUTIONS = {
    MISSING_SECTION_SOLUTION.code: MISSING_SECTION_SOLUTION,
}


def get_solution(code: str) -> Solution | None:
    return _SOLUTIONS.get(code)


def solution_hint(problem: Problem) -> str | None:
    solution = get_solution(problem.code)
    if solution is None:
        return None
    return solution.hint(problem)
