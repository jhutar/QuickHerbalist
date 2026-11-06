"""Compile .po translation files to .mo for gettext at commit time.

Invoked by the `compile-mo` pre-commit hook with the list of changed
.po files. Rewriting a tracked .mo in place makes pre-commit fail with
"files were modified by hook" until the new .mo is staged, keeping
compiled translations in sync with their sources.
"""

import sys
from pathlib import Path

import polib


def main() -> None:
    """Compile each passed .po file to a .mo file in the same directory."""
    for po_path in sys.argv[1:]:
        if not po_path.endswith(".po"):
            continue
        po_file = polib.pofile(po_path)
        po_file.save_as_mofile(Path(po_path).with_suffix(".mo"))


if __name__ == "__main__":
    main()
