# Quick Start

Below is the simplest possible how-to recipe.

## 1. Order the PCB

1. Install [KiCad 9](https://www.kicad.org/download/)
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


**Note**: SuperMini clones sometimes need to have a resistor added to allow reading of battery voltage.

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

```bash
pip install mpremote --break-system-packages
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc && source ~/.bashrc
```

### Flash MicroPython (one-time)

1. Short the **RST** and **GND** pins twice in quick succession — the board mounts as a drive called `NICENANO`
2. Download the UF2 (from jkorte-dev):
   ```bash
   curl -L -o micropython-NRF52840-supermini-v1.24.0-preview.uf2 \
     https://raw.githubusercontent.com/jkorte-dev/micropython-board-NRF52840/main/firmware/micropython-NRF52840-supermini-v1.24.0-preview.uf2
   ```
3. Copy the firmware to the bootloader drive:
   ```bash
   cp micropython-NRF52840-supermini-v1.24.0-preview.uf2 /run/media/$USER/NICENANO/
   ```
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

1. **Power on** — battery percentage shows for 1.5 s, then the live pitch angle appears
2. **Board levelling (first time only)** — if the sensor is not mounted perfectly flat, correct for it: long-press the low button, place the device on a flat surface, short-press the low button to save. Reboot. The correction is stored permanently.
3. **Calibrate** — place the device on your reference surface and short-press the low button; press again to lock it in. This sets the zero point. The display then shows angles relative to this reference.
4. **Select a preset** — short-press the top button to open the preset menu, cycle through your knives, confirm with the low button. The display will show the preset angle (e.g. 18°) when you are holding the knife at the correct sharpening angle.
5. **Sharpen** — the display inverts when you drift more than 2° from the preset angle. Switching presets always stays relative to your calibration — no compounding.
6. **Reflash mode** — long-press the top button to drop to REPL so you can update the firmware.

---

## 6. Reflashing

When you want to update the firmware:

1. Connect to computer.
2. **Hold the low button** until the display shows "Flash mode / ready..."
3. Run `build_flash.py` immediately

