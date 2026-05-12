class ConfigService:
    _config_file = None
    _keys = []

    @classmethod
    def load(cls, config_file):
        cls._config_file = config_file
        with open(cls._config_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                setattr(cls, key, cls._cast(val.strip()))
                if key not in cls._keys:
                    cls._keys.append(key)

    @classmethod
    def set(cls, key, value):
        if key not in cls._keys:
            raise KeyError(key)
        setattr(cls, key, value)
        cls._save()

    @classmethod
    def _save(cls):
        with open(cls._config_file, "w") as f:
            for key in cls._keys:
                f.write("{key}={val}\n".format(key=key, val=getattr(cls, key)))

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
