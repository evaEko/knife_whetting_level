# Hardware Assembly

The KiCad schematic is in [`kicad/kicad.kicad_sch`](kicad/kicad.kicad_sch). Open it in KiCad 9 to view the full schematic and generate gerbers for PCB fabrication. Have it fabricated. It is possible to do this on perfboard: it is a good idea to breadboard it first and plan the perfboard version, use both sides (TODO: documentation of perfboard options).

Wire up the components according to the pin assignments table above. The nice!nano sits on the PCB via its castellated pads or through-hole pins.

If you are using a ProMicro nRF52840 instead of the nice!nano, make sure the voltage divider resistors are in place on the BATIN/P0.04 line — without them battery measurement will not work (the rest will be fine).

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
| PCB| Custom PCB (see kicad folder) | The PCB makes everything simpler, however, you can perfboard it: you will need to use both sides: plan ahead. |
