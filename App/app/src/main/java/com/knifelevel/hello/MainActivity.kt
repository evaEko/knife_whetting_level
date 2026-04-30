package com.knifelevel.hello

import android.Manifest
import android.annotation.SuppressLint
import android.util.Log
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
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.VolumeOff
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import kotlinx.coroutines.launch
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
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

enum class Screen { CONNECT, LIVE, SETTINGS, CALIBRATE, PRESETS }

data class PresetEntry(val name: String, val angle: String)

data class FoundDevice(val address: String, val rssi: Int) {
    val shortId: String get() = address.takeLast(5)
    val signalBars: String get() = when {
        rssi >= -60 -> "▂▄▆█"
        rssi >= -70 -> "▂▄▆·"
        rssi >= -80 -> "▂▄··"
        else        -> "▂···"
    }
}

data class AlertColorPreset(val label: String, val color: Color)

val ALERT_COLORS = listOf(
    AlertColorPreset("Red",    Color(0xFFFFCDD2.toInt())),
    AlertColorPreset("Orange", Color(0xFFFFE0B2.toInt())),
    AlertColorPreset("Yellow", Color(0xFFFFF9C4.toInt())),
    AlertColorPreset("Green",  Color(0xFFC8E6C9.toInt())),
    AlertColorPreset("Blue",   Color(0xFFBBDEFB.toInt())),
)

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
    val customAngleCountdownSec: Int = 5,
    val tooHighColorLabel: String = ALERT_COLORS[0].label,
    val tooLowColorLabel:  String = ALERT_COLORS[4].label,
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
        customAngleCountdownSec = prefs.getInt("custom_angle_countdown_sec", 5),
        tooHighColorLabel = prefs.getString("too_high_color_label", ALERT_COLORS[0].label) ?: ALERT_COLORS[0].label,
        tooLowColorLabel  = prefs.getString("too_low_color_label",  ALERT_COLORS[4].label) ?: ALERT_COLORS[4].label,
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
        .putFloat("lowTone_freq", settings.lowToneFreq)
        .putBoolean("show_target_name", settings.showTargetName)
        .putBoolean("show_target_angle", settings.showTargetAngle)
        .putBoolean("show_delta", settings.showDelta)
        .putInt("custom_angle_countdown_sec", settings.customAngleCountdownSec)
        .putString("too_high_color_label", settings.tooHighColorLabel)
        .putString("too_low_color_label",  settings.tooLowColorLabel)
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
    var appCustomAngleCountdownSec by remember { mutableStateOf(initialAppUi.customAngleCountdownSec) }
    var appTooHighColorLabel by remember { mutableStateOf(initialAppUi.tooHighColorLabel) }
    var appTooLowColorLabel  by remember { mutableStateOf(initialAppUi.tooLowColorLabel) }
    var status           by remember { mutableStateOf("") }
    var permissionsGranted by remember { mutableStateOf(false) }
    var saveStatus       by remember { mutableStateOf("") }
    var presetStatus     by remember { mutableStateOf("") }
    var waitingForReconnect by remember { mutableStateOf(false) }
    val foundDevices     = remember { mutableStateListOf<FoundDevice>() }
    var isScanning       by remember { mutableStateOf(false) }
    var hasScanned       by remember { mutableStateOf(false) }
    val settings         = remember { mutableStateMapOf<String, String>() }
    val presets          = remember { mutableStateListOf<PresetEntry>() }
    var settingsLoaded   by remember { mutableStateOf(false) }
    var presetsLoaded    by remember { mutableStateOf(false) }
    var customAngleCountdown by remember { mutableStateOf(-1) }
    val mainScope = rememberCoroutineScope()

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        permissionsGranted = permissions.values.all { it }
        if (!permissionsGranted) status = "Permissions denied"
    }

    val requiredPermissions = arrayOf(
        Manifest.permission.BLUETOOTH_SCAN,
        Manifest.permission.BLUETOOTH_CONNECT,
        Manifest.permission.ACCESS_FINE_LOCATION,
        Manifest.permission.ACCESS_COARSE_LOCATION
    )

    LaunchedEffect(Unit) {
        val allGranted = requiredPermissions.all {
            context.checkSelfPermission(it) == android.content.pm.PackageManager.PERMISSION_GRANTED
        }
        if (allGranted) {
            permissionsGranted = true
        } else {
            permissionLauncher.launch(requiredPermissions)
        }
    }

    LaunchedEffect(screen, waitingForReconnect, currentTargetAngle) {
        if (screen == Screen.CONNECT || waitingForReconnect || currentTargetAngle.isNotBlank()) return@LaunchedEffect
        while (activeGatt != null && currentTargetAngle.isBlank()) {
            sendCommand("get_target_state")
            delay(1_000)
        }
    }

    LaunchedEffect(screen) {
        Log.d("KL_NAV", "screen = $screen")
    }

    DisposableEffect(Unit) {
        onUnexpectedGattDisconnect = {
            Log.w("KL_NAV", "onUnexpectedGattDisconnect fired on screen=$screen activeGatt=$activeGatt", Throwable("stack"))
            waitingForReconnect = false
            angle = "--"
            currentTargetAngle = ""
            currentTargetName = ""
            lastAngleAt = 0L
            measurementStale = true
            status = "Disconnected"
            if (screen != Screen.CONNECT && screen != Screen.SETTINGS) {
                screen = Screen.CONNECT
            }
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
        Log.d("KL_NAV", "onReady fired, screen=$screen waitingForReconnect=$waitingForReconnect")
        activeGatt = gatt
        val wasReconnecting = waitingForReconnect
        waitingForReconnect = false
        lastAngleAt = 0L
        measurementStale = true
        refreshFromDevice()
        if (screen == Screen.CONNECT || wasReconnecting) {
            screen = Screen.LIVE
        }
    }

    fun connectToDevice(device: FoundDevice) {
        connectToNano(context, device.address, ::onMessage, ::onReady)
    }

    fun doScan() {
        foundDevices.clear()
        isScanning = true
        hasScanned = true
        status = ""
        startScan(
            context,
            onFound = { device ->
                val idx = foundDevices.indexOfFirst { it.address == device.address }
                if (idx < 0) foundDevices.add(device) else foundDevices[idx] = device
            },
            onDone = {
                isScanning = false
                if (foundDevices.size == 1) connectToDevice(foundDevices[0])
            }
        )
    }

    when (screen) {
        Screen.CONNECT -> ConnectScreen(
            status = status,
            enabled = permissionsGranted,
            isScanning = isScanning,
            hasScanned = hasScanned,
            foundDevices = foundDevices,
            onAppSettings = {
                settings.clear()
                settingsLoaded = false
                saveStatus = ""
                if (activeGatt != null) sendCommand("get_settings")
                screen = Screen.SETTINGS
            },
            onScan = { doScan() },
            onConnect = { connectToDevice(it) }
        )
        Screen.LIVE -> LiveScreen(
            angle = angle,
            targetAngle = currentTargetAngle,
            targetName = currentTargetName,
            deviationThreshold = settings["deviation_threshold"]?.toFloatOrNull() ?: 1f,
            measurementStale = measurementStale,
            angleFormat = appAngleFormat,
            deviationBackgroundEnabled = appDeviationBackgroundEnabled,
            tooHighColor = ALERT_COLORS.firstOrNull { it.label == appTooHighColorLabel }?.color ?: ALERT_COLORS[0].color,
            tooLowColor  = ALERT_COLORS.firstOrNull { it.label == appTooLowColorLabel  }?.color ?: ALERT_COLORS[4].color,
            displayArrow = appDisplayArrow,
            soundAlert = appSoundAlert,
            highToneFreq = appHighToneFreq,
            lowToneFreq = appLowToneFreq,
            showTargetName = appShowTargetName,
            showTargetAngle = appShowTargetAngle,
            showDelta = appShowDelta,
            onAppSettings = {
                settings.clear()
                settingsLoaded = false
                saveStatus = ""
                if (activeGatt != null) sendCommand("get_settings")
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
            onCustomAngle = {
                if (customAngleCountdown < 0) {
                    mainScope.launch {
                        for (s in appCustomAngleCountdownSec downTo 1) {
                            customAngleCountdown = s
                            delay(1_000)
                        }
                        customAngleCountdown = -1
                        enqueueCommand("set_custom_angle:$angle")
                    }
                }
            },
            customAngleCountdown = customAngleCountdown,
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
        Screen.SETTINGS -> SettingsScreen(
            settings = settings,
            settingsLoaded = settingsLoaded,
            saveStatus = saveStatus,
            waitingForReconnect = waitingForReconnect,
            onSaveLevel = { draft ->
                saveStatus = "Saving..."
                onQueueDrained = {
                    saveStatus = "Saved."
                    settings.clear()
                    settingsLoaded = false
                    sendCommand("get_settings")
                }
                draft.forEach { (key, value) -> enqueueCommand("set_setting:$key:$value") }
                enqueueCommand("reinit")
            },
            angleFormat = appAngleFormat,
            deviationBackgroundEnabled = appDeviationBackgroundEnabled,
            displayArrow = appDisplayArrow,
            soundAlert = appSoundAlert,
            highToneFreq = appHighToneFreq,
            lowToneFreq = appLowToneFreq,
            showTargetName = appShowTargetName,
            showTargetAngle = appShowTargetAngle,
            showDelta = appShowDelta,
            customAngleCountdownSec = appCustomAngleCountdownSec,
            tooHighColorLabel = appTooHighColorLabel,
            tooLowColorLabel  = appTooLowColorLabel,
            onSaveApp = { updated ->
                appAngleFormat = updated.angleFormat
                appDeviationBackgroundEnabled = updated.deviationBackgroundEnabled
                appDisplayArrow = updated.displayArrow
                appSoundAlert = updated.soundAlert
                appHighToneFreq = updated.highToneFreq
                appLowToneFreq = updated.lowToneFreq
                appShowTargetName = updated.showTargetName
                appShowTargetAngle = updated.showTargetAngle
                appShowDelta = updated.showDelta
                appCustomAngleCountdownSec = updated.customAngleCountdownSec
                appTooHighColorLabel = updated.tooHighColorLabel
                appTooLowColorLabel  = updated.tooLowColorLabel
                saveAppUiSettings(context, updated)
            },
            onBack = { screen = if (activeGatt != null) Screen.LIVE else Screen.CONNECT }
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
fun ConnectScreen(
    status: String,
    enabled: Boolean,
    isScanning: Boolean,
    hasScanned: Boolean,
    foundDevices: List<FoundDevice>,
    onAppSettings: () -> Unit,
    onScan: () -> Unit,
    onConnect: (FoundDevice) -> Unit,
) {
    Box(modifier = Modifier.fillMaxSize().padding(top = 48.dp, start = 24.dp, end = 24.dp, bottom = 24.dp)) {
        TextButton(
            onClick = onAppSettings,
            modifier = Modifier.align(Alignment.TopEnd)
        ) { Text("⚙", style = MaterialTheme.typography.headlineMedium) }
        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.weight(1f))
            Text(
                text = "Blunt",
                style = MaterialTheme.typography.headlineLarge,
                color = MaterialTheme.colorScheme.primary
            )
            Spacer(modifier = Modifier.height(48.dp))
            Button(
                onClick = onScan,
                enabled = enabled && !isScanning,
                modifier = Modifier.fillMaxWidth().height(56.dp)
            ) {
                Text("Scan for Levels", style = MaterialTheme.typography.labelLarge)
            }
            if (status.isNotEmpty()) {
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = status,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.secondary
                )
            }
            Spacer(modifier = Modifier.weight(1f))

            // Device list area
            if (isScanning || foundDevices.isNotEmpty()) {
                Column(modifier = Modifier.fillMaxWidth()) {
                    if (isScanning) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            modifier = Modifier.padding(bottom = 8.dp)
                        ) {
                            CircularProgressIndicator(modifier = Modifier.size(16.dp), strokeWidth = 2.dp)
                            Text("Scanning…", style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.secondary)
                        }
                    }
                    foundDevices.forEach { device ->
                        HorizontalDivider()
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 12.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Column {
                                Text("Knife Level", style = MaterialTheme.typography.bodyLarge)
                                Text(device.shortId, style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.secondary)
                            }
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(12.dp)
                            ) {
                                Text(device.signalBars, style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.secondary)
                                Button(onClick = { onConnect(device) }) { Text("Connect") }
                            }
                        }
                    }
                    if (!isScanning && foundDevices.isEmpty() && hasScanned) {
                        HorizontalDivider()
                        Text(
                            "No devices found.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.secondary,
                            modifier = Modifier.padding(vertical = 16.dp)
                        )
                    }
                }
            }
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
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
    tooHighColor: Color,
    tooLowColor: Color,
    displayArrow: Boolean,
    soundAlert: Boolean,
    highToneFreq: Float,
    lowToneFreq: Float,
    showTargetName: Boolean,
    showTargetAngle: Boolean,
    showDelta: Boolean,
    onAppSettings: () -> Unit,
    onPresets: () -> Unit,
    onCalibrate: () -> Unit,
    onCustomAngle: () -> Unit,
    onDisconnect: () -> Unit,
    customAngleCountdown: Int = -1
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
    var muted by remember { mutableStateOf(false) }
    DisposableEffect(Unit) { onDispose { tonePlayer.stop() } }
    LaunchedEffect(tooLow, tooHigh, displayArrow, soundAlert, muted, highToneFreq, lowToneFreq) {
        when {
            soundAlert && !muted && displayArrow && tooLow  -> tonePlayer.play(highToneFreq)
            soundAlert && !muted && displayArrow && tooHigh -> tonePlayer.play(lowToneFreq)
            else                                  -> tonePlayer.stop()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(
                if (!deviationBackgroundEnabled) MaterialTheme.colorScheme.background
                else if (tooHigh) tooHighColor
                else if (tooLow) tooLowColor
                else MaterialTheme.colorScheme.background
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
            Row(verticalAlignment = Alignment.CenterVertically) {
                if (soundAlert) {
                    TextButton(onClick = { muted = !muted }) {
                        Icon(
                            imageVector = if (muted) Icons.Filled.VolumeOff else Icons.Filled.VolumeUp,
                            contentDescription = if (muted) "Unmute" else "Mute",
                            tint = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.size(28.dp),
                        )
                    }
                }
                TextButton(onClick = onAppSettings) { Text("⚙", style = MaterialTheme.typography.headlineMedium) }
            }
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
                onClick = onCalibrate,
                modifier = Modifier.fillMaxWidth().height(56.dp)
            ) {
                Text("CALIBRATION")
            }
            OutlinedButton(
                onClick = onPresets,
                modifier = Modifier.fillMaxWidth().height(56.dp)
            ) {
                Text("ANGLE LIBRARY")
            }
            OutlinedButton(
                onClick = onCustomAngle,
                enabled = !measurementStale && angle != "--" && customAngleCountdown < 0,
                modifier = Modifier.fillMaxWidth().height(56.dp)
            ) {
                Text(if (customAngleCountdown > 0) "CUSTOM ANGLE ($customAngleCountdown)" else "CUSTOM ANGLE")
            }
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
fun startScan(
    context: Context,
    onFound: (FoundDevice) -> Unit,
    onDone: () -> Unit,
) {
    val manager = context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
    val scanner = manager.adapter.bluetoothLeScanner
    val seen = mutableSetOf<String>()

    val callback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            if (result.device.name == "Knife_Level") {
                val addr = result.device.address
                val device = FoundDevice(addr, result.rssi)
                mainHandler.post {
                    if (seen.add(addr)) onFound(device)
                    else onFound(device)  // update RSSI even for known devices
                }
            }
        }
    }
    scanner.startScan(callback)
    mainHandler.postDelayed({
        scanner.stopScan(callback)
        mainHandler.post { onDone() }
    }, 5_000)
}

@SuppressLint("MissingPermission")
fun connectToNano(context: Context, address: String, onMessage: (String) -> Unit, onReady: (BluetoothGatt) -> Unit) {
    val manager = context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
    mainHandler.post { onMessage("Connecting...") }
    manager.adapter.getRemoteDevice(address)
        .connectGatt(context, false, makeGattCallback(onMessage, onReady))
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
