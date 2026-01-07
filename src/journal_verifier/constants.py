"""Shared constants and regexes for journal verification."""

from __future__ import annotations

import re

DAY_HEADER_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}) \(([^)]+)\)\s*$")
HEADING_RE = re.compile(r"^(#{2,3}) (.+?)\s*$")
BULLET_RE = re.compile(r"^\s*-\s*(.*)$")
SCORE_RE = re.compile(r"^\s*-\s*(\d+)?\s*/\s*5\s*$")

UP_ARROW = "\u2b06"
DOWN_ARROW = "\u2b07"
HELPED_RE = re.compile(rf"^\s*-\s*{UP_ARROW}\ufe0f?\s*Helped today\s*:", re.IGNORECASE)
HURT_RE = re.compile(rf"^\s*-\s*{DOWN_ARROW}\ufe0f?\s*Hurt today\s*:", re.IGNORECASE)
SHORT_TERM_RE = re.compile(r"^\s*-\s*Short-term\s*:", re.IGNORECASE)
LONG_TERM_RE = re.compile(r"^\s*-\s*Long-term\s*:", re.IGNORECASE)

EXPECTED_SECTIONS = [
    ("###", "What happened today"),
    ("###", "What I'm grateful for"),
    ("###", "What I'm looking forward to"),
    ("##", "Signals"),
    ("##", "One adjustment (tomorrow)"),
    ("###", "Final score (1/5)"),
]

EXPECTED_INDEX = {title: idx for idx, (_level, title) in enumerate(EXPECTED_SECTIONS)}
EXPECTED_LEVEL = {title: level for level, title in EXPECTED_SECTIONS}
EXPECTED_TITLES = [title for _level, title in EXPECTED_SECTIONS]

VALID_WEEKDAYS = {
    "monday": "Monday",
    "tuesday": "Tuesday",
    "wednesday": "Wednesday",
    "thursday": "Thursday",
    "friday": "Friday",
    "saturday": "Saturday",
    "sunday": "Sunday",
}

WEEKDAY_PREFIX_RE = re.compile(
    r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
    re.IGNORECASE,
)

BULLET_REQUIRED = {
    "What happened today",
    "What I'm grateful for",
    "One adjustment (tomorrow)",
}

SECTION_TEMPLATES = {
    "What happened today": ["- ", "- ", "- ", "- "],
    "What I'm grateful for": ["- ", "- ", "- "],
    "What I'm looking forward to": ["- Short-term: ", "- Long-term: "],
    "Signals": ["- ⬆️ Helped today:", "- ⬇️ Hurt today:"],
    "One adjustment (tomorrow)": ["- "],
    "Final score (1/5)": ["- /5"],
}
