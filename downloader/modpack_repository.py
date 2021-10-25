import os.path

import requests
import tempfile

import configuration


class ModPack:
    def __init__(self, mod_pack: str):
        """
        Represents the provided mod-pack as an object
        (Will make web requests)

        :param mod_pack:                Mod Pack location (can be: url, .zip file, folder with manifest.json)
        """
        self.mod_pack_loc = mod_pack
        self.mod_pack = self._get_mod_pack_from_url()

    @staticmethod
    def __contains(string: str, query: list) -> bool:
        for qu in query:
            if qu in string:
                return True
        return False

    def _get_mod_pack_from_url(self, retry: bool = True) -> dict or None:
        if not self.is_url():
            return

        slug = self.mod_pack_loc.split("modpacks/")[1].split("/")[0]
        resp = requests.get(
            f"{configuration.c_forge_api}/addon/search?gameId=432&categoryId=0&searchFilter={slug}&pageSize=20&sort=1&sortDescending=true&sectionId=4471",
            headers=configuration.request_headers
        )
        if not resp.status_code == 200:
            if retry:
                return self._get_mod_pack_from_url(retry=False)
            raise ConnectionError(resp.status_code, resp.reason, "Failed after 1 retry")
        resp = resp.json()
        for obj in resp:
            if obj.get("slug") == slug:
                return obj
        return

    def is_url(self) -> bool:
        """
        Returns if provided mod pack string is a url.

        :return:                    Boolean
        """
        return self.__contains(self.mod_pack_loc[:10], ["http://", "https://"])

    def get_mod_pack_inf(self) -> dict:
        """
        Returns the mod pack
        :return:
        """
        return self.mod_pack

    def get_latest_file(self) -> dict:
        return self.mod_pack.get("latestFiles")[0]

    def get_available_files(self) -> list:
        """
        Returns all available files for the specified mod pack

        :return:                    json object (dict)
        """
        resp = requests.get(
            f"{configuration.c_forge_api}/addon/{self.mod_pack.get('id')}/files",
            headers=configuration.request_headers
        )
        if not resp.status_code == 200:
            raise ConnectionError(resp.status_code, resp.reason)
        return resp.json()

    def download_file(self, file: dict, progress: callable = None) -> str:
        """
        Downloads the specified file of the mod pack to a temporary location and returns its path

        :param file:                file dict for file under mod pack
        :param progress:            callback for file download progress
        :return:                    downloaded file location
        """
        destination = os.path.join(tempfile.mkdtemp(), file.get("fileName"))
        resp = requests.get(file.get("downloadUrl"))
        if not resp.status_code == 200:
            raise ConnectionError(resp.status_code, resp.reason)
        total = int(resp.headers.get('content-length', 0))
        size = 0
        is_url = self.is_url()
        with open(destination, "wb") as f:
            for data in resp.iter_content(chunk_size=1024):
                size += f.write(data)
                if progress is not None:
                    progress(size, total, is_url)
        return destination
