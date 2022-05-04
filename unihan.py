import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import IO, Optional
from zipfile import ZipFile, Path as ZPath


def parse_unihan_file(f: IO[str]):
    for line in f:
        line = line.strip()
        if not line or line[0] == "#":
            continue
        u_scalar, field, value = line.split("\t")
        scalar = int(u_scalar.removeprefix("U+"), 16)
        yield scalar, field, value


def parse_unihan_zip(path: Path):
    with ZipFile(path, "r") as zf:
        root = ZPath(zf)
        for p in root.iterdir():
            with p.open() as f:
                yield from parse_unihan_file(f)  # type: ignore


def parse_unihan_dir(path: Path):
    for p in path.iterdir():
        with p.open() as f:
            yield from parse_unihan_file(f)


def parse_unihan_db(path: Path):
    if path.is_dir():
        return parse_unihan_dir(path)
    else:
        return parse_unihan_zip(path)


### Command line utility ###


def query_unihan(path, query_scalar=None, query_field=None):
    for scalar, field, value in parse_unihan_db(path):
        if query_field is None or field in query_field:
            if query_scalar is None or scalar in query_scalar:
                print(f"U+{scalar:X} {field} = {value}")


def get_scalar(c: str):
    if c.lower().startswith(("0x", "u+")):
        return int(c[2:], 16)
    elif len(c) == 1:
        return ord(c)
    elif c.isnumeric():
        return int(c)
    else:
        import unicodedata

        try:
            c = unicodedata.lookup(c)
        except KeyError:
            return None
        else:
            return ord(c)


def download_database(target_path: Path):
    from urllib.request import urlretrieve

    UNIHAN_URL = "https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip"
    print("Downloading database...", file=sys.stderr)
    urlretrieve(UNIHAN_URL, target_path)
    print(f"Database downloaded to {target_path!s}.", file=sys.stderr)


@dataclass
class UnihanCLIArguments:
    db: str
    download_database: bool
    char: Optional[list[str]]
    field: Optional[list[str]]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
Query the Unihan database by character or field name. Print the results for the
properties matching the query, like:

  U+xxxx kFieldName = value

The database must be available either as a zip file, or extracted in a directory.""",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "db",
        nargs="?",
        default="Unihan.zip",
        help="path to the Unihan database (default: Unihan.zip in current"
        " directory; could be a zip file or a directory)",
    )
    parser.add_argument(
        "--download-database",
        action="store_true",
        help="attempts to download the latest version of the database to the given path"
        " if it doesn't exist",
    )
    query_options = parser.add_argument_group(
        "query options",
        "Add query options to filter the results. By default, no filtering is applied.",
    )
    query_options.add_argument(
        "-c",
        "--char",
        nargs="+",
        help="search for properties for the given Unicode codepoint(s) "
        "identified by numeric value or text (default: no filter)",
    )
    query_options.add_argument(
        "-f",
        "--field",
        nargs="+",
        help="search for properties with the given field name(s) "
        "(default: no filter)",
    )
    args = parser.parse_args(namespace=UnihanCLIArguments)
    path = Path(args.db)
    if args.char:
        query_scalar = [*map(get_scalar, args.char)]
    else:
        query_scalar = None
    if not path.exists() and args.download_database:
        download_database(path)
    try:
        query_unihan(path, query_scalar, args.field)
    except FileNotFoundError as err:
        print(err, file=sys.stderr)
        sys.exit(1)
