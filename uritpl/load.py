import json

from uritpl.fault import Failure
from uritpl.io import Source
from uritpl.text import has_surrogate, show
from uritpl.value import Value

_NUMBER = object()


def _number_token(token: str) -> object:
    """Keep numeric syntax distinguishable without converting its contents."""
    return _NUMBER


def _reject_constant(token: str) -> object:
    """Reject Python's non-standard NaN and infinity extensions."""
    raise ValueError(token)


def _ordered_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Keep the first occurrence's position while retaining each last value."""
    return dict(pairs)


def _invalid_json(display: str) -> Failure:
    return Failure(f"{display}: not valid JSON")


def _unsupported(display: str, name: str) -> Failure:
    return Failure(f"{display}: variable {show(name)}: unsupported value")


def _invalid_text(display: str, name: str) -> Failure:
    return Failure(f"{display}: variable {show(name)}: invalid text")


def _validate_value(display: str, name: str, value: object) -> Value:
    if isinstance(value, str):
        if has_surrogate(value):
            raise _invalid_text(display, name)
        return value

    if isinstance(value, list):
        result: list[str] = []
        for member in value:
            if not isinstance(member, str):
                raise _unsupported(display, name)
            if has_surrogate(member):
                raise _invalid_text(display, name)
            result.append(member)
        return result

    if isinstance(value, dict):
        result: dict[str, str] = {}
        for key, member in value.items():
            if not isinstance(key, str):
                raise _unsupported(display, name)
            if has_surrogate(key):
                raise _invalid_text(display, name)
            if not isinstance(member, str):
                raise _unsupported(display, name)
            if has_surrogate(member):
                raise _invalid_text(display, name)
            result[key] = member
        return result

    raise _unsupported(display, name)


def load_variables(source: Source) -> dict[str, Value]:
    """Parse and validate an ordered JSON object of template variables."""
    text = source.text.removeprefix("\ufeff")
    try:
        document: object = json.loads(
            text,
            parse_int=_number_token,
            parse_float=_number_token,
            parse_constant=_reject_constant,
            object_pairs_hook=_ordered_object,
        )
    except (ValueError, RecursionError, MemoryError, OverflowError) as error:
        raise _invalid_json(source.display) from error

    if not isinstance(document, dict):
        raise Failure(f"{source.display}: variables must be a JSON object")

    variables: dict[str, Value] = {}
    for name, value in document.items():
        if has_surrogate(name):
            raise _invalid_text(source.display, name)
        if value is None:
            continue
        variables[name] = _validate_value(source.display, name, value)
    return variables
