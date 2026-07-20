# Architecture Decision Record

## Title
Abstract Kivy Atlas behind a unified SpriteManager

## Status
Accepted

## Context
We need a way to manage 2D sprites, including static images and frame-by-frame animations (with specific durations), configured via a GUI tool. Kivy provides `Atlas` for packing image regions, but it lacks animation sequence and duration support. We considered building a purely custom format or using Atlas.

## Decision
We will use Kivy's `Atlas` to manage static image regions (`x, y, width, height`), but we will build a custom YAML configuration layer on top of it to manage animation sequences (durations and frame ordering).

The GUI tool will **hide the Atlas entirely**. Users will interact only with "Sprites" and "Frames". The GUI will automatically synchronize the underlying `.atlas` JSON (for regions) and the custom YAML file (for sequences), generating unique internal IDs for Atlas regions without exposing them to the user.

## Consequences
- **Positive:** We leverage Kivy's native, optimized `Atlas` loading for textures.
- **Positive:** The user experience is simplified; users do not need to manually manage two separate configuration files or worry about broken references.
- **Negative:** The GUI tool takes on the complexity of safely mutating both a Kivy `.atlas` file and a YAML file in tandem.
