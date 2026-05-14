
# Quick Start

Below is the simplest possible how-to.

## 1. Order the PCB

1. Install [KiCad 10](https://www.kicad.org/download/)
2. Clone this repo or download the kicad files.
2. Open [`kicad/kicad.kicad_sch`](../kicad/kicad.kicad_sch) or one of the available kicad pcb designs.
3. Generate Gerbers: **File → Fabrication Outputs → Gerbers**
4. Upload to a PCB manufacturer — [AISLER](https://aisler.net) is recommended (EU-based, good quality)

## 2. Buy the Components 

| Part | Notes |
|---|---|
| MCU | **nice!nano v2** (pricier, excellent build quality) or **SuperMini nRF52840** (budget option, same firmware) |
| IMU | BNO085 breakout (GY-BNO08X) |
| Display | SSD1306 0.91" OLED |
| 2× push buttons | Tactile SMD, CK KSC6xxG footprint |
| Latch switch | SPDT or SPST, for B+ power line |
| LiPo battery | 3.7V ~100mAh, smallest that fits under Pro Micro footprint (~20×30mm) |


**Battery life estimate**: with the recommended ~100mAh cell, expect about 4 to 6 hours of continuous use with the display on and BLE enabled.

**Note**: SuperMini clones sometimes need to have a resistor added to allow reading of battery voltage. It is not a showstopper but the displayed battery status will be always 0%.

## 3. Solder

1. **Display** — solder first, it will get blocked by the MCU board.
2. **BNO085 module** — next
3. **MCU** — last; make sure it sits high enough above the PCB for the battery to fit underneath. Consider using machined pin headers (sockets) so you can swap the MCU and battery without desoldering.

## 4. Flash

### 4.1. Install mpremote

**Linux:** `pip install mpremote --break-system-packages`

**macOS:** `pip3 install mpremote`

**Windows:** install [Python from python.org](https://www.python.org/downloads/) (check "Add to PATH"), then `pip install mpremote`

If `mpremote` is not found after installing on Linux/macOS, add it to your PATH:
- Linux: `echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc && source ~/.bashrc`
- macOS: `echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.zshrc && source ~/.zshrc`

### 4.2 Flash MicroPython (one-time)

1. Download the UF2 (from jkorte-dev):
   ```bash
   curl -L -o micropython-NRF52840-supermini-v1.26.1.uf2 \
     https://raw.githubusercontent.com/jkorte-dev/micropython-board-NRF52840/main/firmware/micropython-NRF52840-supermini-v1.26.1.uf2
   ```
2. Connect the MCU with a data USB cable to your computer.
3. Short the **RST** and **GND** pins twice in quick succession — the board mounts as a drive called `NICENANO`
4. Copy the firmware to the bootloader drive:

   **Linux:** `cp micropython-NRF52840-supermini-v1.26.1.uf2 /run/media/$USER/NICENANO/`

   **macOS:** `cp micropython-NRF52840-supermini-v1.26.1.uf2 /Volumes/NICENANO/`

   **Windows:** drag and drop the `.uf2` file onto the `NICENANO` drive in Explorer.

   The drive unmounts automatically.

### 4.3 Flash the firmware

1. Go to the [latest workflow run](https://github.com/evaEko/knife_whetting_level/actions/workflows/build.yml) and download the `knife_level_firmware` artifact. Extract the zip.
2. Go to the extracted folder.
2. Edit `src/angles.csv` or `src/config.txt` before flashing. See [HOW_TO_FIRMWARE.md](HOW_TO_FIRMWARE.md) for details.
5. Run from the folder with extract firmware:

```bash
python flash.py
```

Select your port from the menu when prompted. The script will flash all files and reset the board.

### Android app (optional)

Go to the same [workflow run page](https://github.com/evaEko/knife_whetting_level/actions/workflows/build.yml) and download the `knife_level_android_apk` artifact.

1. Extract the artifact zip on your Android device or computer
2. Copy `app-debug.apk` to your phone if needed
3. Open the APK on the phone and allow installation from unknown sources if Android asks
4. Install the app

**Compatibility**

- Android only
- The app connects directly to the device over BLE; no account, pairing, or cloud service is involved

**Known issues**

- If the MCU is not in measurement mode, the app may stay connected but live angle updates pause until the MCU returns to measuring
- BLE reconnect behavior can vary by phone vendor and Android version; if discovery fails after a disconnect, wait a moment and try again
- The app is distributed as an APK artifact, not through Google Play, so Android may show the standard warning about installing from unknown sources

## 5. Use

**Power on** — battery percentage shows for 1.5 s, then the live pitch angle appears.

### Step 1 — Calibrate

Calibration records the full 3D orientation of the sensor placed flat on the stone. This is the zero reference — all angle readings are relative to the stone surface regardless of how the sensor is mounted or rotated.

Do this at the start of every session, after you have positioned your stone. Redo it whenever the stone moves.

1. Place the device flat on your stone.
2. Short-press the low button to open **Settings**.
3. On **Calibration**, short-press the low button.
4. Short-press the low button again — after a settle delay the reading is saved and the device returns to measurement

The display now shows angles relative to your stone surface.

### Step 2 — Set an angle (optional)

> You can sharpen using the live angle display without setting any target. Setting an angle adds deviation detection with alert: the display inverts when you drift more than the configured deviation threshold (configurable), giving you a visual alert.

Short-press the top button to open the preset menu. Cycle through options with the top button, confirm with the low button.

**To use a preset knife angle** — cycle to the knife name and press low.

**To set a custom angle** - cycle to **Custom** and press low.

**To clear the target** — cycle to **Clear** in the preset menu and press low.

## 6. Charging

> **Important (known limitation):** while charging over USB, the latch power switch must be in the ON position. If the latch switch is OFF, the battery will not charge.

With the recommended ~100mAh battery, a full charge is usually enough for one sharpening session. 

## 8. Reflashing

When you want to update the firmware:

1. Connect to computer.
2. **Short-press both buttons at the same time** — the display shows "Ready to flash..."
   - **Note:** once flash mode is active, the only way out is to reset (short RST to GND) or power off/on.
3. If you are flashing from the downloaded firmware package, run `python flash.py`
4. If you are flashing from this repository checkout, run `python build_flash.py`
