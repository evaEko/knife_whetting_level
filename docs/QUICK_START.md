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

Go to the [latest Actions run](https://github.com/evaEko/knife_whetting_level/actions/runs/) and download the `knife_level_firmware` artifact. Extract the zip — it contains everything you need.

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

### Level the board (first time only)

> **What this is for:** The sensor may not sit perfectly flat on the PCB due to soldering, sockets, or mechanical tolerances. Board levelling stores a correction angle so all subsequent readings are accurate regardless of mounting. It is needed only the first time: the setting survives flashing and when the position of the sensor changes.

1. Long-press the low button — display shows "Place on straight surface"
2. Place the device on a known flat surface
3. Short-press the low button — display shows "Reboot!"
4. Power cycle the device — the correction is now active

---

## 5. Use

**Power on** — battery percentage shows for 1.5 s, then the live pitch angle appears.

### Step 1 — Level the board (first time only)

The sensor may not sit perfectly parallel to the surface you attach the device to — this depends on how the PCB was soldered, what adapter you use (magnet, plate, etc.), and how it sits against the knife. Board levelling measures this offset and stores a permanent correction so all subsequent readings are accurate.

You only need to do this once. The correction survives flashing and power cycles.

1. Long-press the low button — display shows "Place on straight surface"
2. Lay the device flat on a known level surface
3. Short-press the low button — device reboots with the correction active

### Step 2 — Calibrate for your session

Calibration sets the zero point for this sharpening session. Your sharpening stone does not need to be level — the device measures relative to wherever it is. What matters is that the stone is in its working position before you calibrate.

Do this at the start of every session, after you have positioned your stone.

1. Place the device flat on your stone 
2. Short-press the low button — display shows "Calibrating..."
3. Short-press again to lock in the zero point

The display now shows angles relative to your stone surface.

### Step 3 — Set an angle and sharpen

> **Optional.** You can sharpen using the live angle display without setting any target — just watch the number. Setting an angle only adds one thing: the display inverts when you drift more than 2° (default, can be adjusted in config.py; However you will need to follow []()) from it, giving you a visual alert.

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

## 6. Charging

> **Important (known limitation):** while charging over USB, the latch power switch must be in the ON position. If the latch switch is OFF, the battery will not charge.

---

## 7. Reflashing

When you want to update the firmware:

1. Connect to computer.
2. **Short-press both buttons at the same time** — the display shows "Ready to flash..."
   - **Note:** once flash mode is active, the only way out is to reset (short RST to GND) or power off/on.
3. Run `build_flash.py` immediately

