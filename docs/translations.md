# Translations

Quick Herbalist uses [gettext](https://www.gnu.org/software/gettext/) for
i18n. This guide covers where translations live, which strings must be
translated, how to add new ones, and how the active locale is chosen.

## Layout

| Path | What it is |
|---|---|
| `src/quick_herbalist/locales/base.pot` | Master template: every translatable `msgid`, no translations. |
| `src/quick_herbalist/locales/en/LC_MESSAGES/base.po` | English catalog (source language). |
| `src/quick_herbalist/locales/en/LC_MESSAGES/base.mo` | Compiled English catalog (binary, generated). |
| `src/quick_herbalist/locales/cs/LC_MESSAGES/base.po` | Czech catalog. |
| `src/quick_herbalist/locales/cs/LC_MESSAGES/base.mo` | Compiled Czech catalog (binary, generated). |
| `src/quick_herbalist/localization.py` | Binds the `base` text domain to the locales directory and exposes `_` (= `gettext.gettext`). |
| `scripts/compile_mo.py` | Compiles a `.po` to a `.mo` with polib. |
| `scripts/update_pot.py` | Regenerates `base.pot` from the `_()` calls in the game code and the recipe keys in `recipes.yaml`. |
| `.pre-commit-config.yaml` | Defines the local `compile-mo` pre-commit hook (id `compile-mo`), which runs `scripts/compile_mo.py` on staged `*.po` files. |

The text domain is `base`, so catalogs live under `<locale_dir>/<lang>/LC_MESSAGES/base.po`
— the standard gettext layout. At runtime gettext looks in
`src/quick_herbalist/locales/` (see `get_locales_dir` in `localization.py`).

Available locales: `en`, `cs`. The directory is `locales/cs/` — **not**
`cz`. `cs` is the ISO 639-1 language code for Czech.

## Scope rules

**Only on-screen strings go through `_()`.**

Translate:

- UI labels, buttons, headings, popups/dialogs
- In-game messages (win/lose, HUD text, toasts)

Never translate (keep English only):

- `logging.*` messages and anything printed to the terminal, including the
  `SystemExit` raised in `src/quick_herbalist/app.py` for an invalid
  `levels.yaml` or `recipes.yaml`. These are for developers, not players.
- `src/quick_herbalist/tools/sprite_editor/` — a developer tool. It must
  never appear in `base.pot`; keep it out of any regeneration glob.

### Potion and recipe names

Recipes in `src/quick_herbalist/assets/recipes.yaml` do not store names
directly. Each recipe has `name_key` and `description_key` fields
(validated in `src/quick_herbalist/potions.py`) which are gettext `msgid`s.
The UI translates them at display time:

```python
name = _(recipe.name_key)
```

(see `src/quick_herbalist/screens/potions_screen.py`). So adding a potion
means adding two translation entries — one for the name, one for the
description — to each catalog. See `docs/add_new_potion.md` for the full
potion workflow.

## Adding a new string

1. **Wrap the string.** In the UI code, wrap the on-screen literal:

   ```python
   self.title = _("Brewed!")
   ```

   For f-strings, translate each literal piece separately (gettext works on
   static strings), e.g. `_("Brewed: ") + _(recipe.name_key)`.

2. **Regenerate `base.pot`.** Run the regeneration script (from the repo
   root):

   ```bash
   uv run python scripts/update_pot.py
   ```

   It extracts every static `_()` call in `src/quick_herbalist/*.py`,
   `screens/*.py`, and `game/*.py`, plus the recipe `name_key`/
   `description_key` and ingredient keys from `assets/recipes.yaml`.
   Output is deterministic (sorted msgids, no timestamps) and never
   includes `tools/sprite_editor/` or logging/terminal strings. `base.pot`
   carries no translations; it only lists the `msgid`s.

3. **Add the `msgid` to each catalog** — `locales/en/LC_MESSAGES/base.po`
   (English `msgstr`) and `locales/cs/LC_MESSAGES/base.po` (Czech `msgstr`):

   ```
   msgid "Brewed!"
   msgstr "Brewed!"
   ```

4. **Commit.** The `compile-mo` pre-commit hook compiles changed `.po` files
   to `.mo` automatically. It rewrites the tracked `.mo` in place, so
   pre-commit reports "files were modified by hook" — stage the regenerated
   `.mo` files (`git add`) and re-commit. Always commit `.po` and `.mo`
   together. Manual fallback: `python scripts/compile_mo.py <file.po>`.

Verify: `make test` and `make check-all`.

## Locale precedence

Intended behavior of the shipped app, from highest to lowest priority:

1. **`settings.locale` in the user's `config.yaml`** — managed by
   `ProfileManager` (`src/quick_herbalist/profiles.py`), stored in Kivy's
   `user_data_dir`. Accepted values: `en`, `cs`, or `system`.
   `system` is the default when the key is unset.
2. **`system`** — follow the environment locale (e.g. `LANG`). Use `cs`
   only when the locale's 2-letter language code is `cs` (e.g.
   `cs_CZ.UTF-8`); any other language code resolves to `en`.
3. **Fallback** — `en`.

Locale changes apply on app **restart**; there is no live switching.
