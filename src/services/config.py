class ConfigService:
    def __init__(self, path):
        self._path = path
        self._keys = []
        self._load()

    def _load(self):
        with open(self._path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                setattr(self, key, self._cast(val.strip()))
                if key not in self._keys:
                    self._keys.append(key)

    def set(self, key, value):
        if key not in self._keys:
            raise KeyError(key)
        setattr(self, key, value)
        self._save()

    def _save(self):
        with open(self._path, "w") as f:
            for key in self._keys:
                f.write("{key}={val}\n".format(key=key, val=getattr(self, key)))

    @staticmethod
    def _cast(val):
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            return val
