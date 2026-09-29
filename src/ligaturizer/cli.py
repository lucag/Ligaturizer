"""Command-line entry points: `ligaturize` and `ligaturize-all`."""

import sys
from argparse import ArgumentParser
from fnmatch import fnmatch
from glob import glob

from ligaturizer import catalog
from ligaturizer.build import GlyphNameClash, NotMonospaced, build
from ligaturizer.fira import WEIGHTS
from ligaturizer.fontforge import FontForgeNotFound
from ligaturizer.selection import SELECTION_FILE, SelectionError


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
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--weight",
        choices=list(WEIGHTS),
        help="The Fira Code weight to copy ligatures from. If unspecified, the weight"
        " nearest the input font's declared weight (usWeightClass) is picked.",
    )
    source.add_argument(
        "--ligature-font-file",
        default="",
        metavar="PATH",
        help="A font file to copy ligatures from, instead of a Fira Code weight.",
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
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="List each character Fira Code's rules mention that the input font lacks.",
    )
    parser.add_argument(
        "--copy-character-glyphs",
        action="store_true",
        help="Also copy Fira Code's glyphs for the characters listed under copy_characters"
        " in the Ligature selection. Punctuation then matches the ligatures more closely,"
        " but may not fit in as well with the rest of the font.",
    )
    parser.add_argument(
        "--scale-character-glyphs-threshold",
        type=float,
        default=catalog.SCALE_CHARACTER_GLYPHS_THRESHOLD,
        metavar="THRESHOLD",
        help="When copying character glyphs, scale those whose width differs from the"
        " input font's by at least this fraction horizontally to fit, and center the"
        " rest. The default (%(default)s) scales those at least 10%% wider or narrower;"
        " 0 scales all of them, and 2 none.",
    )
    parser.add_argument(
        "--selection",
        dest="selection_file",
        default=str(SELECTION_FILE),
        metavar="PATH",
        help="The Ligature selection: ligatures to require or exclude (default: %(default)s).",
    )
    return parser


def _run(**kwargs) -> None:
    try:
        build(**kwargs)
    except (FontForgeNotFound, GlyphNameClash, NotMonospaced, SelectionError) as e:
        sys.exit(f"error: {e}")


def ligaturize() -> None:
    _run(**vars(_parser().parse_args()))


def ligaturize_all() -> None:
    parser = ArgumentParser(description="Ligaturize every font in the catalogue.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="List each character Fira Code's rules mention that an input font lacks.",
    )
    parser.add_argument(
        "--copy-character-glyphs",
        action="store_true",
        help="Build the variant that also copies character glyphs, into"
        f" {catalog.OUTPUT_DIR_WITH_CHARACTERS}.",
    )
    args = parser.parse_args()
    output_dir = (
        catalog.OUTPUT_DIR_WITH_CHARACTERS if args.copy_character_glyphs else catalog.OUTPUT_DIR
    )

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
                output_dir=output_dir,
                prefix=prefix,
                output_name=name,
                glyph_namespace=next((ns for p, ns in namespaces if fnmatch(input_file, p)), ""),
                verbose=args.verbose,
                copy_character_glyphs=args.copy_character_glyphs,
                scale_character_glyphs_threshold=catalog.SCALE_CHARACTER_GLYPHS_THRESHOLD,
            )
