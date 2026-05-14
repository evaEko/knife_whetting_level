package com.knifelevel.blunt.viewmodel

import android.os.SystemClock
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.knifelevel.blunt.model.ConnectionState
import com.knifelevel.blunt.model.FoundDevice
import com.knifelevel.blunt.model.PresetEntry
import com.knifelevel.blunt.repository.AppSettingsRepository
import com.knifelevel.blunt.repository.DeviceRepository
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

private const val STALE_MS       = 1_500L
private const val STALE_CHECK_MS = 500L

class DeviceViewModel(
    private val repo: DeviceRepository,
    private val appSettingsRepo: AppSettingsRepository,
) : ViewModel() {

    val connectionState: StateFlow<ConnectionState>    = repo.connectionState
    val foundDevices: StateFlow<List<FoundDevice>>     = repo.foundDevices
    val angle: StateFlow<Float?>                       = repo.angle
    val calibrationAngle: StateFlow<String>            = repo.calibrationAngle
    val targetAngle: StateFlow<Float?>                 = repo.targetAngle
    val targetName: StateFlow<String>                  = repo.targetName
    val presets: StateFlow<List<PresetEntry>>          = repo.presets
    val deviceSettings: StateFlow<Map<String, String>> = repo.deviceSettings
    val presetsReady: StateFlow<Boolean>               = repo.presetsReady
    val settingsReady: StateFlow<Boolean>              = repo.settingsReady
    val bladeOnStone: StateFlow<Boolean>               = repo.bladeOnStone

    private val _measurementStale  = MutableStateFlow(true)
    val measurementStale: StateFlow<Boolean> = _measurementStale.asStateFlow()

    private val _captureCountdown = MutableStateFlow(-1)
    val captureCountdown: StateFlow<Int> = _captureCountdown.asStateFlow()

    init {
        viewModelScope.launch {
            appSettingsRepo.settings.collect { settings ->
                repo.liftedDetectionEnabled = settings.liftedDetectionEnabled
                repo.liftedVelThreshold     = settings.liftedVelThreshold.toFloat()
                repo.liftedDebounceMs       = settings.liftedDebounceMs.toLong()
            }
        }
        viewModelScope.launch {
            repo.angleReceivedAt.collect { receivedAt ->
                if (receivedAt > 0L) _measurementStale.value = false
            }
        }
        viewModelScope.launch {
            while (true) {
                delay(STALE_CHECK_MS)
                val lastAt = repo.angleReceivedAt.value
                val isStale = lastAt == 0L || SystemClock.elapsedRealtime() - lastAt > STALE_MS
                if (isStale) {
                    _measurementStale.value = true
                    if (connectionState.value == ConnectionState.CONNECTED) repo.restartLive()
                }
            }
        }
        viewModelScope.launch {
            connectionState.collect { state ->
                when (state) {
                    ConnectionState.CONNECTED -> {
                        _measurementStale.value = true
                        repo.refreshFromDevice()
                    }
                    ConnectionState.DISCONNECTED -> {
                        _measurementStale.value = true
                        repo.resetDeviceState()
                    }
                    else -> {}
                }
            }
        }
    }

    // ---------------------------------------------------------------- actions

    fun scan()                       = repo.scan()
    fun connect(device: FoundDevice) = repo.connect(device.address)
    fun disconnect()                 = repo.disconnect()
    fun sendCommand(cmd: String)     = repo.sendCommand(cmd)
    fun calibrate()                  = repo.sendCommand("calibrate")
    fun setTargetAngle(angle: Float) = repo.sendCommand("set_target_angle:$angle")
    fun clearTarget()                = repo.clearTarget()

    fun captureAngle(angle: Float) {
        viewModelScope.launch {
            for (s in 5 downTo 1) { _captureCountdown.value = s; delay(1_000) }
            _captureCountdown.value = -1
            repo.sendCommand("set_custom_angle:${"%.2f".format(angle)}")
        }
    }

    fun savePresets(list: List<PresetEntry>, onDone: () -> Unit) {
        repo.setOnQueueDrained(onDone)
        repo.sendCommand("clear_presets")
        list.forEach { repo.sendCommand("add_preset:${it.name}:${it.angle}") }
    }

    fun saveLevelSettings(draft: Map<String, String>, onDone: () -> Unit) {
        repo.setOnQueueDrained {
            repo.sendCommand("get_settings")
            onDone()
        }
        draft.forEach { (key, value) -> repo.sendCommand("set_setting:$key:$value") }
        repo.sendCommand("reinit")
    }

    fun refreshFromDevice()         = repo.refreshFromDevice()
    fun refreshPresetsAndSettings() = repo.refreshPresetsAndSettings()
}

class DeviceViewModelFactory(
    private val repo: DeviceRepository,
    private val appSettingsRepo: AppSettingsRepository,
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        @Suppress("UNCHECKED_CAST")
        return DeviceViewModel(repo, appSettingsRepo) as T
    }
}
