from uritpl.fault import Failure
from uritpl.io import Io
from uritpl.options import need, parse
from uritpl.percent import encode
from uritpl.text import has_surrogate, show

USAGE = "encode [--reserved] TEXT"


def run_encode(args: list[str], io: Io) -> int:
    parsed = parse(args, {"--reserved"})
    need(USAGE, parsed.args, 1, 1)
    text = parsed.args[0]
    if has_surrogate(text):
        raise Failure(f"invalid text {show(text)}")

    output = encode(text, "--reserved" in parsed.flags)
    io.out(output)
    return 0
