import os


class StorageService:
    def __init__(self, path="data.txt"):
        self._path = path
        self._data = {}

    def load(self):
        self._data = {}
        try:
            with open(self._path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    key, _, val = line.partition("=")
                    self._data[key.strip()] = val.strip()
        except OSError:
            pass
        return self._data

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = str(value)
        self._save()

    def remove(self, key):
        if key in self._data:
            del self._data[key]
            self._save()

    def clear(self):
        self._data = {}
        try:
            os.remove(self._path)
        except OSError:
            pass

    def _save(self):
        with open(self._path, "w") as f:
            for key, val in self._data.items():
                f.write("{k}={v}\n".format(k=key, v=val))
