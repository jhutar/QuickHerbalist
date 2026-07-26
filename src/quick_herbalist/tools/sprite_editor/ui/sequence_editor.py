import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.properties import ListProperty, ObjectProperty, StringProperty
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from quick_herbalist.core.config_parser import get_asset_path


class SelectableTextInput(TextInput):
    """
    Custom TextInput that automatically selects all of its content when focused.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(focus=self.on_focus)

    def on_focus(self, instance, value):
        if value:
            # We schedule selection slightly later to allow focus transit to complete
            Clock.schedule_once(lambda dt: self.select_all(), 0.05)


class FrameCard(BoxLayout):
    """
    A widget representing a single frame card in the sequence editor.
    Allows editing all frame and region properties.
    Supports folding/unfolding dynamically (Accordion UX).
    """

    def __init__(
        self, index, frame_data, is_selected, on_select, on_remove, on_change, **kwargs
    ):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height="120dp" if is_selected else "35dp",
            spacing=5,
            **kwargs,
        )
        self.index = index
        self.frame_data = frame_data
        self.is_selected = is_selected
        self.on_select_cb = on_select
        self.on_remove_cb = on_remove
        self.on_change_cb = on_change

        self._setup_ui()

    def _setup_ui(self):
        self.clear_widgets()

        # Row 1: Header (acting as select / fold trigger) + Delete
        row1 = BoxLayout(
            orientation="horizontal", size_hint_y=None, height="30dp", spacing=5
        )

        atlas_id_disp = self.frame_data.get("atlas_id", "Unsaved")
        header_text = f"Frame #{self.index} ({atlas_id_disp})"

        # Color matching selection status
        self.select_btn = Button(
            text=header_text,
            size_hint_x=0.7,
            background_color=[0.2, 0.6, 1, 1]
            if self.is_selected
            else [0.3, 0.3, 0.3, 1],
            bold=self.is_selected,
        )
        self.select_btn.bind(on_release=self._on_select_clicked)
        row1.add_widget(self.select_btn)

        remove_btn = Button(
            text="Delete", size_hint_x=0.3, background_color=[0.8, 0.2, 0.2, 1]
        )
        remove_btn.bind(on_release=self._on_remove_clicked)
        row1.add_widget(remove_btn)
        self.add_widget(row1)

        # Folded state does not render input fields to avoid UI bloat
        if not self.is_selected:
            return

        # Row 2: Atlas ID (read-only Label) + Duration
        row2 = BoxLayout(
            orientation="horizontal", size_hint_y=None, height="35dp", spacing=5
        )
        row2.add_widget(Label(text="Atlas ID:", size_hint_x=0.2))

        # Display Atlas ID as read-only label
        self.atlas_id_label = Label(
            text=str(self.frame_data.get("atlas_id", "")),
            size_hint_x=0.4,
            halign="left",
            valign="middle",
        )
        self.atlas_id_label.bind(size=self.atlas_id_label.setter("text_size"))
        row2.add_widget(self.atlas_id_label)

        row2.add_widget(Label(text="Dur (ms):", size_hint_x=0.2))
        self.duration_input = SelectableTextInput(
            text=str(self.frame_data.get("duration", 250)),
            multiline=False,
            input_filter="int",
            size_hint_x=0.2,
        )
        self.duration_input.bind(text=self._on_text_changed)
        row2.add_widget(self.duration_input)
        self.add_widget(row2)

        # Row 3: Image + Browse + Status Indicator + X + Y + W + H
        row3 = BoxLayout(
            orientation="horizontal", size_hint_y=None, height="35dp", spacing=5
        )
        row3.add_widget(Label(text="Img:", size_hint_x=0.1))

        # Image Text Input
        self.image_input = SelectableTextInput(
            text=str(self.frame_data.get("image", "test_hero.png")),
            multiline=False,
            size_hint_x=0.2,
        )
        self.image_input.bind(text=self._on_text_changed)
        row3.add_widget(self.image_input)

        # File Chooser Browse button
        browse_btn = Button(text="...", size_hint_x=0.1)
        browse_btn.bind(on_release=self._open_file_chooser)
        row3.add_widget(browse_btn)

        # Validation status label [✔] / [❌]
        self.status_label = Label(text="", size_hint_x=0.08, bold=True)
        row3.add_widget(self.status_label)

        # Coordinates
        row3.add_widget(Label(text="X:", size_hint_x=0.04))
        self.x_input = SelectableTextInput(
            text=str(self.frame_data.get("x", 0)),
            multiline=False,
            input_filter="int",
            size_hint_x=0.08,
        )
        self.x_input.bind(text=self._on_text_changed)
        row3.add_widget(self.x_input)

        row3.add_widget(Label(text="Y:", size_hint_x=0.04))
        self.y_input = SelectableTextInput(
            text=str(self.frame_data.get("y", 0)),
            multiline=False,
            input_filter="int",
            size_hint_x=0.08,
        )
        self.y_input.bind(text=self._on_text_changed)
        row3.add_widget(self.y_input)

        row3.add_widget(Label(text="W:", size_hint_x=0.04))
        self.w_input = SelectableTextInput(
            text=str(self.frame_data.get("w", 32)),
            multiline=False,
            input_filter="int",
            size_hint_x=0.08,
        )
        self.w_input.bind(text=self._on_text_changed)
        row3.add_widget(self.w_input)

        row3.add_widget(Label(text="H:", size_hint_x=0.04))
        self.h_input = SelectableTextInput(
            text=str(self.frame_data.get("h", 32)),
            multiline=False,
            input_filter="int",
            size_hint_x=0.08,
        )
        self.h_input.bind(text=self._on_text_changed)
        row3.add_widget(self.h_input)

        self.add_widget(row3)
        self._update_status_indicator()

    def _update_status_indicator(self):
        img_name = self.image_input.text.strip()
        if not img_name:
            self.status_label.text = "[❌]"
            self.status_label.color = [1, 0, 0, 1]
            return

        full_path = get_asset_path(img_name)
        if os.path.exists(full_path):
            self.status_label.text = "[✔]"
            self.status_label.color = [0, 1, 0, 1]
        else:
            self.status_label.text = "[❌]"
            self.status_label.color = [1, 0, 0, 1]

    def _open_file_chooser(self, instance):
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Root the file chooser in the assets/ directory specifically
        assets_dir = get_asset_path("")
        if assets_dir.endswith(os.sep):
            assets_dir = assets_dir[:-1]

        file_chooser = FileChooserListView(
            path=assets_dir, filters=["*.png", "*.jpg", "*.jpeg"]
        )
        content.add_widget(file_chooser)

        btn_layout = BoxLayout(size_hint_y=None, height="40dp", spacing=10)
        select_btn = Button(text="Select")
        cancel_btn = Button(text="Cancel")

        btn_layout.add_widget(select_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)

        popup = Popup(
            title="Choose Image File from Assets", content=content, size_hint=(0.9, 0.9)
        )

        def on_select(btn_instance):
            if file_chooser.selection:
                selected_path = file_chooser.selection[0]
                filename = os.path.basename(selected_path)
                self.image_input.text = filename
                self._on_text_changed(None, filename)
            popup.dismiss()

        select_btn.bind(on_release=on_select)
        cancel_btn.bind(on_release=popup.dismiss)
        popup.open()

    def _on_select_clicked(self, instance):
        if self.on_select_cb:
            self.on_select_cb(self.index)

    def _on_remove_clicked(self, instance):
        if self.on_remove_cb:
            self.on_remove_cb(self.index)

    def _on_text_changed(self, instance, text):
        if not self.is_selected:
            return

        self._update_status_indicator()

        if self.on_change_cb:
            # Parse coordinate values safely
            try:
                dur = int(self.duration_input.text) if self.duration_input.text else 250
            except ValueError:
                dur = 250

            try:
                x = int(self.x_input.text) if self.x_input.text else 0
            except ValueError:
                x = 0

            try:
                y = int(self.y_input.text) if self.y_input.text else 0
            except ValueError:
                y = 0

            try:
                w = int(self.w_input.text) if self.w_input.text else 32
            except ValueError:
                w = 32

            try:
                h = int(self.h_input.text) if self.h_input.text else 32
            except ValueError:
                h = 32

            updated_data = {
                "atlas_id": self.frame_data.get("atlas_id", ""),
                "duration": dur,
                "image": self.image_input.text,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
            }
            self.on_change_cb(self.index, updated_data)


class SequenceEditorWidget(BoxLayout):
    """
    A widget that allows editing the sequence of frames for a sprite.
    """

    frames = ListProperty(
        []
    )  # List of dicts: {'atlas_id': str, 'duration': int, 'image': str, 'x': int, 'y': int, 'w': int, 'h': int}
    sprite_name = StringProperty("")
    save_callback = ObjectProperty(None)
    frames_changed_callback = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.selected_frame_index = -1
        self._setup_ui()

    def _setup_ui(self):
        self.title_label = Label(
            text="Frame Sequence Editor", size_hint_y=None, height="40dp", bold=True
        )
        self.add_widget(self.title_label)

        # ScrollView for frame cards list
        self.scroll_view = ScrollView()
        self.container = GridLayout(cols=1, size_hint_y=None, spacing=15, padding=10)
        self.container.bind(minimum_height=self.container.setter("height"))
        self.scroll_view.add_widget(self.container)
        self.add_widget(self.scroll_view)

        # Bottom Controls
        controls = BoxLayout(size_hint_y=None, height="50dp", spacing=10, padding=5)
        controls.add_widget(Button(text="Add Frame", on_release=self.add_frame))
        controls.add_widget(
            Button(
                text="Save Sprite",
                on_release=self.save_sequence,
                background_color=[0.2, 0.6, 1, 1],
            )
        )
        self.add_widget(controls)

    def set_sprite_name(self, name):
        self.sprite_name = name
        self.title_label.text = f"Frame Sequence Editor: {name}"

    def load_frames(self, frames):
        self.frames = frames
        # Select first frame by default if frames exist and none is selected
        if self.frames and self.selected_frame_index == -1:
            self.selected_frame_index = 0
        elif not self.frames:
            self.selected_frame_index = -1
        self.refresh_ui()

    def refresh_ui(self):
        self.container.clear_widgets()
        for idx, frame in enumerate(self.frames):
            is_selected = idx == self.selected_frame_index
            card = FrameCard(
                index=idx,
                frame_data=frame,
                is_selected=is_selected,
                on_select=self.select_frame,
                on_remove=self.remove_frame,
                on_change=self.change_frame,
            )
            self.container.add_widget(card)

    def select_frame(self, index):
        self.selected_frame_index = index
        self.refresh_ui()

    def change_frame(self, index, updated_data):
        if 0 <= index < len(self.frames):
            self.frames[index] = updated_data
            if self.frames_changed_callback:
                self.frames_changed_callback(self.frames)

    def add_frame(self, instance):
        if not self.sprite_name:
            # Cannot add frame without selected sprite
            return

        # Rule 4: Given I have a frame selected, When I add a new frame,
        # Then the new frame defaults to the same image and its x coordinate is advanced by its width.
        if 0 <= self.selected_frame_index < len(self.frames):
            ref_frame = self.frames[self.selected_frame_index]
            w = ref_frame.get("w", 32)
            new_frame = {
                "atlas_id": f"{self.sprite_name}_{len(self.frames)}",
                "duration": ref_frame.get("duration", 250),
                "image": ref_frame.get("image", "test_hero.png"),
                "x": ref_frame.get("x", 0) + w,
                "y": ref_frame.get("y", 0),
                "w": w,
                "h": ref_frame.get("h", 32),
            }
        else:
            # Default fallback frame
            new_frame = {
                "atlas_id": f"{self.sprite_name}_{len(self.frames)}",
                "duration": 250,
                "image": "test_hero.png",
                "x": 0,
                "y": 0,
                "w": 32,
                "h": 32,
            }

        self.frames.append(new_frame)
        self.selected_frame_index = len(self.frames) - 1
        self.refresh_ui()
        if self.frames_changed_callback:
            self.frames_changed_callback(self.frames)

    def remove_frame(self, index):
        if 0 <= index < len(self.frames):
            self.frames.pop(index)
            # Adjust selection index
            if self.selected_frame_index >= len(self.frames):
                self.selected_frame_index = len(self.frames) - 1
            self.refresh_ui()
            if self.frames_changed_callback:
                self.frames_changed_callback(self.frames)

    def save_sequence(self, instance):
        if self.save_callback:
            self.save_callback(self.sprite_name, self.frames)
