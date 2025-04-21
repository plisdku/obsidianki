import re
import pathlib
import textwrap
import random

from obsidianki.my_emoji import EMOJI

def split_between_matches(contents, matches):
    """
    Split the contents between the matches.
    """
    match_contents = []
    match_contents.append(contents[:matches[0].start()])
    for idx in range(len(matches)-1):
        match_content = contents[matches[idx].end():matches[idx+1].start()]
        match_contents.append(match_content)
    match_contents.append(contents[matches[-1].end():])
    return match_contents


def split_sections(contents):
    """
    Split the contents into sections based on the tags in the text.
    """
    # Define a regex pattern to match the tags
    tag_pattern = re.compile(r"^\s?(✅)?\s?([A-Za-z ]+):", re.MULTILINE)

    # Find all matches for the tag pattern
    matches = list(tag_pattern.finditer(contents))

    # Filter the matches to only include valid tags
    valid_tags = ["Q", "A", "AA", "Addendum", "Book", "Page", "Chapter", "Tags"]
    matches = [m for m in matches if m.group(2) in valid_tags]

    match_contents = split_between_matches(contents, matches)

    return list(zip(matches, match_contents[1:]))


def convert_math_delims(section: str) -> str:
    r"""
    Convert math delimiters in the section.
        - $...$ becomes \(...\)
        - $$...$$ becomes \[...\]
        
    Args:
        section (str): The section to convert.
    Returns:
        str: The converted section.
    """

    delim_pattern = re.compile(r"(\$+|[{}])", re.MULTILINE)

    delims = list(delim_pattern.finditer(section))

    if not delims:
        return section

    betweens = split_between_matches(section, delims)

    out = []
    out.append(betweens[0])

    curly_brace_depth = 0
    math_delim_depth = 0

    for delim_match, between in zip(delims, betweens[1:]):
        delim = delim_match.group(0)
        if delim == "$":
            if curly_brace_depth == 0:
                if math_delim_depth == 0:
                    delim = r"\("
                    math_delim_depth += 1
                else:
                    delim = r"\)"
                    math_delim_depth -= 1
        elif delim == "$$":
            if curly_brace_depth == 0:
                if math_delim_depth == 0:
                    delim = r"\["
                    math_delim_depth += 1
                else:
                    delim = r"\]"
                    math_delim_depth -= 1
        elif delim == "{":
            curly_brace_depth += 1
        elif delim == "}":
            curly_brace_depth -= 1
        else:
            assert "unexpected token"
        
        out.append(delim)
        out.append(between)

    return "".join(out)


fname = pathlib.Path("/Users/paul/Documents/Obsidian Vault/Math notes/Atakishiyev, On Classical Orthogonal Polynomials.md").absolute()
with open(fname) as fh:
    contents = fh.read()

def convert_obsidian_to_anki(contents: str) -> str:
    tags = {
        "Q": "",
        "A": "",
        "AA": "",
        "Addendum": "",
        "Book": "",
        "Page": "",
        "Chapter": "",
        "Tags": ""
    }

    out_cards = []
    card = {}
    for token, section in split_sections(contents):

        emoji, token_type = token.groups()
        if emoji == "✅":
            pass
        value = convert_math_delims(section.strip())
        tags[token_type] = value.strip()

        if token_type == "Q":
            card = {}
            out_cards.append(card)
            card["Q"] = tags["Q"]
            card["Book"] = tags["Book"]
            card["Chapter"] = tags["Chapter"]
            card["Page"] = tags["Page"]
        else:
            card[token_type] = tags[token_type]
    
    return out_cards


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert Obsidian Markdown to Anki HTML")
    parser.add_argument("input_file", help="Obsidian markdown file")
    parser.add_argument("output_file", help="Output Anki-compatible file")
    args = parser.parse_args()
    
    with open(args.input_file, 'r', encoding='utf-8') as f:
        obsidian_text = f.read()
    
    anki_cards = convert_obsidian_to_anki(obsidian_text)

    # Write to output file in a format Anki can import
    with open(args.output_file, 'w', encoding='utf-8') as f:
        for card in anki_cards:
            if "AA" in card:
                answer = card["A"] + "\n\n" + random.choice(EMOJI) + "\n\n" + card["AA"]
            else:
                answer = card["A"]
            
            card_text = f"Q:\n{card['Q']}\nA:\n{answer}\nBook:\n{card['Book']}\nChapter:\n{card['Chapter']}\nPage:\n{card['Page']}\n"
            f.write(card_text)
            f.write("-"*20 + "\n")
    
    # print(f"Converted {len(anki_cards)} cards from {args.input_file} to {args.output_file}")


if __name__ == "__main__":
    main()