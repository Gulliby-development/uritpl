from uritpl.io import Inputs, Io
from uritpl.lines import split_lines
from uritpl.options import need, parse
from uritpl.problem import render
from uritpl.rules import find_problems
from uritpl.text import plural

USAGE = "check FILE..."


def run_check(args: list[str], io: Io) -> int:
    """Check all named files and report only after every input is read."""
    parsed = parse(args, [])
    need(USAGE, parsed.args, 1, -1)

    inputs = Inputs(io)
    output_lines: list[str] = []
    template_count = 0
    problem_count = 0

    for argument in parsed.args:
        source = inputs.read(argument)
        for line_number, line in enumerate(split_lines(source.text), start=1):
            if line == "":
                continue
            template_count += 1
            problems = find_problems(line)
            problem_count += len(problems)
            output_lines.extend(
                render(source.display, line_number, problem) for problem in problems
            )

    output_lines.append(
        f"{plural(template_count, 'template')} checked, {plural(problem_count, 'problem')}"
    )
    io.out("\n".join(output_lines) + "\n")
    return 1 if problem_count else 0
