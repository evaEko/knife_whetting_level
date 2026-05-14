# TODO

# Case

work in progress

# Firmware

* implement correct detection of battery connected when on usb cable
* refactor ble protocol and related
* fix battery status reading

# Known Issues

- Battery readings can be erratic.
- Occasionally, the Android app cannot detect the level; if this happens, turn the level device off and on again, enable bluetooth and in your Android app rescan.

## GitHub

## PCB

- tidy up: currently multiple versions: the default one, one with sensor on the side, one with sensor on the size and with a larger display (driver needed), 

## Angle Format Setting

## Measurement Improvements

### On-Stone Detection *(needs improvement)*
Basic implementation in place: pitch-based threshold (12°) with 800 ms debounce
on return. Known limitations:
- Threshold is a fixed degree value, not tied to actual blade/stone geometry
- Does not distinguish "blade lifted" from "blade at wrong angle on stone"
- Needs real-world tuning across different sharpening angles and users

## Tests *(from plan — desktop, no hardware)*

- [ ] `test_calibrate_state.py`
- [ ] `test_deviation_state.py`
- [ ] `test_storage_service.py`
- [ ] `test_config_service.py`
- [ ] `test_bno085_parse.py` — parse_reports returns correct accel/gyro tuples
