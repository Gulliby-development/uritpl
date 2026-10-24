from collections.abc import Callable

from uritpl.check import USAGE as CHECK_USAGE
from uritpl.check import run_check
from uritpl.cmd_encode import USAGE as ENCODE_USAGE
from uritpl.cmd_encode import run_encode
from uritpl.cmd_expand import USAGE as EXPAND_USAGE
from uritpl.cmd_expand import run_expand
from uritpl.cmd_explain import USAGE as EXPLAIN_USAGE
from uritpl.cmd_explain import run_explain
from uritpl.cmd_names import USAGE as NAMES_USAGE
from uritpl.cmd_names import run_names
from uritpl.cmd_trace import USAGE as TRACE_USAGE
from uritpl.cmd_trace import run_trace
from uritpl.fault import Failure
from uritpl.io import Io
from uritpl.text import show

COMMANDS: dict[str, tuple[str, Callable[[list[str], Io], int]]] = {
    "expand": (EXPAND_USAGE, run_expand),
    "trace": (TRACE_USAGE, run_trace),
    "explain": (EXPLAIN_USAGE, run_explain),
    "names": (NAMES_USAGE, run_names),
    "encode": (ENCODE_USAGE, run_encode),
    "check": (CHECK_USAGE, run_check),
}

USAGE = "\n".join(f"usage: uritpl {usage}" for usage, _run in COMMANDS.values()) + "\n"


def run(argv: list[str], io: Io) -> int:
    """Dispatch one command and translate user-facing failures at the CLI boundary."""
    try:
        if not argv:
            raise Failure("missing command (expand, trace, explain, names, encode or check)")
        if argv == ["--help"]:
            io.out(USAGE)
            return 0

        command = COMMANDS.get(argv[0])
        if command is None:
            raise Failure(f"unknown command {show(argv[0])}")
        return command[1](argv[1:], io)
    except Failure as failure:
        io.err(f"uritpl: {failure.message}\n")
        return 2
