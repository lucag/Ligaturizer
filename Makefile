# To change which fonts are built, edit src/ligaturizer/catalog.py and then "make".

default: fonts

clean:
	rm -rf fonts/output/* Ligaturized*.zip

release: clean fonts pack

pack:
	zip -r -9 -j LigaturizedFonts.zip fonts/output/

fonts:
	uv run ligaturize-all

ligature-list:
	luajit name2dict.lua < fonts/fira/FiraCode.glyphs

# Build the Ligature source from the fonts/fira submodule.
# FIRA_BUILD=native uses your own fontmake instead of Fira's Docker image.
FIRA_BUILD ?= docker
fira:
	scripts/build-fira $(FIRA_BUILD)

test:
	uv run pytest

lint:
	uv run ruff check
	uv run ruff format --check

.PHONY: fonts test lint fira
