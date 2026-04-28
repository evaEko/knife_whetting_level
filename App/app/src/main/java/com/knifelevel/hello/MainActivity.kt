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
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
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
import com.knifelevel.hello.ui.theme.MyApplicationTheme
import kotlinx.coroutines.delay
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

val NUS_SERVICE_UUID = UUID.fromString("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
val NUS_TX_UUID      = UUID.fromString("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
val NUS_RX_UUID      = UUID.fromString("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
val CCCD_UUID        = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")

val mainHandler      = Handler(Looper.getMainLooper())
const val LIVE_RETRY_MS = 1_000L
var activeGatt: BluetoothGatt? = null
var awaitingLiveAngle = false

// Commands are queued so we never have two concurrent GATT writes
val commandQueue     = ArrayDeque<String>()
var isSendingCommand = false
var onQueueDrained: (() -> Unit)? = null
var onDisconnected: (() -> Unit)? = null

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
    val showTargetName: Boolean,
)

fun loadAppUiSettings(context: Context): AppUiSettings {
    val prefs = context.getSharedPreferences("knife_level_app", Context.MODE_PRIVATE)
    return AppUiSettings(
        angleFormat = AppAngleFormat.fromWire(prefs.getString("angle_format", AppAngleFormat.TWO_DECIMALS.wireValue)),
        deviationBackgroundEnabled = prefs.getBoolean("deviation_background_enabled", true),
        showTargetName = prefs.getBoolean("show_target_name", true),
    )
}

fun saveAppUiSettings(context: Context, settings: AppUiSettings) {
    val prefs = context.getSharedPreferences("knife_level_app", Context.MODE_PRIVATE)
    prefs.edit()
        .putString("angle_format", settings.angleFormat.wireValue)
        .putBoolean("deviation_background_enabled", settings.deviationBackgroundEnabled)
        .putBoolean("show_target_name", settings.showTargetName)
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
    var appAngleFormat by remember { mutableStateOf(initialAppUi.angleFormat) }
    var appDeviationBackgroundEnabled by remember { mutableStateOf(initialAppUi.deviationBackgroundEnabled) }
    var appShowTargetName by remember { mutableStateOf(initialAppUi.showTargetName) }
    var status           by remember { mutableStateOf("") }
    var permissionsGranted by remember { mutableStateOf(false) }
    var saveStatus       by remember { mutableStateOf("") }
    var presetStatus     by remember { mutableStateOf("") }
    var waitingForReconnect by remember { mutableStateOf(false) }
    val settings         = remember { mutableStateMapOf<String, String>() }
    val presets          = remember { mutableStateListOf<PresetEntry>() }
    var settingsLoaded   by remember { mutableStateOf(false) }
    var presetsLoaded    by remember { mutableStateOf(false) }
    var backupAvailable  by remember { mutableStateOf(hasPresetBackup(context)) }

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

    fun onMessage(msg: String) {
        when {
            msg.startsWith("angle:")   -> {
                angle = msg.removePrefix("angle:")
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
        refreshFromDevice()
        screen = Screen.LIVE
    }

    when (screen) {
        Screen.CONNECT -> ConnectScreen(
            status = status,
            enabled = permissionsGranted,
            onConnect = { connectToNano(context, ::onMessage, ::onReady) }
        )
        Screen.LIVE -> LiveScreen(
            angle = angle,
            targetAngle = currentTargetAngle,
            targetName = currentTargetName,
            deviationThreshold = settings["deviation_threshold"]?.toFloatOrNull() ?: 1f,
            angleFormat = appAngleFormat,
            deviationBackgroundEnabled = appDeviationBackgroundEnabled,
            showTargetName = appShowTargetName,
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
                status = ""
                screen = Screen.CONNECT
            }
        )
        Screen.APP_SETTINGS -> AppSettingsScreen(
            angleFormat = appAngleFormat,
            deviationBackgroundEnabled = appDeviationBackgroundEnabled,
            showTargetName = appShowTargetName,
            onSave = { updated ->
                appAngleFormat = updated.angleFormat
                appDeviationBackgroundEnabled = updated.deviationBackgroundEnabled
                appShowTargetName = updated.showTargetName
                saveAppUiSettings(context, updated)
                screen = Screen.LIVE
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
            backupAvailable = backupAvailable,
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
            onSaveToDevice = {
                presetStatus = "Saving presets..."
                onQueueDrained = { presetStatus = "Presets saved." }
                enqueueCommand("clear_presets")
                presets.forEach { preset ->
                    enqueueCommand("add_preset:${preset.name}:${preset.angle}")
                }
            },
            onSaveBackup = {
                savePresetBackup(context, settings, presets)
                backupAvailable = true
                presetStatus = "Backup saved."
            },
            onRestoreBackup = {
                val backup = loadPresetBackup(context)
                if (backup == null) {
                    presetStatus = "err:no backup found"
                } else {
                    presets.clear()
                    presets.addAll(backup.presets)
                    settings.clear()
                    settings.putAll(backup.settings)
                    presetStatus = "Restoring backup..."
                    val needsReboot = backup.settings.keys.any { it != "angle_format" }
                    if (needsReboot) {
                        onQueueDrained = {
                            presetStatus = "Rebooting..."
                            waitingForReconnect = true
                            onDisconnected = {
                                connectToNano(context, ::onMessage, ::onReady)
                            }
                        }
                    } else {
                        onQueueDrained = { presetStatus = "Backup restored." }
                    }
                    enqueueCommand("clear_presets")
                    backup.presets.forEach { preset ->
                        enqueueCommand("add_preset:${preset.name}:${preset.angle}")
                    }
                    backup.settings.forEach { (key, value) ->
                        enqueueCommand("set_setting:$key:$value")
                    }
                    if (needsReboot) {
                        enqueueCommand("reboot")
                    }
                }
            },
            onBack = { screen = Screen.LIVE }
        )
    }
}

data class PresetBackup(val settings: Map<String, String>, val presets: List<PresetEntry>)

fun hasPresetBackup(context: Context): Boolean {
    val prefs = context.getSharedPreferences("knife_level", Context.MODE_PRIVATE)
    return prefs.contains("preset_backup")
}

fun savePresetBackup(context: Context, settings: Map<String, String>, presets: List<PresetEntry>) {
    val prefs = context.getSharedPreferences("knife_level", Context.MODE_PRIVATE)
    val root = JSONObject()
    val settingsJson = JSONObject()
    settings.forEach { (key, value) -> settingsJson.put(key, value) }
    val presetsJson = JSONArray()
    presets.forEach { preset ->
        val item = JSONObject()
        item.put("name", preset.name)
        item.put("angle", preset.angle)
        presetsJson.put(item)
    }
    root.put("settings", settingsJson)
    root.put("presets", presetsJson)
    prefs.edit().putString("preset_backup", root.toString()).apply()
}

fun loadPresetBackup(context: Context): PresetBackup? {
    val prefs = context.getSharedPreferences("knife_level", Context.MODE_PRIVATE)
    val raw = prefs.getString("preset_backup", null) ?: return null
    return try {
        val root = JSONObject(raw)
        val settingsJson = root.getJSONObject("settings")
        val presetsJson = root.getJSONArray("presets")
        val settings = mutableMapOf<String, String>()
        settingsJson.keys().forEach { key -> settings[key] = settingsJson.getString(key) }
        val presets = mutableListOf<PresetEntry>()
        for (index in 0 until presetsJson.length()) {
            val item = presetsJson.getJSONObject(index)
            presets.add(PresetEntry(item.getString("name"), item.getString("angle")))
        }
        PresetBackup(settings, presets)
    } catch (_: Exception) {
        null
    }
}

@Composable
fun ConnectScreen(status: String, enabled: Boolean, onConnect: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
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
    }
}

@Composable
fun LiveScreen(
    angle: String,
    targetAngle: String,
    targetName: String,
    deviationThreshold: Float,
    angleFormat: AppAngleFormat,
    deviationBackgroundEnabled: Boolean,
    showTargetName: Boolean,
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
            .padding(24.dp),
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
            TextButton(onClick = onAppSettings) { Text("⚙") }
        }
        
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
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
            if (showTargetName && targetName.isNotBlank()) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = targetName,
                    style = MaterialTheme.typography.headlineMedium,
                    color = MaterialTheme.colorScheme.tertiary
                )
            }
            if (hasTarget && delta != null) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = if (isOffTarget) {
                        "Off target by ${"%.2f".format(delta)}° (limit ±${"%.2f".format(deviationThreshold)}°)"
                    } else {
                        "On target (Δ ${"%.2f".format(delta)}° / ±${"%.2f".format(deviationThreshold)}°)"
                    },
                    style = MaterialTheme.typography.bodyMedium,
                    color = if (isOffTarget) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary
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
    showTargetName: Boolean,
    onSave: (AppUiSettings) -> Unit,
    onBack: () -> Unit,
) {
    var localFormat by remember(angleFormat) { mutableStateOf(angleFormat) }
    var localDeviationBg by remember(deviationBackgroundEnabled) { mutableStateOf(deviationBackgroundEnabled) }
    var localShowTargetName by remember(showTargetName) { mutableStateOf(showTargetName) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp),
    ) {
        Spacer(modifier = Modifier.height(16.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            TextButton(onClick = onBack) { Text("← Back") }
            Text("App Settings", style = MaterialTheme.typography.titleLarge)
            Button(
                onClick = {
                    onSave(
                        AppUiSettings(
                            angleFormat = localFormat,
                            deviationBackgroundEnabled = localDeviationBg,
                            showTargetName = localShowTargetName,
                        )
                    )
                }
            ) { Text("Save") }
        }

        Spacer(modifier = Modifier.height(8.dp))

        EnumSetting(
            label = "Angle Format (App Only)",
            value = localFormat.wireValue,
            options = listOf(
                AppAngleFormat.TWO_DECIMALS.wireValue,
                AppAngleFormat.ONE_DECIMAL.wireValue,
                AppAngleFormat.HALF_DEGREE.wireValue,
            )
        ) {
            localFormat = AppAngleFormat.fromWire(it)
        }
        HorizontalDivider()

        BoolSetting(
            label = "Deviation Background Highlight",
            value = localDeviationBg,
            onChange = { localDeviationBg = it }
        )
        HorizontalDivider()

        BoolSetting(
            label = "Show Target Name",
            value = localShowTargetName,
            onChange = { localShowTargetName = it }
        )
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
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            TextButton(onClick = onBack) { Text("← BACK") }
            Spacer(modifier = Modifier.weight(1f))
            Text(text = "CALIBRATION", style = MaterialTheme.typography.labelLarge)
            Spacer(modifier = Modifier.weight(1f))
            Spacer(modifier = Modifier.width(64.dp)) // Offset back button
        }
        
        Spacer(modifier = Modifier.height(64.dp))
        
        Text(
            text = "TARGET ANGLE",
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

        Button(
            onClick = onCalibrate,
            modifier = Modifier.fillMaxWidth().height(56.dp)
        ) {
            Text("SET AS ZERO")
        }
        
        if (status.isNotEmpty()) {
            Text(
                text = status,
                modifier = Modifier.padding(top = 8.dp),
                style = MaterialTheme.typography.bodySmall
            )
        }
        Spacer(modifier = Modifier.height(24.dp))
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
    commandQueue.clear()
    isSendingCommand = false
    onQueueDrained = null
    stopLiveAngleRetry()
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
                    stopLiveAngleRetry()
                    onMessage("Disconnected")
                    onDisconnected?.invoke()
                    onDisconnected = null
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
