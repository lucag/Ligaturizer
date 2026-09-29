"""The test pattern: every ligature of the Ligature source, in a table.

`make testpattern` prints it, in the format the `testpattern` file uses: rows
of eight, each right-aligned in six columns. The Specimen shows the same text.
Taken from the Ligature inventory, less the Ligature selection's exclusions.
"""

from ligaturizer.fira import ligature_source
from ligaturizer.inventory import Inventory, read_inventory
from ligaturizer.selection import Selection, read_selection

_PER_ROW = 8
_WIDTH = 6


def pattern(inventory: Inventory, selection: Selection) -> list[str]:
    """Every Fixed ligature, then examples of each Sequence ligature family.

    A family's examples are a plain run of three, and each decoration at the
    start and at the end of a run of two, e.g. "===", "<==", "==>".
    """
    texts = sorted(inventory.fixed)
    for base, decorations in sorted(inventory.sequence_families.items()):
        texts.append(base * 3)
        texts += [d + base * 2 for d in sorted(decorations)]
        texts += [base * 2 + d for d in sorted(decorations)]
    texts = list(dict.fromkeys(texts))
    return [t for t in texts if not any(x in t for x in selection.exclude)]


def table(texts: list[str]) -> list[str]:
    rows = []
    for start in range(0, len(texts), _PER_ROW):
        cells = texts[start : start + _PER_ROW]
        cells += [""] * (_PER_ROW - len(cells))
        rows.append("| " + " ".join(c.rjust(_WIDTH) for c in cells) + " |")
    return rows


def main() -> None:
    inventory = read_inventory(ligature_source("Regular"))
    print("\n".join(table(pattern(inventory, read_selection()))))


if __name__ == "__main__":
    main()
