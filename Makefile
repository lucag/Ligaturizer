# To change which fonts are built, edit fonts.toml and then "make".
# Personal-use fonts build into fonts/output-personal*/, which pack never includes.

default: fonts

all: fonts with-characters

clean:
	rm -rf fonts/output/* fonts/output-with-characters/* Ligaturized*.zip
	rm -rf fonts/output-personal/* fonts/output-personal-with-characters/*

release: clean all pack

pack:
	zip -r -9 -j LigaturizedFonts.zip fonts/output/
	zip -r -9 -j LigaturizedFontsWithCharacters.zip fonts/output-with-characters/

fonts:
	uv run ligaturize-all

# The variant that also copies Fira Code's glyphs for the selection's copy_characters.
with-characters:
	uv run ligaturize-all --copy-character-glyphs

ligature-list:
	luajit name2dict.lua < fonts/fira/FiraCode.glyphs

# Build the Ligature source from the fonts/fira submodule.
# FIRA_BUILD=native uses your own fontmake instead of Fira's Docker image.
FIRA_BUILD ?= docker
fira:
	scripts/build-fira $(FIRA_BUILD)

# Record the ligatures the pinned Fira Code has; run after moving the fonts/fira pin.
ligature-snapshot:
	uv run python -m ligaturizer.selection

test:
	uv run pytest

lint:
	uv run ruff check
	uv run ruff format --check

.PHONY: all fonts with-characters test lint fira ligature-snapshot
