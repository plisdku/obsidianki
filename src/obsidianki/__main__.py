import re
from textwrap import dedent
import pytest

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