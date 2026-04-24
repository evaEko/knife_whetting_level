# Knife Level

Licensed under [CC BY-NC 4.0](LICENSE) — free to use and modify, not for commercial use.

## Getting Started

1. [Assemble the hardware](HOW_TO_HARDWARE.md)
2. [Flash the firmware](HOW_TO_FIRMWARE.md)

### Why nice!nano?

The nice!nano v2 integrates a LiPo charger. You can charge the battery over USB without any additional charging module or circuit. Battery percentage is read via the nRF52840's internal VDDHDIV5 channel — no external resistors needed.

## Features (v1.0)

- Displays current pitch angle
- **Calibration**: set your target sharpening angle with a single button press
- **Visual alert**: display inverts when you drift more than 2° from the calibrated angle, or when you reach the mirror angle on the other side of the blade
- **Idle mode**: IMU report rate drops automatically after 60 s of no movement to save power
- **Battery display**: shows battery percentage on startup
- **Power off**: long-press the button from any state; press again to wake

## Features (v2.0)

- **Preset angle profiles** — define named knives and their angles in `angles.csv`; select them on the device without manual calibration
- **Two-button interface** — low button for calibration, top button to cycle and select presets
- **Flash mode** — long-press the top button to drop to REPL for flashing without unplugging
- **Physical power switch** — B+ latch switch replaces soft power off
