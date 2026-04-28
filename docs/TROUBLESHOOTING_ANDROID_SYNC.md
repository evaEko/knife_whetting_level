# Android Sync: Missing init script in /tmp

## Symptom

Android Studio sync fails with errors like:

- `The specified initialization script '/tmp/sync.studio.tooling.gradle' does not exist.`
- `The specified initialization script '/tmp/sync.studio.tooling1.gradle' does not exist.`

You may also see many false editor errors (for example minSdk reported as 1), while terminal builds still succeed.

## Root cause

This is usually a desync between Android Studio tooling and stale Gradle Daemon processes.

Android Studio sync uses temporary init scripts under `/tmp` and passes them to Gradle. If stale daemons keep old state, they can keep looking for temp files that no longer exist.

## Why terminal builds can still work

Running `./gradlew` from terminal does not use Android Studio sync tooling scripts, so normal builds can pass even when IDE sync fails.

## Recovery steps

1. Stop old daemons:

```bash
./gradlew --stop
```

2. If sync still fails, force a fresh process for sync by disabling daemon temporarily in `App/gradle.properties`:

```properties
org.gradle.daemon=false
```

3. Run sync again in Android Studio.

4. After sync is stable, optionally remove that line to re-enable daemon for faster builds.

## Notes

- If the issue returns, first try `./gradlew --stop` before deeper cleanup.
- This is an IDE/tooling state issue, not usually an app code issue.
