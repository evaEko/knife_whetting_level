# Knife Level

A small wearable device for knife sharpening. Measures blade pitch in real time using a 9-DOF IMU, displays the angle on an OLED, and alerts you when you drift from your target sharpening angle. Built on MicroPython running on an nRF52840 microcontroller with two buttons, a LiPo battery, and a custom PCB small enough to strap to your wrist or clamp to a whetstone stand.

![Device on breadboard](docs/images/knife_whetting_level.jpg)

Licensed under [CC BY-NC 4.0](LICENSE) — free to use and modify, not for commercial use.

> **Disclaimer:** This project is provided as-is, without warranty of any kind. The author is not liable for any damage, injury, or loss arising from the use, misuse, or inability to use this project or any hardware built from it.

## Getting Started

1. [Assemble the hardware](docs/HOW_TO_HARDWARE.md)
2. [Flash the firmware](docs/HOW_TO_FIRMWARE.md)

If impatient, go over [Quick Start](docs/QUICK_START.md).

## Features (v1.0)

- Displays current pitch angle
- **Calibration**: set your target sharpening angle with a single button press
- **Visual alert**: display inverts when you drift more than 2° from the calibrated angle, or when you reach the mirror angle on the other side of the blade
- **Idle mode**: IMU report rate drops automatically after 60 s of no movement to save power
- **Battery display**: shows battery percentage on startup
- **Power off**: long-press the button from any state; press again to wake

## Features (v2.0)

- **Preset angle profiles** — define named knives and their angles in `angles.csv`; select them on the device with the top button
- **Calibration + presets are independent** — calibrate once to set your physical reference point (zero), then switch between knife presets freely; each preset angle is always displayed relative to the calibration, never compounding
- **Two-button interface** — low button for calibration, top button to cycle and select presets
- **Flash mode** — long-press the top button to drop to REPL for flashing without unplugging
- **Physical power switch** — B+ latch switch replaces soft power off
- **Board levelling** — correct for sensor mounting angle once; stored in flash, applied automatically on every boot

