from uritpl.text import show


class Failure(Exception):
    """A user-facing failure with an unprefixed diagnostic message."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class Fault(Exception):
    """A template syntax fault with a stable code and source column."""

    def __init__(self, code: str, col: int, arg: str = "") -> None:
        self.code = code
        self.col = col
        self.arg = arg
        super().__init__(self.text)

    @property
    def text(self) -> str:
        if self.code == "UT004":
            return f"reserved operator {show(self.arg)}"
        messages = {
            "UT001": "unclosed expression",
            "UT002": 'unmatched "}"',
            "UT003": "empty expression",
            "UT005": "bad variable name",
            "UT006": "bad modifier",
        }
        return messages[self.code]
