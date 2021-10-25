import os
import zipfile
import requests
import tempfile
from shutil import rmtree

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
    def __init__(self, file: str):
        self.zip_file = None
        self.root_path = file
        self.listeners = {}
        self.thread = None
        self.errors = []

        self.manifest = None
        self.mods = None

        if not os.path.isdir(file):
            self.zip_file = file
            self.root_path = tempfile.mkdtemp()

    def __enter__(self):
        if self.zip_file is not None:
            with zipfile.ZipFile(self.zip_file, "r") as zf:
                zf.extractall(self.root_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.zip_file is not None:
            rmtree(self.root_path)

    def __call_listener(self, channel: str, *args, **kwargs):
        func = self.listeners.get(channel)
        if func is not None:
            func(*args, **kwargs)

    def register_listener(self, channel: str, callback: callable):
        if channel == "all":
            self.listeners = _AllListeners(callback)
        if type(self.listeners) == dict:
            self.listeners[channel] = callback

    def remove_listener(self, channel: str = "all"):
        if channel == "all":
            self.listeners = {}
        else:
            del self.listeners[channel]

    def get_manifest(self):
        self.__call_listener("manifest_load_start")
        manifest = ModManifest(
            os.path.join(self.root_path, "manifest.json")
        )
        self.__call_listener("manifest_load_end")
        return manifest

    def get_mod_list(self):
        self.__call_listener("mod_load_start")
        repo, errors = ModRepository(
            self.get_manifest().get("files"),
            progress=self.listeners.get("mod_load_progress")
        ).get()
        self.__call_listener("mod_load_end")
        return repo, errors

    def download_file(self, url: str, to: str, name: str):
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

    def download_mods(self, to: str):
        self.__call_listener("download_start")

        if self.manifest is None or self.mods is None:
            raise Exception("WrongOrderException", "functions called in wrong order leading to missing parameters")
        for i, mod_file in enumerate(self.mods):
            self.__call_listener("download_progress", i, len(self.mods), mod_file.get().get("name"))
            self.download_file(mod_file.get().get("url"), to, mod_file.get().get("name"))

        self.__call_listener("download_end")

    def download(self, destination: str):
        self.__call_listener("process_start")

        self.manifest = self.get_manifest()
        self.mods, errors = self.get_mod_list()

        for error in errors:
            self.__call_listener("process_error", f"Error while downloading file '{error[1]}' from project '{error[0]}", halt=True)

        self.download_mods(os.path.join(destination, "mods"))

        self.__call_listener("process_start")

    def initialize(self, destination: str, listeners: dict = None, *args, **kwargs):
        import threading

        if listeners is not None:
            self.listeners = listeners

        self.thread = threading.Thread(target=self.download, args=(destination, *args), kwargs=kwargs)
        return self.thread
