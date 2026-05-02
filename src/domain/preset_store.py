class PresetStore:
    def __init__(self):
        self._presets = []   # list of (name, angle)
        self.index    = 0    # current selection (0 = custom)

    def load(self):
        self._presets = []
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

    def find_name(self, angle):
        """Return the preset name whose angle matches, or None."""
        for name, a in self._presets:
            if abs(abs(a) - abs(angle)) < 1e-6:
                return name
        return None

    def __len__(self):
        return len(self._presets)

    def __getitem__(self, i):
        return self._presets[i]

    def __iter__(self):
        return iter(self._presets)

    @property
    def empty(self):
        return len(self._presets) == 0

    def replace_all(self, presets):
        self._presets = [(name, float(angle)) for name, angle in presets]
        if self.index > len(self._presets):
            self.index = 0
        self.save()

    def save(self):
        try:
            with open('angles.csv', 'w') as f:
                f.write('# knife_id, angle (degrees)\n')
                f.write('# Edit this file before flashing to add your knives\n')
                for name, angle in self._presets:
                    f.write(f"{name}, {float(angle):g}\n")
            try:
                import os
                os.sync()
            except Exception:
                pass
            print(f"Saved {len(self._presets)} angle presets")
        except Exception as e:
            print(f"angles.csv save error: {e}")
            raise
