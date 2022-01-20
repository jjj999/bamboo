import glob as _glob
import os
import typing as t


class DirContext:

    def __init__(self, loc: str) -> None:
        self._loc = loc
        self._current = os.getcwd()

    def __enter__(self) -> None:
        os.chdir(self._loc)

    def __exit__(self, tyep, value, traceback) -> None:
        os.chdir(self._current)


def iglob(
    pattern: str,
    recursive: bool = False,
    remove_dir: bool = False,
    root_dir: t.Optional[str] = None,
) -> t.Generator[str, None, None]:
    if root_dir is None:
        root_dir = os.getcwd()

    with DirContext(root_dir):
        for item in _glob.iglob(pattern, recursive=recursive):
            if remove_dir and os.path.isdir(item):
                continue
            yield item

def glob(
    pattern: str,
    recursive: bool = False,
    remove_dir: bool = False,
    root_dir: t.Optional[str] = None,
) -> t.List[str]:
    return list(iglob(
        pattern,
        recursive=recursive,
        remove_dir=remove_dir,
        root_dir=root_dir,
    ))
