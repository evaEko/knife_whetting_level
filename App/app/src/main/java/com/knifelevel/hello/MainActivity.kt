package com.knifelevel.hello

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.content.Context
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.knifelevel.hello.ui.theme.MyApplicationTheme
import kotlinx.coroutines.delay
import org.json.JSONObject
import java.util.UUID

val NUS_SERVICE_UUID = UUID.fromString("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
val NUS_TX_UUID      = UUID.fromString("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
val NUS_RX_UUID      = UUID.fromString("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
val CCCD_UUID        = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")

val mainHandler      = Handler(Looper.getMainLooper())
const val LIVE_RETRY_MS = 1_000L
const val LIVE_STALE_MS = 1_500L
var activeGatt: BluetoothGatt? = null
var awaitingLiveAngle = false

// Commands are queued so we never have two concurrent GATT writes
val commandQueue     = ArrayDeque<String>()
var isSendingCommand = false
var onQueueDrained: (() -> Unit)? = null
var onDisconnected: (() -> Unit)? = null
var onUnexpectedGattDisconnect: (() -> Unit)? = null

val liveStartRetry = object : Runnable {
    override fun run() {
        if (!awaitingLiveAngle || activeGatt == null) return
        if (!commandQueue.contains("live_start")) {
            enqueueCommand("live_start")
        }
        mainHandler.postDelayed(this, LIVE_RETRY_MS)
    }
}

fun startLiveAngleRetry(gatt: BluetoothGatt) {
    activeGatt = gatt
    awaitingLiveAngle = true
    mainHandler.removeCallbacks(liveStartRetry)
    if (!commandQueue.contains("live_start")) {
        enqueueCommand("live_start")
    }
    mainHandler.postDelayed(liveStartRetry, LIVE_RETRY_MS)
}

fun stopLiveAngleRetry() {
    awaitingLiveAngle = false
    mainHandler.removeCallbacks(liveStartRetry)
}

fun resetBleSession() {
    commandQueue.clear()
    isSendingCommand = false
    onQueueDrained = null
    activeGatt = null
    stopLiveAngleRetry()
}

enum class Screen { CONNECT, LIVE, APP_SETTINGS, SETTINGS, CALIBRATE, PRESETS }

data class PresetEntry(val name: String, val angle: String)

enum class AppAngleFormat(val wireValue: String) {
    TWO_DECIMALS("2d"),
    ONE_DECIMAL("1d"),
    HALF_DEGREE("0.5");

    companion object {
        fun fromWire(value: String?): AppAngleFormat {
            return entries.firstOrNull { it.wireValue == value } ?: TWO_DECIMALS
        }
    }
}

data class AppUiSettings(
    val angleFormat: AppAngleFormat,
    val deviationBackgroundEnabled: Boolean,
    val displayArrow: Boolean,
    val soundAlert: Boolean,
    val highToneFreq: Float,
    val lowToneFreq: Float,
    val showTargetName: Boolean,
    val showTargetAngle: Boolean,
    val showDelta: Boolean,
)

fun loadAppUiSettings(context: Context): AppUiSettings {
    val prefs = context.getSharedPreferences("knife_level_app", Context.MODE_PRIVATE)
    return AppUiSettings(
        angleFormat = AppAngleFormat.fromWire(prefs.getString("angle_format", AppAngleFormat.TWO_DECIMALS.wireValue)),
        deviationBackgroundEnabled = prefs.getBoolean("deviation_background_enabled", true),
        displayArrow = prefs.getBoolean("display_arrow", true),
        soundAlert = prefs.getBoolean("sound_alert", true),
        highToneFreq = prefs.getFloat("high_tone_freq", defaultHighToneFreq()),
        lowToneFreq = prefs.getFloat("low_tone_freq", defaultLowToneFreq()),
        showTargetName = prefs.getBoolean("show_target_name", true),
        showTargetAngle = prefs.getBoolean("show_target_angle", true),
        showDelta = prefs.getBoolean("show_delta", true),
    )
}

fun saveAppUiSettings(context: Context, settings: AppUiSettings) {
    val prefs = context.getSharedPreferences("knife_level_app", Context.MODE_PRIVATE)
    prefs.edit()
        .putString("angle_format", settings.angleFormat.wireValue)
        .putBoolean("deviation_background_enabled", settings.deviationBackgroundEnabled)
        .putBoolean("display_arrow", settings.displayArrow)
        .putBoolean("sound_alert", settings.soundAlert)
        .putFloat("high_tone_freq", settings.highToneFreq)
        .putFloat("low_tone_freq", settings.lowToneFreq)
        .putBoolean("show_target_name", settings.showTargetName)
        .putBoolean("show_target_angle", settings.showTargetAngle)
        .putBoolean("show_delta", settings.showDelta)
        .apply()
}

fun formatAngleForDisplay(raw: String, format: AppAngleFormat): String {
    val value = raw.toFloatOrNull() ?: return raw
    return when (format) {
        AppAngleFormat.TWO_DECIMALS -> "%.2f".format(value)
        AppAngleFormat.ONE_DECIMAL -> "%.1f".format(value)
        AppAngleFormat.HALF_DEGREE -> {
            val rounded = kotlin.math.round(value * 2f) / 2f
            "%.1f".format(rounded)
        }
    }
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MyApplicationTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    MainScreen(context = this)
                }
            }
        }
    }
}

