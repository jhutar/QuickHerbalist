from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ListProperty, NumericProperty, ObjectProperty

class FrameItem(BoxLayout, RecycleDataViewBehavior):
    """
    A widget representing a single frame in the sequence.
    """
    index = NumericProperty(0)
    atlas_id = ObjectProperty(None)
    duration = NumericProperty(100)
    on_remove_frame = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height='40dp', **kwargs)
        self.add_widget(Label(text="Index", size_hint_x=0.2))
        self.id_label = Label(text="", size_hint_x=0.4)
        self.add_widget(self.id_label)
        self.add_widget(Label(text="Duration (ms)", size_hint_x=0.2))
        self.duration_input = TextInput(multiline=False, input_filter='int', size_hint_x=0.2)
        self.duration_input.bind(text=self.on_duration_change)
        self.add_widget(self.duration_input)
        self.add_widget(Button(text="X", size_hint_x=0.2, on_release=self.remove_frame))

    def on_duration_change(self, instance, value):
        try:
            self.duration = int(value)
        except ValueError:
            self.duration = 0

    def refresh_view(self, rv, index, data):
        self.index = index
        self.atlas_id = data.get('atlas_id')
        self.duration = data.get('duration', 100)
        self.id_label.text = str(self.atlas_id)
        self.duration_input.text = str(self.duration)
        self.on_remove_frame = data.get('on_remove_frame')

    def remove_frame(self, instance):
        if self.on_remove_frame:
            self.on_remove_frame(self.index)

class SequenceEditorWidget(BoxLayout):
    """
    A widget that allows editing the sequence of frames for a sprite.
    """
    frames = ListProperty([])  # List of dicts: {'atlas_id': str, 'duration': int}
    sprite_name = ObjectProperty(None)
    on_save_callback = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self._setup_ui()

    def _setup_ui(self):
        self.add_widget(Label(text="Frame Sequence Editor", size_hint_y=None, height='40dp'))
        
        self.rv = RecycleView()
        self.rv.viewclass = FrameItem
        
        # Create the layout for the RecycleView items
        self.layout = GridLayout(cols=1, size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.rv.add_widget(self.layout)
        
        self.add_widget(self.rv)

        # Controls
        controls = BoxLayout(size_hint_y=None, height='50dp')
        controls.add_widget(Button(text="Add Frame", on_release=self.add_frame))
        controls.add_widget(Button(text="Save Sequence", on_release=self.save_sequence))
        self.add_widget(controls)

    def add_frame(self, instance):
        # For now, just add a dummy frame
        self.frames.append({'atlas_id': 'new_atlas_id', 'duration': 100})
        self.refresh_rv()

    def remove_frame(self, index):
        if 0 <= index < len(self.frames):
            self.frames.pop(index)
            self.refresh_rv()

    def refresh_rv(self):
        # We need to pass the callback in the data for each item
        self.rv.data = [
            {
                'atlas_id': frame['atlas_id'],
                'duration': frame['duration'],
                'on_remove_frame': self.remove_frame
            }
            for frame in self.frames
        ]

    def save_sequence(self, instance):
        if self.on_save_callback:
            self.on_save_callback(self.sprite_name, self.frames)
        else:
            print(f"No save callback provided. Saving sequence: {self.frames}")
