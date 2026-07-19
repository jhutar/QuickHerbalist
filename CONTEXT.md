# Domain Glossary

## Sprite
A visual entity used in the game, requested by name. A Sprite can be static (single frame) or animated (multiple frames). When requested from the SpriteManager, it is returned as a fully instantiated Kivy Image Widget that autonomously handles its own animation loop (if applicable).

## SpriteManager
The runtime abstraction used by the game. It loads the configuration (YAML + Atlas) and provides a simple interface to request Sprites by name, returning ready-to-use Kivy Widgets.

## SpriteManager GUI
A standalone desktop application (separate from the main game) used by developers to visually create, edit, and manage Sprites, Frames, and animations. It directly manipulates the YAML and Atlas configuration files.

## Frame
A single static image within a Sprite's animation sequence. It consists of:
- A reference to a texture region (backed by a Kivy Atlas).
- A duration (e.g., 250ms) indicating how long the frame is displayed before moving to the next.