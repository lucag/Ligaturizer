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
        return [name for name, _ in self.shape(text, script)]

    def shape(self, text: str, script: str | None = None) -> list[tuple[str, int]]:
        """Each glyph shaping `text` chooses, with the index of the character it starts at."""
        buf = hb.Buffer()
        buf.add_codepoints([ord(c) for c in text])
        buf.guess_segment_properties()
        if script:
            buf.script = script
        hb.shape(self.font, buf)
        return [(self.font.glyph_to_string(i.codepoint), i.cluster) for i in buf.glyph_infos]


def mismatches(output: Path, ligature_source: Path, strings, namespace: str = "") -> list[str]:
    """Strings for which the Output font and the Ligature source choose different glyphs.

    Encoded glyphs correspond by code point; transplanted glyphs by (namespace-stripped) name.
    """
    out, fira = Shaper(output), Shaper(ligature_source)

    def as_fira(text: str, name: str, cluster: int) -> str:
        if name not in out.codepoint_of:
            return name.removeprefix(namespace)
        # The character it was shaped from, unless calt put it elsewhere; a
        # glyph can stand for several code points (e.g. U+0000 and space).
        codepoint = ord(text[cluster])
        if out.glyph_of.get(codepoint) != name:
            codepoint = out.codepoint_of[name]
        return fira.glyph_of.get(codepoint, f"<U+{codepoint:04X}>")

    failures = []
    for text in strings:
        got = [as_fira(text, n, cluster) for n, cluster in out.shape(text)]
        expected = fira.glyph_names(text)
        if got != expected:
            failures.append(f"{text!r}: got {got}, expected {expected}")
    return failures
