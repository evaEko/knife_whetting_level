# Angle Measurement: Stone Levelling, Target Setting, and Math

This document explains how the device measures blade inclination, how calibration works, and what the math behind it is.

---

## The Problem

The sensor is attached to the blade with a magnet. The magnet lets the sensor spin freely on the blade face — it can rotate like a dial stuck to the surface. When this happens, a naive single-axis reading (e.g. pitch, which measures only the X-component of gravity) changes even though the blade angle has not changed.

The goal is a reading that reports the true inclination of the surface the sensor rests on, regardless of how the sensor has spun on that surface.

---

## The IMU and Gravity

The BNO085 outputs a **game rotation vector** — a quaternion `q = (w, x, y, z)` that describes the sensor's current orientation relative to a reference frame. The reference frame is always aligned with gravity (the accelerometer and gyroscope fuse to track tilt accurately; only heading drifts since there is no magnetometer).

From this quaternion, the gravity unit vector in the sensor's **body frame** is derived analytically (`bno085.py: get_gravity`):

```
gx =  2(wy − xz)
gy = −2(yz + xw)
gz =  2(x² + y²) − 1
```

This vector `(gx, gy, gz)` points in the direction of gravity as seen from inside the sensor housing. It has magnitude 1. It is the foundation of all angle calculations.

> **Why not read the accelerometer directly?** The quaternion-derived gravity is already filtered and fused with the gyroscope, giving a stable, low-noise result. The raw accelerometer also captures vibration and movement, which would make the display jitter during sharpening strokes.

---

## Angle Calculation

The angle between the blade and the stone is computed by `pitch_calculator.py`:

```
dot   = clamp( dot(g, n_stone), −1, 1 )
raw   = arccos(dot) × 180/π
angle = 180 − raw   if raw > 90°
        raw          otherwise
```

where `g` is the current gravity unit vector and `n_stone` is the saved stone normal (see below).

### Why this gives inclination

`dot(g, n_stone)` is the cosine of the angle between the current gravity direction and the "blade-flat-on-stone" reference. When the blade is flat on the stone, `g` and `n_stone` are parallel, `dot = 1`, `arccos(1) = 0°`. When the blade is lifted by 15°, `dot = cos(15°)` and `arccos(cos(15°)) = 15°`.

### The fold-back

If the blade is tilted more than 90° (e.g. vertical or inverted), `arccos` would return a value between 90° and 180°. The firmware folds these back with `180 − raw` so the displayed angle is always in [0°, 90°] and physically means "degrees of lift from the stone surface."

### Why this is invariant to sensor spin

When the sensor spins on the blade face, it rotates around the blade's surface normal in world space. Because `n_stone` was captured with the blade on the stone, it aligns with that axis. Spinning around `n_stone` cannot change the projection of `g` onto `n_stone`:

```
dot( R(n_stone, θ) · g,  n_stone ) = dot( g, n_stone )   for any θ
```

So the reading is stable regardless of sensor spin. Compare this to pitch `= arcsin(gx)`, which only uses one component — spinning freely redistributes weight among gx, gy, gz and changes the reading.

