from obsidianki.convert import extract_flashcard_blocks, get_flashcard_fields, find_dollar_math_substrings, convert_math, FlashcardExtractionError
import pytest
from textwrap import dedent
from itertools import product

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


def test_convert_math():
    assert convert_math("$x$") == r"\(x\)"
    assert convert_math("$$x$$") == r"\[x\]"
    assert convert_math("$x < y$") == r"\(x &lt; y\)"
    assert convert_math("$x & y$") == r"\(x &amp; y\)"
    assert convert_math("$$x\n+\ny$$") == r"\[x<br>+<br>y\]"
