import sys

from uritpl.cli import run


class StdIo:
    """The real binary-stream implementation of the command I/O protocol."""

    def read_stdin(self) -> bytes:
        return sys.stdin.buffer.read()

    def read_file(self, path: str) -> bytes:
        with open(path, "rb") as source:
            return source.read()

    def out(self, text: str) -> None:
        sys.stdout.buffer.write(text.encode("utf-8"))

    def err(self, text: str) -> None:
        sys.stderr.buffer.write(text.encode("utf-8"))


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:], StdIo()))
