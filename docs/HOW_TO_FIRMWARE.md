# How To

## Setup

### Install Python

Make sure Python 3 is installed:

```bash
python --version
```

Python 3.10+ is recommended.

### Install git

**Linux (Debian/Ubuntu):**
```bash
sudo apt install git
```

**Linux (Fedora):**
```bash
sudo dnf install git
```

**macOS:**
```bash
brew install git
```

**Windows:** Download from [git-scm.com](https://git-scm.com/download/win) and run the installer.


### Flash MicroPython (one-time)

MicroPython must be flashed to the board before deploying any code. Download the UF2 from the upstream board-definition repository.

1. **Enter bootloader** — double-tap the reset button on the board. A drive called `NICENANO` will mount.
2. **Download UF2**:
   ```bash
   curl -L -o micropython-NRF52840-supermini-v1.26.1.uf2 \
     https://raw.githubusercontent.com/jkorte-dev/micropython-board-NRF52840/main/firmware/micropython-NRF52840-supermini-v1.26.1.uf2
   ```
3. **Flash**:

   **Linux:**
   ```bash
   cp micropython-NRF52840-supermini-v1.26.1.uf2 /run/media/$USER/NICENANO/
   ```
   **macOS:**
   ```bash
   cp micropython-NRF52840-supermini-v1.26.1.uf2 /Volumes/NICENANO/
   ```
   **Windows:** drag and drop the `.uf2` file onto the `NICENANO` drive in Explorer.

   The board reboots automatically when the copy completes.
4. **Verify** — the `NICENANO` drive disappears and a serial port appears (`/dev/ttyACM0` on Linux, `/dev/tty.usbmodem*` on macOS, `COM*` on Windows).

### Downloading release artifacts

If you do not want to build from the repository manually, open the [Build artifacts workflow](https://github.com/evaEko/knife_whetting_level/actions/workflows/build.yml) and download:

- `knife_level_firmware` for the packaged firmware bundle
- `knife_level_android_apk` for the Android companion app APK

### Install mpremote

**Linux:**
```bash
pip install mpremote --break-system-packages
```
If `mpremote` is not found after installing, add `~/.local/bin` to your PATH:
```bash
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc && source ~/.bashrc
```

**macOS:**
```bash
pip3 install mpremote
```
If `mpremote` is not found, add it to your PATH:
```bash
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.zshrc && source ~/.zshrc
```

**Windows:** install [Python from python.org](https://www.python.org/downloads/) (check "Add to PATH" during install), then:
```
pip install mpremote
```

---

## Flashing

### Prepare sources

Clone the repository:

```bash
git clone https://github.com/evaEko/knife_whetting_level.git
cd knife_whetting_level
```

Edit [`src/config.py`](../src/config.py) to set your pin assignments, angle deviation threshold, display smoothing, and default angle format before flashing. The file is commented — each setting explains itself.

You can also edit [`src/angles.csv`](../src/angles.csv) before flashing if you want to ship a default preset list in the firmware image.

### Connecting the MCU

Plug in the device and find the assigned serial port:

**Linux:** run `dmesg -w` before plugging in and look for a line like:
```
cdc_acm 3-2:1.0: ttyACM0: USB ACM device
```
The port will be `/dev/ttyACM0` or similar.

**macOS:** run `ls /dev/tty.usbmodem*` after plugging in. The port will be something like `/dev/tty.usbmodem1101`.

**Windows:** open Device Manager → Ports (COM & LPT) — the device will appear as `USB Serial Device (COM3)` or similar.

### Getting the device ready to flash

mpremote needs the device to be at the MicroPython REPL prompt before it can transfer files. There are two ways to get there:

**Option 1 — Short-press both buttons simultaneously (recommended)**

Press both buttons at the same time (short press). The display will show "Ready to flash..." and the device drops to REPL. Run `build_flash.py` immediately after.

Note: once flash mode is active, the only way out is to reset (short RST to GND) or power-cycle the device.

**Option 2 — Flash within 1 second of boot**

`main.py` has a 1-second delay at startup before it begins running. If you unplug and replug the device, you have approximately 1 second to start `build_flash.py` before the window closes.

### Flash automatically

Run from the `knife_level_python` directory:

```bash
python build_flash.py
```

You can also pass the serial port explicitly, for example:

```bash
python build_flash.py /dev/ttyACM0
```

The script auto-discovers all files under `src/` (excluding `src/tools/`) and flashes them in one go. `angles.csv` is also flashed automatically.

### Flash manually

Run from the `knife_level_python` directory:

```bash
mpremote connect /dev/ttyACM0 mkdir :domain
mpremote connect /dev/ttyACM0 mkdir :drivers
mpremote connect /dev/ttyACM0 mkdir :states
mpremote connect /dev/ttyACM0 cp src/config.py :config.py
mpremote connect /dev/ttyACM0 cp src/angles.csv :angles.csv
mpremote connect /dev/ttyACM0 cp src/device.py :device.py
mpremote connect /dev/ttyACM0 cp src/main.py :main.py
mpremote connect /dev/ttyACM0 cp src/state.py :state.py
mpremote connect /dev/ttyACM0 cp src/domain/__init__.py :domain/__init__.py
mpremote connect /dev/ttyACM0 cp src/domain/angle_engine.py :domain/angle_engine.py
mpremote connect /dev/ttyACM0 cp src/domain/preset_store.py :domain/preset_store.py
mpremote connect /dev/ttyACM0 cp src/domain/settings.py :domain/settings.py
mpremote connect /dev/ttyACM0 cp src/drivers/battery.py :drivers/battery.py
mpremote connect /dev/ttyACM0 cp src/drivers/ble.py :drivers/ble.py
mpremote connect /dev/ttyACM0 cp src/drivers/bno085.py :drivers/bno085.py
mpremote connect /dev/ttyACM0 cp src/drivers/button.py :drivers/button.py
mpremote connect /dev/ttyACM0 cp src/drivers/buttons.py :drivers/buttons.py
mpremote connect /dev/ttyACM0 cp src/drivers/config_rw.py :drivers/config_rw.py
mpremote connect /dev/ttyACM0 cp src/drivers/display.py :drivers/display.py
mpremote connect /dev/ttyACM0 cp src/drivers/sensor.py :drivers/sensor.py
mpremote connect /dev/ttyACM0 cp src/drivers/ssd1306.py :drivers/ssd1306.py
mpremote connect /dev/ttyACM0 cp src/states/__init__.py :states/__init__.py
mpremote connect /dev/ttyACM0 cp src/states/ble_toggle.py :states/ble_toggle.py
mpremote connect /dev/ttyACM0 cp src/states/calibrate.py :states/calibrate.py
mpremote connect /dev/ttyACM0 cp src/states/flash.py :states/flash.py
mpremote connect /dev/ttyACM0 cp src/states/level.py :states/level.py
mpremote connect /dev/ttyACM0 cp src/states/measure.py :states/measure.py
mpremote connect /dev/ttyACM0 cp src/states/select_angle.py :states/select_angle.py
mpremote connect /dev/ttyACM0 cp src/states/select_format.py :states/select_format.py
mpremote connect /dev/ttyACM0 cp src/states/settings_menu.py :states/settings_menu.py
mpremote connect /dev/ttyACM0 reset
```

### REPL access

```bash
mpremote connect /dev/ttyACM0 repl
```

Hit **Ctrl+C** to interrupt `main.py` and get the `>>>` prompt.

## Runtime controls

- Short-press low: open settings menu (`Calib`, `Level`, `Bluetooth`, `Exit`)
- Short-press top: open preset-angle selection menu
- Long-press top: open angle-format menu (`2 decimals`, `1 decimal`, `0/5 steps`), short-press low to confirm; format is saved and the device auto-reboots
- Short-press both buttons: enter flash mode

### Android companion app

Install it from the `knife_level_android_apk` workflow artifact described above.

The app is a BLE companion for setup, preset management, and easy usage.

It can:

- calibrate using the current live reading
- change device settings exposed over BLE
- manage preset angles

Compatibility:

- Android only
- installs as a standalone APK; it is not distributed through Google Play

Known issues:

- if the MCU is outside measurement mode, the app can stay connected while live angle updates pause
- BLE reconnect behavior varies by phone vendor and Android version; if the device does not immediately reappear after disconnect, wait a moment and try again (turn the device off and on).
