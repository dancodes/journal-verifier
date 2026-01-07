"""Dataclasses for journal verification."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .problems import Problem

@dataclass
class SectionInfo:
    title: str
    level: str
    line_no: int
    content_lines: list[str]


@dataclass
class Entry:
    date: date | None
    date_str: str
    weekday_header: str
    weekday_name: str | None
    line_no: int
    sections: dict[str, SectionInfo] = field(default_factory=dict)
    problems: list[Problem] = field(default_factory=list)
    errors: list[tuple[int, str]] = field(default_factory=list)
