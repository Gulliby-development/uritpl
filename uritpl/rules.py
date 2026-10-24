from uritpl.charset import RESERVED, UNRESERVED, triplet_at
from uritpl.codes import QUERY_AGAIN, QUERY_MISSING, again_text, encoded_text
from uritpl.fault import Fault
from uritpl.model import Literal
from uritpl.parse import parse_template
from uritpl.problem import Problem, sorted_problems


def find_problems(line: str) -> list[Problem]:
    """Return syntax or semantic lint problems for one complete template line."""
    try:
        items = parse_template(line)
    except Fault as fault:
        return [Problem(fault.col, fault.code, fault.text)]

    found: list[Problem] = []
    query_started = False
    changed_characters: set[str] = set()
    first_variables: dict[str, int] = {}

    for item in items:
        if isinstance(item, Literal):
            index = 0
            while index < len(item.text):
                character = item.text[index]
                if character == "?":
                    query_started = True

                if character == "%" and triplet_at(item.text, index):
                    index += 3
                    continue

                if (
                    character not in UNRESERVED
                    and character not in RESERVED
                    and character not in changed_characters
                ):
                    changed_characters.add(character)
                    found.append(
                        Problem(
                            item.col + index,
                            "UT103",
                            encoded_text(character),
                        )
                    )
                index += 1
            continue

        if item.op == "?":
            if query_started:
                found.append(Problem(item.col, "UT101", QUERY_AGAIN))
            query_started = True
        elif item.op == "&" and not query_started:
            found.append(Problem(item.col, "UT102", QUERY_MISSING))

        for spec in item.specs:
            first_col = first_variables.get(spec.name)
            if first_col is None:
                first_variables[spec.name] = spec.col
            else:
                found.append(
                    Problem(
                        spec.col,
                        "UT104",
                        again_text(spec.name, first_col),
                    )
                )

    return sorted_problems(found)
