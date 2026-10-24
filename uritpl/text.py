def plain(text: str) -> str:
    """Replace non-printable or non-ASCII code points with question marks."""
    return "".join(character if 0x20 <= ord(character) <= 0x7E else "?" for character in text)


def show(text: str) -> str:
    """Return printable text framed by double quotes."""
    return '"' + plain(text) + '"'


def plural(count: int, word: str) -> str:
    """Return a count followed by the singular or plural form of a word."""
    suffix = "" if count == 1 else "s"
    return f"{count} {word}{suffix}"


def table(header: list[str], rows: list[list[str]]) -> list[str]:
    """Format a plain-text table with two spaces between left-aligned columns."""
    column_count = len(header)
    for row in rows:
        column_count = max(column_count, len(row))

    widths = [0] * column_count
    for row in [header, *rows]:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    formatted: list[str] = []
    for row in [header, *rows]:
        cells = [
            (row[index] if index < len(row) else "").ljust(widths[index])
            for index in range(column_count)
        ]
        formatted.append("  ".join(cells).rstrip(" "))
    return formatted


def is_alpha(ch: str) -> bool:
    """Return whether ch is one ASCII letter."""
    return len(ch) == 1 and ("A" <= ch <= "Z" or "a" <= ch <= "z")


def is_digit(ch: str) -> bool:
    """Return whether ch is one ASCII digit."""
    return len(ch) == 1 and "0" <= ch <= "9"


def is_hex(ch: str) -> bool:
    """Return whether ch is one ASCII hexadecimal digit."""
    return is_digit(ch) or (len(ch) == 1 and ("A" <= ch <= "F" or "a" <= ch <= "f"))


def has_surrogate(text: str) -> bool:
    """Return whether text contains a Unicode surrogate code point."""
    return any(0xD800 <= ord(character) <= 0xDFFF for character in text)
