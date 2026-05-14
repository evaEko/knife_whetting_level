class PresetStore:
    def __init__(self):
        self._presets = []  # list of (name, angle)

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
        except OSError:
            pass

    def replace_all(self, presets):
        self._presets = [(name, float(angle)) for name, angle in presets]
        self.save()

    def save(self):
        try:
            with open('angles.csv', 'w') as f:
                f.write('# name, angle (degrees)\n')
                for name, angle in self._presets:
                    f.write("{}, {:g}\n".format(name, angle))
        except OSError:
            pass

    def __len__(self):
        return len(self._presets)

    def __iter__(self):
        return iter(self._presets)
