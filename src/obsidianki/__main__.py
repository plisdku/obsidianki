import argparse
import json
import random
import re

import pandas as pd
from markdown2 import markdown

from obsidianki.convert import (
    convert_math,
    extract_flashcard_blocks,
    find_dollar_math_substrings,
    get_flashcard_fields,
)
from obsidianki.my_emoji import EMOJI


def protect_urls(md: str) -> str:
    """Wrap bare URLs in angle brackets to stop underscore parsing."""
    url_pattern = re.compile(
        r"(?<![\(<\[])" r"(https?://[^\s<>\]\)]+)",  # not already in (), <>, or []
        re.IGNORECASE,
    )
    return url_pattern.sub(r"<\1>", md)


def remove_backticks_python(value: str) -> str:
    """
    Remove backticks from Python code blocks.
    """
    # Remove 'python' from code blocks
    return value.replace("```python", "```")


def convert_flashcard_block(fields: dict[str, str]) -> dict[str, str]:
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

            html_content = markdown(
                protect_urls(remove_backticks_python(value)),
                extras=["break-on-newline", "tables", "cuddled-lists"],
            )

            # Replace '{MATHPLACEHOLDER}' with math blocks
            for math_block in math_blocks:
                html_content = html_content.replace("{MATHPLACEHOLDER}", math_block, 1)

            fields[key] = html_content

    return fields


def main():
    parser = argparse.ArgumentParser(description="Convert Obsidian Markdown to Anki HTML")
    parser.add_argument("input_file", help="Obsidian markdown file")
    parser.add_argument("output_file", nargs="?", default="", help="Output Anki-compatible file")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of json")
    parser.add_argument(
        "--all",
        help="Output cards with a checkmark in the question (they will be omitted by default)",
    )
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as f:
        obsidian_text = f.read()

    blocks = extract_flashcard_blocks(obsidian_text)

    card_dicts: list[dict[str, str]] = []

    default_block = {"Q": "", "A": "", "X": "", "R": "", "C": "", "P": ""}
    for block in blocks:
        fields = get_flashcard_fields(block, default_block)

        # Always carry over reference, chapter and page
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

    df.rename(
        columns={
            "Q": "Front",
            "A": "Back",
            "R": "Reference",
            "C": "Chapter",
            "P": "Page",
        },
        inplace=True,
    )
    df = df[["Front", "Back", "Reference", "Chapter", "Page"]]

    if not args.all:
        df.query("~Front.str.contains('✅')", inplace=True)

    if args.output_file:
        # Don't put the header in the file because Anki will make a flashcard out of it.
        df.to_csv(args.output_file, index=False, header=False)
    elif args.json:
        # Convert to JSON format

        # pretty-print json
        # json_data = df.to_json(orient="records", indent=4)
        # compact json
        # json_data = df.to_json(orient="records", indent=None)

        json_str = json.dumps(df.to_dict(orient="records"), indent=4)

        print(json_str)
        # with open(args.output_file, "w", encoding="utf-8") as f:
        #     f.write(json_data)
    else:
        print(df.to_csv(index=False, header=True))

    print()
    print("SUMMARY:")
    print(f"Found {len(card_dicts)} cards.")
    print(f"Output {len(df)} records.")


if __name__ == "__main__":
    main()
