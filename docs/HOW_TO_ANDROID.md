# HOW TO: Blunt Android App

## What is the Blunt Android App?
The Blunt Android app is a companion application for the Knife Level device. It allows you to connect to your level via Bluetooth, view measurements, set target angles, and customize alerts. The app is not required for using the Knife Level — it is provided purely for convenience and enhanced user experience.

### Settings available from the app

The settings screen has two tabs: **Application** (stored on the phone) and **Level** (sent to the device over BLE).

#### Application tab

**Lifted**
- **Enable** — detect when the blade leaves the stone and pause deviation alerts
- **Velocity threshold (°/s)** — minimum angular speed that triggers a lift event (3–30°/s); lower = more sensitive
- **Debounce (ms)** — how long to wait after the last movement before returning to on-stone state (200–4000 ms); higher = fewer false detections when holding the blade in the air

**Measurement Data**
- **Angle Format** — `2d` (two decimals), `1d` (one decimal), `0.5` (nearest 0.5°)
- **Target Name** — show the preset name (e.g. Gyuto) above the live angle
- **Target Angle** — show the target angle value below the live reading
- **Deviation Range** — show the allowed angle range (e.g. 13.0°–17.0°) based on target and threshold
- **Delta** — show the signed difference between the live angle and the target (e.g. Δ+1.2°)

**Visual Alert**
- **Direction Arrows** — show ↑↓ arrows indicating which way to correct the blade; the active arrow turns the alert colour when outside the threshold
- **Arrow Size** — Small / Medium / Large / XL (shown when Direction Arrows is on)
- **Background Color** — change the background colour when outside the deviation threshold
- **Angle too high / too low colour** — pick from Red, Orange, Pink, Teal, Blue (shown when Background Color is on)

**Sound Alert**
- **On angle too high** — play a tone when the blade is above target + threshold; tone pitch and optional custom audio file are configurable
- **On angle too low** — play a tone when the blade is below target − threshold; tone pitch and optional custom audio file are configurable
- **On target** — play a custom audio file (looped) when the blade is within the target range; resumes from where it was interrupted
  - **Continue on lifted** — keep the on-target audio playing when the blade is lifted off the stone

**Custom Angle**
- **Measurement delay (s)** — countdown before the live angle is captured as a custom target (1–15 s); gives time to position the blade

#### Level tab

These settings are written to the device over BLE. Press **Apply** to send.

- **Deviation Threshold (°)** — how far from the target angle before the display inverts (0.0°–4.0°)
- **Capture delay (s)** — settle time before the surface normal is sampled during calibration (1–30 s)

## Installation
You have two options to install the app on your Android phone:

### Option 1: Download APK from Workflow
1. Go to the GitHub repository's Actions tab.
2. Find the latest successful build workflow run.
3. Download the APK artifact to your phone or computer.
4. Transfer the APK to your phone if needed.
5. On your phone, open the APK file and follow the prompts to install. You may need to allow installation from unknown sources.

### Option 2: Build and Install Yourself
1. Install Android Studio (https://developer.android.com/studio) and required SDKs.
2. Clone the repository to your computer.
3. Open the `App` project in Android Studio.
4. Connect your Android phone via USB and enable USB debugging.
5. Click "Run" in Android Studio to build and install the app directly to your device.

## Uploading and Running the App
- After installation, locate the Blunt app icon on your phone and open it.
- Grant all requested permissions (Bluetooth, Location) for proper operation.
- The app will scan for your Knife Level device. Select it to connect.

## Troubleshooting
- **I cannot see my level during scanning:**
  - Make sure BLE is enabled on your Knife Level device.
  - Check if the device appears in your phone's Bluetooth device list. If not, turn the level off and on again.
- **I can't see details about my target angle:**
  - Ensure you have selected a preset or set a custom angle in the app.
- **I don't want some of the alerts:**
  - Go to the app's settings and customize or disable alerts as desired.
