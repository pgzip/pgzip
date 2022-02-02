"""This module provide a simple replacement of Python internal gzip module
to provide a multiprocessing solution for gzip compression/decompression.

License: MIT LICENSE
Copyright (c) 2019 Vincent Li

"""


import sys
from argparse import ArgumentParser
from contextlib import contextmanager
from pathlib import Path
from shutil import copyfileobj
from traceback import format_exc

from .pgzip import PgzipFile


def main():

    # Utility function to help open files with context manager
    # Return stdin/stdout if the filename is '-'
    @contextmanager
    def smart_open(file: str, mode: str, *args, **kwargs):
        if file == "-":
            if "w" in mode:
                yield sys.stdout.buffer
            else:
                yield sys.stdin.buffer
            return
        with open(file, mode, *args, **kwargs) as fh:
            yield fh

    parser = ArgumentParser()
    parser.add_argument("input", help="Input file or '-' for stdin")
    parser.add_argument(
        "-o",
        "--output",
        help="Output file or '-' for stdout (Default: Input file with 'gz' extension or stdout)",
    )
    parser.add_argument(
        "-f",
        "--filename",
        default="",
        help="Name for the original file when compressing",
    )
    parser.add_argument(
        "-d", "--decompress", action="store_true", help="Decompress instead of compress"
    )
    parser.add_argument(
        "-l",
        "--compression-level",
        default=9,
        type=int,
        choices=range(10),  # 0-9
        help="Compression level; 0 = no compression (Default: 9)",
        metavar="{0-9}",
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        help="Number of threads to use (Default: Determine automatically)",
    )
    parser.add_argument(
        "-b",
        "--blocksize",
        type=int,
        help="Block size to use (Default: Determine 100MB)",
        default=10 ** 8,
    )
    args = parser.parse_args()

    # Parse name from input file if output file is not specified
    if args.output is None:
        if args.input == "-":
            args.output = "-"
        elif args.decompress:
            input_path = Path(args.input)
            if input_path.suffix == ".gz":
                args.output = input_path.name[:-3]
            else:
                args.output = input_path.name
        else:
            args.output = f"{Path(args.input).name}.gz"

    if "-" not in (args.input, args.output):
        try:
            if Path(args.input).samefile(args.output):
                print(
                    "Error: Input and output cannot be the same file", file=sys.stderr
                )
                sys.exit(1)
        except OSError:
            pass

    if not args.filename:
        if args.input != "-":
            args.filename = Path(args.input).name
        elif args.output != "-":
            args.filename = Path(args.output).name

    try:
        with smart_open(args.input, "rb") as in_fh, smart_open(
            args.output, "wb"
        ) as out_fh:
            if args.decompress:
                with PgzipFile(
                    mode="rb",
                    compresslevel=args.compression_level,
                    fileobj=in_fh,
                    thread=args.threads,
                ) as pgzip_fh:
                    copyfileobj(pgzip_fh, out_fh)
                    out_fh.flush()
            else:
                with PgzipFile(
                    filename=args.filename,
                    mode="wb",
                    compresslevel=args.compression_level,
                    fileobj=out_fh,
                    thread=args.threads,
                    blocksize=args.blocksize,
                ) as pgzip_fh:
                    copyfileobj(in_fh, pgzip_fh)
                    pgzip_fh.flush()
    except Exception:
        exc_info = sys.exc_info()
        if exc_info[1]:
            print(f"{exc_info[0].__name__}: {exc_info[1]}", file=sys.stderr)
        else:
            print(format_exc(), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("KeyboardInterrupt", file=sys.stderr)
        sys.exit(1)
