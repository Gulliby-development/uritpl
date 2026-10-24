def split_lines(text: str) -> list[str]:
    """Split at LF, dropping one CR only when it directly precedes that LF."""
    lines: list[str] = []
    start = 0
    newline = text.find("\n", start)

    while newline >= 0:
        line = text[start:newline]
        line = line.removesuffix("\r")
        lines.append(line)
        start = newline + 1
        newline = text.find("\n", start)

    if start < len(text):
        lines.append(text[start:])

    return lines
