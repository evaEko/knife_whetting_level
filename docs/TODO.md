# TODO


# Prepare for public:

* MicroPython UF2 in the repo — the firmware binary from jkorte-dev's repo is included in assets/. MicroPython itself is MIT licensed, but you should check that specific build's repo for its license before redistributing the binary. If it's MIT, you're fine — just add attribution.

CC BY-NC 4.0 for software — Creative Commons explicitly recommends against using CC licenses for software code. It works for hardware designs and documentation, but for the Python code, a standard software license (MIT, GPL) would be more appropriate and legally cleaner. You could keep CC BY-NC for the KiCad files and docs, and add MIT or GPL for the src/ code.

nice-nano-kicad library — the files in kicad/nice-nano-kicad/ were from a third-party repo. Worth checking if that had a license that requires attribution.

The drivers — bno085.py check imported modules.

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