@Composable
fun MainScreen(context: Context) {
    val initialAppUi = remember { loadAppUiSettings(context) }
    var screen           by remember { mutableStateOf(Screen.CONNECT) }
    var angle            by remember { mutableStateOf("--") }
    var calibrationAngle by remember { mutableStateOf("--") }
    var currentTargetAngle by remember { mutableStateOf("") }
    var currentTargetName by remember { mutableStateOf("") }
    var lastAngleAt by remember { mutableStateOf(0L) }
    var measurementStale by remember { mutableStateOf(true) }
    var appAngleFormat by remember { mutableStateOf(initialAppUi.angleFormat) }
    var appDeviationBackgroundEnabled by remember { mutableStateOf(initialAppUi.deviationBackgroundEnabled) }
    var appDisplayArrow by remember { mutableStateOf(initialAppUi.displayArrow) }
    var appSoundAlert by remember { mutableStateOf(initialAppUi.soundAlert) }
    var appHighToneFreq by remember { mutableStateOf(initialAppUi.highToneFreq) }
    var appLowToneFreq by remember { mutableStateOf(initialAppUi.lowToneFreq) }
    var appShowTargetName by remember { mutableStateOf(initialAppUi.showTargetName) }
    var appShowTargetAngle by remember { mutableStateOf(initialAppUi.showTargetAngle) }
    var appShowDelta by remember { mutableStateOf(initialAppUi.showDelta) }
    var status           by remember { mutableStateOf("") }
    var permissionsGranted by remember { mutableStateOf(false) }
    var saveStatus       by remember { mutableStateOf("") }
    var presetStatus     by remember { mutableStateOf("") }
    var waitingForReconnect by remember { mutableStateOf(false) }
    val settings         = remember { mutableStateMapOf<String, String>() }
    val presets          = remember { mutableStateListOf<PresetEntry>() }
    var settingsLoaded   by remember { mutableStateOf(false) }
    var presetsLoaded    by remember { mutableStateOf(false) }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        permissionsGranted = permissions.values.all { it }
        if (!permissionsGranted) status = "Permissions denied"
    }

    LaunchedEffect(Unit) {
        permissionLauncher.launch(arrayOf(
            Manifest.permission.BLUETOOTH_SCAN,
            Manifest.permission.BLUETOOTH_CONNECT,
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION
        ))
    }

    LaunchedEffect(screen, waitingForReconnect, currentTargetAngle) {
        if (screen == Screen.CONNECT || waitingForReconnect || currentTargetAngle.isNotBlank()) return@LaunchedEffect
        while (activeGatt != null && currentTargetAngle.isBlank()) {
            sendCommand("get_target_state")
            delay(1_000)
        }
    }

    DisposableEffect(Unit) {
        onUnexpectedGattDisconnect = {
            waitingForReconnect = false
            angle = "--"
            currentTargetAngle = ""
            currentTargetName = ""
            lastAngleAt = 0L
            measurementStale = true
            status = "Disconnected"
            screen = Screen.CONNECT
        }
        onDispose {
            onUnexpectedGattDisconnect = null
        }
    }

    LaunchedEffect(screen, waitingForReconnect) {
        while (screen == Screen.LIVE && !waitingForReconnect) {
            delay(500)
            val gatt = activeGatt
            if (gatt == null) {
                measurementStale = true
                continue
            }
            val isStale = lastAngleAt == 0L ||
                SystemClock.elapsedRealtime() - lastAngleAt > LIVE_STALE_MS
            measurementStale = isStale
            if (isStale && !awaitingLiveAngle) {
                startLiveAngleRetry(gatt)
            }
        }
    }

    fun onMessage(msg: String) {
        when {
            msg.startsWith("angle:")   -> {
                angle = msg.removePrefix("angle:")
                lastAngleAt = SystemClock.elapsedRealtime()
                measurementStale = false
                stopLiveAngleRetry()
            }
            msg.startsWith("calibration:") -> calibrationAngle = msg.removePrefix("calibration:")
            msg.startsWith("preset:") -> {
                val rest = msg.removePrefix("preset:")
                val idx = rest.lastIndexOf(':')
                if (idx > 0) {
                    val name = rest.substring(0, idx)
                    val value = rest.substring(idx + 1)
                    val existing = presets.indexOfFirst { it.name == name }
                    if (existing >= 0) {
                        presets[existing] = PresetEntry(name, value)
                    } else {
                        presets.add(PresetEntry(name, value))
                    }
                }
            }
            msg.startsWith("setting:") -> {
                val rest = msg.removePrefix("setting:")
                val idx  = rest.indexOf(':')
                if (idx > 0) settings[rest.substring(0, idx)] = rest.substring(idx + 1)
            }
            msg == "ok:calibrated"     -> saveStatus = "Calibration saved."
            msg.startsWith("target_state:") -> {
                val rest = msg.removePrefix("target_state:")
                val idx = rest.indexOf(':')
                if (idx >= 0) {
                    currentTargetAngle = rest.substring(0, idx)
                    currentTargetName = rest.substring(idx + 1)
                }
            }
            msg.startsWith("target:")   -> {
                currentTargetAngle = msg.removePrefix("target:")
                currentTargetName = ""
            }
            msg.startsWith("target_name:") -> currentTargetName = msg.removePrefix("target_name:")
            msg == "presets_done"      -> presetsLoaded = true
            msg == "settings_done"      -> settingsLoaded = true
            msg == "ok"                 -> { }
            msg.startsWith("ok:")       -> { }
            msg.startsWith("err:")      -> {
                saveStatus = msg
                presetStatus = msg
            }
            else                        -> status = msg
        }
    }

    fun refreshFromDevice() {
        // Always rebuild local caches from MCU so removed entries disappear.
        presets.clear()
        settings.clear()
        presetsLoaded = false
        settingsLoaded = false
        currentTargetAngle = ""
        currentTargetName = ""
        sendCommand("get_target_state")
        sendCommand("get_presets")
        sendCommand("get_settings")
    }

    fun onReady(gatt: BluetoothGatt) {
        activeGatt = gatt
        waitingForReconnect = false
        lastAngleAt = 0L
        measurementStale = true
        refreshFromDevice()
        screen = Screen.LIVE
    }

    when (screen) {
        Screen.CONNECT -> ConnectScreen(
            status = status,
            enabled = permissionsGranted,
            onAppSettings = { screen = Screen.APP_SETTINGS },
            onConnect = { connectToNano(context, ::onMessage, ::onReady) }
        )
        Screen.LIVE -> LiveScreen(
            angle = angle,
            targetAngle = currentTargetAngle,
            targetName = currentTargetName,
            deviationThreshold = settings["deviation_threshold"]?.toFloatOrNull() ?: 1f,
            measurementStale = measurementStale,
            angleFormat = appAngleFormat,
            deviationBackgroundEnabled = appDeviationBackgroundEnabled,
            displayArrow = appDisplayArrow,
            soundAlert = appSoundAlert,
            highToneFreq = appHighToneFreq,
            lowToneFreq = appLowToneFreq,
            showTargetName = appShowTargetName,
            showTargetAngle = appShowTargetAngle,
            showDelta = appShowDelta,
            onAppSettings = { screen = Screen.APP_SETTINGS },
            onSettings = {
                settings.clear()
                settingsLoaded = false
                saveStatus = ""
                sendCommand("get_settings")
                screen = Screen.SETTINGS
            },
            onPresets   = {
                presets.clear()
                presetsLoaded = false
                settings.clear()
                settingsLoaded = false
                presetStatus = ""
                sendCommand("get_presets")
                sendCommand("get_settings")
                screen = Screen.PRESETS
            },
            onCalibrate = {
                saveStatus = ""
                sendCommand("get_calibration")
                screen = Screen.CALIBRATE
            },
            onDisconnect = {
                requestDeviceDisconnect()
                angle = "--"
                currentTargetAngle = ""
                currentTargetName = ""
                lastAngleAt = 0L
                measurementStale = true
                status = ""
                screen = Screen.CONNECT
            }
        )
        Screen.APP_SETTINGS -> AppSettingsScreen(
            angleFormat = appAngleFormat,
            deviationBackgroundEnabled = appDeviationBackgroundEnabled,
            displayArrow = appDisplayArrow,
            soundAlert = appSoundAlert,
            highToneFreq = appHighToneFreq,
            lowToneFreq = appLowToneFreq,
            showTargetName = appShowTargetName,
            showTargetAngle = appShowTargetAngle,
            showDelta = appShowDelta,
            onSave = { updated ->
                appAngleFormat = updated.angleFormat
                appDeviationBackgroundEnabled = updated.deviationBackgroundEnabled
                appDisplayArrow = updated.displayArrow
                appSoundAlert = updated.soundAlert
                appHighToneFreq = updated.highToneFreq
                appLowToneFreq = updated.lowToneFreq
                appShowTargetName = updated.showTargetName
                appShowTargetAngle = updated.showTargetAngle
                appShowDelta = updated.showDelta
                saveAppUiSettings(context, updated)
            },
            onBack = { screen = Screen.LIVE }
        )
        Screen.SETTINGS -> SettingsScreen(
            settings      = settings,
            settingsLoaded = settingsLoaded,
            saveStatus    = saveStatus,
            waitingForReconnect = waitingForReconnect,
            onSave = { draft ->
                saveStatus = "Saving..."
                val needsReboot = draft.keys.any { it != "angle_format" }
                if (needsReboot) {
                    onQueueDrained = {
                        saveStatus = "Rebooting..."
                        waitingForReconnect = true
                        onDisconnected = {
                            connectToNano(context, ::onMessage, ::onReady)
                        }
                    }
                    draft.forEach { (key, value) -> enqueueCommand("set_setting:$key:$value") }
                    enqueueCommand("reboot")
                } else {
                    onQueueDrained = { saveStatus = "Saved." }
                    draft.forEach { (key, value) -> enqueueCommand("set_setting:$key:$value") }
                }
            },
            onBack = { screen = Screen.LIVE }
        )
        Screen.CALIBRATE -> CalibrationScreen(
            currentAngle = angle,
            calibrationAngle = calibrationAngle,
            status = saveStatus,
            onCalibrate = {
                saveStatus = "Calibrating..."
                sendCommand("calibrate")
            },
            onBack = { screen = Screen.LIVE }
        )
        Screen.PRESETS -> PresetScreen(
            presets = presets,
            presetsLoaded = presetsLoaded,
            settingsLoaded = settingsLoaded,
            status = presetStatus,
            currentTargetAngle = currentTargetAngle,
            waitingForReconnect = waitingForReconnect,
            onAddPreset = { name, angle ->
                presets.add(PresetEntry(name, angle))
            },
            onUpdatePreset = { index, name, angle ->
                presets[index] = PresetEntry(name, angle)
            },
            onDeletePreset = { index ->
                presets.removeAt(index)
            },
            onSelectPreset = { angleValue ->
                presetStatus = ""
                enqueueCommand("set_target_angle:$angleValue")
            },
            onClearTarget = {
                presetStatus = ""
                currentTargetAngle = ""
                currentTargetName = ""
                enqueueCommand("set_target_angle:0")
            },
            onSaveToDevice = {
                presetStatus = "Saving presets..."
                onQueueDrained = { presetStatus = "Presets saved." }
                enqueueCommand("clear_presets")
                presets.forEach { preset ->
                    enqueueCommand("add_preset:${preset.name}:${preset.angle}")
                }
            },
            onBack = { screen = Screen.LIVE }
        )
    }
}

