package com.knifelevel.blunt.ui.screen

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.VolumeOff
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.knifelevel.blunt.AlertSoundPlayer
import com.knifelevel.blunt.OnTargetPlayer
import com.knifelevel.blunt.model.ALERT_COLORS
import com.knifelevel.blunt.model.AppAngleFormat
import com.knifelevel.blunt.model.ArrowSize
import com.knifelevel.blunt.viewmodel.AppSettingsViewModel
import com.knifelevel.blunt.viewmodel.DeviceViewModel

@Composable
fun LiveScreen(
    deviceVm: DeviceViewModel,
    settingsVm: AppSettingsViewModel,
    onSettings: () -> Unit,
    onPresets: () -> Unit,
    onCalibrate: () -> Unit,
    onDisconnect: () -> Unit,
) {
    val angle            by deviceVm.angle.collectAsState()
    val targetAngle      by deviceVm.targetAngle.collectAsState()
    val targetName       by deviceVm.targetName.collectAsState()
    val deviceSettings   by deviceVm.deviceSettings.collectAsState()
    val measurementStale by deviceVm.measurementStale.collectAsState()
    val bladeOnStone     by deviceVm.bladeOnStone.collectAsState()
    val settings         by settingsVm.settings.collectAsState()

    val deviationThreshold = deviceSettings["deviation_threshold"]?.toFloatOrNull() ?: 1f
    val currentAbs   = angle?.let { kotlin.math.abs(it) }
    val targetAbs    = targetAngle?.let { kotlin.math.abs(it) }
    val hasTarget    = targetAbs != null && targetAbs > 0f
    val delta        = if (hasTarget && currentAbs != null) kotlin.math.abs(currentAbs - targetAbs!!) else null
    val isOffTarget  = delta != null && delta > deviationThreshold
    val tooHigh      = hasTarget && currentAbs != null && currentAbs > targetAbs!! + deviationThreshold
    val tooLow       = hasTarget && currentAbs != null && currentAbs < targetAbs!! - deviationThreshold
    val displayAngle = formatAngle(angle, settings.angleFormat)

    val tooHighColor = ALERT_COLORS.firstOrNull { it.label == settings.tooHighColorLabel }?.color ?: ALERT_COLORS[0].color
    val tooLowColor  = ALERT_COLORS.firstOrNull { it.label == settings.tooLowColorLabel  }?.color ?: ALERT_COLORS[4].color

    val context = LocalContext.current
    val tonePlayer     = remember { AlertSoundPlayer(context) }
    val onTargetPlayer = remember { OnTargetPlayer(context) }
    var muted by remember { mutableStateOf(false) }
    DisposableEffect(Unit) { onDispose { tonePlayer.stop(); onTargetPlayer.release() } }

    LaunchedEffect(tooLow, tooHigh, settings, muted, bladeOnStone, hasTarget) {
        when {
            bladeOnStone && settings.soundTooLowEnabled  && !muted && settings.displayArrow && tooLow  -> tonePlayer.play(settings.highToneFreq, settings.customSmallAudioUri)
            bladeOnStone && settings.soundTooHighEnabled && !muted && settings.displayArrow && tooHigh -> tonePlayer.play(settings.lowToneFreq,  settings.customBigAudioUri)
            else -> tonePlayer.stop()
        }
        val onTargetActive = settings.onTargetSoundEnabled && !muted && hasTarget && settings.customOnTargetAudioUri != null &&
            (bladeOnStone && !tooLow && !tooHigh || !bladeOnStone && settings.onTargetContinueOnLifted)
        if (onTargetActive) onTargetPlayer.play(settings.customOnTargetAudioUri!!) else onTargetPlayer.pause()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(
                if (!settings.deviationBackgroundEnabled || !bladeOnStone) MaterialTheme.colorScheme.background
                else if (tooHigh) tooHighColor
                else if (tooLow)  tooLowColor
                else MaterialTheme.colorScheme.background
            )
            .padding(top = 48.dp, start = 24.dp, end = 24.dp, bottom = 24.dp),
        verticalArrangement = Arrangement.SpaceBetween,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text("Blunt", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.secondary)
            Row(verticalAlignment = Alignment.CenterVertically) {
                if (settings.soundTooHighEnabled || settings.soundTooLowEnabled || settings.onTargetSoundEnabled) {
                    TextButton(onClick = { muted = !muted }) {
                        Icon(
                            imageVector = if (muted) Icons.Filled.VolumeOff else Icons.Filled.VolumeUp,
                            contentDescription = if (muted) "Unmute" else "Mute",
                            tint = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.size(28.dp),
                        )
                    }
                }
                TextButton(onClick = onSettings) { Text("⚙", style = MaterialTheme.typography.headlineMedium) }
            }
        }

        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            if (settings.displayArrow && hasTarget && currentAbs != null) {
                val dimColor = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.25f)
                val arrowGap = when (settings.arrowSize) { ArrowSize.XL -> 8.dp; ArrowSize.LARGE -> 24.dp; else -> 48.dp }
                val arrowSpacing = when (settings.arrowSize) { ArrowSize.XL -> 2.dp; ArrowSize.LARGE -> 8.dp; else -> 16.dp }
                val arrowOffsetX = when (settings.arrowSize) { ArrowSize.XL -> (-(settings.arrowSize.sp / 2)).dp; else -> 0.dp }
                Row(
                    horizontalArrangement = Arrangement.spacedBy(arrowGap),
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.offset(x = arrowOffsetX),
                ) {
                    Text("↑", fontSize = settings.arrowSize.sp.sp, color = if (bladeOnStone && tooLow)  MaterialTheme.colorScheme.error else dimColor)
                    Text("↓", fontSize = settings.arrowSize.sp.sp, color = if (bladeOnStone && tooHigh) MaterialTheme.colorScheme.error else dimColor)
                }
                Spacer(modifier = Modifier.height(arrowSpacing))
            }
            Text(
                text = if (settings.showTargetName && hasTarget && targetName.isNotBlank()) targetName else "CURRENT ANGLE",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.secondary
            )
            Text(
                text = if (displayAngle == "--") "--" else "$displayAngle°",
                style = MaterialTheme.typography.displayLarge,
                color = MaterialTheme.colorScheme.primary
            )
            if (hasTarget) {
                Spacer(modifier = Modifier.height(8.dp))
                if (settings.showTargetAngle) {
                    Text("${"%.1f".format(targetAbs!!)}°", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                if (settings.showDeviationRange) {
                    val lo = "%.1f".format(targetAbs!! - deviationThreshold)
                    val hi = "%.1f".format(targetAbs!! + deviationThreshold)
                    Text("$lo° – $hi°", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            if (hasTarget && currentAbs != null && settings.showDelta) {
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Δ %+.1f°".format(currentAbs - targetAbs!!),
                    style = MaterialTheme.typography.titleMedium,
                    color = if (isOffTarget) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary
                )
            }
            if (measurementStale) {
                Spacer(modifier = Modifier.height(8.dp))
                Text("Connected, waiting for measurements...", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.secondary)
            }
        }

        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(
                text = "▲  LIFTED",
                style = MaterialTheme.typography.labelMedium,
                color = if (!bladeOnStone) MaterialTheme.colorScheme.secondary else Color.Transparent,
                modifier = Modifier.align(Alignment.CenterHorizontally)
            )
            OutlinedButton(onClick = onCalibrate, modifier = Modifier.fillMaxWidth().height(56.dp)) { Text("CALIBRATION") }
            OutlinedButton(onClick = onPresets,   modifier = Modifier.fillMaxWidth().height(56.dp)) { Text("TARGET ANGLE") }
            TextButton(onClick = {
                deviceVm.disconnect()
                onDisconnect()
            }, modifier = Modifier.align(Alignment.CenterHorizontally)) {
                Text("DISCONNECT", color = MaterialTheme.colorScheme.error)
            }
        }
    }
}

private fun formatAngle(raw: Float?, format: AppAngleFormat): String {
    if (raw == null) return "--"
    return when (format) {
        AppAngleFormat.TWO_DECIMALS -> "%.2f".format(raw)
        AppAngleFormat.ONE_DECIMAL  -> "%.1f".format(raw)
        AppAngleFormat.HALF_DEGREE  -> "%.1f".format(kotlin.math.round(raw * 2f) / 2f)
    }
}
