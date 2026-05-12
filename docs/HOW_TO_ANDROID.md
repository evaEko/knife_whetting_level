# HOW TO: Blunt Android App

## What is the Blunt Android App?
The Blunt Android app is a companion application for the Knife Level device. It allows you to connect to your level via Bluetooth, view measurements, set target angles, and customize alerts. The app is not required for using the Knife Level — it is provided purely for convenience and enhanced user experience.

### Settings available from the app

**Displayed Data**
- Show/hide preset name on the measuring screen
- Show/hide target angle on the measuring screen
- Restore last selected preset angle on boot

**Measurement**
- **Format** — angle display format: `2d` (two decimals), `1d` (one decimal), `1d_half` (nearest 0.5°)
- **Smoothing** — low-pass filter strength (0.3 = reactive, 0.9 = smooth)
- **Deviation Threshold** — how far from the target angle before the display inverts; supports decimal values (0.5°–5.0° in 0.5° steps)

**Sound Alert**
- **On angle too high** — plays a tone or custom audio file when the blade angle is above the target threshold; tone pitch is configurable
- **On angle too low** — plays a tone or custom audio file when the blade angle is below the target threshold; tone pitch is configurable
- **On target** — plays a custom audio file (looped) when the blade is within the target threshold; resumes from where it was interrupted rather than restarting; optional **Continue on lifted** sub-toggle keeps the audio playing when the blade is lifted off the stone

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