@Composable
fun ConnectScreen(status: String, enabled: Boolean, onAppSettings: () -> Unit, onConnect: () -> Unit) {
    Box(modifier = Modifier.fillMaxSize().padding(top = 48.dp, start = 24.dp, end = 24.dp, bottom = 24.dp)) {
        TextButton(
            onClick = onAppSettings,
            modifier = Modifier.align(Alignment.TopEnd)
        ) { Text("⚙", style = MaterialTheme.typography.headlineMedium) }
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "Blunt",
                style = MaterialTheme.typography.headlineLarge,
                color = MaterialTheme.colorScheme.primary
            )
            Spacer(modifier = Modifier.height(48.dp))
        Button(
            onClick = onConnect,
            enabled = enabled,
            modifier = Modifier.fillMaxWidth().height(56.dp)
        ) {
            Text("CONNECT TO DEVICE", style = MaterialTheme.typography.labelLarge)
        }
        if (status.isNotEmpty()) {
            Spacer(modifier = Modifier.height(24.dp))
            Text(
                text = status,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.secondary
            )
        }
        }   // Column
    }   // Box
}

@Composable
fun LiveScreen(
    angle: String,
    targetAngle: String,
    targetName: String,
    deviationThreshold: Float,
    measurementStale: Boolean,
    angleFormat: AppAngleFormat,
    deviationBackgroundEnabled: Boolean,
    displayArrow: Boolean,
    soundAlert: Boolean,
    highToneFreq: Float,
    lowToneFreq: Float,
    showTargetName: Boolean,
    showTargetAngle: Boolean,
    showDelta: Boolean,
    onAppSettings: () -> Unit,
    onSettings: () -> Unit,
    onPresets: () -> Unit,
    onCalibrate: () -> Unit,
    onDisconnect: () -> Unit
) {
    val displayAngle = formatAngleForDisplay(angle, angleFormat)
    val currentAbs = angle.toFloatOrNull()?.let { kotlin.math.abs(it) }
    val targetAbs = targetAngle.toFloatOrNull()?.let { kotlin.math.abs(it) }
    val hasTarget = targetAbs != null && targetAbs > 0f
    val delta = if (hasTarget && currentAbs != null) kotlin.math.abs(currentAbs - targetAbs!!) else null
    val isOffTarget = delta != null && delta > deviationThreshold
    val tooHigh = hasTarget && currentAbs != null && currentAbs > targetAbs!! + deviationThreshold
    val tooLow  = hasTarget && currentAbs != null && currentAbs < targetAbs!! - deviationThreshold

    val tonePlayer = remember { TonePlayer() }
    DisposableEffect(Unit) { onDispose { tonePlayer.stop() } }
    LaunchedEffect(tooLow, tooHigh, displayArrow, soundAlert, highToneFreq, lowToneFreq) {
        when {
            soundAlert && displayArrow && tooLow  -> tonePlayer.play(highToneFreq)
            soundAlert && displayArrow && tooHigh -> tonePlayer.play(lowToneFreq)
            else                                  -> tonePlayer.stop()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(
                if (isOffTarget && deviationBackgroundEnabled) {
                    MaterialTheme.colorScheme.errorContainer
                } else {
                    MaterialTheme.colorScheme.background
                }
            )
            .padding(top = 48.dp, start = 24.dp, end = 24.dp, bottom = 24.dp),
        verticalArrangement = Arrangement.SpaceBetween,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Blunt",
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.secondary
            )
            TextButton(onClick = onAppSettings) { Text("⚙", style = MaterialTheme.typography.headlineMedium) }
        }
        
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            if (displayArrow && hasTarget && currentAbs != null) {
                val dimColor = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.25f)
                Row(
                    horizontalArrangement = Arrangement.spacedBy(48.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = "↑",
                        fontSize = 72.sp,
                        color = if (tooLow) MaterialTheme.colorScheme.error else dimColor,
                    )
                    Text(
                        text = "↓",
                        fontSize = 72.sp,
                        color = if (tooHigh) MaterialTheme.colorScheme.error else dimColor,
                    )
                }
                Spacer(modifier = Modifier.height(16.dp))
            }
            Text(
                text = "CURRENT ANGLE",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.secondary
            )
            Text(
                text = if (displayAngle == "--") "--" else "$displayAngle°",
                style = MaterialTheme.typography.displayLarge,
                color = MaterialTheme.colorScheme.primary
            )
            if (hasTarget) {
                Spacer(modifier = Modifier.height(8.dp))
                if (showTargetName && targetName.isNotBlank()) {
                    Text(
                        text = targetName,
                        style = MaterialTheme.typography.headlineMedium,
                        color = MaterialTheme.colorScheme.tertiary
                    )
                }
                if (showTargetAngle) {
                    Text(
                        text = "${"%.1f".format(targetAbs!!)}°",
                        style = MaterialTheme.typography.titleLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            if (hasTarget && currentAbs != null && showDelta) {
                val signedDelta = currentAbs - targetAbs!!
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Δ %+.1f°".format(signedDelta),
                    style = MaterialTheme.typography.titleMedium,
                    color = if (isOffTarget) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary
                )
            }
            if (measurementStale) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Connected, waiting for measurements...",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.secondary
                )
            }
        }

        Column(
            modifier = Modifier.fillMaxWidth().padding(bottom = 52.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            OutlinedButton(
                onClick = onPresets,
                modifier = Modifier.fillMaxWidth().height(56.dp)
            ) {
                Text("PRESET ANGLES")
            }
            OutlinedButton(
                onClick = onSettings,
                modifier = Modifier.fillMaxWidth().height(56.dp)
            ) {
                Text("DEVICE SETTINGS")
            }
            OutlinedButton(
                onClick = onCalibrate,
                modifier = Modifier.fillMaxWidth().height(56.dp)
            ) {
                Text("CALIBRATE")
            }
            Spacer(modifier = Modifier.height(12.dp))
            TextButton(
                onClick = onDisconnect,
                modifier = Modifier.align(Alignment.CenterHorizontally)
            ) {
                Text("DISCONNECT", color = MaterialTheme.colorScheme.error)
            }
        }
    }
}

