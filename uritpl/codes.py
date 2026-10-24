from uritpl.text import show

QUERY_AGAIN = 'query already started: use "&" instead of "?"'
QUERY_MISSING = 'no query started before this: use "?" instead of "&"'


def encoded_text(ch: str) -> str:
    """Describe the percent-encoding of one literal code point."""
    codepoint = f"U+{ord(ch):04X}"
    return f"literal character {codepoint} will be percent-encoded"


def again_text(name: str, first_col: int) -> str:
    """Describe a variable name repeated later in a template."""
    return f"variable {show(name)} appears again (first at column {first_col})"
