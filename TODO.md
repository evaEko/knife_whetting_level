# TODO

## PCB

- [ ] Add physical switch in series with B+ for hard power cut
- [ ] Fix pad wiring to B-

## Firmware

- [ ] Add second button (hardware + pin config)
- [ ] Add preset angles to config (list of named angles, e.g. Japanese 15°, European 20°)
- [ ] Second button long press: cycle through preset angles one by one
- [ ] Second button long press on highlighted preset: select it as the target angle

## Long-term: Android App + Bluetooth

The nRF52840 has built-in BLE. The plan is to expose a BLE GATT service from the firmware and build an Android companion app.

### Firmware (BLE)

- [ ] Enable BLE on the nRF52840 via MicroPython
- [ ] Expose a GATT characteristic to receive a target angle from the app
- [ ] Expose a GATT characteristic to stream the current live angle back to the app
- [ ] Merge BLE-received angle with the existing preset/calibration logic

### Android App

- [ ] BLE scan and connect to the device
- [ ] UI to set a target angle and push it to the device
- [ ] Live angle display mirrored from the device
- [ ] Manage and push preset angle profiles to the device
