# The FontForge stage: copies glyphs from the Ligature
# source into the Input font, fitted to its Cell width, renames the font and
# saves it. The uv side then transplants the calt lookups (ADR 0002).
import json

import fontforge
import psMat
from naming import update_font_metadata


def copy_glyphs(
    input_font_file,
    output_dir,
    ligature_source,
    glyphs,
    cell_width,
    family_name,
    result_file,
    characters=(),
    scale_threshold=0.1,
):
    """Copy `glyphs` ({ligature source name: output name}) and save the Output font.

    `characters` lists [ligature source name, code point] pairs whose glyphs
    replace the Input font's own, width-corrected with `scale_threshold`.
    """
    font = fontforge.open(input_font_file)
    update_font_metadata(font, family_name)

    source = fontforge.open(ligature_source)
    source.em = font.em  # uniform scale to the Input font's em
    horizontal_scale = float(cell_width) / source[ord("m")].width

    print(f"    ...copying {len(glyphs)} glyphs from {ligature_source}")
    for source_name, output_name in sorted(glyphs.items()):
        source.selection.select(source_name)
        source.copy()
        font.createChar(-1, output_name)
        font.selection.select(output_name)
        font.paste()
        glyph = font[output_name]
        glyph.transform(psMat.scale(horizontal_scale, 1.0))
        glyph.width = cell_width

    if characters:
        print(f"    ...copying {len(characters)} character glyphs")
    for source_name, codepoint in characters:
        source.selection.select(source_name)
        source.copy()
        font.selection.select(("unicode",), codepoint)
        font.paste()
        fit_character(font[codepoint], cell_width, scale_threshold)

    # Work around a bug in FontForge where the underline height is subtracted
    # from the underline width when you call generate().
    font.upos += font.uwidth

    extension = ".otf" if input_font_file.lower().endswith(".otf") else ".ttf"
    output_file = f"{output_dir}/{font.fontname}{extension}"
    print(f"    ...saving to '{output_file}' ({font.fullname})")
    font.generate(output_file)

    with open(result_file, "w") as f:
        json.dump({"output_file": output_file}, f)


def fit_character(glyph, cell_width, scale_threshold):
    """Fit a copied character (not a ligature) to the Cell width.

    A glyph whose advance differs from the Cell width by at least
    `scale_threshold` (as a fraction of it) is scaled horizontally; a closer
    one keeps its shape and is centered.
    """
    if glyph.width != cell_width:
        if abs(glyph.width - cell_width) / cell_width >= scale_threshold:
            glyph.transform(psMat.scale(cell_width / glyph.width, 1.0))
        else:
            glyph.width = cell_width  # recalculates the bearings
            bearing = round((glyph.left_side_bearing + glyph.right_side_bearing) / 2)
            glyph.left_side_bearing = bearing
            glyph.right_side_bearing = bearing
    # Correct rounding, which would otherwise misalign the ends of long lines.
    glyph.width = cell_width
