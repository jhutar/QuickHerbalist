# Architecture Decision Record

## Title
Convention Over Configuration for Sprite Assets

## Status
Accepted

## Context
We need to determine how the main game (`SpriteManager`) and the standalone GUI tool locate the sprite configuration files (`sprites.yaml` and `sprites.atlas`).

## Decision
We will use **Convention over Configuration**. Both the `SpriteManager` and the GUI tool will hardcode the expectation that these files exist at specific, fixed paths within the project structure, specifically within the `assets/` directory (e.g., `assets/sprites.yaml` and `assets/sprites.atlas`).

## Consequences
- **Positive:** Reduces boilerplate code in the main game; no need to pass configuration paths around.
- **Positive:** Guarantees consistency between the game runtime and the GUI editor.
- **Negative:** Less flexible if the project structure needs to change dramatically, though unlikely for this scope.
