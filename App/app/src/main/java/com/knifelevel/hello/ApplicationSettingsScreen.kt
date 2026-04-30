package com.knifelevel.hello

import androidx.compose.foundation.clickable
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
fun AppSettingsContent(
    modifier: Modifier = Modifier,
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

    Column(modifier = modifier.verticalScroll(rememberScrollState())) {
        ExpandableSection("Displayed Data") {
            EnumSetting(
                label = "Angle Format",
                value = angleFormat.wireValue,
                options = listOf(
                    AppAngleFormat.TWO_DECIMALS.wireValue,
                    AppAngleFormat.ONE_DECIMAL.wireValue,
                    AppAngleFormat.HALF_DEGREE.wireValue,
                )
            ) { onSave(current().copy(angleFormat = AppAngleFormat.fromWire(it))) }
            BoolSetting("Direction Arrows", displayArrow) { onSave(current().copy(displayArrow = it)) }
            BoolSetting("Off-target Highlight", deviationBackgroundEnabled) { onSave(current().copy(deviationBackgroundEnabled = it)) }
            BoolSetting("Target Name", showTargetName) { onSave(current().copy(showTargetName = it)) }
            BoolSetting("Target Angle", showTargetAngle) { onSave(current().copy(showTargetAngle = it)) }
            BoolSetting("Delta", showDelta) { onSave(current().copy(showDelta = it)) }
        }

        ExpandableSection("Sound Alert") {
            BoolSetting("Alert", soundAlert) { onSave(current().copy(soundAlert = it)) }
            if (soundAlert) {
                TonePickerSetting("Angle too high (↑)", HIGH_TONE_OPTIONS, highToneFreq) {
                    onSave(current().copy(highToneFreq = it)); previewTone(it)
                }
                TonePickerSetting("Angle too low (↓)", LOW_TONE_OPTIONS, lowToneFreq) {
                    onSave(current().copy(lowToneFreq = it)); previewTone(it)
                }
            }
        }

        ExpandableSection("Custom Angle") {
            StepperSetting("Countdown (s)", customAngleCountdownSec, 1, 15) {
                onSave(current().copy(customAngleCountdownSec = it))
            }
        }
    }
}

@Composable
fun ExpandableSection(title: String, content: @Composable ColumnScope.() -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    Column(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { expanded = !expanded }
                .padding(vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Text(
                text = if (expanded) "▲" else "▼",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
        if (expanded) {
            Column(modifier = Modifier.fillMaxWidth()) {
                content()
            }
            Spacer(modifier = Modifier.height(8.dp))
        }
        HorizontalDivider()
    }
}

@Composable
fun TonePickerSetting(label: String, options: List<TonePreset>, selectedFreq: Float, onChange: (Float) -> Unit) {
    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 10.dp)) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        Spacer(modifier = Modifier.height(6.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            options.forEach { preset ->
                if (preset.freq == selectedFreq) {
                    Button(onClick = {}) { Text(preset.label) }
                } else {
                    OutlinedButton(onClick = { onChange(preset.freq) }) { Text(preset.label) }
                }
            }
        }
    }
}
