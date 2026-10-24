from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from uritpl.fault import Failure
from uritpl.text import plain


class Io(Protocol):
    """The byte-input and text-output boundary used by commands."""

    def read_stdin(self) -> bytes:
        """Read standard input as bytes."""
        ...

    def read_file(self, path: str) -> bytes:
        """Read a named file as bytes."""
        ...

    def out(self, text: str) -> None:
        """Append text to standard output."""
        ...

    def err(self, text: str) -> None:
        """Append text to standard error."""
        ...


@dataclass
class Source:
    """Decoded input text with its safe display name."""

    display: str
    text: str


class Inputs:
    """Read files and standard input through one strict UTF-8 boundary."""

    def __init__(self, io: Io) -> None:
        self.io = io
        self._stdin_named = False

    def read(self, arg: str) -> Source:
        is_stdin = arg == "-"
        if is_stdin:
            display = "<stdin>"
            if self._stdin_named:
                raise Failure("standard input is named twice")
            self._stdin_named = True
        else:
            display = plain(arg)

        try:
            data = self.io.read_stdin() if is_stdin else self.io.read_file(arg)
        except OSError as error:
            raise Failure(f"{display}: cannot read the file") from error

        try:
            text = data.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise Failure(f"{display}: input is not valid UTF-8") from error
        return Source(display, text)


class MemIo:
    """An in-memory implementation of the command I/O protocol."""

    def __init__(self, stdin: bytes = b"", files: Mapping[str, bytes] | None = None) -> None:
        self.stdin = stdin
        self.files = {} if files is None else files
        self.stdout = ""
        self.stderr = ""

    def read_stdin(self) -> bytes:
        return self.stdin

    def read_file(self, path: str) -> bytes:
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def out(self, text: str) -> None:
        self.stdout += text

    def err(self, text: str) -> None:
        self.stderr += text
