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

enum class Screen { CONNECT, LIVE, SETTINGS }

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
    var status           by remember { mutableStateOf("") }
    var permissionsGranted by remember { mutableStateOf(false) }
    var rebootNeeded     by remember { mutableStateOf(false) }
    var saveStatus       by remember { mutableStateOf("") }
    val settings         = remember { mutableStateMapOf<String, String>() }
    var settingsLoaded   by remember { mutableStateOf(false) }

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
            msg.startsWith("setting:") -> {
                val rest = msg.removePrefix("setting:")
                val idx  = rest.indexOf(':')
                if (idx > 0) settings[rest.substring(0, idx)] = rest.substring(idx + 1)
            }
            msg == "settings_done"      -> settingsLoaded = true
            msg == "ok"                 -> { /* acknowledged, queue handles status */ }
            msg.startsWith("ok:reboot") -> rebootNeeded = true
            msg.startsWith("err:")      -> saveStatus = msg
            else                        -> status = msg
        }
    }

    fun onReady(gatt: BluetoothGatt) {
        activeGatt = gatt
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
                rebootNeeded = false
                saveStatus = ""
                sendCommand("get_settings")
                screen = Screen.SETTINGS
            },
            onPresets   = { /* TODO */ },
            onCalibrate = { /* TODO */ },
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
            onSave = { draft ->
                saveStatus = "Saving..."
                rebootNeeded = false
                onQueueDrained = {
                    saveStatus = if (rebootNeeded) "Saved. Reboot device to apply." else "Saved."
                }
                draft.forEach { (key, value) -> enqueueCommand("set_setting:$key:$value") }
            },
            onBack = { screen = Screen.LIVE }
        )
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
                mainHandler.post { onMessage("Disconnected") }
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
