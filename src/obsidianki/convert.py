# %%
r"""
Convert Obsidian Markdown to Anki HTML, and in reverse.

The only part of this problem that I need to solve is the conversion of the markdown.
I don't care about any images or text formatting. All I care about is the delimiters and
the punctuation.

To convert Obsidian to Anki:
 - convert Obsidian math markdown delimiters to Anki math delimiters. This means
   - $...$ is converted to \(...\)
   - $$...$$ is converted to \[...\]
   - When the character after the closing $ delimiter in Obsidian is a period, semicolon,
    parenthesis, comma, exclamation point, or question mark, it must get scooped into the
    Anki block right before the closing \). This does not apply to $$...$$ conversion.
 - To process an Obsidian markdown file, detect all pairs of sections beginning alternately
   with "Q:" and "A:" at the beginning of a line. Also detect "Addendum:". Each set of a Q,
   A and Addendum block is to be converted to a single Anki card.

Note that it is valid to include the $ character in an equation, for example, in
$$
\textrm{The $x$ axis is the horizontal axis, and $x(\textrm{wherever $x=0$})$ is the vertical axis.}
$$
The $ characters appearing within a math block must NOT be converted since they are valid
LaTeX / MathJax. So to identify an equation block in Obsidian format, we have to find the
outermost $...$ and $$...$$ delimiters correctly.

For the most part, the nested delimiters will exist within curly brace {} blocks, which themselves
can be nested. So we can use a stack to keep track of the current depth of the curly braces.
"""

from textwrap import dedent
from lark import Lark, Transformer, v_args



obsidian_grammar = r"""
    start: front_matter* (math_block | text_block)*

    front_matter: /[^\n]+/ NEWLINE*
    
    math_block: inline_math | display_math
    inline_math: "$" math_content "$" trailing_punct?
    display_math: "$$" math_content "$$"
    
    math_content: (math_char | nested_curly)*
    nested_curly: "{" (math_char | nested_curly)* "}"
    math_char: /[^${}]/
    
    text_block: /[^$]+/
    
    trailing_punct: /[.,;!?)]/ 
    
    %import common.WS
    %ignore WS
"""

@v_args(inline=True)
class ObsidianToAnkiTransformer(Transformer):
    def start(self, *items):
        return ''.join(items)
    
    def text_block(self, text):
        return str(text)
    
    def inline_math(self, *items):
        content = items[0]
        trailing = items[1] if len(items) > 1 else ""
        return f"\\({content}{trailing}\\)"
    
    def display_math(self, content):
        return f"\\[{content}\\]"
    
    def math_content(self, *items):
        return ''.join(str(item) for item in items)
    
    def nested_curly(self, *items):
        return '{' + ''.join(str(item) for item in items) + '}'
    
    def math_char(self, char):
        return str(char)
    
    def trailing_punct(self, punct):
        return str(punct)
    
def convert_obsidian_to_anki(obsidian_text):
    parser = Lark(obsidian_grammar, parser='lalr')
    transformer = ObsidianToAnkiTransformer()
    
    lines = obsidian_text.split('\n')
    cards = []
    current_card = {"Q": [], "A": [], "Addendum": []}
    current_section = None
    
    for line in lines:
        if line.startswith("Q:"):
            if current_section == "A" and current_card["Q"] and current_card["A"]:
                cards.append(current_card)
                current_card = {"Q": [], "A": [], "Addendum": []}
            current_section = "Q"
            line = line[2:].strip()
        elif line.startswith("A:"):
            current_section = "A"
            line = line[2:].strip()
        elif line.startswith("Addendum:"):
            current_section = "Addendum"
            line = line[9:].strip()
        
        if current_section:
            # Parse and transform the line
            try:
                parsed_line = parser.parse(line)
                transformed_line = transformer.transform(parsed_line)
                current_card[current_section].append(transformed_line)
            except Exception as e:
                # Fallback if parsing fails
                current_card[current_section].append(line)
    
    # Add the last card if it exists
    if current_card["Q"] and current_card["A"]:
        cards.append(current_card)
    
    # Format cards for Anki
    anki_cards = []
    for card in cards:
        question = "<br>".join(card["Q"])
        answer = "<br>".join(card["A"])
        if card["Addendum"]:
            answer += "<hr><i>" + "<br>".join(card["Addendum"]) + "</i>"
        anki_cards.append({"front": question, "back": answer})
    
    return anki_cards


# %%

test_input = r"""
# Boas Chapter 12

Today's date

some header fluff

Q: What is $1+1$?
A: $2$.

Q: What is $2+2$?
A:
$4$.
AA: Extra supplement
"""

test_output = {
    "Q": [
        "What is \\(1+1\\)?"
    ],
    "A": [
        "\\(2\\)."
    ],
    "Addendum": [
        "Extra supplement"
    ]
}


obsidian_text = dedent(test_input)

# %%

def test_convert_obsidian_to_anki():
    obsidian_text = dedent(test_input)
    expected_output = [test_output]
    
    result = convert_obsidian_to_anki(obsidian_text)

    print(result)
    
    assert len(result) == len(expected_output), "Number of cards does not match"
    for i, card in enumerate(result):
        assert card["front"] == expected_output[i]["Q"][0], f"Front mismatch at card {i}"
        assert card["back"] == expected_output[i]["A"][0], f"Back mismatch at card {i}"
        if "Addendum" in expected_output[i]:
            assert card["back"].endswith("<hr><i>" + "<br>".join(expected_output[i]["Addendum"]) + "</i>"), f"Addendum mismatch at card {i}"

# test_convert_obsidian_to_anki()

# %%

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
            f.write(f"{card['front']}\t{card['back']}\n")
    
    print(f"Converted {len(anki_cards)} cards from {args.input_file} to {args.output_file}")

if __name__ == "__main__":
    main()