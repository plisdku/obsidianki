from obsidianki.convert import (
    extract_flashcard_blocks,
    get_flashcard_fields,
    find_dollar_math_substrings,
    convert_math
)
from markdown2 import markdown, Markdown
import argparse
import pandas as pd
import random
from obsidianki.my_emoji import EMOJI
import re

def protect_urls(md: str) -> str:
    """Wrap bare URLs in angle brackets to stop underscore parsing."""
    url_pattern = re.compile(r'(?<![\(<\[])'  # not already in (), <>, or []
                             r'(https?://[^\s<>\]\)]+)', re.IGNORECASE)
    return url_pattern.sub(r'<\1>', md)


def remove_backticks_python(value: str) -> str:
    """
    Remove backticks from Python code blocks.
    """
    # Remove 'python' from code blocks
    return value.replace("```python", "```")


def convert_flashcard_block(fields: dict[str,str]) -> dict[str,str]:
    """
    Turn a markdown flashcard block into HTML.
    """
    for key, value in fields.items():
        value = value.strip()
        if not value:
            continue
        
        if key in ("Q", "A", "X"):
            substrings = find_dollar_math_substrings(value)

            math_blocks = []
            for start, end in substrings:
                converted_math = convert_math(value[start:end])
                math_blocks.append(converted_math)
                
            # Replace substrings with '{MATHPLACEHOLDER}'

            for start, end in reversed(substrings):
                value = value[:start] + "{MATHPLACEHOLDER}" + value[end:]
            
            html_content = markdown(protect_urls(remove_backticks_python(value)), extras=["break-on-newline", "tables", "cuddled-lists"])

            # Replace '{MATHPLACEHOLDER}' with math blocks
            for math_block in math_blocks:
                html_content = html_content.replace("{MATHPLACEHOLDER}", math_block, 1)
            
            fields[key] = html_content
    
    return fields


def main():

    parser = argparse.ArgumentParser(description="Convert Obsidian Markdown to Anki HTML")
    parser.add_argument("input_file", help="Obsidian markdown file")
    parser.add_argument("output_file", nargs="?", default="", help="Output Anki-compatible file")
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as f:
        obsidian_text = f.read()

    blocks = extract_flashcard_blocks(obsidian_text)

    card_dicts: list[dict[str, str]] = []

    default_block = {"Q": "", "A": "", "X": "", "R": "", "C": "", "P": ""}
    for block in blocks:
        fields = get_flashcard_fields(block, default_block)

        carryover_keys = ("X", "R", "C", "P")
        default_block = {key: fields[key] for key in carryover_keys if key in fields}

        card_dict = convert_flashcard_block(fields)

        extra = card_dict.get("X", "").strip()

        if extra:
            # I used to add two newlines around the emoji, but my output has <p> and
            # doesn't seem to need extra space.
            card_dict["A"] = card_dict.get("A", "") + random.choice(EMOJI) + extra

        card_dicts.append(card_dict)

    df = pd.DataFrame(card_dicts)

    df.rename(columns={"Q": "Front", "A": "Back", "R": "Reference", "C": "Chapter", "P": "Page"}, inplace=True)
    df = df[["Front", "Back", "Reference", "Chapter", "Page"]]

    if args.output_file:
        # Don't put the header in the file because Anki will make a flashcard out of it.
        df.to_csv(args.output_file, index=False, header=False)
    else:
        print(df.to_csv(index=False, header=True))


    # print("\n-----\n".join(blocks))

    # anki_cards = convert_obsidian_to_anki(obsidian_text)

    # # Write to output file in a format Anki can import
    # with open(args.output_file, "w", encoding="utf-8") as f:
    #     for card in anki_cards:
    #         answer = ""
    #         if "A" in card:
    #             answer = card["A"]
    #         if "AA" in card:
    #             answer += "\n\n" + random.choice(EMOJI) + "\n\n" + card["AA"]

    #         card_text = (
    #             f"Q:\n{card['Q']}\nA:\n{answer}\nBook:\n{card['Book']}"
    #             "\nChapter:\n{card['Chapter']}\nPage:\n{card['Page']}\n"
    #         )
    #         f.write(card_text)
    #         f.write("-" * 20 + "\n")

    # print(f"Converted {len(anki_cards)} cards from {args.input_file} to {args.output_file}")


if __name__ == "__main__":
    main()
