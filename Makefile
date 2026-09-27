# To build with different settings (e.g. turn on character glyph copying),
# edit src/ligaturizer/catalog.py and then "make".

default: without-characters

all: without-characters with-characters

clean:
	rm -rf fonts/output/* fonts/output-with-characters/* Ligaturized*.zip

release: clean all pack

pack:
	zip -r -9 -j LigaturizedFonts.zip fonts/output/
	zip -r -9 -j LigaturizedFontsWithCharacters.zip fonts/output-with-characters/

without-characters:
	uv run ligaturize-all 2>&1 \
	| grep -Fv 'This contextual rule applies no lookups.' \
	| grep -Fv 'Bad device table'

with-characters:
	uv run ligaturize-all --copy-character-glyphs 2>&1 \
	| grep -Fv 'This contextual rule applies no lookups.' \
	| grep -Fv 'Bad device table'

ligature-list:
	luajit name2dict.lua < fonts/fira/FiraCode.glyphs

testpattern:
	grep -F "{   #" src/ligaturizer/fontforge_stage/ligatures.py \
  | grep -v absent \
  | cut -d'#' -f2 \
  | tr -d ' ' \
  | egrep '.' \
  | sed -E 's,\\,\\\\,g' \
  | xargs printf '| %6s %6s %6s %6s %6s %6s %6s %6s |\n'

test:
	uv run pytest

lint:
	uv run ruff check
	uv run ruff format --check

.PHONY: testpattern test lint
