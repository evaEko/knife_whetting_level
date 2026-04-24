# How To

## Setup

### Install Python

Make sure Python 3 is installed:

```bash
python --version
```

### Flash MicroPython (one-time)

MicroPython must be flashed to the board before deploying any code. The firmware is included in the repo under `assets/`.

1. **Enter bootloader** — double-tap the reset button on the board. A drive called `NICENANO` will mount.
2. **Flash**:
   ```bash
   cp assets/micropython-NRF52840-supermini-v1.24.0-preview.uf2 /run/media/$USER/NICENANO/
   ```
   The board reboots automatically when the copy completes.
3. **Verify** — the `NICENANO` drive disappears and a serial port (`/dev/ttyACM0`) appears in `dmesg`.

### Install mpremote

```bash
pip install mpremote --break-system-packages
```

If `mpremote` is not found after installing, add `~/.local/bin` to your PATH:

```bash
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc && source ~/.bashrc
```

---

## Flashing

### Connecting the MCU

Run the following in one terminal before plugging in the device — you will see which tty is assigned:

```bash
dmesg -w
```

Look for a line like:

```
cdc_acm 3-2:1.0: ttyACM0: USB ACM device
```

That `ttyACM0` (or similar) is the port you will use.

### Getting the device ready to flash

mpremote needs the device to be at the MicroPython REPL prompt before it can transfer files. There are two ways to get there:

**Option 1 — Long-press the low button (recommended)**

Hold the low button (P1.11) for 1 second. The display will show "Flash mode / ready..." and the device drops to REPL. Run `build_flash.py` immediately after.

**Option 2 — Flash within 1 second of boot**

`main.py` has a 1-second delay at startup before it begins running. If you unplug and replug the device, you have approximately 1 second to start `build_flash.py` before the window closes.

### Flash automatically

Run from the `knife_level_python` directory:

```bash
python build_flash.py /dev/ttyACM0
```

The script auto-discovers all files under `src/` (excluding `src/tools/`) and flashes them in one go. `angles.csv` is also flashed automatically.

### Flash manually

Run from the `knife_level_python` directory:

```bash
mpremote connect /dev/ttyACM0 mkdir :drivers
mpremote connect /dev/ttyACM0 mkdir :states
mpremote connect /dev/ttyACM0 cp src/config.py :config.py
mpremote connect /dev/ttyACM0 cp src/ctx.py :ctx.py
mpremote connect /dev/ttyACM0 cp src/angles.csv :angles.csv
mpremote connect /dev/ttyACM0 cp src/main.py :main.py
mpremote connect /dev/ttyACM0 cp src/drivers/battery.py :drivers/battery.py
mpremote connect /dev/ttyACM0 cp src/drivers/bno085.py :drivers/bno085.py
mpremote connect /dev/ttyACM0 cp src/drivers/button.py :drivers/button.py
mpremote connect /dev/ttyACM0 cp src/drivers/oled.py :drivers/oled.py
mpremote connect /dev/ttyACM0 cp src/drivers/ssd1306.py :drivers/ssd1306.py
mpremote connect /dev/ttyACM0 cp src/states/__init__.py :states/__init__.py
mpremote connect /dev/ttyACM0 cp src/states/calibration.py :states/calibration.py
mpremote connect /dev/ttyACM0 cp src/states/flash.py :states/flash.py
mpremote connect /dev/ttyACM0 cp src/states/init.py :states/init.py
mpremote connect /dev/ttyACM0 cp src/states/measure.py :states/measure.py
mpremote connect /dev/ttyACM0 cp src/states/select_angle.py :states/select_angle.py
mpremote connect /dev/ttyACM0 reset
```

### REPL access

```bash
mpremote connect /dev/ttyACM0 repl
```

Hit **Ctrl+C** to interrupt `main.py` and get the `>>>` prompt.
