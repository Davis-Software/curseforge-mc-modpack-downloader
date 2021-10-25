import json


class ManifestObject:
    def __init__(self, data: int or str or list or dict):
        self.data = data

    def get(self, key: int or str = None) -> int or str or list or dict:
        if key is not None:
            data = self.data.get(key)
        else:
            data = self.data
        return ManifestObject(data)

    def type(self):
        return type(self.data)

    def __int__(self):
        return int(self.data)

    def __str__(self):
        return str(self.data)

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)


class ModManifest(json.JSONDecoder):
    def __init__(self, manifest_file: str):
        super().__init__(object_hook=None, object_pairs_hook=None)
        with open(manifest_file, "r") as f:
            self.data = self.decode(f.read())

    def get(self, key: str = None):
        if key is not None:
            data = self.data.get(key)
        else:
            data = self.data

        return ManifestObject(data)
