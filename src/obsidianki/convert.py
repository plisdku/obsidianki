import re
import html


class FlashcardExtractionError(Exception):
    pass


def extract_flashcard_blocks(text: str, strip: bool = True) -> list[str]:
    """
    Extract flashcard blocks from the given text.
    Flashcards are delimited by "flashcard:" starting tokens and ":flashcard" ending tokens.
    These tokens are on newlines by themselves.

    Args:
        text: text of a Markdown file with flashcard blocks in it
    Returns:
        list of flashcard blocks, excluding starting and ending tokens
    """

    lines = text.splitlines()
    line_ranges: list[tuple[int, int]] = []

    prev_start: int | None = (
        None  # first line of the block, excluding the starting token
    )

    for idx, line in enumerate(lines):
        if line == ":flashcard:":
            if prev_start is not None:
                line_ranges.append((prev_start, idx))
            prev_start = idx + 1
        elif line == "::":
            if prev_start is not None:
                line_ranges.append((prev_start, idx))
            prev_start = None

    if prev_start is not None:
        raise FlashcardExtractionError(
            f"A flashcard block beginning on line {prev_start} was not closed with a ::"
        )

    blocks = ["\n".join(lines[start:end]) for start, end in line_ranges]
    if strip:
        blocks = [block.strip() for block in blocks]
    return blocks


def get_flashcard_fields(
    text: str, defaults: dict[str, str] | None = None
) -> dict[str, str]:
    """
    Split Q, A and other fields and return them as a dict.
    """
    if defaults is None:
        defaults = {}

    fields = defaults.copy()

    field_pattern = re.compile(
        r"^(A|Answer|X|Extra|R|Reference|Book|C|Chapter|P|Page):", re.MULTILINE
    )

    matches = list(field_pattern.finditer(text))

    starts = [0] + [match.end() for match in matches]
    ends = [match.start() for match in matches] + [len(text)]

    fields["Q"] = text[starts[0] : ends[0]].strip()

    for idx, match in enumerate(matches):
        field = match.group(1)

        content = text[starts[idx + 1] : ends[idx + 1]].strip()

        if field in ("A", "Answer"):
            field = "A"
        elif field in ("X", "Extra"):
            field = "X"
        elif field in ("R", "Reference", "Book"):
            field = "R"
        elif field in ("C", "Chapter"):
            field = "C"
        elif field in ("P", "Page"):
            field = "P"
        else:
            raise FlashcardExtractionError(f"Unknown field {field} in text:\n{text}")

        fields[field] = content

    return fields


def find_dollar_math_substrings(text: str) -> list[tuple[int, int]]:
    r"""
    Find all substrings in the section that are delimited by $ or $$.

    Args:
        text: Markdown text with math delimiters.
    Returns:
        list of start and end indices
    """

    # This regex matches $, $$, {, and }.
    delim_pattern = re.compile(r"(\$+|[{}])", re.MULTILINE)

    delims = list(delim_pattern.finditer(text))

    if not delims:
        return []

    # Get the start and end indices of the delimited math blocks.
    #  - An inline math block is delimited by $...$
    #  - A display math block is delimited by $$...$$
    #  - Math blocks may contain more $ inside them, within curly braces
    #  - Further curly braces and $ may be nested to arbitrary depth
    #
    # So we want to only find the outermost $ or $$.
    #
    # I don't think you'll ever see $$ nested in curly braces. I'm not going
    # to look for this, but it's a potential problem.

    curly_brace_depth = 0
    in_math_block = False

    math_starts: list[int] = []
    math_ends: list[int] = []

    for match in delims:
        # print("Matched:", match.group(0), "at", match.start(), match.end())
        delim = match.group(0)

        if delim in ("$", "$$"):
            if in_math_block:
                if curly_brace_depth == 0:
                    in_math_block = False
                    math_ends.append(match.end())
                else:
                    pass
            else:
                assert (
                    curly_brace_depth == 0
                ), "Should not be counting curly braces outside math blocks"
                in_math_block = True
                math_starts.append(match.start())
        else:
            if in_math_block:
                if delim == "{":
                    curly_brace_depth += 1
                elif delim == "}":
                    curly_brace_depth -= 1
            else:
                pass

    if in_math_block:
        raise FlashcardExtractionError(
            f"A math block beginning at {math_starts[-1]} was not closed with $ or $$"
        )

    if len(math_starts) != len(math_ends):
        raise FlashcardExtractionError(f"Unmatched math delimiters in text:\n{text}")

    return list(zip(math_starts, math_ends))


def convert_math(content: str) -> str:
    r"""
    Convert a math block delimited by $ or $$ to one delimited by \( \) or \[ \],
    and sanitize it for html.
    """
    if content.startswith("$$"):
        assert content.endswith("$$")
        inner_content = content[2:-2]
        delims = (r"\[", r"\]")
    elif content.startswith("$"):
        if len(content) > 2:
            assert not content.endswith("$$")
        assert content.endswith("$")
        inner_content = content[1:-1]
        delims = (r"\(", r"\)")

    sanitized_content = html.escape(inner_content)
    sanitized_content = sanitized_content.replace("\n", "<br>")

    return delims[0] + sanitized_content + delims[1]
