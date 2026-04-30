package com.knifelevel.hello

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

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
    customAngleCountdownSec: Int,
    onSave: (AppUiSettings) -> Unit,
    onBack: () -> Unit,
) {
    fun current() = AppUiSettings(angleFormat, deviationBackgroundEnabled, displayArrow, soundAlert, highToneFreq, lowToneFreq, showTargetName, showTargetAngle, showDelta, customAngleCountdownSec)

    val previewPlayer = remember { TonePlayer() }
    DisposableEffect(Unit) { onDispose { previewPlayer.stop() } }
    val scope = rememberCoroutineScope()
    fun previewTone(freq: Float) {
        scope.launch {
            previewPlayer.play(freq)
            kotlinx.coroutines.delay(2_000)
            previewPlayer.stop()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp),
    ) {
        Spacer(modifier = Modifier.height(48.dp))

        Column(modifier = Modifier.weight(1f).verticalScroll(rememberScrollState())) {
                        StepperSetting(
                            label = "Custom Angle Countdown (s)",
                            value = customAngleCountdownSec,
                            min = 1,
                            max = 15
                        ) { onSave(current().copy(customAngleCountdownSec = it)) }
                        HorizontalDivider()
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
                    label = "↑",
                    options = HIGH_TONE_OPTIONS,
                    selectedFreq = highToneFreq,
                    onChange = { onSave(current().copy(highToneFreq = it)); previewTone(it) }
                )
                TonePickerSetting(
                    label = "↓",
                    options = LOW_TONE_OPTIONS,
                    selectedFreq = lowToneFreq,
                    onChange = { onSave(current().copy(lowToneFreq = it)); previewTone(it) }
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
            .padding(start = 16.dp, top = 4.dp, bottom = 4.dp),
    ) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        options.forEach { preset ->
            val isSelected = preset.freq == selectedFreq
            TextButton(
                onClick = { onChange(preset.freq) },
                modifier = Modifier.fillMaxWidth(),
                contentPadding = PaddingValues(start = 16.dp, top = 2.dp, bottom = 2.dp, end = 8.dp),
            ) {
                Text(
                    text = preset.label,
                    modifier = Modifier.fillMaxWidth(),
                    color = if (isSelected) MaterialTheme.colorScheme.primary
                            else MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
