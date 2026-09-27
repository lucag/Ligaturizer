# Derive ligature behavior from Fira Code's built OTF

Fira Code moved from one-glyph-per-ligature to arbitrary-length Sequence ligatures assembled by `calt` rules, which left our hand-maintained `ligatures.py` silently broken (58 of 144 entries vanished). We decided to take Ligature behavior from the compiled `calt` lookups and glyphs of the released Fira Code OTF for each weight, keeping only a small hand-kept Ligature selection on top.

## Considered Options

- **Hand-maintained list (status quo):** drifts from Fira on every release, and cannot express Sequence ligatures.
- **Fira's sources (`.glyphs` + `features/calt/*.fea`):** closer to intent, but those are inputs to Fira's own Clojure/fontmake build, not what ships; we would be re-implementing their build.
- **Built OTF (chosen):** exactly what Fira users get, available per weight, and changes only when Fira releases.

## Consequences

Scope is Fira's default `calt` only; stylistic sets (`ssNN`) and character variants (`cvNN`) are out of scope for now but should remain addable. Anything the Ligature selection explicitly requires that is absent from the Ligature source fails the build.
