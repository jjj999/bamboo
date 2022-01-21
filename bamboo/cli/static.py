from argparse import Namespace
import typing as t
import wsgiref


def handle_option_dir_download(arg: str) -> str:
    pass


def handle_option_files_download(arg: str) -> t.Tuple[str, ...]:
    pass


def handle_option_dirs_ignore(arg: str) -> t.Tuple[str, ...]:
    pass


def handle_option_files_ignore(arg: str) -> t.Tuple[str, ...]:
    pass


def handle_option_address(arg: str) -> t.Tuple[str, int]:
    pass


def serve_static_contents(
    doc_root: str,
    dir_download: t.Optional[str] = None,
    files_download: t.Tuple[str, ...] = (),
    dirs_ignore: t.Tuple[str, ...] = (),
    files_ignore: t.Tuple[str, ...] = (),
) -> None:
    pass


def handle_static(args: Namespace) -> None:
    pass
