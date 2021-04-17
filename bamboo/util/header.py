from typing import Tuple


def make_header(name: str, value: str, **params: str) -> Tuple[str, str]:
    """Make pair of header field and its value with other directives.

    Args:
        name: Field name of the header.
        value: Value of the field.
        **params: Directives added to the field.
    """
    params = [f"; {header}={val}" for header, val in params.items()]
    params = "".join(params)
    return (name, value + params)
