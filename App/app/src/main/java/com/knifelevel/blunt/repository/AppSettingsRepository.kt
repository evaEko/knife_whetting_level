package com.knifelevel.blunt.repository

import android.content.Context
import com.knifelevel.blunt.model.ALERT_COLORS
import com.knifelevel.blunt.model.AppAngleFormat
import com.knifelevel.blunt.model.AppUiSettings
import com.knifelevel.blunt.model.ArrowSize
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

fun defaultHighToneFreq() = 880f
fun defaultLowToneFreq()  = 440f

class AppSettingsRepository(private val context: Context) {

    private val prefs get() = context.getSharedPreferences("knife_level_app", Context.MODE_PRIVATE)

    private val _settings = MutableStateFlow(load())
    val settings: StateFlow<AppUiSettings> = _settings.asStateFlow()

    fun save(updated: AppUiSettings) {
        _settings.value = updated
        prefs.edit()
            .putString("angle_format", updated.angleFormat.wireValue)
            .putBoolean("deviation_background_enabled", updated.deviationBackgroundEnabled)
            .putBoolean("display_arrow", updated.displayArrow)
            .putBoolean("sound_too_high_enabled", updated.soundTooHighEnabled)
            .putBoolean("sound_too_low_enabled",  updated.soundTooLowEnabled)
            .putFloat("high_tone_freq", updated.highToneFreq)
            .putFloat("low_tone_freq",  updated.lowToneFreq)
            .putBoolean("show_target_name",  updated.showTargetName)
            .putBoolean("show_target_angle", updated.showTargetAngle)
            .putBoolean("show_delta", updated.showDelta)
            .putInt("custom_angle_countdown_sec", updated.customAngleCountdownSec)
            .putString("too_high_color_label", updated.tooHighColorLabel)
            .putString("too_low_color_label",  updated.tooLowColorLabel)
            .putString("arrow_size", updated.arrowSize.label)
            .putString("custom_small_audio_uri", updated.customSmallAudioUri)
            .putString("custom_big_audio_uri",   updated.customBigAudioUri)
            .putBoolean("on_target_sound_enabled", updated.onTargetSoundEnabled)
            .putBoolean("on_target_continue_on_lifted", updated.onTargetContinueOnLifted)
            .putString("custom_on_target_audio_uri", updated.customOnTargetAudioUri)
            .putBoolean("show_deviation_range", updated.showDeviationRange)
            .putBoolean("lifted_detection_enabled", updated.liftedDetectionEnabled)
            .putInt("lifted_vel_threshold", updated.liftedVelThreshold)
            .putInt("lifted_debounce_ms",   updated.liftedDebounceMs)
            .apply()
    }

    private fun load() = AppUiSettings(
        angleFormat              = AppAngleFormat.fromWire(prefs.getString("angle_format", AppAngleFormat.TWO_DECIMALS.wireValue)),
        deviationBackgroundEnabled = prefs.getBoolean("deviation_background_enabled", true),
        displayArrow             = prefs.getBoolean("display_arrow", true),
        soundTooHighEnabled      = prefs.getBoolean("sound_too_high_enabled", prefs.getBoolean("sound_alert", true)),
        soundTooLowEnabled       = prefs.getBoolean("sound_too_low_enabled",  prefs.getBoolean("sound_alert", true)),
        highToneFreq             = prefs.getFloat("high_tone_freq", defaultHighToneFreq()),
        lowToneFreq              = prefs.getFloat("low_tone_freq",  defaultLowToneFreq()),
        showTargetName           = prefs.getBoolean("show_target_name",  true),
        showTargetAngle          = prefs.getBoolean("show_target_angle", true),
        showDelta                = prefs.getBoolean("show_delta", true),
        customAngleCountdownSec  = prefs.getInt("custom_angle_countdown_sec", 5),
        tooHighColorLabel        = prefs.getString("too_high_color_label", ALERT_COLORS[0].label) ?: ALERT_COLORS[0].label,
        tooLowColorLabel         = prefs.getString("too_low_color_label",  ALERT_COLORS[4].label) ?: ALERT_COLORS[4].label,
        arrowSize                = ArrowSize.fromLabel(prefs.getString("arrow_size", ArrowSize.MEDIUM.label)),
        customSmallAudioUri      = prefs.getString("custom_small_audio_uri", null),
        customBigAudioUri        = prefs.getString("custom_big_audio_uri",   null),
        onTargetSoundEnabled     = prefs.getBoolean("on_target_sound_enabled", false),
        onTargetContinueOnLifted = prefs.getBoolean("on_target_continue_on_lifted", false),
        customOnTargetAudioUri   = prefs.getString("custom_on_target_audio_uri", null),
        showDeviationRange         = prefs.getBoolean("show_deviation_range", false),
        liftedDetectionEnabled     = prefs.getBoolean("lifted_detection_enabled", true),
        liftedVelThreshold         = prefs.getInt("lifted_vel_threshold", 10),
        liftedDebounceMs           = prefs.getInt("lifted_debounce_ms",   1500),
    )
}
