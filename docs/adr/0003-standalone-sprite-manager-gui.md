# Architecture Decision Record

## Title
Standalone CLI Entry Point for Sprite Manager GUI

## Status
Accepted

## Context
We need to decide how the Sprite Manager GUI tool is launched and distributed relative to the main game. It could be an in-game overlay (e.g., accessed via a hotkey) or a completely separate application.

## Decision
We will build the Sprite Manager GUI as a **Standalone CLI Entry Point**. It will be a separate Kivy application launched via a distinct command (e.g., `uv run manage-sprites`), rather than being baked into the main game's runtime.

## Consequences
- **Positive:** Keeps the main game codebase clean, lightweight, and free of developer-only UI logic.
- **Positive:** Prevents accidental inclusion or exposure of developer tools in production builds.
- **Negative:** Requires developers to stop the game (or run alongside it) and restart the game to see changes applied, unless hot-reloading is implemented.
