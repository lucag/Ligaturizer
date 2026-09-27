# The Input font's own `calt` is replaced, `liga` is kept

Some Input fonts (e.g. Fantasque Sans Mono, Space Mono) ship their own `calt` feature. We remove it before adding Fira Code's, because two sets of contextual rules interacting would make the Output font's Ligature behavior differ from Fira Code's, which is the property our tests assert. The Input font's `liga` (and other features) are left alone.
