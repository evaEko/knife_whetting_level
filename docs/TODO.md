# TODO

* implement correct detection of battery connected when on usb cable
* when ble is on, there is a small star in the upper right corner in measurement 


## GitHub


## PCB

- [ ] Tidy up

## Long-term: Android App + Bluetooth

The nRF52840 has built-in BLE. The plan is to expose a BLE GATT service from the firmware and build an Android companion app.

### Firmware (BLE)

- [ ] Expose a GATT characteristic to receive a target angle from the app
- [ ] Expose a GATT characteristic to stream the current live angle back to the app
- [ ] Merge BLE-received angle with the existing preset/calibration logic

### Android App

- [ ] BLE scan and connect to the device
- [ ] UI to set a target angle and push it to the device
- [ ] Live angle display mirrored from the device
- [ ] Manage and push preset angle profiles to the device
