# Architecture Decision Record

## Title
Relational "Skinny" YAML Configuration

## Status
Accepted

## Context
We need to define the schema for the custom YAML configuration that manages Sprite animations. The YAML needs to define the sequence of frames and their durations. We considered making the YAML the singular source of truth (storing source file paths and regions) versus a relational approach that references IDs in the `.atlas` file.

## Decision
We will use a **"Skinny" Relational YAML** format. The YAML file will only store the animation sequence and durations, referencing unique `atlas_id`s. The actual source image paths and `(x, y, w, h)` regions will be stored exclusively in the Kivy `.atlas` JSON file. 

When the GUI starts, it will cross-check the YAML and `.atlas` files to ensure all referenced `atlas_id`s exist and everything is in place, warning the user or auto-cleaning orphaned data if inconsistencies are found.

## Consequences
- **Positive:** No duplication of data. The region definitions live only in the `.atlas` file where Kivy expects them.
- **Positive:** Enforces strict synchronization validation on GUI startup.
- **Negative:** The GUI tool and SpriteManager must parse and correlate two separate files to fully resolve a Sprite.