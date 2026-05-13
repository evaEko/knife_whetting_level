package com.knifelevel.blunt.repository

import android.os.SystemClock
import com.knifelevel.blunt.ble.BleManager
import com.knifelevel.blunt.model.ConnectionState
import com.knifelevel.blunt.model.FoundDevice
import com.knifelevel.blunt.model.PresetEntry
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch


class DeviceRepository(private val ble: BleManager) {

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    val connectionState: StateFlow<ConnectionState> = ble.connectionState
    val foundDevices: StateFlow<List<FoundDevice>>  = ble.foundDevices

    private val _angle            = MutableStateFlow<Float?>(null)
    private val _calibrationAngle = MutableStateFlow("")
    private val _targetAngle      = MutableStateFlow<Float?>(null)
    private val _targetName       = MutableStateFlow("")
    private val _presets          = MutableStateFlow<List<PresetEntry>>(emptyList())
    private val _deviceSettings   = MutableStateFlow<Map<String, String>>(emptyMap())
    private val _presetsReady     = MutableStateFlow(false)
    private val _settingsReady    = MutableStateFlow(false)
    private val _bladeOnStone     = MutableStateFlow(true)
    private val _angleReceivedAt  = MutableStateFlow(0L)

    val angle: StateFlow<Float?>              = _angle.asStateFlow()
    val calibrationAngle: StateFlow<String>   = _calibrationAngle.asStateFlow()
    val targetAngle: StateFlow<Float?>        = _targetAngle.asStateFlow()
    val targetName: StateFlow<String>         = _targetName.asStateFlow()
    val presets: StateFlow<List<PresetEntry>> = _presets.asStateFlow()
    val deviceSettings: StateFlow<Map<String, String>> = _deviceSettings.asStateFlow()
    val presetsReady: StateFlow<Boolean>      = _presetsReady.asStateFlow()
    val settingsReady: StateFlow<Boolean>     = _settingsReady.asStateFlow()
    val bladeOnStone: StateFlow<Boolean>      = _bladeOnStone.asStateFlow()
    val angleReceivedAt: StateFlow<Long>      = _angleReceivedAt.asStateFlow()

    var liftedDetectionEnabled: Boolean = true
    var liftedVelThreshold: Float       = 10f
    var liftedDebounceMs: Long          = 1500L

    private var lastAngleVal  = 0f
    private var lastAngleTime = 0L
    private var liftedJob: kotlinx.coroutines.Job? = null

    init {
        scope.launch {
            ble.incomingMessages.collect { parse(it) }
        }
    }

    // ---------------------------------------------------------------- public API

    fun scan()                   = ble.scan()
    fun connect(address: String) = ble.connect(address)
    fun disconnect()             = ble.disconnect()
    fun sendCommand(cmd: String) = ble.send(cmd)
    fun setOnQueueDrained(cb: () -> Unit) = ble.setOnQueueDrained(cb)
    fun restartLive()                     = ble.startLiveRetry()

    fun refreshFromDevice() {
        _presets.value        = emptyList()
        _deviceSettings.value = emptyMap()
        _presetsReady.value   = false
        _settingsReady.value  = false
        _targetAngle.value    = null
        _targetName.value     = ""
        ble.send("get_target_state")
        ble.send("get_presets")
        ble.send("get_settings")
    }

    fun refreshPresetsAndSettings() {
        _presets.value        = emptyList()
        _deviceSettings.value = emptyMap()
        _presetsReady.value   = false
        _settingsReady.value  = false
        ble.send("get_target_state")
        ble.send("get_presets")
        ble.send("get_settings")
    }

    fun clearTarget() {
        _targetAngle.value = null
        _targetName.value  = ""
        ble.send("clear_target")
    }

    fun resetDeviceState() {
        _angle.value          = null
        _calibrationAngle.value = ""
        _targetAngle.value    = null
        _targetName.value     = ""
        _presets.value        = emptyList()
        _deviceSettings.value = emptyMap()
        _presetsReady.value   = false
        _settingsReady.value  = false
        _bladeOnStone.value   = true
        _angleReceivedAt.value = 0L
        lastAngleVal  = 0f
        lastAngleTime = 0L
        liftedJob?.cancel()
        liftedJob = null
    }

    // ---------------------------------------------------------------- message parser

    private fun parse(msg: String) {
        when {
            msg.startsWith("angle:") -> {
                val newAngle = msg.removePrefix("angle:").toFloatOrNull() ?: return
                val now = SystemClock.elapsedRealtime()
                _angle.value = newAngle
                _angleReceivedAt.value = now
                ble.stopLiveRetry()

                if (liftedDetectionEnabled && lastAngleTime > 0L) {
                    val dtSec = (now - lastAngleTime) / 1000f
                    if (dtSec > 0f && kotlin.math.abs(newAngle - lastAngleVal) / dtSec > liftedVelThreshold) {
                        _bladeOnStone.value = false
                        liftedJob?.cancel()
                        liftedJob = scope.launch {
                            delay(liftedDebounceMs)
                            _bladeOnStone.value = true
                        }
                    }
                } else if (!liftedDetectionEnabled) {
                    _bladeOnStone.value = true
                }
                lastAngleVal  = newAngle
                lastAngleTime = now
            }
            msg.startsWith("calibration:") -> _calibrationAngle.value = msg.removePrefix("calibration:")
            msg.startsWith("preset:") -> {
                val rest = msg.removePrefix("preset:")
                val idx = rest.lastIndexOf(':')
                if (idx > 0) {
                    val name  = rest.substring(0, idx)
                    val value = rest.substring(idx + 1)
                    val list  = _presets.value.toMutableList()
                    val existing = list.indexOfFirst { it.name == name }
                    if (existing >= 0) list[existing] = PresetEntry(name, value)
                    else list.add(PresetEntry(name, value))
                    _presets.value = list
                }
            }
            msg.startsWith("setting:") -> {
                val rest = msg.removePrefix("setting:")
                val idx  = rest.indexOf(':')
                if (idx > 0) {
                    val map = _deviceSettings.value.toMutableMap()
                    map[rest.substring(0, idx)] = rest.substring(idx + 1)
                    _deviceSettings.value = map
                }
            }
            msg.startsWith("target_state:") -> {
                val rest = msg.removePrefix("target_state:")
                val idx  = rest.indexOf(':')
                if (idx >= 0) {
                    val a = rest.substring(0, idx).toFloatOrNull()
                    _targetAngle.value = if (a != null && a > 0f) a else null
                    _targetName.value  = rest.substring(idx + 1)
                }
            }
            msg == "presets_done"  -> _presetsReady.value  = true
            msg == "settings_done" -> _settingsReady.value = true
        }
    }
}
