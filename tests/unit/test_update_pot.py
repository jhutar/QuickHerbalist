"""Tests for the base.pot regeneration script (scripts/update_pot.py)."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "update_pot.py"


def load_script():
    """Load scripts/update_pot.py as a module (it lives outside the src package)."""
    spec = importlib.util.spec_from_file_location("update_pot", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def update_pot():
    """Imported update_pot script module."""
    return load_script()


def msgids_from(content):
    """Extract the msgid strings (without header) from .pot text."""
    out = []
    for line in content.splitlines():
        if line.startswith('msgid "') and line != 'msgid ""':
            out.append(line[len('msgid "') : -1])
    return out


def test_script_runs_and_writes_pot(update_pot, tmp_path):
    """main() runs and writes a .pot file with a header and entries."""
    output = tmp_path / "base.pot"
    update_pot.main([str(output)])
    content = output.read_text(encoding="utf-8")
    assert '"Generated-By: update_pot.py\\n"' in content
    assert 'msgid ""' in content
    assert msgids_from(content)


def test_pot_contains_known_screen_msgids(update_pot, tmp_path):
    """Every screen, hint, and recipe msgid from the code ends up in the .pot."""
    output = tmp_path / "base.pot"
    update_pot.main([str(output)])
    msgids = set(msgids_from(output.read_text(encoding="utf-8")))
    expected = {
        "Start Game",
        "Select Character",
        "Potion Crafting",
        "Drag onto cauldron to mix",
        "GAME OVER!",
        "LEVEL COMPLETED!",
        "No potions yet",
        "Flower",
        "Flowers are collectible. Run through them to add them to your harvest.",
        "Stones are obstacles you need to avoid. If you run into them, your mission is over.",
        "potion_magnetism_name",
        "potion_magnetism_description",
        "dandelion_sprite",
        "bluebell_sprite",
    }
    assert expected <= msgids


def test_pot_excludes_sprite_editor_and_logging_strings(update_pot, tmp_path):
    """tools/sprite_editor/ and logging/terminal strings never land in the .pot."""
    output = tmp_path / "base.pot"
    update_pot.main([str(output)])
    content = output.read_text(encoding="utf-8")
    # Literal only present in tools/sprite_editor/.
    assert "Configuration Error" not in content
    # Logging message in game/scene.py, not an on-screen string.
    assert "No free spawn position" not in content
    # Terminal/SystemExit error in app.py, not an on-screen string.
    assert "Refusing to start" not in content


def test_pot_generation_is_deterministic(update_pot, tmp_path):
    """Two consecutive runs produce byte-identical output."""
    first = tmp_path / "first.pot"
    second = tmp_path / "second.pot"
    update_pot.main([str(first)])
    update_pot.main([str(second)])
    assert first.read_bytes() == second.read_bytes()
