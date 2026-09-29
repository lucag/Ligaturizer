"""Build one Output font: the FontForge stage, then the GSUB stage (ADR 0002)."""

import json
import tempfile
from collections import Counter
from pathlib import Path

from fontTools.ttLib import TTFont

from ligaturizer.fira import ligature_source, nearest_weight
from ligaturizer.fontforge import run_stage
from ligaturizer.transplant import plan_glyphs, transplant_calt

# Printable ASCII, whose characters must all share the Cell width.
_ASCII = range(0x21, 0x7F)
# Advances may differ from the Cell width by this much, a rounding artifact
# some fonts have (e.g. Roboto Mono: 1229 and 1230).
_TOLERANCE = 1


class NotMonospaced(ValueError):
    pass


class GlyphNameClash(ValueError):
    pass


def build(
    input_font_file: str,
    output_dir: str = ".",
    ligature_font_file: str | None = None,
    prefix: str | None = None,
    output_name: str | None = None,
    glyph_namespace: str = "",
    weight: str | None = None,
) -> Path:
    """Ligaturize `input_font_file` into `output_dir`; returns the Output font's path.

    The Ligature source is `ligature_font_file` if given, else Fira Code's
    `weight`, else the Fira Code weight nearest the Input font's usWeightClass.
    """
    font = TTFont(input_font_file)
    try:
        width = cell_width(font)
    except NotMonospaced as e:
        raise NotMonospaced(f"{Path(input_font_file).name} is not monospaced: {e}") from None
    source_file = Path(
        ligature_font_file or ligature_source(weight or nearest_weight(font["OS/2"].usWeightClass))
    )
    glyphs = plan_glyphs(TTFont(source_file), glyph_namespace)

    clashes = sorted(set(glyphs.values()) & set(font.getGlyphOrder()))
    if clashes:
        raise GlyphNameClash(
            f"{input_font_file} already has glyphs named like Fira Code's"
            f" ({', '.join(clashes[:5])}...); pass --glyph-namespace to prefix them"
        )

    family_name = output_name or font["name"].getBestFamilyName()
    if prefix:
        family_name = f"{prefix} {family_name}"

    print(f"    ...using ligatures from {source_file}")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        result_file = Path(tmp) / "result.json"
        run_stage(
            "copy_glyphs",
            dict(
                input_font_file=str(input_font_file),
                output_dir=str(output_dir),
                ligature_source=str(source_file),
                glyphs=glyphs,
                cell_width=width,
                family_name=family_name,
                result_file=str(result_file),
            ),
        )
        output_file = Path(json.loads(result_file.read_text())["output_file"])

    missing = transplant_calt(output_file, source_file, glyphs)
    if missing:
        print(f"    ...dropped calt rules for {len(missing)} characters {output_file.name} lacks")
    return output_file


def cell_width(font: TTFont) -> int:
    """The Input font's Cell width; raises NotMonospaced if it has none."""
    cmap = font.getBestCmap()
    widths = Counter(font["hmtx"][cmap[c]][0] for c in _ASCII if c in cmap)
    if max(widths) - min(widths) > _TOLERANCE:
        raise NotMonospaced(
            f"printable ASCII has {len(widths)} advance widths,"
            f" from {min(widths)} to {max(widths)}, not one"
        )
    return widths.most_common(1)[0][0]
