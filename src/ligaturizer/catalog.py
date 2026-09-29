"""The font catalogue, `fonts.toml`: the Input fonts `ligaturize-all` builds."""

import tomllib
from dataclasses import dataclass
from fnmatch import fnmatch
from glob import glob
from pathlib import Path

# Relative to the repository root, like the paths in it.
CATALOGUE_FILE = Path("fonts.toml")


class CatalogueError(ValueError):
    pass


@dataclass(frozen=True)
class Settings:
    name_prefix: str
    scale_character_glyphs_threshold: float
    output_dir: str
    output_dir_with_characters: str
    personal_output_dir: str
    personal_output_dir_with_characters: str

    def output_dir_for(self, personal: bool, with_characters: bool) -> str:
        if personal:
            if with_characters:
                return self.personal_output_dir_with_characters
            return self.personal_output_dir
        return self.output_dir_with_characters if with_characters else self.output_dir


@dataclass(frozen=True)
class Entry:
    pattern: str
    # Exactly one of these is set: prefixed and personal-use fonts get the name
    # prefix, renamed fonts a new family name.
    prefix: str | None
    name: str | None
    personal: bool


@dataclass(frozen=True)
class Build:
    """One Input font to build, as the catalogue describes it."""

    input_font_file: str
    prefix: str | None
    output_name: str | None
    glyph_namespace: str
    personal: bool


@dataclass(frozen=True)
class Catalogue:
    settings: Settings
    entries: tuple[Entry, ...]
    # Pattern -> prefix for the glyphs copied into matching fonts.
    glyph_namespaces: dict[str, str]

    def builds(self) -> list[Build]:
        """Every Input font the catalogue lists, in catalogue order.

        Raises CatalogueError for a pattern that matches nothing, unless it's
        a Personal-use font, which you may not have.
        """
        builds = []
        for entry in self.entries:
            files = sorted(glob(entry.pattern))
            if not files and not entry.personal:
                raise CatalogueError(f"pattern {entry.pattern!r} didn't match any files")
            for file in files:
                namespace = next(
                    (ns for p, ns in self.glyph_namespaces.items() if fnmatch(file, p)), ""
                )
                builds.append(Build(file, entry.prefix, entry.name, namespace, entry.personal))
        return builds


def read_catalogue(path: str | Path = CATALOGUE_FILE) -> Catalogue:
    data = tomllib.loads(Path(path).read_text())
    known = {"settings", "prefixed", "renamed", "personal", "glyph_namespaces"}
    if unknown := set(data) - known:
        raise CatalogueError(f"{path}: unknown keys {sorted(unknown)}")
    try:
        settings = Settings(**data["settings"])
    except (KeyError, TypeError) as e:
        raise CatalogueError(f"{path}: bad [settings] table: {e}") from None

    prefix = settings.name_prefix
    entries = [Entry(p, prefix, None, False) for p in data.get("prefixed", [])]
    entries += [Entry(p, None, name, False) for p, name in data.get("renamed", {}).items()]
    entries += [Entry(p, prefix, None, True) for p in data.get("personal", [])]
    return Catalogue(settings, tuple(entries), dict(data.get("glyph_namespaces", {})))
