from tkinter import Tk

from ui.styles import Colors


class Window(Tk):
    def __init__(self, title: str, dimensions: tuple[int, int] or str, lock_dimensions: bool = False, **kwargs):
        super().__init__(**kwargs)

        if type(dimensions) == tuple:
            self.geometry(f"{dimensions[0]}x{dimensions[1]}")
            if lock_dimensions:
                self.resizable(False, False)

        self.config(background=Colors.body_bg)
        self.title(title)

    def clear_widgets(self):
        for widget in self.grid_slaves():
            widget.destroy()
