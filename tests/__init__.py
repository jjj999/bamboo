import os
import socket
from pathlib import Path
from typing import NamedTuple


NAME_IMAGE = "elephant.jpg"
NAME_BIGDATA_1KB = "bigdata_1kb"
NAME_BIGDATA_1MB = "bigdata_1mb"
NAME_BIGDATA_1GB = "bigdata_1gb"

DIR_TESTS = str(Path(__file__).parent)
DIR_RES = os.path.join(DIR_TESTS, "res")
PATH_IMAGE = os.path.join(DIR_RES, NAME_IMAGE)
PATH_BIGDATA_1KB = os.path.join(DIR_RES, NAME_BIGDATA_1KB)
PATH_BIGDATA_1MB = os.path.join(DIR_RES, NAME_BIGDATA_1MB)
PATH_BIGDATA_1GB = os.path.join(DIR_RES, NAME_BIGDATA_1GB)


class TestDataPaths(NamedTuple):
    small: Path
    medium: Path
    large: Path


def make_test_data(directory: Path, include_large: bool = False) -> TestDataPaths:
    """Create transfer-test data on demand in ``directory``.

    The large file is sparse on filesystems that support sparse files. Reading it
    still transfers the full 1 GB, while setup does not write 1 GB to disk.
    """
    directory.mkdir(parents=True, exist_ok=True)
    paths = TestDataPaths(
        directory / NAME_BIGDATA_1KB,
        directory / NAME_BIGDATA_1MB,
        directory / NAME_BIGDATA_1GB,
    )
    data_1kb = bytes(range(250)) * 4
    paths.small.write_bytes(data_1kb)
    with paths.medium.open("wb") as medium:
        for _ in range(1000):
            medium.write(data_1kb)
    if include_large:
        with paths.large.open("wb") as large:
            large.truncate(10**9)
    return paths


def make_bigdata(include_large: bool = True) -> None:
    """Create the legacy test resources explicitly, without import side effects."""
    make_test_data(Path(DIR_RES), include_large=include_large)


def get_unused_ports(count: int = 1) -> tuple[int, ...]:
    """Return ports that were available together at the time of selection."""
    sockets: list[socket.socket] = []
    try:
        for _ in range(count):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("127.0.0.1", 0))
            sockets.append(sock)
        return tuple(sock.getsockname()[1] for sock in sockets)
    finally:
        for sock in sockets:
            sock.close()


def get_unused_port() -> int:
    return get_unused_ports()[0]


def get_fname(fpath: str) -> str:
    return fpath.split(".")[0]


def get_log_name(fpath: str, *suffix: str) -> str:
    fname = [get_fname(fpath)]
    fname.extend(suffix)
    return f"{'_'.join(fname)}.log"


def get_client_log_name(fpath: str, *suffix: str) -> str:
    fname = [get_fname(fpath)]
    fname.extend(suffix)
    return f"{'_'.join(fname)}_client.log"
