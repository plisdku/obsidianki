from obsidianki.convert import (
    extract_flashcard_blocks,
)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Convert Obsidian Markdown to Anki HTML")
    parser.add_argument("input_file", help="Obsidian markdown file")
    parser.add_argument("output_file", nargs="?", default="", help="Output Anki-compatible file")
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as f:
        obsidian_text = f.read()

    blocks = extract_flashcard_blocks(obsidian_text)

    print("\n-----\n".join(blocks))

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
