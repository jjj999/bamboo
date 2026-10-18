import typing as t


def make_header(name: str, value: str, **params: str) -> t.Tuple[str, str]:
    """Make pair of header field and its value with other directives.

    Args:
        name: Field name of the header.
        value: Value of the field.
        **params: Directives added to the field.
    """
    directives = [f"; {header}={val}" for header, val in params.items()]
    suffix = "".join(directives)
    return (name, value + suffix)
