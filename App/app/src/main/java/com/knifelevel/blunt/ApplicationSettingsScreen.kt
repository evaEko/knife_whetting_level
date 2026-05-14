package com.knifelevel.blunt

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.ui.draw.clip
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import android.content.Intent
import kotlinx.coroutines.launch
import com.knifelevel.blunt.model.ALERT_COLORS
import com.knifelevel.blunt.model.AlertColorPreset
import com.knifelevel.blunt.model.AppAngleFormat
import com.knifelevel.blunt.model.AppUiSettings
import com.knifelevel.blunt.model.ArrowSize

@Composable
fun AppSettingsContent(
    modifier: Modifier = Modifier,
    angleFormat: AppAngleFormat,
    deviationBackgroundEnabled: Boolean,
    displayArrow: Boolean,
    soundTooHighEnabled: Boolean,
    soundTooLowEnabled: Boolean,
    highToneFreq: Float,
    lowToneFreq: Float,
    showTargetName: Boolean,
    showTargetAngle: Boolean,
    showDelta: Boolean,
    customAngleCountdownSec: Int,
    tooHighColorLabel: String,
    tooLowColorLabel: String,
    arrowSize: ArrowSize,
    customSmallAudioUri: String?,
    customBigAudioUri: String?,
    onTargetSoundEnabled: Boolean,
    onTargetContinueOnLifted: Boolean,
    customOnTargetAudioUri: String?,
    showDeviationRange: Boolean,
    liftedDetectionEnabled: Boolean,
    liftedVelThreshold: Int,
    liftedDebounceMs: Int,
    onSave: (AppUiSettings) -> Unit,
) {
    fun current() = AppUiSettings(angleFormat, deviationBackgroundEnabled, displayArrow, soundTooHighEnabled, soundTooLowEnabled, highToneFreq, lowToneFreq, showTargetName, showTargetAngle, showDelta, customAngleCountdownSec, tooHighColorLabel, tooLowColorLabel, arrowSize, customSmallAudioUri, customBigAudioUri, onTargetSoundEnabled, onTargetContinueOnLifted, customOnTargetAudioUri, showDeviationRange, liftedDetectionEnabled, liftedVelThreshold, liftedDebounceMs)

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
        ExpandableSection("Lifted") {
            BoolSetting("Enable", liftedDetectionEnabled,
                "Detect when the blade leaves the stone and pause deviation alerts.") {
                onSave(current().copy(liftedDetectionEnabled = it))
            }
            if (liftedDetectionEnabled) {
                StepperSetting("Velocity threshold (°/s)", liftedVelThreshold, 3, 30,
                    description = "Minimum angular speed that triggers a lift event. Lower = more sensitive to slow movements.") {
                    onSave(current().copy(liftedVelThreshold = it))
                }
                StepperSetting("Debounce (ms)", liftedDebounceMs, 200, 4000, 100,
                    description = "How long to wait after the last movement before returning to on-stone state. Higher = fewer false on-stone detections when holding the blade in the air.") {
                    onSave(current().copy(liftedDebounceMs = it))
                }
            }
        }
        ExpandableSection("Measurement Data") {
            EnumSetting(
                label = "Angle Format",
                value = angleFormat.wireValue,
                options = listOf(
                    AppAngleFormat.TWO_DECIMALS.wireValue,
                    AppAngleFormat.ONE_DECIMAL.wireValue,
                    AppAngleFormat.HALF_DEGREE.wireValue,
                )
            ) { onSave(current().copy(angleFormat = AppAngleFormat.fromWire(it))) }

            BoolSetting("Target Name", showTargetName,
                "Show the preset name (e.g. Gyuto) as the label above the live angle.") {
                onSave(current().copy(showTargetName = it))
            }
            BoolSetting("Target Angle", showTargetAngle,
                "Show the target angle value below the live reading.") {
                onSave(current().copy(showTargetAngle = it))
            }
            BoolSetting("Deviation Range", showDeviationRange,
                "Show the allowed angle range (e.g. 13.0° – 17.0°) based on the target and deviation threshold.") {
                onSave(current().copy(showDeviationRange = it))
            }
            BoolSetting("Delta", showDelta,
                "Show the signed difference between the live angle and the target (e.g. Δ+1.2°).") {
                onSave(current().copy(showDelta = it))
            }
        }

        ExpandableSection("Visual Alert") {

            BoolSetting("Direction Arrows", displayArrow,
                "Show ↑↓ arrows indicating which direction to correct the blade angle. The active arrow turns red when outside the threshold.") {
                onSave(current().copy(displayArrow = it))
            }
            if (displayArrow) {
                EnumSetting(
                    label = "Arrow Size",
                    value = arrowSize.label,
                    options = ArrowSize.entries.map { it.label },
                    compact = true
                ) { onSave(current().copy(arrowSize = ArrowSize.fromLabel(it))) }
            }
            BoolSetting("Background Color", deviationBackgroundEnabled,
                "Change the background colour when the blade drifts outside the deviation threshold.") {
                onSave(current().copy(deviationBackgroundEnabled = it))
            }
            if (deviationBackgroundEnabled) {
                AlertColorPickerSetting(
                    label = "Angle too high (↑)",
                    options = ALERT_COLORS,
                    selectedLabel = tooHighColorLabel,
                    onChange = { onSave(current().copy(tooHighColorLabel = it.label)) }
                )
                AlertColorPickerSetting(
                    label = "Angle too low (↓)",
                    options = ALERT_COLORS,
                    selectedLabel = tooLowColorLabel,
                    onChange = { onSave(current().copy(tooLowColorLabel = it.label)) }
                )
            }
        }

        ExpandableSection("Sound Alert") {
            BoolSetting("On angle too high", soundTooHighEnabled,
                "Play a tone when the blade angle is above target + threshold.") {
                onSave(current().copy(soundTooHighEnabled = it))
            }
            if (soundTooHighEnabled) {
                TonePickerSetting("Angle too small (↑)", HIGH_TONE_OPTIONS, highToneFreq) {
                    onSave(current().copy(highToneFreq = it)); previewTone(it)
                }
                AudioFilePicker(
                    label = "Angle too small — custom file",
                    uri = customSmallAudioUri,
                    onPick = { onSave(current().copy(customSmallAudioUri = it)) },
                    onClear = { onSave(current().copy(customSmallAudioUri = null)) },
                )
            }
            BoolSetting("On angle too low", soundTooLowEnabled,
                "Play a tone when the blade angle is below target − threshold.") {
                onSave(current().copy(soundTooLowEnabled = it))
            }
            if (soundTooLowEnabled) {
                TonePickerSetting("Angle too big (↓)", LOW_TONE_OPTIONS, lowToneFreq) {
                    onSave(current().copy(lowToneFreq = it)); previewTone(it)
                }
                AudioFilePicker(
                    label = "Angle too big — custom file",
                    uri = customBigAudioUri,
                    onPick = { onSave(current().copy(customBigAudioUri = it)) },
                    onClear = { onSave(current().copy(customBigAudioUri = null)) },
                )
            }
            BoolSetting("On target", onTargetSoundEnabled,
                "Play audio when the blade is within the target range. Requires a custom audio file.") {
                onSave(current().copy(onTargetSoundEnabled = it))
            }
            if (onTargetSoundEnabled) {
                BoolSetting("Continue on lifted", onTargetContinueOnLifted,
                    "Keep the on-target audio playing when the blade is lifted off the stone.") {
                    onSave(current().copy(onTargetContinueOnLifted = it))
                }
                AudioFilePicker(
                    label = "On target — custom file",
                    uri = customOnTargetAudioUri,
                    onPick = { onSave(current().copy(customOnTargetAudioUri = it)) },
                    onClear = { onSave(current().copy(customOnTargetAudioUri = null)) },
                )
            }
        }

        ExpandableSection("Custom Angle") {
            StepperSetting("Measurement delay (s)", customAngleCountdownSec, 1, 15,
                description = "Countdown in seconds before the live angle is captured as a custom target. Gives you time to position the blade.") {
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
fun AlertColorPickerSetting(label: String, options: List<AlertColorPreset>, selectedLabel: String, onChange: (AlertColorPreset) -> Unit) {
    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        Spacer(modifier = Modifier.height(8.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            options.forEach { preset ->
                val isSelected = preset.label == selectedLabel
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(preset.color)
                        .then(
                            if (isSelected) Modifier.border(3.dp, Color.White, RoundedCornerShape(8.dp))
                            else Modifier
                        )
                        .clickable { if (!isSelected) onChange(preset) }
                )
            }
        }
    }
}

@Composable
fun TonePickerSetting(label: String, options: List<TonePreset>, selectedFreq: Float, onChange: (Float) -> Unit) {
    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 10.dp)) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        Spacer(modifier = Modifier.height(6.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            val pad = PaddingValues(horizontal = 10.dp, vertical = 4.dp)
            options.forEach { preset ->
                if (preset.freq == selectedFreq) {
                    Button(onClick = {}, contentPadding = pad) { Text(preset.label, style = MaterialTheme.typography.labelSmall) }
                } else {
                    OutlinedButton(onClick = { onChange(preset.freq) }, contentPadding = pad) { Text(preset.label, style = MaterialTheme.typography.labelSmall) }
                }
            }
        }
    }
}

@Composable
fun AudioFilePicker(
    label: String,
    uri: String?,
    onPick: (String) -> Unit,
    onClear: () -> Unit,
) {
    val context = LocalContext.current
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { picked ->
        if (picked != null) {
            context.contentResolver.takePersistableUriPermission(
                picked,
                Intent.FLAG_GRANT_READ_URI_PERMISSION,
            )
            onPick(picked.toString())
        }
    }
    val pad = PaddingValues(horizontal = 10.dp, vertical = 4.dp)
    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text(label, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                if (uri != null) {
                    OutlinedButton(onClick = onClear, contentPadding = pad) {
                        Text("Clear", style = MaterialTheme.typography.labelSmall)
                    }
                }
                Button(onClick = { launcher.launch(arrayOf("audio/*")) }, contentPadding = pad) {
                    Text(if (uri == null) "Pick file" else "Change", style = MaterialTheme.typography.labelSmall)
                }
            }
        }
        if (uri != null) {
            Text(
                text = uri.substringAfterLast('%').substringAfterLast('/').take(40),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.secondary,
            )
        }
    }
}
