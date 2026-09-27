"""Command-line entry points: `ligaturize` and `ligaturize-all`."""

import sys
from argparse import ArgumentParser
from glob import glob

from ligaturizer import catalog
from ligaturizer.fontforge import FontForgeNotFound, run_stage


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
        "--copy-character-glyphs",
        action="store_true",
        help="Copy glyphs for (some) individual characters from the ligature"
        " font as well. This will result in punctuation that matches the"
        " ligatures more closely, but may not fit in as well with the rest"
        " of the font.",
    )
    parser.add_argument(
        "--scale-character-glyphs-threshold",
        type=float,
        default=0.1,
        metavar="THRESHOLD",
        help="When copying character glyphs, if they differ in width from the"
        " width of the input font by at least this much, scale them"
        " horizontally to match the input font even if this noticeably"
        " changes their aspect ratio. The default (0.1) means to scale if"
        " they are at least 10%% wider or narrower. A value of 0 will scale"
        " all copied character glyphs; a value of 2 effectively disables"
        " character glyph scaling.",
    )
    parser.add_argument(
        "--prefix", default="Liga", help="String to prefix the name of the generated font with."
    )
    parser.add_argument(
        "--output-name",
        default="",
        help="Name of the generated font. Completely replaces the original.",
    )
    return parser


def _run(job: dict) -> None:
    try:
        run_stage(job)
    except FontForgeNotFound as e:
        sys.exit(f"error: {e}")


def ligaturize() -> None:
    _run(vars(_parser().parse_args()))


def ligaturize_all() -> None:
    parser = ArgumentParser(description="Ligaturize every font in the catalogue.")
    parser.add_argument("--copy-character-glyphs", action="store_true")
    args = parser.parse_args()

    copy_characters = args.copy_character_glyphs or catalog.COPY_CHARACTER_GLYPHS
    output_dir = (
        "fonts/output-with-characters" if args.copy_character_glyphs else catalog.OUTPUT_DIR
    )

    batches = [(p, catalog.LIGATURIZED_FONT_NAME_PREFIX, None) for p in catalog.prefixed_fonts]
    batches += [(p, None, name) for p, name in catalog.renamed_fonts.items()]
    for pattern, prefix, name in batches:
        files = glob(pattern)
        if not files:
            sys.exit(f"error: pattern {pattern!r} didn't match any files.")
        for input_file in files:
            _run(
                dict(
                    input_font_file=input_file,
                    output_dir=output_dir,
                    ligature_font_file=None,
                    prefix=prefix,
                    output_name=name,
                    copy_character_glyphs=copy_characters,
                    scale_character_glyphs_threshold=catalog.SCALE_CHARACTER_GLYPHS_THRESHOLD,
                )
            )
