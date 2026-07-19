from kivy.app import App
from kivy.uix.label import Label

class SpriteEditorApp(App):
    def build(self):
        return Label(text="Sprite Editor Placeholder")

if __name__ == "__main__":
    SpriteEditorApp().run()
