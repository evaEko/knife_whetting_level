# Knife Level

> **⚠️ v2.0 is under heavy construction.**

### Planned for v2.0

- Predefined angle profiles — save and select common sharpening angles without manual calibration each time
- Hardware power latch button on the PCB for reliable turn off and wake, replacing the soft-off workaround

A digital angle level for knife sharpening. Measures blade pitch in real time using an IMU and displays the angle on a small OLED. Alerts you when you drift from your calibrated sharpening angle.

---

## Bill of Materials

| Component | Part | Notes |
|---|---|---|
| Microcontroller | **nice!nano v2** | nRF52840-based, chosen for built-in LiPo charging — no separate charging module needed |
| IMU | BNO085 | I2C, addr `0x4B` |
| Display | SSD1306 0.91" OLED | I2C, 128×32 px, addr `0x3C` |
| Button | Tactile push button | SMD, e.g. CK KSC6xxG footprint |
| Battery | LiPo 3.7V | Any single-cell LiPo |
| Resistor | **2× resistors for voltage divider** | Required to measure battery voltage via the BATIN/P0.04 pin. The nice!nano v2 has this divider built in on-board — no extra resistors needed if using nice!nano |

### Why nice!nano?

The nice!nano v2 integrates a LiPo charger. You can charge the battery over USB without any additional charging module or circuit. It also exposes a dedicated battery sense pin (BATIN/P0.04) with a built-in voltage divider, enabling direct battery percentage readout with no extra components.

---

## Pin Assignments

| Signal | nice!nano pin | nRF52840 GPIO |
|---|---|---|
| IMU SDA | pin 106 | P1.06 |
| IMU SCL | pin 104 | P1.04 |
| OLED SDA | pin 006 | P0.06 |
| OLED SCK | pin 008 | P0.08 |
| Calibration button | pin 111 | P1.11 |

All I2C buses run at 400 kHz.

---

## Features (v1.0)

- Displays current pitch angle in large text
- **Calibration**: set your target sharpening angle with a single button press
- **Visual alert**: display inverts when you drift more than 2° from the calibrated angle, or when you reach the mirror angle on the other side of the blade
- **Idle mode**: IMU report rate drops automatically after 60 s of no movement to save power
- **Battery display**: shows battery percentage on startup
- **Power off**: long-press the button from any state; press again to wake

---

## Software Architecture

```
states/
  ready.py        — display angle, invert on deviation
  calibration.py  — set offset angle
battery.py        — read VDDHDIV5 via nRF52840 SAADC
button.py         — debounced short/long press detection
oled.py           — display helpers (angle, battery, error)
config.py         — all pin numbers, I2C addresses, thresholds
main.py           — main loop, state dispatch, idle/wake logic
```

---

## Hardware Assembly

The KiCad schematic is in [`kicad/kicad.kicad_sch`](kicad/kicad.kicad_sch). Open it in KiCad 9 to view the full schematic and generate gerbers for PCB fabrication.

Wire up the components according to the pin assignments table above. The nice!nano sits on the PCB via its castellated pads or through-hole pins.

If you are using a ProMicro nRF52840 instead of the nice!nano, make sure the voltage divider resistors are in place on the BATIN/P0.04 line — without them battery measurement will not work.

If you have the PCB, solder in this order: display first, then the BNO085 module, then the MCU. Leave enough clearance under the MCU for the battery. Connect the battery wires to B+ and B- directly on the MCU board.

---

## Setup

### 1. Flash MicroPython (one-time)

The firmware file is included in the repo (`micropython-NRF52840-supermini-v1.24.0-preview.uf2`).

1. **Enter bootloader**: double-tap the reset button on the nice!nano. A drive called `NICENANO` will mount.
2. **Flash**:
   ```bash
   cp micropython-NRF52840-supermini-v1.24.0-preview.uf2 /run/media/$USER/NICENANO/
   ```
   The board reboots automatically when the copy completes.
3. **Verify** — the drive disappears and a serial port (`/dev/ttyACM0`) appears.

### 2. Install mpremote

```bash
pip install mpremote --break-system-packages
```

### 3. Deploy code

To find which serial port your MCU is on, run `dmesg -w` in one terminal before plugging in — you will see the assigned tty (e.g. `ttyACM0`) in the output.

Then flash to the tty:

```bash
mpremote connect /dev/ttyACM0 cp config.py :config.py
mpremote connect /dev/ttyACM0 cp main.py :main.py
mpremote connect /dev/ttyACM0 cp button.py :button.py
mpremote connect /dev/ttyACM0 cp battery.py :battery.py
mpremote connect /dev/ttyACM0 cp oled.py :oled.py
mpremote connect /dev/ttyACM0 cp bno085.py :bno085.py
mpremote connect /dev/ttyACM0 cp ssd1306.py :ssd1306.py
mpremote connect /dev/ttyACM0 mkdir :states
mpremote connect /dev/ttyACM0 cp states/__init__.py :states/__init__.py
mpremote connect /dev/ttyACM0 cp states/ready.py :states/ready.py
mpremote connect /dev/ttyACM0 cp states/calibration.py :states/calibration.py
mpremote connect /dev/ttyACM0 reset
```

### 4. REPL access

```bash
screen /dev/ttyACM0 115200
```

---

## Known Issues

**Battery drain in soft-off mode** — when you power off with a long press, the MCU enters a low-power idle loop but does not fully cut power. The battery will slowly drain over time.

Workaround: add a physical switch in series with the B+ wire between the battery and the MCU. Flip it off when storing the device.

**Unreliable wake from soft-off** — the device fairly often does not wake up on button press. A workaround is to connect it to a power supply (USB charging), which reliably brings it back. The physical power switch described above also avoids this entirely by doing a hard power cycle. A dedicated power button will be added in the next version.

---

## Configuration

All tunable settings are in [`config.py`](config.py):

| Setting | Default | Description |
|---|---|---|
| `DEVIATION_THRESHOLD` | `2.0` | Degrees off-target before the display inverts to warn you |
| `LONG_PRESS_MS` | `1000` | How long to hold the button for a long press (ms) |
| `SMOOTHING` | `0.15` | Low-pass filter strength on the displayed angle — `0.0` is raw, higher is smoother but slower to respond; keep below `0.5` |

Pin numbers and I2C addresses are also in `config.py` if you adapt the build to different hardware.

---

## Usage

1. Power on — battery percentage is shown for 1.5 s, then the live angle appears.
2. Hold the knife at your desired sharpening angle and **short-press** the button to enter calibration mode (`CAL` label shown).
3. Adjust the angle until it looks right, then **short-press** again to lock it in. The display returns to ready mode.
4. Sharpen — the display inverts when you drift more than 2° from your angle.
5. **Long-press** to power off. Press the button again to wake.
