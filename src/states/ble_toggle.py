import machine
from state import State

_CONFIG_PATH = 'config.py'


def read_ble_enabled():
    try:
        with open(_CONFIG_PATH) as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith('BLE_ENABLED') and '=' in stripped:
                    value = stripped.split('=', 1)[1].strip()
                    return value.startswith('True')
    except Exception:
        pass
    return False


def write_ble_enabled(enabled):
    new_line = 'BLE_ENABLED = ' + ('True' if enabled else 'False') + '\n'
    try:
        with open(_CONFIG_PATH) as f:
            lines = f.readlines()
    except Exception:
        lines = []

    replaced = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('BLE_ENABLED') and '=' in stripped:
            lines[i] = new_line
            replaced = True
            break

    if not replaced:
        if lines and not lines[-1].endswith('\n'):
            lines[-1] = lines[-1] + '\n'
        lines.append('\n')
        lines.append('# Enable Bluetooth Low Energy UART service on boot.\n')
        lines.append(new_line)

    try:
        with open(_CONFIG_PATH, 'w') as f:
            f.write(''.join(lines))
    except Exception as e:
        print('BLE write error:', e)


class BleToggleState(State):
    def __init__(self):
        pass

    def enter(self, device):
        device.display.invert(False)
        self._draw(device)

    def update(self, device):
        event = device.buttons.update()
        if event == ('short', 'low'):
            write_ble_enabled(not read_ble_enabled())
            machine.reset()

        if event is not None:
            from states.settings_menu import SettingsMenuState
            return SettingsMenuState()

        return None

    def _draw(self, device):
        enabled = read_ble_enabled()
        device.display.show_ble_toggle(enabled)
