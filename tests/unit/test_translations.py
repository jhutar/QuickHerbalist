"""Completeness checks for the gettext catalogs (base.pot, en/cs base.po, base.mo)."""

import gettext
from pathlib import Path

LOCALES = Path(__file__).resolve().parents[2] / "src" / "quick_herbalist" / "locales"
LANGS = ("en", "cs")


def parse_po(path):
    """Parse a .po file into a {msgid: msgstr} dict (handles wrapped strings)."""
    entries = {}
    current_msgid = None
    msgstr = ""
    have_msgstr = False

    def flush():
        """Store the current entry, if any, and reset state."""
        nonlocal current_msgid, msgstr, have_msgstr
        if current_msgid is not None:
            entries[current_msgid] = msgstr
        current_msgid, msgstr, have_msgstr = None, "", False

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith('msgid "'):
            flush()
            current_msgid = line[len('msgid "') : -1]
        elif line.startswith('msgstr "'):
            msgstr = line[len('msgstr "') : -1]
            have_msgstr = True
        elif line.startswith('"'):
            # Continuation line of the string currently being read.
            chunk = line[1:-1]
            if have_msgstr:
                msgstr += chunk
            elif current_msgid is not None:
                current_msgid += chunk
        elif not line.strip() or line.startswith("#"):
            flush()
    flush()
    return {k: v for k, v in entries.items() if k != ""}


def pot_msgids():
    """All non-header msgids from base.pot."""
    return set(parse_po(LOCALES / "base.pot"))


def test_every_pot_msgid_translated_in_all_locales():
    """Every msgid from the pot has a non-empty msgstr in each catalog."""
    expected = pot_msgids()
    for lang in LANGS:
        catalog = parse_po(LOCALES / lang / "LC_MESSAGES" / "base.po")
        missing = expected - set(catalog)
        empty = {m for m, s in catalog.items() if m in expected and not s}
        assert not missing and not empty, (
            f"{lang}: missing msgids {sorted(missing)}, empty msgstr {sorted(empty)}"
        )


def test_empty_msgstr_is_detected(tmp_path):
    """Parser and completeness check flag an entry with an empty msgstr."""
    po = tmp_path / "base.po"
    po.write_text(
        'msgid "Alpha"\nmsgstr "Alfa"\n\nmsgid "Beta"\nmsgstr ""\n', encoding="utf-8"
    )
    catalog = parse_po(po)
    empty = {m for m, s in catalog.items() if not s}
    assert empty == {"Beta"}


def test_no_obsolete_msgids_in_catalogs():
    """Catalogs contain exactly the pot msgids — nothing from removed strings."""
    expected = pot_msgids()
    for lang in LANGS:
        catalog = parse_po(LOCALES / lang / "LC_MESSAGES" / "base.po")
        obsolete = set(catalog) - expected
        assert not obsolete, f"{lang}: obsolete msgids {sorted(obsolete)}"


def test_compiled_mo_files_cover_all_msgids():
    """Each compiled base.mo resolves every pot msgid to a non-empty string."""
    for lang in LANGS:
        mo_path = LOCALES / lang / "LC_MESSAGES" / "base.mo"
        with open(mo_path, "rb") as f:
            translation = gettext.GNUTranslations(f)
        unresolved = [m for m in pot_msgids() if not translation.gettext(m)]
        assert not unresolved, f"{lang}: mo misses {unresolved}"
