## ★ Angle Format Setting

## Measurement Improvements

### On-Stone Detection *(needs improvement)*
Basic implementation in place: pitch-based threshold (12°) with 800 ms debounce
on return. Known limitations:
- Threshold is a fixed degree value, not tied to actual blade/stone geometry
- Does not distinguish "blade lifted" from "blade at wrong angle on stone"
- Needs real-world tuning across different sharpening angles and users

---

## Boot Sequence

- [ ] Battery percentage display during init (fall back gracefully if unavailable)

## Battery

- [ ] `drivers/battery.py` — read ADC pin → percentage

## Tests *(from plan — desktop, no hardware)*

- [ ] `test_calibrate_state.py`
- [ ] `test_deviation_state.py`
- [ ] `test_storage_service.py`
- [ ] `test_config_service.py`
- [ ] `test_bno085_parse.py` — parse_reports returns correct accel/gyro tuples