@Composable
fun AppSettingsScreen(
    angleFormat: AppAngleFormat,
    deviationBackgroundEnabled: Boolean,
    displayArrow: Boolean,
    soundAlert: Boolean,
    highToneFreq: Float,
    lowToneFreq: Float,
    showTargetName: Boolean,
    showTargetAngle: Boolean,
    showDelta: Boolean,
    onSave: (AppUiSettings) -> Unit,
    onBack: () -> Unit,
) {
    fun current() = AppUiSettings(angleFormat, deviationBackgroundEnabled, displayArrow, soundAlert, highToneFreq, lowToneFreq, showTargetName, showTargetAngle, showDelta)

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp),
    ) {
        Spacer(modifier = Modifier.height(48.dp))

        Column(modifier = Modifier.weight(1f).verticalScroll(rememberScrollState())) {
            Text(
                text = "GENERIC",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.secondary,
                modifier = Modifier.padding(vertical = 8.dp)
            )
            EnumSetting(
                label = "Angle Format (App Only)",
                value = angleFormat.wireValue,
                options = listOf(
                    AppAngleFormat.TWO_DECIMALS.wireValue,
                    AppAngleFormat.ONE_DECIMAL.wireValue,
                    AppAngleFormat.HALF_DEGREE.wireValue,
                )
            ) {
                onSave(current().copy(angleFormat = AppAngleFormat.fromWire(it)))
            }
            HorizontalDivider()

            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "MAIN PAGE",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.secondary,
                modifier = Modifier.padding(vertical = 8.dp)
            )
            BoolSetting(
                label = "Deviation Background Highlight",
                value = deviationBackgroundEnabled,
                onChange = { onSave(current().copy(deviationBackgroundEnabled = it)) }
            )
            HorizontalDivider()
            BoolSetting(
                label = "Display Arrow",
                value = displayArrow,
                onChange = { onSave(current().copy(displayArrow = it)) }
            )
            HorizontalDivider()
            BoolSetting(
                label = "Sound Alert",
                value = soundAlert,
                onChange = { onSave(current().copy(soundAlert = it)) }
            )
            if (soundAlert) {
                TonePickerSetting(
                    label = "↑ High Tone",
                    options = HIGH_TONE_OPTIONS,
                    selectedFreq = highToneFreq,
                    onChange = { onSave(current().copy(highToneFreq = it)) }
                )
                TonePickerSetting(
                    label = "↓ Low Tone",
                    options = LOW_TONE_OPTIONS,
                    selectedFreq = lowToneFreq,
                    onChange = { onSave(current().copy(lowToneFreq = it)) }
                )
            }
            HorizontalDivider()
            BoolSetting(
                label = "Show Target Name",
                value = showTargetName,
                onChange = { onSave(current().copy(showTargetName = it)) }
            )
            HorizontalDivider()
            BoolSetting(
                label = "Show Target Angle",
                value = showTargetAngle,
                onChange = { onSave(current().copy(showTargetAngle = it)) }
            )
            HorizontalDivider()
            BoolSetting(
                label = "Show Delta",
                value = showDelta,
                onChange = { onSave(current().copy(showDelta = it)) }
            )
        }

        TextButton(
            onClick = onBack,
            modifier = Modifier.align(Alignment.End).padding(bottom = 32.dp)
        ) { Text("Ok") }
    }
}

