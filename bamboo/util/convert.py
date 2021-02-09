

import base64
from typing import Dict, List, Union


def encode_binary(data: Union[bytes, bytearray]) -> str:
    return base64.b64encode(data).decode()


def decode2binary(data: str) -> bytes:
    return base64.b64decode(data.encode())


def encode_base64_string(data: str) -> str:
    return encode_binary(data.encode())


def unparse_qs(query: Dict[str, List[str]]) -> str:
    params = []
    for key, vals in query.items():
        repr_vals = ",".join(vals)
        params.append("=".join((key, repr_vals)))
    return "&".join(params)
