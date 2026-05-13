package com.knifelevel.blunt.model

import androidx.compose.ui.graphics.Color

enum class AppAngleFormat(val wireValue: String) {
    TWO_DECIMALS("2d"),
    ONE_DECIMAL("1d"),
    HALF_DEGREE("0.5");

    companion object {
        fun fromWire(value: String?): AppAngleFormat =
            entries.firstOrNull { it.wireValue == value } ?: TWO_DECIMALS
    }
}

enum class ArrowSize(val label: String, val sp: Float) {
    SMALL("Small", 36f),
    MEDIUM("Medium", 72f),
    LARGE("Large", 120f),
    XL("XL", 180f);

    companion object {
        fun fromLabel(label: String?): ArrowSize =
            entries.firstOrNull { it.label == label } ?: MEDIUM
    }
}

data class AlertColorPreset(val label: String, val color: Color)

val ALERT_COLORS = listOf(
    AlertColorPreset("Red",    Color(0xFFF44336.toInt())),
    AlertColorPreset("Orange", Color(0xFFFF5722.toInt())),
    AlertColorPreset("Pink",   Color(0xFFE91E63.toInt())),
    AlertColorPreset("Teal",   Color(0xFF009688.toInt())),
    AlertColorPreset("Blue",   Color(0xFF2196F3.toInt())),
)

data class AppUiSettings(
    val angleFormat: AppAngleFormat,
    val deviationBackgroundEnabled: Boolean,
    val displayArrow: Boolean,
    val soundTooHighEnabled: Boolean = true,
    val soundTooLowEnabled: Boolean = true,
    val highToneFreq: Float,
    val lowToneFreq: Float,
    val showTargetName: Boolean,
    val showTargetAngle: Boolean,
    val showDelta: Boolean,
    val customAngleCountdownSec: Int = 5,
    val tooHighColorLabel: String = ALERT_COLORS[0].label,
    val tooLowColorLabel:  String = ALERT_COLORS[4].label,
    val arrowSize: ArrowSize = ArrowSize.MEDIUM,
    val customSmallAudioUri: String? = null,
    val customBigAudioUri:   String? = null,
    val onTargetSoundEnabled: Boolean = false,
    val onTargetContinueOnLifted: Boolean = false,
    val customOnTargetAudioUri: String? = null,
    val showDeviationRange: Boolean = false,
    val liftedDetectionEnabled: Boolean = true,
    val liftedVelThreshold: Int = 10,
    val liftedDebounceMs: Int = 1500,
)
