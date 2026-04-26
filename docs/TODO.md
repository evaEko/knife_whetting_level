# TODO

* tag v2.0 commit
* implement angle format select: on top button long press display the option for the angle format as we display the preset angles, user confirms selection with the top button and lists with the upper button
* store the angle display setting in eeprom as we store board level

# Prepare for public:

* [x] nice-nano-kicad library — checked: bundled files declare GNU GPLv3 in kicad/nice-nano-kicad/README.md; attribution and license note are included in README.
* [x] The drivers — bno085.py: only imports stdlib (struct, time, math). No third-party dependencies; no attribution required.

## Firmware

- [ ] add return to presets menu 

## GitHub

- [ ] Merge v2.0 into main
- [ ] Set v2.0 (or main) as default branch in GitHub Settings → General → Default branch
- [ ] Verify GitHub Actions workflow appears in Actions tab and run it manually
- [ ] Update QUICK_START.md to link to the firmware artifact download

## PCB


- [ ] Tidy up

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
