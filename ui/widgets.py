import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tkd

from ui.styles import Colors, Style


class LabelFrame(tk.LabelFrame):
    def __init__(self, master, text: str, **kwargs):
        super().__init__(master, text=text, **kwargs)
        self.configure(bg=Colors.body_bg, fg=Colors.body_color)


class Button(ttk.Frame):
    def __init__(self, master, style_type, text: str, dimensions: tuple[int, int] = (80, 30), command: callable = None, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.rgb = tuple(int(style_type.strip("#")[i:i+2], 16) for i in (0, 2, 4))
        self.text = text
        self.width, self.height = dimensions
        self.command = command
        self.configure(width=self.width, height=self.height)

        self.canvas = tk.Canvas(self, highlightthicknes=0, background=style_type, width=self.width, height=self.height)
        self.canvas.place(x=0, y=0)

        self.text_label = tk.Label(self.canvas, text=self.text, bg=style_type, fg=Colors.body_color)
        self.text_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<ButtonPress-1>", self.pressed)
        self.canvas.bind("<ButtonRelease-1>", self.released)
        self.text_label.bind("<ButtonPress-1>", self.pressed)
        self.text_label.bind("<ButtonRelease-1>", self.released)

    @staticmethod
    def __rgb_to_hex(rgb):
        return f"#{('%02x%02x%02x' % rgb)}"

    def config(self, cnf=None, **kwargs):
        self.configure(cnf, **kwargs)
        self.canvas.configure(cnf, **kwargs)

    def on_enter(self, _=None):
        r, g, b = self.rgb
        self.canvas.configure(background=Button.__rgb_to_hex((r - 10, g - 10, b - 10)))
        self.text_label.configure(background=Button.__rgb_to_hex((r - 10, g - 10, b - 10)))

    def on_leave(self, _=None):
        self.canvas.configure(background=Button.__rgb_to_hex(self.rgb))
        self.text_label.configure(background=Button.__rgb_to_hex(self.rgb))

    def pressed(self, _=None):
        r, g, b = self.rgb
        self.canvas.configure(background=Button.__rgb_to_hex((r + 10, g + 10, b + 10)))
        self.text_label.configure(background=Button.__rgb_to_hex((r + 10, g + 10, b + 10)))
        if self.command is not None:
            self.command()
            self.on_leave()

    def released(self, _=None):
        self.on_enter()


class FileInput(LabelFrame):
    def __init__(
        self,
        master,
        style_type,
        text: str,
        dimensions: tuple[int, int],
        placeholder: str = "Select a file",
        title: str = "Select file",
        function: callable = tkd.askopenfilename,
        file_types: list[tuple[str, str]] = None,
        initial_dir: str = None,
        callback: callable = None
    ):
        self.__master = master
        self.__width = dimensions[0]
        self.__height = dimensions[1]

        super().__init__(master, text=text)
        self.__path_label = tk.Label(self, bg=style_type, fg=Colors.body_color, font=("", 15), width=round(self.__width/15), height=16)
        self.__select_btn = Button(self, style_type, "Select", dimensions=(80, self.__height), command=self.select)

        self.__path_label.grid()
        self.__select_btn.grid(row=0, column=1)

        self.__title = title
        self.__function = function
        if file_types is None:
            file_types = [("All Files", "*.*")]
        self.__file_types = file_types
        self.__initial_dir = initial_dir
        self.__callback = callback

        self.selected_path = None

    def config(self, cnf=None, **kw):
        super().configure(cnf, **kw)
        self.__path_label.configure(cnf, **kw)
        self.__select_btn.config(cnf, **kw)

    def get_path(self):
        return self.selected_path

    def select(self):
        self.selected_path = self.__function(initialdir=self.__initial_dir, title=self.__title, filetypes=self.__file_types)
        if self.selected_path == "":
            return

        self.__path_label.configure(text=self.selected_path)
        if self.__callback is not None:
            self.__callback(self.selected_path)

    def place(self, row, column, *args, **kwargs):
        self.grid(row=row, column=column, *args, **kwargs)