@Composable
fun TonePickerSetting(label: String, options: List<TonePreset>, selectedFreq: Float, onChange: (Float) -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(start = 16.dp, top = 8.dp, bottom = 8.dp),
    ) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        Spacer(modifier = Modifier.height(6.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            options.forEach { preset ->
                if (preset.freq == selectedFreq) {
                    Button(onClick = {}) { Text(preset.label) }
                } else {
                    OutlinedButton(onClick = { onChange(preset.freq) }) { Text(preset.label) }
                }
            }
        }
    }
}

@Composable
fun CalibrationScreen(
    currentAngle: String,
    calibrationAngle: String,
    status: String,
    onCalibrate: () -> Unit,
    onBack: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(top = 48.dp, start = 24.dp, end = 24.dp, bottom = 24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(text = "CALIBRATION", style = MaterialTheme.typography.labelLarge)

        Spacer(modifier = Modifier.height(64.dp))

        Text(
            text = "LAST CALIBRATION ANGLE",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.secondary
        )
        Text(
            text = "$calibrationAngle°",
            style = MaterialTheme.typography.displayMedium,
            color = MaterialTheme.colorScheme.tertiary
        )

        Spacer(modifier = Modifier.height(32.dp))

        Text(
            text = "CURRENT READING",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.secondary
        )
        Text(
            text = "$currentAngle°",
            style = MaterialTheme.typography.displayLarge,
            color = MaterialTheme.colorScheme.primary
        )

        Spacer(modifier = Modifier.weight(1f))

        if (status.isNotEmpty()) {
            Text(
                text = status,
                modifier = Modifier.padding(bottom = 8.dp),
                style = MaterialTheme.typography.bodySmall
            )
        }

        Row(
            modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            TextButton(onClick = onBack) { Text("← Back") }
            Button(onClick = onCalibrate) { Text("Apply") }
        }
    }
}

