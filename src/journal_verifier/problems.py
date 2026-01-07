"""Problem definitions and catalog."""

from __future__ import annotations

from dataclasses import dataclass, field


class ProblemCode:
    MISSING_SECTION = "missing_section"
    UNEXPECTED_HEADING = "unexpected_heading"
    HEADING_LEVEL = "heading_level"
    DUPLICATE_HEADING = "duplicate_heading"
    HEADING_ORDER = "heading_order"
    INVALID_DATE = "invalid_date"
    INVALID_WEEKDAY = "invalid_weekday"
    DUPLICATE_DATE = "duplicate_date"
    MISSING_BULLET = "missing_bullet"
    MISSING_SHORT_TERM = "missing_short_term"
    MISSING_LONG_TERM = "missing_long_term"
    MISSING_HELPED = "missing_helped"
    MISSING_HURT = "missing_hurt"
    MISSING_SCORE = "missing_score"
    INVALID_SCORE = "invalid_score"
    SCORE_OUT_OF_RANGE = "score_out_of_range"
    NO_HEADERS = "no_day_headers"
    MISSING_DATE = "missing_date"
    WEEKDAY_MISMATCH = "weekday_mismatch"


ALL_PROBLEM_CODES = [
    ProblemCode.MISSING_SECTION,
    ProblemCode.UNEXPECTED_HEADING,
    ProblemCode.HEADING_LEVEL,
    ProblemCode.DUPLICATE_HEADING,
    ProblemCode.HEADING_ORDER,
    ProblemCode.INVALID_DATE,
    ProblemCode.INVALID_WEEKDAY,
    ProblemCode.DUPLICATE_DATE,
    ProblemCode.MISSING_BULLET,
    ProblemCode.MISSING_SHORT_TERM,
    ProblemCode.MISSING_LONG_TERM,
    ProblemCode.MISSING_HELPED,
    ProblemCode.MISSING_HURT,
    ProblemCode.MISSING_SCORE,
    ProblemCode.INVALID_SCORE,
    ProblemCode.SCORE_OUT_OF_RANGE,
    ProblemCode.NO_HEADERS,
    ProblemCode.MISSING_DATE,
    ProblemCode.WEEKDAY_MISMATCH,
]

STRUCTURAL_CODES = {
    ProblemCode.MISSING_SECTION,
    ProblemCode.UNEXPECTED_HEADING,
    ProblemCode.HEADING_LEVEL,
    ProblemCode.DUPLICATE_HEADING,
    ProblemCode.HEADING_ORDER,
    ProblemCode.INVALID_DATE,
    ProblemCode.INVALID_WEEKDAY,
    ProblemCode.DUPLICATE_DATE,
    ProblemCode.MISSING_BULLET,
    ProblemCode.MISSING_SHORT_TERM,
    ProblemCode.MISSING_LONG_TERM,
    ProblemCode.MISSING_HELPED,
    ProblemCode.MISSING_HURT,
    ProblemCode.MISSING_SCORE,
    ProblemCode.INVALID_SCORE,
    ProblemCode.SCORE_OUT_OF_RANGE,
    ProblemCode.NO_HEADERS,
}

COVERAGE_CODES = {
    ProblemCode.MISSING_DATE,
    ProblemCode.WEEKDAY_MISMATCH,
}


@dataclass(frozen=True)
class Problem:
    code: str
    message: str
    line_no: int | None
    context: dict[str, str] = field(default_factory=dict)
