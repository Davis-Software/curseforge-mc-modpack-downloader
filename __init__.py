import configuration
from ui.styles import Colors
from ui.window import Window
from ui.widgets import LabelFrame, Button, FileInput

from downloader.curseforge_downloader import DownloadManager


class MainWindow(Window):

    app_name = "CurseforgeMC Modpack Downloader"

    width = 1080
    height = 720

    def __init__(self):
        super().__init__(self.app_name, (self.width, self.height), lock_dimensions=False)

        FileInput(self, Colors.secondary, "Input", (self.width, 40)).place(0, 0)


if __name__ == "__main__":
    with DownloadManager("zipfile") as d_mgr:
        d_mgr.register_listener("all", print)
        d_mgr.download("target")

    # MainWindow().mainloop()
