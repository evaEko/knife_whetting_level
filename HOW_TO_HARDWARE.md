# Hardware Assembly

The KiCad schematic is in [`kicad/kicad.kicad_sch`](kicad/kicad.kicad_sch). Open it in KiCad 9 to view the full schematic and generate gerbers for PCB fabrication.

Wire up the components according to the pin assignments table above. The nice!nano sits on the PCB via its castellated pads or through-hole pins.

If you are using a ProMicro nRF52840 instead of the nice!nano, make sure the voltage divider resistors are in place on the BATIN/P0.04 line — without them battery measurement will not work.

If you have the PCB, solder in this order: display first, then the BNO085 module, then the MCU. Leave enough clearance under the MCU for the battery. Connect the battery wires to B+ and B- directly on the MCU board.

## Bill of Materials

| Component | Part | Notes |
|---|---|---|
| Microcontroller | **nice!nano v2** | nRF52840-based, chosen for built-in LiPo charging — no separate charging module needed |
| IMU | BNO085 | I2C, addr `0x4B` |
| Display | SSD1306 0.91" OLED | I2C, 128×32 px, addr `0x3C` |
| Two push buttons  | Tactile push button | SMD, e.g. CK KSC6xxG footprint |
| Battery | LiPo 3.7V 100mAh | Smallest single-cell LiPo that fits under the Pro Micro footprint (e.g. 20×30mm) |
| Resistor | **2× resistors for voltage divider** | Required to measure battery voltage via the BATIN/P0.04 pin. The nice!nano v2 has this divider built in on-board — no extra resistors needed if using nice!nano |

## Pin Assignments

| Signal | nice!nano pin | nRF52840 GPIO |
|---|---|---|
| IMU SDA | pin 106 | P1.06 |
| IMU SCL | pin 104 | P1.04 |
| OLED SDA | pin 006 | P0.06 |
| OLED SCK | pin 008 | P0.08 |
| Low button (calibration) | pin 111 | P1.11 |
| Top button (preset select) | pin 113 | P1.13 |

All I2C buses run at 400 kHz.