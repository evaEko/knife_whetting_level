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

### Install tools

```bash
# Python 3 must be installed
pip install mpremote --break-system-packages
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc && source ~/.bashrc
```

Opening the repo in **VS Code** is recommended — it makes editing `angles.csv` and `config.py` straightforward.

### Customize before flashing

Edit [`src/angles.csv`](../src/angles.csv) to add your knives:

```
my tanto,18
japanese chef,15
european chef,20
```

Adjust any thresholds in [`src/config.py`](../src/config.py) if needed.

### Flash MicroPython (one-time)

1. Short the **RST** and **GND** pins twice in quick succession — the board mounts as a drive called `NICENANO`
2. Copy the firmware:
   ```bash
   cp assets/micropython-NRF52840-supermini-v1.24.0-preview.uf2 /run/media/$USER/NICENANO/
   ```
3. The drive unmounts automatically and the board reboots

### Flash the firmware

Connect the MCU via USB, then run:

```bash
python build_flash.py /dev/ttyACM0
```

Expected output:

```
Found 14 files, flashing to /dev/ttyACM0...
  mpremote connect /dev/ttyACM0 mkdir :drivers
  mpremote connect /dev/ttyACM0 mkdir :states
  mpremote connect /dev/ttyACM0 cp src/config.py :config.py
  mpremote connect /dev/ttyACM0 cp src/ctx.py :ctx.py
  mpremote connect /dev/ttyACM0 cp src/angles.csv :angles.csv
  ...
  mpremote connect /dev/ttyACM0 reset
Done.
```

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
6. **Reflash mode** — long-press the top button to drop to REPL so you can update the firmware or edit `angles.csv`.

---

## 6. Reflashing

When you want to update the firmware or change `angles.csv`:

1. Connect to computer.
2. **Hold the low button** until the display shows "Flash mode / ready..."
3. Run `build_flash.py` immediately

