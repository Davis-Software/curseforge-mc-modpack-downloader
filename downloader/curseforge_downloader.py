import os
import threading
import zipfile
import requests
import tempfile
from shutil import rmtree

from downloader.modpack_repository import ModPack
from downloader.manifest_repository import ModManifest
from downloader.mod_repository import ModRepository


class _AllListeners:
    def __init__(self, callback: callable):
        self.callback = callback

    def __setitem__(self, key, value):
        pass

    def get(self, _):
        return self.callback


class DownloadManager:
    def __init__(self, mod_pack: ModPack or str):
        """
        Provides a contextmanager with various functionalities, the main ones
        being the download and initialize functions\n
        REMINDER: If you don't use self as context manager don't forget to self.finish() if all operations have finished.

        :param mod_pack:                Reference to the wanted mod-pack (can be: class ModPack, .zip file, folder with manifest.json)
        """
        self.zip_file = None
        self.root_path = mod_pack
        self.listeners = {}
        self.thread = None
        self.errors = []

        self.manifest = None
        self.mods = None

        if not os.path.isdir(mod_pack):
            self.zip_file = mod_pack
            self.root_path = tempfile.mkdtemp()

    def __enter__(self):
        if self.zip_file is not None:
            with zipfile.ZipFile(self.zip_file, "r") as zf:
                zf.extractall(self.root_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.zip_file is not None:
            rmtree(self.root_path)

    def finish(self):
        """
        Removes temporary files and finishes.\n
        REMINDER: Needn't be called if using self as context manager; must be called if not using self as context manager.

        :return:                        None
        """
        self.__exit__(None, None, None)

    def __call_listener(self, channel: str, *args, **kwargs):
        func = self.listeners.get(channel)
        if func is not None:
            func(*args, **kwargs)

    def register_listener(self, channel: str, callback: callable):
        """
        Adds a callback to a specific or all channels\n
        WARNING: Event listeners are called synchronously thus will pause the download process

        :param channel:                 The wanted listening channel (can be "all" to apply same callback to all channels)
        :param callback:                The callback function which is called on event occurrence on specified channel(s)
        :return:                        None
        """
        if channel == "all":
            self.listeners = _AllListeners(callback)
        if type(self.listeners) == dict:
            self.listeners[channel] = callback

    def remove_listener(self, channel: str = "all"):
        """
        Removes an established event-listener from a specific or all channels

        :param channel:                 The targeted listening channel (can be "all" to remove from all channels)
        :return:                        None
        """
        if channel == "all":
            self.listeners = {}
        else:
            del self.listeners[channel]

    def get_manifest(self) -> ModManifest:
        """
        Gets all manifest.json contents
        (Emits events during run)

        :return:                        downloader.manifest_repository.ModManifest
        """
        self.__call_listener("manifest_load_start")
        manifest = ModManifest(
            os.path.join(self.root_path, "manifest.json")
        )
        self.__call_listener("manifest_load_end")
        return manifest

    def get_mod_list(self) -> tuple[ModRepository, list]:
        """
        Gets all mods from ModPack's mod list
        (Emits events during run & makes many web requests)

        :return:                        downloader.mod_repository.ModRepository
        """
        self.__call_listener("mod_load_start")
        repo, errors = ModRepository(
            self.get_manifest().get("files"),
            progress=self.listeners.get("mod_load_progress")
        ).get()
        self.__call_listener("mod_load_end")
        return repo, errors

    def _download_file(self, url: str, to: str, name: str):
        path = os.path.join(to, name)
        if not os.path.exists(to):
            os.makedirs(to)

        resp = requests.get(url, stream=True)
        if not resp.status_code == 200:
            self.errors.append(
                (name, resp.status_code, resp.reason)
            )
            return
        total = int(resp.headers.get('content-length', 0))
        size = 0
        with open(path, "wb") as f:
            for data in resp.iter_content(chunk_size=1024):
                size += f.write(data)
                self.__call_listener("download_file_progress", size, total)

    def _download_mods(self, to: str):
        self.__call_listener("download_start")

        if self.manifest is None or self.mods is None:
            raise Exception("WrongOrderException", "functions called in wrong order leading to missing parameters")
        for i, mod_file in enumerate(self.mods):
            self.__call_listener("download_progress", i, len(self.mods), mod_file.get().get("name"))
            self._download_file(mod_file.get().get("url"), to, mod_file.get().get("name"))

        self.__call_listener("download_end")

    def download(self, destination: str):
        """
        Starts downloading all mods to a "mods" folder in the specified destination
        and moves "override" contents from manifest.json to destination
        (Emits events during run & makes many web requests)

        :param destination:             path where the ModPack should be downloaded to
        :return:                        None
        """
        self.__call_listener("process_start")

        self.manifest = self.get_manifest()
        self.mods, errors = self.get_mod_list()

        for error in errors:
            self.__call_listener("process_error", f"Error while downloading file '{error[1]}' from project '{error[0]}", halt=True)

        self._download_mods(os.path.join(destination, "mods"))

        self.__call_listener("process_start")

    def initialize(self, destination: str, listeners: dict[str, callable] = None, *args, **kwargs) -> threading.Thread:
        """
        Initializes a Thread for asynchronous call of self.download

        :param destination:             path where the ModPack should be downloaded to
        :param listeners:               dict with callbacks mapped to event listener channels
        :param args:                    additional args for threading.Thread
        :param kwargs:                  additional kwargs for threading.Thread
        :return:                        threading.Thread
        """
        import threading

        if listeners is not None:
            self.listeners = listeners

        self.thread = threading.Thread(*args, target=self.download, args=(destination, *[]), **kwargs)
        return self.thread
