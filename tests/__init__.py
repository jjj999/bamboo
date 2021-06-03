import os
from pathlib import Path


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


def make_bigdata() -> None:
    if not os.path.isfile(PATH_BIGDATA_1KB):
        with open(PATH_BIGDATA_1KB, "wb") as f_1k:
            f_1k.write(os.getrandom(10**3))

    if not os.path.isfile(PATH_BIGDATA_1MB):
        with open(PATH_BIGDATA_1MB, "wb") as f_1m:
            with open(PATH_BIGDATA_1KB, "rb") as f_1k:
                data_1k = f_1k.read()

            for _ in range(10**3):
                f_1m.write(data_1k)

    if not os.path.isfile(PATH_BIGDATA_1GB):
        with open(PATH_BIGDATA_1GB, "wb") as f_1g:
            with open(PATH_BIGDATA_1MB, "rb") as f_1m:
                data_1m = f_1m.read()

            for _ in range(10**3):
                f_1g.write(data_1m)


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


make_bigdata()