This invariance is exact in theory, but during a fast physical spin the BNO085's quaternion can drift transiently before the sensor fusion settles. This causes momentary spikes in the raw reading even though the true angle hasn't changed. The smoothing filter handles this — see [Clock-spin transient handling](#clock-spin-transient-handling) below.

### Clamping

`dot` is clamped to [−1, 1] before passing to `arccos` to guard against floating-point rounding that would cause a domain error.

---

## Calibration: Stone Levelling

Before any angle can be shown, the device must know what "flat on the stone" looks like. This is the **stone calibration** step (`n_stone`).

**How it works** (`surface_level_handler.py: _capture`):

1. User lays the blade flat on the stone and confirms.
2. The firmware waits a configurable settle delay (default 5 s, from `capture_delay_sec` in `config.txt`).
3. It then collects 20 gravity samples 50 ms apart, averages them, and normalizes the result.
4. The normalized vector is saved as `n_stone` to persistent storage.

```
n_stone = normalize( mean(g_1, g_2, …, g_20) )
```

After this, `pitch(g, n_stone) = 0°` when the blade is flat on the stone by construction, because `dot(n_stone, n_stone) = 1` and `arccos(1) = 0°`.

---

## Target Angle

Once the stone normal is known, the user sets a **target angle** — the desired sharpening angle. There are two ways:

### Preset

Selecting a preset from the angle menu calls `set_target_angle(angle)` directly with a stored degree value. No vector is captured; `n_target` is left unset. The device simply knows "alert when `pitch` is within `deviation_threshold` of this number."

### Custom capture

Selecting "Custom" uses the same `SurfaceLevelHandler` capture process as stone levelling, but saves the result as `n_target`:

```
n_target = normalize( mean(g_1, …, g_20) )
target_angle = pitch(n_target, n_stone)
```

`target_angle` is computed once at save time and stored. During measurement, only `target_angle` is used — `n_target` is retained for reference but not recalculated each frame.

---

## Measurement and Smoothing

Each update cycle (`measure.py: update`):

1. Get the current gravity vector `g` from the IMU.
2. Compute `raw = pitch(g, n_stone)`.
3. Pass through the **smoothing filter**.
4. Expose as `pitch()`.

### Smoothing filter

The filter is an exponential moving average (EMA) with two different alpha values:

| Condition | Alpha | Effect |
|-----------|-------|--------|
| Spike (deviation ≥ 25°) | 0.995 | Heavily suppress — likely motion artifact |
| Moving (vel ≥ 0.1°/frame or deviation ≥ 1°) | 0.70 | Light smoothing — follow the blade |
| Still | 0.995 | Heavy smoothing — freeze the display |

```
pitch_new = α × pitch_old + (1 − α) × raw
```

**Spin detection** (`bno085.py: is_spinning`): the device is considered spinning when angular speed (from the calibrated gyroscope) exceeds 0.5 rad/s (≈ 29°/s).

### Clock-spin transient handling

The sensor is magnetically attached and can be accidentally spun like a clock hand while the blade angle stays constant. Mathematically the reading should be unchanged (see spin invariance above), but in practice the BNO085's quaternion drifts during a fast rotation before sensor fusion re-settles — producing a transient spike in `raw`.

The filter handles this in two stages (`measure.py: _smooth`, `_snap_if_stopped`):

**Stage 1 — freeze during spin:**
When `raw` deviates from the current filtered pitch by ≥ 25° (`_SPIKE_THRESHOLD`), alpha jumps to 0.995. The filtered value barely moves, so the display stays frozen rather than following the spurious spike. The gyroscope being active during the spin keeps `is_spinning()` True, but the spike threshold alone is sufficient to trigger the freeze even if gyro lags slightly.

**Stage 2 — snap after spin:**
When the sensor comes to rest (`is_spinning()` returns False, i.e. angular speed drops below 0.5 rad/s) and the filter is still far from `raw` (≥ 25°), the filter snaps immediately to `raw` instead of slowly converging:

```python
if not is_spinning() and abs(raw - pitch) >= 25°:
    pitch = raw   # snap
```

After a clock spin, the math guarantees `raw` has returned to the pre-spin value (within sensor noise). Snapping to it recovers the correct reading instantly rather than over many EMA cycles.

---

## In-Position Detection

```python
in_position = abs(pitch() − target_angle) <= deviation_threshold
```

`deviation_threshold` is a user-configurable tolerance (0–4°, default adjustable in settings). When `in_position` is True, the display inverts as a visual alert.

---

## No Stone Calibration

If `n_stone` has never been saved, `measure.update()` returns `False` and the display shows "No calibration" with a prompt to run stone levelling. There is no fallback angle calculation.

---

## Session Flow

1. **Stone levelling** (once per sensor placement) — capture `n_stone` with blade flat on stone.
2. **Target selection** — pick a preset angle, or capture a custom `n_target` with blade at the desired sharpening angle.
3. **Measuring** — `pitch(g, n_stone)` updates each cycle. Display inverts when within `deviation_threshold` of `target_angle`.

Changing the target mid-session does not affect stone calibration. Stone calibration persists across power cycles (stored in `data.txt`).

---

## Summary

| Step | What is saved | How |
|------|--------------|-----|
| Stone levelling | `n_stone = normalize(mean(g × 20))` | 20-sample average, normalized |
| Preset target | `target_angle` (degrees) | Set directly from preset list |
| Custom target | `n_target`, `target_angle = pitch(n_target, n_stone)` | Same capture process as stone levelling |
| Measurement | — | `pitch(g, n_stone)` → EMA filter → display |
| In-position | — | `\|pitch − target_angle\| ≤ deviation_threshold` |
