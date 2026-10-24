from uritpl.text import is_hex

UNRESERVED = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
RESERVED = frozenset(":/?#[]@!$&'()*+,;=")


def is_unreserved(ch: str) -> bool:
    """Return whether ch is an RFC 6570 unreserved character."""
    return ch in UNRESERVED


def is_reserved(ch: str) -> bool:
    """Return whether ch is an RFC 6570 reserved character."""
    return ch in RESERVED


def triplet_at(text: str, index: int) -> bool:
    """Return whether text has a percent triplet starting at index."""
    return (
        0 <= index
        and index + 2 < len(text)
        and text[index] == "%"
        and is_hex(text[index + 1])
        and is_hex(text[index + 2])
    )
