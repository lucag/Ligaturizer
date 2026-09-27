"""The Cell width of an Input font."""

import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

from ligaturizer.build import NotMonospaced, cell_width


def _font(widths: dict[str, int]):
    """A font whose printable ASCII advances are 600, except as given in `widths`."""
    chars = [chr(c) for c in range(0x21, 0x7F)]
    names = [f"g{ord(c)}" for c in chars]
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder([".notdef", *names])
    builder.setupCharacterMap({ord(c): n for c, n in zip(chars, names, strict=True)})
    empty = TTGlyphPen(None).glyph()
    builder.setupGlyf({n: empty for n in [".notdef", *names]})
    advances = {n: widths.get(c, 600) for c, n in zip(chars, names, strict=True)}
    builder.setupHorizontalMetrics({".notdef": (600, 0)} | {n: (w, 0) for n, w in advances.items()})
    return builder.font


def test_cell_width_is_the_shared_ascii_advance():
    assert cell_width(_font({})) == 600


def test_one_unit_rounding_differences_take_the_most_common_width():
    assert cell_width(_font({"%": 601, "@": 601})) == 600


def test_fonts_whose_widths_differ_more_are_not_monospaced():
    with pytest.raises(NotMonospaced):
        cell_width(_font({"i": 598}))
