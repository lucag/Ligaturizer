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
):
    """Copy `glyphs` ({ligature source name: output name}) and save the Output font."""
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

    # Work around a bug in FontForge where the underline height is subtracted
    # from the underline width when you call generate().
    font.upos += font.uwidth

    extension = ".otf" if input_font_file.lower().endswith(".otf") else ".ttf"
    output_file = f"{output_dir}/{font.fontname}{extension}"
    print(f"    ...saving to '{output_file}' ({font.fullname})")
    font.generate(output_file)

    with open(result_file, "w") as f:
        json.dump({"output_file": output_file}, f)
