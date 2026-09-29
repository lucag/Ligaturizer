"""The Shaping check: compare an Output font's glyph choices with its Ligature source."""

from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont


class Shaper:
    def __init__(self, path: Path):
        self.font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
        cmap = TTFont(path).getBestCmap()
        self.glyph_of = cmap
        self.codepoint_of = {}
        for codepoint, name in sorted(cmap.items()):
            self.codepoint_of.setdefault(name, codepoint)

    def glyph_names(self, text: str, script: str | None = None) -> list[str]:
        """Shape `text`, as if written in `script` (an ISO 15924 code) if given."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        if script:
            buf.script = script
        hb.shape(self.font, buf)
        return [self.font.glyph_to_string(info.codepoint) for info in buf.glyph_infos]


def mismatches(output: Path, ligature_source: Path, strings, namespace: str = "") -> list[str]:
    """Strings for which the Output font and the Ligature source choose different glyphs.

    Encoded glyphs correspond by code point; transplanted glyphs by (namespace-stripped) name.
    """
    out, fira = Shaper(output), Shaper(ligature_source)

    def as_fira(name: str) -> str:
        if name in out.codepoint_of:
            return fira.glyph_of.get(out.codepoint_of[name], f"<U+{out.codepoint_of[name]:04X}>")
        return name.removeprefix(namespace)

    failures = []
    for text in strings:
        got = [as_fira(n) for n in out.glyph_names(text)]
        expected = fira.glyph_names(text)
        if got != expected:
            failures.append(f"{text!r}: got {got}, expected {expected}")
    return failures
