#!/usr/bin/env /usr/local/bin/zsh

fonts=("./fonts/Operator-Mono/src/Operator Mono/"*.otf(N))

for f in "$fonts[@]"; do
  fontforge -lang py -script ligaturize.py "$f" --output-dir=fonts/output --prefix="Liga"
done
