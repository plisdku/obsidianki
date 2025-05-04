from obsidianki.convert import (
    extract_flashcard_blocks,
    get_flashcard_fields,
    find_dollar_math_substrings,
    convert_math
)

def convert_flashcard_block(block: str) -> str:
    """
    Turn a markdown flashcard block into HTML.
    """

    fields = get_flashcard_fields(block)

    for key, value in fields.items():
        if key in ("Q", "A", "AA"):
            substrings = find_dollar_math_substrings(value)

            math_blocks = []
            for start, end in substrings:
                converted_math = convert_math(value[start:end])
                math_blocks.append(converted_math)

                print(converted_math)
                
            # Replace substrings with '{MATH_PLACEHOLDER}'

            for start, end in reversed(substrings):
                value = value[:start] + "{MATH_PLACEHOLDER}" + value[end:]
            
            print(key)
            print(value)



def main():
    import argparse

    parser = argparse.ArgumentParser(description="Convert Obsidian Markdown to Anki HTML")
    parser.add_argument("input_file", help="Obsidian markdown file")
    parser.add_argument("output_file", nargs="?", default="", help="Output Anki-compatible file")
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as f:
        obsidian_text = f.read()

    blocks = extract_flashcard_blocks(obsidian_text)

    for block in blocks:
        block = convert_flashcard_block(block)
        # print(block)


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
