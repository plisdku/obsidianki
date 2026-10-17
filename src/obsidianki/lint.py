from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from obsidianki.convert import (
    FlashcardExtractionError,
    extract_flashcard_blocks,
    find_dollar_math_substrings,
    get_flashcard_fields,
)


@dataclass(frozen=True)
class LintIssue:
    level: str
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.level}: line {self.line}: {self.message}"


def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def lint_text(text: str, filename: str | Path) -> list[LintIssue]:
    """Check vault flashcard syntax and conventions without exporting cards."""
    path = Path(filename)
    issues: list[LintIssue] = []

    for index, character in enumerate(text):
        if ord(character) < 32 and character not in "\n\r\t":
            issues.append(
                LintIssue(
                    "ERROR",
                    _line_number(text, index),
                    f"control character U+{ord(character):04X}; check for corrupted LaTeX",
                )
            )

    try:
        blocks = extract_flashcard_blocks(text)
    except FlashcardExtractionError as error:
        issues.append(LintIssue("ERROR", 1, str(error)))
        return issues

    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if line == ":flashcard:"]
    expected_reference = path.stem
    defaults: dict[str, str] = {}

    for card_number, (block, start) in enumerate(zip(blocks, starts), start=1):
        line = start + 1
        try:
            fields = get_flashcard_fields(block, defaults)
        except FlashcardExtractionError as error:
            issues.append(LintIssue("ERROR", line, f"card {card_number}: {error}"))
            continue

        question = fields.get("Q", "").strip()
        answer = fields.get("A", "").strip()
        reference = fields.get("R", "").strip()

        if not question:
            issues.append(LintIssue("ERROR", line, f"card {card_number}: empty question"))
        if not answer:
            issues.append(LintIssue("ERROR", line, f"card {card_number}: empty A: field"))
        if reference != expected_reference:
            issues.append(
                LintIssue(
                    "WARNING",
                    line,
                    f"card {card_number}: R: should be filename stem "
                    f"{expected_reference!r} for a card made from this note",
                )
            )

        for field in ("Q", "A", "X"):
            value = fields.get(field, "")
            try:
                find_dollar_math_substrings(value)
            except (AssertionError, FlashcardExtractionError) as error:
                issues.append(LintIssue("ERROR", line, f"card {card_number}, {field}: {error}"))

        defaults = {key: fields[key] for key in ("X", "R", "C", "P") if key in fields}

    return issues


def lint_file(filename: str | Path) -> list[LintIssue]:
    path = Path(filename)
    return lint_text(path.read_text(encoding="utf-8"), path)
