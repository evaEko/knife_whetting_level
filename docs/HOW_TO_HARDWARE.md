# Hardware Assembly

The KiCad schematic is in [`kicad/kicad.kicad_sch`](../kicad/kicad.kicad_sch). Open it in KiCad 9 to view the full schematic and generate gerbers for PCB fabrication. Have it fabricated. It is possible to do this on perfboard: it is a good idea to breadboard it first and plan the perfboard version, use both sides (TODO: documentation of perfboard options).

Wire up the components according to the schematic. The nice!nano or SuperMini sits on the PCB via its castellated pads or through-hole pins.

Battery voltage measurement does not require any external resistors — the firmware reads the nRF52840's internal VDDHDIV5 SAADC channel directly. This works on all supported boards without modification.

If you have the PCB, solder in this order: display first, then the BNO085 module, then the MCU. Leave enough clearance under the MCU for the battery. Connect the battery wires to B+ and B- directly on the MCU board.

Consider socketing the MCU using mill-max or machined pin headers instead of soldering it directly. This lets you swap or replace the board without desoldering, and makes it easier to recover if something goes wrong during flashing.

After assembly, the easiest bring-up path is:

1. flash the UF2 MicroPython base firmware
2. flash the project firmware from this repo or from the workflow artifact bundle
3. level the board once from the on-device settings menu
4. optionally install the Android companion app from the workflow APK artifact for BLE setup, calibration, and preset management

Refer to the images on [breadboarding](images/breadboard/)
and on [PCB assembly](images/pcb_assembly/)

## Bill of Materials

| Component | Part | Notes |
|---|---|---|
| Microcontroller | **nice!nano** or SuperMini nRF52840 | nRF52840-based, chosen for built-in LiPo charging — no separate charging module needed |
| IMU | BNO085 | I2C, addr `0x4B` |
| Display | SSD1306 0.91" OLED | I2C, 128×32 px, addr `0x3C` |
| Two push buttons  | Tactile push button | SMD, e.g. CK KSC6xxG footprint |
| Battery | LiPo 3.7V 100mAh | Smallest single-cell LiPo that fits under the Pro Micro footprint (e.g. 20×30mm) |
| PCB| Custom PCB (see kicad folder) | The PCB makes everything simpler, however, you can perfboard it: you will need to use both sides: plan ahead. |

## Note on MCU Board

The following boards have been tested and confirmed working:

- **nice!nano v1.0** — works
- **nice!nano v2.0** — works (recommended; has the most reliable charging circuit)
- **SuperMini nRF52840** — works; cheaper alternative, pin-compatible with nice!nano

All three use the nRF52840 and support the same MicroPython firmware. Choose any of them — the firmware runs identically on all.

**Battery status**: The firmware reads battery percentage via the nRF52840's internal VDDHDIV5 SAADC channel. This is purely internal to the chip and requires no external components. The P0.04/BATIN pin and any external voltage divider are not used. On the SuperMini, this divider is not populated at the factory anyway — it does not matter.

**Companion app support**: BLE-based Android app features depend on the MCU being flashed with a firmware build where `BLE_ENABLED` is set to `True` in [`src/config.py`](../src/config.py).

