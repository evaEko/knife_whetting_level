package com.knifelevel.blunt.ble

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
import android.os.Handler
import android.os.Looper
import android.util.Log
import com.knifelevel.blunt.model.ConnectionState
import com.knifelevel.blunt.model.FoundDevice
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.UUID

private val NUS_SERVICE_UUID = UUID.fromString("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
private val NUS_TX_UUID      = UUID.fromString("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
private val NUS_RX_UUID      = UUID.fromString("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
private val CCCD_UUID        = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")

private const val SCAN_DURATION_MS  = 5_000L
private const val LIVE_RETRY_MS     = 1_000L

class BleManager(private val context: Context) {

    private val handler = Handler(Looper.getMainLooper())

    private val _connectionState = MutableStateFlow(ConnectionState.DISCONNECTED)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

    private val _foundDevices = MutableStateFlow<List<FoundDevice>>(emptyList())
    val foundDevices: StateFlow<List<FoundDevice>> = _foundDevices.asStateFlow()

    private val _incomingMessages = MutableSharedFlow<String>(extraBufferCapacity = 64)
    val incomingMessages: SharedFlow<String> = _incomingMessages.asSharedFlow()

    private var gatt: BluetoothGatt? = null
    private val commandQueue = ArrayDeque<String>()
    private var isSendingCommand = false
    private var onQueueDrained: (() -> Unit)? = null

    private var awaitingLive = false
    private val liveRetry = object : Runnable {
        override fun run() {
            if (!awaitingLive || gatt == null) return
            if (!commandQueue.contains("live_start")) enqueue("live_start")
            handler.postDelayed(this, LIVE_RETRY_MS)
        }
    }

    // ---------------------------------------------------------------- public API

    @SuppressLint("MissingPermission")
    fun scan() {
        val manager = context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        val adapter = manager.adapter
        if (adapter == null || !adapter.isEnabled) {
            _connectionState.value = ConnectionState.DISCONNECTED
            return
        }
        val scanner = adapter.bluetoothLeScanner ?: return
        _foundDevices.value = emptyList()
        _connectionState.value = ConnectionState.SCANNING

        val callback = object : ScanCallback() {
            override fun onScanResult(callbackType: Int, result: ScanResult) {
                if (result.device.name != "Knife_Level") return
                val device = FoundDevice(result.device.address, result.rssi)
                val current = _foundDevices.value.toMutableList()
                val idx = current.indexOfFirst { it.address == device.address }
                if (idx < 0) current.add(device) else current[idx] = device
                _foundDevices.value = current
            }
            override fun onScanFailed(errorCode: Int) {
                _connectionState.value = ConnectionState.DISCONNECTED
            }
        }
        scanner.startScan(callback)
        handler.postDelayed({
            scanner.stopScan(callback)
            if (_connectionState.value == ConnectionState.SCANNING)
                _connectionState.value = ConnectionState.DISCONNECTED
        }, SCAN_DURATION_MS)
    }

    @SuppressLint("MissingPermission")
    fun connect(address: String) {
        val manager = context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        _connectionState.value = ConnectionState.CONNECTING
        manager.adapter.getRemoteDevice(address)
            .connectGatt(context, false, gattCallback)
    }

    @SuppressLint("MissingPermission")
    fun disconnect() {
        send("app_disconnect")
        handler.postDelayed({ closeGatt() }, 200)
    }

    fun send(command: String) = enqueue(command)

    fun setOnQueueDrained(callback: () -> Unit) {
        onQueueDrained = callback
    }

    // ---------------------------------------------------------------- internals

    private fun enqueue(command: String) {
        commandQueue.add(command)
        if (!isSendingCommand) drain()
    }

    @SuppressLint("MissingPermission")
    private fun drain() {
        if (commandQueue.isEmpty()) {
            isSendingCommand = false
            onQueueDrained?.invoke()
            onQueueDrained = null
            return
        }
        isSendingCommand = true
        val cmd  = commandQueue.removeFirst()
        val g    = gatt ?: return
        val rx   = g.getService(NUS_SERVICE_UUID)?.getCharacteristic(NUS_RX_UUID) ?: return
        writeCharacteristic(g, rx, cmd.toByteArray())
    }

    @SuppressLint("MissingPermission")
    private fun writeCharacteristic(g: BluetoothGatt, c: BluetoothGattCharacteristic, value: ByteArray) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            g.writeCharacteristic(c, value, BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT)
        } else {
            @Suppress("DEPRECATION") c.value = value
            @Suppress("DEPRECATION") g.writeCharacteristic(c)
        }
    }

    fun startLiveRetry() {
        awaitingLive = true
        handler.removeCallbacks(liveRetry)
        if (!commandQueue.contains("live_start")) enqueue("live_start")
        handler.postDelayed(liveRetry, LIVE_RETRY_MS)
    }

    fun stopLiveRetry() {
        awaitingLive = false
        handler.removeCallbacks(liveRetry)
    }

    private fun resetSession() {
        commandQueue.clear()
        isSendingCommand = false
        onQueueDrained = null
        stopLiveRetry()
    }

    @SuppressLint("MissingPermission")
    private fun closeGatt() {
        resetSession()
        gatt?.disconnect()
        gatt?.close()
        gatt = null
        _connectionState.value = ConnectionState.DISCONNECTED
    }

    // ---------------------------------------------------------------- GATT callback

    private val gattCallback = object : BluetoothGattCallback() {

        @SuppressLint("MissingPermission")
        override fun onConnectionStateChange(g: BluetoothGatt, status: Int, newState: Int) {
            when (newState) {
                BluetoothProfile.STATE_CONNECTED -> {
                    gatt = g
                    handler.post { g.requestMtu(512) }
                }
                BluetoothProfile.STATE_DISCONNECTED -> {
                    handler.post {
                        resetSession()
                        gatt = null
                        _connectionState.value = ConnectionState.DISCONNECTED
                    }
                    g.close()
                }
            }
        }

        @SuppressLint("MissingPermission")
        override fun onMtuChanged(g: BluetoothGatt, mtu: Int, status: Int) {
            g.discoverServices()
        }

        @SuppressLint("MissingPermission")
        override fun onServicesDiscovered(g: BluetoothGatt, status: Int) {
            val tx = g.getService(NUS_SERVICE_UUID)?.getCharacteristic(NUS_TX_UUID) ?: return
            g.setCharacteristicNotification(tx, true)
            val descriptor = tx.getDescriptor(CCCD_UUID)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                g.writeDescriptor(descriptor, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
            } else {
                @Suppress("DEPRECATION") descriptor.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                @Suppress("DEPRECATION") g.writeDescriptor(descriptor)
            }
        }

        override fun onDescriptorWrite(g: BluetoothGatt, descriptor: BluetoothGattDescriptor, status: Int) {
            handler.post {
                _connectionState.value = ConnectionState.CONNECTED
                startLiveRetry()
            }
        }

        override fun onCharacteristicWrite(g: BluetoothGatt, c: BluetoothGattCharacteristic, status: Int) {
            handler.post { drain() }
        }

        @Suppress("DEPRECATION", "OVERRIDE_DEPRECATION")
        override fun onCharacteristicChanged(g: BluetoothGatt, c: BluetoothGattCharacteristic) {
            val msg = c.value.toString(Charsets.UTF_8)
            handler.post { _incomingMessages.tryEmit(msg) }
        }
    }
}
