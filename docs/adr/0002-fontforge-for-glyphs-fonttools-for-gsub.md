# FontForge copies glyphs, fontTools transplants GSUB

The Output font is built in two stages: FontForge copies and scales glyphs from the Ligature source (it already does this well and handles CFF↔TrueType outline conversion), then fontTools copies Fira Code's `calt` lookups into the saved font at the table level. FontForge alone cannot reliably import Fira's nested contextual lookups, and fontTools alone would require us to reimplement outline conversion and scaling.

## Consequences

Glyphs keep Fira Code's names (e.g. `hyphen_start.seq`, `less.spacer`) so transplanted lookups need no renaming and shaping tests can compare glyph names directly; an optional namespace prefix exists for Input fonts where names would clash, and an unprefixed clash fails the build.

FontForge's Python bindings cannot be installed from PyPI and are tied to the interpreter FontForge was built against. So the FontForge stage is a single stdlib-only script run as a subprocess (`fontforge -lang=py -script …`), while everything else — orchestration, fontTools, tests — lives in an ordinary `uv`-managed environment that never imports `fontforge`.
