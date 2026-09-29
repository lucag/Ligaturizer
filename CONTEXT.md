# Ligaturizer

Transplants Fira Code's programming ligatures into other monospaced fonts, producing new fonts that behave like Fira Code for ligatures while keeping their own look for everything else.

## Language

### Fonts

**Input font**:
A monospaced font that ligatures are added to.
_Avoid_: target font, destination font

**Output font**:
The Input font with Fira Code's ligatures added, renamed per its license.
_Avoid_: ligaturized font, result font

**Personal-use font**:
An Input font whose license forbids distributing derivatives; its Output fonts are built locally but never included in a release.
_Avoid_: private font, non-free font

**Cell width**:
The single advance width shared by every printable ASCII character of an Input font; the unit all transplanted glyphs are fitted to. Advances within 1 unit of each other count as shared (a rounding artifact), and the most common one is the Cell width. An Input font without one is not monospaced and is rejected.
_Avoid_: emwidth, m-width

**Ligature source**:
The weight of Fira Code, as shipped in its built release, that ligatures are taken from for a given Input font: the one nearest the Input font's declared weight class (`usWeightClass`), ties going to the lighter, unless overridden.
_Avoid_: Fira font, source font

### Ligatures

**Fixed ligature**:
A ligature drawn as a single glyph for one exact character sequence (e.g. `&&`, `!=`).
_Avoid_: simple ligature, liga

**Sequence ligature**:
A ligature of any length built from a start piece, zero or more middle pieces, and an end piece (e.g. arrows like `------>`, runs of `=`, `#`, `_`).
_Avoid_: arrow, variable ligature

**Piece**:
One em-wide component of a Sequence ligature, in the role of start, middle, or end.
_Avoid_: segment, part

**Spacer**:
An empty glyph that replaces a character that has been absorbed into a ligature drawn on a neighbouring position.
_Avoid_: CR glyph, placeholder

**Ligature behavior**:
Which glyphs Fira Code's default `calt` feature chooses for a given text; the thing an Output font must reproduce.
_Avoid_: ligature definitions, ligature list

**Ligature selection**:
The short, hand-kept list of ligatures that are explicitly required or excluded on top of the Ligature behavior taken from the Ligature source, kept in `selection.toml`, along with the characters whose glyphs `--copy-character-glyphs` also takes from the Ligature source. An exclusion leaves out the whole Fira Code rule that makes it (ADR 0005).
_Avoid_: ligatures.py, master list

**Ligature snapshot**:
The generated, committed record of the Fixed ligatures and Sequence ligature families the pinned Ligature source has, kept in `ligature-snapshot.toml`; the build warns about any a Ligature source lacks.
_Avoid_: lock file, baseline

### Verification

**Shaping check**:
A test that shapes the same text with an Output font and with its Ligature source, and passes when both choose corresponding glyphs at every position.
_Avoid_: ligature test, golden test

**Specimen**:
A human-reviewed page showing the same text set in the Ligature source and in an Output font side by side; never a pass/fail check.
_Avoid_: snapshot, screenshot test
