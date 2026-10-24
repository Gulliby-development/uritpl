from uritpl.fault import Fault
from uritpl.model import Varspec
from uritpl.text import is_alpha, is_digit, is_hex


def parse_varspec(text: str, offset: int) -> Varspec:
    """Parse one variable specification starting at a template offset."""
    index = 0
    while index < len(text):
        character = text[index]
        if is_alpha(character) or is_digit(character) or character == "_" or character == ".":
            index += 1
        elif character == "%":
            if index + 2 >= len(text) or not is_hex(text[index + 1]) or not is_hex(text[index + 2]):
                raise Fault("UT005", offset + 1)
            index += 3
        else:
            break

    name = text[:index]
    if not name or name[0] == "." or name[-1] == "." or ".." in name:
        raise Fault("UT005", offset + 1)

    if index < len(text) and text[index] not in ":*":
        raise Fault("UT005", offset + 1)

    if index == len(text):
        return Varspec(name, "", 0, offset + 1)

    modifier_col = offset + index + 1
    if text[index] == "*":
        if index + 1 != len(text):
            raise Fault("UT006", modifier_col)
        return Varspec(name, "explode", 0, offset + 1)

    digits = text[index + 1 :]
    if (
        not 1 <= len(digits) <= 4
        or digits[0] < "1"
        or digits[0] > "9"
        or any(not is_digit(digit) for digit in digits)
    ):
        raise Fault("UT006", modifier_col)
    return Varspec(name, "prefix", int(digits), offset + 1)
