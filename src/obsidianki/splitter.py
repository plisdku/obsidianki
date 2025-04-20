import re
import pathlib

fname = pathlib.Path("/Users/paul/Documents/Obsidian Vault/Math notes/Atakishiyev, On Classical Orthogonal Polynomials.md").absolute()
with open(fname) as fh:
    contents = fh.read()


def split_between_matches(contents, matches):
    """
    Split the contents between the matches.
    """
    match_contents = []
    match_contents.append(contents[:matches[0].start()].strip())
    for idx in range(len(matches)-1):
        match_content = contents[matches[idx].end():matches[idx+1].start()].strip()
        match_contents.append(match_content)
    match_contents.append(contents[matches[-1].end():].strip())
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
    valid_tags = ["Q", "A", "Addendum", "Book", "Page", "Chapter", "Tags"]
    matches = [m for m in matches if m.group(2) in valid_tags]

    match_contents = split_between_matches(contents, matches)

    return list(zip(matches, match_contents))

# print(split_sections(contents))
# exit(0)


eqn = r"""a three-term recurrence relation of the form
$$
x p_n(x) = A_n p_{n+1}(x) + B_n p_n(x) + C_n p_{n-1}(x),
$$
where $p_{-1}(x) = 0$, $p_0(x) = 1$, $A_n, B_n, C_n$ are real, and $A_n C_{n+1} > 0$ for $n = 0, 1, 2, 3, \dots$.
Orthogonality may be defined with respect to a weight function $w(x)$, either on the real line,
$$
\int_{-\infty}^\infty p_m(x) p_n(x) w(x) \, dx = 0, \quad m \ne n,
$$
or discrete,
$$
\sum_{j=0}^\infty p_m(x_j) p_n(x_j) w_j = 0, \quad m \ne n.
$$
"""

delim_pattern = re.compile(r"(\$+|[{}])", re.MULTILINE)

delims = list(delim_pattern.finditer(eqn))
mm = split_between_matches(eqn, delims)
print(mm)

