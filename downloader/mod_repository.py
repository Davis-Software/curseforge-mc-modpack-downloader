import requests

import configuration


class Mod:
    def __init__(self, mod_id: int, file_id: int):
        self.__get_files(mod_id, file_id)

    def __make_request(self, path: str, retry: bool = True):
        resp = requests.get(f"{configuration.c_forge_api}/addon/{path}", headers=configuration.request_headers, timeout=60)
        if resp.status_code != 200:
            if retry:
                return self.__make_request(path, retry=False)
            raise ConnectionError(resp.status_code, resp.reason, "Failed after 1 retry")
        return resp.json()

    def __get_files(self, mod_id: int, file_id: int):
        file1 = self.__make_request(str(mod_id))
        if file1.get("id") == file_id:
            self.__set_file(file1)
            return
        files2 = self.__make_request(f"{mod_id}/files")
        for file in files2:
            if file.get("id") == file_id:
                self.__set_file(file)
                return

    def __set_file(self, file_json: dict):
        self.file = {
            "name": file_json.get("fileName"),
            "url": file_json.get("downloadUrl")
        }

    def get(self):
        return self.file


class ModRepository:
    def __init__(self, files_from_manifest: list, progress: callable = None):
        self.mod_list = list()
        self.errors = list()
        self.progress_callback = progress
        self.__load_mods(files_from_manifest)

    def __load_mods(self, file_list: list):
        for i, file in enumerate(file_list):
            if self.progress_callback is not None:
                self.progress_callback(i, len(file_list))

            if not file.get("required"):
                continue
            try:
                self.mod_list.append(
                    Mod(file.get("projectID"), file.get("fileID"))
                )
            except ConnectionError:
                self.errors.append(
                    (file.get("projectID"), file.get("fileID"))
                )

    def get(self):
        return self.mod_list, self.errors
