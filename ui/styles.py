from enum import Enum
from tkinter.ttk import Style as Sty


class Colors:
    white = "#ffffff"
    gray_100 = "#f8f9fa"
    gray_200 = "#ebebeb"
    gray_300 = "#dee2e6"
    gray_400 = "#ced4da"
    gray_500 = "#adb5bd"
    gray_600 = "#888888"
    gray_700 = "#444444"
    gray_800 = "#303030"
    gray_900 = "#222222"
    black = "#000000"

    blue = "#375a7f"
    indigo = "#6610f2"
    purple = "#6f42c1"
    pink = "#e83e8c"
    red = "#e74c3c"
    orange = "#fd7e14"
    yellow = "#f39c12"
    green = "#00bc8c"
    teal = "#20c997"
    cyan = "#3498db"

    primary = blue
    secondary = gray_700
    success = green
    info = cyan
    warning = yellow
    danger = red
    light = gray_500
    dark = gray_800

    body_bg = gray_900
    body_color = white


class ColorLibrary(Colors, Enum):
    pass


class Style(Sty):
    __variants = [
        "primary",
        "secondary",
        "success",
        "info",
        "warning",
        "danger"
    ]

    def __init__(self, master):
        super().__init__(master)

    def config_for(self, name: str, **kwargs):
        for variant in self.__variants:
            self.configure(f"{variant}.{name}", background=getattr(Colors, variant), **kwargs)
