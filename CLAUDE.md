# Knife Level — AI Contributor Context

## What this project is

A digital angle level for knife sharpening. The device measures blade pitch via an IMU, displays it on a small OLED, and alerts the user when they drift from a calibrated target angle. Runs MicroPython on an nRF52840 microcontroller.

## Hardware

| Component | Part | Notes |
|---|---|---|
| MCU | nice!nano v2 (or SuperMini nRF52840) | nRF52840, BLE, built-in LiPo charger |
| IMU | BNO085 | I2C via `GY-BNO08X` breakout, addr `0x4B` |
| Display | SSD1306 0.91" OLED | I2C, 128×32 px, addr `0x3C` |
| Button | Tactile SMD push button | Calibration/power control |
| Battery | Single-cell LiPo 3.7V | Connected to B+/B- on MCU |

Pin assignments are in `src/config.py`. Pin notation: first digit = port, last two = pin number (e.g. `38` = P1.06).

## Repository layout

```
src/
  main.py           — main loop and state dispatch
  config.py         — all pin numbers, I2C addresses, thresholds
  drivers/
    bno085.py       — BNO085 IMU driver (I2C, rotation vector / pitch)
    ssd1306.py      — SSD1306 OLED driver
    battery.py      — battery % via nRF52840 VDDHDIV5 SAADC (no external resistors)
    button.py       — debounced short/long press detection
    oled.py         — display helpers (angle, battery, error)
  states/
    __init__.py     — state constants
    ready.py        — display angle, invert on deviation
    calibration.py  — set offset angle
  tools/
    scan.py         — I2C bus scanner (dev utility, not flashed)
    test_bno.py     — BNO085 test script (dev utility, not flashed)
kicad/              — KiCad 9 schematic and PCB layout
build_flash.py      — flash script (auto-discovers src/ files, see below)
```

## Flashing

```bash
python build_flash.py /dev/ttyACM0
```

`build_flash.py` auto-discovers all `.py` files under `src/` (excluding `tools/`... actually it includes everything — see note below). MicroPython must already be flashed to the board (see README).

> Note: `src/tools/` is excluded from flashing — dev scripts stay off the device.

## State machine

```
READY ──short press──▶ CALIBRATION
CALIBRATION ──short press──▶ READY  (saves current angle as offset)
ANY STATE ──long press──▶ soft power off  (wake: press button again)
```

In READY: if a calibration offset is set, the display inverts when the angle deviates more than `DEVIATION_THRESHOLD` degrees (default 2°) from the target, or when near the mirror angle on the opposite side.

## Battery measurement

`drivers/battery.py` reads the nRF52840's internal `VDDHDIV5` SAADC channel via direct memory-mapped register access (`machine.mem32`). This is nRF52840-specific — it will not work on RP2040 or other MCUs. No external resistor divider is needed.

## Known issues

- **Soft-off drains battery** — long-press power off enters a low-power idle loop but does not cut power. Workaround: physical switch on B+ line.
- **Unreliable wake** — device sometimes does not wake from soft-off on button press. Connecting USB (charging) reliably wakes it.

## Planned (v2.0)

- Second button for cycling preset angle profiles
- Predefined angles in config (e.g. Japanese 15°, European 20°)
- Hardware power latch on PCB
- Android app via BLE GATT to set target angle remotely

## What NOT to change without care

- `drivers/battery.py` — uses nRF52840-specific register addresses; do not abstract or port without testing on real hardware
- `drivers/bno085.py` — tuned for rotation vector mode with the specific report interval; changing report type or interval affects the complementary filter behaviour in `main.py`
- Display is 128×32 px — the large-text rendering in `oled.py` is sized for this; don't assume a larger canvas
