# Quick Start

Below is the simplest possible how-to recipe.

## 1. Order the PCB

1. Install [KiCad 9](https://www.kicad.org/download/)
2. Clone this repo or download the kicad files.
2. Open [`kicad/kicad.kicad_sch`](../kicad/kicad.kicad_sch)
3. Generate Gerbers: **File → Fabrication Outputs → Gerbers**
4. Upload to a PCB manufacturer — [AISLER](https://aisler.net) is recommended (EU-based, good quality)

---

## 2. Buy the Parts

| Part | Notes |
|---|---|
| MCU | **nice!nano v2** (pricier, excellent build quality) or **SuperMini nRF52840** (budget option, same firmware) |
| IMU | BNO085 breakout (GY-BNO08X) |
| Display | SSD1306 0.91" OLED |
| 2× push buttons | Tactile SMD, CK KSC6xxG footprint |
| Latch switch | SPDT or SPST, for B+ power line |
| LiPo battery | 3.7V ~100mAh, smallest that fits under Pro Micro footprint (~20×30mm) |


**Battery life estimate**: with the recommended ~100mAh cell, expect about 4 to 6 hours of continuous use with the display on and BLE enabled. If the device sits still for long periods, runtime can stretch a bit further, but plan around roughly 5 hours.

**Note**: SuperMini clones sometimes need to have a resistor added to allow reading of battery voltage. IT is not a showstopper but the displayed battery status will be always 0%.

---

## 3. Solder

1. **Display** — solder first, it will get blocked by the MCU board.
2. **BNO085 module** — next
3. **MCU** — last; make sure it sits high enough above the PCB for the battery to fit underneath. Consider using machined pin headers (sockets) so you can swap the MCU without desoldering.

Connect the battery wires to B+ and B- pads on the PCB.

---

## 4. Flash

### Download the firmware

Go to the [latest workflow run](https://github.com/evaEko/knife_whetting_level/actions/workflows/build.yml) and download the `knife_level_firmware` artifact. Extract the zip — it contains everything you need.

> **Want to change preset angles or tolerance?** Edit `src/angles.csv` or `src/config.py` before flashing. See [HOW_TO_FIRMWARE.md](HOW_TO_FIRMWARE.md) for the full manual build and flash instructions.

### Install mpremote

**Linux:** `pip install mpremote --break-system-packages`

**macOS:** `pip3 install mpremote`

**Windows:** install [Python from python.org](https://www.python.org/downloads/) (check "Add to PATH"), then `pip install mpremote`

If `mpremote` is not found after installing on Linux/macOS, add it to your PATH:
- Linux: `echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc && source ~/.bashrc`
- macOS: `echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.zshrc && source ~/.zshrc`

### Flash MicroPython (one-time)

1. Short the **RST** and **GND** pins twice in quick succession — the board mounts as a drive called `NICENANO`
2. Download the UF2 (from jkorte-dev):
   ```bash
   curl -L -o micropython-NRF52840-supermini-v1.26.1.uf2 \
     https://raw.githubusercontent.com/jkorte-dev/micropython-board-NRF52840/main/firmware/micropython-NRF52840-supermini-v1.26.1.uf2
   ```
3. Copy the firmware to the bootloader drive:

   **Linux:** `cp micropython-NRF52840-supermini-v1.26.1.uf2 /run/media/$USER/NICENANO/`

   **macOS:** `cp micropython-NRF52840-supermini-v1.26.1.uf2 /Volumes/NICENANO/`

   **Windows:** drag and drop the `.uf2` file onto the `NICENANO` drive in Explorer.

4. The drive unmounts automatically and the board reboots

### Flash the firmware

Connect the MCU via USB, then run from the extracted folder:

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

**What the app is for**

- Calibrate from the phone
- Change device settings exposed over BLE
- Manage preset angles

**Known issues**

- If the MCU is not in measurement mode, the app may stay connected but live angle updates pause until the MCU returns to measuring
- BLE reconnect behavior can vary by phone vendor and Android version; if discovery fails after a disconnect, wait a moment and try again
- The app is distributed as an APK artifact, not through Google Play, so Android may show the standard warning about installing from unknown sources

### Level the board (first time only)

> **What this is for:** The sensor may not sit perfectly flat on the PCB due to soldering, sockets, or mechanical tolerances. Board levelling stores a correction angle so all subsequent readings are accurate regardless of mounting. It is needed only the first time: the setting survives flashing and when the position of the sensor changes.

1. Short-press the low button to open **Settings**
2. Press the top button until **Level** is shown
3. Short-press the low button to enter board levelling
4. Place the device on a known flat surface
5. Short-press the low button once, then keep the device still for about 1 second
6. The device saves the board offset and reboots automatically

---

## 5. Use

**Power on** — battery percentage shows for 1.5 s, then the live pitch angle appears.

### Step 1 — Level the board (first time only)

The sensor may not sit perfectly parallel to the surface you attach the device to — this depends on how the PCB was soldered, what adapter you use (magnet, plate, etc.), and how it sits against the knife. Board levelling measures this offset and stores a permanent correction so all subsequent readings are accurate.

You only need to do this once. The correction survives flashing and power cycles.

1. Short-press the low button to open **Settings**
2. Press the top button until **Level** is shown
3. Short-press the low button to enter level mode
4. Lay the device flat on a known level surface
5. Short-press the low button — after a short settle delay, the device reboots with the correction active

### Step 2 — Calibrate for your session

Calibration sets the zero point for this sharpening session. Your sharpening stone does not need to be level — the device measures relative to wherever it is. What matters is that the stone is in its working position before you calibrate.

Do this at the start of every session, after you have positioned your stone.

1. Place the device flat on your stone 
2. Short-press the low button to open **Settings**
3. Leave **Calib** selected and short-press the low button again
4. The current reading is stored as zero for this session

The display now shows angles relative to your stone surface.

### Step 3 — Set an angle and sharpen

> **Optional.** You can sharpen using the live angle display without setting any target — just watch the number. Setting an angle only adds one thing: the display inverts when you drift more than 2° by default, giving you a visual alert. This threshold can be adjusted in `config.py` or from the Android app settings.

Short-press the top button to open the preset menu. Cycle through options with the top button, confirm with the low button.

**To use a preset knife angle** — cycle to the knife name and press low. The display shows the live angle; it inverts when you drift more than 2° from the target.

**To set a custom angle:**
1. Cycle to **Custom angle** (first item in the menu) and press low
2. Hold the knife at the angle you want — the display shows the live angle relative to your stone
3. When you are happy with the angle shown, press low to lock it in

**To choose angle display format** — long-press the top button to open the format menu; cycle with top, confirm with low. The device reboots to apply the change.

### Step 4 — Happy sharpening

The display inverts when you drift more than 2° from the target angle, or when you reach the mirror angle on the opposite side of the blade. Switching presets mid-session always stays relative to your calibration — no compounding.

---

## 6. Tuning for your skill level

Open `src/config.py` before flashing and adjust `SMOOTHING` to match how consistently you hold an angle:

| Value | Feel | Best for |
|---|---|---|
| `0.3` | Very reactive — every wobble visible | Learning, diagnosing technique |
| `0.5` | Balanced | Casual sharpening |
| `0.7` | Smooth, stable during strokes | Most users (default) |
| `0.9` | Near-frozen display | Experienced sharpeners with consistent technique |

Higher smoothing means the number barely moves during a steady stroke, which is easier to read. The trade-off is it responds more slowly when you intentionally change angle.

---

## 7. Charging

> **Important (known limitation):** while charging over USB, the latch power switch must be in the ON position. If the latch switch is OFF, the battery will not charge.

With the recommended ~100mAh battery, a full charge is usually enough for one sharpening session, but not for all-day continuous use. If you want markedly longer runtime, use the largest cell that still fits your mechanical layout.

---

## 8. Reflashing

When you want to update the firmware:

1. Connect to computer.
2. **Short-press both buttons at the same time** — the display shows "Ready to flash..."
   - **Note:** once flash mode is active, the only way out is to reset (short RST to GND) or power off/on.
3. If you are flashing from the downloaded firmware package, run `python flash.py`
4. If you are flashing from this repository checkout, run `python build_flash.py`

