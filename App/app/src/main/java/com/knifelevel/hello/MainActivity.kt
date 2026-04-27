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
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

val NUS_SERVICE_UUID = UUID.fromString("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
val NUS_TX_UUID      = UUID.fromString("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
val NUS_RX_UUID      = UUID.fromString("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
val CCCD_UUID        = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")

val mainHandler      = Handler(Looper.getMainLooper())
var activeGatt: BluetoothGatt? = null

// Commands are queued so we never have two concurrent GATT writes
val commandQueue     = ArrayDeque<String>()
var isSendingCommand = false
var onQueueDrained: (() -> Unit)? = null
var onDisconnected: (() -> Unit)? = null

enum class Screen { CONNECT, LIVE, SETTINGS, CALIBRATE, PRESETS }

data class PresetEntry(val name: String, val angle: String)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MainScreen(context = this) }
    }
}

@Composable
fun MainScreen(context: Context) {
    var screen           by remember { mutableStateOf(Screen.CONNECT) }
    var angle            by remember { mutableStateOf("--") }
    var calibrationAngle by remember { mutableStateOf("--") }
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

    fun onMessage(msg: String) {
        when {
            msg.startsWith("angle:")   -> angle = msg.removePrefix("angle:")
            msg.startsWith("calibration:") -> calibrationAngle = msg.removePrefix("calibration:")
            msg.startsWith("preset:") -> {
                val rest = msg.removePrefix("preset:")
                val idx = rest.lastIndexOf(':')
                if (idx > 0) {
                    presets.add(PresetEntry(rest.substring(0, idx), rest.substring(idx + 1)))
                }
            }
            msg.startsWith("setting:") -> {
                val rest = msg.removePrefix("setting:")
                val idx  = rest.indexOf(':')
                if (idx > 0) settings[rest.substring(0, idx)] = rest.substring(idx + 1)
            }
            msg == "ok:calibrated"     -> saveStatus = "Calibration saved."
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

    fun onReady(gatt: BluetoothGatt) {
        activeGatt = gatt
        waitingForReconnect = false
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
                disconnectGatt()
                angle = "--"
                status = ""
                screen = Screen.CONNECT
            }
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
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Button(onClick = onConnect, enabled = enabled) { Text("Connect") }
        Spacer(modifier = Modifier.height(16.dp))
        Text(text = status)
    }
}

@Composable
fun LiveScreen(
    angle: String,
    onSettings: () -> Unit,
    onPresets: () -> Unit,
    onCalibrate: () -> Unit,
    onDisconnect: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(text = "$angle°", style = MaterialTheme.typography.displayLarge)
        Spacer(modifier = Modifier.height(32.dp))
        Button(onClick = onSettings)  { Text("Settings") }
        Spacer(modifier = Modifier.height(8.dp))
        Button(onClick = onPresets)   { Text("Preset Angles") }
        Spacer(modifier = Modifier.height(8.dp))
        Button(onClick = onCalibrate) { Text("Calibrate") }
        Spacer(modifier = Modifier.height(32.dp))
        TextButton(onClick = onDisconnect) { Text("Disconnect") }
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
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        TextButton(onClick = onBack, modifier = Modifier.align(Alignment.Start)) { Text("← Back") }
        Spacer(modifier = Modifier.height(24.dp))
        Text(text = "Calibration", style = MaterialTheme.typography.titleLarge)
        Spacer(modifier = Modifier.height(12.dp))
        Text(text = "$currentAngle°", style = MaterialTheme.typography.displayMedium)
        Spacer(modifier = Modifier.height(8.dp))
        Text(text = "Current calibration: $calibrationAngle°")
        Spacer(modifier = Modifier.height(8.dp))
        Text(text = "Place the level on the reference surface, then use the current reading as zero.")
        if (status.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Text(text = status, color = if (status.startsWith("err")) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary)
        }
        Spacer(modifier = Modifier.height(20.dp))
        Button(onClick = onCalibrate, enabled = status != "Calibrating...") {
            Text("Use Current Reading")
        }
    }
}

@SuppressLint("MissingPermission")
fun disconnectGatt() {
    commandQueue.clear()
    isSendingCommand = false
    onQueueDrained = null
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
        val rx = gatt.getService(NUS_SERVICE_UUID)?.getCharacteristic(NUS_RX_UUID) ?: return
        writeCharacteristic(gatt, rx, "live_start".toByteArray())
        mainHandler.post { onReady(gatt) }
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
