# An exclusion leaves out whole Fira Code lookups, strictly

Fira Code often makes several sequences with one `calt` lookup: a single rule lowers the dot of `i` and `j` after `f`, and another lowers `l` after `F`, `I` and `T`. Only Fixed ligatures get a lookup each. We decided that excluding a sequence in the Ligature selection leaves out every top-level `calt` lookup that makes it, as it stands. If that would also change a sequence the selection doesn't exclude, the build fails and names it. Longer text containing an excluded sequence (e.g. `fii` for `fi`) is expected to change and isn't flagged.

## Considered Options

- **Exact sequence:** rewrite Fira's rules so only the excluded sequence stops (`fi` without `fj`). Precise, but the transplant would stop copying Fira's rules unchanged, and it gets harder to show Output fonts behave like Fira.
- **Whole lookup, quietly:** the same removal with no check. Simplest, but excluding `fi` would silently drop `fj`, `Fl`, `Il` and `Tl` too.

## Consequences

Exclusions come in groups Fira decides, e.g. the default excludes `fi`, `fj`, `Fl`, `Il` and `Tl` together. The check shapes text with the Ligature source with and without the lookups, so the build needs HarfBuzz (`uharfbuzz`), and it costs a little under a second per build.
