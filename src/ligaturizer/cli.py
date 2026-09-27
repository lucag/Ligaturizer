"""Command-line entry points: `ligaturize` and `ligaturize-all`."""

import sys
from argparse import ArgumentParser
from fnmatch import fnmatch
from glob import glob

from ligaturizer import catalog
from ligaturizer.build import GlyphNameClash, NotMonospaced, build
from ligaturizer.fontforge import FontForgeNotFound


def _parser() -> ArgumentParser:
    parser = ArgumentParser(description="Add Fira Code's ligatures to a font.")
    parser.add_argument("input_font_file", help="The TTF or OTF font to add ligatures to.")
    parser.add_argument(
        "--output-dir",
        default=".",
        help="The directory to save the ligaturized font in. The actual filename"
        " will be automatically generated based on the input font name and"
        " the --prefix and --output-name flags.",
    )
    parser.add_argument(
        "--ligature-font-file",
        default="",
        metavar="PATH",
        help="The file to copy ligatures from. If unspecified, a suitable Fira Code"
        " weight is picked based on the input font's name.",
    )
    parser.add_argument(
        "--prefix", default="Liga", help="String to prefix the name of the generated font with."
    )
    parser.add_argument(
        "--output-name",
        default="",
        help="Name of the generated font. Completely replaces the original.",
    )
    parser.add_argument(
        "--glyph-namespace",
        default="",
        metavar="PREFIX",
        help="Prefix the names of glyphs copied from Fira Code, for input fonts"
        " that already have glyphs with the same names.",
    )
    return parser


def _run(**kwargs) -> None:
    try:
        build(**kwargs)
    except (FontForgeNotFound, GlyphNameClash, NotMonospaced) as e:
        sys.exit(f"error: {e}")


def ligaturize() -> None:
    _run(**vars(_parser().parse_args()))


def ligaturize_all() -> None:
    ArgumentParser(description="Ligaturize every font in the catalogue.").parse_args()

    batches = [(p, catalog.LIGATURIZED_FONT_NAME_PREFIX, None) for p in catalog.prefixed_fonts]
    batches += [(p, None, name) for p, name in catalog.renamed_fonts.items()]
    for pattern, prefix, name in batches:
        files = glob(pattern)
        if not files:
            sys.exit(f"error: pattern {pattern!r} didn't match any files.")
        for input_file in files:
            namespaces = catalog.glyph_namespaces.items()
            _run(
                input_font_file=input_file,
                output_dir=catalog.OUTPUT_DIR,
                prefix=prefix,
                output_name=name,
                glyph_namespace=next((ns for p, ns in namespaces if fnmatch(input_file, p)), ""),
            )
