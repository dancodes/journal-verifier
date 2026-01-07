"""Shared models for autofix."""

from __future__ import annotations

from dataclasses import dataclass

from .problems import Problem


@dataclass
class FixContext:
    lines: list[str]


@dataclass
class FixResult:
    problem: Problem
    applied: bool
    message: str
