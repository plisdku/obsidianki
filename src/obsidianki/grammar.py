import lark
import pprint

# g = r"""
# start: section+
# section: DISPLAYMATH non_math DISPLAYMATH
# non_math: /[^$]+/
# DISPLAYMATH: /\$\$/

# %import common.WS
# %ignore WS
# """

# example = r"""
# $$
# e^{ikx}
# $$
# $$
# 1 + 2 + 3 \textrm{ok}
# $$
# """



grammar = r"""
    start: (math | non_math)*
    non_math: /[^$]+/

    math: inline_math | display_math
    display_math: DISPLAY_MATH math_content DISPLAY_MATH
    inline_math: "$" math_content "$" trailing_punct?

    math_content: (math_char | nested_curly)*
    nested_curly: "{" (math_char | nested_curly)* "}"
    math_char: /[^${}]/

    trailing_punct: /[.,:;?!)]/

    DISPLAY_MATH: /\$\$/

    %import common.WS
"""

example = r"""
$$
e^{ikx} \quad \textrm{not $e$ but $\pi$ is relevant}
$$
"""

print(example)
print("-"*20)

parser = lark.Lark(grammar)
tree = parser.parse(example)
# pprint.pprint(tree)
print(tree.pretty())

class MyTransformer(lark.Transformer):
    def non_math(self, items):
        print(items)


MyTransformer().transform(tree)