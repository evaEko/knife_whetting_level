from helpers.vector_parser import VectorParser
from helpers.pitch_calculator import PitchCalculator


class CalibrationService:
    def __init__(self, storage):
        self._storage      = storage
        self._n_stone      = None
        self._n_target     = None
        self._target_angle = None

    def load(self):
        self._n_stone  = VectorParser.parse(self._storage.get('n_stone'))
        self._n_target = VectorParser.parse(self._storage.get('n_target'))
        raw = self._storage.get('target_angle')
        self._target_angle = float(raw) if raw is not None else None

    @property
    def n_stone(self):
        return self._n_stone

    @property
    def n_target(self):
        return self._n_target

    def has_stone(self):
        return self._n_stone is not None

    def has_target(self):
        return self._target_angle is not None

    def has_target(self):
        return self._n_target is not None

    def target_angle(self):
        return self._target_angle

    def set_target_angle(self, angle):
        self._target_angle = float(angle)
        self._storage.set('target_angle', "{:.4f}".format(self._target_angle))

    def clear_target(self):
        self._n_target     = None
        self._target_angle = None
        self._storage.remove('n_target')
        self._storage.remove('target_angle')

    def set_target(self, vec):
        """Persist n_target vector and the derived target_angle float."""
        self._n_target = vec
        fmt = "{:.6f},{:.6f},{:.6f}".format(vec[0], vec[1], vec[2])
        self._storage.set('n_target', fmt)
        if self._n_stone is not None:
            angle = PitchCalculator.pitch(vec, self._n_stone)
            self._target_angle = angle
            self._storage.set('target_angle', "{:.4f}".format(angle))
