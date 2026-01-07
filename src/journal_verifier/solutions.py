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


def _ctx(problem: Problem, key: str, default: str) -> str:
    return problem.context.get(key, default)


def _missing_section_hint(problem: Problem) -> str:
    section = _ctx(problem, "section_title", "(unknown)")
    date_str = _ctx(problem, "date", "(unknown date)")
    return f"Add the '{section}' heading under {date_str} to match the template."


def _unexpected_heading_hint(problem: Problem) -> str:
    title = _ctx(problem, "heading_title", "that heading")
    return f"Remove '{title}' or rename it to a template section heading."


def _heading_level_hint(problem: Problem) -> str:
    title = _ctx(problem, "heading_title", "that heading")
    expected = _ctx(problem, "expected_level", "##")
    return f"Change '{title}' to level {expected} to match the template."


def _duplicate_heading_hint(problem: Problem) -> str:
    title = _ctx(problem, "heading_title", "that heading")
    return f"Remove the duplicate '{title}' section; keep one per day."


def _heading_order_hint(problem: Problem) -> str:
    title = _ctx(problem, "heading_title", "that heading")
    return f"Reorder '{title}' to follow the template sequence."


def _invalid_date_hint(problem: Problem) -> str:
    date_str = _ctx(problem, "date", "(unknown date)")
    return f"Fix the date '{date_str}' to YYYY-MM-DD."


def _invalid_weekday_hint(problem: Problem) -> str:
    weekday = _ctx(problem, "weekday_header", "(unknown)")
    return f"Start the weekday with a valid day name (e.g. '{weekday}')."


def _duplicate_date_hint(problem: Problem) -> str:
    date_str = _ctx(problem, "date", "(unknown date)")
    first_line = _ctx(problem, "first_line", "?")
    return f"Remove or merge the duplicate date '{date_str}' (first at line {first_line})."


def _missing_bullet_hint(problem: Problem) -> str:
    section = _ctx(problem, "section_title", "that section")
    return f"Add at least one list item under '{section}'."


def _missing_short_term_hint(problem: Problem) -> str:
    return "Add a '- Short-term:' item under 'What I'm looking forward to'."


def _missing_long_term_hint(problem: Problem) -> str:
    return "Add a '- Long-term:' item under 'What I'm looking forward to'."


def _missing_helped_hint(problem: Problem) -> str:
    return "Add a '- ⬆️ Helped today:' item under 'Signals'."


def _missing_hurt_hint(problem: Problem) -> str:
    return "Add a '- ⬇️ Hurt today:' item under 'Signals'."


def _missing_score_hint(problem: Problem) -> str:
    return "Add a score line like '- 3/5' under 'Final score (1/5)'."


def _invalid_score_hint(problem: Problem) -> str:
    return "Use a numeric score before /5 (e.g. '- 4/5')."


def _score_out_of_range_hint(problem: Problem) -> str:
    return "Use a score between 0 and 5."


def _no_headers_hint(problem: Problem) -> str:
    return "Add day headers like '## YYYY-MM-DD (Weekday)'."


def _missing_date_hint(problem: Problem) -> str:
    date_str = _ctx(problem, "date", "(unknown date)")
    return f"Add a full day entry for {date_str}."


def _weekday_mismatch_hint(problem: Problem) -> str:
    actual = _ctx(problem, "actual", "(unknown)")
    return f"Update the weekday to '{actual}' or correct the date."


SOLUTIONS = [
    Solution(ProblemCode.MISSING_SECTION, "Add missing section heading", _missing_section_hint),
    Solution(ProblemCode.UNEXPECTED_HEADING, "Remove unexpected heading", _unexpected_heading_hint),
    Solution(ProblemCode.HEADING_LEVEL, "Fix heading level", _heading_level_hint),
    Solution(ProblemCode.DUPLICATE_HEADING, "Remove duplicate heading", _duplicate_heading_hint),
    Solution(ProblemCode.HEADING_ORDER, "Reorder heading", _heading_order_hint),
    Solution(ProblemCode.INVALID_DATE, "Fix invalid date", _invalid_date_hint),
    Solution(ProblemCode.INVALID_WEEKDAY, "Fix invalid weekday", _invalid_weekday_hint),
    Solution(ProblemCode.DUPLICATE_DATE, "Resolve duplicate date", _duplicate_date_hint),
    Solution(ProblemCode.MISSING_BULLET, "Add missing list item", _missing_bullet_hint),
    Solution(ProblemCode.MISSING_SHORT_TERM, "Add short-term item", _missing_short_term_hint),
    Solution(ProblemCode.MISSING_LONG_TERM, "Add long-term item", _missing_long_term_hint),
    Solution(ProblemCode.MISSING_HELPED, "Add helped item", _missing_helped_hint),
    Solution(ProblemCode.MISSING_HURT, "Add hurt item", _missing_hurt_hint),
    Solution(ProblemCode.MISSING_SCORE, "Add score", _missing_score_hint),
    Solution(ProblemCode.INVALID_SCORE, "Fix score format", _invalid_score_hint),
    Solution(ProblemCode.SCORE_OUT_OF_RANGE, "Fix score range", _score_out_of_range_hint),
    Solution(ProblemCode.NO_HEADERS, "Add day headers", _no_headers_hint),
    Solution(ProblemCode.MISSING_DATE, "Add missing date", _missing_date_hint),
    Solution(ProblemCode.WEEKDAY_MISMATCH, "Fix weekday mismatch", _weekday_mismatch_hint),
]

_SOLUTIONS = {solution.code: solution for solution in SOLUTIONS}


def get_solution(code: str) -> Solution | None:
    return _SOLUTIONS.get(code)


def solution_hint(problem: Problem) -> str | None:
    solution = get_solution(problem.code)
    if solution is None:
        return None
    return solution.hint(problem)