@SuppressLint("MissingPermission")
fun requestDeviceDisconnect() {
    val gatt = activeGatt
    if (gatt == null) {
        disconnectGatt()
        return
    }

    val rx = gatt.getService(NUS_SERVICE_UUID)?.getCharacteristic(NUS_RX_UUID)
    if (rx == null) {
        disconnectGatt()
        return
    }

    writeCharacteristic(gatt, rx, "app_disconnect".toByteArray())
    // Give the MCU a brief window to process app_disconnect before we close locally.
    mainHandler.postDelayed({ disconnectGatt() }, 200)
}

@SuppressLint("MissingPermission")
fun disconnectGatt() {
    resetBleSession()
    activeGatt?.disconnect()
    activeGatt?.close()
    activeGatt = null
}

fun sendCommand(command: String) = enqueueCommand(command)

fun enqueueCommand(command: String) {
    commandQueue.add(command)
    if (!isSendingCommand) drainCommandQueue()
}

@SuppressLint("MissingPermission")
fun drainCommandQueue() {
    if (commandQueue.isEmpty()) {
        isSendingCommand = false
        onQueueDrained?.invoke()
        onQueueDrained = null
        return
    }
    isSendingCommand = true
    val cmd  = commandQueue.removeFirst()
    val gatt = activeGatt ?: return
    val rx   = gatt.getService(NUS_SERVICE_UUID)?.getCharacteristic(NUS_RX_UUID) ?: return
    writeCharacteristic(gatt, rx, cmd.toByteArray())
}

