import re
from textwrap import dedent
import pytest
import html
from itertools import product

class FlashcardExtractionError(Exception):
    pass

def extract_flashcard_blocks(text: str, strip:bool = True) -> list[str]:
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
    line_ranges: list[tuple[int,int]] = []

    prev_start: int | None = None # first line of the block, excluding the starting token
    
    for idx, line in enumerate(lines):
        if line == ":flashcard:":
            if prev_start is not None:
                line_ranges.append((prev_start, idx))
            prev_start = idx+1
        elif line == "::":
            if prev_start is not None:
                line_ranges.append((prev_start, idx))
            prev_start = None
    
    if prev_start is not None:
        raise FlashcardExtractionError(f"A flashcard block beginning on line {prev_start} was not closed with a ::")

    blocks = ["\n".join(lines[start:end]) for start, end in line_ranges]
    if strip:
        blocks = [block.strip() for block in blocks]
    return blocks

def test_extract_flashcard_blocks():
    text = dedent(r"""
    There can be some front matter. Then, a card:
    :flashcard:
    First card content
    ::
    Now stuff between the cards. Next I'll do two cards in a row.
    :flashcard:
    Second card content
    :flashcard:
    Third card content
    ::
    And stuff at the end.
    """)

    blocks = extract_flashcard_blocks(text)
    assert blocks == ["First card content", "Second card content", "Third card content"]

def test_extract_no_flashcards():
    text = dedent(r"""
    Just a bunch of text.
                  
    No flashcards here.
    """)

    blocks = extract_flashcard_blocks(text)
    assert blocks == []

def test_extract_unclosed_flashcard():
    text = dedent(r"""
    Make a card but don't close it.
    :flashcard:
    First card content
    """)

    with pytest.raises(FlashcardExtractionError) as excinfo:
        extract_flashcard_blocks(text)

test_extract_flashcard_blocks()
test_extract_no_flashcards()
test_extract_unclosed_flashcard()


def get_flashcard_fields(text: str, defaults: dict[str,str] | None = None) -> dict[str,str]:
    """
    Split Q, A and other fields and return them as a dict.
    """
    if defaults is None:
        defaults = {}

    fields = defaults.copy()

    field_pattern = re.compile(r"^(A|Answer|X|Extra|R|Reference|Book|C|Chapter|P|Page):", re.MULTILINE)
    
    matches = list(field_pattern.finditer(text))

    starts = [0] + [match.end() for match in matches]
    ends = [match.start() for match in matches] + [len(text)]

    fields["Q"] = text[starts[0]:ends[0]].strip()

    for idx, match in enumerate(matches):
        field = match.group(1)

        content = text[starts[idx+1]:ends[idx+1]].strip()

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

def test_get_flashcard_fields():

    for answer, book, chapter, page in product(["A", "Answer"], ["Book", "R"], ["C", "Chapter"], ["P", "Page"]):
        # Swap in equivalent versions of the tags.
        # Also note some newlines put in there.
        text = dedent(f"""
        What is the capital of France?
        {answer}: Paris
        {book}:
        Geography 101
        {chapter}: 2

        {page}: 15

        """)

        fields = get_flashcard_fields(text)
        assert fields["Q"] == "What is the capital of France?"
        assert fields["A"] == "Paris"
        assert fields["R"] == "Geography 101"
        assert fields["C"] == "2"
        assert fields["P"] == "15"

def test_get_flashcard_fields_default():
    text = dedent(r"""
    What is the capital of France?
    """)

    fields = get_flashcard_fields(text, defaults={"Q": "What is the capital of France?", "A": "Paris", "P": "15"})

    assert fields == {
        "Q": "What is the capital of France?",
        "A": "Paris",
        "P": "15"
    }

test_get_flashcard_fields()
test_get_flashcard_fields_default()


def find_dollar_math_substrings(text: str) -> list[tuple[int,int]]:
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
                assert curly_brace_depth == 0, "Should not be counting curly braces outside math blocks"
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
        raise FlashcardExtractionError(f"A math block beginning at {math_starts[-1]} was not closed with $ or $$")

    if len(math_starts) != len(math_ends):
        raise FlashcardExtractionError(f"Unmatched math delimiters in text:\n{text}")

    return list(zip(math_starts, math_ends))

def test_find_dollar_math_substrings():
    text = dedent(r"""
    This is some text with $inline math$ and $$display math$$.
    And some more text with $nested {$math$} in it$.
    And some more text with nested $$display {$m {$at$} h$} in it$$.
    """)

    # text = dedent(r"""
    # And some more text with $nested {$math$} in it$.
    # """)

    math_ranges = find_dollar_math_substrings(text)

    assert text[math_ranges[0][0]:math_ranges[0][1]] == "$inline math$"
    assert text[math_ranges[1][0]:math_ranges[1][1]] == "$$display math$$"
    assert text[math_ranges[2][0]:math_ranges[2][1]] == "$nested {$math$} in it$"
    assert text[math_ranges[3][0]:math_ranges[3][1]] == "$$display {$m {$at$} h$} in it$$"

test_find_dollar_math_substrings()

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

def test_convert_math():
    assert convert_math("$x$") == r"\(x\)"
    assert convert_math("$$x$$") == r"\[x\]"
    assert convert_math("$x < y$") == r"\(x &lt; y\)"
    assert convert_math("$x & y$") == r"\(x &amp; y\)"
    assert convert_math("$$x\n+\ny$$") == r"\[x<br>+<br>y\]"

test_convert_math()

exit()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert Obsidian Markdown to Anki HTML")
    parser.add_argument("input_file", help="Obsidian markdown file")
    parser.add_argument("output_file", nargs="?", default="", help="Output Anki-compatible file")
    args = parser.parse_args()
    
    with open(args.input_file, 'r', encoding='utf-8') as f:
        obsidian_text = f.read()

    blocks = extract_flashcard_blocks(obsidian_text)

    print("\n-----\n".join(blocks))

    
    # anki_cards = convert_obsidian_to_anki(obsidian_text)

    # # Write to output file in a format Anki can import
    # with open(args.output_file, 'w', encoding='utf-8') as f:
    #     for card in anki_cards:
    #         answer = ""
    #         if "A" in card:
    #             answer = card["A"]
    #         if "AA" in card:
    #             answer += "\n\n" + random.choice(EMOJI) + "\n\n" + card["AA"]
            
    #         card_text = f"Q:\n{card['Q']}\nA:\n{answer}\nBook:\n{card['Book']}\nChapter:\n{card['Chapter']}\nPage:\n{card['Page']}\n"
    #         f.write(card_text)
    #         f.write("-"*20 + "\n")
    
    # print(f"Converted {len(anki_cards)} cards from {args.input_file} to {args.output_file}")


if __name__ == "__main__":
    main()