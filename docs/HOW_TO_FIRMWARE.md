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

Edit [`src/config.txt`](../src/config.txt) to set your pin assignments, deviation threshold, and capture delay before flashing. The file is a simple `key=value` text file — each line is self-explanatory.

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

Short-press both buttons simultaneously

Press both buttons at the same time (short press). The display will show "Ready to flash..." and the device drops to REPL.

Note: once flash mode is active, the only way out is to reset (short RST to GND) or power-cycle the device.

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

### REPL access

```bash
mpremote connect /dev/ttyACM0 repl
```

Hit **Ctrl+C** to interrupt `main.py` and get the `>>>` prompt.

## Runtime controls

- Short-press low: open settings menu (`Calibration`, `BLE`, `Deviation`, `Exit`)
- Short-press top (when calibrated): open preset-angle selection menu
- Short-press top (when uncalibrated): go directly to calibration capture
- Short-press both buttons: enter flash mode

### Settings menu

| Item | Behaviour |
|---|---|
| Calibration | Capture stone surface normal; top=cancel, low=capture |
| BLE | Toggle BLE on/off (top), back to menu (low) |
| Deviation | Adjust deviation threshold; top=+0.1°, long-top=+0.5°, low=save, long-low=cancel |
| Exit | Return to measurement |

### Preset-angle selection menu

Cycle through presets with top, confirm with low. Special items at the end:

| Item | Behaviour |
|---|---|
| Custom | Capture the current blade angle as target; top=cancel, low=capture |
| Clear | Unset the current target angle and return to measurement |
| Exit | Return to measurement without changing target |

### Android companion app

Install it from the `knife_level_android_apk` workflow artifact. Refer to [Android app how-to](HOW_TO_ANDROID.md)