@SuppressLint("MissingPermission")
fun writeCharacteristic(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic, value: ByteArray) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        gatt.writeCharacteristic(characteristic, value, BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT)
    } else {
        @Suppress("DEPRECATION")
        characteristic.value = value
        @Suppress("DEPRECATION")
        gatt.writeCharacteristic(characteristic)
    }
}

@SuppressLint("MissingPermission")
fun connectToNano(context: Context, onMessage: (String) -> Unit, onReady: (BluetoothGatt) -> Unit) {
    val bluetoothManager = context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
    val scanner = bluetoothManager.adapter.bluetoothLeScanner

    mainHandler.post { onMessage("Scanning...") }

    val scanCallback = object : ScanCallback() {
        @SuppressLint("MissingPermission")
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            if (result.device.name == "Knife_Level") {
                scanner.stopScan(this)
                mainHandler.post { onMessage("Found Knife_Level, connecting...") }
                result.device.connectGatt(context, false, makeGattCallback(onMessage, onReady))
            }
        }
    }
    scanner.startScan(scanCallback)
}

@SuppressLint("MissingPermission")
fun makeGattCallback(onMessage: (String) -> Unit, onReady: (BluetoothGatt) -> Unit) = object : BluetoothGattCallback() {

    override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
        when (newState) {
            BluetoothProfile.STATE_CONNECTED    -> {
                mainHandler.post { onMessage("Connected, setting up...") }
                gatt.requestMtu(512)
            }
            BluetoothProfile.STATE_DISCONNECTED -> {
                mainHandler.post {
                    resetBleSession()
                    if (onDisconnected != null) {
                        onMessage("Disconnected")
                        onDisconnected?.invoke()
                        onDisconnected = null
                    } else {
                        onUnexpectedGattDisconnect?.invoke()
                    }
                }
                gatt.close()
            }
        }
    }

    override fun onMtuChanged(gatt: BluetoothGatt, mtu: Int, status: Int) {
        gatt.discoverServices()
    }

    override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
        val tx = gatt.getService(NUS_SERVICE_UUID)?.getCharacteristic(NUS_TX_UUID) ?: run {
            mainHandler.post { onMessage("NUS service not found") }
            return
        }
        gatt.setCharacteristicNotification(tx, true)
        val descriptor = tx.getDescriptor(CCCD_UUID)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            gatt.writeDescriptor(descriptor, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
        } else {
            @Suppress("DEPRECATION")
            descriptor.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
            @Suppress("DEPRECATION")
            gatt.writeDescriptor(descriptor)
        }
    }

    override fun onDescriptorWrite(gatt: BluetoothGatt, descriptor: BluetoothGattDescriptor, status: Int) {
        mainHandler.post {
            startLiveAngleRetry(gatt)
            onReady(gatt)
        }
    }

    override fun onCharacteristicWrite(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic, status: Int) {
        mainHandler.post { drainCommandQueue() }
    }

    @Suppress("DEPRECATION", "OVERRIDE_DEPRECATION")
    override fun onCharacteristicChanged(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic) {
        val msg = characteristic.value.toString(Charsets.UTF_8)
        mainHandler.post { onMessage(msg) }
    }
}
