# src_ref — Feature TODO

Feature parity checklist against `src/`. Items the user confirmed are missing
are marked ★.

---

## ★ BLE Protocol

`src_ref/services/ble.py` is a bare wrapper (toggle / enabled / connected).
`src/domain/ble_commands.py` implements the full protocol:

- [ ] Command parser (receive + dispatch on command name)
- [ ] `live_start` / `live_stop` — stream angle over BLE
- [ ] `get_calibration` / `calibrate` — read and trigger calibration
- [ ] `get_presets` / `add_preset` / `clear_presets` — preset sync
- [ ] `set_target_angle` / `set_custom_angle` — set target from app
- [ ] `get_target_state` — report in-position status
- [ ] `get_settings` / `set_setting` — sync settings (deviation threshold,
  angle format, smoothing, show flags)
- [ ] `app_disconnect` / `reinit` / `reboot` — lifecycle commands
- [ ] Continuous BLE updates: angle at 40 ms, target state at 1 s

---

## ★ Stored Angles (Preset System)

`src/` has `PresetStore` backed by `angles.csv`.

- [ ] `PresetStore` service: load / save / find by name
- [ ] `angles.csv` with default presets
- [ ] Preset selection state (replaces or extends current target capture)
- [ ] Custom angle entry (5-second countdown capture, same as src)
- [ ] Preset sync over BLE (add / clear / replace)

---

## ★ Angle Format Setting

`src/states/select_format.py` offers three formats:

- [ ] `2d` — two decimals: `12.34°`
- [ ] `1d` — one decimal: `12.3°`
- [ ] `1d_half` — rounded to 0.5°: `12.5°`
- [ ] Persist format to config; apply in `show_angle()`
- [ ] Add format selector to settings menu
- [ ] Reboot on change (same as src)

---

## Measurement Improvements

### On-Stone Detection *(needs improvement)*
Basic implementation in place: pitch-based threshold (12°) with 800 ms debounce
on return. Known limitations:
- Threshold is a fixed degree value, not tied to actual blade/stone geometry
- Does not distinguish "blade lifted" from "blade at wrong angle on stone"
- Needs real-world tuning across different sharpening angles and users

---

## Boot Sequence

`src/states/boot.py` has a multi-phase splash + hardware init.

- [ ] Splash screen (1 s)
- [ ] Battery percentage display during init (fall back gracefully if unavailable)
- [ ] Hardware init phase: sensor, presets, BLE, settings
- [ ] Transition to calibration or measure based on stored state

---

## Battery

- [ ] `drivers/battery.py` — read ADC pin → percentage
- [ ] Show battery level during boot splash

---

## Idle Power Management

`src/drivers/sensor.py` reduces IMU report interval after 60 s of inactivity.

- [ ] Track last significant movement timestamp
- [ ] After 60 s with < 0.5° change: switch IMU to 1 000 ms report interval
- [ ] Resume 10 ms interval on next movement

---

## Deviation Threshold Controls

`src_ref/states/settings/deviation_state.py` exists but differs from src:

- [ ] Align range: src uses 0.0–4.0° in 0.1° steps; src_ref uses 0.5–10.0° in 0.5° steps
- [ ] Decide and align on one range / step size

---

## Display

`src_ref/services/display.py` has only 4 methods. Missing rendering for:

- [ ] Preset confirmation screen
- [ ] Custom angle capture countdown
- [ ] Battery level during boot
- [ ] Format selection screen

---

## Tests *(from plan — desktop, no hardware)*

- [ ] `test_calibrate_state.py`
- [ ] `test_deviation_state.py`
- [ ] `test_storage_service.py`
- [ ] `test_config_service.py`
- [ ] `test_bno085_parse.py` — parse_reports returns correct accel/gyro tuples
