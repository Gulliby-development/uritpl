Value = str | list[str] | dict[str, str]


def is_undefined(value: Value | None) -> bool:
    """Return whether a supported variable value is undefined."""
    return value is None or (isinstance(value, (list, dict)) and not value)


def kind_of(value: Value) -> str:
    """Return the classification of a supported variable value."""
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "object"
    raise TypeError("unsupported variable value")
