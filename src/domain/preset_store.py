class PresetStore:
    def __init__(self):
        self._presets = []   # list of (name, angle)
        self.index    = 0    # current selection (0 = custom)

    def load(self):
        try:
            with open('angles.csv') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split(',')
                    if len(parts) == 2:
                        self._presets.append((parts[0].strip(), float(parts[1].strip())))
            print(f"Loaded {len(self._presets)} angle presets")
        except Exception as e:
            print(f"angles.csv error: {e}")

    def __len__(self):
        return len(self._presets)

    def __getitem__(self, i):
        return self._presets[i]

    def __iter__(self):
        return iter(self._presets)

    @property
    def empty(self):
        return len(self._presets) == 0
