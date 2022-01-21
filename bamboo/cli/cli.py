import argparse

from .static import handle_static


def main() -> None:
    parser = argparse.ArgumentParser(
        description="The bamboo CLI command tool."
    )
    subparsers = parser.add_subparsers()

    # static
    parser_static = subparsers.add_parser("static")
    parser_static.add_argument(
        "doc-root",
        help="Document root of the static files to be hosted.",
    )
    parser_static.add_argument("--dir-download")
    parser_static.add_argument("--files-download")
    parser_static.add_argument("--dirs-ignore")
    parser_static.add_argument("--files-ignore")
    parser_static.set_defaults(func=handle_static)

    args = parser.parse_args()
    args.func(args)
