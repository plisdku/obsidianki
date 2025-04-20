import re
import pathlib

fname = pathlib.Path("/Users/paul/Documents/Obsidian Vault/Math notes/Atakishiyev, On Classical Orthogonal Polynomials.md").absolute()
with open(fname) as fh:
    contents = fh.read()


def split_sections(contents):
    """
    Split the contents into sections based on the tags in the text.
    """
    # Define a regex pattern to match the tags
    tag_pattern = re.compile(r"^\s?(✅)?\s?([A-Za-z ]+):", re.MULTILINE)

    # Find all matches for the tag pattern
    matches = list(tag_pattern.finditer(contents))

    # Filter the matches to only include valid tags
    valid_tags = ["Q", "A", "Addendum", "Book", "Page", "Chapter", "Tags"]
    matches = [m for m in matches if m.group(2) in valid_tags]

    # Split the contents into sections based on the matches
    match_contents = []
    for idx in range(len(matches)-1):
        match_content = contents[matches[idx].end():matches[idx+1].start()].strip()
        match_contents.append(match_content)
    match_contents.append(contents[matches[-1].end():].strip())

    return list(zip(matches, match_contents))

print(split_sections(contents))
exit(0)


delim_pattern = re.compile(r"(\$+|[{}])", re.MULTILINE)

mm = list(delim_pattern.finditer(contents))
for m in mm:
    print(m)