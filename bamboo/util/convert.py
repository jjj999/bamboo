import base64
import typing as t


__all__ = [
    "decode2binary",
    "encode_binary",
    "encode_base64_string",
    "unparse_qs",
]


def encode_binary(data: t.Union[bytes, bytearray]) -> str:
    return base64.b64encode(data).decode()


def encode_base64_string(data: str) -> str:
    return encode_binary(data.encode())


def decode2binary(data: str) -> bytes:
    return base64.b64decode(data.encode())


def unparse_qs(query: t.Dict[str, t.List[str]]) -> str:
    params = []
    for key, vals in query.items():
        repr_vals = ",".join(vals)
        params.append("=".join((key, repr_vals)))
    return "&".join(params)
