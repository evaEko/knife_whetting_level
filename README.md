# Knife Level

A small digital level for knife sharpening. Measures blade pitch in real time using a 9-DOF IMU, displays the angle on an OLED, and alerts you when you drift from your target sharpening angle.

 Built on MicroPython running on an nRF52840 microcontroller with two buttons, a LiPo battery, and a custom PCB. 


<img src="docs/images/knife_whetting_level.jpg" width="300"/>

Commercial use and resale are not permitted.

## License

- Software code, documentation, images, and hardware design files: [CC BY-NC 4.0](LICENSE)
- Third-party subcomponents may use their own license where noted (for example, `kicad/nice-nano-kicad/`)

### Third-party notices

- `kicad/nice-nano-kicad/` is a third-party nice!nano symbol/footprint library bundled with this project.
- The bundled library declares `GNU GPLv3` in `kicad/nice-nano-kicad/README.md`; keep that notice and attribution when redistributing those files.

> **Disclaimer:** This project is provided as-is, without warranty of any kind. The author is not liable for any damage, injury, or loss arising from the use, misuse, or inability to use this project or any hardware built from it.

## Getting Started

1. [Assemble the hardware](docs/HOW_TO_HARDWARE.md)
2. [Flash the firmware](docs/HOW_TO_FIRMWARE.md)

If impatient, go over [Quick Start](docs/QUICK_START.md).

## Acknowledgements

Thanks to [jkorte-dev](https://github.com/jkorte-dev) for publishing the nRF52840 SuperMini/Nice!Nano MicroPython board definitions and UF2 builds used as a flashing base.

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
- **Flash mode** — short-press both buttons simultaneously to drop to REPL for flashing without unplugging (to exit flash mode, reset via RST↔GND or power-cycle the device)
- **Physical power switch** — B+ latch switch replaces soft power off
- **Board levelling** — correct for sensor mounting angle once; stored in flash, applied automatically on every boot

